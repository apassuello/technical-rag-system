"""
Response schemas for the retriever service.

This module defines Pydantic models for all API response payloads
with comprehensive structure and documentation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DocumentResult(BaseModel):
    """
    Single document retrieval result.
    
    This schema represents a document returned from
    the retrieval operation with relevance score.
    """
    content: str = Field(
        ...,
        description="Document content text",
        example="This is the main content of the retrieved document..."
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Document metadata",
        example={
            "title": "Introduction to Machine Learning",
            "author": "John Doe",
            "type": "pdf",
            "topic": "machine_learning",
            "page": 1
        }
    )
    
    doc_id: str = Field(
        ...,
        description="Unique document identifier",
        example="doc_123456"
    )
    
    source: str = Field(
        ...,
        description="Document source identifier",
        example="/path/to/document.pdf"
    )
    
    score: float = Field(
        ...,
        description="Relevance score (0.0 to 1.0)",
        ge=0.0,
        example=0.85
    )
    
    retrieval_method: str = Field(
        ...,
        description="Method used for retrieval",
        example="modular_unified_hybrid"
    )


class RetrievalResponse(BaseModel):
    """
    Document retrieval response.
    
    This schema represents the response for single
    document retrieval requests.
    """
    success: bool = Field(
        ...,
        description="Whether the retrieval was successful",
        example=True
    )
    
    query: str = Field(
        ...,
        description="Original search query",
        example="What is machine learning?"
    )
    
    documents: List[DocumentResult] = Field(
        default_factory=list,
        description="List of retrieved documents",
    )
    
    retrieval_info: Dict[str, Any] = Field(
        default_factory=dict,
        description="Information about the retrieval process",
        example={
            "strategy": "hybrid",
            "complexity": "medium",
            "k_requested": 10,
            "k_returned": 8,
            "processing_time": 0.125,
            "total_candidates": 1000
        }
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the response",
        example={
            "service_version": "1.0.0",
            "timestamp": "2025-08-22T10:30:00Z",
            "epic2_retriever": "ModularUnifiedRetriever"
        }
    )
    
    error: Optional[str] = Field(
        default=None,
        description="Error message if retrieval failed",
        example=None
    )


class BatchRetrievalResponse(BaseModel):
    """
    Batch document retrieval response.
    
    This schema represents the response for batch
    document retrieval requests.
    """
    success: bool = Field(
        ...,
        description="Whether the batch retrieval was successful",
        example=True
    )
    
    queries: List[str] = Field(
        ...,
        description="Original search queries",
        example=["What is machine learning?", "How do neural networks work?"]
    )
    
    results: List[List[DocumentResult]] = Field(
        default_factory=list,
        description="List of document lists, one for each query"
    )
    
    batch_info: Dict[str, Any] = Field(
        default_factory=dict,
        description="Information about the batch retrieval process",
        example={
            "total_queries": 2,
            "successful_queries": 2,
            "failed_queries": 0,
            "processing_time": 0.350,
            "strategy": "hybrid",
            "parallel_processing": True
        }
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the response",
        example={
            "service_version": "1.0.0",
            "timestamp": "2025-08-22T10:30:00Z",
            "batch_size": 2
        }
    )
    
    errors: List[Optional[str]] = Field(
        default_factory=list,
        description="Error messages for each query (None if successful)",
        example=[None, None]
    )


class IndexingResponse(BaseModel):
    """
    Document indexing response.
    
    This schema represents the response for document
    indexing operations.
    """
    success: bool = Field(
        ...,
        description="Whether the indexing was successful",
        example=True
    )
    
    indexed_documents: int = Field(
        ...,
        description="Number of documents successfully indexed",
        ge=0,
        example=25
    )
    
    total_documents: int = Field(
        ...,
        description="Total number of documents now in the index",
        ge=0,
        example=1025
    )
    
    processing_time: float = Field(
        ...,
        description="Time taken for indexing in seconds",
        ge=0.0,
        example=12.5
    )
    
    message: str = Field(
        ...,
        description="Human-readable status message",
        example="Successfully indexed 25 documents"
    )
    
    indexing_info: Dict[str, Any] = Field(
        default_factory=dict,
        description="Information about the indexing process",
        example={
            "batch_size": 25,
            "embeddings_generated": 25,
            "vector_index_updated": True,
            "sparse_index_updated": True,
            "duplicate_documents": 0
        }
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the response",
        example={
            "service_version": "1.0.0",
            "timestamp": "2025-08-22T10:30:00Z",
            "epic2_retriever": "ModularUnifiedRetriever"
        }
    )
    
    error: Optional[str] = Field(
        default=None,
        description="Error message if indexing failed",
        example=None
    )


class ReindexingResponse(BaseModel):
    """
    Document reindexing response.
    
    This schema represents the response for document
    reindexing operations.
    """
    success: bool = Field(
        ...,
        description="Whether the reindexing was successful",
        example=True
    )
    
    reindexed_documents: int = Field(
        ...,
        description="Number of documents reindexed",
        ge=0,
        example=1000
    )
    
    processing_time: float = Field(
        ...,
        description="Time taken for reindexing in seconds",
        ge=0.0,
        example=45.2
    )
    
    message: str = Field(
        ...,
        description="Human-readable status message",
        example="Successfully reindexed 1000 documents"
    )
    
    reindexing_info: Dict[str, Any] = Field(
        default_factory=dict,
        description="Information about the reindexing process",
        example={
            "vector_index_rebuilt": True,
            "sparse_index_rebuilt": True,
            "documents_verified": 1000,
            "corrupted_documents": 0,
            "embeddings_regenerated": 0
        }
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the response",
        example={
            "service_version": "1.0.0",
            "timestamp": "2025-08-22T10:30:00Z",
            "epic2_retriever": "ModularUnifiedRetriever"
        }
    )
    
    error: Optional[str] = Field(
        default=None,
        description="Error message if reindexing failed",
        example=None
    )


class ComponentStatus(BaseModel):
    """
    Individual component status information.
    """
    name: str = Field(..., description="Component name", example="vector_index")
    status: str = Field(..., description="Component status", example="healthy")
    details: Dict[str, Any] = Field(default_factory=dict, description="Component-specific details")


class RetrieverStatusResponse(BaseModel):
    """
    Retriever service status response.
    
    This schema represents comprehensive status information
    about the retriever service and its components.
    """
    success: bool = Field(
        ...,
        description="Whether the status request was successful",
        example=True
    )
    
    initialized: bool = Field(
        ...,
        description="Whether the service is initialized",
        example=True
    )
    
    status: str = Field(
        ...,
        description="Overall service status",
        example="healthy"
    )
    
    retriever_type: str = Field(
        ...,
        description="Type of retriever being used",
        example="ModularUnifiedRetriever"
    )
    
    configuration: Dict[str, Any] = Field(
        default_factory=dict,
        description="Current service configuration",
        example={
            "vector_index_type": "faiss",
            "sparse_type": "bm25",
            "fusion_type": "rrf",
            "reranker_type": "semantic"
        }
    )
    
    documents: Dict[str, Any] = Field(
        default_factory=dict,
        description="Document index information",
        example={
            "indexed_count": 1000,
            "index_status": "healthy"
        }
    )
    
    performance: Dict[str, Any] = Field(
        default_factory=dict,
        description="Performance statistics",
        example={
            "retrieval_stats": {
                "total_retrievals": 150,
                "avg_time": 0.125,
                "error_count": 2
            }
        }
    )
    
    components: List[ComponentStatus] = Field(
        default_factory=list,
        description="Status of individual components"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the response",
        example={
            "service_version": "1.0.0",
            "timestamp": "2025-08-22T10:30:00Z",
            "uptime": "2h 35m 12s"
        }
    )
    
    error: Optional[str] = Field(
        default=None,
        description="Error message if status check failed",
        example=None
    )


class HealthResponse(BaseModel):
    """
    Health check response.
    
    This schema represents the response for health check endpoints
    including both basic health status and detailed health information.
    """
    status: str = Field(
        ...,
        description="Health status",
        example="healthy"
    )
    
    service: str = Field(
        ...,
        description="Service name",
        example="retriever"
    )
    
    version: str = Field(
        ...,
        description="Service version",
        example="1.0.0"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Health check timestamp"
    )
    
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed health information",
        example={
            "retriever_initialized": True,
            "components_loaded": True,
            "documents_indexed": 1000,
            "last_retrieval": "2025-08-22T10:25:00Z"
        }
    )
    
    checks: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Individual health check results",
        example=[
            {"name": "database_connection", "status": "healthy", "response_time": "5ms"},
            {"name": "vector_index", "status": "healthy", "documents": 1000},
            {"name": "embedder", "status": "healthy", "model_loaded": True}
        ]
    )


class ErrorResponse(BaseModel):
    """
    Standard error response.
    
    This schema represents error responses for failed API requests.
    """
    success: bool = Field(
        default=False,
        description="Whether the request was successful",
        example=False
    )
    
    error: str = Field(
        ...,
        description="Error message",
        example="Invalid query parameter: k must be between 1 and 100"
    )
    
    error_code: Optional[str] = Field(
        default=None,
        description="Error code for programmatic handling",
        example="INVALID_PARAMETER"
    )
    
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details",
        example={"parameter": "k", "provided_value": 150, "max_allowed": 100}
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the error response",
        example={
            "service_version": "1.0.0",
            "timestamp": "2025-08-22T10:30:00Z",
            "request_id": "req_123456"
        }
    )