"""
Configuration management for Analytics Service.

Handles service configuration including Epic 1 cost tracking integration,
performance monitoring settings, and data persistence options.
"""

import os
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
from pathlib import Path
import yaml


class AnalyticsSettings(BaseSettings):
    """Analytics Service configuration settings."""
    
    # Service configuration
    service_name: str = "analytics"
    service_version: str = "1.0.0"
    log_level: str = "INFO"
    debug: bool = False
    
    # Epic 1 cost tracking integration
    enable_cost_tracking: bool = True
    cost_precision_places: int = 6
    daily_budget: Optional[float] = None
    monthly_budget: Optional[float] = None
    alert_thresholds: List[float] = [0.80, 0.95, 1.0]
    
    # Performance monitoring
    enable_performance_tracking: bool = True
    performance_sampling_rate: float = 1.0  # Sample all requests
    slo_response_time_ms: int = 2000  # 2 second SLO
    slo_error_rate_threshold: float = 0.01  # 1% error rate
    slo_availability_threshold: float = 0.999  # 99.9% availability
    
    # Data persistence
    metrics_retention_hours: int = 168  # 1 week
    enable_data_persistence: bool = False
    persistence_backend: str = "memory"  # "memory", "redis", "postgresql"
    redis_url: Optional[str] = None
    database_url: Optional[str] = None
    
    # Analytics configuration
    enable_usage_trends: bool = True
    enable_ab_testing: bool = True
    cost_optimization_threshold: float = 0.30  # 30% cost on simple queries triggers optimization
    provider_optimization_threshold: float = 0.60  # 60% cost from expensive provider
    
    # Circuit breaker settings
    circuit_breaker_enabled: bool = True
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 60
    circuit_breaker_expected_exception: str = "Exception"
    
    # API settings
    api_timeout_seconds: int = 30
    max_batch_size: int = 1000
    enable_detailed_logging: bool = True
    
    class Config:
        env_prefix = "ANALYTICS_"
        case_sensitive = False

    @validator("alert_thresholds")
    def validate_alert_thresholds(cls, v):
        """Validate alert thresholds are between 0 and 1."""
        for threshold in v:
            if not 0 <= threshold <= 1:
                raise ValueError(f"Alert threshold {threshold} must be between 0 and 1")
        return sorted(v)  # Sort thresholds

    @validator("cost_precision_places")
    def validate_precision(cls, v):
        """Validate cost precision places."""
        if not 1 <= v <= 10:
            raise ValueError("Cost precision places must be between 1 and 10")
        return v


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        config_path = Path("config.yaml")
    
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
        
        # Extract analytics-specific configuration
        analytics_config = config.get('analytics', {})
        
        return analytics_config
    except Exception as e:
        print(f"Warning: Could not load config file {config_path}: {e}")
        return {}


# Global settings instance
_settings: Optional[AnalyticsSettings] = None


def get_settings() -> AnalyticsSettings:
    """
    Get global settings instance.
    
    Returns:
        AnalyticsSettings instance
    """
    global _settings
    if _settings is None:
        # Load from YAML config file
        config_data = load_config()
        
        # Override with environment variables
        _settings = AnalyticsSettings(**config_data)
        
    return _settings


def get_cost_tracker_config() -> Dict[str, Any]:
    """
    Get Epic 1 CostTracker configuration.
    
    Returns:
        Configuration dictionary for CostTracker initialization
    """
    settings = get_settings()
    
    from decimal import Decimal
    
    config = {
        "daily_budget": Decimal(str(settings.daily_budget)) if settings.daily_budget else None,
        "monthly_budget": Decimal(str(settings.monthly_budget)) if settings.monthly_budget else None,
        "alert_thresholds": settings.alert_thresholds,
        "precision_places": settings.cost_precision_places,
        "enable_detailed_logging": settings.enable_detailed_logging,
    }
    
    return config


def get_circuit_breaker_config() -> Dict[str, Any]:
    """
    Get circuit breaker configuration.
    
    Returns:
        Configuration dictionary for circuit breaker
    """
    settings = get_settings()
    
    return {
        "failure_threshold": settings.circuit_breaker_failure_threshold,
        "recovery_timeout": settings.circuit_breaker_recovery_timeout,
        "expected_exception": Exception,  # Convert string to exception type
    }


def get_performance_config() -> Dict[str, Any]:
    """
    Get performance monitoring configuration.
    
    Returns:
        Configuration dictionary for performance monitoring
    """
    settings = get_settings()
    
    return {
        "enable_tracking": settings.enable_performance_tracking,
        "sampling_rate": settings.performance_sampling_rate,
        "slo_response_time_ms": settings.slo_response_time_ms,
        "slo_error_rate_threshold": settings.slo_error_rate_threshold,
        "slo_availability_threshold": settings.slo_availability_threshold,
    }