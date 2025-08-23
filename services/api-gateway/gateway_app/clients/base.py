"""
Base service client with common functionality.
"""

import asyncio
import time
from typing import Dict, Any, Optional
import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..core.config import ServiceEndpoint

logger = structlog.get_logger(__name__)


class ServiceError(Exception):
    """Base exception for service errors."""
    
    def __init__(self, message: str, service: str, status_code: Optional[int] = None):
        self.message = message
        self.service = service
        self.status_code = status_code
        super().__init__(f"{service}: {message}")


class ServiceTimeoutError(ServiceError):
    """Exception for service timeout errors."""
    pass


class ServiceUnavailableError(ServiceError):
    """Exception for service unavailable errors."""
    pass


class BaseServiceClient:
    """Base class for service clients with common functionality."""
    
    def __init__(self, service_name: str, endpoint: ServiceEndpoint):
        self.service_name = service_name
        self.endpoint = endpoint
        self.logger = logger.bind(service=service_name)
        
        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            base_url=endpoint.url,
            timeout=httpx.Timeout(endpoint.timeout),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10)
        )
        
        # Metrics
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        self.last_request_time = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ServiceTimeoutError, ServiceUnavailableError))
    )
    async def _make_request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic and error handling."""
        start_time = time.time()
        self.request_count += 1
        
        try:
            self.logger.info(
                "Making request",
                method=method,
                path=path,
                request_count=self.request_count
            )
            
            response = await self.client.request(method, path, **kwargs)
            
            # Update metrics
            response_time = time.time() - start_time
            self.total_response_time += response_time
            self.last_request_time = time.time()
            
            # Handle response
            if response.status_code >= 400:
                self.error_count += 1
                
                if response.status_code == 408 or response.status_code == 504:
                    raise ServiceTimeoutError(
                        f"Request timeout: {response.status_code}",
                        self.service_name,
                        response.status_code
                    )
                elif response.status_code >= 500:
                    raise ServiceUnavailableError(
                        f"Service unavailable: {response.status_code}",
                        self.service_name,
                        response.status_code
                    )
                else:
                    error_detail = response.text
                    raise ServiceError(
                        f"Request failed: {response.status_code} - {error_detail}",
                        self.service_name,
                        response.status_code
                    )
            
            self.logger.info(
                "Request completed successfully",
                method=method,
                path=path,
                status_code=response.status_code,
                response_time=response_time
            )
            
            return response.json()
            
        except httpx.TimeoutException as e:
            self.error_count += 1
            self.logger.error("Request timeout", method=method, path=path, error=str(e))
            raise ServiceTimeoutError(
                f"Request timeout after {self.endpoint.timeout}s",
                self.service_name
            )
        except httpx.ConnectError as e:
            self.error_count += 1
            self.logger.error("Connection error", method=method, path=path, error=str(e))
            raise ServiceUnavailableError(
                f"Cannot connect to service: {str(e)}",
                self.service_name
            )
        except Exception as e:
            self.error_count += 1
            self.logger.error("Unexpected error", method=method, path=path, error=str(e))
            raise ServiceError(
                f"Unexpected error: {str(e)}",
                self.service_name
            )
    
    async def get(self, path: str, **kwargs) -> Dict[str, Any]:
        """Make GET request."""
        return await self._make_request("GET", path, **kwargs)
    
    async def post(self, path: str, **kwargs) -> Dict[str, Any]:
        """Make POST request."""
        return await self._make_request("POST", path, **kwargs)
    
    async def put(self, path: str, **kwargs) -> Dict[str, Any]:
        """Make PUT request."""
        return await self._make_request("PUT", path, **kwargs)
    
    async def delete(self, path: str, **kwargs) -> Dict[str, Any]:
        """Make DELETE request."""
        return await self._make_request("DELETE", path, **kwargs)
    
    async def health_check(self) -> bool:
        """Check service health."""
        try:
            response = await self.get("/health")
            return response.get("status") in ["healthy", "ready"]
        except Exception as e:
            self.logger.warning("Health check failed", error=str(e))
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics."""
        avg_response_time = (
            self.total_response_time / self.request_count 
            if self.request_count > 0 else 0.0
        )
        
        return {
            "service": self.service_name,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / self.request_count if self.request_count > 0 else 0.0,
            "average_response_time": avg_response_time,
            "last_request_time": self.last_request_time,
            "endpoint": self.endpoint.url
        }