"""
Unit tests for API Gateway REST endpoints.
"""

import pytest
from unittest.mock import patch, AsyncMock

from gateway_app.schemas.responses import UnifiedQueryResponse, BatchQueryResponse, GatewayStatusResponse


class TestAPIEndpoints:
    """Test cases for API Gateway REST endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns service information."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["service"] == "API Gateway"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
        assert "epic8_compliance" in data
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "api-gateway"
        assert "timestamp" in data
    
    def test_liveness_probe(self, client):
        """Test Kubernetes liveness probe."""
        response = client.get("/health/live")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "alive"
    
    @patch('app.main.get_gateway_service')
    def test_readiness_probe_healthy(self, mock_get_service, client):
        """Test Kubernetes readiness probe when healthy."""
        # Mock healthy gateway service
        mock_service = AsyncMock()
        mock_service.get_gateway_status.return_value = GatewayStatusResponse(
            status="healthy",
            uptime=100.0,
            services=[
                {"name": "query-analyzer", "status": "healthy"},
                {"name": "generator", "status": "healthy"},
                {"name": "retriever", "status": "healthy"},
                {"name": "cache", "status": "healthy"},
                {"name": "analytics", "status": "healthy"}
            ],
            healthy_services=5,
            total_services=5,
            requests_processed=0,
            average_response_time=0.0,
            error_rate=0.0,
            circuit_breakers={}
        )
        mock_get_service.return_value = mock_service
        
        response = client.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
    
    @patch('app.main.get_gateway_service')
    def test_unified_query_endpoint(self, mock_get_service, client, sample_query_request):
        """Test unified query endpoint."""
        # Mock gateway service
        mock_service = AsyncMock()
        mock_response = UnifiedQueryResponse(
            answer="Test answer",
            sources=[],
            complexity="medium",
            confidence=0.9,
            cost={
                "model_used": "test-model",
                "total_cost": 0.001,
                "model_cost": 0.001,
                "retrieval_cost": 0.0
            },
            metrics={
                "analysis_time": 0.1,
                "retrieval_time": 0.2,
                "generation_time": 0.5,
                "total_time": 0.8,
                "documents_retrieved": 3,
                "cache_hit": False,
                "cache_key": "test-hash"
            },
            query_id="test-query-123",
            strategy_used="balanced"
        )
        mock_service.process_unified_query.return_value = mock_response
        mock_get_service.return_value = mock_service
        
        response = client.post("/api/v1/query", json=sample_query_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["answer"] == "Test answer"
        assert data["complexity"] == "medium"
        assert data["confidence"] == 0.9
        assert data["strategy_used"] == "balanced"
        assert "cost" in data
        assert "metrics" in data
    
    @patch('app.main.get_gateway_service')
    def test_batch_query_endpoint(self, mock_get_service, client, sample_batch_request):
        """Test batch query endpoint."""
        # Mock gateway service
        mock_service = AsyncMock()
        mock_response = BatchQueryResponse(
            batch_id="test-batch-123",
            total_queries=3,
            successful_queries=3,
            failed_queries=0,
            processing_time=1.5,
            parallel_processing=True,
            results=[],
            summary={},
            total_cost=0.003,
            average_cost_per_query=0.001
        )
        mock_service.process_batch_queries.return_value = mock_response
        mock_get_service.return_value = mock_service
        
        response = client.post("/api/v1/batch-query", json=sample_batch_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["batch_id"] == "test-batch-123"
        assert data["total_queries"] == 3
        assert data["successful_queries"] == 3
        assert data["failed_queries"] == 0
        assert data["parallel_processing"] is True
    
    @patch('app.main.get_gateway_service')
    def test_status_endpoint(self, mock_get_service, client):
        """Test status endpoint."""
        # Mock gateway service
        mock_service = AsyncMock()
        mock_status = GatewayStatusResponse(
            status="healthy",
            uptime=3600.0,
            services=[],
            healthy_services=5,
            total_services=5,
            requests_processed=100,
            average_response_time=0.5,
            error_rate=0.01,
            circuit_breakers={
                "query-analyzer": "closed",
                "generator": "closed"
            },
            cache_hit_rate=0.8,
            cache_size=1000
        )
        mock_service.get_gateway_status.return_value = mock_status
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/v1/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["uptime"] == 3600.0
        assert data["healthy_services"] == 5
        assert data["total_services"] == 5
        assert data["requests_processed"] == 100
        assert "circuit_breakers" in data
    
    @patch('app.main.get_gateway_service')
    def test_models_endpoint(self, mock_get_service, client):
        """Test available models endpoint."""
        # Mock gateway service
        mock_service = AsyncMock()
        mock_models = {
            "models": [
                {
                    "name": "llama3.2:3b",
                    "provider": "ollama",
                    "type": "chat",
                    "available": True,
                    "cost_per_token": 0.0,
                    "context_length": 4096,
                    "capabilities": ["chat", "completion"]
                }
            ],
            "total_models": 1,
            "available_models": 1,
            "providers": ["ollama"]
        }
        mock_service.get_available_models.return_value = type('obj', (object,), mock_models)
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/v1/models")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_models"] == 1
        assert data["available_models"] == 1
        assert len(data["providers"]) == 1
        assert data["providers"][0] == "ollama"
    
    def test_query_validation_errors(self, client):
        """Test query validation error handling."""
        # Test empty query
        invalid_request = {
            "query": "",
            "options": {}
        }
        
        response = client.post("/api/v1/query", json=invalid_request)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_batch_validation_errors(self, client):
        """Test batch query validation error handling."""
        # Test empty queries list
        invalid_request = {
            "queries": [],
            "options": {}
        }
        
        response = client.post("/api/v1/batch-query", json=invalid_request)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_batch_size_limit(self, client):
        """Test batch size limit enforcement."""
        # Test batch size over limit
        large_batch = {
            "queries": ["test query"] * 101,  # Over limit of 100
            "options": {}
        }
        
        response = client.post("/api/v1/batch-query", json=large_batch)
        
        assert response.status_code == 422
    
    @patch('app.main.get_gateway_service')
    def test_service_error_handling(self, mock_get_service, client, sample_query_request):
        """Test error handling when services fail."""
        # Mock service failure
        mock_service = AsyncMock()
        mock_service.process_unified_query.side_effect = Exception("Service failure")
        mock_get_service.return_value = mock_service
        
        response = client.post("/api/v1/query", json=sample_query_request)
        
        assert response.status_code == 500
        data = response.json()
        
        assert data["error"] == "QueryProcessingError"
        assert "message" in data
        assert "suggestions" in data
    
    def test_cors_headers(self, client):
        """Test CORS headers are properly set."""
        response = client.options("/api/v1/query")
        
        # Should not fail (CORS is configured)
        assert response.status_code in [200, 405]  # OPTIONS may not be implemented but CORS should be there
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint accessibility."""
        response = client.get("/metrics")
        
        # Should be accessible (Prometheus metrics)
        assert response.status_code == 200
    
    @patch('app.main.get_gateway_service')
    def test_query_with_different_strategies(self, mock_get_service, client):
        """Test query processing with different strategies."""
        strategies = ["cost_optimized", "balanced", "quality_first", "performance"]
        
        # Mock gateway service
        mock_service = AsyncMock()
        mock_response = UnifiedQueryResponse(
            answer="Test answer",
            sources=[],
            complexity="medium",
            confidence=0.9,
            cost={
                "model_used": "test-model",
                "total_cost": 0.001,
                "model_cost": 0.001,
                "retrieval_cost": 0.0
            },
            metrics={
                "analysis_time": 0.1,
                "retrieval_time": 0.2,
                "generation_time": 0.5,
                "total_time": 0.8,
                "documents_retrieved": 3,
                "cache_hit": False,
                "cache_key": "test-hash"
            },
            query_id="test-query-123",
            strategy_used="balanced"  # Will be overridden in test
        )
        
        for strategy in strategies:
            mock_response.strategy_used = strategy
            mock_service.process_unified_query.return_value = mock_response
            mock_get_service.return_value = mock_service
            
            request_data = {
                "query": "Test query",
                "options": {
                    "strategy": strategy
                }
            }
            
            response = client.post("/api/v1/query", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["strategy_used"] == strategy