"""
Score Fusion for Neural Reranking.

This module provides advanced score fusion capabilities for combining
neural reranking scores with retrieval scores using various strategies
including weighted fusion, learned combination, and adaptive methods.
"""

import logging
import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod

from src.core.interfaces import Document
from .config.reranking_config import ScoreFusionConfig, WeightsConfig, NormalizationConfig

logger = logging.getLogger(__name__)


class ScoreNormalizer:
    """Handles score normalization using various methods."""
    
    def __init__(self, config: NormalizationConfig):
        """
        Initialize score normalizer.
        
        Args:
            config: Normalization configuration
        """
        self.config = config
        self.stats = {
            "normalizations": 0,
            "outliers_clipped": 0
        }
    
    def normalize(self, scores: List[float]) -> List[float]:
        """
        Normalize scores using configured method.
        
        Args:
            scores: Raw scores to normalize
            
        Returns:
            Normalized scores
        """
        if not scores:
            return scores
        
        scores_array = np.array(scores)
        
        # Clip outliers if enabled
        if self.config.clip_outliers:
            scores_array = self._clip_outliers(scores_array)
        
        # Apply normalization method
        if self.config.method == "min_max":
            normalized = self._min_max_normalize(scores_array)
        elif self.config.method == "z_score":
            normalized = self._z_score_normalize(scores_array)
        elif self.config.method == "softmax":
            normalized = self._softmax_normalize(scores_array)
        elif self.config.method == "sigmoid":
            normalized = self._sigmoid_normalize(scores_array)
        else:
            logger.warning(f"Unknown normalization method: {self.config.method}")
            normalized = scores_array
        
        self.stats["normalizations"] += 1
        return normalized.tolist()
    
    def _clip_outliers(self, scores: np.ndarray) -> np.ndarray:
        """Clip outliers based on z-score threshold."""
        if len(scores) < 2:
            return scores
        
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        
        if std_score == 0:
            return scores
        
        z_scores = np.abs((scores - mean_score) / std_score)
        outlier_mask = z_scores > self.config.outlier_threshold
        
        if np.any(outlier_mask):
            # Clip outliers to threshold values
            upper_bound = mean_score + self.config.outlier_threshold * std_score
            lower_bound = mean_score - self.config.outlier_threshold * std_score
            
            scores = np.clip(scores, lower_bound, upper_bound)
            self.stats["outliers_clipped"] += np.sum(outlier_mask)
        
        return scores
    
    def _min_max_normalize(self, scores: np.ndarray) -> np.ndarray:
        """Min-max normalization to [0, 1] range."""
        min_score = np.min(scores)
        max_score = np.max(scores)
        
        if max_score == min_score:
            return np.ones_like(scores) * 0.5
        
        return (scores - min_score) / (max_score - min_score)
    
    def _z_score_normalize(self, scores: np.ndarray) -> np.ndarray:
        """Z-score normalization (mean=0, std=1)."""
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        
        if std_score == 0:
            return np.zeros_like(scores)
        
        return (scores - mean_score) / std_score
    
    def _softmax_normalize(self, scores: np.ndarray) -> np.ndarray:
        """Softmax normalization."""
        exp_scores = np.exp(scores - np.max(scores))  # Subtract max for numerical stability
        return exp_scores / np.sum(exp_scores)
    
    def _sigmoid_normalize(self, scores: np.ndarray) -> np.ndarray:
        """Sigmoid normalization to [0, 1] range."""
        return 1 / (1 + np.exp(-scores))


class BaseFusionStrategy(ABC):
    """Abstract base class for score fusion strategies."""
    
    @abstractmethod
    def fuse(
        self,
        retrieval_scores: List[float],
        neural_scores: List[float],
        query: str,
        documents: List[Document]
    ) -> List[float]:
        """
        Fuse retrieval and neural scores.
        
        Args:
            retrieval_scores: Original retrieval scores
            neural_scores: Neural reranking scores
            query: The search query
            documents: List of documents
            
        Returns:
            Fused scores
        """
        pass


class WeightedFusion(BaseFusionStrategy):
    """Weighted fusion of retrieval and neural scores."""
    
    def __init__(self, weights: WeightsConfig):
        """
        Initialize weighted fusion.
        
        Args:
            weights: Weight configuration
        """
        self.weights = weights
        self.stats = {"fusions": 0}
    
    def fuse(
        self,
        retrieval_scores: List[float],
        neural_scores: List[float],
        query: str,
        documents: List[Document]
    ) -> List[float]:
        """Fuse scores using weighted combination."""
        if len(retrieval_scores) != len(neural_scores):
            logger.warning("Score length mismatch in weighted fusion")
            return retrieval_scores
        
        fused_scores = []
        for ret_score, neural_score in zip(retrieval_scores, neural_scores):
            # Basic weighted combination
            fused_score = (
                self.weights.retrieval_score * ret_score +
                self.weights.neural_score * neural_score
                # Future: add graph_score and temporal_score
            )
            fused_scores.append(fused_score)
        
        self.stats["fusions"] += 1
        return fused_scores
    
    def get_stats(self) -> Dict[str, Any]:
        """Get fusion statistics."""
        return self.stats.copy()


class LearnedFusion(BaseFusionStrategy):
    """Learned fusion using a simple neural network."""
    
    def __init__(self, config):
        """
        Initialize learned fusion.
        
        Args:
            config: Learned fusion configuration
        """
        self.config = config
        self.model = None
        self.stats = {"fusions": 0, "model_predictions": 0}
        
        if config.enabled and config.model_path:
            self._load_model()
    
    def _load_model(self):
        """Load the learned fusion model."""
        try:
            # This would load a pre-trained fusion model
            # For now, we'll use a placeholder
            logger.info("Learned fusion model loading not implemented")
            self.model = None
        except Exception as e:
            logger.error(f"Failed to load learned fusion model: {e}")
            self.model = None
    
    def fuse(
        self,
        retrieval_scores: List[float],
        neural_scores: List[float],
        query: str,
        documents: List[Document]
    ) -> List[float]:
        """Fuse scores using learned model."""
        if self.model is None:
            # Fallback to simple weighted fusion
            fused_scores = []
            for ret_score, neural_score in zip(retrieval_scores, neural_scores):
                fused_score = 0.3 * ret_score + 0.7 * neural_score
                fused_scores.append(fused_score)
            return fused_scores
        
        # Use learned model for fusion
        features = self._extract_features(retrieval_scores, neural_scores, query, documents)
        fused_scores = self.model.predict(features)
        
        self.stats["fusions"] += 1
        self.stats["model_predictions"] += len(fused_scores)
        
        return fused_scores.tolist()
    
    def _extract_features(
        self,
        retrieval_scores: List[float],
        neural_scores: List[float],
        query: str,
        documents: List[Document]
    ) -> np.ndarray:
        """Extract features for learned fusion."""
        features = []
        
        for ret_score, neural_score, doc in zip(retrieval_scores, neural_scores, documents):
            # Basic features: retrieval score, neural score, score difference, score ratio
            doc_features = [
                ret_score,
                neural_score,
                abs(ret_score - neural_score),
                neural_score / (ret_score + 1e-8)  # Avoid division by zero
            ]
            features.append(doc_features)
        
        return np.array(features)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get fusion statistics."""
        return self.stats.copy()


class AdaptiveFusion(BaseFusionStrategy):
    """Adaptive fusion that adjusts weights based on query and context."""
    
    def __init__(self, config):
        """
        Initialize adaptive fusion.
        
        Args:
            config: Adaptive fusion configuration
        """
        self.config = config
        self.stats = {"fusions": 0, "adaptations": 0}
        self.query_history = []
    
    def fuse(
        self,
        retrieval_scores: List[float],
        neural_scores: List[float],
        query: str,
        documents: List[Document]
    ) -> List[float]:
        """Fuse scores using adaptive weights."""
        # Determine adaptive weights based on query characteristics
        weights = self._compute_adaptive_weights(query, retrieval_scores, neural_scores)
        
        fused_scores = []
        for ret_score, neural_score in zip(retrieval_scores, neural_scores):
            fused_score = weights["retrieval"] * ret_score + weights["neural"] * neural_score
            fused_scores.append(fused_score)
        
        # Update query history for future adaptations
        if self.config.query_dependent:
            self._update_query_history(query, weights)
        
        self.stats["fusions"] += 1
        return fused_scores
    
    def _compute_adaptive_weights(
        self,
        query: str,
        retrieval_scores: List[float],
        neural_scores: List[float]
    ) -> Dict[str, float]:
        """Compute adaptive weights based on query and score characteristics."""
        # Default weights
        retrieval_weight = 0.3
        neural_weight = 0.7
        
        # Adapt based on score distributions
        if retrieval_scores and neural_scores:
            ret_variance = np.var(retrieval_scores)
            neural_variance = np.var(neural_scores)
            
            # If neural scores have higher variance, trust them more
            if neural_variance > ret_variance * 1.5:
                neural_weight = 0.8
                retrieval_weight = 0.2
            elif ret_variance > neural_variance * 1.5:
                neural_weight = 0.5
                retrieval_weight = 0.5
        
        # Adapt based on query characteristics
        if self.config.query_dependent:
            query_lower = query.lower()
            
            # Technical queries might benefit more from neural reranking
            technical_terms = ["protocol", "implementation", "api", "configuration", "architecture"]
            if any(term in query_lower for term in technical_terms):
                neural_weight = min(0.9, neural_weight + 0.1)
                retrieval_weight = 1.0 - neural_weight
                self.stats["adaptations"] += 1
        
        return {"retrieval": retrieval_weight, "neural": neural_weight}
    
    def _update_query_history(self, query: str, weights: Dict[str, float]):
        """Update query history for future adaptations."""
        self.query_history.append({
            "query": query,
            "weights": weights,
            "timestamp": time.time()
        })
        
        # Keep only recent history
        if len(self.query_history) > self.config.adaptation_window:
            self.query_history = self.query_history[-self.config.adaptation_window:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get fusion statistics."""
        return self.stats.copy()


class ScoreFusion:
    """
    Main score fusion component for neural reranking.
    
    Combines retrieval scores with neural reranking scores using
    configurable strategies including weighted, learned, and adaptive fusion.
    """
    
    def __init__(self, config: ScoreFusionConfig):
        """
        Initialize score fusion.
        
        Args:
            config: Score fusion configuration
        """
        self.config = config
        self.normalizer = ScoreNormalizer(config.normalization)
        
        # Initialize fusion strategy
        if config.method == "weighted":
            self.strategy = WeightedFusion(config.weights)
        elif config.method == "learned":
            self.strategy = LearnedFusion(config.learned_fusion)
        elif config.method == "adaptive":
            self.strategy = AdaptiveFusion(config.adaptive_fusion)
        else:
            logger.warning(f"Unknown fusion method: {config.method}, using weighted")
            self.strategy = WeightedFusion(config.weights)
        
        self.stats = {
            "total_fusions": 0,
            "method": config.method
        }
        
        logger.info(f"ScoreFusion initialized with method: {config.method}")
    
    def fuse_scores(
        self,
        retrieval_scores: List[float],
        neural_scores: List[float],
        query: str,
        documents: List[Document]
    ) -> List[float]:
        """
        Fuse retrieval and neural scores.
        
        Args:
            retrieval_scores: Original retrieval scores
            neural_scores: Neural reranking scores
            query: The search query
            documents: List of documents
            
        Returns:
            Fused scores
        """
        try:
            if not retrieval_scores or not neural_scores:
                return retrieval_scores or neural_scores or []
            
            # Normalize scores first
            norm_retrieval = self.normalizer.normalize(retrieval_scores)
            norm_neural = self.normalizer.normalize(neural_scores)
            
            # Apply fusion strategy
            fused_scores = self.strategy.fuse(norm_retrieval, norm_neural, query, documents)
            
            # Final normalization if needed
            if self.config.method in ["learned", "adaptive"]:
                fused_scores = self.normalizer.normalize(fused_scores)
            
            self.stats["total_fusions"] += 1
            return fused_scores
            
        except Exception as e:
            logger.error(f"Score fusion failed: {e}")
            # Fallback to retrieval scores
            return retrieval_scores
    
    def get_stats(self) -> Dict[str, Any]:
        """Get fusion statistics."""
        stats = self.stats.copy()
        stats.update({
            "normalizer": self.normalizer.stats,
            "strategy": self.strategy.get_stats() if hasattr(self.strategy, 'get_stats') else {}
        })
        return stats
    
    def reset_stats(self) -> None:
        """Reset fusion statistics."""
        self.stats = {
            "total_fusions": 0,
            "method": self.config.method
        }
        self.normalizer.stats = {
            "normalizations": 0,
            "outliers_clipped": 0
        }
        if hasattr(self.strategy, 'stats'):
            self.strategy.stats = getattr(self.strategy.__class__, 'stats', {})