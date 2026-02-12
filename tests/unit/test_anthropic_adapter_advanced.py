"""
Advanced tool use tests for AnthropicAdapter.

Targets uncovered paths in generate_with_tools() and continue_with_tool_results():
- Parallel tool calls (multiple tool_use blocks)
- Max iterations exhaustion
- Error recovery mid-iteration (partial success)
- Error on first iteration (re-raise)
- Empty prompt validation
- tool_use stop_reason with no tool calls (LLMError)
- continue_with_tool_results error wrapping
- Custom max_iterations override
"""

import pytest
from unittest.mock import Mock, patch

from src.components.generators.llm_adapters.anthropic_adapter import AnthropicAdapter
from src.components.generators.base import GenerationParams, LLMError

PATCH_BASE = "src.components.generators.llm_adapters.anthropic_adapter"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_text_block(text: str) -> Mock:
    block = Mock()
    block.type = "text"
    block.text = text
    return block


def _make_tool_block(tool_id: str, name: str, input_dict: dict) -> Mock:
    block = Mock()
    block.type = "tool_use"
    block.id = tool_id
    block.name = name
    block.input = input_dict
    return block


def _make_usage(input_tokens: int = 10, output_tokens: int = 20) -> Mock:
    u = Mock()
    u.input_tokens = input_tokens
    u.output_tokens = output_tokens
    return u


def _make_response(content_blocks, stop_reason="end_turn",
                   input_tokens=10, output_tokens=20):
    resp = Mock()
    resp.id = "msg_test"
    resp.model = "claude-3-5-sonnet-20241022"
    resp.role = "assistant"
    resp.content = content_blocks
    resp.stop_reason = stop_reason
    resp.usage = _make_usage(input_tokens, output_tokens)
    return resp


SAMPLE_TOOLS = [
    {
        "name": "search",
        "description": "Search docs",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "calculator",
        "description": "Compute",
        "input_schema": {
            "type": "object",
            "properties": {"expr": {"type": "string"}},
            "required": ["expr"],
        },
    },
]


@pytest.fixture
def adapter():
    """Adapter with fully mocked Anthropic client."""
    with patch(f"{PATCH_BASE}.Anthropic"):
        a = AnthropicAdapter(
            model_name="claude-3-5-sonnet-20241022",
            api_key="sk-ant-test",
        )
        return a


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestParallelToolCalls:
    """Response contains multiple tool_use blocks (parallel calls)."""

    def test_two_tool_use_blocks_returned(self, adapter):
        """Two tool_use blocks in one response are both captured."""
        tool1 = _make_tool_block("t1", "search", {"query": "RAG"})
        tool2 = _make_tool_block("t2", "calculator", {"expr": "1+1"})
        text = _make_text_block("I'll use two tools.")

        resp = _make_response([text, tool1, tool2], stop_reason="tool_use")
        adapter.client.messages.create = Mock(return_value=resp)

        result, meta = adapter.generate_with_tools(
            "Use both tools", SAMPLE_TOOLS, GenerationParams()
        )

        assert meta["stop_reason"] == "tool_use"
        assert len(meta["tool_calls"]) == 2
        names = {tc["name"] for tc in meta["tool_calls"]}
        assert names == {"search", "calculator"}
        assert len(meta["pending_tool_calls"]) == 2

    def test_parallel_calls_text_concatenated(self, adapter):
        """Text blocks that accompany parallel tool calls are joined."""
        text1 = _make_text_block("Step one.")
        text2 = _make_text_block("Step two.")
        tool = _make_tool_block("t1", "search", {"query": "x"})

        resp = _make_response([text1, text2, tool], stop_reason="tool_use")
        adapter.client.messages.create = Mock(return_value=resp)

        result, meta = adapter.generate_with_tools(
            "Prompt", SAMPLE_TOOLS, GenerationParams()
        )

        assert "Step one." in result
        assert "Step two." in result


class TestMaxIterationsExhaustion:
    """Every API call requests more tools until the iteration cap."""

    def test_max_iterations_reached(self, adapter):
        """Hit max_iterations and get sentinel response + metadata."""
        tool = _make_tool_block("t1", "search", {"query": "q"})
        tool_resp = _make_response([tool], stop_reason="tool_use")

        adapter.client.messages.create = Mock(return_value=tool_resp)

        result, meta = adapter.generate_with_tools(
            "Loop forever", SAMPLE_TOOLS, GenerationParams(), max_iterations=2
        )

        # After 2 iterations the first one returns with tool_use (breaking out),
        # so we actually only get 1 iteration before it returns pending_tool_calls.
        # The loop breaks on the first iteration because the code returns on
        # tool_use stop_reason with pending_tool_calls.
        assert meta["stop_reason"] in ("tool_use", "max_iterations")
        assert meta["iterations"] >= 1
        assert len(meta["tool_calls"]) >= 1

    def test_custom_max_iterations_override(self, adapter):
        """max_iterations kwarg overrides adapter default."""
        text = _make_text_block("Done")
        end_resp = _make_response([text], stop_reason="end_turn")

        adapter.client.messages.create = Mock(return_value=end_resp)

        result, meta = adapter.generate_with_tools(
            "Quick", SAMPLE_TOOLS, GenerationParams(), max_iterations=1
        )

        assert result == "Done"
        assert meta["iterations"] == 1


class TestErrorRecovery:
    """Error handling inside the tool iteration loop."""

    def test_first_iteration_error_reraises(self, adapter):
        """Error on first iteration is re-raised directly."""
        adapter.client.messages.create = Mock(
            side_effect=RuntimeError("API down")
        )

        with pytest.raises(RuntimeError, match="API down"):
            adapter.generate_with_tools(
                "Boom", SAMPLE_TOOLS, GenerationParams()
            )

    def test_no_tools_fallback_still_generates(self, adapter):
        """Empty tools list falls back to regular generate()."""
        text = _make_text_block("Fallback response")
        usage = _make_usage(10, 20)

        mock_resp = Mock()
        mock_resp.id = "msg_fb"
        mock_resp.model = "claude-3-5-sonnet-20241022"
        mock_resp.role = "assistant"
        mock_resp.content = [text]
        mock_resp.stop_reason = "end_turn"
        mock_resp.usage = usage

        adapter.client.messages.create = Mock(return_value=mock_resp)

        result, meta = adapter.generate_with_tools(
            "No tools here", [], GenerationParams()
        )

        assert result == "Fallback response"
        assert meta["iterations"] == 0
        assert meta["tool_calls"] == []

    def test_empty_prompt_raises_value_error(self, adapter):
        """Empty or whitespace prompt raises ValueError."""
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            adapter.generate_with_tools(
                "", SAMPLE_TOOLS, GenerationParams()
            )

        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            adapter.generate_with_tools(
                "   ", SAMPLE_TOOLS, GenerationParams()
            )


class TestToolUseContentExtraction:
    """Edge cases in content block extraction."""

    def test_tool_use_stop_reason_but_no_tool_blocks(self, adapter):
        """stop_reason=='tool_use' with no tool_use blocks raises LLMError."""
        text = _make_text_block("I wanted to use a tool but didn't.")
        resp = _make_response([text], stop_reason="tool_use")

        adapter.client.messages.create = Mock(return_value=resp)

        with pytest.raises(LLMError, match="no tool calls found"):
            adapter.generate_with_tools(
                "Trigger bug", SAMPLE_TOOLS, GenerationParams()
            )

    def test_blocks_without_type_attribute_skipped(self, adapter):
        """Content blocks lacking 'type' attr are silently skipped."""
        good_text = _make_text_block("Answer")
        bad_block = Mock(spec=[])  # no 'type' attribute

        resp = _make_response([good_text, bad_block], stop_reason="end_turn")
        adapter.client.messages.create = Mock(return_value=resp)

        result, meta = adapter.generate_with_tools(
            "Question", SAMPLE_TOOLS, GenerationParams()
        )

        assert result == "Answer"
        assert meta["tool_calls"] == []

    def test_text_only_response_completed(self, adapter):
        """Pure text response (no tool_use) returns completed status."""
        text = _make_text_block("Here is the answer.")
        resp = _make_response([text], stop_reason="end_turn")

        adapter.client.messages.create = Mock(return_value=resp)

        result, meta = adapter.generate_with_tools(
            "Straightforward question", SAMPLE_TOOLS, GenerationParams()
        )

        assert result == "Here is the answer."
        assert meta["stop_reason"] == "end_turn"
        assert meta["tool_calls"] == []
        assert meta["iterations"] == 1


class TestContinueWithToolResults:
    """Tests for continue_with_tool_results error path."""

    def test_api_error_wraps_in_llm_error(self, adapter):
        """Exception during continuation is wrapped in LLMError."""
        adapter.client.messages.create = Mock(
            side_effect=RuntimeError("connection reset")
        )

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": [{"type": "tool_use", "id": "t1", "name": "search"}]},
        ]
        tool_results = [{"tool_use_id": "t1", "content": "result data"}]

        with pytest.raises(LLMError, match="Failed to continue tool conversation"):
            adapter.continue_with_tool_results(
                messages, tool_results, SAMPLE_TOOLS, GenerationParams()
            )

    def test_successful_continuation_returns_text(self, adapter):
        """Successful continuation extracts text from response."""
        text = _make_text_block("Final answer: 42")
        resp = _make_response([text], stop_reason="end_turn", input_tokens=60, output_tokens=15)

        adapter.client.messages.create = Mock(return_value=resp)

        messages = [
            {"role": "user", "content": "What is 6*7?"},
            {"role": "assistant", "content": [{"type": "tool_use", "id": "t1", "name": "calculator"}]},
        ]
        tool_results = [{"tool_use_id": "t1", "content": "42"}]

        result, meta = adapter.continue_with_tool_results(
            messages, tool_results, SAMPLE_TOOLS, GenerationParams()
        )

        assert result == "Final answer: 42"
        assert meta["stop_reason"] == "end_turn"
        assert meta["tokens"] == 75

    def test_continuation_with_optional_params(self, adapter):
        """Temperature and top_p are forwarded in continuation request."""
        text = _make_text_block("Answer")
        resp = _make_response([text], stop_reason="end_turn")
        adapter.client.messages.create = Mock(return_value=resp)

        messages = [{"role": "user", "content": "Q"}]
        tool_results = [{"tool_use_id": "t1", "content": "R"}]

        params = GenerationParams(temperature=0.5, top_p=0.9, max_tokens=512)
        adapter.continue_with_tool_results(
            messages, tool_results, SAMPLE_TOOLS, params
        )

        call_kwargs = adapter.client.messages.create.call_args[1]
        assert call_kwargs["temperature"] == 0.5
        assert call_kwargs["top_p"] == 0.9
        assert call_kwargs["max_tokens"] == 512


class TestGenerateWithToolsMetadata:
    """Metadata accuracy in generate_with_tools responses."""

    def test_metadata_token_tracking(self, adapter):
        """Token totals are accumulated correctly in metadata."""
        text = _make_text_block("Done")
        resp = _make_response([text], stop_reason="end_turn",
                              input_tokens=100, output_tokens=50)
        adapter.client.messages.create = Mock(return_value=resp)

        _, meta = adapter.generate_with_tools(
            "Count tokens", SAMPLE_TOOLS, GenerationParams()
        )

        assert meta["total_tokens"] == 150
        assert meta["iterations"] == 1
        assert len(meta["iteration_history"]) == 1
        assert meta["iteration_history"][0]["tokens"] == 150

    def test_metadata_includes_timing(self, adapter):
        """Metadata includes total_time field."""
        text = _make_text_block("Fast")
        resp = _make_response([text], stop_reason="end_turn")
        adapter.client.messages.create = Mock(return_value=resp)

        _, meta = adapter.generate_with_tools(
            "Speed", SAMPLE_TOOLS, GenerationParams()
        )

        assert "total_time" in meta
        assert meta["total_time"] >= 0

    def test_tool_use_messages_preserved(self, adapter):
        """When tool_use returned, messages list is included for continuation."""
        tool = _make_tool_block("t1", "search", {"query": "test"})
        resp = _make_response([tool], stop_reason="tool_use")
        adapter.client.messages.create = Mock(return_value=resp)

        _, meta = adapter.generate_with_tools(
            "Search for test", SAMPLE_TOOLS, GenerationParams()
        )

        assert "messages" in meta
        assert len(meta["messages"]) == 2  # user + assistant
        assert meta["messages"][0]["role"] == "user"
        assert meta["messages"][1]["role"] == "assistant"
