"""
FAISS backend adapter for advanced retriever.

This module provides a backend adapter that wraps the existing FAISS
functionality to work with the advanced retriever's unified backend
interface. This enables hot-swapping between FAISS and other backends.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from src.core.interfaces import Document
from ..indices.faiss_index import FAISSIndex
from .weaviate_config import WeaviateBackendConfig  # For consistent interface

logger = logging.getLogger(__name__)


class FAISSBackend:
    """
    FAISS backend adapter for advanced retriever.
    
    This adapter wraps the existing FAISSIndex implementation to provide
    a consistent backend interface that can be hot-swapped with other
    vector database backends like Weaviate.
    
    Features:
    - Wraps existing FAISS functionality
    - Consistent interface with other backends
    - Performance monitoring and statistics
    - Graceful error handling and fallbacks
    - Memory usage optimization
    
    The adapter follows the same patterns as external service adapters
    but wraps internal components instead of making network calls.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize FAISS backend adapter.
        
        Args:
            config: Configuration dictionary for FAISS settings
        """
        self.config = config
        self.faiss_config = config.get("faiss", {})
        
        # Initialize wrapped FAISS index
        self.faiss_index = FAISSIndex(self.faiss_config)
        
        # Performance tracking
        self.stats = {
            "total_operations": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
            "last_operation_time": 0.0,
            "search_count": 0,
            "add_count": 0,
            "error_count": 0
        }
        
        # Backend identification
        self.backend_type = "faiss"
        self.backend_version = "wrapped"
        
        logger.info("FAISS backend adapter initialized")
    
    def initialize_index(self, embedding_dim: int) -> None:
        """
        Initialize the FAISS index with specified dimension.
        
        Args:
            embedding_dim: Dimension of the embedding vectors
        """
        start_time = time.time()
        
        try:
            self.faiss_index.initialize_index(embedding_dim)
            
            # Update stats
            elapsed_time = time.time() - start_time
            self._update_stats("initialize", elapsed_time)
            
            logger.info(f"FAISS backend index initialized with dimension {embedding_dim}")
            
        except Exception as e:
            self.stats["error_count"] += 1
            logger.error(f"Failed to initialize FAISS backend: {str(e)}")
            raise RuntimeError(f"FAISS backend initialization failed: {str(e)}") from e
    
    def add_documents(self, documents: List[Document]) -> None:
        """
        Add documents to the FAISS index.
        
        Args:
            documents: List of documents with embeddings to add
        """
        start_time = time.time()
        
        try:
            if not documents:
                raise ValueError("Cannot add empty document list")
            
            # Validate embeddings
            for i, doc in enumerate(documents):
                if doc.embedding is None:
                    raise ValueError(f"Document {i} missing embedding")
            
            self.faiss_index.add_documents(documents)
            
            # Update stats
            elapsed_time = time.time() - start_time
            self._update_stats("add", elapsed_time)
            self.stats["add_count"] += len(documents)
            
            logger.info(f"Added {len(documents)} documents to FAISS backend")
            
        except Exception as e:
            self.stats["error_count"] += 1
            logger.error(f"Failed to add documents to FAISS backend: {str(e)}")
            raise RuntimeError(f"FAISS backend add failed: {str(e)}") from e
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[int, float]]:
        """
        Search for similar documents using FAISS.
        
        Args:
            query_embedding: Query vector
            k: Number of results to return
            
        Returns:
            List of (document_index, score) tuples
        """
        start_time = time.time()
        
        try:
            if k <= 0:
                raise ValueError("k must be positive")
            
            results = self.faiss_index.search(query_embedding, k=k)
            
            # Update stats
            elapsed_time = time.time() - start_time
            self._update_stats("search", elapsed_time)
            self.stats["search_count"] += 1
            
            logger.debug(f"FAISS backend search returned {len(results)} results in {elapsed_time:.4f}s")
            
            return results
            
        except Exception as e:
            self.stats["error_count"] += 1
            logger.error(f"FAISS backend search failed: {str(e)}")
            raise RuntimeError(f"FAISS backend search failed: {str(e)}") from e
    
    def get_document_count(self) -> int:
        """
        Get the number of documents in the index.
        
        Returns:
            Number of indexed documents
        """
        try:
            return self.faiss_index.get_document_count()
        except Exception as e:
            logger.error(f"Failed to get document count: {str(e)}")
            return 0
    
    def is_trained(self) -> bool:
        """
        Check if the index is trained and ready for use.
        
        Returns:
            True if index is trained, False otherwise
        """
        try:
            return self.faiss_index.is_trained()
        except Exception as e:
            logger.error(f"Failed to check training status: {str(e)}")
            return False
    
    def clear(self) -> None:
        """Clear all documents from the index."""
        start_time = time.time()
        
        try:
            self.faiss_index.clear()
            
            # Reset relevant stats
            elapsed_time = time.time() - start_time
            self._update_stats("clear", elapsed_time)
            
            logger.info("FAISS backend cleared")
            
        except Exception as e:
            self.stats["error_count"] += 1
            logger.error(f"Failed to clear FAISS backend: {str(e)}")
            raise RuntimeError(f"FAISS backend clear failed: {str(e)}") from e
    
    def get_backend_info(self) -> Dict[str, Any]:
        """
        Get information about the backend.
        
        Returns:
            Dictionary with backend information
        """
        faiss_info = self.faiss_index.get_index_info()
        
        return {
            "backend_type": self.backend_type,
            "backend_version": self.backend_version,
            "document_count": self.get_document_count(),
            "is_trained": self.is_trained(),
            "faiss_info": faiss_info,
            "stats": self.stats.copy(),
            "config": self.config
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get detailed performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        return {
            "backend_type": "faiss",
            "total_operations": self.stats["total_operations"],
            "total_time": self.stats["total_time"],
            "avg_time": self.stats["avg_time"],
            "last_operation_time": self.stats["last_operation_time"],
            "search_count": self.stats["search_count"],
            "add_count": self.stats["add_count"],
            "error_count": self.stats["error_count"],
            "error_rate": self.stats["error_count"] / max(1, self.stats["total_operations"]),
            "document_count": self.get_document_count(),
            "is_ready": self.is_trained()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the backend.
        
        Returns:
            Dictionary with health status
        """
        try:
            is_healthy = True
            issues = []
            
            # Check if index is initialized
            if not self.is_trained():
                is_healthy = False
                issues.append("Index not trained")
            
            # Check error rate
            error_rate = self.stats["error_count"] / max(1, self.stats["total_operations"])
            if error_rate > 0.1:  # More than 10% errors
                is_healthy = False
                issues.append(f"High error rate: {error_rate:.2%}")
            
            # Check if we have documents
            doc_count = self.get_document_count()
            if doc_count == 0:
                issues.append("No documents indexed")
            
            return {
                "backend_type": "faiss",
                "is_healthy": is_healthy,
                "issues": issues,
                "document_count": doc_count,
                "error_rate": error_rate,
                "total_operations": self.stats["total_operations"]
            }
            
        except Exception as e:
            return {
                "backend_type": "faiss",
                "is_healthy": False,
                "issues": [f"Health check failed: {str(e)}"],
                "error": str(e)
            }
    
    def _update_stats(self, operation: str, elapsed_time: float) -> None:
        """
        Update performance statistics.
        
        Args:
            operation: Name of the operation
            elapsed_time: Time taken for the operation
        """
        self.stats["total_operations"] += 1
        self.stats["total_time"] += elapsed_time
        self.stats["avg_time"] = self.stats["total_time"] / self.stats["total_operations"]
        self.stats["last_operation_time"] = elapsed_time
    
    def supports_hybrid_search(self) -> bool:
        """
        Check if backend supports hybrid search.
        
        Returns:
            False for FAISS (pure vector search only)
        """
        return False
    
    def supports_filtering(self) -> bool:
        """
        Check if backend supports metadata filtering.
        
        Returns:
            False for FAISS (no built-in filtering)
        """
        return False
    
    def get_configuration(self) -> Dict[str, Any]:
        """
        Get the current configuration.
        
        Returns:
            Configuration dictionary
        """
        return {
            "backend_type": "faiss",
            "config": self.config,
            "faiss_config": self.faiss_config
        }