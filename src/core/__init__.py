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

# Phase 4: Clean architecture components
from .platform_orchestrator import PlatformOrchestrator
from .query_processor import QueryProcessor
from .component_factory import ComponentFactory

__all__ = [
    # Data types
    'Document',
    'RetrievalResult', 
    'Answer',
    # Interfaces
    'DocumentProcessor',
    'Embedder',
    'VectorStore',
    'Retriever',
    'AnswerGenerator',
    # Phase 4: Clean architecture
    'PlatformOrchestrator',
    'QueryProcessor',
    'ComponentFactory'
]