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

# New architecture components
from .platform_orchestrator import PlatformOrchestrator
from .query_processor import QueryProcessor

# Legacy compatibility
from .pipeline import RAGPipeline

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
    # Registry (Phase 1 - will be removed in Phase 4)
    'ComponentRegistry',
    'register_component',
    'get_available_components',
    # New architecture
    'PlatformOrchestrator',
    'QueryProcessor',
    # Legacy compatibility
    'RAGPipeline'
]