"""
Epic 2 Component Testing Utilities.

This module provides shared infrastructure for testing Epic 2 sub-components
individually while maintaining integration context within full retriever instances.

Features:
- Component isolation with baseline configurations
- Performance measurement and validation
- Test data generation and management
- Shared assertions and validation utilities
- Component comparison and benchmarking
"""

import os
import sys
import time
import logging
import tempfile
from typing import Dict, List, Any, Optional, Tuple, Union, Type
from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.core.interfaces import Document, RetrievalResult, Embedder
from src.components.retrievers.modular_unified_retriever import ModularUnifiedRetriever
from src.components.embedders.modular_embedder import ModularEmbedder
from src.core.config import ConfigManager

logger = logging.getLogger(__name__)


@dataclass
class ComponentPerformanceMetrics:
    """Performance metrics for component testing."""

    latency_ms: float
    throughput_qps: Optional[float] = None
    memory_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    success_rate: float = 1.0
    error_count: int = 0


@dataclass
class ComponentTestResult:
    """Results from component testing."""

    component_type: str
    component_name: str
    test_name: str
    success: bool
    metrics: ComponentPerformanceMetrics
    details: Dict[str, Any]
    error_message: Optional[str] = None


class ComponentTestDataFactory:
    """Factory for creating test data for component testing."""

    @staticmethod
    def create_minimal_documents(count: int = 10) -> List[Document]:
        """Create minimal test documents for basic functionality testing."""
        documents = []

        base_contents = [
            "RISC-V instruction set architecture overview",
            "Pipeline hazard detection and resolution",
            "Branch prediction algorithms and implementation",
            "Memory hierarchy and cache coherency protocols",
            "Vector processing and SIMD instructions",
            "Floating-point operations and IEEE 754 compliance",
            "Interrupt handling and exception processing",
            "Virtual memory management and page tables",
            "Performance monitoring and profiling tools",
            "Debugging interfaces and trace capabilities",
        ]

        for i in range(count):
            content = base_contents[i % len(base_contents)]
            doc = Document(
                content=f"{content}. Document {i} with additional technical details about implementation specifics.",
                metadata={
                    "id": f"test_doc_{i:03d}",
                    "source": f"test_source_{i}",
                    "category": "technical",
                    "length": len(content),
                    "test_doc": True,
                },
            )
            documents.append(doc)

        return documents

    @staticmethod
    def create_medium_documents(count: int = 100) -> List[Document]:
        """Create medium-sized test dataset for integration testing."""
        documents = []

        # Expanded content templates
        templates = [
            # Core Architecture
            "RISC-V {arch} architecture implements {feature} with {detail}",
            "The {component} subsystem handles {operation} through {mechanism}",
            "Pipeline {stage} performs {function} using {technique}",
            # Performance
            "Performance optimization for {workload} achieves {metric} improvement",
            "Benchmarking {algorithm} shows {result} under {condition}",
            "Latency reduction through {optimization} provides {benefit}",
            # Implementation
            "Hardware implementation of {unit} requires {resource} allocation",
            "Software stack {layer} interfaces with {interface} protocol",
            "System integration {aspect} ensures {property} compliance",
            # Security
            "Security mechanism {protection} prevents {threat} attacks",
            "Cryptographic {algorithm} provides {security} guarantees",
            "Access control {policy} enforces {permission} restrictions",
        ]

        variables = {
            "arch": ["RV32I", "RV64I", "RV32G", "RV64G"],
            "feature": [
                "instruction fetch",
                "decode pipeline",
                "execution units",
                "memory management",
            ],
            "detail": [
                "parallel processing",
                "out-of-order execution",
                "speculative execution",
            ],
            "component": ["cache", "TLB", "branch predictor", "ALU"],
            "operation": ["memory access", "instruction dispatch", "branch resolution"],
            "mechanism": ["forwarding paths", "scoreboarding", "reservation stations"],
            "stage": ["fetch", "decode", "execute", "writeback"],
            "function": [
                "instruction parsing",
                "dependency tracking",
                "resource allocation",
            ],
            "technique": [
                "superscalar design",
                "pipeline forwarding",
                "dynamic scheduling",
            ],
            "workload": [
                "integer operations",
                "floating-point computations",
                "vector processing",
            ],
            "metric": ["25%", "40%", "60%", "75%"],
            "result": ["improved throughput", "reduced latency", "better utilization"],
            "condition": [
                "high-frequency operations",
                "memory-intensive tasks",
                "parallel workloads",
            ],
            "optimization": [
                "cache prefetching",
                "branch prediction",
                "register renaming",
            ],
            "benefit": ["faster execution", "higher IPC", "better energy efficiency"],
            "unit": ["floating-point unit", "vector processor", "crypto accelerator"],
            "resource": ["register file", "execution ports", "memory bandwidth"],
            "layer": ["kernel", "userspace", "firmware"],
            "interface": ["system call", "memory-mapped I/O", "interrupt"],
            "aspect": ["boot sequence", "device drivers", "power management"],
            "property": ["timing", "functional", "security"],
            "protection": ["ASLR", "stack canaries", "CFI"],
            "threat": ["buffer overflow", "ROP", "speculative execution"],
            "algorithm": ["AES", "RSA", "ECC"],
            "security": ["confidentiality", "integrity", "authenticity"],
            "policy": ["RBAC", "MAC", "DAC"],
            "permission": ["read", "write", "execute"],
        }

        import random

        random.seed(42)  # Deterministic for testing

        for i in range(count):
            template = templates[i % len(templates)]

            # Fill template with random variables
            content = template
            for var_name, options in variables.items():
                if f"{{{var_name}}}" in content:
                    content = content.replace(f"{{{var_name}}}", random.choice(options))

            doc = Document(
                content=content + f" This is document {i} in the medium test dataset.",
                metadata={
                    "id": f"medium_doc_{i:03d}",
                    "source": f"medium_source_{i}",
                    "category": random.choice(
                        ["architecture", "performance", "implementation", "security"]
                    ),
                    "complexity": "medium",
                    "test_doc": True,
                    "doc_index": i,
                },
            )
            documents.append(doc)

        return documents

    @staticmethod
    def create_large_documents(count: int = 1000) -> List[Document]:
        """Create large test dataset for performance testing."""
        # Use medium documents as base and expand
        base_docs = ComponentTestDataFactory.create_medium_documents(min(count, 500))
        documents = []

        # Expand by creating variations
        for i in range(count):
            base_doc = base_docs[i % len(base_docs)]

            # Create longer content for performance testing
            expanded_content = base_doc.content
            for j in range(3):  # Add 3 additional sentences
                expanded_content += f" Additional technical detail {j+1} about implementation aspects and performance characteristics."

            doc = Document(
                content=expanded_content,
                metadata={
                    **base_doc.metadata,
                    "id": f"large_doc_{i:04d}",
                    "doc_id": f"large_doc_{i:04d}",
                    "complexity": "large",
                    "expansion_factor": 3,
                },
            )
            documents.append(doc)

        return documents

    @staticmethod
    def create_test_queries(count: int = 20) -> List[str]:
        """Create diverse test queries for component testing."""
        queries = [
            # Technical queries
            "RISC-V instruction set architecture",
            "pipeline hazard detection",
            "branch prediction algorithms",
            "cache coherency protocols",
            "vector processing instructions",
            "floating-point operations",
            "interrupt handling mechanisms",
            "virtual memory management",
            "performance monitoring tools",
            "debugging and trace capabilities",
            # Performance queries
            "optimization techniques",
            "latency reduction methods",
            "throughput improvements",
            "energy efficiency",
            "parallel processing",
            # Implementation queries
            "hardware implementation",
            "software stack integration",
            "system architecture design",
            "resource allocation strategies",
            "execution unit design",
        ]

        # Extend if needed
        while len(queries) < count:
            queries.extend(queries[: min(len(queries), count - len(queries))])

        return queries[:count]


class BaselineConfigurationManager:
    """Manages baseline configurations for component isolation testing."""

    MINIMAL_CONFIGS = {
        "vector_index": {
            "faiss": {
                "type": "faiss",
                "config": {
                    "index_type": "IndexFlatIP",
                    "normalize_embeddings": True,
                    "metric": "cosine",
                },
            },
            "weaviate": {
                "type": "weaviate",
                "config": {
                    "class_name": "Document",
                    "url": "http://localhost:8080",
                    "timeout": 30,
                },
            },
        },
        "sparse": {
            "bm25": {"type": "bm25", "config": {"k1": 1.2, "b": 0.75, "epsilon": 0.25}}
        },
        "fusion": {
            "rrf": {
                "type": "rrf",
                "config": {"k": 60, "weights": {"dense": 0.7, "sparse": 0.3}},
            },
            "weighted": {
                "type": "weighted",
                "config": {"weights": {"dense": 0.7, "sparse": 0.3}, "normalize": True},
            },
            "graph_enhanced_rrf": {
                "type": "graph_enhanced_rrf",
                "config": {
                    "base_fusion": {"k": 60, "weights": {"dense": 0.6, "sparse": 0.3}},
                    "graph_enhancement": {"enabled": True, "graph_weight": 0.1},
                },
            },
        },
        "reranker": {
            "identity": {"type": "identity", "config": {"enabled": True}},
            "semantic": {
                "type": "semantic",
                "config": {
                    "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
                    "enabled": True,
                    "batch_size": 16,
                    "top_k": 10,
                },
            },
            "neural": {
                "type": "neural",
                "config": {
                    "enabled": True,
                    "model_name": "cross-encoder/ms-marco-MiniLM-L6-v2",
                    "batch_size": 16,
                    "max_length": 512,
                    "max_candidates": 50,
                    "initialize_immediately": True,
                },
            },
        },
    }

    @classmethod
    def create_minimal_baseline(cls) -> Dict[str, Any]:
        """Create minimal baseline configuration for component testing."""
        return {
            "vector_index": cls.MINIMAL_CONFIGS["vector_index"]["faiss"],
            "sparse": cls.MINIMAL_CONFIGS["sparse"]["bm25"],
            "fusion": cls.MINIMAL_CONFIGS["fusion"]["rrf"],
            "reranker": cls.MINIMAL_CONFIGS["reranker"]["identity"],
        }

    @classmethod
    def create_focus_config(
        cls,
        component_category: str,
        component_type: str,
        component_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create configuration with focus component and baseline others."""
        config = cls.create_minimal_baseline()

        if component_config:
            config[component_category] = component_config
        else:
            config[component_category] = cls.MINIMAL_CONFIGS[component_category][
                component_type
            ]

        return config

    @classmethod
    def get_component_variants(cls, component_category: str) -> List[str]:
        """Get all available variants for a component category."""
        return list(cls.MINIMAL_CONFIGS[component_category].keys())


class ComponentPerformanceMonitor:
    """Monitors component performance during testing."""

    def __init__(self):
        self.start_time = None
        self.metrics = {}

    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()

    def stop_monitoring(self) -> ComponentPerformanceMetrics:
        """Stop monitoring and return metrics."""
        if self.start_time is None:
            raise ValueError("Monitoring not started")

        latency_ms = (time.time() - self.start_time) * 1000

        return ComponentPerformanceMetrics(latency_ms=latency_ms, success_rate=1.0)

    def measure_operation(
        self, operation_func, *args, **kwargs
    ) -> Tuple[Any, ComponentPerformanceMetrics]:
        """Measure performance of a single operation."""
        self.start_monitoring()

        try:
            result = operation_func(*args, **kwargs)
            metrics = self.stop_monitoring()
            return result, metrics
        except Exception as e:
            latency_ms = (
                (time.time() - self.start_time) * 1000
                if self.start_time is not None
                else 0.0
            )
            metrics = ComponentPerformanceMetrics(
                latency_ms=latency_ms,
                success_rate=0.0,
                error_count=1,
            )
            raise e


class ComponentTestBase(ABC):
    """Base class for component-specific testing."""

    def __init__(self, component_category: str):
        self.component_category = component_category
        self.embedder = self._create_test_embedder()
        self.test_data = ComponentTestDataFactory()
        self.config_manager = BaselineConfigurationManager()
        self.performance_monitor = ComponentPerformanceMonitor()

        # Test datasets
        self.small_docs = None
        self.medium_docs = None
        self.large_docs = None
        self.test_queries = None

    def _create_test_embedder(self) -> Embedder:
        """Create embedder for testing."""
        config = {
            "model": {
                "type": "sentence_transformer",
                "config": {
                    "model_name": "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
                    "embedding_dim": 384,
                    "normalize_embeddings": True,
                    "device": "cpu",  # Use CPU for testing
                },
            },
            "batch_processor": {
                "type": "dynamic",
                "config": {
                    "initial_batch_size": 16,
                    "max_batch_size": 32,
                    "optimize_for_memory": True,
                },
            },
            "cache": {
                "type": "memory",
                "config": {
                    "max_entries": 10,  # Very small cache for testing
                    "max_memory_mb": 1,
                    "enable_statistics": False,
                },
            },
        }
        return ModularEmbedder(config)

    def setup_test_data(self, dataset_size: str = "small"):
        """Set up test data for component testing."""
        if dataset_size == "small":
            self.small_docs = self.test_data.create_minimal_documents(10)
            self.active_docs = self.small_docs
        elif dataset_size == "medium":
            self.medium_docs = self.test_data.create_medium_documents(100)
            self.active_docs = self.medium_docs
        elif dataset_size == "large":
            self.large_docs = self.test_data.create_large_documents(1000)
            self.active_docs = self.large_docs
        else:
            raise ValueError(f"Unknown dataset size: {dataset_size}")

        # Generate embeddings for documents
        if self.active_docs:
            texts = [doc.content for doc in self.active_docs]
            embeddings = self.embedder.embed(texts)

            # Add embeddings to documents
            for doc, embedding in zip(self.active_docs, embeddings):
                doc.embedding = embedding

            logger.debug(f"Generated embeddings for {len(self.active_docs)} documents")

        self.test_queries = self.test_data.create_test_queries(20)

    def create_minimal_retriever(
        self, focus_component_type: str, focus_config: Optional[Dict[str, Any]] = None
    ) -> ModularUnifiedRetriever:
        """Create retriever with minimal baseline + focus component."""
        config = self.config_manager.create_focus_config(
            self.component_category, focus_component_type, focus_config
        )

        retriever = ModularUnifiedRetriever(config, self.embedder)

        # Index test documents
        if hasattr(self, "active_docs") and self.active_docs:
            retriever.index_documents(self.active_docs)

        return retriever

    def measure_component_performance(
        self, retriever: ModularUnifiedRetriever, workload: List[str]
    ) -> ComponentPerformanceMetrics:
        """Measure component-specific performance metrics."""
        total_latency = 0.0
        success_count = 0
        error_count = 0

        for query in workload:
            try:
                results, metrics = self.performance_monitor.measure_operation(
                    retriever.retrieve, query, k=5
                )
                total_latency += metrics.latency_ms
                success_count += 1
            except Exception as e:
                logger.warning(f"Query failed: {e}")
                error_count += 1

        return ComponentPerformanceMetrics(
            latency_ms=total_latency / len(workload) if workload else 0,
            throughput_qps=(
                success_count / (total_latency / 1000) if total_latency > 0 else 0
            ),
            success_rate=success_count / len(workload) if workload else 0,
            error_count=error_count,
        )

    def validate_component_behavior(
        self, retriever: ModularUnifiedRetriever, test_cases: List[Dict[str, Any]]
    ) -> List[ComponentTestResult]:
        """Validate expected component behaviors."""
        results = []

        for test_case in test_cases:
            test_name = test_case.get("name", "unknown_test")
            query = test_case.get("query", "test query")
            expected_properties = test_case.get("expected", {})

            try:
                # Execute test
                search_results = retriever.retrieve(query, k=5)

                # Validate results
                validation_success = True
                details: Dict[str, Any] = {"num_results": len(search_results)}

                # Check minimum results
                if "min_results" in expected_properties:
                    min_results = expected_properties["min_results"]
                    if len(search_results) < min_results:
                        validation_success = False
                        details["min_results_failed"] = (
                            f"Got {len(search_results)}, expected >= {min_results}"
                        )

                # Check score ordering
                if len(search_results) > 1:
                    scores = [r.score for r in search_results]
                    if scores != sorted(scores, reverse=True):
                        validation_success = False
                        details["score_ordering_failed"] = (
                            "Results not ordered by score"
                        )

                result = ComponentTestResult(
                    component_type=self.component_category,
                    component_name=test_case.get("component", "unknown"),
                    test_name=test_name,
                    success=validation_success,
                    metrics=ComponentPerformanceMetrics(
                        latency_ms=0
                    ),  # Would measure in real implementation
                    details=details,
                )

            except Exception as e:
                result = ComponentTestResult(
                    component_type=self.component_category,
                    component_name=test_case.get("component", "unknown"),
                    test_name=test_name,
                    success=False,
                    metrics=ComponentPerformanceMetrics(latency_ms=0, error_count=1),
                    details={},
                    error_message=str(e),
                )

            results.append(result)

        return results

    def compare_component_variants(
        self, variants: List[str], test_workload: List[str]
    ) -> Dict[str, ComponentPerformanceMetrics]:
        """Compare performance across component variants."""
        results = {}

        for variant in variants:
            retriever = self.create_minimal_retriever(variant)
            metrics = self.measure_component_performance(retriever, test_workload)
            results[variant] = metrics

        return results

    @abstractmethod
    def run_component_tests(self) -> List[ComponentTestResult]:
        """Run component-specific tests (implemented by subclasses)."""
        pass


class ComponentTestRunner:
    """Orchestrates component testing across all Epic 2 sub-components."""

    def __init__(self):
        self.test_results = []
        self.component_categories = [
            "vector_indices",
            "fusion_strategies",
            "rerankers",
            "sparse_retrievers",
            "backends",
            "graph_components",
        ]

    def run_all_component_tests(self) -> Dict[str, List[ComponentTestResult]]:
        """Run tests for all component categories."""
        all_results = {}

        for category in self.component_categories:
            logger.info(f"Running {category} tests...")

            try:
                # Import and run component-specific tests
                # This would be implemented when creating the actual test files
                category_results = self._run_category_tests(category)
                all_results[category] = category_results

            except Exception as e:
                logger.error(f"Failed to run {category} tests: {e}")
                all_results[category] = []

        return all_results

    def _run_category_tests(self, category: str) -> List[ComponentTestResult]:
        """Run tests for a specific component category."""
        # Placeholder - would import and run actual test classes
        return []

    def generate_test_report(
        self, results: Dict[str, List[ComponentTestResult]]
    ) -> str:
        """Generate comprehensive test report."""
        report_lines = [
            "# Epic 2 Component Testing Report",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        total_tests = 0
        total_passed = 0

        for category, category_results in results.items():
            if not category_results:
                continue

            category_passed = sum(1 for r in category_results if r.success)
            category_total = len(category_results)
            total_tests += category_total
            total_passed += category_passed

            report_lines.extend(
                [
                    f"## {category.replace('_', ' ').title()}",
                    f"**Results**: {category_passed}/{category_total} tests passed",
                    "",
                ]
            )

            # Component-specific results
            for result in category_results:
                status = "✅ PASS" if result.success else "❌ FAIL"
                report_lines.append(
                    f"- {status} {result.test_name} ({result.metrics.latency_ms:.1f}ms)"
                )

            report_lines.append("")

        # Summary
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        report_lines.extend(
            [
                "## Summary",
                f"**Total Tests**: {total_tests}",
                f"**Passed**: {total_passed}",
                f"**Failed**: {total_tests - total_passed}",
                f"**Success Rate**: {success_rate:.1f}%",
            ]
        )

        return "\n".join(report_lines)


# Shared test utilities
def assert_performance_requirements(
    metrics: ComponentPerformanceMetrics,
    max_latency_ms: float,
    min_success_rate: float = 0.95,
):
    """Assert that performance metrics meet requirements."""
    assert (
        metrics.latency_ms <= max_latency_ms
    ), f"Latency {metrics.latency_ms:.1f}ms exceeds limit {max_latency_ms}ms"
    assert (
        metrics.success_rate >= min_success_rate
    ), f"Success rate {metrics.success_rate:.2%} below minimum {min_success_rate:.2%}"


def create_component_test_environment() -> Dict[str, Any]:
    """Create standardized test environment for component testing."""
    return {
        "temp_dir": tempfile.mkdtemp(prefix="epic2_component_test_"),
        "log_level": logging.INFO,
        "test_seed": 42,
        "embedding_model": "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
    }


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Test the utilities
    factory = ComponentTestDataFactory()
    docs = factory.create_minimal_documents(5)
    queries = factory.create_test_queries(3)

    print(f"Created {len(docs)} test documents")
    print(f"Created {len(queries)} test queries")
    print(f"Sample document: {docs[0].content[:100]}...")
    print(f"Sample query: {queries[0]}")
