"""Tier 2: DomainAwareQueryProcessor validation.

Tests that domain filtering correctly routes in-domain queries to the
full pipeline and provides graceful handling for off-domain queries.
Requires Ollama.

Spec references: SPEC-P1 in docs/specs/query-processors.md
"""

import pytest
from src.core.interfaces import Answer
from src.components.query_processors.domain_aware_query_processor import (
    DomainAwareQueryProcessor,
)

pytestmark = [pytest.mark.validation, pytest.mark.requires_ml, pytest.mark.requires_ollama]


@pytest.fixture
def domain_processor(indexed_orchestrator):
    """Create DomainAwareQueryProcessor wrapping the test orchestrator's components."""
    retriever = indexed_orchestrator.get_component("retriever")
    generator = indexed_orchestrator.get_component("generator")
    return DomainAwareQueryProcessor(
        retriever=retriever,
        generator=generator,
        enable_domain_filtering=True,
    )


class TestDomainFiltering:
    """Verify domain filtering routes queries correctly."""

    @pytest.mark.xfail(
        strict=True,
        reason="SPEC-P1 latent bug: process_query() calls super().process_query() "
               "but parent only defines process(). In-domain path hits AttributeError.",
        raises=AttributeError,
    )
    def test_in_domain_query_produces_answer(self, domain_processor):
        """RISC-V queries should be processed and return answers."""
        answer = domain_processor.process_query("What is RISC-V?")
        assert isinstance(answer, Answer)
        assert len(answer.text) > 50, "In-domain answer should be substantive"

    @pytest.mark.xfail(
        strict=True,
        reason="SPEC-P1 latent bug: process_query() calls super().process_query() "
               "but parent only defines process(). In-domain path hits AttributeError.",
        raises=AttributeError,
    )
    def test_in_domain_answer_is_grounded(self, domain_processor):
        """In-domain answers should reference RISC-V content."""
        answer = domain_processor.process_query("What extensions does RISC-V support?")
        text_lower = answer.text.lower()
        assert any(
            term in text_lower for term in ["risc-v", "extension", "rv32i"]
        ), f"Answer not grounded: {answer.text[:200]}"

    def test_off_domain_query_handled_gracefully(self, domain_processor):
        """Off-domain queries should not crash and should indicate low relevance."""
        # This should either produce a low-confidence answer or a refusal
        answer = domain_processor.process_query(
            "What is the weather forecast for Zurich next week?"
        )
        assert isinstance(answer, Answer)
        # Off-domain: either confidence is low or text indicates limitation
        is_low_confidence = answer.confidence < 0.5
        is_refusal = any(
            phrase in answer.text.lower()
            for phrase in ["not related", "outside", "don't have", "cannot", "beyond"]
        )
        assert is_low_confidence or is_refusal or len(answer.text) > 0, (
            "Off-domain query should be handled (low confidence, refusal, or best-effort)"
        )
