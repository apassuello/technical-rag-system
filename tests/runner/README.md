# RAG Portfolio Test Execution System

A comprehensive test execution framework built on pytest with Epic-aware enhancements, providing a simple CLI interface for running various test suites with enhanced reporting.

## 🏗️ Architecture Overview

### Design Philosophy: Pragmatic Enhancement
This system enhances the existing pytest infrastructure rather than replacing it. It provides:
- **Lightweight CLI wrapper** around pytest with Epic-aware commands  
- **Enhanced reporting** that builds on pytest's output
- **Minimal adapters** only where absolutely necessary
- **Configuration-driven test suites** using existing patterns

### Architecture Components

```
tests/runner/
├── cli.py                    # Main CLI interface
├── config.py                 # Configuration management  
├── discovery.py              # Test discovery engine
├── executor.py               # Test execution orchestrator
├── adapters/                 # Test execution adapters
│   ├── base.py              # Abstract adapter interface
│   └── pytest_adapter.py   # PyTest execution adapter
├── reporters/               # Enhanced reporting system
│   ├── base.py             # Abstract reporter interface
│   ├── terminal.py         # Rich terminal output
│   └── json_reporter.py    # Structured JSON reports
└── test_config.yaml        # Test suite definitions
```

### Key Design Decisions

1. **pytest First**: Built on pytest's robust discovery and execution
2. **Epic Awareness**: Specialized support for Epic 1 multi-model routing tests  
3. **Configuration Driven**: YAML-based test suite definitions
4. **Multiple Output Formats**: Terminal and JSON reporting
5. **Extensible**: Plugin-based architecture for future enhancements

## 🚀 Getting Started

### Basic Usage

```bash
# Run all Epic 1 tests
python test_runner.py epic1 all

# Run Epic 1 unit tests only
python test_runner.py epic1 unit

# Run quick smoke tests  
python test_runner.py smoke

# List available test suites
python test_runner.py list

# Generate JSON report
python test_runner.py epic1 unit --format json --output epic1_unit_report.json
```

### Shell Script Shortcuts

```bash
# Quick smoke tests
./run_tests.sh quick

# Full Epic 1 test suite  
./run_tests.sh epic1

# Show available commands
./run_tests.sh help
```

## 📋 Available Test Suites

### Epic 1 Test Suites
- **epic1_unit**: Unit tests for Epic 1 components (classifiers, analyzers, etc.)
- **epic1_integration**: Integration tests for Epic 1 system orchestration
- **epic1_phase2**: Multi-model routing and cost tracking tests
- **epic1_ml_infrastructure**: ML model training and infrastructure tests
- **epic1_all**: Complete Epic 1 test suite including all phases

### General Test Suites
- **smoke**: Quick health checks across all system components
- **regression**: Bug fix validation across all components
- **integration**: End-to-end integration testing
- **unit**: Complete unit test suite for all components
- **diagnostic**: System diagnostic and forensic tests
- **component**: Individual component validation tests
- **system**: Full system validation tests

## 🎯 Epic-Specific Features

### Epic 1 Multi-Model System
The test runner provides specialized support for Epic 1's multi-model routing architecture:

```bash
# Run Epic 1 unit tests
python test_runner.py epic1 unit

# Run Epic 1 Phase 2 (multi-model) tests
python test_runner.py epic1 phase2

# Run complete Epic 1 test suite
python test_runner.py epic1 all
```

### Epic Results Reporting
The terminal reporter provides Epic-specific summaries:

```
Epic Results:
  EPIC1: 85.7% success rate (6/7 suites)
```

## 📊 Output Formats

### Terminal Output (Default)
Rich terminal output with:
- Color-coded status indicators
- Progress tracking with suite counters
- Epic-specific result summaries
- Failed test details with smart truncation
- Real-time execution feedback

### JSON Output
Structured JSON reports with:
- Complete execution metadata
- Individual test results with timing
- Epic-specific result aggregation
- CI/CD integration ready format

Example:
```bash
python test_runner.py epic1 unit --format json --output epic1_report.json
```

## ⚙️ Configuration

### Test Suite Configuration
Test suites are defined in `tests/runner/test_config.yaml`:

```yaml
suites:
  epic1_unit:
    name: "Epic 1 Unit Tests"
    description: "Unit tests for Epic 1 components"
    patterns:
      - "tests/unit/test_*epic*.py"
      - "tests/unit/test_technical_term_manager.py"
    markers:
      - "epic1"
      - "unit"
    epic: "epic1"
    timeout: 300
```

### Custom Configuration
```bash
python test_runner.py --config custom_config.yaml epic1 all
```

## 🔧 Advanced Usage

### Custom Test Patterns
```bash
python test_runner.py run "tests/epic1/**/*.py" --markers epic1,integration
```

### Validation and Debugging
```bash
# Validate test setup
python test_runner.py validate

# List all available suites
python test_runner.py list
```

### Parallel Execution
```bash
python test_runner.py epic1 unit --parallel
```

### Fail-Fast Mode
```bash
python test_runner.py epic1 all --fail-fast
```

## 🏗️ Technical Implementation

### Test Discovery
The discovery engine:
1. Parses test suite configurations
2. Finds files matching glob patterns  
3. Infers markers from file paths and naming
4. Creates executable test plans

### Execution Orchestration
The orchestrator:
1. Coordinates test execution across adapters
2. Manages resource cleanup and timeouts
3. Provides progress tracking
4. Handles error recovery and reporting

### Adapter System
The pytest adapter:
1. Builds pytest commands with appropriate options
2. Handles optional plugins (timeout, parallel, JSON reporting)
3. Parses output into structured results
4. Provides fallback text parsing when JSON unavailable

### Reporting System
The reporting system:
1. Provides real-time execution feedback
2. Aggregates results across test suites
3. Generates Epic-specific summaries
4. Supports multiple output formats

## 🎯 Epic 1 Integration

### Multi-Model Test Support
The system provides specialized support for Epic 1's multi-model routing:

- **Unit Tests**: Individual component testing (classifiers, analyzers)
- **Integration Tests**: System orchestration validation  
- **Phase 2 Tests**: Multi-model routing and cost tracking
- **ML Infrastructure**: Model training and infrastructure validation

### Performance Tracking
Epic 1 specific performance metrics:
- Query complexity classification accuracy
- Model routing decision accuracy  
- Cost tracking precision
- Response time measurements

## 🚀 Future Enhancements

### Planned Features
- **Epic 2 Support**: Extend for Epic 2 advanced retrieval system
- **Performance Benchmarking**: Automated performance regression detection
- **Test Result Comparison**: Compare results across runs
- **Custom Markers**: User-defined test categorization
- **Remote Execution**: Support for distributed test execution

### Plugin Architecture
The system is designed for extension:
- Custom adapters for different test frameworks
- Additional reporters (HTML, XML, database)
- Test result analyzers and trend tracking
- Integration with CI/CD systems

## 📖 Examples

### Complete Epic 1 Validation
```bash
# Run complete Epic 1 test suite with JSON report
python test_runner.py epic1 all --format json --output epic1_validation.json

# Quick Epic 1 health check
python test_runner.py epic1 unit

# Epic 1 Phase 2 multi-model testing
python test_runner.py epic1 phase2
```

### CI/CD Integration
```bash
# Fail-fast smoke test for CI
python test_runner.py smoke --fail-fast

# Complete system validation with JSON output
python test_runner.py integration --format json --output ci_results.json
```

### Development Workflow
```bash
# Quick validation during development
./run_tests.sh quick

# Component-specific testing
python test_runner.py run "tests/unit/test_complexity_classifier.py"

# Regression testing after bug fixes  
python test_runner.py regression
```

## 🎉 Success Metrics

The system successfully provides:
- **✅ Epic-aware test execution** with specialized Epic 1 support
- **✅ Enhanced reporting** with rich terminal and JSON output
- **✅ Configuration-driven suites** with 14 predefined test suites
- **✅ Robust execution** built on pytest's proven foundation
- **✅ Extensible architecture** ready for Epic 2 and future enhancements

The implementation demonstrates a pragmatic approach to test framework enhancement, providing significant value while maintaining simplicity and reliability.