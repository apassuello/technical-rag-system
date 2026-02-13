"""Unit tests for Epic1MLAnalyzer asyncio fix."""

import asyncio
import inspect
import pytest
from unittest.mock import MagicMock
from src.components.query_processors.base import QueryAnalysis


pytestmark = [pytest.mark.unit]


class TestAnalyzeQueryNoAsyncio:
    """Verify _analyze_query works without asyncio.run()."""

    def test_analyze_query_does_not_use_asyncio_run(self):
        """The sync _analyze_query path should not call asyncio.run()."""
        from src.components.query_processors.analyzers.epic1_ml_analyzer import Epic1MLAnalyzer

        source = inspect.getsource(Epic1MLAnalyzer._analyze_query)
        assert 'asyncio.run' not in source, (
            "_analyze_query should not use asyncio.run() — "
            "it breaks inside running event loops (pytest-asyncio, FastAPI, Jupyter)"
        )

    def test_analyze_query_works_inside_event_loop(self):
        """_analyze_query must not use asyncio.run() — it fails inside running loops."""
        from src.components.query_processors.analyzers.epic1_ml_analyzer import Epic1MLAnalyzer

        # Create analyzer with mocked internals
        analyzer = Epic1MLAnalyzer.__new__(Epic1MLAnalyzer)
        analyzer.logger = __import__('logging').getLogger('test')
        analyzer.view_analyzers = {}
        analyzer.complexity_classifier = None
        analyzer.model_recommender = None
        analyzer._analysis_times = []
        analyzer.total_analyses = 0
        analyzer._model_manager = None
        analyzer._memory_monitor = None
        analyzer.trained_models = {}
        analyzer.ensemble_models = {}

        # Mock _get_trained_model_predictions to return None (triggers fallback)
        analyzer._get_trained_model_predictions = MagicMock(return_value=None)

        # Run inside a running event loop — this is where asyncio.run() would fail
        async def run_in_loop():
            return analyzer._analyze_query("What is RISC-V?")

        result = asyncio.run(run_in_loop())

        assert isinstance(result, QueryAnalysis)
        assert result.query == "What is RISC-V?"
