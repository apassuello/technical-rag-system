#!/usr/bin/env python3
"""
Test script for end-to-end RAG with answer generation pipeline.

This script tests the complete flow from document indexing through
answer generation with citations.
"""

import sys
from pathlib import Path
import time
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import directly since we're in the project directory
sys.path.insert(0, str(Path(__file__).parent))
from src.rag_with_generation import RAGWithGeneration


def test_answer_generation():
    """Test the complete RAG + answer generation pipeline."""
    
    print("=" * 80)
    print("RAG with Answer Generation - End-to-End Test")
    print("=" * 80)
    
    # Initialize system
    print("\n1. Initializing RAG system with answer generation...")
    try:
        rag = RAGWithGeneration(
            primary_model="llama3.2:3b",
            temperature=0.3,
            enable_streaming=True
        )
        print("✅ System initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # Check for existing indexed documents
    print(f"\n2. Checking existing index...")
    print(f"   - Chunks in index: {len(rag.chunks)}")
    
    # If no documents indexed, index the test document
    if len(rag.chunks) == 0:
        print("\n3. No documents found. Indexing test document...")
        test_pdf = Path("data/test/riscv-base-instructions.pdf")
        
        if not test_pdf.exists():
            print(f"❌ Test PDF not found at {test_pdf}")
            return
            
        try:
            start_time = time.time()
            chunk_count = rag.index_document(test_pdf)
            index_time = time.time() - start_time
            print(f"✅ Indexed {chunk_count} chunks in {index_time:.2f}s")
        except Exception as e:
            print(f"❌ Failed to index document: {e}")
            return
    else:
        print("✅ Using existing index")
    
    # Test queries
    test_queries = [
        "What is RISC-V?",
        "How does the RISC-V base integer instruction set work?",
        "What are the main features of RISC-V architecture?",
        "Explain the RISC-V register model",
        "What memory addressing modes does RISC-V support?"
    ]
    
    print("\n4. Testing answer generation with different queries...")
    print("-" * 80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nQuery {i}: {query}")
        print("-" * 40)
        
        try:
            # Test non-streaming first
            result = rag.query_with_answer(
                question=query,
                top_k=5,
                use_hybrid=True,
                dense_weight=0.7,
                return_context=False
            )
            
            # Display results
            print(f"\n📝 Answer:")
            print(result['answer'])
            
            print(f"\n📚 Citations ({len(result['citations'])} sources):")
            for j, citation in enumerate(result['citations'], 1):
                print(f"   {j}. {citation['source']} (Page {citation['page']}) - Score: {citation['relevance']:.3f}")
            
            print(f"\n📊 Statistics:")
            print(f"   - Confidence: {result['confidence']:.1%}")
            print(f"   - Retrieval: {result['retrieval_stats']['method']} ({result['retrieval_stats']['chunks_retrieved']} chunks)")
            print(f"   - Model: {result['generation_stats']['model']}")
            print(f"   - Total time: {result['generation_stats']['total_time']:.2f}s")
            print(f"     - Retrieval: {result['retrieval_stats']['retrieval_time']:.2f}s")
            print(f"     - Generation: {result['generation_stats']['generation_time']:.2f}s")
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            import traceback
            traceback.print_exc()
    
    # Test streaming
    print("\n" + "=" * 80)
    print("5. Testing streaming answer generation...")
    print("-" * 80)
    
    stream_query = "What are the key advantages of RISC-V over other instruction set architectures?"
    print(f"\nStreaming Query: {stream_query}")
    print("\n📝 Streaming Answer:")
    
    try:
        final_result = None
        for chunk in rag.query_with_answer_stream(
            question=stream_query,
            top_k=5,
            use_hybrid=True
        ):
            if isinstance(chunk, str):
                print(chunk, end='', flush=True)
            else:
                # Final result dict
                final_result = chunk
        
        print("\n")  # New line after streaming
        
        if final_result:
            print(f"\n📊 Final Statistics:")
            print(f"   - Citations: {len(final_result['citations'])}")
            print(f"   - Confidence: {final_result['confidence']:.1%}")
            print(f"   - Total time: {final_result['generation_stats']['total_time']:.2f}s")
            
    except Exception as e:
        print(f"\n❌ Streaming error: {e}")
    
    # Test with different configurations
    print("\n" + "=" * 80)
    print("6. Testing different retrieval configurations...")
    print("-" * 80)
    
    config_query = "Describe the RISC-V instruction formats"
    
    configs = [
        {"name": "Pure Semantic", "use_hybrid": False},
        {"name": "Hybrid (70/30)", "use_hybrid": True, "dense_weight": 0.7},
        {"name": "Hybrid (50/50)", "use_hybrid": True, "dense_weight": 0.5},
    ]
    
    for config in configs:
        print(f"\nConfiguration: {config['name']}")
        try:
            result = rag.query_with_answer(
                question=config_query,
                **{k: v for k, v in config.items() if k != 'name'}
            )
            print(f"✅ Confidence: {result['confidence']:.1%}, Citations: {len(result['citations'])}, Time: {result['generation_stats']['total_time']:.2f}s")
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    print("\n" + "=" * 80)
    print("✅ End-to-end testing complete!")
    print("=" * 80)


if __name__ == "__main__":
    test_answer_generation()