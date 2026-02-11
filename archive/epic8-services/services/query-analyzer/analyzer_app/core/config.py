"""
Configuration management for Query Analyzer Service.

This module handles service configuration using Pydantic settings,
supporting both YAML files and environment variables.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AnalyzerConfig(BaseSettings):
    """Configuration for the Query Analyzer components."""
    
    # Feature Extractor Configuration
    feature_extractor: Dict[str, Any] = Field(
        default_factory=lambda: {
            "enable_caching": True,
            "cache_size": 1000,
            "extract_linguistic": True,
            "extract_structural": True,
            "extract_semantic": True
        },
        description="Feature extraction configuration"
    )
    
    # Complexity Classifier Configuration
    complexity_classifier: Dict[str, Any] = Field(
        default_factory=lambda: {
            "thresholds": {
                "simple": 0.3,
                "medium": 0.6,
                "complex": 0.9
            },
            "weights": {
                "length": 0.2,
                "vocabulary": 0.3,
                "syntax": 0.2,
                "semantic": 0.3
            }
        },
        description="Complexity classification configuration"
    )
    
    # Model Recommender Configuration
    model_recommender: Dict[str, Any] = Field(
        default_factory=lambda: {
            "strategy": "balanced",
            "model_mappings": {
                "simple": ["ollama/llama3.2:3b"],
                "medium": ["openai/gpt-3.5-turbo", "ollama/llama3.2:3b"],
                "complex": ["openai/gpt-4", "mistral/mistral-large"]
            },
            "cost_weights": {
                "ollama/llama3.2:3b": 0.0,
                "openai/gpt-3.5-turbo": 0.002,
                "openai/gpt-4": 0.06,
                "mistral/mistral-large": 0.008
            }
        },
        description="Model recommendation configuration"
    )


class PerformanceTargets(BaseSettings):
    """Epic 8 Performance targets configuration."""
    
    response_time_target_ms: int = Field(default=5000, description="Response time target in milliseconds")
    response_time_warning_ms: int = Field(default=2000, description="Response time warning threshold in milliseconds")
    accuracy_target: float = Field(default=0.85, description="Classification accuracy target")
    cost_error_target: float = Field(default=0.05, description="Cost estimation error target")
    memory_limit_gb: float = Field(default=2.0, description="Memory limit in GB")


class CircuitBreakerConfig(BaseSettings):
    """Epic 8 Circuit breaker configuration."""
    
    failure_threshold: int = Field(default=5, description="Number of failures before opening circuit")
    timeout_seconds: int = Field(default=60, description="Time to wait before trying half-open")
    enabled: bool = Field(default=True, description="Enable circuit breaker")


class FallbackConfig(BaseSettings):
    """Epic 8 Fallback mechanism configuration."""
    
    enabled: bool = Field(default=True, description="Enable fallback mechanisms")
    threshold_ms: int = Field(default=3000, description="Timeout threshold for fallback")


class ServiceSettings(BaseSettings):
    """Epic 8 Enhanced service-level configuration settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="QUERY_ANALYZER_",
        case_sensitive=False
    )
    
    # Service Configuration
    service_name: str = Field(default="query-analyzer", description="Service name")
    service_version: str = Field(default="1.0.0", description="Service version")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8082, description="Server port")
    workers: int = Field(default=1, description="Number of worker processes")

    @field_validator('port', mode='before')
    @classmethod
    def sanitize_port(cls, v):
        """Handle Kubernetes service discovery environment variables.

        Kubernetes creates environment variables like:
        QUERY_ANALYZER_PORT=tcp://10.96.29.145:8082

        This validator extracts the port number from the tcp://IP:PORT format
        or falls back to the default port (8082) on any error.

        Args:
            v: The raw port value (could be int, string with port, or K8s URL)

        Returns:
            int: The validated port number

        Examples:
            - "tcp://10.96.29.145:8082" -> 8082
            - "8082" -> 8082
            - 8082 -> 8082
            - Invalid values -> 8082 (default)
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
                    return 8082
            # Try parsing as int if it's a number string
            try:
                return int(v)
            except ValueError:
                # Return default port if string is not numeric
                return 8082
        # Return as-is if already an int or other type
        return v
    
    # gRPC Configuration
    grpc_port: int = Field(default=50051, description="gRPC server port")
    grpc_max_workers: int = Field(default=10, description="Maximum gRPC worker threads")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Logging format (json|text)")
    
    # Metrics Configuration
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_path: str = Field(default="/metrics", description="Metrics endpoint path")
    
    # Performance Configuration
    request_timeout: int = Field(default=30, description="Request timeout in seconds")
    max_concurrent_requests: int = Field(default=100, description="Maximum concurrent requests")
    
    # Health Check Configuration
    health_check_interval: int = Field(default=30, description="Health check interval in seconds")
    health_check_timeout: int = Field(default=2, description="Health check timeout in seconds")
    
    # Epic 8 Enhanced Configuration
    performance_targets: PerformanceTargets = Field(default_factory=PerformanceTargets)
    circuit_breaker: CircuitBreakerConfig = Field(default_factory=CircuitBreakerConfig)
    fallback: FallbackConfig = Field(default_factory=FallbackConfig)
    
    # Analyzer Configuration
    analyzer_config: AnalyzerConfig = Field(default_factory=AnalyzerConfig)
    
    # Configuration File
    config_file: Optional[str] = Field(default=None, description="Path to configuration file")
    
    def load_from_file(self, config_path: Path) -> None:
        """Epic 8 Enhanced configuration loading from YAML file."""
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Update analyzer config if present
            if 'analyzer' in config_data:
                for key, value in config_data['analyzer'].items():
                    if hasattr(self.analyzer_config, key):
                        setattr(self.analyzer_config, key, value)
            
            # Update Epic 8 performance targets
            if 'performance_targets' in config_data:
                for key, value in config_data['performance_targets'].items():
                    if hasattr(self.performance_targets, key):
                        setattr(self.performance_targets, key, value)
            
            # Update Epic 8 circuit breaker config
            if 'circuit_breaker' in config_data:
                for key, value in config_data['circuit_breaker'].items():
                    if hasattr(self.circuit_breaker, key):
                        setattr(self.circuit_breaker, key, value)
                        
            # Update Epic 8 fallback config
            if 'fallback' in config_data:
                for key, value in config_data['fallback'].items():
                    if hasattr(self.fallback, key):
                        setattr(self.fallback, key, value)
            
            # Update service settings (excluding nested configs)
            excluded_keys = {'analyzer', 'performance_targets', 'circuit_breaker', 'fallback'}
            for key, value in config_data.items():
                if key not in excluded_keys and hasattr(self, key):
                    setattr(self, key, value)


@lru_cache()
def get_settings() -> ServiceSettings:
    """Get cached service settings."""
    settings = ServiceSettings()
    
    # Load from config file if specified
    config_file = os.getenv("QUERY_ANALYZER_CONFIG_FILE", "config.yaml")
    config_path = Path(config_file)
    
    if config_path.exists():
        settings.load_from_file(config_path)
    
    return settings


def get_analyzer_config() -> Dict[str, Any]:
    """Get analyzer configuration dictionary."""
    settings = get_settings()
    return {
        "feature_extractor": settings.analyzer_config.feature_extractor,
        "complexity_classifier": settings.analyzer_config.complexity_classifier,
        "model_recommender": settings.analyzer_config.model_recommender
    }