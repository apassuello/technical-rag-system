"""
Utilities for testing Epic 8 API services.

Handles Prometheus metrics registration issues and provides clean app instances for testing.
"""

import sys
import importlib
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch
from prometheus_client import CollectorRegistry, REGISTRY


def reset_prometheus_registry():
    """Reset the Prometheus registry to allow re-registration of metrics."""
    # Clear all collectors from the registry
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass
    
    # Clear the registry mappings
    REGISTRY._collector_to_names.clear()
    REGISTRY._names_to_collectors.clear()


def clear_module_cache(module_patterns: list):
    """Clear imported modules from sys.modules to force reimport."""
    modules_to_remove = []
    for pattern in module_patterns:
        modules_to_remove.extend([
            key for key in sys.modules.keys() 
            if pattern in key
        ])
    
    for module in modules_to_remove:
        sys.modules.pop(module, None)


def mock_prometheus_metrics():
    """Mock all Prometheus metric classes to prevent registration issues."""
    mock_counter = MagicMock()
    mock_counter.return_value = MagicMock()
    mock_counter.return_value.labels.return_value = MagicMock()
    mock_counter.return_value.labels.return_value.inc = MagicMock()
    
    mock_histogram = MagicMock()
    mock_histogram.return_value = MagicMock()
    mock_histogram.return_value.labels.return_value = MagicMock()
    mock_histogram.return_value.labels.return_value.observe = MagicMock()
    
    mock_gauge = MagicMock()
    mock_gauge.return_value = MagicMock()
    mock_gauge.return_value.set = MagicMock()
    
    return {
        'prometheus_client.Counter': mock_counter,
        'prometheus_client.Histogram': mock_histogram,
        'prometheus_client.Gauge': mock_gauge,
    }


def create_test_cache_app():
    """
    Create a test instance of the cache service app with mocked dependencies.
    
    This function handles:
    1. Prometheus metrics mocking to prevent registration conflicts
    2. Module cache clearing to ensure fresh imports
    3. Dependency injection for testability
    """
    # Clear any previously imported cache modules
    clear_module_cache(['cache_app', 'services.cache'])
    
    # Mock Prometheus metrics before importing
    with patch.multiple('prometheus_client', 
                       Counter=MagicMock(return_value=MagicMock()),
                       Histogram=MagicMock(return_value=MagicMock()),
                       Gauge=MagicMock(return_value=MagicMock())):
        
        # Mock Redis client to avoid needing actual Redis
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_redis_instance = MagicMock()
            mock_redis_instance.get = MagicMock(return_value=None)
            mock_redis_instance.set = MagicMock(return_value=True)
            mock_redis_instance.delete = MagicMock(return_value=1)
            mock_redis_instance.exists = MagicMock(return_value=0)
            mock_redis_instance.ping = MagicMock(return_value=True)
            mock_redis.from_url.return_value = mock_redis_instance
            
            # Now we can safely import the app
            from services.cache.cache_app.main import create_app
            
            # Create app with test configuration
            app = create_app()
            
            # Attach the mock redis for test access
            app.state.mock_redis = mock_redis_instance
            
            return app


def create_test_gateway_app():
    """Create a test instance of the API gateway app."""
    clear_module_cache(['gateway_app', 'services.api-gateway'])
    
    with patch.multiple('prometheus_client',
                       Counter=MagicMock(return_value=MagicMock()),
                       Histogram=MagicMock(return_value=MagicMock()),
                       Gauge=MagicMock(return_value=MagicMock())):
        
        # Mock service clients
        with patch('httpx.AsyncClient') as mock_client:
            mock_client_instance = MagicMock()
            mock_client_instance.post = MagicMock(return_value=MagicMock(status_code=200, json=lambda: {}))
            mock_client_instance.get = MagicMock(return_value=MagicMock(status_code=200, json=lambda: {}))
            mock_client.return_value.__aenter__ = MagicMock(return_value=mock_client_instance)
            mock_client.return_value.__aexit__ = MagicMock(return_value=None)
            
            from services.api_gateway.gateway_app.main import create_app
            app = create_app()
            app.state.mock_client = mock_client_instance
            
            return app


def create_test_retriever_app():
    """Create a test instance of the retriever service app."""
    clear_module_cache(['retriever_app', 'services.retriever'])
    
    with patch.multiple('prometheus_client',
                       Counter=MagicMock(return_value=MagicMock()),
                       Histogram=MagicMock(return_value=MagicMock()),
                       Gauge=MagicMock(return_value=MagicMock())):
        
        # Mock FAISS index
        with patch('faiss.IndexFlatL2') as mock_index:
            mock_index_instance = MagicMock()
            mock_index_instance.search = MagicMock(return_value=([0.9], [[0]]))
            mock_index_instance.add = MagicMock()
            mock_index.return_value = mock_index_instance
            
            from services.retriever.retriever_app.main import create_app
            app = create_app()
            app.state.mock_index = mock_index_instance
            
            return app


class MockCache:
    """Mock cache for testing without Redis."""
    
    def __init__(self):
        self.data = {}
    
    async def get(self, key: str) -> Optional[str]:
        return self.data.get(key)
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        self.data[key] = value
        return True
    
    async def delete(self, key: str) -> int:
        if key in self.data:
            del self.data[key]
            return 1
        return 0
    
    async def exists(self, key: str) -> int:
        return 1 if key in self.data else 0
    
    async def ping(self) -> bool:
        return True
    
    async def flushall(self) -> None:
        self.data.clear()
    
    async def dbsize(self) -> int:
        return len(self.data)