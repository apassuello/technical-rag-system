"""
Score-Aware Fusion implementation for Modular Retriever Architecture.

This module provides a direct implementation of score-aware fusion that preserves
semantic relevance signals while maintaining hybrid retrieval benefits.
"""

import logging
from typing import List, Dict, Any, Tuple
from collections import defaultdict

from .base import FusionStrategy

logger = logging.getLogger(__name__)


class ScoreAwareFusion(FusionStrategy):
    """
    Score-aware fusion implementation that preserves semantic relevance.
    
    This is a direct implementation that combines dense and sparse retrieval results
    using a hybrid approach that preserves semantic scores while adding rank-based
    stability and overlap bonuses.
    
    Algorithm Formula:
    final_score = α * normalized_score + β * rank_boost + γ * overlap_bonus
    
    Where:
    - α (score_weight): Preserve semantic relevance from original scores
    - β (rank_weight): Add RRF-style rank stability 
    - γ (overlap_weight): Boost documents appearing in both retrievers
    
    Features:
    - Preserves semantic relevance signals from dense vector search
    - Adds rank-based stability to prevent score noise issues
    - Rewards documents found by both dense and sparse retrievers
    - Configurable balance between score, rank, and overlap factors
    - Score normalization for fair comparison across retrievers
    - Graceful handling of empty result sets
    
    Example:
        config = {
            "score_weight": 0.6,     # α - semantic score importance
            "rank_weight": 0.3,      # β - rank stability factor
            "overlap_weight": 0.1,   # γ - both-retriever bonus
            "normalize_scores": True,
            "k": 60                  # RRF constant for rank component
        }
        fusion = ScoreAwareFusion(config)
        results = fusion.fuse_results(dense_results, sparse_results)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize score-aware fusion strategy.
        
        Args:
            config: Configuration dictionary with:
                - score_weight: Weight for original scores (default: 0.6)
                - rank_weight: Weight for rank-based component (default: 0.3)
                - overlap_weight: Weight for overlap bonus (default: 0.1)
                - normalize_scores: Whether to normalize scores (default: True)
                - k: RRF constant for rank component (default: 60)
        """
        self.config = config
        
        # Extract weights with defaults
        self.score_weight = config.get("score_weight", 0.6)
        self.rank_weight = config.get("rank_weight", 0.3)
        self.overlap_weight = config.get("overlap_weight", 0.1)
        self.normalize_scores = config.get("normalize_scores", True)
        self.k = config.get("k", 60)
        
        # Validation
        if not 0 <= self.score_weight <= 1:
            raise ValueError("score_weight must be between 0 and 1")
        if not 0 <= self.rank_weight <= 1:
            raise ValueError("rank_weight must be between 0 and 1")
        if not 0 <= self.overlap_weight <= 1:
            raise ValueError("overlap_weight must be between 0 and 1")
        if self.k <= 0:
            raise ValueError("k must be positive")
        
        # Normalize weights to sum to 1
        weight_sum = self.score_weight + self.rank_weight + self.overlap_weight
        if weight_sum > 0:
            self.score_weight /= weight_sum
            self.rank_weight /= weight_sum
            self.overlap_weight /= weight_sum
        else:
            # Default weights if all are zero
            self.score_weight = 0.6
            self.rank_weight = 0.3
            self.overlap_weight = 0.1
        
        logger.info(f"ScoreAwareFusion initialized: score={self.score_weight:.3f}, "
                   f"rank={self.rank_weight:.3f}, overlap={self.overlap_weight:.3f}, k={self.k}")
    
    def fuse_results(
        self, 
        dense_results: List[Tuple[int, float]], 
        sparse_results: List[Tuple[int, float]]
    ) -> List[Tuple[int, float]]:
        """
        Fuse dense and sparse retrieval results using score-aware algorithm.
        
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
        normalized_dense = self._normalize_scores(dense_results) if self.normalize_scores else dense_results
        normalized_sparse = self._normalize_scores(sparse_results) if self.normalize_scores else sparse_results
        
        # Convert to dictionaries for efficient lookup
        dense_scores = dict(normalized_dense)
        sparse_scores = dict(normalized_sparse)
        
        # Create rank mappings (1-based indexing for RRF compatibility)
        dense_ranks = {doc_idx: rank for rank, (doc_idx, _) in enumerate(dense_results, 1)}
        sparse_ranks = {doc_idx: rank for rank, (doc_idx, _) in enumerate(sparse_results, 1)}
        
        # Get all unique document IDs
        all_docs = set(dense_scores.keys()) | set(sparse_scores.keys())
        
        # Calculate fused scores using hybrid algorithm
        fused_results = []
        for doc_id in all_docs:
            # Component 1: Normalized scores (semantic relevance)
            dense_score = dense_scores.get(doc_id, 0.0)
            sparse_score = sparse_scores.get(doc_id, 0.0)
            
            # Use max instead of average to prevent negative sparse scores from dragging down positive dense scores
            if doc_id in dense_scores and doc_id in sparse_scores:
                # Take the maximum of the two scores, but weight them appropriately
                if dense_score >= 0 and sparse_score >= 0:
                    avg_score = (dense_score + sparse_score) / 2.0  # Both positive: average
                elif dense_score >= 0 and sparse_score < 0:
                    avg_score = dense_score  # Dense positive, sparse negative: use dense
                elif dense_score < 0 and sparse_score >= 0:
                    avg_score = sparse_score  # Dense negative, sparse positive: use sparse
                else:
                    avg_score = max(dense_score, sparse_score)  # Both negative: use less negative
            else:
                avg_score = max(dense_score, sparse_score)
            
            # Component 2: Rank-based boost (stability)
            rank_boost = 0.0
            if doc_id in dense_ranks:
                rank_boost += 0.5 / (self.k + dense_ranks[doc_id])
            if doc_id in sparse_ranks:
                rank_boost += 0.5 / (self.k + sparse_ranks[doc_id])
            
            # Component 3: Overlap bonus (hybrid benefit)
            overlap_bonus = 1.0 if (doc_id in dense_scores and doc_id in sparse_scores) else 0.0
            
            # Combine components with weights
            final_score = (
                self.score_weight * avg_score +
                self.rank_weight * rank_boost +
                self.overlap_weight * overlap_bonus
            )
            
            fused_results.append((doc_id, final_score))
        
        # Sort by final score (descending)
        fused_results.sort(key=lambda x: x[1], reverse=True)
        
        return fused_results
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get information about the score-aware fusion strategy.
        
        Returns:
            Dictionary with strategy configuration and statistics
        """
        return {
            "algorithm": "score_aware_fusion",
            "score_weight": self.score_weight,
            "rank_weight": self.rank_weight,
            "overlap_weight": self.overlap_weight,
            "normalize_scores": self.normalize_scores,
            "k": self.k,
            "parameters": {
                "score_weight": self.score_weight,
                "rank_weight": self.rank_weight,
                "overlap_weight": self.overlap_weight,
                "normalize_scores": self.normalize_scores,
                "k": self.k
            }
        }
    
    def _normalize_scores(self, results: List[Tuple[int, float]]) -> List[Tuple[int, float]]:
        """
        Normalize scores to [0,1] range using min-max normalization.
        
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
    
    def update_weights(self, score_weight: float, rank_weight: float, overlap_weight: float) -> None:
        """
        Update fusion weights dynamically.
        
        Args:
            score_weight: New weight for score component
            rank_weight: New weight for rank component  
            overlap_weight: New weight for overlap component
        """
        if not 0 <= score_weight <= 1:
            raise ValueError("score_weight must be between 0 and 1")
        if not 0 <= rank_weight <= 1:
            raise ValueError("rank_weight must be between 0 and 1")
        if not 0 <= overlap_weight <= 1:
            raise ValueError("overlap_weight must be between 0 and 1")
        
        # Normalize weights
        weight_sum = score_weight + rank_weight + overlap_weight
        if weight_sum > 0:
            self.score_weight = score_weight / weight_sum
            self.rank_weight = rank_weight / weight_sum
            self.overlap_weight = overlap_weight / weight_sum
        else:
            raise ValueError("At least one weight must be positive")
        
        logger.info(f"Updated ScoreAware weights: score={self.score_weight:.3f}, "
                   f"rank={self.rank_weight:.3f}, overlap={self.overlap_weight:.3f}")
    
    def set_k(self, k: int) -> None:
        """
        Update the RRF k parameter for rank component.
        
        Args:
            k: New RRF constant value
        """
        if k <= 0:
            raise ValueError("k must be positive")
        
        self.k = k
        logger.info(f"Updated ScoreAware k parameter to {k}")
    
    def calculate_individual_scores(
        self, 
        dense_results: List[Tuple[int, float]], 
        sparse_results: List[Tuple[int, float]]
    ) -> Dict[int, Dict[str, float]]:
        """
        Calculate individual score components for debugging purposes.
        
        Args:
            dense_results: List of (document_index, score) from dense retrieval
            sparse_results: List of (document_index, score) from sparse retrieval
            
        Returns:
            Dictionary mapping document_index to individual score components
        """
        # Normalize scores if requested
        normalized_dense = self._normalize_scores(dense_results) if self.normalize_scores else dense_results
        normalized_sparse = self._normalize_scores(sparse_results) if self.normalize_scores else sparse_results
        
        dense_scores = dict(normalized_dense)
        sparse_scores = dict(normalized_sparse)
        
        # Create rank mappings
        dense_ranks = {doc_idx: rank for rank, (doc_idx, _) in enumerate(dense_results, 1)}
        sparse_ranks = {doc_idx: rank for rank, (doc_idx, _) in enumerate(sparse_results, 1)}
        
        all_docs = set(dense_scores.keys()) | set(sparse_scores.keys())
        
        scores = {}
        for doc_id in all_docs:
            dense_score = dense_scores.get(doc_id, 0.0)
            sparse_score = sparse_scores.get(doc_id, 0.0)
            avg_score = (dense_score + sparse_score) / 2.0 if doc_id in dense_scores and doc_id in sparse_scores else max(dense_score, sparse_score)
            
            # Rank boost calculation
            rank_boost = 0.0
            if doc_id in dense_ranks:
                rank_boost += 0.5 / (self.k + dense_ranks[doc_id])
            if doc_id in sparse_ranks:
                rank_boost += 0.5 / (self.k + sparse_ranks[doc_id])
            
            # Overlap bonus
            overlap_bonus = 1.0 if (doc_id in dense_scores and doc_id in sparse_scores) else 0.0
            
            # Final score
            final_score = (
                self.score_weight * avg_score +
                self.rank_weight * rank_boost +
                self.overlap_weight * overlap_bonus
            )
            
            scores[doc_id] = {
                "dense_score": dense_score,
                "sparse_score": sparse_score,
                "avg_score": avg_score,
                "weighted_score": self.score_weight * avg_score,
                "rank_boost": rank_boost,
                "weighted_rank": self.rank_weight * rank_boost,
                "overlap_bonus": overlap_bonus,
                "weighted_overlap": self.overlap_weight * overlap_bonus,
                "final_score": final_score,
                "dense_rank": dense_ranks.get(doc_id),
                "sparse_rank": sparse_ranks.get(doc_id)
            }
        
        return scores
    
    def get_score_statistics(
        self, 
        dense_results: List[Tuple[int, float]], 
        sparse_results: List[Tuple[int, float]]
    ) -> Dict[str, Any]:
        """
        Get comprehensive score statistics for analysis.
        
        Args:
            dense_results: List of (document_index, score) from dense retrieval
            sparse_results: List of (document_index, score) from sparse retrieval
            
        Returns:
            Dictionary with detailed score statistics
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
        
        # Calculate overlap statistics
        if dense_results and sparse_results:
            dense_docs = {doc_id for doc_id, _ in dense_results}
            sparse_docs = {doc_id for doc_id, _ in sparse_results}
            overlap_docs = dense_docs & sparse_docs
            
            stats["overlap"] = {
                "count": len(overlap_docs),
                "dense_total": len(dense_docs),
                "sparse_total": len(sparse_docs),
                "overlap_ratio": len(overlap_docs) / max(len(dense_docs), len(sparse_docs))
            }
        
        return stats