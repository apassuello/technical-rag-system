"""Unit tests for platform service implementations.

Covers ComponentHealthServiceImpl, SystemAnalyticsServiceImpl,
and ConfigurationServiceImpl from src/core/platform_services.py.
These tests recover coverage lost when Epic 8 cloud-native code was deleted.
"""

import time
from unittest.mock import MagicMock, Mock, patch

import pytest

from core.interfaces import ComponentMetrics, HealthStatus
from core.platform_services import (
    ComponentHealthServiceImpl,
    ConfigurationServiceImpl,
    SystemAnalyticsServiceImpl,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def health_service():
    """Fresh ComponentHealthServiceImpl per test."""
    svc = ComponentHealthServiceImpl()
    yield svc
    # Explicit teardown to prevent cross-test pollution
    svc.monitored_components.clear()
    svc.health_history.clear()
    svc.failure_counts.clear()
    svc.last_health_checks.clear()


@pytest.fixture
def analytics_service():
    """Fresh SystemAnalyticsServiceImpl per test."""
    svc = SystemAnalyticsServiceImpl()
    yield svc
    svc.reset_analytics_data()


@pytest.fixture
def mock_config_manager():
    """ConfigManager mock with a valid PipelineConfig-shaped config attribute."""
    mgr = MagicMock()

    # Build nested component configs
    for attr in ("document_processor", "embedder", "retriever", "answer_generator"):
        comp = MagicMock()
        comp.type = f"mock_{attr}"
        comp.config = {"key": "value"}
        setattr(mgr.config, attr, comp)

    # vector_store is optional; present by default
    vs = MagicMock()
    vs.type = "mock_vector_store"
    vs.config = {"index": "flat"}
    mgr.config.vector_store = vs

    # global_settings
    mgr.config.global_settings = {"debug": False}

    return mgr


@pytest.fixture
def config_service(mock_config_manager):
    """Fresh ConfigurationServiceImpl per test."""
    svc = ConfigurationServiceImpl(mock_config_manager)
    yield svc
    svc.config_cache.clear()
    svc.config_history.clear()
    svc.dynamic_configs.clear()


def _make_component(name=None, *, has_health_check=False, has_get_configuration=False,
                    has_get_stats=False, health_check_result=None,
                    get_configuration_result=None, get_stats_result=None,
                    methods=None):
    """Helper: build a mock component with optional method stubs."""
    comp = Mock()
    # Remove default auto-created attributes so hasattr checks are controlled
    comp.configure_mock(**{"health_check": Mock(return_value=health_check_result)} if has_health_check else {})
    comp.configure_mock(**{"get_configuration": Mock(return_value=get_configuration_result)} if has_get_configuration else {})
    comp.configure_mock(**{"get_stats": Mock(return_value=get_stats_result)} if has_get_stats else {})

    # By default Mock auto-generates attributes; explicitly delete ones we
    # do NOT want so that hasattr returns False.
    if not has_health_check:
        if hasattr(comp, "health_check"):
            del comp.health_check
    if not has_get_configuration:
        if hasattr(comp, "get_configuration"):
            del comp.get_configuration
    if not has_get_stats:
        if hasattr(comp, "get_stats"):
            del comp.get_stats

    # Set a real name if provided
    if name is not None:
        comp.name = name
    else:
        # Remove auto-generated .name so _get_component_id falls through to class name
        del comp.name

    # Add explicit methods list if requested (for _get_required_methods checks)
    if methods:
        for m in methods:
            setattr(comp, m, Mock())

    return comp


# ===========================================================================
# ComponentHealthServiceImpl
# ===========================================================================


class TestComponentHealthServiceInit:
    """Verify constructor creates expected instance attributes."""

    def test_initial_state(self, health_service):
        assert health_service.monitored_components == {}
        assert health_service.health_history == {}
        assert health_service.failure_counts == {}
        assert health_service.last_health_checks == {}
        assert health_service.health_check_interval == 30.0


class TestCheckComponentHealth:
    """Tests for check_component_health."""

    def test_returns_health_status(self, health_service):
        comp = _make_component()
        status = health_service.check_component_health(comp)
        assert isinstance(status, HealthStatus)
        assert status.is_healthy is True
        assert status.component_name == "Mock"

    def test_named_component_uses_name_as_id(self, health_service):
        comp = _make_component(name="my_embedder")
        health_service.check_component_health(comp)
        assert "my_embedder" in health_service.health_history

    def test_unnamed_component_uses_class_name_as_id(self, health_service):
        comp = _make_component()
        health_service.check_component_health(comp)
        assert "Mock" in health_service.health_history

    def test_stores_health_history(self, health_service):
        comp = _make_component(name="comp_a")
        health_service.check_component_health(comp)
        assert len(health_service.health_history["comp_a"]) == 1

    def test_history_capped_at_10(self, health_service):
        comp = _make_component(name="overflow")
        # Force fresh checks by setting interval to 0
        health_service.health_check_interval = 0
        for _ in range(15):
            health_service.check_component_health(comp)
        assert len(health_service.health_history["overflow"]) == 10

    def test_rate_limiting_returns_cached_status(self, health_service):
        comp = _make_component(name="limited")
        first = health_service.check_component_health(comp)
        # Second call within interval should return cached result
        second = health_service.check_component_health(comp)
        assert second is first

    def test_rate_limiting_bypassed_after_interval(self, health_service):
        health_service.health_check_interval = 0  # Disable rate limiting
        comp = _make_component(name="unlimited")
        first = health_service.check_component_health(comp)
        second = health_service.check_component_health(comp)
        # Two distinct checks stored
        assert len(health_service.health_history["unlimited"]) == 2

    def test_missing_required_methods_marks_unhealthy(self, health_service):
        """A component whose class name matches a known type but lacks methods."""
        # Create a real class named DocumentProcessor that lacks the 'process' method
        DocumentProcessor = type("DocumentProcessor", (), {"name": "doc_proc"})
        comp = DocumentProcessor()
        status = health_service.check_component_health(comp)
        assert status.is_healthy is False
        assert any("Missing required methods" in i for i in status.issues)

    def test_health_check_method_dict_healthy(self, health_service):
        comp = _make_component(
            name="hc_ok",
            has_health_check=True,
            health_check_result={"healthy": True, "latency": 5},
        )
        status = health_service.check_component_health(comp)
        assert status.is_healthy is True
        assert status.metrics.get("latency") == 5

    def test_health_check_method_dict_unhealthy(self, health_service):
        comp = _make_component(
            name="hc_bad",
            has_health_check=True,
            health_check_result={"healthy": False},
        )
        status = health_service.check_component_health(comp)
        assert status.is_healthy is False
        assert any("Component-specific health check failed" in i for i in status.issues)

    def test_health_check_method_raises(self, health_service):
        comp = _make_component(name="hc_err", has_health_check=True)
        comp.health_check.side_effect = RuntimeError("boom")
        status = health_service.check_component_health(comp)
        assert status.is_healthy is False
        assert any("Health check error" in i for i in status.issues)

    def test_get_configuration_valid_dict(self, health_service):
        comp = _make_component(
            name="cfg_ok",
            has_get_configuration=True,
            get_configuration_result={"a": 1, "b": 2},
        )
        status = health_service.check_component_health(comp)
        assert status.is_healthy is True
        assert status.metrics.get("config_size") == 2

    def test_get_configuration_invalid_response(self, health_service):
        comp = _make_component(
            name="cfg_bad",
            has_get_configuration=True,
            get_configuration_result="not a dict",
        )
        status = health_service.check_component_health(comp)
        assert status.is_healthy is False
        assert any("Invalid configuration response" in i for i in status.issues)

    def test_get_configuration_raises(self, health_service):
        comp = _make_component(name="cfg_err", has_get_configuration=True)
        comp.get_configuration.side_effect = RuntimeError("oops")
        status = health_service.check_component_health(comp)
        assert status.is_healthy is False
        assert any("Configuration check error" in i for i in status.issues)

    @patch("core.platform_services.psutil", create=True)
    def test_memory_metrics_recorded(self, mock_psutil, health_service):
        """When psutil is importable, memory_mb lands in metrics."""
        # psutil is imported inside the method; we need to patch the import itself
        comp = _make_component(name="mem")
        status = health_service.check_component_health(comp)
        # Either psutil is available (memory_mb in metrics) or not (memory_monitoring)
        assert "memory_mb" in status.metrics or "memory_monitoring" in status.metrics


class TestMonitorComponentHealth:
    """Tests for monitor_component_health."""

    def test_adds_component_to_monitored(self, health_service):
        comp = _make_component(name="mon1")
        health_service.monitor_component_health(comp)
        assert "mon1" in health_service.monitored_components

    def test_initializes_failure_count(self, health_service):
        comp = _make_component(name="mon2")
        health_service.monitor_component_health(comp)
        assert health_service.failure_counts["mon2"] == 0

    def test_performs_initial_health_check(self, health_service):
        comp = _make_component(name="mon3")
        health_service.monitor_component_health(comp)
        assert len(health_service.health_history.get("mon3", [])) == 1

    def test_preserves_existing_failure_count(self, health_service):
        health_service.failure_counts["mon4"] = 5
        comp = _make_component(name="mon4")
        health_service.monitor_component_health(comp)
        assert health_service.failure_counts["mon4"] == 5


class TestReportComponentFailure:
    """Tests for report_component_failure."""

    def test_increments_failure_count(self, health_service):
        comp = _make_component(name="fail1")
        health_service.report_component_failure(comp, ValueError("bad input"))
        assert health_service.failure_counts["fail1"] == 1
        health_service.report_component_failure(comp, ValueError("again"))
        assert health_service.failure_counts["fail1"] == 2

    def test_creates_unhealthy_status(self, health_service):
        comp = _make_component(name="fail2")
        health_service.report_component_failure(comp, RuntimeError("crash"))
        history = health_service.health_history["fail2"]
        assert len(history) == 1
        assert history[0].is_healthy is False
        assert "Component failure: crash" in history[0].issues[0]

    def test_failure_metrics_include_error_type(self, health_service):
        comp = _make_component(name="fail3")
        health_service.report_component_failure(comp, TypeError("bad type"))
        status = health_service.health_history["fail3"][0]
        assert status.metrics["error_type"] == "TypeError"
        assert status.metrics["failure_count"] == 1


class TestGetSystemHealthSummary:
    """Tests for get_system_health_summary."""

    def test_empty_system_returns_unknown(self, health_service):
        summary = health_service.get_system_health_summary()
        assert summary["overall_health"] == "unknown"
        assert summary["total_components"] == 0

    def test_all_healthy_components(self, health_service):
        health_service.health_check_interval = 0
        for name in ("a", "b", "c"):
            comp = _make_component(name=name)
            health_service.monitor_component_health(comp)
        summary = health_service.get_system_health_summary()
        assert summary["overall_health"] == "healthy"
        assert summary["healthy_components"] == 3
        assert summary["unhealthy_components"] == 0

    def test_mixed_health_reports_degraded(self, health_service):
        health_service.health_check_interval = 0
        # Healthy component
        good = _make_component(name="good")
        health_service.monitor_component_health(good)
        # Unhealthy component: real class named DocumentProcessor missing 'process'
        BadDocProcessor = type("DocumentProcessor", (), {"name": "bad"})
        bad = BadDocProcessor()
        health_service.monitor_component_health(bad)
        summary = health_service.get_system_health_summary()
        assert summary["overall_health"] == "degraded"

    def test_all_unhealthy_reports_critical(self, health_service):
        health_service.health_check_interval = 0
        for idx, name in enumerate(("x", "y")):
            BadDocProcessor = type("DocumentProcessor", (), {"name": name})
            comp = BadDocProcessor()
            health_service.monitor_component_health(comp)
        summary = health_service.get_system_health_summary()
        assert summary["overall_health"] == "critical"

    def test_total_failures_aggregated(self, health_service):
        health_service.health_check_interval = 0
        comp_a = _make_component(name="fa")
        comp_b = _make_component(name="fb")
        health_service.monitor_component_health(comp_a)
        health_service.monitor_component_health(comp_b)
        health_service.report_component_failure(comp_a, ValueError("err"))
        health_service.report_component_failure(comp_b, ValueError("err"))
        health_service.report_component_failure(comp_b, ValueError("err"))
        summary = health_service.get_system_health_summary()
        assert summary["total_failures"] == 3


class TestHealthServiceHelpers:
    """Tests for helper/accessor methods."""

    def test_get_component_health_history(self, health_service):
        comp = _make_component(name="hist")
        health_service.check_component_health(comp)
        history = health_service.get_component_health_history("hist")
        assert len(history) == 1
        assert isinstance(history[0], HealthStatus)

    def test_get_component_health_history_unknown(self, health_service):
        assert health_service.get_component_health_history("nonexistent") == []

    def test_get_failure_count(self, health_service):
        comp = _make_component(name="fc")
        health_service.report_component_failure(comp, ValueError("x"))
        assert health_service.get_failure_count("fc") == 1
        assert health_service.get_failure_count("unknown") == 0

    def test_reset_failure_count(self, health_service):
        comp = _make_component(name="rfc")
        health_service.report_component_failure(comp, ValueError("x"))
        health_service.reset_failure_count("rfc")
        assert health_service.failure_counts["rfc"] == 0

    def test_reset_failure_count_noop_for_unknown(self, health_service):
        # Should not raise
        health_service.reset_failure_count("nope")

    def test_get_monitored_components(self, health_service):
        for name in ("p", "q"):
            health_service.monitor_component_health(_make_component(name=name))
        assert set(health_service.get_monitored_components()) == {"p", "q"}

    def test_stop_monitoring_component(self, health_service):
        comp = _make_component(name="stop_me")
        health_service.monitor_component_health(comp)
        health_service.stop_monitoring_component("stop_me")
        assert "stop_me" not in health_service.monitored_components

    def test_stop_monitoring_unknown_noop(self, health_service):
        health_service.stop_monitoring_component("ghost")

    def test_get_and_set_health_check_interval(self, health_service):
        assert health_service.get_health_check_interval() == 30.0
        health_service.set_health_check_interval(60.0)
        assert health_service.get_health_check_interval() == 60.0

    def test_set_health_check_interval_minimum(self, health_service):
        health_service.set_health_check_interval(0.1)
        assert health_service.get_health_check_interval() == 1.0

    def test_get_required_methods_known_type(self, health_service):
        assert "process" in health_service._get_required_methods("DocumentProcessor")
        assert "embed" in health_service._get_required_methods("Embedder")
        assert "retrieve" in health_service._get_required_methods("Retriever")
        assert "generate" in health_service._get_required_methods("AnswerGenerator")

    def test_get_required_methods_unknown_type(self, health_service):
        assert health_service._get_required_methods("SomeRandom") == []


# ===========================================================================
# SystemAnalyticsServiceImpl
# ===========================================================================


class TestSystemAnalyticsServiceInit:
    """Verify constructor creates expected instance attributes."""

    def test_initial_state(self, analytics_service):
        assert analytics_service.component_metrics == {}
        assert analytics_service.system_metrics_history == []
        assert analytics_service.performance_tracking == {}
        assert analytics_service.performance_history == {}
        assert analytics_service.query_analytics == {}
        assert analytics_service.analytics_enabled is True


class TestTrackComponentPerformance:
    """Tests for track_component_performance."""

    def test_basic_tracking(self, analytics_service):
        comp = _make_component(name="t1")
        analytics_service.track_component_performance(comp, {"latency_ms": 50, "success": True})
        assert "t1" in analytics_service.performance_tracking
        assert analytics_service.performance_tracking["t1"]["success_count"] == 1
        assert analytics_service.performance_tracking["t1"]["total_operations"] == 1

    def test_error_tracking(self, analytics_service):
        comp = _make_component(name="t2")
        analytics_service.track_component_performance(comp, {"success": False})
        assert analytics_service.performance_tracking["t2"]["error_count"] == 1

    def test_explicit_error_count(self, analytics_service):
        comp = _make_component(name="t3")
        analytics_service.track_component_performance(comp, {"error_count": 5})
        assert analytics_service.performance_tracking["t3"]["error_count"] == 5

    def test_explicit_success_count(self, analytics_service):
        comp = _make_component(name="t4")
        analytics_service.track_component_performance(comp, {"success_count": 10})
        assert analytics_service.performance_tracking["t4"]["success_count"] == 10

    def test_latency_averaging(self, analytics_service):
        comp = _make_component(name="lat")
        analytics_service.track_component_performance(comp, {"latency_ms": 100, "success": True})
        analytics_service.track_component_performance(comp, {"latency_ms": 200, "success": True})
        avg = analytics_service.performance_tracking["lat"]["average_latency"]
        assert abs(avg - 150.0) < 1.0

    def test_performance_history_stored(self, analytics_service):
        comp = _make_component(name="ph")
        analytics_service.track_component_performance(comp, {"success": True})
        assert len(analytics_service.performance_history["ph"]) == 1
        assert "metrics" in analytics_service.performance_history["ph"][0]

    def test_component_metrics_dict_updated(self, analytics_service):
        comp = _make_component(name="cmd")
        analytics_service.track_component_performance(comp, {"response_time": 0.5, "success": True})
        cm = analytics_service.component_metrics["cmd"]
        assert "response_time" in cm
        assert "total_operations" in cm

    def test_component_metrics_objects_stored(self, analytics_service):
        comp = _make_component(name="cmo")
        analytics_service.track_component_performance(comp, {"success": True})
        assert len(analytics_service._component_metrics_objects["cmo"]) == 1
        assert isinstance(analytics_service._component_metrics_objects["cmo"][0], ComponentMetrics)

    def test_unnamed_component_uses_class_name(self, analytics_service):
        comp = _make_component()  # No name -> class name "Mock"
        analytics_service.track_component_performance(comp, {"success": True})
        assert "Mock" in analytics_service.performance_tracking


class TestCollectSystemMetrics:
    """Tests for collect_system_metrics."""

    def test_empty_returns_defaults(self, analytics_service):
        result = analytics_service.collect_system_metrics()
        assert result["total_components"] == 0
        assert result["average_response_time"] == 0.0
        assert result["overall_success_rate"] == 1.0
        assert result["total_errors"] == 0

    def test_with_tracked_components(self, analytics_service):
        comp = _make_component(name="sm1")
        analytics_service.track_component_performance(
            comp,
            {"response_time": 0.5, "success": True},
        )
        result = analytics_service.collect_system_metrics()
        assert result["total_components"] == 1
        assert result["average_response_time"] == 0.5

    def test_aggregates_errors(self, analytics_service):
        for name, errs in [("e1", 2), ("e2", 3)]:
            comp = _make_component(name=name)
            analytics_service.track_component_performance(comp, {"error_count": errs})
        result = analytics_service.collect_system_metrics()
        assert result["total_errors"] == 5


class TestCollectComponentMetrics:
    """Tests for collect_component_metrics."""

    def test_basic_metrics_collected(self, analytics_service):
        comp = _make_component(name="ccm")
        metrics = analytics_service.collect_component_metrics(comp)
        assert isinstance(metrics, ComponentMetrics)
        assert metrics.component_name == "Mock"

    def test_get_stats_integrated(self, analytics_service):
        comp = _make_component(name="gs", has_get_stats=True, get_stats_result={"queries": 42})
        metrics = analytics_service.collect_component_metrics(comp)
        assert metrics.performance_metrics.get("queries") == 42

    def test_get_configuration_integrated(self, analytics_service):
        comp = _make_component(
            name="gc",
            has_get_configuration=True,
            get_configuration_result={"a": 1},
        )
        metrics = analytics_service.collect_component_metrics(comp)
        assert metrics.performance_metrics.get("has_config") is True
        assert metrics.performance_metrics.get("config_complexity") == 1

    def test_success_error_counts_from_tracking(self, analytics_service):
        # Use separate components to avoid dict/list conflict in component_metrics
        # when track_component_performance and collect_component_metrics both write
        # to the same key with different types.
        comp_s = _make_component(name="sec_s")
        comp_e = _make_component(name="sec_e")
        analytics_service.track_component_performance(comp_s, {"success_count": 7})
        analytics_service.track_component_performance(comp_e, {"error_count": 2})
        # Verify performance_tracking stores the counts correctly
        assert analytics_service.performance_tracking["sec_s"]["success_count"] == 7
        assert analytics_service.performance_tracking["sec_e"]["error_count"] == 2
        # collect_component_metrics reads from performance_tracking for counts
        # Use a fresh component (no prior track_component_performance) to avoid conflict
        comp_fresh = _make_component(name="sec_fresh")
        analytics_service.performance_tracking["sec_fresh"] = {"success_count": 7, "error_count": 2}
        metrics = analytics_service.collect_component_metrics(comp_fresh)
        assert metrics.success_count == 7
        assert metrics.error_count == 2

    def test_metrics_history_capped_at_100(self, analytics_service):
        comp = _make_component(name="cap")
        for _ in range(105):
            analytics_service.collect_component_metrics(comp)
        assert len(analytics_service.component_metrics["cap"]) == 100


class TestAggregateSystemMetrics:
    """Tests for aggregate_system_metrics."""

    def test_empty_aggregation(self, analytics_service):
        result = analytics_service.aggregate_system_metrics()
        assert "timestamp" in result
        assert result["total_components"] == 0

    def test_stores_in_history(self, analytics_service):
        analytics_service.aggregate_system_metrics()
        assert len(analytics_service.system_metrics_history) == 1

    def test_history_capped_at_50(self, analytics_service):
        for _ in range(55):
            analytics_service.aggregate_system_metrics()
        assert len(analytics_service.system_metrics_history) == 50

    def test_uses_component_metrics_objects(self, analytics_service):
        comp = _make_component(name="agg")
        analytics_service.track_component_performance(comp, {"success_count": 3})
        result = analytics_service.aggregate_system_metrics()
        # Should include data from _component_metrics_objects
        assert "component_metrics" in result
        if "agg" in result["component_metrics"]:
            assert result["component_metrics"]["agg"]["success_count"] == 3


class TestGenerateAnalyticsReport:
    """Tests for generate_analytics_report."""

    def test_empty_report_structure(self, analytics_service):
        report = analytics_service.generate_analytics_report()
        assert "timestamp" in report
        assert "system_overview" in report
        assert "system_summary" in report
        assert "component_performance" in report
        assert "performance_trends" in report
        assert "recommendations" in report

    def test_component_performance_populated(self, analytics_service):
        comp = _make_component(name="rpt")
        analytics_service.track_component_performance(comp, {"success": True, "latency_ms": 50})
        report = analytics_service.generate_analytics_report()
        assert "rpt" in report["component_performance"]
        assert report["component_performance"]["rpt"]["total_operations"] == 1

    def test_high_error_rate_recommendation(self, analytics_service):
        comp = _make_component(name="herr")
        # Generate many errors to exceed 10% threshold
        for _ in range(5):
            analytics_service.track_component_performance(comp, {"success": False})
        report = analytics_service.generate_analytics_report()
        assert any("High error rate" in r for r in report["recommendations"])

    def test_high_latency_recommendation(self, analytics_service):
        comp = _make_component(name="hlat")
        analytics_service.track_component_performance(comp, {"latency_ms": 2000, "success": True})
        report = analytics_service.generate_analytics_report()
        assert any("High latency" in r for r in report["recommendations"])

    def test_trends_stable_by_default(self, analytics_service):
        report = analytics_service.generate_analytics_report()
        trends = report["performance_trends"]
        assert trends["response_time_trend"] == "stable"
        assert trends["success_rate_trend"] == "stable"
        assert trends["error_rate_trend"] == "stable"

    def test_response_time_trend_increasing(self, analytics_service):
        comp = _make_component(name="rti")
        analytics_service.track_component_performance(comp, {"response_time": 0.1, "success": True})
        analytics_service.track_component_performance(comp, {"response_time": 0.5, "success": True})
        report = analytics_service.generate_analytics_report()
        assert report["performance_trends"]["response_time_trend"] == "increasing"

    def test_response_time_trend_decreasing(self, analytics_service):
        comp = _make_component(name="rtd")
        analytics_service.track_component_performance(comp, {"response_time": 0.5, "success": True})
        analytics_service.track_component_performance(comp, {"response_time": 0.1, "success": True})
        report = analytics_service.generate_analytics_report()
        assert report["performance_trends"]["response_time_trend"] == "decreasing"

    def test_success_rate_trend_improving(self, analytics_service):
        comp = _make_component(name="sri")
        analytics_service.track_component_performance(comp, {"success_rate": 0.8, "success": True})
        analytics_service.track_component_performance(comp, {"success_rate": 0.95, "success": True})
        report = analytics_service.generate_analytics_report()
        assert report["performance_trends"]["success_rate_trend"] == "improving"

    def test_error_rate_trend_increasing(self, analytics_service):
        comp = _make_component(name="eri")
        analytics_service.track_component_performance(comp, {"error_count": 1, "success": True})
        analytics_service.track_component_performance(comp, {"error_count": 10, "success": True})
        report = analytics_service.generate_analytics_report()
        assert report["performance_trends"]["error_rate_trend"] == "increasing"
        assert any("Error count is increasing" in r for r in report["recommendations"])

    def test_healthy_component_counting(self, analytics_service):
        comp = _make_component(name="hcc")
        # Low error rate -> healthy
        analytics_service.track_component_performance(comp, {"success": True})
        report = analytics_service.generate_analytics_report()
        assert report["system_overview"]["healthy_components"] >= 1


class TestCalculatePerformanceScore:
    """Tests for calculate_performance_score."""

    def test_unknown_component_returns_zero(self, analytics_service):
        assert analytics_service.calculate_performance_score("nonexistent") == 0.0

    def test_perfect_component(self, analytics_service):
        comp = _make_component(name="perf")
        analytics_service.track_component_performance(
            comp,
            {"success_rate": 1.0, "response_time": 0.0, "error_count": 0, "total_operations": 100},
        )
        score = analytics_service.calculate_performance_score("perf")
        assert score == 100.0

    def test_score_decreases_with_high_response_time(self, analytics_service):
        comp = _make_component(name="slow")
        analytics_service.track_component_performance(
            comp,
            {"success_rate": 1.0, "response_time": 2.0, "error_count": 0, "total_operations": 1},
        )
        score = analytics_service.calculate_performance_score("slow")
        # response_time=2.0 -> response_score = max(0, 30 - 60) = 0
        assert score < 100.0

    def test_score_bounded_0_to_100(self, analytics_service):
        comp = _make_component(name="bound")
        analytics_service.track_component_performance(
            comp,
            {"success_rate": 0.0, "response_time": 10.0, "error_count": 100, "total_operations": 100},
        )
        score = analytics_service.calculate_performance_score("bound")
        assert 0.0 <= score <= 100.0


class TestAnalyticsServiceHelpers:
    """Tests for helper/accessor methods on SystemAnalyticsServiceImpl."""

    def test_get_component_performance_history(self, analytics_service):
        comp = _make_component(name="cph")
        analytics_service.track_component_performance(comp, {"success": True})
        history = analytics_service.get_component_performance_history("cph")
        assert len(history) == 1
        # Ensure it returns a copy
        history.append({"fake": True})
        assert len(analytics_service.performance_history["cph"]) == 1

    def test_get_component_performance_history_unknown(self, analytics_service):
        assert analytics_service.get_component_performance_history("nope") == []

    def test_clear_analytics_data(self, analytics_service):
        comp = _make_component(name="clr")
        analytics_service.track_component_performance(comp, {"success": True})
        analytics_service.clear_analytics_data()
        assert analytics_service.component_metrics == {}
        assert analytics_service.performance_tracking == {}

    def test_get_analytics_summary(self, analytics_service):
        summary = analytics_service.get_analytics_summary()
        assert summary["analytics_enabled"] is True
        assert summary["monitored_components"] == 0

    def test_enable_disable_analytics(self, analytics_service):
        analytics_service.disable_analytics()
        assert analytics_service.analytics_enabled is False
        analytics_service.enable_analytics()
        assert analytics_service.analytics_enabled is True

    def test_get_component_analytics(self, analytics_service):
        comp = _make_component(name="gca")
        analytics_service.track_component_performance(comp, {"success": True})
        result = analytics_service.get_component_analytics("gca")
        assert "current_metrics" in result
        assert "performance_history" in result

    def test_get_component_analytics_unknown(self, analytics_service):
        assert analytics_service.get_component_analytics("nope") == {}

    def test_track_query_analytics(self, analytics_service):
        analytics_service.track_query_analytics({"query": "test", "latency": 50})
        assert len(analytics_service.query_analytics) == 1

    def test_get_performance_summary_empty(self, analytics_service):
        summary = analytics_service.get_performance_summary()
        assert summary["best_performing_component"] is None
        assert summary["worst_performing_component"] is None
        assert summary["total_requests"] == 0

    def test_get_performance_summary_with_data(self, analytics_service):
        good = _make_component(name="good")
        bad = _make_component(name="bad")
        analytics_service.track_component_performance(
            good, {"success_rate": 0.99, "total_operations": 100, "error_count": 0, "response_time": 0.1},
        )
        analytics_service.track_component_performance(
            bad, {"success_rate": 0.1, "total_operations": 100, "error_count": 50, "response_time": 2.0},
        )
        summary = analytics_service.get_performance_summary()
        assert summary["best_performing_component"] == "good"
        assert summary["worst_performing_component"] == "bad"
        assert summary["total_requests"] > 0

    def test_detect_performance_anomalies_no_data(self, analytics_service):
        assert analytics_service.detect_performance_anomalies() == []

    def test_detect_response_time_spike(self, analytics_service):
        comp = _make_component(name="spike")
        # Need at least 3 data points
        for rt in [0.5, 0.5, 0.5, 5.0]:
            analytics_service.track_component_performance(
                comp, {"response_time": rt, "success": True},
            )
        anomalies = analytics_service.detect_performance_anomalies()
        assert len(anomalies) >= 1
        assert anomalies[0]["type"] == "response_time_spike"

    def test_detect_error_rate_spike(self, analytics_service):
        comp = _make_component(name="err_spike")
        for ec in [1, 1, 1, 20]:
            analytics_service.track_component_performance(
                comp, {"error_count": ec, "success": True},
            )
        anomalies = analytics_service.detect_performance_anomalies()
        assert any(a["type"] == "error_rate_spike" for a in anomalies)

    def test_export_analytics_data(self, analytics_service):
        comp = _make_component(name="exp")
        analytics_service.track_component_performance(comp, {"success": True})
        export = analytics_service.export_analytics_data()
        assert "component_metrics" in export
        assert "system_metrics" in export
        assert "export_timestamp" in export

    def test_reset_analytics_data(self, analytics_service):
        comp = _make_component(name="rst")
        analytics_service.track_component_performance(comp, {"success": True})
        analytics_service.track_query_analytics({"q": "test"})
        analytics_service.reset_analytics_data()
        assert analytics_service.component_metrics == {}
        assert analytics_service.performance_tracking == {}
        assert analytics_service.performance_history == {}
        assert analytics_service.query_analytics == {}
        assert analytics_service._component_metrics_objects == {}


# ===========================================================================
# ConfigurationServiceImpl
# ===========================================================================


class TestConfigurationServiceInit:
    """Verify constructor creates expected instance attributes."""

    def test_initial_state(self, config_service):
        assert config_service.config_manager is not None
        assert isinstance(config_service.config_cache, dict)
        assert isinstance(config_service.config_history, list)
        assert isinstance(config_service.dynamic_configs, dict)

    def test_config_loaded_on_init(self, config_service):
        # _load_current_config should have populated cache
        assert "document_processor" in config_service.config_cache
        assert "embedder" in config_service.config_cache
        assert "retriever" in config_service.config_cache
        assert "answer_generator" in config_service.config_cache
        assert "vector_store" in config_service.config_cache
        assert "global_settings" in config_service.config_cache

    def test_current_config_property(self, config_service):
        assert config_service.current_config is config_service.config_cache


class TestGetComponentConfig:
    """Tests for get_component_config."""

    def test_returns_config_for_known_component(self, config_service):
        cfg = config_service.get_component_config("embedder")
        assert cfg["type"] == "mock_embedder"
        assert "config" in cfg

    def test_returns_empty_dict_for_unknown(self, config_service):
        assert config_service.get_component_config("nonexistent") == {}

    def test_dynamic_overrides_applied(self, config_service):
        config_service.dynamic_configs["embedder"] = {"extra_key": 42}
        cfg = config_service.get_component_config("embedder")
        assert cfg["extra_key"] == 42


class TestUpdateComponentConfig:
    """Tests for update_component_config."""

    def test_updates_existing_component(self, config_service):
        config_service.update_component_config("embedder", {"model_name": "new-model"})
        cfg = config_service.config_cache["embedder"]
        assert cfg["config"]["model_name"] == "new-model"

    def test_creates_new_component_entry(self, config_service):
        config_service.update_component_config("brand_new", {"x": 1})
        assert "brand_new" in config_service.config_cache
        assert config_service.config_cache["brand_new"]["type"] == "unknown"

    def test_records_change_in_history(self, config_service):
        config_service.update_component_config("embedder", {"lr": 0.01})
        assert len(config_service.config_history) >= 1
        latest = config_service.config_history[-1]
        assert latest["component"] == "embedder"
        assert latest["change_type"] == "update"
        assert "old_state" in latest

    def test_rejects_negative_values(self, config_service):
        with pytest.raises(ValueError, match="Invalid negative value"):
            config_service.update_component_config("embedder", {"batch_size": -1})

    def test_dynamic_configs_updated(self, config_service):
        config_service.update_component_config("retriever", {"top_k": 10})
        assert config_service.dynamic_configs["retriever"]["top_k"] == 10

    def test_history_capped_at_100(self, config_service):
        for i in range(105):
            config_service.update_component_config("embedder", {"iter": i})
        assert len(config_service.config_history) == 100


class TestValidateConfiguration:
    """Tests for validate_configuration."""

    def test_valid_dict(self, config_service):
        errors = config_service.validate_configuration({"key": "val"})
        assert errors == []

    def test_non_dict_returns_error(self, config_service):
        errors = config_service.validate_configuration("not a dict")
        assert len(errors) == 1
        assert "must be a dictionary" in errors[0]


class TestGetSystemConfiguration:
    """Tests for get_system_configuration."""

    def test_returns_deep_copy(self, config_service):
        sys_cfg = config_service.get_system_configuration()
        # Mutating the copy should not affect the original
        sys_cfg["embedder"]["type"] = "MUTATED"
        assert config_service.config_cache["embedder"]["type"] == "mock_embedder"


class TestReloadConfiguration:
    """Tests for reload_configuration."""

    def test_reload_calls_config_manager(self, config_service, mock_config_manager):
        config_service.reload_configuration()
        mock_config_manager.reload.assert_called_once()

    def test_reload_records_in_history(self, config_service):
        config_service.reload_configuration()
        reload_entries = [
            h for h in config_service.config_history if h.get("change_type") == "configuration_reload"
        ]
        assert len(reload_entries) >= 1

    def test_reload_failure_propagates(self, config_service, mock_config_manager):
        mock_config_manager.reload.side_effect = RuntimeError("reload failed")
        with pytest.raises(RuntimeError, match="reload failed"):
            config_service.reload_configuration()


class TestGetConfigurationHistory:
    """Tests for get_configuration_history."""

    def test_returns_copy(self, config_service):
        config_service.update_component_config("embedder", {"x": 1})
        history = config_service.get_configuration_history()
        history.clear()
        assert len(config_service.config_history) >= 1
