# Retriever Sub-Component Specifications

> Extracted from source code analysis (2026-02-09). These contracts define observable
> behavior — every assertion here is testable against the actual implementation.

## Fusion Strategies

All fusion strategies implement `FusionStrategy` (ABC) from `src/components/retrievers/fusion/base.py`.

### Base Interface

```
fuse_results(dense_results: List[Tuple[int, float]],
             sparse_results: List[Tuple[int, float]]) → List[Tuple[int, float]]
```

- **Pre:** Each input is a list of `(document_index, score)` tuples. Input order determines rank position (RRF uses enumeration order as rank). No sort enforcement by base class.
- **Post:** Returns `(document_index, fused_score)` tuples sorted descending by fused_score.
- **Invariant:** No duplicate document_index values in output.

Also provides `fuse()` compatibility method that accepts `RetrievalResult` objects.

---

### SPEC-F1: RRFFusion

**Source:** `src/components/retrievers/fusion/rrf_fusion.py`

| Property | Contract |
|----------|----------|
| Algorithm | `score = Σ weight_i / (k + rank_i)` where rank_i is 1-based |
| Config keys | `k` (int, default 60), `weights.dense` (float, default 0.7), `weights.sparse` (float, default 0.3) |
| Score range | Raw RRF: ~0.001–0.05 for typical k=60 (never normalized to [0,1]) |
| Weight normalization | Weights auto-normalized to sum=1.0 on init |
| Empty input: both empty | Returns `[]` |
| Empty input: one empty | Returns copy of non-empty list |
| Score ignores originals | RRF uses only rank position, original scores are discarded |
| Ordering | Descending by fused score |
| Validation | `ValueError` if k ≤ 0 or weights outside [0,1] |

---

### SPEC-F2: ScoreAwareFusion

**Source:** `src/components/retrievers/fusion/score_aware_fusion.py`

| Property | Contract |
|----------|----------|
| Algorithm | `final = α·avg_score + β·rank_boost + γ·overlap_bonus` |
| Config keys | `score_weight` (α, default 0.6), `rank_weight` (β, default 0.3), `overlap_weight` (γ, default 0.1), `normalize_scores` (bool, default True), `k` (int, default 60) |
| Score range | When normalize=True: scores in roughly [0, 1] range (overlap_bonus contributes up to γ) |
| Weight normalization | α+β+γ auto-normalized to sum=1.0 |
| Empty input | Same behavior as RRF: `[]` or copy of non-empty |
| Normalization | Min-max to [0,1] per retriever; identical scores returned as-is |
| Negative score handling | If dense≥0 and sparse<0, uses dense only (not average) |
| Overlap bonus | 1.0 if document appears in both dense and sparse results, else 0.0 |
| Ordering | Descending by final score |
| Validation | `ValueError` if any weight outside [0,1] or k ≤ 0 |

**Rank boost detail:** Each retriever contributes `0.5 / (k + rank)` to rank_boost. The 0.5 is hardcoded, not configurable.

**Key difference from RRF:** Preserves original semantic scores rather than discarding them.

---

### SPEC-F3: GraphEnhancedRRFFusion

**Source:** `src/components/retrievers/fusion/graph_enhanced_fusion.py`

| Property | Contract |
|----------|----------|
| Algorithm | Step 1: base RRF → Step 2: entity + relationship boosts |
| Config keys | `base_fusion` (RRF config), `graph_enhancement.enabled` (bool), `graph_enhancement.graph_weight` (default 0.1), `graph_enhancement.entity_boost` (default 0.15), `graph_enhancement.relationship_boost` (default 0.1) |
| Additional config | `graph_enhancement.similarity_threshold` (default 0.7), `graph_enhancement.max_graph_hops` (default 3) |
| Score range | 0.0–1.0 (capped via `min(score, 1.0)`) |
| Score rescaling | When base RRF range < 0.01, normalizes to [0.1, 1.0] to improve discrimination |
| Requires setup | `set_documents_and_query(documents, query)` must be called before `fuse_results()` for boosts to apply; otherwise entity/relationship boosts are all 0.0 |
| Entity extraction | Uses spaCy `en_core_web_sm` if available, falls back to regex keyword matching |
| Fallback on error | Any exception in graph enhancement → returns base RRF results |
| Fallback on disabled | `graph_enhancement.enabled=False` → pure RRF |
| Ordering | Descending by enhanced score |
| Dependencies | numpy (required), spacy (optional) |

**Enhancement scaling:** Graph boosts are scaled proportionally to base score range (max 50% of base range), preventing boosts from dominating small RRF scores.

---

## Rerankers

All rerankers implement `Reranker` (ABC) from `src/components/retrievers/rerankers/base.py`.

### Base Interface

```
rerank(query: str, documents: List[Document],
       initial_scores: List[float]) → List[Tuple[int, float]]
```

- **Pre:** `documents` and `initial_scores` have same length.
- **Post:** Returns `(original_index, reranked_score)` tuples sorted descending by score.
- **Invariant:** Convention: All reranker implementations fall back to identity on any error. This is not enforced by the ABC but is a consistent implementation pattern.

---

### SPEC-R1: IdentityReranker

**Source:** `src/components/retrievers/rerankers/identity_reranker.py`

| Property | Contract |
|----------|----------|
| Behavior | Pass-through: returns `[(i, score) for i, score in enumerate(initial_scores)]` |
| Model | None |
| Fallback | N/A (is itself the fallback) |
| Score threshold | None |
| Lazy loading | N/A |
| Disabled behavior | Returns `[]` when disabled |

---

### SPEC-R2: SemanticReranker

**Source:** `src/components/retrievers/rerankers/semantic_reranker.py`

| Property | Contract |
|----------|----------|
| Model | `cross-encoder/ms-marco-MiniLM-L-6-v2` (default) |
| Config keys | `model`, `enabled` (bool), `batch_size` (default 32), `top_k` (default 10), `score_threshold` (default 0.0), `device` (default "auto") |
| Lazy loading | Yes — model loaded on first `rerank()` call |
| Score threshold | Drops results with score < threshold (not just reorders) |
| Pre-filtering | Only reranks first min(len(docs), top_k) documents; remaining docs retain initial_scores and are appended |
| Disabled behavior | Returns identity [(i, score)] when disabled (unlike IdentityReranker which returns []) |
| Document truncation | Truncates documents to 2000 characters + appends '...' (up to 2003 chars total) |
| Fallback on error | Returns original ranking (identity behavior) |
| Fallback on import | Gracefully handles missing `sentence-transformers` |
| Score range | Cross-encoder scores (roughly -10 to +10, not normalized to [0,1]) |

---

### SPEC-R3: NeuralReranker

**Source:** `src/components/retrievers/rerankers/neural_reranker.py`

| Property | Contract |
|----------|----------|
| Model | Configurable, default `cross-encoder/ms-marco-MiniLM-L6-v2` |
| Config keys | `enabled`, `initialize_immediately` (bool, default True), `models` (dict), `adaptive` (dict), `score_fusion` (dict), `max_candidates` (default 50) |
| Lazy loading | Yes when `initialize_immediately=False` |
| Pre-filtering | `max_candidates` limits docs before reranking |
| Score fusion | Configurable method with weights and normalization |
| Fallback on error | Returns initial scores (identity behavior) |
| Self-disable on init failure | Gracefully degrades to identity mode permanently on init failure |
| `is_enabled()` | Returns `config.enabled`, not `_initialized` |
| Cache | Result caching for repeated queries |
| Dependencies | numpy (required), utils module (CrossEncoderModels, ModelConfig, AdaptiveStrategies, ScoreFusion, PerformanceOptimizer) |
