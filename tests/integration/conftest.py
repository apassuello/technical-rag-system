"""
Pytest configuration for integration tests.
"""

import pytest
from pathlib import Path
from typing import List


@pytest.fixture(scope="session")
def project_root():
    """Provide project root path for all tests."""
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def orchestrator():
    """Create PlatformOrchestrator once for all integration tests."""
    from src.core.platform_orchestrator import PlatformOrchestrator

    config_path = Path(__file__).resolve().parents[2] / "config" / "test-ollama.yaml"
    return PlatformOrchestrator(config_path)


@pytest.fixture
def fresh_orchestrator():
    """Fresh PlatformOrchestrator for tests that mutate state."""
    from src.core.platform_orchestrator import PlatformOrchestrator

    config_path = Path(__file__).resolve().parents[2] / "config" / "test-ollama.yaml"
    return PlatformOrchestrator(config_path)


@pytest.fixture
def create_test_documents():
    """Create Document objects directly, bypassing PDF file processing.

    Returns a factory function that accepts content strings and produces
    Document objects suitable for ``orchestrator.index_documents()``.
    """
    from src.core.interfaces import Document

    def _create(*contents: str) -> List["Document"]:
        return [
            Document(
                content=c,
                metadata={"source": f"test_doc_{i}", "type": "test"},
            )
            for i, c in enumerate(contents, 1)
        ]

    return _create
