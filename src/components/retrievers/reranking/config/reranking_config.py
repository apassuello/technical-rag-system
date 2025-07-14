"""
Enhanced Neural Reranking Configuration.

This module provides comprehensive configuration classes for neural reranking
components, extending the base NeuralRerankingConfig with advanced features
for model management, adaptive strategies, score fusion, and performance optimization.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from pathlib import Path


@dataclass
class ModelConfig:
    """Configuration for individual neural reranking models."""
    
    # Model identification
    name: str = "cross-encoder/ms-marco-MiniLM-L6-v2"
    backend: str = "sentence_transformers"  # "sentence_transformers", "tensorflow", "keras"
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
    
    def __post_init__(self):
        """Validate model configuration."""
        valid_backends = ["sentence_transformers", "tensorflow", "keras"]
        if self.backend not in valid_backends:
            raise ValueError(f"Backend must be one of {valid_backends}")
        
        valid_types = ["cross_encoder", "bi_encoder", "ensemble"]
        if self.model_type not in valid_types:
            raise ValueError(f"Model type must be one of {valid_types}")
        
        valid_optimizations = ["speed", "balanced", "quality"]
        if self.optimization_level not in valid_optimizations:
            raise ValueError(f"Optimization level must be one of {valid_optimizations}")
        
        if self.batch_size <= 0:
            raise ValueError("Batch size must be positive")
        
        if self.max_length <= 0:
            raise ValueError("Max length must be positive")


@dataclass
class QueryClassificationConfig:
    """Configuration for query classification."""
    enabled: bool = True
    model: str = "built_in"  # "built_in", "custom", "external"
    confidence_threshold: float = 0.7
    # Query type mapping to models
    strategies: Dict[str, str] = field(default_factory=lambda: {
        "technical": "technical_model",
        "general": "default_model", 
        "comparative": "technical_model",
        "procedural": "general_model",
        "factual": "default_model"
    })


@dataclass
class ModelSelectionConfig:
    """Configuration for model selection strategy."""
    strategy: str = "rule_based"  # "rule_based", "learned", "confidence_based"
    fallback_model: str = "default_model"
    switch_threshold: float = 0.5
    # Dynamic model switching
    enable_dynamic_switching: bool = False
    performance_window: int = 100
    quality_threshold: float = 0.8


@dataclass
class PerformanceAdaptationConfig:
    """Configuration for performance adaptation."""
    enabled: bool = True
    latency_target_ms: int = 150
    quality_target: float = 0.85
    adaptive_batch_size: bool = True
    adaptive_candidates: bool = True


@dataclass
class AdaptiveConfig:
    """Configuration for adaptive reranking strategies."""
    
    enabled: bool = True
    
    # Sub-configurations
    query_classification: QueryClassificationConfig = field(default_factory=QueryClassificationConfig)
    model_selection: ModelSelectionConfig = field(default_factory=ModelSelectionConfig)
    performance_adaptation: PerformanceAdaptationConfig = field(default_factory=PerformanceAdaptationConfig)
    
    def __post_init__(self):
        """Validate adaptive configuration."""
        valid_strategies = ["rule_based", "learned", "confidence_based"]
        if self.model_selection.strategy not in valid_strategies:
            raise ValueError(f"Model selection strategy must be one of {valid_strategies}")
        
        if not 0 <= self.query_classification.confidence_threshold <= 1:
            raise ValueError("Confidence threshold must be between 0 and 1")


@dataclass
class WeightsConfig:
    """Configuration for score weights."""
    retrieval_score: float = 0.3
    neural_score: float = 0.7
    graph_score: float = 0.0  # For future graph integration
    temporal_score: float = 0.0  # For future temporal features


@dataclass
class NormalizationConfig:
    """Configuration for score normalization."""
    method: str = "min_max"  # "min_max", "z_score", "softmax", "sigmoid"
    clip_outliers: bool = True
    outlier_threshold: float = 3.0


@dataclass
class LearnedFusionConfig:
    """Configuration for learned fusion."""
    enabled: bool = False
    model_path: Optional[str] = None
    feature_size: int = 4
    hidden_size: int = 16
    learning_rate: float = 0.001


@dataclass
class AdaptiveFusionConfig:
    """Configuration for adaptive fusion."""
    enabled: bool = False
    query_dependent: bool = True
    context_dependent: bool = False
    adaptation_window: int = 50


@dataclass  
class ScoreFusionConfig:
    """Configuration for neural and retrieval score fusion."""
    
    method: str = "weighted"  # "weighted", "learned", "adaptive", "ensemble"
    
    # Sub-configurations
    weights: WeightsConfig = field(default_factory=WeightsConfig)
    normalization: NormalizationConfig = field(default_factory=NormalizationConfig)
    learned_fusion: LearnedFusionConfig = field(default_factory=LearnedFusionConfig)
    adaptive_fusion: AdaptiveFusionConfig = field(default_factory=AdaptiveFusionConfig)
    
    def __post_init__(self):
        """Validate score fusion configuration."""
        valid_methods = ["weighted", "learned", "adaptive", "ensemble"]
        if self.method not in valid_methods:
            raise ValueError(f"Fusion method must be one of {valid_methods}")
        
        valid_normalizations = ["min_max", "z_score", "softmax", "sigmoid"]
        if self.normalization.method not in valid_normalizations:
            raise ValueError(f"Normalization method must be one of {valid_normalizations}")
        
        # Validate weights sum to approximately 1.0
        total_weight = (self.weights.retrieval_score + 
                       self.weights.neural_score + 
                       self.weights.graph_score + 
                       self.weights.temporal_score)
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")


@dataclass
class PerformanceConfig:
    """Configuration for performance optimization."""
    
    # Latency optimization
    max_latency_ms: int = 200
    target_latency_ms: int = 150
    enable_early_stopping: bool = True
    early_stopping_threshold: float = 0.95
    
    # Batch processing
    dynamic_batching: bool = True
    min_batch_size: int = 1
    max_batch_size: int = 64
    batch_timeout_ms: int = 50
    
    # Caching
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    max_cache_size: int = 10000
    cache_strategy: str = "lru"  # "lru", "lfu", "ttl"
    
    # Model optimization
    model_warming: bool = True
    enable_onnx_optimization: bool = False
    enable_tensorrt: bool = False
    precision: str = "fp32"  # "fp32", "fp16", "int8"
    
    # Fallback strategies
    fallback_enabled: bool = True
    fallback_latency_threshold: int = 300
    fallback_error_threshold: int = 3
    fallback_strategy: str = "semantic_reranker"  # "semantic_reranker", "identity", "disable"
    
    # Resource management
    max_memory_mb: int = 2048
    max_gpu_memory_fraction: float = 0.8
    enable_memory_pooling: bool = True
    
    def __post_init__(self):
        """Validate performance configuration."""
        if self.max_latency_ms <= 0:
            raise ValueError("Max latency must be positive")
        
        if self.target_latency_ms > self.max_latency_ms:
            raise ValueError("Target latency cannot exceed max latency")
        
        if self.min_batch_size > self.max_batch_size:
            raise ValueError("Min batch size cannot exceed max batch size")
        
        valid_cache_strategies = ["lru", "lfu", "ttl"]
        if self.cache_strategy not in valid_cache_strategies:
            raise ValueError(f"Cache strategy must be one of {valid_cache_strategies}")
        
        valid_precisions = ["fp32", "fp16", "int8"]
        if self.precision not in valid_precisions:
            raise ValueError(f"Precision must be one of {valid_precisions}")
        
        valid_fallbacks = ["semantic_reranker", "identity", "disable"]
        if self.fallback_strategy not in valid_fallbacks:
            raise ValueError(f"Fallback strategy must be one of {valid_fallbacks}")


@dataclass
class EnhancedNeuralRerankingConfig:
    """
    Enhanced neural reranking configuration.
    
    This extends the base NeuralRerankingConfig with advanced features
    for model management, adaptive strategies, score fusion, and performance
    optimization while maintaining backward compatibility.
    """
    
    enabled: bool = False
    
    # Multiple model support
    models: Dict[str, ModelConfig] = field(default_factory=lambda: {
        "default_model": ModelConfig(
            name="cross-encoder/ms-marco-MiniLM-L6-v2",
            backend="sentence_transformers",
            batch_size=16
        ),
        "technical_model": ModelConfig(
            name="cross-encoder/ms-marco-electra-base", 
            backend="sentence_transformers",
            batch_size=8
        )
    })
    
    # Default model selection
    default_model: str = "default_model"
    
    # Advanced configurations
    adaptive: AdaptiveConfig = field(default_factory=AdaptiveConfig)
    score_fusion: ScoreFusionConfig = field(default_factory=ScoreFusionConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    # Legacy compatibility (from base NeuralRerankingConfig)
    max_candidates: int = 50
    
    # Quality metrics
    evaluation_enabled: bool = True
    evaluation_metrics: List[str] = field(default_factory=lambda: ["ndcg", "map", "mrr", "precision_at_k"])
    evaluation_k_values: List[int] = field(default_factory=lambda: [1, 3, 5, 10])
    evaluation_baseline_comparison: bool = True
    
    def __post_init__(self):
        """Validate enhanced neural reranking configuration."""
        if not self.models:
            raise ValueError("At least one model must be configured")
        
        if self.default_model not in self.models:
            raise ValueError(f"Default model '{self.default_model}' not found in models")
        
        if self.max_candidates <= 0:
            raise ValueError("Max candidates must be positive")
    
    @classmethod
    def from_base_config(cls, base_config: Dict[str, Any]) -> 'EnhancedNeuralRerankingConfig':
        """
        Create enhanced config from base NeuralRerankingConfig.
        
        Args:
            base_config: Base neural reranking configuration dictionary
            
        Returns:
            Enhanced neural reranking configuration
        """
        # Extract base parameters
        enabled = base_config.get('enabled', False)
        model_name = base_config.get('model_name', 'cross-encoder/ms-marco-MiniLM-L6-v2')
        device = base_config.get('device', 'auto')
        max_candidates = base_config.get('max_candidates', 50)
        batch_size = base_config.get('batch_size', 32)
        max_length = base_config.get('max_length', 512)
        max_latency_ms = base_config.get('max_latency_ms', 200)
        
        # Create enhanced configuration
        models = {
            "default_model": ModelConfig(
                name=model_name,
                device=device,
                batch_size=batch_size,
                max_length=max_length
            )
        }
        
        performance = PerformanceConfig(
            max_latency_ms=max_latency_ms,
            target_latency_ms=int(max_latency_ms * 0.75)
        )
        
        return cls(
            enabled=enabled,
            models=models,
            max_candidates=max_candidates,
            performance=performance
        )
    
    def to_base_config(self) -> Dict[str, Any]:
        """
        Convert to base NeuralRerankingConfig format for backward compatibility.
        
        Returns:
            Base configuration dictionary
        """
        default_model = self.models[self.default_model]
        
        return {
            'enabled': self.enabled,
            'model_name': default_model.name,
            'model_type': default_model.model_type,
            'device': default_model.device,
            'max_candidates': self.max_candidates,
            'batch_size': default_model.batch_size,
            'max_length': default_model.max_length,
            'max_latency_ms': self.performance.max_latency_ms,
            'fallback_to_fast_reranker': self.performance.fallback_enabled,
            'fast_reranker_threshold': self.performance.fallback_latency_threshold
        }
    
    def get_model_config(self, model_name: Optional[str] = None) -> ModelConfig:
        """
        Get configuration for a specific model.
        
        Args:
            model_name: Name of the model (defaults to default_model)
            
        Returns:
            Model configuration
        """
        if model_name is None:
            model_name = self.default_model
        
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found in configuration")
        
        return self.models[model_name]
    
    def validate_compatibility(self) -> bool:
        """
        Validate compatibility with existing AdvancedRetriever.
        
        Returns:
            True if configuration is compatible
        """
        try:
            # Check basic requirements
            if not self.models:
                return False
            
            # Validate default model exists
            if self.default_model not in self.models:
                return False
            
            # Check performance constraints
            if self.performance.max_latency_ms > 10000:  # Very generous limit for development/testing
                return False
            
            return True
            
        except Exception:
            return False