"""
Tool execution framework for RAG system.

This package provides a complete tool execution system for LLMs, including:
- Tool interfaces and base classes
- Tool registry and execution coordination
- Data models for tool parameters and results
- Concrete tool implementations

Architecture:
- Provider-agnostic design (works with OpenAI, Anthropic, etc.)
- Type-safe interfaces with full type hints
- Error resilience (tools never crash, always return results)
- Thread-safe tool registry
- Comprehensive observability

Usage:
    >>> from src.components.query_processors.tools import (
    ...     BaseTool,
    ...     ToolRegistry,
    ...     ToolResult,
    ...     CalculatorTool
    ... )
    >>>
    >>> # Create and register tools
    >>> registry = ToolRegistry()
    >>> calculator = CalculatorTool()
    >>> registry.register(calculator)
    >>>
    >>> # Execute tool
    >>> result = registry.execute_tool("calculator", expression="25 * 47")
    >>> print(result.content)  # "1175"
"""

from .base_tool import BaseTool

# Concrete tool implementations
from .implementations import (
    CalculatorTool,
    CodeAnalyzerTool,
    DocumentSearchTool,
)
from .models import (
    ToolCall,
    ToolConversation,
    ToolExecution,
    ToolParameter,
    ToolParameterType,
    ToolResult,
)
from .tool_registry import ToolRegistry

__all__ = [
    # Data models
    "ToolParameterType",
    "ToolParameter",
    "ToolResult",
    "ToolCall",
    "ToolExecution",
    "ToolConversation",
    # Base classes
    "BaseTool",
    # Registry
    "ToolRegistry",
    # Concrete tools
    "CalculatorTool",
    "CodeAnalyzerTool",
    "DocumentSearchTool",
]

__version__ = "1.0.0"
