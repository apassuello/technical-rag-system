"""
Identity Reranker implementation for Modular Retriever Architecture.

This module provides a no-op reranker that returns results unchanged,
useful for disabling reranking while maintaining the same interface.
"""

import logging
from typing import List, Dict, Any, Tuple

from src.core.interfaces import Document
from .base import Reranker

logger = logging.getLogger(__name__)


class IdentityReranker(Reranker):
    """
    Identity reranker that returns results unchanged.
    
    This is a no-op implementation that passes through the original
    ranking without modification. Useful for:
    - Disabling reranking while maintaining interface compatibility
    - Testing and baseline comparisons
    - Performance benchmarking
    - Fallback when reranking models are unavailable
    
    Features:
    - Zero computational overhead
    - Preserves original ranking order
    - Maintains same interface as other rerankers
    - Can be enabled/disabled for consistency
    
    Example:
        config = {
            "enabled": True  # Even when enabled, does nothing
        }
        reranker = IdentityReranker(config)
        results = reranker.rerank(query, documents, initial_scores)
        # results will be identical to input order
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize identity reranker.
        
        Args:
            config: Configuration dictionary with:
                - enabled: Whether reranking is enabled (default: True)
                  Note: Even when enabled, this reranker does nothing
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        
        logger.info(f"IdentityReranker initialized with enabled={self.enabled}")
    
    def rerank(
        self, 
        query: str, 
        documents: List[Document], 
        initial_scores: List[float]
    ) -> List[Tuple[int, float]]:
        """
        Return documents in original order without reranking.
        
        Args:
            query: The search query (unused)
            documents: List of candidate documents (unused)
            initial_scores: Initial relevance scores from fusion
            
        Returns:
            List of (document_index, score) tuples in original order
        """
        if not self.enabled:
            return []
        
        # Return original ranking unchanged
        return [(i, score) for i, score in enumerate(initial_scores)]
    
    def is_enabled(self) -> bool:
        """
        Check if reranking is enabled.
        
        Returns:
            True if reranking should be performed
        """
        return self.enabled
    
    def get_reranker_info(self) -> Dict[str, Any]:
        """
        Get information about the reranker.
        
        Returns:
            Dictionary with reranker configuration and statistics
        """
        return {
            "type": "identity",
            "enabled": self.enabled,
            "description": "No-op reranker that preserves original ranking",
            "computational_overhead": 0.0,
            "modifies_ranking": False
        }
    
    def enable(self) -> None:
        """Enable reranking (no-op for identity reranker)."""
        self.enabled = True
        logger.info("Identity reranker enabled (no-op)")
    
    def disable(self) -> None:
        """Disable reranking."""
        self.enabled = False
        logger.info("Identity reranker disabled")
    
    def get_performance_info(self) -> Dict[str, Any]:
        """
        Get performance information about the reranker.
        
        Returns:
            Dictionary with performance characteristics
        """
        return {
            "average_latency_ms": 0.0,
            "memory_usage_mb": 0.0,
            "cpu_usage_percent": 0.0,
            "gpu_usage_percent": 0.0,
            "throughput_docs_per_second": float('inf'),
            "description": "Identity reranker has zero computational overhead"
        }