"""
Reciprocal Rank Fusion implementation for Modular Retriever Architecture.

This module provides a direct implementation of the RRF algorithm
extracted from the existing fusion system for improved modularity.
"""

import logging
from typing import List, Dict, Any, Tuple
from collections import defaultdict

from .base import FusionStrategy

logger = logging.getLogger(__name__)


class RRFFusion(FusionStrategy):
    """
    Reciprocal Rank Fusion (RRF) implementation.
    
    This is a direct implementation of the RRF algorithm that combines
    dense and sparse retrieval results using rank-based scoring.
    No external dependencies are required.
    
    RRF Formula: score = Σ weight_i / (k + rank_i)
    Where rank_i is the 1-based rank of document in result list i
    
    Features:
    - Configurable RRF constant (k) parameter
    - Weighted fusion with dense/sparse weights
    - Handles empty result sets gracefully
    - Preserves rank-based scoring benefits
    - Optimized for performance
    
    Example:
        config = {
            "k": 60,
            "weights": {
                "dense": 0.7,
                "sparse": 0.3
            }
        }
        fusion = RRFFusion(config)
        results = fusion.fuse_results(dense_results, sparse_results)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize RRF fusion strategy.
        
        Args:
            config: Configuration dictionary with:
                - k: RRF constant controlling rank influence (default: 60)
                - weights: Dictionary with dense and sparse weights
                  - dense: Weight for dense retrieval (default: 0.7)
                  - sparse: Weight for sparse retrieval (default: 0.3)
        """
        self.config = config
        self.k = config.get("k", 60)
        
        # Extract weights
        weights = config.get("weights", {})
        self.dense_weight = weights.get("dense", 0.7)
        self.sparse_weight = weights.get("sparse", 0.3)
        
        # Validation
        if self.k <= 0:
            raise ValueError("k must be positive")
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
        
        logger.info(f"RRFFusion initialized with k={self.k}, dense_weight={self.dense_weight:.3f}")
    
    def fuse_results(
        self, 
        dense_results: List[Tuple[int, float]], 
        sparse_results: List[Tuple[int, float]]
    ) -> List[Tuple[int, float]]:
        """
        Fuse dense and sparse retrieval results using RRF.
        
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
        
        # Calculate RRF scores for each unique document
        rrf_scores: Dict[int, float] = defaultdict(float)
        
        # Add dense retrieval scores (rank-based)
        for rank, (doc_idx, _) in enumerate(dense_results, 1):
            rrf_scores[doc_idx] += self.dense_weight / (self.k + rank)
        
        # Add sparse retrieval scores (rank-based)
        for rank, (doc_idx, _) in enumerate(sparse_results, 1):
            rrf_scores[doc_idx] += self.sparse_weight / (self.k + rank)
        
        # Convert to sorted list
        fused_results = [
            (doc_idx, score) for doc_idx, score in rrf_scores.items()
        ]
        
        # Sort by RRF score (descending)
        fused_results.sort(key=lambda x: x[1], reverse=True)
        
        return fused_results
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get information about the RRF fusion strategy.
        
        Returns:
            Dictionary with strategy configuration and statistics
        """
        return {
            "algorithm": "reciprocal_rank_fusion",
            "k": self.k,
            "dense_weight": self.dense_weight,
            "sparse_weight": self.sparse_weight,
            "parameters": {
                "k": self.k,
                "weights": {
                    "dense": self.dense_weight,
                    "sparse": self.sparse_weight
                }
            }
        }
    
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
        
        logger.info(f"Updated RRF weights: dense={self.dense_weight:.3f}, sparse={self.sparse_weight:.3f}")
    
    def calculate_individual_scores(
        self, 
        dense_results: List[Tuple[int, float]], 
        sparse_results: List[Tuple[int, float]]
    ) -> Dict[int, Dict[str, float]]:
        """
        Calculate individual RRF scores for debugging purposes.
        
        Args:
            dense_results: List of (document_index, score) from dense retrieval
            sparse_results: List of (document_index, score) from sparse retrieval
            
        Returns:
            Dictionary mapping document_index to individual score components
        """
        scores = defaultdict(lambda: {"dense": 0.0, "sparse": 0.0, "total": 0.0})
        
        # Calculate dense scores
        for rank, (doc_idx, _) in enumerate(dense_results, 1):
            dense_score = self.dense_weight / (self.k + rank)
            scores[doc_idx]["dense"] = dense_score
            scores[doc_idx]["total"] += dense_score
        
        # Calculate sparse scores
        for rank, (doc_idx, _) in enumerate(sparse_results, 1):
            sparse_score = self.sparse_weight / (self.k + rank)
            scores[doc_idx]["sparse"] = sparse_score
            scores[doc_idx]["total"] += sparse_score
        
        return dict(scores)
    
    def get_optimal_k(self, result_size: int) -> int:
        """
        Get optimal k value based on result size.
        
        Args:
            result_size: Expected final result size
            
        Returns:
            Optimal k value
        """
        # Adaptive k selection based on result size
        # Smaller k for larger result sets, larger k for smaller sets
        return max(5, min(60, result_size * 3))
    
    def set_k(self, k: int) -> None:
        """
        Update the RRF k parameter.
        
        Args:
            k: New RRF constant value
        """
        if k <= 0:
            raise ValueError("k must be positive")
        
        self.k = k
        logger.info(f"Updated RRF k parameter to {k}")
    
    def get_rank_contributions(
        self, 
        dense_results: List[Tuple[int, float]], 
        sparse_results: List[Tuple[int, float]]
    ) -> Dict[int, Dict[str, Any]]:
        """
        Get detailed rank contributions for analysis.
        
        Args:
            dense_results: List of (document_index, score) from dense retrieval
            sparse_results: List of (document_index, score) from sparse retrieval
            
        Returns:
            Dictionary with rank contributions for each document
        """
        contributions = defaultdict(lambda: {
            "dense_rank": None,
            "sparse_rank": None,
            "dense_contribution": 0.0,
            "sparse_contribution": 0.0
        })
        
        # Track dense ranks and contributions
        for rank, (doc_idx, _) in enumerate(dense_results, 1):
            contributions[doc_idx]["dense_rank"] = rank
            contributions[doc_idx]["dense_contribution"] = self.dense_weight / (self.k + rank)
        
        # Track sparse ranks and contributions
        for rank, (doc_idx, _) in enumerate(sparse_results, 1):
            contributions[doc_idx]["sparse_rank"] = rank
            contributions[doc_idx]["sparse_contribution"] = self.sparse_weight / (self.k + rank)
        
        return dict(contributions)