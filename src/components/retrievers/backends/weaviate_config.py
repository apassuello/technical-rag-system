"""
Weaviate backend configuration schema.

This module provides configuration classes for the Weaviate backend
adapter, including connection settings, schema definitions, and
search parameters.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path


@dataclass
class WeaviateConnectionConfig:
    """Configuration for Weaviate connection."""
    
    url: str = "http://localhost:8080"
    api_key: Optional[str] = None
    timeout: int = 30
    startup_period: int = 5
    additional_headers: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate connection configuration."""
        if not self.url:
            raise ValueError("Weaviate URL cannot be empty")
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        if self.startup_period < 0:
            raise ValueError("Startup period cannot be negative")


@dataclass
class WeaviateSchemaConfig:
    """Configuration for Weaviate schema."""
    
    class_name: str = "TechnicalDocument"
    description: str = "Technical documentation chunks with embeddings"
    vector_index_config: Dict[str, Any] = field(default_factory=lambda: {
        "distance": "cosine",
        "ef": 64,
        "efConstruction": 128,
        "maxConnections": 64
    })
    properties: List[Dict[str, Any]] = field(default_factory=lambda: [
        {
            "name": "content",
            "dataType": ["text"],
            "description": "The main text content of the document chunk"
        },
        {
            "name": "source_file",
            "dataType": ["text"],
            "description": "Original source file path"
        },
        {
            "name": "chunk_index",
            "dataType": ["int"],
            "description": "Index of this chunk within the source document"
        },
        {
            "name": "page_number",
            "dataType": ["int"],
            "description": "Page number in the original document"
        },
        {
            "name": "chunk_size",
            "dataType": ["int"],
            "description": "Size of the chunk in characters"
        },
        {
            "name": "created_at",
            "dataType": ["date"],
            "description": "When this chunk was processed"
        }
    ])
    
    def __post_init__(self):
        """Validate schema configuration."""
        if not self.class_name:
            raise ValueError("Class name cannot be empty")
        if not self.class_name.isalnum():
            raise ValueError("Class name must be alphanumeric")
        if not self.properties:
            raise ValueError("Properties list cannot be empty")


@dataclass
class WeaviateSearchConfig:
    """Configuration for Weaviate search operations."""
    
    hybrid_search_enabled: bool = True
    alpha: float = 0.7  # Balance between vector and keyword search (0=keyword, 1=vector)
    fusion_type: str = "rankedFusion"  # or "relativeScoreFusion"
    limit: int = 100
    offset: int = 0
    autocut: int = 1  # Enable autocut
    certainty_threshold: float = 0.7
    distance_threshold: Optional[float] = None
    
    def __post_init__(self):
        """Validate search configuration."""
        if not 0 <= self.alpha <= 1:
            raise ValueError("Alpha must be between 0 and 1")
        if self.limit <= 0:
            raise ValueError("Limit must be positive")
        if self.offset < 0:
            raise ValueError("Offset cannot be negative")
        if not 0 <= self.certainty_threshold <= 1:
            raise ValueError("Certainty threshold must be between 0 and 1")
        if self.distance_threshold is not None and self.distance_threshold < 0:
            raise ValueError("Distance threshold cannot be negative")


@dataclass
class WeaviateBatchConfig:
    """Configuration for Weaviate batch operations."""
    
    batch_size: int = 100
    num_workers: int = 1
    connection_error_retries: int = 3
    timeout_retries: int = 3
    callback_period: int = 1000
    dynamic_batch_size: bool = True
    min_batch_size: int = 10
    max_batch_size: int = 1000
    
    def __post_init__(self):
        """Validate batch configuration."""
        if self.batch_size <= 0:
            raise ValueError("Batch size must be positive")
        if self.num_workers <= 0:
            raise ValueError("Number of workers must be positive")
        if self.connection_error_retries < 0:
            raise ValueError("Connection error retries cannot be negative")
        if self.timeout_retries < 0:
            raise ValueError("Timeout retries cannot be negative")
        if self.min_batch_size <= 0:
            raise ValueError("Min batch size must be positive")
        if self.max_batch_size < self.min_batch_size:
            raise ValueError("Max batch size must be >= min batch size")


@dataclass
class WeaviateBackendConfig:
    """Complete configuration for Weaviate backend."""
    
    connection: WeaviateConnectionConfig = field(default_factory=WeaviateConnectionConfig)
    schema: WeaviateSchemaConfig = field(default_factory=WeaviateSchemaConfig)
    search: WeaviateSearchConfig = field(default_factory=WeaviateSearchConfig)
    batch: WeaviateBatchConfig = field(default_factory=WeaviateBatchConfig)
    
    # Backend-specific settings
    auto_create_schema: bool = True
    enable_backup: bool = True
    backup_interval_hours: int = 24
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    
    def __post_init__(self):
        """Validate complete backend configuration."""
        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")
        if self.retry_delay_seconds < 0:
            raise ValueError("Retry delay cannot be negative")
        if self.backup_interval_hours <= 0:
            raise ValueError("Backup interval must be positive")
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'WeaviateBackendConfig':
        """Create configuration from dictionary."""
        connection_config = WeaviateConnectionConfig(**config_dict.get('connection', {}))
        schema_config = WeaviateSchemaConfig(**config_dict.get('schema', {}))
        search_config = WeaviateSearchConfig(**config_dict.get('search', {}))
        batch_config = WeaviateBatchConfig(**config_dict.get('batch', {}))
        
        # Extract backend-specific settings
        backend_settings = {
            k: v for k, v in config_dict.items()
            if k not in ['connection', 'schema', 'search', 'batch']
        }
        
        return cls(
            connection=connection_config,
            schema=schema_config,
            search=search_config,
            batch=batch_config,
            **backend_settings
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'connection': {
                'url': self.connection.url,
                'api_key': self.connection.api_key,
                'timeout': self.connection.timeout,
                'startup_period': self.connection.startup_period,
                'additional_headers': self.connection.additional_headers
            },
            'schema': {
                'class_name': self.schema.class_name,
                'description': self.schema.description,
                'vector_index_config': self.schema.vector_index_config,
                'properties': self.schema.properties
            },
            'search': {
                'hybrid_search_enabled': self.search.hybrid_search_enabled,
                'alpha': self.search.alpha,
                'fusion_type': self.search.fusion_type,
                'limit': self.search.limit,
                'offset': self.search.offset,
                'autocut': self.search.autocut,
                'certainty_threshold': self.search.certainty_threshold,
                'distance_threshold': self.search.distance_threshold
            },
            'batch': {
                'batch_size': self.batch.batch_size,
                'num_workers': self.batch.num_workers,
                'connection_error_retries': self.batch.connection_error_retries,
                'timeout_retries': self.batch.timeout_retries,
                'callback_period': self.batch.callback_period,
                'dynamic_batch_size': self.batch.dynamic_batch_size,
                'min_batch_size': self.batch.min_batch_size,
                'max_batch_size': self.batch.max_batch_size
            },
            'auto_create_schema': self.auto_create_schema,
            'enable_backup': self.enable_backup,
            'backup_interval_hours': self.backup_interval_hours,
            'max_retries': self.max_retries,
            'retry_delay_seconds': self.retry_delay_seconds
        }