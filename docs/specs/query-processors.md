# Query Processor Specifications

> Extracted from source code analysis (2026-02-09). Contracts define observable behavior.

## Base Interface: QueryProcessor

**Note:** Two distinct QueryProcessor ABCs exist:
- `src/core/interfaces.py` (with ComponentBase) — used by IntelligentQueryProcessor
- `src/components/query_processors/base.py` — used by ModularQueryProcessor

From `src/core/interfaces.py` (line 332) and `src/components/query_processors/base.py` (line 247):

```
process(query: str, options: Optional[QueryOptions] = None) → Answer
```

## Parent: ModularQueryProcessor

Source: `src/components/query_processors/modular_query_processor.py`

| Property | Contract |
|----------|----------|
| API | `process(query, options?) → Answer` |
| Constructor | Dual-convention design: accepts either config-first (`Dict`/`QueryProcessorConfig`) or retriever-first via polymorphic argument naming |
| Pipeline stages | 1) Query analysis → 2) Document retrieval (using suggested_k) → 3) Context selection → 4) Answer generation → 5) Response assembly |
| Post | Returns Answer with sources and metadata |
| Exception behavior | Raises `RuntimeError` when fallback is disabled or both primary and fallback processing fail |
| Attributes (private) | `_retriever`, `_generator`, `_analyzer`, `_selector`, `_assembler` |
| Attributes (public properties) | `query_analyzer`, `context_selector`, `response_assembler`. **No public retriever/generator properties.** |
| Defaults | Uses sensible defaults if optional components omitted |

---

## SPEC-P1: DomainAwareQueryProcessor

Source: `src/components/query_processors/domain_aware_query_processor.py`

| Property | Contract |
|----------|----------|
| Extends | ModularQueryProcessor |
| API (ABC override) | `process(query, options?) → Answer` (inherited from parent) |
| API (custom method) | `process_query(query, options?) → Answer` (defined at line 109, **NOT an ABC override**) |
| **⚠️ WARNING** | Calling `processor.process(query)` bypasses domain filtering entirely — only `process_query()` applies domain filter logic |
| **⚠️ LATENT BUG** | Line 154: calls `super().process_query(query, options)` but parent defines `process`, not `process_query` — may cause AttributeError at runtime |
| Constructor | Same as parent + `enable_domain_filtering: bool = True` |
| Domain filter | DomainRelevanceFilter component, optimized for RISC-V domain |
| Phase 0 | Domain relevance analysis before standard pipeline |
| Low relevance (< 0.3) | Early exit — no retrieval, no generation, returns refusal Answer |
| Medium relevance (0.3–0.7) | **Same code path as high relevance** — calls `super().process_query()`. No differentiated "conservative" processing. |
| High relevance (> 0.7) | **Same code path as medium relevance** — calls `super().process_query()`. No differentiated "full" processing behavior. |
| Early exit Answer | Contains text indicating query is out of domain scope |
| Domain metadata | Added **only when** `enable_domain_filtering=True` **and** `domain_result is not None`. **NOT added** when domain filtering is disabled. |
| Fallback on error | Falls back to parent (standard pipeline) on any domain filter error |
| Exception behavior | Can raise `RuntimeError` — inherits from ModularQueryProcessor which raises when fallback is disabled or both primary and fallback fail |

ComponentFactory type: `"domain_aware"`

---

## SPEC-P2: IntelligentQueryProcessor

Source: `src/components/query_processors/intelligent_query_processor.py`

| Property | Contract |
|----------|----------|
| Implements | QueryProcessor interface from `src/core/interfaces.py` |
| API | `process(query, options?) → Answer` (line 189, consistent with ABC) |
| Constructor | `__init__(retriever, generator, agent: ReActAgent, query_analyzer, config=None)` |
| Routing logic | complexity < threshold (default 0.7) → RAG pipeline; complexity ≥ threshold → Agent |
| agent parameter | **Positionally required** (no default). Passing `agent=None` explicitly is accepted at construction but will fail later during `_process_with_agent` when calling `self._agent.process()` |
| RAG path | Uses retriever + generator (standard pipeline) |
| Agent path | Delegates to ReActAgent for complex reasoning |
| Agent failure | Falls back to RAG pipeline |
| Metadata: source | `'rag_pipeline'`, `'agent'`, or `'error'` (when both RAG and agent fail) |
| Metadata: complexity | Includes `complexity` (score). **routing_decision dict tracked internally in `self._routing_decisions` but NOT embedded in Answer metadata. No 'threshold' key in Answer metadata.** |
| Cost budget | **Only LOGS a warning** when `max_agent_cost` exceeded. **No hard stop** — the answer is still returned. |
| Exception behavior | **Never raises** — all errors wrapped as Answer objects (unlike ModularQueryProcessor) |
| Config keys | `complexity_threshold` (default 0.7), `max_agent_cost` (float) |
| Config keys (dataclass defaults) | `use_agent_by_default` (default True), `enable_planning` (default True), `enable_parallel_execution` (default True) |
| Config keys (dict-parsing overrides) | `use_agent_by_default` overridden to False (line 155), `enable_planning` overridden to False, `enable_parallel_execution` overridden to False. **Effective default depends on how config is provided.** |

ComponentFactory type: `"intelligent"`

---

## Cross-Processor Invariants

- All processors implement `process(query, options?) → Answer` (base ABC method name)
- **Exception behavior varies:**
  - `ModularQueryProcessor.process()` raises `RuntimeError` when fallback is disabled or both primary and fallback fail
  - `DomainAwareQueryProcessor` inherits ModularQueryProcessor's raising behavior
  - `IntelligentQueryProcessor` **truly never raises** — wraps all errors as Answer objects
- All processors add metadata to Answer indicating processing details
- All processors use retriever + generator as core pipeline components
