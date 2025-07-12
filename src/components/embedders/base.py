"""
Base interfaces for embedder sub-components.

This module defines the abstract interfaces for all embedder sub-components
following the architecture specification in COMPONENT-3-EMBEDDER.md.

Interfaces are derived from rag-interface-reference.md section 3.2.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))


class EmbeddingModel(ABC):
    """
    Core embedding generation interface.
    
    This interface defines the contract for all embedding model implementations,
    whether they are direct implementations (for local models) or adapters
    (for external APIs like OpenAI, Cohere).
    
    Architecture Pattern:
    - Direct Implementation: Local models (SentenceTransformers)
    - Adapter Pattern: External APIs (OpenAI, Cohere)
    """
    
    @abstractmethod
    def encode(self, texts: List[str]) -> np.ndarray:
        """
        Encode texts to embeddings.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            numpy array of shape (len(texts), embedding_dim)
            
        Raises:
            ValueError: If texts list is empty
            RuntimeError: If encoding fails
        """
        pass
        
    @abstractmethod
    def get_model_name(self) -> str:
        """
        Return model identifier.
        
        Returns:
            String identifier for the embedding model
        """
        pass
        
    @abstractmethod
    def get_embedding_dim(self) -> int:
        """
        Return embedding dimension.
        
        Returns:
            Integer dimension of embeddings produced by this model
        """
        pass
    
    @abstractmethod
    def get_max_sequence_length(self) -> int:
        """
        Return maximum sequence length supported by the model.
        
        Returns:
            Maximum number of tokens/characters the model can process
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the model is available and ready for use.
        
        Returns:
            True if model is loaded and ready, False otherwise
        """
        pass


class BatchProcessor(ABC):
    """
    Optimize batch processing interface.
    
    This interface defines batch processing strategies for efficient
    embedding generation. All implementations use direct pattern since
    they contain pure optimization algorithms without external dependencies.
    
    Architecture Pattern: Direct Implementation (pure algorithms)
    """
    
    @abstractmethod
    def process_batch(self, texts: List[str], batch_size: int) -> np.ndarray:
        """
        Process texts in batches for optimal throughput.
        
        Args:
            texts: List of text strings to process
            batch_size: Size of each processing batch
            
        Returns:
            numpy array of embeddings with shape (len(texts), embedding_dim)
            
        Raises:
            ValueError: If batch_size is invalid
            RuntimeError: If batch processing fails
        """
        pass
        
    @abstractmethod
    def optimize_batch_size(self, sample_texts: List[str]) -> int:
        """
        Determine optimal batch size based on sample texts and hardware.
        
        Args:
            sample_texts: Representative sample of texts to analyze
            
        Returns:
            Optimal batch size for the given hardware and text characteristics
        """
        pass
    
    @abstractmethod
    def get_batch_stats(self) -> Dict[str, Any]:
        """
        Get statistics about batch processing performance.
        
        Returns:
            Dictionary with metrics like average batch size, processing time, etc.
        """
        pass
    
    @abstractmethod
    def supports_streaming(self) -> bool:
        """
        Check if this processor supports streaming/incremental processing.
        
        Returns:
            True if streaming is supported, False otherwise
        """
        pass


class EmbeddingCache(ABC):
    """
    Cache computed embeddings interface.
    
    This interface defines caching strategies for avoiding recomputation
    of embeddings. Implementations follow different patterns based on
    the storage backend.
    
    Architecture Patterns:
    - Direct Implementation: In-memory cache
    - Adapter Pattern: External stores (Redis, disk)
    """
    
    @abstractmethod
    def get(self, text: str) -> Optional[np.ndarray]:
        """
        Retrieve cached embedding for text.
        
        Args:
            text: Text string to look up
            
        Returns:
            Cached embedding array or None if not found
            
        Raises:
            RuntimeError: If cache retrieval fails
        """
        pass
        
    @abstractmethod
    def put(self, text: str, embedding: np.ndarray) -> None:
        """
        Store embedding in cache.
        
        Args:
            text: Text string as cache key
            embedding: Embedding array to store
            
        Raises:
            ValueError: If text or embedding is invalid
            RuntimeError: If cache storage fails
        """
        pass
        
    @abstractmethod
    def invalidate(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern.
        
        Args:
            pattern: Pattern to match for invalidation (supports wildcards)
            
        Returns:
            Number of entries invalidated
            
        Raises:
            RuntimeError: If invalidation fails
        """
        pass
    
    @abstractmethod
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        
        Returns:
            Dictionary with hit rate, size, evictions, etc.
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """
        Clear all entries from the cache.
        
        Raises:
            RuntimeError: If cache clearing fails
        """
        pass
    
    @abstractmethod
    def get_cache_size(self) -> int:
        """
        Get current number of cached entries.
        
        Returns:
            Number of entries currently in cache
        """
        pass


class ConfigurableEmbedderComponent(ABC):
    """
    Base class for configurable embedder components.
    
    This provides common configuration and validation functionality
    that all embedder sub-components can inherit.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize component with configuration.
        
        Args:
            config: Component-specific configuration dictionary
        """
        self.config = config
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """
        Validate component configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        pass
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration.
        
        Returns:
            Configuration dictionary
        """
        return self.config.copy()
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update component configuration.
        
        Args:
            updates: Configuration updates to apply
            
        Raises:
            ValueError: If updated configuration is invalid
        """
        old_config = self.config.copy()
        self.config.update(updates)
        
        try:
            self._validate_config()
        except ValueError:
            # Restore old configuration if validation fails
            self.config = old_config
            raise


# Component validation result for health checks
class ComponentValidationResult:
    """Result of component validation/health check."""
    
    def __init__(self, is_valid: bool, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize validation result.
        
        Args:
            is_valid: Whether component passed validation
            message: Human-readable validation message
            details: Optional additional validation details
        """
        self.is_valid = is_valid
        self.message = message
        self.details = details or {}
    
    def __bool__(self) -> bool:
        """Allow boolean evaluation of validation result."""
        return self.is_valid
    
    def __str__(self) -> str:
        """String representation of validation result."""
        status = "VALID" if self.is_valid else "INVALID"
        return f"{status}: {self.message}"