#!/usr/bin/env python3
"""
Integration tests for Epic1 domain-ML integration.

Tests the integration of domain-relevance classifier with Epic1 ML routing system,
ensuring data compatibility, performance impact, and end-to-end functionality.
"""

import pytest
import time
import json
from pathlib import Path
from typing import Dict, Any, List

pytestmark = [pytest.mark.integration]

# Test fixtures and imports
@pytest.fixture
def domain_filter():
    """Domain relevance filter fixture."""
    from src.components.query_processors.domain_relevance_filter import DomainRelevanceFilter
    return DomainRelevanceFilter()

@pytest.fixture
def domain_scorer():
    """Domain relevance scorer fixture."""
    from src.components.query_processors.domain_relevance_filter import DomainRelevanceScorer
    return DomainRelevanceScorer()

@pytest.fixture
def epic1_analyzer():
    """Epic1 ML analyzer fixture."""
    from src.components.query_processors.analyzers.epic1_query_analyzer import Epic1QueryAnalyzer
    return Epic1QueryAnalyzer({'memory_budget_gb': 0.1})

@pytest.fixture
def adaptive_router(epic1_analyzer):
    """Adaptive router with Epic1 analyzer fixture."""
    from src.components.generators.routing.adaptive_router import AdaptiveRouter
    router_config = {
        'strategies': {
            'balanced': {
                'simple_threshold': 0.35,
                'complex_threshold': 0.70
            }
        }
    }
    return AdaptiveRouter(query_analyzer=epic1_analyzer, config=router_config)

@pytest.fixture
def training_data():
    """Load Epic1 training data with domain scores."""
    training_data_path = Path("data/training/epic1_training_dataset_679_with_domain_scores.json")
    if not training_data_path.exists():
        pytest.skip(f"Training data not found: {training_data_path}")
    
    with open(training_data_path) as f:
        return json.load(f)

class TestDomainMLDataCompatibility:
    """Test data compatibility between domain and ML systems."""
    
    def test_training_data_format_compatibility(self, domain_scorer, epic1_analyzer, training_data):
        """Test that training data works with both domain and ML systems."""
        # Test sample of data
        sample_size = min(10, len(training_data))
        
        for sample in training_data[:sample_size]:
            query = sample["query_text"]
            expected_domain_score = sample["domain_relevance_score"]
            expected_domain_tier = sample["domain_relevance_tier"]
            
            # Test domain analysis doesn't fail
            domain_score, domain_tier, domain_details = domain_scorer.score_query(query)
            assert isinstance(domain_score, float)
            assert domain_tier in ['high_relevance', 'medium_relevance', 'low_relevance']
            
            # Test ML analysis doesn't fail
            ml_analysis = epic1_analyzer._analyze_query(query)
            assert hasattr(ml_analysis, 'complexity_score')
            assert hasattr(ml_analysis, 'complexity_level')
            
            # Test data consistency
            score_difference = abs(domain_score - expected_domain_score)
            assert score_difference < 0.2, f"Domain score drift too large: {score_difference}"
    
    def test_combined_data_structures(self, domain_scorer, epic1_analyzer):
        """Test that domain and ML data can be combined without conflicts."""
        test_query = "What is RISC-V vector extension implementation?"
        
        # Get both analyses
        domain_score, domain_tier, domain_details = domain_scorer.score_query(test_query)
        ml_analysis = epic1_analyzer._analyze_query(test_query)
        
        # Test combined structure creation
        combined_result = {
            'query': test_query,
            'domain_analysis': {
                'score': domain_score,
                'tier': domain_tier,
                'details': domain_details
            },
            'ml_analysis': {
                'complexity_score': ml_analysis.complexity_score,
                'complexity_level': ml_analysis.complexity_level,
                'confidence': ml_analysis.confidence,
                'technical_terms': ml_analysis.technical_terms,
                'entities': ml_analysis.entities
            }
        }
        
        # Test no conflicts
        assert 'domain_analysis' in combined_result
        assert 'ml_analysis' in combined_result
        assert isinstance(combined_result['domain_analysis']['score'], float)
        assert isinstance(combined_result['ml_analysis']['complexity_score'], float)

class TestDomainMLPerformance:
    """Test performance impact of domain classification integration."""
    
    def test_domain_classification_performance(self, domain_scorer):
        """Test domain classification meets performance targets."""
        test_queries = [
            "What is RISC-V?",
            "How does RISC-V instruction pipelining optimize performance?",
            "Explain microarchitectural implications of RISC-V vector extensions"
        ]
        
        times = []
        for query in test_queries:
            start = time.perf_counter()
            score, tier, details = domain_scorer.score_query(query)
            end = time.perf_counter()
            times.append((end - start) * 1000)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        # Performance targets
        assert avg_time < 1.0, f"Domain classification too slow: {avg_time:.2f}ms > 1.0ms"
        assert max_time < 2.0, f"Domain classification max too slow: {max_time:.2f}ms > 2.0ms"
    
    def test_combined_pipeline_performance(self, domain_scorer, epic1_analyzer):
        """Test combined domain + ML pipeline performance."""
        test_queries = [
            "What is RISC-V?",  # High relevance
            "How to optimize Docker containers?",  # Low relevance
            "RISC-V vector extension implementation details"  # High relevance, complex
        ]
        
        for query in test_queries:
            start_time = time.perf_counter()
            
            # Stage 1: Domain analysis
            domain_score, domain_tier, domain_details = domain_scorer.score_query(query)
            
            # Stage 2: ML analysis (conditional)
            if domain_score >= 0.3:  # Medium threshold
                analysis = epic1_analyzer._analyze_query(query)
            else:
                analysis = None  # Early exit
            
            end_time = time.perf_counter()
            total_time = (end_time - start_time) * 1000
            
            # Performance target
            assert total_time < 100.0, f"Combined pipeline too slow: {total_time:.2f}ms > 100ms"
    
    def test_early_exit_optimization(self, domain_scorer, epic1_analyzer):
        """Test that low relevance queries exit early and save time."""
        high_relevance_query = "What is RISC-V vector extension?"
        low_relevance_query = "What are Docker best practices?"
        
        # Measure full pipeline for high relevance
        start = time.perf_counter()
        domain_score, _, _ = domain_scorer.score_query(high_relevance_query)
        if domain_score >= 0.3:
            epic1_analyzer._analyze_query(high_relevance_query)
        full_time = (time.perf_counter() - start) * 1000
        
        # Measure early exit for low relevance
        start = time.perf_counter()
        domain_score, _, _ = domain_scorer.score_query(low_relevance_query)
        if domain_score >= 0.3:  # Should be False
            epic1_analyzer._analyze_query(low_relevance_query)
        early_exit_time = (time.perf_counter() - start) * 1000
        
        # Early exit should be significantly faster
        assert early_exit_time < full_time, "Early exit not faster than full pipeline"
        speedup = full_time / max(early_exit_time, 0.001)  # Avoid division by zero
        assert speedup >= 1.5, f"Early exit speedup insufficient: {speedup:.1f}x"

class TestEndToEndIntegration:
    """Test complete end-to-end integration scenarios."""
    
    def test_high_relevance_full_pipeline(self, domain_filter, epic1_analyzer, adaptive_router):
        """Test high relevance query goes through full pipeline."""
        query = "What is RISC-V vector extension RVV?"
        
        # Stage 1: Domain analysis
        domain_result = domain_filter.analyze_domain_relevance(query)
        assert domain_result.is_relevant, "High relevance query should be relevant"
        assert domain_result.relevance_tier == 'high_relevance'
        
        # Stage 2: ML analysis (should proceed)
        ml_analysis = epic1_analyzer._analyze_query(query)
        assert ml_analysis.complexity_level in ['simple', 'medium', 'complex']
        
        # Stage 3: Routing (should succeed)
        routing_decision = adaptive_router.route_query(query, strategy_override='balanced')
        assert routing_decision.selected_model is not None
        assert hasattr(routing_decision.selected_model, 'provider')
        assert hasattr(routing_decision.selected_model, 'model')
    
    def test_low_relevance_early_exit(self, domain_filter):
        """Test low relevance query exits early."""
        query = "What are Docker containerization best practices?"
        
        # Stage 1: Domain analysis
        domain_result = domain_filter.analyze_domain_relevance(query)
        assert not domain_result.is_relevant, "Low relevance query should not be relevant"
        assert domain_result.relevance_tier == 'low_relevance'
        assert domain_result.reasoning is not None
    
    def test_integration_preserves_functionality(self, domain_filter, epic1_analyzer):
        """Test that domain integration doesn't break Epic1 functionality."""
        queries = [
            "What is RISC-V?",
            "How does instruction pipelining work?",
            "Explain vector processing in RISC-V"
        ]
        
        for query in queries:
            # Domain analysis should work
            domain_result = domain_filter.analyze_domain_relevance(query)
            assert hasattr(domain_result, 'is_relevant')
            assert hasattr(domain_result, 'relevance_score')
            assert hasattr(domain_result, 'relevance_tier')
            
            # Epic1 ML analysis should still work
            ml_analysis = epic1_analyzer._analyze_query(query)
            assert hasattr(ml_analysis, 'complexity_score')
            assert hasattr(ml_analysis, 'complexity_level')
            assert hasattr(ml_analysis, 'confidence')

class TestCompatibilityWithExistingTests:
    """Test compatibility with existing Epic1 test infrastructure."""
    
    def test_epic1_analyzer_still_functional(self, epic1_analyzer):
        """Test that Epic1QueryAnalyzer still works as before."""
        query = "What is RISC-V vector extension?"
        
        # Test initialization
        assert epic1_analyzer is not None
        assert hasattr(epic1_analyzer, '_analyze_query')
        
        # Test analysis
        analysis = epic1_analyzer._analyze_query(query)
        assert analysis is not None
        assert hasattr(analysis, 'complexity_level')
        assert hasattr(analysis, 'complexity_score')
        assert hasattr(analysis, 'confidence')
        
        # Test performance metrics
        metrics = epic1_analyzer.get_performance_metrics()
        assert 'epic1_performance' in metrics
    
    def test_domain_integration_non_breaking(self):
        """Test that domain integration doesn't break imports."""
        try:
            # Test core Epic1 imports still work
            from src.components.query_processors.analyzers.epic1_query_analyzer import Epic1QueryAnalyzer
            from src.components.generators.routing.adaptive_router import AdaptiveRouter
            from src.components.generators.epic1_answer_generator import Epic1AnswerGenerator
            
            # Test domain imports work
            from src.components.query_processors.domain_relevance_filter import DomainRelevanceFilter, DomainRelevanceScorer
            
            # Test basic functionality
            analyzer = Epic1QueryAnalyzer({'memory_budget_gb': 0.1})
            domain_filter = DomainRelevanceFilter()
            
            test_query = "What is RISC-V?"
            
            # Both should work independently
            ml_result = analyzer._analyze_query(test_query)
            domain_result = domain_filter.analyze_domain_relevance(test_query)
            
            assert ml_result is not None
            assert domain_result is not None
            
        except ImportError as e:
            pytest.fail(f"Import error after domain integration: {e}")
        except Exception as e:
            pytest.fail(f"Functionality broken after domain integration: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])