"""
Unit tests for PlanExecutor.

Tests plan execution with different strategies, result aggregation,
and error handling.
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.components.query_processors.agents.planning.plan_executor import PlanExecutor
from src.components.query_processors.agents.models import (
    ExecutionPlan,
    ExecutionStrategy,
    SubTask,
    AgentResult,
    ReasoningStep,
    StepType,
)


class TestPlanExecutor:
    """Test suite for PlanExecutor."""

    @pytest.fixture
    def executor(self) -> PlanExecutor:
        """Create PlanExecutor instance."""
        return PlanExecutor(max_parallel_tasks=3, timeout_per_task=60.0)

    @pytest.fixture
    def mock_agent(self) -> Mock:
        """Create mock agent."""
        agent = Mock()
        agent.process = Mock(return_value=AgentResult(
            success=True,
            answer="Test answer",
            reasoning_steps=[],
            tool_calls=[],
            execution_time=1.0,
            total_cost=0.01,
        ))
        return agent

    # Direct Execution Tests

    def test_execute_direct_success(self, executor: PlanExecutor, mock_agent: Mock) -> None:
        """Test direct execution with single query."""
        plan = ExecutionPlan(
            plan_id="test_plan",
            query="What is ML?",
            strategy=ExecutionStrategy.DIRECT,
            tasks=[],
            execution_graph={},
            estimated_time=1.0,
            estimated_cost=0.01,
        )

        result = executor.execute(plan, mock_agent)

        assert result.success
        assert result.final_answer == "Test answer"
        assert "main" in result.task_results
        mock_agent.process.assert_called_once()

    def test_execute_direct_failure(self, executor: PlanExecutor, mock_agent: Mock) -> None:
        """Test direct execution with agent failure."""
        mock_agent.process.return_value = AgentResult(
            success=False,
            answer="",
            reasoning_steps=[],
            tool_calls=[],
            execution_time=1.0,
            total_cost=0.0,
            error="Agent failed",
        )

        plan = ExecutionPlan(
            plan_id="test_plan",
            query="What is ML?",
            strategy=ExecutionStrategy.DIRECT,
            tasks=[],
            execution_graph={},
            estimated_time=1.0,
            estimated_cost=0.01,
        )

        result = executor.execute(plan, mock_agent)

        assert not result.success
        assert result.error == "Agent failed"

    # Sequential Execution Tests

    def test_execute_sequential_success(self, executor: PlanExecutor, mock_agent: Mock) -> None:
        """Test sequential execution of multiple tasks."""
        tasks = [
            SubTask(id=f"task_{i}", description=f"Task {i}", query=f"Do {i}",
                    required_tools=[], dependencies=[], can_run_parallel=False, priority=i)
            for i in range(3)
        ]

        plan = ExecutionPlan(
            plan_id="test_plan",
            query="Multi-step query",
            strategy=ExecutionStrategy.SEQUENTIAL,
            tasks=tasks,
            execution_graph={},
            estimated_time=6.0,
            estimated_cost=0.06,
        )

        result = executor.execute(plan, mock_agent)

        assert result.success
        assert len(result.task_results) == 3
        assert mock_agent.process.call_count == 3

    def test_execute_sequential_task_order(self, executor: PlanExecutor, mock_agent: Mock) -> None:
        """Test tasks are executed in order."""
        executed_tasks = []

        def track_execution(query, context):
            executed_tasks.append(query)
            return AgentResult(
                success=True,
                answer=f"Answer for {query}",
                reasoning_steps=[],
                tool_calls=[],
                execution_time=1.0,
                total_cost=0.01,
            )

        mock_agent.process.side_effect = track_execution

        tasks = [
            SubTask(id="task_0", description="Task 0", query="Query 0",
                    required_tools=[], dependencies=[], can_run_parallel=False, priority=0),
            SubTask(id="task_1", description="Task 1", query="Query 1",
                    required_tools=[], dependencies=["task_0"], can_run_parallel=False, priority=1),
            SubTask(id="task_2", description="Task 2", query="Query 2",
                    required_tools=[], dependencies=["task_1"], can_run_parallel=False, priority=2),
        ]

        plan = ExecutionPlan(
            plan_id="test_plan",
            query="Multi-step query",
            strategy=ExecutionStrategy.SEQUENTIAL,
            tasks=tasks,
            execution_graph={},
            estimated_time=6.0,
            estimated_cost=0.06,
        )

        result = executor.execute(plan, mock_agent)

        assert executed_tasks == ["Query 0", "Query 1", "Query 2"]

    def test_execute_sequential_partial_failure(self, executor: PlanExecutor, mock_agent: Mock) -> None:
        """Test sequential execution continues after task failure."""
        call_count = [0]

        def fail_second_task(query, context):
            call_count[0] += 1
            if call_count[0] == 2:
                return AgentResult(
                    success=False,
                    answer="",
                    reasoning_steps=[],
                    tool_calls=[],
                    execution_time=1.0,
                    total_cost=0.0,
                    error="Task failed",
                )
            return AgentResult(
                success=True,
                answer="Success",
                reasoning_steps=[],
                tool_calls=[],
                execution_time=1.0,
                total_cost=0.01,
            )

        mock_agent.process.side_effect = fail_second_task

        tasks = [
            SubTask(id=f"task_{i}", description=f"Task {i}", query=f"Do {i}",
                    required_tools=[], dependencies=[], can_run_parallel=False, priority=i)
            for i in range(3)
        ]

        plan = ExecutionPlan(
            plan_id="test_plan",
            query="Multi-step query",
            strategy=ExecutionStrategy.SEQUENTIAL,
            tasks=tasks,
            execution_graph={},
            estimated_time=6.0,
            estimated_cost=0.06,
        )

        result = executor.execute(plan, mock_agent)

        assert not result.success  # Overall failure
        assert len(result.task_results) == 3  # All tasks attempted
        assert mock_agent.process.call_count == 3

    # Parallel Execution Tests

    def test_execute_parallel_success(self, executor: PlanExecutor, mock_agent: Mock) -> None:
        """Test parallel execution of independent tasks."""
        tasks = [
            SubTask(id=f"task_{i}", description=f"Task {i}", query=f"Do {i}",
                    required_tools=[], dependencies=[], can_run_parallel=True, priority=i)
            for i in range(3)
        ]

        plan = ExecutionPlan(
            plan_id="test_plan",
            query="Parallel query",
            strategy=ExecutionStrategy.PARALLEL,
            tasks=tasks,
            execution_graph={},
            estimated_time=2.0,
            estimated_cost=0.06,
        )

        result = executor.execute(plan, mock_agent)

        assert result.success
        assert len(result.task_results) == 3
        assert mock_agent.process.call_count == 3

    def test_execute_parallel_partial_failure(self, executor: PlanExecutor, mock_agent: Mock) -> None:
        """Test parallel execution with one task failure."""
        call_count = [0]

        def fail_one_task(query, context):
            call_count[0] += 1
            if call_count[0] == 2:
                return AgentResult(
                    success=False,
                    answer="",
                    reasoning_steps=[],
                    tool_calls=[],
                    execution_time=1.0,
                    total_cost=0.0,
                    error="Task failed",
                )
            return AgentResult(
                success=True,
                answer="Success",
                reasoning_steps=[],
                tool_calls=[],
                execution_time=1.0,
                total_cost=0.01,
            )

        mock_agent.process.side_effect = fail_one_task

        tasks = [
            SubTask(id=f"task_{i}", description=f"Task {i}", query=f"Do {i}",
                    required_tools=[], dependencies=[], can_run_parallel=True, priority=i)
            for i in range(3)
        ]

        plan = ExecutionPlan(
            plan_id="test_plan",
            query="Parallel query",
            strategy=ExecutionStrategy.PARALLEL,
            tasks=tasks,
            execution_graph={},
            estimated_time=2.0,
            estimated_cost=0.06,
        )

        result = executor.execute(plan, mock_agent)

        assert not result.success
        assert len(result.task_results) == 3

    # Hybrid Execution Tests

    def test_execute_hybrid_success(self, executor: PlanExecutor, mock_agent: Mock) -> None:
        """Test hybrid execution with dependency levels."""
        tasks = [
            SubTask(id="task_0", description="Task 0", query="Do 0",
                    required_tools=[], dependencies=[], can_run_parallel=False, priority=0),
            SubTask(id="task_1", description="Task 1", query="Do 1",
                    required_tools=[], dependencies=["task_0"], can_run_parallel=True, priority=1),
            SubTask(id="task_2", description="Task 2", query="Do 2",
                    required_tools=[], dependencies=["task_0"], can_run_parallel=True, priority=2),
        ]

        plan = ExecutionPlan(
            plan_id="test_plan",
            query="Hybrid query",
            strategy=ExecutionStrategy.HYBRID,
            tasks=tasks,
            execution_graph={"task_0": ["task_1", "task_2"], "task_1": [], "task_2": []},
            estimated_time=3.0,
            estimated_cost=0.06,
        )

        result = executor.execute(plan, mock_agent)

        assert result.success
        assert len(result.task_results) == 3
        assert mock_agent.process.call_count == 3

    # Result Aggregation Tests

    def test_aggregate_results_multiple_tasks(self, executor: PlanExecutor, mock_agent: Mock) -> None:
        """Test result aggregation from multiple tasks."""
        tasks = [
            SubTask(id="task_0", description="First task", query="Do 0",
                    required_tools=[], dependencies=[], can_run_parallel=False, priority=0),
            SubTask(id="task_1", description="Second task", query="Do 1",
                    required_tools=[], dependencies=[], can_run_parallel=False, priority=1),
        ]

        plan = ExecutionPlan(
            plan_id="test_plan",
            query="Multi-task query",
            strategy=ExecutionStrategy.SEQUENTIAL,
            tasks=tasks,
            execution_graph={},
            estimated_time=4.0,
            estimated_cost=0.04,
        )

        result = executor.execute(plan, mock_agent)

        # Final answer should include both task descriptions
        assert "First task" in result.final_answer
        assert "Second task" in result.final_answer

    # Context Building Tests

    def test_context_includes_dependencies(self, executor: PlanExecutor, mock_agent: Mock) -> None:
        """Test context includes dependency results."""
        captured_contexts = []

        def capture_context(query, context):
            captured_contexts.append(context)
            return AgentResult(
                success=True,
                answer=f"Answer for {query}",
                reasoning_steps=[],
                tool_calls=[],
                execution_time=1.0,
                total_cost=0.01,
            )

        mock_agent.process.side_effect = capture_context

        tasks = [
            SubTask(id="task_0", description="Task 0", query="Query 0",
                    required_tools=[], dependencies=[], can_run_parallel=False, priority=0),
            SubTask(id="task_1", description="Task 1", query="Query 1",
                    required_tools=[], dependencies=["task_0"], can_run_parallel=False, priority=1),
        ]

        plan = ExecutionPlan(
            plan_id="test_plan",
            query="Multi-step query",
            strategy=ExecutionStrategy.SEQUENTIAL,
            tasks=tasks,
            execution_graph={},
            estimated_time=4.0,
            estimated_cost=0.04,
        )

        result = executor.execute(plan, mock_agent)

        # Second task should have dependency results in context
        assert len(captured_contexts) == 2
        assert "dependency_results" in captured_contexts[1]
        assert "task_0" in captured_contexts[1]["dependency_results"]

    # Metadata Tests

    def test_metadata_includes_strategy(self, executor: PlanExecutor, mock_agent: Mock) -> None:
        """Test metadata includes execution strategy."""
        plan = ExecutionPlan(
            plan_id="test_plan",
            query="Test query",
            strategy=ExecutionStrategy.SEQUENTIAL,
            tasks=[
                SubTask(id="task_0", description="Task", query="Do it",
                        required_tools=[], dependencies=[], can_run_parallel=False, priority=0)
            ],
            execution_graph={},
            estimated_time=2.0,
            estimated_cost=0.02,
        )

        result = executor.execute(plan, mock_agent)

        assert "strategy" in result.metadata
        assert result.metadata["strategy"] == "sequential"

    def test_metadata_includes_task_counts(self, executor: PlanExecutor, mock_agent: Mock) -> None:
        """Test metadata includes task counts."""
        tasks = [
            SubTask(id=f"task_{i}", description=f"Task {i}", query=f"Do {i}",
                    required_tools=[], dependencies=[], can_run_parallel=False, priority=i)
            for i in range(3)
        ]

        plan = ExecutionPlan(
            plan_id="test_plan",
            query="Multi-task query",
            strategy=ExecutionStrategy.SEQUENTIAL,
            tasks=tasks,
            execution_graph={},
            estimated_time=6.0,
            estimated_cost=0.06,
        )

        result = executor.execute(plan, mock_agent)

        assert "completed_tasks" in result.metadata
        assert result.metadata["completed_tasks"] == 3
        assert "total_tasks" in result.metadata
        assert result.metadata["total_tasks"] == 3

    # Cost Tracking Tests

    def test_cost_accumulation(self, executor: PlanExecutor, mock_agent: Mock) -> None:
        """Test cost accumulation across tasks."""
        tasks = [
            SubTask(id=f"task_{i}", description=f"Task {i}", query=f"Do {i}",
                    required_tools=[], dependencies=[], can_run_parallel=False, priority=i)
            for i in range(3)
        ]

        plan = ExecutionPlan(
            plan_id="test_plan",
            query="Multi-task query",
            strategy=ExecutionStrategy.SEQUENTIAL,
            tasks=tasks,
            execution_graph={},
            estimated_time=6.0,
            estimated_cost=0.06,
        )

        result = executor.execute(plan, mock_agent)

        # 3 tasks * $0.01 = $0.03
        assert result.total_cost == pytest.approx(0.03, abs=0.001)

    # Error Handling Tests

    def test_exception_handling(self, executor: PlanExecutor, mock_agent: Mock) -> None:
        """Test exception handling during execution."""
        mock_agent.process.side_effect = Exception("Unexpected error")

        plan = ExecutionPlan(
            plan_id="test_plan",
            query="Test query",
            strategy=ExecutionStrategy.DIRECT,
            tasks=[],
            execution_graph={},
            estimated_time=1.0,
            estimated_cost=0.01,
        )

        result = executor.execute(plan, mock_agent)

        assert not result.success
        assert "Unexpected error" in result.error
        assert result.metadata["error_type"] == "Exception"

    # Edge Cases

    def test_empty_task_list(self, executor: PlanExecutor, mock_agent: Mock) -> None:
        """Test execution with empty task list."""
        plan = ExecutionPlan(
            plan_id="test_plan",
            query="Empty query",
            strategy=ExecutionStrategy.SEQUENTIAL,
            tasks=[],
            execution_graph={},
            estimated_time=0.0,
            estimated_cost=0.0,
        )

        result = executor.execute(plan, mock_agent)

        assert result.success
        assert result.total_cost == 0.0

    def test_execution_time_updated(self, executor: PlanExecutor, mock_agent: Mock) -> None:
        """Test execution time is updated."""
        plan = ExecutionPlan(
            plan_id="test_plan",
            query="Test query",
            strategy=ExecutionStrategy.DIRECT,
            tasks=[],
            execution_graph={},
            estimated_time=1.0,
            estimated_cost=0.01,
        )

        result = executor.execute(plan, mock_agent)

        assert result.execution_time > 0.0
