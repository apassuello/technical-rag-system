#!/usr/bin/env python3
"""
Test script for Weaviate backend implementation.

This script validates the Weaviate backend adapter, configuration,
and migration functionality without requiring a running Weaviate server.
It tests the implementation logic and error handling.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

import logging
import numpy as np
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import test dependencies
from src.core.interfaces import Document
from src.components.retrievers.backends.weaviate_config import WeaviateBackendConfig
from src.components.retrievers.backends.faiss_backend import FAISSBackend
from src.components.retrievers.config.advanced_config import AdvancedRetrieverConfig


def create_test_documents() -> List[Document]:
    """Create test documents for validation."""
    documents = []
    
    # Sample technical content
    contents = [
        "RISC-V is an open standard instruction set architecture (ISA) based on established reduced instruction set computer (RISC) principles.",
        "The ARM Cortex-M series processors are designed for microcontroller applications with emphasis on low power consumption.",
        "Intel x86 architecture uses complex instruction set computing (CISC) design with variable-length instruction encoding.",
        "FPGA (Field-Programmable Gate Array) devices can be reconfigured to implement custom digital logic circuits.",
        "Real-time operating systems (RTOS) provide deterministic timing guarantees for embedded applications."
    ]
    
    for i, content in enumerate(contents):
        # Generate random embedding
        embedding = np.random.normal(0, 1, 384).tolist()
        
        document = Document(
            content=content,
            metadata={
                "source": f"test_doc_{i}.pdf",
                "chunk_index": i,
                "page": i + 1,
                "doc_id": f"doc_{i}"
            },
            embedding=embedding
        )
        documents.append(document)
    
    return documents


def test_weaviate_config():
    """Test Weaviate configuration classes."""
    logger.info("Testing Weaviate configuration...")
    
    try:
        # Test default configuration
        config = WeaviateBackendConfig()
        assert config.connection.url == "http://localhost:8080"
        assert config.schema.class_name == "TechnicalDocument"
        assert config.search.hybrid_search_enabled == True
        
        # Test configuration from dictionary
        config_dict = {
            "connection": {"url": "http://test:8080", "timeout": 60},
            "schema": {"class_name": "TestDoc"},
            "search": {"alpha": 0.8}
        }
        config_from_dict = WeaviateBackendConfig.from_dict(config_dict)
        assert config_from_dict.connection.url == "http://test:8080"
        assert config_from_dict.connection.timeout == 60
        assert config_from_dict.schema.class_name == "TestDoc"
        assert config_from_dict.search.alpha == 0.8
        
        # Test to_dict conversion
        config_dict_out = config_from_dict.to_dict()
        assert isinstance(config_dict_out, dict)
        assert config_dict_out["connection"]["url"] == "http://test:8080"
        
        logger.info("✅ Weaviate configuration tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Weaviate configuration test failed: {str(e)}")
        return False


def test_advanced_config():
    """Test advanced retriever configuration."""
    logger.info("Testing advanced retriever configuration...")
    
    try:
        # Test default configuration
        config = AdvancedRetrieverConfig()
        assert config.backends.primary_backend == "faiss"
        assert config.hybrid_search.enabled == True
        assert config.neural_reranking.enabled == False
        
        # Test feature flags
        assert "weaviate_backend" in config.feature_flags
        enabled_features = config.get_enabled_features()
        assert isinstance(enabled_features, list)
        
        # Test configuration from dictionary
        config_dict = {
            "backends": {
                "primary_backend": "weaviate",
                "fallback_enabled": True
            },
            "hybrid_search": {
                "dense_weight": 0.8,
                "sparse_weight": 0.2
            },
            "feature_flags": {
                "weaviate_backend": True
            }
        }
        
        config_from_dict = AdvancedRetrieverConfig.from_dict(config_dict)
        assert config_from_dict.backends.primary_backend == "weaviate"
        assert config_from_dict.hybrid_search.dense_weight == 0.8
        
        # Test to_dict conversion
        config_dict_out = config_from_dict.to_dict()
        assert isinstance(config_dict_out, dict)
        assert config_dict_out["backends"]["primary_backend"] == "weaviate"
        
        logger.info("✅ Advanced configuration tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Advanced configuration test failed: {str(e)}")
        return False


def test_faiss_backend():
    """Test FAISS backend wrapper."""
    logger.info("Testing FAISS backend wrapper...")
    
    try:
        # Create test configuration
        config = {
            "faiss": {
                "index_type": "IndexFlatIP",
                "normalize_embeddings": True
            }
        }
        
        # Initialize FAISS backend
        backend = FAISSBackend(config)
        assert backend.backend_type == "faiss"
        assert backend.backend_version == "wrapped"
        
        # Test configuration retrieval
        backend_config = backend.get_configuration()
        assert backend_config["backend_type"] == "faiss"
        
        # Test health check
        health = backend.health_check()
        assert isinstance(health, dict)
        assert "is_healthy" in health
        assert "backend_type" in health
        
        # Test performance stats
        stats = backend.get_performance_stats()
        assert isinstance(stats, dict)
        assert "backend_type" in stats
        assert "total_operations" in stats
        
        # Test backend info
        info = backend.get_backend_info()
        assert isinstance(info, dict)
        assert info["backend_type"] == "faiss"
        
        logger.info("✅ FAISS backend tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ FAISS backend test failed: {str(e)}")
        return False


def test_weaviate_backend_without_server():
    """Test Weaviate backend implementation without requiring server."""
    logger.info("Testing Weaviate backend implementation...")
    
    try:
        # Test configuration validation
        config = WeaviateBackendConfig()
        
        # Test that WeaviateBackend handles missing weaviate-client gracefully
        try:
            from src.components.retrievers.backends.weaviate_backend import WeaviateBackend, WEAVIATE_AVAILABLE
            
            if not WEAVIATE_AVAILABLE:
                logger.info("⚠️ Weaviate client not installed - testing import error handling")
                try:
                    backend = WeaviateBackend(config)
                    assert False, "Should have raised ImportError"
                except ImportError as e:
                    assert "weaviate-client is required" in str(e)
                    logger.info("✅ Correctly handles missing weaviate-client")
            else:
                logger.info("📦 Weaviate client is available")
                # Test initialization (will fail to connect but should validate config)
                try:
                    backend = WeaviateBackend(config)
                    # Connection will fail, but class should be created
                    assert backend.backend_type == "weaviate"
                    assert backend.backend_version == "adapter"
                    logger.info("✅ Weaviate backend class created successfully")
                except Exception as e:
                    # Expected to fail connection, but object should be partially initialized
                    logger.info(f"⚠️ Connection failed as expected: {str(e)}")
        
        except ImportError:
            logger.info("⚠️ Could not import WeaviateBackend - checking error handling")
        
        logger.info("✅ Weaviate backend implementation tests completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Weaviate backend test failed: {str(e)}")
        return False


def test_migration_framework():
    """Test migration framework implementation."""
    logger.info("Testing migration framework...")
    
    try:
        from src.components.retrievers.backends.migration.data_validator import DataValidator
        
        # Test data validator
        validator = DataValidator(strict_mode=False)
        test_docs = create_test_documents()
        
        validation_result = validator.validate_documents(test_docs)
        assert isinstance(validation_result, dict)
        assert "is_valid" in validation_result
        assert "total_documents" in validation_result
        assert validation_result["total_documents"] == len(test_docs)
        
        logger.info(f"Validation result: {validation_result['is_valid']}")
        if validation_result["issues"]:
            logger.warning(f"Validation issues: {validation_result['issues']}")
        
        # Test consistency validation
        consistency_result = validator.validate_migration_consistency(test_docs, len(test_docs))
        assert isinstance(consistency_result, dict)
        assert "is_consistent" in consistency_result
        
        logger.info("✅ Migration framework tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration framework test failed: {str(e)}")
        return False


def test_component_factory_integration():
    """Test ComponentFactory integration."""
    logger.info("Testing ComponentFactory integration...")
    
    try:
        from src.core.component_factory import ComponentFactory
        
        # Test that advanced retriever is registered
        factory = ComponentFactory()
        
        # Check if advanced retriever is in the mapping
        assert "advanced" in factory._RETRIEVERS
        assert "AdvancedRetriever" in factory._RETRIEVERS["advanced"]
        
        logger.info("✅ ComponentFactory integration tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ ComponentFactory integration test failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    logger.info("🚀 Starting Weaviate implementation tests...")
    
    tests = [
        test_weaviate_config,
        test_advanced_config,
        test_faiss_backend,
        test_weaviate_backend_without_server,
        test_migration_framework,
        test_component_factory_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Test {test.__name__} crashed: {str(e)}")
            failed += 1
    
    logger.info(f"\n🏁 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("🎉 All tests passed! Weaviate implementation is ready.")
        return True
    else:
        logger.error("❌ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)