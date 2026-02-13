"""Unit tests for OpenAIAdapter.

Mocks all OpenAI API calls and tiktoken. No API key or network required.
Covers: init, response parsing, streaming, cost tracking, function calling,
        continue_with_function_results, error handling.
"""

import json
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# Patch path prefix (no src. prefix — conftest adds src/ to sys.path)
_MOD = "components.generators.llm_adapters.openai_adapter"

pytestmark = [pytest.mark.unit]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_openai_response(
    content="Hello from GPT",
    finish_reason="stop",
    prompt_tokens=10,
    completion_tokens=5,
    tool_calls=None,
    response_id="chatcmpl-abc123",
    model="gpt-3.5-turbo",
):
    """Build a mock OpenAI ChatCompletion response object."""
    message = MagicMock()
    message.role = "assistant"
    message.content = content
    message.tool_calls = tool_calls

    choice = MagicMock()
    choice.message = message
    choice.finish_reason = finish_reason

    usage = MagicMock()
    usage.prompt_tokens = prompt_tokens
    usage.completion_tokens = completion_tokens
    usage.total_tokens = prompt_tokens + completion_tokens

    response = MagicMock()
    response.id = response_id
    response.model = model
    response.choices = [choice]
    response.usage = usage
    response.created = 1700000000

    return response


def _make_tool_call(call_id="call_1", name="calculator", arguments='{"expression":"2+2"}'):
    """Build a mock tool_call object as returned by the OpenAI SDK."""
    tc = MagicMock()
    tc.id = call_id
    tc.type = "function"
    tc.function = MagicMock()
    tc.function.name = name
    tc.function.arguments = arguments
    return tc


def _sample_tools():
    """Minimal tool schema list in OpenAI format."""
    return [
        {
            "type": "function",
            "function": {
                "name": "calculator",
                "description": "Evaluate math",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string"}
                    },
                    "required": ["expression"],
                },
            },
        }
    ]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_openai_class():
    """Patch OpenAI client constructor and OPENAI_AVAILABLE flag."""
    mock_client = MagicMock()
    with (
        patch(f"{_MOD}.OPENAI_AVAILABLE", True),
        patch(f"{_MOD}.OpenAI", return_value=mock_client) as mock_cls,
        patch(f"{_MOD}.tiktoken") as mock_tiktoken,
    ):
        mock_encoder = MagicMock()
        mock_encoder.encode.return_value = list(range(10))  # 10 tokens
        mock_tiktoken.encoding_for_model.return_value = mock_encoder
        yield mock_cls, mock_client, mock_tiktoken


@pytest.fixture
def adapter(mock_openai_class):
    """Return an OpenAIAdapter with a mocked client."""
    from components.generators.llm_adapters.openai_adapter import OpenAIAdapter
    a = OpenAIAdapter(model_name="gpt-3.5-turbo", api_key="sk-test-key")
    return a


@pytest.fixture
def params():
    from components.generators.base import GenerationParams
    return GenerationParams()


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------

class TestInit:

    def test_with_api_key(self, mock_openai_class):
        from components.generators.llm_adapters.openai_adapter import OpenAIAdapter
        a = OpenAIAdapter(model_name="gpt-3.5-turbo", api_key="sk-test")
        assert a.api_key == "sk-test"
        assert a.model_name == "gpt-3.5-turbo"

    def test_missing_key_raises(self, mock_openai_class):
        from components.generators.llm_adapters.openai_adapter import OpenAIAdapter
        with patch.dict("os.environ", {}, clear=True):
            # Remove OPENAI_API_KEY if present
            import os
            os.environ.pop("OPENAI_API_KEY", None)
            with pytest.raises(ValueError, match="API key required"):
                OpenAIAdapter(model_name="gpt-3.5-turbo")

    def test_openai_not_available(self):
        with patch(f"{_MOD}.OPENAI_AVAILABLE", False):
            from components.generators.llm_adapters.openai_adapter import OpenAIAdapter
            with pytest.raises(ImportError, match="OpenAI package not installed"):
                OpenAIAdapter(model_name="gpt-3.5-turbo", api_key="sk-test")

    def test_key_from_env(self, mock_openai_class):
        from components.generators.llm_adapters.openai_adapter import OpenAIAdapter
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-env-key"}):
            a = OpenAIAdapter(model_name="gpt-3.5-turbo")
            assert a.api_key == "sk-env-key"

    def test_key_from_config_dict(self, mock_openai_class):
        from components.generators.llm_adapters.openai_adapter import OpenAIAdapter
        with patch.dict("os.environ", {}, clear=True):
            import os
            os.environ.pop("OPENAI_API_KEY", None)
            a = OpenAIAdapter(
                model_name="gpt-3.5-turbo",
                config={"api_key": "sk-config-key"},
            )
            assert a.api_key == "sk-config-key"

    def test_unknown_model_warning(self, mock_openai_class):
        from components.generators.llm_adapters.openai_adapter import OpenAIAdapter
        # Should not raise; just logs a warning
        a = OpenAIAdapter(model_name="gpt-5-unknown", api_key="sk-test")
        assert a.model_name == "gpt-5-unknown"

    def test_base_url_and_org(self, mock_openai_class):
        mock_cls, _, _ = mock_openai_class
        from components.generators.llm_adapters.openai_adapter import OpenAIAdapter
        OpenAIAdapter(
            model_name="gpt-3.5-turbo",
            api_key="sk-test",
            base_url="https://custom.api/v1",
            organization="org-123",
        )
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["base_url"] == "https://custom.api/v1"
        assert call_kwargs["organization"] == "org-123"


# ---------------------------------------------------------------------------
# _parse_response
# ---------------------------------------------------------------------------

class TestParseResponse:

    def test_extracts_content(self, adapter):
        resp = {
            "choices": [{"message": {"content": "  answer  "}, "finish_reason": "stop"}]
        }
        assert adapter._parse_response(resp) == "answer"

    def test_no_choices_raises(self, adapter):
        from components.generators.base import LLMError
        with pytest.raises(LLMError, match="No choices"):
            adapter._parse_response({"choices": []})

    def test_empty_content_raises(self, adapter):
        from components.generators.base import LLMError
        resp = {"choices": [{"message": {"content": ""}, "finish_reason": "stop"}]}
        with pytest.raises(LLMError, match="Empty content"):
            adapter._parse_response(resp)

    def test_finish_reason_length_logged(self, adapter):
        resp = {
            "choices": [{"message": {"content": "truncated"}, "finish_reason": "length"}]
        }
        # Should not raise; exercises the warning branch
        assert adapter._parse_response(resp) == "truncated"

    def test_finish_reason_content_filter(self, adapter):
        resp = {
            "choices": [{"message": {"content": "filtered"}, "finish_reason": "content_filter"}]
        }
        assert adapter._parse_response(resp) == "filtered"


# ---------------------------------------------------------------------------
# Streaming
# ---------------------------------------------------------------------------

class TestGenerateStreaming:

    def test_yields_chunks(self, adapter, params):
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta = MagicMock()
        chunk1.choices[0].delta.content = "Hello"

        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta = MagicMock()
        chunk2.choices[0].delta.content = " world"

        adapter.client.chat.completions.create.return_value = iter([chunk1, chunk2])

        chunks = list(adapter.generate_streaming("greet", params))
        assert chunks == ["Hello", " world"]

    def test_none_content_skipped(self, adapter, params):
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta = MagicMock()
        chunk1.choices[0].delta.content = None

        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta = MagicMock()
        chunk2.choices[0].delta.content = "data"

        adapter.client.chat.completions.create.return_value = iter([chunk1, chunk2])

        chunks = list(adapter.generate_streaming("prompt", params))
        assert chunks == ["data"]

    def test_empty_choices_skipped(self, adapter, params):
        chunk1 = MagicMock()
        chunk1.choices = []

        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta = MagicMock()
        chunk2.choices[0].delta.content = "ok"

        adapter.client.chat.completions.create.return_value = iter([chunk1, chunk2])

        chunks = list(adapter.generate_streaming("prompt", params))
        assert chunks == ["ok"]

    def test_error_raises_llm_error(self, adapter, params):
        from components.generators.base import LLMError
        adapter.client.chat.completions.create.side_effect = Exception("network fail")

        with pytest.raises(LLMError):
            list(adapter.generate_streaming("prompt", params))


# ---------------------------------------------------------------------------
# Cost tracking
# ---------------------------------------------------------------------------

class TestCostTracking:

    def test_track_usage_with_breakdown(self, adapter):
        usage = {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        breakdown = adapter._track_usage_with_breakdown(usage)

        assert breakdown["input_tokens"] == 100
        assert breakdown["output_tokens"] == 50
        assert breakdown["total_tokens"] == 150
        assert breakdown["model"] == "gpt-3.5-turbo"
        # gpt-3.5-turbo: input=$0.001/1K, output=$0.002/1K
        # 100 input tokens = $0.0001, 50 output tokens = $0.0001
        assert breakdown["input_cost_usd"] == pytest.approx(0.0001, abs=1e-6)
        assert breakdown["output_cost_usd"] == pytest.approx(0.0001, abs=1e-6)
        assert breakdown["total_cost_usd"] == pytest.approx(0.0002, abs=1e-6)

    def test_cost_accumulates(self, adapter):
        usage = {"prompt_tokens": 1000, "completion_tokens": 500}
        adapter._track_usage_with_breakdown(usage)
        adapter._track_usage_with_breakdown(usage)

        assert adapter._input_tokens == 2000
        assert adapter._output_tokens == 1000
        assert adapter._total_cost > Decimal("0")
        assert len(adapter.cost_history) == 2

    def test_get_cost_breakdown(self, adapter):
        usage = {"prompt_tokens": 200, "completion_tokens": 100}
        adapter._track_usage_with_breakdown(usage)
        adapter._request_count = 1

        bd = adapter.get_cost_breakdown()
        assert bd["model"] == "gpt-3.5-turbo"
        assert bd["input_tokens"] == 200
        assert bd["output_tokens"] == 100
        assert bd["total_tokens"] == 300
        assert bd["total_requests"] == 1
        assert "input_cost_usd" in bd
        assert "output_cost_usd" in bd
        assert "pricing_per_1k" in bd

    def test_get_cost_breakdown_unknown_model(self, mock_openai_class):
        from components.generators.llm_adapters.openai_adapter import OpenAIAdapter
        a = OpenAIAdapter(model_name="gpt-5-unknown", api_key="sk-test")
        bd = a.get_cost_breakdown()
        assert bd == {"error": "Pricing not available for this model"}

    def test_estimate_cost(self, adapter):
        est = adapter.estimate_cost("Hello world, this is a test prompt", max_output_tokens=100)
        assert est["model"] == "gpt-3.5-turbo"
        assert "estimated_input_tokens" in est
        assert "estimated_output_tokens" in est
        assert est["estimated_output_tokens"] == 100
        assert est["estimated_total_cost_usd"] > 0

    def test_estimate_cost_uses_tokenizer(self, adapter):
        # The mock tokenizer returns 10 tokens for any input
        est = adapter.estimate_cost("anything", max_output_tokens=50)
        assert est["estimated_input_tokens"] == 10

    def test_get_cost_summary_empty(self, adapter):
        summary = adapter.get_cost_summary()
        assert summary["total_cost_usd"] == 0.0
        assert summary["total_requests"] == 0

    def test_get_cost_summary_after_usage(self, adapter):
        adapter._track_usage_with_breakdown(
            {"prompt_tokens": 500, "completion_tokens": 200}
        )
        summary = adapter.get_cost_summary()
        assert summary["total_requests"] == 1
        assert summary["total_cost_usd"] > 0
        assert "cost_breakdown" in summary

    def test_get_model_info(self, adapter):
        info = adapter.get_model_info()
        assert info["provider"] == "OpenAI"
        assert info["model"] == "gpt-3.5-turbo"
        assert info["supports_streaming"] is True
        assert info["max_context_tokens"] == 16385


# ---------------------------------------------------------------------------
# _make_request
# ---------------------------------------------------------------------------

class TestMakeRequest:

    def test_success(self, adapter, params):
        resp = _mock_openai_response(content="test answer")
        adapter.client.chat.completions.create.return_value = resp

        result = adapter._make_request("prompt", params)
        assert result["choices"][0]["message"]["content"] == "test answer"
        assert result["usage"]["prompt_tokens"] == 10
        assert "cost_breakdown" in result

    def test_rate_limit_retried_then_raises(self, adapter, params):
        """RateLimitError triggers tenacity retries, ultimately re-raises."""
        import openai as openai_mod

        adapter.client.chat.completions.create.side_effect = openai_mod.RateLimitError(
            message="rate limited", response=MagicMock(status_code=429), body=None
        )
        # tenacity wraps the final RateLimitError in RetryError
        with pytest.raises(Exception):  # tenacity.RetryError or RateLimitError
            adapter._make_request("p", params)

    def test_auth_error_mapped(self, adapter, params):
        import openai as openai_mod
        from components.generators.llm_adapters.base_adapter import AuthenticationError

        adapter.client.chat.completions.create.side_effect = openai_mod.AuthenticationError(
            message="bad key", response=MagicMock(status_code=401), body=None
        )
        with pytest.raises(AuthenticationError):
            adapter._make_request("p", params)

    def test_not_found_error_mapped(self, adapter, params):
        import openai as openai_mod
        from components.generators.llm_adapters.base_adapter import ModelNotFoundError

        adapter.client.chat.completions.create.side_effect = openai_mod.NotFoundError(
            message="no model", response=MagicMock(status_code=404), body=None
        )
        with pytest.raises(ModelNotFoundError):
            adapter._make_request("p", params)

    def test_bad_request_error_mapped(self, adapter, params):
        import openai as openai_mod
        from components.generators.base import LLMError

        adapter.client.chat.completions.create.side_effect = openai_mod.BadRequestError(
            message="bad request", response=MagicMock(status_code=400), body=None
        )
        with pytest.raises(LLMError):
            adapter._make_request("p", params)


# ---------------------------------------------------------------------------
# Function calling: generate_with_functions
# ---------------------------------------------------------------------------

class TestGenerateWithFunctions:

    def test_empty_tools_raises(self, adapter):
        with pytest.raises(ValueError, match="Tools list cannot be empty"):
            adapter.generate_with_functions("prompt", tools=[])

    def test_completed_no_tool_calls(self, adapter):
        """When LLM responds without tool_calls, status is 'completed'."""
        resp = _mock_openai_response(
            content="The answer is 42", finish_reason="stop", tool_calls=None
        )
        adapter.client.chat.completions.create.return_value = resp

        result = adapter.generate_with_functions("What is 6*7?", tools=_sample_tools())

        assert result["status"] == "completed"
        assert result["final_response"] == "The answer is 42"
        assert result["iterations"] == 1
        assert result["function_calls"] == []
        assert result["total_tokens"] > 0

    def test_requires_function_execution(self, adapter):
        """When LLM returns tool_calls, status is 'requires_function_execution'."""
        tc = _make_tool_call(call_id="call_abc", name="calculator", arguments='{"expression":"2+2"}')
        resp = _mock_openai_response(
            content=None, finish_reason="tool_calls", tool_calls=[tc]
        )
        adapter.client.chat.completions.create.return_value = resp

        result = adapter.generate_with_functions("What is 2+2?", tools=_sample_tools())

        assert result["status"] == "requires_function_execution"
        assert len(result["pending_tool_calls"]) == 1
        assert result["function_calls"][0]["name"] == "calculator"
        assert result["function_calls"][0]["arguments"] == {"expression": "2+2"}
        assert result["iterations"] == 1

    def test_parallel_tool_calls(self, adapter):
        """Multiple tool_calls in a single response (parallel calling)."""
        tc1 = _make_tool_call(call_id="call_1", name="calculator", arguments='{"expression":"2+2"}')
        tc2 = _make_tool_call(call_id="call_2", name="calculator", arguments='{"expression":"3*3"}')
        resp = _mock_openai_response(
            content=None, finish_reason="tool_calls", tool_calls=[tc1, tc2]
        )
        adapter.client.chat.completions.create.return_value = resp

        result = adapter.generate_with_functions("Compute both", tools=_sample_tools())

        assert result["status"] == "requires_function_execution"
        assert len(result["pending_tool_calls"]) == 2
        assert len(result["function_calls"]) == 2
        assert result["function_calls"][0]["id"] == "call_1"
        assert result["function_calls"][1]["id"] == "call_2"

    def test_malformed_json_arguments(self, adapter):
        """Malformed JSON in tool_call arguments defaults to empty dict."""
        tc = _make_tool_call(call_id="call_bad", name="calculator", arguments="NOT-JSON{{{")
        resp = _mock_openai_response(
            content=None, finish_reason="tool_calls", tool_calls=[tc]
        )
        adapter.client.chat.completions.create.return_value = resp

        result = adapter.generate_with_functions("bad args", tools=_sample_tools())

        assert result["status"] == "requires_function_execution"
        assert result["function_calls"][0]["arguments"] == {}

    def test_error_status_on_exception(self, adapter):
        """API error during function calling returns status='error'."""
        adapter.client.chat.completions.create.side_effect = Exception("API down")

        result = adapter.generate_with_functions("prompt", tools=_sample_tools())

        assert result["status"] == "error"
        assert "API down" in result["error"]
        assert result["iterations"] == 1

    def test_unexpected_finish_reason(self, adapter):
        """Unexpected finish_reason returns 'incomplete' status."""
        resp = _mock_openai_response(
            content="partial answer", finish_reason="length", tool_calls=None
        )
        adapter.client.chat.completions.create.return_value = resp

        result = adapter.generate_with_functions("prompt", tools=_sample_tools())

        assert result["status"] == "incomplete"
        assert result["final_response"] == "partial answer"
        assert result["finish_reason"] == "length"

    def test_default_params_created_when_none(self, adapter):
        """When params=None, defaults are used (no error)."""
        resp = _mock_openai_response(content="ok", finish_reason="stop")
        adapter.client.chat.completions.create.return_value = resp

        result = adapter.generate_with_functions("prompt", tools=_sample_tools(), params=None)
        assert result["status"] == "completed"

    def test_cost_tracked(self, adapter):
        """Cost and token usage accumulate correctly."""
        resp = _mock_openai_response(
            content="answer", finish_reason="stop",
            prompt_tokens=50, completion_tokens=20,
        )
        adapter.client.chat.completions.create.return_value = resp

        result = adapter.generate_with_functions("prompt", tools=_sample_tools())

        assert result["total_tokens"] == 70
        assert result["total_cost_usd"] > 0
        assert len(result["cost_breakdown"]) == 1

    def test_no_choices_raises_error(self, adapter):
        """Empty choices list triggers error status."""
        resp = _mock_openai_response(content="x", finish_reason="stop")
        # Override choices to be empty
        resp.choices = []
        adapter.client.chat.completions.create.return_value = resp

        result = adapter.generate_with_functions("prompt", tools=_sample_tools())
        assert result["status"] == "error"
        assert "No choices" in result["error"]


# ---------------------------------------------------------------------------
# continue_with_function_results
# ---------------------------------------------------------------------------

class TestContinueWithFunctionResults:

    def test_completed_after_function_result(self, adapter):
        """After providing function results, LLM completes."""
        resp = _mock_openai_response(content="The result is 4", finish_reason="stop")
        adapter.client.chat.completions.create.return_value = resp

        messages = [
            {"role": "user", "content": "What is 2+2?"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "call_1", "type": "function",
                     "function": {"name": "calculator", "arguments": '{"expression":"2+2"}'}}
                ],
            },
        ]
        func_results = [{"tool_call_id": "call_1", "content": "4"}]

        result = adapter.continue_with_function_results(
            messages=messages,
            function_results=func_results,
            tools=_sample_tools(),
        )

        assert result["status"] == "completed"
        assert result["final_response"] == "The result is 4"

    def test_empty_function_results_raises(self, adapter):
        with pytest.raises(ValueError, match="function_results cannot be empty"):
            adapter.continue_with_function_results(
                messages=[{"role": "user", "content": "hi"}],
                function_results=[],
                tools=_sample_tools(),
            )

    def test_error_in_continuation(self, adapter):
        """API error during continuation returns error status."""
        adapter.client.chat.completions.create.side_effect = Exception("timeout")

        messages = [{"role": "user", "content": "hi"}]
        func_results = [{"tool_call_id": "call_1", "content": "ok"}]

        result = adapter.continue_with_function_results(
            messages=messages,
            function_results=func_results,
            tools=_sample_tools(),
        )
        assert result["status"] == "error"

    def test_messages_not_mutated(self, adapter):
        """Original messages list should not be mutated (deepcopy)."""
        resp = _mock_openai_response(content="done", finish_reason="stop")
        adapter.client.chat.completions.create.return_value = resp

        original_messages = [{"role": "user", "content": "hi"}]
        original_len = len(original_messages)

        adapter.continue_with_function_results(
            messages=original_messages,
            function_results=[{"tool_call_id": "call_1", "content": "ok"}],
            tools=_sample_tools(),
        )

        assert len(original_messages) == original_len


# ---------------------------------------------------------------------------
# _make_function_request
# ---------------------------------------------------------------------------

class TestMakeFunctionRequest:

    def test_converts_response_with_tool_calls(self, adapter, params):
        """Tool calls from the raw response are converted to dicts."""
        tc = _make_tool_call(call_id="call_x", name="search", arguments='{"q":"test"}')
        resp = _mock_openai_response(
            content=None, finish_reason="tool_calls", tool_calls=[tc]
        )
        adapter.client.chat.completions.create.return_value = resp

        messages = [{"role": "user", "content": "test"}]
        result = adapter._make_function_request(messages, _sample_tools(), params)

        assert len(result["choices"]) == 1
        tc_dicts = result["choices"][0]["message"]["tool_calls"]
        assert len(tc_dicts) == 1
        assert tc_dicts[0]["id"] == "call_x"
        assert tc_dicts[0]["function"]["name"] == "search"

    def test_no_tool_calls_in_response(self, adapter, params):
        """When tool_calls is None, message dict has no tool_calls key."""
        resp = _mock_openai_response(content="plain answer", finish_reason="stop")
        adapter.client.chat.completions.create.return_value = resp

        messages = [{"role": "user", "content": "test"}]
        result = adapter._make_function_request(messages, _sample_tools(), params)

        assert "tool_calls" not in result["choices"][0]["message"]

    def test_cost_tracked(self, adapter, params):
        resp = _mock_openai_response(prompt_tokens=30, completion_tokens=15)
        adapter.client.chat.completions.create.return_value = resp

        messages = [{"role": "user", "content": "test"}]
        result = adapter._make_function_request(messages, _sample_tools(), params)

        assert "cost_breakdown" in result
        assert result["usage"]["total_tokens"] == 45


# ---------------------------------------------------------------------------
# _handle_openai_error
# ---------------------------------------------------------------------------

class TestHandleOpenAIError:

    def test_status_code_401(self, adapter):
        from components.generators.llm_adapters.base_adapter import AuthenticationError
        err = MagicMock()
        err.status_code = 401
        with pytest.raises(AuthenticationError):
            adapter._handle_openai_error(err)

    def test_status_code_404(self, adapter):
        from components.generators.llm_adapters.base_adapter import ModelNotFoundError
        err = MagicMock()
        err.status_code = 404
        with pytest.raises(ModelNotFoundError):
            adapter._handle_openai_error(err)

    def test_status_code_429(self, adapter):
        from components.generators.llm_adapters.base_adapter import RateLimitError
        err = MagicMock()
        err.status_code = 429
        with pytest.raises(RateLimitError):
            adapter._handle_openai_error(err)

    def test_status_code_500(self, adapter):
        from components.generators.base import LLMError
        err = MagicMock()
        err.status_code = 500
        with pytest.raises(LLMError, match="status 500"):
            adapter._handle_openai_error(err)

    def test_string_match_unauthorized(self, adapter):
        from components.generators.llm_adapters.base_adapter import AuthenticationError
        err = Exception("Unauthorized request")
        with pytest.raises(AuthenticationError):
            adapter._handle_openai_error(err)

    def test_string_match_rate_limit(self, adapter):
        from components.generators.llm_adapters.base_adapter import RateLimitError
        err = Exception("rate limit exceeded")
        with pytest.raises(RateLimitError):
            adapter._handle_openai_error(err)

    def test_string_match_model_not_found(self, adapter):
        from components.generators.llm_adapters.base_adapter import ModelNotFoundError
        err = Exception("model not found")
        with pytest.raises(ModelNotFoundError):
            adapter._handle_openai_error(err)

    def test_generic_error(self, adapter):
        from components.generators.base import LLMError
        err = Exception("something unexpected")
        with pytest.raises(LLMError, match="OpenAI error"):
            adapter._handle_openai_error(err)


# ---------------------------------------------------------------------------
# Simple methods
# ---------------------------------------------------------------------------

class TestSimpleMethods:

    def test_get_provider_name(self, adapter):
        assert adapter._get_provider_name() == "OpenAI"

    def test_supports_streaming(self, adapter):
        assert adapter._supports_streaming() is True

    def test_get_max_tokens_known(self, adapter):
        assert adapter._get_max_tokens() == 16385

    def test_get_max_tokens_unknown(self, mock_openai_class):
        from components.generators.llm_adapters.openai_adapter import OpenAIAdapter
        a = OpenAIAdapter(model_name="gpt-5-unknown", api_key="sk-test")
        assert a._get_max_tokens() is None
