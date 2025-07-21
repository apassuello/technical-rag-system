# BM25 Scoring Analysis & Calibration Requirements

**Date**: July 21, 2025  
**Analysis Type**: Critical Scoring Issue Investigation  
**Status**: Root Cause Identified - Requires Calibration System

## Executive Summary

BM25 scoring is exhibiting **document length bias** that inverts relevance rankings, causing Epic 2 quality validation to drop to 16.7%. The issue stems from BM25's document length normalization parameter (`b=0.75`) overly penalizing longer, comprehensive documents while rewarding shorter, less relevant documents.

## Critical Issue Identified

### Problem Statement
For query "What is RISC-V?", BM25 ranks documents in reverse order of relevance:

| Rank | Document | Relevance | Score | tf_ratio | Issue |
|------|----------|-----------|--------|----------|-------|
| 1 | ARM processors... | **LOW** | 1.000000 | 0.0909 | Should be rank 4-5 |
| 2 | x86 processors... | **LOW** | 0.382184 | 0.0667 | Should be rank 5 |
| 3 | RISC-V instruction set... | **HIGH** | 0.248076 | 0.0625 | Should be rank 1-2 |
| 4 | RISC-V processors... | **HIGH** | 0.248076 | 0.0625 | Should be rank 2-3 |
| Missing | RISC-V is an open-source... | **HIGHEST** | Not returned | 0.0556 | Should be rank 1 |

### Root Cause Analysis

**Document Length Normalization Bias**: 
- BM25 parameter `b=0.75` heavily penalizes longer documents
- Term frequency ratio calculation: `tf / doc_length`
- Shorter documents mentioning query terms get artificially inflated scores
- Comprehensive, informative documents get penalized

**Evidence**:
- Most relevant doc (RISC-V definition): 18 tokens → tf_ratio=0.0556 → **worst score**
- Least relevant doc (ARM comparison): 11 tokens → tf_ratio=0.0909 → **best score**

## Impact Assessment

### System-Wide Effects
- **Epic 2 Quality Validation**: Dropped to 16.7% (from previous 50%)
- **Retrieval Precision**: Severely compromised for technical queries
- **User Experience**: Users get irrelevant documents first
- **Epic 2 Features**: Neural reranking and fusion working on wrong base results

### Affected Components
- ✅ **BM25Retriever**: Core issue identified
- ❓ **Fusion Strategies**: May be amplifying BM25 bias  
- ❓ **Neural Reranking**: Limited ability to fix inverted base scores
- ❓ **Graph Enhancement**: May be working with wrong similarity assumptions

## Calibration System Requirements

### 1. BM25 Parameter Calibration
**Current Configuration**:
```yaml
sparse:
  type: "bm25"
  config:
    k1: 1.2          # Term frequency saturation
    b: 0.75          # Document length normalization (PROBLEMATIC)
    min_score: 0.0   # Minimum score threshold
```

**Calibration Needs**:
- **Parameter Range Testing**: b ∈ [0.1, 0.2, 0.25, 0.35, 0.5, 0.75]
- **k1 Optimization**: k1 ∈ [1.0, 1.2, 1.5, 2.0, 2.5]
- **Document Length Compensation**: Alternative normalization methods
- **Query Type Adaptation**: Different parameters for different query types

### 2. Score Normalization Calibration
**Current Issues**:
- Min-max normalization creates artificial score gaps
- Zero scores filtered too aggressively (threshold=0.001)
- Score ranges inconsistent across different document collections

**Calibration Needs**:
- **Normalization Method Selection**: Min-max vs z-score vs sigmoid
- **Threshold Optimization**: Dynamic thresholds based on score distribution
- **Score Distribution Analysis**: Ensure reasonable score spreads
- **Cross-Collection Consistency**: Stable scoring across different document sets

### 3. Fusion Weight Calibration
**Current Weights**:
```yaml
fusion:
  weights:
    dense: 0.7
    sparse: 0.3    # Currently broken due to BM25 bias
```

**Calibration Needs**:
- **Dynamic Weight Adjustment**: Based on query characteristics
- **Score Quality Assessment**: Detect when BM25 scores are unreliable
- **Fallback Strategies**: Reduce sparse weight when BM25 bias detected
- **Query-Adaptive Fusion**: Different weights for factual vs conceptual queries

### 4. Multi-Component Score Calibration
**System-Wide Requirements**:
- **Cross-Component Consistency**: Ensure all components work in similar score ranges
- **Quality Metrics Integration**: Use retrieval quality to guide calibration
- **Performance Monitoring**: Track score quality over time
- **Automated Calibration**: Self-tuning based on user feedback and quality metrics

## Technical Implementation Plan

### Phase 1: Immediate BM25 Fixes (Current Session)
- **Parameter Experimentation**: Test b=[0.25, 0.35] with current queries
- **Quick Validation**: Verify improved rankings for RISC-V queries
- **Configuration Updates**: Apply optimal parameters to all configs

### Phase 2: Comprehensive Calibration System (Future Session)
- **Calibration Framework**: Build systematic parameter optimization system
- **Test Suite Creation**: Comprehensive query/relevance test cases
- **Automated Tuning**: Grid search with quality metrics optimization
- **Configuration Management**: Versioned, validated parameter sets

### Phase 3: Advanced Scoring (Future Enhancement)
- **Content Quality Signals**: Term proximity, density, semantic coherence
- **Query Type Detection**: Adapt scoring based on query characteristics  
- **Ensemble Methods**: Combine multiple scoring approaches
- **Machine Learning Calibration**: Learn optimal parameters from data

## Validation Requirements

### Success Criteria
- **BM25 Rankings**: RISC-V queries rank RISC-V documents highest
- **Epic 2 Quality**: Validation score improves to >50%
- **Cross-Query Consistency**: No regression on other technical queries
- **Score Distributions**: Reasonable score spreads and thresholds

### Test Cases Needed
- **Technical Definition Queries**: "What is RISC-V?", "What is ARM?"
- **Comparative Queries**: "RISC-V vs ARM", "RISC vs CISC"
- **Specific Feature Queries**: "RISC-V vector extensions", "ARM Cortex-M"
- **Negative Cases**: Irrelevant queries should still score low

## Future Session Planning

### Calibration System Session Goals
1. **Build calibration framework** for systematic parameter optimization
2. **Create comprehensive test suite** with ground truth relevance judgments
3. **Implement automated tuning** with multiple quality metrics
4. **Establish monitoring system** for ongoing score quality assessment
5. **Document best practices** for parameter selection and validation

### Expected Deliverables
- **Calibration Framework**: Automated parameter optimization system
- **Parameter Database**: Validated configurations for different use cases
- **Quality Monitoring**: Real-time score quality assessment
- **Documentation**: Complete calibration methodology and best practices

---

**Next Immediate Actions**: Continue investigating fusion and neural reranking scores to understand full scope of scoring issues before implementing calibration system.

**Priority**: HIGH - Core retrieval quality depends on resolving these scoring issues.