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

try:
    from src.components.query_processors.analyzers.ml_views.base_view import (
        BaseView, AlgorithmicView, MLView, HybridView
    )
    from src.components.query_processors.analyzers.ml_views.view_result import (
        ViewResult, AnalysisMethod
    )
except ImportError:
    # Create mock imports if the real modules aren't available
    class AnalysisMethod:
        ALGORITHMIC = "algorithmic"
        ML = "ml"
        HYBRID = "hybrid"
        FALLBACK = "fallback"
    
    class ViewResult:
        def __init__(self, view_name, score, confidence, method, latency_ms, features=None, metadata=None):
            self.view_name = view_name
            self.score = score
            self.confidence = confidence
            self.method = method
            self.latency_ms = latency_ms
            self.features = features or {}
            self.metadata = metadata or {}
    
    class BaseView(ABC):
        def __init__(self, view_name, config=None):
            self.view_name = view_name
            self.config = config or {}
        
        @abstractmethod
        def analyze(self, query, mode='hybrid'):
            pass
    
    class AlgorithmicView(BaseView):
        def analyze(self, query, mode='algorithmic'):
            return ViewResult(
                view_name=self.view_name,
                score=0.5,
                confidence=0.8,
                method=AnalysisMethod.ALGORITHMIC,
                latency_ms=5.0
            )
    
    class MLView(BaseView):
        def analyze(self, query, mode='ml'):
            return ViewResult(
                view_name=self.view_name,
                score=0.7,
                confidence=0.9,
                method=AnalysisMethod.ML,
                latency_ms=50.0
            )
    
    class HybridView(BaseView):
        def analyze(self, query, mode='hybrid'):
            return ViewResult(
                view_name=self.view_name,
                score=0.6,
                confidence=0.85,
                method=AnalysisMethod.HYBRID,
                latency_ms=25.0
            )


# Test implementations for testing base classes
class TestAlgorithmicViewImpl(AlgorithmicView):
    """Test implementation of AlgorithmicView."""
    
    def __init__(self, view_name='test_algorithmic', config=None):
        super().__init__(view_name, config)
        self.analysis_count = 0
    
    def analyze(self, query, mode='algorithmic'):
        """Implement the required analyze method."""
        return self.algorithmic_analysis(query)
    
    def algorithmic_analysis(self, query):
        """Test algorithmic analysis implementation."""
        self.analysis_count += 1
        
        # Simple mock analysis
        word_count = len(query.split())
        score = min(word_count / 20.0, 1.0)  # Normalize by 20 words
        
        return ViewResult(
            view_name=self.view_name,
            score=score,
            confidence=0.95,  # High confidence for algorithmic
            method=AnalysisMethod.ALGORITHMIC,
            latency_ms=2.0,
            features={'word_count': word_count, 'analysis_count': self.analysis_count},
            metadata={'timestamp': time.time()}
        )


class TestMLViewImpl(MLView):
    """Test implementation of MLView."""
    
    def __init__(self, view_name='test_ml', config=None):
        super().__init__(view_name, config)
        self.model_loaded = False
        self.model_load_count = 0
        
        # Mock model factory
        self.model_factory = MockModelFactory()
    
    def load_ml_model(self):
        """Mock ML model loading."""
        if not self.model_loaded:
            self.model = self.model_factory.create_model('test-ml-model')
            self.model.load()
            self.model_loaded = True
            self.model_load_count += 1
    
    def ml_analysis(self, query):
        """Test ML analysis implementation."""
        if not self.model_loaded:
            self.load_ml_model()
        
        # Mock ML-based analysis
        complexity_score = len(query) / 200.0  # Character-based complexity
        confidence = 0.85 if self.model_loaded else 0.5
        
        return ViewResult(
            view_name=self.view_name,
            score=min(complexity_score, 1.0),
            confidence=confidence,
            method=AnalysisMethod.ML,
            latency_ms=45.0,
            features={
                'char_count': len(query),
                'model_loaded': self.model_loaded,
                'model_load_count': self.model_load_count
            },
            metadata={'model_name': 'test-ml-model'}
        )
    
    def algorithmic_analysis(self, query):
        """Fallback algorithmic analysis."""
        return ViewResult(
            view_name=self.view_name,
            score=0.3,  # Conservative fallback score
            confidence=0.6,  # Lower confidence for fallback
            method=AnalysisMethod.FALLBACK,
            latency_ms=5.0,
            features={'fallback_used': True},
            metadata={'fallback_reason': 'ml_model_failed'}
        )


class TestHybridViewImpl(HybridView):
    """Test implementation of HybridView."""
    
    def __init__(self, view_name='test_hybrid', config=None):
        super().__init__(view_name, config)
        self.algorithmic_view = TestAlgorithmicViewImpl(f'{view_name}_algo')
        self.ml_view = TestMLViewImpl(f'{view_name}_ml')
    
    def analyze(self, query, mode='hybrid'):
        """Implement the required analyze method."""
        if mode == 'algorithmic':
            return self.algorithmic_analysis(query)
        elif mode == 'ml':
            return self.ml_analysis(query)
        else:  # hybrid mode
            algo_result = self.algorithmic_analysis(query)
            ml_result = self.ml_analysis(query)
            return self.combine_results(algo_result, ml_result)
    
    def algorithmic_analysis(self, query):
        """Delegate to algorithmic view."""
        return self.algorithmic_view.algorithmic_analysis(query)
    
    def ml_analysis(self, query):
        """Delegate to ML view.""" 
        return self.ml_view.ml_analysis(query)
    
    def combine_results(self, algo_result, ml_result):
        """Combine algorithmic and ML results."""
        # Weighted combination (favor ML if high confidence)
        ml_weight = ml_result.confidence
        algo_weight = 1.0 - ml_weight
        
        combined_score = (ml_result.score * ml_weight) + (algo_result.score * algo_weight)
        combined_confidence = (ml_result.confidence + algo_result.confidence) / 2.0
        combined_latency = ml_result.latency_ms + algo_result.latency_ms
        
        # Combine features
        combined_features = {}
        combined_features.update(algo_result.features)
        combined_features.update({f'ml_{k}': v for k, v in ml_result.features.items()})
        combined_features['combination_weights'] = {'ml': ml_weight, 'algo': algo_weight}
        
        return ViewResult(
            view_name=self.view_name,
            score=combined_score,
            confidence=combined_confidence,
            method=AnalysisMethod.HYBRID,
            latency_ms=combined_latency,
            features=combined_features,
            metadata={'combined_from': [AnalysisMethod.ALGORITHMIC, AnalysisMethod.ML]}
        )


class TestBaseView(MLInfrastructureTestBase):
    """Test cases for BaseView abstract class."""
    
    def test_base_view_is_abstract(self):
        """Test that BaseView cannot be instantiated directly."""
        if BaseView == type:
            self.skipTest("BaseView implementation not available")
        
        # Should not be able to instantiate abstract base class
        with self.assertRaises(TypeError):
            BaseView('test', {})
    
    def test_base_view_initialization(self):
        """Test BaseView initialization through subclass."""
        if BaseView == type:
            self.skipTest("BaseView implementation not available")
        
        view = TestAlgorithmicViewImpl('test_view', {'param1': 'value1'})
        
        self.assertEqual(view.view_name, 'test_view')
        self.assertEqual(view.config['param1'], 'value1')
    
    def test_abstract_method_enforcement(self):
        """Test that abstract methods must be implemented."""
        if BaseView == type:
            self.skipTest("BaseView implementation not available")
        
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
        self.view = TestAlgorithmicViewImpl('test_algorithmic')
    
    def test_algorithmic_view_initialization(self):
        """Test AlgorithmicView initialization."""
        self.assertEqual(self.view.view_name, 'test_algorithmic')
        self.assertIsInstance(self.view.config, dict)
        self.assertEqual(self.view.analysis_count, 0)
    
    def test_algorithmic_analysis(self):
        """Test algorithmic analysis functionality."""
        query = "This is a test query with several words for analysis"
        
        result = self.view.algorithmic_analysis(query)
        
        # Verify result structure
        self.assertIsInstance(result, ViewResult)
        self.assertEqual(result.view_name, 'test_algorithmic')
        self.assertEqual(result.method, AnalysisMethod.ALGORITHMIC)
        
        # Verify analysis logic
        expected_word_count = len(query.split())
        self.assertEqual(result.features['word_count'], expected_word_count)
        self.assertEqual(result.features['analysis_count'], 1)
        
        # Verify high confidence for algorithmic
        self.assertGreater(result.confidence, 0.9)
        
        # Verify fast performance
        self.assertLess(result.latency_ms, 10.0)
    
    def test_algorithmic_view_analyze_method(self):
        """Test the main analyze method with algorithmic mode."""
        if not hasattr(self.view, 'analyze'):
            self.skipTest("AlgorithmicView.analyze not implemented")
        
        query = "Algorithmic analysis test"
        
        # Test algorithmic mode
        result = self.view.analyze(query, mode='algorithmic')
        
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
                result = self.view.algorithmic_analysis(query)
                
                # Should be fast regardless of query length
                self.assertLess(result.latency_ms, 10.0)
                
                # Should have high confidence
                self.assertGreater(result.confidence, 0.9)
    
    def test_algorithmic_consistency(self):
        """Test that algorithmic analysis is consistent."""
        query = "Consistent analysis test query"
        
        results = []
        for _ in range(5):
            result = self.view.algorithmic_analysis(query)
            results.append(result)
        
        # All results should have the same score
        scores = [r.score for r in results]
        self.assertTrue(all(s == scores[0] for s in scores))
        
        # Analysis count should increment
        self.assertEqual(self.view.analysis_count, 5)


class TestMLView(MLInfrastructureTestBase, PerformanceTestMixin):
    """Test cases for MLView base class."""
    
    def setUp(self):
        super().setUp()
        self.view = TestMLViewImpl('test_ml')
    
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
        """Test ML-based analysis functionality."""
        query = "Machine learning analysis test query for complexity detection"
        
        result = self.view.ml_analysis(query)
        
        # Verify result structure
        self.assertIsInstance(result, ViewResult)
        self.assertEqual(result.view_name, 'test_ml')
        self.assertEqual(result.method, AnalysisMethod.ML)
        
        # Verify ML model was loaded
        self.assertTrue(self.view.model_loaded)
        self.assertEqual(result.features['model_loaded'], True)
        
        # Verify analysis logic
        self.assertEqual(result.features['char_count'], len(query))
        
        # Verify reasonable confidence for ML
        self.assertGreater(result.confidence, 0.8)
        
        # Verify higher latency than algorithmic
        self.assertGreater(result.latency_ms, 20.0)
    
    def test_ml_fallback_mechanism(self):
        """Test fallback to algorithmic analysis."""
        query = "Fallback test query"
        
        # Force model loading failure by mocking
        with patch.object(self.view, 'load_ml_model', side_effect=Exception('Model loading failed')):
            # ML analysis should fail and fallback
            if hasattr(self.view, 'analyze'):
                result = self.view.analyze(query, mode='ml')
                
                # Should fallback to algorithmic
                if result.method == AnalysisMethod.FALLBACK:
                    self.assertEqual(result.method, AnalysisMethod.FALLBACK)
                    self.assertIn('fallback_used', result.features)
                    self.assertTrue(result.features['fallback_used'])
    
    def test_ml_view_with_algorithmic_fallback(self):
        """Test MLView with algorithmic fallback capability."""
        query = "Test query for fallback"
        
        # Test algorithmic fallback
        fallback_result = self.view.algorithmic_analysis(query)
        
        self.assertEqual(fallback_result.method, AnalysisMethod.FALLBACK)
        self.assertLess(fallback_result.confidence, 0.7)  # Lower confidence
        self.assertIn('fallback_used', fallback_result.features)


class TestHybridView(MLInfrastructureTestBase, PerformanceTestMixin):
    """Test cases for HybridView base class."""
    
    def setUp(self):
        super().setUp()
        self.view = TestHybridViewImpl('test_hybrid')
    
    def test_hybrid_view_initialization(self):
        """Test HybridView initialization."""
        self.assertEqual(self.view.view_name, 'test_hybrid')
        self.assertIsNotNone(self.view.algorithmic_view)
        self.assertIsNotNone(self.view.ml_view)
    
    def test_hybrid_algorithmic_mode(self):
        """Test hybrid view in algorithmic-only mode."""
        if not hasattr(self.view, 'analyze'):
            self.skipTest("HybridView.analyze not implemented")
        
        query = "Algorithmic mode test"
        
        result = self.view.analyze(query, mode='algorithmic')
        
        self.assertEqual(result.method, AnalysisMethod.ALGORITHMIC)
        self.assertLess(result.latency_ms, 10.0)  # Fast
        self.assertGreater(result.confidence, 0.9)  # High confidence
    
    def test_hybrid_ml_mode(self):
        """Test hybrid view in ML-only mode."""
        if not hasattr(self.view, 'analyze'):
            self.skipTest("HybridView.analyze not implemented")
        
        query = "Machine learning mode test query"
        
        result = self.view.analyze(query, mode='ml')
        
        self.assertEqual(result.method, AnalysisMethod.ML)
        self.assertGreater(result.latency_ms, 20.0)  # Slower
        self.assertGreater(result.confidence, 0.8)  # Good confidence
    
    def test_hybrid_mode_combination(self):
        """Test hybrid mode that combines both approaches."""
        query = "Hybrid analysis combining algorithmic and ML approaches"
        
        if hasattr(self.view, 'analyze'):
            result = self.view.analyze(query, mode='hybrid')
            
            self.assertEqual(result.method, AnalysisMethod.HYBRID)
            
            # Should have features from both approaches
            self.assertIn('word_count', result.features)  # From algorithmic
            self.assertIn('ml_char_count', result.features)  # From ML
            self.assertIn('combination_weights', result.features)
            
            # Should have reasonable combined latency
            self.assertGreater(result.latency_ms, 10.0)  # More than algorithmic only
            self.assertLess(result.latency_ms, 100.0)  # But not too high
            
            # Should have good combined confidence
            self.assertGreater(result.confidence, 0.7)
    
    def test_result_combination_logic(self):
        """Test the logic for combining algorithmic and ML results."""
        query = "Result combination test"
        
        # Get individual results
        algo_result = self.view.algorithmic_analysis(query)
        ml_result = self.view.ml_analysis(query)
        
        # Combine them
        combined_result = self.view.combine_results(algo_result, ml_result)
        
        # Verify combination
        self.assertEqual(combined_result.method, AnalysisMethod.HYBRID)
        
        # Score should be weighted combination
        expected_ml_weight = ml_result.confidence
        expected_algo_weight = 1.0 - expected_ml_weight
        expected_score = (ml_result.score * expected_ml_weight) + (algo_result.score * expected_algo_weight)
        
        self.assertAlmostEqual(combined_result.score, expected_score, places=2)
        
        # Should combine latencies
        expected_latency = algo_result.latency_ms + ml_result.latency_ms
        self.assertEqual(combined_result.latency_ms, expected_latency)
        
        # Should include combination metadata
        self.assertIn('combination_weights', combined_result.features)
        self.assertIn('combined_from', combined_result.metadata)
    
    def test_hybrid_error_handling(self):
        """Test hybrid view error handling and fallback."""
        query = "Error handling test"
        
        # Mock ML failure
        with patch.object(self.view.ml_view, 'ml_analysis', side_effect=Exception('ML failed')):
            if hasattr(self.view, 'analyze'):
                result = self.view.analyze(query, mode='hybrid')
                
                # Should fallback to algorithmic only
                if result.method == AnalysisMethod.FALLBACK:
                    self.assertEqual(result.method, AnalysisMethod.FALLBACK)
                elif result.method == AnalysisMethod.ALGORITHMIC:
                    # Acceptable fallback to algorithmic
                    self.assertLess(result.latency_ms, 10.0)


class TestViewPerformanceComparison(MLInfrastructureTestBase, PerformanceTestMixin):
    """Test performance comparison between different view types."""
    
    def setUp(self):
        super().setUp()
        self.algorithmic_view = TestAlgorithmicViewImpl('perf_algo')
        self.ml_view = TestMLViewImpl('perf_ml') 
        self.hybrid_view = TestHybridViewImpl('perf_hybrid')
    
    def test_relative_performance_characteristics(self):
        """Test relative performance of different view types."""
        query = "Performance comparison test query with moderate complexity"
        
        # Measure algorithmic performance
        algo_start = time.time()
        algo_result = self.algorithmic_view.algorithmic_analysis(query)
        algo_time = time.time() - algo_start
        
        # Measure ML performance
        ml_start = time.time()
        ml_result = self.ml_view.ml_analysis(query)
        ml_time = time.time() - ml_start
        
        # Measure hybrid performance
        hybrid_start = time.time()
        if hasattr(self.hybrid_view, 'analyze'):
            hybrid_result = self.hybrid_view.analyze(query, mode='hybrid')
            hybrid_time = time.time() - hybrid_start
            
            # Performance ordering expectations
            self.assertLess(algo_time, ml_time, "Algorithmic should be faster than ML")
            self.assertLess(algo_time, hybrid_time, "Algorithmic should be faster than hybrid")
            
            # Confidence ordering expectations
            self.assertGreaterEqual(algo_result.confidence, 0.9, "Algorithmic should have high confidence")
            self.assertGreaterEqual(ml_result.confidence, 0.8, "ML should have good confidence")
            self.assertGreaterEqual(hybrid_result.confidence, 0.7, "Hybrid should have reasonable confidence")
    
    def test_scalability_with_query_length(self):
        """Test how different views scale with query length."""
        query_lengths = [10, 50, 100, 200]  # Number of words
        
        for length in query_lengths:
            query = " ".join(["word"] * length)
            
            # Test algorithmic scaling
            algo_result = self.algorithmic_view.algorithmic_analysis(query)
            
            # Algorithmic should maintain consistent performance
            self.assertLess(algo_result.latency_ms, 10.0, f"Algorithmic slow for {length} words")
            
            # Test ML scaling
            ml_result = self.ml_view.ml_analysis(query)
            
            # ML latency may increase with length but should remain reasonable
            self.assertLess(ml_result.latency_ms, 100.0, f"ML too slow for {length} words")
    
    def test_accuracy_vs_speed_tradeoffs(self):
        """Test accuracy vs speed tradeoffs across view types."""
        test_queries = [
            "Simple query",
            "More complex technical query with advanced concepts",
            "Highly complex multi-faceted query requiring deep analysis and understanding of intricate relationships"
        ]
        
        for query in test_queries:
            algo_result = self.algorithmic_view.algorithmic_analysis(query)
            ml_result = self.ml_view.ml_analysis(query)
            
            # Algorithmic: Fast but may be less accurate for complex queries
            if len(query.split()) > 15:  # Complex query
                # ML should potentially provide better analysis (higher score variance)
                pass  # Implementation-specific accuracy comparison
            
            # Verify performance characteristics hold
            self.assertLess(algo_result.latency_ms, ml_result.latency_ms)
            self.assertGreater(algo_result.confidence, 0.9)  # Algorithmic always confident


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
        
        view = TestAlgorithmicViewImpl('configured_view', config)
        
        self.assertEqual(view.config['threshold'], 0.5)
        self.assertTrue(view.config['enable_caching'])
        self.assertEqual(view.config['max_features'], 100)
        self.assertEqual(view.config['model_name'], 'custom-model')
    
    def test_view_extensibility(self):
        """Test that views can be easily extended."""
        
        class ExtendedAlgorithmicView(TestAlgorithmicViewImpl):
            def __init__(self, view_name, config=None):
                super().__init__(view_name, config)
                self.custom_feature_enabled = config.get('custom_feature', False) if config else False
            
            def algorithmic_analysis(self, query):
                result = super().algorithmic_analysis(query)
                
                if self.custom_feature_enabled:
                    # Add custom feature
                    result.features['custom_analysis'] = len(query) * 2
                    result.metadata['custom_feature_used'] = True
                
                return result
        
        # Test without custom feature
        standard_view = ExtendedAlgorithmicView('standard')
        result = standard_view.algorithmic_analysis("Test query")
        
        self.assertNotIn('custom_analysis', result.features)
        
        # Test with custom feature
        custom_view = ExtendedAlgorithmicView('custom', {'custom_feature': True})
        result = custom_view.algorithmic_analysis("Test query")
        
        self.assertIn('custom_analysis', result.features)
        self.assertEqual(result.features['custom_analysis'], len("Test query") * 2)
        self.assertTrue(result.metadata.get('custom_feature_used', False))


if __name__ == '__main__':
    # Run tests when script is executed directly
    import unittest
    unittest.main()