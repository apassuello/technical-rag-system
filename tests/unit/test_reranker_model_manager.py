"""Unit tests for reranker ModelManager and CrossEncoderModels.

Tests cover ModelConfig dataclass, ModelManager lifecycle (load, predict,
unload, stats), and CrossEncoderModels multi-model orchestration. All ML
dependencies (sentence_transformers, torch) are mocked.
"""

import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from components.retrievers.rerankers.utils.model_manager import (
    CrossEncoderModels,
    ModelConfig,
    ModelInfo,
    ModelManager,
)


# ---------------------------------------------------------------------------
# ModelConfig dataclass
# ---------------------------------------------------------------------------

class TestModelConfig:
    """ModelConfig default values and field overrides."""

    def test_default_values(self):
        cfg = ModelConfig()
        assert cfg.name == "cross-encoder/ms-marco-MiniLM-L6-v2"
        assert cfg.backend == "sentence_transformers"
        assert cfg.model_type == "cross_encoder"
        assert cfg.max_length == 512
        assert cfg.device == "auto"
        assert cfg.batch_size == 16
        assert cfg.enable_quantization is False
        assert cfg.api_token is None
        assert cfg.fallback_to_local is True

    def test_custom_values(self):
        cfg = ModelConfig(
            name="custom-model",
            backend="huggingface_api",
            max_length=256,
            device="cpu",
            api_token="tok-123",
        )
        assert cfg.name == "custom-model"
        assert cfg.backend == "huggingface_api"
        assert cfg.max_length == 256
        assert cfg.device == "cpu"
        assert cfg.api_token == "tok-123"


# ---------------------------------------------------------------------------
# ModelInfo dataclass
# ---------------------------------------------------------------------------

class TestModelInfo:

    def test_default_values(self):
        info = ModelInfo(name="m", backend="b", device="cpu")
        assert info.loaded is False
        assert info.inference_count == 0
        assert info.error_count == 0


# ---------------------------------------------------------------------------
# ModelManager
# ---------------------------------------------------------------------------

class TestModelManagerInit:

    def test_initial_state(self):
        cfg = ModelConfig(name="test-model", device="cpu")
        mgr = ModelManager("test-model", cfg)

        assert mgr.name == "test-model"
        assert mgr.model is None
        assert mgr.info.loaded is False
        assert mgr.info.backend == "sentence_transformers"


class TestModelManagerLoad:

    @patch(
        "components.retrievers.rerankers.utils.model_manager.ModelManager._load_sentence_transformer"
    )
    def test_load_model_success(self, mock_load_st):
        cfg = ModelConfig(device="cpu")
        mgr = ModelManager("m1", cfg)

        result = mgr.load_model()

        assert result is True
        assert mgr.info.loaded is True
        assert mgr.info.load_time > 0
        mock_load_st.assert_called_once()

    @patch(
        "components.retrievers.rerankers.utils.model_manager.ModelManager._load_sentence_transformer"
    )
    def test_load_model_already_loaded_returns_cached(self, mock_load_st):
        cfg = ModelConfig(device="cpu")
        mgr = ModelManager("m1", cfg)

        mgr.load_model()
        result = mgr.load_model()

        assert result is True
        # Should only call load once
        mock_load_st.assert_called_once()

    @patch(
        "components.retrievers.rerankers.utils.model_manager.ModelManager._load_sentence_transformer",
        side_effect=RuntimeError("download failed"),
    )
    def test_load_model_failure_returns_false(self, mock_load_st):
        cfg = ModelConfig(device="cpu")
        mgr = ModelManager("m1", cfg)

        result = mgr.load_model()

        assert result is False
        assert mgr.info.loaded is False
        assert mgr.info.error_count == 1

    def test_load_unsupported_backend_returns_false(self):
        cfg = ModelConfig(backend="tensorflow", device="cpu")
        mgr = ModelManager("m1", cfg)

        result = mgr.load_model()

        assert result is False
        assert mgr.info.error_count == 1


class TestModelManagerPredict:

    def _make_loaded_manager(self):
        """Create a ModelManager with a mocked, already-loaded model."""
        cfg = ModelConfig(device="cpu")
        mgr = ModelManager("m1", cfg)
        mgr.model = MagicMock()
        mgr.model.predict.return_value = np.array([0.9, 0.1])
        mgr.info.loaded = True
        return mgr

    def test_predict_local_returns_list(self):
        mgr = self._make_loaded_manager()
        pairs = [["query", "doc1"], ["query", "doc2"]]

        scores = mgr.predict(pairs)

        assert scores == [0.9, 0.1]
        mgr.model.predict.assert_called_once_with(pairs)

    def test_predict_updates_stats(self):
        mgr = self._make_loaded_manager()

        mgr.predict([["q", "d"]])

        assert mgr.info.inference_count == 1
        assert mgr.info.total_inference_time > 0
        assert mgr.info.last_used > 0

    @patch(
        "components.retrievers.rerankers.utils.model_manager.ModelManager.load_model",
        return_value=False,
    )
    def test_predict_not_loaded_raises(self, mock_load):
        cfg = ModelConfig(device="cpu")
        mgr = ModelManager("m1", cfg)

        with pytest.raises(RuntimeError, match="not available"):
            mgr.predict([["q", "d"]])

    def test_predict_model_exception_increments_error_count(self):
        mgr = self._make_loaded_manager()
        mgr.model.predict.side_effect = RuntimeError("inference error")

        with pytest.raises(RuntimeError, match="inference error"):
            mgr.predict([["q", "d"]])

        assert mgr.info.error_count == 1


class TestModelManagerUnload:

    def test_unload_clears_model(self):
        cfg = ModelConfig(device="cpu")
        mgr = ModelManager("m1", cfg)
        mgr.model = MagicMock()
        mgr.info.loaded = True

        mgr.unload_model()

        assert mgr.model is None
        assert mgr.info.loaded is False

    def test_unload_when_not_loaded_is_noop(self):
        cfg = ModelConfig(device="cpu")
        mgr = ModelManager("m1", cfg)
        mgr.unload_model()  # should not raise
        assert mgr.model is None


class TestModelManagerStats:

    def test_get_stats_initial(self):
        cfg = ModelConfig(device="cpu")
        mgr = ModelManager("m1", cfg)
        stats = mgr.get_stats()

        assert stats["name"] == "m1"
        assert stats["loaded"] is False
        assert stats["inference_count"] == 0
        assert stats["avg_inference_time_ms"] == 0.0

    def test_get_stats_after_inference(self):
        cfg = ModelConfig(device="cpu")
        mgr = ModelManager("m1", cfg)
        mgr.model = MagicMock()
        mgr.model.predict.return_value = np.array([0.5])
        mgr.info.loaded = True

        mgr.predict([["q", "d"]])
        stats = mgr.get_stats()

        assert stats["inference_count"] == 1
        assert stats["avg_inference_time_ms"] > 0

    def test_get_info_returns_model_info(self):
        cfg = ModelConfig(device="cpu")
        mgr = ModelManager("m1", cfg)
        info = mgr.get_info()
        assert isinstance(info, ModelInfo)
        assert info.name == "m1"


# ---------------------------------------------------------------------------
# CrossEncoderModels
# ---------------------------------------------------------------------------

class TestCrossEncoderModelsInit:

    def test_init_creates_managers(self):
        configs = {
            "fast": ModelConfig(name="fast-model", device="cpu"),
            "quality": ModelConfig(name="quality-model", device="cpu"),
        }
        cem = CrossEncoderModels(configs)

        assert len(cem.managers) == 2
        assert cem.default_model == "fast"
        assert cem.get_available_models() == ["fast", "quality"]

    def test_init_empty_config(self):
        cem = CrossEncoderModels({})
        assert len(cem.managers) == 0
        assert cem.default_model is None


class TestCrossEncoderModelsPredict:

    def _make_cem_with_loaded_model(self):
        configs = {"m1": ModelConfig(device="cpu")}
        cem = CrossEncoderModels(configs)
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0.8, 0.2])
        cem.managers["m1"].model = mock_model
        cem.managers["m1"].info.loaded = True
        return cem

    def test_predict_uses_default_model(self):
        cem = self._make_cem_with_loaded_model()
        scores = cem.predict([["q", "d1"], ["q", "d2"]])
        assert scores == [0.8, 0.2]
        assert cem.stats["total_predictions"] == 1

    def test_predict_with_named_model(self):
        cem = self._make_cem_with_loaded_model()
        scores = cem.predict([["q", "d1"], ["q", "d2"]], model_name="m1")
        assert scores == [0.8, 0.2]

    def test_predict_empty_pairs_returns_empty(self):
        cem = self._make_cem_with_loaded_model()
        assert cem.predict([]) == []

    def test_predict_unknown_model_falls_back_to_default(self):
        cem = self._make_cem_with_loaded_model()
        scores = cem.predict([["q", "d"]], model_name="nonexistent")
        # Falls back to default "m1"
        assert isinstance(scores, list)

    def test_predict_no_models_raises(self):
        cem = CrossEncoderModels({})
        with pytest.raises(RuntimeError, match="No models available"):
            cem.predict([["q", "d"]])


class TestCrossEncoderModelsLifecycle:

    def test_is_model_loaded(self):
        configs = {"m1": ModelConfig(device="cpu")}
        cem = CrossEncoderModels(configs)
        assert cem.is_model_loaded("m1") is False
        assert cem.is_model_loaded("nonexistent") is False

    @patch(
        "components.retrievers.rerankers.utils.model_manager.ModelManager._load_sentence_transformer"
    )
    def test_load_model(self, mock_load_st):
        configs = {"m1": ModelConfig(device="cpu")}
        cem = CrossEncoderModels(configs)

        result = cem.load_model("m1")
        assert result is True
        assert cem.is_model_loaded("m1") is True

    def test_load_nonexistent_model(self):
        cem = CrossEncoderModels({})
        assert cem.load_model("nope") is False

    def test_unload_model(self):
        configs = {"m1": ModelConfig(device="cpu")}
        cem = CrossEncoderModels(configs)
        cem.managers["m1"].model = MagicMock()
        cem.managers["m1"].info.loaded = True

        cem.unload_model("m1")
        assert cem.is_model_loaded("m1") is False

    def test_unload_all_models(self):
        configs = {
            "m1": ModelConfig(device="cpu"),
            "m2": ModelConfig(device="cpu"),
        }
        cem = CrossEncoderModels(configs)
        for m in cem.managers.values():
            m.model = MagicMock()
            m.info.loaded = True

        cem.unload_all_models()
        assert not any(m.info.loaded for m in cem.managers.values())


class TestCrossEncoderModelsStats:

    def test_get_stats(self):
        configs = {"m1": ModelConfig(device="cpu")}
        cem = CrossEncoderModels(configs)
        stats = cem.get_stats()

        assert stats["total_models"] == 1
        assert stats["loaded_models"] == 0
        assert "models" in stats

    def test_reset_stats(self):
        configs = {"m1": ModelConfig(device="cpu")}
        cem = CrossEncoderModels(configs)
        cem.stats["total_predictions"] = 10

        cem.reset_stats()
        assert cem.stats["total_predictions"] == 0

    def test_get_model_stats(self):
        configs = {"m1": ModelConfig(device="cpu")}
        cem = CrossEncoderModels(configs)
        model_stats = cem.get_model_stats()

        assert "m1" in model_stats
        assert model_stats["m1"]["name"] == "m1"
