"""
Modular Embedder Implementation.

This module implements the primary Embedder interface that coordinates
all embedding sub-components (model, batch processor, cache) through
a configurable architecture following the ModularDocumentProcessor pattern.

Architecture Notes:
- Implements Embedder interface from core.interfaces
- Coordinates sub-components via configuration-driven selection
- Follows adapter vs direct implementation patterns per specification
- Provides unified interface for embedding generation
- Includes comprehensive error handling and metrics
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import logging
import sys

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.core.interfaces import Embedder as EmbedderInterface, HealthStatus

# Forward declaration to avoid circular import
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.core.platform_orchestrator import PlatformOrchestrator
from .base import (
    EmbeddingModel, 
    BatchProcessor, 
    EmbeddingCache, 
    ConfigurableEmbedderComponent,
    ComponentValidationResult
)

# Import sub-component implementations
from .models.sentence_transformer_model import SentenceTransformerModel
from .batch_processors.dynamic_batch_processor import DynamicBatchProcessor
from .caches.memory_cache import MemoryCache

logger = logging.getLogger(__name__)


class ModularEmbedder(EmbedderInterface, ConfigurableEmbedderComponent):
    """
    Modular embedder with configurable sub-components.
    
    This embedder implements the Embedder interface while providing
    a modular architecture where embedding model, batch processing, and
    caching strategies can be configured independently.
    
    Features:
    - Configuration-driven sub-component selection
    - Multiple embedding provider support (extensible)
    - Comprehensive error handling and validation
    - Performance metrics and monitoring
    - Pluggable sub-component architecture
    
    Configuration Structure:
    {
        "model": {
            "type": "sentence_transformer",  # or "openai", "cohere"
            "config": {
                "model_name": "all-MiniLM-L6-v2",
                "device": "mps",
                "normalize_embeddings": true
            }
        },
        "batch_processor": {
            "type": "dynamic",
            "config": {
                "initial_batch_size": 32,
                "max_batch_size": 128,
                "optimize_for_memory": true
            }
        },
        "cache": {
            "type": "memory",  # or "redis", "disk"
            "config": {
                "max_entries": 100000,
                "max_memory_mb": 1024
            }
        }
    }
    
    Architecture Compliance:
    - EmbeddingModel: Mixed (Direct for local, Adapter for APIs)
    - BatchProcessor: Direct implementation (pure algorithms)
    - EmbeddingCache: Mixed (Direct for memory, Adapter for external stores)
    """
    
    # Sub-component type mappings
    _MODEL_TYPES = {
        "sentence_transformer": SentenceTransformerModel,
        # Future: "openai": OpenAIEmbeddingAdapter,
        # Future: "cohere": CohereEmbeddingAdapter,
    }
    
    _BATCH_PROCESSOR_TYPES = {
        "dynamic": DynamicBatchProcessor,
        # Future: "fixed": FixedBatchProcessor,
        # Future: "streaming": StreamingBatchProcessor,
    }
    
    _CACHE_TYPES = {
        "memory": MemoryCache,
        # Future: "redis": RedisCacheAdapter,
        # Future: "disk": DiskCacheAdapter,
    }
    
    def __init__(self, config: Dict[str, Any] = None, **kwargs):
        """
        Initialize modular embedder with sub-components.
        
        Args:
            config: Embedder configuration dictionary
            **kwargs: Alternative configuration parameters (for backward compatibility)
        """
        # Handle configuration - prioritize explicit config, fallback to kwargs
        if config is None:
            config = kwargs
        
        super().__init__(config)
        
        # Initialize sub-components in dependency order
        self.model = self._create_model()
        self.cache = self._create_cache()  
        self.batch_processor = self._create_batch_processor()  # Needs model reference
        
        # Performance tracking
        self._total_embeddings_generated = 0
        self._total_processing_time = 0.0
        self._cache_hits = 0
        self._cache_misses = 0
        self._created_time = time.time()
        
        # Platform services (initialized via initialize_services)
        self.platform: Optional['PlatformOrchestrator'] = None
        
        # Validate complete system
        validation_result = self.validate_components()
        if not validation_result.is_valid:
            raise RuntimeError(f"Component validation failed: {validation_result.message}")
        
        logger.info(f"ModularEmbedder initialized successfully with sub-components: "
                   f"model={self.model.__class__.__name__}, "
                   f"batch_processor={self.batch_processor.__class__.__name__}, "
                   f"cache={self.cache.__class__.__name__}")
    
    def _validate_config(self) -> None:
        """
        Validate embedder configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        required_sections = ["model", "batch_processor", "cache"]
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Validate each sub-component config
        for section in required_sections:
            section_config = self.config[section]
            if "type" not in section_config:
                raise ValueError(f"Missing 'type' in {section} configuration")
            if "config" not in section_config:
                raise ValueError(f"Missing 'config' in {section} configuration")
    
    def _create_model(self) -> EmbeddingModel:
        """
        Create embedding model sub-component.
        
        Returns:
            Configured EmbeddingModel instance
            
        Raises:
            ValueError: If model type is not supported
        """
        model_config = self.config["model"]
        model_type = model_config["type"]
        
        if model_type not in self._MODEL_TYPES:
            available_types = list(self._MODEL_TYPES.keys())
            raise ValueError(f"Unsupported model type '{model_type}'. Available: {available_types}")
        
        model_class = self._MODEL_TYPES[model_type]
        model_instance = model_class(model_config["config"])
        
        logger.debug(f"Created embedding model: {model_type} -> {model_class.__name__}")
        return model_instance
    
    def _create_batch_processor(self) -> BatchProcessor:
        """
        Create batch processor sub-component.
        
        Returns:
            Configured BatchProcessor instance
            
        Raises:
            ValueError: If batch processor type is not supported
        """
        batch_config = self.config["batch_processor"]
        batch_type = batch_config["type"]
        
        if batch_type not in self._BATCH_PROCESSOR_TYPES:
            available_types = list(self._BATCH_PROCESSOR_TYPES.keys())
            raise ValueError(f"Unsupported batch processor type '{batch_type}'. Available: {available_types}")
        
        batch_class = self._BATCH_PROCESSOR_TYPES[batch_type]
        
        # BatchProcessor needs reference to the embedding model
        batch_instance = batch_class(batch_config["config"], self.model)
        
        logger.debug(f"Created batch processor: {batch_type} -> {batch_class.__name__}")
        return batch_instance
    
    def _create_cache(self) -> EmbeddingCache:
        """
        Create embedding cache sub-component.
        
        Returns:
            Configured EmbeddingCache instance
            
        Raises:
            ValueError: If cache type is not supported
        """
        cache_config = self.config["cache"]
        cache_type = cache_config["type"]
        
        if cache_type not in self._CACHE_TYPES:
            available_types = list(self._CACHE_TYPES.keys())
            raise ValueError(f"Unsupported cache type '{cache_type}'. Available: {available_types}")
        
        cache_class = self._CACHE_TYPES[cache_type]
        cache_instance = cache_class(cache_config["config"])
        
        logger.debug(f"Created embedding cache: {cache_type} -> {cache_class.__name__}")
        return cache_instance
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using the modular architecture.
        
        This method coordinates all sub-components:
        1. Check cache for existing embeddings
        2. Use batch processor for optimal throughput on cache misses
        3. Store new embeddings in cache
        4. Return combined results
        
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
        
        start_time = time.time()
        
        try:
            # Step 1: Check cache for existing embeddings
            cached_embeddings = {}
            texts_to_compute = []
            
            for i, text in enumerate(texts):
                cached_embedding = self.cache.get(text)
                if cached_embedding is not None:
                    cached_embeddings[i] = cached_embedding
                    self._cache_hits += 1
                else:
                    texts_to_compute.append((i, text))
                    self._cache_misses += 1
            
            # Step 2: Generate embeddings for cache misses using batch processor
            new_embeddings = {}
            if texts_to_compute:
                texts_for_processing = [text for _, text in texts_to_compute]
                
                # Use batch processor for optimal throughput
                processed_embeddings = self.batch_processor.process_batch(
                    texts_for_processing, 
                    batch_size=32  # Will be optimized by batch processor
                )
                
                # Step 3: Store new embeddings in cache and collect results
                for j, (original_index, text) in enumerate(texts_to_compute):
                    embedding = processed_embeddings[j]
                    
                    # Store in cache
                    self.cache.put(text, embedding)
                    
                    # Store for result assembly
                    new_embeddings[original_index] = embedding
            
            # Step 4: Assemble final results in original order
            result_embeddings = []
            for i in range(len(texts)):
                if i in cached_embeddings:
                    embedding = cached_embeddings[i]
                else:
                    embedding = new_embeddings[i]
                
                # Convert to list format as required by interface
                result_embeddings.append(embedding.tolist())
            
            # Update performance statistics
            processing_time = time.time() - start_time
            self._total_embeddings_generated += len(texts)
            self._total_processing_time += processing_time
            
            # Track performance using platform services
            if self.platform:
                self.platform.track_component_performance(
                    self, 
                    "embedding_generation", 
                    {
                        "success": True,
                        "processing_time": processing_time,
                        "texts_count": len(texts),
                        "cache_hits": len(cached_embeddings),
                        "new_embeddings": len(new_embeddings),
                        "embedding_dimension": self.embedding_dim()
                    }
                )
            
            logger.debug(f"Generated {len(texts)} embeddings in {processing_time:.3f}s "
                        f"(cache hits: {len(cached_embeddings)}, computed: {len(new_embeddings)})")
            
            return result_embeddings
            
        except Exception as e:
            # Track failure using platform services
            if self.platform:
                processing_time = time.time() - start_time
                self.platform.track_component_performance(
                    self, 
                    "embedding_generation", 
                    {
                        "success": False,
                        "processing_time": processing_time,
                        "texts_count": len(texts),
                        "error": str(e)
                    }
                )
            
            logger.error(f"Embedding generation failed: {e}")
            raise RuntimeError(f"Failed to generate embeddings: {str(e)}") from e
    
    def embedding_dim(self) -> int:
        """
        Get the embedding dimension.
        
        Returns:
            Integer dimension of embeddings
        """
        return self.model.get_embedding_dim()
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about the embedder and its sub-components.
        
        Returns:
            Dictionary with embedder configuration and status
        """
        return {
            "component_type": "modular_embedder",
            "embedding_dimension": self.embedding_dim(),
            "model": {
                "type": self.config["model"]["type"],
                "info": self.model.get_model_info() if hasattr(self.model, 'get_model_info') else {}
            },
            "batch_processor": {
                "type": self.config["batch_processor"]["type"],
                "stats": self.batch_processor.get_batch_stats()
            },
            "cache": {
                "type": self.config["cache"]["type"],
                "stats": self.cache.get_cache_stats()
            },
            "performance": self.get_performance_stats(),
            "uptime_seconds": time.time() - self._created_time
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for the embedder.
        
        Returns:
            Dictionary with performance metrics
        """
        total_requests = self._cache_hits + self._cache_misses
        cache_hit_rate = self._cache_hits / total_requests if total_requests > 0 else 0.0
        
        avg_throughput = (
            self._total_embeddings_generated / self._total_processing_time 
            if self._total_processing_time > 0 else 0.0
        )
        
        return {
            "total_embeddings_generated": self._total_embeddings_generated,
            "total_processing_time": self._total_processing_time,
            "average_throughput": avg_throughput,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_hit_rate": cache_hit_rate,
            "uptime_seconds": time.time() - self._created_time
        }
    
    def supports_batching(self) -> bool:
        """
        Check if this embedder supports batch processing.
        
        Returns:
            True, as this implementation supports efficient batch processing
        """
        return True
    
    def validate_components(self) -> ComponentValidationResult:
        """
        Validate all sub-components are properly configured and functional.
        
        Returns:
            ComponentValidationResult with validation status
        """
        try:
            # Test model
            if not self.model.is_available():
                return ComponentValidationResult(
                    False, 
                    "Embedding model is not available",
                    {"model_type": self.config["model"]["type"]}
                )
            
            # Test model with dummy data
            try:
                test_embedding = self.model.encode(["test"])
                if test_embedding.size == 0:
                    return ComponentValidationResult(
                        False,
                        "Model produced empty embedding",
                        {"model_type": self.config["model"]["type"]}
                    )
            except Exception as e:
                return ComponentValidationResult(
                    False,
                    f"Model encoding test failed: {e}",
                    {"model_type": self.config["model"]["type"]}
                )
            
            # Test cache
            try:
                # Test cache operations
                test_embedding = np.array([1.0, 2.0, 3.0])
                self.cache.put("test_key", test_embedding)
                retrieved = self.cache.get("test_key")
                if retrieved is None or not np.array_equal(retrieved, test_embedding):
                    return ComponentValidationResult(
                        False,
                        "Cache put/get operations failed",
                        {"cache_type": self.config["cache"]["type"]}
                    )
                # Clean up test data
                self.cache.invalidate("test_key")
            except Exception as e:
                return ComponentValidationResult(
                    False,
                    f"Cache operations test failed: {e}",
                    {"cache_type": self.config["cache"]["type"]}
                )
            
            # Test batch processor
            if not hasattr(self.batch_processor, 'process_batch'):
                return ComponentValidationResult(
                    False,
                    "Batch processor missing required methods",
                    {"batch_processor_type": self.config["batch_processor"]["type"]}
                )
            
            return ComponentValidationResult(
                True,
                "All components validated successfully",
                {
                    "model_type": self.config["model"]["type"],
                    "batch_processor_type": self.config["batch_processor"]["type"],
                    "cache_type": self.config["cache"]["type"],
                    "embedding_dimension": self.embedding_dim()
                }
            )
            
        except Exception as e:
            return ComponentValidationResult(
                False,
                f"Component validation failed with error: {e}",
                {"error_type": type(e).__name__}
            )
    
    def get_sub_components(self) -> Dict[str, Any]:
        """
        Get information about all sub-components for factory logging.
        
        Returns:
            Dictionary with sub-component details
        """
        return {
            "components": {
                "model": {
                    "type": self.config["model"]["type"],
                    "class": self.model.__class__.__name__,
                    "available": self.model.is_available()
                },
                "batch_processor": {
                    "type": self.config["batch_processor"]["type"],
                    "class": self.batch_processor.__class__.__name__,
                    "supports_streaming": self.batch_processor.supports_streaming()
                },
                "cache": {
                    "type": self.config["cache"]["type"],
                    "class": self.cache.__class__.__name__,
                    "size": self.cache.get_cache_size()
                }
            },
            "architecture": "modular_embedder",
            "total_sub_components": 3
        }
    
    # Standard ComponentBase interface implementation
    def initialize_services(self, platform: 'PlatformOrchestrator') -> None:
        """Initialize platform services for the component.
        
        Args:
            platform: PlatformOrchestrator instance providing services
        """
        self.platform = platform
        logger.info("ModularEmbedder initialized with platform services")

    def get_health_status(self) -> HealthStatus:
        """Get the current health status of the component.
        
        Returns:
            HealthStatus object with component health information
        """
        if self.platform:
            return self.platform.check_component_health(self)
        
        # Fallback if platform services not initialized
        validation_result = self.validate_components()
        
        return HealthStatus(
            is_healthy=validation_result.is_valid,
            status="healthy" if validation_result.is_valid else "unhealthy",
            details={
                "validation_message": validation_result.message,
                "validation_details": validation_result.details,
                "sub_components": self.get_sub_components(),
                "performance": self.get_performance_stats()
            }
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get component-specific metrics.
        
        Returns:
            Dictionary containing component metrics
        """
        if self.platform:
            return self.platform.collect_component_metrics(self)
        
        # Fallback if platform services not initialized
        return {
            "performance": self.get_performance_stats(),
            "model_info": self.get_model_info(),
            "sub_components": self.get_sub_components(),
            "cache_stats": {
                "hits": self._cache_hits,
                "misses": self._cache_misses,
                "hit_rate": self._cache_hits / max(1, self._cache_hits + self._cache_misses)
            }
        }

    def get_capabilities(self) -> List[str]:
        """Get list of component capabilities.
        
        Returns:
            List of capability strings
        """
        capabilities = [
            "text_embedding",
            "batch_processing",
            "caching",
            "modular_architecture",
            "performance_optimization",
            "streaming_support"
        ]
        
        # Add model-specific capabilities
        if self.model:
            capabilities.append(f"model_{self.config['model']['type']}")
            
        # Add batch processor capabilities
        if self.batch_processor:
            capabilities.append(f"batch_processor_{self.config['batch_processor']['type']}")
            if self.batch_processor.supports_streaming():
                capabilities.append("streaming_processing")
        
        # Add cache capabilities
        if self.cache:
            capabilities.append(f"cache_{self.config['cache']['type']}")
        
        return capabilities
    
    def cleanup(self) -> None:
        """Clean up resources used by sub-components."""
        try:
            # Clear cache
            if hasattr(self.cache, 'clear'):
                self.cache.clear()
            
            # Clean up model cache if available
            if hasattr(self.model, 'clear_model_cache'):
                self.model.clear_model_cache()
            
            # Reset batch processor stats if available
            if hasattr(self.batch_processor, 'reset_performance_stats'):
                self.batch_processor.reset_performance_stats()
            
            logger.info("ModularEmbedder cleanup completed")
            
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
    
    def __del__(self):
        """Cleanup on destruction."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore errors during destruction