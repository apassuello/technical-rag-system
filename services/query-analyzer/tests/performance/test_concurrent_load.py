"""
Concurrent load testing for Query Analyzer Service.

Tests the service's ability to handle multiple concurrent requests
and maintain performance under load.
"""

import pytest
import time
import statistics
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from typing import List, Dict, Tuple


class TestConcurrentRequests:
    """Test handling of concurrent requests."""

    def test_concurrent_analyze_requests(self, client, sample_queries):
        """Test concurrent analyze requests."""
        query = sample_queries["medium"][0]
        payload = {"query": query}
        num_concurrent = 10
        
        results = []
        
        def make_request():
            start_time = time.time()
            response = client.post("/api/v1/analyze", json=payload)
            response_time = time.time() - start_time
            
            return {
                "status_code": response.status_code,
                "response_time": response_time,
                "success": response.status_code == 200
            }
        
        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(make_request) for _ in range(num_concurrent)]
            results = [future.result() for future in as_completed(futures)]
        
        # Validate results
        success_count = sum(1 for r in results if r["success"])
        success_rate = success_count / num_concurrent
        
        assert success_rate >= 0.9  # At least 90% should succeed
        
        # Performance should remain reasonable under concurrency
        response_times = [r["response_time"] for r in results if r["success"]]
        if response_times:
            avg_time = statistics.mean(response_times)
            max_time = max(response_times)
            
            assert avg_time < 2.0  # Average should be reasonable
            assert max_time < 5.0  # No request should take too long

    def test_concurrent_mixed_requests(self, client, sample_queries):
        """Test concurrent requests to different endpoints."""
        requests = [
            ("analyze", lambda: client.post("/api/v1/analyze", json={"query": sample_queries["simple"][0]})),
            ("status", lambda: client.get("/api/v1/status")),
            ("components", lambda: client.get("/api/v1/components")),
            ("health", lambda: client.get("/health")),
            ("batch", lambda: client.post("/api/v1/batch-analyze", json=sample_queries["simple"][:2])),
        ]
        
        results = {req_type: [] for req_type, _ in requests}
        
        def make_request(req_type, req_func):
            start_time = time.time()
            try:
                response = req_func()
                response_time = time.time() - start_time
                return {
                    "type": req_type,
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "success": response.status_code in [200, 503]  # 503 acceptable for readiness
                }
            except Exception as e:
                return {
                    "type": req_type,
                    "error": str(e),
                    "response_time": time.time() - start_time,
                    "success": False
                }
        
        # Execute mixed concurrent requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for _ in range(4):  # 4 rounds of each request type
                for req_type, req_func in requests:
                    future = executor.submit(make_request, req_type, req_func)
                    futures.append(future)
            
            for future in as_completed(futures):
                result = future.result()
                results[result["type"]].append(result)
        
        # Validate each request type
        for req_type, req_results in results.items():
            if req_results:
                success_rate = sum(1 for r in req_results if r["success"]) / len(req_results)
                assert success_rate >= 0.8, f"{req_type} requests had low success rate: {success_rate:.2f}"
                
                # Check performance
                response_times = [r["response_time"] for r in req_results if r["success"]]
                if response_times:
                    avg_time = statistics.mean(response_times)
                    max_expected = 3.0 if req_type == "analyze" else 1.0
                    assert avg_time < max_expected

    def test_concurrent_batch_requests(self, client, sample_queries):
        """Test concurrent batch requests."""
        queries = sample_queries["simple"][:3]  # Small batches
        num_concurrent = 5
        
        def make_batch_request():
            start_time = time.time()
            response = client.post("/api/v1/batch-analyze", json=queries)
            response_time = time.time() - start_time
            
            success = response.status_code == 200
            data = response.json() if success else {}
            
            return {
                "status_code": response.status_code,
                "response_time": response_time,
                "success": success,
                "successful_analyses": data.get("successful_analyses", 0),
                "failed_analyses": data.get("failed_analyses", 0)
            }
        
        # Execute concurrent batch requests
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(make_batch_request) for _ in range(num_concurrent)]
            results = [future.result() for future in as_completed(futures)]
        
        # Validate results
        successful_requests = [r for r in results if r["success"]]
        success_rate = len(successful_requests) / num_concurrent
        
        assert success_rate >= 0.8  # At least 80% should succeed
        
        # Check that analyses within batches were successful
        for result in successful_requests:
            total_analyses = result["successful_analyses"] + result["failed_analyses"]
            analysis_success_rate = result["successful_analyses"] / max(total_analyses, 1)
            assert analysis_success_rate >= 0.8

    def test_scaling_concurrent_load(self, client, sample_queries):
        """Test performance scaling with increasing concurrent load."""
        query = sample_queries["simple"][0]
        payload = {"query": query}
        
        concurrency_levels = [1, 5, 10, 20]
        results = {}
        
        for concurrency in concurrency_levels:
            print(f"\nTesting concurrency level: {concurrency}")
            
            def make_request():
                start_time = time.time()
                response = client.post("/api/v1/analyze", json=payload)
                response_time = time.time() - start_time
                return response.status_code, response_time
            
            # Execute requests at this concurrency level
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(make_request) for _ in range(concurrency)]
                request_results = [future.result() for future in as_completed(futures)]
            
            total_time = time.time() - start_time
            
            # Analyze results
            successful_requests = [r for r in request_results if r[0] == 200]
            success_rate = len(successful_requests) / concurrency
            
            if successful_requests:
                response_times = [r[1] for r in successful_requests]
                avg_response_time = statistics.mean(response_times)
                max_response_time = max(response_times)
                
                results[concurrency] = {
                    "success_rate": success_rate,
                    "avg_response_time": avg_response_time,
                    "max_response_time": max_response_time,
                    "total_time": total_time,
                    "throughput": len(successful_requests) / total_time
                }
            
            # Basic validation for this concurrency level
            assert success_rate >= 0.7  # At least 70% success rate
        
        # Validate scaling characteristics
        print(f"\nScaling Results:")
        for concurrency, metrics in results.items():
            print(f"  Concurrency {concurrency}: "
                  f"Success={metrics['success_rate']:.1%}, "
                  f"AvgTime={metrics['avg_response_time']:.3f}s, "
                  f"Throughput={metrics['throughput']:.1f} req/s")
        
        # Performance should not degrade exponentially with concurrency
        if len(results) >= 2:
            low_concurrency = min(results.keys())
            high_concurrency = max(results.keys())
            
            low_avg_time = results[low_concurrency]["avg_response_time"]
            high_avg_time = results[high_concurrency]["avg_response_time"]
            
            # High concurrency should not be more than 5x slower
            assert high_avg_time < low_avg_time * 5

    def test_sustained_concurrent_load(self, client, sample_queries):
        """Test sustained concurrent load over time."""
        query = sample_queries["medium"][0]
        payload = {"query": query}
        
        duration = 30  # Test for 30 seconds
        concurrency = 8
        results = []
        start_time = time.time()
        
        def make_continuous_requests():
            """Make requests continuously for the duration."""
            thread_results = []
            thread_start = time.time()
            
            while time.time() - thread_start < duration:
                request_start = time.time()
                try:
                    response = client.post("/api/v1/analyze", json=payload)
                    request_time = time.time() - request_start
                    
                    thread_results.append({
                        "timestamp": request_start - start_time,
                        "response_time": request_time,
                        "status_code": response.status_code,
                        "success": response.status_code == 200
                    })
                except Exception as e:
                    thread_results.append({
                        "timestamp": request_start - start_time,
                        "response_time": time.time() - request_start,
                        "error": str(e),
                        "success": False
                    })
                
                # Small delay to prevent overwhelming the service
                time.sleep(0.1)
            
            return thread_results
        
        # Start concurrent threads
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(make_continuous_requests) for _ in range(concurrency)]
            
            # Collect all results
            for future in as_completed(futures):
                results.extend(future.result())
        
        # Analyze sustained performance
        successful_requests = [r for r in results if r["success"]]
        total_requests = len(results)
        
        if total_requests > 0:
            success_rate = len(successful_requests) / total_requests
            avg_response_time = statistics.mean([r["response_time"] for r in successful_requests])
            throughput = len(successful_requests) / duration
            
            print(f"\nSustained Load Results:")
            print(f"  Duration: {duration}s")
            print(f"  Total Requests: {total_requests}")
            print(f"  Success Rate: {success_rate:.1%}")
            print(f"  Average Response Time: {avg_response_time:.3f}s")
            print(f"  Throughput: {throughput:.1f} req/s")
            
            # Validate sustained performance
            assert success_rate >= 0.8  # At least 80% success rate
            assert avg_response_time < 2.0  # Average response time reasonable
            assert throughput > 1.0  # At least 1 request per second throughput
        
        # Check for performance degradation over time
        if successful_requests:
            # Split into time windows
            window_size = duration / 5  # 5 time windows
            time_windows = {}
            
            for result in successful_requests:
                window = int(result["timestamp"] / window_size)
                if window not in time_windows:
                    time_windows[window] = []
                time_windows[window].append(result["response_time"])
            
            # Calculate average response time per window
            window_averages = {}
            for window, times in time_windows.items():
                if times:
                    window_averages[window] = statistics.mean(times)
            
            if len(window_averages) >= 2:
                # Performance should not degrade significantly over time
                first_window_avg = window_averages[min(window_averages.keys())]
                last_window_avg = window_averages[max(window_averages.keys())]
                
                # Last window should not be more than 3x slower than first
                assert last_window_avg < first_window_avg * 3


class TestLoadTesting:
    """Load testing with various patterns."""

    def test_spike_load(self, client, sample_queries):
        """Test handling of sudden load spikes."""
        query = sample_queries["simple"][0]
        payload = {"query": query}
        
        # Normal load (warm up)
        for _ in range(5):
            response = client.post("/api/v1/analyze", json=payload)
            assert response.status_code == 200
        
        # Sudden spike
        spike_size = 50
        results = []
        
        def make_request():
            start_time = time.time()
            response = client.post("/api/v1/analyze", json=payload)
            response_time = time.time() - start_time
            return response.status_code, response_time
        
        # Execute spike
        spike_start = time.time()
        
        with ThreadPoolExecutor(max_workers=spike_size) as executor:
            futures = [executor.submit(make_request) for _ in range(spike_size)]
            results = [future.result() for future in as_completed(futures)]
        
        spike_duration = time.time() - spike_start
        
        # Analyze spike handling
        successful_requests = [r for r in results if r[0] == 200]
        success_rate = len(successful_requests) / spike_size
        
        if successful_requests:
            avg_response_time = statistics.mean([r[1] for r in successful_requests])
            max_response_time = max([r[1] for r in successful_requests])
            
            print(f"\nSpike Load Results:")
            print(f"  Spike Size: {spike_size} requests")
            print(f"  Spike Duration: {spike_duration:.2f}s")
            print(f"  Success Rate: {success_rate:.1%}")
            print(f"  Average Response Time: {avg_response_time:.3f}s")
            print(f"  Max Response Time: {max_response_time:.3f}s")
            
            # Service should handle spike reasonably well
            assert success_rate >= 0.7  # At least 70% success during spike
            assert avg_response_time < 5.0  # Average time should be reasonable
            assert max_response_time < 10.0  # No request should take too long

    def test_gradual_ramp_up(self, client, sample_queries):
        """Test gradual load ramp-up."""
        query = sample_queries["medium"][0]
        payload = {"query": query}
        
        ramp_steps = [2, 5, 10, 15, 20]
        results = {}
        
        for concurrency in ramp_steps:
            print(f"Ramping up to {concurrency} concurrent requests...")
            
            def make_request():
                start_time = time.time()
                response = client.post("/api/v1/analyze", json=payload)
                response_time = time.time() - start_time
                return response.status_code, response_time
            
            # Execute requests at current concurrency level
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(make_request) for _ in range(concurrency)]
                step_results = [future.result() for future in as_completed(futures)]
            
            # Analyze this step
            successful = [r for r in step_results if r[0] == 200]
            success_rate = len(successful) / concurrency
            
            if successful:
                avg_time = statistics.mean([r[1] for r in successful])
                results[concurrency] = {
                    "success_rate": success_rate,
                    "avg_response_time": avg_time
                }
            
            # Brief pause between ramp steps
            time.sleep(1)
        
        print(f"\nRamp-up Results:")
        for concurrency, metrics in results.items():
            print(f"  {concurrency} concurrent: "
                  f"Success={metrics['success_rate']:.1%}, "
                  f"AvgTime={metrics['avg_response_time']:.3f}s")
        
        # Service should handle gradual ramp-up well
        for concurrency, metrics in results.items():
            assert metrics["success_rate"] >= 0.8  # High success rate at all levels
            assert metrics["avg_response_time"] < 3.0  # Reasonable response times

    def test_stress_testing(self, client, sample_queries):
        """Stress test to find breaking point."""
        query = sample_queries["simple"][0]  # Use simple query for stress test
        payload = {"query": query}
        
        stress_levels = [25, 50, 75, 100]
        breaking_point = None
        
        for stress_level in stress_levels:
            print(f"Stress testing at {stress_level} concurrent requests...")
            
            def make_request():
                try:
                    start_time = time.time()
                    response = client.post("/api/v1/analyze", json=payload)
                    response_time = time.time() - start_time
                    return response.status_code, response_time, None
                except Exception as e:
                    return 0, 0, str(e)
            
            # Execute stress test
            with ThreadPoolExecutor(max_workers=stress_level) as executor:
                futures = [executor.submit(make_request) for _ in range(stress_level)]
                stress_results = [future.result() for future in as_completed(futures)]
            
            # Analyze stress results
            successful_requests = [r for r in stress_results if r[0] == 200]
            success_rate = len(successful_requests) / stress_level
            
            if successful_requests:
                avg_response_time = statistics.mean([r[1] for r in successful_requests])
                max_response_time = max([r[1] for r in successful_requests])
                
                print(f"  Success Rate: {success_rate:.1%}")
                print(f"  Average Response Time: {avg_response_time:.3f}s")
                print(f"  Max Response Time: {max_response_time:.3f}s")
                
                # Define breaking point as < 50% success rate
                if success_rate < 0.5:
                    breaking_point = stress_level
                    print(f"  Breaking point reached at {stress_level} concurrent requests")
                    break
            else:
                breaking_point = stress_level
                print(f"  Complete failure at {stress_level} concurrent requests")
                break
            
            # Brief pause between stress levels
            time.sleep(2)
        
        # Service should handle reasonable load before breaking
        if breaking_point:
            assert breaking_point >= 25, f"Service broke at only {breaking_point} concurrent requests"
        else:
            print("Service handled all stress levels successfully")

    @pytest.mark.skip(reason="Long-running test, enable for full load testing")
    def test_endurance_testing(self, client, sample_queries):
        """Long-running endurance test."""
        query = sample_queries["simple"][0]
        payload = {"query": query}
        
        test_duration = 300  # 5 minutes
        concurrency = 5
        results = []
        
        start_time = time.time()
        
        def make_continuous_requests():
            thread_results = []
            thread_start = time.time()
            
            while time.time() - thread_start < test_duration:
                request_start = time.time()
                try:
                    response = client.post("/api/v1/analyze", json=payload)
                    request_time = time.time() - request_start
                    
                    thread_results.append({
                        "timestamp": request_start - start_time,
                        "response_time": request_time,
                        "success": response.status_code == 200
                    })
                except Exception:
                    thread_results.append({
                        "timestamp": request_start - start_time,
                        "response_time": time.time() - request_start,
                        "success": False
                    })
                
                time.sleep(0.5)  # Moderate pace
            
            return thread_results
        
        # Run endurance test
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(make_continuous_requests) for _ in range(concurrency)]
            
            for future in as_completed(futures):
                results.extend(future.result())
        
        # Analyze endurance results
        successful_requests = [r for r in results if r["success"]]
        total_requests = len(results)
        
        if total_requests > 0:
            success_rate = len(successful_requests) / total_requests
            avg_response_time = statistics.mean([r["response_time"] for r in successful_requests])
            throughput = len(successful_requests) / test_duration
            
            print(f"\nEndurance Test Results:")
            print(f"  Duration: {test_duration / 60:.1f} minutes")
            print(f"  Total Requests: {total_requests}")
            print(f"  Success Rate: {success_rate:.1%}")
            print(f"  Average Response Time: {avg_response_time:.3f}s")
            print(f"  Throughput: {throughput:.1f} req/s")
            
            # Validate endurance performance
            assert success_rate >= 0.95  # Very high success rate for endurance
            assert avg_response_time < 1.0  # Good average response time
            assert throughput > 2.0  # Sustained throughput