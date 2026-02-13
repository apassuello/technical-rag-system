"""
Integration tests for AnthropicAdapter with real API.

These tests require ANTHROPIC_API_KEY environment variable to be set.
They test real API interactions including:
- Basic generation
- Tool use with multi-turn conversations
- Cost tracking accuracy
- Streaming

Run with: pytest tests/epic5/phase1/integration/test_anthropic_with_tools.py -v
Skip if no API key: pytest tests/epic5/phase1/integration/test_anthropic_with_tools.py -v -m "not requires_api_key"
"""

import pytest
import os
import time
from typing import List, Dict, Any

from src.components.generators.llm_adapters.anthropic_adapter import AnthropicAdapter
from src.components.generators.base import GenerationParams
from src.components.query_processors.tools import BaseTool, ToolParameter, ToolParameterType, ToolResult


# Check if API key is available
HAS_API_KEY = os.getenv('ANTHROPIC_API_KEY') is not None

requires_api_key = pytest.mark.skipif(
    not HAS_API_KEY,
    reason="ANTHROPIC_API_KEY environment variable not set"
)


class CalculatorTool(BaseTool):
    """Simple calculator tool for testing."""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Evaluate mathematical expressions. Use for calculations like '2 + 2', '10 * 5', etc."

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="expression",
                type=ToolParameterType.STRING,
                description="Mathematical expression to evaluate (e.g., '2 + 2', '10 * 5')",
                required=True
            )
        ]

    def execute(self, expression: str) -> ToolResult:
        """Execute calculator tool."""
        try:
            # Basic safe evaluation (for testing only - use ast.literal_eval in production)
            result = eval(expression, {"__builtins__": {}}, {})
            return ToolResult(
                success=True,
                content=str(result)
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Calculation error: {str(e)}"
            )


@pytest.fixture
def adapter():
    """Create adapter with real API key."""
    return AnthropicAdapter(
        model_name="claude-3-haiku-20240307",  # Use cheapest model for testing
        max_tool_iterations=5
    )


@pytest.fixture
def calculator_tool():
    """Create calculator tool."""
    return CalculatorTool()


@pytest.fixture
def calculator_schema(calculator_tool):
    """Get calculator tool schema in Anthropic format."""
    return calculator_tool.to_anthropic_schema()


@requires_api_key
class TestAnthropicAdapterBasicIntegration:
    """Test basic generation with real API."""

    def test_simple_generation(self, adapter):
        """Test simple text generation."""
        params = GenerationParams(
            temperature=0.7,
            max_tokens=100
        )

        result = adapter.generate("Say 'Hello, World!' and nothing else.", params)

        assert isinstance(result, str)
        assert len(result) > 0
        assert "hello" in result.lower() or "world" in result.lower()

        # Check usage tracking
        assert adapter._input_tokens > 0
        assert adapter._output_tokens > 0
        assert float(adapter._total_cost) > 0

    def test_generation_with_parameters(self, adapter):
        """Test generation with various parameters."""
        params = GenerationParams(
            temperature=0.0,  # Deterministic
            max_tokens=50,
            top_p=1.0
        )

        result = adapter.generate("What is 2+2?", params)

        assert isinstance(result, str)
        assert "4" in result

    def test_model_info(self, adapter):
        """Test getting model information."""
        info = adapter.get_model_info()

        assert info['provider'] == 'Anthropic'
        assert info['model'] == 'claude-3-haiku-20240307'
        assert info['supports_streaming'] is True
        assert info['supports_tools'] is True
        assert info['max_context_tokens'] == 200000

    def test_cost_tracking(self, adapter):
        """Test cost tracking accuracy."""
        initial_cost = float(adapter._total_cost)

        params = GenerationParams(max_tokens=50)
        adapter.generate("Test prompt", params)

        final_cost = float(adapter._total_cost)

        assert final_cost > initial_cost
        assert len(adapter.cost_history) > 0

        # Check cost breakdown
        breakdown = adapter.get_cost_breakdown()
        assert breakdown['total_requests'] > 0
        assert breakdown['input_tokens'] > 0
        assert breakdown['output_tokens'] > 0
        assert breakdown['total_cost_usd'] > 0


@requires_api_key
class TestAnthropicAdapterStreaming:
    """Test streaming with real API."""

    def test_streaming_generation(self, adapter):
        """Test streaming text generation."""
        params = GenerationParams(
            temperature=0.7,
            max_tokens=100
        )

        chunks = []
        for chunk in adapter.generate_streaming("Count to 5.", params):
            chunks.append(chunk)

        # Should have received multiple chunks
        assert len(chunks) > 0

        # Combine chunks
        full_response = ''.join(chunks)
        assert len(full_response) > 0

    def test_streaming_cost_tracking(self, adapter):
        """Test that streaming tracks costs."""
        initial_cost = float(adapter._total_cost)

        params = GenerationParams(max_tokens=50)
        list(adapter.generate_streaming("Test", params))

        final_cost = float(adapter._total_cost)
        assert final_cost > initial_cost


@requires_api_key
class TestAnthropicAdapterToolUse:
    """Test tool use with real API."""

    def test_tool_use_single_call(self, adapter, calculator_tool, calculator_schema):
        """Test single tool call scenario."""
        params = GenerationParams(
            temperature=0.0,
            max_tokens=500
        )

        # First iteration - Claude should request calculator
        result, metadata = adapter.generate_with_tools(
            "What is 25 * 47? Use the calculator tool.",
            [calculator_schema],
            params,
            max_iterations=1
        )

        # Should have requested tool use
        assert metadata['iterations'] == 1
        assert 'pending_tool_calls' in metadata or metadata['stop_reason'] == 'end_turn'

        if 'pending_tool_calls' in metadata:
            # Claude requested tools
            tool_calls = metadata['pending_tool_calls']
            assert len(tool_calls) > 0
            assert tool_calls[0]['name'] == 'calculator'

            # Execute tool
            tool_result = calculator_tool.execute_safe(**tool_calls[0]['input'])
            assert tool_result.success
            assert tool_result.content == "1175"

            # Continue conversation with tool results
            tool_results = [{
                'tool_use_id': tool_calls[0]['id'],
                'content': tool_result.content
            }]

            final_result, final_metadata = adapter.continue_with_tool_results(
                metadata['messages'],
                tool_results,
                [calculator_schema],
                params
            )

            assert '1175' in final_result or '1,175' in final_result
            assert final_metadata['stop_reason'] == 'end_turn'

    def test_tool_use_without_tools(self, adapter):
        """Test that generation works without tools."""
        params = GenerationParams(max_tokens=100)

        result, metadata = adapter.generate_with_tools(
            "What is 2+2?",
            [],  # No tools
            params
        )

        assert isinstance(result, str)
        assert metadata['iterations'] == 0
        assert metadata['tool_calls'] == []

    def test_tool_use_cost_tracking(self, adapter, calculator_schema):
        """Test cost tracking across tool iterations."""
        initial_cost = float(adapter._total_cost)

        params = GenerationParams(
            temperature=0.0,
            max_tokens=500
        )

        result, metadata = adapter.generate_with_tools(
            "What is 10 + 20?",
            [calculator_schema],
            params,
            max_iterations=1
        )

        final_cost = float(adapter._total_cost)

        # Cost should increase
        assert final_cost > initial_cost

        # Check metadata has cost information
        if 'total_cost_usd' in metadata:
            assert metadata['total_cost_usd'] > 0
            assert metadata['total_tokens'] > 0


@requires_api_key
class TestAnthropicAdapterErrorHandling:
    """Test error handling with real API."""

    def test_invalid_model(self):
        """Test handling of invalid model name."""
        adapter = AnthropicAdapter(
            model_name="invalid-model-name",
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )

        params = GenerationParams(max_tokens=10)

        with pytest.raises(Exception):  # Should raise some error
            adapter.generate("Test", params)

    def test_empty_prompt(self, adapter):
        """Test handling of empty prompt."""
        params = GenerationParams()

        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            adapter.generate("", params)

    def test_very_long_prompt_handling(self, adapter):
        """Test handling of very long prompts."""
        # Create a prompt that's close to context limit
        long_prompt = "Test. " * 10000

        params = GenerationParams(max_tokens=50)

        # Should either succeed or raise appropriate error
        try:
            result = adapter.generate(long_prompt, params)
            assert isinstance(result, str)
        except Exception as e:
            # Should be a meaningful error, not a crash
            assert "token" in str(e).lower() or "length" in str(e).lower()


@requires_api_key
class TestAnthropicAdapterMultipleModels:
    """Test different Claude models."""

    @pytest.mark.parametrize("model_name", [
        "claude-3-haiku-20240307",
        "claude-3-5-sonnet-20241022",
    ])
    def test_different_models(self, model_name):
        """Test generation with different models."""
        adapter = AnthropicAdapter(model_name=model_name)

        params = GenerationParams(
            temperature=0.7,
            max_tokens=50
        )

        result = adapter.generate("Say hello.", params)

        assert isinstance(result, str)
        assert len(result) > 0

        # Check model info
        info = adapter.get_model_info()
        assert info['model'] == model_name


@requires_api_key
class TestAnthropicAdapterPerformance:
    """Test performance characteristics."""

    def test_latency_reasonable(self, adapter):
        """Test that latency is reasonable."""
        params = GenerationParams(max_tokens=50)

        start_time = time.time()
        result = adapter.generate("Test", params)
        elapsed = time.time() - start_time

        # Should complete in reasonable time (adjust as needed)
        assert elapsed < 30.0  # 30 seconds max
        assert isinstance(result, str)

    def test_multiple_requests(self, adapter):
        """Test multiple sequential requests."""
        params = GenerationParams(max_tokens=20)

        for i in range(3):
            result = adapter.generate(f"Test {i}", params)
            assert isinstance(result, str)

        # Check usage tracking across requests
        assert adapter._request_count == 3
        assert adapter._input_tokens > 0
        assert adapter._output_tokens > 0


if __name__ == "__main__":
    if HAS_API_KEY:
        print("Running integration tests with real Anthropic API...")
        pytest.main([__file__, "-v", "-s"])
    else:
        print("ANTHROPIC_API_KEY not set. Skipping integration tests.")
        print("Set ANTHROPIC_API_KEY environment variable to run these tests.")
