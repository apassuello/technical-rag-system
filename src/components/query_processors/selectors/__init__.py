"""
Context Selector Sub-components.

This module contains implementations of ContextSelector for choosing
optimal documents from retrieval results within token constraints.

Available Selectors:
- MMRSelector: Maximal Marginal Relevance for balancing relevance and diversity
- TokenLimitSelector: Strict token management with optimal packing
- DiversitySelector: Focus on document diversity over pure relevance (future)
"""

from ..base import ContextSelector, ContextSelection
from .base_selector import BaseContextSelector
from .mmr_selector import MMRSelector
from .token_limit_selector import TokenLimitSelector

# Future implementations
# from .diversity_selector import DiversitySelector

__all__ = [
    'ContextSelector',
    'ContextSelection',
    'BaseContextSelector',
    'MMRSelector',
    'TokenLimitSelector',
    # 'DiversitySelector'
]