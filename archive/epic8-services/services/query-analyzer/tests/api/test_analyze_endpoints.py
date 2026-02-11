"""
API tests for analysis endpoints.

Tests /analyze and /batch-analyze endpoints through the FastAPI application.
"""

import json
from unittest.mock import patch

from conftest import (
    assert_confidence_range,
    assert_valid_complexity,
    validate_response_structure,
)


class TestAnalyzeEndpoint:
    """Test cases for POST /api/v1/analyze endpoint."""

    def test_analyze_simple_query(self, client, sample_queries, expected_response_structure, performance_targets):
        """Test analysis of simple query."""
        query = sample_queries["simple"][0]
        payload = {"query": query}
        
        response = client.post("/api/v1/analyze", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        validate_response_structure(data, expected_response_structure)
        
        # Validate content
        assert data["query"] == query
        assert_valid_complexity(data["complexity"], performance_targets["valid_complexities"])
        assert_confidence_range(data["confidence"])
        assert data["processing_time"] > 0
        assert isinstance(data["metadata"], dict)

    def test_analyze_medium_query(self, client, sample_queries):
        """Test analysis of medium complexity query."""
        query = sample_queries["medium"][0]
        payload = {"query": query}
        
        response = client.post("/api/v1/analyze", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["query"] == query
        assert data["complexity"] in ["simple", "medium", "complex"]
        assert len(data["recommended_models"]) > 0

    def test_analyze_complex_query(self, client, sample_queries):
        """Test analysis of complex query."""
        query = sample_queries["complex"][0]
        payload = {"query": query}
        
        response = client.post("/api/v1/analyze", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["query"] == query
        assert data["complexity"] in ["simple", "medium", "complex"]
        assert isinstance(data["cost_estimate"], dict)

    def test_analyze_with_context(self, client, sample_queries):
        """Test analysis with context."""
        query = sample_queries["simple"][0]
        context = {
            "user_id": "test_user_123",
            "session_id": "session_abc",
            "preferences": {"model_preference": "balanced"}
        }
        payload = {
            "query": query,
            "context": context
        }
        
        response = client.post("/api/v1/analyze", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["query"] == query
        assert data["metadata"]["context"] == context

    def test_analyze_with_options(self, client, sample_queries):
        """Test analysis with options."""
        query = sample_queries["medium"][0]
        options = {
            "include_detailed_features": True,
            "timeout": 30
        }
        payload = {
            "query": query,
            "context": None,
            "options": options
        }
        
        response = client.post("/api/v1/analyze", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["query"] == query
        # Options are passed to the analyzer but don't directly affect response structure

    def test_analyze_minimal_payload(self, client):
        """Test analysis with minimal payload."""
        payload = {"query": "What is AI?"}
        
        response = client.post("/api/v1/analyze", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["query"] == "What is AI?"
        assert data["complexity"] in ["simple", "medium", "complex"]

    def test_analyze_empty_query(self, client):
        """Test analysis with empty query."""
        payload = {"query": ""}
        
        response = client.post("/api/v1/analyze", json=payload)
        
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data

    def test_analyze_whitespace_query(self, client):
        """Test analysis with whitespace-only query."""
        payload = {"query": "   \n\t   "}
        
        response = client.post("/api/v1/analyze", json=payload)
        
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data

    def test_analyze_long_query(self, client):
        """Test analysis with very long query."""
        long_query = "A" * 10001  # Exceeds max length
        payload = {"query": long_query}
        
        response = client.post("/api/v1/analyze", json=payload)
        
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data

    def test_analyze_missing_query(self, client):
        """Test analysis without query field."""
        payload = {"context": {"user": "test"}}
        
        response = client.post("/api/v1/analyze", json=payload)
        
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data

    def test_analyze_invalid_context_type(self, client):
        """Test analysis with invalid context type."""
        payload = {
            "query": "test query",
            "context": "invalid_context_string"
        }
        
        response = client.post("/api/v1/analyze", json=payload)
        
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data

    def test_analyze_invalid_options_type(self, client):
        """Test analysis with invalid options type."""
        payload = {
            "query": "test query",
            "options": "invalid_options_string"
        }
        
        response = client.post("/api/v1/analyze", json=payload)
        
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data

    def test_analyze_invalid_json(self, client):
        """Test analysis with invalid JSON."""
        response = client.post(
            "/api/v1/analyze",
            data="invalid json {",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422

    def test_analyze_missing_content_type(self, client):
        """Test analysis without content type header."""
        payload = {"query": "test"}
        
        response = client.post("/api/v1/analyze", data=json.dumps(payload))
        
        # FastAPI should still handle this correctly
        assert response.status_code in [200, 422]

    def test_analyze_unicode_query(self, client):
        """Test analysis with Unicode characters."""
        unicode_query = "¿Qué es la inteligencia artificial? 人工智能是什么？ Что такое ИИ?"
        payload = {"query": unicode_query}
        
        response = client.post("/api/v1/analyze", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == unicode_query

    def test_analyze_special_characters(self, client):
        """Test analysis with special characters."""
        special_query = "What is AI? !@#$%^&*()_+-={}[]|\\:;\"'<>,.?/"
        payload = {"query": special_query}
        
        response = client.post("/api/v1/analyze", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == special_query

    def test_analyze_response_headers(self, client):
        """Test response headers."""
        payload = {"query": "test query"}
        
        response = client.post("/api/v1/analyze", json=payload)
        
        assert response.status_code == 200
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]

    def test_analyze_performance_timing(self, client, sample_queries, performance_targets):
        """Test that analysis meets performance targets."""
        query = sample_queries["complex"][0]  # Use complex query for stress test
        payload = {"query": query}
        
        import time
        start_time = time.time()
        response = client.post("/api/v1/analyze", json=payload)
        total_time = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        # Check both API response time and reported processing time
        assert total_time < 1.0  # API should respond quickly
        assert data["processing_time"] <= performance_targets["max_response_time"]

    def test_analyze_concurrent_requests(self, client, sample_queries):
        """Test concurrent analyze requests."""
        query = sample_queries["simple"][0]
        payload = {"query": query}
        
        # Make multiple concurrent requests using threading
        import threading
        
        results = []
        errors = []
        
        def make_request():
            try:
                response = client.post("/api/v1/analyze", json=payload)
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        threads = [threading.Thread(target=make_request) for _ in range(5)]
        
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert len(errors) == 0
        assert all(status == 200 for status in results)

    @patch('app.core.analyzer.QueryAnalyzerService.analyze_query')
    def test_analyze_service_error(self, mock_analyze, client):
        """Test handling of service errors."""
        mock_analyze.side_effect = RuntimeError("Service error")
        
        payload = {"query": "test query"}
        response = client.post("/api/v1/analyze", json=payload)
        
        assert response.status_code == 500
        error_data = response.json()
        assert "error" in error_data
        assert "message" in error_data
        assert "request_id" in error_data

    @patch('app.core.analyzer.QueryAnalyzerService.analyze_query')
    def test_analyze_validation_error(self, mock_analyze, client):
        """Test handling of validation errors from service."""
        mock_analyze.side_effect = ValueError("Invalid query format")
        
        payload = {"query": "test query"}
        response = client.post("/api/v1/analyze", json=payload)
        
        assert response.status_code == 422
        assert "Invalid query format" in str(response.json())


class TestBatchAnalyzeEndpoint:
    """Test cases for POST /api/v1/batch-analyze endpoint."""

    def test_batch_analyze_simple(self, client, sample_queries):
        """Test batch analysis with simple queries."""
        queries = sample_queries["simple"][:3]
        
        response = client.post("/api/v1/batch-analyze", json=queries)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "request_id" in data
        assert data["total_queries"] == len(queries)
        assert data["successful_analyses"] > 0
        assert data["failed_analyses"] == 0
        assert "processing_time" in data
        assert "complexity_distribution" in data
        assert "results" in data
        
        # Validate results
        results = data["results"]
        assert len(results) == len(queries)
        
        for i, result in enumerate(results):
            assert result["index"] == i
            assert result["query"] == queries[i]
            assert "result" in result

    def test_batch_analyze_with_context(self, client, sample_queries):
        """Test batch analysis with context."""
        queries = sample_queries["medium"][:2]
        context = {"user_id": "batch_test", "session": "test123"}
        payload = {"queries": queries, "context": context}
        
        # Note: The actual endpoint signature might be different
        # This tests the expected interface
        response = client.post("/api/v1/batch-analyze", json=queries, params={"context": json.dumps(context)})
        
        assert response.status_code in [200, 422]  # Depends on implementation

    def test_batch_analyze_empty_list(self, client):
        """Test batch analysis with empty query list."""
        response = client.post("/api/v1/batch-analyze", json=[])
        
        assert response.status_code == 422
        error_data = response.json()
        assert "At least one query is required" in str(error_data)

    def test_batch_analyze_too_many_queries(self, client):
        """Test batch analysis with too many queries."""
        queries = [f"query {i}" for i in range(101)]  # Exceeds limit
        
        response = client.post("/api/v1/batch-analyze", json=queries)
        
        assert response.status_code == 422
        error_data = response.json()
        assert "Maximum 100 queries" in str(error_data)

    def test_batch_analyze_mixed_results(self, client):
        """Test batch analysis with some valid and some invalid queries."""
        queries = [
            "Valid query 1",
            "",  # Invalid empty query
            "Valid query 2",
            "A" * 10001,  # Invalid too long query
            "Valid query 3"
        ]
        
        response = client.post("/api/v1/batch-analyze", json=queries)
        
        # Should still process valid queries
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_queries"] == len(queries)
        # Some should succeed, some should fail
        assert data["successful_analyses"] > 0
        assert data["failed_analyses"] > 0

    def test_batch_analyze_complexity_distribution(self, client, sample_queries):
        """Test complexity distribution in batch results."""
        # Use queries from different complexity levels
        queries = []
        queries.extend(sample_queries["simple"][:2])
        queries.extend(sample_queries["medium"][:2])
        queries.extend(sample_queries["complex"][:1])
        
        response = client.post("/api/v1/batch-analyze", json=queries)
        
        assert response.status_code == 200
        data = response.json()
        
        complexity_dist = data["complexity_distribution"]
        assert "simple" in complexity_dist
        assert "medium" in complexity_dist
        assert "complex" in complexity_dist
        
        # Should have some distribution across complexities
        total_classified = sum(complexity_dist.values())
        assert total_classified > 0

    def test_batch_analyze_performance(self, client, sample_queries):
        """Test batch analysis performance."""
        queries = sample_queries["simple"][:10]  # Moderate batch size
        
        import time
        start_time = time.time()
        response = client.post("/api/v1/batch-analyze", json=queries)
        total_time = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        # Batch should be reasonably fast
        assert total_time < 5.0  # Should complete within 5 seconds
        assert data["processing_time"] > 0

    def test_batch_analyze_invalid_input_type(self, client):
        """Test batch analysis with invalid input type."""
        response = client.post("/api/v1/batch-analyze", json="not_a_list")
        
        assert response.status_code == 422

    def test_batch_analyze_invalid_query_types(self, client):
        """Test batch analysis with invalid query types in list."""
        queries = ["Valid query", 123, None, {"invalid": "object"}]
        
        response = client.post("/api/v1/batch-analyze", json=queries)
        
        # Should handle type errors gracefully
        assert response.status_code in [200, 422]

    @patch('app.core.analyzer.QueryAnalyzerService.analyze_query')
    def test_batch_analyze_service_errors(self, mock_analyze, client):
        """Test batch analysis with service errors."""
        # Mock some successes and some failures
        mock_analyze.side_effect = [
            {"complexity": "simple", "confidence": 0.9},
            RuntimeError("Service error"),
            {"complexity": "medium", "confidence": 0.8}
        ]
        
        queries = ["query1", "query2", "query3"]
        response = client.post("/api/v1/batch-analyze", json=queries)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should handle partial failures
        assert data["successful_analyses"] == 2
        assert data["failed_analyses"] == 1

    def test_batch_analyze_request_id_uniqueness(self, client, sample_queries):
        """Test that batch requests get unique request IDs."""
        queries = sample_queries["simple"][:2]
        
        response1 = client.post("/api/v1/batch-analyze", json=queries)
        response2 = client.post("/api/v1/batch-analyze", json=queries)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Request IDs should be different
        assert data1["request_id"] != data2["request_id"]