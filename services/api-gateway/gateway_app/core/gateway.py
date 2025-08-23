"""
API Gateway Service - Core orchestration logic.
"""

import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional
import structlog

from .config import APIGatewaySettings, get_settings


class SimpleCircuitBreaker:
    """Simple circuit breaker implementation."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    def __enter__(self):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half_open"
            else:
                raise Exception("Circuit breaker is open")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
        else:
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0


from ..clients import (
    QueryAnalyzerClient,
    GeneratorClient,
    RetrieverClient,
    CacheClient,
    AnalyticsClient,
    ServiceError,
    ServiceTimeoutError,
    ServiceUnavailableError
)
from ..schemas.requests import UnifiedQueryRequest, BatchQueryRequest
from ..schemas.responses import (
    UnifiedQueryResponse,
    BatchQueryResponse,
    BatchQueryResult,
    ProcessingMetrics,
    CostBreakdown,
    DocumentSource,
    GatewayStatusResponse,
    ServiceStatus,
    AvailableModelsResponse,
    ModelInfo
)

logger = structlog.get_logger(__name__)


class APIGatewayService:
    """
    API Gateway Service - Orchestrates calls to all other services.
    
    This service implements the unified query processing pipeline:
    1. Check cache for existing response
    2. Analyze query complexity and routing decisions
    3. Retrieve relevant documents  
    4. Generate answer using optimal model
    5. Cache response and record analytics
    """
    
    def __init__(self, settings: Optional[APIGatewaySettings] = None):
        self.settings = settings or get_settings()
        self.logger = logger.bind(service="api-gateway")
        
        # Service clients
        self.query_analyzer: Optional[QueryAnalyzerClient] = None
        self.generator: Optional[GeneratorClient] = None
        self.retriever: Optional[RetrieverClient] = None
        self.cache: Optional[CacheClient] = None
        self.analytics: Optional[AnalyticsClient] = None
        
        # Circuit breakers for resilience
        self.circuit_breakers: Dict[str, SimpleCircuitBreaker] = {}
        
        # Metrics
        self.start_time = time.time()
        self.requests_processed = 0
        self.total_response_time = 0.0
        self.error_count = 0
    
    async def initialize(self):
        """Initialize all service clients and circuit breakers."""
        self.logger.info("Initializing API Gateway Service")
        
        try:
            # Initialize service clients
            await self._initialize_clients()
            
            # Initialize circuit breakers
            self._initialize_circuit_breakers()
            
            # Perform initial health checks
            await self._perform_initial_health_checks()
            
            self.logger.info("API Gateway Service initialized successfully")
            
        except Exception as e:
            self.logger.error("Failed to initialize API Gateway Service", error=str(e))
            raise
    
    async def _initialize_clients(self):
        """Initialize all service clients."""
        # Query Analyzer client
        analyzer_endpoint = self.settings.get_service_endpoint("query-analyzer")
        self.query_analyzer = QueryAnalyzerClient(analyzer_endpoint)
        
        # Generator client
        generator_endpoint = self.settings.get_service_endpoint("generator")
        self.generator = GeneratorClient(generator_endpoint)
        
        # Retriever client
        retriever_endpoint = self.settings.get_service_endpoint("retriever")
        self.retriever = RetrieverClient(retriever_endpoint)
        
        # Cache client
        cache_endpoint = self.settings.get_service_endpoint("cache")
        self.cache = CacheClient(cache_endpoint)
        
        # Analytics client
        analytics_endpoint = self.settings.get_service_endpoint("analytics")
        self.analytics = AnalyticsClient(analytics_endpoint)
    
    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for each service."""
        services = ["query-analyzer", "generator", "retriever", "cache", "analytics"]
        
        for service in services:
            self.circuit_breakers[service] = SimpleCircuitBreaker(
                failure_threshold=self.settings.circuit_breaker_failure_threshold,
                recovery_timeout=self.settings.circuit_breaker_recovery_timeout
            )
    
    async def _perform_initial_health_checks(self):
        """Perform initial health checks on all services."""
        services = [
            ("query-analyzer", self.query_analyzer),
            ("generator", self.generator),
            ("retriever", self.retriever),
            ("cache", self.cache),
            ("analytics", self.analytics)
        ]
        
        for service_name, client in services:
            try:
                is_healthy = await client.health_check()
                self.logger.info(
                    "Service health check",
                    service=service_name,
                    healthy=is_healthy
                )
            except Exception as e:
                self.logger.warning(
                    "Service health check failed",
                    service=service_name,
                    error=str(e)
                )
    
    async def process_unified_query(self, request: UnifiedQueryRequest) -> UnifiedQueryResponse:
        """
        Process unified query through complete pipeline.
        
        Args:
            request: Unified query request
            
        Returns:
            Complete query response with answer, sources, metrics, and cost
        """
        query_id = str(uuid.uuid4())
        start_time = time.time()
        
        self.logger.info(
            "Processing unified query",
            query_id=query_id,
            query_length=len(request.query),
            strategy=request.options.strategy,
            session_id=request.session_id
        )
        
        try:
            # Step 1: Check cache first
            cached_response = None
            cache_time = 0.0
            
            if request.options.cache_enabled and not request.options.force_refresh:
                cache_start = time.time()
                cached_response = await self._get_cached_response(request.query_hash)
                cache_time = time.time() - cache_start
                
                if cached_response:
                    # Record cache hit and return cached response
                    if request.options.analytics_enabled:
                        await self._record_cache_hit(request)
                    
                    self.logger.info(
                        "Returning cached response",
                        query_id=query_id,
                        cache_time=cache_time
                    )
                    
                    return cached_response
            
            # Step 2: Full pipeline execution
            analysis_start = time.time()
            analysis = await self._analyze_query(request)
            analysis_time = time.time() - analysis_start
            
            # Step 3: Retrieve documents
            retrieval_start = time.time()
            documents = await self._retrieve_documents(request, analysis)
            retrieval_time = time.time() - retrieval_start
            
            # Step 4: Generate answer
            generation_start = time.time()
            answer_data = await self._generate_answer(request, documents, analysis)
            generation_time = time.time() - generation_start
            
            # Step 5: Build response
            total_time = time.time() - start_time
            
            response = self._build_unified_response(
                query_id=query_id,
                request=request,
                analysis=analysis,
                documents=documents,
                answer_data=answer_data,
                metrics=ProcessingMetrics(
                    analysis_time=analysis_time,
                    retrieval_time=retrieval_time,
                    generation_time=generation_time,
                    cache_time=cache_time if cache_time > 0 else None,
                    total_time=total_time,
                    documents_retrieved=len(documents),
                    tokens_generated=answer_data.get("tokens_generated"),
                    cache_hit=False,
                    cache_key=request.query_hash
                )
            )
            
            # Step 6: Cache response and record analytics
            if request.options.cache_enabled:
                await self._cache_response(request.query_hash, response)
            
            if request.options.analytics_enabled:
                await self._record_query_completion(request, response)
            
            # Update metrics
            self.requests_processed += 1
            self.total_response_time += total_time
            
            self.logger.info(
                "Query processing completed successfully",
                query_id=query_id,
                total_time=total_time,
                complexity=analysis.get("complexity"),
                cost=response.cost.total_cost
            )
            
            return response
            
        except Exception as e:
            self.error_count += 1
            
            # Record error analytics
            if request.options.analytics_enabled:
                await self._record_error("query_processing", str(e), request.query, request.session_id)
            
            self.logger.error(
                "Query processing failed",
                query_id=query_id,
                error=str(e),
                error_type=type(e).__name__
            )
            
            # Try fallback if available
            fallback_response = await self._try_fallback(request, query_id, str(e))
            if fallback_response:
                return fallback_response
            
            raise
    
    async def process_batch_queries(self, request: BatchQueryRequest) -> BatchQueryResponse:
        """
        Process multiple queries in batch.
        
        Args:
            request: Batch query request
            
        Returns:
            Batch processing results
        """
        batch_id = str(uuid.uuid4())
        start_time = time.time()
        
        self.logger.info(
            "Processing batch queries",
            batch_id=batch_id,
            query_count=len(request.queries),
            parallel_processing=request.parallel_processing,
            max_parallel=request.max_parallel
        )
        
        try:
            results: List[BatchQueryResult] = []
            
            if request.parallel_processing:
                # Process queries in parallel with semaphore to limit concurrency
                semaphore = asyncio.Semaphore(request.max_parallel or 10)
                tasks = []
                
                for i, query in enumerate(request.queries):
                    task = self._process_batch_query(semaphore, i, query, request)
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Convert exceptions to error results
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        results[i] = BatchQueryResult(
                            index=i,
                            query=request.queries[i],
                            success=False,
                            error=str(result),
                            error_code=type(result).__name__
                        )
            
            else:
                # Process queries sequentially
                for i, query in enumerate(request.queries):
                    try:
                        query_request = UnifiedQueryRequest(
                            query=query,
                            context=request.context,
                            options=request.options,
                            session_id=request.session_id,
                            user_id=request.user_id
                        )
                        
                        response = await self.process_unified_query(query_request)
                        
                        results.append(BatchQueryResult(
                            index=i,
                            query=query,
                            success=True,
                            result=response
                        ))
                        
                    except Exception as e:
                        results.append(BatchQueryResult(
                            index=i,
                            query=query,
                            success=False,
                            error=str(e),
                            error_code=type(e).__name__
                        ))
            
            # Calculate summary statistics
            successful = [r for r in results if r.success]
            failed = [r for r in results if not r.success]
            
            total_cost = sum(
                r.result.cost.total_cost for r in successful if r.result
            )
            
            avg_cost = total_cost / len(successful) if successful else 0.0
            
            processing_time = time.time() - start_time
            
            # Build summary
            summary = {
                "average_processing_time": processing_time / len(request.queries),
                "total_cost": total_cost,
                "average_cost_per_query": avg_cost,
                "success_rate": len(successful) / len(request.queries) if request.queries else 0.0,
                "complexity_distribution": self._calculate_complexity_distribution(successful)
            }
            
            batch_response = BatchQueryResponse(
                batch_id=batch_id,
                total_queries=len(request.queries),
                successful_queries=len(successful),
                failed_queries=len(failed),
                processing_time=processing_time,
                parallel_processing=request.parallel_processing,
                results=results,
                summary=summary,
                total_cost=total_cost,
                average_cost_per_query=avg_cost,
                session_id=request.session_id
            )
            
            self.logger.info(
                "Batch processing completed",
                batch_id=batch_id,
                successful=len(successful),
                failed=len(failed),
                total_cost=total_cost,
                processing_time=processing_time
            )
            
            return batch_response
            
        except Exception as e:
            self.logger.error("Batch processing failed", batch_id=batch_id, error=str(e))
            raise
    
    async def _process_batch_query(
        self,
        semaphore: asyncio.Semaphore,
        index: int,
        query: str,
        batch_request: BatchQueryRequest
    ) -> BatchQueryResult:
        """Process single query within batch with concurrency control."""
        async with semaphore:
            try:
                query_request = UnifiedQueryRequest(
                    query=query,
                    context=batch_request.context,
                    options=batch_request.options,
                    session_id=batch_request.session_id,
                    user_id=batch_request.user_id
                )
                
                response = await self.process_unified_query(query_request)
                
                return BatchQueryResult(
                    index=index,
                    query=query,
                    success=True,
                    result=response
                )
                
            except Exception as e:
                return BatchQueryResult(
                    index=index,
                    query=query,
                    success=False,
                    error=str(e),
                    error_code=type(e).__name__
                )
    
    async def _get_cached_response(self, query_hash: str) -> Optional[UnifiedQueryResponse]:
        """Get cached response with circuit breaker protection."""
        try:
            with self.circuit_breakers["cache"]:
                cached_data = await self.cache.get_cached_response(query_hash)
                if cached_data:
                    return UnifiedQueryResponse(**cached_data)
                return None
        except Exception as e:
            self.logger.warning("Cache lookup failed", error=str(e))
            return None
    
    async def _analyze_query(self, request: UnifiedQueryRequest) -> Dict[str, Any]:
        """Analyze query with circuit breaker protection."""
        try:
            with self.circuit_breakers["query-analyzer"]:
                return await self.query_analyzer.analyze_query(
                    query=request.query,
                    context=request.context,
                    complexity_hint=request.options.complexity_hint
                )
        except Exception as e:
            self.logger.error("Query analysis failed", error=str(e))
            # Return fallback analysis
            return {
                "complexity": "medium",
                "confidence": 0.5,
                "recommended_models": ["ollama/llama3.2:3b"],
                "cost_estimate": {"ollama/llama3.2:3b": 0.0},
                "routing_strategy": request.options.strategy,
                "processing_time": 0.0
            }
    
    async def _retrieve_documents(
        self,
        request: UnifiedQueryRequest,
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Retrieve documents with circuit breaker protection."""
        try:
            with self.circuit_breakers["retriever"]:
                max_docs = request.options.max_documents or analysis.get("recommended_doc_count", 10)
                return await self.retriever.retrieve_documents(
                    query=request.query,
                    max_documents=max_docs,
                    complexity=analysis.get("complexity"),
                    retrieval_strategy="hybrid"
                )
        except Exception as e:
            self.logger.error("Document retrieval failed", error=str(e))
            # Return empty documents list to allow generation to continue
            return []
    
    async def _generate_answer(
        self,
        request: UnifiedQueryRequest,
        documents: List[Dict[str, Any]],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate answer with circuit breaker protection."""
        try:
            with self.circuit_breakers["generator"]:
                routing_decision = analysis.get("recommended_models", ["ollama/llama3.2:3b"])[0]
                return await self.generator.generate_answer(
                    query=request.query,
                    context_documents=documents,
                    routing_decision=routing_decision,
                    complexity=analysis.get("complexity"),
                    strategy=request.options.strategy
                )
        except Exception as e:
            self.logger.error("Answer generation failed", error=str(e))
            raise  # Critical failure - cannot continue without answer
    
    def _build_unified_response(
        self,
        query_id: str,
        request: UnifiedQueryRequest,
        analysis: Dict[str, Any],
        documents: List[Dict[str, Any]],
        answer_data: Dict[str, Any],
        metrics: ProcessingMetrics
    ) -> UnifiedQueryResponse:
        """Build unified response from all components."""
        
        # Convert documents to response format
        sources = [
            DocumentSource(
                id=doc.get("id", str(i)),
                title=doc.get("title"),
                content=doc.get("content", ""),
                score=doc.get("score", 0.0),
                metadata=doc.get("metadata")
            )
            for i, doc in enumerate(documents)
        ]
        
        # Build cost breakdown
        cost = CostBreakdown(
            model_used=answer_data.get("model_used", "unknown"),
            input_tokens=answer_data.get("input_tokens"),
            output_tokens=answer_data.get("output_tokens"),
            model_cost=answer_data.get("cost", 0.0),
            retrieval_cost=0.0,  # Retrieval is currently free
            total_cost=answer_data.get("cost", 0.0),
            cost_estimation_confidence=analysis.get("cost_estimation_confidence", 1.0)
        )
        
        return UnifiedQueryResponse(
            answer=answer_data.get("answer", ""),
            sources=sources,
            complexity=analysis.get("complexity", "medium"),
            confidence=answer_data.get("confidence", 0.5),
            cost=cost,
            metrics=metrics,
            query_id=query_id,
            session_id=request.session_id,
            strategy_used=request.options.strategy,
            fallback_used=False,
            warnings=[]
        )
    
    async def _cache_response(self, query_hash: str, response: UnifiedQueryResponse) -> bool:
        """Cache response with circuit breaker protection."""
        try:
            with self.circuit_breakers["cache"]:
                return await self.cache.cache_response(
                    query_hash,
                    response.dict(),
                    ttl=3600  # 1 hour default TTL
                )
        except Exception as e:
            self.logger.warning("Response caching failed", error=str(e))
            return False
    
    async def _record_cache_hit(self, request: UnifiedQueryRequest) -> bool:
        """Record cache hit event."""
        try:
            with self.circuit_breakers["analytics"]:
                return await self.analytics.record_cache_hit(
                    query_hash=request.query_hash,
                    session_id=request.session_id,
                    user_id=request.user_id
                )
        except Exception as e:
            self.logger.warning("Cache hit recording failed", error=str(e))
            return False
    
    async def _record_query_completion(
        self,
        request: UnifiedQueryRequest,
        response: UnifiedQueryResponse
    ) -> bool:
        """Record query completion event."""
        try:
            with self.circuit_breakers["analytics"]:
                return await self.analytics.record_query_completion(
                    query_request=request.dict(),
                    query_response=response.dict()
                )
        except Exception as e:
            self.logger.warning("Query completion recording failed", error=str(e))
            return False
    
    async def _record_error(
        self,
        error_type: str,
        error_message: str,
        query: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """Record error event."""
        try:
            with self.circuit_breakers["analytics"]:
                return await self.analytics.record_error(
                    error_type=error_type,
                    error_message=error_message,
                    query=query,
                    service="api-gateway",
                    session_id=session_id
                )
        except Exception as e:
            self.logger.warning("Error recording failed", error=str(e))
            return False
    
    async def _try_fallback(
        self,
        request: UnifiedQueryRequest,
        query_id: str,
        error_message: str
    ) -> Optional[UnifiedQueryResponse]:
        """Try fallback response generation."""
        try:
            self.logger.info("Attempting fallback response", query_id=query_id)
            
            # Simple fallback: return a basic response
            fallback_metrics = ProcessingMetrics(
                analysis_time=0.0,
                retrieval_time=0.0,
                generation_time=0.0,
                total_time=0.0,
                documents_retrieved=0,
                cache_hit=False,
                cache_key=None
            )
            
            fallback_cost = CostBreakdown(
                model_used="fallback",
                model_cost=0.0,
                total_cost=0.0
            )
            
            return UnifiedQueryResponse(
                answer=f"I apologize, but I'm unable to process your query at the moment due to a service issue. Please try again later. Error: {error_message}",
                sources=[],
                complexity="unknown",
                confidence=0.0,
                cost=fallback_cost,
                metrics=fallback_metrics,
                query_id=query_id,
                session_id=request.session_id,
                strategy_used=request.options.strategy,
                fallback_used=True,
                warnings=[f"Fallback response due to: {error_message}"]
            )
            
        except Exception as e:
            self.logger.error("Fallback response failed", error=str(e))
            return None
    
    def _calculate_complexity_distribution(self, successful_results: List[BatchQueryResult]) -> Dict[str, int]:
        """Calculate complexity distribution for batch results."""
        distribution = {"simple": 0, "medium": 0, "complex": 0, "unknown": 0}
        
        for result in successful_results:
            if result.result:
                complexity = result.result.complexity
                if complexity in distribution:
                    distribution[complexity] += 1
                else:
                    distribution["unknown"] += 1
        
        return distribution
    
    async def get_gateway_status(self) -> GatewayStatusResponse:
        """Get comprehensive gateway status."""
        try:
            self.logger.debug("Getting gateway status")
            
            # Check service health
            services = []
            healthy_count = 0
            
            service_clients = [
                ("query-analyzer", self.query_analyzer),
                ("generator", self.generator),
                ("retriever", self.retriever),
                ("cache", self.cache),
                ("analytics", self.analytics)
            ]
            
            for service_name, client in service_clients:
                try:
                    start_time = time.time()
                    is_healthy = await client.health_check()
                    response_time = time.time() - start_time
                    
                    status = ServiceStatus(
                        name=service_name,
                        status="healthy" if is_healthy else "unhealthy",
                        url=client.endpoint.url,
                        response_time=response_time
                    )
                    
                    if is_healthy:
                        healthy_count += 1
                        
                except Exception as e:
                    status = ServiceStatus(
                        name=service_name,
                        status="error",
                        url=client.endpoint.url if client else "unknown",
                        error=str(e)
                    )
                
                services.append(status)
            
            # Calculate metrics
            uptime = time.time() - self.start_time
            avg_response_time = (
                self.total_response_time / self.requests_processed
                if self.requests_processed > 0 else 0.0
            )
            error_rate = (
                self.error_count / self.requests_processed * 100
                if self.requests_processed > 0 else 0.0
            )
            
            # Get circuit breaker states
            circuit_breaker_states = {
                name: str(cb.state) for name, cb in self.circuit_breakers.items()
            }
            
            # Try to get cache metrics
            cache_hit_rate = None
            cache_size = None
            try:
                if self.cache:
                    cache_stats = await self.cache.get_cache_statistics()
                    cache_hit_rate = cache_stats.get("hit_rate")
                    cache_size = cache_stats.get("total_keys")
            except Exception:
                pass  # Cache metrics are optional
            
            return GatewayStatusResponse(
                status="healthy" if healthy_count == len(service_clients) else "degraded",
                uptime=uptime,
                services=services,
                healthy_services=healthy_count,
                total_services=len(service_clients),
                requests_processed=self.requests_processed,
                average_response_time=avg_response_time,
                error_rate=error_rate,
                circuit_breakers=circuit_breaker_states,
                cache_hit_rate=cache_hit_rate,
                cache_size=cache_size
            )
            
        except Exception as e:
            self.logger.error("Failed to get gateway status", error=str(e))
            raise
    
    async def get_available_models(self) -> AvailableModelsResponse:
        """Get available models from all providers."""
        try:
            self.logger.debug("Getting available models")
            
            # Get models from generator service
            models_data = await self.generator.get_available_models()
            
            models = []
            for model_data in models_data.get("models", []):
                # Add missing 'type' field required by Epic 8 ModelInfo schema
                if "type" not in model_data:
                    model_data["type"] = "generative"  # Default type for LLM models
                models.append(ModelInfo(**model_data))
            
            available_count = len([m for m in models if m.available])
            providers = list(set(m.provider for m in models))
            
            return AvailableModelsResponse(
                models=models,
                total_models=len(models),
                available_models=available_count,
                providers=providers
            )
            
        except Exception as e:
            self.logger.error("Failed to get available models", error=str(e))
            raise
    
    async def close(self):
        """Close all service clients."""
        self.logger.info("Closing API Gateway Service")
        
        clients = [
            self.query_analyzer,
            self.generator,
            self.retriever,
            self.cache,
            self.analytics
        ]
        
        for client in clients:
            if client:
                try:
                    await client.close()
                except Exception as e:
                    self.logger.warning("Error closing client", error=str(e))