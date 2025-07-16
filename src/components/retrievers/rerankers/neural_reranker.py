"""
Enhanced Neural Reranker for Advanced Retrieval.

This module provides a sophisticated neural reranking sub-component that extends
the existing reranker capabilities with advanced features including multiple 
model support, adaptive strategies, score fusion, and performance optimization.

This is the architecture-compliant implementation in the proper rerankers/ 
sub-component location, enhanced with capabilities from the migrated utilities.
"""

import logging
import time
from typing import List, Dict, Any, Tuple, Optional, Union
import numpy as np

from src.core.interfaces import Document
from .base import Reranker
from .utils import (
    ScoreFusion, AdaptiveStrategies, CrossEncoderModels, PerformanceOptimizer,
    ModelConfig, WeightsConfig, NormalizationConfig
)

logger = logging.getLogger(__name__)


class NeuralRerankingError(Exception):
    """Raised when neural reranking operations fail."""
    pass


class NeuralReranker(Reranker):
    """
    Enhanced neural reranker with sophisticated capabilities.
    
    This reranker extends the base Reranker interface with advanced features:
    - Multiple cross-encoder model support with lazy loading
    - Query-type adaptive reranking strategies  
    - Advanced neural + retrieval score fusion
    - Performance optimization with caching and batching
    - Graceful degradation and comprehensive error handling
    - Real-time performance monitoring and adaptation
    
    The implementation follows proper architecture patterns by enhancing
    the existing rerankers sub-component with utilities from the migrated
    reranking/ module capabilities.
    
    Features:
    - ✅ Multiple model support (general + technical domains)
    - ✅ Adaptive model selection based on query type
    - ✅ Advanced score fusion with normalization strategies
    - ✅ Performance optimization (<200ms target)
    - ✅ Intelligent caching with LRU eviction
    - ✅ Batch processing with dynamic sizing
    - ✅ Comprehensive error handling and fallbacks
    - ✅ Real-time metrics collection and adaptation
    
    Example:
        config = {
            "enabled": True,
            "models": {
                "default_model": {
                    "name": "cross-encoder/ms-marco-MiniLM-L6-v2",
                    "max_length": 512,
                    "batch_size": 16
                },
                "technical_model": {
                    "name": "cross-encoder/ms-marco-electra-base",
                    "max_length": 512,
                    "batch_size": 8
                }
            },
            "adaptive": {
                "enabled": True,
                "confidence_threshold": 0.7
            },
            "score_fusion": {
                "method": "weighted",
                "weights": {
                    "neural_score": 0.7,
                    "retrieval_score": 0.3
                }
            },
            "performance": {
                "max_latency_ms": 200,
                "enable_caching": True,
                "max_cache_size": 10000
            }
        }
        reranker = NeuralReranker(config)
        results = reranker.rerank(query, documents, initial_scores)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize enhanced neural reranker.
        
        Args:
            config: Neural reranking configuration dictionary
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        
        # Parse configuration sections
        self._parse_configuration(config)
        
        # Initialize advanced components
        self.models_manager = None
        self.adaptive_strategies = None
        self.score_fusion = None
        self.performance_optimizer = None
        
        # Performance tracking
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0, 
            "failed_queries": 0,
            "total_latency_ms": 0.0,
            "model_switches": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "fallback_activations": 0,
            "adaptive_adjustments": 0
        }
        
        # State management
        self._initialized = False
        self._error_count = 0
        self._last_performance_check = time.time()
        
        # Initialize immediately if enabled (remove lazy initialization)
        initialize_immediately = config.get("initialize_immediately", True)
        if self.enabled and initialize_immediately:
            try:
                self._initialize_if_needed()
            except Exception as e:
                logger.warning(f"Failed to initialize neural reranker: {e}")
                logger.warning("Disabling neural reranker and falling back to identity mode")
                self.enabled = False
                self._initialized = True  # Mark as initialized even when disabled
        else:
            self._initialized = True  # Mark as initialized when disabled
        
        logger.info(f"Enhanced NeuralReranker initialized with {len(self.models_config)} models, "
                   f"enabled={self.enabled}, initialized={self._initialized}")
    
    def _parse_configuration(self, config: Dict[str, Any]):
        """Parse and validate configuration sections."""
        # Models configuration
        self.models_config = config.get("models", {
            "default_model": {
                "name": "cross-encoder/ms-marco-MiniLM-L6-v2",
                "max_length": 512,
                "batch_size": 16
            }
        })
        
        # Convert to ModelConfig objects
        self.model_configs = {}
        for name, model_config in self.models_config.items():
            self.model_configs[name] = ModelConfig(**model_config)
        
        # Adaptive configuration
        adaptive_config = config.get("adaptive", {})
        self.adaptive_enabled = adaptive_config.get("enabled", True)
        self.confidence_threshold = adaptive_config.get("confidence_threshold", 0.7)
        
        # Score fusion configuration
        fusion_config = config.get("score_fusion", {})
        self.fusion_method = fusion_config.get("method", "weighted")
        
        weights_config = fusion_config.get("weights", {})
        self.weights = WeightsConfig(
            retrieval_score=weights_config.get("retrieval_score", 0.3),
            neural_score=weights_config.get("neural_score", 0.7),
            graph_score=weights_config.get("graph_score", 0.0),
            temporal_score=weights_config.get("temporal_score", 0.0)
        )
        
        normalization_config = fusion_config.get("normalization", {})
        self.normalization = NormalizationConfig(
            method=normalization_config.get("method", "min_max"),
            clip_outliers=normalization_config.get("clip_outliers", True),
            outlier_threshold=normalization_config.get("outlier_threshold", 3.0)
        )
        
        # Performance configuration
        perf_config = config.get("performance", {})
        self.max_latency_ms = perf_config.get("max_latency_ms", 200)
        self.target_latency_ms = perf_config.get("target_latency_ms", 150)
        self.enable_caching = perf_config.get("enable_caching", True)
        self.max_cache_size = perf_config.get("max_cache_size", 10000)
        self.cache_ttl_seconds = perf_config.get("cache_ttl_seconds", 3600)
        
        # Legacy compatibility
        self.max_candidates = config.get("max_candidates", 50)
        self.default_model = config.get("default_model", list(self.models_config.keys())[0])
    
    def _initialize_if_needed(self) -> None:
        """Initialize advanced components lazily for better startup performance."""
        if self._initialized or not self.enabled:
            return
        
        try:
            # Initialize models manager
            self.models_manager = CrossEncoderModels(self.model_configs)
            
            # Initialize adaptive strategies
            if self.adaptive_enabled:
                self.adaptive_strategies = AdaptiveStrategies(
                    enabled=True,
                    confidence_threshold=self.confidence_threshold
                )
            
            # Initialize score fusion
            self.score_fusion = ScoreFusion(
                method=self.fusion_method,
                weights=self.weights,
                normalization=self.normalization
            )
            
            # Initialize performance optimizer
            self.performance_optimizer = PerformanceOptimizer(
                max_latency_ms=self.max_latency_ms,
                target_latency_ms=self.target_latency_ms,
                enable_caching=self.enable_caching,
                cache_ttl_seconds=self.cache_ttl_seconds,
                max_cache_size=self.max_cache_size
            )
            
            self._initialized = True
            logger.info("Enhanced NeuralReranker initialization completed")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced neural reranker: {e}")
            self.enabled = False
            raise NeuralRerankingError(f"Initialization failed: {e}")
    
    def rerank(
        self, 
        query: str, 
        documents: List[Document], 
        initial_scores: List[float]
    ) -> List[Tuple[int, float]]:
        """
        Rerank documents using enhanced neural models with advanced strategies.
        
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
            # Check if reranking is enabled
            if not self.enabled:
                return [(i, score) for i, score in enumerate(initial_scores)]
            
            # Validate inputs
            if not documents or not query.strip():
                return []
            
            if len(initial_scores) != len(documents):
                logger.warning("Mismatch between documents and scores, using defaults")
                initial_scores = [1.0] * len(documents)
            
            # Initialize if needed
            self._initialize_if_needed()
            
            if not self._initialized:
                logger.warning("Enhanced neural reranker not initialized, using initial scores")
                return [(i, score) for i, score in enumerate(initial_scores)]
            
            # Check cache first
            cached_scores = self.performance_optimizer.get_cached_scores(
                query, documents, self.default_model
            )
            
            if cached_scores is not None:
                self.stats["cache_hits"] += 1
                return [(i, score) for i, score in enumerate(cached_scores)]
            
            self.stats["cache_misses"] += 1
            
            # Limit candidates for performance
            max_candidates = min(len(documents), self.max_candidates)
            if len(documents) > max_candidates:
                # Sort by initial scores and take top candidates
                sorted_indices = sorted(range(len(initial_scores)), 
                                      key=lambda i: initial_scores[i], reverse=True)
                top_indices = sorted_indices[:max_candidates]
                documents = [documents[i] for i in top_indices]
                initial_scores = [initial_scores[i] for i in top_indices]
            else:
                top_indices = list(range(len(documents)))
            
            # Select optimal model for this query
            selected_model = self._select_model_for_query(query)
            
            # Get neural scores
            neural_scores = self._get_neural_scores(query, documents, selected_model)
            
            # Fuse scores using advanced fusion strategies
            fused_scores = self.score_fusion.fuse_scores(
                initial_scores, neural_scores, query, documents
            )
            
            # Cache the results
            self.performance_optimizer.cache_scores(
                query, documents, selected_model, fused_scores
            )
            
            # Create final results with original indices
            results = []
            for i, score in enumerate(fused_scores):
                original_idx = top_indices[i] if len(documents) <= max_candidates else top_indices[i]
                results.append((original_idx, score))
            
            results.sort(key=lambda x: x[1], reverse=True)
            
            # Update performance statistics
            latency_ms = (time.time() - start_time) * 1000
            self._update_stats(latency_ms, success=True)
            self.performance_optimizer.record_latency(latency_ms)
            
            # Record performance for adaptive learning
            if self.adaptive_strategies:
                query_analysis = self.adaptive_strategies.detector.classify_query(query) if self.adaptive_strategies.detector else None
                query_type = query_analysis.query_type if query_analysis else "general"
                quality_score = self._estimate_quality_score(fused_scores, initial_scores)
                
                self.adaptive_strategies.record_performance(
                    selected_model, query_type, latency_ms, quality_score
                )
            
            # Log performance
            logger.debug(f"Enhanced neural reranking completed in {latency_ms:.1f}ms for {len(documents)} documents")
            
            return results
            
        except Exception as e:
            # Handle errors gracefully
            latency_ms = (time.time() - start_time) * 1000
            self._update_stats(latency_ms, success=False)
            self.stats["fallback_activations"] += 1
            logger.error(f"Enhanced neural reranking failed: {e}")
            
            # Return fallback results
            return [(i, score) for i, score in enumerate(initial_scores)]
    
    def _select_model_for_query(self, query: str) -> str:
        """
        Select the optimal model for the given query using adaptive strategies.
        
        Args:
            query: The search query
            
        Returns:
            Name of the selected model
        """
        if not self.adaptive_strategies or not self.adaptive_strategies.enabled:
            return self.default_model
        
        try:
            available_models = self.models_manager.get_available_models()
            selected_model = self.adaptive_strategies.select_model(
                query, available_models, self.default_model
            )
            
            if selected_model != self.default_model:
                self.stats["model_switches"] += 1
                self.stats["adaptive_adjustments"] += 1
            
            return selected_model
            
        except Exception as e:
            logger.warning(f"Adaptive model selection failed: {e}, using default")
            return self.default_model
    
    def _get_neural_scores(
        self, 
        query: str, 
        documents: List[Document], 
        model_name: str
    ) -> List[float]:
        """
        Get neural relevance scores for query-document pairs.
        
        Args:
            query: The search query
            documents: List of documents
            model_name: Name of the model to use
            
        Returns:
            List of neural relevance scores
        """
        try:
            # Prepare query-document pairs
            query_doc_pairs = []
            for doc in documents:
                doc_text = doc.content
                
                # Smart truncation for model max_length
                model_config = self.model_configs.get(model_name)
                if model_config:
                    max_length = model_config.max_length
                    if len(doc_text) > max_length:
                        # Try to keep complete sentences
                        truncated = doc_text[:max_length - 50]
                        last_period = truncated.rfind('.')
                        if last_period > max_length // 2:
                            doc_text = truncated[:last_period + 1]
                        else:
                            doc_text = truncated + "..."
                
                query_doc_pairs.append([query, doc_text])
            
            # Get scores using models manager
            neural_scores = self.models_manager.predict(query_doc_pairs, model_name)
            
            return neural_scores
            
        except Exception as e:
            logger.error(f"Neural scoring failed: {e}")
            return [0.0] * len(documents)
    
    def _estimate_quality_score(
        self, 
        fused_scores: List[float], 
        initial_scores: List[float]
    ) -> float:
        """
        Estimate quality improvement from neural reranking.
        
        Args:
            fused_scores: Final fused scores
            initial_scores: Initial retrieval scores
            
        Returns:
            Quality score (0-1)
        """
        try:
            # Simple heuristic: how much did the score distribution improve?
            if not fused_scores or not initial_scores:
                return 0.5
            
            # Calculate variance of scores (higher variance = better discrimination)
            fused_variance = np.var(fused_scores)
            initial_variance = np.var(initial_scores)
            
            # Calculate improvement ratio
            if initial_variance > 0:
                improvement_ratio = fused_variance / initial_variance
                # Normalize to 0-1 range
                quality_score = min(1.0, improvement_ratio / 2.0)
            else:
                quality_score = 0.5
            
            return quality_score
            
        except Exception:
            return 0.5
    
    def _update_stats(self, latency_ms: float, success: bool) -> None:
        """Update performance statistics."""
        if success:
            self.stats["successful_queries"] += 1
        else:
            self.stats["failed_queries"] += 1
            self._error_count += 1
        
        self.stats["total_latency_ms"] += latency_ms
    
    def is_enabled(self) -> bool:
        """
        Check if neural reranking is enabled.
        
        Returns:
            True if reranking should be performed
        """
        # Return True if configured to be enabled, regardless of initialization status
        # Initialization happens lazily when rerank() is called
        return self.enabled
    
    def get_reranker_info(self) -> Dict[str, Any]:
        """
        Get information about the enhanced neural reranker.
        
        Returns:
            Dictionary with reranker configuration and statistics
        """
        base_info = {
            "type": "enhanced_neural_reranker",
            "enabled": self.enabled,
            "initialized": self._initialized,
            "default_model": self.default_model,
            "total_models": len(self.models_config),
            "adaptive_enabled": self.adaptive_enabled,
            "score_fusion_method": self.fusion_method,
            "max_latency_ms": self.max_latency_ms,
            "target_latency_ms": self.target_latency_ms,
            "caching_enabled": self.enable_caching
        }
        
        # Add model information
        if self._initialized and self.models_manager:
            base_info["models"] = {
                name: config.name 
                for name, config in self.model_configs.items()
            }
            base_info["model_stats"] = self.models_manager.get_model_stats()
        
        # Add statistics
        base_info["statistics"] = self.stats.copy()
        
        # Add component statistics
        if self._initialized:
            if self.adaptive_strategies:
                base_info["adaptive_stats"] = self.adaptive_strategies.get_stats()
            
            if self.score_fusion:
                base_info["fusion_stats"] = self.score_fusion.get_stats()
            
            if self.performance_optimizer:
                base_info["performance_stats"] = self.performance_optimizer.get_stats()
        
        # Add performance metrics
        if self.stats["total_queries"] > 0:
            base_info["avg_latency_ms"] = self.stats["total_latency_ms"] / self.stats["total_queries"]
            base_info["success_rate"] = self.stats["successful_queries"] / self.stats["total_queries"]
            cache_total = self.stats["cache_hits"] + self.stats["cache_misses"]
            if cache_total > 0:
                base_info["cache_hit_rate"] = self.stats["cache_hits"] / cache_total
        
        return base_info
    
    def reset_stats(self) -> None:
        """Reset all statistics."""
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0, 
            "failed_queries": 0,
            "total_latency_ms": 0.0,
            "model_switches": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "fallback_activations": 0,
            "adaptive_adjustments": 0
        }
        
        if self._initialized:
            if self.adaptive_strategies:
                self.adaptive_strategies.reset_stats()
            if self.score_fusion:
                self.score_fusion.reset_stats()
            if self.performance_optimizer:
                self.performance_optimizer.reset_stats()