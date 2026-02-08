#!/usr/bin/env python3
"""
Standalone test for Phase 2 Block 1 implementation.
Tests models, base classes, and memory without full package import chain.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# Import Phase 2 components directly from module files (bypass __init__.py)
import importlib.util

def import_module_from_file(module_name, file_path):
    """Import a module directly from a file."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Import tools.models first (needed by agents.models)
tools_models_path = project_root / "src" / "components" / "query_processors" / "tools" / "models.py"
tools_models = import_module_from_file("tools_models", str(tools_models_path))
sys.modules["src.components.query_processors.tools.models"] = tools_models

# Create fake package structure for relative imports
# This allows the modules to find each other via relative imports
class FakePackage:
    def __init__(self, name):
        self.__name__ = name
        self.__package__ = name
        self.__path__ = []

agents_package = FakePackage("components.query_processors.agents")
sys.modules["components.query_processors.agents"] = agents_package

# Import models module
models_path = project_root / "src" / "components" / "query_processors" / "agents" / "models.py"
models = import_module_from_file("components.query_processors.agents.models", str(models_path))
models.__package__ = "components.query_processors.agents"

# Import from models
StepType = models.StepType
QueryType = models.QueryType
ExecutionStrategy = models.ExecutionStrategy
ReasoningStep = models.ReasoningStep
AgentResult = models.AgentResult
AgentConfig = models.AgentConfig
QueryAnalysis = models.QueryAnalysis
SubTask = models.SubTask
ExecutionPlan = models.ExecutionPlan
ExecutionResult = models.ExecutionResult
Message = models.Message
ProcessorConfig = models.ProcessorConfig

# Import base_memory first (needed by base_agent)
base_memory_path = project_root / "src" / "components" / "query_processors" / "agents" / "base_memory.py"
base_memory = import_module_from_file("components.query_processors.agents.base_memory", str(base_memory_path))
base_memory.__package__ = "components.query_processors.agents"
BaseMemory = base_memory.BaseMemory
MemoryError = base_memory.MemoryError
MemoryCapacityError = base_memory.MemoryCapacityError
MemoryPersistenceError = base_memory.MemoryPersistenceError

# Import base_agent
base_agent_path = project_root / "src" / "components" / "query_processors" / "agents" / "base_agent.py"
base_agent = import_module_from_file("components.query_processors.agents.base_agent", str(base_agent_path))
base_agent.__package__ = "components.query_processors.agents"
BaseAgent = base_agent.BaseAgent
AgentError = base_agent.AgentError
AgentTimeoutError = base_agent.AgentTimeoutError
AgentIterationLimitError = base_agent.AgentIterationLimitError
AgentToolError = base_agent.AgentToolError
AgentPlanningError = base_agent.AgentPlanningError

# Create memory package
memory_package = FakePackage("components.query_processors.agents.memory")
sys.modules["components.query_processors.agents.memory"] = memory_package

# Import conversation memory
conv_memory_path = project_root / "src" / "components" / "query_processors" / "agents" / "memory" / "conversation_memory.py"
conv_memory = import_module_from_file("components.query_processors.agents.memory.conversation_memory", str(conv_memory_path))
conv_memory.__package__ = "components.query_processors.agents.memory"
ConversationMemory = conv_memory.ConversationMemory

# Import working memory
work_memory_path = project_root / "src" / "components" / "query_processors" / "agents" / "memory" / "working_memory.py"
work_memory = import_module_from_file("components.query_processors.agents.memory.working_memory", str(work_memory_path))
work_memory.__package__ = "components.query_processors.agents.memory"
WorkingMemory = work_memory.WorkingMemory


def test_enums():
    """Test Phase 2 enums."""
    print("Testing enums...")
    assert StepType.THOUGHT.value == "thought"
    assert StepType.ACTION.value == "action"
    assert StepType.OBSERVATION.value == "observation"
    assert StepType.FINAL_ANSWER.value == "final_answer"

    assert QueryType.SIMPLE.value == "simple"
    assert QueryType.RESEARCH.value == "research"
    assert QueryType.ANALYTICAL.value == "analytical"
    assert QueryType.CODE.value == "code"
    assert QueryType.MULTI_STEP.value == "multi_step"

    assert ExecutionStrategy.DIRECT.value == "direct"
    assert ExecutionStrategy.SEQUENTIAL.value == "sequential"
    assert ExecutionStrategy.PARALLEL.value == "parallel"
    assert ExecutionStrategy.HYBRID.value == "hybrid"
    print("✓ Enum tests passed")


def test_reasoning_step():
    """Test ReasoningStep model."""
    print("\nTesting ReasoningStep...")

    # Valid step
    step = ReasoningStep(
        step_number=1,
        step_type=StepType.THOUGHT,
        content="Analyzing query..."
    )
    assert step.step_number == 1
    assert step.step_type == StepType.THOUGHT
    assert step.content == "Analyzing query..."

    # ACTION step requires tool_call
    try:
        step = ReasoningStep(
            step_number=2,
            step_type=StepType.ACTION,
            content="Calling tool..."
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "ACTION step must have tool_call" in str(e)

    print("✓ ReasoningStep tests passed")


def test_agent_result():
    """Test AgentResult model."""
    print("\nTesting AgentResult...")

    # Successful result
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

    # Failed result without error should raise
    try:
        result = AgentResult(
            success=False,
            answer="",
            reasoning_steps=[],
            tool_calls=[],
            execution_time=1.5,
            total_cost=0.0
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Failed AgentResult must have error message" in str(e)

    # Failed result with error
    result = AgentResult(
        success=False,
        answer="",
        reasoning_steps=[],
        tool_calls=[],
        execution_time=1.5,
        total_cost=0.0,
        error="Something went wrong"
    )
    assert result.success is False
    assert result.error == "Something went wrong"

    print("✓ AgentResult tests passed")


def test_agent_config():
    """Test AgentConfig model."""
    print("\nTesting AgentConfig...")

    # Valid config
    config = AgentConfig(
        llm_provider="openai",
        llm_model="gpt-4-turbo",
        temperature=0.7,
        max_tokens=2048,
        max_iterations=10,
        max_execution_time=300
    )
    assert config.llm_provider == "openai"
    assert config.llm_model == "gpt-4-turbo"

    # Invalid provider
    try:
        config = AgentConfig(
            llm_provider="invalid",
            llm_model="model"
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "llm_provider must be" in str(e)

    print("✓ AgentConfig tests passed")


def test_query_analysis():
    """Test QueryAnalysis model."""
    print("\nTesting QueryAnalysis...")

    analysis = QueryAnalysis(
        query_type=QueryType.RESEARCH,
        complexity=0.8,
        intent="information_retrieval",
        entities=["Python", "FastAPI"],
        requires_tools=["search", "rag_search"],
        estimated_steps=5
    )
    assert analysis.query_type == QueryType.RESEARCH
    assert analysis.complexity == 0.8
    assert len(analysis.entities) == 2

    # Invalid complexity
    try:
        analysis = QueryAnalysis(
            query_type=QueryType.SIMPLE,
            complexity=1.5,  # > 1.0
            intent="test",
            entities=[],
            requires_tools=[],
            estimated_steps=1
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "complexity must be between 0.0 and 1.0" in str(e)

    print("✓ QueryAnalysis tests passed")


def test_conversation_memory():
    """Test ConversationMemory."""
    print("\nTesting ConversationMemory...")

    # Create memory
    memory = ConversationMemory(max_messages=3)

    # Add messages
    memory.add_message("user", "Hello")
    memory.add_message("assistant", "Hi! How can I help?")
    memory.add_message("user", "What is Python?")

    messages = memory.get_messages()
    assert len(messages) == 3
    assert messages[0].role == "user"
    assert messages[0].content == "Hello"

    # Test capacity limit
    memory.add_message("assistant", "Python is a programming language")
    messages = memory.get_messages()
    assert len(messages) == 3  # Should be capped at 3
    assert messages[0].role == "assistant"  # Oldest "user: Hello" removed
    assert messages[0].content == "Hi! How can I help?"

    # Test get last N
    last_two = memory.get_messages(last_n=2)
    assert len(last_two) == 2

    # Test clear
    memory.clear()
    assert len(memory.get_messages()) == 0

    print("✓ ConversationMemory tests passed")


def test_working_memory():
    """Test WorkingMemory."""
    print("\nTesting WorkingMemory...")

    # Create memory
    memory = WorkingMemory()

    # Set context
    memory.set_context("task_id", "task-123")
    memory.set_context("step", 1)
    memory.set_context("data", {"key": "value"})

    # Get context
    assert memory.get_context("task_id") == "task-123"
    assert memory.get_context("step") == 1
    assert memory.get_context("nonexistent", "default") == "default"

    # Has context
    assert memory.has_context("task_id")
    assert not memory.has_context("nonexistent")

    # Get all context
    all_ctx = memory.get_all_context()
    assert len(all_ctx) == 3
    assert all_ctx["task_id"] == "task-123"

    # Remove context
    memory.remove_context("data")
    assert not memory.has_context("data")

    # Update
    memory.update({"new_key": "new_value", "another": 42})
    assert memory.get_context("new_key") == "new_value"
    assert memory.get_context("another") == 42

    # Operators
    assert len(memory) == 4  # task_id, step, new_key, another
    assert "task_id" in memory

    # Clear
    memory.clear()
    assert len(memory) == 0

    print("✓ WorkingMemory tests passed")


def test_message():
    """Test Message model."""
    print("\nTesting Message...")

    # Valid message
    msg = Message(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"

    # Invalid role
    try:
        msg = Message(role="invalid", content="test")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "role must be" in str(e)

    # Empty content
    try:
        msg = Message(role="user", content="")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "content cannot be empty" in str(e)

    print("✓ Message tests passed")


def test_processor_config():
    """Test ProcessorConfig model."""
    print("\nTesting ProcessorConfig...")

    config = ProcessorConfig(
        use_agent_by_default=True,
        complexity_threshold=0.7,
        max_agent_cost=0.10,
        enable_planning=True,
        enable_parallel_execution=True
    )
    assert config.use_agent_by_default is True
    assert config.complexity_threshold == 0.7

    # Invalid complexity threshold
    try:
        config = ProcessorConfig(
            complexity_threshold=1.5  # > 1.0
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "complexity_threshold must be between 0.0 and 1.0" in str(e)

    print("✓ ProcessorConfig tests passed")


def run_all_tests():
    """Run all Phase 2 Block 1 tests."""
    print("="*60)
    print("Phase 2 Block 1 - Standalone Test Suite")
    print("="*60)

    try:
        test_enums()
        test_reasoning_step()
        test_agent_result()
        test_agent_config()
        test_query_analysis()
        test_conversation_memory()
        test_working_memory()
        test_message()
        test_processor_config()

        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED (9/9)")
        print("="*60)
        return 0

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
