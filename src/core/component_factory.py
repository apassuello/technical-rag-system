"""
Component Factory for Phase 3 Direct Wiring Architecture.

This module provides a lightweight factory for direct component instantiation,
eliminating the ComponentRegistry overhead and improving startup performance.
It supports both legacy and unified architectures with type-safe component creation.
"""

import logging
import time
import hashlib
from typing import Dict, Type, Any, Optional, Union
from pathlib import Path
from collections import defaultdict, OrderedDict

from .interfaces import (
    DocumentProcessor, 
    Embedder, 
    VectorStore, 
    Retriever, 
    AnswerGenerator,
    QueryProcessor
)

# Component classes will be imported lazily to avoid circular imports
# See _get_component_class() method for lazy loading implementation

logger = logging.getLogger(__name__)


class ComponentFactory:
    """
    Lightweight factory for direct component instantiation.
    
    This factory replaces the ComponentRegistry with direct class mappings,
    eliminating lookup overhead and improving startup performance by ~20%.
    It maintains type safety and provides clear error messages.
    
    Features:
    - Direct component class mapping (no registry lookup)
    - Type-safe instantiation with validation
    - Support for both legacy and unified architectures
    - Comprehensive error handling with actionable messages
    - Performance optimized for production workloads
    
    Example:
        factory = ComponentFactory()
        
        # Create components directly
        processor = factory.create_processor("hybrid_pdf", chunk_size=1000)
        embedder = factory.create_embedder("sentence_transformer", use_mps=True)
        retriever = factory.create_retriever("unified", embedder=embedder, dense_weight=0.7)
    """
    
    # Component type mappings - module paths for lazy loading
    _PROCESSORS: Dict[str, str] = {
        "hybrid_pdf": "src.components.processors.document_processor.ModularDocumentProcessor",
        "modular": "src.components.processors.document_processor.ModularDocumentProcessor",
        "pdf_processor": "src.components.processors.document_processor.ModularDocumentProcessor",  # Fixed: redirect to working implementation
        "legacy_pdf": "src.components.processors.document_processor.ModularDocumentProcessor",  # Fixed: redirect to working implementation
    }
    
    _EMBEDDERS: Dict[str, str] = {
        "modular": "src.components.embedders.modular_embedder.ModularEmbedder",
        "sentence_transformer": "src.components.embedders.sentence_transformer_embedder.SentenceTransformerEmbedder",
        "sentence_transformers": "src.components.embedders.sentence_transformer_embedder.SentenceTransformerEmbedder",  # Alias for compatibility
    }
    
    _VECTOR_STORES: Dict[str, str] = {
        # Legacy vector stores removed - functionality moved to UnifiedRetriever
        # "faiss": "src.components.vector_stores.faiss_store.FAISSVectorStore",
    }
    
    _RETRIEVERS: Dict[str, str] = {
        # Legacy Phase 1 architecture moved to archive
        # "hybrid": "src.components.retrievers.hybrid_retriever.HybridRetriever",
        "unified": "src.components.retrievers.modular_unified_retriever.ModularUnifiedRetriever",  # Fixed: redirect to working implementation
        "modular_unified": "src.components.retrievers.modular_unified_retriever.ModularUnifiedRetriever",
        # Note: enhanced_modular_unified removed - Epic 2 features now handled via advanced config transformation
    }
    
    _GENERATORS: Dict[str, str] = {
        "adaptive": "src.components.generators.epic1_answer_generator.Epic1AnswerGenerator",  # Epic 1 Multi-Model Generator
        "adaptive_generator": "src.components.generators.epic1_answer_generator.Epic1AnswerGenerator",  # Alias for compatibility
        "adaptive_modular": "src.components.generators.answer_generator.AnswerGenerator",  # New modular implementation
        "answer_generator": "src.components.generators.answer_generator.AnswerGenerator",  # Alias for intuitive naming
        "epic1": "src.components.generators.epic1_answer_generator.Epic1AnswerGenerator",  # Epic 1 Multi-Model Generator
        "epic1_multi_model": "src.components.generators.epic1_answer_generator.Epic1AnswerGenerator",  # Alias for Epic 1
    }
    
    _QUERY_PROCESSORS: Dict[str, str] = {
        "modular": "src.components.query_processors.modular_query_processor.ModularQueryProcessor",
        "modular_query_processor": "src.components.query_processors.modular_query_processor.ModularQueryProcessor",  # Alias for compatibility
        "domain_aware": "src.components.query_processors.domain_aware_query_processor.DomainAwareQueryProcessor",  # Epic 1 Phase 1 Domain-Aware Processor
        "epic1_domain_aware": "src.components.query_processors.domain_aware_query_processor.DomainAwareQueryProcessor",  # Alias for Epic 1
        "intelligent": "src.components.query_processors.intelligent_query_processor.IntelligentQueryProcessor",  # Epic 5 Phase 2 Block 3 Intelligent Processor
        "epic5_intelligent": "src.components.query_processors.intelligent_query_processor.IntelligentQueryProcessor",  # Alias for Epic 5
    }
    
    # Query analyzer implementations (used by ModularQueryProcessor)
    _QUERY_ANALYZERS: Dict[str, str] = {
        "nlp": "src.components.query_processors.analyzers.nlp_analyzer.NLPAnalyzer",
        "rule_based": "src.components.query_processors.analyzers.rule_based_analyzer.RuleBasedAnalyzer",
        "epic1": "src.components.query_processors.analyzers.epic1_query_analyzer.Epic1QueryAnalyzer",
        "epic1_ml": "src.components.query_processors.analyzers.epic1_ml_analyzer.Epic1MLAnalyzer",  # Epic 1 ML-powered analyzer
        "epic1_ml_adapter": "src.components.query_processors.analyzers.epic_ml_adapter.EpicMLAdapter",  # Epic 1 with trained models
    }

    # Epic 5: Tool implementations (Phase 1)
    _TOOLS: Dict[str, str] = {
        "calculator": "src.components.query_processors.tools.implementations.calculator_tool.CalculatorTool",
        "code_analyzer": "src.components.query_processors.tools.implementations.code_analyzer_tool.CodeAnalyzerTool",
        "document_search": "src.components.query_processors.tools.implementations.document_search_tool.DocumentSearchTool",
    }

    # Epic 5: Memory implementations (Phase 2 Block 1)
    _MEMORY: Dict[str, str] = {
        "conversation": "src.components.query_processors.agents.memory.conversation_memory.ConversationMemory",
        "working": "src.components.query_processors.agents.memory.working_memory.WorkingMemory",
    }

    # Epic 5: Tool registry (Phase 1)
    _TOOL_REGISTRY: str = "src.components.query_processors.tools.tool_registry.ToolRegistry"
    
    # Phase 4: Performance monitoring and caching
    _performance_metrics: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "creation_count": 0,
        "total_time": 0.0,
        "average_time": 0.0,
        "min_time": float('inf'),
        "max_time": 0.0,
        "last_created": None
    })
    
    # Component cache for reusable instances (LRU with max size)
    _component_cache: OrderedDict[str, Any] = OrderedDict()
    _cache_max_size: int = 10  # Max cached components
    _cacheable_types = {"embedder"}  # Only cache expensive components
    
    # Cache metrics tracking (configurable for production)
    _cache_metrics_enabled: bool = True  # Can be disabled for production
    _cache_hits: int = 0
    _cache_misses: int = 0
    _cache_operations: Dict[str, int] = defaultdict(int)
    
    # Class cache for lazy loading
    _class_cache: Dict[str, Type] = {}
    
    @classmethod
    def _get_component_class(cls, module_path: str) -> Type:
        """
        Lazily import and cache component class.
        
        Args:
            module_path: Module path in format "src.package.module.ClassName"
            
        Returns:
            Component class
        """
        if module_path in cls._class_cache:
            return cls._class_cache[module_path]
        
        try:
            # Split module path and class name
            parts = module_path.split('.')
            class_name = parts[-1]
            module_path_only = '.'.join(parts[:-1])
            
            # Import module using absolute import
            from importlib import import_module
            module = import_module(module_path_only)
            
            # Get class from module
            component_class = getattr(module, class_name)
            
            # Cache for future use
            cls._class_cache[module_path] = component_class
            
            return component_class
            
        except (ImportError, AttributeError) as e:
            raise ImportError(f"Failed to import {module_path}: {e}") from e
    
    @classmethod
    def get_performance_metrics(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get performance metrics for component creation.
        
        Returns:
            Dictionary with creation metrics by component type
        """
        return dict(cls._performance_metrics)
    
    @classmethod
    def reset_performance_metrics(cls) -> None:
        """Reset all performance metrics."""
        cls._performance_metrics.clear()
    
    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """
        Get component cache statistics.
        
        Returns:
            Dictionary with cache size, hit rate, etc.
        """
        total_operations = cls._cache_hits + cls._cache_misses
        hit_rate = cls._cache_hits / total_operations if total_operations > 0 else 0.0
        
        return {
            "cache_size": len(cls._component_cache),
            "max_size": cls._cache_max_size,
            "cached_components": list(cls._component_cache.keys()),
            "cacheable_types": cls._cacheable_types,
            "metrics_enabled": cls._cache_metrics_enabled,
            "hits": cls._cache_hits,
            "misses": cls._cache_misses,
            "total_operations": total_operations,
            "hit_rate": hit_rate,
            "operations_by_type": dict(cls._cache_operations)
        }
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear the component cache."""
        cls._component_cache.clear()
    
    @classmethod
    def enable_cache_metrics(cls, enabled: bool = True) -> None:
        """
        Enable/disable cache metrics tracking.
        
        Args:
            enabled: Whether to enable metrics tracking
        """
        cls._cache_metrics_enabled = enabled
    
    @classmethod
    def reset_cache_metrics(cls) -> None:
        """Reset cache metrics counters."""
        cls._cache_hits = 0
        cls._cache_misses = 0
        cls._cache_operations.clear()
    
    @classmethod
    def _get_cache_key(cls, component_type: str, **kwargs) -> str:
        """
        Generate cache key for component configuration.
        
        Args:
            component_type: Type of component
            **kwargs: Component configuration
            
        Returns:
            Cache key string
        """
        # Create deterministic key from component type and config
        config_str = str(sorted(kwargs.items()))
        key_material = f"{component_type}:{config_str}"
        return hashlib.md5(key_material.encode()).hexdigest()[:16]
    
    @classmethod
    def _get_from_cache(cls, cache_key: str) -> Optional[Any]:
        """
        Get component from cache (LRU update).
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached component or None
        """
        if cache_key in cls._component_cache:
            # Track cache hit
            if cls._cache_metrics_enabled:
                cls._cache_hits += 1
                component_type = cache_key.split('_')[0]  # Extract component type from key
                cls._cache_operations[f"hit_{component_type}"] += 1
            
            # Move to end (most recently used)
            component = cls._component_cache.pop(cache_key)
            cls._component_cache[cache_key] = component
            return component
        else:
            # Track cache miss
            if cls._cache_metrics_enabled:
                cls._cache_misses += 1
                component_type = cache_key.split('_')[0]  # Extract component type from key
                cls._cache_operations[f"miss_{component_type}"] += 1
        
        return None
    
    @classmethod
    def _add_to_cache(cls, cache_key: str, component: Any) -> None:
        """
        Add component to cache with LRU eviction.
        
        Args:
            cache_key: Cache key
            component: Component to cache
        """
        # Remove oldest if at capacity
        if len(cls._component_cache) >= cls._cache_max_size:
            cls._component_cache.popitem(last=False)  # Remove oldest
        
        cls._component_cache[cache_key] = component
    
    @classmethod
    def _track_performance(cls, component_type: str, creation_time: float) -> None:
        """
        Track performance metrics for component creation.
        
        Args:
            component_type: Type of component created
            creation_time: Time taken to create component in seconds
        """
        metrics = cls._performance_metrics[component_type]
        metrics["creation_count"] += 1
        metrics["total_time"] += creation_time
        metrics["average_time"] = metrics["total_time"] / metrics["creation_count"]
        metrics["min_time"] = min(metrics["min_time"], creation_time)
        metrics["max_time"] = max(metrics["max_time"], creation_time)
        metrics["last_created"] = time.time()
    
    @classmethod
    def _create_with_tracking(cls, component_class: Type, component_type: str, use_cache: bool = False, **kwargs) -> Any:
        """
        Create component with performance tracking and optional caching.
        
        Args:
            component_class: Class to instantiate
            component_type: Type identifier for tracking
            use_cache: Whether to use component caching
            **kwargs: Constructor arguments
            
        Returns:
            Instantiated component
        """
        # Check cache first if caching is enabled
        cache_key = None
        if use_cache:
            cache_key = cls._get_cache_key(component_type, **kwargs)
            cached_component = cls._get_from_cache(cache_key)
            if cached_component is not None:
                logger.debug(f"Cache hit for {component_type}")
                cls._track_performance(f"{component_type}_cached", 0.0)
                return cached_component
        
        start_time = time.time()
        try:
            # Log component creation with essential information (INFO level for visibility)
            component = component_class(**kwargs)
            creation_time = time.time() - start_time
            
            # Enhanced logging with component details
            component_name = component.__class__.__name__
            component_module = component.__class__.__module__
            logger.info(f"🏭 ComponentFactory created: {component_name} "
                       f"(type={component_type}, module={component_module}, "
                       f"time={creation_time:.3f}s)")
            
            # Log component-specific info if available
            sub_components_logged = False
            
            # Check for ModularEmbedder and ModularDocumentProcessor sub-components
            if hasattr(component, 'get_sub_components'):
                try:
                    sub_info = component.get_sub_components()
                    if isinstance(sub_info, dict) and 'components' in sub_info:
                        components = sub_info['components']
                        sub_components = [f"{k}:{v.get('class', 'Unknown')}" for k, v in components.items()]
                        logger.info(f"  └─ Sub-components: {', '.join(sub_components)}")
                        sub_components_logged = True
                except Exception:
                    pass  # Don't fail component creation on logging issues
            
            # Fallback to legacy get_component_info for backward compatibility
            if not sub_components_logged and hasattr(component, 'get_component_info'):
                try:
                    info = component.get_component_info()
                    if isinstance(info, dict) and len(info) > 0:
                        sub_components = [f"{k}:{v.get('class', 'Unknown')}" for k, v in info.items()]
                        logger.info(f"  └─ Sub-components: {', '.join(sub_components)}")
                except Exception:
                    pass  # Don't fail component creation on logging issues
            
            # Add to cache if caching is enabled
            if use_cache and cache_key:
                cls._add_to_cache(cache_key, component)
            
            cls._track_performance(component_type, creation_time)
            return component
        except Exception as e:
            creation_time = time.time() - start_time
            cls._track_performance(f"{component_type}_failed", creation_time)
            raise
    
    @classmethod
    def create_processor(cls, processor_type: str, **kwargs) -> DocumentProcessor:
        """
        Create a document processor instance.
        
        Args:
            processor_type: Type of processor ("hybrid_pdf" or "pdf_processor")
            **kwargs: Arguments to pass to the processor constructor
            
        Returns:
            Instantiated DocumentProcessor
            
        Raises:
            ValueError: If processor type is not supported
            TypeError: If constructor arguments are invalid
        """
        if processor_type not in cls._PROCESSORS:
            available = list(cls._PROCESSORS.keys())
            raise ValueError(
                f"Unknown processor type '{processor_type}'. "
                f"Available processors: {available}"
            )
        
        processor_module_path = cls._PROCESSORS[processor_type]
        processor_class = cls._get_component_class(processor_module_path)
        
        try:
            return cls._create_with_tracking(
                processor_class, 
                f"processor_{processor_type}", 
                **kwargs
            )
        except Exception as e:
            raise TypeError(
                f"Failed to create processor '{processor_type}': {e}. "
                f"Check constructor arguments: {kwargs}"
            ) from e
    
    @classmethod
    def create_embedder(cls, embedder_type: str, **kwargs) -> Embedder:
        """
        Create an embedder instance.
        
        Args:
            embedder_type: Type of embedder ("sentence_transformer")
            **kwargs: Arguments to pass to the embedder constructor
            
        Returns:
            Instantiated Embedder
            
        Raises:
            ValueError: If embedder type is not supported
            TypeError: If constructor arguments are invalid
        """
        if embedder_type not in cls._EMBEDDERS:
            available = list(cls._EMBEDDERS.keys())
            raise ValueError(
                f"Unknown embedder type '{embedder_type}'. "
                f"Available embedders: {available}"
            )
        
        embedder_module_path = cls._EMBEDDERS[embedder_type]
        embedder_class = cls._get_component_class(embedder_module_path)
        
        try:
            # Handle different configuration formats
            processed_kwargs = kwargs.copy()
            
            # If nested config format is used, flatten it for SentenceTransformerEmbedder
            if 'config' in kwargs and embedder_type in ['sentence_transformer', 'sentence_transformers']:
                config = kwargs.pop('config')
                processed_kwargs.update(config)
                processed_kwargs.pop('config', None)  # Remove the nested config
            
            # Use caching for embedders (expensive to create)
            return cls._create_with_tracking(
                embedder_class, 
                f"embedder_{embedder_type}", 
                use_cache=True,  # Enable caching for embedders
                **processed_kwargs
            )
        except Exception as e:
            raise TypeError(
                f"Failed to create embedder '{embedder_type}': {e}. "
                f"Check constructor arguments: {kwargs}"
            ) from e
    
    @classmethod
    def create_vector_store(cls, store_type: str, **kwargs) -> VectorStore:
        """
        Create a vector store instance.
        
        Args:
            store_type: Type of vector store ("faiss")
            **kwargs: Arguments to pass to the vector store constructor
            
        Returns:
            Instantiated VectorStore
            
        Raises:
            ValueError: If vector store type is not supported
            TypeError: If constructor arguments are invalid
        """
        if store_type not in cls._VECTOR_STORES:
            available = list(cls._VECTOR_STORES.keys())
            raise ValueError(
                f"Unknown vector store type '{store_type}'. "
                f"Available vector stores: {available}"
            )
        
        store_module_path = cls._VECTOR_STORES[store_type]
        store_class = cls._get_component_class(store_module_path)
        
        try:
            logger.debug(f"Creating {store_type} vector store with args: {kwargs}")
            return store_class(**kwargs)
        except Exception as e:
            raise TypeError(
                f"Failed to create vector store '{store_type}': {e}. "
                f"Check constructor arguments: {kwargs}"
            ) from e
    
    @classmethod
    def create_retriever(cls, retriever_type: str, **kwargs) -> Retriever:
        """
        Create a retriever instance.
        
        Args:
            retriever_type: Type of retriever ("unified" or "modular_unified")
            **kwargs: Arguments to pass to the retriever constructor
            
        Returns:
            Instantiated Retriever
            
        Raises:
            ValueError: If retriever type is not supported
            TypeError: If constructor arguments are invalid
        """
        if retriever_type not in cls._RETRIEVERS:
            available = list(cls._RETRIEVERS.keys())
            raise ValueError(
                f"Unknown retriever type '{retriever_type}'. "
                f"Available retrievers: {available}"
            )
        
        retriever_module_path = cls._RETRIEVERS[retriever_type]
        retriever_class = cls._get_component_class(retriever_module_path)
        
        try:
            logger.debug(f"Creating {retriever_type} retriever with args: {kwargs}")
            
            # Special handling for retrievers that need embedder + config pattern
            if retriever_type in ["modular_unified", "unified"]:
                # Extract embedder and config from kwargs
                embedder = kwargs.pop("embedder", None)
                if embedder is None:
                    raise ValueError(f"ModularUnifiedRetriever requires 'embedder' parameter")
                
                # All remaining kwargs become the config
                config = kwargs
                
                # Extract actual config if it's wrapped in a 'config' key
                if "config" in config and len(config) == 1:
                    actual_config = config["config"]
                else:
                    actual_config = config
                
                # Transform advanced configuration to ModularUnifiedRetriever format if needed
                if cls._is_advanced_config(actual_config):
                    actual_config = cls._transform_advanced_config(actual_config)
                
                # Use the actual config for retriever creation
                config = actual_config
                
                return cls._create_with_tracking(
                    retriever_class, 
                    f"retriever_{retriever_type}", 
                    config=config,
                    embedder=embedder
                )
            else:
                return cls._create_with_tracking(
                    retriever_class, 
                    f"retriever_{retriever_type}", 
                    **kwargs
                )
        except Exception as e:
            raise TypeError(
                f"Failed to create retriever '{retriever_type}': {e}. "
                f"Check constructor arguments: {kwargs}"
            ) from e
    
    @classmethod
    def _is_advanced_config(cls, config: Dict[str, Any]) -> bool:
        """
        Check if the configuration contains advanced features that need transformation.
        
        Args:
            config: Configuration dictionary to check
            
        Returns:
            True if advanced configuration is detected
        """
        # Check for advanced configuration indicators
        advanced_indicators = [
            "backends",
            "neural_reranking", 
            "graph_retrieval",
            "analytics",
            "experiments"
        ]
        
        # Check for new format neural reranking (reranker.type == "neural")
        reranker_config = config.get("reranker", {})
        if reranker_config.get("type") == "neural":
            return True
        
        # Check for new format graph fusion (fusion.type == "graph_enhanced_rrf")
        fusion_config = config.get("fusion", {})
        if fusion_config.get("type") == "graph_enhanced_rrf":
            return True
        
        return any(indicator in config for indicator in advanced_indicators)
    
    @classmethod
    def _transform_advanced_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform advanced configuration format to ModularUnifiedRetriever format.
        
        Args:
            config: Advanced configuration dictionary
            
        Returns:
            Transformed configuration for ModularUnifiedRetriever
        """
        logger.debug("Transforming advanced configuration for ModularUnifiedRetriever")
        
        # Extract base configuration elements
        transformed_config = {}
        
        # Configure vector index based on backend configuration
        if "backends" in config:
            transformed_config["vector_index"] = cls._transform_vector_index_config(config["backends"])
        
        # Configure sparse retriever (BM25)
        transformed_config["sparse"] = {
            "type": "bm25",
            "config": {
                "k1": 1.2,
                "b": 0.75,
                "lowercase": True,
                "preserve_technical_terms": True,
            }
        }
        
        # Configure fusion strategy
        transformed_config["fusion"] = cls._transform_fusion_config(config)
        
        # Configure reranker
        transformed_config["reranker"] = cls._transform_reranker_config(config)
        
        # Copy any other configuration that doesn't need transformation
        for key, value in config.items():
            if key not in ["backends", "neural_reranking", "graph_retrieval", "analytics", "experiments", "reranker"]:
                transformed_config[key] = value
        
        logger.debug(f"Transformed advanced config: {transformed_config}")
        return transformed_config
    
    @classmethod
    def _transform_vector_index_config(cls, backends_config: Dict[str, Any]) -> Dict[str, Any]:
        """Transform backend configuration to vector index configuration."""
        primary_backend = backends_config.get("primary_backend", "faiss")
        
        if primary_backend == "weaviate":
            if "weaviate" in backends_config:
                weaviate_config = backends_config["weaviate"]
                if isinstance(weaviate_config, dict):
                    return {
                        "type": "weaviate",
                        "config": weaviate_config
                    }
                else:
                    # Handle config object with to_dict method
                    return {
                        "type": "weaviate", 
                        "config": weaviate_config.to_dict() if hasattr(weaviate_config, 'to_dict') else weaviate_config
                    }
            else:
                logger.warning("Weaviate backend selected but no weaviate config found, falling back to FAISS")
                return {
                    "type": "faiss",
                    "config": backends_config.get("faiss", {
                        "index_type": "IndexFlatIP",
                        "normalize_embeddings": True,
                        "metric": "cosine"
                    })
                }
        else:
            # Default to FAISS
            return {
                "type": "faiss",
                "config": backends_config.get("faiss", {
                    "index_type": "IndexFlatIP",
                    "normalize_embeddings": True,
                    "metric": "cosine"
                })
            }
    
    @classmethod
    def _transform_fusion_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """Transform fusion configuration with graph enhancement support."""
        # Get hybrid search configuration
        hybrid_search = config.get("hybrid_search", {})
        
        # Base fusion configuration
        base_fusion_config = {
            "k": hybrid_search.get("rrf_k", 60),
            "weights": {
                "dense": hybrid_search.get("dense_weight", 0.7),
                "sparse": hybrid_search.get("sparse_weight", 0.3),
            },
        }
        
        # Check if graph retrieval is enabled
        graph_retrieval = config.get("graph_retrieval", {})
        if graph_retrieval.get("enabled", False):
            graph_enhanced_config = {
                "base_fusion": base_fusion_config,
                "graph_enhancement": {
                    "enabled": True,
                    "graph_weight": 0.1,
                    "entity_boost": 0.15,
                    "relationship_boost": 0.1,
                    "similarity_threshold": graph_retrieval.get("similarity_threshold", 0.7),
                    "max_graph_hops": graph_retrieval.get("max_graph_hops", 3)
                }
            }
            
            return {
                "type": "graph_enhanced_rrf",
                "config": graph_enhanced_config
            }
        else:
            # Use standard fusion - check for explicit fusion.type first, then fall back to hybrid_search
            explicit_fusion = config.get("fusion", {})
            fusion_type = explicit_fusion.get("type") or hybrid_search.get("fusion_method", "rrf")
            
            # If explicit fusion config exists, use it; otherwise use base config
            fusion_config = explicit_fusion.get("config", base_fusion_config) if explicit_fusion.get("type") else base_fusion_config
            
            return {
                "type": fusion_type,
                "config": fusion_config
            }
    
    @classmethod
    def _transform_reranker_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """Transform reranker configuration with neural reranking support."""
        # Check if neural reranking is enabled (support both old and new format)
        neural_reranking = config.get("neural_reranking", {})
        reranker_config = config.get("reranker", {})
        
        # Check new format first (reranker.type == "neural")
        if reranker_config.get("type") == "neural" and reranker_config.get("config", {}).get("enabled", False):
            neural_config_source = reranker_config.get("config", {})
        # Check old format (neural_reranking.enabled)
        elif neural_reranking.get("enabled", False):
            neural_config_source = neural_reranking
        else:
            neural_config_source = None
            
        if neural_config_source:
            # Convert neural reranking config to proper NeuralReranker format
            neural_config = {
                "enabled": True,
                "max_candidates": neural_config_source.get("max_candidates", 50),
                "default_model": neural_config_source.get("default_model", "default_model"),
                "models": neural_config_source.get("models", {
                    "default_model": {
                        "name": neural_config_source.get("model_name", "cross-encoder/ms-marco-MiniLM-L6-v2"),
                        "max_length": neural_config_source.get("max_length", 512),
                        "batch_size": neural_config_source.get("batch_size", 16),
                        "device": "mps" if neural_config_source.get("device", "auto") == "auto" else neural_config_source.get("device", "auto")
                    }
                }),
                "performance": {
                    "target_latency_ms": 200,
                    "max_latency_ms": neural_config_source.get("max_latency_ms", 1000),
                    "enable_caching": True,
                    "max_cache_size": 10000
                },
                "score_fusion": {
                    "method": "weighted",
                    "weights": {
                        "neural_score": 0.7,
                        "retrieval_score": 0.3,
                        "graph_score": 0.0,
                        "temporal_score": 0.0
                    }
                },
                "adaptive": {
                    "enabled": True,
                    "confidence_threshold": 0.7
                }
            }
            
            logger.info(f"✅ ComponentFactory: Neural reranker config transformed successfully")
            logger.debug(f"Neural reranker config: {neural_config}")
            
            return {
                "type": "neural",
                "config": neural_config
            }
        else:
            # Use identity reranker
            return {
                "type": "identity",
                "config": {"enabled": True}
            }
    
    @classmethod
    def create_generator(cls, generator_type: str, **kwargs) -> AnswerGenerator:
        """
        Create an answer generator instance.
        
        Args:
            generator_type: Type of generator ("adaptive")
            **kwargs: Arguments to pass to the generator constructor
            
        Returns:
            Instantiated AnswerGenerator
            
        Raises:
            ValueError: If generator type is not supported
            TypeError: If constructor arguments are invalid
        """
        if generator_type not in cls._GENERATORS:
            available = list(cls._GENERATORS.keys())
            raise ValueError(
                f"Unknown generator type '{generator_type}'. "
                f"Available generators: {available}"
            )
        
        generator_module_path = cls._GENERATORS[generator_type]
        generator_class = cls._get_component_class(generator_module_path)
        
        try:
            logger.debug(f"Creating {generator_type} generator with args: {kwargs}")
            return cls._create_with_tracking(
                generator_class, 
                f"generator_{generator_type}", 
                **kwargs
            )
        except Exception as e:
            raise TypeError(
                f"Failed to create generator '{generator_type}': {e}. "
                f"Check constructor arguments: {kwargs}"
            ) from e
    
    @classmethod
    def create_answer_generator(cls, generator_type: str = "adaptive", **kwargs) -> AnswerGenerator:
        """
        Alias for create_generator() for backward compatibility.
        
        Args:
            generator_type: Type of generator (default: "adaptive")
            **kwargs: Arguments to pass to the generator constructor
            
        Returns:
            Instantiated AnswerGenerator
        """
        return cls.create_generator(generator_type, **kwargs)
    
    @classmethod
    def create_query_analyzer(cls, analyzer_type: str, **kwargs) -> Any:
        """
        Create a query analyzer instance.

        Args:
            analyzer_type: Type of analyzer ("nlp", "rule_based", "epic1", "epic1_ml")
            **kwargs: Arguments to pass to the analyzer constructor

        Returns:
            Instantiated QueryAnalyzer

        Raises:
            ValueError: If analyzer type is not supported
            TypeError: If constructor arguments are invalid
        """
        if analyzer_type not in cls._QUERY_ANALYZERS:
            available = list(cls._QUERY_ANALYZERS.keys())
            raise ValueError(
                f"Unknown analyzer type '{analyzer_type}'. "
                f"Available analyzers: {available}"
            )
        
        analyzer_module_path = cls._QUERY_ANALYZERS[analyzer_type]
        analyzer_class = cls._get_component_class(analyzer_module_path)
        
        try:
            logger.debug(f"Creating {analyzer_type} analyzer with args: {kwargs}")
            return cls._create_with_tracking(
                analyzer_class, 
                f"analyzer_{analyzer_type}", 
                **kwargs
            )
        except Exception as e:
            raise TypeError(
                f"Failed to create analyzer '{analyzer_type}': {e}. "
                f"Check constructor arguments: {kwargs}"
            ) from e
    
    @classmethod
    def create_query_processor(cls, processor_type: str, **kwargs) -> QueryProcessor:
        """
        Create a query processor instance.
        
        Args:
            processor_type: Type of query processor ("modular")
            **kwargs: Arguments to pass to the processor constructor
            
        Returns:
            Instantiated QueryProcessor
            
        Raises:
            ValueError: If processor type is not supported
            TypeError: If constructor arguments are invalid
        """
        if processor_type not in cls._QUERY_PROCESSORS:
            available = list(cls._QUERY_PROCESSORS.keys())
            raise ValueError(
                f"Unknown query processor type '{processor_type}'. "
                f"Available query processors: {available}"
            )
        
        processor_module_path = cls._QUERY_PROCESSORS[processor_type]
        processor_class = cls._get_component_class(processor_module_path)
        
        try:
            logger.debug(f"Creating {processor_type} query processor with args: {kwargs}")
            
            # Special handling for ModularQueryProcessor
            if processor_type == 'modular' or processor_type == 'modular_query_processor':
                # ModularQueryProcessor needs retriever and generator instances
                from src.components.query_processors.base import QueryProcessorConfig

                # Get or create required dependencies
                retriever = kwargs.pop('retriever', None)
                generator = kwargs.pop('generator', None)

                if retriever is None:
                    # Create a default retriever if not provided
                    # ModularUnifiedRetriever needs an embedder
                    embedder = cls.create_embedder('sentence_transformer')
                    retriever = cls.create_retriever('modular_unified', embedder=embedder)

                if generator is None:
                    # Create a default generator if not provided
                    generator = cls.create_generator('adaptive_modular')

                # Build config from remaining kwargs
                config = QueryProcessorConfig(
                    analyzer_type=kwargs.pop('analyzer_type', 'rule_based'),
                    analyzer_config=kwargs.pop('analyzer_config', {}),
                    selector_type=kwargs.pop('selector_type', 'token_limit'),
                    selector_config=kwargs.pop('selector_config', {}),
                    assembler_type=kwargs.pop('assembler_type', 'standard'),
                    assembler_config=kwargs.pop('assembler_config', {})
                )

                # Remove legacy parameters that don't belong to ModularQueryProcessor
                legacy_params = ['default_k', 'min_confidence', 'enable_performance_monitoring']
                for param in legacy_params:
                    kwargs.pop(param, None)

                # Create processor with correct arguments
                return cls._create_with_tracking(
                    processor_class,
                    f"query_processor_{processor_type}",
                    retriever=retriever,
                    generator=generator,
                    config=config,
                    **kwargs  # Any remaining kwargs
                )
            # Special handling for IntelligentQueryProcessor (Epic 5 Phase 2 Block 3)
            elif processor_type == 'intelligent' or processor_type == 'epic5_intelligent':
                # IntelligentQueryProcessor needs retriever, generator, agent, and query_analyzer
                from src.components.query_processors.agents.models import ProcessorConfig

                # Get required dependencies (must be provided)
                retriever = kwargs.pop('retriever', None)
                generator = kwargs.pop('generator', None)
                agent = kwargs.pop('agent', None)
                query_analyzer = kwargs.pop('query_analyzer', None)

                if retriever is None:
                    raise ValueError("IntelligentQueryProcessor requires 'retriever' parameter")
                if generator is None:
                    raise ValueError("IntelligentQueryProcessor requires 'generator' parameter")
                if agent is None:
                    raise ValueError("IntelligentQueryProcessor requires 'agent' parameter (ReActAgent)")
                if query_analyzer is None:
                    raise ValueError("IntelligentQueryProcessor requires 'query_analyzer' parameter (QueryAnalyzer)")

                # Build config from remaining kwargs or use provided config
                config = kwargs.pop('config', None)
                if config is None:
                    config = ProcessorConfig(
                        use_agent_by_default=kwargs.pop('use_agent_by_default', False),
                        complexity_threshold=kwargs.pop('complexity_threshold', 0.7),
                        max_agent_cost=kwargs.pop('max_agent_cost', 0.10),
                        enable_planning=kwargs.pop('enable_planning', False),
                        enable_parallel_execution=kwargs.pop('enable_parallel_execution', False)
                    )

                # Create processor with correct arguments
                return cls._create_with_tracking(
                    processor_class,
                    f"query_processor_{processor_type}",
                    retriever=retriever,
                    generator=generator,
                    agent=agent,
                    query_analyzer=query_analyzer,
                    config=config
                )
            else:
                # Default handling for other processor types
                return cls._create_with_tracking(
                    processor_class,
                    f"query_processor_{processor_type}",
                    **kwargs
                )
        except Exception as e:
            raise TypeError(
                f"Failed to create query processor '{processor_type}': {e}. "
                f"Check constructor arguments: {kwargs}"
            ) from e
    
    @classmethod
    def create_tool(cls, tool_type: str, **kwargs) -> Any:
        """
        Create a tool instance (Epic 5).

        Args:
            tool_type: Type of tool ("calculator", "code_analyzer", "document_search")
            **kwargs: Arguments to pass to the tool constructor

        Returns:
            Instantiated Tool

        Raises:
            ValueError: If tool type is not supported
            TypeError: If constructor arguments are invalid
        """
        if tool_type not in cls._TOOLS:
            available = list(cls._TOOLS.keys())
            raise ValueError(
                f"Unknown tool type '{tool_type}'. "
                f"Available tools: {available}"
            )

        tool_module_path = cls._TOOLS[tool_type]
        tool_class = cls._get_component_class(tool_module_path)

        try:
            return cls._create_with_tracking(
                tool_class,
                f"tool_{tool_type}",
                **kwargs
            )
        except Exception as e:
            raise TypeError(
                f"Failed to create tool '{tool_type}': {e}. "
                f"Check constructor arguments: {kwargs}"
            ) from e

    @classmethod
    def create_memory(cls, memory_type: str, **kwargs) -> Any:
        """
        Create a memory instance (Epic 5).

        Args:
            memory_type: Type of memory ("conversation", "working")
            **kwargs: Arguments to pass to the memory constructor

        Returns:
            Instantiated Memory

        Raises:
            ValueError: If memory type is not supported
            TypeError: If constructor arguments are invalid
        """
        if memory_type not in cls._MEMORY:
            available = list(cls._MEMORY.keys())
            raise ValueError(
                f"Unknown memory type '{memory_type}'. "
                f"Available memory types: {available}"
            )

        memory_module_path = cls._MEMORY[memory_type]
        memory_class = cls._get_component_class(memory_module_path)

        try:
            return cls._create_with_tracking(
                memory_class,
                f"memory_{memory_type}",
                **kwargs
            )
        except Exception as e:
            raise TypeError(
                f"Failed to create memory '{memory_type}': {e}. "
                f"Check constructor arguments: {kwargs}"
            ) from e

    @classmethod
    def create_tool_registry(cls, **kwargs) -> Any:
        """
        Create a ToolRegistry instance (Epic 5).

        Args:
            **kwargs: Arguments to pass to the ToolRegistry constructor

        Returns:
            Instantiated ToolRegistry

        Raises:
            TypeError: If constructor arguments are invalid
        """
        registry_class = cls._get_component_class(cls._TOOL_REGISTRY)

        try:
            return cls._create_with_tracking(
                registry_class,
                "tool_registry",
                **kwargs
            )
        except Exception as e:
            raise TypeError(
                f"Failed to create ToolRegistry: {e}. "
                f"Check constructor arguments: {kwargs}"
            ) from e

    @classmethod
    def is_supported(cls, component_type: str, name: str) -> bool:
        """
        Check if a component type and name are supported.

        Args:
            component_type: Type of component ('processor', 'embedder', 'vector_store',
                           'retriever', 'generator', 'tool', 'memory')
            name: Component name to check

        Returns:
            True if component is supported, False otherwise
        """
        type_mappings = {
            'processor': cls._PROCESSORS,
            'embedder': cls._EMBEDDERS,
            'vector_store': cls._VECTOR_STORES,
            'retriever': cls._RETRIEVERS,
            'generator': cls._GENERATORS,
            'query_processor': cls._QUERY_PROCESSORS,
            'query_analyzer': cls._QUERY_ANALYZERS,
            'tool': cls._TOOLS,
            'memory': cls._MEMORY
        }

        mapping = type_mappings.get(component_type)
        if mapping is None:
            return False

        return name in mapping
    
    @classmethod
    def get_all_supported_components(cls) -> Dict[str, list[str]]:
        """Get all supported components organized by type (alias for get_available_components)."""
        return cls.get_available_components()
    
    @classmethod
    def get_available_components(cls) -> Dict[str, list[str]]:
        """
        Get all available components organized by type.

        Returns:
            Dictionary mapping component types to lists of available component names
        """
        return {
            "processors": list(cls._PROCESSORS.keys()),
            "embedders": list(cls._EMBEDDERS.keys()),
            "vector_stores": list(cls._VECTOR_STORES.keys()),
            "retrievers": list(cls._RETRIEVERS.keys()),
            "generators": list(cls._GENERATORS.keys()),
            "query_processors": list(cls._QUERY_PROCESSORS.keys()),
            "query_analyzers": list(cls._QUERY_ANALYZERS.keys()),
            "tools": list(cls._TOOLS.keys()),
            "memory": list(cls._MEMORY.keys()),
        }
    
    @classmethod
    def validate_configuration(cls, config: Dict[str, Any]) -> list[str]:
        """
        Validate component configuration.
        
        Args:
            config: Configuration dictionary with component specifications
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Component type mappings for validation
        required_components = {
            'document_processor': 'processors',
            'embedder': 'embedders',
            'retriever': 'retrievers',
            'answer_generator': 'generators'
        }
        
        # vector_store is optional in unified architecture
        optional_components = {
            'vector_store': 'vector_stores'
        }
        
        all_components = {**required_components, **optional_components}
        available = cls.get_available_components()
        
        # Check required components
        for comp_key, comp_type_key in required_components.items():
            if comp_key not in config:
                errors.append(f"Missing required component: {comp_key}")
                continue
            
            comp_config = config[comp_key]
            if not isinstance(comp_config, dict) or 'type' not in comp_config:
                errors.append(f"Invalid configuration for {comp_key}: missing 'type' field")
                continue
            
            comp_type = comp_config['type']
            if comp_type not in available[comp_type_key]:
                errors.append(
                    f"Unknown {comp_key} type '{comp_type}'. "
                    f"Available: {available[comp_type_key]}"
                )
        
        # Check optional components if present
        for comp_key, comp_type_key in optional_components.items():
            if comp_key in config:
                comp_config = config[comp_key]
                if not isinstance(comp_config, dict) or 'type' not in comp_config:
                    errors.append(f"Invalid configuration for {comp_key}: missing 'type' field")
                    continue
                
                comp_type = comp_config['type']
                if comp_type not in available[comp_type_key]:
                    errors.append(
                        f"Unknown {comp_key} type '{comp_type}'. "
                        f"Available: {available[comp_type_key]}"
                    )
        
        return errors