"""
Pytest configuration for Epic 8 API tests.
"""

import sys
import os
import signal
import subprocess
import time
import pytest
import asyncio
from pathlib import Path
from typing import Dict, List

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


# K8s service configuration
K8S_CONTEXT = "kind-epic8-testing"
K8S_NAMESPACE = "epic8-dev"
SERVICE_PORTS = {
    'api-gateway': 8080,
    'generator': 8081,
    'query-analyzer': 8082,
    'retriever': 8083,
    'cache': 8084,
    'analytics': 8085,
}


def pytest_collection_modifyitems(config, items):
    """
    Automatically skip tests marked with requires_docker if services are unavailable.

    This hook runs during test collection and checks if Epic 8 K8s services are
    healthy via HTTP. If not, it adds skip markers to all requires_docker tests.
    """
    if not HTTPX_AVAILABLE:
        skip_marker = pytest.mark.skip(reason="httpx not available")
        for item in items:
            if "requires_docker" in item.keywords:
                item.add_marker(skip_marker)
        return

    # HTTP health check on localhost services
    services_available = {}

    # Run sync health check
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def check_all_services():
        async with httpx.AsyncClient(timeout=2.0) as client:
            tasks = []
            for service_name, port in SERVICE_PORTS.items():
                tasks.append(_check_service(client, service_name, port))
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return dict(zip(SERVICE_PORTS.keys(), results))

    try:
        services_available = loop.run_until_complete(check_all_services())
    finally:
        loop.close()

    # Filter to only healthy services
    healthy_services = {name: avail for name, avail in services_available.items() if avail is True}

    # If not ALL services are available, skip requires_docker tests
    # (tests assume full service mesh — partial availability causes spurious failures)
    if len(healthy_services) < len(SERVICE_PORTS):
        skip_marker = pytest.mark.skip(
            reason=(
                "Epic 8 K8s services not available - no healthy services found on localhost:8080-8085\n"
                "   To start port-forwards, run: ./start_port_forwards.sh"
            )
        )
        for item in items:
            if "requires_docker" in item.keywords:
                item.add_marker(skip_marker)


async def _check_service(client: httpx.AsyncClient, service_name: str, port: int) -> bool:
    """Check if a service is healthy via HTTP."""
    try:
        # Try /health first (standard endpoint)
        response = await client.get(f"http://localhost:{port}/health")
        return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException, httpx.RemoteProtocolError):
        return False


@pytest.fixture
def reset_prometheus():
    """Reset Prometheus registry to avoid metric collision between tests.

    Not autouse — only request this in tests that register Prometheus metrics.
    """
    yield
    try:
        from prometheus_client import REGISTRY
        collectors = list(REGISTRY._collector_to_names.keys())
        for collector in collectors:
            try:
                REGISTRY.unregister(collector)
            except (KeyError, ValueError):
                pass
        REGISTRY._collector_to_names.clear()
        REGISTRY._names_to_collectors.clear()
    except ImportError:
        pass


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
