# Epic 1 Systematic Test Failure Resolution Prompt

## Mission
Systematically resolve the 14 Epic 1 test failures to achieve 95%+ success rate using parallel agent orchestration for analysis, solution design, implementation, and validation.

## Current Status
- **Tests Passing**: 68/82 (82.9% success rate)
- **Target**: 78/82 (95% success rate)
- **Gap**: 10 tests need to be fixed
- **Failures**: 14 tests across 3 components

## Phase 1: Parallel Component Analysis

### Use root-cause-analyzer for each component simultaneously:

```
1. Use the root-cause-analyzer agent to investigate AdaptiveRouter test failures:
   - test_routing_decision_accuracy
   - test_fallback_chain_activation  
   - test_state_preservation_during_fallback
   Analyze why router selection doesn't match test expectations in tests/epic1/phase2/test_adaptive_router.py

2. Use the root-cause-analyzer agent to investigate Epic1AnswerGenerator test failures:
   - test_end_to_end_multi_model_workflow (missing cost metadata)
   - test_backward_compatibility_validation (legacy config)
   - test_backward_compatibility_component_factory (factory integration)
   - test_cost_budget_graceful_degradation (budget enforcement)
   - test_routing_overhead_measurement (performance tracking)
   - test_configuration_validation (config validation)
   - test_model_availability_handling (availability checks)
   Analyze implementation gaps in src/components/generators/epic1_answer_generator.py

3. Use the root-cause-analyzer agent to investigate Infrastructure test failures:
   - test_time_range_filtering (CostTracker edge case)
   - test_real_openai_integration (API key requirement)
   Analyze edge cases in src/components/generators/llm_adapters/cost_tracker.py
```

## Phase 2: Parallel Solution Design

### Use software-architect and specs-implementer for each component:

```
4. Use the software-architect agent to design solution for AdaptiveRouter issues:
   - How to align router model selection with test expectations
   - Should we fix the router logic or the test expectations?
   - Design backward-compatible solution

5. Use the specs-implementer agent to design Epic1AnswerGenerator enhancements from specification:
   - Cost tracking metadata structure (cost_usd, input_tokens, output_tokens)
   - Backward compatibility layer for legacy configurations
   - Budget enforcement mechanism with graceful degradation
   - Performance measurement integration
   - Configuration validation schema
   - Model availability checking logic

6. Use the software-architect agent to design Infrastructure fixes:
   - CostTracker time filtering edge case solution
   - Real API test skipping strategy
```

## Phase 3: Parallel Implementation

### Use component-implementer for each component with test-driven approach:

```
7. Use the test-driven-developer agent to write fix validation tests for AdaptiveRouter:
   - Test for corrected model selection behavior
   - Test for proper mock alignment
   - Test for state preservation

8. Use the component-implementer agent to implement AdaptiveRouter fixes:
   - Fix model selection logic OR adjust test expectations
   - Ensure fallback chain works with actual router behavior
   - Maintain state preservation during fallbacks

9. Use the test-driven-developer agent to write fix validation tests for Epic1AnswerGenerator:
   - Test for cost metadata presence in answers
   - Test for legacy config handling
   - Test for budget enforcement behavior
   - Test for performance measurement
   - Test for config validation
   - Test for model availability handling

10. Use the component-implementer agent to implement Epic1AnswerGenerator enhancements:
    - Add cost tracking integration:
      * Capture cost_usd from CostTracker
      * Add input_tokens and output_tokens to metadata
    - Implement backward compatibility layer:
      * Support legacy single-model configurations
      * Convert old format to new Epic1 format
    - Add budget enforcement:
      * Track cumulative costs
      * Implement graceful degradation to cheaper models
    - Add performance measurement:
      * Track routing overhead
      * Add timing metrics
    - Implement configuration validation:
      * Validate required fields
      * Check model configurations
    - Add model availability checking:
      * Verify model accessibility
      * Handle unavailable models gracefully

11. Use the component-implementer agent to implement Infrastructure fixes:
    - Fix CostTracker time range filtering edge case
    - Add proper skip decorator for real API test
```

## Phase 4: Component-Level Testing

### Use test-runner for each component independently:

```
12. Use the test-runner agent to validate AdaptiveRouter fixes:
    Run: pytest tests/epic1/phase2/test_adaptive_router.py -xvs
    Expected: All 3 router tests should pass

13. Use the test-runner agent to validate Epic1AnswerGenerator fixes:
    Run: pytest tests/epic1/phase2/test_epic1_answer_generator.py -xvs
    Expected: At least 6 of 7 generator tests should pass

14. Use the test-runner agent to validate Infrastructure fixes:
    Run: pytest tests/epic1/phase2/test_cost_tracker.py -xvs
    Expected: Time filtering test should pass, API test can skip
```

## Phase 5: Integration Validation

### Use implementation-validator for comprehensive validation:

```
15. Use the implementation-validator agent to perform final Epic 1 validation:
    - Run complete Epic 1 test suite
    - Verify 95% success rate achieved
    - Check for any regression in previously passing tests
    - Validate performance metrics
    - Confirm backward compatibility
    - Generate final Epic 1 completion report
```

## Phase 6: Final System Test (No Agent)

```
16. Run complete Epic 1 test suite:
    pytest tests/epic1/ -xvs --tb=short
    
    Expected Results:
    - Total: 82 tests
    - Passing: 78+ tests
    - Success Rate: 95%+
    - No regression in domain integration tests
```

## Success Criteria

### Must Have (for 95% target):
- [ ] AdaptiveRouter test alignment (3 tests)
- [ ] Epic1AnswerGenerator cost tracking (1 test)
- [ ] Epic1AnswerGenerator backward compatibility (2 tests)
- [ ] Epic1AnswerGenerator budget enforcement (1 test)
- [ ] Epic1AnswerGenerator performance tracking (1 test)
- [ ] CostTracker edge case fix (1 test)

### Nice to Have (for 100%):
- [ ] Epic1AnswerGenerator config validation (1 test)
- [ ] Epic1AnswerGenerator model availability (1 test)
- [ ] Real API integration test (1 test - can skip)

## Parallel Execution Strategy

The agents can work in parallel on different components:
- **Stream 1**: AdaptiveRouter (root-cause → architect → implement → test)
- **Stream 2**: Epic1AnswerGenerator (root-cause → specs → implement → test)
- **Stream 3**: Infrastructure (root-cause → architect → implement → test)

All streams converge at Phase 5 for integration validation.

## Implementation Notes

### Key Files to Modify:
1. `src/components/generators/epic1_answer_generator.py` - Main enhancement target
2. `src/components/generators/routing/adaptive_router.py` - Minor adjustments
3. `src/components/generators/llm_adapters/cost_tracker.py` - Edge case fix
4. `tests/epic1/phase2/test_adaptive_router.py` - Test alignment
5. `tests/epic1/phase2/test_epic1_answer_generator.py` - Test expectations

### Risk Mitigation:
- Create backup of current working state before changes
- Test each component fix independently before integration
- Use version control to track changes per component
- Maintain backward compatibility throughout

## Expected Timeline

- **Phase 1**: 30 minutes (parallel analysis)
- **Phase 2**: 45 minutes (parallel design)
- **Phase 3**: 2 hours (parallel implementation)
- **Phase 4**: 30 minutes (parallel testing)
- **Phase 5**: 20 minutes (integration validation)
- **Phase 6**: 10 minutes (final test run)

**Total**: ~4 hours with parallel execution

## Command Sequence for Claude Code

```bash
# Start three parallel terminal sessions in Claude Code

# Terminal 1: AdaptiveRouter stream
"Analyze and fix the 3 AdaptiveRouter test failures using root-cause-analyzer, then architect solution, implement with tests, and validate"

# Terminal 2: Epic1AnswerGenerator stream  
"Analyze and fix the 7 Epic1AnswerGenerator test failures using root-cause-analyzer and specs-implementer, then implement all missing features with test-driven approach"

# Terminal 3: Infrastructure stream
"Fix the CostTracker time filtering edge case and handle the real API test appropriately"

# After all complete, main terminal:
"Run implementation-validator to verify Epic 1 is complete with 95% success rate"
```

This systematic approach ensures each component is properly analyzed, solutions are well-designed, implementations are test-driven, and the final system achieves the 95% success target.