"""
Dynamic batch processor for optimized embedding generation.

This module provides a direct implementation of the BatchProcessor interface
that dynamically optimizes batch sizes based on available hardware and
text characteristics for maximum throughput.

Features:
- Dynamic batch size optimization
- Hardware-aware processing
- Memory usage monitoring  
- Performance statistics tracking
- Streaming support for large datasets
"""

import time
import numpy as np
from typing import List, Dict, Any, Optional, Iterator, Tuple
import logging
import psutil
import torch
from pathlib import Path
import sys

# Add project root for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from ..base import BatchProcessor, ConfigurableEmbedderComponent, EmbeddingModel

logger = logging.getLogger(__name__)


class DynamicBatchProcessor(BatchProcessor, ConfigurableEmbedderComponent):
    """
    Direct implementation of dynamic batch processing for embeddings.
    
    This processor automatically optimizes batch sizes based on:
    - Available GPU/MPS memory
    - Text length characteristics
    - Hardware performance profiles
    - Memory usage patterns
    
    Configuration:
    {
        "initial_batch_size": 32,
        "max_batch_size": 128,
        "min_batch_size": 1,
        "memory_threshold": 0.8,  # Fraction of available memory to use
        "optimize_for_memory": true,
        "enable_streaming": true,
        "performance_history_size": 100
    }
    
    Performance Features:
    - Adaptive batch sizing based on memory and performance
    - Memory monitoring to prevent OOM errors
    - Performance history tracking for optimization
    - Streaming support for large text lists
    """
    
    def __init__(self, config: Dict[str, Any], embedding_model: EmbeddingModel):
        """
        Initialize dynamic batch processor.
        
        Args:
            config: Batch processor configuration
            embedding_model: The embedding model to process batches for
        """
        super().__init__(config)
        
        self.embedding_model = embedding_model
        
        # Configuration
        self.initial_batch_size = config.get("initial_batch_size", 32)
        self.max_batch_size = config.get("max_batch_size", 128)
        self.min_batch_size = config.get("min_batch_size", 1)
        self.memory_threshold = config.get("memory_threshold", 0.8)
        self.optimize_for_memory = config.get("optimize_for_memory", True)
        self.enable_streaming = config.get("enable_streaming", True)
        self.performance_history_size = config.get("performance_history_size", 100)
        
        # State tracking
        self.current_batch_size = self.initial_batch_size
        self.performance_history: List[Dict[str, float]] = []
        self._total_texts_processed = 0
        self._total_processing_time = 0.0
        self._last_optimization_time = 0.0
        
        logger.info(f"DynamicBatchProcessor initialized: batch_size={self.initial_batch_size}, max={self.max_batch_size}")
    
    def _validate_config(self) -> None:
        """
        Validate batch processor configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate batch sizes
        if self.config.get("min_batch_size", 1) < 1:
            raise ValueError("min_batch_size must be >= 1")
        
        max_batch = self.config.get("max_batch_size", 128)
        min_batch = self.config.get("min_batch_size", 1)
        initial_batch = self.config.get("initial_batch_size", 32)
        
        if max_batch < min_batch:
            raise ValueError("max_batch_size must be >= min_batch_size")
        
        if initial_batch < min_batch or initial_batch > max_batch:
            raise ValueError("initial_batch_size must be between min_batch_size and max_batch_size")
        
        # Validate memory threshold
        memory_threshold = self.config.get("memory_threshold", 0.8)
        if not 0.1 <= memory_threshold <= 1.0:
            raise ValueError("memory_threshold must be between 0.1 and 1.0")
    
    def process_batch(self, texts: List[str], batch_size: int) -> np.ndarray:
        """
        Process texts in batches for optimal throughput.
        
        Args:
            texts: List of text strings to process
            batch_size: Size of each processing batch (will be optimized)
            
        Returns:
            numpy array of embeddings with shape (len(texts), embedding_dim)
            
        Raises:
            ValueError: If texts list is empty
            RuntimeError: If batch processing fails
        """
        if not texts:
            raise ValueError("Cannot process empty text list")
        
        start_time = time.time()
        
        try:
            # Use optimized batch size instead of provided one
            optimal_batch_size = self._get_optimal_batch_size(texts, batch_size)
            
            if len(texts) <= optimal_batch_size:
                # Process all texts in single batch
                embeddings = self.embedding_model.encode(texts)
            else:
                # Process in multiple batches
                embeddings = self._process_in_batches(texts, optimal_batch_size)
            
            # Update performance tracking
            processing_time = time.time() - start_time
            self._update_performance_stats(len(texts), processing_time, optimal_batch_size)
            
            return embeddings
            
        except Exception as e:
            raise RuntimeError(f"Batch processing failed: {e}") from e
    
    def _process_in_batches(self, texts: List[str], batch_size: int) -> np.ndarray:
        """
        Process texts in multiple batches.
        
        Args:
            texts: List of texts to process
            batch_size: Size of each batch
            
        Returns:
            Combined embeddings array
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Monitor memory usage
            if self.optimize_for_memory:
                self._check_memory_usage()
            
            batch_embeddings = self.embedding_model.encode(batch)
            all_embeddings.append(batch_embeddings)
        
        # Combine all embeddings
        return np.vstack(all_embeddings)
    
    def _get_optimal_batch_size(self, texts: List[str], requested_size: int) -> int:
        """
        Determine optimal batch size based on texts and performance history.
        
        Args:
            texts: Sample texts to analyze
            requested_size: Originally requested batch size
            
        Returns:
            Optimized batch size
        """
        # Start with current optimized size
        optimal_size = min(self.current_batch_size, requested_size, self.max_batch_size)
        
        # Adjust based on text characteristics
        if texts:
            avg_text_length = sum(len(text) for text in texts[:10]) / min(len(texts), 10)
            
            # Reduce batch size for very long texts
            if avg_text_length > 1000:
                optimal_size = max(optimal_size // 2, self.min_batch_size)
            elif avg_text_length < 100:
                optimal_size = min(optimal_size * 2, self.max_batch_size)
        
        # Consider memory constraints
        if self.optimize_for_memory:
            memory_usage = psutil.virtual_memory().percent / 100.0
            if memory_usage > self.memory_threshold:
                optimal_size = max(optimal_size // 2, self.min_batch_size)
        
        return max(optimal_size, self.min_batch_size)
    
    def optimize_batch_size(self, sample_texts: List[str]) -> int:
        """
        Determine optimal batch size based on sample texts and hardware.
        
        Args:
            sample_texts: Representative sample of texts to analyze
            
        Returns:
            Optimal batch size for the given hardware and text characteristics
        """
        if not sample_texts:
            return self.initial_batch_size
        
        # Don't re-optimize too frequently
        current_time = time.time()
        if current_time - self._last_optimization_time < 60.0:  # Optimize at most once per minute
            return self.current_batch_size
        
        self._last_optimization_time = current_time
        
        # Test different batch sizes with sample
        test_sizes = [
            self.min_batch_size,
            self.initial_batch_size,
            min(self.initial_batch_size * 2, self.max_batch_size),
            self.max_batch_size
        ]
        
        best_size = self.initial_batch_size
        best_throughput = 0.0
        
        # Use small sample for testing
        test_sample = sample_texts[:min(len(sample_texts), 20)]
        
        for test_size in test_sizes:
            if test_size > len(test_sample):
                continue
                
            try:
                start_time = time.time()
                
                # Test this batch size
                _ = self.embedding_model.encode(test_sample[:test_size])
                
                processing_time = time.time() - start_time
                throughput = test_size / processing_time if processing_time > 0 else 0
                
                if throughput > best_throughput:
                    best_throughput = throughput
                    best_size = test_size
                    
            except Exception as e:
                logger.warning(f"Failed to test batch size {test_size}: {e}")
                continue
        
        self.current_batch_size = best_size
        logger.info(f"Optimized batch size to {best_size} (throughput: {best_throughput:.2f} texts/sec)")
        
        return best_size
    
    def _check_memory_usage(self) -> None:
        """Check memory usage and adjust batch size if necessary."""
        memory_info = psutil.virtual_memory()
        memory_usage = memory_info.percent / 100.0
        
        if memory_usage > self.memory_threshold:
            # Reduce batch size
            old_size = self.current_batch_size
            self.current_batch_size = max(self.current_batch_size // 2, self.min_batch_size)
            
            if self.current_batch_size != old_size:
                logger.warning(f"Reduced batch size from {old_size} to {self.current_batch_size} due to memory usage ({memory_usage:.1%})")
    
    def _update_performance_stats(self, num_texts: int, processing_time: float, batch_size: int) -> None:
        """Update performance statistics."""
        self._total_texts_processed += num_texts
        self._total_processing_time += processing_time
        
        # Add to performance history
        throughput = num_texts / processing_time if processing_time > 0 else 0
        
        performance_record = {
            "timestamp": time.time(),
            "batch_size": batch_size,
            "num_texts": num_texts,
            "processing_time": processing_time,
            "throughput": throughput
        }
        
        self.performance_history.append(performance_record)
        
        # Limit history size
        if len(self.performance_history) > self.performance_history_size:
            self.performance_history.pop(0)
    
    def get_batch_stats(self) -> Dict[str, Any]:
        """
        Get statistics about batch processing performance.
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.performance_history:
            return {
                "total_texts_processed": 0,
                "total_processing_time": 0.0,
                "average_throughput": 0.0,
                "current_batch_size": self.current_batch_size,
                "performance_history_size": 0
            }
        
        recent_throughputs = [record["throughput"] for record in self.performance_history[-10:]]
        avg_recent_throughput = sum(recent_throughputs) / len(recent_throughputs)
        
        overall_throughput = (
            self._total_texts_processed / self._total_processing_time 
            if self._total_processing_time > 0 else 0
        )
        
        return {
            "total_texts_processed": self._total_texts_processed,
            "total_processing_time": self._total_processing_time,
            "average_throughput": overall_throughput,
            "recent_average_throughput": avg_recent_throughput,
            "current_batch_size": self.current_batch_size,
            "min_batch_size": self.min_batch_size,
            "max_batch_size": self.max_batch_size,
            "performance_history_size": len(self.performance_history),
            "memory_threshold": self.memory_threshold,
            "optimize_for_memory": self.optimize_for_memory
        }
    
    def supports_streaming(self) -> bool:
        """
        Check if this processor supports streaming/incremental processing.
        
        Returns:
            True if streaming is supported
        """
        return self.enable_streaming
    
    def stream_process(self, texts: Iterator[str], batch_size: Optional[int] = None) -> Iterator[np.ndarray]:
        """
        Stream process texts in batches.
        
        Args:
            texts: Iterator of text strings
            batch_size: Optional batch size override
            
        Yields:
            Embedding arrays for each batch
            
        Raises:
            RuntimeError: If streaming is disabled or fails
        """
        if not self.enable_streaming:
            raise RuntimeError("Streaming is disabled for this batch processor")
        
        effective_batch_size = batch_size or self.current_batch_size
        batch = []
        
        try:
            for text in texts:
                batch.append(text)
                
                if len(batch) >= effective_batch_size:
                    # Process full batch
                    embeddings = self.process_batch(batch, effective_batch_size)
                    yield embeddings
                    batch = []
            
            # Process remaining texts
            if batch:
                embeddings = self.process_batch(batch, len(batch))
                yield embeddings
                
        except Exception as e:
            raise RuntimeError(f"Streaming batch processing failed: {e}") from e
    
    def reset_performance_stats(self) -> None:
        """Reset all performance statistics."""
        self.performance_history.clear()
        self._total_texts_processed = 0
        self._total_processing_time = 0.0
        self._last_optimization_time = 0.0
        self.current_batch_size = self.initial_batch_size
        
        logger.info("Performance statistics reset")