"""Epic 1 Phase 2 Test Suite.

Comprehensive test suite for Epic 1 Phase 2 multi-model adapters including:
- OpenAI and Mistral LLM adapters
- Cost tracking system with $0.001 precision
- Routing strategies (cost_optimized, quality_first, balanced)
- Adaptive router with <50ms routing overhead
- Epic1AnswerGenerator integration
- End-to-end multi-model workflows

Test Execution:
    python run_epic1_phase2_tests.py              # Run full suite
    python run_epic1_phase2_tests.py --module test_openai_adapter  # Single module
    pytest test_openai_adapter.py -v              # Direct pytest

Test Coverage:
    - 50+ test cases with explicit PASS/FAIL criteria
    - Performance benchmarks (<50ms routing, $0.001 cost precision)
    - Integration and backward compatibility tests
    - Comprehensive error handling and edge cases
"""

# Test suite metadata
__version__ = "1.0.0"
__epic__ = "Epic 1 Phase 2"
__components__ = [
    "OpenAI Adapter",
    "Mistral Adapter", 
    "Cost Tracker",
    "Routing Strategies",
    "Adaptive Router",
    "Epic1AnswerGenerator"
]

# Test execution configuration
DEFAULT_TIMEOUT = 300  # 5 minutes per test module
PERFORMANCE_TARGETS = {
    "routing_latency_ms": 50,
    "cost_precision": "0.001",
    "end_to_end_latency_s": 2,
    "routing_accuracy_pct": 90
}

# Required environment for testing
REQUIRED_ENV_VARS = [
    "OPENAI_API_KEY",   # For OpenAI adapter testing (can use test key)
    "MISTRAL_API_KEY",  # For Mistral adapter testing (can use test key)
]

OPTIONAL_ENV_VARS = [
    "EPIC1_TEST_MODE",    # Enable test mode with mocks
    "EPIC1_USE_MOCKS",    # Force use of mock services
]

# Test data specifications
TEST_DATA = {
    "simple_queries": [
        "What is Python?",
        "Define REST API", 
        "List HTTP methods"
    ],
    "medium_queries": [
        "How does OAuth 2.0 authentication work?",
        "Explain microservices architecture benefits and drawbacks"
    ],
    "complex_queries": [
        "Explain the mathematical foundations of transformer architectures",
        "Compare distributed consensus algorithms in blockchain systems"
    ]
}

# Expected routing decisions for validation
EXPECTED_ROUTING = {
    "cost_optimized": {
        "simple": {"provider": "ollama", "model": "llama3.2:3b"},
        "medium": {"provider": "mistral", "model": "mistral-small"},
        "complex": {"provider": "openai", "model": "gpt-3.5-turbo"}
    },
    "quality_first": {
        "simple": {"provider": "openai", "model": "gpt-3.5-turbo"},
        "medium": {"provider": "openai", "model": "gpt-4-turbo"},
        "complex": {"provider": "openai", "model": "gpt-4-turbo"}
    },
    "balanced": {
        "simple": {"provider": "ollama", "model": "llama3.2:3b"},
        "medium": {"provider": "mistral", "model": "mistral-small"},
        "complex": {"provider": "openai", "model": "gpt-4-turbo"}
    }
}

# Cost validation data
COST_VALIDATION = {
    "openai": {
        "gpt-3.5-turbo": {"input": "0.0010", "output": "0.0020"},
        "gpt-4-turbo": {"input": "0.0100", "output": "0.0300"}
    },
    "mistral": {
        "mistral-small": {"input": "0.0020", "output": "0.0060"},
        "mistral-medium": {"input": "0.0027", "output": "0.0081"}
    },
    "ollama": {
        "llama3.2:3b": {"input": "0.0000", "output": "0.0000"}
    }
}