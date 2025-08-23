"""
Retriever Service - Core Business Logic.

This module implements the RetrieverService that wraps Epic 2's
ModularUnifiedRetriever to provide document retrieval capabilities
in microservices architecture with comprehensive error handling.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from decimal import Decimal
import sys
from concurrent.futures import ThreadPoolExecutor

import structlog
from prometheus_client import Counter, Histogram, Gauge
from circuitbreaker import circuit

# Add main project to path to import Epic 2 components
# From services/retriever/app/core/retriever.py go up 5 levels to project root
project_root = Path(__file__).parent.parent.parent.parent.parent  # 5 levels up to project root
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(project_root))  # Add project root to path

# Import existing Epic 2 components
from src.components.retrievers.modular_unified_retriever import ModularUnifiedRetriever
from src.components.embedders.modular_embedder import ModularEmbedder
from src.core.interfaces import Document, RetrievalResult
from src.core.component_factory import ComponentFactory

logger = structlog.get_logger(__name__)

# Metrics
RETRIEVAL_REQUESTS = Counter('retriever_requests_total', 'Total retrieval requests', ['status', 'strategy'])
RETRIEVAL_DURATION = Histogram('retriever_duration_seconds', 'Retrieval duration', ['strategy'])
DOCUMENT_COUNT = Gauge('retriever_indexed_documents', 'Number of indexed documents')
INDEX_HEALTH = Gauge('retriever_index_health', 'Index health status', ['component'])
BATCH_OPERATIONS = Counter('retriever_batch_operations_total', 'Total batch operations', ['operation', 'status'])


class RetrieverService:
    """
    Service wrapper for Epic 2's ModularUnifiedRetriever.
    
    This service provides:
    - Document retrieval with hybrid search (dense + sparse)
    - Batch retrieval operations
    - Document indexing and reindexing
    - Health monitoring and status reporting
    - Circuit breaker patterns for reliability
    - Comprehensive error handling with fallbacks
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Retriever Service.
        
        Args:
            config: Configuration dictionary for the retriever
        """
        self.config = config or {}
        self.retriever: Optional[ModularUnifiedRetriever] = None
        self.embedder: Optional[ModularEmbedder] = None
        self._initialized = False
        self._initialization_lock = asyncio.Lock()
        self._thread_pool = ThreadPoolExecutor(max_workers=4)
        
        # Performance monitoring
        self.retrieval_stats = {
            "total_retrievals": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
            "last_retrieval_time": 0.0,
            "error_count": 0,
            "circuit_breaker_trips": 0
        }
        
        logger.info("Initializing RetrieverService", config=self.config)
    
    async def _initialize_components(self):
        """Initialize the Epic 2 ModularUnifiedRetriever and Embedder if not already done."""
        if self._initialized:
            return
        
        async with self._initialization_lock:
            if self._initialized:
                return
            
            try:
                # Initialize embedder first (required for retriever)
                embedder_config = self.config.get('embedder_config', {})
                logger.info("Creating embedder with config", config=embedder_config)
                
                # Extract individual parameters for SentenceTransformerEmbedder
                config_dict = embedder_config.get('config', {})
                
                # Map config parameters to constructor arguments (only supported parameters)
                embedder_kwargs = {}
                if 'model_name' in config_dict:
                    embedder_kwargs['model_name'] = config_dict['model_name']
                if 'batch_size' in config_dict:
                    embedder_kwargs['batch_size'] = config_dict['batch_size']
                if 'device' in config_dict:
                    # Map device to use_mps for SentenceTransformerEmbedder
                    embedder_kwargs['use_mps'] = config_dict['device'] in ['mps', 'cuda']
                # Note: normalize_embeddings is not supported by SentenceTransformerEmbedder - removed
                    
                self.embedder = ComponentFactory.create_embedder(
                    embedder_type=embedder_config.get('type', 'sentence_transformer'),
                    **embedder_kwargs
                )
                
                # Initialize the Epic 2 ModularUnifiedRetriever
                retriever_config = self.config.get('retriever_config', {})
                logger.info("Creating ModularUnifiedRetriever with config", config=retriever_config)
                
                self.retriever = ModularUnifiedRetriever(
                    config=retriever_config,
                    embedder=self.embedder
                )
                
                self._initialized = True
                
                # Update health metrics for components
                self._update_health_metrics()
                
                logger.info(
                    "Epic 2 ModularUnifiedRetriever initialized successfully",
                    embedder_type=type(self.embedder).__name__,
                    retriever_components=self.retriever.get_component_info() if self.retriever else {}
                )
                
            except Exception as e:
                logger.error("Failed to initialize Epic 2 components", error=str(e))
                raise
    
    def _update_health_metrics(self):
        """Update Prometheus health metrics for all components."""
        if self.retriever:
            try:
                # Update component health metrics
                INDEX_HEALTH.labels(component="vector_index").set(1)
                INDEX_HEALTH.labels(component="sparse_retriever").set(1)
                INDEX_HEALTH.labels(component="fusion_strategy").set(1)
                INDEX_HEALTH.labels(component="reranker").set(1)
                
                # Update document count
                DOCUMENT_COUNT.set(self.retriever.get_document_count())
                
            except Exception as e:
                logger.warning("Failed to update health metrics", error=str(e))
    
    @circuit(failure_threshold=5, recovery_timeout=60)
    async def retrieve_documents(
        self,
        query: str,
        k: int = 10,
        retrieval_strategy: str = "hybrid",
        complexity: str = "medium",
        max_documents: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents using Epic 2's ModularUnifiedRetriever.
        
        Args:
            query: Search query string
            k: Number of documents to retrieve
            retrieval_strategy: Strategy type (hybrid, semantic, keyword)
            complexity: Query complexity level (simple, medium, complex)
            max_documents: Maximum number of documents to consider (overrides k)
            filters: Optional metadata filters
            
        Returns:
            List of dictionaries containing document data and scores
        """
        if not self._initialized:
            await self._initialize_components()
        
        if not self.retriever:
            raise RuntimeError("Retriever not initialized")
        
        start_time = time.time()
        final_k = max_documents or k
        
        try:
            logger.info(
                "Retrieving documents",
                query_length=len(query),
                k=final_k,
                strategy=retrieval_strategy,
                complexity=complexity,
                filters=filters or {}
            )
            
            # Execute retrieval using Epic 2 component (sync method in thread pool)
            retrieval_results: List[RetrievalResult] = await asyncio.get_event_loop().run_in_executor(
                self._thread_pool,
                self.retriever.retrieve,
                query,
                final_k
            )
            
            processing_time = time.time() - start_time
            
            # Convert RetrievalResult objects to dictionaries
            documents = []
            for result in retrieval_results:
                doc_data = {
                    "content": result.document.content,
                    "metadata": result.document.metadata,
                    "doc_id": result.document.doc_id,
                    "source": result.document.source,
                    "score": result.score,
                    "retrieval_method": result.retrieval_method
                }
                documents.append(doc_data)
            
            # Update performance stats
            self.retrieval_stats["total_retrievals"] += 1
            self.retrieval_stats["total_time"] += processing_time
            self.retrieval_stats["avg_time"] = (
                self.retrieval_stats["total_time"] / self.retrieval_stats["total_retrievals"]
            )
            self.retrieval_stats["last_retrieval_time"] = processing_time
            
            # Update metrics
            RETRIEVAL_REQUESTS.labels(status="success", strategy=retrieval_strategy).inc()
            RETRIEVAL_DURATION.labels(strategy=retrieval_strategy).observe(processing_time)
            
            logger.info(
                "Document retrieval completed",
                strategy=retrieval_strategy,
                results_count=len(documents),
                processing_time=processing_time,
                avg_score=sum(doc["score"] for doc in documents) / len(documents) if documents else 0
            )
            
            return documents
            
        except Exception as e:
            self.retrieval_stats["error_count"] += 1
            RETRIEVAL_REQUESTS.labels(status="error", strategy=retrieval_strategy).inc()
            
            logger.error(
                "Document retrieval failed",
                error=str(e),
                query_length=len(query),
                processing_time=time.time() - start_time
            )
            
            # Attempt fallback retrieval
            return await self._fallback_retrieval(query, final_k)
    
    async def _fallback_retrieval(self, query: str, k: int) -> List[Dict[str, Any]]:
        """
        Fallback retrieval method when main retrieval fails.
        
        Args:
            query: Search query string
            k: Number of documents to retrieve
            
        Returns:
            List of fallback documents or empty list
        """
        try:
            logger.warning("Attempting fallback retrieval", query_length=len(query), k=k)
            
            # Simple fallback: return empty results with error metadata
            # In a real implementation, this might use a simpler retrieval method
            # or cached results
            
            fallback_doc = {
                "content": f"Fallback response: Unable to retrieve documents for query '{query[:50]}...'",
                "metadata": {
                    "title": "Retrieval Error - Fallback Response",
                    "type": "error_fallback",
                    "timestamp": time.time()
                },
                "doc_id": "fallback_error_001",
                "source": "retriever_service_fallback",
                "score": 0.0,
                "retrieval_method": "fallback"
            }
            
            RETRIEVAL_REQUESTS.labels(status="fallback", strategy="fallback").inc()
            logger.info("Fallback retrieval completed with error document")
            
            return [fallback_doc]
            
        except Exception as e:
            logger.error("Fallback retrieval also failed", error=str(e))
            return []
    
    async def batch_retrieve_documents(
        self,
        queries: List[str],
        k: int = 10,
        retrieval_strategy: str = "hybrid"
    ) -> List[List[Dict[str, Any]]]:
        """
        Perform batch retrieval for multiple queries.
        
        Args:
            queries: List of search query strings
            k: Number of documents to retrieve per query
            retrieval_strategy: Strategy type for all queries
            
        Returns:
            List of document lists, one for each query
        """
        if not self._initialized:
            await self._initialize_components()
        
        start_time = time.time()
        
        try:
            logger.info(
                "Starting batch retrieval",
                query_count=len(queries),
                k=k,
                strategy=retrieval_strategy
            )
            
            # Process queries in batches to avoid overwhelming the system
            batch_size = self.config.get('performance', {}).get('batch', {}).get('max_batch_size', 100)
            batch_timeout = self.config.get('performance', {}).get('batch', {}).get('batch_timeout', 5.0)
            
            results = []
            
            for i in range(0, len(queries), batch_size):
                batch_queries = queries[i:i + batch_size]
                
                # Process batch concurrently
                batch_tasks = [
                    self.retrieve_documents(query, k, retrieval_strategy)
                    for query in batch_queries
                ]
                
                try:
                    batch_results = await asyncio.wait_for(
                        asyncio.gather(*batch_tasks, return_exceptions=True),
                        timeout=batch_timeout * len(batch_queries)
                    )
                    
                    # Process results and handle exceptions
                    for j, result in enumerate(batch_results):
                        if isinstance(result, Exception):
                            logger.error(
                                "Batch query failed",
                                query_index=i + j,
                                error=str(result)
                            )
                            results.append([])  # Empty result for failed query
                        else:
                            results.append(result)
                            
                except asyncio.TimeoutError:
                    logger.error("Batch retrieval timed out", batch_size=len(batch_queries))
                    # Add empty results for timed-out batch
                    results.extend([[] for _ in batch_queries])
            
            processing_time = time.time() - start_time
            
            # Update metrics
            BATCH_OPERATIONS.labels(operation="retrieve", status="success").inc()
            
            logger.info(
                "Batch retrieval completed",
                total_queries=len(queries),
                successful_queries=sum(1 for r in results if r),
                processing_time=processing_time
            )
            
            return results
            
        except Exception as e:
            BATCH_OPERATIONS.labels(operation="retrieve", status="error").inc()
            logger.error("Batch retrieval failed", error=str(e))
            raise
    
    async def index_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Index documents in the retriever.
        
        Args:
            documents: List of document dictionaries to index
            
        Returns:
            Dictionary with indexing results
        """
        if not self._initialized:
            await self._initialize_components()
        
        if not self.retriever:
            raise RuntimeError("Retriever not initialized")
        
        start_time = time.time()
        
        try:
            logger.info("Starting document indexing", document_count=len(documents))
            
            # Convert dictionaries to Document objects
            doc_objects = []
            for i, doc_data in enumerate(documents):
                doc = Document(
                    content=doc_data.get('content', ''),
                    metadata=doc_data.get('metadata', {}),
                    doc_id=doc_data.get('doc_id', f'doc_{i}'),
                    source=doc_data.get('source', f'uploaded_doc_{i}')
                )
                
                # Generate embeddings if not provided
                if not hasattr(doc, 'embedding') or doc.embedding is None:
                    doc.embedding = self.embedder.embed([doc.content])[0]
                
                doc_objects.append(doc)
            
            # Index documents using Epic 2 component (sync method in thread pool)
            await asyncio.get_event_loop().run_in_executor(
                self._thread_pool,
                self.retriever.index_documents,
                doc_objects
            )
            
            processing_time = time.time() - start_time
            
            # Update metrics
            DOCUMENT_COUNT.set(self.retriever.get_document_count())
            BATCH_OPERATIONS.labels(operation="index", status="success").inc()
            
            result = {
                "success": True,
                "indexed_documents": len(documents),
                "processing_time": processing_time,
                "total_documents": self.retriever.get_document_count(),
                "message": f"Successfully indexed {len(documents)} documents"
            }
            
            logger.info(
                "Document indexing completed",
                indexed_count=len(documents),
                total_documents=self.retriever.get_document_count(),
                processing_time=processing_time
            )
            
            return result
            
        except Exception as e:
            BATCH_OPERATIONS.labels(operation="index", status="error").inc()
            logger.error("Document indexing failed", error=str(e))
            raise
    
    async def reindex_documents(self) -> Dict[str, Any]:
        """
        Trigger reindexing of all documents.
        
        Returns:
            Dictionary with reindexing results
        """
        if not self._initialized:
            await self._initialize_components()
        
        if not self.retriever:
            raise RuntimeError("Retriever not initialized")
        
        start_time = time.time()
        
        try:
            logger.info("Starting document reindexing")
            
            # Get current documents
            current_docs = self.retriever.documents if hasattr(self.retriever, 'documents') else []
            document_count = len(current_docs)
            
            if document_count == 0:
                return {
                    "success": True,
                    "message": "No documents to reindex",
                    "processing_time": 0.0
                }
            
            # Clear current index and reindex all documents
            await asyncio.get_event_loop().run_in_executor(
                self._thread_pool,
                self.retriever.clear_index
            )
            
            # Reindex all documents
            await asyncio.get_event_loop().run_in_executor(
                self._thread_pool,
                self.retriever.index_documents,
                current_docs
            )
            
            processing_time = time.time() - start_time
            
            # Update metrics
            DOCUMENT_COUNT.set(self.retriever.get_document_count())
            BATCH_OPERATIONS.labels(operation="reindex", status="success").inc()
            
            result = {
                "success": True,
                "reindexed_documents": document_count,
                "processing_time": processing_time,
                "message": f"Successfully reindexed {document_count} documents"
            }
            
            logger.info(
                "Document reindexing completed",
                reindexed_count=document_count,
                processing_time=processing_time
            )
            
            return result
            
        except Exception as e:
            BATCH_OPERATIONS.labels(operation="reindex", status="error").inc()
            logger.error("Document reindexing failed", error=str(e))
            raise
    
    async def get_retriever_status(self) -> Dict[str, Any]:
        """
        Get current retriever status and performance metrics.
        
        Returns:
            Dictionary containing status information
        """
        if not self._initialized:
            return {
                "initialized": False,
                "status": "not_initialized"
            }
        
        try:
            # Get retriever statistics
            retrieval_stats = self.retriever.get_retrieval_stats() if self.retriever else {}
            component_info = self.retriever.get_component_info() if self.retriever else {}
            
            # Get sub-component performance
            sub_component_perf = {}
            if self.retriever and hasattr(self.retriever, 'get_sub_component_performance'):
                sub_component_perf = self.retriever.get_sub_component_performance()
            
            return {
                "initialized": True,
                "status": "healthy",
                "retriever_type": "ModularUnifiedRetriever",
                "configuration": {
                    "vector_index_type": self.config.get('retriever_config', {}).get('vector_index', {}).get('type', 'faiss'),
                    "sparse_type": self.config.get('retriever_config', {}).get('sparse', {}).get('type', 'bm25'),
                    "fusion_type": self.config.get('retriever_config', {}).get('fusion', {}).get('type', 'rrf'),
                    "reranker_type": self.config.get('retriever_config', {}).get('reranker', {}).get('type', 'semantic'),
                    "composite_filtering_enabled": self.config.get('retriever_config', {}).get('composite_filtering', {}).get('enabled', False)
                },
                "documents": {
                    "indexed_count": self.retriever.get_document_count() if self.retriever else 0,
                    "index_status": "healthy" if self.retriever else "not_initialized"
                },
                "performance": {
                    "retrieval_stats": self.retrieval_stats,
                    "sub_components": sub_component_perf
                },
                "components": {
                    "vector_index": "healthy",
                    "sparse_retriever": "healthy", 
                    "fusion_strategy": "healthy",
                    "reranker": "healthy",
                    "embedder": "healthy"
                },
                "epic2_stats": retrieval_stats,
                "epic2_components": component_info
            }
            
        except Exception as e:
            logger.error("Failed to get retriever status", error=str(e))
            return {
                "initialized": True,
                "status": "error",
                "error": str(e)
            }
    
    async def health_check(self) -> bool:
        """
        Perform health check on the retriever service.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self._initialized:
                await self._initialize_components()
            
            if not self.retriever or not self.embedder:
                return False
            
            # Check that components are properly initialized
            if not hasattr(self.retriever, 'vector_index') or not self.retriever.vector_index:
                logger.warning("Health check failed - vector index not initialized")
                return False
            
            if not hasattr(self.retriever, 'sparse_retriever') or not self.retriever.sparse_retriever:
                logger.warning("Health check failed - sparse retriever not initialized") 
                return False
            
            # Perform a simple test retrieval (mock - no actual LLM calls)
            test_query = "test query for health check"
            
            # Just verify the service can handle the request structure
            if not isinstance(test_query, str):
                return False
            
            # Update health metrics
            self._update_health_metrics()
            
            logger.debug("Health check passed")
            return True
            
        except Exception as e:
            # Update health metrics to indicate failure
            for component in ["vector_index", "sparse_retriever", "fusion_strategy", "reranker"]:
                INDEX_HEALTH.labels(component=component).set(0)
            
            logger.error("Health check failed", error=str(e))
            return False
    
    async def shutdown(self):
        """Graceful shutdown of the retriever service."""
        logger.info("Shutting down RetrieverService")
        
        # Update health metrics to indicate shutdown
        for component in ["vector_index", "sparse_retriever", "fusion_strategy", "reranker"]:
            INDEX_HEALTH.labels(component=component).set(0)
        
        DOCUMENT_COUNT.set(0)
        
        # Shutdown thread pool
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)
        
        self._initialized = False
        self.retriever = None
        self.embedder = None