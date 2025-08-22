"""
Request schemas for API Gateway Service.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum


class QueryStrategy(str, Enum):
    """Query processing strategy options."""
    COST_OPTIMIZED = "cost_optimized"
    BALANCED = "balanced"
    QUALITY_FIRST = "quality_first"
    PERFORMANCE = "performance"


class QueryOptions(BaseModel):
    """Options for query processing."""
    
    strategy: QueryStrategy = Field(
        default=QueryStrategy.BALANCED,
        description="Processing strategy for query"
    )
    
    max_cost: Optional[float] = Field(
        default=None,
        description="Maximum cost limit for query processing",
        ge=0.0
    )
    
    max_documents: Optional[int] = Field(
        default=None,
        description="Maximum number of documents to retrieve",
        ge=1,
        le=50
    )
    
    cache_enabled: bool = Field(
        default=True,
        description="Whether to use caching"
    )
    
    force_refresh: bool = Field(
        default=False,
        description="Force refresh cached results"
    )
    
    analytics_enabled: bool = Field(
        default=True,
        description="Whether to record analytics"
    )
    
    complexity_hint: Optional[str] = Field(
        default=None,
        description="Hint for query complexity (simple/medium/complex)"
    )
    
    preferred_models: Optional[List[str]] = Field(
        default=None,
        description="List of preferred models for generation"
    )
    
    timeout: Optional[int] = Field(
        default=None,
        description="Custom timeout for this query in seconds",
        ge=1,
        le=300
    )


class UnifiedQueryRequest(BaseModel):
    """Unified query request through API Gateway."""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="The query text to process"
    )
    
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional context information"
    )
    
    options: QueryOptions = Field(
        default_factory=QueryOptions,
        description="Query processing options"
    )
    
    session_id: Optional[str] = Field(
        default=None,
        description="Session identifier for request correlation"
    )
    
    user_id: Optional[str] = Field(
        default=None,
        description="User identifier for analytics"
    )
    
    @validator('query')
    def validate_query(cls, v):
        """Validate query string."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip()
    
    @validator('context')
    def validate_context(cls, v):
        """Validate context dictionary."""
        if v is not None and not isinstance(v, dict):
            raise ValueError("Context must be a dictionary")
        return v
    
    @property
    def query_hash(self) -> str:
        """Generate hash for query caching."""
        import hashlib
        query_str = f"{self.query}:{self.options.strategy}:{self.options.max_documents}"
        return hashlib.md5(query_str.encode()).hexdigest()


class BatchQueryRequest(BaseModel):
    """Request for batch query processing."""
    
    queries: List[str] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="List of queries to process"
    )
    
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Shared context for all queries"
    )
    
    options: QueryOptions = Field(
        default_factory=QueryOptions,
        description="Shared options for all queries"
    )
    
    session_id: Optional[str] = Field(
        default=None,
        description="Session identifier for request correlation"
    )
    
    user_id: Optional[str] = Field(
        default=None,
        description="User identifier for analytics"
    )
    
    parallel_processing: bool = Field(
        default=True,
        description="Whether to process queries in parallel"
    )
    
    max_parallel: Optional[int] = Field(
        default=10,
        description="Maximum number of parallel query processing",
        ge=1,
        le=50
    )
    
    @validator('queries')
    def validate_queries(cls, v):
        """Validate queries list."""
        for i, query in enumerate(v):
            if not query or not query.strip():
                raise ValueError(f"Query at index {i} cannot be empty or whitespace only")
        return [q.strip() for q in v]
    
    @validator('context')
    def validate_context(cls, v):
        """Validate context dictionary."""
        if v is not None and not isinstance(v, dict):
            raise ValueError("Context must be a dictionary")
        return v