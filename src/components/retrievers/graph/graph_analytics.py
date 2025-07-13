"""
Graph analytics for Epic 2 Week 2.

This module provides analytics capabilities for knowledge graphs including
metrics collection, performance monitoring, and optional visualization
of graph structures and retrieval patterns.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import json

try:
    import networkx as nx
    import numpy as np
except ImportError:
    nx = None
    np = None

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from .config.graph_config import GraphAnalyticsConfig
from .document_graph_builder import DocumentGraphBuilder
from .graph_retriever import GraphRetriever

logger = logging.getLogger(__name__)


@dataclass
class GraphMetrics:
    """Graph structure metrics."""
    nodes: int = 0
    edges: int = 0
    density: float = 0.0
    avg_degree: float = 0.0
    connected_components: int = 0
    diameter: Optional[int] = None
    clustering_coefficient: float = 0.0
    node_type_distribution: Dict[str, int] = field(default_factory=dict)
    edge_type_distribution: Dict[str, int] = field(default_factory=dict)


@dataclass
class RetrievalMetrics:
    """Graph retrieval performance metrics."""
    total_queries: int = 0
    avg_latency_ms: float = 0.0
    cache_hit_rate: float = 0.0
    algorithm_usage: Dict[str, int] = field(default_factory=dict)
    avg_results_per_query: float = 0.0
    query_patterns: Dict[str, int] = field(default_factory=dict)


@dataclass
class AnalyticsSnapshot:
    """Complete analytics snapshot."""
    timestamp: float
    graph_metrics: GraphMetrics
    retrieval_metrics: RetrievalMetrics
    memory_usage_mb: float = 0.0
    processing_stats: Dict[str, Any] = field(default_factory=dict)


class GraphAnalyticsError(Exception):
    """Raised when graph analytics operations fail."""
    pass


class GraphAnalytics:
    """
    Analytics and monitoring for graph-based retrieval.
    
    This class provides comprehensive analytics capabilities including:
    - Graph structure analysis and metrics
    - Retrieval performance monitoring
    - Query pattern analysis
    - Optional visualization of graphs and metrics
    - Time-series tracking of performance
    
    Features:
    - Real-time metrics collection
    - Historical performance tracking
    - Graph visualization (when Plotly is available)
    - Performance trend analysis
    - Memory usage monitoring
    """
    
    def __init__(self, config: GraphAnalyticsConfig):
        """
        Initialize graph analytics.
        
        Args:
            config: Analytics configuration
        """
        self.config = config
        
        # Metrics storage
        self.snapshots: List[AnalyticsSnapshot] = []
        self.current_metrics = {
            "graph": GraphMetrics(),
            "retrieval": RetrievalMetrics()
        }
        
        # Query tracking
        self.query_history: List[Dict[str, Any]] = []
        self.performance_history: List[Dict[str, Any]] = []
        
        # Statistics
        self.stats = {
            "analytics_started": time.time(),
            "snapshots_created": 0,
            "metrics_collected": 0,
            "visualizations_generated": 0
        }
        
        logger.info(f"GraphAnalytics initialized (visualization: {PLOTLY_AVAILABLE})")
    
    def collect_graph_metrics(self, graph_builder: DocumentGraphBuilder) -> GraphMetrics:
        """
        Collect comprehensive graph structure metrics.
        
        Args:
            graph_builder: Document graph builder
            
        Returns:
            Graph metrics object
        """
        if not self.config.collect_graph_metrics:
            return GraphMetrics()
        
        try:
            graph = graph_builder.get_graph()
            
            if not graph or graph.number_of_nodes() == 0:
                return GraphMetrics()
            
            # Basic metrics
            num_nodes = graph.number_of_nodes()
            num_edges = graph.number_of_edges()
            
            metrics = GraphMetrics(
                nodes=num_nodes,
                edges=num_edges
            )
            
            # Calculate density
            if num_nodes > 1:
                metrics.density = nx.density(graph)
            
            # Calculate average degree
            if num_nodes > 0:
                degrees = dict(graph.degree())
                metrics.avg_degree = sum(degrees.values()) / num_nodes
            
            # Connected components
            if graph.is_directed():
                metrics.connected_components = nx.number_weakly_connected_components(graph)
            else:
                metrics.connected_components = nx.number_connected_components(graph)
            
            # Diameter (for smaller graphs)
            if num_nodes < 1000 and nx.is_connected(graph.to_undirected()):
                try:
                    metrics.diameter = nx.diameter(graph.to_undirected())
                except nx.NetworkXError:
                    metrics.diameter = None
            
            # Clustering coefficient
            if num_nodes > 2:
                try:
                    metrics.clustering_coefficient = nx.average_clustering(graph.to_undirected())
                except (nx.NetworkXError, ZeroDivisionError):
                    metrics.clustering_coefficient = 0.0
            
            # Node type distribution
            node_types = defaultdict(int)
            for node_id in graph.nodes():
                node_data = graph.nodes[node_id]
                node_type = node_data.get("node_type", "unknown")
                node_types[node_type] += 1
            metrics.node_type_distribution = dict(node_types)
            
            # Edge type distribution
            edge_types = defaultdict(int)
            for source, target, edge_data in graph.edges(data=True):
                edge_type = edge_data.get("edge_type", "unknown")
                edge_types[edge_type] += 1
            metrics.edge_type_distribution = dict(edge_types)
            
            self.current_metrics["graph"] = metrics
            self.stats["metrics_collected"] += 1
            
            logger.debug(f"Collected graph metrics: {num_nodes} nodes, {num_edges} edges")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect graph metrics: {str(e)}")
            return GraphMetrics()
    
    def collect_retrieval_metrics(self, graph_retriever: GraphRetriever) -> RetrievalMetrics:
        """
        Collect retrieval performance metrics.
        
        Args:
            graph_retriever: Graph retriever component
            
        Returns:
            Retrieval metrics object
        """
        if not self.config.collect_retrieval_metrics:
            return RetrievalMetrics()
        
        try:
            retriever_stats = graph_retriever.get_statistics()
            
            metrics = RetrievalMetrics(
                total_queries=retriever_stats.get("queries_processed", 0),
                avg_latency_ms=retriever_stats.get("avg_search_time", 0.0) * 1000,
                cache_hit_rate=retriever_stats.get("cache_hit_rate", 0.0),
                algorithm_usage=dict(retriever_stats.get("algorithm_usage", {})),
                avg_results_per_query=(
                    retriever_stats.get("total_results_returned", 0) / 
                    max(retriever_stats.get("queries_processed", 1), 1)
                )
            )
            
            self.current_metrics["retrieval"] = metrics
            self.stats["metrics_collected"] += 1
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect retrieval metrics: {str(e)}")
            return RetrievalMetrics()
    
    def create_snapshot(self, graph_builder: DocumentGraphBuilder, 
                       graph_retriever: GraphRetriever) -> AnalyticsSnapshot:
        """
        Create a complete analytics snapshot.
        
        Args:
            graph_builder: Document graph builder
            graph_retriever: Graph retriever component
            
        Returns:
            Analytics snapshot
        """
        timestamp = time.time()
        
        # Collect metrics
        graph_metrics = self.collect_graph_metrics(graph_builder)
        retrieval_metrics = self.collect_retrieval_metrics(graph_retriever)
        
        # Get memory usage
        memory_usage = self._estimate_memory_usage(graph_builder, graph_retriever)
        
        # Get processing stats
        processing_stats = {
            "graph_builder": graph_builder.get_graph_statistics(),
            "graph_retriever": graph_retriever.get_statistics()
        }
        
        snapshot = AnalyticsSnapshot(
            timestamp=timestamp,
            graph_metrics=graph_metrics,
            retrieval_metrics=retrieval_metrics,
            memory_usage_mb=memory_usage,
            processing_stats=processing_stats
        )
        
        # Store snapshot
        self.snapshots.append(snapshot)
        self.stats["snapshots_created"] += 1
        
        # Clean old snapshots based on retention policy
        self._clean_old_snapshots()
        
        logger.info(f"Created analytics snapshot ({len(self.snapshots)} total)")
        
        return snapshot
    
    def track_query(self, query: str, results_count: int, latency_ms: float, 
                   algorithm_used: str, success: bool = True) -> None:
        """
        Track an individual query for analysis.
        
        Args:
            query: Query string
            results_count: Number of results returned
            latency_ms: Query latency in milliseconds
            algorithm_used: Algorithm used for retrieval
            success: Whether query was successful
        """
        query_record = {
            "timestamp": time.time(),
            "query": query,
            "results_count": results_count,
            "latency_ms": latency_ms,
            "algorithm": algorithm_used,
            "success": success,
            "query_length": len(query),
            "query_words": len(query.split())
        }
        
        self.query_history.append(query_record)
        
        # Update query patterns
        if hasattr(self.current_metrics["retrieval"], "query_patterns"):
            query_type = self._classify_query(query)
            self.current_metrics["retrieval"].query_patterns[query_type] = (
                self.current_metrics["retrieval"].query_patterns.get(query_type, 0) + 1
            )
        
        # Limit history size
        max_history = 10000
        if len(self.query_history) > max_history:
            self.query_history = self.query_history[-max_history//2:]
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive analytics report.
        
        Returns:
            Dictionary with analytics report
        """
        if not self.snapshots:
            return {"error": "No analytics data available"}
        
        latest_snapshot = self.snapshots[-1]
        
        # Basic metrics
        report = {
            "timestamp": latest_snapshot.timestamp,
            "graph_metrics": {
                "nodes": latest_snapshot.graph_metrics.nodes,
                "edges": latest_snapshot.graph_metrics.edges,
                "density": latest_snapshot.graph_metrics.density,
                "avg_degree": latest_snapshot.graph_metrics.avg_degree,
                "connected_components": latest_snapshot.graph_metrics.connected_components,
                "clustering_coefficient": latest_snapshot.graph_metrics.clustering_coefficient,
                "node_type_distribution": latest_snapshot.graph_metrics.node_type_distribution,
                "edge_type_distribution": latest_snapshot.graph_metrics.edge_type_distribution
            },
            "retrieval_metrics": {
                "total_queries": latest_snapshot.retrieval_metrics.total_queries,
                "avg_latency_ms": latest_snapshot.retrieval_metrics.avg_latency_ms,
                "cache_hit_rate": latest_snapshot.retrieval_metrics.cache_hit_rate,
                "algorithm_usage": latest_snapshot.retrieval_metrics.algorithm_usage,
                "avg_results_per_query": latest_snapshot.retrieval_metrics.avg_results_per_query
            },
            "performance": {
                "memory_usage_mb": latest_snapshot.memory_usage_mb,
                "snapshots_count": len(self.snapshots),
                "queries_tracked": len(self.query_history)
            }
        }
        
        # Historical trends
        if len(self.snapshots) > 1:
            report["trends"] = self._calculate_trends()
        
        # Query analysis
        if self.query_history:
            report["query_analysis"] = self._analyze_queries()
        
        return report
    
    def visualize_graph(self, graph_builder: DocumentGraphBuilder, 
                       layout: str = "spring", max_nodes: Optional[int] = None) -> Optional[str]:
        """
        Generate graph visualization.
        
        Args:
            graph_builder: Document graph builder
            layout: Layout algorithm (spring, circular, etc.)
            max_nodes: Maximum nodes to visualize
            
        Returns:
            HTML string of visualization or None if disabled/failed
        """
        if not self.config.enable_visualization or not PLOTLY_AVAILABLE:
            return None
        
        try:
            graph = graph_builder.get_graph()
            
            if not graph or graph.number_of_nodes() == 0:
                return None
            
            # Limit graph size for visualization
            max_viz_nodes = max_nodes or self.config.visualization_max_nodes
            if graph.number_of_nodes() > max_viz_nodes:
                # Sample most connected nodes
                node_degrees = dict(graph.degree())
                top_nodes = sorted(node_degrees.items(), key=lambda x: x[1], reverse=True)
                nodes_to_keep = [node for node, _ in top_nodes[:max_viz_nodes]]
                graph = graph.subgraph(nodes_to_keep)
            
            # Convert to undirected for layout
            layout_graph = graph.to_undirected()
            
            # Generate layout
            if layout == "spring":
                pos = nx.spring_layout(layout_graph)
            elif layout == "circular":
                pos = nx.circular_layout(layout_graph)
            elif layout == "kamada_kawai":
                pos = nx.kamada_kawai_layout(layout_graph)
            else:
                pos = nx.spring_layout(layout_graph)
            
            # Create visualization
            fig = self._create_plotly_graph(graph, pos)
            
            self.stats["visualizations_generated"] += 1
            
            return fig.to_html()
            
        except Exception as e:
            logger.error(f"Graph visualization failed: {str(e)}")
            return None
    
    def visualize_metrics(self) -> Optional[str]:
        """
        Generate metrics visualization.
        
        Returns:
            HTML string of metrics visualization or None if disabled/failed
        """
        if not self.config.enable_visualization or not PLOTLY_AVAILABLE or not self.snapshots:
            return None
        
        try:
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=("Graph Growth", "Retrieval Latency", "Node Types", "Algorithm Usage"),
                specs=[[{"secondary_y": True}, {"secondary_y": False}],
                       [{"type": "pie"}, {"type": "pie"}]]
            )
            
            # Extract time series data
            timestamps = [s.timestamp for s in self.snapshots]
            nodes = [s.graph_metrics.nodes for s in self.snapshots]
            edges = [s.graph_metrics.edges for s in self.snapshots]
            latencies = [s.retrieval_metrics.avg_latency_ms for s in self.snapshots]
            
            # Graph growth
            fig.add_trace(
                go.Scatter(x=timestamps, y=nodes, name="Nodes", line=dict(color="blue")),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=timestamps, y=edges, name="Edges", line=dict(color="red")),
                row=1, col=1, secondary_y=True
            )
            
            # Retrieval latency
            fig.add_trace(
                go.Scatter(x=timestamps, y=latencies, name="Latency (ms)", line=dict(color="green")),
                row=1, col=2
            )
            
            # Latest snapshot data for pie charts
            latest = self.snapshots[-1]
            
            # Node types pie chart
            if latest.graph_metrics.node_type_distribution:
                fig.add_trace(
                    go.Pie(
                        labels=list(latest.graph_metrics.node_type_distribution.keys()),
                        values=list(latest.graph_metrics.node_type_distribution.values()),
                        name="Node Types"
                    ),
                    row=2, col=1
                )
            
            # Algorithm usage pie chart
            if latest.retrieval_metrics.algorithm_usage:
                fig.add_trace(
                    go.Pie(
                        labels=list(latest.retrieval_metrics.algorithm_usage.keys()),
                        values=list(latest.retrieval_metrics.algorithm_usage.values()),
                        name="Algorithm Usage"
                    ),
                    row=2, col=2
                )
            
            fig.update_layout(
                title="Graph Analytics Dashboard",
                height=800
            )
            
            self.stats["visualizations_generated"] += 1
            
            return fig.to_html()
            
        except Exception as e:
            logger.error(f"Metrics visualization failed: {str(e)}")
            return None
    
    def _estimate_memory_usage(self, graph_builder: DocumentGraphBuilder, 
                              graph_retriever: GraphRetriever) -> float:
        """Estimate memory usage in MB."""
        try:
            # Get graph builder stats
            builder_stats = graph_builder.get_graph_statistics()
            builder_memory = builder_stats.get("memory_usage_mb", 0.0)
            
            # Estimate retriever memory (cache size)
            retriever_stats = graph_retriever.get_statistics()
            cache_entries = len(graph_retriever.query_cache) if hasattr(graph_retriever, 'query_cache') else 0
            retriever_memory = cache_entries * 0.01  # Rough estimate: 10KB per cache entry
            
            # Analytics memory
            analytics_memory = len(self.snapshots) * 0.001  # Rough estimate: 1KB per snapshot
            
            return builder_memory + retriever_memory + analytics_memory
            
        except Exception:
            return 0.0
    
    def _clean_old_snapshots(self) -> None:
        """Clean old snapshots based on retention policy."""
        if not self.snapshots:
            return
        
        current_time = time.time()
        retention_seconds = self.config.metrics_retention_hours * 3600
        
        # Remove snapshots older than retention period
        self.snapshots = [
            s for s in self.snapshots 
            if current_time - s.timestamp <= retention_seconds
        ]
    
    def _classify_query(self, query: str) -> str:
        """Classify query type for pattern analysis."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["risc-v", "riscv", "isa"]):
            return "architecture"
        elif any(word in query_lower for word in ["extension", "implement", "support"]):
            return "extension"
        elif any(word in query_lower for word in ["protocol", "interface", "communication"]):
            return "protocol"
        elif len(query.split()) <= 2:
            return "short"
        elif len(query.split()) > 10:
            return "long"
        else:
            return "general"
    
    def _calculate_trends(self) -> Dict[str, Any]:
        """Calculate performance trends from historical data."""
        if len(self.snapshots) < 2:
            return {}
        
        # Calculate growth rates
        first = self.snapshots[0]
        last = self.snapshots[-1]
        time_diff = last.timestamp - first.timestamp
        
        if time_diff == 0:
            return {}
        
        node_growth_rate = (last.graph_metrics.nodes - first.graph_metrics.nodes) / time_diff
        edge_growth_rate = (last.graph_metrics.edges - first.graph_metrics.edges) / time_diff
        
        # Average performance metrics
        recent_snapshots = self.snapshots[-5:]  # Last 5 snapshots
        avg_latency = sum(s.retrieval_metrics.avg_latency_ms for s in recent_snapshots) / len(recent_snapshots)
        avg_memory = sum(s.memory_usage_mb for s in recent_snapshots) / len(recent_snapshots)
        
        return {
            "node_growth_rate_per_second": node_growth_rate,
            "edge_growth_rate_per_second": edge_growth_rate,
            "avg_recent_latency_ms": avg_latency,
            "avg_recent_memory_mb": avg_memory,
            "total_time_span_hours": time_diff / 3600
        }
    
    def _analyze_queries(self) -> Dict[str, Any]:
        """Analyze query history for patterns."""
        if not self.query_history:
            return {}
        
        # Query statistics
        latencies = [q["latency_ms"] for q in self.query_history if q["success"]]
        
        analysis = {
            "total_queries": len(self.query_history),
            "successful_queries": sum(1 for q in self.query_history if q["success"]),
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "max_latency_ms": max(latencies) if latencies else 0,
            "min_latency_ms": min(latencies) if latencies else 0
        }
        
        # Query length distribution
        lengths = [q["query_length"] for q in self.query_history]
        analysis["avg_query_length"] = sum(lengths) / len(lengths) if lengths else 0
        
        # Algorithm usage
        algorithms = [q["algorithm"] for q in self.query_history]
        analysis["algorithm_distribution"] = dict(Counter(algorithms))
        
        return analysis
    
    def _create_plotly_graph(self, graph: nx.DiGraph, pos: Dict[str, Tuple[float, float]]) -> go.Figure:
        """Create Plotly graph visualization."""
        # Extract edges
        edge_x = []
        edge_y = []
        for edge in graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        # Create edge trace
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        # Extract nodes
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        
        color_map = {
            "concept": "blue",
            "protocol": "red", 
            "architecture": "green",
            "extension": "purple"
        }
        
        for node in graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            node_data = graph.nodes[node]
            node_text.append(node_data.get("text", node))
            node_type = node_data.get("node_type", "concept")
            node_colors.append(color_map.get(node_type, "gray"))
        
        # Create node trace
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition="middle center",
            marker=dict(
                size=10,
                color=node_colors,
                line=dict(width=2, color="black")
            )
        )
        
        # Create figure
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title="Knowledge Graph Visualization",
                titlefont_size=16,
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                annotations=[ dict(
                    text="Graph Visualization",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.005, y=-0.002,
                    xanchor="left", yanchor="bottom",
                    font=dict(color="gray", size=12)
                )],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )
        )
        
        return fig
    
    def export_data(self, format: str = "json") -> str:
        """
        Export analytics data.
        
        Args:
            format: Export format ("json", "csv")
            
        Returns:
            Exported data as string
        """
        if format == "json":
            export_data = {
                "snapshots": [
                    {
                        "timestamp": s.timestamp,
                        "graph_metrics": {
                            "nodes": s.graph_metrics.nodes,
                            "edges": s.graph_metrics.edges,
                            "density": s.graph_metrics.density,
                            "avg_degree": s.graph_metrics.avg_degree
                        },
                        "retrieval_metrics": {
                            "total_queries": s.retrieval_metrics.total_queries,
                            "avg_latency_ms": s.retrieval_metrics.avg_latency_ms,
                            "cache_hit_rate": s.retrieval_metrics.cache_hit_rate
                        },
                        "memory_usage_mb": s.memory_usage_mb
                    }
                    for s in self.snapshots
                ],
                "query_history": self.query_history,
                "stats": self.stats
            }
            return json.dumps(export_data, indent=2)
        else:
            return "Unsupported export format"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get analytics statistics."""
        return {
            **self.stats,
            "snapshots_count": len(self.snapshots),
            "queries_tracked": len(self.query_history),
            "current_memory_estimate_mb": (
                self.snapshots[-1].memory_usage_mb if self.snapshots else 0.0
            )
        }