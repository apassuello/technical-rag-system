"""
Backend adapters for advanced retriever.

This package provides backend adapters for different vector databases
and retrieval services, enabling the advanced retriever to work with
multiple storage solutions.
"""

from .faiss_backend import FAISSBackend
from .weaviate_backend import WeaviateBackend

__all__ = ['FAISSBackend', 'WeaviateBackend']