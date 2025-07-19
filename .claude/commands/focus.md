# Minimal Context Loading

**Usage**: `/focus [area]`  
**Examples**:
- `/focus migration` - Focus on HuggingFace API migration work
- `/focus epic2` - Focus on Epic 2 neural reranking features
- `/focus testing` - Focus on test development and validation
- `/focus architecture` - Focus on system design and boundaries

Load only essential context for specific work area to preserve conversation space and prevent compaction.

## Instructions

**v2.0 Minimal Loading**: Load <500 tokens of precisely relevant context to enable productive work without triggering conversation compaction.

### Core Workflow

1. **Parse focus area parameter**
   - Valid areas: migration, epic2, neural-reranker, testing, architecture, performance
   - Default to current task from current_plan.md if no area specified

2. **Read current task from state**
   - Read .claude/current_plan.md for current_task and specific focus
   - Identify specific component/function being worked on
   - Note any active blockers or next steps

3. **Load MINIMAL context only**
   - Current task description (2-3 lines max)
   - Specific code file and function/class (not entire file)
   - Relevant test case (specific test method)
   - Key configuration snippet if needed
   - NO comprehensive documentation
   - NO architecture files unless specifically needed

4. **Update focus tracking**
   - Update current_focus in .claude/current_plan.md
   - Add timestamp for focus session
   - Note specific work area

5. **Display loaded context with token count**
   - Show exactly what was loaded
   - Display token count to confirm minimal (<500)
   - Provide specific work guidance

## Focus Areas

### `migration` - HuggingFace API Migration
- Focus: LLM adapter, reranker integration, embedder migration
- Files: src/components/generators/answer_generator.py, config/epic2_hf_api.yaml
- Context: Current implementation status, API integration points

### `epic2` - Neural Reranking & Graph Features  
- Focus: Advanced retriever features, neural reranking, analytics
- Files: src/components/retrievers/modular_unified_retriever.py, tests/test_graph_components.py
- Context: Epic 2 features status, performance metrics

### `neural-reranker` - Cross-Encoder Reranking
- Focus: Neural reranking implementation and optimization
- Files: Neural reranker components, cross-encoder integration
- Context: Reranker pipeline, performance benchmarks

### `testing` - Test Development and Validation
- Focus: Test development, diagnostic analysis, validation
- Files: tests/run_comprehensive_tests.py, tests/diagnostic/
- Context: Test coverage, failing tests, validation metrics

### `architecture` - System Design and Boundaries
- Focus: Component interfaces, modular design, boundaries
- Files: src/core/interfaces.py, component specifications
- Context: Architecture compliance, design decisions

### `performance` - Optimization and Benchmarking
- Focus: Performance optimization, resource usage, benchmarks
- Files: Performance analysis scripts, optimization utilities
- Context: Current benchmarks, bottlenecks, optimization opportunities

## Output Format

```
🎯 FOCUSING: [area]

Loading minimal context...
📄 Loaded ([X] tokens):
   1. Current task: "[specific task description]"
   2. [filename] (lines X-Y)
   3. [test_file]::test_method
   4. [config snippet if needed]

📝 Updated: current_plan.md
   - Current focus: "[area]"
   - Focus timestamp: "[ISO timestamp]"

Ready to work on:
- [Specific immediate action]
- [Key detail to remember]
- [Test to satisfy or command to run]

Token usage: [X]/100000 (minimal - no compaction risk)
```

## Examples

### Focus on Migration Work
```
/focus migration

🎯 FOCUSING: migration

Loading minimal context...
📄 Loaded (387 tokens):
   1. Current task: "Implement HuggingFace LLM adapter for answer generation"
   2. src/components/generators/answer_generator.py (lines 45-67)
   3. config/epic2_hf_api.yaml (HF API configuration)
   4. tests/test_hf_api_manual.py::test_ollama_vs_hf_api

📝 Updated: current_plan.md
   - Current focus: "migration"
   - Focus timestamp: "2025-07-19T15:30:00Z"

Ready to work on:
- Implement HuggingFaceAdapter in answer_generator.py
- Replace OllamaAdapter calls with HF API client
- Test with: python test_hf_api_manual.py

Token usage: 387/100000 (minimal - no compaction risk)
```

### Focus on Testing
```
/focus testing

🎯 FOCUSING: testing

Loading minimal context...
📄 Loaded (295 tokens):
   1. Current task: "Add comprehensive test coverage for Epic 2 features"
   2. tests/epic2_validation/ (test suite structure)
   3. tests/run_comprehensive_tests.py::main
   4. Current coverage: 90.2% validation score

📝 Updated: current_plan.md
   - Current focus: "testing"
   - Focus timestamp: "2025-07-19T15:35:00Z"

Ready to work on:
- Run comprehensive tests to identify gaps
- Add missing test cases for neural reranking
- Validate Epic 2 vs basic component differentiation

Token usage: 295/100000 (minimal - no compaction risk)
```

## Critical Rules

1. **Never load more than 500 tokens**
2. **Load specific functions, not entire files**
3. **Include line numbers for precise context**
4. **Always show token count**
5. **Update focus tracking for continuity**

This command enables productive work without triggering conversation compaction by keeping context minimal and focused.