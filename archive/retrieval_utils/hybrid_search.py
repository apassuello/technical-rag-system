"""
Hybrid retrieval combining dense semantic search with sparse BM25 keyword matching.
Uses modern modular components following the architecture specification.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Modern modular components
import logging

import faiss

from src.components.retrievers.fusion.rrf_fusion import RRFFusion
from src.components.retrievers.fusion.score_aware_fusion import ScoreAwareFusion
from src.components.retrievers.fusion.weighted_fusion import WeightedFusion
from src.components.retrievers.sparse.bm25_retriever import BM25Retriever
from src.shared_utils.embeddings.generator import generate_embeddings

logger = logging.getLogger(__name__)

class HybridRetriever:
    """
    Hybrid retrieval system combining dense semantic search with sparse BM25.
    
    Now uses modern modular components following the architecture specification:
    - BM25Retriever: Modular sparse retrieval component
    - RRFFusion: Reciprocal Rank Fusion strategy
    - WeightedFusion: Score-based fusion strategy
    - ScoreAwareFusion: Advanced fusion with score awareness
    
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
        
        # Initialize modular sparse retriever
        sparse_config = {
            "k1": bm25_k1,
            "b": bm25_b,
            "lowercase": True,
            "preserve_technical_terms": True
        }
        self.sparse_retriever = BM25Retriever(sparse_config)
        
        # Initialize fusion strategies
        fusion_config = {
            "k": rrf_k,
            "weights": {
                "dense": dense_weight,
                "sparse": 1.0 - dense_weight
            }
        }
        self.rrf_fusion = RRFFusion(fusion_config)
        self.weighted_fusion = WeightedFusion(fusion_config)
        self.score_aware_fusion = ScoreAwareFusion(fusion_config)
        
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
            
        logger.info(f"Indexing {len(chunks)} chunks for hybrid retrieval...")
        
        # Store chunks for retrieval
        self.chunks = chunks
        
        # Index for sparse retrieval
        logger.info("Building BM25 sparse index...")
        # Import Document interface
        from src.core.interfaces import Document
        
        # Convert chunks to Document objects for modular components
        documents = []
        for i, chunk in enumerate(chunks):
            # Create Document objects expected by modular components
            doc = Document(
                content=chunk['text'],
                metadata={
                    'source': chunk.get('source', 'unknown'),
                    'page': chunk.get('page', 1),
                    'chunk_id': chunk.get('chunk_id', i),
                    'original_index': i
                }
            )
            documents.append(doc)
        
        self.sparse_retriever.index_documents(documents)
        
        # Index for dense retrieval
        logger.info("Building dense semantic index...")
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
        
        logger.info(f"Hybrid indexing complete: {len(chunks)} chunks ready for search")
        
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
        
        # Use adaptive fusion strategy based on result set size
        total_results = len(set(idx for idx, _ in dense_results) | set(idx for idx, _ in sparse_results))
        
        if total_results <= 20:
            # For small result sets, use weighted fusion to preserve score variation
            fused_results = self.weighted_fusion.fuse_results(dense_results, sparse_results)
        else:
            # For larger sets, use RRF fusion
            fused_results = self.rrf_fusion.fuse_results(dense_results, sparse_results)
        
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
    
    def search_with_fusion_strategy(
        self,
        query: str,
        fusion_strategy: str = "adaptive",
        top_k: int = 10,
        dense_top_k: Optional[int] = None,
        sparse_top_k: Optional[int] = None
    ) -> List[Tuple[int, float, Dict]]:
        """
        Search using a specific fusion strategy for demonstration purposes.
        
        Args:
            query: Search query string
            fusion_strategy: One of "rrf", "weighted", "score_aware", "adaptive"
            top_k: Final number of results to return
            dense_top_k: Results from dense search (default: 2*top_k)
            sparse_top_k: Results from sparse search (default: 2*top_k)
            
        Returns:
            List of (chunk_index, fusion_score, chunk_dict) tuples
        """
        if self.dense_index is None:
            raise ValueError("Must call index_documents() before searching")
            
        if not query.strip():
            return []
            
        # Set default intermediate result counts
        if dense_top_k is None:
            dense_top_k = min(2 * top_k, len(self.chunks))
        if sparse_top_k is None:
            sparse_top_k = min(2 * top_k, len(self.chunks))
            
        # Get retrieval results
        dense_results = self._dense_search(query, dense_top_k)
        sparse_results = self.sparse_retriever.search(query, sparse_top_k)
        
        # Apply requested fusion strategy
        if fusion_strategy == "rrf":
            fused_results = self.rrf_fusion.fuse_results(dense_results, sparse_results)
        elif fusion_strategy == "weighted":
            fused_results = self.weighted_fusion.fuse_results(dense_results, sparse_results)
        elif fusion_strategy == "score_aware":
            fused_results = self.score_aware_fusion.fuse_results(dense_results, sparse_results)
        elif fusion_strategy == "adaptive":
            # Adaptive strategy based on result set size
            total_results = len(set(idx for idx, _ in dense_results) | set(idx for idx, _ in sparse_results))
            if total_results <= 20:
                fused_results = self.weighted_fusion.fuse_results(dense_results, sparse_results)
            else:
                fused_results = self.rrf_fusion.fuse_results(dense_results, sparse_results)
        else:
            raise ValueError(f"Unknown fusion strategy: {fusion_strategy}")
        
        # Prepare final results
        final_results = []
        for chunk_idx, fusion_score in fused_results[:top_k]:
            chunk_dict = self.chunks[chunk_idx]
            final_results.append((chunk_idx, fusion_score, chunk_dict))
        
        return final_results
        
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