"""Core abstractions for the modular RAG system."""

from .interfaces import (
    Document,
    RetrievalResult,
    Answer,
    DocumentProcessor,
    Embedder,
    VectorStore,
    Retriever,
    AnswerGenerator
)

from .registry import (
    ComponentRegistry,
    register_component,
    get_available_components
)

__all__ = [
    'Document',
    'RetrievalResult', 
    'Answer',
    'DocumentProcessor',
    'Embedder',
    'VectorStore',
    'Retriever',
    'AnswerGenerator',
    'ComponentRegistry',
    'register_component',
    'get_available_components'
]