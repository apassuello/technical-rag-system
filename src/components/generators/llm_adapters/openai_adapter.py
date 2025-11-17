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
from typing import Dict, Any, Optional, Iterator, List, Union
from decimal import Decimal
import copy

try:
    import openai
    from openai import OpenAI
    import tiktoken
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None
    tiktoken = None

try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
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
                 timeout: float = 120.0):
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
        
        # Initialize tokenizer for accurate cost calculation
        self.tokenizer = None
        if tiktoken:
            try:
                self.tokenizer = tiktoken.encoding_for_model(model_name)
            except KeyError:
                # Fallback for unknown models
                logger.warning(f"No tokenizer found for {model_name}, using cl100k_base")
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Cost tracking
        self._total_cost = Decimal('0.00')
        self._input_tokens = 0
        self._output_tokens = 0
        self.cost_history = []
        
        # Validate model exists and pricing is available
        if model_name not in self.MODEL_PRICING:
            logger.warning(f"Pricing not available for model {model_name}, cost tracking disabled")
        
        logger.info(f"Initialized OpenAI adapter with model: {model_name}")
    
    @retry(
        retry=retry_if_exception_type(RateLimitError),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=1, max=60)
    )
    def _make_request(self, prompt: str, params: GenerationParams) -> Dict[str, Any]:
        """
        Make a request to OpenAI API with retry logic for rate limits.
        
        Args:
            prompt: The prompt to send to the model
            params: Generation parameters
            
        Returns:
            Raw response from OpenAI API with cost tracking
            
        Raises:
            RateLimitError: If rate limit is exceeded (triggers retry)
            AuthenticationError: If API key is invalid (no retry)
            ModelNotFoundError: If model doesn't exist (no retry)
            LLMError: For other API errors
        """
        try:
            # Prepare messages in chat format
            messages = self._prepare_messages(prompt)
            
            # Prepare request parameters - filter out None values
            request_params = {
                'model': self.model_name,
                'messages': messages
            }
            
            # Add generation parameters if they're not None
            if params.temperature is not None:
                request_params['temperature'] = params.temperature
            if params.max_tokens is not None:
                request_params['max_tokens'] = params.max_tokens
            if params.top_p is not None:
                request_params['top_p'] = params.top_p
            if params.frequency_penalty is not None:
                request_params['frequency_penalty'] = params.frequency_penalty
            if params.presence_penalty is not None:
                request_params['presence_penalty'] = params.presence_penalty
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
                'created': response.created,
                'request_time': request_time
            }
            
            # Track token usage and costs with detailed breakdown
            cost_breakdown = self._track_usage_with_breakdown(response_dict['usage'])
            response_dict['cost_breakdown'] = cost_breakdown
            
            return response_dict
            
        except openai.RateLimitError as e:
            logger.warning(f"OpenAI rate limit exceeded: {str(e)}")
            raise RateLimitError(f"OpenAI rate limit: {str(e)}")
        except openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication failed: {str(e)}")
            raise AuthenticationError(f"OpenAI authentication error: {str(e)}")
        except openai.NotFoundError as e:
            logger.error(f"OpenAI model not found: {str(e)}")
            raise ModelNotFoundError(f"OpenAI model '{self.model_name}' not found: {str(e)}")
        except openai.BadRequestError as e:
            logger.error(f"OpenAI bad request: {str(e)}")
            raise LLMError(f"OpenAI request error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected OpenAI error: {str(e)}")
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
        Track token usage and calculate costs (legacy method).
        
        Args:
            usage: Usage statistics from OpenAI response
        """
        self._track_usage_with_breakdown(usage)
        
    def _track_usage_with_breakdown(self, usage: Dict[str, int]) -> Dict[str, Any]:
        """
        Track token usage and calculate costs with detailed breakdown.
        
        Args:
            usage: Usage statistics from OpenAI response
            
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
            
            # Calculate cost per 1K tokens with Decimal precision
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
                f"OpenAI usage: {prompt_tokens} input + {completion_tokens} output tokens, "
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
                'input': float(self.MODEL_PRICING.get(self.model_name, self.MODEL_PRICING['gpt-3.5-turbo'])['input']),
                'output': float(self.MODEL_PRICING.get(self.model_name, self.MODEL_PRICING['gpt-3.5-turbo'])['output'])
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
        # Count input tokens using tiktoken if available
        if self.tokenizer:
            input_tokens = len(self.tokenizer.encode(prompt))
        else:
            # Fallback: rough estimation (4 chars per token average)
            input_tokens = len(prompt) // 4

        # Get pricing
        pricing = self.MODEL_PRICING.get(self.model_name, self.MODEL_PRICING['gpt-3.5-turbo'])

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
            'model': self.model_name
        }

    def generate_with_functions(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        params: Optional[GenerationParams] = None,
        max_iterations: int = 10,
        tool_choice: str = "auto"
    ) -> Dict[str, Any]:
        """
        Generate response with function calling support.

        Handles multi-turn conversations where the LLM can call functions
        iteratively to solve complex problems. Supports parallel function calls.

        Args:
            prompt: The initial user prompt
            tools: List of tool schemas in OpenAI format
                Example:
                    [
                        {
                            "type": "function",
                            "function": {
                                "name": "calculator",
                                "description": "Evaluate math expressions",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "expression": {
                                            "type": "string",
                                            "description": "Math expression"
                                        }
                                    },
                                    "required": ["expression"]
                                }
                            }
                        }
                    ]
            params: Generation parameters (optional)
            max_iterations: Maximum number of function calling iterations (default: 10)
            tool_choice: Tool selection mode - "auto", "none", or {"type": "function", "function": {"name": "tool_name"}}

        Returns:
            Dictionary with:
                - final_response: Final text response from LLM
                - iterations: Number of function calling iterations
                - function_calls: List of all function calls made
                - total_tokens: Total tokens used across all iterations
                - total_cost_usd: Total cost in USD
                - cost_breakdown: Detailed cost breakdown per iteration
                - messages: Complete conversation history

        Raises:
            LLMError: If function calling fails
            ValueError: If tools list is empty or invalid

        Example:
            >>> adapter = OpenAIAdapter()
            >>> tools = registry.get_openai_schemas()
            >>> result = adapter.generate_with_functions(
            ...     prompt="What is 25 * 47?",
            ...     tools=tools,
            ...     params=GenerationParams(temperature=0.0)
            ... )
            >>> print(result['final_response'])
            >>> print(f"Iterations: {result['iterations']}")
            >>> print(f"Total cost: ${result['total_cost_usd']:.6f}")
        """
        if not tools:
            raise ValueError("Tools list cannot be empty for function calling")

        if params is None:
            params = GenerationParams()

        # Initialize conversation with user message
        messages = [{"role": "user", "content": prompt}]

        # Track metrics across all iterations
        all_function_calls = []
        iteration_costs = []
        total_tokens = 0
        total_cost = Decimal('0.0')

        # Multi-turn function calling loop
        for iteration in range(max_iterations):
            logger.debug(f"Function calling iteration {iteration + 1}/{max_iterations}")

            try:
                # Make API request with tools
                response = self._make_function_request(
                    messages=messages,
                    tools=tools,
                    params=params,
                    tool_choice=tool_choice
                )

                # Track usage and cost for this iteration
                usage = response.get('usage', {})
                cost_breakdown = response.get('cost_breakdown', {})

                iteration_tokens = usage.get('total_tokens', 0)
                iteration_cost = Decimal(str(cost_breakdown.get('total_cost_usd', 0.0)))

                total_tokens += iteration_tokens
                total_cost += iteration_cost
                iteration_costs.append(cost_breakdown)

                # Extract response
                if not response.get('choices'):
                    raise LLMError("No choices in OpenAI function calling response")

                choice = response['choices'][0]
                message = choice.get('message', {})
                finish_reason = choice.get('finish_reason')

                # Add assistant message to conversation
                assistant_message = {
                    "role": "assistant",
                    "content": message.get('content')
                }

                # Check if there are tool calls
                tool_calls = message.get('tool_calls')

                if tool_calls:
                    # Add tool_calls to assistant message
                    assistant_message['tool_calls'] = tool_calls
                    messages.append(assistant_message)

                    # Process each tool call (supports parallel calls)
                    for tool_call in tool_calls:
                        tool_call_id = tool_call.id
                        function_name = tool_call.function.name

                        try:
                            function_args = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse function arguments: {e}")
                            function_args = {}

                        # Record function call
                        function_call_record = {
                            'id': tool_call_id,
                            'name': function_name,
                            'arguments': function_args,
                            'iteration': iteration + 1
                        }
                        all_function_calls.append(function_call_record)

                        logger.debug(
                            f"Function call {tool_call_id}: {function_name}({function_args})"
                        )

                    # Note: Actual function execution happens externally
                    # This method only handles the LLM conversation flow
                    # The caller must provide function results via the returned data

                    # If we have tool calls but this is our last iteration, break
                    if iteration >= max_iterations - 1:
                        logger.warning(
                            f"Reached max iterations ({max_iterations}) with pending tool calls"
                        )
                        break

                    # For this implementation, we return early and let the caller
                    # handle function execution and continuation
                    # This is the pattern that works best with the tool registry
                    return {
                        'status': 'requires_function_execution',
                        'pending_tool_calls': tool_calls,
                        'messages': messages,
                        'iterations': iteration + 1,
                        'function_calls': all_function_calls,
                        'total_tokens': total_tokens,
                        'total_cost_usd': float(total_cost),
                        'cost_breakdown': iteration_costs,
                        'finish_reason': finish_reason
                    }

                elif finish_reason == 'stop':
                    # Normal completion - we have a final answer
                    messages.append(assistant_message)

                    final_response = message.get('content', '')

                    return {
                        'status': 'completed',
                        'final_response': final_response,
                        'iterations': iteration + 1,
                        'function_calls': all_function_calls,
                        'total_tokens': total_tokens,
                        'total_cost_usd': float(total_cost),
                        'cost_breakdown': iteration_costs,
                        'messages': messages,
                        'finish_reason': finish_reason
                    }

                else:
                    # Unexpected finish reason
                    messages.append(assistant_message)
                    logger.warning(f"Unexpected finish_reason: {finish_reason}")

                    return {
                        'status': 'incomplete',
                        'final_response': message.get('content', ''),
                        'iterations': iteration + 1,
                        'function_calls': all_function_calls,
                        'total_tokens': total_tokens,
                        'total_cost_usd': float(total_cost),
                        'cost_breakdown': iteration_costs,
                        'messages': messages,
                        'finish_reason': finish_reason
                    }

            except Exception as e:
                logger.error(f"Error in function calling iteration {iteration + 1}: {e}")

                return {
                    'status': 'error',
                    'error': str(e),
                    'iterations': iteration + 1,
                    'function_calls': all_function_calls,
                    'total_tokens': total_tokens,
                    'total_cost_usd': float(total_cost),
                    'cost_breakdown': iteration_costs,
                    'messages': messages
                }

        # Reached max iterations without completion
        return {
            'status': 'max_iterations_reached',
            'iterations': max_iterations,
            'function_calls': all_function_calls,
            'total_tokens': total_tokens,
            'total_cost_usd': float(total_cost),
            'cost_breakdown': iteration_costs,
            'messages': messages
        }

    def continue_with_function_results(
        self,
        messages: List[Dict[str, Any]],
        function_results: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        params: Optional[GenerationParams] = None,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Continue function calling conversation with function results.

        This method continues a conversation after function execution,
        allowing for multi-turn function calling.

        Args:
            messages: Conversation history (must include tool_calls)
            function_results: List of function execution results
                Example:
                    [
                        {
                            "tool_call_id": "call_abc123",
                            "content": "25 * 47 = 1175"
                        }
                    ]
            tools: List of tool schemas
            params: Generation parameters (optional)
            max_iterations: Maximum additional iterations

        Returns:
            Same format as generate_with_functions()

        Example:
            >>> # Initial call
            >>> result = adapter.generate_with_functions(prompt, tools)
            >>> if result['status'] == 'requires_function_execution':
            ...     # Execute functions
            ...     function_results = execute_functions(result['pending_tool_calls'])
            ...     # Continue conversation
            ...     final = adapter.continue_with_function_results(
            ...         messages=result['messages'],
            ...         function_results=function_results,
            ...         tools=tools
            ...     )
        """
        if not function_results:
            raise ValueError("function_results cannot be empty")

        if params is None:
            params = GenerationParams()

        # Make a copy of messages to avoid mutation
        messages = copy.deepcopy(messages)

        # Add function results to conversation
        for func_result in function_results:
            tool_message = {
                "role": "tool",
                "tool_call_id": func_result['tool_call_id'],
                "content": str(func_result.get('content', ''))
            }
            messages.append(tool_message)

        # Track metrics
        all_function_calls = []
        iteration_costs = []
        total_tokens = 0
        total_cost = Decimal('0.0')

        # Continue the conversation loop
        for iteration in range(max_iterations):
            logger.debug(f"Continuation iteration {iteration + 1}/{max_iterations}")

            try:
                # Make API request
                response = self._make_function_request(
                    messages=messages,
                    tools=tools,
                    params=params,
                    tool_choice="auto"
                )

                # Track usage
                usage = response.get('usage', {})
                cost_breakdown = response.get('cost_breakdown', {})

                iteration_tokens = usage.get('total_tokens', 0)
                iteration_cost = Decimal(str(cost_breakdown.get('total_cost_usd', 0.0)))

                total_tokens += iteration_tokens
                total_cost += iteration_cost
                iteration_costs.append(cost_breakdown)

                # Extract response
                choice = response['choices'][0]
                message = choice.get('message', {})
                finish_reason = choice.get('finish_reason')

                assistant_message = {
                    "role": "assistant",
                    "content": message.get('content')
                }

                tool_calls = message.get('tool_calls')

                if tool_calls:
                    assistant_message['tool_calls'] = tool_calls
                    messages.append(assistant_message)

                    # Record tool calls
                    for tool_call in tool_calls:
                        try:
                            function_args = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError:
                            function_args = {}

                        all_function_calls.append({
                            'id': tool_call.id,
                            'name': tool_call.function.name,
                            'arguments': function_args,
                            'iteration': iteration + 1
                        })

                    # Return for more function execution
                    return {
                        'status': 'requires_function_execution',
                        'pending_tool_calls': tool_calls,
                        'messages': messages,
                        'iterations': iteration + 1,
                        'function_calls': all_function_calls,
                        'total_tokens': total_tokens,
                        'total_cost_usd': float(total_cost),
                        'cost_breakdown': iteration_costs,
                        'finish_reason': finish_reason
                    }

                elif finish_reason == 'stop':
                    messages.append(assistant_message)

                    return {
                        'status': 'completed',
                        'final_response': message.get('content', ''),
                        'iterations': iteration + 1,
                        'function_calls': all_function_calls,
                        'total_tokens': total_tokens,
                        'total_cost_usd': float(total_cost),
                        'cost_breakdown': iteration_costs,
                        'messages': messages,
                        'finish_reason': finish_reason
                    }

                else:
                    messages.append(assistant_message)

                    return {
                        'status': 'incomplete',
                        'final_response': message.get('content', ''),
                        'iterations': iteration + 1,
                        'function_calls': all_function_calls,
                        'total_tokens': total_tokens,
                        'total_cost_usd': float(total_cost),
                        'cost_breakdown': iteration_costs,
                        'messages': messages,
                        'finish_reason': finish_reason
                    }

            except Exception as e:
                logger.error(f"Error in continuation iteration {iteration + 1}: {e}")

                return {
                    'status': 'error',
                    'error': str(e),
                    'iterations': iteration + 1,
                    'function_calls': all_function_calls,
                    'total_tokens': total_tokens,
                    'total_cost_usd': float(total_cost),
                    'cost_breakdown': iteration_costs,
                    'messages': messages
                }

        return {
            'status': 'max_iterations_reached',
            'iterations': max_iterations,
            'function_calls': all_function_calls,
            'total_tokens': total_tokens,
            'total_cost_usd': float(total_cost),
            'cost_breakdown': iteration_costs,
            'messages': messages
        }

    def _make_function_request(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        params: GenerationParams,
        tool_choice: Union[str, Dict[str, Any]] = "auto"
    ) -> Dict[str, Any]:
        """
        Make a function calling request to OpenAI API.

        Args:
            messages: Conversation messages
            tools: Tool schemas
            params: Generation parameters
            tool_choice: Tool selection mode

        Returns:
            Response dictionary with usage and cost tracking

        Raises:
            LLMError: If request fails
        """
        try:
            # Prepare request parameters
            request_params = {
                'model': self.model_name,
                'messages': messages,
                'tools': tools,
                'tool_choice': tool_choice
            }

            # Add generation parameters if not None
            if params.temperature is not None:
                request_params['temperature'] = params.temperature
            if params.max_tokens is not None:
                request_params['max_tokens'] = params.max_tokens
            if params.top_p is not None:
                request_params['top_p'] = params.top_p
            if params.frequency_penalty is not None:
                request_params['frequency_penalty'] = params.frequency_penalty
            if params.presence_penalty is not None:
                request_params['presence_penalty'] = params.presence_penalty

            logger.debug(f"Making OpenAI function calling request to {self.model_name}")
            start_time = time.time()

            response = self.client.chat.completions.create(**request_params)

            request_time = time.time() - start_time
            logger.debug(f"OpenAI function request completed in {request_time:.2f}s")

            # Convert to dictionary format
            response_dict = {
                'id': response.id,
                'model': response.model,
                'choices': [],
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                    'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                    'total_tokens': response.usage.total_tokens if response.usage else 0
                },
                'created': response.created,
                'request_time': request_time
            }

            # Process choices (handle tool calls)
            for choice in response.choices:
                choice_dict = {
                    'message': {
                        'role': choice.message.role,
                        'content': choice.message.content
                    },
                    'finish_reason': choice.finish_reason
                }

                # Add tool_calls if present
                if choice.message.tool_calls:
                    choice_dict['message']['tool_calls'] = [
                        {
                            'id': tc.id,
                            'type': tc.type,
                            'function': {
                                'name': tc.function.name,
                                'arguments': tc.function.arguments
                            }
                        }
                        for tc in choice.message.tool_calls
                    ]

                response_dict['choices'].append(choice_dict)

            # Track cost
            cost_breakdown = self._track_usage_with_breakdown(response_dict['usage'])
            response_dict['cost_breakdown'] = cost_breakdown

            return response_dict

        except openai.RateLimitError as e:
            logger.warning(f"OpenAI rate limit exceeded: {str(e)}")
            raise RateLimitError(f"OpenAI rate limit: {str(e)}")
        except openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication failed: {str(e)}")
            raise AuthenticationError(f"OpenAI authentication error: {str(e)}")
        except openai.NotFoundError as e:
            logger.error(f"OpenAI model not found: {str(e)}")
            raise ModelNotFoundError(f"OpenAI model '{self.model_name}' not found: {str(e)}")
        except openai.BadRequestError as e:
            logger.error(f"OpenAI bad request: {str(e)}")
            raise LLMError(f"OpenAI request error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected OpenAI error: {str(e)}")
            self._handle_openai_error(e)


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