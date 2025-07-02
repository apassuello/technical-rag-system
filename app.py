#!/usr/bin/env python3
"""
HuggingFace Spaces deployment wrapper for the Technical Documentation RAG Assistant.

This file serves as the main entry point for HuggingFace Spaces deployment,
with optimizations for cloud hosting and resource constraints.
"""

import os
import sys
from pathlib import Path
import streamlit as st
import subprocess
import time

# Configure for HuggingFace Spaces deployment
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
os.environ["STREAMLIT_SERVER_ENABLE_CORS"] = "false"
os.environ["STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION"] = "false"

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_ollama_availability():
    """Check if Ollama is available and models are installed."""
    try:
        # Check if ollama command exists
        result = subprocess.run(['which', 'ollama'], capture_output=True, text=True)
        if result.returncode != 0:
            return False, "Ollama not installed"
        
        # Check if required model is available
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode != 0:
            return False, "Ollama service not running"
        
        if 'llama3.2:3b' not in result.stdout:
            return False, "Llama 3.2 model not found"
        
        return True, "Ollama ready"
        
    except Exception as e:
        return False, f"Ollama check failed: {e}"


def setup_cloud_environment():
    """Setup environment for cloud deployment."""
    
    # Check Ollama availability
    ollama_available, ollama_status = check_ollama_availability()
    
    if not ollama_available:
        st.error(f"""
        **Ollama Setup Required**: {ollama_status}
        
        This demo requires Ollama with Llama 3.2 (3B) model. 
        
        **For local development:**
        1. Install Ollama: `brew install ollama`
        2. Pull model: `ollama pull llama3.2:3b`
        3. Run app: `streamlit run app.py`
        
        **Note**: This is a local LLM demo optimized for Apple Silicon.
        For cloud deployment, consider API-based alternatives.
        """)
        
        st.info("""
        **🎯 System Capabilities** (when properly configured):
        - Multi-document PDF processing
        - Hybrid semantic + keyword search  
        - Local LLM answer generation with citations
        - Real-time performance metrics
        - Cross-document source attribution
        """)
        
        st.stop()
    
    return True


def main():
    """Main application entry point."""
    
    # Setup cloud environment
    setup_cloud_environment()
    
    # Import and run the main Streamlit app
    try:
        # Import the main app module
        import streamlit_app
        
        # Run the main application
        streamlit_app.main()
        
    except ImportError as e:
        st.error(f"Failed to import main application: {e}")
        st.info("Please ensure all dependencies are installed correctly.")
        
    except Exception as e:
        st.error(f"Application error: {e}")
        st.info("Please check the logs for detailed error information.")


if __name__ == "__main__":
    main()