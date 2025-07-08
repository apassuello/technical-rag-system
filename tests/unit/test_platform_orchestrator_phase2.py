"""
Tests for Platform Orchestrator Phase 2 (Unified Retriever Support).

This test suite validates the Platform Orchestrator's ability to handle
both legacy (Phase 1) and unified (Phase 2) retriever architectures.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
import tempfile
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.core.platform_orchestrator import PlatformOrchestrator
from src.core.interfaces import Document, Answer


class TestPlatformOrchestratorPhase2:
    """Test suite for Platform Orchestrator Phase 2 features."""
    
    @pytest.fixture
    def legacy_config(self):
        """Create a legacy (Phase 1) configuration."""
        return {
            "document_processor": {
                "type": "pdf_processor",
                "config": {"chunk_size": 1000, "chunk_overlap": 200}
            },
            "embedder": {
                "type": "sentence_transformer",
                "config": {"model_name": "all-MiniLM-L6-v2", "use_mps": True}
            },
            "vector_store": {
                "type": "faiss",
                "config": {"embedding_dim": 384, "index_type": "IndexFlatIP"}
            },
            "retriever": {
                "type": "hybrid",
                "config": {"dense_weight": 0.7, "rrf_k": 10}
            },
            "answer_generator": {
                "type": "adaptive",
                "config": {"model_type": "local", "max_length": 512}
            }
        }
    
    @pytest.fixture
    def unified_config(self):
        """Create a unified (Phase 2) configuration."""
        return {
            "document_processor": {
                "type": "pdf_processor",
                "config": {"chunk_size": 1000, "chunk_overlap": 200}
            },
            "embedder": {
                "type": "sentence_transformer",
                "config": {"model_name": "all-MiniLM-L6-v2", "use_mps": True}
            },
            "retriever": {
                "type": "unified",
                "config": {
                    "dense_weight": 0.7,
                    "embedding_dim": 384,
                    "index_type": "IndexFlatIP",
                    "rrf_k": 10
                }
            },
            "answer_generator": {
                "type": "adaptive",
                "config": {"model_type": "local", "max_length": 512}
            }
        }
    
    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yield Path(f.name)
        Path(f.name).unlink()  # Clean up
    
    def create_config_file(self, config_dict, file_path):
        """Helper to create a config file."""
        with open(file_path, 'w') as f:
            yaml.dump(config_dict, f)
    
    @patch('src.core.platform_orchestrator.ComponentRegistry')
    def test_legacy_architecture_initialization(self, mock_registry, legacy_config, temp_config_file):
        """Test Platform Orchestrator with legacy architecture."""
        self.create_config_file(legacy_config, temp_config_file)
        
        # Mock component creation
        mock_registry.create_processor.return_value = Mock()
        mock_registry.create_embedder.return_value = Mock()
        mock_registry.create_vector_store.return_value = Mock()
        mock_registry.create_retriever.return_value = Mock()
        mock_registry.create_generator.return_value = Mock()
        
        orchestrator = PlatformOrchestrator(temp_config_file)
        
        # Verify legacy architecture is used
        assert orchestrator._using_unified_retriever == False
        assert 'vector_store' in orchestrator._components
        assert 'retriever' in orchestrator._components
        
        # Verify registry calls
        mock_registry.create_processor.assert_called_once()
        mock_registry.create_embedder.assert_called_once()
        mock_registry.create_vector_store.assert_called_once()
        mock_registry.create_retriever.assert_called_once()
        mock_registry.create_generator.assert_called_once()
    
    @patch('src.core.platform_orchestrator.ComponentRegistry')
    def test_unified_architecture_initialization(self, mock_registry, unified_config, temp_config_file):
        """Test Platform Orchestrator with unified architecture."""
        self.create_config_file(unified_config, temp_config_file)
        
        # Mock component creation
        mock_registry.create_processor.return_value = Mock()
        mock_registry.create_embedder.return_value = Mock()
        mock_registry.create_retriever.return_value = Mock()
        mock_registry.create_generator.return_value = Mock()
        
        orchestrator = PlatformOrchestrator(temp_config_file)
        
        # Verify unified architecture is used
        assert orchestrator._using_unified_retriever == True
        assert 'vector_store' not in orchestrator._components
        assert 'retriever' in orchestrator._components
        
        # Verify registry calls (no vector store created)
        mock_registry.create_processor.assert_called_once()
        mock_registry.create_embedder.assert_called_once()
        mock_registry.create_vector_store.assert_not_called()
        mock_registry.create_retriever.assert_called_once()
        mock_registry.create_generator.assert_called_once()
    
    @patch('src.core.platform_orchestrator.ComponentRegistry')
    def test_legacy_document_processing(self, mock_registry, legacy_config, temp_config_file):
        """Test document processing with legacy architecture."""
        self.create_config_file(legacy_config, temp_config_file)
        
        # Mock components
        mock_processor = Mock()
        mock_embedder = Mock()
        mock_vector_store = Mock()
        mock_retriever = Mock()
        
        mock_processor.process.return_value = [
            Document("Test content 1", metadata={"page": 1}),
            Document("Test content 2", metadata={"page": 2})
        ]
        mock_embedder.embed.return_value = [[0.1, 0.2], [0.3, 0.4]]
        
        mock_registry.create_processor.return_value = mock_processor
        mock_registry.create_embedder.return_value = mock_embedder
        mock_registry.create_vector_store.return_value = mock_vector_store
        mock_registry.create_retriever.return_value = mock_retriever
        mock_registry.create_generator.return_value = Mock()
        
        orchestrator = PlatformOrchestrator(temp_config_file)
        
        # Process a document
        with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_doc:
            temp_doc_path = Path(temp_doc.name)
            count = orchestrator.process_document(temp_doc_path)
        
        assert count == 2
        
        # Verify legacy workflow: vector store add called, retriever index called if supported
        mock_vector_store.add.assert_called_once()
        if hasattr(mock_retriever, 'index_documents'):
            mock_retriever.index_documents.assert_called_once()
    
    @patch('src.core.platform_orchestrator.ComponentRegistry')
    def test_unified_document_processing(self, mock_registry, unified_config, temp_config_file):
        """Test document processing with unified architecture."""
        self.create_config_file(unified_config, temp_config_file)
        
        # Mock components
        mock_processor = Mock()
        mock_embedder = Mock()
        mock_retriever = Mock()
        
        mock_processor.process.return_value = [
            Document("Test content 1", metadata={"page": 1}),
            Document("Test content 2", metadata={"page": 2})
        ]
        mock_embedder.embed.return_value = [[0.1, 0.2], [0.3, 0.4]]
        mock_retriever.index_documents = Mock()
        
        mock_registry.create_processor.return_value = mock_processor
        mock_registry.create_embedder.return_value = mock_embedder
        mock_registry.create_retriever.return_value = mock_retriever
        mock_registry.create_generator.return_value = Mock()
        
        orchestrator = PlatformOrchestrator(temp_config_file)
        
        # Process a document
        with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_doc:
            temp_doc_path = Path(temp_doc.name)
            count = orchestrator.process_document(temp_doc_path)
        
        assert count == 2
        
        # Verify unified workflow: only retriever index_documents called
        mock_retriever.index_documents.assert_called_once()
    
    @patch('src.core.platform_orchestrator.ComponentRegistry')
    def test_query_processing_compatibility(self, mock_registry, unified_config, temp_config_file):
        """Test that query processing works the same for both architectures."""
        self.create_config_file(unified_config, temp_config_file)
        
        # Mock components
        mock_retriever = Mock()
        mock_generator = Mock()
        
        mock_retriever.retrieve.return_value = [
            Mock(document=Document("Retrieved content", metadata={"source": "test.pdf"}), score=0.9)
        ]
        mock_generator.generate.return_value = Answer(
            text="Generated answer",
            sources=[Document("Source content")],
            confidence=0.8
        )
        
        mock_registry.create_processor.return_value = Mock()
        mock_registry.create_embedder.return_value = Mock()
        mock_registry.create_retriever.return_value = mock_retriever
        mock_registry.create_generator.return_value = mock_generator
        
        orchestrator = PlatformOrchestrator(temp_config_file)
        
        # Process query
        answer = orchestrator.process_query("What is RISC-V?", k=3)
        
        # Verify same interface regardless of architecture
        assert isinstance(answer, Answer)
        assert answer.text == "Generated answer"
        assert answer.confidence == 0.8
        
        # Verify components were called correctly
        mock_retriever.retrieve.assert_called_once_with("What is RISC-V?", 3)
        mock_generator.generate.assert_called_once()
    
    @patch('src.core.platform_orchestrator.ComponentRegistry')
    def test_configuration_validation(self, mock_registry, temp_config_file):
        """Test configuration validation for both architectures."""
        # Test invalid unified config (missing required fields)
        invalid_unified_config = {
            "document_processor": {"type": "pdf_processor", "config": {}},
            "embedder": {"type": "sentence_transformer", "config": {}},
            "retriever": {"type": "unified", "config": {}},  # Missing required config
            "answer_generator": {"type": "adaptive", "config": {}}
        }
        
        self.create_config_file(invalid_unified_config, temp_config_file)
        
        # Mock registry to raise error for invalid config
        mock_registry.create_retriever.side_effect = TypeError("Missing required argument")
        mock_registry.create_processor.return_value = Mock()
        mock_registry.create_embedder.return_value = Mock()
        mock_registry.create_generator.return_value = Mock()
        
        with pytest.raises(RuntimeError, match="System initialization failed"):
            PlatformOrchestrator(temp_config_file)
    
    @patch('src.core.platform_orchestrator.ComponentRegistry')
    def test_component_health_monitoring(self, mock_registry, unified_config, temp_config_file):
        """Test that health monitoring works for both architectures."""
        self.create_config_file(unified_config, temp_config_file)
        
        # Mock components
        mock_components = {
            'document_processor': Mock(),
            'embedder': Mock(),
            'retriever': Mock(),
            'answer_generator': Mock()
        }
        
        mock_registry.create_processor.return_value = mock_components['document_processor']
        mock_registry.create_embedder.return_value = mock_components['embedder']
        mock_registry.create_retriever.return_value = mock_components['retriever']
        mock_registry.create_generator.return_value = mock_components['answer_generator']
        
        orchestrator = PlatformOrchestrator(temp_config_file)
        
        # Test health monitoring
        health = orchestrator.get_system_health()
        
        assert health['status'] == 'healthy'
        assert health['initialized'] == True
        assert health['architecture'] == 'unified'
        assert len(health['components']) == 4
    
    @patch('src.core.platform_orchestrator.ComponentRegistry')
    def test_backward_compatibility_maintained(self, mock_registry, legacy_config, temp_config_file):
        """Test that legacy code continues to work unchanged."""
        self.create_config_file(legacy_config, temp_config_file)
        
        # Mock all components
        mock_registry.create_processor.return_value = Mock()
        mock_registry.create_embedder.return_value = Mock()
        mock_registry.create_vector_store.return_value = Mock()
        mock_registry.create_retriever.return_value = Mock()
        mock_registry.create_generator.return_value = Mock()
        
        # This should work exactly as in Phase 1
        orchestrator = PlatformOrchestrator(temp_config_file)
        
        assert orchestrator._initialized == True
        assert orchestrator._using_unified_retriever == False
        
        # All original components should be available
        assert 'document_processor' in orchestrator._components
        assert 'embedder' in orchestrator._components
        assert 'vector_store' in orchestrator._components
        assert 'retriever' in orchestrator._components
        assert 'answer_generator' in orchestrator._components
    
    def test_architecture_detection_logging(self, unified_config, temp_config_file, caplog):
        """Test that architecture type is properly logged."""
        self.create_config_file(unified_config, temp_config_file)
        
        import logging
        caplog.set_level(logging.INFO)
        
        with patch('src.core.platform_orchestrator.ComponentRegistry') as mock_registry:
            mock_registry.create_processor.return_value = Mock()
            mock_registry.create_embedder.return_value = Mock()
            mock_registry.create_retriever.return_value = Mock()
            mock_registry.create_generator.return_value = Mock()
            
            PlatformOrchestrator(temp_config_file)
            
            # Check that Phase 2 initialization is logged
            assert "Phase 2: Unified retriever initialized" in caplog.text


class TestPlatformOrchestratorPhase2Integration:
    """Integration tests for Phase 2 features."""
    
    def test_performance_comparison(self):
        """Test that unified architecture performs at least as well as legacy."""
        # This would be a performance benchmark comparing
        # legacy vs unified architectures
        # Implementation would depend on having actual components available
        pass
    
    def test_memory_usage_optimization(self):
        """Test that unified architecture uses less memory than legacy."""
        # This would compare memory usage between architectures
        # Implementation would depend on having actual components available
        pass
    
    def test_migration_path_validation(self):
        """Test that migration from legacy to unified is seamless."""
        # This would test actual migration scenarios
        # Implementation would depend on having actual components available
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])