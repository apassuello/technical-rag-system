"""
Advanced Retriever for Epic 2 Implementation.

This module provides an advanced retriever that extends the ModularUnifiedRetriever
with multi-backend support, hybrid search strategies, neural reranking, and real-time
analytics. It maintains backward compatibility while adding sophisticated features.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np

from src.core.interfaces import Retriever, Document, RetrievalResult, Embedder
from .modular_unified_retriever import ModularUnifiedRetriever
from .backends.faiss_backend import FAISSBackend
from .backends.weaviate_backend import WeaviateBackend
from .config.advanced_config import AdvancedRetrieverConfig
from .backends.migration.faiss_to_weaviate import FAISSToWeaviateMigrator

logger = logging.getLogger(__name__)


class AdvancedRetrievalError(Exception):
    """Raised when advanced retrieval operations fail."""
    pass


class AdvancedRetriever(ModularUnifiedRetriever):
    """
    Advanced retriever with multi-backend support and sophisticated features.
    
    This retriever extends the ModularUnifiedRetriever to provide:
    - Multiple vector database backends (FAISS, Weaviate)
    - Hot-swapping between backends with health monitoring
    - Advanced hybrid search strategies
    - Neural reranking capabilities (future)
    - Knowledge graph integration (future)
    - Real-time analytics and monitoring
    - A/B testing framework (future)
    
    The implementation follows the existing architecture patterns while
    adding Epic 2 enhancements. It maintains full backward compatibility
    with the ModularUnifiedRetriever interface.
    
    Features in this implementation:
    - ✅ Multi-backend support (FAISS + Weaviate)
    - ✅ Backend health monitoring and fallbacks
    - ✅ Migration tools between backends
    - ✅ Enhanced hybrid search
    - 🔄 Neural reranking (framework ready)
    - 🔄 Graph-based retrieval (framework ready)
    - ✅ Performance analytics
    - 🔄 A/B testing (framework ready)
    """
    
    def __init__(self, config: Union[Dict[str, Any], AdvancedRetrieverConfig], embedder: Embedder):
        """
        Initialize the advanced retriever.
        
        Args:
            config: Configuration dictionary or AdvancedRetrieverConfig instance
            embedder: Embedder component for query encoding
        """
        # Convert config if needed
        if isinstance(config, dict):
            self.advanced_config = AdvancedRetrieverConfig.from_dict(config)
        else:
            self.advanced_config = config
        
        # Initialize parent with base configuration
        base_config = self._extract_base_config()
        super().__init__(base_config, embedder)
        
        # Advanced components
        self.backends: Dict[str, Any] = {}
        self.active_backend_name = self.advanced_config.backends.primary_backend
        self.fallback_backend_name = self.advanced_config.backends.fallback_backend
        
        # Performance tracking
        self.advanced_stats = {
            "backend_switches": 0,
            "fallback_activations": 0,
            "total_advanced_retrievals": 0,
            "backend_health_checks": 0,
            "last_health_check": 0,
            "migration_count": 0
        }
        
        # Analytics collector
        self.analytics_enabled = self.advanced_config.analytics.enabled
        self.query_analytics: List[Dict[str, Any]] = []
        
        # Initialize backends
        self._initialize_backends()
        
        # Set up health monitoring
        if self.advanced_config.backends.enable_hot_swap:
            self._setup_health_monitoring()
        
        logger.info(f"Advanced retriever initialized with backend: {self.active_backend_name}")
        logger.info(f"Enabled features: {self.advanced_config.get_enabled_features()}")
    
    def _extract_base_config(self) -> Dict[str, Any]:
        """Extract base configuration for ModularUnifiedRetriever."""
        return {
            "vector_index": {
                "type": "faiss",
                "config": self.advanced_config.backends.faiss
            },
            "sparse": {
                "type": "bm25",
                "config": {
                    "k1": 1.2,
                    "b": 0.75,
                    "lowercase": True,
                    "preserve_technical_terms": True
                }
            },
            "fusion": {
                "type": self.advanced_config.hybrid_search.fusion_method,
                "config": {
                    "k": self.advanced_config.hybrid_search.rrf_k,
                    "weights": {
                        "dense": self.advanced_config.hybrid_search.dense_weight,
                        "sparse": self.advanced_config.hybrid_search.sparse_weight
                    }
                }
            },
            "reranker": {
                "type": "identity",
                "config": {"enabled": True}
            }
        }
    
    def _initialize_backends(self) -> None:
        """Initialize all configured backends."""
        # Initialize FAISS backend (wraps existing functionality)
        faiss_config = {"faiss": self.advanced_config.backends.faiss}
        self.backends["faiss"] = FAISSBackend(faiss_config)
        
        # Initialize Weaviate backend if enabled
        if (self.advanced_config.feature_flags.get("weaviate_backend", False) and 
            self.advanced_config.backends.weaviate):
            
            try:
                self.backends["weaviate"] = WeaviateBackend(self.advanced_config.backends.weaviate)
                logger.info("Weaviate backend initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Weaviate backend: {str(e)}")
                if self.active_backend_name == "weaviate":
                    logger.info("Falling back to FAISS backend")
                    self.active_backend_name = "faiss"
        
        # Validate active backend
        if self.active_backend_name not in self.backends:
            raise AdvancedRetrievalError(f"Active backend '{self.active_backend_name}' not available")
    
    def _setup_health_monitoring(self) -> None:
        """Set up backend health monitoring."""
        logger.info("Health monitoring enabled for backend hot-swapping")
        # Health monitoring implementation would go here
        # For now, we set up the framework
    
    def retrieve(self, query: str, k: int = 5) -> List[RetrievalResult]:
        """
        Retrieve relevant documents using advanced multi-backend search.
        
        This method extends the base retrieve method with:
        - Multi-backend support with automatic fallback
        - Enhanced analytics collection
        - Performance monitoring
        - Health-based backend switching
        
        Args:
            query: Search query string
            k: Number of results to return
            
        Returns:
            List of retrieval results sorted by relevance score
        """
        start_time = time.time()
        
        try:
            # Pre-retrieval analytics
            if self.analytics_enabled:
                self._collect_query_start_analytics(query, k)
            
            # Check backend health and switch if needed
            if self.advanced_config.backends.enable_hot_swap:
                self._check_and_switch_backend()
            
            # Attempt retrieval with active backend
            try:
                results = self._retrieve_with_backend(query, k, self.active_backend_name)
                
                # Post-retrieval analytics
                if self.analytics_enabled:
                    elapsed_time = time.time() - start_time
                    self._collect_query_completion_analytics(query, k, results, elapsed_time, self.active_backend_name)
                
                return results
                
            except Exception as backend_error:
                logger.warning(f"Retrieval failed with {self.active_backend_name} backend: {str(backend_error)}")
                
                # Try fallback backend if enabled
                if (self.advanced_config.backends.fallback_enabled and 
                    self.fallback_backend_name and 
                    self.fallback_backend_name in self.backends):
                    
                    logger.info(f"Attempting fallback to {self.fallback_backend_name} backend")
                    
                    try:
                        results = self._retrieve_with_backend(query, k, self.fallback_backend_name)
                        self.advanced_stats["fallback_activations"] += 1
                        
                        # Consider switching backends
                        if self.advanced_config.backends.enable_hot_swap:
                            self._consider_backend_switch(backend_error)
                        
                        if self.analytics_enabled:
                            elapsed_time = time.time() - start_time
                            self._collect_query_completion_analytics(
                                query, k, results, elapsed_time, 
                                f"{self.active_backend_name}_fallback_{self.fallback_backend_name}"
                            )
                        
                        return results
                        
                    except Exception as fallback_error:
                        logger.error(f"Fallback retrieval also failed: {str(fallback_error)}")
                        raise AdvancedRetrievalError(
                            f"Both primary ({self.active_backend_name}) and fallback "
                            f"({self.fallback_backend_name}) backends failed"
                        ) from backend_error
                else:
                    raise AdvancedRetrievalError(f"Retrieval failed with {self.active_backend_name}") from backend_error
                    
        except Exception as e:
            logger.error(f"Advanced retrieval failed: {str(e)}")
            
            # Try fallback to parent implementation as last resort
            if not isinstance(e, AdvancedRetrievalError):
                logger.info("Attempting fallback to base ModularUnifiedRetriever")
                try:
                    return super().retrieve(query, k)
                except Exception:
                    pass
            
            raise RuntimeError(f"Advanced retrieval failed: {str(e)}") from e
    
    def _retrieve_with_backend(self, query: str, k: int, backend_name: str) -> List[RetrievalResult]:
        """
        Perform retrieval using specified backend.
        
        Args:
            query: Search query
            k: Number of results
            backend_name: Name of backend to use
            
        Returns:
            List of retrieval results
        """
        if backend_name not in self.backends:
            raise ValueError(f"Backend '{backend_name}' not available")
        
        backend = self.backends[backend_name]
        
        if backend_name == "faiss":
            # Use FAISS backend (falls back to parent implementation)
            return super().retrieve(query, k)
        
        elif backend_name == "weaviate":
            # Use Weaviate backend with enhanced search
            return self._retrieve_with_weaviate(query, k, backend)
        
        else:
            raise ValueError(f"Unknown backend: {backend_name}")
    
    def _retrieve_with_weaviate(self, query: str, k: int, backend: WeaviateBackend) -> List[RetrievalResult]:
        """
        Perform retrieval using Weaviate backend.
        
        Args:
            query: Search query
            k: Number of results
            backend: Weaviate backend instance
            
        Returns:
            List of retrieval results
        """
        # Generate query embedding
        query_embedding = np.array(self.embedder.embed([query])[0])
        
        # Perform search (hybrid if supported)
        search_results = backend.search(
            query_embedding=query_embedding,
            k=k,
            query_text=query if backend.supports_hybrid_search() else None
        )
        
        # Convert to RetrievalResult objects
        retrieval_results = []
        for doc_idx, score in search_results:
            if doc_idx < len(self.documents):
                document = self.documents[doc_idx]
                retrieval_result = RetrievalResult(
                    document=document,
                    score=float(score),
                    retrieval_method=f"advanced_weaviate_{'hybrid' if backend.supports_hybrid_search() else 'vector'}"
                )
                retrieval_results.append(retrieval_result)
        
        return retrieval_results
    
    def index_documents(self, documents: List[Document]) -> None:
        """
        Index documents in all active backends.
        
        Args:
            documents: List of documents to index
        """
        if not documents:
            raise ValueError("Cannot index empty document list")
        
        # Store documents (parent method)
        super().index_documents(documents)
        
        # Index in additional backends
        for backend_name, backend in self.backends.items():
            if backend_name == "faiss":
                continue  # Already handled by parent
            
            try:
                logger.info(f"Indexing {len(documents)} documents in {backend_name} backend")
                
                # Get embedding dimension
                embedding_dim = len(documents[0].embedding) if documents[0].embedding else 384
                
                # Initialize and index
                backend.initialize_index(embedding_dim)
                backend.add_documents(documents)
                
                logger.info(f"Successfully indexed documents in {backend_name} backend")
                
            except Exception as e:
                logger.error(f"Failed to index documents in {backend_name} backend: {str(e)}")
                if backend_name == self.active_backend_name:
                    raise RuntimeError(f"Failed to index in active backend {backend_name}") from e
    
    def migrate_backend(self, target_backend: str) -> Dict[str, Any]:
        """
        Migrate data from current backend to target backend.
        
        Args:
            target_backend: Name of target backend
            
        Returns:
            Dictionary with migration results
        """
        if target_backend not in self.backends:
            raise ValueError(f"Target backend '{target_backend}' not available")
        
        if target_backend == self.active_backend_name:
            return {"success": True, "message": "Already using target backend"}
        
        logger.info(f"Starting migration from {self.active_backend_name} to {target_backend}")
        
        try:
            if self.active_backend_name == "faiss" and target_backend == "weaviate":
                # FAISS to Weaviate migration
                faiss_backend = self.backends["faiss"]
                weaviate_backend = self.backends["weaviate"]
                
                migrator = FAISSToWeaviateMigrator(
                    faiss_backend=faiss_backend,
                    weaviate_backend=weaviate_backend,
                    validation_enabled=True
                )
                
                result = migrator.migrate(
                    documents=self.documents,
                    preserve_faiss=True  # Keep FAISS as fallback
                )
                
                if result["success"]:
                    self.active_backend_name = target_backend
                    self.advanced_stats["migration_count"] += 1
                    logger.info("Migration completed successfully")
                
                return result
            
            else:
                return {
                    "success": False,
                    "error": f"Migration from {self.active_backend_name} to {target_backend} not implemented"
                }
                
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_backend_status(self) -> Dict[str, Any]:
        """
        Get status of all backends.
        
        Returns:
            Dictionary with backend status information
        """
        status = {
            "active_backend": self.active_backend_name,
            "fallback_backend": self.fallback_backend_name,
            "backends": {}
        }
        
        for backend_name, backend in self.backends.items():
            try:
                health = backend.health_check()
                info = backend.get_backend_info()
                
                status["backends"][backend_name] = {
                    "health": health,
                    "info": info,
                    "is_active": backend_name == self.active_backend_name
                }
            except Exception as e:
                status["backends"][backend_name] = {
                    "error": str(e),
                    "is_active": backend_name == self.active_backend_name
                }
        
        return status
    
    def get_advanced_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics for advanced retriever.
        
        Returns:
            Dictionary with advanced statistics
        """
        base_stats = super().get_retrieval_stats()
        
        return {
            **base_stats,
            "advanced_stats": self.advanced_stats.copy(),
            "backend_status": self.get_backend_status(),
            "enabled_features": self.advanced_config.get_enabled_features(),
            "analytics": {
                "enabled": self.analytics_enabled,
                "query_count": len(self.query_analytics),
                "latest_queries": self.query_analytics[-5:] if self.query_analytics else []
            }
        }
    
    def _check_and_switch_backend(self) -> None:
        """Check backend health and switch if necessary."""
        current_time = time.time()
        
        # Rate limit health checks
        if (current_time - self.advanced_stats["last_health_check"] < 
            self.advanced_config.backends.health_check_interval_seconds):
            return
        
        try:
            active_backend = self.backends[self.active_backend_name]
            health = active_backend.health_check()
            
            if not health.get("is_healthy", True):
                logger.warning(f"Active backend {self.active_backend_name} unhealthy: {health.get('issues', [])}")
                self._consider_backend_switch(None)
            
            self.advanced_stats["last_health_check"] = current_time
            self.advanced_stats["backend_health_checks"] += 1
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
    
    def _consider_backend_switch(self, error: Optional[Exception]) -> None:
        """Consider switching to fallback backend."""
        if not self.fallback_backend_name or self.fallback_backend_name not in self.backends:
            return
        
        try:
            fallback_backend = self.backends[self.fallback_backend_name]
            fallback_health = fallback_backend.health_check()
            
            if fallback_health.get("is_healthy", False):
                logger.info(f"Switching from {self.active_backend_name} to {self.fallback_backend_name}")
                
                # Swap backends
                self.active_backend_name, self.fallback_backend_name = (
                    self.fallback_backend_name, self.active_backend_name
                )
                
                self.advanced_stats["backend_switches"] += 1
                
        except Exception as e:
            logger.error(f"Backend switch consideration failed: {str(e)}")
    
    def _collect_query_start_analytics(self, query: str, k: int) -> None:
        """Collect analytics at query start."""
        analytics_entry = {
            "timestamp": time.time(),
            "query": query,
            "k": k,
            "backend": self.active_backend_name
        }
        
        # Keep only recent entries to prevent memory growth
        max_entries = 1000
        if len(self.query_analytics) >= max_entries:
            self.query_analytics = self.query_analytics[-max_entries//2:]
        
        self.query_analytics.append(analytics_entry)
    
    def _collect_query_completion_analytics(self, 
                                          query: str, 
                                          k: int, 
                                          results: List[RetrievalResult], 
                                          elapsed_time: float,
                                          method: str) -> None:
        """Collect analytics at query completion."""
        if self.query_analytics:
            # Update the latest entry
            latest_entry = self.query_analytics[-1]
            latest_entry.update({
                "completion_time": time.time(),
                "elapsed_time": elapsed_time,
                "results_count": len(results),
                "method": method,
                "success": True
            })
    
    def get_configuration(self) -> Dict[str, Any]:
        """
        Get the current configuration of the advanced retriever.
        
        Returns:
            Dictionary with configuration parameters
        """
        base_config = super().get_configuration()
        
        return {
            **base_config,
            "advanced_config": self.advanced_config.to_dict(),
            "active_backend": self.active_backend_name,
            "fallback_backend": self.fallback_backend_name,
            "available_backends": list(self.backends.keys())
        }