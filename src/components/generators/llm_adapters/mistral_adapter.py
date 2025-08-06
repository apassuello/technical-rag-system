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

import os
import time
import json
import logging
from typing import Dict, Any, Optional, Iterator, List
from decimal import Decimal

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from .base_adapter import BaseLLMAdapter, RateLimitError, AuthenticationError, ModelNotFoundError
from ..base import GenerationParams, LLMError

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
    
    # Model pricing (per 1M tokens) - updated as of 2024
    MODEL_PRICING = {
        'mistral-tiny': {
            'input': Decimal('0.25'),     # $0.25 per 1M input tokens
            'output': Decimal('0.25')     # $0.25 per 1M output tokens
        },
        'mistral-small': {
            'input': Decimal('2.00'),     # $2.00 per 1M input tokens  
            'output': Decimal('6.00')     # $6.00 per 1M output tokens
        },
        'mistral-medium': {
            'input': Decimal('2.70'),     # $2.70 per 1M input tokens
            'output': Decimal('8.10')     # $8.10 per 1M output tokens
        },
        'mistral-large': {
            'input': Decimal('8.00'),     # $8.00 per 1M input tokens
            'output': Decimal('24.00')    # $24.00 per 1M output tokens
        }
    }
    
    # Model context limits (tokens)
    MODEL_LIMITS = {
        'mistral-tiny': 32000,
        'mistral-small': 32000,
        'mistral-medium': 32000,
        'mistral-large': 32000
    }
    
    # API endpoints
    DEFAULT_BASE_URL = "https://api.mistral.ai/v1"
    
    def __init__(self,
                 model_name: str = "mistral-small",
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 timeout: float = 30.0):
        """
        Initialize Mistral adapter.
        
        Args:
            model_name: Mistral model to use (default: mistral-small)
            api_key: Mistral API key (or set MISTRAL_API_KEY env var)
            base_url: API base URL (optional)
            config: Additional configuration parameters
            max_retries: Maximum retry attempts for failed requests
            retry_delay: Initial delay between retries (seconds)
            timeout: Request timeout in seconds
            
        Raises:
            ImportError: If requests package is not installed
            ValueError: If API key is not provided
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "Requests package not installed. Install with: pip install requests"
            )
        
        # Initialize base adapter
        super().__init__(model_name, config, max_retries, retry_delay)
        
        # Get API key from parameter, config, or environment
        self.api_key = (
            api_key or
            (config or {}).get('api_key') or
            os.getenv('MISTRAL_API_KEY')
        )
        
        if not self.api_key:
            raise ValueError(
                "Mistral API key required. Set MISTRAL_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        # Set API endpoints
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.timeout = timeout
        
        # Headers for API requests
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Cost tracking
        self._total_cost = Decimal('0.00')
        self._input_tokens = 0
        self._output_tokens = 0
        
        # Validate model pricing is available
        if model_name not in self.MODEL_PRICING:
            logger.warning(f"Pricing not available for model {model_name}, cost tracking disabled")
        
        logger.info(f"Initialized Mistral adapter with model: {model_name}")
    
    def _make_request(self, prompt: str, params: GenerationParams) -> Dict[str, Any]:
        """
        Make a request to Mistral API.
        
        Args:
            prompt: The prompt to send to the model
            params: Generation parameters
            
        Returns:
            Raw response from Mistral API
            
        Raises:
            RateLimitError: If rate limit is exceeded
            AuthenticationError: If API key is invalid
            ModelNotFoundError: If model doesn't exist
            LLMError: For other API errors
        """
        try:
            # Prepare messages in chat format
            messages = self._prepare_messages(prompt)
            
            # Prepare request payload
            payload = {
                'model': self.model_name,
                'messages': messages,
                'temperature': params.temperature,
                'max_tokens': params.max_tokens,
                'top_p': params.top_p
            }
            
            # Add stop sequences if provided
            if params.stop_sequences:
                payload['stop'] = params.stop_sequences
            
            # Make API request
            url = f"{self.base_url}/chat/completions"
            logger.debug(f"Making Mistral request to {self.model_name}")
            start_time = time.time()
            
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            
            request_time = time.time() - start_time
            logger.debug(f"Mistral request completed in {request_time:.2f}s")
            
            # Handle HTTP errors
            if response.status_code != 200:
                self._handle_http_error(response)
            
            # Parse JSON response
            response_data = response.json()
            
            # Track token usage and costs
            if 'usage' in response_data:
                self._track_usage(response_data['usage'])
            
            return response_data
            
        except requests.exceptions.RequestException as e:
            raise LLMError(f"Mistral request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise LLMError(f"Invalid JSON response from Mistral: {str(e)}")
        except Exception as e:
            self._handle_mistral_error(e)
    
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
        
        Returns:
            True if model is available
        """
        try:
            # Test with a minimal request
            test_messages = [{"role": "user", "content": "Hi"}]
            payload = {
                'model': self.model_name,
                'messages': test_messages,
                'max_tokens': 1,
                'temperature': 0
            }
            
            url = f"{self.base_url}/chat/completions"
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            
            return response.status_code == 200
            
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
        Track token usage and calculate costs.
        
        Args:
            usage: Usage statistics from Mistral response
        """
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        
        # Update totals
        self._input_tokens += prompt_tokens
        self._output_tokens += completion_tokens
        
        # Calculate costs if pricing available
        if self.model_name in self.MODEL_PRICING:
            pricing = self.MODEL_PRICING[self.model_name]
            
            # Calculate cost per 1M tokens (Mistral pricing is per 1M)
            input_cost = (Decimal(str(prompt_tokens)) / 1000000) * pricing['input']
            output_cost = (Decimal(str(completion_tokens)) / 1000000) * pricing['output']
            total_cost = input_cost + output_cost
            
            self._total_cost += total_cost
            
            logger.debug(
                f"Mistral usage: {prompt_tokens} input + {completion_tokens} output tokens, "
                f"cost: ${total_cost:.6f}"
            )
    
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
        input_cost = (Decimal(str(self._input_tokens)) / 1000000) * pricing['input']
        output_cost = (Decimal(str(self._output_tokens)) / 1000000) * pricing['output']
        
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
            'pricing_per_1m': {
                'input': float(pricing['input']),
                'output': float(pricing['output'])
            }
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