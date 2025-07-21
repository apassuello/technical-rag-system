# Epic 2 Test Specification
## Comprehensive Testing Framework for Advanced Hybrid Retriever Features

**Version**: 2.0  
**Date**: July 16, 2025  
**Status**: Production Ready  
**References**: [MASTER-ARCHITECTURE.md](../architecture/MASTER-ARCHITECTURE.md)

---

## 📋 Executive Summary

This document defines the comprehensive testing framework for Epic 2 Advanced Hybrid Retriever features implemented as **ModularUnifiedRetriever sub-components**. The specification covers configuration-driven testing, component-specific validation, performance benchmarking, and quality measurement requirements for production deployment.

### Epic 2 Implementation Architecture

Epic 2 is implemented as **enhanced sub-components within ModularUnifiedRetriever**:
- **Neural Reranking**: `NeuralReranker` sub-component (vs `IdentityReranker`)  
- **Graph Enhancement**: `GraphEnhancedRRFFusion` sub-component (vs `RRFFusion`)
- **Multi-Backend**: `WeaviateIndex` + `FAISSIndex` support
- **Configuration**: YAML-driven feature activation through ModularUnifiedRetriever config

### Testing Philosophy

Epic 2 testing validates **configuration-driven feature activation** rather than standalone component testing. Tests verify that YAML configuration changes enable advanced capabilities within the existing 6-component architecture.

---

## 🎯 Test Scope and Requirements

### In Scope
- YAML-driven Epic 2 feature activation
- ModularUnifiedRetriever sub-component validation  
- Neural reranking performance and quality
- Graph-enhanced fusion effectiveness
- Multi-backend switching capability
- Configuration validation and error handling
- Component isolation testing with integration context

### Out of Scope
- Standalone Epic 2 component testing (components don't exist independently)
- Traditional component factory testing for Epic 2 (integrated within ModularUnifiedRetriever)
- UI testing (no Epic 2 UI components)

### Epic 2 Architecture Testing Model

```
ModularUnifiedRetriever (Base Component)
├── Vector Index Sub-component
│   ├── FAISSIndex (basic)
│   └── WeaviateIndex (Epic 2)
├── Sparse Retriever Sub-component
│   └── BM25Retriever (shared)
├── Fusion Strategy Sub-component
│   ├── RRFFusion (basic)
│   └── GraphEnhancedRRFFusion (Epic 2)
└── Reranker Sub-component
    ├── IdentityReranker (basic)
    └── NeuralReranker (Epic 2)
```

---

## 🏗️ Test Categories and Structure

### 1. Configuration Validation Tests

#### Purpose
Verify Epic 2 features activate correctly through YAML configuration changes.

#### Test Files
- `test_epic2_configuration_validation_new.py` - Main configuration testing
- Configuration files in `config/test_epic2_*.yaml`

#### Test Cases
1. **Schema Validation**: All Epic 2 configuration files comply with schema
2. **Configuration Parsing**: YAML files parse correctly without errors
3. **Sub-Component Instantiation**: Correct sub-component types created
4. **Parameter Propagation**: Configuration parameters propagate correctly
5. **Feature Activation**: Epic 2 features activate/deactivate as configured
6. **Error Handling**: Invalid configurations handled gracefully

#### Configuration Files Tested
- `test_epic2_base.yaml` - Basic configuration (no Epic 2 features)
- `test_epic2_neural_enabled.yaml` - Neural reranking only
- `test_epic2_graph_enabled.yaml` - Graph enhancement only
- `test_epic2_all_features.yaml` - All Epic 2 features enabled
- `test_epic2_minimal.yaml` - Minimal features configuration

#### Sub-Component Configuration Mapping

| Configuration Value | Sub-Component Class | Epic 2 Feature |
|---------------------|---------------------|----------------|
| `reranker.type: "neural"` | NeuralReranker | Neural reranking |
| `reranker.type: "identity"` | IdentityReranker | Basic reranking |
| `fusion.type: "graph_enhanced_rrf"` | GraphEnhancedRRFFusion | Graph enhancement |
| `fusion.type: "rrf"` | RRFFusion | Basic fusion |
| `vector_index.type: "weaviate"` | WeaviateIndex | Multi-backend |
| `vector_index.type: "faiss"` | FAISSIndex | Single backend |

### 2. Sub-Component Integration Tests

#### Purpose
Validate Epic 2 sub-component integration within ModularUnifiedRetriever context.

#### Test Files
- `test_epic2_subcomponent_integration_new.py` - Integration testing
- Component-specific tests in `tests/epic2_validation/component_specific/`

#### Test Cases
1. **Neural Integration**: NeuralReranker integration within ModularUnifiedRetriever
2. **Graph Integration**: GraphEnhancedRRFFusion integration testing
3. **Multi-Backend Integration**: Vector index sub-component switching
4. **Sub-Component Interactions**: Validate interactions between sub-components
5. **Configuration Switching**: Test configuration-driven sub-component switching
6. **Performance Impact**: Measure performance impact of sub-component combinations

#### Component-Specific Test Structure

```
tests/epic2_validation/component_specific/
├── test_epic2_vector_indices.py    # Vector index testing
├── test_epic2_fusion_strategies.py  # Fusion strategy testing
├── test_epic2_rerankers.py         # Reranker testing
├── test_epic2_sparse_retrievers.py # Sparse retriever testing
├── test_epic2_backends.py          # Backend testing
├── test_epic2_graph_components.py  # Graph component testing
└── epic2_component_test_utilities.py # Shared utilities
```

### 3. Performance Validation Tests

#### Purpose
Validate Epic 2 meets realistic performance targets based on actual implementation.

#### Test Files
- `test_epic2_performance_validation_new.py` - Performance benchmarking
- Performance monitoring and validation utilities

#### Performance Targets

**Latency Targets**:
- Neural reranking overhead: <200ms (for 100 candidates)
- Graph processing overhead: <50ms (for typical queries)
- Backend switching latency: <50ms (FAISS ↔ Weaviate)
- Total pipeline latency: <700ms P95 (including all stages)

**Throughput Targets**:
- Document processing: >10 docs/sec (with Epic 2 features)
- Concurrent queries: 100 simultaneous (with resource limits)
- Graph construction: <10s (for 1000 documents)
- Memory usage: <2GB additional (for all Epic 2 features)

#### Test Cases
1. **Neural Latency**: Neural reranking meets <200ms overhead target
2. **Graph Performance**: Graph processing meets <50ms overhead target
3. **Backend Switching**: Backend switching meets <50ms latency target
4. **Pipeline Latency**: Total pipeline meets <700ms P95 target
5. **Memory Usage**: Memory usage stays within <2GB additional target
6. **Concurrent Processing**: Handle 10+ concurrent queries efficiently

### 4. Quality Improvement Tests

#### Purpose
Validate Epic 2 features improve retrieval quality with statistical significance.

#### Test Files
- `test_epic2_quality_validation_new.py` - Quality validation
- Quality measurement and comparison utilities

#### Quality Targets

**Relevance Improvements**:
- Neural reranking: >15% improvement vs IdentityReranker
- Graph enhancement: >20% improvement vs RRFFusion
- Combined Epic 2: >30% improvement vs basic configuration
- Statistical significance: p<0.05 for all improvements

**Quality Metrics**:
- Retrieval precision@10: >85% (vs >75% baseline)
- Answer relevance: >80% (vs >70% baseline)
- Citation accuracy: >95% (maintained from baseline)
- User satisfaction: >90% (vs >80% baseline)

#### Test Cases
1. **Neural Quality**: Neural reranking shows >15% quality improvement
2. **Graph Quality**: Graph enhancement shows >20% quality improvement
3. **Combined Quality**: Complete Epic 2 shows >30% quality improvement
4. **Statistical Significance**: Improvements are statistically significant
5. **Relevance Analysis**: Score distributions show good separation
6. **Regression Detection**: No quality regression in Epic 2 features

### 5. End-to-End Pipeline Tests

#### Purpose
Validate complete 4-stage Epic 2 pipeline execution.

#### Test Files
- `test_epic2_pipeline_validation_new.py` - Pipeline testing
- End-to-end workflow validation

#### Test Cases
1. **4-Stage Pipeline Execution**: Dense → Sparse → Graph → Neural
2. **Feature Switching**: Configuration-driven feature switching
3. **Concurrent Processing**: Handle concurrent queries with Epic 2 features
4. **Error Handling**: Graceful degradation when components fail
5. **Load Performance**: Pipeline performance under sustained load
6. **Feature Combinations**: Various feature combination scenarios

---

## 🎯 Critical Quality Tests

### Purpose
Validate that Epic 2 components provide actual retrieval quality improvements, not just mechanical functionality. These tests focus on scoring accuracy, relevance improvements, and mathematical correctness.

### 6. BM25 Scoring Validation

#### Test Focus
Verify BM25 algorithm produces correct scores according to the mathematical formula, properly handles edge cases, and filters irrelevant queries.

#### Test Cases
1. **Technical Query Scoring**: 
   - Verify technical queries score >0.7 for relevant documents
   - Example: "What is RISC-V?" on RISC-V documentation should score >0.7
   
2. **Irrelevant Query Filtering**:
   - Verify off-topic queries score <0.3
   - Example: "Where is Paris?" on technical docs should score <0.3
   
3. **TF-IDF Behavior**:
   - Verify term frequency saturation (diminishing returns)
   - Test: Repeated terms should not linearly increase score
   
4. **Document Length Normalization**:
   - Verify similar content scores similarly regardless of doc length
   - Test: Same term frequency ratio in short vs long docs

#### Expected Behavior
```python
# Correct BM25 behavior examples
assert bm25_score("RISC-V", riscv_doc) > 0.7
assert bm25_score("Paris tourism", riscv_doc) < 0.3
assert bm25_score("RISC-V RISC-V", doc) < 2 * bm25_score("RISC-V", doc)
```

### 7. Vector Similarity Validation

#### Test Focus
Verify embeddings capture semantic relationships correctly and produce appropriate similarity ranges.

#### Test Cases
1. **Semantic Similarity Ranges**:
   - Related concepts: similarity >0.8
   - Unrelated concepts: similarity <0.3
   - Clear separation between related/unrelated
   
2. **Synonym Detection**:
   - "RISC-V architecture" vs "RISC V instruction set" >0.8
   - Technical synonyms properly captured
   
3. **Concept Hierarchies**:
   - Parent-child concepts show moderate similarity (0.5-0.7)
   - Sibling concepts show higher similarity (0.6-0.8)

#### Expected Behavior
```python
# Semantic validation examples
sim_related = cosine_similarity("RISC-V ISA", "RISC-V architecture")
sim_unrelated = cosine_similarity("RISC-V ISA", "French cuisine")
assert sim_related > 0.8
assert sim_unrelated < 0.3
assert sim_related > sim_unrelated + 0.4  # Clear separation
```

### 8. Fusion Algorithm Correctness

#### Test Focus
Verify fusion algorithms (RRF, weighted) implement correct mathematical formulas and produce expected score distributions.

#### Test Cases
1. **RRF Formula Verification**:
   - Verify RRF score = Σ(weight * 1/(k + rank))
   - Test with known inputs and expected outputs
   
2. **Weight Impact Validation**:
   - Different weights produce different rankings
   - Weights correctly influence final scores
   
3. **Score Normalization**:
   - Fused scores in expected range [0, 1]
   - No score inflation or deflation

#### Expected Behavior
```python
# RRF formula validation
# Doc appears at rank 0 in dense, rank 1 in sparse
expected_rrf = 0.7 * (1/(60+1)) + 0.3 * (1/(60+2))
actual_rrf = rrf_fusion(dense_results, sparse_results, k=60)
assert abs(actual_rrf - expected_rrf) < 0.001
```

### 9. Neural Reranking Quality

#### Test Focus
Verify neural reranking actually improves relevance, not just changes scores arbitrarily.

#### Test Cases
1. **Relevance Improvement**:
   - More relevant documents move up in ranking
   - Cross-encoder scores align with human judgment
   
2. **Score Calibration**:
   - High-relevance pairs score >0.8
   - Low-relevance pairs score <0.3
   - Scores interpretable as probabilities
   
3. **Ranking Stability**:
   - Similar documents maintain relative order
   - No random shuffling of results

#### Expected Behavior
```python
# Neural reranking quality validation
initial_order = ["generic_pipeline.pdf", "riscv_pipeline.pdf", "arm_pipeline.pdf"]
reranked = neural_reranker("RISC-V pipeline", initial_order)
assert reranked[0] == "riscv_pipeline.pdf"  # Most relevant moved to top
assert reranker.score("RISC-V pipeline", "riscv_pipeline.pdf") > 0.9
```

### 10. End-to-End Retrieval Quality

#### Test Focus
Validate complete retrieval pipeline produces relevant results with appropriate scores.

#### Test Cases
1. **Precision@K Metrics**:
   - Measure % of relevant docs in top K results
   - Target: Precision@5 >0.8, Precision@10 >0.7
   
2. **Ranking Quality**:
   - Most relevant document in top 3
   - No irrelevant documents in top 5
   
3. **Score Distribution**:
   - Clear score gaps between relevant/irrelevant
   - Scores decrease monotonically
   
4. **Query Coverage**:
   - Technical queries find technical content
   - Off-topic queries return empty or low-score results

#### Expected Behavior
```python
# End-to-end quality validation
results = rag.retrieve("RISC-V vector instructions", k=10)
relevant_docs = ["riscv_vector.pdf", "riscv_simd.pdf"]

# Calculate precision@5
top_5_ids = [r.document.id for r in results[:5]]
precision_at_5 = len(set(top_5_ids) & set(relevant_docs)) / 5
assert precision_at_5 >= 0.4  # At least 2/5 relevant

# Verify top result is relevant
assert results[0].document.id in relevant_docs
```

### 11. Epic 2 vs Basic Comparison

#### Test Focus
Quantify and validate the claimed improvements of Epic 2 features over basic configuration.

#### Test Cases
1. **Score Improvement Validation**:
   - Measure score increases with Epic 2
   - Verify claimed 60x improvement scenarios
   
2. **Ranking Quality Comparison**:
   - Compare precision@K metrics
   - Measure nDCG improvements
   
3. **Component Ablation**:
   - Test each Epic 2 component's contribution
   - Verify cumulative improvements

#### Expected Behavior
```python
# Epic 2 improvement validation
basic_results = basic_rag.retrieve(query)
epic2_results = epic2_rag.retrieve(query)

# Verify score improvement
assert epic2_results[0].score > basic_results[0].score * 10  # Significant improvement

# Verify ranking improvement  
epic2_precision = calculate_precision_at_k(epic2_results, relevant_docs, k=5)
basic_precision = calculate_precision_at_k(basic_results, relevant_docs, k=5)
assert epic2_precision > basic_precision + 0.15  # 15% improvement
```

---

## 🧪 Component-Specific Testing Strategy

### Testing Principles

#### 1. Component Isolation with Integration Context
Test specific sub-components in controlled environments while maintaining full retriever context.

```python
# Example: Testing NeuralReranker while using baseline components
retriever_config = {
    "vector_index": {"type": "faiss", "config": minimal_faiss_config},
    "sparse": {"type": "bm25", "config": minimal_bm25_config},
    "fusion": {"type": "rrf", "config": minimal_rrf_config},
    "reranker": {"type": "neural", "config": full_neural_config}  # FOCUS
}
```

#### 2. Progressive Complexity Testing
- Start with minimal viable configurations
- Add complexity incrementally
- Test edge cases and error conditions
- Validate performance under load

#### 3. Baseline Component Strategy
- Use simplest working implementations for non-focus components
- Ensure baseline components don't interfere with test results
- Maintain consistent baseline across tests for comparability

### Component Performance Requirements

- **Vector Index**: <50ms search latency (100 documents)
- **Fusion Strategy**: <5ms fusion latency (50 candidates)
- **Reranker**: <200ms reranking latency (20 candidates)
- **Sparse Retriever**: <20ms search latency (100 documents)
- **Backend**: <100ms operation latency
- **Graph Components**: <10ms graph query latency

---

## 🔧 Test Data and Environment

### Test Document Set

**RISC-V Technical Documentation** (Standard Dataset):
- 10 documents for basic testing
- 100 documents for performance testing
- 1000 documents for scale testing
- Consistent content for Epic 2 validation

**Query Test Suite**:
- 20 factual queries for basic validation
- 50 complex queries for advanced testing
- 100 diverse queries for performance testing
- Known relevance judgments for quality measurement

### Test Environment Setup

**Prerequisites**:
- Docker services: Weaviate, Ollama
- Python dependencies: weaviate-client, networkx, transformers
- Test data: RISC-V documentation set
- GPU support: Optional for neural reranking acceleration

**Environment Validation**:
```bash
# Verify Epic 2 environment
python scripts/validate_epic2_environment.py

# Expected output:
# ✅ Weaviate connection successful
# ✅ Neural reranking models available
# ✅ Graph dependencies installed
# ✅ Test data loaded
```

---

## 🚀 Test Execution Framework

### Test Execution Strategy

**Phase 1: Configuration Validation** (30 minutes)
1. Load all Epic 2 test configurations
2. Verify sub-component creation
3. Validate configuration parsing
4. Test error handling

**Phase 2: Sub-Component Testing** (60 minutes)
1. Neural reranking validation
2. Graph enhancement testing
3. Multi-backend validation
4. Performance baseline measurement

**Phase 3: Integration Testing** (90 minutes)
1. Complete pipeline validation
2. Concurrent query processing
3. Quality comparison testing
4. End-to-end performance validation

**Phase 4: Regression Testing** (30 minutes)
1. Backward compatibility validation
2. Basic configuration still works
3. Performance regression detection
4. Quality regression validation

### Automated Test Execution

**Quick Validation** (5 minutes):
```bash
# Basic Epic 2 functionality check
python tests/epic2_validation/run_quick_epic2_test.py
```

**Comprehensive Validation** (15-30 minutes):
```bash
# Complete Epic 2 test suite
python tests/epic2_validation/run_epic2_comprehensive_tests.py --mode comprehensive
```

**Performance Benchmarking** (30 minutes):
```bash
# Epic 2 performance validation
python tests/epic2_validation/run_epic2_comprehensive_tests.py --mode performance
```

### Test Execution Modes

1. **Quick Mode** (`--mode quick`): Configuration + Sub-component integration (5-10 minutes)
2. **Comprehensive Mode** (`--mode comprehensive`): All test categories (15-30 minutes)
3. **Performance Mode** (`--mode performance`): Performance validation only (10-15 minutes)
4. **Quality Mode** (`--mode quality`): Quality improvement validation (10-15 minutes)
5. **Integration Mode** (`--mode integration`): End-to-end pipeline tests (5-10 minutes)

---

## 📊 Test Validation Criteria

### Pass/Fail Criteria

**Configuration Tests**:
- ✅ PASS: All Epic 2 configurations load without errors
- ✅ PASS: Sub-components match configuration specifications
- ❌ FAIL: Configuration errors or wrong sub-components created

**Performance Tests**:
- ✅ PASS: All latency targets met within 20% variance
- ⚠️ CONDITIONAL: Targets met within 50% variance (investigate)
- ❌ FAIL: Targets exceeded by >50% (performance regression)

**Quality Tests**:
- ✅ PASS: All quality improvements statistically significant
- ⚠️ CONDITIONAL: Some improvements significant (partial success)
- ❌ FAIL: No significant improvements or quality regression

### Test Coverage Requirements

**Configuration Coverage**: 100% of Epic 2 configurations tested
**Sub-Component Coverage**: 100% of Epic 2 sub-components validated
**Integration Coverage**: 100% of Epic 2 integration points tested
**Performance Coverage**: 100% of Epic 2 performance targets benchmarked

### Quality Gates

**Development Quality Gate**:
- All configuration tests pass
- Sub-component tests pass
- Basic performance targets met
- No critical regressions

**Staging Quality Gate**:
- All integration tests pass
- Performance targets met
- Quality improvements validated
- Load testing successful

**Production Quality Gate**:
- All tests pass consistently
- Performance targets exceeded
- Quality improvements proven
- Production deployment validated

---

## 🔍 Troubleshooting Guide

### Common Epic 2 Test Issues

**"Neural reranking model not found"**:
- **Cause**: Missing transformers models
- **Solution**: Run `huggingface-cli download cross-encoder/ms-marco-MiniLM-L6-v2`

**"Weaviate connection failed"**:
- **Cause**: Weaviate service not running
- **Solution**: `docker-compose up -d weaviate`

**"Graph construction timeout"**:
- **Cause**: Large document set or insufficient resources
- **Solution**: Reduce document count or increase timeouts

**"Configuration validation failed"**:
- **Cause**: Invalid Epic 2 configuration format
- **Solution**: Validate against schema and example configurations

### Performance Troubleshooting

**Slow neural reranking**:
- Enable GPU acceleration
- Reduce batch size
- Optimize model loading

**High memory usage**:
- Reduce cache sizes
- Optimize graph construction
- Monitor memory leaks

**Backend switching failures**:
- Verify service availability
- Check network connectivity
- Validate configuration

---

## 📋 Test Reporting and Metrics

### Test Report Structure

**Executive Summary**:
- Overall Epic 2 test status
- Key performance metrics
- Quality improvement measurements
- Production readiness assessment

**Detailed Results**:
- Configuration validation results
- Sub-component test results
- Integration test results
- Performance benchmark results
- Quality comparison results

**Recommendations**:
- Configuration optimization suggestions
- Performance improvement recommendations
- Quality enhancement opportunities
- Production deployment guidance

### Key Metrics Dashboard

**Epic 2 Test Dashboard**:
- Configuration success rate: Target 100%
- Sub-component validation rate: Target 100%
- Performance target achievement: Target >90%
- Quality improvement significance: Target >95%
- Overall Epic 2 readiness: Target >95%

---

## 🔮 Future Enhancements

### Planned Test Improvements

**Advanced Testing**:
- A/B testing framework integration
- Multi-language Epic 2 validation
- Custom model testing support
- Advanced graph algorithms testing

**Performance Optimization**:
- GPU acceleration testing
- Distributed Epic 2 testing
- Cloud backend testing
- Edge deployment testing

### Test Framework Evolution

**Framework Enhancements**:
- Automated test generation
- Machine learning test validation
- Continuous performance monitoring
- Predictive quality assessment

**Integration Improvements**:
- CI/CD pipeline optimization
- Automated deployment testing
- Production monitoring integration
- User experience testing

---

## 📝 Conclusion

This Epic 2 Test Specification provides a comprehensive framework for validating the advanced hybrid retriever features implemented within ModularUnifiedRetriever. The specification emphasizes configuration-driven testing, realistic performance targets, and quality improvement validation while maintaining alignment with the actual Epic 2 implementation architecture.

**Key Success Factors**:
- Configuration-driven validation approach
- Realistic performance and quality targets
- Comprehensive sub-component testing
- Integration with existing architecture
- Automated test execution and reporting

**Expected Outcomes**:
- Reliable Epic 2 feature validation
- Consistent performance benchmarking
- Quality improvement measurement
- Production deployment confidence
- Portfolio demonstration readiness

---

## References

- [MASTER-ARCHITECTURE.md](../architecture/MASTER-ARCHITECTURE.md) - System architecture
- [Epic 2 Implementation Report](../epics/epic2-implementation-report.md) - Implementation details
- [Epic 2 User Guide](../../tests/epic2_validation/README.md) - Usage instructions
- [Master Test Strategy](./master-test-strategy.md) - Overall testing approach
- [Integration Test Plan](./integration-test-plan.md) - General integration testing