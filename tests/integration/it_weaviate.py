"""Docker-based integration tests for WeaviateBackend.

Exercises the real weaviate-client v4 against a local Docker container.
Requires: docker compose up -d  (Weaviate on localhost:8180, gRPC on 50051).
"""

import numpy as np
import pytest

from src.components.retrievers.backends.weaviate_backend import WeaviateBackend
from src.components.retrievers.backends.weaviate_config import (
    WeaviateBackendConfig,
    WeaviateConnectionConfig,
    WeaviateSchemaConfig,
)
from src.core.interfaces import Document

pytestmark = [
    pytest.mark.integration,
    pytest.mark.requires_weaviate,
]

EMBEDDING_DIM = 384
TEST_COLLECTION = "IntegrationTest"


def _random_embedding():
    """Return a normalised random 384-d float32 vector as a Python list."""
    vec = np.random.default_rng(42).standard_normal(EMBEDDING_DIM).astype(np.float32)
    vec /= np.linalg.norm(vec)
    return vec.tolist()


def _make_documents(n: int) -> list[Document]:
    """Create n Documents with distinct random embeddings."""
    rng = np.random.default_rng(123)
    docs = []
    for i in range(n):
        vec = rng.standard_normal(EMBEDDING_DIM).astype(np.float32)
        vec /= np.linalg.norm(vec)
        docs.append(
            Document(
                content=f"Integration test document number {i}.",
                metadata={"source": f"test_{i}.txt", "chunk_index": i, "page": 1},
                embedding=vec.tolist(),
            )
        )
    return docs


@pytest.fixture(scope="module")
def backend():
    """Create a WeaviateBackend connected to the Docker container.

    Uses a dedicated collection name so tests don't collide with
    other data. Tears down the collection after the module finishes.
    """
    config = WeaviateBackendConfig(
        connection=WeaviateConnectionConfig(
            url="http://localhost:8180",
            grpc_port=50051,
            timeout=30,
        ),
        schema=WeaviateSchemaConfig(class_name=TEST_COLLECTION),
        auto_create_schema=True,
        max_retries=2,
        retry_delay_seconds=1.0,
    )
    be = WeaviateBackend(config)
    yield be
    # Cleanup: drop the test collection, then close connection
    try:
        be.client.collections.delete(TEST_COLLECTION)
    except Exception:
        pass
    be.close()


# ── Connection & health ────────────────────────────────────────────


class TestConnection:
    """Verify connectivity and health reporting."""

    def test_connected_and_ready(self, backend: WeaviateBackend):
        assert backend.is_connected is True
        assert backend.client.is_ready()

    def test_health_check_healthy(self, backend: WeaviateBackend):
        health = backend.health_check()
        assert health["backend_type"] == "weaviate"
        assert health["is_connected"] is True
        assert health["schema_created"] is True

    def test_schema_created(self, backend: WeaviateBackend):
        assert backend.schema_created is True
        assert backend.is_trained() is True


# ── CRUD operations ────────────────────────────────────────────────


class TestCRUD:
    """Add documents, count them, search, then clear."""

    def test_add_documents(self, backend: WeaviateBackend):
        docs = _make_documents(5)
        backend.add_documents(docs)
        count = backend.get_document_count()
        assert count == 5

    def test_search_returns_results(self, backend: WeaviateBackend):
        query_vec = np.array(_random_embedding(), dtype=np.float32)
        results = backend.search(query_vec, k=3)
        assert isinstance(results, list)
        assert len(results) <= 3
        # Each result is (doc_index, score)
        for idx, score in results:
            assert isinstance(idx, int)
            assert isinstance(score, float)

    def test_hybrid_search(self, backend: WeaviateBackend):
        """Hybrid search mixes vector similarity with keyword matching."""
        query_vec = np.array(_random_embedding(), dtype=np.float32)
        results = backend.search(query_vec, k=3, query_text="integration test document")
        assert isinstance(results, list)
        assert len(results) <= 3

    def test_document_count_after_add(self, backend: WeaviateBackend):
        count = backend.get_document_count()
        assert count >= 5


# ── Lifecycle ──────────────────────────────────────────────────────


class TestLifecycle:
    """Clear, recreate, and inspect backend info."""

    def test_clear_resets_count(self, backend: WeaviateBackend):
        backend.clear()
        assert backend.get_document_count() == 0
        assert backend.schema_created is True  # clear recreates schema

    def test_add_after_clear(self, backend: WeaviateBackend):
        docs = _make_documents(2)
        backend.add_documents(docs)
        assert backend.get_document_count() == 2

    def test_backend_info(self, backend: WeaviateBackend):
        info = backend.get_backend_info()
        assert isinstance(info, dict)
        assert info["backend_type"] == "weaviate"
        assert info["is_connected"] is True
        assert info["schema_created"] is True
        assert "document_count" in info
        assert "stats" in info
        assert "weaviate_meta" in info
