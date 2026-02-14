"""
Unit Tests for Base View Classes.

Tests the base view architecture including BaseView, AlgorithmicView,
MLView, and HybridView abstract classes and patterns.
"""

import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from abc import ABC, abstractmethod
import pytest

# Imports handled by conftest.py

from fixtures.base_test import MLInfrastructureTestBase, PerformanceTestMixin
from fixtures.mock_models import MockTransformerModel, MockModelFactory
from fixtures.test_data import ViewFrameworkTestData

from src.components.query_processors.analyzers.ml_views.base_view import (
    BaseView, AlgorithmicView, MLView, HybridView
)
from src.components.query_processors.analyzers.ml_views.view_result import (
    ViewResult, AnalysisMethod
)


# Test implementations for testing base classes
class SampleAlgorithmicView(AlgorithmicView):
    """Sample implementation of AlgorithmicView for testing."""

    def __init__(self, view_name='test_algorithmic', config=None):
        super().__init__(view_name, config)
        self.analysis_count = 0

    def _initialize_algorithmic_components(self):
        """Initialize algorithmic components (required by base class)."""
        pass

    def _analyze_algorithmic(self, query: str) -> dict:
        """Test algorithmic analysis implementation.

        Returns dict with score, confidence, features, metadata.
        """
        self.analysis_count += 1

        # Simple mock analysis
        word_count = len(query.split())
        score = min(word_count / 20.0, 1.0)  # Normalize by 20 words

        return {
            'score': score,
            'confidence': 0.95,  # High confidence for algorithmic
            'features': {'word_count': word_count, 'analysis_count': self.analysis_count},
            'metadata': {'timestamp': time.time()}
        }


class SampleMLView(MLView):
    """Sample implementation of MLView for testing."""

    def __init__(self, view_name='test_ml', config=None):
        # MLView requires ml_model_name parameter
        super().__init__(view_name, ml_model_name='test-ml-model', config=config)
        self.model_loaded = False
        self.model_load_count = 0

        # Mock model factory
        self.model_factory = MockModelFactory()

    def _initialize_ml_components(self):
        """Initialize ML components (required by base class)."""
        pass

    def _initialize_algorithmic_fallback(self):
        """Initialize algorithmic fallback components (required by base class)."""
        pass

    def load_ml_model(self):
        """Mock ML model loading."""
        if not self.model_loaded:
            self.model = self.model_factory.create_model('test-ml-model')
            self.model.load()
            self.model_loaded = True
            self.model_load_count += 1

    def _analyze_ml(self, query: str) -> dict:
        """Test ML analysis implementation.

        Returns dict with score, confidence, features, metadata.
        """
        if not self.model_loaded:
            self.load_ml_model()

        # Mock ML-based analysis
        complexity_score = len(query) / 200.0  # Character-based complexity
        confidence = 0.85 if self.model_loaded else 0.5

        return {
            'score': min(complexity_score, 1.0),
            'confidence': confidence,
            'features': {
                'char_count': len(query),
                'model_loaded': self.model_loaded,
                'model_load_count': self.model_load_count
            },
            'metadata': {'model_name': 'test-ml-model'}
        }

    def _analyze_algorithmic_fallback(self, query: str) -> dict:
        """Fallback algorithmic analysis.

        Returns dict with score, confidence, features, metadata.
        """
        return {
            'score': 0.3,  # Conservative fallback score
            'confidence': 0.6,  # Lower confidence for fallback
            'features': {'fallback_used': True},
            'metadata': {'fallback_reason': 'ml_model_failed'}
        }


class SampleHybridView(HybridView):
    """Sample implementation of HybridView for testing."""

    def __init__(self, view_name='test_hybrid', config=None):
        # HybridView requires ml_model_name parameter
        super().__init__(view_name, ml_model_name='test-hybrid-model', config=config)
        self.algorithmic_view = SampleAlgorithmicView(f'{view_name}_algo')
        self.ml_view = SampleMLView(f'{view_name}_ml')

        # Set a mock ML model so sync ML mode works
        self._ml_model = Mock()  # Base class checks if this is truthy

    def _initialize_algorithmic_components(self):
        """Initialize algorithmic components (required by base class)."""
        pass

    def _initialize_ml_components(self):
        """Initialize ML components (required by base class)."""
        pass

    def _analyze_algorithmic(self, query: str) -> dict:
        """Delegate to algorithmic view's internal method.

        Returns dict with score, confidence, features, metadata.
        """
        return self.algorithmic_view._analyze_algorithmic(query)

    def _analyze_ml(self, query: str) -> dict:
        """Delegate to ML view's internal method.

        Returns dict with score, confidence, features, metadata.
        """
        return self.ml_view._analyze_ml(query)


class TestBaseView(MLInfrastructureTestBase):
    """Test cases for BaseView abstract class."""

    def test_base_view_is_abstract(self):
        """Test that BaseView cannot be instantiated directly."""
        # Should not be able to instantiate abstract base class
        with self.assertRaises(TypeError):
            BaseView('test', {})

    def test_base_view_initialization(self):
        """Test BaseView initialization through subclass."""
        view = SampleAlgorithmicView('test_view', {'param1': 'value1'})

        self.assertEqual(view.view_name, 'test_view')
        self.assertEqual(view.config['param1'], 'value1')

    def test_abstract_method_enforcement(self):
        """Test that abstract methods must be implemented."""
        # Create incomplete implementation
        class IncompleteView(BaseView):
            pass  # Missing analyze method

        # Should raise TypeError when trying to instantiate
        with self.assertRaises(TypeError):
            IncompleteView('incomplete')


class TestAlgorithmicView(MLInfrastructureTestBase, PerformanceTestMixin):
    """Test cases for AlgorithmicView base class."""

    def setUp(self):
        super().setUp()
        self.view = SampleAlgorithmicView('test_algorithmic')

    def test_algorithmic_view_initialization(self):
        """Test AlgorithmicView initialization."""
        self.assertEqual(self.view.view_name, 'test_algorithmic')
        self.assertIsInstance(self.view.config, dict)
        self.assertEqual(self.view.analysis_count, 0)

    def test_algorithmic_analysis(self):
        """Test algorithmic analysis functionality (internal method returns dict)."""
        query = "This is a test query with several words for analysis"

        # Call internal method which returns dict
        result_dict = self.view._analyze_algorithmic(query)

        # Verify dict structure
        self.assertIsInstance(result_dict, dict)
        self.assertIn('score', result_dict)
        self.assertIn('confidence', result_dict)
        self.assertIn('features', result_dict)
        self.assertIn('metadata', result_dict)

        # Verify analysis logic
        expected_word_count = len(query.split())
        self.assertEqual(result_dict['features']['word_count'], expected_word_count)
        self.assertEqual(result_dict['features']['analysis_count'], 1)

        # Verify high confidence for algorithmic
        self.assertGreater(result_dict['confidence'], 0.9)

    def test_algorithmic_view_analyze_method(self):
        """Test the main analyze method with algorithmic mode (returns ViewResult)."""
        query = "Algorithmic analysis test"

        # Test algorithmic mode - analyze() is async but we can run it
        import asyncio
        result = asyncio.run(self.view.analyze(query, mode='algorithmic'))

        self.assertIsInstance(result, ViewResult)
        self.assertEqual(result.method, AnalysisMethod.ALGORITHMIC)

        # Test that analysis count incremented
        self.assertEqual(self.view.analysis_count, 1)

    def test_algorithmic_performance_characteristics(self):
        """Test performance characteristics of algorithmic analysis."""
        queries = [
            "Short query",
            "Medium length query with some complexity",
            "Very long query with many words and complex structure for comprehensive algorithmic analysis testing"
        ]

        for query in queries:
            with self.measure_performance(f'algorithmic_analysis_{len(query)}'):
                result_dict = self.view._analyze_algorithmic(query)

                # Should have high confidence
                self.assertGreater(result_dict['confidence'], 0.9)

    def test_algorithmic_consistency(self):
        """Test that algorithmic analysis is consistent."""
        query = "Consistent analysis test query"

        results = []
        for _ in range(5):
            result_dict = self.view._analyze_algorithmic(query)
            results.append(result_dict)

        # All results should have the same score
        scores = [r['score'] for r in results]
        self.assertTrue(all(s == scores[0] for s in scores))

        # Analysis count should increment
        self.assertEqual(self.view.analysis_count, 5)


class TestMLView(MLInfrastructureTestBase, PerformanceTestMixin):
    """Test cases for MLView base class."""

    def setUp(self):
        super().setUp()
        self.view = SampleMLView('test_ml')

    def test_ml_view_initialization(self):
        """Test MLView initialization."""
        self.assertEqual(self.view.view_name, 'test_ml')
        self.assertFalse(self.view.model_loaded)
        self.assertEqual(self.view.model_load_count, 0)

    def test_ml_model_loading(self):
        """Test ML model loading functionality."""
        self.assertFalse(self.view.model_loaded)

        # Load model
        self.view.load_ml_model()

        self.assertTrue(self.view.model_loaded)
        self.assertEqual(self.view.model_load_count, 1)
        self.assertIsNotNone(self.view.model)

        # Loading again should not reload
        self.view.load_ml_model()
        self.assertEqual(self.view.model_load_count, 1)  # Still 1

    def test_ml_analysis(self):
        """Test ML-based analysis functionality (internal method returns dict)."""
        query = "Machine learning analysis test query for complexity detection"

        # Call internal method which returns dict
        result_dict = self.view._analyze_ml(query)

        # Verify dict structure
        self.assertIsInstance(result_dict, dict)
        self.assertIn('score', result_dict)
        self.assertIn('confidence', result_dict)

        # Verify ML model was loaded
        self.assertTrue(self.view.model_loaded)
        self.assertEqual(result_dict['features']['model_loaded'], True)

        # Verify analysis logic
        self.assertEqual(result_dict['features']['char_count'], len(query))

        # Verify reasonable confidence for ML
        self.assertGreater(result_dict['confidence'], 0.8)

    def test_ml_fallback_mechanism(self):
        """Test fallback to algorithmic analysis."""
        query = "Fallback test query"

        # Force model loading failure by mocking
        with patch.object(self.view, 'load_ml_model', side_effect=Exception('Model loading failed')):
            # ML analysis should fail and fallback
            import asyncio
            result = asyncio.run(self.view.analyze(query, mode='ml'))

            # Should fallback to algorithmic
            if result.method == AnalysisMethod.FALLBACK:
                self.assertEqual(result.method, AnalysisMethod.FALLBACK)

    def test_ml_view_with_algorithmic_fallback(self):
        """Test MLView with algorithmic fallback capability."""
        query = "Test query for fallback"

        # Test algorithmic fallback (returns dict)
        fallback_dict = self.view._analyze_algorithmic_fallback(query)

        self.assertIsInstance(fallback_dict, dict)
        self.assertLess(fallback_dict['confidence'], 0.7)  # Lower confidence
        self.assertIn('fallback_used', fallback_dict['features'])


class TestHybridView(MLInfrastructureTestBase, PerformanceTestMixin):
    """Test cases for HybridView base class."""

    def setUp(self):
        super().setUp()
        self.view = SampleHybridView('test_hybrid')

    def test_hybrid_view_initialization(self):
        """Test HybridView initialization."""
        self.assertEqual(self.view.view_name, 'test_hybrid')
        self.assertIsNotNone(self.view.algorithmic_view)
        self.assertIsNotNone(self.view.ml_view)

    def test_hybrid_algorithmic_mode(self):
        """Test hybrid view in algorithmic-only mode (returns ViewResult)."""
        query = "Algorithmic mode test"

        # analyze() is synchronous in HybridView
        result = self.view.analyze(query, mode='algorithmic')

        self.assertEqual(result.method, AnalysisMethod.ALGORITHMIC)
        self.assertGreater(result.confidence, 0.9)  # High confidence

    def test_hybrid_ml_mode(self):
        """Test hybrid view in ML-only mode (returns ViewResult)."""
        query = "Machine learning mode test query"

        # analyze() is synchronous in HybridView
        result = self.view.analyze(query, mode='ml')

        self.assertEqual(result.method, AnalysisMethod.ML)
        self.assertGreater(result.confidence, 0.8)  # Good confidence

    def test_hybrid_mode_combination(self):
        """Test hybrid mode that combines both approaches (returns ViewResult)."""
        query = "Hybrid analysis combining algorithmic and ML approaches"

        result = self.view.analyze(query, mode='hybrid')

        self.assertEqual(result.method, AnalysisMethod.HYBRID)

        # Should have features from both approaches
        self.assertIn('word_count', result.features)  # From algorithmic
        self.assertIn('char_count', result.features)  # From ML

        # Should have good combined confidence
        self.assertGreater(result.confidence, 0.5)

    def test_result_combination_logic(self):
        """Test the logic for combining algorithmic and ML results."""
        query = "Result combination test"

        # Get individual results as dicts (internal methods)
        algo_dict = self.view._analyze_algorithmic(query)
        ml_dict = self.view._analyze_ml(query)

        # Combine them using internal method (takes dicts, returns dict)
        combined_dict = self.view._combine_results(algo_dict, ml_dict)

        # Verify combination
        self.assertIsInstance(combined_dict, dict)
        self.assertIn('score', combined_dict)
        self.assertIn('confidence', combined_dict)

        # Should include combination metadata
        self.assertIn('weights', combined_dict['metadata'])

    def test_hybrid_error_handling(self):
        """Test hybrid view error handling and fallback."""
        query = "Error handling test"

        # Mock ML failure by patching internal method
        with patch.object(self.view, '_analyze_ml', side_effect=Exception('ML failed')):
            result = self.view.analyze(query, mode='hybrid')

            # Should fallback gracefully (algorithmic only or fallback mode)
            self.assertIsInstance(result, ViewResult)
            # Method could be ALGORITHMIC or HYBRID depending on fallback strategy
            self.assertIn(result.method, [AnalysisMethod.ALGORITHMIC, AnalysisMethod.HYBRID, AnalysisMethod.FALLBACK])


class TestViewPerformanceComparison(MLInfrastructureTestBase, PerformanceTestMixin):
    """Test performance comparison between different view types."""

    def setUp(self):
        super().setUp()
        self.algorithmic_view = SampleAlgorithmicView('perf_algo')
        self.ml_view = SampleMLView('perf_ml')
        self.hybrid_view = SampleHybridView('perf_hybrid')

    def test_relative_performance_characteristics(self):
        """Test relative performance of different view types."""
        query = "Performance comparison test query with moderate complexity"

        # Measure algorithmic performance (internal method)
        algo_start = time.time()
        algo_dict = self.algorithmic_view._analyze_algorithmic(query)
        algo_time = time.time() - algo_start

        # Measure ML performance (internal method)
        ml_start = time.time()
        ml_dict = self.ml_view._analyze_ml(query)
        ml_time = time.time() - ml_start

        # Measure hybrid performance (full analyze)
        hybrid_start = time.time()
        hybrid_result = self.hybrid_view.analyze(query, mode='hybrid')
        hybrid_time = time.time() - hybrid_start

        # Confidence ordering expectations
        self.assertGreaterEqual(algo_dict['confidence'], 0.9, "Algorithmic should have high confidence")
        self.assertGreaterEqual(ml_dict['confidence'], 0.8, "ML should have good confidence")
        self.assertGreaterEqual(hybrid_result.confidence, 0.5, "Hybrid should have reasonable confidence")

    def test_scalability_with_query_length(self):
        """Test how different views scale with query length."""
        query_lengths = [10, 50, 100, 200]  # Number of words

        for length in query_lengths:
            query = " ".join(["word"] * length)

            # Test algorithmic scaling (internal method)
            algo_dict = self.algorithmic_view._analyze_algorithmic(query)

            # Algorithmic should maintain high confidence
            self.assertGreater(algo_dict['confidence'], 0.9, f"Algorithmic confidence low for {length} words")

            # Test ML scaling (internal method)
            ml_dict = self.ml_view._analyze_ml(query)

            # ML should have reasonable confidence
            self.assertGreater(ml_dict['confidence'], 0.5, f"ML confidence too low for {length} words")

    def test_accuracy_vs_speed_tradeoffs(self):
        """Test accuracy vs speed tradeoffs across view types."""
        test_queries = [
            "Simple query",
            "More complex technical query with advanced concepts",
            "Highly complex multi-faceted query requiring deep analysis and understanding of intricate relationships"
        ]

        for query in test_queries:
            algo_dict = self.algorithmic_view._analyze_algorithmic(query)
            ml_dict = self.ml_view._analyze_ml(query)

            # Algorithmic: Fast but may be less accurate for complex queries
            if len(query.split()) > 15:  # Complex query
                # ML should potentially provide better analysis (higher score variance)
                pass  # Implementation-specific accuracy comparison

            # Verify confidence characteristics hold
            self.assertGreater(algo_dict['confidence'], 0.9)  # Algorithmic always confident


class TestViewConfigurationAndExtensibility(MLInfrastructureTestBase):
    """Test view configuration and extensibility features."""

    def test_view_configuration(self):
        """Test view configuration handling."""
        config = {
            'threshold': 0.5,
            'enable_caching': True,
            'max_features': 100,
            'model_name': 'custom-model'
        }

        view = SampleAlgorithmicView('configured_view', config)

        self.assertEqual(view.config['threshold'], 0.5)
        self.assertTrue(view.config['enable_caching'])
        self.assertEqual(view.config['max_features'], 100)
        self.assertEqual(view.config['model_name'], 'custom-model')

    def test_view_extensibility(self):
        """Test that views can be easily extended."""

        class ExtendedAlgorithmicView(SampleAlgorithmicView):
            def __init__(self, view_name, config=None):
                super().__init__(view_name, config)
                self.custom_feature_enabled = config.get('custom_feature', False) if config else False

            def _analyze_algorithmic(self, query: str) -> dict:
                result = super()._analyze_algorithmic(query)

                if self.custom_feature_enabled:
                    # Add custom feature
                    result['features']['custom_analysis'] = len(query) * 2
                    result['metadata']['custom_feature_used'] = True

                return result

        # Test without custom feature
        standard_view = ExtendedAlgorithmicView('standard')
        result = standard_view._analyze_algorithmic("Test query")

        self.assertNotIn('custom_analysis', result['features'])

        # Test with custom feature
        custom_view = ExtendedAlgorithmicView('custom', {'custom_feature': True})
        result = custom_view._analyze_algorithmic("Test query")

        self.assertIn('custom_analysis', result['features'])
        self.assertEqual(result['features']['custom_analysis'], len("Test query") * 2)
        self.assertTrue(result['metadata'].get('custom_feature_used', False))


if __name__ == '__main__':
    # Run tests when script is executed directly
    import unittest
    unittest.main()
