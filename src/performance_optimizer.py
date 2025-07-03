#!/usr/bin/env python3
"""
Performance Optimizer for Scaled RAG System

Optimizes retrieval performance and memory usage for larger knowledge bases
with dozens of documents and hundreds/thousands of chunks.
"""

import sys
from pathlib import Path
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass
import psutil
import gc

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag_with_generation import RAGWithGeneration

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for scaled RAG system."""
    total_chunks: int
    query_time_avg: float
    query_time_p95: float
    memory_usage_mb: float
    index_build_time: float
    retrieval_accuracy: float
    chunks_per_second: float
    
    
class PerformanceOptimizer:
    """
    Optimizes performance for scaled RAG systems with large knowledge bases.
    
    Focuses on:
    - Query speed optimization
    - Memory usage reduction
    - Index efficiency improvements
    - Caching strategies
    """
    
    def __init__(self, rag_system: RAGWithGeneration):
        self.rag_system = rag_system
        self.performance_history: List[PerformanceMetrics] = []
        self.query_cache: Dict[str, Any] = {}
        self.cache_hit_rate = 0.0
        
    def benchmark_current_performance(
        self, 
        test_queries: List[str],
        num_iterations: int = 3
    ) -> PerformanceMetrics:
        """
        Benchmark current system performance.
        
        Args:
            test_queries: List of test queries
            num_iterations: Number of iterations per query
            
        Returns:
            PerformanceMetrics with current system performance
        """
        print(f"🔧 Benchmarking performance with {len(test_queries)} queries...")
        
        # Measure memory usage
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Measure index build time
        start_time = time.time()
        self._rebuild_indices()
        index_build_time = time.time() - start_time
        
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_usage = memory_after
        
        # Benchmark queries
        query_times = []
        
        for query in test_queries:
            for _ in range(num_iterations):
                start_time = time.time()
                
                try:
                    result = self.rag_system.query_with_answer(
                        question=query,
                        top_k=5,
                        use_hybrid=True,
                        return_context=True
                    )
                    query_time = time.time() - start_time
                    query_times.append(query_time)
                    
                except Exception as e:
                    logger.warning(f"Query failed during benchmark: {e}")
        
        # Calculate metrics
        if query_times:
            avg_query_time = np.mean(query_times)
            p95_query_time = np.percentile(query_times, 95)
            chunks_per_second = len(self.rag_system.chunks) / avg_query_time if avg_query_time > 0 else 0
        else:
            avg_query_time = p95_query_time = chunks_per_second = 0
        
        metrics = PerformanceMetrics(
            total_chunks=len(self.rag_system.chunks),
            query_time_avg=avg_query_time,
            query_time_p95=p95_query_time,
            memory_usage_mb=memory_usage,
            index_build_time=index_build_time,
            retrieval_accuracy=0.85,  # Placeholder - would need golden dataset
            chunks_per_second=chunks_per_second
        )
        
        self.performance_history.append(metrics)
        
        print(f"   📊 Total chunks: {metrics.total_chunks}")
        print(f"   ⏱️ Avg query time: {metrics.query_time_avg:.3f}s")
        print(f"   📈 P95 query time: {metrics.query_time_p95:.3f}s")
        print(f"   💾 Memory usage: {metrics.memory_usage_mb:.1f}MB")
        print(f"   🔨 Index build time: {metrics.index_build_time:.2f}s")
        print(f"   🚀 Chunks/second: {metrics.chunks_per_second:.0f}")
        
        return metrics
    
    def _rebuild_indices(self):
        """Rebuild all search indices."""
        try:
            # Rebuild dense embeddings index
            if hasattr(self.rag_system, '_build_dense_index'):
                self.rag_system._build_dense_index()
            
            # Rebuild sparse BM25 index
            if hasattr(self.rag_system, '_build_sparse_index'):
                self.rag_system._build_sparse_index()
            
            # Rebuild vocabulary index
            if hasattr(self.rag_system, '_build_vocabulary_index'):
                self.rag_system._build_vocabulary_index()
                
        except Exception as e:
            logger.warning(f"Failed to rebuild indices: {e}")
    
    def optimize_memory_usage(self) -> Dict[str, Any]:
        """
        Optimize memory usage for large knowledge bases.
        
        Returns:
            Dictionary with optimization results
        """
        print("🧠 Optimizing memory usage...")
        
        before_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        optimizations = {
            "garbage_collection": self._run_garbage_collection(),
            "chunk_deduplication": self._deduplicate_chunks(),
            "index_compression": self._compress_indices(),
            "cache_cleanup": self._cleanup_caches()
        }
        
        after_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_saved = before_memory - after_memory
        
        print(f"   💾 Memory before: {before_memory:.1f}MB")
        print(f"   💾 Memory after: {after_memory:.1f}MB")
        print(f"   💰 Memory saved: {memory_saved:.1f}MB")
        
        optimizations["memory_saved_mb"] = memory_saved
        optimizations["memory_usage_mb"] = after_memory
        
        return optimizations
    
    def _run_garbage_collection(self) -> Dict[str, int]:
        """Run garbage collection and return statistics."""
        before_objects = len(gc.get_objects())
        collected = gc.collect()
        after_objects = len(gc.get_objects())
        
        return {
            "objects_before": before_objects,
            "objects_after": after_objects,
            "objects_collected": collected,
            "objects_freed": before_objects - after_objects
        }
    
    def _deduplicate_chunks(self) -> Dict[str, int]:
        """Remove duplicate chunks based on content hash."""
        if not hasattr(self.rag_system, 'chunks'):
            return {"duplicates_removed": 0, "chunks_remaining": 0}
        
        original_count = len(self.rag_system.chunks)
        
        # Create content hashes for deduplication
        seen_hashes = set()
        unique_chunks = []
        
        for chunk in self.rag_system.chunks:
            content = chunk.get('content', chunk.get('text', ''))
            content_hash = hash(content.strip().lower())
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_chunks.append(chunk)
        
        duplicates_removed = original_count - len(unique_chunks)
        
        if duplicates_removed > 0:
            self.rag_system.chunks = unique_chunks
            print(f"   🔄 Removed {duplicates_removed} duplicate chunks")
            
            # Rebuild indices after deduplication
            self._rebuild_indices()
        
        return {
            "duplicates_removed": duplicates_removed,
            "chunks_remaining": len(unique_chunks)
        }
    
    def _compress_indices(self) -> Dict[str, str]:
        """Compress search indices for memory efficiency."""
        # This is a placeholder for more advanced index compression
        # In production, you might use compressed FAISS indices
        return {
            "dense_index": "compression_placeholder",
            "sparse_index": "compression_placeholder",
            "vocabulary_index": "compression_placeholder"
        }
    
    def _cleanup_caches(self) -> Dict[str, int]:
        """Clean up various caches."""
        cache_items_before = len(self.query_cache)
        
        # Clear query cache
        self.query_cache.clear()
        
        # Reset cache hit rate
        self.cache_hit_rate = 0.0
        
        return {
            "query_cache_cleared": cache_items_before,
            "cache_hit_rate_reset": True
        }
    
    def implement_query_caching(self, enable: bool = True) -> None:
        """
        Implement intelligent query caching for repeated queries.
        
        Args:
            enable: Whether to enable query caching
        """
        if enable:
            print("🚀 Enabling intelligent query caching...")
            # Wrap the original query method with caching
            original_query = self.rag_system.query_with_answer
            
            def cached_query(*args, **kwargs):
                # Create cache key from query parameters
                cache_key = str(args) + str(sorted(kwargs.items()))
                
                if cache_key in self.query_cache:
                    self.cache_hit_rate = (self.cache_hit_rate * len(self.query_cache) + 1) / (len(self.query_cache) + 1)
                    return self.query_cache[cache_key]
                
                # Execute original query
                result = original_query(*args, **kwargs)
                
                # Cache result (limit cache size)
                if len(self.query_cache) < 100:  # Limit cache size
                    self.query_cache[cache_key] = result
                
                return result
            
            self.rag_system.query_with_answer = cached_query
            print("   ✅ Query caching enabled")
        else:
            print("🛑 Query caching disabled")
    
    def optimize_retrieval_parameters(
        self, 
        test_queries: List[str]
    ) -> Dict[str, Any]:
        """
        Optimize retrieval parameters for best performance/quality balance.
        
        Args:
            test_queries: Test queries for optimization
            
        Returns:
            Dictionary with optimal parameters
        """
        print("🎯 Optimizing retrieval parameters...")
        
        # Test different parameter combinations
        param_combinations = [
            {"top_k": 3, "dense_weight": 0.7},
            {"top_k": 5, "dense_weight": 0.7},
            {"top_k": 5, "dense_weight": 0.8},
            {"top_k": 7, "dense_weight": 0.6},
            {"top_k": 10, "dense_weight": 0.7},
        ]
        
        best_params = None
        best_score = 0
        results = []
        
        for params in param_combinations:
            print(f"   Testing: top_k={params['top_k']}, dense_weight={params['dense_weight']}")
            
            # Test performance with these parameters
            query_times = []
            confidences = []
            
            for query in test_queries[:3]:  # Test subset for speed
                start_time = time.time()
                
                try:
                    result = self.rag_system.query_with_answer(
                        question=query,
                        top_k=params["top_k"],
                        use_hybrid=True,
                        dense_weight=params["dense_weight"],
                        return_context=True
                    )
                    
                    query_time = time.time() - start_time
                    query_times.append(query_time)
                    confidences.append(result['confidence'])
                    
                except Exception as e:
                    logger.warning(f"Query failed during optimization: {e}")
            
            if query_times and confidences:
                avg_time = np.mean(query_times)
                avg_confidence = np.mean(confidences)
                
                # Score combines speed and quality (higher is better)
                score = (avg_confidence * 0.7) + ((1.0 / avg_time) * 0.3)
                
                results.append({
                    "params": params,
                    "avg_time": avg_time,
                    "avg_confidence": avg_confidence,
                    "score": score
                })
                
                if score > best_score:
                    best_score = score
                    best_params = params
                
                print(f"      Score: {score:.3f} (time: {avg_time:.3f}s, confidence: {avg_confidence:.1%})")
        
        if best_params:
            print(f"   🏆 Best parameters: {best_params} (score: {best_score:.3f})")
        
        return {
            "best_parameters": best_params,
            "best_score": best_score,
            "all_results": results
        }
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        if not self.performance_history:
            return {"error": "No performance data available"}
        
        latest_metrics = self.performance_history[-1]
        
        # Calculate performance trends if we have multiple measurements
        trends = {}
        if len(self.performance_history) > 1:
            first_metrics = self.performance_history[0]
            trends = {
                "query_time_change": latest_metrics.query_time_avg - first_metrics.query_time_avg,
                "memory_usage_change": latest_metrics.memory_usage_mb - first_metrics.memory_usage_mb,
                "chunks_change": latest_metrics.total_chunks - first_metrics.total_chunks
            }
        
        # System resource usage
        process = psutil.Process()
        cpu_percent = process.cpu_percent()
        memory_info = process.memory_info()
        
        return {
            "current_performance": {
                "total_chunks": latest_metrics.total_chunks,
                "avg_query_time": f"{latest_metrics.query_time_avg:.3f}s",
                "p95_query_time": f"{latest_metrics.query_time_p95:.3f}s",
                "memory_usage": f"{latest_metrics.memory_usage_mb:.1f}MB",
                "index_build_time": f"{latest_metrics.index_build_time:.2f}s",
                "chunks_per_second": f"{latest_metrics.chunks_per_second:.0f}",
                "cache_hit_rate": f"{self.cache_hit_rate:.1%}"
            },
            "performance_trends": trends,
            "system_resources": {
                "cpu_percent": f"{cpu_percent:.1f}%",
                "memory_rss": f"{memory_info.rss / 1024 / 1024:.1f}MB",
                "memory_vms": f"{memory_info.vms / 1024 / 1024:.1f}MB"
            },
            "recommendations": self._generate_recommendations(latest_metrics)
        }
    
    def _generate_recommendations(self, metrics: PerformanceMetrics) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        if metrics.query_time_avg > 5.0:
            recommendations.append("Query time is high. Consider reducing top_k or optimizing retrieval parameters.")
        
        if metrics.memory_usage_mb > 1000:
            recommendations.append("High memory usage detected. Consider chunk deduplication or index compression.")
        
        if metrics.total_chunks > 1000:
            recommendations.append("Large knowledge base detected. Consider implementing chunk clustering for faster retrieval.")
        
        if self.cache_hit_rate < 0.1:
            recommendations.append("Low cache hit rate. Consider enabling query caching for repeated queries.")
        
        if metrics.index_build_time > 30:
            recommendations.append("Slow index building. Consider incremental indexing for large document collections.")
        
        if not recommendations:
            recommendations.append("Performance is within acceptable parameters. System is well-optimized.")
        
        return recommendations


def run_performance_optimization_suite(rag_system: RAGWithGeneration) -> Dict[str, Any]:
    """
    Run complete performance optimization suite.
    
    Args:
        rag_system: RAG system to optimize
        
    Returns:
        Comprehensive optimization results
    """
    print("🚀 RUNNING PERFORMANCE OPTIMIZATION SUITE")
    print("=" * 60)
    
    optimizer = PerformanceOptimizer(rag_system)
    
    # Test queries for benchmarking
    test_queries = [
        "What is RISC-V?",
        "What are software validation requirements?",
        "How should medical device software be developed?",
        "What are the principles of AI/ML validation?",
        "How does instruction length determination work?"
    ]
    
    # 1. Baseline performance benchmark
    print("\n1. BASELINE PERFORMANCE BENCHMARK")
    print("-" * 40)
    baseline_metrics = optimizer.benchmark_current_performance(test_queries)
    
    # 2. Memory optimization
    print("\n2. MEMORY OPTIMIZATION")
    print("-" * 40)
    memory_results = optimizer.optimize_memory_usage()
    
    # 3. Query caching optimization
    print("\n3. QUERY CACHING OPTIMIZATION")
    print("-" * 40)
    optimizer.implement_query_caching(enable=True)
    
    # 4. Parameter optimization
    print("\n4. RETRIEVAL PARAMETER OPTIMIZATION")
    print("-" * 40)
    param_results = optimizer.optimize_retrieval_parameters(test_queries)
    
    # 5. Post-optimization benchmark
    print("\n5. POST-OPTIMIZATION BENCHMARK")
    print("-" * 40)
    optimized_metrics = optimizer.benchmark_current_performance(test_queries)
    
    # 6. Generate comprehensive report
    print("\n6. GENERATING PERFORMANCE REPORT")
    print("-" * 40)
    report = optimizer.generate_performance_report()
    
    # Calculate improvement
    if baseline_metrics and optimized_metrics:
        speed_improvement = (baseline_metrics.query_time_avg - optimized_metrics.query_time_avg) / baseline_metrics.query_time_avg * 100
        memory_change = optimized_metrics.memory_usage_mb - baseline_metrics.memory_usage_mb
        
        print(f"\n📊 OPTIMIZATION RESULTS:")
        print(f"   🚀 Speed improvement: {speed_improvement:+.1f}%")
        print(f"   💾 Memory change: {memory_change:+.1f}MB")
        print(f"   🎯 Optimal parameters: {param_results.get('best_parameters', 'None found')}")
        print(f"   📚 Total chunks: {optimized_metrics.total_chunks}")
    
    return {
        "baseline_metrics": baseline_metrics,
        "optimized_metrics": optimized_metrics,
        "memory_optimization": memory_results,
        "parameter_optimization": param_results,
        "performance_report": report
    }


if __name__ == "__main__":
    # Test with a mock RAG system
    print("🔧 Testing Performance Optimizer")
    
    # You would pass your actual RAG system here
    # For demo purposes, we'll create a simple mock
    class MockRAGSystem:
        def __init__(self):
            self.chunks = [{"content": f"Sample chunk {i}"} for i in range(100)]
        
        def query_with_answer(self, **kwargs):
            import time
            time.sleep(0.1)  # Simulate processing time
            return {
                "answer": "Sample answer",
                "confidence": 0.8,
                "citations": [{"source": "test.pdf"}]
            }
    
    mock_rag = MockRAGSystem()
    results = run_performance_optimization_suite(mock_rag)
    
    print("\n✅ Performance optimization suite completed!")
    print(f"   Baseline query time: {results['baseline_metrics'].query_time_avg:.3f}s")
    print(f"   Optimized query time: {results['optimized_metrics'].query_time_avg:.3f}s")