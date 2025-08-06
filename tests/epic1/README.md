# Epic1 Test Organization

This directory contains tests specific to the **Epic1 Query Analyzer architecture**. Epic1 is a multi-model routing system that intelligently selects LLM models based on query complexity analysis.

## 🏗️ Architecture Overview

**Epic1 combines generic components into a specific architecture:**

- **Generic Components** (tested in `tests/unit/`): TechnicalTermManager, SyntacticParser, FeatureExtractor, ComplexityClassifier, ModelRecommender
- **Epic1 Architecture** (tested in `tests/epic1/`): How these components are orchestrated in the Epic1QueryAnalyzer

## 📁 Directory Structure

```
tests/epic1/
├── README.md                           # This file
├── integration/                        # Epic1 architecture integration tests
│   ├── test_epic1_query_analyzer.py    # Epic1QueryAnalyzer orchestrator tests  
│   ├── test_epic1_modular_processor.py # Epic1 + ModularQueryProcessor integration
│   └── test_epic1_end_to_end.py        # Full Epic1 workflow tests
├── regression/                         # Epic1-specific bug fixes
│   └── test_epic1_accuracy_fixes.py    # Tests for Epic1 accuracy improvements
├── smoke/                              # Quick Epic1 health checks
│   └── test_epic1_smoke.py            # Basic Epic1 functionality validation
├── tools/                              # Epic1 development tools
│   ├── debug_clause_detection.py      # Clause detection debugging
│   ├── debug_technical_terms.py       # Technical term analysis
│   ├── debug_syntactic_parser.py      # Syntactic parsing debugging  
│   ├── debug_feature_extractor.py     # Feature extraction analysis
│   └── debug_epic1_workflow.py        # Epic1 workflow debugging
└── validation/                         # Formal Epic1 validation (future)
    ├── test_epic1_accuracy_validation.py    # Statistical accuracy validation
    └── test_epic1_production_readiness.py   # Production deployment validation
```

## 🧪 Test Types

### **Integration Tests** (`integration/`)
Tests how Epic1 components work together in the Epic1 architecture:

- **Epic1QueryAnalyzer Orchestration**: Tests the 5-phase Epic1 pipeline
- **ModularQueryProcessor Integration**: Tests Epic1 with the query processor
- **End-to-End Workflows**: Tests complete Epic1 query routing workflows

**Run Integration Tests:**
```bash
cd tests/epic1/integration
pytest test_epic1_query_analyzer.py -v
pytest test_epic1_modular_processor.py -v
pytest test_epic1_end_to_end.py -v
```

### **Regression Tests** (`regression/`)
Tests Epic1-specific bug fixes and improvements:

- **Accuracy Fixes**: Tests improvements in Epic1 classification accuracy
- **Performance Fixes**: Tests Epic1 performance optimizations

**Run Regression Tests:**
```bash
cd tests/epic1/regression  
pytest test_epic1_accuracy_fixes.py -v
```

### **Smoke Tests** (`smoke/`)
Quick health checks for Epic1 functionality:

- **Basic Functionality**: Can Epic1 classify and route queries?
- **Configuration Loading**: Can Epic1 load its configuration?
- **Component Initialization**: Do all Epic1 components initialize properly?

**Run Smoke Tests:**
```bash
cd tests/epic1/smoke
pytest test_epic1_smoke.py -v
```

### **Development Tools** (`tools/`)
Debugging and analysis tools for Epic1 development:

- **Component Debugging**: Individual component analysis tools
- **Workflow Analysis**: Epic1 pipeline debugging utilities
- **Performance Profiling**: Epic1 performance analysis tools

**Run Debug Tools:**
```bash
cd tests/epic1/tools
python debug_epic1_workflow.py
python debug_clause_detection.py
```

### **Validation Tests** (`validation/`) - **FUTURE**
Formal statistical validation of Epic1 accuracy and production readiness:

- **Statistical Validation**: Cross-validation, confidence intervals
- **Production Readiness**: Load testing, error boundary testing
- **Model Performance**: Comparison with baseline models

## 🎯 Epic1 Success Criteria

### **Current Validated Performance**
Based on `test_epic1_accuracy_fixes.py` results:

| Metric | Target | Achieved | Status |
|--------|--------|----------|---------|
| **Classification Accuracy** | >85% | **100%** | ✅ (3 test queries) |
| **Technical Term Detection** | >80% | **100%** | ✅ (14/14 terms) |
| **Clause Detection** | >90% | **100%** | ✅ (6/6 test cases) |
| **Performance** | <50ms | **0.2ms** | ✅ (P95 across 50 iterations) |
| **Technical Density** | >0.5 | **0.500** | ✅ |

**Overall Success Rate: 80% (4/5 criteria met)**

### **Phase 2 Targets** (Multi-Model Implementation)
- **Cost Reduction**: >40% vs GPT-4 only usage
- **Routing Accuracy**: >90% appropriate model selection  
- **Routing Overhead**: <50ms for routing decision
- **Cost Tracking**: $0.001 accuracy per query
- **Fallback Reliability**: 100% fallback success rate

## 🚀 Running Epic1 Tests

### **Quick Smoke Test**
```bash
cd tests/epic1/smoke
pytest test_epic1_smoke.py -v
```

### **Full Epic1 Test Suite** 
```bash
cd tests/epic1
pytest -v
```

### **Individual Test Categories**
```bash
# Integration tests only
pytest integration/ -v

# Regression tests only  
pytest regression/ -v

# Debug a specific issue
python tools/debug_clause_detection.py
```

### **Performance Validation**
```bash
# Run accuracy fixes test (includes performance measurement)
pytest regression/test_epic1_accuracy_fixes.py -v

# Run Epic1 orchestrator tests (includes latency validation)
pytest integration/test_epic1_query_analyzer.py::TestEpic1QueryAnalyzer::test_latency_target -v
```

## 🔧 Development Workflow

### **Component Development**
1. **Unit test individual components** in `tests/unit/test_[component].py`
2. **Debug component issues** using `tests/epic1/tools/debug_[component].py`
3. **Test Epic1 integration** with `tests/epic1/integration/test_epic1_query_analyzer.py`

### **Epic1 Architecture Changes**
1. **Run smoke tests** to catch basic breakage
2. **Run integration tests** to validate architecture changes  
3. **Run regression tests** to ensure no accuracy/performance loss
4. **Use debug tools** for detailed analysis

### **Before Committing**
```bash
# Run all Epic1 tests
cd tests/epic1 && pytest -v

# Run component unit tests  
cd tests/unit && pytest test_technical_term_manager.py test_syntactic_parser.py test_feature_extractor.py test_complexity_classifier.py test_model_recommender.py -v
```

## 📊 Test Coverage

### **Generic Components** (Unit Tests)
- ✅ `TechnicalTermManager` - Term detection and vocabulary management
- ✅ `SyntacticParser` - Clause detection and syntax analysis  
- ✅ `FeatureExtractor` - Linguistic feature extraction
- ✅ `ComplexityClassifier` - Weighted classification with thresholds
- ✅ `ModelRecommender` - Model selection and cost estimation

### **Epic1 Architecture** (Integration Tests)  
- ✅ `Epic1QueryAnalyzer` - Component orchestration and pipeline
- ✅ `ModularQueryProcessor` integration - Epic1 + query processing
- ✅ End-to-end workflows - Complete Epic1 routing system

### **Epic1 Quality** (Regression Tests)
- ✅ Accuracy improvements - Classification and term detection fixes
- ✅ Performance validation - Latency and throughput measurements

## 🔍 Debugging Epic1 Issues

### **Classification Issues**
```bash
python tests/epic1/tools/debug_epic1_workflow.py
```

### **Component-Specific Issues**
```bash  
python tests/epic1/tools/debug_technical_terms.py    # Vocabulary issues
python tests/epic1/tools/debug_clause_detection.py   # Syntax analysis issues
python tests/epic1/tools/debug_feature_extractor.py  # Feature extraction issues
```

### **Performance Issues**
```bash
pytest tests/epic1/regression/test_epic1_accuracy_fixes.py::test_end_to_end_performance -v
```

## 📈 Future Enhancements

### **Validation Tests** (Planned)
- **Statistical Accuracy Validation**: Cross-validation with larger datasets
- **Production Readiness Testing**: Load testing, concurrent request handling
- **A/B Testing Framework**: Compare Epic1 vs baseline performance

### **Enhanced Tooling** (Planned)  
- **Performance Profiler**: Detailed Epic1 pipeline profiling
- **Accuracy Analyzer**: Statistical analysis of classification performance
- **Cost Calculator**: Epic1 routing cost analysis tools

## 📞 Support

### **Test Issues**
- Check individual component unit tests first: `tests/unit/test_[component].py`
- Use Epic1 debug tools: `tests/epic1/tools/debug_*.py`
- Run Epic1 smoke tests: `tests/epic1/smoke/test_epic1_smoke.py`

### **Epic1 Architecture Issues**
- Review Epic1 integration tests: `tests/epic1/integration/`
- Check Epic1 regression tests: `tests/epic1/regression/`
- Validate with Epic1 end-to-end tests

**The Epic1 test structure separates reusable component testing from Epic1-specific architecture testing, making both more maintainable and the components more reusable.**