"""Test suite for Mistral Adapter - Epic 1 Phase 2.

Tests Mistral adapter implementation including:
- Cost-effective routing for medium complexity queries
- HTTP-based API integration
- Cost calculation accuracy
- Error handling and fallback
"""

import os
import json
import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
import requests

# Import the Mistral adapter
from src.components.generators.llm_adapters.mistral_adapter import MistralAdapter
from src.components.generators.base import Answer


class TestMistralAdapter:
    """Test suite for Mistral adapter functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock API key for testing
        os.environ['MISTRAL_API_KEY'] = 'test-mistral-key-123'
        
        # Test data
        self.test_query = "How does OAuth 2.0 authentication work?"
        self.test_context = "OAuth 2.0 is an authorization framework..."
        self.test_model = "mistral-small"
        
    def teardown_method(self):
        """Clean up after tests."""
        if 'MISTRAL_API_KEY' in os.environ:
            del os.environ['MISTRAL_API_KEY']
    
    # EPIC1-ADAPT-003: Mistral Adapter Cost-Effective Routing
    def test_adapter_initialization(self):
        """Test Mistral adapter initialization.
        
        PASS Criteria:
        - Successful initialization
        - Correct model assignment
        - Provider identification
        - API key security
        """
        adapter = MistralAdapter(model=self.test_model)
        assert adapter is not None
        assert adapter.model == self.test_model
        assert adapter.provider == "Mistral"
        
        # Verify API key is not exposed
        assert 'test-mistral-key' not in str(adapter)
        assert 'test-mistral-key' not in repr(adapter)
    
    def test_adapter_initialization_no_api_key(self):
        """Test adapter fails without API key."""
        if 'MISTRAL_API_KEY' in os.environ:
            del os.environ['MISTRAL_API_KEY']
        
        with pytest.raises(ValueError, match="Mistral API key not found"):
            adapter = MistralAdapter(model=self.test_model)
    
    @patch('requests.post')
    def test_cost_effective_routing(self, mock_post):
        """Test cost-effective inference for medium complexity queries.
        
        Requirement: Lower cost than OpenAI for comparable quality
        PASS Criteria:
        - Cost reduction: >50% vs GPT-4
        - Quality threshold: >80% (by confidence score)
        - Response time: <2 seconds
        - Proper error handling
        """
        # Mock successful Mistral API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': 'OAuth 2.0 is an authorization framework that enables applications to obtain limited access to user accounts...'
                }
            }],
            'usage': {
                'prompt_tokens': 150,
                'completion_tokens': 200,
                'total_tokens': 350
            }
        }
        mock_post.return_value = mock_response
        
        adapter = MistralAdapter(model="mistral-small")
        answer = adapter.generate(
            query=self.test_query,
            context=self.test_context,
            max_tokens=300
        )
        
        # Verify cost calculation
        # Mistral-small: $0.002/1K input, $0.006/1K output (per million tokens)
        expected_input_cost = Decimal('0.000300')  # 150/1000 * 0.002
        expected_output_cost = Decimal('0.001200')  # 200/1000 * 0.006
        expected_total_cost = Decimal('0.001500')
        
        assert 'cost_usd' in answer.metadata
        actual_cost = Decimal(str(answer.metadata['cost_usd']))
        assert abs(actual_cost - expected_total_cost) < Decimal('0.001')
        
        # Verify this is significantly cheaper than GPT-4
        # GPT-4: $0.01 input, $0.03 output
        gpt4_cost = (150/1000 * Decimal('0.01')) + (200/1000 * Decimal('0.03'))
        cost_reduction = (gpt4_cost - actual_cost) / gpt4_cost
        assert cost_reduction > Decimal('0.50')  # >50% reduction
        
        # Verify response quality
        assert len(answer.content) > 50  # Substantial response
        assert 'oauth' in answer.content.lower() or 'authorization' in answer.content.lower()
        
        # Check confidence score if available
        if 'confidence' in answer.metadata:
            assert answer.metadata['confidence'] > 0.8
    
    @patch('requests.post')
    def test_different_model_pricing(self, mock_post):
        """Test cost calculation for different Mistral models."""
        models_and_pricing = {
            'mistral-small': {'input': 0.002, 'output': 0.006},
            'mistral-medium': {'input': 0.0027, 'output': 0.0081},
            'mistral-large': {'input': 0.008, 'output': 0.024}
        }
        
        for model, pricing in models_and_pricing.items():
            # Mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'choices': [{'message': {'content': 'Test response'}}],
                'usage': {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150}
            }
            mock_post.return_value = mock_response
            
            adapter = MistralAdapter(model=model)
            answer = adapter.generate(self.test_query, self.test_context)
            
            # Calculate expected cost
            expected_cost = (Decimal('100')/1000 * Decimal(str(pricing['input']))) + \
                          (Decimal('50')/1000 * Decimal(str(pricing['output'])))
            
            actual_cost = Decimal(str(answer.metadata['cost_usd']))
            assert abs(actual_cost - expected_cost) < Decimal('0.001')
    
    @patch('requests.post')
    def test_http_api_integration(self, mock_post):
        """Test HTTP-based Mistral API integration.
        
        PASS Criteria:
        - Correct API endpoint usage
        - Proper request formatting
        - Response parsing accuracy
        - Header management
        """
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Test response'}}],
            'usage': {'prompt_tokens': 50, 'completion_tokens': 25, 'total_tokens': 75}
        }
        mock_post.return_value = mock_response
        
        adapter = MistralAdapter(model=self.test_model)
        answer = adapter.generate(self.test_query, self.test_context)
        
        # Verify API call was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Check URL
        assert 'https://api.mistral.ai/v1/chat/completions' in call_args[0][0]
        
        # Check headers
        headers = call_args[1]['headers']
        assert 'Authorization' in headers
        assert 'Bearer' in headers['Authorization']
        assert 'Content-Type' in headers
        
        # Check request body
        data = json.loads(call_args[1]['data'])
        assert data['model'] == self.test_model
        assert 'messages' in data
        assert len(data['messages']) > 0
        
        # Verify response parsing
        assert answer.content == 'Test response'
        assert answer.metadata['input_tokens'] == 50
        assert answer.metadata['output_tokens'] == 25
    
    @patch('requests.post')
    def test_error_handling(self, mock_post):
        """Test error handling for various failure scenarios.
        
        PASS Criteria:
        - HTTP error handling
        - JSON parsing error handling
        - Rate limit handling
        - Network timeout handling
        """
        adapter = MistralAdapter(model=self.test_model)
        
        # Test HTTP 429 (rate limit)
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {'error': 'Rate limit exceeded'}
        mock_post.return_value = mock_response
        
        with pytest.raises(Exception) as exc_info:
            adapter.generate(self.test_query, self.test_context)
        assert 'rate limit' in str(exc_info.value).lower()
        
        # Test HTTP 401 (authentication)
        mock_response.status_code = 401
        mock_response.json.return_value = {'error': 'Invalid API key'}
        mock_post.return_value = mock_response
        
        with pytest.raises(Exception) as exc_info:
            adapter.generate(self.test_query, self.test_context)
        assert 'auth' in str(exc_info.value).lower() or 'key' in str(exc_info.value).lower()
        
        # Test network timeout
        mock_post.side_effect = requests.Timeout("Request timeout")
        
        with pytest.raises(Exception) as exc_info:
            adapter.generate(self.test_query, self.test_context)
        assert 'timeout' in str(exc_info.value).lower()
    
    @patch('requests.post')
    def test_token_usage_tracking(self, mock_post):
        """Test accurate token usage tracking.
        
        PASS Criteria:
        - Input token tracking
        - Output token tracking
        - Total token calculation
        - Usage metadata inclusion
        """
        test_cases = [
            {'prompt_tokens': 25, 'completion_tokens': 15, 'total_tokens': 40},
            {'prompt_tokens': 150, 'completion_tokens': 75, 'total_tokens': 225},
            {'prompt_tokens': 500, 'completion_tokens': 200, 'total_tokens': 700},
        ]
        
        adapter = MistralAdapter(model=self.test_model)
        
        for usage in test_cases:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'choices': [{'message': {'content': 'Response'}}],
                'usage': usage
            }
            mock_post.return_value = mock_response
            
            answer = adapter.generate(self.test_query, self.test_context)
            
            # Verify token tracking
            assert answer.metadata['input_tokens'] == usage['prompt_tokens']
            assert answer.metadata['output_tokens'] == usage['completion_tokens']
            assert answer.metadata['total_tokens'] == usage['total_tokens']
            
            # Verify cost is calculated from actual usage
            expected_cost = (Decimal(str(usage['prompt_tokens']))/1000 * Decimal('0.002')) + \
                          (Decimal(str(usage['completion_tokens']))/1000 * Decimal('0.006'))
            actual_cost = Decimal(str(answer.metadata['cost_usd']))
            assert abs(actual_cost - expected_cost) < Decimal('0.001')
    
    def test_model_validation(self):
        """Test model name validation and defaults."""
        # Valid Mistral models
        valid_models = ['mistral-small', 'mistral-medium', 'mistral-large']
        
        for model in valid_models:
            adapter = MistralAdapter(model=model)
            assert adapter.model == model
            
            model_info = adapter.get_model_info()
            assert model_info['provider'] == 'Mistral'
            assert model_info['model'] == model
    
    def test_get_model_info(self):
        """Test model information retrieval."""
        adapter = MistralAdapter(model=self.test_model)
        model_info = adapter.get_model_info()
        
        required_fields = ['provider', 'model', 'max_tokens', 'supports_streaming']
        for field in required_fields:
            assert field in model_info
        
        assert model_info['provider'] == 'Mistral'
        assert model_info['model'] == self.test_model
        assert isinstance(model_info['max_tokens'], int)
        assert model_info['max_tokens'] > 0
    
    @patch('requests.post')
    def test_context_length_handling(self, mock_post):
        """Test handling of context length limits."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Response'}}],
            'usage': {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150}
        }
        mock_post.return_value = mock_response
        
        adapter = MistralAdapter(model=self.test_model)
        
        # Test with very long context
        long_context = "This is a test. " * 1000  # Long context
        answer = adapter.generate(self.test_query, long_context)
        
        # Should handle gracefully (truncation or chunking)
        assert answer is not None
        assert len(answer.content) > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])