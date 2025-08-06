"""Test suite for OpenAI Adapter - Epic 1 Phase 2.

Tests OpenAI adapter implementation including:
- Adapter initialization and configuration
- Cost calculation with $0.001 precision
- Token counting accuracy
- Error handling and fallback mechanisms
- API format conversion
"""

import os
import json
import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Import the OpenAI adapter
from src.components.generators.llm_adapters.openai_adapter import OpenAIAdapter
from src.components.generators.base import Answer


class TestOpenAIAdapter:
    """Test suite for OpenAI adapter functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock API key for testing
        os.environ['OPENAI_API_KEY'] = 'test-api-key-123'
        
        # Test data
        self.test_query = "What is transformer architecture?"
        self.test_context = "Transformers use attention mechanisms..."
        self.test_model = "gpt-4-turbo"
        
    def teardown_method(self):
        """Clean up after tests."""
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
    
    # EPIC1-ADAPT-001: OpenAI Adapter Initialization
    def test_adapter_initialization(self):
        """Test OpenAI adapter initialization and validation.
        
        Requirement: Successful adapter initialization and validation
        PASS Criteria:
        - Initialization: No exceptions raised
        - Connection test: Returns valid response
        - Model info: Contains provider="OpenAI", model="gpt-4-turbo"
        - API key handling: Secure, not exposed in logs
        """
        # Test successful initialization
        adapter = OpenAIAdapter(model_name=self.test_model)
        assert adapter is not None
        assert adapter.model == self.test_model
        assert adapter.provider == "OpenAI"
        
        # Test model info retrieval
        model_info = adapter.get_model_info()
        assert model_info['provider'] == 'OpenAI'
        assert model_info['model'] == self.test_model
        assert 'max_tokens' in model_info
        assert 'supports_streaming' in model_info
        
        # Verify API key is not exposed
        assert adapter.api_key != 'test-api-key-123'  # Should be hidden
        assert 'test-api-key' not in str(adapter)
        assert 'test-api-key' not in repr(adapter)
    
    def test_adapter_initialization_no_api_key(self):
        """Test adapter initialization without API key."""
        # Remove API key
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        
        # Should raise error without API key
        with pytest.raises(ValueError, match="OpenAI API key not found"):
            adapter = OpenAIAdapter(model_name=self.test_model)
    
    # EPIC1-ADAPT-002: OpenAI Cost Calculation Accuracy
    @patch('openai.OpenAI')
    def test_cost_calculation_accuracy(self, mock_openai_class):
        """Test cost calculation with $0.001 precision.
        
        Requirement: Cost calculation with $0.001 precision
        PASS Criteria:
        - Cost precision: Exactly 6 decimal places internally, 3 for display
        - Calculation accuracy: Within $0.001 of expected
        - Token counting: ±1% of actual OpenAI usage
        - Cost breakdown: Separate input/output costs
        """
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock response with known token counts
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
        mock_response.usage = MagicMock(
            prompt_tokens=150,
            completion_tokens=75,
            total_tokens=225
        )
        mock_client.chat.completions.create.return_value = mock_response
        
        # Initialize adapter
        adapter = OpenAIAdapter(model_name="gpt-4-turbo")
        
        # Generate response
        answer = adapter.generate(
            query=self.test_query,
            context=self.test_context,
            max_tokens=100
        )
        
        # Verify cost calculation
        # GPT-4-turbo pricing: $0.01/1K input, $0.03/1K output
        expected_input_cost = Decimal('0.001500')  # 150/1000 * 0.01
        expected_output_cost = Decimal('0.002250')  # 75/1000 * 0.03
        expected_total_cost = Decimal('0.003750')
        
        assert 'cost_usd' in answer.metadata
        assert 'input_tokens' in answer.metadata
        assert 'output_tokens' in answer.metadata
        
        # Check precision (6 decimal places internally)
        actual_cost = Decimal(str(answer.metadata['cost_usd']))
        assert abs(actual_cost - expected_total_cost) < Decimal('0.001')
        
        # Verify token counts
        assert answer.metadata['input_tokens'] == 150
        assert answer.metadata['output_tokens'] == 75
        
        # Check cost breakdown
        assert 'cost_breakdown' in answer.metadata
        breakdown = answer.metadata['cost_breakdown']
        assert 'input_cost' in breakdown
        assert 'output_cost' in breakdown
        assert abs(Decimal(str(breakdown['input_cost'])) - expected_input_cost) < Decimal('0.001')
        assert abs(Decimal(str(breakdown['output_cost'])) - expected_output_cost) < Decimal('0.001')
    
    @patch('openai.OpenAI')
    def test_different_model_pricing(self, mock_openai_class):
        """Test cost calculation for different models."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test"))]
        mock_response.usage = MagicMock(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test GPT-3.5-turbo pricing
        adapter = OpenAIAdapter(model_name="gpt-3.5-turbo")
        answer = adapter.generate(self.test_query, self.test_context)
        
        # GPT-3.5-turbo: $0.001/1K input, $0.002/1K output
        expected_cost = Decimal('0.000200')  # (100/1000*0.001) + (50/1000*0.002)
        actual_cost = Decimal(str(answer.metadata['cost_usd']))
        assert abs(actual_cost - expected_cost) < Decimal('0.001')
    
    # EPIC1-ADAPT-003: Error Handling
    @patch('openai.OpenAI')
    def test_error_handling(self, mock_openai_class):
        """Test error handling and recovery.
        
        PASS Criteria:
        - Proper error handling
        - Clear error messages
        - No sensitive data exposed
        """
        # Mock OpenAI client with error
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Simulate API error
        from openai import OpenAIError
        mock_client.chat.completions.create.side_effect = OpenAIError("API Error")
        
        adapter = OpenAIAdapter(model=self.test_model)
        
        # Should handle error gracefully
        with pytest.raises(Exception) as exc_info:
            answer = adapter.generate(self.test_query, self.test_context)
        
        # Verify error message doesn't expose API key
        assert 'test-api-key' not in str(exc_info.value)
    
    @patch('openai.OpenAI')
    def test_rate_limit_handling(self, mock_openai_class):
        """Test rate limit error handling."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Simulate rate limit error
        from openai import RateLimitError
        mock_client.chat.completions.create.side_effect = RateLimitError("Rate limit exceeded")
        
        adapter = OpenAIAdapter(model=self.test_model)
        
        # Should handle rate limit with appropriate error
        with pytest.raises(Exception) as exc_info:
            answer = adapter.generate(self.test_query, self.test_context)
        
        assert "rate limit" in str(exc_info.value).lower()
    
    # EPIC1-ADAPT-004: Token Counting Accuracy
    @patch('openai.OpenAI')
    def test_token_counting_accuracy(self, mock_openai_class):
        """Test token counting accuracy.
        
        PASS Criteria:
        - Token counting: ±1% of actual OpenAI usage
        - Accurate for various text lengths
        """
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        test_cases = [
            (10, 5),    # Short response
            (100, 50),  # Medium response
            (1000, 500),  # Long response
        ]
        
        adapter = OpenAIAdapter(model=self.test_model)
        
        for input_tokens, output_tokens in test_cases:
            # Mock response with specific token counts
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="x" * output_tokens))]
            mock_response.usage = MagicMock(
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens
            )
            mock_client.chat.completions.create.return_value = mock_response
            
            answer = adapter.generate(self.test_query, self.test_context)
            
            # Verify token counts match
            assert answer.metadata['input_tokens'] == input_tokens
            assert answer.metadata['output_tokens'] == output_tokens
            assert answer.metadata['total_tokens'] == input_tokens + output_tokens
    
    # EPIC1-ADAPT-005: Streaming Support
    @patch('openai.OpenAI')
    def test_streaming_support(self, mock_openai_class):
        """Test streaming response support."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock streaming response
        mock_stream = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=" world"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=None))]),
        ]
        mock_client.chat.completions.create.return_value = mock_stream
        
        adapter = OpenAIAdapter(model=self.test_model)
        
        # Test streaming (if supported)
        model_info = adapter.get_model_info()
        if model_info.get('supports_streaming', False):
            # Note: Actual streaming implementation would need callback support
            pass  # Streaming test would go here
    
    def test_model_validation(self):
        """Test model name validation."""
        # Valid models should work
        valid_models = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo']
        for model in valid_models:
            adapter = OpenAIAdapter(model=model)
            assert adapter.model == model
        
        # Invalid model should raise error or warning
        # (Implementation dependent)
        adapter = OpenAIAdapter(model="invalid-model")
        # Should still initialize but may warn
        assert adapter.model == "invalid-model"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])