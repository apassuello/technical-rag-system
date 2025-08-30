"""
Comprehensive Test Suite for MistralAdapter.

This test suite targets the untested functionality identified in the coverage analysis,
focusing on areas not covered by existing Epic1 tests.

Coverage Target: Increase from 33.5% to 85%+ by testing:
- Error handling and retry mechanisms (100+ statements)
- Cost calculation and tracking (80+ statements)
- Request formatting and response processing (90+ statements)  
- Configuration validation and edge cases (60+ statements)
- Model-specific behaviors and limits (40+ statements)

Test Focus Areas:
- Unit tests for internal methods and error paths
- Cost calculation accuracy and tracking
- API request formatting and validation
- Retry logic and rate limiting behavior
- Configuration edge cases and validation
- Model limits and parameter handling
"""

import pytest
import json
import time
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock, call
from typing import Dict, Any, List
import tempfile
import os

# Import system under test
from src.components.generators.llm_adapters.mistral_adapter import MistralAdapter
from src.components.generators.llm_adapters.base_adapter import RateLimitError, AuthenticationError, ModelNotFoundError
from src.components.generators.base import GenerationParams, LLMError


class TestMistralAdapterComprehensive:
    """Comprehensive test suite for MistralAdapter covering untested functionality."""
    
    @pytest.fixture
    def mock_mistral_client(self):
        """Mock Mistral client for testing."""
        mock_client = Mock()
        mock_response = Mock()
        
        # Configure mock response structure
        mock_choice = Mock()
        mock_choice.message.content = "Test response content"
        mock_choice.finish_reason = "stop"
        
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 100
        mock_response.usage.total_tokens = 150
        
        mock_client.chat.complete.return_value = mock_response
        
        return mock_client, mock_response
    
    @pytest.fixture
    def valid_config(self):
        """Valid configuration for testing."""
        return {
            'api_key': 'test-api-key',
            'model_name': 'mistral-small',
            'max_tokens': 1000,
            'temperature': 0.7,
            'timeout': 30.0,
            'track_costs': True
        }
    
    @pytest.fixture
    def generation_params(self):
        """Standard generation parameters for testing."""
        return GenerationParams(
            max_tokens=500,
            temperature=0.8,
            top_p=0.9,
            frequency_penalty=0.1,
            presence_penalty=0.1
        )
    
    # ==================== INITIALIZATION TESTS ====================
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_initialization_success(self, mock_mistral_class, valid_config):
        """Test successful adapter initialization."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        adapter = MistralAdapter(**valid_config)
        
        # Verify initialization
        assert adapter.model_name == 'mistral-small'
        assert adapter.client == mock_client
        assert adapter.timeout == 30.0
        assert adapter.track_costs is True
        assert adapter._total_cost == Decimal('0.00')
        assert adapter._input_tokens == 0
        assert adapter._output_tokens == 0
        
        # Verify Mistral client initialization
        mock_mistral_class.assert_called_once_with(api_key='test-api-key')
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', False)
    def test_initialization_missing_mistral_package(self):
        """Test initialization failure when mistralai package is missing."""
        with pytest.raises(ImportError, match="Mistral AI package not installed"):
            MistralAdapter(api_key='test-key')
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', False)
    def test_initialization_missing_requests_package(self):
        """Test initialization failure when requests package is missing."""
        with pytest.raises(ImportError, match="Requests package not installed"):
            MistralAdapter(api_key='test-key')
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    def test_initialization_no_api_key(self):
        """Test initialization failure without API key."""
        with patch.dict(os.environ, {}, clear=True):  # Clear env vars
            with pytest.raises(AuthenticationError, match="Mistral API key is required"):
                MistralAdapter(model_name='mistral-small')
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_initialization_api_key_from_environment(self, mock_mistral_class):
        """Test API key loading from environment variable."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        with patch.dict(os.environ, {'MISTRAL_API_KEY': 'env-api-key'}):
            adapter = MistralAdapter(model_name='mistral-small')
            
            # Verify environment API key was used
            mock_mistral_class.assert_called_once_with(api_key='env-api-key')
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_initialization_unknown_model_pricing_warning(self, mock_mistral_class, caplog):
        """Test warning for unknown model pricing."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        adapter = MistralAdapter(model_name='unknown-model', api_key='test-key')
        
        # Check warning was logged
        assert "Pricing not available for model unknown-model" in caplog.text
        assert adapter.model_name == 'unknown-model'
    
    # ==================== COST CALCULATION TESTS ====================
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_calculate_cost_mistral_small(self, mock_mistral_class, valid_config):
        """Test cost calculation for mistral-small model."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        adapter = MistralAdapter(**valid_config)
        
        # Test cost calculation
        input_tokens = 1000  # 1K input tokens
        output_tokens = 500  # 0.5K output tokens
        
        cost = adapter._calculate_cost(input_tokens, output_tokens)
        
        # Expected cost: (1000/1000 * $0.0020) + (500/1000 * $0.0060) = $0.002 + $0.003 = $0.005
        expected_cost = Decimal('0.005')
        assert cost == expected_cost
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_calculate_cost_mistral_large(self, mock_mistral_class):
        """Test cost calculation for mistral-large model."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        adapter = MistralAdapter(model_name='mistral-large', api_key='test-key')
        
        # Test cost calculation
        input_tokens = 2000  # 2K input tokens
        output_tokens = 1000  # 1K output tokens
        
        cost = adapter._calculate_cost(input_tokens, output_tokens)
        
        # Expected cost: (2000/1000 * $0.008) + (1000/1000 * $0.024) = $0.016 + $0.024 = $0.040
        expected_cost = Decimal('0.040')
        assert cost == expected_cost
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_calculate_cost_unknown_model(self, mock_mistral_class):
        """Test cost calculation for unknown model."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        adapter = MistralAdapter(model_name='unknown-model', api_key='test-key')
        
        cost = adapter._calculate_cost(1000, 500)
        
        # Should return 0 for unknown models
        assert cost == Decimal('0.00')
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_track_usage_with_cost_tracking_enabled(self, mock_mistral_class, valid_config):
        """Test usage tracking when cost tracking is enabled."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        adapter = MistralAdapter(**valid_config)
        
        # Track usage
        input_tokens = 1000
        output_tokens = 500
        cost = Decimal('0.005')
        
        adapter._track_usage(input_tokens, output_tokens, cost)
        
        # Verify tracking
        assert adapter._input_tokens == 1000
        assert adapter._output_tokens == 500
        assert adapter._total_cost == Decimal('0.005')
        assert len(adapter.cost_history) == 1
        
        # Verify cost history entry
        history_entry = adapter.cost_history[0]
        assert history_entry['input_tokens'] == 1000
        assert history_entry['output_tokens'] == 500
        assert history_entry['cost'] == Decimal('0.005')
        assert 'timestamp' in history_entry
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_track_usage_accumulation(self, mock_mistral_class, valid_config):
        """Test usage tracking accumulation across multiple calls."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        adapter = MistralAdapter(**valid_config)
        
        # Track multiple usages
        adapter._track_usage(1000, 500, Decimal('0.005'))
        adapter._track_usage(2000, 1000, Decimal('0.010'))
        adapter._track_usage(500, 250, Decimal('0.0025'))
        
        # Verify accumulation
        assert adapter._input_tokens == 3500
        assert adapter._output_tokens == 1750
        assert adapter._total_cost == Decimal('0.0175')
        assert len(adapter.cost_history) == 3
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_get_cost_breakdown(self, mock_mistral_class, valid_config):
        """Test cost breakdown functionality."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        adapter = MistralAdapter(**valid_config)
        
        # Track some usage
        adapter._track_usage(1000, 500, Decimal('0.005'))
        adapter._track_usage(2000, 1000, Decimal('0.010'))
        
        breakdown = adapter.get_cost_breakdown()
        
        # Verify breakdown structure
        assert 'total_cost' in breakdown
        assert 'input_tokens' in breakdown
        assert 'output_tokens' in breakdown
        assert 'total_tokens' in breakdown
        assert 'average_cost_per_token' in breakdown
        assert 'cost_history' in breakdown
        
        # Verify calculations
        assert breakdown['total_cost'] == Decimal('0.015')
        assert breakdown['input_tokens'] == 3000
        assert breakdown['output_tokens'] == 1500
        assert breakdown['total_tokens'] == 4500
        assert breakdown['average_cost_per_token'] == Decimal('0.015') / 4500
        assert len(breakdown['cost_history']) == 2
    
    # ==================== REQUEST FORMATTING TESTS ====================
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_format_request_basic(self, mock_mistral_class, valid_config, generation_params):
        """Test basic request formatting."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        adapter = MistralAdapter(**valid_config)
        
        prompt = "What is machine learning?"
        formatted_request = adapter._format_request(prompt, generation_params)
        
        # Verify request structure
        assert 'model' in formatted_request
        assert 'messages' in formatted_request
        assert 'max_tokens' in formatted_request
        assert 'temperature' in formatted_request
        
        # Verify values
        assert formatted_request['model'] == 'mistral-small'
        assert len(formatted_request['messages']) == 1
        assert formatted_request['messages'][0]['role'] == 'user'
        assert formatted_request['messages'][0]['content'] == prompt
        assert formatted_request['max_tokens'] == 500
        assert formatted_request['temperature'] == 0.8
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_format_request_with_context(self, mock_mistral_class, valid_config, generation_params):
        """Test request formatting with context."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        adapter = MistralAdapter(**valid_config)
        
        prompt = "What is machine learning?"
        context = "Machine learning is a branch of artificial intelligence."
        
        formatted_request = adapter._format_request(prompt, generation_params, context=context)
        
        # Verify context integration
        assert len(formatted_request['messages']) == 2
        assert formatted_request['messages'][0]['role'] == 'system'
        assert formatted_request['messages'][0]['content'] == context
        assert formatted_request['messages'][1]['role'] == 'user'
        assert formatted_request['messages'][1]['content'] == prompt
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_format_request_parameter_mapping(self, mock_mistral_class, valid_config):
        """Test parameter mapping in request formatting."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        adapter = MistralAdapter(**valid_config)
        
        # Test with all parameters
        params = GenerationParams(
            max_tokens=1000,
            temperature=0.5,
            top_p=0.95,
            frequency_penalty=0.2,
            presence_penalty=0.3,
            stop_sequences=["END", "STOP"]
        )
        
        formatted_request = adapter._format_request("test prompt", params)
        
        # Verify parameter mapping
        assert formatted_request['max_tokens'] == 1000
        assert formatted_request['temperature'] == 0.5
        assert formatted_request['top_p'] == 0.95
        
        # Note: Mistral may not support all OpenAI parameters
        # The adapter should handle this gracefully
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_format_request_model_limits(self, mock_mistral_class, valid_config):
        """Test request formatting respects model limits."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        adapter = MistralAdapter(**valid_config)
        
        # Test with tokens exceeding model limit
        params = GenerationParams(max_tokens=50000)  # Exceeds 32K limit
        
        formatted_request = adapter._format_request("test prompt", params)
        
        # Should respect model limit
        model_limit = adapter.MODEL_LIMITS.get('mistral-small', 32000)
        assert formatted_request['max_tokens'] <= model_limit
    
    # ==================== ERROR HANDLING TESTS ====================
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_error_mapping_rate_limit(self, mock_mistral_class, valid_config):
        """Test error mapping for rate limits."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        adapter = MistralAdapter(**valid_config)
        
        # Simulate rate limit error
        rate_limit_error = Exception("Rate limit exceeded")
        rate_limit_error.status_code = 429
        
        mapped_error = adapter._map_error(rate_limit_error)
        
        assert isinstance(mapped_error, RateLimitError)
        assert "Rate limit exceeded" in str(mapped_error)
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_error_mapping_authentication(self, mock_mistral_class, valid_config):
        """Test error mapping for authentication errors."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        adapter = MistralAdapter(**valid_config)
        
        # Simulate authentication error
        auth_error = Exception("Invalid API key")
        auth_error.status_code = 401
        
        mapped_error = adapter._map_error(auth_error)
        
        assert isinstance(mapped_error, AuthenticationError)
        assert "Invalid API key" in str(mapped_error)
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_error_mapping_model_not_found(self, mock_mistral_class, valid_config):
        """Test error mapping for model not found errors."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        adapter = MistralAdapter(**valid_config)
        
        # Simulate model not found error
        model_error = Exception("Model not found")
        model_error.status_code = 404
        
        mapped_error = adapter._map_error(model_error)
        
        assert isinstance(mapped_error, ModelNotFoundError)
        assert "Model not found" in str(mapped_error)
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_error_mapping_generic(self, mock_mistral_class, valid_config):
        """Test error mapping for generic errors."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        adapter = MistralAdapter(**valid_config)
        
        # Simulate generic error
        generic_error = Exception("Something went wrong")
        generic_error.status_code = 500
        
        mapped_error = adapter._map_error(generic_error)
        
        assert isinstance(mapped_error, LLMError)
        assert "Something went wrong" in str(mapped_error)
    
    # ==================== RETRY LOGIC TESTS ====================
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_retry_on_rate_limit(self, mock_sleep, mock_mistral_class, valid_config, generation_params):
        """Test retry logic for rate limit errors."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        adapter = MistralAdapter(**valid_config)
        
        # Configure mock to fail twice then succeed
        rate_limit_error = RateLimitError("Rate limit exceeded")
        mock_success_response = Mock()
        mock_success_response.choices = [Mock()]
        mock_success_response.choices[0].message.content = "Success response"
        mock_success_response.choices[0].finish_reason = "stop"
        mock_success_response.usage.prompt_tokens = 10
        mock_success_response.usage.completion_tokens = 20
        
        adapter.client.chat.complete.side_effect = [
            rate_limit_error,
            rate_limit_error,
            mock_success_response
        ]
        
        # Should succeed after retries
        result = adapter._make_request("test prompt", generation_params)
        
        # Verify retries occurred
        assert adapter.client.chat.complete.call_count == 3
        assert result == mock_success_response
        
        # Verify sleep was called (exponential backoff)
        assert mock_sleep.call_count >= 2
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_retry_exhaustion(self, mock_mistral_class, valid_config, generation_params):
        """Test retry exhaustion behavior."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        adapter = MistralAdapter(**valid_config)
        
        # Configure mock to always fail
        rate_limit_error = RateLimitError("Rate limit exceeded")
        adapter.client.chat.complete.side_effect = rate_limit_error
        
        # Should raise error after exhausting retries
        with pytest.raises(RateLimitError):
            adapter._make_request("test prompt", generation_params)
        
        # Verify maximum retries were attempted
        assert adapter.client.chat.complete.call_count == 5  # stop_after_attempt(5)
    
    # ==================== RESPONSE PROCESSING TESTS ====================
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_process_response_success(self, mock_mistral_class, valid_config):
        """Test successful response processing."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        adapter = MistralAdapter(**valid_config)
        
        # Create mock response
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "Test response content"
        mock_choice.finish_reason = "stop"
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 200
        mock_response.usage.total_tokens = 300
        
        result = adapter._process_response(mock_response)
        
        # Verify response processing
        assert result['text'] == "Test response content"
        assert result['finish_reason'] == "stop"
        assert result['usage']['prompt_tokens'] == 100
        assert result['usage']['completion_tokens'] == 200
        assert result['usage']['total_tokens'] == 300
        assert 'cost' in result
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_process_response_multiple_choices(self, mock_mistral_class, valid_config):
        """Test response processing with multiple choices."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        adapter = MistralAdapter(**valid_config)
        
        # Create mock response with multiple choices
        mock_response = Mock()
        mock_choice1 = Mock()
        mock_choice1.message.content = "First choice"
        mock_choice1.finish_reason = "stop"
        mock_choice2 = Mock()
        mock_choice2.message.content = "Second choice"
        mock_choice2.finish_reason = "stop"
        
        mock_response.choices = [mock_choice1, mock_choice2]
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 200
        
        result = adapter._process_response(mock_response)
        
        # Should return first choice by default
        assert result['text'] == "First choice"
        assert result['finish_reason'] == "stop"
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_process_response_empty_choices(self, mock_mistral_class, valid_config):
        """Test response processing with empty choices."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        adapter = MistralAdapter(**valid_config)
        
        # Create mock response with no choices
        mock_response = Mock()
        mock_response.choices = []
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 0
        
        with pytest.raises(LLMError, match="No response generated"):
            adapter._process_response(mock_response)
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_process_response_missing_usage(self, mock_mistral_class, valid_config):
        """Test response processing with missing usage information."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        adapter = MistralAdapter(**valid_config)
        
        # Create mock response without usage info
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "Test response"
        mock_choice.finish_reason = "stop"
        mock_response.choices = [mock_choice]
        mock_response.usage = None
        
        result = adapter._process_response(mock_response)
        
        # Should handle missing usage gracefully
        assert result['text'] == "Test response"
        assert result['usage']['prompt_tokens'] == 0
        assert result['usage']['completion_tokens'] == 0
        assert result['usage']['total_tokens'] == 0
        assert result['cost'] == Decimal('0.00')
    
    # ==================== INTEGRATION TESTS ====================
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_generate_end_to_end(self, mock_mistral_class, valid_config, generation_params):
        """Test end-to-end generation process."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        # Configure successful response
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "Generated response"
        mock_choice.finish_reason = "stop"
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 100
        
        mock_client.chat.complete.return_value = mock_response
        
        adapter = MistralAdapter(**valid_config)
        
        result = adapter.generate("What is AI?", generation_params)
        
        # Verify end-to-end flow
        assert result['text'] == "Generated response"
        assert result['finish_reason'] == "stop"
        
        # Verify cost tracking
        assert adapter._input_tokens == 50
        assert adapter._output_tokens == 100
        assert adapter._total_cost > Decimal('0.00')
        
        # Verify API call
        mock_client.chat.complete.assert_called_once()
        call_args = mock_client.chat.complete.call_args[1]
        assert call_args['model'] == 'mistral-small'
        assert len(call_args['messages']) == 1
        assert call_args['messages'][0]['content'] == "What is AI?"
    
    # ==================== PERFORMANCE AND EDGE CASE TESTS ====================
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_very_long_prompt_handling(self, mock_mistral_class, valid_config, generation_params):
        """Test handling of very long prompts."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        adapter = MistralAdapter(**valid_config)
        
        # Create very long prompt (simulate token limit exceeded)
        very_long_prompt = "This is a test. " * 10000  # Very long prompt
        
        formatted_request = adapter._format_request(very_long_prompt, generation_params)
        
        # Should handle gracefully and truncate if necessary
        assert 'messages' in formatted_request
        assert len(formatted_request['messages']) == 1
        assert formatted_request['model'] == 'mistral-small'
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_empty_prompt_handling(self, mock_mistral_class, valid_config, generation_params):
        """Test handling of empty prompts."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        adapter = MistralAdapter(**valid_config)
        
        # Test empty prompt
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            adapter.generate("", generation_params)
        
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            adapter.generate("   ", generation_params)
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_timeout_handling(self, mock_mistral_class, valid_config, generation_params):
        """Test timeout handling."""
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        # Configure timeout error
        import socket
        timeout_error = socket.timeout("Request timed out")
        mock_client.chat.complete.side_effect = timeout_error
        
        adapter = MistralAdapter(**valid_config)
        
        with pytest.raises(LLMError, match="timeout"):
            adapter.generate("Test prompt", generation_params)
    
    @patch('src.components.generators.llm_adapters.mistral_adapter.MISTRAL_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.REQUESTS_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.mistral_adapter.Mistral')
    def test_concurrent_request_handling(self, mock_mistral_class, valid_config, generation_params):
        """Test concurrent request handling (thread safety)."""
        import threading
        
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        # Configure successful response
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "Concurrent response"
        mock_choice.finish_reason = "stop"
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        
        mock_client.chat.complete.return_value = mock_response
        
        adapter = MistralAdapter(**valid_config)
        
        results = []
        errors = []
        
        def make_request():
            try:
                result = adapter.generate("Concurrent test", generation_params)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple concurrent threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded
        assert len(errors) == 0
        assert len(results) == 5
        
        # Verify cost tracking is thread-safe
        assert adapter._input_tokens == 50  # 5 * 10
        assert adapter._output_tokens == 100  # 5 * 20