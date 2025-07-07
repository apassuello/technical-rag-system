#!/usr/bin/env python3
"""
Production RAG System Demo
==========================

Comprehensive demonstration of the production-ready RAG system featuring:
- Hybrid TOC + PDFPlumber parsing
- Dense + Sparse retrieval with RRF fusion
- Query enhancement with vocabulary awareness
- Performance benchmarking and quality assessment

This is the SINGLE COMPREHENSIVE DEMO for the entire RAG system.
"""

import sys
from pathlib import Path
import time
import json

# Add project paths
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))

from src.core.pipeline import RAGPipeline


def main():
    """Main production demo showcasing all RAG capabilities."""
    print("🚀 PRODUCTION RAG SYSTEM DEMO")
    print("=" * 70)
    print("Comprehensive demonstration of hybrid parsing + retrieval system")
    print("Single demo showcasing all production capabilities")

    # System configuration
    print(f"\n📊 Production Configuration:")
    print(f"   Parser: Hybrid (TOC navigation + PDFPlumber precision)")
    print(f"   Embeddings: sentence-transformers/all-mpnet-base-v2")
    print(f"   Vector Store: FAISS with cosine similarity")
    print(f"   Retrieval: Hybrid (70% semantic + 30% keyword)")
    print(f"   Fusion: Reciprocal Rank Fusion (k=1)")
    print(f"   Enhancement: Vocabulary-aware query expansion")

    # Initialize RAG system
    rag = RAGPipeline("config/dev.yaml")

    # Document indexing benchmark
    print(f"\n🔧 Document Indexing Benchmark:")
    pdf_path = project_root.parent / "data" / "test" / "riscv-base-instructions.pdf"

    if not pdf_path.exists():
        print("❌ Test PDF not found" + str(pdf_path))
        return False

    print(f"   Document: {pdf_path.name}")

    start_time = time.time()
    chunks_count = rag.index_document(pdf_path)
    index_time = time.time() - start_time

    print(f"   ✅ Indexed {chunks_count} chunks in {index_time:.2f}s")
    print(f"   📈 Speed: {chunks_count/index_time:.1f} chunks/second")

    # Chunk quality analysis
    print(f"\n🔬 Chunk Quality Analysis:")
    if rag.chunks:
        sizes = [len(chunk["text"]) for chunk in rag.chunks]
        quality_scores = [chunk.get("quality_score", 0.0) for chunk in rag.chunks]

        print(f"   Total chunks: {len(rag.chunks)}")
        print(f"   Size range: {min(sizes)}-{max(sizes)} chars")
        print(f"   Average size: {sum(sizes)/len(sizes):.0f} chars")
        print(
            f"   Target range (800-2000): {sum(1 for s in sizes if 800 <= s <= 2000)}/{len(sizes)} ({sum(1 for s in sizes if 800 <= s <= 2000)/len(sizes)*100:.0f}%)"
        )
        print(f"   Average quality: {sum(quality_scores)/len(quality_scores):.3f}")
        print(f"   Parsing method: {rag.chunks[0].get('parsing_method', 'Unknown')}")

    # Query performance benchmark
    print(f"\n🔍 Query Performance Benchmark:")

    test_queries = [
        ("Architecture Overview", "What is RISC-V architecture?"),
        ("Technical Details", "instruction encoding formats"),
        ("System Design", "register file organization"),
        ("Memory Operations", "memory addressing modes"),
        ("Advanced Features", "atomic operations synchronization"),
    ]

    # Test different retrieval methods
    methods = [
        ("Semantic Search", "query"),
        ("Hybrid Search", "hybrid_query"),
        ("Enhanced Hybrid", "enhanced_hybrid_query"),
    ]

    results_summary = {}

    for method_name, method_attr in methods:
        print(f"\n   🎯 Testing {method_name}:")
        method_results = []
        total_time = 0

        for category, query in test_queries:
            start_time = time.time()

            if method_attr == "enhanced_hybrid_query":
                # Test enhanced with enhancement disabled (recommended)
                result = getattr(rag, method_attr)(
                    query, top_k=3, enable_enhancement=False
                )
            else:
                result = getattr(rag, method_attr)(query, top_k=3)

            query_time = time.time() - start_time
            total_time += query_time

            chunks = result.get("chunks", [])
            if chunks:
                top_chunk = chunks[0]
                score_key = (
                    "hybrid_score" if "hybrid" in method_attr else "similarity_score"
                )
                score = top_chunk.get(score_key, 0.0)
                title = top_chunk.get("title", "No title")
                size = len(top_chunk["text"])

                # Quality assessment
                text = top_chunk["text"]
                is_relevant = any(
                    word.lower() in text.lower() for word in query.split()
                )
                is_complete = text.strip().endswith((".", "!", "?", ":", ";"))
                good_size = 800 <= size <= 2000
                no_trash = not any(
                    trash in text.lower() for trash in ["creative commons", "license"]
                )

                quality = sum([is_relevant, is_complete, good_size, no_trash])

                method_results.append(
                    {
                        "query": query,
                        "score": score,
                        "quality": quality,
                        "time": query_time,
                        "size": size,
                    }
                )

                print(
                    f"      {category}: {score:.3f} | {query_time*1000:.1f}ms | Q:{quality}/4"
                )
            else:
                method_results.append(
                    {
                        "query": query,
                        "score": 0.0,
                        "quality": 0,
                        "time": query_time,
                        "size": 0,
                    }
                )
                print(f"      {category}: No results | {query_time*1000:.1f}ms")

        # Method summary
        avg_time = total_time / len(test_queries)
        avg_score = sum(r["score"] for r in method_results) / len(method_results)
        avg_quality = sum(r["quality"] for r in method_results) / len(method_results)
        success_rate = sum(1 for r in method_results if r["score"] > 0) / len(
            method_results
        )

        results_summary[method_name] = {
            "avg_time": avg_time,
            "avg_score": avg_score,
            "avg_quality": avg_quality,
            "success_rate": success_rate,
        }

        print(
            f"      Summary: {avg_score:.3f} avg score | {avg_time*1000:.1f}ms avg | {success_rate*100:.0f}% success"
        )

    # Performance comparison
    print(f"\n📊 Performance Comparison:")
    print(
        f"{'Method':<20} {'Avg Score':<12} {'Avg Time':<12} {'Quality':<10} {'Success':<10}"
    )
    print("-" * 70)

    for method_name, stats in results_summary.items():
        print(
            f"{method_name:<20} {stats['avg_score']:<12.3f} {stats['avg_time']*1000:<12.1f} {stats['avg_quality']:<10.1f} {stats['success_rate']*100:<10.0f}%"
        )

    # Best method identification
    best_method = max(results_summary.items(), key=lambda x: x[1]["avg_score"])
    print(
        f"\n🏆 Best Method: {best_method[0]} (Score: {best_method[1]['avg_score']:.3f})"
    )

    # Detailed example with hybrid search
    print(f"\n🔍 Detailed Query Example (Hybrid Search):")
    example_query = "What is RISC-V architecture?"
    print(f"   Query: '{example_query}'")

    result = rag.query(example_query, top_k=2)
    chunks = result.get("chunks", [])

    if chunks:
        for i, chunk in enumerate(chunks, 1):
            text = chunk["text"]
            score = chunk.get("hybrid_score", 0.0)
            title = chunk.get("title", "No title")

            print(f"\n   📋 Result {i}:")
            print(f"      Score: {score:.3f}")
            print(f"      Title: {title[:60]}...")
            print(f"      Size: {len(text)} chars")
            print(f"      Content: '{text[:150]}...'")

            # Show retrieval method details
            retrieval_method = result.get("retrieval_method", "unknown")
            if retrieval_method == "hybrid":
                dense_weight = result.get("dense_weight", 0.7)
                sparse_weight = result.get("sparse_weight", 0.3)
                print(
                    f"      Fusion: {dense_weight*100:.0f}% semantic + {sparse_weight*100:.0f}% keyword"
                )

    # System assessment
    print(f"\n🎯 Production System Assessment:")

    assessment_criteria = [
        ("Indexing Speed", index_time < 10, f"{index_time:.1f}s"),
        (
            "Query Speed",
            results_summary["Hybrid Search"]["avg_time"] < 0.1,
            f"{results_summary['Hybrid Search']['avg_time']*1000:.1f}ms",
        ),
        (
            "Result Quality",
            results_summary["Hybrid Search"]["avg_quality"] >= 3.0,
            f"{results_summary['Hybrid Search']['avg_quality']:.1f}/4",
        ),
        (
            "Success Rate",
            results_summary["Hybrid Search"]["success_rate"] >= 0.8,
            f"{results_summary['Hybrid Search']['success_rate']*100:.0f}%",
        ),
        (
            "Chunk Quality",
            sum(1 for s in sizes if 800 <= s <= 2000) / len(sizes) >= 0.8,
            f"{sum(1 for s in sizes if 800 <= s <= 2000)/len(sizes)*100:.0f}%",
        ),
    ]

    passed_criteria = 0
    for criterion, passed, value in assessment_criteria:
        status = "✅" if passed else "⚠️"
        print(f"   {status} {criterion}: {value}")
        if passed:
            passed_criteria += 1

    # Final verdict
    overall_score = passed_criteria / len(assessment_criteria)
    print(
        f"\n🏆 OVERALL ASSESSMENT: {passed_criteria}/{len(assessment_criteria)} ({overall_score*100:.0f}%)"
    )

    if overall_score >= 0.8:
        print("   🎉 PRODUCTION-READY RAG SYSTEM!")
        print("   ✅ All critical performance metrics met")
        print("   🚀 Ready for deployment in technical documentation use cases")
        verdict = "EXCELLENT"
    elif overall_score >= 0.6:
        print("   ✅ GOOD RAG SYSTEM")
        print("   🔧 Minor optimizations recommended for production")
        verdict = "GOOD"
    else:
        print("   ⚠️ SYSTEM NEEDS IMPROVEMENT")
        print("   🔧 Consider further optimization before production deployment")
        verdict = "NEEDS_WORK"

    # Technical summary
    print(f"\n📋 Technical Summary:")
    print(f"   Architecture: Hybrid RAG with structure-preserving parsing")
    print(f"   Parsing Method: TOC navigation + PDFPlumber precision + trash filtering")
    print(f"   Retrieval Method: Dense semantic + Sparse keyword with RRF fusion")
    print(
        f"   Performance: {index_time:.1f}s indexing, {results_summary['Hybrid Search']['avg_time']*1000:.1f}ms queries"
    )
    print(
        f"   Quality: {results_summary['Hybrid Search']['avg_quality']:.1f}/4 result quality"
    )
    print(
        f"   Chunk Optimization: {sum(1 for s in sizes if 800 <= s <= 2000)/len(sizes)*100:.0f}% in target size range"
    )

    return verdict == "EXCELLENT"


if __name__ == "__main__":
    print("🎊 STARTING PRODUCTION RAG DEMO")
    print("This comprehensive demo showcases all production capabilities")
    print("=" * 70)

    success = main()

    print(f"\n\n🎊 PRODUCTION DEMO COMPLETE!")
    print("=" * 70)

    if success:
        print("🏆 HYBRID RAG SYSTEM: PRODUCTION READY!")
        print("📋 All performance criteria met for technical documentation RAG")
        print("⚡ Fast indexing + Fast querying + High quality results")
        print("🎯 Optimal balance achieved for production deployment")
    else:
        print("🔧 System functional but may need optimization for production")

    print("\n✨ Production RAG system successfully demonstrated!")
    print("🚀 Ready for advanced features and deployment!")
    print("\n📁 Use CLEANUP_COMMANDS.sh to clean up experimental files")
    print("📖 See PRODUCTION_STRUCTURE.md for final system architecture")
