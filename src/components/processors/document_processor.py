"""
Main Document Processor Implementation.

This module implements the primary DocumentProcessor interface that
coordinates all document processing sub-components (parsing, chunking,
cleaning) through a configurable pipeline.

Architecture Notes:
- Implements DocumentProcessor interface from core.interfaces
- Coordinates sub-components via pipeline pattern
- Configuration-driven component selection
- Provides unified interface for document processing
- Includes comprehensive error handling and metrics
"""

import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.core.interfaces import DocumentProcessor as DocumentProcessorInterface, Document, HealthStatus

# Forward declaration to avoid circular import
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.core.platform_orchestrator import PlatformOrchestrator
from .base import ProcessingPipeline, ConfigurableComponent, ValidationResult
from .pipeline import DocumentProcessingPipeline
from .adapters import PyMuPDFAdapter
from .chunkers import SentenceBoundaryChunker
from .cleaners import TechnicalContentCleaner

logger = logging.getLogger(__name__)


class ModularDocumentProcessor(DocumentProcessorInterface, ConfigurableComponent):
    """
    Modular document processor with configurable sub-components.
    
    This processor implements the DocumentProcessor interface while
    providing a modular architecture where parsing, chunking, and
    cleaning strategies can be configured independently.
    
    Features:
    - Configuration-driven component selection
    - Multiple document format support (extensible)
    - Comprehensive error handling and validation
    - Performance metrics and monitoring
    - Pluggable sub-component architecture
    
    Configuration Structure:
    {
        "parser": {
            "type": "pymupdf",
            "config": {...}
        },
        "chunker": {
            "type": "sentence_boundary",
            "config": {...}
        },
        "cleaner": {
            "type": "technical",
            "config": {...}
        }
    }
    """
    
    def __init__(self, config: Dict[str, Any] = None, chunk_size: int = None, chunk_overlap: int = None, **kwargs):
        """
        Initialize the modular document processor.
        
        Args:
            config: Configuration dictionary for all sub-components
            chunk_size: Legacy parameter for chunk size (backwards compatibility)
            chunk_overlap: Legacy parameter for chunk overlap (backwards compatibility)
            **kwargs: Additional legacy parameters for backwards compatibility
        """
        # Default configuration
        self.config = {
            'parser': {
                'type': 'pymupdf',
                'config': {
                    'max_file_size_mb': 100,
                    'preserve_layout': True
                }
            },
            'chunker': {
                'type': 'sentence_boundary',
                'config': {
                    'chunk_size': 1400,
                    'overlap': 200,
                    'quality_threshold': 0.0
                }
            },
            'cleaner': {
                'type': 'technical',
                'config': {
                    'normalize_whitespace': True,
                    'remove_artifacts': True,
                    'preserve_code_blocks': True
                }
            },
            'pipeline': {
                'enable_validation': True,
                'enable_metrics': True,
                'fail_fast': False
            }
        }
        
        # Handle legacy parameters for backwards compatibility
        if chunk_size is not None or chunk_overlap is not None or kwargs:
            # Convert legacy parameters to config format
            legacy_config = {}
            
            if chunk_size is not None:
                legacy_config['chunker'] = {'config': {'chunk_size': chunk_size}}
            
            if chunk_overlap is not None:
                if 'chunker' not in legacy_config:
                    legacy_config['chunker'] = {'config': {}}
                legacy_config['chunker']['config']['overlap'] = chunk_overlap
            
            # Handle other legacy parameters
            for key, value in kwargs.items():
                if key in ['min_chunk_size', 'enable_quality_filtering', 'quality_threshold']:
                    if 'chunker' not in legacy_config:
                        legacy_config['chunker'] = {'config': {}}
                    legacy_config['chunker']['config'][key] = value
                elif key in ['preserve_layout', 'max_file_size_mb', 'extract_images']:
                    if 'parser' not in legacy_config:
                        legacy_config['parser'] = {'config': {}}
                    legacy_config['parser']['config'][key] = value
                elif key in ['normalize_whitespace', 'remove_artifacts', 'preserve_code_blocks']:
                    if 'cleaner' not in legacy_config:
                        legacy_config['cleaner'] = {'config': {}}
                    legacy_config['cleaner']['config'][key] = value
            
            # Merge legacy config first
            self._merge_config(self.config, legacy_config)
        
        # Apply provided configuration
        if config:
            self._merge_config(self.config, config)
        
        # Initialize components
        self.parser = None
        self.chunker = None
        self.cleaner = None
        self.pipeline = None
        
        # Processing metrics
        self.metrics = {
            'documents_processed': 0,
            'total_processing_time': 0.0,
            'total_chunks_created': 0,
            'total_bytes_processed': 0,
            'errors_encountered': 0,
            'validation_failures': 0,
            'component_metrics': {}
        }
        
        # Platform services (initialized via initialize_services)
        self.platform: Optional['PlatformOrchestrator'] = None
        
        # Initialize components
        self._initialize_components()
    
    def process(self, file_path: Path) -> List[Document]:
        """
        Process a document through the complete pipeline.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List of processed Document objects
            
        Raises:
            ValueError: If file format is not supported
            IOError: If file cannot be read
        """
        start_time = time.perf_counter()
        
        try:
            # Validate document
            if self.config['pipeline']['enable_validation']:
                validation_result = self.validate_document(file_path)
                if not validation_result.valid:
                    self.metrics['validation_failures'] += 1
                    raise ValueError(f"Document validation failed: {validation_result.errors}")
            
            # Process through pipeline
            documents = self.pipeline.process_document(file_path)
            
            # Update metrics
            processing_time = time.perf_counter() - start_time
            self._update_metrics(documents, processing_time, file_path)
            
            # Track performance using platform services
            if self.platform:
                self.platform.track_component_performance(
                    self, 
                    "document_processing", 
                    {
                        "success": True, 
                        "processing_time": processing_time, 
                        "file_path": str(file_path),
                        "documents_created": len(documents),
                        "total_chunks": sum(1 for doc in documents if doc.content)
                    }
                )
            
            return documents
            
        except Exception as e:
            self.metrics['errors_encountered'] += 1
            
            # Track failure using platform services
            if self.platform:
                processing_time = time.perf_counter() - start_time
                self.platform.track_component_performance(
                    self, 
                    "document_processing", 
                    {
                        "success": False, 
                        "processing_time": processing_time, 
                        "file_path": str(file_path),
                        "error": str(e)
                    }
                )
            
            if self.config['pipeline']['fail_fast']:
                raise
            
            # Log error and return empty list for graceful degradation
            print(f"Error processing {file_path}: {str(e)}")
            return []
    
    def supported_formats(self) -> List[str]:
        """
        Return list of supported file extensions.
        
        Returns:
            List of supported file extensions
        """
        if self.parser:
            return self.parser.supported_formats()
        return []
    
    def validate_document(self, file_path: Path) -> ValidationResult:
        """
        Validate document before processing.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            ValidationResult with validation status and messages
        """
        if self.pipeline:
            return self.pipeline.validate_document(file_path)
        
        # Fallback validation
        errors = []
        warnings = []
        
        if not file_path.exists():
            errors.append(f"File not found: {file_path}")
        
        if file_path.suffix.lower() not in self.supported_formats():
            errors.append(f"Unsupported file format: {file_path.suffix}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the processor with new settings.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Use platform configuration service if available
        if self.platform:
            self.platform.update_component_configuration(self, config)
        
        # Validate configuration
        self._validate_config(config)
        
        # Update configuration
        self._merge_config(self.config, config)
        
        # Reinitialize components with new configuration
        self._initialize_components()
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration.
        
        Returns:
            Current configuration dictionary
        """
        return self._deep_copy_dict(self.config)
    
    def get_component_info(self) -> Dict[str, Any]:
        """
        Get information about active components.
        
        Returns:
            Dictionary with component information
        """
        return {
            'parser': {
                'type': self.config['parser']['type'],
                'class': self.parser.__class__.__name__ if self.parser else None,
                'supported_formats': self.parser.supported_formats() if self.parser else []
            },
            'chunker': {
                'type': self.config['chunker']['type'],
                'class': self.chunker.__class__.__name__ if self.chunker else None,
                'strategy': self.chunker.get_chunk_strategy() if hasattr(self.chunker, 'get_chunk_strategy') else None
            },
            'cleaner': {
                'type': self.config['cleaner']['type'],
                'class': self.cleaner.__class__.__name__ if self.cleaner else None,
                'quality_factors': self.cleaner.get_quality_factors() if hasattr(self.cleaner, 'get_quality_factors') else []
            },
            'pipeline': {
                'class': self.pipeline.__class__.__name__ if self.pipeline else None,
                'validation_enabled': self.config['pipeline']['enable_validation'],
                'metrics_enabled': self.config['pipeline']['enable_metrics']
            }
        }
    
    # Standard ComponentBase interface implementation
    def initialize_services(self, platform: 'PlatformOrchestrator') -> None:
        """Initialize platform services for the component.
        
        Args:
            platform: PlatformOrchestrator instance providing services
        """
        self.platform = platform
        logger.info("ModularDocumentProcessor initialized with platform services")

    def get_health_status(self) -> HealthStatus:
        """Get the current health status of the component.
        
        Returns:
            HealthStatus object with component health information
        """
        if self.platform:
            return self.platform.check_component_health(self)
        
        # Fallback if platform services not initialized
        is_healthy = True
        issues = []
        
        # Check sub-components
        if not self.parser:
            is_healthy = False
            issues.append("Parser not initialized")
        
        if not self.chunker:
            is_healthy = False
            issues.append("Chunker not initialized")
        
        if not self.cleaner:
            is_healthy = False
            issues.append("Cleaner not initialized")
        
        if not self.pipeline:
            is_healthy = False
            issues.append("Pipeline not initialized")
        
        return HealthStatus(
            is_healthy=is_healthy,
            issues=issues,
            metrics={
                "sub_components": self.get_component_info(),
                "basic_metrics": self.metrics.copy()
            },
            component_name=self.__class__.__name__
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get component-specific metrics.
        
        Returns:
            Dictionary containing component metrics
        """
        if self.platform:
            try:
                component_metrics = self.platform.analytics_service.collect_component_metrics(self)
                return {
                    "component_name": component_metrics.component_name,
                    "component_type": component_metrics.component_type,
                    "success_count": component_metrics.success_count,
                    "error_count": component_metrics.error_count,
                    "resource_usage": component_metrics.resource_usage,
                    "performance_metrics": component_metrics.performance_metrics,
                    "timestamp": component_metrics.timestamp
                }
            except Exception as e:
                # Fallback if platform service fails
                pass
        
        # Fallback if platform services not initialized - use existing method
        # Update component metrics
        if self.config['pipeline']['enable_metrics']:
            self.metrics['component_metrics'] = {
                'parser': self.parser.get_metrics() if hasattr(self.parser, 'get_metrics') else {},
                'chunker': self.chunker.get_metrics() if hasattr(self.chunker, 'get_metrics') else {},
                'cleaner': self.cleaner.get_metrics() if hasattr(self.cleaner, 'get_metrics') else {},
                'pipeline': self.pipeline.get_metrics() if hasattr(self.pipeline, 'get_metrics') else {}
            }
        
        return self.metrics.copy()

    def get_capabilities(self) -> List[str]:
        """Get list of component capabilities.
        
        Returns:
            List of capability strings
        """
        capabilities = [
            "document_processing",
            "multi_format_support",
            "modular_architecture",
            "configurable_pipeline",
            "performance_metrics"
        ]
        
        # Add parser capabilities
        if self.parser and hasattr(self.parser, 'supported_formats'):
            capabilities.extend([f"parser_{fmt}" for fmt in self.parser.supported_formats()])
        
        # Add chunker capabilities
        if self.chunker:
            capabilities.append(f"chunker_{self.config['chunker']['type']}")
        
        # Add cleaner capabilities
        if self.cleaner:
            capabilities.append(f"cleaner_{self.config['cleaner']['type']}")
        
        return capabilities
    
    def _initialize_components(self) -> None:
        """Initialize all sub-components based on configuration."""
        # Initialize parser
        parser_config = self.config['parser']
        if parser_config['type'] == 'pymupdf':
            self.parser = PyMuPDFAdapter(parser_config['config'])
        else:
            raise ValueError(f"Unknown parser type: {parser_config['type']}")
        
        # Initialize chunker
        chunker_config = self.config['chunker']
        if chunker_config['type'] == 'sentence_boundary':
            self.chunker = SentenceBoundaryChunker(chunker_config['config'])
        else:
            raise ValueError(f"Unknown chunker type: {chunker_config['type']}")
        
        # Initialize cleaner
        cleaner_config = self.config['cleaner']
        if cleaner_config['type'] == 'technical':
            self.cleaner = TechnicalContentCleaner(cleaner_config['config'])
        else:
            raise ValueError(f"Unknown cleaner type: {cleaner_config['type']}")
        
        # Initialize pipeline
        self.pipeline = DocumentProcessingPipeline(
            parser=self.parser,
            chunker=self.chunker,
            cleaner=self.cleaner,
            config=self.config['pipeline']
        )
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate configuration structure and values.
        
        Args:
            config: Configuration to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Check required top-level keys
        required_keys = {'parser', 'chunker', 'cleaner'}
        if not all(key in config for key in required_keys):
            missing_keys = required_keys - set(config.keys())
            raise ValueError(f"Missing required configuration keys: {missing_keys}")
        
        # Validate parser configuration
        parser_config = config['parser']
        if 'type' not in parser_config:
            raise ValueError("Parser configuration must include 'type'")
        
        if parser_config['type'] not in ['pymupdf']:
            raise ValueError(f"Unknown parser type: {parser_config['type']}")
        
        # Validate chunker configuration
        chunker_config = config['chunker']
        if 'type' not in chunker_config:
            raise ValueError("Chunker configuration must include 'type'")
        
        if chunker_config['type'] not in ['sentence_boundary']:
            raise ValueError(f"Unknown chunker type: {chunker_config['type']}")
        
        # Validate cleaner configuration
        cleaner_config = config['cleaner']
        if 'type' not in cleaner_config:
            raise ValueError("Cleaner configuration must include 'type'")
        
        if cleaner_config['type'] not in ['technical']:
            raise ValueError(f"Unknown cleaner type: {cleaner_config['type']}")
    
    def _merge_config(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """
        Recursively merge configuration dictionaries.
        
        Args:
            base: Base configuration dictionary (modified in place)
            update: Update configuration dictionary
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _deep_copy_dict(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a deep copy of a dictionary.
        
        Args:
            d: Dictionary to copy
            
        Returns:
            Deep copy of the dictionary
        """
        result = {}
        for key, value in d.items():
            if isinstance(value, dict):
                result[key] = self._deep_copy_dict(value)
            elif isinstance(value, list):
                result[key] = value.copy()
            else:
                result[key] = value
        return result
    
    def _update_metrics(self, documents: List[Document], processing_time: float, file_path: Path) -> None:
        """
        Update processing metrics.
        
        Args:
            documents: Processed documents
            processing_time: Time taken for processing
            file_path: Path to processed file
        """
        self.metrics['documents_processed'] += 1
        self.metrics['total_processing_time'] += processing_time
        self.metrics['total_chunks_created'] += len(documents)
        
        # Calculate bytes processed
        try:
            file_size = file_path.stat().st_size
            self.metrics['total_bytes_processed'] += file_size
        except OSError:
            pass  # File might not exist or be accessible
        
        # Calculate derived metrics
        if self.metrics['total_processing_time'] > 0:
            self.metrics['average_processing_speed'] = (
                self.metrics['total_bytes_processed'] / self.metrics['total_processing_time']
            )
            self.metrics['documents_per_second'] = (
                self.metrics['documents_processed'] / self.metrics['total_processing_time']
            )
        
        if self.metrics['documents_processed'] > 0:
            self.metrics['average_chunks_per_document'] = (
                self.metrics['total_chunks_created'] / self.metrics['documents_processed']
            )


# Factory functions for easier instantiation

def create_pdf_processor(config: Dict[str, Any] = None) -> ModularDocumentProcessor:
    """
    Create a document processor optimized for PDF processing.
    
    Args:
        config: Optional configuration overrides
        
    Returns:
        Configured ModularDocumentProcessor for PDF processing
    """
    default_config = {
        'parser': {
            'type': 'pymupdf',
            'config': {
                'max_file_size_mb': 100,
                'preserve_layout': True,
                'extract_images': False
            }
        },
        'chunker': {
            'type': 'sentence_boundary',
            'config': {
                'chunk_size': 1400,
                'overlap': 200,
                'quality_threshold': 0.0,
                'preserve_sentences': True
            }
        },
        'cleaner': {
            'type': 'technical',
            'config': {
                'normalize_whitespace': True,
                'remove_artifacts': True,
                'preserve_code_blocks': True,
                'preserve_equations': True
            }
        }
    }
    
    if config:
        processor = ModularDocumentProcessor()
        processor._merge_config(default_config, config)
        processor.configure(default_config)
        return processor
    
    return ModularDocumentProcessor(default_config)


def create_fast_processor(config: Dict[str, Any] = None) -> ModularDocumentProcessor:
    """
    Create a document processor optimized for speed.
    
    Args:
        config: Optional configuration overrides
        
    Returns:
        Configured ModularDocumentProcessor optimized for speed
    """
    fast_config = {
        'parser': {
            'type': 'pymupdf',
            'config': {
                'max_file_size_mb': 50,
                'preserve_layout': False,
                'extract_images': False
            }
        },
        'chunker': {
            'type': 'sentence_boundary',
            'config': {
                'chunk_size': 1000,
                'overlap': 100,
                'quality_threshold': 0.3,
                'enable_quality_filtering': False
            }
        },
        'cleaner': {
            'type': 'technical',
            'config': {
                'normalize_whitespace': True,
                'remove_artifacts': False,
                'preserve_code_blocks': False,
                'detect_pii': False
            }
        },
        'pipeline': {
            'enable_validation': False,
            'enable_metrics': False,
            'fail_fast': True
        }
    }
    
    if config:
        processor = ModularDocumentProcessor()
        processor._merge_config(fast_config, config)
        processor.configure(fast_config)
        return processor
    
    return ModularDocumentProcessor(fast_config)


def create_high_quality_processor(config: Dict[str, Any] = None) -> ModularDocumentProcessor:
    """
    Create a document processor optimized for quality.
    
    Args:
        config: Optional configuration overrides
        
    Returns:
        Configured ModularDocumentProcessor optimized for quality
    """
    quality_config = {
        'parser': {
            'type': 'pymupdf',
            'config': {
                'max_file_size_mb': 200,
                'preserve_layout': True,
                'extract_images': True
            }
        },
        'chunker': {
            'type': 'sentence_boundary',
            'config': {
                'chunk_size': 1800,
                'overlap': 300,
                'quality_threshold': 0.5,
                'enable_quality_filtering': True,
                'preserve_sentences': True
            }
        },
        'cleaner': {
            'type': 'technical',
            'config': {
                'normalize_whitespace': True,
                'remove_artifacts': True,
                'preserve_code_blocks': True,
                'preserve_equations': True,
                'detect_pii': True,
                'preserve_technical_formatting': True
            }
        },
        'pipeline': {
            'enable_validation': True,
            'enable_metrics': True,
            'fail_fast': False
        }
    }
    
    if config:
        processor = ModularDocumentProcessor()
        processor._merge_config(quality_config, config)
        processor.configure(quality_config)
        return processor
    
    return ModularDocumentProcessor(quality_config)