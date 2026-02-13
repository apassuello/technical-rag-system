# Scripts Directory

This directory contains various utility scripts organized by purpose for the RAG Portfolio Project.

## Directory Structure

### analysis/
Analysis and diagnostic scripts:
- `dependency_impact_analyzer.py` - Analyzes dependency changes and their impact
- `analyze_corpus_features.py` - Corpus feature analysis
- `threshold_analysis.py` - Threshold optimization analysis

### deployment/
Deployment and build scripts:
- `docker-setup.sh` - Sets up Docker environment
- `validate-docker-setup.sh` - Validates Docker configuration
- `run_tests.sh` - Runs comprehensive test suite
- `test-build-context.sh` - Tests Docker build context

### profiling/
General performance profiling utilities:
- `performance_baseline_profiler.py` - Creates performance baselines

### testing/
Testing utilities and test runners:

#### testing/namespace/
Namespace collision fixes and tests (legacy, may reference archived epics):
- `final_namespace_test.py` - Final namespace validation
- `fix_namespace_collisions.py` - Fixes namespace collisions
- `fix_test_namespace_collisions.py` - Fixes test namespace issues
- `test_namespace_fix.py` - Tests namespace fixes

### Legacy Structure (Preserved)
The following existing directories contain specialized scripts:

### `/demos/`
Demonstration scripts:
- `demo_basic_rag.py` - Basic RAG system demonstration
- `demo_enhanced_rag_comparison.py` - Enhancement comparison demo
- `demo_hybrid_search.py` - Hybrid search capabilities demo

## Usage

Most scripts can be run directly from their directories. Coverage scripts should be run from the project root:

```bash
# Coverage analysis
./scripts/coverage_comprehensive.sh
./scripts/coverage_unit_tests.sh
./scripts/coverage_integration_tests.sh
./scripts/coverage_epic_specific.sh 1  # Epic 1 coverage

# Legacy demos
python scripts/demos/demo_basic_rag.py
```

## Note

- **Production code** is in `/src/` directory
- **Unit tests** are in `/tests/` directory  
- **Scripts** are for development, demo, and analysis purposes