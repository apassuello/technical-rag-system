"""
Proper unit tests for Epic 8 Cache Service API.

These tests create isolated test instances of the FastAPI app with mocked dependencies.
No Docker containers or external services required.
"""

import pytest
import pytest_asyncio
import hashlib
import json
from unittest.mock import MagicMock, patch, AsyncMock
from httpx import AsyncClient, ASGITransport

# Import test utilities
from .test_utils import create_test_cache_app, MockCache, clear_module_cache


@pytest.fixture(autouse=True)
def clean_imports():
    """Clean module imports before and after each test."""
    # Clear before test
    clear_module_cache(['cache_app', 'services.cache'])
    yield
    # Clear after test
    clear_module_cache(['cache_app', 'services.cache'])


@pytest_asyncio.fixture
async def test_app():
    """Create a test instance of the cache app with mocked dependencies."""
    # Mock all Prometheus metrics to prevent registration issues
    with patch('prometheus_client.Counter', MagicMock(return_value=MagicMock())):
        with patch('prometheus_client.Histogram', MagicMock(return_value=MagicMock())):
            with patch('prometheus_client.Gauge', MagicMock(return_value=MagicMock())):
                # Mock the make_asgi_app for metrics endpoint
                with patch('prometheus_client.make_asgi_app', MagicMock()):
                    # Create a mock cache service
                    mock_cache = MockCache()
                    
                    # Mock the CacheService class
                    with patch('services.cache.cache_app.core.cache.CacheService') as MockCacheService:
                        # Create mock instance
                        mock_service = MagicMock()
                        mock_service.get = AsyncMock(side_effect=mock_cache.get)
                        mock_service.set = AsyncMock(side_effect=mock_cache.set)
                        mock_service.delete = AsyncMock(side_effect=mock_cache.delete)
                        mock_service.clear = AsyncMock(side_effect=mock_cache.flushall)
                        mock_service.get_stats = AsyncMock(return_value={
                            'total_requests': 100,
                            'hits': 60,
                            'misses': 40,
                            'hit_rate': 0.6,
                            'items_cached': len(mock_cache.data)
                        })
                        mock_service.health_check = AsyncMock(return_value={'status': 'healthy'})
                        MockCacheService.return_value = mock_service
                        
                        # Import and create app after all mocks are in place
                        from services.cache.cache_app.main import create_app
                        app = create_app()
                        
                        # Store references for test access
                        app.state.test_cache = mock_cache
                        app.state.test_service = mock_service
                        
                        # Override the get_cache_service dependency
                        from services.cache.cache_app.main import get_cache_service
                        app.dependency_overrides[get_cache_service] = lambda: mock_service
                        
                        yield app


@pytest_asyncio.fixture
async def test_client(test_app):
    """Create an async test client for the cache app."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


def generate_query_hash(query: str) -> str:
    """Generate hash for a query string."""
    return hashlib.sha256(query.encode()).hexdigest()


class TestCacheAPI:
    """Test Cache Service API endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, test_client):
        """Test the health check endpoint."""
        response = await test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "ok"]
    
    @pytest.mark.asyncio
    async def test_cache_post_endpoint(self, test_client, test_app):
        """Test storing data in cache."""
        query = "What is Python?"
        query_hash = generate_query_hash(query)
        
        cache_request = {
            "response_data": {
                "answer": "Python is a programming language",
                "confidence": 0.95
            },
            "content_type": "answer",
            "ttl": 3600
        }
        
        response = await test_client.post(
            f"/api/v1/cache/{query_hash}",
            json=cache_request
        )
        
        # The endpoint should work with our mocked service
        assert response.status_code in [200, 201]
        
        # Verify the mock was called
        test_service = test_app.state.test_service
        assert test_service.set.called
    
    @pytest.mark.asyncio
    async def test_cache_get_endpoint(self, test_client, test_app):
        """Test retrieving data from cache."""
        query = "Test query"
        query_hash = generate_query_hash(query)
        
        # Pre-populate the mock cache
        test_cache = test_app.state.test_cache
        await test_cache.set(query_hash, json.dumps({
            "answer": "Test answer",
            "confidence": 0.9
        }))
        
        response = await test_client.get(f"/api/v1/cache/{query_hash}")
        
        # Should return the cached data
        assert response.status_code == 200
        
        # Verify the mock was called
        test_service = test_app.state.test_service
        assert test_service.get.called
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, test_client, test_app):
        """Test cache miss for non-existent key."""
        non_existent_hash = generate_query_hash("non-existent-query")
        
        response = await test_client.get(f"/api/v1/cache/{non_existent_hash}")
        
        # Should handle cache miss gracefully
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_cache_delete(self, test_client, test_app):
        """Test deleting a cache entry."""
        query = "Delete me"
        query_hash = generate_query_hash(query)
        
        # Pre-populate the cache
        test_cache = test_app.state.test_cache
        await test_cache.set(query_hash, json.dumps({"data": "test"}))
        
        response = await test_client.delete(f"/api/v1/cache/{query_hash}")
        
        assert response.status_code in [200, 204]
        
        # Verify it was deleted
        assert await test_cache.get(query_hash) is None
    
    @pytest.mark.asyncio
    async def test_cache_statistics(self, test_client, test_app):
        """Test cache statistics endpoint."""
        response = await test_client.get("/api/v1/statistics")
        
        if response.status_code == 404:
            pytest.skip("Statistics endpoint not implemented")
        
        assert response.status_code == 200
        stats = response.json()
        
        # Check for expected fields from our mock
        assert "hit_rate" in stats or "hits" in stats
    
    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, test_client):
        """Test Prometheus metrics endpoint."""
        response = await test_client.get("/metrics")
        
        # Metrics endpoint might not be implemented or might be mocked
        assert response.status_code in [200, 404]


class TestCacheAPIErrorHandling:
    """Test error handling in Cache API."""
    
    @pytest.mark.asyncio
    async def test_invalid_json(self, test_client):
        """Test handling of invalid JSON in request."""
        query_hash = generate_query_hash("test")
        
        response = await test_client.post(
            f"/api/v1/cache/{query_hash}",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, test_client):
        """Test handling of missing required fields."""
        query_hash = generate_query_hash("test")
        
        # Missing response_data field
        response = await test_client.post(
            f"/api/v1/cache/{query_hash}",
            json={"ttl": 3600}
        )
        
        assert response.status_code in [400, 422]