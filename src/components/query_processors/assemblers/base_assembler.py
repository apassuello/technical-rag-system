"""
Base Response Assembler Implementation.

This module provides concrete base functionality for response assembly
components, implementing common patterns for Answer object creation and metadata handling.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from ..base import ResponseAssembler, ContextSelection, QueryAnalysis
from src.core.interfaces import Answer, Document

logger = logging.getLogger(__name__)


class BaseResponseAssembler(ResponseAssembler):
    """
    Base implementation providing common functionality for all response assemblers.
    
    This class implements common patterns like Answer object creation,
    metadata handling, and performance tracking that can be reused by
    concrete assembler implementations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize base response assembler with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self._config = config or {}
        self._performance_metrics = {
            'total_assemblies': 0,
            'average_time_ms': 0.0,
            'failed_assemblies': 0,
            'average_metadata_fields': 0.0
        }
        
        # Assembly configuration
        self._include_sources = self._config.get('include_sources', True)
        self._include_metadata = self._config.get('include_metadata', True)
        self._format_citations = self._config.get('format_citations', True)
        self._max_source_length = self._config.get('max_source_length', 500)
        
        # Configure based on provided settings
        self.configure(self._config)
        
        logger.debug(f"Initialized {self.__class__.__name__} with config: {self._config}")
    
    def assemble(
        self,
        query: str,
        answer_text: str, 
        context: ContextSelection,
        confidence: float,
        query_analysis: Optional[QueryAnalysis] = None,
        generation_metadata: Optional[Dict[str, Any]] = None
    ) -> Answer:
        """
        Assemble Answer object with performance tracking and error handling.
        
        Args:
            query: Original user query
            answer_text: Generated answer text
            context: Selected context from ContextSelector
            confidence: Answer confidence score
            query_analysis: Optional query analysis metadata
            generation_metadata: Optional metadata from answer generation
            
        Returns:
            Complete Answer object with sources and metadata
            
        Raises:
            ValueError: If required parameters are missing
            RuntimeError: If assembly fails
        """
        # Validate inputs
        if not answer_text or not answer_text.strip():
            raise ValueError("Answer text cannot be empty")
        
        if not 0.0 <= confidence <= 1.0:
            logger.warning(f"Invalid confidence {confidence}, clamping to [0,1]")
            confidence = max(0.0, min(1.0, confidence))
        
        start_time = time.time()
        
        try:
            # Perform actual assembly (implemented by subclasses)
            result = self._assemble_answer(
                query, answer_text, context, confidence, query_analysis, generation_metadata
            )
            
            # Track performance
            assembly_time = time.time() - start_time
            metadata_field_count = len(result.metadata) if result.metadata else 0
            self._update_performance_metrics(assembly_time, metadata_field_count, success=True)
            
            logger.debug(f"Answer assembly completed in {assembly_time*1000:.1f}ms")
            return result
            
        except Exception as e:
            assembly_time = time.time() - start_time
            self._update_performance_metrics(assembly_time, 0, success=False)
            
            logger.error(f"Answer assembly failed after {assembly_time*1000:.1f}ms: {e}")
            raise RuntimeError(f"Answer assembly failed: {e}") from e
    
    def _assemble_answer(
        self,
        query: str,
        answer_text: str, 
        context: ContextSelection,
        confidence: float,
        query_analysis: Optional[QueryAnalysis] = None,
        generation_metadata: Optional[Dict[str, Any]] = None
    ) -> Answer:
        """
        Perform actual answer assembly (must be implemented by subclasses).
        
        Args:
            query: Validated query string
            answer_text: Validated answer text
            context: Context selection
            confidence: Validated confidence score
            query_analysis: Optional query analysis
            generation_metadata: Optional generation metadata
            
        Returns:
            Complete Answer object
        """
        raise NotImplementedError("Subclasses must implement _assemble_answer")
    
    def get_supported_formats(self) -> List[str]:
        """
        Return base formats supported by all assemblers.
        
        Subclasses should override and extend this list.
        
        Returns:
            List of format names
        """
        return ["standard"]
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the assembler with provided settings.
        
        Args:
            config: Configuration dictionary
        """
        self._config.update(config)
        
        # Apply common configuration
        self._include_sources = config.get('include_sources', self._include_sources)
        self._include_metadata = config.get('include_metadata', self._include_metadata)
        self._format_citations = config.get('format_citations', self._format_citations)
        self._max_source_length = config.get('max_source_length', self._max_source_length)
        
        if 'enable_metrics' in config:
            self._track_metrics = config['enable_metrics']
        else:
            self._track_metrics = True  # Default enable metrics
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for this assembler.
        
        Returns:
            Dictionary with performance statistics
        """
        return self._performance_metrics.copy()
    
    def _update_performance_metrics(
        self, 
        assembly_time: float, 
        metadata_fields: int,
        success: bool
    ) -> None:
        """
        Update internal performance metrics.
        
        Args:
            assembly_time: Time taken for assembly in seconds
            metadata_fields: Number of metadata fields created
            success: Whether assembly succeeded
        """
        if not self._track_metrics:
            return
        
        self._performance_metrics['total_assemblies'] += 1
        
        if success:
            # Update average time using incremental formula
            total_successful = self._performance_metrics['total_assemblies'] - self._performance_metrics['failed_assemblies']
            current_avg_time = self._performance_metrics['average_time_ms']
            self._performance_metrics['average_time_ms'] = (
                (current_avg_time * (total_successful - 1) + assembly_time * 1000) / total_successful
            )
            
            # Update average metadata fields
            current_avg_fields = self._performance_metrics['average_metadata_fields']
            self._performance_metrics['average_metadata_fields'] = (
                (current_avg_fields * (total_successful - 1) + metadata_fields) / total_successful
            )
        else:
            self._performance_metrics['failed_assemblies'] += 1
    
    def _create_sources_list(self, context: ContextSelection) -> List[Document]:
        """
        Create sources list from context selection.
        
        Args:
            context: Context selection with documents
            
        Returns:
            List of source documents
        """
        if not self._include_sources or not context.selected_documents:
            return []
        
        sources = []
        for doc in context.selected_documents:
            # Optionally truncate very long documents in sources
            if self._max_source_length > 0 and len(doc.content) > self._max_source_length:
                # Create a truncated copy
                truncated_content = doc.content[:self._max_source_length] + "..."
                # Copy metadata and add source info there
                truncated_metadata = doc.metadata.copy()
                if hasattr(doc, 'source'):
                    truncated_metadata['source'] = doc.source
                elif 'source' not in truncated_metadata:
                    truncated_metadata['source'] = truncated_metadata.get('source', 'unknown')
                    
                if hasattr(doc, 'chunk_id'):
                    truncated_metadata['chunk_id'] = doc.chunk_id
                elif 'chunk_id' not in truncated_metadata:
                    truncated_metadata['chunk_id'] = truncated_metadata.get('chunk_id', 'unknown')
                
                truncated_doc = Document(
                    content=truncated_content,
                    metadata=truncated_metadata,
                    embedding=None  # Don't include large embedding in sources
                )
                sources.append(truncated_doc)
            else:
                # Create clean copy without embedding for sources
                clean_metadata = doc.metadata.copy()
                if hasattr(doc, 'source'):
                    clean_metadata['source'] = doc.source
                elif 'source' not in clean_metadata:
                    clean_metadata['source'] = clean_metadata.get('source', 'unknown')
                    
                if hasattr(doc, 'chunk_id'):
                    clean_metadata['chunk_id'] = doc.chunk_id
                elif 'chunk_id' not in clean_metadata:
                    clean_metadata['chunk_id'] = clean_metadata.get('chunk_id', 'unknown')
                
                clean_doc = Document(
                    content=doc.content,
                    metadata=clean_metadata,
                    embedding=None
                )
                sources.append(clean_doc)
        
        return sources
    
    def _create_base_metadata(
        self,
        query: str,
        context: ContextSelection,
        query_analysis: Optional[QueryAnalysis] = None,
        generation_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create base metadata that all assemblers include.
        
        Args:
            query: Original query
            context: Context selection
            query_analysis: Optional query analysis
            generation_metadata: Optional generation metadata
            
        Returns:
            Base metadata dictionary
        """
        metadata = {}
        
        if self._include_metadata:
            # Query information
            metadata['query'] = query
            metadata['query_length'] = len(query)
            
            # Context information
            metadata['retrieved_docs'] = len(context.selected_documents)
            metadata['total_tokens'] = context.total_tokens
            metadata['selection_strategy'] = context.selection_strategy
            
            # Context quality metrics
            if hasattr(context, 'diversity_score') and context.diversity_score is not None:
                metadata['diversity_score'] = context.diversity_score
            
            if hasattr(context, 'relevance_score') and context.relevance_score is not None:
                metadata['relevance_score'] = context.relevance_score
            
            # Query analysis information
            if query_analysis:
                metadata['query_complexity'] = query_analysis.complexity_score
                metadata['query_intent'] = query_analysis.intent_category
                metadata['technical_terms_count'] = len(query_analysis.technical_terms)
                metadata['entities_count'] = len(query_analysis.entities)
            
            # Generation information
            if generation_metadata:
                # Include relevant generation metadata
                for key in ['generation_time', 'model', 'provider', 'temperature']:
                    if key in generation_metadata:
                        metadata[key] = generation_metadata[key]
            
            # Assembly information
            metadata['assembler_type'] = self._get_assembler_type()
        
        return metadata
    
    def _get_assembler_type(self) -> str:
        """
        Get the type name of this assembler.
        
        Returns:
            Assembler type string
        """
        return self.__class__.__name__.lower().replace('assembler', '')
    
    def _format_answer_text(self, answer_text: str) -> str:
        """
        Format answer text (can be overridden by subclasses).
        
        Args:
            answer_text: Raw answer text
            
        Returns:
            Formatted answer text
        """
        # Base implementation just cleans whitespace
        return answer_text.strip()
    
    def _extract_citations_from_text(self, text: str) -> List[str]:
        """
        Extract citation references from answer text.
        
        Args:
            text: Answer text to analyze
            
        Returns:
            List of citation references found
        """
        import re
        
        citations = []
        
        # Common citation patterns
        patterns = [
            r'\[Document \d+\]',      # [Document 1]
            r'\[chunk_\d+\]',         # [chunk_1]
            r'\[\d+\]',               # [1]
            r'\[Document \d+, Page \d+\]'  # [Document 1, Page 5]
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            citations.extend(matches)
        
        # Remove duplicates while preserving order
        unique_citations = []
        seen = set()
        for citation in citations:
            if citation not in seen:
                seen.add(citation)
                unique_citations.append(citation)
        
        return unique_citations