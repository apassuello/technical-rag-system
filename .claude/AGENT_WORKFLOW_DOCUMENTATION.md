# Claude Code Agent Ecosystem - Workflow Documentation

## Agent Collaboration Workflow

This document describes how the Claude Code agents work together to create a self-orchestrating development system that mimics a professional development team.

## The Complete Agent Ecosystem

### Core Development Agents
1. **test-driven-developer** - Writes tests before implementation
2. **component-implementer** - Builds code to pass tests
3. **test-runner** - Validates all changes automatically
4. **software-architect** - Makes design decisions
5. **system-optimizer** - Profiles and optimizes performance
6. **root-cause-analyzer** - Investigates serious issues
7. **documentation-validator** - Source of truth for specs
8. **implementation-validator** - Final quality gatekeeper

## Automatic Workflow Triggers

### 1. Feature Development Flow
```
New Feature Request
    ↓
documentation-validator (verify specs exist)
    ↓
software-architect (design solution)
    ↓
test-driven-developer (write failing tests)
    ↓
component-implementer (implement to pass tests)
    ↓
test-runner (AUTOMATIC - validate implementation)
    ↓
system-optimizer (if performance critical)
    ↓
implementation-validator (final approval)
```

### 2. Bug Fix Flow
```
Bug Reported
    ↓
test-driven-developer (reproduce with test)
    ↓
root-cause-analyzer (AUTOMATIC - investigate)
    ↓
documentation-validator (check if behavior is correct)
    ↓
software-architect (if design issue)
    ↓
component-implementer (fix implementation)
    ↓
test-runner (AUTOMATIC - validate fix)
    ↓
implementation-validator (approve for deployment)
```

### 3. Performance Issue Flow
```
Performance Degradation Detected
    ↓
system-optimizer (AUTOMATIC - profile)
    ↓
root-cause-analyzer (if complex issue)
    ↓
software-architect (if architectural change needed)
    ↓
test-driven-developer (write performance tests)
    ↓
component-implementer (implement optimizations)
    ↓
test-runner (AUTOMATIC - verify no regression)
    ↓
system-optimizer (validate improvements)
```

### 4. Serious Error Flow
```
test-runner detects critical failure
    ↓
root-cause-analyzer (AUTOMATIC - investigate)
    ↓
documentation-validator (verify expected behavior)
    ↓
software-architect (if design flaw)
    ↓
test-driven-developer (comprehensive test coverage)
    ↓
component-implementer (implement fix)
    ↓
test-runner (AUTOMATIC - validate)
    ↓
implementation-validator (ensure production ready)
```

## Key Automatic Triggers

### Agents that ALWAYS trigger automatically:

1. **test-runner**
   - Triggers after ANY file modification
   - Triggers after component-implementer completes
   - Triggers after bug fixes

2. **root-cause-analyzer**
   - Triggers when test-runner finds serious failures
   - Triggers on performance degradation
   - Triggers on architectural violations

3. **documentation-validator**
   - Triggers when specs need verification
   - Triggers before major changes
   - Triggers when behavior questions arise

## Agent Communication Patterns

### Information Flow Between Agents

```
┌─────────────────────────────────────────────────────┐
│                 documentation-validator              │
│                   (Source of Truth)                  │
└────────────────────┬───────────────────────────────┘
                     │ Specs & Requirements
     ┌───────────────┼───────────────┬──────────────┐
     ↓               ↓               ↓              ↓
┌──────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────┐
│ architect│ │test-developer│ │implementer│ │validator │
└──────────┘ └──────────────┘ └──────────┘ └──────────┘
     ↓               ↓               ↓              ↓
     └───────────────┼───────────────┴──────────────┘
                     ↓
              ┌─────────────┐
              │ test-runner │ (Automatic Validation)
              └─────────────┘
                     ↓
         ┌──────────────────────┐
         │ root-cause-analyzer  │ (If Issues Found)
         └──────────────────────┘
                     ↓
           ┌──────────────┐
           │ system-optimizer │ (Performance Issues)
           └──────────────┘
```

## Trigger Keywords and Patterns

### Words that Trigger Specific Agents

#### PROACTIVE Triggers (Automatic)
- "MUST BE USED PROACTIVELY" - Agent activates automatically
- "ALWAYS" - Agent runs without being asked
- "Automatically triggered" - Agent self-activates

#### Explicit Invocation
- "Use the [agent-name] agent to..." - Direct invocation
- "Have [agent-name] review..." - Explicit request

## Configuration for Automatic Workflows

### Example: Enforcing Test-First Development

```yaml
# In .claude/settings.json
{
  "workflows": {
    "enforce_tdd": true,
    "auto_test_after_implementation": true,
    "auto_analyze_failures": true,
    "require_spec_validation": true
  },
  "agent_triggers": {
    "on_file_save": ["test-runner"],
    "on_test_failure": ["root-cause-analyzer"],
    "on_implementation": ["test-runner", "system-optimizer"],
    "on_pr_creation": ["implementation-validator"]
  }
}
```

## Best Practices for Agent Collaboration

### 1. Let Agents Hand Off Naturally
Agents know when to involve others based on their findings. Don't manually orchestrate unless necessary.

### 2. Trust the Automatic Triggers
Agents marked with "PROACTIVELY" will activate when appropriate. You don't need to explicitly call them.

### 3. Use Documentation as Truth
The documentation-validator agent is the arbiter when there are questions about correct behavior.

### 4. Follow the Test-First Flow
Always let test-driven-developer write tests before implementation. This ensures quality and specification compliance.

### 5. Don't Skip Validation
The implementation-validator provides final quality assurance. Never deploy without its approval.

## Common Scenarios and Agent Responses

### Scenario 1: "Implement a new document chunking feature"
```
Automatic Flow:
1. documentation-validator checks for specs
2. software-architect designs approach
3. test-driven-developer writes tests
4. component-implementer builds feature
5. test-runner validates (automatic)
6. system-optimizer checks performance
7. implementation-validator approves
```

### Scenario 2: "The retrieval is returning irrelevant results"
```
Automatic Flow:
1. test-driven-developer writes test to reproduce
2. root-cause-analyzer investigates (automatic)
3. documentation-validator verifies expected behavior
4. component-implementer fixes issue
5. test-runner validates (automatic)
```

### Scenario 3: "The system is running slowly"
```
Automatic Flow:
1. system-optimizer profiles (automatic)
2. root-cause-analyzer investigates bottlenecks
3. software-architect reviews if architectural
4. component-implementer optimizes
5. test-runner ensures no regression (automatic)
6. system-optimizer validates improvement
```

## Monitoring Agent Activity

### View Agent Invocations
```bash
# See which agents were called
claude-code --show-agent-history

# See agent handoffs
claude-code --show-agent-flow
```

### Debug Agent Decisions
```bash
# Understand why an agent was triggered
claude-code --debug-agents

# See agent communication
claude-code --verbose
```

## Summary

This agent ecosystem creates a self-healing, self-validating development environment where:
- **Quality is enforced** through automatic testing
- **Problems are investigated** before fixes are attempted  
- **Documentation drives** correct behavior
- **Performance is continuously** monitored
- **Validation happens automatically** at every step

The agents work together like a professional development team, each with specialized expertise, automatically collaborating to produce high-quality, well-tested, performant code.