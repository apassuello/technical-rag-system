"""
Integration tests for OllamaAdapter against a real Ollama server.

Requires Docker with Ollama running and tinyllama model pulled:
    docker run -d -p 11434:11434 ollama/ollama
    docker exec <container> ollama pull tinyllama
"""

import pytest

from components.generators.llm_adapters.ollama_adapter import OllamaAdapter
from components.generators.base import GenerationParams, LLMError
from components.generators.llm_adapters.base_adapter import ModelNotFoundError

pytestmark = [
    pytest.mark.integration,
    pytest.mark.requires_ollama,
]

OLLAMA_URL = "http://localhost:11434"
MODEL = "tinyllama"


@pytest.fixture
def adapter():
    """OllamaAdapter pointed at local Docker Ollama with tinyllama."""
    return OllamaAdapter(
        model_name=MODEL,
        base_url=OLLAMA_URL,
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
        """Generate with tinyllama and verify non-empty string response."""
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
        """validate_connection returns True when Ollama is reachable."""
        assert adapter.validate_connection() is True


# ---------------------------------------------------------------------------
# Model info
# ---------------------------------------------------------------------------


class TestModelInfo:

    def test_get_model_info(self, adapter):
        """get_model_info returns dict with expected keys."""
        info = adapter.get_model_info()
        assert isinstance(info, dict)
        assert info["provider"] == "Ollama"
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
            base_url=OLLAMA_URL,
            timeout=15,
        )
        params = GenerationParams(max_tokens=10)
        with pytest.raises((LLMError, ModelNotFoundError)):
            bad_adapter.generate("hello", params)
