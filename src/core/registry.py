"""
Component Registry for the modular RAG system.

This module provides a centralized registry for all component implementations,
enabling dynamic component discovery, registration, and instantiation. It supports
type-safe operations and provides decorators for auto-registration.
"""

from typing import Dict, Type, Any, Optional, Callable
import logging
from functools import wraps

from .interfaces import (
    DocumentProcessor, 
    Embedder, 
    VectorStore, 
    Retriever, 
    AnswerGenerator
)

logger = logging.getLogger(__name__)


class ComponentRegistry:
    """
    Central registry for all component implementations.
    
    This registry allows components to be registered by name and instantiated
    dynamically based on configuration. It provides type safety and validation
    to ensure only compatible components are registered.
    
    Example:
        # Register a component manually
        ComponentRegistry.register_processor("pdf", MyPDFProcessor)
        
        # Create an instance
        processor = ComponentRegistry.create_processor("pdf", chunk_size=1024)
        
        # Or use the decorator for auto-registration
        @register_component("processor", "pdf")
        class MyPDFProcessor(DocumentProcessor):
            ...
    """
    
    # Component registries by type
    _processors: Dict[str, Type[DocumentProcessor]] = {}
    _embedders: Dict[str, Type[Embedder]] = {}
    _vector_stores: Dict[str, Type[VectorStore]] = {}
    _retrievers: Dict[str, Type[Retriever]] = {}
    _generators: Dict[str, Type[AnswerGenerator]] = {}
    
    @classmethod
    def register_processor(cls, name: str, processor_class: Type[DocumentProcessor]) -> None:
        """
        Register a document processor implementation.
        
        Args:
            name: Unique name for this processor
            processor_class: Class implementing DocumentProcessor interface
            
        Raises:
            TypeError: If processor_class doesn't implement DocumentProcessor
            ValueError: If name is already registered
        """
        cls._validate_component(name, processor_class, DocumentProcessor, cls._processors)
        cls._processors[name] = processor_class
        logger.info(f"Registered document processor: {name}")
    
    @classmethod
    def register_embedder(cls, name: str, embedder_class: Type[Embedder]) -> None:
        """
        Register an embedder implementation.
        
        Args:
            name: Unique name for this embedder
            embedder_class: Class implementing Embedder interface
            
        Raises:
            TypeError: If embedder_class doesn't implement Embedder
            ValueError: If name is already registered
        """
        cls._validate_component(name, embedder_class, Embedder, cls._embedders)
        cls._embedders[name] = embedder_class
        logger.info(f"Registered embedder: {name}")
    
    @classmethod
    def register_vector_store(cls, name: str, store_class: Type[VectorStore]) -> None:
        """
        Register a vector store implementation.
        
        Args:
            name: Unique name for this vector store
            store_class: Class implementing VectorStore interface
            
        Raises:
            TypeError: If store_class doesn't implement VectorStore
            ValueError: If name is already registered
        """
        cls._validate_component(name, store_class, VectorStore, cls._vector_stores)
        cls._vector_stores[name] = store_class
        logger.info(f"Registered vector store: {name}")
    
    @classmethod
    def register_retriever(cls, name: str, retriever_class: Type[Retriever]) -> None:
        """
        Register a retriever implementation.
        
        Args:
            name: Unique name for this retriever
            retriever_class: Class implementing Retriever interface
            
        Raises:
            TypeError: If retriever_class doesn't implement Retriever
            ValueError: If name is already registered
        """
        cls._validate_component(name, retriever_class, Retriever, cls._retrievers)
        cls._retrievers[name] = retriever_class
        logger.info(f"Registered retriever: {name}")
    
    @classmethod
    def register_generator(cls, name: str, generator_class: Type[AnswerGenerator]) -> None:
        """
        Register an answer generator implementation.
        
        Args:
            name: Unique name for this generator
            generator_class: Class implementing AnswerGenerator interface
            
        Raises:
            TypeError: If generator_class doesn't implement AnswerGenerator
            ValueError: If name is already registered
        """
        cls._validate_component(name, generator_class, AnswerGenerator, cls._generators)
        cls._generators[name] = generator_class
        logger.info(f"Registered answer generator: {name}")
    
    @classmethod
    def create_processor(cls, name: str, **kwargs) -> DocumentProcessor:
        """
        Create a document processor instance.
        
        Args:
            name: Name of the registered processor
            **kwargs: Arguments to pass to the processor constructor
            
        Returns:
            Instantiated DocumentProcessor
            
        Raises:
            ValueError: If processor name is not registered
            TypeError: If constructor arguments are invalid
        """
        if name not in cls._processors:
            available = list(cls._processors.keys())
            raise ValueError(f"Unknown processor '{name}'. Available: {available}")
        
        try:
            return cls._processors[name](**kwargs)
        except Exception as e:
            raise TypeError(f"Failed to create processor '{name}': {e}") from e
    
    @classmethod
    def create_embedder(cls, name: str, **kwargs) -> Embedder:
        """
        Create an embedder instance.
        
        Args:
            name: Name of the registered embedder
            **kwargs: Arguments to pass to the embedder constructor
            
        Returns:
            Instantiated Embedder
            
        Raises:
            ValueError: If embedder name is not registered
            TypeError: If constructor arguments are invalid
        """
        if name not in cls._embedders:
            available = list(cls._embedders.keys())
            raise ValueError(f"Unknown embedder '{name}'. Available: {available}")
        
        try:
            return cls._embedders[name](**kwargs)
        except Exception as e:
            raise TypeError(f"Failed to create embedder '{name}': {e}") from e
    
    @classmethod
    def create_vector_store(cls, name: str, **kwargs) -> VectorStore:
        """
        Create a vector store instance.
        
        Args:
            name: Name of the registered vector store
            **kwargs: Arguments to pass to the vector store constructor
            
        Returns:
            Instantiated VectorStore
            
        Raises:
            ValueError: If vector store name is not registered
            TypeError: If constructor arguments are invalid
        """
        if name not in cls._vector_stores:
            available = list(cls._vector_stores.keys())
            raise ValueError(f"Unknown vector store '{name}'. Available: {available}")
        
        try:
            return cls._vector_stores[name](**kwargs)
        except Exception as e:
            raise TypeError(f"Failed to create vector store '{name}': {e}") from e
    
    @classmethod
    def create_retriever(cls, name: str, **kwargs) -> Retriever:
        """
        Create a retriever instance.
        
        Args:
            name: Name of the registered retriever
            **kwargs: Arguments to pass to the retriever constructor
            
        Returns:
            Instantiated Retriever
            
        Raises:
            ValueError: If retriever name is not registered
            TypeError: If constructor arguments are invalid
        """
        if name not in cls._retrievers:
            available = list(cls._retrievers.keys())
            raise ValueError(f"Unknown retriever '{name}'. Available: {available}")
        
        try:
            return cls._retrievers[name](**kwargs)
        except Exception as e:
            raise TypeError(f"Failed to create retriever '{name}': {e}") from e
    
    @classmethod
    def create_generator(cls, name: str, **kwargs) -> AnswerGenerator:
        """
        Create an answer generator instance.
        
        Args:
            name: Name of the registered generator
            **kwargs: Arguments to pass to the generator constructor
            
        Returns:
            Instantiated AnswerGenerator
            
        Raises:
            ValueError: If generator name is not registered
            TypeError: If constructor arguments are invalid
        """
        if name not in cls._generators:
            available = list(cls._generators.keys())
            raise ValueError(f"Unknown generator '{name}'. Available: {available}")
        
        try:
            return cls._generators[name](**kwargs)
        except Exception as e:
            raise TypeError(f"Failed to create generator '{name}': {e}") from e
    
    @classmethod
    def list_processors(cls) -> list[str]:
        """Get list of registered processor names."""
        return list(cls._processors.keys())
    
    @classmethod
    def list_embedders(cls) -> list[str]:
        """Get list of registered embedder names."""
        return list(cls._embedders.keys())
    
    @classmethod
    def list_vector_stores(cls) -> list[str]:
        """Get list of registered vector store names."""
        return list(cls._vector_stores.keys())
    
    @classmethod
    def list_retrievers(cls) -> list[str]:
        """Get list of registered retriever names."""
        return list(cls._retrievers.keys())
    
    @classmethod
    def list_generators(cls) -> list[str]:
        """Get list of registered generator names."""
        return list(cls._generators.keys())
    
    @classmethod
    def is_registered(cls, component_type: str, name: str) -> bool:
        """
        Check if a component is registered.
        
        Args:
            component_type: Type of component ('processor', 'embedder', 'vector_store', 
                           'retriever', 'generator')
            name: Component name to check
            
        Returns:
            True if component is registered, False otherwise
        """
        registries = {
            'processor': cls._processors,
            'embedder': cls._embedders,
            'vector_store': cls._vector_stores,
            'retriever': cls._retrievers,
            'generator': cls._generators
        }
        
        registry = registries.get(component_type)
        if registry is None:
            return False
        
        return name in registry
    
    @classmethod
    def clear_all(cls) -> None:
        """Clear all registered components. Useful for testing."""
        cls._processors.clear()
        cls._embedders.clear()
        cls._vector_stores.clear()
        cls._retrievers.clear()
        cls._generators.clear()
        logger.info("Cleared all component registrations")
    
    @classmethod
    def _validate_component(
        cls, 
        name: str, 
        component_class: Type, 
        interface_class: Type, 
        registry: Dict[str, Type]
    ) -> None:
        """
        Validate a component before registration.
        
        Args:
            name: Component name
            component_class: Class to register
            interface_class: Required interface
            registry: Registry to check for duplicates
            
        Raises:
            TypeError: If component doesn't implement interface
            ValueError: If name is already registered
        """
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Component name must be a non-empty string")
        
        if not issubclass(component_class, interface_class):
            raise TypeError(
                f"Component {component_class.__name__} must implement {interface_class.__name__}"
            )
        
        if name in registry:
            existing = registry[name].__name__
            raise ValueError(
                f"Component name '{name}' already registered with {existing}"
            )


def register_component(component_type: str, name: str) -> Callable:
    """
    Decorator to automatically register components.
    
    Args:
        component_type: Type of component ('processor', 'embedder', 'vector_store', 
                       'retriever', 'generator')
        name: Unique name for the component
        
    Returns:
        Decorator function
        
    Example:
        @register_component("processor", "hybrid_pdf")
        class HybridPDFProcessor(DocumentProcessor):
            ...
    """
    def decorator(cls: Type) -> Type:
        """Register the decorated class."""
        if component_type == "processor":
            ComponentRegistry.register_processor(name, cls)
        elif component_type == "embedder":
            ComponentRegistry.register_embedder(name, cls)
        elif component_type == "vector_store":
            ComponentRegistry.register_vector_store(name, cls)
        elif component_type == "retriever":
            ComponentRegistry.register_retriever(name, cls)
        elif component_type == "generator":
            ComponentRegistry.register_generator(name, cls)
        else:
            valid_types = ["processor", "embedder", "vector_store", "retriever", "generator"]
            raise ValueError(f"Invalid component type '{component_type}'. Valid types: {valid_types}")
        
        return cls
    
    return decorator


def get_available_components() -> Dict[str, list[str]]:
    """
    Get all available components organized by type.
    
    Returns:
        Dictionary mapping component types to lists of available component names
    """
    return {
        "processors": ComponentRegistry.list_processors(),
        "embedders": ComponentRegistry.list_embedders(),
        "vector_stores": ComponentRegistry.list_vector_stores(),
        "retrievers": ComponentRegistry.list_retrievers(),
        "generators": ComponentRegistry.list_generators(),
    }