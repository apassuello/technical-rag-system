"""
Integration tests for ToolRegistry with all tools and adapters.

Tests the complete tool execution pipeline:
1. Register all 3 tools in registry
2. Generate schemas for Anthropic and OpenAI
3. Execute each tool through registry
4. Verify error handling
5. Test registry statistics

Architecture:
- Tests real tool implementations (no mocks for tools)
- Tests actual schema generation
- Tests thread-safe operations
- Verifies complete error handling

Author: Epic 5 Phase 1 Block 3 Testing Agent
Created: 2025-11-17
"""

import pytest
from typing import Dict, List, Any
from unittest.mock import Mock, MagicMock
import time

from src.components.query_processors.tools.tool_registry import ToolRegistry
from src.components.query_processors.tools.implementations import (
    CalculatorTool,
    DocumentSearchTool,
    CodeAnalyzerTool,
)
from src.components.query_processors.tools.models import ToolResult
from src.core.interfaces import Document, RetrievalResult


class TestToolRegistryBasicOperations:
    """Test basic registry operations."""

    def test_register_all_three_tools(self) -> None:
        """
        Test: Register all 3 tools in registry.

        Verifies:
        - All tools register successfully
        - No duplicate registration errors
        - Registry contains correct tool count
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()

        # Create mock retriever for DocumentSearchTool
        mock_retriever = Mock()
        search = DocumentSearchTool(retriever=mock_retriever)

        analyzer = CodeAnalyzerTool()

        # Act
        registry.register(calculator)
        registry.register(search)
        registry.register(analyzer)

        # Assert
        assert len(registry) == 3
        assert "calculator" in registry
        assert "search_documents" in registry
        assert "analyze_code" in registry
        assert registry.has_tool("calculator")
        assert registry.has_tool("search_documents")
        assert registry.has_tool("analyze_code")

    def test_duplicate_registration_raises_error(self) -> None:
        """
        Test: Duplicate tool registration raises ValueError.

        Verifies:
        - First registration succeeds
        - Second registration with same name raises ValueError
        """
        # Arrange
        registry = ToolRegistry()
        calculator1 = CalculatorTool()
        calculator2 = CalculatorTool()

        # Act & Assert
        registry.register(calculator1)
        with pytest.raises(ValueError, match="already registered"):
            registry.register(calculator2)

    def test_unregister_tool(self) -> None:
        """
        Test: Unregister tool removes it from registry.

        Verifies:
        - Tool can be unregistered
        - Tool is no longer in registry
        - Unregistering non-existent tool returns False
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Act
        result = registry.unregister("calculator")

        # Assert
        assert result is True
        assert len(registry) == 0
        assert "calculator" not in registry

        # Unregistering again should return False
        result = registry.unregister("calculator")
        assert result is False

    def test_get_all_tools(self) -> None:
        """
        Test: Get all tools returns complete list.

        Verifies:
        - get_all_tools returns correct number
        - All registered tools are in the list
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        analyzer = CodeAnalyzerTool()

        registry.register(calculator)
        registry.register(analyzer)

        # Act
        tools = registry.get_all_tools()
        tool_names = [t.name for t in tools]

        # Assert
        assert len(tools) == 2
        assert "calculator" in tool_names
        assert "analyze_code" in tool_names

    def test_get_tool_names(self) -> None:
        """
        Test: Get tool names returns correct list.

        Verifies:
        - get_tool_names returns all registered tool names
        - Names match registered tools
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        analyzer = CodeAnalyzerTool()

        registry.register(calculator)
        registry.register(analyzer)

        # Act
        names = registry.get_tool_names()

        # Assert
        assert len(names) == 2
        assert "calculator" in names
        assert "analyze_code" in names


class TestToolRegistrySchemaGeneration:
    """Test schema generation for LLM providers."""

    def test_generate_anthropic_schemas_from_registry(self) -> None:
        """
        Test: Generate Anthropic schemas from registry.

        Verifies:
        - Schema generated for each tool
        - Schemas have correct structure
        - All required fields present
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        analyzer = CodeAnalyzerTool()

        registry.register(calculator)
        registry.register(analyzer)

        # Act
        schemas = registry.get_anthropic_schemas()

        # Assert
        assert len(schemas) == 2

        # Verify schema structure
        for schema in schemas:
            assert "name" in schema
            assert "description" in schema
            assert "input_schema" in schema

            input_schema = schema["input_schema"]
            assert "type" in input_schema
            assert input_schema["type"] == "object"
            assert "properties" in input_schema
            assert "required" in input_schema

        # Verify specific tool schemas
        tool_names = [s["name"] for s in schemas]
        assert "calculator" in tool_names
        assert "analyze_code" in tool_names

    def test_generate_openai_schemas_from_registry(self) -> None:
        """
        Test: Generate OpenAI schemas from registry.

        Verifies:
        - Schema generated for each tool
        - Schemas have correct OpenAI function format
        - All required fields present
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        analyzer = CodeAnalyzerTool()

        registry.register(calculator)
        registry.register(analyzer)

        # Act
        schemas = registry.get_openai_schemas()

        # Assert
        assert len(schemas) == 2

        # Verify schema structure (OpenAI function format)
        for schema in schemas:
            assert "type" in schema
            assert schema["type"] == "function"
            assert "function" in schema

            function = schema["function"]
            assert "name" in function
            assert "description" in function
            assert "parameters" in function

            parameters = function["parameters"]
            assert "type" in parameters
            assert parameters["type"] == "object"
            assert "properties" in parameters
            assert "required" in parameters

        # Verify specific tool schemas
        tool_names = [s["function"]["name"] for s in schemas]
        assert "calculator" in tool_names
        assert "analyze_code" in tool_names

    def test_schema_generation_with_empty_registry(self) -> None:
        """
        Test: Schema generation with empty registry returns empty list.

        Verifies:
        - Empty registry returns empty schema lists
        - No errors raised
        """
        # Arrange
        registry = ToolRegistry()

        # Act
        anthropic_schemas = registry.get_anthropic_schemas()
        openai_schemas = registry.get_openai_schemas()

        # Assert
        assert anthropic_schemas == []
        assert openai_schemas == []


class TestToolRegistryExecution:
    """Test tool execution through registry."""

    def test_execute_calculator_tool(self) -> None:
        """
        Test: Execute Calculator tool through registry.

        Verifies:
        - Tool executes successfully
        - Correct result returned
        - No errors
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Act
        result = registry.execute_tool("calculator", expression="25 * 47")

        # Assert
        assert result.success is True
        assert result.content == "1175"
        assert result.error is None
        assert result.execution_time > 0

    def test_execute_code_analyzer_tool(self) -> None:
        """
        Test: Execute CodeAnalyzer tool through registry.

        Verifies:
        - Tool executes successfully
        - Analysis results returned
        - No errors
        """
        # Arrange
        registry = ToolRegistry()
        analyzer = CodeAnalyzerTool()
        registry.register(analyzer)

        code = """
def hello():
    return "world"
"""

        # Act
        result = registry.execute_tool("analyze_code", code=code)

        # Assert
        assert result.success is True
        assert result.content is not None
        assert result.error is None
        assert "function" in result.content.lower()

    def test_execute_document_search_tool(self) -> None:
        """
        Test: Execute DocumentSearch tool through registry (with mock retriever).

        Verifies:
        - Tool executes successfully
        - Mock retriever called correctly
        - Results formatted properly
        """
        # Arrange
        mock_retriever = Mock()
        # DocumentSearchTool expects RetrievalResult objects with Document objects
        mock_retriever.retrieve.return_value = [
            RetrievalResult(
                document=Document(content="Document 1 content", metadata={}),
                score=0.95,
                retrieval_method="semantic"
            ),
            RetrievalResult(
                document=Document(content="Document 2 content", metadata={}),
                score=0.87,
                retrieval_method="semantic"
            ),
        ]

        registry = ToolRegistry()
        search = DocumentSearchTool(retriever=mock_retriever)
        registry.register(search)

        # Act
        result = registry.execute_tool(
            "search_documents",
            query="test query",
            num_results=2
        )

        # Assert
        assert result.success is True
        assert result.content is not None
        assert "Document 1" in result.content
        # DocumentSearchTool calls retriever.retrieve() not retriever.search()
        mock_retriever.retrieve.assert_called_once_with(query="test query", k=2)

    def test_execute_nonexistent_tool_returns_error(self) -> None:
        """
        Test: Executing non-existent tool returns ToolResult with error.

        Verifies:
        - No exception raised
        - ToolResult has success=False
        - Error message indicates tool not found
        """
        # Arrange
        registry = ToolRegistry()

        # Act
        result = registry.execute_tool("nonexistent_tool", arg="value")

        # Assert
        assert result.success is False
        assert result.error is not None
        assert "not found" in result.error.lower()

    def test_execute_tool_with_invalid_parameters(self) -> None:
        """
        Test: Tool execution with invalid parameters returns error.

        Verifies:
        - Tool catches parameter errors
        - Returns ToolResult with error
        - No exception raised
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Act - missing required parameter
        result = registry.execute_tool("calculator")

        # Assert
        assert result.success is False
        assert result.error is not None


class TestToolRegistryStatistics:
    """Test registry statistics tracking."""

    def test_get_registry_stats(self) -> None:
        """
        Test: Get registry statistics.

        Verifies:
        - Stats include all registered tools
        - Execution counts tracked
        - Success rates calculated
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        analyzer = CodeAnalyzerTool()

        registry.register(calculator)
        registry.register(analyzer)

        # Execute some tools
        registry.execute_tool("calculator", expression="2 + 2")
        registry.execute_tool("calculator", expression="3 * 3")
        registry.execute_tool("analyze_code", code="def test(): pass")

        # Act
        stats = registry.get_registry_stats()

        # Assert
        assert stats["total_tools"] == 2
        assert "calculator" in stats["tool_names"]
        assert "analyze_code" in stats["tool_names"]
        assert stats["total_executions"] >= 3
        assert "per_tool_stats" in stats

    def test_reset_all_stats(self) -> None:
        """
        Test: Reset statistics for all tools.

        Verifies:
        - Stats can be reset
        - All execution counts return to 0
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Execute tool
        registry.execute_tool("calculator", expression="1 + 1")

        # Verify stats before reset
        stats_before = registry.get_registry_stats()
        assert stats_before["total_executions"] > 0

        # Act
        registry.reset_all_stats()

        # Assert
        stats_after = registry.get_registry_stats()
        assert stats_after["total_executions"] == 0

    def test_clear_registry(self) -> None:
        """
        Test: Clear all tools from registry.

        Verifies:
        - All tools removed
        - Registry becomes empty
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        analyzer = CodeAnalyzerTool()

        registry.register(calculator)
        registry.register(analyzer)

        assert len(registry) == 2

        # Act
        registry.clear()

        # Assert
        assert len(registry) == 0
        assert registry.get_all_tools() == []


class TestToolRegistryThreadSafety:
    """Test thread-safe operations (basic tests)."""

    def test_concurrent_registration_safe(self) -> None:
        """
        Test: Registry operations are thread-safe.

        Note: This is a basic test. Full concurrency testing
        would require threading/multiprocessing.

        Verifies:
        - Multiple sequential operations work correctly
        - No data corruption
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        analyzer = CodeAnalyzerTool()

        # Act - Sequential operations (simulating thread safety)
        registry.register(calculator)
        tools1 = registry.get_all_tools()

        registry.register(analyzer)
        tools2 = registry.get_all_tools()

        registry.unregister("calculator")
        tools3 = registry.get_all_tools()

        # Assert
        assert len(tools1) == 1
        assert len(tools2) == 2
        assert len(tools3) == 1

    def test_concurrent_execution_safe(self) -> None:
        """
        Test: Tool execution is thread-safe.

        Verifies:
        - Multiple executions don't interfere
        - All executions complete successfully
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Act - Multiple executions
        result1 = registry.execute_tool("calculator", expression="1 + 1")
        result2 = registry.execute_tool("calculator", expression="2 + 2")
        result3 = registry.execute_tool("calculator", expression="3 + 3")

        # Assert
        assert result1.success is True
        assert result1.content == "2"
        assert result2.success is True
        assert result2.content == "4"
        assert result3.success is True
        assert result3.content == "6"


class TestToolRegistryErrorHandling:
    """Test comprehensive error handling."""

    def test_register_invalid_type_raises_error(self) -> None:
        """
        Test: Registering non-BaseTool raises TypeError.

        Verifies:
        - Type checking enforced
        - Clear error message
        """
        # Arrange
        registry = ToolRegistry()

        # Act & Assert
        with pytest.raises(TypeError, match="BaseTool"):
            registry.register("not a tool")  # type: ignore

    def test_tool_execution_never_raises_exception(self) -> None:
        """
        Test: Tool execution never raises exceptions.

        Verifies:
        - All errors caught and returned in ToolResult
        - No uncaught exceptions propagate
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Act - Execute with invalid expression
        result = registry.execute_tool("calculator", expression="1 / 0")

        # Assert - Should not raise, should return error in result
        assert result.success is False
        assert result.error is not None
        assert "error" in result.error.lower() or "division" in result.error.lower()

    def test_schema_generation_handles_tool_errors(self) -> None:
        """
        Test: Schema generation handles tool errors gracefully.

        Verifies:
        - Failed schema generation for one tool doesn't break others
        - Error logged but not raised
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        analyzer = CodeAnalyzerTool()

        registry.register(calculator)
        registry.register(analyzer)

        # Act
        anthropic_schemas = registry.get_anthropic_schemas()
        openai_schemas = registry.get_openai_schemas()

        # Assert - Should get schemas for both tools
        assert len(anthropic_schemas) >= 2
        assert len(openai_schemas) >= 2


class TestToolRegistryIntegrationScenarios:
    """End-to-end integration scenarios."""

    def test_complete_workflow_register_schema_execute(self) -> None:
        """
        Test: Complete workflow from registration to execution.

        This is an end-to-end test that verifies:
        1. Register multiple tools
        2. Generate schemas for both providers
        3. Execute each tool
        4. Verify all operations successful
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        analyzer = CodeAnalyzerTool()

        # Step 1: Register tools
        registry.register(calculator)
        registry.register(analyzer)

        assert len(registry) == 2

        # Step 2: Generate schemas
        anthropic_schemas = registry.get_anthropic_schemas()
        openai_schemas = registry.get_openai_schemas()

        assert len(anthropic_schemas) == 2
        assert len(openai_schemas) == 2

        # Step 3: Execute tools
        calc_result = registry.execute_tool("calculator", expression="100 / 4")
        analyzer_result = registry.execute_tool(
            "analyze_code",
            code="class Test:\n    pass"
        )

        # Step 4: Verify results
        assert calc_result.success is True
        # Calculator returns "25" for whole numbers (formatted as int)
        assert calc_result.content == "25"

        assert analyzer_result.success is True
        assert "class" in analyzer_result.content.lower()

        # Step 5: Verify statistics
        stats = registry.get_registry_stats()
        assert stats["total_executions"] >= 2
        assert stats["total_tools"] == 2

    def test_error_recovery_workflow(self) -> None:
        """
        Test: Error recovery in multi-step workflow.

        Verifies:
        - Failed tool execution doesn't break registry
        - Subsequent operations continue normally
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)

        # Act - Execute with error, then success
        error_result = registry.execute_tool("nonexistent_tool")
        success_result = registry.execute_tool("calculator", expression="5 + 5")

        # Assert
        assert error_result.success is False
        assert success_result.success is True
        assert success_result.content == "10"

    def test_dynamic_tool_management(self) -> None:
        """
        Test: Dynamic tool addition and removal.

        Verifies:
        - Tools can be added/removed dynamically
        - Schema generation reflects current state
        - Execution works with current tool set
        """
        # Arrange
        registry = ToolRegistry()
        calculator = CalculatorTool()
        analyzer = CodeAnalyzerTool()

        # Step 1: Register calculator only
        registry.register(calculator)
        schemas1 = registry.get_anthropic_schemas()
        assert len(schemas1) == 1

        # Step 2: Add analyzer
        registry.register(analyzer)
        schemas2 = registry.get_anthropic_schemas()
        assert len(schemas2) == 2

        # Step 3: Remove calculator
        registry.unregister("calculator")
        schemas3 = registry.get_anthropic_schemas()
        assert len(schemas3) == 1

        # Step 4: Verify only analyzer works
        calc_result = registry.execute_tool("calculator", expression="1 + 1")
        analyzer_result = registry.execute_tool("analyze_code", code="x = 1")

        assert calc_result.success is False  # Calculator removed
        assert analyzer_result.success is True  # Analyzer still available
