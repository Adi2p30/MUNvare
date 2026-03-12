"""
API tests for Chat endpoints
Tests chat conversation management
"""
import pytest
import json
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


class TestChatEndpoints:
    """Test Chat API endpoints"""

    @patch('app.chat_manager')
    def test_get_all_chats(self, mock_chat_manager, client):
        """Test GET /api/chats"""
        mock_chat_manager.get_all_chats.return_value = [
            {'id': '1', 'messages': []},
            {'id': '2', 'messages': []}
        ]

        response = client.get('/api/chats')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2

    @patch('app.chat_manager')
    def test_create_chat(self, mock_chat_manager, client):
        """Test POST /api/chats"""
        mock_chat_manager.create_chat.return_value = {
            'id': 'new-chat-id',
            'messages': []
        }

        response = client.post('/api/chats')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == 'new-chat-id'

    @patch('app.chat_manager')
    def test_get_chat_by_id(self, mock_chat_manager, client):
        """Test GET /api/chats/<chat_id>"""
        mock_chat_manager.get_chat.return_value = {
            'id': 'test-id',
            'messages': [{'role': 'user', 'content': 'Hello'}]
        }

        response = client.get('/api/chats/test-id')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == 'test-id'

    @patch('app.chat_manager')
    def test_delete_chat(self, mock_chat_manager, client):
        """Test DELETE /api/chats/<chat_id>"""
        response = client.delete('/api/chats/test-id')

        assert response.status_code == 200
        mock_chat_manager.delete_chat.assert_called_with('test-id')

    @patch('app.chat_manager')
    @patch('app.ai_service')
    @patch('app.vectordb')
    def test_send_chat_message(self, mock_vectordb, mock_ai_service, mock_chat_manager, client):
        """Test POST /api/chat"""
        mock_chat_manager.get_chat.return_value = {
            'id': 'chat-id',
            'messages': []
        }

        mock_vectordb.get_context_for_query.return_value = "Context"
        mock_ai_service.chat.return_value = "AI response"

        mock_chat_manager.add_message.side_effect = [
            {'id': 'chat-id', 'messages': [{'role': 'user', 'content': 'Hello'}]},
            {'id': 'chat-id', 'messages': [
                {'role': 'user', 'content': 'Hello'},
                {'role': 'assistant', 'content': 'AI response'}
            ]}
        ]

        response = client.post('/api/chat', json={
            'chat_id': 'chat-id',
            'message': 'Hello'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'response' in data
