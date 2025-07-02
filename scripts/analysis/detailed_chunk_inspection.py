#!/usr/bin/env python3
"""
Detailed Chunk Inspection - Following CLAUDE.md Manual Verification
Examining specific problematic chunks to understand quality issues.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent  # Go up to project-1-technical-rag
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))  # Add rag-portfolio root for shared_utils

from src.basic_rag import BasicRAG


def inspect_chunk_fragments(rag: BasicRAG):
    """Examine fragments to understand why they're incomplete."""
    print("🔍 DETAILED FRAGMENT INSPECTION")
    print("=" * 60)
    
    fragments = []
    for chunk in rag.chunks:
        text = chunk['text'].strip()
        if not (text.endswith(('.', '!', '?', ':', ';')) and 
                (text[0].isupper() or text.startswith(('The ', 'A ', 'An ', 'RISC')))):
            fragments.append(chunk)
    
    print(f"Found {len(fragments)} fragments out of {len(rag.chunks)} total chunks")
    
    for i, chunk in enumerate(fragments[:5]):  # Examine first 5 fragments
        print(f"\n❌ FRAGMENT {i+1}")
        print(f"Source: {Path(chunk['source']).name}")
        print(f"Page: {chunk.get('page', 'Unknown')}")
        print(f"Size: {len(chunk['text'])} chars")
        print(f"Title: {chunk.get('title', 'No title')}")
        print("Full text:")
        print(f'"{chunk["text"]}"')
        print("-" * 40)


def inspect_page_coverage_issue(rag: BasicRAG):
    """Understand why some documents have limited page coverage."""
    print("\n🔍 PAGE COVERAGE DEEP DIVE")
    print("=" * 60)
    
    # Focus on documents with limited coverage
    limited_docs = []
    coverage_data = {}
    
    for chunk in rag.chunks:
        source = Path(chunk['source']).name
        page = chunk.get('page', 0)
        
        if source not in coverage_data:
            coverage_data[source] = {'pages': set(), 'chunks': []}
        
        coverage_data[source]['pages'].add(page)
        coverage_data[source]['chunks'].append(chunk)
    
    for doc, data in coverage_data.items():
        if len(data['pages']) <= 1:
            limited_docs.append((doc, data))
    
    print(f"Documents with limited coverage: {len(limited_docs)}")
    
    for doc, data in limited_docs:
        print(f"\n📄 {doc}")
        print(f"Pages covered: {sorted(list(data['pages']))}")
        print(f"Total chunks: {len(data['chunks'])}")
        
        # Show first few chunks to understand the issue
        print("Sample chunks:")
        for i, chunk in enumerate(data['chunks'][:3]):
            print(f"  {i+1}. Page {chunk.get('page')}, {len(chunk['text'])} chars")
            print(f"     Title: {chunk.get('title', 'No title')}")
            print(f"     Preview: {chunk['text'][:100]}...")


def test_score_variation_manually(rag: BasicRAG):
    """Manually test score variation with controlled queries."""
    print("\n🔍 MANUAL SCORE VARIATION TEST")
    print("=" * 60)
    
    # Test very similar queries
    similar_queries = [
        "RISC-V instruction",
        "RISC-V instructions", 
        "RISC instruction",
        "instruction format"
    ]
    
    print("Testing similar queries for score sensitivity:")
    for query in similar_queries:
        result = rag.hybrid_query(query, top_k=3)
        scores = [chunk.get('hybrid_score', 0) for chunk in result.get('chunks', [])]
        print(f"'{query}': {[f'{s:.6f}' for s in scores]}")
    
    # Test completely different queries
    different_queries = [
        "software validation",
        "medical device guidance", 
        "processor architecture",
        "memory management"
    ]
    
    print("\nTesting different domain queries:")
    for query in different_queries:
        result = rag.hybrid_query(query, top_k=3)
        scores = [chunk.get('hybrid_score', 0) for chunk in result.get('chunks', [])]
        sources = [Path(chunk['source']).name for chunk in result.get('chunks', [])]
        print(f"'{query}': {[f'{s:.6f}' for s in scores]} from {set(sources)}")


def main():
    """Run detailed inspection."""
    print("🔬 DETAILED CHUNK INSPECTION")
    print("Following CLAUDE.md: 'Examine actual content'")
    print("=" * 80)
    
    # Initialize RAG
    rag = BasicRAG()
    data_folder = project_root / "data" / "test"
    results = rag.index_documents(data_folder)
    
    # Detailed inspections
    inspect_chunk_fragments(rag)
    inspect_page_coverage_issue(rag)
    test_score_variation_manually(rag)


if __name__ == "__main__":
    main()