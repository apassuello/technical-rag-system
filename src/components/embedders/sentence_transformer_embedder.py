"""
Sentence Transformer embedder adapter for the modular RAG system.

This module provides an adapter that wraps the existing embedding generation
functionality to conform to the Embedder interface, enabling it to be used
in the modular architecture while preserving all existing functionality.
"""

import sys
from pathlib import Path
from typing import List

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from src.core.interfaces import Embedder
from src.core.registry import register_component
from shared_utils.embeddings.generator import generate_embeddings


@register_component("embedder", "sentence_transformer")
class SentenceTransformerEmbedder(Embedder):
    """
    Adapter for existing sentence transformer embedding generator.
    
    This class wraps the generate_embeddings function to provide an Embedder
    interface while maintaining all the performance optimizations and caching
    capabilities of the original implementation.
    
    Features:
    - Content-based caching for performance
    - Apple Silicon MPS acceleration
    - Batch processing for efficiency
    - 384-dimensional embeddings
    - 100+ texts/second on M4-Pro
    
    Example:
        embedder = SentenceTransformerEmbedder(
            model_name="sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
            use_mps=True
        )
        embeddings = embedder.embed(["Hello world", "How are you?"])
    """
    
    def __init__(
        self, 
        model_name: str = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
        batch_size: int = 32,
        use_mps: bool = True
    ):
        """
        Initialize the sentence transformer embedder.
        
        Args:
            model_name: SentenceTransformer model identifier (default: multi-qa-MiniLM-L6-cos-v1)
            batch_size: Processing batch size for efficiency (default: 32)
            use_mps: Use Apple Silicon acceleration if available (default: True)
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.use_mps = use_mps
        self._embedding_dim = None
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        This method uses the existing generate_embeddings function with
        performance optimizations including content-based caching and
        MPS acceleration.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors, where each vector is a list of floats
            
        Raises:
            ValueError: If texts list is empty
            RuntimeError: If embedding generation fails
        """
        if not texts:
            raise ValueError("Cannot generate embeddings for empty text list")
        
        try:
            # Use existing function with caching and optimization
            embeddings_array = generate_embeddings(
                texts=texts,
                model_name=self.model_name,
                batch_size=self.batch_size,
                use_mps=self.use_mps
            )
            
            # Convert numpy array to list of lists
            embeddings_list = embeddings_array.tolist()
            
            # Cache embedding dimension for future reference
            if self._embedding_dim is None and embeddings_list:
                self._embedding_dim = len(embeddings_list[0])
            
            return embeddings_list
            
        except Exception as e:
            raise RuntimeError(f"Failed to generate embeddings: {str(e)}") from e
    
    def embedding_dim(self) -> int:
        """
        Get the embedding dimension.
        
        Returns:
            Integer dimension of embeddings (typically 384 for multi-qa-MiniLM-L6-cos-v1)
            
        Note:
            If embeddings haven't been generated yet, this method will generate
            a dummy embedding to determine the dimension.
        """
        if self._embedding_dim is not None:
            return self._embedding_dim
        
        # Generate a dummy embedding to get dimension
        dummy_embeddings = self.embed(["test"])
        return len(dummy_embeddings[0])
    
    def get_model_info(self) -> dict:
        """
        Get information about the current model configuration.
        
        Returns:
            Dictionary with model configuration details
        """
        return {
            "model_name": self.model_name,
            "batch_size": self.batch_size,
            "use_mps": self.use_mps,
            "embedding_dimension": self.embedding_dim() if self._embedding_dim else "unknown",
            "component_type": "sentence_transformer"
        }
    
    def supports_batching(self) -> bool:
        """
        Check if this embedder supports batch processing.
        
        Returns:
            True, as this implementation supports efficient batch processing
        """
        return True
    
    def get_cache_stats(self) -> dict:
        """
        Get statistics about the embedding cache.
        
        Note: This would require access to the cache from the original function.
        For now, returns basic info about caching support.
        
        Returns:
            Dictionary with cache information
        """
        return {
            "caching_enabled": True,
            "cache_type": "content_based",
            "note": "Cache statistics require access to global cache from generator module"
        }