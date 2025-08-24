#!/usr/bin/env python3
"""
RAG Portfolio Test Runner

Entry point for the comprehensive test execution system.
Supports Epic-aware test execution with rich reporting.

Usage:
    python test_runner.py epic1 all
    python test_runner.py epic1 integration --format json
    python test_runner.py smoke
    python test_runner.py list
"""

import sys
from pathlib import Path

# Add project root and tests directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tests"))

from runner.cli import main

if __name__ == '__main__':
    sys.exit(main())