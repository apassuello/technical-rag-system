# Epic 1 Multi-Model API Reference

**Version**: 1.0  
**Last Updated**: August 6, 2025  
**Status**: Production Ready

This document provides comprehensive API documentation for the Epic 1 multi-model routing system, including all classes, methods, configuration options, and usage examples.

---

## Table of Contents

1. [Core Components](#1-core-components)
2. [LLM Adapters](#2-llm-adapters)
3. [Routing System](#3-routing-system)
4. [Cost Tracking](#4-cost-tracking)
5. [Configuration Schema](#5-configuration-schema)
6. [Usage Examples](#6-usage-examples)
7. [Error Handling](#7-error-handling)

---

## 1. Core Components

### 1.1 Epic1AnswerGenerator

**Location**: `src.components.generators.epic1_answer_generator`

The main entry point for multi-model answer generation with intelligent routing.

#### Class Definition

```python
class Epic1AnswerGenerator(AnswerGenerator):
    """
    Epic 1 enhanced answer generator with multi-model routing.
    
    Provides intelligent LLM selection based on query complexity analysis
    with comprehensive cost tracking and optimization.
    """
```

#### Constructor

```python
def __init__(self,
             config: Optional[Dict[str, Any]] = None,
             # Legacy parameters for backward compatibility
             model_name: Optional[str] = None,
             temperature: Optional[float] = None,
             max_tokens: Optional[int] = None,
             use_ollama: Optional[bool] = None,
             ollama_url: Optional[str] = None,
             **kwargs) -> None
```

**Parameters**:
- `config`: Complete configuration dictionary for multi-model setup
- `model_name`: Legacy parameter for single-model mode (triggers backward compatibility)
- `temperature`: Generation temperature (0.0-1.0)
- `max_tokens`: Maximum tokens to generate
- `use_ollama`: Legacy parameter to force Ollama usage
- `ollama_url`: Custom Ollama endpoint URL
- `**kwargs`: Additional configuration parameters

#### Methods

##### generate()

```python
def generate(self, query: str, context: List[Document]) -> Answer:
    """
    Generate answer using adaptive multi-model routing.
    
    Args:
        query: User query string
        context: List of relevant context documents
        
    Returns:
        Answer object with routing metadata
        
    Raises:
        ValueError: If query is empty or context is invalid
        GenerationError: If answer generation fails
    """
```

**Usage Example**:
```python
from src.components.generators import Epic1AnswerGenerator

# Initialize with multi-model routing
generator = Epic1AnswerGenerator({
    "routing": {
        "enabled": True,
        "default_strategy": "balanced"
    }
})

# Generate answer with intelligent routing
answer = generator.generate(
    query="How does distributed consensus work?",
    context=retrieved_documents
)

# Access routing information
routing_info = answer.metadata['routing']
print(f"Selected model: {routing_info['selected_model']['model']}")
print(f"Cost: ${routing_info['selected_model']['estimated_cost']:.4f}")
```

##### get_generator_info()

```python
def get_generator_info(self) -> Dict[str, Any]:
    """
    Get comprehensive generator information including routing stats.
    
    Returns:
        Dictionary with configuration, capabilities, and metrics
    """
```

**Response Structure**:
```python
{
    "type": "epic1",
    "routing_enabled": True,
    "epic1_available": True,
    "routing_stats": {
        "total_routing_decisions": 150,
        "avg_routing_time_ms": 12.5,
        "strategy_usage": {
            "balanced": {"count": 120, "percentage": 80.0},
            "cost_optimized": {"count": 30, "percentage": 20.0}
        }
    },
    "cost_summary_24h": {
        "total_requests": 150,
        "total_cost_usd": 0.125000,
        "avg_cost_per_request": 0.000833
    }
}
```

##### get_routing_statistics()

```python
def get_routing_statistics(self) -> Dict[str, Any]:
    """
    Get detailed routing performance statistics.
    
    Returns:
        Dictionary with routing metrics and analytics
    """
```

##### get_cost_breakdown()

```python
def get_cost_breakdown(self) -> Optional[Dict[str, Any]]:
    """
    Get detailed cost breakdown across all models.
    
    Returns:
        Cost analysis dictionary or None if tracking disabled
    """
```

**Response Structure**:
```python
{
    "total_cost": 0.125000,
    "cost_by_provider": {
        "openai": 0.075000,
        "mistral": 0.025000,
        "ollama": 0.000000
    },
    "cost_by_model": {
        "openai/gpt-4-turbo": 0.075000,
        "mistral/mistral-small": 0.025000,
        "ollama/llama3.2:3b": 0.000000
    },
    "cost_by_complexity": {
        "simple": 0.000000,
        "medium": 0.025000,
        "complex": 0.100000
    },
    "optimization_recommendations": [
        {
            "type": "cost_optimization",
            "priority": "medium",
            "suggestion": "Consider routing medium queries to Mistral"
        }
    ]
}
```

---

## 2. LLM Adapters

### 2.1 OpenAI Adapter

**Location**: `src.components.generators.llm_adapters.openai_adapter`

#### Class Definition

```python
class OpenAIAdapter(BaseLLMAdapter):
    """
    OpenAI LLM adapter with GPT-3.5-turbo and GPT-4-turbo support.
    
    Features:
    - Precise token counting and cost tracking
    - Streaming response support
    - Comprehensive error handling
    - Rate limit management
    """
```

#### Constructor

```python
def __init__(self,
             model_name: str = "gpt-3.5-turbo",
             api_key: Optional[str] = None,
             base_url: Optional[str] = None,
             organization: Optional[str] = None,
             config: Optional[Dict[str, Any]] = None,
             max_retries: int = 3,
             retry_delay: float = 1.0,
             timeout: float = 30.0) -> None
```

**Parameters**:
- `model_name`: OpenAI model name ("gpt-3.5-turbo", "gpt-4-turbo", "gpt-4o-mini")
- `api_key`: OpenAI API key (or set `OPENAI_API_KEY` environment variable)
- `base_url`: Custom API base URL (optional)
- `organization`: OpenAI organization ID (optional)
- `config`: Additional configuration parameters
- `max_retries`: Maximum retry attempts for failed requests
- `retry_delay`: Initial delay between retries
- `timeout`: Request timeout in seconds

#### Methods

##### generate()

```python
def generate(self, prompt: str, params: GenerationParams) -> str:
    """
    Generate response using OpenAI API.
    
    Args:
        prompt: Input prompt text
        params: Generation parameters
        
    Returns:
        Generated text response
        
    Raises:
        RateLimitError: If rate limit exceeded
        AuthenticationError: If API key invalid
        ModelNotFoundError: If model doesn't exist
        LLMError: For other API errors
    """
```

##### generate_streaming()

```python
def generate_streaming(self, prompt: str, params: GenerationParams) -> Iterator[str]:
    """
    Generate streaming response from OpenAI.
    
    Args:
        prompt: Input prompt text
        params: Generation parameters
        
    Yields:
        Text chunks as they arrive
    """
```

##### get_cost_breakdown()

```python
def get_cost_breakdown(self) -> Dict[str, Any]:
    """
    Get detailed cost breakdown for this adapter.
    
    Returns:
        Dictionary with cost information and token usage
    """
```

**Response Structure**:
```python
{
    "model": "gpt-4-turbo",
    "total_requests": 25,
    "input_tokens": 5000,
    "output_tokens": 2500,
    "total_tokens": 7500,
    "input_cost_usd": 0.050000,
    "output_cost_usd": 0.075000,
    "total_cost_usd": 0.125000,
    "avg_cost_per_request": 0.005000,
    "pricing_per_1k": {
        "input": 0.01,
        "output": 0.03
    }
}
```

#### Configuration Example

```python
from src.components.generators.llm_adapters import OpenAIAdapter

# Basic setup
adapter = OpenAIAdapter(
    model_name="gpt-4-turbo",
    api_key="sk-...",  # or set OPENAI_API_KEY env var
    timeout=30.0
)

# Advanced configuration
adapter = OpenAIAdapter(
    model_name="gpt-3.5-turbo",
    organization="org-...",  # optional
    config={
        "temperature": 0.7,
        "max_tokens": 1000,
        "frequency_penalty": 0.1
    }
)
```

### 2.2 Mistral Adapter

**Location**: `src.components.generators.llm_adapters.mistral_adapter`

#### Class Definition

```python
class MistralAdapter(BaseLLMAdapter):
    """
    Mistral AI adapter for cost-effective inference.
    
    Features:
    - Support for all Mistral models
    - HTTP-based API integration
    - Per-million token pricing
    - Comprehensive error handling
    """
```

#### Constructor

```python
def __init__(self,
             model_name: str = "mistral-small",
             api_key: Optional[str] = None,
             base_url: Optional[str] = None,
             config: Optional[Dict[str, Any]] = None,
             max_retries: int = 3,
             retry_delay: float = 1.0,
             timeout: float = 30.0) -> None
```

**Parameters**:
- `model_name`: Mistral model ("mistral-small", "mistral-medium", "mistral-large")
- `api_key`: Mistral API key (or set `MISTRAL_API_KEY` environment variable)
- `base_url`: API base URL (defaults to "https://api.mistral.ai/v1")
- `config`: Additional configuration parameters
- `max_retries`: Maximum retry attempts
- `retry_delay`: Initial retry delay
- `timeout`: Request timeout

#### Configuration Example

```python
from src.components.generators.llm_adapters import MistralAdapter

# Basic setup
adapter = MistralAdapter(
    model_name="mistral-small",
    api_key="your-mistral-key",  # or set MISTRAL_API_KEY
    timeout=30.0
)

# With custom configuration
adapter = MistralAdapter(
    model_name="mistral-medium",
    config={
        "temperature": 0.8,
        "max_tokens": 1500,
        "top_p": 0.9
    }
)
```

---

## 3. Routing System

### 3.1 AdaptiveRouter

**Location**: `src.components.generators.routing.adaptive_router`

#### Class Definition

```python
class AdaptiveRouter:
    """
    Adaptive router for intelligent multi-model LLM selection.
    
    Orchestrates query complexity analysis, strategy selection,
    and model routing decisions with comprehensive tracking.
    """
```

#### Constructor

```python
def __init__(self,
             default_strategy: str = "balanced",
             query_analyzer: Optional['Epic1QueryAnalyzer'] = None,
             config: Optional[Dict[str, Any]] = None,
             enable_fallback: bool = True,
             enable_cost_tracking: bool = True) -> None
```

**Parameters**:
- `default_strategy`: Default routing strategy ("cost_optimized", "quality_first", "balanced")
- `query_analyzer`: Epic1QueryAnalyzer instance for complexity analysis
- `config`: Router configuration dictionary
- `enable_fallback`: Whether to enable fallback chain management
- `enable_cost_tracking`: Whether to track routing costs

#### Methods

##### route_query()

```python
def route_query(self,
                query: str,
                query_metadata: Optional[Dict[str, Any]] = None,
                strategy_override: Optional[str] = None,
                context_documents: Optional[List] = None) -> RoutingDecision
```

**Args**:
- `query`: User query to route
- `query_metadata`: Additional query metadata
- `strategy_override`: Override default strategy for this query
- `context_documents`: Context documents for the query

**Returns**: `RoutingDecision` object with comprehensive routing information

**Usage Example**:
```python
from src.components.generators.routing import AdaptiveRouter

# Initialize router
router = AdaptiveRouter(
    default_strategy="balanced",
    enable_fallback=True,
    enable_cost_tracking=True
)

# Route a query
decision = router.route_query(
    query="Explain microservices architecture",
    query_metadata={"source": "user_input"},
    strategy_override="quality_first"  # Force high-quality model
)

# Access routing results
print(f"Selected: {decision.selected_model.provider}/{decision.selected_model.model}")
print(f"Complexity: {decision.complexity_level}")
print(f"Decision time: {decision.decision_time_ms:.1f}ms")
print(f"Estimated cost: ${decision.selected_model.estimated_cost:.4f}")
```

##### get_routing_stats()

```python
def get_routing_stats(self) -> Dict[str, Any]:
    """
    Get comprehensive routing statistics.
    
    Returns:
        Dictionary with performance and usage statistics
    """
```

**Response Structure**:
```python
{
    "total_decisions": 500,
    "avg_decision_time_ms": 15.2,
    "strategy_usage": {
        "balanced": {"count": 350, "percentage": 70.0},
        "cost_optimized": {"count": 100, "percentage": 20.0},
        "quality_first": {"count": 50, "percentage": 10.0}
    },
    "recent_complexity_distribution": {
        "simple": 40,
        "medium": 35,
        "complex": 25
    },
    "recent_provider_distribution": {
        "ollama": 40,
        "mistral": 35,
        "openai": 25
    }
}
```

### 3.2 RoutingDecision

**Location**: `src.components.generators.routing.adaptive_router`

#### Class Definition

```python
class RoutingDecision:
    """
    Comprehensive routing decision with metadata.
    
    Contains all information about a routing decision including
    the selected model, reasoning, and performance metrics.
    """
```

#### Attributes

```python
selected_model: ModelOption          # The chosen model
strategy_used: str                   # Strategy name used
query_complexity: float              # Complexity score (0.0-1.0)
complexity_level: str                # Level (simple/medium/complex)
decision_time_ms: float              # Time to make decision
alternatives_considered: List[ModelOption]  # Other options considered
routing_metadata: Dict[str, Any]     # Additional metadata
timestamp: float                     # Unix timestamp
```

#### Methods

##### to_dict()

```python
def to_dict(self) -> Dict[str, Any]:
    """Convert routing decision to dictionary for serialization."""
```

### 3.3 Routing Strategies

#### 3.3.1 CostOptimizedStrategy

**Location**: `src.components.generators.routing.routing_strategies`

```python
class CostOptimizedStrategy(RoutingStrategy):
    """
    Cost-optimized routing strategy.
    
    Prioritizes cost minimization while maintaining acceptable quality.
    Expected cost reduction: 50-70% vs premium models.
    """
```

**Configuration**:
```python
strategy = CostOptimizedStrategy({
    "simple_threshold": 0.35,
    "complex_threshold": 0.75,
    "max_cost_per_query": 0.010
})
```

#### 3.3.2 QualityFirstStrategy

```python
class QualityFirstStrategy(RoutingStrategy):
    """
    Quality-first routing strategy.
    
    Prioritizes response quality over cost considerations.
    Expected cost increase: 30-50% vs balanced approach.
    """
```

**Configuration**:
```python
strategy = QualityFirstStrategy({
    "simple_threshold": 0.40,
    "complex_threshold": 0.70,
    "min_quality_score": 0.85
})
```

#### 3.3.3 BalancedStrategy

```python
class BalancedStrategy(RoutingStrategy):
    """
    Balanced routing strategy.
    
    Optimizes cost/quality tradeoff using weighted scoring.
    Expected cost reduction: 25-40% with minimal quality loss.
    """
```

**Configuration**:
```python
strategy = BalancedStrategy({
    "simple_threshold": 0.35,
    "complex_threshold": 0.70,
    "cost_weight": 0.4,        # 40% cost consideration
    "quality_weight": 0.6,     # 60% quality consideration
    "max_cost_per_query": 0.020
})
```

---

## 4. Cost Tracking

### 4.1 CostTracker

**Location**: `src.components.generators.llm_adapters.cost_tracker`

#### Class Definition

```python
class CostTracker:
    """
    Centralized cost tracking system with $0.001 precision.
    
    Features:
    - Real-time cost calculation
    - Usage aggregation by multiple dimensions
    - Cost optimization recommendations
    - Thread-safe concurrent access
    - Export capabilities
    """
```

#### Constructor

```python
def __init__(self,
             precision_places: int = 6,
             enable_detailed_logging: bool = True) -> None
```

#### Methods

##### record_usage()

```python
def record_usage(self,
                 provider: str,
                 model: str,
                 input_tokens: int,
                 output_tokens: int,
                 cost_usd: Decimal,
                 query_complexity: Optional[str] = None,
                 request_time_ms: Optional[float] = None,
                 success: bool = True,
                 metadata: Optional[Dict[str, Any]] = None) -> None
```

**Usage Example**:
```python
from src.components.generators.llm_adapters.cost_tracker import get_cost_tracker

# Get global cost tracker instance
tracker = get_cost_tracker()

# Record LLM usage
tracker.record_usage(
    provider="openai",
    model="gpt-4-turbo",
    input_tokens=150,
    output_tokens=75,
    cost_usd=Decimal('0.006750'),
    query_complexity="complex",
    request_time_ms=850.0,
    success=True,
    metadata={"user_id": "user123", "session_id": "sess456"}
)
```

##### get_total_cost()

```python
def get_total_cost(self) -> Decimal:
    """Get total cost across all providers with high precision."""
```

##### get_cost_by_provider()

```python
def get_cost_by_provider(self) -> Dict[str, Decimal]:
    """Get cost breakdown by provider."""
```

##### get_cost_by_complexity()

```python
def get_cost_by_complexity(self) -> Dict[str, Decimal]:
    """Get cost breakdown by query complexity level."""
```

##### get_summary_by_time_period()

```python
def get_summary_by_time_period(self, hours: int = 24) -> CostSummary:
    """Get usage summary for the last N hours."""
```

**Response Structure** (`CostSummary`):
```python
{
    "total_requests": 150,
    "total_input_tokens": 15000,
    "total_output_tokens": 7500,
    "total_cost_usd": Decimal('0.125000'),
    "avg_cost_per_request": Decimal('0.000833'),
    "avg_request_time_ms": 650.5,
    "success_rate": 0.98
}
```

##### get_cost_optimization_recommendations()

```python
def get_cost_optimization_recommendations(self) -> List[Dict[str, Any]]:
    """Generate AI-driven cost optimization recommendations."""
```

**Response Structure**:
```python
[
    {
        "type": "cost_optimization",
        "priority": "high",
        "title": "High cost on simple queries",
        "description": "45.2% of costs from simple queries",
        "suggestion": "Route simple queries to Ollama (free)",
        "potential_savings": "$0.125"
    },
    {
        "type": "provider_optimization", 
        "priority": "medium",
        "title": "High OpenAI usage detected",
        "description": "75.0% of costs from OpenAI",
        "suggestion": "Consider Mistral for medium complexity queries",
        "potential_savings": "$0.075"
    }
]
```

##### export_usage_data()

```python
def export_usage_data(self,
                      format_type: str = 'json',
                      include_metadata: bool = False) -> str:
    """Export usage data in JSON or CSV format."""
```

### 4.2 Convenience Functions

#### record_llm_usage()

```python
def record_llm_usage(provider: str,
                     model: str,
                     input_tokens: int,
                     output_tokens: int,
                     cost_usd: Decimal,
                     query_complexity: Optional[str] = None,
                     request_time_ms: Optional[float] = None,
                     success: bool = True,
                     metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Convenience function to record LLM usage in global tracker.
    """
```

#### get_cost_tracker()

```python
def get_cost_tracker() -> CostTracker:
    """Get the global cost tracker instance."""
```

---

## 5. Configuration Schema

### 5.1 Complete Epic 1 Configuration

**File**: `config/epic1_multi_model.yaml`

#### 5.1.1 Answer Generator Configuration

```yaml
answer_generator:
  type: "epic1"
  config:
    # Multi-model routing
    routing:
      enabled: true
      default_strategy: "balanced"  # cost_optimized | quality_first | balanced
      
      # Query complexity analyzer
      query_analyzer:
        type: "epic1"
        config:
          complexity_classifier:
            thresholds:
              simple_threshold: 0.35
              complex_threshold: 0.70
      
      # Strategy configurations
      strategies:
        cost_optimized:
          max_cost_per_query: 0.010
        quality_first:
          min_quality_score: 0.85
        balanced:
          cost_weight: 0.4
          quality_weight: 0.6
    
    # Model mappings
    models:
      simple:
        primary:
          provider: "ollama"
          model: "llama3.2:3b"
          max_cost_per_query: 0.000
      medium:
        primary:
          provider: "mistral"
          model: "mistral-small"
          max_cost_per_query: 0.005
      complex:
        primary:
          provider: "openai"
          model: "gpt-4-turbo"
          max_cost_per_query: 0.050
    
    # Fallback configuration
    fallback:
      enabled: true
      fallback_chain: ["mistral/mistral-small", "ollama/llama3.2:3b"]
    
    # Cost tracking
    cost_tracking:
      enabled: true
      precision_places: 6
      daily_budget_usd: 10.00
      alert_threshold: 0.8
```

#### 5.1.2 Provider Configurations

```yaml
providers:
  ollama:
    base_url: "http://localhost:11434"
    timeout: 120
    models: ["llama3.2:3b", "llama3.1:8b"]
    
  openai:
    base_url: "https://api.openai.com/v1"
    timeout: 30
    organization: "${OPENAI_ORG_ID}"  # Optional
    models: ["gpt-3.5-turbo", "gpt-4-turbo"]
    
  mistral:
    base_url: "https://api.mistral.ai/v1"
    timeout: 30
    models: ["mistral-small", "mistral-medium", "mistral-large"]
```

#### 5.1.3 Environment Variables

```yaml
api_keys:
  openai_api_key: "${OPENAI_API_KEY}"
  mistral_api_key: "${MISTRAL_API_KEY}"
```

### 5.2 Programmatic Configuration

#### 5.2.1 Basic Multi-Model Setup

```python
config = {
    "routing": {
        "enabled": True,
        "default_strategy": "balanced"
    },
    "cost_tracking": {
        "enabled": True,
        "daily_budget_usd": 5.00
    }
}

generator = Epic1AnswerGenerator(config=config)
```

#### 5.2.2 Cost-Optimized Configuration

```python
config = {
    "routing": {
        "enabled": True,
        "default_strategy": "cost_optimized",
        "strategies": {
            "cost_optimized": {
                "max_cost_per_query": 0.005  # $0.005 max per query
            }
        }
    }
}

generator = Epic1AnswerGenerator(config=config)
```

#### 5.2.3 Quality-First Configuration

```python
config = {
    "routing": {
        "enabled": True,
        "default_strategy": "quality_first",
        "strategies": {
            "quality_first": {
                "min_quality_score": 0.90  # Minimum 90% quality
            }
        }
    }
}

generator = Epic1AnswerGenerator(config=config)
```

---

## 6. Usage Examples

### 6.1 Basic Multi-Model Usage

```python
from src.components.generators import Epic1AnswerGenerator
from src.core.interfaces import Document

# Initialize Epic 1 generator
generator = Epic1AnswerGenerator({
    "routing": {
        "enabled": True,
        "default_strategy": "balanced"
    }
})

# Prepare context documents
context_docs = [
    Document(content="Microservices are...", metadata={"source": "article1"}),
    Document(content="Distributed systems require...", metadata={"source": "article2"})
]

# Generate answer with intelligent routing
answer = generator.generate(
    query="What are the benefits of microservices architecture?",
    context=context_docs
)

# Access answer
print(f"Answer: {answer.text}")
print(f"Confidence: {answer.confidence:.2f}")
print(f"Sources: {len(answer.sources)}")

# Access routing information
routing = answer.metadata['routing']
print(f"Selected model: {routing['selected_model']['provider']}/{routing['selected_model']['model']}")
print(f"Query complexity: {routing['complexity_level']}")
print(f"Estimated cost: ${routing['selected_model']['estimated_cost']:.4f}")
print(f"Routing time: {routing['routing_decision_time_ms']:.1f}ms")
```

### 6.2 Cost Monitoring and Analytics

```python
# Get comprehensive generator information
info = generator.get_generator_info()
print(f"Total routing decisions: {info['routing_stats']['total_decisions']}")
print(f"Average routing time: {info['routing_stats']['avg_decision_time_ms']:.1f}ms")

# Get detailed cost breakdown
cost_breakdown = generator.get_cost_breakdown()
if cost_breakdown:
    print(f"Total cost: ${cost_breakdown['total_cost']:.6f}")
    print("Cost by provider:")
    for provider, cost in cost_breakdown['cost_by_provider'].items():
        print(f"  {provider}: ${cost:.6f}")
    
    print("Cost optimization recommendations:")
    for rec in cost_breakdown['optimization_recommendations']:
        print(f"  {rec['priority']}: {rec['suggestion']}")
```

### 6.3 Strategy Override Usage

```python
# Force cost-optimized routing for a specific query
cost_optimized_answer = generator.generate(
    query="Simple factual question",
    context=context_docs,
    strategy_override="cost_optimized"  # This would be passed to routing
)

# Force quality-first routing for complex technical query
quality_answer = generator.generate(
    query="Complex technical implementation details",
    context=context_docs,
    strategy_override="quality_first"
)
```

### 6.4 Batch Processing with Cost Tracking

```python
from src.components.generators.llm_adapters.cost_tracker import get_cost_tracker

# Process multiple queries and track costs
queries = [
    "What is Python?",  # Simple
    "How does HTTP work?",  # Medium
    "Explain distributed consensus algorithms"  # Complex
]

tracker = get_cost_tracker()
initial_cost = tracker.get_total_cost()

answers = []
for query in queries:
    answer = generator.generate(query, context_docs)
    answers.append(answer)

final_cost = tracker.get_total_cost()
batch_cost = final_cost - initial_cost

print(f"Batch processing cost: ${batch_cost:.6f}")
print(f"Average cost per query: ${batch_cost/len(queries):.6f}")

# Get cost summary for last hour
summary = tracker.get_summary_by_time_period(hours=1)
print(f"Last hour: {summary.total_requests} requests, ${summary.total_cost_usd:.6f}")
```

### 6.5 Custom Routing Strategy

```python
from src.components.generators.routing.routing_strategies import RoutingStrategy, ModelOption

class CustomStrategy(RoutingStrategy):
    def select_model(self, query_complexity, complexity_level, query_metadata=None):
        # Custom routing logic
        if "urgent" in query_metadata.get("tags", []):
            # Use fastest model for urgent queries
            return ModelOption(
                provider="openai",
                model="gpt-3.5-turbo",
                estimated_cost=Decimal('0.002'),
                estimated_quality=0.90,
                estimated_latency_ms=800
            )
        else:
            # Use balanced approach for normal queries
            return self._balanced_selection(query_complexity)

# Register and use custom strategy
custom_router = AdaptiveRouter(
    default_strategy="custom",
    config={"custom": CustomStrategy()}
)
```

### 6.6 Integration with Component Factory

```python
from src.core.component_factory import ComponentFactory

# Create Epic 1 generator through component factory
generator = ComponentFactory.create_answer_generator(
    "epic1",
    config={
        "routing": {"enabled": True},
        "cost_tracking": {"enabled": True}
    }
)

# Generator is now ready for use
answer = generator.generate(query, context_docs)
```

---

## 7. Error Handling

### 7.1 Exception Hierarchy

```python
# Base exceptions
class GenerationError(Exception):
    """Base exception for answer generation errors."""

class LLMError(Exception):
    """Base exception for LLM adapter errors."""

# Specific exceptions
class RateLimitError(LLMError):
    """Rate limit exceeded."""

class AuthenticationError(LLMError):
    """Authentication failed."""

class ModelNotFoundError(LLMError):
    """Model not found."""

class RoutingError(GenerationError):
    """Routing decision failed."""
```

### 7.2 Error Handling Examples

#### 7.2.1 API Key Issues

```python
try:
    generator = Epic1AnswerGenerator({
        "routing": {"enabled": True}
    })
    answer = generator.generate(query, context)
except AuthenticationError as e:
    print(f"API key issue: {e}")
    # Handle authentication error
    # - Check environment variables
    # - Verify API key validity
    # - Use fallback provider
```

#### 7.2.2 Rate Limit Handling

```python
try:
    answer = generator.generate(query, context)
except RateLimitError as e:
    print(f"Rate limit hit: {e}")
    # Automatic retry with exponential backoff
    # Falls back to alternative providers
    time.sleep(60)  # Wait before retry
    answer = generator.generate(query, context)
```

#### 7.2.3 Model Availability Issues

```python
try:
    answer = generator.generate(query, context)
except ModelNotFoundError as e:
    print(f"Model not available: {e}")
    # Automatic fallback to alternative models
    # Epic 1 handles this automatically via fallback chains
```

#### 7.2.4 Cost Budget Exceeded

```python
from decimal import Decimal

# Set up cost tracking with budget
config = {
    "routing": {"enabled": True},
    "cost_tracking": {
        "enabled": True,
        "daily_budget_usd": 1.00  # $1 daily limit
    }
}

generator = Epic1AnswerGenerator(config=config)

# Monitor costs during generation
try:
    answer = generator.generate(query, context)
    
    # Check if approaching budget
    cost_breakdown = generator.get_cost_breakdown()
    if cost_breakdown:
        daily_cost = cost_breakdown['total_cost']
        if daily_cost > 0.80:  # 80% of budget
            print("Warning: Approaching daily cost budget")
            
except Exception as e:
    if "budget exceeded" in str(e):
        print("Daily budget exceeded, switching to free models")
        # Epic 1 automatically falls back to Ollama
```

### 7.3 Logging and Debugging

#### 7.3.1 Enable Debug Logging

```python
import logging

# Enable debug logging for Epic 1 components
logging.basicConfig(level=logging.DEBUG)

# Or configure specific loggers
epic1_logger = logging.getLogger('src.components.generators')
epic1_logger.setLevel(logging.DEBUG)

router_logger = logging.getLogger('src.components.generators.routing')
router_logger.setLevel(logging.DEBUG)
```

#### 7.3.2 Access Routing Decision Details

```python
# Get detailed routing information from answer metadata
answer = generator.generate(query, context)
routing_metadata = answer.metadata.get('routing', {})

print("Routing Decision Details:")
print(f"  Strategy: {routing_metadata.get('strategy_used')}")
print(f"  Complexity: {routing_metadata.get('complexity_level')}")
print(f"  Decision time: {routing_metadata.get('routing_decision_time_ms')}ms")
print(f"  Selected model: {routing_metadata.get('selected_model', {})}")

# Access router statistics for debugging
if hasattr(generator, 'adaptive_router'):
    stats = generator.adaptive_router.get_routing_stats()
    print(f"Total routing decisions: {stats['total_decisions']}")
    print(f"Average decision time: {stats['avg_decision_time_ms']:.1f}ms")
```

#### 7.3.3 Cost Tracking Validation

```python
from src.components.generators.llm_adapters.cost_tracker import get_cost_tracker

# Get detailed cost tracker information
tracker = get_cost_tracker()

# Export detailed usage data for analysis
usage_data = tracker.export_usage_data(format_type='json', include_metadata=True)

# Parse and analyze usage patterns
import json
usage_records = json.loads(usage_data)

for record in usage_records[-10:]:  # Last 10 records
    print(f"Provider: {record['provider']}")
    print(f"Model: {record['model']}")
    print(f"Cost: ${record['cost_usd']}")
    print(f"Success: {record['success']}")
    print(f"Complexity: {record['query_complexity']}")
    print("---")
```

---

## 8. Performance Considerations

### 8.1 Routing Performance

**Expected Performance**:
- Routing decision time: 5-15ms average (target <50ms)
- Memory overhead: <5MB for routing components
- CPU overhead: <1% for routing logic

**Optimization Tips**:
```python
# Cache Epic1QueryAnalyzer results for repeated queries
config = {
    "routing": {
        "query_analyzer": {
            "config": {
                "cache_results": True,
                "cache_ttl_seconds": 300  # 5-minute cache
            }
        }
    }
}
```

### 8.2 Cost Tracking Performance

**Performance Characteristics**:
- Cost calculation: <1ms per record
- Memory usage: ~1KB per usage record
- Thread-safe concurrent access

**Optimization for High Volume**:
```python
# Configure cost tracker for high-volume usage
tracker = CostTracker(
    precision_places=4,  # Reduce precision for performance
    enable_detailed_logging=False  # Disable verbose logging
)

# Periodically clear old records
tracker.clear_usage_data(older_than_hours=24)
```

### 8.3 Model Switching Performance

**Performance Impact**:
- Model switch time: <10ms
- Memory per adapter: 1-5MB
- Connection pooling: Automatic for HTTP-based adapters

---

This comprehensive API reference provides complete documentation for all Epic 1 multi-model routing components, enabling developers to effectively implement and integrate intelligent LLM routing with cost optimization and comprehensive monitoring capabilities.