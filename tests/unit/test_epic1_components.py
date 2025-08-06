#!/usr/bin/env python3
"""
Comprehensive unit tests for Epic 1 Query Analyzer components.

This module tests all sub-components of the Epic1QueryAnalyzer including:
- TechnicalTermManager (utils/technical_terms.py)
- SyntacticParser (utils/syntactic_parser.py)
- FeatureExtractor (components/feature_extractor.py)
- ComplexityClassifier (components/complexity_classifier.py)
- ModelRecommender (components/model_recommender.py)
"""

import pytest
import sys
from pathlib import Path
import time

# Add project to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.components.query_processors.analyzers.utils import (
    TechnicalTermManager,
    SyntacticParser
)
from src.components.query_processors.analyzers.components import (
    FeatureExtractor,
    ComplexityClassifier,
    ModelRecommender
)


class TestTechnicalTermManager:
    """Test TechnicalTermManager utility."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'domains': ['ml', 'rag', 'llm'],
            'min_term_length': 3,
            'case_sensitive': False
        }
        self.manager = TechnicalTermManager(self.config)
    
    def test_initialization(self):
        """Test proper initialization."""
        assert self.manager is not None
        assert len(self.manager.terms) > 0
        assert 'ml' in self.manager.domain_terms
        assert 'rag' in self.manager.domain_terms
        assert 'llm' in self.manager.domain_terms
    
    def test_contains_term(self):
        """Test term detection."""
        # Should detect known ML terms
        assert self.manager.contains_term('transformer')
        assert self.manager.contains_term('embedding')
        assert self.manager.contains_term('neural')
        
        # Should not detect non-technical terms
        assert not self.manager.contains_term('hello')
        assert not self.manager.contains_term('the')
        assert not self.manager.contains_term('is')
        
        # Test minimum length
        assert not self.manager.contains_term('ai')  # Too short
    
    def test_extract_terms(self):
        """Test term extraction from text."""
        text = "The transformer architecture uses attention mechanisms for embeddings"
        terms = self.manager.extract_terms(text)
        
        assert 'transformer' in terms
        assert 'attention' in terms
        assert 'embeddings' in terms or 'embedding' in terms
    
    def test_pattern_detection(self):
        """Test pattern-based technical term detection."""
        text = "We use GPT-4 and BERT-base models with F1-score metrics"
        terms = self.manager.extract_terms(text)
        
        # Should detect model names and metrics
        assert any('GPT' in term for term in terms)
        assert any('BERT' in term for term in terms)
        assert any('F1' in term for term in terms)
    
    def test_calculate_metrics(self):
        """Test metric calculation."""
        text = "How does transformer attention work with embeddings?"
        metrics = self.manager.calculate_metrics(text)
        
        assert 'technical_density' in metrics
        assert 'domain_coverage' in metrics
        assert 'pattern_matches' in metrics
        assert 0.0 <= metrics['technical_density'] <= 1.0
    
    def test_performance(self):
        """Test performance meets requirements."""
        text = "The transformer model uses multi-head attention for sequence-to-sequence tasks"
        
        start = time.time()
        self.manager.extract_terms(text)
        elapsed = (time.time() - start) * 1000
        
        assert elapsed < 5  # Should be under 5ms


class TestSyntacticParser:
    """Test SyntacticParser utility."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = SyntacticParser()
    
    def test_clause_detection(self):
        """Test clause counting."""
        assert self.parser.count_clauses("Simple sentence") == 1
        assert self.parser.count_clauses("First clause, and second clause") == 2
        assert self.parser.count_clauses("If this, then that, otherwise something else") == 3
    
    def test_nesting_depth(self):
        """Test nesting depth calculation."""
        assert self.parser.calculate_nesting_depth("Simple") == 0
        assert self.parser.calculate_nesting_depth("(nested)") == 1
        assert self.parser.calculate_nesting_depth("(outer (inner))") == 2
        assert self.parser.calculate_nesting_depth("[a [b [c]]]") == 3
    
    def test_conjunction_detection(self):
        """Test conjunction counting."""
        assert self.parser.count_conjunctions("Simple") == 0
        assert self.parser.count_conjunctions("This and that") == 1
        assert self.parser.count_conjunctions("A and B or C but D") == 3
    
    def test_question_classification(self):
        """Test question type detection."""
        assert self.parser.classify_question("What is RAG?") == 'what'
        assert self.parser.classify_question("How does it work?") == 'how'
        assert self.parser.classify_question("Why use embeddings?") == 'why'
        assert self.parser.classify_question("When should we apply?") == 'when'
        assert self.parser.classify_question("Is it efficient?") == 'yes_no'
        assert self.parser.classify_question("Compare A and B") == 'compare'
        assert self.parser.classify_question("Implement a solution") == 'action'
        assert self.parser.classify_question("Random text") == 'unknown'
    
    def test_punctuation_complexity(self):
        """Test punctuation complexity scoring."""
        assert self.parser.calculate_punctuation_complexity("Simple") == 0.0
        assert self.parser.calculate_punctuation_complexity("A, B, C") > 0
        assert self.parser.calculate_punctuation_complexity("Complex: (a) first; (b) second.") > 0.5
    
    def test_parse_metrics(self):
        """Test comprehensive parsing."""
        text = "How does the transformer model, which uses attention mechanisms, work?"
        metrics = self.parser.parse(text)
        
        assert 'clause_count' in metrics
        assert 'nesting_depth' in metrics
        assert 'conjunction_count' in metrics
        assert 'question_type' in metrics
        assert 'punctuation_complexity' in metrics
        assert metrics['question_type'] == 'how'
    
    def test_performance(self):
        """Test performance meets requirements."""
        text = "Complex query with (nested structures) and multiple, diverse clauses?"
        
        start = time.time()
        self.parser.parse(text)
        elapsed = (time.time() - start) * 1000
        
        assert elapsed < 10  # Should be under 10ms


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


class TestEpic1QueryAnalyzer:
    """Integration tests for Epic1QueryAnalyzer orchestrator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from src.components.query_processors.analyzers import Epic1QueryAnalyzer
        
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
        # Test with empty query
        analysis = self.analyzer.analyze("")
        assert analysis is not None
        assert 'epic1_analysis' in analysis.metadata
        
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
        assert epic1_data['strategy_used'] == 'cost_optimized'
    
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