"""
Generator service client.
"""

from typing import Any, Dict, List, Optional

import structlog

from ..core.config import ServiceEndpoint
from .base import BaseServiceClient, ServiceError

logger = structlog.get_logger(__name__)


class GeneratorClient(BaseServiceClient):
    """Client for Generator service."""
    
    def __init__(self, endpoint: ServiceEndpoint):
        super().__init__("generator", endpoint)
    
    async def generate_answer(
        self,
        query: str,
        context_documents: List[Dict[str, Any]],
        routing_decision: Optional[str] = None,
        complexity: Optional[str] = None,
        strategy: str = "balanced",
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate answer for query using context documents.
        
        Args:
            query: Original query string
            context_documents: Retrieved documents for context
            routing_decision: Recommended model from analyzer
            complexity: Query complexity level
            strategy: Generation strategy
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated answer with metadata
        """
        try:
            self.logger.info(
                "Generating answer",
                query_length=len(query),
                document_count=len(context_documents),
                routing_decision=routing_decision,
                complexity=complexity,
                strategy=strategy
            )
            
            request_data = {
                "query": query,
                "context_documents": context_documents,
                "options": {
                    "strategy": strategy,
                    "complexity": complexity
                }
            }
            
            if routing_decision:
                request_data["options"]["preferred_model"] = routing_decision
            
            if max_tokens:
                request_data["options"]["max_tokens"] = max_tokens
            
            response = await self.post("/generate", json=request_data)
            
            self.logger.info(
                "Answer generation completed",
                answer_length=len(response.get("answer", "")),
                model_used=response.get("model_used"),
                cost=response.get("cost"),
                processing_time=response.get("processing_time")
            )
            
            return response
            
        except Exception as e:
            self.logger.error("Answer generation failed", error=str(e))
            raise ServiceError(f"Answer generation failed: {str(e)}", self.service_name)
    
    async def get_available_models(self) -> Dict[str, Any]:
        """
        Get list of available models from generator service.
        
        Returns:
            Available models with capabilities and status
        """
        try:
            response = await self.get("/models")
            
            self.logger.debug(
                "Retrieved available models",
                model_count=len(response.get("models", [])),
                available_count=response.get("available_models", 0)
            )
            
            return response
            
        except Exception as e:
            self.logger.error("Failed to get available models", error=str(e))
            raise ServiceError(f"Failed to get models: {str(e)}", self.service_name)
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get generator service status.
        
        Returns:
            Service status and performance metrics
        """
        try:
            response = await self.get("/status")
            
            self.logger.debug(
                "Retrieved generator status",
                status=response.get("status"),
                models_available=response.get("models_available", 0)
            )
            
            return response
            
        except Exception as e:
            self.logger.error("Failed to get generator status", error=str(e))
            raise ServiceError(f"Failed to get status: {str(e)}", self.service_name)
    
    async def estimate_cost(
        self,
        query: str,
        context_length: int,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Estimate cost for generation request.
        
        Args:
            query: Query string
            context_length: Length of context in tokens
            model: Specific model to estimate for
            
        Returns:
            Cost estimation details
        """
        try:
            request_data = {
                "query": query,
                "context_length": context_length
            }
            
            if model:
                request_data["model"] = model
            
            response = await self.post("/estimate-cost", json=request_data)
            
            self.logger.debug(
                "Cost estimation completed",
                estimated_cost=response.get("estimated_cost"),
                model=response.get("model")
            )
            
            return response
            
        except Exception as e:
            self.logger.error("Cost estimation failed", error=str(e))
            raise ServiceError(f"Cost estimation failed: {str(e)}", self.service_name)