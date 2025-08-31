"""
Pytest configuration for Epic 8 API tests.

This conftest.py file ensures that API tests have proper import paths
for service app modules and handles service-specific imports.
"""

import sys
import pytest
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio

# Store original sys.path to restore between tests
_original_sys_path = None

@pytest.fixture(scope="function", autouse=True)
def setup_api_test_environment():
    """
    Set up the environment for each API test.
    Ensures all service app directories are in the path and manages Prometheus registry.
    """
    global _original_sys_path
    
    # Store original sys.path before test
    _original_sys_path = sys.path.copy()
    
    # Add project root and services to path
    project_root = Path(__file__).resolve().parents[3]
    src_path = project_root / "src"
    services_path = project_root / "services"
    
    # Add project root and src first
    paths_to_add = [str(project_root), str(src_path)]
    
    # Add specific service directories and their app subdirectories
    service_names = ['cache', 'api-gateway', 'retriever', 'generator', 'query-analyzer', 'analytics']
    
    for service_name in service_names:
        service_dir = services_path / service_name
        if service_dir.exists():
            # Add service directory
            paths_to_add.append(str(service_dir))
            
            # Add the app subdirectory (cache_app, gateway_app, etc.)
            # Handle both patterns: service_app and service-name_app
            app_name = service_name.replace('-', '_') + '_app'
            app_dir = service_dir / app_name
            
            if app_dir.exists():
                paths_to_add.append(str(app_dir))
            else:
                # Try without the service name prefix (just 'app')
                app_dir = service_dir / 'app'
                if app_dir.exists():
                    paths_to_add.append(str(app_dir))
    
    # Add all paths to sys.path
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    # Clear cached imports and reset Prometheus registry
    # Skip clearing modules for the service being tested to avoid breaking lifespan events
    import inspect
    test_function_name = None
    test_filename = None
    for frame_info in inspect.stack():
        if 'test_' in frame_info.function:
            test_function_name = frame_info.function
            test_filename = frame_info.filename
            break
    
    # Debug: Print what test we're running
    # print(f"DEBUG: Running test function: {test_function_name} in {test_filename}")
    
    service_modules = [
        'cache_app', 'gateway_app', 'retriever_app', 
        'generator_app', 'analyzer_app', 'analytics_app',
        'services.cache', 'services.api_gateway', 'services.retriever',
        'services.generator', 'services.query_analyzer', 'services.analytics'
    ]
    
    # Skip clearing modules that are being actively tested
    modules_to_skip = []
    if test_function_name and 'query_analyzer' in test_function_name:
        modules_to_skip.extend(['analyzer_app', 'services.query_analyzer'])
    elif test_function_name and 'cache' in test_function_name:
        modules_to_skip.extend(['cache_app', 'services.cache'])
    elif test_function_name and 'gateway' in test_function_name:
        modules_to_skip.extend(['gateway_app', 'services.api_gateway'])
    elif test_function_name and 'retriever' in test_function_name:
        modules_to_skip.extend(['retriever_app', 'services.retriever'])
    elif test_function_name and 'generator' in test_function_name:
        modules_to_skip.extend(['generator_app', 'services.generator'])
    elif test_function_name and 'analytics' in test_function_name:
        modules_to_skip.extend(['analytics_app', 'services.analytics'])
    
    for module_prefix in service_modules:
        if module_prefix in modules_to_skip:
            continue
        modules_to_clear = [
            key for key in list(sys.modules.keys()) 
            if key.startswith(module_prefix)
        ]
        for module in modules_to_clear:
            del sys.modules[module]
    
    # Import and use the Prometheus reset utility
    try:
        from .test_utils import reset_prometheus_registry
        reset_prometheus_registry()
    except ImportError:
        # Fallback manual reset if test_utils not available
        from prometheus_client import REGISTRY
        collectors = list(REGISTRY._collector_to_names.keys())
        for collector in collectors:
            try:
                REGISTRY.unregister(collector)
            except (KeyError, ValueError):
                pass
        REGISTRY._collector_to_names.clear()
        REGISTRY._names_to_collectors.clear()
    
    yield  # Run the test
    
    # Restore original sys.path after test
    sys.path = _original_sys_path
    
    # Clear service modules again (except the one being tested)
    for module_prefix in service_modules:
        if module_prefix in modules_to_skip:
            continue
        modules_to_clear = [
            key for key in list(sys.modules.keys()) 
            if key.startswith(module_prefix)
        ]
        for module in modules_to_clear:
            del sys.modules[module]


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def api_test_data():
    """Provide common test data for API tests."""
    return {
        'test_query': 'What is machine learning?',
        'test_documents': [
            {
                'content': 'Machine learning is a subset of artificial intelligence.',
                'metadata': {'source': 'test_doc_1.txt', 'page': 1}
            },
            {
                'content': 'Deep learning is a type of machine learning.',
                'metadata': {'source': 'test_doc_2.txt', 'page': 2}
            }
        ],
        'test_options': {
            'temperature': 0.7,
            'max_tokens': 150,
            'top_k': 5
        },
        'test_headers': {
            'Content-Type': 'application/json',
            'X-Request-ID': 'test-request-123'
        }
    }


@pytest.fixture
def mock_service_responses():
    """Provide mock responses for service calls."""
    return {
        'cache_hit': {
            'cached': True,
            'query_hash': 'abc123',
            'response': {'answer': 'Cached response', 'confidence': 0.9}
        },
        'cache_miss': {
            'cached': False,
            'query_hash': 'xyz789'
        },
        'query_analysis': {
            'complexity': 'medium',
            'domain': 'technical',
            'intent': 'explanation',
            'entities': ['machine learning']
        },
        'retrieval_results': {
            'documents': [
                {'id': '1', 'content': 'Document 1', 'score': 0.95},
                {'id': '2', 'content': 'Document 2', 'score': 0.85}
            ],
            'total': 2
        },
        'generation_result': {
            'answer': 'Generated answer text',
            'confidence': 0.85,
            'model': 'llama3.2:3b',
            'tokens_used': 120
        }
    }


# Configure pytest markers for API tests
def pytest_configure(config):
    """Configure pytest for API tests."""
    config.addinivalue_line(
        "markers", "api: mark test as an API test"
    )
    config.addinivalue_line(
        "markers", "async_test: mark test as async"
    )
    config.addinivalue_line(
        "markers", "requires_service: mark test as requiring a running service"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )