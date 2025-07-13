"""
Graph retrieval configuration for Epic 2 Week 2.

This module provides configuration classes for graph-based retrieval components,
following the established configuration patterns used throughout the system.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class GraphBuilderConfig:
    """Configuration for DocumentGraphBuilder."""
    implementation: str = "networkx"
    node_types: List[str] = field(default_factory=lambda: ["concept", "protocol", "architecture", "extension"])
    relationship_types: List[str] = field(default_factory=lambda: ["implements", "extends", "requires", "conflicts"])
    max_graph_size: int = 10000
    update_strategy: str = "incremental"
    enable_pruning: bool = True
    pruning_threshold: float = 0.1


@dataclass
class EntityExtractionConfig:
    """Configuration for EntityExtractor."""
    implementation: str = "spacy"
    model: str = "en_core_web_sm"
    entity_types: List[str] = field(default_factory=lambda: ["TECH", "PROTOCOL", "ARCH"])
    confidence_threshold: float = 0.8
    batch_size: int = 32
    custom_patterns: Dict[str, List[str]] = field(default_factory=dict)
    enable_custom_entities: bool = True


@dataclass
class RelationshipDetectionConfig:
    """Configuration for RelationshipMapper."""
    implementation: str = "semantic"
    similarity_threshold: float = 0.7
    relationship_model: str = "sentence_transformer"
    max_relationships_per_node: int = 20
    enable_bidirectional: bool = True
    weight_decay_factor: float = 0.9


@dataclass
class GraphRetrievalConfig:
    """Configuration for GraphRetriever."""
    algorithms: List[str] = field(default_factory=lambda: ["shortest_path", "random_walk", "subgraph_expansion"])
    max_graph_results: int = 10
    max_path_length: int = 3
    random_walk_steps: int = 10
    subgraph_radius: int = 2
    score_aggregation: str = "weighted_average"
    enable_path_scoring: bool = True


@dataclass
class GraphAnalyticsConfig:
    """Configuration for GraphAnalytics."""
    enabled: bool = True
    collect_graph_metrics: bool = True
    collect_retrieval_metrics: bool = True
    enable_visualization: bool = False  # Disabled by default for performance
    visualization_max_nodes: int = 100
    metrics_retention_hours: int = 24


@dataclass
class GraphConfig:
    """
    Main configuration class for graph-based retrieval.
    
    This class aggregates all graph-related configuration and provides
    methods for creating configurations from dictionaries and YAML files.
    """
    enabled: bool = True
    builder: GraphBuilderConfig = field(default_factory=GraphBuilderConfig)
    entity_extraction: EntityExtractionConfig = field(default_factory=EntityExtractionConfig)
    relationship_detection: RelationshipDetectionConfig = field(default_factory=RelationshipDetectionConfig)
    retrieval: GraphRetrievalConfig = field(default_factory=GraphRetrievalConfig)
    analytics: GraphAnalyticsConfig = field(default_factory=GraphAnalyticsConfig)
    
    # Performance settings
    max_memory_mb: int = 500
    enable_caching: bool = True
    cache_size: int = 1000
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "GraphConfig":
        """
        Create GraphConfig from dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            GraphConfig instance
        """
        try:
            # Extract main config
            enabled = config_dict.get("enabled", True)
            max_memory_mb = config_dict.get("max_memory_mb", 500)
            enable_caching = config_dict.get("enable_caching", True)
            cache_size = config_dict.get("cache_size", 1000)
            
            # Create sub-configurations
            builder_config = GraphBuilderConfig()
            if "builder" in config_dict:
                builder_dict = config_dict["builder"].get("config", {})
                builder_config = GraphBuilderConfig(
                    implementation=config_dict["builder"].get("implementation", "networkx"),
                    node_types=builder_dict.get("node_types", builder_config.node_types),
                    relationship_types=builder_dict.get("relationship_types", builder_config.relationship_types),
                    max_graph_size=builder_dict.get("max_graph_size", 10000),
                    update_strategy=builder_dict.get("update_strategy", "incremental"),
                    enable_pruning=builder_dict.get("enable_pruning", True),
                    pruning_threshold=builder_dict.get("pruning_threshold", 0.1)
                )
            
            entity_config = EntityExtractionConfig()
            if "entity_extraction" in config_dict:
                entity_dict = config_dict["entity_extraction"].get("config", {})
                entity_config = EntityExtractionConfig(
                    implementation=config_dict["entity_extraction"].get("implementation", "spacy"),
                    model=entity_dict.get("model", "en_core_web_sm"),
                    entity_types=entity_dict.get("entity_types", entity_config.entity_types),
                    confidence_threshold=entity_dict.get("confidence_threshold", 0.8),
                    batch_size=entity_dict.get("batch_size", 32),
                    custom_patterns=entity_dict.get("custom_patterns", {}),
                    enable_custom_entities=entity_dict.get("enable_custom_entities", True)
                )
            
            relationship_config = RelationshipDetectionConfig()
            if "relationship_detection" in config_dict:
                rel_dict = config_dict["relationship_detection"].get("config", {})
                relationship_config = RelationshipDetectionConfig(
                    implementation=config_dict["relationship_detection"].get("implementation", "semantic"),
                    similarity_threshold=rel_dict.get("similarity_threshold", 0.7),
                    relationship_model=rel_dict.get("relationship_model", "sentence_transformer"),
                    max_relationships_per_node=rel_dict.get("max_relationships_per_node", 20),
                    enable_bidirectional=rel_dict.get("enable_bidirectional", True),
                    weight_decay_factor=rel_dict.get("weight_decay_factor", 0.9)
                )
            
            retrieval_config = GraphRetrievalConfig()
            if "retrieval" in config_dict:
                ret_dict = config_dict["retrieval"]
                retrieval_config = GraphRetrievalConfig(
                    algorithms=ret_dict.get("algorithms", retrieval_config.algorithms),
                    max_graph_results=ret_dict.get("max_graph_results", 10),
                    max_path_length=ret_dict.get("max_path_length", 3),
                    random_walk_steps=ret_dict.get("random_walk_steps", 10),
                    subgraph_radius=ret_dict.get("subgraph_radius", 2),
                    score_aggregation=ret_dict.get("score_aggregation", "weighted_average"),
                    enable_path_scoring=ret_dict.get("enable_path_scoring", True)
                )
            
            analytics_config = GraphAnalyticsConfig()
            if "analytics" in config_dict:
                analytics_dict = config_dict["analytics"]
                analytics_config = GraphAnalyticsConfig(
                    enabled=analytics_dict.get("enabled", True),
                    collect_graph_metrics=analytics_dict.get("collect_graph_metrics", True),
                    collect_retrieval_metrics=analytics_dict.get("collect_retrieval_metrics", True),
                    enable_visualization=analytics_dict.get("enable_visualization", False),
                    visualization_max_nodes=analytics_dict.get("visualization_max_nodes", 100),
                    metrics_retention_hours=analytics_dict.get("metrics_retention_hours", 24)
                )
            
            return cls(
                enabled=enabled,
                builder=builder_config,
                entity_extraction=entity_config,
                relationship_detection=relationship_config,
                retrieval=retrieval_config,
                analytics=analytics_config,
                max_memory_mb=max_memory_mb,
                enable_caching=enable_caching,
                cache_size=cache_size
            )
            
        except Exception as e:
            logger.error(f"Failed to create GraphConfig from dict: {str(e)}")
            # Return default configuration on error
            return cls()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert GraphConfig to dictionary.
        
        Returns:
            Configuration dictionary
        """
        return {
            "enabled": self.enabled,
            "builder": {
                "implementation": self.builder.implementation,
                "config": {
                    "node_types": self.builder.node_types,
                    "relationship_types": self.builder.relationship_types,
                    "max_graph_size": self.builder.max_graph_size,
                    "update_strategy": self.builder.update_strategy,
                    "enable_pruning": self.builder.enable_pruning,
                    "pruning_threshold": self.builder.pruning_threshold
                }
            },
            "entity_extraction": {
                "implementation": self.entity_extraction.implementation,
                "config": {
                    "model": self.entity_extraction.model,
                    "entity_types": self.entity_extraction.entity_types,
                    "confidence_threshold": self.entity_extraction.confidence_threshold,
                    "batch_size": self.entity_extraction.batch_size,
                    "custom_patterns": self.entity_extraction.custom_patterns,
                    "enable_custom_entities": self.entity_extraction.enable_custom_entities
                }
            },
            "relationship_detection": {
                "implementation": self.relationship_detection.implementation,
                "config": {
                    "similarity_threshold": self.relationship_detection.similarity_threshold,
                    "relationship_model": self.relationship_detection.relationship_model,
                    "max_relationships_per_node": self.relationship_detection.max_relationships_per_node,
                    "enable_bidirectional": self.relationship_detection.enable_bidirectional,
                    "weight_decay_factor": self.relationship_detection.weight_decay_factor
                }
            },
            "retrieval": {
                "algorithms": self.retrieval.algorithms,
                "max_graph_results": self.retrieval.max_graph_results,
                "max_path_length": self.retrieval.max_path_length,
                "random_walk_steps": self.retrieval.random_walk_steps,
                "subgraph_radius": self.retrieval.subgraph_radius,
                "score_aggregation": self.retrieval.score_aggregation,
                "enable_path_scoring": self.retrieval.enable_path_scoring
            },
            "analytics": {
                "enabled": self.analytics.enabled,
                "collect_graph_metrics": self.analytics.collect_graph_metrics,
                "collect_retrieval_metrics": self.analytics.collect_retrieval_metrics,
                "enable_visualization": self.analytics.enable_visualization,
                "visualization_max_nodes": self.analytics.visualization_max_nodes,
                "metrics_retention_hours": self.analytics.metrics_retention_hours
            },
            "max_memory_mb": self.max_memory_mb,
            "enable_caching": self.enable_caching,
            "cache_size": self.cache_size
        }
    
    def validate(self) -> List[str]:
        """
        Validate configuration and return list of issues.
        
        Returns:
            List of validation error messages
        """
        issues = []
        
        # Validate builder config
        if self.builder.max_graph_size <= 0:
            issues.append("builder.max_graph_size must be positive")
        
        if not self.builder.node_types:
            issues.append("builder.node_types cannot be empty")
        
        if not self.builder.relationship_types:
            issues.append("builder.relationship_types cannot be empty")
        
        # Validate entity extraction config
        if self.entity_extraction.confidence_threshold < 0 or self.entity_extraction.confidence_threshold > 1:
            issues.append("entity_extraction.confidence_threshold must be between 0 and 1")
        
        if self.entity_extraction.batch_size <= 0:
            issues.append("entity_extraction.batch_size must be positive")
        
        # Validate relationship detection config
        if self.relationship_detection.similarity_threshold < 0 or self.relationship_detection.similarity_threshold > 1:
            issues.append("relationship_detection.similarity_threshold must be between 0 and 1")
        
        if self.relationship_detection.max_relationships_per_node <= 0:
            issues.append("relationship_detection.max_relationships_per_node must be positive")
        
        # Validate retrieval config
        if not self.retrieval.algorithms:
            issues.append("retrieval.algorithms cannot be empty")
        
        if self.retrieval.max_graph_results <= 0:
            issues.append("retrieval.max_graph_results must be positive")
        
        # Validate performance settings
        if self.max_memory_mb <= 0:
            issues.append("max_memory_mb must be positive")
        
        if self.cache_size <= 0:
            issues.append("cache_size must be positive")
        
        return issues