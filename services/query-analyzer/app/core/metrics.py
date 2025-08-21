"""
Metrics collection and monitoring for the Query Analyzer service.

This module provides Prometheus metrics integration with comprehensive
performance and business metrics tracking.
"""

import time
from typing import Dict, Any, Optional
from contextlib import contextmanager
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
from prometheus_client.core import REGISTRY
import logging

logger = logging.getLogger(__name__)


class QueryAnalyzerMetrics:
    """
    Metrics collector for the Query Analyzer service.
    
    This class provides centralized metrics collection with Prometheus
    integration for monitoring service performance and business metrics.
    """
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """
        Initialize metrics collector.
        
        Args:
            registry: Optional Prometheus registry (uses default if None)
        """
        self.registry = registry or REGISTRY
        
        # Initialize all metrics
        self._init_counters()
        self._init_histograms()
        self._init_gauges()
        self._init_info_metrics()
        
        logger.info("Initialized QueryAnalyzerMetrics with Prometheus integration")
    
    def _init_counters(self):
        """Initialize counter metrics."""
        # Query processing counters
        self.queries_total = Counter(
            'query_analyzer_queries_total',
            'Total number of queries processed',
            ['status', 'complexity_level', 'model_provider'],
            registry=self.registry
        )
        
        self.errors_total = Counter(
            'query_analyzer_errors_total',
            'Total number of errors by type',
            ['error_type', 'component'],
            registry=self.registry
        )
        
        # Component-specific counters
        self.feature_extractions_total = Counter(
            'query_analyzer_feature_extractions_total',
            'Total number of feature extractions',
            ['status'],
            registry=self.registry
        )
        
        self.classifications_total = Counter(
            'query_analyzer_classifications_total',
            'Total number of complexity classifications',
            ['complexity_level', 'confidence_tier'],
            registry=self.registry
        )
        
        self.recommendations_total = Counter(
            'query_analyzer_recommendations_total',
            'Total number of model recommendations',
            ['model_provider', 'routing_strategy'],
            registry=self.registry
        )
    
    def _init_histograms(self):
        """Initialize histogram metrics."""
        # Latency histograms
        latency_buckets = [0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0]
        
        self.query_duration = Histogram(
            'query_analyzer_query_duration_seconds',
            'Time spent processing queries',
            ['complexity_level'],
            buckets=latency_buckets,
            registry=self.registry
        )
        
        self.feature_extraction_duration = Histogram(
            'query_analyzer_feature_extraction_duration_seconds',
            'Time spent extracting features',
            buckets=latency_buckets[:7],  # Smaller buckets for fast operations
            registry=self.registry
        )
        
        self.classification_duration = Histogram(
            'query_analyzer_classification_duration_seconds',
            'Time spent classifying complexity',
            buckets=latency_buckets[:7],
            registry=self.registry
        )
        
        self.recommendation_duration = Histogram(
            'query_analyzer_recommendation_duration_seconds',
            'Time spent generating recommendations',
            buckets=latency_buckets[:7],
            registry=self.registry
        )
        
        # Business metrics histograms
        self.complexity_score = Histogram(
            'query_analyzer_complexity_score',
            'Distribution of complexity scores',
            ['complexity_level'],
            buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            registry=self.registry
        )
        
        self.confidence_score = Histogram(
            'query_analyzer_confidence_score',
            'Distribution of confidence scores',
            ['component'],
            buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            registry=self.registry
        )
    
    def _init_gauges(self):
        """Initialize gauge metrics."""
        # System health gauges
        self.active_requests = Gauge(
            'query_analyzer_active_requests',
            'Number of currently active requests',
            registry=self.registry
        )
        
        self.memory_usage_bytes = Gauge(
            'query_analyzer_memory_usage_bytes',
            'Current memory usage in bytes',
            registry=self.registry
        )
        
        # Performance gauges
        self.avg_latency_ms = Gauge(
            'query_analyzer_average_latency_milliseconds',
            'Average query processing latency in milliseconds',
            ['window'],  # e.g., '1m', '5m', '15m'
            registry=self.registry
        )
        
        self.error_rate = Gauge(
            'query_analyzer_error_rate',
            'Error rate as a fraction (0.0-1.0)',
            ['window'],
            registry=self.registry
        )
        
        # Business metrics gauges
        self.model_distribution = Gauge(
            'query_analyzer_model_usage_percentage',
            'Percentage of queries routed to each model',
            ['model_provider', 'model_name'],
            registry=self.registry
        )
        
        self.complexity_distribution = Gauge(
            'query_analyzer_complexity_distribution_percentage',
            'Percentage of queries by complexity level',
            ['complexity_level'],
            registry=self.registry
        )
    
    def _init_info_metrics(self):
        """Initialize info metrics."""
        self.service_info = Info(
            'query_analyzer_service_info',
            'Static information about the service',
            registry=self.registry
        )
    
    def set_service_info(self, name: str, version: str, description: str):
        """
        Set service information.
        
        Args:
            name: Service name
            version: Service version
            description: Service description
        """
        self.service_info.info({
            'name': name,
            'version': version,
            'description': description
        })
    
    @contextmanager
    def track_query_processing(self, complexity_level: Optional[str] = None):
        """
        Context manager to track query processing time and count.
        
        Args:
            complexity_level: Optional complexity level for labeling
            
        Usage:
            with metrics.track_query_processing(complexity_level='medium'):
                # Process query
                pass
        """
        labels = [complexity_level] if complexity_level else ['unknown']
        
        start_time = time.time()
        self.active_requests.inc()
        
        try:
            yield
            # Success case
            duration = time.time() - start_time
            self.query_duration.labels(*labels).observe(duration)
            self.queries_total.labels('success', complexity_level or 'unknown', 'unknown').inc()
            
        except Exception as e:
            # Error case
            duration = time.time() - start_time
            self.query_duration.labels(*labels).observe(duration)
            self.queries_total.labels('error', complexity_level or 'unknown', 'unknown').inc()
            self.errors_total.labels(type(e).__name__, 'query_processing').inc()
            raise
            
        finally:
            self.active_requests.dec()
    
    @contextmanager
    def track_component_processing(self, component: str):
        """
        Context manager to track component-specific processing.
        
        Args:
            component: Component name (feature_extraction, classification, recommendation)
        """
        start_time = time.time()
        
        try:
            yield
            # Success case
            duration = time.time() - start_time
            
            if component == 'feature_extraction':
                self.feature_extraction_duration.observe(duration)
                self.feature_extractions_total.labels('success').inc()
            elif component == 'classification':
                self.classification_duration.observe(duration)
            elif component == 'recommendation':
                self.recommendation_duration.observe(duration)
                
        except Exception as e:
            # Error case
            duration = time.time() - start_time
            
            if component == 'feature_extraction':
                self.feature_extraction_duration.observe(duration)
                self.feature_extractions_total.labels('error').inc()
            elif component == 'classification':
                self.classification_duration.observe(duration)
            elif component == 'recommendation':
                self.recommendation_duration.observe(duration)
                
            self.errors_total.labels(type(e).__name__, component).inc()
            raise
    
    def record_complexity_metrics(self, level: str, score: float, confidence: float):
        """
        Record complexity classification metrics.
        
        Args:
            level: Complexity level (simple/medium/complex)
            score: Complexity score (0.0-1.0)
            confidence: Classification confidence (0.0-1.0)
        """
        # Determine confidence tier for labeling
        if confidence >= 0.8:
            confidence_tier = 'high'
        elif confidence >= 0.5:
            confidence_tier = 'medium'
        else:
            confidence_tier = 'low'
        
        self.classifications_total.labels(level, confidence_tier).inc()
        self.complexity_score.labels(level).observe(score)
        self.confidence_score.labels('complexity_classifier').observe(confidence)
    
    def record_recommendation_metrics(self, provider: str, model_name: str, 
                                    strategy: str, confidence: float, cost: float):
        """
        Record model recommendation metrics.
        
        Args:
            provider: Model provider (ollama, openai, etc.)
            model_name: Specific model name
            strategy: Routing strategy used
            confidence: Recommendation confidence
            cost: Estimated cost per query
        """
        self.recommendations_total.labels(provider, strategy).inc()
        self.confidence_score.labels('model_recommender').observe(confidence)
        
        # Update model usage distribution (simplified - would need windowed calculation)
        # This is a placeholder - real implementation would track usage over time
        self.model_distribution.labels(provider, model_name).set(1.0)  # Placeholder
    
    def update_system_metrics(self, memory_bytes: int):
        """
        Update system-level metrics.
        
        Args:
            memory_bytes: Current memory usage in bytes
        """
        self.memory_usage_bytes.set(memory_bytes)
    
    def get_prometheus_metrics(self) -> str:
        """
        Get Prometheus-formatted metrics string.
        
        Returns:
            String containing all metrics in Prometheus format
        """
        return generate_latest(self.registry).decode('utf-8')
    
    def get_metrics_dict(self) -> Dict[str, Any]:
        """
        Get metrics as a dictionary for JSON responses.
        
        Returns:
            Dictionary containing current metric values
        """
        # This would typically involve collecting current values from all metrics
        # For brevity, returning a subset of key metrics
        return {
            'total_queries': self._get_counter_value(self.queries_total),
            'total_errors': self._get_counter_value(self.errors_total),
            'active_requests': self.active_requests._value._value,
            'memory_usage_mb': self.memory_usage_bytes._value._value / (1024 * 1024),
        }
    
    def _get_counter_value(self, counter) -> float:
        """Get total value across all labels for a counter metric."""
        try:
            return sum(sample.value for sample in counter.collect()[0].samples)
        except (IndexError, AttributeError):
            return 0.0


# Global metrics instance
_metrics: Optional[QueryAnalyzerMetrics] = None


def get_metrics() -> QueryAnalyzerMetrics:
    """
    Get the global metrics instance.
    
    Returns:
        Current metrics instance
        
    Raises:
        RuntimeError: If metrics not initialized
    """
    if _metrics is None:
        raise RuntimeError("Metrics not initialized. Call init_metrics() first.")
    return _metrics


def init_metrics(registry: Optional[CollectorRegistry] = None) -> QueryAnalyzerMetrics:
    """
    Initialize the global metrics instance.
    
    Args:
        registry: Optional Prometheus registry
        
    Returns:
        Initialized metrics instance
    """
    global _metrics
    _metrics = QueryAnalyzerMetrics(registry)
    return _metrics