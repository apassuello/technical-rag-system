"""
SentenceTransformer embedding model implementation.

This module provides a direct implementation of the EmbeddingModel interface
for SentenceTransformer models, extracted from the shared_utils functionality
to make the embedder component self-contained.

Features:
- MPS acceleration for Apple Silicon
- Efficient model caching and reuse
- Configurable device selection
- Embedding normalization support
- Memory-efficient processing
"""

import torch
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import logging
import os
import tempfile
from pathlib import Path
import sys

# Add project root for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from ..base import EmbeddingModel, ConfigurableEmbedderComponent

logger = logging.getLogger(__name__)


class SentenceTransformerModel(EmbeddingModel, ConfigurableEmbedderComponent):
    """
    Direct implementation of SentenceTransformer embedding model.
    
    This class provides a self-contained implementation of the EmbeddingModel
    interface using SentenceTransformers, with MPS acceleration support and
    efficient model management.
    
    Configuration:
    {
        "model_name": "sentence-transformers/all-MiniLM-L6-v2",
        "device": "auto",  # or "mps", "cuda", "cpu"
        "normalize_embeddings": true,
        "cache_folder": null,  # or path to cache directory
        "trust_remote_code": false
    }
    
    Performance Features:
    - Apple Silicon MPS acceleration
    - Model caching to avoid reloading
    - Memory-efficient inference mode
    - Configurable device selection
    """
    
    # Class-level model cache to avoid reloading
    _model_cache: Dict[str, SentenceTransformer] = {}
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize SentenceTransformer model.
        
        Args:
            config: Model configuration dictionary
        """
        super().__init__(config)
        
        self.model_name = config.get("model_name", "sentence-transformers/all-MiniLM-L6-v2")
        self.device = self._determine_device(config.get("device", "auto"))
        self.normalize_embeddings = config.get("normalize_embeddings", True)
        self.cache_folder = config.get("cache_folder")
        self.trust_remote_code = config.get("trust_remote_code", False)
        
        # Load model
        self._model = self._load_model()
        self._embedding_dim = None
        self._max_seq_length = None
        
        logger.info(f"SentenceTransformerModel initialized: {self.model_name} on {self.device}")
    
    def _validate_config(self) -> None:
        """
        Validate model configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        required_keys = ["model_name"]
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required configuration key: {key}")
        
        # Validate device
        device = self.config.get("device", "auto")
        valid_devices = ["auto", "cpu", "cuda", "mps"]
        if device not in valid_devices:
            raise ValueError(f"Invalid device '{device}'. Must be one of: {valid_devices}")
        
        # Validate model name
        model_name = self.config["model_name"]
        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError("model_name must be a non-empty string")
    
    def _determine_device(self, device_config: str) -> str:
        """
        Determine the best device to use based on configuration and availability.
        
        Args:
            device_config: Device configuration ("auto", "mps", "cuda", "cpu")
            
        Returns:
            Device string to use
        """
        if device_config == "auto":
            # Auto-detect best available device
            if torch.backends.mps.is_available() and torch.backends.mps.is_built():
                return "mps"
            elif torch.cuda.is_available():
                return "cuda"
            else:
                return "cpu"
        else:
            # Use specified device (validation happens in _validate_config)
            return device_config
    
    def _load_model(self) -> SentenceTransformer:
        """
        Load SentenceTransformer model with caching.
        
        Returns:
            Loaded SentenceTransformer model
            
        Raises:
            RuntimeError: If model loading fails
        """
        cache_key = f"{self.model_name}:{self.device}"
        
        # Check cache first
        if cache_key in self._model_cache:
            logger.debug(f"Using cached model: {cache_key}")
            return self._model_cache[cache_key]
        
        try:
            # Load model with custom cache folder if specified
            if self.cache_folder:
                cache_dir = Path(self.cache_folder)
                cache_dir.mkdir(parents=True, exist_ok=True)
                model = SentenceTransformer(
                    self.model_name,
                    cache_folder=str(cache_dir),
                    trust_remote_code=self.trust_remote_code
                )
            else:
                # Use default cache behavior with fallback
                try:
                    model = SentenceTransformer(
                        self.model_name,
                        trust_remote_code=self.trust_remote_code
                    )
                except Exception as e:
                    # Fallback to explicit cache directory
                    cache_dir = os.environ.get('SENTENCE_TRANSFORMERS_HOME', os.path.join(tempfile.gettempdir(), '.cache', 'sentence-transformers'))
                    os.makedirs(cache_dir, exist_ok=True)
                    model = SentenceTransformer(
                        self.model_name,
                        cache_folder=cache_dir,
                        trust_remote_code=self.trust_remote_code
                    )
            
            # Move to device and set to eval mode
            model = model.to(self.device)
            model.eval()
            
            # Cache the model
            self._model_cache[cache_key] = model
            
            logger.info(f"Loaded model {self.model_name} on device {self.device}")
            return model
            
        except Exception as e:
            raise RuntimeError(f"Failed to load SentenceTransformer model '{self.model_name}': {e}") from e
    
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
        if not texts:
            raise ValueError("Cannot encode empty text list")
        
        try:
            with torch.no_grad():
                embeddings = self._model.encode(
                    texts,
                    convert_to_numpy=True,
                    normalize_embeddings=self.normalize_embeddings,
                    batch_size=32,  # Default batch size, will be overridden by BatchProcessor
                    show_progress_bar=False
                ).astype(np.float32)
            
            # Cache embedding dimension on first use
            if self._embedding_dim is None:
                self._embedding_dim = embeddings.shape[1]
            
            return embeddings
            
        except Exception as e:
            raise RuntimeError(f"Failed to encode texts: {e}") from e
    
    def get_model_name(self) -> str:
        """
        Return model identifier.
        
        Returns:
            String identifier for the embedding model
        """
        return self.model_name
    
    def get_embedding_dim(self) -> int:
        """
        Return embedding dimension.
        
        Returns:
            Integer dimension of embeddings produced by this model
        """
        if self._embedding_dim is None:
            # Get dimension by encoding a dummy text
            dummy_embedding = self.encode(["test"])
            self._embedding_dim = dummy_embedding.shape[1]
        
        return self._embedding_dim
    
    def get_max_sequence_length(self) -> int:
        """
        Return maximum sequence length supported by the model.
        
        Returns:
            Maximum number of tokens the model can process
        """
        if self._max_seq_length is None:
            try:
                # Get max sequence length from model
                self._max_seq_length = self._model.get_max_seq_length()
            except AttributeError:
                # Fallback for models without this method
                self._max_seq_length = 512  # Common default
                logger.warning(f"Could not determine max sequence length for {self.model_name}, using default: 512")
        
        return self._max_seq_length
    
    def is_available(self) -> bool:
        """
        Check if the model is available and ready for use.
        
        Returns:
            True if model is loaded and ready, False otherwise
        """
        try:
            return self._model is not None and hasattr(self._model, 'encode')
        except Exception:
            return False
    
    def get_device_info(self) -> Dict[str, Any]:
        """
        Get information about the device being used.
        
        Returns:
            Dictionary with device information
        """
        device_info = {
            "device": self.device,
            "device_available": True
        }
        
        if self.device == "mps":
            device_info.update({
                "mps_available": torch.backends.mps.is_available(),
                "mps_built": torch.backends.mps.is_built()
            })
        elif self.device == "cuda":
            device_info.update({
                "cuda_available": torch.cuda.is_available(),
                "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0
            })
        
        return device_info
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get comprehensive model information.
        
        Returns:
            Dictionary with model configuration and status
        """
        return {
            "model_name": self.model_name,
            "embedding_dim": self.get_embedding_dim(),
            "max_sequence_length": self.get_max_sequence_length(),
            "device": self.device,
            "normalize_embeddings": self.normalize_embeddings,
            "is_available": self.is_available(),
            "cache_folder": self.cache_folder,
            "trust_remote_code": self.trust_remote_code,
            "component_type": "sentence_transformer_model"
        }
    
    @classmethod
    def clear_model_cache(cls) -> None:
        """Clear the model cache to free memory."""
        cls._model_cache.clear()
        logger.info("SentenceTransformer model cache cleared")
    
    @classmethod
    def get_cache_info(cls) -> Dict[str, Any]:
        """
        Get information about the model cache.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            "cached_models": list(cls._model_cache.keys()),
            "cache_size": len(cls._model_cache)
        }