# Scoring Calibration System Implementation Session

**Session Type**: Implementation & Optimization  
**Estimated Duration**: 3-4 hours  
**Prerequisites**: Comprehensive scoring analysis complete (July 21, 2025)  
**Target Outcome**: Epic 2 quality validation >50% (from current 16.7%)

## Quick Context Recovery

### Critical Issues Identified
1. **BM25 Document Length Bias**: `b=0.75` causes inverted rankings (ARM docs ranked higher than RISC-V docs for "What is RISC-V?")
2. **RRF Parameter Problems**: `k=60` compresses scores, `sparse_weight=0.3` amplifies BM25 bias
3. **Score Contradiction**: Dense results work correctly, sparse results completely inverted

### Evidence Files to Review
```bash
# Key analysis documents
cat docs/analysis/BM25_SCORING_ANALYSIS_AND_CALIBRATION_NEEDS.md
cat docs/analysis/COMPREHENSIVE_SCORING_ANALYSIS_JULY_2025.md

# Test the current broken state
python -m pytest tests/epic2_validation/test_epic2_quality_validation_new.py -v

# Debug scripts available
python debug_bm25_scoring.py          # BM25 bias analysis
python debug_fusion_analysis.py       # RRF parameter analysis
```

## Session Goals

### Phase 1: Immediate Parameter Fixes (1 hour)
**Objective**: Fix critical BM25 and RRF parameters to restore basic functionality

**Actions**:
1. **Update BM25 parameters** in all configurations:
   ```yaml
   # Change from problematic values
   sparse:
     config:
       b: 0.75 → 0.25    # Reduce document length penalty
       k1: 1.2           # Keep (working fine)
   ```

2. **Optimize RRF parameters**:
   ```yaml
   # Improve discriminative power and reduce sparse bias
   fusion:
     config:
       k: 60 → 30        # Better score separation  
       weights:
         dense: 0.7 → 0.8   # Favor working dense component
         sparse: 0.3 → 0.2  # Reduce biased sparse component
   ```

3. **Test with critical queries**:
   - "What is RISC-V?" should rank RISC-V docs 1st, 2nd, 3rd
   - Run Epic 2 validation: target >30% improvement

**Success Criteria**: RISC-V queries rank RISC-V documents highest, Epic 2 score >30%

### Phase 2: Calibration Framework Implementation (2 hours)
**Objective**: Build systematic parameter optimization system

**Architecture**:
```python
class ScoringCalibrationSystem:
    def __init__(self):
        self.test_queries = self._load_ground_truth_queries()
        self.quality_metrics = ["ndcg@10", "precision@5", "mrr"]
        
    def calibrate_bm25_parameters(self, param_ranges):
        # Grid search over k1, b parameters
        # Optimize for relevance ranking quality
        
    def calibrate_fusion_parameters(self, param_ranges):
        # Optimize k, dense_weight, sparse_weight
        # Ensure score discriminative power
        
    def validate_cross_component_consistency(self):
        # Ensure all components work in compatible score ranges
        
    def generate_optimal_configurations(self):
        # Create validated config files for different use cases
```

**Implementation Steps**:
1. **Create calibration framework** with test query suite
2. **Implement parameter grid search** with quality metrics
3. **Build validation pipeline** for cross-component testing
4. **Generate optimized configurations** for basic/demo/epic2

**Success Criteria**: Automated system produces configurations with >50% Epic 2 validation

### Phase 3: Advanced Scoring Enhancements (1 hour)
**Objective**: Implement content quality signals and query-adaptive scoring

**Enhancements**:
1. **Content Quality Signals**:
   - Term proximity scoring
   - Technical term density analysis
   - Document comprehensiveness metrics

2. **Query-Adaptive Parameters**:
   - Detect query type (factual, comparative, technical)
   - Adjust BM25/fusion parameters based on query characteristics
   - Implement fallback strategies for edge cases

3. **Score Quality Monitoring**:
   - Real-time score distribution analysis
   - Automatic bias detection
   - Performance degradation alerts

**Success Criteria**: Enhanced scoring shows measurable quality improvements

## Key Files to Modify

### Configuration Files
```bash
# Update all core configurations
config/basic.yaml      # BM25 b: 0.75→0.25, RRF k: 60→30
config/demo.yaml       # Same parameters + neural reranking optimization  
config/epic2.yaml      # Full optimization for all Epic 2 features
config/default.yaml    # Maintain compatibility with optimized parameters
```

### Component Files
```bash
# BM25 parameter validation
src/components/retrievers/sparse/bm25_retriever.py

# RRF parameter optimization
src/components/retrievers/fusion/rrf_fusion.py

# New calibration system
src/components/calibration/scoring_calibration.py (NEW)
src/components/calibration/quality_metrics.py (NEW)
```

### Test Files
```bash
# Validation tests
tests/epic2_validation/test_epic2_quality_validation_new.py

# Parameter-specific tests
tests/calibration/test_bm25_parameters.py (NEW)
tests/calibration/test_fusion_parameters.py (NEW)
```

## Validation Strategy

### Test Queries with Expected Rankings
```python
test_cases = [
    {
        "query": "What is RISC-V?",
        "expected_order": ["risc_v_intro", "risc_v_instructions", "risc_v_privilege", "arm_arch", "x86_arch"],
        "success_criteria": "RISC-V docs in top 3"
    },
    {
        "query": "RISC-V instruction set",
        "expected_order": ["risc_v_instructions", "risc_v_intro", "risc_v_privilege", "arm_arch", "x86_arch"],
        "success_criteria": "Instruction docs ranked highest"
    },
    {
        "query": "ARM vs RISC-V architecture",
        "expected_order": ["arm_arch", "risc_v_intro", "risc_v_instructions", "x86_arch"],
        "success_criteria": "Both ARM and RISC-V docs in top 3"
    }
]
```

### Quality Metrics Targets
- **Epic 2 Validation**: >50% (from 16.7%)
- **NDCG@10**: >0.7 for technical queries
- **Precision@5**: >0.8 for direct queries
- **Score Separation**: >0.1 difference between relevant/irrelevant docs

## Implementation Commands

### Quick Start Workflow
```bash
# 1. Test current broken state
python -m pytest tests/epic2_validation/test_epic2_quality_validation_new.py -v

# 2. Apply parameter fixes
# Edit config files with new BM25/RRF parameters

# 3. Validate improvements  
python debug_bm25_scoring.py          # Verify BM25 fixes
python -m pytest tests/epic2_validation/test_epic2_quality_validation_new.py -v

# 4. Build calibration system
# Implement calibration framework and run optimization

# 5. Final validation
python -m pytest tests/epic2_validation/ -v    # Full Epic 2 test suite
```

### Debugging Resources
```bash
# Existing debug scripts (ready to use)
python debug_bm25_scoring.py           # BM25 bias analysis
python debug_fusion_analysis.py        # RRF parameter sensitivity
python debug_retrieval_scores.py       # Full pipeline analysis

# Create new calibration scripts
python calibrate_parameters.py         # Grid search optimization
python validate_configurations.py      # Cross-component testing
```

## Expected Session Outcomes

### Immediate Improvements
- **Epic 2 Quality**: 16.7% → >50%
- **Query Relevance**: RISC-V queries rank RISC-V docs correctly
- **Score Quality**: Better discriminative power between relevant/irrelevant docs

### System Enhancements
- **Calibration Framework**: Automated parameter optimization system
- **Quality Monitoring**: Real-time score quality assessment  
- **Configuration Management**: Validated, use-case-specific configs
- **Documentation**: Complete calibration methodology and best practices

### Long-term Benefits
- **Maintainability**: Systematic approach to parameter tuning
- **Scalability**: Framework supports new components and metrics
- **Reliability**: Automated detection and correction of scoring issues
- **Performance**: Optimized parameters for all Epic 2 features

## Risk Mitigation

### Rollback Strategy
- Keep working configurations as backup in `config/archive/working_backup/`
- Test each parameter change incrementally
- Validate with multiple query types to avoid overfitting

### Performance Monitoring
- Track latency impact of parameter changes
- Monitor memory usage during calibration
- Ensure no regression in system stability

### Quality Assurance
- Cross-validate with multiple test query sets
- Test edge cases and boundary conditions
- Verify improvements are statistically significant

---

**Ready to Execute**: This session prompt provides complete context and clear implementation steps to resolve the Epic 2 scoring crisis and build a robust calibration system for long-term quality assurance.