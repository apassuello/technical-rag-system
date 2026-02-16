[![CI](https://github.com/apassuello/technical-rag-system/actions/workflows/ci.yml/badge.svg)](https://github.com/apassuello/technical-rag-system/actions/workflows/ci.yml)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

# Technical Documentation RAG System

Config-driven retrieval-augmented generation with multi-model routing,
hybrid search, and agent-based query processing.

## What This Is

A retrieval-augmented generation system for technical documentation. You write a
YAML config, and `PlatformOrchestrator` assembles a pipeline from five component
slots: document processor, embedder, retriever, answer generator, and query
processor. Each slot has multiple implementations, so the same codebase supports
20+ configurations — from a mock-LLM smoke test to a multi-provider routing
system with neural reranking.

The system is organized into four epics. Epic 1 adds multi-model intelligence
with complexity-based routing across LLM providers. Epic 2 adds hybrid search
(FAISS + BM25), fusion strategies, and neural reranking. Epic 5 adds a ReAct
agent with tool use and working memory. Epic 8 built microservices and Helm
charts, then was archived in favor of the monolith.

This is a portfolio project. It has ~2,700 passing tests at 63% code coverage.
Some components (Weaviate backend, cache service) are partially implemented and
gated behind test markers. The system runs locally without external services — a
mock LLM adapter handles answer generation when Ollama is unavailable.

## Architecture

```
config/*.yaml
     │
     ▼
┌─────────────────────────────────┐
│      PlatformOrchestrator       │
│   (config → component slots)    │
└──┬──────┬──────┬──────┬──────┬──┘
   │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼
┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐
│Proc ││Embed││Retr ││GenAI││Query│
│essor││der  ││iever││     ││Proc │
└─────┘└─────┘└──┬──┘└─────┘└─────┘
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
     vector   sparse   fusion
     index    (BM25)   + rerank
     (FAISS)
```

| Slot | Implementations | Config key |
|------|----------------|------------|
| Document Processor | `hybrid_pdf` | `document_processor` |
| Embedder | `modular` (sentence-transformers) | `embedder` |
| Retriever | `modular_unified` → FAISS + BM25 + fusion + reranker | `retriever` |
| Answer Generator | `adaptive_modular`, `epic1` (multi-model routing) | `answer_generator` |
| Query Processor | `intelligent` (Epic 5 agent-based) | `query_processor` |

**LLM adapters** (under answer generator): `mock`, `ollama`, `openai`, `mistral`,
`anthropic`, `huggingface`, `local`.

The config-driven design means you can A/B compare retrieval strategies, swap LLM
providers, or run the full pipeline with zero external dependencies — all by
changing a YAML file.

## Quick Start

```bash
git clone https://github.com/apassuello/technical-rag-system.git
cd technical-rag-system
./setup.sh
```

Then try it:

```bash
source .venv/bin/activate

python -c "
from src.core.platform_orchestrator import PlatformOrchestrator
orch = PlatformOrchestrator('config/basic.yaml')
print(orch.health_service.get_system_health())
"

# Run unit tests
pytest tests/unit \
  -m 'not requires_ml and not requires_ollama and not requires_postgres and not requires_redis and not integration' \
  --override-ini='addopts=--strict-markers --strict-config --tb=short' -x -q

# Streamlit UI (requires Ollama for real LLM answers)
streamlit run app.py
```

Note: the first `PlatformOrchestrator` call downloads the embedding model (~22MB).

## Feature Epics

### Epic 1: Multi-Model Intelligence

Complexity-based query routing across LLM providers with cost tracking.

- 5-dimensional complexity analysis (vocabulary, structure, domain, reasoning, context)
- 3 routing strategies: `cost_optimized`, `quality_first`, `balanced`
- 8 LLM adapters with fallback chains
- Thread-safe Decimal cost tracking ($0.001 precision)

Key files: `src/components/generators/routing/`, `src/components/generators/llm_adapters/`,
`src/components/generators/epic1_answer_generator.py`
Config: `config/epic1_multi_model.yaml`

### Epic 2: Advanced Retrieval

Hybrid search combining dense and sparse methods with learned fusion.

- FAISS `IndexFlatIP` for dense vector search (384-dim embeddings)
- BM25 for keyword matching with configurable stop words
- 4 fusion strategies: RRF, weighted, graph-enhanced RRF, score-aware
- Neural reranking via cross-encoder models
- Score normalization and calibration

Key files: `src/components/retrievers/`, `src/components/calibration/`
Configs: `config/epic2_graph_enhanced_mock.yaml`, `config/epic2_score_aware_mock.yaml`

### Epic 5: Agent-Based RAG

ReAct agent loop with tool use, working memory, and planning.

- Tool registry with typed parameters
- Working memory for multi-turn context
- ReasoningStep trace (THOUGHT → ACTION → OBSERVATION)
- LangChain integration via `langchain_classic`

Key files: `src/components/query_processors/`
Config: `config/epic5_agents.yaml`, `config/epic5_tools.yaml`

### Epic 8: Cloud-Native (Archived)

Built as 5 microservices with Helm charts and K8s manifests. Archived after
deciding the monolith serves the portfolio better. The code remains in `services/`
as a demonstration of knowing when *not* to distribute.

Key files: `services/api-gateway/`

## Configuration

A trimmed `basic.yaml` showing the structure:

```yaml
document_processor:
  type: "hybrid_pdf"
  config:
    chunk_size: 512

embedder:
  type: "modular"
  config:
    model:
      type: "sentence_transformer"
      config:
        model_name: "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"

retriever:
  type: "modular_unified"
  config:
    vector_index: { type: "faiss" }
    sparse:       { type: "bm25" }
    fusion:       { type: "rrf" }
    reranker:     { type: "identity" }

answer_generator:
  type: "adaptive_modular"
  config:
    llm_client: { type: "mock" }  # no API keys needed
```

Representative configs:

| Config | LLM | Retrieval | Use case |
|--------|-----|-----------|----------|
| `basic.yaml` | mock | FAISS + BM25 + RRF | Testing, CI |
| `test.yaml` | mock | FAISS + BM25 | Integration tests |
| `local.yaml` | ollama | FAISS + BM25 + RRF | Local dev |
| `epic1_multi_model.yaml` | multi-provider routing | FAISS + BM25 | Multi-model evaluation |
| `epic2_graph_enhanced_mock.yaml` | mock | FAISS + BM25 + graph RRF + neural reranker | Retrieval experiments |
| `epic2_score_aware_mock.yaml` | mock | FAISS + BM25 + score-aware fusion | Score calibration |

## Testing

```bash
# Fast unit tests (~30s, no ML deps)
pytest tests/unit \
  -m "not requires_ml and not requires_ollama and not requires_postgres and not requires_redis and not integration" \
  --override-ini="addopts=--strict-markers --strict-config --tb=short" -x -q

# Full suite with coverage
pytest tests/unit tests/integration tests/validation \
  -m "not requires_ml and not requires_ollama" -v --tb=short \
  --cov=src --cov-report=term-missing --cov-fail-under=70
```

Current baseline: ~2,700 passing, ~229 known failures (isolated behind markers).
Coverage: 63% overall.

Test file naming: `ut_` (unit), `it_` (integration), `vt_` (validation).

Markers: `requires_ml`, `requires_ollama`, `requires_weaviate`, `requires_spacy`,
`requires_postgres`, `requires_redis`. Tests auto-skip when services are
unavailable — no manual configuration needed.

## Project Structure

```
src/
├── core/                  # PlatformOrchestrator, ComponentFactory, interfaces
├── components/
│   ├── processors/        # Document chunking and PDF handling
│   ├── embedders/         # Sentence-transformer embeddings
│   ├── retrievers/        # FAISS, BM25, fusion, reranking
│   ├── generators/        # LLM adapters, routing, prompt building
│   ├── query_processors/  # Agent-based query processing (Epic 5)
│   └── calibration/       # Score normalization (Epic 2)
├── training/              # Model training infrastructure
└── evaluation/            # Retrieval quality metrics
config/                    # YAML pipeline configurations
tests/
├── unit/                  # ut_*.py — fast, mocked
├── integration/           # it_*.py — real components
└── validation/            # vt_*.py — quality assertions
services/                  # Archived microservices (Epic 8)
```

## Requirements

- Python 3.11+
- ~2 GB disk (dependencies + embedding model)
- 4 GB RAM minimum
- No GPU required (CPU inference works fine)

Optional:
- [Ollama](https://ollama.ai) for local LLM inference
- Docker for containerized deployment

## License

MIT. Arthur Passuello.
