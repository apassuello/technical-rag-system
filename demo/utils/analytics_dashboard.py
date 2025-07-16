"""
Analytics Dashboard for Epic 2 Demo
===================================

Creates interactive Plotly visualizations for real-time performance monitoring
and component health analysis.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import time
from collections import deque

class PerformanceTracker:
    """Tracks performance metrics over time for analytics"""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.query_history = deque(maxlen=max_history)
        self.stage_history = deque(maxlen=max_history)
        
    def add_query(self, query: str, performance: Dict[str, Any]):
        """Add a query performance record"""
        timestamp = datetime.now()
        record = {
            'timestamp': timestamp,
            'query': query,
            'total_time_ms': performance.get('total_time_ms', 0),
            'stages': performance.get('stages', {}),
            'component_details': performance.get('component_details', {})
        }
        self.query_history.append(record)
        
        # Add stage-specific records
        for stage_name, stage_data in performance.get('stages', {}).items():
            stage_record = {
                'timestamp': timestamp,
                'query': query,
                'stage': stage_name,
                'time_ms': stage_data.get('time_ms', 0),
                'results': stage_data.get('results', 0)
            }
            self.stage_history.append(stage_record)
    
    def get_recent_queries(self, limit: int = 10) -> List[Dict]:
        """Get recent query records"""
        return list(self.query_history)[-limit:]
    
    def get_stage_performance_df(self) -> pd.DataFrame:
        """Get stage performance as DataFrame"""
        if not self.stage_history:
            return pd.DataFrame()
        
        return pd.DataFrame(self.stage_history)
    
    def get_query_performance_df(self) -> pd.DataFrame:
        """Get query performance as DataFrame"""
        if not self.query_history:
            return pd.DataFrame()
        
        return pd.DataFrame(self.query_history)


class AnalyticsDashboard:
    """Main analytics dashboard with interactive charts"""
    
    def __init__(self):
        self.tracker = PerformanceTracker()
        
    def add_query_data(self, query: str, performance: Dict[str, Any]):
        """Add query data to tracking"""
        self.tracker.add_query(query, performance)
    
    def create_stage_performance_chart(self) -> go.Figure:
        """Create interactive stage performance chart"""
        df = self.tracker.get_stage_performance_df()
        
        if df.empty:
            # Return empty chart with placeholder
            fig = go.Figure()
            fig.add_annotation(
                text="No performance data available yet.<br>Run some queries to see analytics!",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font=dict(size=16)
            )
            fig.update_layout(
                title="Stage Performance Over Time",
                xaxis_title="Time",
                yaxis_title="Duration (ms)",
                height=400
            )
            return fig
        
        # Create interactive line chart
        fig = px.line(
            df, 
            x='timestamp', 
            y='time_ms', 
            color='stage',
            title="Stage Performance Over Time",
            labels={'time_ms': 'Duration (ms)', 'timestamp': 'Time'},
            hover_data=['query', 'results']
        )
        
        # Customize layout
        fig.update_layout(
            height=400,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def create_query_performance_chart(self) -> go.Figure:
        """Create query performance overview chart"""
        df = self.tracker.get_query_performance_df()
        
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No query data available yet.<br>Run some queries to see performance trends!",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font=dict(size=16)
            )
            fig.update_layout(
                title="Query Performance Trends",
                xaxis_title="Query",
                yaxis_title="Total Time (ms)",
                height=400
            )
            return fig
        
        # Create bar chart of recent queries
        recent_queries = df.tail(20)  # Last 20 queries
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=list(range(len(recent_queries))),
            y=recent_queries['total_time_ms'],
            text=[f"{q[:30]}..." if len(q) > 30 else q for q in recent_queries['query']],
            textposition='auto',
            hovertemplate='<b>Query:</b> %{text}<br><b>Time:</b> %{y:.0f}ms<extra></extra>',
            marker_color='rgba(46, 134, 171, 0.7)'
        ))
        
        fig.update_layout(
            title="Recent Query Performance",
            xaxis_title="Query Index",
            yaxis_title="Total Time (ms)",
            height=400,
            showlegend=False
        )
        
        return fig
    
    def create_stage_breakdown_chart(self) -> go.Figure:
        """Create stage breakdown pie chart for latest query"""
        df = self.tracker.get_stage_performance_df()
        
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No stage data available yet.<br>Run a query to see stage breakdown!",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font=dict(size=16)
            )
            fig.update_layout(
                title="Stage Breakdown (Latest Query)",
                height=400
            )
            return fig
        
        # Get latest query's stage data
        latest_timestamp = df['timestamp'].max()
        latest_data = df[df['timestamp'] == latest_timestamp]
        
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=latest_data['stage'],
            values=latest_data['time_ms'],
            hole=0.3,
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>Time: %{value:.0f}ms<br>Percentage: %{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title="Stage Breakdown (Latest Query)",
            height=400,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.01
            )
        )
        
        return fig
    
    def create_component_health_chart(self) -> go.Figure:
        """Create component health monitoring chart"""
        df = self.tracker.get_query_performance_df()
        
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No component data available yet.<br>Run queries to see component health!",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font=dict(size=16)
            )
            fig.update_layout(
                title="Component Health Status",
                height=400
            )
            return fig
        
        # Calculate component health metrics
        recent_queries = df.tail(10)
        
        # Mock component health data (in real implementation, this would come from actual metrics)
        components = ['Database', 'Retriever', 'Generator', 'Neural Reranker', 'Graph Engine']
        health_scores = [95, 98, 97, 93, 96]  # Mock scores
        
        # Create gauge-style chart
        fig = go.Figure()
        
        colors = ['green' if score >= 95 else 'yellow' if score >= 90 else 'red' for score in health_scores]
        
        fig.add_trace(go.Bar(
            x=components,
            y=health_scores,
            marker_color=colors,
            text=[f"{score}%" for score in health_scores],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>Health: %{y}%<extra></extra>'
        ))
        
        fig.update_layout(
            title="Component Health Status",
            xaxis_title="Component",
            yaxis_title="Health Score (%)",
            yaxis=dict(range=[0, 100]),
            height=400,
            showlegend=False
        )
        
        return fig
    
    def create_performance_summary_metrics(self) -> Dict[str, Any]:
        """Create performance summary metrics"""
        df = self.tracker.get_query_performance_df()
        
        if df.empty:
            return {
                'total_queries': 0,
                'avg_response_time': 0,
                'fastest_query': 0,
                'slowest_query': 0,
                'success_rate': 0
            }
        
        return {
            'total_queries': len(df),
            'avg_response_time': df['total_time_ms'].mean(),
            'fastest_query': df['total_time_ms'].min(),
            'slowest_query': df['total_time_ms'].max(),
            'success_rate': 100  # Assuming all queries succeed for now
        }
    
    def render_dashboard(self):
        """Render the complete analytics dashboard"""
        st.header("📊 Real-Time Analytics Dashboard")
        
        # Performance summary metrics
        metrics = self.create_performance_summary_metrics()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Queries", metrics['total_queries'])
        with col2:
            st.metric("Avg Response Time", f"{metrics['avg_response_time']:.0f}ms")
        with col3:
            st.metric("Fastest Query", f"{metrics['fastest_query']:.0f}ms")
        with col4:
            st.metric("Success Rate", f"{metrics['success_rate']:.1f}%")
        
        # Performance charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(
                self.create_stage_performance_chart(),
                use_container_width=True
            )
        
        with col2:
            st.plotly_chart(
                self.create_query_performance_chart(),
                use_container_width=True
            )
        
        # Additional charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(
                self.create_stage_breakdown_chart(),
                use_container_width=True
            )
        
        with col2:
            st.plotly_chart(
                self.create_component_health_chart(),
                use_container_width=True
            )
        
        # Query history table
        if not self.tracker.query_history:
            st.info("No query history available yet. Run some queries to see analytics!")
        else:
            st.subheader("📈 Recent Query History")
            recent_queries = self.tracker.get_recent_queries(10)
            
            history_data = []
            for record in recent_queries:
                history_data.append({
                    'Time': record['timestamp'].strftime('%H:%M:%S'),
                    'Query': record['query'][:50] + '...' if len(record['query']) > 50 else record['query'],
                    'Response Time (ms)': f"{record['total_time_ms']:.0f}",
                    'Status': '✅ Success'
                })
            
            st.table(pd.DataFrame(history_data))


# Global analytics dashboard instance
analytics_dashboard = AnalyticsDashboard()