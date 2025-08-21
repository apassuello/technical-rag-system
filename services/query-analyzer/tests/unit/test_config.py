"""
Unit tests for configuration management.

Tests the ServiceSettings and AnalyzerConfig classes, along with
configuration loading from files and environment variables.
"""

import pytest
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open

from app.core.config import (
    ServiceSettings,
    AnalyzerConfig,
    get_settings,
    get_analyzer_config
)


class TestAnalyzerConfig:
    """Test cases for AnalyzerConfig class."""

    def test_default_configuration(self):
        """Test default analyzer configuration values."""
        config = AnalyzerConfig()
        
        # Feature extractor defaults
        assert config.feature_extractor["enable_caching"] is True
        assert config.feature_extractor["cache_size"] == 1000
        assert config.feature_extractor["extract_linguistic"] is True
        assert config.feature_extractor["extract_structural"] is True
        assert config.feature_extractor["extract_semantic"] is True
        
        # Complexity classifier defaults
        assert config.complexity_classifier["thresholds"]["simple"] == 0.3
        assert config.complexity_classifier["thresholds"]["medium"] == 0.6
        assert config.complexity_classifier["thresholds"]["complex"] == 0.9
        
        weights = config.complexity_classifier["weights"]
        assert weights["length"] == 0.2
        assert weights["vocabulary"] == 0.3
        assert weights["syntax"] == 0.2
        assert weights["semantic"] == 0.3
        
        # Model recommender defaults
        assert config.model_recommender["strategy"] == "balanced"
        assert "simple" in config.model_recommender["model_mappings"]
        assert "medium" in config.model_recommender["model_mappings"]
        assert "complex" in config.model_recommender["model_mappings"]
        
        # Check cost weights
        cost_weights = config.model_recommender["cost_weights"]
        assert "ollama/llama3.2:3b" in cost_weights
        assert "openai/gpt-3.5-turbo" in cost_weights
        assert "openai/gpt-4" in cost_weights

    def test_custom_configuration(self):
        """Test custom analyzer configuration."""
        custom_config = AnalyzerConfig(
            feature_extractor={"cache_size": 500, "enable_caching": False},
            complexity_classifier={
                "thresholds": {"simple": 0.2, "medium": 0.5, "complex": 0.8}
            },
            model_recommender={"strategy": "cost_optimized"}
        )
        
        assert custom_config.feature_extractor["cache_size"] == 500
        assert custom_config.feature_extractor["enable_caching"] is False
        assert custom_config.complexity_classifier["thresholds"]["simple"] == 0.2
        assert custom_config.model_recommender["strategy"] == "cost_optimized"


class TestServiceSettings:
    """Test cases for ServiceSettings class."""

    def test_default_settings(self):
        """Test default service settings."""
        settings = ServiceSettings()
        
        assert settings.service_name == "query-analyzer"
        assert settings.service_version == "1.0.0"
        assert settings.host == "0.0.0.0"
        assert settings.port == 8080
        assert settings.workers == 1
        assert settings.grpc_port == 50051
        assert settings.log_level == "INFO"
        assert settings.enable_metrics is True
        assert settings.request_timeout == 30
        assert settings.max_concurrent_requests == 100

    def test_environment_variable_override(self):
        """Test environment variable configuration override."""
        env_vars = {
            "QUERY_ANALYZER_SERVICE_NAME": "test-analyzer",
            "QUERY_ANALYZER_HOST": "127.0.0.1",
            "QUERY_ANALYZER_PORT": "9090",
            "QUERY_ANALYZER_LOG_LEVEL": "DEBUG",
            "QUERY_ANALYZER_WORKERS": "4"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = ServiceSettings()
            
            assert settings.service_name == "test-analyzer"
            assert settings.host == "127.0.0.1"
            assert settings.port == 9090
            assert settings.log_level == "DEBUG"
            assert settings.workers == 4

    def test_boolean_environment_variables(self):
        """Test boolean environment variable parsing."""
        with patch.dict(os.environ, {"QUERY_ANALYZER_ENABLE_METRICS": "false"}):
            settings = ServiceSettings()
            assert settings.enable_metrics is False
            
        with patch.dict(os.environ, {"QUERY_ANALYZER_ENABLE_METRICS": "true"}):
            settings = ServiceSettings()
            assert settings.enable_metrics is True

    def test_case_insensitive_env_vars(self):
        """Test case insensitive environment variables."""
        with patch.dict(os.environ, {"query_analyzer_port": "7070"}):
            settings = ServiceSettings()
            assert settings.port == 7070

    def test_invalid_type_coercion(self):
        """Test handling of invalid type coercion in environment variables."""
        with patch.dict(os.environ, {"QUERY_ANALYZER_PORT": "invalid_port"}):
            with pytest.raises(ValueError):
                ServiceSettings()

    def test_load_from_file_success(self, temp_config_file):
        """Test successful loading from configuration file."""
        settings = ServiceSettings()
        settings.load_from_file(temp_config_file)
        
        assert settings.service_name == "query-analyzer-test"
        assert settings.port == 8081
        assert settings.log_level == "DEBUG"
        
        # Check analyzer config was updated
        assert settings.analyzer_config.feature_extractor["cache_size"] == 500
        assert settings.analyzer_config.complexity_classifier["thresholds"]["simple"] == 0.25
        assert settings.analyzer_config.model_recommender["strategy"] == "cost_optimized"

    def test_load_from_file_nonexistent(self):
        """Test loading from non-existent file."""
        settings = ServiceSettings()
        non_existent = Path("/non/existent/file.yaml")
        
        # Should not raise exception
        settings.load_from_file(non_existent)
        
        # Should maintain default values
        assert settings.service_name == "query-analyzer"
        assert settings.port == 8080

    def test_load_from_file_invalid_yaml(self):
        """Test loading from invalid YAML file."""
        invalid_yaml = "invalid: yaml: content: ["
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            f.flush()
            
            settings = ServiceSettings()
            
            with pytest.raises(yaml.YAMLError):
                settings.load_from_file(Path(f.name))
            
            Path(f.name).unlink()

    def test_load_from_file_partial_config(self):
        """Test loading partial configuration from file."""
        partial_config = {
            "port": 9999,
            "analyzer": {
                "feature_extractor": {"cache_size": 2000}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(partial_config, f)
            f.flush()
            
            settings = ServiceSettings()
            settings.load_from_file(Path(f.name))
            
            # Updated values
            assert settings.port == 9999
            assert settings.analyzer_config.feature_extractor["cache_size"] == 2000
            
            # Default values should remain
            assert settings.service_name == "query-analyzer"
            assert settings.log_level == "INFO"
            
            Path(f.name).unlink()

    def test_nested_analyzer_config_update(self):
        """Test nested analyzer configuration updates."""
        config_data = {
            "analyzer": {
                "complexity_classifier": {
                    "thresholds": {
                        "simple": 0.1,
                        "complex": 0.95
                    },
                    "weights": {
                        "length": 0.5
                    }
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()
            
            settings = ServiceSettings()
            settings.load_from_file(Path(f.name))
            
            # Check nested updates
            thresholds = settings.analyzer_config.complexity_classifier["thresholds"]
            assert thresholds["simple"] == 0.1
            assert thresholds["medium"] == 0.6  # Should keep default
            assert thresholds["complex"] == 0.95
            
            weights = settings.analyzer_config.complexity_classifier["weights"]
            assert weights["length"] == 0.5
            assert weights["vocabulary"] == 0.3  # Should keep default
            
            Path(f.name).unlink()

    def test_invalid_nested_config(self):
        """Test handling of invalid nested configuration."""
        settings = ServiceSettings()
        
        # Mock hasattr to return False for invalid attribute
        with patch('builtins.hasattr', return_value=False):
            config_data = {"invalid_attribute": "value"}
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(config_data, f)
                f.flush()
                
                # Should not raise exception
                settings.load_from_file(Path(f.name))
                
                # Should maintain defaults
                assert settings.service_name == "query-analyzer"
                
                Path(f.name).unlink()


class TestConfigurationFunctions:
    """Test cases for configuration utility functions."""

    def test_get_settings_default(self):
        """Test get_settings with default configuration."""
        with patch.dict(os.environ, {}, clear=True):
            settings = get_settings()
            
            assert isinstance(settings, ServiceSettings)
            assert settings.service_name == "query-analyzer"
            assert settings.port == 8080

    def test_get_settings_cached(self):
        """Test that get_settings returns cached instance."""
        # Clear the cache first
        get_settings.cache_clear()
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Should be the same instance due to lru_cache
        assert settings1 is settings2

    def test_get_settings_with_config_file(self, temp_config_file):
        """Test get_settings with configuration file."""
        env_var = f"QUERY_ANALYZER_CONFIG_FILE={temp_config_file}"
        
        with patch.dict(os.environ, {"QUERY_ANALYZER_CONFIG_FILE": str(temp_config_file)}):
            get_settings.cache_clear()  # Clear cache to force reload
            settings = get_settings()
            
            assert settings.service_name == "query-analyzer-test"
            assert settings.port == 8081

    def test_get_settings_with_missing_config_file(self):
        """Test get_settings with missing configuration file."""
        missing_file = "/path/to/missing/config.yaml"
        
        with patch.dict(os.environ, {"QUERY_ANALYZER_CONFIG_FILE": missing_file}):
            get_settings.cache_clear()
            settings = get_settings()
            
            # Should use defaults when file doesn't exist
            assert settings.service_name == "query-analyzer"
            assert settings.port == 8080

    def test_get_analyzer_config(self):
        """Test get_analyzer_config function."""
        config = get_analyzer_config()
        
        assert isinstance(config, dict)
        assert "feature_extractor" in config
        assert "complexity_classifier" in config
        assert "model_recommender" in config
        
        # Should return the analyzer config from settings
        settings = get_settings()
        expected_config = {
            "feature_extractor": settings.analyzer_config.feature_extractor,
            "complexity_classifier": settings.analyzer_config.complexity_classifier,
            "model_recommender": settings.analyzer_config.model_recommender
        }
        
        assert config == expected_config

    def test_get_analyzer_config_with_custom_settings(self, temp_config_file):
        """Test get_analyzer_config with custom settings."""
        with patch.dict(os.environ, {"QUERY_ANALYZER_CONFIG_FILE": str(temp_config_file)}):
            get_settings.cache_clear()
            config = get_analyzer_config()
            
            # Should reflect custom configuration
            assert config["feature_extractor"]["cache_size"] == 500
            assert config["complexity_classifier"]["thresholds"]["simple"] == 0.25
            assert config["model_recommender"]["strategy"] == "cost_optimized"


class TestConfigurationValidation:
    """Test cases for configuration validation."""

    def test_valid_log_levels(self):
        """Test valid log level configurations."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level in valid_levels:
            with patch.dict(os.environ, {"QUERY_ANALYZER_LOG_LEVEL": level}):
                settings = ServiceSettings()
                assert settings.log_level == level

    def test_valid_port_ranges(self):
        """Test valid port configurations."""
        valid_ports = [1024, 8080, 9090, 65535]
        
        for port in valid_ports:
            with patch.dict(os.environ, {"QUERY_ANALYZER_PORT": str(port)}):
                settings = ServiceSettings()
                assert settings.port == port

    def test_positive_integer_fields(self):
        """Test positive integer field validation."""
        positive_fields = {
            "QUERY_ANALYZER_WORKERS": "workers",
            "QUERY_ANALYZER_REQUEST_TIMEOUT": "request_timeout",
            "QUERY_ANALYZER_MAX_CONCURRENT_REQUESTS": "max_concurrent_requests"
        }
        
        for env_var, field_name in positive_fields.items():
            with patch.dict(os.environ, {env_var: "10"}):
                settings = ServiceSettings()
                assert getattr(settings, field_name) == 10

    def test_string_field_validation(self):
        """Test string field validation."""
        string_fields = {
            "QUERY_ANALYZER_SERVICE_NAME": "service_name",
            "QUERY_ANALYZER_SERVICE_VERSION": "service_version",
            "QUERY_ANALYZER_HOST": "host",
            "QUERY_ANALYZER_LOG_FORMAT": "log_format"
        }
        
        for env_var, field_name in string_fields.items():
            test_value = f"test_{field_name}"
            with patch.dict(os.environ, {env_var: test_value}):
                settings = ServiceSettings()
                assert getattr(settings, field_name) == test_value