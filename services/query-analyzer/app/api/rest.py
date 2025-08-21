"""
REST API endpoints for Query Analyzer Service.
"""

import uuid
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
import structlog
from prometheus_client import Counter, Histogram
import time

from ..core.analyzer import QueryAnalyzerService
from ..schemas.requests import AnalyzeRequest, StatusRequest
from ..schemas.responses import AnalyzeResponse, StatusResponse, ErrorResponse

logger = structlog.get_logger(__name__)

# Metrics
API_REQUESTS = Counter('query_analyzer_api_requests_total', 'API requests', ['endpoint', 'method', 'status'])
API_REQUEST_DURATION = Histogram('query_analyzer_api_request_duration_seconds', 'API request duration', ['endpoint'])

router = APIRouter()


async def get_analyzer_service() -> QueryAnalyzerService:
    """Dependency to get analyzer service from main app."""
    # This will be injected by the main app
    from ..main import get_analyzer_service
    return get_analyzer_service()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_query(
    request: AnalyzeRequest,
    analyzer: QueryAnalyzerService = Depends(get_analyzer_service),
    http_request: Request = None
) -> AnalyzeResponse:
    """
    Analyze a query for complexity classification and model recommendation.
    
    This endpoint takes a query string and returns:
    - Complexity level (simple/medium/complex)
    - Confidence score
    - Extracted features
    - Recommended models
    - Cost estimates
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        logger.info(
            "Processing analyze request",
            request_id=request_id,
            query_length=len(request.query),
            has_context=request.context is not None
        )
        
        # Perform analysis
        result = await analyzer.analyze_query(
            query=request.query,
            context=request.context
        )
        
        # Convert to response model
        response = AnalyzeResponse(**result)
        
        # Update metrics
        duration = time.time() - start_time
        API_REQUESTS.labels(endpoint="analyze", method="POST", status="success").inc()
        API_REQUEST_DURATION.labels(endpoint="analyze").observe(duration)
        
        logger.info(
            "Analysis completed successfully",
            request_id=request_id,
            complexity=response.complexity,
            confidence=response.confidence,
            duration=duration
        )
        
        return response
        
    except ValueError as e:
        API_REQUESTS.labels(endpoint="analyze", method="POST", status="validation_error").inc()
        logger.warning("Validation error", request_id=request_id, error=str(e))
        raise HTTPException(status_code=422, detail=str(e))
        
    except Exception as e:
        API_REQUESTS.labels(endpoint="analyze", method="POST", status="error").inc()
        logger.error("Analysis failed", request_id=request_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="AnalysisError",
                message="Query analysis failed",
                details={"error": str(e)},
                request_id=request_id
            ).dict()
        )


@router.get("/status", response_model=StatusResponse)
async def get_analyzer_status(
    request: StatusRequest = Depends(),
    analyzer: QueryAnalyzerService = Depends(get_analyzer_service)
) -> StatusResponse:
    """
    Get the current status of the query analyzer.
    
    Returns information about:
    - Analyzer initialization status
    - Component health
    - Performance metrics (if requested)
    - Configuration details (if requested)
    """
    try:
        logger.info("Getting analyzer status")
        
        status_data = await analyzer.get_analyzer_status()
        
        # Filter response based on request parameters
        if not request.include_performance:
            status_data.pop("performance", None)
            
        if not request.include_config:
            status_data.pop("configuration", None)
        
        response = StatusResponse(**status_data)
        
        API_REQUESTS.labels(endpoint="status", method="GET", status="success").inc()
        
        return response
        
    except Exception as e:
        API_REQUESTS.labels(endpoint="status", method="GET", status="error").inc()
        logger.error("Failed to get analyzer status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/components")
async def get_component_info(
    analyzer: QueryAnalyzerService = Depends(get_analyzer_service)
) -> Dict[str, Any]:
    """
    Get detailed information about analyzer components.
    
    Returns information about:
    - Feature Extractor status and configuration
    - Complexity Classifier thresholds and weights  
    - Model Recommender strategies and mappings
    - Component performance metrics
    """
    try:
        logger.info("Getting component information")
        
        status = await analyzer.get_analyzer_status()
        
        # Extract component-specific information
        components_info = {
            "service_info": {
                "name": "query-analyzer",
                "version": "1.0.0",
                "analyzer_type": status.get("analyzer_type", "Epic1QueryAnalyzer"),
                "initialized": status.get("initialized", False)
            },
            "components": {
                "feature_extractor": {
                    "status": status.get("components", {}).get("feature_extractor", "unknown"),
                    "description": "Extracts linguistic, structural, and semantic features from queries",
                    "capabilities": [
                        "Linguistic analysis (syntax, vocabulary)",
                        "Structural analysis (length, complexity)", 
                        "Semantic analysis (embeddings, topics)",
                        "Feature caching for performance"
                    ]
                },
                "complexity_classifier": {
                    "status": status.get("components", {}).get("complexity_classifier", "unknown"),
                    "description": "Classifies query complexity into simple/medium/complex levels",
                    "capabilities": [
                        "Multi-factor complexity scoring",
                        "Configurable thresholds",
                        "Confidence estimation",
                        "Real-time classification"
                    ]
                },
                "model_recommender": {
                    "status": status.get("components", {}).get("model_recommender", "unknown"),
                    "description": "Recommends optimal models based on complexity and strategy",
                    "capabilities": [
                        "Multi-model routing (Ollama, OpenAI, Mistral)",
                        "Cost-aware recommendations",
                        "Strategy-based selection (cost_optimized, balanced, quality_first)",
                        "Fallback chain management"
                    ]
                }
            },
            "performance": status.get("performance", {}),
            "configuration": status.get("configuration", {})
        }
        
        API_REQUESTS.labels(endpoint="components", method="GET", status="success").inc()
        
        return components_info
        
    except Exception as e:
        API_REQUESTS.labels(endpoint="components", method="GET", status="error").inc()
        logger.error("Failed to get component info", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-analyze")
async def batch_analyze_queries(
    queries: list[str],
    context: Dict[str, Any] = None,
    analyzer: QueryAnalyzerService = Depends(get_analyzer_service)
) -> Dict[str, Any]:
    """
    Analyze multiple queries in a single request.
    
    Returns analysis results for all queries with summary statistics.
    """
    if not queries:
        raise HTTPException(status_code=422, detail="At least one query is required")
    
    if len(queries) > 100:  # Reasonable limit
        raise HTTPException(status_code=422, detail="Maximum 100 queries per batch request")
    
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        logger.info(
            "Processing batch analyze request",
            request_id=request_id,
            query_count=len(queries)
        )
        
        results = []
        complexity_counts = {"simple": 0, "medium": 0, "complex": 0}
        
        for i, query in enumerate(queries):
            try:
                result = await analyzer.analyze_query(query=query, context=context)
                results.append({
                    "index": i,
                    "query": query,
                    "result": result
                })
                
                # Track complexity distribution
                complexity = result.get("complexity", "unknown")
                if complexity in complexity_counts:
                    complexity_counts[complexity] += 1
                    
            except Exception as e:
                results.append({
                    "index": i,
                    "query": query,
                    "error": str(e)
                })
        
        duration = time.time() - start_time
        
        response = {
            "request_id": request_id,
            "total_queries": len(queries),
            "successful_analyses": len([r for r in results if "result" in r]),
            "failed_analyses": len([r for r in results if "error" in r]),
            "processing_time": duration,
            "complexity_distribution": complexity_counts,
            "results": results
        }
        
        API_REQUESTS.labels(endpoint="batch-analyze", method="POST", status="success").inc()
        API_REQUEST_DURATION.labels(endpoint="batch-analyze").observe(duration)
        
        logger.info(
            "Batch analysis completed",
            request_id=request_id,
            successful=response["successful_analyses"],
            failed=response["failed_analyses"],
            duration=duration
        )
        
        return response
        
    except Exception as e:
        API_REQUESTS.labels(endpoint="batch-analyze", method="POST", status="error").inc()
        logger.error("Batch analysis failed", request_id=request_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))