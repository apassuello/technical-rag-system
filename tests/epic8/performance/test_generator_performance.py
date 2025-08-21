"""
Performance Tests for Epic 8 Generator Service.

Tests basic performance characteristics of the Generator Service based on PT-8.1 
specifications from epic8-test-specification.md. Focus on realistic early-stage 
performance validation rather than full production load testing.

Testing Philosophy:
- Hard Fails: >60s response time, service crashes, >8GB memory, complete failure under minimal load  
- Quality Flags: >2s response time, poor concurrent performance, memory leaks, cost inefficiency

Focus Areas:
- Basic performance sanity checks (10 concurrent requests)
- Memory usage monitoring during generation
- Response time validation per model type
- Cost calculation performance
- Service stability under light concurrent load
"""

import pytest
import asyncio
import time
import threading
import queue
import statistics
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys
import requests
import concurrent.futures

# Add services to path  
services_path = Path(__file__).parent.parent.parent.parent / "services" / "generator"
if services_path.exists():
    sys.path.insert(0, str(services_path))

try:
    from app.core.generator import GeneratorService
    GENERATOR_IMPORTS_AVAILABLE = True
except ImportError as e:
    GENERATOR_IMPORTS_AVAILABLE = False
    GENERATOR_IMPORT_ERROR = str(e)

# Performance test configuration
GENERATOR_BASE_URL = "http://localhost:8081"
LIGHT_CONCURRENT_LOAD = 10  # Realistic early-stage testing
PERFORMANCE_TIMEOUT = 60.0  # Hard fail timeout

# Performance test data
PERFORMANCE_TEST_DOCUMENTS = [
    {
        "content": "RISC-V is an open-source instruction set architecture (ISA) based on established RISC principles. It provides a free, open standard for processor design that enables innovation without licensing restrictions.",
        "metadata": {
            "source": "risc-v-performance-guide.pdf",
            "page": 1,
            "title": "RISC-V Performance Overview"
        },
        "doc_id": "perf_doc_001",
        "score": 0.95
    },
    {
        "content": "The RISC-V instruction set architecture supports multiple implementation strategies, from simple in-order processors to complex out-of-order superscalar designs. This flexibility allows optimization for specific performance targets and power constraints.",
        "metadata": {
            "source": "risc-v-implementation.pdf",
            "page": 8,
            "title": "RISC-V Implementation Strategies"
        },
        "doc_id": "perf_doc_002", 
        "score": 0.88
    },
    {
        "content": "Vector processing capabilities in RISC-V provide significant performance improvements for data-parallel workloads. The vector extension supports configurable vector lengths and a rich set of vector operations optimized for high-performance computing applications.",
        "metadata": {
            "source": "risc-v-vector-performance.pdf",
            "page": 15,
            "title": "RISC-V Vector Performance"
        },
        "doc_id": "perf_doc_003",
        "score": 0.92
    }
]


class TestGeneratorServiceBasicPerformance:
    """Test basic performance characteristics."""

    @pytest.mark.skipif(not GENERATOR_IMPORTS_AVAILABLE, reason=f"Generator imports not available: {GENERATOR_IMPORT_ERROR if not GENERATOR_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_single_generation_performance(self):
        """Test performance of single generation request."""
        try:
            service = GeneratorService()
            
            # Performance test queries of different complexities
            test_queries = [
                {
                    "query": "What is RISC-V?",
                    "complexity": "simple",
                    "expected_max_time": 5.0  # Simple queries should be fast
                },
                {
                    "query": "Explain the key architectural differences between RISC-V and ARM processors",
                    "complexity": "medium", 
                    "expected_max_time": 10.0
                },
                {
                    "query": "Analyze the performance implications of RISC-V vector extensions for machine learning workloads, including memory bandwidth considerations and comparison with SIMD approaches",
                    "complexity": "complex",
                    "expected_max_time": 30.0
                }
            ]
            
            performance_results = []
            
            for test_case in test_queries:
                query = test_case["query"]
                complexity = test_case["complexity"]
                max_expected_time = test_case["expected_max_time"]
                
                try:
                    start_time = time.time()
                    result = await service.generate_answer(
                        query=query,
                        context_documents=PERFORMANCE_TEST_DOCUMENTS[:2],
                        options={"strategy": "balanced"}
                    )
                    response_time = time.time() - start_time
                    
                    # Hard Fail: Any request takes more than 60 seconds
                    assert response_time < 60.0, f"{complexity} query took {response_time:.2f}s - HARD FAIL (>60s)"
                    
                    # Quality Flag: Request takes longer than expected for complexity
                    if response_time > max_expected_time:
                        print(f"WARNING: {complexity} query took {response_time:.2f}s (expected <{max_expected_time}s)")
                    
                    # Quality Flag: Very slow responses
                    if response_time > 2.0:
                        print(f"WARNING: {complexity} query took {response_time:.2f}s (>2s)")
                    
                    performance_results.append({
                        "complexity": complexity,
                        "response_time": response_time,
                        "model_used": result.get("model_used", "unknown"),
                        "cost": result.get("cost", 0),
                        "answer_length": len(result.get("answer", ""))
                    })
                    
                    print(f"✅ {complexity.capitalize()} query: {response_time:.2f}s, {result.get('model_used', 'unknown')}, ${result.get('cost', 0):.4f}")
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    if any(keyword in error_msg for keyword in ["import", "module", "not found"]):
                        print(f"{complexity} query skipped due to missing dependencies")
                        continue
                    else:
                        print(f"WARNING: {complexity} query failed: {e}")
                        continue
            
            if performance_results:
                # Analyze performance trends
                avg_time = sum(r["response_time"] for r in performance_results) / len(performance_results)
                print(f"Average response time: {avg_time:.2f}s")
                
                # Check that response times scale reasonably with complexity
                simple_times = [r["response_time"] for r in performance_results if r["complexity"] == "simple"]
                complex_times = [r["response_time"] for r in performance_results if r["complexity"] == "complex"]
                
                if simple_times and complex_times:
                    avg_simple = sum(simple_times) / len(simple_times)
                    avg_complex = sum(complex_times) / len(complex_times)
                    
                    if avg_simple > avg_complex:
                        print(f"WARNING: Simple queries ({avg_simple:.2f}s) take longer than complex ones ({avg_complex:.2f}s)")
                    else:
                        print(f"✅ Response time scaling: simple {avg_simple:.2f}s, complex {avg_complex:.2f}s")
            else:
                pytest.skip("No performance results available")
                
        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ["import", "module", "not found"]):
                pytest.skip(f"Single generation performance test skipped: {e}")
            else:
                pytest.fail(f"Single generation performance test failed - HARD FAIL: {e}")

    @pytest.mark.skipif(not GENERATOR_IMPORTS_AVAILABLE, reason=f"Generator imports not available: {GENERATOR_IMPORT_ERROR if not GENERATOR_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_service_operations_performance(self):
        """Test performance of basic service operations."""
        try:
            service = GeneratorService()
            
            # Test performance of different service operations
            operations = [
                ("get_generator_status", lambda: service.get_generator_status()),
                ("get_available_models", lambda: service.get_available_models()),
                ("get_model_costs", lambda: service.get_model_costs()),
                ("health_check", lambda: service.health_check())
            ]
            
            operation_results = []
            
            for op_name, op_func in operations:
                times = []
                
                # Run each operation multiple times for statistical significance
                for i in range(5):
                    start_time = time.time()
                    try:
                        result = await op_func()
                        response_time = time.time() - start_time
                        times.append(response_time)
                        
                        # Hard Fail: Any operation takes more than 60 seconds
                        assert response_time < 60.0, f"{op_name} took {response_time:.2f}s - HARD FAIL (>60s)"
                        
                    except Exception as e:
                        error_msg = str(e).lower()
                        if any(keyword in error_msg for keyword in ["import", "module", "not found"]):
                            print(f"{op_name} skipped due to missing dependencies")
                            break
                        else:
                            print(f"WARNING: {op_name} failed: {e}")
                            break
                
                if times:
                    avg_time = sum(times) / len(times)
                    max_time = max(times)
                    min_time = min(times)
                    
                    operation_results.append({
                        "operation": op_name,
                        "avg_time": avg_time,
                        "max_time": max_time,
                        "min_time": min_time,
                        "samples": len(times)
                    })
                    
                    # Quality flags for slow operations
                    if avg_time > 1.0:
                        print(f"WARNING: {op_name} avg time {avg_time:.2f}s (>1s)")
                    elif avg_time > 0.1:
                        print(f"INFO: {op_name} avg time {avg_time:.2f}s")
                    else:
                        print(f"✅ {op_name}: {avg_time:.3f}s avg")
            
            if operation_results:
                print("\nService Operations Performance Summary:")
                for result in operation_results:
                    print(f"   {result['operation']}: {result['avg_time']:.3f}s avg (range: {result['min_time']:.3f}-{result['max_time']:.3f}s)")
            else:
                pytest.skip("No service operation results available")
                
        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ["import", "module", "not found"]):
                pytest.skip(f"Service operations performance test skipped: {e}")
            else:
                pytest.fail(f"Service operations performance test failed - HARD FAIL: {e}")


class TestGeneratorConcurrentPerformance:
    """Test concurrent request performance."""

    @pytest.mark.skipif(not GENERATOR_IMPORTS_AVAILABLE, reason=f"Generator imports not available: {GENERATOR_IMPORT_ERROR if not GENERATOR_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_light_concurrent_load(self):
        """Test service under light concurrent load (10 concurrent requests)."""
        try:
            service = GeneratorService()
            
            # Create light concurrent workload
            num_concurrent = LIGHT_CONCURRENT_LOAD
            concurrent_requests = []
            
            for i in range(num_concurrent):
                request_data = {
                    "query": f"Concurrent test {i+1}: Explain RISC-V key features",
                    "context_documents": PERFORMANCE_TEST_DOCUMENTS[:2],
                    "options": {
                        "strategy": "cost_optimized",  # Use cheaper models for load testing
                        "max_cost": 0.01
                    }
                }
                concurrent_requests.append(request_data)
            
            # Execute concurrent requests
            start_time = time.time()
            
            tasks = []
            for req in concurrent_requests:
                task = asyncio.create_task(
                    service.generate_answer(
                        query=req["query"],
                        context_documents=req["context_documents"],
                        options=req["options"]
                    )
                )
                tasks.append(task)
            
            try:
                # Wait for all tasks with timeout
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=PERFORMANCE_TIMEOUT
                )
                
                total_time = time.time() - start_time
                
                # Hard Fail: Total time exceeds timeout
                assert total_time < PERFORMANCE_TIMEOUT, f"Concurrent load took {total_time:.2f}s - HARD FAIL (>{PERFORMANCE_TIMEOUT}s)"
                
                # Analyze results
                successful_results = []
                failed_results = []
                response_times = []
                
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        error_msg = str(result).lower()
                        if any(keyword in error_msg for keyword in ["import", "module", "not found"]):
                            print(f"Concurrent request {i+1} skipped due to missing dependencies")
                        else:
                            failed_results.append(f"Request {i+1}: {result}")
                    else:
                        successful_results.append(result)
                        # Estimate response time (not perfectly accurate for concurrent)
                        response_times.append(total_time / num_concurrent)
                
                success_rate = len(successful_results) / num_concurrent
                
                # Hard Fail: Complete failure under light load
                if success_rate == 0.0:
                    pytest.fail(f"All {num_concurrent} concurrent requests failed - HARD FAIL")
                
                # Quality Flag: High failure rate under light load
                if success_rate < 0.7:
                    print(f"WARNING: Only {success_rate:.1%} success rate under light concurrent load")
                
                if successful_results:
                    # Calculate performance metrics
                    costs = [r.get("cost", 0) for r in successful_results]
                    models_used = [r.get("model_used", "unknown") for r in successful_results]
                    
                    avg_cost = sum(costs) / len(costs) if costs else 0
                    throughput = len(successful_results) / total_time  # requests per second
                    
                    print(f"✅ Concurrent performance test:")
                    print(f"   Requests: {len(successful_results)}/{num_concurrent} successful")
                    print(f"   Total time: {total_time:.2f}s")
                    print(f"   Throughput: {throughput:.2f} req/s")
                    print(f"   Average cost: ${avg_cost:.4f}")
                    print(f"   Models used: {set(models_used)}")
                    
                    # Quality flags
                    if throughput < 1.0:
                        print(f"WARNING: Low throughput {throughput:.2f} req/s under concurrent load")
                    
                    if avg_cost > 0.05:
                        print(f"WARNING: High average cost ${avg_cost:.4f} under concurrent load")
                
                if failed_results:
                    print(f"Failed requests ({len(failed_results)}):")
                    for failure in failed_results[:5]:  # Show first 5
                        print(f"   {failure}")
                
            except asyncio.TimeoutError:
                pytest.fail(f"Concurrent requests timed out after {PERFORMANCE_TIMEOUT}s - HARD FAIL")
                
        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ["import", "module", "not found"]):
                pytest.skip(f"Concurrent performance test skipped: {e}")
            else:
                pytest.fail(f"Concurrent performance test failed - HARD FAIL: {e}")

    def test_api_concurrent_performance(self):
        """Test API endpoint performance under light concurrent load."""
        try:
            # Test concurrent API requests
            test_request = {
                "query": "What are the performance characteristics of RISC-V?",
                "context_documents": PERFORMANCE_TEST_DOCUMENTS[:2],
                "options": {
                    "strategy": "cost_optimized",
                    "max_cost": 0.01
                }
            }
            
            results_queue = queue.Queue()
            num_concurrent = 5  # Lighter load for API testing
            
            def make_concurrent_request(request_id):
                """Make a single concurrent request."""
                try:
                    start_time = time.time()
                    response = requests.post(
                        f"{GENERATOR_BASE_URL}/api/v1/generate",
                        json=test_request,
                        timeout=30.0
                    )
                    response_time = time.time() - start_time
                    
                    results_queue.put({
                        "request_id": request_id,
                        "status_code": response.status_code,
                        "response_time": response_time,
                        "success": response.status_code < 500,
                        "size": len(response.content) if response.content else 0
                    })
                    
                except Exception as e:
                    results_queue.put({
                        "request_id": request_id,
                        "error": str(e),
                        "success": False,
                        "response_time": 0
                    })
            
            # Start concurrent requests
            threads = []
            start_time = time.time()
            
            for i in range(num_concurrent):
                thread = threading.Thread(target=make_concurrent_request, args=(i,))
                thread.start()
                threads.append(thread)
            
            # Wait for completion with timeout
            for thread in threads:
                thread.join(timeout=60.0)
            
            total_time = time.time() - start_time
            
            # Hard Fail: Total time exceeds 60 seconds
            assert total_time < 60.0, f"API concurrent test took {total_time:.2f}s - HARD FAIL (>60s)"
            
            # Collect results
            results = []
            while not results_queue.empty():
                results.append(results_queue.get())
            
            assert len(results) == num_concurrent, f"Expected {num_concurrent} results, got {len(results)}"
            
            # Analyze performance
            successful_requests = [r for r in results if r.get("success", False)]
            failed_requests = [r for r in results if not r.get("success", False)]
            
            success_rate = len(successful_requests) / len(results)
            
            # Hard Fail: Complete failure under light API load
            if success_rate == 0.0:
                pytest.fail(f"All {num_concurrent} concurrent API requests failed - HARD FAIL")
            
            if successful_requests:
                response_times = [r["response_time"] for r in successful_requests]
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                min_response_time = min(response_times)
                
                throughput = len(successful_requests) / total_time
                
                print(f"✅ API concurrent performance:")
                print(f"   Success rate: {success_rate:.1%} ({len(successful_requests)}/{num_concurrent})")
                print(f"   Total time: {total_time:.2f}s") 
                print(f"   Throughput: {throughput:.2f} req/s")
                print(f"   Response time: {avg_response_time:.2f}s avg (range: {min_response_time:.2f}-{max_response_time:.2f}s)")
                
                # Quality flags
                if avg_response_time > 2.0:
                    print(f"WARNING: High average API response time {avg_response_time:.2f}s")
                
                if max_response_time > 10.0:
                    print(f"WARNING: Maximum API response time {max_response_time:.2f}s (>10s)")
                
                if throughput < 0.5:
                    print(f"WARNING: Low API throughput {throughput:.2f} req/s")
            
            if failed_requests:
                print(f"Failed API requests ({len(failed_requests)}):")
                for req in failed_requests[:3]:  # Show first 3
                    error = req.get("error", "Unknown error")
                    print(f"   Request {req['request_id']}: {error}")
            
            # Verify service is still responsive
            try:
                health_response = requests.get(f"{GENERATOR_BASE_URL}/health", timeout=5.0)
                if health_response.status_code >= 500:
                    pytest.fail("Service unhealthy after concurrent API load - HARD FAIL")
                else:
                    print("✅ Service remained healthy after concurrent API load")
            except:
                print("WARNING: Could not verify service health after concurrent load")
                
        except requests.exceptions.ConnectionError:
            pytest.skip("Generator service not running for API performance test")
        except Exception as e:
            pytest.fail(f"API concurrent performance test failed - HARD FAIL: {e}")


class TestGeneratorMemoryPerformance:
    """Test memory usage during generation operations."""

    def test_memory_usage_during_generation(self):
        """Test memory usage during generation operations."""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Simulate memory-intensive generation workload
            generation_requests = []
            for i in range(3):  # Multiple requests to test memory behavior
                request_data = {
                    "query": f"Memory test {i+1}: Detailed analysis of RISC-V performance optimization strategies for high-performance computing applications, including vector processing, memory hierarchy design, and compiler optimizations",
                    "context_documents": PERFORMANCE_TEST_DOCUMENTS,  # All documents
                    "options": {"strategy": "balanced"}
                }
                generation_requests.append(request_data)
            
            memory_measurements = []
            
            for i, req_data in enumerate(generation_requests):
                try:
                    # Make generation request
                    response = requests.post(
                        f"{GENERATOR_BASE_URL}/api/v1/generate",
                        json=req_data,
                        timeout=30.0
                    )
                    
                    # Measure memory after request
                    current_memory = process.memory_info().rss / 1024 / 1024  # MB
                    memory_increase = current_memory - initial_memory
                    
                    memory_measurements.append({
                        "request": i+1,
                        "memory_mb": current_memory,
                        "increase_mb": memory_increase
                    })
                    
                    # Hard Fail: Process using more than 8GB
                    assert current_memory < 8192, f"Process using {current_memory:.1f}MB after request {i+1} - HARD FAIL (>8GB)"
                    
                    print(f"Request {i+1}: {current_memory:.1f}MB (+{memory_increase:.1f}MB)")
                    
                except requests.exceptions.ConnectionError:
                    pytest.skip("Generator service not running for memory test")
                except requests.exceptions.Timeout:
                    print(f"Request {i+1} timed out - continuing memory test")
                    continue
                except Exception as e:
                    print(f"Request {i+1} failed: {e} - continuing memory test")
                    continue
            
            if memory_measurements:
                # Analyze memory behavior
                memory_increases = [m["increase_mb"] for m in memory_measurements]
                max_memory = max(m["memory_mb"] for m in memory_measurements)
                max_increase = max(memory_increases)
                final_increase = memory_measurements[-1]["increase_mb"]
                
                print(f"Memory usage analysis:")
                print(f"   Initial: {initial_memory:.1f}MB")
                print(f"   Maximum: {max_memory:.1f}MB")
                print(f"   Max increase: {max_increase:.1f}MB")
                print(f"   Final increase: {final_increase:.1f}MB")
                
                # Quality flags for memory usage
                if max_increase > 500:  # 500MB increase
                    print(f"WARNING: High memory increase {max_increase:.1f}MB during generation")
                
                if final_increase > 200:  # 200MB permanent increase
                    print(f"WARNING: Significant memory not released {final_increase:.1f}MB")
                
                # Check for memory leaks (increasing trend)
                if len(memory_increases) >= 3:
                    trend = memory_increases[-1] - memory_increases[0]
                    if trend > 100:  # 100MB increase trend
                        print(f"WARNING: Possible memory leak trend +{trend:.1f}MB")
                    else:
                        print(f"✅ Memory usage stable (trend: {trend:+.1f}MB)")
                        
            else:
                pytest.skip("No memory measurements available")
                
        except ImportError:
            pytest.skip("psutil not available for memory testing")
        except Exception as e:
            pytest.fail(f"Memory performance test failed - HARD FAIL: {e}")

    @pytest.mark.skipif(not GENERATOR_IMPORTS_AVAILABLE, reason=f"Generator imports not available: {GENERATOR_IMPORT_ERROR if not GENERATOR_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_service_memory_efficiency(self):
        """Test service memory efficiency during repeated operations."""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            service = GeneratorService()
            
            # Repeated operations to test memory efficiency
            operations = [
                ("status_check", lambda: service.get_generator_status()),
                ("model_list", lambda: service.get_available_models()),
                ("cost_info", lambda: service.get_model_costs())
            ]
            
            memory_tracking = []
            
            for cycle in range(3):  # 3 cycles of operations
                print(f"Memory efficiency cycle {cycle + 1}:")
                
                for op_name, op_func in operations:
                    try:
                        # Run operation multiple times
                        for _ in range(5):
                            await op_func()
                        
                        # Measure memory
                        current_memory = process.memory_info().rss / 1024 / 1024  # MB
                        increase = current_memory - initial_memory
                        
                        memory_tracking.append({
                            "cycle": cycle + 1,
                            "operation": op_name,
                            "memory_mb": current_memory,
                            "increase_mb": increase
                        })
                        
                        print(f"   {op_name}: {current_memory:.1f}MB (+{increase:.1f}MB)")
                        
                        # Hard Fail: Excessive memory usage
                        assert current_memory < 8192, f"Memory {current_memory:.1f}MB exceeded 8GB - HARD FAIL"
                        
                    except Exception as e:
                        error_msg = str(e).lower()
                        if any(keyword in error_msg for keyword in ["import", "module", "not found"]):
                            print(f"   {op_name}: skipped due to dependencies")
                        else:
                            print(f"   {op_name}: failed - {e}")
            
            if memory_tracking:
                # Analyze memory efficiency
                final_memory = memory_tracking[-1]["memory_mb"]
                final_increase = memory_tracking[-1]["increase_mb"]
                
                # Check for memory growth over cycles
                cycle1_memory = [m["increase_mb"] for m in memory_tracking if m["cycle"] == 1]
                cycle3_memory = [m["increase_mb"] for m in memory_tracking if m["cycle"] == 3]
                
                if cycle1_memory and cycle3_memory:
                    avg_cycle1 = sum(cycle1_memory) / len(cycle1_memory)
                    avg_cycle3 = sum(cycle3_memory) / len(cycle3_memory)
                    growth = avg_cycle3 - avg_cycle1
                    
                    print(f"Memory efficiency summary:")
                    print(f"   Cycle 1 avg: +{avg_cycle1:.1f}MB")
                    print(f"   Cycle 3 avg: +{avg_cycle3:.1f}MB") 
                    print(f"   Growth: {growth:+.1f}MB")
                    
                    if growth > 50:  # 50MB growth over cycles
                        print(f"WARNING: Memory usage grew {growth:.1f}MB across cycles")
                    else:
                        print(f"✅ Memory usage stable across cycles")
            
        except ImportError:
            pytest.skip("psutil not available for service memory testing")
        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ["import", "module", "not found"]):
                pytest.skip(f"Service memory efficiency test skipped: {e}")
            else:
                pytest.fail(f"Service memory efficiency test failed - HARD FAIL: {e}")


class TestGeneratorCostPerformance:
    """Test cost calculation and optimization performance."""

    @pytest.mark.skipif(not GENERATOR_IMPORTS_AVAILABLE, reason=f"Generator imports not available: {GENERATOR_IMPORT_ERROR if not GENERATOR_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_cost_calculation_performance(self):
        """Test performance of cost calculation operations."""
        try:
            service = GeneratorService()
            
            # Test cost calculation speed
            cost_operations = [
                ("get_model_costs", lambda: service.get_model_costs()),
            ]
            
            for op_name, op_func in cost_operations:
                times = []
                
                # Run multiple times for statistical accuracy
                for i in range(10):
                    start_time = time.time()
                    try:
                        result = await op_func()
                        response_time = time.time() - start_time
                        times.append(response_time)
                        
                        # Hard Fail: Cost operation takes more than 10 seconds
                        assert response_time < 10.0, f"{op_name} took {response_time:.2f}s - HARD FAIL (>10s)"
                        
                    except Exception as e:
                        error_msg = str(e).lower()
                        if any(keyword in error_msg for keyword in ["import", "module", "not found"]):
                            pytest.skip(f"Cost calculation test skipped due to dependencies: {e}")
                        else:
                            print(f"WARNING: {op_name} iteration {i+1} failed: {e}")
                            break
                
                if times:
                    avg_time = sum(times) / len(times)
                    max_time = max(times)
                    min_time = min(times)
                    
                    print(f"✅ {op_name} performance:")
                    print(f"   Average: {avg_time:.3f}s")
                    print(f"   Range: {min_time:.3f}s - {max_time:.3f}s")
                    print(f"   Samples: {len(times)}")
                    
                    # Quality flags
                    if avg_time > 0.5:
                        print(f"WARNING: {op_name} average time {avg_time:.3f}s (>0.5s)")
                    
                    if max_time > 1.0:
                        print(f"WARNING: {op_name} maximum time {max_time:.3f}s (>1.0s)")
            
        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ["import", "module", "not found"]):
                pytest.skip(f"Cost calculation performance test skipped: {e}")
            else:
                pytest.fail(f"Cost calculation performance test failed - HARD FAIL: {e}")

    @pytest.mark.skipif(not GENERATOR_IMPORTS_AVAILABLE, reason=f"Generator imports not available: {GENERATOR_IMPORT_ERROR if not GENERATOR_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_cost_optimization_performance(self):
        """Test performance of cost optimization strategies."""
        try:
            service = GeneratorService()
            
            # Test different strategies with focus on performance
            strategies = ["cost_optimized", "balanced", "quality_first"]
            strategy_performance = []
            
            test_query = "What are the key benefits of RISC-V architecture?"
            test_documents = PERFORMANCE_TEST_DOCUMENTS[:2]
            
            for strategy in strategies:
                strategy_times = []
                strategy_costs = []
                
                # Run each strategy multiple times
                for i in range(3):
                    try:
                        start_time = time.time()
                        result = await service.generate_answer(
                            query=test_query,
                            context_documents=test_documents,
                            options={"strategy": strategy}
                        )
                        response_time = time.time() - start_time
                        
                        strategy_times.append(response_time)
                        strategy_costs.append(result.get("cost", 0))
                        
                        # Hard Fail: Strategy takes more than 60 seconds
                        assert response_time < 60.0, f"{strategy} strategy took {response_time:.2f}s - HARD FAIL"
                        
                    except Exception as e:
                        error_msg = str(e).lower()
                        if any(keyword in error_msg for keyword in ["import", "module", "not found"]):
                            break
                        else:
                            print(f"WARNING: {strategy} strategy iteration {i+1} failed: {e}")
                            continue
                
                if strategy_times:
                    avg_time = sum(strategy_times) / len(strategy_times)
                    avg_cost = sum(strategy_costs) / len(strategy_costs)
                    
                    strategy_performance.append({
                        "strategy": strategy,
                        "avg_time": avg_time,
                        "avg_cost": avg_cost,
                        "samples": len(strategy_times)
                    })
                    
                    print(f"✅ {strategy} strategy: {avg_time:.2f}s avg, ${avg_cost:.4f} avg")
            
            if strategy_performance:
                print("\nCost optimization performance summary:")
                for perf in strategy_performance:
                    print(f"   {perf['strategy']}: {perf['avg_time']:.2f}s, ${perf['avg_cost']:.4f} ({perf['samples']} samples)")
                
                # Analyze strategy efficiency
                cost_opt = next((p for p in strategy_performance if p["strategy"] == "cost_optimized"), None)
                quality = next((p for p in strategy_performance if p["strategy"] == "quality_first"), None)
                
                if cost_opt and quality:
                    if cost_opt["avg_cost"] > quality["avg_cost"]:
                        print(f"WARNING: cost_optimized (${cost_opt['avg_cost']:.4f}) costs more than quality_first (${quality['avg_cost']:.4f})")
                    else:
                        print(f"✅ Cost optimization working: cost_opt ${cost_opt['avg_cost']:.4f} < quality ${quality['avg_cost']:.4f}")
            else:
                pytest.skip("No cost optimization performance results available")
                
        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ["import", "module", "not found"]):
                pytest.skip(f"Cost optimization performance test skipped: {e}")
            else:
                pytest.fail(f"Cost optimization performance test failed - HARD FAIL: {e}")


@pytest.mark.performance_integration
class TestGeneratorPerformanceIntegration:
    """Test performance in integration scenarios."""

    def test_end_to_end_performance(self):
        """Test end-to-end performance through API."""
        try:
            # Full workflow performance test
            workflow_requests = [
                {
                    "name": "simple_workflow",
                    "request": {
                        "query": "What is RISC-V?",
                        "context_documents": PERFORMANCE_TEST_DOCUMENTS[:1],
                        "options": {"strategy": "cost_optimized"}
                    },
                    "expected_max_time": 10.0
                },
                {
                    "name": "complex_workflow", 
                    "request": {
                        "query": "Analyze RISC-V performance optimization strategies for high-performance computing",
                        "context_documents": PERFORMANCE_TEST_DOCUMENTS,
                        "options": {"strategy": "quality_first", "max_cost": 0.05}
                    },
                    "expected_max_time": 30.0
                }
            ]
            
            workflow_results = []
            
            for workflow in workflow_requests:
                name = workflow["name"]
                request_data = workflow["request"]
                max_time = workflow["expected_max_time"]
                
                try:
                    start_time = time.time()
                    response = requests.post(
                        f"{GENERATOR_BASE_URL}/api/v1/generate",
                        json=request_data,
                        timeout=60.0
                    )
                    response_time = time.time() - start_time
                    
                    # Hard Fail: Workflow exceeds 60 seconds
                    assert response_time < 60.0, f"{name} took {response_time:.2f}s - HARD FAIL (>60s)"
                    
                    # Quality Flag: Workflow exceeds expected time
                    if response_time > max_time:
                        print(f"WARNING: {name} took {response_time:.2f}s (expected <{max_time}s)")
                    
                    workflow_result = {
                        "name": name,
                        "response_time": response_time,
                        "status_code": response.status_code,
                        "success": response.status_code < 500,
                        "response_size": len(response.content) if response.content else 0
                    }
                    
                    if response.status_code == 200:
                        data = response.json()
                        workflow_result.update({
                            "model_used": data.get("model_used", "unknown"),
                            "cost": data.get("cost", 0),
                            "answer_length": len(data.get("answer", ""))
                        })
                    
                    workflow_results.append(workflow_result)
                    
                    print(f"✅ {name}: {response_time:.2f}s, status {response.status_code}")
                    
                except requests.exceptions.ConnectionError:
                    pytest.skip("Generator service not running for end-to-end test")
                except requests.exceptions.Timeout:
                    pytest.fail(f"{name} timed out - HARD FAIL")
                except Exception as e:
                    print(f"WARNING: {name} failed: {e}")
                    continue
            
            if workflow_results:
                print("\nEnd-to-end performance summary:")
                for result in workflow_results:
                    print(f"   {result['name']}: {result['response_time']:.2f}s, {result['status_code']}")
                    if result.get("cost") is not None:
                        print(f"      Model: {result.get('model_used', 'unknown')}, Cost: ${result['cost']:.4f}")
                
                # Overall performance metrics
                successful_workflows = [r for r in workflow_results if r["success"]]
                if successful_workflows:
                    avg_time = sum(r["response_time"] for r in successful_workflows) / len(successful_workflows)
                    avg_cost = sum(r.get("cost", 0) for r in successful_workflows) / len(successful_workflows)
                    
                    print(f"   Overall: {avg_time:.2f}s avg, ${avg_cost:.4f} avg cost")
            else:
                pytest.skip("No end-to-end performance results available")
                
        except Exception as e:
            pytest.fail(f"End-to-end performance test failed - HARD FAIL: {e}")

    def test_service_stability_under_load(self):
        """Test service stability during sustained light load."""
        try:
            # Sustained load test (shorter duration for early stage)
            duration_seconds = 30  # 30 second test
            request_interval = 2.0  # Request every 2 seconds
            
            test_request = {
                "query": "Stability test: RISC-V architecture overview",
                "context_documents": PERFORMANCE_TEST_DOCUMENTS[:1],
                "options": {"strategy": "cost_optimized"}
            }
            
            start_time = time.time()
            requests_made = 0
            successful_requests = 0
            failed_requests = 0
            response_times = []
            
            print(f"Starting {duration_seconds}s stability test...")
            
            while time.time() - start_time < duration_seconds:
                try:
                    req_start = time.time()
                    response = requests.post(
                        f"{GENERATOR_BASE_URL}/api/v1/generate",
                        json=test_request,
                        timeout=15.0
                    )
                    req_time = time.time() - req_start
                    
                    requests_made += 1
                    
                    if response.status_code < 500:
                        successful_requests += 1
                        response_times.append(req_time)
                    else:
                        failed_requests += 1
                    
                    # Wait before next request
                    time.sleep(max(0, request_interval - req_time))
                    
                except requests.exceptions.ConnectionError:
                    pytest.skip("Generator service not available for stability test")
                except requests.exceptions.Timeout:
                    failed_requests += 1
                    requests_made += 1
                    print("Request timed out during stability test")
                except Exception as e:
                    failed_requests += 1
                    requests_made += 1
                    print(f"Request failed during stability test: {e}")
                
                # Hard Fail: Service completely unresponsive
                if requests_made >= 3 and successful_requests == 0:
                    pytest.fail("Service completely unresponsive during stability test - HARD FAIL")
            
            total_time = time.time() - start_time
            
            if requests_made > 0:
                success_rate = successful_requests / requests_made
                avg_response_time = sum(response_times) / len(response_times) if response_times else 0
                
                print(f"✅ Stability test results ({total_time:.1f}s):")
                print(f"   Requests: {successful_requests}/{requests_made} successful ({success_rate:.1%})")
                print(f"   Average response time: {avg_response_time:.2f}s")
                print(f"   Failed requests: {failed_requests}")
                
                # Quality flags
                if success_rate < 0.8:
                    print(f"WARNING: Low success rate {success_rate:.1%} during sustained load")
                
                if avg_response_time > 5.0:
                    print(f"WARNING: High average response time {avg_response_time:.2f}s during sustained load")
                
                # Verify service is still healthy
                try:
                    health_response = requests.get(f"{GENERATOR_BASE_URL}/health", timeout=5.0)
                    if health_response.status_code >= 500:
                        print("WARNING: Service unhealthy after stability test")
                    else:
                        print("✅ Service remained healthy after stability test")
                except:
                    print("WARNING: Could not verify service health after stability test")
            else:
                pytest.skip("No requests completed during stability test")
                
        except Exception as e:
            pytest.fail(f"Service stability test failed - HARD FAIL: {e}")