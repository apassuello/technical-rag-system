"""
OpenAI LLM Adapter Implementation.

This module provides integration with OpenAI's GPT models through their official API,
supporting both GPT-3.5-turbo and GPT-4-turbo for cost-effective multi-model routing.

Architecture Notes:
- Extends BaseLLMAdapter following established adapter pattern
- Handles OpenAI-specific authentication and rate limiting
- Provides precise token counting and cost tracking
- Supports streaming responses for better UX
- Includes comprehensive error handling and retry logic

Epic 1 Integration:
- Critical component for cost optimization (40%+ reduction target)
- Enables intelligent routing from Epic1QueryAnalyzer complexity analysis
- Provides high-quality responses for complex technical queries
"""

import os
import time
import json
import logging
from typing import Dict, Any, Optional, Iterator, List
from decimal import Decimal

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

from .base_adapter import BaseLLMAdapter, RateLimitError, AuthenticationError, ModelNotFoundError
from ..base import GenerationParams, LLMError

logger = logging.getLogger(__name__)


class OpenAIAdapter(BaseLLMAdapter):
    """
    OpenAI LLM adapter with support for GPT-3.5-turbo and GPT-4-turbo models.
    
    This adapter provides:
    - Authentication via API key
    - Token usage tracking and cost calculation
    - Streaming response support
    - Model-specific parameter optimization
    - Comprehensive error handling with OpenAI-specific mappings
    - Rate limit handling with exponential backoff
    
    Supported Models:
    - gpt-3.5-turbo: Cost-effective for medium complexity queries
    - gpt-4-turbo: High-quality for complex technical queries
    - gpt-4o-mini: Ultra-fast for simple queries (if available)
    
    Configuration Example:
    {
        "model_name": "gpt-3.5-turbo",
        "api_key": "sk-...", # or set OPENAI_API_KEY env var
        "base_url": "https://api.openai.com/v1", # optional
        "organization": "org-...", # optional
        "max_tokens": 1000,
        "temperature": 0.7,
        "timeout": 30.0
    }
    """
    
    # Model pricing (per 1K tokens) - updated as of 2024
    MODEL_PRICING = {
        'gpt-3.5-turbo': {
            'input': Decimal('0.0010'),   # $0.001 per 1K input tokens
            'output': Decimal('0.0020')   # $0.002 per 1K output tokens
        },
        'gpt-4-turbo': {
            'input': Decimal('0.0100'),   # $0.01 per 1K input tokens
            'output': Decimal('0.0300')   # $0.03 per 1K output tokens
        },
        'gpt-4o-mini': {
            'input': Decimal('0.0001'),   # $0.0001 per 1K input tokens
            'output': Decimal('0.0006')   # $0.0006 per 1K output tokens
        }
    }
    
    # Model context limits (tokens)
    MODEL_LIMITS = {
        'gpt-3.5-turbo': 16385,
        'gpt-4-turbo': 128000,
        'gpt-4o-mini': 128000
    }
    
    def __init__(self,
                 model_name: str = "gpt-3.5-turbo",
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 organization: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 timeout: float = 30.0):
        """
        Initialize OpenAI adapter.
        
        Args:
            model_name: OpenAI model to use (default: gpt-3.5-turbo)
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            base_url: API base URL (optional, for custom endpoints)
            organization: OpenAI organization ID (optional)
            config: Additional configuration parameters
            max_retries: Maximum retry attempts for failed requests
            retry_delay: Initial delay between retries (seconds)
            timeout: Request timeout in seconds
            
        Raises:
            ImportError: If openai package is not installed
            ValueError: If API key is not provided
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI package not installed. Install with: pip install openai"
            )
        
        # Initialize base adapter
        super().__init__(model_name, config, max_retries, retry_delay)
        
        # Get API key from parameter, config, or environment
        self.api_key = (
            api_key or
            (config or {}).get('api_key') or
            os.getenv('OPENAI_API_KEY')
        )
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        # Initialize OpenAI client
        client_kwargs = {
            'api_key': self.api_key,
            'timeout': timeout
        }
        
        if base_url:
            client_kwargs['base_url'] = base_url
        if organization:
            client_kwargs['organization'] = organization
            
        self.client = OpenAI(**client_kwargs)
        self.timeout = timeout
        
        # Cost tracking
        self._total_cost = Decimal('0.00')
        self._input_tokens = 0
        self._output_tokens = 0
        
        # Validate model exists and pricing is available
        if model_name not in self.MODEL_PRICING:
            logger.warning(f"Pricing not available for model {model_name}, cost tracking disabled")
        
        logger.info(f"Initialized OpenAI adapter with model: {model_name}")
    
    def _make_request(self, prompt: str, params: GenerationParams) -> Dict[str, Any]:
        """
        Make a request to OpenAI API.
        
        Args:
            prompt: The prompt to send to the model
            params: Generation parameters
            
        Returns:
            Raw response from OpenAI API
            
        Raises:
            RateLimitError: If rate limit is exceeded
            AuthenticationError: If API key is invalid
            ModelNotFoundError: If model doesn't exist
            LLMError: For other API errors
        """
        try:
            # Prepare messages in chat format
            messages = self._prepare_messages(prompt)
            
            # Prepare request parameters
            request_params = {
                'model': self.model_name,
                'messages': messages,
                'temperature': params.temperature,
                'max_tokens': params.max_tokens,
                'top_p': params.top_p,
                'frequency_penalty': params.frequency_penalty,
                'presence_penalty': params.presence_penalty
            }
            
            # Add stop sequences if provided
            if params.stop_sequences:
                request_params['stop'] = params.stop_sequences
            
            # Make API request
            logger.debug(f"Making OpenAI request to {self.model_name}")
            start_time = time.time()
            
            response = self.client.chat.completions.create(**request_params)
            
            request_time = time.time() - start_time
            logger.debug(f"OpenAI request completed in {request_time:.2f}s")
            
            # Convert to dictionary format for consistent handling
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
                'created': response.created
            }
            
            # Track token usage and costs
            self._track_usage(response_dict['usage'])
            
            return response_dict
            
        except Exception as e:
            # Map OpenAI exceptions to standard errors
            self._handle_openai_error(e)
    
    def _parse_response(self, response: Dict[str, Any]) -> str:
        """
        Parse OpenAI response to extract generated text.
        
        Args:
            response: Raw response from OpenAI API
            
        Returns:
            Generated text content
            
        Raises:
            LLMError: If response format is invalid
        """
        try:
            if not response.get('choices'):
                raise LLMError("No choices in OpenAI response")
            
            choice = response['choices'][0]
            message = choice.get('message', {})
            content = message.get('content', '')
            
            if not content:
                raise LLMError("Empty content in OpenAI response")
            
            # Log finish reason for debugging
            finish_reason = choice.get('finish_reason')
            if finish_reason == 'length':
                logger.warning("OpenAI response truncated due to max_tokens limit")
            elif finish_reason == 'content_filter':
                logger.warning("OpenAI response filtered due to content policy")
            
            return content.strip()
            
        except KeyError as e:
            raise LLMError(f"Invalid OpenAI response format: missing {str(e)}")
    
    def generate_streaming(self, prompt: str, params: GenerationParams) -> Iterator[str]:
        """
        Generate a streaming response from OpenAI.
        
        Args:
            prompt: The prompt to send to the model
            params: Generation parameters
            
        Yields:
            Generated text chunks as they arrive
            
        Raises:
            LLMError: If streaming generation fails
        """
        try:
            messages = self._prepare_messages(prompt)
            
            request_params = {
                'model': self.model_name,
                'messages': messages,
                'temperature': params.temperature,
                'max_tokens': params.max_tokens,
                'top_p': params.top_p,
                'frequency_penalty': params.frequency_penalty,
                'presence_penalty': params.presence_penalty,
                'stream': True
            }
            
            if params.stop_sequences:
                request_params['stop'] = params.stop_sequences
            
            logger.debug(f"Starting OpenAI streaming request to {self.model_name}")
            
            # Track tokens for streaming (approximation)
            prompt_tokens = len(prompt.split()) * 1.3  # Rough approximation
            completion_tokens = 0
            
            # Stream response
            stream = self.client.chat.completions.create(**request_params)
            
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    completion_tokens += len(content.split()) * 1.3
                    yield content
            
            # Track approximate usage for streaming
            usage = {
                'prompt_tokens': int(prompt_tokens),
                'completion_tokens': int(completion_tokens),
                'total_tokens': int(prompt_tokens + completion_tokens)
            }
            self._track_usage(usage)
            
        except Exception as e:
            self._handle_openai_error(e)
            raise LLMError(f"OpenAI streaming failed: {str(e)}")
    
    def _get_provider_name(self) -> str:
        """Return the provider name."""
        return "OpenAI"
    
    def _validate_model(self) -> bool:
        """
        Check if the configured model exists and is accessible.
        
        Returns:
            True if model is available
        """
        try:
            # Test with a minimal request
            test_messages = [{"role": "user", "content": "Hi"}]
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=test_messages,
                max_tokens=1,
                temperature=0
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Model validation failed: {str(e)}")
            return False
    
    def _supports_streaming(self) -> bool:
        """OpenAI supports streaming."""
        return True
    
    def _get_max_tokens(self) -> Optional[int]:
        """Get maximum token limit for the current model."""
        return self.MODEL_LIMITS.get(self.model_name)
    
    def _handle_openai_error(self, error: Exception) -> None:
        """
        Map OpenAI-specific errors to standard adapter errors.
        
        Args:
            error: OpenAI exception
            
        Raises:
            Appropriate LLMError subclass
        """
        error_str = str(error).lower()
        
        # Check for specific OpenAI error types if available
        if hasattr(error, 'status_code'):
            status_code = error.status_code
            
            if status_code == 401:
                raise AuthenticationError(f"OpenAI authentication failed: {str(error)}")
            elif status_code == 404:
                raise ModelNotFoundError(f"OpenAI model not found: {str(error)}")
            elif status_code == 429:
                raise RateLimitError(f"OpenAI rate limit exceeded: {str(error)}")
            else:
                raise LLMError(f"OpenAI API error (status {status_code}): {str(error)}")
        
        # Fallback to string matching
        if 'unauthorized' in error_str or 'invalid api key' in error_str:
            raise AuthenticationError(f"OpenAI authentication failed: {str(error)}")
        elif 'model not found' in error_str or 'does not exist' in error_str:
            raise ModelNotFoundError(f"OpenAI model not found: {str(error)}")
        elif 'rate limit' in error_str or 'quota exceeded' in error_str:
            raise RateLimitError(f"OpenAI rate limit exceeded: {str(error)}")
        else:
            raise LLMError(f"OpenAI error: {str(error)}")
    
    def _track_usage(self, usage: Dict[str, int]) -> None:
        """
        Track token usage and calculate costs.
        
        Args:
            usage: Usage statistics from OpenAI response
        """
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        
        # Update totals
        self._input_tokens += prompt_tokens
        self._output_tokens += completion_tokens
        
        # Calculate costs if pricing available
        if self.model_name in self.MODEL_PRICING:
            pricing = self.MODEL_PRICING[self.model_name]
            
            # Calculate cost per 1K tokens
            input_cost = (Decimal(str(prompt_tokens)) / 1000) * pricing['input']
            output_cost = (Decimal(str(completion_tokens)) / 1000) * pricing['output']
            total_cost = input_cost + output_cost
            
            self._total_cost += total_cost
            
            logger.debug(
                f"OpenAI usage: {prompt_tokens} input + {completion_tokens} output tokens, "
                f"cost: ${total_cost:.4f}"
            )
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about the model and usage.
        
        Returns:
            Dictionary with model information, usage stats, and costs
        """
        base_info = super().get_model_info()
        
        # Add OpenAI-specific information
        base_info.update({
            'max_context_tokens': self.MODEL_LIMITS.get(self.model_name),
            'supports_streaming': True,
            'input_tokens_used': self._input_tokens,
            'output_tokens_used': self._output_tokens,
            'total_cost_usd': float(self._total_cost),
            'pricing_per_1k_tokens': {
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


# Helper function for component factory registration
def create_openai_adapter(**kwargs) -> OpenAIAdapter:
    """
    Factory function for creating OpenAI adapter instances.
    
    Args:
        **kwargs: Configuration parameters for the adapter
        
    Returns:
        Configured OpenAI adapter instance
    """
    return OpenAIAdapter(**kwargs)