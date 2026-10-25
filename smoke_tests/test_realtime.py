"""Smoke-test every Socket.IO handler in backend/realtime/socket_manager.py.

One ordered flow: chair creates a room, delegates join, and each chair and
delegate control is emitted with the payload keys the server reads. After
every emit the test reads get_received() and fails if an unexpected ``error``
event arrived. Two errors are part of the protocol and are cleared before the
later checks: a join to a missing room, and open_gsl with a bad chair token.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'backend'))

import app as mun  # noqa: E402
from realtime.socket_manager import _timer_threads, state_manager  # noqa: E402

# Every @sio.on handler. disconnect is invoked via SocketIOTestClient.disconnect().
SERVER_EVENTS = (
    'create_room',
    'join_room',
    'disconnect',
    'start_roll_call',
    'mark_attendance',
    'open_gsl',
    'close_gsl',
    'add_to_gsl',
    'remove_from_gsl',
    'reorder_gsl',
    'next_speaker',
    'start_speaker_timer',
    'pause_speaker_timer',
    'reset_speaker_timer',
    'start_mod_caucus',
    'end_mod_caucus',
    'next_mod_caucus_speaker',
    'start_unmod_caucus',
    'end_unmod_caucus',
    'start_voting',
    'end_voting',
    'accept_motion',
    'reject_motion',
    'grant_right_of_reply',
    'deny_right_of_reply',
    'recognize_point',
    'accept_working_paper',
    'suspend_session',
    'resume_session',
    'adjourn_session',
    'send_announcement',
    'request_to_speak',
    'withdraw_from_list',
    'cast_vote',
    'propose_motion',
    'second_motion',
    'raise_point',
    'request_right_of_reply',
    'submit_working_paper',
    'sign_document',
)


def _arg(packet):
    args = packet.get('args') or []
    if not args:
        return {}
    value = args[0]
    return value if isinstance(value, dict) else {'value': value}


def _names(packets):
    return [packet['name'] for packet in packets]


def _errors(packets):
    messages = []
    for packet in packets:
        if packet['name'] != 'error':
            continue
        data = _arg(packet)
        if isinstance(data, dict):
            messages.append(str(data.get('message', '')))
        else:
            messages.append(str(data))
    return messages


def _assert_no_errors(packets):
    messages = _errors(packets)
    assert not messages, (
        f'unexpected error event(s): {messages}; received {_names(packets)}'
    )


def _require(packets, name):
    for packet in packets:
        if packet['name'] == name:
            return _arg(packet)
    raise AssertionError(f'expected event {name!r}; received {_names(packets)}')


def _state(packets):
    states = [_arg(packet) for packet in packets if packet['name'] == 'room_state_updated']
    assert states, f'expected room_state_updated; received {_names(packets)}'
    return states[-1]


def _delegate(state, country):
    for row in state.get('delegates', []):
        if row.get('country') == country:
            return row
    raise AssertionError(f'{country} missing from delegates {state.get("delegates")}')


def _find(items, item_id):
    for item in items:
        if item.get('id') == item_id:
            return item
    raise AssertionError(f'{item_id} not found in {items}')


def _room_json_paths(room_code):
    names = []
    relative = os.path.join(state_manager.data_dir, f'{room_code}.json')
    if not os.path.isabs(relative):
        relative = os.path.join(ROOT, relative)
    names.append(relative)
    names.append(os.path.join(ROOT, 'data', 'committee_states', f'{room_code}.json'))
    unique = []
    for path in names:
        if path not in unique:
            unique.append(path)
    return unique


def test_realtime_socket_flow():
    """Drive every realtime handler and assert the committee state changes."""
    exercised = []
    room_code = None
    chair_token = None
    france_marked_present = False

    chair = mun.socketio.test_client(mun.app)
    delegate = mun.socketio.test_client(mun.app)
    germany = mun.socketio.test_client(mun.app)
    stranger = mun.socketio.test_client(mun.app)
    room_clients = (chair, delegate, germany)

    def drain():
        packets = []
        for client in room_clients:
            if client.is_connected():
                packets.extend(client.get_received())
        return packets

    def chair_emit(event, **fields):
        exercised.append(event)
        payload = {'room_code': room_code, 'chair_token': chair_token}
        payload.update(fields)
        chair.emit(event, payload)
        packets = drain()
        _assert_no_errors(packets)
        return packets

    def delegate_emit(client, event, **fields):
        exercised.append(event)
        payload = {'room_code': room_code}
        payload.update(fields)
        client.emit(event, payload)
        packets = drain()
        _assert_no_errors(packets)
        return packets

    try:
        startup = drain()
        if stranger.is_connected():
            startup.extend(stranger.get_received())
        _assert_no_errors(startup)

        # 1. Chair creates the room.
        exercised.append('create_room')
        chair.emit('create_room', {'committee_name': 'UNEP', 'agenda': 'Climate'})
        created_packets = drain()
        _assert_no_errors(created_packets)
        created = _require(created_packets, 'room_created')
        room_code = created['room_code']
        chair_token = created['chair_token']
        assert room_code, created
        assert chair_token, created
        state = _state(created_packets)
        assert state['room_code'] == room_code
        assert state['committee_name'] == 'UNEP'
        assert state['agenda'] == 'Climate'
        assert 'chair_token' not in state
        assert any(os.path.isfile(path) for path in _room_json_paths(room_code))

        # 2. France joins as a delegate.
        exercised.append('join_room')
        delegate.emit('join_room', {
            'room_code': room_code,
            'country': 'France',
            'role': 'delegate',
        })
        joined_packets = drain()
        _assert_no_errors(joined_packets)
        joined = _require(joined_packets, 'joined')
        assert joined['room_code'] == room_code
        assert joined['country'] == 'France'
        assert joined['role'] == 'delegate'
        connected = _require(joined_packets, 'delegate_connected')
        assert connected['country'] == 'France'
        state = _state(joined_packets)
        assert _delegate(state, 'France')['connected'] is True
        assert _delegate(state, 'France')['present'] is False

        # 3. Bogus room code. Expected error is cleared here, before later checks.
        exercised.append('join_room')
        stranger.emit('join_room', {
            'room_code': 'NOSUCH',
            'country': 'Spain',
            'role': 'delegate',
        })
        bogus_packets = stranger.get_received()
        bogus_errors = _errors(bogus_packets)
        assert bogus_errors, f'expected error for missing room; received {_names(bogus_packets)}'
        assert all('not found' in message.lower() for message in bogus_errors), bogus_errors
        _assert_no_errors(drain())

        # 4. Roll call and attendance.
        packets = chair_emit('start_roll_call', delegates=['France', 'Germany'])
        _require(packets, 'roll_call_started')
        state = _state(packets)
        assert state['status'] == 'roll_call'
        countries = {row['country'] for row in state['delegates']}
        assert {'France', 'Germany'} <= countries
        assert _delegate(state, 'France')['present'] is False
        assert _delegate(state, 'Germany')['present'] is False

        packets = chair_emit('mark_attendance', country='France', present=True)
        attendance = _require(packets, 'attendance_updated')
        assert attendance['country'] == 'France'
        assert attendance['present'] is True
        state = _state(packets)
        assert _delegate(state, 'France')['present'] is True
        france_marked_present = True

        # General speakers list, timers, then close.
        packets = chair_emit('open_gsl', speaker_time=60)
        state = _state(packets)
        assert state['status'] == 'gsl'
        assert state['gsl']['open'] is True
        assert state['gsl']['speaker_time'] == 60

        packets = chair_emit('add_to_gsl', country='France')
        assert _state(packets)['gsl']['speakers'] == ['France']

        packets = chair_emit('add_to_gsl', country='Germany')
        assert _state(packets)['gsl']['speakers'] == ['France', 'Germany']

        packets = chair_emit('reorder_gsl', speakers=['Germany', 'France'])
        assert _state(packets)['gsl']['speakers'] == ['Germany', 'France']

        packets = chair_emit('next_speaker')
        speaker = _require(packets, 'current_speaker_changed')
        assert speaker['speaker'] == 'Germany'
        state = _state(packets)
        assert state['gsl']['current_index'] == 0
        assert state['gsl']['speakers'] == ['Germany', 'France']

        packets = chair_emit('start_speaker_timer', timer='gsl.timer')
        timer = _state(packets)['gsl']['timer']
        assert timer['running'] is True

        packets = chair_emit('pause_speaker_timer', timer='gsl.timer', remaining=30)
        timer = _state(packets)['gsl']['timer']
        assert timer['running'] is False
        assert timer['remaining'] == 30

        packets = chair_emit('reset_speaker_timer', timer='gsl.timer', duration=60)
        timer = _state(packets)['gsl']['timer']
        assert timer['running'] is False
        assert timer['remaining'] == 60

        packets = chair_emit('close_gsl')
        assert _state(packets)['gsl']['open'] is False

        # Chair can also drop a speaker directly. Germany leaves; France stays
        # so a later withdraw_from_list still changes the list.
        packets = chair_emit('remove_from_gsl', country='Germany')
        speakers = _state(packets)['gsl']['speakers']
        assert 'Germany' not in speakers
        assert 'France' in speakers

        # Moderated caucus.
        packets = chair_emit(
            'start_mod_caucus',
            topic='Financing',
            total_time=120,
            speaker_time=30,
        )
        state = _state(packets)
        assert state['status'] == 'mod_caucus'
        assert state['mod_caucus']['active'] is True
        assert state['mod_caucus']['topic'] == 'Financing'
        assert state['mod_caucus']['total_time'] == 120
        assert state['mod_caucus']['speaker_time'] == 30
        assert state['mod_caucus']['speakers'] == []

        packets = delegate_emit(
            delegate,
            'request_to_speak',
            country='France',
            context='mod_caucus',
        )
        assert _state(packets)['mod_caucus']['speakers'] == ['France']

        packets = chair_emit('next_mod_caucus_speaker')
        speaker = _require(packets, 'current_speaker_changed')
        assert speaker['speaker'] == 'France'
        assert speaker['context'] == 'mod_caucus'
        assert _state(packets)['mod_caucus']['current_index'] == 0

        packets = chair_emit('end_mod_caucus')
        state = _state(packets)
        assert state['mod_caucus']['active'] is False
        assert state['status'] == 'gsl'

        # Unmoderated caucus.
        packets = chair_emit('start_unmod_caucus', duration=90, purpose='Drafting')
        state = _state(packets)
        assert state['status'] == 'unmod_caucus'
        assert state['unmod_caucus']['active'] is True
        assert state['unmod_caucus']['duration'] == 90
        assert state['unmod_caucus']['purpose'] == 'Drafting'

        packets = chair_emit('end_unmod_caucus')
        state = _state(packets)
        assert state['unmod_caucus']['active'] is False
        assert state['status'] == 'gsl'

        # Two motions: the first is seconded and accepted, the second rejected.
        packets = delegate_emit(
            delegate,
            'propose_motion',
            country='France',
            type='Moderated Caucus',
            details={'topic': 'Water'},
        )
        proposed = _require(packets, 'motion_proposed')
        motion_id = proposed['motion_id']
        assert motion_id
        assert proposed['type'] == 'Moderated Caucus'
        assert proposed['proposer'] == 'France'
        motion = _find(_state(packets)['motions_queue'], motion_id)
        assert motion['status'] == 'proposed'
        assert motion['details']['topic'] == 'Water'
        assert motion['proposer'] == 'France'

        packets = delegate_emit(
            delegate,
            'second_motion',
            motion_id=motion_id,
            country='Germany',
        )
        seconded = _require(packets, 'motion_seconded')
        assert seconded['motion_id'] == motion_id
        assert seconded['country'] == 'Germany'
        motion = _find(_state(packets)['motions_queue'], motion_id)
        assert motion['seconds'] == ['Germany']

        packets = chair_emit('accept_motion', motion_id=motion_id)
        decided = _require(packets, 'motion_decided')
        assert decided['motion_id'] == motion_id
        assert decided['accepted'] is True
        assert _find(_state(packets)['motions_queue'], motion_id)['status'] == 'accepted'

        packets = delegate_emit(
            delegate,
            'propose_motion',
            country='France',
            type='Moderated Caucus',
            details={'topic': 'Energy'},
        )
        proposed = _require(packets, 'motion_proposed')
        rejected_motion_id = proposed['motion_id']
        assert rejected_motion_id and rejected_motion_id != motion_id
        assert _find(_state(packets)['motions_queue'], rejected_motion_id)['status'] == 'proposed'

        packets = chair_emit('reject_motion', motion_id=rejected_motion_id)
        decided = _require(packets, 'motion_decided')
        assert decided['motion_id'] == rejected_motion_id
        assert decided['accepted'] is False
        assert _find(_state(packets)['motions_queue'], rejected_motion_id)['status'] == 'rejected'
        assert _find(_state(packets)['motions_queue'], motion_id)['status'] == 'accepted'

        # Point of order.
        packets = delegate_emit(
            delegate,
            'raise_point',
            country='France',
            type='Point of Order',
            details='procedure',
        )
        raised = _require(packets, 'point_raised')
        point_id = raised['point_id']
        assert point_id
        assert raised['type'] == 'Point of Order'
        assert raised['country'] == 'France'
        point = _find(_state(packets)['points_queue'], point_id)
        assert point['status'] == 'pending'
        assert point['details'] == 'procedure'
        assert point['country'] == 'France'

        packets = chair_emit('recognize_point', point_id=point_id)
        addressed = _require(packets, 'point_addressed')
        assert addressed['point_id'] == point_id
        assert _find(_state(packets)['points_queue'], point_id)['status'] == 'addressed'

        # Right of reply: grant one request and deny a second.
        packets = delegate_emit(
            delegate,
            'request_right_of_reply',
            country='Germany',
            regarding='France',
        )
        requested = _require(packets, 'right_of_reply_requested')
        req_id = requested['req_id']
        assert req_id
        assert requested['country'] == 'Germany'
        reply = _find(_state(packets)['right_of_reply_queue'], req_id)
        assert reply['status'] == 'pending'
        assert reply['regarding'] == 'France'
        assert reply['country'] == 'Germany'

        packets = chair_emit('grant_right_of_reply', req_id=req_id)
        granted = _require(packets, 'right_of_reply_granted')
        assert granted['req_id'] == req_id
        assert _find(_state(packets)['right_of_reply_queue'], req_id)['status'] == 'granted'

        packets = delegate_emit(
            delegate,
            'request_right_of_reply',
            country='France',
            regarding='Germany',
        )
        denied_req_id = _require(packets, 'right_of_reply_requested')['req_id']
        assert denied_req_id and denied_req_id != req_id

        packets = chair_emit('deny_right_of_reply', req_id=denied_req_id)
        assert _find(_state(packets)['right_of_reply_queue'], denied_req_id)['status'] == 'denied'
        assert _find(_state(packets)['right_of_reply_queue'], req_id)['status'] == 'granted'

        # Working paper, signature, acceptance.
        packets = delegate_emit(
            delegate,
            'submit_working_paper',
            title='Draft WP',
            sponsors=['France'],
            signatories=['France'],
            content='operative text',
        )
        submitted = _require(packets, 'working_paper_submitted')
        wp_id = submitted['wp_id']
        assert wp_id
        assert submitted['title'] == 'Draft WP'
        paper = _find(_state(packets)['working_papers'], wp_id)
        assert paper['status'] == 'submitted'
        assert paper['title'] == 'Draft WP'
        assert paper['sponsors'] == ['France']
        assert paper['signatories'] == ['France']
        assert paper['content'] == 'operative text'

        packets = delegate_emit(
            delegate,
            'sign_document',
            doc_type='working_papers',
            doc_id=wp_id,
            country='Germany',
        )
        paper = _find(_state(packets)['working_papers'], wp_id)
        assert paper['signatories'] == ['France', 'Germany']

        packets = chair_emit('accept_working_paper', wp_id=wp_id)
        _require(packets, 'draft_resolution_introduced')
        state = _state(packets)
        assert _find(state['working_papers'], wp_id)['status'] == 'accepted'
        assert state['draft_resolutions'], state['draft_resolutions']
        assert state['draft_resolutions'][-1]['title'] == 'Draft WP'
        assert 'Germany' in state['draft_resolutions'][-1]['signatories']

        # Germany connects, then both delegates vote.
        exercised.append('join_room')
        germany.emit('join_room', {
            'room_code': room_code,
            'country': 'Germany',
            'role': 'delegate',
        })
        germany_packets = drain()
        _assert_no_errors(germany_packets)
        germany_joined = _require(germany_packets, 'joined')
        assert germany_joined['room_code'] == room_code
        assert germany_joined['country'] == 'Germany'
        assert germany_joined['role'] == 'delegate'
        assert _delegate(_state(germany_packets), 'Germany')['connected'] is True

        packets = chair_emit(
            'start_voting',
            motion='Draft WP',
            type='substantive',
            requires_majority='simple',
        )
        voting_started = _require(packets, 'voting_started')
        assert voting_started['motion'] == 'Draft WP'
        assert voting_started['type'] == 'substantive'
        state = _state(packets)
        assert state['status'] == 'voting'
        assert state['voting']['active'] is True
        assert state['voting']['motion'] == 'Draft WP'
        assert state['voting']['type'] == 'substantive'
        assert state['voting']['requires_majority'] == 'simple'
        assert state['voting']['votes'] == {}

        packets = delegate_emit(delegate, 'cast_vote', country='France', vote='for')
        cast = _require(packets, 'vote_cast')
        assert cast['country'] == 'France'
        assert cast['vote'] == 'for'
        assert _state(packets)['voting']['votes']['France'] == 'for'

        packets = delegate_emit(germany, 'cast_vote', country='Germany', vote='against')
        cast = _require(packets, 'vote_cast')
        assert cast['country'] == 'Germany'
        assert cast['vote'] == 'against'
        votes = _state(packets)['voting']['votes']
        assert votes['France'] == 'for'
        assert votes['Germany'] == 'against'

        packets = chair_emit('end_voting')
        ended = _require(packets, 'voting_ended')
        result = ended['result']
        assert result['for'] >= 1, result
        assert result['against'] >= 1, result
        state = _state(packets)
        assert state['voting']['active'] is False
        assert state['voting']['status'] == 'closed'
        assert state['voting']['result']['for'] >= 1
        assert state['voting']['result']['against'] >= 1
        assert state['status'] == 'gsl'

        # Announcements and session lifecycle.
        packets = chair_emit('send_announcement', message='Break in 5 minutes')
        announcement = _require(packets, 'announcement')
        assert announcement['message'] == 'Break in 5 minutes'
        assert any(
            item['message'] == 'Break in 5 minutes'
            for item in _state(packets)['announcements']
        )

        packets = chair_emit('suspend_session')
        assert _require(packets, 'committee_status_changed')['status'] == 'suspended'
        assert _state(packets)['status'] == 'suspended'

        packets = chair_emit('resume_session')
        assert _require(packets, 'committee_status_changed')['status'] == 'resumed'
        assert _state(packets)['status'] == 'gsl'

        packets = delegate_emit(delegate, 'withdraw_from_list', country='France')
        assert 'France' not in _state(packets)['gsl']['speakers']

        packets = chair_emit('adjourn_session')
        assert _require(packets, 'committee_status_changed')['status'] == 'adjourned'
        state = _state(packets)
        assert state['status'] == 'adjourned'
        assert _delegate(state, 'France')['present'] is True
        assert france_marked_present is True
        assert _timer_threads[room_code]['active'] is False

        # 5. Wrong chair token. This is the other allowed error, then it is cleared.
        gsl_open_before = state_manager.get_public_state(room_code)['gsl']['open']
        exercised.append('open_gsl')
        stranger.emit('open_gsl', {
            'room_code': room_code,
            'chair_token': 'wrong-token',
            'speaker_time': 60,
        })
        unauthorized_packets = stranger.get_received()
        _assert_no_errors(drain())
        unauthorized = _errors(unauthorized_packets)
        assert unauthorized == ['Unauthorized'], unauthorized
        public = state_manager.get_public_state(room_code)
        assert public['status'] == 'adjourned'
        assert public['gsl']['open'] == gsl_open_before
        assert _delegate(public, 'France')['present'] is True

        # 6. Disconnect hits the server's disconnect handler (it emits nothing).
        for client in (chair, delegate, germany, stranger):
            assert client.is_connected()
            queued_errors = _errors(list(client.queue))
            assert not queued_errors, queued_errors
            client.disconnect()
            assert not client.is_connected()
            assert not _errors(list(client.queue))
        exercised.append('disconnect')

        missing = [name for name in SERVER_EVENTS if name not in exercised]
        assert not missing, f'Socket.IO handlers not driven: {missing}'
    finally:
        if room_code and room_code in _timer_threads:
            _timer_threads[room_code]['active'] = False
            thread = _timer_threads[room_code].get('thread')
            if thread is not None:
                thread.join(timeout=2)
        if room_code:
            for path in _room_json_paths(room_code):
                for candidate in (path, path + '.tmp'):
                    if os.path.isfile(candidate):
                        os.remove(candidate)
        for client in (chair, delegate, germany, stranger):
            try:
                if client.is_connected():
                    client.disconnect()
            except Exception:
                pass
