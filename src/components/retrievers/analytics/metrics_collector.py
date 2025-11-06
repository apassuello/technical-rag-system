"""
Real-time Metrics Collection for Advanced Retriever.

CONSOLIDATION NOTICE: This module has been consolidated into the shared metrics framework.
The previous implementation (228 statements, 0% test coverage) has been replaced with
a reference to the unified metrics system.

For analytics and real-time monitoring functionality, use the shared metrics framework:

    from src.shared_utils.metrics import (
        BaseMetricsCollector,
        AnalyticsQueryMetrics,
        SystemMetrics,
        InMemoryMetricsStorage
    )

Rationale for removal:
- 0% test coverage (228 statements untested)
- Minimal usage throughout the codebase
- Duplicate functionality with calibration metrics collector
- Architectural decision to consolidate into shared framework

If you need the original implementation for reference, it can be found in:
git history prior to the metrics consolidation commit.
"""

import logging
import warnings
from src.shared_utils.metrics import BaseMetricsCollector, AnalyticsQueryMetrics, SystemMetrics

logger = logging.getLogger(__name__)

# Issue deprecation warning
warnings.warn(
    "The analytics metrics collector has been consolidated into src.shared_utils.metrics. "
    "Please use the shared metrics framework for analytics functionality.",
    DeprecationWarning,
    stacklevel=2
)


class MetricsCollector(BaseMetricsCollector):
    """
    DEPRECATED: Analytics metrics collector consolidated into shared framework.
    
    This stub provides basic compatibility but new code should use:
    src.shared_utils.metrics.BaseMetricsCollector with AnalyticsQueryMetrics
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__()
        logger.warning(
            "Analytics MetricsCollector is deprecated. "
            "Use src.shared_utils.metrics.BaseMetricsCollector instead."
        )
    
    def start_query_collection(self, query_id: str, query_text: str):
        return AnalyticsQueryMetrics(query_id=query_id, query_text=query_text)
    
    def collect_performance_metrics(self, query_metrics, total_time: float, **kwargs):
        query_metrics.total_latency = total_time * 1000  # Convert to ms
    
    def calculate_aggregate_metrics(self):
        return {"deprecated": True, "use_shared_framework": True}
    
    def get_metrics_summary(self):
        return "DEPRECATED: Use src.shared_utils.metrics framework"