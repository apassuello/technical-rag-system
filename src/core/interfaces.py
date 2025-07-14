"""
Core interfaces for the modular RAG system.

This module defines abstract base classes and data structures that form
the foundation of the modular architecture. All component implementations
must inherit from these interfaces to ensure compatibility and testability.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


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


class DocumentProcessor(ABC):
    """Interface for document processing strategies.

    Implementations should handle different file formats and
    convert them into a list of Document chunks.
    """

    @abstractmethod
    def process(self, file_path: Path) -> List[Document]:
        """Process a document into chunks.

        Args:
            file_path: Path to the document file

        Returns:
            List of Document chunks

        Raises:
            ValueError: If file format is not supported
            IOError: If file cannot be read
        """
        pass

    @abstractmethod
    def supported_formats(self) -> List[str]:
        """Return list of supported file extensions.

        Returns:
            List of extensions (e.g., ['.pdf', '.txt'])
        """
        pass


class Embedder(ABC):
    """Interface for embedding generation.

    Implementations should convert text into numerical vectors
    suitable for similarity search.
    """

    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (same length as input)

        Raises:
            ValueError: If texts is empty
        """
        pass

    @abstractmethod
    def embedding_dim(self) -> int:
        """Return the dimension of embeddings.

        Returns:
            Integer dimension (e.g., 384, 768)
        """
        pass


class VectorStore(ABC):
    """Interface for vector storage backends.

    Implementations should provide efficient storage and
    similarity search for document embeddings.
    """

    @abstractmethod
    def add(self, documents: List[Document]) -> None:
        """Add documents to the store.

        Args:
            documents: List of documents with embeddings

        Raises:
            ValueError: If documents don't have embeddings
        """
        pass

    @abstractmethod
    def search(self, query_embedding: List[float], k: int = 5) -> List[RetrievalResult]:
        """Search for similar documents.

        Args:
            query_embedding: Query vector
            k: Number of results to return

        Returns:
            List of retrieval results sorted by score (descending)

        Raises:
            ValueError: If k <= 0 or query_embedding is invalid
        """
        pass

    @abstractmethod
    def delete(self, doc_ids: List[str]) -> None:
        """Delete documents by ID.

        Args:
            doc_ids: List of document IDs to delete

        Raises:
            KeyError: If document ID not found
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all documents from the store."""
        pass


class Retriever(ABC):
    """Interface for retrieval strategies.

    Implementations can use different approaches like
    semantic search, BM25, or hybrid methods.
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


class AnswerGenerator(ABC):
    """Interface for answer generation.

    Implementations can use different models and strategies
    for generating answers from context documents.
    """

    @abstractmethod
    def generate(self, query: str, context: List[Document]) -> Answer:
        """Generate answer from query and context.

        Args:
            query: User question
            context: List of relevant documents

        Returns:
            Generated answer with metadata

        Raises:
            ValueError: If query is empty or context is None
        """
        pass


@dataclass
class QueryOptions:
    """Query processing options.

    Attributes:
        k: Number of documents to retrieve
        rerank: Whether to apply reranking
        max_tokens: Maximum tokens for context
        temperature: LLM temperature setting
        stream: Whether to stream responses
    """

    k: int = 5
    rerank: bool = True
    max_tokens: int = 2048
    temperature: float = 0.7
    stream: bool = False


class QueryProcessor(ABC):
    """Interface for query processing workflow.

    Implementations orchestrate the complete query workflow:
    analyze → retrieve → select → generate → assemble.
    """

    @abstractmethod
    def process(self, query: str, options: Optional[QueryOptions] = None) -> Answer:
        """Process a query end-to-end and return a complete answer.

        Args:
            query: User query string
            options: Optional query processing options

        Returns:
            Complete Answer object with text, sources, and metadata

        Raises:
            ValueError: If query is empty or options are invalid
            RuntimeError: If processing pipeline fails
        """
        pass

    @abstractmethod
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query characteristics without full processing.

        Args:
            query: User query string

        Returns:
            Dictionary with query analysis results
        """
        pass
