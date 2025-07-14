"""
Performance Optimization for Neural Reranking.

This module provides performance optimization capabilities including
caching, batch processing, latency optimization, and resource management
to ensure neural reranking meets the <200ms additional latency target.

Simplified from reranking/performance_optimizer.py for integration with
the enhanced neural reranker in the rerankers/ component.
"""

import logging
import time
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from collections import OrderedDict
import threading

from src.core.interfaces import Document

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
            
            # Check if key exists and is not expired
            if key in self.cache:
                if current_time - self.timestamps[key] < self.ttl_seconds:
                    # Move to end (most recently used)
                    value = self.cache.pop(key)
                    self.cache[key] = value
                    self.stats["hits"] += 1
                    return value
                else:
                    # Expired
                    del self.cache[key]
                    del self.timestamps[key]
                    self.stats["ttl_expirations"] += 1
            
            self.stats["misses"] += 1
            return None
    
    def put(self, key: str, value: List[float]):
        """Put scores in cache."""
        with self._lock:
            current_time = time.time()
            
            # Remove if already exists
            if key in self.cache:
                del self.cache[key]
                del self.timestamps[key]
            
            # Add new entry
            self.cache[key] = value
            self.timestamps[key] = current_time
            
            # Check size limit
            while len(self.cache) > self.max_size:
                # Remove least recently used
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.timestamps[oldest_key]
                self.stats["evictions"] += 1
    
    def clear(self):
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
                "hit_rate": hit_rate,
                "ttl_seconds": self.ttl_seconds
            }


class BatchProcessor:
    """Optimized batch processing for neural reranking."""
    
    def __init__(
        self,
        min_batch_size: int = 1,
        max_batch_size: int = 64,
        timeout_ms: int = 50
    ):
        """
        Initialize batch processor.
        
        Args:
            min_batch_size: Minimum batch size
            max_batch_size: Maximum batch size  
            timeout_ms: Batch timeout in milliseconds
        """
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        self.timeout_ms = timeout_ms
        
        self.stats = {
            "batches_processed": 0,
            "total_items": 0,
            "avg_batch_size": 0,
            "timeout_batches": 0
        }
    
    def optimize_batch_size(
        self,
        items: List[Any],
        target_latency_ms: int = 150
    ) -> int:
        """
        Optimize batch size based on item count and latency targets.
        
        Args:
            items: Items to process
            target_latency_ms: Target latency in milliseconds
            
        Returns:
            Optimal batch size
        """
        item_count = len(items)
        
        # Start with configured max batch size
        optimal_size = min(self.max_batch_size, item_count)
        
        # Adjust based on latency target
        if target_latency_ms < 100:
            # Very tight latency - use smaller batches
            optimal_size = min(optimal_size, 16)
        elif target_latency_ms > 300:
            # Looser latency - can use larger batches
            optimal_size = min(optimal_size, 64)
        
        # Ensure minimum batch size
        optimal_size = max(self.min_batch_size, optimal_size)
        
        return optimal_size
    
    def create_batches(
        self,
        items: List[Any],
        batch_size: Optional[int] = None
    ) -> List[List[Any]]:
        """
        Create optimized batches from items.
        
        Args:
            items: Items to batch
            batch_size: Override batch size (optional)
            
        Returns:
            List of batches
        """
        if not items:
            return []
        
        if batch_size is None:
            batch_size = self.optimize_batch_size(items)
        
        batches = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batches.append(batch)
        
        # Update statistics
        self.stats["batches_processed"] += len(batches)
        self.stats["total_items"] += len(items)
        
        if self.stats["batches_processed"] > 0:
            self.stats["avg_batch_size"] = self.stats["total_items"] / self.stats["batches_processed"]
        
        return batches
    
    def get_stats(self) -> Dict[str, Any]:
        """Get batch processing statistics."""
        return self.stats.copy()


class PerformanceOptimizer:
    """
    Performance optimizer for neural reranking.
    
    Provides caching, batch processing, and latency optimization
    to ensure neural reranking meets performance targets.
    """
    
    def __init__(
        self,
        max_latency_ms: int = 200,
        target_latency_ms: int = 150,
        enable_caching: bool = True,
        cache_ttl_seconds: int = 3600,
        max_cache_size: int = 10000,
        dynamic_batching: bool = True,
        min_batch_size: int = 1,
        max_batch_size: int = 64
    ):
        """
        Initialize performance optimizer.
        
        Args:
            max_latency_ms: Maximum allowed latency
            target_latency_ms: Target latency for optimization
            enable_caching: Whether to enable caching
            cache_ttl_seconds: Cache time-to-live
            max_cache_size: Maximum cache entries
            dynamic_batching: Whether to enable dynamic batching
            min_batch_size: Minimum batch size
            max_batch_size: Maximum batch size
        """
        self.max_latency_ms = max_latency_ms
        self.target_latency_ms = target_latency_ms
        self.enable_caching = enable_caching
        self.dynamic_batching = dynamic_batching
        
        # Initialize cache
        self.cache = LRUCache(max_cache_size, cache_ttl_seconds) if enable_caching else None
        
        # Initialize batch processor
        self.batch_processor = BatchProcessor(
            min_batch_size, max_batch_size
        ) if dynamic_batching else None
        
        self.stats = {
            "optimizations": 0,
            "cache_enabled": enable_caching,
            "batching_enabled": dynamic_batching,
            "fallbacks": 0,
            "latency_violations": 0
        }
        
        logger.info(f"PerformanceOptimizer initialized (cache={enable_caching}, batching={dynamic_batching})")
    
    def generate_cache_key(
        self,
        query: str,
        documents: List[Document],
        model_name: str
    ) -> str:
        """
        Generate cache key for query-documents-model combination.
        
        Args:
            query: Search query
            documents: List of documents
            model_name: Model name
            
        Returns:
            Cache key string
        """
        # Create a hash of query + document IDs + model name
        content = f"{query}|{model_name}"
        
        # Add document identifiers
        doc_ids = []
        for doc in documents:
            if hasattr(doc, 'id') and doc.id:
                doc_ids.append(str(doc.id))
            else:
                # Fallback to content hash
                doc_hash = hashlib.md5(doc.content.encode()).hexdigest()[:8]
                doc_ids.append(doc_hash)
        
        content += "|" + ",".join(doc_ids)
        
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_cached_scores(
        self,
        query: str,
        documents: List[Document],
        model_name: str
    ) -> Optional[List[float]]:
        """
        Get cached scores if available.
        
        Args:
            query: Search query
            documents: List of documents
            model_name: Model name
            
        Returns:
            Cached scores or None
        """
        if not self.enable_caching or not self.cache:
            return None
        
        cache_key = self.generate_cache_key(query, documents, model_name)
        return self.cache.get(cache_key)
    
    def cache_scores(
        self,
        query: str,
        documents: List[Document],
        model_name: str,
        scores: List[float]
    ):
        """
        Cache scores for future use.
        
        Args:
            query: Search query
            documents: List of documents
            model_name: Model name
            scores: Scores to cache
        """
        if not self.enable_caching or not self.cache:
            return
        
        cache_key = self.generate_cache_key(query, documents, model_name)
        self.cache.put(cache_key, scores)
    
    def optimize_batch_size(
        self,
        query_doc_pairs: List[List[str]]
    ) -> int:
        """
        Optimize batch size for processing.
        
        Args:
            query_doc_pairs: Query-document pairs
            
        Returns:
            Optimal batch size
        """
        if not self.dynamic_batching or not self.batch_processor:
            return len(query_doc_pairs)
        
        return self.batch_processor.optimize_batch_size(
            query_doc_pairs, self.target_latency_ms
        )
    
    def should_use_fallback(self, estimated_latency_ms: float) -> bool:
        """
        Determine if fallback should be used based on latency estimate.
        
        Args:
            estimated_latency_ms: Estimated processing latency
            
        Returns:
            True if fallback should be used
        """
        return estimated_latency_ms > self.max_latency_ms
    
    def record_latency(self, actual_latency_ms: float):
        """
        Record actual latency for optimization learning.
        
        Args:
            actual_latency_ms: Measured latency
        """
        if actual_latency_ms > self.max_latency_ms:
            self.stats["latency_violations"] += 1
        
        self.stats["optimizations"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance optimization statistics."""
        stats = self.stats.copy()
        
        if self.cache:
            stats["cache"] = self.cache.get_stats()
        
        if self.batch_processor:
            stats["batch_processor"] = self.batch_processor.get_stats()
        
        # Calculate performance metrics
        if self.stats["optimizations"] > 0:
            stats["latency_violation_rate"] = self.stats["latency_violations"] / self.stats["optimizations"]
        
        return stats
    
    def reset_stats(self) -> None:
        """Reset optimization statistics."""
        self.stats = {
            "optimizations": 0,
            "cache_enabled": self.enable_caching,
            "batching_enabled": self.dynamic_batching,
            "fallbacks": 0,
            "latency_violations": 0
        }