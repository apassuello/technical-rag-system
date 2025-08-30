"""
Pytest configuration for integration tests.

This conftest.py file ensures that integration tests have proper import isolation
and access to project modules.
"""

import sys
import pytest
from pathlib import Path
from typing import Dict, Any

# Store original sys.path to restore between tests
_original_sys_path = None

@pytest.fixture(scope="function", autouse=True)
def setup_integration_environment():
    """
    Automatically set up environment for each integration test.
    This fixture runs before and after every test.
    """
    global _original_sys_path
    
    # Store original sys.path before test
    _original_sys_path = sys.path.copy()
    
    # Add project root and src to sys.path
    project_root = Path(__file__).resolve().parents[2]
    src_path = project_root / "src"
    services_path = project_root / "services"
    
    paths_to_add = [str(project_root), str(src_path)]
    
    # Add service paths if they exist
    if services_path.exists():
        for service_dir in services_path.iterdir():
            if service_dir.is_dir():
                paths_to_add.append(str(service_dir))
                # Also add service app subdirectories
                app_dirs = ['app', f'{service_dir.name}_app']
                for app_dir in app_dirs:
                    app_path = service_dir / app_dir
                    if app_path.exists():
                        paths_to_add.append(str(app_path))
    
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    # Clear any cached integration test modules
    integration_prefixes = [
        'tests.integration',
        'test_integration'
    ]
    modules_to_clear = [
        key for key in sys.modules.keys() 
        if any(key.startswith(prefix) for prefix in integration_prefixes)
    ]
    for module in modules_to_clear:
        del sys.modules[module]
    
    yield  # Run the test
    
    # Restore original sys.path after test
    sys.path = _original_sys_path
    
    # Clear integration modules that were imported during the test
    modules_to_clear = [
        key for key in sys.modules.keys() 
        if any(key.startswith(prefix) for prefix in integration_prefixes)
    ]
    for module in modules_to_clear:
        del sys.modules[module]


@pytest.fixture(scope="session")
def project_root():
    """Provide project root path for all tests."""
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def integration_test_data():
    """Provide common test data for integration tests."""
    return {
        'test_documents': [
            {'content': 'Integration test document 1', 'metadata': {'source': 'integration1.txt'}},
            {'content': 'Integration test document 2', 'metadata': {'source': 'integration2.txt'}},
            {'content': 'Complex integration test document with more content', 'metadata': {'source': 'integration3.txt'}}
        ],
        'test_queries': [
            "What is the main topic of the documents?",
            "How does component X integrate with component Y?",
            "End-to-end workflow test query"
        ],
        'test_configs': {
            'basic_pipeline': {
                'processor': 'modular',
                'embedder': 'sentence_transformer', 
                'retriever': 'modular_unified',
                'generator': 'adaptive_modular'
            },
            'epic1_pipeline': {
                'processor': 'epic1_domain_aware',
                'generator': 'epic1_multi_model'
            }
        }
    }


# Configure pytest markers for integration tests
def pytest_configure(config):
    """Configure pytest for integration tests."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "end_to_end: mark test as end-to-end workflow test"
    )
    config.addinivalue_line(
        "markers", "component_integration: mark test as component integration test"
    )
    config.addinivalue_line(
        "markers", "service_integration: mark test as service integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running integration test"
    )