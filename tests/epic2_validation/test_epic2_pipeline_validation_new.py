"""
Epic 2 End-to-End Pipeline Validation Tests
==========================================

This module provides comprehensive validation for the complete Epic 2 4-stage
retrieval pipeline, testing the integration of all features in a production-like
environment with configuration-driven feature switching and concurrent processing.

Pipeline Stages Tested:
1. Dense Retrieval (Vector similarity search)
2. Sparse Retrieval (BM25 keyword search)
3. Graph Enhancement (Document relationship analysis)
4. Neural Reranking (Cross-encoder optimization)

Test Categories:
1. Complete 4-stage pipeline execution
2. Configuration-driven feature switching
3. Concurrent query processing with Epic 2 features
4. Error handling and graceful degradation
5. Pipeline performance under load
6. Feature combination validation

Architecture Reality:
- Tests complete ModularUnifiedRetriever pipeline with all sub-components
- Validates configuration-driven feature activation in production scenarios
- Tests pipeline robustness under various conditions
- Ensures graceful degradation when individual components fail

Performance Validation:
- Complete pipeline latency <700ms P95
- Concurrent processing capability (10+ queries)
- Memory efficiency under load
- Error recovery and resilience
"""

import pytest
import logging
import time
import sys
import asyncio
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
import numpy as np
import statistics
import queue

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


class Epic2PipelineValidator:
    """
    Comprehensive validator for Epic 2 end-to-end pipeline.

    Tests complete 4-stage pipeline execution with all Epic 2 features
    integrated and validates production-ready performance.
    """

    def __init__(self):
        """Initialize pipeline validator."""
        self.test_results = {}
        self.validation_errors = []
        self.pipeline_metrics = {}

        # Pipeline performance targets
        self.targets = {
            "pipeline_latency_p95_ms": 700,  # <700ms P95 total pipeline
            "concurrent_queries": 10,  # Handle 10+ concurrent queries
            "success_rate_percent": 95.0,  # >95% query success rate
            "error_recovery_time_ms": 100,  # <100ms error recovery
            "memory_efficiency_mb": 2048,  # <2GB memory usage
            "throughput_qps": 5.0,  # >5 queries per second sustained
        }

        # Test configurations for pipeline testing
        self.configs = {
            "minimal": "test_epic2_minimal.yaml",  # Basic pipeline
            "neural": "test_epic2_neural_enabled.yaml",  # Neural reranking enabled
            "graph": "test_epic2_graph_enabled.yaml",  # Graph enhancement enabled
            "complete": "test_epic2_all_features.yaml",  # Complete Epic 2 pipeline
        }

    def run_all_validations(self) -> Dict[str, Any]:
        """Run comprehensive pipeline validation tests."""
        logger.info("Starting Epic 2 pipeline validation...")

        try:
            # Test 1: Complete 4-stage pipeline execution
            self.test_results["pipeline_execution"] = self._test_pipeline_execution()

            # Test 2: Configuration-driven feature switching
            self.test_results["feature_switching"] = self._test_feature_switching()

            # Test 3: Concurrent query processing
            self.test_results["concurrent_processing"] = (
                self._test_concurrent_processing()
            )

            # Test 4: Error handling and graceful degradation
            self.test_results["error_handling"] = self._test_error_handling()

            # Test 5: Pipeline performance under load
            self.test_results["load_performance"] = self._test_load_performance()

            # Test 6: Feature combination validation
            self.test_results["feature_combinations"] = (
                self._test_feature_combinations()
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
                "pipeline_metrics": self.pipeline_metrics,
                "validation_errors": self.validation_errors,
            }

        except Exception as e:
            logger.error(f"Pipeline validation failed: {e}")
            self.validation_errors.append(f"Critical validation failure: {e}")
            return {
                "overall_score": 0,
                "passed_tests": 0,
                "total_tests": len(self.test_results),
                "test_results": self.test_results,
                "pipeline_metrics": self.pipeline_metrics,
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

    def _create_comprehensive_test_documents(self) -> List[Document]:
        """Create comprehensive test documents for pipeline testing."""
        documents = [
            # RISC-V Pipeline Architecture
            Document(
                content="RISC-V instruction pipeline implements a sophisticated 5-stage design with fetch, decode, execute, memory access, and writeback stages. The pipeline includes comprehensive hazard detection units that monitor data dependencies between instructions and implement forwarding mechanisms to resolve conflicts without stalling.",
                metadata={
                    "id": "pipeline_comprehensive",
                    "category": "architecture",
                    "complexity": "high",
                },
                embedding=None,
            ),
            Document(
                content="Hazard detection in RISC-V processors involves analyzing instruction dependencies and implementing forwarding paths. The forwarding unit can bypass data from the execute stage or memory stage directly to subsequent instructions that need the same registers.",
                metadata={
                    "id": "hazard_detection",
                    "category": "pipeline",
                    "complexity": "medium",
                },
                embedding=None,
            ),
            # Branch Prediction and Control Flow
            Document(
                content="Branch prediction mechanisms in RISC-V include two-level adaptive predictors with global and local history components. The branch target buffer maintains recently used branch addresses, while the return address stack optimizes function call/return patterns.",
                metadata={
                    "id": "branch_prediction",
                    "category": "control_flow",
                    "complexity": "high",
                },
                embedding=None,
            ),
            Document(
                content="Control hazards occur when branch instructions alter the normal sequential flow of instruction execution. RISC-V processors implement various techniques including branch delay slots, static prediction, and dynamic prediction to minimize performance impact.",
                metadata={
                    "id": "control_hazards",
                    "category": "hazards",
                    "complexity": "medium",
                },
                embedding=None,
            ),
            # Memory Hierarchy and Caching
            Document(
                content="RISC-V memory hierarchy design includes separate L1 instruction and data caches, a unified L2 cache, and main memory. Cache coherency protocols ensure data consistency across multiple cores using modified, exclusive, shared, and invalid (MESI) states.",
                metadata={
                    "id": "memory_hierarchy",
                    "category": "memory",
                    "complexity": "high",
                },
                embedding=None,
            ),
            Document(
                content="Cache coherency in multicore RISC-V systems maintains data consistency through snooping protocols. When one core modifies cached data, other cores with copies of that data are notified and must invalidate or update their copies accordingly.",
                metadata={
                    "id": "cache_coherency",
                    "category": "memory",
                    "complexity": "high",
                },
                embedding=None,
            ),
            # Vector Processing and SIMD
            Document(
                content="Vector extensions in RISC-V provide Single Instruction Multiple Data (SIMD) capabilities through variable-length vector registers. The vector architecture supports configurable vector lengths and multiple data types for efficient parallel processing.",
                metadata={
                    "id": "vector_extensions",
                    "category": "simd",
                    "complexity": "medium",
                },
                embedding=None,
            ),
            Document(
                content="RISC-V vector processing includes support for vector arithmetic, logical operations, memory operations, and reduction operations. Vector mask registers enable predicated execution for conditional vector operations.",
                metadata={
                    "id": "vector_processing",
                    "category": "simd",
                    "complexity": "medium",
                },
                embedding=None,
            ),
            # Security and Privilege Architecture
            Document(
                content="RISC-V privilege architecture defines three privilege levels: machine mode (M-mode), supervisor mode (S-mode), and user mode (U-mode). Each mode has specific access rights to system resources and instruction execution capabilities.",
                metadata={
                    "id": "privilege_levels",
                    "category": "security",
                    "complexity": "medium",
                },
                embedding=None,
            ),
            Document(
                content="Virtual memory in RISC-V provides address translation through page tables with configurable page sizes. The Translation Lookaside Buffer (TLB) caches recent address translations to improve memory access performance.",
                metadata={
                    "id": "virtual_memory",
                    "category": "memory",
                    "complexity": "high",
                },
                embedding=None,
            ),
            # Additional documents for comprehensive testing
            Document(
                content="Interrupt handling in RISC-V supports both synchronous exceptions and asynchronous interrupts. The processor maintains control and status registers (CSRs) for interrupt configuration and uses vectored interrupt dispatch for efficient handling.",
                metadata={
                    "id": "interrupt_handling",
                    "category": "system",
                    "complexity": "medium",
                },
                embedding=None,
            ),
            Document(
                content="Atomic operations in RISC-V ensure memory consistency in multiprocessor systems. Load-reserved and store-conditional instructions provide the foundation for implementing higher-level synchronization primitives.",
                metadata={
                    "id": "atomic_operations",
                    "category": "concurrency",
                    "complexity": "medium",
                },
                embedding=None,
            ),
            Document(
                content="Debug support in RISC-V includes hardware breakpoints, single-step execution capabilities, and program trace generation. The debug module provides external debug access through JTAG or other debug transport interfaces.",
                metadata={
                    "id": "debug_support",
                    "category": "debug",
                    "complexity": "low",
                },
                embedding=None,
            ),
            Document(
                content="Performance monitoring in RISC-V processors uses hardware performance counters to track events like cache misses, branch mispredictions, and instruction counts. These counters support performance analysis and optimization.",
                metadata={
                    "id": "performance_monitoring",
                    "category": "analysis",
                    "complexity": "low",
                },
                embedding=None,
            ),
            Document(
                content="Instruction encoding in RISC-V uses a variable-length format with 16-bit, 32-bit, and longer instruction formats. The base 32-bit instructions provide the core functionality while compressed 16-bit instructions improve code density.",
                metadata={
                    "id": "instruction_encoding",
                    "category": "instruction_set",
                    "complexity": "low",
                },
                embedding=None,
            ),
        ]

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

    def _create_test_queries(self) -> List[Dict[str, Any]]:
        """Create test queries for pipeline validation."""
        return [
            {
                "query": "RISC-V pipeline hazard detection and forwarding mechanisms",
                "expected_categories": ["architecture", "pipeline"],
                "complexity": "high",
            },
            {
                "query": "Branch prediction techniques in RISC-V processors",
                "expected_categories": ["control_flow"],
                "complexity": "medium",
            },
            {
                "query": "Memory hierarchy and cache coherency protocols",
                "expected_categories": ["memory"],
                "complexity": "high",
            },
            {
                "query": "Vector processing and SIMD operations",
                "expected_categories": ["simd"],
                "complexity": "medium",
            },
            {
                "query": "RISC-V privilege levels and security features",
                "expected_categories": ["security"],
                "complexity": "medium",
            },
            {
                "query": "Interrupt handling and exception processing",
                "expected_categories": ["system"],
                "complexity": "medium",
            },
            {
                "query": "Atomic operations and memory consistency",
                "expected_categories": ["concurrency"],
                "complexity": "medium",
            },
            {
                "query": "Debug support and performance monitoring",
                "expected_categories": ["debug", "analysis"],
                "complexity": "low",
            },
        ]

    def _execute_pipeline_query(
        self, retriever: ModularUnifiedRetriever, query: str, top_k: int = 10
    ) -> Tuple[List[RetrievalResult], Dict[str, Any]]:
        """Execute a query through the complete pipeline and measure stages."""
        embedder = retriever.embedder

        # Measure total pipeline execution
        start_time = time.time()
        query_embedding = embedder.embed([query])[0]
        results = retriever.retrieve(query, query_embedding, top_k=top_k)
        total_time = (time.time() - start_time) * 1000

        # Analyze pipeline stages
        pipeline_info = {
            "total_time_ms": total_time,
            "results_count": len(results),
            "neural_reranker_used": isinstance(retriever.reranker, NeuralReranker),
            "neural_enabled": (
                isinstance(retriever.reranker, NeuralReranker)
                and retriever.reranker.is_enabled()
            ),
            "graph_fusion_used": isinstance(
                retriever.fusion_strategy, GraphEnhancedRRFFusion
            ),
            "graph_enabled": (
                isinstance(retriever.fusion_strategy, GraphEnhancedRRFFusion)
                and getattr(retriever.fusion_strategy, "graph_enabled", False)
            ),
            "vector_index_type": type(retriever.vector_index).__name__,
            "has_scores": all(hasattr(r, "score") for r in results),
            "scores_ordered": (
                all(
                    results[i].score >= results[i + 1].score
                    for i in range(len(results) - 1)
                )
                if len(results) > 1
                else True
            ),
        }

        return results, pipeline_info

    def _test_pipeline_execution(self) -> Dict[str, Any]:
        """Test complete 4-stage pipeline execution."""
        test_result = {"passed": False, "details": {}, "errors": []}

        try:
            logger.info("Testing complete 4-stage pipeline execution...")

            # Test complete Epic 2 pipeline
            config, retriever = self._load_config_and_create_retriever(
                self.configs["complete"]
            )

            # Prepare test data
            documents = self._create_comprehensive_test_documents()
            embedder = retriever.embedder
            documents = self._prepare_documents_with_embeddings(documents, embedder)
            retriever.index_documents(documents)

            # Test queries
            test_queries = self._create_test_queries()

            pipeline_results = []
            total_latencies = []

            for query_info in test_queries:
                query = query_info["query"]

                # Execute pipeline
                results, pipeline_info = self._execute_pipeline_query(
                    retriever, query, top_k=10
                )

                # Validate pipeline execution
                execution_valid = (
                    len(results) > 0
                    and pipeline_info["has_scores"]
                    and pipeline_info["scores_ordered"]
                    and pipeline_info["total_time_ms"]
                    < self.targets["pipeline_latency_p95_ms"]
                )

                pipeline_results.append(
                    {
                        "query": query,
                        "execution_valid": execution_valid,
                        "pipeline_info": pipeline_info,
                    }
                )

                total_latencies.append(pipeline_info["total_time_ms"])

            # Calculate pipeline statistics
            avg_latency = statistics.mean(total_latencies)
            p95_latency = np.percentile(total_latencies, 95) if total_latencies else 0
            max_latency = max(total_latencies) if total_latencies else 0

            successful_executions = sum(
                1 for r in pipeline_results if r["execution_valid"]
            )
            success_rate = (successful_executions / len(pipeline_results)) * 100

            # Verify all Epic 2 features are active
            sample_pipeline = (
                pipeline_results[0]["pipeline_info"] if pipeline_results else {}
            )
            all_features_active = sample_pipeline.get(
                "neural_enabled", False
            ) and sample_pipeline.get("graph_enabled", False)

            meets_latency_target = (
                p95_latency <= self.targets["pipeline_latency_p95_ms"]
            )
            meets_success_target = success_rate >= self.targets["success_rate_percent"]

            execution_details = {
                "queries_tested": len(test_queries),
                "successful_executions": successful_executions,
                "success_rate_percent": success_rate,
                "avg_latency_ms": avg_latency,
                "p95_latency_ms": p95_latency,
                "max_latency_ms": max_latency,
                "target_p95_ms": self.targets["pipeline_latency_p95_ms"],
                "target_success_rate": self.targets["success_rate_percent"],
                "meets_latency_target": meets_latency_target,
                "meets_success_target": meets_success_target,
                "all_features_active": all_features_active,
                "pipeline_results": pipeline_results,
            }

            test_result.update(
                {
                    "passed": meets_latency_target
                    and meets_success_target
                    and all_features_active,
                    "details": execution_details,
                }
            )

            if not meets_latency_target:
                test_result["errors"].append(
                    f"Pipeline P95 latency {p95_latency:.1f}ms exceeds target {self.targets['pipeline_latency_p95_ms']}ms"
                )

            if not meets_success_target:
                test_result["errors"].append(
                    f"Pipeline success rate {success_rate:.1f}% below target {self.targets['success_rate_percent']}%"
                )

            if not all_features_active:
                test_result["errors"].append(
                    "Not all Epic 2 features are active in the pipeline"
                )

            # Store metrics
            self.pipeline_metrics["pipeline_avg_latency_ms"] = avg_latency
            self.pipeline_metrics["pipeline_p95_latency_ms"] = p95_latency
            self.pipeline_metrics["pipeline_success_rate"] = success_rate

        except Exception as e:
            test_result["errors"].append(f"Pipeline execution test failed: {e}")
            logger.error(f"Pipeline execution error: {e}")

        return test_result

    def _test_feature_switching(self) -> Dict[str, Any]:
        """Test configuration-driven feature switching."""
        test_result = {"passed": False, "details": {}, "errors": []}

        try:
            logger.info("Testing configuration-driven feature switching...")

            switching_results = {}

            # Test each configuration
            for config_name, config_file in self.configs.items():
                try:
                    config, retriever = self._load_config_and_create_retriever(
                        config_file
                    )

                    # Prepare test data
                    documents = self._create_comprehensive_test_documents()[
                        :10
                    ]  # Smaller set for speed
                    embedder = retriever.embedder
                    documents = self._prepare_documents_with_embeddings(
                        documents, embedder
                    )
                    retriever.index_documents(documents)

                    # Test query execution
                    test_query = "RISC-V pipeline hazard detection"
                    results, pipeline_info = self._execute_pipeline_query(
                        retriever, test_query
                    )

                    # Determine expected features based on configuration
                    expected_features = {
                        "minimal": {"neural": False, "graph": False},
                        "neural": {"neural": True, "graph": False},
                        "graph": {"neural": False, "graph": True},
                        "complete": {"neural": True, "graph": True},
                    }

                    expected = expected_features.get(config_name, {})

                    # Verify feature activation matches configuration
                    features_match = pipeline_info.get(
                        "neural_enabled", False
                    ) == expected.get("neural", False) and pipeline_info.get(
                        "graph_enabled", False
                    ) == expected.get(
                        "graph", False
                    )

                    switching_results[config_name] = {
                        "loaded": True,
                        "execution_successful": len(results) > 0,
                        "features_match": features_match,
                        "expected_neural": expected.get("neural", False),
                        "actual_neural": pipeline_info.get("neural_enabled", False),
                        "expected_graph": expected.get("graph", False),
                        "actual_graph": pipeline_info.get("graph_enabled", False),
                        "latency_ms": pipeline_info.get("total_time_ms", 0),
                        "results_count": len(results),
                    }

                except Exception as e:
                    switching_results[config_name] = {"loaded": False, "error": str(e)}

            # Check if all configurations worked correctly
            all_loaded = all(
                result.get("loaded", False) for result in switching_results.values()
            )
            all_executed = all(
                result.get("execution_successful", False)
                for result in switching_results.values()
                if result.get("loaded", False)
            )
            all_features_match = all(
                result.get("features_match", False)
                for result in switching_results.values()
                if result.get("loaded", False)
            )

            test_result.update(
                {
                    "passed": all_loaded and all_executed and all_features_match,
                    "details": {
                        "switching_results": switching_results,
                        "configs_tested": len(self.configs),
                        "configs_loaded": sum(
                            1
                            for r in switching_results.values()
                            if r.get("loaded", False)
                        ),
                        "configs_executed": sum(
                            1
                            for r in switching_results.values()
                            if r.get("execution_successful", False)
                        ),
                        "configs_features_correct": sum(
                            1
                            for r in switching_results.values()
                            if r.get("features_match", False)
                        ),
                    },
                }
            )

            if not all_loaded:
                test_result["errors"].append("Some configurations failed to load")
            if not all_executed:
                test_result["errors"].append(
                    "Some configurations failed to execute queries"
                )
            if not all_features_match:
                test_result["errors"].append(
                    "Some configurations have incorrect feature activation"
                )

        except Exception as e:
            test_result["errors"].append(f"Feature switching test failed: {e}")
            logger.error(f"Feature switching error: {e}")

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
            documents = self._create_comprehensive_test_documents()
            embedder = retriever.embedder
            documents = self._prepare_documents_with_embeddings(documents, embedder)
            retriever.index_documents(documents)

            # Create test queries for concurrent execution
            test_queries = [
                "RISC-V pipeline hazard detection mechanisms",
                "Branch prediction in modern processors",
                "Memory hierarchy and cache design",
                "Vector processing capabilities",
                "Security features and privilege levels",
                "Interrupt handling and exceptions",
                "Atomic operations and synchronization",
                "Debug support and monitoring",
                "Virtual memory translation",
                "Performance optimization techniques",
            ]

            def process_query(query_text: str) -> Dict[str, Any]:
                """Process a single query and return results."""
                try:
                    start_time = time.time()
                    results, pipeline_info = self._execute_pipeline_query(
                        retriever, query_text
                    )
                    processing_time = (time.time() - start_time) * 1000

                    return {
                        "success": True,
                        "query": query_text,
                        "processing_time_ms": processing_time,
                        "results_count": len(results),
                        "pipeline_info": pipeline_info,
                    }
                except Exception as e:
                    return {"success": False, "query": query_text, "error": str(e)}

            # Execute queries concurrently
            concurrent_results = []
            start_time = time.time()

            with ThreadPoolExecutor(
                max_workers=self.targets["concurrent_queries"]
            ) as executor:
                futures = [
                    executor.submit(process_query, query) for query in test_queries
                ]

                for future in as_completed(futures):
                    result = future.result()
                    concurrent_results.append(result)

            total_time = (time.time() - start_time) * 1000

            # Analyze concurrent processing results
            successful_queries = [
                r for r in concurrent_results if r.get("success", False)
            ]
            failed_queries = [
                r for r in concurrent_results if not r.get("success", False)
            ]

            success_rate = (len(successful_queries) / len(test_queries)) * 100
            avg_processing_time = (
                statistics.mean([r["processing_time_ms"] for r in successful_queries])
                if successful_queries
                else 0
            )
            max_processing_time = (
                max([r["processing_time_ms"] for r in successful_queries])
                if successful_queries
                else 0
            )

            # Calculate throughput
            throughput_qps = (
                len(successful_queries) / (total_time / 1000) if total_time > 0 else 0
            )

            # Check targets
            meets_concurrent_target = (
                len(successful_queries) >= self.targets["concurrent_queries"]
            )
            meets_success_target = success_rate >= self.targets["success_rate_percent"]
            meets_throughput_target = throughput_qps >= self.targets["throughput_qps"]

            concurrent_details = {
                "queries_total": len(test_queries),
                "queries_successful": len(successful_queries),
                "queries_failed": len(failed_queries),
                "success_rate_percent": success_rate,
                "avg_processing_time_ms": avg_processing_time,
                "max_processing_time_ms": max_processing_time,
                "total_time_ms": total_time,
                "throughput_qps": throughput_qps,
                "target_concurrent_queries": self.targets["concurrent_queries"],
                "target_success_rate": self.targets["success_rate_percent"],
                "target_throughput_qps": self.targets["throughput_qps"],
                "meets_concurrent_target": meets_concurrent_target,
                "meets_success_target": meets_success_target,
                "meets_throughput_target": meets_throughput_target,
                "failed_queries": [r.get("query") for r in failed_queries],
            }

            test_result.update(
                {
                    "passed": meets_concurrent_target
                    and meets_success_target
                    and meets_throughput_target,
                    "details": concurrent_details,
                }
            )

            if not meets_concurrent_target:
                test_result["errors"].append(
                    f"Concurrent processing {len(successful_queries)} queries < target {self.targets['concurrent_queries']}"
                )

            if not meets_success_target:
                test_result["errors"].append(
                    f"Success rate {success_rate:.1f}% < target {self.targets['success_rate_percent']}%"
                )

            if not meets_throughput_target:
                test_result["errors"].append(
                    f"Throughput {throughput_qps:.1f} QPS < target {self.targets['throughput_qps']} QPS"
                )

            # Store metrics
            self.pipeline_metrics["concurrent_success_rate"] = success_rate
            self.pipeline_metrics["concurrent_throughput_qps"] = throughput_qps
            self.pipeline_metrics["concurrent_avg_time_ms"] = avg_processing_time

        except Exception as e:
            test_result["errors"].append(f"Concurrent processing test failed: {e}")
            logger.error(f"Concurrent processing error: {e}")

        return test_result

    def _test_error_handling(self) -> Dict[str, Any]:
        """Test error handling and graceful degradation."""
        test_result = {"passed": False, "details": {}, "errors": []}

        try:
            logger.info("Testing error handling and graceful degradation...")

            # Create retriever for error testing
            config, retriever = self._load_config_and_create_retriever(
                self.configs["complete"]
            )

            # Prepare minimal test data
            documents = self._create_comprehensive_test_documents()[:5]
            embedder = retriever.embedder
            documents = self._prepare_documents_with_embeddings(documents, embedder)
            retriever.index_documents(documents)

            error_scenarios = {}

            # Test 1: Empty query handling
            try:
                results, pipeline_info = self._execute_pipeline_query(
                    retriever, "", top_k=5
                )
                error_scenarios["empty_query"] = {
                    "handled": True,
                    "results_count": len(results),
                    "processing_time_ms": pipeline_info.get("total_time_ms", 0),
                }
            except Exception as e:
                error_scenarios["empty_query"] = {"handled": False, "error": str(e)}

            # Test 2: Very long query handling
            try:
                long_query = "RISC-V " * 100  # Very long query
                results, pipeline_info = self._execute_pipeline_query(
                    retriever, long_query, top_k=5
                )
                error_scenarios["long_query"] = {
                    "handled": True,
                    "results_count": len(results),
                    "processing_time_ms": pipeline_info.get("total_time_ms", 0),
                }
            except Exception as e:
                error_scenarios["long_query"] = {"handled": False, "error": str(e)}

            # Test 3: Invalid top_k parameter
            try:
                results, pipeline_info = self._execute_pipeline_query(
                    retriever, "RISC-V pipeline", top_k=0
                )
                error_scenarios["invalid_top_k"] = {
                    "handled": True,
                    "results_count": len(results),
                    "processing_time_ms": pipeline_info.get("total_time_ms", 0),
                }
            except Exception as e:
                error_scenarios["invalid_top_k"] = {"handled": False, "error": str(e)}

            # Test 4: Query with special characters
            try:
                special_query = "RISC-V @#$%^&*() pipeline []{} hazards"
                results, pipeline_info = self._execute_pipeline_query(
                    retriever, special_query, top_k=5
                )
                error_scenarios["special_characters"] = {
                    "handled": True,
                    "results_count": len(results),
                    "processing_time_ms": pipeline_info.get("total_time_ms", 0),
                }
            except Exception as e:
                error_scenarios["special_characters"] = {
                    "handled": False,
                    "error": str(e),
                }

            # Analyze error handling
            scenarios_handled = sum(
                1
                for scenario in error_scenarios.values()
                if scenario.get("handled", False)
            )
            total_scenarios = len(error_scenarios)
            error_handling_rate = (scenarios_handled / total_scenarios) * 100

            # Check if error handling meets requirements
            meets_error_target = (
                error_handling_rate >= 75.0
            )  # At least 75% of error scenarios handled

            error_handling_details = {
                "scenarios_tested": total_scenarios,
                "scenarios_handled": scenarios_handled,
                "error_handling_rate_percent": error_handling_rate,
                "target_handling_rate": 75.0,
                "meets_error_target": meets_error_target,
                "error_scenarios": error_scenarios,
            }

            test_result.update(
                {"passed": meets_error_target, "details": error_handling_details}
            )

            if not meets_error_target:
                test_result["errors"].append(
                    f"Error handling rate {error_handling_rate:.1f}% < target 75%"
                )

        except Exception as e:
            test_result["errors"].append(f"Error handling test failed: {e}")
            logger.error(f"Error handling error: {e}")

        return test_result

    def _test_load_performance(self) -> Dict[str, Any]:
        """Test pipeline performance under load."""
        test_result = {"passed": False, "details": {}, "errors": []}

        try:
            logger.info("Testing pipeline performance under load...")

            # Create retriever for load testing
            config, retriever = self._load_config_and_create_retriever(
                self.configs["complete"]
            )

            # Prepare larger document set for load testing
            documents = self._create_comprehensive_test_documents()
            # Duplicate documents to create a larger test set
            load_documents = documents * 3  # 45 documents total

            embedder = retriever.embedder
            load_documents = self._prepare_documents_with_embeddings(
                load_documents, embedder
            )
            retriever.index_documents(load_documents)

            # Create load test queries
            load_queries = [
                "RISC-V pipeline hazard detection",
                "Branch prediction mechanisms",
                "Memory hierarchy design",
                "Vector processing operations",
                "Security and privilege levels",
            ]

            # Execute sustained load test
            load_results = []
            load_start_time = time.time()

            # Run queries repeatedly for sustained load
            for round_num in range(10):  # 10 rounds of queries
                for query in load_queries:
                    try:
                        start_time = time.time()
                        results, pipeline_info = self._execute_pipeline_query(
                            retriever, query
                        )
                        processing_time = (time.time() - start_time) * 1000

                        load_results.append(
                            {
                                "success": True,
                                "round": round_num,
                                "query": query,
                                "processing_time_ms": processing_time,
                                "results_count": len(results),
                            }
                        )
                    except Exception as e:
                        load_results.append(
                            {
                                "success": False,
                                "round": round_num,
                                "query": query,
                                "error": str(e),
                            }
                        )

            total_load_time = (time.time() - load_start_time) * 1000

            # Analyze load test results
            successful_queries = [r for r in load_results if r.get("success", False)]
            failed_queries = [r for r in load_results if not r.get("success", False)]

            success_rate = (len(successful_queries) / len(load_results)) * 100
            avg_processing_time = (
                statistics.mean([r["processing_time_ms"] for r in successful_queries])
                if successful_queries
                else 0
            )
            p95_processing_time = (
                np.percentile([r["processing_time_ms"] for r in successful_queries], 95)
                if successful_queries
                else 0
            )

            # Calculate sustained throughput
            sustained_throughput = (
                len(successful_queries) / (total_load_time / 1000)
                if total_load_time > 0
                else 0
            )

            # Check performance degradation over time
            early_results = [r for r in successful_queries if r["round"] < 3]
            late_results = [r for r in successful_queries if r["round"] >= 7]

            if early_results and late_results:
                early_avg = statistics.mean(
                    [r["processing_time_ms"] for r in early_results]
                )
                late_avg = statistics.mean(
                    [r["processing_time_ms"] for r in late_results]
                )
                performance_degradation = (
                    ((late_avg - early_avg) / early_avg) * 100 if early_avg > 0 else 0
                )
            else:
                performance_degradation = 0

            # Check targets
            meets_success_target = success_rate >= self.targets["success_rate_percent"]
            meets_latency_target = (
                p95_processing_time <= self.targets["pipeline_latency_p95_ms"]
            )
            meets_throughput_target = (
                sustained_throughput >= self.targets["throughput_qps"]
            )
            acceptable_degradation = (
                performance_degradation <= 20.0
            )  # <20% degradation acceptable

            load_details = {
                "total_queries": len(load_results),
                "successful_queries": len(successful_queries),
                "failed_queries": len(failed_queries),
                "success_rate_percent": success_rate,
                "avg_processing_time_ms": avg_processing_time,
                "p95_processing_time_ms": p95_processing_time,
                "sustained_throughput_qps": sustained_throughput,
                "performance_degradation_percent": performance_degradation,
                "total_load_time_ms": total_load_time,
                "meets_success_target": meets_success_target,
                "meets_latency_target": meets_latency_target,
                "meets_throughput_target": meets_throughput_target,
                "acceptable_degradation": acceptable_degradation,
            }

            test_result.update(
                {
                    "passed": (
                        meets_success_target
                        and meets_latency_target
                        and meets_throughput_target
                        and acceptable_degradation
                    ),
                    "details": load_details,
                }
            )

            if not meets_success_target:
                test_result["errors"].append(
                    f"Load test success rate {success_rate:.1f}% < target {self.targets['success_rate_percent']}%"
                )
            if not meets_latency_target:
                test_result["errors"].append(
                    f"Load test P95 latency {p95_processing_time:.1f}ms > target {self.targets['pipeline_latency_p95_ms']}ms"
                )
            if not meets_throughput_target:
                test_result["errors"].append(
                    f"Sustained throughput {sustained_throughput:.1f} QPS < target {self.targets['throughput_qps']} QPS"
                )
            if not acceptable_degradation:
                test_result["errors"].append(
                    f"Performance degradation {performance_degradation:.1f}% > 20% threshold"
                )

            # Store metrics
            self.pipeline_metrics["load_success_rate"] = success_rate
            self.pipeline_metrics["load_p95_latency_ms"] = p95_processing_time
            self.pipeline_metrics["sustained_throughput_qps"] = sustained_throughput
            self.pipeline_metrics["performance_degradation_percent"] = (
                performance_degradation
            )

        except Exception as e:
            test_result["errors"].append(f"Load performance test failed: {e}")
            logger.error(f"Load performance error: {e}")

        return test_result

    def _test_feature_combinations(self) -> Dict[str, Any]:
        """Test various feature combination scenarios."""
        test_result = {"passed": False, "details": {}, "errors": []}

        try:
            logger.info("Testing feature combination scenarios...")

            combination_results = {}

            # Test each configuration combination
            for config_name, config_file in self.configs.items():
                try:
                    config, retriever = self._load_config_and_create_retriever(
                        config_file
                    )

                    # Prepare test data
                    documents = self._create_comprehensive_test_documents()[
                        :8
                    ]  # Smaller set for speed
                    embedder = retriever.embedder
                    documents = self._prepare_documents_with_embeddings(
                        documents, embedder
                    )
                    retriever.index_documents(documents)

                    # Test multiple queries to validate consistency
                    test_queries = [
                        "RISC-V pipeline hazard detection",
                        "Memory hierarchy and caching",
                        "Vector processing capabilities",
                    ]

                    query_results = []
                    for query in test_queries:
                        results, pipeline_info = self._execute_pipeline_query(
                            retriever, query
                        )
                        query_results.append(
                            {
                                "query": query,
                                "results_count": len(results),
                                "processing_time_ms": pipeline_info["total_time_ms"],
                                "neural_enabled": pipeline_info.get(
                                    "neural_enabled", False
                                ),
                                "graph_enabled": pipeline_info.get(
                                    "graph_enabled", False
                                ),
                            }
                        )

                    # Check consistency across queries
                    neural_consistent = (
                        len(set(r["neural_enabled"] for r in query_results)) == 1
                    )
                    graph_consistent = (
                        len(set(r["graph_enabled"] for r in query_results)) == 1
                    )

                    avg_processing_time = statistics.mean(
                        [r["processing_time_ms"] for r in query_results]
                    )
                    avg_results_count = statistics.mean(
                        [r["results_count"] for r in query_results]
                    )

                    combination_results[config_name] = {
                        "tested": True,
                        "queries_tested": len(test_queries),
                        "neural_consistent": neural_consistent,
                        "graph_consistent": graph_consistent,
                        "avg_processing_time_ms": avg_processing_time,
                        "avg_results_count": avg_results_count,
                        "neural_enabled": (
                            query_results[0]["neural_enabled"]
                            if query_results
                            else False
                        ),
                        "graph_enabled": (
                            query_results[0]["graph_enabled"]
                            if query_results
                            else False
                        ),
                    }

                except Exception as e:
                    combination_results[config_name] = {
                        "tested": False,
                        "error": str(e),
                    }

            # Analyze combination results
            all_tested = all(
                result.get("tested", False) for result in combination_results.values()
            )
            all_consistent = all(
                result.get("neural_consistent", False)
                and result.get("graph_consistent", False)
                for result in combination_results.values()
                if result.get("tested", False)
            )

            # Verify expected feature activation patterns
            expected_combinations = {
                "minimal": {"neural": False, "graph": False},
                "neural": {"neural": True, "graph": False},
                "graph": {"neural": False, "graph": True},
                "complete": {"neural": True, "graph": True},
            }

            combinations_correct = True
            for config_name, result in combination_results.items():
                if result.get("tested", False):
                    expected = expected_combinations.get(config_name, {})
                    actual_neural = result.get("neural_enabled", False)
                    actual_graph = result.get("graph_enabled", False)

                    if actual_neural != expected.get(
                        "neural", False
                    ) or actual_graph != expected.get("graph", False):
                        combinations_correct = False
                        break

            combination_details = {
                "combinations_tested": len(self.configs),
                "combinations_successful": sum(
                    1 for r in combination_results.values() if r.get("tested", False)
                ),
                "all_tested": all_tested,
                "all_consistent": all_consistent,
                "combinations_correct": combinations_correct,
                "combination_results": combination_results,
            }

            test_result.update(
                {
                    "passed": all_tested and all_consistent and combinations_correct,
                    "details": combination_details,
                }
            )

            if not all_tested:
                test_result["errors"].append("Some feature combinations failed to test")
            if not all_consistent:
                test_result["errors"].append(
                    "Feature activation inconsistent across queries"
                )
            if not combinations_correct:
                test_result["errors"].append(
                    "Feature combinations don't match expected patterns"
                )

        except Exception as e:
            test_result["errors"].append(f"Feature combinations test failed: {e}")
            logger.error(f"Feature combinations error: {e}")

        return test_result


# Test execution functions for pytest integration
def test_epic2_pipeline_validation():
    """Test Epic 2 pipeline validation."""
    validator = Epic2PipelineValidator()
    results = validator.run_all_validations()

    # Assert overall success
    assert (
        results["overall_score"] > 70
    ), f"Pipeline validation failed with score {results['overall_score']}%"
    assert (
        results["passed_tests"] >= 4
    ), f"Only {results['passed_tests']} out of {results['total_tests']} tests passed"

    # Assert specific pipeline requirements
    test_results = results["test_results"]

    # Pipeline execution should meet latency targets
    if test_results.get("pipeline_execution", {}).get("details"):
        p95_latency = test_results["pipeline_execution"]["details"].get(
            "p95_latency_ms", 0
        )
        assert (
            p95_latency <= 700
        ), f"Pipeline P95 latency {p95_latency:.1f}ms exceeds 700ms target"

    # Concurrent processing should work
    if test_results.get("concurrent_processing", {}).get("details"):
        success_rate = test_results["concurrent_processing"]["details"].get(
            "success_rate_percent", 0
        )
        assert (
            success_rate >= 95
        ), f"Concurrent processing success rate {success_rate:.1f}% < 95% target"


if __name__ == "__main__":
    # Run validation when script is executed directly
    validator = Epic2PipelineValidator()
    results = validator.run_all_validations()

    print(f"\n{'='*60}")
    print("EPIC 2 PIPELINE VALIDATION RESULTS")
    print(f"{'='*60}")
    print(f"Overall Score: {results['overall_score']:.1f}%")
    print(f"Passed Tests: {results['passed_tests']}/{results['total_tests']}")

    if results["overall_score"] >= 90:
        print("✅ EXCELLENT - Pipeline exceeds all targets!")
    elif results["overall_score"] >= 80:
        print("✅ GOOD - Pipeline meets most targets")
    else:
        print("❌ NEEDS IMPROVEMENT - Pipeline issues found")

    # Show detailed results
    for test_name, result in results["test_results"].items():
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result.get("errors"):
            for error in result["errors"]:
                print(f"    - {error}")

    # Show pipeline metrics
    if results["pipeline_metrics"]:
        print(f"\n📊 Pipeline Metrics:")
        for metric, value in results["pipeline_metrics"].items():
            if "ms" in metric:
                print(f"  {metric}: {value:.1f}ms")
            elif "qps" in metric:
                print(f"  {metric}: {value:.1f} QPS")
            elif "percent" in metric:
                print(f"  {metric}: {value:.1f}%")
            else:
                print(f"  {metric}: {value:.3f}")
