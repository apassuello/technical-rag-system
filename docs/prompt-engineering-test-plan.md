# Prompt Engineering Test Plan - Claude Code Instructions

## 🎯 Testing Philosophy

This document provides **concrete test specifications** for each prompt engineering phase. Use these tests to validate implementations during Claude Code sessions. Each test includes **exact commands**, **expected outputs**, and **acceptance criteria**.

**Core Testing Principles**:
- ✅ **Regression Prevention**: All 18 existing tests must continue passing
- ✅ **Incremental Validation**: Test each component before integration
- ✅ **Performance Boundaries**: Maintain <2s response time throughout
- ✅ **Quality Metrics**: Quantifiable improvements at each phase

---

## 📋 Phase 1: Contextual Retrieval Testing (Days 1-3)

### Day 1: Context Generation Validation

#### Test 1.1: Basic Context Generation
```python
# File: tests/test_contextual_augmenter.py

def test_basic_context_generation():
    """
    Validates context generation for technical chunks
    """
    # Test Data
    document = "Chapter 3: RISC-V Instructions\n3.1 Load Instructions..."
    chunk = "The LW instruction loads a 32-bit value from memory."
    
    # Expected Context
    expected_context = "This chunk discusses the LW (Load Word) instruction from Chapter 3: RISC-V Instructions, specifically in section 3.1 about Load Instructions."
    
    # Validation
    assert len(context) > 20  # Non-trivial context
    assert "LW" in context     # Preserves technical terms
    assert "Chapter 3" in context  # Includes document structure
    
    # Performance
    assert generation_time < 100  # ms per chunk
```

**Claude Code Command**:
```bash
claude "Create test_basic_context_generation following the pattern above. Include:
1. Edge cases (empty chunks, single words, code snippets)
2. Performance measurement using time.perf_counter()
3. Technical term preservation validation
4. Document structure awareness checks"
```

#### Test 1.2: Batch Processing Performance
```python
def test_batch_context_generation():
    """
    Validates batch processing efficiency
    """
    # Test with 50 chunks (typical document)
    chunks = load_test_chunks("riscv-base-instructions.pdf")[:50]
    
    # Performance Requirements
    start_time = time.perf_counter()
    contexts = augmenter.batch_generate_contexts(chunks, batch_size=10)
    elapsed = time.perf_counter() - start_time
    
    # Assertions
    assert elapsed < 5.0  # <100ms per chunk in batch
    assert len(contexts) == 50
    assert all(len(c) > 20 for c in contexts)
    
    # Cache validation
    second_run = time.perf_counter()
    cached_contexts = augmenter.batch_generate_contexts(chunks)
    cached_time = time.perf_counter() - second_run
    
    assert cached_time < 0.1  # Near-instant with cache
```

#### Test 1.3: Context Quality Metrics
```python
def test_context_quality_improvement():
    """
    Measures retrieval improvement with context
    """
    # Ambiguous test queries
    test_queries = [
        "What is the format?",  # Ambiguous without context
        "How does it handle overflow?",
        "What are the constraints?",
        "Explain the addressing mode."
    ]
    
    # Baseline retrieval (no context)
    baseline_results = rag.query_batch(test_queries)
    baseline_accuracy = calculate_accuracy(baseline_results)
    
    # Contextual retrieval
    contextual_results = rag.query_batch_with_context(test_queries)
    contextual_accuracy = calculate_accuracy(contextual_results)
    
    # Must show improvement
    improvement = (contextual_accuracy - baseline_accuracy) / baseline_accuracy
    assert improvement >= 0.40  # Minimum 40% improvement
    
    # Log for tracking
    print(f"Baseline: {baseline_accuracy:.2%}")
    print(f"Contextual: {contextual_accuracy:.2%}")
    print(f"Improvement: {improvement:.2%}")
```

### Day 2: Embedding Strategy Testing

#### Test 1.4: Dual Embedding Validation
```python
def test_dual_embedding_generation():
    """
    Validates dual embedding approach
    """
    chunk = {
        "text": "The ADD instruction performs addition.",
        "context": "From Chapter 4: Arithmetic Instructions...",
        "metadata": {"page": 45, "section": "4.2"}
    }
    
    # Generate embeddings
    embeddings = generator.generate_dual_embeddings([chunk])
    
    # Structural validation
    assert "original" in embeddings
    assert "contextual" in embeddings
    assert "fusion" in embeddings
    
    # Dimension validation
    assert embeddings["original"].shape == (1, 384)
    assert embeddings["contextual"].shape == (1, 384)
    assert embeddings["fusion"].shape == (1, 384)
    
    # Fusion validation (weighted combination)
    expected_fusion = 0.3 * embeddings["original"] + 0.7 * embeddings["contextual"]
    assert np.allclose(embeddings["fusion"], expected_fusion, rtol=1e-5)
```

#### Test 1.5: Retrieval Fusion Testing
```python
def test_retrieval_fusion_accuracy():
    """
    Tests different fusion strategies
    """
    fusion_strategies = [
        {"original": 1.0, "contextual": 0.0},  # Baseline
        {"original": 0.7, "contextual": 0.3},  # Conservative
        {"original": 0.3, "contextual": 0.7},  # Recommended
        {"original": 0.0, "contextual": 1.0},  # Full contextual
    ]
    
    results = {}
    for strategy in fusion_strategies:
        retriever = HybridContextualRetriever(
            dense_weight=0.7,
            fusion_weights=strategy
        )
        accuracy = evaluate_retriever(retriever, test_set)
        results[str(strategy)] = accuracy
    
    # Recommended should perform best
    recommended = results["{'original': 0.3, 'contextual': 0.7}"]
    assert recommended == max(results.values())
    assert recommended > results["{'original': 1.0, 'contextual': 0.0}"] * 1.4
```

### Day 3: Integration Testing

#### Test 1.6: End-to-End Pipeline Test
```python
def test_contextual_rag_pipeline():
    """
    Full pipeline validation with contextual retrieval
    """
    # Load test document
    pdf_path = "data/test/riscv-base-instructions.pdf"
    
    # Process with contextual augmentation
    start_time = time.perf_counter()
    
    # 1. Parse with context
    chunks = parser.parse_with_context(pdf_path)
    assert all("context" in chunk for chunk in chunks)
    
    # 2. Generate dual embeddings
    embeddings = generator.generate_dual_embeddings(chunks)
    assert embeddings["fusion"].shape[0] == len(chunks)
    
    # 3. Build enhanced index
    index = build_contextual_index(chunks, embeddings)
    
    # 4. Test retrieval
    query = "How does RISC-V handle memory alignment?"
    results = index.search(query, k=5)
    
    elapsed = time.perf_counter() - start_time
    
    # Performance assertions
    assert elapsed < 15.0  # Full pipeline under 15s
    assert len(results) == 5
    assert results[0]["score"] > 0.7  # High relevance
    
    # Quality assertions
    assert any("alignment" in r["text"].lower() for r in results)
    assert results[0]["context"] is not None
```

### Phase 1 Acceptance Criteria ✅

**Before proceeding to Phase 2, verify**:
```python
# Run this validation script
def validate_phase1_completion():
    """
    Phase 1 acceptance test
    """
    # 1. All existing tests pass
    assert run_existing_tests() == "18/18 passed"
    
    # 2. Context generation working
    assert test_basic_context_generation() == "PASS"
    assert test_batch_context_generation() == "PASS"
    
    # 3. Performance targets met
    metrics = {
        "chunk_processing_time": measure_chunk_time(),
        "retrieval_improvement": measure_improvement(),
        "pipeline_latency": measure_e2e_latency()
    }
    
    assert metrics["chunk_processing_time"] < 100  # ms
    assert metrics["retrieval_improvement"] >= 0.40  # 40%+
    assert metrics["pipeline_latency"] < 2000  # ms
    
    print("✅ Phase 1 Complete - Proceed to Phase 2")
```

---

## 🧠 Phase 2: Adaptive Prompt Engineering Testing (Days 4-5)

### Day 4: Prompt Component Testing

#### Test 2.1: Query Type Detection
```python
# File: tests/test_adaptive_prompts.py

def test_query_type_detection():
    """
    Validates accurate query classification
    """
    test_cases = [
        ("What is a mutex?", "definition"),
        ("Compare SPI vs I2C", "comparison"),
        ("Debug: Stack overflow in FreeRTOS", "troubleshooting"),
        ("How to implement DMA on STM32?", "implementation"),
        ("Calculate memory for RTOS tasks", "calculation"),
        ("Can this run on 8KB RAM?", "constraint_check"),
        ("Why use pull-up resistors?", "explanation")
    ]
    
    classifier = QueryClassifier()
    
    for query, expected_type in test_cases:
        detected = classifier.detect_type(query)
        assert detected == expected_type, f"Failed: {query}"
    
    # Performance check
    avg_time = measure_classification_time(test_cases)
    assert avg_time < 5  # ms per classification
```

#### Test 2.2: Component Selection
```python
def test_prompt_component_selection():
    """
    Validates appropriate component selection
    """
    composer = AdaptivePromptComposer()
    
    # Test embedded systems query
    query = "Compare interrupt latency between Cortex-M4 and RISC-V"
    components = composer.select_components(query)
    
    assert "technical_context.embedded_systems" in components
    assert "query_types.comparison" in components
    assert "performance_metrics" in components
    
    # Test regulatory query
    query = "FDA compliance for medical device firmware"
    components = composer.select_components(query)
    
    assert "technical_context.regulatory" in components
    assert "safety_considerations" in components
```

#### Test 2.3: Few-Shot Example Selection
```python
def test_few_shot_selection():
    """
    Validates relevant example selection
    """
    # Complex query requiring few-shot
    query = "Implement power-efficient sensor polling for battery-powered IoT"
    
    prompt = composer.compose_prompt(query, context=[], metadata={})
    
    # Should include few-shot examples
    assert "Example 1:" in prompt
    assert "Example 2:" in prompt
    
    # Examples should be relevant
    assert "power" in prompt.lower()
    assert "sensor" in prompt.lower()
    
    # Simple query should not have examples
    simple_query = "What is GPIO?"
    simple_prompt = composer.compose_prompt(simple_query, context=[], metadata={})
    assert "Example 1:" not in simple_prompt
```

### Day 5: Chain-of-Thought Testing

#### Test 2.4: CoT Trigger Detection
```python
def test_cot_trigger_detection():
    """
    Validates when CoT is activated
    """
    test_cases = [
        ("Can BERT run on ESP32?", True),  # Complex feasibility
        ("What is UART?", False),  # Simple definition
        ("Design low-power BLE system", True),  # Complex design
        ("List I2C speeds", False),  # Simple list
    ]
    
    for query, should_trigger in test_cases:
        uses_cot = composer.should_use_cot(query)
        assert uses_cot == should_trigger
```

#### Test 2.5: CoT Response Quality
```python
def test_cot_response_structure():
    """
    Validates CoT produces structured reasoning
    """
    query = "Can I run TensorFlow Lite on STM32F4 with 192KB RAM?"
    context = ["STM32F4 specs...", "TFLite requirements..."]
    
    response = generator.generate_with_cot(query, context)
    
    # Should have structured sections
    assert "1. Memory requirements:" in response
    assert "2. Performance impact:" in response
    assert "3. Power consumption:" in response
    assert "4. Conclusion:" in response
    
    # Should include specific calculations
    assert "KB" in response  # Memory calculations
    assert any(word in response for word in ["feasible", "not feasible", "alternative"])
```

### Phase 2 Acceptance Criteria ✅

```python
def validate_phase2_completion():
    """
    Phase 2 acceptance test
    """
    # Component tests
    assert test_query_type_detection() == "PASS"
    assert test_prompt_component_selection() == "PASS"
    assert test_few_shot_selection() == "PASS"
    
    # Quality metrics
    metrics = evaluate_prompt_quality(test_set)
    assert metrics["relevance"] > 0.85
    assert metrics["completeness"] > 0.80
    assert metrics["technical_accuracy"] > 0.90
    
    # Token efficiency
    avg_tokens = measure_average_tokens()
    assert avg_tokens < baseline_tokens * 0.7  # 30% reduction
    
    print("✅ Phase 2 Complete - Proceed to Phase 3")
```

---

## 🏗️ Phase 3: Production Infrastructure Testing (Days 6-7)

### Day 6: Version Control Testing

#### Test 3.1: Prompt Versioning
```python
# File: tests/test_prompt_versioning.py

def test_prompt_commit_and_rollback():
    """
    Validates version control operations
    """
    manager = PromptVersionManager()
    
    # Initial prompt
    v1 = "You are a technical assistant. Answer concisely."
    commit1 = manager.commit_prompt("main_prompt", v1, {"author": "test"})
    
    # Update prompt
    v2 = "You are an embedded systems expert. Provide detailed technical answers."
    commit2 = manager.commit_prompt("main_prompt", v2, {"author": "test"})
    
    # Verify current version
    current = manager.get_current("main_prompt")
    assert current == v2
    
    # Test rollback
    manager.rollback("main_prompt", commit1)
    rolled_back = manager.get_current("main_prompt")
    assert rolled_back == v1
    
    # Test history
    history = manager.get_history("main_prompt")
    assert len(history) == 2
    assert history[0]["commit"] == commit1
```

#### Test 3.2: Diff Visualization
```python
def test_prompt_diff_generation():
    """
    Validates diff visualization
    """
    v1 = "Answer based on the provided context."
    v2 = "Answer based on the provided technical documentation context. Include code examples when relevant."
    
    diff = manager.generate_diff(v1, v2)
    
    assert "+ technical documentation" in diff
    assert "+ Include code examples when relevant." in diff
    assert "- context." in diff
```

### Day 7: A/B Testing Framework

#### Test 3.3: Experiment Creation
```python
def test_ab_experiment_setup():
    """
    Validates A/B test configuration
    """
    tester = PromptABTester()
    
    base = "Answer the technical question."
    variants = [
        "Answer the technical question with code examples.",
        "Provide a detailed technical answer with examples and explanations."
    ]
    
    exp_id = tester.create_experiment(
        base_prompt=base,
        variants=variants,
        traffic_split=[0.33, 0.33, 0.34],
        min_samples=100
    )
    
    # Verify experiment setup
    exp = tester.get_experiment(exp_id)
    assert len(exp["variants"]) == 3
    assert sum(exp["traffic_split"]) == 1.0
    assert exp["status"] == "running"
```

#### Test 3.4: Statistical Analysis
```python
def test_ab_statistical_significance():
    """
    Validates statistical analysis
    """
    # Simulate results
    results = {
        "control": {"samples": 100, "success": 70, "avg_score": 0.75},
        "variant_1": {"samples": 100, "success": 85, "avg_score": 0.88},
        "variant_2": {"samples": 100, "success": 82, "avg_score": 0.84}
    }
    
    analysis = tester.analyze_experiment(results)
    
    assert "winner" in analysis
    assert "confidence" in analysis
    assert analysis["confidence"] > 0.95  # 95% confidence
    assert "lift" in analysis  # Improvement percentage
```

### Phase 3 Acceptance Criteria ✅

```python
def validate_phase3_completion():
    """
    Phase 3 acceptance test
    """
    # Version control working
    assert test_prompt_commit_and_rollback() == "PASS"
    assert test_prompt_diff_generation() == "PASS"
    
    # A/B testing operational
    assert test_ab_experiment_setup() == "PASS"
    assert test_ab_statistical_significance() == "PASS"
    
    # Integration with RAG
    rag_with_versioning = test_rag_with_version_control()
    assert rag_with_versioning == "PASS"
    
    # Performance impact minimal
    overhead = measure_infrastructure_overhead()
    assert overhead < 50  # ms
    
    print("✅ Phase 3 Complete - Proceed to Phase 4")
```

---

## 📊 Phase 4: Evaluation & Optimization Testing (Week 4, Days 1-2)

### Day 1: RAGAS Implementation Testing

#### Test 4.1: RAGAS Metric Calculation
```python
# File: tests/test_ragas_evaluation.py

def test_ragas_metrics():
    """
    Validates RAGAS implementation
    """
    evaluator = RAGASEvaluator()
    
    # Test dataset
    test_samples = [
        {
            "question": "What is the RISC-V calling convention?",
            "context": ["RISC-V uses registers...", "The calling convention..."],
            "answer": "RISC-V calling convention uses...",
            "ground_truth": "RISC-V calling convention specifies..."
        }
    ]
    
    metrics = evaluator.evaluate(test_samples)
    
    # Verify all metrics calculated
    assert "context_precision" in metrics
    assert "context_recall" in metrics
    assert "faithfulness" in metrics
    assert "answer_relevancy" in metrics
    
    # Verify metric ranges
    for metric, value in metrics.items():
        assert 0 <= value <= 1, f"{metric} out of range: {value}"
```

#### Test 4.2: Custom Metric Integration
```python
def test_embedded_specific_metrics():
    """
    Validates custom metrics for embedded systems
    """
    custom_metrics = {
        "constraint_awareness": ConstraintAwarenessMetric(),
        "code_accuracy": CodeAccuracyMetric(),
        "safety_compliance": SafetyComplianceMetric()
    }
    
    test_case = {
        "question": "Implement PWM on STM32 with 1ms period",
        "answer": "void setupPWM() { TIM2->ARR = 1000; ... }",
        "constraints": {"mcu": "STM32F4", "clock": "16MHz"}
    }
    
    scores = {}
    for name, metric in custom_metrics.items():
        scores[name] = metric.compute(test_case)
    
    # Embedded-specific validations
    assert scores["code_accuracy"] > 0.8  # Valid code
    assert scores["constraint_awareness"] > 0.9  # Respects constraints
```

### Day 2: Automated Optimization Testing

#### Test 4.3: DSPy Optimization
```python
def test_dspy_prompt_optimization():
    """
    Validates automated optimization
    """
    # Initial RAG module
    initial_rag = RAGPromptOptimizer()
    
    # Measure baseline
    baseline_score = evaluate_on_test_set(initial_rag)
    
    # Run optimization
    optimized_rag = optimize_with_dspy(
        initial_rag,
        train_set=training_examples,
        metric=combined_metric,
        epochs=10
    )
    
    # Measure improvement
    optimized_score = evaluate_on_test_set(optimized_rag)
    
    improvement = (optimized_score - baseline_score) / baseline_score
    assert improvement > 0.15  # At least 15% improvement
    
    # Verify optimization details
    assert hasattr(optimized_rag, "optimized_prompts")
    assert len(optimized_rag.optimized_prompts) > 0
```

#### Test 4.4: End-to-End Optimization Pipeline
```python
def test_complete_optimization_pipeline():
    """
    Validates full optimization workflow
    """
    # 1. Collect baseline metrics
    baseline = collect_baseline_metrics()
    
    # 2. Run optimization
    optimization_results = run_optimization_pipeline(
        strategies=["contextual", "few_shot", "cot"],
        iterations=5,
        test_size=50
    )
    
    # 3. Validate improvements
    for strategy, results in optimization_results.items():
        assert results["final_score"] > baseline["score"]
        assert results["iterations_completed"] == 5
        assert "best_configuration" in results
    
    # 4. Select best strategy
    best_strategy = max(optimization_results.items(), 
                       key=lambda x: x[1]["final_score"])
    
    print(f"Best strategy: {best_strategy[0]}")
    print(f"Improvement: {best_strategy[1]['improvement']:.2%}")
```

### Phase 4 Acceptance Criteria ✅

```python
def validate_phase4_completion():
    """
    Final phase acceptance test
    """
    # RAGAS operational
    assert test_ragas_metrics() == "PASS"
    assert test_embedded_specific_metrics() == "PASS"
    
    # Optimization working
    assert test_dspy_prompt_optimization() == "PASS"
    assert test_complete_optimization_pipeline() == "PASS"
    
    # Final system metrics
    final_metrics = {
        "retrieval_accuracy": measure_final_retrieval(),
        "answer_quality": measure_final_quality(),
        "latency": measure_final_latency(),
        "token_efficiency": measure_final_tokens()
    }
    
    # Verify all targets met
    assert final_metrics["retrieval_accuracy"] > baseline * 1.49  # 49%+ improvement
    assert final_metrics["answer_quality"] > 0.90
    assert final_metrics["latency"] < 2000  # ms
    assert final_metrics["token_efficiency"] < baseline * 0.70
    
    print("✅ ALL PHASES COMPLETE - System Ready for Production")
    print(f"Final Metrics: {final_metrics}")
```

---

## 🚀 Continuous Integration Tests

### CI Pipeline Configuration
```yaml
# .github/workflows/prompt-engineering-tests.yml

name: Prompt Engineering Test Suite

on:
  push:
    paths:
      - 'shared_utils/generation/**'
      - 'shared_utils/retrieval/**'
      - 'tests/test_*.py'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Phase 1 - Contextual Retrieval
        run: |
          pytest tests/test_contextual_augmenter.py -v
          pytest tests/test_dual_embeddings.py -v
          
      - name: Phase 2 - Adaptive Prompts
        run: |
          pytest tests/test_adaptive_prompts.py -v
          pytest tests/test_chain_of_thought.py -v
          
      - name: Phase 3 - Infrastructure
        run: |
          pytest tests/test_prompt_versioning.py -v
          pytest tests/test_ab_testing.py -v
          
      - name: Phase 4 - Evaluation
        run: |
          pytest tests/test_ragas_evaluation.py -v
          pytest tests/test_optimization.py -v
          
      - name: Integration Tests
        run: |
          pytest tests/test_integration.py -v --slow
          
      - name: Performance Benchmarks
        run: |
          python benchmarks/prompt_performance.py
```

---

## 📝 Test Data Management

### Creating Test Sets
```python
# File: tests/fixtures/prompt_test_data.py

PROMPT_TEST_CASES = {
    "ambiguous_queries": [
        # Queries that benefit from context
        {"query": "What is the format?", "context_needed": True},
        {"query": "How much memory?", "context_needed": True},
    ],
    
    "technical_queries": [
        # Domain-specific test cases
        {"query": "Implement RTOS mutex", "type": "implementation"},
        {"query": "I2C vs SPI latency", "type": "comparison"},
    ],
    
    "constraint_queries": [
        # Hardware constraint validation
        {"query": "Run on 8KB RAM?", "constraints": {"ram": "8KB"}},
        {"query": "Battery life impact?", "constraints": {"power": "coin cell"}},
    ]
}
```

### Performance Benchmarks
```python
# File: benchmarks/prompt_performance.py

PERFORMANCE_TARGETS = {
    "context_generation": 100,  # ms per chunk
    "embedding_generation": 10,  # ms per chunk
    "prompt_composition": 5,  # ms per query
    "full_pipeline": 2000,  # ms end-to-end
}

def run_performance_suite():
    """Run all performance benchmarks"""
    results = {}
    
    for component, target in PERFORMANCE_TARGETS.items():
        actual = measure_component_performance(component)
        passed = actual <= target
        results[component] = {
            "target": target,
            "actual": actual,
            "passed": passed
        }
    
    return results
```

---

## 🎯 Claude Code Testing Commands

### Quick Test Commands

```bash
# Test individual components
claude "Run test_basic_context_generation and fix any failures. Show the test output and explain fixes."

# Test integration
claude "Run the Phase 1 acceptance criteria tests. If any fail, diagnose the issue and provide fixes."

# Performance testing
claude "Create and run a performance benchmark for contextual retrieval. Target: <100ms per chunk with caching."

# Quality validation
claude "Implement and run the RAGAS evaluation on our test set. Show metrics and suggest improvements."
```

### Debugging Commands

```bash
# Debug test failures
claude "Test test_dual_embedding_generation is failing with shape mismatch. Here's the error: [error]. Debug and fix."

# Performance optimization
claude "The context generation is taking 150ms per chunk. Profile the code and optimize to reach <100ms target."

# Integration issues
claude "The existing tests are failing after adding contextual retrieval. Ensure backward compatibility and fix breaks."
```

---

## 📊 Test Reporting Template

```markdown
## Phase X Test Report

### Summary
- **Total Tests**: XX
- **Passed**: XX
- **Failed**: XX
- **Performance**: ✅/❌ Met targets

### Key Metrics
- **Retrieval Improvement**: XX%
- **Response Quality**: X.XX/1.0
- **Average Latency**: XXXms
- **Token Efficiency**: -XX%

### Issues Found
1. [Issue description]
   - Impact: [High/Medium/Low]
   - Fix: [Description or PR link]

### Next Steps
- [ ] Address failing tests
- [ ] Optimize performance bottlenecks
- [ ] Update documentation
```

---

**Remember**: Each test should be **runnable in isolation** during Claude Code sessions. Use this document as your testing checklist and validation guide throughout implementation. The tests ensure your prompt engineering enhancements maintain the high quality standards established in your Week 2 implementation while delivering the promised 49-67% improvements.