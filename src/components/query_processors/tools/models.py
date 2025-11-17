"""
Data models for tool execution system.

This module defines all data structures used across the tool execution framework,
providing type-safe representations for tool parameters, results, and execution traces.

Architecture:
- Immutable dataclasses for thread safety
- Rich type hints for IDE support and validation
- Clear separation between tool definition and execution
- Support for both Anthropic and OpenAI tool formats
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime


class ToolParameterType(Enum):
    """
    Tool parameter types compatible with both OpenAI and Anthropic schemas.

    Maps to JSON Schema types for maximum compatibility.
    """

    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


@dataclass(frozen=True)
class ToolParameter:
    """
    Definition of a single tool parameter.

    Used to generate schemas for both OpenAI and Anthropic tools.

    Attributes:
        name: Parameter name (must be valid Python identifier)
        type: Parameter type from ToolParameterType
        description: Clear description for LLM understanding
        required: Whether parameter is mandatory
        enum: Optional list of allowed values
        default: Optional default value if not required
        items: Optional schema for array items (if type is ARRAY)
        properties: Optional properties for objects (if type is OBJECT)

    Example:
        >>> param = ToolParameter(
        ...     name="query",
        ...     type=ToolParameterType.STRING,
        ...     description="Search query text",
        ...     required=True
        ... )
    """

    name: str
    type: ToolParameterType
    description: str
    required: bool = True
    enum: Optional[List[str]] = None
    default: Optional[Any] = None
    items: Optional[Dict[str, Any]] = None  # For array types
    properties: Optional[Dict[str, Any]] = None  # For object types

    def to_json_schema(self) -> Dict[str, Any]:
        """
        Convert to JSON Schema format.

        Returns:
            JSON Schema representation of this parameter
        """
        schema: Dict[str, Any] = {
            "type": self.type.value,
            "description": self.description
        }

        if self.enum is not None:
            schema["enum"] = self.enum

        if self.default is not None:
            schema["default"] = self.default

        if self.type == ToolParameterType.ARRAY and self.items is not None:
            schema["items"] = self.items

        if self.type == ToolParameterType.OBJECT and self.properties is not None:
            schema["properties"] = self.properties

        return schema


@dataclass
class ToolResult:
    """
    Result from tool execution.

    Tools MUST return this instead of raising exceptions.
    This ensures graceful error handling and allows LLMs to retry or adapt.

    Attributes:
        success: Whether execution succeeded
        content: Result content (string, dict, list, etc.)
        error: Error message if execution failed
        execution_time: Time taken in seconds
        metadata: Additional execution metadata

    Invariants:
        - If success=False, error must be set
        - If success=True, content should be set
        - execution_time >= 0

    Example:
        >>> # Success case
        >>> result = ToolResult(
        ...     success=True,
        ...     content="The answer is 42",
        ...     execution_time=0.123
        ... )
        >>>
        >>> # Error case
        >>> result = ToolResult(
        ...     success=False,
        ...     error="Invalid input: division by zero",
        ...     execution_time=0.001
        ... )
    """

    success: bool
    content: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate invariants."""
        if not self.success and self.error is None:
            raise ValueError("Failed ToolResult must have error message")
        if self.execution_time < 0:
            raise ValueError("execution_time must be non-negative")


@dataclass
class ToolCall:
    """
    Single tool call request from LLM.

    Represents the LLM's decision to use a tool with specific arguments.

    Attributes:
        id: Unique identifier for this tool call
        tool_name: Name of tool to execute
        arguments: Tool arguments as key-value pairs
        timestamp: When the LLM made this call

    Example:
        >>> call = ToolCall(
        ...     id="call_abc123",
        ...     tool_name="calculator",
        ...     arguments={"expression": "25 * 47"},
        ...     timestamp=datetime.now()
        ... )
    """

    id: str
    tool_name: str
    arguments: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ToolExecution:
    """
    Record of a single tool execution.

    Links a tool call to its result, with timing information.

    Attributes:
        call: Original tool call from LLM
        result: Execution result
        started_at: When execution started
        completed_at: When execution completed
        execution_time: Total execution time in seconds

    Example:
        >>> execution = ToolExecution(
        ...     call=tool_call,
        ...     result=tool_result,
        ...     started_at=start_time,
        ...     completed_at=end_time,
        ...     execution_time=0.123
        ... )
    """

    call: ToolCall
    result: ToolResult
    started_at: datetime
    completed_at: datetime
    execution_time: float

    def __post_init__(self) -> None:
        """Validate timing consistency."""
        if self.completed_at < self.started_at:
            raise ValueError("completed_at must be after started_at")
        if self.execution_time < 0:
            raise ValueError("execution_time must be non-negative")


@dataclass
class ToolConversation:
    """
    Complete multi-turn tool conversation.

    Tracks the entire conversation where an LLM uses tools iteratively
    to solve a problem.

    Attributes:
        prompt: Original user prompt
        tool_executions: List of tool executions in order
        final_answer: Final answer after all tool use
        total_iterations: Number of tool use iterations
        total_tokens: Total tokens used (input + output)
        total_cost_usd: Total API cost in USD
        total_time: Total wall clock time in seconds
        metadata: Additional conversation metadata

    Example:
        >>> conversation = ToolConversation(
        ...     prompt="What is 25 * 47?",
        ...     tool_executions=[calculator_execution],
        ...     final_answer="25 multiplied by 47 equals 1,175",
        ...     total_iterations=1,
        ...     total_tokens=150,
        ...     total_cost_usd=0.0002,
        ...     total_time=2.5
        ... )
    """

    prompt: str
    tool_executions: List[ToolExecution]
    final_answer: str
    total_iterations: int
    total_tokens: int
    total_cost_usd: float
    total_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate conversation consistency."""
        if self.total_iterations < 0:
            raise ValueError("total_iterations must be non-negative")
        if self.total_tokens < 0:
            raise ValueError("total_tokens must be non-negative")
        if self.total_cost_usd < 0:
            raise ValueError("total_cost_usd must be non-negative")
        if self.total_time < 0:
            raise ValueError("total_time must be non-negative")

    def get_successful_executions(self) -> List[ToolExecution]:
        """Get only successful tool executions."""
        return [exe for exe in self.tool_executions if exe.result.success]

    def get_failed_executions(self) -> List[ToolExecution]:
        """Get only failed tool executions."""
        return [exe for exe in self.tool_executions if not exe.result.success]

    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for this conversation.

        Returns:
            Dictionary with success rate, average time, etc.
        """
        total = len(self.tool_executions)
        successful = len(self.get_successful_executions())
        failed = len(self.get_failed_executions())

        return {
            "total_executions": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0.0,
            "average_execution_time": (
                sum(exe.execution_time for exe in self.tool_executions) / total
                if total > 0 else 0.0
            ),
            "total_iterations": self.total_iterations,
            "total_tokens": self.total_tokens,
            "total_cost_usd": self.total_cost_usd,
            "total_time": self.total_time
        }
