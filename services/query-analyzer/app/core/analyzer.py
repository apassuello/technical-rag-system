"""
Query Analyzer Service - Core Business Logic.

This module implements the QueryAnalyzerService that wraps the existing
Epic1QueryAnalyzer for use in the microservices architecture.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import sys

import structlog
from prometheus_client import Counter, Histogram, Gauge

# Add main project to path to import existing components
# From query-analyzer service to project root: ../../
project_root = Path(__file__).parent.parent.parent.parent.parent  # 5 levels up to project root
if project_root.exists():
    sys.path.insert(0, str(project_root))

# Import existing Epic 1 components
from src.components.query_processors.analyzers.epic1_query_analyzer import Epic1QueryAnalyzer
from src.components.query_processors.base import QueryAnalysis

logger = structlog.get_logger(__name__)

# Metrics
ANALYSIS_REQUESTS = Counter('analyzer_requests_total', 'Total analysis requests', ['status'])
ANALYSIS_DURATION = Histogram('analyzer_duration_seconds', 'Analysis duration', ['complexity'])
COMPLEXITY_DISTRIBUTION = Counter('analyzer_complexity_total', 'Queries by complexity', ['complexity'])
COMPONENT_HEALTH = Gauge('analyzer_component_health', 'Component health status', ['component'])


class QueryAnalyzerService:
    """
    Service wrapper for Epic1QueryAnalyzer.
    
    This service provides:
    - Async/await interface for the analyzer
    - Metrics collection and health monitoring
    - Error handling and logging
    - Performance tracking
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Query Analyzer Service.
        
        Args:
            config: Configuration dictionary for the analyzer
        """
        self.config = config or {}
        self.analyzer: Optional[Epic1QueryAnalyzer] = None
        self._initialized = False
        self._initialization_lock = asyncio.Lock()
        
        logger.info("Initializing QueryAnalyzerService", config=self.config)
    
    async def _initialize_analyzer(self):
        """Initialize the Epic1QueryAnalyzer if not already done."""
        if self._initialized:
            return
        
        async with self._initialization_lock:
            if self._initialized:
                return
            
            try:
                # Initialize the Epic1QueryAnalyzer with configuration
                self.analyzer = Epic1QueryAnalyzer(config=self.config)
                self._initialized = True
                
                # Update component health metrics
                COMPONENT_HEALTH.labels(component="feature_extractor").set(1)
                COMPONENT_HEALTH.labels(component="complexity_classifier").set(1)
                COMPONENT_HEALTH.labels(component="model_recommender").set(1)
                
                logger.info("Epic1QueryAnalyzer initialized successfully")
                
            except Exception as e:
                logger.error("Failed to initialize Epic1QueryAnalyzer", error=str(e))
                # Update component health metrics
                COMPONENT_HEALTH.labels(component="feature_extractor").set(0)
                COMPONENT_HEALTH.labels(component="complexity_classifier").set(0)
                COMPONENT_HEALTH.labels(component="model_recommender").set(0)
                raise
    
    async def analyze_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze a query and return complexity analysis results.
        
        Args:
            query: The query string to analyze
            context: Optional context information
            
        Returns:
            Dictionary containing analysis results including:
            - complexity: Complexity level (simple/medium/complex)
            - confidence: Confidence score for the classification
            - features: Extracted features
            - recommended_models: List of recommended models
            - cost_estimate: Estimated cost per model
            - metadata: Additional metadata
        """
        if not self._initialized:
            await self._initialize_analyzer()
        
        if not self.analyzer:
            raise RuntimeError("Analyzer not initialized")
        
        start_time = time.time()
        
        try:
            logger.info("Analyzing query", query_length=len(query))
            
            # Perform analysis using the Epic1QueryAnalyzer (use 'analyze' method)
            analysis_result: QueryAnalysis = self.analyzer.analyze(query)
            
            # Extract data from Epic1 analysis structure
            epic1_data = analysis_result.metadata.get('epic1_analysis', {})
            
            # Extract complexity level and other data
            complexity = epic1_data.get('complexity_level', 'unknown')
            confidence = epic1_data.get('complexity_confidence', 0.0)
            routing_confidence = epic1_data.get('routing_confidence', 0.0)
            
            # Build features from Epic1 feature summary
            feature_summary = epic1_data.get('feature_summary', {})
            features = {
                "word_count": feature_summary.get('word_count', 0),
                "technical_density": feature_summary.get('technical_density', 0.0),
                "syntactic_complexity": feature_summary.get('syntactic_complexity', 0.0),
                "question_type": feature_summary.get('question_type', 'unknown'),
                "ambiguity_score": feature_summary.get('ambiguity_score', 0.0),
                "technical_terms": feature_summary.get('technical_terms', []),
                "composite_scores": feature_summary.get('composite_scores', {})
            }
            
            # Build recommended models from Epic1 analysis
            recommended_models = [{
                "provider": epic1_data.get('model_provider', 'unknown'),
                "name": epic1_data.get('model_name', 'unknown'),
                "full_model": epic1_data.get('recommended_model', 'unknown'),
                "confidence": routing_confidence,
                "fallback_chain": epic1_data.get('fallback_chain', [])
            }]
            
            # Build cost estimate
            cost_estimate = {
                "estimated_cost": epic1_data.get('cost_estimate', 0.0),
                "estimated_latency_ms": epic1_data.get('latency_estimate', 0)
            }
            
            # Convert to service response format
            result = {
                "query": query,
                "complexity": complexity,
                "confidence": confidence,
                "features": features,
                "recommended_models": recommended_models,
                "cost_estimate": cost_estimate,
                "routing_strategy": epic1_data.get('routing_strategy', 'balanced'),
                "processing_time": time.time() - start_time,
                "metadata": {
                    "analyzer_version": "1.0.0",
                    "timestamp": time.time(),
                    "context": context or {},
                    "epic1_analysis": {
                        "complexity_score": epic1_data.get('complexity_score', 0.0),
                        "complexity_breakdown": epic1_data.get('complexity_breakdown', {}),
                        "classification_reasoning": epic1_data.get('classification_reasoning', ''),
                        "recommendation_reasoning": epic1_data.get('recommendation_reasoning', ''),
                        "analysis_time_ms": epic1_data.get('analysis_time_ms', 0.0),
                        "phase_times_ms": epic1_data.get('phase_times_ms', {})
                    }
                }
            }
            
            # Update metrics
            ANALYSIS_REQUESTS.labels(status="success").inc()
            ANALYSIS_DURATION.labels(complexity=complexity).observe(result["processing_time"])
            COMPLEXITY_DISTRIBUTION.labels(complexity=complexity).inc()
            
            logger.info(
                "Query analysis completed",
                complexity=complexity,
                confidence=result["confidence"],
                processing_time=result["processing_time"]
            )
            
            return result
            
        except Exception as e:
            ANALYSIS_REQUESTS.labels(status="error").inc()
            logger.error("Query analysis failed", error=str(e), query_length=len(query))
            raise
    
    async def get_analyzer_status(self) -> Dict[str, Any]:
        """
        Get current analyzer status and performance metrics.
        
        Returns:
            Dictionary containing status information
        """
        if not self._initialized:
            return {
                "initialized": False,
                "status": "not_initialized"
            }
        
        try:
            # Get performance metrics from the analyzer
            performance_metrics = self.analyzer.get_performance_metrics()
            
            return {
                "initialized": True,
                "status": "healthy",
                "analyzer_type": "Epic1QueryAnalyzer",
                "configuration": {
                    "strategy": getattr(self.analyzer.model_recommender, 'strategy', None),
                    "feature_extraction_enabled": True,
                    "complexity_classification_enabled": True,
                    "model_recommendation_enabled": True
                },
                "performance": performance_metrics,
                "components": {
                    "feature_extractor": "healthy",
                    "complexity_classifier": "healthy", 
                    "model_recommender": "healthy"
                }
            }
            
        except Exception as e:
            logger.error("Failed to get analyzer status", error=str(e))
            return {
                "initialized": True,
                "status": "error",
                "error": str(e)
            }
    
    async def health_check(self) -> bool:
        """
        Perform health check on the analyzer service.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self._initialized:
                await self._initialize_analyzer()
            
            if not self.analyzer:
                return False
            
            # Perform a simple test analysis
            test_query = "What is the basic functionality of this system?"
            result = await self.analyze_query(test_query)
            
            # Check that we got a reasonable result
            if (result.get('complexity') in ['simple', 'medium', 'complex'] and
                isinstance(result.get('confidence'), (int, float)) and
                0.0 <= result.get('confidence', 0) <= 1.0):
                
                logger.debug("Health check passed")
                return True
            
            logger.warning("Health check failed - invalid result format")
            return False
            
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return False
    
    async def shutdown(self):
        """Graceful shutdown of the analyzer service."""
        logger.info("Shutting down QueryAnalyzerService")
        
        # Update component health metrics
        COMPONENT_HEALTH.labels(component="feature_extractor").set(0)
        COMPONENT_HEALTH.labels(component="complexity_classifier").set(0)
        COMPONENT_HEALTH.labels(component="model_recommender").set(0)
        
        self._initialized = False
        self.analyzer = None