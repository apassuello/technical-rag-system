"""
API Tests for Epic 8 Query Analyzer Service.

Tests the REST API endpoints of the Query Analyzer Service according to 
the Epic 8 API Reference specifications. Validates request/response schemas,
error handling, and API contract compliance.

Testing Philosophy:
- Hard Fails: 500 errors, invalid JSON, missing required fields, broken endpoints
- Quality Flags: Slow responses, suboptimal status codes, missing optional fields
"""

import pytest
import asyncio
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
    try:
        import requests
        HTTP_CLIENT_AVAILABLE = True
        httpx = None
    except ImportError:
        HTTP_CLIENT_AVAILABLE = False

# Add services to path for direct testing
services_path = Path(__file__).parent.parent.parent.parent / "services" / "query-analyzer"
if services_path.exists():
    sys.path.insert(0, str(services_path))

# Try to import FastAPI app for testing
try:
    from app.api.rest import app as fastapi_app
    from fastapi.testclient import TestClient
    FASTAPI_AVAILABLE = True
except ImportError as e:
    FASTAPI_AVAILABLE = False
    FASTAPI_ERROR = str(e)


class TestQueryAnalyzerAPIBasics:
    """Test basic API functionality and endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client for API testing."""
        if not FASTAPI_AVAILABLE:
            pytest.skip(f"FastAPI not available: {FASTAPI_ERROR}")
        return TestClient(fastapi_app)

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason=f"FastAPI not available: {FASTAPI_ERROR if not FASTAPI_AVAILABLE else ''}")
    def test_api_health_endpoint(self, client):
        """Test that health endpoint is available and returns valid response."""
        try:
            response = client.get("/health")
            
            # Hard fail: 500 error or complete failure
            assert response.status_code != 500, "Health endpoint returns 500 error"
            assert response.status_code in [200, 503], f"Unexpected status code: {response.status_code}"
            
            # Parse JSON response
            data = response.json()
            assert isinstance(data, dict), "Health response must be JSON object"
            
            # Check required fields
            required_fields = ["status", "service"]
            for field in required_fields:
                assert field in data, f"Health response missing required field: {field}"
            
            # Validate field values
            assert data["status"] in ["healthy", "unhealthy"], f"Invalid status: {data['status']}"
            assert isinstance(data["service"], str), "Service field must be string"
            
            print(f"Health endpoint test passed: {data}")
            
        except Exception as e:
            pytest.fail(f"Health endpoint test failed: {e}")

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason=f"FastAPI not available: {FASTAPI_ERROR if not FASTAPI_AVAILABLE else ''}")
    def test_api_docs_endpoint(self, client):
        """Test that API documentation is available."""
        try:
            response = client.get("/docs")
            
            # Should return documentation (HTML or redirect)
            assert response.status_code in [200, 301, 302], f"Docs endpoint status: {response.status_code}"
            
            print(f"API docs endpoint accessible: {response.status_code}")
            
        except Exception as e:
            pytest.fail(f"API docs test failed: {e}")

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason=f"FastAPI not available: {FASTAPI_ERROR if not FASTAPI_AVAILABLE else ''}")
    def test_api_openapi_schema(self, client):
        """Test that OpenAPI schema is available."""
        try:
            response = client.get("/openapi.json")
            
            # Should return valid OpenAPI schema
            assert response.status_code == 200, f"OpenAPI schema status: {response.status_code}"
            
            schema = response.json()
            assert isinstance(schema, dict), "OpenAPI schema must be JSON object"
            assert "openapi" in schema, "Missing OpenAPI version"
            assert "info" in schema, "Missing API info"
            assert "paths" in schema, "Missing API paths"
            
            print(f"OpenAPI schema available with {len(schema.get('paths', {}))} endpoints")
            
        except Exception as e:
            pytest.fail(f"OpenAPI schema test failed: {e}")


class TestQueryAnalyzerAnalyzeEndpoint:
    """Test the /api/v1/analyze endpoint according to Epic 8 API specs."""

    @pytest.fixture
    def client(self):
        """Create test client for API testing."""
        if not FASTAPI_AVAILABLE:
            pytest.skip(f"FastAPI not available: {FASTAPI_ERROR}")
        return TestClient(fastapi_app)

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason=f"FastAPI not available: {FASTAPI_ERROR if not FASTAPI_AVAILABLE else ''}")
    def test_analyze_endpoint_basic(self, client):
        """Test basic analyze endpoint functionality."""
        request_data = {
            "query": "What are the key differences between RISC-V and ARM architectures?",
            "context": {
                "user_tier": "premium",
                "domain": "technical"
            },
            "options": {
                "strategy": "balanced",
                "include_features": True,
                "include_cost_estimate": True
            }
        }
        
        try:
            start_time = time.time()
            response = client.post("/api/v1/analyze", json=request_data)
            response_time = time.time() - start_time
            
            # Hard fail: 500 error or timeout
            assert response.status_code != 500, f"Analyze endpoint returns 500: {response.text}"
            assert response_time < 60.0, f"Request timeout: {response_time:.2f}s"
            
            # Should return 200 for valid request
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            
            # Parse response
            data = response.json()
            assert isinstance(data, dict), "Response must be JSON object"
            
            # Validate required response fields per API spec
            required_fields = [
                "query", "complexity", "confidence", "features", 
                "recommended_models", "cost_estimate", "routing_strategy",
                "processing_time", "metadata"
            ]
            
            missing_fields = []
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
            
            # Hard fail: Missing required fields
            assert len(missing_fields) == 0, f"Missing required fields: {missing_fields}"
            
            # Validate field types and values
            assert data["query"] == request_data["query"], "Query mismatch"
            assert data["complexity"] in ["simple", "medium", "complex"], f"Invalid complexity: {data['complexity']}"
            assert isinstance(data["confidence"], (int, float)), "Confidence must be numeric"
            assert 0.0 <= data["confidence"] <= 1.0, f"Confidence out of range: {data['confidence']}"
            assert isinstance(data["features"], dict), "Features must be object"
            assert isinstance(data["recommended_models"], list), "Recommended models must be array"
            assert isinstance(data["cost_estimate"], dict), "Cost estimate must be object"
            assert isinstance(data["processing_time"], (int, float)), "Processing time must be numeric"
            assert isinstance(data["metadata"], dict), "Metadata must be object"
            
            # Quality flags
            if response_time > 2.0:
                pytest.warns(UserWarning, f"Slow response: {response_time:.2f}s")
            
            if not data["recommended_models"]:
                pytest.warns(UserWarning, "No model recommendations provided")
            
            print(f"Analyze endpoint test passed: {data['complexity']} complexity in {response_time:.3f}s")
            
        except Exception as e:
            pytest.fail(f"Analyze endpoint test failed: {e}")

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason=f"FastAPI not available: {FASTAPI_ERROR if not FASTAPI_AVAILABLE else ''}")
    def test_analyze_endpoint_minimal_request(self, client):
        """Test analyze endpoint with minimal required data."""
        request_data = {
            "query": "What is machine learning?"
        }
        
        try:
            response = client.post("/api/v1/analyze", json=request_data)
            
            # Should work with minimal data
            assert response.status_code == 200, f"Minimal request failed: {response.status_code}"
            
            data = response.json()
            assert "complexity" in data, "Missing complexity in minimal response"
            assert "confidence" in data, "Missing confidence in minimal response"
            
            print(f"Minimal request test passed: {data['complexity']}")
            
        except Exception as e:
            pytest.fail(f"Minimal request test failed: {e}")

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason=f"FastAPI not available: {FASTAPI_ERROR if not FASTAPI_AVAILABLE else ''}")
    def test_analyze_endpoint_validation_errors(self, client):
        """Test analyze endpoint input validation."""
        
        # Test cases for validation errors
        test_cases = [
            ({}, 422, "Missing query field"),
            ({"query": ""}, 422, "Empty query"),
            ({"query": "  "}, 422, "Whitespace-only query"),
            ({"query": "Valid query", "context": "invalid"}, 422, "Invalid context type"),
            ({"query": "Valid query", "options": "invalid"}, 422, "Invalid options type")
        ]
        
        for request_data, expected_status, description in test_cases:
            try:
                response = client.post("/api/v1/analyze", json=request_data)
                
                # Should return validation error
                assert response.status_code == expected_status, f"{description}: expected {expected_status}, got {response.status_code}"
                
                # Response should be valid JSON with error info
                if response.status_code != 200:
                    data = response.json()
                    assert isinstance(data, dict), f"{description}: Error response must be JSON object"
                    # Should have error information
                    assert "detail" in data or "error" in data, f"{description}: Missing error details"
                
                print(f"Validation test passed: {description}")
                
            except Exception as e:
                pytest.fail(f"Validation test failed for {description}: {e}")

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason=f"FastAPI not available: {FASTAPI_ERROR if not FASTAPI_AVAILABLE else ''}")
    def test_analyze_endpoint_edge_cases(self, client):
        """Test analyze endpoint with edge cases."""
        
        # Test very long query
        long_query = "What is machine learning? " * 500  # ~13,000 chars
        
        test_cases = [
            ({"query": "?"}, "Single character query"),
            ({"query": "Yes"}, "Simple yes/no query"),
            ({"query": long_query[:10000]}, "Maximum length query"),  # 10k char limit per spec
            ({"query": "Query with émoji 🤖 and spëcial chars"}, "Unicode query"),
            ({"query": "Query\nwith\nmultiple\nlines"}, "Multiline query")
        ]
        
        for request_data, description in test_cases:
            try:
                response = client.post("/api/v1/analyze", json=request_data)
                
                # Should handle edge cases gracefully
                assert response.status_code in [200, 422], f"{description}: unexpected status {response.status_code}"
                
                if response.status_code == 200:
                    data = response.json()
                    assert "complexity" in data, f"{description}: Missing complexity"
                    print(f"Edge case handled: {description} -> {data['complexity']}")
                else:
                    print(f"Edge case rejected: {description} (validation error)")
                
            except Exception as e:
                pytest.fail(f"Edge case test failed for {description}: {e}")


class TestQueryAnalyzerStatusEndpoint:
    """Test the /api/v1/status endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client for API testing."""
        if not FASTAPI_AVAILABLE:
            pytest.skip(f"FastAPI not available: {FASTAPI_ERROR}")
        return TestClient(fastapi_app)

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason=f"FastAPI not available: {FASTAPI_ERROR if not FASTAPI_AVAILABLE else ''}")
    def test_status_endpoint_basic(self, client):
        """Test basic status endpoint functionality."""
        try:
            response = client.get("/api/v1/status")
            
            # Hard fail: 500 error
            assert response.status_code != 500, f"Status endpoint returns 500: {response.text}"
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert isinstance(data, dict), "Status response must be JSON object"
            
            # Check required fields per API spec
            required_fields = ["service", "version", "status", "initialized"]
            for field in required_fields:
                assert field in data, f"Status response missing {field}"
            
            # Validate field values
            assert data["service"] == "query-analyzer", f"Wrong service name: {data['service']}"
            assert isinstance(data["version"], str), "Version must be string"
            assert data["status"] in ["healthy", "unhealthy", "not_initialized"], f"Invalid status: {data['status']}"
            assert isinstance(data["initialized"], bool), "Initialized must be boolean"
            
            print(f"Status endpoint test passed: {data['status']}")
            
        except Exception as e:
            pytest.fail(f"Status endpoint test failed: {e}")

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason=f"FastAPI not available: {FASTAPI_ERROR if not FASTAPI_AVAILABLE else ''}")
    def test_status_endpoint_with_parameters(self, client):
        """Test status endpoint with query parameters."""
        try:
            response = client.get("/api/v1/status?include_performance=true&include_config=true")
            
            assert response.status_code == 200, f"Status with params failed: {response.status_code}"
            
            data = response.json()
            
            # Performance metrics should be included
            if "performance" in data:
                perf = data["performance"]
                assert isinstance(perf, dict), "Performance must be object"
                # Should have some performance metrics
                if not perf:
                    pytest.warns(UserWarning, "Performance data requested but empty")
            
            # Configuration should be included
            if "configuration" in data:
                config = data["configuration"]
                assert isinstance(config, dict), "Configuration must be object"
            
            print(f"Status with parameters test passed")
            
        except Exception as e:
            pytest.fail(f"Status with parameters test failed: {e}")


class TestQueryAnalyzerComponentsEndpoint:
    """Test the /api/v1/components endpoint."""

    @pytest.fixture  
    def client(self):
        """Create test client for API testing."""
        if not FASTAPI_AVAILABLE:
            pytest.skip(f"FastAPI not available: {FASTAPI_ERROR}")
        return TestClient(fastapi_app)

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason=f"FastAPI not available: {FASTAPI_ERROR if not FASTAPI_AVAILABLE else ''}")
    def test_components_endpoint_basic(self, client):
        """Test basic components endpoint functionality."""
        try:
            response = client.get("/api/v1/components")
            
            # Hard fail: 500 error
            assert response.status_code != 500, f"Components endpoint returns 500: {response.text}"
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert isinstance(data, dict), "Components response must be JSON object"
            
            # Check for expected structure per API spec
            expected_fields = ["service_info", "components"]
            for field in expected_fields:
                assert field in data, f"Components response missing {field}"
            
            # Validate service_info
            service_info = data["service_info"]
            assert isinstance(service_info, dict), "service_info must be object"
            assert "name" in service_info, "Missing service name"
            assert "version" in service_info, "Missing service version"
            
            # Validate components
            components = data["components"]
            assert isinstance(components, dict), "components must be object"
            
            # Should have the main analyzer components
            expected_components = ["feature_extractor", "complexity_classifier", "model_recommender"]
            for component in expected_components:
                if component in components:
                    comp_info = components[component]
                    assert isinstance(comp_info, dict), f"Component {component} must be object"
                    assert "status" in comp_info, f"Component {component} missing status"
                    assert comp_info["status"] in ["healthy", "unhealthy"], f"Invalid component status: {comp_info['status']}"
            
            print(f"Components endpoint test passed with {len(components)} components")
            
        except Exception as e:
            pytest.fail(f"Components endpoint test failed: {e}")


class TestQueryAnalyzerAPIErrorHandling:
    """Test API error handling and edge cases."""

    @pytest.fixture
    def client(self):
        """Create test client for API testing."""
        if not FASTAPI_AVAILABLE:
            pytest.skip(f"FastAPI not available: {FASTAPI_ERROR}")
        return TestClient(fastapi_app)

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason=f"FastAPI not available: {FASTAPI_ERROR if not FASTAPI_AVAILABLE else ''}")
    def test_nonexistent_endpoints(self, client):
        """Test that nonexistent endpoints return 404."""
        nonexistent_endpoints = [
            "/api/v1/nonexistent",
            "/api/v2/analyze",  # Wrong version
            "/analyze",  # Missing version prefix
            "/api/v1/analyze/extra"  # Extra path
        ]
        
        for endpoint in nonexistent_endpoints:
            try:
                response = client.get(endpoint)
                
                # Should return 404 for nonexistent endpoints
                assert response.status_code == 404, f"Endpoint {endpoint} should return 404, got {response.status_code}"
                
                print(f"404 test passed for: {endpoint}")
                
            except Exception as e:
                pytest.fail(f"404 test failed for {endpoint}: {e}")

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason=f"FastAPI not available: {FASTAPI_ERROR if not FASTAPI_AVAILABLE else ''}")
    def test_wrong_http_methods(self, client):
        """Test wrong HTTP methods return appropriate errors."""
        test_cases = [
            ("GET", "/api/v1/analyze", 405),  # Should be POST
            ("PUT", "/api/v1/analyze", 405),
            ("DELETE", "/api/v1/status", 405),  # Should be GET
            ("POST", "/api/v1/status", 405)
        ]
        
        for method, endpoint, expected_status in test_cases:
            try:
                if method == "GET":
                    response = client.get(endpoint)
                elif method == "POST":
                    response = client.post(endpoint, json={})
                elif method == "PUT":
                    response = client.put(endpoint, json={})
                elif method == "DELETE":
                    response = client.delete(endpoint)
                
                # Should return method not allowed
                assert response.status_code == expected_status, f"{method} {endpoint} should return {expected_status}, got {response.status_code}"
                
                print(f"Method test passed: {method} {endpoint} -> {response.status_code}")
                
            except Exception as e:
                pytest.fail(f"Method test failed for {method} {endpoint}: {e}")

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason=f"FastAPI not available: {FASTAPI_ERROR if not FASTAPI_AVAILABLE else ''}")
    def test_invalid_json(self, client):
        """Test handling of invalid JSON in request body."""
        try:
            # Send invalid JSON
            response = client.post(
                "/api/v1/analyze",
                data="invalid json{",
                headers={"Content-Type": "application/json"}
            )
            
            # Should return 422 (validation error) or 400 (bad request)
            assert response.status_code in [400, 422], f"Invalid JSON should return 400/422, got {response.status_code}"
            
            print(f"Invalid JSON test passed: {response.status_code}")
            
        except Exception as e:
            pytest.fail(f"Invalid JSON test failed: {e}")

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason=f"FastAPI not available: {FASTAPI_ERROR if not FASTAPI_AVAILABLE else ''}")
    def test_content_type_handling(self, client):
        """Test different content types."""
        valid_data = {"query": "test query"}
        
        test_cases = [
            ("application/json", 200, "Valid JSON content type"),
            ("text/plain", 422, "Invalid content type"),
            ("application/xml", 422, "XML content type")
        ]
        
        for content_type, expected_status_range, description in test_cases:
            try:
                if content_type == "application/json":
                    response = client.post("/api/v1/analyze", json=valid_data)
                else:
                    response = client.post(
                        "/api/v1/analyze",
                        data=json.dumps(valid_data),
                        headers={"Content-Type": content_type}
                    )
                
                # Check status code is in expected range
                if expected_status_range == 200:
                    assert response.status_code == 200, f"{description}: expected 200, got {response.status_code}"
                else:
                    assert response.status_code >= 400, f"{description}: expected error status, got {response.status_code}"
                
                print(f"Content type test passed: {description} -> {response.status_code}")
                
            except Exception as e:
                pytest.fail(f"Content type test failed for {description}: {e}")


class TestQueryAnalyzerAPIPerformance:
    """Test API performance characteristics."""

    @pytest.fixture
    def client(self):
        """Create test client for API testing."""
        if not FASTAPI_AVAILABLE:
            pytest.skip(f"FastAPI not available: {FASTAPI_ERROR}")
        return TestClient(fastapi_app)

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason=f"FastAPI not available: {FASTAPI_ERROR if not FASTAPI_AVAILABLE else ''}")
    def test_concurrent_requests(self, client):
        """Test handling of concurrent API requests."""
        import threading
        import queue
        
        request_data = {"query": "What is machine learning?"}
        num_requests = 5  # Conservative for early-stage testing
        
        results = queue.Queue()
        
        def make_request():
            try:
                start_time = time.time()
                response = client.post("/api/v1/analyze", json=request_data)
                end_time = time.time()
                
                results.put({
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code == 200,
                    "error": None
                })
            except Exception as e:
                results.put({
                    "status_code": None,
                    "response_time": None,
                    "success": False,
                    "error": str(e)
                })
        
        try:
            # Start concurrent requests
            threads = []
            start_time = time.time()
            
            for i in range(num_requests):
                thread = threading.Thread(target=make_request)
                thread.start()
                threads.append(thread)
            
            # Wait for all to complete
            for thread in threads:
                thread.join(timeout=30)  # 30s timeout per thread
            
            total_time = time.time() - start_time
            
            # Collect results
            successful_requests = 0
            response_times = []
            
            for i in range(num_requests):
                if not results.empty():
                    result = results.get()
                    if result["success"]:
                        successful_requests += 1
                        response_times.append(result["response_time"])
                    elif result["error"]:
                        print(f"Request error: {result['error']}")
            
            # Hard fail: All requests failed
            assert successful_requests > 0, "All concurrent requests failed"
            
            success_rate = successful_requests / num_requests
            
            # Quality flag: Low success rate
            if success_rate < 0.8:
                pytest.warns(UserWarning, f"Low concurrent success rate: {success_rate:.2%}")
            
            # Quality flag: Very slow concurrent handling
            if response_times and max(response_times) > 10.0:
                pytest.warns(UserWarning, f"Slow concurrent response: {max(response_times):.2f}s")
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            print(f"Concurrent test: {successful_requests}/{num_requests} succeeded")
            print(f"Total time: {total_time:.2f}s, Avg response: {avg_response_time:.2f}s")
            
        except Exception as e:
            pytest.fail(f"Concurrent request test failed: {e}")

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason=f"FastAPI not available: {FASTAPI_ERROR if not FASTAPI_AVAILABLE else ''}")
    def test_response_time_consistency(self, client):
        """Test that response times are reasonably consistent."""
        request_data = {"query": "How does machine learning work?"}
        response_times = []
        
        try:
            # Make multiple requests
            for i in range(5):
                start_time = time.time()
                response = client.post("/api/v1/analyze", json=request_data)
                response_time = time.time() - start_time
                
                assert response.status_code == 200, f"Request {i} failed: {response.status_code}"
                response_times.append(response_time)
            
            # Calculate consistency metrics
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            variance = max_time - min_time
            
            # Quality flags
            if avg_time > 5.0:
                pytest.warns(UserWarning, f"High average response time: {avg_time:.2f}s")
            
            if variance > avg_time:
                pytest.warns(UserWarning, f"High response time variance: {variance:.2f}s")
            
            print(f"Response time consistency: avg={avg_time:.3f}s, range={min_time:.3f}-{max_time:.3f}s")
            
        except Exception as e:
            pytest.fail(f"Response time consistency test failed: {e}")


if __name__ == "__main__":
    # Run specific test classes for development
    pytest.main([__file__ + "::TestQueryAnalyzerAPIBasics", "-v"])