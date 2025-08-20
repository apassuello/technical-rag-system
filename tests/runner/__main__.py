"""
Main entry point for running the test runner as a module.

Usage:
    python -m tests.runner epic1 all
    python -m tests.runner list
    python -m tests.runner validate
"""

import sys
from .cli import main

if __name__ == '__main__':
    sys.exit(main())