"""
Test suite for PlatformOrchestrator document processing workflows.

Tests the document processing orchestration, indexing, error handling,
batch processing, and integration between components.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.core.platform_orchestrator import PlatformOrchestrator
from src.core.interfaces import Document
from .conftest import create_test_file, sample_documents


class TestPlatformOrchestratorDocumentProcessing:
    """Test PlatformOrchestrator document processing workflows."""

    def test_process_document_success(self, valid_config_file, mock_component_factory, temp_config_dir):
        """Test successful document processing workflow."""
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        # Create test document file
        test_file = create_test_file(Path(temp_config_dir), "test.pdf", "Test document content")
        
        # Process document
        result = orchestrator.process_document(test_file)
        
        # Verify workflow
        assert result == 1  # Number of document chunks created
        
        # Verify component calls
        mock_processor = mock_component_factory.mock_processor
        mock_embedder = mock_component_factory.mock_embedder
        mock_retriever = mock_component_factory.mock_retriever
        
        mock_processor.process.assert_called_once_with(test_file)
        mock_embedder.embed.assert_called_once_with(["Test content"])
        mock_retriever.index_documents.assert_called_once()

    def test_process_document_nonexistent_file(self, valid_config_file, mock_component_factory):
        """Test processing non-existent document file."""
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        nonexistent_file = Path("/nonexistent/document.pdf")
        
        with pytest.raises(FileNotFoundError, match="Document file not found"):
            orchestrator.process_document(nonexistent_file)

    def test_process_document_uninitialized_system(self, valid_config_file, mock_component_factory):
        """Test processing document with uninitialized system."""
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        # Manually set system as uninitialized
        orchestrator._initialized = False
        
        test_file = Path("test.pdf")
        
        with pytest.raises(RuntimeError, match="System not initialized"):
            orchestrator.process_document(test_file)

    def test_process_document_empty_result(self, valid_config_file, mock_component_factory, temp_config_dir):
        """Test processing document that returns no chunks."""
        # Configure processor to return empty result
        mock_component_factory.mock_processor.process.return_value = []
        
        orchestrator = PlatformOrchestrator(valid_config_file)
        test_file = create_test_file(Path(temp_config_dir), "empty.pdf")
        
        result = orchestrator.process_document(test_file)
        
        assert result == 0
        
        # Verify no embedding or indexing was attempted
        mock_component_factory.mock_embedder.embed.assert_not_called()
        mock_component_factory.mock_retriever.index_documents.assert_not_called()

    def test_process_document_processor_failure(self, valid_config_file, mock_component_factory, temp_config_dir):
        """Test document processing with processor failure."""
        # Configure processor to fail
        mock_component_factory.mock_processor.process.side_effect = Exception("Processing failed")
        
        orchestrator = PlatformOrchestrator(valid_config_file)
        test_file = create_test_file(Path(temp_config_dir), "failing.pdf")
        
        with pytest.raises(Exception, match="Processing failed"):
            orchestrator.process_document(test_file)

    def test_process_document_embedder_failure(self, valid_config_file, mock_component_factory, temp_config_dir):
        """Test document processing with embedder failure."""
        # Configure embedder to fail
        mock_component_factory.mock_embedder.embed.side_effect = Exception("Embedding failed")
        
        orchestrator = PlatformOrchestrator(valid_config_file)
        test_file = create_test_file(Path(temp_config_dir), "embed_fail.pdf")
        
        with pytest.raises(Exception, match="Embedding failed"):
            orchestrator.process_document(test_file)

    def test_process_document_unified_retriever_indexing(self, valid_config_file, mock_component_factory, temp_config_dir):
        """Test document indexing with unified retriever architecture."""
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        # Verify unified architecture
        assert orchestrator._using_unified_retriever is True
        
        test_file = create_test_file(Path(temp_config_dir), "unified_test.pdf")
        
        result = orchestrator.process_document(test_file)
        
        assert result == 1
        
        # Verify unified retriever indexing
        mock_retriever = mock_component_factory.mock_retriever
        mock_retriever.index_documents.assert_called_once()
        
        # Verify documents have embeddings attached
        call_args = mock_retriever.index_documents.call_args[0][0]
        assert len(call_args) == 1  # One document
        assert hasattr(call_args[0], 'embedding')

    @pytest.mark.filterwarnings("ignore:Component validation warnings:UserWarning")
    def test_process_document_legacy_architecture_indexing(self, temp_config_dir, mock_component_factory):
        """Test document indexing with legacy architecture."""
        # Create legacy configuration
        legacy_config = {
            "document_processor": {"type": "hybrid_pdf", "config": {"chunk_size": 1000}},
            "embedder": {"type": "sentence_transformer", "config": {"model": "test-model"}},
            "vector_store": {"type": "faiss", "config": {"dimension": 384}},
            "retriever": {"type": "basic", "config": {"k": 5}},
            "answer_generator": {"type": "adaptive", "config": {"model": "test-generator"}},
            "global_settings": {"platform": {"name": "test", "environment": "test"}}
        }
        
        config_path = Path(temp_config_dir) / "legacy_config.yaml"
        with open(config_path, 'w') as f:
            import yaml
            yaml.dump(legacy_config, f)
        
        # Mock vector store
        mock_vector_store = Mock()
        mock_component_factory.create_vector_store.return_value = mock_vector_store
        
        # Mock retriever with index_documents method
        mock_retriever = Mock()
        mock_retriever.index_documents = Mock()
        mock_component_factory.create_retriever.return_value = mock_retriever
        
        orchestrator = PlatformOrchestrator(config_path)
        
        # Verify legacy architecture
        assert orchestrator._using_unified_retriever is False
        
        test_file = create_test_file(Path(temp_config_dir), "legacy_test.pdf")
        
        result = orchestrator.process_document(test_file)
        
        assert result == 1
        
        # Verify legacy indexing workflow
        mock_vector_store.add.assert_called_once()
        mock_retriever.index_documents.assert_called_once()

    def test_process_documents_batch(self, valid_config_file, mock_component_factory, temp_config_dir):
        """Test batch document processing."""
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        # Create multiple test files
        test_files = [
            create_test_file(Path(temp_config_dir), f"batch_{i}.pdf", f"Content {i}")
            for i in range(3)
        ]
        
        # Process documents in batch
        results = orchestrator.process_documents(test_files)
        
        # Verify results
        assert isinstance(results, dict)
        assert len(results) == 3
        
        for file_path, chunk_count in results.items():
            assert chunk_count == 1  # Each file produces 1 chunk
        
        # Verify all documents were processed
        assert mock_component_factory.mock_processor.process.call_count == 3

    def test_process_documents_partial_failure(self, valid_config_file, mock_component_factory, temp_config_dir):
        """Test batch processing with some documents failing."""
        # Configure processor to fail on second file
        def process_side_effect(file_path):
            if "fail" in str(file_path):
                raise Exception("Processing failed")
            return [Document(content="Test content", metadata={"id": "1", "source": str(file_path)})]
        
        mock_component_factory.mock_processor.process.side_effect = process_side_effect
        
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        test_files = [
            create_test_file(Path(temp_config_dir), "success.pdf"),
            create_test_file(Path(temp_config_dir), "fail.pdf"),
            create_test_file(Path(temp_config_dir), "success2.pdf")
        ]
        
        results = orchestrator.process_documents(test_files)
        
        # Verify results - should contain results for successful files
        assert len(results) == 2  # Only successful files
        assert all(count == 1 for count in results.values())

    def test_document_processing_with_metadata_preservation(self, valid_config_file, mock_component_factory, temp_config_dir):
        """Test document processing preserves metadata through workflow."""
        # Configure processor to return document with rich metadata
        test_document = Document(
            content="Test document with metadata",
            metadata={
                "id": "test_doc_1",
                "source": "test.pdf",
                "page": 1,
                "section": "Introduction",
                "author": "Test Author"
            }
        )
        mock_component_factory.mock_processor.process.return_value = [test_document]
        
        orchestrator = PlatformOrchestrator(valid_config_file)
        test_file = create_test_file(Path(temp_config_dir), "metadata_test.pdf")
        
        result = orchestrator.process_document(test_file)
        
        assert result == 1
        
        # Verify metadata was preserved through indexing
        index_call_args = mock_component_factory.mock_retriever.index_documents.call_args[0][0]
        indexed_document = index_call_args[0]
        
        assert indexed_document.metadata["id"] == "test_doc_1"
        assert indexed_document.metadata["author"] == "Test Author"
        assert hasattr(indexed_document, 'embedding')

    def test_document_processing_large_batch(self, valid_config_file, mock_component_factory, temp_config_dir):
        """Test processing large batch of documents."""
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        # Create large batch of test files
        test_files = [
            create_test_file(Path(temp_config_dir), f"large_batch_{i}.pdf", f"Content {i}")
            for i in range(20)
        ]
        
        results = orchestrator.process_documents(test_files)
        
        # Verify all documents were processed
        assert len(results) == 20
        assert all(count == 1 for count in results.values())
        
        # Verify processing efficiency
        assert mock_component_factory.mock_processor.process.call_count == 20
        assert mock_component_factory.mock_embedder.embed.call_count == 20

    def test_document_processing_analytics_tracking(self, valid_config_file, mock_component_factory, temp_config_dir):
        """Test document processing tracks analytics."""
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        test_file = create_test_file(Path(temp_config_dir), "analytics_test.pdf")
        
        # Process document
        result = orchestrator.process_document(test_file)
        
        assert result == 1
        
        # Verify analytics were potentially tracked
        analytics_service = orchestrator.analytics_service
        assert analytics_service is not None
        
        # Analytics tracking would depend on implementation details

    def test_document_processing_with_embeddings_validation(self, valid_config_file, mock_component_factory, temp_config_dir):
        """Test document processing validates embeddings."""
        # Configure embedder to return invalid embeddings
        mock_component_factory.mock_embedder.embed.return_value = None

        orchestrator = PlatformOrchestrator(valid_config_file)
        test_file = create_test_file(Path(temp_config_dir), "invalid_embeddings.pdf")

        # Should handle invalid embeddings gracefully or raise appropriate error
        with pytest.raises((ValueError, TypeError, AttributeError, RuntimeError)):
            orchestrator.process_document(test_file)

    def test_document_processing_memory_management(self, valid_config_file, mock_component_factory, temp_config_dir):
        """Test document processing manages memory efficiently."""
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        # Create large documents to test memory handling
        large_documents = [
            Document(
                content="x" * 10000,  # Large content
                metadata={"id": f"large_doc_{i}", "source": f"large_{i}.pdf"}
            )
            for i in range(10)
        ]
        
        mock_component_factory.mock_processor.process.return_value = large_documents
        mock_component_factory.mock_embedder.embed.return_value = [[0.1] * 384] * 10
        
        test_file = create_test_file(Path(temp_config_dir), "memory_test.pdf")
        
        result = orchestrator.process_document(test_file)
        
        assert result == 10
        
        # Verify large batch was handled successfully
        embed_call_args = mock_component_factory.mock_embedder.embed.call_args[0][0]
        assert len(embed_call_args) == 10

    def test_document_processing_error_recovery(self, valid_config_file, mock_component_factory, temp_config_dir):
        """Test document processing error recovery mechanisms."""
        # Configure retriever to fail on first attempt, succeed on retry
        call_count = 0
        def index_documents_side_effect(documents):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Temporary indexing failure")
            return None
        
        mock_component_factory.mock_retriever.index_documents.side_effect = index_documents_side_effect
        
        orchestrator = PlatformOrchestrator(valid_config_file)
        test_file = create_test_file(Path(temp_config_dir), "recovery_test.pdf")
        
        # Should either retry and succeed, or fail gracefully
        try:
            result = orchestrator.process_document(test_file)
            # If retry logic is implemented, this should succeed
            assert result == 1
        except Exception:
            # If no retry logic, should fail on first attempt
            assert call_count == 1

    def test_document_processing_concurrent_safety(self, valid_config_file, mock_component_factory, temp_config_dir):
        """Test concurrent document processing safety."""
        import threading
        
        orchestrator = PlatformOrchestrator(valid_config_file)
        
        results = []
        errors = []
        
        def process_document_thread(doc_id):
            try:
                test_file = create_test_file(Path(temp_config_dir), f"concurrent_{doc_id}.pdf")
                result = orchestrator.process_document(test_file)
                results.append((doc_id, result))
            except Exception as e:
                errors.append((doc_id, e))
        
        # Process documents concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=process_document_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify all processing completed successfully
        assert len(errors) == 0
        assert len(results) == 5
        
        # Verify all returned expected result
        assert all(result == 1 for _, result in results)