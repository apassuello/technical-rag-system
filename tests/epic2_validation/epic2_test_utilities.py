"""
Epic 2 Test Utilities
=====================

Common utilities for Epic 2 validation tests providing shared functionality
for test data loading, configuration management, metrics collection, and
test environment setup.

This module provides:
- Test data factories for consistent document and query creation
- Configuration management utilities for Epic 2 test configs
- Performance measurement and metrics collection
- Test environment validation and setup
- Common assertions and validation functions
- Test result formatting and reporting
"""

import logging
import time
import sys
import os
import json
import yaml
import statistics
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
import numpy as np
import psutil

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


class Epic2TestDataFactory:
    """Factory for creating consistent test data across Epic 2 validation tests."""

    @staticmethod
    def create_risc_v_documents(count: int = 15) -> List[Document]:
        """Create comprehensive RISC-V technical documents for testing."""

        base_documents = [
            {
                "content": "RISC-V instruction pipeline implements a sophisticated 5-stage design with fetch, decode, execute, memory access, and writeback stages. The pipeline includes comprehensive hazard detection units that monitor data dependencies between instructions and implement forwarding mechanisms to resolve conflicts without stalling.",
                "metadata": {
                    "id": "pipeline_architecture",
                    "category": "architecture",
                    "complexity": "high",
                    "topics": ["pipeline", "hazards", "forwarding"],
                },
            },
            {
                "content": "Hazard detection in RISC-V processors involves analyzing instruction dependencies and implementing forwarding paths. The forwarding unit can bypass data from the execute stage or memory stage directly to subsequent instructions that need the same registers, eliminating the need for pipeline stalls.",
                "metadata": {
                    "id": "hazard_detection",
                    "category": "pipeline",
                    "complexity": "medium",
                    "topics": ["hazards", "forwarding", "dependencies"],
                },
            },
            {
                "content": "Branch prediction mechanisms in RISC-V include two-level adaptive predictors with global and local history components. The branch target buffer maintains recently used branch addresses, while the return address stack optimizes function call and return patterns for improved control flow prediction.",
                "metadata": {
                    "id": "branch_prediction",
                    "category": "control_flow",
                    "complexity": "high",
                    "topics": ["prediction", "control", "performance"],
                },
            },
            {
                "content": "Control hazards occur when branch instructions alter the normal sequential flow of instruction execution. RISC-V processors implement various techniques including branch delay slots, static prediction, and dynamic prediction to minimize the performance impact of control dependencies.",
                "metadata": {
                    "id": "control_hazards",
                    "category": "hazards",
                    "complexity": "medium",
                    "topics": ["control", "hazards", "branching"],
                },
            },
            {
                "content": "RISC-V memory hierarchy design includes separate L1 instruction and data caches, a unified L2 cache, and main memory. Cache coherency protocols ensure data consistency across multiple cores using modified, exclusive, shared, and invalid (MESI) states for maintaining cache line consistency.",
                "metadata": {
                    "id": "memory_hierarchy",
                    "category": "memory",
                    "complexity": "high",
                    "topics": ["memory", "cache", "hierarchy"],
                },
            },
            {
                "content": "Cache coherency in multicore RISC-V systems maintains data consistency through snooping protocols. When one core modifies cached data, other cores with copies of that data are notified and must invalidate or update their copies accordingly, ensuring memory consistency across the system.",
                "metadata": {
                    "id": "cache_coherency",
                    "category": "memory",
                    "complexity": "high",
                    "topics": ["cache", "coherency", "multicore"],
                },
            },
            {
                "content": "Vector extensions in RISC-V provide Single Instruction Multiple Data (SIMD) capabilities through variable-length vector registers. The vector architecture supports configurable vector lengths and multiple data types for efficient parallel processing of arrays and matrix operations.",
                "metadata": {
                    "id": "vector_extensions",
                    "category": "simd",
                    "complexity": "medium",
                    "topics": ["vector", "simd", "parallel"],
                },
            },
            {
                "content": "RISC-V vector processing includes support for vector arithmetic, logical operations, memory operations, and reduction operations. Vector mask registers enable predicated execution for conditional vector operations, allowing efficient handling of sparse data and conditional computations.",
                "metadata": {
                    "id": "vector_processing",
                    "category": "simd",
                    "complexity": "medium",
                    "topics": ["vector", "operations", "masking"],
                },
            },
            {
                "content": "RISC-V privilege architecture defines three privilege levels: machine mode (M-mode), supervisor mode (S-mode), and user mode (U-mode). Each mode has specific access rights to system resources and instruction execution capabilities, providing security isolation and system control.",
                "metadata": {
                    "id": "privilege_levels",
                    "category": "security",
                    "complexity": "medium",
                    "topics": ["privilege", "security", "modes"],
                },
            },
            {
                "content": "Virtual memory in RISC-V provides address translation through page tables with configurable page sizes. The Translation Lookaside Buffer (TLB) caches recent address translations to improve memory access performance, while page table walkers handle TLB misses efficiently.",
                "metadata": {
                    "id": "virtual_memory",
                    "category": "memory",
                    "complexity": "high",
                    "topics": ["virtual", "memory", "translation"],
                },
            },
            {
                "content": "Interrupt handling in RISC-V supports both synchronous exceptions and asynchronous interrupts. The processor maintains control and status registers (CSRs) for interrupt configuration and uses vectored interrupt dispatch for efficient handling of multiple interrupt sources.",
                "metadata": {
                    "id": "interrupt_handling",
                    "category": "system",
                    "complexity": "medium",
                    "topics": ["interrupts", "exceptions", "system"],
                },
            },
            {
                "content": "Atomic operations in RISC-V ensure memory consistency in multiprocessor systems. Load-reserved and store-conditional instructions provide the foundation for implementing higher-level synchronization primitives like mutexes, semaphores, and lock-free data structures.",
                "metadata": {
                    "id": "atomic_operations",
                    "category": "concurrency",
                    "complexity": "medium",
                    "topics": ["atomic", "synchronization", "concurrency"],
                },
            },
            {
                "content": "Debug support in RISC-V includes hardware breakpoints, single-step execution capabilities, and program trace generation. The debug module provides external debug access through JTAG or other debug transport interfaces, enabling comprehensive debugging and development support.",
                "metadata": {
                    "id": "debug_support",
                    "category": "debug",
                    "complexity": "low",
                    "topics": ["debug", "breakpoints", "trace"],
                },
            },
            {
                "content": "Performance monitoring in RISC-V processors uses hardware performance counters to track events like cache misses, branch mispredictions, and instruction counts. These counters support performance analysis and optimization by providing detailed execution statistics and bottleneck identification.",
                "metadata": {
                    "id": "performance_monitoring",
                    "category": "analysis",
                    "complexity": "low",
                    "topics": ["performance", "monitoring", "counters"],
                },
            },
            {
                "content": "Instruction encoding in RISC-V uses a variable-length format with 16-bit, 32-bit, and longer instruction formats. The base 32-bit instructions provide the core functionality while compressed 16-bit instructions improve code density and reduce memory bandwidth requirements.",
                "metadata": {
                    "id": "instruction_encoding",
                    "category": "instruction_set",
                    "complexity": "low",
                    "topics": ["encoding", "instructions", "compression"],
                },
            },
        ]

        # Generate requested number of documents (cycling through base documents if needed)
        documents = []
        for i in range(count):
            base_doc = base_documents[i % len(base_documents)]

            # Add variation to content if we're cycling through
            content = base_doc["content"]
            if i >= len(base_documents):
                content += f" Extended context for document variant {i + 1} with additional technical details and implementation considerations."

            # Update metadata with unique ID
            metadata = base_doc["metadata"].copy()
            metadata["id"] = f"{metadata['id']}_{i + 1}"
            metadata["variant"] = i // len(base_documents) + 1

            documents.append(
                Document(content=content, metadata=metadata, embedding=None)
            )

        return documents

    @staticmethod
    def create_test_queries() -> List[Dict[str, Any]]:
        """Create test queries with relevance judgments for quality evaluation."""
        return [
            {
                "query": "RISC-V pipeline hazard detection and forwarding mechanisms",
                "relevant_doc_patterns": ["pipeline", "hazard", "forwarding"],
                "expected_categories": ["architecture", "pipeline"],
                "complexity": "high",
                "description": "Pipeline hazards and detection",
            },
            {
                "query": "Branch prediction techniques in RISC-V processors",
                "relevant_doc_patterns": ["branch", "prediction", "control"],
                "expected_categories": ["control_flow"],
                "complexity": "medium",
                "description": "Branch prediction mechanisms",
            },
            {
                "query": "Memory hierarchy and cache coherency protocols",
                "relevant_doc_patterns": ["memory", "cache", "coherency"],
                "expected_categories": ["memory"],
                "complexity": "high",
                "description": "Memory system architecture",
            },
            {
                "query": "Vector processing and SIMD operations in RISC-V",
                "relevant_doc_patterns": ["vector", "simd", "parallel"],
                "expected_categories": ["simd"],
                "complexity": "medium",
                "description": "Vector processing capabilities",
            },
            {
                "query": "RISC-V privilege levels and security features",
                "relevant_doc_patterns": ["privilege", "security", "modes"],
                "expected_categories": ["security"],
                "complexity": "medium",
                "description": "Security and privilege architecture",
            },
            {
                "query": "Interrupt handling and exception processing",
                "relevant_doc_patterns": ["interrupt", "exception", "system"],
                "expected_categories": ["system"],
                "complexity": "medium",
                "description": "System control and interrupts",
            },
            {
                "query": "Atomic operations and memory consistency",
                "relevant_doc_patterns": ["atomic", "synchronization", "concurrency"],
                "expected_categories": ["concurrency"],
                "complexity": "medium",
                "description": "Concurrency and synchronization",
            },
            {
                "query": "Debug support and performance monitoring",
                "relevant_doc_patterns": ["debug", "performance", "monitoring"],
                "expected_categories": ["debug", "analysis"],
                "complexity": "low",
                "description": "Development and analysis tools",
            },
        ]


class Epic2ConfigurationManager:
    """Manager for Epic 2 test configuration files and feature combinations."""

    def __init__(self):
        """Initialize configuration manager."""
        self.config_files = {
            "minimal": "test_epic2_minimal.yaml",
            "neural": "test_epic2_neural_enabled.yaml",
            "graph": "test_epic2_graph_enabled.yaml",
            "complete": "test_epic2_all_features.yaml",
            "base": "test_epic2_base.yaml",
        }

        self.expected_features = {
            "minimal": {"neural": False, "graph": False},
            "neural": {"neural": True, "graph": False},
            "graph": {"neural": False, "graph": True},
            "complete": {"neural": True, "graph": True},
            "base": {"neural": True, "graph": True},  # Base config has both features
        }

    def load_config_and_create_retriever(
        self, config_name: str
    ) -> Tuple[Any, ModularUnifiedRetriever]:
        """Load configuration and create retriever."""
        if config_name not in self.config_files:
            raise ValueError(f"Unknown configuration: {config_name}")

        config_file = self.config_files[config_name]
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

    def validate_feature_activation(
        self, retriever: ModularUnifiedRetriever, config_name: str
    ) -> Dict[str, Any]:
        """Validate that features are activated correctly for the given configuration."""
        expected = self.expected_features.get(config_name, {})

        # Check neural reranking
        neural_enabled = (
            isinstance(retriever.reranker, NeuralReranker)
            and retriever.reranker.is_enabled()
        )

        # Check graph enhancement
        graph_enabled = isinstance(
            retriever.fusion_strategy, GraphEnhancedRRFFusion
        ) and getattr(retriever.fusion_strategy, "graph_enabled", False)

        return {
            "neural_expected": expected.get("neural", False),
            "neural_actual": neural_enabled,
            "neural_correct": neural_enabled == expected.get("neural", False),
            "graph_expected": expected.get("graph", False),
            "graph_actual": graph_enabled,
            "graph_correct": graph_enabled == expected.get("graph", False),
            "all_correct": (
                neural_enabled == expected.get("neural", False)
                and graph_enabled == expected.get("graph", False)
            ),
        }

    def get_all_config_names(self) -> List[str]:
        """Get list of all available configuration names."""
        return list(self.config_files.keys())


class Epic2PerformanceMetrics:
    """Performance measurement and metrics collection for Epic 2 tests."""

    def __init__(self):
        """Initialize performance metrics collector."""
        self.start_times = {}
        self.metrics = {}
        self.baseline_memory = None

    def start_timer(self, operation: str):
        """Start timing an operation."""
        self.start_times[operation] = time.time()

    def end_timer(self, operation: str) -> float:
        """End timing an operation and return duration in milliseconds."""
        if operation not in self.start_times:
            raise ValueError(f"Timer not started for operation: {operation}")

        duration_ms = (time.time() - self.start_times[operation]) * 1000
        self.metrics[f"{operation}_time_ms"] = duration_ms
        del self.start_times[operation]
        return duration_ms

    def measure_memory_usage(self, label: str = "current") -> Dict[str, float]:
        """Measure current memory usage."""
        process = psutil.Process()
        memory_info = process.memory_info()

        memory_data = {
            "rss_mb": memory_info.rss / (1024 * 1024),
            "vms_mb": memory_info.vms / (1024 * 1024),
            "percent": process.memory_percent(),
            "available_mb": psutil.virtual_memory().available / (1024 * 1024),
        }

        self.metrics[f"{label}_memory"] = memory_data
        return memory_data

    def set_baseline_memory(self):
        """Set baseline memory measurement."""
        self.baseline_memory = self.measure_memory_usage("baseline")

    def calculate_memory_overhead(self) -> Optional[float]:
        """Calculate memory overhead vs baseline in MB."""
        if self.baseline_memory is None:
            return None

        current_memory = self.measure_memory_usage("current")
        return current_memory["rss_mb"] - self.baseline_memory["rss_mb"]

    def record_metric(self, name: str, value: Union[float, int, bool, str]):
        """Record a custom metric."""
        self.metrics[name] = value

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all recorded metrics."""
        return self.metrics.copy()

    def calculate_statistics(self, values: List[float]) -> Dict[str, float]:
        """Calculate statistical measures for a list of values."""
        if not values:
            return {}

        return {
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
            "min": min(values),
            "max": max(values),
            "p95": np.percentile(values, 95),
            "p99": np.percentile(values, 99),
        }


class Epic2TestValidator:
    """Common validation functions for Epic 2 tests."""

    @staticmethod
    def validate_retrieval_results(results: List[RetrievalResult]) -> Dict[str, bool]:
        """Validate retrieval results structure and content."""
        return {
            "has_results": len(results) > 0,
            "all_have_documents": all(
                hasattr(r, "document") and r.document is not None for r in results
            ),
            "all_have_scores": all(
                hasattr(r, "score") and r.score is not None for r in results
            ),
            "scores_numeric": all(
                isinstance(r.score, (int, float))
                for r in results
                if hasattr(r, "score")
            ),
            "scores_valid_range": all(
                0 <= r.score <= 1 for r in results if hasattr(r, "score")
            ),
            "scores_ordered": (
                all(
                    results[i].score >= results[i + 1].score
                    for i in range(len(results) - 1)
                )
                if len(results) > 1
                else True
            ),
        }

    @staticmethod
    def validate_pipeline_info(pipeline_info: Dict[str, Any]) -> Dict[str, bool]:
        """Validate pipeline information structure."""
        required_fields = [
            "total_time_ms",
            "results_count",
            "neural_reranker_used",
            "graph_fusion_used",
        ]

        return {
            "has_required_fields": all(
                field in pipeline_info for field in required_fields
            ),
            "valid_timing": isinstance(pipeline_info.get("total_time_ms"), (int, float))
            and pipeline_info.get("total_time_ms", 0) > 0,
            "valid_count": isinstance(pipeline_info.get("results_count"), int)
            and pipeline_info.get("results_count", 0) >= 0,
            "valid_flags": all(
                isinstance(pipeline_info.get(field), bool)
                for field in ["neural_reranker_used", "graph_fusion_used"]
            ),
        }

    @staticmethod
    def assert_performance_target(
        actual: float, target: float, metric_name: str, tolerance: float = 0.1
    ):
        """Assert that a performance metric meets its target with optional tolerance."""
        if actual > target * (1 + tolerance):
            raise AssertionError(
                f"{metric_name}: {actual:.1f} exceeds target {target:.1f} (tolerance: {tolerance*100:.0f}%)"
            )

    @staticmethod
    def assert_quality_improvement(
        baseline: float, enhanced: float, min_improvement: float, metric_name: str
    ):
        """Assert that a quality metric shows minimum improvement."""
        if baseline <= 0:
            raise AssertionError(f"{metric_name}: Invalid baseline value {baseline}")

        improvement = ((enhanced - baseline) / baseline) * 100
        if improvement < min_improvement:
            raise AssertionError(
                f"{metric_name}: Improvement {improvement:.1f}% < required {min_improvement}%"
            )


class Epic2TestReporter:
    """Test result formatting and reporting for Epic 2 validation."""

    def __init__(self):
        """Initialize test reporter."""
        self.report_data = {
            "timestamp": datetime.now().isoformat(),
            "test_results": {},
            "performance_metrics": {},
            "summary": {},
        }

    def add_test_result(self, test_name: str, result: Dict[str, Any]):
        """Add a test result to the report."""
        self.report_data["test_results"][test_name] = result

    def add_performance_metrics(self, metrics: Dict[str, Any]):
        """Add performance metrics to the report."""
        self.report_data["performance_metrics"].update(metrics)

    def generate_summary(self):
        """Generate test summary statistics."""
        test_results = self.report_data["test_results"]

        total_tests = len(test_results)
        passed_tests = sum(
            1 for result in test_results.values() if result.get("passed", False)
        )

        self.report_data["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (
                (passed_tests / total_tests * 100) if total_tests > 0 else 0
            ),
            "overall_status": "PASS" if passed_tests == total_tests else "FAIL",
        }

    def format_console_report(self) -> str:
        """Format report for console output."""
        self.generate_summary()

        lines = []
        lines.append("=" * 60)
        lines.append("EPIC 2 VALIDATION TEST REPORT")
        lines.append("=" * 60)

        summary = self.report_data["summary"]
        lines.append(f"Timestamp: {self.report_data['timestamp']}")
        lines.append(f"Overall Status: {summary['overall_status']}")
        lines.append(f"Success Rate: {summary['success_rate']:.1f}%")
        lines.append(
            f"Tests Passed: {summary['passed_tests']}/{summary['total_tests']}"
        )
        lines.append("")

        # Test results
        lines.append("Test Results:")
        lines.append("-" * 40)
        for test_name, result in self.report_data["test_results"].items():
            status = "✅ PASS" if result.get("passed", False) else "❌ FAIL"
            lines.append(f"  {test_name}: {status}")

            if not result.get("passed", False) and result.get("errors"):
                for error in result["errors"]:
                    lines.append(f"    - {error}")

        lines.append("")

        # Performance metrics
        if self.report_data["performance_metrics"]:
            lines.append("Performance Metrics:")
            lines.append("-" * 40)
            for metric, value in self.report_data["performance_metrics"].items():
                if isinstance(value, (int, float)):
                    if "ms" in metric:
                        lines.append(f"  {metric}: {value:.1f}ms")
                    elif "percent" in metric or "rate" in metric:
                        lines.append(f"  {metric}: {value:.1f}%")
                    elif "qps" in metric:
                        lines.append(f"  {metric}: {value:.1f} QPS")
                    else:
                        lines.append(f"  {metric}: {value:.3f}")
                else:
                    lines.append(f"  {metric}: {value}")

        return "\n".join(lines)

    def save_json_report(self, filename: str):
        """Save report as JSON file."""
        self.generate_summary()

        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(self.report_data, f, indent=2, default=str)


class Epic2TestEnvironment:
    """Test environment validation and setup for Epic 2 tests."""

    @staticmethod
    def validate_environment() -> Dict[str, Any]:
        """Validate that the environment is ready for Epic 2 testing."""
        validation_results = {}

        # Check Python version
        python_version = sys.version_info
        validation_results["python_version"] = {
            "version": f"{python_version.major}.{python_version.minor}.{python_version.micro}",
            "supported": python_version >= (3, 8),
        }

        # Check required modules
        required_modules = [
            "numpy",
            "scipy",
            "transformers",
            "torch",
            "sentence_transformers",
            "faiss",
            "networkx",
            "psutil",
            "yaml",
        ]

        module_status = {}
        for module in required_modules:
            try:
                __import__(module)
                module_status[module] = {"available": True, "error": None}
            except ImportError as e:
                module_status[module] = {"available": False, "error": str(e)}

        validation_results["modules"] = module_status

        # Check memory availability
        memory = psutil.virtual_memory()
        validation_results["memory"] = {
            "total_gb": memory.total / (1024**3),
            "available_gb": memory.available / (1024**3),
            "sufficient": memory.available / (1024**3) >= 4.0,  # Need at least 4GB
        }

        # Check configuration files
        config_files = [
            "test_epic2_minimal.yaml",
            "test_epic2_neural_enabled.yaml",
            "test_epic2_graph_enabled.yaml",
            "test_epic2_all_features.yaml",
        ]

        config_status = {}
        for config_file in config_files:
            config_path = Path(f"config/{config_file}")
            config_status[config_file] = {
                "exists": config_path.exists(),
                "readable": config_path.exists() and config_path.is_file(),
            }

        validation_results["config_files"] = config_status

        # Overall status
        all_modules_ok = all(status["available"] for status in module_status.values())
        all_configs_ok = all(status["readable"] for status in config_status.values())
        memory_ok = validation_results["memory"]["sufficient"]
        python_ok = validation_results["python_version"]["supported"]

        validation_results["overall"] = {
            "ready": all_modules_ok and all_configs_ok and memory_ok and python_ok,
            "issues": [],
        }

        if not python_ok:
            validation_results["overall"]["issues"].append("Python version < 3.8")
        if not all_modules_ok:
            missing = [
                mod for mod, status in module_status.items() if not status["available"]
            ]
            validation_results["overall"]["issues"].append(
                f"Missing modules: {', '.join(missing)}"
            )
        if not all_configs_ok:
            missing = [
                cfg for cfg, status in config_status.items() if not status["readable"]
            ]
            validation_results["overall"]["issues"].append(
                f"Missing configs: {', '.join(missing)}"
            )
        if not memory_ok:
            validation_results["overall"]["issues"].append(
                "Insufficient memory (<4GB available)"
            )

        return validation_results

    @staticmethod
    def print_environment_status():
        """Print environment validation status to console."""
        results = Epic2TestEnvironment.validate_environment()

        print("Epic 2 Test Environment Validation")
        print("=" * 40)

        overall = results["overall"]
        status = "✅ READY" if overall["ready"] else "❌ NOT READY"
        print(f"Status: {status}")

        if overall["issues"]:
            print("Issues:")
            for issue in overall["issues"]:
                print(f"  - {issue}")

        print(
            f"\nPython: {results['python_version']['version']} ({'✅' if results['python_version']['supported'] else '❌'})"
        )
        print(
            f"Memory: {results['memory']['available_gb']:.1f}GB available ({'✅' if results['memory']['sufficient'] else '❌'})"
        )

        print("\nModules:")
        for module, status in results["modules"].items():
            symbol = "✅" if status["available"] else "❌"
            print(f"  {module}: {symbol}")

        print("\nConfig Files:")
        for config, status in results["config_files"].items():
            symbol = "✅" if status["readable"] else "❌"
            print(f"  {config}: {symbol}")


# Convenience functions for common operations
def prepare_documents_with_embeddings(
    documents: List[Document], embedder
) -> List[Document]:
    """Prepare documents with embeddings for indexing."""
    texts = [doc.content for doc in documents]
    embeddings = embedder.embed(texts)

    for doc, embedding in zip(documents, embeddings):
        doc.embedding = embedding

    return documents


def execute_retrieval_with_timing(
    retriever: ModularUnifiedRetriever, query: str, top_k: int = 10
) -> Tuple[List[RetrievalResult], float]:
    """Execute retrieval with timing measurement."""
    embedder = retriever.embedder

    start_time = time.time()
    query_embedding = embedder.embed([query])[0]
    results = retriever.retrieve(query, query_embedding, top_k=top_k)
    processing_time = (time.time() - start_time) * 1000

    return results, processing_time


def compare_configurations(
    config1_name: str, config2_name: str, test_queries: List[str]
) -> Dict[str, Any]:
    """Compare two configurations across multiple queries."""
    config_manager = Epic2ConfigurationManager()

    # Load configurations
    config1, retriever1 = config_manager.load_config_and_create_retriever(config1_name)
    config2, retriever2 = config_manager.load_config_and_create_retriever(config2_name)

    # Prepare test data
    documents = Epic2TestDataFactory.create_risc_v_documents(10)

    embedder1 = retriever1.embedder
    documents1 = prepare_documents_with_embeddings(documents, embedder1)
    retriever1.index_documents(documents1)

    embedder2 = retriever2.embedder
    documents2 = prepare_documents_with_embeddings(documents, embedder2)
    retriever2.index_documents(documents2)

    # Compare performance
    results1_times = []
    results2_times = []

    for query in test_queries:
        results1, time1 = execute_retrieval_with_timing(retriever1, query)
        results2, time2 = execute_retrieval_with_timing(retriever2, query)

        results1_times.append(time1)
        results2_times.append(time2)

    metrics = Epic2PerformanceMetrics()
    stats1 = metrics.calculate_statistics(results1_times)
    stats2 = metrics.calculate_statistics(results2_times)

    return {
        "config1": config1_name,
        "config2": config2_name,
        "config1_stats": stats1,
        "config2_stats": stats2,
        "queries_tested": len(test_queries),
        "avg_speedup": stats1["mean"] / stats2["mean"] if stats2["mean"] > 0 else 1.0,
    }
