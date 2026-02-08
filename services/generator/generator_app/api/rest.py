"""
REST API endpoints for Generator Service.
"""

import time
import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from prometheus_client import Counter, Histogram

from ..core.generator import GeneratorService
from ..schemas.requests import (
    BatchGenerateRequest,
    GenerateRequest,
    ModelStatusRequest,
    RoutingTestRequest,
)
from ..schemas.responses import (
    BatchGenerateResponse,
    ErrorResponse,
    GenerateResponse,
    GeneratorStatusResponse,
    ModelInfo,
    ModelsResponse,
    RoutingDecision,
    RoutingTestResponse,
)

logger = structlog.get_logger(__name__)

# Metrics
API_REQUESTS = Counter('generator_api_requests_total', 'API requests', ['endpoint', 'method', 'status'])
API_REQUEST_DURATION = Histogram('generator_api_request_duration_seconds', 'API request duration', ['endpoint'])

router = APIRouter()


async def get_generator_service() -> GeneratorService:
    """Dependency to get generator service from main app."""
    from ..main import get_generator_service
    return get_generator_service()


@router.post("/generate", response_model=GenerateResponse)
async def generate_answer(
    request: GenerateRequest,
    generator: GeneratorService = Depends(get_generator_service),
    http_request: Request = None
) -> GenerateResponse:
    """
    Generate an answer using multi-model routing.
    
    This endpoint processes a query with context documents and returns:
    - Generated answer using optimal model selection
    - Routing decision details
    - Cost information
    - Confidence scores
    - Performance metrics
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        logger.info(
            "Processing generate request",
            request_id=request_id,
            query_length=len(request.query),
            context_docs=len(request.context_documents),
            options=request.options
        )
        
        # Convert request to service format
        context_documents = []
        for doc in request.context_documents:
            context_documents.append({
                "content": doc.content,
                "metadata": doc.metadata,
                "doc_id": doc.doc_id,
                "source": doc.source,
                "score": doc.score
            })
        
        # Generate answer
        result = await generator.generate_answer(
            query=request.query,
            context_documents=context_documents,
            options=request.options
        )
        
        # Convert to response model
        routing_decision = RoutingDecision(
            strategy=result["routing_decision"]["strategy"],
            available_models=result["routing_decision"]["available_models"],
            selection_reason=result["routing_decision"]["selection_reason"],
            fallback_used=result["routing_decision"]["fallback_used"],
            cost_estimate=result["cost"]
        )
        
        response = GenerateResponse(
            answer=result["answer"],
            query=result["query"],
            model_used=result["model_used"],
            cost=result["cost"],
            confidence=result["confidence"],
            routing_decision=routing_decision,
            processing_time=result["processing_time"],
            metadata=result["metadata"]
        )
        
        # Update metrics
        duration = time.time() - start_time
        API_REQUESTS.labels(endpoint="generate", method="POST", status="success").inc()
        API_REQUEST_DURATION.labels(endpoint="generate").observe(duration)
        
        logger.info(
            "Answer generation completed",
            request_id=request_id,
            model=result["model_used"],
            cost=result["cost"],
            duration=duration
        )
        
        return response
        
    except ValueError as e:
        API_REQUESTS.labels(endpoint="generate", method="POST", status="validation_error").inc()
        logger.warning("Validation error", request_id=request_id, error=str(e))
        raise HTTPException(status_code=422, detail=str(e))
        
    except Exception as e:
        API_REQUESTS.labels(endpoint="generate", method="POST", status="error").inc()
        logger.error("Generation failed", request_id=request_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="GenerationError",
                message="Answer generation failed",
                details={"error": str(e)},
                request_id=request_id
            ).model_dump()
        )


@router.post("/batch-generate", response_model=BatchGenerateResponse)
async def batch_generate_answers(
    request: BatchGenerateRequest,
    generator: GeneratorService = Depends(get_generator_service)
) -> BatchGenerateResponse:
    """
    Generate answers for multiple requests in batch.
    
    Processes multiple generation requests efficiently with:
    - Parallel processing where possible
    - Cost optimization across the batch
    - Summary statistics and reporting
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        logger.info(
            "Processing batch generate request",
            request_id=request_id,
            batch_size=len(request.requests)
        )
        
        results = []
        total_cost = 0.0
        successful_generations = 0
        
        # Process each request in the batch
        for i, gen_request in enumerate(request.requests):
            try:
                # Convert to context documents format
                context_documents = []
                for doc in gen_request.context_documents:
                    context_documents.append({
                        "content": doc.content,
                        "metadata": doc.metadata,
                        "doc_id": doc.doc_id,
                        "source": doc.source,
                        "score": doc.score
                    })
                
                # Generate answer
                result = await generator.generate_answer(
                    query=gen_request.query,
                    context_documents=context_documents,
                    options=gen_request.options
                )
                
                results.append({
                    "index": i,
                    "success": True,
                    "result": result
                })
                
                total_cost += result["cost"]
                successful_generations += 1
                
            except Exception as e:
                results.append({
                    "index": i,
                    "success": False,
                    "error": str(e),
                    "query": gen_request.query
                })
        
        total_processing_time = time.time() - start_time
        
        # Create batch summary
        batch_summary = {
            "total_requests": len(request.requests),
            "successful_generations": successful_generations,
            "failed_generations": len(request.requests) - successful_generations,
            "success_rate": successful_generations / len(request.requests),
            "average_processing_time": total_processing_time / len(request.requests)
        }
        
        response = BatchGenerateResponse(
            results=results,
            batch_summary=batch_summary,
            total_cost=total_cost,
            total_processing_time=total_processing_time
        )
        
        # Update metrics
        API_REQUESTS.labels(endpoint="batch-generate", method="POST", status="success").inc()
        API_REQUEST_DURATION.labels(endpoint="batch-generate").observe(total_processing_time)
        
        logger.info(
            "Batch generation completed",
            request_id=request_id,
            successful=successful_generations,
            failed=len(request.requests) - successful_generations,
            total_cost=total_cost
        )
        
        return response
        
    except Exception as e:
        API_REQUESTS.labels(endpoint="batch-generate", method="POST", status="error").inc()
        logger.error("Batch generation failed", request_id=request_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", response_model=ModelsResponse)
async def get_available_models(
    request: ModelStatusRequest = Depends(),
    generator: GeneratorService = Depends(get_generator_service)
) -> ModelsResponse:
    """
    Get information about available models.
    
    Returns:
    - List of available models with capabilities
    - Cost information (if requested)
    - Health status for each model
    - Performance metrics (if requested)
    """
    try:
        logger.info("Getting available models")
        
        available_models = await generator.get_available_models()
        model_costs = await generator.get_model_costs() if request.include_costs else {}
        
        models = []
        healthy_count = 0
        cost_values = []
        
        for model_name in available_models:
            # Parse provider and model from name (e.g., "openai/gpt-3.5-turbo")
            if "/" in model_name:
                provider, model = model_name.split("/", 1)
            else:
                provider = "unknown"
                model = model_name
            
            cost_per_token = model_costs.get(model_name, None)
            if cost_per_token is not None:
                cost_values.append(cost_per_token)
            
            # Determine model capabilities based on provider and model name
            capabilities = []
            if "gpt-4" in model.lower():
                capabilities = ["text-generation", "reasoning", "analysis", "creative-writing"]
            elif "gpt-3.5" in model.lower():
                capabilities = ["text-generation", "conversation", "summarization"]
            elif "llama" in model.lower():
                capabilities = ["text-generation", "conversation", "local-inference"]
            elif "mistral" in model.lower():
                capabilities = ["text-generation", "reasoning", "multilingual"]
            else:
                capabilities = ["text-generation"]
            
            model_info = ModelInfo(
                name=model_name,
                provider=provider,
                available=True,  # If it's in available_models, it should be available
                cost_per_token=cost_per_token,
                max_tokens=None,  # Would need to extract from config
                capabilities=capabilities
            )
            
            models.append(model_info)
            healthy_count += 1
        
        # Calculate cost range
        cost_range = {}
        if cost_values:
            cost_range = {
                "min": min(cost_values),
                "max": max(cost_values),
                "average": sum(cost_values) / len(cost_values)
            }
        else:
            cost_range = {"min": 0.0, "max": 0.0, "average": 0.0}
        
        response = ModelsResponse(
            models=models,
            total_models=len(models),
            healthy_models=healthy_count,
            cost_range=cost_range
        )
        
        API_REQUESTS.labels(endpoint="models", method="GET", status="success").inc()
        
        return response
        
    except Exception as e:
        API_REQUESTS.labels(endpoint="models", method="GET", status="error").inc()
        logger.error("Failed to get models", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=GeneratorStatusResponse)
async def get_generator_status(
    generator: GeneratorService = Depends(get_generator_service)
) -> GeneratorStatusResponse:
    """
    Get the current status of the generator service.
    
    Returns comprehensive status information including:
    - Service initialization status
    - Available models and their health
    - Component status
    - Performance metrics
    - Configuration details
    """
    try:
        logger.info("Getting generator status")
        
        status_data = await generator.get_generator_status()
        
        response = GeneratorStatusResponse(**status_data)
        
        API_REQUESTS.labels(endpoint="status", method="GET", status="success").inc()
        
        return response
        
    except Exception as e:
        API_REQUESTS.labels(endpoint="status", method="GET", status="error").inc()
        logger.error("Failed to get generator status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-routing", response_model=RoutingTestResponse)
async def test_routing_decision(
    request: RoutingTestRequest,
    generator: GeneratorService = Depends(get_generator_service)
) -> RoutingTestResponse:
    """
    Test routing decision for a query without generating an answer.
    
    This endpoint helps understand which model would be selected
    for a given query and routing strategy without incurring generation costs.
    """
    try:
        logger.info(
            "Testing routing decision",
            query_length=len(request.query),
            strategy=request.strategy,
            max_cost=request.max_cost
        )
        
        # This would require extending the Epic1AnswerGenerator to support dry-run routing
        # For now, provide a mock response based on available models and costs
        available_models = await generator.get_available_models()
        model_costs = await generator.get_model_costs()
        
        # Simple routing logic for testing
        strategy = request.strategy or "balanced"
        max_cost = request.max_cost or 0.05
        
        # Filter models by cost constraint
        eligible_models = []
        for model in available_models:
            cost = model_costs.get(model, 0.0)
            if cost <= max_cost:
                eligible_models.append({"model": model, "cost": cost})
        
        if not eligible_models:
            recommended_model = available_models[0] if available_models else "none"
            cost_estimate = model_costs.get(recommended_model, 0.0)
            selection_reasoning = "No models within cost constraint, using fallback"
        else:
            # Sort by cost for cost_optimized, by quality for quality_first, balanced for balanced
            if strategy == "cost_optimized":
                eligible_models.sort(key=lambda x: x["cost"])
                recommended_model = eligible_models[0]["model"]
                cost_estimate = eligible_models[0]["cost"]
                selection_reasoning = "Selected lowest-cost model within constraints"
            elif strategy == "quality_first":
                # Assume higher cost = higher quality (simplified)
                eligible_models.sort(key=lambda x: x["cost"], reverse=True)
                recommended_model = eligible_models[0]["model"]
                cost_estimate = eligible_models[0]["cost"]
                selection_reasoning = "Selected highest-quality model within constraints"
            else:  # balanced
                # Select middle option or best balance
                eligible_models.sort(key=lambda x: x["cost"])
                mid_index = len(eligible_models) // 2
                recommended_model = eligible_models[mid_index]["model"]
                cost_estimate = eligible_models[mid_index]["cost"]
                selection_reasoning = "Selected balanced option considering cost and quality"
        
        response = RoutingTestResponse(
            query=request.query,
            recommended_model=recommended_model,
            strategy_used=strategy,
            cost_estimate=cost_estimate,
            selection_reasoning=selection_reasoning,
            alternative_models=[
                {"model": item["model"], "cost": item["cost"], "rank": i+1}
                for i, item in enumerate(eligible_models[:5])  # Top 5 alternatives
            ]
        )
        
        API_REQUESTS.labels(endpoint="test-routing", method="POST", status="success").inc()
        
        return response
        
    except Exception as e:
        API_REQUESTS.labels(endpoint="test-routing", method="POST", status="error").inc()
        logger.error("Routing test failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))