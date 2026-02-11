"""
Root conftest.py for RAG Portfolio Project Tests

This file ensures proper Python path configuration for all tests,
enabling imports from src/ and proper test discovery.
"""

import sys
from pathlib import Path

import pytest

# Add project root and src to Python path for all tests
PROJECT_ROOT = Path(__file__).parent.parent
SRC_PATH = PROJECT_ROOT / "src"

# Insert at beginning of path to ensure our modules are found first
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

print(f"✓ Root conftest.py: Added {PROJECT_ROOT} and {SRC_PATH} to sys.path")

# Eagerly import ComponentFactory so the reference survives any test patches
from src.core.component_factory import ComponentFactory as _RealComponentFactory


@pytest.fixture(autouse=True)
def _clear_component_factory_cache():
    """Prevent cached Mock components from leaking between tests.

    Only clear _component_cache (instances), NOT _class_cache (import refs).
    Clearing _class_cache forces re-import of every component class and can
    break PlatformOrchestrator initialization in validation tests.
    """
    _RealComponentFactory._component_cache.clear()
    yield
    _RealComponentFactory._component_cache.clear()


def pytest_sessionfinish(session, exitstatus):
    """Shut down lingering ThreadPoolExecutor threads to prevent pytest from hanging."""
    import concurrent.futures.thread as _thread

    for t in list(_thread._threads_queues):
        _thread._threads_queues[t] = None
