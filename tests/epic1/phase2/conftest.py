"""Test configuration and fixtures for Epic 1 Phase 2 tests.

Provides common fixtures, mock services, and test utilities for all
Epic 1 Phase 2 test modules.
"""

import os
import pytest
from decimal import Decimal
from unittest.mock import Mock, MagicMock
from typing import Dict, List, Any
import tempfile
import json

# Import test configuration
from . import (
    PERFORMANCE_TARGETS, TEST_DATA, EXPECTED_ROUTING, 
    COST_VALIDATION, REQUIRED_ENV_VARS
)


@pytest.fixture(scope="session")
def test_environment():
    """Set up test environment with required variables."""
    # Set test API keys if not provided
    for env_var in REQUIRED_ENV_VARS:
        if env_var not in os.environ:
            os.environ[env_var] = f"test-{env_var.lower().replace('_', '-')}-key"
    
    # Enable test mode
    os.environ['EPIC1_TEST_MODE'] = 'true'
    os.environ['EPIC1_USE_MOCKS'] = 'true'
    
    yield
    
    # Cleanup (keep original env vars, remove test ones)
    test_vars = ['EPIC1_TEST_MODE', 'EPIC1_USE_MOCKS']
    for var in test_vars:
        if var in os.environ:
            del os.environ[var]


@pytest.fixture
def test_queries():
    """Provide categorized test queries."""
    return TEST_DATA


@pytest.fixture 
def expected_routing():
    """Provide expected routing decisions for validation."""
    return EXPECTED_ROUTING


@pytest.fixture
def cost_validation_data():
    """Provide cost validation data."""
    return COST_VALIDATION


@pytest.fixture
def performance_targets():
    """Provide performance targets for validation."""
    return PERFORMANCE_TARGETS


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = MagicMock()
    
    # Standard response for testing
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(
        message=MagicMock(content="This is a test response from OpenAI.")
    )]
    mock_response.usage = MagicMock(
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150
    )
    
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_mistral_response():
    """Mock Mistral API response for testing."""
    return {
        'choices': [{
            'message': {
                'content': 'This is a test response from Mistral.'
            }
        }],
        'usage': {
            'prompt_tokens': 80,
            'completion_tokens': 40,
            'total_tokens': 120
        }
    }


@pytest.fixture
def mock_query_analyzer():
    """Mock Epic1QueryAnalyzer for testing."""
    analyzer = MagicMock()
    
    def analyze_query(query, **kwargs):
        """Mock analysis based on query content."""
        query_lower = query.lower()
        
        # Simple complexity detection
        if len(query.split()) <= 4 or any(word in query_lower for word in ['what', 'define', 'list']):
            complexity = "simple"
            score = 0.25
        elif len(query.split()) <= 10 or any(word in query_lower for word in ['how', 'explain']):
            complexity = "medium" 
            score = 0.55
        else:
            complexity = "complex"
            score = 0.85
        
        return {
            "complexity_level": complexity,
            "complexity_score": score,
            "confidence": 0.90,
            "recommended_model": EXPECTED_ROUTING["balanced"][complexity],
            "features": {
                "technical_terms": len([w for w in query_lower.split() if w in ['api', 'oauth', 'transformer', 'algorithm']]),
                "clause_count": query.count(',') + 1,
                "word_count": len(query.split())
            }
        }
    
    analyzer.analyze.side_effect = analyze_query
    return analyzer


@pytest.fixture
def model_options():
    """Provide model options for testing routing strategies."""
    from src.components.generators.routing.routing_strategies import ModelOption
    
    return {
        "simple": [
            ModelOption("ollama", "llama3.2:3b", Decimal('0.000'), 1.5, 0.75),
            ModelOption("openai", "gpt-3.5-turbo", Decimal('0.002'), 0.8, 0.90)
        ],
        "medium": [
            ModelOption("mistral", "mistral-small", Decimal('0.010'), 1.2, 0.85),
            ModelOption("openai", "gpt-4-turbo", Decimal('0.050'), 2.0, 0.95)
        ],
        "complex": [
            ModelOption("openai", "gpt-3.5-turbo", Decimal('0.020'), 1.5, 0.85),
            ModelOption("openai", "gpt-4-turbo", Decimal('0.100'), 3.0, 0.98)
        ]
    }


@pytest.fixture
def temp_export_file():
    """Provide temporary file for export testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except OSError:
        pass


@pytest.fixture
def sample_usage_records():
    """Provide sample usage records for cost tracking tests."""
    from datetime import datetime, timedelta
    
    base_time = datetime.now()
    
    return [
        {
            "provider": "openai",
            "model": "gpt-4-turbo",
            "input_tokens": 200,
            "output_tokens": 100,
            "cost_usd": Decimal('0.005000'),
            "query_complexity": "complex",
            "timestamp": base_time - timedelta(hours=1)
        },
        {
            "provider": "mistral",
            "model": "mistral-small", 
            "input_tokens": 150,
            "output_tokens": 75,
            "cost_usd": Decimal('0.000750'),
            "query_complexity": "medium",
            "timestamp": base_time - timedelta(minutes=30)
        },
        {
            "provider": "ollama",
            "model": "llama3.2:3b",
            "input_tokens": 100,
            "output_tokens": 50,
            "cost_usd": Decimal('0.000000'),
            "query_complexity": "simple",
            "timestamp": base_time
        }
    ]


@pytest.fixture
def epic1_config():
    """Provide Epic1 multi-model configuration."""
    return {
        "query_analyzer": {
            "type": "epic1"
        },
        "routing": {
            "strategy": "balanced",
            "cost_weight": 0.4,
            "quality_weight": 0.6
        },
        "model_mappings": {
            "simple": {"provider": "ollama", "model": "llama3.2:3b"},
            "medium": {"provider": "mistral", "model": "mistral-small"},
            "complex": {"provider": "openai", "model": "gpt-4-turbo"}
        },
        "cost_tracking": {
            "enabled": True,
            "daily_budget": 10.00,
            "warning_threshold": 0.80
        }
    }


@pytest.fixture
def legacy_config():
    """Provide legacy single-model configuration."""
    return {
        "llm_client": {
            "type": "ollama",
            "config": {
                "model_name": "llama3.2:3b",
                "temperature": 0.7
            }
        }
    }


# Performance testing utilities
class PerformanceTimer:
    """Context manager for measuring performance."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.duration_ms = None
    
    def __enter__(self):
        import time
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        self.end_time = time.perf_counter()
        self.duration_ms = (self.end_time - self.start_time) * 1000


@pytest.fixture
def performance_timer():
    """Provide performance timer for testing."""
    return PerformanceTimer


# Test data validation utilities
def validate_cost_precision(cost_value, precision_places=6):
    """Validate cost precision meets requirements."""
    if not isinstance(cost_value, Decimal):
        return False
    
    # Check decimal places
    decimal_str = str(cost_value)
    if '.' in decimal_str:
        decimal_places = len(decimal_str.split('.')[1])
        return decimal_places <= precision_places
    
    return True


def validate_routing_decision(decision, expected_provider, expected_model):
    """Validate routing decision matches expectations."""
    if not hasattr(decision, 'selected_model'):
        return False
    
    model = decision.selected_model
    return (model.provider == expected_provider and 
            model.model == expected_model)


def validate_performance_target(actual_ms, target_ms, tolerance_factor=1.5):
    """Validate performance meets target with tolerance."""
    return actual_ms <= target_ms * tolerance_factor


# Export validation utilities
@pytest.fixture
def test_utilities():
    """Provide test utility functions."""
    return {
        'validate_cost_precision': validate_cost_precision,
        'validate_routing_decision': validate_routing_decision,
        'validate_performance_target': validate_performance_target
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest for Epic 1 Phase 2 tests."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "critical: marks tests as critical for Phase 2"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection for better organization."""
    for item in items:
        # Add integration marker to integration tests
        if "integration" in item.nodeid or "end_to_end" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add performance marker to performance tests
        if "performance" in item.nodeid or "latency" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        
        # Add critical marker to critical tests
        if any(word in item.name.lower() for word in ['critical', 'basic', 'initialization']):
            item.add_marker(pytest.mark.critical)