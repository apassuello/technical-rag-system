"""
Epic 1 Query Analyzer - Multi-Model Routing Orchestrator.

This module implements the main Epic1QueryAnalyzer that orchestrates
feature extraction, complexity classification, and model recommendation
for intelligent multi-model routing in the RAG system.

Architecture Notes:
- Modular sub-component orchestration
- Direct implementation pattern
- Configuration-driven behavior
- Compatible with existing QueryProcessor infrastructure
"""

import time
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from .base_analyzer import BaseQueryAnalyzer
from ..base import QueryAnalysis
from .components import (
    FeatureExtractor,
    ComplexityClassifier,
    ModelRecommender
)

logger = logging.getLogger(__name__)


class Epic1QueryAnalyzer(BaseQueryAnalyzer):
    """
    Epic 1 query analyzer with modular sub-components for multi-model routing.
    
    This analyzer orchestrates the complete Epic 1 query analysis workflow:
    1. Feature extraction - Extract linguistic and structural features
    2. Complexity classification - Classify as simple/medium/complex
    3. Model recommendation - Recommend optimal model based on strategy
    
    The analyzer integrates seamlessly with the existing QueryProcessor
    infrastructure, providing enhanced metadata for intelligent routing.
    
    Architecture:
    - Follows modular pattern like ModularDocumentProcessor
    - Direct implementation (no external adapters needed)
    - Configuration-driven thresholds and mappings
    - Performance optimized for <50ms overhead
    
    Configuration:
    - feature_extractor: Configuration for feature extraction
    - complexity_classifier: Weights and thresholds for classification
    - model_recommender: Strategy and model mappings for routing
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Epic 1 query analyzer with sub-components.
        
        Args:
            config: Configuration dictionary with sub-component configs
        """
        super().__init__(config)
        
        # Initialize sub-components with their configurations
        self.feature_extractor = FeatureExtractor(
            self._config.get('feature_extractor', {})
        )
        
        self.complexity_classifier = ComplexityClassifier(
            self._config.get('complexity_classifier', {})
        )
        
        self.model_recommender = ModelRecommender(
            self._config.get('model_recommender', {})
        )
        
        # Performance tracking
        self._analysis_times = {
            'feature_extraction': [],
            'complexity_classification': [],
            'model_recommendation': [],
            'total': []
        }
        
        logger.info(
            f"Initialized Epic1QueryAnalyzer with strategy: "
            f"{self.model_recommender.strategy.value}"
        )
    
    def _analyze_query(self, query: str) -> QueryAnalysis:
        """
        Perform Epic 1 query analysis workflow.
        
        This method orchestrates the complete analysis pipeline:
        1. Extract linguistic features
        2. Classify complexity level
        3. Recommend optimal model
        4. Build comprehensive QueryAnalysis
        
        Args:
            query: Clean, validated query string
            
        Returns:
            QueryAnalysis with Epic 1 metadata for routing
        """
        start_time = time.time()
        phase_times = {}
        
        try:
            # Phase 1: Feature Extraction
            phase_start = time.time()
            features = self.feature_extractor.extract(query)
            phase_times['feature_extraction'] = time.time() - phase_start
            
            logger.debug(
                f"Extracted {len(features)} feature categories in "
                f"{phase_times['feature_extraction']*1000:.1f}ms"
            )
            
            # Phase 2: Complexity Classification
            phase_start = time.time()
            classification = self.complexity_classifier.classify(features)
            phase_times['complexity_classification'] = time.time() - phase_start
            
            logger.debug(
                f"Classified as {classification.level} (score: {classification.score:.2f}, "
                f"confidence: {classification.confidence:.2f}) in "
                f"{phase_times['complexity_classification']*1000:.1f}ms"
            )
            
            # Phase 3: Model Recommendation
            phase_start = time.time()
            
            # Convert classification to dict for recommender
            classification_dict = {
                'level': classification.level,
                'score': classification.score,
                'confidence': classification.confidence,
                'breakdown': classification.breakdown
            }
            
            recommendation = self.model_recommender.recommend(
                classification_dict,
                features
            )
            phase_times['model_recommendation'] = time.time() - phase_start
            
            logger.debug(
                f"Recommended {recommendation.model} in "
                f"{phase_times['model_recommendation']*1000:.1f}ms"
            )
            
            # Calculate total time
            total_time = time.time() - start_time
            phase_times['total'] = total_time
            
            # Update performance metrics
            self._update_analysis_times(phase_times)
            
            # Log if exceeding target latency
            if total_time > 0.050:  # 50ms target
                logger.warning(
                    f"Epic1 analysis exceeded 50ms target: {total_time*1000:.1f}ms"
                )
            
            # Build QueryAnalysis with Epic 1 metadata
            return self._build_query_analysis(
                query,
                features,
                classification,
                recommendation,
                phase_times
            )
            
        except Exception as e:
            logger.error(f"Epic1 query analysis failed: {e}")
            # Return basic analysis on failure
            return self._build_fallback_analysis(query, str(e))
    
    def _build_query_analysis(
        self,
        query: str,
        features: Dict[str, Any],
        classification: Any,  # ComplexityClassification
        recommendation: Any,  # ModelRecommendation
        phase_times: Dict[str, float]
    ) -> QueryAnalysis:
        """
        Build comprehensive QueryAnalysis with Epic 1 metadata.
        
        Args:
            query: Original query
            features: Extracted features
            classification: Complexity classification result
            recommendation: Model recommendation result
            phase_times: Performance timing data
            
        Returns:
            QueryAnalysis with Epic 1 routing metadata
        """
        # Extract key features for base QueryAnalysis
        vocabulary_features = features.get('vocabulary_features', {})
        question_features = features.get('question_features', {})
        
        # Determine intent category from question type
        question_type = question_features.get('question_type', 'unknown')
        intent_category = self._map_question_type_to_intent(question_type)
        
        # Suggest retrieval k based on complexity
        suggested_k = self._suggest_retrieval_k(classification.level)
        
        # Build Epic 1 metadata
        epic1_metadata = {
            'complexity_level': classification.level,
            'complexity_score': classification.score,
            'complexity_confidence': classification.confidence,
            'complexity_breakdown': classification.breakdown,
            'recommended_model': recommendation.model,
            'model_provider': recommendation.provider,
            'model_name': recommendation.model_name,
            'routing_confidence': recommendation.confidence,
            'cost_estimate': recommendation.cost_estimate,
            'latency_estimate': recommendation.latency_estimate,
            'fallback_chain': recommendation.fallback_chain,
            'routing_strategy': self.model_recommender.strategy.value,
            'feature_summary': self.feature_extractor.get_summary(features),
            'classification_reasoning': classification.reasoning,
            'recommendation_reasoning': recommendation.reasoning,
            'analysis_time_ms': phase_times['total'] * 1000,
            'phase_times_ms': {
                k: v * 1000 for k, v in phase_times.items()
            }
        }
        
        # Create QueryAnalysis
        return QueryAnalysis(
            query=query,
            complexity_score=classification.score,
            complexity_level=classification.level,
            technical_terms=vocabulary_features.get('technical_terms', []),
            entities=features.get('entity_features', {}).get('entities', []),
            intent_category=intent_category,
            suggested_k=suggested_k,
            confidence=classification.confidence,
            metadata={'epic1_analysis': epic1_metadata}
        )
    
    def _build_fallback_analysis(self, query: str, error: str) -> QueryAnalysis:
        """
        Build fallback QueryAnalysis when analysis fails.
        
        Args:
            query: Original query
            error: Error message
            
        Returns:
            Basic QueryAnalysis with error metadata
        """
        logger.warning(f"Using fallback analysis due to error: {error}")
        
        return QueryAnalysis(
            query=query,
            complexity_score=0.5,  # Default to medium
            complexity_level="medium",  # Default to medium
            technical_terms=[],
            entities=[],
            intent_category='general',
            suggested_k=5,
            confidence=0.3,  # Low confidence due to error
            metadata={
                'epic1_analysis': {
                    'error': error,
                    'complexity_level': 'medium',  # Safe default
                    'recommended_model': 'mistral:mistral-small',  # Default model
                    'routing_confidence': 0.3,
                    'fallback': True
                }
            }
        )
    
    def _map_question_type_to_intent(self, question_type: str) -> str:
        """
        Map question type to intent category.
        
        Args:
            question_type: Question type from feature extraction
            
        Returns:
            Intent category string
        """
        intent_map = {
            'what': 'definition',
            'how': 'explanation',
            'why': 'reasoning',
            'when': 'temporal',
            'where': 'location',
            'who': 'entity',
            'which': 'selection',
            'compare': 'comparison',
            'explain': 'explanation',
            'list': 'enumeration',
            'other_question': 'general_question',
            'statement': 'statement'
        }
        
        return intent_map.get(question_type, 'general')
    
    def _suggest_retrieval_k(self, complexity_level: str) -> int:
        """
        Suggest retrieval k based on complexity level.
        
        More complex queries may benefit from more context.
        
        Args:
            complexity_level: simple/medium/complex
            
        Returns:
            Suggested k value
        """
        k_map = {
            'simple': 3,   # Fewer documents for simple queries
            'medium': 5,   # Standard retrieval
            'complex': 7   # More context for complex queries
        }
        
        return k_map.get(complexity_level, 5)
    
    def _update_analysis_times(self, phase_times: Dict[str, float]) -> None:
        """
        Update performance tracking metrics.
        
        Args:
            phase_times: Dictionary of phase timings
        """
        for phase, time_val in phase_times.items():
            if phase in self._analysis_times:
                # Keep last 100 measurements
                self._analysis_times[phase].append(time_val)
                if len(self._analysis_times[phase]) > 100:
                    self._analysis_times[phase].pop(0)
    
    def get_supported_features(self) -> List[str]:
        """
        Get list of supported analysis features.
        
        Returns:
            List of feature names
        """
        return [
            'epic1_complexity_classification',
            'multi_model_routing',
            'feature_extraction',
            'cost_estimation',
            'latency_estimation',
            'fallback_chains',
            'routing_strategies',
            'technical_term_analysis',
            'syntactic_analysis',
            'question_classification'
        ]
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Update analyzer configuration.
        
        Args:
            config: New configuration dictionary
        """
        super().configure(config)
        
        # Update sub-component configurations
        if 'feature_extractor' in config:
            self.feature_extractor = FeatureExtractor(config['feature_extractor'])
        
        if 'complexity_classifier' in config:
            self.complexity_classifier = ComplexityClassifier(config['complexity_classifier'])
        
        if 'model_recommender' in config:
            self.model_recommender = ModelRecommender(config['model_recommender'])
        
        logger.info("Epic1QueryAnalyzer configuration updated")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the analyzer.
        
        Returns:
            Dictionary of performance statistics
        """
        metrics = super().get_performance_metrics()
        
        # Add Epic 1 specific metrics
        epic1_metrics = {}
        
        for phase, times in self._analysis_times.items():
            if times:
                avg_time = sum(times) / len(times)
                epic1_metrics[f'avg_{phase}_ms'] = avg_time * 1000
                epic1_metrics[f'max_{phase}_ms'] = max(times) * 1000
                epic1_metrics[f'min_{phase}_ms'] = min(times) * 1000
        
        # Check if meeting <50ms target
        if 'avg_total_ms' in epic1_metrics:
            epic1_metrics['meets_latency_target'] = epic1_metrics['avg_total_ms'] < 50
        
        metrics['epic1_performance'] = epic1_metrics
        
        return metrics
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the analyzer.
        
        Returns:
            Dictionary of analyzer statistics
        """
        return {
            'feature_extractor': self.feature_extractor.get_summary({}),
            'complexity_classifier': self.complexity_classifier.get_statistics(),
            'model_recommender': self.model_recommender.get_statistics(),
            'performance_metrics': self.get_performance_metrics(),
            'supported_features': self.get_supported_features()
        }