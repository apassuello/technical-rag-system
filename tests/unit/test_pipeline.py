"""
Unit tests for the RAG Pipeline.

This module tests the RAGPipeline class, including component initialization,
document indexing, querying, and configuration management.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

import sys
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.core.pipeline import RAGPipeline
from src.core.interfaces import Document, RetrievalResult, Answer
from src.core.registry import ComponentRegistry
from src.core.config import PipelineConfig


class TestRAGPipeline:
    """Test cases for RAGPipeline class."""
    
    @pytest.fixture
    def mock_config_data(self):
        """Sample configuration data for testing."""
        return {
            "document_processor": {
                "type": "test_processor",
                "config": {"chunk_size": 1024}
            },
            "embedder": {
                "type": "test_embedder",
                "config": {"model_name": "test-model"}
            },
            "vector_store": {
                "type": "test_vector_store",
                "config": {"dimension": 384}
            },
            "retriever": {
                "type": "test_retriever",
                "config": {"k": 5}
            },
            "answer_generator": {
                "type": "test_generator",
                "config": {"max_tokens": 512}
            }
        }
    
    @pytest.fixture
    def temp_config_file(self, mock_config_data):
        """Create a temporary configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(mock_config_data, f)
            return Path(f.name)
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing."""
        # Mock processor
        mock_processor = Mock()
        mock_processor.process.return_value = [
            Document(
                content="Test content 1", 
                metadata={"chunk_id": 0},
                embedding=None
            ),
            Document(
                content="Test content 2", 
                metadata={"chunk_id": 1},
                embedding=None
            )
        ]
        
        # Mock embedder
        mock_embedder = Mock()
        mock_embedder.embed.return_value = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6]
        ]
        
        # Mock vector store
        mock_vector_store = Mock()
        mock_vector_store.add = Mock()
        mock_vector_store.clear = Mock()
        
        # Mock retriever
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = [
            RetrievalResult(
                document=Document(
                    content="Retrieved content",
                    metadata={"source": "test.pdf"},
                    embedding=[0.1, 0.2, 0.3]
                ),
                score=0.95,
                retrieval_method="test_method"
            )
        ]
        
        # Mock generator
        mock_generator = Mock()
        mock_generator.generate.return_value = Answer(
            text="Generated answer",
            sources=[Document(content="source", metadata={})],
            confidence=0.85,
            metadata={"model": "test"}
        )
        
        return {
            'processor': mock_processor,
            'embedder': mock_embedder,
            'vector_store': mock_vector_store,
            'retriever': mock_retriever,
            'generator': mock_generator
        }
    
    @pytest.fixture
    def mock_registry(self, mock_components):
        """Mock the ComponentRegistry for testing."""
        with patch.object(ComponentRegistry, 'create_processor') as mock_create_proc, \
             patch.object(ComponentRegistry, 'create_embedder') as mock_create_emb, \
             patch.object(ComponentRegistry, 'create_vector_store') as mock_create_vs, \
             patch.object(ComponentRegistry, 'create_retriever') as mock_create_ret, \
             patch.object(ComponentRegistry, 'create_generator') as mock_create_gen:
            
            mock_create_proc.return_value = mock_components['processor']
            mock_create_emb.return_value = mock_components['embedder']
            mock_create_vs.return_value = mock_components['vector_store']
            mock_create_ret.return_value = mock_components['retriever']
            mock_create_gen.return_value = mock_components['generator']
            
            yield {
                'create_processor': mock_create_proc,
                'create_embedder': mock_create_emb,
                'create_vector_store': mock_create_vs,
                'create_retriever': mock_create_ret,
                'create_generator': mock_create_gen
            }
    
    def test_pipeline_initialization_success(self, temp_config_file, mock_registry):
        """Test successful pipeline initialization."""
        pipeline = RAGPipeline(temp_config_file)
        
        # Verify initialization
        assert pipeline._initialized is True
        assert pipeline.config_path == temp_config_file
        
        # Verify components were created
        assert len(pipeline._components) == 5
        assert 'processor' in pipeline._components
        assert 'embedder' in pipeline._components
        assert 'vector_store' in pipeline._components
        assert 'retriever' in pipeline._components
        assert 'generator' in pipeline._components
    
    def test_pipeline_initialization_missing_config(self):
        """Test pipeline initialization with missing config file."""
        with pytest.raises(FileNotFoundError):
            RAGPipeline(Path("nonexistent_config.yaml"))
    
    def test_pipeline_initialization_registry_error(self, temp_config_file):
        """Test pipeline initialization with registry errors."""
        with patch.object(ComponentRegistry, 'create_processor', side_effect=ValueError("Unknown processor")):
            with pytest.raises(RuntimeError, match="Component initialization failed"):
                RAGPipeline(temp_config_file)
    
    def test_index_document_success(self, temp_config_file, mock_registry, mock_components):
        """Test successful document indexing."""
        pipeline = RAGPipeline(temp_config_file)
        
        # Create a test file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            test_file = Path(f.name)
        
        try:
            # Index the document
            chunk_count = pipeline.index_document(test_file)
            
            # Verify results
            assert chunk_count == 2
            mock_components['processor'].process.assert_called_once_with(test_file)
            mock_components['embedder'].embed.assert_called_once()
            mock_components['vector_store'].add.assert_called_once()
            
            # Verify embeddings were added to documents
            added_docs = mock_components['vector_store'].add.call_args[0][0]
            assert all(doc.embedding is not None for doc in added_docs)
            
        finally:
            test_file.unlink()
    
    def test_index_document_missing_file(self, temp_config_file, mock_registry):
        """Test indexing with missing file."""
        pipeline = RAGPipeline(temp_config_file)
        
        with pytest.raises(FileNotFoundError):
            pipeline.index_document(Path("nonexistent.pdf"))
    
    def test_index_document_processor_error(self, temp_config_file, mock_registry, mock_components):
        """Test indexing with processor error."""
        pipeline = RAGPipeline(temp_config_file)
        mock_components['processor'].process.side_effect = Exception("Processing failed")
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            test_file = Path(f.name)
        
        try:
            with pytest.raises(RuntimeError, match="Document indexing failed"):
                pipeline.index_document(test_file)
        finally:
            test_file.unlink()
    
    def test_index_documents_batch(self, temp_config_file, mock_registry, mock_components):
        """Test batch document indexing."""
        pipeline = RAGPipeline(temp_config_file)
        
        # Create test files
        test_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                test_files.append(Path(f.name))
        
        try:
            # Index multiple documents
            results = pipeline.index_documents(test_files)
            
            # Verify results
            assert len(results) == 3
            assert all(count == 2 for count in results.values())
            assert mock_components['processor'].process.call_count == 3
            
        finally:
            for f in test_files:
                f.unlink()
    
    def test_index_documents_partial_failure(self, temp_config_file, mock_registry, mock_components):
        """Test batch indexing with some failures."""
        pipeline = RAGPipeline(temp_config_file)
        
        # Make processor fail for specific files
        def process_side_effect(file_path):
            if "fail" in str(file_path):
                raise Exception("Processing failed")
            return [Document(content="content", metadata={}, embedding=None)]
        
        mock_components['processor'].process.side_effect = process_side_effect
        
        # Create test files
        with tempfile.NamedTemporaryFile(suffix='_fail.pdf', delete=False) as f1, \
             tempfile.NamedTemporaryFile(suffix='_success.pdf', delete=False) as f2:
            test_files = [Path(f1.name), Path(f2.name)]
        
        try:
            results = pipeline.index_documents(test_files)
            
            # Verify partial success
            assert len(results) == 2
            assert results[str(test_files[0])] == 0  # Failed file
            assert results[str(test_files[1])] == 1  # Successful file
            
        finally:
            for f in test_files:
                f.unlink()
    
    def test_query_success(self, temp_config_file, mock_registry, mock_components):
        """Test successful query processing."""
        pipeline = RAGPipeline(temp_config_file)
        
        # Execute query
        answer = pipeline.query("What is RISC-V?")
        
        # Verify results
        assert isinstance(answer, Answer)
        assert answer.text == "Generated answer"
        assert answer.confidence == 0.85
        
        # Verify component calls
        mock_components['retriever'].retrieve.assert_called_once_with("What is RISC-V?", 5)
        mock_components['generator'].generate.assert_called_once()
        
        # Verify metadata was added
        assert "query" in answer.metadata
        assert "retrieved_docs" in answer.metadata
        assert "pipeline_config" in answer.metadata
    
    def test_query_empty_query(self, temp_config_file, mock_registry):
        """Test query with empty string."""
        pipeline = RAGPipeline(temp_config_file)
        
        with pytest.raises(ValueError, match="Query cannot be empty"):
            pipeline.query("")
    
    def test_query_invalid_k(self, temp_config_file, mock_registry):
        """Test query with invalid k value."""
        pipeline = RAGPipeline(temp_config_file)
        
        with pytest.raises(ValueError, match="k must be positive"):
            pipeline.query("test query", k=0)
    
    def test_query_no_results(self, temp_config_file, mock_registry, mock_components):
        """Test query with no retrieval results."""
        pipeline = RAGPipeline(temp_config_file)
        mock_components['retriever'].retrieve.return_value = []
        
        answer = pipeline.query("test query")
        
        # Should return empty answer
        assert "No relevant information found" in answer.text
        assert answer.confidence == 0.0
        assert len(answer.sources) == 0
    
    def test_query_retriever_error(self, temp_config_file, mock_registry, mock_components):
        """Test query with retriever error."""
        pipeline = RAGPipeline(temp_config_file)
        mock_components['retriever'].retrieve.side_effect = Exception("Retrieval failed")
        
        with pytest.raises(RuntimeError, match="Query processing failed"):
            pipeline.query("test query")
    
    def test_get_component(self, temp_config_file, mock_registry, mock_components):
        """Test component access."""
        pipeline = RAGPipeline(temp_config_file)
        
        # Test valid component access
        processor = pipeline.get_component('processor')
        assert processor is mock_components['processor']
        
        # Test invalid component access
        invalid = pipeline.get_component('nonexistent')
        assert invalid is None
    
    def test_get_pipeline_info(self, temp_config_file, mock_registry, mock_components):
        """Test pipeline information retrieval."""
        pipeline = RAGPipeline(temp_config_file)
        
        info = pipeline.get_pipeline_info()
        
        # Verify info structure
        assert "config_path" in info
        assert "initialized" in info
        assert "components" in info
        assert info["initialized"] is True
        assert len(info["components"]) == 5
        
        # Verify component info
        for comp_name in ['processor', 'embedder', 'vector_store', 'retriever', 'generator']:
            assert comp_name in info["components"]
            comp_info = info["components"][comp_name]
            assert "type" in comp_info
            assert "module" in comp_info
    
    def test_clear_index(self, temp_config_file, mock_registry, mock_components):
        """Test index clearing."""
        pipeline = RAGPipeline(temp_config_file)
        
        pipeline.clear_index()
        
        mock_components['vector_store'].clear.assert_called_once()
    
    def test_clear_index_not_initialized(self, temp_config_file):
        """Test clearing index on uninitialized pipeline."""
        with patch.object(ComponentRegistry, 'create_processor', side_effect=Exception("Init failed")):
            with pytest.raises(RuntimeError):
                pipeline = RAGPipeline(temp_config_file)
        
        # This test is more complex because pipeline fails to initialize
        # We'll test this scenario differently
    
    def test_reload_config(self, temp_config_file, mock_registry, mock_components, mock_config_data):
        """Test configuration reloading."""
        pipeline = RAGPipeline(temp_config_file)
        
        # Modify config file
        modified_config = mock_config_data.copy()
        modified_config["embedder"]["config"]["model_name"] = "new-model"
        
        with open(temp_config_file, 'w') as f:
            yaml.dump(modified_config, f)
        
        # Reload configuration
        pipeline.reload_config()
        
        # Verify reinitialization
        assert pipeline._initialized is True
        assert len(pipeline._components) == 5
    
    def test_reload_config_error(self, temp_config_file, mock_registry):
        """Test configuration reload with error."""
        pipeline = RAGPipeline(temp_config_file)
        
        # Mock ConfigManager to raise an error during reload
        with patch('src.core.pipeline.ConfigManager') as mock_config_manager:
            mock_config_manager.side_effect = Exception("Config load failed")
            
            with pytest.raises(RuntimeError, match="Configuration reload failed"):
                pipeline.reload_config()
    
    def test_validate_configuration(self, temp_config_file, mock_registry):
        """Test configuration validation."""
        pipeline = RAGPipeline(temp_config_file)
        
        # Mock registry checks
        with patch.object(ComponentRegistry, 'is_registered', return_value=True):
            errors = pipeline.validate_configuration()
            assert len(errors) == 0
        
        # Test with unregistered components
        with patch.object(ComponentRegistry, 'is_registered', return_value=False):
            errors = pipeline.validate_configuration()
            assert len(errors) > 0
            assert any("not registered" in error for error in errors)
    
    def test_string_representations(self, temp_config_file, mock_registry):
        """Test string representations of pipeline."""
        pipeline = RAGPipeline(temp_config_file)
        
        # Test __str__
        str_repr = str(pipeline)
        assert "RAGPipeline" in str_repr
        assert str(temp_config_file) in str_repr
        assert "initialized=True" in str_repr
        
        # Test __repr__
        repr_str = repr(pipeline)
        assert "RAGPipeline" in repr_str
        assert "config_path" in repr_str
        assert "components=" in repr_str
    
    def test_pipeline_not_initialized_errors(self, temp_config_file):
        """Test operations on uninitialized pipeline."""
        # Create pipeline that fails to initialize
        with patch.object(ComponentRegistry, 'create_processor', side_effect=Exception("Init failed")):
            try:
                pipeline = RAGPipeline(temp_config_file)
            except RuntimeError:
                # Create a pipeline manually and set it as uninitialized
                pipeline = object.__new__(RAGPipeline)
                pipeline._initialized = False
                
                # Test operations that should fail
                with pytest.raises(RuntimeError, match="Pipeline not initialized"):
                    pipeline.index_document(Path("test.pdf"))
                
                with pytest.raises(RuntimeError, match="Pipeline not initialized"):
                    pipeline.query("test query")
                
                with pytest.raises(RuntimeError, match="Pipeline not initialized"):
                    pipeline.clear_index()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])