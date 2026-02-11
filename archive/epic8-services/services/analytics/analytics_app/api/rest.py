"""
REST API endpoints for Analytics Service.

This module implements all REST API endpoints for the Analytics Service,
providing cost tracking, performance analytics, and usage trend analysis.
"""

import time
import uuid
from typing import Any, Dict

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram

from ..core.analytics import AnalyticsService
from ..schemas.requests import (
    BatchRecordQueryRequest,
    RecordQueryRequest,
)
from ..schemas.responses import (
    BatchRecordQueryResponse,
    ErrorResponse,
    RecordQueryResponse,
)

logger = structlog.get_logger(__name__)

# Metrics
API_REQUESTS = Counter('analytics_api_requests_total', 'API requests', ['endpoint', 'method', 'status'])
API_REQUEST_DURATION = Histogram('analytics_api_request_duration_seconds', 'API request duration', ['endpoint'])

router = APIRouter()


async def get_analytics_service() -> AnalyticsService:
    """Dependency to get analytics service from main app."""
    from ..main import get_analytics_service
    return get_analytics_service()


@router.post("/record-query", response_model=RecordQueryResponse)
async def record_query_completion(
    request: RecordQueryRequest,
    analytics: AnalyticsService = Depends(get_analytics_service),
    http_request: Request = None
) -> RecordQueryResponse:
    """
    Record completion of a query for analytics tracking.
    
    This endpoint records comprehensive query data for both cost tracking
    (using Epic 1 CostTracker) and performance analytics. It supports
    multi-model cost tracking with $0.001 precision.
    
    Request Body:
    - query_id: Unique identifier for the query
    - query: The query text (for analysis)
    - complexity: Query complexity level (simple/medium/complex)
    - provider: LLM provider used (openai/mistral/ollama/anthropic)
    - model: Specific model used
    - cost_usd: Cost in USD
    - processing_time_ms: Total processing time
    - response_time_ms: Response generation time
    - input_tokens: Number of input tokens
    - output_tokens: Number of output tokens
    - success: Whether the query was successful
    - error_type: Type of error if unsuccessful
    - metadata: Additional metadata
    
    Returns comprehensive recording confirmation with tracking status.
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        logger.info(
            "Processing record query request",
            request_id=request_id,
            query_id=request.query_id,
            provider=request.provider,
            model=request.model,
            complexity=request.complexity,
            cost_usd=request.cost_usd
        )
        
        # Record the query completion
        await analytics.record_query_completion(
            query_id=request.query_id,
            query=request.query,
            complexity=request.complexity,
            provider=request.provider,
            model=request.model,
            cost_usd=request.cost_usd,
            processing_time_ms=request.processing_time_ms,
            response_time_ms=request.response_time_ms,
            input_tokens=request.input_tokens,
            output_tokens=request.output_tokens,
            success=request.success,
            error_type=request.error_type,
            metadata=request.metadata
        )
        
        # Update metrics
        duration = time.time() - start_time
        API_REQUESTS.labels(endpoint="record-query", method="POST", status="success").inc()
        API_REQUEST_DURATION.labels(endpoint="record-query").observe(duration)
        
        response = RecordQueryResponse(
            success=True,
            query_id=request.query_id,
            recorded_at=time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            cost_tracking_enabled=analytics.settings.enable_cost_tracking,
            performance_tracking_enabled=analytics.settings.enable_performance_tracking,
            message="Query recorded successfully with Epic 1 cost tracking"
        )
        
        logger.info(
            "Query recording completed successfully",
            request_id=request_id,
            query_id=request.query_id,
            duration=duration
        )
        
        return response
        
    except ValueError as e:
        API_REQUESTS.labels(endpoint="record-query", method="POST", status="validation_error").inc()
        logger.warning("Validation error", request_id=request_id, error=str(e))
        raise HTTPException(status_code=422, detail=str(e))
        
    except Exception as e:
        API_REQUESTS.labels(endpoint="record-query", method="POST", status="error").inc()
        logger.error("Query recording failed", request_id=request_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="RecordingError",
                message="Failed to record query completion",
                details={"error": str(e)},
                request_id=request_id
            ).model_dump()
        )


@router.get("/cost-report")
async def get_cost_report(
    time_range_hours: int = Query(24, ge=1, le=8760, description="Time range in hours"),
    include_recommendations: bool = Query(True, description="Include optimization recommendations"),
    analytics: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """
    Generate comprehensive cost optimization report.
    
    This endpoint provides detailed cost analysis using Epic 1 CostTracker
    with $0.001 precision, including:
    
    - Total cost breakdown by provider, model, and complexity
    - Cost optimization recommendations with potential savings
    - Budget status and alerts
    - Performance correlation data
    - Epic 1 integration status
    
    Query Parameters:
    - time_range_hours: Analysis time range (1 hour to 1 year)
    - include_recommendations: Include optimization recommendations (default: true)
    
    Returns comprehensive cost analysis with actionable insights.
    """
    start_time = time.time()
    
    try:
        logger.info(
            "Processing cost report request",
            time_range_hours=time_range_hours,
            include_recommendations=include_recommendations
        )
        
        # Generate cost report
        report = await analytics.get_cost_report(
            time_range_hours=time_range_hours,
            include_recommendations=include_recommendations
        )
        
        # Update metrics
        duration = time.time() - start_time
        API_REQUESTS.labels(endpoint="cost-report", method="GET", status="success").inc()
        API_REQUEST_DURATION.labels(endpoint="cost-report").observe(duration)
        
        logger.info(
            "Cost report generated successfully",
            time_range_hours=time_range_hours,
            total_cost=report.get("cost_summary", {}).get("total_cost_usd", 0),
            recommendations_count=len(report.get("optimization", {}).get("optimization_opportunities", [])),
            duration=duration
        )
        
        return report
        
    except Exception as e:
        API_REQUESTS.labels(endpoint="cost-report", method="GET", status="error").inc()
        logger.error("Cost report generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Cost report generation failed: {str(e)}")


@router.get("/performance-report")
async def get_performance_report(
    time_range_hours: int = Query(24, ge=1, le=8760, description="Time range in hours"),
    analytics: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """
    Generate comprehensive performance analytics report.
    
    This endpoint provides detailed performance analysis including:
    
    - Response time metrics (average, P95, P99)
    - Error rate analysis and trends
    - SLO compliance monitoring
    - Performance by complexity and provider
    - Optimization recommendations
    - Bottleneck identification
    
    Query Parameters:
    - time_range_hours: Analysis time range (1 hour to 1 year)
    
    Returns comprehensive performance analysis with SLO compliance status.
    """
    start_time = time.time()
    
    try:
        logger.info(
            "Processing performance report request",
            time_range_hours=time_range_hours
        )
        
        # Generate performance report
        report = await analytics.get_performance_report(time_range_hours=time_range_hours)
        
        # Update metrics
        duration = time.time() - start_time
        API_REQUESTS.labels(endpoint="performance-report", method="GET", status="success").inc()
        API_REQUEST_DURATION.labels(endpoint="performance-report").observe(duration)
        
        perf_metrics = report.get("performance_metrics", {})
        logger.info(
            "Performance report generated successfully",
            time_range_hours=time_range_hours,
            total_requests=perf_metrics.get("total_requests", 0),
            avg_response_time_ms=perf_metrics.get("avg_response_time_ms", 0),
            error_rate=perf_metrics.get("error_rate", 0),
            slo_compliance=perf_metrics.get("slo_compliance", 0),
            duration=duration
        )
        
        return report
        
    except Exception as e:
        API_REQUESTS.labels(endpoint="performance-report", method="GET", status="error").inc()
        logger.error("Performance report generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Performance report generation failed: {str(e)}")


@router.get("/usage-trends")
async def get_usage_trends(
    time_range_hours: int = Query(24, ge=1, le=8760, description="Time range in hours"),
    bucket_size_hours: int = Query(1, ge=1, le=168, description="Time bucket size in hours"),
    analytics: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """
    Generate usage pattern analysis and trends.
    
    This endpoint provides detailed usage trend analysis including:
    
    - Request volume trends over time
    - Response time patterns and seasonality
    - Cost trends and optimization opportunities  
    - Complexity distribution evolution
    - Provider usage patterns
    - Peak usage identification
    - Basic forecasting insights
    
    Query Parameters:
    - time_range_hours: Analysis time range (1 hour to 1 year)
    - bucket_size_hours: Size of time buckets for aggregation (1 hour to 1 week)
    
    Returns time-series usage data with trend analysis and patterns.
    """
    start_time = time.time()
    
    try:
        # Validate bucket size vs time range
        if bucket_size_hours > time_range_hours:
            raise HTTPException(
                status_code=422, 
                detail="Bucket size cannot be larger than time range"
            )
        
        logger.info(
            "Processing usage trends request",
            time_range_hours=time_range_hours,
            bucket_size_hours=bucket_size_hours
        )
        
        # Generate usage trends report
        report = await analytics.get_usage_trends(
            time_range_hours=time_range_hours,
            bucket_size_hours=bucket_size_hours
        )
        
        # Update metrics
        duration = time.time() - start_time
        API_REQUESTS.labels(endpoint="usage-trends", method="GET", status="success").inc()
        API_REQUEST_DURATION.labels(endpoint="usage-trends").observe(duration)
        
        logger.info(
            "Usage trends generated successfully",
            time_range_hours=time_range_hours,
            bucket_size_hours=bucket_size_hours,
            data_points=len(report.get("time_series_data", [])),
            duration=duration
        )
        
        return report
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        API_REQUESTS.labels(endpoint="usage-trends", method="GET", status="error").inc()
        logger.error("Usage trends generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Usage trends generation failed: {str(e)}")


@router.post("/batch-record")
async def batch_record_queries(
    request: BatchRecordQueryRequest,
    analytics: AnalyticsService = Depends(get_analytics_service)
) -> BatchRecordQueryResponse:
    """
    Record multiple query completions in batch.
    
    This endpoint allows bulk recording of query completion data,
    useful for batch analytics ingestion and historical data import.
    
    Request Body:
    - queries: List of query records (max 1000)
    - batch_id: Optional batch identifier for tracking
    
    Returns batch processing results with success/failure counts.
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        logger.info(
            "Processing batch record request",
            request_id=request_id,
            batch_id=request.batch_id,
            query_count=len(request.queries)
        )
        
        successful_records = 0
        failed_records = 0
        errors = []
        
        # Process each query in the batch
        for i, query_request in enumerate(request.queries):
            try:
                await analytics.record_query_completion(
                    query_id=query_request.query_id,
                    query=query_request.query,
                    complexity=query_request.complexity,
                    provider=query_request.provider,
                    model=query_request.model,
                    cost_usd=query_request.cost_usd,
                    processing_time_ms=query_request.processing_time_ms,
                    response_time_ms=query_request.response_time_ms,
                    input_tokens=query_request.input_tokens,
                    output_tokens=query_request.output_tokens,
                    success=query_request.success,
                    error_type=query_request.error_type,
                    metadata=query_request.metadata
                )
                successful_records += 1
                
            except Exception as e:
                failed_records += 1
                errors.append({
                    "index": i,
                    "query_id": query_request.query_id,
                    "error": str(e)
                })
                logger.warning(f"Failed to record query {i}", error=str(e), query_id=query_request.query_id)
        
        # Update metrics
        duration = time.time() - start_time
        status = "success" if failed_records == 0 else "partial_success" if successful_records > 0 else "error"
        API_REQUESTS.labels(endpoint="batch-record", method="POST", status=status).inc()
        API_REQUEST_DURATION.labels(endpoint="batch-record").observe(duration)
        
        response = BatchRecordQueryResponse(
            success=failed_records == 0,
            total_queries=len(request.queries),
            successful_records=successful_records,
            failed_records=failed_records,
            batch_id=request.batch_id,
            recorded_at=time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            errors=errors
        )
        
        logger.info(
            "Batch recording completed",
            request_id=request_id,
            batch_id=request.batch_id,
            successful=successful_records,
            failed=failed_records,
            duration=duration
        )
        
        return response
        
    except Exception as e:
        API_REQUESTS.labels(endpoint="batch-record", method="POST", status="error").inc()
        logger.error("Batch recording failed", request_id=request_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Batch recording failed: {str(e)}")


@router.get("/status")
async def get_service_status(
    include_details: bool = Query(True, description="Include detailed status information"),
    analytics: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """
    Get comprehensive Analytics Service status.
    
    This endpoint provides detailed service status including:
    
    - Service health and initialization status
    - Component health (cost tracker, metrics store, circuit breaker)
    - Epic 1 integration status
    - Configuration information
    - Performance metrics
    - Circuit breaker state
    
    Query Parameters:
    - include_details: Include detailed status information (default: true)
    
    Returns comprehensive service status information.
    """
    try:
        logger.info(
            "Getting Analytics Service status",
            include_details=include_details
        )
        
        # Get comprehensive service status
        status = await analytics.get_service_status()
        
        # Add API-specific information
        status["api_version"] = "1.0.0"
        status["endpoints"] = {
            "record_query": "POST /api/v1/record-query",
            "cost_report": "GET /api/v1/cost-report",
            "performance_report": "GET /api/v1/performance-report",
            "usage_trends": "GET /api/v1/usage-trends",
            "batch_record": "POST /api/v1/batch-record",
            "status": "GET /api/v1/status"
        }
        
        # Add Epic 8 compliance information
        status["epic8_compliance"] = {
            "cost_tracking_precision": "0.001 USD (Epic 1 integration)",
            "multi_model_support": True,
            "real_time_analytics": True,
            "slo_monitoring": True,
            "circuit_breaker_pattern": analytics.settings.circuit_breaker_enabled
        }
        
        API_REQUESTS.labels(endpoint="status", method="GET", status="success").inc()
        
        logger.info(
            "Status request completed successfully",
            service_status=status.get("status"),
            cost_tracking_enabled=status.get("components", {}).get("cost_tracker", {}).get("enabled", False),
            performance_tracking_enabled=status.get("components", {}).get("metrics_store", {}).get("enabled", False)
        )
        
        return status
        
    except Exception as e:
        API_REQUESTS.labels(endpoint="status", method="GET", status="error").inc()
        logger.error("Failed to get service status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Status request failed: {str(e)}")


@router.get("/export/{format_type}")
async def export_analytics_data(
    format_type: str,
    time_range_hours: int = Query(24, ge=1, le=8760, description="Time range in hours"),
    include_metadata: bool = Query(True, description="Include metadata in export"),
    analytics: AnalyticsService = Depends(get_analytics_service)
) -> JSONResponse:
    """
    Export analytics data in specified format.
    
    This endpoint allows exporting of cost tracking and performance data
    for external analysis, reporting, and data integration.
    
    Path Parameters:
    - format_type: Export format ("json" or "csv")
    
    Query Parameters:
    - time_range_hours: Time range for export
    - include_metadata: Include metadata fields in export
    
    Returns exported data in specified format.
    """
    try:
        if format_type.lower() not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")
        
        logger.info(
            "Processing data export request",
            format_type=format_type,
            time_range_hours=time_range_hours,
            include_metadata=include_metadata
        )
        
        # Export cost data using Epic 1 CostTracker
        if analytics.settings.enable_cost_tracking:
            exported_data = await analytics.cost_tracker.export_cost_data(
                format_type=format_type.lower(),
                include_metadata=include_metadata
            )
        else:
            exported_data = '[]' if format_type.lower() == 'json' else ''
        
        # Set appropriate content type
        if format_type.lower() == 'csv':
            media_type = 'text/csv'
            filename = f"analytics_data_{int(time.time())}.csv"
        else:
            media_type = 'application/json'
            filename = f"analytics_data_{int(time.time())}.json"
        
        API_REQUESTS.labels(endpoint="export", method="GET", status="success").inc()
        
        logger.info(
            "Data export completed successfully",
            format_type=format_type,
            data_size=len(exported_data)
        )
        
        return JSONResponse(
            content=exported_data if format_type.lower() == 'json' else {"data": exported_data},
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        API_REQUESTS.labels(endpoint="export", method="GET", status="error").inc()
        logger.error("Data export failed", error=str(e), format_type=format_type)
        raise HTTPException(status_code=500, detail=f"Data export failed: {str(e)}")