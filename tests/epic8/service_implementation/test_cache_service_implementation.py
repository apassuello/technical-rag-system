"""
Test Suite for Cache Service Core Implementation.

This test suite focuses on testing the business logic of the CacheService class directly,
not through HTTP API endpoints. Tests the core caching functionality including Redis operations,
fallback cache behavior, circuit breaker logic, and TTL strategies.

Key Focus Areas:
- Cache operations (get, set, delete) with performance validation
- Redis backend with fallback to in-memory cache
- Circuit breaker functionality for Redis failures
- TTL strategies based on content types
- Cache statistics and monitoring
- Memory management and LRU eviction
- Error handling and resilience patterns

Test Philosophy:  
- Test SERVICE METHODS directly (not API endpoints)
- Mock Redis dependencies for deterministic testing
- Focus on business logic validation
- Achieve >70% coverage of implementation code
"""

import pytest
import asyncio
import time
import hashlib
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import sys
from pathlib import Path


def _setup_cache_service_imports():
    """Set up imports for Cache Service implementation testing."""
    current_file = Path(__file__).resolve()
    project_root = current_file.parents[3]
    service_path = project_root / "services" / "cache"
    
    if not service_path.exists():
        return False, f"Service path does not exist: {service_path}", {}
    
    service_path_str = str(service_path)
    if service_path_str not in sys.path:
        sys.path.insert(0, service_path_str)
    
    try:
        from cache_app.core.cache import CacheService, InMemoryCache, CacheStats, CachedResponse
        from cache_app.core.config import CacheConfig
        
        imports = {
            'CacheService': CacheService,
            'InMemoryCache': InMemoryCache,
            'CacheStats': CacheStats,
            'CachedResponse': CachedResponse,
            'CacheConfig': CacheConfig
        }
        return True, None, imports
    except ImportError as e:
        return False, f"Import failed: {str(e)}", {}
    except Exception as e:
        return False, f"Unexpected error: {str(e)}", {}


# Execute import setup
IMPORTS_AVAILABLE, IMPORT_ERROR, imported_classes = _setup_cache_service_imports()

# Make imported classes available if imports succeeded
if IMPORTS_AVAILABLE:
    CacheService = imported_classes['CacheService']
    InMemoryCache = imported_classes['InMemoryCache']
    CacheStats = imported_classes['CacheStats']
    CachedResponse = imported_classes['CachedResponse']
    CacheConfig = imported_classes['CacheConfig']


class TestCacheServiceInitialization:
    """Test Cache Service initialization and configuration."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    def test_cache_service_initialization_basic(self):
        """Test basic cache service initialization."""
        config = {
            "redis_url": "redis://localhost:6379",
            "default_ttl": 3600,
            "fallback_cache_size": 1000
        }
        
        service = CacheService(config)
        
        # Verify basic initialization
        assert service.config == config
        assert service.redis_url == "redis://localhost:6379"
        assert service.default_ttl == 3600
        assert service.fallback_cache is not None
        assert service.fallback_cache.max_size == 1000
        assert service.circuit_breaker_open is False
        assert service.circuit_breaker_failures == 0

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    def test_cache_service_initialization_with_ttl_strategies(self):
        """Test cache service initialization with custom TTL strategies."""
        config = {
            "redis_url": "redis://localhost:6379",
            "default_ttl": 1800,
            "ttl_strategies": {
                "simple_query": 7200,
                "medium_query": 3600, 
                "complex_query": 900,
                "default": 1800
            },
            "circuit_breaker_threshold": 10,
            "circuit_breaker_timeout": 120
        }
        
        service = CacheService(config)
        
        # Verify TTL strategies
        assert service.ttl_strategies["simple_query"] == 7200
        assert service.ttl_strategies["medium_query"] == 3600
        assert service.ttl_strategies["complex_query"] == 900
        assert service.ttl_strategies["default"] == 1800
        
        # Verify circuit breaker config
        assert service.circuit_breaker_threshold == 10
        assert service.circuit_breaker_timeout == 120

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_cache_service_async_context_manager(self):
        """Test cache service as async context manager."""
        config = {"redis_url": "redis://localhost:6379", "default_ttl": 3600}
        
        with patch.object(CacheService, 'initialize') as mock_init, \
             patch.object(CacheService, 'close') as mock_close:
            
            mock_init.return_value = None
            mock_close.return_value = None
            
            async with CacheService(config) as service:
                assert service is not None
                mock_init.assert_called_once()
            
            mock_close.assert_called_once()


class TestCacheServiceTTLStrategies:
    """Test TTL calculation and strategy logic."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    def test_ttl_calculation_content_types(self):
        """Test TTL calculation for different content types."""
        config = {
            "redis_url": "redis://localhost:6379",
            "default_ttl": 3600,
            "ttl_strategies": {
                "simple_query": 7200,
                "medium_query": 3600,
                "complex_query": 1800,
                "default": 3600
            }
        }
        
        service = CacheService(config)
        
        # Test different content type TTLs
        assert service._calculate_ttl("simple_query") == 7200
        assert service._calculate_ttl("medium_query") == 3600
        assert service._calculate_ttl("complex_query") == 1800
        assert service._calculate_ttl("unknown_type") == 3600  # Falls back to default
        
        # Test custom TTL override
        assert service._calculate_ttl("simple_query", custom_ttl=900) == 900
        assert service._calculate_ttl("medium_query", custom_ttl=None) == 3600

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    def test_cache_key_generation(self):
        """Test cache key generation logic."""
        config = {"redis_url": "redis://localhost:6379", "default_ttl": 3600}
        service = CacheService(config)
        
        # Test key generation
        query_hash = "abc123def456"
        cache_key = service._generate_cache_key(query_hash)
        
        assert cache_key == f"epic8:response:{query_hash}"
        assert cache_key.startswith("epic8:response:")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    def test_ttl_strategy_performance_characteristics(self):
        """Test that TTL strategy reflects performance characteristics."""
        config = {
            "redis_url": "redis://localhost:6379",
            "default_ttl": 3600,
            "ttl_strategies": {
                "simple_query": 7200,    # Simple queries cached longer
                "medium_query": 3600,    # Medium queries default
                "complex_query": 1800,   # Complex queries shorter (more likely to change)
                "default": 3600
            }
        }
        
        service = CacheService(config)
        
        simple_ttl = service._calculate_ttl("simple_query")
        medium_ttl = service._calculate_ttl("medium_query")
        complex_ttl = service._calculate_ttl("complex_query")
        
        # Simple queries should be cached longest, complex shortest
        assert simple_ttl > medium_ttl > complex_ttl
        assert simple_ttl == 7200
        assert complex_ttl == 1800


class TestCacheServiceCircuitBreaker:
    """Test circuit breaker functionality for Redis failures."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    def test_circuit_breaker_state_management(self):
        """Test circuit breaker state transitions."""
        config = {
            "redis_url": "redis://localhost:6379",
            "circuit_breaker_threshold": 3,
            "circuit_breaker_timeout": 2,
            "default_ttl": 3600
        }
        
        service = CacheService(config)
        
        # Initially closed
        assert service.circuit_breaker_open is False
        assert service._is_circuit_breaker_open() is False
        
        # Record failures
        service._record_redis_failure()
        assert service.circuit_breaker_failures == 1
        assert service.circuit_breaker_open is False
        
        service._record_redis_failure()
        service._record_redis_failure()
        assert service.circuit_breaker_failures == 3
        assert service.circuit_breaker_open is True
        assert service._is_circuit_breaker_open() is True

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    def test_circuit_breaker_timeout_recovery(self):
        """Test circuit breaker recovery after timeout."""
        config = {
            "redis_url": "redis://localhost:6379", 
            "circuit_breaker_threshold": 2,
            "circuit_breaker_timeout": 1,  # 1 second timeout
            "default_ttl": 3600
        }
        
        service = CacheService(config)
        
        # Trigger circuit breaker open
        service._record_redis_failure()
        service._record_redis_failure()
        assert service.circuit_breaker_open is True
        
        # Should still be open immediately
        assert service._is_circuit_breaker_open() is True
        
        # Simulate passage of time
        service.circuit_breaker_last_failure = time.time() - 2  # 2 seconds ago
        
        # Should now be closed
        assert service._is_circuit_breaker_open() is False
        assert service.circuit_breaker_open is False
        assert service.circuit_breaker_failures == 0

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_cache_operations_with_circuit_breaker_open(self):
        """Test cache operations when circuit breaker is open."""
        config = {
            "redis_url": "redis://localhost:6379",
            "circuit_breaker_threshold": 1,
            "default_ttl": 3600
        }
        
        service = CacheService(config)
        
        # Create mock Redis that always fails
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = Exception("Redis down")
        mock_redis.setex.side_effect = Exception("Redis down") 
        service.redis = mock_redis
        
        # First operation should fail and open circuit breaker
        result = await service.get_cached_response("test_hash")
        assert result is None
        assert service.circuit_breaker_open is True
        
        # Subsequent operations should skip Redis (not call it)
        mock_redis.reset_mock()
        result2 = await service.get_cached_response("test_hash2")
        assert result2 is None
        mock_redis.get.assert_not_called()  # Should not try Redis when circuit is open


class TestCacheServiceCoreOperations:
    """Test core cache operations with business logic focus."""

    @pytest.fixture
    def mock_cache_service(self):
        """Create a cache service with mocked Redis for testing."""
        config = {
            "redis_url": "redis://localhost:6379",
            "default_ttl": 3600,
            "ttl_strategies": {
                "simple_query": 7200,
                "medium_query": 3600,
                "complex_query": 1800
            }
        }
        
        with patch('cache_app.core.cache.redis.Redis') as mock_redis_class:
            # Mock Redis class and instance
            mock_redis_instance = AsyncMock()
            mock_redis_class.from_url.return_value = mock_redis_instance
            
            service = CacheService(config)
            service.redis = mock_redis_instance  # Ensure the mocked redis is used
            
            return service, mock_redis_instance

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_get_cached_response_redis_hit(self, mock_cache_service):
        """Test cache hit from Redis backend."""
        service, mock_redis = mock_cache_service
        
        # Mock Redis returning cached data
        test_data = {"answer": "RISC-V is an open instruction set architecture", "confidence": 0.95}
        mock_redis.get.return_value = json.dumps(test_data)
        
        # Test cache retrieval
        query_hash = "test_query_hash_123"
        result = await service.get_cached_response(query_hash)
        
        # Verify result
        assert result == test_data
        
        # Verify Redis was called with correct key
        expected_key = f"epic8:response:{query_hash}"
        mock_redis.get.assert_called_once_with(expected_key)
        
        # Verify statistics updated
        assert service.stats.hits == 1
        assert service.stats.misses == 0

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_get_cached_response_redis_miss_fallback_hit(self, mock_cache_service):
        """Test cache miss from Redis but hit from fallback cache."""
        service, mock_redis = mock_cache_service
        
        # Redis returns None (miss)
        mock_redis.get.return_value = None
        
        # Pre-populate fallback cache
        test_data = {"answer": "Cached in fallback", "source": "memory"}
        cached_response = CachedResponse(
            query_hash="fallback_test",
            response_data=test_data,
            created_at=time.time(),
            ttl=3600,
            content_type="simple_query"
        )
        await service.fallback_cache.set("fallback_test", cached_response)
        
        # Test cache retrieval
        result = await service.get_cached_response("fallback_test")
        
        # Verify result from fallback
        assert result == test_data
        
        # Verify Redis was tried first
        mock_redis.get.assert_called_once()
        
        # Verify statistics (hit from fallback counts as hit)
        assert service.stats.hits == 1

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_cache_response_redis_and_fallback(self, mock_cache_service):
        """Test caching response to both Redis and fallback."""
        service, mock_redis = mock_cache_service
        
        # Mock successful Redis operation
        mock_redis.setex.return_value = True
        
        # Test data
        query_hash = "cache_test_hash"
        response_data = {
            "answer": "Machine learning is a subset of artificial intelligence",
            "confidence": 0.88,
            "sources": ["doc1", "doc2"]
        }
        
        # Cache the response
        success = await service.cache_response(
            query_hash, 
            response_data, 
            content_type="medium_query"
        )
        
        # Verify success
        assert success is True
        
        # Verify Redis was called with correct parameters
        expected_key = f"epic8:response:{query_hash}"
        expected_ttl = 3600  # medium_query TTL
        expected_value = json.dumps(response_data)
        mock_redis.setex.assert_called_once_with(expected_key, expected_ttl, expected_value)
        
        # Verify fallback cache was also updated
        fallback_result = await service.fallback_cache.get(query_hash)
        assert fallback_result is not None
        assert fallback_result.response_data == response_data
        
        # Verify statistics
        assert service.stats.sets == 1

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_cache_response_redis_failure_fallback_success(self, mock_cache_service):
        """Test caching when Redis fails but fallback succeeds."""
        service, mock_redis = mock_cache_service
        
        # Mock Redis failure
        mock_redis.setex.side_effect = Exception("Redis connection failed")
        
        # Test data
        query_hash = "fallback_cache_test"
        response_data = {"answer": "Fallback cache response", "confidence": 0.75}
        
        # Cache the response
        success = await service.cache_response(query_hash, response_data)
        
        # Should still succeed due to fallback
        assert success is True
        
        # Verify circuit breaker was triggered
        assert service.circuit_breaker_failures >= 1
        
        # Verify fallback cache has the data
        fallback_result = await service.fallback_cache.get(query_hash)
        assert fallback_result is not None
        assert fallback_result.response_data == response_data

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_delete_cached_response(self, mock_cache_service):
        """Test cache deletion from both Redis and fallback."""
        service, mock_redis = mock_cache_service
        
        # Mock Redis delete returning 1 (successful deletion)
        mock_redis.delete.return_value = 1
        
        # Pre-populate fallback cache
        cached_response = CachedResponse(
            query_hash="delete_test",
            response_data={"answer": "To be deleted"},
            created_at=time.time(),
            ttl=3600,
            content_type="simple_query"
        )
        await service.fallback_cache.set("delete_test", cached_response)
        
        # Test deletion
        success = await service.delete_cached_response("delete_test")
        
        # Verify success
        assert success is True
        
        # Verify Redis delete was called
        expected_key = f"epic8:response:delete_test"
        mock_redis.delete.assert_called_once_with(expected_key)
        
        # Verify fallback cache item was deleted
        fallback_result = await service.fallback_cache.get("delete_test")
        assert fallback_result is None
        
        # Verify statistics
        assert service.stats.deletes == 1

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_cache_operations_performance_timing(self, mock_cache_service):
        """Test cache operation performance characteristics."""
        service, mock_redis = mock_cache_service
        
        # Mock fast Redis operations
        mock_redis.get.return_value = json.dumps({"answer": "fast response"})
        mock_redis.setex.return_value = True
        
        # Test get operation timing
        start_time = time.time()
        result = await service.get_cached_response("perf_test")
        get_time = time.time() - start_time
        
        # Should be very fast (< 100ms for mocked operation)
        assert get_time < 0.1
        assert result == {"answer": "fast response"}
        
        # Test set operation timing
        start_time = time.time()
        success = await service.cache_response("perf_set_test", {"data": "performance"})
        set_time = time.time() - start_time
        
        # Should be very fast (< 100ms for mocked operation)
        assert set_time < 0.1
        assert success is True


class TestInMemoryCacheBehavior:
    """Test in-memory fallback cache business logic."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_lru_eviction_algorithm(self):
        """Test LRU eviction algorithm in fallback cache."""
        cache = InMemoryCache(max_size=3)
        
        # Create test responses
        responses = [
            CachedResponse(f"hash_{i}", {"data": f"item_{i}"}, time.time(), 3600, "test", 100)
            for i in range(5)
        ]
        
        # Fill cache to capacity
        for i in range(3):
            await cache.set(f"key_{i}", responses[i])
        
        assert len(cache.cache) == 3
        assert len(cache.access_order) == 3
        
        # Access key_0 to make it most recently used
        result = await cache.get("key_0")
        assert result is not None
        assert cache.access_order[-1] == "key_0"  # Should be last (most recent)
        
        # Add new item, should evict key_1 (least recently used)
        await cache.set("key_3", responses[3])
        
        assert len(cache.cache) == 3
        assert "key_1" not in cache.cache  # Should be evicted
        assert "key_0" in cache.cache      # Should still be present (recently accessed)
        assert "key_2" in cache.cache      # Should still be present
        assert "key_3" in cache.cache      # Should be newly added

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_ttl_expiration_logic(self):
        """Test TTL-based expiration in fallback cache."""
        cache = InMemoryCache(max_size=10)
        
        # Create response with short TTL
        current_time = time.time()
        expired_response = CachedResponse(
            query_hash="expired_test",
            response_data={"answer": "should expire"},
            created_at=current_time - 7200,  # Created 2 hours ago
            ttl=3600,  # 1 hour TTL, so expired
            content_type="test"
        )
        
        # Manually add expired response
        cache.cache["expired_key"] = expired_response
        cache.access_order.append("expired_key")
        
        # Create fresh response
        fresh_response = CachedResponse(
            query_hash="fresh_test",
            response_data={"answer": "still fresh"},
            created_at=current_time - 1800,  # Created 30 minutes ago
            ttl=3600,  # 1 hour TTL, still valid
            content_type="test"
        )
        
        await cache.set("fresh_key", fresh_response)
        
        # Getting expired item should return None and remove it
        expired_result = await cache.get("expired_key")
        assert expired_result is None
        assert "expired_key" not in cache.cache
        
        # Getting fresh item should succeed
        fresh_result = await cache.get("fresh_key")
        assert fresh_result is not None
        assert fresh_result.response_data == {"answer": "still fresh"}

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_cache_statistics_accuracy(self):
        """Test accuracy of cache statistics calculation."""
        cache = InMemoryCache(max_size=5)
        
        # Perform various operations
        response1 = CachedResponse("hash1", {"data": "1"}, time.time(), 3600, "test", 50)
        response2 = CachedResponse("hash2", {"data": "2"}, time.time(), 3600, "test", 75)
        
        # Sets
        await cache.set("key1", response1)
        await cache.set("key2", response2)
        
        # Hits
        await cache.get("key1")  # Hit
        await cache.get("key2")  # Hit
        
        # Misses
        await cache.get("nonexistent1")  # Miss
        await cache.get("nonexistent2")  # Miss
        await cache.get("nonexistent3")  # Miss
        
        # Deletes
        await cache.delete("key1")
        
        # Verify statistics
        stats = cache.get_stats()
        assert stats.hits == 2
        assert stats.misses == 3
        assert stats.sets == 2
        assert stats.deletes == 1
        assert stats.total_requests == 5  # 2 hits + 3 misses
        assert stats.hit_rate == 0.4      # 2/5 = 0.4
        assert stats.key_count == 1       # key2 remains
        assert stats.memory_usage_bytes == 75  # Only response2 remains

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_concurrent_cache_operations(self):
        """Test concurrent operations on fallback cache."""
        cache = InMemoryCache(max_size=100)
        
        # Create responses for concurrent testing
        responses = [
            CachedResponse(f"hash_{i}", {"data": f"concurrent_{i}"}, time.time(), 3600, "test", 50)
            for i in range(20)
        ]
        
        # Create concurrent set operations
        set_tasks = [
            cache.set(f"concurrent_key_{i}", responses[i])
            for i in range(20)
        ]
        
        # Execute all sets concurrently
        set_results = await asyncio.gather(*set_tasks)
        
        # All sets should succeed
        assert all(set_results)
        assert len(cache.cache) == 20
        
        # Create concurrent get operations
        get_tasks = [
            cache.get(f"concurrent_key_{i}")
            for i in range(20)
        ]
        
        # Execute all gets concurrently
        get_results = await asyncio.gather(*get_tasks)
        
        # All gets should succeed and return correct data
        for i, result in enumerate(get_results):
            assert result is not None
            assert result.response_data == {"data": f"concurrent_{i}"}

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_cache_clear_functionality(self):
        """Test cache clearing functionality."""
        cache = InMemoryCache(max_size=10)
        
        # Populate cache
        for i in range(5):
            response = CachedResponse(f"hash_{i}", {"data": i}, time.time(), 3600, "test", 25)
            await cache.set(f"key_{i}", response)
        
        assert len(cache.cache) == 5
        assert len(cache.access_order) == 5
        
        # Clear cache
        success = await cache.clear()
        
        assert success is True
        assert len(cache.cache) == 0
        assert len(cache.access_order) == 0
        
        # Verify items are gone
        for i in range(5):
            result = await cache.get(f"key_{i}")
            assert result is None


class TestCacheServiceStatistics:
    """Test cache statistics and monitoring functionality."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_comprehensive_statistics_collection(self):
        """Test comprehensive cache statistics collection."""
        config = {"redis_url": "redis://localhost:6379", "default_ttl": 3600}
        service = CacheService(config)
        
        # Mock Redis info
        mock_redis = AsyncMock()
        mock_redis_info = {
            "used_memory_human": "1.5M",
            "connected_clients": 5,
            "total_commands_processed": 1000,
            "keyspace_hits": 750,
            "keyspace_misses": 250
        }
        mock_redis.info.return_value = mock_redis_info
        service.redis = mock_redis
        
        # Simulate some service activity
        service.stats.hits = 50
        service.stats.misses = 25
        service.stats.sets = 30
        service.stats.deletes = 5
        service.stats.errors = 2
        
        # Get statistics
        stats = await service.get_cache_statistics()
        
        # Verify structure
        assert stats["service"] == "cache"
        assert stats["version"] == "1.0.0"
        assert "timestamp" in stats
        assert "uptime_seconds" in stats
        
        # Verify overall statistics
        overall = stats["overall"]
        assert overall["hits"] == 50
        assert overall["misses"] == 25
        assert overall["sets"] == 30
        assert overall["deletes"] == 5
        assert overall["errors"] == 2
        assert overall["total_requests"] == 75  # hits + misses
        assert overall["hit_rate"] == round(50/75, 4)  # 0.6667
        
        # Verify Redis statistics
        redis_stats = stats["redis"]
        assert redis_stats["connected"] is True
        assert redis_stats["circuit_breaker_open"] is False
        assert redis_stats["info"]["used_memory_human"] == "1.5M"
        assert redis_stats["info"]["keyspace_hits"] == 750
        
        # Verify fallback statistics
        fallback_stats = stats["fallback"]
        assert fallback_stats["enabled"] is True
        assert "current_size" in fallback_stats
        assert "hit_rate" in fallback_stats

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_statistics_with_redis_unavailable(self):
        """Test statistics collection when Redis is unavailable."""
        config = {"redis_url": "redis://localhost:6379", "default_ttl": 3600}
        service = CacheService(config)
        
        # Service has no Redis connection
        service.redis = None
        
        # Populate fallback cache statistics
        service.stats.hits = 30
        service.stats.misses = 20
        service.stats.sets = 25
        
        # Get statistics
        stats = await service.get_cache_statistics()
        
        # Should still provide comprehensive stats
        assert "overall" in stats
        assert "redis" in stats
        assert "fallback" in stats
        
        # Redis should show as disconnected
        redis_stats = stats["redis"]
        assert redis_stats["connected"] is False
        assert redis_stats["info"]["used_memory_human"] == "unknown"
        
        # Overall and fallback stats should still be accurate
        overall = stats["overall"]
        assert overall["hits"] == 30
        assert overall["misses"] == 20


class TestCacheServiceHealthChecks:
    """Test cache service health monitoring."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_health_check_redis_healthy(self):
        """Test health check with Redis available."""
        config = {"redis_url": "redis://localhost:6379", "default_ttl": 3600}
        service = CacheService(config)
        
        # Mock healthy Redis
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True
        mock_redis.info.return_value = {"used_memory_human": "2.1M"}
        service.redis = mock_redis
        
        # Perform health check
        health = await service.health_check()
        
        # Verify results
        assert health["healthy"] is True
        assert health["redis_connected"] is True
        assert health["fallback_available"] is True
        assert health["memory_usage"] == "2.1M"
        assert len(health["issues"]) == 0

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_health_check_redis_failed(self):
        """Test health check with Redis failed."""
        config = {"redis_url": "redis://localhost:6379", "default_ttl": 3600}
        service = CacheService(config)
        
        # Mock failed Redis
        mock_redis = AsyncMock()
        mock_redis.ping.side_effect = Exception("Connection refused")
        service.redis = mock_redis
        
        # Perform health check
        health = await service.health_check()
        
        # Should still be healthy due to fallback cache
        assert health["healthy"] is True  # Service is resilient
        assert health["redis_connected"] is False
        assert health["fallback_available"] is True
        assert len(health["issues"]) >= 1
        assert any("Redis connection failed" in issue for issue in health["issues"])

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_health_check_circuit_breaker_open(self):
        """Test health check with circuit breaker open."""
        config = {
            "redis_url": "redis://localhost:6379",
            "circuit_breaker_threshold": 1,
            "default_ttl": 3600
        }
        service = CacheService(config)
        
        # Open circuit breaker
        service._record_redis_failure()
        assert service.circuit_breaker_open is True
        
        # Mock Redis (shouldn't be called due to circuit breaker)
        mock_redis = AsyncMock()
        service.redis = mock_redis
        
        # Perform health check
        health = await service.health_check()
        
        # Should still be healthy (fallback available)
        assert health["healthy"] is True
        assert health["redis_connected"] is False  # Circuit breaker prevents connection
        assert health["fallback_available"] is True
        assert "circuit breaker open" in health["issues"][0]

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_cache_clear_operations(self):
        """Test cache clearing operations."""
        config = {"redis_url": "redis://localhost:6379", "default_ttl": 3600}
        service = CacheService(config)
        
        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.flushall.return_value = True
        service.redis = mock_redis
        
        # Populate fallback cache
        test_response = CachedResponse("test_hash", {"data": "test"}, time.time(), 3600, "test")
        await service.fallback_cache.set("test_key", test_response)
        
        # Clear cache
        results = await service.clear_cache()
        
        # Verify results
        assert results["redis"] is True
        assert results["fallback"] is True
        
        # Verify Redis was cleared
        mock_redis.flushall.assert_called_once()
        
        # Verify fallback cache is empty
        fallback_result = await service.fallback_cache.get("test_key")
        assert fallback_result is None
        
        # Verify statistics were reset
        assert service.stats.hits == 0
        assert service.stats.misses == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])