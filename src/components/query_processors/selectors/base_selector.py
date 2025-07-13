"""
Base Context Selector Implementation.

This module provides concrete base functionality for context selection
components, implementing common patterns for document filtering and token management.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from ..base import ContextSelector, ContextSelection, QueryAnalysis
from src.core.interfaces import Document

logger = logging.getLogger(__name__)


class BaseContextSelector(ContextSelector):
    """
    Base implementation providing common functionality for all context selectors.
    
    This class implements common patterns like token estimation, document
    filtering, and performance tracking that can be reused by concrete
    selector implementations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize base context selector with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self._config = config or {}
        self._performance_metrics = {
            'total_selections': 0,
            'average_time_ms': 0.0,
            'failed_selections': 0,
            'average_documents_selected': 0.0,
            'average_token_usage': 0.0
        }
        
        # Token estimation configuration
        self._words_per_token = self._config.get('words_per_token', 0.75)  # Rough approximation
        self._safety_margin = self._config.get('safety_margin', 0.9)      # Use 90% of max tokens
        self._min_documents = self._config.get('min_documents', 1)
        self._max_documents = self._config.get('max_documents', 20)
        
        # Configure based on provided settings
        self.configure(self._config)
        
        logger.debug(f"Initialized {self.__class__.__name__} with config: {self._config}")
    
    def select(
        self, 
        query: str,
        documents: List[Document], 
        max_tokens: int,
        query_analysis: Optional[QueryAnalysis] = None
    ) -> ContextSelection:
        """
        Select optimal context documents with performance tracking and error handling.
        
        Args:
            query: Original user query
            documents: Retrieved documents to select from
            max_tokens: Maximum token limit for selected context
            query_analysis: Optional query analysis for optimization
            
        Returns:
            ContextSelection with selected documents and metadata
            
        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If selection fails
        """
        # Validate inputs
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        if not documents:
            return ContextSelection(
                selected_documents=[],
                total_tokens=0,
                selection_strategy=self._get_strategy_name(),
                metadata={'reason': 'no_documents_provided'}
            )
        
        if max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        
        start_time = time.time()
        
        try:
            # Perform actual selection (implemented by subclasses)
            result = self._select_documents(query, documents, max_tokens, query_analysis)
            
            # Track performance
            selection_time = time.time() - start_time
            self._update_performance_metrics(selection_time, len(result.selected_documents), result.total_tokens, success=True)
            
            logger.debug(f"Context selection completed in {selection_time*1000:.1f}ms, selected {len(result.selected_documents)} documents")
            return result
            
        except Exception as e:
            selection_time = time.time() - start_time
            self._update_performance_metrics(selection_time, 0, 0, success=False)
            
            logger.error(f"Context selection failed after {selection_time*1000:.1f}ms: {e}")
            raise RuntimeError(f"Context selection failed: {e}") from e
    
    def _select_documents(
        self,
        query: str,
        documents: List[Document], 
        max_tokens: int,
        query_analysis: Optional[QueryAnalysis] = None
    ) -> ContextSelection:
        """
        Perform actual document selection (must be implemented by subclasses).
        
        Args:
            query: Clean, validated query string
            documents: Valid list of documents
            max_tokens: Positive token limit
            query_analysis: Optional query analysis
            
        Returns:
            ContextSelection with selected documents and metadata
        """
        raise NotImplementedError("Subclasses must implement _select_documents")
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text using configurable approximation.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        if not text:
            return 0
        
        # Simple word-based estimation (can be overridden by subclasses)
        word_count = len(text.split())
        estimated_tokens = int(word_count / self._words_per_token)
        
        # Add small buffer for safety
        return max(1, estimated_tokens)
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the selector with provided settings.
        
        Args:
            config: Configuration dictionary
        """
        self._config.update(config)
        
        # Apply common configuration
        self._words_per_token = config.get('words_per_token', self._words_per_token)
        self._safety_margin = config.get('safety_margin', self._safety_margin)
        self._min_documents = config.get('min_documents', self._min_documents)
        self._max_documents = config.get('max_documents', self._max_documents)
        
        if 'enable_metrics' in config:
            self._track_metrics = config['enable_metrics']
        else:
            self._track_metrics = True  # Default enable metrics
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for this selector.
        
        Returns:
            Dictionary with performance statistics
        """
        return self._performance_metrics.copy()
    
    def _get_strategy_name(self) -> str:
        """
        Get the name of this selection strategy.
        
        Returns:
            Strategy name string
        """
        return self.__class__.__name__.lower().replace('selector', '')
    
    def _update_performance_metrics(
        self, 
        selection_time: float, 
        documents_selected: int, 
        tokens_used: int,
        success: bool
    ) -> None:
        """
        Update internal performance metrics.
        
        Args:
            selection_time: Time taken for selection in seconds
            documents_selected: Number of documents selected
            tokens_used: Total tokens in selected documents
            success: Whether selection succeeded
        """
        if not self._track_metrics:
            return
        
        self._performance_metrics['total_selections'] += 1
        
        if success:
            # Update average time using incremental formula
            total_successful = self._performance_metrics['total_selections'] - self._performance_metrics['failed_selections']
            current_avg_time = self._performance_metrics['average_time_ms']
            self._performance_metrics['average_time_ms'] = (
                (current_avg_time * (total_successful - 1) + selection_time * 1000) / total_successful
            )
            
            # Update average documents selected
            current_avg_docs = self._performance_metrics['average_documents_selected']
            self._performance_metrics['average_documents_selected'] = (
                (current_avg_docs * (total_successful - 1) + documents_selected) / total_successful
            )
            
            # Update average token usage
            current_avg_tokens = self._performance_metrics['average_token_usage']
            self._performance_metrics['average_token_usage'] = (
                (current_avg_tokens * (total_successful - 1) + tokens_used) / total_successful
            )
        else:
            self._performance_metrics['failed_selections'] += 1
    
    def _filter_documents_by_score(
        self, 
        documents: List[Document], 
        min_score: float = 0.0
    ) -> List[Document]:
        """
        Filter documents by minimum relevance score.
        
        Args:
            documents: Documents to filter
            min_score: Minimum score threshold
            
        Returns:
            Filtered list of documents
        """
        if min_score <= 0.0:
            return documents
        
        filtered = []
        for doc in documents:
            # Check if document has a score (from retrieval)
            score = getattr(doc, 'score', 1.0)  # Default to 1.0 if no score
            if score >= min_score:
                filtered.append(doc)
        
        return filtered
    
    def _calculate_diversity_score(self, documents: List[Document]) -> float:
        """
        Calculate diversity score for a set of documents.
        
        This is a simple implementation that can be overridden by subclasses
        for more sophisticated diversity metrics.
        
        Args:
            documents: Documents to analyze
            
        Returns:
            Diversity score between 0.0 and 1.0
        """
        if len(documents) <= 1:
            return 0.0
        
        # Simple diversity based on content length variation
        lengths = [len(doc.content) for doc in documents]
        if not lengths:
            return 0.0
        
        avg_length = sum(lengths) / len(lengths)
        variance = sum((length - avg_length) ** 2 for length in lengths) / len(lengths)
        
        # Normalize variance to 0-1 range (rough approximation)
        diversity = min(1.0, variance / (avg_length ** 2 + 1))
        return diversity
    
    def _calculate_relevance_score(self, documents: List[Document]) -> float:
        """
        Calculate average relevance score for selected documents.
        
        Args:
            documents: Documents to analyze
            
        Returns:
            Average relevance score between 0.0 and 1.0
        """
        if not documents:
            return 0.0
        
        scores = []
        for doc in documents:
            score = getattr(doc, 'score', 0.5)  # Default to 0.5 if no score
            scores.append(score)
        
        return sum(scores) / len(scores)
    
    def _get_effective_max_tokens(self, max_tokens: int) -> int:
        """
        Calculate effective maximum tokens with safety margin.
        
        Args:
            max_tokens: Original maximum tokens
            
        Returns:
            Effective maximum tokens with safety margin applied
        """
        return int(max_tokens * self._safety_margin)
    
    def _sort_documents_by_score(self, documents: List[Document], descending: bool = True) -> List[Document]:
        """
        Sort documents by their relevance scores.
        
        Args:
            documents: Documents to sort
            descending: Sort in descending order (highest scores first)
            
        Returns:
            Sorted list of documents
        """
        return sorted(
            documents,
            key=lambda doc: getattr(doc, 'score', 0.0),
            reverse=descending
        )