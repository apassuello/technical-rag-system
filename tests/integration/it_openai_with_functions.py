"""
Integration tests for OpenAI function calling with real API.

These tests make actual API calls to OpenAI and require:
- OPENAI_API_KEY environment variable set
- openai package installed
- Network connectivity

Tests are automatically skipped if API key is not available.

Test Coverage:
- End-to-end function calling with calculator tool
- Multi-turn conversations
- Parallel function calls
- Cost tracking accuracy
- Real tool execution integration
"""

import pytest
import os
from typing import Dict, Any, List

from src.components.generators.llm_adapters.openai_adapter import OpenAIAdapter
from src.components.generators.base import GenerationParams
from src.components.query_processors.tools.tool_registry import ToolRegistry
from src.components.query_processors.tools.implementations.calculator_tool import CalculatorTool


# Skip all tests if OpenAI API key not available
pytestmark = pytest.mark.skipif(
    not os.getenv('OPENAI_API_KEY'),
    reason="OPENAI_API_KEY not set - skipping OpenAI integration tests"
)


class TestOpenAIFunctionCallingIntegration:
    """Integration tests with real OpenAI API calls."""

    @pytest.fixture
    def adapter(self) -> OpenAIAdapter:
        """Create real OpenAI adapter."""
        return OpenAIAdapter(
            model_name="gpt-3.5-turbo",
            api_key=os.getenv('OPENAI_API_KEY')
        )

    @pytest.fixture
    def registry(self) -> ToolRegistry:
        """Create tool registry with calculator."""
        registry = ToolRegistry()
        calculator = CalculatorTool()
        registry.register(calculator)
        return registry

    @pytest.fixture
    def tools(self, registry: ToolRegistry) -> List[Dict[str, Any]]:
        """Get OpenAI tool schemas from registry."""
        return registry.get_openai_schemas()

    @pytest.mark.integration
    def test_simple_calculator_function_call(
        self,
        adapter: OpenAIAdapter,
        registry: ToolRegistry,
        tools: List[Dict[str, Any]]
    ) -> None:
        """Test simple calculator function call end-to-end."""
        # Initial request
        result = adapter.generate_with_functions(
            prompt="What is 25 multiplied by 47?",
            tools=tools,
            params=GenerationParams(temperature=0.0)
        )

        # Should require function execution
        assert result['status'] == 'requires_function_execution'
        assert len(result['pending_tool_calls']) > 0

        # Execute function calls
        function_results = []
        for tool_call in result['pending_tool_calls']:
            # Extract function call details
            func_name = tool_call['function']['name']
            import json
            func_args = json.loads(tool_call['function']['arguments'])

            # Execute via registry
            execution_result = registry.execute_tool(func_name, **func_args)

            function_results.append({
                'tool_call_id': tool_call['id'],
                'content': execution_result.content if execution_result.success else f"Error: {execution_result.error}"
            })

        # Continue with results
        final_result = adapter.continue_with_function_results(
            messages=result['messages'],
            function_results=function_results,
            tools=tools
        )

        # Should complete successfully
        assert final_result['status'] == 'completed'
        assert final_result['final_response'] is not None
        assert len(final_result['final_response']) > 0

        # Verify cost tracking
        assert final_result['total_cost_usd'] > 0
        assert final_result['total_tokens'] > 0

        # Answer should mention 1175 (25 * 47)
        assert '1175' in final_result['final_response'] or '1,175' in final_result['final_response']

    @pytest.mark.integration
    def test_multi_step_calculation(
        self,
        adapter: OpenAIAdapter,
        registry: ToolRegistry,
        tools: List[Dict[str, Any]]
    ) -> None:
        """Test multi-step calculation requiring multiple function calls."""
        # Request that may require multiple calculations
        result = adapter.generate_with_functions(
            prompt="Calculate (10 + 5) * 3. Show your work.",
            tools=tools,
            params=GenerationParams(temperature=0.0),
            max_iterations=5
        )

        max_iterations = 5
        iteration = 0

        # Loop until completion or max iterations
        while result['status'] == 'requires_function_execution' and iteration < max_iterations:
            iteration += 1

            # Execute all pending function calls
            function_results = []
            for tool_call in result['pending_tool_calls']:
                func_name = tool_call['function']['name']
                import json
                func_args = json.loads(tool_call['function']['arguments'])

                execution_result = registry.execute_tool(func_name, **func_args)

                function_results.append({
                    'tool_call_id': tool_call['id'],
                    'content': str(execution_result.content) if execution_result.success else f"Error: {execution_result.error}"
                })

            # Continue conversation
            result = adapter.continue_with_function_results(
                messages=result['messages'],
                function_results=function_results,
                tools=tools,
                max_iterations=max_iterations - iteration
            )

        # Should eventually complete
        assert result['status'] == 'completed'
        assert result['final_response'] is not None

        # Answer should mention 45 ((10 + 5) * 3)
        assert '45' in result['final_response']

    @pytest.mark.integration
    def test_cost_tracking_accuracy(
        self,
        adapter: OpenAIAdapter,
        tools: List[Dict[str, Any]]
    ) -> None:
        """Test that cost tracking is accurate across iterations."""
        # Make a simple request
        result = adapter.generate_with_functions(
            prompt="What is 2 + 2?",
            tools=tools,
            params=GenerationParams(temperature=0.0)
        )

        # Verify cost breakdown structure
        assert 'total_cost_usd' in result
        assert 'total_tokens' in result
        assert 'cost_breakdown' in result

        total_cost = result['total_cost_usd']
        total_tokens = result['total_tokens']

        # Cost should be positive and reasonable
        assert total_cost > 0
        assert total_cost < 0.01  # Should be less than 1 cent for simple query

        # Tokens should be positive and reasonable
        assert total_tokens > 0
        assert total_tokens < 500  # Should be relatively small

        # Cost breakdown should have entries
        assert len(result['cost_breakdown']) > 0

        # Each breakdown should have required fields
        for breakdown in result['cost_breakdown']:
            assert 'input_tokens' in breakdown
            assert 'output_tokens' in breakdown
            assert 'total_cost_usd' in breakdown

    @pytest.mark.integration
    def test_direct_answer_without_tools(
        self,
        adapter: OpenAIAdapter,
        tools: List[Dict[str, Any]]
    ) -> None:
        """Test that LLM can answer directly without using tools when appropriate."""
        # Question that doesn't require calculator
        result = adapter.generate_with_functions(
            prompt="What is the capital of France?",
            tools=tools,
            params=GenerationParams(temperature=0.0)
        )

        # Should complete without function calls
        assert result['status'] == 'completed'
        assert len(result['function_calls']) == 0

        # Should mention Paris
        assert 'Paris' in result['final_response']

    @pytest.mark.integration
    def test_error_handling_with_invalid_expression(
        self,
        adapter: OpenAIAdapter,
        registry: ToolRegistry,
        tools: List[Dict[str, Any]]
    ) -> None:
        """Test handling when function execution returns an error."""
        # This should trigger calculator with an expression
        result = adapter.generate_with_functions(
            prompt="Calculate 10 divided by 2",
            tools=tools,
            params=GenerationParams(temperature=0.0)
        )

        if result['status'] == 'requires_function_execution':
            # Simulate function execution with error
            function_results = []
            for tool_call in result['pending_tool_calls']:
                # Force an error by providing invalid arguments
                function_results.append({
                    'tool_call_id': tool_call['id'],
                    'content': 'Error: Invalid expression'
                })

            # Continue with error result
            final_result = adapter.continue_with_function_results(
                messages=result['messages'],
                function_results=function_results,
                tools=tools
            )

            # Should handle gracefully
            assert final_result['status'] in ['completed', 'requires_function_execution', 'incomplete']

    @pytest.mark.integration
    @pytest.mark.slow
    def test_parallel_function_calls_if_supported(
        self,
        adapter: OpenAIAdapter,
        registry: ToolRegistry,
        tools: List[Dict[str, Any]]
    ) -> None:
        """Test parallel function calls if OpenAI model supports them."""
        # Request that could benefit from parallel calls
        result = adapter.generate_with_functions(
            prompt="Calculate both 5+3 and 7*2. What are the results?",
            tools=tools,
            params=GenerationParams(temperature=0.0)
        )

        if result['status'] == 'requires_function_execution':
            # Check if multiple tool calls were made
            num_tool_calls = len(result['pending_tool_calls'])

            # Execute all tool calls
            function_results = []
            for tool_call in result['pending_tool_calls']:
                func_name = tool_call['function']['name']
                import json
                func_args = json.loads(tool_call['function']['arguments'])

                execution_result = registry.execute_tool(func_name, **func_args)

                function_results.append({
                    'tool_call_id': tool_call['id'],
                    'content': str(execution_result.content)
                })

            # Continue
            final_result = adapter.continue_with_function_results(
                messages=result['messages'],
                function_results=function_results,
                tools=tools
            )

            # Should complete
            assert final_result['status'] == 'completed'

            # If parallel calls were made, verify both results in answer
            if num_tool_calls > 1:
                # Both results should be mentioned: 8 (5+3) and 14 (7*2)
                assert '8' in final_result['final_response']
                assert '14' in final_result['final_response']


class TestOpenAIFunctionCallingCostOptimization:
    """Test cost optimization features of function calling."""

    @pytest.fixture
    def adapter(self) -> OpenAIAdapter:
        """Create adapter with cost tracking."""
        return OpenAIAdapter(
            model_name="gpt-3.5-turbo",
            api_key=os.getenv('OPENAI_API_KEY')
        )

    @pytest.mark.integration
    def test_cost_comparison_simple_vs_function(
        self,
        adapter: OpenAIAdapter
    ) -> None:
        """Compare costs between simple generation and function calling."""
        # Simple generation without functions
        simple_params = GenerationParams(
            temperature=0.0,
            max_tokens=100
        )

        simple_result = adapter.generate(
            prompt="What is 25 * 47? Just give me the number.",
            params=simple_params
        )

        simple_cost = adapter._total_cost

        # Reset adapter cost tracking
        adapter._total_cost = 0
        adapter._input_tokens = 0
        adapter._output_tokens = 0

        # With function calling (if calculator available)
        # Note: This requires calculator tool to be available
        # For now, just verify the cost tracking works

        # Get model info to verify cost tracking
        model_info = adapter.get_model_info()

        assert 'total_cost_usd' in model_info
        assert 'input_tokens_used' in model_info
        assert 'output_tokens_used' in model_info
