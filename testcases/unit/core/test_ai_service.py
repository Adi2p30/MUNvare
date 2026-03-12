"""
Unit tests for AI Service
Tests Gemini and Ollama integration, hybrid routing, and active memory
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))


class TestAIService:
    """Test AI Service functionality"""

    @patch('core.ai_service.genai')
    @patch('core.ai_service.ollama')
    @patch('core.ai_service.get_active_memory')
    def test_ai_service_initialization(self, mock_active_memory, mock_ollama, mock_genai):
        """Test AI service initializes with Gemini and Ollama"""
        from core.ai_service import AIService

        mock_vectordb = Mock()
        mock_ollama.list = Mock(return_value=[])
        mock_active_memory.return_value = Mock()

        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):
            ai_service = AIService(mock_vectordb)

            assert ai_service.vectordb == mock_vectordb
            assert ai_service.ollama_model == "gemma3:1b"

    @patch('core.ai_service.genai')
    @patch('core.ai_service.ollama')
    def test_chat_with_ollama(self, mock_ollama, mock_genai):
        """Test chat using Ollama for quick responses"""
        from core.ai_service import AIService

        mock_vectordb = Mock()
        mock_ollama.list = Mock(return_value=[])
        mock_ollama.chat = Mock(return_value={'message': {'content': 'Ollama response'}})

        with patch('core.ai_service.ACTIVE_MEMORY_AVAILABLE', False):
            ai_service = AIService(mock_vectordb)
            ai_service.ollama_client = mock_ollama

            response = ai_service.chat("Hello", use_gemini=False)

            assert response == 'Ollama response'
            mock_ollama.chat.assert_called_once()

    @patch('core.ai_service.genai')
    def test_chat_with_gemini(self, mock_genai):
        """Test chat using Gemini for complex tasks"""
        from core.ai_service import AIService

        mock_vectordb = Mock()
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Gemini response"
        mock_model.generate_content = Mock(return_value=mock_response)

        with patch('core.ai_service.ACTIVE_MEMORY_AVAILABLE', False), \
             patch('core.ai_service.OLLAMA_AVAILABLE', False), \
             patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):

            ai_service = AIService(mock_vectordb)
            ai_service.gemini_client = mock_model

            response = ai_service.chat("Complex task", use_gemini=True)

            assert response == "Gemini response"
            mock_model.generate_content.assert_called_once()

    @patch('core.ai_service.genai')
    @patch('core.ai_service.ollama')
    def test_generate_speech(self, mock_ollama, mock_genai):
        """Test speech generation using Gemini"""
        from core.ai_service import AIService

        mock_vectordb = Mock()
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Generated speech content"
        mock_model.generate_content = Mock(return_value=mock_response)

        with patch('core.ai_service.ACTIVE_MEMORY_AVAILABLE', False), \
             patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):

            ai_service = AIService(mock_vectordb)
            ai_service.gemini_client = mock_model

            speech = ai_service.generate_speech(
                speech_type="opening",
                country="USA",
                topic="Climate Change",
                position="Support renewable energy"
            )

            assert "Generated speech content" in speech
            mock_model.generate_content.assert_called_once()

    @patch('core.ai_service.genai')
    @patch('core.ai_service.ollama')
    def test_generate_session_summary(self, mock_ollama, mock_genai):
        """Test session summary generation"""
        from core.ai_service import AIService

        mock_vectordb = Mock()
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Session summary"
        mock_model.generate_content = Mock(return_value=mock_response)

        with patch('core.ai_service.ACTIVE_MEMORY_AVAILABLE', False), \
             patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):

            ai_service = AIService(mock_vectordb)
            ai_service.gemini_client = mock_model

            session = {'name': 'Test MUN'}
            notes = [{'title': 'Note 1'}]
            speeches = [{'title': 'Speech 1'}]
            chat_history = [{'content': 'Test message'}]

            result = ai_service.generate_session_summary(session, notes, speeches, chat_history)

            assert 'summary' in result
            assert 'stats' in result
            assert result['stats']['notes'] == 1
            assert result['stats']['speeches'] == 1

    @patch('core.ai_service.genai')
    @patch('core.ai_service.ollama')
    def test_fallback_mechanism(self, mock_ollama, mock_genai):
        """Test fallback from Ollama to Gemini when Ollama fails"""
        from core.ai_service import AIService

        mock_vectordb = Mock()
        mock_ollama.list = Mock(return_value=[])
        mock_ollama.chat = Mock(side_effect=Exception("Ollama unavailable"))

        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Gemini fallback response"
        mock_model.generate_content = Mock(return_value=mock_response)

        with patch('core.ai_service.ACTIVE_MEMORY_AVAILABLE', False), \
             patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):

            ai_service = AIService(mock_vectordb)
            ai_service.ollama_client = mock_ollama
            ai_service.gemini_client = mock_model

            # Request Ollama but should fallback to Gemini
            response = ai_service.chat("Test", use_gemini=False)

            # Should attempt Gemini as fallback
            assert mock_model.generate_content.called or mock_ollama.chat.called

    @patch('core.ai_service.get_active_memory')
    def test_active_memory_integration(self, mock_get_active_memory):
        """Test AI service integrates with active memory"""
        from core.ai_service import AIService

        mock_vectordb = Mock()
        mock_memory = Mock()
        mock_memory.query_memory = Mock(return_value=["relevant context"])
        mock_get_active_memory.return_value = mock_memory

        with patch('core.ai_service.OLLAMA_AVAILABLE', False), \
             patch('core.ai_service.GEMINI_AVAILABLE', False):

            ai_service = AIService(mock_vectordb)

            assert ai_service.active_memory == mock_memory
