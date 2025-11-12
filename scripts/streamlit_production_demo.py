#!/usr/bin/env python3
"""
Production Streamlit Demo with Confidence Monitoring.

This demonstrates a production-ready Streamlit interface with the current
PlatformOrchestrator architecture, focusing on confidence scores and quality metrics.

Note: This version uses the current architecture. System-level calibration is available
through src.components.calibration.CalibrationManager (see calibration-system-spec.md).
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys
from pathlib import Path
import time
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.platform_orchestrator import PlatformOrchestrator
from src.core.interfaces import Answer, Document

# Page config
st.set_page_config(
    page_title="RAG System - Production Demo",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    margin: 0.5rem 0;
}

.confidence-high { color: #28a745; font-weight: bold; }
.confidence-medium { color: #ffc107; font-weight: bold; }
.confidence-low { color: #dc3545; font-weight: bold; }

.citation-box {
    background: #f8f9fa;
    border-left: 4px solid #007bff;
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 5px;
}
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state."""
    if 'rag_system' not in st.session_state:
        st.session_state.rag_system = None
    if 'documents_loaded' not in st.session_state:
        st.session_state.documents_loaded = False
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []


@st.cache_resource
def load_rag_system():
    """Load and cache the RAG system."""
    try:
        config_path = project_root / "config" / "default.yaml"
        if not config_path.exists():
            config_path = project_root / "config" / "test.yaml"

        orchestrator = PlatformOrchestrator(config_path)
        return orchestrator
    except Exception as e:
        st.error(f"Failed to initialize RAG system: {e}")
        return None


def format_confidence_display(confidence: float) -> str:
    """Format confidence for display with color coding."""
    percentage = confidence * 100
    if confidence >= 0.7:
        css_class = "confidence-high"
        icon = "🟢"
    elif confidence >= 0.4:
        css_class = "confidence-medium"
        icon = "🟡"
    else:
        css_class = "confidence-low"
        icon = "🔴"

    return f'<span class="{css_class}">{icon} {percentage:.1f}%</span>'


def create_confidence_gauge(confidence: float) -> go.Figure:
    """Create a confidence gauge chart."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=confidence * 100,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Confidence Score"},
        delta={'reference': 70},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 40], 'color': "lightgray"},
                {'range': [40, 70], 'color': "lightyellow"},
                {'range': [70, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    fig.update_layout(height=250, margin=dict(t=50, b=0, l=0, r=0))
    return fig


def create_history_chart(history: List[Dict[str, Any]]) -> go.Figure:
    """Create confidence history chart."""
    if not history:
        return None

    df = pd.DataFrame(history)
    fig = px.line(
        df,
        x=df.index,
        y='confidence',
        title='Confidence Score History',
        labels={'confidence': 'Confidence', 'index': 'Query Number'}
    )
    fig.add_hline(y=0.7, line_dash="dash", line_color="green", annotation_text="High Threshold")
    fig.add_hline(y=0.4, line_dash="dash", line_color="orange", annotation_text="Medium Threshold")
    fig.update_layout(height=300, yaxis_range=[0, 1])
    return fig


def main():
    """Main Streamlit application."""
    initialize_session_state()

    # Header
    st.title("🎯 Production RAG System Demo")
    st.markdown("### Confidence-Aware Question Answering")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")

        # System initialization
        if st.session_state.rag_system is None:
            with st.spinner("Initializing RAG system..."):
                st.session_state.rag_system = load_rag_system()

        if st.session_state.rag_system is None:
            st.error("Failed to initialize RAG system. Please check configuration.")
            return

        # System health
        health = st.session_state.rag_system.get_system_health()
        st.success("System Ready")
        st.info(f"Architecture: {health['architecture']}")

        # Document upload
        st.header("📄 Document Management")
        uploaded_file = st.file_uploader("Upload PDF", type=['pdf'])

        if uploaded_file and not st.session_state.documents_loaded:
            with st.spinner("Processing document..."):
                # Save uploaded file temporarily
                temp_path = Path(f"/tmp/{uploaded_file.name}")
                temp_path.write_bytes(uploaded_file.read())

                try:
                    chunk_count = st.session_state.rag_system.process_document(temp_path)
                    st.session_state.documents_loaded = True
                    st.success(f"✅ Processed {chunk_count} chunks")
                except Exception as e:
                    st.error(f"❌ Processing failed: {e}")
                finally:
                    # Clean up temp file
                    if temp_path.exists():
                        temp_path.unlink()

        elif st.session_state.documents_loaded:
            st.success("Documents indexed ✅")

        # Query settings
        st.header("🔧 Query Settings")
        top_k = st.slider("Number of sources (k)", 1, 10, 5)

        # Clear history
        if st.button("🗑️ Clear History"):
            st.session_state.query_history = []
            st.rerun()

    # Main content
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("💬 Ask Questions")

        # Query input
        query = st.text_input(
            "Enter your question:",
            placeholder="What is RISC-V?",
            key="query_input"
        )

        if st.button("🔍 Submit Query", type="primary"):
            if not st.session_state.documents_loaded:
                st.warning("⚠️ Please upload a document first")
            elif not query:
                st.warning("⚠️ Please enter a question")
            else:
                with st.spinner("Generating answer..."):
                    start_time = time.time()
                    try:
                        answer = st.session_state.rag_system.query(query, k=top_k)
                        response_time = time.time() - start_time

                        # Display answer
                        st.subheader("📝 Answer")
                        st.write(answer.text)

                        # Confidence display
                        st.markdown("### Confidence Assessment")
                        st.markdown(format_confidence_display(answer.confidence), unsafe_allow_html=True)

                        # Sources
                        st.subheader("📚 Sources")
                        for i, source_doc in enumerate(answer.sources, 1):
                            with st.expander(f"Source {i}: {source_doc.metadata.get('source', 'Unknown')}"):
                                st.markdown(f"**Page:** {source_doc.metadata.get('page', 'N/A')}")
                                st.markdown(f"**Content Preview:**")
                                content_preview = source_doc.content[:300] + "..." if len(source_doc.content) > 300 else source_doc.content
                                st.text(content_preview)

                        # Metrics
                        metric_col1, metric_col2, metric_col3 = st.columns(3)
                        with metric_col1:
                            st.metric("Response Time", f"{response_time:.2f}s")
                        with metric_col2:
                            st.metric("Sources Used", len(answer.sources))
                        with metric_col3:
                            st.metric("Confidence", f"{answer.confidence:.1%}")

                        # Add to history
                        st.session_state.query_history.append({
                            'query': query,
                            'confidence': answer.confidence,
                            'sources': len(answer.sources),
                            'time': response_time,
                            'timestamp': time.time()
                        })

                    except Exception as e:
                        st.error(f"❌ Query failed: {e}")
                        import traceback
                        with st.expander("Error details"):
                            st.code(traceback.format_exc())

    with col2:
        st.header("📊 Analytics")

        if st.session_state.query_history:
            # Latest confidence gauge
            latest = st.session_state.query_history[-1]
            st.plotly_chart(
                create_confidence_gauge(latest['confidence']),
                use_container_width=True
            )

            # History chart
            if len(st.session_state.query_history) > 1:
                st.plotly_chart(
                    create_history_chart(st.session_state.query_history),
                    use_container_width=True
                )

            # Statistics
            st.subheader("📈 Statistics")
            confidences = [q['confidence'] for q in st.session_state.query_history]
            st.metric("Average Confidence", f"{sum(confidences) / len(confidences):.1%}")
            st.metric("Total Queries", len(st.session_state.query_history))
            st.metric("High Confidence", sum(1 for c in confidences if c >= 0.7))

        else:
            st.info("No queries yet. Submit a query to see analytics.")

    # Query history
    if st.session_state.query_history:
        st.header("📜 Query History")
        history_df = pd.DataFrame(st.session_state.query_history)
        history_df['confidence'] = history_df['confidence'].apply(lambda x: f"{x:.1%}")
        history_df['time'] = history_df['time'].apply(lambda x: f"{x:.2f}s")
        st.dataframe(
            history_df[['query', 'confidence', 'sources', 'time']],
            use_container_width=True
        )

    # Footer
    st.markdown("---")
    st.markdown("""
    **Production Features:**
    - ✅ Real-time confidence monitoring
    - ✅ Source attribution
    - ✅ Performance tracking
    - ✅ Query history
    - ✅ Interactive analytics

    **Note:** System-level calibration available through `CalibrationManager`.
    See `docs/architecture/calibration-system-spec.md` for details.
    """)


if __name__ == "__main__":
    main()
