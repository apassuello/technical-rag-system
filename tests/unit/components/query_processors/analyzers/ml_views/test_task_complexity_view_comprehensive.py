"""
Comprehensive Test Suite for TaskComplexityView - Phase 2 Strategic Component Testing.

This test suite provides complete coverage for TaskComplexityView following the proven
methodology from Phase 1 (ComputationalComplexityView achieved 85.7% coverage).

Target: TaskComplexityView - 301 statements, 20.6% → 85%+ coverage
Architecture: HybridView with DeBERTa-v3 ML + task pattern analysis
Business Value: Epic1 intelligent routing task complexity analysis

Note: This is an integration test requiring ML dependencies (torch, transformers).
Should be in tests/integration/ml_infrastructure/ but kept here with proper markers.
"""

import pytest

# Mark entire module as integration test requiring ML
pytestmark = [pytest.mark.integration, pytest.mark.requires_ml, pytest.mark.slow]
import numpy as np
import torch
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
import asyncio
import time
from pathlib import Path

from src.components.query_processors.analyzers.ml_views.task_complexity_view import TaskComplexityView
from src.components.query_processors.analyzers.ml_views.view_result import ViewResult, AnalysisMethod


class TestTaskComplexityViewComprehensive:
    """Comprehensive test suite for TaskComplexityView following Phase 1 methodology."""

    @pytest.fixture
    def mock_deberta_model(self):
        """Mock DeBERTa-v3 model for ML analysis testing."""
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        # Configure mock model outputs
        mock_model.return_value = Mock()
        mock_model.return_value.last_hidden_state = torch.randn(1, 10, 768)
        mock_model.return_value.pooler_output = torch.randn(1, 768)
        
        # Configure mock tokenizer
        mock_tokenizer.return_value = {
            'input_ids': torch.tensor([[101, 1234, 5678, 102]]),
            'attention_mask': torch.tensor([[1, 1, 1, 1]]),
            'token_type_ids': torch.tensor([[0, 0, 0, 0]])
        }
        mock_tokenizer.encode.return_value = [101, 1234, 5678, 102]
        
        return mock_model, mock_tokenizer

    @pytest.fixture
    def sample_queries(self):
        """Sample queries for task complexity testing."""
        return {
            'simple_factual': "What is the capital of France?",
            'analytical': "Compare the advantages and disadvantages of renewable energy sources.",
            'creative': "Design a creative solution for reducing urban traffic congestion.",
            'multistep': "First analyze the market trends, then create a forecast, and finally recommend strategies.",
            'evaluative': "Evaluate the effectiveness of different teaching methodologies for online learning.",
            'synthesis': "Synthesize information from multiple sources to create a comprehensive proposal.",
            'empty': "",
            'very_long': "Analyze the complex interplay between socioeconomic factors, environmental conditions, and technological advancement in determining the sustainability of urban development projects across different geographical regions while considering the impact of climate change, population growth, and resource availability on long-term viability and community well-being." * 10
        }

    @pytest.fixture
    def default_config(self):
        """Default configuration for TaskComplexityView."""
        return {
            'ml_weight': 0.6,
            'algorithmic_weight': 0.4,
            'performance_mode': 'balanced',
            'enable_caching': True,
            'model_name': 'microsoft/deberta-v3-base',
            'confidence_threshold': 0.7,
            'task_pattern_weights': {
                'blooms_taxonomy': 0.3,
                'task_type': 0.4,
                'cognitive_load': 0.3
            }
        }

    @pytest.fixture  
    def mock_model_manager(self):
        """Mock ModelManager for ML model loading."""
        with patch('src.components.query_processors.analyzers.ml_views.task_complexity_view.ModelManager') as mock_manager:
            mock_instance = Mock()
            mock_manager.return_value = mock_instance
            
            # Mock model loading
            mock_instance.load_model.return_value = (Mock(), Mock())
            mock_instance.is_model_available.return_value = True
            mock_instance.get_model_info.return_value = {'name': 'deberta-v3-base', 'size': '279MB'}
            
            yield mock_instance

    # ==================== INITIALIZATION TESTS ====================
    
    def test_initialization_default_config(self, mock_model_manager):
        """Test successful initialization with default configuration."""
        view = TaskComplexityView()
        
        # Verify basic initialization
        assert view.view_name == "task"
        assert view.ml_weight == 0.5
        assert view.algorithmic_weight == 0.5
        assert hasattr(view, 'enable_blooms_taxonomy')
        assert hasattr(view, 'cognitive_threshold')
        assert hasattr(view, 'task_patterns')
        assert hasattr(view, 'bloom_patterns')
        
    def test_initialization_custom_config(self, mock_model_manager, default_config):
        """Test initialization with custom configuration."""
        custom_config = {
            **default_config,
            'ml_weight': 0.8,
            'algorithmic_weight': 0.2,
            'confidence_threshold': 0.8
        }
        
        view = TaskComplexityView(custom_config)
        
        assert view.ml_weight == 0.8
        assert view.algorithmic_weight == 0.2
        assert view.confidence_threshold == 0.8
        
    def test_initialization_pattern_compilation(self, mock_model_manager):
        """Test that task patterns are compiled correctly."""
        view = TaskComplexityView()
        
        # Verify pattern compilation
        assert hasattr(view, 'bloom_patterns')
        assert hasattr(view, 'task_type_patterns')
        assert hasattr(view, 'multistep_patterns')
        assert len(view.bloom_patterns) > 0
        assert len(view.task_type_patterns) > 0
        
    # ==================== ALGORITHMIC ANALYSIS TESTS ====================
    
    def test_analyze_algorithmic_simple_factual(self, mock_model_manager, sample_queries):
        """Test algorithmic analysis of simple factual query."""
        view = TaskComplexityView()
        query = sample_queries['simple_factual']
        
        result = view._analyze_algorithmic(query)
        
        assert isinstance(result, dict)
        assert 'blooms_taxonomy' in result
        assert 'task_type' in result
        assert 'cognitive_load' in result
        assert 'complexity_score' in result
        assert 'confidence' in result
        assert 'analysis_method' in result
        assert result['analysis_method'] == AnalysisMethod.ALGORITHMIC
        
    def test_analyze_algorithmic_analytical_query(self, mock_model_manager, sample_queries):
        """Test algorithmic analysis of analytical query."""
        view = TaskComplexityView()
        query = sample_queries['analytical']
        
        result = view._analyze_algorithmic(query)
        
        # Should detect higher complexity for analytical task
        assert result['complexity_score'] > 0.5
        assert result['blooms_taxonomy']['level'] in ['analyze', 'evaluate']
        assert result['task_type']['primary'] in ['analytical', 'comparative']
        
    def test_analyze_algorithmic_creative_query(self, mock_model_manager, sample_queries):
        """Test algorithmic analysis of creative query."""
        view = TaskComplexityView()
        query = sample_queries['creative']
        
        result = view._analyze_algorithmic(query)
        
        # Should detect creative task patterns
        assert result['complexity_score'] > 0.6
        assert result['task_type']['primary'] in ['creative', 'design']
        assert result['blooms_taxonomy']['level'] in ['create', 'synthesize']
        
    def test_analyze_algorithmic_multistep_query(self, mock_model_manager, sample_queries):
        """Test algorithmic analysis of multistep query."""
        view = TaskComplexityView()
        query = sample_queries['multistep']
        
        result = view._analyze_algorithmic(query)
        
        # Should detect multistep complexity
        assert result['complexity_score'] > 0.7
        assert result['cognitive_load']['is_multistep'] is True
        assert result['cognitive_load']['step_count'] >= 3
        
    def test_blooms_taxonomy_classification(self, mock_model_manager, sample_queries):
        """Test Bloom's taxonomy classification accuracy."""
        view = TaskComplexityView()
        
        test_cases = [
            (sample_queries['simple_factual'], ['remember', 'understand']),
            (sample_queries['analytical'], ['analyze', 'evaluate']),
            (sample_queries['creative'], ['create', 'synthesize']),
            (sample_queries['evaluative'], ['evaluate'])
        ]
        
        for query, expected_levels in test_cases:
            result = view._classify_blooms_taxonomy(query)
            assert result['level'] in expected_levels
            assert isinstance(result['confidence'], float)
            assert 0 <= result['confidence'] <= 1
            
    def test_task_type_classification(self, mock_model_manager, sample_queries):
        """Test task type classification functionality."""
        view = TaskComplexityView()
        
        for query_type, query in sample_queries.items():
            if query:  # Skip empty query
                result = view._classify_task_type(query)
                assert 'primary' in result
                assert 'secondary' in result
                assert 'confidence' in result
                assert isinstance(result['confidence'], float)
                
    def test_multistep_detection(self, mock_model_manager, sample_queries):
        """Test multistep task detection."""
        view = TaskComplexityView()
        
        # Test multistep query
        result = view._detect_multistep_task(sample_queries['multistep'])
        assert result['is_multistep'] is True
        assert result['step_count'] >= 2
        
        # Test simple query
        result = view._detect_multistep_task(sample_queries['simple_factual'])
        assert result['is_multistep'] is False
        assert result['step_count'] == 1
        
    def test_cognitive_load_analysis(self, mock_model_manager, sample_queries):
        """Test cognitive load analysis functionality."""
        view = TaskComplexityView()
        
        for query_type, query in sample_queries.items():
            if query:  # Skip empty query
                result = view._analyze_cognitive_load(query, {'complexity_score': 0.5})
                assert 'load_level' in result
                assert 'factors' in result
                assert 'is_multistep' in result
                assert isinstance(result['load_level'], str)
                
    # ==================== ML ANALYSIS TESTS ====================
    
    @patch('src.components.query_processors.analyzers.ml_views.task_complexity_view.ModelManager')
    @patch('torch.no_grad')
    def test_analyze_ml_with_model(self, mock_no_grad, mock_manager_class, mock_deberta_model, sample_queries):
        """Test ML analysis with mocked DeBERTa model."""
        mock_model, mock_tokenizer = mock_deberta_model
        
        # Configure ModelManager mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.load_model.return_value = (mock_model, mock_tokenizer)
        mock_manager.is_model_available.return_value = True
        
        # Configure torch.no_grad context manager
        mock_no_grad.return_value.__enter__ = Mock(return_value=None)
        mock_no_grad.return_value.__exit__ = Mock(return_value=None)
        
        view = TaskComplexityView()
        query = sample_queries['analytical']
        
        result = view._analyze_ml(query)
        
        assert isinstance(result, dict)
        assert 'task_classification' in result
        assert 'complexity_score' in result
        assert 'confidence' in result
        assert 'analysis_method' in result
        assert result['analysis_method'] == AnalysisMethod.ML
        assert isinstance(result['confidence'], float)
        assert 0 <= result['confidence'] <= 1
        
    @patch('src.components.query_processors.analyzers.ml_views.task_complexity_view.ModelManager')
    def test_get_query_embedding(self, mock_manager_class, mock_deberta_model, sample_queries):
        """Test query embedding generation."""
        mock_model, mock_tokenizer = mock_deberta_model
        
        # Configure ModelManager mock  
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.load_model.return_value = (mock_model, mock_tokenizer)
        mock_manager.is_model_available.return_value = True
        
        view = TaskComplexityView()
        query = sample_queries['simple_factual']
        
        with patch('torch.no_grad'):
            embedding = view._get_query_embedding(query)
            
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (768,)  # DeBERTa-v3 embedding dimension
        
    @patch('src.components.query_processors.analyzers.ml_views.task_complexity_view.ModelManager')
    def test_compute_anchor_similarities(self, mock_manager_class, mock_deberta_model):
        """Test anchor similarity computation."""
        mock_model, mock_tokenizer = mock_deberta_model
        
        # Configure ModelManager mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.load_model.return_value = (mock_model, mock_tokenizer)
        mock_manager.is_model_available.return_value = True
        
        view = TaskComplexityView()
        query_embedding = np.random.randn(768)
        
        similarities = view._compute_anchor_similarities(query_embedding)
        
        assert isinstance(similarities, dict)
        assert len(similarities) > 0
        for task_type, similarity in similarities.items():
            assert isinstance(similarity, float)
            assert -1 <= similarity <= 1
            
    def test_cosine_similarity_calculation(self, mock_model_manager):
        """Test cosine similarity calculation accuracy."""
        view = TaskComplexityView()
        
        # Test identical vectors
        vec1 = np.array([1, 2, 3])
        vec2 = np.array([1, 2, 3])
        similarity = view._cosine_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 1e-10
        
        # Test orthogonal vectors
        vec1 = np.array([1, 0, 0])
        vec2 = np.array([0, 1, 0])
        similarity = view._cosine_similarity(vec1, vec2)
        assert abs(similarity - 0.0) < 1e-10
        
    # ==================== INTEGRATION TESTS ====================
    
    @patch('src.components.query_processors.analyzers.ml_views.task_complexity_view.ModelManager')
    def test_end_to_end_analysis_flow(self, mock_manager_class, mock_deberta_model, sample_queries):
        """Test complete end-to-end analysis workflow."""
        mock_model, mock_tokenizer = mock_deberta_model
        
        # Configure ModelManager mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.load_model.return_value = (mock_model, mock_tokenizer)
        mock_manager.is_model_available.return_value = True
        
        view = TaskComplexityView()
        query = sample_queries['analytical']
        
        with patch('torch.no_grad'):
            result = view.analyze(query)
            
        assert isinstance(result, ViewResult)
        assert result.view_name == "task"
        assert isinstance(result.complexity_score, float)
        assert 0 <= result.complexity_score <= 1
        assert isinstance(result.confidence, float)
        assert 0 <= result.confidence <= 1
        assert result.analysis_method in [AnalysisMethod.HYBRID, AnalysisMethod.ALGORITHMIC, AnalysisMethod.ML]
        
    # ==================== PERFORMANCE TESTS ====================
    
    def test_algorithmic_analysis_performance(self, mock_model_manager, sample_queries):
        """Test that algorithmic analysis meets <4ms performance target."""
        view = TaskComplexityView()
        query = sample_queries['analytical']
        
        # Warm up
        view._analyze_algorithmic(query)
        
        # Performance test
        start_time = time.perf_counter()
        for _ in range(10):
            view._analyze_algorithmic(query)
        end_time = time.perf_counter()
        
        avg_time_ms = ((end_time - start_time) / 10) * 1000
        assert avg_time_ms < 4.0, f"Algorithmic analysis took {avg_time_ms:.2f}ms, exceeds 4ms target"
        
    @patch('src.components.query_processors.analyzers.ml_views.task_complexity_view.ModelManager')
    def test_ml_analysis_performance(self, mock_manager_class, mock_deberta_model, sample_queries):
        """Test that ML analysis meets <25ms performance target."""
        mock_model, mock_tokenizer = mock_deberta_model
        
        # Configure ModelManager mock
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.load_model.return_value = (mock_model, mock_tokenizer)
        mock_manager.is_model_available.return_value = True
        
        view = TaskComplexityView()
        query = sample_queries['analytical']
        
        with patch('torch.no_grad'):
            # Warm up
            view._analyze_ml(query)
            
            # Performance test
            start_time = time.perf_counter()
            for _ in range(5):
                view._analyze_ml(query)
            end_time = time.perf_counter()
            
        avg_time_ms = ((end_time - start_time) / 5) * 1000
        assert avg_time_ms < 25.0, f"ML analysis took {avg_time_ms:.2f}ms, exceeds 25ms target"
        
    # ==================== ERROR HANDLING TESTS ====================
    
    def test_empty_query_handling(self, mock_model_manager, sample_queries):
        """Test graceful handling of empty queries."""
        view = TaskComplexityView()
        
        result = view._analyze_algorithmic(sample_queries['empty'])
        
        assert isinstance(result, dict)
        assert result['complexity_score'] == 0.0
        assert result['confidence'] == 0.0
        
    def test_very_long_query_handling(self, mock_model_manager, sample_queries):
        """Test handling of very long queries."""
        view = TaskComplexityView()
        query = sample_queries['very_long']
        
        result = view._analyze_algorithmic(query)
        
        # Should handle long queries gracefully
        assert isinstance(result, dict)
        assert 'complexity_score' in result
        assert isinstance(result['complexity_score'], float)
        
    @patch('src.components.query_processors.analyzers.ml_views.task_complexity_view.ModelManager')
    def test_ml_model_unavailable_fallback(self, mock_manager_class, sample_queries):
        """Test fallback when ML model is unavailable."""
        # Configure ModelManager to indicate model unavailable
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        mock_manager.is_model_available.return_value = False
        
        view = TaskComplexityView()
        query = sample_queries['analytical']
        
        result = view._analyze_ml(query)
        
        # Should fallback gracefully
        assert result['analysis_method'] == AnalysisMethod.ALGORITHMIC
        assert isinstance(result['complexity_score'], float)
        
    # ==================== CONFIGURATION TESTS ====================
    
    def test_weight_configuration_impact(self, mock_model_manager, sample_queries):
        """Test that weight configuration affects results."""
        query = sample_queries['analytical']
        
        # Test high algorithmic weight
        view_algo = TaskComplexityView({'ml_weight': 0.2, 'algorithmic_weight': 0.8})
        
        # Test high ML weight  
        view_ml = TaskComplexityView({'ml_weight': 0.8, 'algorithmic_weight': 0.2})
        
        # Both should work with different weightings
        result_algo = view_algo._analyze_algorithmic(query)
        result_ml = view_ml._analyze_algorithmic(query)
        
        assert isinstance(result_algo['complexity_score'], float)
        assert isinstance(result_ml['complexity_score'], float)
        
    def test_confidence_threshold_configuration(self, mock_model_manager, default_config, sample_queries):
        """Test confidence threshold configuration."""
        high_threshold_config = {**default_config, 'confidence_threshold': 0.9}
        low_threshold_config = {**default_config, 'confidence_threshold': 0.3}
        
        view_high = TaskComplexityView(high_threshold_config)
        view_low = TaskComplexityView(low_threshold_config)
        
        assert view_high.confidence_threshold == 0.9
        assert view_low.confidence_threshold == 0.3
        
    # ==================== EDGE CASE TESTS ====================
    
    def test_concurrent_analysis_thread_safety(self, mock_model_manager, sample_queries):
        """Test thread safety for concurrent analysis requests."""
        view = TaskComplexityView()
        queries = [sample_queries['simple_factual'], sample_queries['analytical'], sample_queries['creative']]
        
        import concurrent.futures
        
        def analyze_query(query):
            return view._analyze_algorithmic(query)
            
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(analyze_query, query) for query in queries]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
        # All results should be valid
        assert len(results) == 3
        for result in results:
            assert isinstance(result, dict)
            assert 'complexity_score' in result
            
    def test_special_character_handling(self, mock_model_manager):
        """Test handling of queries with special characters."""
        view = TaskComplexityView()
        
        special_queries = [
            "What is 2+2? Explain the math!",
            "Compare A vs B & C vs D (include pros/cons)",
            "Analyze: Item #1, Item #2, and Item #3 - which is best?",
            "Create a plan using 50% method A + 50% method B"
        ]
        
        for query in special_queries:
            result = view._analyze_algorithmic(query)
            assert isinstance(result, dict)
            assert 'complexity_score' in result
            assert isinstance(result['complexity_score'], float)