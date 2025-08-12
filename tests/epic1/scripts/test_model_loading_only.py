#!/usr/bin/env python3
"""
Test just model loading without usage
"""
import asyncio
import logging
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.components.query_processors.analyzers.ml_models.model_manager import ModelManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_model_loading_only():
    """Test loading models without using them."""
    logger.info("=== MODEL LOADING ONLY TEST ===")
    
    # Create model manager with minimal setup
    manager = ModelManager(memory_budget_gb=2.0, enable_quantization=False)
    
    models_to_test = [
        'sentence-transformers/all-MiniLM-L6-v2',  # Should work
        'distilbert-base-uncased',  # Transformers
        't5-small',  # T5
    ]
    
    results = {}
    
    for model_name in models_to_test:
        try:
            logger.info(f"\n--- Testing {model_name} ---")
            model = await manager.load_model(model_name)
            logger.info(f"✅ {model_name}: {type(model)}")
            results[model_name] = True
            
            # Test get_model method
            cached = manager.get_model(model_name)
            logger.info(f"   Cached: {type(cached)}")
            
        except Exception as e:
            logger.error(f"❌ {model_name}: {e}")
            results[model_name] = False
    
    # Summary
    logger.info(f"\n=== RESULTS ===")
    success_count = 0
    for model_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{model_name}: {status}")
        if success:
            success_count += 1
    
    logger.info(f"Success rate: {success_count}/{len(models_to_test)}")
    
    manager.shutdown()
    return success_count > 0

def main():
    return asyncio.run(test_model_loading_only())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)