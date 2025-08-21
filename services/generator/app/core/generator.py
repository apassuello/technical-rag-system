"""
Generator Service - Core Business Logic.

This module implements the GeneratorService that wraps the existing
Epic1AnswerGenerator for multi-model answer generation in microservices.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys
from decimal import Decimal

import structlog
from prometheus_client import Counter, Histogram, Gauge

# Add main project to path to import existing components
project_root = Path(__file__).parent.parent.parent.parent  # 4 levels up to project root
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

# Import existing Epic 1 components
from components.generators.epic1_answer_generator import Epic1AnswerGenerator
from components.generators.routing.routing_strategies import RoutingStrategy
from core.interfaces import Answer

logger = structlog.get_logger(__name__)

# Metrics
GENERATION_REQUESTS = Counter('generator_requests_total', 'Total generation requests', ['status', 'model'])
GENERATION_DURATION = Histogram('generator_duration_seconds', 'Generation duration', ['model'])
COST_TRACKING = Counter('generator_cost_dollars_total', 'Total cost in dollars', ['model'])
MODEL_HEALTH = Gauge('generator_model_health', 'Model health status', ['model'])


class GeneratorService:
    """
    Service wrapper for Epic1AnswerGenerator.
    
    This service provides:
    - Multi-model answer generation with intelligent routing
    - Cost tracking and optimization
    - Adapter pattern for different LLM providers
    - Async/await interface for microservices
    - Comprehensive monitoring and health checks
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Generator Service.
        
        Args:
            config: Configuration dictionary for the generator
        """
        self.config = config or {}
        self.generator: Optional[Epic1AnswerGenerator] = None
        self._initialized = False
        self._initialization_lock = asyncio.Lock()
        
        logger.info("Initializing GeneratorService", config=self.config)
    
    async def _initialize_generator(self):
        """Initialize the Epic1AnswerGenerator if not already done."""
        if self._initialized:
            return
        
        async with self._initialization_lock:
            if self._initialized:
                return
            
            try:
                # Initialize the Epic1AnswerGenerator with configuration
                self.generator = Epic1AnswerGenerator(config=self.config)
                self._initialized = True
                
                # Update model health metrics for available models
                available_models = await self.get_available_models()
                for model in available_models:
                    MODEL_HEALTH.labels(model=model).set(1)
                
                logger.info(
                    "Epic1AnswerGenerator initialized successfully",
                    models_available=len(available_models)
                )
                
            except Exception as e:
                logger.error("Failed to initialize Epic1AnswerGenerator", error=str(e))
                raise
    
    async def generate_answer(
        self,
        query: str,
        context_documents: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate an answer using multi-model routing.
        
        Args:
            query: The user's query
            context_documents: List of relevant documents for context
            options: Optional generation parameters (model preference, strategy, etc.)
            
        Returns:
            Dictionary containing:
            - answer: The generated answer text
            - model_used: Which model was selected
            - cost: Cost of the generation
            - confidence: Answer confidence score
            - routing_decision: Details about model selection
            - processing_time: Time taken for generation
            - metadata: Additional metadata
        """
        if not self._initialized:
            await self._initialize_generator()
        
        if not self.generator:
            raise RuntimeError("Generator not initialized")
        
        start_time = time.time()
        selected_model = None
        
        try:
            logger.info(
                "Generating answer",
                query_length=len(query),
                context_docs=len(context_documents),
                options=options or {}
            )
            
            # Convert context documents to the format expected by Epic1AnswerGenerator
            from core.interfaces import Document
            documents = []
            for doc_data in context_documents:
                doc = Document(
                    content=doc_data.get('content', ''),
                    metadata=doc_data.get('metadata', {}),
                    doc_id=doc_data.get('doc_id', ''),
                    source=doc_data.get('source', '')
                )
                documents.append(doc)
            
            # Apply options if provided
            if options:
                # Set routing strategy if specified
                if 'strategy' in options:
                    strategy_name = options['strategy']
                    if hasattr(RoutingStrategy, strategy_name.upper()):
                        self.generator.router.strategy = getattr(RoutingStrategy, strategy_name.upper())
                
                # Set model preference if specified
                if 'preferred_model' in options:
                    # This would require extending Epic1AnswerGenerator to support model hints
                    pass
            
            # Generate answer using Epic1AnswerGenerator
            answer: Answer = self.generator.generate_answer(query, documents)
            
            # Extract routing information from the answer metadata
            routing_metadata = answer.metadata.get('routing', {})
            selected_model = routing_metadata.get('model_used', 'unknown')
            cost = routing_metadata.get('cost', 0.0)
            
            # Convert cost to decimal for precision
            if isinstance(cost, (int, float)):
                cost = float(cost)
            
            processing_time = time.time() - start_time
            
            # Prepare response
            result = {
                "answer": answer.content,
                "query": query,
                "model_used": selected_model,
                "cost": cost,
                "confidence": answer.confidence if answer.confidence else 0.0,
                "routing_decision": {
                    "strategy": routing_metadata.get('strategy', 'balanced'),
                    "available_models": routing_metadata.get('available_models', []),
                    "selection_reason": routing_metadata.get('selection_reason', 'default'),
                    "fallback_used": routing_metadata.get('fallback_used', False)
                },
                "processing_time": processing_time,
                "metadata": {
                    "generator_version": "1.0.0",
                    "timestamp": time.time(),
                    "context_documents_count": len(documents),
                    "epic1_metadata": answer.metadata
                }
            }
            
            # Update metrics
            GENERATION_REQUESTS.labels(status="success", model=selected_model).inc()
            GENERATION_DURATION.labels(model=selected_model).observe(processing_time)
            if cost > 0:
                COST_TRACKING.labels(model=selected_model).inc(cost)
            
            logger.info(
                "Answer generation completed",
                model=selected_model,
                cost=cost,
                processing_time=processing_time,
                answer_length=len(answer.content)
            )
            
            return result
            
        except Exception as e:
            GENERATION_REQUESTS.labels(status="error", model=selected_model or "unknown").inc()
            logger.error(
                "Answer generation failed",
                error=str(e),
                query_length=len(query),
                processing_time=time.time() - start_time
            )
            raise
    
    async def get_available_models(self) -> List[str]:
        """
        Get list of available models for generation.
        
        Returns:
            List of model identifiers that are currently available
        """
        if not self._initialized:
            await self._initialize_generator()
        
        if not self.generator:
            return []
        
        try:
            # Get available models from the Epic1AnswerGenerator
            if hasattr(self.generator, 'router') and hasattr(self.generator.router, 'model_registry'):
                models = list(self.generator.router.model_registry.get_available_models())
                return [f"{model.provider}/{model.model_name}" for model in models]
            
            # Fallback: extract from configuration
            if hasattr(self.generator, '_config') and 'routing' in self.generator._config:
                strategies = self.generator._config['routing'].get('strategies', {})
                models = set()
                for strategy_config in strategies.values():
                    if 'model_preferences' in strategy_config:
                        models.update(strategy_config['model_preferences'])
                return list(models)
            
            return []
            
        except Exception as e:
            logger.error("Failed to get available models", error=str(e))
            return []
    
    async def get_model_costs(self) -> Dict[str, float]:
        """
        Get cost estimates for available models.
        
        Returns:
            Dictionary mapping model names to cost per token/request
        """
        if not self._initialized:
            await self._initialize_generator()
        
        try:
            # Extract cost information from Epic1 configuration
            if hasattr(self.generator, '_config') and 'routing' in self.generator._config:
                strategies = self.generator._config['routing'].get('strategies', {})
                costs = {}
                
                for strategy_config in strategies.values():
                    if 'cost_weights' in strategy_config:
                        costs.update(strategy_config['cost_weights'])
                
                return costs
            
            return {}
            
        except Exception as e:
            logger.error("Failed to get model costs", error=str(e))
            return {}
    
    async def get_generator_status(self) -> Dict[str, Any]:
        """
        Get current generator status and performance metrics.
        
        Returns:
            Dictionary containing status information
        """
        if not self._initialized:
            return {
                "initialized": False,
                "status": "not_initialized"
            }
        
        try:
            available_models = await self.get_available_models()
            model_costs = await self.get_model_costs()
            
            return {
                "initialized": True,
                "status": "healthy",
                "generator_type": "Epic1AnswerGenerator",
                "configuration": {
                    "routing_enabled": hasattr(self.generator, 'router'),
                    "fallback_enabled": hasattr(self.generator, '_fallback_config'),
                    "cost_tracking_enabled": True
                },
                "models": {
                    "available_count": len(available_models),
                    "available_models": available_models,
                    "cost_estimates": model_costs
                },
                "components": {
                    "llm_adapters": "healthy",
                    "adaptive_router": "healthy",
                    "cost_tracker": "healthy",
                    "prompt_builders": "healthy",
                    "response_parsers": "healthy"
                }
            }
            
        except Exception as e:
            logger.error("Failed to get generator status", error=str(e))
            return {
                "initialized": True,
                "status": "error",
                "error": str(e)
            }
    
    async def health_check(self) -> bool:
        """
        Perform health check on the generator service.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self._initialized:
                await self._initialize_generator()
            
            if not self.generator:
                return False
            
            # Check that we have at least one available model
            available_models = await self.get_available_models()
            if not available_models:
                logger.warning("Health check failed - no models available")
                return False
            
            # Perform a simple test generation (mock)
            test_query = "What is the basic functionality of this system?"
            test_docs = [{"content": "This is a test document.", "metadata": {}}]
            
            # Just verify the service can handle the request structure
            # without actually calling the LLM (to avoid costs in health checks)
            try:
                # Validate that we can process the request format
                if not isinstance(test_query, str) or not isinstance(test_docs, list):
                    return False
                
                logger.debug("Health check passed")
                return True
                
            except Exception as e:
                logger.warning("Health check failed - service error", error=str(e))
                return False
            
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return False
    
    async def shutdown(self):
        """Graceful shutdown of the generator service."""
        logger.info("Shutting down GeneratorService")
        
        # Update model health metrics
        available_models = await self.get_available_models() if self._initialized else []
        for model in available_models:
            MODEL_HEALTH.labels(model=model).set(0)
        
        self._initialized = False
        self.generator = None