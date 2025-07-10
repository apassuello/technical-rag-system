"""
Document Processor Components.

This package implements the modular Document Processor component with
configurable sub-components for parsing, chunking, and cleaning.

Public Interface:
- ModularDocumentProcessor: Main document processor implementation
- Factory functions: create_pdf_processor, create_fast_processor, create_high_quality_processor

Sub-Components:
- PyMuPDFAdapter: PDF parsing via PyMuPDF
- SentenceBoundaryChunker: Sentence-aware text chunking
- TechnicalContentCleaner: Technical document cleaning

Legacy Support:
- HybridPDFProcessor: Existing PDF processor for backward compatibility

Architecture:
- Follows adapter pattern for external libraries (PyMuPDF)
- Direct implementation for algorithms (chunking, cleaning)
- Configuration-driven component selection
- Comprehensive error handling and metrics
"""

# Legacy processor (for backward compatibility)
from .pdf_processor import HybridPDFProcessor

# Main document processor
from .document_processor import (
    ModularDocumentProcessor,
    create_pdf_processor,
    create_fast_processor,
    create_high_quality_processor
)

# Pipeline coordinator
from .pipeline import DocumentProcessingPipeline

# Sub-component adapters
from .adapters import PyMuPDFAdapter

# Sub-component implementations
from .chunkers import SentenceBoundaryChunker
from .cleaners import TechnicalContentCleaner

# Base interfaces
from .base import (
    DocumentParser,
    TextChunker,
    ContentCleaner,
    ProcessingPipeline,
    ConfigurableComponent,
    QualityAssessment,
    Chunk,
    ValidationResult
)

__all__ = [
    # Legacy processor
    'HybridPDFProcessor',
    
    # Main processor
    'ModularDocumentProcessor',
    
    # Factory functions
    'create_pdf_processor',
    'create_fast_processor', 
    'create_high_quality_processor',
    
    # Pipeline
    'DocumentProcessingPipeline',
    
    # Sub-components
    'PyMuPDFAdapter',
    'SentenceBoundaryChunker',
    'TechnicalContentCleaner',
    
    # Base interfaces
    'DocumentParser',
    'TextChunker',
    'ContentCleaner',
    'ProcessingPipeline',
    'ConfigurableComponent',
    'QualityAssessment',
    'Chunk',
    'ValidationResult'
]