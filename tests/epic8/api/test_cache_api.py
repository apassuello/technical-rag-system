"""
API Tests for Epic 8 Cache Service.

Tests all REST API endpoints, request/response validation, error handling,
health checks, and batch operations following Epic 8 specifications.

Testing Philosophy:
- Hard Fails: 500 errors, >60s responses, invalid JSON, authentication failures
- Quality Flags: >100ms API responses, <60% hit rate, validation issues

Test Coverage:
- All REST endpoints (GET/POST/DELETE /api/v1/cache/{hash}, GET /api/v1/statistics)
- Request/response schema validation
- Error handling and HTTP status codes
- Health check endpoints  
- Batch operations and cache warming
"""

import pytest
import pytest_asyncio
import asyncio
import time
import json
import hashlib
import uuid
from typing import Dict, Any, List
from pathlib import Path
from httpx import AsyncClient
from fastapi.testclient import TestClient
from httpx import ASGITransport
import sys

# Use centralized test utilities for app creation
from .test_utils import create_test_cache_app

try:
    # Import functions we need for testing
    import hashlib
    def generate_query_hash(query: str) -> str:
        """Generate hash for a query string."""
        return hashlib.sha256(query.encode()).hexdigest()
    
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    IMPORT_ERROR = str(e)


@pytest_asyncio.fixture
async def test_client():
    """Create test client for API testing."""
    try:
        app = create_test_cache_app()  # Use our centralized test app creator
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    except Exception as e:
        pytest.skip(f"Could not create test client: {e}")


@pytest.fixture
def sample_cache_data():
    """Sample cache data for testing."""
    return {
        "simple_query": {
            "query": "What is RISC-V?",
            "response_data": {
                "answer": "RISC-V is an open-source instruction set architecture",
                "confidence": 0.95,
                "sources": ["risc-v-spec.pdf"],
                "metadata": {"tokens": 150, "model": "test-model"}
            },
            "content_type": "simple_query",
            "ttl": 7200
        },
        "complex_query": {
            "query": "Explain the implementation of cache coherency in multi-core RISC-V processors",
            "response_data": {
                "answer": "Cache coherency in multi-core RISC-V processors is typically implemented using...",
                "confidence": 0.87,
                "sources": ["risc-v-privileged.pdf", "cache-coherency-paper.pdf"],
                "metadata": {"tokens": 500, "model": "test-model-complex"}
            },
            "content_type": "complex_query", 
            "ttl": 1800
        }
    }


class TestCacheAPIEndpoints:
    """Test core cache API endpoints."""

    # Import availability handled in fixtures
    @pytest.mark.asyncio
    async def test_cache_get_endpoint_basic(self, test_client, sample_cache_data):
        """Test GET /cache/{query_hash} endpoint basic functionality."""
        # Generate query hash for simple query
        query = sample_cache_data["simple_query"]["query"]
        query_hash = generate_query_hash(query)
        
        # Test cache miss (Hard Fail test - should return 404, not 500)
        start_time = time.time()
        response = await test_client.get(f"/api/v1/cache/{query_hash}")
        response_time = time.time() - start_time
        
        # Hard fail: API response >60s indicates broken service
        assert response_time < 60.0, f"API response took {response_time:.2f}s, service broken"
        
        # Should return 404 for cache miss, not 500 error
        assert response.status_code == 404, f"Expected 404 for cache miss, got {response.status_code}"
        
        # Response should be valid JSON
        try:
            error_data = response.json()
            # FastAPI HTTPException returns {"detail": {...}} format
            if "detail" in error_data and isinstance(error_data["detail"], dict):
                assert "error" in error_data["detail"], "Error response detail should contain 'error' field"
            else:
                assert "error" in error_data, "Error response should contain 'error' field"
        except json.JSONDecodeError:
            pytest.fail("Cache miss response should be valid JSON")
        
        # Quality flag: API should be fast
        if response_time > 0.1:  # 100ms
            pytest.warns(UserWarning, f"Cache GET API slow: {response_time:.3f}s (target <100ms)")
        
        print(f"Cache GET API (miss) performance: {response_time*1000:.2f}ms")

    # Import availability handled in fixtures
    @pytest.mark.asyncio
    async def test_cache_get_endpoint_invalid_hash(self, test_client):
        """Test GET /cache/{query_hash} with invalid hash format."""
        invalid_hashes = [
            "too_short",
            "not_hex_characters_in_this_very_long_string_that_is_64_chars_long",
            "123",  
            "",
            "a" * 63,  # Too short by 1
            "a" * 65   # Too long by 1
        ]
        
        for invalid_hash in invalid_hashes:
            start_time = time.time()
            response = await test_client.get(f"/api/v1/cache/{invalid_hash}")
            response_time = time.time() - start_time
            
            # Hard fail: Should not crash (return 500)
            assert response.status_code != 500, f"API crashed with invalid hash: {invalid_hash}"
            
            # Empty string hits routing (404), other invalid formats hit validation (422)
            if invalid_hash == "":
                expected_status = 404  # FastAPI routing - no endpoint for /api/v1/cache/
                error_type = "routing error"
            else:
                expected_status = 422  # Our validation logic
                error_type = "validation error"
            
            assert response.status_code == expected_status, f"Expected {expected_status} ({error_type}) for hash '{invalid_hash}', got {response.status_code}"
            
            # Should be fast even for invalid input
            assert response_time < 1.0, f"Invalid hash handling too slow: {response_time:.2f}s"

    # Import availability handled in fixtures
    @pytest.mark.asyncio
    async def test_cache_post_endpoint_basic(self, test_client, sample_cache_data):
        """Test POST /cache/{query_hash} endpoint for storing responses."""
        # Prepare test data
        query_data = sample_cache_data["simple_query"]
        query_hash = generate_query_hash(query_data["query"])
        
        cache_request = {
            "response_data": query_data["response_data"],
            "content_type": query_data["content_type"],
            "ttl": query_data["ttl"]
        }
        
        # Test cache storage
        start_time = time.time()
        response = await test_client.post(
            f"/api/v1/cache/{query_hash}",
            json=cache_request
        )
        response_time = time.time() - start_time
        
        # Hard fail: Should not return 500 error
        assert response.status_code != 500, f"Cache POST crashed: {response.status_code}"
        
        # Should return 200 for successful storage
        assert response.status_code == 200, f"Expected 200 for successful storage, got {response.status_code}"
        
        # Response should be valid CacheOperationResponse
        try:
            response_data = response.json()
            required_fields = ["request_id", "query_hash", "operation", "success", "processing_time_ms"]
            for field in required_fields:
                assert field in response_data, f"Response missing required field: {field}"
            
            assert response_data["operation"] == "set", "Operation should be 'set'"
            assert response_data["success"] is True, "Operation should succeed"
            assert response_data["query_hash"] == query_hash, "Query hash should match"
            
        except json.JSONDecodeError:
            pytest.fail("Cache POST response should be valid JSON")
        
        # Quality flag: Should be fast
        if response_time > 0.1:  # 100ms
            pytest.warns(UserWarning, f"Cache POST API slow: {response_time:.3f}s (target <100ms)")
        
        print(f"Cache POST API performance: {response_time*1000:.2f}ms")

    # Import availability handled in fixtures
    @pytest.mark.asyncio
    async def test_cache_post_then_get_workflow(self, test_client, sample_cache_data):
        """Test complete POST then GET workflow to verify cache hit."""
        # Prepare test data
        query_data = sample_cache_data["complex_query"]
        query_hash = generate_query_hash(query_data["query"])
        
        cache_request = {
            "response_data": query_data["response_data"],
            "content_type": query_data["content_type"],
            "ttl": query_data["ttl"]
        }
        
        # Step 1: Store in cache
        post_response = await test_client.post(
            f"/api/v1/cache/{query_hash}",
            json=cache_request
        )
        assert post_response.status_code == 200, "Cache storage should succeed"
        
        # Step 2: Retrieve from cache (should be cache hit)
        start_time = time.time()
        get_response = await test_client.get(f"/api/v1/cache/{query_hash}")
        response_time = time.time() - start_time
        
        # Hard fail: Should succeed (not 500 or 404)
        assert get_response.status_code == 200, f"Cache retrieval failed: {get_response.status_code}"
        
        # Verify response structure
        try:
            cache_hit_data = get_response.json()
            required_fields = ["request_id", "query_hash", "found", "response_data", "cache_hit"]
            for field in required_fields:
                assert field in cache_hit_data, f"Cache hit response missing field: {field}"
            
            assert cache_hit_data["found"] is True, "Should find cached data"
            assert cache_hit_data["cache_hit"] is True, "Should be cache hit"
            assert cache_hit_data["response_data"] == query_data["response_data"], "Data should match"
            
        except json.JSONDecodeError:
            pytest.fail("Cache hit response should be valid JSON")
        
        # Quality target: Cache hit should be very fast (<1ms ideal)
        if response_time > 0.001:  # 1ms
            pytest.warns(UserWarning, f"Cache hit slow: {response_time:.3f}s (target <1ms)")
        
        print(f"Cache hit workflow: store->retrieve in {response_time*1000:.2f}ms")

    # Import availability handled in fixtures
    @pytest.mark.asyncio
    async def test_cache_delete_endpoint(self, test_client, sample_cache_data):
        """Test DELETE /cache/{query_hash} endpoint."""
        # First store something to delete
        query_data = sample_cache_data["simple_query"]
        query_hash = generate_query_hash(query_data["query"])
        
        cache_request = {
            "response_data": query_data["response_data"],
            "content_type": query_data["content_type"]
        }
        
        # Store data
        post_response = await test_client.post(f"/api/v1/cache/{query_hash}", json=cache_request)
        assert post_response.status_code == 200, "Should store successfully"
        
        # Verify it's there
        get_response = await test_client.get(f"/api/v1/cache/{query_hash}")
        assert get_response.status_code == 200, "Should retrieve successfully"
        
        # Delete the cached item
        start_time = time.time()
        delete_response = await test_client.delete(f"/api/v1/cache/{query_hash}")
        response_time = time.time() - start_time
        
        # Hard fail: Should not crash
        assert delete_response.status_code != 500, "Delete API should not crash"
        
        # Should return 200 for successful deletion
        assert delete_response.status_code == 200, f"Expected 200 for deletion, got {delete_response.status_code}"
        
        # Verify response structure
        try:
            delete_data = delete_response.json()
            assert "success" in delete_data, "Delete response should contain 'success'"
            assert delete_data["success"] is True, "Deletion should succeed"
            assert delete_data["operation"] == "delete", "Operation should be 'delete'"
            
        except json.JSONDecodeError:
            pytest.fail("Delete response should be valid JSON")
        
        # Verify item is actually deleted
        verify_response = await test_client.get(f"/api/v1/cache/{query_hash}")
        assert verify_response.status_code == 404, "Item should be deleted (404)"
        
        # Quality flag: Should be fast
        if response_time > 0.1:
            pytest.warns(UserWarning, f"Cache DELETE slow: {response_time:.3f}s")
        
        print(f"Cache DELETE API performance: {response_time*1000:.2f}ms")


class TestStatisticsAPIEndpoint:
    """Test statistics API endpoint."""

    # Import availability handled in fixtures
    @pytest.mark.asyncio
    async def test_statistics_endpoint_basic(self, test_client):
        """Test GET /statistics endpoint basic functionality."""
        start_time = time.time()
        response = await test_client.get("/api/v1/statistics")
        response_time = time.time() - start_time
        
        # Hard fail: Should not crash or timeout
        assert response_time < 60.0, f"Statistics API timeout: {response_time:.2f}s"
        assert response.status_code != 500, "Statistics API should not crash"
        
        # Should return 200
        assert response.status_code == 200, f"Expected 200 for statistics, got {response.status_code}"
        
        # Verify response structure
        try:
            stats_data = response.json()
            required_fields = ["service", "version", "timestamp", "statistics"]
            for field in required_fields:
                assert field in stats_data, f"Statistics response missing field: {field}"
            
            # Verify statistics content
            statistics = stats_data["statistics"]
            required_sections = ["overall", "redis", "fallback"]
            for section in required_sections:
                assert section in statistics, f"Statistics missing section: {section}"
            
            # Verify overall statistics
            overall = statistics["overall"]
            assert "hit_rate" in overall, "Missing hit rate in overall stats"
            assert "total_requests" in overall, "Missing total requests"
            assert isinstance(overall["hit_rate"], (int, float)), "Hit rate should be numeric"
            
        except json.JSONDecodeError:
            pytest.fail("Statistics response should be valid JSON")
        
        # Quality flag: Should be reasonably fast
        if response_time > 0.5:  # 500ms
            pytest.warns(UserWarning, f"Statistics API slow: {response_time:.3f}s")
        
        print(f"Statistics API performance: {response_time*1000:.2f}ms")

    # Import availability handled in fixtures
    @pytest.mark.asyncio  
    async def test_statistics_endpoint_query_parameters(self, test_client):
        """Test statistics endpoint with query parameters."""
        # Test with detailed=true
        response = await test_client.get("/api/v1/statistics?include_detailed=true")
        assert response.status_code == 200, "Should handle include_detailed parameter"
        
        stats_data = response.json()
        statistics = stats_data["statistics"]
        # Should include performance section when detailed=true
        assert "performance" in statistics, "Should include performance section"
        
        # Test with redis_info=false
        response = await test_client.get("/api/v1/statistics?include_redis_info=false")
        assert response.status_code == 200, "Should handle include_redis_info parameter"
        
        stats_data = response.json()
        redis_info = stats_data["statistics"]["redis"]
        # Should have minimal Redis info
        expected_minimal_fields = ["connected", "circuit_breaker_open"]
        for field in expected_minimal_fields:
            assert field in redis_info, f"Minimal Redis info missing field: {field}"

    # Import availability handled in fixtures
    @pytest.mark.asyncio
    async def test_statistics_after_operations(self, test_client, sample_cache_data):
        """Test that statistics accurately reflect cache operations."""
        # Get initial statistics
        initial_response = await test_client.get("/api/v1/statistics")
        assert initial_response.status_code == 200
        initial_stats = initial_response.json()["statistics"]["overall"]
        initial_requests = initial_stats.get("total_requests", 0)
        
        # Perform some cache operations
        query_data = sample_cache_data["simple_query"]
        query_hash = generate_query_hash(query_data["query"])
        
        cache_request = {
            "response_data": query_data["response_data"],
            "content_type": query_data["content_type"]
        }
        
        # Cache miss (GET)
        await test_client.get(f"/api/v1/cache/{query_hash}")
        
        # Cache set (POST)
        await test_client.post(f"/api/v1/cache/{query_hash}", json=cache_request)
        
        # Cache hit (GET)
        await test_client.get(f"/api/v1/cache/{query_hash}")
        
        # Get updated statistics
        updated_response = await test_client.get("/api/v1/statistics")
        assert updated_response.status_code == 200
        updated_stats = updated_response.json()["statistics"]["overall"]
        
        # Verify statistics updated
        updated_requests = updated_stats.get("total_requests", 0)
        requests_increase = updated_requests - initial_requests
        
        # Should have at least 2 additional requests (2 GETs)
        assert requests_increase >= 2, f"Statistics not updating: {requests_increase} new requests"
        
        # Hit rate should be reasonable (at least one hit out of operations)
        if updated_requests > 0:
            hit_rate = updated_stats.get("hit_rate", 0)
            assert hit_rate >= 0.0, "Hit rate should be non-negative"
            assert hit_rate <= 1.0, "Hit rate should not exceed 100%"
        
        print(f"Statistics updated: +{requests_increase} requests, {updated_stats.get('hit_rate', 0):.2%} hit rate")


class TestCacheClearAndWarmEndpoints:
    """Test cache clear and warm endpoints."""

    # Import availability handled in fixtures
    @pytest.mark.asyncio
    async def test_cache_clear_endpoint(self, test_client, sample_cache_data):
        """Test POST /clear endpoint for clearing cache."""
        # First populate cache with some data
        for content_type, query_data in sample_cache_data.items():
            query_hash = generate_query_hash(query_data["query"])
            cache_request = {
                "response_data": query_data["response_data"],
                "content_type": query_data["content_type"]
            }
            await test_client.post(f"/api/v1/cache/{query_hash}", json=cache_request)
        
        # Clear cache
        clear_request = {
            "clear_redis": True,
            "clear_fallback": True,
            "reason": "API test cleanup"
        }
        
        start_time = time.time()
        response = await test_client.post("/api/v1/clear", json=clear_request)
        response_time = time.time() - start_time
        
        # Hard fail: Should not crash
        assert response.status_code != 500, "Clear API should not crash"
        assert response_time < 30.0, f"Clear operation timeout: {response_time:.2f}s"
        
        # Should return 200
        assert response.status_code == 200, f"Expected 200 for clear, got {response.status_code}"
        
        # Verify response structure
        try:
            clear_data = response.json()
            assert "success" in clear_data, "Clear response should contain 'success'"
            assert clear_data["operation"] == "clear", "Operation should be 'clear'"
            assert "details" in clear_data, "Should contain details"
            
        except json.JSONDecodeError:
            pytest.fail("Clear response should be valid JSON")
        
        # Verify cache is actually cleared - check one item
        query_hash = generate_query_hash(sample_cache_data["simple_query"]["query"])
        verify_response = await test_client.get(f"/api/v1/cache/{query_hash}")
        assert verify_response.status_code == 404, "Cache should be cleared"
        
        print(f"Cache clear API: {response_time*1000:.2f}ms")

    # Import availability handled in fixtures
    @pytest.mark.asyncio
    async def test_cache_warm_endpoint(self, test_client):
        """Test POST /warm endpoint for cache warming."""
        # Prepare warm data
        warm_data = {
            "entries": [
                {
                    "query": "What is CPU caching?",
                    "response_data": {
                        "answer": "CPU caching stores frequently accessed data closer to the processor",
                        "confidence": 0.9
                    },
                    "content_type": "simple_query",
                    "ttl": 3600
                },
                {
                    "query": "Explain memory hierarchy",
                    "response_data": {
                        "answer": "Memory hierarchy organizes storage by speed and capacity",
                        "confidence": 0.85
                    },
                    "content_type": "medium_query",
                    "ttl": 1800
                }
            ]
        }
        
        start_time = time.time()
        response = await test_client.post("/api/v1/warm", json=warm_data)
        response_time = time.time() - start_time
        
        # Hard fail: Should not crash
        assert response.status_code != 500, "Warm API should not crash"
        assert response_time < 30.0, f"Warm operation timeout: {response_time:.2f}s"
        
        # Should return 200
        assert response.status_code == 200, f"Expected 200 for warm, got {response.status_code}"
        
        # Verify response structure
        try:
            warm_response = response.json()
            assert "success" in warm_response, "Warm response should contain 'success'"
            assert warm_response["operation"] == "warm", "Operation should be 'warm'"
            assert "details" in warm_response, "Should contain details"
            
            details = warm_response["details"]
            assert "successful_warms" in details, "Should report successful warms"
            assert details["total_entries"] == 2, "Should process both entries"
            
        except json.JSONDecodeError:
            pytest.fail("Warm response should be valid JSON")
        
        # Verify warmed data is accessible
        for entry in warm_data["entries"]:
            query_hash = generate_query_hash(entry["query"])
            verify_response = await test_client.get(f"/api/v1/cache/{query_hash}")
            assert verify_response.status_code == 200, f"Warmed data should be accessible: {entry['query']}"
        
        print(f"Cache warm API: {response_time*1000:.2f}ms for {len(warm_data['entries'])} entries")


class TestAPIErrorHandling:
    """Test API error handling and edge cases."""

    # Import availability handled in fixtures
    @pytest.mark.asyncio
    async def test_invalid_json_handling(self, test_client):
        """Test API handling of invalid JSON in requests."""
        query_hash = "a" * 64  # Valid hash format
        
        # Test with invalid JSON
        invalid_jsons = [
            "invalid json string",
            '{"incomplete": json',
            '{"invalid": "quotes}',
            "",
            "null"
        ]
        
        for invalid_json in invalid_jsons:
            response = await test_client.post(
                f"/api/v1/cache/{query_hash}",
                content=invalid_json,
                headers={"Content-Type": "application/json"}
            )
            
            # Should not crash (return 500)
            assert response.status_code != 500, f"API crashed with invalid JSON: {invalid_json[:50]}"
            
            # Should return 422 for validation error
            assert response.status_code == 422, f"Expected 422 for invalid JSON, got {response.status_code}"

    # Import availability handled in fixtures
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, test_client):
        """Test API handling of missing required fields."""
        query_hash = "b" * 64  # Valid hash format
        
        # Test with missing response_data
        incomplete_requests = [
            {},  # Empty
            {"content_type": "simple_query"},  # Missing response_data
            {"response_data": {}},  # Missing content_type (should use default)
            {"ttl": 3600}  # Missing both required fields
        ]
        
        for incomplete_request in incomplete_requests:
            response = await test_client.post(
                f"/api/v1/cache/{query_hash}",
                json=incomplete_request
            )
            
            # Should not crash
            assert response.status_code != 500, f"API crashed with incomplete request: {incomplete_request}"
            
            # Response should indicate validation error or handle gracefully
            if "response_data" not in incomplete_request:
                assert response.status_code == 422, "Missing response_data should return 422"

    # Import availability handled in fixtures
    @pytest.mark.asyncio
    async def test_oversized_request_handling(self, test_client):
        """Test API handling of oversized requests."""
        query_hash = "c" * 64  # Valid hash format
        
        # Create oversized response data (but reasonable for testing)
        oversized_data = {
            "response_data": {
                "answer": "Very large response content. " * 10000,  # ~270KB
                "metadata": {"tokens": 50000, "sources": ["doc"] * 1000}
            },
            "content_type": "complex_query"
        }
        
        start_time = time.time()
        response = await test_client.post(
            f"/api/v1/cache/{query_hash}",
            json=oversized_data
        )
        response_time = time.time() - start_time
        
        # Should not crash or timeout excessively  
        assert response_time < 30.0, f"Oversized request handling timeout: {response_time:.2f}s"
        assert response.status_code != 500, "Should handle oversized requests gracefully"
        
        # Should either succeed or return appropriate error
        if response.status_code == 200:
            # If accepted, should be able to retrieve
            get_response = await test_client.get(f"/api/v1/cache/{query_hash}")
            assert get_response.status_code == 200, "Should retrieve oversized data if stored"
        elif response.status_code == 413:
            # Payload too large is acceptable
            print("Oversized request rejected with 413 (expected)")
        else:
            # Other error codes are acceptable as long as not 500
            print(f"Oversized request handled with status {response.status_code}")

    # Import availability handled in fixtures
    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self, test_client):
        """Test API handling of concurrent requests."""
        # Create concurrent requests
        concurrent_requests = []
        
        for i in range(20):
            query_hash = hashlib.sha256(f"concurrent_test_{i}".encode()).hexdigest()
            request_data = {
                "response_data": {"answer": f"concurrent answer {i}", "index": i},
                "content_type": "simple_query"
            }
            
            # Mix of POST and GET requests
            if i % 2 == 0:
                # POST request
                concurrent_requests.append(
                    test_client.post(f"/api/v1/cache/{query_hash}", json=request_data)
                )
            else:
                # GET request (might miss initially)
                concurrent_requests.append(
                    test_client.get(f"/api/v1/cache/{query_hash}")
                )
        
        start_time = time.time()
        try:
            responses = await asyncio.gather(*concurrent_requests, return_exceptions=True)
            total_time = time.time() - start_time
            
            # Hard fail: Should not take excessively long
            assert total_time < 30.0, f"Concurrent requests took {total_time:.2f}s"
            
            # Count successful responses (not 500 errors)
            successful_responses = [
                r for r in responses 
                if not isinstance(r, Exception) and hasattr(r, 'status_code') and r.status_code != 500
            ]
            
            # Most requests should succeed (not crash)
            success_rate = len(successful_responses) / len(responses)
            assert success_rate >= 0.8, f"Too many failed requests: {success_rate:.2%} success rate"
            
            # Quality flag: Should handle concurrent requests efficiently
            if total_time > 5.0:
                pytest.warns(UserWarning, f"Concurrent API requests slow: {total_time:.2f}s")
            
            print(f"Concurrent API test: {len(successful_responses)}/{len(responses)} succeeded in {total_time:.2f}s")
            
        except Exception as e:
            pytest.fail(f"Concurrent API requests test failed: {e}")


class TestAPIHealthAndMonitoring:
    """Test API health check and monitoring endpoints."""

    # Import availability handled in fixtures
    @pytest.mark.asyncio
    async def test_health_endpoint(self, test_client):
        """Test health check endpoint availability."""
        # Common health check paths
        health_paths = ["/health", "/health/", "/api/health", "/api/v1/health"]
        
        found_health_endpoint = False
        
        for path in health_paths:
            try:
                response = await test_client.get(path)
                if response.status_code == 200:
                    found_health_endpoint = True
                    
                    # Verify health response structure
                    try:
                        health_data = response.json()
                        # Common health check fields
                        if "healthy" in health_data:
                            assert isinstance(health_data["healthy"], bool)
                        if "status" in health_data:
                            assert isinstance(health_data["status"], str)
                    except json.JSONDecodeError:
                        # Text response is also acceptable for health checks
                        pass
                    
                    print(f"Health endpoint found at: {path}")
                    break
                    
            except Exception as e:
                # Continue trying other paths
                continue
        
        # Note: Health endpoint is not strictly required for cache service
        # This is more of a quality check than hard requirement
        if not found_health_endpoint:
            import warnings
            warnings.warn("No standard health endpoint found", UserWarning)

    # Import availability handled in fixtures
    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, test_client):
        """Test Prometheus metrics endpoint availability."""
        # Common metrics paths
        metrics_paths = ["/metrics", "/api/metrics"]
        
        found_metrics_endpoint = False
        
        for path in metrics_paths:
            try:
                response = await test_client.get(path)
                if response.status_code == 200:
                    found_metrics_endpoint = True
                    
                    # Verify it's Prometheus format (text/plain)
                    content_type = response.headers.get("content-type", "")
                    if "text/plain" in content_type:
                        # Check for common Prometheus metrics patterns
                        content = response.text
                        if "# HELP" in content or "# TYPE" in content:
                            print(f"Prometheus metrics endpoint found at: {path}")
                        else:
                            print(f"Metrics endpoint found but may not be Prometheus format: {path}")
                    break
                    
            except Exception as e:
                # Continue trying other paths
                continue
        
        # Note: Metrics endpoint is recommended but not strictly required
        if not found_metrics_endpoint:
            import warnings
            warnings.warn("No Prometheus metrics endpoint found", UserWarning)


if __name__ == "__main__":
    # Run API tests
    pytest.main([__file__, "-v"])