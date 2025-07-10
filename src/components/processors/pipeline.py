"""
Document Processing Pipeline Implementation.

This module implements the ProcessingPipeline interface to orchestrate
the flow of document processing through parsing, chunking, and cleaning
stages. It coordinates sub-components and handles error recovery.

Key Features:
- Sequential processing pipeline (parse → chunk → clean)
- Error handling with graceful degradation options
- Performance monitoring and metrics collection
- Configurable validation and quality controls
- Comprehensive logging and debugging support

Architecture Notes:
- Implements ProcessingPipeline abstract base class
- Orchestrates DocumentParser, TextChunker, and ContentCleaner
- Provides centralized error handling and metrics
- Supports different processing strategies (fail-fast vs. graceful)
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.core.interfaces import Document
from .base import ProcessingPipeline, DocumentParser, TextChunker, ContentCleaner, ValidationResult, ConfigurableComponent


class DocumentProcessingPipeline(ProcessingPipeline, ConfigurableComponent):
    """
    Orchestrates document processing through multiple stages.
    
    This pipeline coordinates the three main processing stages:
    1. Document Parsing - Extract text and metadata from files
    2. Text Chunking - Split text into retrieval-sized chunks
    3. Content Cleaning - Normalize and clean text content
    
    Features:
    - Sequential processing with error handling
    - Performance metrics for each stage
    - Configurable quality controls
    - Graceful degradation on errors
    - Comprehensive validation
    
    Configuration Options:
    - enable_validation: Validate documents before processing
    - enable_metrics: Collect detailed performance metrics
    - fail_fast: Stop on first error vs. continue processing
    - skip_cleaning: Skip cleaning stage for faster processing
    - quality_threshold: Minimum quality score for chunk inclusion
    """
    
    def __init__(
        self, 
        parser: DocumentParser,
        chunker: TextChunker,
        cleaner: ContentCleaner,
        config: Dict[str, Any] = None
    ):
        """
        Initialize the processing pipeline.
        
        Args:
            parser: Document parser instance
            chunker: Text chunker instance
            cleaner: Content cleaner instance
            config: Pipeline configuration
        """
        self.parser = parser
        self.chunker = chunker
        self.cleaner = cleaner
        
        # Default configuration
        self.config = {
            'enable_validation': True,
            'enable_metrics': True,
            'fail_fast': False,
            'skip_cleaning': False,
            'quality_threshold': 0.0,
            'max_chunks_per_document': 1000,
            'enable_debug_logging': False
        }
        
        # Apply provided configuration
        if config:
            self.config.update(config)
        
        # Pipeline metrics
        self.metrics = {
            'documents_processed': 0,
            'total_pipeline_time': 0.0,
            'stage_times': {
                'parsing': 0.0,
                'chunking': 0.0,
                'cleaning': 0.0,
                'validation': 0.0
            },
            'stage_calls': {
                'parsing': 0,
                'chunking': 0,
                'cleaning': 0,
                'validation': 0
            },
            'errors': {
                'parsing_errors': 0,
                'chunking_errors': 0,
                'cleaning_errors': 0,
                'validation_errors': 0
            },
            'chunks_created': 0,
            'chunks_filtered': 0,
            'average_chunks_per_document': 0.0
        }
    
    def process_document(self, file_path: Path) -> List[Document]:
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
        pipeline_start = time.perf_counter()
        
        try:
            # Stage 1: Document Parsing
            parsed_data = self._parse_document(file_path)
            
            # Stage 2: Text Chunking
            chunks = self._chunk_text(parsed_data, file_path)
            
            # Stage 3: Content Cleaning (optional)
            if not self.config['skip_cleaning']:
                cleaned_chunks = self._clean_chunks(chunks)
            else:
                cleaned_chunks = chunks
            
            # Stage 4: Convert to Document objects
            documents = self._create_documents(cleaned_chunks, parsed_data, file_path)
            
            # Stage 5: Quality filtering
            filtered_documents = self._filter_documents(documents)
            
            # Update metrics
            pipeline_time = time.perf_counter() - pipeline_start
            self._update_pipeline_metrics(filtered_documents, pipeline_time)
            
            return filtered_documents
            
        except Exception as e:
            if self.config['fail_fast']:
                raise
            
            # Graceful degradation - log error and return empty list
            self._log_error(f"Pipeline error for {file_path}: {str(e)}")
            return []
    
    def validate_document(self, file_path: Path) -> ValidationResult:
        """
        Validate document before processing.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            ValidationResult with validation status and messages
        """
        if not self.config['enable_validation']:
            return ValidationResult(valid=True)
        
        validation_start = time.perf_counter()
        
        try:
            errors = []
            warnings = []
            
            # Basic file validation
            if not file_path.exists():
                errors.append(f"File not found: {file_path}")
            
            if not file_path.is_file():
                errors.append(f"Path is not a file: {file_path}")
            
            # Format validation
            if file_path.suffix.lower() not in self.parser.supported_formats():
                errors.append(f"Unsupported format: {file_path.suffix}")
            
            # Size validation
            if file_path.exists():
                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                if hasattr(self.parser, 'config') and 'max_file_size_mb' in self.parser.config:
                    max_size = self.parser.config['max_file_size_mb']
                    if file_size_mb > max_size:
                        errors.append(f"File too large: {file_size_mb:.1f}MB > {max_size}MB")
                    elif file_size_mb > max_size * 0.8:
                        warnings.append(f"Large file: {file_size_mb:.1f}MB")
            
            # Permissions validation
            if file_path.exists() and not file_path.stat().st_mode & 0o444:
                errors.append(f"File not readable: {file_path}")
            
            result = ValidationResult(
                valid=len(errors) == 0,
                errors=errors,
                warnings=warnings
            )
            
            # Update metrics
            validation_time = time.perf_counter() - validation_start
            self.metrics['stage_times']['validation'] += validation_time
            self.metrics['stage_calls']['validation'] += 1
            
            if not result.valid:
                self.metrics['errors']['validation_errors'] += 1
            
            return result
            
        except Exception as e:
            self.metrics['errors']['validation_errors'] += 1
            return ValidationResult(
                valid=False,
                errors=[f"Validation error: {str(e)}"]
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get processing metrics for monitoring.
        
        Returns:
            Dictionary with processing metrics and statistics
        """
        # Calculate derived metrics
        derived_metrics = {}
        
        if self.metrics['stage_calls']['parsing'] > 0:
            derived_metrics['average_parsing_time'] = (
                self.metrics['stage_times']['parsing'] / self.metrics['stage_calls']['parsing']
            )
        
        if self.metrics['stage_calls']['chunking'] > 0:
            derived_metrics['average_chunking_time'] = (
                self.metrics['stage_times']['chunking'] / self.metrics['stage_calls']['chunking']
            )
        
        if self.metrics['stage_calls']['cleaning'] > 0:
            derived_metrics['average_cleaning_time'] = (
                self.metrics['stage_times']['cleaning'] / self.metrics['stage_calls']['cleaning']
            )
        
        if self.metrics['documents_processed'] > 0:
            derived_metrics['average_pipeline_time'] = (
                self.metrics['total_pipeline_time'] / self.metrics['documents_processed']
            )
            
            self.metrics['average_chunks_per_document'] = (
                self.metrics['chunks_created'] / self.metrics['documents_processed']
            )
        
        # Combine base and derived metrics
        result = self.metrics.copy()
        result['derived_metrics'] = derived_metrics
        
        return result
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the pipeline with provided settings.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate configuration
        valid_keys = {
            'enable_validation', 'enable_metrics', 'fail_fast', 
            'skip_cleaning', 'quality_threshold', 'max_chunks_per_document',
            'enable_debug_logging'
        }
        
        invalid_keys = set(config.keys()) - valid_keys
        if invalid_keys:
            raise ValueError(f"Invalid configuration keys: {invalid_keys}")
        
        # Validate specific values
        if 'quality_threshold' in config:
            if not isinstance(config['quality_threshold'], (int, float)) or not 0 <= config['quality_threshold'] <= 1:
                raise ValueError("quality_threshold must be a float between 0 and 1")
        
        if 'max_chunks_per_document' in config:
            if not isinstance(config['max_chunks_per_document'], int) or config['max_chunks_per_document'] <= 0:
                raise ValueError("max_chunks_per_document must be a positive integer")
        
        # Update configuration
        self.config.update(config)
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration.
        
        Returns:
            Current configuration dictionary
        """
        return self.config.copy()
    
    def _parse_document(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse document using the configured parser.
        
        Args:
            file_path: Path to document file
            
        Returns:
            Parsed document data
        """
        parse_start = time.perf_counter()
        
        try:
            parsed_data = self.parser.parse(file_path)
            
            # Update metrics
            parse_time = time.perf_counter() - parse_start
            self.metrics['stage_times']['parsing'] += parse_time
            self.metrics['stage_calls']['parsing'] += 1
            
            self._log_debug(f"Parsed {file_path} in {parse_time:.3f}s")
            
            return parsed_data
            
        except Exception as e:
            self.metrics['errors']['parsing_errors'] += 1
            raise IOError(f"Failed to parse document {file_path}: {str(e)}") from e
    
    def _chunk_text(self, parsed_data: Dict[str, Any], file_path: Path) -> List[Dict[str, Any]]:
        """
        Chunk text using the configured chunker.
        
        Args:
            parsed_data: Parsed document data
            file_path: Original file path for metadata
            
        Returns:
            List of text chunks with metadata
        """
        chunk_start = time.perf_counter()
        
        try:
            text = parsed_data.get('text', '')
            if not text:
                raise ValueError("No text found in parsed document")
            
            # Prepare metadata for chunking
            metadata = {
                'source_file': str(file_path),
                'document_metadata': parsed_data.get('metadata', {}),
                'processing_timestamp': time.time()
            }
            
            # Chunk the text
            chunks = self.chunker.chunk(text, metadata)
            
            # Convert Chunk objects to dictionaries for consistency
            chunk_dicts = []
            for chunk in chunks:
                chunk_dict = {
                    'content': chunk.content,
                    'start_pos': chunk.start_pos,
                    'end_pos': chunk.end_pos,
                    'metadata': chunk.metadata
                }
                chunk_dicts.append(chunk_dict)
            
            # Limit chunks if configured
            if len(chunk_dicts) > self.config['max_chunks_per_document']:
                chunk_dicts = chunk_dicts[:self.config['max_chunks_per_document']]
                self._log_debug(f"Limited chunks to {self.config['max_chunks_per_document']} for {file_path}")
            
            # Update metrics
            chunk_time = time.perf_counter() - chunk_start
            self.metrics['stage_times']['chunking'] += chunk_time
            self.metrics['stage_calls']['chunking'] += 1
            
            self._log_debug(f"Created {len(chunk_dicts)} chunks in {chunk_time:.3f}s")
            
            return chunk_dicts
            
        except Exception as e:
            self.metrics['errors']['chunking_errors'] += 1
            raise ValueError(f"Failed to chunk text: {str(e)}") from e
    
    def _clean_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean chunk content using the configured cleaner.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            List of cleaned chunk dictionaries
        """
        clean_start = time.perf_counter()
        
        try:
            cleaned_chunks = []
            
            for chunk in chunks:
                content = chunk.get('content', '')
                if not content:
                    continue
                
                # Clean the content
                cleaned_content = self.cleaner.clean(content)
                
                # Update chunk with cleaned content
                cleaned_chunk = chunk.copy()
                cleaned_chunk['content'] = cleaned_content
                cleaned_chunk['metadata'] = chunk.get('metadata', {}).copy()
                cleaned_chunk['metadata']['cleaned'] = True
                cleaned_chunk['metadata']['original_length'] = len(content)
                cleaned_chunk['metadata']['cleaned_length'] = len(cleaned_content)
                
                cleaned_chunks.append(cleaned_chunk)
            
            # Update metrics
            clean_time = time.perf_counter() - clean_start
            self.metrics['stage_times']['cleaning'] += clean_time
            self.metrics['stage_calls']['cleaning'] += 1
            
            self._log_debug(f"Cleaned {len(cleaned_chunks)} chunks in {clean_time:.3f}s")
            
            return cleaned_chunks
            
        except Exception as e:
            self.metrics['errors']['cleaning_errors'] += 1
            if self.config['fail_fast']:
                raise ValueError(f"Failed to clean chunks: {str(e)}") from e
            else:
                # Return original chunks if cleaning fails
                self._log_error(f"Cleaning failed, using original chunks: {str(e)}")
                return chunks
    
    def _create_documents(
        self, 
        chunks: List[Dict[str, Any]], 
        parsed_data: Dict[str, Any], 
        file_path: Path
    ) -> List[Document]:
        """
        Convert chunks to Document objects.
        
        Args:
            chunks: List of chunk dictionaries
            parsed_data: Original parsed document data
            file_path: Source file path
            
        Returns:
            List of Document objects
        """
        documents = []
        
        for i, chunk in enumerate(chunks):
            content = chunk.get('content', '')
            if not content.strip():
                continue
            
            # Create comprehensive metadata
            metadata = {
                # Source information
                'source': str(file_path),
                'source_name': file_path.name,
                'source_type': file_path.suffix.lower().lstrip('.'),
                
                # Chunk information
                'chunk_index': i,
                'chunk_id': chunk.get('metadata', {}).get('chunk_id', f'chunk_{i}'),
                'start_pos': chunk.get('start_pos', 0),
                'end_pos': chunk.get('end_pos', len(content)),
                
                # Document metadata
                'document_metadata': parsed_data.get('metadata', {}),
                'document_page_count': parsed_data.get('page_count', 0),
                'document_processing_time': parsed_data.get('extraction_time', 0.0),
                
                # Processing metadata
                'processed_by': 'document_processing_pipeline',
                'processing_timestamp': time.time(),
                'pipeline_config': self.config.copy(),
                
                # Quality information
                'quality_score': chunk.get('metadata', {}).get('quality_score', 0.0),
                
                # Preserve any additional metadata from chunk
                **chunk.get('metadata', {})
            }
            
            # Create Document object
            document = Document(
                content=content,
                metadata=metadata,
                embedding=None  # Embeddings will be added later
            )
            
            documents.append(document)
        
        return documents
    
    def _filter_documents(self, documents: List[Document]) -> List[Document]:
        """
        Filter documents based on quality threshold.
        
        Args:
            documents: List of Document objects
            
        Returns:
            List of filtered Document objects
        """
        if self.config['quality_threshold'] <= 0:
            return documents
        
        filtered = []
        filtered_count = 0
        
        for document in documents:
            quality_score = document.metadata.get('quality_score', 0.0)
            if quality_score >= self.config['quality_threshold']:
                filtered.append(document)
            else:
                filtered_count += 1
        
        self.metrics['chunks_filtered'] += filtered_count
        
        if filtered_count > 0:
            self._log_debug(f"Filtered {filtered_count} documents below quality threshold {self.config['quality_threshold']}")
        
        return filtered
    
    def _update_pipeline_metrics(self, documents: List[Document], pipeline_time: float) -> None:
        """
        Update overall pipeline metrics.
        
        Args:
            documents: Processed documents
            pipeline_time: Total pipeline processing time
        """
        self.metrics['documents_processed'] += 1
        self.metrics['total_pipeline_time'] += pipeline_time
        self.metrics['chunks_created'] += len(documents)
    
    def _log_debug(self, message: str) -> None:
        """
        Log debug message if debug logging is enabled.
        
        Args:
            message: Debug message
        """
        if self.config['enable_debug_logging']:
            print(f"[PIPELINE DEBUG] {message}")
    
    def _log_error(self, message: str) -> None:
        """
        Log error message.
        
        Args:
            message: Error message
        """
        print(f"[PIPELINE ERROR] {message}")