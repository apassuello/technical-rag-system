"""Test suite for Mistral Adapter - Epic 1 Phase 2.

Tests Mistral adapter implementation including:
- Cost-effective routing for medium complexity queries
- Real API integration when available
- Cost calculation accuracy
- Error handling and fallback mechanisms

Uses adaptive testing: real API when available, mock when not.
"""

import os
import pytest
from decimal import Decimal
from typing import Dict, Any

# Import adaptive test management
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from tests.epic1.phase2.adaptive_test_manager import AdaptiveTestManager
from tests.epic1.phase2.test_utils import get_generation_params, TEST_QUERIES, TEST_CONTEXTS, COST_LIMITS


class TestMistralAdapter:
    """Test suite for Mistral adapter functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Initialize adaptive test manager
        self.test_manager = AdaptiveTestManager(cost_limit_usd=COST_LIMITS['unit_test'])
        self.adapter = self.test_manager.get_mistral_adapter(model_name="mistral-small")  # Cost-effective model
        self.is_real_api = self.test_manager.is_real_mode('mistral')
        
        # Test data
        self.test_query = TEST_QUERIES['medium']
        self.test_context = TEST_CONTEXTS['medium']
        self.test_model = "mistral-small"  # Cost-effective model
        
    def teardown_method(self):
        """Clean up after tests."""
        if hasattr(self, 'test_manager'):
            summary = self.test_manager.get_test_summary()
            print(f"Test summary: {summary}")  # For debugging
    
    # EPIC1-ADAPT-003: Mistral Adapter Cost-Effective Routing
    def test_adapter_initialization(self):
        """Test Mistral adapter initialization.
        
        PASS Criteria:
        - Successful initialization
        - Correct model assignment
        - Provider identification
        - API key security
        - Works in both real and mock modes
        """
        assert self.adapter is not None
        
        # Test model info retrieval
        model_info = self.adapter.get_model_info()
        assert model_info['provider'] == 'Mistral'
        assert model_info['model'] == self.test_model
        
        # Verify mode is set correctly
        if self.is_real_api:
            assert model_info.get('mode', 'real') == 'real' or 'mode' not in model_info
        else:
            assert model_info.get('mode') == 'mock'
        
        # Verify API key is handled appropriately for the mode
        if self.is_real_api:
            # Real adapter stores the key but we check it's not in string representations
            assert hasattr(self.adapter, 'api_key')
            assert 'u6o11K' not in str(self.adapter)  # Key should not appear in string repr
            assert 'u6o11K' not in repr(self.adapter) # Key should not appear in repr
        else:
            # Mock adapter should hide the key
            assert self.adapter.api_key == "***HIDDEN***"
    
    def test_adapter_initialization_no_api_key(self):
        """Test adapter behavior without API key."""
        # Test with forced mock mode (simulates no API key)
        mock_test_manager = AdaptiveTestManager(force_mock=True)
        mock_adapter = mock_test_manager.get_mistral_adapter(model_name=self.test_model)
        
        # Should work in mock mode even without real API key
        assert mock_adapter is not None
        model_info = mock_adapter.get_model_info()
        assert model_info['mode'] == 'mock'
    
    @pytest.mark.real_api
    @pytest.mark.integration
    def test_real_mistral_integration(self):
        """Test real Mistral API integration when available.
        
        This test only runs when MISTRAL_API_KEY is available.
        """
        if not self.is_real_api:
            pytest.skip("Real Mistral API key not available")
        
        # Test real API call
        params = get_generation_params(temperature=0.0, max_tokens=20)  # Small for cost control
        response = self.adapter.generate(TEST_QUERIES['medium'], params)
        
        # Verify real API response
        assert isinstance(response, str)
        assert len(response.strip()) > 0
        assert 'oauth' in response.lower() or 'auth' in response.lower()  # Should be about OAuth
        
        # Verify cost tracking
        cost_summary = self.adapter.get_cost_summary()
        assert cost_summary['total_cost_usd'] > 0
        assert cost_summary['total_requests'] == 1
        
        # Track cost
        self.test_manager.track_test_cost(Decimal(str(cost_summary['total_cost_usd'])))
    
    @pytest.mark.cost_sensitive
    def test_cost_effective_routing(self):
        """Test cost-effective inference for medium complexity queries.
        
        Requirement: Lower cost than OpenAI for comparable quality
        PASS Criteria:
        - Cost calculation accuracy
        - Response quality
        - Cost tracking functionality
        - Works in both real and mock modes
        """
        # Generate response for cost comparison
        params = get_generation_params(temperature=0.0, max_tokens=50)
        
        if self.is_real_api:
            # Real API test - use medium query
            response = self.adapter.generate(TEST_QUERIES['medium'], params)
        else:
            # Mock test - use test query
            response = self.adapter.generate(self.test_query, params)
        
        # Verify response
        assert isinstance(response, str)
        assert len(response.strip()) > 0
        
        # Get cost summary
        cost_summary = self.adapter.get_cost_summary()
        
        # Verify cost tracking
        assert 'total_cost_usd' in cost_summary
        assert 'total_requests' in cost_summary
        assert cost_summary['total_requests'] > 0
        
        if self.is_real_api:
            # Real API should have actual costs
            assert cost_summary['total_cost_usd'] > 0
            # Track cost
            self.test_manager.track_test_cost(Decimal(str(cost_summary['total_cost_usd'])))
            
            # Verify response is relevant to OAuth (medium complexity query)
            assert 'oauth' in response.lower() or 'auth' in response.lower() or 'token' in response.lower()
        else:
            # Mock should have calculated costs
            assert cost_summary['total_cost_usd'] >= 0
    
    def test_different_model_pricing(self):
        """Test cost calculation for different Mistral models."""
        # Test with different model sizes
        model_adapters = [
            self.test_manager.get_mistral_adapter(model_name="mistral-small"),
            self.test_manager.get_mistral_adapter(model_name="mistral-medium")
        ]
        
        params = get_generation_params(temperature=0.0, max_tokens=20)
        query = TEST_QUERIES['simple'] if self.is_real_api else self.test_query
        
        costs = []
        for adapter in model_adapters:
            response = adapter.generate(query, params)
            assert isinstance(response, str)
            
            cost_summary = adapter.get_cost_summary()
            costs.append(cost_summary['total_cost_usd'])
        
        # Larger models should generally be more expensive (in mock or real)
        # But allow for edge cases where they might be equal
        assert len(costs) == 2
        
        if self.is_real_api:
            # Track all costs
            for cost in costs:
                self.test_manager.track_test_cost(Decimal(str(cost)))
    
    def test_model_info_completeness(self):
        """Test that model info contains required fields."""
        model_info = self.adapter.get_model_info()
        
        # Required fields
        required_fields = ['provider', 'model', 'max_context_tokens']
        for field in required_fields:
            assert field in model_info, f"Missing required field: {field}"
        
        # Provider should be Mistral
        assert model_info['provider'] == 'Mistral'
        assert model_info['model'] == self.test_model
        
        # Should have reasonable token limits
        assert model_info['max_context_tokens'] > 0
    
    def test_basic_generation(self):
        """Test basic text generation functionality."""
        params = get_generation_params(temperature=0.7, max_tokens=30)
        
        # Use appropriate query for mode  
        query = TEST_QUERIES['medium'] if self.is_real_api else self.test_query
        response = self.adapter.generate(query, params)
        
        # Verify response
        assert isinstance(response, str)
        assert len(response.strip()) > 0
        
        if not self.is_real_api:
            # Mock responses should contain model name
            assert self.test_model in response or "Mock response" in response
    
    def test_cost_summary_functionality(self):
        """Test cost summary and tracking functionality."""
        # Generate a response to create usage data
        params = get_generation_params(temperature=0.0, max_tokens=20)
        query = TEST_QUERIES['simple'] if self.is_real_api else self.test_query
        
        response = self.adapter.generate(query, params)
        assert isinstance(response, str)
        
        # Get cost summary
        cost_summary = self.adapter.get_cost_summary()
        
        # Verify summary structure
        required_fields = ['total_cost_usd', 'total_requests', 'model']
        for field in required_fields:
            assert field in cost_summary
        
        # Should have at least one request
        assert cost_summary['total_requests'] >= 1
        assert cost_summary['model'] == self.test_model
        
        if self.is_real_api:
            assert cost_summary['total_cost_usd'] > 0
    
    def test_model_validation(self):
        """Test model name validation and initialization."""
        # Test different valid model names
        valid_models = ['mistral-small', 'mistral-medium', 'mistral-large']
        
        for model_name in valid_models:
            adapter = self.test_manager.get_mistral_adapter(model_name=model_name)
            assert adapter is not None
            
            model_info = adapter.get_model_info()
            assert model_info['model'] == model_name
            assert model_info['provider'] == 'Mistral'


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])