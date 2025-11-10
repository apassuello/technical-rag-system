"""
Response schemas for Generator Service API.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class RoutingDecision(BaseModel):
    """Model routing decision information."""
    
    strategy: str = Field(..., description="Routing strategy used")
    available_models: List[str] = Field(default_factory=list, description="Models that were available")
    selection_reason: str = Field(..., description="Reason for model selection")
    fallback_used: bool = Field(default=False, description="Whether fallback was used")
    cost_estimate: float = Field(..., ge=0.0, description="Estimated cost for this selection")


class GenerateResponse(BaseModel):
    """Response model for answer generation."""
    
    answer: str = Field(..., description="The generated answer")
    query: str = Field(..., description="The original query")
    model_used: str = Field(..., description="Model that generated the answer")
    cost: float = Field(..., ge=0.0, description="Actual cost of generation in USD")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Answer confidence score")
    routing_decision: RoutingDecision = Field(..., description="Routing decision details")
    processing_time: float = Field(..., ge=0.0, description="Processing time in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BatchGenerateResponse(BaseModel):
    """Response model for batch generation."""
    
    results: List[Dict[str, Any]] = Field(..., description="Generation results")
    batch_summary: Dict[str, Any] = Field(..., description="Batch processing summary")
    total_cost: float = Field(..., ge=0.0, description="Total batch cost in USD")
    total_processing_time: float = Field(..., ge=0.0, description="Total processing time")


class ModelInfo(BaseModel):
    """Model information."""
    
    name: str = Field(..., description="Model name")
    provider: str = Field(..., description="Model provider (ollama, openai, mistral)")
    available: bool = Field(..., description="Whether model is currently available")
    cost_per_token: Optional[float] = Field(default=None, description="Cost per token in USD")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens supported")
    capabilities: List[str] = Field(default_factory=list, description="Model capabilities")


class ModelsResponse(BaseModel):
    """Response model for available models."""
    
    models: List[ModelInfo] = Field(..., description="Available models")
    total_models: int = Field(..., description="Total number of models")
    healthy_models: int = Field(..., description="Number of healthy models")
    cost_range: Dict[str, float] = Field(..., description="Cost range (min/max)")


class GeneratorStatusResponse(BaseModel):
    """Response model for generator status."""
    
    initialized: bool = Field(..., description="Whether generator is initialized")
    status: str = Field(..., description="Current status")
    generator_type: Optional[str] = Field(default=None, description="Type of generator")
    configuration: Optional[Dict[str, Any]] = Field(default=None, description="Current configuration")
    models: Optional[Dict[str, Any]] = Field(default=None, description="Model information")
    components: Optional[Dict[str, str]] = Field(default=None, description="Component status")
    error: Optional[str] = Field(default=None, description="Error message if unhealthy")


class RoutingTestResponse(BaseModel):
    """Response model for routing tests."""
    
    query: str = Field(..., description="The test query")
    recommended_model: str = Field(..., description="Recommended model")
    strategy_used: str = Field(..., description="Strategy used for selection")
    cost_estimate: float = Field(..., ge=0.0, description="Estimated cost")
    selection_reasoning: str = Field(..., description="Detailed reasoning for selection")
    alternative_models: List[Dict[str, Any]] = Field(..., description="Alternative model options")


class HealthResponse(BaseModel):
    """Response model for health checks."""
    
    status: str = Field(..., description="Health status (healthy/unhealthy)")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Health check details")


class ErrorResponse(BaseModel):
    """Response model for API errors."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracking")


class CostSummaryResponse(BaseModel):
    """Response model for cost summaries."""
    
    total_cost: float = Field(..., ge=0.0, description="Total cost in USD")
    cost_by_model: Dict[str, float] = Field(..., description="Cost breakdown by model")
    request_count: int = Field(..., description="Number of requests processed")
    average_cost_per_request: float = Field(..., ge=0.0, description="Average cost per request")
    time_period: str = Field(..., description="Time period for this summary")
    budget_status: Dict[str, Any] = Field(..., description="Budget utilization status")