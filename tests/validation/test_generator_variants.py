"""Tier 1: Generator variant validation.

Tests that both answer generator types (epic1, adaptive_modular) produce
grounded answers through the full pipeline. Requires Ollama.

Spec references: SPEC-G1, SPEC-G2 in docs/specs/generators.md
"""

import pytest
from src.core.interfaces import Answer
from src.core.component_factory import ComponentFactory
pytestmark = [pytest.mark.validation, pytest.mark.requires_ml, pytest.mark.requires_ollama]


@pytest.fixture
def adaptive_generator():
    """Create the adaptive_modular generator with Ollama backend."""
    return ComponentFactory.create_generator(
        "adaptive_modular",
        config={
            "llm_client": {
                "type": "ollama",
                "config": {"model_name": "llama3.2:3b", "base_url": "http://localhost:11434"},
            },
        },
    )


@pytest.fixture
def epic1_generator():
    """Create the Epic1 multi-model generator with Ollama backend."""
    return ComponentFactory.create_generator(
        "epic1",
        config={
            "llm_client": {
                "type": "ollama",
                "config": {"model_name": "llama3.2:3b", "base_url": "http://localhost:11434"},
            },
            "routing": {
                "enabled": True,
                "strategies": ["cost_optimized"],
            },
            "cost_tracking": {"enabled": True, "daily_budget": 10.0},
        },
    )


class TestAdaptiveModularGenerator:
    """Validate the adaptive_modular generator produces grounded answers."""

    def test_generates_answer(self, adaptive_generator, indexed_orchestrator):
        """adaptive_modular should generate a non-empty Answer."""
        retriever = indexed_orchestrator.get_component("retriever")
        results = retriever.retrieve("What is RISC-V?", k=3)
        context_docs = [r.document for r in results]

        answer = adaptive_generator.generate("What is RISC-V?", context_docs)
        assert isinstance(answer, Answer)
        assert len(answer.text) > 50, f"Answer too short: {len(answer.text)} chars"

    def test_answer_grounded_in_context(self, adaptive_generator, indexed_orchestrator):
        """Answer should reference content from the provided context."""
        retriever = indexed_orchestrator.get_component("retriever")
        results = retriever.retrieve("What is RISC-V?", k=3)
        context_docs = [r.document for r in results]

        answer = adaptive_generator.generate("What is RISC-V?", context_docs)
        text_lower = answer.text.lower()
        assert any(
            term in text_lower
            for term in ["risc-v", "instruction set", "open standard", "berkeley"]
        ), f"Answer not grounded: {answer.text[:200]}"


class TestGeneratorComparison:
    """Both generators should produce valid answers for the same input."""

    def test_both_generators_produce_answers(
        self, adaptive_generator, epic1_generator, indexed_orchestrator
    ):
        """epic1 and adaptive_modular should both generate valid answers."""
        retriever = indexed_orchestrator.get_component("retriever")
        results = retriever.retrieve("What is RISC-V?", k=3)
        context_docs = [r.document for r in results]

        for label, gen in [("adaptive", adaptive_generator), ("epic1", epic1_generator)]:
            answer = gen.generate("What is RISC-V?", context_docs)
            assert isinstance(answer, Answer), f"{label} didn't return Answer"
            assert len(answer.text) > 20, f"{label} answer too short"
            assert answer.confidence >= 0, f"{label} negative confidence"
