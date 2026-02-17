"""
Model Cache with LRU Eviction and Memory Pressure Handling.

This module provides intelligent caching for ML models with memory-aware
eviction policies and performance optimization features.

Key Features:
- LRU-based eviction policy
- Memory pressure-based intelligent eviction
- Cache hit/miss statistics and monitoring
- Thread-safe operations
- Configurable cache warming strategies
"""

import logging
import threading
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, List, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheStats:
    """Cache performance statistics."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    memory_evictions: int = 0
    total_requests: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests

    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate."""
        return 1.0 - self.hit_rate


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with metadata."""

    key: str
    value: T
    access_time: float = field(default_factory=time.time)
    creation_time: float = field(default_factory=time.time)
    access_count: int = 0
    memory_size_mb: Optional[float] = None

    def update_access(self) -> None:
        """Update access statistics."""
        self.access_time = time.time()
        self.access_count += 1


class ModelCache(Generic[T]):
    """
    LRU cache with memory pressure handling for ML models.

    This cache implements intelligent eviction policies that consider both
    access patterns and memory usage to optimize model loading performance
    while staying within memory budgets.
    """

    def __init__(
        self,
        maxsize: int = 10,
        memory_threshold_mb: float = 1500,
        enable_stats: bool = True,
        warmup_enabled: bool = False
    ):
        """
        Initialize model cache.

        Args:
            maxsize: Maximum number of cached items
            memory_threshold_mb: Memory threshold for pressure-based eviction
            enable_stats: Whether to track performance statistics
            warmup_enabled: Whether to enable background cache warming
        """
        self.maxsize = maxsize
        self.memory_threshold_mb = memory_threshold_mb
        self.enable_stats = enable_stats
        self.warmup_enabled = warmup_enabled

        # Thread-safe cache storage
        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self._lock = threading.RLock()

        # Statistics tracking
        self._stats = CacheStats() if enable_stats else None

        # Memory monitoring integration
        self._memory_monitor = None

        # Warmup configuration
        self._warmup_executor = None
        self._warmup_queue = []

        logger.info(f"Initialized ModelCache: maxsize={maxsize}, "
                   f"memory_threshold={memory_threshold_mb}MB, "
                   f"stats_enabled={enable_stats}")

    def set_memory_monitor(self, memory_monitor) -> None:
        """Set memory monitor for intelligent eviction."""
        self._memory_monitor = memory_monitor
        logger.debug("Memory monitor attached to cache")

    def get(self, key: str) -> Optional[T]:
        """
        Get item from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                entry.update_access()

                # Move to end (most recently used)
                self._cache.move_to_end(key)

                if self._stats:
                    self._stats.hits += 1
                    self._stats.total_requests += 1

                logger.debug(f"Cache HIT for key '{key}'")
                return entry.value
            else:
                if self._stats:
                    self._stats.misses += 1
                    self._stats.total_requests += 1

                logger.debug(f"Cache MISS for key '{key}'")
                return None

    def put(self, key: str, value: T, memory_size_mb: Optional[float] = None) -> None:
        """
        Put item in cache with intelligent eviction.

        Args:
            key: Cache key
            value: Value to cache
            memory_size_mb: Memory size of the value in MB
        """
        with self._lock:
            # Check if we need to evict before adding
            self._ensure_space_for_new_entry(memory_size_mb or 0)

            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                memory_size_mb=memory_size_mb
            )

            # Add to cache
            self._cache[key] = entry

            # Move to end (most recently used)
            self._cache.move_to_end(key)

            logger.debug(f"Cache PUT for key '{key}' (size: {memory_size_mb:.1f}MB)"
                        if memory_size_mb else f"Cache PUT for key '{key}'")

    def _ensure_space_for_new_entry(self, required_memory_mb: float) -> None:
        """Ensure there's space for a new entry."""
        # Size-based eviction
        while len(self._cache) >= self.maxsize:
            self._evict_lru()

        # Memory-based eviction if memory monitor is available
        if self._memory_monitor and required_memory_mb > 0:
            current_memory = self._memory_monitor.get_epic1_memory_usage()

            while (current_memory + required_memory_mb > self.memory_threshold_mb
                   and self._cache):
                evicted_memory = self._evict_lru()
                if evicted_memory:
                    current_memory -= evicted_memory
                    if self._stats:
                        self._stats.memory_evictions += 1
                else:
                    break  # No more entries to evict

    def _evict_lru(self) -> Optional[float]:
        """
        Evict least recently used item.

        Returns:
            Memory size of evicted item in MB, or None if nothing evicted
        """
        if not self._cache:
            return None

        # Get LRU item (first in OrderedDict)
        key, entry = self._cache.popitem(last=False)

        if self._stats:
            self._stats.evictions += 1

        logger.debug(f"Evicted LRU item: '{key}' (size: {entry.memory_size_mb:.1f}MB)"
                    if entry.memory_size_mb else f"Evicted LRU item: '{key}'")

        return entry.memory_size_mb

    def evict(self, key: str) -> bool:
        """
        Manually evict specific item.

        Args:
            key: Key to evict

        Returns:
            True if item was evicted, False if not found
        """
        with self._lock:
            if key in self._cache:
                entry = self._cache.pop(key)

                if self._stats:
                    self._stats.evictions += 1

                logger.debug(f"Manually evicted: '{key}' (size: {entry.memory_size_mb:.1f}MB)"
                           if entry.memory_size_mb else f"Manually evicted: '{key}'")
                return True

            return False

    def clear(self) -> None:
        """Clear all cached items."""
        with self._lock:
            evicted_count = len(self._cache)
            self._cache.clear()

            if self._stats:
                self._stats.evictions += evicted_count

            logger.info(f"Cleared cache: evicted {evicted_count} items")

    def get_stats(self) -> Optional[CacheStats]:
        """Get cache performance statistics."""
        if self._stats:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                memory_evictions=self._stats.memory_evictions,
                total_requests=self._stats.total_requests
            )
        return None

    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information."""
        with self._lock:
            total_memory_mb = sum(
                entry.memory_size_mb or 0
                for entry in self._cache.values()
            )

            entries_info = [
                {
                    'key': entry.key,
                    'memory_mb': entry.memory_size_mb,
                    'access_count': entry.access_count,
                    'age_seconds': time.time() - entry.creation_time,
                    'last_access_seconds_ago': time.time() - entry.access_time
                }
                for entry in self._cache.values()
            ]

            return {
                'size': len(self._cache),
                'maxsize': self.maxsize,
                'total_memory_mb': total_memory_mb,
                'memory_threshold_mb': self.memory_threshold_mb,
                'entries': entries_info,
                'stats': self.get_stats().__dict__ if self._stats else None
            }

    def enable_warmup(self, warmup_keys: List[str], warmup_loader_func) -> None:
        """
        Enable cache warming with background loading.

        Args:
            warmup_keys: List of keys to warm up
            warmup_loader_func: Function to load values for warmup
        """
        if not self.warmup_enabled:
            logger.warning("Cache warmup not enabled during initialization")
            return

        self._warmup_queue = warmup_keys.copy()

        if not self._warmup_executor:
            self._warmup_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="cache-warmup")

        # Start warmup process (fire-and-forget; executor keeps a reference)
        self._warmup_executor.submit(self._warmup_worker, warmup_loader_func)
        logger.info(f"Started cache warmup for {len(warmup_keys)} keys")

    def _warmup_worker(self, loader_func) -> None:
        """Background worker for cache warming."""
        for key in self._warmup_queue:
            if key not in self._cache:  # Only load if not already cached
                try:
                    value = loader_func(key)
                    if value is not None:
                        # Estimate memory size if possible
                        memory_size = getattr(value, 'memory_size_mb', None)
                        self.put(key, value, memory_size)
                        logger.debug(f"Warmed up cache for key: '{key}'")
                except Exception as e:
                    logger.warning(f"Failed to warm up cache for key '{key}': {e}")

            # Small delay to avoid overwhelming the system
            time.sleep(0.1)

        logger.info("Cache warmup completed")

    def log_performance_summary(self) -> None:
        """Log cache performance summary."""
        if not self._stats:
            logger.info("Cache statistics not enabled")
            return

        info = self.get_cache_info()
        stats = self._stats

        logger.info(
            f"Cache Performance Summary:\n"
            f"  Size: {info['size']}/{info['maxsize']}\n"
            f"  Hit Rate: {stats.hit_rate:.2%} ({stats.hits}/{stats.total_requests})\n"
            f"  Evictions: {stats.evictions} (memory-based: {stats.memory_evictions})\n"
            f"  Total Memory: {info['total_memory_mb']:.1f}MB / {info['memory_threshold_mb']:.1f}MB"
        )

    def __contains__(self, key: str) -> bool:
        """Check if key is in cache."""
        with self._lock:
            return key in self._cache

    def __len__(self) -> int:
        """Get number of cached items."""
        with self._lock:
            return len(self._cache)

    def __enter__(self) -> 'ModelCache':
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        if self._warmup_executor:
            self._warmup_executor.shutdown(wait=False)
