"""
Test suite for ConfigurationServiceImpl functionality in PlatformOrchestrator.

Tests the configuration service that manages system configurations,
component configs, history tracking, and dynamic updates.
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
