# Testing Section for README.md

## Testing

The project includes a comprehensive test suite with Epic-aware organization and enhanced diagnostics.

### Quick Start

```bash
# Run quick health check (~10 seconds)
python test_runner.py smoke

# Run Epic 1 tests
python test_runner.py epic1 all        # All Epic 1 tests (~3 minutes)
python test_runner.py epic1 unit       # Unit tests only (~30 seconds)
python test_runner.py epic1 integration # Integration tests (~60 seconds)

# Generate test report
python test_runner.py epic1 all --format json --output report.json

# List available test suites
python test_runner.py list
```

### Test Organization

```
tests/
├── epic1/          # Epic 1: Multi-Model System (150+ tests)
│   ├── phase2/     # Multi-model routing tests
│   ├── integration/# System integration tests
│   └── unit/       # Component unit tests
├── unit/           # Core component tests
├── integration/    # System-wide integration
└── diagnostic/     # System forensics
```

### Test Categories

| Type | Command | Duration | Purpose |
|------|---------|----------|---------|
| Smoke | `test_runner.py smoke` | ~10s | Quick health check |
| Unit | `test_runner.py epic1 unit` | ~30s | Component testing |
| Integration | `test_runner.py epic1 integration` | ~60s | System integration |
| Full Epic 1 | `test_runner.py epic1 all` | ~3min | Complete validation |

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Run tests
  run: |
    python test_runner.py smoke
    python test_runner.py epic1 all --format json --output results.json
```

### Key Features

- **Epic-Aware**: Tests organized by Epic (Epic 1: Multi-Model, Epic 2: Advanced Retrieval)
- **Enhanced Diagnostics**: Intelligent error analysis with fix recommendations
- **Multiple Formats**: Terminal (human) and JSON (CI/CD) output
- **Performance Tracking**: Execution time monitoring and benchmarks

For detailed testing documentation, see [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md).