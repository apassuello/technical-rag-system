"""
Semantic Reranker implementation for Modular Retriever Architecture.

This module provides a direct implementation of cross-encoder based reranking
to improve retrieval quality by reordering candidates based on query relevance.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from src.core.interfaces import Document
from .base import Reranker

logger = logging.getLogger(__name__)


class SemanticReranker(Reranker):
    """
    Semantic reranker using cross-encoder models.
    
    This is a direct implementation that uses cross-encoder models to rerank
    retrieval results based on query-document relevance scores.
    No external API dependencies are required.
    
    Features:
    - Cross-encoder model support (sentence-transformers)
    - Configurable reranking threshold
    - Batch processing for efficiency
    - Optional reranking (can be disabled)
    - Performance monitoring
    
    Example:
        config = {
            "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "enabled": True,
            "batch_size": 32,
            "top_k": 10,
            "score_threshold": 0.0
        }
        reranker = SemanticReranker(config)
        results = reranker.rerank(query, documents, initial_scores)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize semantic reranker.
        
        Args:
            config: Configuration dictionary with:
                - model: Cross-encoder model name (default: "cross-encoder/ms-marco-MiniLM-L-6-v2")
                - enabled: Whether reranking is enabled (default: True)
                - batch_size: Batch size for model inference (default: 32)
                - top_k: Maximum number of documents to rerank (default: 10)
                - score_threshold: Minimum score threshold for reranking (default: 0.0)
                - device: Device to run model on (default: "auto")
        """
        self.config = config
        self.model_name = config.get("model", "cross-encoder/ms-marco-MiniLM-L-6-v2")
        self.enabled = config.get("enabled", True)
        self.batch_size = config.get("batch_size", 32)
        self.top_k = config.get("top_k", 10)
        self.score_threshold = config.get("score_threshold", 0.0)
        self.device = config.get("device", "auto")
        
        # Initialize model lazily
        self.model = None
        self._model_loaded = False
        
        # Validation
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if self.top_k <= 0:
            raise ValueError("top_k must be positive")
        
        logger.info(f"SemanticReranker initialized with model={self.model_name}, enabled={self.enabled}")
    
    def _load_model(self) -> None:
        """Load the cross-encoder model lazily."""
        if self._model_loaded:
            return
        
        if not self.enabled:
            logger.info("Reranker disabled, skipping model loading")
            self._model_loaded = True
            return
        
        try:
            from sentence_transformers import CrossEncoder
            
            logger.info(f"Loading cross-encoder model: {self.model_name}")
            self.model = CrossEncoder(self.model_name, device=self.device)
            self._model_loaded = True
            logger.info("Cross-encoder model loaded successfully")
            
        except ImportError:
            logger.warning("sentence-transformers not available, disabling reranker")
            self.enabled = False
            self._model_loaded = True
        except Exception as e:
            logger.error(f"Failed to load cross-encoder model: {e}")
            self.enabled = False
            self._model_loaded = True
    
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
        if not self.enabled:
            # Return original ranking if reranking is disabled
            return [(i, score) for i, score in enumerate(initial_scores)]
        
        if not documents or not query.strip():
            return []
        
        # Load model if not already loaded
        self._load_model()
        
        if not self._model_loaded or self.model is None:
            # Fallback to original ranking
            return [(i, score) for i, score in enumerate(initial_scores)]
        
        # Limit to top_k documents for efficiency
        num_docs = min(len(documents), self.top_k)
        
        # Create query-document pairs for cross-encoder
        query_doc_pairs = []
        doc_indices = []
        
        for i in range(num_docs):
            doc_text = documents[i].content
            # Truncate very long documents for efficiency
            if len(doc_text) > 2000:
                doc_text = doc_text[:2000] + "..."
            
            query_doc_pairs.append([query, doc_text])
            doc_indices.append(i)
        
        try:
            # Get cross-encoder scores in batches
            cross_encoder_scores = []
            for i in range(0, len(query_doc_pairs), self.batch_size):
                batch = query_doc_pairs[i:i + self.batch_size]
                batch_scores = self.model.predict(batch)
                cross_encoder_scores.extend(batch_scores)
            
            # Create reranked results
            reranked_results = []
            for i, score in enumerate(cross_encoder_scores):
                doc_idx = doc_indices[i]
                # Apply score threshold
                if score >= self.score_threshold:
                    reranked_results.append((doc_idx, float(score)))
            
            # Add remaining documents that weren't reranked
            for i in range(num_docs, len(documents)):
                if i < len(initial_scores):
                    reranked_results.append((i, initial_scores[i]))
            
            # Sort by reranked score (descending)
            reranked_results.sort(key=lambda x: x[1], reverse=True)
            
            return reranked_results
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}, falling back to original ranking")
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
        info = {
            "model": self.model_name,
            "enabled": self.enabled,
            "batch_size": self.batch_size,
            "top_k": self.top_k,
            "score_threshold": self.score_threshold,
            "device": self.device,
            "model_loaded": self._model_loaded
        }
        
        if self.model is not None:
            info["model_device"] = str(self.model.device)
        
        return info
    
    def enable(self) -> None:
        """Enable reranking."""
        self.enabled = True
        logger.info("Reranker enabled")
    
    def disable(self) -> None:
        """Disable reranking."""
        self.enabled = False
        logger.info("Reranker disabled")
    
    def set_top_k(self, top_k: int) -> None:
        """
        Set the maximum number of documents to rerank.
        
        Args:
            top_k: Maximum number of documents to rerank
        """
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        
        self.top_k = top_k
        logger.info(f"Reranker top_k set to {top_k}")
    
    def set_score_threshold(self, threshold: float) -> None:
        """
        Set the minimum score threshold for reranking.
        
        Args:
            threshold: Minimum score threshold
        """
        self.score_threshold = threshold
        logger.info(f"Reranker score threshold set to {threshold}")
    
    def predict_scores(self, query: str, documents: List[Document]) -> List[float]:
        """
        Get cross-encoder scores for query-document pairs.
        
        Args:
            query: The search query
            documents: List of documents
            
        Returns:
            List of relevance scores
        """
        if not self.enabled:
            return [0.0] * len(documents)
        
        self._load_model()
        
        if not self._model_loaded or self.model is None:
            return [0.0] * len(documents)
        
        # Create query-document pairs
        query_doc_pairs = []
        for doc in documents:
            doc_text = doc.content
            if len(doc_text) > 2000:
                doc_text = doc_text[:2000] + "..."
            query_doc_pairs.append([query, doc_text])
        
        try:
            # Get scores in batches
            scores = []
            for i in range(0, len(query_doc_pairs), self.batch_size):
                batch = query_doc_pairs[i:i + self.batch_size]
                batch_scores = self.model.predict(batch)
                scores.extend(batch_scores)
            
            return [float(score) for score in scores]
            
        except Exception as e:
            logger.error(f"Score prediction failed: {e}")
            return [0.0] * len(documents)
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        if not self._model_loaded or self.model is None:
            return {"status": "not_loaded"}
        
        info = {
            "status": "loaded",
            "model_name": self.model_name,
            "device": str(self.model.device) if hasattr(self.model, 'device') else "unknown"
        }
        
        # Try to get model-specific info
        try:
            if hasattr(self.model, 'model'):
                info["model_type"] = type(self.model.model).__name__
            if hasattr(self.model, 'tokenizer'):
                info["tokenizer_type"] = type(self.model.tokenizer).__name__
        except:
            pass
        
        return info