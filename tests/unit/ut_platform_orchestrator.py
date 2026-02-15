"""
Unit tests for Platform Orchestrator component.

Tests the system lifecycle management and component orchestration functionality
introduced in Phase 1 of the architecture migration.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import yaml

from src.core.platform_orchestrator import PlatformOrchestrator
from src.core.interfaces import Document, Answer, RetrievalResult


class TestPlatformOrchestrator(unittest.TestCase):
    """Test cases for PlatformOrchestrator."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary config file
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.yaml"
        
        # Create test configuration
        self.test_config = {
            "document_processor": {
                "type": "hybrid_pdf",
                "config": {"chunk_size": 1000}
            },
            "embedder": {
                "type": "sentence_transformer",
                "config": {"model": "test-model"}
            },
            "retriever": {
                "type": "unified",
                "config": {"dense_weight": 0.7}
            },
            "answer_generator": {
                "type": "adaptive",
                "config": {"model": "test-generator"}
            },
            "global_settings": {
                "platform": {
                    "name": "test",
                    "environment": "test"
                }
            }
        }
        
        # Write config to file
        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('src.core.platform_orchestrator.ComponentFactory')
    def test_initialization(self, mock_factory):
        """Test orchestrator initialization."""
        # Mock component creation
        mock_factory.create_processor.return_value = Mock()
        mock_factory.create_embedder.return_value = Mock()
        mock_factory.create_vector_store.return_value = Mock()
        mock_factory.create_retriever.return_value = Mock()
        mock_factory.create_generator.return_value = Mock()
        
        # Create orchestrator
        orchestrator = PlatformOrchestrator(self.config_path)
        
        # Verify initialization
        self.assertTrue(orchestrator._initialized)
        self.assertEqual(orchestrator.config_path, self.config_path)
        
        # Verify all components were created
        mock_factory.create_processor.assert_called_once()
        mock_factory.create_embedder.assert_called_once()
        mock_factory.create_retriever.assert_called_once()
        mock_factory.create_generator.assert_called_once()
    
    @patch('src.core.platform_orchestrator.ComponentFactory')
    def test_process_document(self, mock_factory):
        """Test document processing workflow."""
        # Create mock components
        mock_processor = Mock()
        mock_embedder = Mock()
        mock_retriever = Mock()
        
        # Set up mock returns
        test_docs = [
            Document(content="Test content", metadata={"id": "1", "source": "test.pdf"})
        ]
        mock_processor.process.return_value = test_docs
        mock_embedder.embed.return_value = [[0.1] * 384]
        
        # Configure factory - using unified retriever (no separate vector store)
        mock_factory.create_processor.return_value = mock_processor
        mock_factory.create_embedder.return_value = mock_embedder
        mock_factory.create_retriever.return_value = mock_retriever
        mock_factory.create_generator.return_value = Mock()
        
        # Create orchestrator and process document
        orchestrator = PlatformOrchestrator(self.config_path)
        
        # Create test document
        test_doc_path = Path(self.temp_dir) / "test.pdf"
        test_doc_path.touch()
        
        result = orchestrator.process_document(test_doc_path)
        
        # Verify workflow
        self.assertEqual(result, 1)
        mock_processor.process.assert_called_once_with(test_doc_path)
        mock_embedder.embed.assert_called_once_with(["Test content"])
        mock_retriever.index_documents.assert_called_once()
    
    @patch('src.core.platform_orchestrator.ComponentFactory')
    def test_process_query(self, mock_factory):
        """Test query processing workflow."""
        # Create mock components
        mock_retriever = Mock()
        mock_generator = Mock()
        
        # Set up mock returns
        test_results = [
            RetrievalResult(
                document=Document(content="Test", metadata={"id": "1", "source": "test.pdf"}),
                score=0.9,
                retrieval_method="hybrid"
            )
        ]
        mock_retriever.retrieve.return_value = test_results
        
        test_answer = Answer(
            text="Test answer",
            sources=[],
            confidence=0.8,
            metadata={}
        )
        mock_generator.generate.return_value = test_answer
        
        # Configure factory
        mock_factory.create_processor.return_value = Mock()
        mock_factory.create_embedder.return_value = Mock()
        mock_factory.create_retriever.return_value = mock_retriever
        mock_factory.create_generator.return_value = mock_generator
        
        # Create orchestrator and process query
        orchestrator = PlatformOrchestrator(self.config_path)
        answer = orchestrator.process_query("Test query", k=5)
        
        # Verify workflow
        self.assertEqual(answer.text, "Test answer")
        self.assertEqual(answer.confidence, 0.8)
        mock_retriever.retrieve.assert_called_once_with("Test query", 5)
        mock_generator.generate.assert_called_once()
    
    @patch('src.core.platform_orchestrator.ComponentFactory')
    def test_get_system_health(self, mock_factory):
        """Test system health reporting."""
        # Set up mocks
        mock_processor = Mock()
        mock_processor.__class__.__name__ = "ModularDocumentProcessor"
        mock_processor.__class__.__module__ = "components.processors"
        
        mock_factory.create_processor.return_value = mock_processor
        mock_factory.create_embedder.return_value = Mock()
        mock_factory.create_retriever.return_value = Mock()
        mock_factory.create_generator.return_value = Mock()
        
        # Create orchestrator
        orchestrator = PlatformOrchestrator(self.config_path)
        health = orchestrator.get_system_health()
        
        # Verify health info
        self.assertTrue(health["initialized"])
        self.assertEqual(health["config_path"], str(self.config_path))
        self.assertIn("components", health)
        self.assertIn("document_processor", health["components"])
    
    @patch('src.core.platform_orchestrator.ComponentFactory')
    def test_error_handling(self, mock_factory):
        """Test error handling during initialization."""
        # Make component creation fail
        mock_factory.create_processor.side_effect = Exception("Test error")
        
        # Verify initialization fails gracefully
        with self.assertRaises(RuntimeError) as context:
            PlatformOrchestrator(self.config_path)
        
        self.assertIn("System initialization failed", str(context.exception))
    
    def test_invalid_config_path(self):
        """Test handling of invalid configuration path."""
        with self.assertRaises(FileNotFoundError):
            PlatformOrchestrator(Path("/nonexistent/config.yaml"))
    
    @patch('src.core.platform_orchestrator.ComponentFactory')
    def test_component_access(self, mock_factory):
        """Test getting individual components."""
        # Set up mocks
        mock_processor = Mock()
        mock_embedder = Mock()
        
        mock_factory.create_processor.return_value = mock_processor
        mock_factory.create_embedder.return_value = mock_embedder
        mock_factory.create_retriever.return_value = Mock()
        mock_factory.create_generator.return_value = Mock()
        
        # Create orchestrator
        orchestrator = PlatformOrchestrator(self.config_path)
        
        # Test component access
        self.assertEqual(orchestrator.get_component("document_processor"), mock_processor)
        self.assertEqual(orchestrator.get_component("embedder"), mock_embedder)
        self.assertIsNone(orchestrator.get_component("nonexistent"))
    
    @patch('src.core.platform_orchestrator.ComponentFactory')
    def test_clear_index(self, mock_factory):
        """Test clearing the index."""
        # Set up mocks — retriever exposes clear_index (ModularUnifiedRetriever API)
        mock_retriever = Mock()

        mock_factory.create_processor.return_value = Mock()
        mock_factory.create_embedder.return_value = Mock()
        mock_factory.create_retriever.return_value = mock_retriever
        mock_factory.create_generator.return_value = Mock()

        # Create orchestrator and clear index
        orchestrator = PlatformOrchestrator(self.config_path)
        orchestrator.clear_index()

        # Verify clear_index was called on the retriever (unified architecture)
        mock_retriever.clear_index.assert_called_once()


if __name__ == '__main__':
    unittest.main()