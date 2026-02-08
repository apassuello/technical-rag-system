"""
REST API endpoints for Query Analyzer Service.
"""

import time
import uuid
from typing import Any, Dict

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from prometheus_client import Counter, Histogram

from ..core.analyzer import QueryAnalyzerService
from ..schemas.requests import AnalyzeRequest
from ..schemas.responses import AnalyzeResponse, ErrorResponse

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
            ).model_dump()
        )


@router.get("/status")
async def get_analyzer_status(
    include_performance: bool = True,
    include_config: bool = False,
    analyzer: QueryAnalyzerService = Depends(get_analyzer_service)
) -> Dict[str, Any]:
    """
    Epic 8 Enhanced status endpoint with comprehensive performance metrics.
    
    Query Parameters:
    - include_performance: Include performance metrics (default: true)
    - include_config: Include configuration details (default: false)
    
    Returns information about:
    - Service health and state
    - Performance metrics with SLA compliance
    - Circuit breaker status
    - Component health status
    - Epic 8 specific metrics
    """
    try:
        logger.info("Getting Epic 8 analyzer status", 
                   include_performance=include_performance,
                   include_config=include_config)
        
        # Get comprehensive status data
        status_data = await analyzer.get_analyzer_status()
        
        # Add Epic 8 specific status information
        current_time = time.time()
        
        # Get performance metrics
        performance_metrics = None
        if include_performance:
            try:
                performance_metrics = await analyzer.get_performance_metrics()
            except Exception as e:
                logger.warning("Could not get performance metrics", error=str(e))
                performance_metrics = {"error": "Performance metrics unavailable"}
        
        # Build Epic 8 compliant response
        epic8_status = {
            "service": "query-analyzer",
            "version": "1.0.0", 
            "status": status_data.get("status", "unknown"),
            "initialized": status_data.get("initialized", False),
            "uptime_seconds": status_data.get("uptime_seconds", 0),
            "analyzer_type": status_data.get("analyzer_type", "Epic1QueryAnalyzer"),
            "service_state": status_data.get("service_state", "unknown"),
            "components": status_data.get("components", {}),
            "last_health_check": current_time
        }
        
        # Add performance data if requested
        if include_performance and performance_metrics:
            epic8_status["performance"] = performance_metrics
        
        # Add configuration if requested
        if include_config:
            epic8_status["configuration"] = status_data.get("configuration", {})
        
        # Add circuit breaker information
        circuit_breaker_info = status_data.get("circuit_breaker", {})
        if circuit_breaker_info:
            epic8_status["circuit_breaker"] = circuit_breaker_info
        
        # Add Epic 8 specific health indicators
        epic8_status["health_indicators"] = {
            "circuit_breaker_healthy": circuit_breaker_info.get("state") == "closed",
            "performance_compliant": epic8_status.get("performance", {}).get("avg_response_time_ms", 0) <= 5000,
            "error_rate_healthy": epic8_status.get("performance", {}).get("error_rate", 0) <= 0.01,
            "fallback_available": status_data.get("configuration", {}).get("fallback_enabled", True)
        }
        
        API_REQUESTS.labels(endpoint="status", method="GET", status="success").inc()
        
        logger.info("Epic 8 status request completed successfully", 
                   service_state=epic8_status.get("service_state"),
                   performance_included=include_performance)
        
        return epic8_status
        
    except Exception as e:
        API_REQUESTS.labels(endpoint="status", method="GET", status="error").inc()
        logger.error("Failed to get Epic 8 analyzer status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Status request failed: {str(e)}")


@router.get("/components")
async def get_component_info(
    analyzer: QueryAnalyzerService = Depends(get_analyzer_service)
) -> Dict[str, Any]:
    """
    Epic 8 Enhanced component information with detailed health and configuration.
    
    Returns comprehensive information about:
    - Feature Extractor status, capabilities, and configuration
    - Complexity Classifier thresholds, weights, and performance metrics
    - Model Recommender strategies, mappings, and routing logic
    - Component-level performance and health indicators
    - Epic 8 compliance status
    """
    try:
        logger.info("Getting Epic 8 component information")
        
        status = await analyzer.get_analyzer_status()
        performance_metrics = await analyzer.get_performance_metrics()
        
        # Extract component-specific information with Epic 8 enhancements
        components_info = {
            "service_info": {
                "name": "query-analyzer",
                "version": "1.0.0",
                "analyzer_type": status.get("analyzer_type", "Epic1QueryAnalyzer"),
                "initialized": status.get("initialized", False),
                "service_state": status.get("service_state", "unknown"),
                "uptime_seconds": status.get("uptime_seconds", 0)
            },
            "components": {
                "feature_extractor": {
                    "status": status.get("components", {}).get("feature_extractor", "unknown"),
                    "description": "Extracts linguistic, structural, and semantic features from queries",
                    "capabilities": [
                        "Linguistic analysis (syntax, vocabulary, technical density)",
                        "Structural analysis (length, complexity, question types)", 
                        "Semantic analysis (embeddings, topics, technical terms)",
                        "Feature caching for performance optimization",
                        "Real-time feature extraction (<100ms target)"
                    ],
                    "configuration": status.get("configuration", {}).get("feature_extractor", {
                        "enable_caching": True,
                        "cache_size": 1000,
                        "extract_linguistic": True,
                        "extract_structural": True,
                        "extract_semantic": True
                    }),
                    "performance_targets": {
                        "extraction_time_ms": 100,
                        "cache_hit_rate": 0.8,
                        "feature_accuracy": 0.95
                    }
                },
                "complexity_classifier": {
                    "status": status.get("components", {}).get("complexity_classifier", "unknown"),
                    "description": "Classifies query complexity into simple/medium/complex levels with Epic 8 accuracy targets",
                    "capabilities": [
                        "Multi-factor complexity scoring (FR-8.1.2)",
                        "85% accuracy target compliance",
                        "Configurable thresholds and weights",
                        "Confidence estimation with uncertainty quantification",
                        "Real-time classification with fallback mechanisms"
                    ],
                    "configuration": status.get("configuration", {}).get("complexity_classifier", {
                        "thresholds": {
                            "simple": 0.3,
                            "medium": 0.6,
                            "complex": 0.9
                        },
                        "weights": {
                            "length": 0.2,
                            "vocabulary": 0.3,
                            "syntax": 0.2,
                            "semantic": 0.3
                        }
                    }),
                    "performance_targets": {
                        "classification_accuracy": 0.85,
                        "confidence_calibration": 0.9,
                        "classification_time_ms": 50
                    }
                },
                "model_recommender": {
                    "status": status.get("components", {}).get("model_recommender", "unknown"),
                    "description": "Recommends optimal models based on complexity and strategy with cost optimization (FR-8.1.4)",
                    "capabilities": [
                        "Multi-model routing (Ollama, OpenAI, Mistral, Anthropic)",
                        "Cost-aware recommendations with <5% error target",
                        "Strategy-based selection (cost_optimized, balanced, quality_first)",
                        "Fallback chain management (FR-8.1.5)",
                        "Dynamic model selection based on availability"
                    ],
                    "configuration": status.get("configuration", {}).get("model_recommender", {
                        "strategy": "balanced",
                        "model_mappings": {
                            "simple": ["ollama/llama3.2:3b"],
                            "medium": ["openai/gpt-3.5-turbo", "ollama/llama3.2:3b"],
                            "complex": ["openai/gpt-4", "mistral/mistral-large"]
                        },
                        "cost_weights": {
                            "ollama/llama3.2:3b": 0.0,
                            "openai/gpt-3.5-turbo": 0.002,
                            "openai/gpt-4": 0.06,
                            "mistral/mistral-large": 0.008
                        }
                    }),
                    "performance_targets": {
                        "recommendation_time_ms": 20,
                        "cost_estimation_error": 0.05,
                        "routing_accuracy": 0.9
                    }
                }
            },
            "epic8_compliance": {
                "functional_requirements": {
                    "FR_8_1_2": "Query complexity analysis with 85% accuracy target",
                    "FR_8_1_3": "Dynamic model selection based on complexity",
                    "FR_8_1_4": "Cost tracking with <5% estimation error",
                    "FR_8_1_5": "Fallback mechanisms for model failures"
                },
                "performance_compliance": {
                    "response_time_target": "5s maximum, 2s preferred",
                    "memory_usage": "<2GB per service instance",
                    "classification_accuracy": "85% target",
                    "cost_estimation_accuracy": "<5% error"
                },
                "current_performance": performance_metrics
            },
            "health_status": {
                "overall_health": status.get("status", "unknown"),
                "circuit_breaker": status.get("circuit_breaker", {}),
                "fallback_available": status.get("configuration", {}).get("fallback_enabled", True),
                "last_updated": time.time()
            }
        }
        
        API_REQUESTS.labels(endpoint="components", method="GET", status="success").inc()
        
        logger.info("Epic 8 component information request completed successfully",
                   component_count=len(components_info["components"]),
                   service_state=components_info["service_info"]["service_state"])
        
        return components_info
        
    except Exception as e:
        API_REQUESTS.labels(endpoint="components", method="GET", status="error").inc()
        logger.error("Failed to get Epic 8 component info", error=str(e))
        raise HTTPException(status_code=500, detail=f"Component info request failed: {str(e)}")


@router.post("/batch-analyze")
async def batch_analyze_queries(
    request: Dict[str, Any],  # Accept full request body per Epic 8 API spec
    analyzer: QueryAnalyzerService = Depends(get_analyzer_service)
) -> Dict[str, Any]:
    """
    Epic 8 Enhanced batch analyze multiple queries.
    
    Expected request format:
    {
      "queries": ["query1", "query2", ...],
      "context": {...},
      "options": {...}
    }
    
    Returns analysis results for all queries with summary statistics.
    """
    # Extract queries and parameters from request
    queries = request.get("queries", [])
    context = request.get("context", {})
    options = request.get("options", {})
    
    # Validation
    if not queries:
        raise HTTPException(status_code=422, detail="At least one query is required")
    
    if not isinstance(queries, list):
        raise HTTPException(status_code=422, detail="Queries must be a list")
    
    if len(queries) > 100:  # Reasonable limit for Epic 8
        raise HTTPException(status_code=422, detail="Maximum 100 queries per batch request")
    
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        logger.info(
            "Processing Epic 8 batch analyze request",
            request_id=request_id,
            query_count=len(queries),
            has_context=bool(context),
            options=options
        )
        
        results = []
        complexity_counts = {"simple": 0, "medium": 0, "complex": 0}
        total_cost = 0.0
        
        # Process each query
        for i, query in enumerate(queries):
            try:
                # Analyze with context
                result = await analyzer.analyze_query(query=query, context=context)
                
                results.append({
                    "index": i,
                    "query": query,
                    "result": {
                        "complexity": result.get("complexity"),
                        "confidence": result.get("confidence"),
                        "recommended_models": result.get("recommended_models"),
                        "cost_estimate": result.get("cost_estimate"),
                        "routing_strategy": result.get("routing_strategy"),
                        "processing_time": result.get("processing_time")
                    }
                })
                
                # Track statistics
                complexity = result.get("complexity", "unknown")
                if complexity in complexity_counts:
                    complexity_counts[complexity] += 1
                
                # Sum costs from all models for this query
                query_cost = sum(result.get("cost_estimate", {}).values())
                total_cost += query_cost
                    
            except Exception as e:
                results.append({
                    "index": i,
                    "query": query,
                    "error": str(e)
                })
                logger.warning(f"Query {i} failed", error=str(e), query=query[:50])
        
        duration = time.time() - start_time
        
        # Calculate summary statistics  
        successful_results = [r for r in results if "result" in r]
        failed_count = len([r for r in results if "error" in r])
        
        if successful_results:
            confidences = [r["result"]["confidence"] for r in successful_results]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            most_common_complexity = max(complexity_counts, key=complexity_counts.get) if any(complexity_counts.values()) else "unknown"
            
            # Determine recommended strategy based on distribution
            if complexity_counts["simple"] > complexity_counts["medium"] + complexity_counts["complex"]:
                recommended_strategy = "cost_optimized"
            elif complexity_counts["complex"] > complexity_counts["simple"] + complexity_counts["medium"]:
                recommended_strategy = "quality_first"
            else:
                recommended_strategy = "balanced"
            
            summary = {
                "average_confidence": round(avg_confidence, 3),
                "most_common_complexity": most_common_complexity,
                "recommended_strategy": recommended_strategy,
                "estimated_total_cost": round(total_cost, 4)
            }
        else:
            summary = {
                "average_confidence": 0.0,
                "most_common_complexity": "unknown",
                "recommended_strategy": "balanced",
                "estimated_total_cost": 0.0
            }
        
        # Epic 8 compliant response format
        response = {
            "request_id": request_id,
            "total_queries": len(queries),
            "successful_analyses": len(successful_results),
            "failed_analyses": failed_count,
            "processing_time": round(duration, 3),
            "complexity_distribution": complexity_counts,
            "summary": summary,
            "results": results
        }
        
        API_REQUESTS.labels(endpoint="batch-analyze", method="POST", status="success").inc()
        API_REQUEST_DURATION.labels(endpoint="batch-analyze").observe(duration)
        
        logger.info(
            "Epic 8 batch analysis completed successfully",
            request_id=request_id,
            successful=response["successful_analyses"],
            failed=response["failed_analyses"],
            duration=duration,
            total_cost=total_cost
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        API_REQUESTS.labels(endpoint="batch-analyze", method="POST", status="error").inc()
        logger.error("Epic 8 batch analysis failed", request_id=request_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")