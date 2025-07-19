"""
BM25 Sparse Retriever implementation for Modular Retriever Architecture.

This module provides a direct implementation of BM25 sparse retrieval
extracted from the existing sparse retrieval system for improved modularity.
"""

import logging
import re
import time
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from rank_bm25 import BM25Okapi

from src.core.interfaces import Document
from .base import SparseRetriever

logger = logging.getLogger(__name__)


class BM25Retriever(SparseRetriever):
    """
    BM25-based sparse retrieval implementation.
    
    This is a direct implementation that handles BM25 keyword search
    without external adapters. It provides efficient sparse retrieval
    for technical documentation with optimized tokenization.
    
    Features:
    - Technical term preservation (handles RISC-V, ARM Cortex-M, etc.)
    - Configurable BM25 parameters (k1, b)
    - Normalized scoring for fusion compatibility
    - Efficient preprocessing and indexing
    - Performance monitoring
    
    Example:
        config = {
            "k1": 1.2,
            "b": 0.75,
            "lowercase": True,
            "preserve_technical_terms": True
        }
        retriever = BM25Retriever(config)
        retriever.index_documents(documents)
        results = retriever.search("RISC-V processor", k=5)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize BM25 sparse retriever.
        
        Args:
            config: Configuration dictionary with:
                - k1: Term frequency saturation parameter (default: 1.2)
                - b: Document length normalization factor (default: 0.75)
                - lowercase: Whether to lowercase text (default: True)
                - preserve_technical_terms: Whether to preserve technical terms (default: True)
                - filter_stop_words: Whether to filter common stop words (default: True)
                - custom_stop_words: Additional stop words to filter (default: empty list)
        """
        self.config = config
        self.k1 = config.get("k1", 1.2)
        self.b = config.get("b", 0.75)
        self.lowercase = config.get("lowercase", True)
        self.preserve_technical_terms = config.get("preserve_technical_terms", True)
        self.filter_stop_words = config.get("filter_stop_words", True)
        self.custom_stop_words = set(config.get("custom_stop_words", []))
        
        # Standard English stop words for BM25 filtering
        self.standard_stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he', 'in', 'is', 'it',
            'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were', 'will', 'with', 'the', 'this', 'but',
            'they', 'have', 'had', 'what', 'said', 'each', 'which', 'she', 'do', 'how', 'their', 'if',
            'up', 'out', 'many', 'then', 'them', 'these', 'so', 'some', 'her', 'would', 'make', 'like',
            'into', 'him', 'time', 'two', 'more', 'go', 'no', 'way', 'could', 'my', 'than', 'first',
            'been', 'call', 'who', 'oil', 'sit', 'now', 'find', 'down', 'day', 'did', 'get', 'come',
            'made', 'may', 'part', 'where', 'much', 'too', 'any', 'after', 'back', 'other', 'see',
            'want', 'just', 'also', 'when', 'here', 'all', 'well', 'can', 'should', 'must', 'might',
            'shall', 'about', 'before', 'through', 'over', 'under', 'above', 'below', 'between', 'among'
        }
        
        # Combine standard and custom stop words
        if self.filter_stop_words:
            self.stop_words = self.standard_stop_words | self.custom_stop_words
        else:
            self.stop_words = self.custom_stop_words
        
        # Validation
        if self.k1 <= 0:
            raise ValueError("k1 must be positive")
        if not 0 <= self.b <= 1:
            raise ValueError("b must be between 0 and 1")
        
        # BM25 components
        self.bm25: Optional[BM25Okapi] = None
        self.documents: List[Document] = []
        self.tokenized_corpus: List[List[str]] = []
        self.chunk_mapping: List[int] = []
        
        # Deferred indexing control
        self._index_dirty = False  # Track if index needs rebuilding
        self._deferred_mode = False  # Enable deferred indexing mode
        
        # Compile regex patterns for technical term preservation
        if self.preserve_technical_terms:
            self._tech_pattern = re.compile(r'[a-zA-Z0-9][\w\-_.]*[a-zA-Z0-9]|[a-zA-Z0-9]')
            self._punctuation_pattern = re.compile(r'[^\w\s\-_.]')
        else:
            self._tech_pattern = re.compile(r'\b\w+\b')
            self._punctuation_pattern = re.compile(r'[^\w\s]')
        
        logger.info(f"BM25Retriever initialized with k1={self.k1}, b={self.b}, stop_words={len(self.stop_words) if self.stop_words else 0}")
    
    def enable_deferred_indexing(self) -> None:
        """Enable deferred indexing mode to avoid rebuilding index on every batch"""
        self._deferred_mode = True
        logger.debug("Deferred indexing mode enabled")
    
    def disable_deferred_indexing(self) -> None:
        """Disable deferred indexing mode and rebuild index if needed"""
        self._deferred_mode = False
        if self._index_dirty:
            self._rebuild_index()
        logger.debug("Deferred indexing mode disabled")
    
    def force_rebuild_index(self) -> None:
        """Force rebuild the BM25 index with all accumulated documents"""
        if self.tokenized_corpus:
            self._rebuild_index()
        else:
            logger.warning("No documents to rebuild index")
    
    def _rebuild_index(self) -> None:
        """Internal method to rebuild the BM25 index"""
        if not self.tokenized_corpus:
            logger.warning("No tokenized corpus available for index rebuild")
            return
        
        start_time = time.time()
        self.bm25 = BM25Okapi(self.tokenized_corpus, k1=self.k1, b=self.b)
        self._index_dirty = False
        
        elapsed = time.time() - start_time
        total_tokens = sum(len(tokens) for tokens in self.tokenized_corpus)
        valid_doc_count = len([tokens for tokens in self.tokenized_corpus if tokens])
        
        logger.info(f"Rebuilt BM25 index with {valid_doc_count} documents in {elapsed:.3f}s")
    
    def index_documents(self, documents: List[Document]) -> None:
        """
        Index documents for BM25 sparse retrieval.
        
        Args:
            documents: List of documents to index
        """
        if not documents:
            raise ValueError("Cannot index empty document list")
        
        start_time = time.time()
        
        # Store documents (extend existing instead of replacing)
        if not hasattr(self, 'documents') or self.documents is None:
            self.documents = []
        if not hasattr(self, 'tokenized_corpus') or self.tokenized_corpus is None:
            self.tokenized_corpus = []
        if not hasattr(self, 'chunk_mapping') or self.chunk_mapping is None:
            self.chunk_mapping = []
        
        # Keep track of starting index for new documents
        start_idx = len(self.documents)
        
        # Add new documents
        self.documents.extend(documents)
        
        # Extract and preprocess texts for new documents only
        texts = [doc.content for doc in documents]
        new_tokenized = [self._preprocess_text(text) for text in texts]
        
        # Filter out empty tokenized texts and track mapping for new documents
        for i, tokens in enumerate(new_tokenized):
            if tokens:  # Only include non-empty tokenized texts
                self.tokenized_corpus.append(tokens)
                self.chunk_mapping.append(start_idx + i)
        
        if not self.tokenized_corpus:
            raise ValueError("No valid text content found in documents")
        
        # Rebuild BM25 index unless in deferred mode
        if self._deferred_mode:
            # Mark index as dirty but don't rebuild yet
            self._index_dirty = True
            logger.debug(f"Added {len(documents)} documents to corpus (deferred mode - index not rebuilt)")
        else:
            # Rebuild index immediately (original behavior)
            self._rebuild_index()
        
        elapsed = time.time() - start_time
        total_tokens = sum(len(tokens) for tokens in self.tokenized_corpus)
        tokens_per_sec = total_tokens / elapsed if elapsed > 0 else 0
        
        valid_doc_count = len([tokens for tokens in self.tokenized_corpus if tokens])
        logger.info(f"Indexed {len(documents)} new documents ({valid_doc_count} total valid) in {elapsed:.3f}s")
        logger.debug(f"Processing rate: {tokens_per_sec:.1f} tokens/second")
    
    def search(self, query: str, k: int = 5) -> List[Tuple[int, float]]:
        """
        Search for documents using BM25 sparse retrieval.
        
        Args:
            query: Search query string
            k: Number of results to return
            
        Returns:
            List of (document_index, score) tuples sorted by relevance
        """
        # Ensure index is built before searching
        if self.bm25 is None or self._index_dirty:
            if self._index_dirty:
                logger.debug("Rebuilding BM25 index before search (was dirty)")
                self._rebuild_index()
            else:
                raise ValueError("Must call index_documents() before searching")
        
        if not query or not query.strip():
            return []
        
        if k <= 0:
            raise ValueError("k must be positive")
        
        # Preprocess query using same method as documents
        query_tokens = self._preprocess_text(query)
        if not query_tokens:
            return []
        
        # Get BM25 scores for all documents
        scores = self.bm25.get_scores(query_tokens)
        
        if len(scores) == 0:
            return []
        
        # Normalize scores to [0,1] range for fusion compatibility
        max_score = np.max(scores)
        if max_score > 0:
            normalized_scores = scores / max_score
        else:
            normalized_scores = scores
        
        # Create results with original document indices
        results = [
            (self.chunk_mapping[i], float(normalized_scores[i]))
            for i in range(len(scores))
        ]
        
        # Sort by score (descending) and return top_k
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:k]
    
    def get_document_count(self) -> int:
        """Get the number of indexed documents."""
        return len(self.documents)
    
    def clear(self) -> None:
        """Clear all indexed documents."""
        self.documents.clear()
        self.tokenized_corpus.clear()
        self.chunk_mapping.clear()
        self.bm25 = None
        logger.info("BM25 index cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the BM25 retriever.
        
        Returns:
            Dictionary with retriever statistics
        """
        stats = {
            "k1": self.k1,
            "b": self.b,
            "lowercase": self.lowercase,
            "preserve_technical_terms": self.preserve_technical_terms,
            "filter_stop_words": self.filter_stop_words,
            "stop_words_count": len(self.stop_words) if self.stop_words else 0,
            "total_documents": len(self.documents),
            "valid_documents": len(self.chunk_mapping),
            "is_indexed": self.bm25 is not None
        }
        
        if self.tokenized_corpus:
            total_tokens = sum(len(tokens) for tokens in self.tokenized_corpus)
            stats.update({
                "total_tokens": total_tokens,
                "avg_tokens_per_doc": total_tokens / len(self.tokenized_corpus) if self.tokenized_corpus else 0
            })
        
        return stats
    
    def _preprocess_text(self, text: str) -> List[str]:
        """
        Preprocess text preserving technical terms and acronyms.
        
        Args:
            text: Raw text to tokenize
            
        Returns:
            List of preprocessed tokens
        """
        if not text or not text.strip():
            return []
        
        # Convert to lowercase while preserving structure
        if self.lowercase:
            text = text.lower()
        
        # Remove punctuation except hyphens, underscores, periods in technical terms
        text = self._punctuation_pattern.sub(' ', text)
        
        # Extract tokens using appropriate pattern
        tokens = self._tech_pattern.findall(text)
        
        # Filter out single characters and empty strings
        tokens = [token for token in tokens if len(token) > 1]
        
        # Filter out stop words if enabled
        if self.stop_words:
            tokens = [token for token in tokens if token.lower() not in self.stop_words]
        
        return tokens
    
    def get_query_tokens(self, query: str) -> List[str]:
        """
        Get preprocessed tokens for a query (useful for debugging).
        
        Args:
            query: Query string
            
        Returns:
            List of preprocessed tokens
        """
        return self._preprocess_text(query)
    
    def get_document_tokens(self, doc_index: int) -> List[str]:
        """
        Get preprocessed tokens for a document (useful for debugging).
        
        Args:
            doc_index: Document index
            
        Returns:
            List of preprocessed tokens
        """
        if 0 <= doc_index < len(self.tokenized_corpus):
            return self.tokenized_corpus[doc_index]
        else:
            raise IndexError(f"Document index {doc_index} out of range")
    
    def get_bm25_scores(self, query: str) -> List[float]:
        """
        Get raw BM25 scores for all documents (useful for debugging).
        
        Args:
            query: Query string
            
        Returns:
            List of BM25 scores (not normalized)
        """
        if self.bm25 is None:
            raise ValueError("Must call index_documents() before getting scores")
        
        query_tokens = self._preprocess_text(query)
        if not query_tokens:
            return []
        
        scores = self.bm25.get_scores(query_tokens)
        return scores.tolist()
    
    def get_term_frequencies(self, query: str) -> Dict[str, int]:
        """
        Get term frequencies for a query (useful for analysis).
        
        Args:
            query: Query string
            
        Returns:
            Dictionary mapping terms to frequencies
        """
        query_tokens = self._preprocess_text(query)
        term_freqs = {}
        for token in query_tokens:
            term_freqs[token] = term_freqs.get(token, 0) + 1
        return term_freqs