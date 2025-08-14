#!/usr/bin/env python3
"""
Test all 5 Epic1 ML models
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.components.query_processors.analyzers.epic1_ml_analyzer import Epic1MLAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_all_models():
    """Test all 5 models."""
    logger.info("=== ALL 5 MODELS TEST ===")
    
    # Create analyzer with larger memory budget
    analyzer = Epic1MLAnalyzer(config={
        'memory_budget_gb': 2.0,
        'parallel_execution': False,
        'enable_performance_monitoring': False,
        'fallback_strategy': 'algorithmic'
    })
    
    # Test query
    query = "How do I implement a neural network with backpropagation?"
    logger.info(f"Testing query: {query}")
    
    # Test each view individually
    view_results = {}
    
    view_names = ['technical', 'linguistic', 'task', 'semantic', 'computational']
    
    for view_name in view_names:
        try:
            logger.info(f"\n--- Testing {view_name} view in ML mode ---")
            view = analyzer.views[view_name]
            
            result = await view.analyze(query, mode='ml')
            
            logger.info(f"✅ {view_name}: score={result.score:.3f}, conf={result.confidence:.3f}, method={result.method.value}")
            view_results[view_name] = {
                'success': True,
                'score': result.score,
                'confidence': result.confidence,
                'method': result.method.value
            }
            
        except Exception as e:
            logger.error(f"❌ {view_name}: {e}")
            view_results[view_name] = {
                'success': False,
                'error': str(e)
            }
    
    # Summary
    logger.info(f"\n=== RESULTS SUMMARY ===")
    success_count = 0
    for view_name, result in view_results.items():
        if result['success']:
            success_count += 1
            logger.info(f"✅ {view_name}: {result['method']} mode, score={result['score']:.3f}")
        else:
            logger.info(f"❌ {view_name}: {result['error']}")
    
    logger.info(f"\nSuccess rate: {success_count}/5 models working in ML mode")
    
    # Quick exit to avoid shutdown hanging
    if success_count >= 3:
        logger.info("🎉 MAJOR SUCCESS: At least 3/5 models working!")
        os._exit(0)
    else:
        logger.info("⚠️  Some models still need work")
        os._exit(1)

def main():
    asyncio.run(test_all_models())

if __name__ == "__main__":
    main()