"""
Session Manager - Handles MUN session/save management
Each session represents a different MUN conference with its own data
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path

class SessionManager:
    def __init__(self, data_dir='data/sessions'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_file = self.data_dir / 'sessions.json'
        self._ensure_sessions_file()

    def _ensure_sessions_file(self):
        """Create sessions file if it doesn't exist"""
        if not self.sessions_file.exists():
            self.sessions_file.write_text(json.dumps([]))

    def _load_sessions(self):
        """Load all sessions from file"""
        try:
            with open(self.sessions_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading sessions: {e}")
            return []

    def _save_sessions(self, sessions):
        """Save sessions to file"""
        try:
            with open(self.sessions_file, 'w') as f:
                json.dump(sessions, f, indent=2)
        except Exception as e:
            print(f"Error saving sessions: {e}")

    def create_session(self, name, description='', dates=''):
        """Create a new MUN session"""
        session_id = str(uuid.uuid4())

        session = {
            'id': session_id,
            'name': name,
            'description': description,
            'dates': dates,
            'status': 'active',  # active or ended
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat(),
            'ended_at': None,
            'summary': None,
            'compressed_memory': None,
            'imported_from': []  # List of session IDs that were imported
        }

        # Create session directory structure
        session_dir = self.data_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for session data
        (session_dir / 'notes').mkdir(exist_ok=True)
        (session_dir / 'speeches').mkdir(exist_ok=True)
        (session_dir / 'chats').mkdir(exist_ok=True)
        (session_dir / 'config').mkdir(exist_ok=True)

        # Initialize empty config
        config = {
            'my_delegate': {},
            'other_delegates': [],
            'committee_info': {}
        }

        with open(session_dir / 'config' / 'config.json', 'w') as f:
            json.dump(config, f, indent=2)

        # Add to sessions list
        sessions = self._load_sessions()
        sessions.append(session)
        self._save_sessions(sessions)

        return session

    def get_all_sessions(self):
        """Get all MUN sessions sorted by last accessed"""
        sessions = self._load_sessions()
        # Sort by last accessed (most recent first)
        sessions.sort(key=lambda x: x.get('last_accessed', x.get('created_at')), reverse=True)
        return sessions

    def get_session(self, session_id):
        """Get a specific session by ID"""
        sessions = self._load_sessions()
        for session in sessions:
            if session['id'] == session_id:
                # Update last accessed
                session['last_accessed'] = datetime.now().isoformat()
                self._save_sessions(sessions)
                return session
        return None

    def update_session(self, session_id, name=None, description=None, dates=None):
        """Update session metadata"""
        sessions = self._load_sessions()

        for session in sessions:
            if session['id'] == session_id:
                if name is not None:
                    session['name'] = name
                if description is not None:
                    session['description'] = description
                if dates is not None:
                    session['dates'] = dates
                session['updated_at'] = datetime.now().isoformat()
                self._save_sessions(sessions)
                return session

        return None

    def delete_session(self, session_id):
        """Delete a session and all its data"""
        sessions = self._load_sessions()

        # Remove from sessions list
        sessions = [s for s in sessions if s['id'] != session_id]
        self._save_sessions(sessions)

        # Delete session directory
        import shutil
        session_dir = self.data_dir / session_id
        if session_dir.exists():
            shutil.rmtree(session_dir)

        return True

    def get_session_dir(self, session_id):
        """Get the directory path for a session"""
        return self.data_dir / session_id

    def get_session_notes_dir(self, session_id):
        """Get the notes directory for a session"""
        return self.data_dir / session_id / 'notes'

    def get_session_speeches_dir(self, session_id):
        """Get the speeches directory for a session"""
        return self.data_dir / session_id / 'speeches'

    def get_session_chats_dir(self, session_id):
        """Get the chats directory for a session"""
        return self.data_dir / session_id / 'chats'

    def get_session_config_file(self, session_id):
        """Get the config file path for a session"""
        return self.data_dir / session_id / 'config' / 'config.json'

    def end_session(self, session_id, summary=None, compressed_memory=None):
        """Mark a session as ended and store summary"""
        sessions = self._load_sessions()

        for session in sessions:
            if session['id'] == session_id:
                session['status'] = 'ended'
                session['ended_at'] = datetime.now().isoformat()
                session['updated_at'] = datetime.now().isoformat()
                if summary:
                    session['summary'] = summary
                if compressed_memory:
                    session['compressed_memory'] = compressed_memory
                self._save_sessions(sessions)
                return session

        return None

    def get_active_sessions(self):
        """Get all active (not ended) sessions"""
        sessions = self._load_sessions()
        active = [s for s in sessions if s.get('status', 'active') == 'active']
        active.sort(key=lambda x: x.get('last_accessed', x.get('created_at')), reverse=True)
        return active

    def get_ended_sessions(self):
        """Get all ended (past) sessions"""
        sessions = self._load_sessions()
        ended = [s for s in sessions if s.get('status') == 'ended']
        ended.sort(key=lambda x: x.get('ended_at', x.get('created_at')), reverse=True)
        return ended

    def import_memory_to_session(self, target_session_id, source_session_id):
        """Import compressed memory from one session to another"""
        sessions = self._load_sessions()

        target_session = None
        source_memory = None

        # Find sessions
        for session in sessions:
            if session['id'] == target_session_id:
                target_session = session
            if session['id'] == source_session_id:
                source_memory = session.get('compressed_memory')

        if not target_session or not source_memory:
            return None

        # Track import
        if 'imported_from' not in target_session:
            target_session['imported_from'] = []

        if source_session_id not in target_session['imported_from']:
            target_session['imported_from'].append(source_session_id)

        # Merge memories if target already has memory
        if target_session.get('compressed_memory'):
            # Will be merged by AI service
            target_session['compressed_memory'] = {
                'existing': target_session['compressed_memory'],
                'imported': source_memory,
                'needs_merge': True
            }
        else:
            target_session['compressed_memory'] = source_memory

        target_session['updated_at'] = datetime.now().isoformat()
        self._save_sessions(sessions)

        return target_session

    def detach_imported_memory(self, session_id, source_session_id):
        """Remove imported memory from a session"""
        sessions = self._load_sessions()

        for session in sessions:
            if session['id'] == session_id:
                if 'imported_from' in session and source_session_id in session['imported_from']:
                    session['imported_from'].remove(source_session_id)

                # If this was the only import, clear the memory
                if not session.get('imported_from'):
                    session['compressed_memory'] = None

                session['updated_at'] = datetime.now().isoformat()
                self._save_sessions(sessions)
                return session

        return None
