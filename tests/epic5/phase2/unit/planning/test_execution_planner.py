"""
Unit tests for ExecutionPlanner.

Tests strategy selection, task ordering, execution graph construction,
and time/cost estimation.
"""

import pytest
from src.components.query_processors.agents.planning.execution_planner import ExecutionPlanner
from src.components.query_processors.agents.models import (
    SubTask,
    ExecutionStrategy,
    QueryAnalysis,
    QueryType,
)


class TestExecutionPlanner:
    """Test suite for ExecutionPlanner."""

    @pytest.fixture
    def planner(self) -> ExecutionPlanner:
        """Create ExecutionPlanner instance."""
        return ExecutionPlanner(optimize_for="latency", avg_task_time=2.0, avg_task_cost=0.02)

    @pytest.fixture
    def cost_planner(self) -> ExecutionPlanner:
        """Create cost-optimized ExecutionPlanner."""
        return ExecutionPlanner(optimize_for="cost")

    # Strategy Selection Tests

    def test_strategy_direct_single_task(self, planner: ExecutionPlanner) -> None:
        """Test DIRECT strategy for single task."""
        tasks = [
            SubTask(
                id="task_0",
                description="Single task",
                query="Do it",
                required_tools=[],
                dependencies=[],
                can_run_parallel=False,
                priority=0,
            )
        ]

        plan = planner.create_plan(tasks, query="test")

        assert plan.strategy == ExecutionStrategy.DIRECT

    def test_strategy_sequential_no_parallelism(self, planner: ExecutionPlanner) -> None:
        """Test SEQUENTIAL strategy when no parallelism possible."""
        tasks = [
            SubTask(id=f"task_{i}", description=f"Task {i}", query=f"Do {i}",
                    required_tools=[], dependencies=[], can_run_parallel=False, priority=i)
            for i in range(3)
        ]

        plan = planner.create_plan(tasks, query="test")

        assert plan.strategy == ExecutionStrategy.SEQUENTIAL

    def test_strategy_parallel_independent_tasks(self, planner: ExecutionPlanner) -> None:
        """Test PARALLEL strategy for independent parallel tasks."""
        tasks = [
            SubTask(id=f"task_{i}", description=f"Task {i}", query=f"Do {i}",
                    required_tools=[], dependencies=[], can_run_parallel=True, priority=i)
            for i in range(3)
        ]

        plan = planner.create_plan(tasks, query="test")

        assert plan.strategy == ExecutionStrategy.PARALLEL

    def test_strategy_hybrid_mixed_dependencies(self, planner: ExecutionPlanner) -> None:
        """Test HYBRID strategy for mixed dependencies and parallelism."""
        tasks = [
            SubTask(id="task_0", description="Task 0", query="Do 0",
                    required_tools=[], dependencies=[], can_run_parallel=False, priority=0),
            SubTask(id="task_1", description="Task 1", query="Do 1",
                    required_tools=[], dependencies=["task_0"], can_run_parallel=True, priority=1),
            SubTask(id="task_2", description="Task 2", query="Do 2",
                    required_tools=[], dependencies=["task_0"], can_run_parallel=True, priority=2),
        ]

        plan = planner.create_plan(tasks, query="test")

        assert plan.strategy == ExecutionStrategy.HYBRID

    def test_strategy_cost_optimization(self, cost_planner: ExecutionPlanner) -> None:
        """Test cost optimization prefers SEQUENTIAL."""
        tasks = [
            SubTask(id=f"task_{i}", description=f"Task {i}", query=f"Do {i}",
                    required_tools=[], dependencies=[], can_run_parallel=True, priority=i)
            for i in range(3)
        ]

        plan = cost_planner.create_plan(tasks, query="test")

        assert plan.strategy == ExecutionStrategy.SEQUENTIAL

    # Task Ordering Tests

    def test_topological_sort_linear(self, planner: ExecutionPlanner) -> None:
        """Test topological sort with linear dependencies."""
        tasks = [
            SubTask(id="task_0", description="Task 0", query="Do 0",
                    required_tools=[], dependencies=[], can_run_parallel=False, priority=0),
            SubTask(id="task_1", description="Task 1", query="Do 1",
                    required_tools=[], dependencies=["task_0"], can_run_parallel=False, priority=1),
            SubTask(id="task_2", description="Task 2", query="Do 2",
                    required_tools=[], dependencies=["task_1"], can_run_parallel=False, priority=2),
        ]

        plan = planner.create_plan(tasks, query="test")

        # Tasks should be in order: task_0, task_1, task_2
        task_ids = [t.id for t in plan.tasks]
        assert task_ids.index("task_0") < task_ids.index("task_1")
        assert task_ids.index("task_1") < task_ids.index("task_2")

    def test_topological_sort_branching(self, planner: ExecutionPlanner) -> None:
        """Test topological sort with branching dependencies."""
        tasks = [
            SubTask(id="task_0", description="Task 0", query="Do 0",
                    required_tools=[], dependencies=[], can_run_parallel=False, priority=0),
            SubTask(id="task_1", description="Task 1", query="Do 1",
                    required_tools=[], dependencies=["task_0"], can_run_parallel=True, priority=1),
            SubTask(id="task_2", description="Task 2", query="Do 2",
                    required_tools=[], dependencies=["task_0"], can_run_parallel=True, priority=2),
            SubTask(id="task_3", description="Task 3", query="Do 3",
                    required_tools=[], dependencies=["task_1", "task_2"], can_run_parallel=False, priority=3),
        ]

        plan = planner.create_plan(tasks, query="test")

        task_ids = [t.id for t in plan.tasks]
        # task_0 must come first
        assert task_ids.index("task_0") == 0
        # task_3 must come last
        assert task_ids.index("task_3") == 3
        # task_1 and task_2 must come before task_3
        assert task_ids.index("task_1") < task_ids.index("task_3")
        assert task_ids.index("task_2") < task_ids.index("task_3")

    # Execution Graph Tests

    def test_execution_graph_construction(self, planner: ExecutionPlanner) -> None:
        """Test execution graph construction."""
        tasks = [
            SubTask(id="task_0", description="Task 0", query="Do 0",
                    required_tools=[], dependencies=[], can_run_parallel=False, priority=0),
            SubTask(id="task_1", description="Task 1", query="Do 1",
                    required_tools=[], dependencies=["task_0"], can_run_parallel=False, priority=1),
        ]

        plan = planner.create_plan(tasks, query="test")

        # Graph should show task_0 → task_1
        assert "task_0" in plan.execution_graph
        assert "task_1" in plan.execution_graph["task_0"]

    def test_execution_graph_multiple_dependents(self, planner: ExecutionPlanner) -> None:
        """Test execution graph with multiple dependents."""
        tasks = [
            SubTask(id="task_0", description="Task 0", query="Do 0",
                    required_tools=[], dependencies=[], can_run_parallel=False, priority=0),
            SubTask(id="task_1", description="Task 1", query="Do 1",
                    required_tools=[], dependencies=["task_0"], can_run_parallel=True, priority=1),
            SubTask(id="task_2", description="Task 2", query="Do 2",
                    required_tools=[], dependencies=["task_0"], can_run_parallel=True, priority=2),
        ]

        plan = planner.create_plan(tasks, query="test")

        # task_0 should have both task_1 and task_2 as dependents
        assert len(plan.execution_graph["task_0"]) == 2
        assert "task_1" in plan.execution_graph["task_0"]
        assert "task_2" in plan.execution_graph["task_0"]

    # Time Estimation Tests

    def test_time_estimation_direct(self, planner: ExecutionPlanner) -> None:
        """Test time estimation for DIRECT strategy."""
        tasks = [
            SubTask(id="task_0", description="Task", query="Do it",
                    required_tools=[], dependencies=[], can_run_parallel=False, priority=0)
        ]

        plan = planner.create_plan(tasks, query="test")

        assert plan.estimated_time == planner.avg_task_time

    def test_time_estimation_sequential(self, planner: ExecutionPlanner) -> None:
        """Test time estimation for SEQUENTIAL strategy."""
        tasks = [
            SubTask(id=f"task_{i}", description=f"Task {i}", query=f"Do {i}",
                    required_tools=[], dependencies=[], can_run_parallel=False, priority=i)
            for i in range(3)
        ]

        plan = planner.create_plan(tasks, query="test")

        # Sequential: 3 tasks * 2.0s = 6.0s
        assert plan.estimated_time == 3 * planner.avg_task_time

    def test_time_estimation_parallel(self, planner: ExecutionPlanner) -> None:
        """Test time estimation for PARALLEL strategy."""
        tasks = [
            SubTask(id=f"task_{i}", description=f"Task {i}", query=f"Do {i}",
                    required_tools=[], dependencies=[], can_run_parallel=True, priority=i)
            for i in range(3)
        ]

        plan = planner.create_plan(tasks, query="test")

        # Parallel: ~2.0s with small overhead
        assert plan.estimated_time < 3 * planner.avg_task_time
        assert plan.estimated_time > planner.avg_task_time

    # Cost Estimation Tests

    def test_cost_estimation_basic(self, planner: ExecutionPlanner) -> None:
        """Test basic cost estimation."""
        tasks = [
            SubTask(id=f"task_{i}", description=f"Task {i}", query=f"Do {i}",
                    required_tools=[], dependencies=[], can_run_parallel=False, priority=i)
            for i in range(3)
        ]

        plan = planner.create_plan(tasks, query="test")

        # Base cost: 3 tasks * $0.02 = $0.06
        assert plan.estimated_cost >= 3 * planner.avg_task_cost

    def test_cost_estimation_parallel_overhead(self, planner: ExecutionPlanner) -> None:
        """Test cost estimation includes parallel overhead."""
        tasks = [
            SubTask(id=f"task_{i}", description=f"Task {i}", query=f"Do {i}",
                    required_tools=[], dependencies=[], can_run_parallel=True, priority=i)
            for i in range(3)
        ]

        plan = planner.create_plan(tasks, query="test")

        # Parallel has 5% overhead
        base_cost = 3 * planner.avg_task_cost
        assert plan.estimated_cost > base_cost

    # Metadata Tests

    def test_metadata_includes_optimization(self, planner: ExecutionPlanner) -> None:
        """Test metadata includes optimization target."""
        tasks = [
            SubTask(id="task_0", description="Task", query="Do it",
                    required_tools=[], dependencies=[], can_run_parallel=False, priority=0)
        ]

        plan = planner.create_plan(tasks, query="test")

        assert "optimization" in plan.metadata
        assert plan.metadata["optimization"] == "latency"

    def test_metadata_includes_task_count(self, planner: ExecutionPlanner) -> None:
        """Test metadata includes task count."""
        tasks = [
            SubTask(id=f"task_{i}", description=f"Task {i}", query=f"Do {i}",
                    required_tools=[], dependencies=[], can_run_parallel=False, priority=i)
            for i in range(3)
        ]

        plan = planner.create_plan(tasks, query="test")

        assert "task_count" in plan.metadata
        assert plan.metadata["task_count"] == 3

    def test_metadata_includes_dependencies_flag(self, planner: ExecutionPlanner) -> None:
        """Test metadata includes has_dependencies flag."""
        tasks = [
            SubTask(id="task_0", description="Task 0", query="Do 0",
                    required_tools=[], dependencies=[], can_run_parallel=False, priority=0),
            SubTask(id="task_1", description="Task 1", query="Do 1",
                    required_tools=[], dependencies=["task_0"], can_run_parallel=False, priority=1),
        ]

        plan = planner.create_plan(tasks, query="test")

        assert "has_dependencies" in plan.metadata
        assert plan.metadata["has_dependencies"] is True

    # Edge Cases

    def test_empty_task_list(self, planner: ExecutionPlanner) -> None:
        """Test handling of empty task list."""
        tasks = []

        plan = planner.create_plan(tasks, query="test")

        assert plan.strategy == ExecutionStrategy.DIRECT
        assert len(plan.tasks) == 0
        assert plan.estimated_time == 0.0
        assert plan.estimated_cost == 0.0

    def test_invalid_dependencies_ignored(self, planner: ExecutionPlanner) -> None:
        """Test invalid dependencies are handled gracefully."""
        tasks = [
            SubTask(id="task_0", description="Task 0", query="Do 0",
                    required_tools=[], dependencies=["nonexistent"], can_run_parallel=False, priority=0),
        ]

        plan = planner.create_plan(tasks, query="test")

        # Should complete without error
        assert len(plan.tasks) == 1

    def test_max_depth_calculation(self, planner: ExecutionPlanner) -> None:
        """Test max depth calculation for time estimation."""
        tasks = [
            SubTask(id="task_0", description="Task 0", query="Do 0",
                    required_tools=[], dependencies=[], can_run_parallel=False, priority=0),
            SubTask(id="task_1", description="Task 1", query="Do 1",
                    required_tools=[], dependencies=["task_0"], can_run_parallel=False, priority=1),
            SubTask(id="task_2", description="Task 2", query="Do 2",
                    required_tools=[], dependencies=["task_1"], can_run_parallel=False, priority=2),
        ]

        plan = planner.create_plan(tasks, query="test")

        # Depth is 3, so time should be based on that
        assert plan.estimated_time > planner.avg_task_time * 2

    def test_plan_id_generated(self, planner: ExecutionPlanner) -> None:
        """Test plan ID is generated."""
        tasks = [
            SubTask(id="task_0", description="Task", query="Do it",
                    required_tools=[], dependencies=[], can_run_parallel=False, priority=0)
        ]

        plan = planner.create_plan(tasks, query="test")

        assert plan.plan_id is not None
        assert len(plan.plan_id) > 0
