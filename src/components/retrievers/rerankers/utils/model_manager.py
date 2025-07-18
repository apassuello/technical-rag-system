"""
Model Management for Neural Reranking.

This module provides sophisticated model management capabilities for neural
reranking including multi-backend support, lazy loading, caching, and
performance optimization for cross-encoder transformer models.

Simplified from reranking/cross_encoder_models.py for integration with
the enhanced neural reranker in the rerankers/ component.
"""

import logging
import time
import os
from typing import Dict, List, Optional, Any, Union
import threading
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for individual neural reranking models."""
    
    # Model identification
    name: str = "cross-encoder/ms-marco-MiniLM-L6-v2"
    backend: str = "sentence_transformers"  # "sentence_transformers", "tensorflow", "keras", "huggingface_api"
    model_type: str = "cross_encoder"  # "cross_encoder", "bi_encoder", "ensemble"
    
    # Model parameters
    max_length: int = 512
    device: str = "auto"  # "auto", "cpu", "cuda", "mps"
    cache_size: int = 1000
    
    # Performance settings
    batch_size: int = 16
    optimization_level: str = "balanced"  # "speed", "balanced", "quality"
    enable_quantization: bool = False
    
    # Model-specific settings
    trust_remote_code: bool = False
    local_files_only: bool = False
    revision: Optional[str] = None
    
    # HuggingFace API settings (for backend="huggingface_api")
    api_token: Optional[str] = None
    timeout: int = 30
    fallback_to_local: bool = True
    max_candidates: int = 100
    score_threshold: float = 0.0


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
        self.tokenizer = None
        self._lock = threading.Lock()
        
        self.info = ModelInfo(
            name=name,
            backend=config.backend,
            device=config.device
        )
        
        logger.info(f"ModelManager created for {name} ({config.backend})")
    
    def load_model(self) -> bool:
        """
        Load the model if not already loaded.
        
        Returns:
            True if model loaded successfully
        """
        with self._lock:
            if self.info.loaded:
                return True
            
            try:
                start_time = time.time()
                
                if self.config.backend == "sentence_transformers":
                    self._load_sentence_transformer()
                elif self.config.backend == "huggingface_api":
                    self._load_huggingface_api()
                else:
                    raise ValueError(f"Unsupported backend: {self.config.backend}")
                
                load_time = time.time() - start_time
                self.info.load_time = load_time
                self.info.loaded = True
                self.info.last_used = time.time()
                
                logger.info(f"Model {self.name} loaded in {load_time:.2f}s")
                return True
                
            except Exception as e:
                logger.error(f"Failed to load model {self.name}: {e}")
                self.info.error_count += 1
                return False
    
    def _resolve_device(self) -> str:
        """
        Resolve 'auto' device to appropriate device for current system.
        
        Returns:
            Resolved device string ('cpu', 'cuda', 'mps', etc.)
        """
        if self.config.device != "auto":
            return self.config.device
        
        try:
            import torch
            
            # Check for MPS (Metal Performance Shaders) on Apple Silicon
            if torch.backends.mps.is_available() and torch.backends.mps.is_built():
                return "mps"
            
            # Check for CUDA
            if torch.cuda.is_available():
                return "cuda"
            
            # Fall back to CPU
            return "cpu"
            
        except ImportError:
            # If torch is not available, default to CPU
            return "cpu"
    
    def _load_sentence_transformer(self):
        """Load model using sentence-transformers."""
        try:
            from sentence_transformers import CrossEncoder
            
            # Resolve device if set to 'auto'
            device = self._resolve_device()
            
            self.model = CrossEncoder(
                self.config.name,
                max_length=self.config.max_length,
                device=device,
                trust_remote_code=self.config.trust_remote_code
            )
            
            logger.debug(f"Sentence transformer model loaded: {self.config.name} on device: {device}")
            
        except ImportError:
            raise ImportError("sentence-transformers library not available")
        except Exception as e:
            raise RuntimeError(f"Failed to load sentence transformer: {e}")
    
    def _load_huggingface_api(self):
        """Load model using HuggingFace Inference API."""
        try:
            from huggingface_hub import InferenceClient
            
            # Get API token from config or environment
            api_token = (
                self.config.api_token or 
                os.getenv("HF_TOKEN") or 
                os.getenv("HUGGINGFACE_API_TOKEN") or
                os.getenv("HF_API_TOKEN")
            )
            
            if not api_token:
                raise ValueError("HuggingFace API token required for huggingface_api backend")
            
            # Create inference client
            self.model = InferenceClient(token=api_token)
            self.api_model_name = self.config.name
            
            logger.debug(f"HuggingFace API client initialized for model: {self.config.name}")
            
        except ImportError:
            raise ImportError("huggingface_hub library not available. Install with: pip install huggingface-hub")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize HuggingFace API client: {e}")
    
    def predict(self, query_doc_pairs: List[List[str]]) -> List[float]:
        """
        Generate predictions for query-document pairs.
        
        Args:
            query_doc_pairs: List of [query, document] pairs
            
        Returns:
            List of relevance scores
        """
        if not self.info.loaded and not self.load_model():
            raise RuntimeError(f"Model {self.name} not available")
        
        start_time = time.time()
        
        try:
            if self.config.backend == "huggingface_api":
                scores = self._predict_api(query_doc_pairs)
            else:
                scores = self._predict_local(query_doc_pairs)
            
            # Update statistics
            inference_time = time.time() - start_time
            self.info.inference_count += 1
            self.info.total_inference_time += inference_time
            self.info.last_used = time.time()
            
            return scores
            
        except Exception as e:
            self.info.error_count += 1
            logger.error(f"Model prediction failed for {self.name}: {e}")
            
            # Try fallback to local if API fails and fallback is enabled
            if self.config.backend == "huggingface_api" and self.config.fallback_to_local:
                logger.warning(f"API prediction failed, attempting fallback to local model")
                try:
                    return self._fallback_to_local(query_doc_pairs)
                except Exception as fallback_error:
                    logger.error(f"Fallback to local model also failed: {fallback_error}")
            
            raise
    
    def _predict_local(self, query_doc_pairs: List[List[str]]) -> List[float]:
        """
        Generate predictions using local model.
        
        Args:
            query_doc_pairs: List of [query, document] pairs
            
        Returns:
            List of relevance scores
        """
        scores = self.model.predict(query_doc_pairs)
        
        # Convert to list if numpy array
        if hasattr(scores, 'tolist'):
            scores = scores.tolist()
        
        return scores
    
    def _predict_api(self, query_doc_pairs: List[List[str]]) -> List[float]:
        """
        Generate predictions using HuggingFace API.
        
        Args:
            query_doc_pairs: List of [query, document] pairs
            
        Returns:
            List of relevance scores
        """
        # Filter by max_candidates if specified
        if self.config.max_candidates > 0 and len(query_doc_pairs) > self.config.max_candidates:
            query_doc_pairs = query_doc_pairs[:self.config.max_candidates]
            logger.debug(f"Filtered to {self.config.max_candidates} candidates for API efficiency")
        
        # Group by query for efficient batch processing
        query_groups = {}
        for i, (query, document) in enumerate(query_doc_pairs):
            if query not in query_groups:
                query_groups[query] = []
            query_groups[query].append((i, document))
        
        # Process each query group
        all_scores = [0.0] * len(query_doc_pairs)
        
        for query, doc_pairs in query_groups.items():
            try:
                # Prepare documents for this query
                documents = []
                indices = []
                
                for idx, document in doc_pairs:
                    # Truncate document if too long
                    if len(document) > self.config.max_length:
                        document = document[:self.config.max_length - 50] + "..."
                    documents.append(document)
                    indices.append(idx)
                
                # Use HuggingFace API for cross-encoder text ranking
                # Format: {"inputs": {"source_sentence": "query", "sentences": ["doc1", "doc2", ...]}}
                import requests
                
                api_url = f"https://api-inference.huggingface.co/models/{self.api_model_name}"
                headers = {"Authorization": f"Bearer {self.config.api_token}"}
                
                payload = {
                    "inputs": {
                        "source_sentence": query,
                        "sentences": documents
                    }
                }
                
                response = requests.post(api_url, headers=headers, json=payload, timeout=self.config.timeout)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Extract scores from response
                    if isinstance(result, list) and len(result) == len(documents):
                        for i, score in enumerate(result):
                            if isinstance(score, dict) and 'score' in score:
                                all_scores[indices[i]] = float(score['score'])
                            elif isinstance(score, (int, float)):
                                all_scores[indices[i]] = float(score)
                            else:
                                all_scores[indices[i]] = 0.0
                    else:
                        logger.warning(f"Unexpected API response format: {result}")
                        for idx in indices:
                            all_scores[idx] = 0.0
                else:
                    logger.warning(f"API request failed: {response.status_code} - {response.text}")
                    for idx in indices:
                        all_scores[idx] = 0.0
                
            except Exception as e:
                logger.warning(f"API prediction failed for query '{query}': {e}")
                for idx in indices:
                    all_scores[idx] = 0.0
        
        # Apply score threshold filtering
        if self.config.score_threshold > 0:
            all_scores = [max(score, self.config.score_threshold) for score in all_scores]
        
        return all_scores
    
    def _fallback_to_local(self, query_doc_pairs: List[List[str]]) -> List[float]:
        """
        Fallback to local model when API fails.
        
        Args:
            query_doc_pairs: List of [query, document] pairs
            
        Returns:
            List of relevance scores
        """
        logger.info("Attempting fallback to local sentence-transformers model")
        
        # Temporarily switch to local backend
        original_backend = self.config.backend
        self.config.backend = "sentence_transformers"
        
        try:
            # Unload API client
            self.model = None
            self.info.loaded = False
            
            # Load local model
            if self.load_model():
                scores = self._predict_local(query_doc_pairs)
                logger.info("Successfully fell back to local model")
                return scores
            else:
                raise RuntimeError("Failed to load local fallback model")
                
        finally:
            # Restore original backend
            self.config.backend = original_backend
    
    def unload_model(self):
        """Unload the model to free memory."""
        with self._lock:
            if self.info.loaded:
                self.model = None
                self.tokenizer = None
                self.info.loaded = False
                logger.info(f"Model {self.name} unloaded")
    
    def get_info(self) -> ModelInfo:
        """Get model information."""
        return self.info
    
    def get_stats(self) -> Dict[str, Any]:
        """Get model statistics."""
        avg_inference_time = 0.0
        if self.info.inference_count > 0:
            avg_inference_time = self.info.total_inference_time / self.info.inference_count
        
        return {
            "name": self.name,
            "loaded": self.info.loaded,
            "inference_count": self.info.inference_count,
            "avg_inference_time_ms": avg_inference_time * 1000,
            "total_inference_time": self.info.total_inference_time,
            "error_count": self.info.error_count,
            "last_used": self.info.last_used
        }


class CrossEncoderModels:
    """
    Multi-model manager for cross-encoder models.
    
    Manages multiple cross-encoder models with lazy loading, caching,
    and automatic model selection based on configuration.
    """
    
    def __init__(self, models_config: Dict[str, ModelConfig]):
        """
        Initialize cross-encoder models manager.
        
        Args:
            models_config: Dictionary of model configurations
        """
        self.models_config = models_config
        self.managers: Dict[str, ModelManager] = {}
        self.default_model = None
        
        # Create model managers
        for name, config in models_config.items():
            self.managers[name] = ModelManager(name, config)
        
        # Set default model
        if models_config:
            self.default_model = list(models_config.keys())[0]
        
        self.stats = {
            "total_predictions": 0,
            "model_switches": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        logger.info(f"CrossEncoderModels initialized with {len(models_config)} models")
    
    def predict(
        self, 
        query_doc_pairs: List[List[str]], 
        model_name: Optional[str] = None
    ) -> List[float]:
        """
        Generate predictions using specified or default model.
        
        Args:
            query_doc_pairs: List of [query, document] pairs
            model_name: Name of model to use (defaults to default_model)
            
        Returns:
            List of relevance scores
        """
        if not query_doc_pairs:
            return []
        
        # Select model
        selected_model = model_name or self.default_model
        if selected_model not in self.managers:
            logger.warning(f"Model {selected_model} not found, using default")
            selected_model = self.default_model
        
        if not selected_model:
            raise RuntimeError("No models available")
        
        try:
            manager = self.managers[selected_model]
            scores = manager.predict(query_doc_pairs)
            
            self.stats["total_predictions"] += 1
            
            return scores
            
        except Exception as e:
            logger.error(f"Prediction failed with model {selected_model}: {e}")
            # Try fallback to default model if different
            if selected_model != self.default_model:
                logger.info(f"Trying fallback to default model: {self.default_model}")
                return self.predict(query_doc_pairs, self.default_model)
            else:
                raise
    
    def get_available_models(self) -> List[str]:
        """Get list of available model names."""
        return list(self.managers.keys())
    
    def is_model_loaded(self, model_name: str) -> bool:
        """Check if a model is loaded."""
        if model_name in self.managers:
            return self.managers[model_name].info.loaded
        return False
    
    def load_model(self, model_name: str) -> bool:
        """
        Load a specific model.
        
        Args:
            model_name: Name of model to load
            
        Returns:
            True if loaded successfully
        """
        if model_name in self.managers:
            return self.managers[model_name].load_model()
        return False
    
    def unload_model(self, model_name: str):
        """Unload a specific model."""
        if model_name in self.managers:
            self.managers[model_name].unload_model()
    
    def unload_all_models(self):
        """Unload all models to free memory."""
        for manager in self.managers.values():
            manager.unload_model()
    
    def get_model_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all models."""
        return {name: manager.get_stats() for name, manager in self.managers.items()}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall statistics."""
        stats = self.stats.copy()
        stats["models"] = self.get_model_stats()
        stats["total_models"] = len(self.managers)
        stats["loaded_models"] = sum(1 for m in self.managers.values() if m.info.loaded)
        
        return stats
    
    def reset_stats(self) -> None:
        """Reset statistics."""
        self.stats = {
            "total_predictions": 0,
            "model_switches": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }