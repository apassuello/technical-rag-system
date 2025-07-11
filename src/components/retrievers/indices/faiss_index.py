"""
FAISS Vector Index implementation for Modular Retriever Architecture.

This module provides a direct implementation of FAISS vector indexing
extracted from the UnifiedRetriever for improved modularity.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import faiss

from src.core.interfaces import Document
from .base import VectorIndex

logger = logging.getLogger(__name__)


class FAISSIndex(VectorIndex):
    """
    FAISS-based vector index implementation.
    
    This is a direct implementation that handles FAISS vector storage and search
    without external adapters. It provides efficient similarity search for
    dense embeddings with configurable index types.
    
    Features:
    - Multiple FAISS index types (Flat, IVF, HNSW)
    - Embedding normalization for cosine similarity
    - Configurable distance metrics
    - Memory-efficient vector storage
    - Apple Silicon MPS compatibility
    
    Example:
        config = {
            "index_type": "IndexFlatIP",
            "normalize_embeddings": True,
            "metric": "cosine"
        }
        index = FAISSIndex(config)
        index.initialize_index(embedding_dim=384)
        index.add_documents(documents)
        results = index.search(query_embedding, k=5)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize FAISS vector index.
        
        Args:
            config: Configuration dictionary with:
                - index_type: FAISS index type (default: "IndexFlatIP")
                - normalize_embeddings: Whether to normalize embeddings (default: True)
                - metric: Distance metric ("cosine" or "euclidean", default: "cosine")
                - nlist: Number of clusters for IVF indices (default: 100)
        """
        self.config = config
        self.index_type = config.get("index_type", "IndexFlatIP")
        self.normalize_embeddings = config.get("normalize_embeddings", True)
        self.metric = config.get("metric", "cosine")
        self.nlist = config.get("nlist", 100)
        
        # FAISS components
        self.index: Optional[faiss.Index] = None
        self.embedding_dim: Optional[int] = None
        self.documents: List[Document] = []
        
        logger.info(f"FAISSIndex initialized with type={self.index_type}")
    
    def initialize_index(self, embedding_dim: int) -> None:
        """
        Initialize the FAISS index with the specified embedding dimension.
        
        Args:
            embedding_dim: Dimension of the embeddings to be indexed
        """
        self.embedding_dim = embedding_dim
        
        if self.index_type == "IndexFlatIP":
            # Inner product (cosine similarity with normalized embeddings)
            self.index = faiss.IndexFlatIP(embedding_dim)
        elif self.index_type == "IndexFlatL2":
            # L2 distance (Euclidean)
            self.index = faiss.IndexFlatL2(embedding_dim)
        elif self.index_type == "IndexIVFFlat":
            # IVF with flat quantizer (requires training)
            nlist = min(self.nlist, max(10, int(np.sqrt(1000))))  # Heuristic for nlist
            if self.metric == "cosine":
                quantizer = faiss.IndexFlatIP(embedding_dim)
            else:
                quantizer = faiss.IndexFlatL2(embedding_dim)
            self.index = faiss.IndexIVFFlat(quantizer, embedding_dim, nlist)
        elif self.index_type == "IndexHNSWFlat":
            # HNSW (Hierarchical Navigable Small World)
            self.index = faiss.IndexHNSWFlat(embedding_dim, 32)  # 32 is M parameter
        else:
            raise ValueError(f"Unsupported FAISS index type: {self.index_type}")
        
        logger.info(f"FAISS index initialized: {self.index_type} with dim={embedding_dim}")
    
    def add_documents(self, documents: List[Document]) -> None:
        """
        Add documents to the FAISS index.
        
        Args:
            documents: List of documents with embeddings to add
            
        Raises:
            ValueError: If documents don't have embeddings or wrong dimension
        """
        if not documents:
            raise ValueError("Cannot add empty document list")
        
        if self.index is None:
            raise RuntimeError("Index not initialized. Call initialize_index() first.")
        
        # Validate embeddings
        for i, doc in enumerate(documents):
            if doc.embedding is None:
                raise ValueError(f"Document {i} is missing embedding")
            if len(doc.embedding) != self.embedding_dim:
                raise ValueError(
                    f"Document {i} embedding dimension {len(doc.embedding)} "
                    f"doesn't match expected {self.embedding_dim}"
                )
        
        # Extract embeddings
        embeddings = np.array([doc.embedding for doc in documents], dtype=np.float32)
        
        # Normalize embeddings if requested
        if self.normalize_embeddings:
            embeddings = self._normalize_embeddings(embeddings)
        
        # Train index if needed (for IVF indices)
        if hasattr(self.index, 'is_trained') and not self.index.is_trained:
            if len(self.documents) + len(documents) >= self.nlist:
                # Combine with existing documents for training
                all_embeddings = embeddings
                if len(self.documents) > 0:
                    existing_embeddings = np.array(
                        [doc.embedding for doc in self.documents], 
                        dtype=np.float32
                    )
                    if self.normalize_embeddings:
                        existing_embeddings = self._normalize_embeddings(existing_embeddings)
                    all_embeddings = np.vstack([existing_embeddings, embeddings])
                
                self.index.train(all_embeddings)
                logger.info(f"FAISS index trained with {len(all_embeddings)} vectors")
        
        # Add embeddings to index
        self.index.add(embeddings)
        
        # Store documents
        self.documents.extend(documents)
        
        logger.debug(f"Added {len(documents)} documents to FAISS index")
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[int, float]]:
        """
        Search for similar documents using FAISS.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of (document_index, similarity_score) tuples
        """
        if self.index is None:
            raise RuntimeError("Index not initialized")
        
        if len(self.documents) == 0:
            return []
        
        # Ensure query embedding is the right shape and type
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        query_embedding = query_embedding.astype(np.float32)
        
        # Normalize query embedding if needed
        if self.normalize_embeddings:
            query_embedding = self._normalize_embeddings(query_embedding)
        
        # Perform search
        k = min(k, len(self.documents))  # Don't search for more docs than we have
        distances, indices = self.index.search(query_embedding, k)
        
        # Convert to list of tuples
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx >= 0:  # FAISS returns -1 for missing results
                # Convert distance to similarity score
                if self.index_type == "IndexFlatIP":
                    # Inner product (higher is better)
                    similarity = float(distance)
                else:
                    # L2 distance (lower is better) - convert to similarity
                    similarity = 1.0 / (1.0 + float(distance))
                
                results.append((int(idx), similarity))
        
        return results
    
    def get_document_count(self) -> int:
        """Get the number of documents in the index."""
        return len(self.documents)
    
    def clear(self) -> None:
        """Clear all documents from the index."""
        self.documents.clear()
        if self.index is not None:
            self.index.reset()
        logger.info("FAISS index cleared")
    
    def get_index_info(self) -> Dict[str, Any]:
        """
        Get information about the FAISS index.
        
        Returns:
            Dictionary with index statistics and configuration
        """
        info = {
            "index_type": self.index_type,
            "embedding_dim": self.embedding_dim,
            "normalize_embeddings": self.normalize_embeddings,
            "metric": self.metric,
            "document_count": len(self.documents),
            "is_trained": self.is_trained()
        }
        
        if self.index is not None:
            info["total_vectors"] = self.index.ntotal
            if self.embedding_dim:
                info["index_size_bytes"] = self.index.ntotal * self.embedding_dim * 4  # float32
        
        return info
    
    def is_trained(self) -> bool:
        """
        Check if the index is trained.
        
        Returns:
            True if the index is ready for searching
        """
        if self.index is None:
            return False
        
        if hasattr(self.index, 'is_trained'):
            return self.index.is_trained
        else:
            # Flat indices don't need training
            return True
    
    def _normalize_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Normalize embeddings for cosine similarity.
        
        Args:
            embeddings: Array of embeddings to normalize
            
        Returns:
            Normalized embeddings
        """
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        # Avoid division by zero
        norms = np.where(norms == 0, 1, norms)
        return embeddings / norms
    
    def save_index(self, filepath: str) -> None:
        """
        Save the FAISS index to disk.
        
        Args:
            filepath: Path to save the index
        """
        if self.index is None:
            raise RuntimeError("No index to save")
        
        faiss.write_index(self.index, filepath)
        logger.info(f"FAISS index saved to {filepath}")
    
    def load_index(self, filepath: str) -> None:
        """
        Load a FAISS index from disk.
        
        Args:
            filepath: Path to load the index from
        """
        self.index = faiss.read_index(filepath)
        logger.info(f"FAISS index loaded from {filepath}")
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get memory usage statistics.
        
        Returns:
            Dictionary with memory usage information
        """
        if self.index is None or self.embedding_dim is None:
            return {"total_bytes": 0, "per_document_bytes": 0}
        
        # Estimate memory usage
        vectors_bytes = self.index.ntotal * self.embedding_dim * 4  # float32
        metadata_bytes = len(self.documents) * 1024  # Rough estimate for document metadata
        
        return {
            "total_bytes": vectors_bytes + metadata_bytes,
            "vectors_bytes": vectors_bytes,
            "metadata_bytes": metadata_bytes,
            "per_document_bytes": (vectors_bytes + metadata_bytes) / max(1, len(self.documents))
        }