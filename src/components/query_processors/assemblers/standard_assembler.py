"""
Standard Response Assembler Implementation.

This module provides minimal overhead response assembly for performance-critical
applications where basic Answer objects are sufficient.

Features:
- Minimal metadata overhead
- Fast assembly performance
- Essential source information only
- Lightweight configuration
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from ..base import ContextSelection, QueryAnalysis
from .base_assembler import BaseResponseAssembler
from src.core.interfaces import Answer, Document

logger = logging.getLogger(__name__)


class StandardAssembler(BaseResponseAssembler):
    """
    Standard response assembler with minimal overhead.
    
    This assembler creates Answer objects with essential information only,
    optimized for performance-critical applications where detailed metadata
    is not required.
    
    Configuration Options:
    - minimal_metadata: Use absolute minimum metadata (default: False)
    - include_basic_stats: Include basic statistics (default: True)
    - strip_large_sources: Remove large document content from sources (default: True)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize standard assembler with configuration.
        
        Args:
            config: Configuration dictionary
        """
        # Initialize attributes first before calling super().__init__
        config_dict = config or {}
        self._minimal_metadata = config_dict.get('minimal_metadata', False)
        self._include_basic_stats = config_dict.get('include_basic_stats', True)
        self._strip_large_sources = config_dict.get('strip_large_sources', True)
        
        super().__init__(config)
        
        # Override base settings for performance
        if self._minimal_metadata:
            self._include_metadata = False
            self._include_sources = True  # Keep sources but strip content
        
        logger.debug(f"Initialized StandardAssembler with minimal_metadata={self._minimal_metadata}")
    
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
        Assemble Answer object with minimal overhead.
        
        Args:
            query: Validated query string
            answer_text: Validated answer text
            context: Context selection
            confidence: Validated confidence score
            query_analysis: Optional query analysis
            generation_metadata: Optional generation metadata
            
        Returns:
            Answer object with minimal metadata
        """
        # Simple text formatting
        formatted_text = answer_text.strip()
        
        # Create sources list (potentially stripped)
        sources = self._create_minimal_sources_list(context)
        
        # Create minimal metadata
        metadata = self._create_minimal_metadata(query, context, generation_metadata)
        
        return Answer(
            text=formatted_text,
            sources=sources,
            confidence=confidence,
            metadata=metadata
        )
    
    def _create_minimal_sources_list(self, context: ContextSelection) -> List[Document]:
        """
        Create minimal sources list for performance.
        
        Args:
            context: Context selection with documents
            
        Returns:
            List of minimal source documents
        """
        if not self._include_sources or not context.selected_documents:
            return []
        
        sources = []
        for doc in context.selected_documents:
            if self._strip_large_sources:
                # Create minimal document with just essential information
                minimal_metadata = {
                    'original_length': len(doc.content),
                    'content_stripped': True
                }
                if doc.metadata:
                    minimal_metadata.update(doc.metadata)
                
                # Add source and chunk_id to metadata
                if hasattr(doc, 'source'):
                    minimal_metadata['source'] = doc.source
                elif 'source' not in minimal_metadata:
                    minimal_metadata['source'] = minimal_metadata.get('source', 'unknown')
                    
                if hasattr(doc, 'chunk_id'):
                    minimal_metadata['chunk_id'] = doc.chunk_id
                elif 'chunk_id' not in minimal_metadata:
                    minimal_metadata['chunk_id'] = minimal_metadata.get('chunk_id', 'unknown')
                
                minimal_doc = Document(
                    content="[Content stripped for performance]",  # Document content cannot be empty
                    metadata=minimal_metadata,
                    embedding=None  # Remove embedding
                )
                sources.append(minimal_doc)
            else:
                # Keep full content but remove embedding
                clean_metadata = doc.metadata.copy() if doc.metadata else {}
                
                # Add source and chunk_id to metadata
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
    
    def _create_minimal_metadata(
        self,
        query: str,
        context: ContextSelection,
        generation_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create minimal metadata for performance.
        
        Args:
            query: Original query
            context: Context selection
            generation_metadata: Optional generation metadata
            
        Returns:
            Minimal metadata dictionary
        """
        if self._minimal_metadata:
            # Absolute minimum metadata
            return {
                'assembler_type': 'standard',
                'source_count': len(context.selected_documents)
            }
        
        metadata = {
            'assembler_type': 'standard',
            'query': query,
            'retrieved_docs': len(context.selected_documents),
            'total_tokens': context.total_tokens,
            'selection_strategy': context.selection_strategy
        }
        
        # Add basic statistics if enabled
        if self._include_basic_stats:
            metadata.update({
                'query_length': len(query),
                'answer_length': 0,  # Will be updated after answer is created
                'source_count': len(context.selected_documents)
            })
        
        # Include minimal generation information
        if generation_metadata:
            # Only include essential generation metadata
            essential_fields = ['model', 'generation_time']
            for field in essential_fields:
                if field in generation_metadata:
                    metadata[field] = generation_metadata[field]
        
        return metadata
    
    def get_supported_formats(self) -> List[str]:
        """
        Return list of formats this standard assembler supports.
        
        Returns:
            List of format names
        """
        base_formats = super().get_supported_formats()
        standard_formats = [
            'minimal',
            'fast',
            'lightweight',
            'performance'
        ]
        return base_formats + standard_formats
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the standard assembler with provided settings.
        
        Args:
            config: Configuration dictionary
        """
        super().configure(config)
        
        # Update standard assembler specific configuration
        self._minimal_metadata = config.get('minimal_metadata', self._minimal_metadata)
        self._include_basic_stats = config.get('include_basic_stats', self._include_basic_stats)
        self._strip_large_sources = config.get('strip_large_sources', self._strip_large_sources)
        
        # Apply minimal metadata setting
        if self._minimal_metadata:
            self._include_metadata = False
            self._include_sources = True