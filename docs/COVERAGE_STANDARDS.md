# Test Coverage Standards and Guidelines

## Overview

This document defines the test coverage standards, monitoring processes, and improvement guidelines for the RAG Portfolio Project. Test coverage is a key quality metric that helps ensure the reliability and maintainability of our codebase.

## Coverage Targets

### Overall Project Targets

| Component Type | Target Coverage | Minimum Coverage | Description |
|----------------|----------------|------------------|-------------|
| **Core Modules** | 85% | 70% | Essential system components (src/core/) |
| **Component Libraries** | 75% | 60% | Reusable components (src/components/) |
| **Business Logic** | 80% | 65% | Application-specific logic |
| **Utilities** | 70% | 50% | Helper functions and utilities |
| **Integration Points** | 90% | 75% | External service adapters |

### Module-Specific Targets

#### Core Modules (`src/core/`)
- **platform_orchestrator.py**: 80% (currently ~8%)
- **component_factory.py**: 85% (currently ~19%)
- **config.py**: 80% (currently ~20%)
- **interfaces.py**: 90% (currently ~55%)

#### Components (`src/components/`)
- **generators/**: 75% (currently ~14%)
- **processors/**: 70% (currently ~22%)
- **embedders/**: 70% (currently ~19%)
- **retrievers/**: 65% (currently ~0.4%)
- **query_processors/**: 70% (currently ~14%)

## Coverage Quality Gates

### Development Gates
- **Pre-commit**: New code must have >70% coverage
- **Pull Request**: Overall coverage cannot decrease
- **Merge**: All critical paths must be covered

### Deployment Gates
- **Staging**: Overall coverage >60%
- **Production**: Overall coverage >70%
- **Release**: Overall coverage >75%

## Coverage Measurement Tools

### Command Line Tools

```bash
# Basic coverage analysis
pytest tests/unit/ --cov=src --cov-report=term-missing

# HTML coverage report
pytest tests/unit/ --cov=src --cov-report=html:htmlcov

# JSON coverage for automation
pytest tests/unit/ --cov=src --cov-report=json:coverage.json

# Comprehensive coverage analysis
./scripts/coverage_comprehensive.sh
```

### Test Runner Integration

```bash
# Using enhanced test runner with coverage
python test_runner.py epic1 unit --coverage
python test_runner.py coverage run unit
python test_runner.py coverage report --format html
```

### Coverage Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `scripts/coverage_unit_tests.sh` | Unit test coverage | `./scripts/coverage_unit_tests.sh` |
| `scripts/coverage_integration_tests.sh` | Integration coverage | `./scripts/coverage_integration_tests.sh` |
| `scripts/coverage_comprehensive.sh` | Full analysis | `./scripts/coverage_comprehensive.sh` |
| `scripts/coverage_epic_specific.sh` | Epic-focused coverage | `./scripts/coverage_epic_specific.sh 1` |

## Coverage Monitoring

### Automated Dashboard

The project includes an automated coverage dashboard that provides:

- **Real-time coverage metrics** by module
- **Visual coverage trends** over time
- **Actionable improvement recommendations**
- **Coverage comparison** between runs

Access the dashboard at: `reports/coverage/dashboard.html`

Generate dashboard:
```bash
python scripts/generate_coverage_dashboard.py coverage.json -o dashboard.html
```

### Coverage Reports

#### Daily Coverage Monitoring
- Automated coverage reports generated nightly
- Coverage trends tracked in `reports/coverage/`
- Dashboard updated with latest metrics

#### Coverage Alerts
- Alert when overall coverage drops below 65%
- Alert when any core module drops below minimum threshold
- Alert when new code has <50% coverage

## Coverage Improvement Guidelines

### 1. Prioritization Strategy

**High Priority (Fix Immediately)**
- Core modules below 60% coverage
- New features with <50% coverage
- Critical bug-fix paths without tests

**Medium Priority (Next Sprint)**
- Component modules below 50% coverage
- Integration points without tests
- Complex algorithms without unit tests

**Low Priority (Future Improvement)**
- Utility functions below 70% coverage
- Legacy code refactoring opportunities
- Documentation and example coverage

### 2. Testing Strategy by Coverage Level

#### 0-25% Coverage (Critical)
1. **Add basic unit tests** for core functionality
2. **Cover main execution paths** (happy path)
3. **Test error handling** for critical failures
4. **Add integration tests** for external dependencies

#### 25-50% Coverage (Poor)
1. **Expand unit test coverage** to edge cases
2. **Add negative test cases** (error conditions)
3. **Test configuration variations**
4. **Add performance regression tests**

#### 50-75% Coverage (Fair)
1. **Test complex conditional logic**
2. **Add integration test scenarios**
3. **Test concurrency and race conditions**
4. **Add property-based tests** for algorithms

#### 75%+ Coverage (Good)
1. **Focus on quality over quantity**
2. **Add mutation testing** to verify test quality
3. **Performance and load testing**
4. **End-to-end workflow testing**

### 3. Code Coverage Best Practices

#### What to Test
- **All public interfaces** and APIs
- **Complex business logic** and algorithms
- **Error handling** and edge cases
- **Configuration loading** and validation
- **External service integrations**

#### What Not to Over-Test
- **Simple getters/setters** without logic
- **Framework boilerplate** code
- **Generated code** and schemas
- **Trivial utility functions**

#### Coverage Exclusions
Use coverage pragmas to exclude:
```python
def debug_helper():  # pragma: no cover
    """Development-only debugging function."""
    pass

if TYPE_CHECKING:  # pragma: no cover
    from typing import Optional
```

## Integration with CI/CD

### GitHub Actions Integration

```yaml
# .github/workflows/coverage.yml
name: Coverage Analysis

on: [push, pull_request]

jobs:
  coverage:
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
          pip install pytest-cov
      
      - name: Run coverage analysis
        run: |
          python test_runner.py coverage run all --fail-under=65
      
      - name: Generate dashboard
        run: |
          python scripts/generate_coverage_dashboard.py coverage.json
      
      - name: Upload coverage reports
        uses: actions/upload-artifact@v2
        with:
          name: coverage-report
          path: |
            coverage.json
            htmlcov/
            reports/coverage/dashboard.html
```

### Jenkins Integration

```groovy
pipeline {
    agent any
    
    stages {
        stage('Coverage Analysis') {
            steps {
                sh 'python test_runner.py coverage run all --format json --output coverage.json'
                sh 'python scripts/generate_coverage_dashboard.py coverage.json'
            }
            
            post {
                always {
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }
    }
    
    post {
        always {
            script {
                def coverage = readJSON file: 'coverage.json'
                def totalPercent = coverage.totals.percent_covered
                
                if (totalPercent < 65) {
                    error("Coverage ${totalPercent}% below minimum 65%")
                }
            }
        }
    }
}
```

## Configuration Files

### pytest.ini
```ini
[tool:pytest]
addopts = 
    --cov=src
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=json:coverage.json
    --cov-fail-under=70
```

### .coveragerc
```ini
[run]
source = src
omit = 
    tests/*
    src/legacy/*
    src/debug/*

[report]
fail_under = 70
show_missing = True
skip_covered = False

exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

## Coverage Troubleshooting

### Common Issues

#### 1. "Coverage data not found"
```bash
# Solution: Ensure tests run with coverage enabled
python -m pytest --cov=src tests/
```

#### 2. "Low coverage despite good tests"
```bash
# Check if all test files are being discovered
pytest --collect-only tests/

# Verify coverage configuration
coverage report --show-missing
```

#### 3. "Coverage not matching expectations"
```bash
# Debug coverage measurement
coverage debug data
coverage debug sys
```

### Performance Optimization

#### Reduce Coverage Overhead
- Use `--cov-append` for incremental coverage
- Exclude large test data files from coverage
- Use `--cov-branch` only when needed

#### Parallel Test Execution
```bash
# Run tests in parallel with coverage
pytest -n auto --cov=src --cov-report=html
```

## Coverage Reporting Standards

### Report Format Requirements

#### Executive Summary
- Overall coverage percentage
- Total lines of code
- Coverage trend (vs previous run)
- Quality gate status

#### Detailed Analysis
- Module-by-module coverage breakdown
- Uncovered lines identification
- Critical path coverage verification
- Test gap analysis

#### Action Items
- Prioritized improvement recommendations
- Specific files/functions needing tests
- Coverage improvement roadmap
- Quality gate compliance status

### Reporting Schedule
- **Daily**: Automated coverage monitoring
- **Weekly**: Coverage trend analysis
- **Monthly**: Coverage quality review
- **Release**: Comprehensive coverage audit

## Success Metrics

### Key Performance Indicators

1. **Coverage Growth Rate**: +5% per month
2. **Coverage Stability**: <2% variance week-over-week
3. **Quality Gate Compliance**: >95% pass rate
4. **Critical Path Coverage**: 100% for core workflows

### Quarterly Reviews
- Coverage target achievement assessment
- Test quality evaluation (mutation testing)
- Coverage tooling effectiveness review
- Process improvement recommendations

## Getting Help

### Documentation
- [Testing Guide](TESTING_GUIDE.md) - Complete testing documentation
- [pytest documentation](https://docs.pytest.org/) - pytest framework
- [coverage.py documentation](https://coverage.readthedocs.io/) - coverage tool

### Commands Quick Reference
```bash
# Generate comprehensive coverage report
./run_tests.sh coverage comprehensive

# Generate coverage dashboard
python scripts/generate_coverage_dashboard.py coverage.json

# Compare coverage between runs
python test_runner.py coverage diff baseline.json current.json

# View detailed coverage report
coverage report --show-missing
coverage html
open htmlcov/index.html
```

---

**Last Updated**: August 22, 2025  
**Document Version**: 1.0  
**Next Review**: September 22, 2025