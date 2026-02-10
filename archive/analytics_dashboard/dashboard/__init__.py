"""
Real-time Analytics Dashboard.

This module provides a Plotly Dash-based dashboard for real-time monitoring
of the advanced retriever system performance and quality metrics.
"""

from .app import create_dashboard_app

__all__ = [
    "create_dashboard_app",
]