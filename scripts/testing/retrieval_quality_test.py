#!/usr/bin/env python3
"""
Retrieval Quality Analysis Script
================================

Focused testing of retrieval quality, source diversity, and scoring validity.
"""

import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent.parent  # Go up to project-1-technical-rag
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))  # Add rag-portfolio root for shared_utils

from src.basic_rag import BasicRAG


def test_retrieval_quality():
    """Test retrieval quality with diverse queries."""
    print("🔍 RETRIEVAL QUALITY ANALYSIS")
    print("="*70)
    
    # Initialize RAG system
    rag = BasicRAG()
    pdf_path = project_root / "data" / "test" / "riscv-base-instructions.pdf"
    
    if not pdf_path.exists():
        print("❌ Test PDF not found")
        return
    
    print("📄 Indexing document...")
    chunks_count = rag.index_document(pdf_path)
    print(f"✅ Loaded {chunks_count} chunks")
    
    # Test queries with different characteristics
    test_queries = [
        ("Broad Query", "What is RISC-V architecture?"),
        ("Specific Technical", "instruction encoding formats"),
        ("Memory Focus", "memory operations addressing"),
        ("Floating Point", "floating point operations"),
        ("Assembly Focus", "load store instructions"),
    ]
    
    print("\n🎯 TESTING RETRIEVAL METHODS")
    print("="*70)
    
    for query_type, query in test_queries:
        print(f"\n{'='*20} {query_type.upper()} {'='*20}")
        print(f"Query: '{query}'")
        
        # Test Semantic Search
        print("\n📊 SEMANTIC SEARCH RESULTS:")
        semantic_result = rag.query(query, top_k=3)
        
        for i, chunk in enumerate(semantic_result.get('chunks', []), 1):
            score = chunk.get('similarity_score', 0.0)
            title = chunk.get('title', 'No title')
            page = chunk.get('page', 'Unknown')
            text = chunk['text']
            
            print(f"   Result {i}: Score={score:.3f}, Title='{title}', Page={page}")
            print(f"   Size: {len(text)} chars")
            print(f"   Content: '{text[:150]}...'")
            print()
        
        # Test Hybrid Search
        print("🔗 HYBRID SEARCH RESULTS:")
        hybrid_result = rag.hybrid_query(query, top_k=3)
        
        for i, chunk in enumerate(hybrid_result.get('chunks', []), 1):
            score = chunk.get('hybrid_score', 0.0)
            title = chunk.get('title', 'No title')
            page = chunk.get('page', 'Unknown')
            text = chunk['text']
            
            print(f"   Result {i}: Score={score:.3f}, Title='{title}', Page={page}")
            print(f"   Size: {len(text)} chars")
            print(f"   Content: '{text[:150]}...'")
            print()
        
        # Analyze source diversity
        semantic_pages = [chunk.get('page', 0) for chunk in semantic_result.get('chunks', [])]
        hybrid_pages = [chunk.get('page', 0) for chunk in hybrid_result.get('chunks', [])]
        
        print(f"📍 SOURCE DIVERSITY ANALYSIS:")
        print(f"   Semantic pages: {semantic_pages}")
        print(f"   Hybrid pages: {hybrid_pages}")
        print(f"   Semantic unique pages: {len(set(semantic_pages))}")
        print(f"   Hybrid unique pages: {len(set(hybrid_pages))}")
        
        # Score comparison
        semantic_scores = [chunk.get('similarity_score', 0.0) for chunk in semantic_result.get('chunks', [])]
        hybrid_scores = [chunk.get('hybrid_score', 0.0) for chunk in hybrid_result.get('chunks', [])]
        
        print(f"📈 SCORE ANALYSIS:")
        print(f"   Semantic scores: {[f'{s:.3f}' for s in semantic_scores]}")
        print(f"   Hybrid scores: {[f'{s:.3f}' for s in hybrid_scores]}")
        print(f"   Semantic range: {max(semantic_scores) - min(semantic_scores):.3f}")
        print(f"   Hybrid range: {max(hybrid_scores) - min(hybrid_scores):.3f}")
        
        print("\n" + "-"*70)


def analyze_document_coverage():
    """Analyze how well our chunks cover the document."""
    print("\n📚 DOCUMENT COVERAGE ANALYSIS")
    print("="*70)
    
    rag = BasicRAG()
    pdf_path = project_root / "data" / "test" / "riscv-base-instructions.pdf"
    rag.index_document(pdf_path)
    
    # Analyze page distribution
    pages = [chunk.get('page', 0) for chunk in rag.chunks]
    page_counts = {}
    for page in pages:
        page_counts[page] = page_counts.get(page, 0) + 1
    
    print(f"📄 PAGE DISTRIBUTION:")
    print(f"   Total pages with chunks: {len(page_counts)}")
    print(f"   Page range: {min(pages)} - {max(pages)}")
    
    # Show top pages by chunk count
    sorted_pages = sorted(page_counts.items(), key=lambda x: x[1], reverse=True)
    print(f"\n📊 TOP PAGES BY CHUNK COUNT:")
    for page, count in sorted_pages[:10]:
        percentage = count / len(rag.chunks) * 100
        print(f"   Page {page}: {count} chunks ({percentage:.1f}%)")
    
    # Analyze titles
    titles = [chunk.get('title', 'No title') for chunk in rag.chunks]
    title_counts = {}
    for title in titles:
        title_counts[title] = title_counts.get(title, 0) + 1
    
    print(f"\n📝 TITLE DISTRIBUTION:")
    sorted_titles = sorted(title_counts.items(), key=lambda x: x[1], reverse=True)
    for title, count in sorted_titles[:10]:
        percentage = count / len(rag.chunks) * 100
        print(f"   '{title}': {count} chunks ({percentage:.1f}%)")


if __name__ == "__main__":
    test_retrieval_quality()
    analyze_document_coverage()
    
    print("\n🎊 RETRIEVAL QUALITY ANALYSIS COMPLETE!")