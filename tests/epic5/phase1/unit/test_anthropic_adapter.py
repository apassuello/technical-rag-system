"""
Unit tests for AnthropicAdapter with mocked API.

Tests all core functionality without making real API calls:
- Basic generation
- Tool use with multi-turn conversations
- Cost tracking
- Error handling
- Streaming support
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from decimal import Decimal
import time

from src.components.generators.llm_adapters.anthropic_adapter import (
    AnthropicAdapter,
    create_anthropic_adapter
)
from src.components.generators.base import GenerationParams
from src.components.generators.llm_adapters.base_adapter import (
    RateLimitError,
    AuthenticationError,
    ModelNotFoundError
)


class TestAnthropicAdapterInitialization:
    """Test adapter initialization and configuration."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        adapter = AnthropicAdapter(
            model_name="claude-3-5-sonnet-20241022",
            api_key="sk-ant-test-key"
        )

        assert adapter.model_name == "claude-3-5-sonnet-20241022"
        assert adapter.api_key == "sk-ant-test-key"
        assert adapter.max_tool_iterations == 10
        assert adapter._input_tokens == 0
        assert adapter._output_tokens == 0
        assert float(adapter._total_cost) == 0.0

    def test_init_with_env_var(self, monkeypatch):
        """Test initialization with ANTHROPIC_API_KEY environment variable."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env-key")

        adapter = AnthropicAdapter(
            model_name="claude-3-haiku-20240307"
        )

        assert adapter.api_key == "sk-ant-env-key"
        assert adapter.model_name == "claude-3-haiku-20240307"

    def test_init_with_config(self):
        """Test initialization with config dictionary."""
        config = {
            "api_key": "sk-ant-config-key",
            "max_tool_iterations": 5
        }

        adapter = AnthropicAdapter(
            model_name="claude-3-opus-20240229",
            config=config
        )

        assert adapter.api_key == "sk-ant-config-key"
        assert adapter.max_tool_iterations == 5

    def test_init_without_api_key(self, monkeypatch):
        """Test that initialization fails without API key."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(ValueError, match="API key required"):
            AnthropicAdapter(model_name="claude-3-5-sonnet-20241022")

    def test_factory_function(self):
        """Test factory function for component registration."""
        adapter = create_anthropic_adapter(
            model_name="claude-3-sonnet-20240229",
            api_key="sk-ant-factory-key"
        )

        assert isinstance(adapter, AnthropicAdapter)
        assert adapter.model_name == "claude-3-sonnet-20240229"


class TestAnthropicAdapterBasicGeneration:
    """Test basic text generation without tools."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked client."""
        with patch('src.components.generators.llm_adapters.anthropic_adapter.Anthropic'):
            adapter = AnthropicAdapter(
                model_name="claude-3-5-sonnet-20241022",
                api_key="sk-ant-test-key"
            )
            return adapter

    def test_generate_success(self, adapter):
        """Test successful generation."""
        # Mock response
        mock_content = Mock()
        mock_content.type = 'text'
        mock_content.text = "This is a test response."

        mock_usage = Mock()
        mock_usage.input_tokens = 10
        mock_usage.output_tokens = 20

        mock_response = Mock()
        mock_response.id = "msg_123"
        mock_response.model = "claude-3-5-sonnet-20241022"
        mock_response.role = "assistant"
        mock_response.content = [mock_content]
        mock_response.stop_reason = "end_turn"
        mock_response.usage = mock_usage

        adapter.client.messages.create = Mock(return_value=mock_response)

        # Test generation
        params = GenerationParams(temperature=0.7, max_tokens=100)
        result = adapter.generate("Test prompt", params)

        assert result == "This is a test response."
        assert adapter._input_tokens == 10
        assert adapter._output_tokens == 20
        assert adapter._request_count == 1

    def test_generate_with_multiple_text_blocks(self, adapter):
        """Test generation with multiple text content blocks."""
        # Mock response with multiple text blocks
        mock_content1 = Mock()
        mock_content1.type = 'text'
        mock_content1.text = "First part."

        mock_content2 = Mock()
        mock_content2.type = 'text'
        mock_content2.text = "Second part."

        mock_usage = Mock()
        mock_usage.input_tokens = 10
        mock_usage.output_tokens = 20

        mock_response = Mock()
        mock_response.id = "msg_123"
        mock_response.model = "claude-3-5-sonnet-20241022"
        mock_response.role = "assistant"
        mock_response.content = [mock_content1, mock_content2]
        mock_response.stop_reason = "end_turn"
        mock_response.usage = mock_usage

        adapter.client.messages.create = Mock(return_value=mock_response)

        # Test generation
        params = GenerationParams()
        result = adapter.generate("Test prompt", params)

        assert result == "First part.\nSecond part."

    def test_generate_max_tokens_reached(self, adapter):
        """Test handling of max_tokens truncation."""
        mock_content = Mock()
        mock_content.type = 'text'
        mock_content.text = "Truncated response..."

        mock_usage = Mock()
        mock_usage.input_tokens = 10
        mock_usage.output_tokens = 100

        mock_response = Mock()
        mock_response.id = "msg_123"
        mock_response.model = "claude-3-5-sonnet-20241022"
        mock_response.role = "assistant"
        mock_response.content = [mock_content]
        mock_response.stop_reason = "max_tokens"
        mock_response.usage = mock_usage

        adapter.client.messages.create = Mock(return_value=mock_response)

        # Test generation (should log warning but succeed)
        params = GenerationParams(max_tokens=100)
        result = adapter.generate("Test prompt", params)

        assert result == "Truncated response..."


class TestAnthropicAdapterToolUse:
    """Test tool use functionality."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked client."""
        with patch('src.components.generators.llm_adapters.anthropic_adapter.Anthropic'):
            adapter = AnthropicAdapter(
                model_name="claude-3-5-sonnet-20241022",
                api_key="sk-ant-test-key"
            )
            return adapter

    @pytest.fixture
    def sample_tools(self):
        """Sample tool schemas."""
        return [
            {
                "name": "calculator",
                "description": "Perform calculations",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Math expression"
                        }
                    },
                    "required": ["expression"]
                }
            }
        ]

    def test_generate_with_tools_no_tool_use(self, adapter, sample_tools):
        """Test generation with tools available but not used."""
        # Mock response without tool use
        mock_content = Mock()
        mock_content.type = 'text'
        mock_content.text = "The answer is 42."

        mock_usage = Mock()
        mock_usage.input_tokens = 50
        mock_usage.output_tokens = 20

        mock_response = Mock()
        mock_response.id = "msg_123"
        mock_response.model = "claude-3-5-sonnet-20241022"
        mock_response.role = "assistant"
        mock_response.content = [mock_content]
        mock_response.stop_reason = "end_turn"
        mock_response.usage = mock_usage

        adapter.client.messages.create = Mock(return_value=mock_response)

        # Test generation with tools
        params = GenerationParams()
        result, metadata = adapter.generate_with_tools(
            "What is 6 * 7?",
            sample_tools,
            params
        )

        assert result == "The answer is 42."
        assert metadata['iterations'] == 1
        assert metadata['tool_calls'] == []
        assert metadata['total_tokens'] == 70
        assert metadata['stop_reason'] == 'end_turn'

    def test_generate_with_tools_single_tool_call(self, adapter, sample_tools):
        """Test generation with single tool call."""
        # Mock response with tool use
        mock_text = Mock()
        mock_text.type = 'text'
        mock_text.text = "Let me calculate that."

        mock_tool = Mock()
        mock_tool.type = 'tool_use'
        mock_tool.id = "toolu_123"
        mock_tool.name = "calculator"
        mock_tool.input = {"expression": "6 * 7"}

        mock_usage = Mock()
        mock_usage.input_tokens = 50
        mock_usage.output_tokens = 30

        mock_response = Mock()
        mock_response.id = "msg_123"
        mock_response.model = "claude-3-5-sonnet-20241022"
        mock_response.role = "assistant"
        mock_response.content = [mock_text, mock_tool]
        mock_response.stop_reason = "tool_use"
        mock_response.usage = mock_usage

        adapter.client.messages.create = Mock(return_value=mock_response)

        # Test generation with tools
        params = GenerationParams()
        result, metadata = adapter.generate_with_tools(
            "What is 6 * 7?",
            sample_tools,
            params
        )

        assert metadata['stop_reason'] == 'tool_use'
        assert len(metadata['tool_calls']) == 1
        assert metadata['tool_calls'][0]['name'] == "calculator"
        assert metadata['tool_calls'][0]['input'] == {"expression": "6 * 7"}
        assert 'pending_tool_calls' in metadata

    def test_generate_with_tools_no_tools_provided(self, adapter):
        """Test that empty tools list falls back to regular generation."""
        # Mock response
        mock_content = Mock()
        mock_content.type = 'text'
        mock_content.text = "Simple response."

        mock_usage = Mock()
        mock_usage.input_tokens = 10
        mock_usage.output_tokens = 10

        mock_response = Mock()
        mock_response.id = "msg_123"
        mock_response.model = "claude-3-5-sonnet-20241022"
        mock_response.role = "assistant"
        mock_response.content = [mock_content]
        mock_response.stop_reason = "end_turn"
        mock_response.usage = mock_usage

        adapter.client.messages.create = Mock(return_value=mock_response)

        # Test with no tools
        params = GenerationParams()
        result, metadata = adapter.generate_with_tools(
            "Test",
            [],  # No tools
            params
        )

        assert result == "Simple response."
        assert metadata['iterations'] == 0
        assert metadata['tool_calls'] == []

    def test_continue_with_tool_results(self, adapter, sample_tools):
        """Test continuing conversation with tool results."""
        # Mock response after tool execution
        mock_content = Mock()
        mock_content.type = 'text'
        mock_content.text = "The result is 42."

        mock_usage = Mock()
        mock_usage.input_tokens = 60
        mock_usage.output_tokens = 15

        mock_response = Mock()
        mock_response.id = "msg_124"
        mock_response.model = "claude-3-5-sonnet-20241022"
        mock_response.role = "assistant"
        mock_response.content = [mock_content]
        mock_response.stop_reason = "end_turn"
        mock_response.usage = mock_usage

        adapter.client.messages.create = Mock(return_value=mock_response)

        # Test continuing conversation
        messages = [
            {"role": "user", "content": "What is 6 * 7?"},
            {"role": "assistant", "content": [{"type": "tool_use", "id": "toolu_123", "name": "calculator"}]}
        ]
        tool_results = [
            {"tool_use_id": "toolu_123", "content": "42"}
        ]

        params = GenerationParams()
        result, metadata = adapter.continue_with_tool_results(
            messages,
            tool_results,
            sample_tools,
            params
        )

        assert result == "The result is 42."
        assert metadata['stop_reason'] == 'end_turn'
        assert metadata['tokens'] == 75


class TestAnthropicAdapterCostTracking:
    """Test cost tracking functionality."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked client."""
        with patch('src.components.generators.llm_adapters.anthropic_adapter.Anthropic'):
            adapter = AnthropicAdapter(
                model_name="claude-3-5-sonnet-20241022",
                api_key="sk-ant-test-key"
            )
            return adapter

    def test_cost_calculation(self, adapter):
        """Test accurate cost calculation."""
        # Simulate usage
        usage = {
            'input_tokens': 1000,
            'output_tokens': 2000,
            'total_tokens': 3000
        }

        cost_breakdown = adapter._track_usage_with_breakdown(usage)

        # Claude 3.5 Sonnet pricing: $3/1M input, $15/1M output
        expected_input_cost = (1000 / 1_000_000) * 3.00
        expected_output_cost = (2000 / 1_000_000) * 15.00
        expected_total = expected_input_cost + expected_output_cost

        assert cost_breakdown['input_tokens'] == 1000
        assert cost_breakdown['output_tokens'] == 2000
        assert abs(cost_breakdown['input_cost_usd'] - expected_input_cost) < 0.000001
        assert abs(cost_breakdown['output_cost_usd'] - expected_output_cost) < 0.000001
        assert abs(cost_breakdown['total_cost_usd'] - expected_total) < 0.000001

    def test_get_model_info(self, adapter):
        """Test get_model_info returns correct information."""
        # Simulate some usage
        adapter._input_tokens = 500
        adapter._output_tokens = 1000
        adapter._total_cost = Decimal('0.015')

        info = adapter.get_model_info()

        assert info['provider'] == 'Anthropic'
        assert info['model'] == 'claude-3-5-sonnet-20241022'
        assert info['supports_streaming'] is True
        assert info['supports_tools'] is True
        assert info['max_tool_iterations'] == 10
        assert info['input_tokens_used'] == 500
        assert info['output_tokens_used'] == 1000
        assert info['total_cost_usd'] == 0.015

    def test_get_cost_breakdown(self, adapter):
        """Test detailed cost breakdown."""
        # Simulate multiple requests
        adapter._input_tokens = 5000
        adapter._output_tokens = 10000
        adapter._request_count = 5
        adapter._total_cost = Decimal('0.165')

        breakdown = adapter.get_cost_breakdown()

        assert breakdown['model'] == 'claude-3-5-sonnet-20241022'
        assert breakdown['total_requests'] == 5
        assert breakdown['input_tokens'] == 5000
        assert breakdown['output_tokens'] == 10000
        assert breakdown['total_tokens'] == 15000
        assert abs(breakdown['avg_cost_per_request'] - 0.033) < 0.001


class TestAnthropicAdapterErrorHandling:
    """Test error handling and retry logic."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked client."""
        with patch('src.components.generators.llm_adapters.anthropic_adapter.Anthropic'):
            adapter = AnthropicAdapter(
                model_name="claude-3-5-sonnet-20241022",
                api_key="sk-ant-test-key"
            )
            return adapter

    def test_authentication_error(self, adapter):
        """Test handling of authentication errors."""
        with patch('src.components.generators.llm_adapters.anthropic_adapter.anthropic') as mock_anthropic:
            mock_anthropic.AuthenticationError = Exception

            adapter.client.messages.create = Mock(
                side_effect=mock_anthropic.AuthenticationError("Invalid API key")
            )

            params = GenerationParams()
            with pytest.raises(AuthenticationError):
                adapter.generate("Test", params)

    def test_rate_limit_error(self, adapter):
        """Test handling of rate limit errors."""
        with patch('src.components.generators.llm_adapters.anthropic_adapter.anthropic') as mock_anthropic:
            mock_anthropic.RateLimitError = Exception

            adapter.client.messages.create = Mock(
                side_effect=mock_anthropic.RateLimitError("Rate limit exceeded")
            )

            params = GenerationParams()
            with pytest.raises(RateLimitError):
                adapter.generate("Test", params)

    def test_model_not_found_error(self, adapter):
        """Test handling of model not found errors."""
        with patch('src.components.generators.llm_adapters.anthropic_adapter.anthropic') as mock_anthropic:
            mock_anthropic.NotFoundError = Exception

            adapter.client.messages.create = Mock(
                side_effect=mock_anthropic.NotFoundError("Model not found")
            )

            params = GenerationParams()
            with pytest.raises(ModelNotFoundError):
                adapter.generate("Test", params)

    def test_empty_prompt_validation(self, adapter):
        """Test that empty prompts are rejected."""
        params = GenerationParams()

        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            adapter.generate("", params)

        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            adapter.generate("   ", params)


class TestAnthropicAdapterStreaming:
    """Test streaming functionality."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked client."""
        with patch('src.components.generators.llm_adapters.anthropic_adapter.Anthropic'):
            adapter = AnthropicAdapter(
                model_name="claude-3-5-sonnet-20241022",
                api_key="sk-ant-test-key"
            )
            return adapter

    def test_streaming_generation(self, adapter):
        """Test streaming text generation."""
        # Mock streaming response
        mock_stream = MagicMock()
        mock_stream.__enter__ = Mock(return_value=mock_stream)
        mock_stream.__exit__ = Mock(return_value=False)
        mock_stream.text_stream = iter(["Hello", " ", "world", "!"])

        mock_final_message = Mock()
        mock_usage = Mock()
        mock_usage.input_tokens = 10
        mock_usage.output_tokens = 20
        mock_final_message.usage = mock_usage
        mock_stream.get_final_message = Mock(return_value=mock_final_message)

        adapter.client.messages.stream = Mock(return_value=mock_stream)

        # Test streaming
        params = GenerationParams()
        chunks = list(adapter.generate_streaming("Test", params))

        assert chunks == ["Hello", " ", "world", "!"]
        assert adapter._input_tokens == 10
        assert adapter._output_tokens == 20


class TestAnthropicAdapterValidation:
    """Test validation methods."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with mocked client."""
        with patch('src.components.generators.llm_adapters.anthropic_adapter.Anthropic'):
            adapter = AnthropicAdapter(
                model_name="claude-3-5-sonnet-20241022",
                api_key="sk-ant-test-key"
            )
            return adapter

    def test_validate_model_success(self, adapter):
        """Test successful model validation."""
        # Mock successful validation response
        mock_content = Mock()
        mock_content.type = 'text'
        mock_content.text = "Hi"

        mock_response = Mock()
        mock_response.content = [mock_content]

        adapter.client.messages.create = Mock(return_value=mock_response)

        assert adapter._validate_model() is True

    def test_validate_model_failure(self, adapter):
        """Test model validation failure."""
        adapter.client.messages.create = Mock(
            side_effect=Exception("Model not available")
        )

        assert adapter._validate_model() is False

    def test_provider_name(self, adapter):
        """Test provider name."""
        assert adapter._get_provider_name() == "Anthropic"

    def test_supports_streaming(self, adapter):
        """Test streaming support."""
        assert adapter._supports_streaming() is True

    def test_get_max_tokens(self, adapter):
        """Test max tokens retrieval."""
        assert adapter._get_max_tokens() == 200000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
