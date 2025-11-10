"""
Pytest configuration for system tests.

This conftest.py file ensures that system tests have proper import isolation
and access to project modules.
"""

import sys
import pytest
from pathlib import Path
from typing import Dict, Any

# Store original sys.path to restore between tests
_original_sys_path = None

@pytest.fixture(scope="function", autouse=True)
def setup_system_environment():
    """
    Automatically set up environment for each system test.
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
    
    # Clear any cached system test modules
    system_prefixes = [
        'tests.system',
        'test_system'
    ]
    modules_to_clear = [
        key for key in sys.modules.keys() 
        if any(key.startswith(prefix) for prefix in system_prefixes)
    ]
    for module in modules_to_clear:
        del sys.modules[module]
    
    yield  # Run the test
    
    # Restore original sys.path after test
    sys.path = _original_sys_path
    
    # Clear system modules that were imported during the test
    modules_to_clear = [
        key for key in sys.modules.keys() 
        if any(key.startswith(prefix) for prefix in system_prefixes)
    ]
    for module in modules_to_clear:
        del sys.modules[module]


@pytest.fixture(scope="session")
def project_root():
    """Provide project root path for all tests."""
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def system_test_data():
    """Provide common test data for system tests."""
    return {
        'system_queries': [
            "System-level test query 1",
            "End-to-end system functionality test",
            "Full pipeline system test"
        ],
        'load_test_data': {
            'concurrent_users': [1, 5, 10, 20],
            'query_batches': [10, 50, 100],
            'timeout_thresholds': [5, 10, 30]
        },
        'system_configurations': {
            'minimal': {'components': 'basic', 'performance': 'low'},
            'standard': {'components': 'full', 'performance': 'medium'},
            'high_performance': {'components': 'full', 'performance': 'high'}
        }
    }


# Configure pytest markers for system tests
def pytest_configure(config):
    """Configure pytest for system tests."""
    config.addinivalue_line(
        "markers", "system: mark test as a system test"
    )
    config.addinivalue_line(
        "markers", "load_test: mark test as load/stress test"
    )
    config.addinivalue_line(
        "markers", "full_pipeline: mark test as full pipeline test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running system test"
    )