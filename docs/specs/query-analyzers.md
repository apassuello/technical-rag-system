# Query Analyzer Specifications

> Extracted from source code analysis (2026-02-09). Contracts define observable behavior.

## Base Interface

QueryAnalyzer ABC from `src/components/query_processors/base.py`

From `src/components/query_processors/analyzers/base_analyzer.py`:

```
analyze(query: str) → QueryAnalysis
```

QueryAnalysis fields:
- `query`: str — the input query
- `complexity_score`: float in [0.0, 1.0] (individual analyzer scoring methods clamp internally)
- `complexity_level`: "simple" | "medium" | "complex"
- `confidence`: float in [0.0, 1.0]
- `technical_terms`: List[str]
- `entities`: List[str]
- `intent_category`: str
- `suggested_k`: int
- `metadata`: Dict[str, Any]

Base class behavior:
- **Pre:** Empty/invalid query raises `ValueError`
- **Post:** `_analyze_query()` result wrapped with performance metrics
- **Error:** `RuntimeError` wrapping on analysis failure
- Performance tracking on both success and failure
- Epic 2 feature analysis: BaseQueryAnalyzer includes Epic 2 feature analysis methods (_analyze_epic2_features, _calculate_neural_reranking_benefit, etc.) inherited by all subclasses

## SPEC-A1: RuleBasedAnalyzer

Source: `src/components/query_processors/analyzers/rule_based_analyzer.py`

| Property | Contract |
|----------|----------|
| Dependencies | None |
| Confidence base | 0.7 (not fixed — adjusted up to 1.0 based on: +0.15 for non-general intent, +0.10 for technical terms, +0.05 for entities) |
| Scoring method | Regex pattern scoring against technical terms, question complexity markers |
| Complexity clamping | Scores clamped to [0.0, 1.0] |
| Thresholds | RuleBasedAnalyzer does NOT set complexity_level from score. It always returns complexity_level='medium' (the QueryAnalysis default). The computed complexity_score is accurate but not mapped to a level. |
| Fallback on error | NONE. _analyze_query() has no try/except. Errors propagate to BaseQueryAnalyzer.analyze() as RuntimeError. |
| Exception behavior | CAN raise RuntimeError via BaseQueryAnalyzer.analyze() if _analyze_query() fails |

ComponentFactory type: `"rule_based"`

## SPEC-A2: NLPAnalyzer

Source: `src/components/query_processors/analyzers/nlp_analyzer.py`

| Property | Contract |
|----------|----------|
| Dependencies | spacy (optional) |
| Confidence base | 0.5 |
| Scoring method | NLP features (POS tags, entity counts, dependency depth) + keyword fallback |
| Without spaCy | Falls back to keyword-only analysis (still functional) |
| Complexity clamping | Scores clamped to [0.0, 1.0] |
| Fallback on error | NONE. _analyze_query() has no try/except. Errors propagate to BaseQueryAnalyzer.analyze() as RuntimeError. |
| Exception behavior | CAN raise RuntimeError via BaseQueryAnalyzer.analyze() if _analyze_query() fails |
| Epic 2 features | Includes _analyze_epic2_features() producing neural reranking benefit, graph enhancement benefit, and hybrid weight optimization data in metadata |

ComponentFactory type: `"nlp"`

## SPEC-A3: Epic1QueryAnalyzer

Source: `src/components/query_processors/analyzers/epic1_query_analyzer.py`

| Property | Contract |
|----------|----------|
| Dependencies | None (pure Python sub-components) |
| Sub-components | FeatureExtractor, ComplexityClassifier, ModelRecommender |
| Analysis phases | 1) Feature extraction → 2) Complexity classification → 3) Model recommendation |
| Confidence | From classifier output |
| Complexity clamping | Scores clamped to [0.0, 1.0] |
| Thresholds | ComplexityClassifier.DEFAULT_THRESHOLDS: simple < 0.15, medium 0.15-0.32, complex >= 0.32. NOTE: The 0.35/0.70 thresholds are used in Epic1MLAnalyzer's ViewResult system, NOT here. |
| Suggested k | simple=3, medium=5, complex=7 |
| Metadata | `metadata['epic1_analysis']` with: `recommended_model`, `cost_estimate`, routing info |
| Cost estimates | Complex queries have higher cost estimates than simple ones |
| Fallback on error | Returns confidence=0.3, medium complexity |
| Exception behavior | Mostly safe — _analyze_query() catches all exceptions and calls _build_fallback_analysis(). However, if _build_fallback_analysis itself fails, RuntimeError could propagate from BaseQueryAnalyzer. |
| Overhead target | < 50ms total analysis time |

ComponentFactory type: `"epic1"`

## SPEC-A4: Epic1MLAnalyzer

Source: `src/components/query_processors/analyzers/epic1_ml_analyzer.py`

| Property | Contract |
|----------|----------|
| Dependencies | torch, joblib, numpy are HARD module-level imports (NOT optional — ImportError if not installed). Trained models from models/epic1/ are optional (graceful fallback to algorithmic). |
| Config keys | `memory_budget_gb` (default 2.0), `enable_performance_monitoring` (default True), `view_weights` (dict), `parallel_execution` (default True), `fallback_strategy` ("algorithmic"\|"conservative"), `confidence_threshold` (default 0.6) |
| Initialization | Lightweight — skips heavy ML infrastructure, lazy loads models |
| With models | Uses trained PyTorch models, 5-view stacking architecture with MetaClassifier fusion |
| Without models | Falls back to algorithmic analysis (still functional) |
| Async API | `analyze_async(query, mode)` with modes: 'ml', 'hybrid', 'algorithmic' |
| Complexity clamping | Scores in [0.0, 1.0] |
| Complexity levels | SIMPLE, MEDIUM, COMPLEX |
| Fallback on error | Returns confidence=0.3, graceful degradation |
| Exception behavior | Has comprehensive fallback chain BUT: file contains duplicate _analyze_query() definitions (second overwrites first). Second definition's fallback uses complexity_level='moderate' which is invalid (should be 'medium'). |
| shutdown() | Cleanup method for model resources |
| Module export | Epic1MLAnalyzer is NOT exported from __init__.py. Must be imported directly from epic1_ml_analyzer module. |

ComponentFactory type: `"epic1_ml"`

## Cross-Analyzer Invariants

- Individual analyzer scoring methods clamp internally (e.g. min(1.0, max(0.0, score))). The QueryAnalysis dataclass does NOT enforce clamping — a caller could construct QueryAnalysis with out-of-range scores.
- RuleBasedAnalyzer and NLPAnalyzer do NOT catch exceptions in _analyze_query(). Errors propagate to BaseQueryAnalyzer.analyze() which wraps them in RuntimeError and re-raises. Only Epic1QueryAnalyzer and Epic1MLAnalyzer have internal try/except with fallback returns.
- RuleBasedAnalyzer, NLPAnalyzer, and Epic1QueryAnalyzer are deterministic for the same input. Epic1MLAnalyzer is NOT deterministic — includes timestamps, performance timing, and analysis count side effects.
- Simple queries should produce lower complexity_score than complex queries (ordering property)
- Most return valid `complexity_level` in {"simple", "medium", "complex"}. Exceptions: RuleBasedAnalyzer never explicitly sets complexity_level (always returns default 'medium'). Epic1MLAnalyzer's second _analyze_query() fallback uses 'moderate' which is NOT a valid level.
