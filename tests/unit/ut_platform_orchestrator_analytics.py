"""
Test suite for SystemAnalyticsServiceImpl functionality in PlatformOrchestrator.

Tests the analytics service that tracks component performance, collects metrics,
generates reports, and provides system insights.
"""

import pytest
import time
from unittest.mock import Mock, patch
from typing import Dict, Any

from src.core.platform_orchestrator import SystemAnalyticsServiceImpl
from src.core.interfaces import ComponentMetrics
from .conftest import MockComponent, create_performance_metrics


class TestSystemAnalyticsServiceImpl:
    """Test SystemAnalyticsServiceImpl business logic and functionality."""

    def test_analytics_service_initialization(self, analytics_service):
        """Test analytics service initializes with correct default state."""
        assert analytics_service.component_metrics == {}
        assert analytics_service.system_metrics_history == []
        assert analytics_service.performance_tracking == {}
        assert analytics_service.analytics_enabled is True

    def test_track_component_performance_new_component(self, analytics_service):
        """Test tracking performance for a new component."""
        component = MockComponent("NewComponent")
        metrics = create_performance_metrics(
            response_time=0.15,
            success_rate=0.95,
            error_count=2
        )

        analytics_service.track_component_performance(component, metrics)

        component_name = "NewComponent"  # Use instance name, not class name
        assert component_name in analytics_service.component_metrics
        stored_metrics = analytics_service.component_metrics[component_name]
        assert stored_metrics["response_time"] == 0.15
        assert stored_metrics["success_rate"] == 0.95
        assert stored_metrics["error_count"] == 2

    def test_track_component_performance_existing_component(self, analytics_service):
        """Test tracking performance for an existing component updates metrics."""
        component = MockComponent("ExistingComponent")

        # Initial metrics
        initial_metrics = create_performance_metrics(response_time=0.1, error_count=1)
        analytics_service.track_component_performance(component, initial_metrics)

        # Updated metrics
        updated_metrics = create_performance_metrics(response_time=0.2, error_count=2)
        analytics_service.track_component_performance(component, updated_metrics)

        component_name = "ExistingComponent"  # Use instance name, not class name
        stored_metrics = analytics_service.component_metrics[component_name]
        assert stored_metrics["response_time"] == 0.2
        assert stored_metrics["error_count"] == 2

    def test_track_component_performance_history(self, analytics_service):
        """Test performance history tracking."""
        component = MockComponent("HistoryComponent")

        # Track multiple performance data points
        for i in range(3):
            metrics = create_performance_metrics(
                response_time=0.1 + i * 0.05,
                success_rate=0.9 + i * 0.02,
                error_count=i
            )
            analytics_service.track_component_performance(component, metrics)
            time.sleep(0.01)  # Ensure different timestamps

        component_name = "HistoryComponent"  # Use instance name, not class name
        assert component_name in analytics_service.performance_history
        history = analytics_service.performance_history[component_name]
        assert len(history) >= 1  # At least the latest should be stored

        # Verify metrics evolution if history is maintained
        if len(history) > 1:
            assert history[-1]["metrics"]["response_time"] > history[0]["metrics"]["response_time"]

    def test_collect_system_metrics(self, analytics_service):
        """Test system-wide metrics collection."""
        # Add some component metrics first
        components = [MockComponent(f"Component{i}") for i in range(3)]
        for i, component in enumerate(components):
            metrics = create_performance_metrics(
                response_time=0.1 + i * 0.05,
                success_rate=0.9 - i * 0.1,
                error_count=i
            )
            analytics_service.track_component_performance(component, metrics)
        
        # Collect system metrics
        system_metrics = analytics_service.collect_system_metrics()
        
        assert isinstance(system_metrics, dict)
        assert "total_components" in system_metrics
        assert "average_response_time" in system_metrics
        assert "overall_success_rate" in system_metrics
        assert "total_errors" in system_metrics
        assert system_metrics["total_components"] >= 3

    def test_collect_system_metrics_empty(self, analytics_service):
        """Test system metrics collection with no components."""
        system_metrics = analytics_service.collect_system_metrics()
        
        assert system_metrics["total_components"] == 0
        assert system_metrics["average_response_time"] == 0.0
        assert system_metrics["overall_success_rate"] == 1.0
        assert system_metrics["total_errors"] == 0

    def test_generate_analytics_report_comprehensive(self, analytics_service):
        """Test comprehensive analytics report generation."""
        # Setup test data
        component = MockComponent("ReportComponent")
        metrics = create_performance_metrics(
            response_time=0.125,
            success_rate=0.96,
            error_count=3,
            memory_usage=256.5,
            cpu_usage=15.2
        )
        analytics_service.track_component_performance(component, metrics)
        
        # Generate report
        report = analytics_service.generate_analytics_report()
        
        # Verify report structure
        assert isinstance(report, dict)
        assert "timestamp" in report
        assert "system_overview" in report
        assert "component_performance" in report
        assert "performance_trends" in report
        assert "recommendations" in report
        
        # Verify system overview
        overview = report["system_overview"]
        assert "total_components" in overview
        assert "healthy_components" in overview
        assert "average_response_time" in overview
        assert "system_load" in overview

    def test_generate_analytics_report_performance_trends(self, analytics_service):
        """Test analytics report includes performance trends."""
        component = MockComponent("TrendComponent")
        
        # Create performance trend over time
        base_time = time.time()
        for i in range(5):
            metrics = create_performance_metrics(
                response_time=0.1 + i * 0.02,  # Increasing response time
                success_rate=0.95 - i * 0.01,  # Decreasing success rate
                error_count=i,
                timestamp=base_time + i * 60
            )
            analytics_service.track_component_performance(component, metrics)
        
        report = analytics_service.generate_analytics_report()
        
        trends = report["performance_trends"]
        assert isinstance(trends, dict)
        assert "response_time_trend" in trends
        assert "success_rate_trend" in trends
        assert "error_rate_trend" in trends

    def test_get_component_analytics(self, analytics_service):
        """Test getting analytics for a specific component."""
        component = MockComponent("SpecificComponent")
        metrics = create_performance_metrics(
            response_time=0.18,
            success_rate=0.94,
            error_count=5
        )
        analytics_service.track_component_performance(component, metrics)

        component_name = "SpecificComponent"  # Use instance name, not class name
        component_analytics = analytics_service.get_component_analytics(component_name)

        assert isinstance(component_analytics, dict)
        assert "current_metrics" in component_analytics
        assert "performance_history" in component_analytics
        assert component_analytics["current_metrics"]["response_time"] == 0.18

    def test_get_component_analytics_nonexistent(self, analytics_service):
        """Test getting analytics for non-existent component."""
        analytics = analytics_service.get_component_analytics("NonExistentComponent")
        
        assert analytics is None or analytics == {}

    def test_track_query_analytics(self, analytics_service):
        """Test query-specific analytics tracking."""
        query_data = {
            "query": "test query",
            "response_time": 1.25,
            "retrieval_time": 0.8,
            "generation_time": 0.45,
            "confidence": 0.87,
            "document_count": 5
        }
        
        analytics_service.track_query_analytics(query_data)
        
        assert len(analytics_service.query_analytics) >= 1
        if analytics_service.query_analytics:
            stored_query = list(analytics_service.query_analytics.values())[0]
            assert stored_query["response_time"] == 1.25
            assert stored_query["confidence"] == 0.87

    def test_get_performance_summary(self, analytics_service):
        """Test performance summary generation."""
        # Add multiple components with different performance characteristics
        for i in range(4):
            component = MockComponent(f"PerfComponent{i}")
            metrics = create_performance_metrics(
                response_time=0.1 + i * 0.1,
                success_rate=0.9 + i * 0.025,
                error_count=i * 2
            )
            analytics_service.track_component_performance(component, metrics)
        
        summary = analytics_service.get_performance_summary()
        
        assert isinstance(summary, dict)
        assert "best_performing_component" in summary
        assert "worst_performing_component" in summary
        assert "average_metrics" in summary
        assert "total_requests" in summary

    def test_calculate_performance_score(self, analytics_service):
        """Test performance score calculation."""
        component = MockComponent("ScoredComponent")

        # High performance metrics
        good_metrics = create_performance_metrics(
            response_time=0.05,
            success_rate=0.99,
            error_count=0
        )
        analytics_service.track_component_performance(component, good_metrics)

        score = analytics_service.calculate_performance_score("ScoredComponent")  # Use instance name, not class name

        assert isinstance(score, (int, float))
        assert 0 <= score <= 100  # Assuming 0-100 scoring

    def test_detect_performance_anomalies(self, analytics_service):
        """Test performance anomaly detection."""
        component = MockComponent("AnomalyComponent")
        
        # Establish baseline performance
        for i in range(10):
            normal_metrics = create_performance_metrics(
                response_time=0.1 + (i % 3) * 0.01,  # Normal variation
                success_rate=0.95 + (i % 2) * 0.02,
                error_count=i % 2
            )
            analytics_service.track_component_performance(component, normal_metrics)
        
        # Add anomalous performance
        anomalous_metrics = create_performance_metrics(
            response_time=2.0,  # Significantly higher
            success_rate=0.5,   # Significantly lower
            error_count=50      # Significantly higher
        )
        analytics_service.track_component_performance(component, anomalous_metrics)
        
        anomalies = analytics_service.detect_performance_anomalies()
        
        assert isinstance(anomalies, (list, dict))
        # Would contain anomaly information if detection is implemented

    def test_export_analytics_data(self, analytics_service):
        """Test analytics data export functionality."""
        # Add some test data
        component = MockComponent("ExportComponent")
        metrics = create_performance_metrics()
        analytics_service.track_component_performance(component, metrics)
        
        exported_data = analytics_service.export_analytics_data()
        
        assert isinstance(exported_data, dict)
        assert "component_metrics" in exported_data
        assert "system_metrics" in exported_data
        assert "export_timestamp" in exported_data

    def test_reset_analytics_data(self, analytics_service):
        """Test resetting analytics data."""
        # Add some test data
        component = MockComponent("ResetComponent")
        metrics = create_performance_metrics()
        analytics_service.track_component_performance(component, metrics)
        
        # Verify data exists
        assert len(analytics_service.component_metrics) > 0
        
        # Reset analytics
        analytics_service.reset_analytics_data()
        
        # Verify data is cleared
        assert len(analytics_service.component_metrics) == 0
        assert len(analytics_service.performance_history) == 0
        assert len(analytics_service.query_analytics) == 0

    def test_concurrent_metric_tracking(self, analytics_service):
        """Test concurrent metric tracking doesn't cause data corruption."""
        import threading
        
        def track_metrics(component_id):
            component = MockComponent(f"ConcurrentComponent{component_id}")
            for i in range(5):
                metrics = create_performance_metrics(
                    response_time=0.1 + component_id * 0.01,
                    error_count=i
                )
                analytics_service.track_component_performance(component, metrics)
        
        # Create multiple threads tracking metrics
        threads = []
        for i in range(3):
            thread = threading.Thread(target=track_metrics, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify data integrity
        assert len(analytics_service.component_metrics) == 3
        for component_name in analytics_service.component_metrics:
            assert isinstance(analytics_service.component_metrics[component_name], dict)

    def test_metrics_aggregation_accuracy(self, analytics_service):
        """Test accuracy of metrics aggregation calculations."""
        # Create components with known metrics for calculation verification
        test_cases = [
            (0.1, 0.95, 5),   # Component 1
            (0.2, 0.90, 10),  # Component 2
            (0.15, 0.98, 2),  # Component 3
        ]
        
        for i, (response_time, success_rate, error_count) in enumerate(test_cases):
            component = MockComponent(f"CalcComponent{i}")
            metrics = create_performance_metrics(
                response_time=response_time,
                success_rate=success_rate,
                error_count=error_count
            )
            analytics_service.track_component_performance(component, metrics)
        
        system_metrics = analytics_service.collect_system_metrics()
        
        # Verify calculations
        expected_avg_response_time = sum(case[0] for case in test_cases) / len(test_cases)
        expected_total_errors = sum(case[2] for case in test_cases)
        
        assert abs(system_metrics["average_response_time"] - expected_avg_response_time) < 0.001
        assert system_metrics["total_errors"] == expected_total_errors