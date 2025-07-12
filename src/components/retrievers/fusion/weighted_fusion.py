"""
Weighted Fusion implementation for Modular Retriever Architecture.

This module provides a direct implementation of score-based weighted fusion
as an alternative to RRF for improved modularity and flexibility.
"""

import logging
from typing import List, Dict, Any, Tuple

from .base import FusionStrategy

logger = logging.getLogger(__name__)


class WeightedFusion(FusionStrategy):
    """
    Weighted score fusion implementation.
    
    This is a direct implementation of score-based fusion that combines
    dense and sparse retrieval results using direct score weighting.
    No external dependencies are required.
    
    Score Formula: final_score = dense_weight * dense_score + sparse_weight * sparse_score
    
    Features:
    - Direct score weighting (not rank-based)
    - Optional score normalization
    - Configurable weights for dense and sparse retrieval
    - Handles empty result sets gracefully
    - Preserves original score information
    
    Example:
        config = {
            "weights": {
                "dense": 0.7,
                "sparse": 0.3
            },
            "normalize": True
        }
        fusion = WeightedFusion(config)
        results = fusion.fuse_results(dense_results, sparse_results)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize weighted fusion strategy.
        
        Args:
            config: Configuration dictionary with:
                - weights: Dictionary with dense and sparse weights
                  - dense: Weight for dense retrieval (default: 0.7)
                  - sparse: Weight for sparse retrieval (default: 0.3)
                - normalize: Whether to normalize scores to [0,1] range (default: True)
        """
        self.config = config
        
        # Extract weights
        weights = config.get("weights", {})
        self.dense_weight = weights.get("dense", 0.7)
        self.sparse_weight = weights.get("sparse", 0.3)
        self.normalize = config.get("normalize", True)
        
        # Validation
        if not 0 <= self.dense_weight <= 1:
            raise ValueError("dense_weight must be between 0 and 1")
        if not 0 <= self.sparse_weight <= 1:
            raise ValueError("sparse_weight must be between 0 and 1")
        
        # Normalize weights if they don't sum to 1
        weight_sum = self.dense_weight + self.sparse_weight
        if weight_sum > 0:
            self.dense_weight /= weight_sum
            self.sparse_weight /= weight_sum
        else:
            self.dense_weight = 0.7
            self.sparse_weight = 0.3
        
        logger.info(f"WeightedFusion initialized with dense_weight={self.dense_weight:.3f}, normalize={self.normalize}")
    
    def fuse_results(
        self, 
        dense_results: List[Tuple[int, float]], 
        sparse_results: List[Tuple[int, float]]
    ) -> List[Tuple[int, float]]:
        """
        Fuse dense and sparse retrieval results using weighted scoring.
        
        Args:
            dense_results: List of (document_index, score) from dense retrieval
            sparse_results: List of (document_index, score) from sparse retrieval
            
        Returns:
            List of (document_index, fused_score) tuples sorted by score
        """
        # Handle empty results
        if not dense_results and not sparse_results:
            return []
        if not dense_results:
            return sparse_results[:] if sparse_results else []
        if not sparse_results:
            return dense_results[:] if dense_results else []
        
        # Normalize scores if requested
        normalized_dense = self._normalize_scores(dense_results) if self.normalize else dense_results
        normalized_sparse = self._normalize_scores(sparse_results) if self.normalize else sparse_results
        
        # Convert to dictionaries for efficient lookup
        dense_scores = dict(normalized_dense)
        sparse_scores = dict(normalized_sparse)
        
        # Get all unique document IDs
        all_docs = set(dense_scores.keys()) | set(sparse_scores.keys())
        
        # Calculate weighted scores
        weighted_results = []
        for doc_id in all_docs:
            dense_score = dense_scores.get(doc_id, 0.0)
            sparse_score = sparse_scores.get(doc_id, 0.0)
            
            final_score = self.dense_weight * dense_score + self.sparse_weight * sparse_score
            weighted_results.append((doc_id, final_score))
        
        # Sort by final score (descending)
        weighted_results.sort(key=lambda x: x[1], reverse=True)
        
        return weighted_results
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get information about the weighted fusion strategy.
        
        Returns:
            Dictionary with strategy configuration and statistics
        """
        return {
            "algorithm": "weighted_score_fusion",
            "dense_weight": self.dense_weight,
            "sparse_weight": self.sparse_weight,
            "normalize": self.normalize,
            "parameters": {
                "weights": {
                    "dense": self.dense_weight,
                    "sparse": self.sparse_weight
                },
                "normalize": self.normalize
            }
        }
    
    def _normalize_scores(self, results: List[Tuple[int, float]]) -> List[Tuple[int, float]]:
        """
        Normalize scores to [0,1] range.
        
        Args:
            results: List of (document_index, score) tuples
            
        Returns:
            List of (document_index, normalized_score) tuples
        """
        if not results:
            return []
        
        scores = [score for _, score in results]
        max_score = max(scores)
        min_score = min(scores)
        score_range = max_score - min_score
        
        if score_range == 0:
            # All scores are the same, return as-is
            return results
        
        # Normalize to [0,1] range
        normalized_results = [
            (doc_id, (score - min_score) / score_range)
            for doc_id, score in results
        ]
        
        return normalized_results
    
    def update_weights(self, dense_weight: float, sparse_weight: float) -> None:
        """
        Update fusion weights dynamically.
        
        Args:
            dense_weight: New weight for dense retrieval
            sparse_weight: New weight for sparse retrieval
        """
        if not 0 <= dense_weight <= 1:
            raise ValueError("dense_weight must be between 0 and 1")
        if not 0 <= sparse_weight <= 1:
            raise ValueError("sparse_weight must be between 0 and 1")
        
        # Normalize weights
        weight_sum = dense_weight + sparse_weight
        if weight_sum > 0:
            self.dense_weight = dense_weight / weight_sum
            self.sparse_weight = sparse_weight / weight_sum
        else:
            raise ValueError("At least one weight must be positive")
        
        logger.info(f"Updated weighted fusion weights: dense={self.dense_weight:.3f}, sparse={self.sparse_weight:.3f}")
    
    def set_normalize(self, normalize: bool) -> None:
        """
        Update the normalization setting.
        
        Args:
            normalize: Whether to normalize scores
        """
        self.normalize = normalize
        logger.info(f"Updated normalization setting to {normalize}")
    
    def calculate_individual_scores(
        self, 
        dense_results: List[Tuple[int, float]], 
        sparse_results: List[Tuple[int, float]]
    ) -> Dict[int, Dict[str, float]]:
        """
        Calculate individual weighted scores for debugging purposes.
        
        Args:
            dense_results: List of (document_index, score) from dense retrieval
            sparse_results: List of (document_index, score) from sparse retrieval
            
        Returns:
            Dictionary mapping document_index to individual score components
        """
        # Normalize scores if requested
        normalized_dense = self._normalize_scores(dense_results) if self.normalize else dense_results
        normalized_sparse = self._normalize_scores(sparse_results) if self.normalize else sparse_results
        
        dense_scores = dict(normalized_dense)
        sparse_scores = dict(normalized_sparse)
        all_docs = set(dense_scores.keys()) | set(sparse_scores.keys())
        
        scores = {}
        for doc_id in all_docs:
            dense_score = dense_scores.get(doc_id, 0.0)
            sparse_score = sparse_scores.get(doc_id, 0.0)
            
            weighted_dense = self.dense_weight * dense_score
            weighted_sparse = self.sparse_weight * sparse_score
            
            scores[doc_id] = {
                "dense": dense_score,
                "sparse": sparse_score,
                "weighted_dense": weighted_dense,
                "weighted_sparse": weighted_sparse,
                "total": weighted_dense + weighted_sparse
            }
        
        return scores
    
    def get_score_statistics(
        self, 
        dense_results: List[Tuple[int, float]], 
        sparse_results: List[Tuple[int, float]]
    ) -> Dict[str, Any]:
        """
        Get score statistics for analysis.
        
        Args:
            dense_results: List of (document_index, score) from dense retrieval
            sparse_results: List of (document_index, score) from sparse retrieval
            
        Returns:
            Dictionary with score statistics
        """
        stats = {}
        
        if dense_results:
            dense_scores = [score for _, score in dense_results]
            stats["dense"] = {
                "min": min(dense_scores),
                "max": max(dense_scores),
                "mean": sum(dense_scores) / len(dense_scores),
                "count": len(dense_scores)
            }
        
        if sparse_results:
            sparse_scores = [score for _, score in sparse_results]
            stats["sparse"] = {
                "min": min(sparse_scores),
                "max": max(sparse_scores),
                "mean": sum(sparse_scores) / len(sparse_scores),
                "count": len(sparse_scores)
            }
        
        return stats