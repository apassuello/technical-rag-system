"""
Integration tests for LLM adapter against a real llama-server instance.

Requires llama-server running with qwen2.5-1.5b-instruct model:
    llama-server -m models/qwen2.5-1.5b-instruct-q4_k_m.gguf \
        --host 0.0.0.0 --port 11434
"""

import requests
import pytest

from components.generators.llm_adapters.ollama_adapter import OllamaAdapter
from components.generators.base import GenerationParams, LLMError
from components.generators.llm_adapters.base_adapter import ModelNotFoundError


def _llm_server_available(model="qwen2.5-1.5b-instruct"):
    """Check whether llama-server is running and responding."""
    try:
        resp = requests.post(
            "http://localhost:11434/v1/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 1,
            },
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


pytestmark = [
    pytest.mark.integration,
    pytest.mark.requires_ollama,
    pytest.mark.skipif(
        not _llm_server_available(),
        reason="llama-server qwen2.5-1.5b-instruct model not available",
    ),
]

SERVER_URL = "http://localhost:11434/v1"
MODEL = "qwen2.5-1.5b-instruct"


@pytest.fixture
def adapter():
    """OllamaAdapter pointed at local llama-server with qwen2.5-1.5b-instruct."""
    return OllamaAdapter(
        model_name=MODEL,
        base_url=SERVER_URL,
        timeout=60,
    )


@pytest.fixture
def params():
    """Default generation params."""
    return GenerationParams()


# ---------------------------------------------------------------------------
# Basic generation
# ---------------------------------------------------------------------------


class TestGeneration:

    def test_basic_generation(self, adapter, params):
        """Generate with qwen2.5-1.5b-instruct and verify non-empty string response."""
        result = adapter.generate("What is 2 + 2?", params)
        assert isinstance(result, str)
        assert len(result.strip()) > 0

    def test_generation_with_params(self, adapter):
        """Generate with explicit temperature and max_tokens."""
        params = GenerationParams(temperature=0.1, max_tokens=30)
        result = adapter.generate("Say hello in one word.", params)
        assert isinstance(result, str)
        assert len(result.strip()) > 0


# ---------------------------------------------------------------------------
# Streaming
# ---------------------------------------------------------------------------


class TestStreaming:

    def test_streaming_yields_chunks(self, adapter, params):
        """generate_streaming yields chunks that combine to non-empty text."""
        chunks = list(adapter.generate_streaming("Count to three.", params))
        assert len(chunks) > 0
        combined = "".join(chunks)
        assert len(combined.strip()) > 0


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidation:

    def test_validate_model_returns_true(self, adapter):
        """_validate_model returns True for an available model."""
        assert adapter._validate_model() is True

    def test_validate_connection_returns_true(self, adapter):
        """validate_connection returns True when llama-server is reachable."""
        assert adapter.validate_connection() is True


# ---------------------------------------------------------------------------
# Model info
# ---------------------------------------------------------------------------


class TestModelInfo:

    def test_get_model_info(self, adapter):
        """get_model_info returns dict with expected keys."""
        info = adapter.get_model_info()
        assert isinstance(info, dict)
        assert info["model"] == MODEL
        assert info["supports_streaming"] is True
        assert "max_tokens" in info
        assert "requests_made" in info


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:

    def test_nonexistent_model_raises(self):
        """A bogus model name raises LLMError or ModelNotFoundError."""
        bad_adapter = OllamaAdapter(
            model_name="nonexistent-model-xyz-999",
            base_url=SERVER_URL,
            timeout=15,
        )
        params = GenerationParams(max_tokens=10)
        with pytest.raises((LLMError, ModelNotFoundError)):
            bad_adapter.generate("hello", params)
