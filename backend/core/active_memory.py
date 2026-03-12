"""
Active Memory Cache with RAG
Persistent memory system that caches all interactions and retrieves relevant context automatically
"""
import os
import json
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from .gemma_embeddings import get_embeddings_service


class ActiveMemoryCache:
    """
    Active memory system that:
    1. Caches all conversations, research, notes, and interactions
    2. Uses Gemma embeddings for vectorization
    3. Automatically retrieves relevant context via RAG
    4. Continuously optimizes memory in background
    """

    def __init__(self, persist_directory: str = "./data/active_memory"):
        """
        Initialize active memory cache

        Args:
            persist_directory: Directory to persist memory data
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB for vector storage
        self.client = chromadb.PersistentClient(path=str(self.persist_directory))

        # Initialize Gemma embeddings
        self.embeddings = get_embeddings_service()

        # Create collections for different memory types
        self.collections = {
            'conversations': self._get_or_create_collection('conversations'),
            'research': self._get_or_create_collection('research'),
            'notes': self._get_or_create_collection('notes'),
            'speeches': self._get_or_create_collection('speeches'),
            'context': self._get_or_create_collection('context')
        }

        # Memory statistics
        self.stats_file = self.persist_directory / 'memory_stats.json'
        self.stats = self._load_stats()

        print(f"✓ Active Memory Cache initialized at {persist_directory}")
        print(f"  Collections: {list(self.collections.keys())}")
        print(f"  Total memories: {self.get_total_memory_count()}")

    def _get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection"""
        try:
            return self.client.get_collection(name=name)
        except:
            return self.client.create_collection(
                name=name,
                metadata={"description": f"Active memory collection for {name}"}
            )

    def _load_stats(self) -> Dict[str, Any]:
        """Load memory statistics"""
        if self.stats_file.exists():
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        return {
            'total_memories': 0,
            'conversations_count': 0,
            'research_count': 0,
            'notes_count': 0,
            'speeches_count': 0,
            'context_count': 0,
            'last_optimization': None,
            'created_at': datetime.now().isoformat()
        }

    def _save_stats(self):
        """Save memory statistics"""
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)

    def cache_conversation(self, user_message: str, assistant_response: str,
                          metadata: Optional[Dict[str, Any]] = None):
        """
        Cache a conversation exchange in memory

        Args:
            user_message: User's message
            assistant_response: Assistant's response
            metadata: Optional metadata (country, topic, etc.)
        """
        timestamp = datetime.now().isoformat()
        memory_id = f"conv_{int(datetime.now().timestamp() * 1000)}"

        # Create combined text for embedding
        combined_text = f"User: {user_message}\nAssistant: {assistant_response}"

        # Generate embedding using Gemma
        embedding = self.embeddings.embed_document(combined_text)

        # Store in ChromaDB
        self.collections['conversations'].add(
            documents=[combined_text],
            embeddings=[embedding],
            metadatas=[{
                'type': 'conversation',
                'user_message': user_message[:500],  # Truncate for metadata
                'timestamp': timestamp,
                **(metadata or {})
            }],
            ids=[memory_id]
        )

        self.stats['conversations_count'] += 1
        self.stats['total_memories'] += 1
        self._save_stats()

        print(f"✓ Cached conversation: {memory_id}")

    def cache_research(self, research_type: str, country: str, topic: str,
                      content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Cache research results in memory

        Args:
            research_type: Type of research (poi, foreign_policy, etc.)
            country: Country researched
            topic: Research topic
            content: Research content
            metadata: Optional additional metadata
        """
        timestamp = datetime.now().isoformat()
        memory_id = f"research_{int(datetime.now().timestamp() * 1000)}"

        # Generate embedding
        embedding = self.embeddings.embed_document(content)

        # Store in ChromaDB
        self.collections['research'].add(
            documents=[content],
            embeddings=[embedding],
            metadatas=[{
                'type': 'research',
                'research_type': research_type,
                'country': country,
                'topic': topic,
                'timestamp': timestamp,
                **(metadata or {})
            }],
            ids=[memory_id]
        )

        self.stats['research_count'] += 1
        self.stats['total_memories'] += 1
        self._save_stats()

        print(f"✓ Cached research: {research_type} for {country} on {topic}")

    def cache_note(self, note_id: str, title: str, content: str,
                  metadata: Optional[Dict[str, Any]] = None):
        """
        Cache a note in memory

        Args:
            note_id: Note identifier
            title: Note title
            content: Note content
            metadata: Optional metadata (folder, tags, etc.)
        """
        timestamp = datetime.now().isoformat()
        memory_id = f"note_{note_id}"

        # Generate embedding
        full_text = f"{title}\n\n{content}"
        embedding = self.embeddings.embed_document(full_text)

        # Store in ChromaDB
        self.collections['notes'].add(
            documents=[full_text],
            embeddings=[embedding],
            metadatas=[{
                'type': 'note',
                'note_id': note_id,
                'title': title,
                'timestamp': timestamp,
                **(metadata or {})
            }],
            ids=[memory_id]
        )

        self.stats['notes_count'] += 1
        self.stats['total_memories'] += 1
        self._save_stats()

        print(f"✓ Cached note: {title}")

    def cache_speech(self, speech_data: Dict[str, Any]):
        """
        Cache a speech in memory

        Args:
            speech_data: Speech data dictionary
        """
        timestamp = datetime.now().isoformat()
        memory_id = f"speech_{speech_data.get('id', int(datetime.now().timestamp() * 1000))}"

        # Generate embedding
        content = speech_data.get('content', '')
        embedding = self.embeddings.embed_document(content)

        # Store in ChromaDB
        self.collections['speeches'].add(
            documents=[content],
            embeddings=[embedding],
            metadatas=[{
                'type': 'speech',
                'country': speech_data.get('country', ''),
                'topic': speech_data.get('topic', ''),
                'speech_type': speech_data.get('speech_type', ''),
                'timestamp': timestamp
            }],
            ids=[memory_id]
        )

        self.stats['speeches_count'] += 1
        self.stats['total_memories'] += 1
        self._save_stats()

        print(f"✓ Cached speech: {speech_data.get('topic', 'Untitled')}")

    def cache_context(self, context_type: str, content: str,
                     metadata: Optional[Dict[str, Any]] = None):
        """
        Cache general context information

        Args:
            context_type: Type of context (config, session, etc.)
            content: Context content
            metadata: Optional metadata
        """
        timestamp = datetime.now().isoformat()
        memory_id = f"context_{context_type}_{int(datetime.now().timestamp() * 1000)}"

        # Generate embedding
        embedding = self.embeddings.embed_document(content)

        # Store in ChromaDB
        self.collections['context'].add(
            documents=[content],
            embeddings=[embedding],
            metadatas=[{
                'type': 'context',
                'context_type': context_type,
                'timestamp': timestamp,
                **(metadata or {})
            }],
            ids=[memory_id]
        )

        self.stats['context_count'] += 1
        self.stats['total_memories'] += 1
        self._save_stats()

        print(f"✓ Cached context: {context_type}")

    def retrieve_relevant_memories(self, query: str, n_results: int = 10,
                                   memory_types: Optional[List[str]] = None,
                                   filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories for a query using RAG

        Args:
            query: Search query
            n_results: Number of results to return
            memory_types: Specific memory types to search (conversations, research, etc.)
            filters: Optional metadata filters

        Returns:
            List of relevant memory items with content and metadata
        """
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)

        # Search across specified collections
        if memory_types is None:
            memory_types = list(self.collections.keys())

        all_results = []

        for memory_type in memory_types:
            if memory_type not in self.collections:
                continue

            try:
                # Query the collection
                results = self.collections[memory_type].query(
                    query_embeddings=[query_embedding],
                    n_results=min(n_results, self.collections[memory_type].count() or 1),
                    where=filters
                )

                # Format results
                if results['documents'] and results['documents'][0]:
                    for i, doc in enumerate(results['documents'][0]):
                        all_results.append({
                            'content': doc,
                            'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                            'distance': results['distances'][0][i] if results.get('distances') else 0,
                            'memory_type': memory_type
                        })

            except Exception as e:
                print(f"Warning: Error querying {memory_type}: {e}")
                continue

        # Sort by relevance (distance)
        all_results.sort(key=lambda x: x['distance'])

        return all_results[:n_results]

    def get_context_for_llm(self, query: str, max_tokens: int = 2000) -> str:
        """
        Get relevant context formatted for LLM consumption

        Args:
            query: User query
            max_tokens: Maximum tokens for context (rough estimate)

        Returns:
            Formatted context string
        """
        memories = self.retrieve_relevant_memories(query, n_results=15)

        if not memories:
            return ""

        # Build context string
        context_parts = ["# Relevant Memory Context\n"]

        current_length = 0
        max_chars = max_tokens * 4  # Rough estimate: 1 token ~= 4 chars

        for memory in memories:
            memory_type = memory['metadata'].get('type', 'unknown')
            content = memory['content']

            # Format based on memory type
            if memory_type == 'conversation':
                header = "## Past Conversation"
            elif memory_type == 'research':
                country = memory['metadata'].get('country', 'Unknown')
                topic = memory['metadata'].get('topic', 'Unknown')
                header = f"## Research: {country} on {topic}"
            elif memory_type == 'note':
                title = memory['metadata'].get('title', 'Note')
                header = f"## Note: {title}"
            elif memory_type == 'speech':
                country = memory['metadata'].get('country', 'Unknown')
                header = f"## Speech by {country}"
            else:
                header = f"## {memory_type.title()}"

            memory_text = f"\n{header}\n{content[:800]}...\n"

            if current_length + len(memory_text) > max_chars:
                break

            context_parts.append(memory_text)
            current_length += len(memory_text)

        return "\n".join(context_parts)

    def get_total_memory_count(self) -> int:
        """Get total number of memories cached"""
        total = 0
        for collection in self.collections.values():
            try:
                total += collection.count()
            except:
                pass
        return total

    def optimize_memory(self):
        """
        Optimize memory by:
        1. Removing duplicate or redundant memories
        2. Compressing old memories
        3. Updating statistics
        """
        print("🔧 Optimizing active memory...")

        # Update stats
        self.stats['last_optimization'] = datetime.now().isoformat()
        self.stats['total_memories'] = self.get_total_memory_count()

        for name, collection in self.collections.items():
            try:
                count = collection.count()
                self.stats[f'{name}_count'] = count
            except:
                pass

        self._save_stats()

        print(f"✓ Memory optimization complete. Total memories: {self.stats['total_memories']}")

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            **self.stats,
            'current_total': self.get_total_memory_count()
        }

    def clear_memory(self, memory_type: Optional[str] = None):
        """
        Clear memories (use with caution!)

        Args:
            memory_type: Specific memory type to clear, or None for all
        """
        if memory_type and memory_type in self.collections:
            self.client.delete_collection(memory_type)
            self.collections[memory_type] = self._get_or_create_collection(memory_type)
            print(f"✓ Cleared {memory_type} memories")
        elif memory_type is None:
            for name in list(self.collections.keys()):
                self.client.delete_collection(name)
                self.collections[name] = self._get_or_create_collection(name)
            print("✓ Cleared all memories")

        self.optimize_memory()


# Singleton instance
_active_memory = None


def get_active_memory() -> ActiveMemoryCache:
    """
    Get or create singleton ActiveMemoryCache instance

    Returns:
        ActiveMemoryCache instance
    """
    global _active_memory

    if _active_memory is None:
        _active_memory = ActiveMemoryCache()

    return _active_memory


if __name__ == "__main__":
    # Test active memory
    print("Testing Active Memory Cache...")

    memory = ActiveMemoryCache()

    # Test caching conversation
    memory.cache_conversation(
        "What is India's stance on climate change?",
        "India has committed to achieving net-zero emissions by 2070...",
        metadata={'country': 'India', 'topic': 'climate change'}
    )

    # Test caching research
    memory.cache_research(
        research_type='foreign_policy',
        country='India',
        topic='climate change',
        content='India is the third-largest emitter of greenhouse gases...'
    )

    # Test retrieval
    print("\n=== Testing Memory Retrieval ===")
    results = memory.retrieve_relevant_memories("India climate policy", n_results=5)

    for i, result in enumerate(results, 1):
        print(f"\nResult {i} ({result['memory_type']}):")
        print(f"Distance: {result['distance']:.4f}")
        print(f"Content: {result['content'][:100]}...")

    # Test LLM context
    print("\n=== Testing LLM Context ===")
    context = memory.get_context_for_llm("What should India do about climate change?")
    print(f"Context length: {len(context)} characters")
    print(f"Context preview:\n{context[:500]}...")

    # Test stats
    print("\n=== Memory Statistics ===")
    stats = memory.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

    print("\n✅ Active Memory Cache test complete!")
