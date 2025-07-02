#!/usr/bin/env python3
"""
Test Formatting Cleanup and Scoring Improvements
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent  # Go up to project-1-technical-rag
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))  # Add rag-portfolio root for shared_utils

from src.basic_rag import BasicRAG


def test_formatting_cleanup():
    """Test if formatting artifacts are removed."""
    print("🧪 TESTING FORMATTING CLEANUP")
    print("=" * 50)
    
    # Index RISC-V document
    rag = BasicRAG()
    pdf_path = project_root / "data" / "test" / "riscv-base-instructions.pdf"
    rag.index_document(pdf_path)
    
    # Check for artifacts in chunks
    artifact_patterns = [
        ('volume_header', 'Volume I: RISC-V'),
        ('document_version', 'Document Version'),
        ('isa_header', 'ISA V20191213'),
        ('manual_title', 'The RISC-V Instruction Set Manual'),
        ('figure_ref', 'Figure '),
        ('table_ref', 'Table '),
        ('email', '@'),
        ('nonbinding', 'Contains Nonbinding'),
    ]
    
    chunks_with_artifacts = 0
    clean_chunks = 0
    
    print(f"\n📊 Analyzing {len(rag.chunks)} chunks for artifacts...")
    
    for chunk in rag.chunks[:50]:  # Sample first 50
        text = chunk['text']
        has_artifact = False
        
        for pattern_name, pattern in artifact_patterns:
            if pattern in text:
                has_artifact = True
                break
        
        if has_artifact:
            chunks_with_artifacts += 1
        else:
            clean_chunks += 1
    
    print(f"   Clean chunks: {clean_chunks}/50 ({clean_chunks/50*100:.1f}%)")
    print(f"   With artifacts: {chunks_with_artifacts}/50")
    
    # Show sample clean chunks
    print(f"\n📄 Sample Clean Chunks:")
    sample_count = 0
    for i, chunk in enumerate(rag.chunks):
        text = chunk['text']
        # Check if truly clean
        is_clean = all(pattern not in text for _, pattern in artifact_patterns)
        
        if is_clean and sample_count < 3:
            print(f"\n   Chunk {i} (Page {chunk.get('page')}):")
            preview = text[:150] + "..." if len(text) > 150 else text
            print(f"   {preview}")
            sample_count += 1
    
    return clean_chunks / 50


def test_scoring_variation():
    """Test if scoring shows better variation."""
    print("\n\n🎯 TESTING SCORING VARIATION")
    print("=" * 50)
    
    # Index all documents
    rag = BasicRAG()
    data_folder = project_root / "data" / "test"
    rag.index_documents(data_folder)
    
    # Test queries
    test_queries = [
        "RISC-V instruction encoding format",
        "floating point arithmetic operations",
        "software validation requirements documentation",
        "medical device AI guidelines",
        "risk assessment process"
    ]
    
    all_scores = []
    score_ranges = []
    
    print(f"\n📊 Testing {len(test_queries)} queries...")
    
    for query in test_queries:
        result = rag.hybrid_query(query, top_k=10)
        scores = [chunk.get('hybrid_score', 0) for chunk in result.get('chunks', [])]
        
        if scores:
            all_scores.extend(scores)
            score_range = max(scores) - min(scores)
            score_ranges.append(score_range)
            
            print(f"\n   Query: '{query[:40]}...'")
            print(f"   Scores: {[f'{s:.4f}' for s in scores[:5]]}")
            print(f"   Range: {score_range:.4f}")
    
    # Analyze overall variation
    if all_scores:
        unique_scores = len(set(f"{s:.4f}" for s in all_scores))
        total_scores = len(all_scores)
        variation_ratio = unique_scores / total_scores
        avg_range = sum(score_ranges) / len(score_ranges)
        
        print(f"\n📈 Score Analysis:")
        print(f"   Total scores: {total_scores}")
        print(f"   Unique scores: {unique_scores}")
        print(f"   Variation ratio: {variation_ratio:.2f}")
        print(f"   Average range: {avg_range:.4f}")
        print(f"   Min score: {min(all_scores):.4f}")
        print(f"   Max score: {max(all_scores):.4f}")
        
        if variation_ratio > 0.7:
            print("   ✅ EXCELLENT: High score variation")
        elif variation_ratio > 0.5:
            print("   🔄 GOOD: Moderate score variation")
        else:
            print("   ⚠️ LIMITED: Low score variation")
        
        return variation_ratio
    
    return 0.0


def test_retrieval_relevance():
    """Test if retrieval results are more relevant."""
    print("\n\n🔍 TESTING RETRIEVAL RELEVANCE")
    print("=" * 50)
    
    rag = BasicRAG()
    data_folder = project_root / "data" / "test"
    rag.index_documents(data_folder)
    
    # Specific queries with expected content
    test_cases = [
        {
            'query': 'RISC-V load store instructions memory addressing',
            'expected_terms': ['load', 'store', 'memory', 'address'],
            'expected_source': 'riscv-base-instructions.pdf'
        },
        {
            'query': 'software validation testing requirements',
            'expected_terms': ['validation', 'testing', 'requirements'],
            'expected_source': 'General-Principles-of-Software-Validation'
        }
    ]
    
    for test in test_cases:
        print(f"\n📌 Query: '{test['query']}'")
        result = rag.hybrid_query(test['query'], top_k=3)
        
        if result.get('chunks'):
            top_chunk = result['chunks'][0]
            text = top_chunk['text'].lower()
            
            # Check term coverage
            terms_found = sum(1 for term in test['expected_terms'] if term in text)
            coverage = terms_found / len(test['expected_terms'])
            
            print(f"   Top result score: {top_chunk.get('hybrid_score', 0):.4f}")
            print(f"   Source: {Path(top_chunk['source']).name}")
            print(f"   Term coverage: {terms_found}/{len(test['expected_terms'])} ({coverage:.0%})")
            
            # Show clean preview
            preview = text[:200] + "..." if len(text) > 200 else text
            print(f"   Content: {preview}")
            
            if coverage >= 0.75:
                print("   ✅ Good relevance")
            else:
                print("   ⚠️ Limited relevance")


if __name__ == "__main__":
    print("🔧 TESTING IMPROVEMENTS")
    print("=" * 70)
    
    # Test formatting cleanup
    cleanup_ratio = test_formatting_cleanup()
    
    # Test scoring variation
    variation_ratio = test_scoring_variation()
    
    # Test retrieval relevance
    test_retrieval_relevance()
    
    print("\n\n🏆 OVERALL ASSESSMENT")
    print("=" * 40)
    print(f"Formatting cleanup: {cleanup_ratio:.0%} clean chunks")
    print(f"Score variation: {variation_ratio:.2f} ratio")
    
    if cleanup_ratio > 0.8 and variation_ratio > 0.6:
        print("\n✅ Improvements successful!")
    else:
        print("\n⚠️ Improvements need more work")