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

from src.core.interfaces import Retriever, Document, RetrievalResult, Embedder
from .indices.base import VectorIndex
from .indices.faiss_index import FAISSIndex
from .indices.weaviate_index import WeaviateIndex
from .sparse.base import SparseRetriever
from .sparse.bm25_retriever import BM25Retriever
from .fusion.base import FusionStrategy
from .fusion.rrf_fusion import RRFFusion
from .fusion.weighted_fusion import WeightedFusion
from .fusion.graph_enhanced_fusion import GraphEnhancedRRFFusion
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
        else:
            raise ValueError(f"Unknown fusion strategy type: {fusion_type}")
    
    def _create_reranker(self, config: Dict[str, Any]) -> Reranker:
        """Create reranker sub-component."""
        reranker_type = config.get("type", "identity")
        reranker_config = config.get("config", {})
        
        if reranker_type == "semantic":
            return SemanticReranker(reranker_config)
        elif reranker_type == "identity":
            return IdentityReranker(reranker_config)
        elif reranker_type == "neural":
            return NeuralReranker(reranker_config)
        else:
            raise ValueError(f"Unknown reranker type: {reranker_type}")
    
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
            
            # Step 1: Generate query embeddings
            query_embedding = np.array(self.embedder.embed([query])[0])
            
            # Step 2: Dense vector search
            dense_results = self.vector_index.search(query_embedding, k=k*2)  # Get more for fusion
            
            # Step 3: Sparse keyword search
            sparse_results = self.sparse_retriever.search(query, k=k*2)  # Get more for fusion
            
            # Step 4: Fuse results
            fused_results = self.fusion_strategy.fuse_results(dense_results, sparse_results)
            
            # Step 5: Apply reranking if enabled
            if self.reranker.is_enabled() and fused_results:
                # Prepare documents and scores for reranking
                top_candidates = fused_results[:k*2]  # Rerank top candidates
                candidate_documents = [self.documents[idx] for idx, _ in top_candidates]
                candidate_scores = [score for _, score in top_candidates]
                
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
            else:
                # No reranking, use fused results directly
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
            
            # Update performance stats
            elapsed_time = time.time() - start_time
            self.retrieval_stats["total_retrievals"] += 1
            self.retrieval_stats["total_time"] += elapsed_time
            self.retrieval_stats["avg_time"] = (
                self.retrieval_stats["total_time"] / self.retrieval_stats["total_retrievals"]
            )
            self.retrieval_stats["last_retrieval_time"] = elapsed_time
            
            return retrieval_results
            
        except Exception as e:
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