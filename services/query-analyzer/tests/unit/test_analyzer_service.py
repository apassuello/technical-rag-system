"""
Unit tests for QueryAnalyzerService class.

Tests the core business logic of the service wrapper around Epic1QueryAnalyzer.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import time

from analyzer_app.core.analyzer import QueryAnalyzerService
from conftest import (
    validate_response_structure,
    assert_valid_complexity,
    assert_confidence_range,
    assert_processing_time
)


class TestQueryAnalyzerService:
    """Test cases for QueryAnalyzerService."""

    @pytest.mark.asyncio
    async def test_initialization(self, analyzer_config):
        """Test service initialization."""
        service = QueryAnalyzerService(config=analyzer_config)
        
        assert service.config == analyzer_config
        assert service.analyzer is None
        assert not service._initialized
        assert service._initialization_lock is not None

    @pytest.mark.asyncio
    async def test_initialization_with_default_config(self):
        """Test service initialization with default configuration."""
        service = QueryAnalyzerService()
        
        assert service.config == {}
        assert service.analyzer is None
        assert not service._initialized

    @pytest.mark.asyncio
    async def test_lazy_analyzer_initialization(self, mock_epic1_analyzer, analyzer_config):
        """Test that analyzer is initialized lazily on first use."""
        with patch('app.core.analyzer.Epic1QueryAnalyzer', return_value=mock_epic1_analyzer):
            service = QueryAnalyzerService(config=analyzer_config)
            
            # Should not be initialized yet
            assert not service._initialized
            assert service.analyzer is None
            
            # Initialize analyzer
            await service._initialize_analyzer()
            
            # Should now be initialized
            assert service._initialized
            assert service.analyzer is mock_epic1_analyzer

    @pytest.mark.asyncio
    async def test_double_initialization_prevented(self, mock_epic1_analyzer, analyzer_config):
        """Test that analyzer initialization is idempotent."""
        with patch('app.core.analyzer.Epic1QueryAnalyzer', return_value=mock_epic1_analyzer) as mock_class:
            service = QueryAnalyzerService(config=analyzer_config)
            
            # Initialize twice
            await service._initialize_analyzer()
            await service._initialize_analyzer()
            
            # Epic1QueryAnalyzer should only be called once
            mock_class.assert_called_once_with(config=analyzer_config)

    @pytest.mark.asyncio
    async def test_concurrent_initialization(self, mock_epic1_analyzer, analyzer_config):
        """Test that concurrent initialization attempts are handled correctly."""
        with patch('app.core.analyzer.Epic1QueryAnalyzer', return_value=mock_epic1_analyzer) as mock_class:
            service = QueryAnalyzerService(config=analyzer_config)
            
            # Start multiple initialization tasks concurrently
            tasks = [service._initialize_analyzer() for _ in range(5)]
            await asyncio.gather(*tasks)
            
            # Epic1QueryAnalyzer should only be called once
            mock_class.assert_called_once_with(config=analyzer_config)
            assert service._initialized

    @pytest.mark.asyncio
    async def test_initialization_failure(self, analyzer_config):
        """Test handling of initialization failures."""
        error_msg = "Failed to load model"
        
        with patch('app.core.analyzer.Epic1QueryAnalyzer', side_effect=RuntimeError(error_msg)):
            service = QueryAnalyzerService(config=analyzer_config)
            
            # Initialization should fail
            with pytest.raises(RuntimeError, match=error_msg):
                await service._initialize_analyzer()
            
            # Service should remain uninitialized
            assert not service._initialized
            assert service.analyzer is None

    @pytest.mark.asyncio
    async def test_analyze_query_success(self, analyzer_service, sample_queries, expected_response_structure, performance_targets):
        """Test successful query analysis."""
        query = sample_queries["medium"][0]
        
        result = await analyzer_service.analyze_query(query)
        
        # Validate response structure
        validate_response_structure(result, expected_response_structure)
        
        # Validate specific fields
        assert result["query"] == query
        assert_valid_complexity(result["complexity"], performance_targets["valid_complexities"])
        assert_confidence_range(result["confidence"])
        assert_processing_time(result["processing_time"], performance_targets["max_response_time"])
        
        # Validate metadata
        assert "analyzer_version" in result["metadata"]
        assert "timestamp" in result["metadata"]
        assert result["metadata"]["context"] == {}

    @pytest.mark.asyncio
    async def test_analyze_query_with_context(self, analyzer_service, sample_queries):
        """Test query analysis with context."""
        query = sample_queries["simple"][0]
        context = {"user_id": "test123", "session": "abc"}
        
        result = await analyzer_service.analyze_query(query, context=context)
        
        assert result["metadata"]["context"] == context

    @pytest.mark.asyncio
    async def test_analyze_query_not_initialized(self, analyzer_config):
        """Test query analysis when service is not initialized."""
        service = QueryAnalyzerService(config=analyzer_config)
        
        # Mock initialization to fail
        with patch.object(service, '_initialize_analyzer', side_effect=RuntimeError("Init failed")):
            with pytest.raises(RuntimeError, match="Init failed"):
                await service.analyze_query("test query")

    @pytest.mark.asyncio
    async def test_analyze_query_analyzer_none(self, analyzer_config):
        """Test query analysis when analyzer is None after initialization."""
        service = QueryAnalyzerService(config=analyzer_config)
        service._initialized = True  # Fake initialization
        service.analyzer = None  # But analyzer is None
        
        with pytest.raises(RuntimeError, match="Analyzer not initialized"):
            await service.analyze_query("test query")

    @pytest.mark.asyncio
    async def test_analyze_query_epic1_error(self, mock_epic1_analyzer, analyzer_config):
        """Test handling of Epic1QueryAnalyzer errors."""
        error_msg = "Analysis failed"
        mock_epic1_analyzer.analyze_query.side_effect = ValueError(error_msg)
        
        with patch('app.core.analyzer.Epic1QueryAnalyzer', return_value=mock_epic1_analyzer):
            service = QueryAnalyzerService(config=analyzer_config)
            await service._initialize_analyzer()
            
            with pytest.raises(ValueError, match=error_msg):
                await service.analyze_query("test query")

    @pytest.mark.asyncio
    async def test_get_analyzer_status_not_initialized(self, analyzer_config):
        """Test status when analyzer is not initialized."""
        service = QueryAnalyzerService(config=analyzer_config)
        
        status = await service.get_analyzer_status()
        
        assert status["initialized"] is False
        assert status["status"] == "not_initialized"

    @pytest.mark.asyncio
    async def test_get_analyzer_status_healthy(self, analyzer_service):
        """Test status when analyzer is healthy."""
        status = await analyzer_service.get_analyzer_status()
        
        assert status["initialized"] is True
        assert status["status"] == "healthy"
        assert status["analyzer_type"] == "Epic1QueryAnalyzer"
        assert "configuration" in status
        assert "performance" in status
        assert "components" in status
        
        # Check components
        components = status["components"]
        assert components["feature_extractor"] == "healthy"
        assert components["complexity_classifier"] == "healthy"
        assert components["model_recommender"] == "healthy"

    @pytest.mark.asyncio
    async def test_get_analyzer_status_performance_metrics(self, analyzer_service):
        """Test that status includes performance metrics."""
        status = await analyzer_service.get_analyzer_status()
        
        performance = status["performance"]
        assert "average_times" in performance
        assert "total_analyses" in performance
        
        avg_times = performance["average_times"]
        assert "feature_extraction" in avg_times
        assert "complexity_classification" in avg_times
        assert "model_recommendation" in avg_times
        assert "total" in avg_times

    @pytest.mark.asyncio
    async def test_get_analyzer_status_error_handling(self, mock_epic1_analyzer, analyzer_config):
        """Test status error handling."""
        # Mock analyzer to raise exception during status check
        mock_epic1_analyzer.model_recommender = None
        
        with patch('app.core.analyzer.Epic1QueryAnalyzer', return_value=mock_epic1_analyzer):
            service = QueryAnalyzerService(config=analyzer_config)
            await service._initialize_analyzer()
            
            # Should handle error gracefully
            status = await service.get_analyzer_status()
            
            assert status["initialized"] is True
            assert status["status"] == "error"
            assert "error" in status

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, analyzer_config):
        """Test health check initializes analyzer."""
        with patch('app.core.analyzer.Epic1QueryAnalyzer') as mock_class:
            mock_analyzer = Mock()
            mock_analysis = Mock()
            mock_analysis.metadata = {
                'complexity': 'simple',
                'confidence': 0.9
            }
            mock_analyzer.analyze_query.return_value = mock_analysis
            mock_class.return_value = mock_analyzer
            
            service = QueryAnalyzerService(config=analyzer_config)
            
            result = await service.health_check()
            
            assert result is True
            mock_class.assert_called_once_with(config=analyzer_config)

    @pytest.mark.asyncio
    async def test_health_check_success(self, analyzer_service):
        """Test successful health check."""
        result = await analyzer_service.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_invalid_result_format(self, mock_epic1_analyzer, analyzer_config):
        """Test health check with invalid analyzer result."""
        # Mock analyzer to return invalid result
        mock_analysis = Mock()
        mock_analysis.metadata = {
            'complexity': 'invalid',  # Invalid complexity
            'confidence': 0.5
        }
        mock_epic1_analyzer.analyze_query.return_value = mock_analysis
        
        with patch('app.core.analyzer.Epic1QueryAnalyzer', return_value=mock_epic1_analyzer):
            service = QueryAnalyzerService(config=analyzer_config)
            
            result = await service.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_confidence_out_of_range(self, mock_epic1_analyzer, analyzer_config):
        """Test health check with confidence out of range."""
        # Mock analyzer to return invalid confidence
        mock_analysis = Mock()
        mock_analysis.metadata = {
            'complexity': 'simple',
            'confidence': 1.5  # Invalid confidence > 1.0
        }
        mock_epic1_analyzer.analyze_query.return_value = mock_analysis
        
        with patch('app.core.analyzer.Epic1QueryAnalyzer', return_value=mock_epic1_analyzer):
            service = QueryAnalyzerService(config=analyzer_config)
            
            result = await service.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_exception(self, mock_epic1_analyzer, analyzer_config):
        """Test health check with analyzer exception."""
        mock_epic1_analyzer.analyze_query.side_effect = Exception("Analysis failed")
        
        with patch('app.core.analyzer.Epic1QueryAnalyzer', return_value=mock_epic1_analyzer):
            service = QueryAnalyzerService(config=analyzer_config)
            
            result = await service.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_shutdown(self, analyzer_service):
        """Test service shutdown."""
        # Verify service is initialized
        assert analyzer_service._initialized
        assert analyzer_service.analyzer is not None
        
        # Shutdown
        await analyzer_service.shutdown()
        
        # Verify cleanup
        assert not analyzer_service._initialized
        assert analyzer_service.analyzer is None

    @pytest.mark.asyncio
    async def test_metrics_collection_success(self, analyzer_service, sample_queries):
        """Test that metrics are collected on successful analysis."""
        query = sample_queries["simple"][0]
        
        with patch('app.core.analyzer.ANALYSIS_REQUESTS') as mock_requests, \
             patch('app.core.analyzer.ANALYSIS_DURATION') as mock_duration, \
             patch('app.core.analyzer.COMPLEXITY_DISTRIBUTION') as mock_complexity:
            
            await analyzer_service.analyze_query(query)
            
            # Verify metrics were updated
            mock_requests.labels.assert_called_with(status="success")
            mock_requests.labels().inc.assert_called_once()
            
            mock_duration.labels.assert_called_with(complexity="medium")
            mock_duration.labels().observe.assert_called_once()
            
            mock_complexity.labels.assert_called_with(complexity="medium")
            mock_complexity.labels().inc.assert_called_once()

    @pytest.mark.asyncio
    async def test_metrics_collection_error(self, mock_epic1_analyzer, analyzer_config):
        """Test that error metrics are collected on failure."""
        mock_epic1_analyzer.analyze_query.side_effect = ValueError("Test error")
        
        with patch('app.core.analyzer.Epic1QueryAnalyzer', return_value=mock_epic1_analyzer), \
             patch('app.core.analyzer.ANALYSIS_REQUESTS') as mock_requests:
            
            service = QueryAnalyzerService(config=analyzer_config)
            
            with pytest.raises(ValueError):
                await service.analyze_query("test query")
            
            # Verify error metrics were updated
            mock_requests.labels.assert_called_with(status="error")
            mock_requests.labels().inc.assert_called_once()

    @pytest.mark.asyncio
    async def test_component_health_metrics(self, analyzer_config):
        """Test component health metrics are updated."""
        with patch('app.core.analyzer.Epic1QueryAnalyzer') as mock_class, \
             patch('app.core.analyzer.COMPONENT_HEALTH') as mock_health:
            
            mock_class.return_value = Mock()
            service = QueryAnalyzerService(config=analyzer_config)
            await service._initialize_analyzer()
            
            # Verify health metrics were set to healthy
            expected_calls = [
                (("component", "feature_extractor"), 1),
                (("component", "complexity_classifier"), 1),
                (("component", "model_recommender"), 1)
            ]
            
            for args, value in expected_calls:
                mock_health.labels.assert_any_call(*args)
            
            # Check that set(1) was called for each component
            assert mock_health.labels().set.call_count == 3

    @pytest.mark.asyncio
    async def test_performance_timing(self, analyzer_service, sample_queries, performance_targets):
        """Test that analysis completes within performance targets."""
        query = sample_queries["complex"][0]  # Use complex query to stress test
        
        start_time = time.time()
        result = await analyzer_service.analyze_query(query)
        total_time = time.time() - start_time
        
        # Verify performance target is met
        assert_processing_time(total_time, performance_targets["max_response_time"])
        assert_processing_time(result["processing_time"], performance_targets["max_response_time"])

    @pytest.mark.asyncio
    async def test_multiple_concurrent_analyses(self, analyzer_service, sample_queries):
        """Test handling multiple concurrent analysis requests."""
        queries = sample_queries["medium"][:3]
        
        # Run analyses concurrently
        tasks = [analyzer_service.analyze_query(query) for query in queries]
        results = await asyncio.gather(*tasks)
        
        # Verify all analyses completed successfully
        assert len(results) == len(queries)
        
        for i, result in enumerate(results):
            assert result["query"] == queries[i]
            assert result["complexity"] in ["simple", "medium", "complex"]
            assert 0.0 <= result["confidence"] <= 1.0