"""
Test Suite for API Gateway Service Core Implementation.

This test suite focuses on testing the business logic of the APIGatewayService class directly,
not through HTTP API endpoints. Tests the core orchestration functionality including service
client management, unified query processing, batch processing, and circuit breaker patterns.

Key Focus Areas:
- Service client initialization and management
- Unified query processing pipeline (cache -> analyze -> retrieve -> generate)
- Batch query processing with concurrency control
- Circuit breaker functionality for service failures
- Fallback response generation
- Service health monitoring and status reporting
- Request routing and optimization

Test Philosophy:
- Test SERVICE METHODS directly (not API endpoints)
- Mock service client dependencies
- Focus on business logic validation
- Achieve >70% coverage of implementation code
"""

import pytest
import asyncio
import time
import uuid
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
from pathlib import Path


def _setup_gateway_service_imports():
    """Set up imports for API Gateway Service implementation testing."""
    current_file = Path(__file__).resolve()
    project_root = current_file.parents[3]
    service_path = project_root / "services" / "api-gateway"
    
    if not service_path.exists():
        return False, f"Service path does not exist: {service_path}", {}
    
    service_path_str = str(service_path)
    if service_path_str not in sys.path:
        sys.path.insert(0, service_path_str)
    
    try:
        from gateway_app.core.gateway import APIGatewayService, SimpleCircuitBreaker
        from gateway_app.core.config import APIGatewaySettings, get_settings
        from gateway_app.schemas.requests import UnifiedQueryRequest, BatchQueryRequest, QueryOptions
        from gateway_app.schemas.responses import (
            UnifiedQueryResponse, BatchQueryResponse, BatchQueryResult,
            ProcessingMetrics, CostBreakdown, DocumentSource,
            GatewayStatusResponse, ServiceStatus, AvailableModelsResponse, ModelInfo
        )
        
        imports = {
            'APIGatewayService': APIGatewayService,
            'SimpleCircuitBreaker': SimpleCircuitBreaker,
            'APIGatewaySettings': APIGatewaySettings,
            'get_settings': get_settings,
            'UnifiedQueryRequest': UnifiedQueryRequest,
            'BatchQueryRequest': BatchQueryRequest,
            'QueryOptions': QueryOptions,
            'UnifiedQueryResponse': UnifiedQueryResponse,
            'BatchQueryResponse': BatchQueryResponse,
            'BatchQueryResult': BatchQueryResult,
            'ProcessingMetrics': ProcessingMetrics,
            'CostBreakdown': CostBreakdown,
            'DocumentSource': DocumentSource,
            'GatewayStatusResponse': GatewayStatusResponse,
            'ServiceStatus': ServiceStatus,
            'AvailableModelsResponse': AvailableModelsResponse,
            'ModelInfo': ModelInfo
        }
        return True, None, imports
    except ImportError as e:
        return False, f"Import failed: {str(e)}", {}
    except Exception as e:
        return False, f"Unexpected error: {str(e)}", {}


# Execute import setup
IMPORTS_AVAILABLE, IMPORT_ERROR, imported_classes = _setup_gateway_service_imports()

# Make imported classes available if imports succeeded
if IMPORTS_AVAILABLE:
    APIGatewayService = imported_classes['APIGatewayService']
    SimpleCircuitBreaker = imported_classes['SimpleCircuitBreaker']
    APIGatewaySettings = imported_classes['APIGatewaySettings']
    get_settings = imported_classes['get_settings']
    UnifiedQueryRequest = imported_classes['UnifiedQueryRequest']
    BatchQueryRequest = imported_classes['BatchQueryRequest']
    QueryOptions = imported_classes['QueryOptions']
    UnifiedQueryResponse = imported_classes['UnifiedQueryResponse']
    BatchQueryResponse = imported_classes['BatchQueryResponse']
    BatchQueryResult = imported_classes['BatchQueryResult']
    ProcessingMetrics = imported_classes['ProcessingMetrics']
    CostBreakdown = imported_classes['CostBreakdown']
    DocumentSource = imported_classes['DocumentSource']
    GatewayStatusResponse = imported_classes['GatewayStatusResponse']
    ServiceStatus = imported_classes['ServiceStatus']
    AvailableModelsResponse = imported_classes['AvailableModelsResponse']
    ModelInfo = imported_classes['ModelInfo']


class TestSimpleCircuitBreaker:
    """Test simple circuit breaker implementation."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state allows operations."""
        cb = SimpleCircuitBreaker(failure_threshold=3, recovery_timeout=60)
        
        # Initial state should be closed
        assert cb.state == "closed"
        assert cb.failure_count == 0
        
        # Should allow operation in closed state
        with cb:
            pass  # Successful operation
        
        assert cb.state == "closed"
        assert cb.failure_count == 0

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    def test_circuit_breaker_failure_accumulation(self):
        """Test circuit breaker failure accumulation and state transition."""
        cb = SimpleCircuitBreaker(failure_threshold=2, recovery_timeout=60)
        
        # First failure
        try:
            with cb:
                raise Exception("Service failure")
        except Exception:
            pass
        
        assert cb.state == "closed"
        assert cb.failure_count == 1
        
        # Second failure should open the circuit
        try:
            with cb:
                raise Exception("Another service failure")
        except Exception:
            pass
        
        assert cb.state == "open"
        assert cb.failure_count == 2

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    def test_circuit_breaker_open_state_blocks_operations(self):
        """Test circuit breaker blocks operations when open."""
        cb = SimpleCircuitBreaker(failure_threshold=1, recovery_timeout=60)
        
        # Trigger failure to open circuit
        try:
            with cb:
                raise Exception("Service failure")
        except Exception:
            pass
        
        assert cb.state == "open"
        
        # Should block subsequent operations
        with pytest.raises(Exception, match="Circuit breaker is open"):
            with cb:
                pass

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker recovery to half-open state."""
        cb = SimpleCircuitBreaker(failure_threshold=1, recovery_timeout=1)  # 1 second timeout
        
        # Open the circuit
        try:
            with cb:
                raise Exception("Service failure")
        except Exception:
            pass
        
        assert cb.state == "open"
        
        # Simulate time passage
        cb.last_failure_time = time.time() - 2  # 2 seconds ago
        
        # Should allow operation in half-open state
        with cb:
            pass  # Successful operation should close circuit
        
        assert cb.state == "closed"
        assert cb.failure_count == 0


class TestAPIGatewayServiceInitialization:
    """Test API Gateway Service initialization and setup."""

    @pytest.fixture
    def mock_settings(self):
        """Mock gateway settings."""
        settings = Mock(spec=APIGatewaySettings)
        settings.get_service_endpoint.return_value = "http://localhost:8000"
        settings.circuit_breaker_failure_threshold = 5
        settings.circuit_breaker_recovery_timeout = 60
        return settings

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    def test_gateway_service_initialization_basic(self, mock_settings):
        """Test basic gateway service initialization."""
        service = APIGatewayService(settings=mock_settings)
        
        # Verify basic initialization
        assert service.settings == mock_settings
        assert service.query_analyzer is None  # Not initialized yet
        assert service.generator is None
        assert service.retriever is None
        assert service.cache is None
        assert service.analytics is None
        assert service.circuit_breakers == {}
        assert service.requests_processed == 0
        assert service.error_count == 0

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_gateway_service_full_initialization(self, mock_settings):
        """Test full gateway service initialization with all clients."""
        with patch('gateway_app.core.gateway.QueryAnalyzerClient') as mock_analyzer_client, \
             patch('gateway_app.core.gateway.GeneratorClient') as mock_generator_client, \
             patch('gateway_app.core.gateway.RetrieverClient') as mock_retriever_client, \
             patch('gateway_app.core.gateway.CacheClient') as mock_cache_client, \
             patch('gateway_app.core.gateway.AnalyticsClient') as mock_analytics_client:
            
            # Mock client instances
            mock_clients = {
                'analyzer': AsyncMock(),
                'generator': AsyncMock(),
                'retriever': AsyncMock(),
                'cache': AsyncMock(),
                'analytics': AsyncMock()
            }
            
            mock_analyzer_client.return_value = mock_clients['analyzer']
            mock_generator_client.return_value = mock_clients['generator']
            mock_retriever_client.return_value = mock_clients['retriever']
            mock_cache_client.return_value = mock_clients['cache']
            mock_analytics_client.return_value = mock_clients['analytics']
            
            # Mock health checks
            for client in mock_clients.values():
                client.health_check.return_value = True
            
            # Initialize service
            service = APIGatewayService(settings=mock_settings)
            await service.initialize()
            
            # Verify clients were created
            assert service.query_analyzer is not None
            assert service.generator is not None
            assert service.retriever is not None
            assert service.cache is not None
            assert service.analytics is not None
            
            # Verify circuit breakers were created
            assert len(service.circuit_breakers) == 5
            for service_name in ["query-analyzer", "generator", "retriever", "cache", "analytics"]:
                assert service_name in service.circuit_breakers
                assert isinstance(service.circuit_breakers[service_name], SimpleCircuitBreaker)

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_gateway_initialization_health_check_failures(self, mock_settings):
        """Test gateway initialization handles health check failures gracefully."""
        with patch('gateway_app.core.gateway.QueryAnalyzerClient') as mock_analyzer_client, \
             patch('gateway_app.core.gateway.GeneratorClient') as mock_generator_client, \
             patch('gateway_app.core.gateway.RetrieverClient') as mock_retriever_client, \
             patch('gateway_app.core.gateway.CacheClient') as mock_cache_client, \
             patch('gateway_app.core.gateway.AnalyticsClient') as mock_analytics_client:
            
            # Mock clients with failing health checks
            mock_clients = {
                'analyzer': AsyncMock(),
                'generator': AsyncMock(),
                'retriever': AsyncMock(),
                'cache': AsyncMock(),
                'analytics': AsyncMock()
            }
            
            mock_analyzer_client.return_value = mock_clients['analyzer']
            mock_generator_client.return_value = mock_clients['generator']
            mock_retriever_client.return_value = mock_clients['retriever']
            mock_cache_client.return_value = mock_clients['cache']
            mock_analytics_client.return_value = mock_clients['analytics']
            
            # Make some health checks fail
            mock_clients['analyzer'].health_check.return_value = True
            mock_clients['generator'].health_check.side_effect = Exception("Generator down")
            mock_clients['retriever'].health_check.return_value = False
            mock_clients['cache'].health_check.return_value = True
            mock_clients['analytics'].health_check.return_value = True
            
            # Should not raise exception during initialization
            service = APIGatewayService(settings=mock_settings)
            await service.initialize()  # Should complete without raising
            
            # Service should still be initialized
            assert service.query_analyzer is not None
            assert service.generator is not None


class TestUnifiedQueryProcessing:
    """Test unified query processing pipeline."""

    @pytest.fixture
    def mock_gateway_with_clients(self, mock_settings):
        """Create gateway with mocked service clients."""
        with patch('gateway_app.core.gateway.QueryAnalyzerClient') as mock_analyzer_client, \
             patch('gateway_app.core.gateway.GeneratorClient') as mock_generator_client, \
             patch('gateway_app.core.gateway.RetrieverClient') as mock_retriever_client, \
             patch('gateway_app.core.gateway.CacheClient') as mock_cache_client, \
             patch('gateway_app.core.gateway.AnalyticsClient') as mock_analytics_client:
            
            service = APIGatewayService(settings=mock_settings)
            
            # Create mock clients
            service.query_analyzer = AsyncMock()
            service.generator = AsyncMock()
            service.retriever = AsyncMock()
            service.cache = AsyncMock()
            service.analytics = AsyncMock()
            
            # Initialize circuit breakers manually
            service._initialize_circuit_breakers()
            
            return service

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_unified_query_processing_cache_miss_full_pipeline(self, mock_gateway_with_clients):
        """Test complete query processing pipeline with cache miss."""
        service = mock_gateway_with_clients
        
        # Mock cache miss
        service.cache.get_cached_response.return_value = None
        
        # Mock query analysis
        analysis_result = {
            "complexity": "medium",
            "confidence": 0.85,
            "recommended_models": ["openai/gpt-4"],
            "cost_estimate": {"openai/gpt-4": 0.005},
            "routing_strategy": "cost_optimized",
            "processing_time": 0.15
        }
        service.query_analyzer.analyze_query.return_value = analysis_result
        
        # Mock document retrieval
        retrieved_docs = [
            {
                "id": "doc_1",
                "title": "RISC-V Overview",
                "content": "RISC-V is an open instruction set architecture...",
                "score": 0.92,
                "metadata": {"source": "documentation"}
            },
            {
                "id": "doc_2", 
                "title": "ISA Fundamentals",
                "content": "Instruction Set Architecture defines...",
                "score": 0.87,
                "metadata": {"source": "handbook"}
            }
        ]
        service.retriever.retrieve_documents.return_value = retrieved_docs
        
        # Mock answer generation
        generation_result = {
            "answer": "RISC-V is an open instruction set architecture that provides a free and open foundation for custom processors.",
            "model_used": "openai/gpt-4",
            "input_tokens": 450,
            "output_tokens": 125,
            "cost": 0.0042,
            "confidence": 0.89,
            "tokens_generated": 125
        }
        service.generator.generate_answer.return_value = generation_result
        
        # Mock successful caching and analytics
        service.cache.cache_response.return_value = True
        service.analytics.record_query_completion.return_value = True
        
        # Create test request
        options = QueryOptions(
            strategy="cost_optimized",
            max_documents=10,
            cache_enabled=True,
            force_refresh=False,
            analytics_enabled=True
        )
        
        request = UnifiedQueryRequest(
            query="What is RISC-V?",
            options=options,
            session_id="test_session_123",
            user_id="test_user"
        )
        
        # Process query
        response = await service.process_unified_query(request)
        
        # Verify response structure
        assert isinstance(response, UnifiedQueryResponse)
        assert response.answer == generation_result["answer"]
        assert response.complexity == "medium"
        assert response.confidence == 0.89
        assert response.strategy_used == "cost_optimized"
        assert response.fallback_used is False
        assert len(response.sources) == 2
        
        # Verify cost breakdown
        assert response.cost.model_used == "openai/gpt-4"
        assert response.cost.input_tokens == 450
        assert response.cost.output_tokens == 125
        assert response.cost.total_cost == 0.0042
        
        # Verify processing metrics
        assert response.metrics.cache_hit is False
        assert response.metrics.documents_retrieved == 2
        assert response.metrics.tokens_generated == 125
        
        # Verify all service calls were made
        service.query_analyzer.analyze_query.assert_called_once()
        service.retriever.retrieve_documents.assert_called_once()
        service.generator.generate_answer.assert_called_once()
        service.cache.cache_response.assert_called_once()
        service.analytics.record_query_completion.assert_called_once()
        
        # Verify service metrics updated
        assert service.requests_processed == 1
        assert service.error_count == 0

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_unified_query_processing_cache_hit(self, mock_gateway_with_clients):
        """Test query processing with cache hit (short circuit)."""
        service = mock_gateway_with_clients
        
        # Mock cache hit with complete response
        cached_response_data = {
            "answer": "Cached answer about RISC-V architecture",
            "sources": [{"id": "cached_doc", "title": "Cached Doc", "content": "cached", "score": 0.9}],
            "complexity": "simple",
            "confidence": 0.95,
            "cost": {"total_cost": 0.0, "model_used": "cache"},
            "metrics": {"cache_hit": True, "total_time": 0.005},
            "query_id": "cached_query_123",
            "session_id": "test_session",
            "strategy_used": "cached",
            "fallback_used": False,
            "warnings": []
        }
        
        service.cache.get_cached_response.return_value = cached_response_data
        service.analytics.record_cache_hit.return_value = True
        
        # Create test request
        options = QueryOptions(cache_enabled=True, force_refresh=False, analytics_enabled=True)
        request = UnifiedQueryRequest(query="What is RISC-V?", options=options)
        
        # Process query
        response = await service.process_unified_query(request)
        
        # Should return cached response directly
        assert response.answer == "Cached answer about RISC-V architecture"
        assert response.complexity == "simple"
        
        # Should not call analysis, retrieval, or generation
        service.query_analyzer.analyze_query.assert_not_called()
        service.retriever.retrieve_documents.assert_not_called()
        service.generator.generate_answer.assert_not_called()
        
        # Should record cache hit
        service.analytics.record_cache_hit.assert_called_once()

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_unified_query_processing_with_service_failures(self, mock_gateway_with_clients):
        """Test query processing with service failures and fallbacks."""
        service = mock_gateway_with_clients
        
        # Mock cache miss
        service.cache.get_cached_response.return_value = None
        
        # Mock query analyzer failure (should use fallback analysis)
        service.query_analyzer.analyze_query.side_effect = Exception("Analyzer service down")
        
        # Mock successful retrieval and generation
        service.retriever.retrieve_documents.return_value = []
        generation_result = {
            "answer": "Generated answer despite analyzer failure",
            "model_used": "ollama/llama3.2:3b",
            "cost": 0.0,
            "confidence": 0.6,
            "tokens_generated": 80
        }
        service.generator.generate_answer.return_value = generation_result
        
        # Create test request
        options = QueryOptions(strategy="balanced", analytics_enabled=True)
        request = UnifiedQueryRequest(query="Complex technical query", options=options)
        
        # Process query
        response = await service.process_unified_query(request)
        
        # Should complete with fallback analysis
        assert response.answer == "Generated answer despite analyzer failure"
        assert response.complexity == "medium"  # Fallback complexity
        assert response.confidence == 0.6
        
        # Should use fallback model recommendation
        assert "ollama/llama3.2:3b" in str(response.cost.model_used)

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_unified_query_processing_generation_failure_with_fallback(self, mock_gateway_with_clients):
        """Test query processing when generation fails and fallback is used."""
        service = mock_gateway_with_clients
        
        # Mock successful analysis and retrieval
        service.cache.get_cached_response.return_value = None
        service.query_analyzer.analyze_query.return_value = {
            "complexity": "complex",
            "recommended_models": ["openai/gpt-4"]
        }
        service.retriever.retrieve_documents.return_value = [{"id": "doc1", "content": "test"}]
        
        # Mock generation failure
        service.generator.generate_answer.side_effect = Exception("Generation service failed")
        
        # Mock analytics
        service.analytics.record_error.return_value = True
        
        # Create test request
        options = QueryOptions(analytics_enabled=True)
        request = UnifiedQueryRequest(query="Test query", options=options)
        
        # Should try fallback response
        response = await service.process_unified_query(request)
        
        # Should return fallback response
        assert response.fallback_used is True
        assert "unable to process" in response.answer.lower()
        assert response.confidence == 0.0
        assert response.cost.total_cost == 0.0
        assert len(response.warnings) > 0
        
        # Should record error
        service.analytics.record_error.assert_called_once()


class TestBatchQueryProcessing:
    """Test batch query processing functionality."""

    @pytest.fixture
    def mock_gateway_for_batch(self, mock_settings):
        """Create gateway service for batch processing tests."""
        service = APIGatewayService(settings=mock_settings)
        service._initialize_circuit_breakers()
        
        # Mock the unified query processing method
        service.process_unified_query = AsyncMock()
        
        return service

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_batch_query_processing_sequential(self, mock_gateway_for_batch):
        """Test batch query processing in sequential mode."""
        service = mock_gateway_for_batch
        
        # Mock successful responses for each query
        mock_responses = []
        for i in range(3):
            mock_response = UnifiedQueryResponse(
                answer=f"Answer {i}",
                sources=[],
                complexity="simple",
                confidence=0.8,
                cost=CostBreakdown(model_used="test", total_cost=0.001),
                metrics=ProcessingMetrics(total_time=1.0),
                query_id=f"query_{i}",
                session_id="batch_session",
                strategy_used="test",
                fallback_used=False,
                warnings=[]
            )
            mock_responses.append(mock_response)
        
        service.process_unified_query.side_effect = mock_responses
        
        # Create batch request
        options = QueryOptions(strategy="balanced")
        batch_request = BatchQueryRequest(
            queries=["Query 1", "Query 2", "Query 3"],
            parallel_processing=False,  # Sequential
            options=options,
            session_id="batch_session"
        )
        
        # Process batch
        batch_response = await service.process_batch_queries(batch_request)
        
        # Verify batch response
        assert isinstance(batch_response, BatchQueryResponse)
        assert batch_response.total_queries == 3
        assert batch_response.successful_queries == 3
        assert batch_response.failed_queries == 0
        assert batch_response.parallel_processing is False
        assert len(batch_response.results) == 3
        
        # Verify all queries succeeded
        for i, result in enumerate(batch_response.results):
            assert result.success is True
            assert result.query == f"Query {i+1}"
            assert result.result.answer == f"Answer {i}"
        
        # Verify summary statistics
        assert batch_response.summary["success_rate"] == 1.0
        assert batch_response.total_cost == 0.003  # 3 * 0.001
        assert batch_response.average_cost_per_query == 0.001
        
        # Verify all queries were processed
        assert service.process_unified_query.call_count == 3

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_batch_query_processing_parallel(self, mock_gateway_for_batch):
        """Test batch query processing in parallel mode."""
        service = mock_gateway_for_batch
        
        # Mock responses with different processing times
        async def mock_query_processing(request):
            # Simulate variable processing times
            await asyncio.sleep(0.1)
            return UnifiedQueryResponse(
                answer=f"Parallel answer for: {request.query}",
                sources=[],
                complexity="medium", 
                confidence=0.85,
                cost=CostBreakdown(model_used="parallel", total_cost=0.002),
                metrics=ProcessingMetrics(total_time=0.1),
                query_id=str(uuid.uuid4()),
                session_id=request.session_id,
                strategy_used="parallel",
                fallback_used=False,
                warnings=[]
            )
        
        service.process_unified_query.side_effect = mock_query_processing
        
        # Create batch request with parallel processing
        options = QueryOptions(strategy="fast")
        batch_request = BatchQueryRequest(
            queries=["Parallel Query 1", "Parallel Query 2", "Parallel Query 3", "Parallel Query 4"],
            parallel_processing=True,
            max_parallel=2,  # Limit concurrency
            options=options,
            session_id="parallel_session"
        )
        
        # Measure processing time
        start_time = time.time()
        batch_response = await service.process_batch_queries(batch_request)
        processing_time = time.time() - start_time
        
        # Verify batch response
        assert batch_response.total_queries == 4
        assert batch_response.successful_queries == 4
        assert batch_response.parallel_processing is True
        
        # Should be faster than sequential (4 queries * 0.1s = 0.4s, but parallel should be ~0.2s)
        assert processing_time < 0.3
        
        # Verify all results
        for result in batch_response.results:
            assert result.success is True
            assert "Parallel answer for:" in result.result.answer

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_batch_query_processing_with_failures(self, mock_gateway_for_batch):
        """Test batch processing with some query failures."""
        service = mock_gateway_for_batch
        
        # Mock mixed success/failure responses
        def mock_query_side_effect(request):
            if "fail" in request.query.lower():
                raise Exception(f"Processing failed for: {request.query}")
            else:
                return UnifiedQueryResponse(
                    answer=f"Success: {request.query}",
                    sources=[],
                    complexity="simple",
                    confidence=0.9,
                    cost=CostBreakdown(model_used="test", total_cost=0.001),
                    metrics=ProcessingMetrics(total_time=0.5),
                    query_id=str(uuid.uuid4()),
                    session_id=request.session_id,
                    strategy_used="test",
                    fallback_used=False,
                    warnings=[]
                )
        
        service.process_unified_query.side_effect = mock_query_side_effect
        
        # Create batch with some failing queries
        options = QueryOptions(strategy="test")
        batch_request = BatchQueryRequest(
            queries=["Success Query 1", "FAIL Query", "Success Query 2", "Another FAIL"],
            parallel_processing=False,
            options=options,
            session_id="mixed_batch"
        )
        
        # Process batch
        batch_response = await service.process_batch_queries(batch_request)
        
        # Verify mixed results
        assert batch_response.total_queries == 4
        assert batch_response.successful_queries == 2
        assert batch_response.failed_queries == 2
        
        # Verify individual results
        successful_results = [r for r in batch_response.results if r.success]
        failed_results = [r for r in batch_response.results if not r.success]
        
        assert len(successful_results) == 2
        assert len(failed_results) == 2
        
        # Check successful results
        for result in successful_results:
            assert "Success:" in result.result.answer
            assert result.error is None
        
        # Check failed results
        for result in failed_results:
            assert result.result is None
            assert "Processing failed" in result.error
            assert result.error_code == "Exception"
        
        # Verify summary statistics
        assert batch_response.summary["success_rate"] == 0.5  # 2/4
        assert batch_response.total_cost == 0.002  # Only successful queries contribute
        assert batch_response.average_cost_per_query == 0.001

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    def test_complexity_distribution_calculation(self, mock_gateway_for_batch):
        """Test complexity distribution calculation for batch results."""
        service = mock_gateway_for_batch
        
        # Create mock successful results with different complexities
        successful_results = [
            BatchQueryResult(
                index=0, query="Q1", success=True,
                result=UnifiedQueryResponse(
                    answer="A1", sources=[], complexity="simple", confidence=0.8,
                    cost=CostBreakdown(model_used="test", total_cost=0.001),
                    metrics=ProcessingMetrics(total_time=1.0),
                    query_id="1", session_id="test", strategy_used="test",
                    fallback_used=False, warnings=[]
                )
            ),
            BatchQueryResult(
                index=1, query="Q2", success=True,
                result=UnifiedQueryResponse(
                    answer="A2", sources=[], complexity="medium", confidence=0.8,
                    cost=CostBreakdown(model_used="test", total_cost=0.002),
                    metrics=ProcessingMetrics(total_time=1.5),
                    query_id="2", session_id="test", strategy_used="test",
                    fallback_used=False, warnings=[]
                )
            ),
            BatchQueryResult(
                index=2, query="Q3", success=True,
                result=UnifiedQueryResponse(
                    answer="A3", sources=[], complexity="complex", confidence=0.7,
                    cost=CostBreakdown(model_used="test", total_cost=0.005),
                    metrics=ProcessingMetrics(total_time=2.0),
                    query_id="3", session_id="test", strategy_used="test",
                    fallback_used=False, warnings=[]
                )
            ),
            BatchQueryResult(
                index=3, query="Q4", success=True,
                result=UnifiedQueryResponse(
                    answer="A4", sources=[], complexity="simple", confidence=0.9,
                    cost=CostBreakdown(model_used="test", total_cost=0.001),
                    metrics=ProcessingMetrics(total_time=0.8),
                    query_id="4", session_id="test", strategy_used="test",
                    fallback_used=False, warnings=[]
                )
            )
        ]
        
        # Test complexity distribution calculation
        distribution = service._calculate_complexity_distribution(successful_results)
        
        assert distribution["simple"] == 2
        assert distribution["medium"] == 1
        assert distribution["complex"] == 1
        assert distribution["unknown"] == 0


class TestGatewayServiceHealthAndStatus:
    """Test gateway service health monitoring and status reporting."""

    @pytest.fixture
    def mock_gateway_with_status(self, mock_settings):
        """Create gateway with mocked clients for status testing."""
        service = APIGatewayService(settings=mock_settings)
        
        # Mock service clients
        service.query_analyzer = AsyncMock()
        service.generator = AsyncMock() 
        service.retriever = AsyncMock()
        service.cache = AsyncMock()
        service.analytics = AsyncMock()
        
        # Add endpoint attributes for status reporting
        for client_name, client in [
            ("query_analyzer", service.query_analyzer),
            ("generator", service.generator),
            ("retriever", service.retriever),
            ("cache", service.cache),
            ("analytics", service.analytics)
        ]:
            client.endpoint = Mock()
            client.endpoint.url = f"http://localhost:800{hash(client_name) % 10}"
        
        service._initialize_circuit_breakers()
        return service

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_gateway_status_all_services_healthy(self, mock_gateway_with_status):
        """Test gateway status when all services are healthy."""
        service = mock_gateway_with_status
        
        # Mock all services as healthy
        service.query_analyzer.health_check.return_value = True
        service.generator.health_check.return_value = True
        service.retriever.health_check.return_value = True
        service.cache.health_check.return_value = True
        service.analytics.health_check.return_value = True
        
        # Mock cache statistics
        service.cache.get_cache_statistics.return_value = {
            "hit_rate": 0.75,
            "total_keys": 1500
        }
        
        # Set some service metrics
        service.requests_processed = 1000
        service.total_response_time = 1500.0  # 1.5s average
        service.error_count = 25
        
        # Get status
        status = await service.get_gateway_status()
        
        # Verify overall status
        assert isinstance(status, GatewayStatusResponse)
        assert status.status == "healthy"
        assert status.healthy_services == 5
        assert status.total_services == 5
        assert status.requests_processed == 1000
        assert status.average_response_time == 1.5
        assert status.error_rate == 2.5  # 25/1000 * 100
        assert status.cache_hit_rate == 0.75
        assert status.cache_size == 1500
        
        # Verify service statuses
        assert len(status.services) == 5
        for service_status in status.services:
            assert service_status.status == "healthy"
            assert service_status.response_time > 0
            assert service_status.error is None
        
        # Verify circuit breaker states
        for service_name in ["query-analyzer", "generator", "retriever", "cache", "analytics"]:
            assert service_name in status.circuit_breakers
            assert status.circuit_breakers[service_name] == "closed"

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_gateway_status_with_service_failures(self, mock_gateway_with_status):
        """Test gateway status when some services are unhealthy."""
        service = mock_gateway_with_status
        
        # Mock mixed service health
        service.query_analyzer.health_check.return_value = True
        service.generator.health_check.side_effect = Exception("Generator service down")
        service.retriever.health_check.return_value = False  # Unhealthy
        service.cache.health_check.return_value = True
        service.analytics.health_check.return_value = True
        
        # Mock cache stats failure
        service.cache.get_cache_statistics.side_effect = Exception("Cache stats unavailable")
        
        # Get status
        status = await service.get_gateway_status()
        
        # Verify degraded status
        assert status.status == "degraded"  # Not all services healthy
        assert status.healthy_services == 3  # analyzer, cache, analytics
        assert status.total_services == 5
        
        # Verify individual service statuses
        service_status_by_name = {s.name: s for s in status.services}
        
        assert service_status_by_name["query-analyzer"].status == "healthy"
        assert service_status_by_name["generator"].status == "error"
        assert "Generator service down" in service_status_by_name["generator"].error
        assert service_status_by_name["retriever"].status == "unhealthy"
        assert service_status_by_name["cache"].status == "healthy"
        assert service_status_by_name["analytics"].status == "healthy"
        
        # Cache metrics should be None due to failure
        assert status.cache_hit_rate is None
        assert status.cache_size is None

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_get_available_models_success(self, mock_gateway_with_status):
        """Test getting available models from generator service."""
        service = mock_gateway_with_status
        
        # Mock generator service response
        generator_models_response = {
            "models": [
                {
                    "id": "openai/gpt-4",
                    "name": "GPT-4",
                    "provider": "openai",
                    "cost_per_token": 0.00003,
                    "available": True,
                    "capabilities": ["text-generation", "reasoning"]
                },
                {
                    "id": "mistral/mixtral-8x7b",
                    "name": "Mixtral 8x7B",
                    "provider": "mistral",
                    "cost_per_token": 0.0000007,
                    "available": True,
                    "capabilities": ["text-generation", "code"]
                },
                {
                    "id": "ollama/llama3.2:3b",
                    "name": "Llama 3.2 3B",
                    "provider": "ollama",
                    "cost_per_token": 0.0,
                    "available": False,  # Currently unavailable
                    "capabilities": ["text-generation"]
                }
            ]
        }
        
        service.generator.get_available_models.return_value = generator_models_response
        
        # Get available models
        models_response = await service.get_available_models()
        
        # Verify response
        assert isinstance(models_response, AvailableModelsResponse)
        assert models_response.total_models == 3
        assert models_response.available_models == 2  # Only 2 are available
        assert set(models_response.providers) == {"openai", "mistral", "ollama"}
        
        # Verify model details
        assert len(models_response.models) == 3
        
        # Find specific models
        gpt4_model = next(m for m in models_response.models if m.id == "openai/gpt-4")
        assert gpt4_model.name == "GPT-4"
        assert gpt4_model.provider == "openai"
        assert gpt4_model.available is True
        assert gpt4_model.type == "generative"  # Should be added by gateway
        
        llama_model = next(m for m in models_response.models if m.id == "ollama/llama3.2:3b")
        assert llama_model.available is False

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_get_available_models_failure(self, mock_gateway_with_status):
        """Test handling of generator service failure when getting models."""
        service = mock_gateway_with_status
        
        # Mock generator service failure
        service.generator.get_available_models.side_effect = Exception("Generator service unavailable")
        
        # Should raise exception
        with pytest.raises(Exception, match="Generator service unavailable"):
            await service.get_available_models()

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR}")
    @pytest.mark.asyncio
    async def test_gateway_service_close_cleanup(self, mock_gateway_with_status):
        """Test proper cleanup when closing gateway service."""
        service = mock_gateway_with_status
        
        # Mock client close methods
        for client in [service.query_analyzer, service.generator, service.retriever, 
                      service.cache, service.analytics]:
            client.close = AsyncMock()
        
        # Make one client close fail
        service.generator.close.side_effect = Exception("Close failed")
        
        # Close service (should not raise exception)
        await service.close()
        
        # Verify all clients had close called
        service.query_analyzer.close.assert_called_once()
        service.generator.close.assert_called_once()
        service.retriever.close.assert_called_once()
        service.cache.close.assert_called_once()
        service.analytics.close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])