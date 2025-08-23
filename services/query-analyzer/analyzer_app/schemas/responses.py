"""
Response schemas for Query Analyzer Service API.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class AnalyzeResponse(BaseModel):
    """Response model for query analysis."""
    
    query: str = Field(..., description="The original query text")
    
    complexity: str = Field(
        ...,
        description="Query complexity level (simple/medium/complex)"
    )
    
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for the complexity classification"
    )
    
    features: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted features from the query"
    )
    
    recommended_models: List[str] = Field(
        default_factory=list,
        description="List of recommended models for this query"
    )
    
    cost_estimate: Dict[str, float] = Field(
        default_factory=dict,
        description="Estimated cost per model in USD"
    )
    
    routing_strategy: str = Field(
        default="balanced",
        description="Routing strategy used (cost_optimized/balanced/quality_first)"
    )
    
    processing_time: float = Field(
        ...,
        ge=0.0,
        description="Processing time in seconds"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the analysis"
    )


class StatusResponse(BaseModel):
    """Response model for analyzer status."""
    
    initialized: bool = Field(..., description="Whether the analyzer is initialized")
    
    status: str = Field(..., description="Current status (healthy/unhealthy/not_initialized)")
    
    analyzer_type: Optional[str] = Field(
        default=None,
        description="Type of analyzer being used"
    )
    
    configuration: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Current analyzer configuration"
    )
    
    performance: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Performance metrics"
    )
    
    components: Optional[Dict[str, str]] = Field(
        default=None,
        description="Status of individual components"
    )
    
    error: Optional[str] = Field(
        default=None,
        description="Error message if status is unhealthy"
    )


class HealthResponse(BaseModel):
    """Response model for health checks."""
    
    status: str = Field(..., description="Health status (healthy/unhealthy)")
    
    service: str = Field(..., description="Service name")
    
    version: str = Field(..., description="Service version")
    
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional health check details"
    )


class ErrorResponse(BaseModel):
    """Response model for API errors."""
    
    error: str = Field(..., description="Error type")
    
    message: str = Field(..., description="Error message")
    
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )
    
    request_id: Optional[str] = Field(
        default=None,
        description="Request ID for tracking"
    )