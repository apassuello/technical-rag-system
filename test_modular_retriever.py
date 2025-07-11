#!/usr/bin/env python3
"""
Quick integration test for ModularUnifiedRetriever.

This test verifies that the modular retriever can be created and used
with the ComponentFactory and that all sub-components work together.
"""

import sys
import logging
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.core.component_factory import ComponentFactory
from src.core.interfaces import Document

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_documents():
    """Create test documents with embeddings."""
    documents = []
    
    # Create sample documents about RISC-V
    texts = [
        "RISC-V is an open standard instruction set architecture based on established reduced instruction set computer principles.",
        "ARM processors are widely used in mobile devices and embedded systems due to their power efficiency.",
        "x86 architecture is commonly found in desktop computers and servers, developed by Intel and AMD.",
        "The RISC-V foundation promotes the development of open-source hardware and software.",
        "Embedded systems require processors that are both efficient and cost-effective for specific applications."
    ]
    
    # Create simple embeddings (in real use, these would come from an embedder)
    for i, text in enumerate(texts):
        # Create a simple embedding based on word hashing
        embedding = np.random.random(384).astype(np.float32).tolist()  # 384-dim embedding as list
        
        doc = Document(
            content=text,
            embedding=embedding,
            metadata={"doc_id": f"doc_{i}", "source": f"test_source_{i}"}
        )
        documents.append(doc)
    
    return documents

def test_modular_retriever():
    """Test the modular unified retriever."""
    logger.info("Testing ModularUnifiedRetriever...")
    
    try:
        # Create test documents
        documents = create_test_documents()
        logger.info(f"Created {len(documents)} test documents")
        
        # Create embedder (mock for testing)
        class MockEmbedder:
            def embed_query(self, query):
                return np.random.random(384).astype(np.float32)
        
        embedder = MockEmbedder()
        
        # Create modular retriever configuration
        config = {
            "vector_index": {
                "type": "faiss",
                "config": {
                    "index_type": "IndexFlatIP",
                    "normalize_embeddings": True
                }
            },
            "sparse": {
                "type": "bm25",
                "config": {
                    "k1": 1.2,
                    "b": 0.75
                }
            },
            "fusion": {
                "type": "rrf",
                "config": {
                    "k": 60,
                    "weights": {
                        "dense": 0.7,
                        "sparse": 0.3
                    }
                }
            },
            "reranker": {
                "type": "identity",
                "config": {
                    "enabled": True
                }
            }
        }
        
        # Create modular retriever using ComponentFactory
        logger.info("Creating modular retriever with ComponentFactory...")
        retriever = ComponentFactory.create_retriever(
            "modular_unified",
            config=config,
            embedder=embedder
        )
        logger.info("✅ ModularUnifiedRetriever created successfully")
        
        # Test indexing
        logger.info("Indexing documents...")
        retriever.index_documents(documents)
        logger.info("✅ Documents indexed successfully")
        
        # Test retrieval
        logger.info("Testing retrieval...")
        query = "RISC-V instruction set architecture"
        results = retriever.retrieve(query, k=3)
        
        logger.info(f"✅ Retrieved {len(results)} results for query: '{query}'")
        
        # Display results
        for i, result in enumerate(results):
            logger.info(f"Result {i+1}: score={result.score:.4f}, content='{result.document.content[:50]}...'")
        
        # Test component info
        logger.info("Testing component info...")
        component_info = retriever.get_component_info()
        logger.info("✅ Component info retrieved successfully")
        
        # Display component info
        for comp_name, comp_info in component_info.items():
            logger.info(f"  {comp_name}: {comp_info['class']}")
        
        # Test stats
        stats = retriever.get_retrieval_stats()
        logger.info(f"✅ Retrieval stats: {stats['retrieval_stats']}")
        
        logger.info("🎉 All tests passed! ModularUnifiedRetriever is working correctly.")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_modular_retriever()
    sys.exit(0 if success else 1)