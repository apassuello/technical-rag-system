"""
Pytest configuration for Epic 8 API tests.
"""

import sys
import pytest
import asyncio
from pathlib import Path


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
