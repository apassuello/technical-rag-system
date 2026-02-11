# Analytics Service - Epic 8 Cloud-Native RAG Platform

## Overview

The Analytics Service is a core component of the Epic 8 Cloud-Native RAG Platform, providing comprehensive cost tracking, performance analytics, and usage trend analysis. It integrates seamlessly with Epic 1's proven CostTracker to maintain $0.001 precision cost tracking while adding enterprise-grade analytics capabilities.

## Features

### 🔧 Epic 1 Integration
- **Cost Tracking**: Direct integration with Epic 1's CostTracker
- **$0.001 Precision**: Maintains Epic 1's proven cost tracking accuracy
- **Multi-Model Support**: Tracks costs across Ollama, OpenAI, Mistral, Anthropic, and HuggingFace
- **Budget Enforcement**: Daily/monthly budget limits with configurable alerts

### 📊 Performance Analytics
- **Real-Time Monitoring**: Track response times, error rates, and throughput
- **SLO Compliance**: Monitor against configurable SLOs (2s response time, 1% error rate, 99.9% availability)
- **Performance Trends**: Identify bottlenecks and optimization opportunities
- **Circuit Breaker**: Resilience pattern for external service failures

### 📈 Usage Analytics
- **Usage Patterns**: Analyze query complexity, provider usage, and cost trends
- **Optimization Recommendations**: Actionable insights for cost and performance optimization
- **Time-Series Analysis**: Trend analysis with configurable time buckets
- **Peak Usage Identification**: Identify high-traffic periods for capacity planning

### 🛡️ Enterprise Features
- **Circuit Breaker Pattern**: Automatic failure handling and recovery
- **Prometheus Metrics**: Full observability with custom metrics
- **Health Checks**: Kubernetes-compatible liveness and readiness probes
- **Structured Logging**: Comprehensive logging with request correlation
- **Security Hardening**: Non-root container, CORS configuration, input validation

## API Endpoints

### Core Analytics Endpoints

#### `POST /api/v1/record-query`
Record completion of a query for analytics tracking.

**Request:**
```json
{
  "query_id": "unique-query-id",
  "query": "How do transformers work?",
  "complexity": "medium",
  "provider": "openai",
  "model": "gpt-4",
  "cost_usd": 0.0234,
  "processing_time_ms": 1250.5,
  "response_time_ms": 980.3,
  "input_tokens": 156,
  "output_tokens": 89,
  "success": true,
  "error_type": null,
  "metadata": {}
}
```

#### `GET /api/v1/cost-report?time_range_hours=24&include_recommendations=true`
Generate comprehensive cost optimization report.

**Response:**
```json
{
  "report_type": "cost_analysis",
  "time_range_hours": 24,
  "cost_summary": {
    "total_cost_usd": 2.456,
    "total_requests": 1234,
    "avg_cost_per_request": 0.00199,
    "cost_by_provider": {
      "openai": 1.234,
      "ollama": 0.000,
      "mistral": 1.222
    }
  },
  "optimization": {
    "potential_total_savings": 0.987,
    "savings_percentage": 40.2,
    "optimization_opportunities": [
      {
        "type": "cost_optimization",
        "priority": "high",
        "title": "High cost on simple queries",
        "suggestion": "Route simple queries to Ollama for 90% cost reduction",
        "potential_savings": "$0.567"
      }
    ]
  },
  "epic1_integration": true
}
```

#### `GET /api/v1/performance-report?time_range_hours=24`
Generate comprehensive performance analytics report.

#### `GET /api/v1/usage-trends?time_range_hours=24&bucket_size_hours=1`
Generate usage pattern analysis and trends.

### Utility Endpoints

#### `GET /api/v1/status`
Get comprehensive service status and health information.

#### `POST /api/v1/batch-record`
Record multiple query completions in batch (up to 1000).

#### `GET /api/v1/export/{format_type}`
Export analytics data in JSON or CSV format.

### Health and Monitoring

#### `GET /health`
Comprehensive health check with component status.

#### `GET /health/live`
Kubernetes liveness probe endpoint.

#### `GET /health/ready`
Kubernetes readiness probe endpoint.

#### `GET /metrics`
Prometheus metrics endpoint.

## Configuration

### Environment Variables

```bash
# Service Configuration
ANALYTICS_SERVICE_NAME=analytics
ANALYTICS_LOG_LEVEL=INFO
ANALYTICS_DEBUG=false

# Epic 1 Cost Tracking
ANALYTICS_ENABLE_COST_TRACKING=true
ANALYTICS_COST_PRECISION_PLACES=6
ANALYTICS_DAILY_BUDGET=50.00
ANALYTICS_MONTHLY_BUDGET=1500.00
ANALYTICS_ALERT_THRESHOLDS=[0.80,0.95,1.0]

# Performance Monitoring
ANALYTICS_ENABLE_PERFORMANCE_TRACKING=true
ANALYTICS_SLO_RESPONSE_TIME_MS=2000
ANALYTICS_SLO_ERROR_RATE_THRESHOLD=0.01
ANALYTICS_SLO_AVAILABILITY_THRESHOLD=0.999

# Data Persistence
ANALYTICS_METRICS_RETENTION_HOURS=168
ANALYTICS_ENABLE_DATA_PERSISTENCE=false
ANALYTICS_PERSISTENCE_BACKEND=memory
ANALYTICS_REDIS_URL=redis://redis:6379

# Circuit Breaker
ANALYTICS_CIRCUIT_BREAKER_ENABLED=true
ANALYTICS_CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
ANALYTICS_CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60
```

### Configuration File (config.yaml)

See `config.yaml` for detailed configuration options including:
- Cost tracking settings
- Performance monitoring thresholds
- Data retention policies
- Circuit breaker configuration
- API settings

## Epic 1 Integration Details

### CostTracker Integration
The service directly imports and uses Epic 1's CostTracker:

```python
from src.components.generators.llm_adapters.cost_tracker import (
    CostTracker, UsageRecord, CostSummary
)
```

### Features Preserved from Epic 1:
- **$0.001 Precision**: All cost calculations maintain 6-decimal precision
- **Budget Enforcement**: Daily/monthly budget limits with threshold alerts
- **Multi-Provider Support**: Consistent cost tracking across all LLM providers
- **Optimization Recommendations**: Epic 1's proven cost optimization logic
- **Export Functionality**: JSON/CSV export capabilities

### Enhanced for Epic 8:
- **Microservice Architecture**: RESTful API endpoints for distributed systems
- **Performance Correlation**: Correlate cost data with performance metrics
- **Session Tracking**: Request-based cost correlation for analytics
- **Circuit Breaker**: Resilience patterns for production deployment

## Usage Examples

### Recording Query Completion

```python
import httpx
import asyncio

async def record_query():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://analytics-service:8085/api/v1/record-query",
            json={
                "query_id": "query-123",
                "query": "Explain machine learning",
                "complexity": "medium",
                "provider": "openai",
                "model": "gpt-4",
                "cost_usd": 0.0234,
                "processing_time_ms": 1250.5,
                "response_time_ms": 980.3,
                "input_tokens": 156,
                "output_tokens": 89,
                "success": True
            }
        )
        return response.json()
```

### Getting Cost Report

```python
async def get_cost_analysis():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://analytics-service:8085/api/v1/cost-report",
            params={
                "time_range_hours": 24,
                "include_recommendations": True
            }
        )
        return response.json()
```

## Deployment

### Docker

```bash
# Build the image
docker build -t analytics-service:1.0.0 .

# Run the container
docker run -p 8085:8085 \
  -e ANALYTICS_ENABLE_COST_TRACKING=true \
  -e ANALYTICS_LOG_LEVEL=INFO \
  analytics-service:1.0.0
```

### Docker Compose

```yaml
version: '3.8'
services:
  analytics:
    build:
      context: .
      dockerfile: services/analytics/Dockerfile
    ports:
      - "8085:8085"
    environment:
      - ANALYTICS_ENABLE_COST_TRACKING=true
      - ANALYTICS_DAILY_BUDGET=50.00
      - ANALYTICS_REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8085/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: analytics-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: analytics-service
  template:
    metadata:
      labels:
        app: analytics-service
    spec:
      containers:
      - name: analytics
        image: analytics-service:1.0.0
        ports:
        - containerPort: 8085
        env:
        - name: ANALYTICS_ENABLE_COST_TRACKING
          value: "true"
        - name: ANALYTICS_REDIS_URL
          value: "redis://redis-service:6379"
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
            port: 8085
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8085
          initialDelaySeconds: 5
          periodSeconds: 5
```

## Monitoring and Metrics

### Prometheus Metrics

The service exposes comprehensive Prometheus metrics:

- `analytics_requests_total` - Total API requests by endpoint and status
- `analytics_request_duration_seconds` - Request duration histogram
- `analytics_cost_tracking_total` - Total cost tracking records by provider/model
- `analytics_service_health` - Service health status gauge

### Health Monitoring

- **Liveness Probe**: `/health/live` - Service is running
- **Readiness Probe**: `/health/ready` - Service is ready to accept requests
- **Health Check**: `/health` - Comprehensive health with component status

### Logging

Structured logging with request correlation:

```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "level": "INFO",
  "logger": "analytics.api.rest",
  "message": "Recorded query completion",
  "request_id": "req-123",
  "query_id": "query-456",
  "provider": "openai",
  "model": "gpt-4",
  "cost_usd": 0.0234,
  "success": true
}
```

## Performance Characteristics

### Throughput
- **Target**: 1000+ concurrent requests
- **Response Time**: <100ms for record operations
- **Batch Processing**: Up to 1000 records per batch

### Scalability
- **Horizontal Scaling**: Stateless service design
- **Resource Usage**: ~1GB RAM, 0.5-1.0 CPU per instance
- **Data Retention**: Configurable (default 1 week)

### Reliability
- **Circuit Breaker**: Automatic failure handling
- **Health Checks**: Comprehensive component monitoring
- **Error Handling**: Graceful degradation and recovery

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
export PYTHONPATH="$(pwd):$(pwd)/../.."
export PROJECT_ROOT="$(pwd)"

# Run the service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8085 --reload
```

### Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/

# Load testing
ab -n 1000 -c 10 http://localhost:8085/health
```

## Integration with Epic 8 Services

### API Gateway Integration
The Analytics Service integrates with the API Gateway for unified query processing:

```python
# API Gateway records query completion
await analytics_client.record_query_completion(
    query_id=request.query_id,
    query=request.query,
    complexity=analysis.complexity,
    provider=response.provider,
    model=response.model,
    cost_usd=response.cost,
    processing_time_ms=total_time,
    response_time_ms=response.generation_time,
    success=response.success
)
```

### Service Communication
- **gRPC**: For high-performance internal communication
- **REST**: For external API access and debugging
- **Circuit Breaker**: For resilient service-to-service calls

## Security Considerations

### Container Security
- **Non-root User**: Runs as `appuser` with minimal privileges
- **Security Updates**: Automated security patches in base image
- **Minimal Attack Surface**: Only required dependencies installed

### API Security
- **Input Validation**: Comprehensive request validation with Pydantic
- **CORS Configuration**: Configurable origins (no wildcards in production)
- **Rate Limiting**: Built-in protection against abuse
- **Request Size Limits**: Prevent resource exhaustion

### Data Security
- **No Sensitive Data Storage**: Only aggregated metrics stored
- **Configurable Retention**: Automatic cleanup of old data
- **Optional Encryption**: Support for encrypted persistence backends

## Troubleshooting

### Common Issues

1. **Epic 1 Import Errors**
   ```bash
   # Ensure proper Python path
   export PYTHONPATH="/app:/app/src"
   
   # Check Epic 1 source availability
   ls -la src/components/generators/llm_adapters/cost_tracker.py
   ```

2. **Performance Issues**
   ```bash
   # Check metrics store health
   curl http://localhost:8085/api/v1/status
   
   # Monitor memory usage
   docker stats analytics-service
   ```

3. **Cost Tracking Issues**
   ```bash
   # Verify Epic 1 integration
   curl http://localhost:8085/health
   
   # Check cost tracker status in logs
   docker logs analytics-service | grep "CostTracker"
   ```

### Debug Mode

Enable debug logging:
```bash
export ANALYTICS_DEBUG=true
export ANALYTICS_LOG_LEVEL=DEBUG
```

## Contributing

This service is part of the Epic 8 Cloud-Native RAG Platform. Contributions should:

1. Maintain Epic 1 CostTracker integration
2. Follow FastAPI best practices
3. Include comprehensive tests
4. Update documentation
5. Maintain security standards

## License

Part of the RAG Portfolio project for ML Engineer positioning in the Swiss tech market.