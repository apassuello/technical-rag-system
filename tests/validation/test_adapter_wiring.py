"""Validation tests for LLM adapter wiring and interface compliance.

Tests verify that each cloud adapter properly implements the BaseLLMAdapter
interface without requiring actual API credentials or network connections.
"""

from unittest.mock import MagicMock, patch
import pytest

from src.components.generators.llm_adapters.base_adapter import (
    RateLimitError,
    AuthenticationError,
    ModelNotFoundError,
    LLMError,
)
from src.components.generators.base import GenerationParams

pytestmark = [pytest.mark.validation]


# ============================================================================
# OpenAI Adapter Tests
# ============================================================================


@pytest.fixture
def openai_adapter():
    """Create OpenAI adapter with mocked client and validation."""
    with patch("src.components.generators.llm_adapters.openai_adapter.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        from src.components.generators.llm_adapters.openai_adapter import OpenAIAdapter

        adapter = OpenAIAdapter(
            model_name="gpt-3.5-turbo",
            api_key="test-key",
            max_retries=1,
            retry_delay=0,
        )

        # Mock _validate_model to avoid validation checks
        with patch.object(adapter, "_validate_model", return_value=True):
            # Mock _make_request for generate tests
            adapter._test_mock_request = MagicMock()
            yield adapter


def test_openai_construction():
    """OpenAI adapter can be constructed with mocked client."""
    with patch("src.components.generators.llm_adapters.openai_adapter.OpenAI") as mock_openai_class:
        mock_openai_class.return_value = MagicMock()

        from src.components.generators.llm_adapters.openai_adapter import OpenAIAdapter

        adapter = OpenAIAdapter(
            model_name="gpt-4",
            api_key="test-key",
            max_retries=1,
        )

        assert adapter.model_name == "gpt-4"
        assert adapter.client is not None
        mock_openai_class.assert_called_once()


def test_openai_generate(openai_adapter):
    """OpenAI adapter generates responses with correct format parsing."""
    mock_response = {
        "choices": [{"message": {"content": "This is a test answer from OpenAI"}}],
        "usage": {"total_tokens": 15},
    }

    with patch.object(openai_adapter, "_make_request", return_value=mock_response):
        result = openai_adapter.generate("Test prompt", GenerationParams())

    assert isinstance(result, str)
    assert len(result) > 0
    assert result == "This is a test answer from OpenAI"


def test_openai_error_handling(openai_adapter):
    """OpenAI adapter properly maps exceptions to LLMError."""
    with patch.object(openai_adapter, "_make_request", side_effect=Exception("API Error")):
        with pytest.raises(LLMError):
            openai_adapter.generate("Test prompt", GenerationParams())


def test_openai_model_info(openai_adapter):
    """OpenAI adapter returns correct model info."""
    info = openai_adapter.get_model_info()

    assert isinstance(info, dict)
    assert "provider" in info
    assert "model" in info
    assert info["provider"] == "OpenAI"
    assert info["model"] == "gpt-3.5-turbo"


# ============================================================================
# Anthropic Adapter Tests
# ============================================================================


@pytest.fixture
def anthropic_adapter():
    """Create Anthropic adapter with mocked client and validation."""
    with patch("src.components.generators.llm_adapters.anthropic_adapter.Anthropic") as mock_anthropic_class:
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        from src.components.generators.llm_adapters.anthropic_adapter import AnthropicAdapter

        adapter = AnthropicAdapter(
            model_name="claude-3-5-sonnet-20241022",
            api_key="test-key",
            max_retries=1,
            retry_delay=0,
        )

        # Mock _validate_model to avoid validation checks
        with patch.object(adapter, "_validate_model", return_value=True):
            adapter._test_mock_request = MagicMock()
            yield adapter


def test_anthropic_construction():
    """Anthropic adapter can be constructed with mocked client."""
    with patch("src.components.generators.llm_adapters.anthropic_adapter.Anthropic") as mock_anthropic_class:
        mock_anthropic_class.return_value = MagicMock()

        from src.components.generators.llm_adapters.anthropic_adapter import AnthropicAdapter

        adapter = AnthropicAdapter(
            model_name="claude-3-opus-20240229",
            api_key="test-key",
            max_retries=1,
        )

        assert adapter.model_name == "claude-3-opus-20240229"
        assert adapter.client is not None
        mock_anthropic_class.assert_called_once()


def test_anthropic_generate(anthropic_adapter):
    """Anthropic adapter generates responses with correct format parsing."""
    # Create mock content blocks that match Anthropic's response structure
    mock_text_block = type("Block", (), {"type": "text", "text": "This is a test answer from Claude"})()
    mock_response = {
        "content": [mock_text_block],
        "usage": {"input_tokens": 10, "output_tokens": 8, "total_tokens": 18},
    }

    with patch.object(anthropic_adapter, "_make_request", return_value=mock_response):
        result = anthropic_adapter.generate("Test prompt", GenerationParams())

    assert isinstance(result, str)
    assert len(result) > 0
    assert result == "This is a test answer from Claude"


def test_anthropic_error_handling(anthropic_adapter):
    """Anthropic adapter properly maps exceptions to LLMError."""
    with patch.object(anthropic_adapter, "_make_request", side_effect=Exception("API Error")):
        with pytest.raises(LLMError):
            anthropic_adapter.generate("Test prompt", GenerationParams())


def test_anthropic_model_info(anthropic_adapter):
    """Anthropic adapter returns correct model info."""
    info = anthropic_adapter.get_model_info()

    assert isinstance(info, dict)
    assert "provider" in info
    assert "model" in info
    assert info["provider"] == "Anthropic"
    assert info["model"] == "claude-3-5-sonnet-20241022"


# ============================================================================
# Mistral Adapter Tests
# ============================================================================


@pytest.fixture
def mistral_adapter():
    """Create Mistral adapter with mocked client and validation."""
    with patch("src.components.generators.llm_adapters.mistral_adapter.Mistral") as mock_mistral_class:
        mock_client = MagicMock()
        mock_mistral_class.return_value = mock_client

        from src.components.generators.llm_adapters.mistral_adapter import MistralAdapter

        adapter = MistralAdapter(
            model_name="mistral-small",
            api_key="test-key",
            max_retries=1,
            retry_delay=0,
        )

        # Mock _validate_model to avoid validation checks
        with patch.object(adapter, "_validate_model", return_value=True):
            adapter._test_mock_request = MagicMock()
            yield adapter


def test_mistral_construction():
    """Mistral adapter can be constructed with mocked client."""
    with patch("src.components.generators.llm_adapters.mistral_adapter.Mistral") as mock_mistral_class:
        mock_mistral_class.return_value = MagicMock()

        from src.components.generators.llm_adapters.mistral_adapter import MistralAdapter

        adapter = MistralAdapter(
            model_name="mistral-medium",
            api_key="test-key",
            max_retries=1,
        )

        assert adapter.model_name == "mistral-medium"
        assert adapter.client is not None
        mock_mistral_class.assert_called_once()


def test_mistral_generate(mistral_adapter):
    """Mistral adapter generates responses with correct format parsing."""
    mock_response = {
        "choices": [{"message": {"content": "This is a test answer from Mistral"}}],
        "usage": {"total_tokens": 12},
    }

    with patch.object(mistral_adapter, "_make_request", return_value=mock_response):
        result = mistral_adapter.generate("Test prompt", GenerationParams())

    assert isinstance(result, str)
    assert len(result) > 0
    assert result == "This is a test answer from Mistral"


def test_mistral_error_handling(mistral_adapter):
    """Mistral adapter properly maps exceptions to LLMError."""
    with patch.object(mistral_adapter, "_make_request", side_effect=Exception("API Error")):
        with pytest.raises(LLMError):
            mistral_adapter.generate("Test prompt", GenerationParams())


def test_mistral_model_info(mistral_adapter):
    """Mistral adapter returns correct model info."""
    info = mistral_adapter.get_model_info()

    assert isinstance(info, dict)
    assert "provider" in info
    assert "model" in info
    assert info["provider"] == "Mistral"
    assert info["model"] == "mistral-small"


# ============================================================================
# HuggingFace Adapter Tests
# ============================================================================


@pytest.fixture
def huggingface_adapter():
    """Create HuggingFace adapter with mocked inference client."""
    with patch("src.components.generators.llm_adapters.huggingface_adapter.InferenceClient") as mock_hf_class:
        mock_client = MagicMock()
        mock_hf_class.return_value = mock_client

        from src.components.generators.llm_adapters.huggingface_adapter import HuggingFaceAdapter

        adapter = HuggingFaceAdapter(
            model_name="microsoft/DialoGPT-medium",
            api_token="test-token",
            timeout=10,
            use_chat_completion=True,
        )

        # Mock _validate_model to avoid validation checks
        with patch.object(adapter, "_validate_model", return_value=True):
            adapter._test_mock_request = MagicMock()
            yield adapter


def test_huggingface_construction():
    """HuggingFace adapter can be constructed with mocked client."""
    with patch("src.components.generators.llm_adapters.huggingface_adapter.InferenceClient") as mock_hf_class:
        mock_hf_class.return_value = MagicMock()

        from src.components.generators.llm_adapters.huggingface_adapter import HuggingFaceAdapter

        adapter = HuggingFaceAdapter(
            model_name="google/flan-t5-base",
            api_token="test-token",
            timeout=15,
        )

        assert adapter.model_name == "google/flan-t5-base"
        assert adapter.timeout == 15
        mock_hf_class.assert_called_once()


def test_huggingface_generate(huggingface_adapter):
    """HuggingFace adapter generates responses with correct format parsing."""
    mock_response = {
        "content": "This is a test answer from HuggingFace",
        "usage": {},
    }

    with patch.object(huggingface_adapter, "_make_request", return_value=mock_response):
        result = huggingface_adapter.generate("Test prompt", GenerationParams())

    assert isinstance(result, str)
    assert len(result) > 0
    assert result == "This is a test answer from HuggingFace"


def test_huggingface_error_handling(huggingface_adapter):
    """HuggingFace adapter properly maps exceptions to LLMError."""
    with patch.object(huggingface_adapter, "_make_request", side_effect=Exception("API Error")):
        with pytest.raises(LLMError):
            huggingface_adapter.generate("Test prompt", GenerationParams())


def test_huggingface_model_info(huggingface_adapter):
    """HuggingFace adapter returns correct model info."""
    info = huggingface_adapter.get_model_info()

    assert isinstance(info, dict)
    assert "provider" in info
    assert "model" in info
    assert info["provider"] == "HuggingFace"
    assert info["model"] == "microsoft/DialoGPT-medium"
