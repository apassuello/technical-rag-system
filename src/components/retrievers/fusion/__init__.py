"""
Fusion Strategy Sub-components for Modular Retriever Architecture.

This module provides fusion strategy implementations for the ModularUnifiedRetriever.
All fusion strategies are direct implementations as they implement pure algorithms.
"""

from .base import FusionStrategy
from .rrf_fusion import RRFFusion
from .weighted_fusion import WeightedFusion

__all__ = ["FusionStrategy", "RRFFusion", "WeightedFusion"]