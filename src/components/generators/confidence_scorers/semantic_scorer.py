"""
Semantic confidence scorer implementation.

This module provides a confidence scorer that evaluates answer quality
based on semantic coherence between query, answer, and context.

Architecture Notes:
- Direct implementation (no adapter needed)
- Pure scoring algorithm without external dependencies
- Uses embeddings for semantic similarity
- Configurable thresholds and weights
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from ..base import ConfidenceScorer, Document, ConfigurableComponent

logger = logging.getLogger(__name__)


class SemanticScorer(ConfidenceScorer, ConfigurableComponent):
    """
    Semantic coherence-based confidence scorer.
    
    Features:
    - Query-answer relevance scoring
    - Answer-context grounding verification
    - Length and quality heuristics
    - Configurable scoring weights
    
    Configuration:
    - min_answer_length: Minimum answer length for high confidence (default: 20)
    - max_answer_length: Maximum reasonable answer length (default: 1000)
    - relevance_weight: Weight for query-answer relevance (default: 0.4)
    - grounding_weight: Weight for context grounding (default: 0.4)
    - quality_weight: Weight for answer quality metrics (default: 0.2)
    - low_retrieval_penalty: Penalty when few documents retrieved (default: 0.3)
    - min_context_documents: Minimum documents for full confidence (default: 3)
    """
    
    def __init__(self,
                 min_answer_length: int = 20,
                 max_answer_length: int = 1000,
                 relevance_weight: float = 0.4,
                 grounding_weight: float = 0.4,
                 quality_weight: float = 0.2,
                 low_retrieval_penalty: float = 0.3,
                 min_context_documents: int = 3,
                 embedder=None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize semantic scorer.
        
        Args:
            min_answer_length: Minimum answer length for high confidence
            max_answer_length: Maximum reasonable answer length
            relevance_weight: Weight for query-answer relevance
            grounding_weight: Weight for context grounding
            quality_weight: Weight for answer quality metrics
            low_retrieval_penalty: Penalty applied when few documents retrieved (default: 0.3)
            min_context_documents: Minimum documents needed for full confidence (default: 3)
            embedder: Optional embedder for semantic similarity (uses simple if None)
            config: Additional configuration
        """
        # Merge config
        scorer_config = {
            'min_answer_length': min_answer_length,
            'max_answer_length': max_answer_length,
            'relevance_weight': relevance_weight,
            'grounding_weight': grounding_weight,
            'quality_weight': quality_weight,
            'low_retrieval_penalty': low_retrieval_penalty,
            'min_context_documents': min_context_documents,
            **(config or {})
        }
        
        super().__init__(scorer_config)
        
        # Set configuration
        self.min_answer_length = scorer_config['min_answer_length']
        self.max_answer_length = scorer_config['max_answer_length']
        self.relevance_weight = scorer_config['relevance_weight']
        self.grounding_weight = scorer_config['grounding_weight']
        self.quality_weight = scorer_config['quality_weight']
        self.low_retrieval_penalty = scorer_config['low_retrieval_penalty']
        self.min_context_documents = scorer_config['min_context_documents']
        
        # Normalize weights
        total_weight = self.relevance_weight + self.grounding_weight + self.quality_weight
        if total_weight > 0:
            self.relevance_weight /= total_weight
            self.grounding_weight /= total_weight
            self.quality_weight /= total_weight
        
        # Embedder for semantic similarity (optional)
        self.embedder = embedder
    
    def set_embedder(self, embedder):
        """Set the embedder for semantic similarity calculations."""
        self.embedder = embedder
    
    def score(self, query: str, answer: str, context: List[Document]) -> float:
        """
        Calculate confidence score for the generated answer.
        
        Args:
            query: Original query
            answer: Generated answer text
            context: Context documents used
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Calculate component scores
        relevance_score = self._calculate_relevance(query, answer)
        grounding_score = self._calculate_grounding(answer, context)
        quality_score = self._calculate_quality(answer)
        
        # Weighted combination
        final_score = (
            self.relevance_weight * relevance_score +
            self.grounding_weight * grounding_score +
            self.quality_weight * quality_score
        )
        
        # Apply low retrieval penalty if insufficient context documents
        retrieval_penalty = 0.0
        if len(context) < self.min_context_documents:
            # Linear penalty based on how many documents are missing
            penalty_factor = 1.0 - (len(context) / self.min_context_documents)
            retrieval_penalty = self.low_retrieval_penalty * penalty_factor
            final_score = final_score * (1.0 - retrieval_penalty)
        
        # Log component scores for debugging
        logger.debug(
            f"Semantic scores - Relevance: {relevance_score:.3f}, "
            f"Grounding: {grounding_score:.3f}, Quality: {quality_score:.3f}, "
            f"Context docs: {len(context)}, Retrieval penalty: {retrieval_penalty:.3f}, "
            f"Final: {final_score:.3f}"
        )
        
        return float(np.clip(final_score, 0.0, 1.0))
    
    def get_scoring_method(self) -> str:
        """Return the name of the scoring method."""
        return "semantic"
    
    def get_scorer_info(self) -> Dict[str, Any]:
        """Get information about the scorer."""
        return {
            'type': 'semantic',
            'scorer_class': self.__class__.__name__,
            'weights': {
                'relevance': self.relevance_weight,
                'grounding': self.grounding_weight,
                'quality': self.quality_weight
            },
            'thresholds': {
                'min_answer_length': self.min_answer_length,
                'max_answer_length': self.max_answer_length
            },
            'retrieval_penalty': {
                'low_retrieval_penalty': self.low_retrieval_penalty,
                'min_context_documents': self.min_context_documents
            },
            'uses_embeddings': self.embedder is not None
        }
    
    def _calculate_relevance(self, query: str, answer: str) -> float:
        """
        Calculate query-answer relevance score.
        
        Args:
            query: User query
            answer: Generated answer
            
        Returns:
            Relevance score (0-1)
        """
        if not query or not answer:
            return 0.0
        
        # If we have an embedder, use semantic similarity
        if self.embedder:
            try:
                query_emb = np.array(self.embedder.embed([query])[0])
                answer_emb = np.array(self.embedder.embed([answer])[0])
                similarity = cosine_similarity(
                    query_emb.reshape(1, -1),
                    answer_emb.reshape(1, -1)
                )[0, 0]
                return float(similarity)
            except Exception as e:
                logger.warning(f"Embedding-based relevance failed: {str(e)}")
        
        # Fallback: Simple keyword overlap
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())
        
        # Remove stop words (simple list)
        stop_words = {'the', 'is', 'at', 'which', 'on', 'and', 'a', 'an', 'as', 'are', 'was', 'were', 'be', 'have', 'has', 'had', 'it', 'to', 'of', 'in', 'for', 'with'}
        query_words -= stop_words
        answer_words -= stop_words
        
        if not query_words:
            return 0.5  # Neutral score if no meaningful words
        
        # Calculate overlap
        overlap = len(query_words & answer_words)
        relevance = overlap / len(query_words)
        
        # Boost score if answer is comprehensive (contains more relevant words)
        if len(answer_words) > len(query_words):
            relevance = min(relevance * 1.2, 1.0)
        
        return relevance
    
    def _calculate_grounding(self, answer: str, context: List[Document]) -> float:
        """
        Calculate how well the answer is grounded in context.
        
        Args:
            answer: Generated answer
            context: Context documents
            
        Returns:
            Grounding score (0-1)
        """
        if not answer or not context:
            return 0.0
        
        # Combine all context
        context_text = ' '.join(doc.content for doc in context)
        
        # If we have embedder, use semantic similarity
        if self.embedder:
            try:
                answer_emb = np.array(self.embedder.embed([answer])[0])
                context_emb = np.array(self.embedder.embed([context_text[:2000]])[0])  # Limit context length
                similarity = cosine_similarity(
                    answer_emb.reshape(1, -1),
                    context_emb.reshape(1, -1)
                )[0, 0]
                return float(similarity)
            except Exception as e:
                logger.warning(f"Embedding-based grounding failed: {str(e)}")
        
        # Fallback: Check phrase overlap
        answer_lower = answer.lower()
        context_lower = context_text.lower()
        
        # Extract meaningful phrases (3-4 words)
        answer_words = answer_lower.split()
        phrase_matches = 0
        total_phrases = 0
        
        for i in range(len(answer_words) - 2):
            phrase = ' '.join(answer_words[i:i+3])
            total_phrases += 1
            if phrase in context_lower:
                phrase_matches += 1
        
        if total_phrases == 0:
            return 0.5  # Neutral for very short answers
        
        grounding = phrase_matches / total_phrases
        
        # Adjust for answer length
        if len(answer) < self.min_answer_length:
            grounding *= 0.8  # Penalize very short answers
        
        return grounding
    
    def _calculate_quality(self, answer: str) -> float:
        """
        Calculate answer quality based on heuristics.
        
        Args:
            answer: Generated answer
            
        Returns:
            Quality score (0-1)
        """
        if not answer:
            return 0.0
        
        quality_score = 1.0
        
        # Length checks
        answer_length = len(answer.strip())
        if answer_length < self.min_answer_length:
            quality_score *= (answer_length / self.min_answer_length)
        elif answer_length > self.max_answer_length:
            quality_score *= 0.8  # Slight penalty for overly long answers
        
        # Check for common quality indicators
        answer_lower = answer.lower()
        
        # Positive indicators
        if any(indicator in answer_lower for indicator in ['because', 'therefore', 'specifically']):
            quality_score *= 1.1
        
        # Negative indicators
        if any(indicator in answer_lower for indicator in ['i don\'t know', 'not sure', 'maybe']):
            quality_score *= 0.7
        
        # Check for proper sentence structure
        sentences = answer.split('.')
        complete_sentences = sum(1 for s in sentences if len(s.strip()) > 10)
        if complete_sentences > 0:
            quality_score *= min(1.2, 1 + (complete_sentences * 0.1))
        
        # Check for repetition
        words = answer_lower.split()
        if len(words) > 10:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.5:  # Too much repetition
                quality_score *= 0.8
        
        # Ensure score is in valid range
        return float(np.clip(quality_score, 0.0, 1.0))