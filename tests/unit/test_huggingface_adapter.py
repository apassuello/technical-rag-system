"""Unit tests for HuggingFaceAdapter.

Mocks InferenceClient and HF_HUB_AVAILABLE. No HuggingFace API calls.
"""

from unittest.mock import MagicMock, patch

import pytest

from components.generators.base import GenerationParams, LLMError
from components.generators.llm_adapters.base_adapter import (
    AuthenticationError,
    ModelNotFoundError,
    RateLimitError,
)

pytestmark = [pytest.mark.unit]

MODULE = "components.generators.llm_adapters.huggingface_adapter"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_client():
    """Pre-configured mock InferenceClient."""
    return MagicMock(name="InferenceClient")


@pytest.fixture
def adapter(mock_client):
    """HuggingFaceAdapter with dummy token (skips _test_connection)."""
    with patch(f"{MODULE}.HF_HUB_AVAILABLE", True), \
         patch(f"{MODULE}.InferenceClient", return_value=mock_client):
        from components.generators.llm_adapters.huggingface_adapter import (
            HuggingFaceAdapter,
        )
        a = HuggingFaceAdapter(
            model_name="microsoft/DialoGPT-medium",
            api_token="dummy_test_token",
        )
    return a


@pytest.fixture
def params():
    return GenerationParams()


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------

class TestInit:

    def test_with_token(self, adapter):
        assert adapter.api_token == "dummy_test_token"
        assert adapter.model_name == "microsoft/DialoGPT-medium"

    def test_without_token_raises(self):
        with patch(f"{MODULE}.HF_HUB_AVAILABLE", True), \
             patch.dict("os.environ", {}, clear=True):
            from components.generators.llm_adapters.huggingface_adapter import (
                HuggingFaceAdapter,
            )
            with pytest.raises(AuthenticationError, match="API token required"):
                HuggingFaceAdapter(model_name="test-model", api_token=None)

    def test_import_unavailable_raises(self):
        with patch(f"{MODULE}.HF_HUB_AVAILABLE", False):
            from components.generators.llm_adapters.huggingface_adapter import (
                HuggingFaceAdapter,
            )
            with pytest.raises(ImportError, match="huggingface_hub is required"):
                HuggingFaceAdapter(model_name="test-model", api_token="tok123")

    def test_dummy_token_skips_connection_test(self, mock_client):
        with patch(f"{MODULE}.HF_HUB_AVAILABLE", True), \
             patch(f"{MODULE}.InferenceClient", return_value=mock_client):
            from components.generators.llm_adapters.huggingface_adapter import (
                HuggingFaceAdapter,
            )
            a = HuggingFaceAdapter(
                model_name="test-model",
                api_token="dummy_skip",
            )
            # _test_connection not called, so client methods untouched
            mock_client.chat_completion.assert_not_called()
            mock_client.text_generation.assert_not_called()
            assert a.model_name == "test-model"

    def test_non_dummy_token_calls_test_connection(self, mock_client):
        """Non-dummy token triggers _test_connection → _validate_model."""
        # _validate_model will call chat_completion; make it succeed
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "ok"
        mock_client.chat_completion.return_value = mock_response

        with patch(f"{MODULE}.HF_HUB_AVAILABLE", True), \
             patch(f"{MODULE}.InferenceClient", return_value=mock_client):
            from components.generators.llm_adapters.huggingface_adapter import (
                HuggingFaceAdapter,
            )
            a = HuggingFaceAdapter(
                model_name="microsoft/DialoGPT-medium",
                api_token="hf_real_token",
            )
            # chat_completion was called by _test_connection → _validate_model
            assert mock_client.chat_completion.called
            assert a.model_name == "microsoft/DialoGPT-medium"

    def test_env_var_fallback(self, mock_client):
        with patch(f"{MODULE}.HF_HUB_AVAILABLE", True), \
             patch(f"{MODULE}.InferenceClient", return_value=mock_client), \
             patch.dict("os.environ", {"HF_TOKEN": "dummy_env_token"}, clear=False):
            from components.generators.llm_adapters.huggingface_adapter import (
                HuggingFaceAdapter,
            )
            a = HuggingFaceAdapter(model_name="test-model")
            assert a.api_token == "dummy_env_token"


# ---------------------------------------------------------------------------
# _make_chat_completion_request
# ---------------------------------------------------------------------------

class TestMakeChatCompletionRequest:

    def test_success_with_choices(self, adapter, mock_client, params):
        mock_choice = MagicMock()
        mock_choice.message.content = "Generated answer"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = {"total_tokens": 42}
        mock_client.chat_completion.return_value = mock_response

        result = adapter._make_chat_completion_request("What is RAG?", params)

        assert result["content"] == "Generated answer"
        assert result["model"] == "microsoft/DialoGPT-medium"
        assert result["response_type"] == "chat_completion"
        assert result["usage"] == {"total_tokens": 42}

    def test_fallback_generated_text(self, adapter, mock_client, params):
        """Response without choices but with generated_text attr."""
        mock_response = MagicMock()
        mock_response.choices = []  # empty
        mock_response.generated_text = "Fallback text"
        mock_client.chat_completion.return_value = mock_response

        result = adapter._make_chat_completion_request("prompt", params)
        assert result["content"] == "Fallback text"

    def test_fallback_str_conversion(self, adapter, mock_client, params):
        """Response without choices and without generated_text."""

        class BareResponse:
            """Response with no choices/generated_text."""
            choices = []

            def __str__(self):
                return "stringified response"

        mock_client.chat_completion.return_value = BareResponse()

        result = adapter._make_chat_completion_request("prompt", params)
        assert result["content"] == "stringified response"

    def test_exception_propagates(self, adapter, mock_client, params):
        mock_client.chat_completion.side_effect = Exception("API down")
        with pytest.raises(Exception, match="API down"):
            adapter._make_chat_completion_request("prompt", params)


# ---------------------------------------------------------------------------
# _make_text_generation_request
# ---------------------------------------------------------------------------

class TestMakeTextGenerationRequest:

    def test_success_string_response(self, adapter, mock_client, params):
        adapter.use_chat_completion = False
        mock_client.text_generation.return_value = "Plain text output"

        result = adapter._make_text_generation_request("prompt", params)

        assert result["content"] == "Plain text output"
        assert result["response_type"] == "text_generation"

    def test_success_object_response(self, adapter, mock_client, params):
        adapter.use_chat_completion = False
        mock_resp = MagicMock()
        mock_resp.generated_text = "Object text output"
        mock_client.text_generation.return_value = mock_resp

        result = adapter._make_text_generation_request("prompt", params)
        assert result["content"] == "Object text output"

    def test_exception_propagates(self, adapter, mock_client, params):
        adapter.use_chat_completion = False
        mock_client.text_generation.side_effect = RuntimeError("boom")
        with pytest.raises(RuntimeError, match="boom"):
            adapter._make_text_generation_request("prompt", params)


# ---------------------------------------------------------------------------
# _make_request — fallback models
# ---------------------------------------------------------------------------

class TestMakeRequestFallback:

    def test_fallback_on_primary_failure(self, mock_client, params):
        with patch(f"{MODULE}.HF_HUB_AVAILABLE", True), \
             patch(f"{MODULE}.InferenceClient", return_value=mock_client):
            from components.generators.llm_adapters.huggingface_adapter import (
                HuggingFaceAdapter,
            )
            a = HuggingFaceAdapter(
                model_name="primary-model",
                api_token="dummy_test",
                fallback_models=["fallback-model"],
            )

        # Primary fails, fallback succeeds
        mock_choice = MagicMock()
        mock_choice.message.content = "fallback answer"
        mock_ok = MagicMock()
        mock_ok.choices = [mock_choice]
        mock_ok.usage = {}
        mock_client.chat_completion.side_effect = [
            Exception("primary down"),
            mock_ok,
        ]

        result = a._make_request("test", params)
        assert result["content"] == "fallback answer"

    def test_all_models_fail_raises(self, mock_client, params):
        with patch(f"{MODULE}.HF_HUB_AVAILABLE", True), \
             patch(f"{MODULE}.InferenceClient", return_value=mock_client):
            from components.generators.llm_adapters.huggingface_adapter import (
                HuggingFaceAdapter,
            )
            a = HuggingFaceAdapter(
                model_name="primary-model",
                api_token="dummy_test",
                fallback_models=["fallback-1"],
            )

        mock_client.chat_completion.side_effect = Exception("rate limit hit 429")

        with pytest.raises(RateLimitError):
            a._make_request("test", params)


# ---------------------------------------------------------------------------
# _parse_response
# ---------------------------------------------------------------------------

class TestParseResponse:

    def test_extracts_content(self, adapter):
        assert adapter._parse_response({"content": "hello"}) == "hello"

    def test_missing_content_returns_empty(self, adapter):
        assert adapter._parse_response({}) == ""

    def test_usage_logging(self, adapter):
        result = adapter._parse_response({
            "content": "ok",
            "usage": {"total_tokens": 100},
        })
        assert result == "ok"


# ---------------------------------------------------------------------------
# generate_streaming
# ---------------------------------------------------------------------------

class TestGenerateStreaming:

    def test_yields_chunks(self, adapter, mock_client, params):
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta.content = "Hello"

        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta.content = " world"

        mock_client.chat_completion.return_value = iter([chunk1, chunk2])

        chunks = list(adapter.generate_streaming("greet", params))
        assert chunks == ["Hello", " world"]

    def test_skips_empty_delta(self, adapter, mock_client, params):
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta.content = "data"

        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta.content = None  # empty

        mock_client.chat_completion.return_value = iter([chunk1, chunk2])

        chunks = list(adapter.generate_streaming("greet", params))
        assert chunks == ["data"]

    def test_fallback_on_error(self, adapter, mock_client, params):
        """On streaming error, falls back to non-streaming generate()."""
        mock_client.chat_completion.side_effect = Exception("stream failed")

        # Patch generate to return known value (avoids retry loops)
        with patch.object(adapter, "generate", return_value="non-stream result"):
            chunks = list(adapter.generate_streaming("greet", params))
        assert chunks == ["non-stream result"]

    def test_text_gen_mode_uses_generate(self, adapter, params):
        """When use_chat_completion is False, yields generate() result."""
        adapter.use_chat_completion = False
        with patch.object(adapter, "generate", return_value="text gen result"):
            chunks = list(adapter.generate_streaming("greet", params))
        assert chunks == ["text gen result"]


# ---------------------------------------------------------------------------
# _validate_model
# ---------------------------------------------------------------------------

class TestValidateModel:

    def test_success_chat(self, adapter, mock_client):
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = "ok"
        mock_client.chat_completion.return_value = mock_resp

        assert adapter._validate_model() is True

    def test_success_text_gen(self, adapter, mock_client):
        adapter.use_chat_completion = False
        mock_client.text_generation.return_value = "ok"

        assert adapter._validate_model() is True

    def test_failure_returns_false(self, adapter, mock_client):
        mock_client.chat_completion.side_effect = Exception("not found")
        assert adapter._validate_model() is False


# ---------------------------------------------------------------------------
# Simple properties
# ---------------------------------------------------------------------------

class TestSimpleMethods:

    def test_get_provider_name(self, adapter):
        assert adapter._get_provider_name() == "HuggingFace"

    def test_supports_streaming_chat(self, adapter):
        adapter.use_chat_completion = True
        assert adapter._supports_streaming() is True

    def test_supports_streaming_text_gen(self, adapter):
        adapter.use_chat_completion = False
        assert adapter._supports_streaming() is False


# ---------------------------------------------------------------------------
# _get_max_tokens
# ---------------------------------------------------------------------------

class TestGetMaxTokens:

    @pytest.mark.parametrize("model,expected", [
        ("microsoft/DialoGPT-medium", 1024),
        ("google/gemma-2-2b-it", 8192),
        ("Qwen/Qwen2.5-1.5B-Instruct", 32768),
        ("google/flan-t5-small", 512),
        ("facebook/bart-base", 1024),
    ])
    def test_known_models(self, adapter, model, expected):
        adapter.model_name = model
        assert adapter._get_max_tokens() == expected

    def test_unknown_model_default(self, adapter):
        adapter.model_name = "custom/unknown-model"
        assert adapter._get_max_tokens() == 1024


# ---------------------------------------------------------------------------
# _handle_provider_error
# ---------------------------------------------------------------------------

class TestHandleProviderError:

    def test_rate_limit(self, adapter):
        with pytest.raises(RateLimitError, match="rate limit"):
            adapter._handle_provider_error(Exception("rate limit exceeded"))

    def test_rate_limit_429(self, adapter):
        with pytest.raises(RateLimitError):
            adapter._handle_provider_error(Exception("HTTP 429"))

    def test_unauthorized(self, adapter):
        with pytest.raises(AuthenticationError, match="authentication"):
            adapter._handle_provider_error(Exception("unauthorized access"))

    def test_not_found(self, adapter):
        with pytest.raises(ModelNotFoundError, match="not found"):
            adapter._handle_provider_error(Exception("model not found"))

    def test_timeout(self, adapter):
        with pytest.raises(LLMError, match="timed out"):
            adapter._handle_provider_error(Exception("request timeout"))

    def test_connection(self, adapter):
        with pytest.raises(LLMError, match="connect"):
            adapter._handle_provider_error(Exception("connection refused"))

    def test_generic(self, adapter):
        with pytest.raises(LLMError, match="API error"):
            adapter._handle_provider_error(Exception("something unexpected"))
