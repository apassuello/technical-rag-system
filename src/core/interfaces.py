"""
Core interfaces for the modular RAG system.

This module defines abstract base classes and data structures that form
the foundation of the modular architecture. All component implementations
must inherit from these interfaces to ensure compatibility and testability.
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
    to enable universal platform service access. Components implementing this
    interface can use platform services for health monitoring, analytics,
    configuration management, and other cross-cutting concerns.
    """
    
    @abstractmethod
    def get_health_status(self) -> 'HealthStatus':
        """Get the current health status of the component.
        
        Returns:
            HealthStatus object with component health information
        """
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Get component-specific metrics.
        
        Returns:
            Dictionary containing component metrics (performance, usage, etc.)
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Get list of component capabilities.
        
        Returns:
            List of capability strings describing what the component can do
        """
        pass
    
    @abstractmethod
    def initialize_services(self, platform: 'PlatformOrchestrator') -> None:
        """Initialize platform services for the component.
        
        Args:
            platform: PlatformOrchestrator instance providing services
        """
        pass


class DocumentProcessor(ComponentBase):
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


class Embedder(ComponentBase):
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


class VectorStore(ComponentBase):
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


class Retriever(ComponentBase):
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


class AnswerGenerator(ComponentBase):
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


class QueryProcessor(ComponentBase):
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


# Platform Orchestrator Service Interfaces
# These interfaces define the system-wide services that ALL components can use

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


@dataclass
class ComponentMetrics:
    """Metrics for a component."""
    component_name: str
    component_type: str
    timestamp: float = field(default_factory=time.time)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    error_count: int = 0
    success_count: int = 0
    
    def __post_init__(self):
        """Validate metrics data."""
        if not self.component_name:
            raise ValueError("component_name cannot be empty")
        if not self.component_type:
            raise ValueError("component_type cannot be empty")


@dataclass
class ExperimentAssignment:
    """Assignment for an A/B test experiment."""
    experiment_id: str
    variant: str
    assignment_time: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate experiment assignment data."""
        if not self.experiment_id:
            raise ValueError("experiment_id cannot be empty")
        if not self.variant:
            raise ValueError("variant cannot be empty")


@dataclass
class ExperimentResult:
    """Result from an A/B test experiment."""
    experiment_id: str
    variant: str
    outcome: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    success: bool = True
    
    def __post_init__(self):
        """Validate experiment result data."""
        if not self.experiment_id:
            raise ValueError("experiment_id cannot be empty")
        if not self.variant:
            raise ValueError("variant cannot be empty")
        if not isinstance(self.outcome, dict):
            raise TypeError("outcome must be a dictionary")


@dataclass
class BackendStatus:
    """Status information for a backend."""
    backend_name: str
    is_available: bool
    last_check: float = field(default_factory=time.time)
    health_metrics: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Validate backend status data."""
        if not self.backend_name:
            raise ValueError("backend_name cannot be empty")
        if not isinstance(self.is_available, bool):
            raise TypeError("is_available must be a boolean")


class ComponentHealthService(ABC):
    """Service interface for component health monitoring."""
    
    @abstractmethod
    def check_component_health(self, component: Any) -> HealthStatus:
        """Check the health of a component.
        
        Args:
            component: Component instance to check
            
        Returns:
            HealthStatus object with health information
        """
        pass
    
    @abstractmethod
    def monitor_component_health(self, component: Any) -> None:
        """Start monitoring a component's health.
        
        Args:
            component: Component instance to monitor
        """
        pass
    
    @abstractmethod
    def report_component_failure(self, component: Any, error: Exception) -> None:
        """Report a component failure.
        
        Args:
            component: Component that failed
            error: Exception that occurred
        """
        pass
    
    @abstractmethod
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get a summary of system health.
        
        Returns:
            Dictionary with system health information
        """
        pass


class SystemAnalyticsService(ABC):
    """Service interface for system analytics collection."""
    
    @abstractmethod
    def collect_component_metrics(self, component: Any) -> ComponentMetrics:
        """Collect metrics from a component.
        
        Args:
            component: Component instance to collect metrics from
            
        Returns:
            ComponentMetrics object with collected metrics
        """
        pass
    
    @abstractmethod
    def aggregate_system_metrics(self) -> Dict[str, Any]:
        """Aggregate metrics across all components.
        
        Returns:
            Dictionary with system-wide metrics
        """
        pass
    
    @abstractmethod
    def track_component_performance(self, component: Any, metrics: Dict[str, Any]) -> None:
        """Track performance metrics for a component.
        
        Args:
            component: Component instance
            metrics: Performance metrics to track
        """
        pass
    
    @abstractmethod
    def generate_analytics_report(self) -> Dict[str, Any]:
        """Generate a comprehensive analytics report.
        
        Returns:
            Dictionary with analytics report
        """
        pass


class ABTestingService(ABC):
    """Service interface for A/B testing."""
    
    @abstractmethod
    def assign_experiment(self, context: Dict[str, Any]) -> ExperimentAssignment:
        """Assign a user to an experiment.
        
        Args:
            context: Context information for assignment
            
        Returns:
            ExperimentAssignment object
        """
        pass
    
    @abstractmethod
    def track_experiment_outcome(self, experiment_id: str, variant: str, outcome: Dict[str, Any]) -> None:
        """Track the outcome of an experiment.
        
        Args:
            experiment_id: Unique experiment identifier
            variant: Variant that was tested
            outcome: Outcome data
        """
        pass
    
    @abstractmethod
    def get_experiment_results(self, experiment_name: str) -> List[ExperimentResult]:
        """Get results for an experiment.
        
        Args:
            experiment_name: Name of the experiment
            
        Returns:
            List of experiment results
        """
        pass
    
    @abstractmethod
    def configure_experiment(self, experiment_config: Dict[str, Any]) -> None:
        """Configure a new experiment.
        
        Args:
            experiment_config: Configuration for the experiment
        """
        pass


class ConfigurationService(ABC):
    """Service interface for configuration management."""
    
    @abstractmethod
    def get_component_config(self, component_name: str) -> Dict[str, Any]:
        """Get configuration for a component.
        
        Args:
            component_name: Name of the component
            
        Returns:
            Dictionary with component configuration
        """
        pass
    
    @abstractmethod
    def update_component_config(self, component_name: str, config: Dict[str, Any]) -> None:
        """Update configuration for a component.
        
        Args:
            component_name: Name of the component
            config: New configuration
        """
        pass
    
    @abstractmethod
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate a configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        pass
    
    @abstractmethod
    def get_system_configuration(self) -> Dict[str, Any]:
        """Get the complete system configuration.
        
        Returns:
            Dictionary with system configuration
        """
        pass


class BackendManagementService(ABC):
    """Service interface for backend management."""
    
    @abstractmethod
    def register_backend(self, backend_name: str, backend_config: Dict[str, Any]) -> None:
        """Register a new backend.
        
        Args:
            backend_name: Name of the backend
            backend_config: Configuration for the backend
        """
        pass
    
    @abstractmethod
    def switch_component_backend(self, component: Any, backend_name: str) -> None:
        """Switch a component to a different backend.
        
        Args:
            component: Component to switch
            backend_name: Name of the target backend
        """
        pass
    
    @abstractmethod
    def get_backend_status(self, backend_name: str) -> BackendStatus:
        """Get status information for a backend.
        
        Args:
            backend_name: Name of the backend
            
        Returns:
            BackendStatus object with status information
        """
        pass
    
    @abstractmethod
    def migrate_component_data(self, component: Any, from_backend: str, to_backend: str) -> None:
        """Migrate component data between backends.
        
        Args:
            component: Component to migrate
            from_backend: Source backend name
            to_backend: Target backend name
        """
        pass
