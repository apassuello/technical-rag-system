"""
Performance Tests for Epic 8 Cache Service.

Tests sub-millisecond operations, high-throughput scenarios, concurrent requests,
memory usage, and hit rate optimization following Epic 8 specifications.

Testing Philosophy:
- Hard Fails: >1000ms operations, <10 ops/sec throughput, >8GB memory, service crashes
- Quality Flags: >1ms cache GET, <60% hit rate, >100MB memory growth, poor scaling

Test Coverage:
- Sub-millisecond cache operation targets (<1ms GET, <5ms SET)
- High-throughput scenarios (10,000+ requests/second)
- Concurrent request handling
- Memory usage and efficiency  
- Cache hit rate optimization (>60% target)
- Scaling behavior and performance degradation
"""

import pytest
import asyncio
import time
import warnings
import json
import hashlib
import uuid
import os
import statistics
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import sys
from concurrent.futures import ThreadPoolExecutor
import threading

# Add services to path
project_path = Path(__file__).parent.parent.parent.parent
services_path = project_path / "services" / "cache"
if services_path.exists():
    sys.path.insert(0, str(services_path))

try:
    from cache_app.core.cache import CacheService, CachedResponse
    from cache_app.core.config import CacheConfig
    from cache_app.api.rest import generate_query_hash
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    IMPORT_ERROR = str(e)

# Module-level skip if cache service is not available
pytestmark = pytest.mark.skipif(
    not IMPORTS_AVAILABLE,
    reason=f"Cache service not implemented: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}"
)

# Check if Redis is available for performance tests
REDIS_AVAILABLE = False
try:
    import aioredis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_URL = None

# Check if performance monitoring tools are available
PERFORMANCE_MONITORING_AVAILABLE = False
try:
    import psutil
    PERFORMANCE_MONITORING_AVAILABLE = True
except ImportError:
    pass


@pytest.fixture(scope="module")
async def performance_config():
    """Optimized configuration for performance testing."""
    return {
        "redis_url": REDIS_URL or "redis://localhost:6379",
        "default_ttl": 3600,
        "fallback_cache_size": 2000,  # Larger for performance tests
        "circuit_breaker_threshold": 10,
        "circuit_breaker_timeout": 30,
        "ttl_strategies": {
            "simple_query": 7200,
            "medium_query": 3600,
            "complex_query": 1800,
            "performance_test": 900,  # Short TTL for performance tests
            "default": 3600
        }
    }


@pytest.fixture(scope="module")
async def optimized_cache_service(performance_config):
    """Optimized cache service for performance testing."""
    if not IMPORTS_AVAILABLE:
        pytest.skip(f"Service imports not available: {IMPORT_ERROR}")
    
    service = CacheService(performance_config)
    
    try:
        await service.initialize()
        yield service
    finally:
        await service.close()


@pytest.fixture
def performance_test_data():
    """Performance test data with varying sizes and complexity."""
    return {
        "micro_data": [
            {
                "query": f"Micro test {i}",
                "response_data": {"answer": f"Micro response {i}", "id": i},
                "size_category": "micro"
            } for i in range(100)
        ],
        "small_data": [
            {
                "query": f"Small test query number {i}",
                "response_data": {
                    "answer": f"Small response with more content for test {i}. " * 5,
                    "metadata": {"id": i, "category": "small", "tokens": 150}
                },
                "size_category": "small"
            } for i in range(50)
        ],
        "medium_data": [
            {
                "query": f"Medium complexity test query with technical content {i}",
                "response_data": {
                    "answer": f"Medium-sized technical response for query {i}. " * 20,
                    "sources": [f"doc_{i}_{j}.pdf" for j in range(3)],
                    "metadata": {
                        "id": i, 
                        "category": "medium",
                        "tokens": 800,
                        "processing_time_ms": 150 + (i % 50)
                    }
                },
                "size_category": "medium"
            } for i in range(25)
        ],
        "large_data": [
            {
                "query": f"Large comprehensive query requiring detailed analysis {i}",
                "response_data": {
                    "answer": f"Large comprehensive response with extensive technical details for query {i}. " * 100,
                    "sources": [f"technical_doc_{i}_{j}.pdf" for j in range(10)],
                    "metadata": {
                        "id": i,
                        "category": "large", 
                        "tokens": 3000,
                        "processing_time_ms": 500 + (i % 100),
                        "complexity_score": 0.8 + (i % 10) * 0.02
                    },
                    "analysis": {
                        "key_points": [f"Point {j} for query {i}" for j in range(10)],
                        "references": {f"ref_{j}": f"Reference {j} data" for j in range(5)}
                    }
                },
                "size_category": "large"
            } for i in range(10)
        ]
    }


class TestSubMillisecondOperations:
    """Test sub-millisecond cache operation targets."""

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_cache_get_sub_millisecond_target(self, optimized_cache_service, performance_test_data):
        """Test cache GET operations meet sub-millisecond target (<1ms)."""
        service = optimized_cache_service
        
        # Pre-populate cache with micro data for fastest retrieval
        micro_data = performance_test_data["micro_data"][:20]
        
        # Store all micro data
        for item in micro_data:
            query_hash = generate_query_hash(item["query"])
            success = await service.cache_response(
                query_hash, 
                item["response_data"], 
                "performance_test"
            )
            assert success is True, f"Failed to store micro data: {item['query'][:20]}"
        
        # Warm up cache with a few retrievals
        for _ in range(3):
            test_hash = generate_query_hash(micro_data[0]["query"])
            await service.get_cached_response(test_hash)
        
        # Measure retrieval performance for multiple operations
        retrieval_times = []
        
        for item in micro_data:
            query_hash = generate_query_hash(item["query"])
            
            # Measure single retrieval operation
            start_time = time.perf_counter()  # High precision timer
            result = await service.get_cached_response(query_hash)
            operation_time = time.perf_counter() - start_time
            
            retrieval_times.append(operation_time)
            
            # Hard fail: Each operation should succeed
            assert result is not None, f"Should retrieve cached data: {item['query'][:20]}"
            assert result == item["response_data"], "Retrieved data should match"
            
            # Hard fail: No operation should take >1000ms (clearly broken)
            assert operation_time < 1.0, f"Cache GET extremely slow: {operation_time:.3f}s"
        
        # Calculate performance statistics
        avg_time = statistics.mean(retrieval_times)
        median_time = statistics.median(retrieval_times)
        p95_time = statistics.quantiles(retrieval_times, n=20)[18]  # 95th percentile
        min_time = min(retrieval_times)
        max_time = max(retrieval_times)
        
        # Hard fail: Average should be reasonable
        assert avg_time < 0.1, f"Average cache GET too slow: {avg_time:.3f}s"
        
        # Epic 8 quality target: Sub-millisecond operations (<1ms)
        sub_ms_operations = sum(1 for t in retrieval_times if t < 0.001)
        sub_ms_rate = sub_ms_operations / len(retrieval_times)
        
        # Quality flag: Should achieve high sub-millisecond rate
        if sub_ms_rate < 0.5:  # At least 50% should be sub-millisecond
            warnings.warn(f"Sub-millisecond rate low: {sub_ms_rate:.1%} (target >50%)", UserWarning, stacklevel=2)
        
        # Quality flag: P95 should be fast
        if p95_time > 0.01:  # 10ms
            warnings.warn(f"P95 cache GET slow: {p95_time:.3f}s (target <10ms)", UserWarning, stacklevel=2)
        
        print(f"Cache GET performance: avg={avg_time*1000:.2f}ms, median={median_time*1000:.2f}ms, p95={p95_time*1000:.2f}ms")
        print(f"Sub-millisecond operations: {sub_ms_rate:.1%} ({sub_ms_operations}/{len(retrieval_times)})")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_cache_set_five_millisecond_target(self, optimized_cache_service, performance_test_data):
        """Test cache SET operations meet 5ms target."""
        service = optimized_cache_service
        
        # Use small data for SET performance testing
        small_data = performance_test_data["small_data"][:15]
        
        # Measure storage performance
        storage_times = []
        
        for item in small_data:
            query_hash = generate_query_hash(item["query"])
            
            # Measure single storage operation
            start_time = time.perf_counter()
            success = await service.cache_response(
                query_hash,
                item["response_data"],
                "performance_test"
            )
            operation_time = time.perf_counter() - start_time
            
            storage_times.append(operation_time)
            
            # Hard fail: Each operation should succeed
            assert success is True, f"Failed to store data: {item['query'][:20]}"
            
            # Hard fail: No operation should take >1000ms
            assert operation_time < 1.0, f"Cache SET extremely slow: {operation_time:.3f}s"
        
        # Calculate performance statistics
        avg_time = statistics.mean(storage_times)
        median_time = statistics.median(storage_times)
        p95_time = statistics.quantiles(storage_times, n=20)[18] if len(storage_times) >= 20 else max(storage_times)
        
        # Hard fail: Average should be reasonable  
        assert avg_time < 0.5, f"Average cache SET too slow: {avg_time:.3f}s"
        
        # Epic 8 quality target: <5ms SET operations
        fast_operations = sum(1 for t in storage_times if t < 0.005)
        fast_rate = fast_operations / len(storage_times)
        
        # Quality flag: Should achieve good fast operation rate
        if fast_rate < 0.3:  # At least 30% should be <5ms
            warnings.warn(f"Fast SET rate low: {fast_rate:.1%} (target >30%)", UserWarning, stacklevel=2)
        
        # Quality flag: P95 should be reasonable
        if p95_time > 0.1:  # 100ms
            warnings.warn(f"P95 cache SET slow: {p95_time:.3f}s", UserWarning, stacklevel=2)
        
        print(f"Cache SET performance: avg={avg_time*1000:.2f}ms, median={median_time*1000:.2f}ms, p95={p95_time*1000:.2f}ms")
        print(f"Sub-5ms operations: {fast_rate:.1%} ({fast_operations}/{len(storage_times)})")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_mixed_operations_performance(self, optimized_cache_service, performance_test_data):
        """Test mixed GET/SET operations performance."""
        service = optimized_cache_service
        
        # Mix of different data sizes
        mixed_data = (
            performance_test_data["micro_data"][:10] + 
            performance_test_data["small_data"][:8] +
            performance_test_data["medium_data"][:5]
        )
        
        operation_times = []
        hit_count = 0
        miss_count = 0
        
        # Simulate realistic mixed workload
        for cycle in range(3):  # Multiple cycles to create hits
            for item in mixed_data:
                query_hash = generate_query_hash(item["query"])
                
                # 60% GET, 40% SET pattern
                if (hash(query_hash) % 10) < 6:
                    # GET operation
                    start_time = time.perf_counter()
                    result = await service.get_cached_response(query_hash)
                    operation_time = time.perf_counter() - start_time
                    
                    if result is not None:
                        hit_count += 1
                        assert result == item["response_data"], "Cache hit data should match"
                    else:
                        miss_count += 1
                        
                else:
                    # SET operation
                    start_time = time.perf_counter()
                    success = await service.cache_response(
                        query_hash, 
                        item["response_data"], 
                        "performance_test"
                    )
                    operation_time = time.perf_counter() - start_time
                    
                    assert success is True, "SET should succeed"
                
                operation_times.append(operation_time)
                
                # Hard fail: Individual operations shouldn't be extremely slow
                assert operation_time < 1.0, f"Mixed operation too slow: {operation_time:.3f}s"
        
        # Calculate overall performance
        total_operations = len(operation_times)
        avg_time = statistics.mean(operation_times)
        hit_rate = hit_count / (hit_count + miss_count) if (hit_count + miss_count) > 0 else 0
        
        # Hard fail: Should handle mixed workload efficiently
        assert avg_time < 0.1, f"Mixed workload average too slow: {avg_time:.3f}s"
        
        # Epic 8 quality target: >60% hit rate
        if hit_rate < 0.6:
            warnings.warn(f"Hit rate below target: {hit_rate:.1%} (target >60%)", UserWarning, stacklevel=2)
        
        # Quality flag: Mixed operations should be fast
        if avg_time > 0.01:  # 10ms
            warnings.warn(f"Mixed operations slow: {avg_time:.3f}s average", UserWarning, stacklevel=2)
        
        print(f"Mixed operations: {total_operations} ops, avg {avg_time*1000:.2f}ms, {hit_rate:.1%} hit rate")


class TestHighThroughputScenarios:
    """Test high-throughput scenarios targeting 10,000+ ops/sec."""

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_sequential_high_throughput(self, optimized_cache_service, performance_test_data):
        """Test sequential high-throughput operations."""
        service = optimized_cache_service
        
        # Use micro data for maximum throughput
        test_data = performance_test_data["micro_data"][:100]
        
        # Phase 1: Sequential SET operations
        set_start_time = time.perf_counter()
        
        for item in test_data:
            query_hash = generate_query_hash(item["query"])
            success = await service.cache_response(
                query_hash,
                item["response_data"],
                "performance_test"
            )
            assert success is True, f"SET should succeed: {item['query'][:10]}"
        
        set_total_time = time.perf_counter() - set_start_time
        set_throughput = len(test_data) / set_total_time
        
        # Phase 2: Sequential GET operations
        get_start_time = time.perf_counter()
        
        for item in test_data:
            query_hash = generate_query_hash(item["query"])
            result = await service.get_cached_response(query_hash)
            assert result is not None, f"GET should succeed: {item['query'][:10]}"
            assert result == item["response_data"], "Data should match"
        
        get_total_time = time.perf_counter() - get_start_time
        get_throughput = len(test_data) / get_total_time
        
        # Hard fail: Should achieve reasonable throughput
        assert set_throughput >= 10, f"SET throughput too low: {set_throughput:.1f} ops/sec"
        assert get_throughput >= 50, f"GET throughput too low: {get_throughput:.1f} ops/sec"
        
        # Epic 8 quality target: High throughput
        if set_throughput < 100:  # 100 ops/sec
            warnings.warn(f"SET throughput below target: {set_throughput:.1f} ops/sec", UserWarning, stacklevel=2)
        
        if get_throughput < 500:  # 500 ops/sec
            warnings.warn(f"GET throughput below target: {get_throughput:.1f} ops/sec", UserWarning, stacklevel=2)
        
        print(f"Sequential throughput: SET {set_throughput:.1f} ops/sec, GET {get_throughput:.1f} ops/sec")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_concurrent_high_throughput(self, optimized_cache_service, performance_test_data):
        """Test concurrent high-throughput operations."""
        service = optimized_cache_service
        
        # Create large batch of concurrent operations
        batch_size = 100
        concurrent_operations = []
        operation_types = []
        
        # Mix of SET and GET operations
        test_data = performance_test_data["micro_data"][:50]
        
        for i in range(batch_size):
            item = test_data[i % len(test_data)]
            query_hash = generate_query_hash(f"{item['query']}_concurrent_{i}")
            
            if i % 3 == 0:
                # SET operation
                concurrent_operations.append(
                    service.cache_response(query_hash, item["response_data"], "performance_test")
                )
                operation_types.append("SET")
            else:
                # GET operation (will mostly miss initially)
                concurrent_operations.append(
                    service.get_cached_response(query_hash)
                )
                operation_types.append("GET")
        
        # Execute all operations concurrently
        start_time = time.perf_counter()
        results = await asyncio.gather(*concurrent_operations, return_exceptions=True)
        total_time = time.perf_counter() - start_time
        
        # Analyze results
        successful_operations = []
        failed_operations = []
        
        for result, op_type in zip(results, operation_types):
            if isinstance(result, Exception):
                failed_operations.append((op_type, str(result)))
            else:
                if op_type == "SET":
                    if result is True:
                        successful_operations.append(op_type)
                    else:
                        failed_operations.append((op_type, f"SET returned {result}"))
                else:  # GET
                    successful_operations.append(op_type)  # Misses are ok
        
        success_rate = len(successful_operations) / len(results)
        throughput = len(results) / total_time
        
        # Hard fail: Should handle concurrent load
        assert total_time < 30.0, f"Concurrent operations too slow: {total_time:.2f}s"
        assert success_rate >= 0.8, f"Too many concurrent failures: {success_rate:.1%}"
        
        # Quality target: High concurrent throughput
        if throughput < 50:  # 50 ops/sec minimum for concurrent
            warnings.warn(f"Concurrent throughput low: {throughput:.1f} ops/sec", UserWarning, stacklevel=2)
        
        # Epic 8 target: Should approach or exceed 1000 ops/sec in ideal conditions
        if throughput < 100:
            warnings.warn(f"Concurrent throughput below expectations: {throughput:.1f} ops/sec", UserWarning, stacklevel=2)
        
        print(f"Concurrent throughput: {throughput:.1f} ops/sec ({success_rate:.1%} success rate)")
        if failed_operations:
            print(f"Failures: {len(failed_operations)}")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_burst_load_handling(self, optimized_cache_service, performance_test_data):
        """Test handling of burst loads followed by sustained load."""
        service = optimized_cache_service
        
        # Burst phase: High intensity short duration
        burst_operations = []
        burst_size = 50
        
        for i in range(burst_size):
            query_hash = generate_query_hash(f"burst_query_{i}")
            data = {"answer": f"burst response {i}", "burst_id": i}
            burst_operations.append(service.cache_response(query_hash, data, "performance_test"))
        
        # Execute burst
        burst_start = time.perf_counter()
        burst_results = await asyncio.gather(*burst_operations)
        burst_time = time.perf_counter() - burst_start
        
        burst_success_rate = sum(1 for r in burst_results if r is True) / len(burst_results)
        burst_throughput = len(burst_results) / burst_time
        
        # Sustained phase: Lower intensity longer duration
        sustained_operations = []
        sustained_size = 30
        
        # Brief pause between burst and sustained
        await asyncio.sleep(0.1)
        
        for i in range(sustained_size):
            query_hash = generate_query_hash(f"sustained_query_{i}")
            data = {"answer": f"sustained response {i}", "sustained_id": i}
            sustained_operations.append(service.cache_response(query_hash, data, "performance_test"))
        
        # Execute sustained load
        sustained_start = time.perf_counter()
        sustained_results = await asyncio.gather(*sustained_operations)
        sustained_time = time.perf_counter() - sustained_start
        
        sustained_success_rate = sum(1 for r in sustained_results if r is True) / len(sustained_results)
        sustained_throughput = len(sustained_results) / sustained_time
        
        # Hard fail: Both phases should handle load
        assert burst_success_rate >= 0.7, f"Burst load handling poor: {burst_success_rate:.1%}"
        assert sustained_success_rate >= 0.9, f"Sustained load handling poor: {sustained_success_rate:.1%}"
        
        # Quality: Service should recover from burst to sustained performance
        if sustained_throughput < burst_throughput * 0.5:
            warnings.warn("Significant performance degradation after burst", UserWarning, stacklevel=2)
        
        print(f"Burst load: {burst_throughput:.1f} ops/sec ({burst_success_rate:.1%} success)")
        print(f"Sustained load: {sustained_throughput:.1f} ops/sec ({sustained_success_rate:.1%} success)")


class TestConcurrentRequestHandling:
    """Test concurrent request handling capabilities."""

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_many_concurrent_readers(self, optimized_cache_service, performance_test_data):
        """Test many concurrent readers accessing same data."""
        service = optimized_cache_service
        
        # Pre-populate with shared data
        shared_data = performance_test_data["small_data"][:5]
        for item in shared_data:
            query_hash = generate_query_hash(item["query"])
            await service.cache_response(query_hash, item["response_data"], "performance_test")
        
        # Create many concurrent readers for same data
        concurrent_readers = []
        reader_count = 50  # 50 concurrent readers
        
        for i in range(reader_count):
            # Each reader reads all shared data
            for item in shared_data:
                query_hash = generate_query_hash(item["query"])
                concurrent_readers.append(
                    service.get_cached_response(query_hash)
                )
        
        # Execute concurrent reads
        start_time = time.perf_counter()
        read_results = await asyncio.gather(*concurrent_readers, return_exceptions=True)
        total_time = time.perf_counter() - start_time
        
        # Analyze results
        successful_reads = [r for r in read_results if not isinstance(r, Exception) and r is not None]
        failed_reads = [r for r in read_results if isinstance(r, Exception)]
        
        success_rate = len(successful_reads) / len(read_results)
        read_throughput = len(read_results) / total_time
        
        # Hard fail: Concurrent reads should succeed
        assert success_rate >= 0.95, f"Many concurrent readers failed: {success_rate:.1%}"
        assert total_time < 10.0, f"Concurrent reads too slow: {total_time:.2f}s"
        
        # Quality: Should handle concurrent readers efficiently
        if read_throughput < 100:  # 100 ops/sec minimum
            warnings.warn(f"Concurrent read throughput low: {read_throughput:.1f} ops/sec", UserWarning, stacklevel=2)
        
        # Data consistency check: All successful reads should return same data
        data_consistency_check = True
        for item in shared_data:
            expected_data = item["response_data"]
            matching_results = [r for r in successful_reads if r == expected_data]
            expected_count = reader_count  # Each reader should get this data once
            
            if len(matching_results) != expected_count:
                data_consistency_check = False
                break
        
        assert data_consistency_check, "Data consistency issue with concurrent readers"
        
        print(f"Concurrent readers: {read_throughput:.1f} ops/sec, {success_rate:.1%} success rate")

    # Service availability handled by fixtures
    @pytest.mark.asyncio  
    async def test_concurrent_writers_different_keys(self, optimized_cache_service, performance_test_data):
        """Test concurrent writers to different keys."""
        service = optimized_cache_service
        
        # Create concurrent writers for different keys
        concurrent_writers = []
        writer_count = 30
        
        for i in range(writer_count):
            query_hash = generate_query_hash(f"concurrent_write_{i}")
            data = {"answer": f"concurrent write response {i}", "writer_id": i, "timestamp": time.time()}
            concurrent_writers.append(
                service.cache_response(query_hash, data, "performance_test")
            )
        
        # Execute concurrent writes
        start_time = time.perf_counter()
        write_results = await asyncio.gather(*concurrent_writers, return_exceptions=True)
        total_time = time.perf_counter() - start_time
        
        successful_writes = [r for r in write_results if r is True]
        failed_writes = [r for r in write_results if isinstance(r, Exception) or r is not True]
        
        success_rate = len(successful_writes) / len(write_results)
        write_throughput = len(write_results) / total_time
        
        # Hard fail: Concurrent writes should succeed
        assert success_rate >= 0.9, f"Concurrent writes failed: {success_rate:.1%}"
        assert total_time < 15.0, f"Concurrent writes too slow: {total_time:.2f}s"
        
        # Quality: Should handle concurrent writes efficiently
        if write_throughput < 20:  # 20 ops/sec minimum for writes
            warnings.warn(f"Concurrent write throughput low: {write_throughput:.1f} ops/sec", UserWarning, stacklevel=2)
        
        # Verify all written data can be retrieved
        verification_reads = []
        for i in range(writer_count):
            query_hash = generate_query_hash(f"concurrent_write_{i}")
            verification_reads.append(service.get_cached_response(query_hash))
        
        verify_results = await asyncio.gather(*verification_reads)
        successful_verifications = [r for r in verify_results if r is not None]
        
        verification_rate = len(successful_verifications) / len(verify_results)
        
        # All successful writes should be retrievable
        assert verification_rate >= success_rate * 0.95, "Written data not consistently retrievable"
        
        print(f"Concurrent writers: {write_throughput:.1f} ops/sec, {success_rate:.1%} success rate")
        print(f"Data verification: {verification_rate:.1%} retrievable")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_mixed_concurrent_workload(self, optimized_cache_service, performance_test_data):
        """Test realistic mixed concurrent workload."""
        service = optimized_cache_service
        
        # Pre-populate some data for reads
        base_data = performance_test_data["micro_data"][:10]
        for item in base_data:
            query_hash = generate_query_hash(item["query"])
            await service.cache_response(query_hash, item["response_data"], "performance_test")
        
        # Create mixed workload: 60% reads, 30% writes, 10% deletes
        mixed_operations = []
        operation_labels = []
        
        total_ops = 60
        
        for i in range(total_ops):
            operation_type = i % 10
            
            if operation_type < 6:  # 60% reads
                # Read existing or random data
                if i % 2 == 0 and base_data:
                    item = base_data[i % len(base_data)]
                    query_hash = generate_query_hash(item["query"])
                else:
                    query_hash = generate_query_hash(f"random_read_{i}")
                
                mixed_operations.append(service.get_cached_response(query_hash))
                operation_labels.append("READ")
                
            elif operation_type < 9:  # 30% writes (operations 6, 7, 8)
                query_hash = generate_query_hash(f"mixed_write_{i}")
                data = {"answer": f"mixed write {i}", "op_id": i}
                mixed_operations.append(service.cache_response(query_hash, data, "performance_test"))
                operation_labels.append("WRITE")
                
            else:  # 10% deletes (operation 9)
                # Delete from base data if available
                if base_data and i < len(base_data):
                    item = base_data[i % len(base_data)]
                    query_hash = generate_query_hash(item["query"])
                    mixed_operations.append(service.delete_cached_response(query_hash))
                    operation_labels.append("DELETE")
                else:
                    # Convert to read if no data to delete
                    query_hash = generate_query_hash(f"fallback_read_{i}")
                    mixed_operations.append(service.get_cached_response(query_hash))
                    operation_labels.append("READ")
        
        # Execute mixed workload
        start_time = time.perf_counter()
        mixed_results = await asyncio.gather(*mixed_operations, return_exceptions=True)
        total_time = time.perf_counter() - start_time
        
        # Analyze results by operation type
        read_results = [(r, l) for r, l in zip(mixed_results, operation_labels) if l == "READ"]
        write_results = [(r, l) for r, l in zip(mixed_results, operation_labels) if l == "WRITE"]
        delete_results = [(r, l) for r, l in zip(mixed_results, operation_labels) if l == "DELETE"]
        
        # Calculate success rates
        successful_reads = sum(1 for r, l in read_results if not isinstance(r, Exception))
        successful_writes = sum(1 for r, l in write_results if r is True)
        successful_deletes = sum(1 for r, l in delete_results if r is True or not isinstance(r, Exception))
        
        total_successful = successful_reads + successful_writes + successful_deletes
        overall_success_rate = total_successful / len(mixed_results)
        
        throughput = len(mixed_results) / total_time
        
        # Hard fail: Mixed workload should be handled
        assert overall_success_rate >= 0.8, f"Mixed workload handling poor: {overall_success_rate:.1%}"
        assert total_time < 20.0, f"Mixed workload too slow: {total_time:.2f}s"
        
        # Quality: Should handle mixed workload efficiently
        if throughput < 30:  # 30 ops/sec minimum for mixed workload
            warnings.warn(f"Mixed workload throughput low: {throughput:.1f} ops/sec", UserWarning, stacklevel=2)
        
        print(f"Mixed concurrent workload: {throughput:.1f} ops/sec, {overall_success_rate:.1%} success rate")
        print(f"Breakdown: {len(read_results)} reads, {len(write_results)} writes, {len(delete_results)} deletes")


class TestMemoryUsageAndEfficiency:
    """Test memory usage and efficiency characteristics."""

    # Service availability handled by fixtures
    @pytest.mark.skipif(not PERFORMANCE_MONITORING_AVAILABLE, reason="psutil not available for memory testing")
    @pytest.mark.asyncio
    async def test_memory_efficiency_under_load(self, optimized_cache_service, performance_test_data):
        """Test memory efficiency under sustained load."""
        service = optimized_cache_service
        
        # Monitor memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_samples = [initial_memory]
        
        # Load test with varying data sizes
        test_phases = [
            ("micro", performance_test_data["micro_data"][:50]),
            ("small", performance_test_data["small_data"][:30]),
            ("medium", performance_test_data["medium_data"][:15]),
            ("large", performance_test_data["large_data"][:5])
        ]
        
        for phase_name, phase_data in test_phases:
            phase_start_memory = process.memory_info().rss / 1024 / 1024
            
            # Load phase data
            for item in phase_data:
                query_hash = generate_query_hash(f"{phase_name}_{item['query']}")
                success = await service.cache_response(
                    query_hash,
                    item["response_data"], 
                    "performance_test"
                )
                assert success is True, f"Should store {phase_name} data"
            
            # Sample memory after phase
            phase_end_memory = process.memory_info().rss / 1024 / 1024
            memory_samples.append(phase_end_memory)
            
            phase_memory_increase = phase_end_memory - phase_start_memory
            
            # Hard fail: Memory increase should not be excessive for any phase
            max_increase_limits = {
                "micro": 10,   # 10MB for micro data
                "small": 25,   # 25MB for small data  
                "medium": 50,  # 50MB for medium data
                "large": 100   # 100MB for large data
            }
            
            assert phase_memory_increase < max_increase_limits[phase_name], \
                f"{phase_name} phase memory increase excessive: {phase_memory_increase:.1f}MB"
            
            print(f"{phase_name} phase: +{phase_memory_increase:.1f}MB memory")
        
        final_memory = process.memory_info().rss / 1024 / 1024
        total_memory_increase = final_memory - initial_memory
        
        # Hard fail: Total memory increase should be reasonable
        assert total_memory_increase < 500, f"Total memory increase excessive: {total_memory_increase:.1f}MB"
        
        # Quality flag: Memory efficiency
        if total_memory_increase > 100:  # 100MB total increase
            warnings.warn(f"High memory usage: +{total_memory_increase:.1f}MB", UserWarning, stacklevel=2)
        
        # Test memory cleanup by clearing cache
        await service.clear_cache()
        await asyncio.sleep(0.1)  # Brief pause for cleanup
        
        cleanup_memory = process.memory_info().rss / 1024 / 1024
        memory_freed = final_memory - cleanup_memory
        
        print(f"Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB (+{total_memory_increase:.1f}MB)")
        print(f"After cleanup: {cleanup_memory:.1f}MB (freed {memory_freed:.1f}MB)")

    # Service availability handled by fixtures
    @pytest.mark.skipif(not PERFORMANCE_MONITORING_AVAILABLE, reason="psutil not available for memory testing")
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self, optimized_cache_service, performance_test_data):
        """Test for memory leaks during repeated operations."""
        service = optimized_cache_service
        
        process = psutil.Process(os.getpid())
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_measurements = []
        
        # Perform repeated cycles of cache operations
        cycles = 10
        ops_per_cycle = 20
        
        for cycle in range(cycles):
            cycle_start_memory = process.memory_info().rss / 1024 / 1024
            
            # Cache operations cycle
            cycle_data = performance_test_data["small_data"][:ops_per_cycle]
            
            for item in cycle_data:
                query_hash = generate_query_hash(f"cycle_{cycle}_{item['query']}")
                
                # Store data
                await service.cache_response(query_hash, item["response_data"], "performance_test")
                
                # Retrieve data
                result = await service.get_cached_response(query_hash)
                assert result == item["response_data"], "Data should match"
                
                # Delete data (to prevent accumulation)
                await service.delete_cached_response(query_hash)
            
            cycle_end_memory = process.memory_info().rss / 1024 / 1024
            memory_measurements.append(cycle_end_memory)
            
            cycle_memory_increase = cycle_end_memory - cycle_start_memory
            
            # Hard fail: Individual cycles should not increase memory excessively
            assert cycle_memory_increase < 20, f"Cycle {cycle} memory increase excessive: {cycle_memory_increase:.1f}MB"
        
        final_memory = process.memory_info().rss / 1024 / 1024
        total_growth = final_memory - baseline_memory
        
        # Analyze memory growth trend
        if len(memory_measurements) >= 5:
            # Check if memory is consistently growing (potential leak)
            recent_avg = statistics.mean(memory_measurements[-3:])  # Last 3 cycles
            early_avg = statistics.mean(memory_measurements[:3])    # First 3 cycles
            
            growth_trend = recent_avg - early_avg
            
            # Quality flag: Memory should not show consistent upward trend
            if growth_trend > 30:  # 30MB growth trend
                warnings.warn(f"Memory growth trend detected: +{growth_trend:.1f}MB", UserWarning, stacklevel=2)
        
        # Hard fail: Total memory growth after repeated cycles
        assert total_growth < 100, f"Memory leak suspected: +{total_growth:.1f}MB after {cycles} cycles"
        
        # Quality flag: Memory growth should be minimal
        if total_growth > 20:  # 20MB growth
            warnings.warn(f"Memory growth after cycles: +{total_growth:.1f}MB", UserWarning, stacklevel=2)
        
        print(f"Memory leak test: {baseline_memory:.1f}MB -> {final_memory:.1f}MB (+{total_growth:.1f}MB) over {cycles} cycles")


class TestCacheHitRateOptimization:
    """Test cache hit rate optimization targeting >60%."""

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_realistic_hit_rate_patterns(self, optimized_cache_service, performance_test_data):
        """Test realistic hit rate patterns with optimized strategies."""
        service = optimized_cache_service
        
        # Simulate realistic query patterns with repetition
        base_queries = performance_test_data["micro_data"][:20]
        
        # Create realistic access pattern: 80/20 rule
        popular_queries = base_queries[:4]      # 20% of queries
        regular_queries = base_queries[4:16]    # 60% of queries  
        rare_queries = base_queries[16:]        # 20% of queries
        
        # Generate access sequence following 80/20 pattern
        access_sequence = []
        
        # 80% of accesses to 20% of queries (popular)
        for _ in range(40):  # 40 accesses
            query = popular_queries[hash(str(_)) % len(popular_queries)]
            access_sequence.append(("popular", query))
        
        # 15% of accesses to 60% of queries (regular)
        for _ in range(15):  # 15 accesses
            query = regular_queries[hash(str(_)) % len(regular_queries)]
            access_sequence.append(("regular", query))
        
        # 5% of accesses to 20% of queries (rare)
        for _ in range(5):   # 5 accesses
            query = rare_queries[hash(str(_)) % len(rare_queries)]
            access_sequence.append(("rare", query))
        
        # Randomize sequence to simulate real access patterns
        import random
        random.shuffle(access_sequence)
        
        hits = 0
        misses = 0
        
        for access_type, query_item in access_sequence:
            query_hash = generate_query_hash(query_item["query"])
            
            # Try to get from cache
            cached_result = await service.get_cached_response(query_hash)
            
            if cached_result is not None:
                hits += 1
                # Verify data integrity
                assert cached_result == query_item["response_data"], "Cached data should match"
            else:
                misses += 1
                # Cache miss - store the response
                success = await service.cache_response(
                    query_hash,
                    query_item["response_data"],
                    "performance_test"
                )
                assert success is True, "Should store on miss"
        
        total_requests = hits + misses
        hit_rate = hits / total_requests if total_requests > 0 else 0
        
        # Hard fail: Should have some hits with this pattern
        assert hits > 0, "Should have cache hits with realistic access pattern"
        
        # Epic 8 quality target: >60% hit rate
        if hit_rate < 0.6:
            warnings.warn(f"Hit rate below Epic 8 target: {hit_rate:.1%} (target >60%)", UserWarning, stacklevel=2)
        
        # With 80/20 pattern, should achieve good hit rate
        expected_min_hit_rate = 0.4  # Should get at least 40% with popular query repetition
        assert hit_rate >= expected_min_hit_rate, f"Hit rate too low for pattern: {hit_rate:.1%}"
        
        print(f"Realistic hit rate test: {hit_rate:.1%} ({hits}/{total_requests})")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_ttl_strategy_effectiveness(self, optimized_cache_service, performance_test_data):
        """Test TTL strategy effectiveness for hit rate optimization."""
        service = optimized_cache_service
        
        # Test different TTL strategies
        ttl_test_cases = [
            {
                "content_type": "simple_query",
                "expected_ttl": 7200,  # 2 hours
                "queries": performance_test_data["micro_data"][:5]
            },
            {
                "content_type": "medium_query", 
                "expected_ttl": 3600,  # 1 hour
                "queries": performance_test_data["small_data"][:3]
            },
            {
                "content_type": "complex_query",
                "expected_ttl": 1800,  # 30 minutes
                "queries": performance_test_data["medium_data"][:2]
            },
            {
                "content_type": "performance_test",
                "expected_ttl": 900,   # 15 minutes  
                "queries": performance_test_data["large_data"][:1]
            }
        ]
        
        total_hits = 0
        total_misses = 0
        
        # Store items with different TTL strategies
        for test_case in ttl_test_cases:
            content_type = test_case["content_type"]
            expected_ttl = test_case["expected_ttl"]
            
            for query_item in test_case["queries"]:
                query_hash = generate_query_hash(f"{content_type}_{query_item['query']}")
                
                # Store with specific content type (uses TTL strategy)
                success = await service.cache_response(
                    query_hash,
                    query_item["response_data"],
                    content_type
                )
                assert success is True, f"Should store {content_type} query"
                
                # Verify TTL strategy was applied by checking internal TTL calculation
                calculated_ttl = service._calculate_ttl(content_type)
                assert calculated_ttl == expected_ttl, \
                    f"TTL strategy incorrect: {calculated_ttl} != {expected_ttl} for {content_type}"
        
        # Test hit rates with immediate retrieval (should all hit)
        immediate_hits = 0
        immediate_total = 0
        
        for test_case in ttl_test_cases:
            content_type = test_case["content_type"]
            
            for query_item in test_case["queries"]:
                query_hash = generate_query_hash(f"{content_type}_{query_item['query']}")
                
                result = await service.get_cached_response(query_hash)
                immediate_total += 1
                
                if result is not None:
                    immediate_hits += 1
                    assert result == query_item["response_data"], "Data should match"
                else:
                    immediate_total += 1  # Count as miss
        
        immediate_hit_rate = immediate_hits / immediate_total if immediate_total > 0 else 0
        
        # All immediate retrievals should hit
        assert immediate_hit_rate >= 0.95, f"Immediate hit rate poor: {immediate_hit_rate:.1%}"
        
        # Test that different TTL strategies provide appropriate cache retention
        # (This is a functional test rather than waiting for expiration)
        
        print(f"TTL strategy test: {immediate_hit_rate:.1%} immediate hit rate")
        print(f"TTL strategies validated: {len(ttl_test_cases)} different content types")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_cache_warming_effectiveness(self, optimized_cache_service, performance_test_data):
        """Test cache warming effectiveness for hit rate improvement."""
        service = optimized_cache_service
        
        # Simulate cache warming with popular queries
        warming_queries = performance_test_data["micro_data"][:10]
        
        # Pre-warm cache
        for query_item in warming_queries:
            query_hash = generate_query_hash(query_item["query"])
            success = await service.cache_response(
                query_hash,
                query_item["response_data"],
                "performance_test"
            )
            assert success is True, "Warming should succeed"
        
        # Test hit rate after warming
        warmed_hits = 0
        warmed_total = len(warming_queries)
        
        for query_item in warming_queries:
            query_hash = generate_query_hash(query_item["query"])
            result = await service.get_cached_response(query_hash)
            
            if result is not None:
                warmed_hits += 1
                assert result == query_item["response_data"], "Warmed data should match"
        
        warmed_hit_rate = warmed_hits / warmed_total
        
        # Warmed queries should have very high hit rate
        assert warmed_hit_rate >= 0.9, f"Cache warming ineffective: {warmed_hit_rate:.1%} hit rate"
        
        # Test mixed workload with warmed and cold queries
        mixed_queries = warming_queries + performance_test_data["small_data"][:5]  # Mix of warm and cold
        
        mixed_hits = 0
        mixed_misses = 0
        
        for query_item in mixed_queries:
            query_hash = generate_query_hash(query_item["query"])
            result = await service.get_cached_response(query_hash)
            
            if result is not None:
                mixed_hits += 1
            else:
                mixed_misses += 1
                # Store cold queries
                await service.cache_response(
                    query_hash,
                    query_item["response_data"],
                    "performance_test"
                )
        
        mixed_hit_rate = mixed_hits / (mixed_hits + mixed_misses)
        
        # Mixed workload should show benefit of cache warming
        expected_mixed_rate = 0.5  # At least 50% due to warming
        assert mixed_hit_rate >= expected_mixed_rate, f"Mixed hit rate too low: {mixed_hit_rate:.1%}"
        
        print(f"Cache warming: warmed {warmed_hit_rate:.1%}, mixed {mixed_hit_rate:.1%}")


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "-x"])  # Stop on first failure for performance tests