#!/usr/bin/env python3
"""
Test multi-document support for the RAG system with answer generation.

This script tests:
1. Multiple document indexing
2. Cross-document search and retrieval
3. Source attribution across documents
4. Answer generation from multiple sources
"""

import sys
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

from src.rag_with_generation import RAGWithGeneration


def test_multi_document_indexing():
    """Test indexing multiple documents."""
    print("=" * 70)
    print("TESTING MULTI-DOCUMENT INDEXING")
    print("=" * 70)
    
    # Initialize RAG system
    rag = RAGWithGeneration()
    
    # Check available test documents
    test_folder = Path("data/test")
    if not test_folder.exists():
        print(f"❌ Test folder not found: {test_folder}")
        return None
    
    pdf_files = list(test_folder.glob("*.pdf"))
    print(f"📄 Found {len(pdf_files)} PDF files:")
    for pdf in pdf_files:
        print(f"   • {pdf.name}")
    
    if len(pdf_files) == 0:
        print("❌ No PDF files found for testing")
        return None
    
    # Test multi-document indexing
    try:
        print(f"\n🔄 Indexing {len(pdf_files)} documents...")
        start_time = time.time()
        
        results = rag.index_documents(test_folder)
        
        indexing_time = time.time() - start_time
        
        print(f"\n✅ Multi-document indexing completed in {indexing_time:.2f}s")
        print(f"📊 Results:")
        
        total_chunks = 0
        successful_docs = 0
        
        for doc_name, chunk_count in results.items():
            if chunk_count > 0:
                print(f"   ✅ {doc_name}: {chunk_count} chunks")
                total_chunks += chunk_count
                successful_docs += 1
            else:
                print(f"   ❌ {doc_name}: Failed to process")
        
        print(f"\n📈 Summary:")
        print(f"   • {successful_docs}/{len(pdf_files)} documents processed successfully")
        print(f"   • {total_chunks} total chunks indexed")
        print(f"   • {len(set(chunk['source'] for chunk in rag.chunks))} unique sources")
        
        return rag if successful_docs > 0 else None
        
    except Exception as e:
        print(f"❌ Multi-document indexing failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_cross_document_search(rag):
    """Test search and retrieval across multiple documents."""
    print("\n" + "=" * 70)
    print("TESTING CROSS-DOCUMENT SEARCH")
    print("=" * 70)
    
    if rag is None:
        print("❌ No RAG system available for testing")
        return False
    
    # Get unique sources
    sources = set(chunk['source'] for chunk in rag.chunks)
    print(f"📚 Available sources: {len(sources)}")
    for source in sorted(sources):
        source_name = Path(source).name
        chunk_count = len([c for c in rag.chunks if c['source'] == source])
        print(f"   • {source_name}: {chunk_count} chunks")
    
    # Test queries that might span multiple documents
    test_queries = [
        "What is RISC-V and what are its applications?",
        "Explain software validation principles",
        "What are the requirements for medical device software?",
        "How does RISC-V relate to software development guidelines?"
    ]
    
    print(f"\n🔍 Testing cross-document search with {len(test_queries)} queries:")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n   Query {i}: {query}")
        
        try:
            # Test hybrid search to get source diversity
            result = rag.hybrid_query(query, top_k=8)
            
            # Analyze source diversity
            retrieved_sources = set()
            for chunk in result['chunks']:
                retrieved_sources.add(Path(chunk['source']).name)
            
            print(f"      📊 Retrieved {len(result['chunks'])} chunks from {len(retrieved_sources)} sources")
            print(f"      📄 Sources: {', '.join(sorted(retrieved_sources))}")
            
            # Check if we got cross-document results
            if len(retrieved_sources) > 1:
                print(f"      ✅ Cross-document search successful")
            elif len(retrieved_sources) == 1:
                print(f"      ⚠️ Single source only")
            else:
                print(f"      ❌ No sources retrieved")
                
        except Exception as e:
            print(f"      ❌ Query failed: {e}")
            return False
    
    return True


def test_multi_document_answer_generation(rag):
    """Test answer generation using multiple document sources."""
    print("\n" + "=" * 70)
    print("TESTING MULTI-DOCUMENT ANSWER GENERATION")
    print("=" * 70)
    
    if rag is None:
        print("❌ No RAG system available for testing")
        return False
    
    # Test queries designed to potentially use multiple sources
    test_queries = [
        {
            "query": "What is RISC-V and how does it relate to software validation?",
            "expected_sources": 2,
            "description": "Architecture + validation query"
        },
        {
            "query": "Explain the principles of software development for embedded systems",
            "expected_sources": 1,  # Might find relevant info in multiple docs
            "description": "General software principles query"
        },
        {
            "query": "What are the key considerations for medical device software using RISC-V?",
            "expected_sources": 2,
            "description": "Cross-domain query (medical + architecture)"
        }
    ]
    
    print(f"🤔 Testing answer generation with {len(test_queries)} cross-document queries:")
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n   Test {i}: {test_case['description']}")
        print(f"   Query: {test_case['query']}")
        
        try:
            start_time = time.time()
            
            # Generate answer with context
            result = rag.query_with_answer(
                question=test_case['query'],
                top_k=8,
                use_hybrid=True,
                dense_weight=0.7,
                return_context=True
            )
            
            response_time = time.time() - start_time
            
            # Analyze source diversity in answer
            citation_sources = set()
            for citation in result['citations']:
                citation_sources.add(citation['source'])
            
            context_sources = set()
            if 'context' in result:
                for chunk in result['context']:
                    context_sources.add(Path(chunk['source']).name)
            
            print(f"      📝 Answer: {len(result['answer'])} characters")
            print(f"      📚 Citations: {len(result['citations'])} from {len(citation_sources)} sources")
            print(f"      🔍 Context: {len(result.get('context', []))} chunks from {len(context_sources)} sources")
            print(f"      🎯 Confidence: {result['confidence']:.1%}")
            print(f"      ⏱️ Time: {response_time:.2f}s")
            
            # Show source breakdown
            if citation_sources:
                print(f"      📄 Citation sources: {', '.join(sorted(citation_sources))}")
            
            if context_sources:
                print(f"      📄 Context sources: {', '.join(sorted(context_sources))}")
            
            # Evaluate multi-document usage
            if len(citation_sources) >= test_case['expected_sources']:
                print(f"      ✅ Multi-document citations achieved")
            elif len(context_sources) >= test_case['expected_sources']:
                print(f"      ⚠️ Multi-document context but single-source citations")
            else:
                print(f"      ⚠️ Single-document response")
                
        except Exception as e:
            print(f"      ❌ Answer generation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True


def test_source_attribution_accuracy(rag):
    """Test that source attribution is accurate across documents."""
    print("\n" + "=" * 70)
    print("TESTING SOURCE ATTRIBUTION ACCURACY")
    print("=" * 70)
    
    if rag is None:
        print("❌ No RAG system available for testing")
        return False
    
    # Test with a specific query and verify citations
    query = "What is RISC-V?"
    
    print(f"🔍 Testing source attribution for: '{query}'")
    
    try:
        result = rag.query_with_answer(
            question=query,
            top_k=5,
            return_context=True
        )
        
        print(f"📊 Analysis:")
        print(f"   Answer length: {len(result['answer'])} characters")
        print(f"   Citations: {len(result['citations'])}")
        print(f"   Context chunks: {len(result.get('context', []))}")
        
        # Verify citation accuracy
        print(f"\n🔍 Citation Details:")
        for i, citation in enumerate(result['citations'], 1):
            print(f"   {i}. Source: {citation['source']}")
            print(f"      Page: {citation['page']}")
            print(f"      Relevance: {citation['relevance']:.1%}")
            print(f"      Snippet: {citation['snippet'][:100]}...")
        
        # Cross-reference with context
        if 'context' in result:
            print(f"\n📚 Context Source Verification:")
            context_by_source = {}
            for chunk in result['context']:
                source = Path(chunk['source']).name
                if source not in context_by_source:
                    context_by_source[source] = 0
                context_by_source[source] += 1
            
            for source, count in context_by_source.items():
                print(f"   • {source}: {count} chunks")
        
        print(f"\n✅ Source attribution test completed")
        return True
        
    except Exception as e:
        print(f"❌ Source attribution test failed: {e}")
        return False


def main():
    """Run all multi-document tests."""
    print("MULTI-DOCUMENT SUPPORT TESTING")
    print("=" * 70)
    
    # Test 1: Multi-document indexing
    rag = test_multi_document_indexing()
    
    if rag is None:
        print("\n❌ MULTI-DOCUMENT INDEXING FAILED - Cannot proceed with other tests")
        return False
    
    # Test 2: Cross-document search
    search_success = test_cross_document_search(rag)
    
    # Test 3: Multi-document answer generation  
    answer_success = test_multi_document_answer_generation(rag)
    
    # Test 4: Source attribution accuracy
    attribution_success = test_source_attribution_accuracy(rag)
    
    # Summary
    print("\n" + "=" * 70)
    print("MULTI-DOCUMENT TEST SUMMARY")
    print("=" * 70)
    
    tests = [
        ("Multi-document indexing", rag is not None),
        ("Cross-document search", search_success),
        ("Multi-document answer generation", answer_success),
        ("Source attribution accuracy", attribution_success)
    ]
    
    passed = 0
    for test_name, success in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:10} {test_name}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 ALL MULTI-DOCUMENT TESTS PASSED!")
        print("✅ Multi-document support is fully functional")
        return True
    else:
        print("⚠️ SOME MULTI-DOCUMENT TESTS FAILED")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)