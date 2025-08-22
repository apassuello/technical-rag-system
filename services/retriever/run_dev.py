#!/usr/bin/env python3
"""
Development runner for the Retriever Service.

This script provides a convenient way to run the service in development mode
with proper environment setup and configuration.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set environment variables for development
os.environ['PYTHONPATH'] = f"{project_root}:{project_root}/src"
os.environ['PROJECT_ROOT'] = str(project_root)

def main():
    """Run the retriever service in development mode."""
    print("🚀 Starting Retriever Service in Development Mode")
    print("=" * 60)
    print(f"Project Root: {project_root}")
    print(f"Python Path: {os.environ['PYTHONPATH']}")
    print(f"Working Directory: {Path.cwd()}")
    print("=" * 60)
    
    try:
        import uvicorn
        
        # Run with uvicorn
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8083,
            reload=True,
            reload_dirs=[str(Path(__file__).parent / "app")],
            log_level="info",
            access_log=True
        )
        
    except ImportError:
        print("❌ uvicorn not found. Please install requirements:")
        print("   pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ Failed to start service: {e}")
        return 1

if __name__ == "__main__":
    exit(main())