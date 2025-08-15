"""
Intent classification implementations.

Provides various approaches for analyzing query intent to determine cognitive
complexity independent of technical vocabulary.
"""

from .rule_based_intent import RuleBasedIntentClassifier

__all__ = ['RuleBasedIntentClassifier']