# Claude Code Agent Quick Reference

## Agent Ecosystem for RAG Portfolio Development

### 🎯 Core Philosophy
Your agents work as an autonomous development team where:
- **Tests are written BEFORE code** (enforced by test-driven-developer)
- **Problems are analyzed BEFORE fixes** (root-cause-analyzer)
- **Documentation is the source of truth** (documentation-validator)
- **Quality gates are automatic** (test-runner, implementation-validator)

## 🤖 Your Agent Team

### Development Flow Agents
| Agent | Trigger | Purpose |
|-------|---------|---------|
| **test-driven-developer** | Before ANY implementation | Writes tests first |
| **component-implementer** | After tests are written | Implements to pass tests |
| **test-runner** | AUTOMATIC after changes | Validates all modifications |

### Problem Solving Agents
| Agent | Trigger | Purpose |
|-------|---------|---------|
| **root-cause-analyzer** | AUTOMATIC on serious issues | Investigates before fixing |
| **software-architect** | On design issues | Makes architectural decisions |
| **system-optimizer** | On performance issues | Profiles and optimizes |

### Quality Assurance Agents
| Agent | Trigger | Purpose |
|-------|---------|---------|
| **documentation-validator** | On spec questions | Source of truth for behavior |
| **implementation-validator** | Before deployment | Final quality gatekeeper |

## 🔄 Automatic Workflows

### Feature Development
```
"I need to add hybrid search to the retriever"
```
**What happens automatically:**
1. documentation-validator checks specs
2. test-driven-developer writes tests
3. You implement the feature
4. test-runner validates automatically
5. system-optimizer checks performance

### Bug Fixing
```
"The document chunker is breaking on PDFs with tables"
```
**What happens automatically:**
1. test-driven-developer reproduces with test
2. root-cause-analyzer investigates
3. You implement the fix
4. test-runner validates automatically

### Performance Issues
```
"Embedding generation is too slow"
```
**What happens automatically:**
1. system-optimizer profiles the code
2. root-cause-analyzer finds bottlenecks
3. You implement optimizations
4. test-runner validates no regression

## 💡 Key Commands

### Let Agents Work Naturally
```bash
# Just describe what you want to do
"Implement a new reranking component for better retrieval accuracy"

# Agents will automatically:
# - Check documentation
# - Write tests first
# - Guide implementation
# - Validate results
```

### Explicit Agent Invocation (when needed)
```bash
# Only if you need a specific agent
"Use the root-cause-analyzer to investigate why tests are failing"
"Use the system-optimizer to profile the embedding generation"
```

## 🚦 Quality Gates

### Automatic Validation Points
1. **After Implementation** → test-runner runs automatically
2. **On Test Failures** → root-cause-analyzer investigates
3. **Before Deployment** → implementation-validator checks everything

### What Gets Blocked Automatically
- ❌ Implementation without tests
- ❌ Fixes without root cause analysis  
- ❌ Deployment without validation
- ❌ Changes that break tests
- ❌ Performance regressions

## 📋 Agent Capabilities

### test-driven-developer
- Writes comprehensive test suites
- Creates performance benchmarks
- Reproduces bugs with tests
- Defines acceptance criteria

### component-implementer
- Implements to satisfy tests
- Follows architectural patterns
- Handles error cases properly
- Triggers validation automatically

### test-runner
- Runs after EVERY change
- Reports coverage metrics
- Detects regressions
- Triggers root cause analysis for failures

### root-cause-analyzer
- Investigates before fixing
- Identifies architectural issues
- Determines proper fixes
- Prevents band-aid solutions

### software-architect
- Designs system architecture
- Makes pattern decisions
- Handles scaling strategies
- Reviews architectural compliance

### system-optimizer
- Profiles performance
- Identifies bottlenecks
- Suggests optimizations
- Validates improvements

### documentation-validator
- Verifies spec compliance
- Arbitrates correct behavior
- Identifies documentation gaps
- Ensures alignment

### implementation-validator
- Final quality check
- Deployment readiness
- Security validation
- Complete assessment

## 🎨 Visual Workflow

```
Your Request
     ↓
[Agents Analyze & Plan]
     ↓
Tests Written First
     ↓
You Implement
     ↓
[Automatic Validation]
     ↓
[Automatic Optimization]
     ↓
Ready for Production
```

## 🔥 Pro Tips

### 1. Trust the Process
Let agents trigger naturally - they know when they're needed

### 2. Always Start with Tests
The test-driven-developer will activate automatically for new features

### 3. Don't Fight the Agents
If an agent blocks something, there's a good reason

### 4. Use Documentation as Truth
When in doubt, documentation-validator has the answer

### 5. Let Agents Collaborate
They hand off to each other automatically

## 🚀 Example Workflows

### Adding a New RAG Component
```bash
"I need to add a graph-based retriever to improve document relationships"

# Automatic flow:
# 1. documentation-validator checks specs
# 2. software-architect designs integration
# 3. test-driven-developer writes tests
# 4. You implement
# 5. test-runner validates
# 6. system-optimizer checks performance
```

### Fixing a Production Issue
```bash
"Users report that queries about RISC-V interrupts return irrelevant results"

# Automatic flow:
# 1. test-driven-developer reproduces issue
# 2. root-cause-analyzer investigates
# 3. documentation-validator verifies correct behavior
# 4. You implement fix
# 5. test-runner validates
```

### Optimizing Performance
```bash
"Document processing is taking too long for large PDFs"

# Automatic flow:
# 1. system-optimizer profiles
# 2. root-cause-analyzer identifies bottlenecks
# 3. test-driven-developer writes benchmarks
# 4. You optimize
# 5. test-runner ensures no regression
```

## 📊 Success Metrics

Your agents will help you achieve:
- ✅ 80%+ test coverage automatically
- ✅ Zero implementation without tests
- ✅ All bugs analyzed before fixing
- ✅ Performance targets met
- ✅ Documentation always current
- ✅ Production-ready code

## 🆘 Troubleshooting

### "Agent didn't trigger automatically"
- Check if agent has "PROACTIVELY" in description
- Ensure you're describing the task clearly
- Try explicit invocation if needed

### "Agents seem to conflict"
- Let them resolve naturally
- documentation-validator is the arbiter
- Check AGENT_WORKFLOW_DOCUMENTATION.md

### "Too many agents triggering"
- This is normal for complex tasks
- Each agent has a specific role
- They'll hand off efficiently

## 📝 Remember

**Your agents are a team, not tools. They:**
- Know when to activate
- Hand off to each other
- Enforce quality automatically
- Prevent common mistakes
- Make you more productive

**Just describe what you want to build, and let the team work!**