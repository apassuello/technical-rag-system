"""
LLM Adapters for Answer Generator.

This module provides adapters for various LLM providers, converting
between the unified interface and provider-specific formats.

Available adapters:
- OllamaAdapter: For local Ollama models
- OpenAIAdapter: For OpenAI API (GPT models)
- HuggingFaceAdapter: For HuggingFace models and Inference API
"""

from .base_adapter import (
    BaseLLMAdapter,
    RateLimitError,
    AuthenticationError,
    ModelNotFoundError
)
from .ollama_adapter import OllamaAdapter

# Future adapters will be imported here
# from .openai_adapter import OpenAIAdapter
# from .huggingface_adapter import HuggingFaceAdapter

__all__ = [
    'BaseLLMAdapter',
    'OllamaAdapter',
    # 'OpenAIAdapter',
    # 'HuggingFaceAdapter',
    'RateLimitError',
    'AuthenticationError',
    'ModelNotFoundError'
]

# Adapter registry for easy lookup
ADAPTER_REGISTRY = {
    'ollama': OllamaAdapter,
    # 'openai': OpenAIAdapter,
    # 'huggingface': HuggingFaceAdapter,
}

def get_adapter_class(provider: str):
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