"""
Unit tests for Pydantic schemas.

Tests request and response models for validation, serialization,
and error handling.
"""

import pytest
from typing import Dict, Any
from pydantic import ValidationError

from analyzer_app.schemas.requests import AnalyzeRequest, StatusRequest
from analyzer_app.schemas.responses import (
    AnalyzeResponse,
    StatusResponse,
    HealthResponse,
    ErrorResponse
)


class TestAnalyzeRequest:
    """Test cases for AnalyzeRequest schema."""

    def test_valid_request(self):
        """Test valid analyze request."""
        request = AnalyzeRequest(
            query="What is machine learning?",
            context={"user_id": "123", "session": "abc"},
            options={"include_features": True}
        )
        
        assert request.query == "What is machine learning?"
        assert request.context == {"user_id": "123", "session": "abc"}
        assert request.options == {"include_features": True}

    def test_minimal_request(self):
        """Test minimal valid request with only required fields."""
        request = AnalyzeRequest(query="Hello world")
        
        assert request.query == "Hello world"
        assert request.context is None
        assert request.options == {}

    def test_query_validation_empty(self):
        """Test query validation with empty string."""
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeRequest(query="")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "Query cannot be empty" in str(errors[0]["msg"])

    def test_query_validation_whitespace_only(self):
        """Test query validation with whitespace only."""
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeRequest(query="   \n\t   ")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "Query cannot be empty" in str(errors[0]["msg"])

    def test_query_validation_too_long(self):
        """Test query validation with too long string."""
        long_query = "x" * 10001  # Exceeds max_length=10000
        
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeRequest(query=long_query)
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "ensure this value has at most 10000 characters" in str(errors[0]["msg"])

    def test_query_whitespace_trimming(self):
        """Test that query whitespace is trimmed."""
        request = AnalyzeRequest(query="  What is Python?  ")
        assert request.query == "What is Python?"

    def test_context_validation_valid_dict(self):
        """Test context validation with valid dictionary."""
        context = {"key1": "value1", "key2": 42, "key3": [1, 2, 3]}
        request = AnalyzeRequest(query="test", context=context)
        assert request.context == context

    def test_context_validation_invalid_type(self):
        """Test context validation with invalid type."""
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeRequest(query="test", context="invalid_context")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "Context must be a dictionary" in str(errors[0]["msg"])

    def test_context_validation_none(self):
        """Test context validation with None."""
        request = AnalyzeRequest(query="test", context=None)
        assert request.context is None

    def test_options_validation_valid_dict(self):
        """Test options validation with valid dictionary."""
        options = {"timeout": 30, "include_metadata": True}
        request = AnalyzeRequest(query="test", options=options)
        assert request.options == options

    def test_options_validation_invalid_type(self):
        """Test options validation with invalid type."""
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeRequest(query="test", options="invalid_options")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "Options must be a dictionary" in str(errors[0]["msg"])

    def test_options_validation_none(self):
        """Test options validation with None."""
        request = AnalyzeRequest(query="test", options=None)
        assert request.options == {}

    def test_json_serialization(self):
        """Test JSON serialization."""
        request = AnalyzeRequest(
            query="test query",
            context={"user": "test"},
            options={"flag": True}
        )
        
        json_data = request.json()
        assert '"query":"test query"' in json_data
        assert '"context":{"user":"test"}' in json_data
        assert '"options":{"flag":true}' in json_data

    def test_dict_conversion(self):
        """Test dictionary conversion."""
        request = AnalyzeRequest(
            query="test query",
            context={"user": "test"}
        )
        
        dict_data = request.dict()
        expected = {
            "query": "test query",
            "context": {"user": "test"},
            "options": {}
        }
        assert dict_data == expected


class TestStatusRequest:
    """Test cases for StatusRequest schema."""

    def test_default_values(self):
        """Test default values for status request."""
        request = StatusRequest()
        
        assert request.include_performance is True
        assert request.include_config is False

    def test_custom_values(self):
        """Test custom values for status request."""
        request = StatusRequest(
            include_performance=False,
            include_config=True
        )
        
        assert request.include_performance is False
        assert request.include_config is True

    def test_boolean_validation(self):
        """Test boolean field validation."""
        # Valid boolean values
        request1 = StatusRequest(include_performance="true")
        assert request1.include_performance is True
        
        request2 = StatusRequest(include_performance="false")
        assert request2.include_performance is False
        
        request3 = StatusRequest(include_performance=1)
        assert request3.include_performance is True
        
        request4 = StatusRequest(include_performance=0)
        assert request4.include_performance is False


class TestAnalyzeResponse:
    """Test cases for AnalyzeResponse schema."""

    def test_valid_response(self):
        """Test valid analyze response."""
        response = AnalyzeResponse(
            query="What is AI?",
            complexity="medium",
            confidence=0.85,
            features={"length": 10, "vocabulary": 0.6},
            recommended_models=["gpt-3.5-turbo", "llama3.2:3b"],
            cost_estimate={"gpt-3.5-turbo": 0.002, "llama3.2:3b": 0.0},
            routing_strategy="balanced",
            processing_time=0.025,
            metadata={"version": "1.0.0"}
        )
        
        assert response.query == "What is AI?"
        assert response.complexity == "medium"
        assert response.confidence == 0.85
        assert response.features == {"length": 10, "vocabulary": 0.6}
        assert response.recommended_models == ["gpt-3.5-turbo", "llama3.2:3b"]
        assert response.routing_strategy == "balanced"
        assert response.processing_time == 0.025

    def test_minimal_response(self):
        """Test minimal valid response."""
        response = AnalyzeResponse(
            query="test",
            complexity="simple",
            confidence=0.9,
            processing_time=0.01
        )
        
        assert response.query == "test"
        assert response.complexity == "simple"
        assert response.confidence == 0.9
        assert response.processing_time == 0.01
        assert response.features == {}
        assert response.recommended_models == []
        assert response.cost_estimate == {}
        assert response.routing_strategy == "balanced"
        assert response.metadata == {}

    def test_confidence_range_validation(self):
        """Test confidence must be between 0.0 and 1.0."""
        # Valid confidence values
        response1 = AnalyzeResponse(
            query="test", complexity="simple", confidence=0.0, processing_time=0.01
        )
        assert response1.confidence == 0.0
        
        response2 = AnalyzeResponse(
            query="test", complexity="simple", confidence=1.0, processing_time=0.01
        )
        assert response2.confidence == 1.0
        
        # Invalid confidence values
        with pytest.raises(ValidationError):
            AnalyzeResponse(
                query="test", complexity="simple", confidence=-0.1, processing_time=0.01
            )
        
        with pytest.raises(ValidationError):
            AnalyzeResponse(
                query="test", complexity="simple", confidence=1.1, processing_time=0.01
            )

    def test_processing_time_validation(self):
        """Test processing time must be non-negative."""
        # Valid processing time
        response = AnalyzeResponse(
            query="test", complexity="simple", confidence=0.5, processing_time=0.0
        )
        assert response.processing_time == 0.0
        
        # Invalid processing time
        with pytest.raises(ValidationError):
            AnalyzeResponse(
                query="test", complexity="simple", confidence=0.5, processing_time=-0.1
            )

    def test_list_field_defaults(self):
        """Test that list fields default to empty lists."""
        response = AnalyzeResponse(
            query="test", complexity="simple", confidence=0.5, processing_time=0.01
        )
        
        assert isinstance(response.recommended_models, list)
        assert len(response.recommended_models) == 0

    def test_dict_field_defaults(self):
        """Test that dict fields default to empty dicts."""
        response = AnalyzeResponse(
            query="test", complexity="simple", confidence=0.5, processing_time=0.01
        )
        
        assert isinstance(response.features, dict)
        assert isinstance(response.cost_estimate, dict)
        assert isinstance(response.metadata, dict)
        assert len(response.features) == 0
        assert len(response.cost_estimate) == 0
        assert len(response.metadata) == 0


class TestStatusResponse:
    """Test cases for StatusResponse schema."""

    def test_minimal_status_response(self):
        """Test minimal status response."""
        response = StatusResponse(
            initialized=True,
            status="healthy"
        )
        
        assert response.initialized is True
        assert response.status == "healthy"
        assert response.analyzer_type is None
        assert response.configuration is None
        assert response.performance is None
        assert response.components is None
        assert response.error is None

    def test_complete_status_response(self):
        """Test complete status response."""
        response = StatusResponse(
            initialized=True,
            status="healthy",
            analyzer_type="Epic1QueryAnalyzer",
            configuration={"strategy": "balanced"},
            performance={"avg_time": 0.02},
            components={"feature_extractor": "healthy"},
            error=None
        )
        
        assert response.initialized is True
        assert response.status == "healthy"
        assert response.analyzer_type == "Epic1QueryAnalyzer"
        assert response.configuration == {"strategy": "balanced"}
        assert response.performance == {"avg_time": 0.02}
        assert response.components == {"feature_extractor": "healthy"}

    def test_error_status_response(self):
        """Test error status response."""
        response = StatusResponse(
            initialized=False,
            status="error",
            error="Failed to initialize analyzer"
        )
        
        assert response.initialized is False
        assert response.status == "error"
        assert response.error == "Failed to initialize analyzer"


class TestHealthResponse:
    """Test cases for HealthResponse schema."""

    def test_healthy_response(self):
        """Test healthy response."""
        response = HealthResponse(
            status="healthy",
            service="query-analyzer",
            version="1.0.0",
            details={"components": "all_healthy"}
        )
        
        assert response.status == "healthy"
        assert response.service == "query-analyzer"
        assert response.version == "1.0.0"
        assert response.details == {"components": "all_healthy"}

    def test_unhealthy_response(self):
        """Test unhealthy response."""
        response = HealthResponse(
            status="unhealthy",
            service="query-analyzer",
            version="1.0.0"
        )
        
        assert response.status == "unhealthy"
        assert response.details is None

    def test_minimal_health_response(self):
        """Test minimal health response."""
        response = HealthResponse(
            status="healthy",
            service="query-analyzer",
            version="1.0.0"
        )
        
        assert response.status == "healthy"
        assert response.service == "query-analyzer"
        assert response.version == "1.0.0"
        assert response.details is None


class TestErrorResponse:
    """Test cases for ErrorResponse schema."""

    def test_minimal_error_response(self):
        """Test minimal error response."""
        response = ErrorResponse(
            error="ValidationError",
            message="Invalid input provided"
        )
        
        assert response.error == "ValidationError"
        assert response.message == "Invalid input provided"
        assert response.details is None
        assert response.request_id is None

    def test_complete_error_response(self):
        """Test complete error response."""
        response = ErrorResponse(
            error="AnalysisError",
            message="Query analysis failed",
            details={"reason": "Model not available"},
            request_id="abc123"
        )
        
        assert response.error == "AnalysisError"
        assert response.message == "Query analysis failed"
        assert response.details == {"reason": "Model not available"}
        assert response.request_id == "abc123"

    def test_error_details_validation(self):
        """Test error details can be any dictionary."""
        details = {
            "error_code": 500,
            "timestamp": "2023-01-01T00:00:00Z",
            "stack_trace": ["line1", "line2"],
            "nested": {"key": "value"}
        }
        
        response = ErrorResponse(
            error="InternalError",
            message="Internal server error",
            details=details
        )
        
        assert response.details == details


class TestSchemaIntegration:
    """Test cases for schema integration and edge cases."""

    def test_json_serialization_roundtrip(self):
        """Test JSON serialization and deserialization."""
        original = AnalyzeResponse(
            query="test query",
            complexity="medium",
            confidence=0.75,
            features={"key": "value"},
            recommended_models=["model1", "model2"],
            cost_estimate={"model1": 0.01},
            processing_time=0.02,
            metadata={"version": "1.0"}
        )
        
        # Serialize to JSON
        json_str = original.json()
        
        # Deserialize from JSON
        parsed = AnalyzeResponse.parse_raw(json_str)
        
        # Should be equal
        assert parsed.query == original.query
        assert parsed.complexity == original.complexity
        assert parsed.confidence == original.confidence
        assert parsed.features == original.features
        assert parsed.recommended_models == original.recommended_models
        assert parsed.cost_estimate == original.cost_estimate
        assert parsed.processing_time == original.processing_time
        assert parsed.metadata == original.metadata

    def test_schema_with_none_values(self):
        """Test schemas handle None values correctly."""
        request = AnalyzeRequest(query="test", context=None, options=None)
        assert request.context is None
        assert request.options == {}
        
        response = StatusResponse(
            initialized=True,
            status="healthy",
            analyzer_type=None,
            configuration=None
        )
        assert response.analyzer_type is None
        assert response.configuration is None

    def test_extra_fields_ignored(self):
        """Test that extra fields are ignored during parsing."""
        data = {
            "query": "test",
            "context": {"user": "test"},
            "options": {},
            "extra_field": "should_be_ignored"
        }
        
        # Should not raise error
        request = AnalyzeRequest.parse_obj(data)
        assert request.query == "test"
        assert not hasattr(request, 'extra_field')

    def test_field_aliases(self):
        """Test field aliases if any are defined."""
        # This tests future-proofing if field aliases are added
        request = AnalyzeRequest(query="test")
        
        # Should be able to access via standard field names
        assert hasattr(request, 'query')
        assert hasattr(request, 'context')
        assert hasattr(request, 'options')

    def test_validation_error_details(self):
        """Test detailed validation error information."""
        try:
            AnalyzeRequest(query="", context="invalid", options="invalid")
        except ValidationError as e:
            errors = e.errors()
            
            # Should have multiple validation errors
            assert len(errors) >= 2  # At least query and context errors
            
            # Each error should have type, msg, and input fields
            for error in errors:
                assert 'type' in error
                assert 'msg' in error
                assert 'input' in error or 'ctx' in error