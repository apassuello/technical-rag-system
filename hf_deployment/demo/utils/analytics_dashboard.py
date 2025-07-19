"""
Analytics dashboard for Epic 2 Demo
===================================

Simplified analytics dashboard for HF deployment
"""

import streamlit as st
import logging
from typing import Any

logger = logging.getLogger(__name__)


def analytics_dashboard(system_manager: Any):
    """Display analytics dashboard"""
    st.subheader("📊 Epic 2 Analytics Dashboard")
    
    if not system_manager.is_initialized:
        st.info("Initialize system to see analytics")
        return
    
    # System status
    status = system_manager.get_system_status()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("System Status", status.get("status", "Unknown"))
        st.metric("Architecture", status.get("architecture", "Unknown").upper())
    
    with col2:
        st.metric("Documents", status.get("documents", 0))
        st.metric("Retriever Type", status.get("retriever_type", "Unknown"))
    
    with col3:
        perf = status.get("performance", {})
        if perf:
            st.metric("Total Queries", perf.get("total_queries", 0))
            avg_time = perf.get("average_response_time", 0)
            st.metric("Avg Response", f"{avg_time:.0f}ms" if avg_time else "N/A")
        else:
            st.metric("Total Queries", "N/A")
            st.metric("Avg Response", "N/A")
    
    # Last query results
    if hasattr(system_manager, 'last_query_results') and system_manager.last_query_results:
        st.subheader("🔍 Last Query Performance")
        
        results = system_manager.last_query_results
        perf = results.get("performance", {})
        
        if perf:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Time", f"{perf.get('total_time_ms', 0):.0f}ms")
                breakdown = perf.get("breakdown", {})
                st.metric("Retrieval", f"{breakdown.get('retrieval_time_ms', 0):.0f}ms")
            
            with col2:
                st.metric("Generation", f"{breakdown.get('generation_time_ms', 0):.0f}ms")
                st.metric("Method", results.get("retrieval_method", "Unknown"))
    
    else:
        st.info("Process a query to see performance analytics")