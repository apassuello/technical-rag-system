# Epic 5 Agent & Tools Framework — Audit & Integration

> Session: 2026-02-10
> Branch: test/integration-cleanup-validation

## Goal

Bring the Epic 5 agent-based RAG framework from "factory-registered but never instantiated" to operational integration with the PlatformOrchestrator.

## Architecture

Epic 5 adds tool-calling, query decomposition, and intelligent routing (agent vs RAG) on top of the existing retrieval pipeline. The framework is 7,723 LOC across 21 source files, with 35 test files (~6,000 LOC). Everything was factory-registered but no config, orchestrator path, or service ever created it.

## Plan (from audit)

| # | Task | Priority | Est. Effort |
|---|------|----------|-------------|
| 1 | Run Epic 5 tests, triage failures | P0 | 30 min |
| 2 | Fix LangChain compatibility issues | P0 | 1-2 hrs |
| 3 | Create config/epic5_agents.yaml | P1 | 30 min |
| 4 | Add orchestrator path for "intelligent" processor | P1 | 2-4 hrs |
| 5 | Write agent E2E integration tests | P1 | 1-2 hrs |
| 6 | Verify no regressions | P2 | 30 min |

## What was done

### Task 1: Epic 5 test triage

Initial run: **110 failed, 418 passed, 23 skipped** (551 total).

Root causes identified:
- LangChain 1.x removed `create_react_agent` and `AgentExecutor` from `langchain.agents`
- `ToolParameterType.FLOAT` doesn't exist (correct name: `NUMBER`)
- Dual-import antipattern: modules loaded as both `src.components...` and `components...`
- Test mocks using outdated APIs (dicts instead of `RetrievalResult`, wrong parameter names)

### Task 2: LangChain compatibility — 4 production bugs fixed

**`src/components/query_processors/agents/langchain_adapter.py`**
- `ToolParameterType.FLOAT` → `ToolParameterType.NUMBER` (line 247)

**`src/components/query_processors/agents/react_agent.py`** (4 fixes)
1. Import chain: added `langchain_classic` as fallback for `create_react_agent` / `AgentExecutor`
2. `ToolCall` constructor: added missing `id=f"call_{i}"` field
3. `WorkingMemory` truthiness: changed `or` to `is not None` check (empty WorkingMemory has len=0)
4. Stats tracking: inner except handler now increments `_total_queries` and `_total_execution_time`

**`src/components/generators/llm_adapters/openai_adapter.py`**
- Changed `tool_call.id` to `tool_call['id']` (dict access, not object attribute)

**`tests/epic5/phase2/unit/conftest.py`** (new file)
- Patches `create_react_agent` and `AgentExecutor` at the correct `components.` module path
- Provides `mock_executor` and `mock_executor_class` fixtures
- Eliminates dual-import patching issues across all Phase 2 unit tests

### Task 3: Config file

**`config/epic5_agents.yaml`** — follows `query_processor: { type: "intelligent", config: {...} }` pattern matching existing configs (basic.yaml, default.yaml). Contains:
- Agent config (react type, LLM provider/model, executor settings, prompt config)
- Tool list (calculator, code_analyzer, document_search)
- Memory config (conversation + working)
- Processor config (complexity_threshold: 0.7, routing logic)
- Planning config (disabled by default)

### Task 4: Orchestrator wiring

**`src/core/platform_orchestrator.py`** — 2 new methods:

`_initialize_intelligent_processor(qp_config_dict)`:
1. Reads agent/tools/memory/processor config from dict
2. Creates AgentConfig and LLM via `_create_agent_llm()`
3. Creates tools via `ComponentFactory.create_tool()` for each configured tool
4. Injects retriever into DocumentSearchTool via `set_retriever()`
5. Creates ConversationMemory and WorkingMemory via `ComponentFactory.create_memory()`
6. Assembles ReActAgent with all dependencies
7. Creates QueryAnalyzer (heuristic, no LLM needed)
8. Builds ProcessorConfig from config dict
9. Passes everything to `ComponentFactory.create_query_processor('intelligent', ...)`

`_create_agent_llm(agent_config)`:
- Creates ChatOpenAI or ChatAnthropic based on provider config
- Raises RuntimeError if provider library not installed

### Task 5: Integration tests

**`tests/epic5/phase2/integration/test_orchestrator_agent_wiring.py`** — 7 tests, all passing:
1. `test_initialize_intelligent_processor_creates_correct_type`
2. `test_tools_created_from_config`
3. `test_document_search_gets_retriever_injected`
4. `test_processor_config_from_yaml`
5. `test_rag_path_with_mocked_components`
6. `test_openai_provider`
7. `test_unsupported_provider_raises`

### Task 6: Regression verification

Integration + validation suite: **131 passed, 4 skipped, 4 xfailed, 0 failed** — identical to pre-session baseline.

### Additional test fixes (via background agents)

66 Epic 5 test failures fixed across Phase 1 and Phase 2:
- Phase 2 planning unit tests: complexity thresholds, decomposer assertions
- Phase 2 integration tests: routing logic, exception handling
- Phase 1 unit tests: anthropic adapter config, calculator syntax, code analyzer, document search, openai functions
- Phase 1 scenarios: calculator, code analysis, document search (partial)
- `test_react_agent.py`: refactored 25 @patch decorators to use conftest fixtures (31/31 passing)

## Results

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Epic 5 passed | 418 | 491 | +73 |
| Epic 5 failed | 110 | 44 | -66 |
| Epic 5 skipped | 23 | 23 | 0 |
| Regression (int+val) | 131/0/4/4 | 131/0/4/4 | no change |

## Remaining 44 failures (all test-side, not production bugs)

| Category | Count | Root cause |
|----------|-------|------------|
| E2E scenarios | 17 | Incorrect `Answer` constructor in mocks |
| Performance benchmarks | 8 | Same `Answer` API + timing mocks |
| Document search scenarios | 8 | Need `RetrievalResult` objects instead of dicts |
| Error handling scenarios | 6 | Mock setup mismatches |
| Anthropic adapter | 2 | Mock exception class inheritance |
| Tool registry integration | 2 | Document search needs `RetrievalResult` |
| Calculator scenario | 1 | OpenAI adapter mock format |

## Integration status (updated)

| Dimension | Before | After |
|-----------|--------|-------|
| Code completeness | 10/10 | 10/10 |
| Error handling | 9/10 | 9/10 |
| Test health | ?/10 | **7/10** (491/558 = 88% pass rate) |
| Integration | 2/10 | **7/10** (config + orchestrator + factory all wired) |
