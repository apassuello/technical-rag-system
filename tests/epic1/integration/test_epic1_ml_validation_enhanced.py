#!/usr/bin/env python3
"""
Epic 1 ML Analyzer Enhanced Validation Test

Proper pytest-based validation of Epic1MLAnalyzer functionality.
Tests actual ML routing with real components using modern pytest patterns.
"""

import pytest
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.integration
@pytest.mark.ml_mode
class TestEpic1MLValidationEnhanced:
    """Enhanced validation tests for Epic1MLAnalyzer."""
    
    @pytest.fixture
    def analyzer_config(self):
        """Provide minimal analyzer configuration."""
        return {
            'memory_budget_gb': 0.5,
            'parallel_execution': False,
            'enable_performance_monitoring': False,
            'fallback_strategy': 'algorithmic'
        }
    
    @pytest.fixture
    def test_queries(self, epic1_test_data):
        """Provide test queries from conftest fixture."""
        return epic1_test_data
    
    def test_ml_analyzer_creation(self, epic1_imports, analyzer_config):
        """Test creating Epic1MLAnalyzer with real components."""
        logger.info("Testing Epic1MLAnalyzer creation...")
        
        # Import Epic1MLAnalyzer
        imports = epic1_imports("analyzer")
        Epic1MLAnalyzer = imports['Epic1MLAnalyzer']
        
        # Create analyzer with minimal config
        analyzer = Epic1MLAnalyzer(config=analyzer_config)
        
        # Validate creation
        assert analyzer is not None
        assert hasattr(analyzer, 'views')
        assert len(analyzer.views) > 0
        assert analyzer.memory_budget_gb == 0.5
        
        logger.info(f"✅ Created Epic1MLAnalyzer")
        logger.info(f"   Views: {list(analyzer.views.keys())}")
        logger.info(f"   Memory budget: {analyzer.memory_budget_gb}GB")
        
        # Test features
        features = analyzer.get_supported_features()
        assert isinstance(features, list)
        assert len(features) > 0
        
        logger.info(f"✅ Supported features: {len(features)}")
        
        # Clean shutdown
        analyzer.shutdown()
        logger.info("✅ Shutdown completed")
    
    @pytest.mark.asyncio
    async def test_ml_analysis_simple_query(self, epic1_imports, analyzer_config, test_queries):
        """Test ML analysis with simple query."""
        logger.info("Testing ML analysis with simple query...")
        
        # Import Epic1MLAnalyzer
        imports = epic1_imports("analyzer")
        Epic1MLAnalyzer = imports['Epic1MLAnalyzer']
        
        # Create analyzer
        analyzer = Epic1MLAnalyzer(config=analyzer_config)
        
        try:
            # Test simple query
            simple_query = test_queries['simple_queries'][0]
            logger.info(f"Testing query: {simple_query}")
            
            result = await analyzer.analyze(simple_query, mode='ml')
            
            # Validate result
            assert result is not None
            assert hasattr(result, 'final_score')
            assert hasattr(result, 'final_complexity')
            assert hasattr(result, 'confidence')
            assert result.final_score >= 0.0
            assert result.confidence >= 0.0
            
            logger.info(f"✅ Analysis complete:")
            logger.info(f"   Score: {result.final_score:.4f}")
            logger.info(f"   Complexity: {result.final_complexity}")
            logger.info(f"   Confidence: {result.confidence:.3f}")
            
        finally:
            analyzer.shutdown()
    
    @pytest.mark.asyncio
    async def test_ml_analysis_all_complexity_levels(self, epic1_imports, analyzer_config, test_queries):
        """Test ML analysis across all complexity levels."""
        logger.info("Testing ML analysis across complexity levels...")
        
        # Import Epic1MLAnalyzer
        imports = epic1_imports("analyzer")
        Epic1MLAnalyzer = imports['Epic1MLAnalyzer']
        
        # Create analyzer
        analyzer = Epic1MLAnalyzer(config=analyzer_config)
        
        try:
            results = {}
            
            # Test each complexity level
            for level, queries in test_queries.items():
                query = queries[0]  # Use first query of each level
                logger.info(f"Testing {level} query: {query[:50]}...")
                
                result = await analyzer.analyze(query, mode='ml')
                results[level] = result
                
                # Validate result
                assert result is not None
                assert result.final_score >= 0.0
                assert result.confidence >= 0.0
                
                logger.info(f"✅ {level}: score={result.final_score:.4f}, confidence={result.confidence:.3f}")
            
            # Validate that different complexity levels produce different scores
            scores = [result.final_score for result in results.values()]
            assert len(set(scores)) > 1, "All queries produced the same score - ML analysis may not be working properly"
            
            logger.info("✅ ML analysis produces varying results across complexity levels")
            
        finally:
            analyzer.shutdown()
    
    @pytest.mark.asyncio
    async def test_ml_vs_algorithmic_mode(self, epic1_imports, analyzer_config):
        """Test difference between ML and algorithmic modes."""
        logger.info("Testing ML vs algorithmic mode differences...")
        
        # Import Epic1MLAnalyzer
        imports = epic1_imports("analyzer")
        Epic1MLAnalyzer = imports['Epic1MLAnalyzer']
        
        # Create analyzer
        analyzer = Epic1MLAnalyzer(config=analyzer_config)
        
        try:
            test_query = "How do I implement machine learning model deployment?"
            
            # Test ML mode
            ml_result = await analyzer.analyze(test_query, mode='ml')
            
            # Test algorithmic mode
            algo_result = await analyzer.analyze(test_query, mode='algorithmic')
            
            # Validate both results
            assert ml_result is not None
            assert algo_result is not None
            
            # Results should be different (or at least use different methods)
            different_scores = ml_result.final_score != algo_result.final_score
            different_confidence = ml_result.confidence != algo_result.confidence
            
            # At least one aspect should be different
            assert different_scores or different_confidence, "ML and algorithmic modes produced identical results"
            
            logger.info(f"✅ ML mode: score={ml_result.final_score:.4f}, confidence={ml_result.confidence:.3f}")
            logger.info(f"✅ Algorithmic mode: score={algo_result.final_score:.4f}, confidence={algo_result.confidence:.3f}")
            logger.info("✅ Modes produce different results")
            
        finally:
            analyzer.shutdown()
    
    def test_analyzer_performance_requirements(self, epic1_imports, analyzer_config):
        """Test that analyzer meets performance requirements."""
        logger.info("Testing analyzer performance requirements...")
        
        # Import Epic1MLAnalyzer
        imports = epic1_imports("analyzer")
        Epic1MLAnalyzer = imports['Epic1MLAnalyzer']
        
        # Create analyzer
        analyzer = Epic1MLAnalyzer(config=analyzer_config)
        
        try:
            # Test memory usage
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_usage_mb = process.memory_info().rss / 1024 / 1024
            
            # Should not use excessive memory
            assert memory_usage_mb < 1000, f"Memory usage too high: {memory_usage_mb:.1f}MB"
            
            logger.info(f"✅ Memory usage: {memory_usage_mb:.1f}MB")
            
            # Test that views are properly initialized
            assert len(analyzer.views) >= 3, f"Expected at least 3 views, got {len(analyzer.views)}"
            
            logger.info(f"✅ Views initialized: {list(analyzer.views.keys())}")
            
        finally:
            analyzer.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])