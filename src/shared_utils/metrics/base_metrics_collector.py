"""
Base abstract class for metrics collectors.

Provides common interface and shared functionality for different metrics
collector implementations across the RAG system.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Protocol, Union
from abc import ABC, abstractmethod
from pathlib import Path

from .data_models import (
    BaseQueryMetrics,
    SystemMetrics,
    SessionMetadata,
    ComponentMetrics
)

logger = logging.getLogger(__name__)


class MetricsStorage(Protocol):
    """Protocol for metrics storage backends."""
    
    def store_query_metrics(self, metrics: BaseQueryMetrics) -> None:
        """Store query metrics."""
        ...
    
    def store_system_metrics(self, metrics: SystemMetrics) -> None:
        """Store system metrics."""
        ...
    
    def get_query_metrics(self, limit: Optional[int] = None) -> List[BaseQueryMetrics]:
        """Retrieve query metrics."""
        ...


class BaseMetricsCollector(ABC):
    """
    Abstract base class for metrics collectors.
    
    Provides common interface and shared functionality for different metrics
    collection strategies across the RAG system.
    """
    
    def __init__(self, 
                 session_metadata: Optional[SessionMetadata] = None,
                 storage: Optional[MetricsStorage] = None):
        """
        Initialize base metrics collector.
        
        Args:
            session_metadata: Optional session metadata
            storage: Optional storage backend for persistence
        """
        self.session_metadata = session_metadata or SessionMetadata()
        self.storage = storage
        self._component_metrics: Dict[str, ComponentMetrics] = {}
        
    @abstractmethod
    def start_query_collection(self, query_id: str, query_text: str) -> BaseQueryMetrics:
        """
        Start collecting metrics for a query.
        
        Args:
            query_id: Unique identifier for the query
            query_text: The query text
            
        Returns:
            Query metrics object to populate
        """
        pass
    
    @abstractmethod
    def collect_performance_metrics(self, 
                                  query_metrics: BaseQueryMetrics,
                                  total_time: float,
                                  **kwargs) -> None:
        """
        Collect performance metrics for a query.
        
        Args:
            query_metrics: Query metrics object to update
            total_time: Total processing time
            **kwargs: Additional performance metrics
        """
        pass
    
    @abstractmethod
    def calculate_aggregate_metrics(self) -> Dict[str, Any]:
        """
        Calculate aggregate metrics across all collected data.
        
        Returns:
            Dictionary containing aggregate metrics
        """
        pass
    
    def record_component_usage(self, 
                              component_name: str, 
                              latency_ms: float, 
                              success: bool = True) -> None:
        """
        Record component usage metrics.
        
        Args:
            component_name: Name of the component
            latency_ms: Processing latency in milliseconds
            success: Whether the operation was successful
        """
        if component_name not in self._component_metrics:
            self._component_metrics[component_name] = ComponentMetrics(component_name)
        
        self._component_metrics[component_name].record_usage(latency_ms, success)
        logger.debug(f"Recorded usage for component {component_name}: {latency_ms:.2f}ms, success={success}")
    
    def get_component_metrics(self) -> Dict[str, ComponentMetrics]:
        """Get all component metrics."""
        return self._component_metrics.copy()
    
    def update_session_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Update session metadata.
        
        Args:
            metadata: Metadata to update
        """
        self.session_metadata.update(metadata)
    
    def export_metrics(self, output_path: Path, include_raw_data: bool = True) -> None:
        """
        Export collected metrics to JSON file.
        
        Args:
            output_path: Path to export file
            include_raw_data: Whether to include raw query data
        """
        try:
            export_data = {
                "session_metadata": self._serialize_session_metadata(),
                "aggregate_metrics": self.calculate_aggregate_metrics(),
                "component_metrics": self._serialize_component_metrics()
            }
            
            if include_raw_data:
                export_data["raw_data"] = self._serialize_raw_data()
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=self._json_serializer)
            
            logger.info(f"Exported metrics to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            raise
    
    def _serialize_session_metadata(self) -> Dict[str, Any]:
        """Serialize session metadata for export."""
        return {
            "session_id": self.session_metadata.session_id,
            "start_time": self.session_metadata.start_time,
            "parameter_config": self.session_metadata.parameter_config,
            "system_config": self.session_metadata.system_config
        }
    
    def _serialize_component_metrics(self) -> Dict[str, Any]:
        """Serialize component metrics for export."""
        return {
            name: {
                "total_calls": metrics.total_calls,
                "avg_latency_ms": metrics.avg_latency,
                "error_rate": metrics.error_rate,
                "status": metrics.status,
                "last_used": metrics.last_used
            }
            for name, metrics in self._component_metrics.items()
        }
    
    @abstractmethod
    def _serialize_raw_data(self) -> List[Dict[str, Any]]:
        """Serialize raw metrics data for export."""
        pass
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for complex objects."""
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return str(obj)
    
    @abstractmethod
    def get_metrics_summary(self) -> str:
        """
        Get human-readable summary of collected metrics.
        
        Returns:
            Human-readable metrics summary
        """
        pass


class InMemoryMetricsStorage:
    """Simple in-memory storage for metrics."""
    
    def __init__(self, max_query_metrics: int = 10000):
        """Initialize storage with maximum capacity."""
        self.max_query_metrics = max_query_metrics
        self.query_metrics: List[BaseQueryMetrics] = []
        self.system_metrics: List[SystemMetrics] = []
    
    def store_query_metrics(self, metrics: BaseQueryMetrics) -> None:
        """Store query metrics with capacity management."""
        self.query_metrics.append(metrics)
        if len(self.query_metrics) > self.max_query_metrics:
            self.query_metrics.pop(0)  # Remove oldest
    
    def store_system_metrics(self, metrics: SystemMetrics) -> None:
        """Store system metrics."""
        self.system_metrics.append(metrics)
        # Keep last 24 hours assuming 1-minute intervals
        if len(self.system_metrics) > 1440:
            self.system_metrics.pop(0)
    
    def get_query_metrics(self, limit: Optional[int] = None) -> List[BaseQueryMetrics]:
        """Retrieve query metrics with optional limit."""
        if limit is None:
            return self.query_metrics.copy()
        return self.query_metrics[-limit:]
    
    def get_system_metrics(self, limit: Optional[int] = None) -> List[SystemMetrics]:
        """Retrieve system metrics with optional limit."""
        if limit is None:
            return self.system_metrics.copy()
        return self.system_metrics[-limit:]