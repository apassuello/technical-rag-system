#!/usr/bin/env python3
"""
Test single model loading for Epic 1
"""
import asyncio
import logging
from pathlib import Path
import sys
import pytest

# Add src to path - fix path resolution for Epic 1 tests
sys.path.insert(0, str(Path(__file__).parents[4] / 'src'))

from src.components.query_processors.analyzers.ml_models.model_manager import ModelManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_single_model():
    """Test loading just one model."""
    logger.info("=== SINGLE MODEL TEST ===")
    
    # Create model manager
    manager = ModelManager(memory_budget_gb=1.0, enable_quantization=False)
    
    try:
        # Test Sentence-BERT first (usually most reliable)
        model_name = 'sentence-transformers/all-MiniLM-L6-v2'
        logger.info(f"Testing model: {model_name}")
        
        model = await manager.load_model(model_name)
        logger.info(f"✅ Successfully loaded {model_name}")
        logger.info(f"Model type: {type(model)}")
        
        # Test model access
        retrieved_model = manager.get_model(model_name)
        logger.info(f"✅ Retrieved model from cache: {type(retrieved_model)}")
        
        # Test simple usage
        if hasattr(model, 'encode'):
            embedding = model.encode("Test query")
            logger.info(f"✅ Generated embedding of shape: {embedding.shape}")
        elif isinstance(model, dict) and 'model' in model:
            logger.info(f"✅ Model is dict with keys: {list(model.keys())}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        manager.shutdown()

def main():
    return asyncio.run(test_single_model())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)