"""Core abstractions for the modular RAG system."""

from .component_factory import ComponentFactory
from .interfaces import (
    Answer,
    AnswerGenerator,
    Document,
    DocumentProcessor,
    Embedder,
    RetrievalResult,
    Retriever,
    VectorStore,
)

# Phase 4: Clean architecture components
from .platform_orchestrator import PlatformOrchestrator
from .query_processor import QueryProcessor

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