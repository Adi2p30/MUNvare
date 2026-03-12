"""
Unit tests for Notes Manager
Tests note CRUD operations, folders, and templates
"""
import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))


class TestNotesManager:
    """Test Notes Manager functionality"""

    def test_create_note(self, temp_data_dir):
        """Test creating a new note"""
        from managers.notes_manager import NotesManager

        manager = NotesManager(data_dir=str(temp_data_dir / 'notes'))

        note = manager.create_note(
            title="Test Note",
            content="This is test content",
            tags=["test", "foreign-policy"]
        )

        assert note is not None
        assert note['title'] == "Test Note"
        assert note['content'] == "This is test content"
        assert 'id' in note
        assert 'created_at' in note

    def test_get_all_notes(self, temp_data_dir):
        """Test retrieving all notes"""
        from managers.notes_manager import NotesManager

        manager = NotesManager(data_dir=str(temp_data_dir / 'notes'))

        note1 = manager.create_note("Note 1", "Content 1")
        note2 = manager.create_note("Note 2", "Content 2")

        notes = manager.get_all_notes()

        assert len(notes) == 2

    def test_get_note_by_id(self, temp_data_dir):
        """Test retrieving a specific note"""
        from managers.notes_manager import NotesManager

        manager = NotesManager(data_dir=str(temp_data_dir / 'notes'))

        created_note = manager.create_note("Test Note", "Content")
        note_id = created_note['id']

        retrieved_note = manager.get_note(note_id)

        assert retrieved_note is not None
        assert retrieved_note['id'] == note_id

    def test_update_note(self, temp_data_dir):
        """Test updating note content"""
        from managers.notes_manager import NotesManager

        manager = NotesManager(data_dir=str(temp_data_dir / 'notes'))

        note = manager.create_note("Old Title", "Old Content")
        note_id = note['id']

        updated = manager.update_note(
            note_id,
            title="New Title",
            content="New Content",
            tags=["updated"]
        )

        assert updated['title'] == "New Title"
        assert updated['content'] == "New Content"
        assert "updated" in updated['tags']

    def test_delete_note(self, temp_data_dir):
        """Test deleting a note"""
        from managers.notes_manager import NotesManager

        manager = NotesManager(data_dir=str(temp_data_dir / 'notes'))

        note = manager.create_note("Test Note", "Content")
        note_id = note['id']

        manager.delete_note(note_id)

        notes = manager.get_all_notes()
        assert not any(n['id'] == note_id for n in notes)

    def test_create_folder(self, temp_data_dir):
        """Test creating note folders"""
        from managers.notes_manager import NotesManager

        manager = NotesManager(data_dir=str(temp_data_dir / 'notes'))

        folder = manager.create_folder("Research", "Foreign Policy Research")

        assert folder is not None
        assert folder['name'] == "Research"
        assert 'id' in folder

    def test_move_note_to_folder(self, temp_data_dir):
        """Test moving note to a folder"""
        from managers.notes_manager import NotesManager

        manager = NotesManager(data_dir=str(temp_data_dir / 'notes'))

        folder = manager.create_folder("Research", "Desc")
        note = manager.create_note("Test Note", "Content")

        updated_note = manager.move_to_folder(note['id'], folder['id'])

        assert updated_note['folder'] == folder['id']

    def test_get_notes_by_tag(self, temp_data_dir):
        """Test filtering notes by tag"""
        from managers.notes_manager import NotesManager

        manager = NotesManager(data_dir=str(temp_data_dir / 'notes'))

        note1 = manager.create_note("Note 1", "Content", tags=["foreign-policy"])
        note2 = manager.create_note("Note 2", "Content", tags=["crisis"])
        note3 = manager.create_note("Note 3", "Content", tags=["foreign-policy"])

        fp_notes = manager.get_notes_by_tag("foreign-policy")

        assert len(fp_notes) == 2
        assert all("foreign-policy" in n['tags'] for n in fp_notes)
