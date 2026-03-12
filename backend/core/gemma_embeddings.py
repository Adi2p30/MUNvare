"""
Gemma-based Embedding Service for Active Memory RAG
Uses Google's Gemini embedding models for vectorization
"""
import os
from typing import List, Union
import numpy as np
from dotenv import load_dotenv

load_dotenv()

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GemmaEmbeddings:
    """
    Gemma embedding service using Google's Gemini API
    Provides high-quality embeddings for RAG memory system
    """

    def __init__(self, model_name: str = "models/text-embedding-004"):
        """
        Initialize Gemma embeddings service

        Args:
            model_name: Gemini embedding model to use
        """
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")

        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        genai.configure(api_key=api_key)
        self.model_name = model_name
        self.embedding_dim = 768  # Gemini text-embedding-004 dimension

        print(f"✓ Gemma Embeddings initialized with {model_name}")

    def embed_text(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Text to embed
            task_type: Task type for embedding optimization
                      Options: RETRIEVAL_QUERY, RETRIEVAL_DOCUMENT,
                              SEMANTIC_SIMILARITY, CLASSIFICATION

        Returns:
            List of floats representing the embedding vector
        """
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type=task_type
            )
            return result['embedding']
        except Exception as e:
            print(f"Error embedding text: {e}")
            # Return zero vector as fallback
            return [0.0] * self.embedding_dim

    def embed_batch(self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently

        Args:
            texts: List of texts to embed
            task_type: Task type for embedding optimization

        Returns:
            List of embedding vectors
        """
        embeddings = []

        # Process in batches to avoid rate limits
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            for text in batch:
                embedding = self.embed_text(text, task_type)
                embeddings.append(embedding)

        return embeddings

    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding optimized for query/search

        Args:
            query: Search query text

        Returns:
            Embedding vector optimized for retrieval
        """
        return self.embed_text(query, task_type="RETRIEVAL_QUERY")

    def embed_document(self, document: str) -> List[float]:
        """
        Generate embedding optimized for document storage

        Args:
            document: Document text to embed

        Returns:
            Embedding vector optimized for document storage
        """
        return self.embed_text(document, task_type="RETRIEVAL_DOCUMENT")

    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score between -1 and 1
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model"""
        return self.embedding_dim


# Singleton instance
_embeddings_service = None


def get_embeddings_service() -> GemmaEmbeddings:
    """
    Get or create singleton GemmaEmbeddings instance

    Returns:
        GemmaEmbeddings service instance
    """
    global _embeddings_service

    if _embeddings_service is None:
        _embeddings_service = GemmaEmbeddings()

    return _embeddings_service


if __name__ == "__main__":
    # Test the embeddings service
    print("Testing Gemma Embeddings Service...")

    embeddings = GemmaEmbeddings()

    # Test single embedding
    text = "What is the foreign policy of India on climate change?"
    embedding = embeddings.embed_query(text)
    print(f"\nQuery embedding dimension: {len(embedding)}")
    print(f"Sample values: {embedding[:5]}")

    # Test document embedding
    doc = "India has committed to reducing carbon emissions by 45% by 2030."
    doc_embedding = embeddings.embed_document(doc)
    print(f"\nDocument embedding dimension: {len(doc_embedding)}")

    # Test similarity
    similarity = embeddings.compute_similarity(embedding, doc_embedding)
    print(f"\nSimilarity between query and document: {similarity:.4f}")

    # Test batch embedding
    docs = [
        "Climate change is a global challenge",
        "Renewable energy is the future",
        "MUN delegates debate international issues"
    ]
    batch_embeddings = embeddings.embed_batch(docs)
    print(f"\nBatch embedding count: {len(batch_embeddings)}")

    print("\n✅ Gemma Embeddings Service test complete!")
