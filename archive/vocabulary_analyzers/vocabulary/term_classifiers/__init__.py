"""
Term classification implementations.

Provides various approaches for classifying technical terms and assigning
complexity weights based on domain sophistication.
"""

from .rule_based_classifier import RuleBasedTermClassifier

__all__ = ['RuleBasedTermClassifier']