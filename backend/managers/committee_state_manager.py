import json
import os
import time
import uuid
from threading import Lock
from typing import Dict, List, Optional


class CommitteeStateManager:
    def __init__(self, data_dir='data/committee_states'):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._rooms: Dict[str, dict] = {}
        self._lock = Lock()

    def _default_state(self, room_code: str, committee_name: str, agenda: str, chair_token: str) -> dict:
        return {
            'room_code': room_code,
            'committee_name': committee_name,
            'agenda': agenda,
            'chair_token': chair_token,
            'status': 'roll_call',
            'created_at': time.time(),
            'delegates': [],
            'gsl': {
                'open': False,
                'speakers': [],
                'current_index': -1,
                'speaker_time': 90,
                'timer': {'running': False, 'remaining': 90, 'started_at': None}
            },
            'mod_caucus': {
                'active': False,
                'topic': '',
                'total_time': 300,
                'speaker_time': 60,
                'speakers': [],
                'current_index': -1,
                'timer': {'running': False, 'remaining': 300, 'started_at': None},
                'speaker_timer': {'running': False, 'remaining': 60, 'started_at': None}
            },
            'unmod_caucus': {
                'active': False,
                'duration': 300,
                'purpose': '',
                'timer': {'running': False, 'remaining': 300, 'started_at': None}
            },
            'voting': {
                'active': False,
                'motion': '',
                'type': 'procedural',
                'votes': {},
                'status': 'pending',
                'requires_majority': 'simple',
                'result': None
            },
            'motions_queue': [],
            'points_queue': [],
            'right_of_reply_queue': [],
            'working_papers': [],
            'draft_resolutions': [],
            'amendments': [],
            'rules': [],
            'announcements': [],
            'session_log': []
        }

    def create_room(self, committee_name: str, agenda: str) -> tuple:
        with self._lock:
            room_code = uuid.uuid4().hex[:6].upper()
            chair_token = uuid.uuid4().hex
            state = self._default_state(room_code, committee_name, agenda, chair_token)
            self._rooms[room_code] = state
            self._persist(room_code)
            return room_code, chair_token

    def get_state(self, room_code: str) -> Optional[dict]:
        with self._lock:
            return self._rooms.get(room_code)

    def get_public_state(self, room_code: str) -> Optional[dict]:
        state = self.get_state(room_code)
        if not state:
            return None
        public = dict(state)
        public.pop('chair_token', None)
        return public

    def verify_chair(self, room_code: str, token: str) -> bool:
        state = self.get_state(room_code)
        return state is not None and state.get('chair_token') == token

    def log_event(self, room_code: str, event_type: str, details: str):
        with self._lock:
            if room_code in self._rooms:
                self._rooms[room_code]['session_log'].append({
                    'timestamp': time.time(),
                    'event_type': event_type,
                    'details': details
                })

    # Attendance
    def set_delegate_list(self, room_code: str, delegates: List[str]) -> bool:
        with self._lock:
            if room_code not in self._rooms:
                return False
            existing = {d['country'] for d in self._rooms[room_code]['delegates']}
            for country in delegates:
                if country not in existing:
                    self._rooms[room_code]['delegates'].append({
                        'country': country,
                        'present': False,
                        'connected': False,
                        'speaking_time_used': 0,
                        'sid': None
                    })
            self._persist(room_code)
            return True

    def mark_attendance(self, room_code: str, country: str, present: bool) -> bool:
        with self._lock:
            if room_code not in self._rooms:
                return False
            for d in self._rooms[room_code]['delegates']:
                if d['country'] == country:
                    d['present'] = present
                    self._persist(room_code)
                    return True
            return False

    def set_delegate_connected(self, room_code: str, country: str, sid: str, connected: bool):
        with self._lock:
            if room_code not in self._rooms:
                return
            found = False
            for d in self._rooms[room_code]['delegates']:
                if d['country'] == country:
                    d['connected'] = connected
                    d['sid'] = sid if connected else None
                    found = True
                    break
            if not found and connected:
                self._rooms[room_code]['delegates'].append({
                    'country': country,
                    'present': False,
                    'connected': True,
                    'speaking_time_used': 0,
                    'sid': sid
                })
            self._persist(room_code)

    # GSL
    def open_gsl(self, room_code: str, speaker_time: int = 90) -> bool:
        with self._lock:
            if room_code not in self._rooms:
                return False
            self._rooms[room_code]['gsl']['open'] = True
            self._rooms[room_code]['gsl']['speaker_time'] = speaker_time
            self._rooms[room_code]['status'] = 'gsl'
            self._persist(room_code)
            return True

    def close_gsl(self, room_code: str) -> bool:
        with self._lock:
            if room_code not in self._rooms:
                return False
            self._rooms[room_code]['gsl']['open'] = False
            self._persist(room_code)
            return True

    def add_to_gsl(self, room_code: str, country: str) -> bool:
        with self._lock:
            if room_code not in self._rooms:
                return False
            gsl = self._rooms[room_code]['gsl']
            if country not in gsl['speakers']:
                gsl['speakers'].append(country)
                self._persist(room_code)
                return True
            return False

    def remove_from_gsl(self, room_code: str, country: str) -> bool:
        with self._lock:
            if room_code not in self._rooms:
                return False
            gsl = self._rooms[room_code]['gsl']
            if country in gsl['speakers']:
                gsl['speakers'].remove(country)
                self._persist(room_code)
                return True
            return False

    def reorder_gsl(self, room_code: str, speakers: List[str]) -> bool:
        with self._lock:
            if room_code not in self._rooms:
                return False
            self._rooms[room_code]['gsl']['speakers'] = speakers
            self._persist(room_code)
            return True

    def next_speaker(self, room_code: str) -> Optional[str]:
        with self._lock:
            if room_code not in self._rooms:
                return None
            gsl = self._rooms[room_code]['gsl']
            gsl['current_index'] += 1
            if gsl['current_index'] < len(gsl['speakers']):
                speaker = gsl['speakers'][gsl['current_index']]
                gsl['timer'] = {'running': False, 'remaining': gsl['speaker_time'], 'started_at': None}
                self._persist(room_code)
                return speaker
            return None

    def _get_timer(self, state: dict, timer_path: str) -> Optional[dict]:
        parts = timer_path.split('.')
        obj = state
        for p in parts[:-1]:
            obj = obj.get(p, {})
        return obj.get(parts[-1])

    def start_timer(self, room_code: str, timer_path: str) -> bool:
        with self._lock:
            if room_code not in self._rooms:
                return False
            parts = timer_path.split('.')
            obj = self._rooms[room_code]
            for p in parts[:-1]:
                obj = obj[p]
            obj[parts[-1]]['running'] = True
            obj[parts[-1]]['started_at'] = time.time()
            self._persist(room_code)
            return True

    def pause_timer(self, room_code: str, timer_path: str, remaining: int) -> bool:
        with self._lock:
            if room_code not in self._rooms:
                return False
            parts = timer_path.split('.')
            obj = self._rooms[room_code]
            for p in parts[:-1]:
                obj = obj[p]
            timer = obj[parts[-1]]
            timer['running'] = False
            timer['remaining'] = remaining
            timer['started_at'] = None
            self._persist(room_code)
            return True

    def reset_timer(self, room_code: str, timer_path: str, duration: int) -> bool:
        with self._lock:
            if room_code not in self._rooms:
                return False
            parts = timer_path.split('.')
            obj = self._rooms[room_code]
            for p in parts[:-1]:
                obj = obj[p]
            obj[parts[-1]] = {'running': False, 'remaining': duration, 'started_at': None}
            self._persist(room_code)
            return True

    # Mod Caucus
    def start_mod_caucus(self, room_code: str, topic: str, total_time: int, speaker_time: int) -> bool:
        with self._lock:
            if room_code not in self._rooms:
                return False
            self._rooms[room_code]['mod_caucus'] = {
                'active': True,
                'topic': topic,
                'total_time': total_time,
                'speaker_time': speaker_time,
                'speakers': [],
                'current_index': -1,
                'timer': {'running': False, 'remaining': total_time, 'started_at': None},
                'speaker_timer': {'running': False, 'remaining': speaker_time, 'started_at': None}
            }
            self._rooms[room_code]['status'] = 'mod_caucus'
            self._persist(room_code)
            return True

    def end_mod_caucus(self, room_code: str) -> bool:
        with self._lock:
            if room_code not in self._rooms:
                return False
            self._rooms[room_code]['mod_caucus']['active'] = False
            self._rooms[room_code]['status'] = 'gsl'
            self._persist(room_code)
            return True

    def add_to_mod_caucus(self, room_code: str, country: str) -> bool:
        with self._lock:
            if room_code not in self._rooms:
                return False
            speakers = self._rooms[room_code]['mod_caucus']['speakers']
            if country not in speakers:
                speakers.append(country)
                self._persist(room_code)
                return True
            return False

    def next_mod_caucus_speaker(self, room_code: str) -> Optional[str]:
        with self._lock:
            if room_code not in self._rooms:
                return None
            mc = self._rooms[room_code]['mod_caucus']
            mc['current_index'] += 1
            if mc['current_index'] < len(mc['speakers']):
                speaker = mc['speakers'][mc['current_index']]
                mc['speaker_timer'] = {'running': False, 'remaining': mc['speaker_time'], 'started_at': None}
                self._persist(room_code)
                return speaker
            return None

    # Unmod Caucus
    def start_unmod_caucus(self, room_code: str, duration: int, purpose: str) -> bool:
        with self._lock:
            if room_code not in self._rooms:
                return False
            self._rooms[room_code]['unmod_caucus'] = {
                'active': True,
                'duration': duration,
                'purpose': purpose,
                'timer': {'running': False, 'remaining': duration, 'started_at': None}
            }
            self._rooms[room_code]['status'] = 'unmod_caucus'
            self._persist(room_code)
            return True

    def end_unmod_caucus(self, room_code: str) -> bool:
        with self._lock:
            if room_code not in self._rooms:
                return False
            self._rooms[room_code]['unmod_caucus']['active'] = False
            self._rooms[room_code]['status'] = 'gsl'
            self._persist(room_code)
            return True

    # Voting
    def start_voting(self, room_code: str, motion: str, vote_type: str = 'procedural', requires_majority: str = 'simple') -> bool:
        with self._lock:
            if room_code not in self._rooms:
                return False
            self._rooms[room_code]['voting'] = {
                'active': True,
                'motion': motion,
                'type': vote_type,
                'votes': {},
                'status': 'open',
                'requires_majority': requires_majority,
                'result': None
            }
            self._rooms[room_code]['status'] = 'voting'
            self._persist(room_code)
            return True

    def cast_vote(self, room_code: str, country: str, vote: str) -> bool:
        with self._lock:
            if room_code not in self._rooms:
                return False
            voting = self._rooms[room_code]['voting']
            if voting.get('active') and voting.get('status') == 'open':
                voting['votes'][country] = vote
                self._persist(room_code)
                return True
            return False

    def end_voting(self, room_code: str) -> dict:
        with self._lock:
            if room_code not in self._rooms:
                return {}
            voting = self._rooms[room_code]['voting']
            voting['active'] = False
            voting['status'] = 'closed'
            votes = voting['votes']
            result = {
                'for': sum(1 for v in votes.values() if v == 'for'),
                'against': sum(1 for v in votes.values() if v == 'against'),
                'abstain': sum(1 for v in votes.values() if v == 'abstain'),
                'pass': sum(1 for v in votes.values() if v == 'pass'),
                'with_rights': sum(1 for v in votes.values() if v == 'with_rights'),
            }
            voting['result'] = result
            self._rooms[room_code]['status'] = 'gsl'
            self._persist(room_code)
            return result

    # Motions
    def propose_motion(self, room_code: str, motion_type: str, proposer: str, details: dict) -> Optional[str]:
        with self._lock:
            if room_code not in self._rooms:
                return None
            motion_id = uuid.uuid4().hex[:8]
            self._rooms[room_code]['motions_queue'].append({
                'id': motion_id,
                'type': motion_type,
                'proposer': proposer,
                'details': details,
                'seconds': [],
                'status': 'proposed'
            })
            self._persist(room_code)
            return motion_id

    def second_motion(self, room_code: str, motion_id: str, country: str) -> bool:
        with self._lock:
            if room_code not in self._rooms:
                return False
            for m in self._rooms[room_code]['motions_queue']:
                if m['id'] == motion_id and country not in m['seconds']:
                    m['seconds'].append(country)
                    self._persist(room_code)
                    return True
            return False

    def decide_motion(self, room_code: str, motion_id: str, accepted: bool) -> bool:
        with self._lock:
            if room_code not in self._rooms:
                return False
            for m in self._rooms[room_code]['motions_queue']:
                if m['id'] == motion_id:
                    m['status'] = 'accepted' if accepted else 'rejected'
                    self._persist(room_code)
                    return True
            return False

    # Points
    def raise_point(self, room_code: str, point_type: str, country: str, details: str) -> str:
        with self._lock:
            point_id = uuid.uuid4().hex[:8]
            if room_code in self._rooms:
                self._rooms[room_code]['points_queue'].append({
                    'id': point_id,
                    'type': point_type,
                    'country': country,
                    'details': details,
                    'status': 'pending'
                })
                self._persist(room_code)
            return point_id

    def address_point(self, room_code: str, point_id: str) -> bool:
        with self._lock:
            if room_code not in self._rooms:
                return False
            for p in self._rooms[room_code]['points_queue']:
                if p['id'] == point_id:
                    p['status'] = 'addressed'
                    self._persist(room_code)
                    return True
            return False

    # Right of Reply
    def request_right_of_reply(self, room_code: str, country: str, regarding: str) -> str:
        with self._lock:
            req_id = uuid.uuid4().hex[:8]
            if room_code in self._rooms:
                self._rooms[room_code]['right_of_reply_queue'].append({
                    'id': req_id,
                    'country': country,
                    'regarding': regarding,
                    'status': 'pending'
                })
                self._persist(room_code)
            return req_id

    def decide_right_of_reply(self, room_code: str, req_id: str, granted: bool) -> bool:
        with self._lock:
            if room_code not in self._rooms:
                return False
            for r in self._rooms[room_code]['right_of_reply_queue']:
                if r['id'] == req_id:
                    r['status'] = 'granted' if granted else 'denied'
                    self._persist(room_code)
                    return True
            return False

    # Working Papers
    def submit_working_paper(self, room_code: str, title: str, sponsors: List[str], signatories: List[str], content: str = '') -> Optional[str]:
        with self._lock:
            if room_code not in self._rooms:
                return None
            wp_id = uuid.uuid4().hex[:8]
            self._rooms[room_code]['working_papers'].append({
                'id': wp_id,
                'title': title,
                'sponsors': sponsors,
                'signatories': signatories,
                'content': content,
                'status': 'submitted'
            })
            self._persist(room_code)
            return wp_id

    def sign_document(self, room_code: str, doc_type: str, doc_id: str, country: str) -> bool:
        with self._lock:
            if room_code not in self._rooms:
                return False
            docs = self._rooms[room_code].get(doc_type, [])
            for doc in docs:
                if doc['id'] == doc_id and country not in doc['signatories']:
                    doc['signatories'].append(country)
                    self._persist(room_code)
                    return True
            return False

    def accept_working_paper(self, room_code: str, wp_id: str) -> bool:
        with self._lock:
            if room_code not in self._rooms:
                return False
            for wp in self._rooms[room_code]['working_papers']:
                if wp['id'] == wp_id:
                    wp['status'] = 'accepted'
                    dr = dict(wp)
                    dr['id'] = uuid.uuid4().hex[:8]
                    dr['clauses'] = []
                    dr['status'] = 'introduced'
                    self._rooms[room_code]['draft_resolutions'].append(dr)
                    self._persist(room_code)
                    return True
            return False

    # Session control
    def change_status(self, room_code: str, status: str) -> bool:
        with self._lock:
            if room_code not in self._rooms:
                return False
            self._rooms[room_code]['status'] = status
            self._persist(room_code)
            return True

    def send_announcement(self, room_code: str, message: str):
        with self._lock:
            if room_code in self._rooms:
                self._rooms[room_code]['announcements'].append({
                    'timestamp': time.time(),
                    'message': message
                })
                self._persist(room_code)

    def _persist(self, room_code: str):
        path = os.path.join(self.data_dir, f'{room_code}.json')
        tmp_path = path + '.tmp'
        try:
            with open(tmp_path, 'w') as f:
                json.dump(self._rooms[room_code], f)
            os.replace(tmp_path, path)
        except Exception:
            pass

    def load_room(self, room_code: str) -> bool:
        path = os.path.join(self.data_dir, f'{room_code}.json')
        if os.path.exists(path):
            with open(path) as f:
                self._rooms[room_code] = json.load(f)
            return True
        return False
