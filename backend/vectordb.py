import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import json
from typing import List, Dict
import re

class MUNVectorDB:
    """Vector database for MUN book content with RAG capabilities"""

    def __init__(self, persist_directory="./data/chromadb"):
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)

        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        try:
            self.collection = self.client.get_collection(name="mun_book")
            print("Loaded existing MUN book collection")
        except:
            self.collection = self.client.create_collection(
                name="mun_book",
                metadata={"description": "MUN Book knowledge base"}
            )
            print("Created new MUN book collection")

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)

        return chunks

    def parse_mun_book(self, book_path: str) -> List[Dict]:
        """Parse MUN book into structured sections"""
        with open(book_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by major sections
        sections = []

        # Extract table of contents items as section markers
        toc_pattern = r'^([A-Z][^\n]+)$'
        lines = content.split('\n')

        current_section = ""
        current_content = []
        section_id = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect section headers (lines with specific patterns)
            if (line.isupper() and len(line) > 5) or \
               line.startswith('What is') or \
               line.startswith('How to') or \
               line.startswith('Rules of') or \
               line in ['Introduction', 'Research 101', 'Lobbying', 'Foreign Policy',
                       'Documentation', 'Voting Procedure', 'Attire']:

                # Save previous section
                if current_section and current_content:
                    content_text = '\n'.join(current_content)
                    chunks = self.chunk_text(content_text, chunk_size=400, overlap=50)

                    for i, chunk in enumerate(chunks):
                        sections.append({
                            'id': f"section_{section_id}_{i}",
                            'section': current_section,
                            'content': chunk,
                            'metadata': {
                                'section_title': current_section,
                                'chunk_index': i,
                                'total_chunks': len(chunks)
                            }
                        })
                    section_id += 1

                # Start new section
                current_section = line
                current_content = []
            else:
                current_content.append(line)

        # Add last section
        if current_section and current_content:
            content_text = '\n'.join(current_content)
            chunks = self.chunk_text(content_text, chunk_size=400, overlap=50)

            for i, chunk in enumerate(chunks):
                sections.append({
                    'id': f"section_{section_id}_{i}",
                    'section': current_section,
                    'content': chunk,
                    'metadata': {
                        'section_title': current_section,
                        'chunk_index': i,
                        'total_chunks': len(chunks)
                    }
                })

        return sections

    def vectorize_book(self, book_path: str):
        """Vectorize the entire MUN book"""
        print("Parsing MUN book...")
        sections = self.parse_mun_book(book_path)
        print(f"Found {len(sections)} text chunks")

        print("Vectorizing content...")
        documents = []
        metadatas = []
        ids = []

        for section in sections:
            documents.append(section['content'])
            metadatas.append(section['metadata'])
            ids.append(section['id'])

        # Add to collection in batches
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_meta = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]

            self.collection.add(
                documents=batch_docs,
                metadatas=batch_meta,
                ids=batch_ids
            )

        print(f"Successfully vectorized {len(documents)} chunks from MUN book")

    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search the vector database"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        formatted_results = []
        if results['documents'] and len(results['documents']) > 0:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    'content': doc,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results.get('distances') else 0
                })

        return formatted_results

    def get_context_for_query(self, query: str, max_context_length: int = 2000) -> str:
        """Get relevant context for a query from the MUN book"""
        results = self.search(query, n_results=5)

        context_parts = []
        current_length = 0

        for result in results:
            content = result['content']
            if current_length + len(content) <= max_context_length:
                section_title = result['metadata'].get('section_title', 'Unknown')
                context_parts.append(f"[From {section_title}]\n{content}")
                current_length += len(content)
            else:
                break

        return "\n\n".join(context_parts)


def initialize_vector_db():
    """Initialize and vectorize the MUN book"""
    db = MUNVectorDB()

    # Check if already vectorized
    try:
        test_results = db.search("What is MUN?", n_results=1)
        if test_results:
            print("Vector database already initialized")
            return db
    except:
        pass

    # Vectorize the book
    book_path = os.path.join(os.path.dirname(__file__), '..', 'MUN Book .txt')
    if os.path.exists(book_path):
        db.vectorize_book(book_path)
    else:
        print(f"Warning: MUN Book not found at {book_path}")

    return db


if __name__ == "__main__":
    # Test the vector database
    db = initialize_vector_db()

    # Test search
    print("\n=== Testing search ===")
    results = db.search("How to write speeches in MUN?", n_results=3)
    for i, result in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"Section: {result['metadata'].get('section_title')}")
        print(f"Content: {result['content'][:200]}...")
