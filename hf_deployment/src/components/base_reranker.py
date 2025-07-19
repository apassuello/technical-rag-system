"""
Base interface for Reranker components in the HF deployment.

Self-contained implementation without external dependencies.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple

# Use unified Document from core interfaces
from ..core.interfaces import Document


class Reranker(ABC):
    """
    Abstract base class for reranker implementations.
    
    This interface defines the contract for all reranker sub-components
    for neural reranking capabilities in the HF deployment system.
    """
    
    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the reranker.
        
        Args:
            config: Configuration dictionary specific to the reranker type
        """
        pass
    
    @abstractmethod
    def rerank(
        self, 
        query: str, 
        documents: List[Document], 
        initial_scores: List[float]
    ) -> List[Tuple[int, float]]:
        """
        Rerank documents based on query relevance.
        
        Args:
            query: The search query
            documents: List of candidate documents
            initial_scores: Initial relevance scores from fusion
            
        Returns:
            List of (document_index, reranked_score) tuples sorted by score
        """
        pass
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """
        Check if reranking is enabled.
        
        Returns:
            True if reranking should be performed
        """
        pass
    
    @abstractmethod
    def get_reranker_info(self) -> Dict[str, Any]:
        """
        Get information about the reranker.
        
        Returns:
            Dictionary with reranker configuration and statistics
        """
        pass
    
    def get_component_info(self) -> Dict[str, Any]:
        """
        Get component information for logging and debugging.
        
        Returns:
            Dictionary with component details
        """
        return {
            "type": "reranker",
            "class": self.__class__.__name__,
            "module": self.__class__.__module__,
            "enabled": self.is_enabled(),
            **self.get_reranker_info()
        }