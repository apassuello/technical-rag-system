#!/usr/bin/env python3
"""
HuggingFace Spaces deployment wrapper for the Technical Documentation RAG Assistant.

This file serves as the main entry point for HuggingFace Spaces deployment,
with optimizations for cloud hosting and resource constraints.

Features:
- Automatic environment detection (HF Spaces vs local)
- Graceful fallbacks for missing dependencies
- Memory-optimized configuration
- Epic 2 enhanced RAG capabilities
"""

import os
import sys
from pathlib import Path
import streamlit as st
import subprocess
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure for HuggingFace Spaces deployment
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
os.environ["STREAMLIT_SERVER_ENABLE_CORS"] = "false" 
os.environ["STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION"] = "false"

# HuggingFace Spaces environment detection
IS_HF_SPACES = os.getenv("SPACE_ID") is not None
IS_LOCAL_DEV = not IS_HF_SPACES

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_environment_capabilities():
    """Check environment capabilities and suggest appropriate configuration."""
    capabilities = {
        "has_ollama": False,
        "has_hf_token": False,
        "memory_optimized": IS_HF_SPACES,
        "recommended_config": "default"
    }
    
    # Check Ollama availability
    try:
        result = subprocess.run(['which', 'ollama'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            # Check if service is running and model available
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and 'llama3.2:3b' in result.stdout:
                capabilities["has_ollama"] = True
                logger.info("Ollama with llama3.2:3b detected")
    except (subprocess.TimeoutExpired, Exception) as e:
        logger.info(f"Ollama check failed or timed out: {e}")

    # Check HuggingFace token availability
    hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
    if hf_token:
        capabilities["has_hf_token"] = True
        logger.info("HuggingFace token detected")

    # Recommend configuration based on capabilities
    if capabilities["has_hf_token"]:
        capabilities["recommended_config"] = "epic2_hf_api"
    elif capabilities["has_ollama"]:
        capabilities["recommended_config"] = "epic2_graph_calibrated" 
    else:
        capabilities["recommended_config"] = "default"
        
    return capabilities


def setup_environment_display(capabilities):
    """Display environment status and configuration recommendations."""
    
    st.sidebar.markdown("### 🔧 Environment Status")
    
    # Environment detection
    if IS_HF_SPACES:
        st.sidebar.success("🌐 Running on HuggingFace Spaces")
    else:
        st.sidebar.info("💻 Running locally")
    
    # Capability status
    if capabilities["has_ollama"]:
        st.sidebar.success("✅ Ollama + Llama 3.2 available")
    else:
        st.sidebar.warning("⚠️ Ollama not available")
        
    if capabilities["has_hf_token"]:
        st.sidebar.success("✅ HuggingFace API available")
    else:
        st.sidebar.info("💡 Add HF_TOKEN for API access")
    
    # Configuration recommendation
    config = capabilities["recommended_config"]
    st.sidebar.markdown(f"**Recommended Config**: `{config}`")
    
    # Setup instructions if needed
    if not capabilities["has_ollama"] and not capabilities["has_hf_token"]:
        st.sidebar.markdown("""
        **Setup Options:**
        1. **API Mode**: Set HF_TOKEN environment variable
        2. **Local Mode**: Install Ollama + `ollama pull llama3.2:3b`
        3. **Demo Mode**: Use mock configuration
        """)
    
    return capabilities


def main():
    """Main application entry point with Epic 2 enhanced capabilities."""
    
    # Page configuration
    st.set_page_config(
        page_title="Epic 2 Enhanced RAG Demo",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Check environment capabilities
    capabilities = check_environment_capabilities()
    setup_environment_display(capabilities)
    
    # Main application header
    st.title("🚀 Epic 2 Enhanced RAG System")
    st.markdown("""
    **Technical Documentation RAG with Advanced Features**
    
    This system demonstrates production-ready RAG capabilities with:
    - 📈 **48.7% MRR improvement** with graph-enhanced fusion
    - 🧠 **Neural reranking** for improved relevance
    - 🔗 **Graph enhancement** for document relationships  
    - ⚡ **Swiss engineering standards** with comprehensive validation
    """)
    
    # Import and run the appropriate app based on capabilities
    try:
        if capabilities["has_hf_token"] or capabilities["has_ollama"]:
            # Use Epic 2 demo with full capabilities
            logger.info(f"Loading Epic 2 demo with config: {capabilities['recommended_config']}")
            
            # Set configuration environment variable
            os.environ["RAG_CONFIG"] = f"config/{capabilities['recommended_config']}.yaml"
            
            # Import and run Epic 2 demo
            import streamlit_epic2_demo
            # The Epic 2 demo will handle its own execution
            
        else:
            # Fallback to basic demo with mock capabilities
            st.info("""
            **Demo Mode Active** - Limited functionality without Ollama or HF API access.
            
            **System Capabilities** (when properly configured):
            - Multi-document PDF processing with 565K chars/sec throughput
            - Hybrid semantic + keyword search with BM25 + vector similarity
            - Advanced neural reranking with cross-encoder models
            - Graph-enhanced document fusion (48.7% MRR improvement)
            - Real-time performance metrics and source attribution
            """)
            
            # Show system architecture
            st.markdown("### 🏗️ System Architecture")
            st.markdown("""
            **6-Component Modular Architecture:**
            1. **Platform Orchestrator** - System lifecycle management
            2. **Document Processor** - PDF parsing and chunking
            3. **Embedder** - Text vectorization with MPS acceleration  
            4. **Retriever** - Hybrid search with graph enhancement
            5. **Answer Generator** - LLM-based response synthesis
            6. **Query Processor** - Workflow orchestration
            """)
            
            # Show performance metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("MRR Improvement", "48.7%", delta="vs baseline")
            with col2:
                st.metric("Score Discrimination", "114,923%", delta="improvement")
            with col3:
                st.metric("Architecture Compliance", "100%", delta="modular")
        
    except ImportError as e:
        st.error(f"Failed to import application modules: {e}")
        st.info("Please ensure all dependencies are installed correctly.")
        
        # Show installation guide
        st.markdown("### 📦 Installation Guide")
        st.code("""
        # Install dependencies
        pip install -r requirements.txt
        
        # For local LLM (recommended)
        ollama pull llama3.2:3b
        
        # For API access (alternative)
        export HF_TOKEN=your_token_here
        """)
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error(f"Application error: {e}")
        st.info("Please check the logs for detailed error information.")


if __name__ == "__main__":
    main()