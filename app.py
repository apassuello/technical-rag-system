"""
Technical Documentation RAG System - Streamlit App

A user-friendly interface for querying technical documentation
using Retrieval-Augmented Generation.

Usage:
    streamlit run app.py

Features:
- Chat-style interface
- Real-time retrieval and answer generation
- Source document display
- Performance metrics
- Sample queries

Author: Arthur Passuello
Created: 2025-11-16
"""

import streamlit as st
import sys
from pathlib import Path
import time
import pickle

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.component_factory import ComponentFactory
from src.core.interfaces import Document
from src.core.config import load_config


# Page configuration
st.set_page_config(
    page_title="Technical Documentation RAG",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .source-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .metric-box {
        background-color: #e8f4f8;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin: 0.3rem 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_rag_system():
    """Load and cache RAG system components."""
    indices_dir = project_root / "data" / "indices"
    config_path = project_root / "config" / "default.yaml"

    # Load configuration
    config = load_config(config_path)

    # Load documents
    documents_path = indices_dir / "documents.pkl"
    with open(documents_path, 'rb') as f:
        documents = pickle.load(f)

    # Load FAISS index
    import faiss
    index_path = indices_dir / "faiss_index.bin"
    faiss_index = faiss.read_index(str(index_path))

    # Initialize embedder
    factory = ComponentFactory()
    embedder_config = config.embedder.model_dump()
    embedder = factory.create_embedder(
        embedder_config["type"],
        **embedder_config.get("config", {})
    )

    # Initialize LLM (check availability)
    llm_type = "mock"
    llm_model = "none"

    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get('models', [])
            if models:
                llm_type = "ollama"
                llm_model = models[0]['name']
    except:
        pass

    return {
        'documents': documents,
        'faiss_index': faiss_index,
        'embedder': embedder,
        'llm_type': llm_type,
        'llm_model': llm_model,
        'config': config
    }


def retrieve_documents(system, query: str, top_k: int = 5):
    """Retrieve relevant documents for query."""
    # Generate query embedding
    query_embedding = system['embedder'].embed([query])[0]

    # Search FAISS index
    import numpy as np
    query_vec = np.array([query_embedding], dtype=np.float32)
    distances, indices = system['faiss_index'].search(query_vec, k=top_k)

    # Collect results
    results = []
    for idx, distance in zip(indices[0], distances[0]):
        if idx < len(system['documents']):
            results.append((system['documents'][idx], float(distance)))

    return results


def generate_answer_ollama(system, query: str, context_docs):
    """Generate answer using Ollama."""
    import requests

    # Build context
    context_parts = []
    for i, (doc, score) in enumerate(context_docs, 1):
        source_name = "Unknown"
        if hasattr(doc, 'metadata') and doc.metadata:
            source = doc.metadata.get('source', 'Unknown')
            if '/' in source or '\\' in source:
                source_name = Path(source).name
            else:
                source_name = source
        context_parts.append(f"[{i}] Source: {source_name}\n{doc.content}\n")

    context = "\n".join(context_parts)

    # Build prompt
    prompt = f"""You are a helpful technical assistant. Answer the question based ONLY on the provided context.
Include citations using [1], [2], etc. to reference sources.

Context:
{context}

Question: {query}

Answer:"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": system['llm_model'],
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )

        if response.status_code == 200:
            return response.json()['response']
        else:
            return f"Error generating answer: {response.status_code}"

    except Exception as e:
        return f"Error: {e}"


def generate_answer_mock(query: str, context_docs):
    """Generate mock answer."""
    top_source = "Unknown"
    if context_docs and hasattr(context_docs[0][0], 'metadata'):
        source = context_docs[0][0].metadata.get('source', 'Unknown')
        if '/' in source or '\\' in source:
            top_source = Path(source).name

    return f"""**[Demo Mode - Install Ollama for real AI answers]**

Based on the retrieved documents from {top_source} and {len(context_docs)-1} other sources,
I found relevant information about: "{query}"

The retrieval system found {len(context_docs)} semantically relevant passages with scores
ranging from {context_docs[0][1]:.2f} to {context_docs[-1][1]:.2f}.

**To enable AI-generated answers:**
1. Install Ollama: `brew install ollama`
2. Download a model: `ollama pull llama3.2:3b`
3. Restart this app

The retrieval system is working perfectly - you're seeing real semantic search results!"""


def main():
    """Main Streamlit app."""

    # Header
    st.markdown('<div class="main-header">📚 Technical Documentation RAG</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI-powered question answering for RISC-V documentation</div>', unsafe_allow_html=True)

    # Load system
    with st.spinner("Loading RAG system..."):
        system = load_rag_system()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        top_k = st.slider("Number of sources to retrieve", 1, 10, 5)
        show_sources = st.checkbox("Show source documents", value=True)
        show_metrics = st.checkbox("Show performance metrics", value=True)

        st.divider()

        st.header("📊 System Info")
        st.metric("Documents Indexed", f"{len(system['documents']):,}")
        st.metric("Vector Dimension", system['faiss_index'].d)
        st.metric("LLM", system['llm_model'])

        if system['llm_type'] == 'mock':
            st.warning("⚠️ Demo mode: Install Ollama for AI answers")

        st.divider()

        st.header("💡 Sample Queries")
        sample_queries = [
            "What are RISC-V vector instructions?",
            "Explain privilege levels in RISC-V",
            "How does memory management work?",
            "What are CSR registers?",
            "How do interrupts work?"
        ]

        for query in sample_queries:
            if st.button(query, key=f"sample_{query}"):
                st.session_state.current_query = query

    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    if 'current_query' in st.session_state:
        query_text = st.session_state.current_query
        del st.session_state.current_query
    else:
        query_text = None

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("🔍 Ask a Question")

        # Query input
        query = st.text_input(
            "Enter your question:",
            value=query_text or "",
            placeholder="e.g., What are RISC-V vector instructions?",
            key="query_input"
        )

        if st.button("Submit", type="primary") or query_text:
            if query:
                with st.spinner("Thinking..."):
                    # Retrieval
                    retrieval_start = time.time()
                    retrieved_docs = retrieve_documents(system, query, top_k=top_k)
                    retrieval_time = (time.time() - retrieval_start) * 1000

                    # Answer generation
                    generation_start = time.time()
                    if system['llm_type'] == 'ollama':
                        answer = generate_answer_ollama(system, query, retrieved_docs)
                    else:
                        answer = generate_answer_mock(query, retrieved_docs)
                    generation_time = (time.time() - generation_start) * 1000

                    # Store in session
                    st.session_state.messages.append({
                        'query': query,
                        'answer': answer,
                        'sources': retrieved_docs,
                        'retrieval_time': retrieval_time,
                        'generation_time': generation_time
                    })

        # Display conversation history
        if st.session_state.messages:
            st.divider()
            st.header("💬 Conversation")

            for i, msg in enumerate(reversed(st.session_state.messages)):
                with st.expander(f"❓ {msg['query']}", expanded=(i == 0)):
                    st.markdown("**Answer:**")
                    st.markdown(msg['answer'])

                    if show_metrics:
                        st.markdown("**Performance:**")
                        col_a, col_b, col_c = st.columns(3)
                        col_a.metric("Retrieval", f"{msg['retrieval_time']:.0f}ms")
                        col_b.metric("Generation", f"{msg['generation_time']:.0f}ms")
                        col_c.metric("Total", f"{msg['retrieval_time'] + msg['generation_time']:.0f}ms")

                    if show_sources:
                        st.markdown("**Sources:**")
                        for j, (doc, score) in enumerate(msg['sources'], 1):
                            source = "Unknown"
                            if hasattr(doc, 'metadata') and doc.metadata:
                                src = doc.metadata.get('source', 'Unknown')
                                source = Path(src).name if ('/' in src or '\\' in src) else src

                            with st.container():
                                st.markdown(f"**[{j}] {source}** (relevance: {score:.3f})")
                                st.caption(doc.content[:300] + "..." if len(doc.content) > 300 else doc.content)

    with col2:
        st.header("ℹ️ About")
        st.markdown("""
        This RAG system uses:
        - **FAISS** for vector search
        - **Sentence Transformers** for embeddings
        - **Ollama** for answer generation (optional)

        The system can answer questions about:
        - RISC-V ISA specifications
        - Vector extensions
        - Privilege levels
        - Memory management
        - And more technical documentation
        """)

        st.divider()

        st.header("📖 How it works")
        st.markdown("""
        1. **Query**: You ask a question
        2. **Retrieve**: System finds relevant passages
        3. **Generate**: LLM creates an answer with citations
        4. **Cite**: Sources are provided for verification
        """)

        if st.button("Clear History"):
            st.session_state.messages = []
            st.rerun()


if __name__ == "__main__":
    main()
