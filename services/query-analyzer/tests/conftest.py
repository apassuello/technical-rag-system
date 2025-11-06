"""
Pytest fixtures and configuration for Query Analyzer Service tests.
"""

import pytest
import asyncio
from typing import Dict, Any, AsyncGenerator
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient
import httpx
import tempfile
import yaml
from pathlib import Path

# Import service components
import sys
service_root = Path(__file__).parent.parent
sys.path.insert(0, str(service_root))

from analyzer_app.main import create_app, get_analyzer_service
from analyzer_app.core.analyzer import QueryAnalyzerService
from analyzer_app.core.config import ServiceSettings, AnalyzerConfig, get_settings
from analyzer_app.schemas.responses import AnalyzeResponse


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_epic1_analyzer():
    """Mock Epic1QueryAnalyzer for testing."""
    mock_analyzer = Mock()
    
    # Mock QueryAnalysis result
    mock_analysis = Mock()
    mock_analysis.metadata = {
        'complexity': 'medium',
        'confidence': 0.85,
        'features': {
            'length': 25,
            'vocabulary_complexity': 0.6,
            'syntax_complexity': 0.7,
            'semantic_complexity': 0.5
        },
        'recommended_models': ['openai/gpt-3.5-turbo', 'ollama/llama3.2:3b'],
        'cost_estimate': {
            'openai/gpt-3.5-turbo': 0.002,
            'ollama/llama3.2:3b': 0.0
        },
        'routing_strategy': 'balanced'
    }
    
    mock_analyzer.analyze_query.return_value = mock_analysis
    mock_analyzer._analysis_times = {
        'feature_extraction': [0.01, 0.012, 0.009],
        'complexity_classification': [0.005, 0.006, 0.004],
        'model_recommendation': [0.003, 0.004, 0.002],
        'total': [0.018, 0.022, 0.015]
    }
    mock_analyzer.model_recommender.strategy = 'balanced'
    
    return mock_analyzer


@pytest.fixture
def analyzer_config():
    """Test configuration for analyzer."""
    return {
        "feature_extractor": {
            "enable_caching": True,
            "cache_size": 100,
            "extract_linguistic": True,
            "extract_structural": True,
            "extract_semantic": True
        },
        "complexity_classifier": {
            "thresholds": {
                "simple": 0.3,
                "medium": 0.6,
                "complex": 0.9
            },
            "weights": {
                "length": 0.2,
                "vocabulary": 0.3,
                "syntax": 0.2,
                "semantic": 0.3
            }
        },
        "model_recommender": {
            "strategy": "balanced",
            "model_mappings": {
                "simple": ["ollama/llama3.2:3b"],
                "medium": ["openai/gpt-3.5-turbo"],
                "complex": ["openai/gpt-4"]
            },
            "cost_weights": {
                "ollama/llama3.2:3b": 0.0,
                "openai/gpt-3.5-turbo": 0.002,
                "openai/gpt-4": 0.06
            }
        }
    }


@pytest.fixture
def service_settings():
    """Test service settings."""
    return ServiceSettings(
        service_name="query-analyzer-test",
        host="127.0.0.1",
        port=8081,
        log_level="DEBUG",
        analyzer_config=AnalyzerConfig()
    )


@pytest.fixture
async def analyzer_service(mock_epic1_analyzer, analyzer_config):
    """Create QueryAnalyzerService instance for testing."""
    with patch('app.core.analyzer.Epic1QueryAnalyzer', return_value=mock_epic1_analyzer):
        service = QueryAnalyzerService(config=analyzer_config)
        await service._initialize_analyzer()
        yield service
        await service.shutdown()


@pytest.fixture
def mock_analyzer_service(analyzer_service):
    """Mock analyzer service for dependency injection."""
    return analyzer_service


@pytest.fixture
def app(mock_analyzer_service):
    """Create FastAPI test app."""
    app = create_app()
    
    # Override dependency
    app.dependency_overrides[get_analyzer_service] = lambda: mock_analyzer_service
    
    return app


@pytest.fixture
def client(app):
    """HTTP test client."""
    return TestClient(app)


@pytest.fixture
async def async_client(app):
    """Async HTTP test client."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def temp_config_file():
    """Create temporary configuration file."""
    config_data = {
        "service_name": "query-analyzer-test",
        "port": 8081,
        "log_level": "DEBUG",
        "analyzer": {
            "feature_extractor": {
                "enable_caching": True,
                "cache_size": 500
            },
            "complexity_classifier": {
                "thresholds": {
                    "simple": 0.25,
                    "medium": 0.65,
                    "complex": 0.85
                }
            },
            "model_recommender": {
                "strategy": "cost_optimized"
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        yield Path(f.name)
    
    Path(f.name).unlink()  # Clean up


@pytest.fixture
def sample_queries():
    """Sample queries for testing."""
    return {
        "simple": [
            "What is Python?",
            "Hello world",
            "How are you?",
            "What time is it?"
        ],
        "medium": [
            "How do I implement a binary search algorithm in Python with error handling?",
            "Explain the differences between REST and GraphQL APIs",
            "What are the best practices for database indexing?",
            "How does machine learning gradient descent work?"
        ],
        "complex": [
            "Design a distributed system architecture for real-time analytics with fault tolerance, load balancing, and automatic scaling capabilities including data persistence strategies",
            "Implement a comprehensive microservices architecture with service discovery, circuit breakers, event sourcing, and CQRS patterns while ensuring ACID properties",
            "Develop a multi-tenant SaaS platform with advanced security features, role-based access control, audit logging, and compliance with GDPR and HIPAA regulations"
        ]
    }


@pytest.fixture
def expected_response_structure():
    """Expected structure of analyze response."""
    return {
        "query": str,
        "complexity": str,
        "confidence": float,
        "features": dict,
        "recommended_models": list,
        "cost_estimate": dict,
        "routing_strategy": str,
        "processing_time": float,
        "metadata": dict
    }


@pytest.fixture
def performance_targets():
    """Performance targets for testing."""
    return {
        "max_response_time": 0.05,  # 50ms
        "min_confidence": 0.0,
        "max_confidence": 1.0,
        "valid_complexities": ["simple", "medium", "complex"],
        "expected_models": [
            "ollama/llama3.2:3b",
            "openai/gpt-3.5-turbo", 
            "openai/gpt-4",
            "mistral/mistral-large"
        ]
    }


# Async test utilities
class AsyncContextManager:
    """Utility for async context management in tests."""
    
    def __init__(self, obj):
        self.obj = obj
    
    async def __aenter__(self):
        return self.obj
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_metrics():
    """Mock Prometheus metrics for testing."""
    with patch('app.core.analyzer.ANALYSIS_REQUESTS'), \
         patch('app.core.analyzer.ANALYSIS_DURATION'), \
         patch('app.core.analyzer.COMPLEXITY_DISTRIBUTION'), \
         patch('app.core.analyzer.COMPONENT_HEALTH'), \
         patch('app.api.rest.API_REQUESTS'), \
         patch('app.api.rest.API_REQUEST_DURATION'):
        yield


# Helper functions for tests
def validate_response_structure(response_data: dict, expected_structure: dict):
    """Validate that response matches expected structure."""
    for key, expected_type in expected_structure.items():
        assert key in response_data, f"Missing key: {key}"
        assert isinstance(response_data[key], expected_type), \
            f"Key {key} should be {expected_type}, got {type(response_data[key])}"


def assert_valid_complexity(complexity: str, valid_complexities: list):
    """Assert complexity is valid."""
    assert complexity in valid_complexities, \
        f"Invalid complexity: {complexity}. Must be one of {valid_complexities}"


def assert_confidence_range(confidence: float, min_val: float = 0.0, max_val: float = 1.0):
    """Assert confidence is in valid range."""
    assert min_val <= confidence <= max_val, \
        f"Confidence {confidence} not in range [{min_val}, {max_val}]"


def assert_processing_time(processing_time: float, max_time: float):
    """Assert processing time meets performance target."""
    assert processing_time <= max_time, \
        f"Processing time {processing_time}s exceeds target {max_time}s"