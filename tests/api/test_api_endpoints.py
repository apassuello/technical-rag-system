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
        sources=[Document(content="RISC-V spec chapter 1", metadata={"title": "RISC-V Spec"})],
        confidence=0.92,
        metadata={"retrieved_docs": 1},
    )
    return orch


@pytest.fixture
def client(mock_orchestrator):
    """Create test client with mocked PlatformOrchestrator."""
    with patch("src.api.app.PlatformOrchestrator", return_value=mock_orchestrator):
        from src.api.app import app
        with TestClient(app) as c:
            yield c


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "components" in data

    def test_health_includes_component_info(self, client):
        resp = client.get("/health")
        data = resp.json()
        assert data["components"]["embedder"] == "ok"
        assert data["components"]["retriever"] == "ok"


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

    def test_query_returns_source_metadata(self, client):
        resp = client.post("/query", json={"query": "test"})
        data = resp.json()
        assert len(data["sources"]) == 1
        assert data["sources"][0]["title"] == "RISC-V Spec"
        assert "RISC-V spec" in data["sources"][0]["content"]
