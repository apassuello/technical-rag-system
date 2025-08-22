# Epic 8: Cloud-Native Multi-Model RAG Platform - Test Suite

## Overview

Comprehensive test suite for Epic 8 microservices implementation, focusing on **realistic early-stage testing** with clear failure detection rather than production-grade requirements.

## Test Directory Structure

```
tests/epic8/
├── unit/           # Service-level unit tests (basic functionality validation)
├── integration/    # Service-to-service communication tests
├── api/           # REST API contract and endpoint validation
├── performance/   # Basic performance sanity checks
└── smoke/         # Quick health checks for microservices
```

## Test Categories

### Unit Tests (`unit/`)
**Focus**: Basic functionality validation
- Service starts and responds to health checks
- Core functionality works without crashing
- API endpoints return proper JSON structure
- Basic business logic validation

### Integration Tests (`integration/`)
**Focus**: Service-to-service communication
- End-to-end request flow completion
- Service discovery functionality
- Cross-service data flow validation

### API Tests (`api/`)
**Focus**: REST API contract validation
- Endpoint compliance with OpenAPI specs
- Request/response schema validation
- Error handling and status codes

### Performance Tests (`performance/`)
**Focus**: Basic performance sanity checks
- System handles 10 concurrent requests without crashing
- Memory usage stays below reasonable limits
- No obvious memory leaks over short duration

### Smoke Tests (`smoke/`)
**Focus**: Quick health checks
- Services start successfully
- Health endpoints return 200 OK
- Basic connectivity verification

## Realistic Testing Thresholds

### Clear Failure Indicators (Hard Fails)
These indicate the system is completely broken:
- Service won't start or crashes immediately
- Health check returns 500 error
- Response time >60 seconds (clearly broken)
- Memory usage >8GB per service (clearly broken)
- 0% classification accuracy (completely broken)

### Quality Indicators (Flag but Don't Fail)
These flag issues for improvement but don't stop testing:
- Classification accuracy <85% (flag for improvement)
- Response time >2s (flag for optimization)
- Cache hit ratio <60% (flag for tuning)
- Cost per query >$0.10 (flag for review)

## Running Epic 8 Tests

### Available Commands

```bash
# Run all Epic 8 unit tests
./run_tests.sh epic8 unit

# Run Epic 8 integration tests
./run_tests.sh epic8 integration

# Run Epic 8 API tests
./run_tests.sh epic8 api

# Run Epic 8 performance tests
./run_tests.sh epic8 performance

# Run Epic 8 smoke tests
./run_tests.sh epic8 smoke

# Run all Epic 8 tests
./run_tests.sh epic8 all
```

### Python Test Runner

```bash
# Run specific Epic 8 test suites
python test_runner.py epic8 unit
python test_runner.py epic8 integration --format json
python test_runner.py epic8 all --output epic8_results.json
```

## Test Implementation Strategy

### Agent Workflow
1. **spec-test-writer**: Creates test suites from Epic 8 specifications
2. **specs-implementer**: Implements functionality from specifications (parallel)
3. **test-runner**: Runs and debugs both tests and implementation

### Current Test Status
- **Query Analyzer Service (1.1)**: 40+ existing tests (enhance for Epic 8)
- **Generator Service (1.2)**: Missing comprehensive test suite (create from specs)
- **Integration Tests**: Not yet implemented (create for service communication)
- **Performance Tests**: Basic sanity checks only (no load testing yet)

## Success Criteria

### Phase 1: Basic Functionality (Week 1)
- ✅ All services start and respond to requests
- ✅ API endpoints return proper JSON structures
- ✅ Basic unit tests pass for core functionality

### Phase 2: Integration (Week 2)
- ✅ End-to-end requests complete successfully
- ✅ Services can communicate with each other
- ✅ Integration tests validate service workflows

### Phase 3: Quality Validation (Week 3)
- ✅ Performance thresholds tracked (flag issues)
- ✅ API contract compliance validated
- ✅ Basic deployment and health checks working

## Configuration

Epic 8 tests are configured in `tests/runner/test_config.yaml` with:
- **Success Rate**: 80% minimum (realistic for early stage)
- **Timeout**: Various per test type (120s-1800s)
- **Parallel Execution**: Enabled for unit and API tests
- **Quality Thresholds**: Defined for flagging vs failing

## Dependencies

### Services Under Test
- **Query Analyzer Service**: `services/query-analyzer/` (implemented)
- **Generator Service**: `services/generator/` (implemented)
- Future: API Gateway, Retriever, Cache, Analytics services

### Test Infrastructure
- **pytest**: Core testing framework
- **FastAPI TestClient**: API endpoint testing
- **httpx**: Async HTTP client testing
- **pytest-asyncio**: Async test support

## Contributing

When adding new Epic 8 tests:

1. Place tests in appropriate category directory
2. Follow realistic threshold approach (flag vs fail)
3. Use existing test patterns from Epic 1
4. Document test purpose and expected behavior
5. Include both positive and negative test cases

## Epic 8 Retriever Service Tests

### Overview

The Retriever Service test suite validates the integration of Epic 2's ModularUnifiedRetriever within Epic 8's microservices architecture, ensuring preservation of functionality while adding cloud-native capabilities.

### Test Structure

```
tests/epic8/
├── unit/test_retriever_service.py           # RetrieverService core functionality
├── api/test_retriever_api.py               # REST API endpoint validation
├── integration/test_retriever_integration.py # Epic 2 integration tests
└── performance/test_retriever_performance.py # Performance and scalability
```

### Key Test Classes

#### Unit Tests (`test_retriever_service.py`)
- **TestRetrieverServiceBasics**: Service initialization and health checks
- **TestRetrieverServiceDocumentRetrieval**: Core retrieval functionality
- **TestRetrieverServiceBatchRetrieval**: Batch operation handling
- **TestRetrieverServiceDocumentIndexing**: Document indexing operations
- **TestRetrieverServiceErrorHandling**: Error scenarios and fallbacks
- **TestRetrieverServiceResources**: Resource management and cleanup

#### API Tests (`test_retriever_api.py`)
- **TestRetrieverAPIHealth**: Health endpoints (`/health`, `/health/live`, `/health/ready`)
- **TestRetrieverAPIDocumentRetrieval**: `/api/v1/retrieve` endpoint validation
- **TestRetrieverAPIBatchRetrieval**: `/api/v1/batch-retrieve` endpoint testing
- **TestRetrieverAPIDocumentIndexing**: `/api/v1/index` and `/api/v1/reindex` endpoints
- **TestRetrieverAPIStatus**: `/api/v1/status` monitoring endpoint
- **TestRetrieverAPIErrorHandling**: Error response validation

#### Integration Tests (`test_retriever_integration.py`)
- **TestRetrieverServiceEpic2Integration**: Epic 2 ModularUnifiedRetriever integration
- **TestRetrieverServicePerformanceVsEpic2**: Performance comparison with direct Epic 2 usage
- **TestRetrieverServiceResilience**: Error handling with Epic 2 components

#### Performance Tests (`test_retriever_performance.py`)
- **TestRetrieverServiceBasicPerformance**: Latency and throughput validation
- **TestRetrieverServiceScalabilityPerformance**: Dataset size scaling tests
- **TestRetrieverServiceResourceUsage**: Memory, CPU, and disk usage monitoring
- **TestRetrieverServiceStressTest**: Load testing and edge cases

### Epic 8 Retriever-Specific Thresholds

#### Hard Fails (System Broken)
- Service startup failure or crashes
- Epic 2 component initialization failure
- API responses >60 seconds
- Memory usage >8GB
- 0% retrieval accuracy

#### Quality Flags (Optimization Needed)
- P95 retrieval latency >2 seconds
- Indexing throughput <1 doc/second
- API success rate <90%
- Memory leaks during sustained operations
- >50% performance overhead vs direct Epic 2

### Running Retriever Service Tests

```bash
# All retriever tests
pytest tests/epic8/unit/test_retriever_service.py tests/epic8/api/test_retriever_api.py tests/epic8/integration/test_retriever_integration.py tests/epic8/performance/test_retriever_performance.py -v

# Quick validation (unit + API)
pytest tests/epic8/unit/test_retriever_service.py tests/epic8/api/test_retriever_api.py -v

# Epic 2 integration tests
pytest tests/epic8/integration/test_retriever_integration.py -v

# Performance validation
pytest tests/epic8/performance/test_retriever_performance.py -v --tb=short
```

### Epic 2 Integration Requirements

The Retriever Service tests require Epic 2 components:
- `ModularUnifiedRetriever` from `src.components.retrievers`
- `ModularEmbedder` from `src.components.embedders`
- `ComponentFactory` from `src.core.component_factory`

Tests use comprehensive mocking when Epic 2 components aren't available:
```python
with mock.patch('app.core.retriever.ComponentFactory') as mock_factory:
    with mock.patch('app.core.retriever.ModularUnifiedRetriever') as mock_retriever:
        # Test with mocked Epic 2 components
        service = RetrieverService(config)
```

### Test Data Patterns

#### Document Templates
```python
test_document = {
    "content": "Substantial content for meaningful retrieval testing...",
    "metadata": {"title": "Test Doc", "topic": "machine_learning"},
    "doc_id": "test_001",
    "source": "test.pdf"
}
```

#### Query Patterns
- **Simple**: "machine learning", "AI"
- **Medium**: "machine learning applications in healthcare"
- **Complex**: "comparative analysis of transformer architectures for NLP tasks"

### Performance Baselines

| Metric | Target | Hard Fail | Quality Flag |
|--------|--------|-----------|-------------|
| Retrieval Latency (P95) | <1s | >60s | >2s |
| Indexing Throughput | >5 docs/sec | 0 docs/sec | <1 doc/sec |
| Concurrent Requests | 20 req/sec | 0% success | <90% success |
| Memory Usage | <2GB | >8GB | >4GB |
| Epic 2 Overhead | <10% | >1000% | >50% |

### Troubleshooting

#### Common Issues
1. **Epic 2 Import Errors**: Ensure project root is in PYTHONPATH
2. **Service Startup Issues**: Check port conflicts and dependencies
3. **Performance Test Timeouts**: Run with `--timeout=300` for longer operations
4. **Memory Issues**: Monitor with `psutil` and run smaller test subsets

#### Test Isolation
- Integration tests use temporary directories for indices
- Unit tests mock external dependencies
- Performance tests clean up resources after execution
- API tests use FastAPI TestClient for isolation

## Notes

- This is **early-stage implementation testing**
- Focus on basic functionality rather than production performance
- Use realistic thresholds that indicate clear failures
- Build foundation for future production-grade testing
- **Retriever Service** demonstrates Epic 2 integration patterns for other services