"""
Unit tests for CodeAnalyzerTool.

Tests cover:
- Code structure analysis (functions, classes, imports)
- Syntax validation
- Complexity metrics
- Error handling
- Input validation
- Tool interface compliance

Test Strategy:
- Comprehensive coverage of Python code structures
- Validation of error handling (tools never raise exceptions)
- Verification of analysis completeness
- Safe execution (no code is actually run)
"""

import pytest
from typing import Dict, Any

from src.components.query_processors.tools.implementations import CodeAnalyzerTool
from src.components.query_processors.tools import ToolResult, ToolParameter


class TestCodeAnalyzerToolBasics:
    """Test basic code analyzer tool functionality."""

    def test_tool_initialization(self):
        """Test tool can be initialized."""
        tool = CodeAnalyzerTool()
        assert tool is not None
        assert tool.name == "analyze_code"

    def test_tool_name(self):
        """Test tool has correct name."""
        tool = CodeAnalyzerTool()
        assert tool.name == "analyze_code"
        assert isinstance(tool.name, str)

    def test_tool_description(self):
        """Test tool has meaningful description."""
        tool = CodeAnalyzerTool()
        assert tool.description is not None
        assert len(tool.description) > 0
        assert "code" in tool.description.lower() or "analyze" in tool.description.lower()

    def test_get_parameters(self):
        """Test tool returns correct parameter definitions."""
        tool = CodeAnalyzerTool()
        params = tool.get_parameters()

        assert isinstance(params, list)
        assert len(params) == 1  # Only 'code' parameter

        param = params[0]
        assert param.name == "code"
        assert param.required is True

    def test_parameter_validation_success(self):
        """Test parameter validation accepts valid inputs."""
        tool = CodeAnalyzerTool()
        valid, error = tool.validate_parameters(code="def foo(): pass")

        assert valid is True
        assert error is None

    def test_parameter_validation_missing(self):
        """Test parameter validation rejects missing required params."""
        tool = CodeAnalyzerTool()
        valid, error = tool.validate_parameters()

        assert valid is False
        assert error is not None
        assert "code" in error.lower()


class TestCodeAnalyzerFunctions:
    """Test function analysis."""

    @pytest.fixture
    def analyzer(self) -> CodeAnalyzerTool:
        """Create analyzer tool instance."""
        return CodeAnalyzerTool()

    def test_simple_function(self, analyzer):
        """Test analysis of simple function."""
        code = """
def hello():
    return "world"
"""
        result = analyzer.execute(code=code)

        assert result.success is True
        assert result.metadata["syntax_valid"] is True
        assert result.metadata["num_functions"] == 1
        assert len(result.metadata["functions"]) == 1
        assert result.metadata["functions"][0]["name"] == "hello"

    def test_function_with_parameters(self, analyzer):
        """Test function with parameters."""
        code = """
def greet(name, age):
    return f"Hello {name}, you are {age}"
"""
        result = analyzer.execute(code=code)

        assert result.success is True
        func = result.metadata["functions"][0]
        assert func["name"] == "greet"
        assert func["num_parameters"] == 2
        assert "name" in func["parameters"]
        assert "age" in func["parameters"]

    def test_function_with_docstring(self, analyzer):
        """Test function with docstring."""
        code = '''
def documented():
    """This function has a docstring."""
    return True
'''
        result = analyzer.execute(code=code)

        assert result.success is True
        func = result.metadata["functions"][0]
        assert func["has_docstring"] is True

    def test_function_without_docstring(self, analyzer):
        """Test function without docstring."""
        code = """
def undocumented():
    return True
"""
        result = analyzer.execute(code=code)

        assert result.success is True
        func = result.metadata["functions"][0]
        assert func["has_docstring"] is False

    def test_multiple_functions(self, analyzer):
        """Test analysis of multiple functions."""
        code = """
def func1():
    pass

def func2(x):
    return x * 2

def func3(a, b, c):
    return a + b + c
"""
        result = analyzer.execute(code=code)

        assert result.success is True
        assert result.metadata["num_functions"] == 3
        assert len(result.metadata["functions"]) == 3

        names = [f["name"] for f in result.metadata["functions"]]
        assert "func1" in names
        assert "func2" in names
        assert "func3" in names

    def test_async_function(self, analyzer):
        """Test async function detection."""
        code = """
async def async_function():
    return "async"
"""
        result = analyzer.execute(code=code)

        assert result.success is True
        func = result.metadata["functions"][0]
        assert func["is_async"] is True

    def test_regular_function_not_async(self, analyzer):
        """Test regular function is not marked as async."""
        code = """
def regular_function():
    return "sync"
"""
        result = analyzer.execute(code=code)

        assert result.success is True
        func = result.metadata["functions"][0]
        assert func["is_async"] is False


class TestCodeAnalyzerClasses:
    """Test class analysis."""

    @pytest.fixture
    def analyzer(self) -> CodeAnalyzerTool:
        """Create analyzer tool instance."""
        return CodeAnalyzerTool()

    def test_simple_class(self, analyzer):
        """Test analysis of simple class."""
        code = """
class MyClass:
    pass
"""
        result = analyzer.execute(code=code)

        assert result.success is True
        assert result.metadata["num_classes"] == 1
        assert len(result.metadata["classes"]) == 1
        assert result.metadata["classes"][0]["name"] == "MyClass"

    def test_class_with_methods(self, analyzer):
        """Test class with methods."""
        code = """
class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

    def multiply(self, a, b):
        return a * b
"""
        result = analyzer.execute(code=code)

        assert result.success is True
        cls = result.metadata["classes"][0]
        assert cls["name"] == "Calculator"
        assert cls["num_methods"] == 3

    def test_class_with_inheritance(self, analyzer):
        """Test class with base classes."""
        code = """
class Parent:
    pass

class Child(Parent):
    pass
"""
        result = analyzer.execute(code=code)

        assert result.success is True
        assert result.metadata["num_classes"] == 2

        # Find Child class
        child = next(c for c in result.metadata["classes"] if c["name"] == "Child")
        assert "Parent" in child["base_classes"]

    def test_class_with_docstring(self, analyzer):
        """Test class with docstring."""
        code = '''
class Documented:
    """This class has a docstring."""
    pass
'''
        result = analyzer.execute(code=code)

        assert result.success is True
        cls = result.metadata["classes"][0]
        assert cls["has_docstring"] is True

    def test_class_without_docstring(self, analyzer):
        """Test class without docstring."""
        code = """
class Undocumented:
    pass
"""
        result = analyzer.execute(code=code)

        assert result.success is True
        cls = result.metadata["classes"][0]
        assert cls["has_docstring"] is False

    def test_multiple_classes(self, analyzer):
        """Test analysis of multiple classes."""
        code = """
class Class1:
    pass

class Class2:
    def method(self):
        pass

class Class3(Class1, Class2):
    pass
"""
        result = analyzer.execute(code=code)

        assert result.success is True
        assert result.metadata["num_classes"] == 3


class TestCodeAnalyzerImports:
    """Test import analysis."""

    @pytest.fixture
    def analyzer(self) -> CodeAnalyzerTool:
        """Create analyzer tool instance."""
        return CodeAnalyzerTool()

    def test_simple_import(self, analyzer):
        """Test simple import statement."""
        code = """
import math
"""
        result = analyzer.execute(code=code)

        assert result.success is True
        assert result.metadata["num_imports"] == 1
        assert "math" in result.metadata["imports"]

    def test_multiple_imports(self, analyzer):
        """Test multiple import statements."""
        code = """
import os
import sys
import math
"""
        result = analyzer.execute(code=code)

        assert result.success is True
        assert result.metadata["num_imports"] == 3
        assert "os" in result.metadata["imports"]
        assert "sys" in result.metadata["imports"]
        assert "math" in result.metadata["imports"]

    def test_from_import(self, analyzer):
        """Test from...import statement."""
        code = """
from typing import List, Dict
"""
        result = analyzer.execute(code=code)

        assert result.success is True
        # from typing import List, Dict counts as 1 import statement but 2 names
        assert result.metadata["num_imports"] == 1

    def test_combined_imports(self, analyzer):
        """Test combination of import types."""
        code = """
import os
from typing import List
import sys
from pathlib import Path
"""
        result = analyzer.execute(code=code)

        assert result.success is True
        assert result.metadata["num_imports"] == 4


class TestCodeAnalyzerMetrics:
    """Test code metrics and complexity analysis."""

    @pytest.fixture
    def analyzer(self) -> CodeAnalyzerTool:
        """Create analyzer tool instance."""
        return CodeAnalyzerTool()

    def test_lines_of_code(self, analyzer):
        """Test lines of code counting."""
        code = """
def func1():
    pass

def func2():
    return True
"""
        result = analyzer.execute(code=code)

        assert result.success is True
        assert result.metadata["lines_of_code"] > 0

    def test_statement_counting(self, analyzer):
        """Test statement counting."""
        code = """
x = 1
y = 2
z = x + y
"""
        result = analyzer.execute(code=code)

        assert result.success is True
        assert result.metadata["num_statements"] >= 3

    def test_main_block_detection(self, analyzer):
        """Test detection of if __name__ == "__main__": block."""
        code = '''
def main():
    print("Hello")

if __name__ == "__main__":
    main()
'''
        result = analyzer.execute(code=code)

        assert result.success is True
        assert result.metadata["has_main_block"] is True

    def test_no_main_block(self, analyzer):
        """Test code without main block."""
        code = """
def func():
    pass
"""
        result = analyzer.execute(code=code)

        assert result.success is True
        assert result.metadata["has_main_block"] is False

    def test_function_complexity_metric(self, analyzer):
        """Test average function complexity calculation."""
        code = """
def simple():
    return 1

def complex():
    x = 1
    y = 2
    z = 3
    return x + y + z
"""
        result = analyzer.execute(code=code)

        assert result.success is True
        assert "avg_function_complexity" in result.metadata
        assert result.metadata["avg_function_complexity"] > 0


class TestCodeAnalyzerSyntaxErrors:
    """Test syntax error handling."""

    @pytest.fixture
    def analyzer(self) -> CodeAnalyzerTool:
        """Create analyzer tool instance."""
        return CodeAnalyzerTool()

    def test_syntax_error_detection(self, analyzer):
        """Test syntax error is detected and reported."""
        code = """
def broken(
    return "missing closing paren"
"""
        result = analyzer.execute(code=code)

        # Syntax error is a valid analysis result, not a failure
        assert result.success is True
        assert result.metadata["syntax_valid"] is False
        assert "error_type" in result.metadata
        assert result.metadata["error_type"] == "SyntaxError"

    def test_invalid_indentation(self, analyzer):
        """Test invalid indentation is detected."""
        code = """
def func():
return "bad indent"
"""
        result = analyzer.execute(code=code)

        assert result.success is True
        assert result.metadata["syntax_valid"] is False

    def test_syntax_error_formatting(self, analyzer):
        """Test syntax error is formatted for LLM."""
        code = "def broken("

        result = analyzer.execute(code=code)

        assert result.success is True
        assert result.content is not None
        assert "SYNTAX ERROR" in result.content
        assert "Error:" in result.content

    def test_valid_syntax_indicator(self, analyzer):
        """Test valid syntax is indicated in results."""
        code = "def valid(): pass"

        result = analyzer.execute(code=code)

        assert result.success is True
        assert result.metadata["syntax_valid"] is True
        assert "SUCCESS" in result.content


class TestCodeAnalyzerInputValidation:
    """Test input validation and edge cases."""

    @pytest.fixture
    def analyzer(self) -> CodeAnalyzerTool:
        """Create analyzer tool instance."""
        return CodeAnalyzerTool()

    def test_empty_code(self, analyzer):
        """Test error on empty code."""
        result = analyzer.execute(code="")

        assert result.success is False
        assert result.error is not None
        assert "empty" in result.error.lower()

    def test_whitespace_only_code(self, analyzer):
        """Test error on whitespace-only code."""
        result = analyzer.execute(code="   \n\n   ")

        assert result.success is False
        assert result.error is not None

    def test_none_code(self, analyzer):
        """Test error on None code."""
        result = analyzer.execute(code=None)

        assert result.success is False
        assert result.error is not None
        assert "None" in result.error

    def test_minimal_valid_code(self, analyzer):
        """Test minimal valid code."""
        result = analyzer.execute(code="pass")

        assert result.success is True
        assert result.metadata["syntax_valid"] is True

    def test_comment_only_code(self, analyzer):
        """Test code with only comments."""
        code = """
# This is a comment
# Another comment
"""
        result = analyzer.execute(code=code)

        assert result.success is True
        assert result.metadata["syntax_valid"] is True
        assert result.metadata["num_functions"] == 0
        assert result.metadata["num_classes"] == 0


class TestCodeAnalyzerResultFormatting:
    """Test result formatting."""

    @pytest.fixture
    def analyzer(self) -> CodeAnalyzerTool:
        """Create analyzer tool instance."""
        return CodeAnalyzerTool()

    def test_complete_analysis_formatting(self, analyzer):
        """Test complete analysis is formatted correctly."""
        code = '''
import math

def calculate_area(radius):
    """Calculate circle area."""
    return math.pi * radius ** 2

class Circle:
    """A circle class."""
    def __init__(self, radius):
        self.radius = radius

if __name__ == "__main__":
    print("Hello")
'''
        result = analyzer.execute(code=code)

        assert result.success is True
        content = result.content

        # Check key sections are present
        assert "SUCCESS" in content
        assert "Basic Metrics" in content
        assert "Imports" in content
        assert "Functions" in content
        assert "Classes" in content
        assert "Code Quality Notes" in content

        # Check specific details
        assert "math" in content  # Import
        assert "calculate_area" in content  # Function
        assert "Circle" in content  # Class
        assert "has docstring" in content.lower()  # Docstring detection

    def test_empty_analysis_formatting(self, analyzer):
        """Test formatting when no code structures found."""
        code = "# Just a comment"

        result = analyzer.execute(code=code)

        assert result.success is True
        content = result.content

        assert "SUCCESS" in content
        assert "Functions: 0" in content
        assert "Classes: 0" in content


class TestCodeAnalyzerToolInterface:
    """Test tool interface compliance."""

    def test_execute_safe_method(self):
        """Test execute_safe method works correctly."""
        tool = CodeAnalyzerTool()
        result = tool.execute_safe(code="def foo(): pass")

        assert isinstance(result, ToolResult)
        assert result.success is True

    def test_execute_safe_with_validation_error(self):
        """Test execute_safe handles validation errors."""
        tool = CodeAnalyzerTool()
        result = tool.execute_safe()  # Missing required parameter

        assert isinstance(result, ToolResult)
        assert result.success is False
        assert result.error is not None

    def test_anthropic_schema_generation(self):
        """Test Anthropic schema generation."""
        tool = CodeAnalyzerTool()
        schema = tool.to_anthropic_schema()

        assert "name" in schema
        assert schema["name"] == "analyze_code"
        assert "description" in schema
        assert "input_schema" in schema
        assert "properties" in schema["input_schema"]
        assert "code" in schema["input_schema"]["properties"]

    def test_openai_schema_generation(self):
        """Test OpenAI schema generation."""
        tool = CodeAnalyzerTool()
        schema = tool.to_openai_schema()

        assert "type" in schema
        assert schema["type"] == "function"
        assert "function" in schema
        assert "name" in schema["function"]
        assert schema["function"]["name"] == "analyze_code"

    def test_get_stats(self):
        """Test statistics tracking."""
        tool = CodeAnalyzerTool()

        tool.execute_safe(code="pass")
        tool.execute_safe(code="def foo(): pass")

        stats = tool.get_stats()

        assert "name" in stats
        assert stats["name"] == "analyze_code"
        assert "executions" in stats
        assert stats["executions"] == 2

    def test_reset_stats(self):
        """Test statistics reset."""
        tool = CodeAnalyzerTool()

        tool.execute_safe(code="pass")
        stats = tool.get_stats()
        assert stats["executions"] == 1

        tool.reset_stats()
        stats = tool.get_stats()
        assert stats["executions"] == 0


class TestCodeAnalyzerSafety:
    """Test that code analyzer never executes code."""

    @pytest.fixture
    def analyzer(self) -> CodeAnalyzerTool:
        """Create analyzer tool instance."""
        return CodeAnalyzerTool()

    def test_dangerous_code_not_executed(self, analyzer):
        """Test dangerous code is analyzed but not executed."""
        code = '''
import os
os.system("rm -rf /")  # This should NEVER execute
'''
        # This should analyze successfully without executing
        result = analyzer.execute(code=code)

        assert result.success is True
        assert result.metadata["syntax_valid"] is True
        # Code is analyzed but never executed

    def test_infinite_loop_not_executed(self, analyzer):
        """Test infinite loop code is analyzed but not executed."""
        code = """
while True:
    pass
"""
        # Should complete instantly (not hang)
        result = analyzer.execute(code=code)

        assert result.success is True
        assert result.metadata["syntax_valid"] is True

    def test_exception_code_not_executed(self, analyzer):
        """Test code that would raise exceptions is safe to analyze."""
        code = """
def will_raise():
    raise Exception("This should not execute")

will_raise()
"""
        # Should analyze successfully without executing
        result = analyzer.execute(code=code)

        assert result.success is True
        assert result.metadata["syntax_valid"] is True
        assert result.metadata["num_functions"] == 1


class TestCodeAnalyzerComplexScenarios:
    """Test complex code analysis scenarios."""

    @pytest.fixture
    def analyzer(self) -> CodeAnalyzerTool:
        """Create analyzer tool instance."""
        return CodeAnalyzerTool()

    def test_real_world_module(self, analyzer):
        """Test analysis of realistic Python module."""
        code = '''
"""
A realistic Python module for demonstration.
"""

import os
import sys
from typing import List, Optional

class DataProcessor:
    """Process data from various sources."""

    def __init__(self, source: str):
        """Initialize processor."""
        self.source = source

    def process(self, data: List[str]) -> List[str]:
        """Process the data."""
        return [item.strip() for item in data]

    def validate(self, item: str) -> bool:
        """Validate a single item."""
        return len(item) > 0

def main():
    """Main entry point."""
    processor = DataProcessor("input.txt")
    data = ["hello", "world"]
    result = processor.process(data)
    print(result)

if __name__ == "__main__":
    main()
'''
        result = analyzer.execute(code=code)

        assert result.success is True
        assert result.metadata["syntax_valid"] is True
        assert result.metadata["num_classes"] == 1
        assert result.metadata["num_functions"] == 1  # main (class methods counted separately)
        assert result.metadata["num_imports"] >= 2
        assert result.metadata["has_main_block"] is True
        assert result.metadata["has_docstrings"] is True
