"""Unit tests for query processor ModelManager.

ModelManager is the central coordinator for ML model lifecycle: loading,
caching, memory management, quantization, and monitoring. All heavy deps
(transformers, torch, psutil) are mocked so tests run fast without GPU/ML.
"""

import asyncio
import time
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

pytestmark = [pytest.mark.unit]


# ---------------------------------------------------------------------------
# Helpers — build mock infrastructure so ModelManager.__init__ succeeds
# ---------------------------------------------------------------------------

def _make_mock_memory_monitor():
    """Return a MemoryMonitor mock with the API ModelManager actually calls."""
    mm = MagicMock()
    mm.start_monitoring = MagicMock()
    mm.stop_monitoring = MagicMock()
    mm.estimate_model_memory = MagicMock(return_value=300.0)
    mm.would_exceed_budget = MagicMock(return_value=False)
    mm.get_eviction_candidates = MagicMock(return_value={})
    mm.record_actual_model_memory = MagicMock()
    mm.get_epic1_memory_usage = MagicMock(return_value=100.0)

    # get_current_stats returns a MemoryStats-like object
    stats = MagicMock()
    stats.total_mb = 16384.0
    stats.used_mb = 4096.0
    stats.available_mb = 12288.0
    stats.epic1_process_mb = 100.0
    mm.get_current_stats = MagicMock(return_value=stats)

    mm.get_memory_pressure_level = MagicMock(return_value="low")
    return mm


def _make_mock_model_cache():
    """Return a ModelCache mock with the API ModelManager actually calls."""
    mc = MagicMock()
    mc.set_memory_monitor = MagicMock()
    mc.get = MagicMock(return_value=None)  # cache miss by default
    mc.put = MagicMock()
    mc.evict = MagicMock()
    mc.clear = MagicMock()

    cache_info = {
        "size": 0,
        "maxsize": 10,
        "total_memory_mb": 0.0,
    }
    mc.get_cache_info = MagicMock(return_value=cache_info)

    cache_stats = MagicMock()
    cache_stats.hit_rate = 0.0
    mc.get_stats = MagicMock(return_value=cache_stats)
    return mc


def _make_mock_perf_monitor():
    """Return a PerformanceMonitor mock."""
    pm = MagicMock()
    pm.record_request = MagicMock()
    pm.record_latency = MagicMock()
    pm.record_memory_usage = MagicMock()
    pm.log_performance_report = MagicMock()
    pm.shutdown = MagicMock()
    return pm


def _make_mock_quant_utils():
    """Return a QuantizationUtils mock."""
    qu = MagicMock()
    qu.quantize_transformer_model = MagicMock()
    return qu


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_infra():
    """Patch infrastructure deps so ModelManager.__init__ uses our mocks."""
    mm = _make_mock_memory_monitor()
    mc = _make_mock_model_cache()
    pm = _make_mock_perf_monitor()
    qu = _make_mock_quant_utils()

    base = "components.query_processors.analyzers.ml_models.model_manager"
    with (
        patch(f"{base}.MemoryMonitor", return_value=mm),
        patch(f"{base}.ModelCache", return_value=mc),
        patch(f"{base}.PerformanceMonitor", return_value=pm),
        patch(f"{base}.QuantizationUtils", return_value=qu),
    ):
        yield {
            "memory_monitor": mm,
            "model_cache": mc,
            "performance_monitor": pm,
            "quantization_utils": qu,
        }


@pytest.fixture
def manager(mock_infra):
    """Create a ModelManager with all infra mocked out."""
    from components.query_processors.analyzers.ml_models.model_manager import (
        ModelManager,
    )

    mgr = ModelManager(
        memory_budget_gb=2.0,
        cache_size=10,
        enable_quantization=True,
        enable_monitoring=True,
        model_timeout_seconds=5.0,
        max_concurrent_loads=2,
    )
    yield mgr
    # Shutdown to clean up executor threads
    mgr.shutdown()


@pytest.fixture
def manager_no_monitoring(mock_infra):
    """ModelManager with monitoring and quantization disabled."""
    from components.query_processors.analyzers.ml_models.model_manager import (
        ModelManager,
    )

    mgr = ModelManager(
        memory_budget_gb=1.0,
        cache_size=5,
        enable_quantization=False,
        enable_monitoring=False,
    )
    yield mgr
    mgr.shutdown()


# ===========================================================================
# Tests
# ===========================================================================


class TestModelManagerInit:
    """Constructor and default configuration."""

    def test_default_memory_budget(self, manager):
        assert manager.memory_budget_gb == 2.0
        assert manager.memory_budget_mb == 2.0 * 1024

    def test_default_configs_populated(self, manager):
        assert len(manager.model_configurations) == 5
        expected_keys = {"SciBERT", "DistilBERT", "DeBERTa-v3", "Sentence-BERT", "T5-small"}
        assert set(manager.model_configurations.keys()) == expected_keys

    def test_hf_name_reverse_mapping(self, manager):
        """Each model config should have a HuggingFace name -> config key mapping."""
        assert "allenai/scibert_scivocab_uncased" in manager._hf_name_to_config_key
        assert manager._hf_name_to_config_key["allenai/scibert_scivocab_uncased"] == "SciBERT"

    def test_memory_monitor_started(self, manager, mock_infra):
        mock_infra["memory_monitor"].start_monitoring.assert_called_once()

    def test_model_cache_has_memory_monitor(self, manager, mock_infra):
        mock_infra["model_cache"].set_memory_monitor.assert_called_once_with(
            mock_infra["memory_monitor"]
        )

    def test_quantization_disabled(self, manager_no_monitoring):
        assert manager_no_monitoring.quantization_utils is None

    def test_monitoring_disabled(self, manager_no_monitoring):
        assert manager_no_monitoring.performance_monitor is None

    def test_empty_registries_at_start(self, manager):
        assert manager.model_registry == {}
        assert manager.model_instances == {}
        assert manager._model_factories == {}


class TestModelConfigurations:
    """Verify the five default model configurations."""

    @pytest.mark.parametrize(
        "key,hf_name,model_type",
        [
            ("SciBERT", "allenai/scibert_scivocab_uncased", "transformers"),
            ("DistilBERT", "distilbert-base-uncased", "transformers"),
            ("DeBERTa-v3", "microsoft/deberta-v3-base", "transformers"),
            ("Sentence-BERT", "sentence-transformers/all-MiniLM-L6-v2", "sentence_transformers"),
            ("T5-small", "t5-small", "transformers"),
        ],
    )
    def test_config_entry(self, manager, key, hf_name, model_type):
        cfg = manager.model_configurations[key]
        assert cfg["model_name"] == hf_name
        assert cfg["model_type"] == model_type
        assert "estimated_memory_mb" in cfg
        assert isinstance(cfg["estimated_memory_mb"], (int, float))
        assert cfg["quantization_method"] == "dynamic"


class TestRegisterModelFactory:
    """register_model_factory stores callable keyed by model type."""

    def test_register_and_retrieve(self, manager):
        factory = MagicMock(return_value="fake_model")
        manager.register_model_factory("custom_model", factory)
        assert "custom_model" in manager._model_factories
        assert manager._model_factories["custom_model"] is factory


class TestLoadModelAsync:
    """Async load_model flow with cache hits, misses, and errors."""

    def test_cache_hit_returns_cached_model(self, manager, mock_infra):
        """When cache has the model, load_model returns it without loading."""
        sentinel = object()
        mock_infra["model_cache"].get.return_value = sentinel

        result = asyncio.run(
            manager.load_model("SciBERT")
        )

        assert result is sentinel
        mock_infra["model_cache"].get.assert_called_with("SciBERT")

    def test_cache_hit_updates_access_time(self, manager, mock_infra):
        """Cache hit should update last_accessed on the model registry entry."""
        from components.query_processors.analyzers.ml_models.model_manager import ModelInfo

        mock_infra["model_cache"].get.return_value = "cached"
        manager.model_registry["SciBERT"] = ModelInfo(
            name="SciBERT", model_type="SciBERT", status="loaded"
        )

        asyncio.run(manager.load_model("SciBERT"))

        assert manager.model_registry["SciBERT"].last_accessed is not None

    def test_force_reload_skips_cache(self, manager, mock_infra):
        """force_reload=True should bypass the cache and load fresh."""
        mock_infra["model_cache"].get.return_value = "cached"

        factory = MagicMock(return_value={"model": "fresh", "tokenizer": None})
        manager.register_model_factory("SciBERT", factory)

        result = asyncio.run(
            manager.load_model("SciBERT", force_reload=True)
        )

        # Cache.get should NOT have been called (force_reload skips cache check)
        mock_infra["model_cache"].get.assert_not_called()
        factory.assert_called_once()

    def test_load_via_registered_factory(self, manager, mock_infra):
        """Model loaded via factory goes through _load_model_sync and caches."""
        model_obj = {"model": MagicMock(), "tokenizer": MagicMock()}
        factory = MagicMock(return_value=model_obj)
        manager.register_model_factory("SciBERT", factory)

        result = asyncio.run(
            manager.load_model("SciBERT")
        )

        factory.assert_called_once()
        assert result is model_obj
        # Model should be in model_instances and registry
        assert "SciBERT" in manager.model_instances
        assert manager.model_registry["SciBERT"].status == "loaded"

    def test_load_via_hf_name_factory(self, manager, mock_infra):
        """Factory registered under config key is found when using HF model name."""
        model_obj = {"model": "scibert_model", "tokenizer": None}
        factory = MagicMock(return_value=model_obj)
        manager.register_model_factory("SciBERT", factory)

        result = asyncio.run(
            manager.load_model("allenai/scibert_scivocab_uncased")
        )

        factory.assert_called_once()
        assert result is model_obj

    def test_unknown_model_raises(self, manager, mock_infra):
        """Loading a model with no configuration should raise ModelLoadingError."""
        from components.query_processors.analyzers.ml_models.model_manager import (
            ModelLoadingError,
        )

        with pytest.raises(ModelLoadingError, match="No configuration found"):
            asyncio.run(
                manager.load_model("NonExistentModel")
            )

    def test_factory_exception_sets_error_status(self, manager, mock_infra):
        """If the factory raises, model status should be 'error'."""
        from components.query_processors.analyzers.ml_models.model_manager import (
            ModelLoadingError,
        )

        factory = MagicMock(side_effect=RuntimeError("GPU OOM"))
        manager.register_model_factory("SciBERT", factory)

        with pytest.raises(ModelLoadingError):
            asyncio.run(
                manager.load_model("SciBERT")
            )

        assert manager.model_registry["SciBERT"].status == "error"
        assert "GPU OOM" in manager.model_registry["SciBERT"].error_message

    def test_load_records_performance_metrics(self, manager, mock_infra):
        """Performance monitor should record request on load_model call."""
        factory = MagicMock(return_value="model")
        manager.register_model_factory("DistilBERT", factory)

        asyncio.run(
            manager.load_model("DistilBERT")
        )

        mock_infra["performance_monitor"].record_request.assert_called()


class TestGetModel:
    """get_model and get_model_info accessors."""

    def test_get_model_returns_none_when_not_loaded(self, manager):
        assert manager.get_model("SciBERT") is None

    def test_get_model_returns_instance_after_registration(self, manager):
        manager.model_instances["SciBERT"] = "fake_model"
        assert manager.get_model("SciBERT") == "fake_model"

    def test_get_model_info_returns_none_when_unknown(self, manager):
        assert manager.get_model_info("SciBERT") is None

    def test_get_model_info_returns_info(self, manager):
        from components.query_processors.analyzers.ml_models.model_manager import ModelInfo

        info = ModelInfo(name="SciBERT", model_type="SciBERT", status="loaded")
        manager.model_registry["SciBERT"] = info
        assert manager.get_model_info("SciBERT") is info


class TestListLoadedModels:
    """list_loaded_models filters by status == 'loaded'."""

    def test_empty_when_nothing_loaded(self, manager):
        assert manager.list_loaded_models() == []

    def test_only_loaded_models_returned(self, manager):
        from components.query_processors.analyzers.ml_models.model_manager import ModelInfo

        manager.model_registry["A"] = ModelInfo(name="A", model_type="A", status="loaded")
        manager.model_registry["B"] = ModelInfo(name="B", model_type="B", status="error")
        manager.model_registry["C"] = ModelInfo(name="C", model_type="C", status="loaded")

        loaded = manager.list_loaded_models()
        names = {m.name for m in loaded}
        assert names == {"A", "C"}


class TestMemoryUsageSummary:
    """get_memory_usage_summary aggregates info from monitor + cache."""

    def test_summary_structure(self, manager, mock_infra):
        summary = manager.get_memory_usage_summary()
        assert "system_memory" in summary
        assert "model_cache" in summary
        assert "memory_budget" in summary
        assert "loaded_models" in summary

    def test_budget_in_summary(self, manager, mock_infra):
        summary = manager.get_memory_usage_summary()
        assert summary["memory_budget"]["budget_mb"] == 2.0 * 1024

    def test_system_memory_from_monitor(self, manager, mock_infra):
        summary = manager.get_memory_usage_summary()
        assert summary["system_memory"]["total_mb"] == 16384.0
        assert summary["system_memory"]["available_mb"] == 12288.0


class TestEviction:
    """Model eviction removes from cache, instances, and registry."""

    def test_evict_model(self, manager, mock_infra):
        from components.query_processors.analyzers.ml_models.model_manager import ModelInfo

        manager.model_instances["old_model"] = "instance"
        manager.model_registry["old_model"] = ModelInfo(
            name="old_model", model_type="old_model", status="loaded", memory_mb=300.0
        )

        asyncio.run(
            manager._evict_model("old_model")
        )

        mock_infra["model_cache"].evict.assert_called_with("old_model")
        assert "old_model" not in manager.model_instances
        assert manager.model_registry["old_model"].status == "unloaded"
        assert manager.model_registry["old_model"].memory_mb is None


class TestShutdown:
    """shutdown clears all state and stops monitoring."""

    def test_shutdown_clears_everything(self, mock_infra):
        """Create manager, populate state, shutdown, verify cleared."""
        from components.query_processors.analyzers.ml_models.model_manager import (
            ModelManager,
            ModelInfo,
        )

        mgr = ModelManager(memory_budget_gb=1.0)
        mgr.model_registry["X"] = ModelInfo(name="X", model_type="X", status="loaded")
        mgr.model_instances["X"] = "instance"

        mgr.shutdown()

        assert len(mgr.model_registry) == 0
        assert len(mgr.model_instances) == 0
        mock_infra["memory_monitor"].stop_monitoring.assert_called()
        mock_infra["model_cache"].clear.assert_called()

    def test_context_manager_calls_shutdown(self, mock_infra):
        from components.query_processors.analyzers.ml_models.model_manager import ModelManager

        with ModelManager(memory_budget_gb=1.0) as mgr:
            pass

        mock_infra["memory_monitor"].stop_monitoring.assert_called()
        mock_infra["model_cache"].clear.assert_called()


class TestModelInfo:
    """Dataclass basics for ModelInfo."""

    def test_defaults(self):
        from components.query_processors.analyzers.ml_models.model_manager import ModelInfo

        info = ModelInfo(name="test", model_type="bert", status="unloaded")
        assert info.memory_mb is None
        assert info.quantized is False
        assert info.metadata == {}

    def test_metadata_not_shared(self):
        """Each instance should get its own metadata dict."""
        from components.query_processors.analyzers.ml_models.model_manager import ModelInfo

        a = ModelInfo(name="a", model_type="a", status="unloaded")
        b = ModelInfo(name="b", model_type="b", status="unloaded")
        a.metadata["key"] = "value"
        assert "key" not in b.metadata


class TestModelLoadingError:
    """ModelLoadingError is a plain Exception subclass."""

    def test_is_exception(self):
        from components.query_processors.analyzers.ml_models.model_manager import (
            ModelLoadingError,
        )

        err = ModelLoadingError("boom")
        assert isinstance(err, Exception)
        assert str(err) == "boom"


class TestLoadModelDefault:
    """_load_model_default dispatches to transformers or sentence_transformers."""

    def test_unsupported_model_type_raises(self, manager):
        from components.query_processors.analyzers.ml_models.model_manager import (
            ModelLoadingError,
        )

        config = {"model_type": "unknown_framework", "model_name": "foo"}
        with pytest.raises(ModelLoadingError, match="Unsupported model type"):
            manager._load_model_default("foo", config)

    def test_transformers_import_error_raises(self, manager):
        """When transformers is not importable, raise ModelLoadingError."""
        from components.query_processors.analyzers.ml_models.model_manager import (
            ModelLoadingError,
        )

        config = {"model_type": "transformers", "model_name": "test-model"}

        with patch("builtins.__import__", side_effect=ImportError("no transformers")):
            with pytest.raises(ModelLoadingError, match="transformers library not available"):
                manager._load_model_default("test-model", config)

    def test_sentence_transformers_import_error_raises(self, manager):
        """When sentence-transformers is not importable, raise ModelLoadingError."""
        from components.query_processors.analyzers.ml_models.model_manager import (
            ModelLoadingError,
        )

        config = {"model_type": "sentence_transformers", "model_name": "test-model"}

        with patch("builtins.__import__", side_effect=ImportError("no sentence_transformers")):
            with pytest.raises(ModelLoadingError, match="sentence-transformers library not available"):
                manager._load_model_default("test-model", config)


class TestLogStatusReport:
    """log_status_report delegates to get_memory_usage_summary and perf monitor."""

    def test_log_status_report_runs_without_error(self, manager, mock_infra):
        """Smoke test: log_status_report should not raise."""
        manager.log_status_report()
        # Performance monitor should have its report logged
        mock_infra["performance_monitor"].log_performance_report.assert_called_once()
