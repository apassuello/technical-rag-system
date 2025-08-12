#!/usr/bin/env python3
"""Run Epic 1 validation test to check current implementation status."""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Set environment variable to reduce logging noise
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

# Import and run the test
try:
    from test_epic1_end_to_end import main
    print("Starting Epic 1 validation test...")
    success = main()
    print(f"\nTest completed with status: {'SUCCESS' if success else 'FAILED'}")
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all dependencies are installed.")
except Exception as e:
    print(f"Error running test: {e}")
    import traceback
    traceback.print_exc()
