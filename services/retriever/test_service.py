#!/usr/bin/env python3
"""
Simple test script for the Retriever Service.

This script validates that the service can be imported and basic
functionality works correctly.
"""

import sys
import os
from pathlib import Path

# Add project root and service directory to path
project_root = Path(__file__).parent.parent.parent
service_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(service_root))

# Set environment variables
os.environ['PYTHONPATH'] = f"{project_root}:{project_root}/src:{service_root}"
os.environ['PROJECT_ROOT'] = str(project_root)

def test_imports():
    """Test that all modules can be imported successfully."""
    print("Testing imports...")
    
    try:
        from retriever_app.core.config import get_settings
        print("✅ Config module imported successfully")
    except ImportError as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    try:
        from retriever_app.core.retriever import RetrieverService
        print("✅ RetrieverService imported successfully")
    except ImportError as e:
        print(f"❌ RetrieverService import failed: {e}")
        return False
    
    try:
        from retriever_app.schemas.requests import RetrievalRequest
        from retriever_app.schemas.responses import RetrievalResponse
        print("✅ Schema modules imported successfully")
    except ImportError as e:
        print(f"❌ Schema import failed: {e}")
        return False
    
    try:
        from retriever_app.api.rest import router
        print("✅ API router imported successfully")
    except ImportError as e:
        print(f"❌ API router import failed: {e}")
        return False
    
    try:
        from retriever_app.main import create_app
        print("✅ FastAPI app imported successfully")
    except ImportError as e:
        print(f"❌ FastAPI app import failed: {e}")
        return False
    
    return True


def test_configuration():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    try:
        from retriever_app.core.config import get_settings
        settings = get_settings()
        
        print(f"✅ Configuration loaded:")
        print(f"   - Service name: {settings.service.name}")
        print(f"   - Service port: {settings.service.port}")
        print(f"   - Retriever config type: {settings.retriever_config.get('vector_index', {}).get('type', 'unknown')}")
        print(f"   - Embedder config type: {settings.embedder_config.get('type', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_schemas():
    """Test Pydantic schema validation."""
    print("\nTesting schemas...")
    
    try:
        from retriever_app.schemas.requests import RetrievalRequest
        from retriever_app.schemas.responses import RetrievalResponse, DocumentResult
        
        # Test valid request
        request = RetrievalRequest(
            query="What is machine learning?",
            k=10,
            retrieval_strategy="hybrid",
            complexity="medium"
        )
        print(f"✅ Valid request created: {request.query[:30]}...")
        
        # Test valid response structure
        doc_result = DocumentResult(
            content="Sample document content",
            metadata={"title": "Test Doc"},
            doc_id="test_001",
            source="test_source",
            score=0.85,
            retrieval_method="test"
        )
        
        response = RetrievalResponse(
            success=True,
            query=request.query,
            documents=[doc_result],
            retrieval_info={"k_requested": 10, "k_returned": 1}
        )
        print(f"✅ Valid response created with {len(response.documents)} document(s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        return False


def test_service_creation():
    """Test RetrieverService creation (without initialization)."""
    print("\nTesting service creation...")
    
    try:
        from retriever_app.core.retriever import RetrieverService
        
        # Create service with minimal config
        config = {
            "retriever_config": {
                "vector_index": {"type": "faiss", "config": {}},
                "sparse": {"type": "bm25", "config": {}},
                "fusion": {"type": "rrf", "config": {}},
                "reranker": {"type": "identity", "config": {}}
            },
            "embedder_config": {
                "type": "sentence_transformer",
                "config": {"model_name": "sentence-transformers/all-MiniLM-L6-v2"}
            }
        }
        
        service = RetrieverService(config=config)
        print(f"✅ RetrieverService created successfully")
        print(f"   - Initialized: {service._initialized}")
        print(f"   - Config keys: {list(service.config.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Service creation test failed: {e}")
        return False


def test_fastapi_app():
    """Test FastAPI app creation."""
    print("\nTesting FastAPI app creation...")
    
    try:
        from retriever_app.main import create_app
        
        app = create_app()
        print(f"✅ FastAPI app created successfully")
        print(f"   - Title: {app.title}")
        print(f"   - Version: {app.version}")
        print(f"   - Routes: {len(app.routes)} routes")
        
        # List some key routes
        route_paths = [route.path for route in app.routes if hasattr(route, 'path')]
        key_routes = [path for path in route_paths if path.startswith('/api/v1/')]
        print(f"   - API routes: {key_routes}")
        
        return True
        
    except Exception as e:
        print(f"❌ FastAPI app test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Retriever Service Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_configuration,
        test_schemas,
        test_service_creation,
        test_fastapi_app
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ Test {test.__name__} failed")
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Service structure is valid.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the issues above.")
        return 1


if __name__ == "__main__":
    exit(main())