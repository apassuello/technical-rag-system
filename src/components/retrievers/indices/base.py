"""
Base interface for Vector Index sub-components.

This module defines the abstract base class for all vector index implementations
in the modular retriever architecture.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from src.core.interfaces import Document


class VectorIndex(ABC):
    """
    Abstract base class for vector index implementations.
    
    This interface defines the contract for all vector index sub-components
    in the modular retriever architecture. Implementations can be either
    direct (FAISS) or adapters for cloud services (Pinecone, Weaviate).
    """
    
    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the vector index.
        
        Args:
            config: Configuration dictionary specific to the index type
        """
        pass
    
    @abstractmethod
    def initialize_index(self, embedding_dim: int) -> None:
        """
        Initialize the index with the specified embedding dimension.
        
        Args:
            embedding_dim: Dimension of the embeddings to be indexed
        """
        pass
    
    @abstractmethod
    def add_documents(self, documents: List[Document]) -> None:
        """
        Add documents to the index.
        
        Args:
            documents: List of documents with embeddings to add
            
        Raises:
            ValueError: If documents don't have embeddings or wrong dimension
        """
        pass
    
    @abstractmethod
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[int, float]]:
        """
        Search for similar documents using vector similarity.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of (document_index, similarity_score) tuples
        """
        pass
    
    @abstractmethod
    def get_document_count(self) -> int:
        """
        Get the number of documents in the index.
        
        Returns:
            Number of indexed documents
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all documents from the index."""
        pass
    
    @abstractmethod
    def get_index_info(self) -> Dict[str, Any]:
        """
        Get information about the index.
        
        Returns:
            Dictionary with index statistics and configuration
        """
        pass
    
    @abstractmethod
    def is_trained(self) -> bool:
        """
        Check if the index is trained (relevant for some index types).
        
        Returns:
            True if the index is ready for searching
        """
        pass
    
    def get_component_info(self) -> Dict[str, Any]:
        """
        Get component information for logging and debugging.
        
        Returns:
            Dictionary with component details
        """
        return {
            "type": "vector_index",
            "class": self.__class__.__name__,
            "module": self.__class__.__module__,
            "document_count": self.get_document_count(),
            "is_trained": self.is_trained(),
            **self.get_index_info()
        }