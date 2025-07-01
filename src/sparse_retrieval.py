"""
Sparse Retrieval using BM25 algorithm for keyword-based document search.
Complements dense semantic search with exact term matching capabilities.
"""

from typing import List, Dict, Tuple, Optional
from rank_bm25 import BM25Okapi
import re
import time
import numpy as np


class BM25SparseRetriever:
    """
    BM25-based sparse retrieval for technical documentation.

    Optimized for technical terms, acronyms, and precise keyword matching
    that complements semantic similarity search in hybrid RAG systems.
    
    Performance: Handles 1000+ chunks efficiently with <100ms search times.
    """

    def __init__(self, k1: float = 1.2, b: float = 0.75):
        """
        BM25 retriever for technical documentation.

        Args:
            k1: Term frequency saturation parameter (1.2 typical)
                Higher values increase influence of term frequency
            b: Document length normalization factor (0.75 typical)
               0.0 = no normalization, 1.0 = full normalization

        Raises:
            ValueError: If k1 or b parameters are invalid
        """
        if k1 <= 0:
            raise ValueError("k1 must be positive")
        if not 0 <= b <= 1:
            raise ValueError("b must be between 0 and 1")
            
        self.k1 = k1
        self.b = b
        self.bm25: Optional[BM25Okapi] = None
        self.corpus: List[str] = []
        self.tokenized_corpus: List[List[str]] = []
        self.chunk_mapping: List[int] = []
        
        # Compile regex for technical term preservation
        self._tech_pattern = re.compile(r'[a-zA-Z0-9][\w\-_.]*[a-zA-Z0-9]|[a-zA-Z0-9]')
        self._punctuation_pattern = re.compile(r'[^\w\s\-_.]')

    def _preprocess_text(self, text: str) -> List[str]:
        """
        Preprocess text preserving technical terms and acronyms.
        
        Args:
            text: Raw text to tokenize
            
        Returns:
            List of preprocessed tokens
            
        Performance: ~10K tokens/second
        """
        if not text or not text.strip():
            return []
            
        # Convert to lowercase while preserving structure
        text = text.lower()
        
        # Remove punctuation except hyphens, underscores, periods in technical terms
        text = self._punctuation_pattern.sub(' ', text)
        
        # Extract technical terms (handles RISC-V, RV32I, ARM Cortex-M, etc.)
        tokens = self._tech_pattern.findall(text)
        
        # Filter out single characters and empty strings
        tokens = [token for token in tokens if len(token) > 1]
        
        return tokens

    def index_documents(self, chunks: List[Dict]) -> None:
        """
        Index chunk texts for BM25 search with performance monitoring.
        
        Args:
            chunks: List of chunk dictionaries with 'text' field
            
        Raises:
            ValueError: If chunks is empty or malformed
            KeyError: If chunks missing required 'text' field
            
        Performance: ~1000 chunks/second preprocessing + indexing
        """
        if not chunks:
            raise ValueError("Cannot index empty chunk list")
            
        start_time = time.time()
        
        # Extract and validate texts
        try:
            texts = [chunk['text'] for chunk in chunks]
        except KeyError:
            raise KeyError("All chunks must contain 'text' field")
            
        # Preprocess all texts
        self.corpus = texts
        self.tokenized_corpus = [self._preprocess_text(text) for text in texts]
        
        # Filter out empty tokenized texts and track mapping
        valid_corpus = []
        self.chunk_mapping = []
        
        for i, tokens in enumerate(self.tokenized_corpus):
            if tokens:  # Only include non-empty tokenized texts
                valid_corpus.append(tokens)
                self.chunk_mapping.append(i)
        
        if not valid_corpus:
            raise ValueError("No valid text content found in chunks")
            
        # Create BM25 index
        self.bm25 = BM25Okapi(valid_corpus, k1=self.k1, b=self.b)
        
        elapsed = time.time() - start_time
        tokens_per_sec = sum(len(tokens) for tokens in self.tokenized_corpus) / elapsed
        
        print(f"Indexed {len(chunks)} chunks ({len(valid_corpus)} valid) in {elapsed:.3f}s")
        print(f"Processing rate: {tokens_per_sec:.1f} tokens/second")

    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Search for relevant chunks using BM25 with normalized scores.
        
        Args:
            query: Search query string
            top_k: Maximum number of results to return
            
        Returns:
            List of (chunk_index, normalized_score) tuples sorted by relevance
            Scores normalized to [0,1] range for fusion compatibility
            
        Raises:
            ValueError: If not indexed or invalid parameters
            
        Performance: <100ms for 1000+ document corpus
        """
        if self.bm25 is None:
            raise ValueError("Must call index_documents() before searching")
            
        if not query or not query.strip():
            return []
            
        if top_k <= 0:
            raise ValueError("top_k must be positive")
            
        # Preprocess query using same method as documents
        query_tokens = self._preprocess_text(query)
        if not query_tokens:
            return []
            
        # Get BM25 scores for all documents
        scores = self.bm25.get_scores(query_tokens)
        
        if len(scores) == 0:
            return []
            
        # Normalize scores to [0,1] range
        max_score = np.max(scores)
        if max_score > 0:
            normalized_scores = scores / max_score
        else:
            normalized_scores = scores
            
        # Create results with original chunk indices
        results = [
            (self.chunk_mapping[i], float(normalized_scores[i])) 
            for i in range(len(scores))
        ]
        
        # Sort by score (descending) and return top_k
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]
