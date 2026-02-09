"""
Mock ML Models for Epic 1 Infrastructure Testing.

Provides lightweight mock objects that simulate transformer model behavior
without requiring actual ML libraries or models.
"""

import time
import threading
import random
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from unittest.mock import MagicMock
import weakref


@dataclass
class MockModelConfig:
    """Configuration for mock model behavior."""
    
    name: str
    memory_mb: float = 300.0
    load_time_seconds: float = 1.0
    quantized_memory_mb: Optional[float] = None
    supports_quantization: bool = True
    failure_rate: float = 0.0  # Probability of operation failure
    thread_safe: bool = True


class MockTransformerModel:
    """
    Mock transformer model that simulates real model behavior.
    
    Features:
    - Configurable memory usage
    - Simulated loading times
    - Quantization support
    - Error injection for testing
    - Thread-safe operations
    """
    
    def __init__(self, config: MockModelConfig):
        self.config = config
        self._loaded = False
        self._quantized = False
        self._lock = threading.RLock() if config.thread_safe else None
        self._memory_usage_mb = 0.0
        self._load_start_time = None
        self._access_count = 0
        self._last_accessed = None
        
        # Weak reference tracking for memory simulation
        self._instances = weakref.WeakSet()
        self._instances.add(self)
    
    @property
    def name(self) -> str:
        return self.config.name
    
    @property
    def is_loaded(self) -> bool:
        return self._loaded
    
    @property
    def is_quantized(self) -> bool:
        return self._quantized
    
    @property
    def memory_usage_mb(self) -> float:
        """Get current memory usage."""
        if not self._loaded:
            return 0.0
        
        if self._quantized and self.config.quantized_memory_mb:
            return self.config.quantized_memory_mb
        else:
            return self.config.memory_mb
    
    def load(self) -> None:
        """Simulate model loading."""
        if self._lock:
            with self._lock:
                self._load_impl()
        else:
            self._load_impl()
    
    def _load_impl(self) -> None:
        """Internal load implementation."""
        if self._loaded:
            return
        
        # Simulate failure
        if random.random() < self.config.failure_rate:
            raise RuntimeError(f"Mock model {self.config.name} failed to load")
        
        self._load_start_time = time.time()
        
        # Simulate loading time
        time.sleep(self.config.load_time_seconds)
        
        self._loaded = True
        self._memory_usage_mb = self.config.memory_mb
    
    def eval(self) -> 'MockTransformerModel':
        """Simulate PyTorch model.eval() for quantization compatibility."""
        # Mock models are always in eval mode
        return self

    def named_children(self):
        """Simulate PyTorch nn.Module.named_children() for quantization compatibility."""
        # Return empty iterator - mock models don't have child modules
        return iter([])

    def modules(self):
        """Simulate PyTorch nn.Module.modules() for quantization compatibility."""
        # Return iterator with just self - mock models don't have child modules
        return iter([self])

    def parameters(self):
        """Simulate PyTorch nn.Module.parameters() for quantization compatibility."""
        # Return empty iterator - mock models don't have trainable parameters
        return iter([])

    def unload(self) -> None:
        """Simulate model unloading."""
        if self._lock:
            with self._lock:
                self._unload_impl()
        else:
            self._unload_impl()
    
    def _unload_impl(self) -> None:
        """Internal unload implementation."""
        self._loaded = False
        self._quantized = False
        self._memory_usage_mb = 0.0
    
    def quantize(self, method: str = 'dynamic') -> Dict[str, Any]:
        """Simulate model quantization."""
        if self._lock:
            with self._lock:
                return self._quantize_impl(method)
        else:
            return self._quantize_impl(method)
    
    def _quantize_impl(self, method: str) -> Dict[str, Any]:
        """Internal quantization implementation."""
        if not self._loaded:
            raise RuntimeError("Cannot quantize unloaded model")
        
        if not self.config.supports_quantization:
            return {
                'success': False,
                'error_message': f'Model {self.config.name} does not support quantization',
                'method': method
            }
        
        # Simulate failure
        if random.random() < self.config.failure_rate:
            return {
                'success': False,
                'error_message': f'Quantization failed for {self.config.name}',
                'method': method
            }
        
        # Calculate quantized size
        original_size = self.config.memory_mb
        quantized_size = self.config.quantized_memory_mb or (original_size * 0.5)
        compression_ratio = original_size / quantized_size
        
        self._quantized = True
        self._memory_usage_mb = quantized_size
        
        return {
            'success': True,
            'method': method,
            'original_size_mb': original_size,
            'quantized_size_mb': quantized_size,
            'compression_ratio': compression_ratio,
            'memory_savings_mb': original_size - quantized_size
        }
    
    def predict(self, inputs: Any) -> Any:
        """Simulate model inference."""
        if not self._loaded:
            raise RuntimeError("Model not loaded")
        
        self._access_count += 1
        self._last_accessed = time.time()
        
        # Simulate failure
        if random.random() < self.config.failure_rate:
            raise RuntimeError("Mock prediction failed")
        
        # Return mock predictions
        return f"mock_prediction_from_{self.config.name}"
    
    def get_memory_footprint(self) -> float:
        """Get memory footprint in bytes."""
        return self.memory_usage_mb * 1024 * 1024
    
    def get_stats(self) -> Dict[str, Any]:
        """Get model statistics."""
        return {
            'name': self.config.name,
            'loaded': self._loaded,
            'quantized': self._quantized,
            'memory_mb': self.memory_usage_mb,
            'access_count': self._access_count,
            'last_accessed': self._last_accessed,
            'load_time': time.time() - self._load_start_time if self._load_start_time else None
        }

    def __getstate__(self) -> Dict[str, Any]:
        """Prepare object for pickling by removing non-picklable RLock."""
        state = self.__dict__.copy()
        # Remove the lock (not picklable)
        state['_lock'] = None
        # Remove weakref set (not picklable)
        state['_instances'] = None
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        """Restore object from pickle by recreating RLock."""
        self.__dict__.update(state)
        # Recreate lock if needed
        if self.config.thread_safe:
            self._lock = threading.RLock()
        # Recreate weakref set
        self._instances = weakref.WeakSet()
        self._instances.add(self)


class MockModelFactory:
    """Factory for creating mock models with predefined configurations."""
    
    # Predefined model configurations based on real models
    MODEL_CONFIGS = {
        'SciBERT': MockModelConfig(
            name='SciBERT',
            memory_mb=440.0,
            quantized_memory_mb=220.0,
            load_time_seconds=2.0
        ),
        'DistilBERT': MockModelConfig(
            name='DistilBERT', 
            memory_mb=260.0,
            quantized_memory_mb=130.0,
            load_time_seconds=1.5
        ),
        'DeBERTa-v3': MockModelConfig(
            name='DeBERTa-v3',
            memory_mb=750.0,
            quantized_memory_mb=375.0,
            load_time_seconds=3.0
        ),
        'Sentence-BERT': MockModelConfig(
            name='Sentence-BERT',
            memory_mb=420.0,
            quantized_memory_mb=210.0,
            load_time_seconds=2.2
        ),
        'T5-small': MockModelConfig(
            name='T5-small',
            memory_mb=240.0,
            quantized_memory_mb=120.0,
            load_time_seconds=1.8
        ),
        'test-model-small': MockModelConfig(
            name='test-model-small',
            memory_mb=100.0,
            quantized_memory_mb=50.0,
            load_time_seconds=0.5
        ),
        'test-model-large': MockModelConfig(
            name='test-model-large',
            memory_mb=1000.0,
            quantized_memory_mb=500.0,
            load_time_seconds=5.0
        ),
        'test-model-unreliable': MockModelConfig(
            name='test-model-unreliable',
            memory_mb=300.0,
            quantized_memory_mb=150.0,
            load_time_seconds=1.0,
            failure_rate=0.3  # 30% failure rate for testing
        ),
        'test-model-no-quantization': MockModelConfig(
            name='test-model-no-quantization',
            memory_mb=200.0,
            supports_quantization=False,
            load_time_seconds=1.0
        )
    }
    
    @classmethod
    def create_model(cls, model_name: str, **kwargs) -> MockTransformerModel:
        """Create a mock model by name."""
        if model_name not in cls.MODEL_CONFIGS:
            # Create default config for unknown models
            config = MockModelConfig(
                name=model_name,
                memory_mb=kwargs.get('memory_mb', 300.0),
                load_time_seconds=kwargs.get('load_time_seconds', 1.0)
            )
        else:
            config = cls.MODEL_CONFIGS[model_name]
            
            # Override with kwargs
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        
        return MockTransformerModel(config)
    
    @classmethod
    def get_model_configs(cls) -> Dict[str, MockModelConfig]:
        """Get all predefined model configurations."""
        return cls.MODEL_CONFIGS.copy()
    
    @classmethod
    def create_test_suite_models(cls) -> List[MockTransformerModel]:
        """Create a suite of models for comprehensive testing."""
        return [
            cls.create_model('test-model-small'),
            cls.create_model('test-model-large'), 
            cls.create_model('test-model-unreliable'),
            cls.create_model('test-model-no-quantization'),
            cls.create_model('SciBERT'),
            cls.create_model('DistilBERT')
        ]


class MockModelLoader:
    """
    Mock model loader that simulates HuggingFace transformers loading.
    
    Can be used to replace actual model loading in tests.
    """
    
    def __init__(self):
        self._loaded_models: Dict[str, MockTransformerModel] = {}
        self._loading_times: Dict[str, float] = {}
    
    def load_model(self, model_name: str, **kwargs) -> MockTransformerModel:
        """Load a mock model."""
        if model_name in self._loaded_models:
            return self._loaded_models[model_name]
        
        start_time = time.time()
        model = MockModelFactory.create_model(model_name, **kwargs)
        model.load()
        
        self._loaded_models[model_name] = model
        self._loading_times[model_name] = time.time() - start_time
        
        return model
    
    def get_loaded_models(self) -> Dict[str, MockTransformerModel]:
        """Get all loaded models."""
        return self._loaded_models.copy()
    
    def get_loading_times(self) -> Dict[str, float]:
        """Get loading times for all models."""
        return self._loading_times.copy()
    
    def unload_model(self, model_name: str) -> None:
        """Unload a model."""
        if model_name in self._loaded_models:
            self._loaded_models[model_name].unload()
            del self._loaded_models[model_name]
    
    def clear(self) -> None:
        """Clear all loaded models."""
        for model in self._loaded_models.values():
            model.unload()
        self._loaded_models.clear()
        self._loading_times.clear()


class MockAsyncModelLoader:
    """
    Async version of MockModelLoader for testing async loading scenarios.
    """
    
    def __init__(self):
        self._loader = MockModelLoader()
    
    async def load_model(self, model_name: str, **kwargs) -> MockTransformerModel:
        """Async model loading simulation."""
        import asyncio
        
        # Run sync loading in executor to simulate async behavior
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self._loader.load_model, 
            model_name, 
            **kwargs
        )
    
    def get_loaded_models(self) -> Dict[str, MockTransformerModel]:
        return self._loader.get_loaded_models()
    
    def get_loading_times(self) -> Dict[str, float]:
        return self._loader.get_loading_times()
    
    async def unload_model(self, model_name: str) -> None:
        self._loader.unload_model(model_name)
    
    async def clear(self) -> None:
        self._loader.clear()


def create_mock_model_factory_functions() -> Dict[str, Callable]:
    """
    Create mock factory functions that can be registered with ModelManager.
    
    Returns a dict of model_name -> factory_function.
    """
    factory_functions = {}
    
    for model_name in MockModelFactory.MODEL_CONFIGS.keys():
        def make_factory(name: str):
            def factory():
                return MockModelFactory.create_model(name)
            return factory
        
        factory_functions[model_name] = make_factory(model_name)
    
    return factory_functions


def patch_model_loading():
    """
    Context manager that patches real model loading with mock loading.
    
    Usage:
        with patch_model_loading():
            # Code that loads models will use mocks
            model = some_model_loading_function()
    """
    from unittest.mock import patch
    
    mock_loader = MockModelLoader()
    
    def mock_from_pretrained(model_name, **kwargs):
        return mock_loader.load_model(model_name, **kwargs)
    
    return patch('transformers.AutoModel.from_pretrained', side_effect=mock_from_pretrained)