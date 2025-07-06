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

__all__ = [
    'Document',
    'RetrievalResult', 
    'Answer',
    'DocumentProcessor',
    'Embedder',
    'VectorStore',
    'Retriever',
    'AnswerGenerator'
]