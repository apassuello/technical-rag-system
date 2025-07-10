"""
Sentence Boundary Chunker Implementation.

This chunker implements intelligent text splitting that preserves sentence
boundaries and semantic coherence. It refactors the existing chunking logic
from the legacy system while conforming to the TextChunker interface.

Key Features:
- ZERO mid-sentence breaks for better retrieval quality
- Configurable chunk size and overlap
- Quality filtering for low-value content
- Technical document optimizations
- Deterministic chunk IDs for reproducibility

Architecture Notes:
- Direct implementation (no adapter pattern) as per MASTER-ARCHITECTURE.md
- Preserves all existing functionality from legacy chunker
- Adds interface compliance and configuration support
"""

import re
import hashlib
from typing import List, Dict, Any
from pathlib import Path
import sys

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "hf_deployment" / "src"))

from ..base import TextChunker, Chunk, ConfigurableComponent, QualityAssessment
from shared_utils.document_processing.chunker import chunk_technical_text, _is_low_quality_chunk


class SentenceBoundaryChunker(TextChunker, ConfigurableComponent, QualityAssessment):
    """
    Sentence-boundary preserving text chunker.
    
    This chunker implements the proven sentence-boundary algorithm from the
    legacy system, ensuring zero mid-sentence breaks while maintaining
    optimal chunk sizes for retrieval. It includes aggressive quality
    filtering and technical content optimization.
    
    Algorithm Details:
    - Expands search window up to 50% beyond target size to find sentence boundaries
    - Prefers chunks within 70-150% of target size over fragmenting
    - Never falls back to mid-sentence breaks
    - Quality filtering removes headers, captions, and navigation elements
    
    Configuration Options:
    - chunk_size: Target chunk size in characters (default: 1400)
    - overlap: Overlap between chunks in characters (default: 200)
    - min_chunk_size: Minimum acceptable chunk size (default: 800)
    - preserve_sentences: Always preserve sentence boundaries (default: True)
    - quality_threshold: Minimum quality score for chunk inclusion (default: 0.0)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the sentence boundary chunker.
        
        Args:
            config: Configuration dictionary with chunker settings
        """
        # Default configuration
        self.config = {
            'chunk_size': 1400,
            'overlap': 200,
            'min_chunk_size': 800,
            'preserve_sentences': True,
            'quality_threshold': 0.0,
            'max_chunk_size': 2100,
            'enable_quality_filtering': True
        }
        
        # Apply provided configuration
        if config:
            self.config.update(config)
        
        # Performance and quality metrics
        self.metrics = {
            'chunks_created': 0,
            'chunks_filtered': 0,
            'total_text_processed': 0,
            'average_chunk_size': 0.0,
            'sentence_boundary_compliance': 1.0,
            'quality_distribution': {'high': 0, 'medium': 0, 'low': 0}
        }
        
        # Quality assessment factors
        self.quality_factors = [
            'content_length',
            'sentence_completeness',
            'technical_relevance',
            'structural_integrity',
            'information_density'
        ]
    
    def chunk(self, text: str, metadata: Dict[str, Any]) -> List[Chunk]:
        """
        Split text into sentence-boundary preserving chunks.
        
        Args:
            text: Input text to be chunked
            metadata: Document metadata to preserve in chunks
            
        Returns:
            List of Chunk objects with content and metadata
            
        Raises:
            ValueError: If text is empty or invalid
        """
        if not text or not isinstance(text, str):
            raise ValueError("Text must be a non-empty string")
        
        # Use the existing proven chunking algorithm
        legacy_chunks = chunk_technical_text(
            text=text,
            chunk_size=self.config['chunk_size'],
            overlap=self.config['overlap']
        )
        
        # Convert legacy chunks to new Chunk objects
        chunks = []
        for i, legacy_chunk in enumerate(legacy_chunks):
            try:
                chunk = self._create_chunk_from_legacy(legacy_chunk, metadata, i)
                
                # Apply quality filtering if enabled
                if self.config['enable_quality_filtering']:
                    quality_score = self.assess_quality(chunk.content)
                    if quality_score < self.config['quality_threshold']:
                        self.metrics['chunks_filtered'] += 1
                        continue
                
                chunks.append(chunk)
                self.metrics['chunks_created'] += 1
                
            except ValueError as e:
                # Skip invalid chunks
                self.metrics['chunks_filtered'] += 1
                continue
        
        # Update metrics
        self._update_metrics(text, chunks)
        
        return chunks
    
    def get_chunk_strategy(self) -> str:
        """
        Return the chunking strategy identifier.
        
        Returns:
            Strategy name
        """
        return "sentence_boundary"
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the chunker with provided settings.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate configuration
        self._validate_config(config)
        
        # Update configuration
        self.config.update(config)
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration.
        
        Returns:
            Current configuration dictionary
        """
        return self.config.copy()
    
    def assess_quality(self, content: str) -> float:
        """
        Assess the quality of chunk content.
        
        Args:
            content: Content to assess
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        if not content:
            return 0.0
        
        # Use legacy quality assessment as base
        if _is_low_quality_chunk(content):
            return 0.1  # Very low quality but not zero
        
        quality_score = 0.0
        
        # Factor 1: Content length (30% weight)
        length_score = self._assess_content_length(content)
        quality_score += length_score * 0.3
        
        # Factor 2: Sentence completeness (25% weight)
        sentence_score = self._assess_sentence_completeness(content)
        quality_score += sentence_score * 0.25
        
        # Factor 3: Technical relevance (20% weight)
        technical_score = self._assess_technical_relevance(content)
        quality_score += technical_score * 0.2
        
        # Factor 4: Structural integrity (15% weight)
        structure_score = self._assess_structural_integrity(content)
        quality_score += structure_score * 0.15
        
        # Factor 5: Information density (10% weight)
        density_score = self._assess_information_density(content)
        quality_score += density_score * 0.1
        
        return min(1.0, quality_score)
    
    def get_quality_factors(self) -> List[str]:
        """
        Get list of quality factors considered.
        
        Returns:
            List of quality factor names
        """
        return self.quality_factors.copy()
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get chunking metrics.
        
        Returns:
            Dictionary with chunking metrics and statistics
        """
        return self.metrics.copy()
    
    def _create_chunk_from_legacy(
        self, 
        legacy_chunk: Dict[str, Any], 
        document_metadata: Dict[str, Any],
        chunk_index: int
    ) -> Chunk:
        """
        Create a new Chunk object from legacy chunk data.
        
        Args:
            legacy_chunk: Legacy chunk data
            document_metadata: Document metadata
            chunk_index: Index of chunk in document
            
        Returns:
            New Chunk object
        """
        content = legacy_chunk.get('text', '')
        if not content:
            raise ValueError("Empty chunk content")
        
        # Create comprehensive metadata
        chunk_metadata = {
            # Legacy chunk information
            'chunk_id': legacy_chunk.get('chunk_id', f'chunk_{chunk_index}'),
            'word_count': legacy_chunk.get('word_count', len(content.split())),
            'sentence_complete': legacy_chunk.get('sentence_complete', True),
            
            # Document context
            'document_source': document_metadata.get('source', ''),
            'document_title': document_metadata.get('title', ''),
            'document_author': document_metadata.get('author', ''),
            'document_page_count': document_metadata.get('page_count', 0),
            
            # Chunking metadata
            'chunking_strategy': self.get_chunk_strategy(),
            'chunk_size_config': self.config['chunk_size'],
            'overlap_config': self.config['overlap'],
            'quality_score': self.assess_quality(content),
            
            # Processing metadata
            'chunk_index': chunk_index,
            'creation_timestamp': document_metadata.get('processing_timestamp'),
            'processor_version': '1.0',
            
            # Preserve original document metadata
            **{k: v for k, v in document_metadata.items() if k not in [
                'source', 'title', 'author', 'page_count', 'processing_timestamp'
            ]}
        }
        
        return Chunk(
            content=content,
            start_pos=legacy_chunk.get('start_char', 0),
            end_pos=legacy_chunk.get('end_char', len(content)),
            metadata=chunk_metadata
        )
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate configuration parameters.
        
        Args:
            config: Configuration to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        if 'chunk_size' in config:
            if not isinstance(config['chunk_size'], int) or config['chunk_size'] <= 0:
                raise ValueError("chunk_size must be a positive integer")
        
        if 'overlap' in config:
            if not isinstance(config['overlap'], int) or config['overlap'] < 0:
                raise ValueError("overlap must be a non-negative integer")
        
        if 'min_chunk_size' in config:
            if not isinstance(config['min_chunk_size'], int) or config['min_chunk_size'] <= 0:
                raise ValueError("min_chunk_size must be a positive integer")
        
        if 'quality_threshold' in config:
            if not isinstance(config['quality_threshold'], (int, float)) or not 0 <= config['quality_threshold'] <= 1:
                raise ValueError("quality_threshold must be a float between 0 and 1")
        
        # Validate relationships
        chunk_size = config.get('chunk_size', self.config['chunk_size'])
        overlap = config.get('overlap', self.config['overlap'])
        min_chunk_size = config.get('min_chunk_size', self.config['min_chunk_size'])
        
        if overlap >= chunk_size:
            raise ValueError("overlap must be less than chunk_size")
        
        if min_chunk_size > chunk_size:
            raise ValueError("min_chunk_size must be less than or equal to chunk_size")
    
    def _update_metrics(self, text: str, chunks: List[Chunk]) -> None:
        """
        Update chunking metrics.
        
        Args:
            text: Original text
            chunks: Created chunks
        """
        self.metrics['total_text_processed'] += len(text)
        
        if chunks:
            chunk_sizes = [len(chunk.content) for chunk in chunks]
            self.metrics['average_chunk_size'] = sum(chunk_sizes) / len(chunk_sizes)
            
            # Update quality distribution
            for chunk in chunks:
                quality_score = chunk.metadata.get('quality_score', 0.0)
                if quality_score >= 0.8:
                    self.metrics['quality_distribution']['high'] += 1
                elif quality_score >= 0.5:
                    self.metrics['quality_distribution']['medium'] += 1
                else:
                    self.metrics['quality_distribution']['low'] += 1
    
    def _assess_content_length(self, content: str) -> float:
        """
        Assess content length appropriateness.
        
        Args:
            content: Content to assess
            
        Returns:
            Length quality score (0.0 to 1.0)
        """
        length = len(content)
        target_size = self.config['chunk_size']
        min_size = self.config['min_chunk_size']
        
        if length < min_size:
            return 0.3  # Too short
        elif length > target_size * 1.5:
            return 0.7  # Too long but acceptable
        else:
            # Optimal range
            return 1.0
    
    def _assess_sentence_completeness(self, content: str) -> float:
        """
        Assess sentence completeness.
        
        Args:
            content: Content to assess
            
        Returns:
            Sentence completeness score (0.0 to 1.0)
        """
        # Check if content ends with sentence terminators
        terminators = ['.', '!', '?', ':', ';']
        if any(content.rstrip().endswith(term) for term in terminators):
            return 1.0
        
        # Check if it's a complete thought (has subject and verb patterns)
        words = content.split()
        if len(words) < 3:
            return 0.3
        
        # Simple heuristic: if it has common sentence patterns
        common_patterns = ['the', 'is', 'are', 'was', 'were', 'has', 'have', 'will', 'can', 'this', 'that']
        pattern_count = sum(1 for word in words if word.lower() in common_patterns)
        
        return min(1.0, pattern_count / 5.0)
    
    def _assess_technical_relevance(self, content: str) -> float:
        """
        Assess technical content relevance.
        
        Args:
            content: Content to assess
            
        Returns:
            Technical relevance score (0.0 to 1.0)
        """
        content_lower = content.lower()
        
        # Technical indicators
        technical_terms = [
            'algorithm', 'implementation', 'system', 'method', 'process',
            'function', 'parameter', 'variable', 'configuration', 'protocol',
            'architecture', 'design', 'specification', 'interface', 'module',
            'register', 'memory', 'processor', 'instruction', 'operation'
        ]
        
        term_count = sum(1 for term in technical_terms if term in content_lower)
        
        # Code indicators
        code_indicators = ['()', '[]', '{', '}', '==', '!=', '<=', '>=', '->', '=>']
        code_count = sum(1 for indicator in code_indicators if indicator in content)
        
        # Combine scores
        tech_score = min(1.0, term_count / 10.0)
        code_score = min(1.0, code_count / 5.0)
        
        return max(tech_score, code_score)
    
    def _assess_structural_integrity(self, content: str) -> float:
        """
        Assess structural integrity of content.
        
        Args:
            content: Content to assess
            
        Returns:
            Structural integrity score (0.0 to 1.0)
        """
        # Check for proper capitalization
        sentences = re.split(r'[.!?]+', content)
        properly_capitalized = sum(1 for s in sentences if s.strip() and s.strip()[0].isupper())
        
        if not sentences:
            return 0.0
        
        capitalization_score = properly_capitalized / len(sentences)
        
        # Check for balanced parentheses/brackets
        balance_score = 1.0
        for open_char, close_char in [('(', ')'), ('[', ']'), ('{', '}')]:
            if content.count(open_char) != content.count(close_char):
                balance_score -= 0.2
        
        return max(0.0, (capitalization_score + balance_score) / 2.0)
    
    def _assess_information_density(self, content: str) -> float:
        """
        Assess information density of content.
        
        Args:
            content: Content to assess
            
        Returns:
            Information density score (0.0 to 1.0)
        """
        words = content.split()
        if len(words) < 5:
            return 0.3
        
        # Calculate unique word ratio
        unique_words = set(word.lower() for word in words)
        unique_ratio = len(unique_words) / len(words)
        
        # Calculate average word length (longer words often more informative)
        avg_word_length = sum(len(word) for word in words) / len(words)
        length_score = min(1.0, avg_word_length / 6.0)  # Normalize to 6 characters
        
        # Combine scores
        return (unique_ratio + length_score) / 2.0