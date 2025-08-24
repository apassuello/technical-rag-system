"""
Integration Tests for Epic 8 Cache Service.

Tests Redis integration with real Redis instance, cache hit/miss scenarios,
performance under different loads, API Gateway integration, and cache invalidation
following Epic 8 specifications.

Testing Philosophy:
- Hard Fails: Complete service failure, >60s responses, Redis connectivity loss, data corruption
- Quality Flags: <60% hit rate, >10ms Redis operations, memory leaks, poor integration

Test Coverage:
- Redis integration with real Redis instance
- Cache hit/miss scenarios with realistic data
- Performance under different loads
- Integration with API Gateway service
- Cache invalidation and TTL behavior
- Service resilience and failover
"""

import pytest
import pytest_asyncio
import asyncio
import time
import json
import hashlib
import uuid
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Add services to path
services_path = Path(__file__).parent.parent.parent.parent / "services" / "cache"
if services_path.exists():
    sys.path.insert(0, str(services_path))

try:
    from cache_app.core.cache import CacheService, CachedResponse
    from cache_app.core.config import CacheConfig
    from cache_app.main import create_app
    from cache_app.api.rest import generate_query_hash
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    IMPORT_ERROR = str(e)

# Check if Redis is available for integration tests
REDIS_AVAILABLE = False
try:
    import redis.asyncio as redis
    # Try connecting to Redis for integration tests
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_URL = None


@pytest_asyncio.fixture(scope="module")
async def redis_integration_config():
    """Configuration for Redis integration testing."""
    return {
        "redis_url": REDIS_URL or "redis://localhost:6379",
        "default_ttl": 3600,
        "fallback_cache_size": 1000,
        "circuit_breaker_threshold": 5,
        "circuit_breaker_timeout": 30,
        "ttl_strategies": {
            "simple_query": 7200,
            "medium_query": 3600,
            "complex_query": 1800,
            "default": 3600
        }
    }


@pytest_asyncio.fixture(scope="module")
async def cache_service_with_redis(redis_integration_config):
    """Cache service with real Redis connection for integration testing."""
    if not IMPORTS_AVAILABLE:
        pytest.skip(f"Service imports not available: {IMPORT_ERROR}")
    
    if not REDIS_AVAILABLE:
        pytest.skip("Redis not available for integration tests")
    
    service = CacheService(redis_integration_config)
    
    try:
        await service.initialize()
        
        # Test Redis connection
        if service.redis:
            await service.redis.ping()
            print("Redis connection established for integration testing")
        else:
            pytest.skip("Could not establish Redis connection")
        
        yield service
        
    except Exception as e:
        pytest.skip(f"Redis connection failed: {e}")
    
    finally:
        await service.close()


@pytest.fixture
def integration_test_data():
    """Comprehensive test data for integration testing."""
    return {
        "realistic_queries": [
            {
                "query": "What are the key features of RISC-V instruction set architecture?",
                "response_data": {
                    "answer": "RISC-V is an open-source instruction set architecture (ISA) with key features including: 1) Modular design with base integer ISA and optional extensions, 2) Simple and regular instruction format, 3) Large 32-register design, 4) Clean separation of user and privileged architecture, 5) Stable base and frozen standard.",
                    "confidence": 0.92,
                    "sources": ["risc-v-spec-20191213.pdf", "risc-v-privileged-20211203.pdf"],
                    "metadata": {
                        "tokens": 487,
                        "model": "technical-docs-v2",
                        "processing_time_ms": 234,
                        "categories": ["computer-architecture", "instruction-sets"]
                    }
                },
                "content_type": "medium_query",
                "expected_ttl": 3600
            },
            {
                "query": "How does cache coherency work in multi-core processors?",
                "response_data": {
                    "answer": "Cache coherency in multi-core processors ensures all cores see a consistent view of memory through protocols like MESI (Modified, Exclusive, Shared, Invalid). When one core modifies cached data, the protocol invalidates or updates copies in other caches. This involves cache-to-cache transfers, bus snooping, and directory-based schemes in larger systems.",
                    "confidence": 0.89,
                    "sources": ["computer-architecture-textbook.pdf", "cache-coherency-protocols.pdf"],
                    "metadata": {
                        "tokens": 612,
                        "model": "complex-technical-v1",
                        "processing_time_ms": 456,
                        "categories": ["computer-architecture", "memory-systems", "parallel-computing"]
                    }
                },
                "content_type": "complex_query",
                "expected_ttl": 1800
            },
            {
                "query": "What is a CPU?",
                "response_data": {
                    "answer": "A CPU (Central Processing Unit) is the primary component of a computer that performs most processing tasks by executing instructions and managing data flow.",
                    "confidence": 0.98,
                    "sources": ["basic-computing-guide.pdf"],
                    "metadata": {
                        "tokens": 89,
                        "model": "simple-qa-v1",
                        "processing_time_ms": 67,
                        "categories": ["basic-computing"]
                    }
                },
                "content_type": "simple_query",
                "expected_ttl": 7200
            }
        ],
        "load_test_queries": [
            {
                "query": f"Load test query {i}",
                "response_data": {
                    "answer": f"This is load test response number {i} with sufficient content to test realistic cache storage and retrieval performance under load conditions.",
                    "confidence": 0.85,
                    "metadata": {"index": i, "test_type": "load_test"}
                },
                "content_type": "simple_query"
            } for i in range(100)
        ]
    }


class TestRedisIntegration:
    """Test Redis integration functionality."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not available for integration tests")
    @pytest.mark.asyncio
    async def test_redis_connection_establishment(self, cache_service_with_redis):
        """Test Redis connection establishment and basic operations (Hard Fail test)."""
        service = cache_service_with_redis
        
        try:
            # Redis should be connected
            assert service.redis is not None, "Redis should be connected for integration test"
            assert not service._is_circuit_breaker_open(), "Circuit breaker should be closed"
            
            # Test basic Redis ping
            start_time = time.time()
            pong = await service.redis.ping()
            ping_time = time.time() - start_time
            
            # Hard fail: Redis ping should work
            assert pong is True, "Redis ping should return True"
            
            # Quality flag: Redis ping should be fast
            if ping_time > 0.01:  # 10ms
                pytest.warns(UserWarning, f"Redis ping slow: {ping_time:.3f}s (target <10ms)")
            
            print(f"Redis ping successful: {ping_time*1000:.2f}ms")
            
        except Exception as e:
            pytest.fail(f"Redis connection test failed: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not available for integration tests")
    @pytest.mark.asyncio
    async def test_redis_cache_operations_basic(self, cache_service_with_redis, integration_test_data):
        """Test basic Redis cache operations with real Redis."""
        service = cache_service_with_redis
        
        # Use realistic query data
        query_data = integration_test_data["realistic_queries"][0]
        query_hash = generate_query_hash(query_data["query"])
        
        # Test cache storage to Redis
        start_time = time.time()
        success = await service.cache_response(
            query_hash=query_hash,
            response_data=query_data["response_data"],
            content_type=query_data["content_type"]
        )
        store_time = time.time() - start_time
        
        # Hard fail: Storage should succeed
        assert success is True, "Redis cache storage should succeed"
        
        # Quality flag: Should be reasonably fast
        if store_time > 0.05:  # 50ms
            pytest.warns(UserWarning, f"Redis cache store slow: {store_time:.3f}s (target <50ms)")
        
        # Test cache retrieval from Redis
        start_time = time.time()
        retrieved_data = await service.get_cached_response(query_hash)
        retrieve_time = time.time() - start_time
        
        # Hard fail: Should retrieve successfully
        assert retrieved_data is not None, "Should retrieve cached data from Redis"
        assert retrieved_data == query_data["response_data"], "Retrieved data should match stored data"
        
        # Quality flag: Retrieval should be very fast
        if retrieve_time > 0.01:  # 10ms
            pytest.warns(UserWarning, f"Redis cache retrieve slow: {retrieve_time:.3f}s (target <10ms)")
        
        print(f"Redis cache operations: store {store_time*1000:.2f}ms, retrieve {retrieve_time*1000:.2f}ms")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not available for integration tests")
    @pytest.mark.asyncio
    async def test_redis_ttl_behavior(self, cache_service_with_redis):
        """Test Redis TTL (Time To Live) behavior with real Redis."""
        service = cache_service_with_redis
        
        # Store item with short TTL for testing
        test_hash = generate_query_hash("TTL test query")
        test_data = {"answer": "TTL test response", "timestamp": time.time()}
        
        short_ttl = 2  # 2 seconds
        success = await service.cache_response(test_hash, test_data, custom_ttl=short_ttl)
        assert success is True, "Should store with custom TTL"
        
        # Verify item is there immediately
        immediate_result = await service.get_cached_response(test_hash)
        assert immediate_result is not None, "Item should be available immediately"
        
        # Check TTL in Redis directly
        if service.redis:
            cache_key = service._generate_cache_key(test_hash)
            redis_ttl = await service.redis.ttl(cache_key)
            
            # TTL should be close to what we set (allowing for small timing differences)
            assert redis_ttl > 0, "TTL should be positive"
            assert redis_ttl <= short_ttl, f"TTL should be <= {short_ttl}, got {redis_ttl}"
            
            print(f"Redis TTL set correctly: {redis_ttl}s remaining")
        
        # Wait for expiration (with buffer)
        await asyncio.sleep(short_ttl + 0.5)
        
        # Item should be expired
        expired_result = await service.get_cached_response(test_hash)
        assert expired_result is None, "Item should be expired from Redis"
        
        print("Redis TTL expiration test passed")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not available for integration tests")
    @pytest.mark.asyncio
    async def test_redis_failover_to_fallback(self, redis_integration_config):
        """Test failover to fallback cache when Redis fails."""
        # Create service with Redis
        service = CacheService(redis_integration_config)
        await service.initialize()
        
        # Store some data in both Redis and fallback
        test_hash = generate_query_hash("Failover test query")
        test_data = {"answer": "Failover test response", "timestamp": time.time()}
        
        success = await service.cache_response(test_hash, test_data)
        assert success is True, "Should store successfully with Redis working"
        
        # Verify data is in Redis
        redis_result = await service.get_cached_response(test_hash)
        assert redis_result is not None, "Data should be in Redis"
        
        # Simulate Redis failure by closing connection
        if service.redis:
            await service.redis.close()
            service.redis = None
        
        # Data should still be available from fallback cache
        fallback_result = await service.get_cached_response(test_hash)
        assert fallback_result is not None, "Data should be available from fallback"
        assert fallback_result == test_data, "Fallback data should match"
        
        # New storage should work with fallback only
        new_hash = generate_query_hash("New data after Redis failure")
        new_data = {"answer": "New response with fallback only"}
        
        success = await service.cache_response(new_hash, new_data)
        assert success is True, "Should store successfully with fallback only"
        
        # Should retrieve from fallback
        new_result = await service.get_cached_response(new_hash)
        assert new_result == new_data, "Should retrieve new data from fallback"
        
        print("Redis failover to fallback test passed")


class TestCacheHitMissScenarios:
    """Test realistic cache hit/miss scenarios."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_realistic_cache_hit_patterns(self, cache_service_with_redis, integration_test_data):
        """Test realistic cache hit patterns with technical documentation queries."""
        service = cache_service_with_redis
        
        # Simulate realistic query patterns
        queries = integration_test_data["realistic_queries"]
        
        # Add queries with some repetition to simulate realistic patterns
        query_sequence = []
        for _ in range(3):  # Repeat pattern 3 times
            query_sequence.extend(queries)
            # Add some repeated queries (common in real usage)
            query_sequence.append(queries[0])  # Simple query repeated
            query_sequence.append(queries[2])  # Basic query repeated
        
        hit_count = 0
        miss_count = 0
        total_time = 0
        
        for query_data in query_sequence:
            query_hash = generate_query_hash(query_data["query"])
            
            start_time = time.time()
            
            # Try to get from cache first
            cached_result = await service.get_cached_response(query_hash)
            
            if cached_result is not None:
                hit_count += 1
                # Verify cached data integrity
                assert cached_result == query_data["response_data"], "Cached data should match original"
            else:
                miss_count += 1
                # Cache miss - store the response
                await service.cache_response(
                    query_hash=query_hash,
                    response_data=query_data["response_data"],
                    content_type=query_data["content_type"]
                )
            
            operation_time = time.time() - start_time
            total_time += operation_time
            
            # Hard fail: Operations should not be excessively slow
            assert operation_time < 1.0, f"Cache operation too slow: {operation_time:.2f}s"
        
        # Calculate hit rate
        total_requests = hit_count + miss_count
        hit_rate = hit_count / total_requests if total_requests > 0 else 0
        avg_time = total_time / total_requests if total_requests > 0 else 0
        
        # Hard fail: Should have some hits due to repetition
        assert hit_count > 0, "Should have some cache hits with repeated queries"
        
        # Quality flag: Hit rate should be reasonable for this pattern
        expected_hit_rate = 0.4  # With repetition, should get ~40%+ hits
        if hit_rate < expected_hit_rate:
            pytest.warns(UserWarning, f"Hit rate {hit_rate:.2%} below expected {expected_hit_rate:.1%}")
        
        # Quality flag: Average operation time should be fast
        if avg_time > 0.05:  # 50ms
            pytest.warns(UserWarning, f"Average cache operation slow: {avg_time:.3f}s")
        
        print(f"Cache hit/miss test: {hit_rate:.2%} hit rate ({hit_count}/{total_requests}), avg {avg_time*1000:.2f}ms")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_cache_invalidation_scenarios(self, cache_service_with_redis, integration_test_data):
        """Test various cache invalidation scenarios."""
        service = cache_service_with_redis
        
        # Store multiple items with different TTLs
        test_items = [
            {
                "hash": generate_query_hash("Short TTL item"),
                "data": {"answer": "Short TTL response", "type": "short"},
                "ttl": 1  # 1 second
            },
            {
                "hash": generate_query_hash("Medium TTL item"),
                "data": {"answer": "Medium TTL response", "type": "medium"},
                "ttl": 10  # 10 seconds
            },
            {
                "hash": generate_query_hash("Long TTL item"),
                "data": {"answer": "Long TTL response", "type": "long"},
                "ttl": 3600  # 1 hour
            }
        ]
        
        # Store all items
        for item in test_items:
            success = await service.cache_response(
                item["hash"], 
                item["data"], 
                custom_ttl=item["ttl"]
            )
            assert success is True, f"Should store item with TTL {item['ttl']}"
        
        # Verify all items are initially available
        for item in test_items:
            result = await service.get_cached_response(item["hash"])
            assert result is not None, f"Item should be available: {item['data']['type']}"
            assert result == item["data"], "Data should match"
        
        # Wait for short TTL to expire
        await asyncio.sleep(1.5)
        
        # Check invalidation
        short_result = await service.get_cached_response(test_items[0]["hash"])
        medium_result = await service.get_cached_response(test_items[1]["hash"])
        long_result = await service.get_cached_response(test_items[2]["hash"])
        
        assert short_result is None, "Short TTL item should be expired"
        assert medium_result is not None, "Medium TTL item should still be available"
        assert long_result is not None, "Long TTL item should still be available"
        
        # Manual deletion test
        delete_success = await service.delete_cached_response(test_items[1]["hash"])
        assert delete_success is True, "Manual deletion should succeed"
        
        deleted_result = await service.get_cached_response(test_items[1]["hash"])
        assert deleted_result is None, "Manually deleted item should be gone"
        
        # Long TTL item should still be there
        final_result = await service.get_cached_response(test_items[2]["hash"])
        assert final_result is not None, "Long TTL item should survive"
        
        print("Cache invalidation scenarios test passed")


class TestCachePerformanceUnderLoad:
    """Test cache performance under different load conditions."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_moderate_load_performance(self, cache_service_with_redis, integration_test_data):
        """Test cache performance under moderate load (100 operations)."""
        service = cache_service_with_redis
        
        # Use load test data
        load_queries = integration_test_data["load_test_queries"][:50]  # 50 queries for moderate load
        
        # Phase 1: Store all queries (cache misses)
        store_times = []
        start_time = time.time()
        
        for query_data in load_queries:
            query_hash = generate_query_hash(query_data["query"])
            
            operation_start = time.time()
            success = await service.cache_response(
                query_hash, 
                query_data["response_data"], 
                query_data["content_type"]
            )
            operation_time = time.time() - operation_start
            store_times.append(operation_time)
            
            # Hard fail: Each operation should succeed
            assert success is True, f"Store operation should succeed for query {query_data['query'][:20]}"
            
            # Hard fail: Individual operations shouldn't be excessively slow
            assert operation_time < 1.0, f"Store operation too slow: {operation_time:.2f}s"
        
        total_store_time = time.time() - start_time
        avg_store_time = sum(store_times) / len(store_times)
        
        # Phase 2: Retrieve all queries (cache hits)
        retrieve_times = []
        start_time = time.time()
        
        for query_data in load_queries:
            query_hash = generate_query_hash(query_data["query"])
            
            operation_start = time.time()
            result = await service.get_cached_response(query_hash)
            operation_time = time.time() - operation_start
            retrieve_times.append(operation_time)
            
            # Hard fail: Should retrieve successfully
            assert result is not None, f"Should retrieve cached data for query {query_data['query'][:20]}"
            assert result == query_data["response_data"], "Retrieved data should match"
            
            # Hard fail: Retrieval shouldn't be excessively slow
            assert operation_time < 1.0, f"Retrieve operation too slow: {operation_time:.2f}s"
        
        total_retrieve_time = time.time() - start_time
        avg_retrieve_time = sum(retrieve_times) / len(retrieve_times)
        
        # Calculate overall performance metrics
        store_throughput = len(load_queries) / total_store_time
        retrieve_throughput = len(load_queries) / total_retrieve_time
        
        # Hard fail: Should handle reasonable throughput
        assert store_throughput >= 10, f"Store throughput too low: {store_throughput:.1f} ops/sec"
        assert retrieve_throughput >= 50, f"Retrieve throughput too low: {retrieve_throughput:.1f} ops/sec"
        
        # Quality flags: Performance targets
        if avg_store_time > 0.05:  # 50ms
            pytest.warns(UserWarning, f"Average store time slow: {avg_store_time:.3f}s")
        
        if avg_retrieve_time > 0.01:  # 10ms
            pytest.warns(UserWarning, f"Average retrieve time slow: {avg_retrieve_time:.3f}s")
        
        print(f"Moderate load test: Store {store_throughput:.1f} ops/sec, Retrieve {retrieve_throughput:.1f} ops/sec")
        print(f"Average times: Store {avg_store_time*1000:.2f}ms, Retrieve {avg_retrieve_time*1000:.2f}ms")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_concurrent_operations_performance(self, cache_service_with_redis):
        """Test cache performance with concurrent operations."""
        service = cache_service_with_redis
        
        # Create concurrent operations mix
        concurrent_operations = []
        operation_types = []
        
        # Mix of store and retrieve operations
        for i in range(20):  # 20 concurrent operations
            query_hash = generate_query_hash(f"Concurrent operation {i}")
            data = {"answer": f"Concurrent response {i}", "index": i}
            
            if i % 2 == 0:
                # Store operation
                concurrent_operations.append(
                    service.cache_response(query_hash, data, "simple_query")
                )
                operation_types.append("store")
            else:
                # Retrieve operation (will mostly miss initially)
                concurrent_operations.append(
                    service.get_cached_response(query_hash)
                )
                operation_types.append("retrieve")
        
        # Execute all operations concurrently
        start_time = time.time()
        results = await asyncio.gather(*concurrent_operations, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Hard fail: Should not take excessively long
        assert total_time < 30.0, f"Concurrent operations took {total_time:.2f}s (too slow)"
        
        # Analyze results
        successful_operations = []
        failed_operations = []
        
        for i, (result, op_type) in enumerate(zip(results, operation_types)):
            if isinstance(result, Exception):
                failed_operations.append((i, op_type, str(result)))
            else:
                if op_type == "store":
                    # Store operations should return True
                    if result is True:
                        successful_operations.append((i, op_type, result))
                    else:
                        failed_operations.append((i, op_type, f"Store returned {result}"))
                else:
                    # Retrieve operations can return None (miss) or data (hit)
                    successful_operations.append((i, op_type, result))
        
        success_rate = len(successful_operations) / len(results)
        throughput = len(results) / total_time
        
        # Hard fail: Most operations should succeed
        assert success_rate >= 0.8, f"Too many concurrent operation failures: {success_rate:.2%} success rate"
        
        # Quality flag: Should handle concurrent operations efficiently
        if throughput < 10:  # 10 ops/sec minimum
            pytest.warns(UserWarning, f"Concurrent operation throughput low: {throughput:.1f} ops/sec")
        
        if total_time > 5.0:
            pytest.warns(UserWarning, f"Concurrent operations slow: {total_time:.2f}s")
        
        print(f"Concurrent operations: {success_rate:.2%} success rate, {throughput:.1f} ops/sec")
        if failed_operations:
            print(f"Failed operations: {len(failed_operations)}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, cache_service_with_redis):
        """Test memory usage under sustained load."""
        try:
            import psutil
            import os
        except ImportError:
            pytest.skip("psutil not available for memory testing")
        
        service = cache_service_with_redis
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create sustained load with varying data sizes
        operations = []
        for i in range(200):  # 200 operations
            query_hash = generate_query_hash(f"Memory test query {i}")
            
            # Vary data size to test memory handling
            content_size = 100 + (i % 10) * 50  # 100-550 characters
            data = {
                "answer": "Memory test response content. " * content_size,
                "index": i,
                "metadata": {"size": content_size, "timestamp": time.time()}
            }
            
            operations.append(service.cache_response(query_hash, data))
        
        # Execute operations in batches to simulate sustained load
        batch_size = 20
        for i in range(0, len(operations), batch_size):
            batch = operations[i:i+batch_size]
            results = await asyncio.gather(*batch)
            
            # All operations in batch should succeed
            assert all(r is True for r in results), f"Batch {i//batch_size} had failures"
            
            # Check memory after each batch
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory
            
            # Hard fail: Memory usage should not be excessive (>2GB increase)
            assert memory_increase < 2000, f"Excessive memory usage: +{memory_increase:.1f}MB"
            
            # Brief pause between batches
            await asyncio.sleep(0.1)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_memory_increase = final_memory - initial_memory
        
        # Quality flag: Memory usage should be reasonable
        if total_memory_increase > 100:  # 100MB increase
            pytest.warns(UserWarning, f"High memory usage under load: +{total_memory_increase:.1f}MB")
        
        # Test memory cleanup by getting cache statistics
        stats = await service.get_cache_statistics()
        fallback_memory = stats.get("fallback", {}).get("memory_usage_bytes", 0) / 1024 / 1024
        
        print(f"Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB (+{total_memory_increase:.1f}MB)")
        print(f"Fallback cache memory: {fallback_memory:.1f}MB")


class TestServiceResilience:
    """Test service resilience and error recovery."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, redis_integration_config):
        """Test circuit breaker behavior with Redis failures."""
        # Create service with low circuit breaker threshold for testing
        config = redis_integration_config.copy()
        config["circuit_breaker_threshold"] = 3
        config["circuit_breaker_timeout"] = 5  # 5 seconds for testing
        
        service = CacheService(config)
        await service.initialize()
        
        # Initially circuit breaker should be closed
        assert not service._is_circuit_breaker_open(), "Circuit breaker should start closed"
        
        # Store some data successfully first
        test_hash = "circuit_breaker_test"
        test_data = {"answer": "circuit breaker test data"}
        
        success = await service.cache_response(test_hash, test_data)
        assert success is True, "Initial storage should succeed"
        
        # Simulate Redis failures by corrupting the Redis connection
        if service.redis:
            # Force Redis operations to fail
            original_get = service.redis.get
            original_setex = service.redis.setex
            
            async def failing_get(*args, **kwargs):
                raise Exception("Simulated Redis failure")
            
            async def failing_setex(*args, **kwargs):
                raise Exception("Simulated Redis failure")
            
            service.redis.get = failing_get
            service.redis.setex = failing_setex
            
            # Trigger failures to open circuit breaker
            failure_count = 0
            for i in range(5):  # More than threshold
                try:
                    await service.cache_response(f"fail_test_{i}", {"data": f"fail {i}"})
                    await service.get_cached_response(f"fail_test_{i}")
                    failure_count += 2
                except:
                    pass  # Failures are expected
            
            # Circuit breaker should now be open
            assert service._is_circuit_breaker_open(), "Circuit breaker should be open after failures"
            assert service.circuit_breaker_failures >= config["circuit_breaker_threshold"]
            
            # Operations should now use fallback cache only
            fallback_hash = "fallback_test"
            fallback_data = {"answer": "fallback only data"}
            
            success = await service.cache_response(fallback_hash, fallback_data)
            assert success is True, "Should succeed with fallback cache"
            
            result = await service.get_cached_response(fallback_hash)
            assert result == fallback_data, "Should retrieve from fallback cache"
            
            # Restore Redis operations
            service.redis.get = original_get
            service.redis.setex = original_setex
            
            # Wait for circuit breaker timeout
            await asyncio.sleep(config["circuit_breaker_timeout"] + 1)
            
            # Circuit breaker should close
            assert not service._is_circuit_breaker_open(), "Circuit breaker should close after timeout"
            
            print("Circuit breaker integration test passed")
        
        await service.close()

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_data_integrity_under_stress(self, cache_service_with_redis):
        """Test data integrity under stress conditions."""
        service = cache_service_with_redis
        
        # Store complex data with various types
        test_cases = [
            {
                "hash": generate_query_hash("Unicode test ñoño 测试 🚀"),
                "data": {
                    "answer": "Unicode response with ñoño 测试 emojis 🚀🎯",
                    "special_chars": "!@#$%^&*()_+-=[]{}|;':\",./<>?",
                    "numbers": [1, 2.5, -3, 0, 999999],
                    "nested": {"level1": {"level2": {"value": "deep"}}}
                }
            },
            {
                "hash": generate_query_hash("Large data test"),
                "data": {
                    "answer": "Large response " * 1000,  # Large text
                    "metadata": {
                        "large_list": list(range(1000)),
                        "large_dict": {f"key_{i}": f"value_{i}" for i in range(100)}
                    }
                }
            },
            {
                "hash": generate_query_hash("Edge case data"),
                "data": {
                    "empty_string": "",
                    "null_value": None,
                    "zero": 0,
                    "false_value": False,
                    "empty_list": [],
                    "empty_dict": {}
                }
            }
        ]
        
        # Store all test cases
        for test_case in test_cases:
            success = await service.cache_response(
                test_case["hash"], 
                test_case["data"]
            )
            assert success is True, f"Should store complex data: {test_case['hash'][:8]}"
        
        # Verify data integrity with multiple retrievals
        for _ in range(5):  # Multiple retrieval cycles
            for test_case in test_cases:
                retrieved = await service.get_cached_response(test_case["hash"])
                
                # Hard fail: Data should be retrievable
                assert retrieved is not None, f"Should retrieve data: {test_case['hash'][:8]}"
                
                # Hard fail: Data should match exactly
                assert retrieved == test_case["data"], f"Data integrity failure: {test_case['hash'][:8]}"
        
        # Test concurrent access to same data
        concurrent_retrievals = []
        for test_case in test_cases:
            for _ in range(10):  # 10 concurrent retrievals per item
                concurrent_retrievals.append(
                    service.get_cached_response(test_case["hash"])
                )
        
        results = await asyncio.gather(*concurrent_retrievals)
        
        # Verify all concurrent retrievals succeeded
        successful_retrievals = [r for r in results if r is not None]
        success_rate = len(successful_retrievals) / len(results)
        
        assert success_rate >= 0.95, f"Data integrity under concurrent access: {success_rate:.2%}"
        
        print(f"Data integrity test: {success_rate:.2%} success rate with concurrent access")


class TestAPIGatewayIntegration:
    """Test integration with API Gateway patterns (simulated)."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_request_correlation_ids(self, cache_service_with_redis):
        """Test request correlation and tracing integration."""
        service = cache_service_with_redis
        
        # Simulate API Gateway request with correlation ID
        correlation_id = str(uuid.uuid4())
        
        # Create queries with correlation context
        queries_with_context = [
            {
                "query": "Gateway integrated query 1",
                "context": {"correlation_id": correlation_id, "user_id": "user_123"}
            },
            {
                "query": "Gateway integrated query 2", 
                "context": {"correlation_id": correlation_id, "user_id": "user_123"}
            }
        ]
        
        # Test that context affects cache keys (same query, different context = different cache)
        for i, query_info in enumerate(queries_with_context):
            query_hash = generate_query_hash(query_info["query"], query_info["context"])
            
            response_data = {
                "answer": f"Gateway response {i+1}",
                "correlation_id": correlation_id,
                "timestamp": time.time()
            }
            
            # Store with context
            success = await service.cache_response(query_hash, response_data)
            assert success is True, f"Should store query {i+1} with context"
            
            # Retrieve with same context
            retrieved = await service.get_cached_response(query_hash)
            assert retrieved == response_data, f"Should retrieve query {i+1} with context"
        
        # Test that same query without context gets different hash
        base_query = queries_with_context[0]["query"]
        base_hash = generate_query_hash(base_query)  # No context
        context_hash = generate_query_hash(base_query, queries_with_context[0]["context"])
        
        assert base_hash != context_hash, "Query hashes should differ with/without context"
        
        # Store same query without context
        base_response = {"answer": "Base response without context"}
        success = await service.cache_response(base_hash, base_response)
        assert success is True, "Should store base query without context"
        
        # Verify both versions are cached independently
        base_result = await service.get_cached_response(base_hash)
        context_result = await service.get_cached_response(context_hash)
        
        assert base_result != context_result, "Cached responses should differ with/without context"
        
        print("Request correlation integration test passed")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_rate_limiting_simulation(self, cache_service_with_redis):
        """Test cache behavior under simulated rate limiting scenarios."""
        service = cache_service_with_redis
        
        # Simulate burst of requests (rate limiting scenario)
        burst_size = 50
        burst_operations = []
        
        # Create burst of cache operations
        for i in range(burst_size):
            query_hash = generate_query_hash(f"Burst query {i}")
            data = {"answer": f"Burst response {i}", "burst_index": i}
            
            # Mix of reads and writes
            if i % 3 == 0:
                burst_operations.append(service.cache_response(query_hash, data))
            else:
                burst_operations.append(service.get_cached_response(query_hash))
        
        # Execute burst within short timeframe
        start_time = time.time()
        results = await asyncio.gather(*burst_operations, return_exceptions=True)
        burst_time = time.time() - start_time
        
        # Analyze burst performance
        successful_ops = [r for r in results if not isinstance(r, Exception)]
        failed_ops = [r for r in results if isinstance(r, Exception)]
        
        success_rate = len(successful_ops) / len(results)
        burst_throughput = len(results) / burst_time
        
        # Hard fail: Should handle burst without complete failure
        assert success_rate >= 0.7, f"Burst handling poor: {success_rate:.2%} success rate"
        
        # Quality flag: Should handle bursts efficiently
        if burst_throughput < 50:  # 50 ops/sec minimum for bursts
            pytest.warns(UserWarning, f"Burst throughput low: {burst_throughput:.1f} ops/sec")
        
        # Test sustained load after burst
        sustained_operations = []
        for i in range(20):
            query_hash = generate_query_hash(f"Sustained query {i}")
            data = {"answer": f"Sustained response {i}"}
            sustained_operations.append(service.cache_response(query_hash, data))
        
        sustained_results = await asyncio.gather(*sustained_operations)
        sustained_success = all(r is True for r in sustained_results)
        
        # Service should recover and handle sustained load
        assert sustained_success, "Service should recover after burst and handle sustained load"
        
        print(f"Rate limiting simulation: {success_rate:.2%} burst success, {burst_throughput:.1f} ops/sec")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v"])