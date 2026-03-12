"""
Integration tests for session data isolation
Tests that sessions maintain separate data and don't interfere
"""
import pytest
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


class TestSessionIsolation:
    """Test session data isolation and independence"""

    def test_sessions_have_isolated_directories(self, temp_data_dir):
        """Test that each session has its own data directories"""
        from managers.session_manager import SessionManager

        manager = SessionManager(data_dir=str(temp_data_dir))

        session1 = manager.create_session("MUN 1", "First", "2025-01-01")
        session2 = manager.create_session("MUN 2", "Second", "2025-02-01")

        session1_dir = temp_data_dir / session1['id']
        session2_dir = temp_data_dir / session2['id']

        assert session1_dir.exists()
        assert session2_dir.exists()
        assert session1_dir != session2_dir

        # Verify subdirectories
        for subdir in ['notes', 'speeches', 'chats', 'config']:
            assert (session1_dir / subdir).exists()
            assert (session2_dir / subdir).exists()

    def test_notes_are_session_scoped(self, temp_data_dir):
        """Test that notes in one session don't appear in another"""
        from managers.session_manager import SessionManager
        from managers.notes_manager import NotesManager

        session_manager = SessionManager(data_dir=str(temp_data_dir))

        session1 = session_manager.create_session("MUN 1", "First", "2025-01-01")
        session2 = session_manager.create_session("MUN 2", "Second", "2025-02-01")

        # Create notes manager for session 1
        notes_dir_1 = session_manager.get_session_notes_dir(session1['id'])
        notes_manager_1 = NotesManager(data_dir=str(notes_dir_1))

        # Create notes manager for session 2
        notes_dir_2 = session_manager.get_session_notes_dir(session2['id'])
        notes_manager_2 = NotesManager(data_dir=str(notes_dir_2))

        # Create note in session 1
        note1 = notes_manager_1.create_note("Session 1 Note", "Content for session 1")

        # Create note in session 2
        note2 = notes_manager_2.create_note("Session 2 Note", "Content for session 2")

        # Verify isolation
        session1_notes = notes_manager_1.get_all_notes()
        session2_notes = notes_manager_2.get_all_notes()

        assert len(session1_notes) == 1
        assert len(session2_notes) == 1
        assert session1_notes[0]['title'] == "Session 1 Note"
        assert session2_notes[0]['title'] == "Session 2 Note"

    def test_config_is_session_scoped(self, temp_data_dir):
        """Test that configuration is isolated per session"""
        from managers.session_manager import SessionManager
        from managers.config_manager import ConfigManager

        session_manager = SessionManager(data_dir=str(temp_data_dir))

        session1 = session_manager.create_session("MUN 1", "First", "2025-01-01")
        session2 = session_manager.create_session("MUN 2", "Second", "2025-02-01")

        # Config for session 1
        config_dir_1 = session_manager.get_session_dir(session1['id']) / 'config'
        config_manager_1 = ConfigManager(data_dir=str(config_dir_1))
        config_manager_1.set_delegate_info({'country': 'USA', 'committee': 'UNSC'})

        # Config for session 2
        config_dir_2 = session_manager.get_session_dir(session2['id']) / 'config'
        config_manager_2 = ConfigManager(data_dir=str(config_dir_2))
        config_manager_2.set_delegate_info({'country': 'China', 'committee': 'GA'})

        # Verify isolation
        config1 = config_manager_1.get_config()
        config2 = config_manager_2.get_config()

        assert config1['my_delegate']['country'] == 'USA'
        assert config2['my_delegate']['country'] == 'China'

    def test_session_memory_import_preserves_target_data(self, temp_data_dir):
        """Test that importing session memory doesn't overwrite target session data"""
        from managers.session_manager import SessionManager

        manager = SessionManager(data_dir=str(temp_data_dir))

        source_session = manager.create_session("Source MUN", "Source", "2025-01-01")
        target_session = manager.create_session("Target MUN", "Target", "2025-02-01")

        # End source with memory
        manager.end_session(
            source_session['id'],
            summary="Source summary",
            compressed_memory="Source compressed memory"
        )

        # Import to target
        updated_target = manager.import_session_memory(
            target_session['id'],
            source_session['id']
        )

        # Verify target session still has its own identity
        assert updated_target['name'] == "Target MUN"
        assert updated_target['description'] == "Target"
        assert updated_target['status'] == 'active'  # Still active, not ended
        assert source_session['id'] in updated_target['imported_from']

    def test_deleting_session_doesnt_affect_others(self, temp_data_dir):
        """Test that deleting one session doesn't affect other sessions"""
        from managers.session_manager import SessionManager

        manager = SessionManager(data_dir=str(temp_data_dir))

        session1 = manager.create_session("MUN 1", "First", "2025-01-01")
        session2 = manager.create_session("MUN 2", "Second", "2025-02-01")
        session3 = manager.create_session("MUN 3", "Third", "2025-03-01")

        # Delete session 2
        manager.delete_session(session2['id'])

        # Verify sessions 1 and 3 still exist
        all_sessions = manager.get_all_sessions()
        session_ids = [s['id'] for s in all_sessions]

        assert session1['id'] in session_ids
        assert session2['id'] not in session_ids
        assert session3['id'] in session_ids
