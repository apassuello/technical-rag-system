#!/usr/bin/env python
"""
Standalone Phase 1 validation script.

Tests Phase 1 implementation without importing the full codebase.
This avoids dependency issues from the existing codebase.
"""

import sys
import os
from pathlib import Path

# Add tools directory directly to path (bypass package imports)
project_root = Path(__file__).parent.parent.parent
tools_path = project_root / "src" / "components" / "query_processors" / "tools"
sys.path.insert(0, str(tools_path))
sys.path.insert(0, str(project_root / "src"))

# Direct module imports (bypass package __init__ files)
import importlib.util

def import_module_from_file(module_name, file_path):
    """Import a module directly from file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Import Phase 1 modules directly
models = import_module_from_file("models", tools_path / "models.py")
base_tool = import_module_from_file("base_tool", tools_path / "base_tool.py")
tool_registry = import_module_from_file("tool_registry", tools_path / "tool_registry.py")
calculator_tool = import_module_from_file("calculator_tool", tools_path / "implementations" / "calculator_tool.py")
code_analyzer_tool = import_module_from_file("code_analyzer_tool", tools_path / "implementations" / "code_analyzer_tool.py")

# Extract classes
ToolParameterType = models.ToolParameterType
ToolParameter = models.ToolParameter
ToolResult = models.ToolResult
ToolCall = models.ToolCall
ToolExecution = models.ToolExecution
ToolConversation = models.ToolConversation
BaseTool = base_tool.BaseTool
ToolRegistry = tool_registry.ToolRegistry
CalculatorTool = calculator_tool.CalculatorTool
CodeAnalyzerTool = code_analyzer_tool.CodeAnalyzerTool


def test_data_models():
    """Test data models."""
    print("Testing data models...")

    # ToolParameter
    param = ToolParameter(
        name="test",
        type=ToolParameterType.STRING,
        description="Test parameter",
        required=True
    )
    schema = param.to_json_schema()
    assert schema["type"] == "string"
    assert schema["description"] == "Test parameter"

    # ToolResult - success
    result = ToolResult(success=True, content="Test", execution_time=0.1)
    assert result.success is True
    assert result.content == "Test"

    # ToolResult - failure
    result = ToolResult(success=False, error="Test error", execution_time=0.1)
    assert result.success is False
    assert result.error == "Test error"

    print("✓ Data models working")


def test_calculator_tool():
    """Test CalculatorTool."""
    print("\nTesting CalculatorTool...")

    calc = CalculatorTool()

    # Test name and description
    assert calc.name == "calculator"
    assert len(calc.description) > 10

    # Test parameters
    params = calc.get_parameters()
    assert len(params) == 1
    assert params[0].name == "expression"

    # Test schema generation
    anthropic_schema = calc.to_anthropic_schema()
    assert anthropic_schema["name"] == "calculator"
    assert "input_schema" in anthropic_schema

    openai_schema = calc.to_openai_schema()
    assert openai_schema["type"] == "function"
    assert openai_schema["function"]["name"] == "calculator"

    # Test execution - success cases
    result = calc.execute(expression="2 + 2")
    assert result.success is True
    assert result.content == "4"

    result = calc.execute(expression="25 * 47")
    assert result.success is True
    assert result.content == "1175"

    result = calc.execute(expression="10 ** 2")
    assert result.success is True
    assert result.content == "100"

    # Test execution - error cases
    result = calc.execute(expression="1 / 0")
    assert result.success is False
    assert "division by zero" in result.error.lower()

    result = calc.execute(expression="import os")
    assert result.success is False

    # Test execute_safe wrapper
    result = calc.execute_safe(expression="5 * 5")
    assert result.success is True
    assert result.content == "25"
    assert result.execution_time > 0

    # Test stats tracking
    stats = calc.get_stats()
    assert stats["executions"] > 0
    assert stats["name"] == "calculator"

    print("✓ CalculatorTool working")


def test_code_analyzer_tool():
    """Test CodeAnalyzerTool."""
    print("\nTesting CodeAnalyzerTool...")

    analyzer = CodeAnalyzerTool()

    # Test name
    assert analyzer.name == "code_analyzer"

    # Test execution - valid code
    code = """
def hello(name):
    return f"Hello, {name}!"

class Greeter:
    def greet(self):
        pass
"""
    result = analyzer.execute(code=code, language="python")
    assert result.success is True
    assert "hello" in result.content.lower()
    assert "greeter" in result.content.lower()

    # Test execution - syntax error
    result = analyzer.execute(code="def broken(", language="python")
    assert result.success is False
    assert "syntax" in result.error.lower()

    print("✓ CodeAnalyzerTool working")


def test_tool_registry():
    """Test ToolRegistry."""
    print("\nTesting ToolRegistry...")

    registry = ToolRegistry()
    calc = CalculatorTool()
    analyzer = CodeAnalyzerTool()

    # Test registration
    registry.register(calc)
    registry.register(analyzer)

    assert len(registry) == 2
    assert "calculator" in registry
    assert "code_analyzer" in registry

    # Test tool retrieval
    tool = registry.get_tool("calculator")
    assert tool is not None
    assert tool.name == "calculator"

    # Test tool names
    names = registry.get_tool_names()
    assert "calculator" in names
    assert "code_analyzer" in names

    # Test schema generation
    anthropic_schemas = registry.get_anthropic_schemas()
    assert len(anthropic_schemas) == 2
    assert anthropic_schemas[0]["name"] in ["calculator", "code_analyzer"]

    openai_schemas = registry.get_openai_schemas()
    assert len(openai_schemas) == 2
    assert openai_schemas[0]["type"] == "function"

    # Test tool execution via registry
    result = registry.execute_tool("calculator", expression="10 + 20")
    assert result.success is True
    assert result.content == "30"

    # Test unknown tool
    result = registry.execute_tool("nonexistent", param="value")
    assert result.success is False
    assert "not found" in result.error.lower()

    # Test registry stats
    stats = registry.get_registry_stats()
    assert stats["total_tools"] == 2
    assert stats["total_executions"] > 0

    print("✓ ToolRegistry working")


def test_thread_safety():
    """Test thread safety of ToolRegistry."""
    print("\nTesting thread safety...")

    import threading

    registry = ToolRegistry()
    calc = CalculatorTool()
    registry.register(calc)

    results = []
    errors = []

    def worker(thread_id):
        try:
            for i in range(10):
                result = registry.execute_tool("calculator", expression=f"{thread_id} * {i}")
                results.append(result)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Thread safety errors: {errors}"
    assert len(results) == 50  # 5 threads * 10 iterations

    print("✓ Thread safety working")


def test_error_handling():
    """Test that tools never raise exceptions."""
    print("\nTesting error handling...")

    calc = CalculatorTool()

    # Various error conditions - all should return ToolResult with error
    test_cases = [
        {"expression": ""},  # Empty
        {"expression": "invalid python code"},  # Invalid
        {"expression": "1 / 0"},  # Division by zero
        {"expression": "__import__('os')"},  # Attempted import
        {},  # Missing required parameter
    ]

    for i, kwargs in enumerate(test_cases):
        try:
            result = calc.execute_safe(**kwargs)
            assert isinstance(result, ToolResult), f"Test {i}: Must return ToolResult"
            assert result.success is False, f"Test {i}: Should fail"
            assert result.error is not None, f"Test {i}: Must have error message"
        except Exception as e:
            raise AssertionError(f"Test {i}: Tool raised exception: {e}")

    print("✓ Error handling working (no exceptions)")


def main():
    """Run all validation tests."""
    print("=" * 70)
    print("Phase 1 Standalone Validation")
    print("=" * 70)

    try:
        test_data_models()
        test_calculator_tool()
        test_code_analyzer_tool()
        test_tool_registry()
        test_thread_safety()
        test_error_handling()

        print("\n" + "=" * 70)
        print("✅ ALL PHASE 1 VALIDATION TESTS PASSED")
        print("=" * 70)
        print(f"\nValidated components:")
        print("  • Data models (ToolResult, ToolParameter, etc.)")
        print("  • BaseTool abstract interface")
        print("  • ToolRegistry (thread-safe)")
        print("  • CalculatorTool implementation")
        print("  • CodeAnalyzerTool implementation")
        print("  • Schema generation (Anthropic + OpenAI)")
        print("  • Error handling (no exceptions)")
        print("  • Thread safety")

        return 0

    except Exception as e:
        print("\n" + "=" * 70)
        print(f"❌ VALIDATION FAILED: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
