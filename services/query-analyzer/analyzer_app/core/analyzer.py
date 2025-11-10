"""
Query Analyzer Service - Core Business Logic.

This module implements the QueryAnalyzerService that wraps the existing
Epic1QueryAnalyzer for use in the microservices architecture with Epic 8 enhancements.

Epic 8 Enhancements:
- Enhanced error handling and fallback mechanisms (FR-8.1.5)
- Performance optimization with <5s response time target
- Improved health monitoring and diagnostics
- Circuit breaker pattern for resilience
- Cost estimation with <5% error target (FR-8.1.4)
"""

import asyncio
import time
import uuid
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys
from dataclasses import dataclass
from enum import Enum
import traceback

import structlog
from prometheus_client import Counter, Histogram, Gauge

# Add main project to path to import existing components
# Use environment variable for containerized deployment
import os
project_root = Path(os.getenv('PROJECT_ROOT', Path(__file__).parent.parent.parent.parent.parent))
if project_root.exists():
    sys.path.insert(0, str(project_root))

# Import existing Epic 1 components
from src.components.query_processors.analyzers.epic1_query_analyzer import Epic1QueryAnalyzer
from src.components.query_processors.base import QueryAnalysis

logger = structlog.get_logger(__name__)

# Epic 8 Enhanced Metrics
ANALYSIS_REQUESTS = Counter('analyzer_requests_total', 'Total analysis requests', ['status', 'fallback_used'])
ANALYSIS_DURATION = Histogram('analyzer_duration_seconds', 'Analysis duration', ['complexity', 'phase'])
COMPLEXITY_DISTRIBUTION = Counter('analyzer_complexity_total', 'Queries by complexity', ['complexity'])
COMPONENT_HEALTH = Gauge('analyzer_component_health', 'Component health status', ['component'])
ERROR_RATE = Counter('analyzer_errors_total', 'Total errors', ['error_type', 'component'])
PERFORMANCE_VIOLATIONS = Counter('analyzer_performance_violations_total', 'Performance SLA violations', ['violation_type'])
FALLBACK_USAGE = Counter('analyzer_fallback_usage_total', 'Fallback mechanism usage', ['fallback_type', 'reason'])


class ServiceState(Enum):
    """Service operational states."""
    INITIALIZING = "initializing"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    UNAVAILABLE = "unavailable"


@dataclass
class PerformanceTarget:
    """Epic 8 Performance targets for the service."""
    response_time_target_ms: int = 5000  # 5s target, 2s preferred
    response_time_warning_ms: int = 2000  # Warning threshold
    accuracy_target: float = 0.85  # 85% accuracy target
    cost_error_target: float = 0.05  # <5% cost estimation error
    memory_limit_gb: float = 2.0  # <2GB memory usage


class CircuitBreakerState(Enum):
    """Circuit breaker states for failure handling."""
    CLOSED = "closed"
    OPEN = "open" 
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """Simple circuit breaker for fault tolerance."""
    failure_threshold: int = 5
    timeout_seconds: int = 60
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0.0
    
    def should_allow_request(self) -> bool:
        """Check if request should be allowed through."""
        now = time.time()
        
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if now - self.last_failure_time > self.timeout_seconds:
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Record successful request."""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
    
    def record_failure(self):
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN


class QueryAnalyzerService:
    """
    Epic 8 Enhanced Query Analyzer Service.
    
    This service provides production-grade capabilities:
    - Epic1QueryAnalyzer integration with enhanced error handling
    - Circuit breaker pattern for resilience (FR-8.1.5)
    - Performance monitoring with SLA tracking
    - Fallback mechanisms for model failures
    - Cost estimation with <5% error target (FR-8.1.4)
    - Enhanced health diagnostics and monitoring
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Query Analyzer Service with Epic 8 enhancements.
        
        Args:
            config: Configuration dictionary for the analyzer (None-safe)
        """
        # Fix: Handle None config gracefully for test compatibility
        self.config = config or {}
        self.analyzer: Optional[Epic1QueryAnalyzer] = None
        self._initialized = False
        self._initialization_lock = asyncio.Lock()
        
        # Epic 8 enhancements - Load from config or use defaults
        self._service_state = ServiceState.INITIALIZING
        
        # Load Epic 8 performance targets from config (None-safe)
        perf_config = self.config.get('performance_targets', {})
        self._performance_targets = PerformanceTarget(
            response_time_target_ms=perf_config.get('response_time_target_ms', 5000),
            response_time_warning_ms=perf_config.get('response_time_warning_ms', 2000),
            accuracy_target=perf_config.get('accuracy_target', 0.85),
            cost_error_target=perf_config.get('cost_error_target', 0.05),
            memory_limit_gb=perf_config.get('memory_limit_gb', 2.0)
        )
        
        # Load circuit breaker configuration (None-safe)
        cb_config = self.config.get('circuit_breaker', {})
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=cb_config.get('failure_threshold', 5),
            timeout_seconds=cb_config.get('timeout_seconds', 60)
        )
        
        self._startup_time = time.time()
        
        # Performance tracking
        self._request_times = []
        self._error_count = 0
        self._total_requests = 0
        self._complexity_accuracy_samples = []
        
        # Load fallback configuration (None-safe)
        fallback_config = self.config.get('fallback', {})
        self._fallback_enabled = fallback_config.get('enabled', True)
        self._fallback_threshold_ms = fallback_config.get('threshold_ms', 3000)
        
        logger.info("Initializing Epic 8 QueryAnalyzerService", 
                   config=self.config, 
                   performance_targets=self._performance_targets)
    
    async def _initialize_analyzer(self):
        """Initialize the Epic1QueryAnalyzer with Epic 8 enhanced error handling."""
        if self._initialized:
            return
        
        async with self._initialization_lock:
            if self._initialized:
                return
            
            initialization_start = time.time()
            
            try:
                self._service_state = ServiceState.INITIALIZING
                
                # Initialize the Epic1QueryAnalyzer with configuration
                logger.info("Starting Epic1QueryAnalyzer initialization")

                # Extract analyzer-specific config for Epic1QueryAnalyzer
                analyzer_config = self.config.get('analyzer', {})
                if not analyzer_config:
                    # Fallback to root config if analyzer key doesn't exist
                    analyzer_config = self.config

                logger.info("Creating Epic1QueryAnalyzer with extracted config",
                           has_analyzer_key='analyzer' in self.config)

                self.analyzer = Epic1QueryAnalyzer(config=analyzer_config)
                
                # Validate analyzer is working
                await self._validate_analyzer_initialization()
                
                self._initialized = True
                self._service_state = ServiceState.HEALTHY
                
                # Update component health metrics
                COMPONENT_HEALTH.labels(component="feature_extractor").set(1)
                COMPONENT_HEALTH.labels(component="complexity_classifier").set(1)
                COMPONENT_HEALTH.labels(component="model_recommender").set(1)
                
                initialization_time = time.time() - initialization_start
                logger.info("Epic1QueryAnalyzer initialized successfully", 
                          initialization_time=initialization_time)
                
            except Exception as e:
                self._service_state = ServiceState.FAILING
                ERROR_RATE.labels(error_type="initialization_failure", component="service").inc()
                
                logger.error("Failed to initialize Epic1QueryAnalyzer", 
                           error=str(e), 
                           traceback=traceback.format_exc())
                
                # Update component health metrics
                COMPONENT_HEALTH.labels(component="feature_extractor").set(0)
                COMPONENT_HEALTH.labels(component="complexity_classifier").set(0)
                COMPONENT_HEALTH.labels(component="model_recommender").set(0)
                raise
    
    async def _validate_analyzer_initialization(self):
        """Validate that the analyzer is properly initialized and working."""
        if not self.analyzer:
            raise RuntimeError("Analyzer not created")
        
        try:
            # Test with a simple query
            test_query = "Test initialization query"
            result = self.analyzer.analyze(test_query)
            
            if not result or not hasattr(result, 'metadata'):
                raise RuntimeError("Analyzer returned invalid result")
                
            logger.info("Analyzer validation passed")
            
        except Exception as e:
            logger.error("Analyzer validation failed", error=str(e))
            raise RuntimeError(f"Analyzer validation failed: {e}")
    
    async def analyze_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Epic 8 Enhanced query analysis with circuit breaker and fallback mechanisms.
        
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
            
        Raises:
            RuntimeError: If analyzer not initialized or circuit breaker is open
            ValueError: If query is invalid
            TimeoutError: If analysis exceeds performance targets
        """
        # Epic 8 enhancement: Circuit breaker check
        if not self._circuit_breaker.should_allow_request():
            ERROR_RATE.labels(error_type="circuit_breaker_open", component="service").inc()
            raise RuntimeError("Service temporarily unavailable due to circuit breaker")
        
        if not self._initialized:
            await self._initialize_analyzer()
        
        if not self.analyzer:
            self._service_state = ServiceState.UNAVAILABLE
            raise RuntimeError("Analyzer not initialized")
        
        # Input validation
        if not query or not query.strip():
            ERROR_RATE.labels(error_type="invalid_input", component="validation").inc()
            raise ValueError("Query cannot be empty")
        
        if len(query) > 10000:  # Epic 8 API spec limit
            ERROR_RATE.labels(error_type="query_too_long", component="validation").inc()
            raise ValueError("Query exceeds maximum length of 10,000 characters")
        
        request_id = str(uuid.uuid4())
        start_time = time.time()
        fallback_used = False
        
        try:
            self._total_requests += 1
            logger.info("Starting Epic 8 query analysis", 
                       query_length=len(query), 
                       request_id=request_id)
            
            # Perform analysis with timeout handling
            try:
                analysis_result = await asyncio.wait_for(
                    self._perform_analysis(query, context, request_id),
                    timeout=self._performance_targets.response_time_target_ms / 1000.0
                )
            except asyncio.TimeoutError:
                # Epic 8 enhancement: Fallback mechanism for timeouts
                PERFORMANCE_VIOLATIONS.labels(violation_type="timeout").inc()
                FALLBACK_USAGE.labels(fallback_type="timeout", reason="analysis_timeout").inc()
                
                if self._fallback_enabled:
                    logger.warning("Analysis timeout, using fallback", 
                                 request_id=request_id, 
                                 timeout_threshold=self._performance_targets.response_time_target_ms)
                    analysis_result = await self._fallback_analysis(query, context, request_id)
                    fallback_used = True
                else:
                    raise TimeoutError(f"Analysis timed out after {self._performance_targets.response_time_target_ms}ms")
            
            processing_time = time.time() - start_time
            
            # Epic 8 enhancement: Performance monitoring
            self._request_times.append(processing_time)
            if len(self._request_times) > 1000:  # Keep last 1000 requests
                self._request_times.pop(0)
            
            # Check performance targets
            processing_time_ms = processing_time * 1000
            if processing_time_ms > self._performance_targets.response_time_warning_ms:
                PERFORMANCE_VIOLATIONS.labels(violation_type="slow_response").inc()
                logger.warning("Slow response detected", 
                             processing_time_ms=processing_time_ms,
                             target_ms=self._performance_targets.response_time_warning_ms)
            
            # Update service state based on performance
            if processing_time_ms > self._performance_targets.response_time_target_ms:
                self._service_state = ServiceState.DEGRADED
            elif self._error_count > 0 and self._total_requests > 0:
                error_rate = self._error_count / self._total_requests
                if error_rate > 0.05:  # 5% error threshold
                    self._service_state = ServiceState.DEGRADED
                else:
                    self._service_state = ServiceState.HEALTHY
            else:
                self._service_state = ServiceState.HEALTHY
            
            # Record successful request for circuit breaker
            self._circuit_breaker.record_success()
            
            # Update metrics
            ANALYSIS_REQUESTS.labels(status="success", fallback_used=str(fallback_used)).inc()
            ANALYSIS_DURATION.labels(complexity=analysis_result["complexity"], phase="total").observe(processing_time)
            COMPLEXITY_DISTRIBUTION.labels(complexity=analysis_result["complexity"]).inc()
            
            logger.info(
                "Epic 8 query analysis completed successfully",
                request_id=request_id,
                complexity=analysis_result["complexity"],
                confidence=analysis_result["confidence"],
                processing_time_ms=processing_time_ms,
                fallback_used=fallback_used,
                service_state=self._service_state.value
            )
            
            return analysis_result
            
        except Exception as e:
            # Epic 8 enhancement: Enhanced error handling
            self._error_count += 1
            self._service_state = ServiceState.FAILING
            self._circuit_breaker.record_failure()
            
            error_type = type(e).__name__
            ERROR_RATE.labels(error_type=error_type, component="analysis").inc()
            ANALYSIS_REQUESTS.labels(status="error", fallback_used=str(fallback_used)).inc()
            
            logger.error("Epic 8 query analysis failed", 
                        request_id=request_id,
                        error=str(e), 
                        error_type=error_type,
                        query_length=len(query),
                        processing_time_ms=(time.time() - start_time) * 1000,
                        traceback=traceback.format_exc())
            raise
    
    async def _perform_analysis(self, query: str, context: Optional[Dict[str, Any]], request_id: str) -> Dict[str, Any]:
        """
        Perform the core Epic1QueryAnalyzer analysis with enhanced data formatting.
        
        Args:
            query: The query to analyze
            context: Optional context information
            request_id: Request ID for tracking
            
        Returns:
            Formatted analysis result compatible with Epic 8 API specification
        """
        phase_start = time.time()
        
        # Perform analysis using the Epic1QueryAnalyzer
        analysis_result: QueryAnalysis = self.analyzer.analyze(query)
        
        phase_time = time.time() - phase_start
        ANALYSIS_DURATION.labels(complexity="unknown", phase="epic1_analysis").observe(phase_time)
        
        # Extract data from Epic1 analysis structure with robust fallbacks
        epic1_data = analysis_result.metadata.get('epic1_analysis', {})

        # Try multiple data extraction paths for robustness
        if not epic1_data and hasattr(analysis_result, 'complexity'):
            # Fallback: extract directly from result attributes
            epic1_data = {
                'complexity_level': getattr(analysis_result, 'complexity', 'medium'),
                'complexity_confidence': getattr(analysis_result, 'confidence', 0.5),
                'routing_confidence': 0.5
            }

        # Extract complexity level with multiple fallback paths
        complexity = (epic1_data.get('complexity_level') or
                     epic1_data.get('complexity') or
                     getattr(analysis_result, 'complexity', 'medium'))

        confidence = (epic1_data.get('complexity_confidence') or
                     epic1_data.get('confidence') or
                     getattr(analysis_result, 'confidence', 0.5))

        routing_confidence = epic1_data.get('routing_confidence', confidence)  # Use complexity confidence as fallback

        # Build features from Epic1 feature summary - Epic 8 format
        feature_summary = epic1_data.get('feature_summary', {})

        # Ensure feature_summary exists
        if not feature_summary and hasattr(analysis_result, 'features'):
            # Extract from result attributes if available
            feature_summary = getattr(analysis_result, 'features', {})

        # Log what we extracted for debugging
        logger.debug("Feature extraction",
                    has_epic1_data=bool(epic1_data),
                    has_feature_summary=bool(feature_summary),
                    complexity=complexity)
        features = {
            "length": feature_summary.get('word_count', len(query.split())),
            "vocabulary_complexity": feature_summary.get('technical_density', 0.0),
            "technical_terms": feature_summary.get('technical_terms', []),
            "question_type": feature_summary.get('question_type', 'factual'),
            "linguistic_features": {
                "num_sentences": feature_summary.get('sentence_count', 1),
                "avg_word_length": feature_summary.get('avg_word_length', 5.0),
                "technical_density": feature_summary.get('technical_density', 0.0)
            },
            "structural_features": {
                "has_questions": '?' in query,
                "comparative_language": any(word in query.lower() for word in ['vs', 'versus', 'compare', 'difference']),
                "specificity_score": feature_summary.get('syntactic_complexity', 0.5)
            }
        }
        
        # Build recommended models list from Epic1 analysis - Epic 8 format
        primary_model = epic1_data.get('recommended_model', 'ollama/llama3.2:3b')
        fallback_chain = epic1_data.get('fallback_chain', ['openai/gpt-3.5-turbo'])
        recommended_models = [primary_model] + fallback_chain
        
        # Build cost estimate per model - Epic 8 format with enhanced accuracy
        cost_estimate = {}
        estimated_cost = epic1_data.get('cost_estimate', 0.0)
        if primary_model:
            cost_estimate[primary_model] = estimated_cost
        
        # Add fallback models with improved cost estimates
        default_costs = {
            'ollama/llama3.2:3b': 0.0,
            'openai/gpt-3.5-turbo': 0.002,
            'openai/gpt-4': 0.06,
            'mistral/mistral-large': 0.008,
            'anthropic/claude-3-sonnet': 0.003
        }
        
        for model in fallback_chain:
            if model not in cost_estimate:
                cost_estimate[model] = default_costs.get(model, 0.002)
        
        # Convert to service response format
        result = {
            "query": query,
            "complexity": complexity,
            "confidence": confidence,
            "features": features,
            "recommended_models": recommended_models,
            "cost_estimate": cost_estimate,
            "routing_strategy": epic1_data.get('routing_strategy', 'balanced'),
            "processing_time": phase_time,
            "metadata": {
                "analyzer_version": "1.0.0",
                "timestamp": time.time(),
                "request_id": request_id,
                "context": context or {},
                "service_state": self._service_state.value,
                "epic1_analysis": {
                    "complexity_score": epic1_data.get('complexity_score', 0.5),
                    "complexity_breakdown": epic1_data.get('complexity_breakdown', {}),
                    "classification_reasoning": epic1_data.get('classification_reasoning', ''),
                    "recommendation_reasoning": epic1_data.get('recommendation_reasoning', ''),
                    "analysis_time_ms": epic1_data.get('analysis_time_ms', phase_time * 1000),
                    "phase_times_ms": epic1_data.get('phase_times_ms', {}),
                    "routing_decision": {
                        "strategy": epic1_data.get('routing_strategy', 'balanced'),
                        "available_models": recommended_models,
                        "selection_reason": epic1_data.get('recommendation_reasoning', 'Default model selection'),
                        "cost_estimate": estimated_cost,
                        "quality_score": routing_confidence
                    }
                }
            }
        }
        
        return result
    
    async def _fallback_analysis(self, query: str, context: Optional[Dict[str, Any]], request_id: str) -> Dict[str, Any]:
        """
        Epic 8 Fallback analysis when primary analysis fails or times out.
        
        This provides basic rule-based analysis to ensure service availability.
        
        Args:
            query: The query to analyze
            context: Optional context information  
            request_id: Request ID for tracking
            
        Returns:
            Basic analysis result using fallback logic
        """
        logger.info("Using fallback analysis", request_id=request_id)
        
        fallback_start = time.time()
        
        # Basic rule-based complexity analysis
        word_count = len(query.split())
        char_count = len(query)
        question_marks = query.count('?')
        
        # Simple complexity heuristics
        if word_count <= 5 and char_count <= 50:
            complexity = "simple"
            confidence = 0.7
            primary_model = "ollama/llama3.2:3b"
        elif word_count <= 15 and char_count <= 200:
            complexity = "medium"
            confidence = 0.6
            primary_model = "openai/gpt-3.5-turbo"
        else:
            complexity = "complex"
            confidence = 0.5
            primary_model = "openai/gpt-4"
        
        # Technical terms detection (basic)
        technical_terms = []
        technical_keywords = ['api', 'database', 'algorithm', 'neural', 'machine learning', 'deep learning', 'kubernetes', 'docker']
        for term in technical_keywords:
            if term in query.lower():
                technical_terms.append(term)
        
        fallback_time = time.time() - fallback_start
        
        result = {
            "query": query,
            "complexity": complexity,
            "confidence": confidence,
            "features": {
                "length": word_count,
                "vocabulary_complexity": len(technical_terms) / max(word_count, 1),
                "technical_terms": technical_terms,
                "question_type": "question" if question_marks > 0 else "statement",
                "linguistic_features": {
                    "num_sentences": query.count('.') + question_marks + 1,
                    "avg_word_length": sum(len(word) for word in query.split()) / max(word_count, 1),
                    "technical_density": len(technical_terms) / max(word_count, 1)
                },
                "structural_features": {
                    "has_questions": question_marks > 0,
                    "comparative_language": any(word in query.lower() for word in ['vs', 'versus', 'compare', 'difference']),
                    "specificity_score": min(word_count / 10.0, 1.0)
                }
            },
            "recommended_models": [primary_model, "ollama/llama3.2:3b"],
            "cost_estimate": {
                primary_model: 0.002 if primary_model != "ollama/llama3.2:3b" else 0.0,
                "ollama/llama3.2:3b": 0.0
            },
            "routing_strategy": "cost_optimized",  # Fallback uses cost-optimized
            "processing_time": fallback_time,
            "metadata": {
                "analyzer_version": "1.0.0-fallback",
                "timestamp": time.time(),
                "request_id": request_id,
                "context": context or {},
                "service_state": self._service_state.value,
                "fallback_used": True,
                "fallback_reason": "Primary analysis timeout or failure"
            }
        }
        
        return result
    
    async def get_analyzer_status(self) -> Dict[str, Any]:
        """
        Epic 8 Enhanced analyzer status with comprehensive performance metrics.
        
        Returns:
            Dictionary containing detailed status information including:
            - Service state and health
            - Performance metrics aligned with Epic 8 targets
            - Component status and configuration
            - Circuit breaker state and error rates
        """
        current_time = time.time()
        uptime_seconds = current_time - self._startup_time
        
        if not self._initialized:
            return {
                "initialized": False,
                "status": "not_initialized",
                "service_state": self._service_state.value,
                "uptime_seconds": uptime_seconds,
                "analyzer_type": "Epic1QueryAnalyzer",
                "performance_targets": {
                    "response_time_target_ms": self._performance_targets.response_time_target_ms,
                    "response_time_warning_ms": self._performance_targets.response_time_warning_ms,
                    "accuracy_target": self._performance_targets.accuracy_target,
                    "cost_error_target": self._performance_targets.cost_error_target
                }
            }
        
        try:
            # Calculate performance metrics
            avg_response_time_ms = 0.0
            p95_response_time_ms = 0.0
            requests_per_second = 0.0
            error_rate = 0.0
            
            if self._request_times:
                avg_response_time_ms = (sum(self._request_times) / len(self._request_times)) * 1000
                sorted_times = sorted(self._request_times)
                p95_index = int(len(sorted_times) * 0.95)
                p95_response_time_ms = sorted_times[p95_index] * 1000 if p95_index < len(sorted_times) else 0
                
                if uptime_seconds > 0:
                    requests_per_second = self._total_requests / uptime_seconds
            
            if self._total_requests > 0:
                error_rate = self._error_count / self._total_requests
            
            # Calculate complexity distribution
            complexity_distribution = {"simple": 0.0, "medium": 0.0, "complex": 0.0}
            # Note: This would need to be tracked during analysis for accurate distribution
            
            # Get performance metrics from the analyzer if available
            epic1_performance = {}
            try:
                if hasattr(self.analyzer, 'get_performance_metrics'):
                    epic1_performance = self.analyzer.get_performance_metrics()
            except Exception as e:
                logger.warning("Could not get Epic1 performance metrics", error=str(e))
            
            status_result = {
                "initialized": True,
                "status": "healthy" if self._service_state == ServiceState.HEALTHY else self._service_state.value,
                "service_state": self._service_state.value,
                "uptime_seconds": uptime_seconds,
                "analyzer_type": "Epic1QueryAnalyzer",
                "configuration": {
                    "strategy": getattr(self.analyzer.model_recommender, 'strategy', None) if self.analyzer else None,
                    "feature_extraction_enabled": True,
                    "complexity_classification_enabled": True,
                    "model_recommendation_enabled": True,
                    "fallback_enabled": self._fallback_enabled,
                    "fallback_threshold_ms": self._fallback_threshold_ms
                },
                "performance": {
                    "total_requests": self._total_requests,
                    "successful_requests": self._total_requests - self._error_count,
                    "failed_requests": self._error_count,
                    "avg_response_time_ms": avg_response_time_ms,
                    "p95_response_time_ms": p95_response_time_ms,
                    "requests_per_second": requests_per_second,
                    "error_rate": error_rate,
                    "complexity_distribution": complexity_distribution,
                    "performance_targets": {
                        "response_time_target_ms": self._performance_targets.response_time_target_ms,
                        "response_time_warning_ms": self._performance_targets.response_time_warning_ms,
                        "accuracy_target": self._performance_targets.accuracy_target,
                        "cost_error_target": self._performance_targets.cost_error_target,
                        "memory_limit_gb": self._performance_targets.memory_limit_gb
                    },
                    "sla_compliance": {
                        "response_time_compliance": avg_response_time_ms <= self._performance_targets.response_time_target_ms,
                        "error_rate_compliance": error_rate <= 0.01,  # 1% error threshold
                        "availability_compliance": self._service_state != ServiceState.UNAVAILABLE
                    }
                },
                "circuit_breaker": {
                    "state": self._circuit_breaker.state.value,
                    "failure_count": self._circuit_breaker.failure_count,
                    "failure_threshold": self._circuit_breaker.failure_threshold,
                    "last_failure_time": self._circuit_breaker.last_failure_time
                },
                "components": {
                    "feature_extractor": "healthy" if self._service_state != ServiceState.FAILING else "degraded",
                    "complexity_classifier": "healthy" if self._service_state != ServiceState.FAILING else "degraded",
                    "model_recommender": "healthy" if self._service_state != ServiceState.FAILING else "degraded"
                },
                "epic1_performance": epic1_performance
            }
            
            return status_result
            
        except Exception as e:
            ERROR_RATE.labels(error_type="status_error", component="service").inc()
            logger.error("Failed to get analyzer status", error=str(e), traceback=traceback.format_exc())
            
            return {
                "initialized": True,
                "status": "error",
                "service_state": ServiceState.FAILING.value,
                "error": str(e),
                "uptime_seconds": uptime_seconds,
                "analyzer_type": "Epic1QueryAnalyzer"
            }
    
    async def health_check(self) -> bool:
        """
        Epic 8 Enhanced health check with comprehensive validation.
        
        Returns:
            True if healthy, False otherwise
        """
        health_start = time.time()
        
        try:
            # Check circuit breaker state
            if self._circuit_breaker.state == CircuitBreakerState.OPEN:
                logger.warning("Health check failed - circuit breaker open")
                return False
            
            if not self._initialized:
                await self._initialize_analyzer()
            
            if not self.analyzer:
                logger.warning("Health check failed - analyzer not initialized")
                return False
            
            # Perform a simple test analysis with timeout
            test_query = "What is machine learning?"  # Simple test query
            
            try:
                result = await asyncio.wait_for(
                    self.analyze_query(test_query),
                    timeout=2.0  # 2 second health check timeout
                )
                
                # Validate result structure
                if not self._validate_analysis_result(result):
                    logger.warning("Health check failed - invalid result format")
                    return False
                
                # Check performance compliance
                health_time_ms = (time.time() - health_start) * 1000
                if health_time_ms > 1000:  # Health check should complete in <1s
                    logger.warning("Health check slow", health_time_ms=health_time_ms)
                    return False
                
                # Check service state
                if self._service_state == ServiceState.UNAVAILABLE:
                    return False
                
                logger.debug("Epic 8 health check passed", health_time_ms=health_time_ms)
                return True
                
            except asyncio.TimeoutError:
                logger.warning("Health check timed out")
                return False
            
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return False
    
    def _validate_analysis_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate that analysis result has expected structure and values.
        
        Args:
            result: Analysis result to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            required_fields = ['query', 'complexity', 'confidence', 'features', 'recommended_models']
            for field in required_fields:
                if field not in result:
                    return False
            
            # Check complexity level
            if result.get('complexity') not in ['simple', 'medium', 'complex']:
                return False
            
            # Check confidence range
            confidence = result.get('confidence', -1)
            if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
                return False
            
            # Check recommended models
            models = result.get('recommended_models', [])
            if not isinstance(models, list) or len(models) == 0:
                return False
            
            return True
            
        except Exception:
            return False
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get detailed performance metrics for monitoring and alerting.
        
        Returns:
            Dictionary with comprehensive performance data
        """
        current_time = time.time()
        uptime_seconds = current_time - self._startup_time
        
        metrics = {
            "uptime_seconds": uptime_seconds,
            "total_requests": self._total_requests,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(self._total_requests, 1),
            "service_state": self._service_state.value,
            "circuit_breaker_state": self._circuit_breaker.state.value,
            "fallback_enabled": self._fallback_enabled,
            "performance_targets": {
                "response_time_target_ms": self._performance_targets.response_time_target_ms,
                "response_time_warning_ms": self._performance_targets.response_time_warning_ms,
                "accuracy_target": self._performance_targets.accuracy_target
            }
        }
        
        if self._request_times:
            avg_time = sum(self._request_times) / len(self._request_times)
            sorted_times = sorted(self._request_times)
            
            metrics.update({
                "avg_response_time_ms": avg_time * 1000,
                "p50_response_time_ms": sorted_times[len(sorted_times)//2] * 1000,
                "p95_response_time_ms": sorted_times[int(len(sorted_times)*0.95)] * 1000,
                "p99_response_time_ms": sorted_times[int(len(sorted_times)*0.99)] * 1000,
                "requests_per_second": self._total_requests / max(uptime_seconds, 1)
            })
        
        return metrics
    
    async def reset_circuit_breaker(self) -> bool:
        """
        Administrative method to reset the circuit breaker.
        
        Returns:
            True if reset successful
        """
        try:
            self._circuit_breaker.state = CircuitBreakerState.CLOSED
            self._circuit_breaker.failure_count = 0
            self._circuit_breaker.last_failure_time = 0.0
            
            logger.info("Circuit breaker reset successfully")
            return True
        except Exception as e:
            logger.error("Failed to reset circuit breaker", error=str(e))
            return False
    
    async def shutdown(self):
        """Epic 8 Enhanced graceful shutdown of the analyzer service."""
        logger.info("Starting Epic 8 QueryAnalyzerService shutdown")
        
        # Set service state to unavailable
        self._service_state = ServiceState.UNAVAILABLE
        
        # Update component health metrics
        COMPONENT_HEALTH.labels(component="feature_extractor").set(0)
        COMPONENT_HEALTH.labels(component="complexity_classifier").set(0)  
        COMPONENT_HEALTH.labels(component="model_recommender").set(0)
        
        # Log final performance statistics
        if self._total_requests > 0:
            final_error_rate = self._error_count / self._total_requests
            avg_response_time = sum(self._request_times) / len(self._request_times) if self._request_times else 0
            
            logger.info("Service shutdown statistics",
                       total_requests=self._total_requests,
                       error_rate=final_error_rate,
                       avg_response_time_ms=avg_response_time * 1000,
                       uptime_seconds=time.time() - self._startup_time)
        
        self._initialized = False
        self.analyzer = None
        
        logger.info("Epic 8 QueryAnalyzerService shutdown complete")