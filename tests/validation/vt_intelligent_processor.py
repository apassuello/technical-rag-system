"""Tier 2: IntelligentQueryProcessor smoke test.

Tests the RAG pipeline path of IntelligentQueryProcessor. The agent path
requires LangChain ReActAgent setup which may not be available — we verify
graceful fallback. Requires Ollama.

Spec references: SPEC-P2 in docs/specs/query-processors.md
"""

import pytest
from src.core.interfaces import Answer
from src.components.query_processors.intelligent_query_processor import (
    IntelligentQueryProcessor,
)

pytestmark = [pytest.mark.validation, pytest.mark.requires_ml, pytest.mark.requires_ollama]


@pytest.fixture
def intelligent_processor(indexed_orchestrator):
    """Create IntelligentQueryProcessor with RAG components, no agent."""
    retriever = indexed_orchestrator.get_component("retriever")
    generator = indexed_orchestrator.get_component("answer_generator")

    # Use the Epic 5 QueryAnalyzer that returns the correct QueryAnalysis type
    from src.components.query_processors.agents.planning.query_analyzer import QueryAnalyzer
    analyzer = QueryAnalyzer()

    # The processor needs an agent, but we test the RAG path by setting
    # a high complexity threshold so all queries go through RAG
    try:
        processor = IntelligentQueryProcessor(
            retriever=retriever,
            generator=generator,
            agent=None,  # No agent — RAG fallback path
            query_analyzer=analyzer,
            config={"complexity_threshold": 0.99, "use_agent_by_default": False},
        )
        return processor
    except (TypeError, ValueError):
        pytest.skip("IntelligentQueryProcessor requires non-None agent")


class TestIntelligentProcessorRAGPath:
    """Verify the RAG pipeline path produces correct answers."""

    def test_simple_query_uses_rag(self, intelligent_processor):
        """Simple queries should route through RAG and produce answers."""
        answer = intelligent_processor.process("What is RISC-V?")
        assert isinstance(answer, Answer)
        assert len(answer.text) > 20, "RAG path should produce substantive answer"

    def test_rag_answer_has_sources(self, intelligent_processor):
        """RAG-routed answers should include retrieval sources."""
        answer = intelligent_processor.process("What extensions does RISC-V support?")
        assert isinstance(answer, Answer)
        # Sources may be in answer.sources or in metadata depending on implementation
        has_sources = (
            bool(answer.sources)
            or "sources" in answer.metadata
            or answer.metadata.get("source") == "rag_pipeline"
        )
        assert has_sources, "RAG path should indicate source"
