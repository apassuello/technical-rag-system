# Generator Specifications

Document contracts for the two answer generator implementations.

## Base Interface: AnswerGenerator

From `src/core/interfaces.py`:
```
generate(query: str, context: List[Document]) -> Answer
```

Answer has: text (str), sources (List[Document]), confidence (float [0,1]), metadata (Dict[str, Any])

## SPEC-G1: AnswerGenerator (adaptive_modular)

Source: `src/components/generators/answer_generator.py`

Exception source: `src/components/generators/base.py` (GenerationError)

| Property | Contract |
|----------|----------|
| API | `generate(query: str, context: List[Document]) -> Answer` |
| Constructor | `__init__(config=None, model_name=None, temperature=None, max_tokens=None, use_ollama=None, ollama_url=None, **kwargs)` |
| Pre: query | Non-empty string (empty raises ValueError directly in generate() method, not via prompt builder) |
| Pre: context | Can be empty list -- generates answer without retrieval context |
| Post: Answer.text | Non-empty string |
| Post: Answer.confidence | Float in [0.0, 1.0] |
| Post: Answer.metadata | Includes `generator_type`, `generation_time` keys |
| Sub-components | prompt_builder (SimplePromptBuilder), llm_client (OllamaAdapter), response_parser (MarkdownParser), confidence_scorer (SemanticScorer) |
| `set_embedder()` | Optional -- enables semantic confidence scoring |
| Error handling | GenerationError wraps ALL exceptions |
| Parser failure | Works when parser returns incomplete data (missing 'answer' key → uses raw_response). Parser exceptions propagate to catch-all and become GenerationError, NOT graceful raw-response fallback. |
| Confidence | Parsed confidence from response overrides scorer if higher |
| Config-driven | Supports both structured dict config and legacy keyword params |

ComponentFactory type: `"adaptive_modular"` or `"answer_generator"`

## SPEC-G2: Epic1AnswerGenerator

Source: `src/components/generators/epic1_answer_generator.py`

| Property | Contract |
|----------|----------|
| API | Same as SPEC-G1: `generate(query, context) -> Answer` |
| Extends | AnswerGenerator -- inherits all base contracts |
| Constructor | Same signature as SPEC-G1 |
| Routing enabled | Via: explicit config['routing']['enabled'] flag, OR EPIC1_AVAILABLE=True, OR config['type'] in ('epic1_multi_model', 'adaptive', 'multi_model'), OR config contains multi-model indicators ('query_analyzer', 'model_mappings', 'strategies', 'cost_tracking') |
| Single-model mode | Falls back to base AnswerGenerator behavior when no routing config |
| Routing strategies | `cost_optimized` (minimize API costs), `quality_first` (best models), `balanced` (tradeoff) |
| Fallback chain | primary model -> fallback list -> hard fallback model |
| Cost tracking | $0.000001 precision (6 decimal places), uses Python Decimal type, daily budget enforcement |
| Budget degradation | When daily budget threshold exceeded, forces cheapest model (Ollama) regardless of routing strategy |
| String-to-Document conversion | Automatically converts string context items to Document objects for backward compatibility |
| Cost on failure | Cost tracking continues even on failures |
| Error handling | Re-raises exceptions (bare raise). Does NOT return an Answer with confidence=0.0. Errors propagate as GenerationError from base class or raw exceptions. |
| Routing metadata | Answer.metadata includes routing decisions, selected model, cost estimate |

ComponentFactory type: `"epic1"` or `"adaptive"`

## Additional Generator Implementation

**Note:** AdaptiveAnswerGenerator (`src/components/generators/adaptive_generator.py`) also implements the AnswerGenerator interface but raises RuntimeError instead of GenerationError and rejects empty context. Not covered by this spec.

## Cross-Generator Invariants

- Both generators accept the same `generate(query, context)` signature
- Both return `Answer` objects with the same interface
- Base AnswerGenerator wraps all exceptions in GenerationError. Epic1AnswerGenerator has bare `raise` that may re-raise raw exceptions (ValueError from empty-query check, or other pre-routing exceptions).
- Both support Ollama as the default LLM backend
- Both add generation_time to metadata
