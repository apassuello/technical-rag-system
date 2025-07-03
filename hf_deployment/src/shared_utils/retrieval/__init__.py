"""
Retrieval utilities for hybrid RAG systems.
Combines dense semantic search with sparse keyword matching.
"""

# Import HybridRetriever with proper error handling
try:
    from .hybrid_search import HybridRetriever
    __all__ = ['HybridRetriever']
except ImportError as e:
    # Handle import errors gracefully for deployment
    print(f"Warning: Could not import HybridRetriever: {e}")
    __all__ = []