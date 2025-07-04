#!/usr/bin/env python3
"""
Technical Documentation RAG System - Streamlit Interface

A professional web interface for the RAG system with answer generation,
optimized for technical documentation Q&A.
"""

import streamlit as st
import sys
from pathlib import Path
import time
import traceback
from typing import List, Dict, Any
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import directly since we're in the project directory
sys.path.insert(0, str(Path(__file__).parent))
from src.rag_with_generation import RAGWithGeneration


# Page configuration
st.set_page_config(
    page_title="Technical Documentation RAG Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for professional styling
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    
    .citation-box {
        background-color: #e8f4f8;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
    }
    
    .answer-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def initialize_rag_system():
    """Initialize the RAG system with HuggingFace API."""
    try:
        import os

        # Try multiple common token names
        api_token = (
            os.getenv("HUGGINGFACE_API_TOKEN")
            or os.getenv("HF_TOKEN")
            or os.getenv("HF_API_TOKEN")
        )

        # Debug logging (will show in Spaces logs) - force to stderr for visibility
        import sys

        if api_token:
            print(
                f"✅ Found HF token (starts with: {api_token[:8]}...)",
                file=sys.stderr,
                flush=True,
            )
        else:
            print(
                "⚠️ No HF token found in environment variables",
                file=sys.stderr,
                flush=True,
            )
            print(
                f"Available env vars: {list(os.environ.keys())}",
                file=sys.stderr,
                flush=True,
            )

        # Check if we're running locally or in HuggingFace Spaces
        is_hf_spaces = os.getenv("SPACE_ID") is not None  # HF Spaces sets SPACE_ID
        use_ollama = True  # os.getenv("USE_OLLAMA", "false").lower() == "true"

        if is_hf_spaces:
            print("🚀 Running in HuggingFace Spaces", file=sys.stderr, flush=True)
            if use_ollama:
                print(
                    "🦙 Ollama enabled in HuggingFace Spaces",
                    file=sys.stderr,
                    flush=True,
                )
            else:
                print("🤗 Using HuggingFace API in Spaces", file=sys.stderr, flush=True)
        else:
            print("💻 Running locally", file=sys.stderr, flush=True)
            if use_ollama:
                print("🦙 Using local Ollama", file=sys.stderr, flush=True)
            else:
                print("🤗 Using HuggingFace API locally", file=sys.stderr, flush=True)

        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

        if use_ollama:
            model_name = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
            print(
                f"🦙 Configured for local Ollama with model: {model_name}",
                file=sys.stderr,
                flush=True,
            )
        else:
            model_name = "sshleifer/distilbart-cnn-12-6"  # Confirmed working HF model
            print(
                f"🤗 Configured for HuggingFace API with model: {model_name}",
                file=sys.stderr,
                flush=True,
            )

        rag = RAGWithGeneration(
            model_name=model_name,
            api_token=api_token,
            temperature=0.3,
            max_tokens=512,
            use_ollama=use_ollama,
            ollama_url=ollama_url,
        )
        return rag, None
    except Exception as e:
        return None, str(e)


def display_header():
    """Display the main header and description."""
    st.markdown(
        '<h1 class="main-header">🔍 Technical Documentation RAG Assistant</h1>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    **Intelligent Q&A System for Technical Documentation**
    
    This system uses advanced hybrid search (semantic + keyword matching) combined with HuggingFace API generation 
    to provide accurate, cited answers from your technical documentation.
    
    **Features:**
    - 🚀 Hybrid retrieval for optimal relevance
    - 📚 Automatic citation and source attribution
    - 🎯 Confidence scoring for answer quality
    - ⚡ HuggingFace API for reliable generation
    """
    )


def display_system_status(rag_system):
    """Display system status and metrics."""
    if rag_system is None:
        return

    with st.sidebar:
        st.header("📊 System Status")

        # Check if documents are indexed
        if hasattr(rag_system, "chunks") and rag_system.chunks:
            st.success(f"✅ {len(rag_system.chunks)} chunks indexed")

            # Show document sources
            sources = set(chunk.get("source", "unknown") for chunk in rag_system.chunks)
            st.info(f"📄 {len(sources)} documents loaded")

            with st.expander("Document Details"):
                for source in sorted(sources):
                    source_name = Path(source).name if source != "unknown" else source
                    chunk_count = len(
                        [c for c in rag_system.chunks if c.get("source") == source]
                    )
                    st.write(f"• {source_name}: {chunk_count} chunks")
        else:
            st.warning("⚠️ No documents indexed")
            st.info("Upload a PDF to get started")

        # Model information
        st.header("🤖 Model Info")
        if hasattr(rag_system, "answer_generator"):
            model_name = getattr(
                rag_system.answer_generator, "model_name", "gpt2-medium"
            )
            st.write(f"**Model:** {model_name}")
            
            # Show warmup warning for Ollama models
            if hasattr(rag_system.answer_generator, 'base_url') or 'llama' in model_name.lower():
                st.warning("⏱️ **First Query Notice**\nFirst query may take 30-60s for model warmup. Subsequent queries will be much faster!")
        else:
            st.write(f"**Model:** gpt2-medium (HuggingFace API)")
        st.write(f"**Temperature:** 0.3")


def handle_document_upload(rag_system):
    """Handle PDF document upload and indexing."""
    st.header("📄 Document Management")

    uploaded_file = st.file_uploader(
        "Upload PDF Document",
        type="pdf",
        help="Upload a technical PDF document to add to the knowledge base",
    )

    if uploaded_file is not None:
        if st.button("Index Document", type="primary"):
            try:
                with st.spinner("Processing document..."):
                    # Save uploaded file temporarily
                    temp_path = Path(f"/tmp/{uploaded_file.name}")
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getvalue())

                    # Index the document
                    start_time = time.time()
                    chunk_count = rag_system.index_document(temp_path)
                    processing_time = time.time() - start_time

                    # Clean up temp file
                    temp_path.unlink()

                    st.markdown(
                        f"""
                    <div class="success-box">
                        ✅ <strong>Document indexed successfully!</strong><br>
                        📊 {chunk_count} chunks created in {processing_time:.2f}s<br>
                        📄 Ready for queries
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Refresh the page to update sidebar
                    st.rerun()

            except Exception as e:
                st.markdown(
                    f"""
                <div class="error-box">
                    ❌ <strong>Error processing document:</strong><br>
                    {str(e)}
                </div>
                """,
                    unsafe_allow_html=True,
                )


def handle_query_interface(rag_system):
    """Handle the main query interface."""
    st.header("🤔 Ask Your Question")

    # Check if documents are available
    if not hasattr(rag_system, "chunks") or not rag_system.chunks:
        st.warning("Please upload and index a document first to ask questions.")
        return

    # Query input
    query = st.text_input(
        "Enter your question:",
        placeholder="e.g., What is RISC-V? How does instruction encoding work?",
        help="Ask any question about the uploaded technical documentation",
    )

    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        col1, col2 = st.columns(2)

        with col1:
            use_hybrid = st.checkbox(
                "Use Hybrid Search",
                value=True,
                help="Combine semantic and keyword search",
            )
            dense_weight = st.slider(
                "Semantic Weight",
                0.0,
                1.0,
                0.7,
                0.1,
                help="Weight for semantic search (vs keyword)",
            )

        with col2:
            top_k = st.slider(
                "Number of Sources",
                1,
                10,
                5,
                help="Number of source chunks to retrieve",
            )
            use_fallback_llm = st.checkbox(
                "Use Fallback Model",
                value=False,
                help="Use larger model for complex queries",
            )

    # Query processing
    if query and st.button("Get Answer", type="primary"):
        try:
            with st.spinner("Searching and generating answer..."):
                start_time = time.time()

                # Debug: Check if documents are actually indexed
                print(
                    f"🔍 Debug: Chunks available: {len(getattr(rag_system, 'chunks', []))}",
                    file=sys.stderr,
                    flush=True,
                )
                if hasattr(rag_system, "chunks") and rag_system.chunks:
                    print(
                        f"🔍 Debug: First chunk preview: {rag_system.chunks[0].get('text', '')[:100]}...",
                        file=sys.stderr,
                        flush=True,
                    )

                # Get answer
                result = rag_system.query_with_answer(
                    question=query,
                    top_k=top_k,
                    use_hybrid=use_hybrid,
                    dense_weight=dense_weight,
                    use_fallback_llm=use_fallback_llm,
                    return_context=True,
                )

                # Debug: Check what was retrieved
                print(
                    f"🔍 Debug: Retrieved chunks: {len(result.get('context', []))}",
                    file=sys.stderr,
                    flush=True,
                )
                print(
                    f"🔍 Debug: Citations: {len(result.get('citations', []))}",
                    file=sys.stderr,
                    flush=True,
                )
                print(
                    f"🔍 Debug: Answer preview: {result.get('answer', '')[:100]}...",
                    file=sys.stderr,
                    flush=True,
                )

                total_time = time.time() - start_time

                # Display results
                display_answer_results(result, total_time)

        except Exception as e:
            st.markdown(
                f"""
            <div class="error-box">
                ❌ <strong>Error generating answer:</strong><br>
                {str(e)}
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Show detailed error in expander for debugging
            with st.expander("🔍 Error Details"):
                st.code(traceback.format_exc())


def display_answer_results(result: Dict[str, Any], total_time: float):
    """Display the answer results in a formatted way."""

    # Main answer
    st.markdown(
        f"""
    <div class="answer-box">
        <h3>📝 Answer</h3>
        {result['answer']}
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Streamlit only accepts 'normal', 'inverse', or 'off' for delta_color
        confidence_color = "normal" if result["confidence"] > 0.6 else "inverse"
        st.metric(
            "Confidence", f"{result['confidence']:.1%}", delta_color=confidence_color
        )

    with col2:
        st.metric("Sources", len(result["citations"]))

    with col3:
        st.metric("Total Time", f"{total_time:.2f}s")

    with col4:
        retrieval_method = result.get("retrieval_stats", {}).get("method", "unknown")
        st.metric("Method", retrieval_method)

    # Citations
    if result["citations"]:
        st.markdown("### 📚 Sources")
        for i, citation in enumerate(result["citations"], 1):
            st.markdown(
                f"""
            <div class="citation-box">
                <strong>{i}. {citation['source']}</strong> (Page {citation['page']})<br>
                <small>Relevance: {citation['relevance']:.1%}</small><br>
                <em>"{citation['snippet']}"</em>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # Detailed metrics
    with st.expander("📊 Detailed Metrics"):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Retrieval Stats")
            retrieval_stats = result.get("retrieval_stats", {})
            st.json(retrieval_stats)

        with col2:
            st.subheader("Generation Stats")
            generation_stats = result.get("generation_stats", {})
            st.json(generation_stats)

    # Context chunks (for debugging)
    if "context" in result and st.checkbox("Show Retrieved Context"):
        st.subheader("🔍 Retrieved Context")
        for i, chunk in enumerate(result["context"], 1):
            with st.expander(
                f"Chunk {i} - {Path(chunk.get('source', 'unknown')).name} (Page {chunk.get('page', 'unknown')})"
            ):
                st.write(
                    f"**Score:** {chunk.get('hybrid_score', chunk.get('similarity_score', 0)):.3f}"
                )
                st.write(f"**Text:** {chunk.get('text', '')[:500]}...")


def display_sample_queries():
    """Display sample queries for user guidance."""
    st.header("💡 Sample Queries")

    sample_queries = [
        "What is RISC-V and what are its main features?",
        "How does the RISC-V instruction encoding work?",
        "What are the differences between RV32I and RV64I?",
        "Explain the RISC-V register model and naming conventions",
        "How does RISC-V handle memory ordering and consistency?",
        "What are the RISC-V privileged instruction set features?",
        "How do atomic instructions work in RISC-V?",
        "What is the RISC-V calling convention?",
    ]

    for query in sample_queries:
        if st.button(f"📌 {query}", key=f"sample_{hash(query)}"):
            st.session_state["sample_query"] = query
            st.rerun()


def main():
    """Main Streamlit application."""

    # Initialize session state
    if "rag_system" not in st.session_state:
        st.session_state["rag_system"] = None
        st.session_state["init_error"] = None

    # Display header
    display_header()

    # Initialize RAG system
    if st.session_state["rag_system"] is None:
        with st.spinner("Initializing RAG system..."):
            rag_system, error = initialize_rag_system()
            st.session_state["rag_system"] = rag_system
            st.session_state["init_error"] = error

    rag_system = st.session_state["rag_system"]
    init_error = st.session_state["init_error"]

    # Check for initialization errors
    if init_error:
        st.markdown(
            f"""
        <div class="error-box">
            ❌ <strong>Failed to initialize RAG system:</strong><br>
            {init_error}<br><br>
            <strong>System uses HuggingFace Inference API</strong><br>
            • For better models, add your HF Pro token as HUGGINGFACE_API_TOKEN<br>
            • Check internet connection for API access
        </div>
        """,
            unsafe_allow_html=True,
        )
        return

    if rag_system is None:
        st.error("Failed to initialize RAG system. Please check the logs.")
        return

    # Display system status in sidebar
    display_system_status(rag_system)

    # Main interface
    tab1, tab2, tab3 = st.tabs(
        ["🤔 Ask Questions", "📄 Manage Documents", "💡 Examples"]
    )

    with tab1:
        # Handle sample query selection
        if "sample_query" in st.session_state:
            st.text_input(
                "Enter your question:",
                value=st.session_state["sample_query"],
                key="main_query",
            )
            del st.session_state["sample_query"]

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
                        chunk_count = rag_system.index_document(test_pdf_path)
                        st.success(
                            f"✅ Test document loaded! {chunk_count} chunks indexed."
                        )
                        st.rerun()
                except Exception as e:
                    st.error(f"Failed to load test document: {e}")
        else:
            st.info("Test document not found at data/test/riscv-base-instructions.pdf")

    with tab3:
        display_sample_queries()

    # Footer
    st.markdown("---")
    st.markdown(
        """
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        Technical Documentation RAG Assistant | Powered by HuggingFace API & RISC-V Documentation<br>
        Built for ML Engineer Portfolio | Swiss Tech Market Focus
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
