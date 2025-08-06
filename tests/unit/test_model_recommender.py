#!/usr/bin/env python3
"""
Unit tests for ModelRecommender component.

This module tests the model recommendation functionality of ModelRecommender,
which is a generic component that can be used by any system requiring
intelligent model selection based on complexity levels and routing strategies.
"""

import pytest
import sys
import time
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.components.query_processors.analyzers.components import ModelRecommender


class TestModelRecommender:
    """Test ModelRecommender component."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'strategy': 'balanced',
            'model_mappings': {
                'simple': {
                    'provider': 'ollama',
                    'model': 'llama3.2:3b',
                    'max_cost_per_query': 0.001,
                    'avg_latency_ms': 500
                },
                'medium': {
                    'provider': 'mistral',
                    'model': 'mistral-small',
                    'max_cost_per_query': 0.01,
                    'avg_latency_ms': 1000
                },
                'complex': {
                    'provider': 'openai',
                    'model': 'gpt-4-turbo',
                    'max_cost_per_query': 0.10,
                    'avg_latency_ms': 2000
                }
            }
        }
        self.recommender = ModelRecommender(self.config)
    
    def test_initialization(self):
        """Test proper initialization."""
        assert self.recommender is not None
        assert self.recommender.strategy == 'balanced'
        assert 'simple' in self.recommender.model_mappings
        assert 'medium' in self.recommender.model_mappings
        assert 'complex' in self.recommender.model_mappings
    
    def test_model_selection(self):
        """Test model selection based on complexity."""
        simple_result = self.recommender.recommend('simple', 0.2, 0.9)
        medium_result = self.recommender.recommend('medium', 0.5, 0.8)
        complex_result = self.recommender.recommend('complex', 0.8, 0.9)
        
        assert simple_result['model'] == 'ollama:llama3.2:3b'
        assert medium_result['model'] == 'mistral:mistral-small'
        assert complex_result['model'] == 'openai:gpt-4-turbo'
    
    def test_cost_estimation(self):
        """Test cost estimation."""
        result = self.recommender.recommend('complex', 0.8, 0.9)
        
        assert 'cost_estimate' in result
        assert result['cost_estimate'] == 0.10
    
    def test_latency_estimation(self):
        """Test latency estimation."""
        result = self.recommender.recommend('simple', 0.2, 0.9)
        
        assert 'latency_estimate' in result
        assert result['latency_estimate'] == 500
    
    def test_fallback_recommendations(self):
        """Test fallback chain generation."""
        result = self.recommender.recommend('complex', 0.8, 0.9)
        
        assert 'fallback_models' in result
        assert len(result['fallback_models']) > 0
        assert result['fallback_models'][0] != result['model']
    
    def test_strategy_selection(self):
        """Test different routing strategies."""
        # Cost optimized strategy
        cost_config = self.config.copy()
        cost_config['strategy'] = 'cost_optimized'
        cost_recommender = ModelRecommender(cost_config)
        
        # Quality first strategy
        quality_config = self.config.copy()
        quality_config['strategy'] = 'quality_first'
        quality_recommender = ModelRecommender(quality_config)
        
        # For medium complexity, strategies might differ
        cost_result = cost_recommender.recommend('medium', 0.5, 0.8)
        quality_result = quality_recommender.recommend('medium', 0.5, 0.8)
        
        # Cost optimized might prefer cheaper model
        # Quality first might prefer better model
        assert cost_result is not None
        assert quality_result is not None
    
    def test_recommendation_metadata(self):
        """Test recommendation metadata generation."""
        result = self.recommender.recommend('medium', 0.5, 0.8)
        
        assert 'provider' in result
        assert 'model_name' in result
        assert 'strategy_used' in result
        assert 'confidence' in result
        assert result['strategy_used'] == 'balanced'
    
    def test_performance(self):
        """Test performance meets requirements."""
        start = time.time()
        self.recommender.recommend('medium', 0.5, 0.8)
        elapsed = (time.time() - start) * 1000
        
        assert elapsed < 5  # Should be under 5ms


if __name__ == "__main__":
    pytest.main([__file__, "-v"])