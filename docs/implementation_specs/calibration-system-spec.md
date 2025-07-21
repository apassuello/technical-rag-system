# Calibration System Specification

**Component**: Cross-Component Calibration System  
**Version**: 1.0  
**Purpose**: Data-driven parameter optimization and confidence calibration  
**Architecture Pattern**: Observer + Strategy Pattern

## 1. System Overview

### 1.1 Objectives
- Systematically tune system parameters based on golden test set performance
- Calibrate confidence scores to reflect actual answer quality
- Provide clear visibility into parameter impacts
- Enable reproducible optimization

### 1.2 Scope
The calibration system will optimize:
- BM25 parameters (k1, b, stop word filtering)
- Fusion weights (dense/sparse balance, composite scoring)
- Confidence scoring weights and thresholds
- Refusal thresholds

### 1.3 Architecture Integration
```
Platform Orchestrator
    ├── CalibrationManager (new sub-component)
    │   ├── ParameterRegistry
    │   ├── MetricsCollector
    │   ├── OptimizationEngine
    │   └── CalibrationReporter
    └── Existing Components (observable)
```

## 2. Core Components Design

### 2.1 Parameter Registry
**Purpose**: Central registry of all tunable parameters

```python
# Structure for parameter definition
Parameter = {
    "name": "bm25_k1",
    "component": "sparse_retriever",
    "path": "retriever.sparse.config.k1",  # YAML path
    "current": 1.2,
    "min": 0.5,
    "max": 2.0,
    "step": 0.1,
    "type": "float",
    "impacts": ["retrieval_precision", "retrieval_recall"]
}
```

### 2.2 Metrics Collector
**Purpose**: Gather performance metrics during test runs

```python
# Metrics structure per query
QueryMetrics = {
    "query_id": "TC001",
    "retrieval_metrics": {
        "documents_retrieved": 5,
        "avg_semantic_score": 0.67,
        "avg_bm25_score": 0.45,
        "fusion_score_spread": 0.23
    },
    "generation_metrics": {
        "confidence_score": 0.85,
        "answer_length": 234,
        "citations_used": 3,
        "generation_time": 1.2
    },
    "validation_results": {
        "meets_expectations": True,
        "confidence_in_range": True,
        "contains_required_terms": True
    }
}
```

### 2.3 Optimization Engine
**Purpose**: Find optimal parameter values

Strategies:
1. **Grid Search**: Exhaustive search over parameter combinations
2. **Binary Search**: For single parameter optimization
3. **Gradient-Free**: For multiple parameters without derivatives

### 2.4 Calibration Reporter
**Purpose**: Generate actionable insights from calibration

Report includes:
- Best parameter configurations
- Performance improvements
- Confidence calibration curves
- Per-category breakdowns

## 3. Calibration Workflow

### 3.1 Full Calibration Process
```
1. Load golden test set
2. Initialize parameter registry
3. For each parameter configuration:
   a. Update system configuration
   b. Run all test queries
   c. Collect metrics
   d. Validate against expectations
4. Analyze results
5. Generate recommendations
6. Apply best configuration
```

### 3.2 Incremental Calibration
```
1. Run baseline with current parameters
2. Identify worst-performing query categories
3. Focus optimization on relevant parameters
4. Test improvements on full set
5. Commit changes if improvement > threshold
```

## 4. Implementation Specifications

### 4.1 Configuration Schema
```yaml
# calibration_config.yaml
calibration:
  enabled: true
  strategy: "grid_search"  # or "binary_search", "gradient_free"
  
  parameters:
    - name: "bm25_k1"
      enabled: true
      search_space: [0.8, 1.0, 1.2, 1.5]
      
    - name: "fusion_weight"
      enabled: true  
      search_space: [0.5, 0.6, 0.7, 0.8]
      
    - name: "semantic_floor"
      enabled: true
      search_space: [0.2, 0.3, 0.4]
      
  optimization:
    target_metric: "overall_accuracy"  # or "confidence_ece", "retrieval_f1"
    constraint_metrics:
      - metric: "avg_latency"
        max_value: 2.0
      - metric: "false_positive_rate"
        max_value: 0.1
        
  confidence_calibration:
    enabled: true
    method: "temperature_scaling"
    n_bins: 10
```

### 4.2 Calibration API
```python
# Main calibration interface
calibrator = CalibrationManager(platform_orchestrator)

# Run full calibration
results = calibrator.calibrate(
    test_set="tests/golden_test_set.json",
    strategy="grid_search",
    target_metric="overall_accuracy"
)

# Run focused calibration
results = calibrator.calibrate_component(
    component="sparse_retriever",
    test_subset="stop_word_tests",
    parameters=["filter_stop_words", "stop_word_sets"]
)

# Generate report
report = calibrator.generate_report(results)
calibrator.save_report("calibration_report.html")
```

### 4.3 Metrics Definition
```python
CALIBRATION_METRICS = {
    # Retrieval metrics
    "retrieval_precision": "Fraction of retrieved docs that are relevant",
    "retrieval_recall": "Fraction of relevant docs that are retrieved", 
    "retrieval_f1": "Harmonic mean of precision and recall",
    
    # Answer quality metrics
    "answer_accuracy": "Fraction of queries answered correctly",
    "confidence_ece": "Expected Calibration Error",
    "refusal_accuracy": "Correct refusals / total refusals",
    
    # System metrics
    "avg_latency": "Average query processing time",
    "p95_latency": "95th percentile latency",
    "throughput": "Queries per second",
    
    # Category-specific
    "technical_accuracy": "Accuracy on technical queries",
    "edge_case_handling": "Success rate on edge cases",
    "false_positive_rate": "Rate of answering out-of-scope queries"
}
```

## 5. Confidence Calibration

### 5.1 Temperature Scaling
```python
# Post-hoc calibration of confidence scores
def calibrate_confidence(raw_confidence, temperature):
    """Apply temperature scaling to confidence scores"""
    # Convert to logit
    logit = np.log(raw_confidence / (1 - raw_confidence))
    # Scale by temperature
    scaled_logit = logit / temperature
    # Convert back to probability
    return 1 / (1 + np.exp(-scaled_logit))
```

### 5.2 ECE Calculation
```python
def calculate_ece(confidence_scores, correct_predictions, n_bins=10):
    """Calculate Expected Calibration Error"""
    # Bin predictions by confidence
    # Compare average confidence vs accuracy per bin
    # Weight by bin size
    # Return weighted average difference
```

### 5.3 Calibration Thresholds
```yaml
confidence_thresholds:
  refusal_threshold: 0.3      # Below this, refuse to answer
  low_confidence: 0.5         # Indicate uncertainty
  high_confidence: 0.8        # Strong answer
  
  # Per-category adjustments
  category_modifiers:
    technical_complex: 0.9    # Reduce confidence for complex queries
    factual_simple: 1.1      # Boost confidence for simple facts
    out_of_scope: 0.5        # Heavily penalize out-of-scope
```

## 6. Claude Code Implementation Guide

### 6.1 Phase 1: Metrics Collection
```
"Implement a metrics collector that:
1. Wraps the existing query() method
2. Captures all intermediate scores and timings
3. Compares results against golden test expectations
4. Outputs structured metrics for analysis"
```

### 6.2 Phase 2: Parameter Search
```
"Create a parameter optimization system that:
1. Loads parameter definitions from configuration
2. Generates parameter combinations for grid search
3. Runs golden test set with each combination
4. Tracks best performing configurations
5. Handles configuration updates safely"
```

### 6.3 Phase 3: Confidence Calibration
```
"Build confidence calibration that:
1. Collects (confidence, was_correct) pairs
2. Implements temperature scaling optimization
3. Calculates ECE before and after calibration
4. Generates calibration curves for visualization"
```

### 6.4 Phase 4: Reporting Dashboard
```
"Create a Streamlit dashboard showing:
1. Parameter impact analysis
2. Before/after performance metrics
3. Confidence calibration curves
4. Per-category performance breakdown
5. Recommendations for production settings"
```

## 7. Execution Strategy

### 7.1 Week 1 Plan
- Day 1-2: Implement metrics collection
- Day 3: Create parameter registry
- Day 4: Build grid search optimizer
- Day 5: Run initial calibration

### 7.2 Week 2 Plan  
- Day 1-2: Implement confidence calibration
- Day 3: Build reporting dashboard
- Day 4: Full system calibration
- Day 5: Document optimal configuration

## 8. Success Criteria

### 8.1 Quantitative Goals
- Reduce irrelevant query false positives by 80%
- Achieve ECE < 0.15 for confidence calibration
- Maintain technical query accuracy > 85%
- Keep p95 latency < 2 seconds

### 8.2 Qualitative Goals
- Clear understanding of parameter impacts
- Reproducible optimization process
- Actionable insights for production
- Demonstration of systematic engineering approach

## 9. Output Artifacts

### 9.1 Calibration Report
```
calibration_report_[date].html
├── Executive Summary
├── Parameter Optimization Results
├── Confidence Calibration Analysis
├── Performance Improvements
├── Per-Category Breakdowns
└── Recommended Configuration
```

### 9.2 Optimal Configuration
```yaml
# optimal_config_[date].yaml
# Generated by calibration system
# Test set: golden_test_set_v1.0.0
# Date: 2024-01-20
# Overall accuracy improvement: 23%

retriever:
  sparse:
    config:
      k1: 1.0  # Reduced from 1.2
      filter_stop_words: true  # Enabled
      stop_word_sets: ["english_common"]
      
  fusion:
    config:
      fusion_weight: 0.6  # Reduced from 0.7
      semantic_floor: 0.35  # Increased from 0.3
      
confidence_scoring:
  temperature: 1.4  # Calibrated value
  refusal_threshold: 0.35  # Increased from 0.3
```

## 10. Future Extensions

- Online calibration from user feedback
- Multi-objective optimization
- Adaptive parameter adjustment
- A/B testing framework integration