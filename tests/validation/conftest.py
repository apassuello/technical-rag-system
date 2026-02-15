"""Pytest configuration for validation tests."""

import pytest
from pathlib import Path

from src.core.interfaces import Document
from src.components.embedders.modular_embedder import ModularEmbedder
from src.components.retrievers.modular_unified_retriever import ModularUnifiedRetriever
from .golden_corpus import ALL_CORPUS_TEXTS


@pytest.fixture(scope="session")
def golden_documents():
    """4 Document objects: 3 on-topic RISC-V + 1 off-topic weather."""
    return [
        Document(content=text, metadata={"source": f"golden_{i}", "type": "test"})
        for i, text in enumerate(ALL_CORPUS_TEXTS)
    ]


@pytest.fixture(scope="session")
def indexed_orchestrator(orchestrator, golden_documents):
    """Orchestrator with golden corpus indexed — shared across all tests.

    Clears any previously-indexed documents first so that validation tests
    always see exactly 4 golden docs, regardless of integration-test ordering.
    """
    retriever = orchestrator.get_component("retriever")
    if hasattr(retriever, "clear_index"):
        retriever.clear_index()
    count = orchestrator.index_documents(golden_documents)
    assert count == 4, f"Expected 4 docs indexed, got {count}"
    return orchestrator


@pytest.fixture(scope="module")
def shared_embedder():
    """Shared embedder instance — expensive to create, reuse across tests."""
    config = {
        "model": {
            "type": "sentence_transformer",
            "config": {
                "model_name": "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
                "device": "auto",
                "normalize_embeddings": True,
            },
        },
        "batch_processor": {"type": "dynamic", "config": {"initial_batch_size": 64}},
        "cache": {"type": "memory", "config": {"max_entries": 1000}},
    }
    return ModularEmbedder(config)


@pytest.fixture
def make_retriever(shared_embedder):
    """Factory fixture: create a retriever with custom fusion/reranker config.

    Usage:
        retriever = make_retriever(fusion_type="score_aware", reranker_type="neural")
    """
    def _make(
        fusion_type: str = "rrf",
        fusion_config: dict = None,
        reranker_type: str = "identity",
        reranker_config: dict = None,
    ) -> ModularUnifiedRetriever:
        config = {
            "vector_index": {
                "type": "faiss",
                "config": {"index_type": "IndexFlatIP", "normalize_embeddings": True},
            },
            "sparse": {
                "type": "bm25",
                "config": {"k1": 1.2, "b": 0.75, "lowercase": True, "filter_stop_words": True},
            },
            "fusion": {"type": fusion_type, "config": fusion_config or {}},
            "reranker": {"type": reranker_type, "config": reranker_config or {"enabled": True}},
        }
        return ModularUnifiedRetriever(config, shared_embedder)

    return _make


@pytest.fixture
def index_golden_corpus(golden_documents):
    """Index golden corpus into a retriever, returning the retriever."""
    def _index(retriever: ModularUnifiedRetriever) -> ModularUnifiedRetriever:
        retriever.index_documents(golden_documents)
        return retriever

    return _index
