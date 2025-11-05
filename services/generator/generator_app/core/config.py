"""
Configuration management for Generator Service.

This module handles service configuration using Pydantic settings,
supporting both YAML files and environment variables.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from functools import lru_cache

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GeneratorConfig(BaseSettings):
    """Configuration for the Generator components."""
    
    # Multi-Model Routing Configuration
    routing: Dict[str, Any] = Field(
        default_factory=lambda: {
            "enabled": True,
            "default_strategy": "balanced",
            "enable_availability_testing": False,
            "availability_check_mode": "startup",
            "fallback_on_failure": True,
            "strategies": {
                "cost_optimized": {
                    "model_preferences": [
                        "ollama/llama3.2:3b",
                        "openai/gpt-3.5-turbo",
                        "mistral/mistral-small"
                    ],
                    "cost_weights": {
                        "ollama/llama3.2:3b": 0.0,
                        "openai/gpt-3.5-turbo": 0.002,
                        "mistral/mistral-small": 0.001
                    },
                    "max_cost_per_query": 0.01
                },
                "balanced": {
                    "model_preferences": [
                        "openai/gpt-3.5-turbo",
                        "mistral/mistral-medium",
                        "ollama/llama3.2:3b"
                    ],
                    "cost_weights": {
                        "openai/gpt-3.5-turbo": 0.002,
                        "mistral/mistral-medium": 0.004,
                        "ollama/llama3.2:3b": 0.0
                    },
                    "max_cost_per_query": 0.05
                },
                "quality_first": {
                    "model_preferences": [
                        "openai/gpt-4",
                        "mistral/mistral-large",
                        "openai/gpt-3.5-turbo"
                    ],
                    "cost_weights": {
                        "openai/gpt-4": 0.06,
                        "mistral/mistral-large": 0.008,
                        "openai/gpt-3.5-turbo": 0.002
                    },
                    "max_cost_per_query": 0.1
                }
            }
        },
        description="Multi-model routing configuration"
    )
    
    # Fallback Configuration
    fallback: Dict[str, Any] = Field(
        default_factory=lambda: {
            "enabled": True,
            "fallback_model": "ollama/llama3.2:3b",
            "max_retries": 3,
            "retry_delay": 1.0,
            "fallback_on_error": True,
            "fallback_on_timeout": True
        },
        description="Fallback chain configuration"
    )
    
    # Cost Tracking Configuration
    cost_tracking: Dict[str, Any] = Field(
        default_factory=lambda: {
            "enabled": True,
            "precision_places": 6,
            "daily_budget_limit": 100.0,
            "per_user_budget_limit": 10.0,
            "alert_threshold": 0.8
        },
        description="Cost tracking and budgeting"
    )
    
    # LLM Adapter Configuration
    adapters: Dict[str, Any] = Field(
        default_factory=lambda: {
            "ollama": {
                "endpoint": "http://ollama:11434",
                "timeout": 30,
                "max_retries": 3,
                "models": {
                    "llama3.2:3b": {
                        "max_tokens": 2048,
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                }
            },
            "openai": {
                "api_key_env": "OPENAI_API_KEY",
                "timeout": 60,
                "max_retries": 3,
                "models": {
                    "gpt-3.5-turbo": {
                        "max_tokens": 2048,
                        "temperature": 0.7
                    },
                    "gpt-4": {
                        "max_tokens": 4096,
                        "temperature": 0.3
                    }
                }
            },
            "mistral": {
                "api_key_env": "MISTRAL_API_KEY",
                "timeout": 60,
                "max_retries": 3,
                "models": {
                    "mistral-small": {
                        "max_tokens": 2048,
                        "temperature": 0.7
                    },
                    "mistral-medium": {
                        "max_tokens": 2048,
                        "temperature": 0.7
                    },
                    "mistral-large": {
                        "max_tokens": 4096,
                        "temperature": 0.3
                    }
                }
            }
        },
        description="LLM adapter configurations"
    )


class ServiceSettings(BaseSettings):
    """Service-level configuration settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="GENERATOR_",
        case_sensitive=False
    )
    
    # Service Configuration
    service_name: str = Field(default="generator", description="Service name")
    service_version: str = Field(default="1.0.0", description="Service version")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8081, description="Server port")
    workers: int = Field(default=1, description="Number of worker processes")

    @field_validator('port', mode='before')
    @classmethod
    def sanitize_port(cls, v):
        """Handle Kubernetes service discovery environment variables.

        Kubernetes creates environment variables like:
        GENERATOR_PORT=tcp://10.96.85.6:8081

        This validator extracts the port number from the tcp://IP:PORT format
        or falls back to the default port (8081) on any error.

        Args:
            v: The raw port value (could be int, string with port, or K8s URL)

        Returns:
            int: The validated port number

        Examples:
            - "tcp://10.96.85.6:8081" -> 8081
            - "8081" -> 8081
            - 8081 -> 8081
            - Invalid values -> 8081 (default)
        """
        if isinstance(v, str):
            # Handle Kubernetes tcp://IP:PORT format
            if v.startswith('tcp://'):
                try:
                    # Extract port from tcp://IP:PORT format
                    port_str = v.split(':')[-1]
                    return int(port_str)
                except (ValueError, IndexError):
                    # Return default port on parsing error
                    return 8081
            # Try parsing as int if it's a number string
            try:
                return int(v)
            except ValueError:
                # Return default port if string is not numeric
                return 8081
        # Return as-is if already an int or other type
        return v
    
    # gRPC Configuration
    grpc_port: int = Field(default=50052, description="gRPC server port")
    grpc_max_workers: int = Field(default=10, description="Maximum gRPC worker threads")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Logging format (json|text)")
    
    # Metrics Configuration
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_path: str = Field(default="/metrics", description="Metrics endpoint path")
    
    # Performance Configuration
    request_timeout: int = Field(default=120, description="Request timeout in seconds")
    max_concurrent_requests: int = Field(default=50, description="Maximum concurrent requests")
    
    # Health Check Configuration
    health_check_interval: int = Field(default=30, description="Health check interval in seconds")
    
    # Generator Configuration
    generator_config: GeneratorConfig = Field(default_factory=GeneratorConfig)
    
    # Configuration File
    config_file: Optional[str] = Field(default=None, description="Path to configuration file")
    
    def load_from_file(self, config_path: Path) -> None:
        """Load configuration from YAML file."""
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Update generator config if present
            if 'generator' in config_data:
                for key, value in config_data['generator'].items():
                    if hasattr(self.generator_config, key):
                        setattr(self.generator_config, key, value)
            
            # Update service settings
            for key, value in config_data.items():
                if key != 'generator' and hasattr(self, key):
                    setattr(self, key, value)


@lru_cache()
def get_settings() -> ServiceSettings:
    """Get cached service settings."""
    settings = ServiceSettings()
    
    # Load from config file if specified
    config_file = os.getenv("GENERATOR_CONFIG_FILE", "config.yaml")
    config_path = Path(config_file)
    
    if config_path.exists():
        settings.load_from_file(config_path)
    
    return settings


def get_generator_config() -> Dict[str, Any]:
    """Get generator configuration dictionary."""
    settings = get_settings()
    return {
        "routing": settings.generator_config.routing,
        "fallback": settings.generator_config.fallback,
        "cost_tracking": settings.generator_config.cost_tracking,
        "adapters": settings.generator_config.adapters
    }