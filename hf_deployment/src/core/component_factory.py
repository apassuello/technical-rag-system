"""
Component Factory for Epic 2 HF Deployment.

This module provides a lightweight factory for Epic 2 component instantiation,
designed specifically for the HF deployment package with self-contained components.
"""

import logging
import time
import hashlib
from typing import Dict, Type, Any, Optional, Union
from pathlib import Path
from collections import defaultdict, OrderedDict

from .interfaces import Retriever, HealthStatus

logger = logging.getLogger(__name__)


class ComponentFactory:
    """
    Lightweight factory for Epic 2 component instantiation.
    
    This factory creates Epic 2 enhanced components for HF deployment,
    maintaining architectural consistency with the main project while
    being completely self-contained.
    
    Features:
    - Direct component class mapping (no registry lookup)
    - Epic 2 advanced retrievers with neural reranking and graph enhancement
    - Type-safe instantiation with validation
    - Performance optimized for HF Spaces deployment
    
    Example:
        factory = ComponentFactory()
        
        # Create Epic 2 advanced retriever
        retriever = factory.create_retriever("epic2_advanced", config=retrieval_config)
    """
    
    # Component type mappings - Epic 2 components only
    _RETRIEVERS: Dict[str, str] = {
        "epic2_advanced": "src.components.advanced_retriever.AdvancedRetriever",
        "advanced": "src.components.advanced_retriever.AdvancedRetriever",  # Alias
    }
    
    # Performance monitoring and caching
    _performance_metrics: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "creation_count": 0,
        "total_time": 0.0,
        "average_time": 0.0,
        "min_time": float('inf'),
        "max_time": 0.0,
        "last_created": None
    })
    
    _component_cache: Dict[str, Any] = OrderedDict()
    _cache_max_size: int = 50  # Conservative for HF Spaces
    
    def __init__(self):
        """Initialize the ComponentFactory."""
        self._initialized = True
        logger.info("🏭 Epic 2 ComponentFactory initialized")
    
    def create_retriever(self, retriever_type: str, **kwargs) -> Retriever:
        """
        Create a retriever component.
        
        Args:
            retriever_type: Type of retriever ('epic2_advanced', 'advanced')
            **kwargs: Configuration parameters for the retriever
            
        Returns:
            Configured retriever instance
            
        Raises:
            ValueError: If retriever_type is not supported
            TypeError: If configuration is invalid
        """
        start_time = time.time()
        
        try:
            # Validate retriever type
            if retriever_type not in self._RETRIEVERS:
                available_types = list(self._RETRIEVERS.keys())
                raise ValueError(f"Unsupported retriever type '{retriever_type}'. Available: {available_types}")
            
            # Generate cache key for component caching
            config_hash = self._hash_config(kwargs)
            cache_key = f"retriever_{retriever_type}_{config_hash}"
            
            # Check cache first
            if cache_key in self._component_cache:
                logger.debug(f"🎯 Using cached retriever: {retriever_type}")
                return self._component_cache[cache_key]
            
            # Load component class
            component_class = self._get_component_class(self._RETRIEVERS[retriever_type])
            
            # Create component instance
            if retriever_type in ["epic2_advanced", "advanced"]:
                # Epic 2 advanced retriever expects config dict
                config = kwargs.get('config', kwargs)
                component = component_class(config)
            else:
                component = component_class(**kwargs)
            
            # Cache the component (with size limit)
            self._cache_component(cache_key, component)
            
            # Record performance metrics
            creation_time = time.time() - start_time
            self._record_performance_metric(f"retriever_{retriever_type}", creation_time)
            
            # Enhanced logging with sub-component information
            sub_components = self._get_sub_component_info(component)
            if sub_components:
                logger.info(f"🏭 ComponentFactory created: {component.__class__.__name__} "
                          f"(type={retriever_type}, module={component.__class__.__module__}, time={creation_time:.3f}s)")
                logger.info(f"  └─ Sub-components: {sub_components}")
            else:
                logger.info(f"🏭 ComponentFactory created: {component.__class__.__name__} "
                          f"(type={retriever_type}, module={component.__class__.__module__}, time={creation_time:.3f}s)")
            
            return component
            
        except Exception as e:
            logger.error(f"❌ Failed to create retriever '{retriever_type}': {e}")
            raise
    
    def _get_component_class(self, module_path: str) -> Type:
        """Dynamically import and return component class."""
        try:
            # Handle relative imports within hf_deployment
            if module_path.startswith("src."):
                module_path = module_path[4:]  # Remove 'src.' prefix
            
            parts = module_path.split('.')
            module_name = '.'.join(parts[:-1])
            class_name = parts[-1]
            
            # Import from current package
            import importlib
            if module_name.startswith("components."):
                # Import from components directory
                from ..components import advanced_retriever
                if class_name == "AdvancedRetriever":
                    return advanced_retriever.AdvancedRetriever
            
            raise ImportError(f"Unknown component class: {class_name}")
            
        except ImportError as e:
            logger.error(f"Failed to import component class '{module_path}': {e}")
            raise
    
    def _hash_config(self, config: Dict[str, Any]) -> str:
        """Generate hash for configuration caching."""
        try:
            config_str = str(sorted(config.items()))
            return hashlib.md5(config_str.encode()).hexdigest()[:8]
        except Exception:
            return "no_cache"
    
    def _cache_component(self, cache_key: str, component: Any) -> None:
        """Cache component with LRU eviction."""
        if len(self._component_cache) >= self._cache_max_size:
            # Remove oldest item
            self._component_cache.popitem(last=False)
        
        self._component_cache[cache_key] = component
        self._component_cache.move_to_end(cache_key)
    
    def _record_performance_metric(self, component_key: str, creation_time: float) -> None:
        """Record performance metrics for component creation."""
        metrics = self._performance_metrics[component_key]
        metrics["creation_count"] += 1
        metrics["total_time"] += creation_time
        metrics["average_time"] = metrics["total_time"] / metrics["creation_count"]
        metrics["min_time"] = min(metrics["min_time"], creation_time)
        metrics["max_time"] = max(metrics["max_time"], creation_time)
        metrics["last_created"] = time.time()
    
    def _get_sub_component_info(self, component: Any) -> str:
        """Extract sub-component information for enhanced logging."""
        try:
            # For Epic 2 AdvancedRetriever, show neural reranker and graph components
            if hasattr(component, 'neural_reranker') and hasattr(component, 'graph_retriever'):
                sub_info = []
                
                if component.neural_reranker:
                    reranker_type = component.neural_reranker.__class__.__name__
                    sub_info.append(f"neural_reranker:{reranker_type}")
                
                if component.graph_retriever:
                    graph_type = component.graph_retriever.__class__.__name__
                    sub_info.append(f"graph_retriever:{graph_type}")
                
                if hasattr(component, 'bm25_retriever') and component.bm25_retriever:
                    sub_info.append("bm25_retriever:BM25Retriever")
                
                return ", ".join(sub_info)
            
            return ""
        except Exception:
            return ""
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all components."""
        return dict(self._performance_metrics)
    
    def clear_cache(self) -> None:
        """Clear component cache."""
        self._component_cache.clear()
        logger.info("🧹 Component cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self._component_cache),
            "max_size": self._cache_max_size,
            "hit_ratio": getattr(self, '_cache_hits', 0) / max(getattr(self, '_cache_attempts', 1), 1)
        }


# Global factory instance for Epic 2 HF deployment
epic2_factory = ComponentFactory()