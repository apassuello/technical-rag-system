"""
Request schemas for Query Analyzer Service API.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator


class AnalyzeRequest(BaseModel):
    """Request model for query analysis."""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="The query text to analyze"
    )
    
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional context information for the analysis"
    )
    
    options: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional analysis options and parameters"
    )
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        """Validate the query string."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip()
    
    @field_validator('context')
    @classmethod
    def validate_context(cls, v):
        """Validate context dictionary."""
        if v is not None and not isinstance(v, dict):
            raise ValueError("Context must be a dictionary")
        return v
    
    @field_validator('options')
    @classmethod
    def validate_options(cls, v):
        """Validate options dictionary."""
        if v is not None and not isinstance(v, dict):
            raise ValueError("Options must be a dictionary")
        return v or {}


class StatusRequest(BaseModel):
    """Request model for analyzer status."""
    
    include_performance: bool = Field(
        default=True,
        description="Whether to include performance metrics"
    )
    
    include_config: bool = Field(
        default=False,
        description="Whether to include configuration details"
    )