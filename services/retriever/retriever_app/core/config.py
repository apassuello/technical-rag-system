"""
Retriever Service Configuration Management.

This module handles configuration loading and validation for the
retriever service using Pydantic settings with YAML support.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
import yaml


class CircuitBreakerConfig(BaseModel):
    """Circuit breaker configuration."""
    failure_threshold: int = Field(default=5, description="Number of failures before opening circuit")
    recovery_timeout: int = Field(default=60, description="Timeout in seconds before attempting recovery")
    expected_exception: str = Field(default="Exception", description="Expected exception class name")


class TimeoutConfig(BaseModel):
    """Timeout configuration."""
    retrieval_timeout: float = Field(default=30.0, description="Timeout for retrieval operations in seconds")
    indexing_timeout: float = Field(default=300.0, description="Timeout for indexing operations in seconds")
    health_check_timeout: float = Field(default=5.0, description="Timeout for health checks in seconds")


class BatchConfig(BaseModel):
    """Batch processing configuration."""
    max_batch_size: int = Field(default=100, description="Maximum documents per batch")
    batch_timeout: float = Field(default=5.0, description="Timeout for batch operations in seconds")


class PerformanceConfig(BaseModel):
    """Performance and reliability configuration."""
    circuit_breaker: CircuitBreakerConfig = Field(default_factory=CircuitBreakerConfig)
    timeouts: TimeoutConfig = Field(default_factory=TimeoutConfig)
    batch: BatchConfig = Field(default_factory=BatchConfig)


class MonitoringConfig(BaseModel):
    """Monitoring and metrics configuration."""
    metrics: Dict[str, Any] = Field(default_factory=lambda: {"enabled": True, "prefix": "retriever"})
    health_checks: Dict[str, Any] = Field(default_factory=lambda: {"enabled": True, "interval": 30})
    logging: Dict[str, Any] = Field(
        default_factory=lambda: {
            "level": "INFO",
            "format": "structured",
            "include_performance_metrics": True
        }
    )


class ServiceConfig(BaseModel):
    """Service configuration."""
    name: str = Field(default="retriever-service", description="Service name")
    version: str = Field(default="1.0.0", description="Service version")
    host: str = Field(default="0.0.0.0", description="Service host")
    port: int = Field(default=8083, description="Service port")
    debug: bool = Field(default=False, description="Enable debug mode")


class Settings(BaseSettings):
    """Main settings class."""
    
    service: ServiceConfig = Field(default_factory=ServiceConfig)
    retriever_config: Dict[str, Any] = Field(default_factory=dict, description="Epic 2 ModularUnifiedRetriever configuration")
    embedder_config: Dict[str, Any] = Field(default_factory=dict, description="Embedder configuration")
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    development: Dict[str, Any] = Field(
        default_factory=lambda: {
            "mock_responses": False,
            "test_data_path": "/tmp/test_documents",
            "performance_profiling": False
        }
    )
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        
    @validator('retriever_config', pre=True, always=True)
    def set_default_retriever_config(cls, v):
        """Set default retriever configuration if not provided."""
        if not v:
            return {
                "vector_index": {
                    "type": "faiss",
                    "config": {
                        "index_type": "IndexFlatIP",
                        "normalize_embeddings": True,
                        "dimension": 384
                    }
                },
                "sparse": {
                    "type": "bm25",
                    "config": {
                        "k1": 1.2,
                        "b": 0.75
                    }
                },
                "fusion": {
                    "type": "rrf",
                    "config": {
                        "k": 60,
                        "weights": {"dense": 0.7, "sparse": 0.3}
                    }
                },
                "reranker": {
                    "type": "semantic",
                    "config": {
                        "enabled": True,
                        "model": "cross-encoder/ms-marco-MiniLM-L-6-v2"
                    }
                }
            }
        return v
    
    @validator('embedder_config', pre=True, always=True)
    def set_default_embedder_config(cls, v):
        """Set default embedder configuration if not provided."""
        if not v:
            return {
                "type": "sentence_transformer",
                "config": {
                    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                    "device": "cpu",
                    "batch_size": 32,
                    "normalize_embeddings": True
                }
            }
        return v


def load_config_from_yaml(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Dictionary containing configuration
    """
    if not config_path:
        # Try to find config.yaml in the service directory
        service_dir = Path(__file__).parent.parent.parent  # Go up 3 levels to service root
        config_path = service_dir / "config.yaml"
    
    config_path = Path(config_path)
    
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config or {}
    except Exception as e:
        print(f"Warning: Failed to load config from {config_path}: {e}")
        return {}


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get settings instance (singleton pattern).
    
    Returns:
        Settings instance
    """
    global _settings
    
    if _settings is None:
        # Load configuration from YAML
        yaml_config = load_config_from_yaml()
        
        # Override with environment variables
        _settings = Settings(**yaml_config)
    
    return _settings


def reload_settings(config_path: Optional[str] = None) -> Settings:
    """
    Reload settings from configuration file.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        New settings instance
    """
    global _settings
    
    yaml_config = load_config_from_yaml(config_path)
    _settings = Settings(**yaml_config)
    
    return _settings