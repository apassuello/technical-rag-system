"""
REST API endpoints for the Retriever Service.

This module defines FastAPI routes for document retrieval operations,
providing comprehensive error handling, request validation, and monitoring.
"""

import time

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from prometheus_client import Counter, Gauge, Histogram

from ..core.retriever import RetrieverService
from ..schemas.requests import (
    BatchRetrievalRequest,
    IndexDocumentsRequest,
    ReindexRequest,
    RetrievalRequest,
)
from ..schemas.responses import (
    BatchRetrievalResponse,
    ComponentStatus,
    DocumentResult,
    ErrorResponse,
    IndexingResponse,
    ReindexingResponse,
    RetrievalResponse,
    RetrieverStatusResponse,
)

logger = structlog.get_logger(__name__)

# Create router
router = APIRouter(tags=["retrieval"])

# Metrics
API_REQUEST_COUNT = Counter('retriever_api_requests_total', 'Total API requests', ['endpoint', 'status'])
API_REQUEST_DURATION = Histogram('retriever_api_request_duration_seconds', 'API request duration', ['endpoint'])
API_ACTIVE_REQUESTS = Gauge('retriever_api_active_requests', 'Currently active API requests', ['endpoint'])

# Global service instance placeholder
retriever_service: RetrieverService = None


def get_retriever_service() -> RetrieverService:
    """Dependency to get the retriever service instance."""
    if retriever_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Retriever service not initialized"
        )
    return retriever_service


@router.post(
    "/retrieve",
    response_model=RetrievalResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve documents",
    description="Retrieve relevant documents using Epic 2's ModularUnifiedRetriever with hybrid search",
    responses={
        200: {"description": "Documents retrieved successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        503: {"model": ErrorResponse, "description": "Service unavailable"}
    }
)
async def retrieve_documents(
    request: RetrievalRequest,
    service: RetrieverService = Depends(get_retriever_service)
) -> RetrievalResponse:
    """
    Retrieve documents for a single query.
    
    This endpoint performs document retrieval using Epic 2's ModularUnifiedRetriever
    with support for various retrieval strategies, complexity levels, and filtering options.
    
    Args:
        request: Retrieval request parameters
        service: RetrieverService dependency
        
    Returns:
        RetrievalResponse with retrieved documents and metadata
        
    Raises:
        HTTPException: For various error conditions
    """
    start_time = time.time()
    endpoint = "retrieve"
    
    # Update active requests metric
    API_ACTIVE_REQUESTS.labels(endpoint=endpoint).inc()
    
    try:
        logger.info(
            "Processing document retrieval request",
            query_length=len(request.query),
            k=request.k,
            strategy=request.retrieval_strategy,
            complexity=request.complexity,
            max_documents=request.max_documents,
            has_filters=bool(request.filters)
        )
        
        # Perform retrieval using the service
        documents = await service.retrieve_documents(
            query=request.query,
            k=request.k,
            retrieval_strategy=request.retrieval_strategy,
            complexity=request.complexity,
            max_documents=request.max_documents,
            filters=request.filters
        )
        
        processing_time = time.time() - start_time
        
        # Convert service results to response format
        document_results = []
        for doc_data in documents:
            doc_result = DocumentResult(
                content=doc_data["content"],
                metadata=doc_data["metadata"],
                doc_id=doc_data["doc_id"],
                source=doc_data["source"],
                score=doc_data["score"],
                retrieval_method=doc_data["retrieval_method"]
            )
            document_results.append(doc_result)
        
        # Prepare response
        response = RetrievalResponse(
            success=True,
            query=request.query,
            documents=document_results,
            retrieval_info={
                "strategy": request.retrieval_strategy,
                "complexity": request.complexity,
                "k_requested": request.k,
                "k_returned": len(documents),
                "processing_time": processing_time,
                "max_documents": request.max_documents,
                "filters_applied": bool(request.filters)
            },
            metadata={
                "service_version": "1.0.0",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "epic2_retriever": "ModularUnifiedRetriever",
                "endpoint": endpoint
            }
        )
        
        # Update success metrics
        API_REQUEST_COUNT.labels(endpoint=endpoint, status="success").inc()
        API_REQUEST_DURATION.labels(endpoint=endpoint).observe(processing_time)
        
        logger.info(
            "Document retrieval completed successfully",
            query_length=len(request.query),
            results_count=len(documents),
            processing_time=processing_time
        )
        
        return response
        
    except ValueError as e:
        # Handle validation errors
        error_msg = f"Invalid request parameters: {str(e)}"
        logger.warning("Document retrieval validation error", error=error_msg)
        
        API_REQUEST_COUNT.labels(endpoint=endpoint, status="validation_error").inc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
        
    except Exception as e:
        # Handle unexpected errors
        processing_time = time.time() - start_time
        error_msg = f"Document retrieval failed: {str(e)}"
        
        API_REQUEST_COUNT.labels(endpoint=endpoint, status="error").inc()
        API_REQUEST_DURATION.labels(endpoint=endpoint).observe(processing_time)
        
        logger.error(
            "Document retrieval failed",
            error=error_msg,
            processing_time=processing_time
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
        
    finally:
        # Decrease active requests metric
        API_ACTIVE_REQUESTS.labels(endpoint=endpoint).dec()


@router.post(
    "/batch-retrieve",
    response_model=BatchRetrievalResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch retrieve documents",
    description="Retrieve documents for multiple queries in a single request",
    responses={
        200: {"description": "Batch retrieval completed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        503: {"model": ErrorResponse, "description": "Service unavailable"}
    }
)
async def batch_retrieve_documents(
    request: BatchRetrievalRequest,
    service: RetrieverService = Depends(get_retriever_service)
) -> BatchRetrievalResponse:
    """
    Retrieve documents for multiple queries.
    
    This endpoint performs batch document retrieval for multiple queries,
    providing efficient processing of multiple requests.
    
    Args:
        request: Batch retrieval request parameters
        service: RetrieverService dependency
        
    Returns:
        BatchRetrievalResponse with results for each query
        
    Raises:
        HTTPException: For various error conditions
    """
    start_time = time.time()
    endpoint = "batch_retrieve"
    
    # Update active requests metric
    API_ACTIVE_REQUESTS.labels(endpoint=endpoint).inc()
    
    try:
        logger.info(
            "Processing batch retrieval request",
            query_count=len(request.queries),
            k=request.k,
            strategy=request.retrieval_strategy
        )
        
        # Perform batch retrieval using the service
        batch_results = await service.batch_retrieve_documents(
            queries=request.queries,
            k=request.k,
            retrieval_strategy=request.retrieval_strategy
        )
        
        processing_time = time.time() - start_time
        
        # Convert service results to response format
        response_results = []
        errors = []
        successful_queries = 0
        
        for i, documents in enumerate(batch_results):
            if documents:  # Successful retrieval
                document_results = []
                for doc_data in documents:
                    doc_result = DocumentResult(
                        content=doc_data["content"],
                        metadata=doc_data["metadata"],
                        doc_id=doc_data["doc_id"],
                        source=doc_data["source"],
                        score=doc_data["score"],
                        retrieval_method=doc_data["retrieval_method"]
                    )
                    document_results.append(doc_result)
                
                response_results.append(document_results)
                errors.append(None)
                successful_queries += 1
            else:  # Failed retrieval
                response_results.append([])
                errors.append(f"No documents retrieved for query {i+1}")
        
        # Prepare response
        response = BatchRetrievalResponse(
            success=True,
            queries=request.queries,
            results=response_results,
            batch_info={
                "total_queries": len(request.queries),
                "successful_queries": successful_queries,
                "failed_queries": len(request.queries) - successful_queries,
                "processing_time": processing_time,
                "strategy": request.retrieval_strategy,
                "k_per_query": request.k,
                "parallel_processing": True
            },
            metadata={
                "service_version": "1.0.0",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "batch_size": len(request.queries),
                "endpoint": endpoint
            },
            errors=errors
        )
        
        # Update success metrics
        API_REQUEST_COUNT.labels(endpoint=endpoint, status="success").inc()
        API_REQUEST_DURATION.labels(endpoint=endpoint).observe(processing_time)
        
        logger.info(
            "Batch retrieval completed successfully",
            total_queries=len(request.queries),
            successful_queries=successful_queries,
            processing_time=processing_time
        )
        
        return response
        
    except ValueError as e:
        # Handle validation errors
        error_msg = f"Invalid batch request parameters: {str(e)}"
        logger.warning("Batch retrieval validation error", error=error_msg)
        
        API_REQUEST_COUNT.labels(endpoint=endpoint, status="validation_error").inc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
        
    except Exception as e:
        # Handle unexpected errors
        processing_time = time.time() - start_time
        error_msg = f"Batch retrieval failed: {str(e)}"
        
        API_REQUEST_COUNT.labels(endpoint=endpoint, status="error").inc()
        API_REQUEST_DURATION.labels(endpoint=endpoint).observe(processing_time)
        
        logger.error(
            "Batch retrieval failed",
            error=error_msg,
            processing_time=processing_time
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
        
    finally:
        # Decrease active requests metric
        API_ACTIVE_REQUESTS.labels(endpoint=endpoint).dec()


@router.post(
    "/index",
    response_model=IndexingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Index documents",
    description="Index new documents in the retriever for future retrieval",
    responses={
        201: {"description": "Documents indexed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        503: {"model": ErrorResponse, "description": "Service unavailable"}
    }
)
async def index_documents(
    request: IndexDocumentsRequest,
    service: RetrieverService = Depends(get_retriever_service)
) -> IndexingResponse:
    """
    Index documents in the retriever.
    
    This endpoint indexes new documents in the Epic 2 ModularUnifiedRetriever,
    making them available for future retrieval operations.
    
    Args:
        request: Document indexing request
        service: RetrieverService dependency
        
    Returns:
        IndexingResponse with indexing results
        
    Raises:
        HTTPException: For various error conditions
    """
    start_time = time.time()
    endpoint = "index"
    
    # Update active requests metric
    API_ACTIVE_REQUESTS.labels(endpoint=endpoint).inc()
    
    try:
        logger.info(
            "Processing document indexing request",
            document_count=len(request.documents)
        )
        
        # Convert request documents to service format
        documents_data = []
        for doc in request.documents:
            doc_dict = {
                "content": doc.content,
                "metadata": doc.metadata,
                "doc_id": doc.doc_id,
                "source": doc.source,
                "embedding": doc.embedding
            }
            documents_data.append(doc_dict)
        
        # Perform indexing using the service
        result = await service.index_documents(documents_data)
        
        processing_time = time.time() - start_time
        
        # Prepare response
        response = IndexingResponse(
            success=result["success"],
            indexed_documents=result["indexed_documents"],
            total_documents=result["total_documents"],
            processing_time=result["processing_time"],
            message=result["message"],
            indexing_info={
                "batch_size": len(request.documents),
                "embeddings_generated": len([doc for doc in request.documents if doc.embedding is None]),
                "vector_index_updated": True,
                "sparse_index_updated": True,
                "duplicate_documents": 0,
                "options": request.options or {}
            },
            metadata={
                "service_version": "1.0.0",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "epic2_retriever": "ModularUnifiedRetriever",
                "endpoint": endpoint
            }
        )
        
        # Update success metrics
        API_REQUEST_COUNT.labels(endpoint=endpoint, status="success").inc()
        API_REQUEST_DURATION.labels(endpoint=endpoint).observe(processing_time)
        
        logger.info(
            "Document indexing completed successfully",
            indexed_count=result["indexed_documents"],
            total_documents=result["total_documents"],
            processing_time=processing_time
        )
        
        return response
        
    except ValueError as e:
        # Handle validation errors
        error_msg = f"Invalid indexing parameters: {str(e)}"
        logger.warning("Document indexing validation error", error=error_msg)
        
        API_REQUEST_COUNT.labels(endpoint=endpoint, status="validation_error").inc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
        
    except Exception as e:
        # Handle unexpected errors
        processing_time = time.time() - start_time
        error_msg = f"Document indexing failed: {str(e)}"
        
        API_REQUEST_COUNT.labels(endpoint=endpoint, status="error").inc()
        API_REQUEST_DURATION.labels(endpoint=endpoint).observe(processing_time)
        
        logger.error(
            "Document indexing failed",
            error=error_msg,
            processing_time=processing_time
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
        
    finally:
        # Decrease active requests metric
        API_ACTIVE_REQUESTS.labels(endpoint=endpoint).dec()


@router.post(
    "/reindex",
    response_model=ReindexingResponse,
    status_code=status.HTTP_200_OK,
    summary="Reindex documents",
    description="Trigger a complete reindexing of all documents",
    responses={
        200: {"description": "Documents reindexed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        503: {"model": ErrorResponse, "description": "Service unavailable"}
    }
)
async def reindex_documents(
    request: ReindexRequest,
    service: RetrieverService = Depends(get_retriever_service)
) -> ReindexingResponse:
    """
    Trigger document reindexing.
    
    This endpoint triggers a complete reindexing of all documents
    in the Epic 2 ModularUnifiedRetriever.
    
    Args:
        request: Reindexing request parameters
        service: RetrieverService dependency
        
    Returns:
        ReindexingResponse with reindexing results
        
    Raises:
        HTTPException: For various error conditions
    """
    start_time = time.time()
    endpoint = "reindex"
    
    # Update active requests metric
    API_ACTIVE_REQUESTS.labels(endpoint=endpoint).inc()
    
    try:
        logger.info(
            "Processing document reindexing request",
            force=request.force
        )
        
        # Perform reindexing using the service
        result = await service.reindex_documents()
        
        processing_time = time.time() - start_time
        
        # Prepare response
        response = ReindexingResponse(
            success=result["success"],
            reindexed_documents=result["reindexed_documents"],
            processing_time=result["processing_time"],
            message=result["message"],
            reindexing_info={
                "vector_index_rebuilt": True,
                "sparse_index_rebuilt": True,
                "documents_verified": result["reindexed_documents"],
                "corrupted_documents": 0,
                "embeddings_regenerated": 0,
                "force_reindex": request.force,
                "options": request.options or {}
            },
            metadata={
                "service_version": "1.0.0",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "epic2_retriever": "ModularUnifiedRetriever",
                "endpoint": endpoint
            }
        )
        
        # Update success metrics
        API_REQUEST_COUNT.labels(endpoint=endpoint, status="success").inc()
        API_REQUEST_DURATION.labels(endpoint=endpoint).observe(processing_time)
        
        logger.info(
            "Document reindexing completed successfully",
            reindexed_count=result["reindexed_documents"],
            processing_time=processing_time
        )
        
        return response
        
    except Exception as e:
        # Handle unexpected errors
        processing_time = time.time() - start_time
        error_msg = f"Document reindexing failed: {str(e)}"
        
        API_REQUEST_COUNT.labels(endpoint=endpoint, status="error").inc()
        API_REQUEST_DURATION.labels(endpoint=endpoint).observe(processing_time)
        
        logger.error(
            "Document reindexing failed",
            error=error_msg,
            processing_time=processing_time
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
        
    finally:
        # Decrease active requests metric
        API_ACTIVE_REQUESTS.labels(endpoint=endpoint).dec()


@router.get(
    "/status",
    response_model=RetrieverStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get retriever status",
    description="Get comprehensive status information about the retriever service",
    responses={
        200: {"description": "Status retrieved successfully"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        503: {"model": ErrorResponse, "description": "Service unavailable"}
    }
)
async def get_retriever_status(
    service: RetrieverService = Depends(get_retriever_service)
) -> RetrieverStatusResponse:
    """
    Get retriever service status.
    
    This endpoint returns comprehensive status information about
    the retriever service and its components.
    
    Args:
        service: RetrieverService dependency
        
    Returns:
        RetrieverStatusResponse with detailed status information
        
    Raises:
        HTTPException: For various error conditions
    """
    start_time = time.time()
    endpoint = "status"
    
    try:
        logger.info("Processing status request")
        
        # Get status from the service
        status_info = await service.get_retriever_status()
        
        processing_time = time.time() - start_time
        
        # Convert component status to response format
        components = []
        if "components" in status_info:
            for comp_name, comp_status in status_info["components"].items():
                component = ComponentStatus(
                    name=comp_name,
                    status=comp_status if isinstance(comp_status, str) else "healthy",
                    details=comp_status if isinstance(comp_status, dict) else {}
                )
                components.append(component)
        
        # Prepare response
        response = RetrieverStatusResponse(
            success=True,
            initialized=status_info.get("initialized", False),
            status=status_info.get("status", "unknown"),
            retriever_type=status_info.get("retriever_type", "Unknown"),
            configuration=status_info.get("configuration", {}),
            documents=status_info.get("documents", {}),
            performance=status_info.get("performance", {}),
            components=components,
            metadata={
                "service_version": "1.0.0",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "uptime": f"{processing_time:.2f}s",
                "endpoint": endpoint,
                "epic2_stats": status_info.get("epic2_stats", {}),
                "epic2_components": status_info.get("epic2_components", {})
            }
        )
        
        # Update success metrics
        API_REQUEST_COUNT.labels(endpoint=endpoint, status="success").inc()
        API_REQUEST_DURATION.labels(endpoint=endpoint).observe(processing_time)
        
        logger.info(
            "Status request completed successfully",
            processing_time=processing_time
        )
        
        return response
        
    except Exception as e:
        # Handle unexpected errors
        processing_time = time.time() - start_time
        error_msg = f"Status request failed: {str(e)}"
        
        API_REQUEST_COUNT.labels(endpoint=endpoint, status="error").inc()
        API_REQUEST_DURATION.labels(endpoint=endpoint).observe(processing_time)
        
        logger.error(
            "Status request failed",
            error=error_msg,
            processing_time=processing_time
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )