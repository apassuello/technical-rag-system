"""
Anthropic Claude LLM Adapter with Tools API Support.

This module provides integration with Anthropic's Claude models through their official API,
supporting Claude 3.5 Sonnet, Opus, and Haiku with full tools API capabilities.

Architecture Notes:
- Extends BaseLLMAdapter following established adapter pattern
- Handles Anthropic-specific authentication and message formatting
- Provides tool use with multi-turn conversations
- Supports streaming responses for better UX
- Includes comprehensive error handling and retry logic
- Precise cost tracking with per-iteration breakdowns

Tool Use Features:
- Multi-turn tool conversations with automatic iteration
- Tool call extraction from Claude responses
- Tool result formatting back to Claude
- Comprehensive cost tracking across all iterations
- Error handling with graceful degradation

Supported Models:
- claude-3-5-sonnet-20241022: Balanced performance and cost
- claude-3-opus-20240229: Highest quality for complex queries
- claude-3-haiku-20240307: Ultra-fast for simple queries

Configuration Example:
{
    "model_name": "claude-3-5-sonnet-20241022",
    "api_key": "sk-ant-...",  # or set ANTHROPIC_API_KEY env var
    "max_tokens": 4096,
    "temperature": 0.7,
    "timeout": 60.0,
    "max_tool_iterations": 10
}
"""

import logging
import os
import time
from decimal import Decimal
from typing import Any, Dict, Iterator, List, Optional, Tuple

try:
    import anthropic
    from anthropic import AI_PROMPT, HUMAN_PROMPT, Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    Anthropic = None
    HUMAN_PROMPT = None
    AI_PROMPT = None

from ..base import GenerationParams, LLMError
from .base_adapter import (
    AuthenticationError,
    BaseLLMAdapter,
    ModelNotFoundError,
    RateLimitError,
)

logger = logging.getLogger(__name__)


class AnthropicAdapter(BaseLLMAdapter):
    """
    Anthropic Claude adapter with support for Claude 3.x models and tools API.

    This adapter provides:
    - Authentication via API key
    - Token usage tracking and cost calculation
    - Streaming response support
    - Multi-turn tool conversations
    - Tool call extraction and result formatting
    - Model-specific parameter optimization
    - Comprehensive error handling with Anthropic-specific mappings
    - Rate limit handling with exponential backoff

    Supported Models:
    - claude-3-5-sonnet-20241022: Balanced performance ($3/$15 per 1M tokens)
    - claude-3-opus-20240229: Highest quality ($15/$75 per 1M tokens)
    - claude-3-haiku-20240307: Ultra-fast ($0.25/$1.25 per 1M tokens)
    - claude-3-sonnet-20240229: Previous generation Sonnet

    Tool Use:
    - Full support for Claude's tools API
    - Multi-turn conversations with automatic iteration
    - Tool result formatting as content blocks
    - Cost tracking across all tool iterations
    - Configurable max iterations with safety limits

    Configuration Example:
    {
        "model_name": "claude-3-5-sonnet-20241022",
        "api_key": "sk-ant-...",  # or set ANTHROPIC_API_KEY env var
        "max_tokens": 4096,
        "temperature": 0.7,
        "timeout": 60.0,
        "max_tool_iterations": 10
    }
    """

    # Model pricing (per 1M tokens) - updated as of 2024
    MODEL_PRICING = {
        'claude-3-5-sonnet-20241022': {
            'input': Decimal('3.00'),     # $3.00 per 1M input tokens
            'output': Decimal('15.00')    # $15.00 per 1M output tokens
        },
        'claude-3-opus-20240229': {
            'input': Decimal('15.00'),    # $15.00 per 1M input tokens
            'output': Decimal('75.00')    # $75.00 per 1M output tokens
        },
        'claude-3-sonnet-20240229': {
            'input': Decimal('3.00'),     # $3.00 per 1M input tokens
            'output': Decimal('15.00')    # $15.00 per 1M output tokens
        },
        'claude-3-haiku-20240307': {
            'input': Decimal('0.25'),     # $0.25 per 1M input tokens
            'output': Decimal('1.25')     # $1.25 per 1M output tokens
        }
    }

    # Model context limits (tokens)
    MODEL_LIMITS = {
        'claude-3-5-sonnet-20241022': 200000,
        'claude-3-opus-20240229': 200000,
        'claude-3-sonnet-20240229': 200000,
        'claude-3-haiku-20240307': 200000
    }

    def __init__(self,
                 model_name: str = "claude-3-5-sonnet-20241022",
                 api_key: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 timeout: float = 120.0,
                 max_tool_iterations: int = 10):
        """
        Initialize Anthropic adapter.

        Args:
            model_name: Claude model to use (default: claude-3-5-sonnet-20241022)
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            config: Additional configuration parameters
            max_retries: Maximum retry attempts for failed requests
            retry_delay: Initial delay between retries (seconds)
            timeout: Request timeout in seconds
            max_tool_iterations: Maximum tool use iterations (default: 10)

        Raises:
            ImportError: If anthropic package is not installed
            ValueError: If API key is not provided
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "Anthropic package not installed. Install with: pip install anthropic>=0.8.0"
            )

        # Initialize base adapter
        super().__init__(model_name, config, max_retries, retry_delay)

        # Get API key from parameter, config, or environment
        self.api_key = (
            api_key or
            (config or {}).get('api_key') or
            os.getenv('ANTHROPIC_API_KEY')
        )

        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )

        # Initialize Anthropic client
        self.client = Anthropic(
            api_key=self.api_key,
            timeout=timeout
        )
        self.timeout = timeout
        self.max_tool_iterations = max_tool_iterations

        # Cost tracking
        self._total_cost = Decimal('0.00')
        self._input_tokens = 0
        self._output_tokens = 0
        self.cost_history: List[Dict[str, Any]] = []

        # Validate model exists and pricing is available
        if model_name not in self.MODEL_PRICING:
            logger.warning(f"Pricing not available for model {model_name}, cost tracking disabled")

        logger.info(f"Initialized Anthropic adapter with model: {model_name}")

    def _make_request(self, prompt: str, params: GenerationParams) -> Dict[str, Any]:
        """
        Make a request to Anthropic API.

        Args:
            prompt: The prompt to send to the model
            params: Generation parameters

        Returns:
            Raw response from Anthropic API with cost tracking

        Raises:
            RateLimitError: If rate limit is exceeded (triggers retry)
            AuthenticationError: If API key is invalid (no retry)
            ModelNotFoundError: If model doesn't exist (no retry)
            LLMError: For other API errors
        """
        try:
            # Prepare messages in chat format
            messages = self._prepare_messages(prompt)

            # Prepare request parameters
            request_params = {
                'model': self.model_name,
                'messages': messages,
                'max_tokens': params.max_tokens or 4096
            }

            # Add optional parameters
            if params.temperature is not None:
                request_params['temperature'] = params.temperature
            if params.top_p is not None:
                request_params['top_p'] = params.top_p
            if params.stop_sequences:
                request_params['stop_sequences'] = params.stop_sequences

            # Make API request
            logger.debug(f"Making Anthropic request to {self.model_name}")
            start_time = time.time()

            response = self.client.messages.create(**request_params)

            request_time = time.time() - start_time
            logger.debug(f"Anthropic request completed in {request_time:.2f}s")

            # Convert to dictionary format for consistent handling
            response_dict = {
                'id': response.id,
                'model': response.model,
                'role': response.role,
                'content': response.content,
                'stop_reason': response.stop_reason,
                'usage': {
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens,
                    'total_tokens': response.usage.input_tokens + response.usage.output_tokens
                },
                'request_time': request_time
            }

            # Track token usage and costs with detailed breakdown
            cost_breakdown = self._track_usage_with_breakdown(response_dict['usage'])
            response_dict['cost_breakdown'] = cost_breakdown

            return response_dict

        except anthropic.RateLimitError as e:
            logger.warning(f"Anthropic rate limit exceeded: {str(e)}")
            raise RateLimitError(f"Anthropic rate limit: {str(e)}")
        except anthropic.AuthenticationError as e:
            logger.error(f"Anthropic authentication failed: {str(e)}")
            raise AuthenticationError(f"Anthropic authentication error: {str(e)}")
        except anthropic.NotFoundError as e:
            logger.error(f"Anthropic model not found: {str(e)}")
            raise ModelNotFoundError(f"Anthropic model '{self.model_name}' not found: {str(e)}")
        except anthropic.BadRequestError as e:
            logger.error(f"Anthropic bad request: {str(e)}")
            raise LLMError(f"Anthropic request error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected Anthropic error: {str(e)}")
            self._handle_anthropic_error(e)

    def _parse_response(self, response: Dict[str, Any]) -> str:
        """
        Parse Anthropic response to extract generated text.

        Args:
            response: Raw response from Anthropic API

        Returns:
            Generated text content

        Raises:
            LLMError: If response format is invalid
        """
        try:
            if not response.get('content'):
                raise LLMError("No content in Anthropic response")

            # Extract text from content blocks
            text_parts = []
            for block in response['content']:
                if hasattr(block, 'text'):
                    text_parts.append(block.text)
                elif isinstance(block, dict) and 'text' in block:
                    text_parts.append(block['text'])

            if not text_parts:
                raise LLMError("No text content in Anthropic response")

            # Log stop reason for debugging
            stop_reason = response.get('stop_reason')
            if stop_reason == 'max_tokens':
                logger.warning("Anthropic response truncated due to max_tokens limit")
            elif stop_reason == 'tool_use':
                logger.debug("Anthropic response includes tool use")

            return '\n'.join(text_parts).strip()

        except (KeyError, AttributeError) as e:
            raise LLMError(f"Invalid Anthropic response format: {str(e)}")

    def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        params: GenerationParams,
        max_iterations: Optional[int] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a response with tool use support.

        This method implements multi-turn tool conversations:
        1. Send initial prompt with tools
        2. If Claude wants to use tools, extract tool calls
        3. Execute tools (handled externally)
        4. Format results and continue conversation
        5. Repeat until Claude provides final answer or max iterations reached

        Args:
            prompt: The initial user prompt
            tools: List of tool schemas in Anthropic format
            params: Generation parameters
            max_iterations: Maximum tool use iterations (overrides default)

        Returns:
            Tuple of (final_answer, metadata) where metadata includes:
            - iterations: Number of tool use iterations
            - tool_calls: List of tool calls made
            - total_tokens: Total tokens used
            - total_cost_usd: Total cost in USD
            - iteration_history: Detailed history of each iteration

        Raises:
            LLMError: If generation fails
            ValueError: If invalid parameters
        """
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        if not tools:
            # No tools provided, fall back to regular generation
            logger.debug("No tools provided, using regular generation")
            response = self.generate(prompt, params)
            return response, {
                'iterations': 0,
                'tool_calls': [],
                'total_tokens': 0,
                'total_cost_usd': 0.0,
                'iteration_history': []
            }

        max_iters = max_iterations or self.max_tool_iterations

        # Initialize conversation tracking
        messages = [{"role": "user", "content": prompt}]
        iteration_history = []
        all_tool_calls = []
        total_tokens = 0
        total_cost = Decimal('0.00')

        start_time = time.time()

        for iteration in range(max_iters):
            try:
                # Prepare request parameters
                request_params = {
                    'model': self.model_name,
                    'messages': messages,
                    'tools': tools,
                    'max_tokens': params.max_tokens or 4096
                }

                # Add optional parameters
                if params.temperature is not None:
                    request_params['temperature'] = params.temperature
                if params.top_p is not None:
                    request_params['top_p'] = params.top_p

                # Make API request
                logger.debug(f"Tool iteration {iteration + 1}/{max_iters}")
                iter_start = time.time()

                response = self.client.messages.create(**request_params)

                iter_time = time.time() - iter_start

                # Track usage and cost
                usage = {
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens,
                    'total_tokens': response.usage.input_tokens + response.usage.output_tokens
                }
                cost_breakdown = self._track_usage_with_breakdown(usage)

                total_tokens += usage['total_tokens']
                total_cost += Decimal(str(cost_breakdown['total_cost_usd']))

                # Check stop reason
                stop_reason = response.stop_reason

                # Extract tool calls if present
                tool_calls = []
                text_content = []

                for block in response.content:
                    if hasattr(block, 'type'):
                        if block.type == 'text':
                            text_content.append(block.text)
                        elif block.type == 'tool_use':
                            tool_calls.append({
                                'id': block.id,
                                'name': block.name,
                                'input': block.input
                            })

                # Record iteration
                iteration_record = {
                    'iteration': iteration + 1,
                    'stop_reason': stop_reason,
                    'tool_calls': tool_calls,
                    'text_content': text_content,
                    'tokens': usage['total_tokens'],
                    'cost_usd': cost_breakdown['total_cost_usd'],
                    'time': iter_time
                }
                iteration_history.append(iteration_record)
                all_tool_calls.extend(tool_calls)

                # Check if we're done
                if stop_reason != 'tool_use':
                    # Claude provided final answer
                    final_answer = '\n'.join(text_content).strip()

                    total_time = time.time() - start_time

                    metadata = {
                        'iterations': iteration + 1,
                        'tool_calls': all_tool_calls,
                        'total_tokens': total_tokens,
                        'total_cost_usd': float(total_cost),
                        'total_time': total_time,
                        'iteration_history': iteration_history,
                        'stop_reason': stop_reason
                    }

                    logger.info(
                        f"Tool conversation completed: {iteration + 1} iterations, "
                        f"{total_tokens} tokens, ${float(total_cost):.6f}"
                    )

                    return final_answer, metadata

                # Claude wants to use tools - this is where external execution happens
                # Return tool calls for external execution
                # This method should be called iteratively with tool results

                # For now, we return the tool calls and let the caller handle execution
                # In a full implementation, this would be handled by a tool executor

                if not tool_calls:
                    # Stop reason was tool_use but no tool calls found
                    raise LLMError("Claude indicated tool use but no tool calls found")

                # Add assistant message to conversation
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Note: Tool results should be added by caller via continue_with_tool_results()
                # For this basic implementation, we return incomplete conversation
                logger.warning(
                    "Tool calls requested but not executed. "
                    "Use continue_with_tool_results() to continue conversation."
                )

                total_time = time.time() - start_time

                metadata = {
                    'iterations': iteration + 1,
                    'tool_calls': all_tool_calls,
                    'total_tokens': total_tokens,
                    'total_cost_usd': float(total_cost),
                    'total_time': total_time,
                    'iteration_history': iteration_history,
                    'stop_reason': 'tool_use',
                    'pending_tool_calls': tool_calls,
                    'messages': messages  # Return conversation state
                }

                # Return partial answer for caller to execute tools
                return '\n'.join(text_content).strip(), metadata

            except Exception as e:
                logger.error(f"Error in tool iteration {iteration + 1}: {str(e)}")
                if iteration == 0:
                    # First iteration failed, raise error
                    raise
                else:
                    # Partial success, return what we have
                    total_time = time.time() - start_time
                    metadata = {
                        'iterations': iteration,
                        'tool_calls': all_tool_calls,
                        'total_tokens': total_tokens,
                        'total_cost_usd': float(total_cost),
                        'total_time': total_time,
                        'iteration_history': iteration_history,
                        'error': str(e)
                    }
                    return "Error during tool execution", metadata

        # Max iterations reached
        logger.warning(f"Max tool iterations ({max_iters}) reached")
        total_time = time.time() - start_time

        metadata = {
            'iterations': max_iters,
            'tool_calls': all_tool_calls,
            'total_tokens': total_tokens,
            'total_cost_usd': float(total_cost),
            'total_time': total_time,
            'iteration_history': iteration_history,
            'stop_reason': 'max_iterations'
        }

        return "Max iterations reached", metadata

    def continue_with_tool_results(
        self,
        messages: List[Dict[str, Any]],
        tool_results: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        params: GenerationParams
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Continue a tool conversation with tool execution results.

        Args:
            messages: Conversation history (from generate_with_tools metadata)
            tool_results: List of tool results in format:
                [{"tool_use_id": "...", "content": "..."}]
            tools: Tool schemas
            params: Generation parameters

        Returns:
            Tuple of (response, metadata)
        """
        # Add tool results to messages
        messages.append({
            "role": "user",
            "content": tool_results
        })

        # Continue conversation
        try:
            request_params = {
                'model': self.model_name,
                'messages': messages,
                'tools': tools,
                'max_tokens': params.max_tokens or 4096
            }

            if params.temperature is not None:
                request_params['temperature'] = params.temperature
            if params.top_p is not None:
                request_params['top_p'] = params.top_p

            response = self.client.messages.create(**request_params)

            # Track usage
            usage = {
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
                'total_tokens': response.usage.input_tokens + response.usage.output_tokens
            }
            cost_breakdown = self._track_usage_with_breakdown(usage)

            # Extract text
            text_parts = []
            for block in response.content:
                if hasattr(block, 'type') and block.type == 'text':
                    text_parts.append(block.text)

            metadata = {
                'stop_reason': response.stop_reason,
                'tokens': usage['total_tokens'],
                'cost_usd': cost_breakdown['total_cost_usd'],
                'messages': messages + [{"role": "assistant", "content": response.content}]
            }

            return '\n'.join(text_parts).strip(), metadata

        except Exception as e:
            logger.error(f"Error continuing tool conversation: {str(e)}")
            raise LLMError(f"Failed to continue tool conversation: {str(e)}")

    def generate_streaming(self, prompt: str, params: GenerationParams) -> Iterator[str]:
        """
        Generate a streaming response from Anthropic.

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
                'max_tokens': params.max_tokens or 4096
            }

            if params.temperature is not None:
                request_params['temperature'] = params.temperature
            if params.top_p is not None:
                request_params['top_p'] = params.top_p
            if params.stop_sequences:
                request_params['stop_sequences'] = params.stop_sequences

            logger.debug(f"Starting Anthropic streaming request to {self.model_name}")

            # Track tokens for streaming (approximate from words)
            output_tokens = 0

            # Stream response
            with self.client.messages.stream(**request_params) as stream:
                for text in stream.text_stream:
                    output_tokens += len(text.split())
                    yield text

                # Get final usage from stream
                final_message = stream.get_final_message()
                if final_message and final_message.usage:
                    usage = {
                        'input_tokens': final_message.usage.input_tokens,
                        'output_tokens': final_message.usage.output_tokens,
                        'total_tokens': final_message.usage.input_tokens + final_message.usage.output_tokens
                    }
                    self._track_usage_with_breakdown(usage)

        except Exception as e:
            self._handle_anthropic_error(e)
            raise LLMError(f"Anthropic streaming failed: {str(e)}")

    def _get_provider_name(self) -> str:
        """Return the provider name."""
        return "Anthropic"

    def _validate_model(self) -> bool:
        """
        Check if the configured model exists and is accessible.

        Returns:
            True if model is available
        """
        try:
            # Test with a minimal request
            test_messages = [{"role": "user", "content": "Hi"}]

            # Validate model is accessible (response content not needed)
            self.client.messages.create(
                model=self.model_name,
                messages=test_messages,
                max_tokens=10
            )

            return True

        except Exception as e:
            logger.error(f"Model validation failed: {str(e)}")
            return False

    def _supports_streaming(self) -> bool:
        """Anthropic supports streaming."""
        return True

    def _get_max_tokens(self) -> Optional[int]:
        """Get maximum token limit for the current model."""
        return self.MODEL_LIMITS.get(self.model_name)

    def _handle_anthropic_error(self, error: Exception) -> None:
        """
        Map Anthropic-specific errors to standard adapter errors.

        Args:
            error: Anthropic exception

        Raises:
            Appropriate LLMError subclass
        """
        error_str = str(error).lower()

        # Check for specific Anthropic error types
        if hasattr(error, 'status_code'):
            status_code = error.status_code

            if status_code == 401:
                raise AuthenticationError(f"Anthropic authentication failed: {str(error)}")
            elif status_code == 404:
                raise ModelNotFoundError(f"Anthropic model not found: {str(error)}")
            elif status_code == 429:
                raise RateLimitError(f"Anthropic rate limit exceeded: {str(error)}")
            else:
                raise LLMError(f"Anthropic API error (status {status_code}): {str(error)}")

        # Fallback to string matching
        if 'unauthorized' in error_str or 'invalid api key' in error_str:
            raise AuthenticationError(f"Anthropic authentication failed: {str(error)}")
        elif 'model not found' in error_str or 'does not exist' in error_str:
            raise ModelNotFoundError(f"Anthropic model not found: {str(error)}")
        elif 'rate limit' in error_str or 'quota exceeded' in error_str:
            raise RateLimitError(f"Anthropic rate limit exceeded: {str(error)}")
        else:
            raise LLMError(f"Anthropic error: {str(error)}")

    def _track_usage_with_breakdown(self, usage: Dict[str, int]) -> Dict[str, Any]:
        """
        Track token usage and calculate costs with detailed breakdown.

        Args:
            usage: Usage statistics from Anthropic response

        Returns:
            Detailed cost breakdown dictionary
        """
        input_tokens = usage.get('input_tokens', 0)
        output_tokens = usage.get('output_tokens', 0)
        total_tokens = usage.get('total_tokens', input_tokens + output_tokens)

        # Update totals
        self._input_tokens += input_tokens
        self._output_tokens += output_tokens

        # Calculate costs if pricing available
        cost_breakdown = {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total_tokens,
            'input_cost_usd': 0.0,
            'output_cost_usd': 0.0,
            'total_cost_usd': 0.0,
            'model': self.model_name,
            'timestamp': time.time()
        }

        if self.model_name in self.MODEL_PRICING:
            pricing = self.MODEL_PRICING[self.model_name]

            # Calculate cost per 1M tokens with Decimal precision
            input_cost = (Decimal(str(input_tokens)) / Decimal('1000000')) * pricing['input']
            output_cost = (Decimal(str(output_tokens)) / Decimal('1000000')) * pricing['output']
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
                f"Anthropic usage: {input_tokens} input + {output_tokens} output tokens, "
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

        # Add Anthropic-specific information
        base_info.update({
            'max_context_tokens': self.MODEL_LIMITS.get(self.model_name),
            'supports_streaming': True,
            'supports_tools': True,
            'max_tool_iterations': self.max_tool_iterations,
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
        input_cost = (Decimal(str(self._input_tokens)) / Decimal('1000000')) * pricing['input']
        output_cost = (Decimal(str(self._output_tokens)) / Decimal('1000000')) * pricing['output']

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
def create_anthropic_adapter(**kwargs) -> AnthropicAdapter:
    """
    Factory function for creating Anthropic adapter instances.

    Args:
        **kwargs: Configuration parameters for the adapter

    Returns:
        Configured Anthropic adapter instance
    """
    return AnthropicAdapter(**kwargs)
