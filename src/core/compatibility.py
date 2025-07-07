"""
Backward compatibility layer for RAGPipeline.

This module provides backward compatibility during the migration to the
new Platform Orchestrator architecture. It maintains the existing RAGPipeline
API while delegating to the new components.
"""

import logging
import warnings
from typing import List, Dict, Any, Optional
from pathlib import Path

from .platform_orchestrator import PlatformOrchestrator
from .query_processor import QueryProcessor
from .interfaces import Answer

logger = logging.getLogger(__name__)


class RAGPipelineCompatibility:
    """
    Backward compatibility wrapper for RAGPipeline.
    
    This class maintains the existing RAGPipeline API while delegating
    to the new Platform Orchestrator architecture. All methods issue
    deprecation warnings to encourage migration.
    
    Example:
        # Old code continues to work
        pipeline = RAGPipeline("config.yaml")
        pipeline.index_document(Path("document.pdf"))
        answer = pipeline.query("What is RISC-V?")
        
        # But users are warned to migrate to:
        orchestrator = PlatformOrchestrator("config.yaml")
        orchestrator.process_document(Path("document.pdf"))
        answer = orchestrator.process_query("What is RISC-V?")
    """
    
    def __init__(self, config_path: Path):
        """
        Initialize compatibility layer with deprecation warning.
        
        Args:
            config_path: Path to YAML configuration file
        """
        warnings.warn(
            "RAGPipeline is deprecated and will be removed in version 2.0. "
            "Please migrate to PlatformOrchestrator:\n"
            "  Old: pipeline = RAGPipeline(config_path)\n"
            "  New: orchestrator = PlatformOrchestrator(config_path)",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Convert string to Path if needed
        if isinstance(config_path, str):
            config_path = Path(config_path)
        
        # Initialize the new orchestrator
        self.orchestrator = PlatformOrchestrator(config_path)
        
        # Store config path for compatibility
        self.config_path = config_path
        self.config = self.orchestrator.config
        self.config_manager = self.orchestrator.config_manager
        
        # Create query processor for query method
        retriever = self.orchestrator.get_component('retriever')
        generator = self.orchestrator.get_component('answer_generator')
        if retriever and generator:
            self.query_processor = QueryProcessor(retriever, generator)
        else:
            self.query_processor = None
        
        logger.info("RAGPipeline compatibility layer initialized")
    
    def index_document(self, file_path: Path) -> int:
        """
        Index a document (compatibility method).
        
        Args:
            file_path: Path to document file
            
        Returns:
            Number of document chunks created
        """
        warnings.warn(
            "index_document() is deprecated. Use PlatformOrchestrator.process_document() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        return self.orchestrator.process_document(file_path)
    
    def index_documents(self, file_paths: List[Path]) -> Dict[str, int]:
        """
        Index multiple documents (compatibility method).
        
        Args:
            file_paths: List of paths to document files
            
        Returns:
            Dictionary mapping file paths to chunk counts
        """
        warnings.warn(
            "index_documents() is deprecated. Use PlatformOrchestrator.process_documents() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        return self.orchestrator.process_documents(file_paths)
    
    def query(self, query: str, k: int = 5) -> Answer:
        """
        Query the pipeline (compatibility method).
        
        Args:
            query: User query string
            k: Number of documents to retrieve
            
        Returns:
            Answer object with generated text and metadata
        """
        warnings.warn(
            "query() is deprecated. Use PlatformOrchestrator.process_query() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Use query processor if available for better compatibility
        if self.query_processor:
            return self.query_processor.process(query, k)
        else:
            return self.orchestrator.process_query(query, k)
    
    def get_component(self, name: str) -> Optional[Any]:
        """
        Get a specific component (compatibility method).
        
        Args:
            name: Component name
            
        Returns:
            Component instance or None if not found
        """
        warnings.warn(
            "get_component() is deprecated. Use PlatformOrchestrator.get_component() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Map old component names to new ones if needed
        component_name_map = {
            'processor': 'document_processor',
            'embedder': 'embedder',
            'vector_store': 'vector_store',
            'retriever': 'retriever',
            'generator': 'answer_generator'
        }
        
        mapped_name = component_name_map.get(name, name)
        return self.orchestrator.get_component(mapped_name)
    
    def get_pipeline_info(self) -> Dict[str, Any]:
        """
        Get pipeline info (compatibility method).
        
        Returns:
            Dictionary with pipeline information
        """
        warnings.warn(
            "get_pipeline_info() is deprecated. Use PlatformOrchestrator.get_system_health() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Transform system health to pipeline info format
        health = self.orchestrator.get_system_health()
        
        return {
            "config_path": health.get("config_path", str(self.config_path)),
            "initialized": health.get("initialized", False),
            "components": health.get("components", {})
        }
    
    def clear_index(self) -> None:
        """
        Clear all indexed documents (compatibility method).
        """
        warnings.warn(
            "clear_index() is deprecated. Use PlatformOrchestrator.clear_index() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        self.orchestrator.clear_index()
    
    def reload_config(self) -> None:
        """
        Reload configuration and reinitialize (compatibility method).
        """
        warnings.warn(
            "reload_config() is deprecated. Use PlatformOrchestrator.reload_config() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        self.orchestrator.reload_config()
        
        # Recreate query processor after reload
        retriever = self.orchestrator.get_component('retriever')
        generator = self.orchestrator.get_component('answer_generator')
        if retriever and generator:
            self.query_processor = QueryProcessor(retriever, generator)
    
    def validate_configuration(self) -> List[str]:
        """
        Validate configuration (compatibility method).
        
        Returns:
            List of validation errors
        """
        warnings.warn(
            "validate_configuration() is deprecated. Use PlatformOrchestrator.validate_configuration() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        return self.orchestrator.validate_configuration()
    
    # Provide access to internal components for compatibility
    @property
    def _components(self):
        """Access to components dictionary (compatibility)."""
        warnings.warn(
            "Direct access to _components is deprecated. Use get_component() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.orchestrator._components
    
    @property
    def _initialized(self):
        """Access to initialized flag (compatibility)."""
        warnings.warn(
            "Direct access to _initialized is deprecated. Use get_system_health() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.orchestrator._initialized
    
    def __str__(self) -> str:
        """String representation."""
        return f"RAGPipeline(config={self.config_path}) [DEPRECATED - Use PlatformOrchestrator]"
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return (f"RAGPipelineCompatibility(config_path={self.config_path}, "
                f"orchestrator={repr(self.orchestrator)})")