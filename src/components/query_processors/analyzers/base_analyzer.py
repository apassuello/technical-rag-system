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
    
    def _analyze_epic2_features(self, query: str, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze Epic 2 features for enhanced retrieval optimization.
        
        Args:
            query: Query string
            features: Basic features extracted from query
            
        Returns:
            Dictionary with Epic 2 feature recommendations
        """
        epic2_features = {}
        
        # Neural reranking optimization
        neural_reranking_score = self._calculate_neural_reranking_benefit(query, features)
        epic2_features['neural_reranking'] = {
            'enabled': neural_reranking_score > 0.5,
            'benefit_score': neural_reranking_score,
            'reason': self._get_neural_reranking_reason(neural_reranking_score, features)
        }
        
        # Graph enhancement optimization
        graph_enhancement_score = self._calculate_graph_enhancement_benefit(query, features)
        epic2_features['graph_enhancement'] = {
            'enabled': graph_enhancement_score > 0.4,
            'benefit_score': graph_enhancement_score,
            'reason': self._get_graph_enhancement_reason(graph_enhancement_score, features)
        }
        
        # Hybrid search weight optimization
        epic2_features['hybrid_weights'] = self._optimize_hybrid_weights(query, features)
        
        # Performance prediction
        epic2_features['performance_prediction'] = self._predict_performance_impact(query, features, epic2_features)
        
        return epic2_features
    
    def _calculate_neural_reranking_benefit(self, query: str, features: Dict[str, Any]) -> float:
        """
        Calculate potential benefit of neural reranking for this query.
        
        Args:
            query: Query string
            features: Basic features
            
        Returns:
            Benefit score (0.0 to 1.0)
        """
        benefit_score = 0.0
        
        # Complex queries benefit more from neural reranking
        complexity = features.get('complexity', 'medium')
        if complexity == 'complex':
            benefit_score += 0.4
        elif complexity == 'medium':
            benefit_score += 0.2
        
        # Technical queries benefit from semantic understanding
        if features.get('has_technical_indicators'):
            benefit_score += 0.3
        
        # Question-based queries benefit from semantic matching
        if features.get('has_question_words'):
            benefit_score += 0.2
        
        # Longer queries have more context for neural models
        if features.get('word_count', 0) > 10:
            benefit_score += 0.2
        
        # Comparison queries benefit from semantic similarity
        if any(word in query.lower() for word in ['compare', 'difference', 'vs', 'versus']):
            benefit_score += 0.3
        
        return min(1.0, benefit_score)
    
    def _calculate_graph_enhancement_benefit(self, query: str, features: Dict[str, Any]) -> float:
        """
        Calculate potential benefit of graph enhancement for this query.
        
        Args:
            query: Query string
            features: Basic features
            
        Returns:
            Benefit score (0.0 to 1.0)
        """
        benefit_score = 0.0
        
        # Queries with entities benefit from graph relationships
        query_lower = query.lower()
        entity_indicators = ['api', 'protocol', 'system', 'component', 'module', 'service', 'function']
        if any(indicator in query_lower for indicator in entity_indicators):
            benefit_score += 0.4
        
        # Relationship-based queries benefit from graph traversal
        relationship_words = ['related', 'connection', 'dependency', 'integrate', 'connect', 'link']
        if any(word in query_lower for word in relationship_words):
            benefit_score += 0.5
        
        # Architecture and design queries benefit from graph structure
        architecture_words = ['architecture', 'design', 'pattern', 'structure', 'flow', 'workflow']
        if any(word in query_lower for word in architecture_words):
            benefit_score += 0.3
        
        # Complex technical queries benefit from entity relationships
        if features.get('has_technical_indicators') and features.get('complexity') == 'complex':
            benefit_score += 0.2
        
        return min(1.0, benefit_score)
    
    def _get_neural_reranking_reason(self, score: float, features: Dict[str, Any]) -> str:
        """Get human-readable reason for neural reranking decision."""
        if score > 0.7:
            return "High semantic complexity benefits from neural understanding"
        elif score > 0.5:
            return "Moderate complexity with semantic benefits"
        elif score > 0.3:
            return "Some semantic benefit possible"
        else:
            return "Simple query, limited neural benefit"
    
    def _get_graph_enhancement_reason(self, score: float, features: Dict[str, Any]) -> str:
        """Get human-readable reason for graph enhancement decision."""
        if score > 0.6:
            return "Strong entity relationships detected"
        elif score > 0.4:
            return "Moderate entity/relationship patterns"
        elif score > 0.2:
            return "Some entity indicators present"
        else:
            return "Limited entity/relationship content"
    
    def _optimize_hybrid_weights(self, query: str, features: Dict[str, Any]) -> Dict[str, float]:
        """
        Optimize hybrid search weights based on query characteristics.
        
        Args:
            query: Query string
            features: Basic features
            
        Returns:
            Optimized weights for dense/sparse/graph components
        """
        # Default weights
        dense_weight = 0.6
        sparse_weight = 0.3
        graph_weight = 0.1
        
        # Adjust based on query characteristics
        if features.get('has_technical_indicators'):
            # Technical queries benefit from semantic similarity
            dense_weight += 0.1
            sparse_weight -= 0.05
            graph_weight -= 0.05
        
        if features.get('word_count', 0) < 5:
            # Short queries benefit from exact term matching
            sparse_weight += 0.1
            dense_weight -= 0.1
        
        # Normalize weights
        total_weight = dense_weight + sparse_weight + graph_weight
        return {
            'dense_weight': dense_weight / total_weight,
            'sparse_weight': sparse_weight / total_weight,
            'graph_weight': graph_weight / total_weight
        }
    
    def _predict_performance_impact(self, query: str, features: Dict[str, Any], epic2_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict performance impact of Epic 2 features for this query.
        
        Args:
            query: Query string
            features: Basic features
            epic2_features: Epic 2 feature analysis
            
        Returns:
            Performance prediction metrics
        """
        prediction = {
            'estimated_latency_ms': 500,  # Base latency
            'quality_improvement': 0.0,
            'resource_impact': 'low'
        }
        
        # Neural reranking impact
        if epic2_features.get('neural_reranking', {}).get('enabled'):
            prediction['estimated_latency_ms'] += 200
            prediction['quality_improvement'] += 0.15
            prediction['resource_impact'] = 'medium'
        
        # Graph enhancement impact
        if epic2_features.get('graph_enhancement', {}).get('enabled'):
            prediction['estimated_latency_ms'] += 100
            prediction['quality_improvement'] += 0.10
            if prediction['resource_impact'] == 'low':
                prediction['resource_impact'] = 'medium'
        
        # Complexity impact
        if features.get('complexity') == 'complex':
            prediction['estimated_latency_ms'] += 100
            prediction['quality_improvement'] += 0.05
        
        return prediction