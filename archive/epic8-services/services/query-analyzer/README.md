# Query Analyzer Service

**Epic 8 Microservice** - Intelligent query complexity analysis and model recommendation service.

## Overview

The Query Analyzer Service encapsulates the Epic1QueryAnalyzer component into a cloud-native microservice, providing:

- **Query Complexity Analysis**: Classify queries as simple/medium/complex
- **Feature Extraction**: Linguistic, structural, and semantic feature analysis
- **Model Recommendation**: Intelligent routing to optimal LLM models
- **Cost Estimation**: Real-time cost analysis for multi-model routing
- **Performance Monitoring**: Comprehensive metrics and health checks

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Query Analyzer Service                      │
├─────────────────────────────────────────────────────────────┤
│  FastAPI REST API      │  gRPC Interface (Phase 1.3)       │
├─────────────────────────────────────────────────────────────┤
│              QueryAnalyzerService (Wrapper)                 │
├─────────────────────────────────────────────────────────────┤
│                 Epic1QueryAnalyzer                          │
├─────────────────┬─────────────────┬─────────────────────────┤
│ FeatureExtractor│ComplexityClass. │  ModelRecommender       │
│ - Linguistic    │ - Multi-factor  │  - Strategy-based       │
│ - Structural    │ - Configurable  │  - Cost-aware           │
│ - Semantic      │ - Real-time     │  - Fallback chains      │
└─────────────────┴─────────────────┴─────────────────────────┘
```

## Components Encapsulated

This service wraps the following **existing Epic1 components**:

### 1. Epic1QueryAnalyzer
- **Location**: `src/components/query_processors/analyzers/epic1_query_analyzer.py`
- **Function**: Main orchestrator for query analysis workflow
- **Sub-components**:

#### FeatureExtractor
- **Location**: `src/components/query_processors/analyzers/components/feature_extractor.py`
- **Function**: Extract linguistic and structural features from queries
- **Features**: Caching, multi-dimensional analysis

#### ComplexityClassifier  
- **Location**: `src/components/query_processors/analyzers/components/complexity_classifier.py`
- **Function**: Classify query complexity with confidence scoring
- **Capabilities**: Configurable thresholds, multi-factor scoring

#### ModelRecommender
- **Location**: `src/components/query_processors/analyzers/components/model_recommender.py`
- **Function**: Recommend optimal models based on complexity and strategy
- **Strategies**: cost_optimized, balanced, quality_first

## API Endpoints

### REST API (Port 8080)

#### POST `/api/v1/analyze`
Analyze a single query for complexity and model recommendations.

**Request:**
```json
{
  "query": "What are the key differences between RISC-V and ARM architectures?",
  "context": {
    "user_tier": "premium",
    "max_cost": 0.05
  },
  "options": {
    "strategy": "quality_first"
  }
}
```

**Response:**
```json
{
  "query": "What are the key differences between RISC-V and ARM architectures?",
  "complexity": "medium",
  "confidence": 0.78,
  "features": {
    "length": 65,
    "vocabulary_complexity": 0.7,
    "technical_terms": ["RISC-V", "ARM", "architectures"],
    "question_type": "comparison"
  },
  "recommended_models": [
    "openai/gpt-3.5-turbo",
    "ollama/llama3.2:3b"
  ],
  "cost_estimate": {
    "openai/gpt-3.5-turbo": 0.002,
    "ollama/llama3.2:3b": 0.0
  },
  "routing_strategy": "quality_first",
  "processing_time": 0.045,
  "metadata": {
    "analyzer_version": "1.0.0",
    "timestamp": 1699123456.789
  }
}
```

#### POST `/api/v1/batch-analyze`
Analyze multiple queries in a single request.

#### GET `/api/v1/status`
Get analyzer status and performance metrics.

#### GET `/api/v1/components`
Get detailed component information and health status.

### Health Checks

- **Liveness**: `GET /health/live` - Kubernetes liveness probe
- **Readiness**: `GET /health/ready` - Kubernetes readiness probe  
- **Detailed**: `GET /health` - Full health check with details

### Metrics (Prometheus)

Available at `/metrics`:

- `analyzer_requests_total` - Total analysis requests by status
- `analyzer_duration_seconds` - Analysis duration by complexity
- `analyzer_complexity_total` - Query distribution by complexity
- `analyzer_component_health` - Component health status

## Configuration

The service uses `config.yaml` for configuration, with environment variable overrides:

```yaml
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
      
  model_recommender:
    strategy: "balanced"
    model_mappings:
      simple: ["ollama/llama3.2:3b"]
      medium: ["openai/gpt-3.5-turbo", "ollama/llama3.2:3b"]
      complex: ["openai/gpt-4", "mistral/mistral-large"]
```

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# Run tests
pytest tests/
```

### Docker Development

```bash
# Build image
docker build -t query-analyzer:latest .

# Run container
docker run -p 8080:8080 -p 50051:50051 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  query-analyzer:latest
```

### Testing the Service

```bash
# Health check
curl http://localhost:8080/health

# Analyze a query
curl -X POST http://localhost:8080/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?"}'

# Get component status
curl http://localhost:8080/api/v1/components

# View metrics
curl http://localhost:8080/metrics
```

## Deployment

This service is designed for Kubernetes deployment as part of the Epic 8 RAG platform.

### Environment Variables

- `QUERY_ANALYZER_HOST` - Service host (default: 0.0.0.0)
- `QUERY_ANALYZER_PORT` - Service port (default: 8080)
- `QUERY_ANALYZER_LOG_LEVEL` - Logging level (default: INFO)
- `QUERY_ANALYZER_CONFIG_FILE` - Configuration file path

### Resource Requirements

- **CPU**: 1 core (requests), 2 cores (limits)
- **Memory**: 2GB (requests), 4GB (limits)  
- **Storage**: Minimal (configuration and logs)

### Dependencies

- **Internal**: None (stateless service)
- **External**: None required (all ML models are optional)

## Epic 8 Integration

This service integrates with other Epic 8 services:

- **API Gateway**: Routes requests to this service
- **Generator Service**: Receives model recommendations from this service
- **Analytics Service**: Receives metrics and analysis data
- **Cache Service**: May cache analysis results

## Performance

- **Target Latency**: <50ms per analysis
- **Throughput**: >100 requests/second
- **Accuracy**: >85% complexity classification
- **Availability**: 99.9% uptime target

## Monitoring

- **Health Checks**: Automated health monitoring
- **Metrics**: Prometheus-compatible metrics
- **Logging**: Structured JSON logging with correlation IDs
- **Tracing**: OpenTelemetry-compatible (Phase 3.2)

---

**Epic 8 Status**: Phase 1.1 Complete ✅  
**Next Phase**: 1.2 - Generator Service extraction  
**Version**: 1.0.0