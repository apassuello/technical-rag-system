"""
REST API endpoints for API Gateway Service.
"""

import uuid
import time
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import JSONResponse
import structlog
from prometheus_client import Counter, Histogram, Gauge

from ..core.gateway import APIGatewayService
from ..schemas.requests import UnifiedQueryRequest, BatchQueryRequest
from ..schemas.responses import (
    UnifiedQueryResponse,
    BatchQueryResponse,
    GatewayStatusResponse,
    AvailableModelsResponse,
    ErrorResponse
)

logger = structlog.get_logger(__name__)

# Metrics
API_REQUESTS = Counter('gateway_api_requests_total', 'API requests', ['endpoint', 'method', 'status'])
API_REQUEST_DURATION = Histogram('gateway_api_request_duration_seconds', 'API request duration', ['endpoint'])
ACTIVE_REQUESTS = Gauge('gateway_active_requests', 'Currently active requests')
PIPELINE_ERRORS = Counter('gateway_pipeline_errors_total', 'Pipeline errors', ['error_type', 'service'])

router = APIRouter()


async def get_gateway_service() -> APIGatewayService:
    """Dependency to get gateway service from main app."""
    from ..main import get_gateway_service
    return get_gateway_service()


@router.post("/query", response_model=UnifiedQueryResponse)
async def process_unified_query(
    request: UnifiedQueryRequest,
    background_tasks: BackgroundTasks,
    gateway: APIGatewayService = Depends(get_gateway_service),
    http_request: Request = None
) -> UnifiedQueryResponse:
    """
    Process unified query through complete RAG pipeline.
    
    This endpoint orchestrates the complete query processing pipeline:
    1. Check cache for existing response (if enabled)
    2. Analyze query complexity and extract features
    3. Retrieve relevant documents based on analysis
    4. Generate answer using optimal model selection
    5. Cache response and record analytics (if enabled)
    
    Returns comprehensive response with answer, sources, cost breakdown,
    and performance metrics.
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        ACTIVE_REQUESTS.inc()
        
        logger.info(
            "Processing unified query request",
            request_id=request_id,
            query_length=len(request.query),
            strategy=request.options.strategy,
            session_id=request.session_id,
            user_id=request.user_id,
            cache_enabled=request.options.cache_enabled,
            max_cost=request.options.max_cost,
            max_documents=request.options.max_documents
        )
        
        # Process query through gateway
        response = await gateway.process_unified_query(request)
        
        # Update metrics
        duration = time.time() - start_time
        API_REQUESTS.labels(endpoint="query", method="POST", status="success").inc()
        API_REQUEST_DURATION.labels(endpoint="query").observe(duration)
        
        logger.info(
            "Unified query processed successfully",
            request_id=request_id,
            query_id=response.query_id,
            complexity=response.complexity,
            total_cost=response.cost.total_cost,
            processing_time=response.metrics.total_time,
            cache_hit=response.metrics.cache_hit,
            fallback_used=response.fallback_used,
            documents_retrieved=response.metrics.documents_retrieved,
            model_used=response.cost.model_used
        )
        
        return response
        
    except ValueError as e:
        API_REQUESTS.labels(endpoint="query", method="POST", status="validation_error").inc()
        PIPELINE_ERRORS.labels(error_type="validation", service="api-gateway").inc()
        logger.warning("Query validation error", request_id=request_id, error=str(e))
        raise HTTPException(status_code=422, detail=str(e))
        
    except Exception as e:
        API_REQUESTS.labels(endpoint="query", method="POST", status="error").inc()
        PIPELINE_ERRORS.labels(error_type="processing", service="api-gateway").inc()
        logger.error("Query processing failed", request_id=request_id, error=str(e))
        
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="QueryProcessingError",
                message="Query processing failed",
                details={"error": str(e), "error_type": type(e).__name__},
                request_id=request_id,
                suggestions=[
                    "Check service status at /api/v1/status",
                    "Verify query format and parameters",
                    "Try again with simpler query if complex"
                ]
            ).dict()
        )
    
    finally:
        ACTIVE_REQUESTS.dec()


@router.post("/batch-query", response_model=BatchQueryResponse)
async def process_batch_queries(
    request: BatchQueryRequest,
    background_tasks: BackgroundTasks,
    gateway: APIGatewayService = Depends(get_gateway_service),
    http_request: Request = None
) -> BatchQueryResponse:
    """
    Process multiple queries in batch with optional parallel processing.
    
    This endpoint supports efficient processing of multiple queries:
    - Parallel processing with configurable concurrency limits
    - Shared context and options across all queries
    - Comprehensive batch statistics and cost tracking
    - Individual query success/failure tracking
    
    Ideal for bulk analysis, A/B testing, or batch operations.
    """
    batch_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        ACTIVE_REQUESTS.inc()
        
        logger.info(
            "Processing batch query request",
            batch_id=batch_id,
            query_count=len(request.queries),
            parallel_processing=request.parallel_processing,
            max_parallel=request.max_parallel,
            session_id=request.session_id,
            user_id=request.user_id
        )
        
        # Validate batch size
        if len(request.queries) > 100:
            raise ValueError("Maximum 100 queries allowed per batch")
        
        # Process batch through gateway
        response = await gateway.process_batch_queries(request)
        
        # Update metrics
        duration = time.time() - start_time
        API_REQUESTS.labels(endpoint="batch-query", method="POST", status="success").inc()
        API_REQUEST_DURATION.labels(endpoint="batch-query").observe(duration)
        
        logger.info(
            "Batch queries processed successfully",
            batch_id=batch_id,
            response_batch_id=response.batch_id,
            total_queries=response.total_queries,
            successful_queries=response.successful_queries,
            failed_queries=response.failed_queries,
            total_cost=response.total_cost,
            processing_time=response.processing_time,
            parallel_processing=response.parallel_processing
        )
        
        return response
        
    except ValueError as e:
        API_REQUESTS.labels(endpoint="batch-query", method="POST", status="validation_error").inc()
        PIPELINE_ERRORS.labels(error_type="validation", service="api-gateway").inc()
        logger.warning("Batch validation error", batch_id=batch_id, error=str(e))
        raise HTTPException(status_code=422, detail=str(e))
        
    except Exception as e:
        API_REQUESTS.labels(endpoint="batch-query", method="POST", status="error").inc()
        PIPELINE_ERRORS.labels(error_type="batch_processing", service="api-gateway").inc()
        logger.error("Batch processing failed", batch_id=batch_id, error=str(e))
        
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="BatchProcessingError",
                message="Batch processing failed",
                details={"error": str(e), "error_type": type(e).__name__},
                request_id=batch_id,
                suggestions=[
                    "Check individual query formats",
                    "Reduce batch size if too large",
                    "Check service status at /api/v1/status"
                ]
            ).dict()
        )
    
    finally:
        ACTIVE_REQUESTS.dec()


@router.get("/status", response_model=GatewayStatusResponse)
async def get_gateway_status(
    include_services: bool = True,
    include_metrics: bool = True,
    gateway: APIGatewayService = Depends(get_gateway_service)
) -> GatewayStatusResponse:
    """
    Get comprehensive API Gateway status and health information.
    
    Query Parameters:
    - include_services: Include individual service health status (default: true)
    - include_metrics: Include performance metrics (default: true)
    
    Returns detailed information about:
    - Overall gateway health and uptime
    - Individual service status and response times
    - Performance metrics and error rates
    - Circuit breaker states
    - Cache performance statistics
    - Request processing statistics
    """
    try:
        logger.info(
            "Getting gateway status",
            include_services=include_services,
            include_metrics=include_metrics
        )
        
        status = await gateway.get_gateway_status()
        
        # Optionally filter response based on query parameters
        if not include_services:
            status.services = []
        
        if not include_metrics:
            status.requests_processed = 0
            status.average_response_time = 0.0
            status.error_rate = 0.0
            status.cache_hit_rate = None
            status.cache_size = None
        
        API_REQUESTS.labels(endpoint="status", method="GET", status="success").inc()
        
        logger.info(
            "Gateway status retrieved successfully",
            overall_status=status.status,
            healthy_services=status.healthy_services,
            total_services=status.total_services,
            uptime=status.uptime,
            requests_processed=status.requests_processed
        )
        
        return status
        
    except Exception as e:
        API_REQUESTS.labels(endpoint="status", method="GET", status="error").inc()
        logger.error("Failed to get gateway status", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get gateway status: {str(e)}"
        )


@router.get("/models", response_model=AvailableModelsResponse)
async def get_available_models(
    provider: str = None,
    available_only: bool = True,
    gateway: APIGatewayService = Depends(get_gateway_service)
) -> AvailableModelsResponse:
    """
    Get available models across all providers.
    
    Query Parameters:
    - provider: Filter by specific provider (e.g., 'openai', 'mistral', 'ollama')
    - available_only: Show only currently available models (default: true)
    
    Returns comprehensive information about:
    - Available models from all providers
    - Model capabilities and specifications
    - Cost information and context limits
    - Current availability status
    - Provider-specific details
    """
    try:
        logger.info(
            "Getting available models",
            provider_filter=provider,
            available_only=available_only
        )
        
        models_response = await gateway.get_available_models()
        
        # Apply filters
        if provider:
            models_response.models = [
                m for m in models_response.models 
                if m.provider.lower() == provider.lower()
            ]
        
        if available_only:
            models_response.models = [
                m for m in models_response.models if m.available
            ]
        
        # Update counts after filtering
        models_response.total_models = len(models_response.models)
        models_response.available_models = len([m for m in models_response.models if m.available])
        models_response.providers = list(set(m.provider for m in models_response.models))
        
        API_REQUESTS.labels(endpoint="models", method="GET", status="success").inc()
        
        logger.info(
            "Available models retrieved successfully",
            total_models=models_response.total_models,
            available_models=models_response.available_models,
            providers=len(models_response.providers),
            provider_filter=provider
        )
        
        return models_response
        
    except Exception as e:
        API_REQUESTS.labels(endpoint="models", method="GET", status="error").inc()
        logger.error("Failed to get available models", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get available models: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Simple health check endpoint for load balancers."""
    return {"status": "healthy", "service": "api-gateway", "timestamp": time.time()}


@router.get("/health/live")
async def liveness_probe():
    """Kubernetes liveness probe."""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_probe(
    gateway: APIGatewayService = Depends(get_gateway_service)
):
    """
    Kubernetes readiness probe - checks if gateway can process requests.
    """
    try:
        # Check if gateway service is initialized
        if not gateway:
            raise HTTPException(status_code=503, detail="Gateway service not initialized")
        
        # Basic connectivity check to critical services
        status = await gateway.get_gateway_status()
        
        # Gateway is ready if at least query analyzer and generator are healthy
        critical_services = ["query-analyzer", "generator"]
        healthy_critical = 0
        
        for service in status.services:
            if service.name in critical_services and service.status == "healthy":
                healthy_critical += 1
        
        if healthy_critical < len(critical_services):
            raise HTTPException(
                status_code=503, 
                detail=f"Critical services unavailable: {critical_services}"
            )
        
        return {"status": "ready"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Readiness check failed: {str(e)}")


@router.get("/metrics")
async def get_metrics():
    """
    Get gateway-specific metrics for monitoring.
    
    Returns metrics in Prometheus format compatible with observability stack.
    """
    try:
        # This endpoint would typically return Prometheus metrics
        # For now, return basic metrics in JSON format
        return {
            "requests_total": API_REQUESTS._value._value,
            "active_requests": ACTIVE_REQUESTS._value._value,
            "pipeline_errors_total": PIPELINE_ERRORS._value._value
        }
    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get metrics")


@router.post("/clear-cache")
async def clear_cache(
    pattern: str = None,
    gateway: APIGatewayService = Depends(get_gateway_service)
) -> Dict[str, Any]:
    """
    Clear cache entries (admin endpoint).
    
    Query Parameters:
    - pattern: Optional pattern to match cache keys
    
    Returns cache clear operation results.
    """
    try:
        logger.info("Clearing cache", pattern=pattern)
        
        # Call cache service through gateway
        result = await gateway.cache.clear_cache(pattern=pattern)
        
        logger.info(
            "Cache cleared successfully",
            keys_removed=result.get("keys_removed", 0),
            pattern=pattern
        )
        
        return result
        
    except Exception as e:
        logger.error("Failed to clear cache", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )