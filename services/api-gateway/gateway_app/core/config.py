"""
Configuration module for API Gateway Service.
"""

import os
from typing import Dict, List, Optional
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings


class ServiceEndpoint(BaseSettings):
    """Configuration for external service endpoints."""
    
    host: str = Field(default="localhost")
    port: int = Field(default=8080)
    scheme: str = Field(default="http")
    path: str = Field(default="")
    timeout: int = Field(default=30)
    retries: int = Field(default=3)
    
    @property
    def url(self) -> str:
        """Build full URL for service."""
        base_url = f"{self.scheme}://{self.host}:{self.port}"
        if self.path:
            return f"{base_url}{self.path}"
        return base_url


class APIGatewaySettings(BaseSettings):
    """API Gateway service configuration."""
    
    # Service info
    service_name: str = Field(default="api-gateway")
    service_version: str = Field(default="1.0.0")
    
    # Server configuration
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8080)
    log_level: str = Field(default="INFO")
    
    # External service endpoints
    query_analyzer_host: str = Field(default="query-analyzer-service")
    query_analyzer_port: int = Field(default=8082)
    
    generator_host: str = Field(default="generator-service") 
    generator_port: int = Field(default=8081)
    
    retriever_host: str = Field(default="retriever-service")
    retriever_port: int = Field(default=8083)
    
    cache_host: str = Field(default="cache-service")
    cache_port: int = Field(default=8084)
    
    analytics_host: str = Field(default="analytics-service")
    analytics_port: int = Field(default=8085)
    
    # Gateway configuration
    max_query_length: int = Field(default=10000)
    max_batch_size: int = Field(default=100)
    default_timeout: int = Field(default=30)
    max_retries: int = Field(default=3)
    
    # Circuit breaker settings
    circuit_breaker_failure_threshold: int = Field(default=5)
    circuit_breaker_recovery_timeout: int = Field(default=60)
    circuit_breaker_expected_exception: tuple = Field(default=(Exception,))
    
    # Rate limiting
    rate_limit_per_minute: int = Field(default=100)
    burst_limit: int = Field(default=20)
    
    # CORS settings
    allowed_origins: List[str] = Field(default=["*"])
    allowed_methods: List[str] = Field(default=["GET", "POST", "PUT", "DELETE"])
    allowed_headers: List[str] = Field(default=["*"])
    
    # Security
    api_key_header: str = Field(default="X-API-Key")
    valid_api_keys: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(
        env_file=".env",
        env_prefix="GATEWAY_",
        case_sensitive=False,
        extra='ignore'  # Ignore extra env vars not defined in model
    )
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Invalid log level. Must be one of: {valid_levels}')
        return v.upper()
    
    @field_validator('allowed_origins')
    @classmethod
    def validate_origins(cls, v):
        """Validate CORS origins."""
        if "*" in v and len(v) > 1:
            raise ValueError("Cannot use wildcard '*' with specific origins")
        return v
    
    def get_service_endpoint(self, service_name: str) -> ServiceEndpoint:
        """Get endpoint configuration for a service."""
        service_configs = {
            "query-analyzer": ServiceEndpoint(
                host=self.query_analyzer_host,
                port=self.query_analyzer_port,
                path="/api/v1",
                timeout=self.default_timeout,
                retries=self.max_retries
            ),
            "generator": ServiceEndpoint(
                host=self.generator_host,
                port=self.generator_port,
                path="/api/v1",
                timeout=self.default_timeout,
                retries=self.max_retries
            ),
            "retriever": ServiceEndpoint(
                host=self.retriever_host,
                port=self.retriever_port,
                path="/api/v1",
                timeout=self.default_timeout,
                retries=self.max_retries
            ),
            "cache": ServiceEndpoint(
                host=self.cache_host,
                port=self.cache_port,
                path="/api/v1",
                timeout=self.default_timeout,
                retries=self.max_retries
            ),
            "analytics": ServiceEndpoint(
                host=self.analytics_host,
                port=self.analytics_port,
                path="/api/v1",
                timeout=self.default_timeout,
                retries=self.max_retries
            )
        }
        
        if service_name not in service_configs:
            raise ValueError(f"Unknown service: {service_name}")
        
        return service_configs[service_name]


# Global settings instance
_settings: Optional[APIGatewaySettings] = None


def get_settings() -> APIGatewaySettings:
    """Get gateway settings instance."""
    global _settings
    if _settings is None:
        _settings = APIGatewaySettings()
    return _settings