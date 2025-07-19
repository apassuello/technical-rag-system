"""
Core interfaces for the Epic 2 HF Deployment RAG system.

This module defines abstract base classes and data structures that form
the foundation of the modular architecture for the HF deployment package.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import time

# Forward declaration for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .platform_orchestrator import PlatformOrchestrator


@dataclass
class Document:
    """Represents a processed document chunk.

    Attributes:
        content: The text content of the chunk
        metadata: Additional metadata about the chunk (source, page, etc.)
        embedding: Optional embedding vector for the chunk
    """

    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None

    def __post_init__(self):
        """Validate document data."""
        if not self.content:
            raise ValueError("Document content cannot be empty")
        if self.embedding is not None and not isinstance(self.embedding, list):
            raise TypeError("Embedding must be a list of floats")


@dataclass
class RetrievalResult:
    """Result from a retrieval operation.

    Attributes:
        document: The retrieved document
        score: Relevance score (higher is better)
        retrieval_method: Method used for retrieval (e.g., 'semantic', 'hybrid')
        metadata: Additional metadata about the retrieval process
    """

    document: Document
    score: float
    retrieval_method: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate retrieval result data."""
        if not isinstance(self.document, Document):
            raise TypeError("document must be a Document instance")
        if not 0 <= self.score <= 1:
            raise ValueError("Score must be between 0 and 1")


@dataclass
class Answer:
    """Generated answer with metadata.

    Attributes:
        text: The generated answer text
        sources: List of source documents used
        confidence: Confidence score (0-1)
        metadata: Additional metadata (e.g., generation params)
    """

    text: str
    sources: List[Document]
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate answer data."""
        if not self.text:
            raise ValueError("Answer text cannot be empty")
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        if not isinstance(self.sources, list):
            raise TypeError("Sources must be a list of Documents")


class ComponentBase(ABC):
    """Base interface for all system components.
    
    This interface defines standard methods that all components must implement
    to enable universal platform service access.
    """
    
    @abstractmethod
    def get_health_status(self) -> 'HealthStatus':
        """Get the current health status of the component."""
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Get component-specific metrics."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Get list of component capabilities."""
        pass


class Retriever(ComponentBase):
    """Interface for retrieval strategies.

    Epic 2 retrievers can use neural reranking, graph enhancement,
    and hybrid search methods.
    """

    @abstractmethod
    def retrieve(self, query: str, k: int = 5) -> List[RetrievalResult]:
        """Retrieve relevant documents for a query.

        Args:
            query: Search query string
            k: Number of results to return

        Returns:
            List of retrieval results

        Raises:
            ValueError: If query is empty or k <= 0
        """
        pass


@dataclass
class HealthStatus:
    """Health status information for a component."""
    is_healthy: bool
    last_check: float = field(default_factory=time.time)
    issues: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    component_name: str = ""
    
    def __post_init__(self):
        """Validate health status data."""
        if not isinstance(self.is_healthy, bool):
            raise TypeError("is_healthy must be a boolean")
        if not isinstance(self.issues, list):
            raise TypeError("issues must be a list of strings")