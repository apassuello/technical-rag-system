#!/usr/bin/env python3
"""
HuggingFace Spaces startup script with Ollama support.
Starts Ollama server in background, then launches Streamlit.
"""

import os
import sys
import subprocess
import time
import signal
from datetime import datetime


def log(message):
    """Log message to stderr for visibility in HF Spaces."""
    print(f"[{datetime.now().isoformat()}] {message}", file=sys.stderr, flush=True)


def start_ollama():
    """Start Ollama server in background."""
    log("🦙 Starting Ollama server...")
    
    try:
        # Start Ollama in background
        ollama_process = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create new process group
        )
        
        log(f"🦙 Ollama server started with PID {ollama_process.pid}")
        
        # Wait for Ollama to be ready
        log("⏳ Waiting for Ollama to be ready...")
        max_retries = 12  # 60 seconds total
        for attempt in range(max_retries):
            try:
                # Test if Ollama is responding
                result = subprocess.run(
                    ["curl", "-s", "http://localhost:11434/api/tags"],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    log("✅ Ollama server is ready!")
                    
                    # Try to pull the model (optimized for HF Spaces)
                    log("📥 Pulling llama3.2:1b model (optimized for container deployment)...")
                    pull_result = subprocess.run(
                        ["ollama", "pull", "llama3.2:1b"],
                        capture_output=True,
                        timeout=300  # 5 minutes for model download
                    )
                    if pull_result.returncode == 0:
                        log("✅ Model llama3.2:1b ready!")
                    else:
                        log("⚠️ Model pull failed, will download on first use")
                    
                    return ollama_process
                    
            except (subprocess.TimeoutExpired, Exception) as e:
                log(f"🔄 Ollama not ready yet (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(5)
                continue
        
        log("❌ Ollama failed to start after 60 seconds")
        ollama_process.terminate()
        return None
        
    except Exception as e:
        log(f"❌ Failed to start Ollama: {e}")
        return None


def main():
    """Start services and Streamlit based on configuration."""
    log("🚀 Starting Technical RAG Assistant in HuggingFace Spaces...")

    # Check which inference method to use
    use_ollama = os.getenv("USE_OLLAMA", "false").lower() == "true"
    use_inference_providers = os.getenv("USE_INFERENCE_PROVIDERS", "false").lower() == "true"
    
    ollama_process = None
    
    # Configure environment variables based on selected inference method
    if use_inference_providers:
        os.environ["USE_INFERENCE_PROVIDERS"] = "true"
        os.environ["USE_OLLAMA"] = "false"
        log("🚀 Using Inference Providers API")
    elif use_ollama:
        os.environ["USE_OLLAMA"] = "true"
        os.environ["USE_INFERENCE_PROVIDERS"] = "false"
        log("🦙 Ollama enabled - starting server...")
        ollama_process = start_ollama()
        
        if ollama_process is None:
            log("🔄 Ollama failed to start, falling back to HuggingFace API")
            os.environ["USE_OLLAMA"] = "false"
            os.environ["USE_INFERENCE_PROVIDERS"] = "false"
    else:
        os.environ["USE_OLLAMA"] = "false"
        os.environ["USE_INFERENCE_PROVIDERS"] = "false"
        log("🤗 Using classic HuggingFace API")

    # Start Streamlit
    log("🎯 Starting Streamlit application...")
    
    def signal_handler(signum, frame):
        """Handle shutdown signals."""
        log("🛑 Received shutdown signal, cleaning up...")
        if ollama_process:
            log("🦙 Stopping Ollama server...")
            try:
                os.killpg(os.getpgid(ollama_process.pid), signal.SIGTERM)
            except:
                pass
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        subprocess.run(
            [
                "streamlit",
                "run",
                "streamlit_app.py",
                "--server.port=8501",
                "--server.address=0.0.0.0",
                "--server.headless=true",
                "--server.enableCORS=false",
                "--server.enableXsrfProtection=false",
            ],
            check=True,
        )
    except Exception as e:
        log(f"❌ Failed to start Streamlit: {e}")
        sys.exit(1)
    finally:
        # Clean up Ollama if it was started
        if ollama_process:
            log("🦙 Cleaning up Ollama server...")
            try:
                os.killpg(os.getpgid(ollama_process.pid), signal.SIGTERM)
            except:
                pass


if __name__ == "__main__":
    main()
