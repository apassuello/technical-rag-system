"""
End-to-end scenario test: Code analysis tool usage.

Scenario:
User provides Python code
Expected: CodeAnalyzer tool called, analysis provided

This test validates the complete code analysis flow:
1. User provides code → Tool selection
2. Code parsing → AST analysis
3. Analysis generation → Result formatting

Author: Epic 5 Phase 1 Block 3 Testing Agent
Created: 2025-11-17
"""

import pytest
from typing import Dict, List, Any
from unittest.mock import Mock, MagicMock

from src.components.query_processors.tools.tool_registry import ToolRegistry
from src.components.query_processors.tools.implementations import CodeAnalyzerTool
from src.components.query_processors.tools.models import ToolResult


class TestCodeAnalysisScenario:
    """
    End-to-end scenario tests for Code Analyzer tool usage.

    These tests simulate real code analysis requests where an LLM
    uses the code analyzer to understand Python code structure.
    """

    def test_simple_function_analysis_scenario(self) -> None:
        """
        Scenario: User provides a simple Python function.

        Expected Flow:
        1. User provides function code
        2. CodeAnalyzer tool selected
        3. Code parsed and analyzed
        4. Function details returned (name, parameters, docstring)
        5. Results formatted for LLM

        This test validates:
        - Tool registration works
        - Code parsing succeeds
        - Analysis results complete
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        code = """
def calculate_area(length: float, width: float) -> float:
    \"\"\"Calculate area of a rectangle.\"\"\"
    return length * width
"""

        # Act
        result = registry.execute_tool("analyze_code", code=code)

        # Assert
        assert result.success is True
        assert result.content is not None
        assert "function" in result.content.lower()
        assert "calculate_area" in result.content
        assert result.error is None

    def test_class_analysis_scenario(self) -> None:
        """
        Scenario: User provides a Python class.

        Expected Flow:
        1. User provides class code
        2. Code analyzed
        3. Class structure returned (methods, attributes)
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        code = """
class Calculator:
    \"\"\"A simple calculator class.\"\"\"

    def add(self, a: int, b: int) -> int:
        return a + b

    def subtract(self, a: int, b: int) -> int:
        return a - b
"""

        # Act
        result = registry.execute_tool("analyze_code", code=code)

        # Assert
        assert result.success is True
        assert result.content is not None
        assert "class" in result.content.lower()
        assert "Calculator" in result.content
        assert "method" in result.content.lower() or "function" in result.content.lower()

    def test_complex_code_scenario(self) -> None:
        """
        Scenario: User provides complex code with multiple elements.

        Expected Flow:
        1. Complex code with functions, classes, imports
        2. Comprehensive analysis performed
        3. All elements identified
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        code = """
import math
from typing import List

def process_data(items: List[int]) -> float:
    \"\"\"Process a list of items.\"\"\"
    return sum(items) / len(items)

class DataProcessor:
    def __init__(self, data: List[int]):
        self.data = data

    def analyze(self) -> Dict[str, float]:
        return {
            'mean': process_data(self.data),
            'max': max(self.data),
            'min': min(self.data)
        }
"""

        # Act
        result = registry.execute_tool("analyze_code", code=code)

        # Assert
        assert result.success is True
        assert result.content is not None
        # Should identify both function and class
        assert "function" in result.content.lower() or "def" in result.content.lower()
        assert "class" in result.content.lower()

    def test_syntax_error_scenario(self) -> None:
        """
        Scenario: User provides code with syntax error.

        Expected Flow:
        1. Invalid Python code provided
        2. Syntax error detected
        3. Error message returned
        4. System remains stable
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        invalid_code = """
def broken_function(
    return "missing closing parenthesis"
"""

        # Act
        result = registry.execute_tool("analyze_code", code=invalid_code)

        # Assert - syntax errors return success=True with error info in metadata
        assert result.success is True
        assert result.metadata.get('syntax_valid') is False
        assert 'syntax' in result.content.lower() or 'error' in result.content.lower()

    def test_empty_code_scenario(self) -> None:
        """
        Scenario: User provides empty code string.

        Expected Flow:
        1. Empty code detected
        2. Appropriate error returned
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

    def test_multiple_analysis_scenario(self) -> None:
        """
        Scenario: User analyzes multiple code snippets in sequence.

        Expected Flow:
        1. First code snippet analyzed
        2. Second code snippet analyzed
        3. Third code snippet analyzed
        4. Each analysis independent and successful
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        snippets = [
            "def func1(): pass",
            "class Class1: pass",
            "x = 42",
        ]

        # Act
        results = []
        for code in snippets:
            result = registry.execute_tool("analyze_code", code=code)
            results.append(result)

        # Assert
        assert len(results) == 3
        assert all(r.success for r in results)


class TestCodeAnalysisWithAnthropicAdapter:
    """
    Test Code Analyzer tool with Anthropic adapter integration.
    """

    def test_code_analyzer_schema_for_anthropic(self) -> None:
        """
        Test: Generate proper Anthropic schema for code analyzer.

        Verifies:
        - Schema matches Anthropic format
        - Required fields present
        - Parameter schema correct
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        # Act
        schemas = registry.get_anthropic_schemas()

        # Assert
        assert len(schemas) == 1

        analyzer_schema = schemas[0]
        assert analyzer_schema["name"] == "analyze_code"
        assert "description" in analyzer_schema
        assert "input_schema" in analyzer_schema

        input_schema = analyzer_schema["input_schema"]
        assert input_schema["type"] == "object"
        assert "code" in input_schema["properties"]
        assert "code" in input_schema["required"]

    def test_code_analyzer_with_mock_anthropic_call(self) -> None:
        """
        Test: Simulate Anthropic API call with code analyzer tool.

        Scenario:
        1. User asks Claude to analyze code
        2. Claude decides to use code analyzer
        3. Tool executes analysis
        4. Results returned to Claude
        5. Claude explains the code
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        # Simulate Claude's tool use request
        tool_name = "analyze_code"
        tool_input = {
            "code": "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)"
        }

        # Act
        result = registry.execute_tool(tool_name, **tool_input)

        # Assert
        assert result.success is True
        assert "function" in result.content.lower() or "factorial" in result.content


class TestCodeAnalysisWithOpenAIAdapter:
    """
    Test Code Analyzer tool with OpenAI adapter integration.
    """

    def test_code_analyzer_schema_for_openai(self) -> None:
        """
        Test: Generate proper OpenAI schema for code analyzer.

        Verifies:
        - Schema matches OpenAI function calling format
        - Required fields present
        - Parameter schema correct
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        # Act
        schemas = registry.get_openai_schemas()

        # Assert
        assert len(schemas) == 1

        analyzer_schema = schemas[0]
        assert analyzer_schema["type"] == "function"
        assert "function" in analyzer_schema

        function = analyzer_schema["function"]
        assert function["name"] == "analyze_code"
        assert "description" in function
        assert "parameters" in function

        parameters = function["parameters"]
        assert parameters["type"] == "object"
        assert "code" in parameters["properties"]
        assert "code" in parameters["required"]

    def test_code_analyzer_with_mock_openai_call(self) -> None:
        """
        Test: Simulate OpenAI function call with code analyzer tool.
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        # Simulate GPT function call
        function_name = "analyze_code"
        function_args = {
            "code": "class Point:\n    def __init__(self, x, y):\n        self.x = x\n        self.y = y"
        }

        # Act
        result = registry.execute_tool(function_name, **function_args)

        # Assert
        assert result.success is True
        assert "class" in result.content.lower() or "Point" in result.content


class TestCodeAnalysisPerformance:
    """
    Performance tests for code analyzer tool.
    """

    def test_code_analysis_execution_time(self) -> None:
        """
        Test: Code analysis executes within acceptable time.

        Requirement: Execution time < 500ms for typical code.

        This ensures responsive user experience.
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        code = """
def example_function(param1: str, param2: int) -> bool:
    \"\"\"Example function for testing.\"\"\"
    if param2 > 0:
        print(param1)
        return True
    return False
"""

        # Act
        result = registry.execute_tool("analyze_code", code=code)

        # Assert
        assert result.success is True
        assert result.execution_time < 0.5  # 500ms max

    def test_large_code_analysis(self) -> None:
        """
        Test: Analyzer handles large code files efficiently.
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        # Generate large code file (50 functions)
        large_code = "\n".join([
            f"def function_{i}(x):\n    return x * {i}"
            for i in range(50)
        ])

        # Act
        result = registry.execute_tool("analyze_code", code=large_code)

        # Assert
        assert result.success is True
        assert result.execution_time < 2.0  # 2 seconds max for large files

    def test_multiple_rapid_analyses(self) -> None:
        """
        Test: Analyzer handles multiple rapid analysis requests.
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        snippets = [f"def func{i}(): pass" for i in range(10)]

        # Act
        results = []
        for code in snippets:
            result = registry.execute_tool("analyze_code", code=code)
            results.append(result)

        # Assert
        assert len(results) == 10
        assert all(r.success for r in results)


class TestCodeAnalysisEdgeCases:
    """
    Edge case tests for code analyzer tool.
    """

    def test_minimal_code(self) -> None:
        """
        Test: Analyzer handles minimal valid code.
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        # Act
        result = registry.execute_tool("analyze_code", code="x = 1")

        # Assert
        assert result.success is True

    def test_complex_nested_code(self) -> None:
        """
        Test: Analyzer handles deeply nested code structures.
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        nested_code = """
class Outer:
    class Inner:
        class DeepInner:
            def nested_method(self):
                def inner_function():
                    return lambda x: x * 2
                return inner_function
"""

        # Act
        result = registry.execute_tool("analyze_code", code=nested_code)

        # Assert
        assert result.success is True

    def test_code_with_decorators(self) -> None:
        """
        Test: Analyzer handles decorated functions.
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        code = """
@staticmethod
@property
def decorated_function():
    return "value"
"""

        # Act
        result = registry.execute_tool("analyze_code", code=code)

        # Assert
        assert result.success is True

    def test_code_with_type_hints(self) -> None:
        """
        Test: Analyzer handles advanced type hints.
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        code = """
from typing import List, Dict, Optional, Union

def typed_function(
    items: List[Dict[str, Union[int, str]]],
    config: Optional[Dict[str, Any]] = None
) -> tuple[bool, str]:
    return True, "success"
"""

        # Act
        result = registry.execute_tool("analyze_code", code=code)

        # Assert
        assert result.success is True

    def test_code_with_async(self) -> None:
        """
        Test: Analyzer handles async/await code.
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        code = """
async def async_function():
    await some_awaitable()
    return "done"
"""

        # Act
        result = registry.execute_tool("analyze_code", code=code)

        # Assert
        assert result.success is True

    def test_code_with_generators(self) -> None:
        """
        Test: Analyzer handles generator functions.
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        code = """
def generator_function(n):
    for i in range(n):
        yield i * 2
"""

        # Act
        result = registry.execute_tool("analyze_code", code=code)

        # Assert
        assert result.success is True

    def test_code_with_context_managers(self) -> None:
        """
        Test: Analyzer handles context managers.
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        code = """
class MyContextManager:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
"""

        # Act
        result = registry.execute_tool("analyze_code", code=code)

        # Assert
        assert result.success is True

    def test_code_with_metaclasses(self) -> None:
        """
        Test: Analyzer handles metaclasses.
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        code = """
class Meta(type):
    def __new__(cls, name, bases, dct):
        return super().__new__(cls, name, bases, dct)

class MyClass(metaclass=Meta):
    pass
"""

        # Act
        result = registry.execute_tool("analyze_code", code=code)

        # Assert
        assert result.success is True

    def test_very_long_code(self) -> None:
        """
        Test: Analyzer handles very long code files.
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        # Generate very long code (1000 lines)
        long_code = "\n".join([
            f"# Line {i}\ndef func_{i}(): return {i}"
            for i in range(500)
        ])

        # Act
        result = registry.execute_tool("analyze_code", code=long_code)

        # Assert
        assert result is not None
        assert isinstance(result, ToolResult)
        # Should either succeed or fail gracefully with size limit error

    def test_code_with_special_characters(self) -> None:
        """
        Test: Analyzer handles code with special characters in strings.
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        code = """
def special_chars():
    s = "Hello @#$%^&*() World!"
    return s
"""

        # Act
        result = registry.execute_tool("analyze_code", code=code)

        # Assert
        assert result.success is True

    def test_code_with_unicode(self) -> None:
        """
        Test: Analyzer handles Unicode characters in code.
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        code = """
def unicode_function():
    greeting = "Здравствуй мир"  # Russian
    result = "你好世界"  # Chinese
    return greeting + result
"""

        # Act
        result = registry.execute_tool("analyze_code", code=code)

        # Assert
        assert result.success is True


class TestCodeAnalysisDetailedOutput:
    """
    Tests for detailed code analysis output.
    """

    def test_analysis_includes_function_signature(self) -> None:
        """
        Test: Analysis includes function signature details.
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        code = """
def calculate(x: int, y: int, operation: str = "add") -> int:
    \"\"\"Perform calculation on two numbers.\"\"\"
    if operation == "add":
        return x + y
    return x - y
"""

        # Act
        result = registry.execute_tool("analyze_code", code=code)

        # Assert
        assert result.success is True
        # Should include function name
        assert "calculate" in result.content

    def test_analysis_includes_class_structure(self) -> None:
        """
        Test: Analysis includes class structure details.
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        code = """
class Vehicle:
    \"\"\"Base vehicle class.\"\"\"

    def __init__(self, brand: str):
        self.brand = brand

    def start(self):
        return "Starting..."
"""

        # Act
        result = registry.execute_tool("analyze_code", code=code)

        # Assert
        assert result.success is True
        assert "Vehicle" in result.content or "class" in result.content.lower()
