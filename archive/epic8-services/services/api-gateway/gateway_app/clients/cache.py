"""
Cache service client.
"""

from typing import Any, Dict, Optional

import structlog

from ..core.config import ServiceEndpoint
from .base import BaseServiceClient, ServiceError

logger = structlog.get_logger(__name__)


class CacheClient(BaseServiceClient):
    """Client for Cache service."""
    
    def __init__(self, endpoint: ServiceEndpoint):
        super().__init__("cache", endpoint)
    
    async def get_cached_response(self, query_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get cached response for query hash.
        
        Args:
            query_hash: Hash of the query for cache lookup
            
        Returns:
            Cached response if found, None otherwise
        """
        try:
            self.logger.debug("Looking up cached response", query_hash=query_hash)
            
            response = await self.get(f"/cache/{query_hash}")
            
            if response.get("found"):
                self.logger.info("Cache hit", query_hash=query_hash)
                return response.get("data")
            else:
                self.logger.debug("Cache miss", query_hash=query_hash)
                return None
                
        except ServiceError as e:
            if e.status_code == 404:
                self.logger.debug("Cache miss (404)", query_hash=query_hash)
                return None
            else:
                self.logger.error("Cache lookup failed", error=str(e), query_hash=query_hash)
                raise
        except Exception as e:
            self.logger.error("Cache lookup error", error=str(e), query_hash=query_hash)
            return None  # Return None on cache errors to allow fallback to processing
    
    async def cache_response(
        self,
        query_hash: str,
        response_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache response data.
        
        Args:
            query_hash: Hash of the query for cache key
            response_data: Response data to cache
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if cached successfully, False otherwise
        """
        try:
            self.logger.debug(
                "Caching response",
                query_hash=query_hash,
                data_size=len(str(response_data)),
                ttl=ttl
            )
            
            request_data = {
                "data": response_data
            }
            
            if ttl:
                request_data["ttl"] = ttl
            
            response = await self.post(f"/cache/{query_hash}", json=request_data)
            
            success = response.get("success", False)
            
            if success:
                self.logger.info("Response cached successfully", query_hash=query_hash)
            else:
                self.logger.warning("Failed to cache response", query_hash=query_hash)
            
            return success
            
        except Exception as e:
            self.logger.error("Cache storage failed", error=str(e), query_hash=query_hash)
            return False  # Return False on cache errors to continue processing
    
    async def invalidate_cache(self, query_hash: str) -> bool:
        """
        Invalidate cached response.
        
        Args:
            query_hash: Hash of the query to invalidate
            
        Returns:
            True if invalidated successfully, False otherwise
        """
        try:
            self.logger.debug("Invalidating cache", query_hash=query_hash)
            
            response = await self.delete(f"/cache/{query_hash}")
            
            success = response.get("success", False)
            
            if success:
                self.logger.info("Cache invalidated", query_hash=query_hash)
            else:
                self.logger.debug("Cache not found for invalidation", query_hash=query_hash)
            
            return success
            
        except Exception as e:
            self.logger.error("Cache invalidation failed", error=str(e), query_hash=query_hash)
            return False
    
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        
        Returns:
            Cache statistics including hit rate, size, etc.
        """
        try:
            response = await self.get("/statistics")
            
            self.logger.debug(
                "Retrieved cache statistics",
                hit_rate=response.get("hit_rate"),
                total_keys=response.get("total_keys"),
                memory_usage=response.get("memory_usage")
            )
            
            return response
            
        except Exception as e:
            self.logger.error("Failed to get cache statistics", error=str(e))
            raise ServiceError(f"Failed to get cache statistics: {str(e)}", self.service_name)
    
    async def clear_cache(self, pattern: Optional[str] = None) -> Dict[str, Any]:
        """
        Clear cache entries.
        
        Args:
            pattern: Optional pattern to match keys (if None, clears all)
            
        Returns:
            Clear operation results
        """
        try:
            self.logger.info("Clearing cache", pattern=pattern)
            
            request_data = {}
            if pattern:
                request_data["pattern"] = pattern
            
            response = await self.post("/clear", json=request_data)
            
            self.logger.info(
                "Cache cleared",
                keys_removed=response.get("keys_removed"),
                pattern=pattern
            )
            
            return response
            
        except Exception as e:
            self.logger.error("Cache clear failed", error=str(e))
            raise ServiceError(f"Cache clear failed: {str(e)}", self.service_name)
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get cache service status.
        
        Returns:
            Service status and cache health
        """
        try:
            response = await self.get("/status")
            
            self.logger.debug(
                "Retrieved cache status",
                status=response.get("status"),
                connected_clients=response.get("connected_clients")
            )
            
            return response
            
        except Exception as e:
            self.logger.error("Failed to get cache status", error=str(e))
            raise ServiceError(f"Failed to get status: {str(e)}", self.service_name)