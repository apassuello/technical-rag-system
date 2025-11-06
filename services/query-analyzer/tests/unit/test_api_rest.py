"""
Unit tests for REST API endpoints.

Tests the FastAPI router and endpoint logic independently from
the full application context.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import uuid
from fastapi import HTTPException

from analyzer_app.api.rest import router, get_analyzer_service
from analyzer_app.core.analyzer import QueryAnalyzerService
from analyzer_app.schemas.requests import AnalyzeRequest, StatusRequest
from analyzer_app.schemas.responses import AnalyzeResponse, StatusResponse


class TestGetAnalyzerServiceDependency:
    """Test cases for get_analyzer_service dependency."""

    def test_get_analyzer_service_import(self):
        """Test that dependency imports main module function."""
        # This test verifies the dependency can import the function
        # In actual usage, this is overridden by the app
        
        with patch('app.api.rest.get_analyzer_service') as mock_get:
            mock_service = Mock(spec=QueryAnalyzerService)
            mock_get.return_value = mock_service
            
            # Should import and call the function
            result = get_analyzer_service()
            assert result is mock_service


class TestAnalyzeEndpoint:
    """Test cases for /analyze endpoint logic."""

    @pytest.mark.asyncio
    async def test_analyze_query_success(self, mock_metrics):
        """Test successful analyze request processing."""
        # Mock analyzer service
        mock_analyzer = AsyncMock(spec=QueryAnalyzerService)
        mock_analyzer.analyze_query.return_value = {
            "query": "What is Python?",
            "complexity": "simple",
            "confidence": 0.9,
            "features": {"length": 15},
            "recommended_models": ["ollama/llama3.2:3b"],
            "cost_estimate": {"ollama/llama3.2:3b": 0.0},
            "routing_strategy": "balanced",
            "processing_time": 0.02,
            "metadata": {"version": "1.0.0"}
        }
        
        # Mock the endpoint function directly
        from analyzer_app.api.rest import analyze_query
        
        request = AnalyzeRequest(query="What is Python?")
        mock_http_request = Mock()
        
        # Call endpoint function
        result = await analyze_query(request, mock_analyzer, mock_http_request)
        
        # Verify service was called correctly
        mock_analyzer.analyze_query.assert_called_once_with(
            query="What is Python?",
            context=None
        )
        
        # Verify response
        assert isinstance(result, AnalyzeResponse)
        assert result.query == "What is Python?"
        assert result.complexity == "simple"
        assert result.confidence == 0.9

    @pytest.mark.asyncio
    async def test_analyze_query_with_context(self, mock_metrics):
        """Test analyze request with context."""
        mock_analyzer = AsyncMock(spec=QueryAnalyzerService)
        mock_analyzer.analyze_query.return_value = {
            "query": "test",
            "complexity": "simple",
            "confidence": 0.8,
            "features": {},
            "recommended_models": [],
            "cost_estimate": {},
            "routing_strategy": "balanced",
            "processing_time": 0.01,
            "metadata": {}
        }
        
        from analyzer_app.api.rest import analyze_query
        
        context = {"user_id": "123", "session": "abc"}
        request = AnalyzeRequest(query="test", context=context)
        mock_http_request = Mock()
        
        await analyze_query(request, mock_analyzer, mock_http_request)
        
        # Verify context was passed
        mock_analyzer.analyze_query.assert_called_once_with(
            query="test",
            context=context
        )

    @pytest.mark.asyncio
    async def test_analyze_query_validation_error(self, mock_metrics):
        """Test analyze endpoint with validation error."""
        mock_analyzer = AsyncMock(spec=QueryAnalyzerService)
        mock_analyzer.analyze_query.side_effect = ValueError("Invalid query format")
        
        from analyzer_app.api.rest import analyze_query
        
        request = AnalyzeRequest(query="invalid query")
        mock_http_request = Mock()
        
        # Should raise HTTPException with 422 status
        with pytest.raises(HTTPException) as exc_info:
            await analyze_query(request, mock_analyzer, mock_http_request)
        
        assert exc_info.value.status_code == 422
        assert "Invalid query format" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_analyze_query_service_error(self, mock_metrics):
        """Test analyze endpoint with service error."""
        mock_analyzer = AsyncMock(spec=QueryAnalyzerService)
        mock_analyzer.analyze_query.side_effect = RuntimeError("Service error")
        
        from analyzer_app.api.rest import analyze_query
        
        request = AnalyzeRequest(query="test")
        mock_http_request = Mock()
        
        # Should raise HTTPException with 500 status
        with pytest.raises(HTTPException) as exc_info:
            await analyze_query(request, mock_analyzer, mock_http_request)
        
        assert exc_info.value.status_code == 500
        
        # Should include error details
        error_detail = exc_info.value.detail
        assert "AnalysisError" in error_detail["error"]
        assert "Query analysis failed" in error_detail["message"]
        assert "error" in error_detail["details"]
        assert "request_id" in error_detail

    @pytest.mark.asyncio
    async def test_analyze_query_request_id_generation(self, mock_metrics):
        """Test that request IDs are generated for tracking."""
        mock_analyzer = AsyncMock(spec=QueryAnalyzerService)
        mock_analyzer.analyze_query.side_effect = Exception("Test error")
        
        from analyzer_app.api.rest import analyze_query
        
        request = AnalyzeRequest(query="test")
        mock_http_request = Mock()
        
        with patch('app.api.rest.uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = Mock()
            mock_uuid.return_value.__str__ = Mock(return_value="test-request-id")
            
            with pytest.raises(HTTPException) as exc_info:
                await analyze_query(request, mock_analyzer, mock_http_request)
            
            # Verify UUID was generated
            mock_uuid.assert_called_once()
            
            # Verify request_id in error response
            assert exc_info.value.detail["request_id"] == "test-request-id"

    @pytest.mark.asyncio
    async def test_analyze_query_metrics_success(self, mock_metrics):
        """Test metrics collection on successful analysis."""
        mock_analyzer = AsyncMock(spec=QueryAnalyzerService)
        mock_analyzer.analyze_query.return_value = {
            "query": "test",
            "complexity": "medium",
            "confidence": 0.75,
            "features": {},
            "recommended_models": [],
            "cost_estimate": {},
            "routing_strategy": "balanced",
            "processing_time": 0.03,
            "metadata": {}
        }
        
        with patch('app.api.rest.API_REQUESTS') as mock_requests, \
             patch('app.api.rest.API_REQUEST_DURATION') as mock_duration:
            
            from analyzer_app.api.rest import analyze_query
            
            request = AnalyzeRequest(query="test")
            mock_http_request = Mock()
            
            await analyze_query(request, mock_analyzer, mock_http_request)
            
            # Verify success metrics
            mock_requests.labels.assert_called_with(endpoint="analyze", method="POST", status="success")
            mock_requests.labels().inc.assert_called_once()
            
            mock_duration.labels.assert_called_with(endpoint="analyze")
            mock_duration.labels().observe.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_query_metrics_error(self, mock_metrics):
        """Test metrics collection on analysis error."""
        mock_analyzer = AsyncMock(spec=QueryAnalyzerService)
        mock_analyzer.analyze_query.side_effect = RuntimeError("Test error")
        
        with patch('app.api.rest.API_REQUESTS') as mock_requests:
            
            from analyzer_app.api.rest import analyze_query
            
            request = AnalyzeRequest(query="test")
            mock_http_request = Mock()
            
            with pytest.raises(HTTPException):
                await analyze_query(request, mock_analyzer, mock_http_request)
            
            # Verify error metrics
            mock_requests.labels.assert_called_with(endpoint="analyze", method="POST", status="error")
            mock_requests.labels().inc.assert_called_once()


class TestStatusEndpoint:
    """Test cases for /status endpoint logic."""

    @pytest.mark.asyncio
    async def test_get_analyzer_status_success(self, mock_metrics):
        """Test successful status request."""
        mock_analyzer = AsyncMock(spec=QueryAnalyzerService)
        mock_analyzer.get_analyzer_status.return_value = {
            "initialized": True,
            "status": "healthy",
            "analyzer_type": "Epic1QueryAnalyzer",
            "configuration": {"strategy": "balanced"},
            "performance": {"avg_time": 0.02},
            "components": {"feature_extractor": "healthy"}
        }
        
        from analyzer_app.api.rest import get_analyzer_status
        
        request = StatusRequest()
        result = await get_analyzer_status(request, mock_analyzer)
        
        # Verify service was called
        mock_analyzer.get_analyzer_status.assert_called_once()
        
        # Verify response
        assert isinstance(result, StatusResponse)
        assert result.initialized is True
        assert result.status == "healthy"
        assert result.analyzer_type == "Epic1QueryAnalyzer"

    @pytest.mark.asyncio
    async def test_get_analyzer_status_exclude_performance(self, mock_metrics):
        """Test status request excluding performance metrics."""
        mock_analyzer = AsyncMock(spec=QueryAnalyzerService)
        mock_analyzer.get_analyzer_status.return_value = {
            "initialized": True,
            "status": "healthy",
            "performance": {"should_be_removed": True},
            "configuration": {"should_remain": True}
        }
        
        from analyzer_app.api.rest import get_analyzer_status
        
        request = StatusRequest(include_performance=False)
        result = await get_analyzer_status(request, mock_analyzer)
        
        # Performance should be None in response
        assert result.performance is None
        assert result.configuration == {"should_remain": True}

    @pytest.mark.asyncio
    async def test_get_analyzer_status_exclude_config(self, mock_metrics):
        """Test status request excluding configuration."""
        mock_analyzer = AsyncMock(spec=QueryAnalyzerService)
        mock_analyzer.get_analyzer_status.return_value = {
            "initialized": True,
            "status": "healthy",
            "performance": {"should_remain": True},
            "configuration": {"should_be_removed": True}
        }
        
        from analyzer_app.api.rest import get_analyzer_status
        
        request = StatusRequest(include_config=False)
        result = await get_analyzer_status(request, mock_analyzer)
        
        # Configuration should be None in response
        assert result.configuration is None
        assert result.performance == {"should_remain": True}

    @pytest.mark.asyncio
    async def test_get_analyzer_status_error(self, mock_metrics):
        """Test status endpoint with service error."""
        mock_analyzer = AsyncMock(spec=QueryAnalyzerService)
        mock_analyzer.get_analyzer_status.side_effect = RuntimeError("Status error")
        
        from analyzer_app.api.rest import get_analyzer_status
        
        request = StatusRequest()
        
        # Should raise HTTPException with 500 status
        with pytest.raises(HTTPException) as exc_info:
            await get_analyzer_status(request, mock_analyzer)
        
        assert exc_info.value.status_code == 500
        assert "Status error" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_analyzer_status_metrics(self, mock_metrics):
        """Test status endpoint metrics collection."""
        mock_analyzer = AsyncMock(spec=QueryAnalyzerService)
        mock_analyzer.get_analyzer_status.return_value = {
            "initialized": True,
            "status": "healthy"
        }
        
        with patch('app.api.rest.API_REQUESTS') as mock_requests:
            
            from analyzer_app.api.rest import get_analyzer_status
            
            request = StatusRequest()
            await get_analyzer_status(request, mock_analyzer)
            
            # Verify success metrics
            mock_requests.labels.assert_called_with(endpoint="status", method="GET", status="success")
            mock_requests.labels().inc.assert_called_once()


class TestComponentsEndpoint:
    """Test cases for /components endpoint logic."""

    @pytest.mark.asyncio
    async def test_get_component_info_success(self, mock_metrics):
        """Test successful components request."""
        mock_analyzer = AsyncMock(spec=QueryAnalyzerService)
        mock_analyzer.get_analyzer_status.return_value = {
            "initialized": True,
            "analyzer_type": "Epic1QueryAnalyzer",
            "components": {
                "feature_extractor": "healthy",
                "complexity_classifier": "healthy",
                "model_recommender": "healthy"
            },
            "performance": {"avg_time": 0.02},
            "configuration": {"strategy": "balanced"}
        }
        
        from analyzer_app.api.rest import get_component_info
        
        result = await get_component_info(mock_analyzer)
        
        # Verify structure
        assert "service_info" in result
        assert "components" in result
        assert "performance" in result
        assert "configuration" in result
        
        # Verify service info
        service_info = result["service_info"]
        assert service_info["name"] == "query-analyzer"
        assert service_info["version"] == "1.0.0"
        assert service_info["analyzer_type"] == "Epic1QueryAnalyzer"
        assert service_info["initialized"] is True
        
        # Verify components
        components = result["components"]
        assert "feature_extractor" in components
        assert "complexity_classifier" in components
        assert "model_recommender" in components
        
        # Each component should have status, description, and capabilities
        for component in components.values():
            assert "status" in component
            assert "description" in component
            assert "capabilities" in component
            assert isinstance(component["capabilities"], list)

    @pytest.mark.asyncio
    async def test_get_component_info_error(self, mock_metrics):
        """Test components endpoint with service error."""
        mock_analyzer = AsyncMock(spec=QueryAnalyzerService)
        mock_analyzer.get_analyzer_status.side_effect = RuntimeError("Component error")
        
        from analyzer_app.api.rest import get_component_info
        
        # Should raise HTTPException with 500 status
        with pytest.raises(HTTPException) as exc_info:
            await get_component_info(mock_analyzer)
        
        assert exc_info.value.status_code == 500
        assert "Component error" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_component_info_metrics(self, mock_metrics):
        """Test components endpoint metrics collection."""
        mock_analyzer = AsyncMock(spec=QueryAnalyzerService)
        mock_analyzer.get_analyzer_status.return_value = {
            "initialized": True,
            "components": {}
        }
        
        with patch('app.api.rest.API_REQUESTS') as mock_requests:
            
            from analyzer_app.api.rest import get_component_info
            
            await get_component_info(mock_analyzer)
            
            # Verify success metrics
            mock_requests.labels.assert_called_with(endpoint="components", method="GET", status="success")
            mock_requests.labels().inc.assert_called_once()


class TestBatchAnalyzeEndpoint:
    """Test cases for /batch-analyze endpoint logic."""

    @pytest.mark.asyncio
    async def test_batch_analyze_success(self, mock_metrics):
        """Test successful batch analysis."""
        mock_analyzer = AsyncMock(spec=QueryAnalyzerService)
        
        # Mock different analysis results
        mock_analyzer.analyze_query.side_effect = [
            {
                "query": "query1",
                "complexity": "simple",
                "confidence": 0.9,
                "features": {},
                "recommended_models": [],
                "cost_estimate": {},
                "routing_strategy": "balanced",
                "processing_time": 0.01,
                "metadata": {}
            },
            {
                "query": "query2",
                "complexity": "medium",
                "confidence": 0.8,
                "features": {},
                "recommended_models": [],
                "cost_estimate": {},
                "routing_strategy": "balanced",
                "processing_time": 0.02,
                "metadata": {}
            }
        ]
        
        from analyzer_app.api.rest import batch_analyze_queries
        
        queries = ["query1", "query2"]
        context = {"user": "test"}
        
        result = await batch_analyze_queries(queries, context, mock_analyzer)
        
        # Verify service calls
        assert mock_analyzer.analyze_query.call_count == 2
        mock_analyzer.analyze_query.assert_any_call(query="query1", context=context)
        mock_analyzer.analyze_query.assert_any_call(query="query2", context=context)
        
        # Verify response structure
        assert "request_id" in result
        assert result["total_queries"] == 2
        assert result["successful_analyses"] == 2
        assert result["failed_analyses"] == 0
        assert "processing_time" in result
        assert "complexity_distribution" in result
        assert "results" in result
        
        # Verify complexity distribution
        complexity_dist = result["complexity_distribution"]
        assert complexity_dist["simple"] == 1
        assert complexity_dist["medium"] == 1
        assert complexity_dist["complex"] == 0
        
        # Verify individual results
        results = result["results"]
        assert len(results) == 2
        assert results[0]["index"] == 0
        assert results[0]["query"] == "query1"
        assert "result" in results[0]
        assert results[1]["index"] == 1
        assert results[1]["query"] == "query2"
        assert "result" in results[1]

    @pytest.mark.asyncio
    async def test_batch_analyze_empty_queries(self, mock_metrics):
        """Test batch analysis with empty query list."""
        mock_analyzer = AsyncMock(spec=QueryAnalyzerService)
        
        from analyzer_app.api.rest import batch_analyze_queries
        
        # Should raise HTTPException for empty queries
        with pytest.raises(HTTPException) as exc_info:
            await batch_analyze_queries([], None, mock_analyzer)
        
        assert exc_info.value.status_code == 422
        assert "At least one query is required" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_batch_analyze_too_many_queries(self, mock_metrics):
        """Test batch analysis with too many queries."""
        mock_analyzer = AsyncMock(spec=QueryAnalyzerService)
        
        from analyzer_app.api.rest import batch_analyze_queries
        
        # Create 101 queries (exceeds limit of 100)
        queries = [f"query{i}" for i in range(101)]
        
        # Should raise HTTPException for too many queries
        with pytest.raises(HTTPException) as exc_info:
            await batch_analyze_queries(queries, None, mock_analyzer)
        
        assert exc_info.value.status_code == 422
        assert "Maximum 100 queries per batch request" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_batch_analyze_partial_failures(self, mock_metrics):
        """Test batch analysis with some failures."""
        mock_analyzer = AsyncMock(spec=QueryAnalyzerService)
        
        # Mock one success, one failure
        mock_analyzer.analyze_query.side_effect = [
            {
                "query": "query1",
                "complexity": "simple",
                "confidence": 0.9,
                "features": {},
                "recommended_models": [],
                "cost_estimate": {},
                "routing_strategy": "balanced",
                "processing_time": 0.01,
                "metadata": {}
            },
            RuntimeError("Analysis failed for query2")
        ]
        
        from analyzer_app.api.rest import batch_analyze_queries
        
        queries = ["query1", "query2"]
        result = await batch_analyze_queries(queries, None, mock_analyzer)
        
        # Verify response handles partial failures
        assert result["total_queries"] == 2
        assert result["successful_analyses"] == 1
        assert result["failed_analyses"] == 1
        
        # Verify results include both success and error
        results = result["results"]
        assert len(results) == 2
        assert "result" in results[0]
        assert "error" in results[1]
        assert results[1]["error"] == "Analysis failed for query2"

    @pytest.mark.asyncio
    async def test_batch_analyze_metrics(self, mock_metrics):
        """Test batch analysis metrics collection."""
        mock_analyzer = AsyncMock(spec=QueryAnalyzerService)
        mock_analyzer.analyze_query.return_value = {
            "complexity": "simple",
            "confidence": 0.9,
            "features": {},
            "recommended_models": [],
            "cost_estimate": {},
            "routing_strategy": "balanced",
            "processing_time": 0.01,
            "metadata": {}
        }
        
        with patch('app.api.rest.API_REQUESTS') as mock_requests, \
             patch('app.api.rest.API_REQUEST_DURATION') as mock_duration:
            
            from analyzer_app.api.rest import batch_analyze_queries
            
            queries = ["query1", "query2"]
            await batch_analyze_queries(queries, None, mock_analyzer)
            
            # Verify success metrics
            mock_requests.labels.assert_called_with(endpoint="batch-analyze", method="POST", status="success")
            mock_requests.labels().inc.assert_called_once()
            
            mock_duration.labels.assert_called_with(endpoint="batch-analyze")
            mock_duration.labels().observe.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_analyze_request_id(self, mock_metrics):
        """Test that batch analysis generates request ID."""
        mock_analyzer = AsyncMock(spec=QueryAnalyzerService)
        mock_analyzer.analyze_query.return_value = {
            "complexity": "simple",
            "confidence": 0.9,
            "features": {},
            "recommended_models": [],
            "cost_estimate": {},
            "routing_strategy": "balanced",
            "processing_time": 0.01,
            "metadata": {}
        }
        
        from analyzer_app.api.rest import batch_analyze_queries
        
        with patch('app.api.rest.uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = Mock()
            mock_uuid.return_value.__str__ = Mock(return_value="batch-request-id")
            
            queries = ["query1"]
            result = await batch_analyze_queries(queries, None, mock_analyzer)
            
            # Verify UUID was generated
            mock_uuid.assert_called_once()
            assert result["request_id"] == "batch-request-id"