"""
Pytest configuration and shared fixtures for MUNvare test suite
"""
import pytest
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Mock heavy dependencies globally before any imports
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['ollama'] = MagicMock()

@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_vectordb():
    """Mock vector database for testing"""
    mock_db = Mock()
    mock_db.get_context_for_query = Mock(return_value="Mock context from vectordb")
    mock_db.search = Mock(return_value=[{"content": "test doc", "metadata": {}, "distance": 0.9}])
    return mock_db

@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing"""
    mock_service = Mock()
    mock_service.chat_with_context = Mock(return_value="Mock AI response")
    mock_service.generate_speech = Mock(return_value="Mock speech content")
    return mock_service

@pytest.fixture
def sample_session():
    """Sample session data for testing"""
    return {
        'id': 'test-session-123',
        'name': 'Test MUN Conference',
        'description': 'A test conference',
        'dates': '2025-01-01 to 2025-01-03',
        'status': 'active',
        'created_at': '2025-01-01T00:00:00',
        'updated_at': '2025-01-01T00:00:00',
        'last_accessed': '2025-01-01T00:00:00',
        'ended_at': None,
        'summary': None,
        'compressed_memory': None,
        'imported_from': []
    }

@pytest.fixture
def sample_note():
    """Sample note data for testing"""
    return {
        'id': 'note-123',
        'title': 'Test Note',
        'content': 'This is a test note about foreign policy.',
        'created_at': '2025-01-01T00:00:00',
        'updated_at': '2025-01-01T00:00:00',
        'tags': ['foreign-policy', 'test'],
        'folder': None
    }

@pytest.fixture
def sample_chat():
    """Sample chat data for testing"""
    return {
        'id': 'chat-123',
        'messages': [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': 'Hi! How can I help you?'}
        ],
        'created_at': '2025-01-01T00:00:00',
        'updated_at': '2025-01-01T00:00:00'
    }

@pytest.fixture
def sample_delegate():
    """Sample delegate configuration for testing"""
    return {
        'country': 'United States',
        'committee': 'UNSC',
        'position': 'Permanent Member',
        'goals': 'Maintain international peace and security'
    }

@pytest.fixture
def sample_speech():
    """Sample speech data for testing"""
    return {
        'id': 'speech-123',
        'title': 'Opening Statement',
        'content': 'Honorable chair, fellow delegates...',
        'type': 'opening',
        'created_at': '2025-01-01T00:00:00',
        'word_count': 250
    }

@pytest.fixture
def client():
    """Create Flask test client with mocked dependencies"""
    # Mock all dependencies before importing app
    with patch('core.vectordb.initialize_vector_db') as mock_init_vdb, \
         patch('core.ai_service.AIService') as mock_ai, \
         patch('managers.config_manager.ConfigManager') as mock_config, \
         patch('managers.chat_manager.ChatManager') as mock_chat, \
         patch('managers.notes_manager.NotesManager') as mock_notes, \
         patch('managers.session_manager.SessionManager') as mock_session, \
         patch('managers.committee_flow_manager.CommitteeFlowManager') as mock_committee, \
         patch('agents.AgentOrchestrator') as mock_orchestrator:

        # Setup mocks
        mock_init_vdb.return_value = Mock()
        mock_ai.return_value = Mock()
        mock_config.return_value = Mock()
        mock_chat.return_value = Mock()
        mock_notes.return_value = Mock()
        mock_session.return_value = Mock()
        mock_committee.return_value = Mock()
        mock_orchestrator.return_value = Mock()

        # Now import app
        from app import app
        app.config['TESTING'] = True

        with app.test_client() as client:
            yield client

@pytest.fixture
def mock_ollama():
    """Mock Ollama client for testing"""
    mock = Mock()
    mock.chat = Mock(return_value={'message': {'content': 'Mock Ollama response'}})
    mock.list = Mock(return_value=[])
    return mock

@pytest.fixture
def mock_gemini():
    """Mock Gemini client for testing"""
    mock = Mock()
    mock_response = Mock()
    mock_response.text = "Mock Gemini response"
    mock.generate_content = Mock(return_value=mock_response)
    return mock
