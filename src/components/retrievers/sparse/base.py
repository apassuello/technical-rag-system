"""
Base interface for Sparse Retriever sub-components.

This module defines the abstract base class for all sparse retrieval implementations
in the modular retriever architecture.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple

from src.core.interfaces import Document


class SparseRetriever(ABC):
    """
    Abstract base class for sparse retrieval implementations.
    
    This interface defines the contract for all sparse retriever sub-components
    in the modular retriever architecture. Implementations can be either
    direct (BM25) or adapters for external services (Elasticsearch).
    """
    
    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the sparse retriever.
        
        Args:
            config: Configuration dictionary specific to the retriever type
        """
        pass
    
    @abstractmethod
    def index_documents(self, documents: List[Document]) -> None:
        """
        Index documents for sparse retrieval.
        
        Args:
            documents: List of documents to index
        """
        pass
    
    @abstractmethod
    def search(self, query: str, k: int = 5) -> List[Tuple[int, float]]:
        """
        Search for documents using sparse retrieval.
        
        Args:
            query: Search query string
            k: Number of results to return
            
        Returns:
            List of (document_index, score) tuples
        """
        pass
    
    @abstractmethod
    def get_document_count(self) -> int:
        """
        Get the number of indexed documents.
        
        Returns:
            Number of indexed documents
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all indexed documents."""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the sparse retriever.
        
        Returns:
            Dictionary with retriever statistics
        """
        pass
    
    def get_component_info(self) -> Dict[str, Any]:
        """
        Get component information for logging and debugging.
        
        Returns:
            Dictionary with component details
        """
        return {
            "type": "sparse_retriever",
            "class": self.__class__.__name__,
            "module": self.__class__.__module__,
            "document_count": self.get_document_count(),
            **self.get_stats()
        }