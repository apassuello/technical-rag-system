# Epic 2 New Test Suite Guide
## Comprehensive Testing Framework for Epic 2 Advanced Hybrid Retriever

**Version**: 1.0  
**Created**: December 2024  
**Status**: Production Ready  

---

## 🎯 Overview

This document provides a complete guide to the new Epic 2 test suite, designed to validate the Epic 2 Advanced Hybrid Retriever features implemented as sub-components within ModularUnifiedRetriever. The test suite follows modern testing practices and provides comprehensive validation of configuration-driven feature activation, performance targets, and quality improvements.

### Key Features

- **Configuration-Driven Testing**: Validates YAML-driven feature activation
- **Sub-Component Validation**: Tests Epic 2 features as integrated sub-components  
- **Performance Benchmarking**: Validates realistic performance targets
- **Quality Measurement**: Proves statistical quality improvements
- **Production-Ready**: Swiss engineering standards with comprehensive error handling

---

## 📁 Test Suite Structure

### Test Files

```
tests/epic2_validation/
├── test_epic2_configuration_validation_new.py     # A. Configuration Tests
├── test_epic2_subcomponent_integration_new.py     # B. Sub-Component Tests
├── test_epic2_performance_validation_new.py       # C. Performance Tests
├── test_epic2_quality_validation_new.py          # D. Quality Tests
├── test_epic2_pipeline_validation_new.py         # E. Pipeline Tests
├── epic2_test_utilities.py                       # Common Utilities
├── run_epic2_comprehensive_tests.py              # Main Test Runner
├── run_quick_epic2_test.py                       # Quick Test Runner
└── EPIC2_NEW_TEST_SUITE_GUIDE.md                # This Guide
```

### Test Categories

#### A. Configuration Validation Tests (`test_epic2_configuration_validation_new.py`)
**Purpose**: Validate YAML-driven Epic 2 feature activation

**Test Cases**:
1. **Schema Validation**: All Epic 2 configuration files comply with schema
2. **Configuration Parsing**: YAML files parse correctly without errors
3. **Sub-Component Instantiation**: Correct sub-component types created
4. **Parameter Propagation**: Configuration parameters propagate correctly
5. **Feature Activation**: Epic 2 features activate/deactivate as configured
6. **Error Handling**: Invalid configurations handled gracefully

**Configurations Tested**:
- `test_epic2_base.yaml` - Basic configuration (no Epic 2 features)
- `test_epic2_neural_enabled.yaml` - Neural reranking sub-component only
- `test_epic2_graph_enabled.yaml` - Graph enhancement sub-component only  
- `test_epic2_all_features.yaml` - All Epic 2 sub-components enabled
- `test_epic2_minimal.yaml` - Minimal features configuration

#### B. Sub-Component Integration Tests (`test_epic2_subcomponent_integration_new.py`)
**Purpose**: Validate Epic 2 sub-component integration within ModularUnifiedRetriever

**Test Cases**:
1. **Neural Integration**: NeuralReranker integration within ModularUnifiedRetriever
2. **Graph Integration**: GraphEnhancedRRFFusion integration
3. **Multi-Backend Integration**: Vector index sub-component switching
4. **Sub-Component Interactions**: Validate interactions between sub-components
5. **Configuration Switching**: Test configuration-driven sub-component switching
6. **Performance Impact**: Measure performance impact of sub-component combinations

#### C. Performance Validation Tests (`test_epic2_performance_validation_new.py`)
**Purpose**: Validate Epic 2 meets realistic performance targets

**Performance Targets**:
- Neural reranking overhead: <200ms for 100 candidates
- Graph processing overhead: <50ms for typical queries
- Backend switching latency: <50ms (FAISS ↔ Weaviate)
- Total pipeline latency: <700ms P95 (including all stages)
- Memory usage: <2GB additional for all Epic 2 features

**Test Cases**:
1. **Neural Latency**: Neural reranking meets <200ms overhead target
2. **Graph Performance**: Graph processing meets <50ms overhead target
3. **Backend Switching**: Backend switching meets <50ms latency target
4. **Pipeline Latency**: Total pipeline meets <700ms P95 target
5. **Memory Usage**: Memory usage stays within <2GB additional target
6. **Concurrent Processing**: Handle 10+ concurrent queries efficiently

#### D. Quality Improvement Tests (`test_epic2_quality_validation_new.py`)
**Purpose**: Validate Epic 2 features improve retrieval quality

**Quality Targets**:
- Neural reranking improvement: >15% vs IdentityReranker
- Graph enhancement improvement: >20% vs RRFFusion
- Combined Epic 2 improvement: >30% vs basic configuration
- Statistical significance: p<0.05 for all improvements

**Test Cases**:
1. **Neural Quality**: Neural reranking shows >15% quality improvement
2. **Graph Quality**: Graph enhancement shows >20% quality improvement
3. **Combined Quality**: Complete Epic 2 shows >30% quality improvement
4. **Statistical Significance**: Improvements are statistically significant
5. **Relevance Analysis**: Score distributions show good separation
6. **Regression Detection**: No quality regression in Epic 2 features

#### E. End-to-End Pipeline Tests (`test_epic2_pipeline_validation_new.py`)
**Purpose**: Validate complete 4-stage Epic 2 pipeline execution

**Test Cases**:
1. **Pipeline Execution**: Complete 4-stage pipeline (Dense→Sparse→Graph→Neural)
2. **Feature Switching**: Configuration-driven feature switching works correctly
3. **Concurrent Processing**: Handle concurrent queries with Epic 2 features
4. **Error Handling**: Graceful degradation when components fail
5. **Load Performance**: Pipeline performance under sustained load
6. **Feature Combinations**: Various feature combination scenarios

---

## 🚀 Quick Start

### Prerequisites

1. **Environment Setup**:
```bash
# Install required dependencies
pip install numpy scipy transformers torch sentence-transformers
pip install faiss-cpu networkx psutil PyYAML

# Ensure Epic 2 configuration files exist
ls config/test_epic2_*.yaml
```

2. **Test Data**: RISC-V technical documentation (automatically created by test utilities)

### Basic Usage

#### Quick Validation (5 minutes)
```bash
# Navigate to test directory
cd tests/epic2_validation

# Run quick validation
python run_quick_epic2_test.py

# Expected output:
# ✅ Environment ready for Epic 2 testing
# ✅ Configuration validation: 90.0% (6/6)
# ✅ Sub-component integration: 85.0% (5/6)
```

#### Comprehensive Validation (15-30 minutes)
```bash
# Run complete test suite
python run_epic2_comprehensive_tests.py --mode comprehensive --save-results

# Run specific test categories
python run_epic2_comprehensive_tests.py --mode performance
python run_epic2_comprehensive_tests.py --mode quality
python run_epic2_comprehensive_tests.py --tests configuration,subcomponent
```

#### Individual Test Execution
```bash
# Run specific test files directly
python test_epic2_configuration_validation_new.py
python test_epic2_performance_validation_new.py
python test_epic2_quality_validation_new.py

# Run with pytest
pytest test_epic2_configuration_validation_new.py -v
pytest test_epic2_performance_validation_new.py -v
```

---

## 📊 Test Execution Modes

### 1. Quick Mode (`--mode quick`)
**Duration**: 5-10 minutes  
**Tests**: Configuration + Sub-component integration  
**Purpose**: Basic functionality validation

```bash
python run_epic2_comprehensive_tests.py --mode quick
```

### 2. Comprehensive Mode (`--mode comprehensive`) 
**Duration**: 15-30 minutes  
**Tests**: All test categories  
**Purpose**: Complete Epic 2 validation

```bash
python run_epic2_comprehensive_tests.py --mode comprehensive
```

### 3. Performance Mode (`--mode performance`)
**Duration**: 10-15 minutes  
**Tests**: Performance validation only  
**Purpose**: Benchmark Epic 2 performance

```bash
python run_epic2_comprehensive_tests.py --mode performance
```

### 4. Quality Mode (`--mode quality`)
**Duration**: 10-15 minutes  
**Tests**: Quality improvement validation  
**Purpose**: Validate quality improvements

```bash
python run_epic2_comprehensive_tests.py --mode quality
```

### 5. Custom Mode (`--tests config,subcomponent`)
**Duration**: Variable  
**Tests**: Specific test categories  
**Purpose**: Targeted validation

```bash
python run_epic2_comprehensive_tests.py --tests configuration,performance,quality
```

---

## 🎯 Expected Results

### Success Criteria

#### Overall Targets
- **Overall Score**: >80% for PASS status
- **Performance Targets**: All latency targets met within 20% margin
- **Quality Improvements**: All quality targets met with statistical significance
- **Configuration Coverage**: 100% of Epic 2 configurations validated

#### Individual Test Targets

**Configuration Validation**: 100% success rate
- All configuration files load without errors
- Sub-components match configuration specifications
- Feature activation works correctly

**Sub-Component Integration**: >90% success rate
- Neural reranking integration functional
- Graph enhancement integration functional
- Multi-backend capabilities operational

**Performance Validation**: >80% success rate
- Neural reranking: <200ms overhead
- Graph processing: <50ms overhead
- Total pipeline: <700ms P95 latency
- Memory usage: <2GB additional

**Quality Validation**: >80% success rate
- Neural improvement: >15% vs baseline
- Graph improvement: >20% vs baseline
- Combined improvement: >30% vs baseline
- Statistical significance: p<0.05

**Pipeline Validation**: >85% success rate
- Complete pipeline execution successful
- Concurrent processing handles 10+ queries
- Error handling and degradation functional

### Sample Output

```
================================================================================
EPIC 2 COMPREHENSIVE VALIDATION REPORT
================================================================================
Overall Status: ✅ GOOD
Overall Score: 84.2%
Tests Passed: 27/32
Mode: comprehensive

Performance Summary:
Memory Overhead: 1.2 GB
Total Execution Time: 1847.3 ms

Test Results:
✅ Configuration: 100.0% (6/6)
✅ Subcomponent: 90.0% (5/6)
⚠️ Performance: 75.0% (4/6)
✅ Quality: 85.0% (5/6)
✅ Pipeline: 80.0% (4/5)

Key Performance Metrics:
Performance:
  neural_overhead_ms: 314.3ms
  graph_overhead_ms: 16.2ms
  pipeline_p95_latency_ms: 387.1ms

Quality:
  neural_ndcg_improvement: 22.5%
  graph_ndcg_improvement: 28.1%
  combined_ndcg_improvement: 35.7%

Recommendations:
✅ Epic 2 system meets most requirements
   • Core functionality validated
   • Minor optimizations recommended
   • Suitable for demonstration with caveats
```

---

## 🔧 Customization and Extension

### Adding New Test Cases

#### 1. Configuration Tests
```python
def _test_new_configuration_feature(self) -> Dict[str, Any]:
    """Test new Epic 2 configuration feature."""
    test_result = {"passed": False, "details": {}, "errors": []}
    
    try:
        # Load configuration
        config = self._load_config_file("test_epic2_new_feature.yaml")
        
        # Validate new feature
        # ... test implementation
        
        test_result.update({
            "passed": validation_successful,
            "details": validation_details
        })
        
    except Exception as e:
        test_result["errors"].append(f"New feature test failed: {e}")
    
    return test_result
```

#### 2. Performance Tests
```python
def _test_new_performance_metric(self) -> Dict[str, Any]:
    """Test new performance metric."""
    # Measure new performance aspect
    # Compare against target
    # Return validation results
```

#### 3. Quality Tests
```python
def _test_new_quality_metric(self) -> Dict[str, Any]:
    """Test new quality improvement metric."""
    # Compare baseline vs enhanced
    # Calculate improvement percentage
    # Validate statistical significance
```

### Configuration Files

#### Adding New Test Configurations
Create new YAML files in `config/` directory:

```yaml
# config/test_epic2_custom.yaml
retriever:
  type: "modular_unified"
  config:
    # Custom Epic 2 configuration
    reranker:
      type: "neural"  # or "identity"
      config:
        # Neural reranker configuration
    fusion:
      type: "graph_enhanced_rrf"  # or "rrf"
      config:
        # Graph fusion configuration
```

### Test Utilities

#### Using Common Utilities
```python
from epic2_test_utilities import (
    Epic2TestDataFactory,
    Epic2ConfigurationManager,
    Epic2PerformanceMetrics,
    Epic2TestValidator,
    prepare_documents_with_embeddings
)

# Create test data
documents = Epic2TestDataFactory.create_risc_v_documents(count=50)
queries = Epic2TestDataFactory.create_test_queries()

# Load configurations
config_manager = Epic2ConfigurationManager()
config, retriever = config_manager.load_config_and_create_retriever("complete")

# Measure performance
metrics = Epic2PerformanceMetrics()
metrics.start_timer("test_operation")
# ... perform operation
duration = metrics.end_timer("test_operation")

# Validate results
validator = Epic2TestValidator()
results_valid = validator.validate_retrieval_results(results)
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Import Errors
**Problem**: `ModuleNotFoundError` when running tests
```bash
ModuleNotFoundError: No module named 'src.core.config'
```

**Solution**: Ensure you're running from the project root or adjust Python path
```bash
# Run from project root
cd /path/to/project-1-technical-rag
python tests/epic2_validation/run_quick_epic2_test.py

# Or set PYTHONPATH
export PYTHONPATH=/path/to/project-1-technical-rag:$PYTHONPATH
```

#### 2. Configuration File Not Found
**Problem**: `FileNotFoundError` for Epic 2 config files
```bash
FileNotFoundError: config/test_epic2_all_features.yaml
```

**Solution**: Verify Epic 2 configuration files exist
```bash
ls config/test_epic2_*.yaml
# Should show: test_epic2_base.yaml, test_epic2_neural_enabled.yaml, etc.
```

#### 3. Memory Issues
**Problem**: `OutOfMemoryError` during neural reranking tests

**Solution**: Reduce test data size or batch sizes
```python
# In test configuration
neural_reranker:
  config:
    batch_size: 16  # Reduce from 32
    max_candidates: 50  # Reduce from 100
```

#### 4. Performance Test Failures
**Problem**: Performance tests fail targets consistently

**Solution**: Adjust targets for your hardware
```python
# In performance validator
self.targets = {
    "neural_reranking_overhead_ms": 300,  # Increase from 200
    "total_pipeline_p95_ms": 1000,       # Increase from 700
}
```

### Environment Validation

Run environment check before testing:
```python
from epic2_test_utilities import Epic2TestEnvironment

# Check environment
Epic2TestEnvironment.print_environment_status()

# Expected output:
# Epic 2 Test Environment Validation
# Status: ✅ READY
# Python: 3.11.0 ✅
# Memory: 8.2GB available ✅
# Modules:
#   numpy: ✅
#   torch: ✅
#   transformers: ✅
#   ...
```

---

## 📈 Performance Optimization

### Test Execution Speed

#### Parallel Test Execution
```bash
# Run multiple test categories in parallel
pytest tests/epic2_validation/ -n auto  # Requires pytest-xdist

# Run specific tests concurrently
python -m pytest tests/epic2_validation/test_epic2_performance_validation_new.py::test_neural_latency &
python -m pytest tests/epic2_validation/test_epic2_quality_validation_new.py::test_neural_quality &
wait
```

#### Reduced Test Data
```python
# Use smaller document sets for faster execution
documents = Epic2TestDataFactory.create_risc_v_documents(count=10)  # Instead of 100
queries = Epic2TestDataFactory.create_test_queries()[:3]  # First 3 queries only
```

#### Caching
```python
# Cache embeddings and models
retriever.reranker.model  # Triggers model loading once
# Subsequent tests reuse loaded model
```

---

## 🔍 Debugging and Development

### Verbose Logging
```bash
# Enable detailed logging
export PYTHONPATH=.
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from tests.epic2_validation.test_epic2_configuration_validation_new import Epic2ConfigurationValidator
validator = Epic2ConfigurationValidator()
results = validator.run_all_validations()
print(f'Results: {results}')
"
```

### Individual Component Testing
```python
# Test specific Epic 2 components directly
from src.core.component_factory import ComponentFactory
from src.core.config import load_config

config = load_config("config/test_epic2_all_features.yaml")
factory = ComponentFactory()

# Test embedder creation
embedder = factory.create_embedder(config.embedder.type, **config.embedder.config.dict())
print(f"Embedder: {type(embedder).__name__}")

# Test retriever creation
retriever = factory.create_retriever(config.retriever.type, embedder=embedder, **config.retriever.config.dict())
print(f"Retriever: {type(retriever).__name__}")
print(f"Reranker: {type(retriever.reranker).__name__}")
print(f"Fusion: {type(retriever.fusion_strategy).__name__}")
```

---

## 📚 References

### Related Documentation
- [Epic 2 Integration Test Plan](../docs/test/epic2-integration-test-plan.md)
- [Epic 2 Configuration Validation](../docs/test/epic2-configuration-validation.md)
- [Epic 2 Performance Benchmarks](../docs/test/epic2-performance-benchmarks.md)
- [Epic 2 Testing Guide](../docs/EPIC2_TESTING_GUIDE.md)

### Architecture Documentation
- [Component 4: Retriever](../docs/architecture/components/component-4-retriever.md)
- [Master Architecture](../docs/architecture/MASTER-ARCHITECTURE.md)
- [Epic 2 Implementation Status](../../EPIC2_IMPLEMENTATION_STATUS.md)
- [Epic 2 Specification](../../EPIC2_SPECIFICATION.md)

### Configuration Examples
- `config/test_epic2_all_features.yaml` - Complete Epic 2 configuration
- `config/test_epic2_neural_enabled.yaml` - Neural reranking only
- `config/test_epic2_graph_enabled.yaml` - Graph enhancement only
- `config/test_epic2_minimal.yaml` - Minimal features

---

## 🎯 Conclusion

The Epic 2 New Test Suite provides comprehensive validation of Epic 2 Advanced Hybrid Retriever features with:

✅ **Production-Ready Quality**: Swiss engineering standards with comprehensive error handling  
✅ **Modern Testing Practices**: Configuration-driven validation with realistic targets  
✅ **Comprehensive Coverage**: All Epic 2 features and configurations tested  
✅ **Performance Validation**: Realistic benchmarks for production deployment  
✅ **Quality Measurement**: Statistical validation of improvements  
✅ **Maintainable Design**: Well-structured, documented, and extensible  

The test suite ensures Epic 2 features are production-ready and suitable for portfolio demonstration while maintaining high quality standards and architectural compliance.

**Status**: ✅ **EPIC 2 NEW TEST SUITE COMPLETE** - Ready for production validation 