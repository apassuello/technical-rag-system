"""
Mistral LLM Adapter Implementation.

This module provides integration with Mistral AI models through their official API,
optimized for cost-effective inference for medium-complexity queries in the Epic 1
multi-model routing system.

Architecture Notes:
- Extends BaseLLMAdapter following established adapter pattern
- Handles Mistral-specific authentication and API integration
- Provides cost tracking and token usage monitoring
- Optimized for cost-effective medium-complexity technical queries
- Includes comprehensive error handling and retry logic

Epic 1 Integration:
- Key component for cost-effective middle tier (medium complexity queries)
- Bridges gap between local models and premium GPT-4 for optimal cost/quality
- Enables 40%+ cost reduction through intelligent query routing
"""

import json
import logging
import os
import time
from decimal import Decimal
from typing import Any, Dict, Iterator, Optional

from config.llm_providers import MISTRAL

try:
    from mistralai import Mistral
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False
    Mistral = None

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from tenacity import (
        retry,
        retry_if_exception_type,
        stop_after_attempt,
        wait_exponential,
    )
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False
    # Define dummy decorators for fallback
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    def stop_after_attempt(*args, **kwargs):
        return None

    def wait_exponential(*args, **kwargs):
        return None

    def retry_if_exception_type(*args, **kwargs):
        return None

from ..base import GenerationParams, LLMError
from .base_adapter import (
    AuthenticationError,
    BaseLLMAdapter,
    ModelNotFoundError,
    RateLimitError,
)

logger = logging.getLogger(__name__)


class MistralAdapter(BaseLLMAdapter):
    """
    Mistral AI LLM adapter with support for cost-effective models.

    This adapter provides:
    - Authentication via API key
    - Token usage tracking and cost calculation
    - Support for multiple Mistral models (small, medium, large)
    - Comprehensive error handling with Mistral-specific mappings
    - Rate limit handling with exponential backoff
    - Optimized for cost-effective medium-complexity queries

    Supported Models:
    - mistral-tiny: Ultra-fast for simple queries (deprecated but supported)
    - mistral-small: Cost-effective for medium complexity queries
    - mistral-medium: Balanced performance for complex queries
    - mistral-large: High-performance for most complex queries

    Configuration Example:
    {
        "model_name": "mistral-small",
        "api_key": "your-api-key", # or set MISTRAL_API_KEY env var
        "base_url": "https://api.mistral.ai/v1", # optional
        "max_tokens": 1000,
        "temperature": 0.7,
        "timeout": 30.0
    }
    """

    # Current Mistral pricing per 1K tokens (as of January 2025)
    MODEL_PRICING = {
        'mistral-tiny': {
            'input': Decimal('0.0002'),   # $0.0002 per 1K input tokens
            'output': Decimal('0.0002')   # $0.0002 per 1K output tokens
        },
        'mistral-small': {
            'input': Decimal('0.0020'),   # $0.002 per 1K input tokens
            'output': Decimal('0.0060')   # $0.006 per 1K output tokens
        },
        'mistral-small-latest': {
            'input': Decimal('0.0020'),   # $0.002 per 1K input tokens
            'output': Decimal('0.0060')   # $0.006 per 1K output tokens
        },
        'mistral-medium': {
            'input': Decimal('0.0027'),   # $0.0027 per 1K input tokens
            'output': Decimal('0.0081')   # $0.0081 per 1K output tokens
        },
        'mistral-large': {
            'input': Decimal('0.0080'),   # $0.008 per 1K input tokens
            'output': Decimal('0.0240')   # $0.024 per 1K output tokens
        }
    }

    # Model context limits (tokens)
    MODEL_LIMITS = {
        'mistral-tiny': 32000,
        'mistral-small': 32000,
        'mistral-small-latest': 32000,
        'mistral-medium': 32000,
        'mistral-large': 32000
    }

    # API endpoints
    DEFAULT_BASE_URL = "https://api.mistral.ai/v1"

    def __init__(self,
                 model_name: str = MISTRAL.model,
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 timeout: float = 120.0):
        """
        Initialize Mistral adapter with production configuration.

        Args:
            model_name: Mistral model to use (default: mistral-small)
            api_key: Mistral API key (or set MISTRAL_API_KEY env var)
            base_url: API base URL (optional)
            config: Additional configuration parameters
            max_retries: Maximum retry attempts for failed requests
            retry_delay: Initial delay between retries (seconds)
            timeout: Request timeout in seconds

        Raises:
            ImportError: If mistralai package is not installed
            AuthenticationError: If API key is not provided
        """
        if not MISTRAL_AVAILABLE:
            raise ImportError(
                "Mistral AI package not installed. Install with: pip install mistralai"
            )

        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "Requests package not installed. Install with: pip install requests"
            )

        # Merge config with defaults
        adapter_config = {
            'api_key': api_key or os.getenv('MISTRAL_API_KEY'),
            'base_url': base_url or self.DEFAULT_BASE_URL,
            'timeout': timeout,
            'track_costs': True,
            **(config or {})
        }

        super().__init__(model_name, adapter_config, max_retries, retry_delay)

        # Validate API key
        if not adapter_config['api_key']:
            raise AuthenticationError("Mistral API key is required. Set MISTRAL_API_KEY environment variable.")

        # Initialize Mistral client
        self.client = Mistral(api_key=adapter_config['api_key'])
        self.timeout = adapter_config['timeout']
        self.track_costs = adapter_config['track_costs']

        # Cost tracking with detailed breakdown
        self._total_cost = Decimal('0.00')
        self._input_tokens = 0
        self._output_tokens = 0
        self.cost_history = []

        # Validate model pricing is available
        if model_name not in self.MODEL_PRICING:
            logger.warning(f"Pricing not available for model {model_name}, cost tracking disabled")

        logger.info(f"Initialized Mistral adapter with model: {model_name}, cost tracking: {self.track_costs}")

    @retry(
        retry=retry_if_exception_type(RateLimitError),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=1, max=60)
    )
    def _make_request(self, prompt: str, params: GenerationParams) -> Dict[str, Any]:
        """
        Make a request to Mistral API with retry logic for rate limits.

        Args:
            prompt: The prompt to send to the model
            params: Generation parameters

        Returns:
            Raw response from Mistral API with cost tracking

        Raises:
            RateLimitError: If rate limit is exceeded (triggers retry)
            AuthenticationError: If API key is invalid (no retry)
            ModelNotFoundError: If model doesn't exist (no retry)
            LLMError: For other API errors
        """
        try:
            # Prepare messages in chat format
            messages = []
            for msg in self._prepare_messages(prompt):
                # Convert to Mistral message format
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            # Prepare request parameters
            chat_params = {
                'model': self.model_name,
                'messages': messages
            }

            # Add generation parameters if they're not None
            if params.temperature is not None:
                chat_params['temperature'] = params.temperature
            if params.max_tokens is not None:
                chat_params['max_tokens'] = params.max_tokens
            if params.top_p is not None:
                chat_params['top_p'] = params.top_p
            if params.stop_sequences:
                chat_params['stop'] = params.stop_sequences

            # Make API request using official client
            logger.debug(f"Making Mistral request to {self.model_name}")
            start_time = time.time()

            response = self.client.chat.complete(**chat_params)

            request_time = time.time() - start_time
            logger.debug(f"Mistral request completed in {request_time:.2f}s")

            # Convert response to dictionary format for consistent handling
            response_dict = {
                'id': response.id,
                'model': response.model,
                'choices': [
                    {
                        'message': {
                            'role': choice.message.role,
                            'content': choice.message.content
                        },
                        'finish_reason': choice.finish_reason
                    }
                    for choice in response.choices
                ],
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                    'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                    'total_tokens': response.usage.total_tokens if response.usage else 0
                },
                'created': getattr(response, 'created', int(time.time())),
                'request_time': request_time
            }

            # Track token usage and costs with detailed breakdown
            if self.track_costs:
                cost_breakdown = self._track_usage_with_breakdown(response_dict['usage'])
                response_dict['cost_breakdown'] = cost_breakdown

            return response_dict

        except Exception as e:
            # Handle Mistral-specific errors
            error_str = str(e).lower()
            if '429' in error_str or 'rate limit' in error_str:
                logger.warning(f"Mistral rate limit exceeded: {str(e)}")
                raise RateLimitError(f"Mistral rate limit: {str(e)}")
            elif '401' in error_str or 'unauthorized' in error_str:
                logger.error(f"Mistral authentication failed: {str(e)}")
                raise AuthenticationError(f"Mistral authentication error: {str(e)}")
            elif '404' in error_str or 'not found' in error_str:
                logger.error(f"Mistral model not found: {str(e)}")
                raise ModelNotFoundError(f"Mistral model '{self.model_name}' not found: {str(e)}")
            else:
                logger.error(f"Unexpected Mistral error: {str(e)}")
                raise LLMError(f"Mistral API error: {str(e)}")

    def _parse_response(self, response: Dict[str, Any]) -> str:
        """
        Parse Mistral response to extract generated text.

        Args:
            response: Raw response from Mistral API

        Returns:
            Generated text content

        Raises:
            LLMError: If response format is invalid
        """
        try:
            if not response.get('choices'):
                raise LLMError("No choices in Mistral response")

            choice = response['choices'][0]
            message = choice.get('message', {})
            content = message.get('content', '')

            if not content:
                raise LLMError("Empty content in Mistral response")

            # Log finish reason for debugging
            finish_reason = choice.get('finish_reason')
            if finish_reason == 'length':
                logger.warning("Mistral response truncated due to max_tokens limit")
            elif finish_reason == 'stop':
                logger.debug("Mistral response completed normally")

            return content.strip()

        except KeyError as e:
            raise LLMError(f"Invalid Mistral response format: missing {str(e)}")

    def generate_streaming(self, prompt: str, params: GenerationParams) -> Iterator[str]:
        """
        Generate a streaming response from Mistral.

        Note: Mistral API supports streaming, but this implementation uses
        non-streaming for simplicity. Can be enhanced to support true streaming.

        Args:
            prompt: The prompt to send to the model
            params: Generation parameters

        Yields:
            Generated text chunks

        Raises:
            LLMError: If streaming generation fails
        """
        # For now, use non-streaming and yield the full response
        # This can be enhanced to support Mistral's streaming API
        logger.info("Using simulated streaming for Mistral (full response)")
        response = self.generate(prompt, params)
        yield response

    def _get_provider_name(self) -> str:
        """Return the provider name."""
        return "Mistral"

    def _validate_model(self) -> bool:
        """
        Check if the configured model exists and is accessible.

        Uses the official Mistral client (self.client) which is already
        configured with API key and base URL in __init__.

        Returns:
            True if model is available
        """
        try:
            # Test with a minimal request via the official client
            response = self.client.chat.complete(
                model=self.model_name,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
                temperature=0
            )
            return response is not None and hasattr(response, 'choices')

        except Exception as e:
            logger.error(f"Model validation failed: {str(e)}")
            return False

    def _supports_streaming(self) -> bool:
        """Mistral supports streaming, but using simulated for now."""
        return False  # Set to True when real streaming is implemented

    def _get_max_tokens(self) -> Optional[int]:
        """Get maximum token limit for the current model."""
        return self.MODEL_LIMITS.get(self.model_name)

    def _handle_http_error(self, response: requests.Response) -> None:
        """
        Handle HTTP error responses from Mistral API.

        Args:
            response: HTTP response object

        Raises:
            Appropriate LLMError subclass
        """
        status_code = response.status_code

        try:
            error_data = response.json()
            error_message = error_data.get('message', response.text)
        except json.JSONDecodeError:
            error_message = response.text

        if status_code == 401:
            raise AuthenticationError(f"Mistral authentication failed: {error_message}")
        elif status_code == 404:
            raise ModelNotFoundError(f"Mistral model not found: {error_message}")
        elif status_code == 429:
            raise RateLimitError(f"Mistral rate limit exceeded: {error_message}")
        elif status_code >= 500:
            raise LLMError(f"Mistral server error ({status_code}): {error_message}")
        else:
            raise LLMError(f"Mistral API error ({status_code}): {error_message}")

    def _handle_mistral_error(self, error: Exception) -> None:
        """
        Map Mistral-specific errors to standard adapter errors.

        Args:
            error: Mistral exception

        Raises:
            Appropriate LLMError subclass
        """
        error_str = str(error).lower()

        if 'unauthorized' in error_str or 'invalid api key' in error_str:
            raise AuthenticationError(f"Mistral authentication failed: {str(error)}")
        elif 'model not found' in error_str or 'does not exist' in error_str:
            raise ModelNotFoundError(f"Mistral model not found: {str(error)}")
        elif 'rate limit' in error_str or 'quota exceeded' in error_str:
            raise RateLimitError(f"Mistral rate limit exceeded: {str(error)}")
        else:
            raise LLMError(f"Mistral error: {str(error)}")

    def _track_usage(self, usage: Dict[str, int]) -> None:
        """
        Track token usage and calculate costs (legacy method).

        Args:
            usage: Usage statistics from Mistral response
        """
        self._track_usage_with_breakdown(usage)

    def _track_usage_with_breakdown(self, usage: Dict[str, int]) -> Dict[str, Any]:
        """
        Track token usage and calculate costs with detailed breakdown.

        Args:
            usage: Usage statistics from Mistral response

        Returns:
            Detailed cost breakdown dictionary
        """
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        total_tokens = usage.get('total_tokens', prompt_tokens + completion_tokens)

        # Update totals
        self._input_tokens += prompt_tokens
        self._output_tokens += completion_tokens

        # Calculate costs if pricing available
        cost_breakdown = {
            'input_tokens': prompt_tokens,
            'output_tokens': completion_tokens,
            'total_tokens': total_tokens,
            'input_cost_usd': 0.0,
            'output_cost_usd': 0.0,
            'total_cost_usd': 0.0,
            'model': self.model_name,
            'timestamp': time.time()
        }

        if self.model_name in self.MODEL_PRICING:
            pricing = self.MODEL_PRICING[self.model_name]

            # Calculate cost per 1K tokens with Decimal precision (matching OpenAI format)
            input_cost = (Decimal(str(prompt_tokens)) / Decimal('1000')) * pricing['input']
            output_cost = (Decimal(str(completion_tokens)) / Decimal('1000')) * pricing['output']
            total_cost = input_cost + output_cost

            # Round to 6 decimal places for maximum precision
            from decimal import ROUND_HALF_UP
            input_cost = input_cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
            output_cost = output_cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
            total_cost = total_cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)

            self._total_cost += total_cost

            # Update breakdown with calculated costs
            cost_breakdown.update({
                'input_cost_usd': float(input_cost),
                'output_cost_usd': float(output_cost),
                'total_cost_usd': float(total_cost)
            })

            # Add to history
            self.cost_history.append(cost_breakdown.copy())

            logger.debug(
                f"Mistral usage: {prompt_tokens} input + {completion_tokens} output tokens, "
                f"cost: ${float(total_cost):.6f}"
            )

        return cost_breakdown

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about the model and usage.

        Returns:
            Dictionary with model information, usage stats, and costs
        """
        base_info = super().get_model_info()

        # Add Mistral-specific information
        base_info.update({
            'max_context_tokens': self.MODEL_LIMITS.get(self.model_name),
            'supports_streaming': self._supports_streaming(),
            'input_tokens_used': self._input_tokens,
            'output_tokens_used': self._output_tokens,
            'total_cost_usd': float(self._total_cost),
            'pricing_per_1m_tokens': {
                'input': float(self.MODEL_PRICING.get(self.model_name, {}).get('input', 0)),
                'output': float(self.MODEL_PRICING.get(self.model_name, {}).get('output', 0))
            }
        })

        return base_info

    def get_cost_breakdown(self) -> Dict[str, Any]:
        """
        Get detailed cost breakdown for this adapter.

        Returns:
            Dictionary with detailed cost information
        """
        if self.model_name not in self.MODEL_PRICING:
            return {'error': 'Pricing not available for this model'}

        pricing = self.MODEL_PRICING[self.model_name]
        input_cost = (Decimal(str(self._input_tokens)) / 1000) * pricing['input']
        output_cost = (Decimal(str(self._output_tokens)) / 1000) * pricing['output']

        return {
            'model': self.model_name,
            'total_requests': self._request_count,
            'input_tokens': self._input_tokens,
            'output_tokens': self._output_tokens,
            'total_tokens': self._input_tokens + self._output_tokens,
            'input_cost_usd': float(input_cost),
            'output_cost_usd': float(output_cost),
            'total_cost_usd': float(self._total_cost),
            'avg_cost_per_request': float(self._total_cost / max(1, self._request_count)),
            'pricing_per_1k': {
                'input': float(pricing['input']),
                'output': float(pricing['output'])
            }
        }

    def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive cost tracking summary with analytics.

        Returns:
            Dictionary with cost analytics and recommendations
        """
        if not self.cost_history:
            return {
                'total_cost_usd': 0.0,
                'total_requests': 0,
                'total_tokens': 0,
                'average_cost_per_request': 0.0,
                'average_tokens_per_request': 0.0,
                'cost_breakdown': {'input': 0.0, 'output': 0.0}
            }

        total_requests = len(self.cost_history)
        total_tokens = sum(c['total_tokens'] for c in self.cost_history)
        total_input_cost = sum(c['input_cost_usd'] for c in self.cost_history)
        total_output_cost = sum(c['output_cost_usd'] for c in self.cost_history)

        return {
            'total_cost_usd': float(self._total_cost),
            'total_requests': total_requests,
            'total_tokens': total_tokens,
            'average_cost_per_request': float(self._total_cost / total_requests),
            'average_tokens_per_request': total_tokens / total_requests,
            'cost_breakdown': {
                'input': float(total_input_cost),
                'output': float(total_output_cost)
            },
            'model': self.model_name,
            'pricing_per_1k_tokens': {
                'input': float(self.MODEL_PRICING.get(self.model_name, self.MODEL_PRICING['mistral-small'])['input']),
                'output': float(self.MODEL_PRICING.get(self.model_name, self.MODEL_PRICING['mistral-small'])['output'])
            }
        }

    def estimate_cost(self, prompt: str, max_output_tokens: int = 500) -> Dict[str, Any]:
        """
        Estimate cost for a prompt before making the API call.

        Args:
            prompt: Input prompt text
            max_output_tokens: Estimated output token count

        Returns:
            Cost estimation breakdown
        """
        # Rough estimation for token counting (4 chars per token average)
        # Mistral doesn't provide a tokenizer library like OpenAI's tiktoken
        input_tokens = len(prompt) // 4

        # Get pricing
        pricing = self.MODEL_PRICING.get(self.model_name, self.MODEL_PRICING['mistral-small'])

        # Calculate estimated costs
        input_cost = (Decimal(str(input_tokens)) / Decimal('1000')) * pricing['input']
        output_cost = (Decimal(str(max_output_tokens)) / Decimal('1000')) * pricing['output']
        total_cost = input_cost + output_cost

        return {
            'estimated_input_tokens': input_tokens,
            'estimated_output_tokens': max_output_tokens,
            'estimated_total_tokens': input_tokens + max_output_tokens,
            'estimated_input_cost_usd': float(input_cost.quantize(Decimal('0.000001'))),
            'estimated_output_cost_usd': float(output_cost.quantize(Decimal('0.000001'))),
            'estimated_total_cost_usd': float(total_cost.quantize(Decimal('0.000001'))),
            'model': self.model_name,
            'note': 'Token estimation is approximate (Mistral does not provide a tokenizer library)'
        }


# Helper function for component factory registration
def create_mistral_adapter(**kwargs) -> MistralAdapter:
    """
    Factory function for creating Mistral adapter instances.

    Args:
        **kwargs: Configuration parameters for the adapter

    Returns:
        Configured Mistral adapter instance
    """
    return MistralAdapter(**kwargs)
