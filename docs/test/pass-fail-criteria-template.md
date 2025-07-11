# PASS/FAIL Criteria Template
## RAG Technical Documentation System

**Version**: 1.0  
**Purpose**: Standardized template for defining test acceptance criteria  
**Last Updated**: July 2025

---

## 1. Template Overview

This template provides a standardized format for defining PASS/FAIL criteria across all test plans. Clear, measurable criteria ensure objective test evaluation and automated validation.

---

## 2. Standard Test Case Format

```yaml
Test ID: [COMPONENT-TYPE-NUMBER]
Title: [Descriptive test title]
Requirement: [Link to architecture/component spec]
Priority: [High/Medium/Low]
Type: [Functional/Performance/Security/Integration/etc.]

Preconditions:
  - [Required system state]
  - [Test data requirements]
  - [Environment configuration]

Test Steps:
  1. [Specific, reproducible action]
  2. [Measurable observation point]
  3. [Validation step]

PASS Criteria:
  Functional:
    - [Specific behavior observed]
    - [Output matches expected format]
  Performance:
    - [Metric] < [Threshold] (e.g., Response time < 100ms)
    - [Throughput] > [Minimum] (e.g., Throughput > 1000 req/s)
  Quality:
    - [Quality metric] > [Threshold] (e.g., Accuracy > 95%)
    - [Error rate] < [Maximum] (e.g., Error rate < 0.1%)

FAIL Criteria:
  - Any PASS criterion not met
  - [Specific failure condition]
  - [Unacceptable behavior observed]
  - [System crash or data corruption]

Exit Criteria:
  - All test steps completed
  - Results recorded in test management system
  - Defects logged if applicable

Automated Validation:
  - Script: [test_script_name.py]
  - Metrics collected: [List of automated metrics]
  - Thresholds file: [thresholds.yaml]
```

---

## 3. Criteria Types and Examples

### 3.1 Functional Criteria

**Definition**: Validates that the system performs its intended functions correctly.

**Examples**:
```yaml
PASS Criteria:
  Functional:
    - All PDF pages extracted without errors
    - Text maintains original formatting
    - Metadata includes page numbers and structure
    - No duplicate content in output
```

### 3.2 Performance Criteria

**Definition**: Validates that the system meets performance requirements.

**Examples**:
```yaml
PASS Criteria:
  Performance:
    - Document processing rate > 1M chars/second
    - p95 latency < 50ms
    - Memory usage < 500MB for 100MB document
    - CPU utilization < 80% under load
```

### 3.3 Quality Criteria

**Definition**: Validates output quality and accuracy.

**Examples**:
```yaml
PASS Criteria:
  Quality:
    - Chunk boundaries preserve complete sentences (100%)
    - Citation accuracy > 98%
    - Retrieval precision @ 10 > 0.85
    - Answer relevance score > 0.9
```

### 3.4 Reliability Criteria

**Definition**: Validates system stability and error handling.

**Examples**:
```yaml
PASS Criteria:
  Reliability:
    - No crashes during 4-hour test run
    - Error recovery successful within 30 seconds
    - All transactions complete or rollback cleanly
    - Graceful degradation under resource pressure
```

### 3.5 Security Criteria

**Definition**: Validates security controls and data protection.

**Examples**:
```yaml
PASS Criteria:
  Security:
    - Input validation rejects malicious payloads
    - PII detected and masked in all outputs
    - API keys not exposed in logs or errors
    - Access control enforced for all endpoints
```

---

## 4. Quantitative Threshold Guidelines

### 4.1 Performance Thresholds

| Metric | Excellent | Acceptable | Fail |
|--------|-----------|------------|------|
| Response Time (p50) | < 500ms | < 1000ms | ≥ 1000ms |
| Response Time (p95) | < 1500ms | < 2000ms | ≥ 2000ms |
| Throughput | > 1000 req/s | > 500 req/s | ≤ 500 req/s |
| Error Rate | < 0.01% | < 0.1% | ≥ 0.1% |

### 4.2 Quality Thresholds

| Metric | Excellent | Acceptable | Fail |
|--------|-----------|------------|------|
| Accuracy | > 98% | > 95% | ≤ 95% |
| Precision | > 0.9 | > 0.85 | ≤ 0.85 |
| Recall | > 0.9 | > 0.85 | ≤ 0.85 |
| F1 Score | > 0.9 | > 0.85 | ≤ 0.85 |

### 4.3 Resource Thresholds

| Metric | Excellent | Acceptable | Fail |
|--------|-----------|------------|------|
| CPU Usage | < 60% | < 80% | ≥ 80% |
| Memory Usage | < 70% | < 85% | ≥ 85% |
| Disk I/O | < 50MB/s | < 100MB/s | ≥ 100MB/s |
| Network Latency | < 10ms | < 50ms | ≥ 50ms |

---

## 5. Exit Criteria Standards

### 5.1 Test Execution Exit Criteria

**Successful Test Execution**:
- All test steps completed as documented
- All PASS criteria met
- Results recorded with evidence
- No blocking issues encountered

**Failed Test Execution**:
- One or more FAIL criteria triggered
- Test blocked by environment issues
- Critical defect prevents completion
- System instability observed

### 5.2 Test Phase Exit Criteria

**Component Testing Exit**:
- 100% of high priority tests executed
- > 95% of medium priority tests executed
- All critical defects resolved
- Performance within 10% of targets

**Integration Testing Exit**:
- All component interfaces validated
- Data flow tests passing
- No integration defects of high severity
- Error handling verified

**System Testing Exit**:
- All business scenarios validated
- End-to-end performance acceptable
- User acceptance criteria met
- Operational readiness confirmed

---

## 6. Automated Validation

### 6.1 Threshold Configuration

```yaml
# thresholds.yaml
component: document_processor
tests:
  pdf_extraction:
    performance:
      processing_rate: 
        min: 1000000  # chars/second
      memory_usage:
        max: 524288000  # 500MB in bytes
    quality:
      extraction_accuracy:
        min: 0.98
      metadata_completeness:
        min: 1.0
```

### 6.2 Validation Script Structure

```python
# validate_test_results.py
def validate_criteria(test_id, results, thresholds):
    """
    Validates test results against defined thresholds
    Returns: (pass/fail, details)
    """
    passed = True
    details = []
    
    for metric, value in results.items():
        threshold = thresholds.get(metric)
        if threshold:
            if 'min' in threshold and value < threshold['min']:
                passed = False
                details.append(f"{metric}: {value} < {threshold['min']}")
            if 'max' in threshold and value > threshold['max']:
                passed = False
                details.append(f"{metric}: {value} > {threshold['max']}")
    
    return passed, details
```

---

## 7. Best Practices

### 7.1 Writing Effective Criteria

1. **Be Specific**: Use exact values, not vague terms
2. **Be Measurable**: Criteria must be objectively verifiable
3. **Be Realistic**: Set achievable thresholds based on requirements
4. **Be Complete**: Cover all aspects of the requirement

### 7.2 Common Mistakes to Avoid

1. **Subjective Criteria**: "System performs well" ❌
   - Better: "Response time < 100ms for 95% of requests" ✓

2. **Unmeasurable Criteria**: "User-friendly interface" ❌
   - Better: "All actions complete within 3 clicks" ✓

3. **Missing Thresholds**: "Fast processing" ❌
   - Better: "Processing rate > 1M chars/second" ✓

4. **Ambiguous Conditions**: "Handles errors gracefully" ❌
   - Better: "Returns specific error code and recovers within 30s" ✓

---

## 8. Integration with Test Management

### 8.1 Test Result Recording

```yaml
Test Execution Record:
  test_id: C2-FUNC-001
  execution_date: 2025-07-11
  environment: staging
  
  results:
    functional:
      pdf_extraction: PASS
      metadata_preservation: PASS
    performance:
      processing_rate: 1250000  # PASS (> 1M)
      memory_usage: 450000000   # PASS (< 500MB)
    quality:
      accuracy: 0.99            # PASS (> 0.98)
  
  overall_result: PASS
  evidence: 
    - logs/test_c2_func_001_20250711.log
    - screenshots/extraction_results.png
```

### 8.2 Defect Linking

When a test fails, link defects with clear traceability:
- Failed criterion
- Actual vs expected values
- Evidence of failure
- Impact assessment

---

## References

- [MASTER-TEST-STRATEGY.md](./MASTER-TEST-STRATEGY.md) - Overall testing approach
- Test automation frameworks documentation
- Industry standards (ISO 29119, IEEE 829)