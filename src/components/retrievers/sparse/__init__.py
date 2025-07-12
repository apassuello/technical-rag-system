"""
Sparse Retriever Sub-components for Modular Retriever Architecture.

This module provides sparse retrieval implementations for the ModularUnifiedRetriever.
Includes both direct implementations (BM25) and adapters for external services.
"""

from .base import SparseRetriever
from .bm25_retriever import BM25Retriever

__all__ = ["SparseRetriever", "BM25Retriever"]