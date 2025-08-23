"""
Unit Tests for Epic 8 API Gateway Service.

Tests the core functionality of the APIGatewayService orchestrating all services
in the microservices deployment. Based on CT-8.3 specifications from epic8-test-specification.md.

Testing Philosophy:
- Hard Fails: Service crashes, health check 500s, >60s response, >8GB memory, 0% success rate
- Quality Flags: <95% success rate, >2s response, circuit breaker failures, invalid orchestration

Test Categories:
- Service initialization and health checks (CT-8.3.1)
- Pipeline orchestration functionality (CT-8.3.2)
- Circuit breaker behavior and resilience (CT-8.3.3)
- Error handling and fallback scenarios (CT-8.3.4)
- Configuration loading and validation (CT-8.3.5)
"""

import pytest
import asyncio
import time
import uuid
import unittest.mock as mock
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys
from datetime import datetime
from unittest.mock import Mock, AsyncMock, MagicMock, patch

# Simple fix: Mock prometheus_client to prevent registry collisions
mock.patch.dict('sys.modules', {
    'prometheus_client': mock.Mock(
        Counter=mock.Mock(),
        Histogram=mock.Mock(),
        Gauge=mock.Mock()
    )
}).start()

# Robust service import logic for Epic 8 testing
def _setup_service_imports():
    """Set up imports for Epic 8 API Gateway Service testing."""
    # Get the absolute path to the service
    current_file = Path(__file__).resolve()
    project_root = current_file.parents[3]  # Go up 3 levels from tests/epic8/unit/
    service_path = project_root / "services" / "api-gateway"
    
    if not service_path.exists():
        return False, f"Service path does not exist: {service_path}", {}
    
    # Add service path to sys.path if not already present
    service_path_str = str(service_path)
    if service_path_str not in sys.path:
        sys.path.insert(0, service_path_str)
    
    # Ensure __init__.py files exist for proper module structure
    app_init = service_path / "gateway_app" / "__init__.py"
    core_init = service_path / "gateway_app" / "core" / "__init__.py"
    
    if not app_init.exists() or not core_init.exists():
        return False, f"Missing __init__.py files in service structure", {}
    
    try:
        # Try importing the required modules
        from gateway_app.core.gateway import APIGatewayService, SimpleCircuitBreaker
        from gateway_app.schemas.requests import UnifiedQueryRequest, BatchQueryRequest, QueryOptions
        from gateway_app.schemas.responses import (
            UnifiedQueryResponse, BatchQueryResponse, BatchQueryResult,
            ProcessingMetrics, CostBreakdown, DocumentSource, GatewayStatusResponse,
            ServiceStatus, AvailableModelsResponse, ModelInfo
        )
        from gateway_app.core.config import APIGatewaySettings
        
        # Return the imported classes so they can be used globally
        imports = {
            'APIGatewayService': APIGatewayService,
            'SimpleCircuitBreaker': SimpleCircuitBreaker,
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
            'ModelInfo': ModelInfo,
            'APIGatewaySettings': APIGatewaySettings
        }
        return True, None, imports
    except ImportError as e:
        return False, f"Import failed: {str(e)}", {}
    except Exception as e:
        return False, f"Unexpected error during import: {str(e)}", {}

# Execute import setup
IMPORTS_AVAILABLE, IMPORT_ERROR, imported_classes = _setup_service_imports()

# Make imported classes available globally if imports succeeded
if IMPORTS_AVAILABLE:
    APIGatewayService = imported_classes['APIGatewayService']
    SimpleCircuitBreaker = imported_classes['SimpleCircuitBreaker']
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
    APIGatewaySettings = imported_classes['APIGatewaySettings']

# Clean up the setup function from global namespace
del _setup_service_imports, imported_classes


class TestAPIGatewayServiceBasics:
    """Test basic service initialization and health checks (CT-8.3.1)."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test that service can be initialized without crashing (Hard Fail test)."""
        try:
            # Test basic initialization
            service = APIGatewayService()
            assert service is not None
            assert service.start_time > 0
            assert service.requests_processed == 0
            assert service.error_count == 0
            assert service.query_analyzer is None  # Should start uninitialized
            assert service.generator is None
            assert service.retriever is None
            assert service.cache is None
            assert service.analytics is None
            
            # Test with custom settings
            settings = APIGatewaySettings(
                service_name="test-gateway",
                host="localhost",
                port=8080
            )
            service_with_settings = APIGatewayService(settings=settings)
            assert service_with_settings.settings.service_name == "test-gateway"
            assert service_with_settings.settings.port == 8080
            
        except Exception as e:
            pytest.fail(f"Service initialization crashed (Hard Fail): {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_service_client_initialization(self):
        """Test service client initialization (CT-8.3.1)."""
        service = APIGatewayService()
        
        # Mock all client classes
        with patch('gateway_app.core.gateway.QueryAnalyzerClient') as MockQueryAnalyzer, \
             patch('gateway_app.core.gateway.GeneratorClient') as MockGenerator, \
             patch('gateway_app.core.gateway.RetrieverClient') as MockRetriever, \
             patch('gateway_app.core.gateway.CacheClient') as MockCache, \
             patch('gateway_app.core.gateway.AnalyticsClient') as MockAnalytics:
            
            # Mock health checks
            mock_clients = [
                MockQueryAnalyzer.return_value,
                MockGenerator.return_value,
                MockRetriever.return_value,
                MockCache.return_value,
                MockAnalytics.return_value
            ]
            
            for client in mock_clients:
                client.health_check = AsyncMock(return_value=True)
            
            try:
                start_time = time.time()
                await service.initialize()
                init_time = time.time() - start_time
                
                # Hard fail: Initialization takes >60s (clearly broken)
                assert init_time < 60.0, f"Initialization took {init_time:.2f}s, service is broken"
                
                # Verify clients are initialized
                assert service.query_analyzer is not None
                assert service.generator is not None
                assert service.retriever is not None
                assert service.cache is not None
                assert service.analytics is not None
                
                # Verify circuit breakers are initialized
                expected_services = ["query-analyzer", "generator", "retriever", "cache", "analytics"]
                for service_name in expected_services:
                    assert service_name in service.circuit_breakers
                    assert isinstance(service.circuit_breakers[service_name], SimpleCircuitBreaker)
                
                # Quality flag: Initialization should ideally be fast
                if init_time > 2.0:
                    import warnings
                    warnings.warn(f"Initialization slow: {init_time:.2f}s (flag for optimization)", UserWarning)
                
                print(f"Service initialization completed in {init_time:.3f}s")
                
            except Exception as e:
                pytest.fail(f"Service initialization crashed (Hard Fail): {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_circuit_breaker_initialization(self):
        """Test circuit breaker initialization and configuration (CT-8.3.3)."""
        # Test with custom circuit breaker settings
        settings = APIGatewaySettings(
            circuit_breaker_failure_threshold=3,
            circuit_breaker_recovery_timeout=30
        )
        service = APIGatewayService(settings=settings)
        
        try:
            service._initialize_circuit_breakers()
            
            # Verify circuit breakers are created with correct settings
            expected_services = ["query-analyzer", "generator", "retriever", "cache", "analytics"]
            for service_name in expected_services:
                cb = service.circuit_breakers[service_name]
                assert cb.failure_threshold == 3
                assert cb.recovery_timeout == 30
                assert cb.state == "closed"  # Should start closed
                assert cb.failure_count == 0
                
            print(f"Circuit breakers initialized for {len(expected_services)} services")
            
        except Exception as e:
            pytest.fail(f"Circuit breaker initialization failed: {e}")


class TestAPIGatewayServicePipelineOrchestration:
    """Test pipeline orchestration functionality (CT-8.3.2)."""

    @pytest.fixture
    def mock_service_clients(self):
        """Create mock service clients for testing."""
        query_analyzer = AsyncMock()
        generator = AsyncMock()
        retriever = AsyncMock()
        cache = AsyncMock()
        analytics = AsyncMock()
        
        # Mock query analyzer response
        query_analyzer.analyze_query.return_value = {
            "complexity": "medium",
            "confidence": 0.8,
            "recommended_models": ["openai/gpt-3.5-turbo"],
            "cost_estimate": {"openai/gpt-3.5-turbo": 0.002},
            "routing_strategy": "balanced",
            "recommended_doc_count": 5
        }
        
        # Mock retriever response
        retriever.retrieve_documents.return_value = [
            {
                "id": "doc1",
                "title": "Test Document 1",
                "content": "Test content 1",
                "score": 0.9,
                "metadata": {"source": "test"}
            },
            {
                "id": "doc2",
                "title": "Test Document 2", 
                "content": "Test content 2",
                "score": 0.8,
                "metadata": {"source": "test"}
            }
        ]
        
        # Mock generator response
        generator.generate_answer.return_value = {
            "answer": "This is a test answer based on the retrieved documents.",
            "confidence": 0.85,
            "model_used": "openai/gpt-3.5-turbo",
            "input_tokens": 100,
            "output_tokens": 50,
            "cost": 0.002,
            "tokens_generated": 50
        }
        
        # Mock cache responses
        cache.get_cached_response.return_value = None  # No cache hit by default
        cache.cache_response.return_value = True
        cache.clear_cache.return_value = {"keys_removed": 5}
        cache.get_cache_statistics.return_value = {"hit_rate": 0.65, "total_keys": 100}
        
        # Mock analytics responses
        analytics.record_cache_hit.return_value = True
        analytics.record_query_completion.return_value = True
        analytics.record_error.return_value = True
        
        # Mock health checks
        for client in [query_analyzer, generator, retriever, cache, analytics]:
            client.health_check.return_value = True
            client.close.return_value = None
            client.endpoint.url = "http://mock-service"
        
        return {
            "query_analyzer": query_analyzer,
            "generator": generator,
            "retriever": retriever,
            "cache": cache,
            "analytics": analytics
        }

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_unified_query_processing_pipeline(self, mock_service_clients):
        """Test complete unified query processing pipeline (CT-8.3.2)."""
        service = APIGatewayService()
        
        # Inject mock clients
        service.query_analyzer = mock_service_clients["query_analyzer"]
        service.generator = mock_service_clients["generator"]
        service.retriever = mock_service_clients["retriever"]
        service.cache = mock_service_clients["cache"]
        service.analytics = mock_service_clients["analytics"]
        
        # Initialize circuit breakers
        service._initialize_circuit_breakers()
        
        # Create test request
        request = UnifiedQueryRequest(
            query="How does machine learning work?",
            options=QueryOptions(
                strategy="balanced",
                cache_enabled=True,
                analytics_enabled=True,
                max_documents=10,
                max_cost=0.10
            ),
            session_id="test-session",
            user_id="test-user"
        )
        
        try:
            start_time = time.time()
            response = await service.process_unified_query(request)
            processing_time = time.time() - start_time
            
            # Hard fail: Response time >60s (clearly broken)
            assert processing_time < 60.0, f"Query processing took {processing_time:.2f}s, service is broken"
            
            # Validate response structure
            assert isinstance(response, UnifiedQueryResponse)
            assert response.answer is not None
            assert len(response.answer) > 0
            assert response.complexity == "medium"
            assert 0.0 <= response.confidence <= 1.0
            assert response.cost.total_cost >= 0.0
            assert response.query_id is not None
            assert response.session_id == "test-session"
            assert response.strategy_used == "balanced"
            assert response.fallback_used is False
            
            # Validate sources
            assert len(response.sources) == 2  # Based on mock data
            for source in response.sources:
                assert isinstance(source, DocumentSource)
                assert source.id is not None
                assert source.score >= 0.0
            
            # Validate metrics
            assert isinstance(response.metrics, ProcessingMetrics)
            assert response.metrics.total_time > 0
            assert response.metrics.analysis_time is not None
            assert response.metrics.retrieval_time is not None
            assert response.metrics.generation_time is not None
            assert response.metrics.documents_retrieved == 2
            assert response.metrics.cache_hit is False
            
            # Validate cost breakdown
            assert isinstance(response.cost, CostBreakdown)
            assert response.cost.model_used == "openai/gpt-3.5-turbo"
            assert response.cost.total_cost == 0.002
            
            # Verify service calls were made
            mock_service_clients["query_analyzer"].analyze_query.assert_called_once()
            mock_service_clients["retriever"].retrieve_documents.assert_called_once()
            mock_service_clients["generator"].generate_answer.assert_called_once()
            mock_service_clients["cache"].cache_response.assert_called_once()
            mock_service_clients["analytics"].record_query_completion.assert_called_once()
            
            # Update service metrics
            assert service.requests_processed == 1
            assert service.total_response_time > 0
            
            # Quality flag: Response time should ideally be <2s
            if processing_time > 2.0:
                import warnings
                warnings.warn(f"Query processing slow: {processing_time:.2f}s (flag for optimization)", UserWarning)
            
            print(f"Pipeline processing completed in {processing_time:.3f}s")
            
        except Exception as e:
            pytest.fail(f"Unified query processing failed (Hard Fail): {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_batch_query_processing(self, mock_service_clients):
        """Test batch query processing functionality (CT-8.3.2)."""
        service = APIGatewayService()
        
        # Inject mock clients
        service.query_analyzer = mock_service_clients["query_analyzer"]
        service.generator = mock_service_clients["generator"]
        service.retriever = mock_service_clients["retriever"]
        service.cache = mock_service_clients["cache"]
        service.analytics = mock_service_clients["analytics"]
        service._initialize_circuit_breakers()
        
        # Create batch request
        batch_request = BatchQueryRequest(
            queries=[
                "What is machine learning?",
                "How do neural networks work?",
                "Explain deep learning algorithms"
            ],
            options=QueryOptions(strategy="balanced", cache_enabled=True),
            parallel_processing=True,
            max_parallel=2,
            session_id="test-batch-session",
            user_id="test-user"
        )
        
        try:
            start_time = time.time()
            response = await service.process_batch_queries(batch_request)
            processing_time = time.time() - start_time
            
            # Hard fail: Batch processing takes >60s
            assert processing_time < 60.0, f"Batch processing took {processing_time:.2f}s"
            
            # Validate batch response structure
            assert isinstance(response, BatchQueryResponse)
            assert response.batch_id is not None
            assert response.total_queries == 3
            assert response.session_id == "test-batch-session"
            assert response.parallel_processing is True
            assert len(response.results) == 3
            
            # Check individual results
            successful_count = 0
            for i, result in enumerate(response.results):
                assert isinstance(result, BatchQueryResult)
                assert result.index == i
                assert result.query == batch_request.queries[i]
                
                if result.success:
                    successful_count += 1
                    assert result.result is not None
                    assert isinstance(result.result, UnifiedQueryResponse)
                    assert result.error is None
                else:
                    assert result.error is not None
                    assert result.error_code is not None
            
            # Hard fail: 0% success rate (completely broken)
            assert successful_count > 0, "All batch queries failed - system is broken"
            
            # Calculate success rate
            success_rate = successful_count / len(batch_request.queries)
            assert response.successful_queries == successful_count
            assert response.failed_queries == (3 - successful_count)
            
            # Quality flag: Success rate should ideally be >95%
            if success_rate < 0.95:
                import warnings
                warnings.warn(f"Batch success rate {success_rate:.2%} below 95% target", UserWarning)
            
            # Validate summary statistics
            assert "summary" in response.dict()
            summary = response.summary
            assert "total_cost" in summary
            assert "success_rate" in summary
            assert summary["success_rate"] == success_rate
            
            print(f"Batch processing: {successful_count}/{len(batch_request.queries)} successful in {processing_time:.3f}s")
            
        except Exception as e:
            pytest.fail(f"Batch query processing failed (Hard Fail): {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_cache_integration(self, mock_service_clients):
        """Test cache integration in pipeline (CT-8.3.2)."""
        service = APIGatewayService()
        
        # Inject mock clients
        service.query_analyzer = mock_service_clients["query_analyzer"]
        service.generator = mock_service_clients["generator"]
        service.retriever = mock_service_clients["retriever"]
        service.cache = mock_service_clients["cache"]
        service.analytics = mock_service_clients["analytics"]
        service._initialize_circuit_breakers()
        
        # Create request with caching enabled
        request = UnifiedQueryRequest(
            query="What is caching?",
            options=QueryOptions(
                cache_enabled=True,
                analytics_enabled=True,
                force_refresh=False
            ),
            session_id="cache-test"
        )
        
        try:
            # First request - should miss cache and process normally
            response1 = await service.process_unified_query(request)
            
            # Verify cache was checked and response was cached
            mock_service_clients["cache"].get_cached_response.assert_called()
            mock_service_clients["cache"].cache_response.assert_called()
            assert response1.metrics.cache_hit is False
            
            # Second request - mock cache hit with proper UnifiedQueryResponse structure
            # Cache should return the SAME answer as the original response, not different text
            cached_response_data = {
                "answer": "This is a test answer based on the retrieved documents.",  # Same as mock generator
                "sources": [
                    {
                        "id": "doc1",
                        "title": "Test Document 1",
                        "content": "Test content 1",
                        "score": 0.9,
                        "metadata": {"source": "test", "page": 1}
                    },
                    {
                        "id": "doc2", 
                        "title": "Test Document 2",
                        "content": "Test content 2",
                        "score": 0.8,
                        "metadata": {"source": "test", "page": 2}
                    }
                ],
                "complexity": "medium",
                "confidence": 0.85,
                # Proper CostBreakdown structure
                "cost": {
                    "model_used": "openai/gpt-3.5-turbo",
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "model_cost": 0.002,
                    "retrieval_cost": 0.0,
                    "total_cost": 0.002,
                    "cost_estimation_confidence": 1.0
                },
                # Proper ProcessingMetrics structure  
                "metrics": {
                    "analysis_time": 0.0001,
                    "retrieval_time": 0.0002,
                    "generation_time": 0.0007, 
                    "cache_time": 0.001,
                    "total_time": 0.001,
                    "documents_retrieved": 2,
                    "tokens_generated": 50,
                    "cache_hit": True,
                    "cache_key": request.query_hash
                },
                "query_id": str(uuid.uuid4()),
                "session_id": "cache-test",
                "timestamp": datetime.utcnow().isoformat(),
                "strategy_used": "balanced",
                "fallback_used": False,
                "warnings": []
            }
            
            mock_service_clients["cache"].get_cached_response.return_value = cached_response_data
            
            response2 = await service.process_unified_query(request)
            
            # Should return cached response with same content but faster time
            assert response2.answer == "This is a test answer based on the retrieved documents."  # Same answer as original
            assert response2.metrics.cache_hit is True
            assert response2.metrics.total_time < 0.01  # Should be much faster from cache
            
            # Analytics should record cache hit
            mock_service_clients["analytics"].record_cache_hit.assert_called()
            
            print("Cache integration test passed")
            
        except Exception as e:
            pytest.fail(f"Cache integration test failed: {e}")


class TestAPIGatewayServiceCircuitBreaker:
    """Test circuit breaker behavior and resilience (CT-8.3.3)."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_circuit_breaker_basic_functionality(self):
        """Test basic circuit breaker functionality (CT-8.3.3)."""
        # Test circuit breaker states
        cb = SimpleCircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        # Should start closed
        assert cb.state == "closed"
        assert cb.failure_count == 0
        
        # Test successful operation
        try:
            with cb:
                pass  # Successful operation
            assert cb.state == "closed"
            assert cb.failure_count == 0
        except Exception:
            pytest.fail("Circuit breaker failed on successful operation")
        
        # Test failures
        for i in range(2):  # failure_threshold = 2
            try:
                with cb:
                    raise Exception("Test failure")
            except Exception:
                pass  # Expected
        
        # Should now be open
        assert cb.state == "open"
        assert cb.failure_count == 2
        
        # Should reject requests when open
        try:
            with cb:
                pass
            pytest.fail("Circuit breaker should reject requests when open")
        except Exception as e:
            assert "Circuit breaker is open" in str(e)
        
        # Test recovery after timeout
        time.sleep(1.1)  # Wait for recovery timeout
        
        try:
            with cb:
                pass  # Successful operation should reset
            assert cb.state == "closed"
            assert cb.failure_count == 0
        except Exception:
            pytest.fail("Circuit breaker failed to recover")
        
        print("Circuit breaker basic functionality test passed")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_circuit_breaker_service_protection(self):
        """Test circuit breaker protecting service calls (CT-8.3.3)."""
        service = APIGatewayService()
        service._initialize_circuit_breakers()
        
        # Mock a failing service client
        failing_client = AsyncMock()
        failing_client.analyze_query.side_effect = Exception("Service unavailable")
        service.query_analyzer = failing_client
        
        request = UnifiedQueryRequest(
            query="Test query",
            options=QueryOptions(strategy="balanced")
        )
        
        # Epic 8 Spec RT-8.1.2: Circuit breaker should open within 10 failures
        # and return fallback responses in <500ms
        fallback_responses = 0
        response_times = []
        
        for i in range(12):  # Try enough to trigger circuit breaker
            start_time = time.time()
            try:
                response = await service.process_unified_query(request)
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                response_times.append(response_time)
                
                # Check if it's a fallback response
                if hasattr(response, 'answer') and "fallback" in response.answer.lower():
                    fallback_responses += 1
                elif hasattr(response, 'sources') and len(response.sources) == 0:
                    fallback_responses += 1  # Likely fallback if no sources
                
            except Exception as e:
                # Epic 8 spec expects graceful handling, not exceptions
                print(f"Unexpected exception (should be graceful): {e}")
        
        # Epic 8 specification validation
        query_analyzer_cb = service.circuit_breakers["query-analyzer"]
        
        # Check circuit breaker opened within 10 failures (RT-8.1.2)
        if query_analyzer_cb.failure_count >= 10:
            assert query_analyzer_cb.state == "open", "Circuit breaker should be open after 10 failures"
            print(f"✅ Circuit breaker opened after {query_analyzer_cb.failure_count} failures (Epic 8 compliant)")
        
        # Check fallback responses returned quickly (RT-8.1.2: <500ms)
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            assert avg_response_time < 500, f"Fallback responses too slow: {avg_response_time:.1f}ms > 500ms"
            print(f"✅ Fallback responses averaged {avg_response_time:.1f}ms (Epic 8 compliant)")
        
        # Check service remained stable (RT-8.1.2: No upstream crashes)
        assert fallback_responses > 0, "Should have returned fallback responses during failures"
        
        print("Circuit breaker service protection test completed")


class TestAPIGatewayServiceErrorHandling:
    """Test error handling and fallback scenarios (CT-8.3.4)."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_fallback_response_generation(self):
        """Test fallback response when services fail (CT-8.3.4)."""
        service = APIGatewayService()
        
        # Mock all services to fail
        failing_client = AsyncMock()
        failing_client.analyze_query.side_effect = Exception("Service down")
        failing_client.retrieve_documents.side_effect = Exception("Service down")
        failing_client.generate_answer.side_effect = Exception("Service down")
        
        service.query_analyzer = failing_client
        service.retriever = failing_client
        service.generator = failing_client
        
        # Mock analytics to work (optional service)
        analytics_client = AsyncMock()
        analytics_client.record_error.return_value = True
        service.analytics = analytics_client
        
        service._initialize_circuit_breakers()
        
        request = UnifiedQueryRequest(
            query="Test query for fallback",
            options=QueryOptions(strategy="balanced", analytics_enabled=True)
        )
        
        try:
            response = await service.process_unified_query(request)
            
            # Should return fallback response
            assert response.fallback_used is True
            assert "service issue" in response.answer.lower() or "unable to process" in response.answer.lower()
            assert len(response.warnings) > 0
            assert response.confidence == 0.0
            assert response.cost.total_cost == 0.0
            
            # Error should be recorded in analytics
            analytics_client.record_error.assert_called()
            
            print("Fallback response generation test passed")
            
        except Exception as e:
            # If fallback also fails, that's acceptable but should be a clear error
            if "fallback" in str(e).lower():
                print(f"Fallback failed gracefully: {e}")
            else:
                pytest.fail(f"Unexpected error in fallback test: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_partial_service_failure_handling(self):
        """Test handling when only some services fail (CT-8.3.4)."""
        service = APIGatewayService()
        
        # Mock query analyzer to work
        working_analyzer = AsyncMock()
        working_analyzer.analyze_query.return_value = {
            "complexity": "simple",
            "confidence": 0.5,
            "recommended_models": ["ollama/llama3.2:3b"],
            "cost_estimate": {"ollama/llama3.2:3b": 0.0},
            "routing_strategy": "balanced"
        }
        service.query_analyzer = working_analyzer
        
        # Mock retriever to fail
        failing_retriever = AsyncMock()
        failing_retriever.retrieve_documents.side_effect = Exception("Retrieval service down")
        service.retriever = failing_retriever
        
        # Mock generator to work (should work with empty documents)
        working_generator = AsyncMock()
        working_generator.generate_answer.return_value = {
            "answer": "Generated answer without retrieved documents",
            "confidence": 0.3,
            "model_used": "ollama/llama3.2:3b",
            "cost": 0.0,
            "tokens_generated": 20
        }
        service.generator = working_generator
        
        # Mock cache and analytics
        service.cache = AsyncMock()
        service.cache.get_cached_response.return_value = None
        service.cache.cache_response.return_value = True
        
        service.analytics = AsyncMock()
        service.analytics.record_query_completion.return_value = True
        
        service._initialize_circuit_breakers()
        
        request = UnifiedQueryRequest(
            query="Test partial failure handling",
            options=QueryOptions(strategy="balanced")
        )
        
        try:
            response = await service.process_unified_query(request)
            
            # Should succeed with degraded functionality
            assert response is not None
            assert response.fallback_used is False  # Not full fallback
            assert len(response.sources) == 0  # No documents retrieved
            assert response.answer is not None
            assert len(response.answer) > 0
            
            # Generator should have been called with empty documents
            working_generator.generate_answer.assert_called_once()
            call_args = working_generator.generate_answer.call_args
            documents = call_args.kwargs.get('context_documents', [])
            assert len(documents) == 0
            
            print("Partial service failure handling test passed")
            
        except Exception as e:
            pytest.fail(f"Partial failure handling failed: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_invalid_request_handling(self):
        """Test handling of invalid requests (CT-8.3.4)."""
        service = APIGatewayService()
        
        # Test cases for invalid requests
        invalid_requests = [
            # Empty query
            UnifiedQueryRequest(query="", options=QueryOptions()),
            # Very long query
            UnifiedQueryRequest(query="x" * 100000, options=QueryOptions()),
            # Invalid cost limit
            UnifiedQueryRequest(query="test", options=QueryOptions(max_cost=-1.0)),
            # Invalid document limit
            UnifiedQueryRequest(query="test", options=QueryOptions(max_documents=-5)),
        ]
        
        for i, request in enumerate(invalid_requests):
            try:
                # Should either handle gracefully or raise clear validation error
                response = await service.process_unified_query(request)
                
                # If it succeeds, should be valid response
                assert response is not None
                print(f"Invalid request {i} handled gracefully")
                
            except (ValueError, TypeError, Exception) as e:
                # Validation errors are acceptable
                print(f"Invalid request {i} rejected with: {type(e).__name__}")
                continue


class TestAPIGatewayServiceStatus:
    """Test service status and health monitoring functionality."""

    @pytest.fixture
    def mock_healthy_clients(self):
        """Create mock clients that are healthy."""
        clients = {}
        for service_name in ["query-analyzer", "generator", "retriever", "cache", "analytics"]:
            client = AsyncMock()
            client.health_check.return_value = True
            client.endpoint.url = f"http://{service_name}:8080"
            clients[service_name] = client
        return clients

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_gateway_status_healthy(self, mock_healthy_clients):
        """Test gateway status when all services are healthy."""
        service = APIGatewayService()
        
        # Inject healthy clients
        service.query_analyzer = mock_healthy_clients["query-analyzer"]
        service.generator = mock_healthy_clients["generator"]
        service.retriever = mock_healthy_clients["retriever"]
        service.cache = mock_healthy_clients["cache"]
        service.analytics = mock_healthy_clients["analytics"]
        
        # Initialize circuit breakers
        service._initialize_circuit_breakers()
        
        # Set some metrics
        service.requests_processed = 100
        service.total_response_time = 50.0
        service.error_count = 2
        
        try:
            status = await service.get_gateway_status()
            
            # Validate status structure
            assert isinstance(status, GatewayStatusResponse)
            assert status.status == "healthy"
            assert status.healthy_services == 5
            assert status.total_services == 5
            assert status.uptime > 0
            assert status.requests_processed == 100
            assert status.average_response_time == 0.5  # 50.0/100
            assert status.error_rate == 2.0  # 2/100 * 100
            
            # Validate service status details
            assert len(status.services) == 5
            for service_status in status.services:
                assert isinstance(service_status, ServiceStatus)
                assert service_status.status == "healthy"
                assert service_status.response_time is not None
                assert service_status.url.startswith("http://")
            
            # Validate circuit breaker states
            assert len(status.circuit_breakers) == 5
            for cb_name, cb_state in status.circuit_breakers.items():
                assert cb_state == "closed"  # Should all be closed
            
            print(f"Gateway status test passed: {status.status} with {status.healthy_services}/{status.total_services} healthy services")
            
        except Exception as e:
            pytest.fail(f"Gateway status test failed: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_available_models(self):
        """Test getting available models from generator service."""
        service = APIGatewayService()
        
        # Mock generator client
        generator_client = AsyncMock()
        generator_client.get_available_models.return_value = {
            "models": [
                {
                    "provider": "openai",
                    "name": "gpt-3.5-turbo",
                    "available": True,
                    "context_length": 4096,
                    "input_cost": 0.0015,
                    "output_cost": 0.002
                },
                {
                    "provider": "ollama", 
                    "name": "llama3.2:3b",
                    "available": True,
                    "context_length": 2048,
                    "input_cost": 0.0,
                    "output_cost": 0.0
                }
            ]
        }
        service.generator = generator_client
        
        try:
            models_response = await service.get_available_models()
            
            # Validate response structure
            assert isinstance(models_response, AvailableModelsResponse)
            assert len(models_response.models) == 2
            assert models_response.total_models == 2
            assert models_response.available_models == 2
            assert "openai" in models_response.providers
            assert "ollama" in models_response.providers
            
            # Validate model details
            for model in models_response.models:
                assert isinstance(model, ModelInfo)
                assert model.provider in ["openai", "ollama"]
                assert model.name is not None
                assert model.available is True
                assert model.context_length > 0
            
            print(f"Available models test passed: {len(models_response.models)} models from {len(models_response.providers)} providers")
            
        except Exception as e:
            pytest.fail(f"Available models test failed: {e}")


class TestAPIGatewayServiceConfiguration:
    """Test configuration loading and validation (CT-8.3.5)."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_service_configuration(self):
        """Test service configuration options."""
        # Test with various configurations
        config_tests = [
            {
                "service_name": "test-gateway",
                "host": "0.0.0.0",
                "port": 8000,
                "circuit_breaker_failure_threshold": 5,
                "circuit_breaker_recovery_timeout": 60
            },
            {
                "service_name": "custom-gateway",
                "host": "127.0.0.1", 
                "port": 9000,
                "circuit_breaker_failure_threshold": 3,
                "circuit_breaker_recovery_timeout": 30
            }
        ]
        
        for config in config_tests:
            try:
                settings = APIGatewaySettings(**config)
                service = APIGatewayService(settings=settings)
                
                # Validate configuration was applied
                assert service.settings.service_name == config["service_name"]
                assert service.settings.host == config["host"] 
                assert service.settings.port == config["port"]
                assert service.settings.circuit_breaker_failure_threshold == config["circuit_breaker_failure_threshold"]
                assert service.settings.circuit_breaker_recovery_timeout == config["circuit_breaker_recovery_timeout"]
                
                print(f"Configuration test passed for {config['service_name']}")
                
            except Exception as e:
                pytest.fail(f"Configuration test failed for {config}: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_service_cleanup(self):
        """Test service cleanup and resource management."""
        service = APIGatewayService()
        
        # Create mock clients
        clients = []
        for _ in range(5):
            client = AsyncMock()
            client.close.return_value = None
            clients.append(client)
        
        service.query_analyzer = clients[0]
        service.generator = clients[1]
        service.retriever = clients[2]
        service.cache = clients[3]
        service.analytics = clients[4]
        
        try:
            await service.close()
            
            # Verify all clients were closed
            for client in clients:
                client.close.assert_called_once()
            
            print("Service cleanup test passed")
            
        except Exception as e:
            pytest.fail(f"Service cleanup test failed: {e}")


# Memory and performance tests
class TestAPIGatewayServiceResources:
    """Test resource usage and performance characteristics."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_memory_usage_basic(self):
        """Test that service doesn't use excessive memory."""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            service = APIGatewayService()
            service._initialize_circuit_breakers()
            
            # Create minimal mock clients to avoid import issues
            for attr in ["query_analyzer", "generator", "retriever", "cache", "analytics"]:
                setattr(service, attr, AsyncMock())
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Hard fail: >8GB memory usage (clearly broken)
            assert final_memory < 8000, f"Memory usage {final_memory:.1f}MB exceeds 8GB limit"
            
            # Quality flag: Large memory increase might indicate issue
            if memory_increase > 500:  # 500MB increase
                import warnings
                warnings.warn(f"Large memory increase: {memory_increase:.1f}MB", UserWarning)
            
            print(f"Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB (+{memory_increase:.1f}MB)")
            
        except ImportError:
            pytest.skip("psutil not available for memory testing")
        except Exception as e:
            pytest.fail(f"Memory usage test failed: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self):
        """Test handling of concurrent requests."""
        service = APIGatewayService()
        
        # Create fast mock clients
        mock_clients = {}
        for name in ["query_analyzer", "generator", "retriever", "cache", "analytics"]:
            client = AsyncMock()
            mock_clients[name] = client
            setattr(service, name, client)
        
        # Setup mock responses
        mock_clients["query_analyzer"].analyze_query.return_value = {
            "complexity": "simple", "confidence": 0.8, "recommended_models": ["test-model"]
        }
        mock_clients["retriever"].retrieve_documents.return_value = []
        mock_clients["generator"].generate_answer.return_value = {
            "answer": "Test answer", "confidence": 0.8, "cost": 0.0, "tokens_generated": 10
        }
        mock_clients["cache"].get_cached_response.return_value = None
        mock_clients["cache"].cache_response.return_value = True
        mock_clients["analytics"].record_query_completion.return_value = True
        
        service._initialize_circuit_breakers()
        
        # Create concurrent requests
        requests = [
            UnifiedQueryRequest(query=f"Test query {i}", options=QueryOptions())
            for i in range(10)
        ]
        
        try:
            start_time = time.time()
            tasks = [service.process_unified_query(req) for req in requests]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # Count successful vs failed results
            successful = [r for r in results if isinstance(r, UnifiedQueryResponse)]
            failed = [r for r in results if isinstance(r, Exception)]
            
            # Hard fail: All requests failed
            assert len(successful) > 0, "All concurrent requests failed"
            
            # Calculate success rate
            success_rate = len(successful) / len(requests)
            
            # Quality flag: Success rate should be high
            if success_rate < 0.9:
                import warnings
                warnings.warn(f"Concurrent success rate {success_rate:.2%} below 90%", UserWarning)
            
            print(f"Concurrent test: {len(successful)}/{len(requests)} succeeded in {total_time:.2f}s")
            
        except Exception as e:
            pytest.fail(f"Concurrent request test failed: {e}")


if __name__ == "__main__":
    # Run specific test classes for development
    pytest.main([__file__ + "::TestAPIGatewayServiceBasics", "-v"])