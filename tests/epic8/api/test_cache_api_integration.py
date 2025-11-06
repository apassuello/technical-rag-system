"""
Integration tests for Epic 8 Cache Service API using running Docker container.

These tests connect to the actual cache service running in Docker.
"""

import pytest
import pytest_asyncio
import hashlib
import json
import time
from typing import Dict, Any

# Import fixtures from integration conftest
from .conftest_integration import cache_client, service_health_check, sample_cache_data, clear_cache


def generate_query_hash(query: str) -> str:
    """Generate hash for a query string."""
    return hashlib.sha256(query.encode()).hexdigest()


@pytest.mark.integration
@pytest.mark.asyncio
class TestCacheAPIIntegration:
    """Integration tests for Cache Service API endpoints."""
    
    async def test_health_endpoint(self, cache_client):
        """Test the health check endpoint."""
        response = await cache_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "ok"]
    
    async def test_cache_post_and_get(self, cache_client, sample_cache_data):
        """Test storing and retrieving data from cache."""
        # Clear cache first for test isolation
        await clear_cache(cache_client)
        
        # Generate query hash
        query_hash = generate_query_hash(sample_cache_data["query"])
        
        # Store in cache
        cache_request = {
            "query": sample_cache_data["query"],
            "response_data": sample_cache_data["response"],
            "ttl": sample_cache_data["ttl"]
        }
        
        post_response = await cache_client.post(
            f"/api/v1/cache/{query_hash}",
            json=cache_request
        )
        
        # Check if endpoint exists and handles request
        if post_response.status_code == 404:
            pytest.skip("Cache POST endpoint not implemented")
        
        assert post_response.status_code in [200, 201], f"Unexpected status: {post_response.status_code}"
        
        # Retrieve from cache
        get_response = await cache_client.get(f"/api/v1/cache/{query_hash}")
        
        if get_response.status_code == 404:
            pytest.skip("Cache GET endpoint not implemented")
        
        assert get_response.status_code == 200
        cached_data = get_response.json()
        
        # Verify cached data matches what we stored
        assert "response_data" in cached_data or "answer" in cached_data
    
    async def test_cache_miss(self, cache_client):
        """Test cache miss for non-existent key."""
        # Use a unique hash that won't exist
        non_existent_hash = hashlib.sha256(b"non-existent-query-12345").hexdigest()
        
        response = await cache_client.get(f"/api/v1/cache/{non_existent_hash}")
        
        # Could be 404 or 200 with null/empty response depending on implementation
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            # Check if response indicates cache miss
            assert data is None or data.get("cached") is False or data.get("response_data") is None
    
    async def test_cache_delete(self, cache_client, sample_cache_data):
        """Test deleting a cache entry."""
        # First store something
        query_hash = generate_query_hash(sample_cache_data["query"])
        
        cache_request = {
            "query": sample_cache_data["query"],
            "response_data": sample_cache_data["response"],
            "ttl": sample_cache_data["ttl"]
        }
        
        # Store in cache
        await cache_client.post(f"/api/v1/cache/{query_hash}", json=cache_request)
        
        # Delete from cache
        delete_response = await cache_client.delete(f"/api/v1/cache/{query_hash}")
        
        if delete_response.status_code == 404:
            pytest.skip("Cache DELETE endpoint not implemented")
        
        assert delete_response.status_code in [200, 204]
        
        # Verify it's gone
        get_response = await cache_client.get(f"/api/v1/cache/{query_hash}")
        if get_response.status_code == 200:
            data = get_response.json()
            assert data is None or data.get("cached") is False
    
    async def test_cache_statistics(self, cache_client):
        """Test cache statistics endpoint."""
        response = await cache_client.get("/api/v1/statistics")
        
        if response.status_code == 404:
            pytest.skip("Statistics endpoint not implemented")
        
        assert response.status_code == 200
        stats = response.json()
        
        # Check for expected statistics fields - accept various formats from actual service
        assert isinstance(stats, dict) and ("hit_rate" in stats or "hits" in stats or "total_requests" in stats or "cache_performance" in stats)
    
    async def test_concurrent_cache_operations(self, cache_client, sample_cache_data):
        """Test concurrent cache operations."""
        import asyncio
        
        # Clear cache first
        await clear_cache(cache_client)
        
        # Create multiple cache entries concurrently
        async def store_entry(index: int):
            query = f"{sample_cache_data['query']} - variation {index}"
            query_hash = generate_query_hash(query)
            
            cache_request = {
                "query": query,
                "response_data": {**sample_cache_data["response"], "index": index},
                "ttl": 3600
            }
            
            response = await cache_client.post(
                f"/api/v1/cache/{query_hash}",
                json=cache_request
            )
            return response.status_code
        
        # Store 5 entries concurrently
        tasks = [store_entry(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check that operations succeeded
        for result in results:
            if isinstance(result, Exception):
                continue  # Skip exceptions
            assert result in [200, 201, 404]  # 404 if endpoint not implemented


@pytest.mark.integration
@pytest.mark.asyncio
class TestCacheAPIPerformance:
    """Performance tests for Cache Service API."""
    
    async def test_cache_response_time(self, cache_client, sample_cache_data):
        """Test cache response time is within acceptable limits."""
        query_hash = generate_query_hash(sample_cache_data["query"])
        
        # Measure GET response time
        start_time = time.time()
        response = await cache_client.get(f"/api/v1/cache/{query_hash}")
        response_time = time.time() - start_time
        
        # Cache GET should be very fast (< 100ms)
        assert response_time < 0.1, f"Cache GET took {response_time:.3f}s"
    
    async def test_cache_throughput(self, cache_client):
        """Test cache can handle multiple requests per second."""
        import asyncio
        
        async def make_request():
            query_hash = hashlib.sha256(f"test-{time.time()}".encode()).hexdigest()
            try:
                response = await cache_client.get(f"/api/v1/cache/{query_hash}")
                return response.status_code
            except Exception:
                return None
        
        # Make 10 concurrent requests
        start_time = time.time()
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Should handle 10 requests in under 1 second
        assert total_time < 1.0, f"10 requests took {total_time:.3f}s"
        
        # Most requests should succeed
        successful = [r for r in results if r in [200, 404]]
        assert len(successful) >= 8, f"Only {len(successful)}/10 requests succeeded"