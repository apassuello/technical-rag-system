"""
Abstract base class for all tools.

Defines the contract that all tools must implement to work with the tool
execution framework and both OpenAI and Anthropic LLM providers.

Architecture:
- ABC for strict interface enforcement
- Tools NEVER raise exceptions (return errors in ToolResult)
- Schema generation for both OpenAI and Anthropic
- Type-safe parameter validation
- Comprehensive error handling

Usage:
    >>> class MyTool(BaseTool):
    ...     @property
    ...     def name(self) -> str:
    ...         return "my_tool"
    ...
    ...     @property
    ...     def description(self) -> str:
    ...         return "Does something useful"
    ...
    ...     def get_parameters(self) -> List[ToolParameter]:
    ...         return [
    ...             ToolParameter(
    ...                 name="input",
    ...                 type=ToolParameterType.STRING,
    ...                 description="Input text"
    ...             )
    ...         ]
    ...
    ...     def execute(self, input: str) -> ToolResult:
    ...         try:
    ...             result = self._do_work(input)
    ...             return ToolResult(success=True, content=result)
    ...         except Exception as e:
    ...             return ToolResult(success=False, error=str(e))
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import logging
import time

from .models import (
    ToolParameter,
    ToolParameterType,
    ToolResult,
)

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """
    Abstract base class for all tools.

    Responsibilities:
    - Define tool schema (name, description, parameters)
    - Execute tool logic safely (never raise exceptions)
    - Validate parameters before execution
    - Generate schemas for different LLM providers
    - Provide observability (logging, timing)

    Invariants:
    - name must be unique across all tools
    - execute() NEVER raises exceptions
    - description must be clear enough for LLM understanding
    - All public methods have type hints

    Example Implementation:
        See module docstring for complete example.
    """

    def __init__(self):
        """
        Initialize base tool.

        Subclasses should call super().__init__() if they override.
        """
        self._execution_count = 0
        self._total_execution_time = 0.0
        self._error_count = 0
        self._logger = logging.getLogger(f"{__name__}.{self.name}")

    # ===================================================================
    # Abstract Methods (MUST be implemented by subclasses)
    # ===================================================================

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Tool name (unique identifier).

        Must be:
        - Unique across all tools
        - Valid Python identifier (no spaces, special chars)
        - Descriptive and concise
        - Snake_case by convention

        Returns:
            Tool name string

        Example:
            return "calculator"
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Tool description for LLM.

        Must be:
        - Clear and concise
        - Explain what the tool does
        - Explain when to use it
        - Written for LLM understanding

        Returns:
            Tool description string

        Example:
            return "Evaluate mathematical expressions. Use for calculations."
        """
        pass

    @abstractmethod
    def get_parameters(self) -> List[ToolParameter]:
        """
        Get tool parameter definitions.

        Defines the schema for tool inputs.

        Returns:
            List of ToolParameter objects

        Example:
            return [
                ToolParameter(
                    name="expression",
                    type=ToolParameterType.STRING,
                    description="Mathematical expression to evaluate",
                    required=True
                )
            ]
        """
        pass

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute tool with given parameters.

        CRITICAL: This method MUST NEVER raise exceptions.
        All errors should be caught and returned in ToolResult.

        Args:
            **kwargs: Tool parameters (validated before this is called)

        Returns:
            ToolResult with success status and content or error

        Invariants:
            - Never raises exceptions
            - Always returns ToolResult
            - Logs all executions
            - Updates execution metrics

        Example:
            def execute(self, expression: str) -> ToolResult:
                try:
                    result = self._calculate(expression)
                    return ToolResult(success=True, content=result)
                except Exception as e:
                    logger.error(f"Calculation failed: {e}")
                    return ToolResult(success=False, error=str(e))
        """
        pass

    # ===================================================================
    # Concrete Methods (can be overridden if needed)
    # ===================================================================

    def validate_parameters(self, **kwargs) -> Tuple[bool, Optional[str]]:
        """
        Validate parameters before execution.

        Default implementation checks:
        - All required parameters present
        - Parameter types match (basic check)

        Can be overridden for custom validation.

        Args:
            **kwargs: Parameters to validate

        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if valid
            - (False, "error description") if invalid

        Example:
            >>> tool = MyTool()
            >>> valid, error = tool.validate_parameters(input="test")
            >>> assert valid is True
            >>> assert error is None
        """
        params = self.get_parameters()
        required_params = [p.name for p in params if p.required]

        # Check required parameters
        for param_name in required_params:
            if param_name not in kwargs:
                return False, f"Missing required parameter: {param_name}"

        # Check for unknown parameters
        known_params = {p.name for p in params}
        for param_name in kwargs:
            if param_name not in known_params:
                return False, f"Unknown parameter: {param_name}"

        return True, None

    def execute_safe(self, **kwargs) -> ToolResult:
        """
        Execute tool with automatic validation and error handling.

        This is the recommended way to execute tools externally.
        Validates parameters, executes tool, tracks metrics.

        Args:
            **kwargs: Tool parameters

        Returns:
            ToolResult with success status and content or error

        Example:
            >>> tool = CalculatorTool()
            >>> result = tool.execute_safe(expression="2 + 2")
            >>> print(result.content)  # "4"
        """
        start_time = time.time()

        try:
            # Validate parameters
            valid, error = self.validate_parameters(**kwargs)
            if not valid:
                self._logger.warning(f"Parameter validation failed: {error}")
                self._error_count += 1
                return ToolResult(
                    success=False,
                    error=f"Parameter validation failed: {error}",
                    execution_time=time.time() - start_time
                )

            # Execute tool
            self._logger.debug(f"Executing {self.name} with params: {kwargs}")
            result = self.execute(**kwargs)

            # Update metrics
            execution_time = time.time() - start_time
            self._execution_count += 1
            self._total_execution_time += execution_time

            if not result.success:
                self._error_count += 1
                self._logger.warning(
                    f"{self.name} execution failed: {result.error}"
                )
            else:
                self._logger.debug(
                    f"{self.name} executed successfully in {execution_time:.3f}s"
                )

            # Update execution time if not set
            if result.execution_time == 0.0:
                result.execution_time = execution_time

            return result

        except Exception as e:
            # This should never happen (execute should catch all exceptions)
            # But we handle it anyway for safety
            execution_time = time.time() - start_time
            self._logger.error(
                f"Unexpected exception in {self.name}: {e}",
                exc_info=True
            )
            self._error_count += 1
            return ToolResult(
                success=False,
                error=f"Unexpected error: {str(e)}",
                execution_time=execution_time
            )

    def to_anthropic_schema(self) -> Dict[str, Any]:
        """
        Convert tool to Anthropic tool schema format.

        Returns:
            Dictionary in Anthropic tool schema format

        Example:
            {
                "name": "calculator",
                "description": "Evaluate mathematical expressions",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Math expression"
                        }
                    },
                    "required": ["expression"]
                }
            }
        """
        params = self.get_parameters()

        properties = {}
        required = []

        for param in params:
            properties[param.name] = param.to_json_schema()
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }

    def to_openai_schema(self) -> Dict[str, Any]:
        """
        Convert tool to OpenAI function schema format.

        Returns:
            Dictionary in OpenAI function schema format

        Example:
            {
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "Evaluate mathematical expressions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "Math expression"
                            }
                        },
                        "required": ["expression"]
                    }
                }
            }
        """
        params = self.get_parameters()

        properties = {}
        required = []

        for param in params:
            properties[param.name] = param.to_json_schema()
            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get tool execution statistics.

        Returns:
            Dictionary with execution metrics

        Example:
            {
                "name": "calculator",
                "executions": 42,
                "errors": 2,
                "success_rate": 0.952,
                "total_time": 12.5,
                "avg_time": 0.298
            }
        """
        return {
            "name": self.name,
            "executions": self._execution_count,
            "errors": self._error_count,
            "success_rate": (
                (self._execution_count - self._error_count) / self._execution_count
                if self._execution_count > 0
                else 0.0
            ),
            "total_time": self._total_execution_time,
            "avg_time": (
                self._total_execution_time / self._execution_count
                if self._execution_count > 0
                else 0.0
            )
        }

    def reset_stats(self) -> None:
        """Reset execution statistics."""
        self._execution_count = 0
        self._total_execution_time = 0.0
        self._error_count = 0

    def __repr__(self) -> str:
        """String representation of tool."""
        return f"{self.__class__.__name__}(name='{self.name}')"
