"""
Base adapter implementation for LLM providers.

This module provides common functionality shared by all LLM adapters,
including error handling, retry logic, and format conversion utilities.

Architecture Notes:
- All LLM-specific logic must be in adapters, not in the orchestrator
- Adapters handle authentication, format conversion, and error mapping
- Each provider's peculiarities are hidden behind the unified interface
"""

import time
import logging
from typing import Dict, Any, Optional, List, Iterator
from abc import abstractmethod
import json

from ..base import LLMAdapter, LLMError, GenerationParams, ConfigurableComponent

logger = logging.getLogger(__name__)


class RateLimitError(LLMError):
    """Rate limit exceeded error."""
    pass


class AuthenticationError(LLMError):
    """Authentication failed error."""
    pass


class ModelNotFoundError(LLMError):
    """Model not found error."""
    pass


class BaseLLMAdapter(LLMAdapter, ConfigurableComponent):
    """
    Base implementation for LLM adapters with common functionality.
    
    Provides:
    - Retry logic with exponential backoff
    - Common error handling and mapping
    - Response validation
    - Metrics collection
    - Configuration management
    
    Subclasses must implement:
    - _make_request: Provider-specific API call
    - _parse_response: Convert provider response to text
    - _get_provider_name: Return provider name
    - _validate_model: Check if model exists
    """
    
    def __init__(self, 
                 model_name: str,
                 config: Optional[Dict[str, Any]] = None,
                 max_retries: int = 3,
                 retry_delay: float = 1.0):
        """
        Initialize base LLM adapter.
        
        Args:
            model_name: Name of the model to use
            config: Provider-specific configuration
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (seconds)
        """
        super().__init__(config)
        self.model_name = model_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._request_count = 0
        self._total_tokens = 0
        self._last_request_time = 0
        
    def generate(self, prompt: str, params: GenerationParams) -> str:
        """
        Generate a response with retry logic and error handling.
        
        Args:
            prompt: The prompt to send to the LLM
            params: Generation parameters
            
        Returns:
            Generated text response
            
        Raises:
            LLMError: If generation fails after retries
        """
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty")
            
        # Track request timing
        start_time = time.time()
        self._last_request_time = start_time
        
        # Attempt generation with retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # Make provider-specific request
                response = self._make_request(prompt, params)
                
                # Parse provider response
                text = self._parse_response(response)
                
                # Validate response
                if not text or not text.strip():
                    raise LLMError("Empty response from LLM")
                
                # Update metrics
                self._request_count += 1
                if 'usage' in response:
                    self._total_tokens += response['usage'].get('total_tokens', 0)
                
                # Log success
                elapsed = time.time() - start_time
                logger.info(f"{self._get_provider_name()} generation completed in {elapsed:.2f}s")
                
                return text
                
            except RateLimitError as e:
                # Rate limit - use exponential backoff
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Rate limit hit, retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"Rate limit exceeded after {self.max_retries} attempts")
                    
            except AuthenticationError as e:
                # Authentication errors are not retryable
                logger.error(f"Authentication failed: {str(e)}")
                raise
                
            except Exception as e:
                # Other errors - retry with backoff
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Generation failed: {str(e)}, retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"Generation failed after {self.max_retries} attempts: {str(e)}")
        
        # All retries exhausted
        raise LLMError(f"Generation failed after {self.max_retries} attempts: {str(last_error)}")
    
    def generate_streaming(self, prompt: str, params: GenerationParams) -> Iterator[str]:
        """
        Generate a streaming response.
        
        Default implementation calls generate() and yields the result.
        Subclasses should override for true streaming support.
        
        Args:
            prompt: The prompt to send to the LLM
            params: Generation parameters
            
        Yields:
            Generated text chunks
        """
        # Default: yield full response as single chunk
        # Subclasses should override for true streaming
        logger.warning(f"{self._get_provider_name()} adapter using simulated streaming")
        yield self.generate(prompt, params)
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model and provider.
        
        Returns:
            Dictionary with model information
        """
        return {
            'provider': self._get_provider_name(),
            'model': self.model_name,
            'supports_streaming': self._supports_streaming(),
            'max_tokens': self._get_max_tokens(),
            'requests_made': self._request_count,
            'total_tokens_used': self._total_tokens,
            'configuration': self._get_safe_config()
        }
    
    def validate_connection(self) -> bool:
        """
        Validate the connection to the LLM provider.
        
        Returns:
            True if connection is valid
            
        Raises:
            LLMError: If connection validation fails
        """
        try:
            # Validate model exists
            if not self._validate_model():
                raise ModelNotFoundError(f"Model '{self.model_name}' not found")
            
            # Make a minimal test request
            test_prompt = "Hello"
            test_params = GenerationParams(max_tokens=10, temperature=0)
            response = self.generate(test_prompt, test_params)
            
            return bool(response)
            
        except Exception as e:
            logger.error(f"Connection validation failed: {str(e)}")
            raise LLMError(f"Failed to validate {self._get_provider_name()} connection: {str(e)}")
    
    # Abstract methods that subclasses must implement
    
    @abstractmethod
    def _make_request(self, prompt: str, params: GenerationParams) -> Dict[str, Any]:
        """
        Make a request to the LLM provider.
        
        Args:
            prompt: The prompt to send
            params: Generation parameters
            
        Returns:
            Raw response from provider
            
        Raises:
            Provider-specific exceptions
        """
        pass
    
    @abstractmethod
    def _parse_response(self, response: Dict[str, Any]) -> str:
        """
        Parse the provider response to extract generated text.
        
        Args:
            response: Raw response from provider
            
        Returns:
            Generated text
        """
        pass
    
    @abstractmethod
    def _get_provider_name(self) -> str:
        """Return the provider name (e.g., 'Ollama', 'OpenAI')."""
        pass
    
    @abstractmethod
    def _validate_model(self) -> bool:
        """Check if the configured model exists/is available."""
        pass
    
    # Optional methods that subclasses can override
    
    def _supports_streaming(self) -> bool:
        """Whether this adapter supports true streaming."""
        return False
    
    def _get_max_tokens(self) -> Optional[int]:
        """Get maximum token limit for this model."""
        return None
    
    def _get_safe_config(self) -> Dict[str, Any]:
        """Get configuration with sensitive data removed."""
        safe_config = self.config.copy()
        # Remove sensitive keys
        sensitive_keys = ['api_key', 'token', 'secret', 'password']
        for key in sensitive_keys:
            if key in safe_config:
                safe_config[key] = '***'
        return safe_config
    
    # Utility methods for subclasses
    
    def _handle_provider_error(self, error: Exception) -> None:
        """
        Map provider-specific errors to standard errors.
        
        Subclasses should override to handle specific error types.
        
        Args:
            error: Provider-specific error
            
        Raises:
            Appropriate LLMError subclass
        """
        error_msg = str(error).lower()
        
        if 'rate limit' in error_msg or '429' in error_msg:
            raise RateLimitError(str(error))
        elif 'unauthorized' in error_msg or '401' in error_msg or 'api key' in error_msg:
            raise AuthenticationError(str(error))
        elif 'not found' in error_msg or '404' in error_msg:
            raise ModelNotFoundError(str(error))
        else:
            raise LLMError(f"Provider error: {str(error)}")
    
    def _prepare_messages(self, prompt: str) -> List[Dict[str, str]]:
        """
        Prepare messages in chat format.
        
        Many providers expect chat-style message format.
        
        Args:
            prompt: The prompt text
            
        Returns:
            List of message dictionaries
        """
        return [{"role": "user", "content": prompt}]
    
    def _extract_content(self, message: Dict[str, Any]) -> str:
        """
        Extract content from a message object.
        
        Handles various message formats from different providers.
        
        Args:
            message: Message object
            
        Returns:
            Extracted content string
        """
        # Try common content locations
        if isinstance(message, str):
            return message
        elif isinstance(message, dict):
            return (message.get('content') or 
                   message.get('text') or 
                   message.get('message') or 
                   str(message))
        else:
            return str(message)