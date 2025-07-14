"""
Dashboard Overview Layout.

This module provides the overview layout for the analytics dashboard,
showing high-level system metrics and status.
"""

from typing import Dict, Any
from dash import html, dcc
import plotly.graph_objs as go
import plotly.express as px


def create_overview_layout(dashboard_data: Dict[str, Any]) -> html.Div:
    """
    Create overview dashboard layout.
    
    Args:
        dashboard_data: Real-time dashboard data
        
    Returns:
        Overview layout component
    """
    overview = dashboard_data.get("overview", {})
    performance = dashboard_data.get("performance", {})
    quality = dashboard_data.get("quality", {})
    time_series = dashboard_data.get("time_series", {})
    
    # Key metrics cards
    metrics_cards = [
        _create_metric_card(
            "Total Queries",
            overview.get("total_queries", 0),
            "📊",
            "total-queries-card"
        ),
        _create_metric_card(
            "Queries/Min",
            f"{overview.get('queries_per_minute', 0):.1f}",
            "⚡",
            "qpm-card"
        ),
        _create_metric_card(
            "Avg Latency",
            f"{overview.get('avg_latency_ms', 0):.1f}ms",
            "⏱️",
            "latency-card"
        ),
        _create_metric_card(
            "Success Rate", 
            f"{overview.get('success_rate', 0):.1f}%",
            "✅",
            "success-card"
        )
    ]
    
    # System status
    status_indicators = _create_status_indicators(performance, quality)
    
    # Time series charts
    charts = _create_overview_charts(time_series, performance)
    
    return html.Div([
        # Key metrics row
        html.Div([
            html.H2("System Overview", className="section-title"),
            html.Div(metrics_cards, className="metrics-cards")
        ], className="metrics-section"),
        
        # Status indicators
        html.Div([
            html.H3("System Status", className="subsection-title"),
            status_indicators
        ], className="status-section"),
        
        # Charts
        html.Div([
            html.H3("Performance Trends", className="subsection-title"),
            charts
        ], className="charts-section")
        
    ], className="overview-layout")


def _create_metric_card(title: str, value: str, icon: str, card_id: str) -> html.Div:
    """Create a metric card component."""
    return html.Div([
        html.Div([
            html.Span(icon, className="metric-icon"),
            html.Div([
                html.H3(str(value), className="metric-value"),
                html.P(title, className="metric-title")
            ], className="metric-text")
        ], className="metric-content")
    ], className="metric-card", id=card_id)


def _create_status_indicators(performance: Dict[str, Any], quality: Dict[str, Any]) -> html.Div:
    """Create system status indicators."""
    
    # Determine status colors based on metrics
    latency_p95 = performance.get("latency_percentiles", {}).get("p95", 0)
    avg_confidence = quality.get("avg_confidence_score", 0)
    
    # Status determination
    latency_status = "healthy" if latency_p95 < 500 else "warning" if latency_p95 < 1000 else "critical"
    quality_status = "healthy" if avg_confidence > 0.8 else "warning" if avg_confidence > 0.6 else "critical"
    
    status_colors = {
        "healthy": "#4CAF50",
        "warning": "#FF9800",
        "critical": "#F44336"
    }
    
    indicators = [
        html.Div([
            html.Span("●", style={"color": status_colors[latency_status], "fontSize": "20px"}),
            html.Span(f"Latency P95: {latency_p95:.1f}ms", className="status-text")
        ], className="status-indicator"),
        
        html.Div([
            html.Span("●", style={"color": status_colors[quality_status], "fontSize": "20px"}),
            html.Span(f"Quality Score: {avg_confidence:.2f}", className="status-text")
        ], className="status-indicator"),
        
        html.Div([
            html.Span("●", style={"color": "#4CAF50", "fontSize": "20px"}),
            html.Span("Neural Reranking: Active", className="status-text")
        ], className="status-indicator"),
        
        html.Div([
            html.Span("●", style={"color": "#4CAF50", "fontSize": "20px"}),
            html.Span("Multi-Backend: Operational", className="status-text")
        ], className="status-indicator")
    ]
    
    return html.Div(indicators, className="status-indicators")


def _create_overview_charts(time_series: Dict[str, Any], performance: Dict[str, Any]) -> html.Div:
    """Create overview charts."""
    
    # Queries per second over time
    qps_chart = _create_qps_chart(time_series)
    
    # Latency distribution
    latency_chart = _create_latency_distribution_chart(performance)
    
    # Component latency breakdown
    component_chart = _create_component_latency_chart(performance)
    
    return html.Div([
        # Top row - QPS and Latency Distribution
        html.Div([
            html.Div([
                dcc.Graph(figure=qps_chart, config={'displayModeBar': False})
            ], className="chart-container"),
            
            html.Div([
                dcc.Graph(figure=latency_chart, config={'displayModeBar': False})
            ], className="chart-container")
        ], className="charts-row"),
        
        # Bottom row - Component breakdown
        html.Div([
            html.Div([
                dcc.Graph(figure=component_chart, config={'displayModeBar': False})
            ], className="chart-container-full")
        ], className="charts-row")
    ])


def _create_qps_chart(time_series: Dict[str, Any]) -> go.Figure:
    """Create queries per second chart."""
    timestamps = time_series.get("timestamps", [])
    qps_values = time_series.get("qps", [])
    
    fig = go.Figure()
    
    if timestamps and qps_values:
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=qps_values,
            mode='lines+markers',
            name='QPS',
            line=dict(color='#2E86AB', width=3),
            marker=dict(size=6)
        ))
    
    fig.update_layout(
        title="Queries Per Second",
        xaxis_title="Time",
        yaxis_title="QPS",
        height=300,
        margin=dict(l=50, r=50, t=50, b=50),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def _create_latency_distribution_chart(performance: Dict[str, Any]) -> go.Figure:
    """Create latency distribution chart."""
    latency_percentiles = performance.get("latency_percentiles", {})
    
    percentiles = ['P50', 'P95', 'P99']
    values = [
        latency_percentiles.get("p50", 0),
        latency_percentiles.get("p95", 0),
        latency_percentiles.get("p99", 0)
    ]
    
    colors = ['#4CAF50', '#FF9800', '#F44336']
    
    fig = go.Figure(data=[
        go.Bar(
            x=percentiles,
            y=values,
            marker=dict(color=colors),
            text=[f'{v:.1f}ms' for v in values],
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        title="Latency Percentiles",
        xaxis_title="Percentile",
        yaxis_title="Latency (ms)",
        height=300,
        margin=dict(l=50, r=50, t=50, b=50),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def _create_component_latency_chart(performance: Dict[str, Any]) -> go.Figure:
    """Create component latency breakdown chart."""
    component_latencies = performance.get("component_latencies", {})
    
    components = list(component_latencies.keys())
    latencies = list(component_latencies.values())
    
    # Color mapping for components
    color_map = {
        "dense_retrieval": "#2E86AB",
        "sparse_retrieval": "#A23B72", 
        "graph_retrieval": "#F18F01",
        "neural_reranking": "#C73E1D"
    }
    
    colors = [color_map.get(comp, "#666666") for comp in components]
    
    fig = go.Figure(data=[
        go.Bar(
            x=components,
            y=latencies,
            marker=dict(color=colors),
            text=[f'{lat:.1f}ms' for lat in latencies],
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        title="Component Latency Breakdown",
        xaxis_title="Component",
        yaxis_title="Average Latency (ms)",
        height=350,
        margin=dict(l=50, r=50, t=50, b=50),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig