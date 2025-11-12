"""
Conftest for Epic 1 ML Infrastructure tests.

Ensures fixtures directory is importable for ml_infrastructure tests.
"""

import sys
from pathlib import Path

# Add fixtures directory to Python path
ML_INFRA_DIR = Path(__file__).parent
FIXTURES_DIR = ML_INFRA_DIR / "fixtures"

if str(FIXTURES_DIR.parent) not in sys.path:
    sys.path.insert(0, str(FIXTURES_DIR.parent))

print(f"✓ ML Infrastructure conftest: Added fixtures path to sys.path")
