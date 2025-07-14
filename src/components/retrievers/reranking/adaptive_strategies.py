"""
Adaptive Strategies for Neural Reranking.

This module provides query-type aware reranking strategies that can
adapt model selection and parameters based on query characteristics
to optimize relevance and performance.
"""

import logging
import re
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .config.reranking_config import AdaptiveConfig

logger = logging.getLogger(__name__)


@dataclass
class QueryAnalysis:
    """Results of query analysis."""
    query_type: str
    confidence: float
    features: Dict[str, Any]
    recommended_model: str


class QueryTypeDetector:
    """
    Detects query types to enable adaptive reranking strategies.
    
    Analyzes queries to classify them into categories like technical,
    procedural, comparative, etc. to enable optimal model selection.
    """
    
    def __init__(self, config):
        """
        Initialize query type detector.
        
        Args:
            config: Query classification configuration
        """
        self.config = config
        self.stats = {
            "classifications": 0,
            "type_counts": {},
            "high_confidence": 0,
            "low_confidence": 0
        }
        
        # Define patterns for different query types
        self.patterns = {
            "technical": [
                r'\b(api|protocol|implementation|configuration|architecture)\b',
                r'\b(install|setup|configure|deploy)\b',
                r'\b(error|exception|debug|troubleshoot)\b',
                r'\b(version|compatibility|requirement)\b'
            ],
            "procedural": [
                r'\bhow to\b',
                r'\bstep by step\b',
                r'\bguide|tutorial|walkthrough\b',
                r'\bprocess|procedure|workflow\b'
            ],
            "comparative": [
                r'\bvs\b|\bversus\b',
                r'\bdifference between\b',
                r'\bcompare|comparison\b',
                r'\bbetter|best|worse|worst\b'
            ],
            "factual": [
                r'\bwhat is\b|\bwho is\b|\bwhere is\b',
                r'\bdefine|definition\b',
                r'\bexplain|describe\b'
            ],
            "general": []  # Catch-all for queries that don't match other patterns
        }
        
        logger.info("QueryTypeDetector initialized with built-in patterns")
    
    def classify_query(self, query: str) -> QueryAnalysis:
        """
        Classify a query into a type category.
        
        Args:
            query: The search query to classify
            
        Returns:
            Query analysis with type, confidence, and features
        """
        query_lower = query.lower()
        type_scores = {}
        
        # Calculate scores for each query type
        for query_type, patterns in self.patterns.items():
            if not patterns:  # Skip empty pattern lists (like general)
                continue
                
            score = 0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    matches += 1
                    score += 1
            
            # Normalize score by number of patterns
            if patterns:
                type_scores[query_type] = score / len(patterns)
        
        # Find the best matching type
        if type_scores:
            best_type = max(type_scores.keys(), key=lambda k: type_scores[k])
            confidence = type_scores[best_type]
        else:
            best_type = "general"
            confidence = 0.5  # Default confidence for general queries
        
        # Apply confidence threshold
        if confidence < self.config.confidence_threshold:
            best_type = "general"
            confidence = 0.5
        
        # Extract additional features
        features = self._extract_features(query)
        
        # Get recommended model
        recommended_model = self.config.strategies.get(best_type, "default_model")
        
        # Update statistics
        self._update_stats(best_type, confidence)
        
        return QueryAnalysis(
            query_type=best_type,
            confidence=confidence,
            features=features,
            recommended_model=recommended_model
        )
    
    def _extract_features(self, query: str) -> Dict[str, Any]:
        """Extract additional features from the query."""
        features = {
            "length": len(query),
            "word_count": len(query.split()),
            "has_question_mark": "?" in query,
            "has_quotes": '"' in query or "'" in query,
            "is_uppercase": query.isupper(),
            "starts_with_question_word": query.lower().startswith(('what', 'how', 'when', 'where', 'why', 'who')),
            "technical_terms": len([w for w in query.lower().split() if w in ['api', 'protocol', 'config', 'setup']])
        }
        
        return features
    
    def _update_stats(self, query_type: str, confidence: float):
        """Update classification statistics."""
        self.stats["classifications"] += 1
        self.stats["type_counts"][query_type] = self.stats["type_counts"].get(query_type, 0) + 1
        
        if confidence >= 0.8:
            self.stats["high_confidence"] += 1
        elif confidence < 0.5:
            self.stats["low_confidence"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get classification statistics."""
        return self.stats.copy()


class AdaptiveStrategies:
    """
    Adaptive reranking strategies that adjust based on query characteristics.
    
    This component analyzes queries and selects optimal models and parameters
    to maximize relevance while maintaining performance targets.
    """
    
    def __init__(self, config: AdaptiveConfig):
        """
        Initialize adaptive strategies.
        
        Args:
            config: Adaptive configuration
        """
        self.config = config
        self.detector = QueryTypeDetector(config.query_classification) if config.enabled else None
        
        self.stats = {
            "model_selections": 0,
            "adaptations": 0,
            "fallbacks": 0
        }
        
        # Performance tracking for adaptive adjustments
        self.performance_history = []
        
        logger.info(f"AdaptiveStrategies initialized, enabled={config.enabled}")
    
    def select_model(
        self, 
        query: str, 
        available_models: List[str], 
        default_model: str
    ) -> str:
        """
        Select the optimal model for a given query.
        
        Args:
            query: The search query
            available_models: List of available model names
            default_model: Default model to fall back to
            
        Returns:
            Name of the selected model
        """
        if not self.config.enabled or not self.detector:
            return default_model
        
        try:
            # Classify the query
            analysis = self.detector.classify_query(query)
            
            # Get recommended model
            recommended_model = analysis.recommended_model
            
            # Check if recommended model is available
            if recommended_model in available_models:
                selected_model = recommended_model
            else:
                logger.warning(f"Recommended model {recommended_model} not available, using default")
                selected_model = default_model
                self.stats["fallbacks"] += 1
            
            # Consider performance-based adaptations
            if self.config.model_selection.enable_dynamic_switching:
                selected_model = self._consider_performance_adaptation(
                    selected_model, available_models, default_model
                )
            
            self.stats["model_selections"] += 1
            
            logger.debug(f"Selected model '{selected_model}' for query type '{analysis.query_type}' "
                        f"(confidence: {analysis.confidence:.2f})")
            
            return selected_model
            
        except Exception as e:
            logger.error(f"Model selection failed: {e}")
            self.stats["fallbacks"] += 1
            return default_model
    
    def _consider_performance_adaptation(
        self, 
        current_selection: str, 
        available_models: List[str], 
        default_model: str
    ) -> str:
        """Consider performance-based model adaptation."""
        try:
            # Check recent performance history
            if len(self.performance_history) >= self.config.model_selection.performance_window:
                recent_performance = self.performance_history[-self.config.model_selection.performance_window:]
                
                # Calculate average quality for current selection
                current_model_performance = [
                    p for p in recent_performance 
                    if p.get("model") == current_selection
                ]
                
                if current_model_performance:
                    avg_quality = sum(p.get("quality", 0) for p in current_model_performance) / len(current_model_performance)
                    
                    # Switch if quality is below threshold
                    if avg_quality < self.config.model_selection.quality_threshold:
                        logger.info(f"Switching from {current_selection} due to low quality: {avg_quality:.2f}")
                        self.stats["adaptations"] += 1
                        return self.config.model_selection.fallback_model
            
            return current_selection
            
        except Exception as e:
            logger.warning(f"Performance adaptation failed: {e}")
            return current_selection
    
    def adapt_parameters(
        self, 
        query: str, 
        model_name: str, 
        base_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Adapt model parameters based on query characteristics.
        
        Args:
            query: The search query
            model_name: Selected model name
            base_config: Base model configuration
            
        Returns:
            Adapted configuration
        """
        if not self.config.enabled:
            return base_config
        
        try:
            adapted_config = base_config.copy()
            
            # Adapt batch size based on query complexity
            if self.config.performance_adaptation.adaptive_batch_size:
                query_complexity = self._assess_query_complexity(query)
                
                if query_complexity == "high":
                    adapted_config["batch_size"] = max(1, adapted_config.get("batch_size", 16) // 2)
                elif query_complexity == "low":
                    adapted_config["batch_size"] = min(64, adapted_config.get("batch_size", 16) * 2)
            
            # Adapt number of candidates based on query type
            if self.config.performance_adaptation.adaptive_candidates:
                analysis = self.detector.classify_query(query) if self.detector else None
                
                if analysis and analysis.query_type == "technical":
                    # Technical queries might benefit from more candidates
                    adapted_config["max_candidates"] = min(100, adapted_config.get("max_candidates", 50) * 1.5)
                elif analysis and analysis.query_type == "factual":
                    # Factual queries might need fewer candidates
                    adapted_config["max_candidates"] = max(10, adapted_config.get("max_candidates", 50) // 2)
            
            return adapted_config
            
        except Exception as e:
            logger.error(f"Parameter adaptation failed: {e}")
            return base_config
    
    def _assess_query_complexity(self, query: str) -> str:
        """Assess query complexity for parameter adaptation."""
        word_count = len(query.split())
        
        if word_count > 10:
            return "high"
        elif word_count < 3:
            return "low"
        else:
            return "medium"
    
    def record_performance(
        self, 
        model: str, 
        query_type: str, 
        latency_ms: float, 
        quality_score: float
    ):
        """
        Record performance metrics for adaptive learning.
        
        Args:
            model: Model used
            query_type: Type of query
            latency_ms: Processing latency
            quality_score: Quality metric (0-1)
        """
        performance_record = {
            "model": model,
            "query_type": query_type,
            "latency_ms": latency_ms,
            "quality": quality_score,
            "timestamp": time.time()
        }
        
        self.performance_history.append(performance_record)
        
        # Keep only recent history
        max_history = self.config.model_selection.performance_window * 2
        if len(self.performance_history) > max_history:
            self.performance_history = self.performance_history[-max_history:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get adaptive strategies statistics."""
        stats = self.stats.copy()
        
        if self.detector:
            stats["detector"] = self.detector.get_stats()
        
        # Add performance summary
        if self.performance_history:
            recent_performance = self.performance_history[-50:]  # Last 50 records
            stats["recent_performance"] = {
                "avg_latency_ms": sum(p["latency_ms"] for p in recent_performance) / len(recent_performance),
                "avg_quality": sum(p["quality"] for p in recent_performance) / len(recent_performance),
                "total_records": len(self.performance_history)
            }
        
        return stats
    
    def reset_stats(self) -> None:
        """Reset adaptive strategies statistics."""
        self.stats = {
            "model_selections": 0,
            "adaptations": 0,
            "fallbacks": 0
        }
        
        if self.detector:
            self.detector.stats = {
                "classifications": 0,
                "type_counts": {},
                "high_confidence": 0,
                "low_confidence": 0
            }