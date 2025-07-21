"""
Modular Unified Retriever for Architecture Compliance.

This module provides a modular implementation of the unified retriever
that decomposes functionality into well-defined sub-components following
the architecture specification.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from src.core.interfaces import Retriever, Document, RetrievalResult, Embedder, HealthStatus

# Forward declaration to avoid circular import
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.core.platform_orchestrator import PlatformOrchestrator
from .indices.base import VectorIndex
from .indices.faiss_index import FAISSIndex
from .indices.weaviate_index import WeaviateIndex
from .sparse.base import SparseRetriever
from .sparse.bm25_retriever import BM25Retriever
from .fusion.base import FusionStrategy
from .fusion.rrf_fusion import RRFFusion
from .fusion.weighted_fusion import WeightedFusion
from .fusion.graph_enhanced_fusion import GraphEnhancedRRFFusion
from .fusion.score_aware_fusion import ScoreAwareFusion
from .rerankers.base import Reranker
from .rerankers.semantic_reranker import SemanticReranker
from .rerankers.identity_reranker import IdentityReranker
from .rerankers.neural_reranker import NeuralReranker

logger = logging.getLogger(__name__)


class ModularUnifiedRetriever(Retriever):
    """
    Modular unified retriever with pluggable sub-components.
    
    This implementation follows the architecture specification by decomposing
    the retrieval functionality into four distinct sub-components:
    - Vector Index: Handles dense semantic search
    - Sparse Retriever: Handles keyword-based search
    - Fusion Strategy: Combines dense and sparse results
    - Reranker: Improves result relevance
    
    Each sub-component can be independently configured and tested,
    improving modularity and maintainability.
    
    Features:
    - Architecture-compliant modular design
    - Configurable sub-components
    - Component factory integration
    - Performance monitoring
    - Backward compatibility with UnifiedRetriever
    - Enhanced logging and debugging
    
    Example:
        config = {
            "vector_index": {
                "type": "faiss",
                "config": {"index_type": "IndexFlatIP", "normalize_embeddings": True}
            },
            "sparse": {
                "type": "bm25",
                "config": {"k1": 1.2, "b": 0.75}
            },
            "fusion": {
                "type": "rrf",
                "config": {"k": 60, "weights": {"dense": 0.7, "sparse": 0.3}}
            },
            "reranker": {
                "type": "semantic",
                "config": {"enabled": True, "model": "cross-encoder/ms-marco-MiniLM-L-6-v2"}
            }
        }
        retriever = ModularUnifiedRetriever(config, embedder)
    """
    
    def __init__(self, config: Dict[str, Any], embedder: Embedder):
        """
        Initialize the modular unified retriever.
        
        Args:
            config: Configuration dictionary with sub-component specifications
            embedder: Embedder component for query encoding
        """
        self.config = config
        self.embedder = embedder
        self.documents: List[Document] = []
        
        # Composite filtering configuration (NEW)
        composite_config = config.get("composite_filtering", {})
        self.composite_filtering_enabled = composite_config.get("enabled", False)
        self.fusion_weight = composite_config.get("fusion_weight", 0.7)
        self.semantic_weight = composite_config.get("semantic_weight", 0.3)
        self.min_composite_score = composite_config.get("min_composite_score", 0.4)
        self.max_candidates_multiplier = composite_config.get("max_candidates", 15) / 10.0  # Convert to multiplier (1.5x)
        
        # Legacy semantic gap detection configuration (DEPRECATED)
        self.min_semantic_alignment = config.get("min_semantic_alignment", 0.3)
        
        # Initialize sub-components
        self.vector_index = self._create_vector_index(config.get("vector_index", {}))
        self.sparse_retriever = self._create_sparse_retriever(config.get("sparse", {}))
        self.fusion_strategy = self._create_fusion_strategy(config.get("fusion", {}))
        self.reranker = self._create_reranker(config.get("reranker", {}))
        
        # Performance tracking
        self.retrieval_stats = {
            "total_retrievals": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
            "last_retrieval_time": 0.0
        }
        
        # Backend management (for multi-backend performance testing)
        self.active_backend_name = "faiss"  # Default backend
        self.available_backends = ["faiss", "weaviate"]
        self.backend_switch_count = 0
        
        # Platform services (initialized via initialize_services)
        self.platform: Optional['PlatformOrchestrator'] = None
        
        logger.info("ModularUnifiedRetriever initialized with all sub-components")
    
    def _create_vector_index(self, config: Dict[str, Any]) -> VectorIndex:
        """Create vector index sub-component."""
        index_type = config.get("type", "faiss")
        index_config = config.get("config", {})
        
        if index_type == "faiss":
            return FAISSIndex(index_config)
        elif index_type == "weaviate":
            return WeaviateIndex(index_config)
        else:
            raise ValueError(f"Unknown vector index type: {index_type}")
    
    def _create_sparse_retriever(self, config: Dict[str, Any]) -> SparseRetriever:
        """Create sparse retriever sub-component."""
        retriever_type = config.get("type", "bm25")
        retriever_config = config.get("config", {})
        
        if retriever_type == "bm25":
            return BM25Retriever(retriever_config)
        else:
            raise ValueError(f"Unknown sparse retriever type: {retriever_type}")
    
    def _create_fusion_strategy(self, config: Dict[str, Any]) -> FusionStrategy:
        """Create fusion strategy sub-component."""
        fusion_type = config.get("type", "rrf")
        fusion_config = config.get("config", {})
        
        if fusion_type == "rrf":
            return RRFFusion(fusion_config)
        elif fusion_type == "weighted":
            return WeightedFusion(fusion_config)
        elif fusion_type == "graph_enhanced_rrf":
            return GraphEnhancedRRFFusion(fusion_config)
        elif fusion_type == "score_aware":
            return ScoreAwareFusion(fusion_config)
        else:
            raise ValueError(f"Unknown fusion strategy type: {fusion_type}. Available options: rrf, weighted, graph_enhanced_rrf, score_aware")
    
    def _create_reranker(self, config: Dict[str, Any]) -> Reranker:
        """Create reranker sub-component."""
        reranker_type = config.get("type", "identity")
        reranker_config = config.get("config", {})
        
        logger.info(f"🔧 Creating reranker: type={reranker_type}, config keys={list(reranker_config.keys())}")
        
        if reranker_type == "semantic":
            reranker = SemanticReranker(reranker_config)
        elif reranker_type == "identity":
            reranker = IdentityReranker(reranker_config)
        elif reranker_type == "neural":
            try:
                reranker = NeuralReranker(reranker_config)
                logger.info(f"✅ NeuralReranker created successfully: enabled={reranker.enabled}, initialized={reranker._initialized}")
            except Exception as e:
                logger.error(f"❌ Failed to create NeuralReranker: {e}")
                logger.warning("Falling back to IdentityReranker")
                reranker = IdentityReranker({"enabled": True})
        else:
            raise ValueError(f"Unknown reranker type: {reranker_type}")
        
        return reranker
    
    def retrieve(self, query: str, k: int = 5) -> List[RetrievalResult]:
        """
        Retrieve relevant documents using modular hybrid search.
        
        This method orchestrates the complete retrieval pipeline:
        1. Generate query embeddings
        2. Perform dense vector search
        3. Perform sparse keyword search
        4. Fuse results using configured strategy
        5. Apply reranking if enabled
        
        Args:
            query: Search query string
            k: Number of results to return
            
        Returns:
            List of retrieval results sorted by relevance score
        """
        start_time = time.time()
        
        try:
            # Validation
            if k <= 0:
                raise ValueError("k must be positive")
            if not query.strip():
                raise ValueError("Query cannot be empty")
            if not self.documents:
                raise RuntimeError("No documents have been indexed")
            
            logger.info(f"🔍 MODULAR RETRIEVER: Starting retrieval for query: '{query}' (k={k})")
            logger.info(f"📚 CORPUS STATUS: {len(self.documents)} documents indexed")
            
            # Step 1: Generate query embeddings
            query_embedding = np.array(self.embedder.embed([query])[0])
            logger.info(f"🔤 QUERY EMBEDDING: Generated {query_embedding.shape} dimensional vector")
            
            # Step 2: Dense vector search (with efficiency optimization)
            candidate_multiplier = int(self.max_candidates_multiplier * k) if self.composite_filtering_enabled else k*2
            logger.info(f"🎯 DENSE SEARCH: Searching for top {candidate_multiplier} candidates")
            dense_results = self.vector_index.search(query_embedding, k=candidate_multiplier)
            logger.info(f"✅ DENSE RESULTS: {len(dense_results)} documents found")
            
            # Log top dense results with scores
            if dense_results:
                logger.info(f"📊 TOP DENSE SCORES:")
                for i, (doc_idx, score) in enumerate(dense_results[:3]):
                    if doc_idx < len(self.documents):
                        doc_title = self.documents[doc_idx].metadata.get('title', f'doc_{doc_idx}')[:50]
                        logger.info(f"   {i+1}. [{doc_idx}] {doc_title}... → {score:.4f}")
            else:
                logger.warning(f"⚠️ DENSE SEARCH: No results found!")
            
            # Step 3: Sparse keyword search (with efficiency optimization)
            logger.info(f"🔎 SPARSE SEARCH: BM25 keyword search for '{query}' (k={candidate_multiplier})")
            sparse_results = self.sparse_retriever.search(query, k=candidate_multiplier)
            logger.info(f"✅ SPARSE RESULTS: {len(sparse_results)} documents found")
            
            # Log top sparse results with scores  
            if sparse_results:
                logger.info(f"📊 TOP SPARSE SCORES:")
                for i, (doc_idx, score) in enumerate(sparse_results[:3]):
                    if doc_idx < len(self.documents):
                        doc_title = self.documents[doc_idx].metadata.get('title', f'doc_{doc_idx}')[:50]
                        logger.info(f"   {i+1}. [{doc_idx}] {doc_title}... → {score:.4f}")
            else:
                logger.warning(f"⚠️ SPARSE SEARCH: No results found!")
            
            # Step 3.5: Set documents and query for graph enhancement (if supported)
            if hasattr(self.fusion_strategy, 'set_documents_and_query'):
                self.fusion_strategy.set_documents_and_query(self.documents, query)
            
            # Step 4: Fuse results
            fusion_name = self.fusion_strategy.__class__.__name__
            logger.info(f"🔄 FUSION STRATEGY: Using {fusion_name} to combine results")
            fused_results = self.fusion_strategy.fuse_results(dense_results, sparse_results)
            logger.info(f"✅ FUSION RESULTS: {len(fused_results)} documents after fusion")
            
            # Log top fused results with scores
            if fused_results:
                logger.info(f"📊 TOP FUSED SCORES:")
                for i, (doc_idx, score) in enumerate(fused_results[:5]):
                    if doc_idx < len(self.documents):
                        doc_title = self.documents[doc_idx].metadata.get('title', f'doc_{doc_idx}')[:50]
                        logger.info(f"   {i+1}. [{doc_idx}] {doc_title}... → {score:.4f}")
            else:
                logger.warning(f"⚠️ FUSION: No results after fusion!")
            
            # Step 4.5: Composite filtering (NEW) or semantic gap detection (LEGACY)
            if self.composite_filtering_enabled:
                # NEW: Individual document composite scoring
                filtered_results = self._calculate_composite_scores(query_embedding, fused_results)
                if not filtered_results:
                    logger.info("Composite filtering: No documents passed quality threshold")
                    return []
                fused_results = filtered_results  # Use filtered results for reranking
            else:
                # LEGACY: Global semantic gap detection (DEPRECATED)
                if fused_results and self.min_semantic_alignment > 0:
                    semantic_alignment = self._calculate_semantic_alignment(query_embedding, fused_results[:5])
                    if semantic_alignment < self.min_semantic_alignment:
                        logger.info(f"Query-document semantic alignment too low: {semantic_alignment:.3f} < {self.min_semantic_alignment}")
                        return []  # No semantically relevant documents found
            
            # Step 5: Apply reranking if enabled
            if self.reranker.is_enabled() and fused_results:
                reranker_name = self.reranker.__class__.__name__
                logger.info(f"🧠 RERANKING: Using {reranker_name} to improve relevance")
                
                # Prepare documents and scores for reranking
                top_candidates = fused_results[:k*2]  # Rerank top candidates
                candidate_documents = [self.documents[idx] for idx, _ in top_candidates]
                candidate_scores = [score for _, score in top_candidates]
                
                logger.info(f"🔄 RERANKING: Processing {len(top_candidates)} candidates")
                reranked_results = self.reranker.rerank(query, candidate_documents, candidate_scores)
                
                # Update final results with reranked scores
                final_results = []
                for local_idx, reranked_score in reranked_results:
                    if local_idx < len(top_candidates):
                        original_idx = top_candidates[local_idx][0]
                        final_results.append((original_idx, reranked_score))
                
                # Add remaining documents that weren't reranked
                reranked_indices = {top_candidates[local_idx][0] for local_idx, _ in reranked_results 
                                   if local_idx < len(top_candidates)}
                for doc_idx, score in fused_results:
                    if doc_idx not in reranked_indices:
                        final_results.append((doc_idx, score))
                
                # Sort by final score and limit to k
                final_results.sort(key=lambda x: x[1], reverse=True)
                final_results = final_results[:k]
                
                logger.info(f"✅ RERANKING: Final {len(final_results)} results after reranking")
            else:
                # No reranking, use fused results directly
                logger.info(f"⏭️ RERANKING: Skipped (reranker disabled or no results)")
                final_results = fused_results[:k]
            
            # Convert to RetrievalResult objects
            retrieval_results = []
            for doc_idx, score in final_results:
                if doc_idx < len(self.documents):
                    document = self.documents[doc_idx]
                    retrieval_result = RetrievalResult(
                        document=document,
                        score=float(score),
                        retrieval_method="modular_unified_hybrid"
                    )
                    retrieval_results.append(retrieval_result)
            
            # Log final results summary
            logger.info(f"🎯 FINAL RETRIEVAL RESULTS: {len(retrieval_results)} documents")
            if retrieval_results:
                logger.info(f"📊 FINAL RANKING:")
                for i, result in enumerate(retrieval_results):
                    doc_title = result.document.metadata.get('title', f'doc_{result.document.content[:30]}')[:50]
                    logger.info(f"   {i+1}. {doc_title}... → {result.score:.4f}")
            else:
                logger.warning(f"❌ NO RESULTS: Query '{query}' returned no relevant documents!")
            
            # Update performance stats
            elapsed_time = time.time() - start_time
            self.retrieval_stats["total_retrievals"] += 1
            self.retrieval_stats["total_time"] += elapsed_time
            self.retrieval_stats["avg_time"] = (
                self.retrieval_stats["total_time"] / self.retrieval_stats["total_retrievals"]
            )
            self.retrieval_stats["last_retrieval_time"] = elapsed_time
            
            # Log performance summary
            logger.info(f"⚡ RETRIEVAL PERFORMANCE: {elapsed_time*1000:.1f}ms total, {len(retrieval_results)}/{k} results")
            logger.info(f"🏁 RETRIEVAL COMPLETE: Query '{query}' processed successfully")
            
            # Track performance using platform services
            if self.platform:
                self.platform.track_component_performance(
                    self, 
                    "document_retrieval", 
                    {
                        "success": True,
                        "retrieval_time": elapsed_time,
                        "query": query,
                        "results_count": len(retrieval_results),
                        "k_requested": k,
                        "indexed_documents": len(self.documents)
                    }
                )
            
            return retrieval_results
            
        except Exception as e:
            # Track failure using platform services
            if self.platform:
                elapsed_time = time.time() - start_time
                self.platform.track_component_performance(
                    self, 
                    "document_retrieval", 
                    {
                        "success": False,
                        "retrieval_time": elapsed_time,
                        "query": query,
                        "k_requested": k,
                        "indexed_documents": len(self.documents),
                        "error": str(e)
                    }
                )
            
            logger.error(f"Modular retrieval failed: {str(e)}")
            raise RuntimeError(f"Modular retrieval failed: {str(e)}") from e
    
    def index_documents(self, documents: List[Document]) -> None:
        """
        Index documents in all sub-components.
        
        Args:
            documents: List of documents to index
        """
        if not documents:
            raise ValueError("Cannot index empty document list")
        
        # Store documents (extend existing instead of replacing)
        if not hasattr(self, 'documents') or self.documents is None:
            self.documents = []
        self.documents.extend(documents)
        
        # Get embedding dimension from first document
        if documents[0].embedding is not None:
            embedding_dim = len(documents[0].embedding)
        else:
            raise ValueError("Documents must have embeddings before indexing")
        
        # Initialize index only if not already initialized
        if not hasattr(self.vector_index, 'index') or self.vector_index.index is None:
            self.vector_index.initialize_index(embedding_dim)
        
        # Add documents to vector index
        self.vector_index.add_documents(documents)
        
        # Index in sparse retriever (this needs fixing too)
        self.sparse_retriever.index_documents(documents)
        
        logger.info(f"Indexed {len(documents)} documents in all sub-components")
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the modular retrieval system.
        
        Returns:
            Dictionary with retrieval statistics and sub-component information
        """
        stats = {
            "component_type": "modular_unified_retriever",
            "indexed_documents": len(self.documents),
            "retrieval_stats": self.retrieval_stats.copy(),
            "sub_components": {
                "vector_index": self.vector_index.get_index_info(),
                "sparse_retriever": self.sparse_retriever.get_stats(),
                "fusion_strategy": self.fusion_strategy.get_strategy_info(),
                "reranker": self.reranker.get_reranker_info()
            }
        }
        
        return stats
    
    def get_component_info(self) -> Dict[str, Any]:
        """
        Get detailed information about all sub-components.
        
        Returns:
            Dictionary with component details for logging
        """
        return {
            "vector_index": self.vector_index.get_component_info(),
            "sparse_retriever": self.sparse_retriever.get_component_info(),
            "fusion_strategy": self.fusion_strategy.get_component_info(),
            "reranker": self.reranker.get_component_info()
        }
    
    def supports_batch_queries(self) -> bool:
        """
        Check if this retriever supports batch query processing.
        
        Returns:
            False, as the current implementation processes queries individually
        """
        return False
    
    def get_configuration(self) -> Dict[str, Any]:
        """
        Get the current configuration of the modular retriever.
        
        Returns:
            Dictionary with configuration parameters
        """
        return {
            "vector_index": {
                "type": "faiss",
                "config": self.vector_index.get_index_info()
            },
            "sparse": {
                "type": "bm25",
                "config": self.sparse_retriever.get_stats()
            },
            "fusion": {
                "type": type(self.fusion_strategy).__name__.lower().replace("fusion", ""),
                "config": self.fusion_strategy.get_strategy_info()
            },
            "reranker": {
                "type": type(self.reranker).__name__.lower().replace("reranker", ""),
                "config": self.reranker.get_reranker_info()
            }
        }
    
    def clear_index(self) -> None:
        """
        Clear all indexed documents and reset all sub-components.
        """
        self.documents.clear()
        self.vector_index.clear()
        self.sparse_retriever.clear()
        
        # Reset performance stats
        self.retrieval_stats = {
            "total_retrievals": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
            "last_retrieval_time": 0.0
        }
        
        logger.info("Cleared all documents from modular retriever")
    
    def _consider_backend_switch(self, error: Exception) -> None:
        """
        Consider switching to a different backend due to an error.
        
        This method is used for performance testing of backend switching.
        In a real implementation, this would switch to a fallback backend.
        
        Args:
            error: The exception that triggered the switch consideration
        """
        logger.warning(f"Backend switch consideration triggered by: {error}")
        
        # Simulate backend switching logic
        if self.active_backend_name == "faiss":
            self.active_backend_name = "weaviate"
        else:
            self.active_backend_name = "faiss"
        
        self.backend_switch_count += 1
        logger.info(f"Switched to backend: {self.active_backend_name} (switch count: {self.backend_switch_count})")
    
    # Standard ComponentBase interface implementation
    def initialize_services(self, platform: 'PlatformOrchestrator') -> None:
        """Initialize platform services for the component.
        
        Args:
            platform: PlatformOrchestrator instance providing services
        """
        self.platform = platform
        logger.info("ModularUnifiedRetriever initialized with platform services")

    def get_health_status(self) -> HealthStatus:
        """Get the current health status of the component.
        
        Returns:
            HealthStatus object with component health information
        """
        if self.platform:
            return self.platform.check_component_health(self)
        
        # Fallback if platform services not initialized
        is_healthy = True
        issues = []
        
        # Check sub-components
        if not hasattr(self.vector_index, 'get_index_info'):
            is_healthy = False
            issues.append("Vector index not properly initialized")
        
        if not hasattr(self.sparse_retriever, 'get_stats'):
            is_healthy = False
            issues.append("Sparse retriever not properly initialized")
        
        if not hasattr(self.fusion_strategy, 'get_strategy_info'):
            is_healthy = False
            issues.append("Fusion strategy not properly initialized")
        
        if not hasattr(self.reranker, 'get_reranker_info'):
            is_healthy = False
            issues.append("Reranker not properly initialized")
        
        return HealthStatus(
            is_healthy=is_healthy,
            issues=issues,
            metrics={
                "indexed_documents": len(self.documents),
                "retrieval_stats": self.retrieval_stats,
                "sub_components": self.get_component_info()
            },
            component_name=self.__class__.__name__
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get component-specific metrics.
        
        Returns:
            Dictionary containing component metrics
        """
        if self.platform:
            try:
                component_metrics = self.platform.analytics_service.collect_component_metrics(self)
                return {
                    "component_name": component_metrics.component_name,
                    "component_type": component_metrics.component_type,
                    "success_count": component_metrics.success_count,
                    "error_count": component_metrics.error_count,
                    "resource_usage": component_metrics.resource_usage,
                    "performance_metrics": component_metrics.performance_metrics,
                    "timestamp": component_metrics.timestamp
                }
            except Exception as e:
                # Fallback if platform service fails
                pass
        
        # Fallback if platform services not initialized
        return {
            "indexed_documents": len(self.documents),
            "retrieval_stats": self.retrieval_stats,
            "sub_components": self.get_component_info(),
            "configuration": self.get_configuration()
        }

    def get_capabilities(self) -> List[str]:
        """Get list of component capabilities.
        
        Returns:
            List of capability strings
        """
        capabilities = [
            "hybrid_retrieval",
            "modular_architecture",
            "dense_search",
            "sparse_search",
            "result_fusion",
            "reranking"
        ]
        
        # Add vector index capabilities
        if hasattr(self.vector_index, 'get_capabilities'):
            capabilities.extend([f"vector_{cap}" for cap in self.vector_index.get_capabilities()])
        
        # Add sparse retriever capabilities
        if hasattr(self.sparse_retriever, 'get_capabilities'):
            capabilities.extend([f"sparse_{cap}" for cap in self.sparse_retriever.get_capabilities()])
        
        # Add fusion strategy capabilities
        if hasattr(self.fusion_strategy, 'get_capabilities'):
            capabilities.extend([f"fusion_{cap}" for cap in self.fusion_strategy.get_capabilities()])
        
        # Add reranker capabilities
        if hasattr(self.reranker, 'get_capabilities'):
            capabilities.extend([f"reranker_{cap}" for cap in self.reranker.get_capabilities()])
        
        return capabilities
    
    def get_document_count(self) -> int:
        """Get the number of documents in the retriever."""
        return len(self.documents)
    
    def get_sub_component_performance(self) -> Dict[str, Any]:
        """
        Get performance information for each sub-component.
        
        Returns:
            Dictionary with performance metrics
        """
        performance = {
            "vector_index": {
                "document_count": self.vector_index.get_document_count(),
                "is_trained": self.vector_index.is_trained()
            },
            "sparse_retriever": {
                "document_count": self.sparse_retriever.get_document_count(),
                "stats": self.sparse_retriever.get_stats()
            },
            "fusion_strategy": {
                "info": self.fusion_strategy.get_strategy_info()
            },
            "reranker": {
                "enabled": self.reranker.is_enabled(),
                "info": self.reranker.get_reranker_info()
            }
        }
        
        return performance
    
    def debug_retrieval(self, query: str, k: int = 5) -> Dict[str, Any]:
        """
        Perform retrieval with detailed debugging information.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            Dictionary with step-by-step retrieval information
        """
        debug_info = {
            "query": query,
            "k": k,
            "steps": {}
        }
        
        try:
            # Step 1: Query embedding
            query_embedding = self.embedder.embed_query(query)
            debug_info["steps"]["embedding"] = {
                "embedding_dim": len(query_embedding),
                "embedding_norm": float(np.linalg.norm(query_embedding))
            }
            
            # Step 2: Dense search
            dense_results = self.vector_index.search(query_embedding, k=k*2)
            debug_info["steps"]["dense_search"] = {
                "results_count": len(dense_results),
                "top_scores": [score for _, score in dense_results[:5]]
            }
            
            # Step 3: Sparse search
            sparse_results = self.sparse_retriever.search(query, k=k*2)
            debug_info["steps"]["sparse_search"] = {
                "results_count": len(sparse_results),
                "top_scores": [score for _, score in sparse_results[:5]]
            }
            
            # Step 3.5: Set documents and query for graph enhancement (if supported)
            if hasattr(self.fusion_strategy, 'set_documents_and_query'):
                self.fusion_strategy.set_documents_and_query(self.documents, query)
            
            # Step 4: Fusion
            fused_results = self.fusion_strategy.fuse_results(dense_results, sparse_results)
            debug_info["steps"]["fusion"] = {
                "results_count": len(fused_results),
                "top_scores": [score for _, score in fused_results[:5]],
                "fusion_type": type(self.fusion_strategy).__name__
            }
            
            # Step 5: Reranking
            if self.reranker.is_enabled():
                top_candidates = fused_results[:k*2]
                candidate_documents = [self.documents[idx] for idx, _ in top_candidates]
                candidate_scores = [score for _, score in top_candidates]
                
                reranked_results = self.reranker.rerank(query, candidate_documents, candidate_scores)
                debug_info["steps"]["reranking"] = {
                    "enabled": True,
                    "candidates_count": len(candidate_documents),
                    "reranked_count": len(reranked_results),
                    "top_reranked_scores": [score for _, score in reranked_results[:5]]
                }
            else:
                debug_info["steps"]["reranking"] = {"enabled": False}
            
        except Exception as e:
            debug_info["error"] = str(e)
        
        return debug_info
    
    def _calculate_composite_scores(self, query_embedding: np.ndarray, fused_results: List[Tuple[int, float]]) -> List[Tuple[int, float]]:
        """
        Calculate composite scores for individual documents combining fusion scores and semantic similarity.
        
        This method replaces the global semantic gap detection with per-document quality assessment.
        Each document gets a composite score: α * fusion_score + β * semantic_similarity
        Only documents above the composite threshold are included.
        
        Args:
            query_embedding: Query embedding vector
            fused_results: List of (document_index, fusion_score) from fusion strategy
            
        Returns:
            List of (document_index, composite_score) for documents that pass the threshold
        """
        if not fused_results:
            return []
        
        try:
            # Normalize fusion scores to 0-1 range for fair combination
            fusion_scores = [score for _, score in fused_results]
            if len(set(fusion_scores)) > 1:  # Only normalize if there's variation
                min_score, max_score = min(fusion_scores), max(fusion_scores)
                score_range = max_score - min_score
                if score_range > 0:
                    normalized_fusion = [(score - min_score) / score_range for score in fusion_scores]
                else:
                    normalized_fusion = [1.0] * len(fusion_scores)  # All scores identical
            else:
                normalized_fusion = [1.0] * len(fusion_scores)  # All scores identical
            
            # Get document texts and embeddings
            doc_indices = [doc_idx for doc_idx, _ in fused_results]
            documents = [self.documents[idx] for idx in doc_indices if idx < len(self.documents)]
            
            if not documents:
                return []
            
            doc_texts = [doc.content for doc in documents]
            doc_embeddings = self.embedder.embed(doc_texts)
            
            # Calculate composite scores for each document
            composite_results = []
            for i, (doc_idx, original_fusion_score) in enumerate(fused_results):
                if i >= len(doc_embeddings) or doc_idx >= len(self.documents):
                    continue
                    
                # Calculate semantic similarity
                doc_emb_array = np.array(doc_embeddings[i])
                query_norm = query_embedding / np.linalg.norm(query_embedding)
                doc_norm = doc_emb_array / np.linalg.norm(doc_emb_array)
                semantic_similarity = np.dot(query_norm, doc_norm)
                
                # Calculate composite score
                normalized_fusion_score = normalized_fusion[i]
                composite_score = (self.fusion_weight * normalized_fusion_score + 
                                 self.semantic_weight * semantic_similarity)
                
                # Apply threshold filter
                if composite_score >= self.min_composite_score:
                    composite_results.append((doc_idx, composite_score))
                
                # Debug logging for first few documents
                if i < 3:
                    logger.info(f"COMPOSITE DEBUG - Doc {i+1}: fusion={original_fusion_score:.3f}, "
                               f"norm_fusion={normalized_fusion_score:.3f}, semantic={semantic_similarity:.3f}, "
                               f"composite={composite_score:.3f}, threshold={self.min_composite_score}")
            
            # Sort by composite score (descending) and return
            composite_results.sort(key=lambda x: x[1], reverse=True)
            
            logger.info(f"COMPOSITE FILTERING - {len(fused_results)} input → {len(composite_results)} passed threshold")
            return composite_results
            
        except Exception as e:
            logger.warning(f"Error in composite scoring: {e}")
            # Fallback to original fusion results
            return fused_results
    
    def _calculate_semantic_alignment(self, query_embedding: np.ndarray, fused_results: List[Tuple[int, float]]) -> float:
        """
        Calculate semantic alignment between query and top retrieved documents.
        
        Args:
            query_embedding: Query embedding vector
            fused_results: List of (document_index, score) from fusion
            
        Returns:
            Average cosine similarity between query and top documents
        """
        if not fused_results:
            return 0.0
        
        try:
            # Get embeddings for top documents
            top_doc_indices = [doc_idx for doc_idx, _ in fused_results]
            top_documents = [self.documents[idx] for idx in top_doc_indices if idx < len(self.documents)]
            
            if not top_documents:
                return 0.0
            
            # Extract text content for embedding
            doc_texts = [doc.content for doc in top_documents]
            
            # Get document embeddings
            doc_embeddings = self.embedder.embed(doc_texts)
            
            # Calculate cosine similarities
            similarities = []
            for i, doc_embedding in enumerate(doc_embeddings):
                doc_emb_array = np.array(doc_embedding)
                # Normalize vectors for cosine similarity
                query_norm = query_embedding / np.linalg.norm(query_embedding)
                doc_norm = doc_emb_array / np.linalg.norm(doc_emb_array)
                similarity = np.dot(query_norm, doc_norm)
                similarities.append(similarity)
                
                # Debug: Log individual document similarities for investigation
                if i < 3:  # Only log first 3 docs to avoid spam
                    doc_preview = doc_texts[i][:100] + "..." if len(doc_texts[i]) > 100 else doc_texts[i]
                    logger.debug(f"Doc {i+1} similarity: {similarity:.3f} - {doc_preview}")
            
            # Return average similarity
            avg_similarity = np.mean(similarities) if similarities else 0.0
            logger.debug(f"Semantic alignment: {len(similarities)} docs, similarities={[f'{s:.3f}' for s in similarities[:5]]}, avg={avg_similarity:.3f}")
            return float(avg_similarity)
            
        except Exception as e:
            logger.warning(f"Error calculating semantic alignment: {e}")
            return 0.0  # Conservative fallback