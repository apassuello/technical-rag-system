"""
Unit tests for configuration management system.

Tests the ComponentConfig, PipelineConfig, and ConfigManager classes.
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.core.config import (
    ComponentConfig,
    PipelineConfig,
    ConfigManager,
    load_config,
    create_default_config
)


class TestComponentConfig:
    """Test ComponentConfig model."""
    
    def test_component_config_creation(self):
        """Test basic component config creation."""
        config = ComponentConfig(
            type="hybrid_pdf",
            config={"chunk_size": 1024, "overlap": 128}
        )
        assert config.type == "hybrid_pdf"
        assert config.config["chunk_size"] == 1024
        assert config.config["overlap"] == 128
    
    def test_component_config_default_config(self):
        """Test that config defaults to empty dict."""
        config = ComponentConfig(type="test")
        assert config.config == {}
    
    def test_component_config_type_validation(self):
        """Test type validation."""
        # Empty type should raise error
        with pytest.raises(ValueError, match="Component type cannot be empty"):
            ComponentConfig(type="")
        
        # Whitespace-only type should raise error
        with pytest.raises(ValueError, match="Component type cannot be empty"):
            ComponentConfig(type="   ")
        
        # Type with whitespace should be stripped
        config = ComponentConfig(type="  test  ")
        assert config.type == "test"


class TestPipelineConfig:
    """Test PipelineConfig model."""
    
    def test_pipeline_config_creation(self):
        """Test full pipeline config creation."""
        config = PipelineConfig(
            document_processor=ComponentConfig(type="pdf", config={"size": 1024}),
            embedder=ComponentConfig(type="sentence_transformer"),
            vector_store=ComponentConfig(type="faiss"),
            retriever=ComponentConfig(type="hybrid"),
            answer_generator=ComponentConfig(type="adaptive")
        )
        
        assert config.document_processor.type == "pdf"
        assert config.embedder.type == "sentence_transformer"
        assert config.vector_store.type == "faiss"
        assert config.retriever.type == "hybrid"
        assert config.answer_generator.type == "adaptive"
    
    def test_pipeline_config_global_settings(self):
        """Test global settings."""
        config = PipelineConfig(
            document_processor=ComponentConfig(type="pdf"),
            embedder=ComponentConfig(type="st"),
            vector_store=ComponentConfig(type="faiss"),
            retriever=ComponentConfig(type="hybrid"),
            answer_generator=ComponentConfig(type="adaptive"),
            global_settings={"debug": True, "log_level": "INFO"}
        )
        
        assert config.global_settings["debug"] is True
        assert config.global_settings["log_level"] == "INFO"
    
    def test_pipeline_config_forbids_extra_fields(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValueError):
            PipelineConfig(
                document_processor=ComponentConfig(type="pdf"),
                embedder=ComponentConfig(type="st"),
                vector_store=ComponentConfig(type="faiss"),
                retriever=ComponentConfig(type="hybrid"),
                answer_generator=ComponentConfig(type="adaptive"),
                unknown_field="should fail"
            )


class TestConfigManager:
    """Test ConfigManager functionality."""
    
    def test_config_manager_default_config(self):
        """Test loading default configuration."""
        manager = ConfigManager()
        config = manager._get_default_config()
        
        assert config.document_processor.type == "hybrid_pdf"
        assert config.embedder.type == "sentence_transformer"
        assert config.vector_store.type == "faiss"
        assert config.retriever.type == "hybrid"
        assert config.answer_generator.type == "adaptive"
    
    def test_config_manager_load_from_file(self):
        """Test loading from YAML file."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                "document_processor": {"type": "test_pdf", "config": {"test": True}},
                "embedder": {"type": "test_embedder", "config": {}},
                "vector_store": {"type": "test_store", "config": {}},
                "retriever": {"type": "test_retriever", "config": {}},
                "answer_generator": {"type": "test_generator", "config": {}}
            }, f)
            temp_path = Path(f.name)
        
        try:
            manager = ConfigManager(config_path=temp_path)
            config = manager.load()
            
            assert config.document_processor.type == "test_pdf"
            assert config.document_processor.config["test"] is True
        finally:
            temp_path.unlink()
    
    def test_config_manager_env_overrides(self):
        """Test environment variable overrides."""
        # Set environment variables
        os.environ['RAG_EMBEDDER__TYPE'] = 'overridden_embedder'
        os.environ['RAG_EMBEDDER__CONFIG__MODEL_NAME'] = 'test-model'
        os.environ['RAG_RETRIEVER__CONFIG__DENSE_WEIGHT'] = '0.8'
        os.environ['RAG_VECTOR_STORE__CONFIG__NORMALIZE'] = 'false'
        
        try:
            manager = ConfigManager()
            config = manager._apply_env_overrides({
                "embedder": {"type": "original", "config": {"model_name": "original-model"}},
                "retriever": {"type": "hybrid", "config": {"dense_weight": 0.7}},
                "vector_store": {"type": "faiss", "config": {"normalize": True}},
                "document_processor": {"type": "pdf", "config": {}},
                "answer_generator": {"type": "adaptive", "config": {}}
            })
            
            assert config["embedder"]["type"] == "overridden_embedder"
            assert config["embedder"]["config"]["model_name"] == "test-model"
            assert config["retriever"]["config"]["dense_weight"] == 0.8
            assert config["vector_store"]["config"]["normalize"] is False
            
        finally:
            # Clean up environment variables
            for key in ['RAG_EMBEDDER__TYPE', 'RAG_EMBEDDER__CONFIG__MODEL_NAME', 
                       'RAG_RETRIEVER__CONFIG__DENSE_WEIGHT', 'RAG_VECTOR_STORE__CONFIG__NORMALIZE']:
                os.environ.pop(key, None)
    
    def test_config_manager_save(self):
        """Test saving configuration to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_config.yaml"
            
            manager = ConfigManager()
            manager.save(output_path)
            
            assert output_path.exists()
            
            # Load and verify
            with open(output_path, 'r') as f:
                data = yaml.safe_load(f)
            
            assert data["document_processor"]["type"] == "hybrid_pdf"
            assert data["embedder"]["type"] == "sentence_transformer"
    
    def test_config_manager_get_component_config(self):
        """Test getting specific component config."""
        manager = ConfigManager()
        
        embedder_config = manager.get_component_config("embedder")
        assert embedder_config.type == "sentence_transformer"
        
        retriever_config = manager.get_component_config("retriever")
        assert retriever_config.type == "hybrid"
    
    def test_config_manager_lazy_loading(self):
        """Test that config is loaded lazily."""
        manager = ConfigManager()
        assert manager._config is None
        
        # Access config property
        config = manager.config
        assert manager._config is not None
        assert config.embedder.type == "sentence_transformer"
        
        # Second access should return cached config
        config2 = manager.config
        assert config2 is config


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_load_config_function(self):
        """Test load_config convenience function."""
        config = load_config()
        assert isinstance(config, PipelineConfig)
        assert config.document_processor.type == "hybrid_pdf"
    
    def test_create_default_config_function(self):
        """Test create_default_config function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "default.yaml"
            
            create_default_config(output_path)
            
            assert output_path.exists()
            
            # Verify it's valid YAML with comments
            content = output_path.read_text()
            assert "# RAG Pipeline Configuration" in content
            assert "document_processor:" in content
            assert "embedder:" in content
            
            # Verify it can be loaded
            manager = ConfigManager(config_path=output_path)
            config = manager.load()
            assert config.document_processor.type == "hybrid_pdf"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])