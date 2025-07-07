"""
Hybrid retriever adapter for the modular RAG system.

This module provides an adapter that wraps the existing HybridRetriever
to conform to the Retriever interface, enabling it to be used
in the modular architecture while preserving all existing functionality.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from src.core.interfaces import Document, RetrievalResult, Retriever, VectorStore, Embedder
from src.core.registry import register_component
from shared_utils.retrieval.hybrid_search import HybridRetriever as OriginalHybridRetriever


@register_component("retriever", "hybrid")
class HybridRetriever(Retriever):
    """
    Adapter for existing hybrid retrieval system.
    
    This class wraps the HybridRetriever to provide a Retriever interface
    while maintaining all the performance optimizations and search quality
    of the original implementation.
    
    Features:
    - Dense semantic search with sentence transformers
    - Sparse BM25 keyword matching
    - Reciprocal Rank Fusion (RRF) for result combination
    - Source diversity enhancement
    - Sub-second search on 1000+ document corpus
    - Optimized for technical documentation
    
    Example:
        retriever = HybridRetriever(
            vector_store=faiss_store,
            embedder=sentence_embedder,
            dense_weight=0.7,
            rrf_k=10
        )
        results = retriever.retrieve("What is RISC-V?", k=5)
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedder: Embedder,
        dense_weight: float = 0.7,
        embedding_model: str = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
        use_mps: bool = True,
        bm25_k1: float = 1.2,
        bm25_b: float = 0.75,
        rrf_k: int = 10
    ):
        """
        Initialize the hybrid retriever.
        
        Args:
            vector_store: Vector store for dense retrieval
            embedder: Embedder for query encoding
            dense_weight: Weight for semantic similarity in fusion (default: 0.7)
            embedding_model: Sentence transformer model name
            use_mps: Use Apple Silicon MPS acceleration (default: True)
            bm25_k1: BM25 term frequency saturation parameter (default: 1.2)
            bm25_b: BM25 document length normalization parameter (default: 0.75)
            rrf_k: Reciprocal Rank Fusion constant (default: 10)
        """
        self.vector_store = vector_store
        self.embedder = embedder
        self.dense_weight = dense_weight
        self.sparse_weight = 1.0 - dense_weight
        
        # Initialize the original hybrid retriever
        self.hybrid_retriever = OriginalHybridRetriever(
            dense_weight=dense_weight,
            embedding_model=embedding_model,
            use_mps=use_mps,
            bm25_k1=bm25_k1,
            bm25_b=bm25_b,
            rrf_k=rrf_k
        )
        
        # Track indexed documents for compatibility
        self.indexed_documents: List[Document] = []
        self._chunks_cache: List[Dict] = []
    
    def retrieve(self, query: str, k: int = 5) -> List[RetrievalResult]:
        """
        Retrieve relevant documents using hybrid search.
        
        This method combines dense semantic search and sparse BM25 retrieval
        using Reciprocal Rank Fusion to provide high-quality results for
        technical documentation queries.
        
        Args:
            query: Search query string
            k: Number of results to return (default: 5)
            
        Returns:
            List of retrieval results sorted by relevance score
            
        Raises:
            ValueError: If k <= 0 or query is empty
            RuntimeError: If no documents have been indexed
        """
        if k <= 0:
            raise ValueError("k must be positive")
        
        if not query.strip():
            raise ValueError("Query cannot be empty")
        
        if not self._chunks_cache:
            raise RuntimeError("No documents have been indexed")
        
        try:
            # Use the original hybrid retriever for search
            search_results = self.hybrid_retriever.search(
                query=query,
                top_k=k,
                fusion_method="rrf"
            )
            
            # Convert results to RetrievalResult objects
            retrieval_results = []
            for result in search_results:
                # Extract chunk information
                chunk_idx = result.get('chunk_idx', 0)
                score = result.get('score', 0.0)
                method = result.get('method', 'hybrid')
                
                # Get corresponding document
                if chunk_idx < len(self.indexed_documents):
                    document = self.indexed_documents[chunk_idx]
                    
                    retrieval_result = RetrievalResult(
                        document=document,
                        score=float(score),
                        retrieval_method=f"hybrid_{method}"
                    )
                    retrieval_results.append(retrieval_result)
            
            return retrieval_results
            
        except Exception as e:
            raise RuntimeError(f"Hybrid retrieval failed: {str(e)}") from e
    
    def index_documents(self, documents: List[Document]) -> None:
        """
        Index documents for retrieval.
        
        This method prepares documents for both dense and sparse retrieval
        by converting them to the format expected by the original HybridRetriever.
        
        Args:
            documents: List of documents to index
            
        Raises:
            ValueError: If documents list is empty
        """
        if not documents:
            raise ValueError("Cannot index empty document list")
        
        # Store documents for later retrieval
        self.indexed_documents = documents.copy()
        
        # Convert documents to chunk format expected by original retriever
        chunks = []
        for i, doc in enumerate(documents):
            chunk = {
                "text": doc.content,
                "chunk_id": i,
                # Add metadata from document
                **doc.metadata
            }
            chunks.append(chunk)
        
        # Cache chunks for result mapping
        self._chunks_cache = chunks
        
        # Index documents in the original hybrid retriever
        self.hybrid_retriever.index_documents(chunks)
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the retrieval system.
        
        Returns:
            Dictionary with retrieval statistics and configuration
        """
        stats = {
            "indexed_documents": len(self.indexed_documents),
            "dense_weight": self.dense_weight,
            "sparse_weight": self.sparse_weight,
            "retrieval_type": "hybrid_dense_sparse"
        }
        
        # Get stats from original retriever if available
        try:
            original_stats = self.hybrid_retriever.get_retrieval_stats()
            stats.update(original_stats)
        except Exception:
            # Original retriever might not have this method
            pass
        
        return stats
    
    def supports_batch_queries(self) -> bool:
        """
        Check if this retriever supports batch query processing.
        
        Returns:
            False, as the current implementation processes queries individually
        """
        return False
    
    def get_configuration(self) -> Dict[str, Any]:
        """
        Get the current configuration of the retriever.
        
        Returns:
            Dictionary with configuration parameters
        """
        return {
            "dense_weight": self.dense_weight,
            "sparse_weight": self.sparse_weight,
            "bm25_k1": getattr(self.hybrid_retriever, 'bm25_k1', 1.2),
            "bm25_b": getattr(self.hybrid_retriever, 'bm25_b', 0.75),
            "rrf_k": getattr(self.hybrid_retriever, 'rrf_k', 10),
            "embedding_model": getattr(self.hybrid_retriever, 'embedding_model', "unknown"),
            "use_mps": getattr(self.hybrid_retriever, 'use_mps', True)
        }
    
    def clear_index(self) -> None:
        """
        Clear all indexed documents.
        
        This method resets the retriever to its initial state.
        """
        self.indexed_documents.clear()
        self._chunks_cache.clear()
        
        # Reinitialize the original hybrid retriever
        config = self.get_configuration()
        self.hybrid_retriever = OriginalHybridRetriever(
            dense_weight=config["dense_weight"],
            embedding_model=config["embedding_model"],
            use_mps=config["use_mps"],
            bm25_k1=config["bm25_k1"],
            bm25_b=config["bm25_b"],
            rrf_k=config["rrf_k"]
        )