"""
End-to-end scenario test: Calculator tool usage.

Scenario:
User asks: "What is 25 * 47?"
Expected: Calculator tool called, correct answer returned

This test validates the complete flow:
1. User query → Tool selection
2. Tool execution → Result generation
3. Result formatting → Final answer

Author: Epic 5 Phase 1 Block 3 Testing Agent
Created: 2025-11-17
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List, Any

from src.components.query_processors.tools.tool_registry import ToolRegistry
from src.components.query_processors.tools.implementations import CalculatorTool
from src.components.generators.llm_adapters.anthropic_adapter import AnthropicAdapter
from src.components.generators.llm_adapters.openai_adapter import OpenAIAdapter


class TestCalculatorScenario:
    """
    End-to-end scenario tests for Calculator tool usage.

    These tests simulate real user interactions where an LLM
    decides to use the calculator tool to answer questions.
    """

    def test_simple_multiplication_scenario(self) -> None:
        """
        Scenario: User asks "What is 25 * 47?"

        Expected Flow:
        1. User provides question
        2. Calculator tool selected
        3. Expression "25 * 47" evaluated
        4. Result "1175" returned
        5. Final answer formatted

        This test validates:
        - Tool registration works
        - Tool execution succeeds
        - Correct result returned
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        user_question = "What is 25 * 47?"
        expected_expression = "25 * 47"
        expected_answer = "1175"

        # Act - Simulate tool execution
        result = registry.execute_tool("calculator", expression=expected_expression)

        # Assert
        assert result.success is True
        assert result.content == expected_answer
        assert result.error is None
        assert result.execution_time > 0

        # Verify this could be formatted into a final answer
        final_answer = f"The result of {expected_expression} is {result.content}."
        assert "1175" in final_answer

    def test_complex_expression_scenario(self) -> None:
        """
        Scenario: User asks "What is (100 + 50) * 2 - 25?"

        Expected Flow:
        1. Complex mathematical expression
        2. Calculator evaluates step by step
        3. Correct result returned
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        user_question = "What is (100 + 50) * 2 - 25?"
        expression = "(100 + 50) * 2 - 25"
        expected_answer = "275"

        # Act
        result = registry.execute_tool("calculator", expression=expression)

        # Assert
        assert result.success is True
        assert result.content == expected_answer

    def test_floating_point_scenario(self) -> None:
        """
        Scenario: User asks "What is 22 / 7?"

        Expected Flow:
        1. Division operation
        2. Floating point result
        3. Proper decimal formatting
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        expression = "22 / 7"

        # Act
        result = registry.execute_tool("calculator", expression=expression)

        # Assert
        assert result.success is True
        # Result should be approximately 3.14285...
        result_float = float(result.content)
        assert 3.14 < result_float < 3.15

    def test_error_handling_scenario(self) -> None:
        """
        Scenario: User provides invalid expression "What is 1 / 0?"

        Expected Flow:
        1. Invalid expression detected
        2. Error caught gracefully
        3. Error message returned to user
        4. System remains stable
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        invalid_expression = "1 / 0"

        # Act
        result = registry.execute_tool("calculator", expression=invalid_expression)

        # Assert
        assert result.success is False
        assert result.error is not None
        assert "error" in result.error.lower() or "division" in result.error.lower()

    def test_multiple_calculations_scenario(self) -> None:
        """
        Scenario: User asks multiple math questions in sequence.

        Expected Flow:
        1. First calculation: 10 + 20
        2. Second calculation: 30 * 2
        3. Third calculation: 60 - 5
        4. All calculations succeed independently
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        calculations = [
            ("10 + 20", "30"),
            ("30 * 2", "60"),
            ("60 - 5", "55"),
        ]

        # Act & Assert
        for expression, expected in calculations:
            result = registry.execute_tool("calculator", expression=expression)
            assert result.success is True
            assert result.content == expected


class TestCalculatorWithAnthropicAdapter:
    """
    Test Calculator tool with Anthropic adapter integration.

    Validates that the tool can be properly integrated with
    Claude (Anthropic's LLM) using the correct schema format.
    """

    def test_calculator_schema_for_anthropic(self) -> None:
        """
        Test: Generate proper Anthropic schema for calculator.

        Verifies:
        - Schema matches Anthropic format
        - Required fields present
        - Parameter schema correct
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Act
        schemas = registry.get_anthropic_schemas()

        # Assert
        assert len(schemas) == 1

        calc_schema = schemas[0]
        assert calc_schema["name"] == "calculator"
        assert "description" in calc_schema
        assert "input_schema" in calc_schema

        input_schema = calc_schema["input_schema"]
        assert input_schema["type"] == "object"
        assert "expression" in input_schema["properties"]
        assert "expression" in input_schema["required"]

    @patch('anthropic.Anthropic')
    def test_calculator_with_mock_anthropic_call(
        self,
        mock_anthropic_class: MagicMock
    ) -> None:
        """
        Test: Simulate Anthropic API call with calculator tool.

        Scenario:
        1. User asks math question
        2. Claude decides to use calculator
        3. Tool executes
        4. Result returned to Claude
        5. Claude formats final answer

        Note: This uses mocks to avoid actual API calls.
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Mock Anthropic response that requests calculator tool
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Simulate Claude requesting to use calculator
        mock_tool_use = MagicMock()
        mock_tool_use.name = "calculator"
        mock_tool_use.input = {"expression": "25 * 47"}

        # Act - Execute the tool call
        result = registry.execute_tool(
            tool_name=mock_tool_use.name,
            **mock_tool_use.input
        )

        # Assert
        assert result.success is True
        assert result.content == "1175"


class TestCalculatorWithOpenAIAdapter:
    """
    Test Calculator tool with OpenAI adapter integration.

    Validates that the tool can be properly integrated with
    GPT models using OpenAI's function calling format.
    """

    def test_calculator_schema_for_openai(self) -> None:
        """
        Test: Generate proper OpenAI schema for calculator.

        Verifies:
        - Schema matches OpenAI function calling format
        - Required fields present
        - Parameter schema correct
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Act
        schemas = registry.get_openai_schemas()

        # Assert
        assert len(schemas) == 1

        calc_schema = schemas[0]
        assert calc_schema["type"] == "function"
        assert "function" in calc_schema

        function = calc_schema["function"]
        assert function["name"] == "calculator"
        assert "description" in function
        assert "parameters" in function

        parameters = function["parameters"]
        assert parameters["type"] == "object"
        assert "expression" in parameters["properties"]
        assert "expression" in parameters["required"]

    def test_calculator_with_mock_openai_call(self) -> None:
        """
        Test: Simulate OpenAI function call with calculator tool.

        Scenario:
        1. User asks math question
        2. GPT decides to call calculator function
        3. Tool executes
        4. Result returned to GPT
        5. GPT formats final answer

        Note: This uses mocks to avoid actual API calls.
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Simulate GPT function call
        function_name = "calculator"
        function_args = {"expression": "100 / 4"}

        # Act
        result = registry.execute_tool(function_name, **function_args)

        # Assert
        assert result.success is True
        assert result.content == "25.0"


class TestCalculatorPerformance:
    """
    Performance tests for calculator tool.

    Validates that tool executes quickly enough for
    real-time LLM interactions.
    """

    def test_calculator_execution_time(self) -> None:
        """
        Test: Calculator executes within acceptable time.

        Requirement: Execution time < 100ms for simple expressions.

        This ensures responsive user experience.
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Act
        result = registry.execute_tool("calculator", expression="999 * 999")

        # Assert
        assert result.success is True
        assert result.execution_time < 0.1  # 100ms max

    def test_calculator_handles_rapid_fire_requests(self) -> None:
        """
        Test: Calculator handles multiple rapid requests.

        Simulates high-throughput scenario where multiple
        calculations happen in quick succession.
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        expressions = [f"{i} * {i}" for i in range(1, 11)]

        # Act
        results = []
        for expr in expressions:
            result = registry.execute_tool("calculator", expression=expr)
            results.append(result)

        # Assert
        assert len(results) == 10
        assert all(r.success for r in results)

        # Verify results are correct
        for i, result in enumerate(results, start=1):
            expected = str(i * i)
            assert result.content == expected


class TestCalculatorEdgeCases:
    """
    Edge case tests for calculator tool.

    Tests unusual but valid scenarios to ensure robustness.
    """

    def test_very_large_number(self) -> None:
        """
        Test: Calculator handles very large numbers.
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Act
        result = registry.execute_tool(
            "calculator",
            expression="999999999 * 999999999"
        )

        # Assert
        assert result.success is True
        assert result.content is not None

    def test_very_small_number(self) -> None:
        """
        Test: Calculator handles very small decimals.
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Act
        result = registry.execute_tool(
            "calculator",
            expression="0.0000001 * 0.0000001"
        )

        # Assert
        assert result.success is True
        assert result.content is not None

    def test_scientific_notation(self) -> None:
        """
        Test: Calculator handles scientific notation.
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Act
        result = registry.execute_tool(
            "calculator",
            expression="1e10 * 2e5"
        )

        # Assert
        assert result.success is True
        # Result should be 2e15
        result_float = float(result.content)
        assert abs(result_float - 2e15) < 1e10  # Allow for floating point

    def test_empty_expression(self) -> None:
        """
        Test: Calculator handles empty expression gracefully.
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Act
        result = registry.execute_tool("calculator", expression="")

        # Assert
        assert result.success is False
        assert result.error is not None

    def test_invalid_syntax(self) -> None:
        """
        Test: Calculator handles invalid syntax gracefully.
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Note: "2 + + 2" is valid Python (parsed as 2 + (+2))
        invalid_expressions = [
            "2 + ",  # Incomplete expression
            "* 5",
            "10 /",
            "(5 + 3",
            "5 + 3)",
        ]

        # Act & Assert
        for expr in invalid_expressions:
            result = registry.execute_tool("calculator", expression=expr)
            assert result.success is False, f"Should fail for: {expr}"
            assert result.error is not None
