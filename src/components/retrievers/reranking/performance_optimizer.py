"""
Performance Optimizer for Neural Reranking.

This module provides performance optimization capabilities including
caching, batch processing, latency optimization, and resource management
to ensure neural reranking meets the <200ms additional latency target.
"""

import logging
import time
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from collections import OrderedDict
import threading

from src.core.interfaces import Document
from .config.reranking_config import PerformanceConfig

logger = logging.getLogger(__name__)


class LRUCache:
    """Thread-safe LRU cache for neural reranking scores."""
    
    def __init__(self, max_size: int, ttl_seconds: int = 3600):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of entries
            ttl_seconds: Time-to-live for cache entries
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = OrderedDict()
        self.timestamps = {}
        self._lock = threading.Lock()
        
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "ttl_expirations": 0
        }
    
    def get(self, key: str) -> Optional[List[float]]:
        """Get cached scores by key."""
        with self._lock:
            current_time = time.time()
            
            if key in self.cache:
                # Check TTL
                if current_time - self.timestamps[key] > self.ttl_seconds:
                    del self.cache[key]
                    del self.timestamps[key]
                    self.stats["ttl_expirations"] += 1
                    self.stats["misses"] += 1
                    return None
                
                # Move to end (most recently used)
                value = self.cache.pop(key)
                self.cache[key] = value
                self.stats["hits"] += 1
                return value
            
            self.stats["misses"] += 1
            return None
    
    def put(self, key: str, value: List[float]) -> None:
        """Cache scores with key."""
        with self._lock:
            current_time = time.time()
            
            if key in self.cache:
                # Update existing entry
                self.cache.pop(key)
            elif len(self.cache) >= self.max_size:
                # Evict least recently used
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.timestamps[oldest_key]
                self.stats["evictions"] += 1
            
            self.cache[key] = value
            self.timestamps[key] = current_time
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self.cache.clear()
            self.timestamps.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0
            
            return {
                **self.stats,
                "size": len(self.cache),
                "max_size": self.max_size,
                "hit_rate": hit_rate
            }


class BatchProcessor:
    """Optimized batch processing for neural model inference."""
    
    def __init__(self, config: PerformanceConfig):
        """
        Initialize batch processor.
        
        Args:
            config: Performance configuration
        """
        self.config = config
        self.stats = {
            "batches_processed": 0,
            "total_items": 0,
            "total_time_ms": 0,
            "adaptive_adjustments": 0
        }
        
        # Dynamic batch size tracking
        self.current_batch_size = config.max_batch_size // 2
        self.latency_history = []
    
    def process_batch(self, model, query_doc_pairs: List[List[str]]) -> List[float]:
        """
        Process query-document pairs in optimized batches.
        
        Args:
            model: Model for inference
            query_doc_pairs: List of [query, document] pairs
            
        Returns:
            List of relevance scores
        """
        if not query_doc_pairs:
            return []
        
        start_time = time.time()
        all_scores = []
        
        try:
            # Process in batches
            for i in range(0, len(query_doc_pairs), self.current_batch_size):
                batch = query_doc_pairs[i:i + self.current_batch_size]
                
                batch_start = time.time()
                batch_scores = model.predict(batch)
                batch_latency = (time.time() - batch_start) * 1000
                
                all_scores.extend(batch_scores)
                
                # Track latency for adaptive adjustment
                self.latency_history.append(batch_latency)
                
                # Early stopping if taking too long
                if self.config.enable_early_stopping:
                    total_elapsed = (time.time() - start_time) * 1000
                    if total_elapsed > self.config.max_latency_ms * 0.8:  # 80% of limit
                        logger.warning(f"Early stopping batch processing at {total_elapsed:.1f}ms")
                        break
            
            # Update statistics
            total_time = (time.time() - start_time) * 1000
            self.stats["batches_processed"] += 1
            self.stats["total_items"] += len(query_doc_pairs)
            self.stats["total_time_ms"] += total_time
            
            # Adaptive batch size adjustment
            if self.config.dynamic_batching:
                self._adjust_batch_size(total_time, len(query_doc_pairs))
            
            return all_scores
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            raise
    
    def _adjust_batch_size(self, total_time_ms: float, num_items: int) -> None:
        """Adjust batch size based on recent performance."""
        if len(self.latency_history) < 5:  # Need some history
            return
        
        try:
            # Calculate recent average latency per item
            recent_latencies = self.latency_history[-5:]
            avg_latency_per_batch = sum(recent_latencies) / len(recent_latencies)
            
            # Target: stay under target latency
            target_latency = self.config.target_latency_ms
            
            if avg_latency_per_batch > target_latency * 0.8:  # Too slow
                # Reduce batch size
                new_batch_size = max(
                    self.config.min_batch_size,
                    int(self.current_batch_size * 0.8)
                )
                if new_batch_size != self.current_batch_size:
                    self.current_batch_size = new_batch_size
                    self.stats["adaptive_adjustments"] += 1
                    logger.debug(f"Reduced batch size to {self.current_batch_size}")
                    
            elif avg_latency_per_batch < target_latency * 0.5:  # Too conservative
                # Increase batch size
                new_batch_size = min(
                    self.config.max_batch_size,
                    int(self.current_batch_size * 1.2)
                )
                if new_batch_size != self.current_batch_size:
                    self.current_batch_size = new_batch_size
                    self.stats["adaptive_adjustments"] += 1
                    logger.debug(f"Increased batch size to {self.current_batch_size}")
            
            # Keep only recent history
            if len(self.latency_history) > 20:
                self.latency_history = self.latency_history[-20:]
                
        except Exception as e:
            logger.warning(f"Batch size adjustment failed: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get batch processing statistics."""
        stats = self.stats.copy()
        
        if stats["batches_processed"] > 0:
            stats["avg_batch_time_ms"] = stats["total_time_ms"] / stats["batches_processed"]
            stats["avg_items_per_batch"] = stats["total_items"] / stats["batches_processed"]
        
        stats["current_batch_size"] = self.current_batch_size
        
        if self.latency_history:
            stats["recent_avg_latency_ms"] = sum(self.latency_history[-5:]) / min(5, len(self.latency_history))
        
        return stats


class PerformanceOptimizer:
    """
    Performance optimizer for neural reranking.
    
    Provides caching, batch processing, latency optimization, and resource
    management to ensure neural reranking meets performance targets.
    """
    
    def __init__(self, config: PerformanceConfig):
        """
        Initialize performance optimizer.
        
        Args:
            config: Performance configuration
        """
        self.config = config
        
        # Initialize cache if enabled
        if config.enable_caching:
            self.cache = LRUCache(config.max_cache_size, config.cache_ttl_seconds)
        else:
            self.cache = None
        
        # Initialize batch processor
        self.batch_processor = BatchProcessor(config)
        
        # Performance tracking
        self.stats = {
            "optimizations": 0,
            "cache_operations": 0,
            "fallback_activations": 0,
            "latency_adaptations": 0
        }
        
        self.initialized = False
        logger.info(f"PerformanceOptimizer initialized, caching={config.enable_caching}")
    
    def initialize(self) -> None:
        """Initialize performance optimizer."""
        if self.initialized:
            return
        
        # Perform any initialization tasks
        self.initialized = True
        logger.info("PerformanceOptimizer initialization completed")
    
    def optimize_input(
        self, 
        documents: List[Document], 
        scores: List[float], 
        max_candidates: int
    ) -> Tuple[List[Document], List[float]]:
        """
        Optimize input by limiting candidates and sorting by relevance.
        
        Args:
            documents: List of documents
            scores: Initial scores
            max_candidates: Maximum candidates to process
            
        Returns:
            Tuple of optimized documents and scores
        """
        try:
            if len(documents) <= max_candidates:
                return documents, scores
            
            # Sort by initial scores and take top candidates
            doc_score_pairs = list(zip(documents, scores))
            doc_score_pairs.sort(key=lambda x: x[1], reverse=True)
            
            optimized_docs = [pair[0] for pair in doc_score_pairs[:max_candidates]]
            optimized_scores = [pair[1] for pair in doc_score_pairs[:max_candidates]]
            
            self.stats["optimizations"] += 1
            
            logger.debug(f"Optimized input from {len(documents)} to {len(optimized_docs)} candidates")
            return optimized_docs, optimized_scores
            
        except Exception as e:
            logger.error(f"Input optimization failed: {e}")
            return documents, scores
    
    def get_cache_key(self, query: str, documents: List[Document], model_name: str) -> str:
        """
        Generate cache key for query-documents-model combination.
        
        Args:
            query: Search query
            documents: List of documents  
            model_name: Model name
            
        Returns:
            Cache key string
        """
        # Create a hash of query + document contents + model
        content_hash = hashlib.md5()
        content_hash.update(query.encode('utf-8'))
        content_hash.update(model_name.encode('utf-8'))
        
        for doc in documents:
            # Use first 200 chars of content for hashing
            doc_snippet = doc.content[:200] if len(doc.content) > 200 else doc.content
            content_hash.update(doc_snippet.encode('utf-8'))
        
        return content_hash.hexdigest()
    
    def get_cached_scores(self, cache_key: str) -> Optional[List[float]]:
        """Get cached scores if available."""
        if not self.cache:
            return None
        
        self.stats["cache_operations"] += 1
        return self.cache.get(cache_key)
    
    def cache_scores(self, cache_key: str, scores: List[float]) -> None:
        """Cache scores for future use."""
        if not self.cache:
            return
        
        self.cache.put(cache_key, scores)
        self.stats["cache_operations"] += 1
    
    def batch_predict(
        self, 
        model, 
        query_doc_pairs: List[List[str]], 
        batch_size: int
    ) -> List[float]:
        """
        Perform optimized batch prediction.
        
        Args:
            model: Model for inference
            query_doc_pairs: Query-document pairs
            batch_size: Batch size (may be adapted)
            
        Returns:
            List of scores
        """
        # Use batch processor for optimized inference
        return self.batch_processor.process_batch(model, query_doc_pairs)
    
    def adapt_for_latency(self, current_latency_ms: float) -> None:
        """
        Adapt configuration based on current latency.
        
        Args:
            current_latency_ms: Current processing latency
        """
        if current_latency_ms <= self.config.target_latency_ms:
            return  # Performance is good
        
        try:
            # Reduce batch size if latency is too high
            if self.config.dynamic_batching:
                reduction_factor = min(0.8, self.config.target_latency_ms / current_latency_ms)
                new_batch_size = max(
                    self.config.min_batch_size,
                    int(self.batch_processor.current_batch_size * reduction_factor)
                )
                
                if new_batch_size != self.batch_processor.current_batch_size:
                    self.batch_processor.current_batch_size = new_batch_size
                    self.stats["latency_adaptations"] += 1
                    logger.info(f"Adapted batch size to {new_batch_size} due to latency {current_latency_ms:.1f}ms")
            
            # Could implement other adaptations like reducing max_candidates
            
        except Exception as e:
            logger.warning(f"Latency adaptation failed: {e}")
    
    def optimize_cache(self) -> None:
        """Optimize cache performance."""
        if not self.cache:
            return
        
        try:
            cache_stats = self.cache.get_stats()
            
            # Clear cache if hit rate is very low
            if cache_stats.get("hit_rate", 0) < 0.1 and cache_stats.get("size", 0) > 100:
                self.cache.clear()
                logger.info("Cleared cache due to low hit rate")
            
        except Exception as e:
            logger.warning(f"Cache optimization failed: {e}")
    
    def check_resource_usage(self) -> Dict[str, Any]:
        """Check current resource usage."""
        try:
            import psutil
            
            # Get memory usage
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            
            resource_info = {
                "memory_mb": memory_mb,
                "memory_limit_mb": self.config.max_memory_mb,
                "memory_usage_pct": (memory_mb / self.config.max_memory_mb) * 100,
                "cache_size": self.cache.get_stats()["size"] if self.cache else 0
            }
            
            # Check if memory usage is too high
            if resource_info["memory_usage_pct"] > 90:
                logger.warning(f"High memory usage: {resource_info['memory_usage_pct']:.1f}%")
                
                # Clear cache to free memory
                if self.cache:
                    self.cache.clear()
                    logger.info("Cleared cache due to high memory usage")
            
            return resource_info
            
        except ImportError:
            return {"status": "psutil not available"}
        except Exception as e:
            logger.warning(f"Resource check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance optimizer statistics."""
        stats = self.stats.copy()
        
        # Add batch processor stats
        stats["batch_processor"] = self.batch_processor.get_stats()
        
        # Add cache stats if available
        if self.cache:
            stats["cache"] = self.cache.get_stats()
        
        # Add resource usage
        stats["resources"] = self.check_resource_usage()
        
        return stats
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.cache:
            self.cache.clear()
        
        logger.info("PerformanceOptimizer cleanup completed")