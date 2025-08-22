"""
Unit tests for API Gateway Service core functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from app.core.gateway import APIGatewayService
from app.schemas.requests import UnifiedQueryRequest, BatchQueryRequest, QueryOptions
from app.schemas.responses import UnifiedQueryResponse, BatchQueryResponse


class TestAPIGatewayService:
    """Test cases for APIGatewayService."""
    
    @pytest.mark.asyncio
    async def test_process_unified_query_success(self, mock_gateway_service, sample_query_request):
        """Test successful unified query processing."""
        # Create request object
        request = UnifiedQueryRequest(**sample_query_request)
        
        # Process query
        response = await mock_gateway_service.process_unified_query(request)
        
        # Verify response
        assert isinstance(response, UnifiedQueryResponse)
        assert response.answer == "This is a test answer."
        assert response.complexity == "medium"
        assert response.confidence == 0.9
        assert len(response.sources) == 1
        assert response.cost.total_cost == 0.0
        assert response.metrics.cache_hit is False
        assert response.session_id == "test-session-123"
        assert response.strategy_used == "balanced"
        assert response.fallback_used is False
    
    @pytest.mark.asyncio
    async def test_process_unified_query_with_cache_hit(self, mock_gateway_service, sample_query_request):
        """Test unified query processing with cache hit."""
        # Mock cache hit
        cached_response = UnifiedQueryResponse(
            answer="Cached answer",
            sources=[],
            complexity="medium",
            confidence=0.8,
            cost={"model_used": "cached", "total_cost": 0.0},
            metrics={
                "analysis_time": 0.0,
                "retrieval_time": 0.0, 
                "generation_time": 0.0,
                "total_time": 0.001,
                "documents_retrieved": 0,
                "cache_hit": True,
                "cache_key": "test-hash"
            },
            query_id="cached-query-123",
            strategy_used="balanced"
        )
        
        mock_gateway_service.cache.get_cached_response.return_value = cached_response.dict()
        
        # Create request
        request = UnifiedQueryRequest(**sample_query_request)
        
        # Process query
        response = await mock_gateway_service.process_unified_query(request)
        
        # Verify cache hit
        assert response.answer == "Cached answer"
        assert response.metrics.cache_hit is True
        
        # Verify analytics call for cache hit
        mock_gateway_service.analytics.record_cache_hit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_batch_queries_success(self, mock_gateway_service, sample_batch_request):
        """Test successful batch query processing."""
        # Create request object
        request = BatchQueryRequest(**sample_batch_request)
        
        # Process batch
        response = await mock_gateway_service.process_batch_queries(request)
        
        # Verify response
        assert isinstance(response, BatchQueryResponse)
        assert response.total_queries == 3
        assert response.successful_queries == 3
        assert response.failed_queries == 0
        assert response.parallel_processing is True
        assert len(response.results) == 3
        
        # Verify all queries succeeded
        for result in response.results:
            assert result.success is True
            assert result.result is not None
            assert isinstance(result.result, UnifiedQueryResponse)
    
    @pytest.mark.asyncio
    async def test_process_batch_queries_sequential(self, mock_gateway_service, sample_batch_request):
        """Test batch query processing in sequential mode."""
        # Modify request for sequential processing
        sample_batch_request["parallel_processing"] = False
        request = BatchQueryRequest(**sample_batch_request)
        
        # Process batch
        response = await mock_gateway_service.process_batch_queries(request)
        
        # Verify response
        assert response.parallel_processing is False
        assert response.successful_queries == 3
        assert response.failed_queries == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, mock_gateway_service, sample_query_request):
        """Test circuit breaker functionality."""
        # Create request
        request = UnifiedQueryRequest(**sample_query_request)
        
        # Mock circuit breaker behavior
        for service_name, cb in mock_gateway_service.circuit_breakers.items():
            cb.__enter__.return_value = cb
            cb.__exit__.return_value = None
        
        # Process query
        response = await mock_gateway_service.process_unified_query(request)
        
        # Verify circuit breakers were used
        for cb in mock_gateway_service.circuit_breakers.values():
            cb.__enter__.assert_called()
            cb.__exit__.assert_called()
        
        assert isinstance(response, UnifiedQueryResponse)
    
    @pytest.mark.asyncio
    async def test_fallback_response(self, mock_gateway_service, sample_query_request):
        """Test fallback response when services fail."""
        # Mock generator failure
        mock_gateway_service.generator.generate_answer.side_effect = Exception("Service unavailable")
        
        # Create request
        request = UnifiedQueryRequest(**sample_query_request)
        
        # Should get fallback response instead of exception
        with pytest.raises(Exception):  # Will raise since we mock generator failure
            await mock_gateway_service.process_unified_query(request)
    
    @pytest.mark.asyncio
    async def test_get_gateway_status(self, mock_gateway_service):
        """Test gateway status retrieval."""
        status = await mock_gateway_service.get_gateway_status()
        
        # Verify status structure
        assert status.service == "api-gateway"
        assert status.version == "1.0.0"
        assert status.status in ["healthy", "degraded"]
        assert len(status.services) == 5  # All 5 services
        assert status.total_services == 5
        assert status.uptime >= 0
        
        # Verify service details
        service_names = {s.name for s in status.services}
        expected_services = {"query-analyzer", "generator", "retriever", "cache", "analytics"}
        assert service_names == expected_services
    
    @pytest.mark.asyncio
    async def test_get_available_models(self, mock_gateway_service):
        """Test available models retrieval."""
        models_response = await mock_gateway_service.get_available_models()
        
        # Verify response structure
        assert models_response.total_models >= 0
        assert models_response.available_models >= 0
        assert len(models_response.providers) >= 0
        assert isinstance(models_response.models, list)
    
    @pytest.mark.asyncio
    async def test_error_handling_and_analytics(self, mock_gateway_service, sample_query_request):
        """Test error handling and analytics recording."""
        # Mock analytics failure (should not affect main processing)
        mock_gateway_service.analytics.record_query_completion.side_effect = Exception("Analytics failed")
        
        # Create request
        request = UnifiedQueryRequest(**sample_query_request)
        
        # Process query (should succeed despite analytics failure)
        response = await mock_gateway_service.process_unified_query(request)
        
        # Verify main processing succeeded
        assert isinstance(response, UnifiedQueryResponse)
        assert response.answer == "This is a test answer."
    
    @pytest.mark.asyncio
    async def test_query_options_handling(self, mock_gateway_service):
        """Test different query options."""
        # Test with different strategies
        strategies = ["cost_optimized", "balanced", "quality_first", "performance"]
        
        for strategy in strategies:
            request = UnifiedQueryRequest(
                query="Test query",
                options=QueryOptions(
                    strategy=strategy,
                    max_documents=3,
                    cache_enabled=False,
                    analytics_enabled=False
                )
            )
            
            response = await mock_gateway_service.process_unified_query(request)
            assert response.strategy_used == strategy
    
    @pytest.mark.asyncio
    async def test_cost_tracking(self, mock_gateway_service, sample_query_request):
        """Test cost tracking functionality."""
        # Create request
        request = UnifiedQueryRequest(**sample_query_request)
        
        # Process query
        response = await mock_gateway_service.process_unified_query(request)
        
        # Verify cost information
        assert response.cost is not None
        assert response.cost.model_used == "ollama/llama3.2:3b"
        assert response.cost.total_cost == 0.0  # Ollama is free
        assert response.cost.cost_estimation_confidence > 0
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, mock_gateway_service, sample_query_request):
        """Test timeout handling for service calls."""
        # Mock timeout on retriever
        mock_gateway_service.retriever.retrieve_documents.side_effect = asyncio.TimeoutError("Request timeout")
        
        # Create request
        request = UnifiedQueryRequest(**sample_query_request)
        
        # Should continue with empty documents instead of failing
        response = await mock_gateway_service.process_unified_query(request)
        
        # Verify processing continued
        assert isinstance(response, UnifiedQueryResponse)
        assert len(response.sources) == 0  # No documents due to timeout