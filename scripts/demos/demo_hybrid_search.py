#!/usr/bin/env python3
"""
Hybrid Search Demo
Demonstrates BM25 sparse retrieval + semantic dense retrieval with RRF fusion.
"""

import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent.parent  # Go up to project-1-technical-rag
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))  # Add rag-portfolio root for shared_utils

from src.sparse_retrieval import BM25SparseRetriever
from src.fusion import reciprocal_rank_fusion
from shared_utils.retrieval.hybrid_search import HybridRetriever


def main():
    print("🔍 Hybrid Search Demo - BM25 + Semantic Retrieval with RRF")
    print("=" * 60)
    
    # Sample technical documentation chunks
    chunks = [
        {
            "text": "RISC-V is an open standard instruction set architecture (ISA) based on established reduced instruction set computer (RISC) principles.",
            "source": "riscv-spec.pdf",
            "page": 1,
            "chunk_id": 0
        },
        {
            "text": "The RV32I base integer instruction set provides 32-bit addresses and integer operations for embedded applications.",
            "source": "riscv-spec.pdf", 
            "page": 2,
            "chunk_id": 1
        },
        {
            "text": "ARM Cortex-M processors are designed specifically for microcontroller applications with emphasis on low power consumption.",
            "source": "arm-guide.pdf",
            "page": 1,
            "chunk_id": 2
        },
        {
            "text": "Machine learning models require substantial amounts of training data to achieve optimal performance in real-world applications.",
            "source": "ml-handbook.pdf",
            "page": 5,
            "chunk_id": 3
        },
        {
            "text": "Vector databases enable efficient similarity search operations on high-dimensional embedding vectors for AI applications.",
            "source": "vector-db-guide.pdf",
            "page": 10,
            "chunk_id": 4
        },
        {
            "text": "The RISC-V Foundation promotes open-source hardware development and provides comprehensive documentation for implementers.",
            "source": "riscv-foundation.pdf",
            "page": 1,
            "chunk_id": 5
        }
    ]
    
    print(f"📚 Indexing {len(chunks)} technical documentation chunks...")
    
    # Initialize hybrid retriever
    hybrid_retriever = HybridRetriever(
        dense_weight=0.7,  # 70% semantic, 30% keyword
        use_mps=False      # Disable for demo compatibility
    )
    
    # Index documents
    hybrid_retriever.index_documents(chunks)
    
    # Test queries demonstrating different search scenarios
    test_queries = [
        ("RV32I", "Exact keyword match test"),
        ("machine learning training", "Semantic similarity test"),
        ("RISC-V embedded systems", "Hybrid keyword + semantic test"),
        ("vector similarity search", "Technical concept search"),
        ("ARM low power", "Multi-term technical search")
    ]
    
    print("\n🔍 Testing Hybrid Search on Various Query Types")
    print("=" * 60)
    
    for query, description in test_queries:
        print(f"\n📝 Query: '{query}' ({description})")
        print("-" * 40)
        
        # Perform hybrid search
        results = hybrid_retriever.search(query, top_k=3)
        
        if not results:
            print("   No results found")
            continue
            
        for i, (chunk_idx, rrf_score, chunk_dict) in enumerate(results, 1):
            print(f"   {i}. Score: {rrf_score:.4f}")
            print(f"      Text: {chunk_dict['text'][:80]}...")
            print(f"      Source: {chunk_dict['source']}")
            
    # Demonstrate weight adjustment effects
    print(f"\n⚖️  Testing Dense Weight Impact on Query: 'RV32I'")
    print("=" * 60)
    
    weights_to_test = [0.1, 0.5, 0.9]  # Sparse-heavy, balanced, semantic-heavy
    
    for weight in weights_to_test:
        print(f"\n🎯 Dense Weight: {weight:.1f} (Semantic: {weight*100:.0f}%, Keyword: {(1-weight)*100:.0f}%)")
        
        # Create retriever with specific weight
        weighted_retriever = HybridRetriever(dense_weight=weight, use_mps=False)
        weighted_retriever.index_documents(chunks)
        
        results = weighted_retriever.search("RV32I", top_k=2)
        
        for i, (chunk_idx, rrf_score, chunk_dict) in enumerate(results, 1):
            print(f"   {i}. Score: {rrf_score:.4f} - {chunk_dict['text'][:60]}...")
    
    # Show retrieval statistics
    print(f"\n📊 Hybrid Retrieval Statistics")
    print("=" * 60)
    
    stats = hybrid_retriever.get_retrieval_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.3f}")
        else:
            print(f"   {key}: {value}")
    
    print(f"\n✅ Hybrid Search Demo Complete!")
    print(f"   - BM25 sparse retrieval: Excellent for exact keyword matching")
    print(f"   - Semantic dense retrieval: Superior for conceptual similarity")
    print(f"   - RRF fusion: Combines both strengths optimally")


if __name__ == "__main__":
    main()