"""
Cross-Encoder Model Management for Neural Reranking.

This module provides sophisticated model management capabilities for neural
reranking including multi-backend support, lazy loading, caching, and
performance optimization for cross-encoder transformer models.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Union
import threading
from dataclasses import dataclass
import numpy as np

from .config.reranking_config import EnhancedNeuralRerankingConfig, ModelConfig

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Information about a loaded model."""
    name: str
    backend: str
    device: str
    loaded: bool = False
    load_time: float = 0.0
    inference_count: int = 0
    total_inference_time: float = 0.0
    last_used: float = 0.0
    memory_usage_mb: float = 0.0
    error_count: int = 0


class ModelManager:
    """
    Manager for individual cross-encoder models.
    
    Handles model loading, caching, and lifecycle management for a single
    cross-encoder model with support for multiple backends.
    """
    
    def __init__(self, name: str, config: ModelConfig):
        """
        Initialize model manager.
        
        Args:
            name: Model identifier
            config: Model configuration
        """
        self.name = name
        self.config = config
        self.model = None
        self.info = ModelInfo(
            name=name,
            backend=config.backend,
            device=config.device
        )
        self._lock = threading.Lock()
        
        logger.debug(f"ModelManager created for {name} ({config.backend})")
    
    def load_model(self) -> bool:
        """
        Load the model lazily.
        
        Returns:
            True if model loaded successfully
        """
        with self._lock:
            if self.info.loaded:
                return True
            
            try:
                start_time = time.time()
                
                if self.config.backend == "sentence_transformers":
                    self.model = self._load_sentence_transformer()
                elif self.config.backend == "tensorflow":
                    self.model = self._load_tensorflow_model()
                elif self.config.backend == "keras":
                    self.model = self._load_keras_model()
                else:
                    raise ValueError(f"Unsupported backend: {self.config.backend}")
                
                self.info.load_time = time.time() - start_time
                self.info.loaded = True
                self.info.last_used = time.time()
                
                logger.info(f"Model {self.name} loaded successfully in {self.info.load_time:.2f}s")
                return True
                
            except Exception as e:
                self.info.error_count += 1
                logger.error(f"Failed to load model {self.name}: {e}")
                return False
    
    def _load_sentence_transformer(self):
        """Load model using sentence-transformers backend."""
        try:
            from sentence_transformers import CrossEncoder
            
            model = CrossEncoder(
                self.config.name,
                device=self._get_device(),
                trust_remote_code=self.config.trust_remote_code,
                revision=self.config.revision
            )
            
            # Apply optimizations if configured
            if self.config.enable_quantization:
                model = self._apply_quantization(model)
            
            return model
            
        except ImportError:
            raise ImportError("sentence-transformers not available")
    
    def _load_tensorflow_model(self):
        """Load model using TensorFlow backend."""
        try:
            import tensorflow as tf
            from transformers import TFAutoModelForSequenceClassification, AutoTokenizer
            
            model = TFAutoModelForSequenceClassification.from_pretrained(
                self.config.name,
                trust_remote_code=self.config.trust_remote_code,
                revision=self.config.revision
            )
            
            tokenizer = AutoTokenizer.from_pretrained(
                self.config.name,
                trust_remote_code=self.config.trust_remote_code,
                revision=self.config.revision
            )
            
            # Wrap in a container for consistent interface
            return TensorFlowModelWrapper(model, tokenizer, self.config)
            
        except ImportError:
            raise ImportError("TensorFlow not available")
    
    def _load_keras_model(self):
        """Load model using Keras backend."""
        try:
            import keras
            from transformers import TFAutoModelForSequenceClassification, AutoTokenizer
            
            # Load using TensorFlow but optimize for Keras
            model = TFAutoModelForSequenceClassification.from_pretrained(
                self.config.name,
                trust_remote_code=self.config.trust_remote_code,
                revision=self.config.revision
            )
            
            tokenizer = AutoTokenizer.from_pretrained(
                self.config.name,
                trust_remote_code=self.config.trust_remote_code,
                revision=self.config.revision
            )
            
            return KerasModelWrapper(model, tokenizer, self.config)
            
        except ImportError:
            raise ImportError("Keras not available")
    
    def _get_device(self) -> str:
        """Get the appropriate device for model loading."""
        if self.config.device == "auto":
            try:
                import torch
                if torch.cuda.is_available():
                    return "cuda"
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    return "mps"
                else:
                    return "cpu"
            except ImportError:
                return "cpu"
        
        return self.config.device
    
    def _apply_quantization(self, model):
        """Apply quantization optimizations if available."""
        try:
            # This would need to be implemented based on the specific
            # quantization library being used
            logger.info(f"Quantization requested for {self.name} but not implemented")
            return model
        except Exception as e:
            logger.warning(f"Quantization failed for {self.name}: {e}")
            return model
    
    def predict(self, query_doc_pairs: List[List[str]]) -> List[float]:
        """
        Predict relevance scores for query-document pairs.
        
        Args:
            query_doc_pairs: List of [query, document] pairs
            
        Returns:
            List of relevance scores
        """
        if not self.info.loaded:
            if not self.load_model():
                raise RuntimeError(f"Model {self.name} failed to load")
        
        start_time = time.time()
        
        try:
            if self.config.backend == "sentence_transformers":
                scores = self.model.predict(query_doc_pairs)
            else:
                # For TensorFlow/Keras models, use wrapper predict method
                scores = self.model.predict(query_doc_pairs)
            
            # Update statistics
            self.info.inference_count += 1
            self.info.total_inference_time += time.time() - start_time
            self.info.last_used = time.time()
            
            return [float(score) for score in scores]
            
        except Exception as e:
            self.info.error_count += 1
            logger.error(f"Inference failed for model {self.name}: {e}")
            raise
    
    def get_info(self) -> ModelInfo:
        """Get model information."""
        return self.info
    
    def unload_model(self) -> None:
        """Unload the model to free memory."""
        with self._lock:
            if self.info.loaded:
                self.model = None
                self.info.loaded = False
                logger.info(f"Model {self.name} unloaded")
    
    def get_avg_inference_time(self) -> float:
        """Get average inference time in seconds."""
        if self.info.inference_count == 0:
            return 0.0
        return self.info.total_inference_time / self.info.inference_count


class TensorFlowModelWrapper:
    """Wrapper for TensorFlow models to provide consistent interface."""
    
    def __init__(self, model, tokenizer, config: ModelConfig):
        self.model = model
        self.tokenizer = tokenizer
        self.config = config
    
    def predict(self, query_doc_pairs: List[List[str]]) -> List[float]:
        """Predict scores using TensorFlow model."""
        import tensorflow as tf
        
        # Tokenize inputs
        inputs = self.tokenizer(
            query_doc_pairs,
            padding=True,
            truncation=True,
            max_length=self.config.max_length,
            return_tensors="tf"
        )
        
        # Run inference
        outputs = self.model(**inputs)
        
        # Extract scores (assuming classification head outputs logits)
        logits = outputs.logits
        
        # Apply sigmoid to get probabilities (for binary classification)
        scores = tf.nn.sigmoid(logits).numpy()
        
        # If multi-class, take the positive class probability
        if scores.shape[1] > 1:
            scores = scores[:, 1]  # Assume positive class is at index 1
        else:
            scores = scores.flatten()
        
        return scores.tolist()


class KerasModelWrapper:
    """Wrapper for Keras models to provide consistent interface."""
    
    def __init__(self, model, tokenizer, config: ModelConfig):
        self.model = model
        self.tokenizer = tokenizer
        self.config = config
    
    def predict(self, query_doc_pairs: List[List[str]]) -> List[float]:
        """Predict scores using Keras model."""
        import tensorflow as tf
        
        # Tokenize inputs
        inputs = self.tokenizer(
            query_doc_pairs,
            padding=True,
            truncation=True,
            max_length=self.config.max_length,
            return_tensors="tf"
        )
        
        # Run inference using Keras API
        outputs = self.model(inputs)
        
        # Extract scores
        logits = outputs.logits if hasattr(outputs, 'logits') else outputs
        
        # Apply sigmoid for probabilities
        scores = tf.nn.sigmoid(logits).numpy()
        
        # Handle multi-class vs binary classification
        if len(scores.shape) > 1 and scores.shape[1] > 1:
            scores = scores[:, 1]  # Positive class
        else:
            scores = scores.flatten()
        
        return scores.tolist()


class CrossEncoderModels:
    """
    Cross-encoder model management system.
    
    Manages multiple cross-encoder models with lazy loading, caching,
    and performance optimization. Supports multiple backends including
    sentence-transformers, TensorFlow, and Keras.
    """
    
    def __init__(self, config: EnhancedNeuralRerankingConfig):
        """
        Initialize cross-encoder models manager.
        
        Args:
            config: Enhanced neural reranking configuration
        """
        self.config = config
        self.managers: Dict[str, ModelManager] = {}
        self.initialized = False
        
        # Initialize model managers
        for name, model_config in config.models.items():
            self.managers[name] = ModelManager(name, model_config)
        
        logger.info(f"CrossEncoderModels initialized with {len(self.managers)} models")
    
    def initialize(self) -> None:
        """Initialize the model management system."""
        if self.initialized:
            return
        
        # Pre-load default model if caching is enabled
        if self.config.performance.enable_caching:
            default_manager = self.managers.get(self.config.default_model)
            if default_manager:
                default_manager.load_model()
        
        self.initialized = True
        logger.info("CrossEncoderModels initialization completed")
    
    def get_model(self, model_name: str) -> Optional[ModelManager]:
        """
        Get a model manager by name.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model manager or None if not found
        """
        return self.managers.get(model_name)
    
    def predict(self, model_name: str, query_doc_pairs: List[List[str]]) -> List[float]:
        """
        Predict scores using a specific model.
        
        Args:
            model_name: Name of the model to use
            query_doc_pairs: List of [query, document] pairs
            
        Returns:
            List of relevance scores
        """
        manager = self.get_model(model_name)
        if manager is None:
            raise ValueError(f"Model {model_name} not found")
        
        return manager.predict(query_doc_pairs)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status of all models.
        
        Returns:
            Dictionary with model status information
        """
        status = {}
        
        for name, manager in self.managers.items():
            info = manager.get_info()
            status[name] = {
                "loaded": info.loaded,
                "backend": info.backend,
                "device": info.device,
                "inference_count": info.inference_count,
                "avg_inference_time_ms": manager.get_avg_inference_time() * 1000,
                "error_count": info.error_count,
                "last_used": info.last_used
            }
        
        return status
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get detailed performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        stats = {
            "total_models": len(self.managers),
            "loaded_models": sum(1 for m in self.managers.values() if m.info.loaded),
            "total_inferences": sum(m.info.inference_count for m in self.managers.values()),
            "total_errors": sum(m.info.error_count for m in self.managers.values()),
            "models": {}
        }
        
        for name, manager in self.managers.items():
            info = manager.get_info()
            stats["models"][name] = {
                "inference_count": info.inference_count,
                "total_time_ms": info.total_inference_time * 1000,
                "avg_time_ms": manager.get_avg_inference_time() * 1000,
                "error_count": info.error_count,
                "load_time_ms": info.load_time * 1000
            }
        
        return stats
    
    def cleanup(self) -> None:
        """Clean up all loaded models."""
        for manager in self.managers.values():
            manager.unload_model()
        
        logger.info("CrossEncoderModels cleanup completed")
    
    def reload_model(self, model_name: str) -> bool:
        """
        Reload a specific model.
        
        Args:
            model_name: Name of the model to reload
            
        Returns:
            True if reload was successful
        """
        manager = self.get_model(model_name)
        if manager is None:
            return False
        
        manager.unload_model()
        return manager.load_model()
    
    def get_memory_usage(self) -> Dict[str, float]:
        """
        Get memory usage for all models.
        
        Returns:
            Dictionary with memory usage in MB
        """
        memory_usage = {}
        
        for name, manager in self.managers.items():
            # This would need to be implemented with actual memory profiling
            # For now, we'll return placeholder values
            if manager.info.loaded:
                memory_usage[name] = manager.info.memory_usage_mb
            else:
                memory_usage[name] = 0.0
        
        return memory_usage