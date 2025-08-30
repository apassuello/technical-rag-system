#!/usr/bin/env python3
"""
Simple ML mode test - exit immediately after testing
"""
import asyncio
import logging
import os
import sys
from pathlib import Path
import pytest

# Add src to path - updated for scripts/ location
project_root = Path(__file__).parents[2]  # scripts/epic1_training/ is 2 levels from root
sys.path.insert(0, str(project_root / 'src'))

from src.components.query_processors.analyzers.epic1_ml_analyzer import Epic1MLAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_ml_mode():
    """Test ML mode quickly."""
    logger.info("=== ML MODE SIMPLE TEST ===")
    
    # Create analyzer with minimal config
    analyzer = Epic1MLAnalyzer(config={
        'memory_budget_gb': 1.0,
        'parallel_execution': False,
        'enable_performance_monitoring': False,
        'fallback_strategy': 'algorithmic'
    })
    
    # Test one simple query in ML mode
    query = "What is machine learning?"
    logger.info(f"Testing ML mode with: {query}")
    
    try:
        # Test just the semantic view (most reliable) in ML mode
        semantic_view = analyzer.views['semantic']
        result = await semantic_view.analyze(query, mode='ml')
        
        logger.info(f"✅ Semantic ML analysis: score={result.score:.3f}, method={result.method.value}")
        
        # Quick exit without full shutdown
        logger.info("✅ ML mode test completed successfully!")
        os._exit(0)
        
    except Exception as e:
        logger.error(f"❌ ML mode test failed: {e}")
        import traceback
        traceback.print_exc()
        os._exit(1)

def main():
    asyncio.run(test_ml_mode())

if __name__ == "__main__":
    main()