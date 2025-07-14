"""
Dashboard Performance Layout.

This module provides detailed performance monitoring layout including
latency analysis, throughput metrics, and component performance breakdown.
"""

from typing import Dict, Any, List
from dash import html, dcc
import plotly.graph_objs as go
import plotly.express as px


def create_performance_layout(dashboard_data: Dict[str, Any]) -> html.Div:
    """
    Create performance monitoring dashboard layout.
    
    Args:
        dashboard_data: Real-time dashboard data
        
    Returns:
        Performance layout component
    """
    performance = dashboard_data.get("performance", {})
    time_series = dashboard_data.get("time_series", {})
    components = dashboard_data.get("components", {})
    backends = dashboard_data.get("backends", {})
    
    # Performance summary
    summary_section = _create_performance_summary(performance)
    
    # Time series charts
    time_series_section = _create_time_series_section(time_series)
    
    # Component performance
    component_section = _create_component_performance_section(components)
    
    # Backend performance
    backend_section = _create_backend_performance_section(backends)
    
    return html.Div([
        summary_section,
        time_series_section,
        component_section,
        backend_section
    ], className="performance-layout")


def _create_performance_summary(performance: Dict[str, Any]) -> html.Div:
    """Create performance summary section."""
    latency_percentiles = performance.get("latency_percentiles", {})
    throughput = performance.get("throughput", {})
    component_latencies = performance.get("component_latencies", {})
    
    # Key performance metrics
    perf_cards = [
        _create_perf_card(
            "P50 Latency",
            f"{latency_percentiles.get('p50', 0):.1f}ms",
            "📊",
            "good" if latency_percentiles.get('p50', 0) < 200 else "warning"
        ),
        _create_perf_card(
            "P95 Latency", 
            f"{latency_percentiles.get('p95', 0):.1f}ms",
            "📈",
            "good" if latency_percentiles.get('p95', 0) < 500 else "warning"
        ),
        _create_perf_card(
            "P99 Latency",
            f"{latency_percentiles.get('p99', 0):.1f}ms", 
            "🔴",
            "good" if latency_percentiles.get('p99', 0) < 1000 else "warning"
        ),
        _create_perf_card(
            "Current QPS",
            f"{throughput.get('current_qps', 0):.2f}",
            "⚡",
            "good"
        ),
        _create_perf_card(
            "Peak QPS",
            f"{throughput.get('peak_qps', 0):.2f}",
            "🚀",
            "good"
        )
    ]
    
    return html.Div([
        html.H2("Performance Summary", className="section-title"),
        html.Div(perf_cards, className="perf-cards")
    ], className="performance-summary")


def _create_perf_card(title: str, value: str, icon: str, status: str) -> html.Div:
    """Create performance metric card."""
    status_colors = {
        "good": "#4CAF50",
        "warning": "#FF9800", 
        "critical": "#F44336"
    }
    
    return html.Div([
        html.Div([
            html.Span(icon, className="perf-icon"),
            html.Div([
                html.H3(value, className="perf-value", style={"color": status_colors.get(status, "#333")}),
                html.P(title, className="perf-title")
            ], className="perf-text")
        ], className="perf-content")
    ], className="perf-card")


def _create_time_series_section(time_series: Dict[str, Any]) -> html.Div:
    """Create time series performance charts."""
    latency_chart = _create_latency_time_series(time_series)
    qps_chart = _create_qps_time_series(time_series)
    success_rate_chart = _create_success_rate_time_series(time_series)
    
    return html.Div([
        html.H3("Performance Trends", className="subsection-title"),
        
        # Latency over time
        html.Div([
            dcc.Graph(figure=latency_chart, config={'displayModeBar': False})
        ], className="chart-container-full"),
        
        # QPS and Success Rate
        html.Div([
            html.Div([
                dcc.Graph(figure=qps_chart, config={'displayModeBar': False})
            ], className="chart-container"),
            
            html.Div([
                dcc.Graph(figure=success_rate_chart, config={'displayModeBar': False})
            ], className="chart-container")
        ], className="charts-row")
        
    ], className="time-series-section")


def _create_latency_time_series(time_series: Dict[str, Any]) -> go.Figure:
    """Create latency time series chart."""
    timestamps = time_series.get("timestamps", [])
    latencies = time_series.get("latency", [])
    
    fig = go.Figure()
    
    if timestamps and latencies:
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=latencies,
            mode='lines',
            name='Latency',
            line=dict(color='#2E86AB', width=2),
            fill='tonexty',
            fillcolor='rgba(46, 134, 171, 0.1)'
        ))
    
    fig.update_layout(
        title="Latency Over Time",
        xaxis_title="Time",
        yaxis_title="Latency (ms)",
        height=400,
        margin=dict(l=50, r=50, t=50, b=50),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    
    return fig


def _create_qps_time_series(time_series: Dict[str, Any]) -> go.Figure:
    """Create QPS time series chart."""
    timestamps = time_series.get("timestamps", [])
    qps_values = time_series.get("qps", [])
    
    fig = go.Figure()
    
    if timestamps and qps_values:
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=qps_values,
            mode='lines+markers',
            name='QPS',
            line=dict(color='#4CAF50', width=3),
            marker=dict(size=4)
        ))
    
    fig.update_layout(
        title="Queries Per Second",
        xaxis_title="Time", 
        yaxis_title="QPS",
        height=300,
        margin=dict(l=50, r=50, t=50, b=50),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    
    return fig


def _create_success_rate_time_series(time_series: Dict[str, Any]) -> go.Figure:
    """Create success rate time series chart."""
    timestamps = time_series.get("timestamps", [])
    success_rates = time_series.get("success_rate", [])
    
    fig = go.Figure()
    
    if timestamps and success_rates:
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=success_rates,
            mode='lines',
            name='Success Rate',
            line=dict(color='#FF9800', width=3),
            fill='tozeroy',
            fillcolor='rgba(255, 152, 0, 0.1)'
        ))
    
    fig.update_layout(
        title="Success Rate (%)",
        xaxis_title="Time",
        yaxis_title="Success Rate (%)",
        yaxis=dict(range=[0, 100]),
        height=300,
        margin=dict(l=50, r=50, t=50, b=50),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    
    return fig


def _create_component_performance_section(components: Dict[str, Any]) -> html.Div:
    """Create component performance analysis section."""
    if not components:
        return html.Div([
            html.H3("Component Performance", className="subsection-title"),
            html.P("No component data available", className="no-data")
        ])
    
    # Component metrics table
    component_table = _create_component_table(components)
    
    # Component latency comparison chart
    component_chart = _create_component_comparison_chart(components)
    
    return html.Div([
        html.H3("Component Performance", className="subsection-title"),
        
        # Component comparison chart
        html.Div([
            dcc.Graph(figure=component_chart, config={'displayModeBar': False})
        ], className="chart-container-full"),
        
        # Component details table
        component_table
        
    ], className="component-performance-section")


def _create_component_table(components: Dict[str, Any]) -> html.Div:
    """Create component performance table."""
    table_rows = []
    
    for component_name, metrics in components.items():
        status = metrics.get("status", "unknown")
        status_color = {
            "healthy": "#4CAF50",
            "warning": "#FF9800",
            "error": "#F44336",
            "unknown": "#9E9E9E"
        }.get(status, "#9E9E9E")
        
        row = html.Tr([
            html.Td(component_name, className="component-name-cell"),
            html.Td([
                html.Span("●", style={"color": status_color}),
                html.Span(f" {status.title()}")
            ], className="status-cell"),
            html.Td(f"{metrics.get('total_calls', 0):,}", className="number-cell"),
            html.Td(f"{metrics.get('avg_latency_ms', 0):.1f}ms", className="number-cell"),
            html.Td(f"{metrics.get('error_rate', 0):.1f}%", className="number-cell")
        ])
        
        table_rows.append(row)
    
    table = html.Table([
        html.Thead([
            html.Tr([
                html.Th("Component"),
                html.Th("Status"),
                html.Th("Total Calls"),
                html.Th("Avg Latency"),
                html.Th("Error Rate")
            ])
        ]),
        html.Tbody(table_rows)
    ], className="component-table")
    
    return table


def _create_component_comparison_chart(components: Dict[str, Any]) -> go.Figure:
    """Create component performance comparison chart."""
    component_names = list(components.keys())
    latencies = [metrics.get("avg_latency_ms", 0) for metrics in components.values()]
    error_rates = [metrics.get("error_rate", 0) for metrics in components.values()]
    
    fig = go.Figure()
    
    # Latency bars
    fig.add_trace(go.Bar(
        x=component_names,
        y=latencies,
        name='Latency (ms)',
        marker=dict(color='#2E86AB'),
        yaxis='y1'
    ))
    
    # Error rate line
    fig.add_trace(go.Scatter(
        x=component_names,
        y=error_rates,
        name='Error Rate (%)',
        mode='lines+markers',
        line=dict(color='#F44336', width=3),
        marker=dict(size=8),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title="Component Latency vs Error Rate",
        xaxis_title="Component",
        yaxis=dict(
            title="Latency (ms)",
            titlefont=dict(color='#2E86AB'),
            tickfont=dict(color='#2E86AB')
        ),
        yaxis2=dict(
            title="Error Rate (%)",
            titlefont=dict(color='#F44336'),
            tickfont=dict(color='#F44336'),
            anchor='x',
            overlaying='y',
            side='right'
        ),
        height=400,
        margin=dict(l=50, r=80, t=50, b=50),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(x=0.01, y=0.99)
    )
    
    return fig


def _create_backend_performance_section(backends: Dict[str, Any]) -> html.Div:
    """Create backend performance section."""
    if not backends:
        return html.Div([
            html.H3("Backend Performance", className="subsection-title"),
            html.P("No backend data available", className="no-data")
        ])
    
    # Backend comparison chart
    backend_chart = _create_backend_comparison_chart(backends)
    
    # Backend metrics cards
    backend_cards = []
    for backend_name, metrics in backends.items():
        success_rate = metrics.get("success_rate", 0)
        total_queries = metrics.get("total_queries", 0)
        avg_latency = metrics.get("avg_latency_ms", 0)
        
        status = "good" if success_rate > 95 else "warning" if success_rate > 80 else "critical"
        
        card = html.Div([
            html.H4(f"{backend_name.title()} Backend", className="backend-title"),
            html.Div([
                html.Div([
                    html.Span(f"{total_queries:,}", className="backend-metric-value"),
                    html.Span("Total Queries", className="backend-metric-label")
                ], className="backend-metric"),
                
                html.Div([
                    html.Span(f"{success_rate:.1f}%", className="backend-metric-value"),
                    html.Span("Success Rate", className="backend-metric-label")
                ], className="backend-metric"),
                
                html.Div([
                    html.Span(f"{avg_latency:.1f}ms", className="backend-metric-value"),
                    html.Span("Avg Latency", className="backend-metric-label")
                ], className="backend-metric")
            ], className="backend-metrics")
        ], className="backend-card")
        
        backend_cards.append(card)
    
    return html.Div([
        html.H3("Backend Performance", className="subsection-title"),
        
        # Backend cards
        html.Div(backend_cards, className="backend-cards"),
        
        # Backend comparison chart
        html.Div([
            dcc.Graph(figure=backend_chart, config={'displayModeBar': False})
        ], className="chart-container-full")
        
    ], className="backend-performance-section")


def _create_backend_comparison_chart(backends: Dict[str, Any]) -> go.Figure:
    """Create backend performance comparison chart."""
    backend_names = list(backends.keys())
    success_rates = [metrics.get("success_rate", 0) for metrics in backends.values()]
    latencies = [metrics.get("avg_latency_ms", 0) for metrics in backends.values()]
    
    fig = go.Figure()
    
    # Success rate bars
    fig.add_trace(go.Bar(
        x=backend_names,
        y=success_rates,
        name='Success Rate (%)',
        marker=dict(color='#4CAF50'),
        yaxis='y1'
    ))
    
    # Latency line
    fig.add_trace(go.Scatter(
        x=backend_names,
        y=latencies,
        name='Latency (ms)',
        mode='lines+markers',
        line=dict(color='#2E86AB', width=3),
        marker=dict(size=8),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title="Backend Success Rate vs Latency",
        xaxis_title="Backend",
        yaxis=dict(
            title="Success Rate (%)",
            titlefont=dict(color='#4CAF50'),
            tickfont=dict(color='#4CAF50'),
            range=[0, 100]
        ),
        yaxis2=dict(
            title="Latency (ms)",
            titlefont=dict(color='#2E86AB'),
            tickfont=dict(color='#2E86AB'),
            anchor='x',
            overlaying='y',
            side='right'
        ),
        height=400,
        margin=dict(l=50, r=80, t=50, b=50),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(x=0.01, y=0.99)
    )
    
    return fig