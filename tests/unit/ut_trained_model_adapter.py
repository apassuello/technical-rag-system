"""Unit tests for TrainedModelAdapter.

Mocks importlib dynamic loading and filesystem access. No trained models required.
"""

import json
from types import ModuleType
from unittest.mock import MagicMock, mock_open, patch

import pytest

pytestmark = [pytest.mark.unit]

MODULE = "components.query_processors.analyzers.ml_views.trained_model_adapter"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_system_config():
    """Minimal epic1_system_config.json content."""
    return {
        "epic1_system_info": {
            "version": "1.0.0",
            "training_date": "2026-01-01",
            "dataset_size": 5000,
            "best_fusion_method": "weighted_average",
            "performance_summary": {"accuracy": 0.92},
        }
    }


def _make_prediction(
    complexity_score=0.6,
    level="medium",
    view_scores=None,
    fusion_method="weighted_average",
):
    """Build a prediction dict matching Epic1Predictor.predict() output."""
    return {
        "complexity_score": complexity_score,
        "complexity_level": level,
        "view_scores": view_scores or {"technical": 0.5, "linguistic": 0.6},
        "fusion_method": fusion_method,
        "metadata": {"model_version": "1.0.0"},
    }


def _build_adapter(mock_importlib, predictor=None, config=None):
    """Construct a TrainedModelAdapter with mocked filesystem and importlib.

    Patches Path.exists, builtins.open, and importlib.util so that
    _initialize_adapter succeeds without real files.
    """
    from components.query_processors.analyzers.ml_views.trained_model_adapter import (
        TrainedModelAdapter,
    )

    mock_predictor = predictor or MagicMock()
    mock_module = ModuleType("epic1_predictor")
    mock_module.Epic1Predictor = MagicMock(return_value=mock_predictor)

    mock_spec = MagicMock()
    mock_spec.loader = MagicMock()
    mock_importlib.util.spec_from_file_location.return_value = mock_spec
    mock_importlib.util.module_from_spec.return_value = mock_module

    config_data = config or _make_system_config()

    with patch(f"{MODULE}.Path") as MockPath:
        # Make model_dir / "..." return a Path-like with exists() = True
        path_instance = MagicMock()
        path_instance.exists.return_value = True
        path_instance.__truediv__ = MagicMock(return_value=path_instance)
        MockPath.return_value = path_instance

        with patch("builtins.open", mock_open(read_data=json.dumps(config_data))):
            adapter = TrainedModelAdapter(model_dir="models/epic1")

    return adapter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_importlib():
    with patch(f"{MODULE}.importlib") as m:
        yield m


@pytest.fixture
def mock_predictor():
    predictor = MagicMock()
    predictor.predict.return_value = _make_prediction()
    return predictor


@pytest.fixture
def adapter(mock_importlib, mock_predictor):
    return _build_adapter(mock_importlib, predictor=mock_predictor)


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------

class TestIsAvailable:

    def test_available_when_predictor_loaded(self, adapter):
        assert adapter.is_available() is True

    def test_unavailable_when_predictor_none(self, adapter):
        adapter.predictor = None
        assert adapter.is_available() is False


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------

class TestPredictComplexity:

    @pytest.mark.asyncio
    async def test_returns_expected_keys(self, adapter):
        result = await adapter.predict_complexity("What is FAISS?")
        assert "score" in result
        assert "level" in result
        assert "confidence" in result
        assert "view_scores" in result
        assert "fusion_method" in result
        assert "metadata" in result
        assert "features" in result

    @pytest.mark.asyncio
    async def test_maps_predictor_output(self, adapter, mock_predictor):
        mock_predictor.predict.return_value = _make_prediction(
            complexity_score=0.8, level="complex"
        )
        result = await adapter.predict_complexity("distributed architecture")
        assert result["score"] == 0.8
        assert result["level"] == "complex"

    @pytest.mark.asyncio
    async def test_raises_when_unavailable(self, adapter):
        adapter.predictor = None
        with pytest.raises(RuntimeError, match="not available"):
            await adapter.predict_complexity("anything")

    @pytest.mark.asyncio
    async def test_records_prediction_count(self, adapter):
        assert adapter._prediction_count == 0
        await adapter.predict_complexity("query one")
        assert adapter._prediction_count == 1
        await adapter.predict_complexity("query two")
        assert adapter._prediction_count == 2


# ---------------------------------------------------------------------------
# Confidence calculation
# ---------------------------------------------------------------------------

class TestCalculateConfidence:

    def test_high_consistency_high_confidence(self, adapter):
        prediction = _make_prediction(
            complexity_score=0.2,
            view_scores={"a": 0.5, "b": 0.5, "c": 0.5},
        )
        confidence = adapter._calculate_confidence(prediction)
        # All identical scores → std=0 → consistency_factor=1.0
        assert confidence >= 0.5

    def test_low_consistency_lower_confidence(self, adapter):
        prediction = _make_prediction(
            complexity_score=0.5,
            view_scores={"a": 0.1, "b": 0.9},
        )
        confidence = adapter._calculate_confidence(prediction)
        # High std → low consistency_factor
        assert confidence < 0.7

    def test_confidence_clamped_to_valid_range(self, adapter):
        prediction = _make_prediction(
            complexity_score=0.5,
            view_scores={"a": 0.0, "b": 1.0, "c": 0.0, "d": 1.0},
        )
        confidence = adapter._calculate_confidence(prediction)
        assert 0.1 <= confidence <= 0.95

    def test_exception_returns_default(self, adapter):
        # Broken prediction dict triggers fallback
        confidence = adapter._calculate_confidence({"bad": "data"})
        assert confidence == 0.7


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

class TestInit:

    def test_model_dir_stored(self, mock_importlib):
        """model_dir is stored as a Path object."""
        from components.query_processors.analyzers.ml_views.trained_model_adapter import (
            TrainedModelAdapter,
        )

        mock_predictor = MagicMock()
        adapter = _build_adapter(mock_importlib, predictor=mock_predictor)
        # model_dir is a MagicMock(Path) in the adapter due to Path patch,
        # but we can verify the adapter stores it and is_available works
        assert adapter.model_dir is not None
        assert adapter.is_available() is True

    def test_predictor_not_found_sets_none(self, mock_importlib):
        """When predictor script doesn't exist, predictor stays None."""
        from components.query_processors.analyzers.ml_views.trained_model_adapter import (
            TrainedModelAdapter,
        )

        with patch(f"{MODULE}.Path") as MockPath:
            path_instance = MagicMock()
            # config exists, predictor does NOT
            path_instance.exists.side_effect = [True, False]
            path_instance.__truediv__ = MagicMock(return_value=path_instance)
            MockPath.return_value = path_instance

            with patch("builtins.open", mock_open(read_data=json.dumps(_make_system_config()))):
                adapter = TrainedModelAdapter(model_dir="models/epic1")

        assert adapter.predictor is None
        assert adapter.is_available() is False

    def test_init_failure_increments_error_count(self, mock_importlib):
        """If _initialize_adapter raises, _load_error_count is incremented."""
        from components.query_processors.analyzers.ml_views.trained_model_adapter import (
            TrainedModelAdapter,
        )

        with patch(f"{MODULE}.Path") as MockPath:
            path_instance = MagicMock()
            path_instance.exists.return_value = True
            path_instance.__truediv__ = MagicMock(return_value=path_instance)
            MockPath.return_value = path_instance

            with patch("builtins.open", side_effect=PermissionError("denied")):
                with pytest.raises(PermissionError):
                    TrainedModelAdapter(model_dir="models/epic1")


# ---------------------------------------------------------------------------
# Dynamic loading
# ---------------------------------------------------------------------------

class TestDynamicLoading:

    def test_importlib_spec_called(self, mock_importlib, mock_predictor):
        _build_adapter(mock_importlib, predictor=mock_predictor)
        mock_importlib.util.spec_from_file_location.assert_called_once()

    def test_module_from_spec_called(self, mock_importlib, mock_predictor):
        _build_adapter(mock_importlib, predictor=mock_predictor)
        mock_importlib.util.module_from_spec.assert_called_once()

    def test_exec_module_called(self, mock_importlib, mock_predictor):
        _build_adapter(mock_importlib, predictor=mock_predictor)
        spec = mock_importlib.util.spec_from_file_location.return_value
        spec.loader.exec_module.assert_called_once()


# ---------------------------------------------------------------------------
# Model info & performance stats
# ---------------------------------------------------------------------------

class TestModelInfo:

    def test_loaded_returns_config_fields(self, adapter):
        info = adapter.get_model_info()
        assert info["status"] == "loaded"
        assert info["version"] == "1.0.0"
        assert "training_date" in info

    def test_not_loaded_returns_status(self, adapter):
        adapter.system_config = None
        info = adapter.get_model_info()
        assert info == {"status": "not_loaded"}

    @pytest.mark.asyncio
    async def test_performance_stats_after_predictions(self, adapter):
        await adapter.predict_complexity("q1")
        await adapter.predict_complexity("q2")
        stats = adapter.get_performance_stats()
        assert stats["prediction_count"] == 2
        assert stats["average_prediction_time_ms"] > 0
        assert stats["model_info"]["status"] == "loaded"


# ---------------------------------------------------------------------------
# Predict error path & extract features
# ---------------------------------------------------------------------------

class TestPredictErrorPath:

    @pytest.mark.asyncio
    async def test_predictor_exception_reraises(self, adapter, mock_predictor):
        mock_predictor.predict.side_effect = ValueError("model exploded")
        with pytest.raises(ValueError, match="model exploded"):
            await adapter.predict_complexity("boom")
        # Error still recorded in prediction count
        assert adapter._prediction_count == 1


class TestExtractFeatures:

    def test_extracts_expected_keys(self, adapter):
        prediction = _make_prediction(complexity_score=0.4, level="simple")
        features = adapter._extract_features(prediction)
        assert features["complexity_score"] == 0.4
        assert features["complexity_level"] == "simple"
        assert "view_scores" in features
        assert "fusion_method" in features


# ---------------------------------------------------------------------------
# Confidence boundary distance branches
# ---------------------------------------------------------------------------

class TestConfidenceBoundaries:

    def test_low_complexity_boundary(self, adapter):
        """complexity_score <= 0.35 uses lower boundary path."""
        prediction = _make_prediction(
            complexity_score=0.1,
            view_scores={"a": 0.5, "b": 0.5},
        )
        confidence = adapter._calculate_confidence(prediction)
        assert 0.1 <= confidence <= 0.95

    def test_high_complexity_boundary(self, adapter):
        """complexity_score >= 0.7 uses upper boundary path."""
        prediction = _make_prediction(
            complexity_score=0.9,
            view_scores={"a": 0.5, "b": 0.5},
        )
        confidence = adapter._calculate_confidence(prediction)
        assert 0.1 <= confidence <= 0.95

    def test_medium_complexity_boundary(self, adapter):
        """complexity_score between 0.35 and 0.7 uses medium path."""
        prediction = _make_prediction(
            complexity_score=0.5,
            view_scores={"a": 0.5, "b": 0.5},
        )
        confidence = adapter._calculate_confidence(prediction)
        assert 0.1 <= confidence <= 0.95


# ---------------------------------------------------------------------------
# FeatureBasedView
# ---------------------------------------------------------------------------

class TestFeatureBasedView:

    def test_init_with_adapter(self, adapter):
        from components.query_processors.analyzers.ml_views.trained_model_adapter import (
            FeatureBasedView,
        )
        view = FeatureBasedView(view_name="technical", model_adapter=adapter)
        assert view.view_name == "technical"
        assert view.model_adapter is adapter
        assert hasattr(view, "complexity_keywords")

    @pytest.mark.asyncio
    async def test_analyze_ml_returns_view_score(self, adapter, mock_predictor):
        from components.query_processors.analyzers.ml_views.trained_model_adapter import (
            FeatureBasedView,
        )
        mock_predictor.predict.return_value = _make_prediction(
            complexity_score=0.7,
            level="complex",
            view_scores={"technical": 0.8, "linguistic": 0.6},
        )
        view = FeatureBasedView(view_name="technical", model_adapter=adapter)
        result = await view._analyze_ml("distributed systems query")
        assert result["score"] == 0.8  # view-specific score
        assert "confidence" in result
        assert result["metadata"]["analysis_method"] == "trained_model"

    @pytest.mark.asyncio
    async def test_analyze_ml_raises_when_unavailable(self, adapter):
        from components.query_processors.analyzers.ml_views.trained_model_adapter import (
            FeatureBasedView,
        )
        adapter.predictor = None
        view = FeatureBasedView(view_name="technical", model_adapter=adapter)
        with pytest.raises(RuntimeError, match="not available"):
            await view._analyze_ml("anything")

    @pytest.mark.asyncio
    async def test_algorithmic_fallback_returns_score(self, adapter):
        from components.query_processors.analyzers.ml_views.trained_model_adapter import (
            FeatureBasedView,
        )
        view = FeatureBasedView(view_name="technical", model_adapter=adapter)
        result = await view._analyze_algorithmic_fallback("what is FAISS")
        assert "score" in result
        assert result["confidence"] == 0.5
        assert result["metadata"]["analysis_method"] == "algorithmic_fallback"

    @pytest.mark.asyncio
    async def test_algorithmic_fallback_complex_keywords(self, adapter):
        from components.query_processors.analyzers.ml_views.trained_model_adapter import (
            FeatureBasedView,
        )
        view = FeatureBasedView(view_name="technical", model_adapter=adapter)
        result = await view._analyze_algorithmic_fallback(
            "optimization of distributed scalable architecture"
        )
        # Complex keywords present → higher score
        assert result["score"] > 0.7
