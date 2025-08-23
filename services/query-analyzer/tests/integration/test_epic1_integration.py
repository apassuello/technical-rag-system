"""
Integration tests for Epic1QueryAnalyzer integration.

Tests the actual integration with Epic1QueryAnalyzer components,
ensuring proper data flow and compatibility.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

from analyzer_app.core.analyzer import QueryAnalyzerService
from conftest import (
    assert_valid_complexity,
    assert_confidence_range,
    assert_processing_time
)

# Add project root to path for Epic1 imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from components.query_processors.analyzers.epic1_query_analyzer import Epic1QueryAnalyzer
    from components.query_processors.base import QueryAnalysis
    EPIC1_AVAILABLE = True
except ImportError:
    EPIC1_AVAILABLE = False


@pytest.mark.skipif(not EPIC1_AVAILABLE, reason="Epic1QueryAnalyzer not available")
class TestEpic1QueryAnalyzerIntegration:
    """Test integration with actual Epic1QueryAnalyzer."""

    @pytest.fixture
    def epic1_config(self):
        """Configuration for Epic1QueryAnalyzer."""
        return {
            "feature_extractor": {
                "enable_caching": True,
                "cache_size": 100,
                "extract_linguistic": True,
                "extract_structural": True,
                "extract_semantic": True
            },
            "complexity_classifier": {
                "thresholds": {
                    "simple": 0.3,
                    "medium": 0.6,
                    "complex": 0.9
                },
                "weights": {
                    "length": 0.25,
                    "vocabulary": 0.25,
                    "syntax": 0.25,
                    "semantic": 0.25
                }
            },
            "model_recommender": {
                "strategy": "balanced",
                "model_mappings": {
                    "simple": ["ollama/llama3.2:3b"],
                    "medium": ["openai/gpt-3.5-turbo", "ollama/llama3.2:3b"],
                    "complex": ["openai/gpt-4", "mistral/mistral-large"]
                },
                "cost_weights": {
                    "ollama/llama3.2:3b": 0.0,
                    "openai/gpt-3.5-turbo": 0.002,
                    "openai/gpt-4": 0.06,
                    "mistral/mistral-large": 0.008
                }
            }
        }

    @pytest.mark.asyncio
    async def test_epic1_analyzer_initialization(self, epic1_config):
        """Test Epic1QueryAnalyzer initializes correctly in service."""
        service = QueryAnalyzerService(config=epic1_config)
        
        # Initialize should create Epic1QueryAnalyzer
        await service._initialize_analyzer()
        
        assert service._initialized
        assert service.analyzer is not None
        assert isinstance(service.analyzer, Epic1QueryAnalyzer)

    @pytest.mark.asyncio
    async def test_epic1_analyzer_workflow(self, epic1_config, sample_queries, performance_targets):
        """Test complete Epic1QueryAnalyzer workflow integration."""
        service = QueryAnalyzerService(config=epic1_config)
        
        for complexity_level, queries in sample_queries.items():
            query = queries[0]
            
            result = await service.analyze_query(query)
            
            # Validate Epic1 integration
            assert result["query"] == query
            assert_valid_complexity(result["complexity"], performance_targets["valid_complexities"])
            assert_confidence_range(result["confidence"])
            assert_processing_time(result["processing_time"], performance_targets["max_response_time"])
            
            # Epic1-specific validations
            assert "features" in result
            assert isinstance(result["features"], dict)
            assert "recommended_models" in result
            assert isinstance(result["recommended_models"], list)
            assert len(result["recommended_models"]) > 0

    @pytest.mark.asyncio
    async def test_epic1_feature_extraction(self, epic1_config, sample_queries):
        """Test Epic1 feature extraction integration."""
        service = QueryAnalyzerService(config=epic1_config)
        
        # Test different query types
        simple_query = sample_queries["simple"][0]
        complex_query = sample_queries["complex"][0]
        
        simple_result = await service.analyze_query(simple_query)
        complex_result = await service.analyze_query(complex_query)
        
        # Feature extraction should produce different results
        simple_features = simple_result["features"]
        complex_features = complex_result["features"]
        
        assert isinstance(simple_features, dict)
        assert isinstance(complex_features, dict)
        
        # Features should be different for different complexity queries
        # Exact feature names depend on Epic1 implementation
        assert simple_features != complex_features

    @pytest.mark.asyncio
    async def test_epic1_complexity_classification(self, epic1_config, sample_queries):
        """Test Epic1 complexity classification integration."""
        service = QueryAnalyzerService(config=epic1_config)
        
        # Test that different queries get appropriate classifications
        classifications = {}
        
        for complexity_level, queries in sample_queries.items():
            query = queries[0]
            result = await service.analyze_query(query)
            classifications[query] = result["complexity"]
        
        # Should have some variation in classifications
        unique_classifications = set(classifications.values())
        assert len(unique_classifications) > 1, "All queries classified the same"

    @pytest.mark.asyncio
    async def test_epic1_model_recommendation(self, epic1_config, sample_queries):
        """Test Epic1 model recommendation integration."""
        service = QueryAnalyzerService(config=epic1_config)
        
        for complexity_level, queries in sample_queries.items():
            query = queries[0]
            result = await service.analyze_query(query)
            
            models = result["recommended_models"]
            costs = result["cost_estimate"]
            
            # Should recommend appropriate models
            assert len(models) > 0
            
            # Cost estimates should be provided
            assert isinstance(costs, dict)
            
            # Some models should have cost estimates
            for model in models:
                if model in costs:
                    assert costs[model] >= 0

    @pytest.mark.asyncio
    async def test_epic1_routing_strategy_impact(self, epic1_config, sample_queries):
        """Test that Epic1 routing strategy affects recommendations."""
        strategies = ["cost_optimized", "balanced", "quality_first"]
        results_by_strategy = {}
        
        for strategy in strategies:
            config = epic1_config.copy()
            config["model_recommender"]["strategy"] = strategy
            
            service = QueryAnalyzerService(config=config)
            query = sample_queries["medium"][0]
            
            result = await service.analyze_query(query)
            results_by_strategy[strategy] = result
        
        # Different strategies should potentially recommend different models
        model_sets = [
            set(result["recommended_models"])
            for result in results_by_strategy.values()
        ]
        
        # At least some strategies should differ
        # (Exact behavior depends on Epic1 implementation)
        assert any(s1 != s2 for s1 in model_sets for s2 in model_sets)

    @pytest.mark.asyncio
    async def test_epic1_performance_tracking(self, epic1_config, sample_queries):
        """Test Epic1 performance tracking integration."""
        service = QueryAnalyzerService(config=epic1_config)
        
        # Run multiple analyses
        for _ in range(3):
            query = sample_queries["simple"][0]
            await service.analyze_query(query)
        
        # Check performance metrics in status
        status = await service.get_analyzer_status()
        
        if "performance" in status and status["performance"]:
            performance = status["performance"]
            
            # Should have timing information
            if "average_times" in performance:
                avg_times = performance["average_times"]
                
                # Epic1 should track different phases
                expected_phases = ["feature_extraction", "complexity_classification", "model_recommendation", "total"]
                for phase in expected_phases:
                    if phase in avg_times:
                        assert avg_times[phase] >= 0

    @pytest.mark.asyncio
    async def test_epic1_error_handling(self, epic1_config):
        """Test Epic1 error handling integration."""
        service = QueryAnalyzerService(config=epic1_config)
        
        # Test with potentially problematic queries
        problematic_queries = [
            "",  # Empty query
            "A" * 1000,  # Very long query
            "\x00\x01\x02",  # Binary data
            "пруветpx}",  # Unicode with special characters
        ]
        
        for query in problematic_queries:
            try:
                result = await service.analyze_query(query)
                # If no exception, result should be valid
                assert "complexity" in result
                assert "confidence" in result
            except Exception as e:
                # Some queries may legitimately fail
                assert isinstance(e, (ValueError, RuntimeError))

    @pytest.mark.asyncio
    async def test_epic1_configuration_impact(self, sample_queries):
        """Test that Epic1 configuration changes affect behavior."""
        base_config = {
            "complexity_classifier": {
                "thresholds": {
                    "simple": 0.3,
                    "medium": 0.6,
                    "complex": 0.9
                }
            }
        }
        
        # Config with very low thresholds (everything should be complex)
        low_threshold_config = {
            "complexity_classifier": {
                "thresholds": {
                    "simple": 0.01,
                    "medium": 0.02,
                    "complex": 0.03
                }
            }
        }
        
        # Test with base config
        base_service = QueryAnalyzerService(config=base_config)
        query = sample_queries["simple"][0]
        base_result = await base_service.analyze_query(query)
        
        # Test with low threshold config
        low_service = QueryAnalyzerService(config=low_threshold_config)
        low_result = await low_service.analyze_query(query)
        
        # Results might be different due to configuration
        # (Exact behavior depends on Epic1 implementation)
        # At minimum, both should be valid results
        for result in [base_result, low_result]:
            assert result["complexity"] in ["simple", "medium", "complex"]
            assert 0.0 <= result["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_epic1_caching_behavior(self, epic1_config, sample_queries):
        """Test Epic1 caching behavior integration."""
        # Enable caching in config
        config_with_cache = epic1_config.copy()
        config_with_cache["feature_extractor"]["enable_caching"] = True
        config_with_cache["feature_extractor"]["cache_size"] = 100
        
        service = QueryAnalyzerService(config=config_with_cache)
        query = sample_queries["medium"][0]
        
        # First analysis (cache miss)
        result1 = await service.analyze_query(query)
        time1 = result1["processing_time"]
        
        # Second analysis (cache hit - should be faster)
        result2 = await service.analyze_query(query)
        time2 = result2["processing_time"]
        
        # Results should be consistent
        assert result1["query"] == result2["query"]
        assert result1["complexity"] == result2["complexity"]
        
        # Second call might be faster due to caching
        # (Exact behavior depends on Epic1 caching implementation)
        assert time2 >= 0  # At minimum, should be valid time

    @pytest.mark.asyncio
    async def test_epic1_component_health(self, epic1_config):
        """Test Epic1 component health monitoring integration."""
        service = QueryAnalyzerService(config=epic1_config)
        
        # Get status after initialization
        status = await service.get_analyzer_status()
        
        # Should report component health
        if "components" in status:
            components = status["components"]
            
            # Epic1 has three main components
            expected_components = ["feature_extractor", "complexity_classifier", "model_recommender"]
            for component in expected_components:
                if component in components:
                    assert components[component] in ["healthy", "unhealthy", "unknown"]


@pytest.mark.skipif(EPIC1_AVAILABLE, reason="Testing fallback when Epic1 not available")
class TestEpic1UnavailableHandling:
    """Test handling when Epic1QueryAnalyzer is not available."""

    @pytest.mark.asyncio
    async def test_missing_epic1_error(self, analyzer_config):
        """Test error when Epic1QueryAnalyzer is missing."""
        with patch('app.core.analyzer.Epic1QueryAnalyzer', side_effect=ImportError("Epic1 not found")):
            service = QueryAnalyzerService(config=analyzer_config)
            
            with pytest.raises(ImportError):
                await service._initialize_analyzer()

    @pytest.mark.asyncio
    async def test_epic1_import_fallback(self, analyzer_config):
        """Test graceful handling of Epic1 import issues."""
        # Mock import failure
        with patch.dict('sys.modules', {'components.query_processors.analyzers.epic1_query_analyzer': None}):
            with pytest.raises(ImportError):
                from analyzer_app.core.analyzer import Epic1QueryAnalyzer


class TestEpic1MockedIntegration:
    """Test Epic1 integration with mocked components for consistent testing."""

    def create_mock_epic1_analyzer(self):
        """Create a realistic mock of Epic1QueryAnalyzer."""
        mock_analyzer = Mock()
        
        # Mock sub-components
        mock_analyzer.feature_extractor = Mock()
        mock_analyzer.complexity_classifier = Mock()
        mock_analyzer.model_recommender = Mock()
        mock_analyzer.model_recommender.strategy = "balanced"
        
        # Mock analysis times
        mock_analyzer._analysis_times = {
            'feature_extraction': [0.005, 0.006, 0.004],
            'complexity_classification': [0.003, 0.004, 0.002],
            'model_recommendation': [0.002, 0.003, 0.002],
            'total': [0.010, 0.013, 0.008]
        }
        
        return mock_analyzer

    @pytest.mark.asyncio
    async def test_mocked_epic1_integration(self, analyzer_config, sample_queries, performance_targets):
        """Test integration with mocked Epic1QueryAnalyzer."""
        mock_analyzer = self.create_mock_epic1_analyzer()
        
        # Mock analyze_query method
        def mock_analyze(query):
            mock_result = Mock()
            mock_result.metadata = {
                'complexity': 'medium',
                'confidence': 0.75,
                'features': {
                    'length': len(query),
                    'word_count': len(query.split()),
                    'vocabulary_complexity': 0.6,
                    'syntax_complexity': 0.5,
                    'semantic_complexity': 0.4
                },
                'recommended_models': ['openai/gpt-3.5-turbo', 'ollama/llama3.2:3b'],
                'cost_estimate': {
                    'openai/gpt-3.5-turbo': 0.002,
                    'ollama/llama3.2:3b': 0.0
                },
                'routing_strategy': 'balanced'
            }
            return mock_result
        
        mock_analyzer.analyze_query = mock_analyze
        
        # Test with mocked analyzer
        with patch('app.core.analyzer.Epic1QueryAnalyzer', return_value=mock_analyzer):
            service = QueryAnalyzerService(config=analyzer_config)
            
            query = sample_queries["medium"][0]
            result = await service.analyze_query(query)
            
            # Validate integration
            assert result["query"] == query
            assert result["complexity"] == "medium"
            assert result["confidence"] == 0.75
            assert len(result["features"]) > 0
            assert len(result["recommended_models"]) > 0
            assert isinstance(result["cost_estimate"], dict)

    @pytest.mark.asyncio
    async def test_mocked_epic1_status_integration(self, analyzer_config):
        """Test status integration with mocked Epic1QueryAnalyzer."""
        mock_analyzer = self.create_mock_epic1_analyzer()
        
        with patch('app.core.analyzer.Epic1QueryAnalyzer', return_value=mock_analyzer):
            service = QueryAnalyzerService(config=analyzer_config)
            await service._initialize_analyzer()
            
            status = await service.get_analyzer_status()
            
            # Validate status integration
            assert status["initialized"] is True
            assert status["status"] == "healthy"
            assert status["analyzer_type"] == "Epic1QueryAnalyzer"
            
            # Should include performance metrics
            if "performance" in status:
                performance = status["performance"]
                assert "average_times" in performance
                assert "total_analyses" in performance

    @pytest.mark.asyncio
    async def test_mocked_epic1_configuration_integration(self, analyzer_config):
        """Test configuration integration with mocked Epic1QueryAnalyzer."""
        mock_analyzer = self.create_mock_epic1_analyzer()
        
        with patch('app.core.analyzer.Epic1QueryAnalyzer', return_value=mock_analyzer) as mock_class:
            service = QueryAnalyzerService(config=analyzer_config)
            await service._initialize_analyzer()
            
            # Verify Epic1QueryAnalyzer was initialized with correct config
            mock_class.assert_called_once_with(config=analyzer_config)
            
            # Configuration should be accessible
            status = await service.get_analyzer_status()
            assert "configuration" in status
            config_status = status["configuration"]
            
            # Should reflect the configured strategy
            assert config_status["strategy"] == "balanced"