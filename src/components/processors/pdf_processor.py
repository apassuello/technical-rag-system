"""
PDF processor adapter for the modular RAG system.

This module provides an adapter that wraps the existing HybridParser
to conform to the DocumentProcessor interface, enabling it to be used
in the modular architecture while preserving all existing functionality.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from src.core.interfaces import Document, DocumentProcessor
from src.core.registry import register_component
from shared_utils.document_processing.hybrid_parser import HybridParser
from shared_utils.document_processing.toc_guided_parser import TOCGuidedParser


@register_component("processor", "hybrid_pdf")
class HybridPDFProcessor(DocumentProcessor):
    """
    Adapter for existing hybrid PDF parser.
    
    This class wraps the HybridParser to provide a DocumentProcessor interface
    while maintaining all the advanced parsing capabilities of the original
    implementation including TOC navigation, PDFPlumber extraction, and
    aggressive content filtering.
    
    Features:
    - TOC-guided navigation for reliable structure mapping
    - PDFPlumber precision with font/position analysis
    - Aggressive trash filtering while preserving technical content
    - Quality scoring for every chunk
    - Optimal chunk sizing (1200-1500 chars with 200 char overlap)
    
    Example:
        processor = HybridPDFProcessor(chunk_size=1024, chunk_overlap=128)
        documents = processor.process(Path("document.pdf"))
    """
    
    def __init__(
        self, 
        chunk_size: int = 1400, 
        chunk_overlap: int = 200,
        min_chunk_size: int = 800,
        max_chunk_size: int = 2000
    ):
        """
        Initialize the PDF processor.
        
        Args:
            chunk_size: Target chunk size in characters (default: 1400)
            chunk_overlap: Overlap between chunks in characters (default: 200)
            min_chunk_size: Minimum chunk size (default: 800)
            max_chunk_size: Maximum chunk size (default: 2000)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        
        # Initialize the hybrid parser with optimal settings
        self.hybrid_parser = HybridParser(
            target_chunk_size=chunk_size,
            min_chunk_size=min_chunk_size,
            max_chunk_size=max_chunk_size
        )
        
        # Initialize TOC parser for metadata extraction
        self.toc_parser = TOCGuidedParser()
    
    def process(self, file_path: Path) -> List[Document]:
        """
        Process a PDF document into a list of Document objects.
        
        This method uses the hybrid approach combining TOC navigation
        and PDFPlumber extraction to create high-quality document chunks.
        
        Args:
            file_path: Path to the PDF document
            
        Returns:
            List of Document objects with content, metadata, and embeddings
            
        Raises:
            ValueError: If file format is not supported or file doesn't exist
            IOError: If file cannot be read
        """
        if not file_path.exists():
            raise IOError(f"PDF file not found: {file_path}")
        
        if file_path.suffix.lower() != '.pdf':
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        try:
            # Extract PDF data using TOC parser for metadata
            pdf_data = self.toc_parser.extract_pdf_data(file_path)
            
            # Parse document using hybrid approach
            chunks = self.hybrid_parser.parse_document(file_path, pdf_data)
            
            # Convert chunks to Document objects
            documents = []
            for chunk_data in chunks:
                doc = self._create_document_from_chunk(chunk_data, file_path)
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            raise IOError(f"Failed to process PDF {file_path}: {str(e)}") from e
    
    def supported_formats(self) -> List[str]:
        """
        Return list of supported file extensions.
        
        Returns:
            List of supported extensions
        """
        return ['.pdf']
    
    def _create_document_from_chunk(
        self, 
        chunk_data: Dict[str, Any], 
        source_path: Path
    ) -> Document:
        """
        Create a Document object from chunk data.
        
        Args:
            chunk_data: Chunk data from hybrid parser
            source_path: Path to source document
            
        Returns:
            Document object with standardized metadata
        """
        # Extract content from chunk
        content = chunk_data.get('content', '')
        
        # Create comprehensive metadata
        metadata = {
            # Source information
            'source': str(source_path),
            'source_name': source_path.name,
            'source_type': 'pdf',
            
            # Chunk information
            'chunk_id': chunk_data.get('chunk_id', 0),
            'chunk_size': len(content),
            'content_hash': chunk_data.get('content_hash', ''),
            
            # Position information
            'start_page': chunk_data.get('start_page', 1),
            'end_page': chunk_data.get('end_page', 1),
            'page_numbers': chunk_data.get('page_numbers', []),
            
            # Quality metrics
            'quality_score': chunk_data.get('quality_score', 0.0),
            'is_clean': chunk_data.get('is_clean', True),
            
            # Structure information
            'toc_section': chunk_data.get('toc_section', ''),
            'section_title': chunk_data.get('section_title', ''),
            'section_level': chunk_data.get('section_level', 0),
            
            # Processing metadata
            'processing_method': 'hybrid_toc_pdfplumber',
            'chunk_overlap': self.chunk_overlap,
            'target_chunk_size': self.chunk_size,
            
            # Additional fields from original chunk
            **{k: v for k, v in chunk_data.items() if k not in [
                'content', 'chunk_id', 'content_hash', 'start_page', 
                'end_page', 'page_numbers', 'quality_score', 'is_clean',
                'toc_section', 'section_title', 'section_level'
            ]}
        }
        
        return Document(
            content=content,
            metadata=metadata,
            embedding=None  # Embeddings will be added later
        )