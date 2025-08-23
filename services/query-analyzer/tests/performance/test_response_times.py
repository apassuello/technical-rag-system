"""
Performance tests for response times.

Tests that the Query Analyzer Service meets performance targets
for various operations and load conditions.
"""

import pytest
import time
import statistics
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

from conftest import assert_processing_time


class TestSingleRequestPerformance:
    """Test performance of individual requests."""

    def test_analyze_response_time_simple(self, client, sample_queries, performance_targets):
        """Test analyze endpoint response time for simple queries."""
        query = sample_queries["simple"][0]
        payload = {"query": query}
        
        # Measure response time
        start_time = time.time()
        response = client.post("/api/v1/analyze", json=payload)
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate performance targets
        assert response_time < 1.0  # API should respond within 1 second
        assert_processing_time(data["processing_time"], performance_targets["max_response_time"])

    def test_analyze_response_time_medium(self, client, sample_queries, performance_targets):
        """Test analyze endpoint response time for medium queries."""
        query = sample_queries["medium"][0]
        payload = {"query": query}
        
        start_time = time.time()
        response = client.post("/api/v1/analyze", json=payload)
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        assert response_time < 1.0
        assert_processing_time(data["processing_time"], performance_targets["max_response_time"])

    def test_analyze_response_time_complex(self, client, sample_queries, performance_targets):
        """Test analyze endpoint response time for complex queries."""
        query = sample_queries["complex"][0]
        payload = {"query": query}
        
        start_time = time.time()
        response = client.post("/api/v1/analyze", json=payload)
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        # Complex queries may take slightly longer but should still be fast
        assert response_time < 2.0
        assert_processing_time(data["processing_time"], performance_targets["max_response_time"])

    def test_status_response_time(self, client):
        """Test status endpoint response time."""
        start_time = time.time()
        response = client.get("/api/v1/status")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 0.5  # Status should be very fast

    def test_components_response_time(self, client):
        """Test components endpoint response time."""
        start_time = time.time()
        response = client.get("/api/v1/components")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 0.5  # Components info should be fast

    def test_health_response_time(self, client):
        """Test health endpoint response time."""
        start_time = time.time()
        response = client.get("/health")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 0.5  # Health check should be fast

    def test_liveness_response_time(self, client):
        """Test liveness probe response time."""
        start_time = time.time()
        response = client.get("/health/live")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 0.1  # Liveness should be very fast

    def test_readiness_response_time(self, client):
        """Test readiness probe response time."""
        start_time = time.time()
        response = client.get("/health/ready")
        response_time = time.time() - start_time
        
        assert response.status_code in [200, 503]
        assert response_time < 0.5  # Readiness should be fast


class TestConsistentPerformance:
    """Test performance consistency across multiple requests."""

    def test_analyze_performance_consistency(self, client, sample_queries, performance_targets):
        """Test that analyze performance is consistent across multiple requests."""
        query = sample_queries["medium"][0]
        payload = {"query": query}
        
        response_times = []
        processing_times = []
        
        # Make multiple requests
        for _ in range(10):
            start_time = time.time()
            response = client.post("/api/v1/analyze", json=payload)
            response_time = time.time() - start_time
            
            assert response.status_code == 200
            data = response.json()
            
            response_times.append(response_time)
            processing_times.append(data["processing_time"])
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        std_response_time = statistics.stdev(response_times)
        
        avg_processing_time = statistics.mean(processing_times)
        max_processing_time = max(processing_times)
        std_processing_time = statistics.stdev(processing_times)
        
        # Performance should be consistent
        assert avg_response_time < 1.0
        assert max_response_time < 2.0
        assert std_response_time < 0.5  # Low variance
        
        assert avg_processing_time < performance_targets["max_response_time"]
        assert max_processing_time < performance_targets["max_response_time"] * 2
        assert std_processing_time < performance_targets["max_response_time"]

    def test_sequential_request_performance(self, client, sample_queries):
        """Test performance degradation over sequential requests."""
        queries = sample_queries["simple"] + sample_queries["medium"]
        
        response_times = []
        
        # Make sequential requests
        for query in queries:
            payload = {"query": query}
            
            start_time = time.time()
            response = client.post("/api/v1/analyze", json=payload)
            response_time = time.time() - start_time
            
            assert response.status_code == 200
            response_times.append(response_time)
        
        # Performance should not degrade significantly over time
        first_half = response_times[:len(response_times)//2]
        second_half = response_times[len(response_times)//2:]
        
        avg_first = statistics.mean(first_half)
        avg_second = statistics.mean(second_half)
        
        # Second half should not be significantly slower (allow 50% degradation max)
        assert avg_second < avg_first * 1.5

    def test_mixed_endpoint_performance(self, client, sample_queries):
        """Test performance when mixing different endpoint types."""
        operations = [
            ("analyze", lambda: client.post("/api/v1/analyze", json={"query": sample_queries["simple"][0]})),
            ("status", lambda: client.get("/api/v1/status")),
            ("components", lambda: client.get("/api/v1/components")),
            ("health", lambda: client.get("/health")),
        ]
        
        results = {}
        
        # Mix different operations
        for _ in range(20):  # Total 80 requests
            for op_name, op_func in operations:
                start_time = time.time()
                response = op_func()
                response_time = time.time() - start_time
                
                assert response.status_code in [200, 503]
                
                if op_name not in results:
                    results[op_name] = []
                results[op_name].append(response_time)
        
        # Each operation type should maintain good performance
        for op_name, times in results.items():
            avg_time = statistics.mean(times)
            max_time = max(times)
            
            if op_name == "analyze":
                assert avg_time < 1.0
                assert max_time < 2.0
            else:
                assert avg_time < 0.5
                assert max_time < 1.0


class TestBatchPerformance:
    """Test performance of batch operations."""

    def test_batch_analyze_performance(self, client, sample_queries):
        """Test batch analyze performance."""
        queries = sample_queries["simple"][:5]  # Small batch
        
        start_time = time.time()
        response = client.post("/api/v1/batch-analyze", json=queries)
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        # Batch should be efficient
        assert response_time < 5.0  # Should complete within 5 seconds
        assert data["processing_time"] > 0
        
        # Should be more efficient than individual requests
        # (This is a rough estimate - actual efficiency depends on implementation)
        estimated_individual_time = len(queries) * 0.5  # Assuming 0.5s per query
        efficiency_ratio = response_time / estimated_individual_time
        assert efficiency_ratio < 1.5  # Batch should not be much slower

    def test_batch_analyze_scaling(self, client, sample_queries):
        """Test batch analyze performance scaling."""
        batch_sizes = [1, 5, 10, 20]
        results = {}
        
        for batch_size in batch_sizes:
            queries = (sample_queries["simple"] * ((batch_size // 4) + 1))[:batch_size]
            
            start_time = time.time()
            response = client.post("/api/v1/batch-analyze", json=queries)
            response_time = time.time() - start_time
            
            assert response.status_code == 200
            results[batch_size] = response_time
        
        # Performance should scale reasonably (not exponentially)
        for i in range(1, len(batch_sizes)):
            current_size = batch_sizes[i]
            prev_size = batch_sizes[i-1]
            
            size_ratio = current_size / prev_size
            time_ratio = results[current_size] / results[prev_size]
            
            # Time should not grow much faster than size
            assert time_ratio < size_ratio * 2

    def test_concurrent_batch_performance(self, client, sample_queries):
        """Test performance of concurrent batch requests."""
        queries = sample_queries["simple"][:3]  # Small batches
        
        def make_batch_request():
            start_time = time.time()
            response = client.post("/api/v1/batch-analyze", json=queries)
            response_time = time.time() - start_time
            return response.status_code, response_time
        
        # Make concurrent batch requests
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_batch_request) for _ in range(3)]
            results = [future.result() for future in as_completed(futures)]
        
        # All should succeed
        status_codes = [result[0] for result in results]
        response_times = [result[1] for result in results]
        
        assert all(status == 200 for status in status_codes)
        
        # Concurrent performance should be reasonable
        max_time = max(response_times)
        avg_time = statistics.mean(response_times)
        
        assert max_time < 10.0  # Should not take too long even under concurrency
        assert avg_time < 5.0


class TestColdStartPerformance:
    """Test cold start and warm-up performance."""

    @pytest.mark.asyncio
    async def test_first_request_performance(self, analyzer_service, sample_queries, performance_targets):
        """Test performance of first request (cold start)."""
        query = sample_queries["simple"][0]
        
        # Create a new service instance to simulate cold start
        from analyzer_app.core.analyzer import QueryAnalyzerService
        from unittest.mock import patch
        
        with patch('app.core.analyzer.Epic1QueryAnalyzer') as mock_epic1:
            mock_analyzer = analyzer_service.analyzer  # Use existing mock
            mock_epic1.return_value = mock_analyzer
            
            fresh_service = QueryAnalyzerService(config={})
            
            # First request (cold start)
            start_time = time.time()
            result = await fresh_service.analyze_query(query)
            cold_start_time = time.time() - start_time
            
            # Second request (warm)
            start_time = time.time()
            result = await fresh_service.analyze_query(query)
            warm_time = time.time() - start_time
            
            # Cold start may be slower, but should still meet reasonable targets
            assert cold_start_time < 5.0  # Cold start should complete within 5 seconds
            assert warm_time < performance_targets["max_response_time"] * 2
            
            # Warm requests should be faster than cold start
            assert warm_time <= cold_start_time

    def test_service_warmup_pattern(self, client, sample_queries):
        """Test service warm-up pattern."""
        query = sample_queries["simple"][0]
        payload = {"query": query}
        
        response_times = []
        
        # Make several requests to warm up the service
        for i in range(10):
            start_time = time.time()
            response = client.post("/api/v1/analyze", json=payload)
            response_time = time.time() - start_time
            
            assert response.status_code == 200
            response_times.append(response_time)
        
        # Performance should stabilize after warm-up
        early_times = response_times[:3]  # First 3 requests
        late_times = response_times[-3:]  # Last 3 requests
        
        avg_early = statistics.mean(early_times)
        avg_late = statistics.mean(late_times)
        
        # Later requests should not be significantly slower
        # (They might be faster due to caching, but shouldn't be much slower)
        assert avg_late <= avg_early * 1.5


class TestResourceUsagePerformance:
    """Test performance under different resource usage patterns."""

    def test_memory_efficient_processing(self, client, sample_queries):
        """Test that processing remains efficient under memory pressure."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Process many queries to test memory efficiency
        queries = (sample_queries["simple"] + sample_queries["medium"]) * 5
        
        response_times = []
        
        for query in queries:
            payload = {"query": query}
            
            start_time = time.time()
            response = client.post("/api/v1/analyze", json=payload)
            response_time = time.time() - start_time
            
            assert response.status_code == 200
            response_times.append(response_time)
        
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable
        assert memory_growth < 50 * 1024 * 1024  # Less than 50MB growth
        
        # Performance should remain consistent
        early_times = response_times[:5]
        late_times = response_times[-5:]
        
        avg_early = statistics.mean(early_times)
        avg_late = statistics.mean(late_times)
        
        # Performance should not degrade significantly with memory usage
        assert avg_late < avg_early * 2.0

    def test_cpu_efficient_processing(self, client, sample_queries):
        """Test CPU efficiency during processing."""
        import psutil
        import threading
        
        # Monitor CPU usage during processing
        cpu_usage = []
        monitoring = True
        
        def monitor_cpu():
            while monitoring:
                cpu_usage.append(psutil.cpu_percent(interval=0.1))
                time.sleep(0.1)
        
        # Start CPU monitoring
        monitor_thread = threading.Thread(target=monitor_cpu)
        monitor_thread.start()
        
        try:
            # Process queries under CPU monitoring
            queries = sample_queries["medium"][:5]
            
            for query in queries:
                payload = {"query": query}
                response = client.post("/api/v1/analyze", json=payload)
                assert response.status_code == 200
                
        finally:
            monitoring = False
            monitor_thread.join()
        
        if cpu_usage:
            avg_cpu = statistics.mean(cpu_usage)
            max_cpu = max(cpu_usage)
            
            # CPU usage should be reasonable (not pegging the system)
            assert avg_cpu < 80.0  # Average CPU should be reasonable
            assert max_cpu < 95.0  # Should not completely saturate CPU


class TestPerformanceRegression:
    """Test for performance regressions."""

    def test_performance_baseline(self, client, sample_queries, performance_targets):
        """Establish performance baseline for regression testing."""
        test_cases = [
            ("simple_query", sample_queries["simple"][0]),
            ("medium_query", sample_queries["medium"][0]),
            ("complex_query", sample_queries["complex"][0]),
        ]
        
        results = {}
        
        for test_name, query in test_cases:
            payload = {"query": query}
            times = []
            
            # Run multiple iterations
            for _ in range(5):
                start_time = time.time()
                response = client.post("/api/v1/analyze", json=payload)
                response_time = time.time() - start_time
                
                assert response.status_code == 200
                data = response.json()
                times.append({
                    "api_time": response_time,
                    "processing_time": data["processing_time"]
                })
            
            results[test_name] = {
                "avg_api_time": statistics.mean([t["api_time"] for t in times]),
                "avg_processing_time": statistics.mean([t["processing_time"] for t in times]),
                "max_api_time": max([t["api_time"] for t in times]),
                "max_processing_time": max([t["processing_time"] for t in times]),
            }
        
        # Assert baseline performance targets
        for test_name, metrics in results.items():
            assert metrics["avg_api_time"] < 1.0
            assert metrics["max_api_time"] < 2.0
            assert metrics["avg_processing_time"] < performance_targets["max_response_time"]
            assert metrics["max_processing_time"] < performance_targets["max_response_time"] * 2
        
        # Store results for future regression testing
        # In a real scenario, these would be stored in a performance tracking system
        print(f"\nPerformance Baseline Results:")
        for test_name, metrics in results.items():
            print(f"  {test_name}:")
            print(f"    API Time: {metrics['avg_api_time']:.3f}s avg, {metrics['max_api_time']:.3f}s max")
            print(f"    Processing Time: {metrics['avg_processing_time']:.3f}s avg, {metrics['max_processing_time']:.3f}s max")

    def test_performance_percentiles(self, client, sample_queries, performance_targets):
        """Test performance percentiles."""
        query = sample_queries["medium"][0]
        payload = {"query": query}
        
        response_times = []
        processing_times = []
        
        # Collect data from many requests
        for _ in range(50):
            start_time = time.time()
            response = client.post("/api/v1/analyze", json=payload)
            response_time = time.time() - start_time
            
            assert response.status_code == 200
            data = response.json()
            
            response_times.append(response_time)
            processing_times.append(data["processing_time"])
        
        # Calculate percentiles
        def percentile(data, p):
            sorted_data = sorted(data)
            index = (len(sorted_data) - 1) * p / 100.0
            lower = int(index)
            upper = lower + 1
            weight = index - lower
            if upper >= len(sorted_data):
                return sorted_data[-1]
            return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight
        
        p50_response = percentile(response_times, 50)
        p90_response = percentile(response_times, 90)
        p95_response = percentile(response_times, 95)
        p99_response = percentile(response_times, 99)
        
        p50_processing = percentile(processing_times, 50)
        p90_processing = percentile(processing_times, 90)
        p95_processing = percentile(processing_times, 95)
        p99_processing = percentile(processing_times, 99)
        
        # Assert percentile targets
        assert p50_response < 0.5    # 50% of requests under 0.5s
        assert p90_response < 1.0    # 90% of requests under 1s
        assert p95_response < 2.0    # 95% of requests under 2s
        assert p99_response < 5.0    # 99% of requests under 5s
        
        assert p50_processing < performance_targets["max_response_time"] / 2
        assert p90_processing < performance_targets["max_response_time"]
        assert p95_processing < performance_targets["max_response_time"] * 2
        assert p99_processing < performance_targets["max_response_time"] * 4
        
        print(f"\nPerformance Percentiles:")
        print(f"  API Response Time: P50={p50_response:.3f}s, P90={p90_response:.3f}s, P95={p95_response:.3f}s, P99={p99_response:.3f}s")
        print(f"  Processing Time: P50={p50_processing:.3f}s, P90={p90_processing:.3f}s, P95={p95_processing:.3f}s, P99={p99_processing:.3f}s")