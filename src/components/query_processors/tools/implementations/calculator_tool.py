"""
Calculator tool for safe mathematical expression evaluation.

Provides LLMs with the ability to perform accurate mathematical calculations
without the risk of arbitrary code execution.

Architecture:
- Safe evaluation using ast.literal_eval and operator mapping
- Supports basic arithmetic and mathematical functions
- NEVER raises exceptions (returns errors in ToolResult)
- Comprehensive input validation
- Clear error messages for LLM understanding

Usage:
    >>> from src.components.query_processors.tools.implementations import CalculatorTool
    >>>
    >>> calculator = CalculatorTool()
    >>> result = calculator.execute(expression="25 * 47 + 100")
    >>> print(result.content)  # "1275"
    >>>
    >>> # Error handling
    >>> result = calculator.execute(expression="1 / 0")
    >>> print(result.error)  # "Division by zero"
"""

import ast
import operator
import math
from typing import List, Any, Union
import logging

from ..base_tool import BaseTool
from ..models import ToolParameter, ToolParameterType, ToolResult


logger = logging.getLogger(__name__)


class CalculatorTool(BaseTool):
    """
    Safe mathematical expression evaluator.

    Evaluates mathematical expressions using a restricted AST parser
    that only allows safe operations (no arbitrary code execution).

    Supported Operations:
    - Arithmetic: +, -, *, /, //, %, **
    - Unary: +, -
    - Functions: sqrt, sin, cos, tan, log, log10, exp, abs, ceil, floor
    - Constants: pi, e

    Safety:
    - No eval() or exec()
    - No arbitrary code execution
    - Input validation
    - Result bounds checking
    - Comprehensive error handling

    Example:
        >>> tool = CalculatorTool()
        >>> result = tool.execute(expression="sqrt(16) + 2 ** 3")
        >>> print(result.content)  # "12.0"
        >>>
        >>> # Complex expression
        >>> result = tool.execute(expression="(25 * 47) + (100 / 4)")
        >>> print(result.content)  # "1200.0"
    """

    # Safe operators mapping
    _OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    # Safe functions mapping
    _FUNCTIONS = {
        'sqrt': math.sqrt,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'log': math.log,
        'log10': math.log10,
        'exp': math.exp,
        'abs': abs,
        'ceil': math.ceil,
        'floor': math.floor,
        'round': round,
    }

    # Safe constants
    _CONSTANTS = {
        'pi': math.pi,
        'e': math.e,
    }

    # Maximum result magnitude to prevent overflow issues
    _MAX_RESULT = 1e100

    def __init__(self):
        """
        Initialize calculator tool.

        Sets up operator mappings and validation rules.
        """
        super().__init__()
        self._logger.info("Initialized CalculatorTool")

    @property
    def name(self) -> str:
        """
        Tool name.

        Returns:
            "calculator"
        """
        return "calculator"

    @property
    def description(self) -> str:
        """
        Tool description for LLM.

        Returns:
            Clear description of calculator capabilities and when to use it
        """
        return (
            "Evaluates mathematical expressions safely. "
            "Supports arithmetic operators (+, -, *, /, **, %), "
            "mathematical functions (sqrt, sin, cos, tan, log, exp), "
            "and constants (pi, e). "
            "Use this tool for any mathematical calculations. "
            "Returns the numerical result as a string."
        )

    def get_parameters(self) -> List[ToolParameter]:
        """
        Get tool parameter definitions.

        Returns:
            List containing single 'expression' parameter
        """
        return [
            ToolParameter(
                name="expression",
                type=ToolParameterType.STRING,
                description=(
                    "Mathematical expression to evaluate. "
                    "Can include numbers, operators (+, -, *, /, **, %), "
                    "functions (sqrt, sin, cos, log, etc.), "
                    "and constants (pi, e). "
                    "Example: '25 * 47 + sqrt(16)'"
                ),
                required=True
            )
        ]

    def execute(self, expression: str) -> ToolResult:
        """
        Execute mathematical expression evaluation.

        Args:
            expression: Mathematical expression to evaluate

        Returns:
            ToolResult with:
            - success=True, content=result (as string) on success
            - success=False, error=description on failure

        Example:
            >>> result = tool.execute(expression="2 + 2")
            >>> print(result.content)  # "4"
            >>>
            >>> result = tool.execute(expression="sqrt(16) * 3")
            >>> print(result.content)  # "12.0"
        """
        try:
            # Validate input
            if not expression or not expression.strip():
                return ToolResult(
                    success=False,
                    error="Expression cannot be empty"
                )

            expression = expression.strip()

            # Log execution
            self._logger.debug(f"Evaluating expression: {expression}")

            # Parse expression into AST
            try:
                tree = ast.parse(expression, mode='eval')
            except SyntaxError as e:
                return ToolResult(
                    success=False,
                    error=f"Invalid expression syntax: {str(e)}"
                )

            # Evaluate the AST
            try:
                result = self._eval_node(tree.body)
            except ZeroDivisionError:
                return ToolResult(
                    success=False,
                    error="Division by zero"
                )
            except ValueError as e:
                return ToolResult(
                    success=False,
                    error=f"Mathematical error: {str(e)}"
                )
            except OverflowError:
                return ToolResult(
                    success=False,
                    error="Result too large (overflow)"
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    error=f"Evaluation error: {str(e)}"
                )

            # Validate result
            if not isinstance(result, (int, float)):
                return ToolResult(
                    success=False,
                    error=f"Invalid result type: {type(result).__name__}"
                )

            # Check for overflow
            if abs(result) > self._MAX_RESULT:
                return ToolResult(
                    success=False,
                    error=f"Result too large: {result}"
                )

            # Check for NaN or infinity
            if math.isnan(result):
                return ToolResult(
                    success=False,
                    error="Result is not a number (NaN)"
                )
            if math.isinf(result):
                return ToolResult(
                    success=False,
                    error="Result is infinite"
                )

            # Format result
            # Use integer formatting if result is a whole number
            if isinstance(result, float) and result.is_integer():
                content = str(int(result))
            else:
                content = str(result)

            self._logger.debug(f"Expression evaluated successfully: {content}")

            return ToolResult(
                success=True,
                content=content,
                metadata={
                    "expression": expression,
                    "result_type": type(result).__name__
                }
            )

        except Exception as e:
            # This should never happen (all exceptions should be caught above)
            # But we handle it anyway for absolute safety
            self._logger.error(f"Unexpected error in calculator: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )

    def _eval_node(self, node: ast.AST) -> Union[int, float]:
        """
        Recursively evaluate AST node.

        Args:
            node: AST node to evaluate

        Returns:
            Numerical result

        Raises:
            ValueError: If node type is not allowed
            ZeroDivisionError: If division by zero
            OverflowError: If result too large
        """
        # Number literal
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Unsupported constant type: {type(node.value).__name__}")

        # Binary operation (e.g., 2 + 3)
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_type = type(node.op)

            if op_type not in self._OPERATORS:
                raise ValueError(f"Unsupported operator: {op_type.__name__}")

            op_func = self._OPERATORS[op_type]
            return op_func(left, right)

        # Unary operation (e.g., -5)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op_type = type(node.op)

            if op_type not in self._OPERATORS:
                raise ValueError(f"Unsupported unary operator: {op_type.__name__}")

            op_func = self._OPERATORS[op_type]
            return op_func(operand)

        # Function call (e.g., sqrt(16))
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple function calls are supported")

            func_name = node.func.id
            if func_name not in self._FUNCTIONS:
                raise ValueError(f"Unsupported function: {func_name}")

            # Evaluate arguments
            args = [self._eval_node(arg) for arg in node.args]

            # Call function
            func = self._FUNCTIONS[func_name]
            try:
                return func(*args)
            except TypeError as e:
                raise ValueError(f"Invalid arguments for {func_name}: {str(e)}")

        # Name (variable/constant, e.g., pi, e)
        elif isinstance(node, ast.Name):
            name = node.id
            if name not in self._CONSTANTS:
                raise ValueError(f"Unsupported constant: {name}")
            return self._CONSTANTS[name]

        # Unsupported node type
        else:
            raise ValueError(f"Unsupported expression type: {type(node).__name__}")
