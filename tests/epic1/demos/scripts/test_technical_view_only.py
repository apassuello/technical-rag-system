#!/usr/bin/env python3
"""
Test just technical view to verify fix
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

async def test_technical_view():
    """Test just technical view."""
    logger.info("=== TECHNICAL VIEW TEST ===")
    
    # Create analyzer 
    analyzer = Epic1MLAnalyzer(config={
        'memory_budget_gb': 1.0,
        'parallel_execution': False,
        'enable_performance_monitoring': False
    })
    
    # Test query
    query = "How do I implement a transformer neural network?"
    logger.info(f"Testing query: {query}")
    
    try:
        # Test technical view in ML mode
        technical_view = analyzer.views['technical']
        result = await technical_view.analyze(query, mode='ml')
        
        logger.info(f"✅ Technical ML: score={result.score:.3f}, conf={result.confidence:.3f}, method={result.method.value}")
        
        # Quick exit
        if result.score > 0:
            logger.info("🎉 SUCCESS: Technical view now working in ML mode!")
        else:
            logger.info("⚠️ Working but score is 0 - check embedding extraction")
        
        os._exit(0)
        
    except Exception as e:
        logger.error(f"❌ Technical view test failed: {e}")
        import traceback
        traceback.print_exc()
        os._exit(1)

def main():
    asyncio.run(test_technical_view())

if __name__ == "__main__":
    main()