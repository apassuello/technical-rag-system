"""
LlamaAdapter — adapter for local llama-server via OpenAI-compatible /v1/ API.

Extends OpenAIAdapter with sensible defaults for local inference:
- api_key defaults to "local" (required by OpenAI client but unused)
- base_url defaults from LOCAL config (llm_providers.py)
- Cost tracking always returns zero (local inference is free)
- Health check hits /health on the base server (not /v1/health)
"""

import logging
import os
import time
from decimal import Decimal
from typing import Any, Dict, Optional

try:
    from openai import OpenAI
    import tiktoken
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None
    tiktoken = None

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from config.llm_providers import LOCAL
from .openai_adapter import OpenAIAdapter

logger = logging.getLogger(__name__)


class LlamaAdapter(OpenAIAdapter):
    """Adapter for local llama-server via OpenAI-compatible /v1/ API.

    Inherits all generation logic from OpenAIAdapter. Overrides only:
    - Constructor defaults (api_key, base_url, model from LOCAL config)
    - Provider name ("llama-server")
    - Model validation (GET /health on the llama-server)
    - Cost tracking (always zero — local inference is free)
    """

    # Local inference has no pricing or hard token limits
    MODEL_PRICING = {}
    MODEL_LIMITS = {}

    def __init__(
        self,
        model_name: str = LOCAL.model,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 120.0,
        **kwargs,
    ):
        resolved_api_key = (
            api_key
            or (config or {}).get("api_key")
            or os.getenv("OPENAI_API_KEY")
            or "local"
        )
        resolved_base_url = base_url or LOCAL.base_url

        super().__init__(
            model_name=model_name,
            api_key=resolved_api_key,
            base_url=resolved_base_url,
            config=config,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
        )

        # Keep the original base URL (without /v1) for health checks
        self._llama_base_url = resolved_base_url or ""

        logger.info(
            "Initialized LlamaAdapter for %s at %s",
            model_name,
            resolved_base_url,
        )

    def _get_provider_name(self) -> str:
        return "llama-server"

    def _validate_model(self) -> bool:
        """Check llama-server health via GET /health (on the base server, not /v1)."""
        if not REQUESTS_AVAILABLE:
            logger.warning("requests not installed — skipping health check")
            return False

        # Strip /v1 suffix to get the base server URL
        health_base = self._llama_base_url
        if health_base.endswith("/v1"):
            health_base = health_base[: -len("/v1")]
        health_url = health_base.rstrip("/") + "/health"

        try:
            resp = requests.get(health_url, timeout=5)
            return resp.status_code == 200
        except Exception as e:
            logger.error("llama-server health check failed: %s", e)
            return False

    def _track_usage_with_breakdown(self, usage: Dict[str, int]) -> Dict[str, Any]:
        """Track token counts but always report zero cost."""
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

        self._input_tokens += prompt_tokens
        self._output_tokens += completion_tokens

        return {
            "input_tokens": prompt_tokens,
            "output_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "input_cost_usd": 0.0,
            "output_cost_usd": 0.0,
            "total_cost_usd": 0.0,
            "model": self.model_name,
            "timestamp": time.time(),
        }
