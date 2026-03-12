"""
Unit tests for Active Memory system
Tests RAG-based memory storage and retrieval
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))


class TestActiveMemory:
    """Test Active Memory RAG system"""

    @patch('core.active_memory.chromadb')
    def test_active_memory_initialization(self, mock_chromadb):
        """Test active memory initialization"""
        from core.active_memory import ActiveMemory

        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_or_create_collection = Mock(return_value=mock_collection)
        mock_chromadb.PersistentClient = Mock(return_value=mock_client)

        memory = ActiveMemory()

        assert memory is not None
        mock_chromadb.PersistentClient.assert_called_once()

    @patch('core.active_memory.chromadb')
    def test_track_conversation(self, mock_chromadb):
        """Test tracking conversation in active memory"""
        from core.active_memory import ActiveMemory

        mock_collection = Mock()
        mock_client = Mock()
        mock_client.get_or_create_collection = Mock(return_value=mock_collection)
        mock_chromadb.PersistentClient = Mock(return_value=mock_client)

        memory = ActiveMemory()
        memory.collection = mock_collection

        memory.track_conversation(
            user_message="What is the foreign policy of USA?",
            assistant_response="The USA foreign policy focuses on...",
            session_id="test-session"
        )

        mock_collection.add.assert_called_once()

    @patch('core.active_memory.chromadb')
    def test_track_research(self, mock_chromadb):
        """Test tracking research in active memory"""
        from core.active_memory import ActiveMemory

        mock_collection = Mock()
        mock_client = Mock()
        mock_client.get_or_create_collection = Mock(return_value=mock_collection)
        mock_chromadb.PersistentClient = Mock(return_value=mock_client)

        memory = ActiveMemory()
        memory.collection = mock_collection

        memory.track_research(
            topic="Climate Change",
            country="USA",
            findings="USA supports renewable energy",
            session_id="test-session"
        )

        mock_collection.add.assert_called_once()

    @patch('core.active_memory.chromadb')
    def test_query_memory(self, mock_chromadb):
        """Test querying active memory"""
        from core.active_memory import ActiveMemory

        mock_collection = Mock()
        mock_collection.query = Mock(return_value={
            'documents': [['Relevant memory 1', 'Relevant memory 2']],
            'distances': [[0.2, 0.4]],
            'metadatas': [[{'type': 'conversation'}, {'type': 'research'}]]
        })

        mock_client = Mock()
        mock_client.get_or_create_collection = Mock(return_value=mock_collection)
        mock_chromadb.PersistentClient = Mock(return_value=mock_client)

        memory = ActiveMemory()
        memory.collection = mock_collection

        results = memory.query_memory("USA foreign policy", n_results=5)

        assert len(results) > 0
        mock_collection.query.assert_called_once()

    @patch('core.active_memory.chromadb')
    def test_get_session_context(self, mock_chromadb):
        """Test retrieving context for a specific session"""
        from core.active_memory import ActiveMemory

        mock_collection = Mock()
        mock_collection.query = Mock(return_value={
            'documents': [['Session-specific memory']],
            'distances': [[0.1]],
            'metadatas': [[{'session_id': 'test-session'}]]
        })

        mock_client = Mock()
        mock_client.get_or_create_collection = Mock(return_value=mock_collection)
        mock_chromadb.PersistentClient = Mock(return_value=mock_client)

        memory = ActiveMemory()
        memory.collection = mock_collection

        context = memory.get_session_context("test-session", max_length=1000)

        assert isinstance(context, str)
        assert len(context) > 0
