#!/usr/bin/env python3
"""
Test ML vs Algorithmic Analysis in Epic1
"""
import asyncio
import logging
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.components.query_processors.analyzers.epic1_ml_analyzer import Epic1MLAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_analysis_modes():
    """Test different analysis modes to understand ML vs Algorithmic."""
    
    analyzer = Epic1MLAnalyzer(config={
        'memory_budget_gb': 1.0,
        'parallel_execution': False,
        'enable_performance_monitoring': True
    })
    
    test_query = "How do I implement a transformer neural network with attention mechanisms?"
    
    logger.info("=== TESTING ANALYSIS MODES ===")
    logger.info(f"Query: {test_query}")
    
    # Test different modes
    modes = ['algorithmic', 'ml', 'hybrid']
    
    for mode in modes:
        logger.info(f"\n--- Testing {mode.upper()} mode ---")
        
        try:
            result = await analyzer.analyze(test_query, mode=mode)
            
            logger.info(f"✅ {mode} analysis:")
            logger.info(f"   Score: {result.final_score:.3f}")
            logger.info(f"   Level: {result.final_complexity}")
            logger.info(f"   Confidence: {result.confidence:.3f}")
            logger.info(f"   Time: {result.total_latency_ms:.1f}ms")
            logger.info(f"   Analysis method: {result.metadata.get('analysis_method', 'unknown')}")
            
            # Check individual view methods
            view_methods = []
            for view_name, view_result in result.view_results.items():
                if hasattr(view_result, 'method'):
                    view_methods.append(f"{view_name}:{view_result.method.value}")
                elif hasattr(view_result, 'metadata'):
                    method = view_result.metadata.get('analysis_method', 'unknown')
                    view_methods.append(f"{view_name}:{method}")
            
            logger.info(f"   View methods: {', '.join(view_methods)}")
            
        except Exception as e:
            logger.error(f"❌ {mode} analysis failed: {e}")
    
    # Test individual views in ML mode
    logger.info(f"\n--- Testing Individual Views in ML Mode ---")
    
    for view_name, view in analyzer.views.items():
        try:
            result = await view.analyze(test_query, mode='ml')
            logger.info(f"✅ {view_name} (ML): score={result.score:.3f}, conf={result.confidence:.3f}, method={result.method.value}")
        except Exception as e:
            logger.error(f"❌ {view_name} (ML) failed: {e}")
    
    analyzer.shutdown()

def main():
    asyncio.run(test_analysis_modes())

if __name__ == "__main__":
    main()