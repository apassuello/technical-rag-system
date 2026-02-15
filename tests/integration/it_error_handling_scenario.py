"""
End-to-end scenario test: Error handling across all tools.

Scenarios:
- Tool execution failures
- Invalid parameters
- Missing tools
- System errors

This test validates that the tool system handles errors gracefully
and never raises unhandled exceptions.

Author: Epic 5 Phase 1 Block 3 Testing Agent
Created: 2025-11-17
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, List, Any

pytestmark = [pytest.mark.integration]

from src.components.query_processors.tools.tool_registry import ToolRegistry
from src.components.query_processors.tools.implementations import (
    CalculatorTool,
    DocumentSearchTool,
    CodeAnalyzerTool,
)
from src.components.query_processors.tools.models import ToolResult, ToolParameter
from src.components.query_processors.tools.base_tool import BaseTool


class TestToolExecutionFailures:
    """
    Test scenarios where tool execution fails for various reasons.

    All failures should be caught and returned as ToolResult with
    success=False and descriptive error messages.
    """

    def test_calculator_division_by_zero(self) -> None:
        """
        Scenario: User tries to divide by zero.

        Expected Flow:
        1. Calculator tool receives "10 / 0"
        2. Execution fails with ZeroDivisionError
        3. Error caught and returned in ToolResult
        4. System remains stable
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Act
        result = registry.execute_tool("calculator", expression="10 / 0")

        # Assert
        assert result.success is False
        assert result.error is not None
        assert "error" in result.error.lower() or "division" in result.error.lower()
        # Execution time should still be recorded
        assert result.execution_time >= 0

    def test_calculator_invalid_expression(self) -> None:
        """
        Scenario: User provides invalid mathematical expression.

        Expected: SyntaxError caught, descriptive error returned.

        Note: "2 + + 2" is valid (unary plus: 2 + (+2) = 4)
              "5 / / 2" is valid (floor division: 5 // 2 = 2)
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        invalid_expressions = [
            "* 5",  # Syntax error: binary operator without left operand
            "(((1 + 2)",  # Syntax error: unmatched parentheses
            "x + y",  # Undefined variables
        ]

        # Act & Assert
        for expr in invalid_expressions:
            result = registry.execute_tool("calculator", expression=expr)
            assert result.success is False, f"Should fail for: {expr}"
            assert result.error is not None
            assert isinstance(result.error, str)

    def test_code_analyzer_syntax_error(self) -> None:
        """
        Scenario: User provides code with syntax errors.

        Expected: Analysis succeeds and reports syntax error in content.

        Note: CodeAnalyzerTool treats syntax errors as successful analysis
              that identifies syntax issues (success=True with error details).
              "return 42" is valid Python in module scope (Python 3.x).
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        invalid_codes = [
            "def broken(",  # Incomplete function - syntax error
            "if True",  # Missing colon - syntax error
            "class Test",  # Missing colon - syntax error
            "def func():\nreturn x",  # Incorrect indentation - syntax error
        ]

        # Act & Assert
        for code in invalid_codes:
            result = registry.execute_tool("analyze_code", code=code)
            # Syntax error analysis is a successful result that reports the error
            assert result.success is True, f"Analysis should succeed for: {code[:20]}"
            assert result.content is not None
            assert "SYNTAX ERROR" in result.content, f"Should report syntax error for: {code[:20]}"
            assert result.metadata.get("syntax_valid") is False

    def test_document_search_retriever_failure(self) -> None:
        """
        Scenario: Retriever raises exception during search.

        Expected: Exception caught, error returned in ToolResult.

        Note: DocumentSearchTool uses num_results parameter, not top_k.
              Error message format is "Search failed: <exception message>".
        """
        # Arrange
        mock_retriever = Mock()
        mock_retriever.retrieve.side_effect = RuntimeError("Index corrupted")

        registry = ToolRegistry()
        search_tool = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search_tool)

        # Act
        result = registry.execute_tool(
            "search_documents",
            query="test query",
            num_results=5
        )

        # Assert
        assert result.success is False
        assert result.error is not None
        assert "failed" in result.error.lower() or "corrupted" in result.error.lower()

    def test_document_search_retriever_timeout(self) -> None:
        """
        Scenario: Retriever times out during search.

        Expected: Timeout handled gracefully.
        """
        # Arrange
        mock_retriever = Mock()
        mock_retriever.search.side_effect = TimeoutError("Search timed out")

        registry = ToolRegistry()
        search_tool = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search_tool)

        # Act
        result = registry.execute_tool(
            "search_documents",
            query="test query",
            top_k=10
        )

        # Assert
        assert result.success is False
        assert result.error is not None


class TestInvalidParameters:
    """
    Test scenarios with invalid or missing parameters.
    """

    def test_calculator_missing_expression(self) -> None:
        """
        Scenario: Calculator called without required 'expression' parameter.

        Expected: Missing parameter error returned.
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Act - Missing required parameter
        result = registry.execute_tool("calculator")

        # Assert
        assert result.success is False
        assert result.error is not None

    def test_calculator_none_expression(self) -> None:
        """
        Scenario: Calculator called with expression=None.

        Expected: Invalid parameter error.
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Act
        result = registry.execute_tool("calculator", expression=None)

        # Assert
        assert result.success is False
        assert result.error is not None

    def test_document_search_missing_query(self) -> None:
        """
        Scenario: Document search called without 'query' parameter.

        Expected: Missing parameter error.
        """
        # Arrange
        mock_retriever = Mock()
        registry = ToolRegistry()
        search_tool = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search_tool)

        # Act
        result = registry.execute_tool("search_documents", top_k=5)

        # Assert
        assert result.success is False
        assert result.error is not None

    def test_document_search_empty_query(self) -> None:
        """
        Scenario: Document search with empty query string.

        Expected: Validation error.
        """
        # Arrange
        mock_retriever = Mock()
        registry = ToolRegistry()
        search_tool = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search_tool)

        # Act
        result = registry.execute_tool(
            "search_documents",
            query="",
            top_k=5
        )

        # Assert
        assert result.success is False
        assert result.error is not None

    def test_document_search_invalid_top_k(self) -> None:
        """
        Scenario: Document search with invalid top_k values.

        Expected: Validation error for negative or zero values.
        """
        # Arrange
        mock_retriever = Mock()
        registry = ToolRegistry()
        search_tool = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search_tool)

        invalid_top_k_values = [-1, 0, -100]

        # Act & Assert
        for top_k in invalid_top_k_values:
            result = registry.execute_tool(
                "search_documents",
                query="test",
                top_k=top_k
            )
            assert result.success is False, f"Should fail for top_k={top_k}"
            assert result.error is not None

    def test_code_analyzer_missing_code(self) -> None:
        """
        Scenario: Code analyzer called without 'code' parameter.

        Expected: Missing parameter error.
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        # Act
        result = registry.execute_tool("analyze_code")

        # Assert
        assert result.success is False
        assert result.error is not None

    def test_code_analyzer_none_code(self) -> None:
        """
        Scenario: Code analyzer with code=None.

        Expected: Invalid parameter error.
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        # Act
        result = registry.execute_tool("analyze_code", code=None)

        # Assert
        assert result.success is False
        assert result.error is not None

    def test_code_analyzer_empty_code(self) -> None:
        """
        Scenario: Code analyzer with empty string.

        Expected: Validation error.
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        # Act
        result = registry.execute_tool("analyze_code", code="")

        # Assert
        assert result.success is False
        assert result.error is not None


class TestMissingTools:
    """
    Test scenarios where tools are not registered or not found.
    """

    def test_execute_nonexistent_tool(self) -> None:
        """
        Scenario: User tries to execute tool that doesn't exist.

        Expected: Tool not found error returned (not exception).
        """
        # Arrange
        registry = ToolRegistry()

        # Act
        result = registry.execute_tool(
            "nonexistent_tool",
            param="value"
        )

        # Assert
        assert result.success is False
        assert result.error is not None
        assert "not found" in result.error.lower()

    def test_execute_unregistered_tool(self) -> None:
        """
        Scenario: Tool was registered but then unregistered.

        Expected: Tool not found error.
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)
        registry.unregister("calculator")

        # Act
        result = registry.execute_tool("calculator", expression="1 + 1")

        # Assert
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_execute_with_typo_in_tool_name(self) -> None:
        """
        Scenario: User provides tool name with typo.

        Expected: Tool not found error with helpful message.
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Act - Typo in tool name
        result = registry.execute_tool(
            "calcuator",  # Typo: should be "calculator"
            expression="2 + 2"
        )

        # Assert
        assert result.success is False
        assert "not found" in result.error.lower()


class TestSystemErrors:
    """
    Test scenarios with system-level errors.
    """

    def test_tool_registry_handles_memory_error(self) -> None:
        """
        Scenario: Tool encounters MemoryError during execution.

        Expected: Error caught and returned gracefully.
        """
        # Arrange
        class MemoryErrorTool(BaseTool):
            @property
            def name(self) -> str:
                return "memory_error_tool"

            @property
            def description(self) -> str:
                return "Tool that raises MemoryError"

            def get_parameters(self) -> List[ToolParameter]:
                return []

            def execute(self, **kwargs) -> ToolResult:
                raise MemoryError("Out of memory")

        registry = ToolRegistry()
        error_tool = MemoryErrorTool()
        registry.register(error_tool)

        # Act
        result = registry.execute_tool("memory_error_tool")

        # Assert
        assert result.success is False
        assert result.error is not None

    def test_tool_handles_keyboard_interrupt_gracefully(self) -> None:
        """
        Scenario: Tool execution interrupted (e.g., user cancellation).

        Note: KeyboardInterrupt should typically propagate, but
        tool should handle it gracefully if caught.
        """
        # Arrange
        class InterruptibleTool(BaseTool):
            @property
            def name(self) -> str:
                return "interruptible_tool"

            @property
            def description(self) -> str:
                return "Tool that can be interrupted"

            def get_parameters(self) -> List[ToolParameter]:
                return []

            def execute(self, **kwargs) -> ToolResult:
                # Simulate long operation that gets interrupted
                raise KeyboardInterrupt("User interrupted")

        registry = ToolRegistry()
        tool = InterruptibleTool()
        registry.register(tool)

        # Act - This might propagate KeyboardInterrupt
        # (which is acceptable behavior)
        try:
            result = registry.execute_tool("interruptible_tool")
            # If we get here, it was caught
            assert result.success is False
        except KeyboardInterrupt:
            # If KeyboardInterrupt propagates, that's also acceptable
            pass

    def test_tool_handles_recursion_error(self) -> None:
        """
        Scenario: Tool encounters RecursionError.

        Expected: Error caught and returned.
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Create expression that could cause recursion issues
        # (though calculator should handle this safely)
        deeply_nested = "(" * 1000 + "1" + ")" * 1000

        # Act
        result = registry.execute_tool("calculator", expression=deeply_nested)

        # Assert - Should either succeed or fail gracefully
        assert result is not None
        assert isinstance(result, ToolResult)


class TestErrorRecovery:
    """
    Test that system recovers from errors and continues operating.
    """

    def test_error_doesnt_break_registry(self) -> None:
        """
        Scenario: Error in one tool execution doesn't break registry.

        Expected: Subsequent operations continue normally.
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Act - First execution fails
        error_result = registry.execute_tool("calculator", expression="1 / 0")

        # Second execution succeeds
        success_result = registry.execute_tool("calculator", expression="2 + 2")

        # Assert
        assert error_result.success is False
        assert success_result.success is True
        assert success_result.content == "4"

    def test_multiple_errors_in_sequence(self) -> None:
        """
        Scenario: Multiple errors in sequence don't accumulate or cause issues.

        Expected: Each error handled independently.

        Note: CodeAnalyzerTool returns success=True for syntax errors
              (it successfully analyzes and reports the syntax error).
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        analyzer = CodeAnalyzerTool()
        registry.register(calculator)
        registry.register(analyzer)

        # Act - Multiple failing operations
        results = [
            registry.execute_tool("calculator", expression="1 / 0"),  # Fails
            registry.execute_tool("analyze_code", code="def broken("),  # Succeeds with syntax error report
            registry.execute_tool("nonexistent_tool"),  # Fails
            registry.execute_tool("calculator"),  # Fails - missing parameter
        ]

        # Assert
        assert len(results) == 4
        # First result: calculator division by zero (fails)
        assert results[0].success is False
        assert results[0].error is not None
        # Second result: code analyzer with syntax error (succeeds with error report)
        assert results[1].success is True
        assert "SYNTAX ERROR" in results[1].content
        # Third result: nonexistent tool (fails)
        assert results[2].success is False
        assert results[2].error is not None
        # Fourth result: missing parameter (fails)
        assert results[3].success is False
        assert results[3].error is not None

        # System should still work after errors
        good_result = registry.execute_tool("calculator", expression="5 + 5")
        assert good_result.success is True

    def test_error_in_one_tool_doesnt_affect_others(self) -> None:
        """
        Scenario: Error in one tool doesn't affect other tools.

        Expected: Tools remain independent.
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        analyzer = CodeAnalyzerTool()

        registry.register(calculator)
        registry.register(analyzer)

        # Act - Calculator fails
        calc_error = registry.execute_tool("calculator", expression="1 / 0")

        # Analyzer still works
        analyzer_result = registry.execute_tool(
            "analyze_code",
            code="def test(): pass"
        )

        # Assert
        assert calc_error.success is False
        assert analyzer_result.success is True


class TestErrorMessages:
    """
    Test that error messages are clear and helpful.
    """

    def test_error_messages_are_strings(self) -> None:
        """
        Test: All error messages are strings (not exception objects).
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Act
        result = registry.execute_tool("calculator", expression="1 / 0")

        # Assert
        assert result.success is False
        assert isinstance(result.error, str)
        assert len(result.error) > 0

    def test_error_messages_are_descriptive(self) -> None:
        """
        Test: Error messages provide useful information.
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Act
        result = registry.execute_tool("nonexistent_tool")

        # Assert
        assert result.success is False
        assert "not found" in result.error.lower()
        assert "nonexistent_tool" in result.error

    def test_parameter_error_messages_mention_parameter(self) -> None:
        """
        Test: Parameter errors mention which parameter is problematic.
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Act - Missing expression parameter
        result = registry.execute_tool("calculator")

        # Assert
        assert result.success is False
        # Error should mention the parameter issue
        assert "expression" in result.error.lower() or "parameter" in result.error.lower()


class TestConcurrentErrors:
    """
    Test error handling in concurrent scenarios.

    Note: These are basic tests. Full concurrency testing would
    require threading/multiprocessing.
    """

    def test_rapid_fire_errors_handled(self) -> None:
        """
        Test: Multiple rapid errors don't cause issues.
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Act - Rapid fire errors
        results = []
        for _ in range(10):
            result = registry.execute_tool("calculator", expression="1 / 0")
            results.append(result)

        # Assert
        assert len(results) == 10
        assert all(not r.success for r in results)
        assert all(r.error is not None for r in results)

    def test_mixed_success_and_errors(self) -> None:
        """
        Test: Mixed successful and failing operations.
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        expressions = [
            ("1 + 1", True),
            ("1 / 0", False),
            ("2 * 2", True),
            ("invalid", False),
            ("3 + 3", True),
        ]

        # Act
        results = []
        for expr, _ in expressions:
            result = registry.execute_tool("calculator", expression=expr)
            results.append(result)

        # Assert
        for i, (expr, should_succeed) in enumerate(expressions):
            assert results[i].success == should_succeed, f"Failed for: {expr}"


class TestErrorLogging:
    """
    Test that errors are properly logged (metadata).
    """

    def test_failed_execution_records_execution_time(self) -> None:
        """
        Test: Failed executions still record execution time.
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Act
        result = registry.execute_tool("calculator", expression="1 / 0")

        # Assert
        assert result.success is False
        assert result.execution_time >= 0
        # Even errors should have some execution time

    def test_error_result_has_all_required_fields(self) -> None:
        """
        Test: Error ToolResult has all required fields populated.
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Act
        result = registry.execute_tool("calculator", expression="invalid")

        # Assert
        assert hasattr(result, 'success')
        assert hasattr(result, 'content')
        assert hasattr(result, 'error')
        assert hasattr(result, 'execution_time')
        assert hasattr(result, 'metadata')

        assert result.success is False
        assert result.error is not None
        assert result.execution_time >= 0
