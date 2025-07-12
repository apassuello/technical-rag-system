"""
Maximal Marginal Relevance (MMR) Context Selector Implementation.

This module provides context selection using the Maximal Marginal Relevance
algorithm to balance relevance and diversity in document selection.

MMR Formula:
MMR = λ * Relevance(doc, query) - (1-λ) * max(Similarity(doc, selected_doc))

Features:
- Configurable relevance-diversity trade-off (lambda parameter)
- Efficient similarity computation using document embeddings
- Token-aware selection with safety margins
- Comprehensive metadata tracking
"""

import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import sys

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from ..base import ContextSelection, QueryAnalysis
from .base_selector import BaseContextSelector
from src.core.interfaces import Document

logger = logging.getLogger(__name__)


class MMRSelector(BaseContextSelector):
    """
    Maximal Marginal Relevance context selector.
    
    This selector implements the MMR algorithm to choose documents that
    balance relevance to the query with diversity among selected documents.
    This helps avoid redundant information while maintaining high relevance.
    
    Configuration Options:
    - lambda_param: Relevance vs diversity trade-off (0.0-1.0, default: 0.5)
    - min_relevance: Minimum relevance score to consider (default: 0.0)
    - similarity_threshold: Maximum similarity allowed between selected docs (default: 0.9)
    - use_query_similarity: Use query-document similarity for relevance (default: True)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize MMR selector with configuration.
        
        Args:
            config: Configuration dictionary
        """
        # Initialize attributes first before calling super().__init__
        config_dict = config or {}
        self._lambda_param = config_dict.get('lambda_param', 0.5)
        self._min_relevance = config_dict.get('min_relevance', 0.0)
        self._similarity_threshold = config_dict.get('similarity_threshold', 0.9)
        self._use_query_similarity = config_dict.get('use_query_similarity', True)
        
        super().__init__(config)
        
        # Validate lambda parameter
        if not 0.0 <= self._lambda_param <= 1.0:
            logger.warning(f"Invalid lambda_param {self._lambda_param}, using 0.5")
            self._lambda_param = 0.5
        
        logger.debug(f"Initialized MMRSelector with lambda={self._lambda_param}")
    
    def _select_documents(
        self,
        query: str,
        documents: List[Document], 
        max_tokens: int,
        query_analysis: Optional[QueryAnalysis] = None
    ) -> ContextSelection:
        """
        Select documents using Maximal Marginal Relevance algorithm.
        
        Args:
            query: Clean, validated query string
            documents: Valid list of documents
            max_tokens: Positive token limit
            query_analysis: Optional query analysis
            
        Returns:
            ContextSelection with MMR-selected documents and metadata
        """
        effective_max_tokens = self._get_effective_max_tokens(max_tokens)
        
        # Filter by minimum relevance if configured
        candidate_docs = self._filter_documents_by_score(documents, self._min_relevance)
        
        if not candidate_docs:
            return ContextSelection(
                selected_documents=[],
                total_tokens=0,
                selection_strategy="mmr",
                metadata={'reason': 'no_documents_meet_min_relevance', 'min_relevance': self._min_relevance}
            )
        
        # Sort candidates by relevance score (highest first)
        candidate_docs = self._sort_documents_by_score(candidate_docs, descending=True)
        
        # Apply MMR selection
        selected_docs, selection_metadata = self._apply_mmr_selection(
            query, candidate_docs, effective_max_tokens, query_analysis
        )
        
        # Calculate final metrics
        total_tokens = sum(self.estimate_tokens(doc.content) for doc in selected_docs)
        diversity_score = self._calculate_diversity_score(selected_docs)
        relevance_score = self._calculate_relevance_score(selected_docs)
        
        return ContextSelection(
            selected_documents=selected_docs,
            total_tokens=total_tokens,
            selection_strategy="mmr",
            diversity_score=diversity_score,
            relevance_score=relevance_score,
            metadata={
                'mmr_lambda': self._lambda_param,
                'candidates_considered': len(candidate_docs),
                'token_limit': effective_max_tokens,
                'safety_margin_used': self._safety_margin,
                **selection_metadata
            }
        )
    
    def _apply_mmr_selection(
        self,
        query: str,
        candidate_docs: List[Document],
        max_tokens: int,
        query_analysis: Optional[QueryAnalysis] = None
    ) -> Tuple[List[Document], Dict[str, Any]]:
        """
        Apply MMR algorithm to select documents.
        
        Args:
            query: User query
            candidate_docs: Documents to select from (sorted by relevance)
            max_tokens: Maximum tokens allowed
            query_analysis: Optional query analysis
            
        Returns:
            Tuple of (selected_documents, selection_metadata)
        """
        selected_docs = []
        remaining_tokens = max_tokens
        mmr_scores = []
        
        # Track why selection stopped
        selection_end_reason = "max_tokens_reached"
        
        # Get query embedding if available and needed
        query_embedding = self._get_query_embedding(query, query_analysis)
        
        # Pre-compute document embeddings for similarity calculations
        doc_embeddings = self._get_document_embeddings(candidate_docs)
        
        while candidate_docs and remaining_tokens > 0:
            best_doc = None
            best_mmr_score = -float('inf')
            best_doc_idx = -1
            
            # Calculate MMR score for each remaining candidate
            for i, candidate in enumerate(candidate_docs):
                mmr_score = self._calculate_mmr_score(
                    candidate, i, selected_docs, query_embedding, doc_embeddings
                )
                
                # Check if this document would fit within token limit
                doc_tokens = self.estimate_tokens(candidate.content)
                if doc_tokens <= remaining_tokens:
                    if mmr_score > best_mmr_score:
                        best_mmr_score = mmr_score
                        best_doc = candidate
                        best_doc_idx = i
            
            # If no document fits, we're done
            if best_doc is None:
                if not selected_docs:
                    # No documents fit at all - try to fit the smallest one
                    smallest_doc = min(candidate_docs, key=lambda d: self.estimate_tokens(d.content))
                    smallest_tokens = self.estimate_tokens(smallest_doc.content)
                    if smallest_tokens <= max_tokens:  # Use original max_tokens for last resort
                        selected_docs.append(smallest_doc)
                        selection_end_reason = "forced_smallest_document"
                    else:
                        selection_end_reason = "no_documents_fit"
                break
            
            # Add best document to selection
            selected_docs.append(best_doc)
            best_doc_tokens = self.estimate_tokens(best_doc.content)
            remaining_tokens -= best_doc_tokens
            mmr_scores.append(best_mmr_score)
            
            # Remove selected document from candidates
            candidate_docs.pop(best_doc_idx)
            if doc_embeddings is not None:
                doc_embeddings = np.delete(doc_embeddings, best_doc_idx, axis=0)
            
            # Check if we've reached document limits
            if len(selected_docs) >= self._max_documents:
                selection_end_reason = "max_documents_reached"
                break
        
        # If no documents were selected due to constraints
        if not selected_docs and candidate_docs:
            selection_end_reason = "constraints_too_restrictive"
        
        metadata = {
            'mmr_scores': mmr_scores,
            'selection_end_reason': selection_end_reason,
            'remaining_tokens': remaining_tokens,
            'documents_considered': len(candidate_docs) + len(selected_docs),
            'query_embedding_available': query_embedding is not None,
            'doc_embeddings_available': doc_embeddings is not None
        }
        
        return selected_docs, metadata
    
    def _calculate_mmr_score(
        self,
        candidate: Document,
        candidate_idx: int,
        selected_docs: List[Document],
        query_embedding: Optional[np.ndarray],
        doc_embeddings: Optional[np.ndarray]
    ) -> float:
        """
        Calculate MMR score for a candidate document.
        
        MMR = λ * Relevance(doc, query) - (1-λ) * max(Similarity(doc, selected_doc))
        
        Args:
            candidate: Candidate document
            candidate_idx: Index of candidate in embeddings array
            selected_docs: Already selected documents
            query_embedding: Query embedding vector (optional)
            doc_embeddings: Document embedding matrix (optional)
            
        Returns:
            MMR score for the candidate
        """
        # Relevance term (λ * Relevance)
        relevance = self._get_document_relevance(candidate, query_embedding, candidate_idx, doc_embeddings)
        relevance_term = self._lambda_param * relevance
        
        # Diversity term ((1-λ) * max(Similarity))
        if not selected_docs:
            # First document - no diversity penalty
            diversity_term = 0.0
        else:
            max_similarity = self._calculate_max_similarity(
                candidate, candidate_idx, selected_docs, doc_embeddings
            )
            diversity_term = (1 - self._lambda_param) * max_similarity
        
        return relevance_term - diversity_term
    
    def _get_document_relevance(
        self,
        document: Document,
        query_embedding: Optional[np.ndarray],
        doc_idx: int,
        doc_embeddings: Optional[np.ndarray]
    ) -> float:
        """
        Get relevance score for a document.
        
        Args:
            document: Document to score
            query_embedding: Query embedding (optional)
            doc_idx: Document index in embeddings
            doc_embeddings: Document embeddings (optional)
            
        Returns:
            Relevance score between 0.0 and 1.0
        """
        # Primary: Use retrieval score if available
        if hasattr(document, 'score') and document.score is not None:
            return min(1.0, max(0.0, document.score))
        
        # Secondary: Use embedding similarity if available
        if (self._use_query_similarity and 
            query_embedding is not None and 
            doc_embeddings is not None and 
            doc_idx < len(doc_embeddings)):
            
            doc_embedding = doc_embeddings[doc_idx]
            similarity = self._calculate_cosine_similarity(query_embedding, doc_embedding)
            return max(0.0, similarity)  # Ensure non-negative
        
        # Fallback: Use default relevance
        return 0.5
    
    def _calculate_max_similarity(
        self,
        candidate: Document,
        candidate_idx: int,
        selected_docs: List[Document],
        doc_embeddings: Optional[np.ndarray]
    ) -> float:
        """
        Calculate maximum similarity between candidate and selected documents.
        
        Args:
            candidate: Candidate document
            candidate_idx: Index of candidate in embeddings
            selected_docs: Already selected documents
            doc_embeddings: Document embeddings (optional)
            
        Returns:
            Maximum similarity score
        """
        if not selected_docs:
            return 0.0
        
        max_sim = 0.0
        
        # Use embeddings if available
        if doc_embeddings is not None and candidate_idx < len(doc_embeddings):
            candidate_embedding = doc_embeddings[candidate_idx]
            
            for selected_doc in selected_docs:
                # Find embedding for selected document
                selected_embedding = getattr(selected_doc, 'embedding', None)
                if selected_embedding is not None:
                    similarity = self._calculate_cosine_similarity(candidate_embedding, selected_embedding)
                    max_sim = max(max_sim, similarity)
        
        # Fallback: Simple text-based similarity
        if max_sim == 0.0:
            for selected_doc in selected_docs:
                text_similarity = self._calculate_text_similarity(candidate.content, selected_doc.content)
                max_sim = max(max_sim, text_similarity)
        
        return max_sim
    
    def _calculate_cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity between -1 and 1
        """
        try:
            # Ensure vectors are numpy arrays
            vec1 = np.asarray(vec1)
            vec2 = np.asarray(vec2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.warning(f"Failed to calculate cosine similarity: {e}")
            return 0.0
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple text-based similarity as fallback.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Simple Jaccard similarity on words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _get_query_embedding(
        self, 
        query: str, 
        query_analysis: Optional[QueryAnalysis]
    ) -> Optional[np.ndarray]:
        """
        Get query embedding for similarity calculations.
        
        Args:
            query: Query string
            query_analysis: Optional query analysis with embedding
            
        Returns:
            Query embedding vector or None
        """
        # Check if query analysis contains embedding
        if query_analysis and hasattr(query_analysis, 'metadata'):
            metadata = query_analysis.metadata
            if 'query_embedding' in metadata:
                return np.asarray(metadata['query_embedding'])
        
        # No query embedding available
        return None
    
    def _get_document_embeddings(self, documents: List[Document]) -> Optional[np.ndarray]:
        """
        Extract document embeddings into matrix for efficient computation.
        
        Args:
            documents: List of documents
            
        Returns:
            Matrix of document embeddings or None
        """
        embeddings = []
        
        for doc in documents:
            if hasattr(doc, 'embedding') and doc.embedding is not None:
                embeddings.append(np.asarray(doc.embedding))
            else:
                # No embedding available for this document
                return None
        
        if embeddings:
            try:
                return np.array(embeddings)
            except Exception as e:
                logger.warning(f"Failed to create embedding matrix: {e}")
                return None
        
        return None
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the MMR selector with provided settings.
        
        Args:
            config: Configuration dictionary
        """
        super().configure(config)
        
        # Update MMR-specific configuration
        if 'lambda_param' in config:
            new_lambda = config['lambda_param']
            if 0.0 <= new_lambda <= 1.0:
                self._lambda_param = new_lambda
            else:
                logger.warning(f"Invalid lambda_param {new_lambda}, keeping {self._lambda_param}")
        
        self._min_relevance = config.get('min_relevance', self._min_relevance)
        self._similarity_threshold = config.get('similarity_threshold', self._similarity_threshold)
        self._use_query_similarity = config.get('use_query_similarity', self._use_query_similarity)
    
    def get_configuration(self) -> Dict[str, Any]:
        """
        Get current MMR configuration.
        
        Returns:
            Configuration dictionary
        """
        base_config = self._config.copy()
        base_config.update({
            'lambda_param': self._lambda_param,
            'min_relevance': self._min_relevance,
            'similarity_threshold': self._similarity_threshold,
            'use_query_similarity': self._use_query_similarity,
            'selector_type': 'mmr'
        })
        return base_config