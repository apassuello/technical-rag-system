"""
Central LLM provider configuration — single source of truth.

All code that needs model names, provider types, base URLs, or API keys
should import from this module instead of hardcoding values.

To switch the default provider, set LLM_PROVIDER env var:
    LLM_PROVIDER=openai pytest ...
    LLM_PROVIDER=local python app.py
"""

import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class LLMProviderConfig:
    """Configuration for an LLM provider."""
    adapter_type: str
    model: str
    base_url: Optional[str] = None
    api_key_env: Optional[str] = None
    cost_per_1k_input: Decimal = Decimal("0")
    cost_per_1k_output: Decimal = Decimal("0")
    estimated_quality: float = 0.75
    estimated_latency_ms: float = 500.0

    @property
    def api_key(self) -> Optional[str]:
        if self.api_key_env:
            return os.getenv(self.api_key_env)
        return "local"

    @property
    def is_free(self) -> bool:
        return self.cost_per_1k_input == Decimal("0") and self.cost_per_1k_output == Decimal("0")


# --- Provider definitions ---

LOCAL = LLMProviderConfig(
    adapter_type="openai",
    model="qwen2.5-1.5b-instruct",
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
    cost_per_1k_input=Decimal("0.0000"),
    cost_per_1k_output=Decimal("0.0000"),
    estimated_quality=0.75,
    estimated_latency_ms=100.0,
)

OPENAI = LLMProviderConfig(
    adapter_type="openai",
    model="gpt-4o-mini",
    api_key_env="OPENAI_API_KEY",
    cost_per_1k_input=Decimal("0.00015"),
    cost_per_1k_output=Decimal("0.0006"),
    estimated_quality=0.90,
    estimated_latency_ms=400.0,
)

ANTHROPIC = LLMProviderConfig(
    adapter_type="anthropic",
    model="claude-3-5-haiku-latest",
    api_key_env="ANTHROPIC_API_KEY",
    cost_per_1k_input=Decimal("0.001"),
    cost_per_1k_output=Decimal("0.005"),
    estimated_quality=0.92,
    estimated_latency_ms=500.0,
)

MISTRAL = LLMProviderConfig(
    adapter_type="mistral",
    model="mistral-small-latest",
    api_key_env="MISTRAL_API_KEY",
    cost_per_1k_input=Decimal("0.001"),
    cost_per_1k_output=Decimal("0.003"),
    estimated_quality=0.87,
    estimated_latency_ms=300.0,
)

HUGGINGFACE = LLMProviderConfig(
    adapter_type="huggingface",
    model="microsoft/DialoGPT-medium",
    api_key_env="HF_TOKEN",
    cost_per_1k_input=Decimal("0.0000"),
    cost_per_1k_output=Decimal("0.0000"),
    estimated_quality=0.70,
    estimated_latency_ms=600.0,
)

PROVIDERS = {
    "local": LOCAL,
    "openai": OPENAI,
    "anthropic": ANTHROPIC,
    "mistral": MISTRAL,
    "huggingface": HUGGINGFACE,
}

DEFAULT_PROVIDER_NAME = os.getenv("LLM_PROVIDER", "local")
if DEFAULT_PROVIDER_NAME not in PROVIDERS:
    import logging as _logging
    _logging.getLogger(__name__).warning(
        "Unknown LLM_PROVIDER '%s', falling back to 'local'", DEFAULT_PROVIDER_NAME
    )
    DEFAULT_PROVIDER_NAME = "local"
DEFAULT = PROVIDERS[DEFAULT_PROVIDER_NAME]
