"""Unit tests for HybridView and MLView base paths in base_view.py.

Tests weighted combination logic, fallback behaviour, and async paths
using concrete subclasses that override abstract methods.
"""

import pytest

from components.query_processors.analyzers.ml_views.base_view import HybridView, MLView
from components.query_processors.analyzers.ml_views.view_result import AnalysisMethod


# ---------------------------------------------------------------------------
# Concrete test subclasses
# ---------------------------------------------------------------------------

class ConcreteHybridView(HybridView):
    """HybridView with controllable algorithmic/ML stubs."""

    def __init__(self, *, alg_result=None, ml_result=None, alg_error=None, ml_error=None, **kw):
        self._alg_result = alg_result
        self._ml_result = ml_result
        self._alg_error = alg_error
        self._ml_error = ml_error
        super().__init__(view_name="test_hybrid", ml_model_name="stub", **kw)

    def _analyze_algorithmic(self, query):
        if self._alg_error:
            raise self._alg_error
        return self._alg_result

    def _analyze_ml(self, query):
        if self._ml_error:
            raise self._ml_error
        return self._ml_result


class ConcreteMLView(MLView):
    """MLView with controllable ML/fallback stubs."""

    def __init__(self, *, ml_result=None, fb_result=None, ml_error=None, fb_error=None, **kw):
        self._ml_result_val = ml_result
        self._fb_result_val = fb_result
        self._ml_error = ml_error
        self._fb_error = fb_error
        super().__init__(view_name="test_ml", ml_model_name="stub", **kw)

    def _analyze_ml(self, query):
        if self._ml_error:
            raise self._ml_error
        return self._ml_result_val

    def _analyze_algorithmic_fallback(self, query):
        if self._fb_error:
            raise self._fb_error
        return self._fb_result_val


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _result(score=0.7, confidence=0.9, features=None, metadata=None):
    return {
        "score": score,
        "confidence": confidence,
        "features": features or {},
        "metadata": metadata or {},
    }


# ---------------------------------------------------------------------------
# HybridView._combine_results — direct unit tests
# ---------------------------------------------------------------------------

class TestHybridViewCombine:
    """Tests for _combine_results weighted combination logic."""

    def test_both_succeed_weighted_combination(self):
        view = ConcreteHybridView(
            alg_result=_result(score=0.4, confidence=1.0),
            ml_result=_result(score=0.8, confidence=1.0),
        )
        # Default weights: alg 0.4, ml 0.6
        combined = view._combine_results(
            _result(score=0.4, confidence=1.0),
            _result(score=0.8, confidence=1.0),
        )
        expected_score = 0.4 * 0.4 + 0.6 * 0.8  # 0.64
        assert abs(combined["score"] - expected_score) < 1e-9
        assert combined["confidence"] > 0

    def test_ml_fails_algorithmic_only(self):
        view = ConcreteHybridView(alg_result=_result(score=0.5, confidence=0.9))
        combined = view._combine_results(_result(score=0.5, confidence=0.9), None)
        # Algorithmic only → confidence * 0.8 penalty
        assert abs(combined["confidence"] - 0.9 * 0.8) < 1e-9
        assert combined["metadata"]["combination_note"] == "algorithmic_only"

    def test_algorithmic_fails_ml_only(self):
        view = ConcreteHybridView(ml_result=_result(score=0.6, confidence=0.85))
        combined = view._combine_results(None, _result(score=0.6, confidence=0.85))
        assert abs(combined["confidence"] - 0.85 * 0.9) < 1e-9
        assert combined["metadata"]["combination_note"] == "ml_only"

    def test_both_fail_returns_default(self):
        view = ConcreteHybridView()
        combined = view._combine_results(None, None)
        assert combined["score"] == 0.5
        assert combined["confidence"] == 0.0
        assert combined["metadata"]["combination_error"] == "both_analyses_failed"


# ---------------------------------------------------------------------------
# HybridView.analyze (sync) paths
# ---------------------------------------------------------------------------

class TestHybridViewAnalyzeSync:

    def test_hybrid_mode_both_succeed(self):
        view = ConcreteHybridView(
            alg_result=_result(score=0.3, confidence=0.8),
            ml_result=_result(score=0.7, confidence=0.9),
        )
        result = view.analyze("test query", mode="auto")
        assert result.method == AnalysisMethod.HYBRID
        expected_score = 0.4 * 0.3 + 0.6 * 0.7  # 0.54
        assert abs(result.score - expected_score) < 1e-6

    def test_algorithmic_mode(self):
        view = ConcreteHybridView(
            alg_result=_result(score=0.4, confidence=0.85),
            ml_result=_result(score=0.9, confidence=0.95),
        )
        result = view.analyze("test query", mode="algorithmic")
        assert result.method == AnalysisMethod.ALGORITHMIC
        assert abs(result.score - 0.4) < 1e-6

    def test_ml_mode_no_model_falls_back_to_algorithmic(self):
        view = ConcreteHybridView(
            alg_result=_result(score=0.3, confidence=0.7),
            ml_result=_result(score=0.9, confidence=0.95),
        )
        # _ml_model is None → should fall back to algorithmic
        result = view.analyze("test query", mode="ml")
        assert result.method == AnalysisMethod.ALGORITHMIC

    def test_hybrid_ml_error_degrades_gracefully(self):
        view = ConcreteHybridView(
            alg_result=_result(score=0.5, confidence=0.8),
            ml_error=RuntimeError("model crash"),
        )
        result = view.analyze("test query", mode="hybrid")
        assert result.method == AnalysisMethod.HYBRID
        # ML failed → _combine_results gets None for ml → algorithmic_only path
        assert result.score > 0


# ---------------------------------------------------------------------------
# MLView.analyze (async) — ML primary with fallback
# ---------------------------------------------------------------------------

class TestMLViewAnalyze:

    @pytest.mark.asyncio
    async def test_ml_no_model_falls_back(self):
        """ML model unavailable → algorithmic fallback with 0.8× confidence."""
        view = ConcreteMLView(
            fb_result=_result(score=0.6, confidence=1.0),
        )
        # No model_manager, no _ml_model → falls through to fallback
        result = await view.analyze("test query", mode="auto")
        assert result.method == AnalysisMethod.FALLBACK
        # Confidence reduced by 0.8
        assert abs(result.confidence - 0.8) < 1e-6
        assert result.metadata.get("fallback_reason") == "ml_unavailable"

    @pytest.mark.asyncio
    async def test_algorithmic_mode_uses_fallback_directly(self):
        view = ConcreteMLView(
            fb_result=_result(score=0.4, confidence=0.9),
        )
        result = await view.analyze("test query", mode="algorithmic")
        assert result.method == AnalysisMethod.FALLBACK
        assert abs(result.confidence - 0.9 * 0.8) < 1e-6

    @pytest.mark.asyncio
    async def test_fallback_also_fails_returns_error_result(self):
        view = ConcreteMLView(
            fb_error=RuntimeError("all broken"),
        )
        result = await view.analyze("test query", mode="algorithmic")
        assert result.confidence == 0.0
        assert result.metadata.get("is_error") is True


# ---------------------------------------------------------------------------
# HybridView.analyze_async — async parallel path
# ---------------------------------------------------------------------------

class TestHybridViewAnalyzeAsync:

    @pytest.mark.asyncio
    async def test_async_hybrid_both_succeed(self):
        view = ConcreteHybridView(
            alg_result=_result(score=0.3, confidence=0.8),
            ml_result=_result(score=0.7, confidence=0.9),
        )
        # _get_ml_result checks _ml_model; set truthy so ML path runs
        view._ml_model = object()
        result = await view.analyze_async("test query", mode="auto")
        assert result.method == AnalysisMethod.HYBRID
        expected_score = 0.4 * 0.3 + 0.6 * 0.7
        assert abs(result.score - expected_score) < 1e-6

    @pytest.mark.asyncio
    async def test_async_algorithmic_mode(self):
        view = ConcreteHybridView(
            alg_result=_result(score=0.5, confidence=0.75),
        )
        result = await view.analyze_async("test query", mode="algorithmic")
        assert result.method == AnalysisMethod.ALGORITHMIC
        assert abs(result.score - 0.5) < 1e-6

    @pytest.mark.asyncio
    async def test_async_hybrid_ml_error(self):
        view = ConcreteHybridView(
            alg_result=_result(score=0.5, confidence=0.8),
            ml_error=RuntimeError("boom"),
        )
        result = await view.analyze_async("test query")
        assert result.method == AnalysisMethod.HYBRID
        # ML failed → algorithmic_only combination
        assert result.score > 0

    @pytest.mark.asyncio
    async def test_async_hybrid_both_fail(self):
        view = ConcreteHybridView(
            alg_error=RuntimeError("alg fail"),
            ml_error=RuntimeError("ml fail"),
        )
        result = await view.analyze_async("test query")
        assert result.method == AnalysisMethod.HYBRID
        assert result.score == 0.5
        assert result.confidence == 0.0
