"""
Integration Tests for Epic 8 API Gateway Service.

Tests complete integration between API Gateway and all microservices in the Epic 8 ecosystem.
Based on CT-8.5 specifications from epic8-test-specification.md.

Testing Philosophy:
- Hard Fails: Complete pipeline failures, >60s response, service communication breakdowns
- Quality Flags: <90% integration success, >5s end-to-end time, partial service failures

Test Categories:
- Query Analyzer service integration (CT-8.5.1)
- Generator service integration (CT-8.5.2) 
- Retriever service integration (CT-8.5.3)
- Cache service integration (CT-8.5.4)
- Analytics service integration (CT-8.5.5)
- Complete pipeline integration (CT-8.5.6)
"""

import pytest
import asyncio
import time
import uuid
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys
from unittest.mock import Mock, AsyncMock, MagicMock, patch
import httpx

# Add services to path
services_path = Path(__file__).parent.parent.parent.parent / "services" / "api-gateway"
if services_path.exists():
    sys.path.insert(0, str(services_path))

try:
    from gateway_app.core.gateway import APIGatewayService
    from gateway_app.schemas.requests import UnifiedQueryRequest, BatchQueryRequest, QueryOptions
    from gateway_app.schemas.responses import (
        UnifiedQueryResponse, BatchQueryResponse, GatewayStatusResponse,
        ProcessingMetrics, CostBreakdown, DocumentSource
    )
    from gateway_app.core.config import APIGatewaySettings
    from gateway_app.clients.query_analyzer import QueryAnalyzerClient  
    from gateway_app.clients.generator import GeneratorClient
    from gateway_app.clients.retriever import RetrieverClient
    from gateway_app.clients.cache import CacheClient
    from gateway_app.clients.analytics import AnalyticsClient
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    IMPORT_ERROR = str(e)


# Test data factories for Pydantic schema objects
def create_test_cost_breakdown(
    model_used: str = "test-model",
    model_cost: float = 0.001,
    total_cost: float = None,
    input_tokens: int = None,
    output_tokens: int = None,
    retrieval_cost: float = 0.0,
    cost_estimation_confidence: float = 1.0
) -> CostBreakdown:
    """Create a test CostBreakdown object with all required fields."""
    if total_cost is None:
        total_cost = model_cost + retrieval_cost
    
    return CostBreakdown(
        model_used=model_used,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        model_cost=model_cost,
        retrieval_cost=retrieval_cost,
        total_cost=total_cost,
        cost_estimation_confidence=cost_estimation_confidence
    )


def create_test_processing_metrics(
    analysis_time: float = 0.1,
    retrieval_time: float = 0.2,
    generation_time: float = 0.3,
    total_time: float = None,
    documents_retrieved: int = 0,
    cache_hit: bool = False,
    cache_time: float = None,
    tokens_generated: int = None,
    cache_key: str = None
) -> ProcessingMetrics:
    """Create a test ProcessingMetrics object with all required fields."""
    if total_time is None:
        total_time = analysis_time + retrieval_time + generation_time
        if cache_time:
            total_time += cache_time
    
    return ProcessingMetrics(
        analysis_time=analysis_time,
        retrieval_time=retrieval_time,
        generation_time=generation_time,
        cache_time=cache_time,
        total_time=total_time,
        documents_retrieved=documents_retrieved,
        tokens_generated=tokens_generated,
        cache_hit=cache_hit,
        cache_key=cache_key
    )


def create_test_document_source(
    id: str = "test-doc",
    title: str = "Test Document",
    content: str = "Test content",
    score: float = 0.9,
    metadata: Dict[str, Any] = None
) -> DocumentSource:
    """Create a test DocumentSource object."""
    if metadata is None:
        metadata = {"source": "test.pdf", "page": 1}
    
    return DocumentSource(
        id=id,
        title=title,
        content=content,
        score=score,
        metadata=metadata
    )


def create_test_unified_query_response(
    answer: str = "Test answer",
    sources: List[DocumentSource] = None,
    complexity: str = "simple",
    confidence: float = 0.8,
    cost: CostBreakdown = None,
    metrics: ProcessingMetrics = None,
    query_id: str = "test-query",
    session_id: str = "test-session",
    strategy_used: str = "balanced",
    fallback_used: bool = False,
    warnings: List[str] = None
) -> UnifiedQueryResponse:
    """Create a test UnifiedQueryResponse object with all required fields."""
    if sources is None:
        sources = []
    if cost is None:
        cost = create_test_cost_breakdown()
    if metrics is None:
        metrics = create_test_processing_metrics()
    if warnings is None:
        warnings = []
    
    return UnifiedQueryResponse(
        answer=answer,
        sources=sources,
        complexity=complexity,
        confidence=confidence,
        cost=cost,
        metrics=metrics,
        query_id=query_id,
        session_id=session_id,
        strategy_used=strategy_used,
        fallback_used=fallback_used,
        warnings=warnings
    )


class TestAPIGatewayQueryAnalyzerIntegration:
    """Test integration with Query Analyzer service (CT-8.5.1)."""

    @pytest.fixture
    def mock_query_analyzer_client(self):
        """Create realistic mock for Query Analyzer client."""
        client = AsyncMock(spec=QueryAnalyzerClient)
        
        # Mock successful analysis response
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
        
        # Mock health check
        client.health_check.return_value = True
        
        # Mock endpoint structure
        client.endpoint = Mock()
        client.endpoint.url = "http://query-analyzer:8081"
        
        return client

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_query_analyzer_integration_success(self, mock_query_analyzer_client):
        """Test successful integration with Query Analyzer (CT-8.5.1)."""
        gateway = APIGatewayService()
        gateway.query_analyzer = mock_query_analyzer_client
        gateway._initialize_circuit_breakers()
        
        request = UnifiedQueryRequest(
            query="How does machine learning work?",
            context={"domain": "educational", "type": "Q&A"},
            options=QueryOptions(
                strategy="balanced",
                complexity_hint="medium"
            )
        )
        
        try:
            # Test analysis through gateway
            start_time = time.time()
            analysis = await gateway._analyze_query(request)
            integration_time = time.time() - start_time
            
            # Hard fail: Integration takes >60s
            assert integration_time < 60.0, f"Query Analyzer integration took {integration_time:.2f}s"
            
            # Validate analysis result structure
            assert "complexity" in analysis, "Analysis missing complexity"
            assert "confidence" in analysis, "Analysis missing confidence"
            assert "recommended_models" in analysis, "Analysis missing recommended_models"
            assert "cost_estimate" in analysis, "Analysis missing cost_estimate"
            
            # Validate analysis values
            assert analysis["complexity"] in ["simple", "medium", "complex"], "Invalid complexity"
            assert 0.0 <= analysis["confidence"] <= 1.0, "Invalid confidence range"
            assert len(analysis["recommended_models"]) > 0, "No model recommendations"
            assert isinstance(analysis["cost_estimate"], dict), "Cost estimate should be dict"
            
            # Verify client was called correctly
            mock_query_analyzer_client.analyze_query.assert_called_once_with(
                query=request.query,
                context=request.context,
                complexity_hint=request.options.complexity_hint
            )
            
            # Quality flag: Integration should be fast
            if integration_time > 1.0:
                pytest.warns(UserWarning, f"Query Analyzer integration slow: {integration_time:.3f}s")
            
            print(f"Query Analyzer integration successful: {analysis['complexity']} complexity, {integration_time:.3f}s")
            
        except Exception as e:
            pytest.fail(f"Query Analyzer integration failed (Hard Fail): {e}")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_query_analyzer_integration_failure(self):
        """Test Query Analyzer integration failure handling (CT-8.5.1)."""
        gateway = APIGatewayService()
        
        # Mock failing analyzer client
        failing_client = AsyncMock()
        failing_client.analyze_query.side_effect = Exception("Analyzer service unavailable")
        gateway.query_analyzer = failing_client
        gateway._initialize_circuit_breakers()
        
        request = UnifiedQueryRequest(
            query="Test query for failure handling",
            options=QueryOptions(strategy="balanced")
        )
        
        try:
            # Should return fallback analysis
            analysis = await gateway._analyze_query(request)
            
            # Should get fallback analysis 
            assert analysis is not None, "Should return fallback analysis"
            assert "complexity" in analysis, "Fallback analysis missing complexity"
            assert "recommended_models" in analysis, "Fallback analysis missing models"
            
            # Fallback should provide basic values
            assert analysis["complexity"] in ["simple", "medium", "complex"], "Invalid fallback complexity"
            assert len(analysis["recommended_models"]) > 0, "Fallback should recommend at least one model"
            
            print("Query Analyzer failure handling successful - fallback analysis returned")
            
        except Exception as e:
            pytest.fail(f"Query Analyzer failure handling failed: {e}")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_query_analyzer_circuit_breaker_integration(self, mock_query_analyzer_client):
        """Test circuit breaker behavior with Query Analyzer (CT-8.5.1)."""
        gateway = APIGatewayService()
        gateway.query_analyzer = mock_query_analyzer_client
        gateway._initialize_circuit_breakers()
        
        # Initially should work
        request = UnifiedQueryRequest(query="Test query", options=QueryOptions())
        analysis = await gateway._analyze_query(request)
        assert analysis is not None
        
        # Verify circuit breaker starts closed
        cb = gateway.circuit_breakers["query-analyzer"]
        assert cb.state == "closed", "Circuit breaker should start closed"
        
        # Mock failures to trigger circuit breaker
        mock_query_analyzer_client.analyze_query.side_effect = Exception("Service down")
        
        # Trigger failures up to threshold
        for i in range(cb.failure_threshold):
            try:
                await gateway._analyze_query(request)
            except Exception:
                # Expected failures to trigger circuit breaker
                pass
        
        # Circuit breaker should now be open
        if cb.failure_count >= cb.failure_threshold:
            assert cb.state == "open", "Circuit breaker should open after failures"
            print(f"Circuit breaker opened after {cb.failure_count} failures")
        
        print("Query Analyzer circuit breaker integration test completed")


class TestAPIGatewayGeneratorIntegration:
    """Test integration with Generator service (CT-8.5.2)."""

    @pytest.fixture
    def mock_generator_client(self):
        """Create realistic mock for Generator client."""
        client = AsyncMock(spec=GeneratorClient)
        
        # Mock successful generation response
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
        
        # Mock available models
        client.get_available_models.return_value = {
            "models": [
                {
                    "provider": "openai",
                    "name": "gpt-3.5-turbo",
                    "available": True,
                    "context_length": 4096,
                    "input_cost": 0.0015,
                    "output_cost": 0.002
                },
                {
                    "provider": "ollama",
                    "name": "llama3.2:3b", 
                    "available": True,
                    "context_length": 2048,
                    "input_cost": 0.0,
                    "output_cost": 0.0
                }
            ]
        }
        
        client.health_check.return_value = True
        
        # Mock endpoint structure
        client.endpoint = Mock()
        client.endpoint.url = "http://generator:8082"
        
        return client

    @pytest.fixture
    def sample_documents(self):
        """Sample retrieved documents for generation."""
        return [
            {
                "id": "doc1",
                "title": "Introduction to Machine Learning",
                "content": "Machine learning is a method of data analysis that automates analytical model building.",
                "score": 0.95,
                "metadata": {"source": "ml_textbook.pdf", "page": 1}
            },
            {
                "id": "doc2", 
                "title": "AI and ML Fundamentals",
                "content": "Artificial intelligence and machine learning are closely related fields focusing on creating intelligent systems.",
                "score": 0.87,
                "metadata": {"source": "ai_guide.pdf", "page": 12}
            }
        ]

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_generator_integration_success(self, mock_generator_client, sample_documents):
        """Test successful integration with Generator service (CT-8.5.2)."""
        gateway = APIGatewayService()
        gateway.generator = mock_generator_client
        gateway._initialize_circuit_breakers()
        
        request = UnifiedQueryRequest(
            query="What is machine learning?",
            options=QueryOptions(strategy="balanced")
        )
        
        analysis = {
            "complexity": "medium",
            "recommended_models": ["openai/gpt-3.5-turbo"],
            "routing_strategy": "balanced"
        }
        
        try:
            start_time = time.time()
            answer_data = await gateway._generate_answer(request, sample_documents, analysis)
            integration_time = time.time() - start_time
            
            # Hard fail: Generation takes >60s
            assert integration_time < 60.0, f"Generator integration took {integration_time:.2f}s"
            
            # Validate answer data structure
            assert "answer" in answer_data, "Answer data missing answer"
            assert "confidence" in answer_data, "Answer data missing confidence"
            assert "model_used" in answer_data, "Answer data missing model_used"
            assert "cost" in answer_data, "Answer data missing cost"
            
            # Validate answer data values
            assert len(answer_data["answer"]) > 0, "Answer cannot be empty"
            assert 0.0 <= answer_data["confidence"] <= 1.0, "Invalid confidence range"
            assert answer_data["cost"] >= 0.0, "Cost cannot be negative"
            assert answer_data["model_used"] is not None, "Model used should be specified"
            
            # Verify client was called correctly
            mock_generator_client.generate_answer.assert_called_once()
            call_args = mock_generator_client.generate_answer.call_args
            assert call_args.kwargs["query"] == request.query
            assert call_args.kwargs["context_documents"] == sample_documents
            assert call_args.kwargs["routing_decision"] == "openai/gpt-3.5-turbo"
            
            # Quality flag: Generation should be reasonably fast
            if integration_time > 3.0:
                pytest.warns(UserWarning, f"Generator integration slow: {integration_time:.3f}s")
            
            print(f"Generator integration successful: {len(answer_data['answer'])} chars, {integration_time:.3f}s")
            
        except Exception as e:
            pytest.fail(f"Generator integration failed (Hard Fail): {e}")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_generator_integration_failure(self):
        """Test Generator integration failure handling (CT-8.5.2)."""
        gateway = APIGatewayService()
        
        # Mock failing generator client
        failing_client = AsyncMock()
        failing_client.generate_answer.side_effect = Exception("Generator service unavailable")
        gateway.generator = failing_client
        gateway._initialize_circuit_breakers()
        
        request = UnifiedQueryRequest(query="Test query", options=QueryOptions())
        analysis = {"recommended_models": ["test-model"]}
        
        try:
            # Should raise exception since answer generation is critical
            with pytest.raises(Exception):
                await gateway._generate_answer(request, [], analysis)
            
            print("Generator failure handling successful - exception raised as expected")
            
        except pytest.raises(Exception):
            pass  # Expected behavior
        except Exception as e:
            pytest.fail(f"Generator failure handling unexpected error: {e}")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_generator_model_availability_integration(self, mock_generator_client):
        """Test model availability integration (CT-8.5.2)."""
        gateway = APIGatewayService()
        gateway.generator = mock_generator_client
        
        try:
            models_response = await gateway.get_available_models()
            
            # Validate models response
            assert hasattr(models_response, 'models'), "Response should have models"
            assert hasattr(models_response, 'total_models'), "Response should have total_models" 
            assert hasattr(models_response, 'available_models'), "Response should have available_models"
            assert hasattr(models_response, 'providers'), "Response should have providers"
            
            # Validate model data
            assert len(models_response.models) > 0, "Should have at least one model"
            assert models_response.available_models <= models_response.total_models, "Available should not exceed total"
            assert len(models_response.providers) > 0, "Should have at least one provider"
            
            # Check specific models from mock
            model_names = [m.name for m in models_response.models]
            assert "gpt-3.5-turbo" in model_names, "Should include GPT-3.5"
            assert "llama3.2:3b" in model_names, "Should include Llama model"
            
            print(f"Model availability integration successful: {len(models_response.models)} models, {len(models_response.providers)} providers")
            
        except Exception as e:
            pytest.fail(f"Model availability integration failed: {e}")


class TestAPIGatewayRetrieverIntegration:
    """Test integration with Retriever service (CT-8.5.3)."""

    @pytest.fixture
    def mock_retriever_client(self):
        """Create realistic mock for Retriever client."""
        client = AsyncMock(spec=RetrieverClient)
        
        # Mock document retrieval response
        client.retrieve_documents.return_value = [
            {
                "id": "doc_001",
                "title": "Machine Learning Fundamentals",
                "content": "Machine learning is a branch of artificial intelligence that focuses on algorithms that can learn from and make predictions on data.",
                "score": 0.94,
                "metadata": {
                    "source": "ml_handbook.pdf",
                    "page": 15,
                    "section": "Introduction",
                    "last_modified": "2024-01-15"
                }
            },
            {
                "id": "doc_002",
                "title": "Deep Learning Concepts", 
                "content": "Deep learning uses neural networks with multiple layers to model and understand complex patterns in data.",
                "score": 0.89,
                "metadata": {
                    "source": "dl_guide.pdf", 
                    "page": 8,
                    "section": "Neural Networks",
                    "last_modified": "2024-02-01"
                }
            },
            {
                "id": "doc_003",
                "title": "AI Applications",
                "content": "Artificial intelligence applications span across various industries including healthcare, finance, and autonomous vehicles.",
                "score": 0.76,
                "metadata": {
                    "source": "ai_applications.pdf",
                    "page": 23, 
                    "section": "Industry Use Cases",
                    "last_modified": "2024-01-30"
                }
            }
        ]
        
        client.health_check.return_value = True
        
        # Mock endpoint structure
        client.endpoint = Mock()
        client.endpoint.url = "http://retriever:8083"
        
        return client

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_retriever_integration_success(self, mock_retriever_client):
        """Test successful integration with Retriever service (CT-8.5.3)."""
        gateway = APIGatewayService()
        gateway.retriever = mock_retriever_client
        gateway._initialize_circuit_breakers()
        
        request = UnifiedQueryRequest(
            query="What is machine learning?",
            options=QueryOptions(
                strategy="balanced",
                max_documents=5
            )
        )
        
        analysis = {
            "complexity": "medium",
            "recommended_doc_count": 5
        }
        
        try:
            start_time = time.time()
            documents = await gateway._retrieve_documents(request, analysis)
            integration_time = time.time() - start_time
            
            # Hard fail: Retrieval takes >60s
            assert integration_time < 60.0, f"Retriever integration took {integration_time:.2f}s"
            
            # Validate documents structure
            assert isinstance(documents, list), "Documents should be a list"
            assert len(documents) > 0, "Should retrieve at least one document"
            
            # Validate document structure
            for i, doc in enumerate(documents):
                assert "id" in doc, f"Document {i} missing id"
                assert "title" in doc, f"Document {i} missing title"
                assert "content" in doc, f"Document {i} missing content" 
                assert "score" in doc, f"Document {i} missing score"
                assert "metadata" in doc, f"Document {i} missing metadata"
                
                # Validate document values
                assert len(doc["content"]) > 0, f"Document {i} content cannot be empty"
                assert 0.0 <= doc["score"] <= 1.0, f"Document {i} invalid score: {doc['score']}"
                assert isinstance(doc["metadata"], dict), f"Document {i} metadata should be dict"
            
            # Documents should be sorted by relevance (descending)
            scores = [doc["score"] for doc in documents]
            assert scores == sorted(scores, reverse=True), "Documents should be sorted by score descending"
            
            # Verify client was called correctly
            mock_retriever_client.retrieve_documents.assert_called_once()
            call_args = mock_retriever_client.retrieve_documents.call_args
            assert call_args.kwargs["query"] == request.query
            assert call_args.kwargs["max_documents"] == 5
            assert call_args.kwargs["complexity"] == "medium"
            
            # Quality flag: Retrieval should be fast
            if integration_time > 2.0:
                pytest.warns(UserWarning, f"Retriever integration slow: {integration_time:.3f}s")
            
            print(f"Retriever integration successful: {len(documents)} documents, avg score: {sum(scores)/len(scores):.3f}")
            
        except Exception as e:
            pytest.fail(f"Retriever integration failed (Hard Fail): {e}")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_retriever_integration_failure(self):
        """Test Retriever integration failure handling (CT-8.5.3)."""
        gateway = APIGatewayService()
        
        # Mock failing retriever client
        failing_client = AsyncMock()
        failing_client.retrieve_documents.side_effect = Exception("Retriever service unavailable")
        gateway.retriever = failing_client
        gateway._initialize_circuit_breakers()
        
        request = UnifiedQueryRequest(query="Test query", options=QueryOptions())
        analysis = {"complexity": "medium"}
        
        try:
            # Should return empty documents list to allow generation to continue
            documents = await gateway._retrieve_documents(request, analysis)
            
            assert isinstance(documents, list), "Should return list even on failure"
            assert len(documents) == 0, "Should return empty list on failure"
            
            print("Retriever failure handling successful - empty documents returned")
            
        except Exception as e:
            pytest.fail(f"Retriever failure handling failed: {e}")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_retriever_integration_document_limits(self, mock_retriever_client):
        """Test document limit handling in retriever integration (CT-8.5.3)."""
        gateway = APIGatewayService()
        gateway.retriever = mock_retriever_client
        gateway._initialize_circuit_breakers()
        
        # Test with different document limits
        test_cases = [
            {"max_documents": 1, "expected_call": 1},
            {"max_documents": 3, "expected_call": 3},
            {"max_documents": None, "expected_call": 5},  # Default from analysis
        ]
        
        for test_case in test_cases:
            request = UnifiedQueryRequest(
                query="Test query",
                options=QueryOptions(max_documents=test_case["max_documents"])
            )
            
            analysis = {"recommended_doc_count": 5}
            
            await gateway._retrieve_documents(request, analysis)
            
            # Verify correct max_documents was passed
            call_args = mock_retriever_client.retrieve_documents.call_args
            expected_max = test_case["expected_call"]
            actual_max = call_args.kwargs["max_documents"]
            
            assert actual_max == expected_max, f"Expected max_documents {expected_max}, got {actual_max}"
            
        print("Document limit handling test passed")


class TestAPIGatewayCacheIntegration:
    """Test integration with Cache service (CT-8.5.4)."""

    @pytest.fixture
    def mock_cache_client(self):
        """Create realistic mock for Cache client."""
        client = AsyncMock(spec=CacheClient)
        
        # Mock cache operations
        client.get_cached_response.return_value = None  # Default: no cache hit
        client.cache_response.return_value = True
        client.clear_cache.return_value = {"keys_removed": 10, "pattern": "*"}
        client.get_cache_statistics.return_value = {
            "hit_rate": 0.68,
            "total_keys": 250,
            "total_hits": 170,
            "total_misses": 80,
            "memory_usage": "45MB",
            "uptime": 7200
        }
        
        client.health_check.return_value = True
        
        # Mock endpoint structure
        client.endpoint = Mock()
        client.endpoint.url = "http://cache:8084"
        
        return client

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_cache_integration_miss_and_store(self, mock_cache_client):
        """Test cache miss and subsequent storage (CT-8.5.4)."""
        gateway = APIGatewayService()
        gateway.cache = mock_cache_client
        gateway._initialize_circuit_breakers()
        
        query_hash = "test_hash_123"
        
        try:
            # Test cache miss
            start_time = time.time()
            cached_response = await gateway._get_cached_response(query_hash)
            cache_get_time = time.time() - start_time
            
            # Should return None for cache miss
            assert cached_response is None, "Should return None for cache miss"
            
            # Verify cache was checked
            mock_cache_client.get_cached_response.assert_called_once_with(query_hash)
            
            # Test cache storage
            mock_response = create_test_unified_query_response(
                answer="Test answer",
                sources=[],
                complexity="simple",
                confidence=0.8,
                cost=create_test_cost_breakdown(total_cost=0.001),
                metrics=create_test_processing_metrics(
                    analysis_time=0.1,
                    retrieval_time=0.1,
                    generation_time=0.3,
                    total_time=0.5,
                    documents_retrieved=0,
                    cache_hit=False
                ),
                query_id="test-query",
                session_id="test-session",
                strategy_used="balanced",
                fallback_used=False,
                warnings=[]
            )
            
            start_time = time.time()
            cache_stored = await gateway._cache_response(query_hash, mock_response)
            cache_store_time = time.time() - start_time
            
            # Should successfully store
            assert cache_stored is True, "Cache storage should succeed"
            
            # Verify cache was called correctly
            mock_cache_client.cache_response.assert_called_once()
            call_args = mock_cache_client.cache_response.call_args
            assert call_args[0][0] == query_hash  # First arg is query_hash
            assert call_args[1]["ttl"] == 3600  # TTL argument
            
            # Quality flags for performance
            if cache_get_time > 0.1:
                pytest.warns(UserWarning, f"Cache get slow: {cache_get_time:.3f}s")
            if cache_store_time > 0.5:
                pytest.warns(UserWarning, f"Cache store slow: {cache_store_time:.3f}s")
            
            print(f"Cache integration successful: get={cache_get_time:.3f}s, store={cache_store_time:.3f}s")
            
        except Exception as e:
            pytest.fail(f"Cache integration failed: {e}")

    # Service availability handled by fixtures
    @pytest.mark.asyncio 
    async def test_cache_integration_hit(self, mock_cache_client):
        """Test cache hit scenario (CT-8.5.4)."""
        gateway = APIGatewayService()
        gateway.cache = mock_cache_client
        gateway._initialize_circuit_breakers()
        
        # Mock cached response data - cache client returns dict, not Pydantic object
        cached_response_obj = create_test_unified_query_response(
            answer="Cached answer about machine learning",
            sources=[],
            complexity="medium", 
            confidence=0.89,
            cost=create_test_cost_breakdown(model_used="cached", total_cost=0.0, model_cost=0.0),
            metrics=create_test_processing_metrics(
                analysis_time=0.0,
                retrieval_time=0.0,
                generation_time=0.0,
                total_time=0.001,
                documents_retrieved=0,
                cache_hit=True
            ),
            query_id="cached-query-id",
            session_id="cached-session",
            strategy_used="balanced",
            fallback_used=False,
            warnings=[]
        )
        
        # Cache client returns dictionary representation, not the object itself
        mock_cache_client.get_cached_response.return_value = cached_response_obj.model_dump()
        
        query_hash = "cached_hash_456"
        
        try:
            cached_response = await gateway._get_cached_response(query_hash)
            
            # Should return cached response
            assert cached_response is not None, "Should return cached response"
            assert cached_response.answer == "Cached answer about machine learning"
            assert cached_response.metrics.cache_hit is True
            assert cached_response.cost.total_cost == 0.0  # Cached responses have no cost
            
            print("Cache hit integration successful")
            
        except Exception as e:
            pytest.fail(f"Cache hit integration failed: {e}")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_cache_integration_failure(self):
        """Test cache integration failure handling (CT-8.5.4)."""
        gateway = APIGatewayService()
        
        # Mock failing cache client
        failing_client = AsyncMock()
        failing_client.get_cached_response.side_effect = Exception("Cache service unavailable")
        failing_client.cache_response.side_effect = Exception("Cache storage failed")
        gateway.cache = failing_client
        gateway._initialize_circuit_breakers()
        
        try:
            # Cache failures should not break the pipeline
            cached_response = await gateway._get_cached_response("test_hash")
            assert cached_response is None, "Should return None on cache failure"
            
            mock_response = create_test_unified_query_response(
                answer="Test", 
                sources=[], 
                complexity="simple", 
                confidence=0.5,
                cost=create_test_cost_breakdown(total_cost=0.0, model_cost=0.0),
                metrics=create_test_processing_metrics(
                    analysis_time=0.03,
                    retrieval_time=0.03,
                    generation_time=0.04,
                    total_time=0.1,
                    documents_retrieved=0,
                    cache_hit=False
                ),
                query_id="test", 
                session_id="test", 
                strategy_used="balanced",
                fallback_used=False, 
                warnings=[]
            )
            
            cache_stored = await gateway._cache_response("test_hash", mock_response)
            assert cache_stored is False, "Should return False on cache storage failure"
            
            print("Cache failure handling successful - pipeline continues without cache")
            
        except Exception as e:
            pytest.fail(f"Cache failure handling failed: {e}")


class TestAPIGatewayAnalyticsIntegration:
    """Test integration with Analytics service (CT-8.5.5)."""

    @pytest.fixture
    def mock_analytics_client(self):
        """Create realistic mock for Analytics client."""
        client = AsyncMock(spec=AnalyticsClient)
        
        # Mock analytics operations
        client.record_cache_hit.return_value = True
        client.record_query_completion.return_value = True
        client.record_error.return_value = True
        
        client.health_check.return_value = True
        
        # Mock endpoint structure
        client.endpoint = Mock()
        client.endpoint.url = "http://analytics:8085"
        
        return client

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_analytics_integration_query_completion(self, mock_analytics_client):
        """Test analytics integration for query completion (CT-8.5.5)."""
        gateway = APIGatewayService()
        gateway.analytics = mock_analytics_client
        gateway._initialize_circuit_breakers()
        
        request = UnifiedQueryRequest(
            query="Test analytics query",
            session_id="analytics-session",
            user_id="analytics-user",
            options=QueryOptions(analytics_enabled=True)
        )
        
        response = create_test_unified_query_response(
            answer="Analytics test answer",
            sources=[],
            complexity="medium",
            confidence=0.85,
            cost=create_test_cost_breakdown(total_cost=0.003, model_cost=0.003),
            metrics=create_test_processing_metrics(
                analysis_time=0.3,
                retrieval_time=0.4,
                generation_time=0.5,
                total_time=1.2,
                documents_retrieved=0,
                cache_hit=False
            ),
            query_id="analytics-query-id",
            session_id="analytics-session",
            strategy_used="balanced",
            fallback_used=False,
            warnings=[]
        )
        
        try:
            start_time = time.time()
            result = await gateway._record_query_completion(request, response)
            analytics_time = time.time() - start_time
            
            # Should succeed
            assert result is True, "Analytics recording should succeed"
            
            # Verify analytics was called correctly
            mock_analytics_client.record_query_completion.assert_called_once()
            call_args = mock_analytics_client.record_query_completion.call_args
            assert call_args.kwargs["query_request"] == request.model_dump()
            assert call_args.kwargs["query_response"] == response.model_dump()
            
            # Quality flag: Analytics should be fast and non-blocking
            if analytics_time > 1.0:
                pytest.warns(UserWarning, f"Analytics recording slow: {analytics_time:.3f}s")
            
            print(f"Analytics query completion integration successful: {analytics_time:.3f}s")
            
        except Exception as e:
            pytest.fail(f"Analytics query completion integration failed: {e}")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_analytics_integration_cache_hit(self, mock_analytics_client):
        """Test analytics integration for cache hits (CT-8.5.5)."""
        gateway = APIGatewayService()
        gateway.analytics = mock_analytics_client
        gateway._initialize_circuit_breakers()
        
        request = UnifiedQueryRequest(
            query="Cache hit test",
            session_id="cache-session", 
            user_id="cache-user",
            options=QueryOptions(analytics_enabled=True)
        )
        
        try:
            result = await gateway._record_cache_hit(request)
            
            # Should succeed
            assert result is True, "Cache hit analytics should succeed"
            
            # Verify analytics was called correctly
            mock_analytics_client.record_cache_hit.assert_called_once()
            call_args = mock_analytics_client.record_cache_hit.call_args
            assert call_args.kwargs["query_hash"] == request.query_hash
            assert call_args.kwargs["session_id"] == request.session_id
            assert call_args.kwargs["user_id"] == request.user_id
            
            print("Analytics cache hit integration successful")
            
        except Exception as e:
            pytest.fail(f"Analytics cache hit integration failed: {e}")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_analytics_integration_error_recording(self, mock_analytics_client):
        """Test analytics integration for error recording (CT-8.5.5)."""
        gateway = APIGatewayService()
        gateway.analytics = mock_analytics_client
        gateway._initialize_circuit_breakers()
        
        try:
            result = await gateway._record_error(
                error_type="test_error",
                error_message="Test error for analytics",
                query="Test query with error",
                session_id="error-session"
            )
            
            # Should succeed
            assert result is True, "Error analytics should succeed"
            
            # Verify analytics was called correctly
            mock_analytics_client.record_error.assert_called_once()
            call_args = mock_analytics_client.record_error.call_args
            assert call_args.kwargs["error_type"] == "test_error"
            assert call_args.kwargs["error_message"] == "Test error for analytics"
            assert call_args.kwargs["query"] == "Test query with error"
            assert call_args.kwargs["service"] == "api-gateway"
            assert call_args.kwargs["session_id"] == "error-session"
            
            print("Analytics error recording integration successful")
            
        except Exception as e:
            pytest.fail(f"Analytics error recording integration failed: {e}")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_analytics_integration_failure(self):
        """Test analytics integration failure handling (CT-8.5.5)."""
        gateway = APIGatewayService()
        
        # Mock failing analytics client
        failing_client = AsyncMock()
        failing_client.record_query_completion.side_effect = Exception("Analytics unavailable")
        failing_client.record_cache_hit.side_effect = Exception("Analytics unavailable")
        failing_client.record_error.side_effect = Exception("Analytics unavailable")
        gateway.analytics = failing_client
        gateway._initialize_circuit_breakers()
        
        try:
            # Analytics failures should not break the pipeline
            request = UnifiedQueryRequest(query="test", options=QueryOptions())
            response = create_test_unified_query_response(
                answer="test", 
                sources=[], 
                complexity="simple", 
                confidence=0.5,
                cost=create_test_cost_breakdown(total_cost=0.0, model_cost=0.0),
                metrics=create_test_processing_metrics(
                    analysis_time=0.03,
                    retrieval_time=0.03,
                    generation_time=0.04,
                    total_time=0.1,
                    documents_retrieved=0,
                    cache_hit=False
                ),
                query_id="test", 
                session_id="test", 
                strategy_used="balanced",
                fallback_used=False, 
                warnings=[]
            )
            
            # All should return False but not raise exceptions
            result1 = await gateway._record_query_completion(request, response)
            result2 = await gateway._record_cache_hit(request)
            result3 = await gateway._record_error("test", "test error")
            
            assert result1 is False, "Should return False on analytics failure"
            assert result2 is False, "Should return False on analytics failure"
            assert result3 is False, "Should return False on analytics failure"
            
            print("Analytics failure handling successful - pipeline continues without analytics")
            
        except Exception as e:
            pytest.fail(f"Analytics failure handling failed: {e}")


class TestAPIGatewayCompletePipelineIntegration:
    """Test complete end-to-end pipeline integration (CT-8.5.6)."""

    @pytest.fixture
    def full_mock_gateway(self):
        """Create gateway with all services mocked for complete integration testing."""
        gateway = APIGatewayService()
        
        # Query Analyzer
        query_analyzer = AsyncMock()
        query_analyzer.analyze_query.return_value = {
            "complexity": "medium",
            "confidence": 0.87,
            "recommended_models": ["openai/gpt-3.5-turbo"],
            "cost_estimate": {"openai/gpt-3.5-turbo": 0.002},
            "routing_strategy": "balanced",
            "recommended_doc_count": 5
        }
        query_analyzer.health_check.return_value = True
        query_analyzer.endpoint.url = "http://query-analyzer:8081"
        
        # Retriever
        retriever = AsyncMock()
        retriever.retrieve_documents.return_value = [
            {
                "id": "doc1",
                "title": "ML Basics",
                "content": "Machine learning fundamentals and concepts.",
                "score": 0.95,
                "metadata": {"source": "textbook.pdf"}
            },
            {
                "id": "doc2", 
                "title": "AI Overview",
                "content": "Artificial intelligence introduction and applications.",
                "score": 0.87,
                "metadata": {"source": "guide.pdf"}
            }
        ]
        retriever.health_check.return_value = True
        retriever.endpoint.url = "http://retriever:8083"
        
        # Generator
        generator = AsyncMock()
        generator.generate_answer.return_value = {
            "answer": "Machine learning is a subset of AI that enables systems to learn from data without explicit programming. It uses statistical techniques to give computers the ability to learn from experience.",
            "confidence": 0.92,
            "model_used": "openai/gpt-3.5-turbo",
            "input_tokens": 120,
            "output_tokens": 35,
            "cost": 0.0023,
            "tokens_generated": 35
        }
        generator.health_check.return_value = True
        generator.endpoint.url = "http://generator:8082"
        
        # Cache
        cache = AsyncMock()
        cache.get_cached_response.return_value = None  # No cache hit
        cache.cache_response.return_value = True
        cache.get_cache_statistics.return_value = {"hit_rate": 0.65, "total_keys": 100}
        cache.health_check.return_value = True
        cache.endpoint.url = "http://cache:8084"
        
        # Analytics
        analytics = AsyncMock()
        analytics.record_query_completion.return_value = True
        analytics.record_cache_hit.return_value = True
        analytics.record_error.return_value = True
        analytics.health_check.return_value = True
        
        # Mock endpoint structure
        analytics.endpoint = Mock()
        analytics.endpoint.url = "http://analytics:8085"
        
        # Assign to gateway
        gateway.query_analyzer = query_analyzer
        gateway.retriever = retriever
        gateway.generator = generator
        gateway.cache = cache
        gateway.analytics = analytics
        
        gateway._initialize_circuit_breakers()
        
        return gateway

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_complete_pipeline_integration_success(self, full_mock_gateway):
        """Test complete end-to-end pipeline integration (CT-8.5.6)."""
        gateway = full_mock_gateway
        
        request = UnifiedQueryRequest(
            query="What is machine learning and how does it work?",
            context={"domain": "educational", "type": "documentation"},
            options=QueryOptions(
                strategy="balanced",
                cache_enabled=True,
                analytics_enabled=True,
                max_documents=5,
                max_cost=0.10
            ),
            session_id="integration-test-session",
            user_id="integration-test-user"
        )
        
        try:
            start_time = time.time()
            response = await gateway.process_unified_query(request)
            total_integration_time = time.time() - start_time
            
            # Hard fail: Complete pipeline takes >60s
            assert total_integration_time < 60.0, f"Complete pipeline took {total_integration_time:.2f}s"
            
            # Validate complete response structure
            assert isinstance(response, UnifiedQueryResponse)
            assert response.answer is not None
            assert len(response.answer) > 0
            assert response.complexity == "medium"
            assert 0.0 <= response.confidence <= 1.0
            assert response.query_id is not None
            assert response.session_id == "integration-test-session"
            assert response.strategy_used == "balanced"
            assert response.fallback_used is False
            
            # Validate sources integration
            assert len(response.sources) == 2  # From mock retriever
            for source in response.sources:
                assert source.id is not None
                assert source.score >= 0.0
                assert source.content is not None
            
            # Validate metrics integration
            metrics = response.metrics
            assert metrics.total_time > 0
            assert metrics.analysis_time is not None
            assert metrics.retrieval_time is not None
            assert metrics.generation_time is not None
            assert metrics.documents_retrieved == 2
            assert metrics.cache_hit is False
            
            # Validate cost integration
            cost = response.cost
            assert cost.total_cost == 0.0023  # From mock generator
            assert cost.model_used == "openai/gpt-3.5-turbo"
            
            # Verify all services were called in correct order
            gateway.query_analyzer.analyze_query.assert_called_once()
            gateway.cache.get_cached_response.assert_called_once()
            gateway.retriever.retrieve_documents.assert_called_once()
            gateway.generator.generate_answer.assert_called_once()
            gateway.cache.cache_response.assert_called_once()
            gateway.analytics.record_query_completion.assert_called_once()
            
            # Verify service metrics updated
            assert gateway.requests_processed == 1
            assert gateway.total_response_time > 0
            assert gateway.error_count == 0
            
            # Quality flag: Complete pipeline should be efficient
            if total_integration_time > 5.0:
                pytest.warns(UserWarning, f"Complete pipeline slow: {total_integration_time:.3f}s")
            
            print(f"Complete pipeline integration successful: {total_integration_time:.3f}s, {len(response.answer)} chars answer")
            
        except Exception as e:
            pytest.fail(f"Complete pipeline integration failed (Hard Fail): {e}")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_batch_pipeline_integration(self, full_mock_gateway):
        """Test batch processing complete integration (CT-8.5.6)."""
        gateway = full_mock_gateway
        
        batch_request = BatchQueryRequest(
            queries=[
                "What is machine learning?",
                "How do neural networks work?", 
                "Explain deep learning concepts?"
            ],
            context={"domain": "technical", "type": "education"},
            options=QueryOptions(
                strategy="cost_optimized",
                cache_enabled=True,
                analytics_enabled=True
            ),
            parallel_processing=True,
            max_parallel=2,
            session_id="batch-integration-session",
            user_id="batch-integration-user"
        )
        
        try:
            start_time = time.time()
            response = await gateway.process_batch_queries(batch_request)
            batch_integration_time = time.time() - start_time
            
            # Hard fail: Batch processing takes >60s
            assert batch_integration_time < 60.0, f"Batch integration took {batch_integration_time:.2f}s"
            
            # Validate batch response structure
            assert isinstance(response, BatchQueryResponse)
            assert response.batch_id is not None
            assert response.total_queries == 3
            assert response.parallel_processing is True
            assert len(response.results) == 3
            assert response.session_id == "batch-integration-session"
            
            # Validate individual results
            successful_count = 0
            for i, result in enumerate(response.results):
                assert result.index == i
                assert result.query == batch_request.queries[i]
                
                if result.success:
                    successful_count += 1
                    assert result.result is not None
                    assert isinstance(result.result, UnifiedQueryResponse)
                    assert len(result.result.answer) > 0
            
            # Hard fail: 0% success rate
            assert successful_count > 0, "All batch queries failed"
            
            # Calculate success rate
            success_rate = successful_count / len(batch_request.queries)
            assert response.successful_queries == successful_count
            assert response.failed_queries == (3 - successful_count)
            
            # Quality flag: Batch success rate should be high
            if success_rate < 0.9:
                pytest.warns(UserWarning, f"Batch integration success rate {success_rate:.2%} below 90%")
            
            # Validate summary statistics
            assert response.total_cost > 0  # Should have some cost
            assert response.processing_time > 0
            
            print(f"Batch pipeline integration successful: {successful_count}/3 queries in {batch_integration_time:.3f}s")
            
        except Exception as e:
            pytest.fail(f"Batch pipeline integration failed (Hard Fail): {e}")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_pipeline_integration_with_cache_hit(self, full_mock_gateway):
        """Test pipeline integration with cache hit scenario (CT-8.5.6)."""
        gateway = full_mock_gateway
        
        # Configure cache to return cached response
        cached_response_obj = create_test_unified_query_response(
            answer="Cached machine learning answer from previous request",
            sources=[create_test_document_source(
                id="cached_doc", 
                title="Cached Document", 
                content="Cached content", 
                score=0.9
            )],
            complexity="medium",
            confidence=0.88,
            cost=create_test_cost_breakdown(model_used="cached", total_cost=0.0, model_cost=0.0),
            metrics=create_test_processing_metrics(
                analysis_time=0.0,
                retrieval_time=0.0,
                generation_time=0.0,
                total_time=0.002,
                documents_retrieved=1,
                cache_hit=True,
                cache_key="test_hash"
            ),
            query_id="cached-query-123",
            session_id="cache-hit-session", 
            strategy_used="balanced",
            fallback_used=False,
            warnings=[]
        )
        
        # Cache client returns dictionary representation 
        gateway.cache.get_cached_response.return_value = cached_response_obj.model_dump()
        
        request = UnifiedQueryRequest(
            query="What is machine learning?",
            options=QueryOptions(
                cache_enabled=True,
                analytics_enabled=True,
                force_refresh=False
            ),
            session_id="cache-hit-session"
        )
        
        try:
            response = await gateway.process_unified_query(request)
            
            # Should return cached response
            assert response.answer == "Cached machine learning answer from previous request"
            assert response.metrics.cache_hit is True
            assert response.cost.total_cost == 0.0
            
            # Should not call analysis, retrieval, or generation
            gateway.query_analyzer.analyze_query.assert_not_called()
            gateway.retriever.retrieve_documents.assert_not_called()
            gateway.generator.generate_answer.assert_not_called()
            
            # Should record cache hit
            gateway.analytics.record_cache_hit.assert_called_once()
            
            print("Cache hit pipeline integration successful")
            
        except Exception as e:
            pytest.fail(f"Cache hit pipeline integration failed: {e}")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_pipeline_integration_with_service_failures(self, full_mock_gateway):
        """Test pipeline integration resilience with partial service failures (CT-8.5.6)."""
        gateway = full_mock_gateway
        
        # Make retriever fail but keep other services working
        gateway.retriever.retrieve_documents.side_effect = Exception("Retriever unavailable")
        
        request = UnifiedQueryRequest(
            query="Test resilience with retriever failure",
            options=QueryOptions(strategy="balanced", analytics_enabled=True)
        )
        
        try:
            response = await gateway.process_unified_query(request)
            
            # Pipeline should continue with empty documents
            assert response is not None
            assert response.answer is not None  # Generator should still work
            assert len(response.sources) == 0  # No documents retrieved
            assert response.fallback_used is False  # Not full fallback, partial degradation
            
            # Verify services were still called appropriately
            gateway.query_analyzer.analyze_query.assert_called_once()
            gateway.generator.generate_answer.assert_called_once()
            
            # Generator should have been called with empty documents
            call_args = gateway.generator.generate_answer.call_args
            documents = call_args.kwargs.get("context_documents", [])
            assert len(documents) == 0, "Generator should receive empty documents on retriever failure"
            
            print("Partial service failure integration successful - pipeline degraded gracefully")
            
        except Exception as e:
            pytest.fail(f"Partial service failure integration failed: {e}")


if __name__ == "__main__":
    # Run specific test classes for development
    pytest.main([__file__ + "::TestAPIGatewayCompletePipelineIntegration", "-v"])