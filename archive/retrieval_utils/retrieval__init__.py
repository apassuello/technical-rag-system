"""
Retrieval utilities for hybrid RAG systems.
Combines dense semantic search with sparse keyword matching.
"""

from .hybrid_search import HybridRetriever

__all__ = ['HybridRetriever']