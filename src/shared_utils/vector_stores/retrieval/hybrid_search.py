"""
Hybrid retrieval combining dense semantic search with sparse BM25 keyword matching.
Uses Reciprocal Rank Fusion (RRF) to combine results from both approaches.
"""

from typing import List, Dict, Tuple, Optional
import numpy as np
from pathlib import Path
import sys

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent / "project-1-technical-rag"
sys.path.append(str(project_root))

from src.sparse_retrieval import BM25SparseRetriever
from src.fusion import reciprocal_rank_fusion, adaptive_fusion
from shared_utils.embeddings.generator import generate_embeddings
import faiss


class HybridRetriever:
    """
    Hybrid retrieval system combining dense semantic search with sparse BM25.
    
    Optimized for technical documentation where both semantic similarity
    and exact keyword matching are important for retrieval quality.
    
    Performance: Sub-second search on 1000+ document corpus
    """
    
    def __init__(
        self,
        dense_weight: float = 0.7,
        embedding_model: str = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
        use_mps: bool = True,
        bm25_k1: float = 1.2,
        bm25_b: float = 0.75,
        rrf_k: int = 10
    ):
        """
        Initialize hybrid retriever with dense and sparse components.
        
        Args:
            dense_weight: Weight for semantic similarity in fusion (0.7 default)
            embedding_model: Sentence transformer model name
            use_mps: Use Apple Silicon MPS acceleration for embeddings
            bm25_k1: BM25 term frequency saturation parameter
            bm25_b: BM25 document length normalization parameter
            rrf_k: Reciprocal Rank Fusion constant (1=strong rank preference, 2=moderate)
            
        Raises:
            ValueError: If parameters are invalid
        """
        if not 0 <= dense_weight <= 1:
            raise ValueError("dense_weight must be between 0 and 1")
            
        self.dense_weight = dense_weight
        self.embedding_model = embedding_model
        self.use_mps = use_mps
        self.rrf_k = rrf_k
        
        # Initialize sparse retriever
        self.sparse_retriever = BM25SparseRetriever(k1=bm25_k1, b=bm25_b)
        
        # Dense retrieval components (initialized on first index)
        self.dense_index: Optional[faiss.Index] = None
        self.chunks: List[Dict] = []
        self.embeddings: Optional[np.ndarray] = None
        
    def index_documents(self, chunks: List[Dict]) -> None:
        """
        Index documents for both dense and sparse retrieval.
        
        Args:
            chunks: List of chunk dictionaries with 'text' field
            
        Raises:
            ValueError: If chunks is empty or malformed
            
        Performance: ~100 chunks/second for complete indexing
        """
        if not chunks:
            raise ValueError("Cannot index empty chunk list")
            
        print(f"Indexing {len(chunks)} chunks for hybrid retrieval...")
        
        # Store chunks for retrieval
        self.chunks = chunks
        
        # Index for sparse retrieval
        print("Building BM25 sparse index...")
        self.sparse_retriever.index_documents(chunks)
        
        # Index for dense retrieval
        print("Building dense semantic index...")
        texts = [chunk['text'] for chunk in chunks]
        
        # Generate embeddings
        self.embeddings = generate_embeddings(
            texts, 
            model_name=self.embedding_model,
            use_mps=self.use_mps
        )
        
        # Create FAISS index
        embedding_dim = self.embeddings.shape[1]
        self.dense_index = faiss.IndexFlatIP(embedding_dim)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(self.embeddings)
        self.dense_index.add(self.embeddings)
        
        print(f"Hybrid indexing complete: {len(chunks)} chunks ready for search")
        
    def search(
        self, 
        query: str, 
        top_k: int = 10,
        dense_top_k: Optional[int] = None,
        sparse_top_k: Optional[int] = None
    ) -> List[Tuple[int, float, Dict]]:
        """
        Hybrid search combining dense and sparse retrieval with RRF.
        
        Args:
            query: Search query string
            top_k: Final number of results to return
            dense_top_k: Results from dense search (default: 2*top_k)
            sparse_top_k: Results from sparse search (default: 2*top_k)
            
        Returns:
            List of (chunk_index, rrf_score, chunk_dict) tuples
            
        Raises:
            ValueError: If not indexed or invalid parameters
            
        Performance: <200ms for 1000+ document corpus
        """
        if self.dense_index is None:
            raise ValueError("Must call index_documents() before searching")
            
        if not query.strip():
            return []
            
        if top_k <= 0:
            raise ValueError("top_k must be positive")
            
        # Set default intermediate result counts
        if dense_top_k is None:
            dense_top_k = min(2 * top_k, len(self.chunks))
        if sparse_top_k is None:
            sparse_top_k = min(2 * top_k, len(self.chunks))
            
        # Dense semantic search
        dense_results = self._dense_search(query, dense_top_k)
        
        # Sparse BM25 search  
        sparse_results = self.sparse_retriever.search(query, sparse_top_k)
        
        # Combine using Adaptive Fusion (better for small result sets)
        fused_results = adaptive_fusion(
            dense_results=dense_results,
            sparse_results=sparse_results,
            dense_weight=self.dense_weight,
            result_size=top_k
        )
        
        # Prepare final results with chunk content and apply source diversity
        final_results = []
        for chunk_idx, rrf_score in fused_results:
            chunk_dict = self.chunks[chunk_idx]
            final_results.append((chunk_idx, rrf_score, chunk_dict))
        
        # Apply source diversity enhancement
        diverse_results = self._enhance_source_diversity(final_results, top_k)
            
        return diverse_results
        
    def _dense_search(self, query: str, top_k: int) -> List[Tuple[int, float]]:
        """
        Perform dense semantic search using FAISS.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of (chunk_index, similarity_score) tuples
        """
        # Generate query embedding
        query_embedding = generate_embeddings(
            [query],
            model_name=self.embedding_model, 
            use_mps=self.use_mps
        )
        
        # Normalize for cosine similarity
        faiss.normalize_L2(query_embedding)
        
        # Search dense index
        similarities, indices = self.dense_index.search(query_embedding, top_k)
        
        # Convert to required format
        results = [
            (int(indices[0][i]), float(similarities[0][i]))
            for i in range(len(indices[0]))
            if indices[0][i] != -1  # Filter out invalid results
        ]
        
        return results
    
    def _enhance_source_diversity(
        self, 
        results: List[Tuple[int, float, Dict]], 
        top_k: int,
        max_per_source: int = 2
    ) -> List[Tuple[int, float, Dict]]:
        """
        Enhance source diversity in retrieval results to prevent over-focusing on single documents.
        
        Args:
            results: List of (chunk_idx, score, chunk_dict) tuples sorted by relevance
            top_k: Maximum number of results to return
            max_per_source: Maximum chunks allowed per source document
            
        Returns:
            Diversified results maintaining relevance while improving source coverage
        """
        if not results:
            return []
            
        source_counts = {}
        diverse_results = []
        
        # First pass: Add highest scoring results respecting source limits
        for chunk_idx, score, chunk_dict in results:
            source = chunk_dict.get('source', 'unknown')
            current_count = source_counts.get(source, 0)
            
            if current_count < max_per_source:
                diverse_results.append((chunk_idx, score, chunk_dict))
                source_counts[source] = current_count + 1
                
                if len(diverse_results) >= top_k:
                    break
        
        # Second pass: If we still need more results, relax source constraints
        if len(diverse_results) < top_k:
            for chunk_idx, score, chunk_dict in results:
                if (chunk_idx, score, chunk_dict) not in diverse_results:
                    diverse_results.append((chunk_idx, score, chunk_dict))
                    
                    if len(diverse_results) >= top_k:
                        break
        
        return diverse_results[:top_k]
        
    def get_retrieval_stats(self) -> Dict[str, any]:
        """
        Get statistics about the indexed corpus and retrieval performance.
        
        Returns:
            Dictionary with corpus statistics
        """
        if not self.chunks:
            return {"status": "not_indexed"}
            
        return {
            "status": "indexed",
            "total_chunks": len(self.chunks),
            "dense_index_size": self.dense_index.ntotal if self.dense_index else 0,
            "embedding_dim": self.embeddings.shape[1] if self.embeddings is not None else 0,
            "sparse_indexed_chunks": len(self.sparse_retriever.chunk_mapping),
            "dense_weight": self.dense_weight,
            "sparse_weight": 1.0 - self.dense_weight,
            "rrf_k": self.rrf_k
        }