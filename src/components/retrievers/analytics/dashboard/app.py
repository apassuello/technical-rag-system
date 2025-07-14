"""
Main Plotly Dash Analytics Dashboard Application.

This module creates and configures the main dashboard application for
real-time monitoring of the advanced retriever system.
"""

import logging
from typing import Optional, Dict, Any
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import threading
import time

from ..metrics_collector import MetricsCollector
from .layouts.overview import create_overview_layout
from .layouts.performance import create_performance_layout
from .layouts.queries import create_queries_layout

logger = logging.getLogger(__name__)


class AnalyticsDashboard:
    """
    Real-time analytics dashboard for advanced retriever monitoring.
    
    This dashboard provides comprehensive real-time monitoring capabilities
    including system overview, performance metrics, query analysis, and
    component health monitoring.
    """
    
    def __init__(self, 
                 metrics_collector: MetricsCollector,
                 title: str = "Advanced Retriever Analytics",
                 debug: bool = False):
        """
        Initialize analytics dashboard.
        
        Args:
            metrics_collector: Metrics collector instance
            title: Dashboard title
            debug: Enable debug mode
        """
        self.metrics_collector = metrics_collector
        self.title = title
        self.debug = debug
        
        # Create Dash app
        self.app = dash.Dash(__name__, title=title)
        self.app.config.suppress_callback_exceptions = True
        
        # Dashboard state
        self.is_running = False
        self.refresh_interval = 5000  # 5 seconds
        
        # Setup layout and callbacks
        self._setup_layout()
        self._setup_callbacks()
        
        logger.info(f"AnalyticsDashboard initialized: {title}")
    
    def _setup_layout(self) -> None:
        """Setup the main dashboard layout."""
        self.app.layout = html.Div([
            # Header
            html.Div([
                html.H1(self.title, className="dashboard-title"),
                html.Div([
                    html.Span("🟢 Live", className="status-indicator"),
                    html.Span(id="last-update", className="last-update")
                ], className="header-status")
            ], className="dashboard-header"),
            
            # Auto-refresh component
            dcc.Interval(
                id='dashboard-refresh',
                interval=self.refresh_interval,
                n_intervals=0
            ),
            
            # Tab navigation
            dcc.Tabs(id="dashboard-tabs", value="overview", children=[
                dcc.Tab(label="📊 Overview", value="overview"),
                dcc.Tab(label="⚡ Performance", value="performance"),
                dcc.Tab(label="🔍 Queries", value="queries"),
                dcc.Tab(label="🔧 Components", value="components"),
            ]),
            
            # Main content area
            html.Div(id="dashboard-content", className="dashboard-content"),
            
            # Store for dashboard data
            dcc.Store(id='dashboard-data'),
            
        ], className="dashboard-container")
    
    def _setup_callbacks(self) -> None:
        """Setup dashboard callbacks for interactivity."""
        
        @self.app.callback(
            Output('dashboard-data', 'data'),
            Output('last-update', 'children'),
            Input('dashboard-refresh', 'n_intervals')
        )
        def update_dashboard_data(n_intervals):
            """Update dashboard data from metrics collector."""
            try:
                dashboard_data = self.metrics_collector.get_real_time_dashboard_data()
                timestamp = time.strftime("%H:%M:%S", time.localtime())
                return dashboard_data, f"Last update: {timestamp}"
            except Exception as e:
                logger.error(f"Failed to update dashboard data: {e}")
                return {}, f"Error: {str(e)}"
        
        @self.app.callback(
            Output('dashboard-content', 'children'),
            Input('dashboard-tabs', 'value'),
            State('dashboard-data', 'data')
        )
        def update_content(active_tab, dashboard_data):
            """Update dashboard content based on active tab."""
            if not dashboard_data:
                return html.Div("Loading...", className="loading")
            
            try:
                if active_tab == "overview":
                    return create_overview_layout(dashboard_data)
                elif active_tab == "performance":
                    return create_performance_layout(dashboard_data)
                elif active_tab == "queries":
                    return create_queries_layout(dashboard_data)
                elif active_tab == "components":
                    return self._create_components_layout(dashboard_data)
                else:
                    return html.Div("Invalid tab selected")
            except Exception as e:
                logger.error(f"Failed to update content for tab {active_tab}: {e}")
                return html.Div(f"Error loading {active_tab}: {str(e)}", className="error")
    
    def _create_components_layout(self, dashboard_data: Dict[str, Any]) -> html.Div:
        """Create components monitoring layout."""
        components_data = dashboard_data.get("components", {})
        backends_data = dashboard_data.get("backends", {})
        
        # Component health cards
        component_cards = []
        for component_name, metrics in components_data.items():
            status = metrics.get("status", "unknown")
            status_color = {
                "healthy": "#4CAF50",
                "warning": "#FF9800", 
                "error": "#F44336",
                "unknown": "#9E9E9E"
            }.get(status, "#9E9E9E")
            
            card = html.Div([
                html.H4(component_name, className="component-name"),
                html.Div([
                    html.Span("●", style={"color": status_color, "fontSize": "20px"}),
                    html.Span(status.title(), className="component-status")
                ], className="status-row"),
                html.Div([
                    html.Div(f"Calls: {metrics.get('total_calls', 0)}", className="metric"),
                    html.Div(f"Latency: {metrics.get('avg_latency_ms', 0):.1f}ms", className="metric"),
                    html.Div(f"Error Rate: {metrics.get('error_rate', 0):.1f}%", className="metric"),
                ], className="metrics-row")
            ], className="component-card")
            
            component_cards.append(card)
        
        # Backend status
        backend_cards = []
        for backend_name, metrics in backends_data.items():
            success_rate = metrics.get("success_rate", 0)
            color = "#4CAF50" if success_rate > 95 else "#FF9800" if success_rate > 80 else "#F44336"
            
            card = html.Div([
                html.H4(f"{backend_name} Backend", className="backend-name"),
                html.Div([
                    html.Div(f"Queries: {metrics.get('total_queries', 0)}", className="metric"),
                    html.Div(f"Success: {success_rate:.1f}%", className="metric"),
                    html.Div(f"Latency: {metrics.get('avg_latency_ms', 0):.1f}ms", className="metric"),
                ], className="metrics-row")
            ], className="backend-card")
            
            backend_cards.append(card)
        
        return html.Div([
            html.H2("Component Health", className="section-title"),
            html.Div(component_cards, className="cards-grid"),
            
            html.H2("Backend Status", className="section-title"),
            html.Div(backend_cards, className="cards-grid"),
        ], className="components-layout")
    
    def run(self, host: str = "127.0.0.1", port: int = 8050, **kwargs) -> None:
        """
        Run the dashboard server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            **kwargs: Additional arguments for Dash.run_server()
        """
        self.is_running = True
        
        logger.info(f"Starting dashboard server at http://{host}:{port}")
        
        try:
            self.app.run_server(
                host=host,
                port=port,
                debug=self.debug,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Dashboard server failed: {e}")
            raise
        finally:
            self.is_running = False
    
    def stop(self) -> None:
        """Stop the dashboard server."""
        self.is_running = False
        logger.info("Dashboard server stopped")


def create_dashboard_app(metrics_collector: MetricsCollector, 
                        title: str = "Advanced Retriever Analytics",
                        debug: bool = False) -> AnalyticsDashboard:
    """
    Create and configure analytics dashboard application.
    
    Args:
        metrics_collector: Metrics collector instance
        title: Dashboard title
        debug: Enable debug mode
        
    Returns:
        Configured dashboard application
    """
    dashboard = AnalyticsDashboard(
        metrics_collector=metrics_collector,
        title=title,
        debug=debug
    )
    
    return dashboard