"""
API tests for status and information endpoints.

Tests /status and /components endpoints through the FastAPI application.
"""

from unittest.mock import patch


class TestStatusEndpoint:
    """Test cases for GET /api/v1/status endpoint."""

    def test_status_default(self, client):
        """Test status endpoint with default parameters."""
        response = client.get("/api/v1/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "initialized" in data
        assert "status" in data
        assert isinstance(data["initialized"], bool)
        assert data["status"] in ["healthy", "unhealthy", "not_initialized", "error"]
        
        # Should include performance by default
        if data["initialized"]:
            assert "performance" in data or data["performance"] is None

    def test_status_include_performance(self, client):
        """Test status endpoint with performance metrics included."""
        response = client.get("/api/v1/status", params={"include_performance": "true"})
        
        assert response.status_code == 200
        data = response.json()
        
        if data["initialized"] and data["status"] == "healthy":
            # Performance should be included or None
            assert "performance" in data

    def test_status_exclude_performance(self, client):
        """Test status endpoint with performance metrics excluded."""
        response = client.get("/api/v1/status", params={"include_performance": "false"})
        
        assert response.status_code == 200
        data = response.json()
        
        # Performance should be None or not present
        assert data.get("performance") is None

    def test_status_include_config(self, client):
        """Test status endpoint with configuration included."""
        response = client.get("/api/v1/status", params={"include_config": "true"})
        
        assert response.status_code == 200
        data = response.json()
        
        if data["initialized"] and data["status"] == "healthy":
            # Configuration should be included or None
            assert "configuration" in data

    def test_status_exclude_config(self, client):
        """Test status endpoint with configuration excluded."""
        response = client.get("/api/v1/status", params={"include_config": "false"})
        
        assert response.status_code == 200
        data = response.json()
        
        # Configuration should be None or not present
        assert data.get("configuration") is None

    def test_status_both_includes(self, client):
        """Test status endpoint with both performance and config included."""
        params = {
            "include_performance": "true",
            "include_config": "true"
        }
        response = client.get("/api/v1/status", params=params)
        
        assert response.status_code == 200
        data = response.json()
        
        if data["initialized"] and data["status"] == "healthy":
            assert "performance" in data
            assert "configuration" in data

    def test_status_both_excludes(self, client):
        """Test status endpoint with both performance and config excluded."""
        params = {
            "include_performance": "false",
            "include_config": "false"
        }
        response = client.get("/api/v1/status", params=params)
        
        assert response.status_code == 200
        data = response.json()
        
        # Both should be None or not present
        assert data.get("performance") is None
        assert data.get("configuration") is None

    def test_status_healthy_response(self, client):
        """Test status endpoint when service is healthy."""
        response = client.get("/api/v1/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Assuming service is properly initialized in tests
        if data["status"] == "healthy":
            assert data["initialized"] is True
            assert "analyzer_type" in data
            assert data["analyzer_type"] == "Epic1QueryAnalyzer"
            assert "components" in data
            
            # Components should show health status
            components = data["components"]
            expected_components = ["feature_extractor", "complexity_classifier", "model_recommender"]
            for component in expected_components:
                if component in components:
                    assert components[component] in ["healthy", "unhealthy", "unknown"]

    def test_status_performance_metrics(self, client):
        """Test status endpoint performance metrics structure."""
        response = client.get("/api/v1/status", params={"include_performance": "true"})
        
        assert response.status_code == 200
        data = response.json()
        
        if data.get("performance"):
            performance = data["performance"]
            
            # Should have timing information
            if "average_times" in performance:
                avg_times = performance["average_times"]
                assert isinstance(avg_times, dict)
                
                # Common timing phases
                expected_phases = ["feature_extraction", "complexity_classification", "model_recommendation", "total"]
                for phase in expected_phases:
                    if phase in avg_times:
                        assert isinstance(avg_times[phase], (int, float))
                        assert avg_times[phase] >= 0
            
            if "total_analyses" in performance:
                assert isinstance(performance["total_analyses"], int)
                assert performance["total_analyses"] >= 0

    def test_status_configuration_structure(self, client):
        """Test status endpoint configuration structure."""
        response = client.get("/api/v1/status", params={"include_config": "true"})
        
        assert response.status_code == 200
        data = response.json()
        
        if data.get("configuration"):
            config = data["configuration"]
            assert isinstance(config, dict)
            
            # Should have key configuration elements
            expected_config_keys = ["strategy", "feature_extraction_enabled", "complexity_classification_enabled", "model_recommendation_enabled"]
            for key in expected_config_keys:
                if key in config:
                    if key == "strategy":
                        assert config[key] in ["cost_optimized", "balanced", "quality_first", None]
                    else:
                        assert isinstance(config[key], bool)

    def test_status_invalid_boolean_params(self, client):
        """Test status endpoint with invalid boolean parameters."""
        response = client.get("/api/v1/status", params={"include_performance": "invalid"})
        
        # FastAPI should handle boolean conversion
        assert response.status_code in [200, 422]

    def test_status_response_headers(self, client):
        """Test status endpoint response headers."""
        response = client.get("/api/v1/status")
        
        assert response.status_code == 200
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]

    @patch('app.core.analyzer.QueryAnalyzerService.get_analyzer_status')
    def test_status_service_error(self, mock_get_status, client):
        """Test status endpoint when service returns error."""
        mock_get_status.side_effect = RuntimeError("Status retrieval failed")
        
        response = client.get("/api/v1/status")
        
        assert response.status_code == 500
        error_data = response.json()
        assert "Status retrieval failed" in str(error_data)

    def test_status_multiple_requests(self, client):
        """Test multiple status requests for consistency."""
        responses = []
        for _ in range(3):
            response = client.get("/api/v1/status")
            assert response.status_code == 200
            responses.append(response.json())
        
        # Status should be consistent across requests
        statuses = [r["status"] for r in responses]
        initialized_flags = [r["initialized"] for r in responses]
        
        assert len(set(statuses)) == 1  # All should be the same
        assert len(set(initialized_flags)) == 1  # All should be the same


class TestComponentsEndpoint:
    """Test cases for GET /api/v1/components endpoint."""

    def test_components_basic(self, client):
        """Test components endpoint basic functionality."""
        response = client.get("/api/v1/components")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "service_info" in data
        assert "components" in data
        
        # Service info structure
        service_info = data["service_info"]
        assert "name" in service_info
        assert "version" in service_info
        assert "analyzer_type" in service_info
        assert "initialized" in service_info
        
        assert service_info["name"] == "query-analyzer"
        assert service_info["version"] == "1.0.0"
        assert isinstance(service_info["initialized"], bool)

    def test_components_structure(self, client):
        """Test components endpoint component structure."""
        response = client.get("/api/v1/components")
        
        assert response.status_code == 200
        data = response.json()
        
        components = data["components"]
        expected_components = ["feature_extractor", "complexity_classifier", "model_recommender"]
        
        for component_name in expected_components:
            if component_name in components:
                component = components[component_name]
                
                # Each component should have required fields
                assert "status" in component
                assert "description" in component
                assert "capabilities" in component
                
                # Validate field types
                assert component["status"] in ["healthy", "unhealthy", "unknown"]
                assert isinstance(component["description"], str)
                assert isinstance(component["capabilities"], list)
                assert len(component["capabilities"]) > 0

    def test_components_feature_extractor_info(self, client):
        """Test feature extractor component information."""
        response = client.get("/api/v1/components")
        
        assert response.status_code == 200
        data = response.json()
        
        if "feature_extractor" in data["components"]:
            fe = data["components"]["feature_extractor"]
            
            # Should have meaningful description and capabilities
            assert "feature" in fe["description"].lower() or "extract" in fe["description"].lower()
            
            capabilities = fe["capabilities"]
            expected_capabilities = ["linguistic", "structural", "semantic", "caching"]
            
            # Should have some of these capabilities mentioned
            capabilities_text = " ".join(capabilities).lower()
            has_expected = any(cap in capabilities_text for cap in expected_capabilities)
            assert has_expected

    def test_components_complexity_classifier_info(self, client):
        """Test complexity classifier component information."""
        response = client.get("/api/v1/components")
        
        assert response.status_code == 200
        data = response.json()
        
        if "complexity_classifier" in data["components"]:
            cc = data["components"]["complexity_classifier"]
            
            # Should have meaningful description and capabilities
            assert "complexity" in cc["description"].lower() or "classif" in cc["description"].lower()
            
            capabilities = cc["capabilities"]
            expected_capabilities = ["threshold", "confidence", "classification", "scoring"]
            
            # Should mention some classification concepts
            capabilities_text = " ".join(capabilities).lower()
            has_expected = any(cap in capabilities_text for cap in expected_capabilities)
            assert has_expected

    def test_components_model_recommender_info(self, client):
        """Test model recommender component information."""
        response = client.get("/api/v1/components")
        
        assert response.status_code == 200
        data = response.json()
        
        if "model_recommender" in data["components"]:
            mr = data["components"]["model_recommender"]
            
            # Should have meaningful description and capabilities
            assert "model" in mr["description"].lower() or "recommend" in mr["description"].lower()
            
            capabilities = mr["capabilities"]
            expected_capabilities = ["routing", "cost", "strategy", "fallback", "openai", "ollama"]
            
            # Should mention some model recommendation concepts
            capabilities_text = " ".join(capabilities).lower()
            has_expected = any(cap in capabilities_text for cap in expected_capabilities)
            assert has_expected

    def test_components_performance_info(self, client):
        """Test components endpoint includes performance information."""
        response = client.get("/api/v1/components")
        
        assert response.status_code == 200
        data = response.json()
        
        # May include performance information
        if "performance" in data:
            performance = data["performance"]
            assert isinstance(performance, dict)

    def test_components_configuration_info(self, client):
        """Test components endpoint includes configuration information."""
        response = client.get("/api/v1/components")
        
        assert response.status_code == 200
        data = response.json()
        
        # May include configuration information
        if "configuration" in data:
            configuration = data["configuration"]
            assert isinstance(configuration, dict)

    def test_components_when_uninitialized(self, client):
        """Test components endpoint when service is not initialized."""
        # This test would need the service to be in an uninitialized state
        # which might be difficult to achieve in the test environment
        response = client.get("/api/v1/components")
        
        # Should still return valid response structure
        assert response.status_code == 200
        data = response.json()
        
        # Service info should indicate not initialized
        service_info = data["service_info"]
        if not service_info["initialized"]:
            # Components may have unknown status
            components = data["components"]
            for component in components.values():
                assert component["status"] in ["healthy", "unhealthy", "unknown"]

    @patch('app.core.analyzer.QueryAnalyzerService.get_analyzer_status')
    def test_components_service_error(self, mock_get_status, client):
        """Test components endpoint when service returns error."""
        mock_get_status.side_effect = RuntimeError("Component info failed")
        
        response = client.get("/api/v1/components")
        
        assert response.status_code == 500
        error_data = response.json()
        assert "Component info failed" in str(error_data)

    def test_components_response_headers(self, client):
        """Test components endpoint response headers."""
        response = client.get("/api/v1/components")
        
        assert response.status_code == 200
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]

    def test_components_caching_behavior(self, client):
        """Test components endpoint caching behavior."""
        # Make multiple requests
        responses = []
        for _ in range(3):
            response = client.get("/api/v1/components")
            assert response.status_code == 200
            responses.append(response.json())
        
        # Service info should be consistent
        service_infos = [r["service_info"] for r in responses]
        for i in range(1, len(service_infos)):
            assert service_infos[i]["name"] == service_infos[0]["name"]
            assert service_infos[i]["version"] == service_infos[0]["version"]

    def test_components_detailed_capabilities(self, client):
        """Test that components provide detailed capability information."""
        response = client.get("/api/v1/components")
        
        assert response.status_code == 200
        data = response.json()
        
        components = data["components"]
        
        # Each component should have multiple capabilities listed
        for component_name, component_info in components.items():
            capabilities = component_info["capabilities"]
            
            # Should have at least 2 capabilities per component
            assert len(capabilities) >= 2
            
            # Each capability should be descriptive (not just single words)
            for capability in capabilities:
                assert len(capability) > 10  # Should be descriptive sentences

    def test_components_status_consistency(self, client):
        """Test component status consistency."""
        response = client.get("/api/v1/components")
        
        assert response.status_code == 200
        data = response.json()
        
        service_initialized = data["service_info"]["initialized"]
        components = data["components"]
        
        # If service is initialized, components should generally be healthy
        if service_initialized:
            component_statuses = [comp["status"] for comp in components.values()]
            healthy_count = component_statuses.count("healthy")
            
            # Most components should be healthy if service is initialized
            assert healthy_count > 0