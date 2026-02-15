"""Unit tests for LlamaAdapter.

Mocks the OpenAI client and all external dependencies.
No llama-server or network access required.
"""

import os
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from components.generators.base import GenerationParams, LLMError
from components.generators.llm_adapters.base_adapter import (
    AuthenticationError,
    ModelNotFoundError,
    RateLimitError,
)

pytestmark = [pytest.mark.unit]

MODULE = "components.generators.llm_adapters.llama_adapter"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_openai_client():
    """Return a mock OpenAI client with chat.completions wired up."""
    client = MagicMock()
    return client


PARENT_MODULE = "components.generators.llm_adapters.openai_adapter"


@pytest.fixture
def _patch_imports(mock_openai_client):
    """Patch OPENAI_AVAILABLE, OpenAI class, and tiktoken in both modules.

    LlamaAdapter inherits from OpenAIAdapter, so the actual OpenAI()
    call is in openai_adapter — we must patch there too.
    """
    mock_tiktoken = MagicMock()
    mock_tiktoken.encoding_for_model.side_effect = KeyError("unknown model")
    mock_tiktoken.get_encoding.return_value = MagicMock()

    mock_openai_cls = MagicMock(return_value=mock_openai_client)

    with patch(f"{MODULE}.OPENAI_AVAILABLE", True), \
         patch(f"{PARENT_MODULE}.OPENAI_AVAILABLE", True), \
         patch(f"{PARENT_MODULE}.OpenAI", mock_openai_cls), \
         patch(f"{PARENT_MODULE}.tiktoken", mock_tiktoken):
        yield mock_openai_cls


@pytest.fixture
def adapter(_patch_imports):
    """LlamaAdapter with mocked client."""
    from components.generators.llm_adapters.llama_adapter import LlamaAdapter
    return LlamaAdapter()


@pytest.fixture
def params():
    return GenerationParams()


def _make_chat_response(content="Hello world", prompt_tokens=10, completion_tokens=20):
    """Build a mock OpenAI chat.completions.create() response object."""
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
    resp.model = "qwen2.5-1.5b-instruct"
    resp.choices = [choice]
    resp.usage = usage
    resp.created = 1700000000
    return resp


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------

class TestInit:

    def test_defaults_from_local_config(self, adapter):
        """LlamaAdapter defaults come from LOCAL config, not hardcoded values."""
        from config.llm_providers import LOCAL
        assert adapter.model_name == LOCAL.model

    def test_explicit_overrides(self, _patch_imports):
        from components.generators.llm_adapters.llama_adapter import LlamaAdapter
        a = LlamaAdapter(
            model_name="my-custom-model",
            base_url="http://otherhost:8080/v1",
        )
        assert a.model_name == "my-custom-model"

    def test_no_api_key_needed(self, _patch_imports):
        """LlamaAdapter should NOT raise when no API key is provided."""
        # Ensure no OPENAI_API_KEY in env
        with patch.dict("os.environ", {}, clear=True):
            os.environ.pop("OPENAI_API_KEY", None)
            from components.generators.llm_adapters.llama_adapter import LlamaAdapter
            a = LlamaAdapter()
            assert a.api_key == "local"

    def test_base_url_passed_to_client(self, _patch_imports):
        """The base_url must be forwarded to the OpenAI client constructor."""
        mock_openai_cls = _patch_imports
        from components.generators.llm_adapters.llama_adapter import LlamaAdapter
        LlamaAdapter(base_url="http://myhost:9999/v1")
        call_kwargs = mock_openai_cls.call_args
        assert call_kwargs is not None
        assert call_kwargs.kwargs.get("base_url") == "http://myhost:9999/v1"

    def test_cost_tracking_always_zero(self, adapter):
        assert adapter._total_cost == Decimal("0.00")
        assert adapter.MODEL_PRICING == {}
        assert adapter.MODEL_LIMITS == {}


# ---------------------------------------------------------------------------
# Provider name
# ---------------------------------------------------------------------------

class TestProviderName:

    def test_returns_llama_server(self, adapter):
        assert adapter._get_provider_name() == "llama-server"


# ---------------------------------------------------------------------------
# Validate model — uses /health on the base server
# ---------------------------------------------------------------------------

class TestValidateModel:

    def test_health_check_success(self, adapter):
        with patch(f"{MODULE}.requests") as mock_requests:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_requests.get.return_value = mock_resp
            assert adapter._validate_model() is True
            # Should call the base server /health, not /v1/health
            call_url = mock_requests.get.call_args[0][0]
            assert "/v1" not in call_url
            assert call_url.endswith("/health")

    def test_health_check_failure(self, adapter):
        with patch(f"{MODULE}.requests") as mock_requests:
            mock_resp = MagicMock()
            mock_resp.status_code = 503
            mock_requests.get.return_value = mock_resp
            assert adapter._validate_model() is False

    def test_health_check_connection_error(self, adapter):
        with patch(f"{MODULE}.requests") as mock_requests:
            mock_requests.get.side_effect = ConnectionError("refused")
            assert adapter._validate_model() is False

    def test_health_check_timeout(self, adapter):
        with patch(f"{MODULE}.requests") as mock_requests:
            mock_requests.get.side_effect = TimeoutError("timed out")
            assert adapter._validate_model() is False


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestRegistration:

    def test_local_in_registry(self):
        from components.generators.llm_adapters import ADAPTER_REGISTRY
        assert "local" in ADAPTER_REGISTRY

    def test_get_adapter_class_returns_llama(self):
        from components.generators.llm_adapters import get_adapter_class
        from components.generators.llm_adapters.llama_adapter import LlamaAdapter
        assert get_adapter_class("local") is LlamaAdapter


# ---------------------------------------------------------------------------
# get_model_info
# ---------------------------------------------------------------------------

class TestGetModelInfo:

    def test_provider_is_llama_server(self, adapter):
        info = adapter.get_model_info()
        assert info["provider"] == "llama-server"

    def test_model_from_local_config(self, adapter):
        from config.llm_providers import LOCAL
        info = adapter.get_model_info()
        assert info["model"] == LOCAL.model


# ---------------------------------------------------------------------------
# Cost tracking — always zero for local
# ---------------------------------------------------------------------------

class TestCostTracking:

    def test_track_usage_zero_cost(self, adapter):
        usage = {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        breakdown = adapter._track_usage_with_breakdown(usage)
        assert breakdown["input_cost_usd"] == 0.0
        assert breakdown["output_cost_usd"] == 0.0
        assert breakdown["total_cost_usd"] == 0.0
        # Tokens still tracked
        assert breakdown["input_tokens"] == 100
        assert breakdown["output_tokens"] == 50
