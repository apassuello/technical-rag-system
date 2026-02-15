#!/usr/bin/env python3
"""
Unit tests for FeatureExtractor component.

This module tests the feature extraction functionality of FeatureExtractor,
which is a generic component that can be used by any system requiring
comprehensive linguistic feature analysis.
"""

import pytest
import time

from src.components.query_processors.analyzers.components import FeatureExtractor


class TestFeatureExtractor:
    """Test FeatureExtractor component."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'technical_terms': {
                'domains': ['ml', 'rag'],
                'min_term_length': 3
            },
            'enable_entity_extraction': True
        }
        self.extractor = FeatureExtractor(self.config)
    
    def test_initialization(self):
        """Test proper initialization."""
        assert self.extractor is not None
        assert self.extractor.technical_terms is not None
        assert self.extractor.syntactic_parser is not None
    
    def test_feature_extraction(self):
        """Test comprehensive feature extraction."""
        query = "How does transformer attention mechanism work?"
        features = self.extractor.extract(query)
        
        # Check all feature categories exist (actual implementation uses _features suffix)
        assert 'length_features' in features
        assert 'syntactic_features' in features
        assert 'vocabulary_features' in features
        assert 'question_features' in features
        assert 'ambiguity_features' in features
        assert 'entity_features' in features
        assert 'composite_features' in features
        
        # Check that features are extracted
        assert len(features) > 0
        
        # Check basic structure
        for category in features.values():
            assert isinstance(category, (dict, str, list))
    
    def test_length_features(self):
        """Test length-based features."""
        short = "What is RAG?"
        long = " ".join(["word"] * 50)
        
        short_features = self.extractor.extract(short)['length_features']
        long_features = self.extractor.extract(long)['length_features']
        
        assert short_features['word_count'] < long_features['word_count']
        assert short_features['char_count'] < long_features['char_count']
        # Check normalized features exist
        assert 'word_count_norm' in short_features
        assert 'char_count_norm' in short_features
    
    def test_syntactic_features(self):
        """Test syntactic complexity features."""
        simple = "Simple query"
        complex = "If (this and that), then [something else], otherwise nothing"
        
        simple_features = self.extractor.extract(simple)['syntactic_features']
        complex_features = self.extractor.extract(complex)['syntactic_features']
        
        assert simple_features['clause_density'] < complex_features['clause_density']
        assert simple_features['nesting_depth'] < complex_features['nesting_depth']
        assert simple_features['conjunction_density'] < complex_features['conjunction_density']
    
    def test_vocabulary_features(self):
        """Test vocabulary complexity features."""
        basic = "What is a list?"
        technical = "How does transformer multi-head attention work with embeddings?"
        
        basic_features = self.extractor.extract(basic)['vocabulary_features']
        technical_features = self.extractor.extract(technical)['vocabulary_features']
        
        assert basic_features['technical_density'] < technical_features['technical_density']
        # Check that technical features are properly detected
        assert basic_features['technical_term_count'] < technical_features['technical_term_count']
    
    def test_composite_features(self):
        """Test composite feature calculation."""
        query = "Complex technical query with multiple aspects"
        features = self.extractor.extract(query)
        
        composite = features['composite_features']
        assert 'overall_complexity' in composite
        assert 'technical_depth' in composite
        assert 'structural_complexity' in composite
        assert 0.0 <= composite['overall_complexity'] <= 1.0
    
    def test_performance(self):
        """Test performance meets requirements."""
        query = "How can we optimize transformer-based models for production?"
        
        start = time.time()
        self.extractor.extract(query)
        elapsed = (time.time() - start) * 1000
        
        assert elapsed < 30  # Should be under 30ms


if __name__ == "__main__":
    pytest.main([__file__, "-v"])