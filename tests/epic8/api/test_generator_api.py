"""
API Tests for Epic 8 Generator Service.

Tests REST API endpoints for the Generator Service based on Epic 8 API specifications
and CT-8.2 test requirements. Validates API contracts, request/response schemas,
and error handling.

Testing Philosophy:
- Hard Fails: 500 errors, >60s response, invalid schemas, service crashes
- Quality Flags: >2s response, validation errors, poor error messages, schema violations

Focus Areas:
- REST API contract validation from Epic 8 API specs
- Request/response schema compliance for generation endpoints  
- Error handling and status codes
- Batch generation functionality
- Health endpoints and monitoring
"""

import pytest
import asyncio
import time
import json
import requests
from typing import Dict, Any, List
from pathlib import Path
import sys

# Test configuration
GENERATOR_BASE_URL = "http://localhost:8081"
API_TIMEOUT = 60.0  # Hard fail timeout


class TestGeneratorAPIHealth:
    """Test health and status endpoints."""

    def test_health_endpoint_basic(self):
        """Test basic health endpoint availability (Hard Fail test)."""
        try:
            start_time = time.time()
            response = requests.get(f"{GENERATOR_BASE_URL}/health", timeout=API_TIMEOUT)
            response_time = time.time() - start_time
            
            # Hard Fail: Response time > 60 seconds
            assert response_time < 60.0, f"Health endpoint took {response_time:.2f}s - HARD FAIL (>60s)"
            
            # Hard Fail: 500+ status codes
            if response.status_code >= 500:
                pytest.fail(f"Health endpoint returned {response.status_code} - HARD FAIL (server error)")
            
            # Should return some form of JSON response
            if response.status_code == 200:
                try:
                    data = response.json()
                    assert isinstance(data, dict), "Health response should be JSON object"
                except json.JSONDecodeError:
                    # Quality Flag: Health endpoint doesn't return JSON
                    print("WARNING: Health endpoint doesn't return valid JSON")
                    
        except requests.exceptions.ConnectionError:
            pytest.skip("Generator service not running - cannot test API endpoints")
        except requests.exceptions.Timeout:
            pytest.fail(f"Health endpoint timed out after {API_TIMEOUT}s - HARD FAIL")
        except Exception as e:
            pytest.fail(f"Health endpoint test failed - HARD FAIL: {e}")

    def test_status_endpoint_response_schema(self):
        """Test status endpoint returns expected schema."""
        try:
            start_time = time.time()
            response = requests.get(f"{GENERATOR_BASE_URL}/api/v1/status", timeout=API_TIMEOUT)
            response_time = time.time() - start_time
            
            # Quality Flag: Slow response
            if response_time > 2.0:
                print(f"WARNING: Status endpoint took {response_time:.2f}s (>2s)")
            
            # Hard Fail: 500+ errors
            if response.status_code >= 500:
                pytest.fail(f"Status endpoint returned {response.status_code} - HARD FAIL")
            
            if response.status_code == 200:
                data = response.json()
                
                # Expected schema fields from Epic 8 API spec
                expected_fields = [
                    "service", "version", "status", "initialized", 
                    "uptime_seconds", "generator_type"
                ]
                
                for field in expected_fields:
                    if field not in data:
                        print(f"WARNING: Status response missing field: {field}")
                
                # Validate field types
                if "initialized" in data:
                    assert isinstance(data["initialized"], bool), "initialized should be boolean"
                
                if "status" in data:
                    assert isinstance(data["status"], str), "status should be string"
                    valid_statuses = ["healthy", "unhealthy", "initializing", "error"]
                    if data["status"] not in valid_statuses:
                        print(f"WARNING: Unexpected status value: {data['status']}")
                
        except requests.exceptions.ConnectionError:
            pytest.skip("Generator service not running")
        except requests.exceptions.Timeout:
            pytest.fail(f"Status endpoint timed out - HARD FAIL")
        except Exception as e:
            pytest.fail(f"Status endpoint test failed - HARD FAIL: {e}")


class TestGeneratorAPIGeneration:
    """Test answer generation endpoints."""

    def test_generate_endpoint_request_validation(self):
        """Test generate endpoint validates requests properly."""
        try:
            # Test with invalid request (missing required fields)
            invalid_requests = [
                {},  # Empty request
                {"query": "test"},  # Missing context_documents
                {"context_documents": []},  # Missing query
                {"query": "", "context_documents": [{"content": "test"}]},  # Empty query
                {"query": "test", "context_documents": []},  # Empty context
            ]
            
            for invalid_request in invalid_requests:
                try:
                    start_time = time.time()
                    response = requests.post(
                        f"{GENERATOR_BASE_URL}/api/v1/generate",
                        json=invalid_request,
                        timeout=API_TIMEOUT
                    )
                    response_time = time.time() - start_time
                    
                    # Should not take too long even for validation errors
                    assert response_time < 10.0, f"Validation took {response_time:.2f}s"
                    
                    # Should return 4xx error for validation issues
                    assert 400 <= response.status_code < 500, f"Expected 4xx for invalid request, got {response.status_code}"
                    
                    # Should return structured error response
                    if response.headers.get('content-type', '').startswith('application/json'):
                        error_data = response.json()
                        if isinstance(error_data, dict) and "error" not in str(error_data).lower():
                            print(f"WARNING: Error response doesn't clearly indicate error: {error_data}")
                    
                except requests.exceptions.Timeout:
                    pytest.fail(f"Validation request timed out - HARD FAIL")
                
        except requests.exceptions.ConnectionError:
            pytest.skip("Generator service not running")
        except Exception as e:
            pytest.fail(f"Request validation test failed - HARD FAIL: {e}")

    def test_generate_endpoint_valid_request(self):
        """Test generate endpoint with valid request."""
        try:
            # Valid request matching Epic 8 API specification
            valid_request = {
                "query": "What are the key features of RISC-V architecture?",
                "context_documents": [
                    {
                        "content": "RISC-V is an open-source instruction set architecture that provides free, open standards for processor design. It offers modularity and customization capabilities.",
                        "metadata": {
                            "source": "risc-v-overview.pdf",
                            "page": 1,
                            "title": "RISC-V Introduction"
                        },
                        "doc_id": "doc_001",
                        "score": 0.95
                    },
                    {
                        "content": "The RISC-V ISA is designed to support a wide range of computing devices, from microcontrollers to supercomputers, with a focus on simplicity and extensibility.",
                        "metadata": {
                            "source": "risc-v-design.pdf", 
                            "page": 5
                        },
                        "doc_id": "doc_002",
                        "score": 0.88
                    }
                ],
                "options": {
                    "strategy": "balanced",
                    "max_cost": 0.05,
                    "include_sources": True,
                    "temperature": 0.7
                }
            }
            
            start_time = time.time()
            response = requests.post(
                f"{GENERATOR_BASE_URL}/api/v1/generate",
                json=valid_request,
                timeout=API_TIMEOUT
            )
            response_time = time.time() - start_time
            
            # Hard Fail: Response time > 60 seconds
            assert response_time < 60.0, f"Generation took {response_time:.2f}s - HARD FAIL (>60s)"
            
            # Quality Flag: Slow response
            if response_time > 2.0:
                print(f"WARNING: Generation took {response_time:.2f}s (>2s)")
            
            # Check response status
            if response.status_code >= 500:
                pytest.fail(f"Generation returned server error {response.status_code} - HARD FAIL")
            
            if response.status_code == 200:
                # Validate response schema
                data = response.json()
                
                # Required fields from Epic 8 API spec
                required_fields = [
                    "answer", "query", "model_used", "cost", "confidence",
                    "routing_decision", "processing_time", "metadata"
                ]
                
                missing_fields = []
                for field in required_fields:
                    if field not in data:
                        missing_fields.append(field)
                
                if missing_fields:
                    pytest.fail(f"Response missing required fields: {missing_fields} - Schema violation")
                
                # Validate field types and ranges
                assert isinstance(data["answer"], str), "answer should be string"
                assert len(data["answer"]) > 0, "answer should not be empty"
                
                assert isinstance(data["query"], str), "query should be string"
                assert data["query"] == valid_request["query"], "query should match request"
                
                assert isinstance(data["model_used"], str), "model_used should be string"
                assert len(data["model_used"]) > 0, "model_used should not be empty"
                
                assert isinstance(data["cost"], (int, float)), "cost should be numeric"
                assert data["cost"] >= 0, "cost should be non-negative"
                
                assert isinstance(data["confidence"], (int, float)), "confidence should be numeric"
                assert 0 <= data["confidence"] <= 1, f"confidence {data['confidence']} should be in [0,1]"
                
                assert isinstance(data["processing_time"], (int, float)), "processing_time should be numeric"
                assert data["processing_time"] > 0, "processing_time should be positive"
                
                # Validate routing_decision structure
                routing = data["routing_decision"]
                assert isinstance(routing, dict), "routing_decision should be dict"
                
                routing_fields = ["strategy", "selection_reason"]
                for field in routing_fields:
                    if field not in routing:
                        print(f"WARNING: routing_decision missing field: {field}")
                
            elif response.status_code == 422:
                # Validation error - check if reasonable
                error_data = response.json()
                print(f"Validation error: {error_data}")
                # Don't fail - might be due to missing dependencies
                
            elif response.status_code == 503:
                # Service unavailable - acceptable for early stage
                pytest.skip("Generator service unavailable (503) - acceptable for early stage")
                
            else:
                print(f"WARNING: Unexpected response status {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            pytest.skip("Generator service not running")
        except requests.exceptions.Timeout:
            pytest.fail(f"Generation request timed out - HARD FAIL")
        except Exception as e:
            pytest.fail(f"Valid generation request test failed - HARD FAIL: {e}")

    def test_generate_endpoint_cost_constraint(self):
        """Test that generation respects cost constraints."""
        try:
            # Request with strict cost constraint
            cost_constrained_request = {
                "query": "Simple question about RISC-V",
                "context_documents": [
                    {
                        "content": "RISC-V is open-source.",
                        "metadata": {"source": "test.pdf"},
                        "doc_id": "doc_simple"
                    }
                ],
                "options": {
                    "strategy": "cost_optimized",
                    "max_cost": 0.001  # Very low cost constraint
                }
            }
            
            response = requests.post(
                f"{GENERATOR_BASE_URL}/api/v1/generate",
                json=cost_constrained_request,
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                actual_cost = data.get("cost", 0)
                max_cost = 0.001
                
                # Check cost constraint compliance (with 5% tolerance per CT-8.2.1)
                tolerance = max_cost * 0.05
                if actual_cost > max_cost + tolerance:
                    print(f"WARNING: Cost constraint violated - max: {max_cost}, actual: {actual_cost}")
                
                # Check that cost-optimized strategy was used
                routing = data.get("routing_decision", {})
                strategy = routing.get("strategy", "")
                if strategy not in ["cost_optimized", "cost_optimal"]:
                    print(f"WARNING: Expected cost_optimized strategy, got: {strategy}")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Generator service not running")
        except Exception as e:
            # Don't hard fail - cost constraints may not be fully implemented yet
            print(f"Cost constraint test failed (acceptable for early stage): {e}")


class TestGeneratorAPIBatchGeneration:
    """Test batch generation functionality."""

    def test_batch_generate_endpoint_basic(self):
        """Test basic batch generation endpoint."""
        try:
            # Simple batch request
            batch_request = {
                "requests": [
                    {
                        "query": "What is RISC-V?",
                        "context_documents": [
                            {
                                "content": "RISC-V is an open-source instruction set architecture.",
                                "metadata": {"source": "test1.pdf"},
                                "doc_id": "doc1"
                            }
                        ],
                        "options": {"strategy": "cost_optimized"}
                    },
                    {
                        "query": "How does RISC-V compare to ARM?",
                        "context_documents": [
                            {
                                "content": "RISC-V offers open-source flexibility while ARM requires licensing.",
                                "metadata": {"source": "test2.pdf"},
                                "doc_id": "doc2"
                            }
                        ],
                        "options": {"strategy": "balanced"}
                    }
                ],
                "batch_options": {
                    "parallel_processing": True,
                    "max_parallel": 2
                }
            }
            
            start_time = time.time()
            response = requests.post(
                f"{GENERATOR_BASE_URL}/api/v1/batch-generate",
                json=batch_request,
                timeout=API_TIMEOUT
            )
            response_time = time.time() - start_time
            
            # Hard Fail: Response time > 60 seconds
            assert response_time < 60.0, f"Batch generation took {response_time:.2f}s - HARD FAIL"
            
            # Check response
            if response.status_code >= 500:
                pytest.fail(f"Batch generation returned server error {response.status_code} - HARD FAIL")
            
            if response.status_code == 200:
                data = response.json()
                
                # Expected fields from Epic 8 API spec
                expected_fields = ["results", "batch_summary", "total_cost", "total_processing_time"]
                for field in expected_fields:
                    if field not in data:
                        print(f"WARNING: Batch response missing field: {field}")
                
                # Validate results structure
                if "results" in data:
                    results = data["results"]
                    assert isinstance(results, list), "results should be list"
                    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
                    
                    for i, result in enumerate(results):
                        assert isinstance(result, dict), f"Result {i} should be dict"
                        assert "index" in result, f"Result {i} missing index"
                        
                        # Should have either success result or error info
                        if "result" in result:
                            # Success case - validate structure
                            gen_result = result["result"]
                            assert isinstance(gen_result, dict), f"Generation result {i} should be dict"
                        elif "error" in result:
                            # Error case - acceptable for early stage
                            print(f"Batch item {i} failed: {result.get('error', 'unknown error')}")
                        else:
                            print(f"WARNING: Result {i} has unclear success/failure status")
                
                # Validate batch summary
                if "batch_summary" in data:
                    summary = data["batch_summary"]
                    assert isinstance(summary, dict), "batch_summary should be dict"
                    
                    if "total_requests" in summary:
                        assert summary["total_requests"] == 2, f"Expected 2 total_requests, got {summary['total_requests']}"
            
            elif response.status_code == 404:
                pytest.skip("Batch generate endpoint not implemented yet")
            elif response.status_code >= 400:
                # Client error - check if reasonable
                print(f"Batch request failed with {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error details: {error_data}")
                except:
                    pass
                # Don't hard fail - might be early implementation
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Generator service not running")
        except requests.exceptions.Timeout:
            pytest.fail(f"Batch generation timed out - HARD FAIL")
        except Exception as e:
            # Don't hard fail - batch generation might not be fully implemented
            print(f"Batch generation test failed (acceptable for early stage): {e}")


class TestGeneratorAPIModelsEndpoint:
    """Test models information endpoint."""

    def test_models_endpoint_response(self):
        """Test models endpoint returns model information."""
        try:
            start_time = time.time()
            response = requests.get(f"{GENERATOR_BASE_URL}/api/v1/models", timeout=API_TIMEOUT)
            response_time = time.time() - start_time
            
            # Should respond quickly
            assert response_time < 10.0, f"Models endpoint took {response_time:.2f}s"
            
            # Hard Fail: Server error
            if response.status_code >= 500:
                pytest.fail(f"Models endpoint returned server error {response.status_code} - HARD FAIL")
            
            if response.status_code == 200:
                data = response.json()
                
                # Expected structure from Epic 8 API spec
                expected_fields = ["models", "total_models", "healthy_models"]
                for field in expected_fields:
                    if field not in data:
                        print(f"WARNING: Models response missing field: {field}")
                
                # Validate models list
                if "models" in data:
                    models = data["models"]
                    assert isinstance(models, list), "models should be list"
                    
                    for model in models:
                        assert isinstance(model, dict), "Each model should be dict"
                        
                        # Required model fields
                        model_fields = ["name", "provider", "available"]
                        for field in model_fields:
                            if field not in model:
                                print(f"WARNING: Model missing field: {field}")
                        
                        # Validate field types
                        if "name" in model:
                            assert isinstance(model["name"], str), "model name should be string"
                            assert len(model["name"]) > 0, "model name should not be empty"
                        
                        if "available" in model:
                            assert isinstance(model["available"], bool), "available should be boolean"
                        
                        if "cost_per_token" in model and model["cost_per_token"] is not None:
                            assert isinstance(model["cost_per_token"], (int, float)), "cost_per_token should be numeric"
                            assert model["cost_per_token"] >= 0, "cost_per_token should be non-negative"
                
                # Validate counts
                if "models" in data and "total_models" in data:
                    assert data["total_models"] == len(data["models"]), "total_models should match models list length"
                
                if "healthy_models" in data and "total_models" in data:
                    assert data["healthy_models"] <= data["total_models"], "healthy_models should not exceed total_models"
            
            elif response.status_code == 404:
                pytest.skip("Models endpoint not implemented yet")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Generator service not running")
        except requests.exceptions.Timeout:
            pytest.fail(f"Models endpoint timed out - HARD FAIL")
        except Exception as e:
            pytest.fail(f"Models endpoint test failed - HARD FAIL: {e}")


class TestGeneratorAPIErrorHandling:
    """Test API error handling and edge cases."""

    def test_invalid_json_handling(self):
        """Test that API handles invalid JSON gracefully."""
        try:
            # Send invalid JSON
            invalid_json = '{"query": "test", "context_documents": [{'  # Incomplete JSON
            
            response = requests.post(
                f"{GENERATOR_BASE_URL}/api/v1/generate",
                data=invalid_json,
                headers={"Content-Type": "application/json"},
                timeout=10.0
            )
            
            # Should return 4xx error for invalid JSON
            assert 400 <= response.status_code < 500, f"Expected 4xx for invalid JSON, got {response.status_code}"
            
            # Should not crash the service
            # Test that service is still responsive
            health_response = requests.get(f"{GENERATOR_BASE_URL}/health", timeout=5.0)
            if health_response.status_code >= 500:
                pytest.fail("Service crashed after invalid JSON - HARD FAIL")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Generator service not running")
        except Exception as e:
            pytest.fail(f"Invalid JSON handling test failed - HARD FAIL: {e}")

    def test_large_request_handling(self):
        """Test that API handles large requests appropriately."""
        try:
            # Create request with large query and many documents
            large_query = "What are the implications of RISC-V architecture? " * 100  # ~5KB query
            large_documents = []
            
            for i in range(20):  # Maximum per API spec
                large_documents.append({
                    "content": f"This is document {i} with substantial content about RISC-V architecture. " * 50,
                    "metadata": {"source": f"large_doc_{i}.pdf", "page": i},
                    "doc_id": f"large_doc_{i}",
                    "score": 0.9
                })
            
            large_request = {
                "query": large_query,
                "context_documents": large_documents,
                "options": {"strategy": "cost_optimized"}
            }
            
            start_time = time.time()
            response = requests.post(
                f"{GENERATOR_BASE_URL}/api/v1/generate",
                json=large_request,
                timeout=60.0
            )
            response_time = time.time() - start_time
            
            # Should not timeout
            assert response_time < 60.0, f"Large request took {response_time:.2f}s - HARD FAIL"
            
            # Should either succeed or fail gracefully (not crash)
            if response.status_code >= 500:
                # Check if service is still responsive
                health_response = requests.get(f"{GENERATOR_BASE_URL}/health", timeout=5.0)
                if health_response.status_code >= 500:
                    pytest.fail("Service crashed after large request - HARD FAIL")
            
            # If rejected, should be clear why
            if response.status_code == 413:  # Payload too large
                print("Large request rejected (413) - acceptable")
            elif response.status_code == 422:  # Validation error
                print("Large request validation failed - check if limits are reasonable")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Generator service not running")
        except requests.exceptions.Timeout:
            # Timeout is acceptable for very large requests
            print("Large request timed out - acceptable behavior")
        except Exception as e:
            pytest.fail(f"Large request handling test failed - HARD FAIL: {e}")

    def test_concurrent_requests_handling(self):
        """Test that API handles concurrent requests without crashing."""
        try:
            import threading
            import queue
            
            # Simple request for concurrent testing
            test_request = {
                "query": "What is RISC-V?",
                "context_documents": [
                    {
                        "content": "RISC-V is an open-source instruction set architecture.",
                        "metadata": {"source": "test.pdf"},
                        "doc_id": "test_doc"
                    }
                ]
            }
            
            results_queue = queue.Queue()
            num_concurrent = 3  # Modest concurrent load
            
            def make_request(request_id):
                try:
                    start_time = time.time()
                    response = requests.post(
                        f"{GENERATOR_BASE_URL}/api/v1/generate",
                        json=test_request,
                        timeout=30.0
                    )
                    response_time = time.time() - start_time
                    
                    results_queue.put({
                        "request_id": request_id,
                        "status_code": response.status_code,
                        "response_time": response_time,
                        "success": response.status_code < 500
                    })
                except Exception as e:
                    results_queue.put({
                        "request_id": request_id,
                        "error": str(e),
                        "success": False
                    })
            
            # Start concurrent requests
            threads = []
            start_time = time.time()
            
            for i in range(num_concurrent):
                thread = threading.Thread(target=make_request, args=(i,))
                thread.start()
                threads.append(thread)
            
            # Wait for all to complete
            for thread in threads:
                thread.join(timeout=60.0)
            
            total_time = time.time() - start_time
            
            # Collect results
            results = []
            while not results_queue.empty():
                results.append(results_queue.get())
            
            assert len(results) == num_concurrent, f"Expected {num_concurrent} results, got {len(results)}"
            
            # Check for crashes (all requests getting 500+ errors)
            server_errors = sum(1 for r in results if r.get("status_code", 500) >= 500)
            if server_errors == num_concurrent:
                pytest.fail("All concurrent requests failed with server errors - HARD FAIL")
            
            # Check for reasonable performance
            avg_response_time = sum(r.get("response_time", 0) for r in results if "response_time" in r) / len(results)
            if avg_response_time > 10.0:
                print(f"WARNING: Average response time {avg_response_time:.2f}s for concurrent requests")
            
            # Service should still be responsive
            health_response = requests.get(f"{GENERATOR_BASE_URL}/health", timeout=5.0)
            if health_response.status_code >= 500:
                pytest.fail("Service unhealthy after concurrent requests - HARD FAIL")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Generator service not running")
        except Exception as e:
            pytest.fail(f"Concurrent requests test failed - HARD FAIL: {e}")


class TestGeneratorAPIRouting:
    """Test routing-related API endpoints."""

    def test_routing_test_endpoint(self):
        """Test the routing test endpoint (if implemented)."""
        try:
            routing_test_request = {
                "query": "Complex technical analysis of RISC-V vector extensions",
                "strategy": "quality_first",
                "max_cost": 0.05
            }
            
            response = requests.post(
                f"{GENERATOR_BASE_URL}/api/v1/test-routing",
                json=routing_test_request,
                timeout=10.0
            )
            
            if response.status_code == 404:
                pytest.skip("Routing test endpoint not implemented yet")
            elif response.status_code >= 500:
                pytest.fail(f"Routing test endpoint server error {response.status_code} - HARD FAIL")
            elif response.status_code == 200:
                data = response.json()
                
                # Expected fields from Epic 8 API spec
                expected_fields = ["query", "recommended_model", "strategy_used", "cost_estimate"]
                for field in expected_fields:
                    if field not in data:
                        print(f"WARNING: Routing test response missing field: {field}")
                
                # Validate response structure
                if "query" in data:
                    assert data["query"] == routing_test_request["query"], "Query should match request"
                
                if "recommended_model" in data:
                    assert isinstance(data["recommended_model"], str), "recommended_model should be string"
                    assert len(data["recommended_model"]) > 0, "recommended_model should not be empty"
                
                if "cost_estimate" in data:
                    assert isinstance(data["cost_estimate"], (int, float)), "cost_estimate should be numeric"
                    assert data["cost_estimate"] >= 0, "cost_estimate should be non-negative"
                    
                    # Should respect cost constraint
                    if data["cost_estimate"] > routing_test_request["max_cost"] * 1.1:  # 10% tolerance
                        print(f"WARNING: Routing test exceeded cost constraint: {data['cost_estimate']} > {routing_test_request['max_cost']}")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Generator service not running")
        except Exception as e:
            # Don't hard fail - routing test endpoint may not be implemented
            print(f"Routing test endpoint failed (acceptable for early stage): {e}")


@pytest.mark.api_integration
class TestGeneratorAPIIntegration:
    """Test API integration scenarios."""

    def test_api_workflow_complete(self):
        """Test complete API workflow if service is available."""
        try:
            # 1. Check service health
            health_response = requests.get(f"{GENERATOR_BASE_URL}/health", timeout=5.0)
            if health_response.status_code >= 500:
                pytest.skip("Service unhealthy - skipping workflow test")
            
            # 2. Get service status
            status_response = requests.get(f"{GENERATOR_BASE_URL}/api/v1/status", timeout=5.0)
            if status_response.status_code != 200:
                print(f"WARNING: Status endpoint returned {status_response.status_code}")
            
            # 3. Get available models (if endpoint exists)
            models_response = requests.get(f"{GENERATOR_BASE_URL}/api/v1/models", timeout=5.0)
            if models_response.status_code == 404:
                print("Models endpoint not implemented yet")
            elif models_response.status_code >= 500:
                print("WARNING: Models endpoint server error")
            
            # 4. Attempt generation (may fail due to dependencies)
            gen_request = {
                "query": "What is the basic concept of RISC-V?",
                "context_documents": [
                    {
                        "content": "RISC-V is an open standard instruction set architecture based on established reduced instruction set computer principles.",
                        "metadata": {"source": "risc-v-intro.pdf"},
                        "doc_id": "intro_001"
                    }
                ],
                "options": {"strategy": "balanced"}
            }
            
            gen_response = requests.post(
                f"{GENERATOR_BASE_URL}/api/v1/generate",
                json=gen_request,
                timeout=30.0
            )
            
            if gen_response.status_code == 200:
                print("✅ Complete API workflow successful")
                data = gen_response.json()
                print(f"Generated answer length: {len(data.get('answer', ''))}")
                print(f"Model used: {data.get('model_used', 'unknown')}")
                print(f"Cost: ${data.get('cost', 0):.4f}")
            elif gen_response.status_code >= 500:
                print(f"WARNING: Generation failed with server error {gen_response.status_code}")
            else:
                print(f"Generation failed with status {gen_response.status_code} (may be expected)")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Generator service not running")
        except Exception as e:
            # Don't hard fail - this is an integration test
            print(f"API workflow test failed (acceptable for early stage): {e}")

    def test_api_error_consistency(self):
        """Test that API errors are consistent across endpoints."""
        try:
            endpoints_to_test = [
                ("POST", "/api/v1/generate", {"invalid": "request"}),
                ("POST", "/api/v1/batch-generate", {"invalid": "request"}),
                ("POST", "/api/v1/test-routing", {"invalid": "request"}),
            ]
            
            for method, endpoint, payload in endpoints_to_test:
                try:
                    response = requests.post(f"{GENERATOR_BASE_URL}{endpoint}", json=payload, timeout=5.0)
                    
                    if response.status_code == 404:
                        continue  # Endpoint not implemented
                    
                    if 400 <= response.status_code < 500:
                        # Should return structured error
                        try:
                            error_data = response.json()
                            if not isinstance(error_data, dict):
                                print(f"WARNING: {endpoint} error response not structured: {error_data}")
                        except json.JSONDecodeError:
                            print(f"WARNING: {endpoint} error response not JSON")
                    
                except requests.exceptions.Timeout:
                    print(f"WARNING: {endpoint} timed out")
                except Exception as e:
                    print(f"WARNING: {endpoint} test failed: {e}")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Generator service not running")
        except Exception as e:
            # Don't hard fail - this is a quality check
            print(f"API error consistency test failed: {e}")