#!/usr/bin/env python3
"""
Performance Benchmarking Suite - Phase 6.4

Comprehensive performance comparison between BasicRAG and RAGPipeline systems including:
1. Document indexing performance
2. Query response times
3. Memory usage analysis
4. Concurrent query handling
5. Resource utilization
6. Scalability testing

This provides performance validation for migration decisions.
"""

import sys
import time
import psutil
import threading
import statistics
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import gc
import numpy as np
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import both systems
from src.basic_rag import BasicRAG
from src.core.pipeline import RAGPipeline

# Import components for auto-registration
from src.components.processors.pdf_processor import HybridPDFProcessor
from src.components.embedders.sentence_transformer_embedder import SentenceTransformerEmbedder
from src.components.vector_stores.faiss_store import FAISSVectorStore
from src.components.retrievers.hybrid_retriever import HybridRetriever
from src.components.generators.adaptive_generator import AdaptiveAnswerGenerator

@dataclass
class PerformanceMetrics:
    """Performance metrics for a single operation."""
    operation: str
    system: str
    execution_time: float
    memory_before: float
    memory_after: float
    memory_peak: float
    cpu_percent: float
    success: bool
    error_message: Optional[str] = None

@dataclass
class IndexingBenchmark:
    """Benchmarking results for document indexing."""
    document_path: str
    document_size_mb: float
    old_system_metrics: PerformanceMetrics
    new_system_metrics: PerformanceMetrics
    speedup_factor: float
    memory_efficiency: float
    chunks_old: int
    chunks_new: int

@dataclass
class QueryBenchmark:
    """Benchmarking results for query performance."""
    query: str
    old_system_metrics: PerformanceMetrics
    new_system_metrics: PerformanceMetrics
    speedup_factor: float
    memory_efficiency: float

@dataclass
class ConcurrencyBenchmark:
    """Benchmarking results for concurrent query handling."""
    num_threads: int
    queries_per_thread: int
    old_system_throughput: float  # queries per second
    new_system_throughput: float
    old_system_avg_latency: float
    new_system_avg_latency: float
    old_system_error_rate: float
    new_system_error_rate: float

@dataclass
class ScalabilityBenchmark:
    """Benchmarking results for scalability testing."""
    document_count: int
    index_size_old: int  # number of chunks
    index_size_new: int
    indexing_time_old: float
    indexing_time_new: float
    query_time_old: float
    query_time_new: float
    memory_usage_old: float
    memory_usage_new: float

@dataclass
class BenchmarkReport:
    """Complete performance benchmark report."""
    timestamp: str
    test_environment: Dict[str, Any]
    indexing_benchmarks: List[IndexingBenchmark]
    query_benchmarks: List[QueryBenchmark]
    concurrency_benchmarks: List[ConcurrencyBenchmark]
    scalability_benchmarks: List[ScalabilityBenchmark]
    summary_statistics: Dict[str, float]
    recommendations: List[str]

class PerformanceBenchmarker:
    """Handles comprehensive performance benchmarking."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or (project_root / "config" / "default.yaml")
        self.process = psutil.Process()
        
        # Test queries for benchmarking
        self.test_queries = [
            "What is RISC-V?",
            "How do RISC-V instructions work?",
            "What are the main features of the base integer instruction set?",
            "Explain the register file organization in RISC-V",
            "What is the purpose of immediate encoding in RISC-V instructions?",
            "How does the instruction fetch process work?",
            "What are the different types of RISC-V instructions?",
            "Describe the memory addressing modes",
            "What is the role of the program counter?",
            "How are control flow instructions implemented?"
        ]
    
    def run_comprehensive_benchmark(self, test_documents: List[Path]) -> BenchmarkReport:
        """
        Run comprehensive performance benchmarking.
        
        Args:
            test_documents: List of documents to benchmark with
            
        Returns:
            Complete benchmark report
        """
        print("⚡ Starting comprehensive performance benchmarking...")
        print(f"Testing with {len(test_documents)} documents")
        print(f"System: {psutil.cpu_count()} cores, {psutil.virtual_memory().total // 1024**3}GB RAM")
        
        # Collect environment info
        test_env = self._collect_environment_info()
        
        # Run different benchmark categories
        indexing_benchmarks = self._benchmark_indexing(test_documents)
        query_benchmarks = self._benchmark_queries()
        concurrency_benchmarks = self._benchmark_concurrency()
        scalability_benchmarks = self._benchmark_scalability(test_documents)
        
        # Calculate summary statistics
        summary_stats = self._calculate_summary_statistics(
            indexing_benchmarks, query_benchmarks, concurrency_benchmarks, scalability_benchmarks
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(summary_stats)
        
        report = BenchmarkReport(
            timestamp=datetime.now().isoformat(),
            test_environment=test_env,
            indexing_benchmarks=indexing_benchmarks,
            query_benchmarks=query_benchmarks,
            concurrency_benchmarks=concurrency_benchmarks,
            scalability_benchmarks=scalability_benchmarks,
            summary_statistics=summary_stats,
            recommendations=recommendations
        )
        
        print(f"\n📊 Benchmarking complete!")
        self._print_summary(report)
        
        return report
    
    def _collect_environment_info(self) -> Dict[str, Any]:
        """Collect information about the test environment."""
        return {
            "cpu_count": psutil.cpu_count(),
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "memory_total_gb": psutil.virtual_memory().total // 1024**3,
            "python_version": sys.version,
            "platform": sys.platform,
            "timestamp": datetime.now().isoformat()
        }
    
    def _benchmark_indexing(self, test_documents: List[Path]) -> List[IndexingBenchmark]:
        """Benchmark document indexing performance."""
        print("\n📚 Benchmarking document indexing...")
        benchmarks = []
        
        for doc_path in test_documents:
            if not doc_path.exists():
                continue
                
            print(f"  Testing: {doc_path.name}")
            doc_size_mb = doc_path.stat().st_size / 1024 / 1024
            
            # Benchmark old system
            old_metrics, chunks_old = self._benchmark_indexing_system(doc_path, "old")
            
            # Force garbage collection and clear memory
            gc.collect()
            time.sleep(1)
            
            # Benchmark new system
            new_metrics, chunks_new = self._benchmark_indexing_system(doc_path, "new")
            
            # Calculate derived metrics
            speedup_factor = old_metrics.execution_time / new_metrics.execution_time if new_metrics.execution_time > 0 else 1.0
            memory_efficiency = old_metrics.memory_peak / new_metrics.memory_peak if new_metrics.memory_peak > 0 else 1.0
            
            benchmark = IndexingBenchmark(
                document_path=str(doc_path),
                document_size_mb=doc_size_mb,
                old_system_metrics=old_metrics,
                new_system_metrics=new_metrics,
                speedup_factor=speedup_factor,
                memory_efficiency=memory_efficiency,
                chunks_old=chunks_old,
                chunks_new=chunks_new
            )
            
            benchmarks.append(benchmark)
            print(f"    Speedup: {speedup_factor:.2f}x, Memory efficiency: {memory_efficiency:.2f}x")
        
        return benchmarks
    
    def _benchmark_indexing_system(self, doc_path: Path, system_type: str) -> Tuple[PerformanceMetrics, int]:
        """Benchmark indexing for a specific system."""
        memory_before = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_peak = memory_before
        chunks_count = 0
        
        try:
            if system_type == "old":
                start_time = time.time()
                rag_system = BasicRAG()
                chunks_count = rag_system.index_document(doc_path)
                execution_time = time.time() - start_time
            else:  # new system
                start_time = time.time()
                rag_system = RAGPipeline(self.config_path)
                chunks_count = rag_system.index_document(doc_path)
                execution_time = time.time() - start_time
            
            memory_after = self.process.memory_info().rss / 1024 / 1024  # MB
            memory_peak = max(memory_peak, memory_after)
            cpu_percent = self.process.cpu_percent()
            
            metrics = PerformanceMetrics(
                operation="index_document",
                system=system_type,
                execution_time=execution_time,
                memory_before=memory_before,
                memory_after=memory_after,
                memory_peak=memory_peak,
                cpu_percent=cpu_percent,
                success=True
            )
            
        except Exception as e:
            metrics = PerformanceMetrics(
                operation="index_document",
                system=system_type,
                execution_time=0.0,
                memory_before=memory_before,
                memory_after=memory_before,
                memory_peak=memory_before,
                cpu_percent=0.0,
                success=False,
                error_message=str(e)
            )
        
        return metrics, chunks_count
    
    def _benchmark_queries(self) -> List[QueryBenchmark]:
        """Benchmark query performance."""
        print("\n🔍 Benchmarking query performance...")
        
        # Initialize both systems with the same document
        test_doc = project_root / "data" / "test" / "riscv-base-instructions.pdf"
        if not test_doc.exists():
            print("⚠️ Test document not found, skipping query benchmarks")
            return []
        
        print("  Initializing systems...")
        old_system = BasicRAG()
        old_system.index_document(test_doc)
        
        new_system = RAGPipeline(self.config_path)
        new_system.index_document(test_doc)
        
        benchmarks = []
        
        print("  Testing queries...")
        for i, query in enumerate(self.test_queries[:5]):  # Test first 5 queries
            print(f"    Query {i+1}: {query[:50]}...")
            
            # Benchmark old system
            old_metrics = self._benchmark_query_system(old_system, query, "old")
            
            # Benchmark new system
            new_metrics = self._benchmark_query_system(new_system, query, "new")
            
            # Calculate derived metrics
            speedup_factor = old_metrics.execution_time / new_metrics.execution_time if new_metrics.execution_time > 0 else 1.0
            memory_efficiency = old_metrics.memory_peak / new_metrics.memory_peak if new_metrics.memory_peak > 0 else 1.0
            
            benchmark = QueryBenchmark(
                query=query,
                old_system_metrics=old_metrics,
                new_system_metrics=new_metrics,
                speedup_factor=speedup_factor,
                memory_efficiency=memory_efficiency
            )
            
            benchmarks.append(benchmark)
        
        return benchmarks
    
    def _benchmark_query_system(self, rag_system, query: str, system_type: str) -> PerformanceMetrics:
        """Benchmark query for a specific system."""
        memory_before = self.process.memory_info().rss / 1024 / 1024  # MB
        
        try:
            start_time = time.time()
            
            if system_type == "old":
                # Use appropriate method for old system
                if hasattr(rag_system, 'hybrid_query'):
                    result = rag_system.hybrid_query(query, top_k=5)
                else:
                    result = rag_system.query(query)
            else:  # new system
                result = rag_system.query(query, k=5)
            
            execution_time = time.time() - start_time
            
            memory_after = self.process.memory_info().rss / 1024 / 1024  # MB
            memory_peak = max(memory_before, memory_after)
            cpu_percent = self.process.cpu_percent()
            
            metrics = PerformanceMetrics(
                operation="query",
                system=system_type,
                execution_time=execution_time,
                memory_before=memory_before,
                memory_after=memory_after,
                memory_peak=memory_peak,
                cpu_percent=cpu_percent,
                success=True
            )
            
        except Exception as e:
            metrics = PerformanceMetrics(
                operation="query",
                system=system_type,
                execution_time=0.0,
                memory_before=memory_before,
                memory_after=memory_before,
                memory_peak=memory_before,
                cpu_percent=0.0,
                success=False,
                error_message=str(e)
            )
        
        return metrics
    
    def _benchmark_concurrency(self) -> List[ConcurrencyBenchmark]:
        """Benchmark concurrent query handling."""
        print("\n🚀 Benchmarking concurrency performance...")
        
        # Test document
        test_doc = project_root / "data" / "test" / "riscv-base-instructions.pdf"
        if not test_doc.exists():
            print("⚠️ Test document not found, skipping concurrency benchmarks")
            return []
        
        benchmarks = []
        thread_counts = [1, 2, 4, 8]
        queries_per_thread = 3
        
        for num_threads in thread_counts:
            if num_threads > psutil.cpu_count():
                continue
                
            print(f"  Testing {num_threads} threads...")
            
            # Test old system
            old_throughput, old_latency, old_error_rate = self._test_concurrency_system(
                test_doc, "old", num_threads, queries_per_thread
            )
            
            # Test new system
            new_throughput, new_latency, new_error_rate = self._test_concurrency_system(
                test_doc, "new", num_threads, queries_per_thread
            )
            
            benchmark = ConcurrencyBenchmark(
                num_threads=num_threads,
                queries_per_thread=queries_per_thread,
                old_system_throughput=old_throughput,
                new_system_throughput=new_throughput,
                old_system_avg_latency=old_latency,
                new_system_avg_latency=new_latency,
                old_system_error_rate=old_error_rate,
                new_system_error_rate=new_error_rate
            )
            
            benchmarks.append(benchmark)
            print(f"    Old: {old_throughput:.1f} q/s, New: {new_throughput:.1f} q/s")
        
        return benchmarks
    
    def _test_concurrency_system(self, test_doc: Path, system_type: str, num_threads: int, queries_per_thread: int) -> Tuple[float, float, float]:
        """Test concurrency for a specific system."""
        queries = self.test_queries[:queries_per_thread] * (num_threads // len(self.test_queries) + 1)
        queries = queries[:num_threads * queries_per_thread]
        
        def worker_function(queries_batch):
            """Worker function for concurrent testing."""
            try:
                if system_type == "old":
                    rag_system = BasicRAG()
                    rag_system.index_document(test_doc)
                else:
                    rag_system = RAGPipeline(self.config_path)
                    rag_system.index_document(test_doc)
                
                results = []
                for query in queries_batch:
                    start_time = time.time()
                    try:
                        if system_type == "old":
                            result = rag_system.hybrid_query(query, top_k=3)
                        else:
                            result = rag_system.query(query, k=3)
                        
                        latency = time.time() - start_time
                        results.append((True, latency))
                    except Exception as e:
                        latency = time.time() - start_time
                        results.append((False, latency))
                
                return results
                
            except Exception as e:
                # Return failed results for all queries
                return [(False, 0.0) for _ in queries_batch]
        
        # Split queries among threads
        queries_per_worker = max(1, len(queries) // num_threads)
        query_batches = [queries[i:i+queries_per_worker] for i in range(0, len(queries), queries_per_worker)]
        
        # Ensure we don't have empty batches
        query_batches = [batch for batch in query_batches if batch]
        
        # Run concurrent tests
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker_function, batch) for batch in query_batches]
            all_results = []
            for future in futures:
                all_results.extend(future.result())
        
        total_time = time.time() - start_time
        
        # Calculate metrics
        successful_queries = sum(1 for success, _ in all_results if success)
        total_queries = len(all_results)
        
        throughput = successful_queries / total_time if total_time > 0 else 0.0
        latencies = [latency for success, latency in all_results if success]
        avg_latency = statistics.mean(latencies) if latencies else 0.0
        error_rate = (total_queries - successful_queries) / total_queries if total_queries > 0 else 1.0
        
        return throughput, avg_latency, error_rate
    
    def _benchmark_scalability(self, test_documents: List[Path]) -> List[ScalabilityBenchmark]:
        """Benchmark scalability with different numbers of documents."""
        print("\n📈 Benchmarking scalability...")
        
        if not test_documents:
            print("⚠️ No test documents provided, skipping scalability benchmarks")
            return []
        
        benchmarks = []
        
        # Test with 1, 2, 3... documents (up to available)
        for doc_count in range(1, min(len(test_documents) + 1, 4)):
            print(f"  Testing with {doc_count} document(s)...")
            
            docs_to_test = test_documents[:doc_count]
            
            # Test old system
            old_results = self._test_scalability_system(docs_to_test, "old")
            
            # Test new system
            new_results = self._test_scalability_system(docs_to_test, "new")
            
            benchmark = ScalabilityBenchmark(
                document_count=doc_count,
                index_size_old=old_results["index_size"],
                index_size_new=new_results["index_size"],
                indexing_time_old=old_results["indexing_time"],
                indexing_time_new=new_results["indexing_time"],
                query_time_old=old_results["query_time"],
                query_time_new=new_results["query_time"],
                memory_usage_old=old_results["memory_usage"],
                memory_usage_new=new_results["memory_usage"]
            )
            
            benchmarks.append(benchmark)
        
        return benchmarks
    
    def _test_scalability_system(self, documents: List[Path], system_type: str) -> Dict[str, float]:
        """Test scalability for a specific system."""
        try:
            memory_before = self.process.memory_info().rss / 1024 / 1024  # MB
            
            # Initialize system
            if system_type == "old":
                rag_system = BasicRAG()
            else:
                rag_system = RAGPipeline(self.config_path)
            
            # Index documents
            start_time = time.time()
            total_chunks = 0
            
            for doc_path in documents:
                if doc_path.exists():
                    chunks = rag_system.index_document(doc_path)
                    total_chunks += chunks
            
            indexing_time = time.time() - start_time
            
            # Test query performance
            test_query = "What is RISC-V?"
            start_time = time.time()
            
            try:
                if system_type == "old":
                    result = rag_system.hybrid_query(test_query, top_k=5)
                else:
                    result = rag_system.query(test_query, k=5)
                query_time = time.time() - start_time
            except Exception:
                query_time = float('inf')
            
            memory_after = self.process.memory_info().rss / 1024 / 1024  # MB
            memory_usage = memory_after - memory_before
            
            return {
                "index_size": total_chunks,
                "indexing_time": indexing_time,
                "query_time": query_time,
                "memory_usage": memory_usage
            }
            
        except Exception as e:
            return {
                "index_size": 0,
                "indexing_time": float('inf'),
                "query_time": float('inf'),
                "memory_usage": float('inf')
            }
    
    def _calculate_summary_statistics(
        self,
        indexing_benchmarks: List[IndexingBenchmark],
        query_benchmarks: List[QueryBenchmark],
        concurrency_benchmarks: List[ConcurrencyBenchmark],
        scalability_benchmarks: List[ScalabilityBenchmark]
    ) -> Dict[str, float]:
        """Calculate summary statistics across all benchmarks."""
        stats = {}
        
        # Indexing statistics
        if indexing_benchmarks:
            speedups = [b.speedup_factor for b in indexing_benchmarks if b.speedup_factor != float('inf')]
            if speedups:
                stats["avg_indexing_speedup"] = statistics.mean(speedups)
                stats["max_indexing_speedup"] = max(speedups)
                stats["min_indexing_speedup"] = min(speedups)
            
            memory_effs = [b.memory_efficiency for b in indexing_benchmarks if b.memory_efficiency != float('inf')]
            if memory_effs:
                stats["avg_indexing_memory_efficiency"] = statistics.mean(memory_effs)
        
        # Query statistics
        if query_benchmarks:
            speedups = [b.speedup_factor for b in query_benchmarks if b.speedup_factor != float('inf')]
            if speedups:
                stats["avg_query_speedup"] = statistics.mean(speedups)
                stats["max_query_speedup"] = max(speedups)
                stats["min_query_speedup"] = min(speedups)
        
        # Concurrency statistics
        if concurrency_benchmarks:
            old_throughputs = [b.old_system_throughput for b in concurrency_benchmarks]
            new_throughputs = [b.new_system_throughput for b in concurrency_benchmarks]
            
            if old_throughputs and new_throughputs:
                stats["max_old_throughput"] = max(old_throughputs)
                stats["max_new_throughput"] = max(new_throughputs)
                stats["throughput_improvement"] = max(new_throughputs) / max(old_throughputs) if max(old_throughputs) > 0 else 1.0
        
        return stats
    
    def _generate_recommendations(self, stats: Dict[str, float]) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        
        # Indexing recommendations
        avg_indexing_speedup = stats.get("avg_indexing_speedup", 1.0)
        if avg_indexing_speedup > 1.2:
            recommendations.append("✅ Indexing performance improved - new system is faster")
        elif avg_indexing_speedup < 0.8:
            recommendations.append("⚠️ Indexing performance regression - consider optimization")
        
        # Query recommendations
        avg_query_speedup = stats.get("avg_query_speedup", 1.0)
        if avg_query_speedup > 1.2:
            recommendations.append("✅ Query performance improved - new system is faster")
        elif avg_query_speedup < 0.8:
            recommendations.append("⚠️ Query performance regression - review configuration")
        
        # Memory recommendations
        memory_eff = stats.get("avg_indexing_memory_efficiency", 1.0)
        if memory_eff > 1.2:
            recommendations.append("✅ Memory efficiency improved - new system uses less memory")
        elif memory_eff < 0.8:
            recommendations.append("⚠️ Higher memory usage - monitor in production")
        
        # Throughput recommendations
        throughput_improvement = stats.get("throughput_improvement", 1.0)
        if throughput_improvement > 1.2:
            recommendations.append("✅ Concurrent throughput improved - better scalability")
        elif throughput_improvement < 0.8:
            recommendations.append("⚠️ Concurrent performance degraded - check threading")
        
        return recommendations
    
    def _print_summary(self, report: BenchmarkReport):
        """Print benchmark summary."""
        print("\n" + "="*60)
        print("⚡ PERFORMANCE BENCHMARK SUMMARY")
        print("="*60)
        
        stats = report.summary_statistics
        
        print(f"Test Environment: {report.test_environment['cpu_count']} cores, {report.test_environment['memory_total_gb']}GB RAM")
        
        # Indexing results
        if report.indexing_benchmarks:
            print(f"\n📚 Indexing Performance:")
            print(f"  • Average speedup: {stats.get('avg_indexing_speedup', 1.0):.2f}x")
            print(f"  • Memory efficiency: {stats.get('avg_indexing_memory_efficiency', 1.0):.2f}x")
            print(f"  • Documents tested: {len(report.indexing_benchmarks)}")
        
        # Query results
        if report.query_benchmarks:
            print(f"\n🔍 Query Performance:")
            print(f"  • Average speedup: {stats.get('avg_query_speedup', 1.0):.2f}x")
            print(f"  • Range: {stats.get('min_query_speedup', 1.0):.2f}x - {stats.get('max_query_speedup', 1.0):.2f}x")
            print(f"  • Queries tested: {len(report.query_benchmarks)}")
        
        # Concurrency results
        if report.concurrency_benchmarks:
            print(f"\n🚀 Concurrency Performance:")
            print(f"  • Max throughput (old): {stats.get('max_old_throughput', 0):.1f} queries/sec")
            print(f"  • Max throughput (new): {stats.get('max_new_throughput', 0):.1f} queries/sec")
            print(f"  • Throughput improvement: {stats.get('throughput_improvement', 1.0):.2f}x")
        
        # Recommendations
        if report.recommendations:
            print(f"\n💡 Recommendations:")
            for rec in report.recommendations:
                print(f"  • {rec}")
        
        # Overall assessment
        avg_speedup = stats.get('avg_query_speedup', 1.0)
        throughput_improvement = stats.get('throughput_improvement', 1.0)
        
        if avg_speedup > 1.1 and throughput_improvement > 1.1:
            print(f"\n✅ OVERALL: Significant performance improvements detected")
        elif avg_speedup > 0.9 and throughput_improvement > 0.9:
            print(f"\n✅ OVERALL: Performance maintained or improved")
        else:
            print(f"\n⚠️ OVERALL: Performance regression detected - review optimization")

def main():
    """Main benchmarking workflow."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance Benchmark: BasicRAG vs RAGPipeline")
    parser.add_argument("--config", type=str, default="config/default.yaml", help="Configuration file for new system")
    parser.add_argument("--documents", type=str, nargs="+", help="Test documents (default: uses test document)")
    parser.add_argument("--save-report", type=str, help="Save detailed report to file")
    parser.add_argument("--quick", action="store_true", help="Run quick benchmark (fewer tests)")
    
    args = parser.parse_args()
    
    # Determine test documents
    if args.documents:
        test_docs = [Path(doc) for doc in args.documents]
    else:
        # Use default test document
        test_docs = [project_root / "data" / "test" / "riscv-base-instructions.pdf"]
    
    # Filter existing documents
    existing_docs = [doc for doc in test_docs if doc.exists()]
    if not existing_docs:
        print("❌ No valid test documents found")
        sys.exit(1)
    
    print(f"⚡ Performance Benchmarking: BasicRAG vs RAGPipeline")
    print(f"Configuration: {args.config}")
    print(f"Test documents: {[doc.name for doc in existing_docs]}")
    
    # Run benchmarks
    benchmarker = PerformanceBenchmarker(Path(args.config))
    report = benchmarker.run_comprehensive_benchmark(existing_docs)
    
    # Save detailed report if requested
    if args.save_report:
        with open(args.save_report, 'w') as f:
            json.dump(asdict(report), f, indent=2, default=str)
        print(f"\n💾 Detailed report saved to: {args.save_report}")

if __name__ == "__main__":
    main()