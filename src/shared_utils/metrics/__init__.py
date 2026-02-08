"""
Shared metrics collection framework for the RAG system.

This module provides a unified metrics collection infrastructure that can be used
across different components of the RAG system for consistent metrics gathering,
analysis, and reporting.

Key Components:
- BaseMetricsCollector: Abstract base class for metrics collectors
- CalibrationQueryMetrics, AnalyticsQueryMetrics: Specialized metric data models
- MetricsConverter: Utilities for converting between metric formats
- InMemoryMetricsStorage: Simple storage backend for metrics

Example usage:

    from src.shared_utils.metrics import MetricsCollector
    
    # Create metrics collector
    collector = MetricsCollector()
    
    # Start collecting metrics for a query
    metrics = collector.start_query_collection("Q001", "What is RISC-V?")
    
    # Collect various metrics
    collector.collect_retrieval_metrics(metrics, retrieval_results, retrieval_time=0.12)
    collector.collect_generation_metrics(metrics, answer, confidence, generation_time)
    collector.collect_performance_metrics(metrics, total_time, memory_mb, cpu_percent)
    
    # Get summary and export
    logger.info(collector.get_metrics_summary())
    collector.export_metrics(Path("metrics.json"))
"""

# Import base classes and protocols
import logging

from .base_metrics_collector import (
    BaseMetricsCollector,
    InMemoryMetricsStorage,
    MetricsStorage,
)

# Import concrete implementations
from .calibration_collector import MetricsCollector, QueryMetrics

# Import data models
from .data_models import (
    AnalyticsQueryMetrics,
    BaseQueryMetrics,
    CalibrationQueryMetrics,
    ComponentMetrics,
    MetricsConverter,
    SessionMetadata,
    SystemMetrics,
)

logger = logging.getLogger(__name__)
# Define public API
__all__ = [
    # Base classes
    'BaseMetricsCollector',
    'MetricsStorage', 
    'InMemoryMetricsStorage',
    
    # Data models
    'BaseQueryMetrics',
    'CalibrationQueryMetrics',
    'AnalyticsQueryMetrics', 
    'SystemMetrics',
    'SessionMetadata',
    'ComponentMetrics',
    'MetricsConverter',
    
    # Concrete implementations
    'MetricsCollector',  # Main calibration metrics collector
    'QueryMetrics',      # Legacy alias for backward compatibility
]

# Version information
__version__ = "1.0.0"
__author__ = "RAG Portfolio Project"
__description__ = "Shared metrics collection framework"