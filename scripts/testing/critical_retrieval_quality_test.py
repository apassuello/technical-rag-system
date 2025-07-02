#!/usr/bin/env python3
"""
Critical Retrieval Quality Test
Following CLAUDE.md: Examine actual retrieval results, not just metrics.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent  # Go up to project-1-technical-rag
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))  # Add rag-portfolio root for shared_utils

from src.basic_rag import BasicRAG


def test_retrieval_quality():
    """Test actual retrieval quality with real queries."""
    print("🔍 CRITICAL RETRIEVAL QUALITY TEST")
    print("=" * 70)
    
    # Initialize and index
    rag = BasicRAG()
    data_folder = project_root / "data" / "test"
    
    print("📄 Indexing all documents...")
    results = rag.index_documents(data_folder)
    print(f"✅ Indexed {sum(results.values())} chunks from {len(results)} documents\n")
    
    # Test queries covering different domains
    test_queries = [
        # Technical queries
        ("RISC-V load and store instructions", "riscv-base-instructions.pdf"),
        ("floating point operations RISC-V", "riscv-base-instructions.pdf"),
        
        # Medical device queries
        ("software validation process requirements", "General-Principles-of-Software-Validation"),
        ("medical device AI machine learning guidelines", "GMLP_Guiding_Principles.pdf"),
        
        # Cross-domain queries
        ("risk assessment documentation requirements", None),
        ("technical specifications and validation", None),
    ]
    
    print("🧪 TESTING RETRIEVAL QUALITY")
    print("-" * 70)
    
    for query, expected_source in test_queries:
        print(f"\n📌 Query: '{query}'")
        print(f"   Expected source: {expected_source or 'Any relevant'}")
        
        # Test hybrid retrieval
        result = rag.hybrid_query(query, top_k=5)
        chunks = result.get('chunks', [])
        
        if not chunks:
            print("   ❌ NO RESULTS FOUND!")
            continue
        
        print(f"   Found {len(chunks)} results")
        
        # Analyze results
        sources_found = set()
        relevance_scores = []
        
        for i, chunk in enumerate(chunks[:3]):  # Top 3
            source = Path(chunk['source']).name
            sources_found.add(source)
            score = chunk.get('hybrid_score', 0)
            relevance_scores.append(score)
            
            print(f"\n   Result {i+1}:")
            print(f"   - Source: {source}")
            print(f"   - Page: {chunk.get('page', 'unknown')}")
            print(f"   - Score: {score:.4f}")
            print(f"   - Title: {chunk.get('title', 'No title')}")
            
            # Show actual content for manual assessment
            text_preview = chunk['text'][:200] + "..." if len(chunk['text']) > 200 else chunk['text']
            print(f"   - Content: {text_preview}")
            
            # Manual relevance check
            query_terms = query.lower().split()
            matching_terms = sum(1 for term in query_terms if term in chunk['text'].lower())
            print(f"   - Query terms found: {matching_terms}/{len(query_terms)}")
            
            # Check if expected source found
            if expected_source and expected_source in source:
                print(f"   ✅ Expected source found")
            elif expected_source:
                print(f"   ⚠️  Different source than expected")
        
        # Overall assessment for this query
        if expected_source:
            if any(expected_source in s for s in sources_found):
                print(f"\n   ✅ Query successful: Found expected source")
            else:
                print(f"\n   ❌ Query failed: Expected source not in top results")
        else:
            if len(sources_found) > 1:
                print(f"\n   ✅ Good source diversity: {len(sources_found)} sources")
            else:
                print(f"\n   ⚠️  Limited source diversity")
    
    # Test edge cases
    print("\n\n🔧 EDGE CASE TESTS")
    print("-" * 50)
    
    # Empty query
    print("\n1. Empty query test:")
    empty_result = rag.hybrid_query("", top_k=5)
    print(f"   Result: {len(empty_result.get('chunks', []))} chunks")
    
    # Single word query
    print("\n2. Single word query test:")
    single_result = rag.hybrid_query("validation", top_k=5)
    print(f"   Result: {len(single_result.get('chunks', []))} chunks")
    sources = set(Path(c['source']).name for c in single_result.get('chunks', []))
    print(f"   Sources: {len(sources)} unique")
    
    # Very specific technical query
    print("\n3. Very specific technical query:")
    specific_result = rag.hybrid_query("RISC-V CSR mstatus register fields", top_k=5)
    if specific_result.get('chunks'):
        first_chunk = specific_result['chunks'][0]
        print(f"   Top result: {Path(first_chunk['source']).name}, page {first_chunk.get('page')}")
        print(f"   Score: {first_chunk.get('hybrid_score', 0):.4f}")
    else:
        print("   ❌ No results found")
    
    # Test scoring consistency
    print("\n\n🎯 SCORING ANALYSIS")
    print("-" * 40)
    
    # Collect all scores
    all_scores = []
    for query, _ in test_queries[:3]:
        result = rag.hybrid_query(query, top_k=10)
        scores = [c.get('hybrid_score', 0) for c in result.get('chunks', [])]
        all_scores.extend(scores)
    
    if all_scores:
        print(f"Score range: {min(all_scores):.4f} - {max(all_scores):.4f}")
        print(f"Score variance: {max(all_scores) - min(all_scores):.4f}")
        
        # Check for suspicious patterns
        score_strings = [f"{s:.3f}" for s in all_scores]
        unique_scores = len(set(score_strings))
        print(f"Unique scores: {unique_scores} out of {len(all_scores)}")
        
        if unique_scores < len(all_scores) * 0.5:
            print("⚠️  WARNING: Limited score variation detected")
        else:
            print("✅ Good score variation")


if __name__ == "__main__":
    test_retrieval_quality()