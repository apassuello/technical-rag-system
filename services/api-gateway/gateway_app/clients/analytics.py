"""
Analytics service client.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import structlog

from .base import BaseServiceClient, ServiceError
from ..core.config import ServiceEndpoint

logger = structlog.get_logger(__name__)


class AnalyticsClient(BaseServiceClient):
    """Client for Analytics service."""
    
    def __init__(self, endpoint: ServiceEndpoint):
        super().__init__("analytics", endpoint)
    
    async def record_cache_hit(
        self,
        query_hash: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Record cache hit event.
        
        Args:
            query_hash: Hash of the cached query
            session_id: Optional session identifier
            user_id: Optional user identifier
            
        Returns:
            True if recorded successfully
        """
        try:
            self.logger.debug("Recording cache hit", query_hash=query_hash)
            
            request_data = {
                "event_type": "cache_hit",
                "query_hash": query_hash,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            if session_id:
                request_data["session_id"] = session_id
            
            if user_id:
                request_data["user_id"] = user_id
            
            response = await self.post("/record-event", json=request_data)
            
            return response.get("success", False)
            
        except Exception as e:
            self.logger.error("Failed to record cache hit", error=str(e))
            return False  # Don't fail requests on analytics errors
    
    async def record_query_completion(
        self,
        query_request: Dict[str, Any],
        query_response: Dict[str, Any]
    ) -> bool:
        """
        Record query completion event with full details.
        
        Args:
            query_request: Original query request
            query_response: Query response with metrics
            
        Returns:
            True if recorded successfully
        """
        try:
            self.logger.debug(
                "Recording query completion",
                query_id=query_response.get("query_id"),
                complexity=query_response.get("complexity"),
                cost=query_response.get("cost", {}).get("total_cost")
            )
            
            request_data = {
                "event_type": "query_completion",
                "query_data": {
                    "query": query_request.get("query"),
                    "query_id": query_response.get("query_id"),
                    "session_id": query_request.get("session_id"),
                    "user_id": query_request.get("user_id")
                },
                "response_data": {
                    "complexity": query_response.get("complexity"),
                    "confidence": query_response.get("confidence"),
                    "strategy_used": query_response.get("strategy_used"),
                    "fallback_used": query_response.get("fallback_used", False)
                },
                "performance_data": query_response.get("metrics", {}),
                "cost_data": query_response.get("cost", {}),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            response = await self.post("/record-query", json=request_data)
            
            return response.get("success", False)
            
        except Exception as e:
            self.logger.error("Failed to record query completion", error=str(e))
            return False  # Don't fail requests on analytics errors
    
    async def record_error(
        self,
        error_type: str,
        error_message: str,
        query: Optional[str] = None,
        service: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """
        Record error event.
        
        Args:
            error_type: Type of error
            error_message: Error message
            query: Optional query that caused error
            service: Optional service where error occurred
            session_id: Optional session identifier
            
        Returns:
            True if recorded successfully
        """
        try:
            self.logger.debug(
                "Recording error event",
                error_type=error_type,
                service=service
            )
            
            request_data = {
                "event_type": "error",
                "error_type": error_type,
                "error_message": error_message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            if query:
                request_data["query"] = query
            
            if service:
                request_data["service"] = service
            
            if session_id:
                request_data["session_id"] = session_id
            
            response = await self.post("/record-error", json=request_data)
            
            return response.get("success", False)
            
        except Exception as e:
            self.logger.error("Failed to record error event", error=str(e))
            return False
    
    async def get_cost_report(
        self,
        time_range: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get cost optimization report.
        
        Args:
            time_range: Time range for report (e.g., '24h', '7d', '30d')
            user_id: Optional user filter
            
        Returns:
            Cost analysis and optimization recommendations
        """
        try:
            params = {}
            if time_range:
                params["time_range"] = time_range
            if user_id:
                params["user_id"] = user_id
            
            response = await self.get("/cost-report", params=params)
            
            self.logger.info(
                "Retrieved cost report",
                time_range=time_range,
                total_cost=response.get("total_cost"),
                query_count=response.get("query_count")
            )
            
            return response
            
        except Exception as e:
            self.logger.error("Failed to get cost report", error=str(e))
            raise ServiceError(f"Failed to get cost report: {str(e)}", self.service_name)
    
    async def get_performance_report(
        self,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get performance analytics report.
        
        Args:
            time_range: Time range for report
            
        Returns:
            Performance metrics and trends
        """
        try:
            params = {}
            if time_range:
                params["time_range"] = time_range
            
            response = await self.get("/performance-report", params=params)
            
            self.logger.info(
                "Retrieved performance report",
                time_range=time_range,
                avg_response_time=response.get("avg_response_time"),
                total_queries=response.get("total_queries")
            )
            
            return response
            
        except Exception as e:
            self.logger.error("Failed to get performance report", error=str(e))
            raise ServiceError(f"Failed to get performance report: {str(e)}", self.service_name)
    
    async def get_usage_trends(
        self,
        time_range: Optional[str] = None,
        granularity: str = "hour"
    ) -> Dict[str, Any]:
        """
        Get usage pattern analysis.
        
        Args:
            time_range: Time range for analysis
            granularity: Data granularity (hour, day, week)
            
        Returns:
            Usage trends and patterns
        """
        try:
            params = {"granularity": granularity}
            if time_range:
                params["time_range"] = time_range
            
            response = await self.get("/usage-trends", params=params)
            
            self.logger.info(
                "Retrieved usage trends",
                time_range=time_range,
                granularity=granularity,
                data_points=len(response.get("trends", []))
            )
            
            return response
            
        except Exception as e:
            self.logger.error("Failed to get usage trends", error=str(e))
            raise ServiceError(f"Failed to get usage trends: {str(e)}", self.service_name)
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get analytics service status.
        
        Returns:
            Service status and metrics storage health
        """
        try:
            response = await self.get("/status")
            
            self.logger.debug(
                "Retrieved analytics status",
                status=response.get("status"),
                events_stored=response.get("events_stored")
            )
            
            return response
            
        except Exception as e:
            self.logger.error("Failed to get analytics status", error=str(e))
            raise ServiceError(f"Failed to get status: {str(e)}", self.service_name)