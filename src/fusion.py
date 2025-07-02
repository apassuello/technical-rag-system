"""
Reciprocal Rank Fusion for combining dense and sparse retrieval results.
Implements the RRF algorithm with configurable weighting.
"""

from typing import List, Tuple, Dict
from collections import defaultdict


def reciprocal_rank_fusion(
    dense_results: List[Tuple[int, float]],
    sparse_results: List[Tuple[int, float]],
    dense_weight: float = 0.7,
    k: int = 60,
) -> List[Tuple[int, float]]:
    """
    Combine dense and sparse retrieval using Reciprocal Rank Fusion.

    RRF Formula: score = Σ weight_i / (k + rank_i)
    Where rank_i is the 1-based rank of document in result list i

    Args:
        dense_results: [(chunk_idx, similarity_score), ...] sorted by relevance
        sparse_results: [(chunk_idx, bm25_score), ...] sorted by relevance  
        dense_weight: Weight for semantic similarity (default 0.7)
        k: RRF constant controlling rank influence (default 60)

    Returns:
        Fused results as [(chunk_idx, rrf_score), ...] sorted by combined score
        
    Raises:
        ValueError: If weights are invalid or results are malformed
        
    Performance: O(n + m) where n, m are result list lengths
    """
    if not 0 <= dense_weight <= 1:
        raise ValueError("dense_weight must be between 0 and 1")
        
    if k <= 0:
        raise ValueError("k must be positive")
        
    sparse_weight = 1.0 - dense_weight
    
    # Handle empty results
    if not dense_results and not sparse_results:
        return []
    if not dense_results:
        return sparse_results
    if not sparse_results:
        return dense_results
    
    # Calculate RRF scores for each unique document
    rrf_scores: Dict[int, float] = defaultdict(float)
    
    # Add dense retrieval scores (rank-based)
    for rank, (chunk_idx, _) in enumerate(dense_results, 1):
        rrf_scores[chunk_idx] += dense_weight / (k + rank)
    
    # Add sparse retrieval scores (rank-based)  
    for rank, (chunk_idx, _) in enumerate(sparse_results, 1):
        rrf_scores[chunk_idx] += sparse_weight / (k + rank)
    
    # Convert to sorted list
    fused_results = [
        (chunk_idx, score) for chunk_idx, score in rrf_scores.items()
    ]
    
    # Sort by RRF score (descending)
    fused_results.sort(key=lambda x: x[1], reverse=True)
    
    return fused_results


def weighted_score_fusion(
    dense_results: List[Tuple[int, float]],
    sparse_results: List[Tuple[int, float]], 
    dense_weight: float = 0.7,
) -> List[Tuple[int, float]]:
    """
    Alternative fusion using direct score weighting (not rank-based).
    
    Score Formula: final_score = dense_weight * dense_score + sparse_weight * sparse_score
    
    Args:
        dense_results: [(chunk_idx, similarity_score), ...]
        sparse_results: [(chunk_idx, bm25_score), ...]  
        dense_weight: Weight for semantic scores (default 0.7)
        
    Returns:
        Fused results sorted by weighted score
        
    Note: Requires normalized input scores for fair weighting
    """
    if not 0 <= dense_weight <= 1:
        raise ValueError("dense_weight must be between 0 and 1")
        
    sparse_weight = 1.0 - dense_weight
    
    # Convert to dictionaries for efficient lookup
    dense_scores = dict(dense_results)
    sparse_scores = dict(sparse_results)
    
    # Get all unique document IDs
    all_docs = set(dense_scores.keys()) | set(sparse_scores.keys())
    
    # Calculate weighted scores
    weighted_results = []
    for doc_id in all_docs:
        dense_score = dense_scores.get(doc_id, 0.0)
        sparse_score = sparse_scores.get(doc_id, 0.0)
        
        final_score = dense_weight * dense_score + sparse_weight * sparse_score
        weighted_results.append((doc_id, final_score))
    
    # Sort by final score (descending)
    weighted_results.sort(key=lambda x: x[1], reverse=True)
    
    return weighted_results