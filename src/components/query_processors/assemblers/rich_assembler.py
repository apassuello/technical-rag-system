"""
Rich Response Assembler Implementation.

This module provides comprehensive response assembly with detailed metadata,
source information, and enhanced formatting for production use.

Features:
- Comprehensive metadata collection
- Citation analysis and validation
- Source document summaries
- Quality metrics and confidence scoring
- Detailed assembly diagnostics
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


class RichAssembler(BaseResponseAssembler):
    """
    Rich response assembler with comprehensive metadata and formatting.
    
    This assembler creates Answer objects with detailed metadata, source
    summaries, citation analysis, and quality metrics. It's designed for
    production use where comprehensive information is needed.
    
    Configuration Options:
    - include_source_summaries: Include document summaries (default: True)
    - include_citation_analysis: Analyze citations in answer (default: True)
    - include_quality_metrics: Include quality assessment (default: True)
    - include_debug_info: Include assembly diagnostics (default: False)
    - citation_format: Citation format style ("inline", "numbered", "document")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize rich assembler with configuration.
        
        Args:
            config: Configuration dictionary
        """
        # Initialize attributes first before calling super().__init__
        config_dict = config or {}
        self._include_source_summaries = config_dict.get('include_source_summaries', True)
        self._include_citation_analysis = config_dict.get('include_citation_analysis', True)
        self._include_quality_metrics = config_dict.get('include_quality_metrics', True)
        self._include_debug_info = config_dict.get('include_debug_info', False)
        self._citation_format = config_dict.get('citation_format', 'inline')
        
        super().__init__(config)
        
        logger.debug(f"Initialized RichAssembler with citation_format={self._citation_format}")
    
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
        Assemble comprehensive Answer object with rich metadata.
        
        Args:
            query: Validated query string
            answer_text: Validated answer text
            context: Context selection
            confidence: Validated confidence score
            query_analysis: Optional query analysis
            generation_metadata: Optional generation metadata
            
        Returns:
            Answer object with comprehensive metadata
        """
        # Format answer text
        formatted_text = self._format_answer_text(answer_text)
        
        # Create sources list
        sources = self._create_sources_list(context)
        
        # Create base metadata
        metadata = self._create_base_metadata(query, context, query_analysis, generation_metadata)
        
        # Add rich metadata
        if self._include_source_summaries:
            metadata['source_summaries'] = self._create_source_summaries(context.selected_documents)
        
        if self._include_citation_analysis:
            citation_analysis = self._analyze_citations(formatted_text, context.selected_documents)
            metadata['citation_analysis'] = citation_analysis
        
        if self._include_quality_metrics:
            quality_metrics = self._calculate_quality_metrics(
                formatted_text, context, confidence, query_analysis
            )
            metadata['quality_metrics'] = quality_metrics
        
        if self._include_debug_info:
            debug_info = self._create_debug_info(context, generation_metadata)
            metadata['debug_info'] = debug_info
        
        # Add assembly-specific metadata
        metadata.update({
            'assembler_version': '1.0',
            'assembly_features': self._get_enabled_features(),
            'answer_length': len(formatted_text),
            'word_count': len(formatted_text.split()),
            'source_count': len(sources)
        })
        
        return Answer(
            text=formatted_text,
            sources=sources,
            confidence=confidence,
            metadata=metadata
        )
    
    def _create_source_summaries(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """
        Create summaries for source documents.
        
        Args:
            documents: Source documents
            
        Returns:
            List of document summaries
        """
        summaries = []
        
        for i, doc in enumerate(documents):
            # Get source and chunk_id from metadata or attributes
            source = getattr(doc, 'source', None) or doc.metadata.get('source', 'unknown')
            chunk_id = getattr(doc, 'chunk_id', None) or doc.metadata.get('chunk_id', 'unknown')
            
            summary = {
                'index': i,
                'source': source,
                'chunk_id': chunk_id,
                'content_length': len(doc.content),
                'word_count': len(doc.content.split()),
                'preview': doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
            }
            
            # Add document metadata if available
            if doc.metadata:
                # Extract useful metadata fields
                metadata_fields = ['page', 'title', 'section', 'quality_score']
                for field in metadata_fields:
                    if field in doc.metadata:
                        summary[field] = doc.metadata[field]
            
            # Add relevance score if available
            if hasattr(doc, 'score'):
                summary['relevance_score'] = doc.score
            
            summaries.append(summary)
        
        return summaries
    
    def _analyze_citations(self, answer_text: str, documents: List[Document]) -> Dict[str, Any]:
        """
        Analyze citations in the answer text.
        
        Args:
            answer_text: Answer text to analyze
            documents: Source documents used
            
        Returns:
            Citation analysis results
        """
        citations_found = self._extract_citations_from_text(answer_text)
        
        analysis = {
            'citations_found': citations_found,
            'citation_count': len(citations_found),
            'has_citations': len(citations_found) > 0,
            'citation_density': len(citations_found) / max(1, len(answer_text.split())) * 100,  # Citations per 100 words
        }
        
        # Validate citations against available sources
        validation_results = self._validate_citations(citations_found, documents)
        analysis['validation'] = validation_results
        
        # Analyze citation patterns
        pattern_analysis = self._analyze_citation_patterns(citations_found)
        analysis['patterns'] = pattern_analysis
        
        return analysis
    
    def _validate_citations(self, citations: List[str], documents: List[Document]) -> Dict[str, Any]:
        """
        Validate that citations reference available documents.
        
        Args:
            citations: List of citation strings
            documents: Available source documents
            
        Returns:
            Citation validation results
        """
        validation = {
            'valid_citations': [],
            'invalid_citations': [],
            'validation_rate': 0.0
        }
        
        # Create mapping of available document references
        available_refs = set()
        for i, doc in enumerate(documents):
            # Common reference formats
            available_refs.add(f"[Document {i+1}]")
            available_refs.add(f"[{i+1}]")
            
            # Get chunk_id from attribute or metadata
            chunk_id = getattr(doc, 'chunk_id', None) or doc.metadata.get('chunk_id', None)
            if chunk_id:
                available_refs.add(f"[{chunk_id}]")
        
        # Validate each citation
        for citation in citations:
            if citation in available_refs:
                validation['valid_citations'].append(citation)
            else:
                validation['invalid_citations'].append(citation)
        
        # Calculate validation rate
        total_citations = len(citations)
        if total_citations > 0:
            validation['validation_rate'] = len(validation['valid_citations']) / total_citations
        
        return validation
    
    def _analyze_citation_patterns(self, citations: List[str]) -> Dict[str, Any]:
        """
        Analyze patterns in citation usage.
        
        Args:
            citations: List of citation strings
            
        Returns:
            Pattern analysis results
        """
        import re
        
        patterns = {
            'document_format': 0,    # [Document N]
            'simple_format': 0,      # [N]  
            'chunk_format': 0,       # [chunk_N]
            'page_format': 0         # [Document N, Page N]
        }
        
        for citation in citations:
            if re.match(r'\[Document \d+, Page \d+\]', citation):
                patterns['page_format'] += 1
            elif re.match(r'\[Document \d+\]', citation):
                patterns['document_format'] += 1
            elif re.match(r'\[chunk_\d+\]', citation):
                patterns['chunk_format'] += 1
            elif re.match(r'\[\d+\]', citation):
                patterns['simple_format'] += 1
        
        # Determine dominant pattern
        dominant_pattern = max(patterns.items(), key=lambda x: x[1])[0] if citations else 'none'
        
        return {
            'format_counts': patterns,
            'dominant_format': dominant_pattern,
            'format_consistency': max(patterns.values()) / max(1, len(citations))
        }
    
    def _calculate_quality_metrics(
        self,
        answer_text: str,
        context: ContextSelection,
        confidence: float,
        query_analysis: Optional[QueryAnalysis] = None
    ) -> Dict[str, Any]:
        """
        Calculate quality metrics for the assembled answer.
        
        Args:
            answer_text: Generated answer text
            context: Context selection used
            confidence: Answer confidence score
            query_analysis: Optional query analysis
            
        Returns:
            Quality metrics dictionary
        """
        metrics = {}
        
        # Text quality metrics
        metrics['answer_length'] = len(answer_text)
        metrics['word_count'] = len(answer_text.split())
        metrics['sentence_count'] = answer_text.count('.') + answer_text.count('!') + answer_text.count('?')
        
        # Calculate average sentence length
        if metrics['sentence_count'] > 0:
            metrics['avg_sentence_length'] = metrics['word_count'] / metrics['sentence_count']
        else:
            metrics['avg_sentence_length'] = 0.0
        
        # Content quality indicators
        metrics['has_technical_content'] = any(
            term in answer_text.lower() 
            for term in ['implementation', 'algorithm', 'protocol', 'configuration', 'api']
        )
        
        metrics['has_examples'] = any(
            phrase in answer_text.lower()
            for phrase in ['example', 'for instance', 'such as', 'like']
        )
        
        metrics['has_explanations'] = any(
            phrase in answer_text.lower()
            for phrase in ['because', 'since', 'due to', 'this means', 'in other words']
        )
        
        # Source utilization metrics
        metrics['sources_used'] = len(context.selected_documents)
        metrics['token_efficiency'] = context.total_tokens / max(1, len(answer_text))
        
        if hasattr(context, 'relevance_score') and context.relevance_score is not None:
            metrics['source_relevance'] = context.relevance_score
        
        if hasattr(context, 'diversity_score') and context.diversity_score is not None:
            metrics['source_diversity'] = context.diversity_score
        
        # Overall quality score (0.0 - 1.0)
        quality_components = [
            confidence,  # LLM confidence
            min(1.0, metrics['word_count'] / 50),  # Length adequacy (up to 50 words)
            1.0 if metrics['has_technical_content'] else 0.5,  # Technical content
            1.0 if metrics['has_explanations'] else 0.7,  # Explanatory content
            min(1.0, metrics['sources_used'] / 3)  # Source utilization (up to 3 sources)
        ]
        
        metrics['overall_quality'] = sum(quality_components) / len(quality_components)
        
        return metrics
    
    def _create_debug_info(
        self,
        context: ContextSelection,
        generation_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create debug information for troubleshooting.
        
        Args:
            context: Context selection
            generation_metadata: Generation metadata
            
        Returns:
            Debug information dictionary
        """
        debug_info = {
            'context_metadata': context.metadata,
            'selection_strategy': context.selection_strategy,
            'total_tokens': context.total_tokens
        }
        
        if generation_metadata:
            debug_info['generation_metadata'] = generation_metadata
        
        # Add assembler configuration
        debug_info['assembler_config'] = {
            'include_source_summaries': self._include_source_summaries,
            'include_citation_analysis': self._include_citation_analysis,
            'include_quality_metrics': self._include_quality_metrics,
            'citation_format': self._citation_format
        }
        
        return debug_info
    
    def _get_enabled_features(self) -> List[str]:
        """
        Get list of enabled rich assembler features.
        
        Returns:
            List of enabled feature names
        """
        features = []
        
        if self._include_source_summaries:
            features.append('source_summaries')
        
        if self._include_citation_analysis:
            features.append('citation_analysis')
        
        if self._include_quality_metrics:
            features.append('quality_metrics')
        
        if self._include_debug_info:
            features.append('debug_info')
        
        if self._format_citations:
            features.append('citation_formatting')
        
        return features
    
    def get_supported_formats(self) -> List[str]:
        """
        Return list of formats this rich assembler supports.
        
        Returns:
            List of format names
        """
        base_formats = super().get_supported_formats()
        rich_formats = [
            'rich',
            'comprehensive',
            'detailed',
            'production'
        ]
        return base_formats + rich_formats
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the rich assembler with provided settings.
        
        Args:
            config: Configuration dictionary
        """
        super().configure(config)
        
        # Update rich assembler specific configuration
        self._include_source_summaries = config.get('include_source_summaries', self._include_source_summaries)
        self._include_citation_analysis = config.get('include_citation_analysis', self._include_citation_analysis)
        self._include_quality_metrics = config.get('include_quality_metrics', self._include_quality_metrics)
        self._include_debug_info = config.get('include_debug_info', self._include_debug_info)
        
        # Validate citation format
        valid_formats = ['inline', 'numbered', 'document']
        new_format = config.get('citation_format', self._citation_format)
        if new_format in valid_formats:
            self._citation_format = new_format
        else:
            logger.warning(f"Invalid citation_format {new_format}, keeping {self._citation_format}")
    
    def _format_answer_text(self, answer_text: str) -> str:
        """
        Format answer text with rich formatting options.
        
        Args:
            answer_text: Raw answer text
            
        Returns:
            Formatted answer text
        """
        # Base formatting
        formatted = super()._format_answer_text(answer_text)
        
        # Additional rich formatting
        if self._format_citations:
            formatted = self._apply_citation_formatting(formatted)
        
        return formatted
    
    def _apply_citation_formatting(self, text: str) -> str:
        """
        Apply citation formatting based on configuration.
        
        Args:
            text: Text with citations
            
        Returns:
            Text with formatted citations
        """
        # This is a placeholder for citation formatting
        # Can be extended based on specific formatting requirements
        return text