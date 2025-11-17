"""
Centralized tool registry for managing and executing tools.

Provides thread-safe registration, lookup, and execution of tools
with schema generation for both OpenAI and Anthropic providers.

Architecture:
- Thread-safe with RLock for all operations
- Centralized tool management
- Schema generation for multiple providers
- Safe tool execution with error handling
- Comprehensive observability

Usage:
    >>> from src.components.query_processors.tools import (
    ...     ToolRegistry,
    ...     CalculatorTool
    ... )
    >>>
    >>> # Create registry and register tools
    >>> registry = ToolRegistry()
    >>> calculator = CalculatorTool()
    >>> registry.register(calculator)
    >>>
    >>> # Get schemas for LLM providers
    >>> anthropic_schemas = registry.get_anthropic_schemas()
    >>> openai_schemas = registry.get_openai_schemas()
    >>>
    >>> # Execute tools
    >>> result = registry.execute_tool("calculator", expression="2 + 2")
    >>> print(result.content)  # "4"
"""

from typing import Dict, List, Optional
import logging
import threading

from .base_tool import BaseTool
from .models import ToolResult


logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Central registry for all tools.

    Responsibilities:
    - Register/unregister tools
    - Provide thread-safe tool lookup
    - Generate schemas for different LLM providers
    - Execute tools with error handling
    - Track tool usage statistics

    Invariants:
    - Tool names must be unique
    - All operations are thread-safe
    - Failed lookups return None, not exceptions
    - Tool execution failures return ToolResult with error

    Example:
        >>> registry = ToolRegistry()
        >>> registry.register(CalculatorTool())
        >>> registry.register(DocumentSearchTool())
        >>>
        >>> # Get all tool schemas
        >>> schemas = registry.get_anthropic_schemas()
        >>>
        >>> # Execute a tool
        >>> result = registry.execute_tool("calculator", expression="5 * 5")
        >>> print(result.content)  # "25"
    """

    def __init__(self):
        """
        Initialize tool registry.

        Creates empty registry with thread-safe lock.
        """
        self._tools: Dict[str, BaseTool] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        self._logger.info("Initialized ToolRegistry")

    def register(self, tool: BaseTool) -> None:
        """
        Register a tool.

        Args:
            tool: Tool instance to register

        Raises:
            ValueError: If tool with same name already registered
            TypeError: If tool is not a BaseTool instance

        Example:
            >>> registry = ToolRegistry()
            >>> calculator = CalculatorTool()
            >>> registry.register(calculator)
            >>> # calculator is now available via registry
        """
        if not isinstance(tool, BaseTool):
            raise TypeError(
                f"Tool must be instance of BaseTool, got {type(tool)}"
            )

        tool_name = tool.name

        with self._lock:
            if tool_name in self._tools:
                raise ValueError(
                    f"Tool '{tool_name}' already registered. "
                    "Use unregister() first if you want to replace it."
                )

            self._tools[tool_name] = tool
            self._logger.info(
                f"Registered tool: {tool_name} ({tool.__class__.__name__})"
            )

    def unregister(self, tool_name: str) -> bool:
        """
        Unregister a tool by name.

        Args:
            tool_name: Name of tool to unregister

        Returns:
            True if tool was unregistered, False if tool not found

        Example:
            >>> registry.unregister("calculator")
            True
            >>> registry.unregister("nonexistent")
            False
        """
        with self._lock:
            if tool_name in self._tools:
                del self._tools[tool_name]
                self._logger.info(f"Unregistered tool: {tool_name}")
                return True
            else:
                self._logger.warning(
                    f"Attempted to unregister unknown tool: {tool_name}"
                )
                return False

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found

        Example:
            >>> calculator = registry.get_tool("calculator")
            >>> if calculator:
            ...     result = calculator.execute_safe(expression="2 + 2")
        """
        with self._lock:
            return self._tools.get(name)

    def has_tool(self, name: str) -> bool:
        """
        Check if tool is registered.

        Args:
            name: Tool name

        Returns:
            True if tool is registered, False otherwise

        Example:
            >>> if registry.has_tool("calculator"):
            ...     # use calculator
        """
        with self._lock:
            return name in self._tools

    def get_all_tools(self) -> List[BaseTool]:
        """
        Get all registered tools.

        Returns:
            List of all tool instances

        Example:
            >>> tools = registry.get_all_tools()
            >>> for tool in tools:
            ...     print(f"{tool.name}: {tool.description}")
        """
        with self._lock:
            return list(self._tools.values())

    def get_tool_names(self) -> List[str]:
        """
        Get names of all registered tools.

        Returns:
            List of tool names

        Example:
            >>> names = registry.get_tool_names()
            >>> print(names)  # ['calculator', 'search_documents', ...]
        """
        with self._lock:
            return list(self._tools.keys())

    def get_anthropic_schemas(self) -> List[Dict]:
        """
        Get all tools as Anthropic tool schemas.

        Returns:
            List of Anthropic tool schema dictionaries

        Example:
            >>> schemas = registry.get_anthropic_schemas()
            >>> response = anthropic_client.messages.create(
            ...     model="claude-3-5-sonnet-20241022",
            ...     tools=schemas,
            ...     messages=[...]
            ... )
        """
        with self._lock:
            schemas = []
            for tool in self._tools.values():
                try:
                    schema = tool.to_anthropic_schema()
                    schemas.append(schema)
                except Exception as e:
                    self._logger.error(
                        f"Failed to generate Anthropic schema for {tool.name}: {e}",
                        exc_info=True
                    )
            return schemas

    def get_openai_schemas(self) -> List[Dict]:
        """
        Get all tools as OpenAI function schemas.

        Returns:
            List of OpenAI function schema dictionaries

        Example:
            >>> schemas = registry.get_openai_schemas()
            >>> response = openai_client.chat.completions.create(
            ...     model="gpt-4-turbo",
            ...     tools=schemas,
            ...     messages=[...]
            ... )
        """
        with self._lock:
            schemas = []
            for tool in self._tools.values():
                try:
                    schema = tool.to_openai_schema()
                    schemas.append(schema)
                except Exception as e:
                    self._logger.error(
                        f"Failed to generate OpenAI schema for {tool.name}: {e}",
                        exc_info=True
                    )
            return schemas

    def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Execute a tool by name.

        This is a convenience method that:
        1. Looks up the tool
        2. Validates it exists
        3. Executes it safely
        4. Returns result or error

        Args:
            tool_name: Name of tool to execute
            **kwargs: Tool arguments

        Returns:
            ToolResult with success status and content or error

        Note:
            This method NEVER raises exceptions. All errors are returned
            in the ToolResult.

        Example:
            >>> result = registry.execute_tool(
            ...     "calculator",
            ...     expression="25 * 47"
            ... )
            >>> if result.success:
            ...     print(f"Answer: {result.content}")
            ... else:
            ...     print(f"Error: {result.error}")
        """
        # Get tool (thread-safe)
        tool = self.get_tool(tool_name)

        if tool is None:
            error_msg = f"Tool '{tool_name}' not found in registry"
            self._logger.error(error_msg)
            return ToolResult(
                success=False,
                error=error_msg,
                execution_time=0.0
            )

        # Execute tool safely
        try:
            result = tool.execute_safe(**kwargs)
            return result
        except Exception as e:
            # This should never happen (execute_safe catches all exceptions)
            # But we handle it anyway for absolute safety
            error_msg = f"Unexpected error executing {tool_name}: {str(e)}"
            self._logger.error(error_msg, exc_info=True)
            return ToolResult(
                success=False,
                error=error_msg,
                execution_time=0.0
            )

    def get_registry_stats(self) -> Dict:
        """
        Get statistics for the entire registry.

        Returns:
            Dictionary with registry statistics including per-tool stats

        Example:
            >>> stats = registry.get_registry_stats()
            >>> print(f"Total tools: {stats['total_tools']}")
            >>> print(f"Total executions: {stats['total_executions']}")
        """
        with self._lock:
            tool_stats = {}
            total_executions = 0
            total_errors = 0

            for tool_name, tool in self._tools.items():
                stats = tool.get_stats()
                tool_stats[tool_name] = stats
                total_executions += stats['executions']
                total_errors += stats['errors']

            return {
                'total_tools': len(self._tools),
                'tool_names': list(self._tools.keys()),
                'total_executions': total_executions,
                'total_errors': total_errors,
                'overall_success_rate': (
                    (total_executions - total_errors) / total_executions
                    if total_executions > 0
                    else 0.0
                ),
                'per_tool_stats': tool_stats
            }

    def reset_all_stats(self) -> None:
        """
        Reset statistics for all tools.

        Example:
            >>> registry.reset_all_stats()
            >>> # All tool execution counters reset to 0
        """
        with self._lock:
            for tool in self._tools.values():
                tool.reset_stats()
            self._logger.info("Reset statistics for all tools")

    def clear(self) -> None:
        """
        Clear all tools from registry.

        Use with caution - this removes all registered tools.

        Example:
            >>> registry.clear()
            >>> print(len(registry.get_all_tools()))  # 0
        """
        with self._lock:
            self._tools.clear()
            self._logger.info("Cleared all tools from registry")

    def __len__(self) -> int:
        """
        Get number of registered tools.

        Example:
            >>> print(len(registry))  # 3
        """
        with self._lock:
            return len(self._tools)

    def __contains__(self, tool_name: str) -> bool:
        """
        Check if tool is in registry.

        Example:
            >>> if "calculator" in registry:
            ...     # use calculator
        """
        return self.has_tool(tool_name)

    def __repr__(self) -> str:
        """String representation of registry."""
        with self._lock:
            return (
                f"ToolRegistry(tools={len(self._tools)}, "
                f"names={list(self._tools.keys())})"
            )
