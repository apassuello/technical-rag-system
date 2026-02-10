"""
Unit tests for CalculatorTool.

Tests cover:
- Basic arithmetic operations
- Mathematical functions
- Constants (pi, e)
- Error handling
- Input validation
- Edge cases
- Tool interface compliance

Test Strategy:
- Comprehensive coverage of all supported operations
- Validation of error handling (tools never raise exceptions)
- Verification of ToolResult structure
- Testing of tool schema generation
"""

import pytest
import math
from typing import List

from src.components.query_processors.tools.implementations import CalculatorTool
from src.components.query_processors.tools import ToolResult, ToolParameter


class TestCalculatorToolBasics:
    """Test basic calculator tool functionality."""

    def test_tool_initialization(self):
        """Test tool can be initialized."""
        tool = CalculatorTool()
        assert tool is not None
        assert tool.name == "calculator"

    def test_tool_name(self):
        """Test tool has correct name."""
        tool = CalculatorTool()
        assert tool.name == "calculator"
        assert isinstance(tool.name, str)

    def test_tool_description(self):
        """Test tool has meaningful description."""
        tool = CalculatorTool()
        assert tool.description is not None
        assert len(tool.description) > 0
        assert "mathematical" in tool.description.lower() or "math" in tool.description.lower()

    def test_get_parameters(self):
        """Test tool returns correct parameter definitions."""
        tool = CalculatorTool()
        params = tool.get_parameters()

        assert isinstance(params, list)
        assert len(params) == 1  # Only 'expression' parameter

        param = params[0]
        assert param.name == "expression"
        assert param.required is True

    def test_parameter_validation_success(self):
        """Test parameter validation accepts valid inputs."""
        tool = CalculatorTool()
        valid, error = tool.validate_parameters(expression="2 + 2")

        assert valid is True
        assert error is None

    def test_parameter_validation_missing(self):
        """Test parameter validation rejects missing required params."""
        tool = CalculatorTool()
        valid, error = tool.validate_parameters()

        assert valid is False
        assert error is not None
        assert "expression" in error.lower()


class TestCalculatorArithmetic:
    """Test basic arithmetic operations."""

    @pytest.fixture
    def calculator(self) -> CalculatorTool:
        """Create calculator tool instance."""
        return CalculatorTool()

    def test_addition(self, calculator):
        """Test addition operation."""
        result = calculator.execute(expression="2 + 3")

        assert result.success is True
        assert result.content == "5"
        assert result.error is None

    def test_subtraction(self, calculator):
        """Test subtraction operation."""
        result = calculator.execute(expression="10 - 3")

        assert result.success is True
        assert result.content == "7"

    def test_multiplication(self, calculator):
        """Test multiplication operation."""
        result = calculator.execute(expression="25 * 47")

        assert result.success is True
        assert result.content == "1175"

    def test_division(self, calculator):
        """Test division operation."""
        result = calculator.execute(expression="100 / 4")

        assert result.success is True
        assert result.content == "25"

    def test_floor_division(self, calculator):
        """Test floor division operation."""
        result = calculator.execute(expression="10 // 3")

        assert result.success is True
        assert result.content == "3"

    def test_modulo(self, calculator):
        """Test modulo operation."""
        result = calculator.execute(expression="10 % 3")

        assert result.success is True
        assert result.content == "1"

    def test_exponentiation(self, calculator):
        """Test exponentiation operation."""
        result = calculator.execute(expression="2 ** 8")

        assert result.success is True
        assert result.content == "256"

    def test_complex_expression(self, calculator):
        """Test complex arithmetic expression."""
        result = calculator.execute(expression="(25 * 47) + (100 / 4)")

        assert result.success is True
        assert result.content == "1200"

    def test_operator_precedence(self, calculator):
        """Test operator precedence is respected."""
        result = calculator.execute(expression="2 + 3 * 4")

        assert result.success is True
        assert result.content == "14"  # Not 20

    def test_parentheses_precedence(self, calculator):
        """Test parentheses override precedence."""
        result = calculator.execute(expression="(2 + 3) * 4")

        assert result.success is True
        assert result.content == "20"

    def test_negative_numbers(self, calculator):
        """Test negative numbers."""
        result = calculator.execute(expression="-5 + 3")

        assert result.success is True
        assert result.content == "-2"

    def test_floating_point(self, calculator):
        """Test floating point arithmetic."""
        result = calculator.execute(expression="10 / 3")

        assert result.success is True
        # Should be approximately 3.333...
        assert float(result.content) == pytest.approx(3.333333, rel=1e-5)


class TestCalculatorFunctions:
    """Test mathematical functions."""

    @pytest.fixture
    def calculator(self) -> CalculatorTool:
        """Create calculator tool instance."""
        return CalculatorTool()

    def test_sqrt(self, calculator):
        """Test square root function."""
        result = calculator.execute(expression="sqrt(16)")

        assert result.success is True
        assert result.content == "4"

    def test_sqrt_non_integer(self, calculator):
        """Test square root with non-integer result."""
        result = calculator.execute(expression="sqrt(2)")

        assert result.success is True
        assert float(result.content) == pytest.approx(math.sqrt(2))

    def test_sin(self, calculator):
        """Test sine function."""
        result = calculator.execute(expression="sin(0)")

        assert result.success is True
        assert float(result.content) == pytest.approx(0.0, abs=1e-10)

    def test_cos(self, calculator):
        """Test cosine function."""
        result = calculator.execute(expression="cos(0)")

        assert result.success is True
        assert float(result.content) == pytest.approx(1.0)

    def test_log(self, calculator):
        """Test natural logarithm."""
        result = calculator.execute(expression="log(e)")

        assert result.success is True
        assert float(result.content) == pytest.approx(1.0)

    def test_exp(self, calculator):
        """Test exponential function."""
        result = calculator.execute(expression="exp(0)")

        assert result.success is True
        assert float(result.content) == pytest.approx(1.0)

    def test_abs(self, calculator):
        """Test absolute value function."""
        result = calculator.execute(expression="abs(-42)")

        assert result.success is True
        assert result.content == "42"

    def test_ceil(self, calculator):
        """Test ceiling function."""
        result = calculator.execute(expression="ceil(3.2)")

        assert result.success is True
        assert result.content == "4"

    def test_floor(self, calculator):
        """Test floor function."""
        result = calculator.execute(expression="floor(3.8)")

        assert result.success is True
        assert result.content == "3"

    def test_round(self, calculator):
        """Test round function."""
        result = calculator.execute(expression="round(3.7)")

        assert result.success is True
        assert result.content == "4"

    def test_function_with_arithmetic(self, calculator):
        """Test combining functions with arithmetic."""
        result = calculator.execute(expression="sqrt(16) + 2 ** 3")

        assert result.success is True
        assert result.content == "12"


class TestCalculatorConstants:
    """Test mathematical constants."""

    @pytest.fixture
    def calculator(self) -> CalculatorTool:
        """Create calculator tool instance."""
        return CalculatorTool()

    def test_pi_constant(self, calculator):
        """Test pi constant."""
        result = calculator.execute(expression="pi")

        assert result.success is True
        assert float(result.content) == pytest.approx(math.pi)

    def test_e_constant(self, calculator):
        """Test e constant."""
        result = calculator.execute(expression="e")

        assert result.success is True
        assert float(result.content) == pytest.approx(math.e)

    def test_pi_in_expression(self, calculator):
        """Test using pi in calculations."""
        result = calculator.execute(expression="2 * pi")

        assert result.success is True
        assert float(result.content) == pytest.approx(2 * math.pi)


class TestCalculatorErrorHandling:
    """Test error handling (tools never raise exceptions)."""

    @pytest.fixture
    def calculator(self) -> CalculatorTool:
        """Create calculator tool instance."""
        return CalculatorTool()

    def test_division_by_zero(self, calculator):
        """Test division by zero returns error (not exception)."""
        result = calculator.execute(expression="1 / 0")

        assert result.success is False
        assert result.error is not None
        assert "zero" in result.error.lower()

    def test_empty_expression(self, calculator):
        """Test empty expression returns error."""
        result = calculator.execute(expression="")

        assert result.success is False
        assert result.error is not None

    def test_whitespace_only_expression(self, calculator):
        """Test whitespace-only expression returns error."""
        result = calculator.execute(expression="   ")

        assert result.success is False
        assert result.error is not None

    def test_invalid_syntax(self, calculator):
        """Test invalid syntax returns error."""
        # Use an actually invalid expression (incomplete operator)
        result = calculator.execute(expression="2 + ")

        assert result.success is False
        assert result.error is not None
        assert "syntax" in result.error.lower()

    def test_invalid_function(self, calculator):
        """Test invalid function name returns error."""
        result = calculator.execute(expression="invalid_func(5)")

        assert result.success is False
        assert result.error is not None

    def test_sqrt_negative(self, calculator):
        """Test sqrt of negative returns error."""
        result = calculator.execute(expression="sqrt(-1)")

        assert result.success is False
        assert result.error is not None

    def test_log_negative(self, calculator):
        """Test log of negative returns error."""
        result = calculator.execute(expression="log(-1)")

        assert result.success is False
        assert result.error is not None

    def test_unsupported_operation(self, calculator):
        """Test unsupported operations return error."""
        # Bitwise operations are not supported
        result = calculator.execute(expression="5 & 3")

        assert result.success is False
        assert result.error is not None

    def test_variable_assignment_not_allowed(self, calculator):
        """Test variable assignment returns error."""
        result = calculator.execute(expression="x = 5")

        assert result.success is False
        assert result.error is not None


class TestCalculatorToolInterface:
    """Test tool interface compliance."""

    def test_execute_safe_method(self):
        """Test execute_safe method works correctly."""
        tool = CalculatorTool()
        result = tool.execute_safe(expression="2 + 2")

        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.content == "4"

    def test_execute_safe_with_validation_error(self):
        """Test execute_safe handles validation errors."""
        tool = CalculatorTool()
        result = tool.execute_safe()  # Missing required parameter

        assert isinstance(result, ToolResult)
        assert result.success is False
        assert result.error is not None

    def test_anthropic_schema_generation(self):
        """Test Anthropic schema generation."""
        tool = CalculatorTool()
        schema = tool.to_anthropic_schema()

        assert "name" in schema
        assert schema["name"] == "calculator"
        assert "description" in schema
        assert "input_schema" in schema
        assert "properties" in schema["input_schema"]
        assert "expression" in schema["input_schema"]["properties"]

    def test_openai_schema_generation(self):
        """Test OpenAI schema generation."""
        tool = CalculatorTool()
        schema = tool.to_openai_schema()

        assert "type" in schema
        assert schema["type"] == "function"
        assert "function" in schema
        assert "name" in schema["function"]
        assert schema["function"]["name"] == "calculator"
        assert "parameters" in schema["function"]

    def test_get_stats(self):
        """Test statistics tracking."""
        tool = CalculatorTool()

        # Execute a few operations
        tool.execute_safe(expression="2 + 2")
        tool.execute_safe(expression="3 * 3")

        stats = tool.get_stats()

        assert "name" in stats
        assert stats["name"] == "calculator"
        assert "executions" in stats
        assert stats["executions"] == 2
        assert "success_rate" in stats

    def test_reset_stats(self):
        """Test statistics reset."""
        tool = CalculatorTool()

        # Execute and verify stats
        tool.execute_safe(expression="2 + 2")
        stats = tool.get_stats()
        assert stats["executions"] == 1

        # Reset and verify
        tool.reset_stats()
        stats = tool.get_stats()
        assert stats["executions"] == 0


class TestCalculatorMetadata:
    """Test metadata in results."""

    @pytest.fixture
    def calculator(self) -> CalculatorTool:
        """Create calculator tool instance."""
        return CalculatorTool()

    def test_success_metadata(self, calculator):
        """Test successful execution includes metadata."""
        result = calculator.execute(expression="2 + 2")

        assert result.success is True
        assert result.metadata is not None
        assert "expression" in result.metadata
        assert result.metadata["expression"] == "2 + 2"

    def test_metadata_includes_result_type(self, calculator):
        """Test metadata includes result type."""
        result = calculator.execute(expression="5")

        assert "result_type" in result.metadata


class TestCalculatorEdgeCases:
    """Test edge cases and special scenarios."""

    @pytest.fixture
    def calculator(self) -> CalculatorTool:
        """Create calculator tool instance."""
        return CalculatorTool()

    def test_very_large_numbers(self, calculator):
        """Test very large number handling."""
        result = calculator.execute(expression="2 ** 100")

        # Should succeed (within bounds)
        assert result.success is True

    def test_extremely_large_overflow(self, calculator):
        """Test overflow protection."""
        result = calculator.execute(expression="10 ** 1000")

        # Should fail gracefully (too large)
        assert result.success is False
        assert result.error is not None

    def test_very_small_numbers(self, calculator):
        """Test very small numbers."""
        result = calculator.execute(expression="1 / 1000000")

        assert result.success is True
        assert float(result.content) == pytest.approx(1e-6)

    def test_integer_result_formatting(self, calculator):
        """Test integer results are formatted as integers."""
        result = calculator.execute(expression="4.0 + 2.0")

        assert result.success is True
        assert result.content == "6"  # Not "6.0"

    def test_expression_with_whitespace(self, calculator):
        """Test expressions with extra whitespace."""
        result = calculator.execute(expression="  2  +  3  ")

        assert result.success is True
        assert result.content == "5"
