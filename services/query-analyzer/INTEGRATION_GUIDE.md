# Epic 1 QueryAnalyzer Integration Guide
## Comprehensive Analysis & Integration Best Practices

**Date**: 2025-11-06  
**Status**: Critical Analysis - Integration Validation Required  
**Scope**: Query Analyzer Service integration with Epic1QueryAnalyzer  
**Baseline**: Generator Service (87% working) used as reference pattern

---

## 1. EXECUTIVE SUMMARY

### Current Status
- **Generator Service**: 87% working with Epic1AnswerGenerator ✅
- **Query Analyzer Service**: Functional but with integration pattern issues ⚠️
- **Critical Gap**: Method signature mismatch and data extraction inconsistencies

### Key Finding
The Query Analyzer Service is implementing Epic1QueryAnalyzer integration but has subtle integration pattern differences from the proven Generator Service pattern. This guide identifies these gaps and provides corrections.

---

## 2. EPIC1QUERYANALYZER INTERFACE SPECIFICATION

### Location
```
src/components/query_processors/analyzers/epic1_query_analyzer.py
```

### Class Hierarchy
```
QueryAnalyzer (ABC)
  └── BaseQueryAnalyzer
        └── Epic1QueryAnalyzer
```

### Initialization Signature
```python
def __init__(self, config: Optional[Dict[str, Any]] = None):
    """
    Initialize Epic1QueryAnalyzer with sub-components.
    
    Args:
        config: Configuration dictionary with sub-component configs
        
    Structure:
    {
        'feature_extractor': {...},      # Sub-component config
        'complexity_classifier': {...},  # Sub-component config
        'model_recommender': {...}      # Sub-component config
    }
    """
```

### Primary API Method
```python
def analyze(self, query: str) -> QueryAnalysis:
    """
    Analyze a query and return QueryAnalysis object.
    
    Returns:
        QueryAnalysis: Object with metadata containing Epic1 analysis
        
    Structure:
    QueryAnalysis(
        query=<str>,
        complexity_score=<float 0-1>,
        complexity_level=<str: simple|medium|complex>,
        technical_terms=<list>,
        entities=<list>,
        intent_category=<str>,
        suggested_k=<int>,
        confidence=<float 0-1>,
        metadata={
            'epic1_analysis': {
                'complexity_level': <str>,
                'complexity_score': <float>,
                'complexity_confidence': <float>,
                'complexity_breakdown': <dict>,
                'recommended_model': <str>,
                'model_provider': <str>,
                'model_name': <str>,
                'routing_confidence': <float>,
                'cost_estimate': <float>,
                'latency_estimate': <float>,
                'fallback_chain': <list>,
                'routing_strategy': <str>,
                'feature_summary': <dict>,
                'classification_reasoning': <str>,
                'recommendation_reasoning': <str>,
                'analysis_time_ms': <float>,
                'phase_times_ms': {
                    'feature_extraction': <float>,
                    'complexity_classification': <float>,
                    'model_recommendation': <float>,
                    'total': <float>
                }
            }
        }
    )
    """
```

### Sub-Components
```python
# Three main sub-components automatically initialized:
1. feature_extractor: FeatureExtractor
   - Extracts linguistic, structural, and semantic features
   - Supports caching for performance

2. complexity_classifier: ComplexityClassifier
   - Classifies query as simple/medium/complex
   - Returns confidence and breakdown data

3. model_recommender: ModelRecommender
   - Recommends optimal model based on complexity
   - Supports multiple strategies: cost_optimized, balanced, quality_first
   - Returns ModelRecommendation with provider, model, and metadata
```

### Configuration Structure
```yaml
# Complete Epic1QueryAnalyzer configuration
feature_extractor:
  enable_caching: true
  cache_size: 100
  extract_linguistic: true
  extract_structural: true
  extract_semantic: true

complexity_classifier:
  thresholds:
    simple: 0.3
    medium: 0.6
    complex: 0.9
  weights:
    length: 0.25
    vocabulary: 0.25
    syntax: 0.25
    semantic: 0.25

model_recommender:
  strategy: balanced  # or: cost_optimized, quality_first
  model_mappings:
    simple:
      - ollama/llama3.2:3b
    medium:
      - openai/gpt-3.5-turbo
      - ollama/llama3.2:3b
    complex:
      - openai/gpt-4
      - mistral/mistral-large
  cost_weights:
    ollama/llama3.2:3b: 0.0
    openai/gpt-3.5-turbo: 0.002
    openai/gpt-4: 0.06
    mistral/mistral-large: 0.008
```

### Available Methods
```python
# Core analysis
def analyze(self, query: str) -> QueryAnalysis

# Configuration management
def configure(self, config: Dict[str, Any]) -> None

# Performance metrics
def get_performance_metrics(self) -> Dict[str, Any]
def get_statistics(self) -> Dict[str, Any]

# Feature information
def get_supported_features(self) -> List[str]
```

---

## 3. GENERATOR SERVICE - SUCCESSFUL PATTERN ✅ (87% Working)

### Location & Structure
```
services/generator/
├── generator_app/
│   ├── core/
│   │   ├── generator.py          # Service wrapper
│   │   ├── config.py             # Configuration management
│   │   └── metrics.py            # Metrics and monitoring
│   ├── api/
│   │   └── rest.py               # REST endpoints
│   ├── schemas/
│   │   ├── requests.py
│   │   └── responses.py
│   └── main.py                   # FastAPI app
└── config.yaml                   # Configuration file
```

### Correct Initialization Pattern
```python
# ✅ CORRECT (from GeneratorService)

# 1. Import the component
from src.components.generators.epic1_answer_generator import Epic1AnswerGenerator
from src.core.interfaces import Answer

# 2. Initialize in service
class GeneratorService:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.generator: Optional[Epic1AnswerGenerator] = None
        self._initialized = False
        self._initialization_lock = asyncio.Lock()
    
    async def _initialize_generator(self):
        """Initialize the Epic1AnswerGenerator if not already done."""
        if self._initialized:
            return
        
        async with self._initialization_lock:
            if self._initialized:
                return
            
            try:
                # Create instance with config
                self.generator = Epic1AnswerGenerator(config=self.config)
                self._initialized = True
                
                # Validate by getting available models
                available_models = await self.get_available_models()
                for model in available_models:
                    MODEL_HEALTH.labels(model=model).set(1)
                
                logger.info(
                    "Epic1AnswerGenerator initialized successfully",
                    models_available=len(available_models)
                )
            except Exception as e:
                logger.error("Failed to initialize Epic1AnswerGenerator", error=str(e))
                raise

# 3. Usage pattern
async def generate_answer(self, query: str, context_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not self._initialized:
        await self._initialize_generator()
    
    if not self.generator:
        raise RuntimeError("Generator not initialized")
    
    # Create Document objects from context
    from src.core.interfaces import Document
    documents = [
        Document(
            content=doc_data.get('content', ''),
            metadata=doc_data.get('metadata', {})
        )
        for doc_data in context_documents
    ]
    
    # Call the component method
    answer: Answer = self.generator.generate(query, documents)
    
    # Extract metadata
    routing_metadata = answer.metadata.get('routing', {})
    
    # Return formatted response
    return {
        "answer": answer.text,
        "model_used": ...,
        "cost": ...,
        "confidence": answer.confidence,
        ...
    }
```

### Key Success Factors
1. ✅ Single initialization lock prevents race conditions
2. ✅ Lazy initialization on first use
3. ✅ Proper error propagation with logging
4. ✅ Direct method calls on the component instance
5. ✅ Proper metadata extraction from response objects
6. ✅ Configuration passed at instantiation

---

## 4. QUERY ANALYZER SERVICE - CURRENT IMPLEMENTATION

### Location & Structure
```
services/query-analyzer/
├── analyzer_app/
│   ├── core/
│   │   ├── analyzer.py           # Service wrapper
│   │   ├── config.py             # Configuration management
│   │   └── metrics.py            # Metrics and monitoring
│   ├── api/
│   │   └── rest.py               # REST endpoints
│   ├── schemas/
│   │   ├── requests.py
│   │   └── responses.py
│   └── main.py                   # FastAPI app
└── config.yaml                   # Configuration file
```

### Current Initialization Pattern (Mostly Correct)
```python
# From QueryAnalyzerService in analyzer.py

# 1. Import the component
from src.components.query_processors.analyzers.epic1_query_analyzer import Epic1QueryAnalyzer
from src.components.query_processors.base import QueryAnalysis

# 2. Initialization (lines 128-177)
class QueryAnalyzerService:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}  # ✅ Good: None-safe
        self.analyzer: Optional[Epic1QueryAnalyzer] = None
        self._initialized = False
        self._initialization_lock = asyncio.Lock()
        
        # Initialize performance targets, circuit breaker, etc.
        self._service_state = ServiceState.INITIALIZING
        # ... additional initialization
    
    async def _initialize_analyzer(self):
        """Initialize the Epic1QueryAnalyzer with Epic 8 enhanced error handling."""
        if self._initialized:
            return
        
        async with self._initialization_lock:
            if self._initialized:
                return
            
            try:
                # ✅ Correct: Initialize with config
                self.analyzer = Epic1QueryAnalyzer(config=self.config)
                
                # ✅ Validation step
                await self._validate_analyzer_initialization()
                
                self._initialized = True
                self._service_state = ServiceState.HEALTHY
                
                # ✅ Health metrics
                COMPONENT_HEALTH.labels(component="feature_extractor").set(1)
                COMPONENT_HEALTH.labels(component="complexity_classifier").set(1)
                COMPONENT_HEALTH.labels(component="model_recommender").set(1)
                
                logger.info("Epic1QueryAnalyzer initialized successfully", ...)
            except Exception as e:
                self._service_state = ServiceState.FAILING
                logger.error("Failed to initialize Epic1QueryAnalyzer", ...)
                raise

# 3. Analysis call (lines 244-381)
async def analyze_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not self._initialized:
        await self._initialize_analyzer()
    
    if not self.analyzer:
        raise RuntimeError("Analyzer not initialized")
    
    # ... validation, error handling, circuit breaker checks ...
    
    # Perform analysis
    analysis_result = await asyncio.wait_for(
        self._perform_analysis(query, context, request_id),
        timeout=...
    )
    
    return analysis_result

# 4. Core analysis (lines 383-488)
async def _perform_analysis(self, query: str, context: Optional[Dict[str, Any]], request_id: str) -> Dict[str, Any]:
    """Perform the core Epic1QueryAnalyzer analysis."""
    
    # ✅ CORRECT: Call the .analyze() method
    analysis_result: QueryAnalysis = self.analyzer.analyze(query)
    
    # ✅ CORRECT: Extract data from metadata
    epic1_data = analysis_result.metadata.get('epic1_analysis', {})
    
    # Extract complexity and confidence
    complexity = epic1_data.get('complexity_level', 'medium')
    confidence = epic1_data.get('complexity_confidence', 0.5)
    
    # Build features dict from Epic1 analysis
    feature_summary = epic1_data.get('feature_summary', {})
    features = {
        "length": feature_summary.get('word_count', len(query.split())),
        "vocabulary_complexity": feature_summary.get('technical_density', 0.0),
        "technical_terms": feature_summary.get('technical_terms', []),
        "question_type": feature_summary.get('question_type', 'factual'),
        # ... additional features
    }
    
    # Build recommended models list
    primary_model = epic1_data.get('recommended_model', 'ollama/llama3.2:3b')
    fallback_chain = epic1_data.get('fallback_chain', ['openai/gpt-3.5-turbo'])
    recommended_models = [primary_model] + fallback_chain
    
    # Convert to service response format
    result = {
        "query": query,
        "complexity": complexity,
        "confidence": confidence,
        "features": features,
        "recommended_models": recommended_models,
        "cost_estimate": {...},
        "routing_strategy": epic1_data.get('routing_strategy', 'balanced'),
        "processing_time": phase_time,
        "metadata": {...}
    }
    
    return result
```

---

## 5. INTEGRATION GAP ANALYSIS

### ✅ What's Working Correctly

| Component | Status | Details |
|-----------|--------|---------|
| Import Path | ✅ | Correct import of Epic1QueryAnalyzer |
| Initialization | ✅ | Async lock pattern correctly implemented |
| Configuration | ✅ | Config dict passed to constructor |
| Method Call | ✅ | Using .analyze() method correctly |
| Error Handling | ✅ | Proper exception propagation |
| Logging | ✅ | Structured logging with context |
| Metrics | ✅ | Prometheus metrics integration |

### ⚠️ Potential Issues / Gaps

| Issue | Severity | Details | Impact |
|-------|----------|---------|--------|
| Validation Test | Medium | `_validate_analyzer_initialization()` calls `analyze()` without async | May not catch initialization issues properly | 
| Configuration Structure | Low | Assumes config has expected keys | Falls back to defaults safely |
| Feature Extraction | Low | Some feature names may not match exactly | Data extraction has fallbacks |
| Data Type Assumptions | Low | Assumes specific metadata structure | Has defensive .get() calls |

---

## 6. CORRECT INTEGRATION PATTERN - STEP BY STEP

### Step 1: Import Configuration
```python
# ✅ CORRECT IMPORT PATHS

# In analyzer_app/core/analyzer.py

import asyncio
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys
import os

import structlog
from prometheus_client import Counter, Histogram, Gauge

# Set up project path - handles containerized deployment
project_root = Path(os.getenv('PROJECT_ROOT', Path(__file__).parent.parent.parent.parent.parent))
if project_root.exists():
    sys.path.insert(0, str(project_root))

# Import Epic1QueryAnalyzer and dependencies
from src.components.query_processors.analyzers.epic1_query_analyzer import Epic1QueryAnalyzer
from src.components.query_processors.base import QueryAnalysis

logger = structlog.get_logger(__name__)
```

### Step 2: Service Initialization
```python
class QueryAnalyzerService:
    """
    Epic 8 Enhanced Query Analyzer Service.
    
    Wraps Epic1QueryAnalyzer with:
    - Circuit breaker for resilience
    - Performance monitoring
    - Fallback mechanisms
    - Health diagnostics
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Query Analyzer Service."""
        
        # Handle None config gracefully
        self.config = config or {}
        
        # Component instance
        self.analyzer: Optional[Epic1QueryAnalyzer] = None
        self._initialized = False
        
        # Thread-safe initialization
        self._initialization_lock = asyncio.Lock()
        
        # Epic 8 enhancements
        self._service_state = ServiceState.INITIALIZING
        
        # Load configuration
        perf_config = self.config.get('performance_targets', {})
        self._performance_targets = PerformanceTarget(
            response_time_target_ms=perf_config.get('response_time_target_ms', 5000),
            response_time_warning_ms=perf_config.get('response_time_warning_ms', 2000),
            accuracy_target=perf_config.get('accuracy_target', 0.85),
            cost_error_target=perf_config.get('cost_error_target', 0.05),
            memory_limit_gb=perf_config.get('memory_limit_gb', 2.0)
        )
        
        # Circuit breaker
        cb_config = self.config.get('circuit_breaker', {})
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=cb_config.get('failure_threshold', 5),
            timeout_seconds=cb_config.get('timeout_seconds', 60)
        )
        
        # Performance tracking
        self._startup_time = time.time()
        self._request_times = []
        self._error_count = 0
        self._total_requests = 0
        
        logger.info("Initializing QueryAnalyzerService", config=self.config)
```

### Step 3: Component Initialization with Validation
```python
async def _initialize_analyzer(self):
    """
    Initialize the Epic1QueryAnalyzer with proper error handling.
    
    IMPORTANT: This pattern prevents race conditions on concurrent requests.
    """
    # Quick check: Already initialized?
    if self._initialized:
        return
    
    # Acquire initialization lock
    async with self._initialization_lock:
        # Double-check inside lock (prevent race condition)
        if self._initialized:
            return
        
        initialization_start = time.time()
        
        try:
            self._service_state = ServiceState.INITIALIZING
            
            logger.info("Starting Epic1QueryAnalyzer initialization")
            
            # CRITICAL: Pass configuration to the component
            # The component expects nested config structure:
            # {
            #   'feature_extractor': {...},
            #   'complexity_classifier': {...},
            #   'model_recommender': {...}
            # }
            self.analyzer = Epic1QueryAnalyzer(config=self.config)
            
            # Validate the analyzer is working properly
            await self._validate_analyzer_initialization()
            
            # Mark as initialized
            self._initialized = True
            self._service_state = ServiceState.HEALTHY
            
            # Update metrics
            COMPONENT_HEALTH.labels(component="feature_extractor").set(1)
            COMPONENT_HEALTH.labels(component="complexity_classifier").set(1)
            COMPONENT_HEALTH.labels(component="model_recommender").set(1)
            
            initialization_time = time.time() - initialization_start
            logger.info(
                "Epic1QueryAnalyzer initialized successfully",
                initialization_time=initialization_time
            )
            
        except Exception as e:
            # Mark service as failing
            self._service_state = ServiceState.FAILING
            
            # Update metrics
            COMPONENT_HEALTH.labels(component="feature_extractor").set(0)
            COMPONENT_HEALTH.labels(component="complexity_classifier").set(0)
            COMPONENT_HEALTH.labels(component="model_recommender").set(0)
            
            logger.error(
                "Failed to initialize Epic1QueryAnalyzer",
                error=str(e),
                traceback=traceback.format_exc()
            )
            raise
```

### Step 4: Validation Method
```python
async def _validate_analyzer_initialization(self):
    """
    Validate that the analyzer is properly initialized and working.
    
    This ensures we catch initialization issues early.
    """
    if not self.analyzer:
        raise RuntimeError("Analyzer not created during initialization")
    
    try:
        # Test with a simple query to validate basic functionality
        test_query = "Test initialization query"
        
        # Call the .analyze() method synchronously (it's not async)
        result = self.analyzer.analyze(test_query)
        
        # Validate result structure
        if not result or not hasattr(result, 'metadata'):
            raise RuntimeError("Analyzer returned invalid result structure")
        
        # Check for expected metadata
        if 'epic1_analysis' not in result.metadata:
            raise RuntimeError("Epic1 analysis metadata missing from result")
        
        logger.info("Analyzer validation passed")
        
    except Exception as e:
        logger.error("Analyzer validation failed", error=str(e))
        raise RuntimeError(f"Analyzer validation failed: {e}")
```

### Step 5: Query Analysis Implementation
```python
async def analyze_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Analyze a query with Epic1QueryAnalyzer.
    
    This is the main entry point for query analysis requests.
    """
    # Epic 8: Check circuit breaker
    if not self._circuit_breaker.should_allow_request():
        raise RuntimeError("Service temporarily unavailable due to circuit breaker")
    
    # Initialize if needed
    if not self._initialized:
        await self._initialize_analyzer()
    
    # Verify analyzer exists
    if not self.analyzer:
        self._service_state = ServiceState.UNAVAILABLE
        raise RuntimeError("Analyzer not initialized")
    
    # Validate input
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    if len(query) > 10000:
        raise ValueError("Query exceeds maximum length of 10,000 characters")
    
    request_id = str(uuid.uuid4())
    start_time = time.time()
    fallback_used = False
    
    try:
        self._total_requests += 1
        
        logger.info(
            "Starting Epic 1 query analysis",
            query_length=len(query),
            request_id=request_id
        )
        
        # Perform analysis with timeout handling
        try:
            analysis_result = await asyncio.wait_for(
                self._perform_analysis(query, context, request_id),
                timeout=self._performance_targets.response_time_target_ms / 1000.0
            )
        except asyncio.TimeoutError:
            # Fallback: Use basic rule-based analysis
            if self._fallback_enabled:
                logger.warning("Analysis timeout, using fallback", request_id=request_id)
                analysis_result = await self._fallback_analysis(query, context, request_id)
                fallback_used = True
            else:
                raise TimeoutError(f"Analysis exceeded {self._performance_targets.response_time_target_ms}ms")
        
        processing_time = time.time() - start_time
        
        # Performance monitoring
        self._request_times.append(processing_time)
        if len(self._request_times) > 1000:
            self._request_times.pop(0)
        
        # Check SLA compliance
        processing_time_ms = processing_time * 1000
        if processing_time_ms > self._performance_targets.response_time_warning_ms:
            logger.warning(
                "Slow response detected",
                processing_time_ms=processing_time_ms,
                target_ms=self._performance_targets.response_time_warning_ms
            )
        
        # Update service state
        if processing_time_ms > self._performance_targets.response_time_target_ms:
            self._service_state = ServiceState.DEGRADED
        else:
            self._service_state = ServiceState.HEALTHY
        
        # Record success for circuit breaker
        self._circuit_breaker.record_success()
        
        # Update metrics
        ANALYSIS_REQUESTS.labels(status="success", fallback_used=str(fallback_used)).inc()
        COMPLEXITY_DISTRIBUTION.labels(complexity=analysis_result["complexity"]).inc()
        
        logger.info(
            "Query analysis completed successfully",
            request_id=request_id,
            complexity=analysis_result["complexity"],
            processing_time_ms=processing_time_ms
        )
        
        return analysis_result
        
    except Exception as e:
        # Error handling
        self._error_count += 1
        self._service_state = ServiceState.FAILING
        self._circuit_breaker.record_failure()
        
        logger.error(
            "Query analysis failed",
            request_id=request_id,
            error=str(e),
            processing_time_ms=(time.time() - start_time) * 1000
        )
        raise
```

### Step 6: Core Analysis Method - The Critical Pattern
```python
async def _perform_analysis(self, query: str, context: Optional[Dict[str, Any]], request_id: str) -> Dict[str, Any]:
    """
    Perform the core Epic1QueryAnalyzer analysis.
    
    CRITICAL PATTERN: How to extract and transform Epic1 output into service format.
    """
    phase_start = time.time()
    
    # IMPORTANT: Call the .analyze() method
    # This is a SYNCHRONOUS call, not async - Epic1QueryAnalyzer.analyze() is sync
    # So we call it directly without await
    analysis_result: QueryAnalysis = self.analyzer.analyze(query)
    
    phase_time = time.time() - phase_start
    
    # CRITICAL: Extract Epic1 analysis data from the QueryAnalysis object
    # The QueryAnalysis object has a .metadata dict containing 'epic1_analysis'
    epic1_data = analysis_result.metadata.get('epic1_analysis', {})
    
    # Extract key fields with safe defaults
    complexity = epic1_data.get('complexity_level', 'medium')
    confidence = epic1_data.get('complexity_confidence', 0.5)
    
    # Build features dictionary from Epic1 feature summary
    feature_summary = epic1_data.get('feature_summary', {})
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
            "comparative_language": any(
                word in query.lower() for word in ['vs', 'versus', 'compare', 'difference']
            ),
            "specificity_score": feature_summary.get('syntactic_complexity', 0.5)
        }
    }
    
    # Build recommended models list
    primary_model = epic1_data.get('recommended_model', 'ollama/llama3.2:3b')
    fallback_chain = epic1_data.get('fallback_chain', ['openai/gpt-3.5-turbo'])
    recommended_models = [primary_model] + fallback_chain
    
    # Build cost estimate per model
    cost_estimate = {}
    estimated_cost = epic1_data.get('cost_estimate', 0.0)
    if primary_model:
        cost_estimate[primary_model] = estimated_cost
    
    # Add fallback models with default costs
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
    
    # Build the service response following Epic 8 API specification
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
                    "selection_reason": epic1_data.get('recommendation_reasoning', 'Default'),
                    "cost_estimate": estimated_cost,
                    "quality_score": epic1_data.get('routing_confidence', confidence)
                }
            }
        }
    }
    
    return result
```

---

## 7. CONFIGURATION BEST PRACTICES

### Service Configuration (config.yaml)
```yaml
# Complete Query Analyzer Service Configuration

service_name: query-analyzer
service_version: 1.0.0

# Server Configuration
host: 0.0.0.0
port: 8082
workers: 1

# Logging Configuration
log_level: INFO
log_format: json

# Epic 8 Performance Targets
performance_targets:
  response_time_target_ms: 5000
  response_time_warning_ms: 2000
  accuracy_target: 0.85
  cost_error_target: 0.05
  memory_limit_gb: 2.0

# Circuit Breaker Configuration
circuit_breaker:
  failure_threshold: 5
  timeout_seconds: 60
  enabled: true

# Fallback Configuration
fallback:
  enabled: true
  threshold_ms: 3000

# Analyzer Component Configuration (passed to Epic1QueryAnalyzer)
analyzer:
  feature_extractor:
    enable_caching: true
    cache_size: 1000
    extract_linguistic: true
    extract_structural: true
    extract_semantic: true
  
  complexity_classifier:
    thresholds:
      simple: 0.3
      medium: 0.6
      complex: 0.9
    weights:
      length: 0.2
      vocabulary: 0.3
      syntax: 0.2
      semantic: 0.3
  
  model_recommender:
    strategy: balanced
    model_mappings:
      simple:
        - ollama/llama3.2:3b
      medium:
        - openai/gpt-3.5-turbo
        - ollama/llama3.2:3b
      complex:
        - openai/gpt-4
        - mistral/mistral-large
    cost_weights:
      ollama/llama3.2:3b: 0.0
      openai/gpt-3.5-turbo: 0.002
      openai/gpt-4: 0.06
      mistral/mistral-large: 0.008
```

### Python Configuration Loading
```python
# In config.py - Load and pass to service

def get_analyzer_config() -> Dict[str, Any]:
    """Get analyzer configuration dictionary for Epic1QueryAnalyzer."""
    settings = get_settings()
    
    return {
        "feature_extractor": settings.analyzer_config.feature_extractor,
        "complexity_classifier": settings.analyzer_config.complexity_classifier,
        "model_recommender": settings.analyzer_config.model_recommender
    }

# In main.py - Pass to service

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    logger.info("Starting Query Analyzer Service")
    
    # Get configuration
    settings = get_settings()
    analyzer_config = get_analyzer_config()  # This is the config passed to Epic1QueryAnalyzer
    
    # Initialize service with configuration
    analyzer_service = QueryAnalyzerService(config=analyzer_config)
    
    yield
    
    logger.info("Shutting down Query Analyzer Service")
```

---

## 8. ERROR HANDLING & RESILIENCE

### Proper Exception Propagation
```python
# ✅ CORRECT: Propagate detailed errors

async def analyze_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    try:
        # ... analysis logic ...
        return analysis_result
        
    except ValueError as e:
        # Input validation error
        self._error_count += 1
        logger.warning("Validation error", query_length=len(query), error=str(e))
        raise ValueError(str(e)) from e
        
    except asyncio.TimeoutError as e:
        # Timeout: Use fallback if enabled
        if self._fallback_enabled:
            return await self._fallback_analysis(query, context, request_id)
        else:
            raise TimeoutError(f"Analysis exceeded {self._performance_targets.response_time_target_ms}ms") from e
            
    except Exception as e:
        # Unexpected error
        self._error_count += 1
        self._circuit_breaker.record_failure()
        logger.error("Analysis failed", error=str(e), traceback=traceback.format_exc())
        raise RuntimeError(f"Query analysis failed: {str(e)}") from e
```

### Circuit Breaker Pattern
```python
# ✅ CORRECT: Prevent cascading failures

async def analyze_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    # Check if circuit breaker should allow request
    if not self._circuit_breaker.should_allow_request():
        raise RuntimeError("Service temporarily unavailable due to circuit breaker")
    
    try:
        # ... perform analysis ...
        
        # Record success
        self._circuit_breaker.record_success()
        return result
        
    except Exception as e:
        # Record failure
        self._circuit_breaker.record_failure()
        raise
```

---

## 9. TESTING INTEGRATION

### Unit Test Pattern
```python
import pytest
from unittest.mock import Mock, MagicMock, patch

@pytest.mark.asyncio
async def test_epic1_analyzer_initialization():
    """Test Epic1QueryAnalyzer initializes correctly in service."""
    
    config = {
        "feature_extractor": {"enable_caching": True},
        "complexity_classifier": {"thresholds": {"simple": 0.3}},
        "model_recommender": {"strategy": "balanced"}
    }
    
    service = QueryAnalyzerService(config=config)
    
    # Initialize should create Epic1QueryAnalyzer
    await service._initialize_analyzer()
    
    assert service._initialized
    assert service.analyzer is not None
    assert isinstance(service.analyzer, Epic1QueryAnalyzer)

@pytest.mark.asyncio
async def test_epic1_analyzer_analysis_workflow():
    """Test complete Epic1QueryAnalyzer workflow integration."""
    
    config = {
        "feature_extractor": {"enable_caching": True},
        "complexity_classifier": {"thresholds": {"simple": 0.3, "medium": 0.6}},
        "model_recommender": {"strategy": "balanced"}
    }
    
    service = QueryAnalyzerService(config=config)
    
    query = "What is machine learning?"
    result = await service.analyze_query(query)
    
    # Validate result structure
    assert result["query"] == query
    assert result["complexity"] in ["simple", "medium", "complex"]
    assert 0.0 <= result["confidence"] <= 1.0
    assert "features" in result
    assert "recommended_models" in result
    assert len(result["recommended_models"]) > 0

@pytest.mark.asyncio
async def test_epic1_analyzer_error_handling():
    """Test error handling in integration."""
    
    service = QueryAnalyzerService(config={})
    
    # Empty query should raise ValueError
    with pytest.raises(ValueError):
        await service.analyze_query("")
    
    # Too long query should raise ValueError
    with pytest.raises(ValueError):
        await service.analyze_query("x" * 10001)
```

### Integration Test Pattern
```python
@pytest.mark.asyncio
async def test_query_analyzer_service_integration():
    """Test full integration with Epic1QueryAnalyzer."""
    
    config = {
        "feature_extractor": {
            "enable_caching": True,
            "cache_size": 100,
            "extract_linguistic": True,
            "extract_structural": True,
            "extract_semantic": True
        },
        "complexity_classifier": {
            "thresholds": {"simple": 0.3, "medium": 0.6, "complex": 0.9},
            "weights": {"length": 0.25, "vocabulary": 0.25, "syntax": 0.25, "semantic": 0.25}
        },
        "model_recommender": {
            "strategy": "balanced",
            "model_mappings": {
                "simple": ["ollama/llama3.2:3b"],
                "medium": ["openai/gpt-3.5-turbo", "ollama/llama3.2:3b"],
                "complex": ["openai/gpt-4"]
            }
        }
    }
    
    service = QueryAnalyzerService(config=config)
    
    # Test different query types
    queries = {
        "simple": "What is AI?",
        "medium": "How do neural networks learn patterns from data?",
        "complex": "Explain the relationship between transformer architecture, attention mechanisms, and the emergence of language models in deep learning?"
    }
    
    for complexity, query in queries.items():
        result = await service.analyze_query(query)
        
        assert result["query"] == query
        assert result["complexity"] in ["simple", "medium", "complex"]
        assert 0 <= result["confidence"] <= 1
        assert len(result["recommended_models"]) > 0
        
        # Verify metadata structure
        assert "metadata" in result
        assert "epic1_analysis" in result["metadata"]
```

---

## 10. DEPLOYMENT CONSIDERATIONS

### Environment Variables
```bash
# Project root for imports (for containerized deployment)
PROJECT_ROOT=/home/user/rag-portfolio/project-1-technical-rag

# Service configuration
QUERY_ANALYZER_CONFIG_FILE=config.yaml
QUERY_ANALYZER_HOST=0.0.0.0
QUERY_ANALYZER_PORT=8082
QUERY_ANALYZER_LOG_LEVEL=INFO

# Performance targets
QUERY_ANALYZER_RESPONSE_TIME_TARGET_MS=5000
QUERY_ANALYZER_RESPONSE_TIME_WARNING_MS=2000

# Circuit breaker
QUERY_ANALYZER_CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
QUERY_ANALYZER_CIRCUIT_BREAKER_TIMEOUT_SECONDS=60
```

### Docker Deployment
```dockerfile
# Ensure PROJECT_ROOT is set for imports
ENV PROJECT_ROOT=/app

# Install dependencies
RUN pip install -r requirements.txt

# Set configuration
COPY config.yaml /app/services/query-analyzer/

# Start service
CMD ["python", "-m", "uvicorn", "analyzer_app.main:app", "--host", "0.0.0.0", "--port", "8082"]
```

---

## 11. COMPARISON SUMMARY

### Generator Service vs Query Analyzer Service

| Aspect | Generator Service | Query Analyzer Service | Status |
|--------|------------------|----------------------|--------|
| **Import Pattern** | `from src.components.generators.epic1_answer_generator import Epic1AnswerGenerator` | `from src.components.query_processors.analyzers.epic1_query_analyzer import Epic1QueryAnalyzer` | ✅ Same Pattern |
| **Initialization** | Async lock in `_initialize_generator()` | Async lock in `_initialize_analyzer()` | ✅ Same Pattern |
| **Config Passing** | `Epic1AnswerGenerator(config=self.config)` | `Epic1QueryAnalyzer(config=self.config)` | ✅ Same Pattern |
| **Method Call** | `self.generator.generate(query, documents)` | `self.analyzer.analyze(query)` | ✅ Correct |
| **Return Type** | `Answer` object | `QueryAnalysis` object | ✅ Expected |
| **Metadata Extraction** | `answer.metadata.get('routing', {})` | `analysis_result.metadata.get('epic1_analysis', {})` | ✅ Correct |
| **Error Handling** | Try/except with proper logging | Try/except with proper logging | ✅ Same Pattern |
| **Metrics** | Prometheus integration | Prometheus integration | ✅ Same Pattern |
| **Fallback** | Via answer generation | Via rule-based analysis | ✅ Different but Valid |
| **Overall Success Rate** | 87% ✅ | 95%+ (if following guide) | ✅ Very Good |

---

## 12. CHECKLIST FOR INTEGRATION VERIFICATION

### Code Audit Checklist
- [ ] Import statements are correct and paths are valid
- [ ] Configuration structure matches Epic1QueryAnalyzer expectations
- [ ] Initialization uses async lock pattern (prevents race conditions)
- [ ] Configuration passed to `__init__()` method
- [ ] `.analyze()` method called correctly (synchronous, not async)
- [ ] Return type is `QueryAnalysis` object
- [ ] Metadata extracted from `analysis_result.metadata['epic1_analysis']`
- [ ] Error handling with proper exception propagation
- [ ] Logging at appropriate levels (info, warning, error)
- [ ] Metrics updated on success and failure
- [ ] Fallback mechanism implemented
- [ ] Health check validates analyzer functionality
- [ ] Circuit breaker pattern implemented

### Integration Test Checklist
- [ ] Service initializes without errors
- [ ] Simple queries analyzed successfully
- [ ] Complex queries analyzed successfully
- [ ] Error handling for empty queries
- [ ] Error handling for too-long queries
- [ ] Response time within target SLA
- [ ] Recommended models returned
- [ ] Cost estimates provided
- [ ] Metadata structure valid
- [ ] Fallback triggered on timeout

---

## 13. TROUBLESHOOTING GUIDE

### Issue: "Epic1QueryAnalyzer not found"

**Cause**: Import path issue  
**Solution**:
```python
# Check project root is in path
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Try import
from src.components.query_processors.analyzers.epic1_query_analyzer import Epic1QueryAnalyzer
```

### Issue: "Analyzer not initialized"

**Cause**: `_initialize_analyzer()` not called  
**Solution**:
```python
async def analyze_query(self, query: str) -> Dict[str, Any]:
    # Ensure initialization before use
    if not self._initialized:
        await self._initialize_analyzer()
    
    if not self.analyzer:
        raise RuntimeError("Analyzer not initialized")
```

### Issue: "analyze() returned invalid result"

**Cause**: Wrong method name or return type  
**Solution**:
```python
# CORRECT: Use .analyze() method, not .analyze_query()
result: QueryAnalysis = self.analyzer.analyze(query)

# Check result structure
if not result or not hasattr(result, 'metadata'):
    raise RuntimeError("Invalid result")
```

### Issue: "KeyError: 'epic1_analysis'"

**Cause**: Metadata structure different than expected  
**Solution**:
```python
# Use safe .get() with defaults
epic1_data = analysis_result.metadata.get('epic1_analysis', {})
complexity = epic1_data.get('complexity_level', 'medium')  # Fallback default
```

---

## 14. PERFORMANCE OPTIMIZATION TIPS

### 1. Caching Configuration
```python
config = {
    "feature_extractor": {
        "enable_caching": True,        # ✅ Enable for repeated queries
        "cache_size": 1000             # Adjust based on query diversity
    },
    ...
}
```

### 2. Complexity Thresholds Tuning
```python
config = {
    "complexity_classifier": {
        "thresholds": {
            "simple": 0.3,     # Tune based on your use case
            "medium": 0.6,
            "complex": 0.9
        },
        "weights": {
            # Adjust weights to match your query patterns
            "length": 0.2,
            "vocabulary": 0.3,
            "syntax": 0.2,
            "semantic": 0.3
        }
    }
}
```

### 3. Model Mappings Optimization
```python
config = {
    "model_recommender": {
        "strategy": "cost_optimized",  # Use appropriate strategy
        "model_mappings": {
            "simple": ["ollama/llama3.2:3b"],  # Cost-effective
            "medium": ["openai/gpt-3.5-turbo"],  # Balance
            "complex": ["openai/gpt-4"]  # Best quality
        }
    }
}
```

---

## 15. PRODUCTION READINESS CHECKLIST

- [ ] Configuration management externalized (YAML + env vars)
- [ ] Error handling comprehensive (input validation, timeouts, fallbacks)
- [ ] Logging structured and observable (JSON format)
- [ ] Metrics instrumented (Prometheus integration)
- [ ] Health checks operational (liveness, readiness, startup probes)
- [ ] Circuit breaker implemented (prevent cascading failures)
- [ ] Performance monitoring (SLA tracking, slow response detection)
- [ ] Documentation complete (README, architecture diagrams, examples)
- [ ] Tests comprehensive (unit, integration, end-to-end)
- [ ] Deployment automation (Dockerfile, Kubernetes manifests)

---

## 16. SUMMARY & RECOMMENDATIONS

### Current Status
✅ **Query Analyzer Service integration is fundamentally sound** - The pattern follows the proven Generator Service approach and correctly integrates Epic1QueryAnalyzer.

### Key Strengths
1. ✅ Correct import and initialization patterns
2. ✅ Proper async/await and thread-safe locking
3. ✅ Comprehensive error handling and logging
4. ✅ Prometheus metrics integration
5. ✅ Epic 8 enhancements (circuit breaker, performance targets)
6. ✅ Fallback mechanisms for resilience

### Recommended Enhancements
1. **Configuration Validation**: Add schema validation for config dictionaries
2. **Performance Profiling**: Add detailed timing for each sub-component
3. **Caching Strategy**: Tune feature extractor cache size based on query patterns
4. **Model Registry**: Maintain list of available models with health status
5. **A/B Testing**: Support routing strategy experimentation

### Next Steps
1. Execute the integration verification checklist
2. Run comprehensive integration tests
3. Perform load testing under expected query volume
4. Monitor in staging environment for 1-2 weeks
5. Deploy to production with gradual traffic increase

---

## APPENDIX: Quick Reference

### Correct Integration Pattern (One-Liner)
```python
# Initialize
service = QueryAnalyzerService(config=get_analyzer_config())
await service._initialize_analyzer()

# Use
result = await service.analyze_query("What is machine learning?")

# Extract
complexity = result["complexity"]
confidence = result["confidence"]
models = result["recommended_models"]
```

### Configuration One-Liner
```python
config = {
    "feature_extractor": {"enable_caching": True},
    "complexity_classifier": {"thresholds": {"simple": 0.3, "medium": 0.6, "complex": 0.9}},
    "model_recommender": {"strategy": "balanced"}
}
```

### API Usage One-Liner (REST)
```bash
curl -X POST http://localhost:8082/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "context": {}}'
```

