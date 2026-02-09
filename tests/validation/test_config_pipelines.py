"""Tier 1: Config-driven pipeline validation.

Tests that different YAML configs boot a working PlatformOrchestrator
and produce correct results end-to-end. Requires Ollama.

Spec references: all specs — validates full component wiring.
"""

import pytest
from pathlib import Path
from src.core.platform_orchestrator import PlatformOrchestrator
from src.core.interfaces import Answer, Document
from .golden_corpus import GOLDEN_RETRIEVAL_CASES, ALL_CORPUS_TEXTS, ON_TOPIC_TEXTS

pytestmark = [pytest.mark.validation, pytest.mark.requires_ml, pytest.mark.requires_ollama]

CONFIGS_DIR = Path(__file__).parent / "configs"

PIPELINE_CONFIGS = [
    pytest.param("basic_local.yaml", id="basic-adaptive-modular"),
    pytest.param("epic2_score_aware_local.yaml", id="epic2-score-aware-neural"),
    pytest.param("epic2_graph_enhanced_local.yaml", id="epic2-graph-semantic"),
]


@pytest.fixture(params=PIPELINE_CONFIGS)
def pipeline(request):
    """Boot PlatformOrchestrator from a test config, index golden corpus."""
    config_path = CONFIGS_DIR / request.param
    orch = PlatformOrchestrator(config_path)

    docs = [
        Document(content=text, metadata={"source": f"golden_{i}", "type": "test"})
        for i, text in enumerate(ON_TOPIC_TEXTS)
    ]
    count = orch.index_documents(docs)
    assert count == 3, f"Expected 3 docs indexed, got {count}"
    return orch, request.param


class TestConfigPipelineEndToEnd:
    """Each config should boot and produce a correct answer."""

    def test_pipeline_produces_answer(self, pipeline):
        """Config-driven pipeline should produce a non-empty Answer."""
        orch, config_name = pipeline
        answer = orch.process_query("What is RISC-V?")

        assert isinstance(answer, Answer), f"{config_name}: didn't return Answer"
        assert len(answer.text) > 50, f"{config_name}: answer too short"
        assert answer.sources, f"{config_name}: no sources"

    def test_pipeline_answer_grounded(self, pipeline):
        """Answer should contain terms from the indexed content."""
        orch, config_name = pipeline
        answer = orch.process_query("What is RISC-V?")

        text_lower = answer.text.lower()
        grounding_terms = ["risc-v", "instruction set", "open standard", "berkeley"]
        matched = [t for t in grounding_terms if t in text_lower]
        assert matched, f"{config_name}: answer not grounded in context"

    def test_pipeline_retrieval_quality(self, pipeline):
        """Retriever within the pipeline should rank correctly."""
        orch, config_name = pipeline
        retriever = orch.get_component("retriever")
        results = retriever.retrieve("What extensions does RISC-V support?", k=3)

        assert len(results) > 0
        # The extensions doc should be in top-2 at minimum
        top_contents = [r.document.content for r in results[:2]]
        assert any(
            "RV32I" in c or "vector extension" in c for c in top_contents
        ), f"{config_name}: extensions doc not in top-2"

    def test_pipeline_health(self, pipeline):
        """System should report healthy after query."""
        orch, config_name = pipeline
        orch.process_query("What is RISC-V?")
        health = orch.get_system_health()
        assert health["status"] == "healthy", f"{config_name}: unhealthy after query"
