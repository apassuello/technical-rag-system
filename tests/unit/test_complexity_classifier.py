#!/usr/bin/env python3
"""
Unit tests for ComplexityClassifier component.

This module tests the complexity classification functionality of ComplexityClassifier,
which is a generic component that can be used by any system requiring
weighted feature classification with configurable thresholds.
"""

import pytest
import sys
import time
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.components.query_processors.analyzers.components import ComplexityClassifier


class TestComplexityClassifier:
    """Test ComplexityClassifier component."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'weights': {
                'length': 0.20,
                'syntactic': 0.25,
                'vocabulary': 0.30,
                'question': 0.15,
                'ambiguity': 0.10
            },
            'thresholds': {
                'simple': 0.35,
                'complex': 0.70
            }
        }
        self.classifier = ComplexityClassifier(self.config)
    
    def test_initialization(self):
        """Test proper initialization."""
        assert self.classifier is not None
        assert sum(self.classifier.weights.values()) == pytest.approx(1.0, 0.01)
        assert self.classifier.thresholds['simple'] < self.classifier.thresholds['complex']
    
    def test_score_calculation(self):
        """Test weighted score calculation."""
        features = {
            'length': {'normalized': 0.5},
            'syntactic': {'normalized': 0.6},
            'vocabulary': {'complexity_score': 0.7},
            'question': {'complexity': 0.4},
            'ambiguity': {'score': 0.3}
        }
        
        result = self.classifier.classify(features)
        
        assert 'complexity_score' in result
        assert 'complexity_level' in result
        assert 'confidence' in result
        assert 'breakdown' in result
        
        # Check weighted calculation
        expected = (0.5 * 0.20 + 0.6 * 0.25 + 0.7 * 0.30 + 0.4 * 0.15 + 0.3 * 0.10)
        assert result['complexity_score'] == pytest.approx(expected, 0.01)
    
    def test_level_classification(self):
        """Test complexity level assignment."""
        # Simple query features
        simple_features = {
            'length': {'normalized': 0.1},
            'syntactic': {'normalized': 0.1},
            'vocabulary': {'complexity_score': 0.1},
            'question': {'complexity': 0.1},
            'ambiguity': {'score': 0.1}
        }
        
        # Complex query features
        complex_features = {
            'length': {'normalized': 0.8},
            'syntactic': {'normalized': 0.9},
            'vocabulary': {'complexity_score': 0.9},
            'question': {'complexity': 0.8},
            'ambiguity': {'score': 0.7}
        }
        
        simple_result = self.classifier.classify(simple_features)
        complex_result = self.classifier.classify(complex_features)
        
        assert simple_result['complexity_level'] == 'simple'
        assert complex_result['complexity_level'] == 'complex'
    
    def test_confidence_scoring(self):
        """Test confidence calculation based on threshold distance."""
        # Score close to threshold should have lower confidence
        borderline_features = {
            'length': {'normalized': 0.35},
            'syntactic': {'normalized': 0.35},
            'vocabulary': {'complexity_score': 0.35},
            'question': {'complexity': 0.35},
            'ambiguity': {'score': 0.35}
        }
        
        # Score far from threshold should have higher confidence
        clear_features = {
            'length': {'normalized': 0.1},
            'syntactic': {'normalized': 0.1},
            'vocabulary': {'complexity_score': 0.1},
            'question': {'complexity': 0.1},
            'ambiguity': {'score': 0.1}
        }
        
        borderline_result = self.classifier.classify(borderline_features)
        clear_result = self.classifier.classify(clear_features)
        
        assert clear_result['confidence'] > borderline_result['confidence']
    
    def test_breakdown_generation(self):
        """Test breakdown by category."""
        features = {
            'length': {'normalized': 0.5},
            'syntactic': {'normalized': 0.6},
            'vocabulary': {'complexity_score': 0.7},
            'question': {'complexity': 0.4},
            'ambiguity': {'score': 0.3}
        }
        
        result = self.classifier.classify(features)
        breakdown = result['breakdown']
        
        assert 'length' in breakdown
        assert 'syntactic' in breakdown
        assert 'vocabulary' in breakdown
        assert 'question' in breakdown
        assert 'ambiguity' in breakdown
        
        # Check weighted scores
        assert breakdown['length'] == pytest.approx(0.5 * 0.20, 0.01)
    
    def test_performance(self):
        """Test performance meets requirements."""
        features = {
            'length': {'normalized': 0.5},
            'syntactic': {'normalized': 0.6},
            'vocabulary': {'complexity_score': 0.7},
            'question': {'complexity': 0.4},
            'ambiguity': {'score': 0.3}
        }
        
        start = time.time()
        self.classifier.classify(features)
        elapsed = (time.time() - start) * 1000
        
        assert elapsed < 10  # Should be under 10ms


if __name__ == "__main__":
    pytest.main([__file__, "-v"])