"""
Calibration system components for systematic parameter optimization.

This package provides the calibration framework specified in
docs/implementation_specs/calibration-system-spec.md for data-driven
parameter optimization and confidence calibration.
"""

from .calibration_manager import CalibrationManager
from .parameter_registry import ParameterRegistry
from .metrics_collector import MetricsCollector
from .optimization_engine import OptimizationEngine

__all__ = [
    "CalibrationManager",
    "ParameterRegistry", 
    "MetricsCollector",
    "OptimizationEngine"
]