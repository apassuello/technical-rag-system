"""
Enhanced Vocabulary Analysis System.

This module provides a modular, future-ready architecture for vocabulary and intent
analysis in query complexity classification. Supports both rule-based and ML-based
approaches through clean abstractions.
"""

from .base import TermClassifier, IntentClassifier
from .vocabulary_analyzer import VocabularyAnalyzer

__all__ = ['TermClassifier', 'IntentClassifier', 'VocabularyAnalyzer']