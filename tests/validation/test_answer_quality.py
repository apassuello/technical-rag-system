"""Tier 2: Answer quality property validation.

Tests that generated answers exhibit properties of correct answers:
grounded in context, substantive, appropriate confidence. Requires Ollama.
"""

import pytest
from src.core.interfaces import Answer
from .golden_corpus import GOLDEN_RETRIEVAL_CASES

pytestmark = [pytest.mark.validation, pytest.mark.requires_ml, pytest.mark.requires_ollama]


class TestAnswerGrounding:
    """Validate that answers are grounded in retrieved context."""

    @pytest.mark.parametrize(
        "case",
        GOLDEN_RETRIEVAL_CASES,
        ids=[c["query"][:40] for c in GOLDEN_RETRIEVAL_CASES],
    )
    def test_answer_contains_grounding_terms(self, indexed_orchestrator, case):
        """Answer should contain at least one term from the expected source."""
        answer = indexed_orchestrator.process_query(case["query"])

        assert isinstance(answer, Answer)
        text_lower = answer.text.lower()
        matched = [t for t in case["grounding_terms"] if t.lower() in text_lower]
        assert matched, (
            f"Answer for '{case['query']}' contains none of "
            f"{case['grounding_terms']}:\n{answer.text[:200]}"
        )

    @pytest.mark.parametrize(
        "case",
        GOLDEN_RETRIEVAL_CASES,
        ids=[c["query"][:40] for c in GOLDEN_RETRIEVAL_CASES],
    )
    def test_sources_contain_relevant_content(self, indexed_orchestrator, case):
        """At least one source should contain a grounding term."""
        answer = indexed_orchestrator.process_query(case["query"])

        assert answer.sources, "Should have sources"
        source_texts = " ".join(s.content.lower() for s in answer.sources)
        matched = [t for t in case["grounding_terms"] if t.lower() in source_texts]
        assert matched, "Sources should contain query-relevant content"


class TestAnswerProperties:
    """Validate structural properties of generated answers."""

    def test_answer_substantiveness(self, indexed_orchestrator):
        """Answers should be between 50 and 3000 characters."""
        answer = indexed_orchestrator.process_query("What is RISC-V?")
        assert 50 < len(answer.text) < 3000, (
            f"Answer length {len(answer.text)} outside [50, 3000]"
        )

    def test_in_domain_confidence_above_threshold(self, indexed_orchestrator):
        """In-domain queries should produce confidence above 0.1."""
        answer = indexed_orchestrator.process_query("What is RISC-V?")
        assert answer.confidence > 0.1, (
            f"In-domain confidence {answer.confidence} too low"
        )

    def test_different_queries_produce_different_answers(self, indexed_orchestrator):
        """Distinct queries should produce distinct answer text."""
        a1 = indexed_orchestrator.process_query("What is RISC-V?")
        a2 = indexed_orchestrator.process_query("What extensions does RISC-V support?")
        assert a1.text != a2.text, "Different queries produced identical answers"
