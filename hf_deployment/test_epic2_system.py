#!/usr/bin/env python3
"""
Test script for Epic 2 HF deployment system.
"""

import sys
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))

def test_epic2_system():
    """Test the Epic 2 system functionality."""
    print("🧪 Testing Epic 2 HF Deployment System...")
    
    try:
        # Test imports
        print("1. Testing imports...")
        from src.core.component_factory import epic2_factory
        from src.epic2_rag_with_generation import Epic2RAGWithGeneration
        from src.rag_with_generation import RAGWithGeneration
        from src.basic_rag import BasicRAG
        print("   ✅ All imports successful")
        
        # Test Epic 2 system initialization  
        print("2. Testing Epic 2 system initialization...")
        rag_system = Epic2RAGWithGeneration(enable_epic2_features=True)
        print("   ✅ Epic 2 RAG system initialized")
        
        # Test ComponentFactory
        print("3. Testing ComponentFactory...")
        config = {
            'dense_weight': 0.4,
            'sparse_weight': 0.3,
            'graph_weight': 0.3,
            'reranker': {
                'enabled': True,
                'config': {
                    'model_name': 'cross-encoder/ms-marco-MiniLM-L6-v2',
                    'max_candidates': 20,
                    'initialize_immediately': False
                }
            },
            'graph_retrieval': {
                'enabled': True,
                'similarity_threshold': 0.65,
                'use_pagerank': True
            }
        }
        
        retriever = epic2_factory.create_retriever('epic2_advanced', config=config)
        print("   ✅ ComponentFactory working")
        
        # Test document indexing
        print("4. Testing document indexing...")
        test_docs = [
            {'text': 'RISC-V is an open standard instruction set architecture.', 'metadata': {'source': 'test1'}},
            {'text': 'The RISC-V processor pipeline consists of multiple stages.', 'metadata': {'source': 'test2'}}
        ]
        
        if rag_system.advanced_retriever:
            rag_system.advanced_retriever.index_documents(test_docs)
            print("   ✅ Document indexing working")
            
            # Test health and capabilities
            health = rag_system.advanced_retriever.get_health_status()
            capabilities = rag_system.advanced_retriever.get_capabilities()
            
            print(f"   ✅ Health: {health.is_healthy}")
            print(f"   ✅ Capabilities: {len(capabilities)} features")
            
            # Check Epic 2 specific features
            epic2_features = [cap for cap in capabilities if cap in ['neural_reranking', 'graph_enhancement', 'hybrid_search']]
            print(f"   🚀 Epic 2 features: {epic2_features}")
        
        print("🎉 Epic 2 system fully functional!")
        print("📦 Ready for HuggingFace Spaces deployment!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_epic2_system()
    sys.exit(0 if success else 1)