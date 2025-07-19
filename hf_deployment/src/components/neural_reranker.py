"""
Self-contained Neural Reranker for HF Deployment.

Simplified implementation of neural reranking without external dependencies
from the main project. Uses cross-encoder models for document reranking.
"""

import logging
import time
from typing import List, Dict, Any, Tuple, Optional
import sys

try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False

from .base_reranker import Reranker, Document

logger = logging.getLogger(__name__)


class NeuralReranker(Reranker):
    """
    Self-contained neural reranker using cross-encoder models.
    
    This implementation is designed for HF deployment with minimal dependencies
    and focuses on reliable neural reranking functionality.
    
    Features:
    - Cross-encoder based reranking (local models)
    - Configurable model selection
    - Performance optimization with batch processing
    - Graceful fallback when models unavailable
    - Memory-efficient operation
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize neural reranker.
        
        Args:
            config: Configuration dictionary with model and performance settings
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        
        # Model configuration
        self.model_name = config.get("model_name", "cross-encoder/ms-marco-MiniLM-L6-v2")
        self.max_length = config.get("max_length", 512)
        self.batch_size = config.get("batch_size", 32)
        self.max_candidates = config.get("max_candidates", 100)
        
        # Performance settings
        self.max_latency_ms = config.get("max_latency_ms", 5000)
        self.fallback_to_fast_reranker = config.get("fallback_to_fast_reranker", True)
        
        # Statistics
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "total_latency_ms": 0.0,
            "fallback_activations": 0
        }
        
        # Model initialization
        self.model = None
        self._initialized = False
        
        # Check if we can use cross-encoder models
        if not CROSS_ENCODER_AVAILABLE:
            logger.warning("sentence-transformers not available, disabling neural reranking")
            self.enabled = False
        
        # Initialize model if enabled
        if self.enabled:
            self._initialize_model()
        
        logger.info(f"NeuralReranker initialized with model='{self.model_name}', enabled={self.enabled}")
    
    def _initialize_model(self):
        """Initialize the cross-encoder model."""
        try:
            print(f"🧠 Loading neural reranker model: {self.model_name}", file=sys.stderr, flush=True)
            self.model = CrossEncoder(self.model_name)
            self._initialized = True
            print(f"✅ Neural reranker model loaded successfully", file=sys.stderr, flush=True)
            
        except Exception as e:
            logger.error(f"Failed to load neural reranker model '{self.model_name}': {e}")
            print(f"❌ Neural reranker model failed to load: {e}", file=sys.stderr, flush=True)
            self.enabled = False
            self._initialized = False
    
    def rerank(
        self, 
        query: str, 
        documents: List[Document], 
        initial_scores: List[float]
    ) -> List[Tuple[int, float]]:
        """
        Rerank documents using neural cross-encoder model.
        
        Args:
            query: The search query
            documents: List of candidate documents
            initial_scores: Initial relevance scores from retrieval
            
        Returns:
            List of (document_index, reranked_score) tuples sorted by score
        """
        start_time = time.time()
        self.stats["total_queries"] += 1
        
        try:
            # Check if reranking is enabled and available
            if not self.enabled or not self._initialized:
                # Return original scores as fallback
                return [(i, score) for i, score in enumerate(initial_scores)]
            
            # Validate inputs
            if not documents or not query.strip():
                return []
            
            if len(initial_scores) != len(documents):
                logger.warning("Mismatch between documents and scores, using defaults")
                initial_scores = [1.0] * len(documents)
            
            # Limit candidates for performance
            max_candidates = min(len(documents), self.max_candidates)
            if len(documents) > max_candidates:
                # Sort by initial scores and take top candidates
                sorted_indices = sorted(range(len(initial_scores)), 
                                      key=lambda i: initial_scores[i], reverse=True)
                top_indices = sorted_indices[:max_candidates]
                selected_docs = [documents[i] for i in top_indices]
                selected_scores = [initial_scores[i] for i in top_indices]
            else:
                top_indices = list(range(len(documents)))
                selected_docs = documents
                selected_scores = initial_scores
            
            # Prepare query-document pairs for cross-encoder
            query_doc_pairs = []
            for doc in selected_docs:
                doc_text = doc.content
                
                # Truncate if necessary to fit model max_length
                if len(doc_text) > self.max_length - 50:  # Leave room for query
                    # Try to keep complete sentences
                    truncated = doc_text[:self.max_length - 50]
                    last_period = truncated.rfind('.')
                    if last_period > len(truncated) // 2:
                        doc_text = truncated[:last_period + 1]
                    else:
                        doc_text = truncated + "..."
                
                query_doc_pairs.append([query, doc_text])
            
            # Get neural relevance scores
            neural_scores = self.model.predict(query_doc_pairs)
            
            # Convert numpy scores to Python floats if necessary
            if hasattr(neural_scores, 'tolist'):
                neural_scores = neural_scores.tolist()
            
            # Ensure we have the right number of scores
            if len(neural_scores) != len(selected_docs):
                logger.warning(f"Neural model returned {len(neural_scores)} scores for {len(selected_docs)} documents")
                neural_scores = neural_scores[:len(selected_docs)]
            
            # Create final results with original indices
            results = []
            for i, neural_score in enumerate(neural_scores):
                original_idx = top_indices[i]
                # Use neural score directly (cross-encoder scores are already relevance scores)
                results.append((original_idx, float(neural_score)))
            
            # Add remaining documents with their original scores if we truncated
            if len(documents) > max_candidates:
                remaining_indices = sorted_indices[max_candidates:]
                for idx in remaining_indices:
                    results.append((idx, initial_scores[idx] * 0.5))  # Penalize non-reranked docs
            
            # Sort by reranked scores
            results.sort(key=lambda x: x[1], reverse=True)
            
            # Update statistics
            latency_ms = (time.time() - start_time) * 1000
            self.stats["successful_queries"] += 1
            self.stats["total_latency_ms"] += latency_ms
            
            logger.debug(f"Neural reranking completed in {latency_ms:.1f}ms for {len(documents)} documents")
            
            return results
            
        except Exception as e:
            # Handle errors gracefully with fallback
            latency_ms = (time.time() - start_time) * 1000
            self.stats["failed_queries"] += 1
            self.stats["fallback_activations"] += 1
            self.stats["total_latency_ms"] += latency_ms
            
            logger.error(f"Neural reranking failed: {e}")
            
            # Return original scores as fallback
            return [(i, score) for i, score in enumerate(initial_scores)]
    
    def is_enabled(self) -> bool:
        """
        Check if neural reranking is enabled.
        
        Returns:
            True if reranking should be performed
        """
        return self.enabled and self._initialized
    
    def get_reranker_info(self) -> Dict[str, Any]:
        """
        Get information about the neural reranker.
        
        Returns:
            Dictionary with reranker configuration and statistics
        """
        info = {
            "type": "neural_reranker",
            "model_name": self.model_name,
            "enabled": self.enabled,
            "initialized": self._initialized,
            "max_length": self.max_length,
            "batch_size": self.batch_size,
            "max_candidates": self.max_candidates,
            "cross_encoder_available": CROSS_ENCODER_AVAILABLE,
            "statistics": self.stats.copy()
        }
        
        # Add performance metrics
        if self.stats["total_queries"] > 0:
            info["avg_latency_ms"] = self.stats["total_latency_ms"] / self.stats["total_queries"]
            info["success_rate"] = self.stats["successful_queries"] / self.stats["total_queries"]
        
        return info
    
    def reset_stats(self):
        """Reset statistics."""
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "total_latency_ms": 0.0,
            "fallback_activations": 0
        }


class IdentityReranker(Reranker):
    """
    Identity reranker that returns original scores unchanged.
    
    Used as a fallback when neural reranking is disabled or unavailable.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize identity reranker."""
        self.config = config
        self.enabled = config.get("enabled", True)
        
    def rerank(
        self, 
        query: str, 
        documents: List[Document], 
        initial_scores: List[float]
    ) -> List[Tuple[int, float]]:
        """Return original scores unchanged."""
        return [(i, score) for i, score in enumerate(initial_scores)]
    
    def is_enabled(self) -> bool:
        """Identity reranker is always enabled."""
        return self.enabled
    
    def get_reranker_info(self) -> Dict[str, Any]:
        """Get identity reranker info."""
        return {
            "type": "identity_reranker",
            "enabled": self.enabled,
            "description": "Returns original scores unchanged"
        }