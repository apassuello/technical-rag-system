"""
Real-time Metrics Collection for Advanced Retriever.

This module collects and aggregates real-time metrics from the advanced
retriever system for analytics dashboard and performance monitoring.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import threading
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """Metrics for a single query."""
    query_id: str
    query_text: str
    timestamp: float
    
    # Latency metrics (milliseconds)
    total_latency: float
    dense_retrieval_latency: float
    sparse_retrieval_latency: float
    graph_retrieval_latency: float
    neural_reranking_latency: float
    
    # Quality metrics
    num_results: int
    relevance_scores: List[float]
    confidence_score: float
    
    # Component usage
    components_used: List[str]
    backend_used: str
    
    # User interaction
    user_id: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class SystemMetrics:
    """System-wide performance metrics."""
    timestamp: float
    
    # Performance
    queries_per_second: float
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    
    # Quality
    avg_relevance_score: float
    avg_confidence_score: float
    success_rate: float
    
    # Resource usage
    memory_usage_mb: float
    cpu_usage_percent: float
    
    # Component status
    active_components: List[str]
    component_health: Dict[str, str]


class MetricsCollector:
    """
    Real-time metrics collector for advanced retriever analytics.
    
    This class collects, aggregates, and provides access to real-time
    metrics from the advanced retriever system for dashboard visualization
    and performance monitoring.
    """
    
    def __init__(self, 
                 max_query_history: int = 10000,
                 aggregation_window_seconds: int = 60,
                 storage_path: Optional[Path] = None):
        """
        Initialize metrics collector.
        
        Args:
            max_query_history: Maximum number of query metrics to keep
            aggregation_window_seconds: Window for aggregating metrics
            storage_path: Optional path to persist metrics
        """
        self.max_query_history = max_query_history
        self.aggregation_window_seconds = aggregation_window_seconds
        self.storage_path = storage_path
        
        # Query-level metrics storage
        self.query_metrics: deque = deque(maxlen=max_query_history)
        self.query_metrics_lock = threading.RLock()
        
        # System-level metrics
        self.system_metrics: deque = deque(maxlen=1440)  # 24 hours at 1-minute intervals
        self.system_metrics_lock = threading.RLock()
        
        # Real-time aggregation
        self.current_window_start = time.time()
        self.current_window_queries = []
        
        # Component tracking
        self.component_metrics = defaultdict(lambda: {
            "total_calls": 0,
            "total_latency": 0.0,
            "error_count": 0,
            "last_used": 0.0
        })
        
        # Backend performance tracking
        self.backend_metrics = defaultdict(lambda: {
            "total_queries": 0,
            "total_latency": 0.0,
            "success_count": 0,
            "error_count": 0
        })
        
        # Dashboard data cache
        self.dashboard_cache = {}
        self.cache_timestamp = 0.0
        self.cache_ttl_seconds = 5.0  # 5-second cache
        
        logger.info(f"MetricsCollector initialized with {max_query_history} query history")
    
    def record_query_metrics(self, metrics: QueryMetrics) -> None:
        """
        Record metrics for a completed query.
        
        Args:
            metrics: Query metrics to record
        """
        with self.query_metrics_lock:
            self.query_metrics.append(metrics)
            self.current_window_queries.append(metrics)
        
        # Update component metrics
        self._update_component_metrics(metrics)
        
        # Update backend metrics
        self._update_backend_metrics(metrics)
        
        # Check if we should aggregate system metrics
        if time.time() - self.current_window_start >= self.aggregation_window_seconds:
            self._aggregate_system_metrics()
        
        # Invalidate dashboard cache
        self.cache_timestamp = 0.0
        
        logger.debug(f"Recorded query metrics: {metrics.query_id}")
    
    def record_component_usage(self, 
                              component_name: str, 
                              latency_ms: float, 
                              success: bool = True) -> None:
        """
        Record component usage metrics.
        
        Args:
            component_name: Name of the component
            latency_ms: Processing latency in milliseconds
            success: Whether the operation was successful
        """
        metrics = self.component_metrics[component_name]
        metrics["total_calls"] += 1
        metrics["total_latency"] += latency_ms
        metrics["last_used"] = time.time()
        
        if not success:
            metrics["error_count"] += 1
    
    def get_real_time_dashboard_data(self) -> Dict[str, Any]:
        """
        Get real-time data for dashboard visualization.
        
        Returns:
            Dictionary with dashboard data
        """
        # Check cache first
        current_time = time.time()
        if (current_time - self.cache_timestamp) < self.cache_ttl_seconds and self.dashboard_cache:
            return self.dashboard_cache
        
        # Generate fresh dashboard data
        dashboard_data = {
            "timestamp": current_time,
            "overview": self._get_overview_metrics(),
            "performance": self._get_performance_metrics(),
            "quality": self._get_quality_metrics(),
            "components": self._get_component_metrics(),
            "backends": self._get_backend_metrics(),
            "recent_queries": self._get_recent_queries(),
            "time_series": self._get_time_series_data()
        }
        
        # Update cache
        self.dashboard_cache = dashboard_data
        self.cache_timestamp = current_time
        
        return dashboard_data
    
    def _get_overview_metrics(self) -> Dict[str, Any]:
        """Get high-level overview metrics."""
        with self.query_metrics_lock:
            recent_queries = list(self.query_metrics)[-100:]  # Last 100 queries
        
        if not recent_queries:
            return {
                "total_queries": 0,
                "queries_per_minute": 0.0,
                "avg_latency_ms": 0.0,
                "success_rate": 0.0
            }
        
        # Calculate queries per minute
        if len(recent_queries) >= 2:
            time_span = recent_queries[-1].timestamp - recent_queries[0].timestamp
            queries_per_minute = (len(recent_queries) / max(time_span, 1)) * 60
        else:
            queries_per_minute = 0.0
        
        # Calculate average latency
        avg_latency = sum(q.total_latency for q in recent_queries) / len(recent_queries)
        
        # Calculate success rate (assume success if confidence > 0.5)
        successful_queries = sum(1 for q in recent_queries if q.confidence_score > 0.5)
        success_rate = successful_queries / len(recent_queries) * 100
        
        return {
            "total_queries": len(self.query_metrics),
            "queries_per_minute": queries_per_minute,
            "avg_latency_ms": avg_latency,
            "success_rate": success_rate
        }
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics."""
        with self.query_metrics_lock:
            recent_queries = list(self.query_metrics)[-1000:]  # Last 1000 queries
        
        if not recent_queries:
            return {}
        
        # Calculate latency percentiles
        latencies = [q.total_latency for q in recent_queries]
        latencies.sort()
        
        n = len(latencies)
        p50 = latencies[int(n * 0.5)] if n > 0 else 0.0
        p95 = latencies[int(n * 0.95)] if n > 0 else 0.0
        p99 = latencies[int(n * 0.99)] if n > 0 else 0.0
        
        # Component latency breakdown
        component_latencies = {
            "dense_retrieval": sum(q.dense_retrieval_latency for q in recent_queries) / len(recent_queries),
            "sparse_retrieval": sum(q.sparse_retrieval_latency for q in recent_queries) / len(recent_queries),
            "graph_retrieval": sum(q.graph_retrieval_latency for q in recent_queries) / len(recent_queries),
            "neural_reranking": sum(q.neural_reranking_latency for q in recent_queries) / len(recent_queries)
        }
        
        return {
            "latency_percentiles": {
                "p50": p50,
                "p95": p95,
                "p99": p99
            },
            "component_latencies": component_latencies,
            "throughput": {
                "current_qps": len(recent_queries) / 60.0 if recent_queries else 0.0,
                "peak_qps": self._calculate_peak_qps(recent_queries)
            }
        }
    
    def _get_quality_metrics(self) -> Dict[str, Any]:
        """Get quality-related metrics."""
        with self.query_metrics_lock:
            recent_queries = list(self.query_metrics)[-1000:]
        
        if not recent_queries:
            return {}
        
        # Average relevance scores
        avg_relevance = 0.0
        total_results = 0
        
        for query in recent_queries:
            if query.relevance_scores:
                avg_relevance += sum(query.relevance_scores)
                total_results += len(query.relevance_scores)
        
        if total_results > 0:
            avg_relevance /= total_results
        
        # Confidence distribution
        confidences = [q.confidence_score for q in recent_queries]
        high_confidence = sum(1 for c in confidences if c > 0.8)
        medium_confidence = sum(1 for c in confidences if 0.5 <= c <= 0.8)
        low_confidence = sum(1 for c in confidences if c < 0.5)
        
        return {
            "avg_relevance_score": avg_relevance,
            "avg_confidence_score": sum(confidences) / len(confidences) if confidences else 0.0,
            "confidence_distribution": {
                "high": high_confidence,
                "medium": medium_confidence,
                "low": low_confidence
            },
            "avg_results_per_query": sum(q.num_results for q in recent_queries) / len(recent_queries)
        }
    
    def _get_component_metrics(self) -> Dict[str, Any]:
        """Get component usage and performance metrics."""
        components_data = {}
        
        for component_name, metrics in self.component_metrics.items():
            if metrics["total_calls"] > 0:
                avg_latency = metrics["total_latency"] / metrics["total_calls"]
                error_rate = metrics["error_count"] / metrics["total_calls"] * 100
                
                components_data[component_name] = {
                    "total_calls": metrics["total_calls"],
                    "avg_latency_ms": avg_latency,
                    "error_rate": error_rate,
                    "last_used": metrics["last_used"],
                    "status": "healthy" if error_rate < 5 else "warning" if error_rate < 15 else "error"
                }
        
        return components_data
    
    def _get_backend_metrics(self) -> Dict[str, Any]:
        """Get backend performance metrics."""
        backends_data = {}
        
        for backend_name, metrics in self.backend_metrics.items():
            if metrics["total_queries"] > 0:
                avg_latency = metrics["total_latency"] / metrics["total_queries"]
                success_rate = metrics["success_count"] / metrics["total_queries"] * 100
                
                backends_data[backend_name] = {
                    "total_queries": metrics["total_queries"],
                    "avg_latency_ms": avg_latency,
                    "success_rate": success_rate,
                    "error_count": metrics["error_count"]
                }
        
        return backends_data
    
    def _get_recent_queries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent query details."""
        with self.query_metrics_lock:
            recent_queries = list(self.query_metrics)[-limit:]
        
        query_data = []
        for query in recent_queries:
            query_data.append({
                "query_id": query.query_id,
                "query_text": query.query_text[:100] + "..." if len(query.query_text) > 100 else query.query_text,
                "timestamp": query.timestamp,
                "total_latency": query.total_latency,
                "confidence_score": query.confidence_score,
                "num_results": query.num_results,
                "backend_used": query.backend_used,
                "components_used": query.components_used
            })
        
        return query_data
    
    def _get_time_series_data(self) -> Dict[str, Any]:
        """Get time series data for charts."""
        with self.system_metrics_lock:
            system_data = list(self.system_metrics)[-60:]  # Last 60 minutes
        
        if not system_data:
            return {}
        
        timestamps = [s.timestamp for s in system_data]
        latencies = [s.avg_latency_ms for s in system_data]
        qps = [s.queries_per_second for s in system_data]
        success_rates = [s.success_rate for s in system_data]
        
        return {
            "timestamps": timestamps,
            "latency": latencies,
            "qps": qps,
            "success_rate": success_rates
        }
    
    def _update_component_metrics(self, query_metrics: QueryMetrics) -> None:
        """Update component-level metrics from query."""
        for component in query_metrics.components_used:
            self.record_component_usage(component, query_metrics.total_latency / len(query_metrics.components_used))
    
    def _update_backend_metrics(self, query_metrics: QueryMetrics) -> None:
        """Update backend-level metrics from query."""
        backend = query_metrics.backend_used
        metrics = self.backend_metrics[backend]
        
        metrics["total_queries"] += 1
        metrics["total_latency"] += query_metrics.total_latency
        
        if query_metrics.confidence_score > 0.5:
            metrics["success_count"] += 1
        else:
            metrics["error_count"] += 1
    
    def _aggregate_system_metrics(self) -> None:
        """Aggregate current window into system metrics."""
        if not self.current_window_queries:
            return
        
        current_time = time.time()
        window_duration = current_time - self.current_window_start
        
        # Calculate aggregated metrics
        total_queries = len(self.current_window_queries)
        qps = total_queries / window_duration if window_duration > 0 else 0.0
        
        latencies = [q.total_latency for q in self.current_window_queries]
        avg_latency = sum(latencies) / len(latencies)
        latencies.sort()
        
        n = len(latencies)
        p95_latency = latencies[int(n * 0.95)] if n > 0 else 0.0
        p99_latency = latencies[int(n * 0.99)] if n > 0 else 0.0
        
        # Quality metrics
        confidences = [q.confidence_score for q in self.current_window_queries]
        avg_confidence = sum(confidences) / len(confidences)
        
        relevance_scores = []
        for query in self.current_window_queries:
            relevance_scores.extend(query.relevance_scores)
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
        
        success_count = sum(1 for q in self.current_window_queries if q.confidence_score > 0.5)
        success_rate = success_count / total_queries * 100
        
        # Create system metrics
        system_metrics = SystemMetrics(
            timestamp=current_time,
            queries_per_second=qps,
            avg_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            avg_relevance_score=avg_relevance,
            avg_confidence_score=avg_confidence,
            success_rate=success_rate,
            memory_usage_mb=0.0,  # Placeholder
            cpu_usage_percent=0.0,  # Placeholder
            active_components=list(set(comp for q in self.current_window_queries for comp in q.components_used)),
            component_health={}  # Placeholder
        )
        
        # Store system metrics
        with self.system_metrics_lock:
            self.system_metrics.append(system_metrics)
        
        # Reset window
        self.current_window_start = current_time
        self.current_window_queries = []
        
        logger.debug(f"Aggregated system metrics: QPS={qps:.2f}, avg_latency={avg_latency:.1f}ms")
    
    def _calculate_peak_qps(self, queries: List[QueryMetrics], window_seconds: int = 60) -> float:
        """Calculate peak queries per second in a sliding window."""
        if len(queries) < 2:
            return 0.0
        
        max_qps = 0.0
        
        for i in range(len(queries)):
            window_start = queries[i].timestamp
            window_end = window_start + window_seconds
            
            # Count queries in this window
            count = 0
            for j in range(i, len(queries)):
                if queries[j].timestamp <= window_end:
                    count += 1
                else:
                    break
            
            qps = count / window_seconds
            max_qps = max(max_qps, qps)
        
        return max_qps
    
    def export_metrics(self, filepath: Path) -> None:
        """
        Export metrics to file.
        
        Args:
            filepath: Path to export file
        """
        try:
            export_data = {
                "export_timestamp": time.time(),
                "query_metrics": [asdict(q) for q in self.query_metrics],
                "system_metrics": [asdict(s) for s in self.system_metrics],
                "component_metrics": dict(self.component_metrics),
                "backend_metrics": dict(self.backend_metrics)
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Metrics exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics.
        
        Returns:
            Dictionary with summary statistics
        """
        with self.query_metrics_lock:
            total_queries = len(self.query_metrics)
            
        with self.system_metrics_lock:
            total_system_metrics = len(self.system_metrics)
        
        return {
            "total_queries_recorded": total_queries,
            "total_system_metrics": total_system_metrics,
            "active_components": len(self.component_metrics),
            "active_backends": len(self.backend_metrics),
            "collection_window_seconds": self.aggregation_window_seconds,
            "max_query_history": self.max_query_history,
            "cache_ttl_seconds": self.cache_ttl_seconds
        }