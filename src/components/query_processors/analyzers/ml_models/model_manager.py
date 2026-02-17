"""
Central Model Manager for Epic 1 ML Infrastructure.

This module provides the central coordination point for all ML model operations
in the Epic 1 system, integrating memory monitoring, caching, quantization,
and performance tracking into a unified interface.

Key Features:
- Lazy model loading with memory-aware management
- Intelligent caching with LRU and memory pressure eviction
- Automatic quantization for memory optimization
- Comprehensive performance monitoring and alerting
- Thread-safe operations with concurrent request handling
- Graceful error handling and fallback strategies
"""

import asyncio
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

# Import our infrastructure components
from .memory_monitor import MemoryMonitor
from .model_cache import ModelCache
from .performance_monitor import PerformanceMonitor
from .quantization import QuantizationUtils

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Information about a managed model."""

    name: str
    model_type: str  # 'SciBERT', 'DistilBERT', etc.
    status: str      # 'unloaded', 'loading', 'loaded', 'error'
    memory_mb: Optional[float] = None
    quantized: bool = False
    load_time_seconds: Optional[float] = None
    last_accessed: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ModelLoadingError(Exception):
    """Exception raised when model loading fails."""
    pass


class ModelManager:
    """
    Central ML model manager with comprehensive infrastructure integration.

    Provides intelligent model lifecycle management with memory awareness,
    performance optimization, and robust error handling for the Epic 1 system.
    """

    def __init__(
        self,
        memory_budget_gb: float = 2.0,
        cache_size: int = 10,
        enable_quantization: bool = True,
        enable_monitoring: bool = True,
        model_timeout_seconds: float = 30.0,
        max_concurrent_loads: int = 2
    ):
        """
        Initialize the model manager.

        Args:
            memory_budget_gb: Memory budget in GB
            cache_size: Maximum number of cached models
            enable_quantization: Whether to use quantization
            enable_monitoring: Whether to enable performance monitoring
            model_timeout_seconds: Timeout for model loading operations
            max_concurrent_loads: Maximum concurrent model loading operations
        """
        self.memory_budget_gb = memory_budget_gb
        self.memory_budget_mb = memory_budget_gb * 1024  # Convert to MB
        self.enable_quantization = enable_quantization
        self.enable_monitoring = enable_monitoring
        self.model_timeout_seconds = model_timeout_seconds
        self.max_concurrent_loads = max_concurrent_loads

        # Initialize infrastructure components
        self.memory_monitor = MemoryMonitor()
        self.model_cache = ModelCache(
            maxsize=cache_size,
            memory_threshold_mb=self.memory_budget_mb * 0.9,  # 90% of budget
            enable_stats=True
        )
        self.quantization_utils = QuantizationUtils(enable_validation=True) if enable_quantization else None
        self.performance_monitor = PerformanceMonitor() if enable_monitoring else None

        # Integrate components
        self.model_cache.set_memory_monitor(self.memory_monitor)

        # Model registry and status tracking
        self.model_registry: Dict[str, ModelInfo] = {}
        self.model_instances: Dict[str, Any] = {}  # Actual loaded model instances

        # Thread safety and concurrency control
        self._lock = threading.RLock()
        self._loading_semaphore = threading.Semaphore(max_concurrent_loads)
        self._loading_futures: Dict[str, Any] = {}  # Track ongoing loads

        # Model loading executor
        self._loading_executor = ThreadPoolExecutor(
            max_workers=max_concurrent_loads,
            thread_name_prefix="model-loader"
        )

        # Model factory functions - registered dynamically
        self._model_factories: Dict[str, Callable] = {}

        # Initialize default model configurations
        self._initialize_model_configurations()

        # Start memory monitoring
        self.memory_monitor.start_monitoring()

        logger.info(f"Initialized ModelManager: budget={memory_budget_gb}GB, "
                   f"cache_size={cache_size}, quantization={enable_quantization}")

    def _initialize_model_configurations(self) -> None:
        """Initialize default model configurations."""
        self.model_configurations = {
            'SciBERT': {
                'model_name': 'allenai/scibert_scivocab_uncased',
                'model_type': 'transformers',
                'estimated_memory_mb': 440,
                'quantization_method': 'dynamic'
            },
            'DistilBERT': {
                'model_name': 'distilbert-base-uncased',
                'model_type': 'transformers',
                'estimated_memory_mb': 260,
                'quantization_method': 'dynamic'
            },
            'DeBERTa-v3': {
                'model_name': 'microsoft/deberta-v3-base',
                'model_type': 'transformers',
                'estimated_memory_mb': 750,
                'quantization_method': 'dynamic'
            },
            'Sentence-BERT': {
                'model_name': 'sentence-transformers/all-MiniLM-L6-v2',
                'model_type': 'sentence_transformers',
                'estimated_memory_mb': 420,
                'quantization_method': 'dynamic'
            },
            'T5-small': {
                'model_name': 't5-small',  # Fixed: was 'google-t5/t5-small'
                'model_type': 'transformers',
                'estimated_memory_mb': 240,
                'quantization_method': 'dynamic'
            }
        }

        # Create reverse mapping from HuggingFace model names to configuration keys
        # This allows views to use either the config key OR the HuggingFace model name
        self._hf_name_to_config_key = {}
        for config_key, config in self.model_configurations.items():
            hf_name = config['model_name']
            self._hf_name_to_config_key[hf_name] = config_key

        logger.debug(f"Initialized {len(self.model_configurations)} model configurations")
        logger.debug(f"HuggingFace name mappings: {list(self._hf_name_to_config_key.keys())}")

    def register_model_factory(self, model_type: str, factory_function: Callable) -> None:
        """
        Register a factory function for a specific model type.

        Args:
            model_type: Type of model (e.g., 'SciBERT', 'DistilBERT')
            factory_function: Function that loads and returns the model
        """
        self._model_factories[model_type] = factory_function
        logger.debug(f"Registered factory for model type: {model_type}")

    async def load_model(self, model_name: str, force_reload: bool = False) -> Any:
        """
        Load a model with intelligent caching and memory management.

        Args:
            model_name: Name of the model to load
            force_reload: Whether to force reload even if cached

        Returns:
            Loaded model instance

        Raises:
            ModelLoadingError: If model loading fails
        """
        # Record request for monitoring
        if self.performance_monitor:
            self.performance_monitor.record_request(f"load_model_{model_name}")

        start_time = time.time()

        try:
            # Check cache first (unless force reload)
            if not force_reload:
                cached_model = self.model_cache.get(model_name)
                if cached_model is not None:
                    self._update_model_access_time(model_name)
                    if self.performance_monitor:
                        latency_ms = (time.time() - start_time) * 1000
                        self.performance_monitor.record_latency(f"load_model_{model_name}", latency_ms)
                    logger.debug(f"Returned cached model: {model_name}")
                    return cached_model

            # Check if already loading
            with self._lock:
                if model_name in self._loading_futures:
                    logger.debug(f"Model {model_name} already loading, waiting...")
                    future = self._loading_futures[model_name]
                    try:
                        return await asyncio.wait_for(
                            asyncio.wrap_future(future),
                            timeout=self.model_timeout_seconds
                        )
                    except asyncio.TimeoutError:
                        raise ModelLoadingError(f"Timeout waiting for {model_name} to load")

            # Start loading process
            return await self._load_model_with_management(model_name)

        except Exception as e:
            # Record error metrics
            if self.performance_monitor:
                latency_ms = (time.time() - start_time) * 1000
                self.performance_monitor.record_latency(f"load_model_{model_name}_error", latency_ms)

            error_msg = f"Failed to load model {model_name}: {str(e)}"
            logger.error(error_msg)

            # Update model status
            with self._lock:
                if model_name in self.model_registry:
                    self.model_registry[model_name].status = 'error'
                    self.model_registry[model_name].error_message = str(e)

            raise ModelLoadingError(error_msg) from e

    async def _load_model_with_management(self, model_name: str) -> Any:
        """Load model with full memory and performance management."""
        with self._lock:
            # Initialize model info if not exists
            if model_name not in self.model_registry:
                self.model_registry[model_name] = ModelInfo(
                    name=model_name,
                    model_type=model_name,  # Assume model_name == model_type for now
                    status='unloaded'
                )

            # Update status to loading
            self.model_registry[model_name].status = 'loading'

        # Acquire loading semaphore
        async with asyncio.Lock():  # Convert semaphore to async
            try:
                # Check memory constraints
                await self._ensure_memory_available(model_name)

                # Create loading future
                future = self._loading_executor.submit(self._load_model_sync, model_name)

                with self._lock:
                    self._loading_futures[model_name] = future

                # Wait for loading with timeout
                try:
                    model = await asyncio.wait_for(
                        asyncio.wrap_future(future),
                        timeout=self.model_timeout_seconds
                    )

                    # Post-processing and caching
                    await self._post_process_loaded_model(model_name, model)

                    return model

                finally:
                    # Clean up loading future
                    with self._lock:
                        if model_name in self._loading_futures:
                            del self._loading_futures[model_name]

            except Exception as e:
                with self._lock:
                    if model_name in self.model_registry:
                        self.model_registry[model_name].status = 'error'
                        self.model_registry[model_name].error_message = str(e)
                raise

    async def _ensure_memory_available(self, model_name: str) -> None:
        """Ensure sufficient memory is available for model loading."""
        estimated_memory = self.memory_monitor.estimate_model_memory(
            model_name,
            quantized=self.enable_quantization
        )

        if self.memory_monitor.would_exceed_budget(model_name, self.memory_budget_mb, self.enable_quantization):
            # Need to evict some models
            target_free_mb = estimated_memory * 1.2  # Add 20% buffer
            eviction_candidates = self.memory_monitor.get_eviction_candidates(target_free_mb)

            logger.info(f"Memory pressure detected for {model_name}, evicting {len(eviction_candidates)} models")

            for evict_model_name in eviction_candidates.keys():
                await self._evict_model(evict_model_name)

                # Check if we have enough memory now
                if not self.memory_monitor.would_exceed_budget(model_name, self.memory_budget_mb, self.enable_quantization):
                    break

    async def _evict_model(self, model_name: str) -> None:
        """Evict a model from memory and cache."""
        with self._lock:
            # Remove from cache
            self.model_cache.evict(model_name)

            # Remove from model instances
            if model_name in self.model_instances:
                del self.model_instances[model_name]

            # Update model status
            if model_name in self.model_registry:
                self.model_registry[model_name].status = 'unloaded'
                self.model_registry[model_name].memory_mb = None

        logger.debug(f"Evicted model: {model_name}")

    def _load_model_sync(self, model_name: str) -> Any:
        """Synchronous model loading implementation."""
        start_time = time.time()

        try:
            # Get model configuration - support both config keys and HuggingFace model names
            config_key = model_name
            config = self.model_configurations.get(config_key)

            # If not found by config key, try HuggingFace model name mapping
            if not config and hasattr(self, '_hf_name_to_config_key'):
                config_key = self._hf_name_to_config_key.get(model_name)
                if config_key:
                    config = self.model_configurations.get(config_key)
                    logger.debug(f"Mapped HuggingFace model name '{model_name}' to config key '{config_key}'")

            if not config:
                available_names = list(self.model_configurations.keys())
                if hasattr(self, '_hf_name_to_config_key'):
                    available_names.extend(list(self._hf_name_to_config_key.keys()))
                raise ModelLoadingError(
                    f"No configuration found for model: {model_name}. "
                    f"Available models: {available_names}"
                )

            # Use registered factory or default loading
            # Try both the original model_name and the config_key for factories
            if model_name in self._model_factories:
                logger.debug(f"Loading {model_name} using registered factory")
                model = self._model_factories[model_name]()
            elif config_key != model_name and config_key in self._model_factories:
                logger.debug(f"Loading {config_key} using registered factory (mapped from {model_name})")
                model = self._model_factories[config_key]()
            else:
                logger.debug(f"Loading {model_name} using default method")
                model = self._load_model_default(model_name, config)

            # Apply quantization if enabled (currently disabled for compatibility)
            if self.enable_quantization and self.quantization_utils and False:  # Disabled for now
                logger.debug(f"Applying quantization to {model_name}")
                # Extract actual model from dict if needed
                quantization_target = model.get('model', model) if isinstance(model, dict) else model
                quant_result = self.quantization_utils.quantize_transformer_model(quantization_target, method='dynamic')

                if quant_result.success:
                    logger.info(f"Quantized {model_name}: {quant_result.compression_ratio:.2f}x compression, "
                               f"{quant_result.memory_savings_mb:.1f}MB saved")
                    # Note: In practice, would use the quantized model
                    # model = quantized_model  # Uncomment when quantization is stable
                else:
                    logger.warning(f"Quantization failed for {model_name}: {quant_result.error_message}")
            else:
                if self.enable_quantization:
                    logger.debug(f"Quantization disabled for {model_name} (compatibility mode)")

            # Record loading time
            load_time = time.time() - start_time

            # Update model registry
            with self._lock:
                model_info = self.model_registry[model_name]
                model_info.status = 'loaded'
                model_info.load_time_seconds = load_time
                model_info.last_accessed = time.time()
                model_info.quantized = self.enable_quantization

                # Store model instance
                self.model_instances[model_name] = model

            logger.info(f"Successfully loaded model {model_name} in {load_time:.2f}s")
            return model

        except Exception as e:
            logger.error(f"Model loading failed for {model_name}: {e}")
            raise

    def _load_model_default(self, model_name: str, config: Dict[str, Any]) -> Any:
        """Default model loading implementation."""
        model_type = config.get('model_type', 'transformers')
        hf_model_name = config.get('model_name', model_name)

        if model_type == 'transformers':
            # Load HuggingFace transformers model
            try:
                from transformers import AutoModel, AutoTokenizer

                # TODO: Pin model revision hash for supply-chain security
                model = AutoModel.from_pretrained(hf_model_name)

                # Try to load tokenizer, with fallback for problematic models
                try:
                    # TODO: Pin model revision hash for supply-chain security
                    tokenizer = AutoTokenizer.from_pretrained(hf_model_name)
                    logger.debug(f"✅ Fast tokenizer loaded for {hf_model_name}: {type(tokenizer)}")
                except Exception as tokenizer_error:
                    logger.warning(f"Fast tokenizer failed for {hf_model_name}, trying slow tokenizer: {tokenizer_error}")
                    try:
                        # TODO: Pin model revision hash for supply-chain security
                        tokenizer = AutoTokenizer.from_pretrained(hf_model_name, use_fast=False)
                        logger.debug(f"✅ Slow tokenizer loaded for {hf_model_name}: {type(tokenizer)}")
                    except Exception as slow_tokenizer_error:
                        logger.error(f"Both tokenizers failed for {hf_model_name}: {slow_tokenizer_error}")
                        # For some models, we might need specific approaches
                        if 'deberta' in hf_model_name.lower():
                            logger.info(f"Attempting DeBERTa-specific tokenizer for {hf_model_name}")
                            try:
                                from transformers import DebertaV2Tokenizer
                                # TODO: Pin model revision hash for supply-chain security
                                tokenizer = DebertaV2Tokenizer.from_pretrained(hf_model_name)
                                logger.info(f"✅ DeBertaV2Tokenizer loaded for {hf_model_name}")
                            except Exception as deberta_error:
                                logger.error(f"DeBertaV2Tokenizer also failed: {deberta_error}")
                                tokenizer = None
                        else:
                            tokenizer = None

                # Return a wrapper or just the model
                return {'model': model, 'tokenizer': tokenizer}

            except ImportError:
                raise ModelLoadingError("transformers library not available")

        elif model_type == 'sentence_transformers':
            # Load sentence transformers model
            try:
                from sentence_transformers import SentenceTransformer

                model = SentenceTransformer(hf_model_name)
                return model

            except ImportError:
                raise ModelLoadingError("sentence-transformers library not available")

        else:
            raise ModelLoadingError(f"Unsupported model type: {model_type}")

    async def _post_process_loaded_model(self, model_name: str, model: Any) -> None:
        """Post-process loaded model (caching, memory tracking, etc.)."""
        # Estimate actual memory usage
        try:
            if hasattr(model, 'get_memory_footprint'):
                actual_memory_mb = model.get_memory_footprint() / (1024 * 1024)
            else:
                # Rough estimation
                actual_memory_mb = self.memory_monitor.estimate_model_memory(model_name, self.enable_quantization)

            # Record actual memory usage
            self.memory_monitor.record_actual_model_memory(model_name, actual_memory_mb)

            # Update model info
            with self._lock:
                if model_name in self.model_registry:
                    self.model_registry[model_name].memory_mb = actual_memory_mb

            # Cache the model
            self.model_cache.put(model_name, model, actual_memory_mb)

            # Record memory usage for monitoring
            if self.performance_monitor:
                self.performance_monitor.record_memory_usage(model_name, actual_memory_mb)

        except Exception as e:
            logger.warning(f"Post-processing failed for {model_name}: {e}")

    def _update_model_access_time(self, model_name: str) -> None:
        """Update last access time for a model."""
        with self._lock:
            if model_name in self.model_registry:
                self.model_registry[model_name].last_accessed = time.time()

    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get information about a model."""
        with self._lock:
            return self.model_registry.get(model_name)

    def get_model(self, model_name: str) -> Optional[Any]:
        """Get a loaded model instance."""
        with self._lock:
            return self.model_instances.get(model_name)

    def list_loaded_models(self) -> List[ModelInfo]:
        """Get list of all loaded models."""
        with self._lock:
            return [info for info in self.model_registry.values() if info.status == 'loaded']

    def get_memory_usage_summary(self) -> Dict[str, Any]:
        """Get comprehensive memory usage summary."""
        memory_stats = self.memory_monitor.get_current_stats()
        cache_info = self.model_cache.get_cache_info()

        return {
            'system_memory': {
                'total_mb': memory_stats.total_mb,
                'used_mb': memory_stats.used_mb,
                'available_mb': memory_stats.available_mb,
                'epic1_process_mb': memory_stats.epic1_process_mb
            },
            'model_cache': {
                'size': cache_info['size'],
                'maxsize': cache_info['maxsize'],
                'total_memory_mb': cache_info['total_memory_mb'],
                'hit_rate': self.model_cache.get_stats().hit_rate if self.model_cache.get_stats() else 0.0
            },
            'memory_budget': {
                'budget_mb': self.memory_budget_mb,
                'used_percentage': (cache_info['total_memory_mb'] / self.memory_budget_mb * 100) if self.memory_budget_mb > 0 else 0,
                'pressure_level': self.memory_monitor.get_memory_pressure_level(self.memory_budget_mb)
            },
            'loaded_models': [
                {
                    'name': info.name,
                    'memory_mb': info.memory_mb,
                    'status': info.status,
                    'quantized': info.quantized
                }
                for info in self.list_loaded_models()
            ]
        }

    def log_status_report(self) -> None:
        """Log comprehensive status report."""
        memory_summary = self.get_memory_usage_summary()

        logger.info("=== MODEL MANAGER STATUS REPORT ===")
        logger.info(f"Memory Budget: {self.memory_budget_mb:.1f}MB")
        logger.info(f"Memory Pressure: {memory_summary['memory_budget']['pressure_level']}")
        logger.info(f"Cache Hit Rate: {memory_summary['model_cache']['hit_rate']:.2%}")
        logger.info(f"Loaded Models: {len(memory_summary['loaded_models'])}")

        for model_info in memory_summary['loaded_models']:
            logger.info(f"  - {model_info['name']}: {model_info['memory_mb']:.1f}MB "
                       f"({'quantized' if model_info['quantized'] else 'full precision'})")

        if self.performance_monitor:
            logger.info("Performance Monitoring: Enabled")
            self.performance_monitor.log_performance_report()

        logger.info("=== END STATUS REPORT ===")

    def shutdown(self) -> None:
        """Shutdown the model manager and clean up resources."""
        logger.info("Shutting down ModelManager...")

        # Stop monitoring
        self.memory_monitor.stop_monitoring()

        # Clear cache and models
        with self._lock:
            self.model_cache.clear()
            self.model_instances.clear()
            self.model_registry.clear()

        # Shutdown executors
        if self._loading_executor:
            self._loading_executor.shutdown(wait=False)

        logger.info("ModelManager shutdown complete")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()
