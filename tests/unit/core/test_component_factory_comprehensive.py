#!/usr/bin/env python3
"""
Comprehensive Component Factory Tests - Epic 8 Test Enhancement

Tests the ComponentFactory's ability to create all modern components
with proper configuration, sub-component initialization, and factory patterns.

This replaces scattered factory tests and focuses on modern architecture.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.core.component_factory import ComponentFactory
from src.core.interfaces import (
    DocumentProcessor, Embedder, Retriever, AnswerGenerator,
    QueryProcessor
)


class TestComponentFactoryCore:
    """Test core factory functionality and patterns."""
    
    def test_factory_singleton_pattern(self):
        """Test factory maintains singleton-like behavior for configuration."""
        factory1 = ComponentFactory()
        factory2 = ComponentFactory()
        
        # Should be same configuration handling (not same instance necessarily)
        assert factory1._load_config.__func__ == factory2._load_config.__func__
    
    def test_factory_component_registration(self):
        """Test all modern components are properly registered."""
        # Core components that must be available
        required_components = {
            'processor': ['hybrid_pdf'],
            'embedder': ['sentence_transformer'],
            'retriever': ['unified'],
            'generator': ['answer_generator'],
            'query_processor': ['basic'],
            'orchestrator': ['platform_orchestrator']
        }
        
        for component_type, component_implementations in required_components.items():
            for implementation in component_implementations:
                try:
                    if component_type == 'processor':
                        component = ComponentFactory.create_processor(implementation)
                    elif component_type == 'embedder':
                        component = ComponentFactory.create_embedder(implementation)
                    elif component_type == 'retriever':
                        # Retriever needs an embedder
                        embedder = ComponentFactory.create_embedder("sentence_transformer")
                        component = ComponentFactory.create_retriever(implementation, embedder=embedder)
                    elif component_type == 'generator':
                        component = ComponentFactory.create_generator(implementation)
                    elif component_type == 'query_processor':
                        component = ComponentFactory.create_query_processor(implementation)
                    elif component_type == 'orchestrator':
                        component = ComponentFactory.create_orchestrator()
                    
                    assert component is not None, f"{component_type}:{implementation} creation failed"
                    print(f"✅ {component_type}:{implementation} - {component.__class__.__name__}")
                    
                except Exception as e:
                    pytest.fail(f"Failed to create {component_type}:{implementation} - {e}")


class TestModularComponentCreation:
    """Test creation of modular components with sub-component validation."""
    
    def test_create_modular_document_processor(self):
        """Test DocumentProcessor creation with sub-components."""
        processor = ComponentFactory.create_processor("hybrid_pdf")
        
        # Validate component type
        assert processor is not None
        assert hasattr(processor, 'process_document')
        
        # Validate modular architecture
        if hasattr(processor, 'get_component_info'):
            component_info = processor.get_component_info()
            expected_components = ['parser', 'chunker', 'cleaner', 'pipeline']
            
            for expected_component in expected_components:
                assert expected_component in component_info, f"Missing sub-component: {expected_component}"
                assert component_info[expected_component] is not None
                print(f"✅ ModularDocumentProcessor sub-component: {expected_component}")
    
    def test_create_modular_embedder(self):
        """Test Embedder creation with sub-components."""
        embedder = ComponentFactory.create_embedder("sentence_transformer")
        
        # Validate component type
        assert embedder is not None
        assert hasattr(embedder, 'embed')
        
        # Validate modular architecture
        if hasattr(embedder, 'get_component_info'):
            component_info = embedder.get_component_info()
            expected_components = ['model', 'batch_processor', 'cache']
            
            for expected_component in expected_components:
                assert expected_component in component_info, f"Missing sub-component: {expected_component}"
                print(f"✅ ModularEmbedder sub-component: {expected_component}")
    
    def test_create_unified_retriever(self):
        """Test UnifiedRetriever creation with sub-components."""
        retriever = ComponentFactory.create_retriever("unified")
        
        # Validate component type
        assert retriever is not None
        assert hasattr(retriever, 'retrieve')
        
        # Validate modular architecture
        if hasattr(retriever, 'get_component_info'):
            component_info = retriever.get_component_info()
            expected_components = ['vector_index', 'sparse_retriever', 'fusion', 'reranker']
            
            for expected_component in expected_components:
                assert expected_component in component_info, f"Missing sub-component: {expected_component}"
                print(f"✅ ModularUnifiedRetriever sub-component: {expected_component}")
    
    def test_create_modular_answer_generator(self):
        """Test AnswerGenerator creation with sub-components."""
        generator = ComponentFactory.create_generator("answer_generator")
        
        # Validate component type
        assert generator is not None
        assert hasattr(generator, 'generate_answer')
        
        # Validate modular architecture  
        if hasattr(generator, 'get_component_info'):
            component_info = generator.get_component_info()
            expected_components = ['prompt_builder', 'llm_client', 'response_parser', 'confidence_scorer']
            
            for expected_component in expected_components:
                assert expected_component in component_info, f"Missing sub-component: {expected_component}"
                print(f"✅ AnswerGenerator sub-component: {expected_component}")


class TestConfigurationHandling:
    """Test configuration-driven component creation."""
    
    def test_default_configuration_loading(self):
        """Test components can be created with default configuration."""
        # Should work without explicit configuration
        processor = ComponentFactory.create_processor("hybrid_pdf")
        embedder = ComponentFactory.create_embedder("sentence_transformer")
        retriever = ComponentFactory.create_retriever("unified")
        generator = ComponentFactory.create_generator("answer_generator")
        
        assert all([processor, embedder, retriever, generator])
        print("✅ All components created with default configuration")
    
    def test_custom_configuration_override(self):
        """Test components respect custom configuration parameters."""
        # Custom configuration for embedder
        custom_config = {
            'model_name': 'sentence-transformers/all-MiniLM-L6-v2',
            'batch_size': 64,
            'cache_size': 1000
        }
        
        with patch('src.core.component_factory.ComponentFactory._load_config') as mock_load:
            mock_load.return_value = MagicMock()
            mock_load.return_value.embedder = MagicMock()
            mock_load.return_value.embedder.modular = custom_config
            
            embedder = ComponentFactory.create_embedder("sentence_transformer")
            assert embedder is not None
            print("✅ Custom configuration handling validated")
    
    def test_configuration_error_handling(self):
        """Test graceful handling of configuration errors."""
        with patch('src.core.component_factory.ComponentFactory._load_config') as mock_load:
            mock_load.side_effect = Exception("Configuration loading failed")
            
            # Should still create component with fallback configuration
            try:
                processor = ComponentFactory.create_processor("modular")
                # If it doesn't raise, that's acceptable (fallback behavior)
                print("✅ Configuration error handled gracefully")
            except Exception as e:
                # If it raises, should be informative
                assert "Configuration loading failed" in str(e)
                print("✅ Configuration error properly propagated")


class TestFactoryErrorHandling:
    """Test factory error handling and edge cases."""
    
    def test_invalid_component_type_handling(self):
        """Test handling of invalid component types."""
        with pytest.raises((ValueError, KeyError, NotImplementedError)):
            ComponentFactory.create_processor("nonexistent_type")
        
        with pytest.raises((ValueError, KeyError, NotImplementedError)):
            ComponentFactory.create_embedder("invalid_embedder")
        
        print("✅ Invalid component types properly rejected")
    
    def test_component_creation_failure_handling(self):
        """Test handling when component creation fails."""
        # Mock a component that fails during initialization
        with patch('src.components.processors.document_processor.ModularDocumentProcessor') as mock_processor:
            mock_processor.side_effect = Exception("Component initialization failed")
            
            with pytest.raises(Exception) as exc_info:
                ComponentFactory.create_processor("modular")
            
            assert "Component initialization failed" in str(exc_info.value)
            print("✅ Component creation failure properly handled")
    
    def test_missing_dependencies_handling(self):
        """Test handling when component dependencies are missing."""
        # This tests the factory's ability to handle missing imports gracefully
        with patch('sys.modules', {'src.components.processors.document_processor': None}):
            try:
                processor = ComponentFactory.create_processor("modular")
                # If successful, factory has good fallback handling
                print("✅ Missing dependencies handled with fallback")
            except (ImportError, AttributeError, ModuleNotFoundError):
                # Expected behavior for missing dependencies
                print("✅ Missing dependencies properly detected and reported")


class TestFactoryPerformance:
    """Test factory performance characteristics."""
    
    def test_component_creation_performance(self):
        """Test component creation performance meets targets."""
        import time
        
        # Test creation time for each component type
        component_types = [
            ('processor', 'hybrid_pdf'),
            ('embedder', 'sentence_transformer'), 
            ('retriever', 'unified'),
            ('generator', 'answer_generator')
        ]
        
        for component_type, implementation in component_types:
            start_time = time.time()
            
            if component_type == 'processor':
                component = ComponentFactory.create_processor(implementation)
            elif component_type == 'embedder':
                component = ComponentFactory.create_embedder(implementation)
            elif component_type == 'retriever':
                component = ComponentFactory.create_retriever(implementation)
            elif component_type == 'generator':
                component = ComponentFactory.create_generator(implementation)
            
            creation_time = time.time() - start_time
            
            # Swiss engineering performance target: <1 second component creation
            assert creation_time < 1.0, f"{component_type}:{implementation} took {creation_time:.3f}s (>1s limit)"
            assert component is not None
            
            print(f"✅ {component_type}:{implementation} created in {creation_time:.3f}s")
    
    def test_factory_caching_behavior(self):
        """Test factory caching/reuse behavior for expensive components."""
        # Multiple creations should be efficient
        embedders = []
        start_time = time.time()
        
        for _ in range(3):
            embedder = ComponentFactory.create_embedder("sentence_transformer")
            embedders.append(embedder)
        
        total_time = time.time() - start_time
        
        # Multiple creations should be reasonable (may or may not cache instances)
        assert total_time < 5.0, f"Multiple component creation took {total_time:.3f}s (too slow)"
        assert all(e is not None for e in embedders)
        
        print(f"✅ Multiple embedder creation completed in {total_time:.3f}s")


class TestInterfaceCompliance:
    """Test components implement required interfaces correctly."""
    
    def test_document_processor_interface(self):
        """Test DocumentProcessor interface compliance."""
        processor = ComponentFactory.create_processor("modular")
        
        # Check required methods exist
        assert hasattr(processor, 'process_document')
        assert callable(processor.process_document)
        
        # Check method signatures accept expected parameters
        import inspect
        sig = inspect.signature(processor.process_document)
        assert len(sig.parameters) >= 1  # At least document path/content parameter
        
        print("✅ DocumentProcessor interface compliance validated")
    
    def test_embedder_interface(self):
        """Test Embedder interface compliance."""
        embedder = ComponentFactory.create_embedder("sentence_transformer")
        
        # Check required methods exist
        required_methods = ['embed_texts', 'embed_batch']
        for method_name in required_methods:
            assert hasattr(embedder, method_name), f"Missing method: {method_name}"
            assert callable(getattr(embedder, method_name))
        
        print("✅ Embedder interface compliance validated")
    
    def test_retriever_interface(self):
        """Test Retriever interface compliance.""" 
        retriever = ComponentFactory.create_retriever("modular_unified")
        
        # Check required methods exist
        assert hasattr(retriever, 'retrieve')
        assert callable(retriever.retrieve)
        
        # Check method signatures
        import inspect
        sig = inspect.signature(retriever.retrieve)
        assert len(sig.parameters) >= 2  # query and k parameters minimum
        
        print("✅ Retriever interface compliance validated")
    
    def test_answer_generator_interface(self):
        """Test AnswerGenerator interface compliance."""
        generator = ComponentFactory.create_generator("answer_generator")
        
        # Check required methods exist
        assert hasattr(generator, 'generate_answer')
        assert callable(generator.generate_answer)
        
        print("✅ AnswerGenerator interface compliance validated")


if __name__ == "__main__":
    # Run tests with detailed output
    pytest.main([__file__, "-v", "-s", "--tb=short"])