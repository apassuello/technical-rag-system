"""
Memory Monitor for ML Model Management.

This module provides real-time memory usage tracking and prediction for ML models,
enabling intelligent model loading/eviction decisions to stay within memory budgets.

Key Features:
- Real-time memory usage tracking
- Model memory footprint estimation
- Memory pressure detection and alerting
- Cross-platform compatibility (Linux, macOS, Windows)
"""

import psutil
import logging
import time
from typing import Dict, Optional, NamedTuple
from dataclasses import dataclass
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """Memory usage statistics."""
    
    total_mb: float
    used_mb: float
    available_mb: float
    percent_used: float
    epic1_process_mb: float
    
    
class ModelMemoryInfo(NamedTuple):
    """Memory information for a specific model."""
    
    model_name: str
    estimated_size_mb: float
    actual_size_mb: Optional[float] = None
    quantized: bool = False


class MemoryMonitor:
    """
    Real-time memory usage monitor with model-aware tracking.
    
    Tracks system memory usage and provides intelligent predictions
    for model loading decisions within the Epic 1 memory budget.
    """
    
    def __init__(self, update_interval_seconds: float = 1.0):
        """
        Initialize memory monitor.
        
        Args:
            update_interval_seconds: How often to update memory stats
        """
        self.update_interval = update_interval_seconds
        self._current_stats = None
        self._model_memory_map = {}  # model_name -> actual_memory_mb
        self._model_estimates = {}   # model_name -> estimated_memory_mb
        self._monitoring = False
        self._monitor_thread = None
        
        # Initialize model size estimates (in MB)
        self._initialize_model_estimates()
        
        logger.info(f"Initialized MemoryMonitor with {update_interval_seconds}s update interval")
    
    def _initialize_model_estimates(self) -> None:
        """Initialize memory estimates for different ML models."""
        self._model_estimates = {
            # Transformer models (approximate sizes in MB after quantization)
            'SciBERT': {'full': 440, 'quantized': 220},
            'DistilBERT': {'full': 260, 'quantized': 130},
            'DeBERTa-v3': {'full': 750, 'quantized': 375},
            'Sentence-BERT': {'full': 420, 'quantized': 210},
            'T5-small': {'full': 240, 'quantized': 120},
            
            # Additional overhead per model (tokenizers, buffers, etc.)
            'model_overhead': 50
        }
    
    def start_monitoring(self) -> None:
        """Start continuous memory monitoring in background thread."""
        if self._monitoring:
            logger.warning("Memory monitoring already started")
            return
            
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("Started memory monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop memory monitoring."""
        if not self._monitoring:
            return
            
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
        logger.info("Stopped memory monitoring")
    
    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while self._monitoring:
            try:
                self._current_stats = self._get_current_memory_stats()
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in memory monitoring loop: {e}")
                time.sleep(self.update_interval * 2)  # Back off on error
    
    def _get_current_memory_stats(self) -> MemoryStats:
        """Get current system memory statistics."""
        # Get system memory info
        virtual_memory = psutil.virtual_memory()
        
        # Get current process memory usage
        process = psutil.Process()
        process_memory_mb = process.memory_info().rss / 1024 / 1024
        
        return MemoryStats(
            total_mb=virtual_memory.total / 1024 / 1024,
            used_mb=virtual_memory.used / 1024 / 1024,
            available_mb=virtual_memory.available / 1024 / 1024,
            percent_used=virtual_memory.percent,
            epic1_process_mb=process_memory_mb
        )
    
    def get_current_stats(self) -> MemoryStats:
        """Get current memory statistics."""
        if self._current_stats is None or not self._monitoring:
            return self._get_current_memory_stats()
        return self._current_stats
    
    def get_epic1_memory_usage(self) -> float:
        """Get current Epic 1 process memory usage in MB."""
        return self.get_current_stats().epic1_process_mb
    
    def estimate_model_memory(self, model_name: str, quantized: bool = True) -> float:
        """
        Estimate memory footprint for a model.
        
        Args:
            model_name: Name of the model
            quantized: Whether the model will be quantized
            
        Returns:
            Estimated memory usage in MB
        """
        if model_name in self._model_estimates:
            size_key = 'quantized' if quantized else 'full'
            base_size = self._model_estimates[model_name][size_key]
            overhead = self._model_estimates['model_overhead']
            return base_size + overhead
        else:
            # Default estimate for unknown models
            default_size = 300 if not quantized else 150
            logger.warning(f"No memory estimate for model '{model_name}', using default: {default_size}MB")
            return default_size + self._model_estimates['model_overhead']
    
    def record_actual_model_memory(self, model_name: str, memory_mb: float) -> None:
        """Record actual memory usage for a loaded model."""
        self._model_memory_map[model_name] = memory_mb
        
        # Update estimates based on actual usage
        if model_name in self._model_estimates:
            estimated = self.estimate_model_memory(model_name)
            ratio = memory_mb / estimated
            logger.debug(f"Model {model_name}: estimated={estimated:.1f}MB, actual={memory_mb:.1f}MB, ratio={ratio:.2f}")
            
            # If actual usage is significantly different, log a warning
            if ratio < 0.5 or ratio > 2.0:
                logger.warning(f"Model {model_name} memory usage ({memory_mb:.1f}MB) differs significantly from estimate ({estimated:.1f}MB)")
    
    def get_actual_model_memory(self, model_name: str) -> Optional[float]:
        """Get actual recorded memory usage for a model."""
        return self._model_memory_map.get(model_name)
    
    def would_exceed_budget(self, model_name: str, memory_budget_mb: float, quantized: bool = True) -> bool:
        """
        Check if loading a model would exceed the memory budget.
        
        Args:
            model_name: Name of the model to load
            memory_budget_mb: Memory budget in MB
            quantized: Whether the model will be quantized
            
        Returns:
            True if loading the model would exceed the budget
        """
        current_usage = self.get_epic1_memory_usage()
        estimated_model_size = self.estimate_model_memory(model_name, quantized)
        
        projected_usage = current_usage + estimated_model_size
        
        logger.debug(f"Memory budget check: current={current_usage:.1f}MB, "
                    f"estimated_model={estimated_model_size:.1f}MB, "
                    f"projected={projected_usage:.1f}MB, budget={memory_budget_mb:.1f}MB")
        
        return projected_usage > memory_budget_mb
    
    def get_memory_pressure_level(self, memory_budget_mb: float) -> str:
        """
        Assess current memory pressure level.
        
        Args:
            memory_budget_mb: Memory budget in MB
            
        Returns:
            Pressure level: 'low', 'medium', 'high', 'critical'
        """
        current_usage = self.get_epic1_memory_usage()
        usage_ratio = current_usage / memory_budget_mb
        
        if usage_ratio < 0.5:
            return 'low'
        elif usage_ratio < 0.7:
            return 'medium'
        elif usage_ratio < 0.9:
            return 'high'
        else:
            return 'critical'
    
    def get_eviction_candidates(self, target_free_mb: float) -> Dict[str, float]:
        """
        Get models that could be evicted to free the target amount of memory.
        
        Args:
            target_free_mb: Amount of memory to free in MB
            
        Returns:
            Dict mapping model names to their memory usage
        """
        # Sort models by actual memory usage (descending)
        candidates = {}
        total_freeable = 0
        
        for model_name, memory_mb in sorted(
            self._model_memory_map.items(), 
            key=lambda x: x[1], 
            reverse=True
        ):
            candidates[model_name] = memory_mb
            total_freeable += memory_mb
            
            if total_freeable >= target_free_mb:
                break
        
        return candidates
    
    def log_memory_status(self) -> None:
        """Log current memory status for debugging."""
        stats = self.get_current_stats()
        logger.info(f"Memory Status - Total: {stats.total_mb:.1f}MB, "
                   f"Used: {stats.used_mb:.1f}MB ({stats.percent_used:.1f}%), "
                   f"Available: {stats.available_mb:.1f}MB, "
                   f"Epic1 Process: {stats.epic1_process_mb:.1f}MB")
        
        if self._model_memory_map:
            logger.info("Loaded models memory usage:")
            for model_name, memory_mb in self._model_memory_map.items():
                logger.info(f"  {model_name}: {memory_mb:.1f}MB")
    
    def __enter__(self):
        """Context manager entry."""
        self.start_monitoring()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_monitoring()