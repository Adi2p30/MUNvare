"""
API tests for Notes endpoints
Tests note CRUD operations, folders, and export functionality
"""
import pytest
import json
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


class TestNotesEndpoints:
    """Test Notes API endpoints"""

    @patch('app.notes_manager')
    def test_get_all_notes(self, mock_notes_manager, client):
        """Test GET /api/notes"""
        mock_notes_manager.get_all_notes.return_value = [
            {'id': '1', 'title': 'Note 1'},
            {'id': '2', 'title': 'Note 2'}
        ]

        response = client.get('/api/notes')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2

    @patch('app.notes_manager')
    def test_create_note(self, mock_notes_manager, client):
        """Test POST /api/notes"""
        mock_notes_manager.create_note.return_value = {
            'id': 'new-note-id',
            'title': 'New Note',
            'content': 'Note content'
        }

        response = client.post('/api/notes', json={
            'title': 'New Note',
            'content': 'Note content',
            'tags': ['research']
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['title'] == 'New Note'

    @patch('app.notes_manager')
    def test_get_note_by_id(self, mock_notes_manager, client):
        """Test GET /api/notes/<note_id>"""
        mock_notes_manager.get_note.return_value = {
            'id': 'test-id',
            'title': 'Test Note'
        }

        response = client.get('/api/notes/test-id')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == 'test-id'

    @patch('app.notes_manager')
    def test_update_note(self, mock_notes_manager, client):
        """Test PUT /api/notes/<note_id>"""
        mock_notes_manager.update_note.return_value = {
            'id': 'test-id',
            'title': 'Updated Note'
        }

        response = client.put('/api/notes/test-id', json={
            'title': 'Updated Note',
            'content': 'Updated content'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['title'] == 'Updated Note'

    @patch('app.notes_manager')
    def test_delete_note(self, mock_notes_manager, client):
        """Test DELETE /api/notes/<note_id>"""
        response = client.delete('/api/notes/test-id')

        assert response.status_code == 200
        mock_notes_manager.delete_note.assert_called_with('test-id')

    @patch('app.notes_manager')
    @patch('app.ai_service')
    def test_analyze_note(self, mock_ai_service, mock_notes_manager, client):
        """Test POST /api/notes/<note_id>/analyze"""
        mock_notes_manager.get_note.return_value = {
            'id': 'test-id',
            'content': 'Note content to analyze'
        }

        mock_ai_service.chat.return_value = "Analysis results"

        response = client.post('/api/notes/test-id/analyze', json={
            'analysis_type': 'summary'
        })

        assert response.status_code == 200

    @patch('app.notes_manager')
    def test_export_note_txt(self, mock_notes_manager, client):
        """Test GET /api/notes/<note_id>/export/txt"""
        mock_notes_manager.get_note.return_value = {
            'id': 'test-id',
            'title': 'Test Note',
            'content': 'Note content'
        }

        response = client.get('/api/notes/test-id/export/txt')

        assert response.status_code == 200
        assert response.content_type.startswith('text/plain')

    @patch('app.notes_manager')
    def test_create_folder(self, mock_notes_manager, client):
        """Test POST /api/notes-v2/folders"""
        mock_notes_manager.create_folder.return_value = {
            'id': 'folder-id',
            'name': 'Research'
        }

        response = client.post('/api/notes-v2/folders', json={
            'name': 'Research',
            'description': 'Research notes'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'Research'

    @patch('app.notes_manager')
    def test_move_note_to_folder(self, mock_notes_manager, client):
        """Test POST /api/notes/<note_id>/move-to-folder"""
        mock_notes_manager.move_to_folder.return_value = {
            'id': 'note-id',
            'folder': 'folder-id'
        }

        response = client.post('/api/notes/note-id/move-to-folder', json={
            'folder_id': 'folder-id'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['folder'] == 'folder-id'
