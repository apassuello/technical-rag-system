"""
In-memory embedding cache implementation.

This module provides a direct implementation of the EmbeddingCache interface
using in-memory storage with LRU eviction, content-based hashing, and
comprehensive statistics tracking.

Features:
- LRU eviction policy
- Content-based cache keys
- Memory usage monitoring
- Cache statistics and hit rate tracking
- Pattern-based invalidation
- Thread-safe operations
"""

import hashlib
import time
import fnmatch
import threading
from collections import OrderedDict
from typing import Optional, Dict, Any, List, Tuple
import numpy as np
import logging
from pathlib import Path
import sys

# Add project root for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from ..base import EmbeddingCache, ConfigurableEmbedderComponent

logger = logging.getLogger(__name__)


class MemoryCache(EmbeddingCache, ConfigurableEmbedderComponent):
    """
    Direct implementation of in-memory embedding cache.
    
    This cache uses content-based keys and LRU eviction to efficiently
    store and retrieve embeddings while managing memory usage.
    
    Configuration:
    {
        "max_entries": 100000,
        "max_memory_mb": 1024,  # Maximum memory usage in MB
        "eviction_policy": "lru",  # Currently only LRU supported
        "ttl_seconds": null,  # Time-to-live (null = no expiration)
        "normalize_keys": true,  # Normalize text before creating cache keys
        "enable_statistics": true  # Track detailed statistics
    }
    
    Performance Features:
    - Fast O(1) lookup and insertion
    - Memory-efficient storage
    - LRU eviction for optimal hit rates
    - Content-based deduplication
    - Thread-safe operations
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize memory cache.
        
        Args:
            config: Cache configuration dictionary
        """
        super().__init__(config)
        
        # Configuration
        self.max_entries = config.get("max_entries", 100000)
        self.max_memory_mb = config.get("max_memory_mb", 1024)
        self.eviction_policy = config.get("eviction_policy", "lru")
        self.ttl_seconds = config.get("ttl_seconds")
        self.normalize_keys = config.get("normalize_keys", True)
        self.enable_statistics = config.get("enable_statistics", True)
        
        # Cache storage (using OrderedDict for LRU)
        self._cache: OrderedDict[str, Tuple[np.ndarray, float]] = OrderedDict()
        self._lock = threading.RLock()  # Thread safety
        
        # Statistics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "invalidations": 0,
            "memory_bytes": 0,
            "created_time": time.time()
        }
        
        logger.info(f"MemoryCache initialized: max_entries={self.max_entries}, max_memory={self.max_memory_mb}MB")
    
    def _validate_config(self) -> None:
        """
        Validate cache configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate max_entries
        max_entries = self.config.get("max_entries", 100000)
        if not isinstance(max_entries, int) or max_entries < 1:
            raise ValueError("max_entries must be a positive integer")
        
        # Validate max_memory_mb
        max_memory = self.config.get("max_memory_mb", 1024)
        if not isinstance(max_memory, (int, float)) or max_memory <= 0:
            raise ValueError("max_memory_mb must be a positive number")
        
        # Validate eviction_policy
        eviction_policy = self.config.get("eviction_policy", "lru")
        if eviction_policy != "lru":
            raise ValueError("Only 'lru' eviction policy is currently supported")
        
        # Validate TTL
        ttl = self.config.get("ttl_seconds")
        if ttl is not None and (not isinstance(ttl, (int, float)) or ttl <= 0):
            raise ValueError("ttl_seconds must be a positive number or null")
    
    def _create_cache_key(self, text: str) -> str:
        """
        Create a cache key from text content.
        
        Args:
            text: Text to create key for
            
        Returns:
            Cache key string
        """
        # Normalize text if configured
        if self.normalize_keys:
            # Basic normalization: strip whitespace, lowercase
            normalized_text = text.strip().lower()
        else:
            normalized_text = text
        
        # Create content-based hash
        content_hash = hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()
        return f"embedding:{content_hash[:16]}"  # Truncate for efficiency
    
    def _is_expired(self, timestamp: float) -> bool:
        """
        Check if a cache entry is expired.
        
        Args:
            timestamp: Entry creation timestamp
            
        Returns:
            True if expired, False otherwise
        """
        if self.ttl_seconds is None:
            return False
        
        return (time.time() - timestamp) > self.ttl_seconds
    
    def _estimate_memory_usage(self, embedding: np.ndarray) -> int:
        """
        Estimate memory usage of an embedding.
        
        Args:
            embedding: Embedding array
            
        Returns:
            Estimated memory usage in bytes
        """
        # numpy array memory + overhead
        array_bytes = embedding.nbytes
        overhead_bytes = 64  # Approximate overhead for key, timestamp, etc.
        return array_bytes + overhead_bytes
    
    def _evict_if_necessary(self) -> None:
        """Evict entries if cache limits are exceeded."""
        # Check entry count limit
        while len(self._cache) >= self.max_entries:
            self._evict_lru_entry()
        
        # Check memory limit
        max_memory_bytes = self.max_memory_mb * 1024 * 1024
        while self._stats["memory_bytes"] > max_memory_bytes and self._cache:
            self._evict_lru_entry()
    
    def _evict_lru_entry(self) -> None:
        """Evict the least recently used entry."""
        if not self._cache:
            return
        
        # Remove oldest entry (LRU)
        key, (embedding, _) = self._cache.popitem(last=False)
        
        # Update memory usage
        memory_freed = self._estimate_memory_usage(embedding)
        self._stats["memory_bytes"] -= memory_freed
        self._stats["evictions"] += 1
        
        logger.debug(f"Evicted cache entry: {key}, memory freed: {memory_freed} bytes")
    
    def get(self, text: str) -> Optional[np.ndarray]:
        """
        Retrieve cached embedding for text.
        
        Args:
            text: Text string to look up
            
        Returns:
            Cached embedding array or None if not found
            
        Raises:
            RuntimeError: If cache retrieval fails
        """
        cache_key = self._create_cache_key(text)
        
        with self._lock:
            try:
                if cache_key in self._cache:
                    embedding, timestamp = self._cache[cache_key]
                    
                    # Check expiration
                    if self._is_expired(timestamp):
                        # Remove expired entry
                        del self._cache[cache_key]
                        memory_freed = self._estimate_memory_usage(embedding)
                        self._stats["memory_bytes"] -= memory_freed
                        
                        if self.enable_statistics:
                            self._stats["misses"] += 1
                        
                        return None
                    
                    # Move to end (most recently used)
                    self._cache.move_to_end(cache_key)
                    
                    if self.enable_statistics:
                        self._stats["hits"] += 1
                    
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return embedding.copy()  # Return copy to prevent modification
                
                else:
                    if self.enable_statistics:
                        self._stats["misses"] += 1
                    
                    logger.debug(f"Cache miss for key: {cache_key}")
                    return None
                    
            except Exception as e:
                raise RuntimeError(f"Cache retrieval failed for key '{cache_key}': {e}") from e
    
    def put(self, text: str, embedding: np.ndarray) -> None:
        """
        Store embedding in cache.
        
        Args:
            text: Text string as cache key
            embedding: Embedding array to store
            
        Raises:
            ValueError: If text or embedding is invalid
            RuntimeError: If cache storage fails
        """
        if not text or not text.strip():
            raise ValueError("Text key cannot be empty")
        
        if embedding is None or embedding.size == 0:
            raise ValueError("Embedding cannot be empty")
        
        cache_key = self._create_cache_key(text)
        current_time = time.time()
        
        with self._lock:
            try:
                # Estimate memory usage
                memory_needed = self._estimate_memory_usage(embedding)
                
                # Remove existing entry if present
                if cache_key in self._cache:
                    old_embedding, _ = self._cache[cache_key]
                    old_memory = self._estimate_memory_usage(old_embedding)
                    self._stats["memory_bytes"] -= old_memory
                
                # Evict if necessary before adding
                self._evict_if_necessary()
                
                # Store new entry
                self._cache[cache_key] = (embedding.copy(), current_time)
                self._stats["memory_bytes"] += memory_needed
                
                logger.debug(f"Cached embedding for key: {cache_key}, size: {memory_needed} bytes")
                
            except Exception as e:
                raise RuntimeError(f"Cache storage failed for key '{cache_key}': {e}") from e
    
    def invalidate(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern.
        
        Args:
            pattern: Pattern to match for invalidation (supports wildcards)
            
        Returns:
            Number of entries invalidated
            
        Raises:
            RuntimeError: If invalidation fails
        """
        with self._lock:
            try:
                keys_to_remove = []
                
                # Find matching keys
                for key in self._cache.keys():
                    if fnmatch.fnmatch(key, pattern):
                        keys_to_remove.append(key)
                
                # Remove matching entries
                invalidated_count = 0
                for key in keys_to_remove:
                    if key in self._cache:
                        embedding, _ = self._cache[key]
                        memory_freed = self._estimate_memory_usage(embedding)
                        self._stats["memory_bytes"] -= memory_freed
                        del self._cache[key]
                        invalidated_count += 1
                
                if self.enable_statistics:
                    self._stats["invalidations"] += invalidated_count
                
                logger.info(f"Invalidated {invalidated_count} cache entries matching pattern: {pattern}")
                return invalidated_count
                
            except Exception as e:
                raise RuntimeError(f"Cache invalidation failed for pattern '{pattern}': {e}") from e
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        
        Returns:
            Dictionary with hit rate, size, evictions, etc.
        """
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0.0
            
            return {
                "size": len(self._cache),
                "max_entries": self.max_entries,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_rate": hit_rate,
                "evictions": self._stats["evictions"],
                "invalidations": self._stats["invalidations"],
                "memory_bytes": self._stats["memory_bytes"],
                "memory_mb": self._stats["memory_bytes"] / (1024 * 1024),
                "max_memory_mb": self.max_memory_mb,
                "memory_usage_percent": (self._stats["memory_bytes"] / (self.max_memory_mb * 1024 * 1024)) * 100,
                "uptime_seconds": time.time() - self._stats["created_time"],
                "ttl_seconds": self.ttl_seconds,
                "eviction_policy": self.eviction_policy
            }
    
    def clear(self) -> None:
        """
        Clear all entries from the cache.
        
        Raises:
            RuntimeError: If cache clearing fails
        """
        with self._lock:
            try:
                self._cache.clear()
                self._stats["memory_bytes"] = 0
                logger.info("Cache cleared")
                
            except Exception as e:
                raise RuntimeError(f"Cache clearing failed: {e}") from e
    
    def get_cache_size(self) -> int:
        """
        Get current number of cached entries.
        
        Returns:
            Number of entries currently in cache
        """
        with self._lock:
            return len(self._cache)
    
    def get_memory_info(self) -> Dict[str, Any]:
        """
        Get detailed memory usage information.
        
        Returns:
            Dictionary with memory statistics
        """
        with self._lock:
            return {
                "current_memory_bytes": self._stats["memory_bytes"],
                "current_memory_mb": self._stats["memory_bytes"] / (1024 * 1024),
                "max_memory_mb": self.max_memory_mb,
                "memory_efficiency": self._stats["memory_bytes"] / len(self._cache) if self._cache else 0,
                "average_embedding_size": self._stats["memory_bytes"] / len(self._cache) if self._cache else 0
            }
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.
        
        Returns:
            Number of expired entries removed
        """
        if self.ttl_seconds is None:
            return 0
        
        with self._lock:
            current_time = time.time()
            expired_keys = []
            
            for key, (embedding, timestamp) in self._cache.items():
                if self._is_expired(timestamp):
                    expired_keys.append(key)
            
            # Remove expired entries
            for key in expired_keys:
                if key in self._cache:
                    embedding, _ = self._cache[key]
                    memory_freed = self._estimate_memory_usage(embedding)
                    self._stats["memory_bytes"] -= memory_freed
                    del self._cache[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)