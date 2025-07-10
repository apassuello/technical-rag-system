"""
PyMuPDF Adapter for Document Processing.

This adapter wraps the existing PyMuPDF-based PDF parser to provide
a consistent DocumentParser interface. It preserves all existing
functionality while conforming to the modular architecture.

Architecture Notes:
- Uses adapter pattern as specified in MASTER-ARCHITECTURE.md section 2.3
- Wraps external PyMuPDF library to isolate API dependencies
- Maintains performance characteristics of original implementation
- Provides consistent interface for pipeline integration
"""

import sys
from pathlib import Path
from typing import List, Dict, Any
import time

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "hf_deployment" / "src"))

from ..base import DocumentParser, ValidationResult, ConfigurableComponent
from shared_utils.document_processing.pdf_parser import extract_text_with_metadata


class PyMuPDFAdapter(DocumentParser, ConfigurableComponent):
    """
    Adapter for PyMuPDF-based PDF parsing.
    
    This adapter wraps the existing `extract_text_with_metadata` function
    to provide a consistent DocumentParser interface while preserving
    all existing functionality and performance characteristics.
    
    Features:
    - Page-by-page text extraction with metadata preservation
    - Robust error handling for corrupted or malformed PDFs
    - Performance timing for optimization analysis
    - Memory-efficient processing for large documents
    - Configurable extraction parameters
    
    Configuration Options:
    - extract_images: Whether to extract images from PDFs
    - preserve_layout: Whether to preserve document layout
    - max_file_size_mb: Maximum file size to process
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the PyMuPDF adapter.
        
        Args:
            config: Configuration dictionary with adapter settings
        """
        # Default configuration
        self.config = {
            'extract_images': False,
            'preserve_layout': True,
            'max_file_size_mb': 100,
            'encoding': 'utf-8'
        }
        
        # Apply provided configuration
        if config:
            self.config.update(config)
        
        # Performance tracking
        self.metrics = {
            'documents_processed': 0,
            'total_processing_time': 0.0,
            'total_pages_processed': 0,
            'average_processing_speed': 0.0,
            'errors_encountered': 0
        }
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse PDF document using PyMuPDF.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing:
            - 'text': Complete concatenated text from all pages
            - 'metadata': PDF metadata (title, author, etc.)
            - 'pages': List of page-level data
            - 'structure': Document structure information
            - 'processing_info': Processing statistics
            
        Raises:
            ValueError: If file format is not supported
            IOError: If file cannot be read or is corrupted
        """
        start_time = time.perf_counter()
        
        try:
            # Validate file
            validation_result = self._validate_file(file_path)
            if not validation_result.valid:
                raise ValueError(f"Invalid PDF file: {validation_result.errors}")
            
            # Extract text using existing function
            pdf_data = extract_text_with_metadata(file_path)
            
            # Enhance with additional structure information
            enhanced_data = self._enhance_pdf_data(pdf_data, file_path)
            
            # Update metrics
            processing_time = time.perf_counter() - start_time
            self._update_metrics(enhanced_data, processing_time)
            
            return enhanced_data
            
        except Exception as e:
            self.metrics['errors_encountered'] += 1
            if isinstance(e, (ValueError, IOError)):
                raise
            else:
                raise IOError(f"Failed to parse PDF {file_path}: {str(e)}") from e
    
    def extract_metadata(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract enhanced metadata from parsed PDF document.
        
        Args:
            document: Parsed document data from parse() method
            
        Returns:
            Dictionary containing enhanced document metadata
        """
        base_metadata = document.get('metadata', {})
        
        # Enhance metadata with additional information
        enhanced_metadata = {
            # Original PDF metadata
            **base_metadata,
            
            # Document characteristics
            'format': 'pdf',
            'parser': 'pymupdf',
            'page_count': document.get('page_count', 0),
            'total_characters': len(document.get('text', '')),
            'processing_time': document.get('processing_info', {}).get('processing_time', 0.0),
            
            # Structure information
            'has_toc': self._has_table_of_contents(document),
            'estimated_reading_time': self._estimate_reading_time(document.get('text', '')),
            'language': self._detect_language(document.get('text', '')),
            
            # Quality indicators
            'content_quality': self._assess_content_quality(document),
            'extraction_confidence': self._calculate_extraction_confidence(document)
        }
        
        return enhanced_metadata
    
    def supported_formats(self) -> List[str]:
        """
        Return list of supported file extensions.
        
        Returns:
            List of PDF file extensions
        """
        return ['.pdf']
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the adapter with provided settings.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate configuration
        valid_keys = {'extract_images', 'preserve_layout', 'max_file_size_mb', 'encoding'}
        invalid_keys = set(config.keys()) - valid_keys
        if invalid_keys:
            raise ValueError(f"Invalid configuration keys: {invalid_keys}")
        
        # Validate specific values
        if 'max_file_size_mb' in config:
            if not isinstance(config['max_file_size_mb'], (int, float)) or config['max_file_size_mb'] <= 0:
                raise ValueError("max_file_size_mb must be a positive number")
        
        # Update configuration
        self.config.update(config)
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration.
        
        Returns:
            Current configuration dictionary
        """
        return self.config.copy()
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get processing metrics.
        
        Returns:
            Dictionary with processing metrics and statistics
        """
        return self.metrics.copy()
    
    def _validate_file(self, file_path: Path) -> ValidationResult:
        """
        Validate PDF file before processing.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []
        
        # Check file existence
        if not file_path.exists():
            errors.append(f"File not found: {file_path}")
        
        # Check file extension
        if file_path.suffix.lower() != '.pdf':
            errors.append(f"Unsupported file format: {file_path.suffix}")
        
        # Check file size
        if file_path.exists():
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.config['max_file_size_mb']:
                errors.append(f"File too large: {file_size_mb:.1f}MB > {self.config['max_file_size_mb']}MB")
            elif file_size_mb > self.config['max_file_size_mb'] * 0.8:
                warnings.append(f"Large file size: {file_size_mb:.1f}MB")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _enhance_pdf_data(self, pdf_data: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
        """
        Enhance PDF data with additional structure information.
        
        Args:
            pdf_data: Original PDF data from extract_text_with_metadata
            file_path: Path to source file
            
        Returns:
            Enhanced PDF data with additional structure
        """
        enhanced_data = pdf_data.copy()
        
        # Add structure information
        enhanced_data['structure'] = {
            'pages': self._analyze_page_structure(pdf_data.get('pages', [])),
            'sections': self._detect_sections(pdf_data.get('text', '')),
            'formatting': self._analyze_formatting(pdf_data.get('text', ''))
        }
        
        # Add processing information
        enhanced_data['processing_info'] = {
            'source_file': str(file_path),
            'processing_time': pdf_data.get('extraction_time', 0.0),
            'adapter': 'pymupdf',
            'configuration': self.config.copy()
        }
        
        return enhanced_data
    
    def _update_metrics(self, document: Dict[str, Any], processing_time: float) -> None:
        """
        Update processing metrics.
        
        Args:
            document: Processed document data
            processing_time: Time taken for processing
        """
        self.metrics['documents_processed'] += 1
        self.metrics['total_processing_time'] += processing_time
        self.metrics['total_pages_processed'] += document.get('page_count', 0)
        
        # Calculate average processing speed (pages/second)
        if self.metrics['total_processing_time'] > 0:
            self.metrics['average_processing_speed'] = (
                self.metrics['total_pages_processed'] / self.metrics['total_processing_time']
            )
    
    def _has_table_of_contents(self, document: Dict[str, Any]) -> bool:
        """
        Check if document has a table of contents.
        
        Args:
            document: Parsed document data
            
        Returns:
            True if document appears to have a TOC
        """
        text = document.get('text', '').lower()
        toc_indicators = [
            'table of contents',
            'contents',
            'chapter 1',
            'section 1',
            '1. introduction',
            '1.1 ',
            '1.2 '
        ]
        
        return any(indicator in text for indicator in toc_indicators)
    
    def _estimate_reading_time(self, text: str) -> float:
        """
        Estimate reading time in minutes.
        
        Args:
            text: Document text
            
        Returns:
            Estimated reading time in minutes
        """
        # Average reading speed: 200-250 words per minute
        words = len(text.split())
        return words / 225.0  # Use 225 WPM as average
    
    def _detect_language(self, text: str) -> str:
        """
        Detect document language (basic heuristic).
        
        Args:
            text: Document text
            
        Returns:
            Detected language code
        """
        # Simple heuristic - can be enhanced with proper language detection
        if len(text) < 100:
            return 'unknown'
        
        # Check for common English words
        english_words = ['the', 'and', 'of', 'to', 'in', 'is', 'it', 'that', 'this', 'with']
        text_lower = text.lower()
        english_count = sum(1 for word in english_words if word in text_lower)
        
        return 'en' if english_count >= 5 else 'unknown'
    
    def _assess_content_quality(self, document: Dict[str, Any]) -> float:
        """
        Assess content quality of the document.
        
        Args:
            document: Parsed document data
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        text = document.get('text', '')
        pages = document.get('pages', [])
        
        if not text:
            return 0.0
        
        quality_score = 0.0
        
        # Factor 1: Text length indicates content richness
        text_length_score = min(len(text) / 10000, 1.0)  # Normalize to 10k chars
        quality_score += text_length_score * 0.3
        
        # Factor 2: Page consistency
        if pages:
            page_lengths = [len(page.get('text', '')) for page in pages]
            if page_lengths:
                avg_length = sum(page_lengths) / len(page_lengths)
                consistency_score = 1.0 - (max(page_lengths) - min(page_lengths)) / (avg_length + 1)
                quality_score += max(0, consistency_score) * 0.2
        
        # Factor 3: Sentence structure
        sentences = text.split('.')
        complete_sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        sentence_score = min(len(complete_sentences) / 100, 1.0)
        quality_score += sentence_score * 0.3
        
        # Factor 4: Technical content indicators
        technical_indicators = ['figure', 'table', 'section', 'chapter', 'algorithm', 'equation']
        technical_score = min(sum(1 for indicator in technical_indicators if indicator in text.lower()) / 10, 1.0)
        quality_score += technical_score * 0.2
        
        return min(quality_score, 1.0)
    
    def _calculate_extraction_confidence(self, document: Dict[str, Any]) -> float:
        """
        Calculate confidence in extraction quality.
        
        Args:
            document: Parsed document data
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        text = document.get('text', '')
        processing_time = document.get('extraction_time', 0.0)
        
        if not text:
            return 0.0
        
        confidence = 0.8  # Base confidence for successful extraction
        
        # Factor in processing time (very fast might indicate issues)
        if processing_time > 0:
            chars_per_second = len(text) / processing_time
            if chars_per_second > 1000000:  # Suspiciously fast
                confidence -= 0.2
            elif chars_per_second < 1000:  # Suspiciously slow
                confidence -= 0.1
        
        # Factor in text quality indicators
        weird_chars = sum(1 for char in text if ord(char) > 127 and char not in 'àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ')
        if weird_chars > len(text) * 0.05:  # More than 5% weird characters
            confidence -= 0.3
        
        return max(0.0, min(1.0, confidence))
    
    def _analyze_page_structure(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze page structure patterns.
        
        Args:
            pages: List of page data
            
        Returns:
            Page structure analysis
        """
        if not pages:
            return {}
        
        page_lengths = [page.get('char_count', 0) for page in pages]
        
        return {
            'total_pages': len(pages),
            'average_page_length': sum(page_lengths) / len(page_lengths) if page_lengths else 0,
            'min_page_length': min(page_lengths) if page_lengths else 0,
            'max_page_length': max(page_lengths) if page_lengths else 0,
            'has_consistent_length': max(page_lengths) - min(page_lengths) < 1000 if page_lengths else False
        }
    
    def _detect_sections(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect document sections using simple heuristics.
        
        Args:
            text: Document text
            
        Returns:
            List of detected sections
        """
        sections = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Simple section detection patterns
            if (line_stripped and 
                (line_stripped.endswith(':') or 
                 any(pattern in line_stripped.lower() for pattern in ['chapter', 'section', 'introduction', 'conclusion']))):
                sections.append({
                    'title': line_stripped,
                    'line_number': i,
                    'level': self._estimate_section_level(line_stripped)
                })
        
        return sections[:20]  # Limit to first 20 sections
    
    def _analyze_formatting(self, text: str) -> Dict[str, Any]:
        """
        Analyze text formatting characteristics.
        
        Args:
            text: Document text
            
        Returns:
            Formatting analysis
        """
        lines = text.split('\n')
        
        return {
            'total_lines': len(lines),
            'empty_lines': sum(1 for line in lines if not line.strip()),
            'average_line_length': sum(len(line) for line in lines) / len(lines) if lines else 0,
            'has_bullet_points': any('•' in line or '* ' in line for line in lines),
            'has_numbered_lists': any(line.strip().startswith(('1.', '2.', '3.')) for line in lines),
            'indentation_levels': len(set(len(line) - len(line.lstrip()) for line in lines if line.strip()))
        }
    
    def _estimate_section_level(self, title: str) -> int:
        """
        Estimate section level based on title format.
        
        Args:
            title: Section title
            
        Returns:
            Estimated section level (1-4)
        """
        title_lower = title.lower()
        
        if 'chapter' in title_lower:
            return 1
        elif any(word in title_lower for word in ['introduction', 'conclusion', 'abstract']):
            return 1
        elif title.strip().endswith(':'):
            return 2
        elif any(char.isdigit() for char in title):
            return 3
        else:
            return 4