#!/usr/bin/env python3
"""
Technical Documentation RAG System - Streamlit Interface

A professional web interface for the RAG system with answer generation,
optimized for technical documentation Q&A.
"""

import os
# Set environment variables before importing streamlit
os.environ['HOME'] = '/app'
os.environ['STREAMLIT_CONFIG_DIR'] = '/app/.streamlit'
os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

import streamlit as st
import sys
from pathlib import Path
import time
import traceback
from typing import List, Dict, Any
import json

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import directly since we're in the project directory
sys.path.insert(0, str(Path(__file__).parent))
from src.rag_with_generation import RAGWithGeneration


# Page configuration
st.set_page_config(
    page_title="Technical Documentation RAG Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional appearance
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, #f0f8ff, #e6f3ff);
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    
    .system-stats {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    
    .error-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
    
    .metrics-container {
        display: flex;
        justify-content: space-around;
        margin: 1rem 0;
    }
    
    .metric-box {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        min-width: 120px;
    }
    
    .citation-box {
        background-color: #e8f4fd;
        padding: 0.8rem;
        border-radius: 6px;
        border-left: 3px solid #2196F3;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
    
    .sample-query {
        background-color: #f0f8ff;
        padding: 0.8rem;
        border-radius: 6px;
        margin: 0.5rem 0;
        cursor: pointer;
        border-left: 3px solid #4CAF50;
    }
    
    .sample-query:hover {
        background-color: #e6f3ff;
    }
</style>
""", unsafe_allow_html=True)


def initialize_rag_system(api_token=None, model_name=None):
    """Initialize the RAG system with HuggingFace API."""
    try:
        # Check for token in environment first
        import os
        token = api_token or os.getenv("HUGGINGFACE_API_TOKEN")
        
        # Use selected model or default based on Pro vs Free tier
        if not model_name:
            if token:
                model_name = "mistralai/Mistral-7B-Instruct-v0.2"  # Pro: Best for technical Q&A
            else:
                model_name = "gpt2-medium"  # Free tier: Best available
        
        rag_system = RAGWithGeneration(
            model_name=model_name,
            api_token=token,  # Use provided token or env variable
            temperature=0.3,
            max_tokens=512
        )
        return rag_system, None
    except Exception as e:
        error_msg = f"RAG system initialization failed: {str(e)}"
        return None, error_msg


def display_header():
    """Display application header with branding."""
    st.markdown("""
    <div class="main-header">
        🔍 Technical Documentation RAG Assistant
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem; color: #666;">
        Advanced hybrid retrieval with local LLM answer generation<br>
        <strong>Built for Swiss ML Engineering Excellence</strong>
    </div>
    """, unsafe_allow_html=True)


def display_system_status(rag_system):
    """Display system status and metrics in sidebar."""
    with st.sidebar:
        st.markdown("### 🏥 System Status")
        
        # Basic system info
        chunk_count = len(rag_system.chunks) if rag_system.chunks else 0
        source_count = len(set(chunk.get('source', '') for chunk in rag_system.chunks)) if rag_system.chunks else 0
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📄 Documents", source_count)
        with col2:
            st.metric("🧩 Chunks", chunk_count)
        
        # Model info
        st.markdown("### 🤖 Model Status")
        if rag_system.answer_generator.api_token:
            st.success("✅ HuggingFace API (Authenticated)")
        else:
            st.info("ℹ️ HuggingFace API (Free Tier)")
        st.info("🔍 Hybrid Search Active")
        
        # API Configuration
        st.markdown("### ⚙️ API Configuration")
        with st.expander("HuggingFace Configuration"):
            st.markdown("""
            **Using HF Token:**
            1. Set as Space Secret: `HUGGINGFACE_API_TOKEN`
            2. Or paste token below
            
            **Benefits of token:**
            - Higher rate limits
            - Better models (Llama 2, Falcon)
            - Faster response times
            """)
            
            token_input = st.text_input(
                "HF Token", 
                type="password", 
                help="Your HuggingFace API token",
                key="hf_token_input"
            )
            
            # Model selection - Pro tier models from your guide
            if rag_system.answer_generator.api_token:
                model_options = [
                    "mistralai/Mistral-7B-Instruct-v0.2",    # Best for technical Q&A
                    "codellama/CodeLlama-7b-Instruct-hf",    # Perfect for code docs
                    "meta-llama/Llama-2-7b-chat-hf",        # Well-rounded
                    "codellama/CodeLlama-13b-Instruct-hf",   # Higher quality (slower)
                    "meta-llama/Llama-2-13b-chat-hf",       # Better reasoning
                    "microsoft/DialoGPT-large",              # Conversational fallback
                    "tiiuae/falcon-7b-instruct",             # Efficient option
                    "gpt2-medium"                            # Emergency fallback
                ]
            else:
                model_options = [
                    "gpt2-medium",  # Best bet for free tier  
                    "gpt2",         # Always available
                    "distilgpt2"    # Fastest option
                ]
            
            current_model = rag_system.answer_generator.model_name
            selected_model = st.selectbox(
                "Model",
                model_options,
                index=model_options.index(current_model) if current_model in model_options else 0,
                key="model_select"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Update Configuration"):
                    if token_input or selected_model != current_model:
                        # Reinitialize with new settings
                        st.session_state['api_token'] = token_input if token_input else st.session_state.get('api_token')
                        st.session_state['selected_model'] = selected_model
                        st.session_state['rag_system'] = None
                        st.rerun()
            
            with col2:
                if st.button("Test Pro Models"):
                    # Test all Pro models from your guide
                    pro_models = [
                        "mistralai/Mistral-7B-Instruct-v0.2",
                        "codellama/CodeLlama-7b-Instruct-hf", 
                        "meta-llama/Llama-2-7b-chat-hf",
                        "codellama/CodeLlama-13b-Instruct-hf",
                        "meta-llama/Llama-2-13b-chat-hf",
                        "microsoft/DialoGPT-large",
                        "tiiuae/falcon-7b-instruct"
                    ]
                    
                    test_token = token_input if token_input else st.session_state.get('api_token')
                    
                    with st.spinner("Testing Pro models..."):
                        results = {}
                        for model in pro_models:
                            try:
                                import requests
                                import os
                                token = test_token or os.getenv("HUGGINGFACE_API_TOKEN")
                                
                                headers = {"Content-Type": "application/json"}
                                if token:
                                    headers["Authorization"] = f"Bearer {token}"
                                
                                response = requests.post(
                                    f"https://api-inference.huggingface.co/models/{model}",
                                    headers=headers,
                                    json={"inputs": "What is RISC-V?", "parameters": {"max_new_tokens": 50}},
                                    timeout=15
                                )
                                
                                if response.status_code == 200:
                                    results[model] = "✅ Available"
                                elif response.status_code == 404:
                                    results[model] = "❌ Not found"
                                elif response.status_code == 503:
                                    results[model] = "⏳ Loading"
                                else:
                                    results[model] = f"❌ Error {response.status_code}"
                                    
                            except Exception as e:
                                results[model] = f"❌ Failed: {str(e)[:30]}"
                        
                        # Display results
                        st.subheader("🧪 Pro Model Test Results:")
                        for model, status in results.items():
                            model_short = model.split('/')[-1]
                            st.write(f"**{model_short}**: {status}")
        
        if chunk_count > 0:
            st.markdown("### 📊 Index Statistics")
            st.markdown(f"""
            - **Indexed Documents**: {source_count}
            - **Total Chunks**: {chunk_count}
            - **Search Method**: Hybrid (Semantic + BM25)
            - **Embeddings**: 384-dim MiniLM-L6
            """)


def handle_query_interface(rag_system):
    """Handle the main query interface."""
    if not rag_system.chunks:
        st.warning("⚠️ No documents indexed yet. Please upload documents in the 'Manage Documents' tab.")
        return
    
    # Query input
    query = st.text_input(
        "Enter your question:",
        placeholder="e.g., What is RISC-V and what are its main features?",
        key="main_query"
    )
    
    # Advanced options
    with st.expander("🔧 Advanced Options"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            top_k = st.slider("Results to retrieve", 3, 10, 5)
        with col2:
            dense_weight = st.slider("Semantic weight", 0.5, 1.0, 0.7, 0.1)
        with col3:
            use_fallback = st.checkbox("Use fallback model", False)
    
    if st.button("🔍 Search & Generate Answer", type="primary"):
        if not query.strip():
            st.error("Please enter a question.")
            return
        
        try:
            # Execute query with timing
            start_time = time.time()
            
            with st.spinner("🔍 Searching documents and generating answer..."):
                result = rag_system.query_with_answer(
                    question=query,
                    top_k=top_k,
                    use_hybrid=True,
                    dense_weight=dense_weight,
                    use_fallback_llm=use_fallback
                )
            
            total_time = time.time() - start_time
            
            # Display results
            display_query_results(result, total_time)
            
        except Exception as e:
            st.error(f"❌ Query failed: {str(e)}")
            st.markdown(f"**Error details:** {traceback.format_exc()}")


def display_query_results(result: Dict, total_time: float):
    """Display query results with metrics and citations."""
    
    # Performance metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("⏱️ Total Time", f"{total_time:.2f}s")
    with col2:
        st.metric("🎯 Confidence", f"{result['confidence']:.1%}")
    with col3:
        st.metric("📄 Sources", len(result['sources']))
    with col4:
        retrieval_time = result['retrieval_stats']['retrieval_time']
        st.metric("🔍 Retrieval", f"{retrieval_time:.2f}s")
    
    # Answer
    st.markdown("### 💬 Generated Answer")
    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #28a745; color: #333333;">
        {result['answer']}
    </div>
    """, unsafe_allow_html=True)
    
    # Citations
    if result['citations']:
        st.markdown("### 📚 Sources & Citations")
        
        for i, citation in enumerate(result['citations'], 1):
            st.markdown(f"""
            <div class="citation-box">
                <strong>[{i}]</strong> {citation['source']} (Page {citation['page']})<br>
                <small><em>Relevance: {citation['relevance']:.1%}</em></small><br>
                <small>"{citation['snippet']}"</small>
            </div>
            """, unsafe_allow_html=True)
    
    # Technical details
    with st.expander("🔬 Technical Details"):
        st.json({
            "retrieval_method": result['retrieval_stats']['method'],
            "chunks_retrieved": result['retrieval_stats']['chunks_retrieved'],
            "dense_weight": result['retrieval_stats'].get('dense_weight', 'N/A'),
            "model_used": result['generation_stats']['model'],
            "generation_time": f"{result['generation_stats']['generation_time']:.3f}s"
        })


def handle_document_upload(rag_system):
    """Handle document upload and indexing."""
    st.subheader("📤 Upload Documents")
    
    uploaded_files = st.file_uploader(
        "Upload PDF documents",
        type=['pdf'],
        accept_multiple_files=True,
        help="Upload technical documentation, manuals, or research papers"
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            if st.button(f"Index {uploaded_file.name}", key=f"index_{uploaded_file.name}"):
                try:
                    # Save uploaded file temporarily in app directory
                    import tempfile
                    import os
                    
                    # Create temp directory in app folder
                    temp_dir = Path("/app/temp_uploads")
                    temp_dir.mkdir(exist_ok=True)
                    
                    temp_path = temp_dir / uploaded_file.name
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                    
                    # Index the document
                    st.write(f"🔄 Starting to process {uploaded_file.name}...")
                    st.write(f"📁 File saved to: {temp_path}")
                    st.write(f"📏 File size: {temp_path.stat().st_size} bytes")
                    
                    # Capture print output for debugging
                    import io
                    import sys
                    
                    captured_output = io.StringIO()
                    sys.stdout = captured_output
                    
                    try:
                        with st.spinner(f"Processing {uploaded_file.name}..."):
                            chunk_count = rag_system.index_document(temp_path)
                            
                    finally:
                        # Restore stdout
                        sys.stdout = sys.__stdout__
                        
                        # Show captured output
                        output = captured_output.getvalue()
                        if output:
                            st.text_area("Processing Log:", output, height=150)
                    
                    st.success(f"✅ {uploaded_file.name} indexed! {chunk_count} chunks added.")
                    
                    # Clean up temp file
                    try:
                        temp_path.unlink()
                    except:
                        pass
                        
                    st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Failed to index {uploaded_file.name}: {str(e)}")
                    import traceback
                    st.error(f"Details: {traceback.format_exc()}")


def display_sample_queries():
    """Display sample queries for demonstration."""
    st.subheader("💡 Sample Questions")
    st.markdown("Click on any question to try it:")
    
    sample_queries = [
        "What is RISC-V and what are its main features?",
        "How does RISC-V compare to ARM and x86 architectures?",
        "What are the different RISC-V instruction formats?",
        "Explain RISC-V base integer instructions",
        "What are the benefits of using RISC-V in embedded systems?",
        "How does RISC-V handle memory management?",
        "What are RISC-V privileged instructions?",
        "Describe RISC-V calling conventions"
    ]
    
    for query in sample_queries:
        if st.button(query, key=f"sample_{hash(query)}"):
            st.session_state['sample_query'] = query
            st.rerun()


def main():
    """Main Streamlit application."""
    
    # Initialize session state
    if 'rag_system' not in st.session_state:
        st.session_state['rag_system'] = None
        st.session_state['init_error'] = None
    if 'api_token' not in st.session_state:
        st.session_state['api_token'] = None
    
    # Display header
    display_header()
    
    # Initialize RAG system
    if st.session_state['rag_system'] is None:
        with st.spinner("Initializing RAG system..."):
            selected_model = st.session_state.get('selected_model')
            rag_system, error = initialize_rag_system(
                st.session_state.get('api_token'),
                selected_model
            )
            st.session_state['rag_system'] = rag_system
            st.session_state['init_error'] = error
    
    rag_system = st.session_state['rag_system']
    init_error = st.session_state['init_error']
    
    # Check for initialization errors
    if init_error:
        st.markdown(f"""
        <div class="error-box">
            ❌ <strong>Failed to initialize RAG system:</strong><br>
            {init_error}<br><br>
            <strong>System uses HuggingFace Inference API</strong><br>
            If you see network errors, please check your internet connection.
        </div>
        """, unsafe_allow_html=True)
        return
    
    if rag_system is None:
        st.error("Failed to initialize RAG system. Please check the logs.")
        return
    
    # Display system status in sidebar
    display_system_status(rag_system)
    
    # Main interface
    tab1, tab2, tab3 = st.tabs(["🤔 Ask Questions", "📄 Manage Documents", "💡 Examples"])
    
    with tab1:
        # Handle sample query selection
        if 'sample_query' in st.session_state:
            st.text_input(
                "Enter your question:",
                value=st.session_state['sample_query'],
                key="main_query"
            )
            del st.session_state['sample_query']
        
        handle_query_interface(rag_system)
    
    with tab2:
        handle_document_upload(rag_system)
        
        # Option to load test document
        st.subheader("📖 Test Document")
        test_pdf_path = Path("data/test/riscv-base-instructions.pdf")
        
        if test_pdf_path.exists():
            if st.button("Load RISC-V Test Document"):
                try:
                    with st.spinner("Loading test document..."):
                        st.write(f"🔄 Processing test document: {test_pdf_path}")
                        st.write(f"📏 File size: {test_pdf_path.stat().st_size} bytes")
                        
                        chunk_count = rag_system.index_document(test_pdf_path)
                        st.success(f"✅ Test document loaded! {chunk_count} chunks indexed.")
                        st.rerun()
                except Exception as e:
                    st.error(f"Failed to load test document: {e}")
                    import traceback
                    st.error(f"Details: {traceback.format_exc()}")
        else:
            st.info("Test document not found at data/test/riscv-base-instructions.pdf")
    
    with tab3:
        display_sample_queries()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        Technical Documentation RAG Assistant | Powered by HuggingFace API & RISC-V Documentation<br>
        Built for ML Engineer Portfolio | Swiss Tech Market Focus
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()