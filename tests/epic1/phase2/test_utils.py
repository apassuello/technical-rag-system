"""Test utilities for Epic 1 Phase 2 testing.

Provides mock classes and helper functions for testing adapters.
"""

from typing import Optional, List
from dataclasses import dataclass


@dataclass
class MockGenerationParams:
    """Mock GenerationParams for testing when real one not available."""
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 100
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop_sequences: Optional[List[str]] = None


def get_generation_params(**kwargs) -> 'MockGenerationParams':
    """Get GenerationParams (mock if real not available)."""
    try:
        from src.components.generators.base import GenerationParams
        return GenerationParams(**kwargs)
    except ImportError:
        return MockGenerationParams(**kwargs)


# Test data constants
TEST_QUERIES = {
    'simple': "What is 2+2?",
    'medium': "How does OAuth 2.0 authentication work in web applications?",
    'complex': "Explain the transformer architecture and its attention mechanism, including mathematical formulations and computational complexity analysis."
}

TEST_CONTEXTS = {
    'simple': ["Basic arithmetic operations involve addition, subtraction, multiplication, and division."],
    'medium': ["OAuth 2.0 is an authorization framework that enables applications to obtain limited access to user accounts..."],
    'complex': ["The Transformer architecture revolutionized natural language processing by introducing the attention mechanism..."]
}

# Cost limits for different test types
COST_LIMITS = {
    'unit_test': 0.01,      # $0.01 per unit test
    'integration_test': 0.10, # $0.10 per integration test
    'performance_test': 0.50, # $0.50 per performance test
    'full_suite': 2.00      # $2.00 for full test suite
}

# Model configurations for testing
TEST_MODELS = {
    'openai': {
        'cheap': 'gpt-3.5-turbo',
        'expensive': 'gpt-4-turbo',
        'fastest': 'gpt-4o-mini'
    },
    'mistral': {
        'cheap': 'mistral-small',
        'medium': 'mistral-medium',
        'expensive': 'mistral-large'
    }
}