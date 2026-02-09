# Testing Guide

## Current Test Infrastructure (February 2026)

The project uses plain `pytest` with custom markers for test categorization. Three test tiers provide different levels of validation with different dependency requirements.

### Quick Reference

```bash
# CI-safe validation (no Ollama, no Docker) — ~17s
pytest tests/validation/ -m "validation and not requires_ollama and not requires_weaviate" -v

# Full validation + integration (requires Ollama) — ~2min
pytest tests/integration/ tests/validation/ -v --tb=short

# Unit regression — ~50s
pytest tests/unit/ -q --tb=no

# All tests with coverage — ~3min
pytest tests/unit/ tests/integration/ tests/validation/ --cov=src --cov-report=term-missing --tb=short

# Adapter wiring only (no external deps) — ~3s
pytest tests/validation/test_adapter_wiring.py -v

# Config pipeline matrix only (requires Ollama) — ~90s
pytest tests/validation/test_config_pipelines.py -v
```

### Current Test Counts (February 9, 2026)

| Suite | Total | Passed | Xfailed | Skipped | Time |
|-------|-------|--------|---------|---------|------|
| Integration + Validation | 139 | 131 | 4 | 4 | ~2min |
| CI-safe (no Ollama/Weaviate) | 57 | 55 | 2 | 0 | ~17s |
| Unit regression | 1109 | 1092 | 0 | 10 | ~50s |

### Test Tiers

| Tier | Marker | Dependencies | What it tests |
|------|--------|-------------|---------------|
| **Tier 0** | `validation` only | ML models (sentence-transformers) | Query analyzers, fusion strategies, rerankers, adapter wiring |
| **Tier 1** | `requires_ml, requires_ollama` | + Ollama (llama3.2:3b) | Config pipelines (12 fusion x reranker configs), generators, processors |
| **Tier 2** | `requires_weaviate` | + Docker (Weaviate) | Weaviate vector backend (currently xfail due to v3/v4 API mismatch) |

### Fusion x Reranker Matrix (12 configs, all tested)

|  | identity | semantic | neural |
|---|---|---|---|
| **rrf** | basic_local | rrf_semantic | rrf_neural |
| **weighted** | weighted_identity | weighted_semantic | weighted_neural |
| **score_aware** | score_aware_identity | score_aware_semantic | epic2_score_aware |
| **graph_enhanced** | graph_enhanced_identity | epic2_graph_enhanced | graph_enhanced_neural |

### Pytest Markers

Key markers registered in `pytest.ini`:

- `validation` — Validation tests checking retrieval and answer quality
- `requires_ml` — Requires ML dependencies (torch, transformers, sentence-transformers)
- `requires_ollama` — Requires Ollama service running on localhost:11434
- `requires_weaviate` — Requires Weaviate Docker container on localhost:8180
- `unit`, `component`, `integration` — Standard test layers

### Known Issues (documented as xfail)

1. ModelRecommender.recommend() returns dict, but epic1_query_analyzer accesses .model attribute
2. DomainAwareQueryProcessor.process_query() calls super().process_query() but parent only has process()
3. WeaviateBackend uses weaviate-client v3 API; v4 is installed (needs backend migration)

---

## Legacy Test Runner (August 2025)

The sections below document the legacy `test_runner.py` infrastructure from August 2025. These commands may no longer work. Use the pytest commands above instead.

## Table of Contents
1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Test Runner System](#test-runner-system)
4. [Test Organization](#test-organization)
5. [Running Tests](#running-tests)
6. [Test Suites](#test-suites)
7. [Output Formats](#output-formats)
8. [Diagnostic Analysis](#diagnostic-analysis)
9. [CI/CD Integration](#cicd-integration)
10. [Troubleshooting](#troubleshooting)

## Overview

The RAG Portfolio Project uses a sophisticated test execution system designed specifically for managing Epic-based test organization with enhanced diagnostics and reporting capabilities.

### Key Features
- **Epic-Aware Organization**: Tests organized by Epic (Epic 1: Multi-Model System, Epic 2: Advanced Retrieval)
- **Unified CLI Interface**: Single command interface for all test execution
- **Enhanced Diagnostics**: Intelligent error analysis with actionable recommendations
- **Multiple Output Formats**: Terminal (human-readable) and JSON (machine-readable)
- **Performance Tracking**: Execution time monitoring and performance benchmarks

## Quick Start

### Basic Commands

```bash
# Run smoke tests (quick health check - ~10 seconds)
python test_runner.py smoke

# Run Epic 1 integration tests
python test_runner.py epic1 integration

# Run all Epic 1 tests
python test_runner.py epic1 all

# Generate JSON report
python test_runner.py epic1 unit --format json --output report.json

# List all available test suites
python test_runner.py list

# Validate test configuration
python test_runner.py validate
```

## Test Runner System

### Architecture

The test runner follows a layered architecture:

```
CLI Interface (test_runner.py)
    ↓
Configuration Management (tests/runner/config.py)
    ↓
Test Discovery Engine (tests/runner/discovery.py)
    ↓
Execution Orchestrator (tests/runner/executor.py)
    ↓
PyTest Adapter (tests/runner/adapters/pytest_adapter.py)
    ↓
Reporting System (tests/runner/reporters/)
    ↓
Diagnostic Analysis (tests/runner/diagnostics.py)
```

### Installation

The test runner requires no additional installation beyond the project dependencies:

```bash
# Ensure you're in the project directory
cd project-1-technical-rag

# The test runner is ready to use
python test_runner.py --help
```

## Test Organization

### Directory Structure

```
tests/
├── epic1/                    # Epic 1: Multi-Model System Tests
│   ├── phase2/              # Phase 2 implementation (79 tests)
│   ├── integration/         # Integration tests (26 tests)
│   ├── ml_infrastructure/   # ML components (unit & integration)
│   ├── smoke/              # Quick health checks
│   └── regression/         # Bug fix validation
├── epic2_validation/        # Epic 2: Advanced Retrieval (future)
├── unit/                   # Component unit tests
├── integration/            # System integration tests
├── diagnostic/             # System forensics
├── component/              # Component-specific tests
└── smoke/                  # System-wide smoke tests
```

### Test Categories

| Category | Purpose | Execution Time | When to Run |
|----------|---------|----------------|--------------|
| **Smoke** | Quick health check | ~10s | Every commit |
| **Unit** | Component isolation | ~30s | Before PR |
| **Integration** | Component interaction | ~60s | Before merge |
| **Phase 2** | Multi-model system | ~90s | Epic 1 changes |
| **Regression** | Bug fix validation | ~60s | After fixes |
| **Diagnostic** | System analysis | ~90s | Debugging |

## Running Tests

### Epic 1 Test Execution

Epic 1 tests cover the Multi-Model Answer Generator with Adaptive Routing system.

#### Run All Epic 1 Tests
```bash
# Run complete Epic 1 test suite (includes all phases)
python test_runner.py epic1 all

# Expected output:
# - Total tests: ~150
# - Execution time: ~3 minutes
# - Success rate: >94%
```

#### Run Specific Epic 1 Components
```bash
# Unit tests (ML classifiers, analyzers)
python test_runner.py epic1 unit
# Tests: 34, Time: ~30s

# Integration tests (system orchestration)
python test_runner.py epic1 integration
# Tests: 26, Time: ~60s

# Phase 2 tests (multi-model routing)
python test_runner.py epic1 phase2
# Tests: 79, Time: ~90s

# ML infrastructure tests
python test_runner.py epic1 ml
# Tests: 7, Time: ~45s

# Quick smoke tests
python test_runner.py epic1 smoke
# Tests: 1, Time: ~5s
```

### System-Wide Test Execution

#### Quick Validation
```bash
# Smoke tests across all components
python test_runner.py smoke
# Tests: 4, Time: ~10s, Purpose: Quick health check

# Validate test configuration
python test_runner.py validate
# Checks all test patterns and configuration
```

#### Comprehensive Testing
```bash
# All unit tests
python test_runner.py unit
# Tests: 13, Time: ~60s

# All integration tests
python test_runner.py integration
# Tests: 5, Time: ~90s

# Diagnostic tests
python test_runner.py diagnostic
# Tests: 8, Time: ~90s
```

### Pattern-Based Execution

Run tests matching specific patterns:

```bash
# Run specific test files
python test_runner.py run "tests/epic1/phase2/test_cost_tracker.py"

# Run tests matching pattern
python test_runner.py run "tests/epic1/**/test_*adapter*.py"

# Run with specific markers
python test_runner.py run "tests/**/*.py" --markers epic1,integration
```

### Command-Line Options

#### Global Options
```bash
--config, -c CONFIG     # Path to custom configuration file
--verbose, -v          # Verbose output (default: enabled)
--help, -h            # Show help message
```

#### Execution Options
```bash
--format {terminal,json}  # Output format (default: terminal)
--output FILE            # Save output to file (JSON format)
--fail-fast, -f         # Stop on first failure
--parallel, -p          # Run tests in parallel (where safe)
--capture {yes,no,all}  # Capture output mode
--timeout SECONDS       # Override test timeout
```

#### Examples with Options
```bash
# JSON output with custom file
python test_runner.py epic1 unit --format json --output unit_results.json

# Fail-fast mode for quick feedback
python test_runner.py epic1 all --fail-fast

# Verbose terminal output (default)
python test_runner.py epic1 integration --verbose

# Custom timeout for slow tests
python test_runner.py epic1 phase2 --timeout 300
```

## Test Suites

### Available Test Suites

| Suite | Tests | Time | Description |
|-------|-------|------|-------------|
| **epic1_all** | ~150 | 3min | Complete Epic 1 test suite |
| **epic1_unit** | 34 | 30s | Epic 1 unit tests |
| **epic1_integration** | 26 | 60s | Epic 1 integration tests |
| **epic1_phase2** | 79 | 90s | Multi-model routing tests |
| **epic1_ml** | 7 | 45s | ML infrastructure tests |
| **epic1_smoke** | 1 | 5s | Epic 1 health check |
| **smoke** | 4 | 10s | System smoke tests |
| **unit** | 13 | 60s | All unit tests |
| **integration** | 5 | 90s | All integration tests |
| **diagnostic** | 8 | 90s | System diagnostic tests |
| **component** | 6 | 60s | Component validation |
| **regression** | 1 | 30s | Bug fix validation |

### Suite Configuration

Test suites are configured in `tests/runner/test_config.yaml`:

```yaml
test_suites:
  epic1_unit:
    name: "Epic 1 Unit Tests"
    description: "Unit tests for Epic 1 components"
    patterns:
      - "tests/unit/test_technical_term_manager.py"
      - "tests/unit/test_syntactic_parser.py"
      - "tests/unit/test_feature_extractor.py"
      - "tests/unit/test_complexity_classifier.py"
      - "tests/unit/test_model_recommender.py"
    markers:
      - "epic1"
      - "unit"
    timeout: 300
    parallel: false
```

## Output Formats

### Terminal Output (Default)

Human-readable format with color-coded results:

```
============================================================
                RAG Portfolio Test Execution                
============================================================

Configuration:
  Output Format: terminal
  Verbose: True
  Fail Fast: False

Test Suites: 1 suites scheduled
  • Epic 1 Integration Tests [epic1] (timeout: 600s)

[1/1] Running: Epic 1 Integration Tests (epic1)
    Integration tests for Epic 1 system orchestration
    Patterns: tests/epic1/integration/test_*.py
    
    ✓ PASSED - 26 tests in 54.32s
      26 passed

============================================================
                     ✓ Test Run PASSED                      
============================================================

Summary:
  Total Duration: 60.45s
  Total Tests: 26
  Success Rate: 100.0%
  
Epic Results:
  EPIC1: 100.0% success rate (1/1 suites)

🎉 All tests passed! System is ready.
```

### JSON Output

Machine-readable format for CI/CD integration:

```json
{
  "metadata": {
    "format_version": "2.0",
    "generated_at": "2025-08-15T12:30:44",
    "generator": "RAG Portfolio Enhanced Test Runner"
  },
  "execution": {
    "duration": 60.45,
    "success": true,
    "fail_fast_triggered": false
  },
  "results": {
    "total_tests": 26,
    "passed": 26,
    "failed": 0,
    "skipped": 0,
    "success_rate": 100.0
  },
  "suites": [
    {
      "name": "Epic 1 Integration Tests",
      "duration": 54.32,
      "passed": 26,
      "failed": 0,
      "test_results": [...]
    }
  ],
  "diagnostics": {
    "executive_summary": {
      "total_issues": 0,
      "critical": 0,
      "major": 0,
      "minor": 0
    },
    "component_health": {
      "Epic1AnswerGenerator": "EXCELLENT"
    }
  }
}
```

## Diagnostic Analysis

### Enhanced Error Reporting

When tests fail, the diagnostic engine provides:

1. **Error Categorization**
   - API_ERROR: External service issues
   - LOGIC_ERROR: Test assertion failures
   - IMPORT_ERROR: Module/dependency issues
   - TIMEOUT_ERROR: Performance problems

2. **Root Cause Analysis**
   ```
   🔍 Diagnostic Analysis
   ────────────────────────
   Executive Summary:
     Total Issues: 5
     🔴 Critical Issues: 2 (API authentication)
     🟡 Major Issues: 3 (logic errors)
   
   🚀 Priority Actions:
     1. Configure API keys: OPENAI_API_KEY, MISTRAL_API_KEY
     2. Start Ollama service: ollama serve
     3. Review test expectations in model_recommender.py
   
   ⏱️ Estimated Fix Time: 45 minutes
   ```

3. **Component Health Assessment**
   ```
   🏥 Component Health:
     ❌ Epic1AnswerGenerator: DEGRADED
       Issues: 5 (2 critical, 3 major)
     ✅ AdaptiveRouter: HEALTHY
     ✅ CostTracker: HEALTHY
   ```

### Issue Prioritization

Issues are prioritized by impact:

| Priority | Impact | Fix Time | Action Required |
|----------|--------|----------|-----------------|
| **Critical** | System broken | Immediate | Block deployment |
| **Major** | Feature broken | 1-2 hours | Fix before merge |
| **Minor** | Non-critical | 2-4 hours | Fix in next sprint |
| **Info** | Enhancement | Optional | Nice to have |

## CI/CD Integration

### GitHub Actions Integration

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run smoke tests
        run: python test_runner.py smoke
      
      - name: Run Epic 1 tests
        run: python test_runner.py epic1 all --format json --output results.json
      
      - name: Upload test results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: results.json
```

### Jenkins Integration

```groovy
pipeline {
    agent any
    
    stages {
        stage('Test') {
            steps {
                sh 'python test_runner.py epic1 all --format json --output epic1_results.json'
            }
        }
        
        stage('Report') {
            steps {
                archiveArtifacts artifacts: '*_results.json'
                junit 'test-reports/*.xml'
            }
        }
    }
    
    post {
        always {
            script {
                def results = readJSON file: 'epic1_results.json'
                if (results.results.success_rate < 95) {
                    error("Test success rate below 95%: ${results.results.success_rate}%")
                }
            }
        }
    }
}
```

## Troubleshooting

### Common Issues and Solutions

#### 1. "0 tests found" Error
```bash
# Validate test patterns
python test_runner.py validate

# Check specific pattern
python test_runner.py run "tests/epic1/**/*.py" --verbose
```

#### 2. Import Errors
```bash
# Ensure you're in the project root
cd project-1-technical-rag

# Run with proper Python path
PYTHONPATH=. python test_runner.py epic1 unit
```

#### 3. API Key Issues
```bash
# Set environment variables for Epic 1 tests
export OPENAI_API_KEY="your-key"
export MISTRAL_API_KEY="your-key"

# Or use mock mode
export EPIC1_USE_MOCKS=true
python test_runner.py epic1 phase2
```

#### 4. Timeout Issues
```bash
# Increase timeout for slow tests
python test_runner.py epic1 phase2 --timeout 600

# Or run specific slow tests separately
python test_runner.py run "tests/epic1/ml_infrastructure/**/*.py" --timeout 900
```

### Debug Mode

Enable detailed debugging:

```bash
# Maximum verbosity
python test_runner.py epic1 unit --verbose --capture no

# Debug test discovery
python test_runner.py validate --verbose

# Debug specific test
pytest tests/epic1/phase2/test_cost_tracker.py -vvs
```

### Performance Tips

1. **Use Smoke Tests First**: Quick validation before comprehensive testing
2. **Run in Parallel**: Use `--parallel` for unit tests (not integration)
3. **Fail Fast**: Use `--fail-fast` during development for quick feedback
4. **Targeted Testing**: Run specific components rather than full suites

## Coverage Monitoring

### Coverage Analysis Commands

The test runner includes comprehensive coverage monitoring capabilities:

```bash
# Run tests with coverage analysis
python test_runner.py epic1 unit --coverage

# Generate coverage reports
python test_runner.py coverage run unit
python test_runner.py coverage report --format html

# Compare coverage between runs
python test_runner.py coverage diff baseline.json current.json
```

### Coverage Scripts

Specialized coverage scripts for different scenarios:

```bash
# Unit test coverage analysis
./run_tests.sh coverage unit

# Integration test coverage analysis
./run_tests.sh coverage integration

# Comprehensive coverage analysis
./run_tests.sh coverage comprehensive

# Epic-specific coverage analysis
./run_tests.sh coverage epic1
./run_tests.sh coverage epic8
```

### Coverage Dashboard

Access the interactive coverage dashboard:

```bash
# Generate HTML coverage dashboard
python scripts/generate_coverage_dashboard.py coverage.json -o dashboard.html

# View dashboard
open reports/coverage/dashboard.html
```

### Coverage Achievements (August 2025)

| Component Type | Target Coverage | **ACHIEVED STATUS** | Achievement |
|----------------|----------------|---------------------|-------------|
| **Epic 1 Multi-Model** | 80% | **80-99% ACHIEVED** ✅ | Stable |
| **Epic 2 Calibration** | 75% | **97.4% ACHIEVED** ✅ | Comprehensive |  
| **Core Modules** | 85% | **85%+ ACHIEVED** ✅ | Robust Infrastructure |
| **Retrieval Systems** | 75% | **75-90% ACHIEVED** ✅ | Complete Coverage |
| **Training Pipeline** | 70% | **99.5% ACHIEVED** ✅ | Validated Accuracy |
| **Epic 8 Services** | 70% | **93.3% ACHIEVED** ✅ | Specification Compliant |

For detailed coverage standards, see [COVERAGE_STANDARDS.md](COVERAGE_STANDARDS.md).

## Best Practices

### Test Development

1. **Follow Naming Conventions**
   - Test files: `test_*.py`
   - Test classes: `TestClassName`
   - Test methods: `test_specific_behavior`

2. **Use Appropriate Markers**
   ```python
   @pytest.mark.epic1
   @pytest.mark.integration
   @pytest.mark.slow
   def test_complex_integration():
       pass
   ```

3. **Organize by Epic**
   - Place Epic-specific tests in `tests/epic1/` or `tests/epic2/`
   - Use consistent directory structure

### Continuous Testing

1. **Pre-Commit**: Run smoke tests
   ```bash
   python test_runner.py smoke  # ~10 seconds
   ```

2. **Pre-Push**: Run relevant Epic tests
   ```bash
   python test_runner.py epic1 unit  # ~30 seconds
   ```

3. **Pre-Merge**: Run comprehensive tests
   ```bash
   python test_runner.py epic1 all  # ~3 minutes
   ```

4. **Nightly**: Run full test suite
   ```bash
   python test_runner.py epic1 all --format json --output nightly.json
   python test_runner.py diagnostic
   ```

## Advanced Usage

### Custom Test Configuration

Create custom test suite configurations:

```yaml
# custom_tests.yaml
test_suites:
  my_custom_suite:
    name: "Custom Test Suite"
    patterns:
      - "tests/my_tests/**/*.py"
    markers:
      - "custom"
    timeout: 300
```

Run with custom configuration:
```bash
python test_runner.py --config custom_tests.yaml run my_custom_suite
```

### Programmatic Usage

```python
from tests.runner.cli import TestRunner

# Create runner instance
runner = TestRunner()

# Run tests programmatically
results = runner.run_suite("epic1_integration", format="json")

# Access results
print(f"Success rate: {results['results']['success_rate']}%")
print(f"Total tests: {results['results']['total_tests']}")
```

### Integration with IDE

#### VS Code
```json
// .vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Run Epic 1 Tests",
      "type": "shell",
      "command": "python test_runner.py epic1 all",
      "group": {
        "kind": "test",
        "isDefault": true
      }
    }
  ]
}
```

#### PyCharm
Configure as External Tool:
- Program: `python`
- Arguments: `test_runner.py epic1 all`
- Working directory: `$ProjectFileDir$`

## Conclusion

The test runner provides a comprehensive, Epic-aware testing solution with enhanced diagnostics and reporting. Use it to:

- Quickly validate system health with smoke tests
- Run targeted Epic-specific test suites
- Generate detailed reports for CI/CD integration
- Diagnose and fix test failures efficiently

For additional help:
```bash
python test_runner.py --help
python test_runner.py epic1 --help
```