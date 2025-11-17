"""
Data models for Phase 2 agent system.

This module defines all data structures used by the agent framework,
including agent results, reasoning steps, query analysis, execution plans, and more.

Architecture:
- All models use @dataclass for immutability and validation
- Enums for type-safe constants
- __post_init__ validation for invariants
- 100% type hints for type safety

Usage:
    >>> from src.components.query_processors.agents.models import AgentResult, ReasoningStep
    >>>
    >>> result = AgentResult(
    ...     success=True,
    ...     answer="The answer is 42",
    ...     reasoning_steps=[...],
    ...     tool_calls=[],
    ...     execution_time=1.5,
    ...     total_cost=0.01
    ... )
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# Import Phase 1 models
from src.components.query_processors.tools.models import ToolCall, ToolResult


# =============================================================================
# Enumerations
# =============================================================================

class StepType(Enum):
    """Type of reasoning step in agent process."""

    THOUGHT = "thought"  # Agent internal reasoning
    ACTION = "action"  # Tool execution request
    OBSERVATION = "observation"  # Tool execution result
    FINAL_ANSWER = "final_answer"  # Agent's conclusion


class QueryType(Enum):
    """Query classification types."""

    SIMPLE = "simple"  # Direct RAG retrieval
    RESEARCH = "research"  # Multi-document synthesis
    ANALYTICAL = "analytical"  # Requires computation/analysis
    CODE = "code"  # Code-related query
    MULTI_STEP = "multi_step"  # Requires planning and multiple steps


class ExecutionStrategy(Enum):
    """Execution strategy for query processing."""

    DIRECT = "direct"  # Single RAG query (no agent)
    SEQUENTIAL = "sequential"  # Sequential tool use
    PARALLEL = "parallel"  # Parallel tool execution
    HYBRID = "hybrid"  # Mix of sequential and parallel


# =============================================================================
# Agent Results
# =============================================================================

@dataclass
class ReasoningStep:
    """Single reasoning step in agent process."""

    step_number: int
    step_type: StepType
    content: str
    tool_call: Optional[ToolCall] = None
    tool_result: Optional[ToolResult] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate reasoning step."""
        if self.step_number < 0:
            raise ValueError("step_number must be non-negative")

        # ACTION steps should have tool_call
        if self.step_type == StepType.ACTION and self.tool_call is None:
            raise ValueError("ACTION step must have tool_call")

        # OBSERVATION steps should have tool_result
        if self.step_type == StepType.OBSERVATION and self.tool_result is None:
            raise ValueError("OBSERVATION step must have tool_result")


@dataclass
class AgentResult:
    """Result from agent processing."""

    success: bool
    answer: str
    reasoning_steps: List[ReasoningStep]
    tool_calls: List[ToolCall]
    execution_time: float  # seconds
    total_cost: float  # USD
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate agent result invariants."""
        if not self.success and self.error is None:
            raise ValueError("Failed AgentResult must have error message")

        if self.success and self.error is not None:
            raise ValueError("Successful AgentResult should not have error message")

        if self.execution_time < 0:
            raise ValueError("execution_time must be non-negative")

        if self.total_cost < 0:
            raise ValueError("total_cost must be non-negative")


# =============================================================================
# Agent Configuration
# =============================================================================

@dataclass
class AgentConfig:
    """Agent configuration parameters."""

    llm_provider: str  # "openai" or "anthropic"
    llm_model: str  # e.g., "gpt-4-turbo", "claude-3-5-sonnet-20241022"
    temperature: float = 0.7
    max_tokens: int = 2048
    max_iterations: int = 10
    max_execution_time: int = 300  # seconds
    early_stopping: str = "force"  # or "generate"
    verbose: bool = False

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.llm_provider not in ["openai", "anthropic"]:
            raise ValueError("llm_provider must be 'openai' or 'anthropic'")

        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError("temperature must be between 0.0 and 2.0")

        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")

        if self.max_iterations <= 0:
            raise ValueError("max_iterations must be positive")

        if self.max_execution_time <= 0:
            raise ValueError("max_execution_time must be positive")


# =============================================================================
# Query Analysis
# =============================================================================

@dataclass
class QueryAnalysis:
    """Analysis of query characteristics."""

    query_type: QueryType
    complexity: float  # 0.0-1.0 (0=simple, 1=very complex)
    intent: str  # "information_retrieval", "analysis", "code_debug", etc.
    entities: List[str]  # Extracted entities
    requires_tools: List[str]  # Predicted tool requirements
    estimated_steps: int  # Estimated reasoning steps needed
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate query analysis."""
        if not (0.0 <= self.complexity <= 1.0):
            raise ValueError("complexity must be between 0.0 and 1.0")

        if self.estimated_steps < 1:
            raise ValueError("estimated_steps must be at least 1")


# =============================================================================
# Query Planning
# =============================================================================

@dataclass
class SubTask:
    """Sub-task in query decomposition."""

    id: str
    description: str
    query: str
    required_tools: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # IDs of prerequisite tasks
    can_run_parallel: bool = False
    priority: int = 0  # Lower = higher priority
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate sub-task."""
        if not self.id:
            raise ValueError("SubTask id cannot be empty")

        if not self.query:
            raise ValueError("SubTask query cannot be empty")

        if self.priority < 0:
            raise ValueError("priority must be non-negative")


@dataclass
class ExecutionPlan:
    """Execution plan for query processing."""

    plan_id: str
    query: str
    strategy: ExecutionStrategy
    tasks: List[SubTask] = field(default_factory=list)
    execution_graph: Dict[str, List[str]] = field(default_factory=dict)  # Dependency graph
    estimated_time: float = 0.0  # seconds
    estimated_cost: float = 0.0  # USD
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate execution plan."""
        if not self.plan_id:
            raise ValueError("plan_id cannot be empty")

        if not self.query:
            raise ValueError("query cannot be empty")

        if self.estimated_time < 0:
            raise ValueError("estimated_time must be non-negative")

        if self.estimated_cost < 0:
            raise ValueError("estimated_cost must be non-negative")


@dataclass
class ExecutionResult:
    """Result from plan execution."""

    success: bool
    final_answer: str
    task_results: Dict[str, Any] = field(default_factory=dict)  # Results for each sub-task
    reasoning_trace: List[ReasoningStep] = field(default_factory=list)
    execution_time: float = 0.0  # seconds
    total_cost: float = 0.0  # USD
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate execution result."""
        if not self.success and self.error is None:
            raise ValueError("Failed ExecutionResult must have error message")

        if self.execution_time < 0:
            raise ValueError("execution_time must be non-negative")

        if self.total_cost < 0:
            raise ValueError("total_cost must be non-negative")


# =============================================================================
# Memory
# =============================================================================

@dataclass
class Message:
    """Conversation message."""

    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate message."""
        if self.role not in ["user", "assistant", "system"]:
            raise ValueError("role must be 'user', 'assistant', or 'system'")

        if not self.content:
            raise ValueError("content cannot be empty")


# =============================================================================
# Processor Configuration
# =============================================================================

@dataclass
class ProcessorConfig:
    """Intelligent processor configuration."""

    use_agent_by_default: bool = True
    complexity_threshold: float = 0.7  # Use agent if complexity > threshold
    max_agent_cost: float = 0.10  # Max cost per query (USD)
    enable_planning: bool = True
    enable_parallel_execution: bool = True

    def __post_init__(self) -> None:
        """Validate processor configuration."""
        if not (0.0 <= self.complexity_threshold <= 1.0):
            raise ValueError("complexity_threshold must be between 0.0 and 1.0")

        if self.max_agent_cost < 0:
            raise ValueError("max_agent_cost must be non-negative")
