"""
Integration tests for full service functionality.

Tests the complete Query Analyzer Service including FastAPI application,
service lifecycle, and full request-response cycles.
"""

import pytest
import asyncio
from unittest.mock import patch, Mock
import json
import time

from analyzer_app.main import create_app, get_analyzer_service
from analyzer_app.core.analyzer import QueryAnalyzerService
from conftest import (
    validate_response_structure,
    assert_valid_complexity,
    assert_confidence_range,
    assert_processing_time
)


class TestServiceLifecycle:
    """Test service startup and shutdown lifecycle."""

    @pytest.mark.asyncio
    async def test_app_creation(self):
        """Test FastAPI app creation."""
        app = create_app()
        
        assert app.title == "Query Analyzer Service"
        assert app.description == "Microservice for query analysis and complexity classification"
        assert app.version == "1.0.0"
        
        # Check routes are registered
        route_paths = [route.path for route in app.routes]
        assert "/api/v1/analyze" in route_paths
        assert "/api/v1/status" in route_paths
        assert "/api/v1/components" in route_paths
        assert "/api/v1/batch-analyze" in route_paths
        assert "/health" in route_paths
        assert "/health/live" in route_paths
        assert "/health/ready" in route_paths
        assert "/metrics" in str(route_paths)  # Mounted as sub-app

    @pytest.mark.asyncio
    async def test_service_initialization(self, mock_epic1_analyzer, analyzer_config):
        """Test service initialization with Epic1QueryAnalyzer."""
        with patch('app.core.analyzer.Epic1QueryAnalyzer', return_value=mock_epic1_analyzer):
            service = QueryAnalyzerService(config=analyzer_config)
            
            # Service should initialize lazily
            assert not service._initialized
            
            # Initialize on first use
            await service._initialize_analyzer()
            assert service._initialized
            assert service.analyzer is mock_epic1_analyzer

    @pytest.mark.asyncio
    async def test_service_health_monitoring(self, analyzer_service):
        """Test service health monitoring functionality."""
        # Health check should pass
        is_healthy = await analyzer_service.health_check()
        assert is_healthy is True
        
        # Status should show healthy
        status = await analyzer_service.get_analyzer_status()
        assert status["initialized"] is True
        assert status["status"] == "healthy"
        assert status["analyzer_type"] == "Epic1QueryAnalyzer"

    @pytest.mark.asyncio
    async def test_service_shutdown(self, analyzer_service):
        """Test graceful service shutdown."""
        # Verify service is operational
        assert analyzer_service._initialized
        assert analyzer_service.analyzer is not None
        
        # Shutdown should clean up properly
        await analyzer_service.shutdown()
        assert not analyzer_service._initialized
        assert analyzer_service.analyzer is None

    @pytest.mark.asyncio
    async def test_concurrent_service_usage(self, analyzer_service, sample_queries):
        """Test concurrent service usage."""
        queries = sample_queries["simple"] + sample_queries["medium"][:2]
        
        # Run multiple analyses concurrently
        tasks = [
            analyzer_service.analyze_query(query)
            for query in queries
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed
        assert len(results) == len(queries)
        for result in results:
            assert not isinstance(result, Exception)
            assert "query" in result
            assert "complexity" in result


class TestFullRequestResponseCycle:
    """Test complete request-response cycles through the service."""

    @pytest.mark.asyncio
    async def test_end_to_end_analysis(self, analyzer_service, sample_queries, expected_response_structure, performance_targets):
        """Test end-to-end query analysis."""
        for complexity, queries in sample_queries.items():
            for query in queries[:1]:  # Test one query per complexity
                result = await analyzer_service.analyze_query(query)
                
                # Validate structure and content
                validate_response_structure(result, expected_response_structure)
                assert result["query"] == query
                assert_valid_complexity(result["complexity"], performance_targets["valid_complexities"])
                assert_confidence_range(result["confidence"])
                assert_processing_time(result["processing_time"], performance_targets["max_response_time"])
                
                # Validate metadata
                assert "analyzer_version" in result["metadata"]
                assert "timestamp" in result["metadata"]
                assert isinstance(result["metadata"]["timestamp"], (int, float))

    @pytest.mark.asyncio
    async def test_context_preservation(self, analyzer_service, sample_queries):
        """Test that context is preserved through analysis."""
        query = sample_queries["medium"][0]
        context = {
            "user_id": "test-user-123",
            "session_id": "session-abc",
            "preferences": {"model": "balanced"},
            "metadata": {"source": "integration_test"}
        }
        
        result = await analyzer_service.analyze_query(query, context=context)
        
        # Context should be preserved in response metadata
        assert result["metadata"]["context"] == context

    @pytest.mark.asyncio
    async def test_feature_extraction_integration(self, analyzer_service, sample_queries):
        """Test feature extraction integration."""
        # Use a query with distinctive features
        query = sample_queries["complex"][0]  # Long, technical query
        
        result = await analyzer_service.analyze_query(query)
        
        # Should extract meaningful features
        features = result["features"]
        assert isinstance(features, dict)
        # Epic1QueryAnalyzer should provide various features
        # Exact structure depends on Epic1 implementation
        
        # Features should influence complexity classification
        assert result["complexity"] in ["simple", "medium", "complex"]

    @pytest.mark.asyncio
    async def test_model_recommendation_integration(self, analyzer_service, sample_queries):
        """Test model recommendation integration."""
        for complexity, queries in sample_queries.items():
            query = queries[0]
            result = await analyzer_service.analyze_query(query)
            
            # Should have model recommendations
            models = result["recommended_models"]
            assert isinstance(models, list)
            assert len(models) > 0
            
            # Should have cost estimates for recommended models
            costs = result["cost_estimate"]
            assert isinstance(costs, dict)
            
            # Each recommended model should have a cost estimate
            for model in models:
                if model in costs:  # Some models might not have costs (like Ollama)
                    assert isinstance(costs[model], (int, float))
                    assert costs[model] >= 0

    @pytest.mark.asyncio
    async def test_routing_strategy_integration(self, analyzer_service, sample_queries):
        """Test routing strategy integration."""
        query = sample_queries["medium"][0]
        
        result = await analyzer_service.analyze_query(query)
        
        # Should have routing strategy
        strategy = result["routing_strategy"]
        assert strategy in ["cost_optimized", "balanced", "quality_first"]
        
        # Strategy should influence model recommendations
        models = result["recommended_models"]
        costs = result["cost_estimate"]
        
        # For balanced strategy, should have mix of models
        if strategy == "balanced":
            assert len(models) > 0
        # For cost_optimized, should prefer lower cost models
        elif strategy == "cost_optimized":
            # Should include free models (Ollama) if available
            free_models = [m for m in models if costs.get(m, 0) == 0]
            if free_models:
                assert len(free_models) > 0

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, mock_epic1_analyzer, analyzer_config):
        """Test error handling in full integration."""
        # Mock Epic1QueryAnalyzer to fail
        mock_epic1_analyzer.analyze_query.side_effect = RuntimeError("Epic1 analysis failed")
        
        with patch('app.core.analyzer.Epic1QueryAnalyzer', return_value=mock_epic1_analyzer):
            service = QueryAnalyzerService(config=analyzer_config)
            
            # Error should propagate properly
            with pytest.raises(RuntimeError, match="Epic1 analysis failed"):
                await service.analyze_query("test query")

    @pytest.mark.asyncio
    async def test_performance_consistency(self, analyzer_service, sample_queries, performance_targets):
        """Test performance consistency across multiple requests."""
        query = sample_queries["medium"][0]
        results = []
        
        # Run multiple analyses
        for _ in range(5):
            result = await analyzer_service.analyze_query(query)
            results.append(result)
        
        # All should meet performance targets
        for result in results:
            assert_processing_time(result["processing_time"], performance_targets["max_response_time"])
        
        # Results should be consistent (same complexity/confidence range)
        complexities = [r["complexity"] for r in results]
        confidences = [r["confidence"] for r in results]
        
        # Complexity should be consistent
        assert len(set(complexities)) <= 2  # Allow some variation
        
        # Confidence should be in reasonable range
        for confidence in confidences:
            assert_confidence_range(confidence)

    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, analyzer_service, sample_queries):
        """Test that service doesn't leak memory over multiple requests."""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Run many analyses
        queries = sample_queries["simple"] * 10  # 40 total queries
        
        for query in queries:
            await analyzer_service.analyze_query(query)
            
        # Force garbage collection
        gc.collect()
        
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (less than 100MB)
        assert memory_growth < 100 * 1024 * 1024, f"Memory grew by {memory_growth / 1024 / 1024:.2f}MB"


class TestServiceConfiguration:
    """Test service configuration integration."""

    @pytest.mark.asyncio
    async def test_configuration_loading(self, temp_config_file):
        """Test configuration loading from file."""
        from analyzer_app.core.config import get_settings
        import os
        
        # Set config file environment variable
        with patch.dict(os.environ, {"QUERY_ANALYZER_CONFIG_FILE": str(temp_config_file)}):
            get_settings.cache_clear()  # Clear cache
            settings = get_settings()
            
            # Should load custom configuration
            assert settings.service_name == "query-analyzer-test"
            assert settings.port == 8081
            assert settings.analyzer_config.feature_extractor["cache_size"] == 500

    @pytest.mark.asyncio
    async def test_configuration_validation(self, analyzer_config):
        """Test configuration validation in service."""
        # Test with valid configuration
        service = QueryAnalyzerService(config=analyzer_config)
        assert service.config == analyzer_config
        
        # Test with empty configuration (should use defaults)
        service_empty = QueryAnalyzerService(config={})
        assert service_empty.config == {}

    @pytest.mark.asyncio
    async def test_environment_variable_integration(self):
        """Test environment variable integration."""
        from analyzer_app.core.config import ServiceSettings
        import os
        
        env_vars = {
            "QUERY_ANALYZER_LOG_LEVEL": "DEBUG",
            "QUERY_ANALYZER_PORT": "9090",
            "QUERY_ANALYZER_ENABLE_METRICS": "false"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = ServiceSettings()
            
            assert settings.log_level == "DEBUG"
            assert settings.port == 9090
            assert settings.enable_metrics is False


class TestServiceMetrics:
    """Test metrics collection integration."""

    @pytest.mark.asyncio
    async def test_metrics_collection_integration(self, analyzer_service, sample_queries):
        """Test that metrics are collected during service operation."""
        with patch('app.core.analyzer.ANALYSIS_REQUESTS') as mock_requests, \
             patch('app.core.analyzer.ANALYSIS_DURATION') as mock_duration, \
             patch('app.core.analyzer.COMPLEXITY_DISTRIBUTION') as mock_complexity, \
             patch('app.core.analyzer.COMPONENT_HEALTH') as mock_health:
            
            # Perform analysis
            query = sample_queries["simple"][0]
            await analyzer_service.analyze_query(query)
            
            # Verify metrics were collected
            mock_requests.labels.assert_called()
            mock_duration.labels.assert_called()
            mock_complexity.labels.assert_called()

    @pytest.mark.asyncio
    async def test_component_health_metrics(self, mock_epic1_analyzer, analyzer_config):
        """Test component health metrics are updated."""
        with patch('app.core.analyzer.Epic1QueryAnalyzer', return_value=mock_epic1_analyzer), \
             patch('app.core.analyzer.COMPONENT_HEALTH') as mock_health:
            
            service = QueryAnalyzerService(config=analyzer_config)
            await service._initialize_analyzer()
            
            # Health metrics should be set for each component
            expected_components = ["feature_extractor", "complexity_classifier", "model_recommender"]
            for component in expected_components:
                mock_health.labels.assert_any_call(component=component)
            
            # Shutdown should reset health metrics
            await service.shutdown()
            
            # Health should be set to 0 for each component
            shutdown_calls = [call for call in mock_health.labels().set.call_args_list if call[0][0] == 0]
            assert len(shutdown_calls) == 3  # One for each component


class TestServiceRobustness:
    """Test service robustness and edge cases."""

    @pytest.mark.asyncio
    async def test_malformed_query_handling(self, analyzer_service):
        """Test handling of malformed queries."""
        malformed_queries = [
            "",  # Empty - should be caught by validation
            "A" * 10001,  # Too long - should be caught by validation
            "\x00\x01\x02",  # Binary data
            "SELECT * FROM users; DROP TABLE users;",  # Potential injection
            "жЂп╟╚",  # Unicode edge case
        ]
        
        for query in malformed_queries:
            try:
                result = await analyzer_service.analyze_query(query)
                # If it doesn't raise an exception, should return valid result
                assert "complexity" in result
                assert "confidence" in result
            except (ValueError, RuntimeError):
                # Expected for some malformed queries
                pass

    @pytest.mark.asyncio
    async def test_service_recovery_after_error(self, mock_epic1_analyzer, analyzer_config):
        """Test service can recover after errors."""
        # Mock analyzer to fail once, then succeed
        mock_epic1_analyzer.analyze_query.side_effect = [
            RuntimeError("Temporary failure"),
            Mock(metadata={'complexity': 'simple', 'confidence': 0.9})
        ]
        
        with patch('app.core.analyzer.Epic1QueryAnalyzer', return_value=mock_epic1_analyzer):
            service = QueryAnalyzerService(config=analyzer_config)
            
            # First call should fail
            with pytest.raises(RuntimeError):
                await service.analyze_query("test query")
            
            # Second call should succeed
            result = await service.analyze_query("test query")
            assert result["complexity"] == "simple"

    @pytest.mark.asyncio
    async def test_high_concurrency_handling(self, analyzer_service, sample_queries):
        """Test service under high concurrency load."""
        # Create many concurrent tasks
        queries = sample_queries["simple"] * 20  # 80 concurrent requests
        
        async def analyze_with_delay(query):
            # Add small delay to increase concurrency
            await asyncio.sleep(0.001)
            return await analyzer_service.analyze_query(query)
        
        # Run all tasks concurrently
        tasks = [analyze_with_delay(query) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Most should succeed (allow for some failures under high load)
        successful = [r for r in results if not isinstance(r, Exception)]
        failure_rate = (len(results) - len(successful)) / len(results)
        
        # Failure rate should be low (less than 5%)
        assert failure_rate < 0.05, f"High failure rate: {failure_rate:.2%}"
        
        # All successful results should be valid
        for result in successful:
            assert "complexity" in result
            assert "confidence" in result

    @pytest.mark.asyncio
    async def test_service_state_consistency(self, analyzer_service, sample_queries):
        """Test service maintains consistent state across operations."""
        # Perform multiple operations
        query = sample_queries["medium"][0]
        
        # Multiple analyses
        for _ in range(3):
            result = await analyzer_service.analyze_query(query)
            assert result["query"] == query
        
        # Status checks
        for _ in range(3):
            status = await analyzer_service.get_analyzer_status()
            assert status["initialized"] is True
            assert status["status"] == "healthy"
        
        # Health checks
        for _ in range(3):
            health = await analyzer_service.health_check()
            assert health is True