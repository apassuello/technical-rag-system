"""
Pytest configuration for Epic 1 tests.
"""

import sys
import pytest
from pathlib import Path
from typing import Dict, Any


@pytest.fixture(scope="module")
def epic1_imports():
    """
    Provide a clean way to import Epic 1 modules for each test module.
    """
    def _import_epic1_component(component_name: str) -> Dict[str, Any]:
        """
        Import specific Epic 1 components.

        Args:
            component_name: Name of the component ('analyzer', 'training', 'ml_models')

        Returns:
            Dictionary of imported classes and functions
        """
        project_root = Path(__file__).resolve().parents[2]
        src_path = project_root / "src"

        if not src_path.exists():
            raise ImportError(f"Source path does not exist: {src_path}")

        imports = {}

        try:
            if component_name == "analyzer":
                from src.components.query_processors.analyzers.epic1_ml_analyzer import Epic1MLAnalyzer
                from src.components.query_processors.analyzers.epic1_query_analyzer import Epic1QueryAnalyzer
                imports = {
                    'Epic1MLAnalyzer': Epic1MLAnalyzer,
                    'Epic1QueryAnalyzer': Epic1QueryAnalyzer
                }
            elif component_name == "training":
                from src.training.dataset_generation_framework import ClaudeDatasetGenerator, DatasetGenerationConfig
                from src.training.data_loader import Epic1DataLoader
                from src.training.view_trainer import ViewTrainer
                imports = {
                    'ClaudeDatasetGenerator': ClaudeDatasetGenerator,
                    'DatasetGenerationConfig': DatasetGenerationConfig,
                    'Epic1DataLoader': Epic1DataLoader,
                    'ViewTrainer': ViewTrainer
                }
            elif component_name == "ml_models":
                from src.components.query_processors.analyzers.ml_models.model_manager import ModelManager
                imports = {'ModelManager': ModelManager}
            elif component_name == "views":
                from src.components.query_processors.analyzers.epic1_ml_analyzer import (
                    SemanticView, TechnicalView, ContextualView, StructuralView
                )
                imports = {
                    'SemanticView': SemanticView,
                    'TechnicalView': TechnicalView,
                    'ContextualView': ContextualView,
                    'StructuralView': StructuralView
                }

        except ImportError as e:
            raise ImportError(f"Failed to import {component_name} modules: {e}")

        return imports

    return _import_epic1_component


@pytest.fixture(scope="session")
def project_root():
    """Provide project root path for all tests."""
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def epic1_test_data():
    """Provide common test data for Epic 1 tests."""
    return {
        'simple_queries': [
            "What is Python?",
            "How to print hello world?",
            "List common HTTP status codes"
        ],
        'medium_queries': [
            "How do I implement rate limiting for REST APIs?",
            "Explain database indexing strategies",
            "How to optimize SQL queries for performance?"
        ],
        'complex_queries': [
            "How can I design a distributed consensus algorithm with Byzantine fault tolerance?",
            "Explain transformer attention mechanisms in detail with mathematical formulations",
            "Design a microservices architecture for high-throughput data processing"
        ]
    }
