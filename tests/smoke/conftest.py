"""
Pytest configuration for smoke tests.

This conftest.py file ensures that smoke tests have proper import isolation
and access to project modules.
"""

import sys
import pytest
from pathlib import Path
from typing import Dict, Any

# Store original sys.path to restore between tests
_original_sys_path = None

@pytest.fixture(scope="function", autouse=True)
def setup_smoke_environment():
    """
    Automatically set up environment for each smoke test.
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
    
    # Clear any cached smoke test modules
    smoke_prefixes = [
        'tests.smoke',
        'test_smoke'
    ]
    modules_to_clear = [
        key for key in sys.modules.keys() 
        if any(key.startswith(prefix) for prefix in smoke_prefixes)
    ]
    for module in modules_to_clear:
        del sys.modules[module]
    
    yield  # Run the test
    
    # Restore original sys.path after test
    sys.path = _original_sys_path
    
    # Clear smoke modules that were imported during the test
    modules_to_clear = [
        key for key in sys.modules.keys() 
        if any(key.startswith(prefix) for prefix in smoke_prefixes)
    ]
    for module in modules_to_clear:
        del sys.modules[module]


@pytest.fixture(scope="session")
def project_root():
    """Provide project root path for all tests."""
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def smoke_test_data():
    """Provide common test data for smoke tests."""
    return {
        'basic_queries': [
            "Hello",
            "What is this?",
            "Test query"
        ],
        'simple_documents': [
            {'content': 'Simple test document', 'source': 'test.txt'},
            {'content': 'Another test document', 'source': 'test2.txt'}
        ],
        'health_endpoints': [
            '/health',
            '/status',
            '/ready'
        ]
    }


# Configure pytest markers for smoke tests
def pytest_configure(config):
    """Configure pytest for smoke tests."""
    config.addinivalue_line(
        "markers", "smoke: mark test as a smoke test"
    )
    config.addinivalue_line(
        "markers", "health_check: mark test as a health check"
    )
    config.addinivalue_line(
        "markers", "basic_functionality: mark test as basic functionality test"
    )
    config.addinivalue_line(
        "markers", "quick: mark test as a quick smoke test"
    )