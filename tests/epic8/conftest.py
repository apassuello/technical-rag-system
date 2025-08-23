"""
Pytest configuration for Epic 8 tests to fix import isolation issues.

This conftest.py file ensures that each service's tests have proper import isolation
and prevents sys.path pollution between different service tests.
"""

import sys
import pytest
from pathlib import Path
from typing import Dict, Any
import importlib

# Store original sys.path to restore between tests
_original_sys_path = None

@pytest.fixture(scope="function", autouse=True)
def isolate_service_imports():
    """
    Automatically isolate imports for each test to prevent conflicts.
    This fixture runs before and after every test.
    """
    global _original_sys_path
    
    # Store original sys.path before test
    _original_sys_path = sys.path.copy()
    
    # Clear any cached imports from service app modules
    service_prefixes = ['app.', 'gateway_app.', 'cache_app.', 'generator_app.', 'analyzer_app.', 'retriever_app.', 'analytics_app.']
    modules_to_clear = [key for key in sys.modules.keys() if any(key.startswith(prefix) for prefix in service_prefixes)]
    for module in modules_to_clear:
        del sys.modules[module]
    
    yield  # Run the test
    
    # Restore original sys.path after test
    sys.path = _original_sys_path
    
    # Clear any service imports that were added during the test
    service_prefixes = ['app.', 'gateway_app.', 'cache_app.', 'generator_app.', 'analyzer_app.', 'retriever_app.', 'analytics_app.']
    modules_to_clear = [key for key in sys.modules.keys() if any(key.startswith(prefix) for prefix in service_prefixes)]
    for module in modules_to_clear:
        del sys.modules[module]


@pytest.fixture(scope="module")
def service_imports():
    """
    Provide a clean way to import service modules for each test module.
    """
    def _import_service(service_name: str) -> Dict[str, Any]:
        """
        Import a specific service's modules.
        
        Args:
            service_name: Name of the service (e.g., 'generator', 'query-analyzer')
            
        Returns:
            Dictionary of imported classes and functions
        """
        project_root = Path(__file__).resolve().parents[2]
        service_path = project_root / "services" / service_name
        
        if not service_path.exists():
            raise ImportError(f"Service path does not exist: {service_path}")
        
        # Add service path to sys.path if not already there
        service_path_str = str(service_path)
        if service_path_str not in sys.path:
            sys.path.insert(0, service_path_str)
        
        imports = {}
        
        try:
            # Import based on service type
            if service_name == "generator":
                from generator_app.core.generator import GeneratorService
                from generator_app.schemas.requests import GenerateRequest, DocumentContext
                from generator_app.schemas.responses import GenerateResponse
                imports = {
                    'GeneratorService': GeneratorService,
                    'GenerateRequest': GenerateRequest,
                    'DocumentContext': DocumentContext,
                    'GenerateResponse': GenerateResponse
                }
            elif service_name == "query-analyzer":
                from analyzer_app.core.analyzer import QueryAnalyzerService
                from analyzer_app.schemas.requests import AnalyzeRequest
                from analyzer_app.schemas.responses import AnalyzeResponse
                imports = {
                    'QueryAnalyzerService': QueryAnalyzerService,
                    'AnalyzeRequest': AnalyzeRequest,
                    'AnalyzeResponse': AnalyzeResponse
                }
            elif service_name == "retriever":
                from retriever_app.core.retriever import RetrieverService
                imports = {'RetrieverService': RetrieverService}
            elif service_name == "cache":
                from cache_app.core.cache import CacheService, InMemoryCache
                imports = {
                    'CacheService': CacheService,
                    'InMemoryCache': InMemoryCache
                }
            elif service_name == "api-gateway":
                from gateway_app.core.gateway import APIGatewayService
                imports = {'APIGatewayService': APIGatewayService}
            elif service_name == "analytics":
                from analytics_app.core.analytics import AnalyticsService
                imports = {'AnalyticsService': AnalyticsService}
                
        except ImportError as e:
            raise ImportError(f"Failed to import {service_name} modules: {e}")
        
        return imports
    
    return _import_service


@pytest.fixture(scope="session")
def project_root():
    """Provide project root path for all tests."""
    return Path(__file__).resolve().parents[2]


# Configure pytest to not capture warnings about import issues
def pytest_configure(config):
    """Configure pytest for Epic 8 tests."""
    config.addinivalue_line(
        "markers", "service: mark test as belonging to a specific service"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )