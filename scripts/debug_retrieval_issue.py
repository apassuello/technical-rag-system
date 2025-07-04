#!/usr/bin/env python3
"""
Debug retrieval quality issues that are causing low confidence scores.
"""

import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.rag_with_generation import RAGWithGeneration

def debug_retrieval_quality():
    """Debug why retrieval is not finding good context."""
    print("🔍 RETRIEVAL QUALITY DEBUG")
    print("=" * 80)
    
    # Initialize RAG system
    rag = RAGWithGeneration()
    
    # Load one specific document for focused testing
    doc_path = Path("data/test/riscv-base-instructions.pdf")
    if doc_path.exists():
        print(f"Loading: {doc_path}")
        chunks = rag.index_document(str(doc_path))
        print(f"✅ Loaded {chunks} chunks")
    else:
        print(f"❌ Document not found: {doc_path}")
        return
    
    print(f"Total chunks in system: {len(rag.chunks)}")
    
    # Sample some chunks to see their content
    print(f"\n📄 SAMPLE CHUNKS")
    print("-" * 50)
    for i, chunk in enumerate(rag.chunks[:5]):
        content = chunk.get('content', chunk.get('text', ''))
        print(f"Chunk {i+1}: {len(content)} chars")
        print(f"   Content: {content[:100]}...")
        print(f"   Source: {chunk.get('metadata', {}).get('source', 'unknown')}")
        print(f"   Page: {chunk.get('metadata', {}).get('page_number', 'unknown')}")
        print()
    
    # Test retrieval with a technical query
    test_query = "What are the RISC-V base integer instruction formats?"
    print(f"\n🎯 RETRIEVAL TEST")
    print("-" * 50)
    print(f"Query: {test_query}")
    
    # Test with different top_k values
    for top_k in [3, 5, 10]:
        print(f"\n--- top_k = {top_k} ---")
        
        result = rag.query_with_answer(
            question=test_query,
            top_k=top_k,
            use_hybrid=True,
            return_context=True
        )
        
        retrieved_chunks = result.get('context', [])
        confidence = result.get('confidence', 0)
        answer = result.get('answer', '')
        citations = result.get('citations', [])
        
        print(f"Retrieved chunks: {len(retrieved_chunks)}")
        print(f"Confidence: {confidence:.1%}")
        print(f"Citations: {len(citations)}")
        print(f"Answer length: {len(answer)} chars")
        
        # Examine retrieved chunks
        if retrieved_chunks:
            print("Retrieved content:")
            for i, chunk in enumerate(retrieved_chunks[:3]):
                content = chunk.get('text', chunk.get('content', ''))
                score = chunk.get('score', 'unknown')
                print(f"   {i+1}. Score: {score}, Content: {content[:80]}...")
        else:
            print("   No chunks retrieved!")
    
    # Test a medical device query if we have medical docs
    medical_query = "What are the FDA software validation requirements?"
    print(f"\n🏥 MEDICAL DEVICE TEST")
    print("-" * 50)
    print(f"Query: {medical_query}")
    
    result = rag.query_with_answer(
        question=medical_query,
        top_k=5,
        use_hybrid=True,
        return_context=True
    )
    
    retrieved_chunks = result.get('context', [])
    confidence = result.get('confidence', 0)
    
    print(f"Retrieved chunks: {len(retrieved_chunks)}")
    print(f"Confidence: {confidence:.1%}")
    
    if len(retrieved_chunks) == 0:
        print("❌ No medical device context found - need to load FDA documents")
    
    # Test irrelevant query (should have low confidence)
    irrelevant_query = "What is the capital of Mars?"
    print(f"\n🌍 IRRELEVANT QUERY TEST")
    print("-" * 50)
    print(f"Query: {irrelevant_query}")
    
    result = rag.query_with_answer(
        question=irrelevant_query,
        top_k=5,
        use_hybrid=True,
        return_context=True
    )
    
    retrieved_chunks = result.get('context', [])
    confidence = result.get('confidence', 0)
    
    print(f"Retrieved chunks: {len(retrieved_chunks)}")
    print(f"Confidence: {confidence:.1%}")
    print(f"✅ Expected low confidence for irrelevant query")
    
    # Check if the issue is the retrieval scoring
    print(f"\n🔬 DIRECT RETRIEVAL TEST")
    print("-" * 50)
    
    # Test the basic RAG retrieval
    try:
        basic_results = rag.hybrid_query(test_query, top_k=5)
        print(f"Basic hybrid query returned {len(basic_results)} results")
        
        for i, result in enumerate(basic_results[:3]):
            content = result.get('text', result.get('content', ''))
            score = result.get('score', 'unknown')
            print(f"   {i+1}. Score: {score:.3f}, Content: {content[:80]}...")
            
    except Exception as e:
        print(f"❌ Basic retrieval failed: {e}")
    
    print(f"\n✅ DEBUG COMPLETE")
    print("Key findings:")
    print(f"   • Total chunks available: {len(rag.chunks)}")
    print(f"   • Retrieval working: {'Yes' if retrieved_chunks else 'No'}")
    print(f"   • Confidence correlates with retrieval: {'Yes' if confidence > 0 else 'No'}")

if __name__ == "__main__":
    debug_retrieval_quality()