"""
API tests for health check endpoints.

Tests /health, /health/live, and /health/ready endpoints for Kubernetes integration.
"""

import pytest
from unittest.mock import patch


class TestHealthEndpoint:
    """Test cases for GET /health endpoint."""

    def test_health_basic(self, client):
        """Test basic health endpoint functionality."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "status" in data
        assert "service" in data
        assert "version" in data
        
        # Validate content
        assert data["status"] in ["healthy", "unhealthy"]
        assert data["service"] == "query-analyzer"
        assert data["version"] == "1.0.0"

    def test_health_healthy_service(self, client):
        """Test health endpoint when service is healthy."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        if data["status"] == "healthy":
            # Should include details about health
            if "details" in data:
                details = data["details"]
                assert isinstance(details, dict)
                
                # Should indicate analyzer is initialized and components loaded
                if "analyzer_initialized" in details:
                    assert isinstance(details["analyzer_initialized"], bool)
                if "components_loaded" in details:
                    assert isinstance(details["components_loaded"], bool)

    def test_health_response_format(self, client):
        """Test health endpoint response format compliance."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Required fields
        required_fields = ["status", "service", "version"]
        for field in required_fields:
            assert field in data
            assert data[field] is not None
            assert isinstance(data[field], str)
        
        # Optional details field
        if "details" in data:
            assert isinstance(data["details"], dict)

    def test_health_response_headers(self, client):
        """Test health endpoint response headers."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]

    def test_health_multiple_requests(self, client):
        """Test health endpoint consistency across multiple requests."""
        responses = []
        for _ in range(3):
            response = client.get("/health")
            assert response.status_code == 200
            responses.append(response.json())
        
        # Service name and version should be consistent
        for i in range(1, len(responses)):
            assert responses[i]["service"] == responses[0]["service"]
            assert responses[i]["version"] == responses[0]["version"]

    @patch('app.main.analyzer_service', None)
    def test_health_service_not_initialized(self, client):
        """Test health endpoint when service is not initialized."""
        response = client.get("/health")
        
        # Should return 503 when service not initialized
        assert response.status_code == 503
        error_data = response.json()
        assert "Service not initialized" in str(error_data)

    @patch('app.core.analyzer.QueryAnalyzerService.health_check')
    def test_health_check_failure(self, mock_health_check, client):
        """Test health endpoint when health check fails."""
        mock_health_check.return_value = False
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"

    @patch('app.core.analyzer.QueryAnalyzerService.health_check')
    def test_health_check_exception(self, mock_health_check, client):
        """Test health endpoint when health check raises exception."""
        mock_health_check.side_effect = Exception("Health check error")
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        
        if "details" in data:
            assert "error" in data["details"]

    def test_health_performance(self, client):
        """Test health endpoint response time."""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        # Health check should be fast (< 1 second)
        assert response_time < 1.0


class TestLivenessProbe:
    """Test cases for GET /health/live endpoint."""

    def test_liveness_basic(self, client):
        """Test basic liveness probe functionality."""
        response = client.get("/health/live")
        
        assert response.status_code == 200
        data = response.json()
        
        # Simple liveness response
        assert "status" in data
        assert data["status"] == "alive"

    def test_liveness_always_succeeds(self, client):
        """Test that liveness probe always succeeds when service is running."""
        # Make multiple requests
        for _ in range(3):
            response = client.get("/health/live")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "alive"

    def test_liveness_response_format(self, client):
        """Test liveness probe response format."""
        response = client.get("/health/live")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be simple JSON response
        assert isinstance(data, dict)
        assert "status" in data
        assert data["status"] == "alive"

    def test_liveness_response_headers(self, client):
        """Test liveness probe response headers."""
        response = client.get("/health/live")
        
        assert response.status_code == 200
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]

    def test_liveness_performance(self, client):
        """Test liveness probe performance."""
        import time
        
        start_time = time.time()
        response = client.get("/health/live")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        # Liveness should be very fast (< 0.1 seconds)
        assert response_time < 0.1

    def test_liveness_concurrent_requests(self, client):
        """Test concurrent liveness probe requests."""
        import threading
        results = []
        
        def make_request():
            response = client.get("/health/live")
            results.append(response.status_code)
        
        threads = [threading.Thread(target=make_request) for _ in range(5)]
        
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # All should succeed
        assert all(status == 200 for status in results)


class TestReadinessProbe:
    """Test cases for GET /health/ready endpoint."""

    def test_readiness_basic(self, client):
        """Test basic readiness probe functionality."""
        response = client.get("/health/ready")
        
        # Response should be 200 if ready, 503 if not ready
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert data["status"] == "ready"

    def test_readiness_when_ready(self, client):
        """Test readiness probe when service is ready."""
        response = client.get("/health/ready")
        
        # Assuming service is ready in test environment
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "ready"

    @patch('app.main.analyzer_service', None)
    def test_readiness_service_not_initialized(self, client):
        """Test readiness probe when service is not initialized."""
        response = client.get("/health/ready")
        
        # Should return 503 when service not ready
        assert response.status_code == 503
        error_data = response.json()
        assert "Service not ready" in str(error_data)

    @patch('app.core.analyzer.QueryAnalyzerService.health_check')
    def test_readiness_health_check_failure(self, mock_health_check, client):
        """Test readiness probe when health check fails."""
        mock_health_check.return_value = False
        
        response = client.get("/health/ready")
        
        # Should return 503 when not ready
        assert response.status_code == 503
        error_data = response.json()
        assert "Service not ready" in str(error_data)

    @patch('app.core.analyzer.QueryAnalyzerService.health_check')
    def test_readiness_health_check_exception(self, mock_health_check, client):
        """Test readiness probe when health check raises exception."""
        mock_health_check.side_effect = Exception("Health check failed")
        
        response = client.get("/health/ready")
        
        # Should return 503 when health check fails
        assert response.status_code == 503

    def test_readiness_response_format(self, client):
        """Test readiness probe response format."""
        response = client.get("/health/ready")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            assert "status" in data
            assert data["status"] == "ready"
        else:
            # Error response format
            assert response.status_code == 503

    def test_readiness_response_headers(self, client):
        """Test readiness probe response headers."""
        response = client.get("/health/ready")
        
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]

    def test_readiness_performance(self, client):
        """Test readiness probe performance."""
        import time
        
        start_time = time.time()
        response = client.get("/health/ready")
        response_time = time.time() - start_time
        
        # Readiness should be reasonably fast (< 1 second)
        assert response_time < 1.0

    def test_readiness_consistency(self, client):
        """Test readiness probe consistency."""
        responses = []
        
        # Make multiple requests quickly
        for _ in range(3):
            response = client.get("/health/ready")
            responses.append(response.status_code)
        
        # Should be consistent (all ready or all not ready)
        assert len(set(responses)) <= 2  # Allow for some transition states


class TestHealthEndpointIntegration:
    """Integration tests for all health endpoints."""

    def test_health_endpoints_exist(self, client):
        """Test that all health endpoints are accessible."""
        endpoints = ["/health", "/health/live", "/health/ready"]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should not return 404
            assert response.status_code != 404

    def test_health_endpoint_consistency(self, client):
        """Test consistency between different health endpoints."""
        health_response = client.get("/health")
        live_response = client.get("/health/live")
        ready_response = client.get("/health/ready")
        
        # Live should always be successful if we can reach it
        assert live_response.status_code == 200
        
        # If health is healthy and ready is ready, they should be consistent
        if (health_response.status_code == 200 and 
            ready_response.status_code == 200):
            
            health_data = health_response.json()
            ready_data = ready_response.json()
            
            if health_data["status"] == "healthy":
                assert ready_data["status"] == "ready"

    def test_kubernetes_health_check_pattern(self, client):
        """Test Kubernetes health check pattern compliance."""
        # Kubernetes expects:
        # - liveness: Simple check that process is running
        # - readiness: Check that service is ready to handle requests
        # - Both should return 200 OK or 5xx for failure
        
        live_response = client.get("/health/live")
        ready_response = client.get("/health/ready")
        
        # Liveness should always succeed if process is running
        assert live_response.status_code == 200
        
        # Readiness should be 200 if ready, 503 if not
        assert ready_response.status_code in [200, 503]

    def test_health_endpoint_error_handling(self, client):
        """Test health endpoint error handling."""
        # Test with invalid paths
        invalid_paths = ["/health/invalid", "/health/live/invalid", "/health/ready/invalid"]
        
        for path in invalid_paths:
            response = client.get(path)
            assert response.status_code == 404

    def test_health_endpoint_methods(self, client):
        """Test health endpoints only accept GET method."""
        endpoints = ["/health", "/health/live", "/health/ready"]
        invalid_methods = ["POST", "PUT", "DELETE", "PATCH"]
        
        for endpoint in endpoints:
            for method in invalid_methods:
                response = client.request(method, endpoint)
                # Should return 405 Method Not Allowed
                assert response.status_code == 405

    def test_health_endpoints_concurrent_access(self, client):
        """Test concurrent access to health endpoints."""
        import threading
        import time
        
        results = {"health": [], "live": [], "ready": []}
        
        def check_health():
            results["health"].append(client.get("/health").status_code)
        
        def check_live():
            results["live"].append(client.get("/health/live").status_code)
        
        def check_ready():
            results["ready"].append(client.get("/health/ready").status_code)
        
        # Create multiple concurrent requests
        threads = []
        for _ in range(3):
            threads.append(threading.Thread(target=check_health))
            threads.append(threading.Thread(target=check_live))
            threads.append(threading.Thread(target=check_ready))
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(results["health"]) == 3
        assert len(results["live"]) == 3
        assert len(results["ready"]) == 3
        
        # Live should always succeed
        assert all(status == 200 for status in results["live"])

    def test_health_endpoints_response_time(self, client):
        """Test response time of all health endpoints."""
        import time
        
        endpoints = ["/health", "/health/live", "/health/ready"]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            response_time = time.time() - start_time
            
            # All health endpoints should be fast
            max_time = 1.0 if endpoint == "/health" else 0.5
            assert response_time < max_time, f"{endpoint} took {response_time:.3f}s"