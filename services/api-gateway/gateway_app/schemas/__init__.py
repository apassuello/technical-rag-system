"""
Schemas package for API Gateway Service.
"""

from .requests import (
    UnifiedQueryRequest,
    BatchQueryRequest,
    QueryOptions
)

from .responses import (
    UnifiedQueryResponse,
    BatchQueryResponse,
    GatewayStatusResponse,
    ModelInfo,
    AvailableModelsResponse,
    ErrorResponse
)

__all__ = [
    # Requests
    "UnifiedQueryRequest",
    "BatchQueryRequest", 
    "QueryOptions",
    
    # Responses
    "UnifiedQueryResponse",
    "BatchQueryResponse",
    "GatewayStatusResponse",
    "ModelInfo",
    "AvailableModelsResponse",
    "ErrorResponse"
]