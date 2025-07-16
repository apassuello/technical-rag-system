#!/usr/bin/env python3
"""Test script to verify config loading for different validators."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import load_config
from src.core.component_factory import ComponentFactory
from src.components.embedders.sentence_transformer_embedder import SentenceTransformerEmbedder

def test_config_loading():
    """Test different config loading scenarios."""
    
    configs_to_test = [
        "test_epic2_all_features",
        "test_epic2_neural_enabled",
        "test_epic2_graph_enabled"
    ]
    
    embedder = SentenceTransformerEmbedder(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    for config_name in configs_to_test:
        print(f"\n{'='*60}")
        print(f"Testing config: {config_name}")
        print('='*60)
        
        try:
            config_path = Path(f"config/{config_name}.yaml")
            config = load_config(config_path)
            
            print(f"✅ Config loaded successfully")
            print(f"Retriever type: {config.retriever.type}")
            print(f"Raw config: {config.retriever.config}")
            
            # Handle dict config
            if hasattr(config.retriever.config, 'reranker'):
                reranker_config = config.retriever.config.reranker
            else:
                reranker_config = config.retriever.config.get('reranker', {})
            print(f"Reranker config: {reranker_config}")
            
            # Try to create the retriever
            retriever_config = config.retriever.config if hasattr(config.retriever.config, 'model_dump') else config.retriever.config
            if hasattr(retriever_config, 'model_dump'):
                retriever_config = retriever_config.model_dump()
                
            retriever = ComponentFactory.create_retriever(
                config.retriever.type,
                embedder=embedder,
                **retriever_config
            )
            
            print(f"✅ Retriever created successfully")
            print(f"Actual reranker type: {type(retriever.reranker).__name__}")
            print(f"Reranker enabled: {retriever.reranker.is_enabled()}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_config_loading()