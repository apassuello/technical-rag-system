#!/usr/bin/env python3
"""
Minimal HuggingFace Spaces startup script.
Starts Streamlit directly with fallback to HF API (no Ollama complexity for now).
"""

import os
import sys
import subprocess
from datetime import datetime

def log(message):
    """Log message to stderr for visibility in HF Spaces."""
    print(f"[{datetime.now().isoformat()}] {message}", file=sys.stderr, flush=True)

def main():
    """Minimal startup - just run Streamlit with HF API."""
    log("🚀 Starting Technical RAG Assistant in HuggingFace Spaces...")
    
    # Set environment for HF API fallback
    os.environ['USE_OLLAMA'] = 'false'
    log("🤗 Using HuggingFace API (Ollama disabled for initial deployment)")
    
    # Start Streamlit directly
    log("🎯 Starting Streamlit application...")
    try:
        subprocess.run([
            'streamlit', 'run', 'streamlit_app.py',
            '--server.port=8501',
            '--server.address=0.0.0.0',
            '--server.headless=true',
            '--server.enableCORS=false',
            '--server.enableXsrfProtection=false'
        ], check=True)
    except Exception as e:
        log(f"❌ Failed to start Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()