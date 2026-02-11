"""
Response schemas for Analytics Service.

This module defines Pydantic models for all Analytics Service REST API responses.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service health status (healthy/unhealthy)")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional health details")


class RecordQueryResponse(BaseModel):
    """Response after recording a query."""
    success: bool = Field(..., description="Whether recording was successful")
    query_id: str = Field(..., description="Query ID that was recorded")
    recorded_at: str = Field(..., description="Timestamp when recorded (ISO format)")
    cost_tracking_enabled: bool = Field(..., description="Whether cost tracking is active")
    performance_tracking_enabled: bool = Field(..., description="Whether performance tracking is active")
    message: str = Field(default="Query recorded successfully", description="Status message")


class BatchRecordQueryResponse(BaseModel):
    """Response after recording multiple queries."""
    success: bool = Field(..., description="Whether batch recording was successful")
    total_queries: int = Field(..., description="Total number of queries in batch")
    successful_records: int = Field(..., description="Number of successfully recorded queries")
    failed_records: int = Field(..., description="Number of failed records")
    batch_id: Optional[str] = Field(None, description="Batch identifier")
    recorded_at: str = Field(..., description="Timestamp when recorded (ISO format)")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="List of errors for failed records")


class CostSummary(BaseModel):
    """Cost summary data."""
    total_cost_usd: float = Field(..., description="Total cost in USD")
    total_requests: int = Field(..., description="Total number of requests")
    avg_cost_per_request: float = Field(..., description="Average cost per request")
    cost_by_provider: Dict[str, float] = Field(..., description="Cost breakdown by provider")
    cost_by_model: Dict[str, float] = Field(..., description="Cost breakdown by model")
    cost_by_complexity: Dict[str, float] = Field(..., description="Cost breakdown by complexity")


class OptimizationRecommendation(BaseModel):
    """Cost optimization recommendation."""
    type: str = Field(..., description="Recommendation type")
    priority: str = Field(..., description="Priority level (high/medium/low)")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    suggestion: str = Field(..., description="Actionable suggestion")
    potential_savings: str = Field(..., description="Estimated potential savings")


class CostReportResponse(BaseModel):
    """Cost optimization report response."""
    report_type: str = Field(default="cost_analysis", description="Report type")
    time_range_hours: int = Field(..., description="Time range analyzed")
    generated_at: str = Field(..., description="Report generation timestamp (ISO format)")
    cost_summary: CostSummary = Field(..., description="Cost summary data")
    optimization_recommendations: List[OptimizationRecommendation] = Field(default_factory=list, description="Optimization recommendations")
    budget_status: Dict[str, Any] = Field(..., description="Budget status and alerts")
    epic1_integration: bool = Field(default=True, description="Epic 1 CostTracker integration status")


class PerformanceMetrics(BaseModel):
    """Performance metrics data."""
    total_requests: int = Field(..., description="Total number of requests")
    successful_requests: int = Field(..., description="Number of successful requests")
    failed_requests: int = Field(..., description="Number of failed requests")
    avg_response_time_ms: float = Field(..., description="Average response time in milliseconds")
    p95_response_time_ms: float = Field(..., description="95th percentile response time")
    p99_response_time_ms: float = Field(..., description="99th percentile response time")
    error_rate: float = Field(..., description="Error rate (0.0 to 1.0)")
    requests_per_second: float = Field(..., description="Requests per second")
    slo_compliance: float = Field(..., description="SLO compliance percentage")


class SLOStatus(BaseModel):
    """SLO compliance status."""
    response_time_slo: int = Field(..., description="Response time SLO in milliseconds")
    error_rate_slo: float = Field(..., description="Error rate SLO threshold")
    availability_slo: float = Field(..., description="Availability SLO threshold")
    current_compliance: float = Field(..., description="Current SLO compliance percentage")
    response_time_compliant: bool = Field(..., description="Whether response time meets SLO")
    error_rate_compliant: bool = Field(..., description="Whether error rate meets SLO")
    availability_compliant: bool = Field(..., description="Whether availability meets SLO")


class PerformanceRecommendation(BaseModel):
    """Performance optimization recommendation."""
    type: str = Field(..., description="Recommendation type")
    priority: str = Field(..., description="Priority level")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    suggestions: List[str] = Field(..., description="List of actionable suggestions")


class PerformanceReportResponse(BaseModel):
    """Performance analytics report response."""
    report_type: str = Field(default="performance_analysis", description="Report type")
    time_range_hours: int = Field(..., description="Time range analyzed")
    generated_at: str = Field(..., description="Report generation timestamp")
    performance_metrics: PerformanceMetrics = Field(..., description="Core performance metrics")
    slo_status: SLOStatus = Field(..., description="SLO compliance status")
    complexity_analysis: Dict[str, Any] = Field(..., description="Analysis by query complexity")
    provider_analysis: Dict[str, Any] = Field(..., description="Analysis by provider/model")
    recommendations: List[PerformanceRecommendation] = Field(default_factory=list, description="Performance recommendations")


class UsageTrendPoint(BaseModel):
    """Single usage trend data point."""
    timestamp: str = Field(..., description="Timestamp (ISO format)")
    request_count: int = Field(..., description="Number of requests in time bucket")
    avg_response_time: float = Field(..., description="Average response time for bucket")
    error_rate: float = Field(..., description="Error rate for bucket")
    cost_usd: float = Field(..., description="Total cost for bucket")
    complexity_distribution: Dict[str, int] = Field(..., description="Distribution of complexity levels")
    provider_distribution: Dict[str, int] = Field(..., description="Distribution of providers used")


class TrendAnalysis(BaseModel):
    """Trend analysis results."""
    request_volume_trend: str = Field(..., description="Request volume trend (increasing/decreasing/stable)")
    response_time_trend: str = Field(..., description="Response time trend")
    error_rate_trend: str = Field(..., description="Error rate trend")
    cost_trend: str = Field(..., description="Cost trend")
    peak_usage_time: Optional[str] = Field(None, description="Time of peak usage")
    complexity_patterns: Dict[str, Any] = Field(..., description="Complexity usage patterns")
    provider_usage_patterns: Dict[str, Any] = Field(..., description="Provider usage patterns")


class UsageTrendsResponse(BaseModel):
    """Usage trends analysis response."""
    report_type: str = Field(default="usage_trends", description="Report type")
    time_range_hours: int = Field(..., description="Time range analyzed")
    bucket_size_hours: int = Field(..., description="Time bucket size")
    generated_at: str = Field(..., description="Report generation timestamp")
    trend_analysis: TrendAnalysis = Field(..., description="Trend analysis results")
    time_series_data: List[UsageTrendPoint] = Field(..., description="Time series data points")


class ABTestResult(BaseModel):
    """A/B test analysis result."""
    test_id: str = Field(..., description="A/B test identifier")
    variant_a_metrics: Dict[str, float] = Field(..., description="Variant A metrics")
    variant_b_metrics: Dict[str, float] = Field(..., description="Variant B metrics")
    statistical_significance: Dict[str, bool] = Field(..., description="Statistical significance by metric")
    confidence_intervals: Dict[str, Dict[str, float]] = Field(..., description="Confidence intervals")
    recommendation: str = Field(..., description="Test conclusion recommendation")


class ABTestResponse(BaseModel):
    """A/B test analysis response."""
    test_id: str = Field(..., description="A/B test identifier")
    time_range_hours: int = Field(..., description="Analysis time range")
    generated_at: str = Field(..., description="Analysis generation timestamp")
    result: ABTestResult = Field(..., description="A/B test analysis results")


class ServiceStatus(BaseModel):
    """Service status information."""
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    status: str = Field(..., description="Service status")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    initialized: bool = Field(..., description="Whether service is initialized")
    components: Dict[str, Dict[str, Any]] = Field(..., description="Component status information")
    configuration: Dict[str, Any] = Field(..., description="Service configuration")


class ErrorResponse(BaseModel):
    """Error response format."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Error timestamp")


class ValidationErrorResponse(BaseModel):
    """Validation error response format."""
    error: str = Field(default="ValidationError", description="Error type")
    message: str = Field(..., description="Validation error message")
    field_errors: List[Dict[str, Any]] = Field(..., description="Field-specific validation errors")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


# API Response wrapper for consistency
class APIResponse(BaseModel):
    """Generic API response wrapper."""
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Union[
        CostReportResponse,
        PerformanceReportResponse, 
        UsageTrendsResponse,
        ABTestResponse,
        ServiceStatus,
        RecordQueryResponse,
        BatchRecordQueryResponse
    ]] = Field(None, description="Response data")
    error: Optional[ErrorResponse] = Field(None, description="Error information if unsuccessful")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")