"""
Text Chunking Implementations.

This package contains direct implementations of text chunking strategies.
All chunkers implement the TextChunker abstract base class and use
pure algorithms without external dependencies.

Available Chunkers:
- SentenceBoundaryChunker: Sentence-aware chunking for semantic coherence
- Future: SemanticChunker, StructuralChunker, FixedSizeChunker
"""

from .sentence_boundary import SentenceBoundaryChunker

__all__ = ['SentenceBoundaryChunker']