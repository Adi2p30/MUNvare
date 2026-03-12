"""
Unit tests for Session Manager
Tests session CRUD operations and session isolation
"""
import pytest
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))


class TestSessionManager:
    """Test Session Manager functionality"""

    def test_create_session(self, temp_data_dir):
        """Test creating a new MUN session"""
        from managers.session_manager import SessionManager

        manager = SessionManager(data_dir=str(temp_data_dir))

        session = manager.create_session(
            name="Test MUN 2025",
            description="Test conference",
            dates="2025-01-01 to 2025-01-03"
        )

        assert session is not None
        assert session['name'] == "Test MUN 2025"
        assert session['status'] == 'active'
        assert 'id' in session

        # Verify session directory was created
        session_dir = temp_data_dir / session['id']
        assert session_dir.exists()
        assert (session_dir / 'notes').exists()
        assert (session_dir / 'speeches').exists()
        assert (session_dir / 'chats').exists()
        assert (session_dir / 'config').exists()

    def test_get_all_sessions(self, temp_data_dir):
        """Test retrieving all sessions"""
        from managers.session_manager import SessionManager

        manager = SessionManager(data_dir=str(temp_data_dir))

        # Create multiple sessions
        session1 = manager.create_session("MUN 1", "First", "2025-01-01")
        session2 = manager.create_session("MUN 2", "Second", "2025-02-01")

        sessions = manager.get_all_sessions()

        assert len(sessions) == 2
        assert any(s['name'] == "MUN 1" for s in sessions)
        assert any(s['name'] == "MUN 2" for s in sessions)

    def test_get_session_by_id(self, temp_data_dir):
        """Test retrieving a specific session"""
        from managers.session_manager import SessionManager

        manager = SessionManager(data_dir=str(temp_data_dir))

        created_session = manager.create_session("Test MUN", "Desc", "2025-01-01")
        session_id = created_session['id']

        retrieved_session = manager.get_session(session_id)

        assert retrieved_session is not None
        assert retrieved_session['id'] == session_id
        assert retrieved_session['name'] == "Test MUN"

    def test_update_session(self, temp_data_dir):
        """Test updating session information"""
        from managers.session_manager import SessionManager

        manager = SessionManager(data_dir=str(temp_data_dir))

        session = manager.create_session("Old Name", "Old desc", "2025-01-01")
        session_id = session['id']

        updated = manager.update_session(
            session_id,
            name="New Name",
            description="New desc",
            dates="2025-02-01"
        )

        assert updated['name'] == "New Name"
        assert updated['description'] == "New desc"
        assert updated['dates'] == "2025-02-01"

    def test_delete_session(self, temp_data_dir):
        """Test deleting a session"""
        from managers.session_manager import SessionManager

        manager = SessionManager(data_dir=str(temp_data_dir))

        session = manager.create_session("Test MUN", "Desc", "2025-01-01")
        session_id = session['id']

        manager.delete_session(session_id)

        # Verify session is removed
        sessions = manager.get_all_sessions()
        assert not any(s['id'] == session_id for s in sessions)

    def test_end_session(self, temp_data_dir):
        """Test ending a session with summary"""
        from managers.session_manager import SessionManager

        manager = SessionManager(data_dir=str(temp_data_dir))

        session = manager.create_session("Test MUN", "Desc", "2025-01-01")
        session_id = session['id']

        ended_session = manager.end_session(
            session_id,
            summary="Great conference!",
            compressed_memory="Key memories..."
        )

        assert ended_session['status'] == 'ended'
        assert ended_session['summary'] == "Great conference!"
        assert ended_session['ended_at'] is not None

    def test_get_active_sessions(self, temp_data_dir):
        """Test retrieving only active sessions"""
        from managers.session_manager import SessionManager

        manager = SessionManager(data_dir=str(temp_data_dir))

        active_session = manager.create_session("Active MUN", "Desc", "2025-01-01")
        ended_session = manager.create_session("Ended MUN", "Desc", "2025-01-01")
        manager.end_session(ended_session['id'], summary="Done")

        active_sessions = manager.get_active_sessions()

        assert len(active_sessions) == 1
        assert active_sessions[0]['id'] == active_session['id']

    def test_get_ended_sessions(self, temp_data_dir):
        """Test retrieving only ended sessions"""
        from managers.session_manager import SessionManager

        manager = SessionManager(data_dir=str(temp_data_dir))

        active_session = manager.create_session("Active MUN", "Desc", "2025-01-01")
        ended_session = manager.create_session("Ended MUN", "Desc", "2025-01-01")
        manager.end_session(ended_session['id'], summary="Done")

        ended_sessions = manager.get_ended_sessions()

        assert len(ended_sessions) == 1
        assert ended_sessions[0]['id'] == ended_session['id']

    def test_session_directories_isolation(self, temp_data_dir):
        """Test that each session has isolated data directories"""
        from managers.session_manager import SessionManager

        manager = SessionManager(data_dir=str(temp_data_dir))

        session1 = manager.create_session("MUN 1", "Desc", "2025-01-01")
        session2 = manager.create_session("MUN 2", "Desc", "2025-01-01")

        session1_dir = manager.get_session_notes_dir(session1['id'])
        session2_dir = manager.get_session_notes_dir(session2['id'])

        assert session1_dir != session2_dir
        assert session1_dir.exists()
        assert session2_dir.exists()

    def test_import_session_memory(self, temp_data_dir):
        """Test importing memory from one session to another"""
        from managers.session_manager import SessionManager

        manager = SessionManager(data_dir=str(temp_data_dir))

        source_session = manager.create_session("Source MUN", "Desc", "2025-01-01")
        target_session = manager.create_session("Target MUN", "Desc", "2025-02-01")

        # End source session with memory
        manager.end_session(
            source_session['id'],
            summary="Source summary",
            compressed_memory="Source memory"
        )

        # Import to target
        updated_target = manager.import_session_memory(
            target_session['id'],
            source_session['id']
        )

        assert source_session['id'] in updated_target['imported_from']
