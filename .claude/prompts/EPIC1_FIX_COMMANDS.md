# Epic 1 Test Resolution - Agent Orchestration Commands

Copy and paste these commands into Claude Code to systematically fix all Epic 1 test failures using your agent ecosystem.

## 🎯 Current Situation
- **Status**: 68/82 tests passing (82.9%)
- **Target**: 78/82 tests passing (95%)
- **Failures**: 14 tests across 3 components

---

## Phase 1: Analysis (Run These Simultaneously)

### Terminal 1 - AdaptiveRouter Analysis
```bash
Use the root-cause-analyzer agent to investigate why these 3 AdaptiveRouter tests are failing in tests/epic1/phase2/test_adaptive_router.py:
1. test_routing_decision_accuracy - router selects ollama but test expects mistral
2. test_fallback_chain_activation - primary model mismatch with test mocks
3. test_state_preservation_during_fallback - model selection vs test expectations

Focus on whether the issue is in the router logic (src/components/generators/routing/adaptive_router.py) or test expectations.
```

### Terminal 2 - Epic1AnswerGenerator Analysis
```bash
Use the root-cause-analyzer agent to investigate why these 7 Epic1AnswerGenerator tests are failing in tests/epic1/phase2/test_epic1_answer_generator.py:
1. test_end_to_end_multi_model_workflow - missing cost_usd and input_tokens in answer metadata
2. test_backward_compatibility_validation - legacy config format not supported
3. test_backward_compatibility_component_factory - factory registration incomplete
4. test_cost_budget_graceful_degradation - budget enforcement not implemented
5. test_routing_overhead_measurement - performance tracking missing
6. test_configuration_validation - config validation logic missing
7. test_model_availability_handling - availability checks not implemented

Examine src/components/generators/epic1_answer_generator.py for implementation gaps.
```

### Terminal 3 - Infrastructure Analysis
```bash
Use the root-cause-analyzer agent to investigate these 2 infrastructure test failures:
1. test_time_range_filtering in CostTracker - edge case with time filtering
2. test_real_openai_integration - requires actual API key

Check src/components/generators/llm_adapters/cost_tracker.py for the time filtering issue.
```

---

## Phase 2: Solution Design (After Analysis)

### For AdaptiveRouter
```bash
Use the software-architect agent to design the solution for AdaptiveRouter test failures based on the root cause analysis. Should we:
1. Modify the router's model selection logic to match test expectations?
2. Update the test expectations to match the router's actual behavior?
3. Implement a configuration that satisfies both?

Provide specific implementation recommendations.
```

### For Epic1AnswerGenerator
```bash
Use the specs-implementer agent to design the Epic1AnswerGenerator enhancements based on these specifications:

1. Cost Tracking: Add cost_usd, input_tokens, output_tokens to answer metadata
2. Backward Compatibility: Support legacy single-model configurations
3. Budget Enforcement: Implement cumulative cost tracking with graceful degradation
4. Performance Measurement: Add routing overhead tracking
5. Configuration Validation: Validate required fields and model configs
6. Model Availability: Check model accessibility with fallback handling

Create the implementation structure for src/components/generators/epic1_answer_generator.py
```

### For Infrastructure
```bash
Use the software-architect agent to design fixes for:
1. CostTracker time_range_filtering edge case - propose robust datetime handling
2. Real API test - recommend skip strategy or mock approach
```

---

## Phase 3: Implementation (After Design)

### AdaptiveRouter Implementation
```bash
Use the component-implementer agent to implement the AdaptiveRouter fixes based on the architect's solution:
- Apply the recommended changes to either router logic or test expectations
- Ensure all 3 tests will pass after implementation
- Maintain backward compatibility
File: src/components/generators/routing/adaptive_router.py or tests/epic1/phase2/test_adaptive_router.py
```

### Epic1AnswerGenerator Implementation
```bash
Use the component-implementer agent to implement all Epic1AnswerGenerator enhancements from the specs-implementer design:

In src/components/generators/epic1_answer_generator.py:
1. Integrate CostTracker to add cost_usd, input_tokens, output_tokens to metadata
2. Add backward compatibility layer for legacy configurations
3. Implement budget enforcement with graceful degradation
4. Add performance measurement for routing overhead
5. Implement configuration validation
6. Add model availability checking

Ensure each feature addresses its corresponding test failure.
```

### Infrastructure Implementation
```bash
Use the component-implementer agent to:
1. Fix the CostTracker time_range_filtering edge case in src/components/generators/llm_adapters/cost_tracker.py
2. Add appropriate skip decorator or mock for test_real_openai_integration
```

---

## Phase 4: Component Testing (After Implementation)

### Test Each Component
```bash
# Test AdaptiveRouter fixes
Use the test-runner agent to validate AdaptiveRouter: pytest tests/epic1/phase2/test_adaptive_router.py -xvs

# Test Epic1AnswerGenerator fixes  
Use the test-runner agent to validate Epic1AnswerGenerator: pytest tests/epic1/phase2/test_epic1_answer_generator.py -xvs

# Test Infrastructure fixes
Use the test-runner agent to validate Infrastructure: pytest tests/epic1/phase2/test_cost_tracker.py tests/epic1/phase2/test_llm_adapters.py -xvs
```

---

## Phase 5: Final Validation

### Integration Test
```bash
Use the implementation-validator agent to perform comprehensive Epic 1 validation:
- Run the complete Epic 1 test suite
- Verify we achieved 95%+ success rate (78+ tests passing)
- Check for any regressions
- Generate Epic 1 completion report
```

### Final System Test (No Agent)
```bash
# Run complete test suite to confirm success
pytest tests/epic1/ -xvs --tb=short

# Expected: 78+/82 tests passing (95%+ success rate)
```

---

## 🚀 Quick Start Commands

If you want to run everything in sequence in a single terminal:

```bash
# Complete Epic 1 fix workflow
"I need to fix the remaining 14 Epic 1 test failures to achieve 95% success rate. There are 3 AdaptiveRouter failures, 7 Epic1AnswerGenerator failures, and 2 infrastructure failures. Please use root-cause-analyzer to investigate each component's failures, then use appropriate agents to design and implement solutions, and finally validate the fixes achieve our 95% target."
```

Or for maximum parallelization, open 3 terminals and run simultaneously:

**Terminal 1:**
```bash
"Fix the 3 AdaptiveRouter test failures in tests/epic1/phase2/test_adaptive_router.py"
```

**Terminal 2:**
```bash
"Fix the 7 Epic1AnswerGenerator test failures by implementing cost tracking, backward compatibility, budget enforcement, and other missing features"
```

**Terminal 3:**
```bash
"Fix the CostTracker time filtering edge case and handle the real API test"
```

Then after all complete:
```bash
"Validate Epic 1 achieves 95% success rate with all fixes integrated"
```

---

## Expected Results

After running these commands:
- ✅ AdaptiveRouter: 3/3 tests fixed
- ✅ Epic1AnswerGenerator: 6-7/7 tests fixed  
- ✅ Infrastructure: 1-2/2 tests fixed
- ✅ **Total**: 78+/82 tests passing (95%+ success rate)
- ✅ Epic 1 marked as COMPLETE and production-ready

Your agent ecosystem will handle the analysis, design, implementation, and validation automatically!