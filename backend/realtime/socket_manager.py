import time
import threading
from flask_socketio import SocketIO, emit, join_room, leave_room
from managers.committee_state_manager import CommitteeStateManager

socketio = SocketIO()
state_manager = CommitteeStateManager()

_timer_threads = {}  # room_code -> {'active': bool, 'thread': Thread}


def init_socketio(app):
    socketio.init_app(app, cors_allowed_origins='*', async_mode='threading')
    return socketio


def _timer_thread_fn(room_code):
    timer_paths = [
        'gsl.timer',
        'mod_caucus.timer',
        'mod_caucus.speaker_timer',
        'unmod_caucus.timer',
    ]
    while _timer_threads.get(room_code, {}).get('active'):
        state = state_manager.get_public_state(room_code)
        if not state:
            break
        ticked = False
        for path in timer_paths:
            parts = path.split('.')
            obj = state
            for p in parts[:-1]:
                obj = obj.get(p, {})
            timer = obj.get(parts[-1], {})
            if timer.get('running') and timer.get('remaining', 0) > 0:
                new_remaining = timer['remaining'] - 1
                state_manager.pause_timer(room_code, path, new_remaining)
                ticked = True
                if new_remaining <= 0:
                    socketio.emit('timer_expired', {'timer': path}, room=room_code)
        if ticked:
            updated = state_manager.get_public_state(room_code)
            socketio.emit('timer_tick', updated, room=room_code)
        time.sleep(1)


def _start_room_timer(room_code):
    if room_code not in _timer_threads:
        _timer_threads[room_code] = {'active': True}
        t = threading.Thread(target=_timer_thread_fn, args=(room_code,), daemon=True)
        _timer_threads[room_code]['thread'] = t
        t.start()


def _broadcast(room_code, event='room_state_updated'):
    state = state_manager.get_public_state(room_code)
    if state:
        socketio.emit(event, state, room=room_code)


def register_events(sio):

    def require_chair(data):
        room_code = data.get('room_code', '').upper()
        token = data.get('chair_token', '')
        return room_code, state_manager.verify_chair(room_code, token)

    @sio.on('create_room')
    def on_create_room(data):
        committee_name = data.get('committee_name', 'Committee')
        agenda = data.get('agenda', '')
        room_code, chair_token = state_manager.create_room(committee_name, agenda)
        join_room(room_code)
        _start_room_timer(room_code)
        state_manager.log_event(room_code, 'room_created', f'Room {room_code} created')
        emit('room_created', {'room_code': room_code, 'chair_token': chair_token})
        _broadcast(room_code)

    @sio.on('join_room')
    def on_join_room(data):
        room_code = data.get('room_code', '').upper()
        country = data.get('country', '')
        role = data.get('role', 'delegate')

        state = state_manager.get_state(room_code)
        if not state:
            if not state_manager.load_room(room_code):
                emit('error', {'message': f'Room {room_code} not found'})
                return

        join_room(room_code)
        _start_room_timer(room_code)

        if role == 'delegate' and country:
            state_manager.set_delegate_connected(room_code, country, '', True)
            state_manager.log_event(room_code, 'delegate_joined', country)
            emit('joined', {'room_code': room_code, 'country': country, 'role': role})
            _broadcast(room_code)
            sio.emit('delegate_connected', {'country': country}, room=room_code)
        else:
            emit('joined', {'room_code': room_code, 'role': role})
            emit('room_state', state_manager.get_public_state(room_code))

    @sio.on('disconnect')
    def on_disconnect():
        pass

    # === CHAIR EVENTS ===

    @sio.on('start_roll_call')
    def on_start_roll_call(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        delegates = data.get('delegates', [])
        state_manager.set_delegate_list(room_code, delegates)
        state_manager.change_status(room_code, 'roll_call')
        state_manager.log_event(room_code, 'roll_call_started', f'{len(delegates)} delegates')
        _broadcast(room_code)
        sio.emit('roll_call_started', {}, room=room_code)

    @sio.on('mark_attendance')
    def on_mark_attendance(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        country = data.get('country')
        present = data.get('present', True)
        state_manager.mark_attendance(room_code, country, present)
        _broadcast(room_code)
        sio.emit('attendance_updated', {'country': country, 'present': present}, room=room_code)

    @sio.on('open_gsl')
    def on_open_gsl(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        speaker_time = data.get('speaker_time', 90)
        state_manager.open_gsl(room_code, speaker_time)
        state_manager.log_event(room_code, 'gsl_opened', f'Speaker time: {speaker_time}s')
        _broadcast(room_code)

    @sio.on('close_gsl')
    def on_close_gsl(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        state_manager.close_gsl(room_code)
        _broadcast(room_code)

    @sio.on('add_to_gsl')
    def on_add_to_gsl(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        country = data.get('country')
        state_manager.add_to_gsl(room_code, country)
        state_manager.log_event(room_code, 'added_to_gsl', country)
        _broadcast(room_code)

    @sio.on('remove_from_gsl')
    def on_remove_from_gsl(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        state_manager.remove_from_gsl(room_code, data.get('country'))
        _broadcast(room_code)

    @sio.on('reorder_gsl')
    def on_reorder_gsl(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        state_manager.reorder_gsl(room_code, data.get('speakers', []))
        _broadcast(room_code)

    @sio.on('next_speaker')
    def on_next_speaker(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        speaker = state_manager.next_speaker(room_code)
        state_manager.log_event(room_code, 'speaker_changed', speaker or 'end of list')
        _broadcast(room_code)
        sio.emit('current_speaker_changed', {'speaker': speaker}, room=room_code)

    @sio.on('start_speaker_timer')
    def on_start_speaker_timer(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        state_manager.start_timer(room_code, data.get('timer', 'gsl.timer'))
        _broadcast(room_code)

    @sio.on('pause_speaker_timer')
    def on_pause_speaker_timer(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        state_manager.pause_timer(room_code, data.get('timer', 'gsl.timer'), data.get('remaining', 0))
        _broadcast(room_code)

    @sio.on('reset_speaker_timer')
    def on_reset_speaker_timer(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        state_manager.reset_timer(room_code, data.get('timer', 'gsl.timer'), data.get('duration', 90))
        _broadcast(room_code)

    @sio.on('start_mod_caucus')
    def on_start_mod_caucus(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        state_manager.start_mod_caucus(room_code, data.get('topic', ''), data.get('total_time', 300), data.get('speaker_time', 60))
        state_manager.log_event(room_code, 'mod_caucus_started', data.get('topic', ''))
        _broadcast(room_code)

    @sio.on('end_mod_caucus')
    def on_end_mod_caucus(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        state_manager.end_mod_caucus(room_code)
        _broadcast(room_code)

    @sio.on('next_mod_caucus_speaker')
    def on_next_mod_caucus_speaker(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        speaker = state_manager.next_mod_caucus_speaker(room_code)
        _broadcast(room_code)
        sio.emit('current_speaker_changed', {'speaker': speaker, 'context': 'mod_caucus'}, room=room_code)

    @sio.on('start_unmod_caucus')
    def on_start_unmod_caucus(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        state_manager.start_unmod_caucus(room_code, data.get('duration', 300), data.get('purpose', ''))
        state_manager.log_event(room_code, 'unmod_caucus_started', data.get('purpose', ''))
        _broadcast(room_code)

    @sio.on('end_unmod_caucus')
    def on_end_unmod_caucus(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        state_manager.end_unmod_caucus(room_code)
        _broadcast(room_code)

    @sio.on('start_voting')
    def on_start_voting(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        state_manager.start_voting(room_code, data.get('motion', ''), data.get('type', 'procedural'), data.get('requires_majority', 'simple'))
        state_manager.log_event(room_code, 'voting_started', data.get('motion', ''))
        _broadcast(room_code)
        sio.emit('voting_started', {'motion': data.get('motion'), 'type': data.get('type')}, room=room_code)

    @sio.on('end_voting')
    def on_end_voting(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        result = state_manager.end_voting(room_code)
        state_manager.log_event(room_code, 'voting_ended', str(result))
        _broadcast(room_code)
        sio.emit('voting_ended', {'result': result}, room=room_code)

    @sio.on('accept_motion')
    def on_accept_motion(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        motion_id = data.get('motion_id')
        state_manager.decide_motion(room_code, motion_id, True)
        _broadcast(room_code)
        sio.emit('motion_decided', {'motion_id': motion_id, 'accepted': True}, room=room_code)

    @sio.on('reject_motion')
    def on_reject_motion(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        motion_id = data.get('motion_id')
        state_manager.decide_motion(room_code, motion_id, False)
        _broadcast(room_code)
        sio.emit('motion_decided', {'motion_id': motion_id, 'accepted': False}, room=room_code)

    @sio.on('grant_right_of_reply')
    def on_grant_right_of_reply(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        req_id = data.get('req_id')
        state_manager.decide_right_of_reply(room_code, req_id, True)
        _broadcast(room_code)
        sio.emit('right_of_reply_granted', {'req_id': req_id}, room=room_code)

    @sio.on('deny_right_of_reply')
    def on_deny_right_of_reply(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        state_manager.decide_right_of_reply(room_code, data.get('req_id'), False)
        _broadcast(room_code)

    @sio.on('recognize_point')
    def on_recognize_point(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        point_id = data.get('point_id')
        state_manager.address_point(room_code, point_id)
        _broadcast(room_code)
        sio.emit('point_addressed', {'point_id': point_id}, room=room_code)

    @sio.on('accept_working_paper')
    def on_accept_working_paper(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        state_manager.accept_working_paper(room_code, data.get('wp_id'))
        state_manager.log_event(room_code, 'working_paper_accepted', data.get('wp_id', ''))
        _broadcast(room_code)
        sio.emit('draft_resolution_introduced', {}, room=room_code)

    @sio.on('suspend_session')
    def on_suspend_session(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        state_manager.change_status(room_code, 'suspended')
        state_manager.log_event(room_code, 'session_suspended', '')
        _broadcast(room_code)
        sio.emit('committee_status_changed', {'status': 'suspended'}, room=room_code)

    @sio.on('resume_session')
    def on_resume_session(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        state_manager.change_status(room_code, 'gsl')
        state_manager.log_event(room_code, 'session_resumed', '')
        _broadcast(room_code)
        sio.emit('committee_status_changed', {'status': 'resumed'}, room=room_code)

    @sio.on('adjourn_session')
    def on_adjourn_session(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        state_manager.change_status(room_code, 'adjourned')
        state_manager.log_event(room_code, 'session_adjourned', '')
        if room_code in _timer_threads:
            _timer_threads[room_code]['active'] = False
        _broadcast(room_code)
        sio.emit('committee_status_changed', {'status': 'adjourned'}, room=room_code)

    @sio.on('send_announcement')
    def on_send_announcement(data):
        room_code, ok = require_chair(data)
        if not ok:
            emit('error', {'message': 'Unauthorized'}); return
        message = data.get('message', '')
        state_manager.send_announcement(room_code, message)
        _broadcast(room_code)
        sio.emit('announcement', {'message': message, 'timestamp': time.time()}, room=room_code)

    # === DELEGATE EVENTS ===

    @sio.on('request_to_speak')
    def on_request_to_speak(data):
        room_code = data.get('room_code', '').upper()
        country = data.get('country', '')
        context = data.get('context', 'gsl')
        if context == 'mod_caucus':
            state_manager.add_to_mod_caucus(room_code, country)
        else:
            state_manager.add_to_gsl(room_code, country)
        state_manager.log_event(room_code, 'request_to_speak', f'{country} ({context})')
        _broadcast(room_code)

    @sio.on('withdraw_from_list')
    def on_withdraw_from_list(data):
        room_code = data.get('room_code', '').upper()
        state_manager.remove_from_gsl(room_code, data.get('country', ''))
        _broadcast(room_code)

    @sio.on('cast_vote')
    def on_cast_vote(data):
        room_code = data.get('room_code', '').upper()
        country = data.get('country', '')
        vote = data.get('vote', '')
        state_manager.cast_vote(room_code, country, vote)
        _broadcast(room_code)
        sio.emit('vote_cast', {'country': country, 'vote': vote}, room=room_code)

    @sio.on('propose_motion')
    def on_propose_motion(data):
        room_code = data.get('room_code', '').upper()
        proposer = data.get('country', '')
        motion_type = data.get('type', '')
        details = data.get('details', {})
        motion_id = state_manager.propose_motion(room_code, motion_type, proposer, details)
        state_manager.log_event(room_code, 'motion_proposed', f'{proposer}: {motion_type}')
        _broadcast(room_code)
        sio.emit('motion_proposed', {'motion_id': motion_id, 'type': motion_type, 'proposer': proposer}, room=room_code)

    @sio.on('second_motion')
    def on_second_motion(data):
        room_code = data.get('room_code', '').upper()
        state_manager.second_motion(room_code, data.get('motion_id', ''), data.get('country', ''))
        _broadcast(room_code)
        sio.emit('motion_seconded', {'motion_id': data.get('motion_id'), 'country': data.get('country')}, room=room_code)

    @sio.on('raise_point')
    def on_raise_point(data):
        room_code = data.get('room_code', '').upper()
        country = data.get('country', '')
        point_type = data.get('type', 'Point of Order')
        details = data.get('details', '')
        point_id = state_manager.raise_point(room_code, point_type, country, details)
        state_manager.log_event(room_code, 'point_raised', f'{country}: {point_type}')
        _broadcast(room_code)
        sio.emit('point_raised', {'point_id': point_id, 'type': point_type, 'country': country}, room=room_code)

    @sio.on('request_right_of_reply')
    def on_request_right_of_reply(data):
        room_code = data.get('room_code', '').upper()
        country = data.get('country', '')
        regarding = data.get('regarding', '')
        req_id = state_manager.request_right_of_reply(room_code, country, regarding)
        _broadcast(room_code)
        sio.emit('right_of_reply_requested', {'req_id': req_id, 'country': country}, room=room_code)

    @sio.on('submit_working_paper')
    def on_submit_working_paper(data):
        room_code = data.get('room_code', '').upper()
        wp_id = state_manager.submit_working_paper(
            room_code,
            data.get('title', ''),
            data.get('sponsors', []),
            data.get('signatories', []),
            data.get('content', '')
        )
        state_manager.log_event(room_code, 'working_paper_submitted', data.get('title', ''))
        _broadcast(room_code)
        sio.emit('working_paper_submitted', {'wp_id': wp_id, 'title': data.get('title')}, room=room_code)

    @sio.on('sign_document')
    def on_sign_document(data):
        room_code = data.get('room_code', '').upper()
        state_manager.sign_document(room_code, data.get('doc_type', 'working_papers'), data.get('doc_id', ''), data.get('country', ''))
        _broadcast(room_code)
