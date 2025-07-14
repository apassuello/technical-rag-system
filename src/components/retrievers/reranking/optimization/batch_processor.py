"""
Optimized Batch Processor for Neural Reranking.

This module provides advanced batch processing strategies for neural reranking
to optimize throughput and latency while maintaining quality, including
dynamic batching, memory management, and adaptive sizing.
"""

import time
import logging
from typing import List, Dict, Any, Tuple, Optional, Union
from collections import deque
from dataclasses import dataclass
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class BatchRequest:
    """A batch processing request."""
    request_id: str
    query: str
    documents: List[str]
    initial_scores: List[float]
    timestamp: float
    priority: int = 0
    callback: Optional[callable] = None


@dataclass
class BatchResult:
    """Result from batch processing."""
    request_id: str
    scores: List[float]
    processing_time: float
    batch_size: int
    queue_time: float


class OptimizedBatchProcessor:
    """
    Advanced batch processor for neural reranking optimization.
    
    This processor implements sophisticated batching strategies to optimize
    neural reranking performance including:
    - Dynamic batch sizing based on load and latency targets
    - Adaptive queuing with timeout handling
    - Memory-aware processing
    - Priority-based request handling
    - Concurrent batch processing
    """
    
    def __init__(self,
                 min_batch_size: int = 1,
                 max_batch_size: int = 32,
                 target_latency_ms: float = 100.0,
                 max_queue_time_ms: float = 50.0,
                 memory_limit_mb: float = 512.0,
                 num_workers: int = 2):
        """
        Initialize optimized batch processor.
        
        Args:
            min_batch_size: Minimum batch size for processing
            max_batch_size: Maximum batch size for processing
            target_latency_ms: Target processing latency
            max_queue_time_ms: Maximum time to wait in queue
            memory_limit_mb: Memory limit for batch processing
            num_workers: Number of worker threads for processing
        """
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        self.target_latency_ms = target_latency_ms
        self.max_queue_time_ms = max_queue_time_ms
        self.memory_limit_mb = memory_limit_mb
        self.num_workers = num_workers
        
        # Request queue and processing
        self.request_queue = deque()
        self.processing_stats = {
            "total_requests": 0,
            "total_batches": 0,
            "total_processing_time": 0.0,
            "total_queue_time": 0.0,
            "batch_size_history": deque(maxlen=100),
            "latency_history": deque(maxlen=100),
            "throughput_history": deque(maxlen=100),
        }
        
        # Adaptive parameters
        self.current_batch_size = min_batch_size
        self.adaptive_enabled = True
        self.adaptation_window = 10  # Number of batches for adaptation
        
        # Threading and synchronization
        self.executor = ThreadPoolExecutor(max_workers=num_workers)
        self.queue_lock = threading.Lock()
        self.running = False
        self.processor_thread: Optional[threading.Thread] = None
        
        # Memory management
        self.memory_usage_mb = 0.0
        self.memory_monitor_enabled = True
        
        logger.info(f"OptimizedBatchProcessor initialized with batch_size={min_batch_size}-{max_batch_size}")
    
    def start(self) -> None:
        """Start the batch processor."""
        if self.running:
            logger.warning("Batch processor already running")
            return
        
        self.running = True
        self.processor_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processor_thread.start()
        
        logger.info("Batch processor started")
    
    def stop(self) -> None:
        """Stop the batch processor."""
        self.running = False
        
        if self.processor_thread and self.processor_thread.is_alive():
            self.processor_thread.join(timeout=5.0)
        
        self.executor.shutdown(wait=True)
        
        logger.info("Batch processor stopped")
    
    def submit_request(self,
                      request_id: str,
                      query: str,
                      documents: List[str],
                      initial_scores: List[float],
                      priority: int = 0,
                      callback: Optional[callable] = None) -> Optional[BatchResult]:
        """
        Submit a request for batch processing.
        
        Args:
            request_id: Unique identifier for the request
            query: Search query
            documents: List of document texts
            initial_scores: Initial retrieval scores
            priority: Request priority (higher = more important)
            callback: Optional callback for async processing
            
        Returns:
            Batch result if processed synchronously, None if async
        """
        request = BatchRequest(
            request_id=request_id,
            query=query,
            documents=documents,
            initial_scores=initial_scores,
            timestamp=time.time(),
            priority=priority,
            callback=callback
        )
        
        # Add to queue
        with self.queue_lock:
            # Insert based on priority
            inserted = False
            for i, existing_request in enumerate(self.request_queue):
                if request.priority > existing_request.priority:
                    self.request_queue.insert(i, request)
                    inserted = True
                    break
            
            if not inserted:
                self.request_queue.append(request)
        
        # If synchronous (no callback), wait for result
        if callback is None:
            return self._wait_for_result(request_id)
        
        return None
    
    def _processing_loop(self) -> None:
        """Main processing loop for batch handling."""
        while self.running:
            try:
                # Check if we should process a batch
                if self._should_process_batch():
                    batch = self._create_batch()
                    if batch:
                        self._process_batch(batch)
                
                # Brief sleep to prevent busy waiting
                time.sleep(0.001)  # 1ms
                
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                time.sleep(0.1)  # Longer sleep on error
    
    def _should_process_batch(self) -> bool:
        """Determine if a batch should be processed now."""
        with self.queue_lock:
            queue_size = len(self.request_queue)
            
            if queue_size == 0:
                return False
            
            # Check if we have minimum batch size
            if queue_size >= self.current_batch_size:
                return True
            
            # Check if oldest request is approaching timeout
            if self.request_queue:
                oldest_request = self.request_queue[0]
                queue_time = (time.time() - oldest_request.timestamp) * 1000
                
                if queue_time >= self.max_queue_time_ms:
                    return True
            
            return False
    
    def _create_batch(self) -> List[BatchRequest]:
        """Create a batch from queued requests."""
        batch = []
        
        with self.queue_lock:
            # Take up to current_batch_size requests
            batch_size = min(self.current_batch_size, len(self.request_queue))
            
            for _ in range(batch_size):
                if self.request_queue:
                    batch.append(self.request_queue.popleft())
        
        return batch
    
    def _process_batch(self, batch: List[BatchRequest]) -> None:
        """Process a batch of requests."""
        if not batch:
            return
        
        start_time = time.time()
        batch_size = len(batch)
        
        try:
            # Prepare batch data
            queries = [req.query for req in batch]
            all_documents = [req.documents for req in batch]
            all_initial_scores = [req.initial_scores for req in batch]
            
            # Process batch (placeholder - in practice, call neural model)
            batch_scores = self._process_neural_batch(queries, all_documents, all_initial_scores)
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000
            
            # Create results for each request
            for i, request in enumerate(batch):
                queue_time = (start_time - request.timestamp) * 1000
                
                result = BatchResult(
                    request_id=request.request_id,
                    scores=batch_scores[i] if i < len(batch_scores) else request.initial_scores,
                    processing_time=processing_time,
                    batch_size=batch_size,
                    queue_time=queue_time
                )
                
                # Handle result (callback or store for sync requests)
                if request.callback:
                    try:
                        request.callback(result)
                    except Exception as e:
                        logger.error(f"Callback failed for request {request.request_id}: {e}")
                else:
                    # Store for synchronous retrieval
                    self._store_result(result)
            
            # Update statistics
            self._update_stats(batch_size, processing_time, [
                (start_time - req.timestamp) * 1000 for req in batch
            ])
            
            # Adapt batch size if enabled
            if self.adaptive_enabled:
                self._adapt_batch_size(processing_time, batch_size)
            
            logger.debug(f"Processed batch of {batch_size} requests in {processing_time:.1f}ms")
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            
            # Return original scores for failed requests
            for request in batch:
                result = BatchResult(
                    request_id=request.request_id,
                    scores=request.initial_scores,
                    processing_time=0.0,
                    batch_size=batch_size,
                    queue_time=(time.time() - request.timestamp) * 1000
                )
                
                if request.callback:
                    request.callback(result)
                else:
                    self._store_result(result)
    
    def _process_neural_batch(self,
                            queries: List[str],
                            all_documents: List[List[str]],
                            all_initial_scores: List[List[float]]) -> List[List[float]]:
        """
        Process a batch through neural reranking model.
        
        This is a placeholder implementation. In practice, this would:
        1. Prepare query-document pairs for the batch
        2. Run neural model inference
        3. Apply score fusion
        4. Return reranked scores
        
        Args:
            queries: List of queries
            all_documents: List of document lists (one per query)
            all_initial_scores: List of initial score lists
            
        Returns:
            List of reranked scores for each query
        """
        # Placeholder implementation - simulate neural processing
        batch_scores = []
        
        for i, (query, documents, initial_scores) in enumerate(zip(queries, all_documents, all_initial_scores)):
            # Simulate neural reranking by slightly modifying scores
            neural_scores = []
            for j, (doc, score) in enumerate(zip(documents, initial_scores)):
                # Simple simulation: boost scores based on query-doc similarity
                boost = 0.1 * (j % 2)  # Alternate boost pattern
                neural_score = min(1.0, score + boost)
                neural_scores.append(neural_score)
            
            batch_scores.append(neural_scores)
        
        # Simulate processing time
        time.sleep(0.01)  # 10ms simulation
        
        return batch_scores
    
    def _adapt_batch_size(self, processing_time: float, batch_size: int) -> None:
        """Adapt batch size based on performance metrics."""
        if len(self.processing_stats["latency_history"]) < self.adaptation_window:
            return
        
        # Calculate recent average latency
        recent_latencies = list(self.processing_stats["latency_history"])[-self.adaptation_window:]
        avg_latency = np.mean(recent_latencies)
        
        # Adapt batch size based on latency vs target
        if avg_latency > self.target_latency_ms * 1.2:  # 20% over target
            # Decrease batch size if latency is too high
            new_batch_size = max(self.min_batch_size, self.current_batch_size - 1)
        elif avg_latency < self.target_latency_ms * 0.8:  # 20% under target
            # Increase batch size if latency is acceptable
            new_batch_size = min(self.max_batch_size, self.current_batch_size + 1)
        else:
            # Keep current batch size
            new_batch_size = self.current_batch_size
        
        if new_batch_size != self.current_batch_size:
            logger.debug(f"Adapting batch size: {self.current_batch_size} -> {new_batch_size} "
                        f"(avg_latency: {avg_latency:.1f}ms)")
            self.current_batch_size = new_batch_size
    
    def _update_stats(self,
                     batch_size: int,
                     processing_time: float,
                     queue_times: List[float]) -> None:
        """Update processing statistics."""
        self.processing_stats["total_requests"] += batch_size
        self.processing_stats["total_batches"] += 1
        self.processing_stats["total_processing_time"] += processing_time
        self.processing_stats["total_queue_time"] += sum(queue_times)
        
        self.processing_stats["batch_size_history"].append(batch_size)
        self.processing_stats["latency_history"].append(processing_time)
        
        # Calculate throughput (requests per second)
        if processing_time > 0:
            throughput = (batch_size / processing_time) * 1000  # Convert ms to seconds
            self.processing_stats["throughput_history"].append(throughput)
    
    def _store_result(self, result: BatchResult) -> None:
        """Store result for synchronous requests."""
        # In practice, you'd use a proper result store (Redis, memory cache, etc.)
        # For now, this is a placeholder
        pass
    
    def _wait_for_result(self, request_id: str, timeout: float = 5.0) -> Optional[BatchResult]:
        """Wait for a synchronous request result."""
        # Placeholder implementation
        # In practice, you'd wait for the result to be available in the result store
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            # Check if result is available (placeholder)
            time.sleep(0.01)  # 10ms polling
            
            # For now, return a dummy result after short wait
            if (time.time() - start_time) > 0.1:  # 100ms
                return BatchResult(
                    request_id=request_id,
                    scores=[],
                    processing_time=100.0,
                    batch_size=1,
                    queue_time=50.0
                )
        
        logger.warning(f"Request {request_id} timed out")
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get batch processing statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        stats = self.processing_stats.copy()
        
        # Calculate derived metrics
        if stats["total_batches"] > 0:
            stats["avg_batch_size"] = stats["total_requests"] / stats["total_batches"]
            stats["avg_processing_time"] = stats["total_processing_time"] / stats["total_batches"]
        else:
            stats["avg_batch_size"] = 0.0
            stats["avg_processing_time"] = 0.0
        
        if stats["total_requests"] > 0:
            stats["avg_queue_time"] = stats["total_queue_time"] / stats["total_requests"]
        else:
            stats["avg_queue_time"] = 0.0
        
        # Recent performance metrics
        if stats["latency_history"]:
            recent_latencies = list(stats["latency_history"])[-10:]  # Last 10 batches
            stats["recent_avg_latency"] = np.mean(recent_latencies)
            stats["recent_p95_latency"] = np.percentile(recent_latencies, 95)
        
        if stats["throughput_history"]:
            recent_throughput = list(stats["throughput_history"])[-10:]
            stats["recent_avg_throughput"] = np.mean(recent_throughput)
        
        # Configuration
        stats["config"] = {
            "min_batch_size": self.min_batch_size,
            "max_batch_size": self.max_batch_size,
            "current_batch_size": self.current_batch_size,
            "target_latency_ms": self.target_latency_ms,
            "max_queue_time_ms": self.max_queue_time_ms,
            "memory_limit_mb": self.memory_limit_mb,
            "num_workers": self.num_workers,
            "adaptive_enabled": self.adaptive_enabled
        }
        
        # Current status
        with self.queue_lock:
            stats["current_queue_size"] = len(self.request_queue)
        
        stats["running"] = self.running
        
        return stats
    
    def reset_stats(self) -> None:
        """Reset processing statistics."""
        self.processing_stats = {
            "total_requests": 0,
            "total_batches": 0,
            "total_processing_time": 0.0,
            "total_queue_time": 0.0,
            "batch_size_history": deque(maxlen=100),
            "latency_history": deque(maxlen=100),
            "throughput_history": deque(maxlen=100),
        }
        
        logger.info("Batch processing statistics reset")
    
    def set_adaptive_parameters(self,
                               target_latency_ms: Optional[float] = None,
                               max_queue_time_ms: Optional[float] = None,
                               adaptive_enabled: Optional[bool] = None) -> None:
        """
        Update adaptive processing parameters.
        
        Args:
            target_latency_ms: New target latency
            max_queue_time_ms: New maximum queue time
            adaptive_enabled: Enable/disable adaptive batching
        """
        if target_latency_ms is not None:
            self.target_latency_ms = target_latency_ms
        
        if max_queue_time_ms is not None:
            self.max_queue_time_ms = max_queue_time_ms
        
        if adaptive_enabled is not None:
            self.adaptive_enabled = adaptive_enabled
        
        logger.info(f"Updated adaptive parameters: target_latency={self.target_latency_ms}ms, "
                   f"max_queue_time={self.max_queue_time_ms}ms, adaptive={self.adaptive_enabled}")
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()