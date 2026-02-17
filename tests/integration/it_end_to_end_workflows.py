"""
Phase 5.1: End-to-End Integration Tests

Comprehensive integration testing for the complete RAG system workflows.
Tests the entire pipeline from document processing to answer generation,
verifying that retrieval actually finds indexed content.
"""

import os
import time
import pytest
import tempfile
from pathlib import Path

from src.core.platform_orchestrator import PlatformOrchestrator
from src.core.interfaces import Answer
from tests.validation.golden_corpus import (
    RISCV_OVERVIEW,
    RISCV_EXTENSIONS,
    RISCV_APPLICATIONS,
)


@pytest.mark.integration
@pytest.mark.requires_ml
@pytest.mark.requires_ollama
class TestEndToEndWorkflows:
    """Test complete end-to-end workflows for the RAG system."""

    @pytest.fixture
    def test_document(self):
        """Get the dedicated integration test PDF."""
        test_pdf = Path(__file__).parent / "fixtures" / "test_riscv_basics.pdf"
        if not test_pdf.exists():
            pytest.skip("Integration test PDF not found")
        return test_pdf

    @pytest.fixture
    def indexed_orchestrator(self, orchestrator, create_test_documents):
        """Orchestrator pre-loaded with substantial RISC-V content.

        Indexes three paragraphs covering overview, extensions, and
        applications — enough for retrieval to reliably find matches.
        """
        docs = create_test_documents(RISCV_OVERVIEW, RISCV_EXTENSIONS, RISCV_APPLICATIONS)
        count = orchestrator.index_documents(docs)
        assert count == 3, f"Expected 3 docs indexed, got {count}"
        return orchestrator

    # -- Document processing --

    def test_complete_document_processing_workflow(self, orchestrator, test_document):
        """Test complete document processing from PDF to indexed chunks."""
        chunk_count = orchestrator.process_document(test_document)
        assert chunk_count > 0, f"No chunks were processed: {chunk_count}"

        system_health = orchestrator.get_system_health()
        assert system_health["status"] == "healthy"
        assert system_health["initialized"]

    # -- Query pipeline (index → retrieve → generate) --

    def test_complete_query_processing_workflow(self, indexed_orchestrator):
        """Test full query pipeline with guaranteed retrieval."""
        answer = indexed_orchestrator.process_query("What is RISC-V?")

        assert isinstance(answer, Answer)
        assert answer.text, "Answer should not be empty"
        assert len(answer.text) > 10, "Answer should be substantial"
        assert answer.sources, "Retrieval should find indexed content"
        assert answer.confidence > 0.1, "In-domain query should have meaningful confidence"
        assert isinstance(answer.metadata, dict)
        assert any(
            "RISC-V" in s.content or "instruction set" in s.content
            for s in answer.sources
        ), "Sources should contain query-relevant content"

    def test_multi_document_workflow(self, indexed_orchestrator):
        """Test querying across multiple indexed documents."""
        answer = indexed_orchestrator.process_query("What are RISC-V extensions?")

        assert isinstance(answer, Answer)
        assert answer.text
        assert answer.sources, "Should retrieve from indexed content"
        assert any(
            "extension" in s.content.lower() for s in answer.sources
        ), "Sources should match the extensions query"

    # -- Error handling --

    def test_error_handling_workflow(self, orchestrator):
        """Test error handling for missing files and empty index."""
        with pytest.raises(FileNotFoundError):
            orchestrator.process_document(Path("/tmp/non_existent_doc.pdf"))

        # Need a fresh orchestrator with empty index for this assertion —
        # the session-scoped fixture may already have indexed documents.
        config_path = Path(__file__).resolve().parent.parent.parent / "config" / "test-local.yaml"
        fresh = PlatformOrchestrator(config_path)
        with pytest.raises(RuntimeError, match="No documents have been indexed"):
            fresh.process_query("What is quantum computing?")

    # -- Health monitoring --

    def test_system_health_monitoring_workflow(self, indexed_orchestrator):
        """Test system health stays healthy through the full pipeline."""
        health = indexed_orchestrator.get_system_health()
        assert health["status"] == "healthy"

        indexed_orchestrator.process_query("What is RISC-V?")
        post_query_health = indexed_orchestrator.get_system_health()
        assert post_query_health["status"] == "healthy"

    # -- Performance --

    def test_performance_metrics_workflow(self, orchestrator, test_document):
        """Test that processing and querying complete in measurable time."""
        start = time.perf_counter()
        chunk_count = orchestrator.process_document(test_document)
        processing_time = time.perf_counter() - start

        assert chunk_count > 0
        assert processing_time < 60, "Document processing should complete within 60s"

        start = time.perf_counter()
        answer = orchestrator.process_query("What is RISC-V?")
        query_time = time.perf_counter() - start

        assert isinstance(answer, Answer)
        assert query_time < 60, "Query processing should complete within 60s"


@pytest.mark.integration
@pytest.mark.requires_ml
@pytest.mark.requires_ollama
class TestArchitectureCompatibility:
    """Test the unified retriever architecture produces meaningful answers."""

    def test_unified_architecture_workflow(self, orchestrator, create_test_documents):
        """Test index → query → answer with unified retriever."""
        docs = create_test_documents(RISCV_OVERVIEW, RISCV_EXTENSIONS)
        chunk_count = orchestrator.index_documents(docs)
        assert chunk_count == 2

        answer = orchestrator.process_query("What is RISC-V?")
        assert isinstance(answer, Answer)
        assert answer.text
        assert answer.sources, "Should retrieve indexed content"

    def test_architecture_comparison(self, orchestrator, create_test_documents):
        """Test that different queries produce distinct, sourced answers."""
        docs = create_test_documents(RISCV_OVERVIEW, RISCV_EXTENSIONS, RISCV_APPLICATIONS)
        orchestrator.index_documents(docs)

        answer1 = orchestrator.process_query("What is RISC-V?")
        answer2 = orchestrator.process_query("What extensions does RISC-V support?")

        for answer in (answer1, answer2):
            assert isinstance(answer, Answer)
            assert answer.text
            assert answer.sources, "Each query should retrieve indexed content"

        assert answer1.text != answer2.text, "Different queries should produce different answers"


@pytest.mark.integration
@pytest.mark.requires_ml
class TestErrorRecoveryScenarios:
    """Test error handling and recovery scenarios."""

    def test_invalid_document_recovery(self, orchestrator):
        """Test that processing an empty PDF returns 0 and system stays healthy."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            invalid_doc = Path(f.name)

        try:
            chunk_count = orchestrator.process_document(invalid_doc)
            assert chunk_count == 0, "Empty PDF should produce 0 chunks"

            health = orchestrator.get_system_health()
            assert health["status"] == "healthy"
        finally:
            os.unlink(invalid_doc)

    @pytest.mark.requires_ollama
    def test_memory_pressure_recovery(self, orchestrator, create_test_documents):
        """Test indexing and querying a large document."""
        large_content = (
            "This document discusses memory management in modern operating systems. "
            "Virtual memory, page tables, and TLBs are fundamental concepts. "
        ) * 100
        docs = create_test_documents(large_content)

        chunk_count = orchestrator.index_documents(docs)
        assert chunk_count > 0

        answer = orchestrator.process_query("What is memory management?")
        assert isinstance(answer, Answer)
        assert answer.text
        assert answer.sources, "Should retrieve from large indexed document"

        health = orchestrator.get_system_health()
        assert health["status"] == "healthy"

    @pytest.mark.requires_ollama
    def test_sequential_multi_query(self, orchestrator, create_test_documents):
        """Test handling multiple sequential queries on indexed content."""
        docs = create_test_documents(RISCV_OVERVIEW, RISCV_EXTENSIONS, RISCV_APPLICATIONS)
        orchestrator.index_documents(docs)

        queries = [
            "What is RISC-V?",
            "What extensions does RISC-V support?",
            "Where are RISC-V processors used?",
        ]

        answers = []
        for query in queries:
            answer = orchestrator.process_query(query)
            answers.append(answer)

        assert len(answers) == len(queries)
        for answer in answers:
            assert isinstance(answer, Answer)
            assert answer.text
            assert answer.sources, "Each query should retrieve indexed content"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
