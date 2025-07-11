"""
Tests for ComponentFactory - Phase 3 Direct Wiring

This test suite validates the ComponentFactory implementation:
- Component type mapping and validation
- Direct component instantiation
- Error handling and validation
- Configuration validation integration
- Performance characteristics
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.core.component_factory import ComponentFactory
from src.core.interfaces import (
    DocumentProcessor, Embedder, VectorStore, 
    Retriever, AnswerGenerator
)


class TestComponentFactory:
    """Test suite for ComponentFactory functionality."""
    
    def test_get_available_components(self):
        """Test retrieving available components."""
        
        available = ComponentFactory.get_available_components()
        
        # Check structure
        assert isinstance(available, dict)
        assert "processors" in available
        assert "embedders" in available
        assert "vector_stores" in available
        assert "retrievers" in available
        assert "generators" in available
        
        # Check content
        assert "hybrid_pdf" in available["processors"]
        assert "sentence_transformer" in available["embedders"]
        assert "faiss" in available["vector_stores"]
        assert "unified" in available["retrievers"]
        assert "hybrid" in available["retrievers"]
        assert "adaptive" in available["generators"]
    
    def test_component_aliases(self):
        """Test that component aliases are properly mapped."""
        
        available = ComponentFactory.get_available_components()
        
        # Check aliases exist
        assert "pdf_processor" in available["processors"]  # Alias for hybrid_pdf
        assert "sentence_transformers" in available["embedders"]  # Alias for sentence_transformer
        assert "adaptive_generator" in available["generators"]  # Alias for adaptive
    
    def test_is_supported(self):
        """Test component support checking."""
        
        # Valid components
        assert ComponentFactory.is_supported("processor", "hybrid_pdf") == True
        assert ComponentFactory.is_supported("embedder", "sentence_transformer") == True
        assert ComponentFactory.is_supported("vector_store", "faiss") == True
        assert ComponentFactory.is_supported("retriever", "unified") == True
        assert ComponentFactory.is_supported("retriever", "hybrid") == True
        assert ComponentFactory.is_supported("generator", "adaptive") == True
        
        # Aliases
        assert ComponentFactory.is_supported("processor", "pdf_processor") == True
        assert ComponentFactory.is_supported("embedder", "sentence_transformers") == True
        assert ComponentFactory.is_supported("generator", "adaptive_generator") == True
        
        # Invalid components
        assert ComponentFactory.is_supported("processor", "unknown") == False
        assert ComponentFactory.is_supported("unknown_type", "any") == False
        assert ComponentFactory.is_supported("embedder", "invalid") == False


class TestProcessorCreation:
    """Test document processor creation."""
    
    def test_create_processor_success(self):
        """Test successful processor creation."""
        
        processor = ComponentFactory.create_processor(
            "hybrid_pdf",
            chunk_size=1000,
            chunk_overlap=200
        )
        
        assert isinstance(processor, DocumentProcessor)
        assert hasattr(processor, 'process')
        assert callable(processor.process)
    
    def test_create_processor_alias(self):
        """Test processor creation with alias."""
        
        processor = ComponentFactory.create_processor(
            "pdf_processor",  # Alias for hybrid_pdf
            chunk_size=1000,
            chunk_overlap=200
        )
        
        assert isinstance(processor, DocumentProcessor)
    
    def test_create_processor_invalid_type(self):
        """Test processor creation with invalid type."""
        
        with pytest.raises(ValueError) as exc_info:
            ComponentFactory.create_processor("unknown_processor")
        
        error_msg = str(exc_info.value)
        assert "Unknown processor type" in error_msg
        assert "Available processors:" in error_msg
        assert "hybrid_pdf" in error_msg
    
    def test_create_processor_invalid_args(self):
        """Test processor creation with invalid arguments."""
        
        with pytest.raises(TypeError) as exc_info:
            ComponentFactory.create_processor("hybrid_pdf", invalid_arg="value")
        
        error_msg = str(exc_info.value)
        assert "Failed to create processor" in error_msg
        assert "hybrid_pdf" in error_msg


class TestEmbedderCreation:
    """Test embedder creation."""
    
    def test_create_embedder_success(self):
        """Test successful embedder creation."""
        
        embedder = ComponentFactory.create_embedder(
            "sentence_transformer",
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            use_mps=False
        )
        
        assert isinstance(embedder, Embedder)
        assert hasattr(embedder, 'embed')
        assert callable(embedder.embed)
        assert hasattr(embedder, 'embedding_dim')
    
    def test_create_embedder_alias(self):
        """Test embedder creation with alias."""
        
        embedder = ComponentFactory.create_embedder(
            "sentence_transformers",  # Alias
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            use_mps=False
        )
        
        assert isinstance(embedder, Embedder)
    
    def test_create_embedder_invalid_type(self):
        """Test embedder creation with invalid type."""
        
        with pytest.raises(ValueError) as exc_info:
            ComponentFactory.create_embedder("unknown_embedder")
        
        error_msg = str(exc_info.value)
        assert "Unknown embedder type" in error_msg
        assert "Available embedders:" in error_msg
        assert "sentence_transformer" in error_msg


class TestVectorStoreCreation:
    """Test vector store creation."""
    
    def test_create_vector_store_success(self):
        """Test successful vector store creation."""
        
        vector_store = ComponentFactory.create_vector_store(
            "faiss",
            embedding_dim=384,
            index_type="IndexFlatIP"
        )
        
        assert isinstance(vector_store, VectorStore)
        assert hasattr(vector_store, 'add')
        assert callable(vector_store.add)
    
    def test_create_vector_store_invalid_type(self):
        """Test vector store creation with invalid type."""
        
        with pytest.raises(ValueError) as exc_info:
            ComponentFactory.create_vector_store("unknown_store")
        
        error_msg = str(exc_info.value)
        assert "Unknown vector store type" in error_msg
        assert "Available vector stores:" in error_msg
        assert "faiss" in error_msg


class TestRetrieverCreation:
    """Test retriever creation."""
    
    def test_create_unified_retriever_success(self):
        """Test successful unified retriever creation."""
        
        # Create embedder first
        embedder = ComponentFactory.create_embedder(
            "sentence_transformer",
            use_mps=False
        )
        
        retriever = ComponentFactory.create_retriever(
            "unified",
            embedder=embedder,
            embedding_dim=384,
            dense_weight=0.7
        )
        
        assert isinstance(retriever, Retriever)
        assert hasattr(retriever, 'retrieve')
        assert callable(retriever.retrieve)
        assert hasattr(retriever, 'index_documents')
    
    def test_create_hybrid_retriever_success(self):
        """Test successful hybrid retriever creation."""
        
        # Create dependencies
        embedder = ComponentFactory.create_embedder("sentence_transformer", use_mps=False)
        vector_store = ComponentFactory.create_vector_store("faiss", embedding_dim=384)
        
        retriever = ComponentFactory.create_retriever(
            "hybrid",
            vector_store=vector_store,
            embedder=embedder,
            dense_weight=0.7
        )
        
        assert isinstance(retriever, Retriever)
        assert hasattr(retriever, 'retrieve')
        assert callable(retriever.retrieve)
    
    def test_create_retriever_invalid_type(self):
        """Test retriever creation with invalid type."""
        
        with pytest.raises(ValueError) as exc_info:
            ComponentFactory.create_retriever("unknown_retriever")
        
        error_msg = str(exc_info.value)
        assert "Unknown retriever type" in error_msg
        assert "Available retrievers:" in error_msg
        assert "unified" in error_msg
        assert "hybrid" in error_msg
    
    def test_create_retriever_missing_args(self):
        """Test retriever creation with missing required arguments."""
        
        with pytest.raises(TypeError) as exc_info:
            ComponentFactory.create_retriever("unified")  # Missing embedder
        
        error_msg = str(exc_info.value)
        assert "Failed to create retriever" in error_msg
        assert "unified" in error_msg


class TestGeneratorCreation:
    """Test answer generator creation."""
    
    def test_create_generator_success(self):
        """Test successful generator creation."""
        
        generator = ComponentFactory.create_generator(
            "adaptive",
            model_name="sshleifer/distilbart-cnn-12-6",
            max_tokens=256
        )
        
        assert isinstance(generator, AnswerGenerator)
        assert hasattr(generator, 'generate')
        assert callable(generator.generate)
    
    def test_create_generator_alias(self):
        """Test generator creation with alias."""
        
        generator = ComponentFactory.create_generator(
            "adaptive_generator",  # Alias
            model_name="sshleifer/distilbart-cnn-12-6",
            max_tokens=256
        )
        
        assert isinstance(generator, AnswerGenerator)
    
    def test_create_modular_generator_success(self):
        """Test successful modular generator creation."""
        
        generator = ComponentFactory.create_generator(
            "adaptive_modular",  # New modular implementation
            model_name="llama3.2",
            temperature=0.5,
            max_tokens=512
        )
        
        assert isinstance(generator, AnswerGenerator)
        assert hasattr(generator, 'generate')
        assert hasattr(generator, 'get_component_info')
        
        # Test that sub-components are visible
        info = generator.get_component_info()
        assert 'prompt_builder' in info
        assert 'llm_client' in info
        assert 'response_parser' in info
        assert 'confidence_scorer' in info
        
        # Verify it's the modular implementation
        assert info['llm_client']['class'] == 'OllamaAdapter'
        assert info['prompt_builder']['class'] == 'SimplePromptBuilder'
    
    def test_create_generator_invalid_type(self):
        """Test generator creation with invalid type."""
        
        with pytest.raises(ValueError) as exc_info:
            ComponentFactory.create_generator("unknown_generator")
        
        error_msg = str(exc_info.value)
        assert "Unknown generator type" in error_msg
        assert "Available generators:" in error_msg
        assert "adaptive" in error_msg


class TestConfigurationValidation:
    """Test configuration validation functionality."""
    
    def test_validate_configuration_success_unified(self):
        """Test successful unified configuration validation."""
        
        config = {
            "document_processor": {"type": "hybrid_pdf", "config": {"chunk_size": 1000}},
            "embedder": {"type": "sentence_transformer", "config": {"use_mps": False}},
            "retriever": {"type": "unified", "config": {"embedding_dim": 384}},
            "answer_generator": {"type": "adaptive", "config": {"model_name": "sshleifer/distilbart-cnn-12-6"}}
        }
        
        errors = ComponentFactory.validate_configuration(config)
        assert len(errors) == 0
    
    def test_validate_configuration_success_legacy(self):
        """Test successful legacy configuration validation."""
        
        config = {
            "document_processor": {"type": "hybrid_pdf", "config": {"chunk_size": 1000}},
            "embedder": {"type": "sentence_transformer", "config": {"use_mps": False}},
            "vector_store": {"type": "faiss", "config": {"embedding_dim": 384}},
            "retriever": {"type": "hybrid", "config": {"dense_weight": 0.7}},
            "answer_generator": {"type": "adaptive", "config": {"model_name": "sshleifer/distilbart-cnn-12-6"}}
        }
        
        errors = ComponentFactory.validate_configuration(config)
        assert len(errors) == 0
    
    def test_validate_configuration_missing_required(self):
        """Test validation with missing required components."""
        
        config = {
            "document_processor": {"type": "hybrid_pdf", "config": {}},
            # Missing embedder
            "retriever": {"type": "unified", "config": {}},
            "answer_generator": {"type": "adaptive", "config": {}}
        }
        
        errors = ComponentFactory.validate_configuration(config)
        assert len(errors) > 0
        assert any("Missing required component: embedder" in error for error in errors)
    
    def test_validate_configuration_invalid_type(self):
        """Test validation with invalid component type."""
        
        config = {
            "document_processor": {"type": "unknown_processor", "config": {}},
            "embedder": {"type": "sentence_transformer", "config": {}},
            "retriever": {"type": "unified", "config": {}},
            "answer_generator": {"type": "adaptive", "config": {}}
        }
        
        errors = ComponentFactory.validate_configuration(config)
        assert len(errors) > 0
        assert any("Unknown document_processor type" in error for error in errors)
        assert any("Available:" in error for error in errors)
    
    def test_validate_configuration_invalid_structure(self):
        """Test validation with invalid configuration structure."""
        
        config = {
            "document_processor": {"invalid_key": "value"},  # Missing 'type'
            "embedder": {"type": "sentence_transformer", "config": {}},
            "retriever": {"type": "unified", "config": {}},
            "answer_generator": {"type": "adaptive", "config": {}}
        }
        
        errors = ComponentFactory.validate_configuration(config)
        assert len(errors) > 0
        assert any("missing 'type' field" in error for error in errors)


class TestFactoryPerformance:
    """Test ComponentFactory performance characteristics."""
    
    def test_component_creation_speed(self):
        """Test that component creation is reasonably fast."""
        
        import time
        
        # Test processor creation speed
        start = time.time()
        for _ in range(10):
            processor = ComponentFactory.create_processor("hybrid_pdf", chunk_size=1000)
        processor_time = (time.time() - start) / 10
        
        # Should be fast (less than 100ms per component)
        assert processor_time < 0.1, f"Processor creation too slow: {processor_time:.3f}s"
        
        # Test embedder creation speed
        start = time.time()
        for _ in range(5):  # Fewer iterations since embedder is slower
            embedder = ComponentFactory.create_embedder("sentence_transformer", use_mps=False)
        embedder_time = (time.time() - start) / 5
        
        # Embedder can be slower but should be reasonable
        assert embedder_time < 2.0, f"Embedder creation too slow: {embedder_time:.3f}s"
    
    def test_error_handling_speed(self):
        """Test that error handling is fast."""
        
        import time
        
        # Test error detection speed
        start = time.time()
        for _ in range(100):
            try:
                ComponentFactory.create_processor("invalid_type")
            except ValueError:
                pass  # Expected
        error_time = (time.time() - start) / 100
        
        # Error handling should be very fast
        assert error_time < 0.001, f"Error handling too slow: {error_time:.5f}s"
    
    def test_validation_speed(self):
        """Test that configuration validation is fast."""
        
        import time
        
        config = {
            "document_processor": {"type": "hybrid_pdf", "config": {}},
            "embedder": {"type": "sentence_transformer", "config": {}},
            "retriever": {"type": "unified", "config": {}},
            "answer_generator": {"type": "adaptive", "config": {}}
        }
        
        # Test validation speed
        start = time.time()
        for _ in range(50):
            errors = ComponentFactory.validate_configuration(config)
        validation_time = (time.time() - start) / 50
        
        # Validation should be very fast
        assert validation_time < 0.001, f"Validation too slow: {validation_time:.5f}s"


class TestFactoryIntegration:
    """Test ComponentFactory integration scenarios."""
    
    def test_end_to_end_pipeline_creation(self):
        """Test creating a complete pipeline using only the factory."""
        
        # Create all components
        processor = ComponentFactory.create_processor("hybrid_pdf", chunk_size=1000)
        embedder = ComponentFactory.create_embedder("sentence_transformer", use_mps=False)
        retriever = ComponentFactory.create_retriever("unified", embedder=embedder, embedding_dim=384)
        generator = ComponentFactory.create_generator("adaptive", model_name="sshleifer/distilbart-cnn-12-6")
        
        # Verify all components are created and have correct interfaces
        assert isinstance(processor, DocumentProcessor)
        assert isinstance(embedder, Embedder)
        assert isinstance(retriever, Retriever)
        assert isinstance(generator, AnswerGenerator)
        
        # Verify components have required methods
        assert hasattr(processor, 'process')
        assert hasattr(embedder, 'embed')
        assert hasattr(retriever, 'retrieve')
        assert hasattr(generator, 'generate')
    
    def test_legacy_vs_unified_architecture(self):
        """Test creating both legacy and unified architectures."""
        
        # Create embedder for both architectures
        embedder = ComponentFactory.create_embedder("sentence_transformer", use_mps=False)
        
        # Legacy architecture
        vector_store = ComponentFactory.create_vector_store("faiss", embedding_dim=384)
        legacy_retriever = ComponentFactory.create_retriever(
            "hybrid",
            vector_store=vector_store,
            embedder=embedder,
            dense_weight=0.7
        )
        
        # Unified architecture  
        unified_retriever = ComponentFactory.create_retriever(
            "unified",
            embedder=embedder,
            embedding_dim=384,
            dense_weight=0.7
        )
        
        # Both should be valid retrievers
        assert isinstance(legacy_retriever, Retriever)
        assert isinstance(unified_retriever, Retriever)
        
        # Both should have retrieve method
        assert hasattr(legacy_retriever, 'retrieve')
        assert hasattr(unified_retriever, 'retrieve')
    
    def test_component_reuse(self):
        """Test reusing components across multiple creations."""
        
        # Create embedder once
        embedder = ComponentFactory.create_embedder("sentence_transformer", use_mps=False)
        
        # Use same embedder for multiple retrievers
        retriever1 = ComponentFactory.create_retriever("unified", embedder=embedder, embedding_dim=384)
        retriever2 = ComponentFactory.create_retriever("unified", embedder=embedder, embedding_dim=384, dense_weight=0.8)
        
        # Both should work with the same embedder
        assert isinstance(retriever1, Retriever)
        assert isinstance(retriever2, Retriever)
    
    def test_alias_consistency(self):
        """Test that aliases produce equivalent components."""
        
        # Create components using primary names
        processor1 = ComponentFactory.create_processor("hybrid_pdf", chunk_size=1000)
        embedder1 = ComponentFactory.create_embedder("sentence_transformer", use_mps=False)
        generator1 = ComponentFactory.create_generator("adaptive", model_name="sshleifer/distilbart-cnn-12-6")
        
        # Create components using aliases
        processor2 = ComponentFactory.create_processor("pdf_processor", chunk_size=1000)
        embedder2 = ComponentFactory.create_embedder("sentence_transformers", use_mps=False)
        generator2 = ComponentFactory.create_generator("adaptive_generator", model_name="sshleifer/distilbart-cnn-12-6")
        
        # Should be same types
        assert type(processor1) == type(processor2)
        assert type(embedder1) == type(embedder2)
        assert type(generator1) == type(generator2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])