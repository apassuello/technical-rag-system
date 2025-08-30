"""
Pytest configuration for Epic 1 tests to fix import isolation issues.

This conftest.py file ensures that Epic 1 tests have proper import isolation
and prevents sys.path pollution between different test modules.
"""

import sys
import pytest
from pathlib import Path
from typing import Dict, Any
import importlib

# Store original sys.path to restore between tests
_original_sys_path = None

@pytest.fixture(scope="function", autouse=True)
def isolate_epic1_imports():
    """
    Automatically isolate imports for each test to prevent conflicts.
    This fixture runs before and after every test.
    """
    global _original_sys_path
    
    # Store original sys.path before test
    _original_sys_path = sys.path.copy()
    
    # Add project root to sys.path for Epic 1 tests
    project_root = Path(__file__).resolve().parents[2]
    src_path = project_root / "src"
    
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Clear any cached imports from Epic 1 modules
    epic1_prefixes = [
        'src.components.query_processors.analyzers.epic1',
        'src.training.',
        'epic1_',
        'test_epic1'
    ]
    modules_to_clear = [
        key for key in sys.modules.keys() 
        if any(key.startswith(prefix) for prefix in epic1_prefixes)
    ]
    for module in modules_to_clear:
        del sys.modules[module]
    
    yield  # Run the test
    
    # Restore original sys.path after test
    sys.path = _original_sys_path
    
    # Clear any Epic 1 imports that were added during the test
    modules_to_clear = [
        key for key in sys.modules.keys() 
        if any(key.startswith(prefix) for prefix in epic1_prefixes)
    ]
    for module in modules_to_clear:
        del sys.modules[module]


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


# Configure pytest to not capture warnings about import issues
def pytest_configure(config):
    """Configure pytest for Epic 1 tests."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "training: mark test as related to training functionality"
    )
    config.addinivalue_line(
        "markers", "ml_mode: mark test as related to ML mode functionality"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )