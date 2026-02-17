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

from .base_view import AlgorithmicView, BaseView, HybridView, MLView
from .computational_complexity_view import ComputationalComplexityView
from .linguistic_complexity_view import LinguisticComplexityView
from .semantic_complexity_view import SemanticComplexityView
from .task_complexity_view import TaskComplexityView

# Import individual views
from .technical_complexity_view import TechnicalComplexityView
from .view_result import AnalysisResult, ViewResult

__all__ = [
    'BaseView',
    'AlgorithmicView',
    'MLView',
    'HybridView',
    'ViewResult',
    'AnalysisResult',
    'TechnicalComplexityView',
    'LinguisticComplexityView',
    'TaskComplexityView',
    'SemanticComplexityView',
    'ComputationalComplexityView'
]
