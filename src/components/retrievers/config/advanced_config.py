"""
Advanced retriever configuration schema.

This module provides configuration classes for the advanced retriever
that supports multiple backends, hybrid search strategies, and advanced
features like neural reranking and analytics.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

from ..backends.weaviate_config import WeaviateBackendConfig


@dataclass
class BackendConfig:
    """Configuration for retrieval backends."""
    
    # Primary backend selection
    primary_backend: str = "faiss"  # "faiss" or "weaviate"
    fallback_enabled: bool = True
    fallback_backend: Optional[str] = None
    
    # Backend-specific configurations
    faiss: Dict[str, Any] = field(default_factory=lambda: {
        "index_type": "IndexFlatIP",
        "normalize_embeddings": True,
        "metric": "cosine"
    })
    
    weaviate: Optional[WeaviateBackendConfig] = None
    
    # Hot-swapping configuration
    enable_hot_swap: bool = False
    health_check_interval_seconds: int = 30
    switch_threshold_error_rate: float = 0.1
    
    def __post_init__(self):
        """Validate backend configuration."""
        valid_backends = ["faiss", "weaviate"]
        
        if self.primary_backend not in valid_backends:
            raise ValueError(f"Primary backend must be one of {valid_backends}")
        
        if self.fallback_backend and self.fallback_backend not in valid_backends:
            raise ValueError(f"Fallback backend must be one of {valid_backends}")
        
        if self.fallback_backend == self.primary_backend:
            raise ValueError("Fallback backend cannot be the same as primary")
        
        # Initialize Weaviate config if using Weaviate
        if self.primary_backend == "weaviate" or self.fallback_backend == "weaviate":
            if self.weaviate is None:
                self.weaviate = WeaviateBackendConfig()


@dataclass
class HybridSearchConfig:
    """Configuration for hybrid search strategies."""
    
    enabled: bool = True
    
    # Search strategy weights
    dense_weight: float = 0.7
    sparse_weight: float = 0.3
    graph_weight: float = 0.0  # For future graph-based retrieval
    
    # Fusion method
    fusion_method: str = "rrf"  # "rrf", "weighted", "learned"
    rrf_k: int = 60
    
    # Advanced fusion parameters
    adaptive_weights: bool = False
    query_dependent_weighting: bool = False
    normalization_method: str = "min_max"  # "min_max", "z_score", "softmax"
    
    # Performance optimization
    max_candidates_per_strategy: int = 100
    early_termination_threshold: float = 0.95
    
    def __post_init__(self):
        """Validate hybrid search configuration."""
        if not 0 <= self.dense_weight <= 1:
            raise ValueError("Dense weight must be between 0 and 1")
        if not 0 <= self.sparse_weight <= 1:
            raise ValueError("Sparse weight must be between 0 and 1")
        if not 0 <= self.graph_weight <= 1:
            raise ValueError("Graph weight must be between 0 and 1")
        
        total_weight = self.dense_weight + self.sparse_weight + self.graph_weight
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
        
        valid_fusion_methods = ["rrf", "weighted", "learned"]
        if self.fusion_method not in valid_fusion_methods:
            raise ValueError(f"Fusion method must be one of {valid_fusion_methods}")
        
        valid_normalization = ["min_max", "z_score", "softmax"]
        if self.normalization_method not in valid_normalization:
            raise ValueError(f"Normalization method must be one of {valid_normalization}")


@dataclass
class NeuralRerankingConfig:
    """Configuration for neural reranking."""
    
    enabled: bool = False
    
    # Model configuration
    model_name: str = "cross-encoder/ms-marco-MiniLM-L6-v2"
    model_type: str = "cross_encoder"  # "cross_encoder", "bi_encoder", "ensemble"
    device: str = "auto"  # "auto", "cpu", "cuda", "mps"
    
    # Reranking parameters
    max_candidates: int = 50
    batch_size: int = 32
    max_length: int = 512
    
    # Performance thresholds
    max_latency_ms: int = 200
    fallback_to_fast_reranker: bool = True
    fast_reranker_threshold: int = 100  # Switch to fast reranker if more candidates
    
    # Training and fine-tuning
    enable_online_learning: bool = False
    feedback_weight: float = 0.1
    update_frequency: int = 1000
    
    def __post_init__(self):
        """Validate neural reranking configuration."""
        if self.max_candidates <= 0:
            raise ValueError("Max candidates must be positive")
        if self.batch_size <= 0:
            raise ValueError("Batch size must be positive")
        if self.max_length <= 0:
            raise ValueError("Max length must be positive")
        if self.max_latency_ms <= 0:
            raise ValueError("Max latency must be positive")


@dataclass
class GraphRetrievalConfig:
    """Configuration for graph-based retrieval (future implementation)."""
    
    enabled: bool = False
    
    # Graph construction
    enable_entity_linking: bool = True
    enable_cross_references: bool = True
    similarity_threshold: float = 0.8
    max_connections_per_document: int = 10
    
    # Graph algorithms
    use_pagerank: bool = True
    pagerank_damping: float = 0.85
    use_community_detection: bool = False
    community_algorithm: str = "louvain"
    
    # Retrieval strategies
    max_graph_hops: int = 2
    graph_weight_decay: float = 0.5
    combine_with_vector_search: bool = True
    
    def __post_init__(self):
        """Validate graph retrieval configuration."""
        if not 0 <= self.similarity_threshold <= 1:
            raise ValueError("Similarity threshold must be between 0 and 1")
        if not 0 <= self.pagerank_damping <= 1:
            raise ValueError("PageRank damping must be between 0 and 1")
        if self.max_graph_hops <= 0:
            raise ValueError("Max graph hops must be positive")


@dataclass
class AnalyticsConfig:
    """Configuration for analytics and monitoring."""
    
    enabled: bool = True
    
    # Metrics collection
    collect_query_metrics: bool = True
    collect_performance_metrics: bool = True
    collect_quality_metrics: bool = True
    
    # Dashboard configuration
    dashboard_enabled: bool = False
    dashboard_port: int = 8050
    dashboard_host: str = "localhost"
    auto_refresh_seconds: int = 5
    
    # Data retention
    metrics_retention_days: int = 30
    detailed_logs_retention_days: int = 7
    
    # Visualization options
    enable_real_time_plots: bool = True
    enable_query_analysis: bool = True
    enable_performance_heatmaps: bool = True
    
    def __post_init__(self):
        """Validate analytics configuration."""
        if self.dashboard_port <= 0 or self.dashboard_port > 65535:
            raise ValueError("Dashboard port must be between 1 and 65535")
        if self.metrics_retention_days <= 0:
            raise ValueError("Metrics retention must be positive")


@dataclass
class ExperimentsConfig:
    """Configuration for A/B testing and experiments."""
    
    enabled: bool = False
    
    # Assignment strategy
    assignment_method: str = "deterministic"  # "random", "deterministic", "contextual"
    assignment_key_field: str = "query_hash"
    
    # Experiment tracking
    experiment_id: Optional[str] = None
    control_config: Optional[Dict[str, Any]] = None
    treatment_configs: List[Dict[str, Any]] = field(default_factory=list)
    
    # Statistical parameters
    min_sample_size: int = 100
    confidence_level: float = 0.95
    effect_size_threshold: float = 0.05
    
    # Monitoring
    auto_winner_detection: bool = True
    max_experiment_duration_days: int = 30
    early_stopping_enabled: bool = True
    
    def __post_init__(self):
        """Validate experiments configuration."""
        valid_methods = ["random", "deterministic", "contextual"]
        if self.assignment_method not in valid_methods:
            raise ValueError(f"Assignment method must be one of {valid_methods}")
        
        if not 0 < self.confidence_level < 1:
            raise ValueError("Confidence level must be between 0 and 1")
        
        if self.effect_size_threshold <= 0:
            raise ValueError("Effect size threshold must be positive")


@dataclass
class AdvancedRetrieverConfig:
    """Complete configuration for the advanced retriever."""
    
    # Component configurations
    backends: BackendConfig = field(default_factory=BackendConfig)
    hybrid_search: HybridSearchConfig = field(default_factory=HybridSearchConfig)
    neural_reranking: NeuralRerankingConfig = field(default_factory=NeuralRerankingConfig)
    graph_retrieval: GraphRetrievalConfig = field(default_factory=GraphRetrievalConfig)
    analytics: AnalyticsConfig = field(default_factory=AnalyticsConfig)
    experiments: ExperimentsConfig = field(default_factory=ExperimentsConfig)
    
    # Legacy compatibility
    legacy_mode: bool = False
    legacy_fallback: bool = True
    
    # Performance settings
    max_total_latency_ms: int = 700
    enable_caching: bool = True
    cache_size: int = 1000
    
    # Feature flags
    enable_all_features: bool = False
    feature_flags: Dict[str, bool] = field(default_factory=lambda: {
        "weaviate_backend": True,
        "neural_reranking": False,
        "graph_retrieval": False,
        "analytics_dashboard": False,
        "ab_testing": False
    })
    
    def __post_init__(self):
        """Validate complete configuration."""
        if self.max_total_latency_ms <= 0:
            raise ValueError("Max total latency must be positive")
        if self.cache_size < 0:
            raise ValueError("Cache size cannot be negative")
        
        # Auto-enable features if enable_all_features is True
        if self.enable_all_features:
            for key in self.feature_flags:
                self.feature_flags[key] = True
            
            # Enable sub-component features
            self.neural_reranking.enabled = True
            self.graph_retrieval.enabled = True
            self.analytics.enabled = True
            self.analytics.dashboard_enabled = True
            self.experiments.enabled = True
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'AdvancedRetrieverConfig':
        """Create configuration from dictionary."""
        # Extract sub-configurations
        backends_config = BackendConfig(**config_dict.get('backends', {}))
        hybrid_config = HybridSearchConfig(**config_dict.get('hybrid_search', {}))
        reranking_config = NeuralRerankingConfig(**config_dict.get('neural_reranking', {}))
        graph_config = GraphRetrievalConfig(**config_dict.get('graph_retrieval', {}))
        analytics_config = AnalyticsConfig(**config_dict.get('analytics', {}))
        experiments_config = ExperimentsConfig(**config_dict.get('experiments', {}))
        
        # Extract main configuration
        main_config = {
            k: v for k, v in config_dict.items()
            if k not in ['backends', 'hybrid_search', 'neural_reranking', 
                        'graph_retrieval', 'analytics', 'experiments']
        }
        
        return cls(
            backends=backends_config,
            hybrid_search=hybrid_config,
            neural_reranking=reranking_config,
            graph_retrieval=graph_config,
            analytics=analytics_config,
            experiments=experiments_config,
            **main_config
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'backends': {
                'primary_backend': self.backends.primary_backend,
                'fallback_enabled': self.backends.fallback_enabled,
                'fallback_backend': self.backends.fallback_backend,
                'faiss': self.backends.faiss,
                'weaviate': self.backends.weaviate.to_dict() if self.backends.weaviate else None,
                'enable_hot_swap': self.backends.enable_hot_swap,
                'health_check_interval_seconds': self.backends.health_check_interval_seconds,
                'switch_threshold_error_rate': self.backends.switch_threshold_error_rate
            },
            'hybrid_search': {
                'enabled': self.hybrid_search.enabled,
                'dense_weight': self.hybrid_search.dense_weight,
                'sparse_weight': self.hybrid_search.sparse_weight,
                'graph_weight': self.hybrid_search.graph_weight,
                'fusion_method': self.hybrid_search.fusion_method,
                'rrf_k': self.hybrid_search.rrf_k,
                'adaptive_weights': self.hybrid_search.adaptive_weights,
                'query_dependent_weighting': self.hybrid_search.query_dependent_weighting,
                'normalization_method': self.hybrid_search.normalization_method
            },
            'neural_reranking': {
                'enabled': self.neural_reranking.enabled,
                'model_name': self.neural_reranking.model_name,
                'model_type': self.neural_reranking.model_type,
                'device': self.neural_reranking.device,
                'max_candidates': self.neural_reranking.max_candidates,
                'batch_size': self.neural_reranking.batch_size,
                'max_length': self.neural_reranking.max_length
            },
            'graph_retrieval': {
                'enabled': self.graph_retrieval.enabled,
                'enable_entity_linking': self.graph_retrieval.enable_entity_linking,
                'enable_cross_references': self.graph_retrieval.enable_cross_references,
                'similarity_threshold': self.graph_retrieval.similarity_threshold,
                'use_pagerank': self.graph_retrieval.use_pagerank,
                'pagerank_damping': self.graph_retrieval.pagerank_damping
            },
            'analytics': {
                'enabled': self.analytics.enabled,
                'collect_query_metrics': self.analytics.collect_query_metrics,
                'dashboard_enabled': self.analytics.dashboard_enabled,
                'dashboard_port': self.analytics.dashboard_port,
                'metrics_retention_days': self.analytics.metrics_retention_days
            },
            'experiments': {
                'enabled': self.experiments.enabled,
                'assignment_method': self.experiments.assignment_method,
                'min_sample_size': self.experiments.min_sample_size,
                'confidence_level': self.experiments.confidence_level,
                'auto_winner_detection': self.experiments.auto_winner_detection
            },
            'legacy_mode': self.legacy_mode,
            'legacy_fallback': self.legacy_fallback,
            'max_total_latency_ms': self.max_total_latency_ms,
            'enable_caching': self.enable_caching,
            'cache_size': self.cache_size,
            'enable_all_features': self.enable_all_features,
            'feature_flags': self.feature_flags
        }
    
    def get_enabled_features(self) -> List[str]:
        """Get list of enabled features."""
        enabled = []
        
        if self.feature_flags.get('weaviate_backend', False):
            enabled.append('weaviate_backend')
        if self.neural_reranking.enabled:
            enabled.append('neural_reranking')
        if self.graph_retrieval.enabled:
            enabled.append('graph_retrieval')
        if self.analytics.dashboard_enabled:
            enabled.append('analytics_dashboard')
        if self.experiments.enabled:
            enabled.append('ab_testing')
        
        return enabled