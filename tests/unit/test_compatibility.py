"""
Unit tests for the backward compatibility layer.

Tests that the legacy RAGPipeline API continues to work correctly
while delegating to the new Platform Orchestrator architecture.
"""

import unittest
from unittest.mock import Mock, patch, call
from pathlib import Path
import warnings
import tempfile
import yaml

from src.core.compatibility import RAGPipelineCompatibility
from src.core.pipeline import RAGPipeline
from src.core.interfaces import Document, Answer, RetrievalResult


class TestCompatibilityLayer(unittest.TestCase):
    """Test cases for RAGPipeline compatibility layer."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary config file
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.yaml"
        
        # Create test configuration
        self.test_config = {
            "document_processor": {"type": "hybrid_pdf", "config": {}},
            "embedder": {"type": "sentence_transformer", "config": {}},
            "vector_store": {"type": "faiss", "config": {}},
            "retriever": {"type": "hybrid", "config": {}},
            "answer_generator": {"type": "adaptive", "config": {}}
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('src.core.compatibility.PlatformOrchestrator')
    def test_initialization_with_deprecation_warning(self, mock_orchestrator_class):
        """Test that initialization issues deprecation warning."""
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator
        
        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Create compatibility layer
            compat = RAGPipelineCompatibility(self.config_path)
            
            # Verify deprecation warning was issued
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[0].category, DeprecationWarning))
            self.assertIn("RAGPipeline is deprecated", str(w[0].message))
            self.assertIn("PlatformOrchestrator", str(w[0].message))
    
    @patch('src.core.compatibility.PlatformOrchestrator')
    def test_index_document_delegation(self, mock_orchestrator_class):
        """Test index_document delegates to process_document."""
        mock_orchestrator = Mock()
        mock_orchestrator.process_document.return_value = 10
        mock_orchestrator_class.return_value = mock_orchestrator
        
        # Create compatibility layer
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            compat = RAGPipelineCompatibility(self.config_path)
        
        # Test document indexing with warning
        test_path = Path("test.pdf")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = compat.index_document(test_path)
        
        # Verify delegation
        self.assertEqual(result, 10)
        mock_orchestrator.process_document.assert_called_once_with(test_path)
        
        # Verify deprecation warning
        self.assertTrue(any("index_document() is deprecated" in str(warning.message) for warning in w))
    
    @patch('src.core.compatibility.PlatformOrchestrator')
    def test_index_documents_delegation(self, mock_orchestrator_class):
        """Test index_documents delegates to process_documents."""
        mock_orchestrator = Mock()
        # Mock process_documents to return the expected dictionary
        mock_orchestrator.process_documents.return_value = {
            "doc1.pdf": 5,
            "doc2.pdf": 10,
            "doc3.pdf": 0
        }
        mock_orchestrator_class.return_value = mock_orchestrator
        
        # Create compatibility layer
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            compat = RAGPipelineCompatibility(self.config_path)
        
        # Test batch indexing
        test_paths = [Path("doc1.pdf"), Path("doc2.pdf"), Path("doc3.pdf")]
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            results = compat.index_documents(test_paths)
        
        # Verify results
        self.assertEqual(results, {
            "doc1.pdf": 5,
            "doc2.pdf": 10,
            "doc3.pdf": 0
        })
        
        # Verify delegation
        mock_orchestrator.process_documents.assert_called_once_with(test_paths)
        
        # Verify deprecation warning
        self.assertTrue(any("index_documents() is deprecated" in str(warning.message) for warning in w))
    
    @patch('src.core.compatibility.PlatformOrchestrator')
    @patch('src.core.compatibility.QueryProcessor')
    def test_query_delegation(self, mock_query_processor_class, mock_orchestrator_class):
        """Test query delegates to QueryProcessor."""
        # Set up mocks
        mock_orchestrator = Mock()
        mock_retriever = Mock()
        mock_generator = Mock()
        mock_orchestrator.get_component.side_effect = lambda name: {
            'retriever': mock_retriever,
            'answer_generator': mock_generator
        }.get(name)
        mock_orchestrator_class.return_value = mock_orchestrator
        
        mock_query_processor = Mock()
        test_answer = Answer(text="Test answer", sources=[], confidence=0.8, metadata={})
        mock_query_processor.process.return_value = test_answer
        mock_query_processor_class.return_value = mock_query_processor
        
        # Create compatibility layer
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            compat = RAGPipelineCompatibility(self.config_path)
        
        # Test query
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = compat.query("Test query", k=3)
        
        # Verify result
        self.assertEqual(result, test_answer)
        mock_query_processor.process.assert_called_once_with("Test query", 3)
        
        # Verify deprecation warning
        self.assertTrue(any("query() is deprecated" in str(warning.message) for warning in w))
    
    @patch('src.core.compatibility.PlatformOrchestrator')
    def test_get_component_with_mapping(self, mock_orchestrator_class):
        """Test get_component with name mapping."""
        mock_orchestrator = Mock()
        mock_component = Mock()
        mock_orchestrator.get_component.return_value = mock_component
        mock_orchestrator_class.return_value = mock_orchestrator
        
        # Create compatibility layer
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            compat = RAGPipelineCompatibility(self.config_path)
        
        # Test component access with old name
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = compat.get_component("processor")
        
        # Verify mapping
        self.assertEqual(result, mock_component)
        mock_orchestrator.get_component.assert_called_with("document_processor")
        
        # Test with new name
        result = compat.get_component("embedder")
        mock_orchestrator.get_component.assert_called_with("embedder")
    
    @patch('src.core.compatibility.PlatformOrchestrator')
    def test_get_pipeline_info_transformation(self, mock_orchestrator_class):
        """Test get_pipeline_info transforms system health."""
        mock_orchestrator = Mock()
        mock_orchestrator.get_system_health.return_value = {
            "initialized": True,
            "config_path": "/path/to/config",
            "components": {"test": "components"},
            "platform": {"name": "test"}
        }
        mock_orchestrator_class.return_value = mock_orchestrator
        
        # Create compatibility layer
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            compat = RAGPipelineCompatibility(self.config_path)
        
        # Get pipeline info
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            info = compat.get_pipeline_info()
        
        # Verify transformation
        self.assertEqual(info["config_path"], "/path/to/config")
        self.assertEqual(info["initialized"], True)
        self.assertEqual(info["components"], {"test": "components"})
        self.assertNotIn("platform", info)  # Platform info should be excluded
    
    @patch('src.core.compatibility.PlatformOrchestrator')
    def test_clear_index_delegation(self, mock_orchestrator_class):
        """Test clear_index delegation."""
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator
        
        # Create compatibility layer
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            compat = RAGPipelineCompatibility(self.config_path)
        
        # Clear index
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            compat.clear_index()
        
        # Verify delegation
        mock_orchestrator.clear_index.assert_called_once()
    
    @patch('src.core.compatibility.PlatformOrchestrator')
    def test_reload_config_delegation(self, mock_orchestrator_class):
        """Test reload_config delegation and query processor recreation."""
        mock_orchestrator = Mock()
        mock_retriever = Mock()
        mock_generator = Mock()
        mock_orchestrator.get_component.side_effect = lambda name: {
            'retriever': mock_retriever,
            'answer_generator': mock_generator
        }.get(name)
        mock_orchestrator_class.return_value = mock_orchestrator
        
        # Create compatibility layer
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            compat = RAGPipelineCompatibility(self.config_path)
        
        # Reload config
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            compat.reload_config()
        
        # Verify delegation
        mock_orchestrator.reload_config.assert_called_once()
        
        # Verify query processor was recreated
        self.assertIsNotNone(compat.query_processor)
    
    def test_ragpipeline_class_compatibility(self):
        """Test that RAGPipeline class from pipeline module works."""
        # Test importing and using the legacy class
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # This should work but issue warnings
            with patch('src.core.compatibility.PlatformOrchestrator'):
                pipeline = RAGPipeline(self.config_path)
                
        # Should have warnings about deprecated module and class
        self.assertTrue(len(w) >= 1)
        self.assertTrue(any("deprecated" in str(warning.message) for warning in w))
    
    @patch('src.core.compatibility.PlatformOrchestrator')
    def test_property_access_warnings(self, mock_orchestrator_class):
        """Test that accessing internal properties issues warnings."""
        mock_orchestrator = Mock()
        mock_orchestrator._components = {"test": "component"}
        mock_orchestrator._initialized = True
        mock_orchestrator_class.return_value = mock_orchestrator
        
        # Create compatibility layer
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            compat = RAGPipelineCompatibility(self.config_path)
        
        # Access _components property
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            components = compat._components
        
        self.assertEqual(components, {"test": "component"})
        self.assertTrue(any("_components is deprecated" in str(warning.message) for warning in w))
        
        # Access _initialized property
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            initialized = compat._initialized
        
        self.assertEqual(initialized, True)
        self.assertTrue(any("_initialized is deprecated" in str(warning.message) for warning in w))


if __name__ == '__main__':
    unittest.main()