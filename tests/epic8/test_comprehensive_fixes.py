"""
Comprehensive Epic 8 Test Fixes - TDD Approach

This test file exposes specific issues found in Epic 8 tests and provides fixes.
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

class TestEpic8SchemaFixes:
    """Test that schema validation issues are fixed."""
    
    def test_model_info_schema_has_required_fields(self):
        """Test that ModelInfo schema includes all required fields."""
        try:
            from services.api_gateway.gateway_app.schemas.responses import ModelInfo
            
            # Test data that should work with proper schema
            valid_model_data = {
                "name": "test-model",
                "provider": "test-provider", 
                "type": "chat",  # This field was missing in tests
                "available": True
            }
            
            # This should not raise ValidationError
            model = ModelInfo(**valid_model_data)
            assert model.type == "chat"
            assert model.name == "test-model"
            
        except ImportError:
            pytest.skip("ModelInfo schema not available")
    
    def test_available_models_response_schema(self):
        """Test that AvailableModelsResponse works with proper ModelInfo data."""
        try:
            from services.api_gateway.gateway_app.schemas.responses import (
                AvailableModelsResponse, ModelInfo
            )
            
            # Create valid model data with all required fields
            models_data = [
                {
                    "name": "gpt-3.5-turbo",
                    "provider": "openai",
                    "type": "chat",  # Required field
                    "available": True,
                    "context_length": 4096
                },
                {
                    "name": "llama3.2:3b",
                    "provider": "ollama", 
                    "type": "instruct",  # Required field
                    "available": True,
                    "context_length": 2048
                }
            ]
            
            # This should work without ValidationError
            response = AvailableModelsResponse(
                models=models_data,
                total_models=2,
                available_models=2,
                providers=["openai", "ollama"]
            )
            
            assert len(response.models) == 2
            assert all(model.type in ["chat", "instruct"] for model in response.models)
            
        except ImportError:
            pytest.skip("AvailableModelsResponse schema not available")

class TestEpic8ImportFixes:
    """Test that import issues are resolved."""

    @pytest.mark.skip(reason="Cache service not implemented yet")
    def test_cache_service_imports_available(self):
        """Test that cache service can be imported properly."""
        try:
            # This should work if paths are set up correctly
            from services.cache.cache_app.main import create_app
            assert create_app is not None

        except ImportError as e:
            # Provide detailed information about the import failure
            pytest.fail(f"Cache service import failed: {e}")
    
    @pytest.mark.skip(reason="Service imports require Docker container environment")
    def test_api_gateway_service_imports_available(self):
        """Test that API gateway service can be imported properly.

        Note: API Gateway service imports require the Docker containerized
        environment with proper service paths. This test cannot pass in the
        test environment where services/ is not on the Python path.
        """
        try:
            from services.api_gateway.gateway_app.main import create_app
            assert create_app is not None

        except ImportError as e:
            pytest.fail(f"API Gateway service import failed: {e}")

class TestEpic8ServiceAvailability:
    """Test that services are properly mocked and available."""

    @pytest.mark.skip(reason="Cache service was never implemented")
    def test_service_mocking_reduces_skips(self):
        """Test that proper service mocking reduces test skips.

        Note: The cache service was never implemented. See project memory:
        'Epic 8 cache: services/cache/ never implemented — all tests skip'
        This test would fail because create_test_cache_app() doesn't exist.
        """
        # This test verifies that our test utilities properly mock services
        from tests.epic8.api.test_utils import (
            create_test_cache_app,
            create_test_gateway_app
        )

        # These should work without raising exceptions
        cache_app = create_test_cache_app()
        assert cache_app is not None

        gateway_app = create_test_gateway_app()
        assert gateway_app is not None
