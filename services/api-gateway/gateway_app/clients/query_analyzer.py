"""
Query Analyzer service client.
"""

from typing import Any, Dict, List, Optional

import structlog

from ..core.config import ServiceEndpoint
from .base import BaseServiceClient, ServiceError

logger = structlog.get_logger(__name__)


class QueryAnalyzerClient(BaseServiceClient):
    """Client for Query Analyzer service."""
    
    def __init__(self, endpoint: ServiceEndpoint):
        super().__init__("query-analyzer", endpoint)
    
    async def analyze_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        complexity_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze query for complexity and model recommendations.
        
        Args:
            query: Query string to analyze
            context: Optional context information
            complexity_hint: Optional complexity hint
            
        Returns:
            Analysis result with complexity, confidence, recommended models, etc.
        """
        try:
            self.logger.info(
                "Analyzing query",
                query_length=len(query),
                has_context=context is not None,
                complexity_hint=complexity_hint
            )
            
            request_data = {
                "query": query,
                "context": context or {},
                "options": {}
            }
            
            if complexity_hint:
                request_data["options"]["complexity_hint"] = complexity_hint
            
            response = await self.post("/analyze", json=request_data)
            
            self.logger.info(
                "Query analysis completed",
                complexity=response.get("complexity"),
                confidence=response.get("confidence"),
                recommended_models=len(response.get("recommended_models", []))
            )
            
            return response
            
        except Exception as e:
            self.logger.error("Query analysis failed", error=str(e))
            raise ServiceError(f"Query analysis failed: {str(e)}", self.service_name)
    
    async def batch_analyze(
        self,
        queries: List[str],
        context: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze multiple queries in batch.
        
        Args:
            queries: List of query strings
            context: Optional shared context
            options: Optional analysis options
            
        Returns:
            Batch analysis results
        """
        try:
            self.logger.info(
                "Batch analyzing queries",
                query_count=len(queries),
                has_context=context is not None
            )
            
            request_data = {
                "queries": queries,
                "context": context or {},
                "options": options or {}
            }
            
            response = await self.post("/batch-analyze", json=request_data)
            
            self.logger.info(
                "Batch analysis completed",
                total_queries=response.get("total_queries"),
                successful=response.get("successful_analyses"),
                failed=response.get("failed_analyses")
            )
            
            return response
            
        except Exception as e:
            self.logger.error("Batch analysis failed", error=str(e))
            raise ServiceError(f"Batch analysis failed: {str(e)}", self.service_name)
    
    async def get_status(self, include_performance: bool = True) -> Dict[str, Any]:
        """
        Get analyzer service status.
        
        Args:
            include_performance: Whether to include performance metrics
            
        Returns:
            Service status information
        """
        try:
            params = {"include_performance": include_performance}
            response = await self.get("/status", params=params)
            
            self.logger.debug(
                "Retrieved analyzer status",
                status=response.get("status"),
                service_state=response.get("service_state")
            )
            
            return response
            
        except Exception as e:
            self.logger.error("Failed to get analyzer status", error=str(e))
            raise ServiceError(f"Failed to get status: {str(e)}", self.service_name)
    
    async def get_components(self) -> Dict[str, Any]:
        """
        Get analyzer component information.
        
        Returns:
            Component information and capabilities
        """
        try:
            response = await self.get("/components")
            
            self.logger.debug(
                "Retrieved component information",
                component_count=len(response.get("components", {}))
            )
            
            return response
            
        except Exception as e:
            self.logger.error("Failed to get component info", error=str(e))
            raise ServiceError(f"Failed to get components: {str(e)}", self.service_name)