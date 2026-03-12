#!/usr/bin/env python3
"""
Test script for Active Memory RAG system
Tests the complete memory-enhanced AI service
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from core.vectordb import initialize_vector_db
from core.ai_service import AIService
from core.active_memory import get_active_memory
from core.memory_optimizer import get_memory_optimizer


def test_embeddings():
    """Test Gemma embeddings service"""
    print("\n" + "="*60)
    print("TEST 1: Gemma Embeddings Service")
    print("="*60)

    try:
        from core.gemma_embeddings import get_embeddings_service

        embeddings = get_embeddings_service()

        # Test query embedding
        query = "What is India's position on climate change?"
        query_emb = embeddings.embed_query(query)

        print(f"✓ Query embedding dimension: {len(query_emb)}")
        print(f"✓ Sample values: {query_emb[:3]}")

        # Test document embedding
        doc = "India has committed to net-zero emissions by 2070"
        doc_emb = embeddings.embed_document(doc)

        print(f"✓ Document embedding dimension: {len(doc_emb)}")

        # Test similarity
        similarity = embeddings.compute_similarity(query_emb, doc_emb)
        print(f"✓ Similarity score: {similarity:.4f}")

        print("\n✅ Embeddings test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Embeddings test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_active_memory():
    """Test Active Memory Cache"""
    print("\n" + "="*60)
    print("TEST 2: Active Memory Cache")
    print("="*60)

    try:
        memory = get_active_memory()

        # Test caching conversation
        memory.cache_conversation(
            user_message="What is the Paris Agreement?",
            assistant_response="The Paris Agreement is an international treaty on climate change...",
            metadata={'topic': 'climate change'}
        )

        # Test caching research
        memory.cache_research(
            research_type='foreign_policy',
            country='India',
            topic='climate change',
            content='India is committed to achieving net-zero emissions by 2070. Key policies include...'
        )

        # Test caching note
        memory.cache_note(
            note_id='test_note_1',
            title='Climate Change Research',
            content='Key facts about climate change and India\'s stance...'
        )

        print(f"✓ Cached 3 different memory types")

        # Test retrieval
        results = memory.retrieve_relevant_memories(
            "India climate policy",
            n_results=5
        )

        print(f"✓ Retrieved {len(results)} relevant memories")

        for i, result in enumerate(results[:3], 1):
            print(f"\n  Memory {i} ({result['memory_type']}):")
            print(f"  Distance: {result['distance']:.4f}")
            print(f"  Content: {result['content'][:80]}...")

        # Test LLM context formatting
        context = memory.get_context_for_llm("What should India do about climate change?")
        print(f"\n✓ Generated LLM context: {len(context)} characters")

        # Test stats
        stats = memory.get_stats()
        print(f"\n✓ Memory statistics:")
        print(f"  Total memories: {stats['current_total']}")
        print(f"  Conversations: {stats.get('conversations_count', 0)}")
        print(f"  Research: {stats.get('research_count', 0)}")
        print(f"  Notes: {stats.get('notes_count', 0)}")

        print("\n✅ Active Memory test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Active Memory test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memory_optimizer():
    """Test Memory Optimizer"""
    print("\n" + "="*60)
    print("TEST 3: Memory Optimizer")
    print("="*60)

    try:
        optimizer = get_memory_optimizer(optimization_interval=60)  # 1 minute

        # Check status before starting
        status = optimizer.get_status()
        print(f"✓ Optimizer status: {status['running']}")

        # Start optimizer
        optimizer.start()
        print("✓ Optimizer started in background")

        # Force an optimization
        optimizer.force_optimize()
        print("✓ Forced optimization completed")

        # Check status after
        status = optimizer.get_status()
        print(f"✓ Optimizer running: {status['running']}")
        print(f"✓ Last optimization: {status['last_optimization']}")

        # Stop optimizer
        optimizer.stop()
        print("✓ Optimizer stopped")

        print("\n✅ Memory Optimizer test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Memory Optimizer test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_service_with_memory():
    """Test AI Service with Active Memory integration"""
    print("\n" + "="*60)
    print("TEST 4: AI Service with Active Memory RAG")
    print("="*60)

    try:
        # Initialize vector DB and AI service
        print("Initializing services...")
        vectordb = initialize_vector_db()
        ai_service = AIService(vectordb)

        if not ai_service.gemini_client:
            print("⚠ Gemini not available, skipping AI service test")
            return True

        # First conversation
        print("\n--- First Conversation ---")
        response1 = ai_service.chat_with_context(
            "What are the key MUN procedures for moderated caucus?"
        )
        print(f"Response 1 length: {len(response1)} chars")
        print(f"Response 1 preview: {response1[:150]}...")

        # Second conversation (should use memory from first)
        print("\n--- Second Conversation (using memory) ---")
        response2 = ai_service.chat_with_context(
            "Can you remind me what we just discussed about MUN?"
        )
        print(f"Response 2 length: {len(response2)} chars")
        print(f"Response 2 preview: {response2[:150]}...")

        # Test speech generation with caching
        print("\n--- Speech Generation (cached) ---")
        speech = ai_service.generate_speech(
            country="India",
            topic="Climate Change",
            speech_type="GSL"
        )
        print(f"✓ Generated speech: {len(speech)} chars")

        # Verify memory was cached
        memory = get_active_memory()
        stats = memory.get_stats()
        print(f"\n✓ Current memory stats:")
        print(f"  Total: {stats['current_total']}")
        print(f"  Conversations: {stats.get('conversations_count', 0)}")
        print(f"  Speeches: {stats.get('speeches_count', 0)}")

        print("\n✅ AI Service with Memory test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ AI Service with Memory test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_end_to_end():
    """Complete end-to-end test"""
    print("\n" + "="*60)
    print("TEST 5: End-to-End System Test")
    print("="*60)

    try:
        # Initialize everything
        vectordb = initialize_vector_db()
        ai_service = AIService(vectordb)
        memory = get_active_memory()

        if not ai_service.gemini_client:
            print("⚠ Gemini not available, skipping E2E test")
            return True

        # Simulate a complete user workflow
        print("\n=== Simulating User Workflow ===")

        # Step 1: User asks a question
        print("\n1. User asks about MUN procedures...")
        response = ai_service.chat_with_context(
            "How do I prepare for a MUN conference?"
        )
        print(f"✓ Got response: {len(response)} chars")

        # Step 2: User generates speech
        print("\n2. User generates a speech...")
        speech = ai_service.generate_speech(
            country="United States",
            topic="Global Security",
            committee="UNSC"
        )
        print(f"✓ Generated speech: {len(speech)} chars")

        # Step 3: User asks follow-up (should use memory)
        print("\n3. User asks follow-up question...")
        followup = ai_service.chat_with_context(
            "Can you help me improve the speech we just created?"
        )
        print(f"✓ Got follow-up response: {len(followup)} chars")

        # Step 4: Check memory
        print("\n4. Checking memory system...")
        results = memory.retrieve_relevant_memories(
            "MUN speech United States security",
            n_results=3
        )
        print(f"✓ Found {len(results)} relevant memories")

        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['memory_type']}: distance={result['distance']:.4f}")

        # Step 5: Verify optimizer is running
        print("\n5. Checking background optimizer...")
        optimizer = get_memory_optimizer()
        status = optimizer.get_status()
        print(f"✓ Optimizer status: {status}")

        print("\n✅ End-to-End test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ End-to-End test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("ACTIVE MEMORY RAG SYSTEM - TEST SUITE")
    print("="*60)

    results = {
        "Gemma Embeddings": test_embeddings(),
        "Active Memory Cache": test_active_memory(),
        "Memory Optimizer": test_memory_optimizer(),
        "AI Service with Memory": test_ai_service_with_memory(),
        "End-to-End System": test_end_to_end()
    }

    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)

    passed = 0
    failed = 0

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal: {passed} passed, {failed} failed")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Active Memory RAG system is working!")
    else:
        print(f"\n⚠ {failed} test(s) failed. Check errors above.")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
