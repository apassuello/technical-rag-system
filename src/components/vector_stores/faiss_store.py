"""
FAISS vector store adapter for the modular RAG system.

This module provides an adapter that wraps FAISS functionality
to conform to the VectorStore interface, enabling it to be used
in the modular architecture while preserving performance optimizations.
"""

import faiss
import numpy as np
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from src.core.interfaces import Document, RetrievalResult, VectorStore

logger = logging.getLogger(__name__)


class FAISSVectorStore(VectorStore):
    """
    FAISS-based vector store implementation.
    
    This class provides a VectorStore interface using FAISS for efficient
    similarity search. It supports different FAISS index types and includes
    optimizations like embedding normalization for cosine similarity.
    
    Features:
    - Multiple FAISS index types (Flat, IVF, HNSW)
    - Embedding normalization for cosine similarity
    - Document metadata storage and retrieval
    - Efficient batch operations
    - Memory-efficient document management
    
    Example:
        store = FAISSVectorStore(embedding_dim=384, index_type="IndexFlatIP")
        store.add(documents_with_embeddings)
        results = store.search(query_embedding, k=5)
    """
    
    def __init__(
        self,
        embedding_dim: int = 384,
        index_type: str = "IndexFlatIP",
        normalize_embeddings: bool = True,
        metric: str = "cosine"
    ):
        """
        Initialize the FAISS vector store.
        
        Args:
            embedding_dim: Dimension of embeddings (default: 384)
            index_type: FAISS index type (default: "IndexFlatIP")
            normalize_embeddings: Whether to normalize embeddings (default: True)
            metric: Distance metric ("cosine" or "euclidean", default: "cosine")
        """
        self.embedding_dim = embedding_dim
        self.index_type = index_type
        self.normalize_embeddings = normalize_embeddings
        self.metric = metric
        
        # Initialize FAISS index
        self.index: Optional[faiss.Index] = None
        
        # Document storage
        self.documents: List[Document] = []
        self.doc_id_to_index: Dict[str, int] = {}
        
        # Track document count for ID generation
        self._next_doc_id = 0
    
    def add(self, documents: List[Document]) -> None:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of documents with embeddings
            
        Raises:
            ValueError: If documents don't have embeddings
        """
        if not documents:
            logger.warning("No documents provided to add")
            return
        
        # Validate that all documents have embeddings
        for i, doc in enumerate(documents):
            if doc.embedding is None:
                raise ValueError(f"Document {i} is missing embedding")
            if len(doc.embedding) != self.embedding_dim:
                raise ValueError(
                    f"Document {i} embedding dimension {len(doc.embedding)} "
                    f"doesn't match expected {self.embedding_dim}"
                )
        
        # Initialize index if this is the first batch
        if self.index is None:
            self._initialize_index()
        
        # Extract embeddings and prepare for FAISS
        embeddings = np.array([doc.embedding for doc in documents], dtype=np.float32)
        
        # Normalize embeddings if requested
        if self.normalize_embeddings:
            embeddings = self._normalize_embeddings(embeddings)
        
        # Add to FAISS index
        self.index.add(embeddings)
        
        # Store documents with generated IDs
        start_index = len(self.documents)
        for i, doc in enumerate(documents):
            doc_id = str(self._next_doc_id)
            self._next_doc_id += 1
            
            # Add doc_id to metadata if not present
            if 'doc_id' not in doc.metadata:
                doc.metadata['doc_id'] = doc_id
            
            # Store document and mapping
            self.documents.append(doc)
            self.doc_id_to_index[doc_id] = start_index + i
        
        logger.info(f"Added {len(documents)} documents to FAISS vector store")
    
    def search(
        self, 
        query_embedding: List[float], 
        k: int = 5
    ) -> List[RetrievalResult]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query vector
            k: Number of results to return
            
        Returns:
            List of retrieval results sorted by score (descending)
            
        Raises:
            ValueError: If k <= 0 or query_embedding is invalid
            RuntimeError: If no documents have been added
        """
        if k <= 0:
            raise ValueError("k must be positive")
        
        if self.index is None or len(self.documents) == 0:
            raise RuntimeError("No documents in vector store")
        
        if len(query_embedding) != self.embedding_dim:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} "
                f"doesn't match expected {self.embedding_dim}"
            )
        
        # Prepare query embedding
        query_array = np.array([query_embedding], dtype=np.float32)
        if self.normalize_embeddings:
            query_array = self._normalize_embeddings(query_array)
        
        # Search FAISS index
        actual_k = min(k, len(self.documents))
        scores, indices = self.index.search(query_array, actual_k)
        
        # Convert to RetrievalResult objects
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for invalid results
                continue
                
            document = self.documents[idx]
            result = RetrievalResult(
                document=document,
                score=float(score),
                retrieval_method=f"faiss_{self.index_type.lower()}"
            )
            results.append(result)
        
        return results
    
    def delete(self, doc_ids: List[str]) -> None:
        """
        Delete documents by ID.
        
        Args:
            doc_ids: List of document IDs to delete
            
        Raises:
            KeyError: If document ID not found
            NotImplementedError: FAISS doesn't support individual deletion
        """
        # Check that all IDs exist
        for doc_id in doc_ids:
            if doc_id not in self.doc_id_to_index:
                raise KeyError(f"Document ID '{doc_id}' not found")
        
        # FAISS doesn't support individual document deletion efficiently
        # This would require rebuilding the entire index
        raise NotImplementedError(
            "FAISS doesn't support efficient individual document deletion. "
            "Use clear() to remove all documents and re-add the remaining ones."
        )
    
    def clear(self) -> None:
        """Clear all documents from the store."""
        self.index = None
        self.documents.clear()
        self.doc_id_to_index.clear()
        self._next_doc_id = 0
        logger.info("Cleared all documents from FAISS vector store")
    
    def get_document_count(self) -> int:
        """Get the number of documents in the store."""
        return len(self.documents)
    
    def get_index_info(self) -> Dict[str, Any]:
        """
        Get information about the FAISS index.
        
        Returns:
            Dictionary with index information
        """
        info = {
            "index_type": self.index_type,
            "embedding_dim": self.embedding_dim,
            "normalize_embeddings": self.normalize_embeddings,
            "metric": self.metric,
            "document_count": len(self.documents),
            "is_trained": self.index.is_trained if self.index else False,
            "total_vectors": self.index.ntotal if self.index else 0
        }
        
        if self.index:
            info["index_size_bytes"] = self.index.ntotal * self.embedding_dim * 4  # float32
        
        return info
    
    def _initialize_index(self) -> None:
        """Initialize the FAISS index based on configuration."""
        if self.index_type == "IndexFlatIP":
            # Inner product (cosine similarity with normalized embeddings)
            self.index = faiss.IndexFlatIP(self.embedding_dim)
        elif self.index_type == "IndexFlatL2":
            # L2 distance (Euclidean)
            self.index = faiss.IndexFlatL2(self.embedding_dim)
        elif self.index_type == "IndexIVFFlat":
            # IVF with flat quantizer (requires training)
            nlist = min(100, max(10, int(np.sqrt(1000))))  # Heuristic for nlist
            quantizer = faiss.IndexFlatL2(self.embedding_dim)
            self.index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, nlist)
        else:
            raise ValueError(f"Unsupported FAISS index type: {self.index_type}")
        
        logger.info(f"Initialized FAISS index: {self.index_type}")
    
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