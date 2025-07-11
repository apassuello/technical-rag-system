"""
Base interface for Fusion Strategy sub-components.

This module defines the abstract base class for all fusion strategy implementations
in the modular retriever architecture.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple


class FusionStrategy(ABC):
    """
    Abstract base class for fusion strategy implementations.
    
    This interface defines the contract for all fusion strategy sub-components
    in the modular retriever architecture. All implementations are direct
    as they implement pure algorithms without external dependencies.
    """
    
    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the fusion strategy.
        
        Args:
            config: Configuration dictionary specific to the fusion strategy
        """
        pass
    
    @abstractmethod
    def fuse_results(
        self, 
        dense_results: List[Tuple[int, float]], 
        sparse_results: List[Tuple[int, float]]
    ) -> List[Tuple[int, float]]:
        """
        Fuse dense and sparse retrieval results.
        
        Args:
            dense_results: List of (document_index, score) from dense retrieval
            sparse_results: List of (document_index, score) from sparse retrieval
            
        Returns:
            List of (document_index, fused_score) tuples sorted by score
        """
        pass
    
    @abstractmethod
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get information about the fusion strategy.
        
        Returns:
            Dictionary with strategy configuration and statistics
        """
        pass
    
    def get_component_info(self) -> Dict[str, Any]:
        """
        Get component information for logging and debugging.
        
        Returns:
            Dictionary with component details
        """
        return {
            "type": "fusion_strategy",
            "class": self.__class__.__name__,
            "module": self.__class__.__module__,
            **self.get_strategy_info()
        }