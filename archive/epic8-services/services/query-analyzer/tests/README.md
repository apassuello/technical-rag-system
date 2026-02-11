# Query Analyzer Service - Test Suite

This directory contains a comprehensive test suite for the Query Analyzer Service, validating all aspects of the microservice including Epic1QueryAnalyzer integration, API endpoints, performance, and error handling.

## Test Structure

```
tests/
├── conftest.py                    # Pytest fixtures and utilities
├── pytest.ini                    # Pytest configuration
├── requirements.txt              # Test dependencies
├── run_tests.py                  # Test runner script
├── README.md                     # This file
├── unit/                         # Unit tests for individual components
│   ├── test_analyzer_service.py  # QueryAnalyzerService tests
│   ├── test_config.py            # Configuration management tests
│   ├── test_schemas.py           # Pydantic schema validation tests
│   └── test_api_rest.py          # REST API endpoint logic tests
├── integration/                  # Service integration tests
│   ├── test_service_integration.py  # Full service integration
│   └── test_epic1_integration.py   # Epic1QueryAnalyzer integration
├── api/                          # API endpoint tests
│   ├── test_analyze_endpoints.py   # /analyze and /batch-analyze
│   ├── test_status_endpoints.py    # /status and /components
│   └── test_health_endpoints.py    # Health check endpoints
└── performance/                  # Performance and load tests
    ├── test_response_times.py       # Response time validation
    └── test_concurrent_load.py     # Concurrency and load testing
```

## Test Categories

### Unit Tests (`unit/`)
- **QueryAnalyzerService**: Service initialization, analysis workflow, error handling
- **Configuration**: YAML/env var loading, validation, defaults
- **Schemas**: Pydantic request/response model validation
- **API Logic**: REST endpoint business logic (mocked dependencies)

### Integration Tests (`integration/`)
- **Service Integration**: Full service lifecycle, health monitoring, metrics
- **Epic1 Integration**: Actual Epic1QueryAnalyzer integration and compatibility
- **Configuration Loading**: End-to-end configuration management
- **Memory/Resource Usage**: Resource efficiency and leak detection

### API Tests (`api/`)
- **Analysis Endpoints**: `/api/v1/analyze`, `/api/v1/batch-analyze`
- **Status Endpoints**: `/api/v1/status`, `/api/v1/components`
- **Health Endpoints**: `/health`, `/health/live`, `/health/ready`
- **Error Handling**: Validation errors, service errors, edge cases

### Performance Tests (`performance/`)
- **Response Times**: Individual request performance targets (<50ms)
- **Concurrent Load**: Multi-threaded request handling
- **Scaling**: Performance under increasing load
- **Stress Testing**: Breaking point identification
- **Endurance**: Sustained load over time

## Running Tests

### Quick Start

```bash
# Run all unit tests
python run_tests.py unit

# Run integration tests
python run_tests.py integration

# Run API tests  
python run_tests.py api

# Run performance tests (excluding slow tests)
python run_tests.py performance

# Run quick smoke tests
python run_tests.py quick

# Run all tests with coverage
python run_tests.py coverage
```

### Advanced Usage

```bash
# Run specific test file
pytest unit/test_analyzer_service.py -v

# Run specific test method
pytest unit/test_analyzer_service.py::TestQueryAnalyzerService::test_initialization -v

# Run tests with markers
pytest -m "not slow" -v

# Run tests matching pattern
pytest -k "analyze" -v

# Run tests in parallel
pytest -n auto

# Generate coverage report
pytest --cov=app --cov-report=html

# Stop on first failure
pytest -x
```

### Using the Test Runner Script

```bash
# Full argument support
python run_tests.py --suite=unit --coverage --verbose --parallel

# Run with specific markers
python run_tests.py --markers="not slow"

# Run tests matching pattern
python run_tests.py --pattern="health"

# Fail fast mode
python run_tests.py --fail-fast
```

## Test Configuration

### Pytest Configuration (`pytest.ini`)
- Test discovery patterns
- Default options and reporting
- Async test support
- Coverage requirements (80% minimum)
- Timeout settings (300s max)

### Fixtures (`conftest.py`)
- **Mock Services**: `mock_epic1_analyzer`, `analyzer_service`
- **Test Data**: `sample_queries`, `analyzer_config`, `expected_response_structure`
- **Performance Targets**: `performance_targets` with 50ms response time requirement
- **FastAPI Testing**: `app`, `client`, `async_client` fixtures
- **Configuration Testing**: `temp_config_file`, `service_settings`

## Key Test Features

### Epic1QueryAnalyzer Integration
- **Mock Integration**: Comprehensive mocking for consistent testing
- **Real Integration**: Optional tests with actual Epic1QueryAnalyzer (when available)
- **Configuration Testing**: Validates Epic1 configuration passes correctly
- **Performance Validation**: Ensures Epic1 integration meets performance targets

### Performance Validation
- **Response Time Targets**: <50ms processing time requirement
- **Concurrency Testing**: Up to 100 concurrent requests
- **Load Testing**: Spike, ramp-up, and sustained load patterns
- **Resource Monitoring**: Memory and CPU usage tracking

### API Compliance
- **OpenAPI Compatibility**: All endpoints match API specification
- **Error Handling**: Proper HTTP status codes and error responses
- **Request Validation**: Pydantic schema validation testing
- **Health Check Standards**: Kubernetes-compatible health endpoints

### Robust Error Handling
- **Service Errors**: Epic1QueryAnalyzer failure scenarios
- **Validation Errors**: Invalid request handling
- **Network Errors**: Timeout and connection failure simulation
- **Resource Errors**: Memory/CPU exhaustion scenarios

## Expected Performance Targets

### Response Times
- **Analyze Endpoint**: <50ms processing time (95th percentile)
- **Status Endpoint**: <500ms response time
- **Health Endpoints**: <100ms response time
- **Batch Processing**: Linear scaling with batch size

### Concurrency
- **Success Rate**: >90% success rate under 10 concurrent requests
- **Degradation**: <5x response time increase under high load
- **Throughput**: >10 requests/second sustained throughput

### Reliability
- **Uptime**: Service remains responsive under load
- **Memory**: <50MB growth over 100 requests
- **Recovery**: Automatic recovery from transient failures

## Test Data

### Sample Queries
- **Simple**: "What is Python?", "Hello world"
- **Medium**: "How to implement binary search algorithm?"
- **Complex**: "Design distributed system with fault tolerance"

### Mock Responses
- **Complexity Levels**: simple, medium, complex
- **Confidence Scores**: 0.0 to 1.0 range
- **Model Recommendations**: Ollama, OpenAI, Mistral models
- **Cost Estimates**: Realistic pricing per model

## Continuous Integration

### Test Execution Phases
1. **Unit Tests**: Fast, isolated component testing
2. **Integration Tests**: Service integration validation
3. **API Tests**: End-to-end API testing
4. **Performance Tests**: Response time and load validation

### Quality Gates
- **Coverage**: Minimum 80% code coverage
- **Performance**: All tests meet performance targets
- **API Compatibility**: All endpoints return expected schemas
- **Error Handling**: Graceful degradation under failure conditions

## Troubleshooting

### Common Issues

1. **Epic1QueryAnalyzer Import Errors**
   ```bash
   # Run tests without Epic1 integration
   pytest -m "not epic1"
   ```

2. **Performance Test Failures**
   ```bash
   # Run without performance tests
   pytest -m "not performance"
   ```

3. **Slow Test Execution**
   ```bash
   # Run tests in parallel
   pytest -n auto
   
   # Skip slow tests
   pytest -m "not slow"
   ```

4. **Memory Issues During Testing**
   ```bash
   # Run tests with memory profiling
   pytest --memray
   ```

### Environment Variables
- `QUERY_ANALYZER_CONFIG_FILE`: Custom config file path
- `QUERY_ANALYZER_LOG_LEVEL`: Set logging level for tests
- `PYTEST_TIMEOUT`: Override default test timeout

## Contributing to Tests

### Adding New Tests
1. Follow existing test patterns and naming conventions
2. Use appropriate fixtures from `conftest.py`
3. Include both positive and negative test cases
4. Add performance validations where applicable
5. Update this README if adding new test categories

### Test Quality Standards
- **Isolation**: Tests should not depend on each other
- **Determinism**: Tests should produce consistent results
- **Performance**: Unit tests should complete quickly (<1s each)
- **Readability**: Clear test names and documentation
- **Maintainability**: Use fixtures and utilities to reduce duplication

### Performance Test Guidelines
- Use realistic test data and scenarios
- Validate both average and worst-case performance
- Include resource usage monitoring
- Set reasonable timeouts for different test types
- Document expected performance characteristics

This comprehensive test suite ensures the Query Analyzer Service meets production quality standards with full Epic1QueryAnalyzer integration, proper API compliance, and robust performance characteristics.