"""Unit tests for MistralAdapter.

Mocks the Mistral client and all external dependencies.
No Mistral API key or network access required.
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from tenacity import RetryError

from components.generators.base import GenerationParams, LLMError
from components.generators.llm_adapters.base_adapter import (
    AuthenticationError,
    ModelNotFoundError,
    RateLimitError,
)

pytestmark = [pytest.mark.unit]

MODULE = "components.generators.llm_adapters.mistral_adapter"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_mistral_client():
    """Return a mock Mistral client with chat.complete wired up."""
    client = MagicMock()
    return client


@pytest.fixture
def _patch_imports(mock_mistral_client):
    """Patch MISTRAL_AVAILABLE, REQUESTS_AVAILABLE, and Mistral class."""
    with patch(f"{MODULE}.MISTRAL_AVAILABLE", True), \
         patch(f"{MODULE}.REQUESTS_AVAILABLE", True), \
         patch(f"{MODULE}.Mistral", return_value=mock_mistral_client):
        yield


@pytest.fixture
def adapter(_patch_imports):
    """MistralAdapter with mocked client."""
    from components.generators.llm_adapters.mistral_adapter import MistralAdapter
    return MistralAdapter(model_name="mistral-small", api_key="test-key-123")


@pytest.fixture
def params():
    return GenerationParams()


def _make_chat_response(content="Hello world", prompt_tokens=10, completion_tokens=20):
    """Build a mock Mistral chat.complete() response object."""
    choice = MagicMock()
    choice.message.role = "assistant"
    choice.message.content = content
    choice.finish_reason = "stop"

    usage = MagicMock()
    usage.prompt_tokens = prompt_tokens
    usage.completion_tokens = completion_tokens
    usage.total_tokens = prompt_tokens + completion_tokens

    resp = MagicMock()
    resp.id = "chatcmpl-test-123"
    resp.model = "mistral-small"
    resp.choices = [choice]
    resp.usage = usage
    resp.created = 1700000000
    return resp


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------

class TestInit:

    def test_success(self, adapter):
        assert adapter.model_name == "mistral-small"
        assert adapter._total_cost == Decimal("0.00")
        assert adapter._input_tokens == 0
        assert adapter._output_tokens == 0
        assert adapter.cost_history == []

    def test_no_api_key_raises(self, _patch_imports):
        from components.generators.llm_adapters.mistral_adapter import MistralAdapter
        with patch.dict("os.environ", {}, clear=True):
            # Remove MISTRAL_API_KEY from env if present
            import os
            os.environ.pop("MISTRAL_API_KEY", None)
            with pytest.raises(AuthenticationError, match="API key is required"):
                MistralAdapter(model_name="mistral-small", api_key=None)

    def test_mistral_unavailable_raises(self):
        with patch(f"{MODULE}.MISTRAL_AVAILABLE", False), \
             patch(f"{MODULE}.REQUESTS_AVAILABLE", True):
            from components.generators.llm_adapters.mistral_adapter import MistralAdapter
            with pytest.raises(ImportError, match="mistralai"):
                MistralAdapter(model_name="mistral-small", api_key="key")

    def test_requests_unavailable_raises(self):
        with patch(f"{MODULE}.MISTRAL_AVAILABLE", True), \
             patch(f"{MODULE}.REQUESTS_AVAILABLE", False):
            from components.generators.llm_adapters.mistral_adapter import MistralAdapter
            with pytest.raises(ImportError, match="requests"):
                MistralAdapter(model_name="mistral-small", api_key="key")

    def test_env_var_api_key(self, _patch_imports):
        from components.generators.llm_adapters.mistral_adapter import MistralAdapter
        with patch.dict("os.environ", {"MISTRAL_API_KEY": "env-key-456"}):
            a = MistralAdapter(model_name="mistral-small")
            assert a.model_name == "mistral-small"


# ---------------------------------------------------------------------------
# _make_request
# ---------------------------------------------------------------------------

class TestMakeRequest:

    def test_success(self, adapter, mock_mistral_client, params):
        mock_mistral_client.chat.complete.return_value = _make_chat_response()

        result = adapter._make_request("Tell me about AI", params)

        assert result["id"] == "chatcmpl-test-123"
        assert result["model"] == "mistral-small"
        assert result["choices"][0]["message"]["content"] == "Hello world"
        assert result["usage"]["prompt_tokens"] == 10
        assert result["usage"]["completion_tokens"] == 20
        assert "request_time" in result
        mock_mistral_client.chat.complete.assert_called_once()

    def test_rate_limit_429(self, adapter, mock_mistral_client, params):
        mock_mistral_client.chat.complete.side_effect = Exception("429 rate limit exceeded")

        # tenacity retries RateLimitError 5 times then wraps in RetryError
        with pytest.raises(RetryError):
            adapter._make_request("hello", params)

    def test_auth_error_401(self, adapter, mock_mistral_client, params):
        mock_mistral_client.chat.complete.side_effect = Exception("401 unauthorized")

        with pytest.raises(AuthenticationError, match="authentication"):
            adapter._make_request("hello", params)

    def test_not_found_404(self, adapter, mock_mistral_client, params):
        mock_mistral_client.chat.complete.side_effect = Exception("404 not found")

        with pytest.raises(ModelNotFoundError, match="not found"):
            adapter._make_request("hello", params)

    def test_generic_error(self, adapter, mock_mistral_client, params):
        mock_mistral_client.chat.complete.side_effect = Exception("something broke")

        with pytest.raises(LLMError, match="Mistral API error"):
            adapter._make_request("hello", params)

    def test_cost_tracking_populated(self, adapter, mock_mistral_client, params):
        mock_mistral_client.chat.complete.return_value = _make_chat_response(
            prompt_tokens=100, completion_tokens=50
        )

        result = adapter._make_request("test", params)

        assert "cost_breakdown" in result
        assert result["cost_breakdown"]["input_tokens"] == 100
        assert result["cost_breakdown"]["output_tokens"] == 50
        assert adapter._input_tokens == 100
        assert adapter._output_tokens == 50

    def test_params_forwarded(self, adapter, mock_mistral_client):
        mock_mistral_client.chat.complete.return_value = _make_chat_response()
        p = GenerationParams(temperature=0.3, max_tokens=256, top_p=0.9, stop_sequences=["END"])

        adapter._make_request("test", p)

        call_kwargs = mock_mistral_client.chat.complete.call_args[1]
        assert call_kwargs["temperature"] == 0.3
        assert call_kwargs["max_tokens"] == 256
        assert call_kwargs["top_p"] == 0.9
        assert call_kwargs["stop"] == ["END"]


# ---------------------------------------------------------------------------
# _parse_response
# ---------------------------------------------------------------------------

class TestParseResponse:

    def test_extracts_content(self, adapter):
        resp = {
            "choices": [{"message": {"content": "  The answer is 42  "}, "finish_reason": "stop"}]
        }
        assert adapter._parse_response(resp) == "The answer is 42"

    def test_empty_content_raises(self, adapter):
        resp = {"choices": [{"message": {"content": ""}, "finish_reason": "stop"}]}
        with pytest.raises(LLMError, match="Empty content"):
            adapter._parse_response(resp)

    def test_no_choices_raises(self, adapter):
        with pytest.raises(LLMError, match="No choices"):
            adapter._parse_response({"choices": []})

    def test_missing_choices_key_raises(self, adapter):
        with pytest.raises(LLMError, match="No choices"):
            adapter._parse_response({})


# ---------------------------------------------------------------------------
# generate_streaming
# ---------------------------------------------------------------------------

class TestGenerateStreaming:

    def test_yields_single_chunk(self, adapter, mock_mistral_client, params):
        mock_mistral_client.chat.complete.return_value = _make_chat_response("streamed text")

        chunks = list(adapter.generate_streaming("hello", params))
        assert len(chunks) == 1
        assert "streamed text" in chunks[0]


# ---------------------------------------------------------------------------
# Simple properties
# ---------------------------------------------------------------------------

class TestSimpleMethods:

    def test_get_provider_name(self, adapter):
        assert adapter._get_provider_name() == "Mistral"

    def test_supports_streaming_false(self, adapter):
        assert adapter._supports_streaming() is False

    def test_get_max_tokens_known_model(self, adapter):
        assert adapter._get_max_tokens() == 32000

    def test_get_max_tokens_unknown_model(self, _patch_imports):
        from components.generators.llm_adapters.mistral_adapter import MistralAdapter
        a = MistralAdapter(model_name="mistral-custom", api_key="key")
        assert a._get_max_tokens() is None


# ---------------------------------------------------------------------------
# Cost tracking
# ---------------------------------------------------------------------------

class TestCostTracking:

    def test_track_usage_with_breakdown(self, adapter):
        usage = {"prompt_tokens": 1000, "completion_tokens": 500, "total_tokens": 1500}
        breakdown = adapter._track_usage_with_breakdown(usage)

        assert breakdown["input_tokens"] == 1000
        assert breakdown["output_tokens"] == 500
        assert breakdown["total_tokens"] == 1500
        assert breakdown["model"] == "mistral-small"
        # mistral-small: input $0.002/1K, output $0.006/1K
        # 1000 input -> 0.002, 500 output -> 0.003
        assert breakdown["input_cost_usd"] == pytest.approx(0.002, abs=1e-6)
        assert breakdown["output_cost_usd"] == pytest.approx(0.003, abs=1e-6)
        assert breakdown["total_cost_usd"] == pytest.approx(0.005, abs=1e-6)
        assert adapter._total_cost == Decimal("0.005000")

    def test_track_usage_accumulates(self, adapter):
        usage = {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        adapter._track_usage_with_breakdown(usage)
        adapter._track_usage_with_breakdown(usage)

        assert adapter._input_tokens == 200
        assert adapter._output_tokens == 100
        assert len(adapter.cost_history) == 2

    def test_get_cost_breakdown(self, adapter, mock_mistral_client, params):
        # Simulate a request to bump _request_count via base class generate()
        mock_mistral_client.chat.complete.return_value = _make_chat_response(
            prompt_tokens=500, completion_tokens=200
        )
        adapter.generate("test prompt", params)

        breakdown = adapter.get_cost_breakdown()
        assert breakdown["model"] == "mistral-small"
        assert breakdown["input_tokens"] == 500
        assert breakdown["output_tokens"] == 200
        assert breakdown["total_requests"] == 1
        assert "pricing_per_1k" in breakdown

    def test_get_cost_breakdown_unknown_model(self, _patch_imports):
        from components.generators.llm_adapters.mistral_adapter import MistralAdapter
        a = MistralAdapter(model_name="mistral-custom", api_key="key")
        result = a.get_cost_breakdown()
        assert "error" in result

    def test_get_cost_summary_empty(self, adapter):
        summary = adapter.get_cost_summary()
        assert summary["total_cost_usd"] == 0.0
        assert summary["total_requests"] == 0
        assert summary["total_tokens"] == 0

    def test_get_cost_summary_populated(self, adapter):
        adapter._track_usage_with_breakdown(
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        )
        summary = adapter.get_cost_summary()
        assert summary["total_requests"] == 1
        assert summary["total_tokens"] == 150
        assert summary["total_cost_usd"] > 0
        assert summary["model"] == "mistral-small"
        assert "cost_breakdown" in summary

    def test_estimate_cost(self, adapter):
        # "hello world" = 11 chars -> 11//4 = 2 input tokens
        est = adapter.estimate_cost("hello world", max_output_tokens=100)
        assert est["estimated_input_tokens"] == 2
        assert est["estimated_output_tokens"] == 100
        assert est["estimated_total_tokens"] == 102
        assert est["model"] == "mistral-small"
        assert est["estimated_total_cost_usd"] > 0
        assert "note" in est


# ---------------------------------------------------------------------------
# get_model_info
# ---------------------------------------------------------------------------

class TestGetModelInfo:

    def test_includes_mistral_fields(self, adapter):
        info = adapter.get_model_info()

        assert info["provider"] == "Mistral"
        assert info["model"] == "mistral-small"
        assert info["max_context_tokens"] == 32000
        assert info["supports_streaming"] is False
        assert info["input_tokens_used"] == 0
        assert info["output_tokens_used"] == 0
        assert info["total_cost_usd"] == 0.0
        assert "pricing_per_1m_tokens" in info
