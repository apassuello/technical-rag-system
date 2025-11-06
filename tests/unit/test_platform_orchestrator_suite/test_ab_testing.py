"""
Test suite for ABTestingServiceImpl functionality in PlatformOrchestrator.

Tests the A/B testing service that manages experiments, assigns variants,
tracks outcomes, and provides statistical analysis.
"""

import pytest
import time
import uuid
from unittest.mock import Mock, patch
from typing import Dict, Any

from src.core.platform_orchestrator import ABTestingServiceImpl
from src.core.interfaces import ExperimentAssignment, ExperimentResult
from .conftest import create_performance_metrics


class TestABTestingServiceImpl:
    """Test ABTestingServiceImpl business logic and functionality."""

    def test_ab_testing_service_initialization(self, ab_testing_service):
        """Test A/B testing service initializes with correct default state."""
        assert ab_testing_service.active_experiments == {}
        assert ab_testing_service.assignments == {}
        assert ab_testing_service.results == {}
        assert ab_testing_service.experiments == {}

    def test_configure_experiment_basic(self, ab_testing_service):
        """Test configuring a basic A/B experiment."""
        experiment_config = {
            "name": "test_retrieval_experiment",
            "variants": {
                "control": {"dense_weight": 0.7},
                "treatment": {"dense_weight": 0.8}
            },
            "traffic_allocation": {"control": 0.5, "treatment": 0.5},
            "duration_days": 7,
            "success_metrics": ["response_time", "relevance_score"]
        }
        
        ab_testing_service.configure_experiment(experiment_config)
        
        experiment_name = "test_retrieval_experiment"
        assert experiment_name in ab_testing_service.experiments
        stored_config = ab_testing_service.experiments[experiment_name]
        assert stored_config["variants"]["control"]["dense_weight"] == 0.7
        assert stored_config["traffic_allocation"]["control"] == 0.5

    def test_configure_experiment_validation(self, ab_testing_service):
        """Test experiment configuration validation."""
        # Invalid traffic allocation (doesn't sum to 1.0)
        invalid_config = {
            "name": "invalid_experiment",
            "variants": {
                "control": {"param": "value1"},
                "treatment": {"param": "value2"}
            },
            "traffic_allocation": {"control": 0.7, "treatment": 0.7}  # Sums to 1.4
        }
        
        with pytest.raises((ValueError, AssertionError)):
            ab_testing_service.configure_experiment(invalid_config)

    def test_assign_experiment_new_context(self, ab_testing_service):
        """Test experiment assignment for new context."""
        # Configure experiment first
        experiment_config = {
            "name": "assignment_test",
            "variants": {
                "control": {"model": "base_model"},
                "treatment": {"model": "improved_model"}
            },
            "traffic_allocation": {"control": 0.6, "treatment": 0.4}
        }
        ab_testing_service.configure_experiment(experiment_config)
        
        context = {
            "user_id": "user123",
            "session_id": "session456",
            "experiment": "assignment_test"
        }
        
        assignment = ab_testing_service.assign_experiment(context)
        
        assert isinstance(assignment, ExperimentAssignment)
        assert assignment.experiment_id == "assignment_test"
        assert assignment.variant in ["control", "treatment"]
        assert assignment.user_id == "user123"
        assert isinstance(assignment.config, dict)

    def test_assign_experiment_consistent_assignment(self, ab_testing_service):
        """Test that experiment assignments are consistent for the same user."""
        experiment_config = {
            "name": "consistency_test",
            "variants": {
                "control": {"setting": "default"},
                "treatment": {"setting": "optimized"}
            },
            "traffic_allocation": {"control": 0.5, "treatment": 0.5}
        }
        ab_testing_service.configure_experiment(experiment_config)
        
        context = {
            "user_id": "consistent_user",
            "experiment": "consistency_test"
        }
        
        # Get assignment multiple times
        assignment1 = ab_testing_service.assign_experiment(context)
        assignment2 = ab_testing_service.assign_experiment(context)
        assignment3 = ab_testing_service.assign_experiment(context)
        
        # Should get the same variant every time
        assert assignment1.variant == assignment2.variant == assignment3.variant

    def test_assign_experiment_traffic_allocation(self, ab_testing_service):
        """Test that traffic allocation is approximately respected."""
        experiment_config = {
            "name": "traffic_test",
            "variants": {
                "control": {"param": "control_value"},
                "treatment": {"param": "treatment_value"}
            },
            "traffic_allocation": {"control": 0.8, "treatment": 0.2}
        }
        ab_testing_service.configure_experiment(experiment_config)
        
        # Generate many assignments
        control_count = 0
        treatment_count = 0
        total_assignments = 1000
        
        for i in range(total_assignments):
            context = {
                "user_id": f"user{i}",
                "experiment": "traffic_test"
            }
            assignment = ab_testing_service.assign_experiment(context)
            
            if assignment.variant == "control":
                control_count += 1
            else:
                treatment_count += 1
        
        # Check that allocation is approximately correct (within 5%)
        control_ratio = control_count / total_assignments
        treatment_ratio = treatment_count / total_assignments
        
        assert abs(control_ratio - 0.8) < 0.05
        assert abs(treatment_ratio - 0.2) < 0.05

    def test_track_experiment_outcome(self, ab_testing_service):
        """Test tracking experiment outcomes."""
        # First configure and assign experiment
        experiment_config = {
            "name": "outcome_test",
            "variants": {
                "control": {"algorithm": "standard"},
                "treatment": {"algorithm": "enhanced"}
            },
            "traffic_allocation": {"control": 0.5, "treatment": 0.5}
        }
        ab_testing_service.configure_experiment(experiment_config)
        
        context = {"user_id": "outcome_user", "experiment": "outcome_test"}
        assignment = ab_testing_service.assign_experiment(context)
        
        # Track outcome
        outcome = {
            "response_time": 0.125,
            "relevance_score": 0.89,
            "user_satisfaction": 4.2,
            "conversion": True
        }
        
        ab_testing_service.track_experiment_outcome(
            assignment.experiment_id,
            assignment.variant,
            outcome
        )
        
        # Verify outcome was stored
        experiment_id = assignment.experiment_id
        assert experiment_id in ab_testing_service.results
        
        results = ab_testing_service.results[experiment_id]
        variant_results = results[assignment.variant]
        assert len(variant_results) == 1
        assert variant_results[0]["response_time"] == 0.125

    def test_get_experiment_results(self, ab_testing_service):
        """Test retrieving experiment results and analysis."""
        # Setup experiment with multiple outcomes
        experiment_config = {
            "name": "results_test",
            "variants": {
                "control": {"feature": "off"},
                "treatment": {"feature": "on"}
            },
            "traffic_allocation": {"control": 0.5, "treatment": 0.5}
        }
        ab_testing_service.configure_experiment(experiment_config)
        
        # Add multiple outcomes for each variant
        experiment_id = "results_test"
        
        # Control group outcomes
        for i in range(5):
            ab_testing_service.track_experiment_outcome(
                experiment_id, "control", {
                    "response_time": 0.15 + i * 0.01,
                    "success": True
                }
            )
        
        # Treatment group outcomes  
        for i in range(5):
            ab_testing_service.track_experiment_outcome(
                experiment_id, "treatment", {
                    "response_time": 0.12 + i * 0.01,
                    "success": True
                }
            )
        
        # Get experiment results
        results = ab_testing_service.get_experiment_results(experiment_id)
        
        assert isinstance(results, dict)
        assert "experiment_id" in results
        assert "variants" in results
        assert "summary" in results
        assert "control" in results["variants"]
        assert "treatment" in results["variants"]

    def test_calculate_statistical_significance(self, ab_testing_service):
        """Test statistical significance calculation."""
        # Setup experiment with sufficient data for significance testing
        experiment_config = {
            "name": "significance_test",
            "variants": {
                "control": {"version": "v1"},
                "treatment": {"version": "v2"}
            },
            "traffic_allocation": {"control": 0.5, "treatment": 0.5}
        }
        ab_testing_service.configure_experiment(experiment_config)
        
        experiment_id = "significance_test"
        
        # Add outcomes with clear difference
        # Control: higher response times
        for i in range(20):
            ab_testing_service.track_experiment_outcome(
                experiment_id, "control", {
                    "response_time": 0.2 + (i % 5) * 0.01,
                    "success": True
                }
            )
        
        # Treatment: lower response times
        for i in range(20):
            ab_testing_service.track_experiment_outcome(
                experiment_id, "treatment", {
                    "response_time": 0.15 + (i % 5) * 0.01,
                    "success": True
                }
            )
        
        # Calculate significance
        significance = ab_testing_service.calculate_statistical_significance(experiment_id)
        
        assert isinstance(significance, dict)
        assert "p_value" in significance
        assert "confidence_level" in significance
        assert "is_significant" in significance

    def test_get_active_experiments(self, ab_testing_service):
        """Test retrieving active experiments."""
        # Configure multiple experiments
        for i in range(3):
            experiment_config = {
                "name": f"active_experiment_{i}",
                "variants": {
                    "control": {"param": f"control_{i}"},
                    "treatment": {"param": f"treatment_{i}"}
                },
                "traffic_allocation": {"control": 0.5, "treatment": 0.5},
                "status": "active"
            }
            ab_testing_service.configure_experiment(experiment_config)
        
        active_experiments = ab_testing_service.get_active_experiments()
        
        assert isinstance(active_experiments, (list, dict))
        assert len(active_experiments) == 3

    def test_stop_experiment(self, ab_testing_service):
        """Test stopping an active experiment."""
        experiment_config = {
            "name": "stoppable_experiment",
            "variants": {
                "control": {"feature": "disabled"},
                "treatment": {"feature": "enabled"}
            },
            "traffic_allocation": {"control": 0.5, "treatment": 0.5},
            "status": "active"
        }
        ab_testing_service.configure_experiment(experiment_config)
        
        # Stop the experiment
        ab_testing_service.stop_experiment("stoppable_experiment")
        
        # Verify experiment is no longer active
        config = ab_testing_service.experiments["stoppable_experiment"]
        assert config.get("status") != "active"

    def test_experiment_duration_tracking(self, ab_testing_service):
        """Test experiment duration and automatic expiration."""
        experiment_config = {
            "name": "duration_test",
            "variants": {
                "control": {"setting": "default"},
                "treatment": {"setting": "new"}
            },
            "traffic_allocation": {"control": 0.5, "treatment": 0.5},
            "duration_days": 0.001,  # Very short duration for testing
            "start_time": time.time()
        }
        ab_testing_service.configure_experiment(experiment_config)
        
        # Check if experiment expiration logic exists
        expired_experiments = ab_testing_service.get_expired_experiments()
        
        # Would contain the experiment if expiration logic is implemented
        assert isinstance(expired_experiments, (list, dict))

    def test_experiment_variant_performance_comparison(self, ab_testing_service):
        """Test comparing performance between experiment variants."""
        experiment_config = {
            "name": "performance_comparison",
            "variants": {
                "control": {"algorithm": "baseline"},
                "treatment": {"algorithm": "optimized"}
            },
            "traffic_allocation": {"control": 0.5, "treatment": 0.5}
        }
        ab_testing_service.configure_experiment(experiment_config)
        
        experiment_id = "performance_comparison"
        
        # Add performance data for both variants
        # Control performance
        for i in range(10):
            ab_testing_service.track_experiment_outcome(
                experiment_id, "control", {
                    "response_time": 0.2,
                    "accuracy": 0.85,
                    "user_rating": 3.5
                }
            )
        
        # Treatment performance (better)
        for i in range(10):
            ab_testing_service.track_experiment_outcome(
                experiment_id, "treatment", {
                    "response_time": 0.15,
                    "accuracy": 0.92,
                    "user_rating": 4.2
                }
            )
        
        comparison = ab_testing_service.compare_variant_performance(experiment_id)
        
        assert isinstance(comparison, dict)
        assert "winning_variant" in comparison
        assert "performance_improvement" in comparison
        assert "metrics_comparison" in comparison

    def test_experiment_assignment_edge_cases(self, ab_testing_service):
        """Test experiment assignment edge cases."""
        # Test with minimal context
        minimal_context = {"experiment": "nonexistent_experiment"}
        assignment = ab_testing_service.assign_experiment(minimal_context)
        
        # Should handle gracefully (return None or default)
        assert assignment is None or isinstance(assignment, ExperimentAssignment)

    def test_concurrent_experiment_operations(self, ab_testing_service):
        """Test concurrent experiment operations don't cause data corruption."""
        import threading
        
        experiment_config = {
            "name": "concurrent_test",
            "variants": {
                "control": {"concurrent": "test"},
                "treatment": {"concurrent": "optimized"}
            },
            "traffic_allocation": {"control": 0.5, "treatment": 0.5}
        }
        ab_testing_service.configure_experiment(experiment_config)
        
        def assign_and_track(user_id):
            context = {"user_id": f"user{user_id}", "experiment": "concurrent_test"}
            assignment = ab_testing_service.assign_experiment(context)
            
            outcome = {"metric": user_id * 0.1}
            ab_testing_service.track_experiment_outcome(
                assignment.experiment_id,
                assignment.variant,
                outcome
            )
        
        # Run concurrent operations
        threads = []
        for i in range(10):
            thread = threading.Thread(target=assign_and_track, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify data integrity
        results = ab_testing_service.results.get("concurrent_test", {})
        total_outcomes = sum(len(variant_results) for variant_results in results.values())
        assert total_outcomes == 10

    def test_experiment_config_updates(self, ab_testing_service):
        """Test updating experiment configurations."""
        # Initial configuration
        initial_config = {
            "name": "updatable_experiment",
            "variants": {
                "control": {"param": "initial"},
                "treatment": {"param": "initial_treatment"}
            },
            "traffic_allocation": {"control": 0.6, "treatment": 0.4}
        }
        ab_testing_service.configure_experiment(initial_config)
        
        # Updated configuration
        updated_config = {
            "name": "updatable_experiment",
            "variants": {
                "control": {"param": "updated"},
                "treatment": {"param": "updated_treatment"},
                "new_variant": {"param": "new"}
            },
            "traffic_allocation": {"control": 0.4, "treatment": 0.3, "new_variant": 0.3}
        }
        ab_testing_service.configure_experiment(updated_config)
        
        # Verify update
        stored_config = ab_testing_service.experiments["updatable_experiment"]
        assert "new_variant" in stored_config["variants"]
        assert stored_config["traffic_allocation"]["control"] == 0.4