"""
Advanced Retriever with Epic 2 Features for HF Deployment.

Self-contained implementation combining hybrid search, neural reranking,
and graph enhancement without external dependencies.
"""

import logging
import time
from typing import List, Dict, Any, Tuple, Optional
import sys
from pathlib import Path

try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

# Import our self-contained Epic 2 components
from .neural_reranker import NeuralReranker, IdentityReranker
from .graph_retriever import GraphRetriever
from .base_reranker import Document

# Import existing HF deployment utilities
sys.path.append(str(Path(__file__).parent.parent))
from shared_utils.embeddings.generator import generate_embeddings

logger = logging.getLogger(__name__)


class AdvancedRetriever:
    """
    Advanced retriever combining hybrid search, neural reranking, and graph enhancement.
    
    This is the Epic 2 equivalent retriever for HF deployment, providing:
    - Dense semantic search with FAISS
    - Sparse BM25 keyword search  
    - Reciprocal Rank Fusion (RRF)
    - Neural reranking with cross-encoder models
    - Graph-based document relationship enhancement
    - Analytics and performance monitoring
    
    Features preserved from Epic 2:
    - ✅ Multi-backend support (FAISS primary)
    - ✅ Neural reranking with local cross-encoder
    - ✅ Graph enhancement with entity linking
    - ✅ Performance optimization and caching
    - ✅ Comprehensive statistics and monitoring
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize advanced retriever with Epic 2 capabilities.
        
        Args:
            config: Configuration dictionary with all retrieval settings
        """
        self.config = config
        
        # Basic retrieval configuration
        self.dense_weight = config.get("dense_weight", 0.4)
        self.sparse_weight = config.get("sparse_weight", 0.3)
        self.graph_weight = config.get("graph_weight", 0.3)
        self.rrf_k = config.get("rrf_k", 60)
        
        # Model configuration
        self.embedding_model = config.get("embedding_model", "sentence-transformers/multi-qa-MiniLM-L6-cos-v1")
        
        # Performance settings
        self.max_candidates_per_strategy = config.get("max_candidates_per_strategy", 200)
        self.early_termination_threshold = config.get("early_termination_threshold", 0.95)
        
        # Initialize components
        self.faiss_index = None
        self.bm25_retriever = None
        self.neural_reranker = None
        self.graph_retriever = None
        
        # Data storage
        self.documents = []
        self.document_embeddings = None
        
        # Statistics
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "total_latency_ms": 0.0,
            "dense_retrieval_time": 0.0,
            "sparse_retrieval_time": 0.0,
            "graph_enhancement_time": 0.0,
            "neural_reranking_time": 0.0,
            "fusion_time": 0.0
        }
        
        # Initialize Epic 2 components
        self._initialize_components()
        
        logger.info(f"AdvancedRetriever initialized with Epic 2 features")
    
    def _initialize_components(self):
        """Initialize Epic 2 sub-components."""
        try:
            # Initialize neural reranker
            reranker_config = self.config.get("reranker", {})
            if reranker_config.get("enabled", True):
                try:
                    self.neural_reranker = NeuralReranker(reranker_config.get("config", {}))
                except Exception as e:
                    logger.warning(f"Failed to initialize neural reranker: {e}")
                    self.neural_reranker = IdentityReranker({"enabled": True})
            else:
                self.neural_reranker = IdentityReranker({"enabled": True})
            
            # Initialize graph retriever
            graph_config = self.config.get("graph_retrieval", {})
            if graph_config.get("enabled", True):
                try:
                    self.graph_retriever = GraphRetriever(graph_config)
                except Exception as e:
                    logger.warning(f"Failed to initialize graph retriever: {e}")
                    self.graph_retriever = None
            
            # Initialize BM25 (simple implementation)
            self._initialize_bm25()
            
            logger.info("Epic 2 components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Epic 2 components: {e}")
    
    def _initialize_bm25(self):
        """Initialize simple BM25 implementation."""
        try:
            from collections import Counter
            import math
            
            class SimpleBM25:
                def __init__(self, k1=1.2, b=0.75):
                    self.k1 = k1
                    self.b = b
                    self.documents = []
                    self.doc_lengths = []
                    self.avg_doc_length = 0
                    self.doc_freqs = []
                    self.vocab = set()
                
                def fit(self, documents):
                    self.documents = documents
                    self.doc_lengths = []
                    self.doc_freqs = []
                    
                    # Tokenize and build vocabulary
                    for doc in documents:
                        tokens = doc.lower().split()
                        self.doc_lengths.append(len(tokens))
                        self.vocab.update(tokens)
                        self.doc_freqs.append(Counter(tokens))
                    
                    self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 0
                
                def search(self, query, top_k=10):
                    if not self.documents:
                        return []
                    
                    query_tokens = query.lower().split()
                    scores = []
                    
                    for i, doc_freq in enumerate(self.doc_freqs):
                        score = 0
                        doc_length = self.doc_lengths[i]
                        
                        for token in query_tokens:
                            if token in doc_freq:
                                tf = doc_freq[token]
                                # Document frequency
                                df = sum(1 for df_dict in self.doc_freqs if token in df_dict)
                                idf = math.log((len(self.documents) - df + 0.5) / (df + 0.5))
                                
                                # BM25 score
                                score += idf * (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length))
                        
                        scores.append((i, score))
                    
                    # Sort by score and return top_k
                    scores.sort(key=lambda x: x[1], reverse=True)
                    return scores[:top_k]
            
            self.bm25_retriever = SimpleBM25()
            
        except Exception as e:
            logger.error(f"Failed to initialize BM25: {e}")
            self.bm25_retriever = None
    
    def index_documents(self, documents: List[Dict[str, Any]]):
        """
        Index documents for retrieval.
        
        Args:
            documents: List of document dictionaries with 'text' and metadata
        """
        try:
            print(f"🔍 Indexing {len(documents)} documents with Epic 2 features...", file=sys.stderr, flush=True)
            
            # Store documents
            self.documents = []
            doc_texts = []
            
            for doc in documents:
                doc_obj = Document(
                    content=doc['text'],
                    metadata=doc.get('metadata', {})
                )
                self.documents.append(doc_obj)
                doc_texts.append(doc['text'])
            
            # Generate embeddings for dense retrieval
            if FAISS_AVAILABLE:
                print(f"🔤 Generating embeddings...", file=sys.stderr, flush=True)
                embeddings = generate_embeddings(doc_texts, model=self.embedding_model)
                self.document_embeddings = np.array(embeddings)
                
                # Build FAISS index
                dimension = self.document_embeddings.shape[1]
                self.faiss_index = faiss.IndexFlatIP(dimension)
                
                # Normalize embeddings for cosine similarity
                faiss.normalize_L2(self.document_embeddings)
                self.faiss_index.add(self.document_embeddings)
                
                print(f"✅ FAISS index built with {len(documents)} documents", file=sys.stderr, flush=True)
            else:
                print(f"⚠️ FAISS not available, using embedding similarity", file=sys.stderr, flush=True)
                embeddings = generate_embeddings(doc_texts, model=self.embedding_model)
                self.document_embeddings = np.array(embeddings)
            
            # Index documents in BM25
            if self.bm25_retriever:
                print(f"📝 Building BM25 index...", file=sys.stderr, flush=True)
                self.bm25_retriever.fit(doc_texts)
                print(f"✅ BM25 index built", file=sys.stderr, flush=True)
            
            # Build graph for graph enhancement
            if self.graph_retriever and self.graph_retriever.is_enabled():
                print(f"🕸️ Building document graph...", file=sys.stderr, flush=True)
                self.graph_retriever.build_document_graph(self.documents)
                print(f"✅ Document graph built", file=sys.stderr, flush=True)
            
            print(f"🚀 Epic 2 indexing complete!", file=sys.stderr, flush=True)
            
        except Exception as e:
            logger.error(f"Failed to index documents: {e}")
            raise
    
    def search(
        self, 
        query: str, 
        top_k: int = 10, 
        use_neural_reranking: bool = True,
        use_graph_enhancement: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search documents using Epic 2 advanced retrieval.
        
        Args:
            query: Search query
            top_k: Number of results to return
            use_neural_reranking: Whether to use neural reranking
            use_graph_enhancement: Whether to use graph enhancement
            
        Returns:
            List of search results with Epic 2 enhancements
        """
        start_time = time.time()
        self.stats["total_queries"] += 1
        
        try:
            if not self.documents:
                return []
            
            # Stage 1: Dense retrieval
            dense_start = time.time()
            dense_results = self._dense_search(query, self.max_candidates_per_strategy)
            self.stats["dense_retrieval_time"] += time.time() - dense_start
            
            # Stage 2: Sparse retrieval  
            sparse_start = time.time()
            sparse_results = self._sparse_search(query, self.max_candidates_per_strategy)
            self.stats["sparse_retrieval_time"] += time.time() - sparse_start
            
            # Stage 3: Graph enhancement
            graph_start = time.time()
            if use_graph_enhancement and self.graph_retriever and self.graph_retriever.is_enabled():
                initial_scores = [score for _, score in dense_results]
                enhanced_scores = self.graph_retriever.enhance_retrieval_scores(
                    query, self.documents, initial_scores
                )
                # Update dense results with enhanced scores
                dense_results = [(idx, enhanced_scores[i] if i < len(enhanced_scores) else score) 
                               for i, (idx, score) in enumerate(dense_results)]
            self.stats["graph_enhancement_time"] += time.time() - graph_start
            
            # Stage 4: Fusion
            fusion_start = time.time()
            fused_results = self._fuse_results(dense_results, sparse_results, top_k * 2)
            self.stats["fusion_time"] += time.time() - fusion_start
            
            # Stage 5: Neural reranking
            rerank_start = time.time()
            if use_neural_reranking and self.neural_reranker and self.neural_reranker.is_enabled():
                # Prepare documents and scores for reranking
                rerank_docs = [self.documents[idx] for idx, _ in fused_results]
                rerank_scores = [score for _, score in fused_results]
                
                # Rerank
                reranked_results = self.neural_reranker.rerank(query, rerank_docs, rerank_scores)
                
                # Convert back to original indices
                final_results = []
                for rank_idx, rerank_score in reranked_results:
                    original_idx = fused_results[rank_idx][0]
                    final_results.append((original_idx, rerank_score))
            else:
                final_results = fused_results
            self.stats["neural_reranking_time"] += time.time() - rerank_start
            
            # Limit to top_k results
            final_results = final_results[:top_k]
            
            # Format results
            formatted_results = []
            for idx, score in final_results:
                result = {
                    "text": self.documents[idx].content,
                    "metadata": self.documents[idx].metadata,
                    "score": float(score),
                    "index": idx
                }
                
                # Add graph connections if available
                if self.graph_retriever and self.graph_retriever.is_enabled():
                    connections = self.graph_retriever.get_document_connections(idx, self.documents)
                    result["graph_connections"] = connections["connections"]
                    result["related_entities"] = connections["entities"]
                
                formatted_results.append(result)
            
            # Update statistics
            total_time = time.time() - start_time
            self.stats["successful_queries"] += 1
            self.stats["total_latency_ms"] += total_time * 1000
            
            logger.debug(f"Epic 2 search completed in {total_time*1000:.1f}ms for query: {query[:50]}...")
            
            return formatted_results
            
        except Exception as e:
            self.stats["failed_queries"] += 1
            logger.error(f"Advanced search failed: {e}")
            return []
    
    def _dense_search(self, query: str, top_k: int) -> List[Tuple[int, float]]:
        """Perform dense semantic search."""
        try:
            # Generate query embedding
            query_embedding = generate_embeddings([query], model=self.embedding_model)[0]
            query_embedding = np.array([query_embedding])
            
            if FAISS_AVAILABLE and self.faiss_index:
                # Use FAISS for efficient search
                faiss.normalize_L2(query_embedding)
                scores, indices = self.faiss_index.search(query_embedding, min(top_k, len(self.documents)))
                
                return [(int(indices[0][i]), float(scores[0][i])) for i in range(len(indices[0]))]
            else:
                # Fallback to numpy similarity
                similarities = np.dot(self.document_embeddings, query_embedding.T).flatten()
                sorted_indices = np.argsort(similarities)[::-1][:top_k]
                
                return [(int(idx), float(similarities[idx])) for idx in sorted_indices]
        
        except Exception as e:
            logger.error(f"Dense search failed: {e}")
            return []
    
    def _sparse_search(self, query: str, top_k: int) -> List[Tuple[int, float]]:
        """Perform sparse BM25 search."""
        try:
            if not self.bm25_retriever:
                return []
            
            results = self.bm25_retriever.search(query, top_k)
            return results
        
        except Exception as e:
            logger.error(f"Sparse search failed: {e}")
            return []
    
    def _fuse_results(
        self, 
        dense_results: List[Tuple[int, float]], 
        sparse_results: List[Tuple[int, float]], 
        top_k: int
    ) -> List[Tuple[int, float]]:
        """Fuse dense and sparse results using RRF."""
        try:
            # Reciprocal Rank Fusion
            doc_scores = {}
            
            # Add dense scores
            for rank, (doc_idx, score) in enumerate(dense_results):
                rrf_score = self.dense_weight / (self.rrf_k + rank + 1)
                doc_scores[doc_idx] = doc_scores.get(doc_idx, 0) + rrf_score
            
            # Add sparse scores
            for rank, (doc_idx, score) in enumerate(sparse_results):
                rrf_score = self.sparse_weight / (self.rrf_k + rank + 1)
                doc_scores[doc_idx] = doc_scores.get(doc_idx, 0) + rrf_score
            
            # Sort by fused score
            fused_results = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
            return fused_results[:top_k]
        
        except Exception as e:
            logger.error(f"Fusion failed: {e}")
            return dense_results[:top_k]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive Epic 2 statistics."""
        stats = self.stats.copy()
        
        # Add component stats
        if self.neural_reranker:
            stats["neural_reranker"] = self.neural_reranker.get_reranker_info()
        
        if self.graph_retriever:
            stats["graph_retriever"] = self.graph_retriever.get_stats()
        
        # Add performance metrics
        if self.stats["total_queries"] > 0:
            stats["avg_latency_ms"] = self.stats["total_latency_ms"] / self.stats["total_queries"]
            stats["success_rate"] = self.stats["successful_queries"] / self.stats["total_queries"]
        
        stats.update({
            "total_documents": len(self.documents),
            "faiss_available": FAISS_AVAILABLE,
            "components_enabled": {
                "neural_reranking": self.neural_reranker and self.neural_reranker.is_enabled(),
                "graph_enhancement": self.graph_retriever and self.graph_retriever.is_enabled(),
                "dense_search": self.faiss_index is not None or self.document_embeddings is not None,
                "sparse_search": self.bm25_retriever is not None
            }
        })
        
        return stats