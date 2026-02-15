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

# Eagerly import ComponentFactory so the reference survives any test patches
from src.core.component_factory import ComponentFactory as _RealComponentFactory


import src.core.platform_orchestrator as _po_module


@pytest.fixture(autouse=True)
def _clear_component_factory_cache(request):
    """Prevent cached Mock components from leaking between unit tests.

    Only active for tests/unit — integration and validation tests need
    component reuse across session-scoped orchestrator fixtures.

    Clears caches AND restores the ComponentFactory reference in the
    platform_orchestrator module namespace. Unit tests that patch
    'src.core.platform_orchestrator.ComponentFactory' can leave a Mock
    reference that persists into subsequent tests (e.g. validation tests),
    causing 'Mock object is not iterable' errors when the orchestrator
    tries to use a Mock embedder.
    """
    is_unit = "/tests/unit/" in str(request.fspath) or str(request.fspath).endswith("/tests/unit")
    if is_unit:
        _RealComponentFactory._component_cache.clear()
        _RealComponentFactory._class_cache.clear()
        _po_module.ComponentFactory = _RealComponentFactory
    yield
    if is_unit:
        _RealComponentFactory._component_cache.clear()
        _RealComponentFactory._class_cache.clear()
        _po_module.ComponentFactory = _RealComponentFactory


def pytest_sessionfinish(session, exitstatus):
    """Shut down lingering ThreadPoolExecutor threads to prevent pytest from hanging.

    Uses the internal _threads_queues dict to deregister threads from
    Python's atexit handler.  This is a private API but stable across
    Python 3.9-3.12 and the only reliable way to prevent the hang.
    """
    import concurrent.futures.thread as _cft

    for t in list(_cft._threads_queues):
        _cft._threads_queues[t] = None


import urllib.request


@pytest.fixture(scope="session")
def orchestrator():
    """Shared PlatformOrchestrator — loaded once, used by integration + validation."""
    from src.core.platform_orchestrator import PlatformOrchestrator

    config_path = Path(__file__).resolve().parent.parent / "config" / "test-ollama.yaml"
    orch = PlatformOrchestrator(config_path)
    yield orch
    if hasattr(orch, '_components'):
        orch._components.clear()
    if hasattr(orch, 'health_service'):
        orch.health_service.monitored_components.clear()
        orch.health_service.health_history.clear()
    if hasattr(orch, 'analytics_service'):
        orch.analytics_service.component_metrics.clear()


def _spacy_model_available(model: str = "en_core_web_sm") -> bool:
    """Check if spaCy and a specific model are installed."""
    try:
        import spacy
        spacy.load(model)
        return True
    except Exception:
        return False


def _service_available(url: str, timeout: float = 2.0) -> bool:
    """Check if an HTTP service is reachable."""
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except Exception:
        return False


TIER_ORDER = {"unit": 0, "integration": 1, "validation": 2}


def _get_tier(item):
    parts = item.nodeid.split("/")
    for part in parts:
        if part in TIER_ORDER:
            return TIER_ORDER[part]
    return len(TIER_ORDER)


def pytest_collection_modifyitems(config, items):
    """Auto-skip tests whose required services are unavailable, then sort by tier."""
    service_checks = {
        "requires_ollama": (
            lambda: _service_available("http://localhost:11434/health"),
            "llama-server not running on localhost:11434",
        ),
        "requires_weaviate": (
            lambda: _service_available("http://localhost:8180/v1/.well-known/ready"),
            "Weaviate not running on localhost:8180",
        ),
        "requires_spacy": (
            lambda: _spacy_model_available(),
            "spaCy or en_core_web_sm not installed (pip install spacy && python -m spacy download en_core_web_sm)",
        ),
    }

    # Cache availability checks (run each probe at most once)
    availability = {}
    for marker_name, (check_fn, _reason) in service_checks.items():
        availability[marker_name] = check_fn()

    for item in items:
        for marker_name, (_check_fn, reason) in service_checks.items():
            if marker_name in {m.name for m in item.iter_markers()}:
                if not availability[marker_name]:
                    item.add_marker(pytest.mark.skip(reason=reason))

    # Sort by tier: unit → integration → validation
    items.sort(key=_get_tier)
