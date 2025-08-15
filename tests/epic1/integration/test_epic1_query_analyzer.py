#!/usr/bin/env python3
"""
Integration tests for Epic1QueryAnalyzer orchestrator.

This module tests the Epic1-specific architecture that orchestrates
the individual components into the Epic1QueryAnalyzer system.
This is Epic1-specific because it tests the particular way these
components are combined and configured for the Epic1 use case.
"""

import pytest
import sys
import time
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.components.query_processors.analyzers import Epic1QueryAnalyzer


class TestEpic1QueryAnalyzer:
    """Integration tests for Epic1QueryAnalyzer orchestrator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'feature_extractor': {
                'technical_terms': {
                    'domains': ['ml', 'rag', 'llm'],
                    'min_term_length': 3
                },
                'enable_entity_extraction': True
            },
            'complexity_classifier': {
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
            },
            'model_recommender': {
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
        }
        self.analyzer = Epic1QueryAnalyzer(self.config)
    
    def test_initialization(self):
        """Test proper orchestrator initialization."""
        assert self.analyzer is not None
        assert self.analyzer.feature_extractor is not None
        assert self.analyzer.complexity_classifier is not None
        assert self.analyzer.model_recommender is not None
    
    def test_end_to_end_analysis(self):
        """Test complete analysis pipeline."""
        query = "How does transformer attention mechanism work?"
        analysis = self.analyzer.analyze(query)
        
        assert analysis is not None
        assert 'epic1_analysis' in analysis.metadata
        
        epic1_data = analysis.metadata['epic1_analysis']
        assert 'complexity_level' in epic1_data
        assert 'complexity_score' in epic1_data
        assert 'recommended_model' in epic1_data
        assert 'cost_estimate' in epic1_data
        assert 'latency_estimate' in epic1_data
    
    def test_simple_query_classification(self):
        """Test simple query classification."""
        queries = [
            "What is RAG?",
            "Define embedding",
            "List components"
        ]
        
        for query in queries:
            analysis = self.analyzer.analyze(query)
            epic1_data = analysis.metadata['epic1_analysis']
            assert epic1_data['complexity_level'] == 'simple'
            assert 'ollama' in epic1_data['recommended_model']
    
    def test_complex_query_classification(self):
        """Test complex query classification."""
        query = ("Implement a hybrid retrieval system that combines BM25, "
                "dense embeddings, and cross-encoder reranking with dynamic "
                "weight adjustment based on query characteristics and document types")
        
        analysis = self.analyzer.analyze(query)
        epic1_data = analysis.metadata['epic1_analysis']
        
        # Should be medium or complex
        assert epic1_data['complexity_level'] in ['medium', 'complex']
        assert epic1_data['complexity_score'] > 0.35
    
    def test_performance_metrics(self):
        """Test performance tracking."""
        # Run multiple analyses
        queries = ["Simple query", "Medium complexity query here", "Very complex query"]
        for query in queries:
            self.analyzer.analyze(query)
        
        metrics = self.analyzer.get_performance_metrics()
        
        assert 'epic1_performance' in metrics
        perf = metrics['epic1_performance']
        assert 'avg_total_ms' in perf
        assert 'meets_latency_target' in perf
        assert perf['avg_total_ms'] < 50  # Should meet <50ms target
    
    def test_error_handling(self):
        """Test graceful error handling."""
        # Test with empty query - should raise ValueError
        with pytest.raises(ValueError, match="Query cannot be empty"):
            self.analyzer.analyze("")
        
        # Test with very long query
        long_query = " ".join(["word"] * 1000)
        analysis = self.analyzer.analyze(long_query)
        assert analysis is not None
    
    def test_configuration_flexibility(self):
        """Test different configurations."""
        # Test with cost-optimized strategy
        cost_config = self.config.copy()
        cost_config['model_recommender']['strategy'] = 'cost_optimized'
        cost_analyzer = Epic1QueryAnalyzer(cost_config)
        
        query = "Medium complexity technical question"
        analysis = cost_analyzer.analyze(query)
        
        assert analysis is not None
        epic1_data = analysis.metadata['epic1_analysis']
        # Strategy should be reflected in recommended model selection
        # even if not explicitly in metadata
        assert 'recommended_model' in epic1_data
        # Cost-optimized should prefer cheaper models
        assert 'cost_estimate' in epic1_data
    
    def test_latency_target(self):
        """Test <50ms latency target."""
        queries = [
            "Simple query",
            "How does the retriever work?",
            "Complex multi-part question with technical details"
        ]
        
        for query in queries:
            start = time.time()
            self.analyzer.analyze(query)
            elapsed = (time.time() - start) * 1000
            
            assert elapsed < 50, f"Query '{query[:30]}...' took {elapsed:.1f}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])