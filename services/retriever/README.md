# Retriever Service

The Retriever Service provides document retrieval capabilities for Epic 8's cloud-native RAG platform by wrapping Epic 2's ModularUnifiedRetriever in a microservices architecture.

## Overview

This service implements a REST API interface for Epic 2's proven retrieval capabilities, including:

- **Hybrid Search**: Combines dense semantic search (FAISS) with sparse keyword search (BM25)
- **Modular Architecture**: Pluggable components for vector indexing, sparse retrieval, fusion strategies, and reranking
- **Circuit Breaker Pattern**: Reliability through fallback mechanisms
- **Performance Monitoring**: Comprehensive metrics and health checks
- **Batch Processing**: Efficient handling of multiple queries
- **Document Management**: Indexing and reindexing operations

## Features

### Core Retrieval Capabilities
- **Dense Vector Search**: FAISS-based semantic similarity
- **Sparse Keyword Search**: BM25-based term matching
- **Result Fusion**: Multiple strategies (RRF, weighted, score-aware)
- **Semantic Reranking**: Cross-encoder based relevance improvement
- **Composite Filtering**: Advanced quality control mechanisms

### Microservice Features
- **REST API**: Comprehensive endpoints for all operations
- **Circuit Breakers**: Automatic fallback handling
- **Prometheus Metrics**: Performance and operational monitoring
- **Health Checks**: Kubernetes-compatible liveness/readiness probes
- **Structured Logging**: Comprehensive operational visibility
- **Error Handling**: Graceful degradation and error recovery

## API Endpoints

### Document Retrieval
- `POST /api/v1/retrieve` - Single query document retrieval
- `POST /api/v1/batch-retrieve` - Batch query processing

### Document Management
- `POST /api/v1/index` - Index new documents
- `POST /api/v1/reindex` - Trigger complete reindexing

### Service Management
- `GET /api/v1/status` - Comprehensive service status
- `GET /health` - Health check with detailed information
- `GET /health/live` - Kubernetes liveness probe
- `GET /health/ready` - Kubernetes readiness probe
- `GET /metrics` - Prometheus metrics

## Configuration

The service is configured via `config.yaml` with the following sections:

### Service Configuration
```yaml
service:
  name: "retriever-service"
  version: "1.0.0"
  host: "0.0.0.0"
  port: 8083
  debug: false
```

### Epic 2 Retriever Configuration
```yaml
retriever_config:
  vector_index:
    type: "faiss"
    config:
      index_type: "IndexFlatIP"
      normalize_embeddings: true
      dimension: 384

  sparse:
    type: "bm25"
    config:
      k1: 1.2
      b: 0.75

  fusion:
    type: "rrf"
    config:
      k: 60
      weights:
        dense: 0.7
        sparse: 0.3

  reranker:
    type: "semantic"
    config:
      enabled: true
      model: "cross-encoder/ms-marco-MiniLM-L-6-v2"
```

### Performance Configuration
```yaml
performance:
  circuit_breaker:
    failure_threshold: 5
    recovery_timeout: 60
  
  timeouts:
    retrieval_timeout: 30.0
    indexing_timeout: 300.0
  
  batch:
    max_batch_size: 100
    batch_timeout: 5.0
```

## Development

### Local Setup

1. **Install Dependencies**:
   ```bash
   cd services/retriever
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   # Copy and modify configuration
   cp config.yaml config.local.yaml
   # Edit config.local.yaml as needed
   ```

3. **Run Service**:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8083 --reload
   ```

4. **Access Documentation**:
   - API Docs: http://localhost:8083/docs
   - ReDoc: http://localhost:8083/redoc
   - Health: http://localhost:8083/health
   - Metrics: http://localhost:8083/metrics

### Docker Deployment

1. **Build Image**:
   ```bash
   # From project root
   docker build -f services/retriever/Dockerfile -t retriever-service:latest .
   ```

2. **Run Container**:
   ```bash
   docker run -p 8083:8083 \
     -e PYTHONPATH=/app:/app/src \
     -e PROJECT_ROOT=/app \
     retriever-service:latest
   ```

### Docker Compose Integration

```yaml
version: '3.8'
services:
  retriever:
    build:
      context: .
      dockerfile: services/retriever/Dockerfile
    ports:
      - "8083:8083"
    environment:
      - PYTHONPATH=/app:/app/src
      - PROJECT_ROOT=/app
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8083/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

## Testing

### Unit Tests
```bash
cd services/retriever
pytest tests/ -v --cov=app
```

### Integration Tests
```bash
# Start service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8083 &

# Run integration tests
pytest tests/integration/ -v
```

### Load Testing
```bash
# Example using curl
curl -X POST "http://localhost:8083/api/v1/retrieve" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "k": 10,
    "retrieval_strategy": "hybrid",
    "complexity": "medium"
  }'
```

## Monitoring

### Prometheus Metrics

The service exposes the following metrics:

- `retriever_requests_total` - Total retrieval requests by status and strategy
- `retriever_duration_seconds` - Retrieval duration by strategy
- `retriever_indexed_documents` - Number of indexed documents
- `retriever_index_health` - Index health status by component
- `retriever_api_requests_total` - Total API requests by endpoint and status
- `retriever_api_request_duration_seconds` - API request duration by endpoint

### Health Checks

- **Liveness**: Service is running (http://localhost:8083/health/live)
- **Readiness**: Service is ready to accept requests (http://localhost:8083/health/ready)
- **Detailed Health**: Comprehensive health information (http://localhost:8083/health)

### Logging

Structured logging with the following fields:
- `timestamp` - ISO format timestamp
- `level` - Log level (INFO, WARNING, ERROR)
- `logger` - Logger name
- `message` - Log message
- `query_length` - Query string length
- `results_count` - Number of results returned
- `processing_time` - Operation duration
- `error` - Error details (for error logs)

## Architecture Integration

### Epic 2 Integration

This service wraps Epic 2's ModularUnifiedRetriever, preserving all its capabilities:

- **Vector Index**: FAISSIndex for dense semantic search
- **Sparse Retriever**: BM25Retriever for keyword search
- **Fusion Strategy**: RRFFusion, WeightedFusion, ScoreAwareFusion
- **Reranker**: SemanticReranker, NeuralReranker, IdentityReranker

### API Gateway Integration

Designed to integrate with the API Gateway service:

```python
# API Gateway usage example
retriever_client = RetrieverClient("retriever-service:8083")
documents = await retriever_client.retrieve_documents(
    query=query,
    complexity=analysis.complexity,
    max_documents=analysis.recommended_doc_count
)
```

### Service Dependencies

- **Epic 2 ModularUnifiedRetriever**: Core retrieval functionality
- **ModularEmbedder**: Document and query embedding generation
- **ComponentFactory**: Component creation and configuration
- **Redis** (optional): Caching layer for improved performance
- **PostgreSQL** (optional): Metadata storage for documents

## Error Handling

The service implements comprehensive error handling:

### Circuit Breaker Pattern
- Automatic fallback when retrieval fails
- Configurable failure threshold and recovery timeout
- Graceful degradation with fallback responses

### Fallback Mechanisms
- Simple fallback retrieval for critical failures
- Error document generation with helpful messages
- Metric tracking for fallback usage

### Error Categories
- **Validation Errors**: Invalid request parameters (400)
- **Service Errors**: Internal processing failures (500)
- **Timeout Errors**: Operations exceeding timeout limits
- **Circuit Breaker**: Service temporarily unavailable (503)

## Performance Optimization

### Async Processing
- Non-blocking I/O for all operations
- Concurrent batch processing
- Thread pool for CPU-intensive tasks

### Resource Management
- Configurable batch sizes
- Memory-efficient document handling
- Connection pooling for database operations

### Caching Strategy
- Response caching for common queries
- Index caching for frequently accessed documents
- Embedding caching to avoid recomputation

## Production Considerations

### Security
- Non-root user in Docker container
- Input validation and sanitization
- Rate limiting (via API Gateway)
- CORS configuration for web clients

### Scalability
- Horizontal scaling via Kubernetes
- Load balancing across instances
- Stateless design for easy scaling

### Reliability
- Health checks for Kubernetes orchestration
- Graceful shutdown handling
- Automatic restart on failures
- Comprehensive monitoring and alerting

## Troubleshooting

### Common Issues

1. **Service Won't Start**:
   - Check Python path configuration
   - Verify Epic 2 components are available
   - Check port availability

2. **Retrieval Failures**:
   - Verify document indexing
   - Check embedder initialization
   - Review circuit breaker status

3. **Performance Issues**:
   - Monitor batch sizes
   - Check timeout configurations
   - Review resource usage

### Debug Mode

Enable debug mode for detailed logging:

```yaml
service:
  debug: true

monitoring:
  logging:
    level: "DEBUG"
    include_performance_metrics: true
```

### Logs Analysis

```bash
# View service logs
docker logs retriever-service

# Filter for errors
docker logs retriever-service 2>&1 | grep ERROR

# Monitor performance
curl http://localhost:8083/metrics | grep retriever_
```