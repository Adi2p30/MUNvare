"""
Unit tests for VectorDB module
Tests ChromaDB integration and RAG functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))

# Mock heavy dependencies before importing
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['torch'] = MagicMock()


class TestVectorDB:
    """Test VectorDB initialization and operations"""

    @patch('core.vectordb.chromadb.PersistentClient')
    def test_initialize_mun_vector_db(self, mock_chromadb):
        """Test MUNVectorDB initialization"""
        from core.vectordb import MUNVectorDB

        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_collection = Mock(return_value=mock_collection)
        mock_chromadb.return_value = mock_client

        vectordb = MUNVectorDB(persist_directory="/tmp/test_vectordb")

        assert vectordb is not None
        assert vectordb.client == mock_client
        mock_chromadb.assert_called_once()

    @patch('core.vectordb.chromadb.PersistentClient')
    def test_chunk_text(self, mock_chromadb):
        """Test text chunking functionality"""
        from core.vectordb import MUNVectorDB

        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_collection = Mock(return_value=mock_collection)
        mock_chromadb.return_value = mock_client

        vectordb = MUNVectorDB()

        text = " ".join([f"word{i}" for i in range(1000)])
        chunks = vectordb.chunk_text(text, chunk_size=100, overlap=10)

        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)

    @patch('core.vectordb.chromadb.PersistentClient')
    def test_search(self, mock_chromadb):
        """Test searching the vector database"""
        from core.vectordb import MUNVectorDB

        mock_collection = Mock()
        mock_collection.query = Mock(return_value={
            'documents': [['Test result document']],
            'metadatas': [[{'section_title': 'Test Section'}]],
            'distances': [[0.5]]
        })

        mock_client = Mock()
        mock_client.get_collection = Mock(return_value=mock_collection)
        mock_chromadb.return_value = mock_client

        vectordb = MUNVectorDB()
        vectordb.collection = mock_collection

        results = vectordb.search("test query", n_results=5)

        assert len(results) > 0
        assert results[0]['content'] == 'Test result document'
        assert 'metadata' in results[0]
        mock_collection.query.assert_called_once()

    @patch('core.vectordb.chromadb.PersistentClient')
    def test_get_context_for_query(self, mock_chromadb):
        """Test getting formatted context for a query"""
        from core.vectordb import MUNVectorDB

        mock_collection = Mock()
        mock_collection.query = Mock(return_value={
            'documents': [['Doc 1 content', 'Doc 2 content']],
            'metadatas': [[
                {'section_title': 'Section 1'},
                {'section_title': 'Section 2'}
            ]],
            'distances': [[0.3, 0.6]]
        })

        mock_client = Mock()
        mock_client.get_collection = Mock(return_value=mock_collection)
        mock_chromadb.return_value = mock_client

        vectordb = MUNVectorDB()
        vectordb.collection = mock_collection

        context = vectordb.get_context_for_query("test query", max_context_length=500)

        assert isinstance(context, str)
        assert len(context) > 0
        assert 'Section 1' in context or 'Section 2' in context

    @patch('core.vectordb.chromadb.PersistentClient')
    def test_initialize_vector_db_function(self, mock_chromadb):
        """Test initialize_vector_db helper function"""
        from core.vectordb import initialize_vector_db

        mock_collection = Mock()
        mock_collection.query = Mock(return_value={
            'documents': [['Test doc']],
            'metadatas': [[{}]],
            'distances': [[0.1]]
        })

        mock_client = Mock()
        mock_client.get_collection = Mock(return_value=mock_collection)
        mock_chromadb.return_value = mock_client

        vectordb = initialize_vector_db()

        assert vectordb is not None
