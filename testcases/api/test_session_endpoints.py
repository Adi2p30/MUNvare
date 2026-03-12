"""
API tests for Session endpoints
Tests all session-related API routes
"""
import pytest
import json
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


class TestSessionEndpoints:
    """Test Session API endpoints"""

    @patch('app.session_manager')
    def test_get_all_sessions(self, mock_session_manager, client):
        """Test GET /api/sessions"""
        mock_session_manager.get_all_sessions.return_value = [
            {'id': '1', 'name': 'MUN 2025'},
            {'id': '2', 'name': 'MUN 2024'}
        ]

        response = client.get('/api/sessions')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2
        assert data[0]['name'] == 'MUN 2025'

    @patch('app.session_manager')
    def test_create_session(self, mock_session_manager, client):
        """Test POST /api/sessions"""
        mock_session_manager.create_session.return_value = {
            'id': 'new-session-id',
            'name': 'New MUN',
            'status': 'active'
        }

        response = client.post('/api/sessions', json={
            'name': 'New MUN',
            'description': 'Test conference',
            'dates': '2025-01-01'
        })

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == 'New MUN'
        mock_session_manager.create_session.assert_called_once()

    @patch('app.session_manager')
    def test_create_session_missing_name(self, mock_session_manager, client):
        """Test POST /api/sessions without required name"""
        response = client.post('/api/sessions', json={
            'description': 'Test conference'
        })

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    @patch('app.session_manager')
    def test_get_session_by_id(self, mock_session_manager, client):
        """Test GET /api/sessions/<session_id>"""
        mock_session_manager.get_session.return_value = {
            'id': 'test-id',
            'name': 'Test MUN'
        }

        response = client.get('/api/sessions/test-id')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == 'test-id'

    @patch('app.session_manager')
    def test_get_session_not_found(self, mock_session_manager, client):
        """Test GET /api/sessions/<session_id> when session doesn't exist"""
        mock_session_manager.get_session.return_value = None

        response = client.get('/api/sessions/nonexistent')

        assert response.status_code == 404

    @patch('app.session_manager')
    def test_update_session(self, mock_session_manager, client):
        """Test PUT /api/sessions/<session_id>"""
        mock_session_manager.update_session.return_value = {
            'id': 'test-id',
            'name': 'Updated MUN'
        }

        response = client.put('/api/sessions/test-id', json={
            'name': 'Updated MUN',
            'description': 'Updated desc'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'Updated MUN'

    @patch('app.session_manager')
    def test_delete_session(self, mock_session_manager, client):
        """Test DELETE /api/sessions/<session_id>"""
        response = client.delete('/api/sessions/test-id')

        assert response.status_code == 200
        mock_session_manager.delete_session.assert_called_with('test-id')

    @patch('app.session_manager')
    @patch('app.ai_service')
    def test_end_session(self, mock_ai_service, mock_session_manager, client):
        """Test POST /api/sessions/<session_id>/end"""
        mock_session_manager.get_session.return_value = {
            'id': 'test-id',
            'name': 'Test MUN'
        }
        mock_session_manager.get_session_notes_dir.return_value = Mock()
        mock_session_manager.get_session_speeches_dir.return_value = Mock()
        mock_session_manager.get_session_chats_dir.return_value = Mock()

        mock_ai_service.generate_session_summary.return_value = {
            'summary': 'Test summary',
            'compressed_memory': 'Test memory',
            'stats': {'notes': 5}
        }

        mock_session_manager.end_session.return_value = {
            'id': 'test-id',
            'status': 'ended'
        }

        response = client.post('/api/sessions/test-id/end')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'summary' in data

    @patch('app.session_manager')
    def test_get_active_sessions(self, mock_session_manager, client):
        """Test GET /api/sessions/active"""
        mock_session_manager.get_active_sessions.return_value = [
            {'id': '1', 'status': 'active'}
        ]

        response = client.get('/api/sessions/active')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]['status'] == 'active'

    @patch('app.session_manager')
    def test_get_ended_sessions(self, mock_session_manager, client):
        """Test GET /api/sessions/ended"""
        mock_session_manager.get_ended_sessions.return_value = [
            {'id': '1', 'status': 'ended'}
        ]

        response = client.get('/api/sessions/ended')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]['status'] == 'ended'
