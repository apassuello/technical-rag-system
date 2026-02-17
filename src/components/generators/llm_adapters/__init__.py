"""
LLM Adapters for Answer Generator.

This module provides adapters for various LLM providers, converting
between the unified interface and provider-specific formats.

Available adapters:
- LlamaAdapter: For local llama-server (OpenAI-compatible /v1/ API)
- OllamaAdapter: For local Ollama models
- OpenAIAdapter: For OpenAI API (GPT models)
- AnthropicAdapter: For Anthropic Claude API (with tools support)
- HuggingFaceAdapter: For HuggingFace models and Inference API
- MistralAdapter: For Mistral AI API
"""

from .anthropic_adapter import AnthropicAdapter
from .base_adapter import (
    AuthenticationError,
    BaseLLMAdapter,
    ModelNotFoundError,
    RateLimitError,
)
from .huggingface_adapter import HuggingFaceAdapter
from .llama_adapter import LlamaAdapter
from .mistral_adapter import MistralAdapter
from .mock_adapter import MockLLMAdapter
from .ollama_adapter import OllamaAdapter
from .openai_adapter import OpenAIAdapter

__all__ = [
    'BaseLLMAdapter',
    'LlamaAdapter',
    'OllamaAdapter',
    'HuggingFaceAdapter',
    'MockLLMAdapter',
    'OpenAIAdapter',
    'MistralAdapter',
    'AnthropicAdapter',
    'RateLimitError',
    'AuthenticationError',
    'ModelNotFoundError'
]

# Adapter registry for easy lookup
ADAPTER_REGISTRY = {
    'local': LlamaAdapter,
    'ollama': OllamaAdapter,
    'huggingface': HuggingFaceAdapter,
    'mock': MockLLMAdapter,
    'openai': OpenAIAdapter,
    'mistral': MistralAdapter,
    'anthropic': AnthropicAdapter,
}

from typing import Type


def get_adapter_class(provider: str) -> Type[BaseLLMAdapter]:
    """
    Get adapter class by provider name.

    Args:
        provider: Provider name (e.g., 'ollama', 'openai')

    Returns:
        Adapter class

    Raises:
        ValueError: If provider not found
    """
    if provider not in ADAPTER_REGISTRY:
        raise ValueError(f"Unknown LLM provider: {provider}. Available: {list(ADAPTER_REGISTRY.keys())}")
    return ADAPTER_REGISTRY[provider]
