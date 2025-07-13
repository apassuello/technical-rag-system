"""
Token-Limit Context Selector Implementation.

This module provides context selection focused on optimal token usage
and strict adherence to token limits with intelligent document packing.

Features:
- Strict token limit enforcement with safety margins
- Intelligent document packing algorithms
- Priority-based selection (relevance, length, quality)
- Comprehensive token usage tracking and optimization
"""

import logging
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


class TokenLimitSelector(BaseContextSelector):
    """
    Token-limit focused context selector.
    
    This selector prioritizes strict adherence to token limits while
    maximizing the quality and relevance of selected content. It uses
    intelligent packing algorithms to optimize token usage.
    
    Configuration Options:
    - packing_strategy: How to pack documents ("greedy", "optimal", "balanced")
    - min_relevance: Minimum relevance score to consider (default: 0.0) 
    - prefer_shorter: Prefer shorter documents for better packing (default: False)
    - quality_weight: Weight for document quality in selection (default: 0.3)
    - length_penalty: Penalty for very long documents (default: 0.1)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize token-limit selector with configuration.
        
        Args:
            config: Configuration dictionary
        """
        # Initialize attributes first before calling super().__init__
        config_dict = config or {}
        self._packing_strategy = config_dict.get('packing_strategy', 'greedy')
        self._min_relevance = config_dict.get('min_relevance', 0.0)
        self._prefer_shorter = config_dict.get('prefer_shorter', False)
        self._quality_weight = config_dict.get('quality_weight', 0.3)
        self._length_penalty = config_dict.get('length_penalty', 0.1)
        
        super().__init__(config)
        
        # Validate configuration
        if self._packing_strategy not in ['greedy', 'optimal', 'balanced']:
            logger.warning(f"Unknown packing_strategy {self._packing_strategy}, using 'greedy'")
            self._packing_strategy = 'greedy'
        
        logger.debug(f"Initialized TokenLimitSelector with strategy={self._packing_strategy}")
    
    def _select_documents(
        self,
        query: str,
        documents: List[Document], 
        max_tokens: int,
        query_analysis: Optional[QueryAnalysis] = None
    ) -> ContextSelection:
        """
        Select documents with strict token limit enforcement.
        
        Args:
            query: Clean, validated query string
            documents: Valid list of documents
            max_tokens: Positive token limit
            query_analysis: Optional query analysis
            
        Returns:
            ContextSelection with token-optimized documents and metadata
        """
        effective_max_tokens = self._get_effective_max_tokens(max_tokens)
        
        # Filter by minimum relevance if configured
        candidate_docs = self._filter_documents_by_score(documents, self._min_relevance)
        
        if not candidate_docs:
            return ContextSelection(
                selected_documents=[],
                total_tokens=0,
                selection_strategy="token_limit",
                metadata={'reason': 'no_documents_meet_min_relevance', 'min_relevance': self._min_relevance}
            )
        
        # Prepare documents with token counts and scores
        prepared_docs = self._prepare_documents_for_selection(candidate_docs, query_analysis)
        
        # Apply token-aware selection based on strategy
        if self._packing_strategy == 'optimal':
            selected_docs, selection_metadata = self._optimal_selection(prepared_docs, effective_max_tokens)
        elif self._packing_strategy == 'balanced':
            selected_docs, selection_metadata = self._balanced_selection(prepared_docs, effective_max_tokens)
        else:  # greedy
            selected_docs, selection_metadata = self._greedy_selection(prepared_docs, effective_max_tokens)
        
        # Calculate final metrics
        total_tokens = sum(doc_info['token_count'] for doc_info in selected_docs)
        actual_documents = [doc_info['document'] for doc_info in selected_docs]
        
        diversity_score = self._calculate_diversity_score(actual_documents)
        relevance_score = self._calculate_relevance_score(actual_documents)
        
        return ContextSelection(
            selected_documents=actual_documents,
            total_tokens=total_tokens,
            selection_strategy="token_limit",
            diversity_score=diversity_score,
            relevance_score=relevance_score,
            metadata={
                'packing_strategy': self._packing_strategy,
                'token_efficiency': total_tokens / effective_max_tokens if effective_max_tokens > 0 else 0.0,
                'candidates_considered': len(candidate_docs),
                'token_limit': effective_max_tokens,
                'safety_margin_used': self._safety_margin,
                **selection_metadata
            }
        )
    
    def _prepare_documents_for_selection(
        self, 
        documents: List[Document], 
        query_analysis: Optional[QueryAnalysis]
    ) -> List[Dict[str, Any]]:
        """
        Prepare documents with token counts and selection scores.
        
        Args:
            documents: Documents to prepare
            query_analysis: Optional query analysis
            
        Returns:
            List of document info dictionaries
        """
        prepared = []
        
        for doc in documents:
            token_count = self.estimate_tokens(doc.content)
            relevance_score = getattr(doc, 'score', 0.5)
            
            # Calculate quality score (can be extended based on document metadata)
            quality_score = self._calculate_document_quality(doc)
            
            # Calculate selection score combining relevance, quality, and length factors
            selection_score = self._calculate_selection_score(
                relevance_score, quality_score, token_count
            )
            
            doc_info = {
                'document': doc,
                'token_count': token_count,
                'relevance_score': relevance_score,
                'quality_score': quality_score,
                'selection_score': selection_score,
                'efficiency_ratio': relevance_score / max(1, token_count)  # Relevance per token
            }
            
            prepared.append(doc_info)
        
        return prepared
    
    def _calculate_document_quality(self, document: Document) -> float:
        """
        Calculate quality score for a document.
        
        Args:
            document: Document to score
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        quality = 0.5  # Base quality
        
        # Check for document metadata that indicates quality
        if hasattr(document, 'metadata') and document.metadata:
            metadata = document.metadata
            
            # Quality indicators from document processing
            if 'quality_score' in metadata:
                quality = max(quality, metadata['quality_score'])
            
            # Page information suggests structured content
            if 'page' in metadata and metadata['page'] is not None:
                quality += 0.1
            
            # Title information suggests well-structured content
            if 'title' in metadata and metadata['title']:
                quality += 0.1
            
            # Technical content may be higher quality for technical queries
            if 'parsing_method' in metadata and metadata['parsing_method'] == 'structure_preserving':
                quality += 0.1
        
        # Content-based quality indicators
        content = document.content
        if len(content) > 100:  # Minimum reasonable content length
            # Balanced paragraph structure
            sentences = content.count('.') + content.count('!') + content.count('?')
            if sentences > 2:
                quality += 0.1
            
            # Technical indicators
            if any(term in content.lower() for term in ['algorithm', 'implementation', 'configuration', 'protocol']):
                quality += 0.05
        
        return min(1.0, max(0.0, quality))
    
    def _calculate_selection_score(
        self, 
        relevance: float, 
        quality: float, 
        token_count: int
    ) -> float:
        """
        Calculate combined selection score for document ranking.
        
        Args:
            relevance: Relevance score (0.0-1.0)
            quality: Quality score (0.0-1.0)
            token_count: Number of tokens in document
            
        Returns:
            Combined selection score
        """
        # Base score from relevance and quality
        base_score = relevance + (self._quality_weight * quality)
        
        # Apply length penalty if configured
        if self._length_penalty > 0 and token_count > 500:  # Penalty for very long documents
            length_factor = 1.0 - (self._length_penalty * min(1.0, (token_count - 500) / 1000))
            base_score *= length_factor
        
        # Boost score for shorter documents if preferred
        if self._prefer_shorter and token_count < 200:
            base_score *= 1.1
        
        return base_score
    
    def _greedy_selection(
        self, 
        prepared_docs: List[Dict[str, Any]], 
        max_tokens: int
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Greedy document selection prioritizing highest scores.
        
        Args:
            prepared_docs: Documents with computed scores and token counts
            max_tokens: Maximum tokens allowed
            
        Returns:
            Tuple of (selected_documents, selection_metadata)
        """
        # Sort by selection score (highest first)
        sorted_docs = sorted(prepared_docs, key=lambda x: x['selection_score'], reverse=True)
        
        selected = []
        remaining_tokens = max_tokens
        
        for doc_info in sorted_docs:
            if doc_info['token_count'] <= remaining_tokens:
                selected.append(doc_info)
                remaining_tokens -= doc_info['token_count']
                
                # Stop if we've reached document limit
                if len(selected) >= self._max_documents:
                    break
        
        metadata = {
            'selection_method': 'greedy',
            'documents_considered': len(sorted_docs),
            'selection_stopped_reason': 'token_limit' if remaining_tokens > 0 else 'max_documents',
            'token_utilization': (max_tokens - remaining_tokens) / max_tokens if max_tokens > 0 else 0.0
        }
        
        return selected, metadata
    
    def _balanced_selection(
        self, 
        prepared_docs: List[Dict[str, Any]], 
        max_tokens: int
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Balanced selection considering both score and token efficiency.
        
        Args:
            prepared_docs: Documents with computed scores and token counts
            max_tokens: Maximum tokens allowed
            
        Returns:
            Tuple of (selected_documents, selection_metadata)
        """
        # Calculate combined score: selection_score + efficiency_ratio
        for doc_info in prepared_docs:
            doc_info['balanced_score'] = (
                doc_info['selection_score'] + 
                0.3 * doc_info['efficiency_ratio']  # Weight efficiency
            )
        
        # Sort by balanced score
        sorted_docs = sorted(prepared_docs, key=lambda x: x['balanced_score'], reverse=True)
        
        selected = []
        remaining_tokens = max_tokens
        
        for doc_info in sorted_docs:
            if doc_info['token_count'] <= remaining_tokens:
                selected.append(doc_info)
                remaining_tokens -= doc_info['token_count']
                
                if len(selected) >= self._max_documents:
                    break
        
        metadata = {
            'selection_method': 'balanced',
            'documents_considered': len(sorted_docs),
            'efficiency_weight': 0.3,
            'token_utilization': (max_tokens - remaining_tokens) / max_tokens if max_tokens > 0 else 0.0
        }
        
        return selected, metadata
    
    def _optimal_selection(
        self, 
        prepared_docs: List[Dict[str, Any]], 
        max_tokens: int
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Optimal selection using dynamic programming approach (simplified knapsack).
        
        Args:
            prepared_docs: Documents with computed scores and token counts
            max_tokens: Maximum tokens allowed
            
        Returns:
            Tuple of (selected_documents, selection_metadata)
        """
        # For performance, limit optimal selection to reasonable number of documents
        if len(prepared_docs) > 50:
            # Fall back to balanced selection for large sets
            logger.debug("Too many documents for optimal selection, using balanced approach")
            return self._balanced_selection(prepared_docs, max_tokens)
        
        # Simplified dynamic programming approach
        # This is a bounded knapsack variant
        
        n = len(prepared_docs)
        dp = [[0.0 for _ in range(max_tokens + 1)] for _ in range(n + 1)]
        
        # Fill the DP table
        for i in range(1, n + 1):
            doc_info = prepared_docs[i - 1]
            weight = doc_info['token_count']
            value = doc_info['selection_score']
            
            for w in range(max_tokens + 1):
                # Don't take the document
                dp[i][w] = dp[i - 1][w]
                
                # Take the document if it fits
                if weight <= w:
                    dp[i][w] = max(dp[i][w], dp[i - 1][w - weight] + value)
        
        # Backtrack to find selected documents
        selected = []
        w = max_tokens
        for i in range(n, 0, -1):
            if dp[i][w] != dp[i - 1][w]:
                selected.append(prepared_docs[i - 1])
                w -= prepared_docs[i - 1]['token_count']
        
        selected.reverse()  # Maintain original order preference
        
        metadata = {
            'selection_method': 'optimal',
            'documents_considered': n,
            'optimal_value': dp[n][max_tokens],
            'token_utilization': (max_tokens - w) / max_tokens if max_tokens > 0 else 0.0
        }
        
        return selected, metadata
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the token-limit selector with provided settings.
        
        Args:
            config: Configuration dictionary
        """
        super().configure(config)
        
        # Update token-limit specific configuration
        old_strategy = self._packing_strategy
        self._packing_strategy = config.get('packing_strategy', self._packing_strategy)
        if self._packing_strategy not in ['greedy', 'optimal', 'balanced']:
            logger.warning(f"Invalid packing_strategy {self._packing_strategy}, keeping {old_strategy}")
            self._packing_strategy = old_strategy
        
        self._min_relevance = config.get('min_relevance', self._min_relevance)
        self._prefer_shorter = config.get('prefer_shorter', self._prefer_shorter)
        self._quality_weight = config.get('quality_weight', self._quality_weight)
        self._length_penalty = config.get('length_penalty', self._length_penalty)