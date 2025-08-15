# Copy-Paste This Into Claude Code

## The Ultimate Epic 1 Fix Command

Just copy and paste this single command into Claude Code:

```bash
I need to fix Epic 1 test failures to achieve 95% success rate. Current status: 68/82 tests passing (82.9%). 

There are 14 failures across 3 components:
- AdaptiveRouter: 3 test failures (model selection mismatches)
- Epic1AnswerGenerator: 7 test failures (missing cost tracking, backward compatibility, budget enforcement, performance tracking)
- Infrastructure: 2 test failures (CostTracker edge case, API test)

Please orchestrate the agents to:
1. Have root-cause-analyzer investigate each component's failures in parallel
2. Have software-architect design AdaptiveRouter fixes, specs-implementer design Epic1AnswerGenerator features, and software-architect design Infrastructure fixes
3. Have test-driven-developer write tests for the fixes
4. Have component-implementer implement all solutions
5. Have test-runner validate each component
6. Have implementation-validator confirm we achieved 95% success rate

The agents should work on all three components in parallel where possible. Focus on Epic1AnswerGenerator as it has the most failures and highest impact.
```

## Or Use Three Parallel Commands

Open 3 terminals in Claude Code and run simultaneously:

### Terminal 1:
```bash
Fix the 3 AdaptiveRouter test failures where the router selects ollama but tests expect mistral. Decide whether to fix router logic or test expectations.
```

### Terminal 2:
```bash
Fix the 7 Epic1AnswerGenerator test failures by implementing: cost tracking metadata (cost_usd, input_tokens, output_tokens), backward compatibility for legacy configs, budget enforcement with graceful degradation, performance measurement, config validation, and model availability checking.
```

### Terminal 3:
```bash
Fix the CostTracker time_range_filtering edge case and add appropriate handling for the test_real_openai_integration test that requires an API key.
```

### Then in main terminal after all complete:
```bash
Run implementation-validator to confirm Epic 1 achieves 95% success rate and generate completion report.
```

## What Will Happen

Your agents will automatically:

1. **root-cause-analyzer** investigates why each test fails
2. **software-architect** and **specs-implementer** design solutions
3. **test-driven-developer** writes validation tests
4. **component-implementer** implements the fixes
5. **test-runner** validates each component works
6. **implementation-validator** confirms 95% target achieved

Expected time: ~4 hours
Expected result: 78+/82 tests passing (95%+ success rate)

## Quick Validation

After completion, run:
```bash
pytest tests/epic1/ --tb=short
```

Should show: "78 passed" or better out of 82 total tests.