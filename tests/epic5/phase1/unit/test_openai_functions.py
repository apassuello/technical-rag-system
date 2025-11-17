"""
Unit tests for OpenAI function calling support.

Tests the generate_with_functions() and continue_with_function_results() methods
of the OpenAIAdapter without making real API calls.

Test Coverage:
- Function call extraction from responses
- Multi-turn conversation handling
- Parallel function call support
- Cost tracking across iterations
- Error handling for various scenarios
- Message format validation
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from decimal import Decimal
from typing import Dict, Any, List

from src.components.generators.llm_adapters.openai_adapter import OpenAIAdapter
from src.components.generators.base import GenerationParams, LLMError


class TestOpenAIFunctionCalling:
    """Test suite for OpenAI function calling functionality."""

    @pytest.fixture
    def mock_client(self) -> Mock:
        """Create a mock OpenAI client."""
        client = Mock()
        return client

    @pytest.fixture
    def adapter(self, mock_client: Mock) -> OpenAIAdapter:
        """Create OpenAIAdapter with mocked client."""
        with patch('src.components.generators.llm_adapters.openai_adapter.OpenAI'):
            adapter = OpenAIAdapter(
                model_name="gpt-3.5-turbo",
                api_key="test-key-123"
            )
            adapter.client = mock_client
            return adapter

    @pytest.fixture
    def sample_tools(self) -> List[Dict[str, Any]]:
        """Sample tool schemas in OpenAI format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "Evaluate mathematical expressions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "Math expression to evaluate"
                            }
                        },
                        "required": ["expression"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "City name"
                            }
                        },
                        "required": ["location"]
                    }
                }
            }
        ]

    def test_function_calling_with_empty_tools_raises_error(self, adapter: OpenAIAdapter) -> None:
        """Test that empty tools list raises ValueError."""
        with pytest.raises(ValueError, match="Tools list cannot be empty"):
            adapter.generate_with_functions(
                prompt="Test",
                tools=[]
            )

    def test_single_function_call_extraction(
        self,
        adapter: OpenAIAdapter,
        mock_client: Mock,
        sample_tools: List[Dict[str, Any]]
    ) -> None:
        """Test extraction of a single function call from response."""
        # Mock response with function call
        mock_response = Mock()
        mock_response.id = "chatcmpl-123"
        mock_response.model = "gpt-3.5-turbo"
        mock_response.created = 1234567890

        # Mock usage
        mock_usage = Mock()
        mock_usage.prompt_tokens = 50
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 70
        mock_response.usage = mock_usage

        # Mock choice with tool call
        mock_tool_call = Mock()
        mock_tool_call.id = "call_abc123"
        mock_tool_call.type = "function"
        mock_tool_call.function = Mock()
        mock_tool_call.function.name = "calculator"
        mock_tool_call.function.arguments = '{"expression": "25 * 47"}'

        mock_choice = Mock()
        mock_choice.message = Mock()
        mock_choice.message.role = "assistant"
        mock_choice.message.content = None
        mock_choice.message.tool_calls = [mock_tool_call]
        mock_choice.finish_reason = "tool_calls"

        mock_response.choices = [mock_choice]

        mock_client.chat.completions.create.return_value = mock_response

        # Call generate_with_functions
        result = adapter.generate_with_functions(
            prompt="What is 25 * 47?",
            tools=sample_tools,
            params=GenerationParams(temperature=0.0)
        )

        # Verify result
        assert result['status'] == 'requires_function_execution'
        assert result['iterations'] == 1
        assert len(result['function_calls']) == 1

        # Verify function call details
        func_call = result['function_calls'][0]
        assert func_call['id'] == 'call_abc123'
        assert func_call['name'] == 'calculator'
        assert func_call['arguments'] == {'expression': '25 * 47'}
        assert func_call['iteration'] == 1

        # Verify pending tool calls
        assert len(result['pending_tool_calls']) == 1
        assert result['pending_tool_calls'][0]['id'] == 'call_abc123'

        # Verify cost tracking
        assert result['total_tokens'] == 70
        assert isinstance(result['total_cost_usd'], float)
        assert result['total_cost_usd'] > 0

    def test_parallel_function_calls(
        self,
        adapter: OpenAIAdapter,
        mock_client: Mock,
        sample_tools: List[Dict[str, Any]]
    ) -> None:
        """Test handling of parallel function calls."""
        # Mock response with multiple parallel tool calls
        mock_response = Mock()
        mock_response.id = "chatcmpl-456"
        mock_response.model = "gpt-3.5-turbo"
        mock_response.created = 1234567890

        mock_usage = Mock()
        mock_usage.prompt_tokens = 60
        mock_usage.completion_tokens = 30
        mock_usage.total_tokens = 90
        mock_response.usage = mock_usage

        # Create multiple tool calls
        mock_tool_call_1 = Mock()
        mock_tool_call_1.id = "call_1"
        mock_tool_call_1.type = "function"
        mock_tool_call_1.function = Mock()
        mock_tool_call_1.function.name = "calculator"
        mock_tool_call_1.function.arguments = '{"expression": "10 + 5"}'

        mock_tool_call_2 = Mock()
        mock_tool_call_2.id = "call_2"
        mock_tool_call_2.type = "function"
        mock_tool_call_2.function = Mock()
        mock_tool_call_2.function.name = "get_weather"
        mock_tool_call_2.function.arguments = '{"location": "London"}'

        mock_choice = Mock()
        mock_choice.message = Mock()
        mock_choice.message.role = "assistant"
        mock_choice.message.content = None
        mock_choice.message.tool_calls = [mock_tool_call_1, mock_tool_call_2]
        mock_choice.finish_reason = "tool_calls"

        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        # Call generate_with_functions
        result = adapter.generate_with_functions(
            prompt="What's 10+5 and what's the weather in London?",
            tools=sample_tools
        )

        # Verify parallel calls
        assert result['status'] == 'requires_function_execution'
        assert len(result['function_calls']) == 2
        assert len(result['pending_tool_calls']) == 2

        # Verify both functions recorded
        func_names = [fc['name'] for fc in result['function_calls']]
        assert 'calculator' in func_names
        assert 'get_weather' in func_names

    def test_completion_without_function_calls(
        self,
        adapter: OpenAIAdapter,
        mock_client: Mock,
        sample_tools: List[Dict[str, Any]]
    ) -> None:
        """Test completion when LLM responds without calling functions."""
        # Mock response without tool calls
        mock_response = Mock()
        mock_response.id = "chatcmpl-789"
        mock_response.model = "gpt-3.5-turbo"
        mock_response.created = 1234567890

        mock_usage = Mock()
        mock_usage.prompt_tokens = 40
        mock_usage.completion_tokens = 15
        mock_usage.total_tokens = 55
        mock_response.usage = mock_usage

        mock_choice = Mock()
        mock_choice.message = Mock()
        mock_choice.message.role = "assistant"
        mock_choice.message.content = "I can help with that!"
        mock_choice.message.tool_calls = None
        mock_choice.finish_reason = "stop"

        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        # Call generate_with_functions
        result = adapter.generate_with_functions(
            prompt="Hello!",
            tools=sample_tools
        )

        # Verify completion
        assert result['status'] == 'completed'
        assert result['final_response'] == "I can help with that!"
        assert result['iterations'] == 1
        assert len(result['function_calls']) == 0
        assert result['finish_reason'] == 'stop'

    def test_continue_with_function_results(
        self,
        adapter: OpenAIAdapter,
        mock_client: Mock,
        sample_tools: List[Dict[str, Any]]
    ) -> None:
        """Test continuing conversation with function results."""
        # Setup: messages from previous call with tool_calls
        messages = [
            {"role": "user", "content": "What is 25 * 47?"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_abc123",
                        "type": "function",
                        "function": {
                            "name": "calculator",
                            "arguments": '{"expression": "25 * 47"}'
                        }
                    }
                ]
            }
        ]

        function_results = [
            {
                "tool_call_id": "call_abc123",
                "content": "1175"
            }
        ]

        # Mock final response after function execution
        mock_response = Mock()
        mock_response.id = "chatcmpl-final"
        mock_response.model = "gpt-3.5-turbo"
        mock_response.created = 1234567890

        mock_usage = Mock()
        mock_usage.prompt_tokens = 80
        mock_usage.completion_tokens = 25
        mock_usage.total_tokens = 105
        mock_response.usage = mock_usage

        mock_choice = Mock()
        mock_choice.message = Mock()
        mock_choice.message.role = "assistant"
        mock_choice.message.content = "The answer is 1,175."
        mock_choice.message.tool_calls = None
        mock_choice.finish_reason = "stop"

        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        # Continue with results
        result = adapter.continue_with_function_results(
            messages=messages,
            function_results=function_results,
            tools=sample_tools
        )

        # Verify completion
        assert result['status'] == 'completed'
        assert result['final_response'] == "The answer is 1,175."
        assert result['iterations'] == 1

        # Verify function result was added to messages
        call_args = mock_client.chat.completions.create.call_args
        sent_messages = call_args.kwargs['messages']

        # Should have: user, assistant (tool_calls), tool (result)
        assert len(sent_messages) >= 3
        tool_messages = [m for m in sent_messages if m.get('role') == 'tool']
        assert len(tool_messages) == 1
        assert tool_messages[0]['tool_call_id'] == 'call_abc123'
        assert tool_messages[0]['content'] == '1175'

    def test_continue_with_empty_function_results_raises_error(
        self,
        adapter: OpenAIAdapter,
        sample_tools: List[Dict[str, Any]]
    ) -> None:
        """Test that empty function results raises ValueError."""
        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(ValueError, match="function_results cannot be empty"):
            adapter.continue_with_function_results(
                messages=messages,
                function_results=[],
                tools=sample_tools
            )

    def test_cost_tracking_across_iterations(
        self,
        adapter: OpenAIAdapter,
        mock_client: Mock,
        sample_tools: List[Dict[str, Any]]
    ) -> None:
        """Test that costs are tracked correctly across multiple iterations."""
        # Mock first response with function call
        mock_response_1 = Mock()
        mock_response_1.id = "chatcmpl-1"
        mock_response_1.model = "gpt-3.5-turbo"
        mock_response_1.created = 1234567890

        mock_usage_1 = Mock()
        mock_usage_1.prompt_tokens = 50
        mock_usage_1.completion_tokens = 20
        mock_usage_1.total_tokens = 70
        mock_response_1.usage = mock_usage_1

        mock_tool_call = Mock()
        mock_tool_call.id = "call_1"
        mock_tool_call.type = "function"
        mock_tool_call.function = Mock()
        mock_tool_call.function.name = "calculator"
        mock_tool_call.function.arguments = '{"expression": "5 + 5"}'

        mock_choice_1 = Mock()
        mock_choice_1.message = Mock()
        mock_choice_1.message.role = "assistant"
        mock_choice_1.message.content = None
        mock_choice_1.message.tool_calls = [mock_tool_call]
        mock_choice_1.finish_reason = "tool_calls"

        mock_response_1.choices = [mock_choice_1]

        # First call
        mock_client.chat.completions.create.return_value = mock_response_1

        result_1 = adapter.generate_with_functions(
            prompt="What is 5 + 5?",
            tools=sample_tools
        )

        assert result_1['total_tokens'] == 70
        first_cost = result_1['total_cost_usd']
        assert first_cost > 0

        # Mock second response with final answer
        mock_response_2 = Mock()
        mock_response_2.id = "chatcmpl-2"
        mock_response_2.model = "gpt-3.5-turbo"
        mock_response_2.created = 1234567891

        mock_usage_2 = Mock()
        mock_usage_2.prompt_tokens = 80
        mock_usage_2.completion_tokens = 15
        mock_usage_2.total_tokens = 95
        mock_response_2.usage = mock_usage_2

        mock_choice_2 = Mock()
        mock_choice_2.message = Mock()
        mock_choice_2.message.role = "assistant"
        mock_choice_2.message.content = "The answer is 10."
        mock_choice_2.message.tool_calls = None
        mock_choice_2.finish_reason = "stop"

        mock_response_2.choices = [mock_choice_2]

        mock_client.chat.completions.create.return_value = mock_response_2

        # Continue with results
        result_2 = adapter.continue_with_function_results(
            messages=result_1['messages'],
            function_results=[{"tool_call_id": "call_1", "content": "10"}],
            tools=sample_tools
        )

        # Verify cumulative tracking in continuation
        assert result_2['total_tokens'] == 95  # Tokens from second call
        assert result_2['total_cost_usd'] > 0

        # Verify cost breakdown exists
        assert len(result_2['cost_breakdown']) == 1

    def test_invalid_function_arguments_handled_gracefully(
        self,
        adapter: OpenAIAdapter,
        mock_client: Mock,
        sample_tools: List[Dict[str, Any]]
    ) -> None:
        """Test that invalid JSON in function arguments is handled gracefully."""
        # Mock response with invalid JSON
        mock_response = Mock()
        mock_response.id = "chatcmpl-bad"
        mock_response.model = "gpt-3.5-turbo"
        mock_response.created = 1234567890

        mock_usage = Mock()
        mock_usage.prompt_tokens = 50
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 70
        mock_response.usage = mock_usage

        mock_tool_call = Mock()
        mock_tool_call.id = "call_bad"
        mock_tool_call.type = "function"
        mock_tool_call.function = Mock()
        mock_tool_call.function.name = "calculator"
        mock_tool_call.function.arguments = '{invalid json}'  # Invalid JSON

        mock_choice = Mock()
        mock_choice.message = Mock()
        mock_choice.message.role = "assistant"
        mock_choice.message.content = None
        mock_choice.message.tool_calls = [mock_tool_call]
        mock_choice.finish_reason = "tool_calls"

        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        # Call should not crash
        result = adapter.generate_with_functions(
            prompt="Test",
            tools=sample_tools
        )

        # Should still record the function call with empty args
        assert result['status'] == 'requires_function_execution'
        assert len(result['function_calls']) == 1
        assert result['function_calls'][0]['arguments'] == {}  # Empty dict for invalid JSON

    def test_max_iterations_limit(
        self,
        adapter: OpenAIAdapter,
        mock_client: Mock,
        sample_tools: List[Dict[str, Any]]
    ) -> None:
        """Test that max_iterations limit is respected."""
        # Mock response that always returns function calls
        mock_response = Mock()
        mock_response.id = "chatcmpl-loop"
        mock_response.model = "gpt-3.5-turbo"
        mock_response.created = 1234567890

        mock_usage = Mock()
        mock_usage.prompt_tokens = 50
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 70
        mock_response.usage = mock_usage

        mock_tool_call = Mock()
        mock_tool_call.id = "call_loop"
        mock_tool_call.type = "function"
        mock_tool_call.function = Mock()
        mock_tool_call.function.name = "calculator"
        mock_tool_call.function.arguments = '{"expression": "1 + 1"}'

        mock_choice = Mock()
        mock_choice.message = Mock()
        mock_choice.message.role = "assistant"
        mock_choice.message.content = None
        mock_choice.message.tool_calls = [mock_tool_call]
        mock_choice.finish_reason = "tool_calls"

        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        # Call with max_iterations=1
        result = adapter.generate_with_functions(
            prompt="Test",
            tools=sample_tools,
            max_iterations=1
        )

        # Should stop after first iteration
        assert result['iterations'] == 1
        assert result['status'] == 'requires_function_execution'

    def test_default_params_used_when_none_provided(
        self,
        adapter: OpenAIAdapter,
        mock_client: Mock,
        sample_tools: List[Dict[str, Any]]
    ) -> None:
        """Test that default GenerationParams are used when none provided."""
        mock_response = Mock()
        mock_response.id = "chatcmpl-default"
        mock_response.model = "gpt-3.5-turbo"
        mock_response.created = 1234567890

        mock_usage = Mock()
        mock_usage.prompt_tokens = 50
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 70
        mock_response.usage = mock_usage

        mock_choice = Mock()
        mock_choice.message = Mock()
        mock_choice.message.role = "assistant"
        mock_choice.message.content = "Default response"
        mock_choice.message.tool_calls = None
        mock_choice.finish_reason = "stop"

        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        # Call without params
        result = adapter.generate_with_functions(
            prompt="Test",
            tools=sample_tools
            # No params provided
        )

        # Should complete successfully with defaults
        assert result['status'] == 'completed'
        assert result['final_response'] == "Default response"

        # Verify API was called
        assert mock_client.chat.completions.create.called


class TestOpenAIFunctionCallingEdgeCases:
    """Test edge cases and error scenarios for function calling."""

    @pytest.fixture
    def adapter(self) -> OpenAIAdapter:
        """Create OpenAIAdapter with mocked client."""
        with patch('src.components.generators.llm_adapters.openai_adapter.OpenAI'):
            adapter = OpenAIAdapter(
                model_name="gpt-3.5-turbo",
                api_key="test-key-123"
            )
            adapter.client = Mock()
            return adapter

    @pytest.fixture
    def sample_tools(self) -> List[Dict[str, Any]]:
        """Sample tool schemas."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "test_tool",
                    "description": "Test tool",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "input": {"type": "string"}
                        }
                    }
                }
            }
        ]

    def test_no_choices_in_response_raises_error(
        self,
        adapter: OpenAIAdapter,
        sample_tools: List[Dict[str, Any]]
    ) -> None:
        """Test that response without choices raises LLMError."""
        # Mock response with no choices
        mock_response = Mock()
        mock_response.id = "chatcmpl-no-choices"
        mock_response.model = "gpt-3.5-turbo"
        mock_response.created = 1234567890
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 0
        mock_response.usage.total_tokens = 10
        mock_response.choices = []  # Empty choices

        adapter.client.chat.completions.create.return_value = mock_response

        result = adapter.generate_with_functions(
            prompt="Test",
            tools=sample_tools
        )

        # Should return error status
        assert result['status'] == 'error'
        assert 'error' in result

    def test_message_format_with_none_content(
        self,
        adapter: OpenAIAdapter,
        sample_tools: List[Dict[str, Any]]
    ) -> None:
        """Test handling of None content in assistant messages."""
        mock_response = Mock()
        mock_response.id = "chatcmpl-none"
        mock_response.model = "gpt-3.5-turbo"
        mock_response.created = 1234567890

        mock_usage = Mock()
        mock_usage.prompt_tokens = 50
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 70
        mock_response.usage = mock_usage

        mock_choice = Mock()
        mock_choice.message = Mock()
        mock_choice.message.role = "assistant"
        mock_choice.message.content = None  # Explicitly None
        mock_choice.message.tool_calls = None
        mock_choice.finish_reason = "stop"

        mock_response.choices = [mock_choice]
        adapter.client.chat.completions.create.return_value = mock_response

        result = adapter.generate_with_functions(
            prompt="Test",
            tools=sample_tools
        )

        # Should handle None content gracefully
        assert result['status'] == 'completed'
        assert result['final_response'] == ''  # Empty string for None content
