"""
Request schemas for the retriever service.

This module defines Pydantic models for all API request payloads
with comprehensive validation and documentation.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator


class RetrievalRequest(BaseModel):
    """
    Single document retrieval request.
    
    This schema defines the parameters for retrieving documents
    using the Epic 2 ModularUnifiedRetriever.
    """
    query: str = Field(
        ...,
        description="Search query string",
        min_length=1,
        max_length=1000,
        example="What is machine learning?"
    )
    
    k: int = Field(
        default=10,
        description="Number of documents to retrieve",
        ge=1,
        le=100,
        example=10
    )
    
    retrieval_strategy: str = Field(
        default="hybrid",
        description="Retrieval strategy to use",
        example="hybrid"
    )
    
    complexity: str = Field(
        default="medium",
        description="Query complexity level",
        example="medium"
    )
    
    max_documents: Optional[int] = Field(
        default=None,
        description="Maximum number of documents to consider (overrides k)",
        ge=1,
        le=1000,
        example=50
    )
    
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata filters to apply",
        example={"type": "pdf", "topic": "machine_learning"}
    )
    
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional retrieval options and parameters",
        example={"reranking_enabled": True, "fusion_weight": 0.7}
    )
    
    @validator('retrieval_strategy')
    def validate_retrieval_strategy(cls, v):
        """Validate retrieval strategy."""
        allowed_strategies = ["hybrid", "semantic", "keyword", "dense", "sparse"]
        if v not in allowed_strategies:
            raise ValueError(f"retrieval_strategy must be one of {allowed_strategies}")
        return v
    
    @validator('complexity')
    def validate_complexity(cls, v):
        """Validate complexity level."""
        allowed_complexities = ["simple", "medium", "complex", "auto"]
        if v not in allowed_complexities:
            raise ValueError(f"complexity must be one of {allowed_complexities}")
        return v
    
    @validator('max_documents')
    def validate_max_documents(cls, v, values):
        """Validate max_documents against k."""
        if v is not None and 'k' in values and v < values['k']:
            raise ValueError("max_documents must be greater than or equal to k")
        return v


class BatchRetrievalRequest(BaseModel):
    """
    Batch document retrieval request.
    
    This schema defines parameters for retrieving documents
    for multiple queries in a single request.
    """
    queries: List[str] = Field(
        ...,
        description="List of search query strings",
        min_items=1,
        max_items=100,
        example=["What is machine learning?", "How does neural networks work?"]
    )
    
    k: int = Field(
        default=10,
        description="Number of documents to retrieve per query",
        ge=1,
        le=100,
        example=10
    )
    
    retrieval_strategy: str = Field(
        default="hybrid",
        description="Retrieval strategy to use for all queries",
        example="hybrid"
    )
    
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional retrieval options applied to all queries",
        example={"reranking_enabled": True, "parallel_processing": True}
    )
    
    @validator('queries')
    def validate_queries(cls, v):
        """Validate query list."""
        # Check each query individually
        for i, query in enumerate(v):
            if not isinstance(query, str) or len(query.strip()) == 0:
                raise ValueError(f"Query at index {i} must be a non-empty string")
            if len(query) > 1000:
                raise ValueError(f"Query at index {i} exceeds maximum length of 1000 characters")
        return v
    
    @validator('retrieval_strategy')
    def validate_retrieval_strategy(cls, v):
        """Validate retrieval strategy."""
        allowed_strategies = ["hybrid", "semantic", "keyword", "dense", "sparse"]
        if v not in allowed_strategies:
            raise ValueError(f"retrieval_strategy must be one of {allowed_strategies}")
        return v


class DocumentData(BaseModel):
    """
    Document data for indexing.
    
    This schema defines the structure for documents
    to be indexed in the retriever.
    """
    content: str = Field(
        ...,
        description="Document content text",
        min_length=1,
        max_length=100000,  # 100KB max
        example="This is the main content of the document..."
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
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
    
    doc_id: Optional[str] = Field(
        default=None,
        description="Unique document identifier",
        max_length=255,
        example="doc_123456"
    )
    
    source: Optional[str] = Field(
        default=None,
        description="Document source identifier",
        max_length=500,
        example="/path/to/document.pdf"
    )
    
    embedding: Optional[List[float]] = Field(
        default=None,
        description="Pre-computed document embedding vector (optional)",
        example=None
    )
    
    @validator('content')
    def validate_content(cls, v):
        """Validate content field."""
        if not v.strip():
            raise ValueError("Document content cannot be empty")
        return v
    
    @validator('embedding')
    def validate_embedding(cls, v):
        """Validate embedding vector."""
        if v is not None:
            if len(v) == 0:
                raise ValueError("Embedding vector cannot be empty")
            if not all(isinstance(x, (int, float)) for x in v):
                raise ValueError("Embedding vector must contain only numbers")
        return v


class IndexDocumentsRequest(BaseModel):
    """
    Document indexing request.
    
    This schema defines parameters for indexing
    documents in the retriever.
    """
    documents: List[DocumentData] = Field(
        ...,
        description="List of documents to index",
        min_items=1,
        max_items=1000  # Limit batch size
    )
    
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Indexing options and parameters",
        example={
            "batch_size": 100,
            "generate_embeddings": True,
            "update_existing": False
        }
    )
    
    @validator('documents')
    def validate_documents(cls, v):
        """Validate document list."""
        if len(v) == 0:
            raise ValueError("Document list cannot be empty")
        
        # Check for duplicate doc_ids
        doc_ids = [doc.doc_id for doc in v if doc.doc_id is not None]
        if len(doc_ids) != len(set(doc_ids)):
            raise ValueError("Document IDs must be unique")
        
        return v


class ReindexRequest(BaseModel):
    """
    Document reindexing request.
    
    This schema defines parameters for triggering
    a complete reindexing of all documents.
    """
    force: bool = Field(
        default=False,
        description="Force reindexing even if index appears healthy",
        example=False
    )
    
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Reindexing options and parameters",
        example={
            "rebuild_vector_index": True,
            "rebuild_sparse_index": True,
            "verify_documents": True
        }
    )