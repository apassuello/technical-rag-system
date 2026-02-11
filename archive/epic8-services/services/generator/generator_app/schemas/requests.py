"""
Request schemas for Generator Service API.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class DocumentContext(BaseModel):
    """Document context for generation."""
    
    content: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    doc_id: Optional[str] = Field(default=None, description="Document identifier")
    source: Optional[str] = Field(default=None, description="Document source")
    score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Relevance score")


class GenerateRequest(BaseModel):
    """Request model for answer generation."""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The user's query"
    )
    
    context_documents: List[DocumentContext] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Relevant documents for context"
    )
    
    options: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Generation options and parameters"
    )
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        """Validate the query string."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip()
    
    @field_validator('context_documents')
    @classmethod
    def validate_context_documents(cls, v):
        """Validate context documents."""
        if not v:
            raise ValueError("At least one context document is required")
        return v
    
    @field_validator('options')
    @classmethod
    def validate_options(cls, v):
        """Validate options dictionary."""
        if v is not None and not isinstance(v, dict):
            raise ValueError("Options must be a dictionary")
        
        # Validate specific options if present
        if 'strategy' in v:
            valid_strategies = ['cost_optimized', 'balanced', 'quality_first']
            if v['strategy'] not in valid_strategies:
                raise ValueError(f"Strategy must be one of: {valid_strategies}")
        
        if 'max_cost' in v:
            if not isinstance(v['max_cost'], (int, float)) or v['max_cost'] < 0:
                raise ValueError("max_cost must be a non-negative number")
        
        if 'preferred_model' in v:
            if not isinstance(v['preferred_model'], str):
                raise ValueError("preferred_model must be a string")
        
        return v or {}


class BatchGenerateRequest(BaseModel):
    """Request model for batch generation."""
    
    requests: List[GenerateRequest] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="List of generation requests"
    )
    
    batch_options: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Batch-level options"
    )


class ModelStatusRequest(BaseModel):
    """Request model for model status."""
    
    include_costs: bool = Field(
        default=True,
        description="Whether to include cost information"
    )
    
    include_performance: bool = Field(
        default=False,
        description="Whether to include performance metrics"
    )


class RoutingTestRequest(BaseModel):
    """Request model for testing routing decisions."""
    
    query: str = Field(..., description="Test query")
    strategy: Optional[str] = Field(default=None, description="Routing strategy to test")
    max_cost: Optional[float] = Field(default=None, ge=0.0, description="Maximum cost constraint")
    
    @field_validator('strategy')
    @classmethod
    def validate_strategy(cls, v):
        """Validate routing strategy."""
        if v is not None:
            valid_strategies = ['cost_optimized', 'balanced', 'quality_first']
            if v not in valid_strategies:
                raise ValueError(f"Strategy must be one of: {valid_strategies}")
        return v