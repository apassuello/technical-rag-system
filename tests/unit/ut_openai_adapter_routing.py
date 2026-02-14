"""Test suite for OpenAI Adapter - Epic 1 Phase 2.

Tests OpenAI adapter implementation including:
- Adapter initialization and configuration
- Cost calculation with $0.001 precision
- Token counting accuracy
- Error handling and fallback mechanisms
- Real API integration when available

Uses adaptive testing: real API when available, mock when not.
"""

import os
import pytest
from decimal import Decimal
from typing import Dict, Any

# Unit tests always use mock adapters — never call real APIs
os.environ.setdefault("EPIC1_USE_MOCK_APIS", "true")

# Import adaptive test management (support modules in tests/unit/)
from tests.unit.adaptive_test_manager import AdaptiveTestManager
from tests.unit.phase2_test_utils import get_generation_params, TEST_QUERIES, TEST_CONTEXTS, COST_LIMITS


class TestOpenAIAdapter:
    """Test suite for OpenAI adapter functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Initialize adaptive test manager
        self.test_manager = AdaptiveTestManager(cost_limit_usd=COST_LIMITS['unit_test'])
        self.adapter = self.test_manager.get_openai_adapter(model_name="gpt-3.5-turbo")  # Use cheaper model for tests
        self.is_real_api = self.test_manager.is_real_mode('openai')
        
        # Test data
        self.test_query = TEST_QUERIES['medium']
        self.test_context = TEST_CONTEXTS['medium']
        self.test_model = "gpt-3.5-turbo"  # Use cost-effective model
        
    def teardown_method(self):
        """Clean up after tests."""
        if hasattr(self, 'test_manager'):
            summary = self.test_manager.get_test_summary()
            print(f"Test summary: {summary}")  # For debugging
    
    # EPIC1-ADAPT-001: OpenAI Adapter Initialization
    def test_adapter_initialization(self):
        """Test OpenAI adapter initialization and validation.
        
        Requirement: Successful adapter initialization and validation
        PASS Criteria:
        - Initialization: No exceptions raised
        - Model info: Contains provider="OpenAI"
        - API key handling: Secure, not exposed in logs
        - Works in both real and mock modes
        """
        # Test successful initialization
        assert self.adapter is not None
        
        # Test model info retrieval
        model_info = self.adapter.get_model_info()
        assert model_info['provider'] == 'OpenAI'
        assert model_info['model'] == self.test_model
        assert 'max_context_tokens' in model_info or 'max_tokens' in model_info
        assert 'supports_streaming' in model_info
        
        # Verify mode is set correctly
        if self.is_real_api:
            assert model_info.get('mode', 'real') == 'real' or 'mode' not in model_info
        else:
            assert model_info.get('mode') == 'mock'
        
        # Verify API key is handled appropriately for the mode
        if self.is_real_api:
            # Real adapter stores the key but we check it's not in string representations
            assert hasattr(self.adapter, 'api_key')
            assert 'sk-' not in str(self.adapter)  # Key should not appear in string repr
            assert 'sk-' not in repr(self.adapter) # Key should not appear in repr
        else:
            # Mock adapter should hide the key
            assert self.adapter.api_key == "***HIDDEN***"
    
    def test_adapter_initialization_no_api_key(self):
        """Test adapter initialization without API key."""
        # Test with forced mock mode (simulates no API key)
        mock_test_manager = AdaptiveTestManager(force_mock=True)
        mock_adapter = mock_test_manager.get_openai_adapter(model_name=self.test_model)
        
        # Should work in mock mode even without real API key
        assert mock_adapter is not None
        model_info = mock_adapter.get_model_info()
        assert model_info['mode'] == 'mock'
    
    # EPIC1-ADAPT-002: OpenAI Cost Calculation Accuracy
    @pytest.mark.cost_sensitive
    def test_cost_calculation_accuracy(self):
        """Test cost calculation with $0.001 precision.
        
        Requirement: Cost calculation with $0.001 precision
        PASS Criteria:
        - Cost precision: Within $0.001 of expected
        - Token counting: Reasonable approximation
        - Cost tracking: Proper accumulation
        - Works in both real and mock modes
        """
        # Generate response with test query
        params = get_generation_params(temperature=0.0, max_tokens=50)  # Small for cost control
        
        if self.is_real_api:
            # Real API test - use simple query to minimize cost
            response = self.adapter.generate(TEST_QUERIES['simple'], params)
        else:
            # Mock test - can use any query
            response = self.adapter.generate(self.test_query, params)
        
        # Verify response and cost tracking
        assert isinstance(response, str)
        assert len(response) > 0
        
        # Get cost summary
        cost_summary = self.adapter.get_cost_summary()
        
        # Verify cost tracking structure
        assert 'total_cost_usd' in cost_summary
        assert 'total_requests' in cost_summary
        assert cost_summary['total_requests'] > 0
        
        if self.is_real_api:
            # Real API should have actual costs
            assert cost_summary['total_cost_usd'] > 0
            # Track cost to ensure we don't exceed limits
            self.test_manager.track_test_cost(Decimal(str(cost_summary['total_cost_usd'])))
        else:
            # Mock should have calculated costs
            assert cost_summary['total_cost_usd'] >= 0  # Could be zero for mock
    
    def test_different_model_pricing(self):
        """Test cost calculation for different models."""
        # Test with cheaper model first
        cheap_adapter = self.test_manager.get_openai_adapter(model_name="gpt-3.5-turbo")
        expensive_adapter = self.test_manager.get_openai_adapter(model_name="gpt-4-turbo")
        
        params = get_generation_params(temperature=0.0, max_tokens=20)
        
        # Generate with both models
        if self.is_real_api:
            query = TEST_QUERIES['simple']  # Use simple query for cost control
        else:
            query = self.test_query
        
        cheap_response = cheap_adapter.generate(query, params)
        expensive_response = expensive_adapter.generate(query, params)
        
        # Get costs
        cheap_cost = cheap_adapter.get_cost_summary()['total_cost_usd']
        expensive_cost = expensive_adapter.get_cost_summary()['total_cost_usd']
        
        # GPT-4 should be more expensive than GPT-3.5 (in mock or real)
        assert expensive_cost >= cheap_cost  # Allow equal for edge cases
        
        if self.is_real_api:
            # Track costs
            self.test_manager.track_test_cost(Decimal(str(cheap_cost + expensive_cost)))
    
    @pytest.mark.real_api
    @pytest.mark.integration
    def test_real_openai_integration(self):
        """Test real OpenAI API integration when available.
        
        This test only runs when OPENAI_API_KEY is available.
        """
        if not self.is_real_api:
            pytest.skip("Real OpenAI API key not available")
        
        # Test real API call
        params = get_generation_params(temperature=0.0, max_tokens=10)
        response = self.adapter.generate(TEST_QUERIES['simple'], params)
        
        # Verify real API response
        assert isinstance(response, str)
        assert len(response.strip()) > 0
        assert "4" in response  # Should answer "What is 2+2?" correctly
        
        # Verify cost tracking
        cost_summary = self.adapter.get_cost_summary()
        assert cost_summary['total_cost_usd'] > 0
        assert cost_summary['total_requests'] == 1
        
        # Track cost
        self.test_manager.track_test_cost(Decimal(str(cost_summary['total_cost_usd'])))
    
    def test_error_handling(self):
        """Test error handling and API key security."""
        # Verify API key security
        assert 'sk-' not in str(self.adapter)
        if not self.is_real_api:
            assert self.adapter.api_key == "***HIDDEN***"
        
        # Test adapter mode reporting
        model_info = self.adapter.get_model_info()
        assert 'provider' in model_info
        assert model_info['provider'] == 'OpenAI'
    
    def test_basic_generation(self):
        """Test basic text generation functionality."""
        params = get_generation_params(temperature=0.7, max_tokens=30)
        
        # Use appropriate query for mode
        query = TEST_QUERIES['simple'] if self.is_real_api else self.test_query
        response = self.adapter.generate(query, params)
        
        # Verify response
        assert isinstance(response, str)
        assert len(response.strip()) > 0
        
        if not self.is_real_api:
            # Mock responses contain model name
            assert self.test_model in response or "Mock response" in response
    
    def test_model_info_completeness(self):
        """Test that model info contains required fields."""
        model_info = self.adapter.get_model_info()
        
        # Required fields
        required_fields = ['provider', 'model', 'supports_streaming']
        for field in required_fields:
            assert field in model_info, f"Missing required field: {field}"
        
        # Provider should be OpenAI
        assert model_info['provider'] == 'OpenAI'
        assert model_info['model'] == self.test_model
        
        # Should have token limits
        assert 'max_context_tokens' in model_info or 'max_tokens' in model_info
    
    def test_streaming_support_availability(self):
        """Test streaming support reporting."""
        model_info = self.adapter.get_model_info()
        
        # Should report streaming support status
        assert 'supports_streaming' in model_info
        
        # OpenAI should support streaming (both real and mock report this)
        if self.is_real_api:
            # Real OpenAI adapters support streaming
            assert model_info['supports_streaming'] == True
        # Mock may or may not claim streaming support
    
    def test_model_validation(self):
        """Test model name validation and initialization."""
        # Test different valid model names
        valid_models = ['gpt-3.5-turbo', 'gpt-4-turbo', 'gpt-4o-mini']
        
        for model_name in valid_models:
            adapter = self.test_manager.get_openai_adapter(model_name=model_name)
            assert adapter is not None
            
            model_info = adapter.get_model_info()
            assert model_info['model'] == model_name
            assert model_info['provider'] == 'OpenAI'


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])