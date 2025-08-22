"""
Retriever service client.
"""

from typing import Dict, Any, List, Optional
import structlog

from .base import BaseServiceClient, ServiceError
from ..core.config import ServiceEndpoint

logger = structlog.get_logger(__name__)


class RetrieverClient(BaseServiceClient):
    """Client for Retriever service."""
    
    def __init__(self, endpoint: ServiceEndpoint):
        super().__init__("retriever", endpoint)
    
    async def retrieve_documents(
        self,
        query: str,
        max_documents: int = 10,
        complexity: Optional[str] = None,
        retrieval_strategy: str = "hybrid",
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for query.
        
        Args:
            query: Query string
            max_documents: Maximum number of documents to retrieve
            complexity: Query complexity level for optimization
            retrieval_strategy: Strategy to use (hybrid, dense, sparse)
            filters: Optional metadata filters
            
        Returns:
            List of retrieved documents with scores
        """
        try:
            self.logger.info(
                "Retrieving documents",
                query_length=len(query),
                max_documents=max_documents,
                complexity=complexity,
                strategy=retrieval_strategy
            )
            
            request_data = {
                "query": query,
                "max_documents": max_documents,
                "strategy": retrieval_strategy
            }
            
            if complexity:
                request_data["complexity"] = complexity
            
            if filters:
                request_data["filters"] = filters
            
            response = await self.post("/retrieve", json=request_data)
            
            documents = response.get("documents", [])
            
            self.logger.info(
                "Document retrieval completed",
                documents_retrieved=len(documents),
                processing_time=response.get("processing_time")
            )
            
            return documents
            
        except Exception as e:
            self.logger.error("Document retrieval failed", error=str(e))
            raise ServiceError(f"Document retrieval failed: {str(e)}", self.service_name)
    
    async def batch_retrieve(
        self,
        queries: List[str],
        max_documents: int = 10,
        strategy: str = "hybrid"
    ) -> Dict[str, Any]:
        """
        Retrieve documents for multiple queries in batch.
        
        Args:
            queries: List of query strings
            max_documents: Maximum documents per query
            strategy: Retrieval strategy
            
        Returns:
            Batch retrieval results
        """
        try:
            self.logger.info(
                "Batch retrieving documents",
                query_count=len(queries),
                max_documents=max_documents,
                strategy=strategy
            )
            
            request_data = {
                "queries": queries,
                "max_documents": max_documents,
                "strategy": strategy
            }
            
            response = await self.post("/batch-retrieve", json=request_data)
            
            self.logger.info(
                "Batch retrieval completed",
                total_queries=response.get("total_queries"),
                successful=response.get("successful_retrievals")
            )
            
            return response
            
        except Exception as e:
            self.logger.error("Batch retrieval failed", error=str(e))
            raise ServiceError(f"Batch retrieval failed: {str(e)}", self.service_name)
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get retriever service status.
        
        Returns:
            Service status and index statistics
        """
        try:
            response = await self.get("/status")
            
            self.logger.debug(
                "Retrieved retriever status",
                status=response.get("status"),
                index_size=response.get("index_size"),
                document_count=response.get("document_count")
            )
            
            return response
            
        except Exception as e:
            self.logger.error("Failed to get retriever status", error=str(e))
            raise ServiceError(f"Failed to get status: {str(e)}", self.service_name)
    
    async def reindex_documents(
        self,
        document_source: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Trigger document reindexing.
        
        Args:
            document_source: Optional specific document source to reindex
            
        Returns:
            Reindexing status and progress
        """
        try:
            self.logger.info("Triggering document reindexing", source=document_source)
            
            request_data = {}
            if document_source:
                request_data["source"] = document_source
            
            response = await self.post("/reindex", json=request_data)
            
            self.logger.info(
                "Reindexing triggered",
                job_id=response.get("job_id"),
                estimated_time=response.get("estimated_time")
            )
            
            return response
            
        except Exception as e:
            self.logger.error("Reindexing failed", error=str(e))
            raise ServiceError(f"Reindexing failed: {str(e)}", self.service_name)
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """
        Get detailed index statistics.
        
        Returns:
            Index statistics and health metrics
        """
        try:
            response = await self.get("/index/stats")
            
            self.logger.debug(
                "Retrieved index statistics",
                document_count=response.get("document_count"),
                index_size_mb=response.get("index_size_mb")
            )
            
            return response
            
        except Exception as e:
            self.logger.error("Failed to get index stats", error=str(e))
            raise ServiceError(f"Failed to get index stats: {str(e)}", self.service_name)