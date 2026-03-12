"""
Integration tests for memory system
Tests active memory, memory manager, and their integration
"""
import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


class TestMemoryIntegration:
    """Test memory system integration"""

    @patch('core.active_memory.chromadb')
    @patch('managers.memory_manager.MemoryManager')
    def test_active_memory_and_manager_integration(self, mock_manager_class, mock_chromadb):
        """Test that active memory and memory manager work together"""
        from core.active_memory import ActiveMemory

        mock_collection = Mock()
        mock_client = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        active_memory = ActiveMemory()

        # Track interaction
        active_memory.track_conversation(
            user_message="What is USA foreign policy?",
            assistant_response="USA focuses on democracy...",
            session_id="test-session"
        )

        # Verify storage
        mock_collection.add.assert_called_once()

    @patch('core.active_memory.chromadb')
    def test_memory_context_flows_to_ai(self, mock_chromadb):
        """Test that memory provides context to AI requests"""
        from core.active_memory import ActiveMemory

        mock_collection = Mock()
        mock_collection.query.return_value = {
            'documents': [['Previous discussion about USA policy']],
            'distances': [[0.2]],
            'metadatas': [[{'session_id': 'test'}]]
        }

        mock_client = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client

        active_memory = ActiveMemory()
        active_memory.collection = mock_collection

        # Query memory
        context = active_memory.query_memory("USA foreign policy")

        assert len(context) > 0
        assert mock_collection.query.called

    def test_memory_manager_tracks_research_history(self, temp_data_dir):
        """Test that memory manager tracks research operations"""
        from managers.memory_manager import MemoryManager

        memory_manager = MemoryManager(data_dir=str(temp_data_dir / 'memory'))

        # Track research
        memory_manager.track_research(
            topic="Climate Change",
            country="USA",
            findings="USA supports renewable energy transition",
            session_id="test-session"
        )

        # Retrieve history
        history = memory_manager.get_research_history_for_topic("USA", "Climate Change")

        assert history is not None
        assert len(history) > 0

    def test_memory_manager_provides_compact_context(self, temp_data_dir):
        """Test that memory manager provides compact context for LLMs"""
        from managers.memory_manager import MemoryManager

        memory_manager = MemoryManager(data_dir=str(temp_data_dir / 'memory'))

        # Add some agent executions
        memory_manager.track_agent_execution(
            agent_name="ResearchAgent",
            task="Foreign policy research",
            result="Completed successfully"
        )

        # Get compact memory
        compact_memory = memory_manager.get_compact_memory_for_llm(max_tokens=300)

        assert isinstance(compact_memory, str)
        # Should fit within token limit
        assert len(compact_memory.split()) < 300

    @patch('core.ai_service.get_active_memory')
    @patch('core.ai_service.genai')
    @patch('core.ai_service.ollama')
    def test_ai_service_uses_active_memory(self, mock_ollama, mock_genai, mock_active_memory):
        """Test that AI service integrates with active memory"""
        from core.ai_service import AIService

        mock_memory = Mock()
        mock_memory.query_memory.return_value = ["Relevant context"]
        mock_active_memory.return_value = mock_memory

        mock_vectordb = Mock()

        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):
            ai_service = AIService(mock_vectordb)

            assert ai_service.active_memory == mock_memory

    def test_orchestrator_uses_memory_for_context(self, mock_vectordb):
        """Test that orchestrator retrieves and uses memory context"""
        from agents.orchestrator import AgentOrchestrator

        with patch('agents.orchestrator.MemoryManager') as mock_memory_class:
            mock_memory_instance = Mock()
            mock_memory_instance.get_compact_memory_for_llm.return_value = "Memory summary"
            mock_memory_instance.get_research_history_for_topic.return_value = "Previous research"
            mock_memory_class.return_value = mock_memory_instance

            orchestrator = AgentOrchestrator(vectordb=mock_vectordb)

            # Verify memory manager was initialized
            assert orchestrator.memory is not None
            assert orchestrator.memory.get_compact_memory_for_llm

    def test_session_end_creates_compressed_memory(self, temp_data_dir):
        """Test that ending a session creates compressed memory"""
        from managers.session_manager import SessionManager

        manager = SessionManager(data_dir=str(temp_data_dir))

        session = manager.create_session("Test MUN", "Desc", "2025-01-01")

        ended_session = manager.end_session(
            session['id'],
            summary="Session completed successfully",
            compressed_memory="Key memories: Discussed climate policy, generated 3 speeches"
        )

        assert ended_session['compressed_memory'] is not None
        assert "Key memories" in ended_session['compressed_memory']
        assert ended_session['status'] == 'ended'
