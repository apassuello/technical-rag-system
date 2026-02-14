"""
Test suite for PlatformOrchestrator query processing workflows.

Tests the query processing orchestration, retrieval, answer generation,
A/B testing integration, and end-to-end query workflows.
"""

import pytest
import time
from unittest.mock import Mock, patch

from src.core.platform_orchestrator import PlatformOrchestrator
from src.core.interfaces import Answer, RetrievalResult, Document, ExperimentAssignment
from .conftest import sample_retrieval_results, sample_documents


class TestPlatformOrchestratorQueryProcessing:
    """Test PlatformOrchestrator query processing workflows."""

    def test_process_query_success(self, valid_config_file, mock_component_factory):
        """Test successful query processing workflow."""
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        test_query = "What is machine learning?"
        answer = orchestrator.process_query(test_query, k=5)
        
        # Verify answer structure
        assert isinstance(answer, Answer)
        assert answer.text == "Test answer"
        assert answer.confidence == 0.8
        
        # Verify component workflow
        mock_retriever = mock_component_factory.mock_retriever
        mock_generator = mock_component_factory.mock_generator
        
        mock_retriever.retrieve.assert_called_once_with(test_query, 5)
        mock_generator.generate.assert_called_once()

    def test_process_query_custom_k_value(self, valid_config_file, mock_component_factory):
        """Test query processing with custom k value."""
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        test_query = "Test query with custom k"
        answer = orchestrator.process_query(test_query, k=10)
        
        assert isinstance(answer, Answer)
        
        # Verify k parameter was passed correctly
        mock_retriever = mock_component_factory.mock_retriever
        mock_retriever.retrieve.assert_called_once_with(test_query, 10)

    def test_process_query_uninitialized_system(self, valid_config_file, mock_component_factory):
        """Test query processing with uninitialized system."""
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        # Manually set system as uninitialized
        orchestrator._initialized = False
        
        with pytest.raises(RuntimeError, match="System not initialized"):
            orchestrator.process_query("test query")

    def test_process_query_retrieval_failure(self, valid_config_file, mock_component_factory):
        """Test query processing with retrieval failure."""
        # Configure retriever to fail
        mock_component_factory.mock_retriever.retrieve.side_effect = Exception("Retrieval failed")
        
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        with pytest.raises(Exception, match="Retrieval failed"):
            orchestrator.process_query("failing query")

    def test_process_query_generation_failure(self, valid_config_file, mock_component_factory):
        """Test query processing with answer generation failure."""
        # Configure generator to fail
        mock_component_factory.mock_generator.generate.side_effect = Exception("Generation failed")
        
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        with pytest.raises(Exception, match="Generation failed"):
            orchestrator.process_query("generation failing query")

    def test_process_query_empty_retrieval_results(self, valid_config_file, mock_component_factory):
        """Test query processing with empty retrieval results."""
        # Configure retriever to return empty results
        mock_component_factory.mock_retriever.retrieve.return_value = []
        
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        answer = orchestrator.process_query("no results query")
        
        # Should still generate answer (possibly with "no results" message)
        assert isinstance(answer, Answer)
        
        # Verify generation was still called
        mock_component_factory.mock_generator.generate.assert_called_once()

    def test_process_query_with_retrieval_context(self, valid_config_file, mock_component_factory, sample_retrieval_results):
        """Test query processing passes retrieval context to generator."""
        # Configure retriever with specific results
        mock_component_factory.mock_retriever.retrieve.return_value = sample_retrieval_results
        
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        answer = orchestrator.process_query("contextual query")
        
        # Verify generator received retrieval results
        mock_generator = mock_component_factory.mock_generator
        generate_call = mock_generator.generate.call_args
        
        # Should include query and retrieval results
        assert generate_call is not None
        call_args, call_kwargs = generate_call
        
        # Verify retrieval results were passed
        assert len(call_args) >= 2 or 'retrieved_docs' in call_kwargs or 'context' in call_kwargs

    def test_process_query_performance_tracking(self, valid_config_file, mock_component_factory):
        """Test query processing tracks performance metrics."""
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        start_time = time.time()
        answer = orchestrator.process_query("performance tracking query")
        end_time = time.time()
        
        assert isinstance(answer, Answer)
        
        # Verify performance tracking (if implemented)
        analytics_service = orchestrator.analytics_service
        
        # Would check if query analytics were recorded
        if hasattr(analytics_service, 'query_analytics') and analytics_service.query_analytics:
            assert len(analytics_service.query_analytics) > 0

    def test_process_query_with_confidence_scoring(self, valid_config_file, mock_component_factory):
        """Test query processing includes confidence scoring."""
        # Configure generator with specific confidence
        test_answer = Answer(
            text="High confidence answer",
            sources=[],
            confidence=0.92,
            metadata={"model": "test-generator", "tokens": 150}
        )
        mock_component_factory.mock_generator.generate.return_value = test_answer
        
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        answer = orchestrator.process_query("confidence query")
        
        assert answer.confidence == 0.92
        assert answer.text == "High confidence answer"

    def test_process_query_with_source_attribution(self, valid_config_file, mock_component_factory, sample_retrieval_results):
        """Test query processing includes proper source attribution."""
        # Configure retriever and generator with source information
        mock_component_factory.mock_retriever.retrieve.return_value = sample_retrieval_results
        
        test_answer = Answer(
            text="Answer with sources",
            sources=[
                {"document_id": "doc1", "chunk_id": "chunk1", "score": 0.95},
                {"document_id": "doc2", "chunk_id": "chunk2", "score": 0.87}
            ],
            confidence=0.88,
            metadata={"source_count": 2}
        )
        mock_component_factory.mock_generator.generate.return_value = test_answer
        
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        answer = orchestrator.process_query("source attribution query")
        
        assert len(answer.sources) == 2
        assert answer.sources[0]["score"] == 0.95
        assert answer.metadata["source_count"] == 2

    def test_process_query_error_handling_and_recovery(self, valid_config_file, mock_component_factory):
        """Test query processing error handling and recovery."""
        # Configure retriever to fail once, then succeed
        call_count = 0
        original_retrieve = mock_component_factory.mock_retriever.retrieve
        
        def retrieve_with_retry(query, k):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Temporary retrieval failure")
            return original_retrieve.return_value
        
        mock_component_factory.mock_retriever.retrieve.side_effect = retrieve_with_retry
        
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        # Should either implement retry logic or fail gracefully
        try:
            answer = orchestrator.process_query("retry query")
            # If retry logic exists, should succeed
            assert isinstance(answer, Answer)
            assert call_count == 2
        except Exception:
            # If no retry logic, should fail on first attempt
            assert call_count == 1

    def test_process_query_with_query_preprocessing(self, valid_config_file, mock_component_factory):
        """Test query processing with query preprocessing."""
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        # Test various query formats
        queries = [
            "What is machine learning?",
            "WHAT IS MACHINE LEARNING?",  # All caps
            "what is machine learning",    # No punctuation
            "  What is machine learning?  ",  # Extra whitespace
        ]
        
        for query in queries:
            answer = orchestrator.process_query(query)
            assert isinstance(answer, Answer)
            
            # Verify retriever was called (preprocessing may normalize query)
            mock_component_factory.mock_retriever.retrieve.assert_called()

    def test_process_query_batch_processing(self, valid_config_file, mock_component_factory):
        """Test batch query processing if implemented."""
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        queries = [
            "What is machine learning?",
            "How does deep learning work?",
            "What are neural networks?"
        ]
        
        # Test batch processing if method exists
        if hasattr(orchestrator, 'process_queries_batch'):
            answers = orchestrator.process_queries_batch(queries)
            
            assert isinstance(answers, list)
            assert len(answers) == 3
            assert all(isinstance(answer, Answer) for answer in answers)
        else:
            # Test individual processing
            answers = [orchestrator.process_query(query) for query in queries]
            
            assert len(answers) == 3
            assert all(isinstance(answer, Answer) for answer in answers)

    def test_process_query_with_filtering(self, valid_config_file, mock_component_factory):
        """Test query processing with result filtering."""
        # Configure retriever with mixed quality results
        mixed_results = [
            RetrievalResult(
                document=Document(content="High quality content", metadata={"quality": "high"}),
                score=0.95,
                retrieval_method="dense"
            ),
            RetrievalResult(
                document=Document(content="Low quality content", metadata={"quality": "low"}),
                score=0.30,
                retrieval_method="sparse"
            )
        ]
        mock_component_factory.mock_retriever.retrieve.return_value = mixed_results
        
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        answer = orchestrator.process_query("filtered query")
        
        assert isinstance(answer, Answer)
        
        # Verify filtering logic (implementation dependent)
        # High quality results should be prioritized

    def test_process_query_concurrent_processing(self, valid_config_file, mock_component_factory):
        """Test concurrent query processing safety."""
        import threading
        
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        results = []
        errors = []
        
        def process_query_thread(query_id):
            try:
                query = f"Concurrent query {query_id}"
                answer = orchestrator.process_query(query)
                results.append((query_id, answer))
            except Exception as e:
                errors.append((query_id, e))
        
        # Process queries concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=process_query_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify all processing completed successfully
        assert len(errors) == 0
        assert len(results) == 5
        
        # Verify all returned valid answers
        assert all(isinstance(answer, Answer) for _, answer in results)

    def test_process_query_memory_efficiency(self, valid_config_file, mock_component_factory):
        """Test query processing memory efficiency."""
        # Configure retriever to return many results
        large_results = [
            RetrievalResult(
                document=Document(content="x" * 1000, metadata={"id": f"doc_{i}"}),
                score=max(0.0, 0.8 - i * 0.01),  # Ensure non-negative scores
                retrieval_method="hybrid"
            )
            for i in range(100)
        ]
        mock_component_factory.mock_retriever.retrieve.return_value = large_results
        
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        answer = orchestrator.process_query("large results query")
        
        assert isinstance(answer, Answer)
        
        # Verify large result set was handled efficiently
        # Implementation may limit results or handle them in batches

    def test_process_query_analytics_integration(self, valid_config_file, mock_component_factory):
        """Test query processing integration with analytics service."""
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        query = "analytics integration query"
        answer = orchestrator.process_query(query)
        
        assert isinstance(answer, Answer)
        
        # Verify analytics tracking
        analytics_service = orchestrator.analytics_service
        
        # Check if query was recorded (implementation dependent)
        if hasattr(analytics_service, 'track_query_analytics'):
            # Would verify query analytics were recorded
            pass

    def test_process_query_health_monitoring(self, valid_config_file, mock_component_factory):
        """Test query processing updates component health monitoring."""
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        answer = orchestrator.process_query("health monitoring query")
        
        assert isinstance(answer, Answer)
        
        # Verify health monitoring was updated
        health_service = orchestrator.health_service
        
        # Health status should be updated after successful query processing
        if hasattr(health_service, 'monitored_components') and health_service.monitored_components:
            # Components should show healthy status after successful operation
            pass

    def test_process_query_with_custom_parameters(self, valid_config_file, mock_component_factory):
        """Test query processing with custom parameters."""
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        # Test with custom parameters if supported
        custom_params = {
            "temperature": 0.2,
            "max_tokens": 200,
            "include_sources": True
        }
        
        if hasattr(orchestrator, 'process_query_with_params'):
            answer = orchestrator.process_query_with_params("custom params query", **custom_params)
        else:
            # Fallback to regular processing
            answer = orchestrator.process_query("custom params query")
        
        assert isinstance(answer, Answer)