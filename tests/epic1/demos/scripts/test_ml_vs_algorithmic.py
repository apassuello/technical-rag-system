#!/usr/bin/env python3
"""
Test ML vs Algorithmic Analysis in Epic1 - Enhanced to test both classifiers
"""
import asyncio
import logging
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from src.components.query_processors.analyzers.epic1_ml_analyzer import Epic1MLAnalyzer
from src.components.query_processors.analyzers.epic1_query_analyzer import Epic1QueryAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ml_vs_rule_based():
    """Test ML-based classifier vs Rule-based classifier to show performance differences."""
    
    # Initialize both classifiers
    ml_analyzer = Epic1MLAnalyzer(config={
        'memory_budget_gb': 1.0,
        'parallel_execution': False,
        'enable_performance_monitoring': True
    })
    
    rule_analyzer = Epic1QueryAnalyzer(config={
        'confidence_threshold': 0.6,
        'enable_caching': False
    })
    
    # Test queries of different complexities
    test_queries = [
        ("What is Python?", "simple"),
        ("How do I implement rate limiting for REST APIs?", "medium"),
        ("How can I design a distributed consensus algorithm with Byzantine fault tolerance?", "complex"),
        ("Explain transformer attention mechanisms in detail", "complex"),
        ("List common HTTP status codes", "simple"),
        ("How to optimize database queries for large datasets with indexing strategies?", "medium")
    ]
    
    logger.info("=== TESTING ML vs RULE-BASED CLASSIFIERS ===")
    logger.info(f"Testing {len(test_queries)} queries\n")
    
    ml_results = []
    rule_results = []
    
    for query, expected_level in test_queries:
        logger.info(f"Query: {query[:60]}...")
        logger.info(f"Expected level: {expected_level}")
        
        # Test ML-based classifier
        try:
            ml_result = await ml_analyzer.analyze(query, mode='ml')
            ml_results.append({
                'query': query,
                'expected': expected_level,
                'score': ml_result.final_score,
                'level': ml_result.final_complexity.value,
                'confidence': ml_result.confidence,
                'time_ms': ml_result.total_latency_ms,
                'trained_models_used': ml_result.metadata.get('trained_models_used', False),
                'fusion_method': ml_result.metadata.get('fusion_method', 'none'),
                'view_count': len(ml_result.view_results)
            })
            logger.info(f"✅ ML Classifier:")
            logger.info(f"   Score: {ml_result.final_score:.4f} | Level: {ml_result.final_complexity.value}")
            logger.info(f"   Confidence: {ml_result.confidence:.3f} | Time: {ml_result.total_latency_ms:.1f}ms")
            logger.info(f"   Trained models: {ml_result.metadata.get('trained_models_used', False)}")
            logger.info(f"   Fusion method: {ml_result.metadata.get('fusion_method', 'none')}")
            
        except Exception as e:
            logger.error(f"❌ ML analysis failed: {e}")
            ml_results.append({
                'query': query,
                'expected': expected_level,
                'error': str(e)
            })
        
        # Test rule-based classifier
        try:
            import time
            rule_start_time = time.time()
            rule_result = rule_analyzer.analyze(query)  # Rule-based analyzer is sync, not async
            rule_analysis_time = (time.time() - rule_start_time) * 1000  # Convert to ms
            
            rule_results.append({
                'query': query,
                'expected': expected_level,
                'score': rule_result.complexity_score,
                'level': rule_result.complexity_level,
                'confidence': rule_result.confidence,
                'time_ms': rule_analysis_time,
                'method': 'rule_based'
            })
            logger.info(f"✅ Rule-based Classifier:")
            logger.info(f"   Score: {rule_result.complexity_score:.4f} | Level: {rule_result.complexity_level}")
            logger.info(f"   Confidence: {rule_result.confidence:.3f} | Time: {rule_analysis_time:.1f}ms")
            
        except Exception as e:
            logger.error(f"❌ Rule-based analysis failed: {e}")
            rule_results.append({
                'query': query,
                'expected': expected_level,
                'error': str(e)
            })
        
        logger.info("")
    
    # Calculate performance metrics
    logger.info("=== PERFORMANCE COMPARISON ===")
    
    # ML classifier metrics
    ml_successful = [r for r in ml_results if 'error' not in r]
    if ml_successful:
        ml_avg_time = sum(r['time_ms'] for r in ml_successful) / len(ml_successful)
        ml_avg_confidence = sum(r['confidence'] for r in ml_successful) / len(ml_successful)
        ml_trained_count = sum(1 for r in ml_successful if r.get('trained_models_used', False))
        
        logger.info(f"ML Classifier ({len(ml_successful)}/{len(test_queries)} successful):")
        logger.info(f"   Average time: {ml_avg_time:.1f}ms")
        logger.info(f"   Average confidence: {ml_avg_confidence:.3f}")
        logger.info(f"   Used trained models: {ml_trained_count}/{len(ml_successful)} queries")
        
        # Check if ML predictions vary (not hardcoded)
        ml_scores = [r['score'] for r in ml_successful]
        ml_score_range = max(ml_scores) - min(ml_scores) if ml_scores else 0
        logger.info(f"   Score variation: {ml_score_range:.4f} (range: {min(ml_scores) if ml_scores else 0:.4f} - {max(ml_scores) if ml_scores else 0:.4f})")
    
    # Rule-based classifier metrics
    rule_successful = [r for r in rule_results if 'error' not in r]
    if rule_successful:
        rule_avg_time = sum(r['time_ms'] for r in rule_successful) / len(rule_successful)
        rule_avg_confidence = sum(r['confidence'] for r in rule_successful) / len(rule_successful)
        
        logger.info(f"\nRule-based Classifier ({len(rule_successful)}/{len(test_queries)} successful):")
        logger.info(f"   Average time: {rule_avg_time:.1f}ms")
        logger.info(f"   Average confidence: {rule_avg_confidence:.3f}")
        
        # Check if rule-based predictions vary
        rule_scores = [r['score'] for r in rule_successful]
        rule_score_range = max(rule_scores) - min(rule_scores) if rule_scores else 0
        logger.info(f"   Score variation: {rule_score_range:.4f} (range: {min(rule_scores) if rule_scores else 0:.4f} - {max(rule_scores) if rule_scores else 0:.4f})")
    
    # Compare accuracy (simplified - based on expected vs predicted levels)
    if ml_successful and rule_successful:
        logger.info(f"\n=== ACCURACY COMPARISON ===")
        
        # Simple level match comparison
        ml_correct = sum(1 for r in ml_successful if r['level'] == r['expected'])
        rule_correct = sum(1 for r in rule_successful if r['level'] == r['expected'])
        
        ml_accuracy = ml_correct / len(ml_successful) * 100 if ml_successful else 0
        rule_accuracy = rule_correct / len(rule_successful) * 100 if rule_successful else 0
        
        logger.info(f"ML Classifier accuracy: {ml_accuracy:.1f}% ({ml_correct}/{len(ml_successful)})")
        logger.info(f"Rule-based accuracy: {rule_accuracy:.1f}% ({rule_correct}/{len(rule_successful)})")
        
        if ml_accuracy > rule_accuracy:
            logger.info(f"✅ ML Classifier outperforms rule-based by {ml_accuracy - rule_accuracy:.1f}%")
        else:
            logger.info(f"⚠️  Rule-based classifier performs better")
    
    logger.info(f"\n=== TEST SUMMARY ===")
    logger.info(f"ML classifier uses trained models: {'✅' if any(r.get('trained_models_used', False) for r in ml_successful) else '❌'}")
    logger.info(f"ML predictions vary correctly: {'✅' if ml_score_range > 0.1 else '❌'}")
    logger.info(f"Both classifiers operational: {'✅' if ml_successful and rule_successful else '❌'}")
    
    return {
        'ml_results': ml_results,
        'rule_results': rule_results,
        'ml_successful': len(ml_successful),
        'rule_successful': len(rule_successful),
        'total_queries': len(test_queries)
    }

def main():
    results = asyncio.run(test_ml_vs_rule_based())
    
    # Print final status
    if results['ml_successful'] > 0 and results['rule_successful'] > 0:
        print("\n🎉 SUCCESS: Both ML and rule-based classifiers are working!")
        print(f"   ML classifier: {results['ml_successful']}/{results['total_queries']} queries successful")
        print(f"   Rule-based: {results['rule_successful']}/{results['total_queries']} queries successful")
    else:
        print("\n❌ FAILURE: One or both classifiers not working properly")
    
    return results

if __name__ == "__main__":
    main()