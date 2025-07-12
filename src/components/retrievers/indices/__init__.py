"""
Vector Index Sub-components for Modular Retriever Architecture.

This module provides vector index implementations for the ModularUnifiedRetriever.
Includes both direct implementations (FAISS) and adapters for cloud services.
"""

from .base import VectorIndex
from .faiss_index import FAISSIndex

__all__ = ["VectorIndex", "FAISSIndex"]