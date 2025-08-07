"""
ML Views Framework for Epic 1 Multi-View Query Complexity Analyzer.

This module provides the framework for implementing hybrid algorithmic+ML views
that analyze different aspects of query complexity.

Components:
- BaseView: Abstract base for all view implementations
- AlgorithmicView: Fast algorithmic-only analysis
- MLView: ML-primary analysis with algorithmic fallback
- HybridView: Balanced algorithmic + ML combination
- ViewResult: Standardized result format
- ViewOrchestrator: Parallel execution and aggregation
- ErrorHandler: Comprehensive error handling and fallbacks
"""

from .base_view import BaseView, AlgorithmicView, MLView, HybridView
from .view_result import ViewResult, AnalysisResult
from .view_orchestrator import ViewOrchestrator
from .error_handling import ViewErrorHandler

__all__ = [
    'BaseView',
    'AlgorithmicView', 
    'MLView',
    'HybridView',
    'ViewResult',
    'AnalysisResult',
    'ViewOrchestrator',
    'ViewErrorHandler'
]