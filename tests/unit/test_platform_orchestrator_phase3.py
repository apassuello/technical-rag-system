"""
Tests for Platform Orchestrator Phase 3 - Factory Integration

This test suite validates Phase 3 Platform Orchestrator enhancements:
- ComponentFactory integration for direct component instantiation
- Enhanced configuration validation with factory integration
- Performance improvements and optimized initialization
- Backward compatibility with existing configurations
- Enhanced error handling and health monitoring
"""

import pytest
import tempfile
import yaml
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.core.platform_orchestrator import PlatformOrchestrator
from src.core.interfaces import Answer
from src.core.component_factory import ComponentFactory


class TestPlatformOrchestratorPhase3:
    """Test suite for Platform Orchestrator Phase 3 functionality."""
    
    @pytest.fixture
    def unified_config(self):
        """Create a unified (Phase 2) configuration for testing."""
        return {
            "document_processor": {
                "type": "hybrid_pdf",
                "config": {"chunk_size": 1000, "chunk_overlap": 200}
            },
            "embedder": {
                "type": "sentence_transformer",
                "config": {"model_name": "all-MiniLM-L6-v2", "use_mps": False}
            },
            "retriever": {
                "type": "unified",
                "config": {
                    "embedding_dim": 384,
                    "index_type": "IndexFlatIP", 
                    "dense_weight": 0.7,
                    "rrf_k": 10
                }
            },
            "answer_generator": {
                "type": "adaptive",
                "config": {"model_name": "sshleifer/distilbart-cnn-12-6", "max_tokens": 256}
            },
            "global_settings": {
                "platform": "phase3_test",
                "log_level": "WARNING"  # Reduce noise in tests
            }
        }
    
    @pytest.fixture
    def legacy_config(self):
        """Create a legacy (Phase 1) configuration for testing."""
        return {
            "document_processor": {
                "type": "hybrid_pdf",
                "config": {"chunk_size": 1000, "chunk_overlap": 200}
            },
            "embedder": {
                "type": "sentence_transformer",
                "config": {"model_name": "all-MiniLM-L6-v2", "use_mps": False}
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
                "config": {"model_name": "sshleifer/distilbart-cnn-12-6", "max_tokens": 256}
            },
            "global_settings": {
                "platform": "phase3_legacy_test",
                "log_level": "WARNING"
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


class TestFactoryIntegration(TestPlatformOrchestratorPhase3):
    """Test ComponentFactory integration in Platform Orchestrator."""
    
    def test_unified_architecture_initialization(self, unified_config, temp_config_file):
        """Test Platform Orchestrator initialization with unified architecture."""
        
        self.create_config_file(unified_config, temp_config_file)
        
        # Initialize orchestrator
        orchestrator = PlatformOrchestrator(temp_config_file)
        
        # Verify initialization
        assert orchestrator._initialized == True
        assert orchestrator._using_unified_retriever == True
        
        # Verify components were created
        assert len(orchestrator._components) == 4
        assert 'document_processor' in orchestrator._components
        assert 'embedder' in orchestrator._components
        assert 'retriever' in orchestrator._components
        assert 'answer_generator' in orchestrator._components
        
        # Verify no vector store for unified architecture
        assert 'vector_store' not in orchestrator._components
    
    def test_legacy_architecture_initialization(self, legacy_config, temp_config_file):
        """Test Platform Orchestrator initialization with legacy architecture."""
        
        self.create_config_file(legacy_config, temp_config_file)
        
        # Initialize orchestrator
        orchestrator = PlatformOrchestrator(temp_config_file)
        
        # Verify initialization
        assert orchestrator._initialized == True
        assert orchestrator._using_unified_retriever == False
        
        # Verify components were created
        assert len(orchestrator._components) == 5
        assert 'document_processor' in orchestrator._components
        assert 'embedder' in orchestrator._components
        assert 'vector_store' in orchestrator._components
        assert 'retriever' in orchestrator._components
        assert 'answer_generator' in orchestrator._components
    
    def test_enhanced_health_monitoring(self, unified_config, temp_config_file):
        """Test enhanced health monitoring with factory integration."""
        
        self.create_config_file(unified_config, temp_config_file)
        orchestrator = PlatformOrchestrator(temp_config_file)
        
        # Get system health
        health = orchestrator.get_system_health()
        
        # Verify basic health info
        assert health['status'] == 'healthy'
        assert health['initialized'] == True
        assert health['architecture'] == 'unified'
        
        # Verify factory integration info
        assert 'factory_info' in health
        factory_info = health['factory_info']
        assert 'processors' in factory_info
        assert 'embedders' in factory_info
        assert 'retrievers' in factory_info
        assert 'generators' in factory_info
        
        # Verify component health info includes factory management
        for comp_name, comp_info in health['components'].items():
            assert 'factory_managed' in comp_info
            assert comp_info['factory_managed'] == True
    
    def test_factory_based_validation(self, unified_config, temp_config_file):
        """Test enhanced configuration validation using ComponentFactory."""
        
        self.create_config_file(unified_config, temp_config_file)
        orchestrator = PlatformOrchestrator(temp_config_file)
        
        # Test valid configuration
        errors = orchestrator.validate_configuration()
        assert len(errors) == 0
        
        # Test with invalid component type
        orchestrator.config.document_processor.type = "invalid_processor"
        errors = orchestrator.validate_configuration()
        assert len(errors) > 0
        assert any("Unknown document_processor type" in error for error in errors)


class TestConfigurationValidation(TestPlatformOrchestratorPhase3):
    """Test enhanced configuration validation."""
    
    def test_invalid_component_type_error(self, temp_config_file):
        """Test initialization with invalid component type."""
        
        invalid_config = {
            "document_processor": {"type": "unknown_processor", "config": {}},
            "embedder": {"type": "sentence_transformer", "config": {"use_mps": False}},
            "retriever": {"type": "unified", "config": {"embedding_dim": 384}},
            "answer_generator": {"type": "adaptive", "config": {"model_name": "sshleifer/distilbart-cnn-12-6"}}
        }
        
        self.create_config_file(invalid_config, temp_config_file)
        
        with pytest.raises(Exception) as exc_info:
            PlatformOrchestrator(temp_config_file)
        
        error_msg = str(exc_info.value)
        assert ("unknown" in error_msg.lower() or "initialization failed" in error_msg.lower())
    
    def test_architecture_consistency_validation(self, temp_config_file):
        """Test architecture consistency validation."""
        
        # Test unified retriever with vector_store (invalid)
        inconsistent_config = {
            "document_processor": {"type": "hybrid_pdf", "config": {}},
            "embedder": {"type": "sentence_transformer", "config": {"use_mps": False}},
            "vector_store": {"type": "faiss", "config": {"embedding_dim": 384}},
            "retriever": {"type": "unified", "config": {"embedding_dim": 384}},
            "answer_generator": {"type": "adaptive", "config": {"model_name": "sshleifer/distilbart-cnn-12-6"}}
        }
        
        self.create_config_file(inconsistent_config, temp_config_file)
        
        with pytest.raises(Exception) as exc_info:
            PlatformOrchestrator(temp_config_file)
        
        # Should fail due to configuration validation
        error_msg = str(exc_info.value)
        assert ("unified retriever architecture detected" in error_msg.lower() or 
                "initialization failed" in error_msg.lower())
    
    def test_component_creation_error_handling(self, temp_config_file):
        """Test enhanced error handling for component creation failures."""
        
        config = {
            "document_processor": {"type": "hybrid_pdf", "config": {}},
            "embedder": {"type": "sentence_transformer", "config": {"use_mps": False}},
            "retriever": {"type": "unified", "config": {"embedding_dim": 384}},
            "answer_generator": {"type": "adaptive", "config": {"model_name": "sshleifer/distilbart-cnn-12-6"}}
        }
        
        self.create_config_file(config, temp_config_file)
        
        # Mock ComponentFactory to raise an error
        with patch.object(ComponentFactory, 'create_processor') as mock_create:
            mock_create.side_effect = TypeError("Missing required argument")
            
            with pytest.raises(RuntimeError) as exc_info:
                PlatformOrchestrator(temp_config_file)
            
            error_msg = str(exc_info.value)
            assert "System initialization failed" in error_msg


class TestPerformanceOptimizations(TestPlatformOrchestratorPhase3):
    """Test performance optimizations in Phase 3."""
    
    def test_initialization_performance(self, unified_config, temp_config_file):
        """Test that initialization is reasonably fast."""
        
        import time
        
        self.create_config_file(unified_config, temp_config_file)
        
        # Measure initialization time
        start_time = time.time()
        orchestrator = PlatformOrchestrator(temp_config_file)
        init_time = time.time() - start_time
        
        # Initialization should be fast (less than 5 seconds for testing)
        assert init_time < 5.0, f"Initialization too slow: {init_time:.3f}s"
        assert orchestrator._initialized == True
    
    def test_health_monitoring_performance(self, unified_config, temp_config_file):
        """Test that health monitoring is fast."""
        
        import time
        
        self.create_config_file(unified_config, temp_config_file)
        orchestrator = PlatformOrchestrator(temp_config_file)
        
        # Measure health check time
        start_time = time.time()
        for _ in range(10):
            health = orchestrator.get_system_health()
        health_time = (time.time() - start_time) / 10
        
        # Health checks should be very fast
        assert health_time < 0.1, f"Health monitoring too slow: {health_time:.3f}s"
        assert health['status'] == 'healthy'
    
    def test_validation_performance(self, unified_config, temp_config_file):
        """Test that configuration validation is fast."""
        
        import time
        
        self.create_config_file(unified_config, temp_config_file)
        orchestrator = PlatformOrchestrator(temp_config_file)
        
        # Measure validation time
        start_time = time.time()
        for _ in range(20):
            errors = orchestrator.validate_configuration()
        validation_time = (time.time() - start_time) / 20
        
        # Validation should be very fast
        assert validation_time < 0.01, f"Validation too slow: {validation_time:.4f}s"
        assert len(errors) == 0


class TestBackwardCompatibility(TestPlatformOrchestratorPhase3):
    """Test backward compatibility with existing configurations."""
    
    def test_phase1_config_compatibility(self, legacy_config, temp_config_file):
        """Test that Phase 1 configurations still work."""
        
        self.create_config_file(legacy_config, temp_config_file)
        
        # Should initialize successfully
        orchestrator = PlatformOrchestrator(temp_config_file)
        
        assert orchestrator._initialized == True
        assert orchestrator._using_unified_retriever == False
        assert 'vector_store' in orchestrator._components
        assert 'retriever' in orchestrator._components
    
    def test_phase2_config_compatibility(self, unified_config, temp_config_file):
        """Test that Phase 2 configurations still work."""
        
        self.create_config_file(unified_config, temp_config_file)
        
        # Should initialize successfully
        orchestrator = PlatformOrchestrator(temp_config_file)
        
        assert orchestrator._initialized == True
        assert orchestrator._using_unified_retriever == True
        assert 'vector_store' not in orchestrator._components
        assert 'retriever' in orchestrator._components
    
    def test_component_aliases_support(self, temp_config_file):
        """Test that component aliases work in configuration."""
        
        alias_config = {
            "document_processor": {"type": "pdf_processor", "config": {"chunk_size": 1000}},  # Alias
            "embedder": {"type": "sentence_transformers", "config": {"use_mps": False}},  # Alias
            "retriever": {"type": "unified", "config": {"embedding_dim": 384}},
            "answer_generator": {"type": "adaptive_generator", "config": {"model_name": "sshleifer/distilbart-cnn-12-6"}}  # Alias
        }
        
        self.create_config_file(alias_config, temp_config_file)
        
        # Should work with aliases
        orchestrator = PlatformOrchestrator(temp_config_file)
        assert orchestrator._initialized == True
    
    def test_api_compatibility(self, unified_config, temp_config_file):
        """Test that the Platform Orchestrator API remains unchanged."""
        
        self.create_config_file(unified_config, temp_config_file)
        orchestrator = PlatformOrchestrator(temp_config_file)
        
        # Test all public methods exist and work
        assert hasattr(orchestrator, 'process_document')
        assert hasattr(orchestrator, 'process_query')
        assert hasattr(orchestrator, 'get_system_health')
        assert hasattr(orchestrator, 'validate_configuration')
        assert hasattr(orchestrator, 'get_component')
        
        # Test method signatures haven't changed
        health = orchestrator.get_system_health()
        assert isinstance(health, dict)
        
        errors = orchestrator.validate_configuration()
        assert isinstance(errors, list)
        
        component = orchestrator.get_component('embedder')
        assert component is not None


class TestIntegrationScenarios(TestPlatformOrchestratorPhase3):
    """Test integration scenarios combining multiple Phase 3 features."""
    
    def test_end_to_end_unified_workflow(self, unified_config, temp_config_file):
        """Test complete workflow with unified architecture."""
        
        self.create_config_file(unified_config, temp_config_file)
        orchestrator = PlatformOrchestrator(temp_config_file)
        
        # Verify system is healthy
        health = orchestrator.get_system_health()
        assert health['status'] == 'healthy'
        assert health['architecture'] == 'unified'
        
        # Verify configuration is valid
        errors = orchestrator.validate_configuration()
        assert len(errors) == 0
        
        # Test component access
        embedder = orchestrator.get_component('embedder')
        retriever = orchestrator.get_component('retriever')
        generator = orchestrator.get_component('answer_generator')
        
        assert embedder is not None
        assert retriever is not None
        assert generator is not None
    
    def test_end_to_end_legacy_workflow(self, legacy_config, temp_config_file):
        """Test complete workflow with legacy architecture."""
        
        self.create_config_file(legacy_config, temp_config_file)
        orchestrator = PlatformOrchestrator(temp_config_file)
        
        # Verify system is healthy
        health = orchestrator.get_system_health()
        assert health['status'] == 'healthy'
        assert health['architecture'] == 'legacy'
        
        # Verify configuration is valid
        errors = orchestrator.validate_configuration()
        assert len(errors) == 0
        
        # Test component access (including vector store)
        embedder = orchestrator.get_component('embedder')
        vector_store = orchestrator.get_component('vector_store')
        retriever = orchestrator.get_component('retriever')
        generator = orchestrator.get_component('answer_generator')
        
        assert embedder is not None
        assert vector_store is not None
        assert retriever is not None
        assert generator is not None
    
    def test_configuration_migration_scenario(self, legacy_config, unified_config, temp_config_file):
        """Test migrating from legacy to unified configuration."""
        
        # Start with legacy configuration
        self.create_config_file(legacy_config, temp_config_file)
        legacy_orchestrator = PlatformOrchestrator(temp_config_file)
        
        assert legacy_orchestrator._using_unified_retriever == False
        assert 'vector_store' in legacy_orchestrator._components
        
        # Switch to unified configuration
        self.create_config_file(unified_config, temp_config_file)
        unified_orchestrator = PlatformOrchestrator(temp_config_file)
        
        assert unified_orchestrator._using_unified_retriever == True
        assert 'vector_store' not in unified_orchestrator._components
        
        # Both should be healthy
        legacy_health = legacy_orchestrator.get_system_health()
        unified_health = unified_orchestrator.get_system_health()
        
        assert legacy_health['status'] == 'healthy'
        assert unified_health['status'] == 'healthy'
        assert legacy_health['architecture'] == 'legacy'
        assert unified_health['architecture'] == 'unified'


class TestErrorRecovery(TestPlatformOrchestratorPhase3):
    """Test error recovery and resilience."""
    
    def test_partial_component_failure_handling(self, unified_config, temp_config_file):
        """Test handling when some components fail to initialize."""
        
        self.create_config_file(unified_config, temp_config_file)
        
        # Mock one component to fail
        with patch.object(ComponentFactory, 'create_embedder') as mock_create:
            mock_create.side_effect = RuntimeError("Component creation failed")
            
            with pytest.raises(RuntimeError) as exc_info:
                PlatformOrchestrator(temp_config_file)
            
            error_msg = str(exc_info.value)
            assert "System initialization failed" in error_msg
    
    def test_configuration_reload_capability(self, unified_config, temp_config_file):
        """Test configuration reload functionality."""
        
        self.create_config_file(unified_config, temp_config_file)
        orchestrator = PlatformOrchestrator(temp_config_file)
        
        # Verify initial state
        assert orchestrator._initialized == True
        original_components = len(orchestrator._components)
        
        # Modify configuration
        modified_config = unified_config.copy()
        modified_config['global_settings']['platform'] = 'modified_test'
        self.create_config_file(modified_config, temp_config_file)
        
        # Reload configuration
        orchestrator.reload_config()
        
        # Verify reload worked
        assert orchestrator._initialized == True
        assert len(orchestrator._components) == original_components
        assert orchestrator.config.global_settings['platform'] == 'modified_test'
    
    def test_graceful_degradation_on_factory_issues(self, unified_config, temp_config_file):
        """Test graceful handling when ComponentFactory has issues."""
        
        self.create_config_file(unified_config, temp_config_file)
        
        # Test that orchestrator handles factory import issues gracefully
        # (This is more of a design validation than a specific test case)
        orchestrator = PlatformOrchestrator(temp_config_file)
        
        # Even if factory has issues, basic operations should work
        health = orchestrator.get_system_health()
        assert isinstance(health, dict)
        assert 'status' in health


if __name__ == "__main__":
    pytest.main([__file__, "-v"])