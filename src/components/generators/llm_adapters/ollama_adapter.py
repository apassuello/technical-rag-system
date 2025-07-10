"""
Ollama LLM adapter implementation.

This adapter provides integration with local Ollama models, handling
the specific API format and response structure of Ollama.

Architecture Notes:
- Converts between unified interface and Ollama API format
- Handles Ollama-specific parameters and responses
- Supports both regular and streaming generation
- Maps Ollama errors to standard LLMError types
"""

import json
import requests
import logging
from typing import Dict, Any, Optional, Iterator
from urllib.parse import urljoin

from .base_adapter import BaseLLMAdapter, LLMError, ModelNotFoundError
from ..base import GenerationParams

logger = logging.getLogger(__name__)


class OllamaAdapter(BaseLLMAdapter):
    """
    Adapter for Ollama local LLM integration.
    
    Features:
    - Support for all Ollama models
    - Streaming response support
    - Automatic model pulling if not available
    - Context window management
    - Format conversion for Ollama API
    
    Configuration:
    - base_url: Ollama server URL (default: http://localhost:11434)
    - timeout: Request timeout in seconds (default: 120)
    - auto_pull: Automatically pull models if not found (default: False)
    """
    
    def __init__(self,
                 model_name: str = "llama3.2",
                 base_url: str = "http://localhost:11434",
                 timeout: int = 120,
                 auto_pull: bool = False,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize Ollama adapter.
        
        Args:
            model_name: Ollama model name (e.g., "llama3.2", "mistral")
            base_url: Ollama server URL
            timeout: Request timeout in seconds
            auto_pull: Automatically pull models if not found
            config: Additional configuration
        """
        # Merge config
        adapter_config = {
            'base_url': base_url,
            'timeout': timeout,
            'auto_pull': auto_pull,
            **(config or {})
        }
        
        super().__init__(model_name, adapter_config)
        
        self.base_url = adapter_config['base_url'].rstrip('/')
        self.timeout = adapter_config['timeout']
        self.auto_pull = adapter_config['auto_pull']
        
        # API endpoints
        self.generate_url = urljoin(self.base_url + '/', 'api/generate')
        self.chat_url = urljoin(self.base_url + '/', 'api/chat')
        self.tags_url = urljoin(self.base_url + '/', 'api/tags')
        self.pull_url = urljoin(self.base_url + '/', 'api/pull')
        
        logger.info(f"Initialized Ollama adapter for model '{model_name}' at {base_url}")
    
    def _make_request(self, prompt: str, params: GenerationParams) -> Dict[str, Any]:
        """
        Make a request to Ollama API.
        
        Args:
            prompt: The prompt to send
            params: Generation parameters
            
        Returns:
            Ollama API response
            
        Raises:
            Various request exceptions
        """
        # Convert to Ollama format
        ollama_params = self._convert_params(params)
        
        # Prepare request payload
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": ollama_params
        }
        
        try:
            # Make request
            response = requests.post(
                self.generate_url,
                json=payload,
                timeout=self.timeout
            )
            
            # Check for errors
            if response.status_code == 404:
                # Model not found
                if self.auto_pull:
                    logger.info(f"Model '{self.model_name}' not found, attempting to pull...")
                    self._pull_model()
                    # Retry request
                    response = requests.post(
                        self.generate_url,
                        json=payload,
                        timeout=self.timeout
                    )
                else:
                    raise ModelNotFoundError(f"Model '{self.model_name}' not found. Set auto_pull=True to download it.")
            
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.Timeout:
            raise LLMError(f"Ollama request timed out after {self.timeout}s")
        except requests.exceptions.ConnectionError:
            raise LLMError(f"Failed to connect to Ollama at {self.base_url}. Is Ollama running?")
        except requests.exceptions.HTTPError as e:
            self._handle_http_error(e)
        except Exception as e:
            self._handle_provider_error(e)
    
    def _parse_response(self, response: Dict[str, Any]) -> str:
        """
        Parse Ollama response to extract generated text.
        
        Args:
            response: Ollama API response
            
        Returns:
            Generated text
        """
        # Ollama returns response in 'response' field
        text = response.get('response', '')
        
        # Log token usage if available
        if 'eval_count' in response:
            logger.debug(f"Ollama used {response['eval_count']} tokens for generation")
        
        return text
    
    def generate_streaming(self, prompt: str, params: GenerationParams) -> Iterator[str]:
        """
        Generate a streaming response from Ollama.
        
        Args:
            prompt: The prompt to send
            params: Generation parameters
            
        Yields:
            Generated text chunks
        """
        # Convert parameters
        ollama_params = self._convert_params(params)
        
        # Prepare streaming request
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": True,
            "options": ollama_params
        }
        
        try:
            # Make streaming request
            response = requests.post(
                self.generate_url,
                json=payload,
                stream=True,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            # Process streaming response
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if 'response' in chunk:
                            yield chunk['response']
                        
                        # Check if generation is done
                        if chunk.get('done', False):
                            break
                            
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse streaming chunk: {line}")
                        continue
                        
        except Exception as e:
            self._handle_provider_error(e)
    
    def _get_provider_name(self) -> str:
        """Return the provider name."""
        return "Ollama"
    
    def _validate_model(self) -> bool:
        """Check if the model exists in Ollama."""
        try:
            response = requests.get(self.tags_url, timeout=10)
            response.raise_for_status()
            
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            
            # Check exact match or partial match (e.g., "llama3.2" matches "llama3.2:latest")
            for name in model_names:
                if self.model_name in name or name in self.model_name:
                    return True
                    
            return False
            
        except Exception as e:
            logger.warning(f"Failed to validate model: {str(e)}")
            # Assume model exists if we can't check
            return True
    
    def _supports_streaming(self) -> bool:
        """Ollama supports streaming."""
        return True
    
    def _get_max_tokens(self) -> Optional[int]:
        """Get max tokens for current model."""
        # Model-specific limits
        model_limits = {
            'llama3.2': 4096,
            'llama3.1': 128000,
            'llama3': 8192,
            'llama2': 4096,
            'mistral': 8192,
            'mixtral': 32768,
            'gemma': 8192,
            'gemma2': 8192,
            'phi3': 4096,
            'qwen2.5': 32768,
        }
        
        # Check for exact match or prefix
        for model, limit in model_limits.items():
            if model in self.model_name.lower():
                return limit
                
        # Default for unknown models
        return 4096
    
    def _convert_params(self, params: GenerationParams) -> Dict[str, Any]:
        """
        Convert unified parameters to Ollama format.
        
        Args:
            params: Unified generation parameters
            
        Returns:
            Ollama-specific parameters
        """
        ollama_params = {}
        
        # Map common parameters
        if params.temperature is not None:
            ollama_params['temperature'] = params.temperature
        if params.max_tokens is not None:
            ollama_params['num_predict'] = params.max_tokens
        if params.top_p is not None:
            ollama_params['top_p'] = params.top_p
        if params.frequency_penalty is not None:
            ollama_params['repeat_penalty'] = 1.0 + params.frequency_penalty
        if params.stop_sequences:
            ollama_params['stop'] = params.stop_sequences
            
        # Add Ollama-specific defaults
        ollama_params.setdefault('seed', -1)  # Random seed
        ollama_params.setdefault('num_ctx', 2048)  # Context window
        
        return ollama_params
    
    def _pull_model(self) -> None:
        """Pull a model from Ollama registry."""
        logger.info(f"Pulling model '{self.model_name}'...")
        
        payload = {"name": self.model_name, "stream": False}
        
        try:
            response = requests.post(
                self.pull_url,
                json=payload,
                timeout=600  # 10 minutes for model download
            )
            response.raise_for_status()
            
            logger.info(f"Successfully pulled model '{self.model_name}'")
            
        except Exception as e:
            raise LLMError(f"Failed to pull model '{self.model_name}': {str(e)}")
    
    def _handle_http_error(self, error: requests.exceptions.HTTPError) -> None:
        """Handle HTTP errors from Ollama."""
        if error.response.status_code == 404:
            raise ModelNotFoundError(f"Model '{self.model_name}' not found")
        elif error.response.status_code == 400:
            raise LLMError(f"Bad request to Ollama: {error.response.text}")
        elif error.response.status_code == 500:
            raise LLMError(f"Ollama server error: {error.response.text}")
        else:
            raise LLMError(f"HTTP error {error.response.status_code}: {error.response.text}")
    
    def _handle_provider_error(self, error: Exception) -> None:
        """Map Ollama-specific errors to standard errors."""
        error_msg = str(error).lower()
        
        if 'connection' in error_msg:
            raise LLMError(f"Cannot connect to Ollama at {self.base_url}. Is Ollama running?")
        elif 'timeout' in error_msg:
            raise LLMError(f"Request to Ollama timed out")
        elif 'model' in error_msg and 'not found' in error_msg:
            raise ModelNotFoundError(f"Model '{self.model_name}' not found")
        else:
            super()._handle_provider_error(error)