"""
Test configuration and fixtures for API Gateway Service.

Comprehensive fixtures for unit, API, integration, and performance testing.
Based on Epic 8 test specifications and patterns.
"""

import pytest
import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock
from fastapi.testclient import TestClient
import httpx

from app.main import app, gateway_service
from app.core.config import APIGatewaySettings
from app.core.gateway import APIGatewayService, SimpleCircuitBreaker
from app.schemas.requests import UnifiedQueryRequest, BatchQueryRequest, QueryOptions
from app.schemas.responses import (
    UnifiedQueryResponse, BatchQueryResponse, BatchQueryResult,
    ProcessingMetrics, CostBreakdown, DocumentSource, GatewayStatusResponse,
    ServiceStatus, AvailableModelsResponse, ModelInfo
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Test configuration settings."""
    return APIGatewaySettings(
        # Use localhost for testing
        query_analyzer_host="localhost",
        query_analyzer_port=8082,
        generator_host="localhost",
        generator_port=8081,
        retriever_host="localhost",
        retriever_port=8083,
        cache_host="localhost",
        cache_port=8084,
        analytics_host="localhost",
        analytics_port=8085,
        
        # Test-specific settings
        max_query_length=1000,
        max_batch_size=10,
        default_timeout=5,
        max_retries=1,
        
        # Allow all origins for testing
        allowed_origins=["*"],
        
        # Disable API key requirement for testing
        valid_api_keys=[]
    )


@pytest.fixture
def mock_query_analyzer_client():
    """Mock Query Analyzer client."""
    mock = AsyncMock()
    mock.analyze_query.return_value = {
        "complexity": "medium",
        "confidence": 0.85,
        "recommended_models": ["ollama/llama3.2:3b"],
        "cost_estimate": {"ollama/llama3.2:3b": 0.0},
        "routing_strategy": "balanced",
        "processing_time": 0.1
    }
    mock.health_check.return_value = True
    mock.get_status.return_value = {"status": "healthy"}
    mock.endpoint.url = "http://localhost:8082/api/v1"
    return mock


@pytest.fixture
def mock_generator_client():
    """Mock Generator client."""
    mock = AsyncMock()
    mock.generate_answer.return_value = {
        "answer": "This is a test answer.",
        "model_used": "ollama/llama3.2:3b",
        "cost": 0.0,
        "processing_time": 0.5,
        "confidence": 0.9,
        "input_tokens": 100,
        "output_tokens": 20
    }
    mock.get_available_models.return_value = {
        "models": [
            {
                "name": "llama3.2:3b",
                "provider": "ollama",
                "type": "chat",
                "available": True,
                "cost_per_token": 0.0
            }
        ]
    }
    mock.health_check.return_value = True
    mock.endpoint.url = "http://localhost:8081/api/v1"
    return mock


@pytest.fixture
def mock_retriever_client():
    """Mock Retriever client."""
    mock = AsyncMock()
    mock.retrieve_documents.return_value = [
        {
            "id": "doc1",
            "title": "Test Document",
            "content": "This is test content.",
            "score": 0.95,
            "metadata": {"source": "test"}
        }
    ]
    mock.health_check.return_value = True
    mock.endpoint.url = "http://localhost:8083/api/v1"
    return mock


@pytest.fixture
def mock_cache_client():
    """Mock Cache client."""
    mock = AsyncMock()
    mock.get_cached_response.return_value = None  # No cache hit by default
    mock.cache_response.return_value = True
    mock.get_cache_statistics.return_value = {
        "hit_rate": 0.6,
        "total_keys": 100,
        "memory_usage": "10MB"
    }
    mock.health_check.return_value = True
    mock.endpoint.url = "http://localhost:8084/api/v1"
    return mock


@pytest.fixture
def mock_analytics_client():
    """Mock Analytics client."""
    mock = AsyncMock()
    mock.record_cache_hit.return_value = True
    mock.record_query_completion.return_value = True
    mock.record_error.return_value = True
    mock.health_check.return_value = True
    mock.endpoint.url = "http://localhost:8085/api/v1"
    return mock


@pytest.fixture
async def mock_gateway_service(
    test_settings,
    mock_query_analyzer_client,
    mock_generator_client,
    mock_retriever_client,
    mock_cache_client,
    mock_analytics_client
):
    """Mock Gateway service with all clients."""
    service = APIGatewayService(test_settings)
    
    # Replace clients with mocks
    service.query_analyzer = mock_query_analyzer_client
    service.generator = mock_generator_client
    service.retriever = mock_retriever_client
    service.cache = mock_cache_client
    service.analytics = mock_analytics_client
    
    # Mock circuit breakers
    service.circuit_breakers = {
        "query-analyzer": MagicMock(),
        "generator": MagicMock(),
        "retriever": MagicMock(),
        "cache": MagicMock(),
        "analytics": MagicMock()
    }
    
    # Configure circuit breaker mocks to act as pass-through
    for cb in service.circuit_breakers.values():
        cb.__enter__ = MagicMock(return_value=cb)
        cb.__exit__ = MagicMock(return_value=None)
    
    return service


@pytest.fixture
def client():
    """Test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_query_request():
    """Sample query request for testing."""
    return {
        "query": "What is machine learning?",
        "context": {"domain": "AI"},
        "options": {
            "strategy": "balanced",
            "max_documents": 5,
            "cache_enabled": True,
            "analytics_enabled": True
        },
        "session_id": "test-session-123",
        "user_id": "test-user-456"
    }


@pytest.fixture
def sample_batch_request():
    """Sample batch request for testing."""
    return {
        "queries": [
            "What is machine learning?",
            "How does deep learning work?",
            "What are neural networks?"
        ],
        "context": {"domain": "AI"},
        "options": {
            "strategy": "balanced",
            "max_documents": 5
        },
        "session_id": "test-session-123",
        "parallel_processing": True,
        "max_parallel": 3
    }


# ============================================================================
# EPIC 8 COMPREHENSIVE TEST FIXTURES
# ============================================================================

@pytest.fixture
def epic8_test_settings():
    """Epic 8 test configuration settings with circuit breakers."""
    return APIGatewaySettings(
        service_name="api-gateway-test",
        host="127.0.0.1",
        port=8080,
        log_level="DEBUG",
        
        # Service endpoints for Epic 8
        query_analyzer_host="localhost",
        query_analyzer_port=8081,
        generator_host="localhost", 
        generator_port=8082,
        retriever_host="localhost",
        retriever_port=8083,
        cache_host="localhost",
        cache_port=8084,
        analytics_host="localhost",
        analytics_port=8085,
        
        # Circuit breaker settings
        circuit_breaker_failure_threshold=3,
        circuit_breaker_recovery_timeout=5,
        
        # Performance settings
        max_query_length=10000,
        max_batch_size=100,
        default_timeout=30,
        max_retries=2,
        
        # Security settings (relaxed for testing)
        allowed_origins=["*"],
        valid_api_keys=[]
    )


@pytest.fixture
def realistic_query_analyzer_client():
    """Realistic mock Query Analyzer client with Epic 1 integration."""
    client = AsyncMock()
    
    # Realistic analysis responses based on Epic 1
    client.analyze_query.return_value = {
        "query": "How does machine learning work?",
        "complexity": "medium",
        "confidence": 0.87,
        "features": {
            "word_count": 6,
            "technical_density": 0.5,
            "syntactic_complexity": 0.3,
            "question_type": "how",
            "ambiguity_score": 0.2,
            "technical_terms": ["machine", "learning"]
        },
        "recommended_models": [
            {
                "provider": "openai",
                "name": "gpt-3.5-turbo", 
                "confidence": 0.9,
                "reasoning": "Medium complexity suitable for GPT-3.5"
            },
            {
                "provider": "ollama",
                "name": "llama3.2:3b",
                "confidence": 0.7,
                "reasoning": "Cost-effective option for medium queries"
            }
        ],
        "cost_estimate": {
            "openai/gpt-3.5-turbo": 0.002,
            "ollama/llama3.2:3b": 0.0
        },
        "routing_strategy": "balanced",
        "processing_time": 0.045,
        "metadata": {
            "analyzer_version": "1.0.0",
            "model_used": "epic1-analyzer"
        }
    }
    
    client.health_check.return_value = True
    client.endpoint.url = "http://query-analyzer:8081"
    client.close.return_value = None
    
    return client


@pytest.fixture
def realistic_generator_client():
    """Realistic mock Generator client with multi-model support."""
    client = AsyncMock()
    
    # Realistic generation responses
    client.generate_answer.return_value = {
        "answer": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from data without explicit programming. It uses algorithms to identify patterns in data and make predictions or decisions.",
        "confidence": 0.92,
        "model_used": "openai/gpt-3.5-turbo",
        "input_tokens": 150,
        "output_tokens": 45,
        "cost": 0.0025,
        "tokens_generated": 45,
        "processing_time": 0.823,
        "metadata": {
            "temperature": 0.7,
            "max_tokens": 1000,
            "prompt_template": "epic1-standard"
        }
    }
    
    # Available models response
    client.get_available_models.return_value = {
        "models": [
            {
                "provider": "openai",
                "name": "gpt-3.5-turbo",
                "available": True,
                "context_length": 4096,
                "input_cost": 0.0015,
                "output_cost": 0.002,
                "model_type": "chat",
                "description": "Fast and efficient for most tasks"
            },
            {
                "provider": "openai",
                "name": "gpt-4",
                "available": True, 
                "context_length": 8192,
                "input_cost": 0.03,
                "output_cost": 0.06,
                "model_type": "chat",
                "description": "Most capable model for complex tasks"
            },
            {
                "provider": "ollama",
                "name": "llama3.2:3b",
                "available": True,
                "context_length": 2048,
                "input_cost": 0.0,
                "output_cost": 0.0,
                "model_type": "chat",
                "description": "Free local model for basic tasks"
            }
        ]
    }
    
    client.health_check.return_value = True
    client.endpoint.url = "http://generator:8082"
    client.close.return_value = None
    
    return client


@pytest.fixture
def realistic_retriever_client():
    """Realistic mock Retriever client with Epic 2 ModularUnifiedRetriever."""
    client = AsyncMock()
    
    # Realistic document retrieval responses
    client.retrieve_documents.return_value = [
        {
            "id": "doc_001",
            "title": "Machine Learning Fundamentals",
            "content": "Machine learning is a branch of artificial intelligence that focuses on algorithms that can learn from and make predictions on data. It encompasses supervised learning, unsupervised learning, and reinforcement learning approaches.",
            "score": 0.94,
            "metadata": {
                "source": "ml_handbook.pdf",
                "page": 15,
                "section": "Introduction",
                "last_modified": "2024-01-15",
                "document_type": "technical_documentation"
            }
        },
        {
            "id": "doc_002", 
            "title": "Deep Learning Neural Networks",
            "content": "Deep learning uses neural networks with multiple layers to model and understand complex patterns in data. These networks can automatically learn feature representations from raw data.",
            "score": 0.89,
            "metadata": {
                "source": "dl_guide.pdf",
                "page": 8,
                "section": "Neural Networks", 
                "last_modified": "2024-02-01",
                "document_type": "tutorial"
            }
        },
        {
            "id": "doc_003",
            "title": "AI Applications in Industry",
            "content": "Artificial intelligence applications span across various industries including healthcare for diagnosis, finance for fraud detection, and autonomous vehicles for navigation systems.",
            "score": 0.76,
            "metadata": {
                "source": "ai_applications.pdf",
                "page": 23,
                "section": "Industry Use Cases",
                "last_modified": "2024-01-30",
                "document_type": "case_study"
            }
        }
    ]
    
    client.health_check.return_value = True
    client.endpoint.url = "http://retriever:8083"
    client.close.return_value = None
    
    return client


@pytest.fixture
def realistic_cache_client():
    """Realistic mock Cache client with Redis-like behavior."""
    client = AsyncMock()
    
    # Cache operations
    client.get_cached_response.return_value = None  # No cache hit by default
    client.cache_response.return_value = True
    client.clear_cache.return_value = {"keys_removed": 10, "pattern": "*"}
    
    # Cache statistics
    client.get_cache_statistics.return_value = {
        "hit_rate": 0.68,
        "total_keys": 250,
        "total_hits": 170,
        "total_misses": 80,
        "memory_usage": "45MB",
        "uptime": 7200,
        "evicted_keys": 15,
        "expired_keys": 5
    }
    
    client.health_check.return_value = True
    client.endpoint.url = "http://cache:8084"
    client.close.return_value = None
    
    return client


@pytest.fixture
def realistic_analytics_client():
    """Realistic mock Analytics client for tracking and monitoring."""
    client = AsyncMock()
    
    # Analytics operations
    client.record_cache_hit.return_value = True
    client.record_query_completion.return_value = True
    client.record_error.return_value = True
    client.record_batch_completion.return_value = True
    
    # Analytics data
    client.get_analytics_summary.return_value = {
        "total_queries": 1250,
        "successful_queries": 1187,
        "failed_queries": 63,
        "cache_hit_rate": 0.62,
        "average_response_time": 1.34,
        "cost_per_query": 0.0018,
        "popular_models": ["openai/gpt-3.5-turbo", "ollama/llama3.2:3b"],
        "error_types": {"timeout": 25, "service_unavailable": 18, "validation": 20}
    }
    
    client.health_check.return_value = True
    client.endpoint.url = "http://analytics:8085"
    client.close.return_value = None
    
    return client


@pytest.fixture
async def comprehensive_gateway_service(
    epic8_test_settings,
    realistic_query_analyzer_client,
    realistic_generator_client,
    realistic_retriever_client,
    realistic_cache_client,
    realistic_analytics_client
):
    """Comprehensive gateway service with all realistic clients."""
    gateway = APIGatewayService(epic8_test_settings)
    
    # Inject realistic clients
    gateway.query_analyzer = realistic_query_analyzer_client
    gateway.generator = realistic_generator_client
    gateway.retriever = realistic_retriever_client
    gateway.cache = realistic_cache_client
    gateway.analytics = realistic_analytics_client
    
    # Initialize circuit breakers
    gateway._initialize_circuit_breakers()
    
    return gateway


@pytest.fixture
def fast_performance_gateway():
    """Gateway optimized for performance testing with minimal delays."""
    gateway = APIGatewayService()
    
    # Fast mock services for performance testing
    for service_name in ["query_analyzer", "retriever", "generator", "cache", "analytics"]:
        client = AsyncMock()
        setattr(gateway, service_name, client)
    
    # Configure fast responses
    gateway.query_analyzer.analyze_query.return_value = {
        "complexity": "simple", "confidence": 0.8, "recommended_models": ["test-model"],
        "cost_estimate": {"test-model": 0.001}
    }
    gateway.retriever.retrieve_documents.return_value = [
        {"id": "fast_doc", "title": "Fast", "content": "Fast content", "score": 0.9, "metadata": {}}
    ]
    gateway.generator.generate_answer.return_value = {
        "answer": "Fast answer", "confidence": 0.9, "cost": 0.001, "tokens_generated": 10
    }
    gateway.cache.get_cached_response.return_value = None
    gateway.cache.cache_response.return_value = True
    gateway.analytics.record_query_completion.return_value = True
    
    # Health checks
    for client in [gateway.query_analyzer, gateway.retriever, gateway.generator, gateway.cache, gateway.analytics]:
        client.health_check.return_value = True
        client.endpoint.url = "http://fast-service:8080"
        client.close.return_value = None
    
    gateway._initialize_circuit_breakers()
    
    return gateway


@pytest.fixture
def failing_services_gateway():
    """Gateway with failing services for resilience testing."""
    gateway = APIGatewayService()
    
    # Create failing services
    for service_name in ["query_analyzer", "retriever", "generator", "cache", "analytics"]:
        client = AsyncMock()
        # Make all service calls fail
        for method in ["analyze_query", "retrieve_documents", "generate_answer", 
                      "get_cached_response", "cache_response", "record_query_completion"]:
            if hasattr(client, method):
                setattr(getattr(client, method), "side_effect", Exception(f"{service_name} unavailable"))
        
        client.health_check.return_value = False
        client.endpoint.url = f"http://failing-{service_name}:8080"
        client.close.return_value = None
        setattr(gateway, service_name, client)
    
    gateway._initialize_circuit_breakers()
    
    return gateway


@pytest.fixture
def sample_test_queries():
    """Sample queries for testing with various complexities."""
    return {
        "simple": [
            "Hi",
            "What is Python?",
            "Yes or no?",
            "Thanks"
        ],
        "medium": [
            "How does machine learning work?",
            "Explain neural networks and their applications",
            "What are the differences between supervised and unsupervised learning?",
            "How do I implement a REST API in Python?"
        ],
        "complex": [
            "Design a distributed microservices architecture for a high-traffic e-commerce platform with real-time analytics, fault tolerance, and automatic scaling capabilities",
            "Implement a comprehensive machine learning pipeline with feature engineering, model selection, hyperparameter tuning, and deployment automation for production environments",
            "Create a multi-tenant SaaS platform with advanced security, role-based access control, audit logging, and compliance with GDPR, HIPAA, and SOX regulations"
        ]
    }


@pytest.fixture
def performance_test_data():
    """Data for performance testing scenarios."""
    return {
        "response_time_targets": {
            "single_query_avg": 2.0,      # seconds
            "single_query_p95": 5.0,      # seconds
            "batch_query_per_item": 3.0,  # seconds per query in batch
            "concurrent_degradation": 1.5  # max degradation factor
        },
        "throughput_targets": {
            "min_queries_per_second": 1.0,
            "concurrent_success_rate": 0.9,
            "sustained_load_success_rate": 0.95
        },
        "resource_limits": {
            "max_memory_mb": 8000,
            "max_response_time_s": 60,
            "circuit_breaker_overhead_percent": 50
        }
    }


@pytest.fixture
async def async_test_client():
    """Async test client for API testing."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def epic8_test_requests():
    """Pre-built test requests for Epic 8 testing."""
    return {
        "simple_query": UnifiedQueryRequest(
            query="What is AI?",
            options=QueryOptions(strategy="balanced", cache_enabled=True)
        ),
        "complex_query": UnifiedQueryRequest(
            query="Explain the mathematical foundations of transformer attention mechanisms and their computational complexity implications for large language models",
            options=QueryOptions(
                strategy="quality_optimized", 
                max_documents=10,
                max_cost=0.10,
                complexity_hint="complex"
            ),
            context="Technical deep-dive research",
            session_id="complex-session",
            user_id="researcher"
        ),
        "batch_request": BatchQueryRequest(
            queries=["What is ML?", "How do neural networks work?", "Explain deep learning"],
            options=QueryOptions(strategy="cost_optimized", cache_enabled=True),
            parallel_processing=True,
            max_parallel=3,
            session_id="batch-session"
        )
    }


@pytest.fixture 
def circuit_breaker_test_scenarios():
    """Test scenarios for circuit breaker behavior."""
    return {
        "normal_operation": {
            "failure_rate": 0.0,
            "expected_state": "closed"
        },
        "intermittent_failures": {
            "failure_rate": 0.3,  # 30% failure rate
            "expected_state": "closed"  # Should stay closed
        },
        "high_failure_rate": {
            "failure_rate": 0.8,  # 80% failure rate
            "expected_state": "open"   # Should open
        },
        "recovery_scenario": {
            "initial_failures": 5,
            "recovery_delay": 1.0,
            "expected_final_state": "closed"
        }
    }


# Helper functions for test data generation
def generate_test_documents(count: int = 5) -> List[Dict[str, Any]]:
    """Generate test documents for retrieval testing."""
    return [
        {
            "id": f"test_doc_{i:03d}",
            "title": f"Test Document {i}",
            "content": f"This is the content of test document {i}. It contains information relevant to the query and can be used for testing retrieval and generation functionality.",
            "score": max(0.1, 1.0 - i * 0.1),
            "metadata": {
                "source": f"test_source_{i}.pdf",
                "page": i + 1,
                "section": f"Section {i}",
                "document_type": "test_document"
            }
        }
        for i in range(count)
    ]


def create_mock_response(
    answer: str = "Test answer",
    complexity: str = "medium",
    confidence: float = 0.85,
    cost: float = 0.002,
    cache_hit: bool = False
) -> UnifiedQueryResponse:
    """Create a mock UnifiedQueryResponse for testing."""
    return UnifiedQueryResponse(
        answer=answer,
        sources=[DocumentSource(
            id="test_doc",
            title="Test Document",
            content="Test content",
            score=0.9,
            metadata={"source": "test.pdf"}
        )],
        complexity=complexity,
        confidence=confidence,
        cost=CostBreakdown(
            model_used="test-model",
            total_cost=cost,
            model_cost=cost
        ),
        metrics=ProcessingMetrics(
            total_time=1.0,
            analysis_time=0.1,
            retrieval_time=0.2,
            generation_time=0.6,
            documents_retrieved=1,
            cache_hit=cache_hit
        ),
        query_id=str(uuid.uuid4()),
        session_id="test-session",
        strategy_used="balanced",
        fallback_used=False,
        warnings=[]
    )