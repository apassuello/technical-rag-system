"""
Comprehensive Test Suite for OpenAIAdapter.

This test suite targets the untested functionality identified in the coverage analysis,
focusing on areas not covered by existing Epic1 tests.

Coverage Target: Increase from 31.4% to 85%+ by testing:
- Token counting and precise cost calculation (100+ statements)
- Streaming response handling (80+ statements)
- Request formatting and parameter mapping (90+ statements)
- Error handling and retry mechanisms (70+ statements)
- Model-specific optimizations and limits (50+ statements)

Test Focus Areas:
- Unit tests for tiktoken integration and token counting
- Streaming response processing and chunking
- Request formatting with OpenAI-specific parameters
- Cost calculation accuracy across different models
- Error mapping and retry behavior
- Model limits and parameter validation
"""

import pytest
import json
import time
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock, call
from typing import Dict, Any, List, Iterator
import tempfile
import os

# Import system under test
from src.components.generators.llm_adapters.openai_adapter import OpenAIAdapter
from src.components.generators.llm_adapters.base_adapter import RateLimitError, AuthenticationError, ModelNotFoundError
from src.components.generators.base import GenerationParams, LLMError


class TestOpenAIAdapterComprehensive:
    """Comprehensive test suite for OpenAIAdapter covering untested functionality."""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client for testing."""
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
        mock_response.model = "gpt-3.5-turbo"
        
        mock_client.chat.completions.create.return_value = mock_response
        
        return mock_client, mock_response
    
    @pytest.fixture
    def mock_tiktoken(self):
        """Mock tiktoken for token counting."""
        mock_encoding = Mock()
        mock_encoding.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
        
        with patch('src.components.generators.llm_adapters.openai_adapter.tiktoken') as mock_tiktoken_module:
            mock_tiktoken_module.encoding_for_model.return_value = mock_encoding
            yield mock_tiktoken_module, mock_encoding
    
    @pytest.fixture
    def valid_config(self):
        """Valid configuration for testing."""
        return {
            'api_key': 'sk-test-api-key',
            'model_name': 'gpt-3.5-turbo',
            'timeout': 30.0,
            'organization': 'org-test',
            'config': {
                'max_tokens': 1000,
                'temperature': 0.7
            }
        }
    
    @pytest.fixture
    def generation_params(self):
        """Standard generation parameters for testing."""
        return GenerationParams(
            max_tokens=500,
            temperature=0.8,
            top_p=0.9,
            frequency_penalty=0.1,
            presence_penalty=0.1,
            stop_sequences=["END", "STOP"]
        )
    
    # ==================== INITIALIZATION TESTS ====================
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_initialization_success(self, mock_openai_class, valid_config):
        """Test successful adapter initialization."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(**valid_config)
        
        # Verify initialization
        assert adapter.model_name == 'gpt-3.5-turbo'
        assert adapter.client == mock_client
        assert adapter.timeout == 30.0
        assert adapter._total_cost == Decimal('0.00')
        assert adapter._input_tokens == 0
        assert adapter._output_tokens == 0
        
        # Verify OpenAI client initialization
        mock_openai_class.assert_called_once_with(
            api_key='sk-test-api-key',
            organization='org-test',
            timeout=30.0
        )
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', False)
    def test_initialization_missing_openai_package(self):
        """Test initialization failure when openai package is missing."""
        with pytest.raises(ImportError, match="OpenAI package not installed"):
            OpenAIAdapter(api_key='sk-test-key')
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_initialization_no_api_key(self, mock_openai_class):
        """Test initialization failure without API key."""
        with patch.dict(os.environ, {}, clear=True):  # Clear env vars
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                OpenAIAdapter(model_name='gpt-3.5-turbo')
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_initialization_api_key_from_environment(self, mock_openai_class):
        """Test API key loading from environment variable."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-env-api-key'}):
            adapter = OpenAIAdapter(model_name='gpt-3.5-turbo')
            
            # Verify environment API key was used
            mock_openai_class.assert_called_once_with(
                api_key='sk-env-api-key',
                organization=None,
                timeout=120.0
            )
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_initialization_custom_base_url(self, mock_openai_class, valid_config):
        """Test initialization with custom base URL."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        valid_config['base_url'] = 'https://custom-openai-endpoint.com/v1'
        adapter = OpenAIAdapter(**valid_config)
        
        # Verify custom base URL was used
        mock_openai_class.assert_called_once_with(
            api_key='sk-test-api-key',
            base_url='https://custom-openai-endpoint.com/v1',
            organization='org-test',
            timeout=30.0
        )
    
    # ==================== TOKEN COUNTING TESTS ====================
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_count_tokens_with_tiktoken(self, mock_openai_class, valid_config, mock_tiktoken):
        """Test token counting using tiktoken."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_tiktoken_module, mock_encoding = mock_tiktoken
        
        adapter = OpenAIAdapter(**valid_config)
        
        text = "This is a test message for token counting"
        token_count = adapter._count_tokens(text)
        
        # Verify tiktoken was used
        mock_tiktoken_module.encoding_for_model.assert_called_once_with('gpt-3.5-turbo')
        mock_encoding.encode.assert_called_once_with(text)
        
        # Verify token count
        assert token_count == 5  # Mock returns [1, 2, 3, 4, 5]
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_count_tokens_fallback_estimation(self, mock_openai_class, valid_config):
        """Test token counting fallback when tiktoken is unavailable."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock tiktoken to not be available
        with patch('src.components.generators.llm_adapters.openai_adapter.tiktoken', None):
            adapter = OpenAIAdapter(**valid_config)
            
            text = "This is a test message"  # 5 words
            token_count = adapter._count_tokens(text)
            
            # Should use word-based estimation (roughly words * 1.3)
            expected_tokens = int(len(text.split()) * 1.3)
            assert token_count == expected_tokens
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_count_tokens_unknown_model(self, mock_openai_class, mock_tiktoken):
        """Test token counting with unknown model falls back to estimation."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_tiktoken_module, mock_encoding = mock_tiktoken
        
        # Mock tiktoken to raise error for unknown model
        mock_tiktoken_module.encoding_for_model.side_effect = KeyError("Unknown model")
        
        adapter = OpenAIAdapter(model_name='unknown-model', api_key='sk-test-key')
        
        text = "This is a test message"
        token_count = adapter._count_tokens(text)
        
        # Should fall back to word-based estimation
        expected_tokens = int(len(text.split()) * 1.3)
        assert token_count == expected_tokens
    
    # ==================== COST CALCULATION TESTS ====================
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_calculate_cost_gpt_3_5_turbo(self, mock_openai_class, valid_config):
        """Test cost calculation for gpt-3.5-turbo model."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(**valid_config)
        
        # Test cost calculation
        input_tokens = 1000  # 1K input tokens
        output_tokens = 500  # 0.5K output tokens
        
        cost = adapter._calculate_cost(input_tokens, output_tokens)
        
        # Expected cost: (1000/1000 * $0.0010) + (500/1000 * $0.0020) = $0.001 + $0.001 = $0.002
        expected_cost = Decimal('0.002')
        assert cost == expected_cost
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_calculate_cost_gpt_4_turbo(self, mock_openai_class):
        """Test cost calculation for gpt-4-turbo model."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(model_name='gpt-4-turbo', api_key='sk-test-key')
        
        # Test cost calculation
        input_tokens = 2000  # 2K input tokens
        output_tokens = 1000  # 1K output tokens
        
        cost = adapter._calculate_cost(input_tokens, output_tokens)
        
        # Expected cost: (2000/1000 * $0.0100) + (1000/1000 * $0.0300) = $0.020 + $0.030 = $0.050
        expected_cost = Decimal('0.050')
        assert cost == expected_cost
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_calculate_cost_gpt_4o_mini(self, mock_openai_class):
        """Test cost calculation for gpt-4o-mini model."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(model_name='gpt-4o-mini', api_key='sk-test-key')
        
        # Test cost calculation
        input_tokens = 5000  # 5K input tokens
        output_tokens = 2000  # 2K output tokens
        
        cost = adapter._calculate_cost(input_tokens, output_tokens)
        
        # Expected cost: (5000/1000 * $0.0001) + (2000/1000 * $0.0006) = $0.0005 + $0.0012 = $0.0017
        expected_cost = Decimal('0.0017')
        assert cost == expected_cost
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_calculate_cost_unknown_model(self, mock_openai_class):
        """Test cost calculation for unknown model."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(model_name='unknown-model', api_key='sk-test-key')
        
        cost = adapter._calculate_cost(1000, 500)
        
        # Should return 0 for unknown models
        assert cost == Decimal('0.00')
    
    # ==================== REQUEST FORMATTING TESTS ====================
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_format_request_basic(self, mock_openai_class, valid_config, generation_params):
        """Test basic request formatting."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(**valid_config)
        
        prompt = "What is machine learning?"
        formatted_request = adapter._format_request(prompt, generation_params)
        
        # Verify request structure
        assert 'model' in formatted_request
        assert 'messages' in formatted_request
        assert 'max_tokens' in formatted_request
        assert 'temperature' in formatted_request
        assert 'top_p' in formatted_request
        assert 'frequency_penalty' in formatted_request
        assert 'presence_penalty' in formatted_request
        assert 'stop' in formatted_request
        
        # Verify values
        assert formatted_request['model'] == 'gpt-3.5-turbo'
        assert len(formatted_request['messages']) == 1
        assert formatted_request['messages'][0]['role'] == 'user'
        assert formatted_request['messages'][0]['content'] == prompt
        assert formatted_request['max_tokens'] == 500
        assert formatted_request['temperature'] == 0.8
        assert formatted_request['top_p'] == 0.9
        assert formatted_request['frequency_penalty'] == 0.1
        assert formatted_request['presence_penalty'] == 0.1
        assert formatted_request['stop'] == ["END", "STOP"]
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_format_request_with_context(self, mock_openai_class, valid_config, generation_params):
        """Test request formatting with context."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(**valid_config)
        
        prompt = "What is machine learning?"
        context = "Machine learning is a branch of artificial intelligence."
        
        formatted_request = adapter._format_request(prompt, generation_params, context=context)
        
        # Verify context integration
        assert len(formatted_request['messages']) == 2
        assert formatted_request['messages'][0]['role'] == 'system'
        assert formatted_request['messages'][0]['content'] == context
        assert formatted_request['messages'][1]['role'] == 'user'
        assert formatted_request['messages'][1]['content'] == prompt
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_format_request_parameter_filtering(self, mock_openai_class, valid_config):
        """Test parameter filtering for None values."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(**valid_config)
        
        # Test with None parameters
        params = GenerationParams(
            max_tokens=1000,
            temperature=None,  # Should be filtered out
            top_p=0.95,
            frequency_penalty=None,  # Should be filtered out
            presence_penalty=0.3,
            stop_sequences=None  # Should be filtered out
        )
        
        formatted_request = adapter._format_request("test prompt", params)
        
        # Verify None parameters are filtered out
        assert 'temperature' not in formatted_request
        assert 'frequency_penalty' not in formatted_request
        assert 'stop' not in formatted_request
        
        # Verify non-None parameters are present
        assert formatted_request['max_tokens'] == 1000
        assert formatted_request['top_p'] == 0.95
        assert formatted_request['presence_penalty'] == 0.3
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_format_request_model_limits(self, mock_openai_class, valid_config):
        """Test request formatting respects model limits."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(**valid_config)
        
        # Test with tokens exceeding model limit for gpt-3.5-turbo (16385)
        params = GenerationParams(max_tokens=20000)
        
        formatted_request = adapter._format_request("test prompt", params)
        
        # Should respect model limit
        model_limit = adapter.MODEL_LIMITS.get('gpt-3.5-turbo', 16385)
        assert formatted_request['max_tokens'] <= model_limit
    
    # ==================== STREAMING RESPONSE TESTS ====================
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_generate_streaming_success(self, mock_openai_class, valid_config, generation_params):
        """Test successful streaming response generation."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Create mock streaming response chunks
        chunk1 = Mock()
        chunk1.choices = [Mock()]
        chunk1.choices[0].delta.content = "Hello"
        chunk1.choices[0].finish_reason = None
        
        chunk2 = Mock()
        chunk2.choices = [Mock()]
        chunk2.choices[0].delta.content = " world"
        chunk2.choices[0].finish_reason = None
        
        chunk3 = Mock()
        chunk3.choices = [Mock()]
        chunk3.choices[0].delta.content = "!"
        chunk3.choices[0].finish_reason = "stop"
        
        # Mock usage info in final chunk
        chunk3.usage = Mock()
        chunk3.usage.prompt_tokens = 10
        chunk3.usage.completion_tokens = 20
        chunk3.usage.total_tokens = 30
        
        mock_stream = iter([chunk1, chunk2, chunk3])
        mock_client.chat.completions.create.return_value = mock_stream
        
        adapter = OpenAIAdapter(**valid_config)
        
        # Test streaming generation
        result = adapter.generate_streaming("Test prompt", generation_params)
        
        # Verify streaming result
        assert hasattr(result, '__iter__')
        
        # Collect all chunks
        chunks = list(result)
        assert len(chunks) == 3
        
        # Verify chunk content
        assert chunks[0]['text'] == "Hello"
        assert chunks[1]['text'] == " world"
        assert chunks[2]['text'] == "!"
        
        # Verify final chunk has usage info
        assert chunks[2]['finish_reason'] == "stop"
        assert 'usage' in chunks[2]
        assert chunks[2]['usage']['prompt_tokens'] == 10
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_generate_streaming_error_handling(self, mock_openai_class, valid_config, generation_params):
        """Test streaming error handling."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock stream that raises error
        def error_stream():
            yield Mock()  # First chunk succeeds
            raise Exception("Streaming error")
        
        mock_client.chat.completions.create.return_value = error_stream()
        
        adapter = OpenAIAdapter(**valid_config)
        
        # Test streaming with error
        result = adapter.generate_streaming("Test prompt", generation_params)
        
        # Should handle error gracefully
        chunks = []
        try:
            for chunk in result:
                chunks.append(chunk)
        except LLMError as e:
            assert "Streaming error" in str(e)
        
        # Should have received first chunk before error
        assert len(chunks) >= 1
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_process_streaming_chunk_empty_content(self, mock_openai_class, valid_config):
        """Test processing streaming chunk with empty content."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(**valid_config)
        
        # Create chunk with no content
        chunk = Mock()
        chunk.choices = [Mock()]
        chunk.choices[0].delta.content = None
        chunk.choices[0].finish_reason = None
        
        result = adapter._process_streaming_chunk(chunk)
        
        # Should return None for empty content
        assert result is None
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_process_streaming_chunk_final_chunk(self, mock_openai_class, valid_config):
        """Test processing final streaming chunk with usage info."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(**valid_config)
        
        # Create final chunk with usage info
        chunk = Mock()
        chunk.choices = [Mock()]
        chunk.choices[0].delta.content = "Final text"
        chunk.choices[0].finish_reason = "stop"
        chunk.usage = Mock()
        chunk.usage.prompt_tokens = 50
        chunk.usage.completion_tokens = 100
        chunk.usage.total_tokens = 150
        
        result = adapter._process_streaming_chunk(chunk)
        
        # Should include usage info
        assert result['text'] == "Final text"
        assert result['finish_reason'] == "stop"
        assert result['usage']['prompt_tokens'] == 50
        assert result['usage']['completion_tokens'] == 100
        assert 'cost' in result
    
    # ==================== ERROR HANDLING TESTS ====================
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_error_mapping_rate_limit(self, mock_openai_class, valid_config):
        """Test error mapping for rate limits."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(**valid_config)
        
        # Simulate OpenAI rate limit error
        from openai import RateLimitError as OpenAIRateLimitError
        openai_error = Mock(spec=OpenAIRateLimitError)
        openai_error.response = Mock()
        openai_error.response.status_code = 429
        openai_error.message = "Rate limit exceeded"
        
        with patch('src.components.generators.llm_adapters.openai_adapter.openai.RateLimitError', OpenAIRateLimitError):
            mapped_error = adapter._map_error(openai_error)
        
        assert isinstance(mapped_error, RateLimitError)
        assert "Rate limit exceeded" in str(mapped_error)
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_error_mapping_authentication(self, mock_openai_class, valid_config):
        """Test error mapping for authentication errors."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(**valid_config)
        
        # Simulate OpenAI authentication error
        from openai import AuthenticationError as OpenAIAuthError
        openai_error = Mock(spec=OpenAIAuthError)
        openai_error.response = Mock()
        openai_error.response.status_code = 401
        openai_error.message = "Invalid API key"
        
        with patch('src.components.generators.llm_adapters.openai_adapter.openai.AuthenticationError', OpenAIAuthError):
            mapped_error = adapter._map_error(openai_error)
        
        assert isinstance(mapped_error, AuthenticationError)
        assert "Invalid API key" in str(mapped_error)
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_error_mapping_model_not_found(self, mock_openai_class, valid_config):
        """Test error mapping for model not found errors."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(**valid_config)
        
        # Simulate OpenAI not found error
        from openai import NotFoundError as OpenAINotFoundError
        openai_error = Mock(spec=OpenAINotFoundError)
        openai_error.response = Mock()
        openai_error.response.status_code = 404
        openai_error.message = "Model not found"
        
        with patch('src.components.generators.llm_adapters.openai_adapter.openai.NotFoundError', OpenAINotFoundError):
            mapped_error = adapter._map_error(openai_error)
        
        assert isinstance(mapped_error, ModelNotFoundError)
        assert "Model not found" in str(mapped_error)
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_error_mapping_generic(self, mock_openai_class, valid_config):
        """Test error mapping for generic errors."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(**valid_config)
        
        # Simulate generic error
        generic_error = Exception("Something went wrong")
        
        mapped_error = adapter._map_error(generic_error)
        
        assert isinstance(mapped_error, LLMError)
        assert "Something went wrong" in str(mapped_error)
    
    # ==================== RESPONSE PROCESSING TESTS ====================
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_process_response_success(self, mock_openai_class, valid_config):
        """Test successful response processing."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(**valid_config)
        
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
        
        # Verify cost tracking was updated
        assert adapter._input_tokens == 100
        assert adapter._output_tokens == 200
        assert adapter._total_cost > Decimal('0.00')
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_process_response_multiple_choices(self, mock_openai_class, valid_config):
        """Test response processing with multiple choices."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(**valid_config)
        
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
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_process_response_empty_choices(self, mock_openai_class, valid_config):
        """Test response processing with empty choices."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(**valid_config)
        
        # Create mock response with no choices
        mock_response = Mock()
        mock_response.choices = []
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 0
        
        with pytest.raises(LLMError, match="No response generated"):
            adapter._process_response(mock_response)
    
    # ==================== INTEGRATION TESTS ====================
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_generate_end_to_end(self, mock_openai_class, valid_config, generation_params, mock_tiktoken):
        """Test end-to-end generation process."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_tiktoken_module, mock_encoding = mock_tiktoken
        
        # Configure successful response
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "Generated response"
        mock_choice.finish_reason = "stop"
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 100
        
        mock_client.chat.completions.create.return_value = mock_response
        
        adapter = OpenAIAdapter(**valid_config)
        
        result = adapter.generate("What is AI?", generation_params)
        
        # Verify end-to-end flow
        assert result['text'] == "Generated response"
        assert result['finish_reason'] == "stop"
        
        # Verify cost tracking
        assert adapter._input_tokens == 50
        assert adapter._output_tokens == 100
        assert adapter._total_cost > Decimal('0.00')
        
        # Verify API call
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs['model'] == 'gpt-3.5-turbo'
        assert len(call_kwargs['messages']) == 1
        assert call_kwargs['messages'][0]['content'] == "What is AI?"
        assert call_kwargs['stream'] is False
    
    # ==================== PERFORMANCE AND EDGE CASE TESTS ====================
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_empty_prompt_handling(self, mock_openai_class, valid_config, generation_params):
        """Test handling of empty prompts."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        adapter = OpenAIAdapter(**valid_config)
        
        # Test empty prompt
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            adapter.generate("", generation_params)
        
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            adapter.generate("   ", generation_params)
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_very_long_prompt_token_estimation(self, mock_openai_class, valid_config, mock_tiktoken):
        """Test token estimation for very long prompts."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_tiktoken_module, mock_encoding = mock_tiktoken
        
        adapter = OpenAIAdapter(**valid_config)
        
        # Create very long prompt
        very_long_prompt = "This is a test. " * 5000  # Very long prompt
        
        # Mock large token count
        mock_encoding.encode.return_value = list(range(20000))  # 20K tokens
        
        token_count = adapter._count_tokens(very_long_prompt)
        
        # Should count tokens correctly
        assert token_count == 20000
    
    @patch('src.components.generators.llm_adapters.openai_adapter.OPENAI_AVAILABLE', True)
    @patch('src.components.generators.llm_adapters.openai_adapter.OpenAI')
    def test_concurrent_request_handling(self, mock_openai_class, valid_config, generation_params):
        """Test concurrent request handling (thread safety)."""
        import threading
        
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Configure successful response
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "Concurrent response"
        mock_choice.finish_reason = "stop"
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        
        mock_client.chat.completions.create.return_value = mock_response
        
        adapter = OpenAIAdapter(**valid_config)
        
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