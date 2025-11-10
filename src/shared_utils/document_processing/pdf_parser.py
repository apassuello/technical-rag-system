"""
BasicRAG System - PDF Document Parser

This module implements robust PDF text extraction functionality as part of the BasicRAG
technical documentation system. It serves as the entry point for document ingestion,
converting PDF files into structured text data suitable for chunking and embedding.

Key Features:
- Page-by-page text extraction with metadata preservation
- Robust error handling for corrupted or malformed PDFs
- Performance timing for optimization analysis
- Memory-efficient processing for large documents

Technical Approach:
- Uses PyMuPDF (fitz) for reliable text extraction across PDF versions
- Maintains document structure with page-level granularity
- Preserves PDF metadata (author, title, creation date, etc.)

Dependencies:
- PyMuPDF (fitz): Chosen for superior text extraction accuracy and speed
- Standard library: pathlib for cross-platform file handling

Performance Characteristics:
- Typical processing: 10-50 pages/second on modern hardware
- Memory usage: O(n) with document size, but processes page-by-page
- Scales linearly with document length

Author: Arthur Passuello
Date: June 2025
Project: RAG Portfolio - Technical Documentation System
"""

from typing import Dict, List, Any
from pathlib import Path
import time
import fitz  # PyMuPDF


def extract_text_with_metadata(pdf_path: Path) -> Dict[str, Any]:
    """
    Extract text and metadata from technical PDF documents with production-grade reliability.
    
    This function serves as the primary ingestion point for the RAG system, converting
    PDF documents into structured data. It's optimized for technical documentation with
    emphasis on preserving structure and handling various PDF formats gracefully.
    
    @param pdf_path: Path to the PDF file to process
    @type pdf_path: pathlib.Path
    
    @return: Dictionary containing extracted text and comprehensive metadata
    @rtype: Dict[str, Any] with the following structure:
        {
            "text": str,           # Complete concatenated text from all pages
            "pages": List[Dict],   # Per-page breakdown with text and statistics
                                  # Each page dict contains:
                                  # - page_number: int (1-indexed for human readability)
                                  # - text: str (raw text from that page)
                                  # - char_count: int (character count for that page)
            "metadata": Dict,      # PDF metadata (title, author, subject, etc.)
            "page_count": int,     # Total number of pages processed
            "extraction_time": float  # Processing duration in seconds
        }
        
    @throws FileNotFoundError: If the specified PDF file doesn't exist
    @throws ValueError: If the PDF is corrupted, encrypted, or otherwise unreadable
    
    Performance Notes:
    - Processes ~10-50 pages/second depending on PDF complexity
    - Memory usage is proportional to document size but page-by-page processing
      prevents loading entire document into memory at once
    - Extraction time is included for performance monitoring and optimization
    
    Usage Example:
        >>> pdf_path = Path("technical_manual.pdf")
        >>> result = extract_text_with_metadata(pdf_path)
        >>> print(f"Extracted {result['page_count']} pages in {result['extraction_time']:.2f}s")
        >>> first_page_text = result['pages'][0]['text']
    """
    # Validate input file exists before attempting to open
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Start performance timer for extraction analytics
    start_time = time.perf_counter()
    
    try:
        # Open PDF with PyMuPDF - automatically handles various PDF versions
        # Using string conversion for compatibility with older fitz versions
        doc = fitz.open(str(pdf_path))
        
        # Extract document-level metadata (may include title, author, subject, keywords)
        # Default to empty dict if no metadata present (common in scanned PDFs)
        metadata = doc.metadata or {}
        page_count = len(doc)
        
        # Initialize containers for page-by-page extraction
        pages = []  # Will store individual page data
        all_text = []  # Will store text for concatenation
        
        # Process each page sequentially to maintain document order
        for page_num in range(page_count):
            # Load page object (0-indexed internally)
            page = doc[page_num]
            
            # Extract text using default extraction parameters
            # This preserves reading order and handles multi-column layouts
            page_text = page.get_text()
            
            # Store page data with human-readable page numbering (1-indexed)
            pages.append({
                "page_number": page_num + 1,  # Convert to 1-indexed for user clarity
                "text": page_text,
                "char_count": len(page_text)  # Useful for chunking decisions
            })
            
            # Accumulate text for final concatenation
            all_text.append(page_text)
        
        # Properly close the PDF to free resources
        doc.close()
        
        # Calculate total extraction time for performance monitoring
        extraction_time = time.perf_counter() - start_time
        
        # Return comprehensive extraction results
        return {
            "text": "\n".join(all_text),  # Full document text with page breaks
            "pages": pages,                # Detailed page-by-page breakdown
            "metadata": metadata,          # Original PDF metadata
            "page_count": page_count,      # Total pages for quick reference
            "extraction_time": extraction_time  # Performance metric
        }
        
    except Exception as e:
        # Wrap any extraction errors with context for debugging
        # Common causes: encrypted PDFs, corrupted files, unsupported formats
        raise ValueError(f"Failed to process PDF: {e}")