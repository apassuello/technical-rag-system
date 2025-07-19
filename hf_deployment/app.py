"""
Epic 2 Interactive Streamlit Demo
=================================

Professional demonstration of the Epic 2 Enhanced RAG System capabilities
showcasing advanced hybrid retrieval, neural reranking, and graph enhancement.

Target: Swiss Tech Market ML Engineer Portfolio
System: Epic 2 Enhanced RAG with 100% modular architecture compliance
Data: Complete RISC-V technical documentation corpus
"""

import streamlit as st
import sys
import os
from pathlib import Path
import time
import logging
from typing import Dict, Any, List

# Add demo utils to path
sys.path.append(str(Path(__file__).parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import system integration
try:
    from demo.utils.system_integration import get_system_manager
    from demo.utils.analytics_dashboard import analytics_dashboard
    system_manager = get_system_manager()
except ImportError as e:
    st.error(f"Failed to import system integration: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Epic 2 Enhanced RAG Demo",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional appearance
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #2E86AB, #A23B72);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .epic2-badge {
        background: #28a745;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .model-badge {
        background: #17a2b8;
        color: white;
        padding: 0.2rem 0.4rem;
        border-radius: 0.2rem;
        font-size: 0.7rem;
        margin: 0.1rem;
        display: inline-block;
    }
    
    .status-online {
        color: #28a745;
        font-weight: bold;
    }
    
    .status-processing {
        color: #ffc107;
        font-weight: bold;
    }
    
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2E86AB;
        margin: 0.5rem 0;
    }
    
    .stage-indicator {
        padding: 0.5rem;
        margin: 0.25rem;
        border-radius: 0.25rem;
        text-align: center;
        font-weight: bold;
    }
    
    .stage-complete { background: #d4edda; color: #155724; }
    .stage-active { background: #fff3cd; color: #856404; }
    .stage-pending { background: #f8d7da; color: #721c24; }
    
    .performance-excellent { background: #d4edda; color: #155724; }
    .performance-good { background: #fff3cd; color: #856404; }
    .performance-needs-improvement { background: #f8d7da; color: #721c24; }
</style>
""", unsafe_allow_html=True)


def display_header():
    """Display the main header with Epic 2 branding"""
    st.markdown("""
    <div class="main-header">
        <h1>🚀 Epic 2 Enhanced RAG System</h1>
        <p>Neural Intelligence meets Graph Enhancement • Professional ML Portfolio Demo</p>
        <span class="epic2-badge">EPIC 2 ENABLED</span>
        <span class="epic2-badge">NEURAL RERANKING</span>
        <span class="epic2-badge">GRAPH ENHANCEMENT</span>
        <span class="epic2-badge">HYBRID SEARCH</span>
    </div>
    """, unsafe_allow_html=True)


def display_system_status():
    """Display comprehensive system status in sidebar"""
    with st.sidebar:
        st.header("🎯 System Status")
        
        # Get system status from manager
        if system_manager.is_initialized:
            status = system_manager.get_system_status()
            backend_info = system_manager.get_llm_backend_info()
            
            # Main status
            st.markdown('<p class="status-online">✅ System Online</p>', unsafe_allow_html=True)
            st.info(f"📄 {status.get('documents', 0)} documents indexed")
            st.info(f"🏗️ Architecture: {status.get('architecture', 'Unknown').upper()}")
            
            # LLM Backend info
            st.subheader("🤖 LLM Backend")
            if backend_info['using_hf_api']:
                st.markdown("🤗 **HuggingFace API**")
                st.markdown(f"⚡ **Model**: {backend_info['model_name']}")
                if backend_info.get('api_available'):
                    st.success("✅ API Available")
                else:
                    st.warning("⚠️ API Limited")
            else:
                st.markdown("🦙 **Local Ollama**")
                st.markdown(f"🏠 **Model**: {backend_info['model_name']}")
                if backend_info.get('ollama_available'):
                    st.success("✅ Ollama Connected")
                else:
                    st.error("❌ Ollama Offline")
            
            # Performance metrics
            if 'performance' in status:
                perf = status['performance']
                st.subheader("📊 Performance")
                
                # Query processing time
                avg_time = perf.get('average_query_time', 0)
                if avg_time < 2:
                    time_class = "performance-excellent"
                    time_icon = "🟢"
                elif avg_time < 5:
                    time_class = "performance-good"  
                    time_icon = "🟡"
                else:
                    time_class = "performance-needs-improvement"
                    time_icon = "🔴"
                
                st.markdown(f"""
                <div class="stage-indicator {time_class}">
                    {time_icon} Avg Query: {avg_time:.1f}s
                </div>
                """, unsafe_allow_html=True)
                
                # Component status
                components = perf.get('components', {})
                st.write("**Component Status:**")
                for component, active in components.items():
                    icon = "✅" if active else "❌"
                    st.write(f"{icon} {component.replace('_', ' ').title()}")
            
        else:
            st.markdown('<p class="status-processing">⚡ Initializing...</p>', unsafe_allow_html=True)
            st.info("Loading Epic 2 system components")


def handle_document_upload():
    """Handle document upload and processing"""
    st.header("📄 Document Management")
    
    # Document upload
    uploaded_file = st.file_uploader(
        "Upload PDF Document",
        type="pdf",
        help="Upload technical documentation for Epic 2 processing"
    )
    
    if uploaded_file is not None:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"Selected: {uploaded_file.name} ({uploaded_file.size:,} bytes)")
        
        with col2:
            if st.button("🚀 Process Document", type="primary"):
                try:
                    with st.spinner("Processing with Epic 2 features..."):
                        # Save uploaded file temporarily
                        temp_path = Path(f"/tmp/{uploaded_file.name}")
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getvalue())
                        
                        # Process document
                        start_time = time.time()
                        result = system_manager.process_document(temp_path)
                        processing_time = time.time() - start_time
                        
                        # Clean up
                        temp_path.unlink()
                        
                        # Display results
                        st.success(f"✅ Document processed successfully!")
                        st.info(f"📊 {result['chunks']} chunks created in {processing_time:.2f}s")
                        st.info(f"🚀 Epic 2 features: Neural reranking + Graph enhancement active")
                        
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Processing failed: {e}")
    
    # Quick load test documents
    st.subheader("📚 Test Documents")
    
    test_docs = [
        ("RISC-V Base Instructions", "data/test/riscv-base-instructions.pdf"),
        ("RISC-V Quick Reference", "data/test/riscv-card.pdf"),
        ("GMLP Guiding Principles", "data/test/GMLP_Guiding_Principles.pdf")
    ]
    
    for doc_name, doc_path in test_docs:
        doc_file = Path(doc_path)
        if doc_file.exists():
            if st.button(f"📖 Load {doc_name}", key=f"load_{doc_name}"):
                try:
                    with st.spinner(f"Loading {doc_name} with Epic 2..."):
                        result = system_manager.process_document(doc_file)
                        st.success(f"✅ {doc_name} loaded! {result['chunks']} chunks processed.")
                        st.rerun()
                except Exception as e:
                    st.error(f"Failed to load {doc_name}: {e}")
        else:
            st.info(f"📄 {doc_name}: File not found ({doc_path})")


def handle_query_interface():
    """Handle the main query interface"""
    st.header("🧠 Epic 2 Intelligent Query")
    
    # Check if system is ready
    if not system_manager.is_initialized:
        st.warning("⚠️ System is still initializing. Please wait...")
        return
    
    status = system_manager.get_system_status()
    if status.get('documents', 0) == 0:
        st.warning("⚠️ Please upload and process a document first to enable querying.")
        return
    
    # Query input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "Ask your question:",
            placeholder="e.g., How does RISC-V handle atomic operations?",
            help="Epic 2 will enhance your query with neural intelligence and graph relationships"
        )
    
    with col2:
        mode = st.selectbox(
            "Processing Mode:",
            ["🚀 Epic 2 Enhanced", "📚 Basic RAG"],
            help="Choose between Epic 2 advanced features or basic retrieval"
        )
    
    # Advanced options
    with st.expander("🔧 Advanced Options"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            top_k = st.slider("Results Count", 3, 20, 8)
            use_reranking = st.checkbox("Neural Reranking", value=True)
            
        with col2:
            use_graph = st.checkbox("Graph Enhancement", value=True)
            similarity_threshold = st.slider("Quality Threshold", 0.0, 1.0, 0.3)
            
        with col3:
            include_context = st.checkbox("Show Context", value=False)
            use_hybrid = st.checkbox("Hybrid Search", value=True)
    
    # Process query
    if query and st.button("🚀 Process Query", type="primary"):
        try:
            use_epic2 = "Epic 2" in mode
            
            with st.spinner("🧠 Epic 2 Processing: Neural reranking + Graph analysis..." if use_epic2 else "📚 Basic processing..."):
                start_time = time.time()
                
                result = system_manager.query_with_analytics(
                    question=query,
                    top_k=top_k,
                    use_epic2=use_epic2,
                    use_reranking=use_reranking,
                    use_graph=use_graph,
                    similarity_threshold=similarity_threshold,
                    include_context=include_context,
                    use_hybrid=use_hybrid
                )
                
                total_time = time.time() - start_time
            
            # Display results
            display_query_results(result, total_time, use_epic2)
            
        except Exception as e:
            st.error(f"Query processing failed: {e}")
            with st.expander("🔍 Technical Details"):
                import traceback
                st.code(traceback.format_exc())


def display_query_results(result: Dict[str, Any], total_time: float, epic2_used: bool):
    """Display query results with Epic 2 enhancements"""
    
    # Main answer
    answer_style = "performance-excellent" if epic2_used else "metric-card"
    mode_indicator = "🚀 **Epic 2 Enhanced Answer**" if epic2_used else "📚 **Basic RAG Answer**"
    
    st.markdown(f"""
    <div class="{answer_style}" style="padding: 1.5rem; margin: 1rem 0;">
        {mode_indicator}<br><br>
        {result['answer']}
    </div>
    """, unsafe_allow_html=True)
    
    # Performance metrics
    st.subheader("⚡ Performance Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        confidence = result.get('confidence', 0)
        conf_color = "🟢" if confidence > 0.7 else "🟡" if confidence > 0.4 else "🔴"
        st.metric("Confidence", f"{confidence:.1%}", delta=conf_color)
    
    with col2:
        st.metric("Total Time", f"{total_time*1000:.0f}ms")
    
    with col3:
        citations_count = len(result.get('citations', []))
        st.metric("Sources Found", citations_count)
    
    with col4:
        method = result.get('retrieval_method', 'unknown')
        st.metric("Method", method.replace('_', ' ').title())
    
    # Epic 2 specific performance breakdown
    if epic2_used and 'epic2_analytics' in result:
        analytics = result['epic2_analytics']
        
        st.subheader("🚀 Epic 2 Performance Breakdown")
        
        if 'component_times' in analytics:
            times = analytics['component_times']
            
            cols = st.columns(len(times))
            for i, (component, time_ms) in enumerate(times.items()):
                with cols[i]:
                    if time_ms < 500:
                        perf_class = "performance-excellent"
                        icon = "🟢"
                    elif time_ms < 1500:
                        perf_class = "performance-good"
                        icon = "🟡"
                    else:
                        perf_class = "performance-needs-improvement"
                        icon = "🔴"
                    
                    st.markdown(f"""
                    <div class="stage-indicator {perf_class}">
                        {icon} {component.replace('_', ' ').title()}<br>{time_ms:.0f}ms
                    </div>
                    """, unsafe_allow_html=True)
        
        # Epic 2 features status
        if analytics.get('epic2_features_used'):
            st.info("✨ **Epic 2 Features Active**: Neural reranking, graph enhancement, and hybrid search optimized this response.")
    
    # Citations
    if result.get('citations'):
        st.subheader("📚 Source Citations")
        
        for i, citation in enumerate(result['citations'], 1):
            epic2_enhanced = citation.get('epic2_enhanced', False)
            enhancement_text = "🚀 Epic 2 Enhanced" if epic2_enhanced else "📚 Standard"
            
            citation_style = "performance-excellent" if epic2_enhanced else "metric-card"
            
            st.markdown(f"""
            <div class="{citation_style}" style="margin: 0.5rem 0;">
                <strong>{i}. {citation['source']}</strong> (Page {citation['page']}) - {enhancement_text}<br>
                <small>Relevance: {citation['relevance']:.1%}</small><br>
                <em>"{citation['snippet']}"</em>
            </div>
            """, unsafe_allow_html=True)
    
    # Context (if requested)
    if 'context' in result and result['context']:
        st.subheader("🔍 Retrieved Context")
        
        for i, chunk in enumerate(result['context'], 1):
            epic2_info = ""
            if chunk.get('epic2_enhanced'):
                epic2_details = []
                if chunk.get('graph_connections', 0) > 0:
                    epic2_details.append(f"{chunk['graph_connections']} graph connections")
                if chunk.get('related_entities'):
                    epic2_details.append(f"{len(chunk['related_entities'])} entities")
                
                if epic2_details:
                    epic2_info = f" - 🚀 Epic 2: {', '.join(epic2_details)}"
            
            with st.expander(f"Context {i}: {chunk.get('source', 'Unknown')} (Score: {chunk.get('score', 0):.3f}){epic2_info}"):
                st.write(f"**Text**: {chunk.get('text', '')[:800]}...")
                if chunk.get('related_entities'):
                    st.write(f"**Entities**: {', '.join(chunk['related_entities'][:8])}")


def display_sample_queries():
    """Display sample queries optimized for Epic 2"""
    st.header("💡 Sample Queries")
    
    st.markdown("These queries showcase Epic 2's advanced capabilities:")
    
    samples = [
        ("🧠 Neural Precision", "What is RISC-V and what are its main architectural advantages?"),
        ("🕸️ Graph Relations", "How do atomic operations relate to memory ordering in RISC-V?"),
        ("🔍 Deep Analysis", "Compare RV32I and RV64I instruction sets with implementation details"),
        ("📊 Technical Deep-dive", "Explain RISC-V privileged architecture and security features"),
        ("🚀 Complex Reasoning", "How does RISC-V vector extension work with memory constraints?"),
    ]
    
    col1, col2 = st.columns(2)
    
    for i, (category, query) in enumerate(samples):
        col = col1 if i % 2 == 0 else col2
        
        with col:
            if st.button(f"{category}: {query[:35]}...", key=f"sample_{i}"):
                st.session_state["sample_query"] = query
                st.rerun()


def main():
    """Main Streamlit application"""
    
    # Display header
    display_header()
    
    # Display system status
    display_system_status()
    
    # Initialize system
    if not system_manager.is_initialized:
        with st.spinner("🚀 Initializing Epic 2 system..."):
            try:
                system_manager.initialize_system()
                st.rerun()
            except Exception as e:
                st.error(f"Failed to initialize Epic 2 system: {e}")
                st.info("💡 **Troubleshooting**: Check that all dependencies are installed and models are accessible")
                return
    
    # Main interface
    tab1, tab2, tab3, tab4 = st.tabs(
        ["🧠 Query", "📄 Documents", "💡 Samples", "📊 Analytics"]
    )
    
    with tab1:
        # Handle sample query selection
        if "sample_query" in st.session_state:
            st.text_input(
                "Ask your question:",
                value=st.session_state["sample_query"],
                key="main_query_input"
            )
            del st.session_state["sample_query"]
        
        handle_query_interface()
    
    with tab2:
        handle_document_upload()
    
    with tab3:
        display_sample_queries()
    
    with tab4:
        if system_manager.is_initialized:
            analytics_dashboard(system_manager)
        else:
            st.info("📊 Analytics will be available after system initialization")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        🚀 <strong>Epic 2 Enhanced RAG System</strong> | Neural Intelligence + Graph Enhancement<br>
        Swiss Engineering Standards • Production-Ready Architecture<br>
        Built for ML Engineer Portfolio Demonstration
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()