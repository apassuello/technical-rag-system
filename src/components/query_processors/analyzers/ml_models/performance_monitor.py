"""
Performance Monitor for ML Model Operations.

This module provides comprehensive performance tracking and monitoring for
ML model operations in the Epic 1 system, including latency, memory usage,
accuracy metrics, and system health indicators.

Key Features:
- Real-time latency and throughput tracking
- Memory usage monitoring and alerting
- Accuracy and quality metrics collection
- Performance trend analysis
- Automated alert generation
- Comprehensive reporting and logging
"""

import json
import logging
import threading
import time
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, NamedTuple, Optional

logger = logging.getLogger(__name__)


class PerformanceMetric(NamedTuple):
    """Individual performance metric data point."""
    
    timestamp: float
    metric_name: str
    value: float
    metadata: Dict[str, Any] = {}


@dataclass
class LatencyStats:
    """Latency statistics for a specific operation."""
    
    operation_name: str
    count: int = 0
    total_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    recent_times: deque = field(default_factory=lambda: deque(maxlen=100))
    
    @property
    def avg_time_ms(self) -> float:
        """Calculate average latency."""
        return self.total_time_ms / self.count if self.count > 0 else 0.0
    
    @property
    def p95_time_ms(self) -> float:
        """Calculate 95th percentile latency."""
        if not self.recent_times:
            return 0.0
        sorted_times = sorted(self.recent_times)
        p95_index = int(0.95 * len(sorted_times))
        return sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]
    
    def add_measurement(self, latency_ms: float) -> None:
        """Add a latency measurement."""
        self.count += 1
        self.total_time_ms += latency_ms
        self.min_time_ms = min(self.min_time_ms, latency_ms)
        self.max_time_ms = max(self.max_time_ms, latency_ms)
        self.recent_times.append(latency_ms)


@dataclass
class ThroughputStats:
    """Throughput statistics for operations."""
    
    operation_name: str
    request_count: int = 0
    start_time: float = field(default_factory=time.time)
    recent_requests: deque = field(default_factory=lambda: deque(maxlen=1000))
    
    @property
    def requests_per_second(self) -> float:
        """Calculate current requests per second."""
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        return self.request_count / elapsed_time if elapsed_time > 0 else 0.0
    
    @property
    def recent_rps(self) -> float:
        """Calculate requests per second for recent window."""
        current_time = time.time()
        recent_window = [t for t in self.recent_requests if current_time - t <= 60.0]  # Last minute
        return len(recent_window) / 60.0 if recent_window else 0.0
    
    def add_request(self) -> None:
        """Record a new request."""
        current_time = time.time()
        self.request_count += 1
        self.recent_requests.append(current_time)


@dataclass
class QualityStats:
    """Quality and accuracy statistics."""
    
    operation_name: str
    total_evaluations: int = 0
    accuracy_sum: float = 0.0
    confidence_sum: float = 0.0
    quality_scores: deque = field(default_factory=lambda: deque(maxlen=1000))
    
    @property
    def avg_accuracy(self) -> float:
        """Calculate average accuracy."""
        return self.accuracy_sum / self.total_evaluations if self.total_evaluations > 0 else 0.0
    
    @property
    def avg_confidence(self) -> float:
        """Calculate average confidence."""
        return self.confidence_sum / self.total_evaluations if self.total_evaluations > 0 else 0.0
    
    def add_evaluation(self, accuracy: float, confidence: float) -> None:
        """Add quality evaluation."""
        self.total_evaluations += 1
        self.accuracy_sum += accuracy
        self.confidence_sum += confidence
        self.quality_scores.append({'accuracy': accuracy, 'confidence': confidence, 'timestamp': time.time()})


class AlertManager:
    """Manages performance alerts and notifications."""

    def __init__(self) -> None:
        self.alert_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.alert_history: deque = deque(maxlen=1000)
        
    def register_alert_handler(self, alert_type: str, handler: Callable) -> None:
        """Register an alert handler for a specific alert type."""
        self.alert_handlers[alert_type].append(handler)
        logger.debug(f"Registered alert handler for {alert_type}")
    
    def trigger_alert(self, alert_type: str, message: str, severity: str = 'warning', metadata: Dict[str, Any] = None) -> None:
        """Trigger an alert of specified type."""
        alert = {
            'type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': time.time(),
            'metadata': metadata or {}
        }
        
        self.alert_history.append(alert)
        
        # Log the alert
        log_level = logging.ERROR if severity == 'error' else logging.WARNING
        logger.log(log_level, f"ALERT [{alert_type}]: {message}")
        
        # Call registered handlers
        for handler in self.alert_handlers.get(alert_type, []):
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")


class PerformanceMonitor:
    """
    Comprehensive performance monitoring for Epic 1 ML operations.
    
    Tracks latency, throughput, memory usage, accuracy, and system health
    with configurable alerting and reporting capabilities.
    """
    
    def __init__(
        self,
        enable_alerts: bool = True,
        metrics_retention_hours: int = 24,
        alert_thresholds: Optional[Dict[str, float]] = None
    ):
        """
        Initialize performance monitor.
        
        Args:
            enable_alerts: Whether to enable alerting
            metrics_retention_hours: How long to retain detailed metrics
            alert_thresholds: Custom alert thresholds
        """
        self.enable_alerts = enable_alerts
        self.metrics_retention_hours = metrics_retention_hours
        
        # Performance statistics
        self.latency_stats: Dict[str, LatencyStats] = {}
        self.throughput_stats: Dict[str, ThroughputStats] = {}
        self.quality_stats: Dict[str, QualityStats] = {}
        
        # Raw metrics storage
        self.raw_metrics: deque = deque(maxlen=10000)
        
        # Alert management
        self.alert_manager = AlertManager() if enable_alerts else None
        
        # Alert thresholds
        self.alert_thresholds = alert_thresholds or {
            'max_latency_ms': 5000,
            'min_accuracy': 0.7,
            'max_memory_mb': 2048,
            'min_throughput_rps': 0.1
        }
        
        # Thread safety
        self._lock = threading.RLock()

        # Background cleanup
        self._stop_event = threading.Event()
        self._cleanup_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="perf-monitor-cleanup")
        self._start_cleanup_task()
        
        logger.info(f"Initialized PerformanceMonitor (alerts={enable_alerts}, "
                   f"retention={metrics_retention_hours}h)")
    
    def _start_cleanup_task(self) -> None:
        """Start background task for metrics cleanup."""
        def cleanup_worker():
            while not self._stop_event.is_set():
                self._stop_event.wait(3600)  # Wait 1 hour or until stopped
                if not self._stop_event.is_set():
                    try:
                        self._cleanup_old_metrics()
                    except Exception as e:
                        logger.error(f"Metrics cleanup failed: {e}")

        self._cleanup_executor.submit(cleanup_worker)

    def shutdown(self) -> None:
        """Shut down the background cleanup task and executor."""
        self._stop_event.set()
        self._cleanup_executor.shutdown(wait=False)
    
    def _cleanup_old_metrics(self) -> None:
        """Clean up old metrics beyond retention period."""
        cutoff_time = time.time() - (self.metrics_retention_hours * 3600)
        
        with self._lock:
            # Clean raw metrics
            while self.raw_metrics and self.raw_metrics[0].timestamp < cutoff_time:
                self.raw_metrics.popleft()
            
            # Clean quality scores
            for stats in self.quality_stats.values():
                while stats.quality_scores and stats.quality_scores[0]['timestamp'] < cutoff_time:
                    stats.quality_scores.popleft()
        
        logger.debug("Completed metrics cleanup")
    
    def record_latency(self, operation: str, latency_ms: float, metadata: Dict[str, Any] = None) -> None:
        """
        Record latency measurement for an operation.
        
        Args:
            operation: Name of the operation
            latency_ms: Latency in milliseconds
            metadata: Additional metadata
        """
        with self._lock:
            if operation not in self.latency_stats:
                self.latency_stats[operation] = LatencyStats(operation)
            
            self.latency_stats[operation].add_measurement(latency_ms)
            
            # Store raw metric
            self.raw_metrics.append(PerformanceMetric(
                timestamp=time.time(),
                metric_name=f"{operation}_latency",
                value=latency_ms,
                metadata=metadata or {}
            ))
        
        # Check for alerts
        if self.alert_manager and latency_ms > self.alert_thresholds.get('max_latency_ms', 5000):
            self.alert_manager.trigger_alert(
                'high_latency',
                f"High latency detected for {operation}: {latency_ms:.1f}ms",
                severity='warning',
                metadata={'operation': operation, 'latency_ms': latency_ms}
            )
    
    def record_request(self, operation: str) -> None:
        """
        Record a request for throughput tracking.
        
        Args:
            operation: Name of the operation
        """
        with self._lock:
            if operation not in self.throughput_stats:
                self.throughput_stats[operation] = ThroughputStats(operation)
            
            self.throughput_stats[operation].add_request()
    
    def record_quality(self, operation: str, accuracy: float, confidence: float) -> None:
        """
        Record quality metrics for an operation.
        
        Args:
            operation: Name of the operation
            accuracy: Accuracy score (0-1)
            confidence: Confidence score (0-1)
        """
        with self._lock:
            if operation not in self.quality_stats:
                self.quality_stats[operation] = QualityStats(operation)
            
            self.quality_stats[operation].add_evaluation(accuracy, confidence)
        
        # Check for alerts
        if self.alert_manager and accuracy < self.alert_thresholds.get('min_accuracy', 0.7):
            self.alert_manager.trigger_alert(
                'low_accuracy',
                f"Low accuracy detected for {operation}: {accuracy:.3f}",
                severity='warning',
                metadata={'operation': operation, 'accuracy': accuracy, 'confidence': confidence}
            )
    
    def record_memory_usage(self, operation: str, memory_mb: float) -> None:
        """
        Record memory usage for an operation.
        
        Args:
            operation: Name of the operation
            memory_mb: Memory usage in MB
        """
        # Store raw metric
        with self._lock:
            self.raw_metrics.append(PerformanceMetric(
                timestamp=time.time(),
                metric_name=f"{operation}_memory",
                value=memory_mb,
                metadata={'operation': operation}
            ))
        
        # Check for alerts
        if self.alert_manager and memory_mb > self.alert_thresholds.get('max_memory_mb', 2048):
            self.alert_manager.trigger_alert(
                'high_memory',
                f"High memory usage detected for {operation}: {memory_mb:.1f}MB",
                severity='error',
                metadata={'operation': operation, 'memory_mb': memory_mb}
            )
    
    def get_latency_stats(self, operation: str) -> Optional[LatencyStats]:
        """Get latency statistics for an operation."""
        with self._lock:
            return self.latency_stats.get(operation)
    
    def get_throughput_stats(self, operation: str) -> Optional[ThroughputStats]:
        """Get throughput statistics for an operation."""
        with self._lock:
            return self.throughput_stats.get(operation)
    
    def get_quality_stats(self, operation: str) -> Optional[QualityStats]:
        """Get quality statistics for an operation."""
        with self._lock:
            return self.quality_stats.get(operation)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        with self._lock:
            summary = {
                'timestamp': time.time(),
                'operations': {},
                'system_health': self._calculate_system_health(),
                'alert_count': len(self.alert_manager.alert_history) if self.alert_manager else 0
            }
            
            # Summarize each operation
            all_operations = set()
            all_operations.update(self.latency_stats.keys())
            all_operations.update(self.throughput_stats.keys())
            all_operations.update(self.quality_stats.keys())
            
            for operation in all_operations:
                op_summary = {'name': operation}
                
                # Latency info
                if operation in self.latency_stats:
                    lat_stats = self.latency_stats[operation]
                    op_summary['latency'] = {
                        'avg_ms': lat_stats.avg_time_ms,
                        'p95_ms': lat_stats.p95_time_ms,
                        'min_ms': lat_stats.min_time_ms,
                        'max_ms': lat_stats.max_time_ms,
                        'count': lat_stats.count
                    }
                
                # Throughput info
                if operation in self.throughput_stats:
                    thr_stats = self.throughput_stats[operation]
                    op_summary['throughput'] = {
                        'rps': thr_stats.requests_per_second,
                        'recent_rps': thr_stats.recent_rps,
                        'total_requests': thr_stats.request_count
                    }
                
                # Quality info
                if operation in self.quality_stats:
                    qual_stats = self.quality_stats[operation]
                    op_summary['quality'] = {
                        'avg_accuracy': qual_stats.avg_accuracy,
                        'avg_confidence': qual_stats.avg_confidence,
                        'evaluation_count': qual_stats.total_evaluations
                    }
                
                summary['operations'][operation] = op_summary
            
            return summary
    
    def _calculate_system_health(self) -> str:
        """Calculate overall system health score."""
        health_issues = []
        
        # Check latency health
        for operation, stats in self.latency_stats.items():
            if stats.p95_time_ms > self.alert_thresholds.get('max_latency_ms', 5000):
                health_issues.append(f"high_latency_{operation}")
        
        # Check quality health
        for operation, stats in self.quality_stats.items():
            if stats.avg_accuracy < self.alert_thresholds.get('min_accuracy', 0.7):
                health_issues.append(f"low_accuracy_{operation}")
        
        # Determine health level
        if not health_issues:
            return 'healthy'
        elif len(health_issues) <= 2:
            return 'degraded'
        else:
            return 'unhealthy'
    
    def log_performance_report(self) -> None:
        """Log detailed performance report."""
        summary = self.get_performance_summary()
        
        logger.info("=== PERFORMANCE REPORT ===")
        logger.info(f"System Health: {summary['system_health']}")
        logger.info(f"Active Alerts: {summary['alert_count']}")
        logger.info(f"Monitored Operations: {len(summary['operations'])}")
        
        for operation, stats in summary['operations'].items():
            logger.info(f"\nOperation: {operation}")
            
            if 'latency' in stats:
                lat = stats['latency']
                logger.info(f"  Latency: avg={lat['avg_ms']:.1f}ms, p95={lat['p95_ms']:.1f}ms, "
                           f"min={lat['min_ms']:.1f}ms, max={lat['max_ms']:.1f}ms ({lat['count']} samples)")
            
            if 'throughput' in stats:
                thr = stats['throughput']
                logger.info(f"  Throughput: {thr['rps']:.2f} RPS (recent: {thr['recent_rps']:.2f} RPS, "
                           f"total: {thr['total_requests']} requests)")
            
            if 'quality' in stats:
                qual = stats['quality']
                logger.info(f"  Quality: accuracy={qual['avg_accuracy']:.3f}, "
                           f"confidence={qual['avg_confidence']:.3f} ({qual['evaluation_count']} evaluations)")
        
        logger.info("=== END PERFORMANCE REPORT ===")
    
    def export_metrics(self, filepath: Path, format: str = 'json') -> None:
        """
        Export metrics to file.
        
        Args:
            filepath: Path to export file
            format: Export format ('json', 'csv')
        """
        summary = self.get_performance_summary()
        
        if format.lower() == 'json':
            with open(filepath, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
        elif format.lower() == 'csv':
            # Implement CSV export if needed
            logger.warning("CSV export not implemented yet")
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        logger.info(f"Exported performance metrics to {filepath}")
    
    def register_alert_handler(self, alert_type: str, handler: Callable) -> None:
        """Register custom alert handler."""
        if self.alert_manager:
            self.alert_manager.register_alert_handler(alert_type, handler)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._cleanup_executor:
            self._cleanup_executor.shutdown(wait=False)