"""
Enhanced Neural Reranking Configuration.

This module provides a simplified configuration class for neural reranking
that doesn't depend on the old reranking/ module structure.

Extracted essential configuration from the original reranking_config.py
for use in the architecture-compliant rerankers/ component.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


@dataclass
class EnhancedNeuralRerankingConfig:
    """
    Enhanced neural reranking configuration.
    
    Simplified version that maintains essential functionality while
    removing dependencies on the redundant reranking/ module.
    """
    
    enabled: bool = False
    
    # Multiple model support (simplified structure)
    models: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "default_model": {
            "name": "cross-encoder/ms-marco-MiniLM-L6-v2",
            "device": "auto",
            "batch_size": 16,
            "max_length": 512
        }
    })
    
    # Default model selection
    default_model: str = "default_model"
    
    # Legacy compatibility parameters
    max_candidates: int = 50
    model_name: str = "cross-encoder/ms-marco-MiniLM-L6-v2"
    model_type: str = "cross_encoder"
    device: str = "auto"
    batch_size: int = 16
    max_length: int = 512
    max_latency_ms: int = 200
    fallback_to_fast_reranker: bool = True
    fast_reranker_threshold: int = 100
    
    # Advanced configuration (simplified)
    adaptive_enabled: bool = True
    score_fusion_method: str = "weighted"
    neural_weight: float = 0.7
    retrieval_weight: float = 0.3
    enable_caching: bool = True
    cache_size: int = 10000
    
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
        Create enhanced config from base configuration dictionary.
        
        Args:
            base_config: Base neural reranking configuration dictionary
            
        Returns:
            Enhanced neural reranking configuration
        """
        # Extract base parameters with defaults
        enabled = base_config.get('enabled', False)
        model_name = base_config.get('model_name', 'cross-encoder/ms-marco-MiniLM-L6-v2')
        device = base_config.get('device', 'auto')
        max_candidates = base_config.get('max_candidates', 50)
        batch_size = base_config.get('batch_size', 16)
        max_length = base_config.get('max_length', 512)
        max_latency_ms = base_config.get('max_latency_ms', 200)
        
        # Handle models configuration
        models = base_config.get('models', {})
        if not models:
            # Create default model from legacy parameters
            models = {
                "default_model": {
                    "name": model_name,
                    "device": device,
                    "batch_size": batch_size,
                    "max_length": max_length
                }
            }
        
        # Get default model
        default_model = base_config.get('default_model', 'default_model')
        if default_model not in models:
            default_model = list(models.keys())[0] if models else 'default_model'
        
        return cls(
            enabled=enabled,
            models=models,
            default_model=default_model,
            max_candidates=max_candidates,
            model_name=model_name,
            model_type=base_config.get('model_type', 'cross_encoder'),
            device=device,
            batch_size=batch_size,
            max_length=max_length,
            max_latency_ms=max_latency_ms,
            fallback_to_fast_reranker=base_config.get('fallback_to_fast_reranker', True),
            fast_reranker_threshold=base_config.get('fast_reranker_threshold', 100),
            adaptive_enabled=base_config.get('adaptive_enabled', True),
            score_fusion_method=base_config.get('score_fusion_method', 'weighted'),
            neural_weight=base_config.get('neural_weight', 0.7),
            retrieval_weight=base_config.get('retrieval_weight', 0.3),
            enable_caching=base_config.get('enable_caching', True),
            cache_size=base_config.get('cache_size', 10000)
        )
    
    def to_base_config(self) -> Dict[str, Any]:
        """
        Convert to base configuration format for backward compatibility.
        
        Returns:
            Base configuration dictionary
        """
        return {
            'enabled': self.enabled,
            'model_name': self.model_name,
            'model_type': self.model_type,
            'device': self.device,
            'max_candidates': self.max_candidates,
            'batch_size': self.batch_size,
            'max_length': self.max_length,
            'max_latency_ms': self.max_latency_ms,
            'fallback_to_fast_reranker': self.fallback_to_fast_reranker,
            'fast_reranker_threshold': self.fast_reranker_threshold,
            'models': self.models,
            'default_model': self.default_model,
            'adaptive_enabled': self.adaptive_enabled,
            'score_fusion_method': self.score_fusion_method,
            'neural_weight': self.neural_weight,
            'retrieval_weight': self.retrieval_weight,
            'enable_caching': self.enable_caching,
            'cache_size': self.cache_size
        }
    
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
            
            # Check performance constraints (very generous limit for testing)
            if self.max_latency_ms > 10000:
                return False
            
            return True
            
        except Exception:
            return False