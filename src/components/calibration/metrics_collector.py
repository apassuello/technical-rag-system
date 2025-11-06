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

# Import from shared utilities for backward compatibility
from src.shared_utils.metrics import (
    MetricsCollector as _MetricsCollector,
    QueryMetrics as _QueryMetrics,
    CalibrationQueryMetrics
)

logger = logging.getLogger(__name__)

# Issue deprecation warning when this module is imported
warnings.warn(
    "Importing from src.components.calibration.metrics_collector is deprecated. "
    "Please use src.shared_utils.metrics instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export for backward compatibility
MetricsCollector = _MetricsCollector
QueryMetrics = _QueryMetrics

# Also export the base data class for completeness
__all__ = ['MetricsCollector', 'QueryMetrics', 'CalibrationQueryMetrics']

# Log the compatibility layer activation
logger.info("Using compatibility layer for calibration metrics collector. "
           "Consider updating imports to use src.shared_utils.metrics")