"""
Phase 5.1: End-to-End Integration Tests

Comprehensive integration testing for the complete RAG system workflows.
Tests the entire pipeline from document processing to answer generation.
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from src.core.platform_orchestrator import PlatformOrchestrator
from src.core.config import ConfigManager
from src.core.interfaces import Document, Answer


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows for the RAG system."""
    
    @pytest.fixture
    def test_config_path(self):
        """Get path to test configuration."""
        return Path(__file__).parent.parent.parent / "config" / "test.yaml"
    
    @pytest.fixture
    def test_document(self):
        """Get a real test PDF document from the test data."""
        # Use existing test document from data/test directory
        test_data_dir = Path(__file__).parent.parent.parent / "data" / "test"
        available_docs = list(test_data_dir.glob("*.pdf"))
        
        if not available_docs:
            pytest.skip("No test PDF documents available")
            
        # Use first available PDF document
        return available_docs[0]
    
    @pytest.fixture
    def orchestrator(self, test_config_path):
        """Create platform orchestrator for testing."""
        return PlatformOrchestrator(test_config_path)
    
    def test_complete_document_processing_workflow(self, orchestrator, test_document):
        """Test complete document processing from PDF to indexed chunks."""
        # Process document
        chunk_count = orchestrator.process_document(test_document)
        
        # Verify document was processed
        assert chunk_count > 0, f"No chunks were processed: {chunk_count}"
        
        # Verify document is in system
        system_health = orchestrator.get_system_health()
        assert system_health["status"] == "healthy", "System should be healthy after processing"
        assert system_health["initialized"], "System should be initialized"
    
    def test_complete_query_processing_workflow(self, orchestrator, test_document):
        """Test complete query processing from question to answer."""
        # First process a document
        chunk_count = orchestrator.process_document(test_document)
        assert chunk_count > 0, "Document should be processed"
        
        # Test query processing
        query = "What is this document about?"
        answer = orchestrator.process_query(query)
        
        # Verify answer was generated
        assert isinstance(answer, Answer), "Should return Answer object"
        assert answer.text, "Answer should not be empty"
        assert answer.sources, "Answer should have sources"
        assert 0 <= answer.confidence <= 1, "Answer should have valid confidence score"
        assert isinstance(answer.metadata, dict), "Answer should have metadata"
        
        # Verify answer quality
        assert len(answer.text) > 10, "Answer should be substantial"
    
    def test_multi_document_workflow(self, orchestrator):
        """Test workflow with multiple documents."""
        # Create multiple test documents
        doc1_content = """
        # Document 1: RISC-V Basics
        RISC-V is an open instruction set architecture.
        It was developed at UC Berkeley.
        """
        
        doc2_content = """
        # Document 2: RISC-V Extensions
        RISC-V supports various extensions:
        - Vector extension
        - Compressed instruction extension
        - Floating-point extension
        """
        
        docs = []
        for i, content in enumerate([doc1_content, doc2_content], 1):
            with tempfile.NamedTemporaryFile(mode='w', suffix=f'_doc{i}.pdf', delete=False) as f:
                f.write(content)
                docs.append(Path(f.name))
        
        try:
            # Process multiple documents
            for doc in docs:
                result = orchestrator.process_document(doc)
                assert result.success, f"Failed to process {doc}"
            
            # Test query that should use information from both documents
            answer = orchestrator.process_query("What are RISC-V extensions?")
            
            # Verify answer incorporates multiple sources
            assert len(answer.sources) > 1, "Answer should use multiple sources"
            assert "extension" in answer.answer.lower(), "Answer should mention extensions"
            
            # Test another query
            answer2 = orchestrator.process_query("Where was RISC-V developed?")
            assert "berkeley" in answer2.answer.lower(), "Answer should mention Berkeley"
            
        finally:
            # Clean up
            for doc in docs:
                os.unlink(doc)
    
    def test_error_handling_workflow(self, orchestrator):
        """Test error handling in end-to-end workflows."""
        # Test with non-existent document
        non_existent = Path("/tmp/non_existent_doc.pdf")
        result = orchestrator.process_document(non_existent)
        
        assert not result.success, "Should fail with non-existent document"
        assert result.error, "Should have error message"
        
        # Test query without any documents
        answer = orchestrator.process_query("What is quantum computing?")
        
        # Should handle gracefully
        assert isinstance(answer, Answer), "Should return Answer object even without docs"
        
    def test_system_health_monitoring_workflow(self, orchestrator, test_document):
        """Test system health monitoring throughout workflow."""
        # Check initial health
        initial_health = orchestrator.get_system_health()
        assert initial_health.components_healthy, "System should be healthy initially"
        
        # Process document and check health
        orchestrator.process_document(test_document)
        post_process_health = orchestrator.get_system_health()
        assert post_process_health.components_healthy, "System should be healthy after processing"
        
        # Process query and check health
        orchestrator.process_query("What is this document about?")
        post_query_health = orchestrator.get_system_health()
        assert post_query_health.components_healthy, "System should be healthy after query"
        
        # Clean up
        os.unlink(test_document)
    
    def test_performance_metrics_workflow(self, orchestrator, test_document):
        """Test performance metrics collection throughout workflow."""
        # Process document and collect metrics
        result = orchestrator.process_document(test_document)
        assert result.processing_time > 0, "Should have processing time"
        assert result.chunks_processed > 0, "Should have chunk count"
        
        # Process query and collect metrics
        answer = orchestrator.process_query("What is RISC-V?")
        assert answer.processing_time > 0, "Should have query processing time"
        assert answer.retrieval_time > 0, "Should have retrieval time"
        
        # Clean up
        os.unlink(test_document)


class TestArchitectureCompatibility:
    """Test compatibility between different architecture configurations."""
    
    @pytest.fixture
    def unified_config(self):
        """Create unified architecture configuration."""
        return {
            "document_processor": {
                "type": "hybrid_pdf",
                "config": {"chunk_size": 512, "chunk_overlap": 64}
            },
            "embedder": {
                "type": "sentence_transformer",
                "config": {"model_name": "sentence-transformers/all-MiniLM-L6-v2"}
            },
            "retriever": {
                "type": "unified",
                "config": {
                    "dense_weight": 0.7,
                    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
                }
            },
            "answer_generator": {
                "type": "adaptive",
                "config": {"model_name": "deepset/roberta-base-squad2"}
            },
            "global_settings": {
                "environment": "test",
                "log_level": "WARNING"
            }
        }
    
    @pytest.fixture
    def legacy_config(self):
        """Create legacy architecture configuration."""
        return {
            "document_processor": {
                "type": "hybrid_pdf",
                "config": {"chunk_size": 512, "chunk_overlap": 64}
            },
            "embedder": {
                "type": "sentence_transformer",
                "config": {"model_name": "sentence-transformers/all-MiniLM-L6-v2"}
            },
            "vector_store": {
                "type": "faiss",
                "config": {"embedding_dim": 384, "index_type": "IndexFlatL2"}
            },
            "retriever": {
                "type": "hybrid",
                "config": {
                    "dense_weight": 0.7,
                    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
                }
            },
            "answer_generator": {
                "type": "adaptive",
                "config": {"model_name": "deepset/roberta-base-squad2"}
            },
            "global_settings": {
                "environment": "test",
                "log_level": "WARNING"
            }
        }
    
    def test_unified_architecture_workflow(self, unified_config):
        """Test end-to-end workflow with unified architecture."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(unified_config, f)
            config_path = Path(f.name)
        
        try:
            # Test unified architecture
            orchestrator = PlatformOrchestrator(config_path)
            
            # Create test document
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
                f.write("Test document content about RISC-V architecture.")
                doc_path = Path(f.name)
            
            try:
                # Test document processing
                result = orchestrator.process_document(doc_path)
                assert result.success, "Unified architecture should process documents"
                
                # Test query processing
                answer = orchestrator.process_query("What is RISC-V?")
                assert answer.answer, "Unified architecture should generate answers"
                
            finally:
                os.unlink(doc_path)
                
        finally:
            os.unlink(config_path)
    
    def test_architecture_comparison(self, unified_config, legacy_config):
        """Test that both architectures produce similar results."""
        # Create config files
        configs = []
        for i, config in enumerate([unified_config, legacy_config]):
            with tempfile.NamedTemporaryFile(mode='w', suffix=f'_config{i}.yaml', delete=False) as f:
                import yaml
                yaml.dump(config, f)
                configs.append(Path(f.name))
        
        # Create test document
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
            f.write("RISC-V is an open instruction set architecture.")
            doc_path = Path(f.name)
        
        try:
            results = []
            
            # Test both architectures
            for config_path in configs:
                orchestrator = PlatformOrchestrator(config_path)
                
                # Process document
                doc_result = orchestrator.process_document(doc_path)
                assert doc_result.success, f"Document processing failed for {config_path}"
                
                # Process query
                answer = orchestrator.process_query("What is RISC-V?")
                results.append(answer)
            
            # Compare results
            unified_answer, legacy_answer = results
            
            # Both should have answers
            assert unified_answer.answer, "Unified architecture should generate answer"
            assert legacy_answer.answer, "Legacy architecture should generate answer"
            
            # Both should have sources
            assert unified_answer.sources, "Unified architecture should have sources"
            assert legacy_answer.sources, "Legacy architecture should have sources"
            
            # Both should mention RISC-V
            assert "risc-v" in unified_answer.answer.lower(), "Unified answer should mention RISC-V"
            assert "risc-v" in legacy_answer.answer.lower(), "Legacy answer should mention RISC-V"
            
        finally:
            # Clean up
            for config_path in configs:
                os.unlink(config_path)
            os.unlink(doc_path)


class TestErrorRecoveryScenarios:
    """Test error handling and recovery scenarios."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator with test config."""
        config_path = Path(__file__).parent.parent.parent / "config" / "test.yaml"
        return PlatformOrchestrator(config_path)
    
    def test_invalid_document_recovery(self, orchestrator):
        """Test recovery from invalid document processing."""
        # Create invalid document (empty file)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            invalid_doc = Path(f.name)
        
        try:
            # Process invalid document
            result = orchestrator.process_document(invalid_doc)
            
            # Should handle gracefully
            assert not result.success, "Should fail with invalid document"
            assert result.error, "Should have error message"
            
            # System should still be healthy
            health = orchestrator.get_system_health()
            assert health.components_healthy, "System should remain healthy after error"
            
            # Should still be able to process queries
            answer = orchestrator.process_query("Test query")
            assert isinstance(answer, Answer), "Should still handle queries after error"
            
        finally:
            os.unlink(invalid_doc)
    
    def test_memory_pressure_recovery(self, orchestrator):
        """Test recovery from memory pressure scenarios."""
        # Create large document content
        large_content = "This is a test document. " * 1000
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
            f.write(large_content)
            large_doc = Path(f.name)
        
        try:
            # Process large document
            result = orchestrator.process_document(large_doc)
            
            # Should handle even if memory intensive
            if result.success:
                # If processing succeeded, query should also work
                answer = orchestrator.process_query("What is this document about?")
                assert isinstance(answer, Answer), "Should generate answer"
            else:
                # If processing failed due to memory, system should still be healthy
                health = orchestrator.get_system_health()
                assert health.components_healthy, "System should remain healthy"
                
        finally:
            os.unlink(large_doc)
    
    def test_concurrent_request_handling(self, orchestrator):
        """Test handling of concurrent requests."""
        # Create test document
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
            f.write("Test document about RISC-V processors.")
            doc_path = Path(f.name)
        
        try:
            # Process document first
            result = orchestrator.process_document(doc_path)
            assert result.success, "Document processing should succeed"
            
            # Simulate concurrent queries
            queries = [
                "What is RISC-V?",
                "How does RISC-V work?",
                "What are the benefits of RISC-V?"
            ]
            
            answers = []
            for query in queries:
                answer = orchestrator.process_query(query)
                answers.append(answer)
            
            # All queries should be handled
            assert len(answers) == len(queries), "Should handle all queries"
            for answer in answers:
                assert isinstance(answer, Answer), "Should return Answer objects"
                assert answer.answer, "Should generate actual answers"
                
        finally:
            os.unlink(doc_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])