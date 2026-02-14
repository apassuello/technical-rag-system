"""Tier 1: Config-driven pipeline validation.

Tests that different YAML configs boot a working PlatformOrchestrator
and produce correct results end-to-end.

Two test classes:
- TestConfigPipelineEndToEnd: Full Ollama-backed pipelines (requires_ollama)
- TestCISafePipeline: Every config with mock LLM override (no Ollama needed)

Spec references: all specs — validates full component wiring.
"""

import copy

import pytest
import yaml
from pathlib import Path
from src.core.platform_orchestrator import PlatformOrchestrator
from src.core.interfaces import Answer, Document
from .golden_corpus import GOLDEN_RETRIEVAL_CASES, ALL_CORPUS_TEXTS, ON_TOPIC_TEXTS

pytestmark = [pytest.mark.validation, pytest.mark.requires_ml, pytest.mark.requires_ollama]

CONFIGS_DIR = Path(__file__).parent / "configs"

PIPELINE_CONFIGS = [
    pytest.param("basic_local.yaml", id="rrf-identity"),
    pytest.param("epic2_score_aware_local.yaml", id="score_aware-neural"),
    pytest.param("epic2_graph_enhanced_local.yaml", id="graph_enhanced-semantic"),
    pytest.param("rrf_semantic.yaml", id="rrf-semantic"),
    pytest.param("rrf_neural.yaml", id="rrf-neural"),
    pytest.param("weighted_identity.yaml", id="weighted-identity"),
    pytest.param("weighted_semantic.yaml", id="weighted-semantic"),
    pytest.param("weighted_neural.yaml", id="weighted-neural"),
    pytest.param("score_aware_identity.yaml", id="score_aware-identity"),
    pytest.param("score_aware_semantic.yaml", id="score_aware-semantic"),
    pytest.param("graph_enhanced_identity.yaml", id="graph_enhanced-identity"),
    pytest.param("graph_enhanced_neural.yaml", id="graph_enhanced-neural"),
]


@pytest.fixture(scope="class", params=PIPELINE_CONFIGS)
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


# ---------------------------------------------------------------------------
# CI-safe: every config with mock LLM override (no Ollama, no Weaviate)
# ---------------------------------------------------------------------------

MOCK_LLM_CLIENT = {
    "type": "mock",
    "config": {
        "model_name": "mock-model",
        "response_pattern": "technical",
        "include_citations": True,
    },
}

# Configs that need external services beyond ML (Weaviate, etc.)
_SKIP_CI_CONFIGS = {"weaviate_rrf_local.yaml"}

# Discover all YAML configs, excluding external-service ones
_ALL_YAML = sorted(p.name for p in CONFIGS_DIR.glob("*.yaml") if p.name not in _SKIP_CI_CONFIGS)

CI_SAFE_CONFIGS = [
    pytest.param(name, id=name.removesuffix(".yaml"))
    for name in _ALL_YAML
]


def _mock_config_path(original_path: Path, tmp_path: Path) -> Path:
    """Load a config YAML, override llm_client to mock, write to tmp_path."""
    with open(original_path) as f:
        cfg = yaml.safe_load(f)

    # Override generator's LLM client to mock
    gen = cfg.get("answer_generator", {})
    gen_config = gen.setdefault("config", {})
    gen_config["llm_client"] = copy.deepcopy(MOCK_LLM_CLIENT)

    out = tmp_path / original_path.name
    with open(out, "w") as f:
        yaml.dump(cfg, f)
    return out


@pytest.fixture(scope="class", params=CI_SAFE_CONFIGS)
def ci_pipeline(request, tmp_path_factory):
    """Boot PlatformOrchestrator with mock generator — no Ollama needed.

    Loads each config, overrides llm_client to mock, writes to a temp dir,
    then boots the orchestrator.  query_processor is kept intact so the
    wiring fix in platform_orchestrator is actually exercised.
    """
    tmp_dir = tmp_path_factory.mktemp("ci_pipeline")
    original = CONFIGS_DIR / request.param
    mock_path = _mock_config_path(original, tmp_dir)
    orch = PlatformOrchestrator(mock_path)

    docs = [
        Document(content=text, metadata={"source": f"golden_{i}", "type": "test"})
        for i, text in enumerate(ON_TOPIC_TEXTS)
    ]
    count = orch.index_documents(docs)
    assert count == 3, f"Expected 3 docs indexed, got {count}"
    return orch, request.param


class TestCISafePipeline:
    """Pipeline tests that run without Ollama (mock generator)."""

    pytestmark = [pytest.mark.validation, pytest.mark.requires_ml]

    def test_pipeline_produces_answer(self, ci_pipeline):
        """Mock pipeline should produce a non-empty Answer."""
        orch, config_name = ci_pipeline
        answer = orch.process_query("What is RISC-V?")

        assert isinstance(answer, Answer), f"{config_name}: didn't return Answer"
        assert len(answer.text) > 20, f"{config_name}: answer too short"
        assert answer.sources, f"{config_name}: no sources"

    def test_pipeline_health(self, ci_pipeline):
        """System should report healthy after query."""
        orch, config_name = ci_pipeline
        orch.process_query("What is RISC-V?")
        health = orch.get_system_health()
        assert health["status"] == "healthy", f"{config_name}: unhealthy after query"
