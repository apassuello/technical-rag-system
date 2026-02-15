"""
Pytest configuration for integration tests.

Consolidated from:
- tests/integration/conftest.py (original)
- tests/component/conftest.py (component_test_data)
- tests/epic1/conftest.py (epic1_imports → ml_imports, epic1_test_data → analyzer_test_data)
"""

import sys

import pytest
from pathlib import Path
from typing import Any, Dict, List

# Add tests/unit/ to sys.path so integration tests that import from
# ``fixtures.xxx`` (shared ML test fixtures) can resolve them.
_UNIT_DIR = Path(__file__).resolve().parent.parent / "unit"
if str(_UNIT_DIR) not in sys.path:
    sys.path.insert(0, str(_UNIT_DIR))


@pytest.fixture(scope="session")
def project_root():
    """Provide project root path for all tests."""
    return Path(__file__).resolve().parents[2]


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


# ---------------------------------------------------------------------------
# From tests/component/conftest.py
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def component_test_data():
    """Provide common test data for component-level integration tests."""
    return {
        "sample_text": "This is sample text for component testing.",
        "sample_embeddings": [0.1, 0.2, 0.3, 0.4, 0.5],
        "sample_documents": [
            {"content": "Component test document", "metadata": {"source": "comp_test.txt"}},
        ],
        "test_configurations": {
            "embedder": {
                "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                "device": "cpu",
            },
            "retriever": {"similarity_top_k": 5, "fusion_method": "rrf"},
            "generator": {"model": "qwen2.5-1.5b-instruct", "temperature": 0.1},
        },
    }


# ---------------------------------------------------------------------------
# From tests/epic1/conftest.py (renamed for generic use)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def ml_imports():
    """Import ML/Epic1 components by name.

    Usage::

        def test_analyzer(ml_imports):
            classes = ml_imports("analyzer")
            analyzer = classes["Epic1MLAnalyzer"]()
    """

    def _import_component(component_name: str) -> Dict[str, Any]:
        imports: Dict[str, Any] = {}

        try:
            if component_name == "analyzer":
                from src.components.query_processors.analyzers.epic1_ml_analyzer import (
                    Epic1MLAnalyzer,
                )
                from src.components.query_processors.analyzers.epic1_query_analyzer import (
                    Epic1QueryAnalyzer,
                )

                imports = {
                    "Epic1MLAnalyzer": Epic1MLAnalyzer,
                    "Epic1QueryAnalyzer": Epic1QueryAnalyzer,
                }
            elif component_name == "training":
                from src.training.dataset_generation_framework import (
                    ClaudeDatasetGenerator,
                    DatasetGenerationConfig,
                )
                from src.training.data_loader import Epic1DataLoader
                from src.training.view_trainer import ViewTrainer

                imports = {
                    "ClaudeDatasetGenerator": ClaudeDatasetGenerator,
                    "DatasetGenerationConfig": DatasetGenerationConfig,
                    "Epic1DataLoader": Epic1DataLoader,
                    "ViewTrainer": ViewTrainer,
                }
            elif component_name == "ml_models":
                from src.components.query_processors.analyzers.ml_models.model_manager import (
                    ModelManager,
                )

                imports = {"ModelManager": ModelManager}
            elif component_name == "views":
                from src.components.query_processors.analyzers.epic1_ml_analyzer import (
                    SemanticView,
                    TechnicalView,
                    ContextualView,
                    StructuralView,
                )

                imports = {
                    "SemanticView": SemanticView,
                    "TechnicalView": TechnicalView,
                    "ContextualView": ContextualView,
                    "StructuralView": StructuralView,
                }
        except ImportError as e:
            raise ImportError(f"Failed to import {component_name} modules: {e}")

        return imports

    return _import_component


@pytest.fixture(scope="session")
def analyzer_test_data():
    """Common test data for ML analyzer integration tests."""
    return {
        "simple_queries": [
            "What is Python?",
            "How to print hello world?",
            "List common HTTP status codes",
        ],
        "medium_queries": [
            "How do I implement rate limiting for REST APIs?",
            "Explain database indexing strategies",
            "How to optimize SQL queries for performance?",
        ],
        "complex_queries": [
            "How can I design a distributed consensus algorithm with Byzantine fault tolerance?",
            "Explain transformer attention mechanisms in detail with mathematical formulations",
            "Design a microservices architecture for high-throughput data processing",
        ],
    }
