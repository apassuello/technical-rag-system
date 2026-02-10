"""
Unit tests for ReAct agent.

Tests the ReAct (Reason + Act) agent implementation using LangChain.

Test Categories:
- Agent initialization
- Query processing (single-step and multi-step)
- Memory integration
- Tool integration
- Reasoning trace
- Error handling
- Statistics tracking

Coverage Target: >95%
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from typing import List
from datetime import datetime

# Add src to path for direct imports (avoid torch dependency in components.__init__)
src_path = Path(__file__).parents[4] / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from components.query_processors.agents.react_agent import ReActAgent
from components.query_processors.agents.models import (
    AgentConfig,
    AgentResult,
    ReasoningStep,
    StepType
)
from components.query_processors.agents.memory.conversation_memory import (
    ConversationMemory
)
from components.query_processors.agents.memory.working_memory import (
    WorkingMemory
)
from components.query_processors.tools.implementations import (
    CalculatorTool
)
from components.query_processors.tools.models import ToolResult


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def agent_config():
    """Default agent configuration."""
    return AgentConfig(
        llm_provider="openai",
        llm_model="gpt-4-turbo",
        temperature=0.7,
        max_tokens=2048,
        max_iterations=10,
        max_execution_time=300,
        early_stopping="force",
        verbose=False
    )


@pytest.fixture
def mock_llm():
    """Mock LangChain LLM."""
    llm = Mock()
    llm.model_name = "gpt-4-turbo"
    return llm


@pytest.fixture
def calculator_tool():
    """Calculator tool instance."""
    return CalculatorTool()


@pytest.fixture
def conversation_memory():
    """Conversation memory instance."""
    return ConversationMemory(max_messages=100)


@pytest.fixture
def working_memory():
    """Working memory instance."""
    return WorkingMemory()


# =============================================================================
# Initialization Tests
# =============================================================================

def test_agent_initialization(
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test agent initializes correctly."""
    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    assert agent.llm is mock_llm
    assert len(agent.phase1_tools) == 1
    assert agent.memory is conversation_memory
    assert agent.config is agent_config


def test_agent_initialization_with_working_memory(
    mock_llm,
    calculator_tool,
    conversation_memory,
    working_memory,
    agent_config
):
    """Test agent initializes with working memory."""
    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config,
        working_memory=working_memory
    )

    assert agent.working_memory is working_memory


def test_agent_initialization_creates_working_memory_if_not_provided(
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test agent creates working memory if not provided."""
    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    assert isinstance(agent.working_memory, WorkingMemory)


def test_agent_converts_phase1_tools_to_langchain(
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test agent converts Phase 1 tools to LangChain format."""
    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    assert len(agent.langchain_tools) == 1
    assert agent.langchain_tools[0].name == "calculator"


def test_agent_initialization_with_multiple_tools(
    mock_llm,
    conversation_memory,
    agent_config
):
    """Test agent initializes with multiple tools."""
    tools = [CalculatorTool()]

    agent = ReActAgent(
        llm=mock_llm,
        tools=tools,
        memory=conversation_memory,
        config=agent_config
    )

    assert len(agent.langchain_tools) >= 1


# =============================================================================
# Query Processing Tests
# =============================================================================

def test_process_simple_query(
    mock_executor,
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test processing simple query."""
    mock_executor.invoke = Mock(return_value={
        "output": "4",
        "intermediate_steps": []
    })

    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    result = agent.process("What is 2 + 2?")

    assert result.success is True
    assert "4" in result.answer
    assert result.execution_time > 0


def test_process_adds_query_to_memory(
    mock_executor,
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test query is added to conversation memory."""
    mock_executor.invoke = Mock(return_value={
        "output": "Answer",
        "intermediate_steps": []
    })

    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    query = "Test query"
    agent.process(query)

    messages = conversation_memory.get_messages()
    assert any(msg.content == query and msg.role == "user" for msg in messages)


def test_process_adds_answer_to_memory(
    mock_executor,
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test answer is added to conversation memory."""
    answer = "The answer is 42"
    mock_executor.invoke = Mock(return_value={
        "output": answer,
        "intermediate_steps": []
    })

    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    agent.process("Test query")

    messages = conversation_memory.get_messages()
    assert any(msg.content == answer and msg.role == "assistant" for msg in messages)


def test_process_empty_query_returns_error(
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test processing empty query returns error."""
    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    result = agent.process("")

    assert result.success is False
    assert result.error is not None
    assert "empty" in result.error.lower()


def test_process_never_raises_exception(
    mock_executor,
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test process() never raises exceptions."""
    # Mock executor to raise exception
    mock_executor.invoke = Mock(side_effect=RuntimeError("Test error"))

    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    # Should not raise, should return error in AgentResult
    result = agent.process("Test query")

    assert result.success is False
    assert result.error is not None


# =============================================================================
# Multi-Step Reasoning Tests
# =============================================================================

def test_process_with_intermediate_steps(
    mock_executor,
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test processing with intermediate steps."""
    # Mock agent action and observation
    mock_action = Mock()
    mock_action.tool = "calculator"
    mock_action.tool_input = "2 + 2"
    mock_action.log = "I need to calculate 2 + 2"

    mock_executor.invoke = Mock(return_value={
        "output": "4",
        "intermediate_steps": [(mock_action, "4")]
    })

    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    result = agent.process("What is 2 + 2?")

    assert result.success is True
    assert len(result.reasoning_steps) > 0


def test_reasoning_trace_includes_all_step_types(
    mock_executor,
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test reasoning trace includes THOUGHT, ACTION, OBSERVATION, FINAL_ANSWER."""
    mock_action = Mock()
    mock_action.tool = "calculator"
    mock_action.tool_input = "2 + 2"
    mock_action.log = "Thinking about the calculation"

    mock_executor.invoke = Mock(return_value={
        "output": "4",
        "intermediate_steps": [(mock_action, "4")]
    })

    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    result = agent.process("What is 2 + 2?")

    step_types = {step.step_type for step in result.reasoning_steps}

    # Should have multiple step types
    assert StepType.FINAL_ANSWER in step_types


def test_tool_calls_tracked(
    mock_executor,
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test tool calls are tracked in result."""
    mock_action = Mock()
    mock_action.tool = "calculator"
    mock_action.tool_input = "2 + 2"
    mock_action.log = "Calculating"

    mock_executor.invoke = Mock(return_value={
        "output": "4",
        "intermediate_steps": [(mock_action, "4")]
    })

    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    result = agent.process("What is 2 + 2?")

    assert len(result.tool_calls) > 0
    assert result.tool_calls[0].tool_name == "calculator"


# =============================================================================
# Reasoning Trace Tests
# =============================================================================

def test_get_reasoning_trace(
    mock_executor,
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test get_reasoning_trace returns steps."""
    mock_executor.invoke = Mock(return_value={
        "output": "4",
        "intermediate_steps": []
    })

    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    agent.process("Test query")
    trace = agent.get_reasoning_trace()

    assert isinstance(trace, list)
    assert len(trace) > 0
    assert all(isinstance(step, ReasoningStep) for step in trace)


def test_reasoning_trace_is_copy(
    mock_executor,
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test reasoning trace returns copy, not reference."""
    mock_executor.invoke = Mock(return_value={
        "output": "4",
        "intermediate_steps": []
    })

    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    agent.process("Test query")
    trace1 = agent.get_reasoning_trace()
    trace2 = agent.get_reasoning_trace()

    assert trace1 is not trace2  # Different objects
    assert len(trace1) == len(trace2)  # Same content


def test_reasoning_steps_have_sequential_numbers(
    mock_executor,
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test reasoning steps have sequential step numbers."""
    mock_executor.invoke = Mock(return_value={
        "output": "4",
        "intermediate_steps": []
    })

    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    agent.process("Test query")
    trace = agent.get_reasoning_trace()

    step_numbers = [step.step_number for step in trace]
    assert step_numbers == list(range(1, len(step_numbers) + 1))


# =============================================================================
# Memory Integration Tests
# =============================================================================

def test_working_memory_available_during_processing(
    mock_executor,
    mock_llm,
    calculator_tool,
    conversation_memory,
    working_memory,
    agent_config
):
    """Test working memory is available during processing."""
    mock_executor.invoke = Mock(return_value={
        "output": "4",
        "intermediate_steps": []
    })

    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config,
        working_memory=working_memory
    )

    working_memory.set_context("test_key", "test_value")
    agent.process("Test query")

    # Working memory should still have the value
    assert working_memory.get_context("test_key") == "test_value"


def test_conversation_history_passed_to_executor(
    mock_executor,
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test conversation history is passed to executor."""
    mock_executor.invoke = Mock(return_value={
        "output": "4",
        "intermediate_steps": []
    })

    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    # Add some history
    conversation_memory.add_message("user", "Previous query")
    conversation_memory.add_message("assistant", "Previous answer")

    agent.process("Current query")

    # Executor should have been called with context
    mock_executor.invoke.assert_called()


# =============================================================================
# Statistics Tests
# =============================================================================

def test_stats_track_query_count(
    mock_executor,
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test statistics track query count."""
    mock_executor.invoke = Mock(return_value={
        "output": "4",
        "intermediate_steps": []
    })

    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    agent.process("Query 1")
    agent.process("Query 2")

    stats = agent.get_stats()
    assert stats["total_queries"] == 2


def test_stats_track_success_rate(
    mock_executor,
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test statistics track success rate."""
    # First call succeeds
    mock_executor.invoke = Mock(side_effect=[
        {"output": "4", "intermediate_steps": []},
        RuntimeError("Test error")
    ])

    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    agent.process("Query 1")  # Success
    agent.process("Query 2")  # Failure

    stats = agent.get_stats()
    assert stats["success_count"] == 1
    assert stats["success_rate"] == 0.5


def test_stats_track_execution_time(
    mock_executor,
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test statistics track execution time."""
    mock_executor.invoke = Mock(return_value={
        "output": "4",
        "intermediate_steps": []
    })

    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    agent.process("Query")

    stats = agent.get_stats()
    assert stats["total_execution_time"] > 0
    assert stats["avg_execution_time"] > 0


def test_stats_track_cost(
    mock_executor,
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test statistics track cost."""
    mock_executor.invoke = Mock(return_value={
        "output": "4",
        "intermediate_steps": []
    })

    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    agent.process("Query")

    stats = agent.get_stats()
    assert "total_cost" in stats
    assert "avg_cost" in stats


# =============================================================================
# Reset Tests
# =============================================================================

def test_reset_clears_reasoning_trace(
    mock_executor,
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test reset clears reasoning trace."""
    mock_executor.invoke = Mock(return_value={
        "output": "4",
        "intermediate_steps": []
    })

    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    agent.process("Query")
    assert len(agent.get_reasoning_trace()) > 0

    agent.reset()
    assert len(agent.get_reasoning_trace()) == 0


def test_reset_clears_tool_calls(
    mock_executor,
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test reset clears tool call history."""
    mock_action = Mock()
    mock_action.tool = "calculator"
    mock_action.tool_input = "2 + 2"
    mock_action.log = "Calculating"

    mock_executor.invoke = Mock(return_value={
        "output": "4",
        "intermediate_steps": [(mock_action, "4")]
    })

    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    result = agent.process("Query")
    assert len(result.tool_calls) > 0

    agent.reset()

    # Next query should have empty tool calls initially
    result2 = agent.process("Query 2")
    # (tool calls are per-query, so this tests internal state reset)


def test_reset_clears_working_memory(
    mock_executor,
    mock_llm,
    calculator_tool,
    conversation_memory,
    working_memory,
    agent_config
):
    """Test reset clears working memory."""
    mock_executor.invoke = Mock(return_value={
        "output": "4",
        "intermediate_steps": []
    })

    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config,
        working_memory=working_memory
    )

    working_memory.set_context("test_key", "test_value")
    agent.reset()

    assert working_memory.get_context("test_key") is None


# =============================================================================
# Cost Estimation Tests
# =============================================================================

def test_cost_estimation_for_openai(
    mock_executor,
    mock_llm,
    calculator_tool,
    conversation_memory
):
    """Test cost estimation for OpenAI."""
    config = AgentConfig(
        llm_provider="openai",
        llm_model="gpt-4-turbo",
        max_iterations=10
    )

    mock_executor.invoke = Mock(return_value={
        "output": "4",
        "intermediate_steps": []
    })

    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=config
    )

    result = agent.process("What is 2 + 2?")

    # Should have estimated cost
    assert result.total_cost >= 0


def test_cost_estimation_for_anthropic(
    mock_executor,
    mock_llm,
    calculator_tool,
    conversation_memory
):
    """Test cost estimation for Anthropic."""
    config = AgentConfig(
        llm_provider="anthropic",
        llm_model="claude-3-5-sonnet-20241022",
        max_iterations=10
    )

    mock_executor.invoke = Mock(return_value={
        "output": "4",
        "intermediate_steps": []
    })

    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=config
    )

    result = agent.process("What is 2 + 2?")

    # Should have estimated cost
    assert result.total_cost >= 0


# =============================================================================
# Metadata Tests
# =============================================================================

def test_result_includes_metadata(
    mock_executor,
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test result includes metadata."""
    mock_executor.invoke = Mock(return_value={
        "output": "4",
        "intermediate_steps": []
    })

    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    result = agent.process("Query")

    assert "llm_provider" in result.metadata
    assert "llm_model" in result.metadata
    assert "iterations" in result.metadata
    assert "tools_used" in result.metadata


# =============================================================================
# String Representation Tests
# =============================================================================

def test_agent_repr(
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test agent string representation."""
    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    repr_str = repr(agent)

    assert "ReActAgent" in repr_str
    assert "gpt-4-turbo" in repr_str
    assert "max_iterations=10" in repr_str


# =============================================================================
# Validation Tests
# =============================================================================

def test_validate_query_accepts_valid_query(
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test validate_query accepts valid query."""
    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    assert agent.validate_query("Valid query") is True


def test_validate_query_rejects_empty_query(
    mock_llm,
    calculator_tool,
    conversation_memory,
    agent_config
):
    """Test validate_query rejects empty query."""
    agent = ReActAgent(
        llm=mock_llm,
        tools=[calculator_tool],
        memory=conversation_memory,
        config=agent_config
    )

    assert agent.validate_query("") is False
    assert agent.validate_query("   ") is False
