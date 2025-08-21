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

## Notes

- This is **early-stage implementation testing**
- Focus on basic functionality rather than production performance
- Use realistic thresholds that indicate clear failures
- Build foundation for future production-grade testing