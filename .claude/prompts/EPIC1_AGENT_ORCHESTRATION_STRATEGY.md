# Epic 1 Agent Orchestration Strategy & Executable Prompts

> **This document serves two purposes:**
> 1. 📚 **Reference Guide** - Understand the complete orchestration strategy
> 2. 🚀 **Executable Prompts** - Copy sections marked with "📋 EXECUTABLE" directly into Claude Code

---

## 📋 EXECUTABLE: Master Orchestration Command

Copy this entire section into Claude Code for complete autonomous orchestration:

```bash
I need to achieve 95% test success rate for Epic 1 using intelligent agent orchestration.

Current State:
- Tests Passing: 68/82 (82.9%)
- Target: 78/82 (95.0%)
- Components with failures:
  * AdaptiveRouter: 3 test failures
  * Epic1AnswerGenerator: 7 test failures  
  * Infrastructure: 2 test failures

Execute the following orchestration strategy:

PHASE 1 - PARALLEL ANALYSIS (30 minutes):
- Stream 1: root-cause-analyzer investigates AdaptiveRouter test failures (test_routing_decision_accuracy, test_fallback_chain_activation, test_state_preservation_during_fallback)
- Stream 2: root-cause-analyzer investigates Epic1AnswerGenerator gaps (missing cost tracking, no backward compatibility, no budget enforcement, missing performance measurement)
- Stream 3: root-cause-analyzer investigates Infrastructure issues (CostTracker time filtering, API test requirements)

PHASE 2 - PARALLEL DESIGN (45 minutes):
- Stream 1: software-architect designs AdaptiveRouter solution
- Stream 2: specs-implementer creates Epic1AnswerGenerator specifications
- Stream 3: software-architect designs Infrastructure fixes

PHASE 3 - IMPLEMENTATION (2 hours):
- test-driven-developer writes validation tests for all fixes
- component-implementer implements all solutions following TDD
- Maintain backward compatibility throughout

PHASE 4 - VALIDATION (30 minutes):
- test-runner validates each component independently
- implementation-validator performs integration testing
- performance-profiler confirms no regression

PHASE 5 - CERTIFICATION (30 minutes):
- implementation-validator certifies 95% achievement
- documentation-specialist updates Epic 1 docs
- Generate completion report

Execute with parallel streams where possible. Prioritize Epic1AnswerGenerator as it has the most failures.
```

---

## 📚 REFERENCE: Complete Strategy Documentation

### Mission Parameters
- **Current State**: 68/82 tests passing (82.9%)
- **Target State**: 78/82 tests passing (95.0%)
- **Gap Analysis**: 10 tests must be fixed
- **Components**: AdaptiveRouter (3), Epic1AnswerGenerator (7), Infrastructure (4)

### Agent Orchestration Matrix

```
Component              Agents Assigned                    Parallel  Priority
─────────────────────────────────────────────────────────────────────────
AdaptiveRouter     →  root-cause-analyzer                  ✓        HIGH
                   →  software-architect                   ✓        HIGH
                   →  component-implementer                          HIGH
                   →  test-runner                                    HIGH

Epic1AnswerGenerator → root-cause-analyzer                  ✓        CRITICAL
                   →  specs-implementer                    ✓        CRITICAL  
                   →  test-driven-developer                ✓        CRITICAL
                   →  component-implementer                          CRITICAL
                   →  test-runner                                    CRITICAL

Infrastructure     →  root-cause-analyzer                  ✓        MEDIUM
                   →  software-architect                   ✓        MEDIUM
                   →  component-implementer                          MEDIUM
                   →  test-runner                                    MEDIUM

Integration        →  implementation-validator                      FINAL
                   →  performance-profiler                           FINAL
                   →  documentation-specialist                        FINAL
```

---

## 📋 EXECUTABLE: Component-Specific Workflows

### Option A: AdaptiveRouter Focused Command

```bash
Execute AdaptiveRouter resolution workflow:

1. root-cause-analyzer: Investigate why these 3 tests fail:
   - test_routing_decision_accuracy (expects mistral, gets ollama)
   - test_fallback_chain_activation (primary model mismatch)
   - test_state_preservation_during_fallback (model selection issue)
   Focus: Is the issue in router logic or test expectations?

2. software-architect: Design solution based on root cause
   - Option A: Modify router selection algorithm
   - Option B: Align test expectations with router
   - Option C: Configuration-based resolution

3. component-implementer: Implement the architected solution
   - Apply to src/components/generators/routing/adaptive_router.py
   - Or update tests/epic1/phase2/test_adaptive_router.py
   - Maintain backward compatibility

4. test-runner: Validate all 3 AdaptiveRouter tests pass
```

### Option B: Epic1AnswerGenerator Focused Command

```bash
Execute Epic1AnswerGenerator complete implementation:

1. root-cause-analyzer: Identify all 7 implementation gaps:
   - Cost tracking metadata (cost_usd, input_tokens, output_tokens)
   - Backward compatibility layer for legacy configs
   - Budget enforcement with graceful degradation
   - Performance measurement and routing overhead
   - Configuration validation logic
   - Model availability checking

2. specs-implementer: Create detailed specifications for each feature:
   Cost Tracking:
     - Integrate with CostTracker
     - Add metadata to Answer objects
     - Track cumulative costs
   
   Backward Compatibility:
     - Detect legacy configuration format
     - Auto-convert to Epic1 format
     - Maintain existing API contracts

   Budget Enforcement:
     - Real-time cost accumulation
     - Threshold monitoring at $0.01 precision
     - Graceful degradation to cheaper models

3. test-driven-developer: Write comprehensive validation tests

4. component-implementer: Implement all 7 features in 
   src/components/generators/epic1_answer_generator.py

5. test-runner: Validate 7/7 Epic1AnswerGenerator tests pass
```

### Option C: Infrastructure Focused Command

```bash
Execute Infrastructure fixes:

1. root-cause-analyzer: Investigate 2 infrastructure issues:
   - CostTracker time_range_filtering datetime edge case
   - test_real_openai_integration API key requirement

2. software-architect: Design robust solutions:
   - Datetime handling improvements
   - Test skip strategy for API tests

3. component-implementer: Implement fixes in
   src/components/generators/llm_adapters/cost_tracker.py

4. test-runner: Validate infrastructure tests handled appropriately
```

---

## 📋 EXECUTABLE: Parallel Execution Commands

### For Maximum Speed - Open 3 Terminals

**Terminal 1:**
```bash
Use agent orchestration to fix AdaptiveRouter: 
root-cause-analyzer → software-architect → component-implementer → test-runner 
for the 3 failing tests where router selects wrong models
```

**Terminal 2:**
```bash
Use agent orchestration to implement Epic1AnswerGenerator features:
root-cause-analyzer → specs-implementer → test-driven-developer → component-implementer → test-runner
for all 7 missing features including cost tracking, backward compatibility, and budget enforcement
```

**Terminal 3:**
```bash
Use agent orchestration to fix Infrastructure:
root-cause-analyzer → software-architect → component-implementer → test-runner
for CostTracker edge case and API test handling
```

**Main Terminal (after all complete):**
```bash
Use implementation-validator to certify Epic 1 achieves 95% success rate with comprehensive integration testing and generate completion report
```

---

## 📋 EXECUTABLE: Intelligent Autonomy Command

Let agents completely self-organize:

```bash
Epic 1 has 14 test failures preventing 95% success rate achievement.

Component failures:
- AdaptiveRouter: 3 tests (model selection mismatches)
- Epic1AnswerGenerator: 7 tests (missing cost tracking, backward compatibility, budget enforcement, performance tracking)
- Infrastructure: 2 tests (datetime edge case, API test)

Have the agents autonomously:
1. Analyze each component's failures in parallel
2. Design appropriate solutions using architect/specs agents
3. Implement fixes with TDD approach
4. Validate each component achieves full success
5. Perform integration testing
6. Certify 95% target achieved

Agents should self-organize, hand off tasks intelligently, and work in parallel where possible. Epic1AnswerGenerator is the critical path with most failures.
```

---

## 📚 REFERENCE: Detailed Agent Workflows

### Workflow Architecture

```yaml
Epic1_Resolution:
  parallel_streams:
    - stream: AdaptiveRouter
      agents: [root-cause-analyzer, software-architect, component-implementer, test-runner]
      priority: HIGH
      duration: 3.5 hours
      
    - stream: Epic1AnswerGenerator  
      agents: [root-cause-analyzer, specs-implementer, test-driven-developer, component-implementer, test-runner]
      priority: CRITICAL
      duration: 4 hours
      
    - stream: Infrastructure
      agents: [root-cause-analyzer, software-architect, component-implementer, test-runner]
      priority: MEDIUM
      duration: 2.5 hours
      
  integration:
    agents: [implementation-validator, performance-profiler, documentation-specialist]
    duration: 1 hour
    
  total_duration: 4-5 hours (parallel)
```

---

## 📊 Success Metrics & Tracking

### Real-Time Progress Indicators

```python
# Agents will report progress like this:
[root-cause-analyzer]: Investigating AdaptiveRouter failures... 3 root causes identified
[specs-implementer]: Creating Epic1AnswerGenerator specifications... 7 features specified
[component-implementer]: Implementing fixes... 5/7 features complete
[test-runner]: Validating... AdaptiveRouter: 3/3 ✓, Epic1: 5/7 ⚠️
[implementation-validator]: Final validation... 78/82 tests passing (95.1%) ✓
```

### Component Success Matrix

| Component | Start | Current | Target | Status |
|-----------|-------|---------|--------|--------|
| AdaptiveRouter | 7/10 | → | 10/10 | 🔄 In Progress |
| Epic1AnswerGenerator | 2/9 | → | 9/9 | 🔄 In Progress |
| Infrastructure | 10/12 | → | 12/12 | 🔄 In Progress |
| **Total** | **68/82** | **→** | **78/82** | **🎯 95% Target** |

---

## 📋 EXECUTABLE: Quick Validation Command

After fixes complete:

```bash
Run comprehensive Epic 1 validation:
1. pytest tests/epic1/ --tb=short
2. Verify 78+ tests passing (95%+ success rate)
3. Check no regression in domain integration tests
4. Generate Epic 1 completion certificate
```

---

## 🎯 How to Use This Document

### As a Reference:
1. **Study** the orchestration matrix to understand agent collaboration
2. **Review** workflows to see how agents hand off tasks
3. **Learn** the parallel execution strategy for efficiency

### As Executable Prompts:
1. **Find** sections marked "📋 EXECUTABLE"
2. **Copy** the entire command block
3. **Paste** into Claude Code
4. **Watch** agents execute the strategy

### Best Practice:
1. **Read** the strategy first (5 minutes)
2. **Choose** your execution approach (master command or parallel)
3. **Execute** with confidence knowing the full plan
4. **Monitor** agent progress reports

---

## 🏁 Start Commands Summary

### Fastest (One Command):
Copy the "Master Orchestration Command" section

### Most Control (Parallel):
Copy the three terminal commands from "Parallel Execution Commands"

### Most Intelligent (Autonomous):
Copy the "Intelligent Autonomy Command"

### Most Understanding (Workflow):
Copy individual workflow commands as needed

Your agent ecosystem is ready to execute this comprehensive strategy!