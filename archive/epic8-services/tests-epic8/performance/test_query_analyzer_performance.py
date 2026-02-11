"""
Performance Tests for Epic 8 Query Analyzer Service.

Tests performance characteristics, resource usage, and scalability of the
Query Analyzer Service according to PT-8.1 specifications from 
epic8-test-specification.md.

Testing Philosophy:
- Hard Fails: >60s response time, >8GB memory, complete crashes, 0% throughput
- Quality Flags: >2s response time, high memory usage, low throughput, resource leaks
"""

import pytest
import asyncio
import time
import warnings
import threading
import queue
from typing import List, Dict, Any
from pathlib import Path
import sys
import gc

# Resource monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Add services to path
project_path = Path(__file__).parent.parent.parent.parent
services_path = project_path / "services" / "query-analyzer"
if services_path.exists():
    sys.path.insert(0, str(services_path))

try:
    from analyzer_app.core.analyzer import QueryAnalyzerService
    SERVICE_IMPORTS_AVAILABLE = True
except ImportError as e:
    SERVICE_IMPORTS_AVAILABLE = False
    SERVICE_IMPORT_ERROR = str(e)


class TestQueryAnalyzerBasicPerformance:
    """Test basic performance characteristics."""

    @pytest.mark.skipif(not SERVICE_IMPORTS_AVAILABLE, reason=f"Service imports not available: {SERVICE_IMPORT_ERROR if not SERVICE_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_single_query_response_time(self):
        """Test response time for single queries (PT-8.1 baseline)."""
        service = QueryAnalyzerService()
        
        test_queries = [
            ("Simple query", "simple"),
            ("How does machine learning work in practice?", "medium"),
            ("Analyze the computational complexity of distributed algorithms", "complex")
        ]
        
        response_times = []
        
        try:
            for query, expected_complexity in test_queries:
                start_time = time.time()
                result = await service.analyze_query(query)
                response_time = time.time() - start_time
                
                response_times.append({
                    "query": query,
                    "complexity": result.get("complexity", "unknown"),
                    "expected": expected_complexity,
                    "response_time": response_time
                })
                
                # Hard fail: >60s response time (clearly broken)
                assert response_time < 60.0, f"Query took {response_time:.2f}s - service is broken"
                
                # Quality flag: >2s response time (suboptimal)
                if response_time > 2.0:
                    warnings.warn(f"Slow response for '{query[:50]}...': {response_time:.2f}s", UserWarning, stacklevel=2)
            
            # Calculate statistics
            times = [r["response_time"] for r in response_times]
            avg_time = sum(times) / len(times)
            max_time = max(times)
            min_time = min(times)
            
            print(f"\nSingle Query Performance Results:")
            print(f"  Average: {avg_time:.3f}s")
            print(f"  Range: {min_time:.3f}s - {max_time:.3f}s")
            
            for result in response_times:
                print(f"  '{result['query'][:40]}...' -> {result['response_time']:.3f}s ({result['complexity']})")
            
            # Quality checks
            if avg_time > 1.0:
                warnings.warn(f"High average response time: {avg_time:.3f}s", UserWarning, stacklevel=2)
            
            if max_time > 5.0:
                warnings.warn(f"Very slow maximum response time: {max_time:.3f}s", UserWarning, stacklevel=2)
                
        except Exception as e:
            pytest.fail(f"Single query performance test failed: {e}")

    @pytest.mark.skipif(not SERVICE_IMPORTS_AVAILABLE, reason=f"Service imports not available: {SERVICE_IMPORT_ERROR if not SERVICE_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_initialization_performance(self):
        """Test service initialization performance."""
        try:
            # Test cold start time
            start_time = time.time()
            service = QueryAnalyzerService()
            creation_time = time.time() - start_time
            
            # Service creation should be very fast
            assert creation_time < 5.0, f"Service creation took {creation_time:.2f}s"
            
            # Test first query (triggers initialization)
            start_time = time.time()
            result = await service.analyze_query("First query to trigger initialization")
            init_time = time.time() - start_time
            
            # Hard fail: >60s initialization
            assert init_time < 60.0, f"Initialization took {init_time:.2f}s - too slow"
            
            # Quality flag: >10s initialization
            if init_time > 10.0:
                warnings.warn(f"Slow initialization: {init_time:.2f}s", UserWarning, stacklevel=2)
            
            # Test subsequent query (should be faster)
            start_time = time.time()
            await service.analyze_query("Second query after initialization")
            subsequent_time = time.time() - start_time
            
            # Subsequent should be faster than initialization
            assert subsequent_time < init_time, "Subsequent query not faster than initialization"
            
            print(f"\nInitialization Performance Results:")
            print(f"  Service creation: {creation_time:.3f}s")
            print(f"  First query (init): {init_time:.3f}s")
            print(f"  Subsequent query: {subsequent_time:.3f}s")
            print(f"  Speedup factor: {init_time/subsequent_time:.1f}x")
            
        except Exception as e:
            pytest.fail(f"Initialization performance test failed: {e}")

    @pytest.mark.skipif(not SERVICE_IMPORTS_AVAILABLE, reason=f"Service imports not available: {SERVICE_IMPORT_ERROR if not SERVICE_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_query_length_performance_scaling(self):
        """Test how performance scales with query length."""
        service = QueryAnalyzerService()
        
        # Create queries of different lengths
        base_query = "What are the implications of machine learning in modern computing systems? "
        test_cases = [
            (base_query, "short"),
            (base_query * 5, "medium"),
            (base_query * 20, "long"),
            (base_query * 50, "very_long")
        ]
        
        results = []
        
        try:
            for query, length_category in test_cases:
                start_time = time.time()
                result = await service.analyze_query(query)
                response_time = time.time() - start_time
                
                # Hard fail: >60s for any query length
                assert response_time < 60.0, f"{length_category} query took {response_time:.2f}s"
                
                results.append({
                    "length_category": length_category,
                    "query_length": len(query),
                    "word_count": len(query.split()),
                    "response_time": response_time,
                    "complexity": result.get("complexity", "unknown")
                })
                
                print(f"{length_category:>10} ({len(query):>5} chars): {response_time:.3f}s -> {result.get('complexity')}")
            
            # Check for reasonable scaling
            times = [r["response_time"] for r in results]
            short_time = times[0]
            long_time = times[-1]
            
            # Very long queries shouldn't be more than 10x slower
            if long_time > short_time * 10:
                warnings.warn(f"Poor scaling: {long_time:.2f}s vs {short_time:.2f}s ({long_time/short_time:.1f}x)", UserWarning, stacklevel=2)
            
            print(f"\nQuery Length Scaling Results:")
            print(f"  Scaling factor: {long_time/short_time:.1f}x (long vs short)")
            
        except Exception as e:
            pytest.fail(f"Query length scaling test failed: {e}")


class TestQueryAnalyzerConcurrentPerformance:
    """Test concurrent request handling performance."""

    @pytest.mark.skipif(not SERVICE_IMPORTS_AVAILABLE, reason=f"Service imports not available: {SERVICE_IMPORT_ERROR if not SERVICE_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_concurrent_requests_basic(self):
        """Test basic concurrent request handling (10 requests)."""
        service = QueryAnalyzerService()
        
        # Create 10 concurrent requests (conservative for early-stage testing)
        queries = [f"What is machine learning approach number {i}?" for i in range(10)]
        
        try:
            start_time = time.time()
            tasks = [service.analyze_query(query) for query in queries]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # Analyze results
            successful_results = [r for r in results if not isinstance(r, Exception)]
            failed_results = [r for r in results if isinstance(r, Exception)]
            
            # Hard fail: All requests failed
            assert len(successful_results) > 0, "All concurrent requests failed"
            
            success_rate = len(successful_results) / len(queries)
            throughput = len(successful_results) / total_time  # requests/second
            
            # Quality checks
            if success_rate < 0.8:
                warnings.warn(f"Low concurrent success rate: {success_rate:.2%}", UserWarning, stacklevel=2)
            
            if throughput < 1.0:  # Less than 1 request per second
                warnings.warn(f"Low throughput: {throughput:.2f} req/s", UserWarning, stacklevel=2)
            
            if total_time > 30.0:  # 10 requests taking >30s
                warnings.warn(f"Slow concurrent processing: {total_time:.2f}s", UserWarning, stacklevel=2)
            
            print(f"\nConcurrent Performance Results (10 requests):")
            print(f"  Success rate: {success_rate:.2%} ({len(successful_results)}/{len(queries)})")
            print(f"  Total time: {total_time:.2f}s")
            print(f"  Throughput: {throughput:.2f} req/s")
            print(f"  Failed requests: {len(failed_results)}")
            
            if failed_results:
                print(f"  Sample error: {failed_results[0]}")
            
        except Exception as e:
            pytest.fail(f"Concurrent requests test failed: {e}")

    @pytest.mark.skipif(not SERVICE_IMPORTS_AVAILABLE, reason=f"Service imports not available: {SERVICE_IMPORT_ERROR if not SERVICE_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_concurrent_mixed_complexity(self):
        """Test concurrent requests with mixed complexity queries."""
        service = QueryAnalyzerService()
        
        # Mix of simple, medium, and complex queries
        queries = [
            ("Hi", "simple"),
            ("Yes", "simple"),
            ("What is AI?", "simple"),
            ("How does machine learning work?", "medium"),
            ("Explain neural network architectures", "medium"),
            ("Compare different optimization algorithms", "medium"),
            ("Analyze distributed consensus protocols", "complex"),
            ("Derive mathematical foundations of transformers", "complex")
        ]
        
        try:
            start_time = time.time()
            tasks = [service.analyze_query(query) for query, _ in queries]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # Analyze results by complexity
            complexity_results = {"simple": [], "medium": [], "complex": []}
            
            for i, result in enumerate(results):
                if not isinstance(result, Exception):
                    expected_complexity = queries[i][1]
                    actual_complexity = result.get("complexity", "unknown")
                    complexity_results[expected_complexity].append({
                        "expected": expected_complexity,
                        "actual": actual_complexity,
                        "query": queries[i][0]
                    })
            
            total_successful = sum(len(results) for results in complexity_results.values())
            success_rate = total_successful / len(queries)
            
            # Hard fail: No successful results
            assert total_successful > 0, "All mixed complexity requests failed"
            
            print(f"\nMixed Complexity Concurrent Results:")
            print(f"  Total success rate: {success_rate:.2%} ({total_successful}/{len(queries)})")
            print(f"  Total time: {total_time:.2f}s")
            
            for complexity, results_list in complexity_results.items():
                if results_list:
                    correct = sum(1 for r in results_list if r["actual"] == r["expected"])
                    accuracy = correct / len(results_list)
                    print(f"  {complexity:>7}: {len(results_list)} requests, {accuracy:.2%} accuracy")
            
        except Exception as e:
            pytest.fail(f"Mixed complexity concurrent test failed: {e}")

    @pytest.mark.skipif(not SERVICE_IMPORTS_AVAILABLE, reason=f"Service imports not available: {SERVICE_IMPORT_ERROR if not SERVICE_IMPORTS_AVAILABLE else ''}")
    def test_threaded_concurrent_requests(self):
        """Test concurrent requests from multiple threads."""
        service = QueryAnalyzerService()
        
        num_threads = 5
        requests_per_thread = 3
        results_queue = queue.Queue()
        
        def worker_thread(thread_id):
            """Worker function for each thread."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                for i in range(requests_per_thread):
                    query = f"Thread {thread_id} query {i}: What is machine learning?"
                    start_time = time.time()
                    
                    result = loop.run_until_complete(service.analyze_query(query))
                    
                    response_time = time.time() - start_time
                    
                    results_queue.put({
                        "thread_id": thread_id,
                        "request_id": i,
                        "response_time": response_time,
                        "success": True,
                        "complexity": result.get("complexity", "unknown"),
                        "error": None
                    })
                    
            except Exception as e:
                results_queue.put({
                    "thread_id": thread_id,
                    "request_id": -1,
                    "response_time": None,
                    "success": False,
                    "complexity": None,
                    "error": str(e)
                })
            finally:
                loop.close()
        
        try:
            # Start all threads
            threads = []
            start_time = time.time()
            
            for thread_id in range(num_threads):
                thread = threading.Thread(target=worker_thread, args=(thread_id,))
                thread.start()
                threads.append(thread)
            
            # Wait for completion
            for thread in threads:
                thread.join(timeout=60)  # 60s timeout per thread
            
            total_time = time.time() - start_time
            
            # Collect results
            results = []
            while not results_queue.empty():
                results.append(results_queue.get())
            
            successful_results = [r for r in results if r["success"]]
            failed_results = [r for r in results if not r["success"]]
            
            expected_total = num_threads * requests_per_thread
            success_rate = len(successful_results) / expected_total
            
            # Hard fail: All threaded requests failed
            assert len(successful_results) > 0, "All threaded requests failed"
            
            # Quality checks
            if success_rate < 0.8:
                warnings.warn(f"Low threaded success rate: {success_rate:.2%}", UserWarning, stacklevel=2)
            
            if total_time > 60.0:
                warnings.warn(f"Slow threaded processing: {total_time:.2f}s", UserWarning, stacklevel=2)
            
            print(f"\nThreaded Concurrent Results:")
            print(f"  Threads: {num_threads}, Requests/thread: {requests_per_thread}")
            print(f"  Success rate: {success_rate:.2%} ({len(successful_results)}/{expected_total})")
            print(f"  Total time: {total_time:.2f}s")
            print(f"  Failed requests: {len(failed_results)}")
            
            if successful_results:
                response_times = [r["response_time"] for r in successful_results]
                avg_time = sum(response_times) / len(response_times)
                print(f"  Average response time: {avg_time:.3f}s")
            
        except Exception as e:
            pytest.fail(f"Threaded concurrent test failed: {e}")


class TestQueryAnalyzerResourceUsage:
    """Test resource usage and memory characteristics."""

    @pytest.mark.skipif(not SERVICE_IMPORTS_AVAILABLE, reason=f"Service imports not available: {SERVICE_IMPORT_ERROR if not SERVICE_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available for memory monitoring")
    @pytest.mark.asyncio
    async def test_memory_usage_baseline(self):
        """Test baseline memory usage."""
        import os
        process = psutil.Process(os.getpid())
        
        try:
            # Get initial memory
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Create service
            service = QueryAnalyzerService()
            after_creation = process.memory_info().rss / 1024 / 1024  # MB
            
            # Perform first analysis (initialization)
            await service.analyze_query("First query for memory test")
            after_init = process.memory_info().rss / 1024 / 1024  # MB
            
            # Perform several more analyses
            for i in range(10):
                await service.analyze_query(f"Memory test query {i}")
            
            after_queries = process.memory_info().rss / 1024 / 1024  # MB
            
            # Calculate memory increases
            creation_increase = after_creation - initial_memory
            init_increase = after_init - after_creation
            queries_increase = after_queries - after_init
            total_increase = after_queries - initial_memory
            
            # Hard fail: >8GB total memory usage
            assert after_queries < 8000, f"Memory usage {after_queries:.1f}MB exceeds 8GB limit"
            
            # Quality flags
            if total_increase > 1000:  # 1GB increase
                warnings.warn(f"High memory increase: {total_increase:.1f}MB", UserWarning, stacklevel=2)
            
            if queries_increase > 100:  # 100MB for 10 queries
                warnings.warn(f"High per-query memory increase: {queries_increase:.1f}MB for 10 queries", UserWarning, stacklevel=2)
            
            print(f"\nMemory Usage Results:")
            print(f"  Initial: {initial_memory:.1f}MB")
            print(f"  After creation: {after_creation:.1f}MB (+{creation_increase:.1f}MB)")
            print(f"  After init: {after_init:.1f}MB (+{init_increase:.1f}MB)")
            print(f"  After 10 queries: {after_queries:.1f}MB (+{queries_increase:.1f}MB)")
            print(f"  Total increase: {total_increase:.1f}MB")
            
        except Exception as e:
            pytest.fail(f"Memory usage test failed: {e}")

    @pytest.mark.skipif(not SERVICE_IMPORTS_AVAILABLE, reason=f"Service imports not available: {SERVICE_IMPORT_ERROR if not SERVICE_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available for memory monitoring")
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self):
        """Test for potential memory leaks."""
        import os
        process = psutil.Process(os.getpid())
        
        try:
            service = QueryAnalyzerService()
            
            # Perform initial queries to stabilize
            for i in range(5):
                await service.analyze_query(f"Stabilization query {i}")
            
            # Force garbage collection
            gc.collect()
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Perform many queries and check memory growth
            for batch in range(3):  # 3 batches of 10 queries each
                for i in range(10):
                    await service.analyze_query(f"Leak test batch {batch} query {i}")
                
                # Check memory after each batch
                gc.collect()
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - baseline_memory
                
                print(f"  Batch {batch + 1}: {current_memory:.1f}MB (+{memory_increase:.1f}MB)")
                
                # Quality flag: Significant memory growth
                if memory_increase > 50 * (batch + 1):  # More than 50MB per batch
                    warnings.warn(f"Potential memory leak: {memory_increase:.1f}MB after {(batch + 1) * 10} queries", UserWarning, stacklevel=2)
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            total_increase = final_memory - baseline_memory
            
            print(f"\nMemory Leak Detection Results:")
            print(f"  Baseline: {baseline_memory:.1f}MB")
            print(f"  Final: {final_memory:.1f}MB")
            print(f"  Increase: {total_increase:.1f}MB for 30 queries")
            print(f"  Per query: {total_increase/30:.2f}MB")
            
            # Quality flag: High per-query memory increase
            if total_increase > 150:  # 150MB for 30 queries
                warnings.warn(f"High memory growth: {total_increase:.1f}MB for 30 queries", UserWarning, stacklevel=2)
            
        except Exception as e:
            pytest.fail(f"Memory leak detection test failed: {e}")

    @pytest.mark.skipif(not SERVICE_IMPORTS_AVAILABLE, reason=f"Service imports not available: {SERVICE_IMPORT_ERROR if not SERVICE_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available for CPU monitoring")
    @pytest.mark.asyncio
    async def test_cpu_usage_monitoring(self):
        """Test CPU usage characteristics."""
        import os
        process = psutil.Process(os.getpid())
        
        try:
            service = QueryAnalyzerService()
            
            # Monitor CPU usage during analysis
            cpu_samples = []
            
            # Perform analyses while monitoring CPU
            for i in range(5):
                cpu_before = process.cpu_percent()
                
                start_time = time.time()
                await service.analyze_query(f"CPU test query {i}: How does machine learning work?")
                analysis_time = time.time() - start_time
                
                cpu_after = process.cpu_percent()
                
                cpu_samples.append({
                    "cpu_before": cpu_before,
                    "cpu_after": cpu_after,
                    "analysis_time": analysis_time
                })
                
                # Brief pause to allow CPU measurement
                await asyncio.sleep(0.1)
            
            # Calculate CPU statistics
            avg_cpu = sum(s["cpu_after"] for s in cpu_samples) / len(cpu_samples)
            max_cpu = max(s["cpu_after"] for s in cpu_samples)
            avg_time = sum(s["analysis_time"] for s in cpu_samples) / len(cpu_samples)
            
            print(f"\nCPU Usage Results:")
            print(f"  Average CPU: {avg_cpu:.1f}%")
            print(f"  Maximum CPU: {max_cpu:.1f}%")
            print(f"  Average analysis time: {avg_time:.3f}s")
            
            # Quality flags
            if avg_cpu > 90:
                warnings.warn(f"High average CPU usage: {avg_cpu:.1f}%", UserWarning, stacklevel=2)
            
            if max_cpu > 100:  # This shouldn't happen, but check anyway
                warnings.warn(f"CPU usage exceeded 100%: {max_cpu:.1f}%", UserWarning, stacklevel=2)
            
        except Exception as e:
            pytest.fail(f"CPU usage monitoring test failed: {e}")


class TestQueryAnalyzerStressTest:
    """Stress testing for edge cases and limits."""

    @pytest.mark.skipif(not SERVICE_IMPORTS_AVAILABLE, reason=f"Service imports not available: {SERVICE_IMPORT_ERROR if not SERVICE_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_rapid_fire_requests(self):
        """Test rapid consecutive requests."""
        service = QueryAnalyzerService()
        
        num_requests = 20
        queries = [f"Rapid fire query {i}" for i in range(num_requests)]
        
        try:
            start_time = time.time()
            
            # Fire requests as fast as possible
            results = []
            for query in queries:
                result = await service.analyze_query(query)
                results.append(result)
            
            total_time = time.time() - start_time
            throughput = num_requests / total_time
            
            # All requests should succeed
            assert len(results) == num_requests, f"Only {len(results)}/{num_requests} requests completed"
            
            # Validate all results
            for i, result in enumerate(results):
                assert "complexity" in result, f"Result {i} missing complexity"
                assert result["complexity"] in ["simple", "medium", "complex"], f"Result {i} invalid complexity"
            
            print(f"\nRapid Fire Results:")
            print(f"  Requests: {num_requests}")
            print(f"  Total time: {total_time:.2f}s")
            print(f"  Throughput: {throughput:.2f} req/s")
            print(f"  Average time per request: {total_time/num_requests:.3f}s")
            
            # Quality checks
            if throughput < 5.0:  # Less than 5 req/s
                warnings.warn(f"Low rapid fire throughput: {throughput:.2f} req/s", UserWarning, stacklevel=2)
            
        except Exception as e:
            pytest.fail(f"Rapid fire test failed: {e}")

    @pytest.mark.skipif(not SERVICE_IMPORTS_AVAILABLE, reason=f"Service imports not available: {SERVICE_IMPORT_ERROR if not SERVICE_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_sustained_load_performance(self):
        """Test performance under sustained load over time."""
        service = QueryAnalyzerService()
        
        duration_seconds = 30  # 30-second sustained test
        target_interval = 0.5  # Try for 2 requests per second
        
        results = []
        start_time = time.time()
        
        try:
            request_count = 0
            
            while time.time() - start_time < duration_seconds:
                query = f"Sustained load query {request_count}"
                
                query_start = time.time()
                result = await service.analyze_query(query)
                query_time = time.time() - query_start
                
                results.append({
                    "request_id": request_count,
                    "query_time": query_time,
                    "complexity": result.get("complexity", "unknown"),
                    "timestamp": time.time() - start_time
                })
                
                request_count += 1
                
                # Brief pause to control rate
                await asyncio.sleep(max(0, target_interval - query_time))
            
            total_time = time.time() - start_time
            actual_throughput = len(results) / total_time
            
            # Calculate performance statistics
            query_times = [r["query_time"] for r in results]
            avg_query_time = sum(query_times) / len(query_times)
            max_query_time = max(query_times)
            min_query_time = min(query_times)
            
            print(f"\nSustained Load Results ({total_time:.1f}s):")
            print(f"  Total requests: {len(results)}")
            print(f"  Throughput: {actual_throughput:.2f} req/s")
            print(f"  Query time - Avg: {avg_query_time:.3f}s, Range: {min_query_time:.3f}-{max_query_time:.3f}s")
            
            # Hard fail: No requests completed
            assert len(results) > 0, "No requests completed during sustained load test"
            
            # Quality checks
            if actual_throughput < 1.0:
                warnings.warn(f"Low sustained throughput: {actual_throughput:.2f} req/s", UserWarning, stacklevel=2)
            
            if max_query_time > 10.0:
                warnings.warn(f"Very slow query during sustained load: {max_query_time:.2f}s", UserWarning, stacklevel=2)
            
            # Check for performance degradation over time
            first_half = query_times[:len(query_times)//2]
            second_half = query_times[len(query_times)//2:]
            
            if len(first_half) > 0 and len(second_half) > 0:
                first_avg = sum(first_half) / len(first_half)
                second_avg = sum(second_half) / len(second_half)
                
                if second_avg > first_avg * 1.5:  # 50% slower
                    warnings.warn(f"Performance degradation: {first_avg:.3f}s -> {second_avg:.3f}s", UserWarning, stacklevel=2)
                
                print(f"  Performance trend: {first_avg:.3f}s -> {second_avg:.3f}s")
            
        except Exception as e:
            pytest.fail(f"Sustained load test failed: {e}")


if __name__ == "__main__":
    # Run specific test classes for development
    pytest.main([__file__ + "::TestQueryAnalyzerBasicPerformance", "-v"])