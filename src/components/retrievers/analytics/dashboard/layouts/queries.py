"""
Dashboard Queries Layout.

This module provides query analysis and monitoring layout including
recent queries, query patterns, and quality analysis.
"""

from typing import Dict, Any, List
from dash import html, dcc, dash_table
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd


def create_queries_layout(dashboard_data: Dict[str, Any]) -> html.Div:
    """
    Create queries analysis dashboard layout.
    
    Args:
        dashboard_data: Real-time dashboard data
        
    Returns:
        Queries layout component
    """
    recent_queries = dashboard_data.get("recent_queries", [])
    quality = dashboard_data.get("quality", {})
    
    # Query statistics summary
    query_summary = _create_query_summary(recent_queries, quality)
    
    # Recent queries table
    queries_table = _create_queries_table(recent_queries)
    
    # Query analysis charts
    analysis_charts = _create_query_analysis_charts(recent_queries, quality)
    
    return html.Div([
        query_summary,
        analysis_charts,
        queries_table
    ], className="queries-layout")


def _create_query_summary(recent_queries: List[Dict[str, Any]], quality: Dict[str, Any]) -> html.Div:
    """Create query statistics summary."""
    if not recent_queries:
        stats_cards = [
            _create_query_stat_card("Total Queries", "0", "📊"),
            _create_query_stat_card("Avg Confidence", "0.00", "🎯"),
            _create_query_stat_card("Avg Results", "0", "📄"),
            _create_query_stat_card("Avg Latency", "0ms", "⏱️")
        ]
    else:
        # Calculate statistics
        total_queries = len(recent_queries)
        avg_confidence = sum(q.get("confidence_score", 0) for q in recent_queries) / total_queries
        avg_results = sum(q.get("num_results", 0) for q in recent_queries) / total_queries
        avg_latency = sum(q.get("total_latency", 0) for q in recent_queries) / total_queries
        
        stats_cards = [
            _create_query_stat_card("Total Queries", str(total_queries), "📊"),
            _create_query_stat_card("Avg Confidence", f"{avg_confidence:.2f}", "🎯"),
            _create_query_stat_card("Avg Results", f"{avg_results:.1f}", "📄"),
            _create_query_stat_card("Avg Latency", f"{avg_latency:.0f}ms", "⏱️")
        ]
    
    return html.Div([
        html.H2("Query Statistics", className="section-title"),
        html.Div(stats_cards, className="query-stats-cards")
    ], className="query-summary")


def _create_query_stat_card(title: str, value: str, icon: str) -> html.Div:
    """Create query statistics card."""
    return html.Div([
        html.Div([
            html.Span(icon, className="query-stat-icon"),
            html.Div([
                html.H3(value, className="query-stat-value"),
                html.P(title, className="query-stat-title")
            ], className="query-stat-text")
        ], className="query-stat-content")
    ], className="query-stat-card")


def _create_queries_table(recent_queries: List[Dict[str, Any]]) -> html.Div:
    """Create recent queries table."""
    if not recent_queries:
        return html.Div([
            html.H3("Recent Queries", className="subsection-title"),
            html.P("No recent queries available", className="no-data")
        ])
    
    # Prepare data for table
    table_data = []
    for query in recent_queries[-20:]:  # Show last 20 queries
        table_data.append({
            "Query": query.get("query_text", "")[:60] + "..." if len(query.get("query_text", "")) > 60 else query.get("query_text", ""),
            "Timestamp": pd.to_datetime(query.get("timestamp", 0), unit="s").strftime("%H:%M:%S") if query.get("timestamp") else "",
            "Latency": f"{query.get('total_latency', 0):.0f}ms",
            "Confidence": f"{query.get('confidence_score', 0):.2f}",
            "Results": str(query.get("num_results", 0)),
            "Backend": query.get("backend_used", ""),
            "Components": ", ".join(query.get("components_used", [])[:2])  # Show first 2 components
        })
    
    # Create DataTable
    table = dash_table.DataTable(
        data=table_data,
        columns=[
            {"name": "Query", "id": "Query", "presentation": "markdown"},
            {"name": "Time", "id": "Timestamp"},
            {"name": "Latency", "id": "Latency"},
            {"name": "Confidence", "id": "Confidence"},
            {"name": "Results", "id": "Results"},
            {"name": "Backend", "id": "Backend"},
            {"name": "Components", "id": "Components"}
        ],
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontFamily': 'Arial'
        },
        style_header={
            'backgroundColor': '#f8f9fa',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f8f9fa'
            }
        ],
        page_size=10,
        sort_action="native"
    )
    
    return html.Div([
        html.H3("Recent Queries", className="subsection-title"),
        table
    ], className="queries-table-section")


def _create_query_analysis_charts(recent_queries: List[Dict[str, Any]], quality: Dict[str, Any]) -> html.Div:
    """Create query analysis charts."""
    if not recent_queries:
        return html.Div([
            html.H3("Query Analysis", className="subsection-title"),
            html.P("No data available for analysis", className="no-data")
        ])
    
    # Confidence distribution chart
    confidence_chart = _create_confidence_distribution_chart(recent_queries)
    
    # Latency vs confidence scatter
    latency_confidence_chart = _create_latency_confidence_chart(recent_queries)
    
    # Backend usage pie chart
    backend_chart = _create_backend_usage_chart(recent_queries)
    
    # Query length distribution
    query_length_chart = _create_query_length_distribution(recent_queries)
    
    return html.Div([
        html.H3("Query Analysis", className="subsection-title"),
        
        # Top row - Confidence and Latency analysis
        html.Div([
            html.Div([
                dcc.Graph(figure=confidence_chart, config={'displayModeBar': False})
            ], className="chart-container"),
            
            html.Div([
                dcc.Graph(figure=latency_confidence_chart, config={'displayModeBar': False})
            ], className="chart-container")
        ], className="charts-row"),
        
        # Bottom row - Backend usage and Query patterns
        html.Div([
            html.Div([
                dcc.Graph(figure=backend_chart, config={'displayModeBar': False})
            ], className="chart-container"),
            
            html.Div([
                dcc.Graph(figure=query_length_chart, config={'displayModeBar': False})
            ], className="chart-container")
        ], className="charts-row")
        
    ], className="query-analysis-section")


def _create_confidence_distribution_chart(recent_queries: List[Dict[str, Any]]) -> go.Figure:
    """Create confidence score distribution chart."""
    confidences = [q.get("confidence_score", 0) for q in recent_queries]
    
    fig = go.Figure(data=[
        go.Histogram(
            x=confidences,
            nbinsx=20,
            marker=dict(color='#2E86AB', opacity=0.7),
            name='Confidence Distribution'
        )
    ])
    
    fig.update_layout(
        title="Confidence Score Distribution",
        xaxis_title="Confidence Score",
        yaxis_title="Number of Queries",
        height=300,
        margin=dict(l=50, r=50, t=50, b=50),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    
    return fig


def _create_latency_confidence_chart(recent_queries: List[Dict[str, Any]]) -> go.Figure:
    """Create latency vs confidence scatter plot."""
    latencies = [q.get("total_latency", 0) for q in recent_queries]
    confidences = [q.get("confidence_score", 0) for q in recent_queries]
    backends = [q.get("backend_used", "unknown") for q in recent_queries]
    
    # Color mapping for backends
    color_map = {"faiss": "#2E86AB", "weaviate": "#A23B72", "unknown": "#666666"}
    colors = [color_map.get(backend, "#666666") for backend in backends]
    
    fig = go.Figure(data=go.Scatter(
        x=latencies,
        y=confidences,
        mode='markers',
        marker=dict(
            color=colors,
            size=8,
            opacity=0.7
        ),
        text=[f"Backend: {b}" for b in backends],
        hovertemplate="<b>Latency:</b> %{x:.1f}ms<br><b>Confidence:</b> %{y:.2f}<br>%{text}<extra></extra>"
    ))
    
    fig.update_layout(
        title="Latency vs Confidence",
        xaxis_title="Latency (ms)",
        yaxis_title="Confidence Score",
        height=300,
        margin=dict(l=50, r=50, t=50, b=50),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def _create_backend_usage_chart(recent_queries: List[Dict[str, Any]]) -> go.Figure:
    """Create backend usage pie chart."""
    backends = [q.get("backend_used", "unknown") for q in recent_queries]
    backend_counts = {}
    
    for backend in backends:
        backend_counts[backend] = backend_counts.get(backend, 0) + 1
    
    labels = list(backend_counts.keys())
    values = list(backend_counts.values())
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']
    
    fig = go.Figure(data=[
        go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors[:len(labels)]),
            textinfo='label+percent',
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        title="Backend Usage Distribution",
        height=300,
        margin=dict(l=50, r=50, t=50, b=50),
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def _create_query_length_distribution(recent_queries: List[Dict[str, Any]]) -> go.Figure:
    """Create query length distribution chart."""
    query_lengths = [len(q.get("query_text", "").split()) for q in recent_queries]
    
    # Create bins for query lengths
    bins = [0, 2, 5, 10, 15, 20, float('inf')]
    bin_labels = ["1-2", "3-5", "6-10", "11-15", "16-20", "20+"]
    bin_counts = [0] * (len(bins) - 1)
    
    for length in query_lengths:
        for i in range(len(bins) - 1):
            if bins[i] < length <= bins[i + 1]:
                bin_counts[i] += 1
                break
    
    fig = go.Figure(data=[
        go.Bar(
            x=bin_labels,
            y=bin_counts,
            marker=dict(color='#4CAF50'),
            text=bin_counts,
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        title="Query Length Distribution (Words)",
        xaxis_title="Number of Words",
        yaxis_title="Number of Queries", 
        height=300,
        margin=dict(l=50, r=50, t=50, b=50),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    
    return fig