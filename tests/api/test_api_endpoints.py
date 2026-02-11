"""Tests for the FastAPI RAG API wrapper."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.core.interfaces import Answer, Document


@pytest.fixture
def mock_orchestrator():
    orch = MagicMock()
    orch.get_system_health.return_value = {
        "status": "healthy",
        "components": {"embedder": "ok", "retriever": "ok"},
    }
    orch.process_query.return_value = Answer(
        text="RISC-V is an open ISA.",
        sources=[Document(content="RISC-V spec chapter 1", title="RISC-V Spec")],
        confidence=0.92,
        metadata={"retrieved_docs": 1},
    )
    return orch


@pytest.fixture
def client(mock_orchestrator):
    """Create test client with mocked orchestrator."""
    import src.api.app as api_module

    api_module._orchestrator = mock_orchestrator
    with TestClient(api_module.app) as c:
        yield c
    api_module._orchestrator = None


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

    def test_health_503_when_not_initialized(self):
        import src.api.app as api_module

        api_module._orchestrator = None
        with TestClient(api_module.app) as c:
            resp = c.get("/health")
            assert resp.status_code == 503


class TestQueryEndpoint:
    def test_query_returns_answer(self, client):
        resp = client.post("/query", json={"query": "What is RISC-V?"})
        assert resp.status_code == 200
        data = resp.json()
        assert "RISC-V" in data["answer"]
        assert data["confidence"] > 0.5
        assert len(data["sources"]) == 1

    def test_query_empty_rejected(self, client):
        resp = client.post("/query", json={"query": ""})
        assert resp.status_code == 422

    def test_query_with_custom_k(self, client, mock_orchestrator):
        resp = client.post("/query", json={"query": "test", "k": 10})
        assert resp.status_code == 200
        mock_orchestrator.process_query.assert_called_with("test", k=10)
