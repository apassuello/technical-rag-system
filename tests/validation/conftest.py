"""Pytest configuration for validation tests."""

import pytest
from pathlib import Path

from src.core.platform_orchestrator import PlatformOrchestrator
from src.core.interfaces import Document
from .golden_corpus import ALL_CORPUS_TEXTS


@pytest.fixture
def orchestrator():
    """Create PlatformOrchestrator with test config."""
    config_path = Path(__file__).resolve().parents[2] / "config" / "test.yaml"
    return PlatformOrchestrator(config_path)


@pytest.fixture
def golden_documents():
    """4 Document objects: 3 on-topic RISC-V + 1 off-topic weather."""
    return [
        Document(content=text, metadata={"source": f"golden_{i}", "type": "test"})
        for i, text in enumerate(ALL_CORPUS_TEXTS)
    ]


@pytest.fixture
def indexed_orchestrator(orchestrator, golden_documents):
    """Orchestrator with golden corpus indexed."""
    count = orchestrator.index_documents(golden_documents)
    assert count == 4, f"Expected 4 docs indexed, got {count}"
    return orchestrator
