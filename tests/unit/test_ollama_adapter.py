"""Unit tests for OllamaAdapter.

Mocks all HTTP calls via requests. No Ollama server required.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from components.generators.llm_adapters.ollama_adapter import OllamaAdapter
from components.generators.base import GenerationParams, LLMError
from components.generators.llm_adapters.base_adapter import ModelNotFoundError

pytestmark = [pytest.mark.unit]

PATCH_REQUESTS = "components.generators.llm_adapters.ollama_adapter.requests"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def adapter():
    """OllamaAdapter with defaults, env var ignored."""
    return OllamaAdapter(
        model_name="llama3.2:3b",
        base_url="http://localhost:11434",
    )


@pytest.fixture
def params():
    """Default GenerationParams for tests."""
    return GenerationParams()


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------

class TestInit:

    def test_default_model_name(self, adapter):
        assert adapter.model_name == "llama3.2:3b"

    def test_default_url(self, adapter):
        assert adapter.base_url == "http://localhost:11434"

    def test_custom_url(self):
        a = OllamaAdapter(base_url="http://gpu-box:11434")
        assert a.base_url == "http://gpu-box:11434"

    def test_trailing_slash_stripped(self):
        a = OllamaAdapter(base_url="http://localhost:11434/")
        assert a.base_url == "http://localhost:11434"

    def test_default_timeout(self, adapter):
        assert adapter.timeout == 120

    def test_auto_pull_default_false(self, adapter):
        assert adapter.auto_pull is False

    def test_endpoints_constructed(self, adapter):
        assert adapter.generate_url == "http://localhost:11434/api/generate"
        assert adapter.tags_url == "http://localhost:11434/api/tags"
        assert adapter.pull_url == "http://localhost:11434/api/pull"

    def test_env_var_fallback(self):
        with patch.dict("os.environ", {"OLLAMA_URL": "http://envhost:9999"}):
            a = OllamaAdapter()
            assert a.base_url == "http://envhost:9999"


# ---------------------------------------------------------------------------
# _make_request
# ---------------------------------------------------------------------------

class TestMakeRequest:

    @patch(PATCH_REQUESTS)
    def test_success(self, mock_requests, adapter, params):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"response": "hello", "done": True}
        mock_resp.raise_for_status = MagicMock()
        mock_requests.post.return_value = mock_resp

        result = adapter._make_request("say hi", params)
        assert result == {"response": "hello", "done": True}
        mock_requests.post.assert_called_once()

    @patch(PATCH_REQUESTS)
    def test_connection_error(self, mock_requests, adapter, params):
        mock_requests.post.side_effect = requests.exceptions.ConnectionError("refused")
        mock_requests.exceptions = requests.exceptions

        with pytest.raises(LLMError, match="Failed to connect"):
            adapter._make_request("hello", params)

    @patch(PATCH_REQUESTS)
    def test_timeout_error(self, mock_requests, adapter, params):
        mock_requests.post.side_effect = requests.exceptions.Timeout("timed out")
        mock_requests.exceptions = requests.exceptions

        with pytest.raises(LLMError, match="timed out"):
            adapter._make_request("hello", params)

    @patch(PATCH_REQUESTS)
    def test_404_no_auto_pull_raises(self, mock_requests, adapter, params):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_requests.post.return_value = mock_resp
        mock_requests.exceptions = requests.exceptions

        with pytest.raises(ModelNotFoundError, match="not found"):
            adapter._make_request("hello", params)

    @patch(PATCH_REQUESTS)
    def test_404_with_auto_pull_retries(self, mock_requests, params):
        adapter = OllamaAdapter(
            model_name="llama3.2:3b",
            base_url="http://localhost:11434",
            auto_pull=True,
        )
        # First call returns 404; pull succeeds; retry returns 200
        first_resp = MagicMock()
        first_resp.status_code = 404
        pull_resp = MagicMock()
        pull_resp.raise_for_status = MagicMock()
        retry_resp = MagicMock()
        retry_resp.status_code = 200
        retry_resp.json.return_value = {"response": "ok"}
        retry_resp.raise_for_status = MagicMock()

        mock_requests.post.side_effect = [first_resp, pull_resp, retry_resp]
        mock_requests.exceptions = requests.exceptions

        result = adapter._make_request("hello", params)
        assert result == {"response": "ok"}
        assert mock_requests.post.call_count == 3

    @patch(PATCH_REQUESTS)
    def test_http_error_delegates_to_handler(self, mock_requests, adapter, params):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=MagicMock(status_code=500, text="internal error")
        )
        mock_requests.post.return_value = mock_resp
        mock_requests.exceptions = requests.exceptions

        with pytest.raises(LLMError, match="Ollama server error"):
            adapter._make_request("hello", params)


# ---------------------------------------------------------------------------
# _parse_response
# ---------------------------------------------------------------------------

class TestParseResponse:

    def test_extracts_response_field(self, adapter):
        assert adapter._parse_response({"response": "the answer"}) == "the answer"

    def test_missing_response_returns_empty(self, adapter):
        assert adapter._parse_response({}) == ""

    def test_logs_eval_count(self, adapter):
        # Should not raise; just exercises the eval_count branch
        result = adapter._parse_response({"response": "ok", "eval_count": 42})
        assert result == "ok"


# ---------------------------------------------------------------------------
# generate_streaming
# ---------------------------------------------------------------------------

class TestGenerateStreaming:

    @patch(PATCH_REQUESTS)
    def test_yields_chunks_until_done(self, mock_requests, adapter, params):
        lines = [
            json.dumps({"response": "Hello", "done": False}).encode(),
            json.dumps({"response": " world", "done": True}).encode(),
        ]
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.iter_lines.return_value = iter(lines)
        mock_requests.post.return_value = mock_resp

        chunks = list(adapter.generate_streaming("greet", params))
        assert chunks == ["Hello", " world"]

    @patch(PATCH_REQUESTS)
    def test_skips_empty_lines(self, mock_requests, adapter, params):
        lines = [
            b"",
            json.dumps({"response": "hi", "done": True}).encode(),
        ]
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.iter_lines.return_value = iter(lines)
        mock_requests.post.return_value = mock_resp

        chunks = list(adapter.generate_streaming("greet", params))
        assert chunks == ["hi"]

    @patch(PATCH_REQUESTS)
    def test_malformed_json_skipped(self, mock_requests, adapter, params):
        lines = [
            b"not json",
            json.dumps({"response": "ok", "done": True}).encode(),
        ]
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.iter_lines.return_value = iter(lines)
        mock_requests.post.return_value = mock_resp

        chunks = list(adapter.generate_streaming("greet", params))
        assert chunks == ["ok"]

    @patch(PATCH_REQUESTS)
    def test_provider_error_raises(self, mock_requests, adapter, params):
        mock_requests.post.side_effect = Exception("connection reset")

        with pytest.raises(LLMError):
            list(adapter.generate_streaming("greet", params))


# ---------------------------------------------------------------------------
# _validate_model
# ---------------------------------------------------------------------------

class TestValidateModel:

    @patch(PATCH_REQUESTS)
    def test_model_found_exact(self, mock_requests, adapter):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "models": [{"name": "llama3.2:3b"}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        assert adapter._validate_model() is True

    @patch(PATCH_REQUESTS)
    def test_model_found_partial(self, mock_requests, adapter):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "models": [{"name": "llama3.2:latest"}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        # "llama3.2" is in "llama3.2:latest" → match
        adapter_short = OllamaAdapter(
            model_name="llama3.2",
            base_url="http://localhost:11434",
        )
        mock_requests.get.return_value = mock_resp
        assert adapter_short._validate_model() is True

    @patch(PATCH_REQUESTS)
    def test_model_not_found(self, mock_requests, adapter):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "models": [{"name": "mistral:latest"}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        assert adapter._validate_model() is False

    @patch(PATCH_REQUESTS)
    def test_exception_returns_true(self, mock_requests, adapter):
        mock_requests.get.side_effect = Exception("network error")
        # Assumes model exists if validation fails
        assert adapter._validate_model() is True


# ---------------------------------------------------------------------------
# _pull_model
# ---------------------------------------------------------------------------

class TestPullModel:

    @patch(PATCH_REQUESTS)
    def test_success(self, mock_requests, adapter):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_requests.post.return_value = mock_resp

        adapter._pull_model()  # Should not raise
        mock_requests.post.assert_called_once()
        call_kwargs = mock_requests.post.call_args
        assert call_kwargs[1]["json"]["name"] == "llama3.2:3b"

    @patch(PATCH_REQUESTS)
    def test_failure_raises(self, mock_requests, adapter):
        mock_requests.post.side_effect = Exception("disk full")

        with pytest.raises(LLMError, match="Failed to pull"):
            adapter._pull_model()


# ---------------------------------------------------------------------------
# Simple properties / methods
# ---------------------------------------------------------------------------

class TestSimpleMethods:

    def test_get_provider_name(self, adapter):
        assert adapter._get_provider_name() == "Ollama"

    def test_supports_streaming(self, adapter):
        assert adapter._supports_streaming() is True


# ---------------------------------------------------------------------------
# _get_max_tokens
# ---------------------------------------------------------------------------

class TestGetMaxTokens:

    @pytest.mark.parametrize("model,expected", [
        ("llama3.2:3b", 4096),
        ("llama3.1:70b", 128000),
        ("llama3:latest", 8192),
        ("llama2:7b", 4096),
        ("mistral:latest", 8192),
        ("mixtral:8x7b", 32768),
        ("gemma:2b", 8192),
        ("gemma2:9b", 8192),
        ("phi3:mini", 4096),
        ("qwen2.5:7b", 32768),
    ])
    def test_known_models(self, model, expected):
        a = OllamaAdapter(model_name=model, base_url="http://localhost:11434")
        assert a._get_max_tokens() == expected

    def test_unknown_model_default(self):
        a = OllamaAdapter(model_name="custom-finetuned:v1", base_url="http://localhost:11434")
        assert a._get_max_tokens() == 4096


# ---------------------------------------------------------------------------
# _convert_params
# ---------------------------------------------------------------------------

class TestConvertParams:

    def test_all_params(self, adapter):
        params = GenerationParams(
            temperature=0.5,
            max_tokens=256,
            top_p=0.9,
            frequency_penalty=0.3,
            stop_sequences=["END"],
        )
        result = adapter._convert_params(params)
        assert result["temperature"] == 0.5
        assert result["num_predict"] == 256
        assert result["top_p"] == 0.9
        assert result["repeat_penalty"] == 1.3
        assert result["stop"] == ["END"]

    def test_defaults_added(self, adapter):
        params = GenerationParams()
        result = adapter._convert_params(params)
        assert "seed" in result
        assert "num_ctx" in result
        assert result["num_ctx"] == 2048

    def test_none_params_excluded(self, adapter):
        params = GenerationParams(
            temperature=None,
            max_tokens=None,
            top_p=None,
            frequency_penalty=None,
            stop_sequences=None,
        )
        result = adapter._convert_params(params)
        # Only the defaults should be present
        assert "temperature" not in result
        assert "num_predict" not in result


# ---------------------------------------------------------------------------
# _handle_http_error
# ---------------------------------------------------------------------------

class TestHandleHttpError:

    def _make_http_error(self, status_code, text="error body"):
        resp = MagicMock()
        resp.status_code = status_code
        resp.text = text
        error = requests.exceptions.HTTPError(response=resp)
        error.response = resp
        return error

    def test_404_raises_model_not_found(self, adapter):
        with pytest.raises(ModelNotFoundError):
            adapter._handle_http_error(self._make_http_error(404))

    def test_400_raises_llm_error(self, adapter):
        with pytest.raises(LLMError, match="Bad request"):
            adapter._handle_http_error(self._make_http_error(400))

    def test_500_raises_llm_error(self, adapter):
        with pytest.raises(LLMError, match="server error"):
            adapter._handle_http_error(self._make_http_error(500))

    def test_other_status_raises_llm_error(self, adapter):
        with pytest.raises(LLMError, match="HTTP error 503"):
            adapter._handle_http_error(self._make_http_error(503))


# ---------------------------------------------------------------------------
# _handle_provider_error
# ---------------------------------------------------------------------------

class TestHandleProviderError:

    def test_connection_error(self, adapter):
        with pytest.raises(LLMError, match="Cannot connect"):
            adapter._handle_provider_error(Exception("connection refused"))

    def test_timeout_error(self, adapter):
        with pytest.raises(LLMError, match="timed out"):
            adapter._handle_provider_error(Exception("request timeout"))

    def test_model_not_found_error(self, adapter):
        with pytest.raises(ModelNotFoundError):
            adapter._handle_provider_error(Exception("model xyz not found"))

    def test_generic_error_falls_through_to_base(self, adapter):
        with pytest.raises(LLMError, match="Provider error"):
            adapter._handle_provider_error(Exception("something unexpected"))
