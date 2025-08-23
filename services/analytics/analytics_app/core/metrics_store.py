"""
Metrics Store for Analytics Service.

This module implements the metrics storage and retrieval system for the
Analytics Service, supporting both in-memory and persistent storage options.

Features:
- High-performance in-memory storage
- Time-series data handling
- Aggregation and analysis functions
- Performance monitoring and SLO tracking
- Usage pattern analysis
- Optional persistence to external systems
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics
import logging
import json
from threading import Lock

import structlog
from .config import get_settings

logger = structlog.get_logger(__name__)


@dataclass
class QueryMetric:
    """
    Individual query metric record.
    
    Attributes:
        timestamp: When the query was processed
        query_id: Unique identifier for the query
        query: The query text (optional, for analysis)
        complexity: Query complexity level
        provider: LLM provider used
        model: Specific model used
        cost_usd: Cost in USD
        processing_time_ms: Total processing time
        response_time_ms: Response generation time
        success: Whether the query was successful
        error_type: Error type if unsuccessful
        metadata: Additional metadata
    """
    timestamp: datetime
    query_id: str
    query: Optional[str]
    complexity: str
    provider: str
    model: str
    cost_usd: float
    processing_time_ms: float
    response_time_ms: float
    success: bool
    error_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """
    Aggregated performance metrics.
    
    Attributes:
        total_requests: Total number of requests
        successful_requests: Number of successful requests
        failed_requests: Number of failed requests
        avg_response_time_ms: Average response time
        p95_response_time_ms: 95th percentile response time
        p99_response_time_ms: 99th percentile response time
        error_rate: Error rate (0.0 to 1.0)
        total_cost_usd: Total cost
        avg_cost_per_request: Average cost per request
        requests_per_second: Requests per second
        slo_compliance: SLO compliance percentage
    """
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    error_rate: float
    total_cost_usd: float
    avg_cost_per_request: float
    requests_per_second: float
    slo_compliance: float


@dataclass
class UsageTrend:
    """
    Usage trend data.
    
    Attributes:
        time_period: Time period identifier
        request_count: Number of requests in period
        avg_response_time: Average response time in period
        error_rate: Error rate in period
        cost_usd: Total cost in period
        complexity_distribution: Distribution of query complexities
        provider_distribution: Distribution of providers used
    """
    time_period: str
    request_count: int
    avg_response_time: float
    error_rate: float
    cost_usd: float
    complexity_distribution: Dict[str, int]
    provider_distribution: Dict[str, int]


class MetricsStore:
    """
    High-performance metrics storage and analysis system.
    
    This class provides:
    - In-memory storage with optional persistence
    - Time-series data handling and aggregation
    - Performance metrics calculation
    - Usage trend analysis
    - SLO compliance monitoring
    - Thread-safe operations
    """
    
    def __init__(self):
        """Initialize the metrics store."""
        self.settings = get_settings()
        
        # Thread-safe storage
        self._lock = Lock()
        
        # In-memory storage
        self._metrics: deque = deque(maxlen=10000)  # Keep last 10k metrics
        self._hourly_aggregates: Dict[str, Dict] = {}  # Hourly pre-aggregated data
        
        # Performance tracking
        self._start_time = datetime.now()
        self._last_cleanup = datetime.now()
        
        # SLO thresholds
        self.slo_response_time_ms = self.settings.slo_response_time_ms
        self.slo_error_rate_threshold = self.settings.slo_error_rate_threshold
        self.slo_availability_threshold = self.settings.slo_availability_threshold
        
        logger.info(
            "Initialized MetricsStore",
            retention_hours=self.settings.metrics_retention_hours,
            slo_response_time_ms=self.slo_response_time_ms,
            slo_error_rate_threshold=self.slo_error_rate_threshold
        )
    
    async def record_query_metric(self, metric: QueryMetric) -> None:
        """
        Record a query metric.
        
        Args:
            metric: QueryMetric instance to record
        """
        try:
            with self._lock:
                self._metrics.append(metric)
                
                # Update hourly aggregates
                hour_key = metric.timestamp.strftime("%Y-%m-%d-%H")
                if hour_key not in self._hourly_aggregates:
                    self._hourly_aggregates[hour_key] = {
                        "request_count": 0,
                        "successful_requests": 0,
                        "failed_requests": 0,
                        "total_cost": 0.0,
                        "total_response_time": 0.0,
                        "response_times": [],
                        "complexity_counts": defaultdict(int),
                        "provider_counts": defaultdict(int),
                        "error_types": defaultdict(int)
                    }
                
                agg = self._hourly_aggregates[hour_key]
                agg["request_count"] += 1
                agg["total_cost"] += metric.cost_usd
                agg["total_response_time"] += metric.response_time_ms
                agg["response_times"].append(metric.response_time_ms)
                agg["complexity_counts"][metric.complexity] += 1
                agg["provider_counts"][f"{metric.provider}/{metric.model}"] += 1
                
                if metric.success:
                    agg["successful_requests"] += 1
                else:
                    agg["failed_requests"] += 1
                    if metric.error_type:
                        agg["error_types"][metric.error_type] += 1
            
            # Periodic cleanup
            await self._periodic_cleanup()
            
            logger.debug(
                "Recorded query metric",
                query_id=metric.query_id,
                complexity=metric.complexity,
                success=metric.success,
                cost=metric.cost_usd
            )
            
        except Exception as e:
            logger.error("Failed to record query metric", error=str(e))
            raise
    
    async def get_performance_metrics(self, hours_back: int = 1) -> PerformanceMetrics:
        """
        Get performance metrics for the specified time period.
        
        Args:
            hours_back: Number of hours to look back
            
        Returns:
            PerformanceMetrics instance
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            with self._lock:
                # Filter metrics by time
                relevant_metrics = [
                    m for m in self._metrics
                    if m.timestamp >= cutoff_time
                ]
            
            if not relevant_metrics:
                return PerformanceMetrics(
                    total_requests=0,
                    successful_requests=0,
                    failed_requests=0,
                    avg_response_time_ms=0.0,
                    p95_response_time_ms=0.0,
                    p99_response_time_ms=0.0,
                    error_rate=0.0,
                    total_cost_usd=0.0,
                    avg_cost_per_request=0.0,
                    requests_per_second=0.0,
                    slo_compliance=100.0
                )
            
            # Calculate metrics
            total_requests = len(relevant_metrics)
            successful_requests = sum(1 for m in relevant_metrics if m.success)
            failed_requests = total_requests - successful_requests
            
            response_times = [m.response_time_ms for m in relevant_metrics]
            avg_response_time = statistics.mean(response_times)
            p95_response_time = self._percentile(response_times, 0.95)
            p99_response_time = self._percentile(response_times, 0.99)
            
            error_rate = failed_requests / total_requests if total_requests > 0 else 0.0
            
            total_cost = sum(m.cost_usd for m in relevant_metrics)
            avg_cost_per_request = total_cost / total_requests if total_requests > 0 else 0.0
            
            # Calculate RPS
            time_span_hours = hours_back
            requests_per_second = total_requests / (time_span_hours * 3600) if time_span_hours > 0 else 0.0
            
            # Calculate SLO compliance
            slo_compliant_requests = sum(
                1 for m in relevant_metrics
                if m.success and m.response_time_ms <= self.slo_response_time_ms
            )
            slo_compliance = (slo_compliant_requests / total_requests * 100) if total_requests > 0 else 100.0
            
            return PerformanceMetrics(
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                avg_response_time_ms=avg_response_time,
                p95_response_time_ms=p95_response_time,
                p99_response_time_ms=p99_response_time,
                error_rate=error_rate,
                total_cost_usd=total_cost,
                avg_cost_per_request=avg_cost_per_request,
                requests_per_second=requests_per_second,
                slo_compliance=slo_compliance
            )
            
        except Exception as e:
            logger.error("Failed to get performance metrics", error=str(e))
            raise
    
    async def get_usage_trends(self, hours_back: int = 24, bucket_hours: int = 1) -> List[UsageTrend]:
        """
        Get usage trends over time.
        
        Args:
            hours_back: Number of hours to analyze
            bucket_hours: Size of time buckets in hours
            
        Returns:
            List of UsageTrend instances
        """
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)
            
            trends = []
            current_time = start_time
            
            while current_time < end_time:
                bucket_end = current_time + timedelta(hours=bucket_hours)
                
                with self._lock:
                    # Filter metrics for this time bucket
                    bucket_metrics = [
                        m for m in self._metrics
                        if current_time <= m.timestamp < bucket_end
                    ]
                
                if bucket_metrics:
                    # Calculate metrics for this bucket
                    request_count = len(bucket_metrics)
                    successful_requests = sum(1 for m in bucket_metrics if m.success)
                    
                    response_times = [m.response_time_ms for m in bucket_metrics]
                    avg_response_time = statistics.mean(response_times)
                    
                    error_rate = (request_count - successful_requests) / request_count
                    total_cost = sum(m.cost_usd for m in bucket_metrics)
                    
                    complexity_dist = defaultdict(int)
                    provider_dist = defaultdict(int)
                    
                    for metric in bucket_metrics:
                        complexity_dist[metric.complexity] += 1
                        provider_dist[f"{metric.provider}/{metric.model}"] += 1
                    
                    trend = UsageTrend(
                        time_period=current_time.isoformat(),
                        request_count=request_count,
                        avg_response_time=avg_response_time,
                        error_rate=error_rate,
                        cost_usd=total_cost,
                        complexity_distribution=dict(complexity_dist),
                        provider_distribution=dict(provider_dist)
                    )
                    
                    trends.append(trend)
                
                current_time = bucket_end
            
            logger.debug("Generated usage trends", 
                        trends_count=len(trends), 
                        hours_back=hours_back,
                        bucket_hours=bucket_hours)
            
            return trends
            
        except Exception as e:
            logger.error("Failed to get usage trends", error=str(e))
            raise
    
    async def get_complexity_analysis(self, hours_back: int = 24) -> Dict[str, Any]:
        """
        Analyze query complexity patterns.
        
        Args:
            hours_back: Number of hours to analyze
            
        Returns:
            Complexity analysis data
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            with self._lock:
                relevant_metrics = [
                    m for m in self._metrics
                    if m.timestamp >= cutoff_time
                ]
            
            if not relevant_metrics:
                return {
                    "complexity_distribution": {},
                    "cost_by_complexity": {},
                    "performance_by_complexity": {},
                    "total_requests": 0
                }
            
            # Analyze by complexity
            complexity_stats = defaultdict(lambda: {
                "count": 0,
                "total_cost": 0.0,
                "response_times": [],
                "success_count": 0
            })
            
            for metric in relevant_metrics:
                stats = complexity_stats[metric.complexity]
                stats["count"] += 1
                stats["total_cost"] += metric.cost_usd
                stats["response_times"].append(metric.response_time_ms)
                if metric.success:
                    stats["success_count"] += 1
            
            # Calculate distributions and performance
            total_requests = len(relevant_metrics)
            complexity_distribution = {}
            cost_by_complexity = {}
            performance_by_complexity = {}
            
            for complexity, stats in complexity_stats.items():
                complexity_distribution[complexity] = stats["count"] / total_requests
                cost_by_complexity[complexity] = stats["total_cost"]
                
                performance_by_complexity[complexity] = {
                    "avg_response_time_ms": statistics.mean(stats["response_times"]),
                    "success_rate": stats["success_count"] / stats["count"],
                    "avg_cost_per_request": stats["total_cost"] / stats["count"],
                    "request_count": stats["count"]
                }
            
            analysis = {
                "complexity_distribution": complexity_distribution,
                "cost_by_complexity": cost_by_complexity,
                "performance_by_complexity": performance_by_complexity,
                "total_requests": total_requests,
                "analysis_period_hours": hours_back,
                "generated_at": datetime.now().isoformat()
            }
            
            logger.debug("Generated complexity analysis", 
                        total_requests=total_requests,
                        complexity_types=list(complexity_distribution.keys()))
            
            return analysis
            
        except Exception as e:
            logger.error("Failed to get complexity analysis", error=str(e))
            raise
    
    async def get_provider_analysis(self, hours_back: int = 24) -> Dict[str, Any]:
        """
        Analyze provider usage patterns.
        
        Args:
            hours_back: Number of hours to analyze
            
        Returns:
            Provider analysis data
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            with self._lock:
                relevant_metrics = [
                    m for m in self._metrics
                    if m.timestamp >= cutoff_time
                ]
            
            if not relevant_metrics:
                return {
                    "provider_distribution": {},
                    "cost_by_provider": {},
                    "performance_by_provider": {},
                    "total_requests": 0
                }
            
            # Analyze by provider/model
            provider_stats = defaultdict(lambda: {
                "count": 0,
                "total_cost": 0.0,
                "response_times": [],
                "success_count": 0
            })
            
            for metric in relevant_metrics:
                provider_key = f"{metric.provider}/{metric.model}"
                stats = provider_stats[provider_key]
                stats["count"] += 1
                stats["total_cost"] += metric.cost_usd
                stats["response_times"].append(metric.response_time_ms)
                if metric.success:
                    stats["success_count"] += 1
            
            # Calculate distributions and performance
            total_requests = len(relevant_metrics)
            provider_distribution = {}
            cost_by_provider = {}
            performance_by_provider = {}
            
            for provider, stats in provider_stats.items():
                provider_distribution[provider] = stats["count"] / total_requests
                cost_by_provider[provider] = stats["total_cost"]
                
                performance_by_provider[provider] = {
                    "avg_response_time_ms": statistics.mean(stats["response_times"]),
                    "success_rate": stats["success_count"] / stats["count"],
                    "avg_cost_per_request": stats["total_cost"] / stats["count"],
                    "request_count": stats["count"]
                }
            
            analysis = {
                "provider_distribution": provider_distribution,
                "cost_by_provider": cost_by_provider,
                "performance_by_provider": performance_by_provider,
                "total_requests": total_requests,
                "analysis_period_hours": hours_back,
                "generated_at": datetime.now().isoformat()
            }
            
            logger.debug("Generated provider analysis",
                        total_requests=total_requests,
                        provider_count=len(provider_distribution))
            
            return analysis
            
        except Exception as e:
            logger.error("Failed to get provider analysis", error=str(e))
            raise
    
    async def _periodic_cleanup(self) -> None:
        """Perform periodic cleanup of old data."""
        now = datetime.now()
        
        # Only cleanup every hour
        if (now - self._last_cleanup).total_seconds() < 3600:
            return
        
        try:
            retention_cutoff = now - timedelta(hours=self.settings.metrics_retention_hours)
            
            with self._lock:
                # Clean up hourly aggregates
                hours_to_remove = [
                    hour_key for hour_key, data in self._hourly_aggregates.items()
                    if datetime.strptime(hour_key, "%Y-%m-%d-%H") < retention_cutoff
                ]
                
                for hour_key in hours_to_remove:
                    del self._hourly_aggregates[hour_key]
            
            self._last_cleanup = now
            
            if hours_to_remove:
                logger.info("Cleaned up old metrics", removed_hours=len(hours_to_remove))
            
        except Exception as e:
            logger.error("Failed to cleanup old metrics", error=str(e))
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = int(percentile * len(sorted_data))
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        
        return sorted_data[index]
    
    async def health_check(self) -> bool:
        """
        Perform health check on the metrics store.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            with self._lock:
                # Check if we can access the metrics
                metrics_count = len(self._metrics)
                aggregates_count = len(self._hourly_aggregates)
            
            # Try to record a test metric
            test_metric = QueryMetric(
                timestamp=datetime.now(),
                query_id="health_check",
                query=None,
                complexity="simple",
                provider="test",
                model="test",
                cost_usd=0.0,
                processing_time_ms=1.0,
                response_time_ms=1.0,
                success=True
            )
            
            # This should work if the store is healthy
            # We'll remove it immediately
            with self._lock:
                original_len = len(self._metrics)
                self._metrics.append(test_metric)
                # Remove the test metric
                if len(self._metrics) > original_len:
                    self._metrics.pop()
            
            logger.debug("Metrics store health check passed",
                        metrics_count=metrics_count,
                        aggregates_count=aggregates_count)
            
            return True
            
        except Exception as e:
            logger.error("Metrics store health check failed", error=str(e))
            return False


# Global instance
_metrics_store: Optional[MetricsStore] = None


def get_metrics_store() -> MetricsStore:
    """
    Get global metrics store instance.
    
    Returns:
        MetricsStore instance
    """
    global _metrics_store
    if _metrics_store is None:
        _metrics_store = MetricsStore()
    return _metrics_store