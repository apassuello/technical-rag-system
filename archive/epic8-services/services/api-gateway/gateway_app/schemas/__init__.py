"""
Schemas package for API Gateway Service.
"""

from .requests import BatchQueryRequest, QueryOptions, UnifiedQueryRequest
from .responses import (
    AvailableModelsResponse,
    BatchQueryResponse,
    ErrorResponse,
    GatewayStatusResponse,
    ModelInfo,
    UnifiedQueryResponse,
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