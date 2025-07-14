"""
Vector Index Sub-components for Modular Retriever Architecture.

This module provides vector index implementations for the ModularUnifiedRetriever.
Includes both direct implementations (FAISS) and adapters for cloud services (Weaviate).
"""

from .base import VectorIndex
from .faiss_index import FAISSIndex
from .weaviate_index import WeaviateIndex

__all__ = ["VectorIndex", "FAISSIndex", "WeaviateIndex"]