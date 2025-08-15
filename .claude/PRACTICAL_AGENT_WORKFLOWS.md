# Practical Agent Workflows - Live Examples

This file contains practical examples you can use RIGHT NOW to see your agents in action. Copy and paste these into Claude Code to watch the magic happen!

## 🎯 Example 1: Building a New RAG Component

### Scenario: Add a Document Deduplication Feature

```bash
# Just type this in Claude Code:
"I need to add a document deduplication feature to prevent duplicate documents in our vector store. It should use content hashing to identify duplicates."
```

**What will happen automatically:**

1. **documentation-validator** checks if deduplication specs exist
2. **software-architect** designs the deduplication approach  
3. **rag-specialist** suggests optimal hashing strategies
4. **test-driven-developer** writes comprehensive tests:
   - Test exact duplicates are caught
   - Test near-duplicates handling
   - Test performance with large document sets
5. **component-implementer** guides you to implement
6. **test-runner** validates implementation
7. **performance-profiler** measures impact
8. **code-reviewer** reviews the code
9. **documentation-specialist** updates docs

## 🎯 Example 2: Fixing a Performance Issue

### Scenario: Slow Document Processing

```bash
# Type this:
"Users are reporting that processing large PDFs (>100 pages) is taking over 30 seconds. This is too slow for our requirements."
```

**What will happen automatically:**

1. **performance-profiler** immediately profiles current performance
2. **root-cause-analyzer** investigates the bottleneck
3. **system-optimizer** suggests optimization strategies
4. **test-driven-developer** writes performance benchmarks
5. **component-implementer** implements optimizations
6. **test-runner** ensures no regression
7. **performance-profiler** validates improvements
8. **documentation-specialist** documents the optimization

## 🎯 Example 3: Security Vulnerability

### Scenario: Potential Prompt Injection

```bash
# Type this:
"We need to add protection against prompt injection attacks in our query processor"
```

**What will happen automatically:**

1. **security-auditor** analyzes current vulnerabilities
2. **test-driven-developer** writes security tests
3. **rag-specialist** suggests RAG-specific protections
4. **component-implementer** implements security measures
5. **test-runner** validates security tests pass
6. **security-auditor** re-audits the solution
7. **documentation-validator** ensures security docs updated

## 🎯 Example 4: Complete Feature Development

### Scenario: Implement Hybrid Search

```bash
# Type this:
"Implement hybrid search combining dense semantic search with sparse keyword search for better retrieval accuracy"
```

**Watch the full orchestration:**

```
Your Request
    ↓
documentation-validator: "Checking for hybrid search specifications..."
    ↓
software-architect: "Designing hybrid search architecture with fusion strategy..."
    ↓
rag-specialist: "Recommending BM25 + dense embeddings with reciprocal rank fusion..."
    ↓
test-driven-developer: "Writing tests for hybrid search:
  - test_dense_search_alone()
  - test_sparse_search_alone()  
  - test_hybrid_fusion()
  - test_ranking_preservation()
  - test_performance_targets()"
    ↓
[You implement the feature]
    ↓
test-runner: "Running tests... All 5 tests passing ✅"
    ↓
performance-profiler: "Profiling hybrid search:
  - Latency: 12ms (p50), 28ms (p99) ✅
  - Throughput: 1,200 QPS ✅"
    ↓
code-reviewer: "Code quality review:
  - Architecture: ✅ Clean separation
  - Performance: ✅ Efficient fusion
  - Testing: ✅ 92% coverage"
    ↓
implementation-validator: "APPROVED for deployment"
```

## 🎯 Example 5: Bug Investigation

### Scenario: Mysterious Retrieval Failures

```bash
# Type this:
"Some queries are returning completely irrelevant documents, but only for queries about 'RISC-V interrupts'. Other queries work fine."
```

**Intelligent investigation flow:**

```
Your Bug Report
    ↓
test-driven-developer: "Creating test to reproduce issue..."
    ↓
root-cause-analyzer: "INVESTIGATING:
  - Analyzing query processing for 'RISC-V interrupts'
  - Checking tokenization... Found issue!
  - Hyphen causing tokenizer to split incorrectly"
    ↓
documentation-validator: "Checking if hyphen handling is specified...
  - Specification gap found"
    ↓
software-architect: "Designing tokenization fix:
  - Add special token handling for technical terms"
    ↓
component-implementer: "Implementing fix with special token rules"
    ↓
test-runner: "Bug fixed, all tests passing ✅"
```

## 🎯 Example 6: Production Deployment Prep

### Scenario: Prepare for Production

```bash
# Type this:
"Prepare the RAG system for production deployment next week"
```

**Complete production preparation:**

```
Your Request
    ↓
implementation-validator: "Starting production readiness assessment..."
    ↓
security-auditor: "Scanning for vulnerabilities...
  - Input validation: ✅
  - Rate limiting: ⚠️ Needs implementation
  - Authentication: ✅"
    ↓
performance-profiler: "Profiling production performance...
  - Load testing at 1000 QPS
  - Memory usage stable at 3.2GB
  - CPU usage 65% average"
    ↓
test-runner: "Running full test suite...
  - Unit tests: 156/156 passing
  - Integration tests: 42/42 passing
  - E2E tests: 18/18 passing"
    ↓
documentation-specialist: "Updating production docs...
  - Deployment guide created
  - Configuration documented
  - Troubleshooting guide added"
    ↓
code-reviewer: "Final code review...
  - No critical issues
  - 2 minor suggestions"
    ↓
implementation-validator: "Production Readiness: APPROVED ✅"
```

## 🎯 Example 7: Research & Implementation

### Scenario: Explore New Technique

```bash
# Type this:
"Research and implement CRAG (Corrective RAG) to improve our retrieval accuracy"
```

**Research to implementation flow:**

```
Your Request
    ↓
rag-specialist: "Analyzing CRAG architecture:
  - Retrieval correction mechanism
  - Confidence scoring needed
  - Web search fallback option"
    ↓
software-architect: "Designing CRAG integration:
  - Minimal changes to existing pipeline
  - Add confidence scorer component
  - Implement correction strategy"
    ↓
test-driven-developer: "Creating CRAG tests:
  - test_low_confidence_correction()
  - test_high_confidence_passthrough()
  - test_fallback_mechanism()"
    ↓
[Implementation happens]
    ↓
performance-profiler: "CRAG impact analysis:
  - Accuracy improved by 15%
  - Latency increased by 20ms
  - Acceptable trade-off"
```

## 🔥 Quick Test Commands

### Test 1: Basic Agent Activation
```bash
"Create a simple function to calculate cosine similarity between two vectors"
# Watch test-driven-developer write tests first!
```

### Test 2: Performance Check
```bash
"Check the performance of our current embedding generation"
# Watch performance-profiler analyze your system!
```

### Test 3: Security Audit
```bash
"Review our API endpoints for security vulnerabilities"
# Watch security-auditor scan your code!
```

### Test 4: Documentation Update
```bash
"Update the README with our latest features"
# Watch documentation-specialist create comprehensive docs!
```

## 💡 Pro Tips for Using Your Agents

### 1. Let Them Lead
Don't specify which agent to use - just describe the problem and let them self-organize.

### 2. Trust the Process
If an agent says "tests must be written first", don't fight it. The system is enforcing quality.

### 3. Provide Context
The more context you give, the better the agents perform:
```bash
# Good:
"The document chunker is breaking on PDFs with embedded tables, causing data loss"

# Better:
"The document chunker is breaking on PDFs with embedded tables, specifically losing table headers and cell relationships. This happens with financial reports that have complex nested tables."
```

### 4. Use Natural Language
Talk to your agents like you would to a dev team:
```bash
"We need better error messages when retrieval fails"
"Can we make the embedding generation faster?"
"Something's wrong with the search - it's not finding obvious matches"
```

### 5. Review Agent Reports
Each agent provides detailed reports. Read them! They contain valuable insights:
- Performance bottlenecks
- Security vulnerabilities  
- Code quality issues
- Architecture recommendations

## 🚀 Advanced Workflows

### Multi-Phase Development
```bash
"Phase 1: Design a caching system for embeddings
Phase 2: Implement with Redis
Phase 3: Add cache warming strategies
Phase 4: Monitor cache hit rates"
```

### Parallel Development
```bash
"While I'm working on the frontend, can you:
1. Optimize the retrieval performance
2. Add better error handling to the API
3. Update the documentation"
```

### Investigative Debugging
```bash
"Something is causing memory leaks in production. It seems to happen after processing large batches of documents. Can you investigate?"
```

## 📊 Monitoring Your Agents

### See What They're Doing
Your agents will clearly indicate when they're active:
```
[test-driven-developer]: Writing test for deduplication...
[component-implementer]: Implementing to satisfy tests...
[test-runner]: AUTOMATIC - Validating implementation...
[performance-profiler]: Measuring performance impact...
```

### Track Their Recommendations
Agents provide actionable recommendations:
```
[system-optimizer]: "Implement batching: Expected 3x speedup"
[security-auditor]: "Add rate limiting: Critical for production"
[rag-specialist]: "Use HNSW index: 10x faster retrieval"
```

## 🎪 Your Agent Ecosystem in Action

```
         Your Natural Language Request
                      ↓
    ┌────────────────────────────────────┐
    │      Agents Self-Organize          │
    └────────────────────────────────────┘
                      ↓
    ┌────────────────────────────────────┐
    │        Plan & Validate Specs       │
    │  (documentation-validator, architect)│
    └────────────────────────────────────┘
                      ↓
    ┌────────────────────────────────────┐
    │         Write Tests First          │
    │     (test-driven-developer)        │
    └────────────────────────────────────┘
                      ↓
    ┌────────────────────────────────────┐
    │      You Implement Solution        │
    │  (guided by component-implementer)  │
    └────────────────────────────────────┘
                      ↓
    ┌────────────────────────────────────┐
    │    Automatic Quality Assurance     │
    │  (test-runner, code-reviewer)      │
    └────────────────────────────────────┘
                      ↓
    ┌────────────────────────────────────┐
    │     Performance & Security         │
    │ (performance-profiler, security)   │
    └────────────────────────────────────┘
                      ↓
    ┌────────────────────────────────────┐
    │      Documentation Updated         │
    │   (documentation-specialist)       │
    └────────────────────────────────────┘
                      ↓
            Production Ready! 🚀
```

## Start Building Now!

Pick any example above and paste it into Claude Code. Watch your agent team spring into action, collaborating to deliver high-quality, well-tested, documented, and optimized code.

Remember: **You just describe what you want. Your agents handle the rest!**