"""
Request schemas for Analytics Service.

This module defines Pydantic models for all Analytics Service REST API requests.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class RecordQueryRequest(BaseModel):
    """
    Request to record a completed query for analytics.
    
    This is the primary request type for recording query completion
    data that will be used for cost tracking and performance analytics.
    """
    query_id: str = Field(..., description="Unique identifier for the query")
    query: str = Field(..., description="The query text (for analysis)")
    complexity: str = Field(..., description="Query complexity level (simple/medium/complex)")
    provider: str = Field(..., description="LLM provider used (openai/mistral/ollama/anthropic)")
    model: str = Field(..., description="Specific model used (e.g., gpt-4, llama3.2:3b)")
    cost_usd: float = Field(..., ge=0, description="Cost in USD")
    processing_time_ms: float = Field(..., ge=0, description="Total processing time in milliseconds")
    response_time_ms: float = Field(..., ge=0, description="Response generation time in milliseconds")
    input_tokens: int = Field(default=0, ge=0, description="Number of input tokens")
    output_tokens: int = Field(default=0, ge=0, description="Number of output tokens")
    success: bool = Field(default=True, description="Whether the query was successful")
    error_type: Optional[str] = Field(None, description="Type of error if unsuccessful")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator("complexity")
    @classmethod
    def validate_complexity(cls, v):
        """Validate complexity is one of the allowed values."""
        if v.lower() not in ["simple", "medium", "complex"]:
            raise ValueError("Complexity must be one of: simple, medium, complex")
        return v.lower()
    
    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v):
        """Validate provider is one of the supported providers."""
        if v.lower() not in ["openai", "mistral", "ollama", "anthropic", "huggingface"]:
            raise ValueError("Provider must be one of: openai, mistral, ollama, anthropic, huggingface")
        return v.lower()
    
    @field_validator("query")
    @classmethod
    def validate_query_length(cls, v):
        """Limit query length for storage efficiency."""
        if len(v) > 10000:
            raise ValueError("Query length must be <= 10000 characters")
        return v


class BatchRecordQueryRequest(BaseModel):
    """
    Request to record multiple completed queries in batch.
    
    Useful for bulk analytics data ingestion.
    """
    queries: List[RecordQueryRequest] = Field(..., description="List of query records")
    batch_id: Optional[str] = Field(None, description="Optional batch identifier")
    
    @field_validator("queries")
    @classmethod
    def validate_batch_size(cls, v):
        """Limit batch size to prevent resource exhaustion."""
        if len(v) > 1000:
            raise ValueError("Batch size must be <= 1000 queries")
        if len(v) == 0:
            raise ValueError("At least one query is required")
        return v


class CostReportRequest(BaseModel):
    """
    Request for cost optimization report.
    """
    time_range_hours: int = Field(default=24, ge=1, le=8760, description="Time range in hours (max 1 year)")
    include_recommendations: bool = Field(default=True, description="Include optimization recommendations")
    include_detailed_breakdown: bool = Field(default=True, description="Include detailed cost breakdown")
    group_by: Optional[str] = Field(None, description="Group results by: provider, model, complexity")
    
    @field_validator("group_by")
    @classmethod
    def validate_group_by(cls, v):
        """Validate group_by parameter."""
        if v is not None and v.lower() not in ["provider", "model", "complexity"]:
            raise ValueError("group_by must be one of: provider, model, complexity")
        return v.lower() if v else None


class PerformanceReportRequest(BaseModel):
    """
    Request for performance analytics report.
    """
    time_range_hours: int = Field(default=24, ge=1, le=8760, description="Time range in hours (max 1 year)")
    include_slo_analysis: bool = Field(default=True, description="Include SLO compliance analysis")
    include_trends: bool = Field(default=True, description="Include performance trends")
    percentiles: List[float] = Field(default=[0.50, 0.90, 0.95, 0.99], description="Response time percentiles to calculate")
    
    @field_validator("percentiles")
    @classmethod
    def validate_percentiles(cls, v):
        """Validate percentiles are valid."""
        for p in v:
            if not 0.0 <= p <= 1.0:
                raise ValueError(f"Percentile {p} must be between 0.0 and 1.0")
        return sorted(v)


class UsageTrendsRequest(BaseModel):
    """
    Request for usage trends analysis.
    """
    time_range_hours: int = Field(default=24, ge=1, le=8760, description="Time range in hours (max 1 year)")
    bucket_size_hours: int = Field(default=1, ge=1, le=168, description="Size of time buckets in hours (max 1 week)")
    include_patterns: bool = Field(default=True, description="Include usage pattern analysis")
    include_forecasting: bool = Field(default=False, description="Include basic usage forecasting")
    
    @field_validator("bucket_size_hours")
    @classmethod
    def validate_bucket_size(cls, v, values):
        """Validate bucket size is reasonable for the time range."""
        time_range = values.get("time_range_hours", 24)
        if v > time_range:
            raise ValueError("Bucket size cannot be larger than time range")
        return v


class ABTestRequest(BaseModel):
    """
    Request for A/B test analysis.
    """
    test_id: str = Field(..., description="A/B test identifier")
    time_range_hours: int = Field(default=24, ge=1, le=8760, description="Time range for analysis")
    metrics: List[str] = Field(default=["response_time", "cost", "success_rate"], description="Metrics to analyze")
    confidence_level: float = Field(default=0.95, ge=0.8, le=0.99, description="Statistical confidence level")
    
    @field_validator("metrics")
    @classmethod
    def validate_metrics(cls, v):
        """Validate metrics are supported."""
        valid_metrics = ["response_time", "cost", "success_rate", "error_rate", "user_satisfaction"]
        for metric in v:
            if metric not in valid_metrics:
                raise ValueError(f"Metric '{metric}' not supported. Valid metrics: {valid_metrics}")
        return v


class HealthCheckRequest(BaseModel):
    """
    Request for health check with options.
    """
    include_details: bool = Field(default=True, description="Include detailed health information")
    check_dependencies: bool = Field(default=True, description="Check external dependencies")
    timeout_seconds: int = Field(default=10, ge=1, le=60, description="Health check timeout")