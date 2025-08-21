"""
Configuration management for Query Analyzer Service.

This module handles service configuration using Pydantic settings,
supporting both YAML files and environment variables.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from functools import lru_cache

import yaml
from pydantic import BaseSettings, Field
from pydantic_settings import SettingsConfigDict


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


class ServiceSettings(BaseSettings):
    """Service-level configuration settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="QUERY_ANALYZER_",
        case_sensitive=False
    )
    
    # Service Configuration
    service_name: str = Field(default="query-analyzer", description="Service name")
    service_version: str = Field(default="1.0.0", description="Service version")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8080, description="Server port")
    workers: int = Field(default=1, description="Number of worker processes")
    
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
    
    # Analyzer Configuration
    analyzer_config: AnalyzerConfig = Field(default_factory=AnalyzerConfig)
    
    # Configuration File
    config_file: Optional[str] = Field(default=None, description="Path to configuration file")
    
    def load_from_file(self, config_path: Path) -> None:
        """Load configuration from YAML file."""
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Update analyzer config if present
            if 'analyzer' in config_data:
                for key, value in config_data['analyzer'].items():
                    if hasattr(self.analyzer_config, key):
                        setattr(self.analyzer_config, key, value)
            
            # Update service settings
            for key, value in config_data.items():
                if key != 'analyzer' and hasattr(self, key):
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