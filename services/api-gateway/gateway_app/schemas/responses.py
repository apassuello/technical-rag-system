"""
Response schemas for API Gateway Service.
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime, timezone


def utc_now() -> datetime:
    """Get current UTC datetime using timezone-aware format."""
    return datetime.now(timezone.utc)

class DocumentSource(BaseModel):
    """Document source information."""
    
    id: str = Field(..., description="Document identifier")
    title: Optional[str] = Field(None, description="Document title")
    content: str = Field(..., description="Document content/excerpt")
    score: float = Field(..., description="Relevance score", ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")


class ProcessingMetrics(BaseModel):
    """Processing performance metrics."""
    
    analysis_time: float = Field(..., description="Query analysis time in seconds")
    retrieval_time: float = Field(..., description="Document retrieval time in seconds") 
    generation_time: float = Field(..., description="Answer generation time in seconds")
    cache_time: Optional[float] = Field(None, description="Cache operation time in seconds")
    total_time: float = Field(..., description="Total processing time in seconds")
    
    documents_retrieved: int = Field(..., description="Number of documents retrieved")
    tokens_generated: Optional[int] = Field(None, description="Number of tokens generated")
    
    cache_hit: bool = Field(..., description="Whether result came from cache")
    cache_key: Optional[str] = Field(None, description="Cache key used")


class CostBreakdown(BaseModel):
    """Cost breakdown for query processing."""
    
    model_used: str = Field(..., description="Model used for generation")
    input_tokens: Optional[int] = Field(None, description="Number of input tokens")
    output_tokens: Optional[int] = Field(None, description="Number of output tokens")
    
    model_cost: float = Field(..., description="Cost for model usage", ge=0.0)
    retrieval_cost: float = Field(default=0.0, description="Cost for retrieval", ge=0.0)
    total_cost: float = Field(..., description="Total cost for query", ge=0.0)
    
    cost_estimation_confidence: float = Field(
        default=1.0, 
        description="Confidence in cost estimation",
        ge=0.0,
        le=1.0
    )


class UnifiedQueryResponse(BaseModel):
    """Unified response from API Gateway."""
    
    # Core response
    answer: str = Field(..., description="Generated answer")
    sources: List[DocumentSource] = Field(
        default_factory=list,
        description="Source documents used"
    )
    
    # Processing information
    complexity: str = Field(..., description="Determined query complexity")
    confidence: float = Field(
        ..., 
        description="Confidence in response quality",
        ge=0.0,
        le=1.0
    )
    
    # Cost and performance
    cost: CostBreakdown = Field(..., description="Cost breakdown")
    metrics: ProcessingMetrics = Field(..., description="Processing metrics")
    
    # Metadata
    query_id: str = Field(..., description="Unique query identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    timestamp: datetime = Field(default_factory=utc_now)
    
    # Gateway-specific
    strategy_used: str = Field(..., description="Strategy used for processing")
    fallback_used: bool = Field(default=False, description="Whether fallback was used")
    
    # Error information (if any)
    warnings: List[str] = Field(default_factory=list, description="Processing warnings")


class BatchQueryResult(BaseModel):
    """Result for a single query in batch processing."""
    
    index: int = Field(..., description="Query index in batch")
    query: str = Field(..., description="Original query")
    success: bool = Field(..., description="Whether processing succeeded")
    
    # Success case
    result: Optional[UnifiedQueryResponse] = Field(None, description="Query result")
    
    # Error case
    error: Optional[str] = Field(None, description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")


class BatchQueryResponse(BaseModel):
    """Response for batch query processing."""
    
    # Batch metadata
    batch_id: str = Field(..., description="Unique batch identifier")
    total_queries: int = Field(..., description="Total number of queries in batch")
    successful_queries: int = Field(..., description="Number of successful queries")
    failed_queries: int = Field(..., description="Number of failed queries")
    
    # Processing information
    processing_time: float = Field(..., description="Total batch processing time")
    parallel_processing: bool = Field(..., description="Whether parallel processing was used")
    
    # Results
    results: List[BatchQueryResult] = Field(..., description="Individual query results")
    
    # Summary statistics
    summary: Dict[str, Any] = Field(..., description="Batch processing summary")
    
    # Cost information
    total_cost: float = Field(..., description="Total cost for batch", ge=0.0)
    average_cost_per_query: float = Field(..., description="Average cost per query", ge=0.0)
    
    # Metadata
    timestamp: datetime = Field(default_factory=utc_now)
    session_id: Optional[str] = Field(None, description="Session identifier")


class ServiceStatus(BaseModel):
    """Status of an individual service."""
    
    name: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    url: str = Field(..., description="Service URL")
    response_time: Optional[float] = Field(None, description="Last response time")
    last_check: datetime = Field(default_factory=utc_now)
    error: Optional[str] = Field(None, description="Last error message")


class GatewayStatusResponse(BaseModel):
    """Gateway status response."""
    
    # Gateway info
    service: str = Field(default="api-gateway")
    version: str = Field(default="1.0.0")
    status: str = Field(..., description="Overall gateway status")
    uptime: float = Field(..., description="Gateway uptime in seconds")
    
    # Service health
    services: List[ServiceStatus] = Field(..., description="Status of connected services")
    healthy_services: int = Field(..., description="Number of healthy services")
    total_services: int = Field(..., description="Total number of services")
    
    # Performance metrics
    requests_processed: int = Field(..., description="Total requests processed")
    average_response_time: float = Field(..., description="Average response time")
    error_rate: float = Field(..., description="Error rate percentage")
    
    # Circuit breaker status
    circuit_breakers: Dict[str, str] = Field(..., description="Circuit breaker states")
    
    # Cache metrics
    cache_hit_rate: Optional[float] = Field(None, description="Cache hit rate")
    cache_size: Optional[int] = Field(None, description="Current cache size")
    
    # Timestamp
    timestamp: datetime = Field(default_factory=utc_now)


class ModelInfo(BaseModel):
    """Information about available model."""
    
    name: str = Field(..., description="Model name")
    provider: str = Field(..., description="Model provider")
    type: str = Field(..., description="Model type")
    context_length: Optional[int] = Field(None, description="Maximum context length")
    cost_per_token: Optional[float] = Field(None, description="Cost per token")
    description: Optional[str] = Field(None, description="Model description")
    capabilities: List[str] = Field(default_factory=list, description="Model capabilities")
    available: bool = Field(..., description="Whether model is currently available")
    last_checked: datetime = Field(default_factory=utc_now)


class AvailableModelsResponse(BaseModel):
    """Response for available models endpoint."""
    
    models: List[ModelInfo] = Field(..., description="Available models")
    total_models: int = Field(..., description="Total number of models")
    available_models: int = Field(..., description="Number of available models")
    providers: List[str] = Field(..., description="Available providers")
    last_updated: datetime = Field(default_factory=utc_now)


class ErrorResponse(BaseModel):
    """Error response schema."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    request_id: Optional[str] = Field(None, description="Request identifier")
    timestamp: datetime = Field(default_factory=utc_now)
    suggestions: Optional[List[str]] = Field(None, description="Suggested actions")