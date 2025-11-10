"""
Configuration for Epic 8 API integration tests against running Docker containers.

This conftest ensures tests connect to actual running services instead of
trying to instantiate them locally.
"""

import pytest
import pytest_asyncio
import httpx
import asyncio
import time
from typing import Dict, Any, AsyncGenerator
from pathlib import Path

# Service URLs for Docker containers
SERVICE_URLS = {
    'api_gateway': 'http://localhost:8080',
    'cache': 'http://localhost:8084',
    'retriever': 'http://localhost:8083',
    'generator': 'http://localhost:8081',
    'query_analyzer': 'http://localhost:8082',
    'analytics': 'http://localhost:8085',
}

# Health check endpoints
HEALTH_ENDPOINTS = {
    'api_gateway': '/health',
    'cache': '/health',
    'retriever': '/health',
    'generator': '/health',
    'query_analyzer': '/health',
    'analytics': '/health',
}


@pytest_asyncio.fixture(scope="session")
async def service_health_check():
    """Check if all required services are running and healthy."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        for service_name, base_url in SERVICE_URLS.items():
            health_endpoint = HEALTH_ENDPOINTS.get(service_name, '/health')
            try:
                response = await client.get(f"{base_url}{health_endpoint}")
                if response.status_code != 200:
                    pytest.skip(f"Service {service_name} is not healthy: {response.status_code}")
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                pytest.skip(f"Service {service_name} is not reachable: {e}")
    
    return True


@pytest_asyncio.fixture
async def cache_client(service_health_check) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Async HTTP client for Cache Service."""
    async with httpx.AsyncClient(base_url=SERVICE_URLS['cache'], timeout=10.0) as client:
        yield client


@pytest_asyncio.fixture
async def gateway_client(service_health_check) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Async HTTP client for API Gateway."""
    async with httpx.AsyncClient(base_url=SERVICE_URLS['api_gateway'], timeout=10.0) as client:
        yield client


@pytest_asyncio.fixture
async def retriever_client(service_health_check) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Async HTTP client for Retriever Service."""
    async with httpx.AsyncClient(base_url=SERVICE_URLS['retriever'], timeout=10.0) as client:
        yield client


@pytest_asyncio.fixture
async def generator_client(service_health_check) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Async HTTP client for Generator Service."""
    async with httpx.AsyncClient(base_url=SERVICE_URLS['generator'], timeout=10.0) as client:
        yield client


@pytest_asyncio.fixture
async def analytics_client(service_health_check) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Async HTTP client for Analytics Service."""
    async with httpx.AsyncClient(base_url=SERVICE_URLS['analytics'], timeout=10.0) as client:
        yield client


@pytest_asyncio.fixture
async def query_analyzer_client(service_health_check) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Async HTTP client for Query Analyzer Service."""
    async with httpx.AsyncClient(base_url=SERVICE_URLS['query_analyzer'], timeout=10.0) as client:
        yield client


@pytest.fixture
def sample_query_data():
    """Sample query data for testing."""
    return {
        "simple": {
            "query": "What is Python?",
            "options": {
                "temperature": 0.7,
                "max_tokens": 150
            }
        },
        "complex": {
            "query": "Explain the implementation details of transformer attention mechanisms with mathematical formulations",
            "options": {
                "temperature": 0.3,
                "max_tokens": 500
            }
        }
    }


@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    return [
        {
            "id": "doc1",
            "content": "Python is a high-level programming language.",
            "metadata": {"source": "test_doc1.txt", "page": 1}
        },
        {
            "id": "doc2",
            "content": "Machine learning uses Python extensively.",
            "metadata": {"source": "test_doc2.txt", "page": 2}
        }
    ]


@pytest.fixture
def sample_cache_data():
    """Sample cache data for testing."""
    return {
        "query": "What is RISC-V?",
        "response": {
            "answer": "RISC-V is an open-source instruction set architecture",
            "confidence": 0.95,
            "sources": ["risc-v-spec.pdf"],
            "metadata": {"tokens": 150, "model": "test-model"}
        },
        "ttl": 3600
    }


# Helper functions for common test operations
async def wait_for_service(service_name: str, timeout: float = 30.0) -> bool:
    """Wait for a service to become available."""
    base_url = SERVICE_URLS.get(service_name)
    if not base_url:
        return False
    
    health_endpoint = HEALTH_ENDPOINTS.get(service_name, '/health')
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        while time.time() - start_time < timeout:
            try:
                response = await client.get(f"{base_url}{health_endpoint}", timeout=2.0)
                if response.status_code == 200:
                    return True
            except (httpx.ConnectError, httpx.TimeoutException):
                pass
            await asyncio.sleep(1)
    
    return False


async def clear_cache(cache_client: httpx.AsyncClient) -> None:
    """Clear all cache entries for test isolation."""
    try:
        await cache_client.post("/api/v1/cache/clear")
    except Exception:
        pass  # Ignore if clear endpoint doesn't exist


# Test markers
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test against running services"
    )
    config.addinivalue_line(
        "markers", "requires_docker: mark test as requiring Docker containers"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )