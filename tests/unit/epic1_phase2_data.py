"""Epic 1 Phase 2 test data constants.

Moved from tests/epic1/phase2/__init__.py during test reorganization.
Used by routing/cost tracking unit tests.
"""

from decimal import Decimal

PERFORMANCE_TARGETS = {
    "routing_latency_ms": 50,
    "cost_precision": "0.001",
    "end_to_end_latency_s": 2,
    "routing_accuracy_pct": 90,
}

REQUIRED_ENV_VARS = [
    "OPENAI_API_KEY",
    "MISTRAL_API_KEY",
]

TEST_DATA = {
    "simple_queries": [
        "What is Python?",
        "Define REST API",
        "List HTTP methods",
    ],
    "medium_queries": [
        "How does OAuth 2.0 authentication work?",
        "Explain microservices architecture benefits and drawbacks",
    ],
    "complex_queries": [
        "Explain the mathematical foundations of transformer architectures",
        "Compare distributed consensus algorithms in blockchain systems",
    ],
}

EXPECTED_ROUTING = {
    "cost_optimized": {
        "simple": {"provider": "ollama", "model": "llama3.2:3b"},
        "medium": {"provider": "mistral", "model": "mistral-small"},
        "complex": {"provider": "openai", "model": "gpt-3.5-turbo"},
    },
    "quality_first": {
        "simple": {"provider": "openai", "model": "gpt-3.5-turbo"},
        "medium": {"provider": "openai", "model": "gpt-4-turbo"},
        "complex": {"provider": "openai", "model": "gpt-4-turbo"},
    },
    "balanced": {
        "simple": {"provider": "ollama", "model": "llama3.2:3b"},
        "medium": {"provider": "mistral", "model": "mistral-small"},
        "complex": {"provider": "openai", "model": "gpt-4-turbo"},
    },
}

COST_VALIDATION = {
    "openai": {
        "gpt-3.5-turbo": {"input": "0.0010", "output": "0.0020"},
        "gpt-4-turbo": {"input": "0.0100", "output": "0.0300"},
    },
    "mistral": {
        "mistral-small": {"input": "0.0020", "output": "0.0060"},
        "mistral-medium": {"input": "0.0027", "output": "0.0081"},
    },
    "ollama": {
        "llama3.2:3b": {"input": "0.0000", "output": "0.0000"},
    },
}
