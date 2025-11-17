"""
Unit tests for Phase 2 data models.

Tests all dataclasses, enums, and validation logic in models.py.
"""

import pytest
from datetime import datetime
from src.components.query_processors.agents.models import (
    # Enums
    StepType,
    QueryType,
    ExecutionStrategy,
    # Results
    ReasoningStep,
    AgentResult,
    ExecutionResult,
    # Configuration
    AgentConfig,
    ProcessorConfig,
    # Planning
    QueryAnalysis,
    SubTask,
    ExecutionPlan,
    # Memory
    Message,
)
from src.components.query_processors.tools.models import ToolCall, ToolResult


class TestEnums:
    """Test enum definitions."""

    def test_step_type_enum(self):
        """Test StepType enum values."""
        assert StepType.THOUGHT.value == "thought"
        assert StepType.ACTION.value == "action"
        assert StepType.OBSERVATION.value == "observation"
        assert StepType.FINAL_ANSWER.value == "final_answer"

    def test_query_type_enum(self):
        """Test QueryType enum values."""
        assert QueryType.SIMPLE.value == "simple"
        assert QueryType.RESEARCH.value == "research"
        assert QueryType.ANALYTICAL.value == "analytical"
        assert QueryType.CODE.value == "code"
        assert QueryType.MULTI_STEP.value == "multi_step"

    def test_execution_strategy_enum(self):
        """Test ExecutionStrategy enum values."""
        assert ExecutionStrategy.DIRECT.value == "direct"
        assert ExecutionStrategy.SEQUENTIAL.value == "sequential"
        assert ExecutionStrategy.PARALLEL.value == "parallel"
        assert ExecutionStrategy.HYBRID.value == "hybrid"


class TestReasoningStep:
    """Test ReasoningStep dataclass."""

    def test_valid_thought_step(self):
        """Test creating valid THOUGHT step."""
        step = ReasoningStep(
            step_number=1,
            step_type=StepType.THOUGHT,
            content="I need to calculate this"
        )
        assert step.step_number == 1
        assert step.step_type == StepType.THOUGHT
        assert step.content == "I need to calculate this"
        assert step.tool_call is None
        assert step.tool_result is None

    def test_valid_action_step(self):
        """Test creating valid ACTION step with tool_call."""
        tool_call = ToolCall(tool_name="calculator", arguments={"expression": "2+2"})
        step = ReasoningStep(
            step_number=2,
            step_type=StepType.ACTION,
            content="Calling calculator",
            tool_call=tool_call
        )
        assert step.step_type == StepType.ACTION
        assert step.tool_call == tool_call

    def test_valid_observation_step(self):
        """Test creating valid OBSERVATION step with tool_result."""
        tool_result = ToolResult(success=True, content="4")
        step = ReasoningStep(
            step_number=3,
            step_type=StepType.OBSERVATION,
            content="Result received",
            tool_result=tool_result
        )
        assert step.step_type == StepType.OBSERVATION
        assert step.tool_result == tool_result

    def test_negative_step_number_raises_error(self):
        """Test that negative step_number raises ValueError."""
        with pytest.raises(ValueError, match="step_number must be non-negative"):
            ReasoningStep(
                step_number=-1,
                step_type=StepType.THOUGHT,
                content="Test"
            )

    def test_action_without_tool_call_raises_error(self):
        """Test that ACTION step without tool_call raises ValueError."""
        with pytest.raises(ValueError, match="ACTION step must have tool_call"):
            ReasoningStep(
                step_number=1,
                step_type=StepType.ACTION,
                content="Calling tool"
            )

    def test_observation_without_tool_result_raises_error(self):
        """Test that OBSERVATION step without tool_result raises ValueError."""
        with pytest.raises(ValueError, match="OBSERVATION step must have tool_result"):
            ReasoningStep(
                step_number=1,
                step_type=StepType.OBSERVATION,
                content="Got result"
            )


class TestAgentResult:
    """Test AgentResult dataclass."""

    def test_valid_success_result(self):
        """Test creating valid successful AgentResult."""
        result = AgentResult(
            success=True,
            answer="The answer is 42",
            reasoning_steps=[],
            tool_calls=[],
            execution_time=1.5,
            total_cost=0.01
        )
        assert result.success is True
        assert result.answer == "The answer is 42"
        assert result.error is None
        assert result.execution_time == 1.5
        assert result.total_cost == 0.01

    def test_valid_failure_result(self):
        """Test creating valid failed AgentResult."""
        result = AgentResult(
            success=False,
            answer="",
            reasoning_steps=[],
            tool_calls=[],
            execution_time=0.5,
            total_cost=0.0,
            error="Processing failed"
        )
        assert result.success is False
        assert result.error == "Processing failed"

    def test_failed_result_without_error_raises_error(self):
        """Test that failed result without error message raises ValueError."""
        with pytest.raises(ValueError, match="Failed AgentResult must have error message"):
            AgentResult(
                success=False,
                answer="",
                reasoning_steps=[],
                tool_calls=[],
                execution_time=0.5,
                total_cost=0.0
            )

    def test_success_result_with_error_raises_error(self):
        """Test that successful result with error message raises ValueError."""
        with pytest.raises(ValueError, match="Successful AgentResult should not have error message"):
            AgentResult(
                success=True,
                answer="Answer",
                reasoning_steps=[],
                tool_calls=[],
                execution_time=1.0,
                total_cost=0.01,
                error="Should not have this"
            )

    def test_negative_execution_time_raises_error(self):
        """Test that negative execution_time raises ValueError."""
        with pytest.raises(ValueError, match="execution_time must be non-negative"):
            AgentResult(
                success=True,
                answer="Answer",
                reasoning_steps=[],
                tool_calls=[],
                execution_time=-1.0,
                total_cost=0.01
            )

    def test_negative_cost_raises_error(self):
        """Test that negative total_cost raises ValueError."""
        with pytest.raises(ValueError, match="total_cost must be non-negative"):
            AgentResult(
                success=True,
                answer="Answer",
                reasoning_steps=[],
                tool_calls=[],
                execution_time=1.0,
                total_cost=-0.01
            )


class TestAgentConfig:
    """Test AgentConfig dataclass."""

    def test_valid_openai_config(self):
        """Test creating valid OpenAI config."""
        config = AgentConfig(
            llm_provider="openai",
            llm_model="gpt-4-turbo"
        )
        assert config.llm_provider == "openai"
        assert config.llm_model == "gpt-4-turbo"
        assert config.temperature == 0.7
        assert config.max_tokens == 2048

    def test_valid_anthropic_config(self):
        """Test creating valid Anthropic config."""
        config = AgentConfig(
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
            temperature=0.5,
            max_tokens=4096
        )
        assert config.llm_provider == "anthropic"
        assert config.temperature == 0.5
        assert config.max_tokens == 4096

    def test_invalid_provider_raises_error(self):
        """Test that invalid provider raises ValueError."""
        with pytest.raises(ValueError, match="llm_provider must be 'openai' or 'anthropic'"):
            AgentConfig(
                llm_provider="invalid",
                llm_model="model"
            )

    def test_invalid_temperature_raises_error(self):
        """Test that invalid temperature raises ValueError."""
        with pytest.raises(ValueError, match="temperature must be between 0.0 and 2.0"):
            AgentConfig(
                llm_provider="openai",
                llm_model="gpt-4",
                temperature=3.0
            )

    def test_invalid_max_tokens_raises_error(self):
        """Test that invalid max_tokens raises ValueError."""
        with pytest.raises(ValueError, match="max_tokens must be positive"):
            AgentConfig(
                llm_provider="openai",
                llm_model="gpt-4",
                max_tokens=0
            )


class TestQueryAnalysis:
    """Test QueryAnalysis dataclass."""

    def test_valid_simple_query_analysis(self):
        """Test creating valid simple query analysis."""
        analysis = QueryAnalysis(
            query_type=QueryType.SIMPLE,
            complexity=0.3,
            intent="information_retrieval",
            entities=["machine learning"],
            requires_tools=[],
            estimated_steps=1
        )
        assert analysis.query_type == QueryType.SIMPLE
        assert analysis.complexity == 0.3
        assert analysis.estimated_steps == 1

    def test_valid_complex_query_analysis(self):
        """Test creating valid complex query analysis."""
        analysis = QueryAnalysis(
            query_type=QueryType.MULTI_STEP,
            complexity=0.9,
            intent="research_and_analysis",
            entities=["ML", "papers", "2024"],
            requires_tools=["document_search", "calculator"],
            estimated_steps=5
        )
        assert analysis.query_type == QueryType.MULTI_STEP
        assert analysis.complexity == 0.9
        assert len(analysis.requires_tools) == 2

    def test_invalid_complexity_too_low_raises_error(self):
        """Test that complexity < 0 raises ValueError."""
        with pytest.raises(ValueError, match="complexity must be between 0.0 and 1.0"):
            QueryAnalysis(
                query_type=QueryType.SIMPLE,
                complexity=-0.1,
                intent="test",
                entities=[],
                requires_tools=[],
                estimated_steps=1
            )

    def test_invalid_complexity_too_high_raises_error(self):
        """Test that complexity > 1 raises ValueError."""
        with pytest.raises(ValueError, match="complexity must be between 0.0 and 1.0"):
            QueryAnalysis(
                query_type=QueryType.SIMPLE,
                complexity=1.5,
                intent="test",
                entities=[],
                requires_tools=[],
                estimated_steps=1
            )

    def test_invalid_estimated_steps_raises_error(self):
        """Test that estimated_steps < 1 raises ValueError."""
        with pytest.raises(ValueError, match="estimated_steps must be at least 1"):
            QueryAnalysis(
                query_type=QueryType.SIMPLE,
                complexity=0.5,
                intent="test",
                entities=[],
                requires_tools=[],
                estimated_steps=0
            )


class TestSubTask:
    """Test SubTask dataclass."""

    def test_valid_subtask(self):
        """Test creating valid SubTask."""
        task = SubTask(
            id="task-1",
            description="Search for papers",
            query="Find ML papers from 2024",
            required_tools=["document_search"],
            dependencies=[],
            can_run_parallel=True,
            priority=1
        )
        assert task.id == "task-1"
        assert task.can_run_parallel is True
        assert task.priority == 1

    def test_empty_id_raises_error(self):
        """Test that empty id raises ValueError."""
        with pytest.raises(ValueError, match="SubTask id cannot be empty"):
            SubTask(
                id="",
                description="Test",
                query="Test query"
            )

    def test_empty_query_raises_error(self):
        """Test that empty query raises ValueError."""
        with pytest.raises(ValueError, match="SubTask query cannot be empty"):
            SubTask(
                id="task-1",
                description="Test",
                query=""
            )

    def test_negative_priority_raises_error(self):
        """Test that negative priority raises ValueError."""
        with pytest.raises(ValueError, match="priority must be non-negative"):
            SubTask(
                id="task-1",
                description="Test",
                query="Test query",
                priority=-1
            )


class TestExecutionPlan:
    """Test ExecutionPlan dataclass."""

    def test_valid_direct_plan(self):
        """Test creating valid direct execution plan."""
        plan = ExecutionPlan(
            plan_id="plan-123",
            query="What is ML?",
            strategy=ExecutionStrategy.DIRECT,
            estimated_time=2.0,
            estimated_cost=0.01
        )
        assert plan.plan_id == "plan-123"
        assert plan.strategy == ExecutionStrategy.DIRECT
        assert len(plan.tasks) == 0

    def test_valid_sequential_plan_with_tasks(self):
        """Test creating valid sequential plan with tasks."""
        tasks = [
            SubTask(id="task-1", description="Step 1", query="Query 1"),
            SubTask(id="task-2", description="Step 2", query="Query 2")
        ]
        plan = ExecutionPlan(
            plan_id="plan-456",
            query="Complex query",
            strategy=ExecutionStrategy.SEQUENTIAL,
            tasks=tasks,
            estimated_time=10.0,
            estimated_cost=0.05
        )
        assert len(plan.tasks) == 2
        assert plan.strategy == ExecutionStrategy.SEQUENTIAL

    def test_empty_plan_id_raises_error(self):
        """Test that empty plan_id raises ValueError."""
        with pytest.raises(ValueError, match="plan_id cannot be empty"):
            ExecutionPlan(
                plan_id="",
                query="Test query",
                strategy=ExecutionStrategy.DIRECT
            )

    def test_empty_query_raises_error(self):
        """Test that empty query raises ValueError."""
        with pytest.raises(ValueError, match="query cannot be empty"):
            ExecutionPlan(
                plan_id="plan-123",
                query="",
                strategy=ExecutionStrategy.DIRECT
            )


class TestExecutionResult:
    """Test ExecutionResult dataclass."""

    def test_valid_success_result(self):
        """Test creating valid successful execution result."""
        result = ExecutionResult(
            success=True,
            final_answer="The answer is 42",
            task_results={"task-1": "result1"},
            execution_time=5.0,
            total_cost=0.02
        )
        assert result.success is True
        assert result.final_answer == "The answer is 42"
        assert result.error is None

    def test_valid_failure_result(self):
        """Test creating valid failed execution result."""
        result = ExecutionResult(
            success=False,
            final_answer="",
            error="Execution failed"
        )
        assert result.success is False
        assert result.error == "Execution failed"

    def test_failed_without_error_raises_error(self):
        """Test that failed result without error raises ValueError."""
        with pytest.raises(ValueError, match="Failed ExecutionResult must have error message"):
            ExecutionResult(
                success=False,
                final_answer=""
            )


class TestMessage:
    """Test Message dataclass."""

    def test_valid_user_message(self):
        """Test creating valid user message."""
        msg = Message(role="user", content="Hello!")
        assert msg.role == "user"
        assert msg.content == "Hello!"
        assert isinstance(msg.timestamp, datetime)

    def test_valid_assistant_message(self):
        """Test creating valid assistant message."""
        msg = Message(role="assistant", content="Hi! How can I help?")
        assert msg.role == "assistant"

    def test_valid_system_message(self):
        """Test creating valid system message."""
        msg = Message(role="system", content="You are a helpful assistant")
        assert msg.role == "system"

    def test_invalid_role_raises_error(self):
        """Test that invalid role raises ValueError."""
        with pytest.raises(ValueError, match="role must be 'user', 'assistant', or 'system'"):
            Message(role="invalid", content="Test")

    def test_empty_content_raises_error(self):
        """Test that empty content raises ValueError."""
        with pytest.raises(ValueError, match="content cannot be empty"):
            Message(role="user", content="")


class TestProcessorConfig:
    """Test ProcessorConfig dataclass."""

    def test_valid_default_config(self):
        """Test creating config with defaults."""
        config = ProcessorConfig()
        assert config.use_agent_by_default is True
        assert config.complexity_threshold == 0.7
        assert config.max_agent_cost == 0.10

    def test_valid_custom_config(self):
        """Test creating custom config."""
        config = ProcessorConfig(
            use_agent_by_default=False,
            complexity_threshold=0.5,
            max_agent_cost=0.25,
            enable_planning=False
        )
        assert config.use_agent_by_default is False
        assert config.complexity_threshold == 0.5
        assert config.enable_planning is False

    def test_invalid_threshold_raises_error(self):
        """Test that invalid threshold raises ValueError."""
        with pytest.raises(ValueError, match="complexity_threshold must be between 0.0 and 1.0"):
            ProcessorConfig(complexity_threshold=1.5)

    def test_negative_cost_raises_error(self):
        """Test that negative cost raises ValueError."""
        with pytest.raises(ValueError, match="max_agent_cost must be non-negative"):
            ProcessorConfig(max_agent_cost=-0.01)
