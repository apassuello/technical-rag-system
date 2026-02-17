"""
Shared data models for metrics collection across the RAG system.

Contains common data structures used by different metrics collectors
for consistent metric representation and interoperability.
"""

import logging
import time
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class BaseQueryMetrics(ABC):
    """Base query metrics structure with common fields."""
    query_id: str
    query_text: str
    timestamp: Union[str, float] = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    def get_timestamp_float(self) -> float:
        """Get timestamp as float for calculations."""
        if isinstance(self.timestamp, str):
            try:
                return datetime.fromisoformat(self.timestamp).timestamp()
            except ValueError:
                return time.time()
        return self.timestamp


@dataclass
class CalibrationQueryMetrics(BaseQueryMetrics):
    """
    Query metrics for calibration system following calibration-system-spec.md structure.

    Extends BaseQueryMetrics with calibration-specific metrics for parameter optimization
    and confidence calibration.
    """

    # Retrieval metrics
    retrieval_metrics: Dict[str, Any] = field(default_factory=dict)

    # Generation metrics
    generation_metrics: Dict[str, Any] = field(default_factory=dict)

    # Validation results
    validation_results: Dict[str, Any] = field(default_factory=dict)

    # Performance metrics
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalyticsQueryMetrics(BaseQueryMetrics):
    """
    Query metrics for analytics dashboard and real-time monitoring.

    Extends BaseQueryMetrics with analytics-specific metrics for dashboard
    visualization and performance monitoring.
    """

    # Latency metrics (milliseconds)
    total_latency: float = 0.0
    dense_retrieval_latency: float = 0.0
    sparse_retrieval_latency: float = 0.0
    graph_retrieval_latency: float = 0.0
    neural_reranking_latency: float = 0.0

    # Quality metrics
    num_results: int = 0
    relevance_scores: List[float] = field(default_factory=list)
    confidence_score: float = 0.0

    # Component usage
    components_used: List[str] = field(default_factory=list)
    backend_used: str = ""

    # Stage timing information
    stage_times: Optional[Dict[str, float]] = None
    stage_count: Optional[int] = None

    # User interaction
    user_id: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class SystemMetrics:
    """System-wide performance metrics for monitoring and analytics."""
    timestamp: float

    # Performance
    queries_per_second: float = 0.0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0

    # Quality
    avg_relevance_score: float = 0.0
    avg_confidence_score: float = 0.0
    success_rate: float = 0.0

    # Resource usage
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0

    # Component status
    active_components: List[str] = field(default_factory=list)
    component_health: Dict[str, str] = field(default_factory=dict)


@dataclass
class SessionMetadata:
    """Session-level metadata for metrics collection."""
    session_id: str = field(
        default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    start_time: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )
    parameter_config: Dict[str, Any] = field(default_factory=dict)
    system_config: Dict[str, Any] = field(default_factory=dict)

    def update(self, metadata: Dict[str, Any]) -> None:
        """Update session metadata with new values."""
        for key, value in metadata.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                # Store unknown metadata in system_config
                self.system_config[key] = value


@dataclass
class ComponentMetrics:
    """Metrics for individual component performance tracking."""
    component_name: str
    total_calls: int = 0
    total_latency: float = 0.0
    error_count: int = 0
    last_used: float = 0.0

    def record_usage(self, latency_ms: float, success: bool = True) -> None:
        """Record a component usage event."""
        self.total_calls += 1
        self.total_latency += latency_ms
        self.last_used = time.time()

        if not success:
            self.error_count += 1

    @property
    def avg_latency(self) -> float:
        """Calculate average latency."""
        return self.total_latency / self.total_calls if self.total_calls > 0 else 0.0

    @property
    def error_rate(self) -> float:
        """Calculate error rate percentage."""
        return (self.error_count / self.total_calls * 100) if self.total_calls > 0 else 0.0

    @property
    def status(self) -> str:
        """Get component health status."""
        error_rate = self.error_rate
        if error_rate < 5:
            return "healthy"
        elif error_rate < 15:
            return "warning"
        else:
            return "error"


class MetricsConverter:
    """Utility class for converting between different metrics formats."""

    @staticmethod
    def calibration_to_analytics(calibration_metrics: CalibrationQueryMetrics) -> AnalyticsQueryMetrics:
        """Convert calibration metrics to analytics format."""
        return AnalyticsQueryMetrics(
            query_id=calibration_metrics.query_id,
            query_text=calibration_metrics.query_text,
            timestamp=calibration_metrics.get_timestamp_float(),
            total_latency=calibration_metrics.performance_metrics.get("total_time", 0.0) * 1000,  # Convert to ms
            confidence_score=calibration_metrics.generation_metrics.get("confidence_score", 0.0),
            num_results=calibration_metrics.retrieval_metrics.get("documents_retrieved", 0),
            # Extract component information if available
            components_used=["calibration"],  # Default component
            backend_used="calibration_system"
        )

    @staticmethod
    def analytics_to_calibration(analytics_metrics: AnalyticsQueryMetrics) -> CalibrationQueryMetrics:
        """Convert analytics metrics to calibration format."""
        timestamp = analytics_metrics.timestamp
        if isinstance(timestamp, float):
            timestamp = datetime.fromtimestamp(timestamp).isoformat()

        return CalibrationQueryMetrics(
            query_id=analytics_metrics.query_id,
            query_text=analytics_metrics.query_text,
            timestamp=timestamp,
            retrieval_metrics={
                "documents_retrieved": analytics_metrics.num_results,
                "retrieval_time": analytics_metrics.dense_retrieval_latency / 1000,  # Convert to seconds
                "relevance_scores": analytics_metrics.relevance_scores
            },
            generation_metrics={
                "confidence_score": analytics_metrics.confidence_score,
                "generation_time": analytics_metrics.total_latency / 1000,  # Convert to seconds
                "backend_used": analytics_metrics.backend_used
            },
            performance_metrics={
                "total_time": analytics_metrics.total_latency / 1000,  # Convert to seconds
                "components_used": analytics_metrics.components_used
            }
        )
