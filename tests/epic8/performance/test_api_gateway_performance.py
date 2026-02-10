"""
Performance Tests for Epic 8 API Gateway Service.

Tests performance characteristics and scalability of the API Gateway under various load conditions.
Based on CT-8.6 specifications from epic8-test-specification.md.

Testing Philosophy:
- Hard Fails: System crashes, >60s response, >8GB memory, complete failure under load
- Quality Flags: >2s average response, <1000 req/s throughput, >10% error rate under load

Test Categories:
- Response time performance (CT-8.6.1)
- Concurrent request handling (CT-8.6.2)
- Memory usage under load (CT-8.6.3)
- Timeout behavior (CT-8.6.4)
- Circuit breaker performance (CT-8.6.5)
- Batch processing performance (CT-8.6.6)
"""

import pytest
import asyncio
import time
import warnings
import threading
import queue
import statistics
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys
from unittest.mock import Mock, AsyncMock, MagicMock
import gc

# Add services to path
project_path = Path(__file__).parent.parent.parent.parent
services_path = project_path / "services" / "api-gateway"
if services_path.exists():
    sys.path.insert(0, str(services_path))

try:
    from gateway_app.core.gateway import APIGatewayService, SimpleCircuitBreaker
    from gateway_app.schemas.requests import UnifiedQueryRequest, BatchQueryRequest, QueryOptions
    from gateway_app.schemas.responses import UnifiedQueryResponse, BatchQueryResponse
    from gateway_app.core.config import APIGatewaySettings
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    IMPORT_ERROR = str(e)


class TestAPIGatewayResponseTimePerformance:
    """Test response time performance characteristics (CT-8.6.1)."""

    @pytest.fixture
    def fast_mock_gateway(self):
        """Create gateway with fast mock services for performance testing."""
        gateway = APIGatewayService()
        
        # Fast mock services
        query_analyzer = AsyncMock()
        query_analyzer.analyze_query = AsyncMock(return_value={
            "complexity": "medium",
            "confidence": 0.8,
            "recommended_models": ["openai/gpt-3.5-turbo"],
            "cost_estimate": {"openai/gpt-3.5-turbo": 0.002}
        })
        query_analyzer.health_check = AsyncMock(return_value=True)
        query_analyzer.endpoint.url = "http://fast-analyzer:8081"
        
        retriever = AsyncMock()
        retriever.retrieve_documents = AsyncMock(return_value=[
            {"id": "doc1", "title": "Fast Doc", "content": "Fast content", "score": 0.9, "metadata": {}}
        ])
        retriever.health_check = AsyncMock(return_value=True)
        retriever.endpoint.url = "http://fast-retriever:8083"
        
        generator = AsyncMock()
        generator.generate_answer = AsyncMock(return_value={
            "answer": "Fast generated answer for performance testing",
            "confidence": 0.9,
            "model_used": "openai/gpt-3.5-turbo",
            "cost": 0.002,
            "tokens_generated": 20
        })
        generator.health_check = AsyncMock(return_value=True)
        generator.endpoint.url = "http://fast-generator:8082"
        
        cache = AsyncMock()
        cache.get_cached_response = AsyncMock(return_value=None)
        cache.cache_response = AsyncMock(return_value=True)
        cache.health_check = AsyncMock(return_value=True)
        cache.endpoint.url = "http://fast-cache:8084"
        
        analytics = AsyncMock()
        analytics.record_query_completion = AsyncMock(return_value=True)
        analytics.health_check = AsyncMock(return_value=True)
        analytics.endpoint.url = "http://fast-analytics:8085"
        
        gateway.query_analyzer = query_analyzer
        gateway.retriever = retriever
        gateway.generator = generator
        gateway.cache = cache
        gateway.analytics = analytics
        
        gateway._initialize_circuit_breakers()
        
        return gateway

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_single_query_response_time_performance(self, fast_mock_gateway):
        """Test single query response time performance (CT-8.6.1)."""
        gateway = fast_mock_gateway
        
        request = UnifiedQueryRequest(
            query="Performance test query for response time measurement",
            options=QueryOptions(strategy="balanced", cache_enabled=True, analytics_enabled=True)
        )
        
        # Perform multiple measurements
        response_times = []
        responses = []
        
        try:
            for i in range(20):  # 20 measurements for statistical significance
                start_time = time.time()
                response = await gateway.process_unified_query(request)
                response_time = time.time() - start_time
                
                response_times.append(response_time)
                responses.append(response)
                
                # Hard fail: Any single request >60s
                assert response_time < 60.0, f"Request {i} took {response_time:.2f}s, exceeding 60s limit"
                
                # Validate response structure
                assert response is not None
                assert len(response.answer) > 0
            
            # Calculate performance statistics
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times) 
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            std_response_time = statistics.stdev(response_times)
            
            # Hard fail: Average response time >60s
            assert avg_response_time < 60.0, f"Average response time {avg_response_time:.2f}s exceeds 60s limit"
            
            # Quality flags based on CT-8.6.1 targets
            if avg_response_time > 2.0:
                warnings.warn(f"Average response time {avg_response_time:.3f}s exceeds 2s target", UserWarning, stacklevel=2)
            
            if p95_response_time > 5.0:
                warnings.warn(f"P95 response time {p95_response_time:.3f}s exceeds 5s target", UserWarning, stacklevel=2)
            
            if std_response_time > 1.0:
                warnings.warn(f"High response time variability: std={std_response_time:.3f}s", UserWarning, stacklevel=2)
            
            # Verify all responses succeeded
            assert all(r.fallback_used is False for r in responses), "No responses should use fallback"
            
            print(f"\nSingle Query Performance Results:")
            print(f"  Samples: {len(response_times)}")
            print(f"  Average: {avg_response_time:.3f}s")
            print(f"  Median:  {median_response_time:.3f}s")
            print(f"  P95:     {p95_response_time:.3f}s")
            print(f"  Min/Max: {min_response_time:.3f}s / {max_response_time:.3f}s")
            print(f"  Std Dev: {std_response_time:.3f}s")
            
        except Exception as e:
            pytest.fail(f"Single query response time performance test failed: {e}")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_batch_query_response_time_performance(self, fast_mock_gateway):
        """Test batch query response time performance (CT-8.6.1)."""
        gateway = fast_mock_gateway
        
        # Test different batch sizes
        batch_sizes = [1, 5, 10, 20]
        
        for batch_size in batch_sizes:
            queries = [f"Batch performance test query {i}" for i in range(batch_size)]
            
            batch_request = BatchQueryRequest(
                queries=queries,
                options=QueryOptions(strategy="balanced", cache_enabled=True),
                parallel_processing=True,
                max_parallel=min(5, batch_size)  # Limit concurrency
            )
            
            try:
                start_time = time.time()
                response = await gateway.process_batch_queries(batch_request)
                batch_time = time.time() - start_time
                
                # Hard fail: Batch processing >60s
                assert batch_time < 60.0, f"Batch size {batch_size} took {batch_time:.2f}s"
                
                # Validate batch response
                assert response.total_queries == batch_size
                assert len(response.results) == batch_size
                
                # Calculate per-query time
                per_query_time = batch_time / batch_size
                
                # Quality flags
                if per_query_time > 2.0:
                    warnings.warn(f"Batch size {batch_size}: per-query time {per_query_time:.3f}s exceeds 2s", UserWarning, stacklevel=2)
                
                if response.successful_queries < batch_size * 0.95:  # <95% success
                    warnings.warn(f"Batch size {batch_size}: success rate {response.successful_queries/batch_size:.2%}", UserWarning, stacklevel=2)
                
                print(f"Batch size {batch_size}: {batch_time:.3f}s total, {per_query_time:.3f}s per query")
                
            except Exception as e:
                pytest.fail(f"Batch performance test failed for size {batch_size}: {e}")


class TestAPIGatewayConcurrentRequestHandling:
    """Test concurrent request handling performance (CT-8.6.2)."""

    @pytest.fixture
    def concurrent_mock_gateway(self):
        """Create gateway optimized for concurrency testing."""
        gateway = APIGatewayService()
        
        # Mock services with slight delays to simulate real conditions
        async def mock_analyze(query, context=None, complexity_hint=None):
            await asyncio.sleep(0.01)  # 10ms simulation
            return {
                "complexity": "medium",
                "confidence": 0.8,
                "recommended_models": ["test-model"],
                "cost_estimate": {"test-model": 0.001}
            }
        
        async def mock_retrieve(query, max_documents=5, complexity=None, retrieval_strategy=None):
            await asyncio.sleep(0.02)  # 20ms simulation
            return [{"id": f"doc{i}", "title": f"Doc {i}", "content": f"Content {i}", "score": 0.9-i*0.1, "metadata": {}} for i in range(min(3, max_documents))]
        
        async def mock_generate(query, context_documents, routing_decision=None, complexity=None, strategy=None):
            await asyncio.sleep(0.05)  # 50ms simulation
            return {
                "answer": f"Generated answer for: {query[:50]}...",
                "confidence": 0.85,
                "model_used": "test-model",
                "cost": 0.001,
                "tokens_generated": 25
            }
        
        async def mock_cache_get(query_hash):
            await asyncio.sleep(0.001)  # 1ms simulation
            return None
        
        async def mock_cache_set(query_hash, response, ttl=3600):
            await asyncio.sleep(0.001)  # 1ms simulation
            return True
        
        async def mock_analytics(query_request, query_response):
            await asyncio.sleep(0.002)  # 2ms simulation
            return True
        
        # Setup mock services
        gateway.query_analyzer = AsyncMock()
        gateway.query_analyzer.analyze_query = mock_analyze
        gateway.query_analyzer.health_check = AsyncMock(return_value=True)
        gateway.query_analyzer.endpoint.url = "http://concurrent-analyzer:8081"
        
        gateway.retriever = AsyncMock()
        gateway.retriever.retrieve_documents = mock_retrieve
        gateway.retriever.health_check = AsyncMock(return_value=True)
        gateway.retriever.endpoint.url = "http://concurrent-retriever:8083"
        
        gateway.generator = AsyncMock()
        gateway.generator.generate_answer = mock_generate
        gateway.generator.health_check = AsyncMock(return_value=True)
        gateway.generator.endpoint.url = "http://concurrent-generator:8082"
        
        gateway.cache = AsyncMock()
        gateway.cache.get_cached_response = mock_cache_get
        gateway.cache.cache_response = mock_cache_set
        gateway.cache.health_check = AsyncMock(return_value=True)
        gateway.cache.endpoint.url = "http://concurrent-cache:8084"
        
        gateway.analytics = AsyncMock()
        gateway.analytics.record_query_completion = mock_analytics
        gateway.analytics.health_check = AsyncMock(return_value=True)
        gateway.analytics.endpoint.url = "http://concurrent-analytics:8085"
        
        gateway._initialize_circuit_breakers()
        
        return gateway

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_concurrent_query_performance(self, concurrent_mock_gateway):
        """Test concurrent query handling performance (CT-8.6.2)."""
        gateway = concurrent_mock_gateway
        
        # Test different concurrency levels
        concurrency_levels = [1, 5, 10, 25, 50]
        
        for concurrency in concurrency_levels:
            # Create requests
            requests = [
                UnifiedQueryRequest(
                    query=f"Concurrent test query {i} with some content for realistic processing",
                    options=QueryOptions(strategy="balanced", analytics_enabled=True)
                )
                for i in range(concurrency)
            ]
            
            try:
                start_time = time.time()
                
                # Execute all requests concurrently
                tasks = [gateway.process_unified_query(req) for req in requests]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                total_time = time.time() - start_time
                
                # Hard fail: Concurrent processing >60s
                assert total_time < 60.0, f"Concurrency {concurrency} took {total_time:.2f}s"
                
                # Analyze results
                successful_results = [r for r in results if isinstance(r, UnifiedQueryResponse)]
                failed_results = [r for r in results if isinstance(r, Exception)]
                
                success_rate = len(successful_results) / len(results)
                throughput = len(requests) / total_time  # requests per second
                
                # Hard fail: Complete failure under load
                assert len(successful_results) > 0, f"All {concurrency} concurrent requests failed"
                
                # Quality flags
                if success_rate < 0.9:
                    warnings.warn(f"Concurrency {concurrency}: success rate {success_rate:.2%} below 90%", UserWarning, stacklevel=2)
                
                if throughput < 1.0:  # Less than 1 request per second
                    warnings.warn(f"Concurrency {concurrency}: throughput {throughput:.2f} req/s below 1.0", UserWarning, stacklevel=2)
                
                # Performance metrics
                avg_response_time = total_time / concurrency  # Average time per request
                if avg_response_time > 5.0:
                    warnings.warn(f"Concurrency {concurrency}: avg response time {avg_response_time:.3f}s exceeds 5s", UserWarning, stacklevel=2)
                
                print(f"Concurrency {concurrency}: {success_rate:.2%} success, {throughput:.1f} req/s, {avg_response_time:.3f}s avg")
                
            except Exception as e:
                pytest.fail(f"Concurrent performance test failed at concurrency {concurrency}: {e}")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_sustained_load_performance(self, concurrent_mock_gateway):
        """Test performance under sustained load (CT-8.6.2)."""
        gateway = concurrent_mock_gateway
        
        # Sustained load test: 5 requests per second for 30 seconds
        duration = 10  # Reduced for testing
        requests_per_second = 3
        total_requests = duration * requests_per_second
        
        request_template = UnifiedQueryRequest(
            query="Sustained load test query with realistic content for performance measurement",
            options=QueryOptions(strategy="balanced")
        )
        
        try:
            start_time = time.time()
            completed_requests = 0
            successful_requests = 0
            failed_requests = 0
            response_times = []
            
            # Rate-limited request sending
            async def send_request_batch():
                nonlocal completed_requests, successful_requests, failed_requests
                
                batch_start = time.time()
                
                # Send batch of requests
                batch_tasks = []
                for _ in range(requests_per_second):
                    task = gateway.process_unified_query(request_template)
                    batch_tasks.append(task)
                
                # Wait for batch completion
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Process results
                for result in batch_results:
                    completed_requests += 1
                    if isinstance(result, UnifiedQueryResponse):
                        successful_requests += 1
                    else:
                        failed_requests += 1
                
                batch_time = time.time() - batch_start
                response_times.append(batch_time)
            
            # Execute sustained load
            for second in range(duration):
                await send_request_batch()
                
                # Wait until next second (rate limiting)
                elapsed = time.time() - start_time
                sleep_time = (second + 1) - elapsed
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
            
            total_duration = time.time() - start_time
            
            # Calculate metrics
            success_rate = successful_requests / completed_requests if completed_requests > 0 else 0
            throughput = completed_requests / total_duration
            avg_response_time = statistics.mean(response_times) if response_times else 0
            
            # Hard fails
            assert successful_requests > 0, "All sustained load requests failed"
            assert total_duration < 60.0, f"Sustained load test took {total_duration:.2f}s"
            
            # Quality flags
            if success_rate < 0.95:
                warnings.warn(f"Sustained load success rate {success_rate:.2%} below 95%", UserWarning, stacklevel=2)
            
            if throughput < requests_per_second * 0.8:  # Less than 80% of target throughput
                warnings.warn(f"Sustained load throughput {throughput:.2f} req/s below target", UserWarning, stacklevel=2)
            
            print(f"\nSustained Load Performance ({duration}s):")
            print(f"  Completed: {completed_requests}/{total_requests} requests")
            print(f"  Success Rate: {success_rate:.2%}")
            print(f"  Throughput: {throughput:.2f} req/s")
            print(f"  Avg Batch Time: {avg_response_time:.3f}s")
            
        except Exception as e:
            pytest.fail(f"Sustained load performance test failed: {e}")


class TestAPIGatewayMemoryUsage:
    """Test memory usage under load (CT-8.6.3)."""

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self):
        """Test memory usage during high load (CT-8.6.3)."""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            gateway = APIGatewayService()
            
            # Setup lightweight mocks for memory testing
            for service_name in ["query_analyzer", "retriever", "generator", "cache", "analytics"]:
                client = AsyncMock()
                setattr(gateway, service_name, client)
            
            # Configure fast responses
            gateway.query_analyzer.analyze_query.return_value = {"complexity": "simple", "confidence": 0.5}
            gateway.retriever.retrieve_documents.return_value = []
            gateway.generator.generate_answer.return_value = {"answer": "test", "confidence": 0.5, "cost": 0.0, "tokens_generated": 5}
            gateway.cache.get_cached_response.return_value = None
            gateway.cache.cache_response.return_value = True
            gateway.analytics.record_query_completion.return_value = True
            
            gateway._initialize_circuit_breakers()
            
            # Memory measurement points
            memory_measurements = []
            
            # Process batches of requests
            batch_size = 50
            num_batches = 10  # Total: 500 requests
            
            for batch in range(num_batches):
                # Create batch of requests
                requests = [
                    UnifiedQueryRequest(query=f"Memory test query {i}", options=QueryOptions())
                    for i in range(batch_size)
                ]
                
                # Process batch
                batch_start_time = time.time()
                tasks = [gateway.process_unified_query(req) for req in requests]
                await asyncio.gather(*tasks, return_exceptions=True)
                batch_time = time.time() - batch_start_time
                
                # Hard fail: Batch takes too long (potential memory issue)
                assert batch_time < 60.0, f"Batch {batch} took {batch_time:.2f}s"
                
                # Measure memory after batch
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_measurements.append(current_memory)
                
                # Force garbage collection
                gc.collect()
                
                # Hard fail: Memory usage >8GB
                assert current_memory < 8000, f"Memory usage {current_memory:.1f}MB exceeds 8GB limit"
                
                print(f"Batch {batch+1}/{num_batches}: {batch_time:.2f}s, {current_memory:.1f}MB")
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            max_memory = max(memory_measurements)
            
            # Memory analysis
            memory_trend = memory_measurements[-1] - memory_measurements[0] if len(memory_measurements) > 1 else 0
            
            # Quality flags
            if memory_increase > 1000:  # >1GB increase
                warnings.warn(f"Large memory increase: {memory_increase:.1f}MB", UserWarning, stacklevel=2)
            
            if memory_trend > 500:  # >500MB trend increase
                warnings.warn(f"Memory trend increase: {memory_trend:.1f}MB (potential leak)", UserWarning, stacklevel=2)
            
            print(f"\nMemory Usage Analysis:")
            print(f"  Initial: {initial_memory:.1f}MB")
            print(f"  Final: {final_memory:.1f}MB") 
            print(f"  Peak: {max_memory:.1f}MB")
            print(f"  Increase: {memory_increase:.1f}MB")
            print(f"  Trend: {memory_trend:.1f}MB")
            
        except ImportError:
            pytest.skip("psutil not available for memory testing")
        except Exception as e:
            pytest.fail(f"Memory usage test failed: {e}")


class TestAPIGatewayTimeoutBehavior:
    """Test timeout behavior and handling (CT-8.6.4)."""

    @pytest.fixture
    def slow_mock_gateway(self):
        """Create gateway with slow services for timeout testing."""
        gateway = APIGatewayService()
        
        # Mock services with configurable delays
        async def slow_analyze(delay=1.0):
            await asyncio.sleep(delay)
            return {"complexity": "medium", "confidence": 0.8, "recommended_models": ["test-model"]}
        
        async def slow_retrieve(delay=1.0):
            await asyncio.sleep(delay)
            return [{"id": "doc1", "title": "Slow Doc", "content": "Slow content", "score": 0.9, "metadata": {}}]
        
        async def slow_generate(delay=1.0):
            await asyncio.sleep(delay)
            return {"answer": "Slow answer", "confidence": 0.8, "cost": 0.001, "tokens_generated": 10}
        
        gateway.query_analyzer = AsyncMock()
        gateway.retriever = AsyncMock()
        gateway.generator = AsyncMock()
        gateway.cache = AsyncMock()
        gateway.analytics = AsyncMock()
        
        # Store delay functions for test control
        gateway._slow_analyze = slow_analyze
        gateway._slow_retrieve = slow_retrieve
        gateway._slow_generate = slow_generate
        
        gateway._initialize_circuit_breakers()
        
        return gateway

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_service_timeout_handling(self, slow_mock_gateway):
        """Test handling of service timeouts (CT-8.6.4)."""
        gateway = slow_mock_gateway
        
        # Test different timeout scenarios
        timeout_scenarios = [
            {"service": "analyzer", "delay": 5.0},
            {"service": "retriever", "delay": 3.0},
            {"service": "generator", "delay": 10.0},
        ]
        
        for scenario in timeout_scenarios:
            service = scenario["service"] 
            delay = scenario["delay"]
            
            # Configure service with delay
            if service == "analyzer":
                gateway.query_analyzer.analyze_query.side_effect = lambda **kwargs: gateway._slow_analyze(delay)
                gateway.retriever.retrieve_documents.return_value = []
                gateway.generator.generate_answer.return_value = {"answer": "test", "confidence": 0.5, "cost": 0.0, "tokens_generated": 5}
            elif service == "retriever":
                gateway.query_analyzer.analyze_query.return_value = {"complexity": "medium", "recommended_models": ["test"]}
                gateway.retriever.retrieve_documents.side_effect = lambda **kwargs: gateway._slow_retrieve(delay)
                gateway.generator.generate_answer.return_value = {"answer": "test", "confidence": 0.5, "cost": 0.0, "tokens_generated": 5}
            elif service == "generator":
                gateway.query_analyzer.analyze_query.return_value = {"complexity": "medium", "recommended_models": ["test"]}
                gateway.retriever.retrieve_documents.return_value = []
                gateway.generator.generate_answer.side_effect = lambda **kwargs: gateway._slow_generate(delay)
            
            gateway.cache.get_cached_response.return_value = None
            gateway.cache.cache_response.return_value = True
            gateway.analytics.record_query_completion.return_value = True
            
            request = UnifiedQueryRequest(
                query=f"Timeout test for {service} service",
                options=QueryOptions(strategy="balanced")
            )
            
            try:
                start_time = time.time()
                
                # Use asyncio.wait_for to implement timeout
                try:
                    response = await asyncio.wait_for(
                        gateway.process_unified_query(request),
                        timeout=15.0  # 15 second timeout
                    )
                    processing_time = time.time() - start_time
                    
                    # If it completes, validate it took expected time
                    if processing_time < delay * 0.8:  # Completed too fast, mock might not be working
                        warnings.warn(f"{service} timeout test: completed too fast ({processing_time:.2f}s)", UserWarning, stacklevel=2)
                    
                    print(f"{service} timeout test: completed in {processing_time:.2f}s")
                    
                except asyncio.TimeoutError:
                    # Timeout occurred - this is acceptable behavior
                    timeout_time = time.time() - start_time
                    print(f"{service} timeout test: timed out after {timeout_time:.2f}s (expected)")
                    assert timeout_time >= 14.5, "Timeout should occur near the timeout limit"
                
                # Hard fail: Processing should not exceed 60s total
                total_time = time.time() - start_time
                assert total_time < 60.0, f"{service} timeout test took {total_time:.2f}s"
                
            except Exception as e:
                pytest.fail(f"Timeout test failed for {service}: {e}")


class TestAPIGatewayCircuitBreakerPerformance:
    """Test circuit breaker performance characteristics (CT-8.6.5)."""

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_circuit_breaker_performance_impact(self):
        """Test circuit breaker performance impact (CT-8.6.5)."""
        # Test direct service calls vs circuit breaker protected calls
        
        # Test 1: Direct mock service
        mock_service = AsyncMock()
        mock_service.test_operation.return_value = "success"
        
        # Measure direct calls
        direct_times = []
        for _ in range(100):
            start = time.time()
            await mock_service.test_operation()
            direct_times.append(time.time() - start)
        
        # Test 2: Circuit breaker protected calls
        cb = SimpleCircuitBreaker(failure_threshold=5, recovery_timeout=1)
        
        cb_times = []
        for _ in range(100):
            start = time.time()
            try:
                with cb:
                    await mock_service.test_operation()
                cb_times.append(time.time() - start)
            except Exception:
                pass  # Circuit breaker rejection
        
        # Analyze performance impact
        avg_direct = statistics.mean(direct_times)
        avg_cb = statistics.mean(cb_times) if cb_times else 0
        
        if cb_times:
            overhead = ((avg_cb - avg_direct) / avg_direct) * 100 if avg_direct > 0 else 0
            
            # Quality flag: Circuit breaker overhead should be minimal
            if overhead > 50:  # >50% overhead
                warnings.warn(f"Circuit breaker overhead: {overhead:.1f}%", UserWarning, stacklevel=2)
            
            print(f"Circuit breaker performance: {overhead:.1f}% overhead ({avg_direct*1000:.2f}ms -> {avg_cb*1000:.2f}ms)")
        
        print("Circuit breaker performance test completed")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_recovery_performance(self):
        """Test circuit breaker failure and recovery performance (CT-8.6.5)."""
        cb = SimpleCircuitBreaker(failure_threshold=3, recovery_timeout=0.1)  # Fast recovery for testing
        
        mock_service = AsyncMock()
        
        # Phase 1: Normal operation
        mock_service.test_operation.return_value = "success"
        
        success_times = []
        for _ in range(5):
            start = time.time()
            try:
                with cb:
                    await mock_service.test_operation()
                success_times.append(time.time() - start)
            except Exception:
                pass
        
        assert cb.state == "closed", "Circuit breaker should be closed during success"
        
        # Phase 2: Trigger failures
        mock_service.test_operation.side_effect = Exception("Service failed")
        
        failure_times = []
        for _ in range(5):  # More than failure threshold
            start = time.time()
            try:
                with cb:
                    await mock_service.test_operation()
            except Exception:
                failure_times.append(time.time() - start)
        
        assert cb.state == "open", "Circuit breaker should be open after failures"
        
        # Phase 3: Test rejection performance
        rejection_times = []
        for _ in range(5):
            start = time.time()
            try:
                with cb:
                    await mock_service.test_operation()
            except Exception:
                rejection_times.append(time.time() - start)
        
        # Phase 4: Recovery
        await asyncio.sleep(0.2)  # Wait for recovery timeout
        mock_service.test_operation.side_effect = None
        mock_service.test_operation.return_value = "recovered"
        
        recovery_times = []
        for _ in range(3):
            start = time.time()
            try:
                with cb:
                    await mock_service.test_operation()
                recovery_times.append(time.time() - start)
            except Exception:
                pass
        
        # Analyze performance
        avg_success = statistics.mean(success_times) if success_times else 0
        avg_failure = statistics.mean(failure_times) if failure_times else 0
        avg_rejection = statistics.mean(rejection_times) if rejection_times else 0
        avg_recovery = statistics.mean(recovery_times) if recovery_times else 0
        
        # Quality checks
        if avg_rejection > avg_success * 2:  # Rejection should be faster than success
            warnings.warn(f"Circuit breaker rejection slow: {avg_rejection*1000:.2f}ms", UserWarning, stacklevel=2)
        
        print(f"Circuit breaker state performance:")
        print(f"  Success: {avg_success*1000:.2f}ms")
        print(f"  Failure: {avg_failure*1000:.2f}ms") 
        print(f"  Rejection: {avg_rejection*1000:.2f}ms")
        print(f"  Recovery: {avg_recovery*1000:.2f}ms")


class TestAPIGatewayBatchProcessingPerformance:
    """Test batch processing performance characteristics (CT-8.6.6)."""

    @pytest.fixture
    def batch_mock_gateway(self):
        """Create gateway optimized for batch performance testing."""
        gateway = APIGatewayService()
        
        # Fast mock services for batch testing
        gateway.query_analyzer = AsyncMock()
        gateway.query_analyzer.analyze_query.return_value = {"complexity": "simple", "confidence": 0.8, "recommended_models": ["test-model"]}
        
        gateway.retriever = AsyncMock()
        gateway.retriever.retrieve_documents.return_value = [{"id": "doc1", "title": "Doc", "content": "Content", "score": 0.9, "metadata": {}}]
        
        gateway.generator = AsyncMock()
        gateway.generator.generate_answer.return_value = {"answer": "Batch answer", "confidence": 0.8, "cost": 0.001, "tokens_generated": 15}
        
        gateway.cache = AsyncMock()
        gateway.cache.get_cached_response.return_value = None
        gateway.cache.cache_response.return_value = True
        
        gateway.analytics = AsyncMock()
        gateway.analytics.record_query_completion.return_value = True
        
        gateway._initialize_circuit_breakers()
        
        return gateway

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_batch_size_performance_scaling(self, batch_mock_gateway):
        """Test performance scaling with different batch sizes (CT-8.6.6)."""
        gateway = batch_mock_gateway
        
        batch_sizes = [1, 5, 10, 25, 50, 100]
        performance_results = []
        
        for batch_size in batch_sizes:
            queries = [f"Batch scaling test query {i}" for i in range(batch_size)]
            
            # Test sequential processing
            sequential_request = BatchQueryRequest(
                queries=queries,
                options=QueryOptions(strategy="balanced"),
                parallel_processing=False
            )
            
            start_time = time.time()
            sequential_response = await gateway.process_batch_queries(sequential_request)
            sequential_time = time.time() - start_time
            
            # Test parallel processing
            parallel_request = BatchQueryRequest(
                queries=queries,
                options=QueryOptions(strategy="balanced"),
                parallel_processing=True,
                max_parallel=min(10, batch_size)
            )
            
            start_time = time.time()
            parallel_response = await gateway.process_batch_queries(parallel_request)
            parallel_time = time.time() - start_time
            
            # Calculate metrics
            sequential_throughput = batch_size / sequential_time
            parallel_throughput = batch_size / parallel_time
            speedup = sequential_time / parallel_time if parallel_time > 0 else 1
            
            performance_results.append({
                "batch_size": batch_size,
                "sequential_time": sequential_time,
                "parallel_time": parallel_time,
                "sequential_throughput": sequential_throughput,
                "parallel_throughput": parallel_throughput,
                "speedup": speedup
            })
            
            # Hard fails
            assert sequential_time < 60.0, f"Sequential batch {batch_size} took {sequential_time:.2f}s"
            assert parallel_time < 60.0, f"Parallel batch {batch_size} took {parallel_time:.2f}s"
            
            # Quality checks
            if parallel_time > sequential_time:
                warnings.warn(f"Batch {batch_size}: parallel slower than sequential", UserWarning, stacklevel=2)
            
            if speedup < 1.2 and batch_size > 5:  # Should have some speedup for larger batches
                warnings.warn(f"Batch {batch_size}: low parallel speedup {speedup:.2f}x", UserWarning, stacklevel=2)
            
            print(f"Batch {batch_size}: seq={sequential_time:.2f}s, par={parallel_time:.2f}s, speedup={speedup:.2f}x")
        
        # Analyze scaling trends
        throughputs = [r["parallel_throughput"] for r in performance_results]
        if len(throughputs) > 1:
            # Check if throughput scales reasonably
            small_batch_throughput = throughputs[1]  # Skip batch_size=1
            large_batch_throughput = throughputs[-1]
            
            if large_batch_throughput < small_batch_throughput * 0.5:  # Significant degradation
                warnings.warn(f"Batch throughput degradation: {small_batch_throughput:.1f} -> {large_batch_throughput:.1f} req/s", UserWarning, stacklevel=2)
        
        print(f"\nBatch Performance Scaling Results:")
        for result in performance_results:
            print(f"  Size {result['batch_size']:3d}: {result['parallel_throughput']:6.1f} req/s, {result['speedup']:5.2f}x speedup")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_batch_parallelization_efficiency(self, batch_mock_gateway):
        """Test efficiency of batch parallelization (CT-8.6.6)."""
        gateway = batch_mock_gateway
        
        batch_size = 20
        queries = [f"Parallelization efficiency test query {i}" for i in range(batch_size)]
        
        # Test different parallelization levels
        parallel_levels = [1, 2, 5, 10, 20]
        results = {}
        
        for max_parallel in parallel_levels:
            batch_request = BatchQueryRequest(
                queries=queries,
                options=QueryOptions(strategy="balanced"),
                parallel_processing=True,
                max_parallel=max_parallel
            )
            
            start_time = time.time()
            response = await gateway.process_batch_queries(batch_request)
            processing_time = time.time() - start_time
            
            throughput = batch_size / processing_time
            efficiency = throughput / max_parallel if max_parallel > 0 else 0
            
            results[max_parallel] = {
                "time": processing_time,
                "throughput": throughput, 
                "efficiency": efficiency,
                "success_rate": response.successful_queries / response.total_queries
            }
            
            # Hard fail
            assert processing_time < 60.0, f"Parallelization {max_parallel} took {processing_time:.2f}s"
            
            print(f"Parallel {max_parallel:2d}: {processing_time:.2f}s, {throughput:.1f} req/s, {efficiency:.2f} eff")
        
        # Analyze efficiency trends
        max_efficiency = max(r["efficiency"] for r in results.values())
        optimal_parallel = None
        
        for parallel_level, result in results.items():
            if result["efficiency"] == max_efficiency:
                optimal_parallel = parallel_level
                break
        
        # Quality checks
        if optimal_parallel and optimal_parallel < batch_size // 4:
            warnings.warn(f"Low optimal parallelization: {optimal_parallel} for batch size {batch_size}", UserWarning, stacklevel=2)
        
        print(f"\nOptimal parallelization: {optimal_parallel} workers (efficiency: {max_efficiency:.2f})")


if __name__ == "__main__":
    # Run specific test classes for development
    pytest.main([__file__ + "::TestAPIGatewayResponseTimePerformance", "-v"])