"""
Base interfaces for Document Processor sub-components.

This module defines the abstract base classes that all Document Processor
sub-components must implement, following the modular architecture specification.
These interfaces ensure consistent behavior across different implementations
while enabling pluggable, testable components.

Architecture Reference:
- COMPONENT-2-DOCUMENT-PROCESSOR.md section 3.2 (Sub-Components)
- rag-interface-reference.md section 3.1 (Document Processing Sub-Components)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path


# --- Data Classes ---

@dataclass
class Chunk:
    """Text chunk with position and metadata information."""
    content: str
    start_pos: int
    end_pos: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate chunk data."""
        if not self.content:
            raise ValueError("Chunk content cannot be empty")
        if self.start_pos < 0:
            raise ValueError("Chunk start_pos must be non-negative")
        if self.end_pos <= self.start_pos:
            raise ValueError("Chunk end_pos must be greater than start_pos")


@dataclass
class ValidationResult:
    """Result of document validation operation."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Ensure consistency between valid flag and errors."""
        if not self.valid and not self.errors:
            raise ValueError("Invalid validation result must have errors")


# --- Abstract Base Classes ---

class DocumentParser(ABC):
    """
    Abstract base class for document parsers.
    
    Document parsers are responsible for extracting text and structure from
    various document formats. They use the adapter pattern for external
    libraries (PyMuPDF, python-docx, etc.) to provide a consistent interface.
    
    Implementation Guidelines:
    - Use adapters for external parsing libraries
    - Preserve document structure and metadata
    - Handle format-specific extraction requirements
    - Provide graceful error handling for corrupted documents
    """
    
    @abstractmethod
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse document and extract content and structure.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary containing:
            - 'text': Full document text
            - 'metadata': Document metadata (title, author, etc.)
            - 'pages': List of page-level data (if applicable)
            - 'structure': Document structure information
            
        Raises:
            ValueError: If file format is not supported
            IOError: If file cannot be read or is corrupted
        """
        pass
    
    @abstractmethod
    def extract_metadata(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract document metadata from parsed document.
        
        Args:
            document: Parsed document data
            
        Returns:
            Dictionary containing document metadata
        """
        pass
    
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """
        Return list of supported file extensions.
        
        Returns:
            List of file extensions (e.g., ['.pdf', '.docx'])
        """
        pass


class TextChunker(ABC):
    """
    Abstract base class for text chunking strategies.
    
    Text chunkers split documents into semantic chunks suitable for retrieval.
    They implement direct algorithms (no external dependencies) for various
    chunking strategies like sentence-boundary, semantic, or structural chunking.
    
    Implementation Guidelines:
    - Direct implementation (no adapters for algorithms)
    - Preserve semantic boundaries
    - Configurable chunk size and overlap
    - Quality filtering for low-value content
    """
    
    @abstractmethod
    def chunk(self, text: str, metadata: Dict[str, Any]) -> List[Chunk]:
        """
        Split text into semantic chunks.
        
        Args:
            text: Input text to be chunked
            metadata: Document metadata to preserve in chunks
            
        Returns:
            List of Chunk objects with content and metadata
            
        Raises:
            ValueError: If text is empty or invalid
        """
        pass
    
    @abstractmethod
    def get_chunk_strategy(self) -> str:
        """
        Return the chunking strategy identifier.
        
        Returns:
            Strategy name (e.g., 'sentence_boundary', 'semantic')
        """
        pass


class ContentCleaner(ABC):
    """
    Abstract base class for content cleaning strategies.
    
    Content cleaners normalize and clean text content for better retrieval
    and generation quality. They implement direct algorithms for various
    cleaning strategies like technical content preservation, PII detection,
    or language-specific normalization.
    
    Implementation Guidelines:
    - Direct implementation (no adapters for algorithms)
    - Preserve important technical content
    - Configurable cleaning strategies
    - Handle domain-specific requirements
    """
    
    @abstractmethod
    def clean(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Input text to be cleaned
            
        Returns:
            Cleaned text with normalized formatting
            
        Raises:
            ValueError: If text is None or invalid
        """
        pass
    
    @abstractmethod
    def normalize(self, text: str) -> str:
        """
        Normalize text formatting and structure.
        
        Args:
            text: Input text to normalize
            
        Returns:
            Normalized text with consistent formatting
        """
        pass
    
    @abstractmethod
    def remove_pii(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Remove personally identifiable information from text.
        
        Args:
            text: Input text potentially containing PII
            
        Returns:
            Tuple of (cleaned_text, detected_pii_entities)
            
        Note:
            This method may be a placeholder in initial implementations
            and can be enhanced later with proper PII detection.
        """
        pass


# --- Pipeline Interfaces ---

class ProcessingPipeline(ABC):
    """
    Abstract base class for document processing pipelines.
    
    Processing pipelines orchestrate the flow of document processing
    through parsing, chunking, and cleaning stages. They coordinate
    the sub-components and handle configuration-driven behavior.
    """
    
    @abstractmethod
    def process_document(self, file_path: Path) -> List['Document']:
        """
        Process a document through the complete pipeline.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List of processed Document objects
            
        Raises:
            ValueError: If document format is not supported
            IOError: If document cannot be processed
        """
        pass
    
    @abstractmethod
    def validate_document(self, file_path: Path) -> ValidationResult:
        """
        Validate document before processing.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            ValidationResult with validation status and messages
        """
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get processing metrics for monitoring.
        
        Returns:
            Dictionary with processing metrics and statistics
        """
        pass


# --- Configuration Interfaces ---

class ConfigurableComponent(ABC):
    """
    Abstract base class for configurable components.
    
    Components that can be configured through YAML configuration
    should implement this interface to ensure consistent configuration
    handling across the system.
    """
    
    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure component with provided configuration.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration.
        
        Returns:
            Current configuration dictionary
        """
        pass


# --- Quality Interfaces ---

class QualityAssessment(ABC):
    """
    Abstract base class for quality assessment components.
    
    Components that assess content quality should implement this
    interface to provide consistent quality metrics.
    """
    
    @abstractmethod
    def assess_quality(self, content: str) -> float:
        """
        Assess the quality of content.
        
        Args:
            content: Content to assess
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        pass
    
    @abstractmethod
    def get_quality_factors(self) -> List[str]:
        """
        Get list of quality factors considered.
        
        Returns:
            List of quality factor names
        """
        pass