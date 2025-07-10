"""
Document Parser Adapters.

This package contains adapter implementations for external document parsing
libraries. Adapters wrap external APIs to provide consistent interfaces
following the DocumentParser abstract base class.

Available Adapters:
- PyMuPDFAdapter: PDF parsing using PyMuPDF (fitz)
- Future: DocxAdapter, HtmlAdapter, etc.
"""

from .pymupdf_adapter import PyMuPDFAdapter

__all__ = ['PyMuPDFAdapter']