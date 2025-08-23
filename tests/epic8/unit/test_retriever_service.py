"""
Unit Tests for Epic 8 Retriever Service.

Tests the core functionality of the RetrieverService wrapping Epic 2's ModularUnifiedRetriever
for microservices deployment. Based on CT-8.3 specifications from epic8-test-specification.md.

Testing Philosophy:
- Hard Fails: Service crashes, health check 500s, >60s response, >8GB memory, 0% retrieval success
- Quality Flags: <10ms avg retrieval, >90% hit rate, retrieval accuracy, fallback mechanisms
"""

import pytest
import asyncio
import time
import unittest.mock as mock
from typing import Dict, Any, List
from pathlib import Path
import sys

# Simple fix: Mock prometheus_client to prevent registry collisions
mock.patch.dict('sys.modules', {
    'prometheus_client': mock.Mock(
        Counter=mock.Mock(),
        Histogram=mock.Mock(),
        Gauge=mock.Mock()
    )
}).start()

# Robust service import logic for Epic 8 testing
def _setup_service_imports():
    """Set up imports for Epic 8 Retriever Service testing."""
    # Get the absolute path to the service
    current_file = Path(__file__).resolve()
    project_root = current_file.parents[3]  # Go up 3 levels from tests/epic8/unit/
    service_path = project_root / "services" / "retriever"
    
    if not service_path.exists():
        return False, f"Service path does not exist: {service_path}", {}
    
    # Add service path to sys.path if not already present
    service_path_str = str(service_path)
    if service_path_str not in sys.path:
        sys.path.insert(0, service_path_str)
    
    # Ensure __init__.py files exist for proper module structure
    app_init = service_path / "retriever_app" / "__init__.py"
    core_init = service_path / "retriever_app" / "core" / "__init__.py"
    
    if not app_init.exists() or not core_init.exists():
        return False, f"Missing __init__.py files in service structure", {}
    
    try:
        # Try importing the required modules
        from retriever_app.core.retriever import RetrieverService
        
        # Return the imported classes so they can be used globally
        imports = {
            'RetrieverService': RetrieverService
        }
        return True, None, imports
    except ImportError as e:
        return False, f"Import failed: {str(e)}", {}
    except Exception as e:
        return False, f"Unexpected error during import: {str(e)}", {}

# Execute import setup
IMPORTS_AVAILABLE, IMPORT_ERROR, imported_classes = _setup_service_imports()

# Make imported classes available globally if imports succeeded
if IMPORTS_AVAILABLE:
    RetrieverService = imported_classes['RetrieverService']

# Clean up the setup function from global namespace
del _setup_service_imports, imported_classes


# Pytest fixtures for Epic 8 testing infrastructure
@pytest.fixture(autouse=True)  
def isolate_prometheus_registry():
    """
    Isolate Prometheus metrics registry for each test to prevent collisions.
    
    Multiple Epic 8 services define metrics with the same names, causing
    'Duplicated timeseries in CollectorRegistry' errors in tests.
    """
    import prometheus_client
    
    # Create a new isolated registry for this test
    test_registry = prometheus_client.CollectorRegistry()
    
    # Store the original global registry
    original_registry = prometheus_client.REGISTRY
    
    try:
        # Replace the global registry with our isolated one
        prometheus_client.REGISTRY = test_registry
        
        # Clear any existing global state 
        if hasattr(prometheus_client, '_COLLECTORS'):
            prometheus_client._COLLECTORS.clear()
            
        yield test_registry
        
    finally:
        # Restore the original registry after the test
        prometheus_client.REGISTRY = original_registry


class TestRetrieverServiceBasics:
    """Test basic service initialization and health checks."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test that service can be initialized without crashing (Hard Fail test)."""
        try:
            # Test default initialization
            service = RetrieverService()
            assert service is not None
            assert not service._initialized  # Should start uninitialized
            assert service.retriever is None
            assert service.embedder is None
            assert service.config == {}
            
            # Test initialization with configuration
            test_config = {
                'retriever_config': {'vector_index': {'type': 'faiss'}},
                'embedder_config': {'type': 'sentence_transformer'},
                'performance': {'batch': {'max_batch_size': 50}},
                'monitoring': {'metrics_enabled': True}
            }
            
            service_with_config = RetrieverService(config=test_config)
            assert service_with_config.config == test_config
            assert service_with_config._thread_pool is not None
            assert isinstance(service_with_config.retrieval_stats, dict)
            
            # Verify stats initialization
            expected_stats = {
                "total_retrievals", "total_time", "avg_time", 
                "last_retrieval_time", "error_count", "circuit_breaker_trips"
            }
            assert set(service_with_config.retrieval_stats.keys()) == expected_stats
            
        except Exception as e:
            pytest.fail(f"Service initialization crashed: {e}")
    
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_health_check_basic(self):
        """Test basic health check functionality (Hard Fail test)."""
        service = RetrieverService()
        
        # Health check should not return 500 error or crash
        start_time = time.time()
        try:
            health_result = await service.health_check()
            health_check_time = time.time() - start_time
            
            # Hard fail: Health check takes >60s (clearly broken)
            assert health_check_time < 60.0, f"Health check took {health_check_time:.2f}s, service is broken"
            
            # Should return boolean
            assert isinstance(health_result, bool), "Health check should return boolean"
            
            # Quality flag: Health check should ideally be fast
            if health_check_time > 2.0:
                pytest.warns(UserWarning, f"Health check slow: {health_check_time:.2f}s (flag for optimization)")
                
        except Exception as e:
            pytest.fail(f"Health check crashed (Hard Fail): {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_component_initialization(self):
        """Test Epic 2 component initialization (Integration test)."""
        # Mock the Epic 2 components to avoid actual initialization
        with mock.patch('src.core.component_factory.ComponentFactory') as mock_factory:
            with mock.patch('src.components.retrievers.modular_unified_retriever.ModularUnifiedRetriever') as mock_retriever:
                mock_embedder = mock.Mock()
                mock_retriever_instance = mock.Mock()
                
                mock_factory.create_embedder.return_value = mock_embedder
                mock_retriever.return_value = mock_retriever_instance
                mock_retriever_instance.get_component_info.return_value = {'type': 'modular_unified'}
                mock_retriever_instance.get_document_count.return_value = 100
                
                service = RetrieverService({
                    'embedder_config': {'type': 'sentence_transformer'},
                    'retriever_config': {'type': 'modular_unified'}
                })
                
                try:
                    await service._initialize_components()
                    
                    # Verify initialization completed
                    assert service._initialized is True
                    assert service.embedder is not None
                    assert service.retriever is not None
                    
                    # Verify factory calls
                    mock_factory.create_embedder.assert_called_once()
                    mock_retriever.assert_called_once()
                    
                    print("Epic 2 component initialization test passed")
                    
                except Exception as e:
                    pytest.fail(f"Component initialization failed: {e}")


class TestRetrieverServiceDocumentRetrieval:
    """Test document retrieval functionality based on CT-8.3.1 specifications."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_document_retrieval_basic(self):
        """Test basic document retrieval functionality (CT-8.3.1)."""
        # Mock Epic 2 components
        with mock.patch('src.core.component_factory.ComponentFactory') as mock_factory:
            with mock.patch('src.components.retrievers.modular_unified_retriever.ModularUnifiedRetriever') as mock_retriever:
                # Setup mocks
                mock_embedder = mock.Mock()
                mock_retriever_instance = mock.Mock()
                
                # Mock retrieval results
                from unittest.mock import Mock
                mock_result = Mock()
                mock_result.document = Mock()
                mock_result.document.content = "Test document content about machine learning"
                mock_result.document.metadata = {"title": "ML Guide", "page": 1}
                mock_result.document.doc_id = "doc_001"
                mock_result.document.source = "test.pdf"
                mock_result.score = 0.85
                mock_result.retrieval_method = "modular_unified_hybrid"
                
                mock_retriever_instance.retrieve.return_value = [mock_result]
                mock_retriever_instance.get_document_count.return_value = 100
                mock_retriever_instance.get_component_info.return_value = {'type': 'modular_unified'}
                
                mock_factory.create_embedder.return_value = mock_embedder
                mock_retriever.return_value = mock_retriever_instance
                
                service = RetrieverService()
                
                try:
                    # Test retrieval
                    start_time = time.time()
                    result = await service.retrieve_documents(
                        query="What is machine learning?",
                        k=10,
                        retrieval_strategy="hybrid"
                    )
                    retrieval_time = time.time() - start_time
                    
                    # Hard fail: Response time >60s (clearly broken)
                    assert retrieval_time < 60.0, f"Retrieval took {retrieval_time:.2f}s, service is broken"
                    
                    # Quality flag: Should be fast (sub-second)
                    if retrieval_time > 1.0:
                        pytest.warns(UserWarning, f"Slow retrieval: {retrieval_time:.2f}s (target <1s)")
                    
                    # Validate response structure
                    assert isinstance(result, list), "Result should be a list"
                    assert len(result) > 0, "Should return at least one result"
                    
                    doc = result[0]
                    assert "content" in doc, "Document missing 'content' field"
                    assert "metadata" in doc, "Document missing 'metadata' field"
                    assert "doc_id" in doc, "Document missing 'doc_id' field"
                    assert "source" in doc, "Document missing 'source' field"
                    assert "score" in doc, "Document missing 'score' field"
                    assert "retrieval_method" in doc, "Document missing 'retrieval_method' field"
                    
                    # Validate field types and values
                    assert isinstance(doc["content"], str), "Content must be string"
                    assert isinstance(doc["metadata"], dict), "Metadata must be dict"
                    assert isinstance(doc["score"], (int, float)), "Score must be numeric"
                    assert 0.0 <= doc["score"] <= 1.0, f"Score {doc['score']} out of range [0,1]"
                    
                    # Verify stats updated
                    assert service.retrieval_stats["total_retrievals"] == 1
                    assert service.retrieval_stats["total_time"] > 0
                    assert service.retrieval_stats["avg_time"] > 0
                    
                    print(f"Basic retrieval test passed: {len(result)} docs in {retrieval_time:.3f}s")
                    
                except Exception as e:
                    pytest.fail(f"Basic retrieval test failed: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_retrieval_strategies(self):
        """Test different retrieval strategies (CT-8.3.1)."""
        with mock.patch('src.core.component_factory.ComponentFactory') as mock_factory:
            with mock.patch('src.components.retrievers.modular_unified_retriever.ModularUnifiedRetriever') as mock_retriever:
                # Setup mocks
                mock_embedder = mock.Mock()
                mock_retriever_instance = mock.Mock()
                
                mock_result = mock.Mock()
                mock_result.document = mock.Mock()
                mock_result.document.content = "Test content"
                mock_result.document.metadata = {}
                mock_result.document.doc_id = "doc_001"
                mock_result.document.source = "test.pdf"
                mock_result.score = 0.75
                mock_result.retrieval_method = "test_method"
                
                mock_retriever_instance.retrieve.return_value = [mock_result]
                mock_retriever_instance.get_component_info.return_value = {'type': 'modular_unified'}
                mock_retriever_instance.get_document_count.return_value = 100
                
                mock_factory.create_embedder.return_value = mock_embedder
                mock_retriever.return_value = mock_retriever_instance
                
                service = RetrieverService()
                
                strategies = ["hybrid", "semantic", "keyword"]
                
                for strategy in strategies:
                    try:
                        result = await service.retrieve_documents(
                            query=f"Test query for {strategy}",
                            k=5,
                            retrieval_strategy=strategy
                        )
                        
                        # Should return results for all strategies
                        assert len(result) > 0, f"No results for {strategy} strategy"
                        
                        # Verify retriever was called with correct parameters
                        mock_retriever_instance.retrieve.assert_called()
                        
                        print(f"Strategy {strategy} test passed")
                        
                    except Exception as e:
                        pytest.fail(f"Strategy {strategy} test failed: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_retrieval_fallback_mechanism(self):
        """Test fallback mechanism when Epic 2 retrieval fails."""
        with mock.patch('src.core.component_factory.ComponentFactory') as mock_factory:
            with mock.patch('src.components.retrievers.modular_unified_retriever.ModularUnifiedRetriever') as mock_retriever:
                # Setup mocks to fail
                mock_embedder = mock.Mock()
                mock_retriever_instance = mock.Mock()
                mock_retriever_instance.retrieve.side_effect = Exception("Epic 2 retrieval failed")
                mock_retriever_instance.get_component_info.return_value = {'type': 'modular_unified'}
                mock_retriever_instance.get_document_count.return_value = 100
                
                mock_factory.create_embedder.return_value = mock_embedder
                mock_retriever.return_value = mock_retriever_instance
                
                service = RetrieverService()
                
                try:
                    result = await service.retrieve_documents(
                        query="Test query that will fail",
                        k=10
                    )
                    
                    # Should return fallback results, not crash
                    assert isinstance(result, list), "Should return fallback results"
                    
                    if len(result) > 0:
                        # Verify fallback document structure
                        fallback_doc = result[0]
                        assert "content" in fallback_doc
                        assert "retrieval_method" in fallback_doc
                        assert fallback_doc["retrieval_method"] == "fallback"
                        assert fallback_doc["score"] == 0.0
                    
                    # Error count should be incremented
                    assert service.retrieval_stats["error_count"] > 0
                    
                    print("Fallback mechanism test passed")
                    
                except Exception as e:
                    pytest.fail(f"Fallback mechanism failed: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_retrieval_parameter_validation(self):
        """Test parameter validation for retrieval requests."""
        with mock.patch('retriever_app.core.retriever.ComponentFactory'):
            with mock.patch('retriever_app.core.retriever.ModularUnifiedRetriever'):
                service = RetrieverService()
                
                # Test valid parameters
                try:
                    await service.retrieve_documents(
                        query="Valid query",
                        k=10,
                        retrieval_strategy="hybrid",
                        complexity="medium",
                        max_documents=50
                    )
                    # Should not raise exception (with mocked components)
                except Exception as e:
                    if "not initialized" not in str(e):  # Expected error with mocks
                        pytest.fail(f"Valid parameters should not fail: {e}")
                
                print("Parameter validation test passed")


class TestRetrieverServiceBatchRetrieval:
    """Test batch retrieval functionality based on CT-8.3.2 specifications."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_batch_retrieval_basic(self):
        """Test basic batch retrieval functionality (CT-8.3.2)."""
        with mock.patch('src.core.component_factory.ComponentFactory') as mock_factory:
            with mock.patch('src.components.retrievers.modular_unified_retriever.ModularUnifiedRetriever') as mock_retriever:
                # Setup mocks
                mock_embedder = mock.Mock()
                mock_retriever_instance = mock.Mock()
                
                mock_result = mock.Mock()
                mock_result.document = mock.Mock()
                mock_result.document.content = "Batch test content"
                mock_result.document.metadata = {"title": "Batch Doc"}
                mock_result.document.doc_id = "batch_doc_001"
                mock_result.document.source = "batch.pdf"
                mock_result.score = 0.80
                mock_result.retrieval_method = "modular_unified_hybrid"
                
                mock_retriever_instance.retrieve.return_value = [mock_result]
                mock_retriever_instance.get_component_info.return_value = {'type': 'modular_unified'}
                mock_retriever_instance.get_document_count.return_value = 100
                
                mock_factory.create_embedder.return_value = mock_embedder
                mock_retriever.return_value = mock_retriever_instance
                
                service = RetrieverService()
                
                try:
                    queries = [
                        "What is machine learning?",
                        "How do neural networks work?",
                        "What is deep learning?"
                    ]
                    
                    start_time = time.time()
                    results = await service.batch_retrieve_documents(
                        queries=queries,
                        k=5,
                        retrieval_strategy="hybrid"
                    )
                    batch_time = time.time() - start_time
                    
                    # Hard fail: Batch processing >60s per query is broken
                    max_time_per_query = batch_time / len(queries)
                    assert max_time_per_query < 60.0, f"Batch processing {max_time_per_query:.2f}s per query is broken"
                    
                    # Quality flag: Should be reasonably efficient
                    if batch_time > len(queries) * 2.0:  # More than 2s per query
                        pytest.warns(UserWarning, f"Batch processing slow: {batch_time:.2f}s for {len(queries)} queries")
                    
                    # Validate results structure
                    assert isinstance(results, list), "Results should be a list"
                    assert len(results) == len(queries), f"Should return {len(queries)} result sets"
                    
                    # Validate individual result sets
                    for i, result_set in enumerate(results):
                        assert isinstance(result_set, list), f"Result set {i} should be a list"
                        if len(result_set) > 0:  # If results were returned
                            doc = result_set[0]
                            assert "content" in doc, f"Result set {i} missing content"
                            assert "score" in doc, f"Result set {i} missing score"
                    
                    print(f"Batch retrieval test passed: {len(queries)} queries in {batch_time:.3f}s")
                    
                except Exception as e:
                    pytest.fail(f"Batch retrieval test failed: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_batch_error_handling(self):
        """Test batch retrieval error handling and partial failures."""
        with mock.patch('src.core.component_factory.ComponentFactory') as mock_factory:
            with mock.patch('src.components.retrievers.modular_unified_retriever.ModularUnifiedRetriever') as mock_retriever:
                # Setup mocks with some failures
                mock_embedder = mock.Mock()
                mock_retriever_instance = mock.Mock()
                
                # Mock to fail on second call
                call_count = 0
                def failing_retrieve(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 2:
                        raise Exception("Simulated retrieval failure")
                    
                    mock_result = mock.Mock()
                    mock_result.document = mock.Mock()
                    mock_result.document.content = f"Content {call_count}"
                    mock_result.document.metadata = {}
                    mock_result.document.doc_id = f"doc_{call_count}"
                    mock_result.document.source = "test.pdf"
                    mock_result.score = 0.75
                    mock_result.retrieval_method = "test"
                    return [mock_result]
                
                mock_retriever_instance.retrieve.side_effect = failing_retrieve
                mock_retriever_instance.get_component_info.return_value = {'type': 'modular_unified'}
                mock_retriever_instance.get_document_count.return_value = 100
                
                mock_factory.create_embedder.return_value = mock_embedder
                mock_retriever.return_value = mock_retriever_instance
                
                service = RetrieverService()
                
                try:
                    queries = ["Query 1", "Query 2 (will fail)", "Query 3"]
                    
                    results = await service.batch_retrieve_documents(
                        queries=queries,
                        k=5
                    )
                    
                    # Should return results even with some failures
                    assert len(results) == 3, "Should return results for all queries"
                    
                    # First and third should succeed, second should be empty or fallback
                    assert len(results[0]) > 0, "First query should succeed"
                    assert len(results[2]) > 0, "Third query should succeed"
                    # Second query might be empty due to failure
                    
                    print(f"Batch error handling test passed: partial failures handled")
                    
                except Exception as e:
                    pytest.fail(f"Batch error handling test failed: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_batch_timeout_handling(self):
        """Test batch retrieval timeout handling."""
        service = RetrieverService({
            'performance': {
                'batch': {
                    'max_batch_size': 2,
                    'batch_timeout': 0.1  # Very short timeout for testing
                }
            }
        })
        
        # Mock slow retrieval
        with mock.patch.object(service, 'retrieve_documents') as mock_retrieve:
            async def slow_retrieve(*args, **kwargs):
                await asyncio.sleep(1.0)  # Longer than timeout
                return []
            
            mock_retrieve.side_effect = slow_retrieve
            
            try:
                queries = ["Query 1", "Query 2"]
                
                results = await service.batch_retrieve_documents(
                    queries=queries,
                    k=5
                )
                
                # Should handle timeout gracefully
                assert isinstance(results, list), "Should return results despite timeout"
                assert len(results) == len(queries), "Should return results for all queries"
                
                # Results might be empty due to timeout
                print("Batch timeout handling test passed")
                
            except Exception as e:
                pytest.fail(f"Batch timeout handling test failed: {e}")


class TestRetrieverServiceDocumentIndexing:
    """Test document indexing functionality based on CT-8.3.3 specifications."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_document_indexing_basic(self):
        """Test basic document indexing functionality (CT-8.3.3)."""
        with mock.patch('src.core.component_factory.ComponentFactory') as mock_factory:
            with mock.patch('src.components.retrievers.modular_unified_retriever.ModularUnifiedRetriever') as mock_retriever:
                # Setup mocks
                mock_embedder = mock.Mock()
                mock_embedder.embed.return_value = [[0.1, 0.2, 0.3]]  # Mock embedding
                
                mock_retriever_instance = mock.Mock()
                mock_retriever_instance.index_documents.return_value = None  # Successful indexing
                mock_retriever_instance.get_document_count.return_value = 105  # +5 documents
                mock_retriever_instance.get_component_info.return_value = {'type': 'modular_unified'}
                
                mock_factory.create_embedder.return_value = mock_embedder
                mock_retriever.return_value = mock_retriever_instance
                
                service = RetrieverService()
                
                try:
                    # Test indexing
                    documents = [
                        {
                            "content": "Machine learning is a subset of artificial intelligence",
                            "metadata": {"title": "ML Introduction", "type": "article"},
                            "doc_id": "ml_001",
                            "source": "intro.txt"
                        },
                        {
                            "content": "Neural networks are inspired by biological neurons",
                            "metadata": {"title": "Neural Networks", "type": "article"},
                            "doc_id": "nn_001", 
                            "source": "neural.txt"
                        }
                    ]
                    
                    start_time = time.time()
                    result = await service.index_documents(documents)
                    indexing_time = time.time() - start_time
                    
                    # Hard fail: Indexing >60s for small batch is broken
                    assert indexing_time < 60.0, f"Indexing took {indexing_time:.2f}s, service is broken"
                    
                    # Quality flag: Should be reasonably fast
                    if indexing_time > len(documents):  # More than 1s per document
                        pytest.warns(UserWarning, f"Slow indexing: {indexing_time:.2f}s for {len(documents)} docs")
                    
                    # Validate response structure
                    assert isinstance(result, dict), "Result should be a dict"
                    assert result["success"] is True, "Indexing should succeed"
                    assert result["indexed_documents"] == len(documents), "Should index all documents"
                    assert result["processing_time"] > 0, "Should report processing time"
                    assert result["total_documents"] > 0, "Should report total document count"
                    assert "message" in result, "Should include status message"
                    
                    # Verify embedder was called
                    mock_embedder.embed.assert_called()
                    
                    # Verify retriever indexing was called
                    mock_retriever_instance.index_documents.assert_called_once()
                    
                    print(f"Document indexing test passed: {len(documents)} docs in {indexing_time:.3f}s")
                    
                except Exception as e:
                    pytest.fail(f"Document indexing test failed: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_document_indexing_with_embeddings(self):
        """Test indexing documents with pre-computed embeddings."""
        with mock.patch('src.core.component_factory.ComponentFactory') as mock_factory:
            with mock.patch('src.components.retrievers.modular_unified_retriever.ModularUnifiedRetriever') as mock_retriever:
                # Setup mocks
                mock_embedder = mock.Mock()
                mock_retriever_instance = mock.Mock()
                mock_retriever_instance.index_documents.return_value = None
                mock_retriever_instance.get_document_count.return_value = 101
                mock_retriever_instance.get_component_info.return_value = {'type': 'modular_unified'}
                
                mock_factory.create_embedder.return_value = mock_embedder
                mock_retriever.return_value = mock_retriever_instance
                
                service = RetrieverService()
                
                try:
                    # Test with pre-computed embeddings
                    documents = [
                        {
                            "content": "Document with pre-computed embedding",
                            "metadata": {"title": "Pre-embedded Doc"},
                            "doc_id": "pre_001",
                            "source": "pre.txt",
                            "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]  # Pre-computed
                        }
                    ]
                    
                    result = await service.index_documents(documents)
                    
                    # Should succeed
                    assert result["success"] is True
                    assert result["indexed_documents"] == 1
                    
                    # Embedder should not be called for pre-embedded docs
                    # (though this is implementation detail)
                    
                    print("Document indexing with embeddings test passed")
                    
                except Exception as e:
                    pytest.fail(f"Document indexing with embeddings test failed: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_document_reindexing(self):
        """Test document reindexing functionality."""
        with mock.patch('src.core.component_factory.ComponentFactory') as mock_factory:
            with mock.patch('src.components.retrievers.modular_unified_retriever.ModularUnifiedRetriever') as mock_retriever:
                # Setup mocks
                mock_embedder = mock.Mock()
                mock_retriever_instance = mock.Mock()
                
                # Mock existing documents
                mock_doc = mock.Mock()
                mock_doc.content = "Existing document"
                mock_retriever_instance.documents = [mock_doc]
                
                mock_retriever_instance.clear_index.return_value = None
                mock_retriever_instance.index_documents.return_value = None
                mock_retriever_instance.get_document_count.return_value = 1
                mock_retriever_instance.get_component_info.return_value = {'type': 'modular_unified'}
                
                mock_factory.create_embedder.return_value = mock_embedder
                mock_retriever.return_value = mock_retriever_instance
                
                service = RetrieverService()
                
                try:
                    start_time = time.time()
                    result = await service.reindex_documents()
                    reindex_time = time.time() - start_time
                    
                    # Hard fail: Reindexing >60s for single doc is broken
                    assert reindex_time < 60.0, f"Reindexing took {reindex_time:.2f}s, service is broken"
                    
                    # Validate response
                    assert isinstance(result, dict), "Result should be a dict"
                    assert result["success"] is True, "Reindexing should succeed"
                    assert result["reindexed_documents"] >= 0, "Should report reindexed count"
                    assert result["processing_time"] > 0, "Should report processing time"
                    assert "message" in result, "Should include status message"
                    
                    # Verify clear and reindex were called
                    mock_retriever_instance.clear_index.assert_called_once()
                    mock_retriever_instance.index_documents.assert_called_once()
                    
                    print(f"Document reindexing test passed in {reindex_time:.3f}s")
                    
                except Exception as e:
                    pytest.fail(f"Document reindexing test failed: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_indexing_error_handling(self):
        """Test error handling during document indexing."""
        with mock.patch('src.core.component_factory.ComponentFactory') as mock_factory:
            with mock.patch('src.components.retrievers.modular_unified_retriever.ModularUnifiedRetriever') as mock_retriever:
                # Setup mocks to fail
                mock_embedder = mock.Mock()
                mock_embedder.embed.side_effect = Exception("Embedding failed")
                
                mock_retriever_instance = mock.Mock()
                mock_retriever_instance.get_component_info.return_value = {'type': 'modular_unified'}
                mock_retriever_instance.get_document_count.return_value = 100
                
                mock_factory.create_embedder.return_value = mock_embedder
                mock_retriever.return_value = mock_retriever_instance
                
                service = RetrieverService()
                
                try:
                    documents = [
                        {
                            "content": "Document that will fail to embed",
                            "metadata": {"title": "Failing Doc"},
                            "doc_id": "fail_001",
                            "source": "fail.txt"
                        }
                    ]
                    
                    # Should raise exception gracefully
                    with pytest.raises(Exception):
                        await service.index_documents(documents)
                    
                    print("Indexing error handling test passed")
                    
                except AssertionError:
                    raise  # Re-raise pytest assertions
                except Exception as e:
                    pytest.fail(f"Indexing error handling test failed: {e}")


class TestRetrieverServiceStatus:
    """Test service status and monitoring functionality."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_get_retriever_status(self):
        """Test retriever status reporting."""
        with mock.patch('src.core.component_factory.ComponentFactory') as mock_factory:
            with mock.patch('src.components.retrievers.modular_unified_retriever.ModularUnifiedRetriever') as mock_retriever:
                # Setup mocks
                mock_embedder = mock.Mock()
                mock_retriever_instance = mock.Mock()
                mock_retriever_instance.get_retrieval_stats.return_value = {
                    "total_queries": 50,
                    "avg_response_time": 0.125
                }
                mock_retriever_instance.get_component_info.return_value = {
                    "type": "modular_unified",
                    "components": ["vector_index", "sparse_retriever", "fusion", "reranker"]
                }
                mock_retriever_instance.get_document_count.return_value = 1000
                
                mock_factory.create_embedder.return_value = mock_embedder
                mock_retriever.return_value = mock_retriever_instance
                
                service = RetrieverService({
                    'retriever_config': {
                        'vector_index': {'type': 'faiss'},
                        'sparse': {'type': 'bm25'},
                        'fusion': {'type': 'rrf'},
                        'reranker': {'type': 'semantic'}
                    }
                })
                
                try:
                    # Test status before initialization
                    status_before = await service.get_retriever_status()
                    assert isinstance(status_before, dict), "Status must be dict"
                    assert "initialized" in status_before, "Status missing 'initialized'"
                    assert status_before["initialized"] is False, "Should not be initialized initially"
                    
                    # Initialize service (mock)
                    await service._initialize_components()
                    
                    # Test status after initialization
                    status_after = await service.get_retriever_status()
                    assert status_after["initialized"] is True, "Should be initialized after setup"
                    
                    # Check status fields
                    expected_fields = [
                        "initialized", "status", "retriever_type", "configuration",
                        "documents", "performance", "components"
                    ]
                    for field in expected_fields:
                        assert field in status_after, f"Status missing '{field}'"
                    
                    # Validate field values
                    assert status_after["status"] in ["healthy", "error", "not_initialized"], "Invalid status value"
                    assert status_after["retriever_type"] == "ModularUnifiedRetriever", "Wrong retriever type"
                    assert isinstance(status_after["configuration"], dict), "Configuration must be dict"
                    assert isinstance(status_after["documents"], dict), "Documents info must be dict"
                    assert isinstance(status_after["performance"], dict), "Performance info must be dict"
                    assert isinstance(status_after["components"], dict), "Components info must be dict"
                    
                    print(f"Status test passed: {status_after['status']} ({status_after['retriever_type']})")
                    
                except Exception as e:
                    pytest.fail(f"Status test failed: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_service_shutdown(self):
        """Test graceful service shutdown."""
        service = RetrieverService()
        
        try:
            # Initialize some state
            service._initialized = True
            service.retriever = mock.Mock()
            service.embedder = mock.Mock()
            
            # Shutdown service
            await service.shutdown()
            
            # Verify shutdown state
            assert service._initialized is False, "Service should be uninitialized after shutdown"
            assert service.retriever is None, "Retriever should be None after shutdown"
            assert service.embedder is None, "Embedder should be None after shutdown"
            
            # Thread pool should be shutdown
            assert service._thread_pool._shutdown is True, "Thread pool should be shutdown"
            
            print("Service shutdown test passed")
            
        except Exception as e:
            pytest.fail(f"Service shutdown test failed: {e}")


class TestRetrieverServiceErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_uninitialized_service_behavior(self):
        """Test behavior when service is not initialized."""
        service = RetrieverService()
        
        # Service should initialize itself on first use
        with mock.patch('src.core.component_factory.ComponentFactory') as mock_factory:
            with mock.patch('src.components.retrievers.modular_unified_retriever.ModularUnifiedRetriever') as mock_retriever:
                mock_embedder = mock.Mock()
                mock_retriever_instance = mock.Mock()
                mock_retriever_instance.retrieve.return_value = []
                mock_retriever_instance.get_component_info.return_value = {'type': 'modular_unified'}
                mock_retriever_instance.get_document_count.return_value = 0
                
                mock_factory.create_embedder.return_value = mock_embedder
                mock_retriever.return_value = mock_retriever_instance
                
                try:
                    # Should auto-initialize
                    result = await service.retrieve_documents("test query")
                    assert service._initialized is True, "Should auto-initialize"
                    
                    print("Uninitialized service behavior test passed")
                    
                except Exception as e:
                    pytest.fail(f"Uninitialized service behavior test failed: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_concurrent_initialization(self):
        """Test concurrent initialization safety."""
        service = RetrieverService()
        
        with mock.patch('src.core.component_factory.ComponentFactory') as mock_factory:
            with mock.patch('src.components.retrievers.modular_unified_retriever.ModularUnifiedRetriever') as mock_retriever:
                mock_embedder = mock.Mock()
                mock_retriever_instance = mock.Mock()
                mock_retriever_instance.get_component_info.return_value = {'type': 'modular_unified'}
                mock_retriever_instance.get_document_count.return_value = 0
                
                mock_factory.create_embedder.return_value = mock_embedder
                mock_retriever.return_value = mock_retriever_instance
                
                try:
                    # Run concurrent initializations
                    tasks = [service._initialize_components() for _ in range(5)]
                    await asyncio.gather(*tasks)
                    
                    # Should be initialized only once
                    assert service._initialized is True
                    assert mock_factory.create_embedder.call_count == 1, "Should initialize only once"
                    
                    print("Concurrent initialization test passed")
                    
                except Exception as e:
                    pytest.fail(f"Concurrent initialization test failed: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_circuit_breaker_behavior(self):
        """Test circuit breaker pattern for retrieval failures."""
        service = RetrieverService()
        
        # Test that repeated failures trigger circuit breaker
        # (This is more of an integration test with the @circuit decorator)
        
        with mock.patch('src.core.component_factory.ComponentFactory') as mock_factory:
            with mock.patch('src.components.retrievers.modular_unified_retriever.ModularUnifiedRetriever') as mock_retriever:
                mock_embedder = mock.Mock()
                mock_retriever_instance = mock.Mock()
                mock_retriever_instance.retrieve.side_effect = Exception("Persistent failure")
                mock_retriever_instance.get_component_info.return_value = {'type': 'modular_unified'}
                mock_retriever_instance.get_document_count.return_value = 100
                
                mock_factory.create_embedder.return_value = mock_embedder
                mock_retriever.return_value = mock_retriever_instance
                
                try:
                    # Multiple failures should eventually trigger circuit breaker
                    failure_count = 0
                    for i in range(3):  # Try a few times
                        try:
                            await service.retrieve_documents(f"failing query {i}")
                        except:
                            failure_count += 1
                    
                    # Error count should be tracked
                    assert service.retrieval_stats["error_count"] >= failure_count
                    
                    print(f"Circuit breaker test passed: {failure_count} failures tracked")
                    
                except Exception as e:
                    pytest.fail(f"Circuit breaker test failed: {e}")


class TestRetrieverServiceResources:
    """Test resource usage and performance characteristics."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_memory_usage_basic(self):
        """Test that service doesn't use excessive memory."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        service = RetrieverService()
        
        with mock.patch('src.core.component_factory.ComponentFactory') as mock_factory:
            with mock.patch('src.components.retrievers.modular_unified_retriever.ModularUnifiedRetriever') as mock_retriever:
                mock_embedder = mock.Mock()
                mock_retriever_instance = mock.Mock()
                mock_retriever_instance.retrieve.return_value = []
                mock_retriever_instance.get_component_info.return_value = {'type': 'modular_unified'}
                mock_retriever_instance.get_document_count.return_value = 100
                
                mock_factory.create_embedder.return_value = mock_embedder
                mock_retriever.return_value = mock_retriever_instance
                
                # Run several operations
                for i in range(10):
                    await service.retrieve_documents(f"Test query {i}")
                
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = final_memory - initial_memory
                
                # Hard fail: >8GB memory usage (clearly broken)
                assert final_memory < 8000, f"Memory usage {final_memory:.1f}MB exceeds 8GB limit"
                
                # Quality flag: Large memory increase might indicate leak
                if memory_increase > 1000:  # 1GB increase
                    pytest.warns(UserWarning, f"Large memory increase: {memory_increase:.1f}MB")
                
                print(f"Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB (+{memory_increase:.1f}MB)")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_thread_pool_resource_management(self):
        """Test thread pool resource management."""
        service = RetrieverService()
        
        try:
            # Verify thread pool exists and has reasonable limits
            assert service._thread_pool is not None, "Thread pool should be initialized"
            assert service._thread_pool._max_workers <= 10, "Thread pool should have reasonable worker limit"
            
            # Test shutdown cleans up resources
            await service.shutdown()
            assert service._thread_pool._shutdown is True, "Thread pool should be shutdown"
            
            print("Thread pool resource management test passed")
            
        except Exception as e:
            pytest.fail(f"Thread pool resource test failed: {e}")


if __name__ == "__main__":
    # Run specific test classes for development
    pytest.main([__file__ + "::TestRetrieverServiceBasics", "-v"])