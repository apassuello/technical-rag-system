"""
Utility modules for Epic 1 Query Analysis.

This package contains shared utilities used by the Epic1QueryAnalyzer
and its sub-components for linguistic analysis and feature extraction.
"""

from .technical_terms import TechnicalTermManager
from .syntactic_parser import SyntacticParser

__all__ = [
    'TechnicalTermManager',
    'SyntacticParser'
]