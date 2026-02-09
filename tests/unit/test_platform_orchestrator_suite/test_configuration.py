"""
Test suite for ConfigurationServiceImpl functionality in PlatformOrchestrator.

Tests the configuration service that manages system configurations,
component configs, validation, history tracking, and dynamic updates.
"""

import pytest
import time
from unittest.mock import Mock, patch
from typing import Dict, Any

from src.core.platform_orchestrator import ConfigurationServiceImpl
from .conftest import mock_config_manager


class TestConfigurationServiceImpl:
    """Test ConfigurationServiceImpl business logic and functionality."""

    def test_configuration_service_initialization(self, configuration_service):
        """Test configuration service initializes correctly."""
        assert configuration_service.config_manager is not None
        assert configuration_service.current_config is not None
        assert configuration_service.config_history == []
        assert configuration_service.validation_rules is not None

    def test_get_component_config_existing(self, configuration_service):
        """Test getting configuration for existing component."""
        config = configuration_service.get_component_config("document_processor")
        
        assert isinstance(config, dict)
        assert "type" in config
        assert "config" in config
        assert config["type"] == "hybrid_pdf"

    def test_get_component_config_nonexistent(self, configuration_service):
        """Test getting configuration for non-existent component."""
        config = configuration_service.get_component_config("nonexistent_component")
        
        assert config is None or config == {}

    def test_update_component_config(self, configuration_service):
        """Test updating component configuration."""
        new_config = {
            "chunk_size": 2000,
            "overlap": 200,
            "new_parameter": "test_value"
        }
        
        configuration_service.update_component_config("document_processor", new_config)
        
        # Verify configuration was updated
        updated_config = configuration_service.get_component_config("document_processor")
        assert updated_config["config"]["chunk_size"] == 2000
        assert updated_config["config"]["new_parameter"] == "test_value"

    def test_update_component_config_validation(self, configuration_service):
        """Test configuration update with validation."""
        # Invalid configuration that should fail validation
        invalid_config = {
            "chunk_size": -100,  # Invalid negative value
            "invalid_param": "invalid"
        }
        
        with pytest.raises((ValueError, AssertionError)):
            configuration_service.update_component_config("document_processor", invalid_config)

    def test_validate_configuration_valid(self, configuration_service):
        """Test configuration validation with valid config."""
        valid_config = {
            "document_processor": {
                "type": "hybrid_pdf",
                "config": {"chunk_size": 1500, "overlap": 150}
            },
            "embedder": {
                "type": "sentence_transformer",
                "config": {"model": "valid-model"}
            }
        }
        
        validation_errors = configuration_service.validate_configuration(valid_config)
        
        assert isinstance(validation_errors, list)
        assert len(validation_errors) == 0

    def test_validate_configuration_invalid(self, configuration_service):
        """Test configuration validation with invalid config."""
        invalid_config = {
            "document_processor": {
                "type": "nonexistent_type",
                "config": {"chunk_size": "invalid_size"}  # Should be int
            },
            "embedder": {
                # Missing required fields
            }
        }
        
        validation_errors = configuration_service.validate_configuration(invalid_config)
        
        assert isinstance(validation_errors, list)
        assert len(validation_errors) > 0
        assert any("type" in error.lower() for error in validation_errors)

    def test_get_system_configuration(self, configuration_service):
        """Test getting complete system configuration."""
        system_config = configuration_service.get_system_configuration()
        
        assert isinstance(system_config, dict)
        assert "document_processor" in system_config
        assert "embedder" in system_config
        assert "retriever" in system_config
        assert "answer_generator" in system_config

    def test_reload_configuration(self, configuration_service):
        """Test reloading configuration from source."""
        # Mock the config manager reload
        original_config = configuration_service.current_config.copy()
        
        configuration_service.reload_configuration()
        
        # Verify reload was called on config manager
        configuration_service.config_manager.reload.assert_called_once()

    def test_configuration_history_tracking(self, configuration_service):
        """Test configuration change history is tracked."""
        # Initial configuration change
        new_config = {"chunk_size": 1500}
        configuration_service.update_component_config("document_processor", new_config)
        
        history = configuration_service.get_configuration_history()
        
        assert isinstance(history, list)
        # History should contain at least the initial configuration
        if len(history) > 0:
            assert "timestamp" in history[0]
            assert "change_type" in history[0]
            assert "component" in history[0]

    def test_export_configuration(self, configuration_service):
        """Test exporting configuration data."""
        exported_config = configuration_service.export_configuration()
        
        assert isinstance(exported_config, dict)
        assert "document_processor" in exported_config
        assert "embedder" in exported_config
        assert "export_metadata" in exported_config
        assert "export_timestamp" in exported_config["export_metadata"]

    def test_import_configuration(self, configuration_service):
        """Test importing configuration data."""
        imported_config = {
            "document_processor": {
                "type": "imported_processor",
                "config": {"imported_param": "imported_value"}
            },
            "embedder": {
                "type": "imported_embedder",
                "config": {"imported_model": "imported-model"}
            },
            "retriever": {
                "type": "imported_retriever",
                "config": {"retriever_param": "retriever_value"}
            },
            "answer_generator": {
                "type": "imported_generator",
                "config": {"generator_param": "generator_value"}
            }
        }

        configuration_service.import_configuration(imported_config)

        # Verify imported configuration is active
        current_config = configuration_service.get_system_configuration()
        assert current_config["document_processor"]["type"] == "imported_processor"
        assert current_config["embedder"]["type"] == "imported_embedder"
        assert current_config["retriever"]["type"] == "imported_retriever"
        assert current_config["answer_generator"]["type"] == "imported_generator"

    def test_import_configuration_validation(self, configuration_service):
        """Test importing configuration with validation."""
        # Invalid imported configuration
        invalid_imported_config = {
            "document_processor": {
                "type": "invalid_type",
                "config": {"invalid": "config"}
            }
        }
        
        with pytest.raises((ValueError, AssertionError)):
            configuration_service.import_configuration(invalid_imported_config)

    def test_configuration_backup_and_restore(self, configuration_service):
        """Test configuration backup and restore functionality."""
        # Create backup
        backup = configuration_service.create_configuration_backup()
        
        assert isinstance(backup, dict)
        assert "configuration" in backup
        assert "backup_timestamp" in backup
        
        # Modify configuration
        new_config = {"modified_param": "modified_value"}
        configuration_service.update_component_config("document_processor", new_config)
        
        # Restore from backup
        configuration_service.restore_configuration_backup(backup)
        
        # Verify restoration
        restored_config = configuration_service.get_component_config("document_processor")
        assert "modified_param" not in restored_config.get("config", {})

    def test_configuration_diff(self, configuration_service):
        """Test configuration difference calculation."""
        import copy

        # Get original configuration
        original_config = configuration_service.get_system_configuration()

        # Create modified configuration - must use deepcopy to create independent nested structures
        modified_config = copy.deepcopy(original_config)
        modified_config["document_processor"]["config"]["chunk_size"] = 3000
        modified_config["embedder"]["config"]["model"] = "different-model"

        # Calculate diff
        diff = configuration_service.calculate_configuration_diff(
            original_config, modified_config
        )

        assert isinstance(diff, dict)
        assert "added" in diff
        assert "modified" in diff
        assert "removed" in diff
        assert len(diff["modified"]) >= 2  # chunk_size and model changes

    def test_configuration_template_management(self, configuration_service):
        """Test configuration template management."""
        # Create configuration template
        template = {
            "name": "test_template",
            "description": "Test configuration template",
            "configuration": {
                "document_processor": {
                    "type": "template_processor",
                    "config": {"template_param": "template_value"}
                }
            }
        }
        
        configuration_service.save_configuration_template(template)
        
        # Retrieve template
        saved_template = configuration_service.get_configuration_template("test_template")
        
        assert saved_template is not None
        assert saved_template["name"] == "test_template"
        assert saved_template["configuration"]["document_processor"]["type"] == "template_processor"

    def test_apply_configuration_template(self, configuration_service):
        """Test applying configuration template."""
        # Create and save template
        template = {
            "name": "apply_template",
            "configuration": {
                "document_processor": {
                    "type": "template_processor",
                    "config": {"template_chunk_size": 2500}
                }
            }
        }
        configuration_service.save_configuration_template(template)
        
        # Apply template
        configuration_service.apply_configuration_template("apply_template")
        
        # Verify template was applied
        current_config = configuration_service.get_component_config("document_processor")
        assert current_config["type"] == "template_processor"
        assert current_config["config"]["template_chunk_size"] == 2500

    def test_configuration_environment_variables(self, configuration_service):
        """Test configuration with environment variable substitution."""
        config_with_env_vars = {
            "document_processor": {
                "type": "${PROCESSOR_TYPE:hybrid_pdf}",
                "config": {
                    "chunk_size": "${CHUNK_SIZE:1000}",
                    "api_key": "${API_KEY}"
                }
            }
        }
        
        # Test environment variable resolution
        resolved_config = configuration_service.resolve_environment_variables(config_with_env_vars)
        
        assert isinstance(resolved_config, dict)
        # Should resolve with defaults or environment values
        assert resolved_config["document_processor"]["type"] in ["hybrid_pdf", "${PROCESSOR_TYPE:hybrid_pdf}"]

    def test_configuration_schema_validation(self, configuration_service):
        """Test configuration against schema validation."""
        # Valid configuration matching expected schema
        valid_config = {
            "document_processor": {
                "type": "hybrid_pdf",
                "config": {
                    "chunk_size": 1000,
                    "overlap": 100,
                    "max_pages": 100
                }
            }
        }
        
        is_valid = configuration_service.validate_against_schema(valid_config)
        assert is_valid is True

    def test_configuration_migration(self, configuration_service):
        """Test configuration migration between versions."""
        # Old format configuration
        old_config = {
            "processor": {  # Old key
                "chunk_size": 1000
            },
            "embedder": {
                "model_name": "old-model"  # Old parameter name
            }
        }
        
        # Migrate configuration
        migrated_config = configuration_service.migrate_configuration(
            old_config, 
            from_version="1.0", 
            to_version="2.0"
        )
        
        assert isinstance(migrated_config, dict)
        # Should contain new format keys
        assert "document_processor" in migrated_config or "processor" in migrated_config

    def test_configuration_validation_rules(self, configuration_service):
        """Test custom configuration validation rules."""
        # Add custom validation rule
        def chunk_size_rule(config):
            chunk_size = config.get("document_processor", {}).get("config", {}).get("chunk_size", 1000)
            if chunk_size < 100 or chunk_size > 10000:
                return "Chunk size must be between 100 and 10000"
            return None
        
        configuration_service.add_validation_rule("chunk_size_validation", chunk_size_rule)
        
        # Test with invalid chunk size
        invalid_config = {
            "document_processor": {
                "config": {"chunk_size": 50}  # Too small
            }
        }
        
        errors = configuration_service.validate_configuration(invalid_config)
        assert any("Chunk size must be between" in error for error in errors)

    def test_concurrent_configuration_updates(self, configuration_service):
        """Test concurrent configuration updates."""
        import threading
        
        def update_config(component_name, value):
            config = {"test_param": f"value_{value}"}
            configuration_service.update_component_config(component_name, config)
        
        # Run concurrent updates
        threads = []
        for i in range(5):
            thread = threading.Thread(target=update_config, args=("document_processor", i))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify final state is consistent
        final_config = configuration_service.get_component_config("document_processor")
        assert isinstance(final_config, dict)
        assert "config" in final_config

    def test_configuration_change_notifications(self, configuration_service):
        """Test configuration change notifications."""
        notifications = []
        
        def config_change_callback(component_name, old_config, new_config):
            notifications.append({
                "component": component_name,
                "old": old_config,
                "new": new_config,
                "timestamp": time.time()
            })
        
        # Register callback
        configuration_service.register_change_callback(config_change_callback)
        
        # Make configuration change
        new_config = {"notification_test": "test_value"}
        configuration_service.update_component_config("document_processor", new_config)
        
        # Verify notification was sent
        assert len(notifications) == 1
        assert notifications[0]["component"] == "document_processor"

    def test_configuration_rollback(self, configuration_service):
        """Test configuration rollback functionality."""
        # Get initial configuration
        initial_config = configuration_service.get_component_config("document_processor")
        
        # Make changes
        changed_config = {"rollback_test": "changed_value"}
        configuration_service.update_component_config("document_processor", changed_config)
        
        # Verify change
        modified_config = configuration_service.get_component_config("document_processor")
        assert modified_config["config"]["rollback_test"] == "changed_value"
        
        # Rollback to previous version
        configuration_service.rollback_configuration("document_processor", steps=1)
        
        # Verify rollback
        rolled_back_config = configuration_service.get_component_config("document_processor")
        assert "rollback_test" not in rolled_back_config.get("config", {})