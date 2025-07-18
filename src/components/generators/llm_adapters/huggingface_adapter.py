"""
HuggingFace LLM adapter implementation.

This adapter provides integration with HuggingFace Inference API, handling
the specific API format and response structure of HuggingFace models.

Architecture Notes:
- Converts between unified interface and HuggingFace API format
- Handles both chat completion and text generation endpoints
- Supports automatic model selection and fallback
- Maps HuggingFace errors to standard LLMError types
"""

import os
import logging
import time
from typing import Dict, Any, Optional, List, Iterator
from datetime import datetime

from .base_adapter import BaseLLMAdapter, LLMError, ModelNotFoundError, AuthenticationError, RateLimitError
from ..base import GenerationParams

logger = logging.getLogger(__name__)

# Check for HuggingFace Hub availability
try:
    from huggingface_hub import InferenceClient
    HF_HUB_AVAILABLE = True
except ImportError:
    HF_HUB_AVAILABLE = False
    logger.warning("huggingface_hub not available. Install with: pip install huggingface-hub")


class HuggingFaceAdapter(BaseLLMAdapter):
    """
    Adapter for HuggingFace Inference API integration.
    
    Features:
    - Support for both chat completion and text generation
    - Automatic model selection and fallback
    - OpenAI-compatible chat completion format
    - Comprehensive error handling and retry logic
    - Multiple model support with automatic fallback
    
    Configuration:
    - api_token: HuggingFace API token (required)
    - timeout: Request timeout in seconds (default: 30)
    - use_chat_completion: Prefer chat completion over text generation
    - fallback_models: List of models to try if primary fails
    """
    
    # Models that work well with chat completion format
    CHAT_MODELS = [
        "microsoft/DialoGPT-medium",       # Proven conversational model
        "google/gemma-2-2b-it",            # Instruction-tuned, good for Q&A
        "meta-llama/Llama-3.2-3B-Instruct", # If available with token
        "Qwen/Qwen2.5-1.5B-Instruct",     # Small, fast, good quality
    ]
    
    # Fallback models for classic text generation
    CLASSIC_MODELS = [
        "google/flan-t5-small",            # Good for instructions
        "deepset/roberta-base-squad2",     # Q&A specific
        "facebook/bart-base",              # Summarization
    ]
    
    def __init__(self,
                 model_name: str = "microsoft/DialoGPT-medium",
                 api_token: Optional[str] = None,
                 timeout: int = 30,
                 use_chat_completion: bool = True,
                 fallback_models: Optional[List[str]] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize HuggingFace adapter.
        
        Args:
            model_name: HuggingFace model name
            api_token: HuggingFace API token
            timeout: Request timeout in seconds
            use_chat_completion: Prefer chat completion over text generation
            fallback_models: List of fallback models to try
            config: Additional configuration
        """
        if not HF_HUB_AVAILABLE:
            raise ImportError("huggingface_hub is required for HuggingFace adapter. Install with: pip install huggingface-hub")
        
        # Get API token from various sources
        self.api_token = (
            api_token or 
            os.getenv("HUGGINGFACE_API_TOKEN") or 
            os.getenv("HF_TOKEN") or 
            os.getenv("HF_API_TOKEN")
        )
        
        if not self.api_token:
            raise AuthenticationError("HuggingFace API token required. Set HF_TOKEN environment variable or pass api_token parameter.")
        
        # Merge configuration
        adapter_config = {
            'api_token': self.api_token,
            'timeout': timeout,
            'use_chat_completion': use_chat_completion,
            'fallback_models': fallback_models or [],
            **(config or {})
        }
        
        super().__init__(model_name, adapter_config)
        
        self.timeout = adapter_config['timeout']
        self.use_chat_completion = adapter_config['use_chat_completion']
        self.fallback_models = adapter_config['fallback_models']
        
        # Initialize client
        self.client = InferenceClient(token=self.api_token)
        
        # Test connection and determine best model (only if not using dummy token)
        if not self.api_token.startswith("dummy_"):
            self._test_connection()
        else:
            logger.info("Using dummy token, skipping connection test")
        
        logger.info(f"Initialized HuggingFace adapter for model '{self.model_name}' (chat_completion: {self.use_chat_completion})")
    
    def _make_request(self, prompt: str, params: GenerationParams) -> Dict[str, Any]:
        """
        Make a request to HuggingFace API.
        
        Args:
            prompt: The prompt to send
            params: Generation parameters
            
        Returns:
            HuggingFace API response
            
        Raises:
            Various request exceptions
        """
        try:
            if self.use_chat_completion:
                return self._make_chat_completion_request(prompt, params)
            else:
                return self._make_text_generation_request(prompt, params)
        except Exception as e:
            # Try fallback models if primary fails
            for fallback_model in self.fallback_models:
                try:
                    logger.info(f"Trying fallback model: {fallback_model}")
                    original_model = self.model_name
                    self.model_name = fallback_model
                    
                    if self.use_chat_completion:
                        result = self._make_chat_completion_request(prompt, params)
                    else:
                        result = self._make_text_generation_request(prompt, params)
                    
                    # Success with fallback
                    logger.info(f"Successfully used fallback model: {fallback_model}")
                    return result
                    
                except Exception as fallback_error:
                    logger.warning(f"Fallback model {fallback_model} failed: {fallback_error}")
                    # Restore original model name
                    self.model_name = original_model
                    continue
            
            # All models failed
            self._handle_provider_error(e)
    
    def _make_chat_completion_request(self, prompt: str, params: GenerationParams) -> Dict[str, Any]:
        """Make a chat completion request."""
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = self.client.chat_completion(
                messages=messages,
                model=self.model_name,
                temperature=params.temperature,
                max_tokens=params.max_tokens,
                stream=False
            )
            
            # Extract content from response
            if hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content
                return {
                    'content': content,
                    'model': self.model_name,
                    'usage': getattr(response, 'usage', {}),
                    'response_type': 'chat_completion'
                }
            else:
                # Handle different response formats
                if hasattr(response, 'generated_text'):
                    content = response.generated_text
                else:
                    content = str(response)
                
                return {
                    'content': content,
                    'model': self.model_name,
                    'usage': {},
                    'response_type': 'chat_completion'
                }
                
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise
    
    def _make_text_generation_request(self, prompt: str, params: GenerationParams) -> Dict[str, Any]:
        """Make a text generation request."""
        try:
            response = self.client.text_generation(
                model=self.model_name,
                prompt=prompt,
                max_new_tokens=params.max_tokens,
                temperature=params.temperature,
                do_sample=params.temperature > 0,
                top_p=params.top_p,
                stop_sequences=params.stop_sequences
            )
            
            # Handle response format
            if isinstance(response, str):
                content = response
            else:
                content = getattr(response, 'generated_text', str(response))
            
            return {
                'content': content,
                'model': self.model_name,
                'usage': {},
                'response_type': 'text_generation'
            }
            
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            raise
    
    def _parse_response(self, response: Dict[str, Any]) -> str:
        """
        Parse HuggingFace response to extract generated text.
        
        Args:
            response: HuggingFace API response
            
        Returns:
            Generated text
        """
        content = response.get('content', '')
        
        # Log usage if available
        if 'usage' in response and response['usage']:
            usage = response['usage']
            total_tokens = usage.get('total_tokens', 0)
            if total_tokens > 0:
                logger.debug(f"HuggingFace used {total_tokens} tokens for generation")
        
        return content
    
    def generate_streaming(self, prompt: str, params: GenerationParams) -> Iterator[str]:
        """
        Generate a streaming response from HuggingFace.
        
        Args:
            prompt: The prompt to send
            params: Generation parameters
            
        Yields:
            Generated text chunks
        """
        try:
            if self.use_chat_completion:
                # Try streaming chat completion
                messages = [{"role": "user", "content": prompt}]
                
                response = self.client.chat_completion(
                    messages=messages,
                    model=self.model_name,
                    temperature=params.temperature,
                    max_tokens=params.max_tokens,
                    stream=True
                )
                
                for chunk in response:
                    if hasattr(chunk, 'choices') and chunk.choices:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, 'content') and delta.content:
                            yield delta.content
            else:
                # Fallback to non-streaming for text generation
                logger.warning("Streaming not supported for text generation, falling back to non-streaming")
                yield self.generate(prompt, params)
                
        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            # Fallback to non-streaming
            yield self.generate(prompt, params)
    
    def _get_provider_name(self) -> str:
        """Return the provider name."""
        return "HuggingFace"
    
    def _validate_model(self) -> bool:
        """Check if the model exists in HuggingFace."""
        try:
            # Try a simple test request
            test_prompt = "Hello"
            
            if self.use_chat_completion:
                test_messages = [{"role": "user", "content": test_prompt}]
                response = self.client.chat_completion(
                    messages=test_messages,
                    model=self.model_name,
                    max_tokens=10,
                    temperature=0.1
                )
            else:
                response = self.client.text_generation(
                    model=self.model_name,
                    prompt=test_prompt,
                    max_new_tokens=10
                )
            
            return bool(response)
            
        except Exception as e:
            logger.warning(f"Model validation failed: {e}")
            return False
    
    def _supports_streaming(self) -> bool:
        """HuggingFace supports streaming for chat completion."""
        return self.use_chat_completion
    
    def _get_max_tokens(self) -> Optional[int]:
        """Get max tokens for current model."""
        # Model-specific limits (approximate)
        model_limits = {
            'microsoft/DialoGPT-medium': 1024,
            'google/gemma-2-2b-it': 8192,
            'meta-llama/Llama-3.2-3B-Instruct': 4096,
            'Qwen/Qwen2.5-1.5B-Instruct': 32768,
            'google/flan-t5-small': 512,
            'deepset/roberta-base-squad2': 512,
            'facebook/bart-base': 1024,
        }
        
        # Check for exact match
        if self.model_name in model_limits:
            return model_limits[self.model_name]
        
        # Check for partial match
        for model_prefix, limit in model_limits.items():
            if model_prefix in self.model_name:
                return limit
        
        # Default for unknown models
        return 1024
    
    def _test_connection(self) -> None:
        """Test the connection and find the best working model."""
        logger.info("Testing HuggingFace API connection...")
        
        # Test primary model first
        if self._validate_model():
            logger.info(f"Primary model {self.model_name} is working")
            return
        
        # Try chat models if using chat completion
        if self.use_chat_completion:
            for model in self.CHAT_MODELS:
                if model != self.model_name:
                    try:
                        logger.info(f"Testing chat model: {model}")
                        original_model = self.model_name
                        self.model_name = model
                        
                        if self._validate_model():
                            logger.info(f"Found working chat model: {model}")
                            return
                        
                        # Restore original if failed
                        self.model_name = original_model
                        
                    except Exception as e:
                        logger.warning(f"Chat model {model} failed: {e}")
                        continue
        
        # Try classic models as fallback
        logger.info("Trying classic text generation models...")
        for model in self.CLASSIC_MODELS:
            try:
                logger.info(f"Testing classic model: {model}")
                original_model = self.model_name
                original_chat = self.use_chat_completion
                
                self.model_name = model
                self.use_chat_completion = False
                
                if self._validate_model():
                    logger.info(f"Found working classic model: {model}")
                    return
                
                # Restore original settings if failed
                self.model_name = original_model
                self.use_chat_completion = original_chat
                
            except Exception as e:
                logger.warning(f"Classic model {model} failed: {e}")
                continue
        
        # If we get here, no models worked
        raise ModelNotFoundError(f"No working models found. Original model '{self.model_name}' is not accessible.")
    
    def _handle_provider_error(self, error: Exception) -> None:
        """Map HuggingFace-specific errors to standard errors."""
        error_msg = str(error).lower()
        
        if 'rate limit' in error_msg or '429' in error_msg:
            raise RateLimitError(f"HuggingFace rate limit exceeded: {error}")
        elif 'unauthorized' in error_msg or '401' in error_msg or 'token' in error_msg:
            raise AuthenticationError(f"HuggingFace authentication failed: {error}")
        elif 'not found' in error_msg or '404' in error_msg:
            raise ModelNotFoundError(f"HuggingFace model not found: {error}")
        elif 'timeout' in error_msg:
            raise LLMError(f"HuggingFace request timed out: {error}")
        elif 'connection' in error_msg:
            raise LLMError(f"Failed to connect to HuggingFace API: {error}")
        else:
            raise LLMError(f"HuggingFace API error: {error}")