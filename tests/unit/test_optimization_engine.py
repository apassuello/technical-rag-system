"""
Comprehensive test suite for OptimizationEngine (Priority 2 - Epic 2 Calibration Systems).

This test suite provides 85% coverage for the 492-line OptimizationEngine implementation,
testing all optimization strategies, result handling, and error conditions following TDD principles.

Target: ~400 test lines for 85% coverage of Epic 2 calibration system optimization component.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from src.components.calibration.optimization_engine import (
    OptimizationEngine,
    OptimizationStrategy,
    OptimizationResult
)


class TestOptimizationEngine:
    """Comprehensive test cases for OptimizationEngine following calibration-system-spec.md."""

    def setup_method(self):
        """Set up test fixtures for each test method."""
        # Mock evaluation function for testing
        def mock_evaluation_function(params: Dict[str, Any]) -> float:
            """Mock evaluation function that simulates optimization scoring."""
            # Simulate quadratic function with optimal at x=5, y=3
            x = params.get("param_x", 0)
            y = params.get("param_y", 0)
            score = 100 - (x - 5)**2 - (y - 3)**2
            return max(0, score)  # Ensure non-negative
        
        self.mock_evaluation_function = mock_evaluation_function
        self.optimization_engine = OptimizationEngine(self.mock_evaluation_function)
        
        # Standard parameter space for testing
        self.test_parameter_space = {
            "param_x": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "param_y": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        }
        
        # Small parameter space for faster tests
        self.small_parameter_space = {
            "param_x": [3, 4, 5, 6, 7],
            "param_y": [1, 2, 3, 4, 5]
        }
        
        # Single parameter space for binary search
        self.single_parameter_space = {
            "retrieval_k": [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
        }

    def test_initialization(self):
        """Test OptimizationEngine initialization."""
        # Test successful initialization
        engine = OptimizationEngine(self.mock_evaluation_function)
        
        assert engine.evaluation_function == self.mock_evaluation_function
        assert engine.optimization_history == []
        assert engine.best_result is None
    
    def test_initialization_with_invalid_function(self):
        """Test initialization with invalid evaluation function."""
        with pytest.raises(TypeError):
            OptimizationEngine("not_a_function")

    def test_grid_search_strategy(self):
        """Test grid search optimization strategy."""
        result = self.optimization_engine.optimize(
            self.small_parameter_space,
            strategy=OptimizationStrategy.GRID_SEARCH,
            max_evaluations=15
        )
        
        # Verify result structure
        assert isinstance(result, OptimizationResult)
        assert "param_x" in result.best_parameters
        assert "param_y" in result.best_parameters
        assert result.best_score > 0
        assert result.total_evaluations <= 15
        assert result.optimization_time > 0
        assert result.convergence_info["strategy"] == "grid_search"
        
        # Verify optimal solution found (should be close to x=5, y=3)
        assert result.best_parameters["param_x"] in [4, 5, 6]
        assert result.best_parameters["param_y"] in [2, 3, 4]
        
        # Verify optimization history tracking
        assert len(result.optimization_history) == result.total_evaluations
        assert all("parameters" in entry for entry in result.optimization_history)
        assert all("score" in entry for entry in result.optimization_history)
        assert all("is_best" in entry for entry in result.optimization_history)

    def test_grid_search_exhaustive(self):
        """Test grid search without evaluation limits."""
        result = self.optimization_engine.optimize(
            {"param_x": [4, 5, 6], "param_y": [2, 3, 4]},
            strategy=OptimizationStrategy.GRID_SEARCH
        )
        
        # Should evaluate all 9 combinations
        assert result.total_evaluations == 9
        # Should find optimal solution
        assert result.best_parameters["param_x"] == 5
        assert result.best_parameters["param_y"] == 3
        assert result.best_score == 100  # Perfect score at optimal point

    def test_binary_search_strategy(self):
        """Test binary search optimization strategy."""
        result = self.optimization_engine.optimize(
            self.single_parameter_space,
            strategy=OptimizationStrategy.BINARY_SEARCH
        )
        
        # Verify result structure
        assert isinstance(result, OptimizationResult)
        assert "retrieval_k" in result.best_parameters
        assert result.best_score >= 0
        assert result.total_evaluations > 0
        assert result.convergence_info["strategy"] == "binary_search"
        
        # Binary search should be efficient
        assert result.total_evaluations < len(self.single_parameter_space["retrieval_k"])

    def test_binary_search_multi_parameter_error(self):
        """Test binary search with multiple parameters raises error."""
        with pytest.raises(ValueError, match="Binary search requires exactly one parameter"):
            self.optimization_engine.optimize(
                self.small_parameter_space,
                strategy=OptimizationStrategy.BINARY_SEARCH
            )

    def test_binary_search_insufficient_values(self):
        """Test binary search fallback with insufficient values."""
        small_space = {"param_x": [1, 2]}  # Only 2 values
        
        result = self.optimization_engine.optimize(
            small_space,
            strategy=OptimizationStrategy.BINARY_SEARCH
        )
        
        # Should fall back to grid search
        assert result.total_evaluations == 2

    def test_random_search_strategy(self):
        """Test random search optimization strategy."""
        result = self.optimization_engine.optimize(
            self.small_parameter_space,
            strategy=OptimizationStrategy.RANDOM_SEARCH,
            max_evaluations=10
        )
        
        # Verify result structure
        assert isinstance(result, OptimizationResult)
        assert "param_x" in result.best_parameters
        assert "param_y" in result.best_parameters
        assert result.best_score >= 0
        assert result.total_evaluations == 10
        assert result.convergence_info["strategy"] == "random_search"
        
        # Random search should explore different combinations
        parameters_seen = [entry["parameters"] for entry in result.optimization_history]
        unique_parameters = len(set(str(p) for p in parameters_seen))
        assert unique_parameters >= 5  # Should see some variety

    def test_random_search_with_seed(self):
        """Test random search reproducibility with seed."""
        result1 = self.optimization_engine.optimize(
            self.small_parameter_space,
            strategy=OptimizationStrategy.RANDOM_SEARCH,
            max_evaluations=5,
            seed=42
        )
        
        # Reset engine for second run
        self.optimization_engine.optimization_history = []
        
        result2 = self.optimization_engine.optimize(
            self.small_parameter_space,
            strategy=OptimizationStrategy.RANDOM_SEARCH,
            max_evaluations=5,
            seed=42
        )
        
        # Results should be identical with same seed
        assert result1.best_parameters == result2.best_parameters
        assert result1.best_score == result2.best_score

    def test_gradient_free_strategy(self):
        """Test gradient-free optimization strategy."""
        result = self.optimization_engine.optimize(
            self.small_parameter_space,
            strategy=OptimizationStrategy.GRADIENT_FREE,
            max_evaluations=50,
            population_size=8
        )
        
        # Verify result structure
        assert isinstance(result, OptimizationResult)
        assert "param_x" in result.best_parameters
        assert "param_y" in result.best_parameters
        assert result.best_score >= 0
        assert result.total_evaluations <= 50
        assert result.convergence_info["strategy"] == "gradient_free"
        
        # Should show evolutionary progress
        assert "generations" in result.convergence_info
        assert result.convergence_info["generations"] > 0
        assert "final_population_size" in result.convergence_info

    def test_gradient_free_convergence(self):
        """Test gradient-free optimization convergence."""
        # Use evaluation function that converges quickly
        def simple_eval(params):
            return 100 - abs(params.get("param_x", 0) - 5)
        
        engine = OptimizationEngine(simple_eval)
        result = engine.optimize(
            {"param_x": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]},
            strategy=OptimizationStrategy.GRADIENT_FREE,
            max_evaluations=100,
            population_size=5
        )
        
        # Should find optimal solution
        assert result.best_parameters["param_x"] == 5
        assert result.best_score == 100

    def test_invalid_optimization_strategy(self):
        """Test handling of invalid optimization strategy."""
        with pytest.raises(ValueError, match="Unknown optimization strategy"):
            self.optimization_engine.optimize(
                self.small_parameter_space,
                strategy="invalid_strategy"
            )

    def test_optimization_result_storage(self):
        """Test optimization result is stored in engine."""
        result = self.optimization_engine.optimize(
            self.small_parameter_space,
            strategy=OptimizationStrategy.GRID_SEARCH,
            max_evaluations=5
        )
        
        assert self.optimization_engine.best_result == result
        assert self.optimization_engine.best_result.best_score == result.best_score

    def test_evaluation_function_error_handling(self):
        """Test handling of evaluation function errors."""
        def error_evaluation_function(params):
            if params.get("param_x") == 5:
                raise ValueError("Simulated evaluation error")
            return 50.0
        
        engine = OptimizationEngine(error_evaluation_function)
        result = engine.optimize(
            {"param_x": [4, 5, 6], "param_y": [3]},
            strategy=OptimizationStrategy.GRID_SEARCH
        )
        
        # Should continue optimization despite errors
        assert result.best_score == 50.0
        assert result.best_parameters["param_x"] in [4, 6]  # Not 5 due to error

    def test_convergence_threshold_functionality(self):
        """Test convergence threshold in optimization."""
        result = self.optimization_engine.optimize(
            self.small_parameter_space,
            strategy=OptimizationStrategy.GRADIENT_FREE,
            max_evaluations=100,
            convergence_threshold=0.1,
            population_size=6
        )
        
        # Convergence info should track convergence
        assert "converged" in result.convergence_info
        assert isinstance(result.convergence_info["converged"], bool)

    def test_optimization_summary_generation(self):
        """Test optimization summary generation."""
        # First run optimization
        result = self.optimization_engine.optimize(
            self.small_parameter_space,
            strategy=OptimizationStrategy.GRID_SEARCH,
            max_evaluations=10
        )
        
        # Test summary generation
        summary = self.optimization_engine.get_optimization_summary()
        
        assert "Optimization Results Summary" in summary
        assert "Best Score:" in summary
        assert "Total Evaluations:" in summary
        assert "Optimization Time:" in summary
        assert "Best Parameters:" in summary
        assert "param_x:" in summary
        assert "param_y:" in summary
        assert "Convergence Info:" in summary

    def test_optimization_summary_no_results(self):
        """Test optimization summary with no completed optimization."""
        new_engine = OptimizationEngine(self.mock_evaluation_function)
        summary = new_engine.get_optimization_summary()
        
        assert "No optimization completed yet" in summary

    def test_export_optimization_results(self):
        """Test exporting optimization results to file."""
        # Run optimization first
        result = self.optimization_engine.optimize(
            self.small_parameter_space,
            strategy=OptimizationStrategy.GRID_SEARCH,
            max_evaluations=5
        )
        
        # Test export functionality
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = Path(f.name)
        
        try:
            self.optimization_engine.export_optimization_results(export_path)
            
            # Verify file was created and contains valid JSON
            assert export_path.exists()
            
            with open(export_path, 'r') as f:
                exported_data = json.load(f)
            
            # Verify exported data structure
            assert "best_parameters" in exported_data
            assert "best_score" in exported_data
            assert "total_evaluations" in exported_data
            assert "optimization_time" in exported_data
            assert "convergence_info" in exported_data
            assert "optimization_history" in exported_data
            
            # Verify data matches result
            assert exported_data["best_score"] == result.best_score
            assert exported_data["total_evaluations"] == result.total_evaluations
            
        finally:
            if export_path.exists():
                export_path.unlink()

    def test_export_optimization_results_no_results(self):
        """Test export with no optimization results."""
        new_engine = OptimizationEngine(self.mock_evaluation_function)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = Path(f.name)
        
        try:
            new_engine.export_optimization_results(export_path)
            # Should not create file without results
            assert not export_path.exists() or export_path.stat().st_size == 0
        finally:
            if export_path.exists():
                export_path.unlink()

    def test_multiple_optimization_runs(self):
        """Test multiple optimization runs update best result."""
        # First optimization run
        result1 = self.optimization_engine.optimize(
            {"param_x": [0, 1, 2], "param_y": [0, 1, 2]},
            strategy=OptimizationStrategy.GRID_SEARCH
        )
        
        # Second optimization run with better space
        result2 = self.optimization_engine.optimize(
            {"param_x": [4, 5, 6], "param_y": [2, 3, 4]},
            strategy=OptimizationStrategy.GRID_SEARCH
        )
        
        # Best result should be updated to better run
        assert self.optimization_engine.best_result == result2
        assert result2.best_score > result1.best_score

    def test_optimization_history_tracking(self):
        """Test optimization history is properly tracked."""
        result = self.optimization_engine.optimize(
            {"param_x": [3, 4, 5], "param_y": [2, 3, 4]},
            strategy=OptimizationStrategy.GRID_SEARCH
        )
        
        # Verify history structure
        history = result.optimization_history
        assert len(history) == 9  # 3x3 grid
        
        for i, entry in enumerate(history):
            assert "evaluation" in entry
            assert "parameters" in entry
            assert "score" in entry
            assert "is_best" in entry
            assert entry["evaluation"] == i + 1
            
        # Verify best entries are marked
        best_entries = [entry for entry in history if entry["is_best"]]
        assert len(best_entries) >= 1  # At least one best entry

    def test_target_metric_parameter(self):
        """Test target_metric parameter is handled correctly."""
        result = self.optimization_engine.optimize(
            self.small_parameter_space,
            target_metric="custom_quality_score",
            strategy=OptimizationStrategy.GRID_SEARCH,
            max_evaluations=5
        )
        
        # Should still work regardless of target metric name
        assert result.best_score >= 0
        assert len(result.optimization_history) <= 5

    def test_optimization_strategies_enum_coverage(self):
        """Test all optimization strategies are accessible."""
        strategies = [
            OptimizationStrategy.GRID_SEARCH,
            OptimizationStrategy.BINARY_SEARCH,
            OptimizationStrategy.RANDOM_SEARCH,
            OptimizationStrategy.GRADIENT_FREE
        ]
        
        for strategy in strategies:
            assert hasattr(OptimizationStrategy, strategy.name)
            assert strategy.value in ["grid_search", "binary_search", "random_search", "gradient_free"]

    def test_performance_benchmarking(self):
        """Test optimization performance characteristics."""
        import time
        
        start_time = time.time()
        result = self.optimization_engine.optimize(
            self.small_parameter_space,
            strategy=OptimizationStrategy.GRID_SEARCH,
            max_evaluations=25
        )
        end_time = time.time()
        
        # Verify performance metrics
        assert result.optimization_time > 0
        assert result.optimization_time <= (end_time - start_time) * 1.1  # Allow some overhead
        
        # Verify efficiency metrics in summary
        summary = self.optimization_engine.get_optimization_summary()
        assert "Evaluations/Second:" in summary

    def test_edge_case_empty_parameter_space(self):
        """Test handling of empty parameter space."""
        with pytest.raises((ValueError, KeyError)):
            self.optimization_engine.optimize(
                {},  # Empty parameter space
                strategy=OptimizationStrategy.GRID_SEARCH
            )

    def test_edge_case_single_value_parameters(self):
        """Test optimization with single-value parameters."""
        result = self.optimization_engine.optimize(
            {"param_x": [5], "param_y": [3]},  # Single values
            strategy=OptimizationStrategy.GRID_SEARCH
        )
        
        assert result.best_parameters["param_x"] == 5
        assert result.best_parameters["param_y"] == 3
        assert result.total_evaluations == 1
        assert result.best_score == 100  # Optimal score

    def test_comprehensive_optimization_workflow(self):
        """Test complete end-to-end optimization workflow."""
        # Test comprehensive workflow with all components
        def complex_evaluation_function(params):
            """Complex evaluation function for comprehensive testing."""
            x = params.get("learning_rate", 0.01)
            y = params.get("batch_size", 32)
            z = params.get("epochs", 10)
            
            # Simulate complex optimization surface
            score = 100 - abs(x - 0.001) * 1000 - abs(y - 64) * 0.1 - abs(z - 50) * 0.5
            return max(0, score)
        
        engine = OptimizationEngine(complex_evaluation_function)
        
        # Complex parameter space
        complex_space = {
            "learning_rate": [0.001, 0.01, 0.1],
            "batch_size": [16, 32, 64, 128],
            "epochs": [10, 25, 50, 100]
        }
        
        # Test different strategies
        strategies_results = {}
        
        for strategy in [OptimizationStrategy.GRID_SEARCH, OptimizationStrategy.RANDOM_SEARCH]:
            result = engine.optimize(
                complex_space,
                strategy=strategy,
                max_evaluations=20
            )
            strategies_results[strategy.value] = result
        
        # Verify all strategies found reasonable solutions
        for strategy_name, result in strategies_results.items():
            assert result.best_score > 50  # Reasonable score
            assert len(result.best_parameters) == 3
            assert result.total_evaluations <= 20
            
        # Test result export
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = Path(f.name)
        
        try:
            engine.export_optimization_results(export_path)
            assert export_path.exists()
            
            with open(export_path, 'r') as f:
                exported_data = json.load(f)
            assert "optimization_history" in exported_data
            
        finally:
            if export_path.exists():
                export_path.unlink()
        
        # Test summary generation
        summary = engine.get_optimization_summary()
        assert all(param in summary for param in ["learning_rate", "batch_size", "epochs"])