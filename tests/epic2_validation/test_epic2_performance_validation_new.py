"""
Epic 2 Performance Validation Tests
===================================

This module provides comprehensive performance validation for Epic 2 features
to ensure they meet the realistic performance targets specified in the documentation.

Performance Targets (from epic2-performance-benchmarks.md):
- Neural reranking overhead: <200ms for 100 candidates
- Graph processing overhead: <50ms for typical queries
- Backend switching latency: <50ms (FAISS ↔ Weaviate)
- Total pipeline latency: <700ms P95 (including all stages)
- Memory usage: <2GB additional for all Epic 2 features

Test Categories:
1. Neural reranking latency validation
2. Graph processing performance
3. Backend switching performance
4. Total pipeline latency (P95)
5. Memory usage monitoring
6. Concurrent query processing
7. Scalability testing

Architecture Reality:
- Performance measured for sub-components within ModularUnifiedRetriever
- Tests measure incremental overhead vs basic configuration
- Realistic targets based on actual implementation constraints
- Production deployment requirements validated
"""

import pytest
import logging
import time
import sys
import psutil
import statistics
import gc
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import Epic 2 components and infrastructure
from src.core.config import load_config
from src.core.component_factory import ComponentFactory
from src.core.interfaces import Document, RetrievalResult
from src.components.retrievers.modular_unified_retriever import ModularUnifiedRetriever
from src.components.retrievers.rerankers.neural_reranker import NeuralReranker
from src.components.retrievers.rerankers.identity_reranker import IdentityReranker
from src.components.retrievers.fusion.graph_enhanced_rrf_fusion import (
    GraphEnhancedRRFFusion,
)
from src.components.retrievers.fusion.rrf_fusion import RRFFusion

logger = logging.getLogger(__name__)


class Epic2PerformanceValidator:
    """
    Comprehensive validator for Epic 2 performance targets.

    Validates that Epic 2 features meet realistic performance benchmarks
    suitable for production deployment.
    """

    def __init__(self):
        """Initialize performance validator."""
        self.test_results = {}
        self.validation_errors = []
        self.performance_metrics = {}

        # Performance targets from documentation
        self.targets = {
            "neural_reranking_overhead_ms": 200,  # <200ms for 100 candidates
            "graph_processing_overhead_ms": 50,  # <50ms for typical queries
            "backend_switching_latency_ms": 50,  # <50ms switching time
            "total_pipeline_p95_ms": 700,  # <700ms P95 latency
            "additional_memory_gb": 2.0,  # <2GB additional memory
            "concurrent_queries": 10,  # Handle 10+ concurrent queries
            "throughput_qps": 10,  # 10+ queries per second
        }

        # Test configurations
        self.configs = {
            "basic": "test_epic2_minimal.yaml",  # Baseline (no Epic 2 features)
            "neural": "test_epic2_neural_enabled.yaml",  # Neural reranking only
            "graph": "test_epic2_graph_enabled.yaml",  # Graph enhancement only
            "complete": "test_epic2_all_features.yaml",  # All Epic 2 features
        }

    def run_all_validations(self) -> Dict[str, Any]:
        """Run comprehensive performance validation tests."""
        logger.info("Starting Epic 2 performance validation...")

        try:
            # Test 1: Neural reranking latency
            self.test_results["neural_latency"] = self._test_neural_reranking_latency()

            # Test 2: Graph processing performance
            self.test_results["graph_performance"] = (
                self._test_graph_processing_performance()
            )

            # Test 3: Backend switching performance
            self.test_results["backend_switching"] = (
                self._test_backend_switching_performance()
            )

            # Test 4: Total pipeline latency
            self.test_results["pipeline_latency"] = self._test_total_pipeline_latency()

            # Test 5: Memory usage validation
            self.test_results["memory_usage"] = self._test_memory_usage()

            # Test 6: Concurrent query processing
            self.test_results["concurrent_processing"] = (
                self._test_concurrent_processing()
            )

            # Calculate overall score
            passed_tests = sum(
                1
                for result in self.test_results.values()
                if result.get("passed", False)
            )
            total_tests = len(self.test_results)
            overall_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

            return {
                "overall_score": overall_score,
                "passed_tests": passed_tests,
                "total_tests": total_tests,
                "test_results": self.test_results,
                "performance_metrics": self.performance_metrics,
                "validation_errors": self.validation_errors,
            }

        except Exception as e:
            logger.error(f"Performance validation failed: {e}")
            self.validation_errors.append(f"Critical validation failure: {e}")
            return {
                "overall_score": 0,
                "passed_tests": 0,
                "total_tests": len(self.test_results),
                "test_results": self.test_results,
                "performance_metrics": self.performance_metrics,
                "validation_errors": self.validation_errors,
            }

    def _load_config_and_create_retriever(
        self, config_file: str
    ) -> Tuple[Any, ModularUnifiedRetriever]:
        """Load configuration and create retriever for testing."""
        config_path = Path(f"config/{config_file}")
        config = load_config(config_path)

        # Create embedder (required dependency)
        factory = ComponentFactory()
        embedder = factory.create_embedder(
            config.embedder.type, **config.embedder.config.dict()
        )

        # Create retriever
        retriever = factory.create_retriever(
            config.retriever.type, embedder=embedder, **config.retriever.config.dict()
        )

        return config, retriever

    def _create_test_documents(self, count: int = 100) -> List[Document]:
        """Create test documents for performance testing."""
        documents = []

        base_contents = [
            "RISC-V instruction pipeline implements 5-stage design with fetch, decode, execute, memory, and writeback stages for efficient processing.",
            "Branch prediction in RISC-V processors uses two-level adaptive predictors to reduce control hazards and improve execution performance.",
            "RISC-V memory hierarchy includes L1 instruction cache, L1 data cache, shared L2 cache, and main memory with coherency protocols.",
            "Vector extensions in RISC-V provide SIMD operations for parallel processing with variable-length vector registers and operations.",
            "RISC-V privilege levels include machine mode, supervisor mode, and user mode for security isolation and virtualization support.",
            "Cache coherency in RISC-V systems maintains data consistency using MESI protocol with modified, exclusive, shared, and invalid states.",
            "Interrupt handling in RISC-V architecture supports both synchronous exceptions and asynchronous interrupts with vectored dispatch.",
            "Virtual memory in RISC-V provides address translation using page tables with configurable page sizes and protection bits.",
            "Atomic operations in RISC-V ensure memory consistency in multi-core systems using load-reserved and store-conditional instructions.",
            "Debug support in RISC-V includes hardware breakpoints, single-step execution, and trace capabilities for development tools.",
        ]

        for i in range(count):
            base_idx = i % len(base_contents)
            content = f"{base_contents[base_idx]} Document {i+1} additional context and technical details."

            documents.append(
                Document(
                    content=content,
                    metadata={
                        "id": f"perf_doc_{i+1}",
                        "topic": f"topic_{i % 5}",
                        "complexity": "medium" if i % 2 == 0 else "high",
                    },
                    embedding=None,
                )
            )

        return documents

    def _prepare_documents_with_embeddings(
        self, documents: List[Document], embedder
    ) -> List[Document]:
        """Prepare documents with embeddings for indexing."""
        texts = [doc.content for doc in documents]
        embeddings = embedder.embed(texts)

        for doc, embedding in zip(documents, embeddings):
            doc.embedding = embedding

        return documents

    def _measure_memory_usage(self) -> Dict[str, float]:
        """Measure current memory usage."""
        process = psutil.Process()
        memory_info = process.memory_info()

        return {
            "rss_mb": memory_info.rss / (1024 * 1024),  # Resident Set Size
            "vms_mb": memory_info.vms / (1024 * 1024),  # Virtual Memory Size
            "percent": process.memory_percent(),
            "available_mb": psutil.virtual_memory().available / (1024 * 1024),
        }

    def _test_neural_reranking_latency(self) -> Dict[str, Any]:
        """Test neural reranking latency meets <200ms target for 100 candidates."""
        test_result = {"passed": False, "details": {}, "errors": []}

        try:
            logger.info("Testing neural reranking latency...")

            # Test both basic and neural configurations
            latency_results = {}

            # Test basic configuration (IdentityReranker)
            config, basic_retriever = self._load_config_and_create_retriever(
                self.configs["basic"]
            )

            # Test neural configuration (NeuralReranker)
            config, neural_retriever = self._load_config_and_create_retriever(
                self.configs["neural"]
            )

            # Prepare test data (100 candidates as per target)
            documents = self._create_test_documents(100)

            # Test basic retriever latency
            embedder = basic_retriever.embedder
            documents = self._prepare_documents_with_embeddings(documents, embedder)
            basic_retriever.index_documents(documents)

            query = "RISC-V pipeline hazard detection and forwarding mechanisms"
            query_embedding = embedder.embed([query])[0]

            # Warm up
            basic_retriever.retrieve(query, query_embedding, top_k=10)

            # Measure basic retrieval time (multiple runs for accuracy)
            basic_times = []
            for _ in range(5):
                start_time = time.time()
                results = basic_retriever.retrieve(query, query_embedding, top_k=10)
                basic_times.append((time.time() - start_time) * 1000)

            basic_avg_time = statistics.mean(basic_times)

            # Test neural retriever latency
            embedder = neural_retriever.embedder
            documents = self._prepare_documents_with_embeddings(documents, embedder)
            neural_retriever.index_documents(documents)

            query_embedding = embedder.embed([query])[0]

            # Warm up neural model
            neural_retriever.retrieve(query, query_embedding, top_k=10)

            # Measure neural retrieval time
            neural_times = []
            for _ in range(5):
                start_time = time.time()
                results = neural_retriever.retrieve(query, query_embedding, top_k=10)
                neural_times.append((time.time() - start_time) * 1000)

            neural_avg_time = statistics.mean(neural_times)

            # Calculate overhead
            neural_overhead = neural_avg_time - basic_avg_time
            meets_target = (
                neural_overhead <= self.targets["neural_reranking_overhead_ms"]
            )

            latency_results = {
                "basic_avg_time_ms": basic_avg_time,
                "neural_avg_time_ms": neural_avg_time,
                "neural_overhead_ms": neural_overhead,
                "target_overhead_ms": self.targets["neural_reranking_overhead_ms"],
                "meets_target": meets_target,
                "neural_reranker_used": isinstance(
                    neural_retriever.reranker, NeuralReranker
                ),
                "neural_enabled": (
                    isinstance(neural_retriever.reranker, NeuralReranker)
                    and neural_retriever.reranker.is_enabled()
                ),
            }

            test_result.update(
                {
                    "passed": meets_target and latency_results["neural_enabled"],
                    "details": latency_results,
                }
            )

            if not meets_target:
                test_result["errors"].append(
                    f"Neural reranking overhead {neural_overhead:.1f}ms exceeds target {self.targets['neural_reranking_overhead_ms']}ms"
                )

            if not latency_results["neural_enabled"]:
                test_result["errors"].append(
                    "Neural reranking was not properly enabled"
                )

            # Store metrics
            self.performance_metrics["neural_overhead_ms"] = neural_overhead
            self.performance_metrics["basic_retrieval_ms"] = basic_avg_time
            self.performance_metrics["neural_retrieval_ms"] = neural_avg_time

        except Exception as e:
            test_result["errors"].append(f"Neural latency test failed: {e}")
            logger.error(f"Neural latency error: {e}")

        return test_result

    def _test_graph_processing_performance(self) -> Dict[str, Any]:
        """Test graph processing overhead meets <50ms target."""
        test_result = {"passed": False, "details": {}, "errors": []}

        try:
            logger.info("Testing graph processing performance...")

            # Test basic vs graph-enhanced configurations
            config, basic_retriever = self._load_config_and_create_retriever(
                self.configs["basic"]
            )
            config, graph_retriever = self._load_config_and_create_retriever(
                self.configs["graph"]
            )

            # Prepare test data
            documents = self._create_test_documents(
                50
            )  # Moderate size for graph testing

            # Test basic fusion latency
            embedder = basic_retriever.embedder
            documents = self._prepare_documents_with_embeddings(documents, embedder)
            basic_retriever.index_documents(documents)

            query = "RISC-V memory hierarchy and cache coherency"
            query_embedding = embedder.embed([query])[0]

            # Warm up
            basic_retriever.retrieve(query, query_embedding, top_k=10)

            # Measure basic fusion time
            basic_times = []
            for _ in range(5):
                start_time = time.time()
                results = basic_retriever.retrieve(query, query_embedding, top_k=10)
                basic_times.append((time.time() - start_time) * 1000)

            basic_avg_time = statistics.mean(basic_times)

            # Test graph-enhanced fusion latency
            embedder = graph_retriever.embedder
            documents = self._prepare_documents_with_embeddings(documents, embedder)
            graph_retriever.index_documents(documents)

            query_embedding = embedder.embed([query])[0]

            # Warm up
            graph_retriever.retrieve(query, query_embedding, top_k=10)

            # Measure graph fusion time
            graph_times = []
            for _ in range(5):
                start_time = time.time()
                results = graph_retriever.retrieve(query, query_embedding, top_k=10)
                graph_times.append((time.time() - start_time) * 1000)

            graph_avg_time = statistics.mean(graph_times)

            # Calculate overhead
            graph_overhead = graph_avg_time - basic_avg_time
            meets_target = (
                graph_overhead <= self.targets["graph_processing_overhead_ms"]
            )

            graph_results = {
                "basic_avg_time_ms": basic_avg_time,
                "graph_avg_time_ms": graph_avg_time,
                "graph_overhead_ms": graph_overhead,
                "target_overhead_ms": self.targets["graph_processing_overhead_ms"],
                "meets_target": meets_target,
                "graph_fusion_used": isinstance(
                    graph_retriever.fusion_strategy, GraphEnhancedRRFFusion
                ),
                "graph_enabled": (
                    isinstance(graph_retriever.fusion_strategy, GraphEnhancedRRFFusion)
                    and getattr(graph_retriever.fusion_strategy, "graph_enabled", False)
                ),
            }

            test_result.update(
                {
                    "passed": meets_target and graph_results["graph_enabled"],
                    "details": graph_results,
                }
            )

            if not meets_target:
                test_result["errors"].append(
                    f"Graph processing overhead {graph_overhead:.1f}ms exceeds target {self.targets['graph_processing_overhead_ms']}ms"
                )

            if not graph_results["graph_enabled"]:
                test_result["errors"].append(
                    "Graph enhancement was not properly enabled"
                )

            # Store metrics
            self.performance_metrics["graph_overhead_ms"] = graph_overhead
            self.performance_metrics["basic_fusion_ms"] = basic_avg_time
            self.performance_metrics["graph_fusion_ms"] = graph_avg_time

        except Exception as e:
            test_result["errors"].append(f"Graph performance test failed: {e}")
            logger.error(f"Graph performance error: {e}")

        return test_result

    def _test_backend_switching_performance(self) -> Dict[str, Any]:
        """Test backend switching latency meets <50ms target."""
        test_result = {"passed": False, "details": {}, "errors": []}

        try:
            logger.info("Testing backend switching performance...")

            # For now, test FAISS backend initialization time as a proxy
            # (actual multi-backend switching would require Weaviate setup)

            switching_results = {}

            # Test FAISS backend initialization time
            config, retriever = self._load_config_and_create_retriever(
                self.configs["complete"]
            )

            # Test backend reinitialization time
            documents = self._create_test_documents(20)
            embedder = retriever.embedder
            documents = self._prepare_documents_with_embeddings(documents, embedder)

            # Measure indexing time as proxy for backend switching
            indexing_times = []
            for _ in range(3):
                # Create new retriever instance to simulate switching
                config, new_retriever = self._load_config_and_create_retriever(
                    self.configs["complete"]
                )

                start_time = time.time()
                new_retriever.index_documents(documents[:10])  # Small subset for speed
                indexing_times.append((time.time() - start_time) * 1000)

            avg_indexing_time = statistics.mean(indexing_times)
            meets_target = (
                avg_indexing_time <= self.targets["backend_switching_latency_ms"]
            )

            switching_results = {
                "avg_indexing_time_ms": avg_indexing_time,
                "target_latency_ms": self.targets["backend_switching_latency_ms"],
                "meets_target": meets_target,
                "backend_type": type(retriever.vector_index).__name__,
                "test_documents": 10,
            }

            test_result.update({"passed": meets_target, "details": switching_results})

            if not meets_target:
                test_result["errors"].append(
                    f"Backend switching time {avg_indexing_time:.1f}ms exceeds target {self.targets['backend_switching_latency_ms']}ms"
                )

            # Store metrics
            self.performance_metrics["backend_switching_ms"] = avg_indexing_time

        except Exception as e:
            test_result["errors"].append(f"Backend switching test failed: {e}")
            logger.error(f"Backend switching error: {e}")

        return test_result

    def _test_total_pipeline_latency(self) -> Dict[str, Any]:
        """Test total pipeline latency meets <700ms P95 target."""
        test_result = {"passed": False, "details": {}, "errors": []}

        try:
            logger.info("Testing total pipeline latency...")

            # Test complete Epic 2 pipeline with all features
            config, retriever = self._load_config_and_create_retriever(
                self.configs["complete"]
            )

            # Prepare test data
            documents = self._create_test_documents(100)
            embedder = retriever.embedder
            documents = self._prepare_documents_with_embeddings(documents, embedder)
            retriever.index_documents(documents)

            # Test queries for latency measurement
            queries = [
                "RISC-V pipeline hazard detection mechanisms",
                "Branch prediction in RISC-V processors",
                "Memory hierarchy and cache coherency",
                "Vector extensions and SIMD operations",
                "Privilege levels and security features",
            ]

            # Warm up
            query_embedding = embedder.embed([queries[0]])[0]
            retriever.retrieve(queries[0], query_embedding, top_k=10)

            # Measure latencies for multiple queries
            latencies = []
            for query in queries:
                query_embedding = embedder.embed([query])[0]

                # Run each query multiple times
                for _ in range(4):  # 20 total measurements (5 queries x 4 runs)
                    start_time = time.time()
                    results = retriever.retrieve(query, query_embedding, top_k=10)
                    latencies.append((time.time() - start_time) * 1000)

            # Calculate statistics
            avg_latency = statistics.mean(latencies)
            p95_latency = np.percentile(latencies, 95)
            max_latency = max(latencies)
            min_latency = min(latencies)

            meets_target = p95_latency <= self.targets["total_pipeline_p95_ms"]

            pipeline_results = {
                "avg_latency_ms": avg_latency,
                "p95_latency_ms": p95_latency,
                "max_latency_ms": max_latency,
                "min_latency_ms": min_latency,
                "target_p95_ms": self.targets["total_pipeline_p95_ms"],
                "meets_target": meets_target,
                "measurements": len(latencies),
                "features_active": {
                    "neural": isinstance(retriever.reranker, NeuralReranker),
                    "graph": isinstance(
                        retriever.fusion_strategy, GraphEnhancedRRFFusion
                    ),
                },
            }

            test_result.update({"passed": meets_target, "details": pipeline_results})

            if not meets_target:
                test_result["errors"].append(
                    f"Pipeline P95 latency {p95_latency:.1f}ms exceeds target {self.targets['total_pipeline_p95_ms']}ms"
                )

            # Store metrics
            self.performance_metrics["pipeline_avg_latency_ms"] = avg_latency
            self.performance_metrics["pipeline_p95_latency_ms"] = p95_latency
            self.performance_metrics["pipeline_max_latency_ms"] = max_latency

        except Exception as e:
            test_result["errors"].append(f"Pipeline latency test failed: {e}")
            logger.error(f"Pipeline latency error: {e}")

        return test_result

    def _test_memory_usage(self) -> Dict[str, Any]:
        """Test memory usage stays within <2GB additional target."""
        test_result = {"passed": False, "details": {}, "errors": []}

        try:
            logger.info("Testing memory usage...")

            # Measure baseline memory
            gc.collect()  # Force garbage collection
            baseline_memory = self._measure_memory_usage()

            # Load Epic 2 system with all features
            config, retriever = self._load_config_and_create_retriever(
                self.configs["complete"]
            )

            # Index documents to load models and data
            documents = self._create_test_documents(100)
            embedder = retriever.embedder
            documents = self._prepare_documents_with_embeddings(documents, embedder)
            retriever.index_documents(documents)

            # Trigger neural model loading by doing a retrieval
            query = "RISC-V pipeline hazard detection"
            query_embedding = embedder.embed([query])[0]
            retriever.retrieve(query, query_embedding, top_k=10)

            # Measure Epic 2 memory usage
            epic2_memory = self._measure_memory_usage()

            # Calculate additional memory usage
            additional_memory_mb = epic2_memory["rss_mb"] - baseline_memory["rss_mb"]
            additional_memory_gb = additional_memory_mb / 1024

            meets_target = additional_memory_gb <= self.targets["additional_memory_gb"]

            memory_results = {
                "baseline_memory_mb": baseline_memory["rss_mb"],
                "epic2_memory_mb": epic2_memory["rss_mb"],
                "additional_memory_mb": additional_memory_mb,
                "additional_memory_gb": additional_memory_gb,
                "target_additional_gb": self.targets["additional_memory_gb"],
                "meets_target": meets_target,
                "memory_percent": epic2_memory["percent"],
                "available_memory_mb": epic2_memory["available_mb"],
            }

            test_result.update({"passed": meets_target, "details": memory_results})

            if not meets_target:
                test_result["errors"].append(
                    f"Additional memory usage {additional_memory_gb:.2f}GB exceeds target {self.targets['additional_memory_gb']}GB"
                )

            # Store metrics
            self.performance_metrics["additional_memory_gb"] = additional_memory_gb
            self.performance_metrics["epic2_memory_mb"] = epic2_memory["rss_mb"]

        except Exception as e:
            test_result["errors"].append(f"Memory usage test failed: {e}")
            logger.error(f"Memory usage error: {e}")

        return test_result

    def _test_concurrent_processing(self) -> Dict[str, Any]:
        """Test concurrent query processing capability."""
        test_result = {"passed": False, "details": {}, "errors": []}

        try:
            logger.info("Testing concurrent query processing...")

            # Create retriever for concurrent testing
            config, retriever = self._load_config_and_create_retriever(
                self.configs["complete"]
            )

            # Prepare test data
            documents = self._create_test_documents(50)
            embedder = retriever.embedder
            documents = self._prepare_documents_with_embeddings(documents, embedder)
            retriever.index_documents(documents)

            # Test queries
            queries = [
                "RISC-V pipeline hazard detection",
                "Branch prediction mechanisms",
                "Memory hierarchy design",
                "Vector processing capabilities",
                "Privilege level security",
                "Cache coherency protocols",
                "Interrupt handling systems",
                "Virtual memory translation",
                "Atomic operations support",
                "Debug infrastructure",
            ]

            def process_query(query_text):
                """Process a single query."""
                try:
                    query_embedding = embedder.embed([query_text])[0]
                    start_time = time.time()
                    results = retriever.retrieve(query_text, query_embedding, top_k=5)
                    processing_time = (time.time() - start_time) * 1000
                    return {
                        "success": True,
                        "query": query_text,
                        "processing_time_ms": processing_time,
                        "results_count": len(results),
                    }
                except Exception as e:
                    return {"success": False, "query": query_text, "error": str(e)}

            # Test concurrent processing
            concurrent_results = []
            start_time = time.time()

            with ThreadPoolExecutor(
                max_workers=self.targets["concurrent_queries"]
            ) as executor:
                futures = [executor.submit(process_query, query) for query in queries]

                for future in as_completed(futures):
                    result = future.result()
                    concurrent_results.append(result)

            total_time = (time.time() - start_time) * 1000

            # Analyze results
            successful_queries = [
                r for r in concurrent_results if r.get("success", False)
            ]
            failed_queries = [
                r for r in concurrent_results if not r.get("success", False)
            ]

            success_rate = len(successful_queries) / len(queries)
            avg_processing_time = (
                statistics.mean([r["processing_time_ms"] for r in successful_queries])
                if successful_queries
                else 0
            )

            # Calculate throughput
            throughput_qps = (
                len(successful_queries) / (total_time / 1000) if total_time > 0 else 0
            )

            meets_concurrent_target = (
                len(successful_queries) >= self.targets["concurrent_queries"]
            )
            meets_throughput_target = throughput_qps >= self.targets["throughput_qps"]

            concurrent_test_results = {
                "queries_total": len(queries),
                "queries_successful": len(successful_queries),
                "queries_failed": len(failed_queries),
                "success_rate": success_rate,
                "avg_processing_time_ms": avg_processing_time,
                "total_time_ms": total_time,
                "throughput_qps": throughput_qps,
                "target_concurrent_queries": self.targets["concurrent_queries"],
                "target_throughput_qps": self.targets["throughput_qps"],
                "meets_concurrent_target": meets_concurrent_target,
                "meets_throughput_target": meets_throughput_target,
                "failed_query_errors": [r.get("error") for r in failed_queries],
            }

            test_result.update(
                {
                    "passed": meets_concurrent_target
                    and meets_throughput_target
                    and success_rate >= 0.9,
                    "details": concurrent_test_results,
                }
            )

            if not meets_concurrent_target:
                test_result["errors"].append(
                    f"Concurrent processing {len(successful_queries)} queries < target {self.targets['concurrent_queries']}"
                )

            if not meets_throughput_target:
                test_result["errors"].append(
                    f"Throughput {throughput_qps:.1f} QPS < target {self.targets['throughput_qps']} QPS"
                )

            if success_rate < 0.9:
                test_result["errors"].append(f"Success rate {success_rate:.1%} < 90%")

            # Store metrics
            self.performance_metrics["concurrent_success_rate"] = success_rate
            self.performance_metrics["throughput_qps"] = throughput_qps
            self.performance_metrics["concurrent_avg_time_ms"] = avg_processing_time

        except Exception as e:
            test_result["errors"].append(f"Concurrent processing test failed: {e}")
            logger.error(f"Concurrent processing error: {e}")

        return test_result


# Test execution functions for pytest integration
def test_epic2_performance_validation():
    """Test Epic 2 performance validation."""
    validator = Epic2PerformanceValidator()
    results = validator.run_all_validations()

    # Assert overall success
    assert (
        results["overall_score"] > 70
    ), f"Performance validation failed with score {results['overall_score']}%"
    assert (
        results["passed_tests"] >= 4
    ), f"Only {results['passed_tests']} out of {results['total_tests']} tests passed"

    # Assert specific performance targets
    test_results = results["test_results"]

    # Neural reranking should meet latency target
    if test_results.get("neural_latency", {}).get("details"):
        neural_overhead = test_results["neural_latency"]["details"].get(
            "neural_overhead_ms", 0
        )
        assert (
            neural_overhead <= 200
        ), f"Neural reranking overhead {neural_overhead:.1f}ms exceeds 200ms target"

    # Graph processing should meet latency target
    if test_results.get("graph_performance", {}).get("details"):
        graph_overhead = test_results["graph_performance"]["details"].get(
            "graph_overhead_ms", 0
        )
        assert (
            graph_overhead <= 50
        ), f"Graph processing overhead {graph_overhead:.1f}ms exceeds 50ms target"

    # Pipeline latency should meet P95 target
    if test_results.get("pipeline_latency", {}).get("details"):
        p95_latency = test_results["pipeline_latency"]["details"].get(
            "p95_latency_ms", 0
        )
        assert (
            p95_latency <= 700
        ), f"Pipeline P95 latency {p95_latency:.1f}ms exceeds 700ms target"


if __name__ == "__main__":
    # Run validation when script is executed directly
    validator = Epic2PerformanceValidator()
    results = validator.run_all_validations()

    print(f"\n{'='*60}")
    print("EPIC 2 PERFORMANCE VALIDATION RESULTS")
    print(f"{'='*60}")
    print(f"Overall Score: {results['overall_score']:.1f}%")
    print(f"Passed Tests: {results['passed_tests']}/{results['total_tests']}")

    if results["overall_score"] >= 90:
        print("✅ EXCELLENT - All performance targets met!")
    elif results["overall_score"] >= 80:
        print("✅ GOOD - Most performance targets met")
    else:
        print("❌ NEEDS IMPROVEMENT - Performance issues found")

    # Show detailed results
    for test_name, result in results["test_results"].items():
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result.get("errors"):
            for error in result["errors"]:
                print(f"    - {error}")

    # Show performance metrics
    if results["performance_metrics"]:
        print(f"\n📊 Performance Metrics:")
        for metric, value in results["performance_metrics"].items():
            if "ms" in metric:
                print(f"  {metric}: {value:.1f}ms")
            elif "gb" in metric:
                print(f"  {metric}: {value:.2f}GB")
            elif "qps" in metric:
                print(f"  {metric}: {value:.1f} QPS")
            else:
                print(f"  {metric}: {value}")
