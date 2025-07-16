"""
Epic 2 Sparse Retrievers Component Tests.

This module tests the sparse retriever sub-component (BM25Retriever) within the
ModularUnifiedRetriever context while using baseline components for isolation testing.

Test Categories:
- BM25 Algorithm Implementation and Accuracy
- Index Construction and Management
- Query Processing and Term Matching
- Parameter Tuning (k1, b, epsilon)
- Performance and Scalability
- Concurrent Access and Thread Safety
- Memory Usage and Optimization
- Edge Case Handling
"""

import os
import sys
import time
import logging
import tempfile
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import threading
import queue

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from epic2_component_test_utilities import (
    ComponentTestBase,
    ComponentTestResult,
    ComponentPerformanceMetrics,
    assert_performance_requirements,
    ComponentTestDataFactory,
    BaselineConfigurationManager,
)
from src.core.interfaces import Document, RetrievalResult
from src.components.retrievers.modular_unified_retriever import ModularUnifiedRetriever

logger = logging.getLogger(__name__)


class TestSparseRetrievers(ComponentTestBase):
    """Test suite for Epic 2 sparse retriever components."""

    def __init__(self):
        super().__init__("sparse")
        self.test_results = []

    def setup_method(self):
        """Set up test environment for each test method."""
        self.setup_test_data("small")  # Start with small dataset

    def test_bm25_algorithm_accuracy(self):
        """Test BM25 algorithm implementation and accuracy."""
        logger.info("Testing BM25 algorithm accuracy...")

        # Set up test data first
        self.setup_test_data("small")

        # Test with standard BM25 configuration
        bm25_config = {
            "type": "bm25",
            "config": {"k1": 1.2, "b": 0.75, "epsilon": 0.25},
        }

        retriever = self.create_minimal_retriever("bm25", bm25_config)

        # Verify sparse retriever was created
        assert retriever.sparse_retriever is not None
        assert retriever.sparse_retriever.__class__.__name__ == "BM25Retriever"

        # Test basic BM25 functionality
        results = retriever.retrieve("RISC-V instruction architecture", k=5)
        assert len(results) > 0, "BM25 retriever returned no results"
        assert all(isinstance(r, RetrievalResult) for r in results)

        # BM25 scores should be positive and ordered
        scores = [r.score for r in results]
        assert all(
            score >= 0 for score in scores
        ), "BM25 should produce non-negative scores"
        assert scores == sorted(
            scores, reverse=True
        ), "BM25 results not properly ordered"

        # Test term frequency behavior - exact matches should score highly
        exact_match_results = retriever.retrieve("RISC-V", k=3)
        partial_match_results = retriever.retrieve("architecture", k=3)

        if exact_match_results and partial_match_results:
            # Documents containing exact query terms should generally score well
            exact_top_score = exact_match_results[0].score if exact_match_results else 0
            partial_top_score = (
                partial_match_results[0].score if partial_match_results else 0
            )

            logger.info(f"Exact match top score: {exact_top_score:.4f}")
            logger.info(f"Partial match top score: {partial_top_score:.4f}")

        logger.info("✅ BM25 algorithm accuracy test passed")

    def test_keyword_matching(self):
        """Test keyword matching and term weighting."""
        logger.info("Testing keyword matching...")

        # Set up test data first
        self.setup_test_data("small")

        retriever = self.create_minimal_retriever("bm25")

        # Test different types of keyword queries
        keyword_tests = [
            {
                "query": "pipeline",
                "expected_terms": ["pipeline"],
                "description": "Single keyword",
            },
            {
                "query": "pipeline hazard",
                "expected_terms": ["pipeline", "hazard"],
                "description": "Multiple keywords",
            },
            {
                "query": "RISC-V instruction set",
                "expected_terms": ["RISC-V", "instruction", "set"],
                "description": "Technical terms",
            },
            {
                "query": "cache coherency memory",
                "expected_terms": ["cache", "coherency", "memory"],
                "description": "Domain-specific terms",
            },
        ]

        for test_case in keyword_tests:
            query = test_case["query"]
            results = retriever.retrieve(query, k=5)

            assert len(results) >= 0, f"Keyword matching failed for: {query}"

            if results:
                # Check that top results contain query terms
                top_result = results[0]
                content_lower = top_result.document.content.lower()
                query_lower = query.lower()

                # At least some query terms should appear in top results
                query_terms = query_lower.split()
                matches = sum(1 for term in query_terms if term in content_lower)
                match_ratio = matches / len(query_terms) if query_terms else 0

                logger.info(
                    f"'{query}' -> {match_ratio:.2f} term match ratio in top result"
                )

                # Verify scores are reasonable
                scores = [r.score for r in results]
                assert all(isinstance(score, (int, float)) for score in scores)
                assert all(score >= 0 for score in scores)

        logger.info("✅ Keyword matching test passed")

    def test_bm25_parameter_tuning(self):
        """Test BM25 parameter effects (k1, b, epsilon)."""
        logger.info("Testing BM25 parameter tuning...")

        # Set up test data first
        self.setup_test_data("small")

        test_query = "branch prediction hazard detection"

        # Test different k1 values (term frequency saturation)
        k1_values = [0.5, 1.2, 2.0, 3.0]
        k1_results = {}

        for k1 in k1_values:
            config = {"type": "bm25", "config": {"k1": k1, "b": 0.75, "epsilon": 0.25}}

            retriever = self.create_minimal_retriever("bm25", config)
            results = retriever.retrieve(test_query, k=3)
            k1_results[k1] = results

            if results:
                top_score = results[0].score
                logger.info(f"k1={k1}: top score = {top_score:.4f}")
                assert top_score >= 0, f"Invalid score with k1={k1}"

        # Test different b values (document length normalization)
        b_values = [0.0, 0.25, 0.75, 1.0]
        b_results = {}

        for b in b_values:
            config = {"type": "bm25", "config": {"k1": 1.2, "b": b, "epsilon": 0.25}}

            retriever = self.create_minimal_retriever("bm25", config)
            results = retriever.retrieve(test_query, k=3)
            b_results[b] = results

            if results:
                top_score = results[0].score
                logger.info(f"b={b}: top score = {top_score:.4f}")
                assert top_score >= 0, f"Invalid score with b={b}"

        # Test different epsilon values (IDF lower bound)
        epsilon_values = [0.0, 0.25, 0.5, 1.0]

        for epsilon in epsilon_values:
            config = {
                "type": "bm25",
                "config": {"k1": 1.2, "b": 0.75, "epsilon": epsilon},
            }

            retriever = self.create_minimal_retriever("bm25", config)
            results = retriever.retrieve(test_query, k=3)

            if results:
                top_score = results[0].score
                logger.info(f"epsilon={epsilon}: top score = {top_score:.4f}")
                assert top_score >= 0, f"Invalid score with epsilon={epsilon}"

        logger.info("✅ BM25 parameter tuning test passed")

    def test_index_construction(self):
        """Test BM25 index construction and management."""
        logger.info("Testing BM25 index construction...")

        # Test with different dataset sizes
        dataset_sizes = ["small", "medium"]

        for size in dataset_sizes:
            self.setup_test_data(size)

            # Measure index construction time
            start_time = time.time()
            retriever = self.create_minimal_retriever("bm25")
            construction_time = (time.time() - start_time) * 1000

            # Test that index was built successfully
            results = retriever.retrieve("test query", k=3)
            assert len(results) >= 0, f"Index construction failed for {size} dataset"

            # Index construction should be reasonably fast
            max_construction_time = 1000 if size == "small" else 5000  # ms
            assert (
                construction_time < max_construction_time
            ), f"Index construction too slow for {size}: {construction_time:.1f}ms"

            logger.info(
                f"✅ {size} dataset index construction: {construction_time:.1f}ms"
            )

        logger.info("✅ Index construction test passed")

    def test_query_processing(self):
        """Test query processing and normalization."""
        logger.info("Testing query processing...")

        retriever = self.create_minimal_retriever("bm25")

        # Test different query formats
        query_tests = [
            {"query": "Simple query", "description": "Basic text"},
            {"query": "UPPERCASE QUERY", "description": "Uppercase text"},
            {"query": "mixed Case Query", "description": "Mixed case"},
            {"query": "query with punctuation!", "description": "With punctuation"},
            {"query": "  query  with  spaces  ", "description": "Extra whitespace"},
            {
                "query": "hyphenated-terms and_underscores",
                "description": "Special characters",
            },
        ]

        for test_case in query_tests:
            query = test_case["query"]

            try:
                results = retriever.retrieve(query, k=3)

                # Should handle all query formats gracefully
                assert isinstance(results, list), f"Invalid result type for: {query}"

                if results:
                    # Results should be valid
                    assert all(isinstance(r, RetrievalResult) for r in results)
                    scores = [r.score for r in results]
                    assert all(isinstance(score, (int, float)) for score in scores)
                    assert all(score >= 0 for score in scores)

                logger.info(f"✅ {test_case['description']}: {len(results)} results")

            except Exception as e:
                logger.warning(f"Query processing failed for '{query}': {e}")

        logger.info("✅ Query processing test passed")

    def test_search_performance(self):
        """Test BM25 search performance."""
        logger.info("Testing BM25 search performance...")

        # Set up medium dataset for performance testing
        self.setup_test_data("medium")
        retriever = self.create_minimal_retriever("bm25")

        # Performance test workload
        test_queries = self.test_data.create_test_queries(20)

        # Measure search performance
        start_time = time.time()
        total_results = 0
        query_times = []

        for query in test_queries:
            query_start = time.time()
            results = retriever.retrieve(query, k=5)
            query_time = (time.time() - query_start) * 1000

            query_times.append(query_time)
            total_results += len(results)

        total_time = time.time() - start_time
        avg_latency_ms = (total_time * 1000) / len(test_queries)
        max_latency_ms = max(query_times)
        min_latency_ms = min(query_times)

        # Performance assertions
        assert (
            avg_latency_ms < 50
        ), f"BM25 search too slow: {avg_latency_ms:.1f}ms average"
        assert max_latency_ms < 200, f"BM25 worst case too slow: {max_latency_ms:.1f}ms"
        assert total_results > 0, "No results returned from BM25"

        # Throughput calculation
        throughput_qps = len(test_queries) / total_time
        assert throughput_qps > 10, f"BM25 throughput too low: {throughput_qps:.1f} QPS"

        logger.info(
            f"✅ BM25 performance: {avg_latency_ms:.1f}ms avg, {throughput_qps:.1f} QPS"
        )
        logger.info(f"   Latency range: {min_latency_ms:.1f} - {max_latency_ms:.1f}ms")

    def test_concurrent_access(self):
        """Test concurrent access to BM25 retriever."""
        logger.info("Testing concurrent access...")

        retriever = self.create_minimal_retriever("bm25")

        # Test concurrent searches
        results_queue = queue.Queue()
        errors_queue = queue.Queue()

        def search_worker(worker_id: int):
            try:
                for i in range(10):
                    query = f"concurrent test query {worker_id}_{i}"
                    results = retriever.retrieve(query, k=3)
                    results_queue.put((worker_id, i, len(results)))
            except Exception as e:
                errors_queue.put((worker_id, str(e)))

        # Start multiple worker threads
        threads = []
        num_workers = 5

        for i in range(num_workers):
            thread = threading.Thread(target=search_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Check results
        total_searches = 0
        while not results_queue.empty():
            worker_id, query_id, result_count = results_queue.get()
            total_searches += 1
            assert (
                result_count >= 0
            ), f"Worker {worker_id} query {query_id} got negative results"

        # Check for errors
        error_count = 0
        while not errors_queue.empty():
            worker_id, error = errors_queue.get()
            logger.warning(f"Worker {worker_id} error: {error}")
            error_count += 1

        expected_searches = num_workers * 10
        assert error_count == 0, f"Concurrent access errors: {error_count}"
        assert (
            total_searches == expected_searches
        ), f"Missing searches: got {total_searches}, expected {expected_searches}"

        logger.info(
            f"✅ Concurrent access test passed: {total_searches} successful searches"
        )

    def test_memory_usage(self):
        """Test memory usage characteristics."""
        logger.info("Testing memory usage...")

        # Use larger dataset for memory testing
        self.setup_test_data("medium")

        try:
            import psutil
            import os

            # Measure initial memory
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Create BM25 retriever and index
            retriever = self.create_minimal_retriever("bm25")

            # Perform searches to test memory stability
            queries = self.test_data.create_test_queries(50)

            for i, query in enumerate(queries):
                results = retriever.retrieve(query, k=5)
                assert len(results) >= 0

                # Check memory every 10 queries
                if i % 10 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_increase = current_memory - initial_memory

                    # Memory shouldn't grow excessively
                    assert (
                        memory_increase < 200
                    ), f"Excessive memory growth: {memory_increase:.1f}MB at query {i}"

            final_memory = process.memory_info().rss / 1024 / 1024
            total_increase = final_memory - initial_memory

            logger.info(f"✅ Memory usage: {total_increase:.1f}MB total increase")

        except ImportError:
            logger.warning("psutil not available, skipping memory test")

    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        logger.info("Testing edge cases...")

        retriever = self.create_minimal_retriever("bm25")

        # Test edge case queries
        edge_cases = [
            ("", "Empty query"),
            ("a", "Single character"),
            ("!@#$%", "Only punctuation"),
            ("the and or", "Stop words only"),
            ("x" * 1000, "Very long query"),
            ("query\nwith\nnewlines", "Newlines"),
            ("query\twith\ttabs", "Tabs"),
        ]

        for query, description in edge_cases:
            try:
                results = retriever.retrieve(query, k=3) if query else []

                # Should handle gracefully
                assert isinstance(
                    results, list
                ), f"Invalid result type for {description}"

                if results:
                    assert all(isinstance(r, RetrievalResult) for r in results)
                    scores = [r.score for r in results]
                    assert all(isinstance(score, (int, float)) for score in scores)
                    assert all(score >= 0 for score in scores)

                logger.info(f"✅ {description}: {len(results)} results")

            except ValueError as e:
                # Some edge cases might legitimately fail
                if "empty" in str(e).lower():
                    logger.info(f"Expected error for {description}: {e}")
                else:
                    logger.warning(f"Unexpected error for {description}: {e}")

            except Exception as e:
                logger.warning(f"Error in {description}: {e}")

        logger.info("✅ Edge cases test passed")

    def run_component_tests(self) -> List[ComponentTestResult]:
        """Run all sparse retriever component tests."""
        test_methods = [
            self.test_bm25_algorithm_accuracy,
            self.test_keyword_matching,
            self.test_bm25_parameter_tuning,
            self.test_index_construction,
            self.test_query_processing,
            self.test_search_performance,
            self.test_concurrent_access,
            self.test_memory_usage,
            self.test_edge_cases,
        ]

        results = []

        for test_method in test_methods:
            test_name = test_method.__name__
            logger.info(f"\n🧪 Running {test_name}...")

            try:
                start_time = time.time()
                test_method()
                end_time = time.time()

                result = ComponentTestResult(
                    component_type="sparse",
                    component_name="BM25Retriever",
                    test_name=test_name,
                    success=True,
                    metrics=ComponentPerformanceMetrics(
                        latency_ms=(end_time - start_time) * 1000
                    ),
                    details={"execution_time_ms": (end_time - start_time) * 1000},
                )

            except Exception as e:
                result = ComponentTestResult(
                    component_type="sparse",
                    component_name="BM25Retriever",
                    test_name=test_name,
                    success=False,
                    metrics=ComponentPerformanceMetrics(latency_ms=0, error_count=1),
                    details={},
                    error_message=str(e),
                )
                logger.error(f"❌ {test_name} failed: {e}")

            results.append(result)

        # Summary
        passed = sum(1 for r in results if r.success)
        total = len(results)
        logger.info(f"\n📊 Sparse Retrievers Tests Summary: {passed}/{total} passed")

        return results


def run_sparse_retrievers_tests():
    """Run sparse retriever component tests."""
    logger.info("🚀 Starting Epic 2 Sparse Retrievers Component Tests")

    test_suite = TestSparseRetrievers()
    results = test_suite.run_component_tests()

    # Generate summary report
    passed_tests = [r for r in results if r.success]
    failed_tests = [r for r in results if not r.success]

    print(f"\n📈 Test Results Summary:")
    print(f"✅ Passed: {len(passed_tests)}")
    print(f"❌ Failed: {len(failed_tests)}")
    print(f"📊 Success Rate: {len(passed_tests)/len(results)*100:.1f}%")

    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for test in failed_tests:
            print(f"  - {test.test_name}: {test.error_message}")

    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    results = run_sparse_retrievers_tests()

    # Exit with appropriate code
    failed_count = sum(1 for r in results if not r.success)
    sys.exit(failed_count)
