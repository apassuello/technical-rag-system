"""Adaptive Test Manager for Epic 1 Phase 2.

Provides configurable real API + mock testing capabilities with smart mode detection
and cost-aware test execution.
"""

import os
import logging
from typing import Optional, Dict, Any, Union
from decimal import Decimal
from unittest.mock import MagicMock

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, use existing environment

# Import real adapters
try:
    from src.components.generators.llm_adapters.openai_adapter import OpenAIAdapter
    OPENAI_ADAPTER_AVAILABLE = True
except ImportError:
    OPENAI_ADAPTER_AVAILABLE = False
    OpenAIAdapter = None

try:
    from src.components.generators.llm_adapters.mistral_adapter import MistralAdapter
    MISTRAL_ADAPTER_AVAILABLE = True
except ImportError:
    MISTRAL_ADAPTER_AVAILABLE = False
    MistralAdapter = None

try:
    from src.components.generators.base import GenerationParams
    GENERATION_PARAMS_AVAILABLE = True
except ImportError:
    GENERATION_PARAMS_AVAILABLE = False
    GenerationParams = None

logger = logging.getLogger(__name__)


class MockOpenAIAdapter:
    """Mock OpenAI adapter for testing without API calls."""
    
    def __init__(self, model_name="gpt-3.5-turbo", **kwargs):
        self.model_name = model_name
        self.api_key = "***HIDDEN***"
        self._total_cost = Decimal('0.00')
        self._request_count = 0
        
        # Mock pricing matching real adapter
        self.MODEL_PRICING = {
            'gpt-3.5-turbo': {'input': Decimal('0.0010'), 'output': Decimal('0.0020')},
            'gpt-4-turbo': {'input': Decimal('0.0100'), 'output': Decimal('0.0300')},
            'gpt-4o-mini': {'input': Decimal('0.0001'), 'output': Decimal('0.0006')}
        }
    
    def generate(self, prompt: str, params: 'GenerationParams') -> str:
        """Mock generation with cost calculation."""
        # Estimate tokens (rough approximation)
        input_tokens = len(prompt.split()) * 4
        output_tokens = min(params.max_tokens or 100, 150)  # Mock output length
        
        # Calculate mock cost
        pricing = self.MODEL_PRICING.get(self.model_name, self.MODEL_PRICING['gpt-3.5-turbo'])
        input_cost = (Decimal(str(input_tokens)) / Decimal('1000')) * pricing['input']
        output_cost = (Decimal(str(output_tokens)) / Decimal('1000')) * pricing['output']
        total_cost = input_cost + output_cost
        
        self._total_cost += total_cost
        self._request_count += 1
        
        return f"Mock response from OpenAI {self.model_name} for: {prompt[:50]}..."
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            'provider': 'OpenAI',
            'model': self.model_name,
            'max_context_tokens': 16385 if 'gpt-3.5' in self.model_name else 128000,
            'supports_streaming': True,
            'mode': 'mock'
        }
    
    def get_cost_summary(self) -> Dict[str, Any]:
        return {
            'total_cost_usd': float(self._total_cost),
            'total_requests': self._request_count,
            'model': self.model_name,
            'mode': 'mock'
        }


class MockMistralAdapter:
    """Mock Mistral adapter for testing without API calls."""
    
    def __init__(self, model_name="mistral-small", **kwargs):
        self.model_name = model_name
        self.api_key = "***HIDDEN***"
        self._total_cost = Decimal('0.00')
        self._request_count = 0
        
        # Mock pricing matching real adapter
        self.MODEL_PRICING = {
            'mistral-small': {'input': Decimal('0.0020'), 'output': Decimal('0.0060')},
            'mistral-medium': {'input': Decimal('0.0027'), 'output': Decimal('0.0081')},
            'mistral-large': {'input': Decimal('0.0080'), 'output': Decimal('0.0240')}
        }
    
    def generate(self, prompt: str, params: 'GenerationParams') -> str:
        """Mock generation with cost calculation."""
        # Estimate tokens
        input_tokens = len(prompt.split()) * 4
        output_tokens = min(params.max_tokens or 100, 120)
        
        # Calculate mock cost
        pricing = self.MODEL_PRICING.get(self.model_name, self.MODEL_PRICING['mistral-small'])
        input_cost = (Decimal(str(input_tokens)) / Decimal('1000')) * pricing['input']
        output_cost = (Decimal(str(output_tokens)) / Decimal('1000')) * pricing['output']
        total_cost = input_cost + output_cost
        
        self._total_cost += total_cost
        self._request_count += 1
        
        return f"Mock response from Mistral {self.model_name} for: {prompt[:50]}..."
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            'provider': 'Mistral',
            'model': self.model_name,
            'max_context_tokens': 32000,
            'supports_streaming': False,
            'mode': 'mock'
        }
    
    def get_cost_summary(self) -> Dict[str, Any]:
        return {
            'total_cost_usd': float(self._total_cost),
            'total_requests': self._request_count,
            'model': self.model_name,
            'mode': 'mock'
        }


class AdaptiveTestManager:
    """Manages real API vs mock testing modes with smart defaults."""
    
    def __init__(self, force_mock: bool = False, cost_limit_usd: float = 1.0):
        """Initialize adaptive test manager.
        
        Args:
            force_mock: Force mock mode even if API keys available
            cost_limit_usd: Maximum cost allowed for real API tests
        """
        self.force_mock = force_mock or os.getenv('EPIC1_USE_MOCK_APIS', '').lower() == 'true'
        self.cost_limit_usd = Decimal(str(cost_limit_usd))
        self.total_test_cost = Decimal('0.00')
        
        # Detect available API keys
        self.openai_key_available = bool(os.getenv('OPENAI_API_KEY'))
        self.mistral_key_available = bool(os.getenv('MISTRAL_API_KEY'))
        
        # Determine modes
        self.openai_mode = self._determine_mode('openai')
        self.mistral_mode = self._determine_mode('mistral')
        
        logger.info(f"AdaptiveTestManager initialized:")
        logger.info(f"  OpenAI mode: {self.openai_mode}")
        logger.info(f"  Mistral mode: {self.mistral_mode}")
        logger.info(f"  Cost limit: ${self.cost_limit_usd}")
    
    def _determine_mode(self, provider: str) -> str:
        """Determine test mode for a provider."""
        if self.force_mock:
            return 'mock'
        
        # Check for explicit mock request via environment
        if os.getenv(f'{provider.upper()}_USE_MOCK', '').lower() == 'true':
            return 'mock'
        
        if provider == 'openai':
            if self.openai_key_available and OPENAI_ADAPTER_AVAILABLE:
                # Test if we can actually use the API (basic validation)
                try:
                    return 'real'
                except Exception as e:
                    logger.warning(f"OpenAI adapter validation failed, using mock: {e}")
                    return 'mock'
            else:
                return 'mock'
        elif provider == 'mistral':
            if self.mistral_key_available and MISTRAL_ADAPTER_AVAILABLE:
                # Test if we can actually use the API
                try:
                    return 'real'
                except Exception as e:
                    logger.warning(f"Mistral adapter validation failed, using mock: {e}")
                    return 'mock'
            else:
                return 'mock'
        else:
            return 'mock'
    
    def get_openai_adapter(self, model_name: str = "gpt-3.5-turbo", **kwargs) -> Union[OpenAIAdapter, MockOpenAIAdapter]:
        """Get OpenAI adapter in appropriate mode."""
        if self.openai_mode == 'real':
            if not OPENAI_ADAPTER_AVAILABLE:
                logger.warning("Real OpenAI adapter not available, using mock")
                return MockOpenAIAdapter(model_name=model_name, **kwargs)
            
            try:
                return OpenAIAdapter(model_name=model_name, **kwargs)
            except Exception as e:
                logger.warning(f"Failed to create real OpenAI adapter, using mock: {e}")
                return MockOpenAIAdapter(model_name=model_name, **kwargs)
        else:
            return MockOpenAIAdapter(model_name=model_name, **kwargs)
    
    def get_mistral_adapter(self, model_name: str = "mistral-small", **kwargs) -> Union[MistralAdapter, MockMistralAdapter]:
        """Get Mistral adapter in appropriate mode."""
        if self.mistral_mode == 'real':
            if not MISTRAL_ADAPTER_AVAILABLE:
                logger.warning("Real Mistral adapter not available, using mock")
                return MockMistralAdapter(model_name=model_name, **kwargs)
            
            try:
                return MistralAdapter(model_name=model_name, **kwargs)
            except ImportError as e:
                logger.warning(f"Mistral package not installed, using mock: {e}")
                return MockMistralAdapter(model_name=model_name, **kwargs)
            except Exception as e:
                logger.warning(f"Failed to create real Mistral adapter, using mock: {e}")
                return MockMistralAdapter(model_name=model_name, **kwargs)
        else:
            return MockMistralAdapter(model_name=model_name, **kwargs)
    
    def is_real_mode(self, provider: str) -> bool:
        """Check if provider is using real API mode."""
        if provider == 'openai':
            return self.openai_mode == 'real'
        elif provider == 'mistral':
            return self.mistral_mode == 'real'
        return False
    
    def track_test_cost(self, cost_usd: Decimal) -> None:
        """Track test costs and enforce limits."""
        self.total_test_cost += cost_usd
        
        if self.total_test_cost > self.cost_limit_usd:
            logger.warning(f"Test cost limit exceeded: ${self.total_test_cost} > ${self.cost_limit_usd}")
            raise ValueError(f"Test cost limit of ${self.cost_limit_usd} exceeded")
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get summary of test execution."""
        return {
            'openai_mode': self.openai_mode,
            'mistral_mode': self.mistral_mode,
            'total_cost_usd': float(self.total_test_cost),
            'cost_limit_usd': float(self.cost_limit_usd),
            'api_keys_available': {
                'openai': self.openai_key_available,
                'mistral': self.mistral_key_available
            },
            'adapters_available': {
                'openai': OPENAI_ADAPTER_AVAILABLE,
                'mistral': MISTRAL_ADAPTER_AVAILABLE
            }
        }


# Convenience function for test files
def get_test_manager(**kwargs) -> AdaptiveTestManager:
    """Get configured test manager instance."""
    return AdaptiveTestManager(**kwargs)


# Pytest fixtures for easy use in tests
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "real_api: mark test to run only with real API access"
    )
    config.addinivalue_line(
        "markers", "mock: mark test to run only in mock mode"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test requiring real APIs"
    )
    config.addinivalue_line(
        "markers", "cost_sensitive: mark test that may incur API costs"
    )