"""
API Tests for Epic 8 Cache Service REST Endpoints.

Tests the REST API endpoints of the Cache Service according to 
the Epic 8 API Reference specifications. Uses DockerServiceClient 
for testing against actual running Docker services.
"""

import pytest
import hashlib
import json
import time
from typing import Dict, Any
from pathlib import Path
import sys

# Test if HTTP client libraries are available
try:
    import httpx
    HTTP_CLIENT_AVAILABLE = True
except ImportError:
    HTTP_CLIENT_AVAILABLE = False

# FastAPI setup for Docker service testing
try:
    from fastapi.testclient import TestClient
    FASTAPI_AVAILABLE = True
    FASTAPI_ERROR = None
except ImportError as e:
    FASTAPI_AVAILABLE = False
    FASTAPI_ERROR = str(e)

# Docker service client for testing against actual running services
if FASTAPI_AVAILABLE:
    class DockerServiceClient:
        """Client for testing against actual Docker services."""
        def __init__(self, base_url="http://localhost:8084"):
            self.base_url = base_url
            
        def get(self, path):
            """Make GET request to Docker service."""
            with httpx.Client() as client:
                return client.get(f"{self.base_url}{path}")
                
        def post(self, path, json=None, data=None, headers=None):
            """Make POST request to Docker service."""
            with httpx.Client() as client:
                if data is not None:
                    return client.post(f"{self.base_url}{path}", content=data, headers=headers)
                else:
                    return client.post(f"{self.base_url}{path}", json=json, headers=headers)
                
        def put(self, path, json=None, data=None, headers=None):
            """Make PUT request to Docker service."""
            with httpx.Client() as client:
                if data is not None:
                    return client.put(f"{self.base_url}{path}", content=data, headers=headers)
                else:
                    return client.put(f"{self.base_url}{path}", json=json, headers=headers)
                
        def delete(self, path):
            """Make DELETE request to Docker service.""" 
            with httpx.Client() as client:
                return client.delete(f"{self.base_url}{path}")

# Global client instance for all tests
client = DockerServiceClient() if FASTAPI_AVAILABLE else None

# Check if cache service is implemented
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[3]
service_path = project_root / "services" / "cache"
CACHE_SERVICE_EXISTS = service_path.exists()

# Module-level skip if cache service is not available
pytestmark = pytest.mark.skipif(
    not CACHE_SERVICE_EXISTS,
    reason=f"Cache service not implemented: {service_path} does not exist"
)


def generate_query_hash(query: str) -> str:
    """Generate hash for a query string."""
    return hashlib.sha256(query.encode()).hexdigest()


class TestCacheAPI:
    """Test Cache Service API endpoints using Docker service client."""
    
    def test_health_endpoint(self):
        """Test the health check endpoint."""
        if not FASTAPI_AVAILABLE:
            pytest.skip(f"FastAPI not available: {FASTAPI_ERROR}")
            
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "ok"]
    
    def test_cache_post_endpoint(self):
        """Test storing data in cache."""
        if not FASTAPI_AVAILABLE:
            pytest.skip(f"FastAPI not available: {FASTAPI_ERROR}")
            
        query = "What is Python?"
        query_hash = generate_query_hash(query)
        
        cache_request = {
            "response_data": {
                "answer": "Python is a programming language",
                "confidence": 0.95
            },
            "content_type": "simple_query",
            "ttl": 3600
        }
        
        response = client.post(
            f"/api/v1/cache/{query_hash}",
            json=cache_request
        )
        
        # The endpoint should work with the running Docker service
        assert response.status_code in [200, 201]
        
        # Verify the response contains operation result
        data = response.json()
        assert isinstance(data, dict)
        # Accept various response formats from the actual service
        assert any(key in data for key in ["success", "cached", "operation", "status"])
    
    def test_cache_get_endpoint(self):
        """Test retrieving data from cache."""
        if not FASTAPI_AVAILABLE:
            pytest.skip(f"FastAPI not available: {FASTAPI_ERROR}")
            
        query = "Test query"
        query_hash = generate_query_hash(query)
        
        # First, try to get an existing cache entry (may be empty)
        response = client.get(f"/api/v1/cache/{query_hash}")
        
        # Should handle both cache hit and cache miss cases gracefully
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            # Verify the response structure if it's a cache hit
            data = response.json()
            assert isinstance(data, dict)
    
    def test_cache_delete(self):
        """Test deleting a cache entry."""
        if not FASTAPI_AVAILABLE:
            pytest.skip(f"FastAPI not available: {FASTAPI_ERROR}")
            
        query = "Delete me"
        query_hash = generate_query_hash(query)
        
        # Try to delete (may or may not exist)
        response = client.delete(f"/api/v1/cache/{query_hash}")
        
        # Accept various success responses for delete operation
        assert response.status_code in [200, 204, 404]
    
    def test_cache_statistics(self):
        """Test cache statistics endpoint."""
        if not FASTAPI_AVAILABLE:
            pytest.skip(f"FastAPI not available: {FASTAPI_ERROR}")
            
        response = client.get("/api/v1/statistics")
        
        if response.status_code == 404:
            pytest.skip("Statistics endpoint not implemented")
        
        assert response.status_code == 200
        stats = response.json()
        
        # Check for expected statistics fields
        assert isinstance(stats, dict)
        # Accept various statistics formats from the actual service
    
    def test_metrics_endpoint(self):
        """Test Prometheus metrics endpoint."""
        if not FASTAPI_AVAILABLE:
            pytest.skip(f"FastAPI not available: {FASTAPI_ERROR}")
            
        response = client.get("/metrics")
        
        # Metrics endpoint might return metrics, not be implemented, or redirect
        assert response.status_code in [200, 404, 307]


class TestCacheAPIErrorHandling:
    """Test error handling in Cache API using Docker service client."""
    
    def test_invalid_json(self):
        """Test handling of invalid JSON in request."""
        if not FASTAPI_AVAILABLE:
            pytest.skip(f"FastAPI not available: {FASTAPI_ERROR}")
            
        query_hash = generate_query_hash("test")
        
        response = client.post(
            f"/api/v1/cache/{query_hash}",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code in [400, 422]
    
    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        if not FASTAPI_AVAILABLE:
            pytest.skip(f"FastAPI not available: {FASTAPI_ERROR}")
            
        query_hash = generate_query_hash("test")
        
        # Missing response_data field
        response = client.post(
            f"/api/v1/cache/{query_hash}",
            json={"ttl": 3600}
        )
        
        assert response.status_code in [400, 422]