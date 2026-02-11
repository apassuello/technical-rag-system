# API Gateway Service

**Epic 8 - Cloud-Native RAG Platform**

The API Gateway Service is the main orchestration service for the cloud-native RAG platform, coordinating all other microservices to provide a unified query processing pipeline.

## Overview

The API Gateway acts as the single entry point for all client requests, orchestrating calls to:
- **Query Analyzer Service** - Query complexity analysis and model routing
- **Generator Service** - Answer generation with multi-model support
- **Retriever Service** - Document retrieval with Epic 2 integration
- **Cache Service** - Response caching for performance optimization
- **Analytics Service** - Cost tracking and performance analytics

## Key Features

### 🚀 Unified Query Processing
- Single endpoint for complete RAG pipeline
- Intelligent model routing based on query complexity
- Cost optimization with sub-$0.01 target per query
- Circuit breaker patterns for resilience

### 📊 Batch Processing
- Parallel processing of multiple queries
- Configurable concurrency limits
- Comprehensive batch statistics
- Individual query success/failure tracking

### 🛡️ Resilience & Performance
- Circuit breakers for all service dependencies
- Automatic fallback responses
- Response caching with configurable TTL
- Request timeout and retry handling

### 📈 Monitoring & Analytics
- Prometheus metrics integration
- Comprehensive cost tracking
- Performance monitoring with SLO compliance
- Real-time service health status

## API Endpoints

### Core Endpoints

#### `POST /api/v1/query`
Process unified query through complete RAG pipeline.

```json
{
  "query": "How does machine learning work?",
  "context": {"domain": "AI"},
  "options": {
    "strategy": "balanced",
    "max_documents": 10,
    "cache_enabled": true,
    "analytics_enabled": true,
    "max_cost": 0.01
  },
  "session_id": "session-123",
  "user_id": "user-456"
}
```

**Response**: Complete answer with sources, cost breakdown, and performance metrics.

#### `POST /api/v1/batch-query`
Process multiple queries in batch with optional parallelization.

```json
{
  "queries": [
    "What is machine learning?",
    "How does deep learning work?",
    "What are neural networks?"
  ],
  "context": {"domain": "AI"},
  "options": {
    "strategy": "cost_optimized"
  },
  "parallel_processing": true,
  "max_parallel": 5
}
```

**Response**: Batch results with individual query outcomes and summary statistics.

### Status & Management

#### `GET /api/v1/status`
Comprehensive gateway and service health information.

#### `GET /api/v1/models`
Available models across all providers with capabilities and status.

#### `GET /health/live` & `/health/ready`
Kubernetes health probes for container orchestration.

#### `GET /metrics`
Prometheus metrics for monitoring and alerting.

## Configuration

### Environment Variables

```bash
# Service Endpoints
GATEWAY_QUERY_ANALYZER_HOST=query-analyzer-service
GATEWAY_QUERY_ANALYZER_PORT=8082
GATEWAY_GENERATOR_HOST=generator-service
GATEWAY_GENERATOR_PORT=8081
GATEWAY_RETRIEVER_HOST=retriever-service
GATEWAY_RETRIEVER_PORT=8083
GATEWAY_CACHE_HOST=cache-service
GATEWAY_CACHE_PORT=8084
GATEWAY_ANALYTICS_HOST=analytics-service
GATEWAY_ANALYTICS_PORT=8085

# Gateway Configuration
GATEWAY_MAX_QUERY_LENGTH=10000
GATEWAY_MAX_BATCH_SIZE=100
GATEWAY_DEFAULT_TIMEOUT=30
GATEWAY_MAX_RETRIES=3

# Circuit Breaker Settings
GATEWAY_CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
GATEWAY_CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60

# Rate Limiting
GATEWAY_RATE_LIMIT_PER_MINUTE=100
GATEWAY_BURST_LIMIT=20

# Security (Production)
GATEWAY_VALID_API_KEYS=key1,key2,key3
```

### Configuration File

See `config.yaml` for complete configuration options including:
- Service endpoints and timeouts
- Circuit breaker settings
- CORS configuration
- Security settings
- Epic 8 compliance parameters

## Deployment

### Docker

```bash
# Build image
docker build -t api-gateway:1.0.0 .

# Run container
docker run -p 8080:8080 \
  -e GATEWAY_QUERY_ANALYZER_HOST=localhost \
  -e GATEWAY_GENERATOR_HOST=localhost \
  api-gateway:1.0.0
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: api-gateway:1.0.0
        ports:
        - containerPort: 8080
        env:
        - name: GATEWAY_QUERY_ANALYZER_HOST
          value: "query-analyzer-service"
        - name: GATEWAY_GENERATOR_HOST
          value: "generator-service"
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "1000m"
            memory: "2Gi"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8080
          initialDelaySeconds: 30
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 5
```

### Docker Compose

```yaml
version: '3.8'
services:
  api-gateway:
    build: .
    ports:
      - "8080:8080"
    environment:
      - GATEWAY_QUERY_ANALYZER_HOST=query-analyzer
      - GATEWAY_GENERATOR_HOST=generator
      - GATEWAY_RETRIEVER_HOST=retriever
      - GATEWAY_CACHE_HOST=cache
      - GATEWAY_ANALYTICS_HOST=analytics
    depends_on:
      - query-analyzer
      - generator
      - retriever
      - cache
      - analytics
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Development

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

### Testing

```bash
# Unit tests
pytest tests/unit/

# Integration tests (requires running services)
pytest tests/integration/

# Load testing
python tests/load_test.py
```

## Architecture

### Service Integration

```
┌─────────────────┐    ┌──────────────────┐
│   API Gateway   │────│  Query Analyzer  │
│                 │    │    Service       │
│  Orchestrates   │    └──────────────────┘
│  Complete RAG   │    
│  Pipeline       │    ┌──────────────────┐
│                 │────│   Generator      │
│  - Caching      │    │    Service       │
│  - Analytics    │    └──────────────────┘
│  - Cost Track   │    
│  - Fallbacks    │    ┌──────────────────┐
│                 │────│   Retriever      │
└─────────────────┘    │    Service       │
         │              └──────────────────┘
         │              
         │              ┌──────────────────┐
         ├──────────────│     Cache        │
         │              │    Service       │
         │              └──────────────────┘
         │              
         │              ┌──────────────────┐
         └──────────────│   Analytics      │
                        │    Service       │
                        └──────────────────┘
```

### Request Flow

1. **Request Validation** - Validate query format and parameters
2. **Cache Check** - Look for existing cached response
3. **Query Analysis** - Analyze complexity and extract routing decisions
4. **Document Retrieval** - Fetch relevant documents based on analysis
5. **Answer Generation** - Generate response using optimal model
6. **Response Assembly** - Combine all components into unified response
7. **Caching & Analytics** - Store response and record metrics

### Circuit Breaker Integration

Each service dependency is protected by circuit breakers that:
- Track failure rates and response times
- Open circuit on repeated failures
- Provide fallback responses when possible
- Automatically recover after timeout period

## Performance Targets

### Epic 8 Compliance

- **Response Time**: P95 < 2 seconds, maximum 10 seconds
- **Throughput**: Support 1000+ concurrent requests
- **Cost Efficiency**: Average < $0.01 per query
- **Availability**: 99.9% uptime target
- **Cache Performance**: > 60% hit rate for common queries

### Monitoring Metrics

- Request rate and latency distributions
- Error rates by service and error type
- Circuit breaker states and trip rates
- Cost per query and optimization opportunities
- Cache hit rates and performance
- Service dependency health and response times

## Security

### Production Security

- API key authentication on all endpoints
- CORS configuration for web applications
- Request rate limiting and burst protection
- Input validation and sanitization
- Structured logging for audit trails

### Network Security

- Internal service communication over private networks
- mTLS for service-to-service communication (with Istio)
- Network policies for pod isolation
- Secret management for API keys and tokens

## Troubleshooting

### Common Issues

1. **Service Unavailable (503)**
   - Check individual service health at `/api/v1/status`
   - Verify service endpoints and network connectivity
   - Check circuit breaker states

2. **High Response Times**
   - Monitor service-specific latencies in status endpoint
   - Check cache hit rates and optimize cache configuration
   - Verify resource limits and auto-scaling settings

3. **Cost Budget Exceeded**
   - Review cost reports at analytics service
   - Adjust model routing strategies
   - Implement stricter cost limits in query options

### Health Monitoring

```bash
# Check overall gateway status
curl http://localhost:8080/api/v1/status

# Check individual service health
curl http://localhost:8080/health/ready

# Monitor real-time metrics
curl http://localhost:8080/metrics
```

## Contributing

### Development Guidelines

1. Follow FastAPI and Pydantic patterns established in codebase
2. Add comprehensive tests for new features
3. Update metrics and monitoring for new endpoints
4. Document API changes in OpenAPI schema
5. Ensure Epic 8 compliance standards are maintained

### Code Quality

- Type hints required for all functions
- Structured logging with correlation IDs
- Error handling with proper fallbacks
- Circuit breaker integration for new service calls
- Prometheus metrics for new functionality

## License

This API Gateway Service is part of the Epic 8 Cloud-Native RAG Platform, developed for Swiss tech market positioning and ML Engineering excellence demonstration.