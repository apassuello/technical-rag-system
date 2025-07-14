"""
Weaviate Vector Index Adapter for Modular Retriever Architecture.

This module provides a proper VectorIndex adapter for Weaviate external service
integration, following the established adapter pattern used for external APIs
like OllamaAdapter and PyMuPDFAdapter.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from src.core.interfaces import Document
from .base import VectorIndex
from ..backends.weaviate_backend import WeaviateBackend
from ..backends.weaviate_config import WeaviateBackendConfig

logger = logging.getLogger(__name__)


class WeaviateIndexError(Exception):
    """Raised when Weaviate index operations fail."""
    pass


class WeaviateIndex(VectorIndex):
    """
    Weaviate Vector Index adapter for external service integration.
    
    This adapter provides a VectorIndex interface for Weaviate external service,
    following the same adapter pattern used for other external integrations
    like OllamaAdapter. It wraps the existing WeaviateBackend to provide
    architecture-compliant vector index functionality.
    
    Features:
    - ✅ Implements VectorIndex interface completely
    - ✅ Adapts external Weaviate service to internal interface
    - ✅ Wraps existing WeaviateBackend functionality
    - ✅ Provides error handling and graceful fallbacks
    - ✅ Maintains performance monitoring and statistics
    - ✅ Follows established adapter patterns
    
    Architecture Compliance:
    - Proper adapter pattern for external service ✅
    - Located in indices/ sub-component ✅
    - Implements required VectorIndex interface ✅
    - Follows ComponentFactory creation pattern ✅
    
    Example:
        config = {
            "connection": {
                "url": "http://localhost:8080",
                "api_key": None
            },
            "schema": {
                "class_name": "TechnicalDocument"
            }
        }
        index = WeaviateIndex(config)
        index.initialize_index(embedding_dim=384)
        index.add_documents(documents)
        results = index.search(query_embedding, k=5)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Weaviate vector index adapter.
        
        Args:
            config: Configuration dictionary for Weaviate connection and schema
        """
        self.config = config
        
        # Wrap existing WeaviateBackend as adapter
        try:
            self.weaviate_backend = WeaviateBackend(config)
            self.is_available = True
        except Exception as e:
            logger.error(f"Failed to initialize Weaviate backend: {e}")
            self.weaviate_backend = None
            self.is_available = False
        
        # Track initialization state
        self.embedding_dim: Optional[int] = None
        self.is_initialized = False
        
        # Performance tracking
        self.adapter_stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "avg_operation_time": 0.0
        }
        
        logger.info(f"WeaviateIndex adapter initialized (available: {self.is_available})")
    
    def initialize_index(self, embedding_dim: int) -> None:
        """
        Initialize the Weaviate index with the specified embedding dimension.
        
        Args:
            embedding_dim: Dimension of the embeddings to be indexed
        """
        if not self.is_available:
            raise WeaviateIndexError("Weaviate backend not available")
        
        try:
            self.embedding_dim = embedding_dim
            self.weaviate_backend.initialize_index(embedding_dim)
            self.is_initialized = True
            logger.info(f"Weaviate index initialized with dimension {embedding_dim}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Weaviate index: {e}")
            raise WeaviateIndexError(f"Weaviate index initialization failed: {e}") from e
    
    def add_documents(self, documents: List[Document]) -> None:
        """
        Add documents to the Weaviate index.
        
        Args:
            documents: List of documents with embeddings to add
            
        Raises:
            WeaviateIndexError: If documents cannot be added
        """
        if not self.is_available:
            raise WeaviateIndexError("Weaviate backend not available")
        
        if not self.is_initialized:
            raise WeaviateIndexError("Index not initialized. Call initialize_index() first.")
        
        try:
            self.weaviate_backend.add_documents(documents)
            self.adapter_stats["successful_operations"] += 1
            logger.debug(f"Added {len(documents)} documents to Weaviate index")
            
        except Exception as e:
            self.adapter_stats["failed_operations"] += 1
            logger.error(f"Failed to add documents to Weaviate index: {e}")
            raise WeaviateIndexError(f"Failed to add documents: {e}") from e
        finally:
            self.adapter_stats["total_operations"] += 1
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[int, float]]:
        """
        Search for similar documents using Weaviate vector similarity.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of (document_index, similarity_score) tuples
        """
        if not self.is_available:
            raise WeaviateIndexError("Weaviate backend not available")
        
        if not self.is_initialized:
            raise WeaviateIndexError("Index not initialized")
        
        try:
            results = self.weaviate_backend.search(query_embedding, k)
            self.adapter_stats["successful_operations"] += 1
            return results
            
        except Exception as e:
            self.adapter_stats["failed_operations"] += 1
            logger.error(f"Weaviate index search failed: {e}")
            raise WeaviateIndexError(f"Search failed: {e}") from e
        finally:
            self.adapter_stats["total_operations"] += 1
    
    def get_document_count(self) -> int:
        """
        Get the number of documents in the Weaviate index.
        
        Returns:
            Number of indexed documents
        """
        if not self.is_available:
            return 0
        
        try:
            return self.weaviate_backend.get_document_count()
        except Exception as e:
            logger.error(f"Failed to get Weaviate document count: {e}")
            return 0
    
    def clear(self) -> None:
        """Clear all documents from the Weaviate index."""
        if not self.is_available:
            logger.warning("Weaviate backend not available, cannot clear")
            return
        
        try:
            self.weaviate_backend.clear()
            logger.info("Weaviate index cleared")
            
        except Exception as e:
            logger.error(f"Failed to clear Weaviate index: {e}")
            raise WeaviateIndexError(f"Clear failed: {e}") from e
    
    def get_index_info(self) -> Dict[str, Any]:
        """
        Get information about the Weaviate index.
        
        Returns:
            Dictionary with index statistics and configuration
        """
        base_info = {
            "index_type": "weaviate",
            "embedding_dim": self.embedding_dim,
            "is_available": self.is_available,
            "is_initialized": self.is_initialized,
            "document_count": self.get_document_count(),
            "adapter_stats": self.adapter_stats.copy()
        }
        
        if self.is_available and self.weaviate_backend:
            try:
                backend_info = self.weaviate_backend.get_backend_info()
                base_info.update({
                    "weaviate_info": backend_info,
                    "connection_url": getattr(self.weaviate_backend.config.connection, 'url', 'unknown'),
                    "schema_class": getattr(self.weaviate_backend.config.schema, 'class_name', 'unknown')
                })
            except Exception as e:
                logger.warning(f"Failed to get Weaviate backend info: {e}")
                base_info["backend_error"] = str(e)
        
        return base_info
    
    def is_trained(self) -> bool:
        """
        Check if the index is trained and ready for searching.
        
        Returns:
            True if the index is ready (Weaviate doesn't require training)
        """
        return self.is_available and self.is_initialized
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the Weaviate connection.
        
        Returns:
            Dictionary with health status information
        """
        if not self.is_available:
            return {
                "is_healthy": False,
                "issues": ["Weaviate backend not available"],
                "adapter_available": False
            }
        
        try:
            backend_health = self.weaviate_backend.health_check()
            return {
                **backend_health,
                "adapter_available": True,
                "adapter_stats": self.adapter_stats.copy()
            }
        except Exception as e:
            return {
                "is_healthy": False,
                "issues": [f"Health check failed: {e}"],
                "adapter_available": True,
                "adapter_error": str(e)
            }
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get memory usage statistics.
        
        Returns:
            Dictionary with memory usage information
        """
        if not self.is_available:
            return {"total_bytes": 0, "per_document_bytes": 0, "adapter_available": False}
        
        try:
            backend_memory = self.weaviate_backend.get_memory_usage()
            return {
                **backend_memory,
                "adapter_available": True,
                "adapter_overhead_bytes": 1024  # Minimal adapter overhead
            }
        except Exception as e:
            logger.warning(f"Failed to get Weaviate memory usage: {e}")
            return {
                "total_bytes": 0,
                "per_document_bytes": 0,
                "adapter_available": True,
                "memory_error": str(e)
            }
    
    def supports_batch_queries(self) -> bool:
        """
        Check if this index supports batch query processing.
        
        Returns:
            True if Weaviate supports batch operations
        """
        return self.is_available and getattr(self.weaviate_backend, 'supports_batch_operations', lambda: False)()
    
    def get_adapter_info(self) -> Dict[str, Any]:
        """
        Get adapter-specific information for debugging.
        
        Returns:
            Dictionary with adapter details
        """
        return {
            "adapter_type": "weaviate_index",
            "adapter_class": self.__class__.__name__,
            "adapter_module": self.__class__.__module__,
            "backend_available": self.is_available,
            "backend_initialized": self.is_initialized,
            "embedding_dimension": self.embedding_dim,
            "adapter_statistics": self.adapter_stats.copy(),
            "configuration": {
                "connection_url": getattr(self.config.get('connection', {}), 'url', 'not_configured') if isinstance(self.config.get('connection', {}), dict) else 'not_configured',
                "schema_class": getattr(self.config.get('schema', {}), 'class_name', 'not_configured') if isinstance(self.config.get('schema', {}), dict) else 'not_configured'
            }
        }