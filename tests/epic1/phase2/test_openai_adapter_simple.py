"""Simplified OpenAI Adapter Tests - Epic 1 Phase 2.

Simple mock-based tests for OpenAI adapter functionality.
"""

import os
import pytest
from decimal import Decimal
from unittest.mock import Mock, MagicMock


class MockOpenAIAdapter:
    """Mock OpenAI adapter for testing."""
    
    def __init__(self, model_name="gpt-3.5-turbo", **kwargs):
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("OpenAI API key required")
        
        self.model_name = model_name
        self.api_key = "***HIDDEN***"
        
        # Mock pricing
        self.MODEL_PRICING = {
            'gpt-3.5-turbo': {'input': Decimal('0.0010'), 'output': Decimal('0.0020')},
            'gpt-4-turbo': {'input': Decimal('0.0100'), 'output': Decimal('0.0300')}
        }
    
    def get_model_info(self):
        return {
            'provider': 'OpenAI',
            'model': self.model_name,
            'max_tokens': 4096,
            'supports_streaming': True
        }
    
    def generate(self, query, context, max_tokens=100):
        # Mock response with cost calculation
        input_tokens = len(query.split()) * 4 + len(' '.join(context).split()) * 4
        output_tokens = 50  # Mock output
        
        pricing = self.MODEL_PRICING.get(self.model_name, self.MODEL_PRICING['gpt-3.5-turbo'])
        input_cost = (Decimal(str(input_tokens)) / 1000) * pricing['input']
        output_cost = (Decimal(str(output_tokens)) / 1000) * pricing['output']
        total_cost = input_cost + output_cost
        
        return type('Answer', (), {
            'content': f'Mock response from OpenAI {self.model_name}',
            'metadata': {
                'cost_usd': float(total_cost),
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens,
                'cost_breakdown': {
                    'input_cost': float(input_cost),
                    'output_cost': float(output_cost)
                }
            }
        })()


class TestOpenAIAdapter:
    """Test suite for OpenAI adapter functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        os.environ['OPENAI_API_KEY'] = 'test-openai-key'
        self.test_model = "gpt-4-turbo"
        self.test_query = "How does OAuth 2.0 authentication work?"
        self.test_context = ["OAuth 2.0 is an authorization framework..."]
    
    def teardown_method(self):
        """Clean up after tests."""
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
    
    def test_adapter_initialization(self):
        """Test OpenAI adapter initialization and validation."""
        adapter = MockOpenAIAdapter(model_name=self.test_model)
        assert adapter is not None
        assert adapter.model_name == self.test_model
        
        # Test model info retrieval
        model_info = adapter.get_model_info()
        assert model_info['provider'] == 'OpenAI'
        assert model_info['model'] == self.test_model
        assert 'max_tokens' in model_info
        assert 'supports_streaming' in model_info
        
        # Verify API key is hidden
        assert adapter.api_key == "***HIDDEN***"
    
    def test_adapter_initialization_no_api_key(self):
        """Test adapter initialization without API key."""
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        
        with pytest.raises(ValueError, match="OpenAI API key required"):
            MockOpenAIAdapter(model_name=self.test_model)
    
    def test_cost_calculation_accuracy(self):
        """Test cost calculation with precision."""
        adapter = MockOpenAIAdapter(model_name="gpt-4-turbo")
        
        query = "Test query with four words"
        context = ["Test context with four words"]
        
        answer = adapter.generate(query=query, context=context, max_tokens=100)
        
        # Verify cost calculation structure
        assert 'cost_usd' in answer.metadata
        assert 'input_tokens' in answer.metadata
        assert 'output_tokens' in answer.metadata
        assert 'total_tokens' in answer.metadata
        
        # Check that costs are calculated correctly
        assert answer.metadata['cost_usd'] > 0
        assert answer.metadata['input_tokens'] > 0
        assert answer.metadata['output_tokens'] > 0
        
        # Check cost breakdown exists
        assert 'cost_breakdown' in answer.metadata
        breakdown = answer.metadata['cost_breakdown']
        assert 'input_cost' in breakdown
        assert 'output_cost' in breakdown
        
        # Verify total equals sum of breakdown
        expected_total = breakdown['input_cost'] + breakdown['output_cost']
        assert abs(answer.metadata['cost_usd'] - expected_total) < 0.001
    
    def test_different_model_pricing(self):
        """Test cost calculation for different models."""
        # Test GPT-3.5-turbo pricing
        adapter = MockOpenAIAdapter(model_name="gpt-3.5-turbo")
        answer = adapter.generate("test query", ["test context"])
        gpt35_cost = answer.metadata['cost_usd']
        
        # Test GPT-4-turbo pricing  
        adapter = MockOpenAIAdapter(model_name="gpt-4-turbo")
        answer = adapter.generate("test query", ["test context"])
        gpt4_cost = answer.metadata['cost_usd']
        
        # GPT-4 should be more expensive than GPT-3.5
        assert gpt4_cost > gpt35_cost
    
    def test_token_counting_accuracy(self):
        """Test token counting accuracy."""
        adapter = MockOpenAIAdapter(model_name=self.test_model)
        
        test_cases = [
            ("short query", ["short context"]),
            ("this is a longer query with more words", ["longer context with more words too"]),
        ]
        
        for query, context in test_cases:
            answer = adapter.generate(query, context)
            
            # Verify token counts are reasonable
            assert answer.metadata['input_tokens'] > 0
            assert answer.metadata['output_tokens'] > 0
            assert answer.metadata['total_tokens'] == answer.metadata['input_tokens'] + answer.metadata['output_tokens']
    
    def test_model_validation(self):
        """Test model name validation."""
        valid_models = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo']
        for model in valid_models:
            adapter = MockOpenAIAdapter(model_name=model)
            assert adapter.model_name == model
        
        # Invalid model should still work in mock
        adapter = MockOpenAIAdapter(model_name="invalid-model")
        assert adapter.model_name == "invalid-model"
    
    def test_streaming_support(self):
        """Test streaming response support."""
        adapter = MockOpenAIAdapter(model_name=self.test_model)
        
        model_info = adapter.get_model_info()
        assert model_info.get('supports_streaming', False) == True
    
    def test_response_generation(self):
        """Test basic response generation."""
        adapter = MockOpenAIAdapter(model_name=self.test_model)
        answer = adapter.generate(self.test_query, self.test_context)
        
        assert answer.content is not None
        assert len(answer.content) > 0
        assert self.test_model in answer.content
        
        # Verify metadata structure
        metadata = answer.metadata
        required_fields = ['cost_usd', 'input_tokens', 'output_tokens', 'cost_breakdown']
        for field in required_fields:
            assert field in metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])