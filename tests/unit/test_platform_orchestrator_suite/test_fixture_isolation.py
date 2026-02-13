"""
Test fixture isolation and state cleanup.

This test file verifies that service fixtures properly clean up state
between tests to prevent test contamination issues.
"""

import pytest

from src.core.platform_orchestrator import (
    ComponentHealthServiceImpl,
    SystemAnalyticsServiceImpl,
)
from .conftest import MockComponent


class TestFixtureIsolation:
    """Test that fixtures properly isolate state between tests."""

    def test_health_service_isolation_test1(self, health_service):
        """First test that uses health_service - should have clean state."""
        # Verify initial clean state
        assert len(health_service.monitored_components) == 0
        assert len(health_service.health_history) == 0
        assert len(health_service.failure_counts) == 0
        assert len(health_service.last_health_checks) == 0

        # Add some state
        component = MockComponent("Test1Component")
        health_service.monitor_component_health(component)

        # Verify state was added
        assert len(health_service.monitored_components) == 1
        assert "Test1Component" in health_service.monitored_components

    def test_health_service_isolation_test2(self, health_service):
        """Second test that uses health_service - should have clean state from first test."""
        # Verify clean state (no contamination from test1)
        assert len(health_service.monitored_components) == 0
        assert len(health_service.health_history) == 0
        assert len(health_service.failure_counts) == 0
        assert len(health_service.last_health_checks) == 0

        # Add different state
        component = MockComponent("Test2Component")
        health_service.monitor_component_health(component)

        # Verify only this test's state is present
        assert len(health_service.monitored_components) == 1
        assert "Test2Component" in health_service.monitored_components
        assert "Test1Component" not in health_service.monitored_components

    def test_health_service_isolation_test3(self, health_service):
        """Third test - verify state is still clean."""
        # Should have completely clean state
        assert len(health_service.monitored_components) == 0
        assert len(health_service.health_history) == 0

        # Add multiple components
        for i in range(3):
            component = MockComponent(f"Test3Component{i}")
            health_service.monitor_component_health(component)

        assert len(health_service.monitored_components) == 3

    def test_analytics_service_isolation_test1(self, analytics_service):
        """First test with analytics_service - should have clean state."""
        assert len(analytics_service.component_metrics) == 0
        assert len(analytics_service.system_metrics_history) == 0
        assert len(analytics_service.performance_tracking) == 0
        assert len(analytics_service.performance_history) == 0
        assert len(analytics_service.query_analytics) == 0

        # Add some state
        component = MockComponent("AnalyticsTest1")
        metrics = analytics_service.collect_component_metrics(component)

        # Verify state was added
        assert metrics.component_name == "MockComponent"

    def test_analytics_service_isolation_test2(self, analytics_service):
        """Second test with analytics_service - should have clean state."""
        # Verify clean state (no contamination from test1)
        assert len(analytics_service.component_metrics) == 0
        assert len(analytics_service.system_metrics_history) == 0
        assert len(analytics_service.performance_tracking) == 0

    def test_multiple_services_no_cross_contamination(
        self, health_service, analytics_service
    ):
        """Verify multiple services don't contaminate each other."""
        # All should start clean
        assert len(health_service.monitored_components) == 0
        assert len(analytics_service.component_metrics) == 0

        # Modify all services
        component = MockComponent("MultiServiceTest")
        health_service.monitor_component_health(component)
        analytics_service.collect_component_metrics(component)

        # Each should have their own state
        assert len(health_service.monitored_components) == 1

    def test_sequential_runs_maintain_isolation(self, health_service):
        """Test that running multiple operations in sequence maintains isolation."""
        # First operation
        comp1 = MockComponent("Seq1")
        health_service.monitor_component_health(comp1)
        assert len(health_service.monitored_components) == 1

        # Clear manually to simulate cleanup
        health_service.monitored_components.clear()
        health_service.health_history.clear()
        health_service.failure_counts.clear()
        health_service.last_health_checks.clear()

        # Second operation should see clean state
        assert len(health_service.monitored_components) == 0
        comp2 = MockComponent("Seq2")
        health_service.monitor_component_health(comp2)
        assert len(health_service.monitored_components) == 1
        assert "Seq1" not in health_service.monitored_components
        assert "Seq2" in health_service.monitored_components
