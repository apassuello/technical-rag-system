"""
Unit tests for LangChain tool adapter.

Tests the adapter that converts Phase 1 tools to LangChain format.

Test Categories:
- Adapter creation and initialization
- Schema conversion (Phase 1 → Pydantic)
- Tool execution via adapter
- Error handling
- Bulk conversion utilities

Coverage Target: >95%
"""

import pytest
import sys
from pathlib import Path
from typing import List
from pydantic import BaseModel
import importlib.util

# Direct module loading to bypass components.__init__.py
project_root = Path(__file__).parents[4]
src_path = project_root / "src"

def load_module_from_path(module_name, file_path):
    """Load a module from file path without triggering package __init__."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Load required modules directly
adapter_path = src_path / "components/query_processors/agents/langchain_adapter.py"
base_tool_path = src_path / "components/query_processors/tools/base_tool.py"
models_path = src_path / "components/query_processors/tools/models.py"
calc_path = src_path / "components/query_processors/tools/implementations/calculator_tool.py"
code_path = src_path / "components/query_processors/tools/implementations/code_analyzer_tool.py"

# Load modules
models_module = load_module_from_path("test_models", models_path)
base_tool_module = load_module_from_path("test_base_tool", base_tool_path)
adapter_module = load_module_from_path("test_adapter", adapter_path)
calc_module = load_module_from_path("test_calculator", calc_path)
code_module = load_module_from_path("test_code_analyzer", code_path)

# Import what we need
PhaseOneToolAdapter = adapter_module.PhaseOneToolAdapter
convert_tools_to_langchain = adapter_module.convert_tools_to_langchain
_map_parameter_type = adapter_module._map_parameter_type
BaseTool = base_tool_module.BaseTool
ToolParameter = models_module.ToolParameter
ToolParameterType = models_module.ToolParameterType
ToolResult = models_module.ToolResult
CalculatorTool = calc_module.CalculatorTool
CodeAnalyzerTool = code_module.CodeAnalyzerTool


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def calculator_tool():
    """Calculator tool instance."""
    return CalculatorTool()


@pytest.fixture
def code_analyzer_tool():
    """Code analyzer tool instance."""
    return CodeAnalyzerTool()


@pytest.fixture
def mock_tool():
    """Mock tool for testing."""
    class MockTool(BaseTool):
        @property
        def name(self) -> str:
            return "mock_tool"

        @property
        def description(self) -> str:
            return "A mock tool for testing"

        def get_parameters(self) -> List[ToolParameter]:
            return [
                ToolParameter(
                    name="input_text",
                    type=ToolParameterType.STRING,
                    description="Input text",
                    required=True
                ),
                ToolParameter(
                    name="count",
                    type=ToolParameterType.INTEGER,
                    description="Count parameter",
                    required=False
                )
            ]

        def execute(self, **kwargs) -> ToolResult:
            return ToolResult(
                success=True,
                content=f"Processed: {kwargs.get('input_text', '')}"
            )

    return MockTool()


# =============================================================================
# Adapter Creation Tests
# =============================================================================

def test_adapter_from_phase1_tool_calculator(calculator_tool):
    """Test adapter creation from calculator tool."""
    adapter = PhaseOneToolAdapter.from_phase1_tool(calculator_tool)

    assert adapter.name == "calculator"
    assert "mathematical" in adapter.description.lower()
    assert adapter.phase1_tool is calculator_tool
    assert adapter.args_schema is not None


def test_adapter_from_phase1_tool_code_analyzer(code_analyzer_tool):
    """Test adapter creation from code analyzer tool."""
    adapter = PhaseOneToolAdapter.from_phase1_tool(code_analyzer_tool)

    assert adapter.name == "code_analyzer"
    assert "code" in adapter.description.lower()
    assert adapter.phase1_tool is code_analyzer_tool
    assert adapter.args_schema is not None


def test_adapter_preserves_tool_name(mock_tool):
    """Test adapter preserves tool name."""
    adapter = PhaseOneToolAdapter.from_phase1_tool(mock_tool)
    assert adapter.name == mock_tool.name


def test_adapter_preserves_tool_description(mock_tool):
    """Test adapter preserves tool description."""
    adapter = PhaseOneToolAdapter.from_phase1_tool(mock_tool)
    assert adapter.description == mock_tool.description


# =============================================================================
# Schema Conversion Tests
# =============================================================================

def test_pydantic_schema_creation(calculator_tool):
    """Test Pydantic schema is created correctly."""
    schema = PhaseOneToolAdapter._create_pydantic_schema(calculator_tool)

    assert issubclass(schema, BaseModel)
    assert "expression" in schema.__fields__


def test_pydantic_schema_required_fields(mock_tool):
    """Test required fields are marked correctly in schema."""
    schema = PhaseOneToolAdapter._create_pydantic_schema(mock_tool)

    # Check required field
    assert "input_text" in schema.__fields__
    assert schema.__fields__["input_text"].is_required()


def test_pydantic_schema_optional_fields(mock_tool):
    """Test optional fields are marked correctly in schema."""
    schema = PhaseOneToolAdapter._create_pydantic_schema(mock_tool)

    # Check optional field
    assert "count" in schema.__fields__
    assert not schema.__fields__["count"].is_required()


def test_pydantic_schema_field_descriptions(mock_tool):
    """Test field descriptions are preserved."""
    schema = PhaseOneToolAdapter._create_pydantic_schema(mock_tool)

    input_field = schema.__fields__["input_text"]
    assert input_field.field_info.description == "Input text"


def test_parameter_type_mapping_string():
    """Test STRING type mapping."""
    result = _map_parameter_type(ToolParameterType.STRING)
    assert result == str


def test_parameter_type_mapping_integer():
    """Test INTEGER type mapping."""
    result = _map_parameter_type(ToolParameterType.INTEGER)
    assert result == int


def test_parameter_type_mapping_float():
    """Test FLOAT type mapping."""
    result = _map_parameter_type(ToolParameterType.FLOAT)
    assert result == float


def test_parameter_type_mapping_boolean():
    """Test BOOLEAN type mapping."""
    result = _map_parameter_type(ToolParameterType.BOOLEAN)
    assert result == bool


def test_parameter_type_mapping_array():
    """Test ARRAY type mapping."""
    result = _map_parameter_type(ToolParameterType.ARRAY)
    assert result == list


def test_parameter_type_mapping_object():
    """Test OBJECT type mapping."""
    result = _map_parameter_type(ToolParameterType.OBJECT)
    assert result == dict


# =============================================================================
# Execution Tests
# =============================================================================

def test_adapter_run_success(calculator_tool):
    """Test successful tool execution via adapter."""
    adapter = PhaseOneToolAdapter.from_phase1_tool(calculator_tool)

    result = adapter._run(expression="2 + 2")

    assert result == "4"


def test_adapter_run_with_complex_expression(calculator_tool):
    """Test adapter with complex expression."""
    adapter = PhaseOneToolAdapter.from_phase1_tool(calculator_tool)

    result = adapter._run(expression="25 * 47 + 100")

    assert result == "1275"


def test_adapter_run_with_error(calculator_tool):
    """Test adapter returns error string on failure."""
    adapter = PhaseOneToolAdapter.from_phase1_tool(calculator_tool)

    result = adapter._run(expression="1 / 0")

    assert "error" in result.lower()
    assert "zero" in result.lower()


def test_adapter_run_with_invalid_params(mock_tool):
    """Test adapter handles invalid parameters."""
    adapter = PhaseOneToolAdapter.from_phase1_tool(mock_tool)

    # Missing required parameter
    result = adapter._run()

    assert "error" in result.lower() or "missing" in result.lower()


def test_adapter_async_run_falls_back_to_sync(calculator_tool):
    """Test async execution falls back to sync."""
    import asyncio

    adapter = PhaseOneToolAdapter.from_phase1_tool(calculator_tool)

    async def test_async():
        result = await adapter._arun(expression="2 + 2")
        return result

    result = asyncio.run(test_async())
    assert result == "4"


def test_adapter_logs_execution(calculator_tool, caplog):
    """Test adapter logs tool execution."""
    import logging
    caplog.set_level(logging.DEBUG)

    adapter = PhaseOneToolAdapter.from_phase1_tool(calculator_tool)
    adapter._run(expression="2 + 2")

    assert any("calculator" in record.message.lower() for record in caplog.records)


# =============================================================================
# Bulk Conversion Tests
# =============================================================================

def test_convert_empty_list():
    """Test converting empty tool list."""
    result = convert_tools_to_langchain([])
    assert result == []


def test_convert_single_tool(calculator_tool):
    """Test converting single tool."""
    result = convert_tools_to_langchain([calculator_tool])

    assert len(result) == 1
    assert isinstance(result[0], PhaseOneToolAdapter)
    assert result[0].name == "calculator"


def test_convert_multiple_tools(calculator_tool, code_analyzer_tool):
    """Test converting multiple tools."""
    result = convert_tools_to_langchain([calculator_tool, code_analyzer_tool])

    assert len(result) == 2
    assert all(isinstance(tool, PhaseOneToolAdapter) for tool in result)
    assert {tool.name for tool in result} == {"calculator", "code_analyzer"}


def test_convert_preserves_order(calculator_tool, code_analyzer_tool):
    """Test conversion preserves tool order."""
    result = convert_tools_to_langchain([calculator_tool, code_analyzer_tool])

    assert result[0].name == "calculator"
    assert result[1].name == "code_analyzer"


# =============================================================================
# Error Handling Tests
# =============================================================================

def test_adapter_never_raises_on_execution(calculator_tool):
    """Test adapter never raises exceptions during execution."""
    adapter = PhaseOneToolAdapter.from_phase1_tool(calculator_tool)

    # Try various invalid inputs - should return error strings, not raise
    result1 = adapter._run(expression="")
    assert isinstance(result1, str)

    result2 = adapter._run(expression="invalid syntax!")
    assert isinstance(result2, str)


def test_convert_handles_partial_failures():
    """Test bulk conversion continues on individual failures."""
    class BrokenTool(BaseTool):
        @property
        def name(self) -> str:
            return "broken"

        @property
        def description(self) -> str:
            return "Broken tool"

        def get_parameters(self) -> List[ToolParameter]:
            raise RuntimeError("Broken!")

        def execute(self, **kwargs) -> ToolResult:
            return ToolResult(success=True, content="")

    calculator = CalculatorTool()
    broken = BrokenTool()

    # Should convert calculator, skip broken
    result = convert_tools_to_langchain([calculator, broken])

    assert len(result) >= 1  # At least calculator should convert


# =============================================================================
# Integration Tests
# =============================================================================

def test_adapter_with_real_calculator_expressions(calculator_tool):
    """Test adapter with various calculator expressions."""
    adapter = PhaseOneToolAdapter.from_phase1_tool(calculator_tool)

    test_cases = [
        ("2 + 2", "4"),
        ("10 - 5", "5"),
        ("3 * 4", "12"),
        ("15 / 3", "5"),
        ("2 ** 3", "8")
    ]

    for expression, expected in test_cases:
        result = adapter._run(expression=expression)
        assert expected in result or float(expected) == float(result)


def test_adapter_with_code_analyzer(code_analyzer_tool):
    """Test adapter with code analyzer tool."""
    adapter = PhaseOneToolAdapter.from_phase1_tool(code_analyzer_tool)

    code = "def hello(): return 'world'"
    result = adapter._run(code=code, analysis_type="syntax")

    # Should return some analysis result
    assert isinstance(result, str)
    assert len(result) > 0


# =============================================================================
# Property Tests
# =============================================================================

def test_adapter_config_allows_arbitrary_types():
    """Test adapter Pydantic config allows Phase 1 tools."""
    # This should not raise validation errors
    adapter = PhaseOneToolAdapter.from_phase1_tool(CalculatorTool())
    assert adapter.phase1_tool is not None


def test_adapter_has_correct_langchain_interface(calculator_tool):
    """Test adapter implements LangChain BaseTool interface."""
    adapter = PhaseOneToolAdapter.from_phase1_tool(calculator_tool)

    # Check LangChain BaseTool methods exist
    assert hasattr(adapter, '_run')
    assert hasattr(adapter, '_arun')
    assert hasattr(adapter, 'name')
    assert hasattr(adapter, 'description')
    assert hasattr(adapter, 'args_schema')


# =============================================================================
# Edge Cases
# =============================================================================

def test_adapter_with_tool_returning_none():
    """Test adapter handles tool returning None."""
    class NoneReturningTool(BaseTool):
        @property
        def name(self) -> str:
            return "none_tool"

        @property
        def description(self) -> str:
            return "Returns None"

        def get_parameters(self) -> List[ToolParameter]:
            return []

        def execute(self, **kwargs) -> ToolResult:
            return ToolResult(success=True, content=None)

    adapter = PhaseOneToolAdapter.from_phase1_tool(NoneReturningTool())
    result = adapter._run()

    # Should convert None to string
    assert isinstance(result, str)


def test_adapter_with_empty_tool_description():
    """Test adapter handles tool with minimal description."""
    class MinimalTool(BaseTool):
        @property
        def name(self) -> str:
            return "minimal"

        @property
        def description(self) -> str:
            return ""

        def get_parameters(self) -> List[ToolParameter]:
            return []

        def execute(self, **kwargs) -> ToolResult:
            return ToolResult(success=True, content="OK")

    adapter = PhaseOneToolAdapter.from_phase1_tool(MinimalTool())
    assert adapter.description == ""
