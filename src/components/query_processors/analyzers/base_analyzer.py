"""
Base Query Analyzer Implementation.

This module provides concrete base functionality that can be inherited
by specific analyzer implementations, reducing code duplication.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from ..base import QueryAnalyzer, QueryAnalysis

logger = logging.getLogger(__name__)


class BaseQueryAnalyzer(QueryAnalyzer):
    """
    Base implementation providing common functionality for all analyzers.
    
    This class implements common patterns like configuration management,
    basic validation, and performance tracking that can be reused by
    concrete analyzer implementations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize base analyzer with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self._config = config or {}
        self._performance_metrics = {
            'total_analyses': 0,
            'average_time_ms': 0.0,
            'failed_analyses': 0
        }
        
        # Configure based on provided settings
        self.configure(self._config)
        
        logger.debug(f"Initialized {self.__class__.__name__} with config: {self._config}")
    
    def analyze(self, query: str) -> QueryAnalysis:
        """
        Analyze query with performance tracking and error handling.
        
        Args:
            query: User query string
            
        Returns:
            QueryAnalysis with extracted characteristics
            
        Raises:
            ValueError: If query is empty or invalid
            RuntimeError: If analysis fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        start_time = time.time()
        
        try:
            # Perform actual analysis (implemented by subclasses)
            result = self._analyze_query(query)
            
            # Track performance
            analysis_time = time.time() - start_time
            self._update_performance_metrics(analysis_time, success=True)
            
            logger.debug(f"Query analysis completed in {analysis_time*1000:.1f}ms")
            return result
            
        except Exception as e:
            analysis_time = time.time() - start_time
            self._update_performance_metrics(analysis_time, success=False)
            
            logger.error(f"Query analysis failed after {analysis_time*1000:.1f}ms: {e}")
            raise RuntimeError(f"Query analysis failed: {e}") from e
    
    def _analyze_query(self, query: str) -> QueryAnalysis:
        """
        Perform actual query analysis (must be implemented by subclasses).
        
        Args:
            query: Clean, validated query string
            
        Returns:
            QueryAnalysis with extracted characteristics
        """
        raise NotImplementedError("Subclasses must implement _analyze_query")
    
    def get_supported_features(self) -> List[str]:
        """
        Return base features supported by all analyzers.
        
        Subclasses should override and extend this list.
        
        Returns:
            List of feature names
        """
        return ["basic_analysis"]
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the analyzer with provided settings.
        
        Args:
            config: Configuration dictionary
        """
        self._config.update(config)
        
        # Apply common configuration
        if 'timeout_seconds' in config:
            self._timeout = config['timeout_seconds']
        else:
            self._timeout = 5.0  # Default timeout
        
        if 'enable_metrics' in config:
            self._track_metrics = config['enable_metrics']
        else:
            self._track_metrics = True  # Default enable metrics
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for this analyzer.
        
        Returns:
            Dictionary with performance statistics
        """
        return self._performance_metrics.copy()
    
    def _update_performance_metrics(self, analysis_time: float, success: bool) -> None:
        """
        Update internal performance metrics.
        
        Args:
            analysis_time: Time taken for analysis in seconds
            success: Whether analysis succeeded
        """
        if not self._track_metrics:
            return
        
        self._performance_metrics['total_analyses'] += 1
        
        if success:
            # Update average time using incremental formula
            total = self._performance_metrics['total_analyses'] - self._performance_metrics['failed_analyses']
            current_avg = self._performance_metrics['average_time_ms']
            self._performance_metrics['average_time_ms'] = (
                (current_avg * (total - 1) + analysis_time * 1000) / total
            )
        else:
            self._performance_metrics['failed_analyses'] += 1
    
    def _extract_basic_features(self, query: str) -> Dict[str, Any]:
        """
        Extract basic features that all analyzers can provide.
        
        Args:
            query: Query string to analyze
            
        Returns:
            Dictionary with basic features
        """
        features = {}
        
        # Basic text statistics
        features['length'] = len(query)
        features['word_count'] = len(query.split())
        features['sentence_count'] = query.count('.') + query.count('?') + query.count('!')
        
        # Simple pattern detection
        features['has_question_words'] = any(
            word in query.lower() 
            for word in ['what', 'how', 'why', 'when', 'where', 'who', 'which']
        )
        
        features['has_technical_indicators'] = any(
            indicator in query.lower()
            for indicator in ['implement', 'configure', 'api', 'protocol', 'algorithm']
        )
        
        # Complexity estimation
        if features['word_count'] < 5:
            features['complexity'] = 'simple'
        elif features['word_count'] < 15:
            features['complexity'] = 'medium'
        else:
            features['complexity'] = 'complex'
        
        return features
    
    def _determine_intent_category(self, query: str, features: Dict[str, Any]) -> str:
        """
        Determine basic intent category from query and features.
        
        Args:
            query: Query string
            features: Extracted features
            
        Returns:
            Intent category string
        """
        query_lower = query.lower()
        
        # Technical documentation patterns
        if any(word in query_lower for word in ['what is', 'define', 'explain']):
            return 'definition'
        
        if any(word in query_lower for word in ['how to', 'how do', 'implement']):
            return 'procedural'
        
        if any(word in query_lower for word in ['compare', 'difference', 'vs', 'versus']):
            return 'comparison'
        
        if any(word in query_lower for word in ['example', 'sample', 'demo']):
            return 'example'
        
        if features.get('has_technical_indicators'):
            return 'technical'
        
        return 'general'
    
    def _suggest_retrieval_k(self, query: str, features: Dict[str, Any]) -> int:
        """
        Suggest optimal number of documents to retrieve based on query analysis.
        
        Args:
            query: Query string
            features: Extracted features
            
        Returns:
            Suggested k value for retrieval
        """
        # Base k on complexity and intent
        base_k = self._config.get('default_k', 5)
        
        complexity = features.get('complexity', 'medium')
        intent = features.get('intent_category', 'general')
        
        # Adjust based on complexity
        if complexity == 'simple':
            k = max(3, base_k - 2)
        elif complexity == 'complex':
            k = min(10, base_k + 3)
        else:
            k = base_k
        
        # Adjust based on intent
        if intent in ['comparison', 'example']:
            k = min(12, k + 2)  # Need more examples for comparisons
        elif intent == 'definition':
            k = max(2, k - 1)   # Definitions usually need fewer sources
        
        return k