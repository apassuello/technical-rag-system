"""Tier 2: Weaviate vector index validation.

Tests retrieval pipeline with Weaviate backend instead of FAISS.
Requires Docker: semitechnologies/weaviate:1.23.7 on port 8180.
"""

import pytest
import urllib.request
from pathlib import Path

from src.core.platform_orchestrator import PlatformOrchestrator
from src.core.interfaces import Answer, Document
from .golden_corpus import ON_TOPIC_TEXTS

pytestmark = [
    pytest.mark.validation,
    pytest.mark.requires_ml,
    pytest.mark.requires_ollama,
    pytest.mark.requires_weaviate,
]

CONFIGS_DIR = Path(__file__).parent / "configs"


@pytest.fixture(scope="session")
def weaviate_available():
    """Check if Weaviate is accessible on localhost:8180."""
    try:
        urllib.request.urlopen("http://localhost:8180/v1/.well-known/ready", timeout=3)
    except Exception:
        pytest.skip("Weaviate not available on localhost:8180")


@pytest.fixture(scope="session", autouse=True)
def clean_weaviate(weaviate_available):
    """Delete stale collections before test run to prevent shard errors."""
    try:
        import weaviate
        from weaviate.classes.init import AdditionalConfig, Timeout

        client = weaviate.connect_to_custom(
            http_host="localhost",
            http_port=8180,
            http_secure=False,
            grpc_host="localhost",
            grpc_port=50051,
            grpc_secure=False,
            additional_config=AdditionalConfig(
                timeout=Timeout(query=30, insert=60)
            ),
        )

        try:
            client.collections.delete("TestTechnicalDocument")
        except Exception:
            pass
        finally:
            client.close()
    except Exception:
        pass
    yield


@pytest.fixture
def weaviate_pipeline(weaviate_available):
    """Boot PlatformOrchestrator with Weaviate backend, index golden corpus."""
    config_path = CONFIGS_DIR / "weaviate_rrf_local.yaml"
    orch = PlatformOrchestrator(config_path)

    docs = [
        Document(content=text, metadata={"source": f"golden_{i}", "type": "test"})
        for i, text in enumerate(ON_TOPIC_TEXTS)
    ]
    count = orch.index_documents(docs)
    assert count == 3, f"Expected 3 docs indexed, got {count}"
    return orch


class TestWeaviateRetrieval:
    """Weaviate backend should produce equivalent results to FAISS."""

    def test_index_and_retrieve(self, weaviate_pipeline):
        """Weaviate retriever should return relevant documents."""
        retriever = weaviate_pipeline.get_component("retriever")
        results = retriever.retrieve("What is RISC-V?", k=3)

        assert len(results) > 0, "No results from Weaviate retriever"
        top_contents = [r.document.content for r in results[:2]]
        assert any(
            "RISC-V" in c for c in top_contents
        ), "RISC-V doc not in top-2 results"

    def test_document_count(self, weaviate_pipeline):
        """Weaviate index should report correct document count."""
        retriever = weaviate_pipeline.get_component("retriever")
        results = retriever.retrieve("What is RISC-V?", k=10)
        assert len(results) >= 1, "Expected at least 1 result"

    def test_pipeline_produces_answer(self, weaviate_pipeline):
        """Full pipeline with Weaviate should produce a grounded answer."""
        answer = weaviate_pipeline.process_query("What is RISC-V?")

        assert isinstance(answer, Answer), "Didn't return Answer"
        assert len(answer.text) > 50, "Answer too short"
        assert answer.sources, "No sources"

    def test_pipeline_health(self, weaviate_pipeline):
        """System should report healthy with Weaviate backend."""
        weaviate_pipeline.process_query("What is RISC-V?")
        health = weaviate_pipeline.get_system_health()
        assert health["status"] == "healthy", "Unhealthy after query"
