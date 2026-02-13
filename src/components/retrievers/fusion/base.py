"""
Base interface for Fusion Strategy sub-components.

This module defines the abstract base class for all fusion strategy implementations
in the modular retriever architecture.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple


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

    def fuse(
        self,
        dense_results: List[Any],
        sparse_results: List[Any]
    ) -> List[Any]:
        """
        Fuse dense and sparse retrieval results (supports both tuples and RetrievalResult objects).

        This method exists for API compatibility with tests and handles both tuple format
        and RetrievalResult object format.

        Args:
            dense_results: List of (document_index, score) tuples OR RetrievalResult objects
            sparse_results: List of (document_index, score) tuples OR RetrievalResult objects

        Returns:
            List in the same format as inputs (tuples or RetrievalResult objects)
        """
        # Import here to avoid circular dependency
        from src.core.interfaces import RetrievalResult

        # Check if inputs are RetrievalResult objects
        uses_retrieval_results = False
        document_map = {}
        doc_id_map = {}  # Map document content to unique index

        if dense_results and hasattr(dense_results[0], 'document'):
            uses_retrieval_results = True
            # Convert RetrievalResult to tuples for fusion
            dense_tuples = []
            for result in dense_results:
                # Use document content or ID as unique identifier
                doc_id = id(result.document) if result.document else None
                if doc_id not in doc_id_map:
                    doc_id_map[doc_id] = len(doc_id_map)
                    document_map[doc_id_map[doc_id]] = result.document
                idx = doc_id_map[doc_id]
                dense_tuples.append((idx, result.score))
        else:
            dense_tuples = dense_results

        if sparse_results and hasattr(sparse_results[0], 'document'):
            uses_retrieval_results = True
            # Convert RetrievalResult to tuples for fusion
            sparse_tuples = []
            for result in sparse_results:
                # Use document content or ID as unique identifier
                doc_id = id(result.document) if result.document else None
                if doc_id not in doc_id_map:
                    doc_id_map[doc_id] = len(doc_id_map)
                    document_map[doc_id_map[doc_id]] = result.document
                idx = doc_id_map[doc_id]
                sparse_tuples.append((idx, result.score))
        else:
            sparse_tuples = sparse_results

        # Perform fusion on tuples
        fused_tuples = self.fuse_results(dense_tuples, sparse_tuples)

        # Convert back to RetrievalResult if needed
        if uses_retrieval_results:
            fused_results = []
            for doc_idx, score in fused_tuples:
                if doc_idx in document_map:
                    fused_results.append(
                        RetrievalResult(
                            document=document_map[doc_idx],
                            score=score,
                            retrieval_method="fusion"
                        )
                    )
            return fused_results
        else:
            return fused_tuples

    def get_capabilities(self) -> List[str]:
        """
        Get list of capabilities this fusion strategy provides.

        Returns:
            List of capability strings
        """
        return [
            "result_fusion",
            "score_combination",
            "rank_aggregation"
        ]