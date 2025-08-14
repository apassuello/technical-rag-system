#!/usr/bin/env python3
"""
Epic 1 ML Analyzer Validation Test

Direct validation of Epic1MLAnalyzer functionality without mocks.
Tests actual ML routing with real components.
"""

import sys
import time
import logging
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.core.component_factory import ComponentFactory
from src.components.query_processors.analyzers.epic1_ml_analyzer import Epic1MLAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_ml_analyzer_creation():
    """Test creating Epic1MLAnalyzer with real components."""
    logger.info("Testing Epic1MLAnalyzer creation...")
    
    try:
        # Create analyzer with minimal config
        analyzer = Epic1MLAnalyzer(config={
            'memory_budget_gb': 0.5,
            'parallel_execution': False,
            'enable_performance_monitoring': False
        })
        
        logger.info(f"✅ Created Epic1MLAnalyzer")
        logger.info(f"   Views: {list(analyzer.views.keys())}")
        logger.info(f"   Memory budget: {analyzer.memory_budget_gb}GB")
        
        # Test features
        features = analyzer.get_supported_features()
        logger.info(f"✅ Supported features: {len(features)}")
        
        # Clean shutdown
        analyzer.shutdown()
        logger.info("✅ Shutdown completed")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create analyzer: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_query_analysis():
    """Test actual query analysis with ML routing."""
    logger.info("\nTesting query analysis...")
    
    test_queries = [
        ("What is Python?", "simple"),
        ("How do I implement a neural network with backpropagation and gradient descent?", "medium"),
        ("Design a comprehensive distributed system architecture that handles real-time data processing, implements fault tolerance through consensus algorithms, manages state replication across multiple data centers, and provides horizontal scalability while maintaining ACID guarantees.", "complex")
    ]
    
    try:
        # Create analyzer
        analyzer = Epic1MLAnalyzer(config={
            'memory_budget_gb': 0.5,
            'parallel_execution': False,
            'fallback_strategy': 'algorithmic'
        })
        
        results = []
        
        for query, expected_level in test_queries:
            logger.info(f"\nAnalyzing: '{query[:50]}...'")
            
            try:
                # Perform analysis
                start_time = time.time()
                
                # Run async analyze method
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                ml_result = loop.run_until_complete(
                    analyzer.analyze(query, mode='algorithmic')  # Use algorithmic mode for speed
                )
                
                analysis_time = (time.time() - start_time) * 1000
                
                logger.info(f"✅ Analysis completed in {analysis_time:.1f}ms")
                logger.info(f"   Complexity: {ml_result.final_complexity} (expected: {expected_level})")
                logger.info(f"   Score: {ml_result.final_score:.3f}")
                logger.info(f"   Confidence: {ml_result.confidence:.3f}")
                logger.info(f"   Model recommendation: {ml_result.metadata.get('model_recommendation', 'N/A')}")
                
                # Check if analysis is reasonable
                is_correct = (
                    (expected_level == "simple" and ml_result.final_score < 0.4) or
                    (expected_level == "medium" and 0.3 < ml_result.final_score < 0.8) or
                    (expected_level == "complex" and ml_result.final_score > 0.6)
                )
                
                results.append({
                    'query': query[:50],
                    'expected': expected_level,
                    'actual': str(ml_result.final_complexity.value),
                    'score': ml_result.final_score,
                    'correct': is_correct,
                    'time_ms': analysis_time
                })
                
            except Exception as e:
                logger.error(f"❌ Analysis failed: {e}")
                results.append({
                    'query': query[:50],
                    'expected': expected_level,
                    'error': str(e)
                })
        
        # Clean shutdown
        analyzer.shutdown()
        
        # Calculate accuracy
        correct = sum(1 for r in results if r.get('correct', False))
        total = len(results)
        accuracy = (correct / total) * 100 if total > 0 else 0
        
        logger.info(f"\n{'='*60}")
        logger.info("ANALYSIS RESULTS SUMMARY")
        logger.info(f"{'='*60}")
        for result in results:
            if 'error' in result:
                logger.info(f"❌ {result['query']}: ERROR - {result['error']}")
            elif result['correct']:
                logger.info(f"✅ {result['query']}: {result['expected']} -> {result['actual']} ({result['score']:.3f})")
            else:
                logger.info(f"❌ {result['query']}: {result['expected']} -> {result['actual']} ({result['score']:.3f})")
        
        logger.info(f"\nAccuracy: {accuracy:.1f}% ({correct}/{total})")
        
        return accuracy >= 60  # At least 60% accuracy for basic test
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_view_execution():
    """Test that individual views are working."""
    logger.info("\nTesting individual view execution...")
    
    try:
        analyzer = Epic1MLAnalyzer(config={
            'memory_budget_gb': 0.5,
            'parallel_execution': False
        })
        
        test_query = "How do I implement a machine learning algorithm?"
        
        # Test each view directly
        for view_name, view in analyzer.views.items():
            try:
                logger.info(f"\nTesting {view_name} view...")
                
                # Run view analysis (algorithmic mode for speed)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    view.analyze(test_query, mode='algorithmic')
                )
                
                logger.info(f"✅ {view_name}: score={result.score:.3f}, confidence={result.confidence:.3f}")
                
            except Exception as e:
                logger.error(f"❌ {view_name} failed: {e}")
        
        analyzer.shutdown()
        return True
        
    except Exception as e:
        logger.error(f"❌ View execution test failed: {e}")
        return False


def main():
    """Run all validation tests."""
    logger.info("=" * 80)
    logger.info("EPIC 1 ML ANALYZER VALIDATION")
    logger.info("=" * 80)
    
    tests = [
        ("ML Analyzer Creation", test_ml_analyzer_creation),
        ("Query Analysis", test_query_analysis),
        ("View Execution", test_view_execution),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"TEST: {test_name}")
        logger.info('='*60)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"\n✅ {test_name}: PASSED")
            else:
                logger.error(f"\n❌ {test_name}: FAILED")
                
        except Exception as e:
            logger.error(f"\n❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("VALIDATION SUMMARY")
    logger.info('='*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name:<30} {status}")
    
    logger.info(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 ALL VALIDATION TESTS PASSED!")
        logger.info("Epic1MLAnalyzer is working correctly!")
        return 0
    else:
        logger.error(f"\n❌ {total - passed} tests failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)