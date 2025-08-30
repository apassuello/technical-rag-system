"""
Pytest configuration for diagnostic tests.

This conftest.py file ensures that diagnostic tests have proper import isolation
and access to project modules.
"""

import sys
import pytest
from pathlib import Path
from typing import Dict, Any

# Store original sys.path to restore between tests
_original_sys_path = None

@pytest.fixture(scope="function", autouse=True)
def setup_diagnostic_environment():
    """
    Automatically set up environment for each diagnostic test.
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
    
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    # Clear any cached diagnostic test modules
    diagnostic_prefixes = [
        'tests.diagnostic',
        'test_diagnostic'
    ]
    modules_to_clear = [
        key for key in sys.modules.keys() 
        if any(key.startswith(prefix) for prefix in diagnostic_prefixes)
    ]
    for module in modules_to_clear:
        del sys.modules[module]
    
    yield  # Run the test
    
    # Restore original sys.path after test
    sys.path = _original_sys_path
    
    # Clear diagnostic modules that were imported during the test
    modules_to_clear = [
        key for key in sys.modules.keys() 
        if any(key.startswith(prefix) for prefix in diagnostic_prefixes)
    ]
    for module in modules_to_clear:
        del sys.modules[module]


@pytest.fixture(scope="session")
def project_root():
    """Provide project root path for all tests."""
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def diagnostic_test_data():
    """Provide common test data for diagnostic tests."""
    return {
        'sample_documents': [
            {'content': 'Sample document content', 'metadata': {'source': 'test.txt'}},
            {'content': 'Another document', 'metadata': {'source': 'test2.txt'}}
        ],
        'sample_queries': [
            "What is Python?",
            "How does the system work?",
            "Technical documentation question"
        ],
        'test_configurations': {
            'basic': {'timeout': 5, 'max_retries': 3},
            'extended': {'timeout': 30, 'max_retries': 5}
        }
    }


# Configure pytest markers for diagnostic tests
def pytest_configure(config):
    """Configure pytest for diagnostic tests."""
    config.addinivalue_line(
        "markers", "forensic: mark test as a forensic diagnostic test"
    )
    config.addinivalue_line(
        "markers", "system_validation: mark test as system validation"
    )
    config.addinivalue_line(
        "markers", "performance_diagnostic: mark test as performance diagnostic"
    )
    config.addinivalue_line(
        "markers", "component_diagnostic: mark test as component diagnostic"
    )