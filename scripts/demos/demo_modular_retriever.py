#!/usr/bin/env python3
"""
Modular Retriever Demo using ComponentFactory
Demonstrates the full ModularUnifiedRetriever with all fusion strategies.
"""

import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent.parent  # Go up to project-1-technical-rag
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))  # Add rag-portfolio root for shared_utils

from src.core.component_factory import ComponentFactory
from src.core.interfaces import Document


def main():
    print("🏗️  Modular Retriever Demo - ComponentFactory Integration")
    print("🎯 Demonstrates: ModularUnifiedRetriever with all fusion strategies")
    print("=" * 75)
    
    # Sample technical documentation
    documents = [
        Document(
            content="RISC-V is an open standard instruction set architecture (ISA) based on established reduced instruction set computer (RISC) principles.",
            metadata={'source': 'riscv-spec.pdf', 'page': 1}
        ),
        Document(
            content="The RV32I base integer instruction set provides 32-bit addresses and integer operations for embedded applications.",
            metadata={'source': 'riscv-spec.pdf', 'page': 2}
        ),
        Document(
            content="ARM Cortex-M processors are designed specifically for microcontroller applications with emphasis on low power consumption.",
            metadata={'source': 'arm-guide.pdf', 'page': 1}
        ),
        Document(
            content="Vector databases enable efficient similarity search operations on high-dimensional embedding vectors for AI applications.",
            metadata={'source': 'vector-db-guide.pdf', 'page': 10}
        ),
        Document(
            content="Machine learning models require substantial amounts of training data to achieve optimal performance in real-world applications.",
            metadata={'source': 'ml-handbook.pdf', 'page': 5}
        )
    ]
    
    print(f"📚 Created {len(documents)} Document objects")
    
    # Create embedder using ComponentFactory
    print("\n🏭 Creating components using ComponentFactory...")
    try:
        embedder = ComponentFactory.create_embedder("sentence_transformer", 
                                                   model_name="sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
                                                   use_mps=False)
        print("✅ Embedder created successfully")
        
        # Configure retriever with different fusion strategies to test
        configs = [
            {
                "name": "RRF Fusion",
                "config": {
                    "vector_index": {"type": "faiss"},
                    "sparse": {"type": "bm25"},
                    "fusion": {"type": "rrf", "config": {"k": 60}},
                    "reranker": {"type": "identity"}
                }
            },
            {
                "name": "Weighted Fusion", 
                "config": {
                    "vector_index": {"type": "faiss"},
                    "sparse": {"type": "bm25"},
                    "fusion": {"type": "weighted", "config": {"normalize": True}},
                    "reranker": {"type": "identity"}
                }
            }
        ]
        
        for config_info in configs:
            print(f"\n🎯 Testing {config_info['name']}:")
            print("-" * 50)
            
            # Create modular unified retriever
            retriever = ComponentFactory.create_retriever("modular_unified", 
                                                         config=config_info['config'], 
                                                         embedder=embedder)
            print("✅ ModularUnifiedRetriever created")
            
            # Index documents
            retriever.index_documents(documents)
            print(f"✅ Indexed {len(documents)} documents")
            
            # Test search
            query = "RISC-V processor architecture"
            results = retriever.search(query, k=3)
            
            print(f"🔍 Search results for: '{query}'")
            for i, result in enumerate(results, 1):
                content_preview = result.document.content[:60] + "..." if len(result.document.content) > 60 else result.document.content
                print(f"   {i}. Score: {result.score:.4f}")
                print(f"      Content: {content_preview}")
                print(f"      Source: {result.document.metadata.get('source', 'unknown')}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Note: This demo requires the full modular architecture to be functional.")
        print("Some components may not be fully implemented yet.")
        
    print(f"\n✅ Modular Retriever Demo Complete!")
    print(f"📋 ComponentFactory Benefits:")
    print(f"   - ✅ Clean Configuration: YAML/Dict-based component setup")
    print(f"   - ✅ Type Safety: Automatic component validation")
    print(f"   - ✅ Extensibility: Easy to add new fusion strategies")
    print(f"   - ✅ Testing: Each sub-component can be tested independently")
    print(f"   - ✅ Production Ready: Enterprise configuration management")


if __name__ == "__main__":
    main()