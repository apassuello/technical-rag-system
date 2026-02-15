# RAG Portfolio Project 1 — Technical Documentation System

## Project
Multi-model RAG system: document processing → embedding → retrieval → generation.
PlatformOrchestrator assembles components from config YAML (config/*.yaml).
Monorepo migration in progress — target repo: technical-rag-system (empty, 0 commits pushed).

**Stack**: Python 3.11, FastAPI, PyTorch, sentence-transformers, FAISS, Pydantic v2, pytest
**Services**: 5 microservices in services/ (api-gateway, query-analyzer, generator, retriever, analytics)
**Epics**: 1 (multi-model), 2 (advanced retrieval), 5 (agents), 8 (cloud-native K8s deployment)

## Build & Test

```bash
# Fast unit tests (no ML deps, no coverage, <30s)
pytest tests/unit \
  -m "not requires_ml and not requires_ollama and not requires_postgres and not requires_redis and not integration" \
  --override-ini="addopts=--strict-markers --strict-config --tb=short" -x -q

# Full validation (unit + integration + validation + coverage)
pytest tests/unit tests/integration tests/validation \
  -m "not requires_ml and not requires_ollama" -v --tb=short \
  --cov=src --cov-report=term-missing --cov-fail-under=70

# Lint + type check
ruff check src/ services/
mypy src/ --ignore-missing-imports
```

## Code Patterns
- ComponentFactory builds components from config dicts (no _load_config method)
- Config YAML → PlatformOrchestrator → component slots (processor, embedder, retriever, generator, query_processor)
- Retriever has sub-slots: vector_index, sparse, fusion, reranker
- LLM adapters: ollama, openai, mistral, anthropic, huggingface, mock
- Tests use pytest markers: unit, component, integration, requires_ml, requires_ollama, etc.

## Anti-Patterns
- NEVER claim "production-ready" or "enterprise-grade" as self-description
- NEVER skip root-cause investigation — no "skip tests" shortcuts
- NEVER mock non-existent methods — verify API exists before writing test
- NEVER use hardcoded paths (/Users/apa/) — use relative paths
- NEVER import from rag_portfolio (stale monorepo reference)

## Git
- Branch: feature/, fix/, test/, chore/ prefixes
- Commit: type(scope): description (conventional commits)
- Only commit src/, tests/, services/ code — exclude .claude/, docs drafts, temp markdown
- Do NOT push unless explicitly asked

## Current State
- Migration: ~35%, target repo empty, 73 stale refs remaining
- Test baseline: ~650 passing, ~229 actual failures (dependency failures isolated with markers)
- Coverage: integration 23.4%, unit 45.3% of src/
- Only test.yaml config path has integration coverage (1 of ~6 meaningful combos)
