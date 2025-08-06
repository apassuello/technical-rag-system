#!/usr/bin/env python3
"""
Unit tests for FeatureExtractor component.

This module tests the feature extraction functionality of FeatureExtractor,
which is a generic component that can be used by any system requiring
comprehensive linguistic feature analysis.
"""

import pytest
import sys
import time
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

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
        
        # Check all feature categories exist
        assert 'length' in features
        assert 'syntactic' in features
        assert 'vocabulary' in features
        assert 'question' in features
        assert 'ambiguity' in features
        assert 'entities' in features
        assert 'composite' in features
        
        # Check normalization
        for category in features.values():
            if isinstance(category, dict):
                for value in category.values():
                    if isinstance(value, (int, float)):
                        assert 0.0 <= value <= 1.0
    
    def test_length_features(self):
        """Test length-based features."""
        short = "What is RAG?"
        long = " ".join(["word"] * 50)
        
        short_features = self.extractor.extract(short)['length']
        long_features = self.extractor.extract(long)['length']
        
        assert short_features['word_count'] < long_features['word_count']
        assert short_features['char_count'] < long_features['char_count']
        assert short_features['normalized'] < long_features['normalized']
    
    def test_syntactic_features(self):
        """Test syntactic complexity features."""
        simple = "Simple query"
        complex = "If (this and that), then [something else], otherwise nothing"
        
        simple_features = self.extractor.extract(simple)['syntactic']
        complex_features = self.extractor.extract(complex)['syntactic']
        
        assert simple_features['clause_density'] < complex_features['clause_density']
        assert simple_features['nesting_depth'] < complex_features['nesting_depth']
        assert simple_features['conjunction_density'] < complex_features['conjunction_density']
    
    def test_vocabulary_features(self):
        """Test vocabulary complexity features."""
        basic = "What is a list?"
        technical = "How does transformer multi-head attention work with embeddings?"
        
        basic_features = self.extractor.extract(basic)['vocabulary']
        technical_features = self.extractor.extract(technical)['vocabulary']
        
        assert basic_features['technical_density'] < technical_features['technical_density']
        assert basic_features['complexity_score'] < technical_features['complexity_score']
    
    def test_composite_features(self):
        """Test composite feature calculation."""
        query = "Complex technical query with multiple aspects"
        features = self.extractor.extract(query)
        
        composite = features['composite']
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