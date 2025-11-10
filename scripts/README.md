# Scripts Directory

This directory contains various utility scripts organized by purpose for the Epic 8 Cloud-Native RAG Platform.

## Directory Structure

### analysis/
Analysis and diagnostic scripts:
- `dependency_impact_analyzer.py` - Analyzes dependency changes and their impact
- `analyze_corpus_features.py` - Corpus feature analysis
- `threshold_analysis.py` - Threshold optimization analysis

### deployment/
Deployment and build scripts for Epic 8 services:
- `build-services.sh` - Builds all Epic 8 Docker services
- `docker-setup.sh` - Sets up Docker environment
- `validate-docker-setup.sh` - Validates Docker configuration
- `validate-epic8-build.sh` - Validates Epic 8 service builds
- `run_tests.sh` - Runs comprehensive test suite
- `test-build-context.sh` - Tests Docker build context

### epic8/
Epic 8 specific performance and monitoring scripts:
- `epic8_comprehensive_performance_profiler.py` - Comprehensive performance profiling
- `epic8_performance_profiler.py` - Basic performance profiling
- `redis_lifecycle_performance_analysis.py` - Redis performance analysis

### profiling/
General performance profiling utilities:
- `performance_baseline_profiler.py` - Creates performance baselines

### testing/
Testing utilities and test runners:
- `run_epic8_tests_isolated.py` - Runs Epic 8 tests in isolation
- `test_runner.py` - Main test runner utility

#### testing/namespace/
Namespace collision fixes and tests:
- `final_namespace_test.py` - Final namespace validation
- `fix_namespace_collisions.py` - Fixes namespace collisions
- `fix_test_namespace_collisions.py` - Fixes test namespace issues
- `test_namespace_fix.py` - Tests namespace fixes

### Legacy Structure (Preserved)
The following existing directories contain specialized scripts:

### `/demos/`
Production-ready demonstration scripts:
- `demo_basic_rag.py` - Basic RAG system demonstration  
- `demo_enhanced_rag_comparison.py` - Enhancement comparison demo
- `demo_hybrid_search.py` - Hybrid search capabilities demo

## Usage

Most scripts can be run directly from their directories. For deployment scripts, run from the project root:

```bash
# Epic 8 deployment
./scripts/deployment/build-services.sh
python scripts/epic8/epic8_performance_profiler.py
python scripts/testing/run_epic8_tests_isolated.py

# Legacy demos
python scripts/demos/demo_basic_rag.py
```

## Note

- **Production code** is in `/src/` directory
- **Unit tests** are in `/tests/` directory  
- **Scripts** are for development, demo, and analysis purposes