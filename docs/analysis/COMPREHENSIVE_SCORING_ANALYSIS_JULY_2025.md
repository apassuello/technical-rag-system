# Comprehensive Scoring Analysis - Epic 2 Quality Issues

**Date**: July 21, 2025  
**Analysis Type**: Multi-Component Scoring Investigation  
**Epic 2 Quality Score**: 16.7% (Critical - down from 50%)  
**Status**: Root Causes Identified - Multiple Scoring Issues

## Executive Summary

Epic 2 quality validation has dropped to 16.7% due to **multiple interconnected scoring issues** across the retrieval pipeline. The primary issue is **BM25 document length bias** causing inverted relevance rankings, which then propagates through fusion and final scoring.

## Critical Issues Identified

### 1. 🚨 BM25 Scoring Inversion (Primary Issue)

**Problem**: BM25 ranks irrelevant documents higher than relevant ones due to document length normalization bias.

**Evidence** (Query: "What is RISC-V?"):
| Rank | Document | Relevance | BM25 Score | tf_ratio | Should Be Rank |
|------|----------|-----------|------------|----------|----------------|
| 1 | ARM processors... | **LOW** | 1.000000 | 0.0909 | 4-5 |
| 2 | x86 processors... | **LOW** | 0.382184 | 0.0667 | 5 |
| 3 | RISC-V instruction set... | **HIGH** | 0.248076 | 0.0625 | 1-2 |
| 4 | RISC-V processors... | **HIGH** | 0.248076 | 0.0625 | 2-3 |
| Missing | RISC-V is an open-source... | **HIGHEST** | Not returned | 0.0556 | 1 |

**Root Cause**: 
- BM25 parameter `b=0.75` heavily penalizes longer documents
- Shorter documents mentioning query terms get artificially inflated scores
- Term frequency ratio calculation favors brevity over comprehensiveness

### 2. ⚡ Dense vs Sparse Score Contradiction

**Dense Results (Semantic Similarity)** - ✅ **WORKING CORRECTLY**:
1. Doc 0 (RISC-V Introduction): 0.833712 - **Highest relevance**
2. Doc 1 (RISC-V Instructions): 0.603084 - **High relevance**
3. Doc 2 (RISC-V Privilege Levels): 0.587613 - **High relevance**

**Sparse Results (BM25)** - ❌ **COMPLETELY INVERTED**:
1. Doc 3 (ARM Architecture): 1.000000 - **Should be lowest**
2. Doc 4 (x86 Architecture): 0.382184 - **Should be lowest**  
3. Doc 1 (RISC-V Instructions): 0.248076 - **Should be highest**

### 3. 🔀 RRF Fusion Parameter Issues

**Current RRF Configuration**:
```yaml
fusion:
  type: "rrf"
  config:
    k: 60              # TOO HIGH
    weights:
      dense: 0.7       # Correct
      sparse: 0.3      # Amplifying BM25 bias
```

**Issues Identified**:
- **k=60 too high**: Creates very small scores (~0.015), reducing discriminative power
- **BM25 bias amplification**: 30% weight given to inverted BM25 scores
- **Score range compression**: All final scores clustered around 0.01-0.02

**RRF Analysis** (k=60):
| Doc | Dense Rank | Sparse Rank | Dense Score | Sparse Score | Total RRF | Issue |
|-----|------------|-------------|-------------|--------------|-----------|-------|
| 0 (RISC-V Intro) | 1 | N/A | 0.011475 | 0.000000 | 0.011475 | Missing from sparse |
| 1 (RISC-V Instr) | 2 | 3 | 0.011290 | 0.004762 | 0.016052 | Should be higher |
| 3 (ARM) | N/A | 1 | 0.000000 | 0.004918 | 0.004918 | Wrong sparse rank |

**Parameter Sensitivity Analysis**:
| k | Doc 1 (RISC-V) | Doc 3 (ARM) | Advantage |
|---|----------------|-------------|-----------|
| 10 | 0.081410 | 0.027273 | RISC-V ✅ |
| 30 | 0.030966 | 0.009677 | RISC-V ✅ |
| 60 | 0.016052 | 0.004918 | RISC-V (weak) |
| 100 | 0.009775 | 0.002970 | RISC-V (weaker) |

### 4. 📊 Score Distribution Problems

**All Components Show Issues**:
- **BM25 scores**: Inverted ranking (high scores for irrelevant docs)
- **Dense scores**: Good semantic ranking but not reaching fusion effectively
- **Fusion scores**: Compressed into narrow range (0.004-0.016)
- **Final scores**: Poor discriminative power due to upstream issues

## Impact Assessment

### System-Wide Effects
- **Epic 2 Quality**: 16.7% validation score (critical failure)
- **User Experience**: Users get wrong documents first
- **Neural Reranking**: Limited ability to fix fundamentally inverted base scores
- **Graph Enhancement**: Working with wrong similarity assumptions
- **Overall Retrieval**: Precision severely compromised

### Component Interaction Analysis
```
BM25 Bias → Fusion Pollution → Poor Final Ranking
     ↓            ↓                   ↓
Wrong sparse   Compressed      Neural reranker
rankings   →   scores      →   can't recover
```

## Detailed Scoring Flow Analysis

### Current Pipeline Issues
1. **BM25**: Returns inverted rankings (ARM > RISC-V for "What is RISC-V?")
2. **Dense**: Returns correct rankings (RISC-V docs top)
3. **RRF Fusion**: 
   - Combines correct dense + wrong sparse
   - k=60 compresses all scores  
   - 30% weight amplifies BM25 bias
4. **Neural Reranking**: 
   - Receives poorly fused candidates
   - Limited ability to recover from wrong base ranking
5. **Final Result**: Epic 2 quality failure

### Expected vs Actual Flow
**Expected**:
```
Query → BM25 ✅ + Dense ✅ → Fusion ✅ → Reranking ✅ → High Quality
```

**Actual**:
```
Query → BM25 ❌ + Dense ✅ → Fusion ⚠️ → Reranking ⚠️ → Low Quality
```

## Configuration Analysis

### Current Problematic Parameters
```yaml
# BM25 Configuration - CAUSING BIAS
sparse:
  type: "bm25"
  config:
    k1: 1.2          # OK
    b: 0.75          # TOO HIGH - penalizes long docs
    min_score: 0.0   # OK

# RRF Configuration - POOR PARAMETERS  
fusion:
  type: "rrf"
  config:
    k: 60            # TOO HIGH - compresses scores
    weights:
      dense: 0.7     # OK
      sparse: 0.3    # AMPLIFIES BM25 BIAS
```

### Recommended Parameter Changes
```yaml
# BM25 Configuration - FIXED
sparse:
  type: "bm25"
  config:
    k1: 1.2          # Keep
    b: 0.25          # REDUCE from 0.75
    min_score: 0.0   # Keep

# RRF Configuration - OPTIMIZED
fusion:
  type: "rrf"
  config:
    k: 30            # REDUCE from 60
    weights:
      dense: 0.8     # INCREASE (dense works correctly)
      sparse: 0.2    # REDUCE (sparse is biased)
```

## Fix Strategy

### Phase 1: Immediate BM25 Fix
1. **Reduce b parameter**: 0.75 → 0.25 (reduce length penalty)
2. **Test with problematic queries**: Verify RISC-V docs rank higher
3. **Update all configurations**: Apply fix to basic, demo, epic2 configs

### Phase 2: RRF Optimization
1. **Reduce k parameter**: 60 → 30 (increase score discriminative power)
2. **Adjust fusion weights**: 70/30 → 80/20 (favor working dense over biased sparse)
3. **Validate score ranges**: Ensure reasonable score distribution

### Phase 3: System Validation
1. **Run Epic 2 tests**: Verify quality score improvement >50%
2. **Test multiple queries**: Ensure no regression on other queries
3. **Performance check**: Confirm no significant latency impact

## Expected Outcomes

### Performance Improvements
- **Epic 2 Quality**: 16.7% → >50% (target improvement)
- **BM25 Rankings**: RISC-V docs should rank above ARM/x86 for relevant queries
- **Fusion Scores**: Better discriminative power with larger score ranges
- **Overall Precision**: Measurable improvement in retrieval quality

### Risk Mitigation
- **Gradual parameter adjustment**: Test each change incrementally
- **Multiple query validation**: Ensure broad improvement, not overfitting
- **Performance monitoring**: Track latency and memory usage
- **Rollback strategy**: Keep working configurations as backup

## Calibration System Requirements

### Immediate Needs (This Session)
- **BM25 parameter tuning**: b and k1 optimization
- **RRF parameter adjustment**: k and weight optimization  
- **Quick validation**: Test with Epic 2 queries

### Future Calibration System (Next Session)
- **Automated parameter optimization**: Grid search with quality metrics
- **Query type adaptation**: Different parameters for different query types
- **Performance monitoring**: Real-time score quality assessment
- **Multi-component consistency**: Ensure all components work in compatible ranges

## Test Cases for Validation

### Core Test Queries
1. **"What is RISC-V?"** - Should rank RISC-V docs 1st, 2nd, 3rd
2. **"RISC-V instruction set"** - Should prioritize instruction-related docs
3. **"ARM vs RISC-V"** - Should rank both architectures appropriately
4. **"x86 processor architecture"** - Should rank x86 docs highest

### Success Criteria
- **Relevant docs top 3**: For direct queries about RISC-V
- **Score separation**: Clear score differences between relevant/irrelevant
- **Cross-query consistency**: No major regression on other technical queries
- **Epic 2 validation**: >50% overall quality score

---

**Next Actions**: Implement BM25 parameter fixes and test with Epic 2 validation suite.

**Priority**: CRITICAL - Core retrieval quality depends on resolving these scoring issues.