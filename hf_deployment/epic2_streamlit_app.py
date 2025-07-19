#!/usr/bin/env python3
"""
Epic 2 Enhanced RAG System - Streamlit Interface for HF Deployment

Professional web interface with Epic 2 advanced features:
- Neural reranking with cross-encoder models
- Graph-based document relationships
- Performance analytics and monitoring
- Configurable feature toggles
"""

import streamlit as st
import sys
import os
from pathlib import Path
import time
import traceback
from typing import List, Dict, Any
import json

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
from src.epic2_rag_with_generation import Epic2RAGWithGeneration

# Page configuration
st.set_page_config(
    page_title="Epic 2 Enhanced RAG Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Enhanced CSS for Epic 2 features
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #2E86AB, #A23B72);
        color: white;
        padding: 1.5rem;
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
        margin: 0.2rem;
        display: inline-block;
    }
    
    .feature-card {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #2E86AB;
    }
    
    .metric-card {
        background: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        text-align: center;
    }
    
    .citation-box {
        background-color: #e8f4f8;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
        color: #212529;
    }
    
    .epic2-citation-box {
        background-color: #e8f5e8;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
        color: #212529;
    }
    
    .answer-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #212529;
    }
    
    .epic2-answer-box {
        background: linear-gradient(135deg, #f8f9fa, #e8f5e8);
        border: 2px solid #28a745;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #212529;
    }
    
    .performance-indicator {
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin: 0.25rem;
        text-align: center;
        font-weight: bold;
    }
    
    .perf-excellent { background: #d4edda; color: #155724; }
    .perf-good { background: #fff3cd; color: #856404; }
    .perf-fair { background: #f8d7da; color: #721c24; }
    
    .component-status {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 0.2rem;
        font-size: 0.8rem;
        margin: 0.1rem;
    }
    
    .status-active { background: #d4edda; color: #155724; }
    .status-inactive { background: #f8d7da; color: #721c24; }
    .status-fallback { background: #fff3cd; color: #856404; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_epic2_rag_system():
    """Initialize Epic 2 RAG system with environment detection."""
    try:
        # Auto-detect configuration
        api_token = (
            os.getenv("HUGGINGFACE_API_TOKEN") or
            os.getenv("HF_TOKEN") or 
            os.getenv("HF_API_TOKEN")
        )
        
        use_inference_providers = os.getenv("USE_INFERENCE_PROVIDERS", "true").lower() == "true"
        use_ollama = os.getenv("USE_OLLAMA", "false").lower() == "true"
        enable_epic2 = os.getenv("ENABLE_EPIC2_FEATURES", "true").lower() == "true"
        
        # Environment detection
        is_hf_spaces = os.getenv("SPACE_ID") is not None
        
        print(f"🚀 Initializing Epic 2 RAG System", file=sys.stderr, flush=True)
        print(f"   Environment: {'HuggingFace Spaces' if is_hf_spaces else 'Local'}", file=sys.stderr, flush=True)
        print(f"   Epic 2 Features: {enable_epic2}", file=sys.stderr, flush=True)
        print(f"   API Token: {'Available' if api_token else 'Not found'}", file=sys.stderr, flush=True)
        
        # Initialize system
        rag_system = Epic2RAGWithGeneration(
            api_token=api_token,
            use_inference_providers=use_inference_providers,
            use_ollama=use_ollama,
            enable_epic2_features=enable_epic2
        )
        
        return rag_system, None
        
    except Exception as e:
        print(f"❌ Epic 2 initialization failed: {e}", file=sys.stderr, flush=True)
        return None, str(e)


def display_epic2_header():
    """Display Epic 2 enhanced header."""
    st.markdown("""
    <div class="main-header">
        <h1>🚀 Epic 2 Enhanced RAG Assistant</h1>
        <p>Advanced Technical Documentation Q&A with Neural Intelligence</p>
        <span class="epic2-badge">EPIC 2 ENABLED</span>
        <span class="epic2-badge">NEURAL RERANKING</span>
        <span class="epic2-badge">GRAPH ENHANCEMENT</span>
        <span class="epic2-badge">HF SPACES READY</span>
    </div>
    """, unsafe_allow_html=True)


def display_epic2_system_status(rag_system):
    """Display comprehensive Epic 2 system status."""
    with st.sidebar:
        st.header("🎯 Epic 2 System Status")
        
        # Get system status
        system_status = rag_system.get_system_status()
        epic2_capabilities = rag_system.get_epic2_capabilities()
        
        # Main status
        if system_status["status"] == "Online":
            st.success(f"✅ System Online")
            st.info(f"📄 {system_status['documents']} documents indexed")
            st.info(f"🏗️ Architecture: {system_status['architecture'].upper()}")
        else:
            st.error("❌ System Offline")
        
        # Epic 2 Features Status
        st.subheader("🚀 Epic 2 Features")
        
        features = {
            "Neural Reranking": epic2_capabilities.get("neural_reranking", False),
            "Graph Enhancement": epic2_capabilities.get("graph_enhancement", False),
            "Hybrid Search": epic2_capabilities.get("hybrid_search", False),
            "Analytics": epic2_capabilities.get("analytics_tracking", False)
        }
        
        for feature, enabled in features.items():
            status_class = "status-active" if enabled else "status-inactive"
            icon = "✅" if enabled else "❌"
            st.markdown(f"""
            <div class="component-status {status_class}">
                {icon} {feature}
            </div>
            """, unsafe_allow_html=True)
        
        # Backend Information
        st.subheader("🤖 LLM Backend")
        backend_info = system_status.get("backend_info", {})
        
        if backend_info.get("using_inference_providers"):
            st.markdown("🚀 **Inference Providers API**")
            st.markdown("⚡ **Performance**: 2-5s responses")
        elif backend_info.get("using_ollama"):
            st.markdown("🦙 **Local Ollama**")
            st.markdown("🏠 **Mode**: Privacy-first local")
        else:
            st.markdown("🤗 **Classic HuggingFace API**")
            st.markdown("📊 **Mode**: Traditional API")
        
        st.markdown(f"**Model**: {backend_info.get('model_name', 'Unknown')}")
        
        # Performance Analytics (if available)
        if "analytics" in system_status:
            analytics = system_status["analytics"]
            if analytics["queries_processed"] > 0:
                st.subheader("📊 Performance Analytics")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Queries", analytics["queries_processed"])
                    st.metric("Epic 2 Queries", analytics["epic2_queries"])
                
                with col2:
                    avg_time = analytics["total_response_time"] / analytics["queries_processed"] * 1000
                    st.metric("Avg Response", f"{avg_time:.0f}ms")
                    epic2_ratio = analytics["epic2_queries"] / analytics["queries_processed"] * 100
                    st.metric("Epic 2 Usage", f"{epic2_ratio:.0f}%")


def handle_epic2_document_upload(rag_system):
    """Handle document upload with Epic 2 indexing."""
    st.header("📄 Document Management")
    
    uploaded_file = st.file_uploader(
        "Upload PDF Document",
        type="pdf",
        help="Upload technical documentation for Epic 2 enhanced processing"
    )
    
    if uploaded_file is not None:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            epic2_enabled = st.checkbox(
                "Enable Epic 2 Features", 
                value=True,
                help="Use neural reranking and graph enhancement during indexing"
            )
        
        with col2:
            if st.button("🚀 Index with Epic 2", type="primary"):
                try:
                    with st.spinner("Processing with Epic 2 features..."):
                        # Save uploaded file
                        temp_path = Path(f"/tmp/{uploaded_file.name}")
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getvalue())
                        
                        # Index with Epic 2
                        start_time = time.time()
                        chunk_count = rag_system.index_document(temp_path)
                        processing_time = time.time() - start_time
                        
                        # Clean up
                        temp_path.unlink()
                        
                        # Success message
                        st.markdown(f"""
                        <div class="feature-card">
                            ✅ <strong>Epic 2 Indexing Complete!</strong><br>
                            📊 {chunk_count} chunks processed in {processing_time:.2f}s<br>
                            🚀 Neural reranking and graph features ready<br>
                            📄 Ready for advanced queries
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Epic 2 indexing failed: {str(e)}")


def handle_epic2_query_interface(rag_system):
    """Handle Epic 2 enhanced query interface."""
    st.header("🧠 Epic 2 Intelligent Query")
    
    # Check system readiness
    if not rag_system.chunks:
        st.warning("⚠️ Please upload and index a document first to experience Epic 2 features.")
        return
    
    # Query input with Epic 2 options
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "Ask your question:",
            placeholder="e.g., How does RISC-V handle atomic operations?",
            help="Epic 2 will enhance your query with neural intelligence"
        )
    
    with col2:
        epic2_mode = st.selectbox(
            "Query Mode:",
            ["🚀 Epic 2 Enhanced", "📚 Basic RAG"],
            help="Choose between Epic 2 advanced features or basic retrieval"
        )
    
    # Epic 2 Advanced Options
    with st.expander("🔧 Epic 2 Advanced Options"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            use_neural_reranking = st.checkbox(
                "Neural Reranking",
                value=True,
                help="Use cross-encoder models for precision"
            )
            
            use_graph_enhancement = st.checkbox(
                "Graph Enhancement",
                value=True,
                help="Leverage document relationships"
            )
        
        with col2:
            top_k = st.slider("Results Count", 3, 15, 8)
            similarity_threshold = st.slider("Quality Threshold", 0.1, 0.8, 0.3)
        
        with col3:
            return_context = st.checkbox("Show Context", value=False)
            use_hybrid = st.checkbox("Hybrid Search", value=True)
    
    # Process query
    if query and st.button("🚀 Process with Epic 2", type="primary"):
        try:
            # Determine Epic 2 usage
            use_epic2_features = "Epic 2" in epic2_mode
            
            # Show processing indicator
            processing_text = "🧠 Epic 2 Processing: Neural reranking + Graph analysis..." if use_epic2_features else "📚 Basic processing..."
            
            with st.spinner(processing_text):
                start_time = time.time()
                
                result = rag_system.query_with_answer(
                    question=query,
                    top_k=top_k,
                    use_hybrid=use_hybrid,
                    return_context=return_context,
                    similarity_threshold=similarity_threshold,
                    use_epic2_features=use_epic2_features
                )
                
                total_time = time.time() - start_time
            
            # Display Epic 2 enhanced results
            display_epic2_results(result, total_time, use_epic2_features)
            
        except Exception as e:
            st.error(f"Epic 2 query processing failed: {str(e)}")
            with st.expander("🔍 Technical Details"):
                st.code(traceback.format_exc())


def display_epic2_results(result: Dict[str, Any], total_time: float, epic2_used: bool):
    """Display Epic 2 enhanced results."""
    
    # Determine result styling based on Epic 2 usage
    answer_class = "epic2-answer-box" if epic2_used else "answer-box"
    citation_class = "epic2-citation-box" if epic2_used else "citation-box"
    
    # Main answer with Epic 2 styling
    epic2_indicator = "🚀 **Epic 2 Enhanced Answer**" if epic2_used else "📚 **Basic RAG Answer**"
    
    st.markdown(f"""
    <div class="{answer_class}">
        {epic2_indicator}<br><br>
        {result['answer']}
    </div>
    """, unsafe_allow_html=True)
    
    # Performance metrics with Epic 2 breakdown
    st.subheader("⚡ Performance Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        confidence_color = "🟢" if result["confidence"] > 0.7 else "🟡" if result["confidence"] > 0.4 else "🔴"
        st.metric("Confidence", f"{result['confidence']:.1%}", delta=confidence_color)
    
    with col2:
        st.metric("Total Time", f"{total_time*1000:.0f}ms")
    
    with col3:
        st.metric("Sources Found", len(result["citations"]))
    
    with col4:
        method = result.get("retrieval_stats", {}).get("method", "unknown")
        st.metric("Method", method.replace("_", " ").title())
    
    # Epic 2 specific performance breakdown
    if epic2_used and "epic2_metadata" in result:
        epic2_meta = result["epic2_metadata"]
        
        st.subheader("🚀 Epic 2 Performance Breakdown")
        
        if "component_times" in epic2_meta:
            times = epic2_meta["component_times"]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                retrieval_time = times.get("retrieval", 0)
                perf_class = "perf-excellent" if retrieval_time < 500 else "perf-good" if retrieval_time < 1000 else "perf-fair"
                st.markdown(f"""
                <div class="performance-indicator {perf_class}">
                    🔍 Retrieval: {retrieval_time:.0f}ms
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                generation_time = times.get("generation", 0)
                perf_class = "perf-excellent" if generation_time < 2000 else "perf-good" if generation_time < 5000 else "perf-fair"
                st.markdown(f"""
                <div class="performance-indicator {perf_class}">
                    🤖 Generation: {generation_time:.0f}ms
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                total_epic2_time = epic2_meta.get("total_processing_time_ms", 0)
                perf_class = "perf-excellent" if total_epic2_time < 3000 else "perf-good" if total_epic2_time < 6000 else "perf-fair"
                st.markdown(f"""
                <div class="performance-indicator {perf_class}">
                    🚀 Total Epic 2: {total_epic2_time:.0f}ms
                </div>
                """, unsafe_allow_html=True)
        
        # Epic 2 features used
        if "advanced_features_active" in epic2_meta and epic2_meta["advanced_features_active"]:
            st.info("✨ **Epic 2 Features Active**: Neural reranking, graph enhancement, and hybrid search were used to generate this response.")
    
    # Citations with Epic 2 enhancements
    if result["citations"]:
        st.subheader("📚 Enhanced Source Citations")
        
        for i, citation in enumerate(result["citations"], 1):
            epic2_enhanced = citation.get("epic2_enhanced", False)
            enhancement_indicator = "🚀 Epic 2 Enhanced" if epic2_enhanced else "📚 Basic"
            
            st.markdown(f"""
            <div class="{citation_class}">
                <strong>{i}. {citation['source']}</strong> (Page {citation['page']}) - {enhancement_indicator}<br>
                <small>Relevance: {citation['relevance']:.1%}</small><br>
                <em>"{citation['snippet']}"</em>
            </div>
            """, unsafe_allow_html=True)
    
    # Context display (if requested)
    if "context" in result and result["context"]:
        st.subheader("🔍 Retrieved Context Details")
        
        for i, chunk in enumerate(result["context"], 1):
            epic2_info = ""
            if chunk.get("epic2_enhanced"):
                epic2_details = []
                if chunk.get("graph_connections", 0) > 0:
                    epic2_details.append(f"{chunk['graph_connections']} graph connections")
                if chunk.get("related_entities"):
                    epic2_details.append(f"{len(chunk['related_entities'])} entities")
                
                if epic2_details:
                    epic2_info = f" - 🚀 Epic 2: {', '.join(epic2_details)}"
            
            with st.expander(f"Context {i}: {chunk.get('source', 'Unknown')} (Score: {chunk.get('score', 0):.3f}){epic2_info}"):
                st.write(f"**Text**: {chunk.get('text', '')[:500]}...")
                if chunk.get("related_entities"):
                    st.write(f"**Entities**: {', '.join(chunk['related_entities'][:5])}")


def display_epic2_sample_queries():
    """Display Epic 2 optimized sample queries."""
    st.header("💡 Epic 2 Sample Queries")
    
    st.markdown("These queries are optimized to showcase Epic 2's advanced capabilities:")
    
    sample_queries = [
        ("🧠 Neural Precision", "What is RISC-V and what are its main architectural advantages?"),
        ("🕸️ Graph Relations", "How do atomic operations relate to memory ordering in RISC-V?"),
        ("🔍 Deep Analysis", "Compare RV32I and RV64I instruction sets with implementation details"),
        ("📊 Technical Deep-dive", "Explain RISC-V privileged architecture and security features"),
        ("🚀 Complex Reasoning", "How does RISC-V vector extension work with memory constraints?"),
    ]
    
    col1, col2 = st.columns(2)
    
    for i, (category, query) in enumerate(sample_queries):
        col = col1 if i % 2 == 0 else col2
        
        with col:
            if st.button(f"{category}: {query[:40]}...", key=f"epic2_sample_{i}"):
                st.session_state["epic2_query"] = query
                st.rerun()


def main():
    """Main Epic 2 Streamlit application."""
    
    # Initialize session state
    if "rag_system" not in st.session_state:
        st.session_state["rag_system"] = None
        st.session_state["init_error"] = None
    
    # Display Epic 2 header
    display_epic2_header()
    
    # Initialize Epic 2 system
    if st.session_state["rag_system"] is None:
        with st.spinner("🚀 Initializing Epic 2 RAG System..."):
            rag_system, error = initialize_epic2_rag_system()
            st.session_state["rag_system"] = rag_system
            st.session_state["init_error"] = error
    
    rag_system = st.session_state["rag_system"]
    init_error = st.session_state["init_error"]
    
    # Handle initialization errors
    if init_error:
        st.error(f"❌ Epic 2 initialization failed: {init_error}")
        st.info("💡 **Troubleshooting**: Ensure HF_TOKEN is set for API access")
        return
    
    if rag_system is None:
        st.error("❌ Failed to initialize Epic 2 system")
        return
    
    # Display Epic 2 system status
    display_epic2_system_status(rag_system)
    
    # Main interface with Epic 2 features
    tab1, tab2, tab3, tab4 = st.tabs(
        ["🧠 Epic 2 Query", "📄 Document Upload", "💡 Sample Queries", "📊 System Analytics"]
    )
    
    with tab1:
        # Handle sample query selection
        if "epic2_query" in st.session_state:
            st.text_input(
                "Ask your question:",
                value=st.session_state["epic2_query"],
                key="main_epic2_query"
            )
            del st.session_state["epic2_query"]
        
        handle_epic2_query_interface(rag_system)
    
    with tab2:
        handle_epic2_document_upload(rag_system)
        
        # Quick test document option
        st.subheader("📖 Test with Sample Document")
        test_pdf_path = Path("data/test/riscv-base-instructions.pdf")
        
        if test_pdf_path.exists():
            if st.button("🚀 Load RISC-V Test Document with Epic 2"):
                try:
                    with st.spinner("🧠 Processing with Epic 2 features..."):
                        chunk_count = rag_system.index_document(test_pdf_path)
                        st.success(f"✅ Epic 2 processing complete! {chunk_count} chunks with neural enhancements.")
                        st.rerun()
                except Exception as e:
                    st.error(f"Epic 2 processing failed: {e}")
        else:
            st.info("Test document not found. Upload your own PDF to experience Epic 2 features.")
    
    with tab3:
        display_epic2_sample_queries()
    
    with tab4:
        if rag_system:
            system_status = rag_system.get_system_status()
            
            st.subheader("📊 Epic 2 System Analytics")
            
            if "analytics" in system_status:
                analytics = system_status["analytics"]
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Queries", analytics["queries_processed"])
                
                with col2:
                    st.metric("Epic 2 Queries", analytics["epic2_queries"])
                
                with col3:
                    if analytics["queries_processed"] > 0:
                        avg_time = analytics["total_response_time"] / analytics["queries_processed"]
                        st.metric("Avg Response Time", f"{avg_time:.2f}s")
                    else:
                        st.metric("Avg Response Time", "N/A")
                
                with col4:
                    epic2_ratio = (analytics["epic2_queries"] / max(analytics["queries_processed"], 1)) * 100
                    st.metric("Epic 2 Usage", f"{epic2_ratio:.0f}%")
                
                # Component performance
                if "component_performance" in analytics:
                    st.subheader("🔧 Component Performance")
                    comp_perf = analytics["component_performance"]
                    
                    performance_data = {
                        "Retrieval": comp_perf.get("retrieval", 0),
                        "Neural Reranking": comp_perf.get("neural_reranking", 0),
                        "Graph Enhancement": comp_perf.get("graph_enhancement", 0),
                        "Generation": comp_perf.get("generation", 0)
                    }
                    
                    for component, time_spent in performance_data.items():
                        if time_spent > 0:
                            st.metric(f"{component} Time", f"{time_spent:.3f}s")
            else:
                st.info("📊 Process some queries to see analytics data")
    
    # Epic 2 Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        🚀 <strong>Epic 2 Enhanced RAG Assistant</strong> | Neural Intelligence + Graph Relationships<br>
        Powered by HuggingFace API • Cross-Encoder Reranking • Document Graph Analysis<br>
        Built for Swiss Tech Market | Production-Ready Architecture
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()