"""
Pytest configuration for component tests.

This conftest.py file ensures that component tests have proper import isolation
and access to project modules.
"""

import sys
import pytest
from pathlib import Path
from typing import Dict, Any

# Store original sys.path to restore between tests
_original_sys_path = None

@pytest.fixture(scope="function", autouse=True)
def setup_component_environment():
    """
    Automatically set up environment for each component test.
    This fixture runs before and after every test.
    """
    global _original_sys_path
    
    # Store original sys.path before test
    _original_sys_path = sys.path.copy()
    
    # Add project root and src to sys.path
    project_root = Path(__file__).resolve().parents[2]
    src_path = project_root / "src"
    
    paths_to_add = [str(project_root), str(src_path)]
    
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    # Clear any cached component test modules
    component_prefixes = [
        'tests.component',
        'test_component'
    ]
    modules_to_clear = [
        key for key in sys.modules.keys() 
        if any(key.startswith(prefix) for prefix in component_prefixes)
    ]
    for module in modules_to_clear:
        del sys.modules[module]
    
    yield  # Run the test
    
    # Restore original sys.path after test
    sys.path = _original_sys_path
    
    # Clear component modules that were imported during the test
    modules_to_clear = [
        key for key in sys.modules.keys() 
        if any(key.startswith(prefix) for prefix in component_prefixes)
    ]
    for module in modules_to_clear:
        del sys.modules[module]


@pytest.fixture(scope="session")
def project_root():
    """Provide project root path for all tests."""
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def component_test_data():
    """Provide common test data for component tests."""
    return {
        'sample_text': 'This is sample text for component testing.',
        'sample_embeddings': [0.1, 0.2, 0.3, 0.4, 0.5],
        'sample_documents': [
            {'content': 'Component test document', 'metadata': {'source': 'comp_test.txt'}},
        ],
        'test_configurations': {
            'embedder': {
                'model_name': 'sentence-transformers/all-MiniLM-L6-v2',
                'device': 'cpu'
            },
            'retriever': {
                'similarity_top_k': 5,
                'fusion_method': 'rrf'
            },
            'generator': {
                'model': 'llama3.2:3b',
                'temperature': 0.1
            }
        }
    }


# Configure pytest markers for component tests
def pytest_configure(config):
    """Configure pytest for component tests."""
    config.addinivalue_line(
        "markers", "component: mark test as a component test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "embedder: mark test as embedder component test"
    )
    config.addinivalue_line(
        "markers", "retriever: mark test as retriever component test"
    )
    config.addinivalue_line(
        "markers", "generator: mark test as generator component test"
    )
    config.addinivalue_line(
        "markers", "processor: mark test as processor component test"
    )