# Generator Service

**Epic 8 Microservice** - Multi-model answer generation with intelligent routing and cost optimization.

## Overview

The Generator Service encapsulates the Epic1AnswerGenerator component into a cloud-native microservice, providing:

- **Multi-Model Routing**: Intelligent selection between Ollama, OpenAI, Mistral, and other LLM providers
- **Cost Optimization**: Real-time cost tracking and budget-aware routing
- **Adaptive Strategies**: cost_optimized, balanced, and quality_first routing strategies
- **Fallback Chains**: Robust error handling with automatic fallback mechanisms
- **Performance Monitoring**: Comprehensive metrics and health checks

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Generator Service                         │
├─────────────────────────────────────────────────────────────┤
│  FastAPI REST API      │  gRPC Interface (Phase 1.3)       │
├─────────────────────────────────────────────────────────────┤
│               GeneratorService (Wrapper)                    │
├─────────────────────────────────────────────────────────────┤
│                 Epic1AnswerGenerator                        │
├──────────────┬────────────────┬──────────────┬──────────────┤
│ LLM Adapters │ AdaptiveRouter │ CostTracker  │PromptBuilder │
│ - Ollama     │ - Strategies   │ - Budget     │ - Templates  │
│ - OpenAI     │ - Model Select │ - Precision  │ - Context    │
│ - Mistral    │ - Fallback     │ - Alerts     │ - Validation │
│ - HuggingFace│ - A/B Testing  │ - Reporting  │ - Parsing    │
└──────────────┴────────────────┴──────────────┴──────────────┘
```

## Components Encapsulated

This service wraps the following **existing Epic1 components**:

### 1. Epic1AnswerGenerator
- **Location**: `src/components/generators/epic1_answer_generator.py`
- **Function**: Main orchestrator for multi-model answer generation
- **Sub-components**:

#### LLM Adapters
- **Ollama Adapter**: `src/components/generators/llm_adapters/ollama_adapter.py`
- **OpenAI Adapter**: `src/components/generators/llm_adapters/openai_adapter.py`
- **Mistral Adapter**: `src/components/generators/llm_adapters/mistral_adapter.py`
- **HuggingFace Adapter**: `src/components/generators/llm_adapters/huggingface_adapter.py`

#### Routing System
- **AdaptiveRouter**: `src/components/generators/routing/adaptive_router.py`
- **RoutingStrategies**: `src/components/generators/routing/routing_strategies.py`
- **ModelRegistry**: `src/components/generators/routing/model_registry.py`

#### Supporting Components
- **CostTracker**: `src/components/generators/llm_adapters/cost_tracker.py`
- **PromptBuilder**: `src/components/generators/prompt_builders/simple_prompt.py`
- **ResponseParser**: `src/components/generators/response_parsers/markdown_parser.py`
- **ConfidenceScorer**: `src/components/generators/confidence_scorers/semantic_scorer.py`

## API Endpoints

### REST API (Port 8081)

#### POST `/api/v1/generate`
Generate an answer using multi-model routing.

**Request:**
```json
{
  "query": "What are the key advantages of RISC-V over traditional architectures?",
  "context_documents": [
    {
      "content": "RISC-V is an open-source instruction set architecture...",
      "metadata": {"source": "risc-v-spec.pdf", "page": 1},
      "doc_id": "doc_1",
      "score": 0.95
    }
  ],
  "options": {
    "strategy": "balanced",
    "max_cost": 0.05,
    "preferred_model": "openai/gpt-3.5-turbo"
  }
}
```

**Response:**
```json
{
  "answer": "RISC-V offers several key advantages over traditional architectures...",
  "query": "What are the key advantages of RISC-V over traditional architectures?",
  "model_used": "openai/gpt-3.5-turbo",
  "cost": 0.0023,
  "confidence": 0.92,
  "routing_decision": {
    "strategy": "balanced",
    "available_models": ["openai/gpt-3.5-turbo", "ollama/llama3.2:3b"],
    "selection_reason": "Best balance of cost and quality for medium complexity query",
    "fallback_used": false,
    "cost_estimate": 0.0023
  },
  "processing_time": 1.23,
  "metadata": {
    "generator_version": "1.0.0",
    "timestamp": 1699123456.789,
    "context_documents_count": 1
  }
}
```

#### POST `/api/v1/batch-generate`
Process multiple generation requests in batch.

#### GET `/api/v1/models`
Get information about available models and their capabilities.

#### GET `/api/v1/status`
Get generator status and performance metrics.

#### POST `/api/v1/test-routing`
Test routing decisions without generating answers (cost-free).

### Health Checks

- **Liveness**: `GET /health/live` - Kubernetes liveness probe
- **Readiness**: `GET /health/ready` - Kubernetes readiness probe  
- **Detailed**: `GET /health` - Full health check with model availability

### Metrics (Prometheus)

Available at `/metrics`:

- `generator_requests_total` - Total generation requests by status and model
- `generator_duration_seconds` - Generation duration by model
- `generator_cost_dollars_total` - Total cost by model
- `generator_model_health` - Model health status

## Multi-Model Routing Strategies

### 1. Cost Optimized (`cost_optimized`)
- **Priority**: Minimize cost per query
- **Model Preference**: Ollama → OpenAI GPT-3.5 → Mistral Small
- **Max Cost**: $0.01 per query
- **Use Case**: High-volume, budget-constrained scenarios

### 2. Balanced (`balanced`)
- **Priority**: Balance cost and quality
- **Model Preference**: OpenAI GPT-3.5 → Mistral Medium → Ollama
- **Max Cost**: $0.05 per query  
- **Use Case**: General-purpose applications

### 3. Quality First (`quality_first`)
- **Priority**: Maximum answer quality
- **Model Preference**: OpenAI GPT-4 → Mistral Large → OpenAI GPT-3.5
- **Max Cost**: $0.10 per query
- **Use Case**: Critical applications, complex reasoning

## Configuration

The service uses `config.yaml` for configuration:

```yaml
generator:
  routing:
    enabled: true
    default_strategy: "balanced"
    strategies:
      balanced:
        model_preferences:
          - "openai/gpt-3.5-turbo"
          - "mistral/mistral-medium"
          - "ollama/llama3.2:3b"
        cost_weights:
          "openai/gpt-3.5-turbo": 0.002
          "mistral/mistral-medium": 0.004
          "ollama/llama3.2:3b": 0.0
        max_cost_per_query: 0.05

  fallback:
    enabled: true
    fallback_model: "ollama/llama3.2:3b"
    max_retries: 3

  cost_tracking:
    enabled: true
    precision_places: 6
    daily_budget_limit: 100.0
```

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8081

# Run tests
pytest tests/
```

### Docker Development

```bash
# Build image
docker build -t generator:latest .

# Run container
docker run -p 8081:8081 -p 50052:50052 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -e OPENAI_API_KEY=your_key \
  -e MISTRAL_API_KEY=your_key \
  generator:latest
```

### Testing the Service

```bash
# Health check
curl http://localhost:8081/health

# Get available models
curl http://localhost:8081/api/v1/models

# Test routing decision (no cost)
curl -X POST http://localhost:8081/api/v1/test-routing \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "strategy": "cost_optimized"}'

# Generate an answer
curl -X POST http://localhost:8081/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "context_documents": [{
      "content": "Machine learning is a subset of AI...",
      "metadata": {}
    }]
  }'
```

## Deployment

### Environment Variables

- `GENERATOR_HOST` - Service host (default: 0.0.0.0)
- `GENERATOR_PORT` - Service port (default: 8081)
- `GENERATOR_LOG_LEVEL` - Logging level (default: INFO)
- `GENERATOR_CONFIG_FILE` - Configuration file path
- `OPENAI_API_KEY` - OpenAI API key (required for OpenAI models)
- `MISTRAL_API_KEY` - Mistral API key (required for Mistral models)

### Resource Requirements

- **CPU**: 2 cores (requests), 4 cores (limits)
- **Memory**: 4GB (requests), 8GB (limits)
- **Storage**: Minimal (configuration and logs)
- **Network**: Outbound HTTPS for API calls

### Dependencies

- **Internal Services**: Query Analyzer Service (for complexity analysis)
- **External Services**: 
  - OpenAI API (optional)
  - Mistral AI API (optional)
  - Ollama server (optional)

## Epic 8 Integration

This service integrates with other Epic 8 services:

- **Query Analyzer**: Receives complexity analysis and model recommendations
- **API Gateway**: Routes generation requests to this service
- **Cache Service**: May cache generated responses
- **Analytics Service**: Receives cost and performance metrics

## Performance

- **Target Latency**: <2s for most queries
- **Throughput**: >50 concurrent requests
- **Cost Efficiency**: <$0.01 average per query (balanced strategy)
- **Availability**: 99.9% uptime target

## Cost Management

- **Real-time Tracking**: Track costs to $0.000001 precision
- **Budget Controls**: Daily and per-user budget limits
- **Cost Alerts**: Automated alerts at 80% budget utilization
- **Model Selection**: Automatic cost-aware routing

---

**Epic 8 Status**: Phase 1.2 Complete ✅  
**Next Phase**: 1.3 - Service communication layer (gRPC/protobuf)  
**Version**: 1.0.0