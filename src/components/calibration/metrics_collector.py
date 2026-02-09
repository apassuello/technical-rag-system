"""
Metrics collector for the calibration system.

This module provides backward compatibility by re-exporting the metrics collector
from the shared utilities module. The actual implementation has been moved to
src.shared_utils.metrics for system-wide reusability.

DEPRECATION NOTICE: This module is maintained for backward compatibility.
New code should import directly from src.shared_utils.metrics.

Usage:
    from src.components.calibration.metrics_collector import MetricsCollector, QueryMetrics
    
    # This is equivalent to:
    # from src.shared_utils.metrics import MetricsCollector, QueryMetrics
"""

import logging
import warnings

from src.shared_utils.metrics import CalibrationQueryMetrics

# Import from shared utilities for backward compatibility
from src.shared_utils.metrics import MetricsCollector as _MetricsCollector
from src.shared_utils.metrics import QueryMetrics as _QueryMetrics

logger = logging.getLogger(__name__)

# Issue deprecation warning when this module is imported
warnings.warn(
    "Importing from src.components.calibration.metrics_collector is deprecated. "
    "Please use src.shared_utils.metrics instead.",
    DeprecationWarning,
    stacklevel=2
)

# Create wrapper class that uses local logger for backward compatibility
class MetricsCollector(_MetricsCollector):
    """Wrapper class that ensures logging works with backward compatible import path."""

    def start_query_collection(self, query_id: str, query_text: str):
        """Start collecting metrics for a query."""
        result = super().start_query_collection(query_id, query_text)
        logger.debug(f"Started metrics collection for query: {query_id}")
        return result

    def collect_retrieval_metrics(self, query_metrics, retrieval_results, **kwargs):
        """Collect retrieval-specific metrics."""
        super().collect_retrieval_metrics(query_metrics, retrieval_results, **kwargs)
        logger.debug(f"Collected retrieval metrics for {query_metrics.query_id}")

    def collect_generation_metrics(self, query_metrics, answer, confidence_score, generation_time, **kwargs):
        """Collect answer generation metrics."""
        super().collect_generation_metrics(query_metrics, answer, confidence_score, generation_time, **kwargs)
        logger.debug(f"Collected generation metrics for {query_metrics.query_id}")

    def collect_validation_results(self, query_metrics, expected_behavior, actual_results):
        """Collect validation results against expected behavior."""
        super().collect_validation_results(query_metrics, expected_behavior, actual_results)
        meets_expectations = query_metrics.validation_results.get("meets_expectations", False)
        logger.debug(f"Collected validation results for {query_metrics.query_id}: {'PASS' if meets_expectations else 'FAIL'}")

    def export_metrics(self, output_path):
        """Export collected metrics to JSON file."""
        try:
            super().export_metrics(output_path)
            logger.info(f"Exported metrics to {output_path}")
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")

# Re-export for backward compatibility
QueryMetrics = _QueryMetrics

# Also export the base data class for completeness
__all__ = ['MetricsCollector', 'QueryMetrics', 'CalibrationQueryMetrics']

# Log the compatibility layer activation
logger.info("Using compatibility layer for calibration metrics collector. "
           "Consider updating imports to use src.shared_utils.metrics")