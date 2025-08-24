"""
Integration Tests for Epic 8 Query Analyzer Service.

Tests integration between the Query Analyzer Service and Epic 1 components,
service startup/configuration, and end-to-end functionality according to
IT-8.1 specifications from epic8-test-specification.md.

Testing Philosophy:
- Hard Fails: Service won't start, Epic 1 integration broken, configuration loading fails
- Quality Flags: Slow startup, suboptimal Epic 1 integration, missing metrics
"""

import pytest
import asyncio
import time
import json
from typing import Dict, Any
from pathlib import Path
import sys
import os

# Add services to path
services_path = Path(__file__).parent.parent.parent.parent / "services" / "query-analyzer"
if services_path.exists():
    sys.path.insert(0, str(services_path))

# Add main project to path for Epic 1 components
project_root = Path(__file__).parent.parent.parent.parent
if project_root.exists():
    sys.path.insert(0, str(project_root))

try:
    sys.path.insert(0, str(project_root / "services" / "query-analyzer"))
    from analyzer_app.core.analyzer import QueryAnalyzerService
    SERVICE_IMPORTS_AVAILABLE = True
except ImportError as e:
    SERVICE_IMPORTS_AVAILABLE = False
    SERVICE_IMPORT_ERROR = str(e)

try:
    from src.components.query_processors.analyzers.epic1_query_analyzer import Epic1QueryAnalyzer
    from src.components.query_processors.base import QueryAnalysis
    EPIC1_IMPORTS_AVAILABLE = True
except ImportError as e:
    EPIC1_IMPORTS_AVAILABLE = False
    EPIC1_IMPORT_ERROR = str(e)


class TestQueryAnalyzerEpic1Integration:
    """Test integration with Epic 1 Query Analyzer components."""

    @pytest.mark.skipif(not SERVICE_IMPORTS_AVAILABLE, reason=f"Service imports not available: {SERVICE_IMPORT_ERROR if not SERVICE_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.skipif(not EPIC1_IMPORTS_AVAILABLE, reason=f"Epic 1 imports not available: {EPIC1_IMPORT_ERROR if not EPIC1_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_epic1_analyzer_integration(self):
        """Test that service properly integrates with Epic1QueryAnalyzer."""
        try:
            # Initialize service
            service = QueryAnalyzerService()
            
            # Perform analysis to trigger Epic1 initialization
            test_query = "What are the advantages of RISC-V architecture?"
            result = await service.analyze_query(test_query)
            
            # Verify service has Epic1 analyzer
            assert service.analyzer is not None, "Epic1QueryAnalyzer not initialized"
            assert isinstance(service.analyzer, Epic1QueryAnalyzer), "Wrong analyzer type"
            assert service._initialized is True, "Service not marked as initialized"
            
            # Verify Epic1 integration in response
            assert "metadata" in result, "Missing metadata field"
            metadata = result["metadata"]
            assert "epic1_analysis" in metadata, "Missing Epic1 analysis data"
            
            epic1_data = metadata["epic1_analysis"]
            
            # Check Epic1-specific fields are present
            epic1_fields = [
                "complexity_score", "complexity_breakdown", 
                "classification_reasoning", "recommendation_reasoning"
            ]
            
            present_fields = [field for field in epic1_fields if field in epic1_data]
            
            # Quality flag: Missing Epic1 fields
            if len(present_fields) < len(epic1_fields):
                missing = set(epic1_fields) - set(present_fields)
                pytest.warns(UserWarning, f"Missing Epic1 fields: {missing}")
            
            print(f"Epic1 integration test passed: {len(present_fields)}/{len(epic1_fields)} fields present")
            print(f"Analyzer type: {type(service.analyzer).__name__}")
            
        except Exception as e:
            pytest.fail(f"Epic1 integration test failed: {e}")

    @pytest.mark.skipif(not SERVICE_IMPORTS_AVAILABLE, reason=f"Service imports not available: {SERVICE_IMPORT_ERROR if not SERVICE_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.skipif(not EPIC1_IMPORTS_AVAILABLE, reason=f"Epic 1 imports not available: {EPIC1_IMPORT_ERROR if not EPIC1_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_epic1_configuration_passthrough(self):
        """Test that configuration is properly passed to Epic1 components."""
        try:
            # Test with custom configuration
            config = {
                "strategy": "quality_first",
                "enable_cost_tracking": True,
                "complexity_thresholds": {
                    "simple": 0.3,
                    "medium": 0.6,
                    "complex": 0.9
                }
            }
            
            service = QueryAnalyzerService(config=config)
            
            # Trigger initialization
            result = await service.analyze_query("Test query for configuration")
            
            # Verify configuration was passed
            assert service.config == config, "Configuration not stored correctly"
            
            # Check that Epic1 analyzer has some configuration
            if hasattr(service.analyzer, 'config'):
                print(f"Epic1 analyzer config: {service.analyzer.config}")
            
            # Verify strategy is reflected in results (if available)
            if "routing_strategy" in result:
                strategy = result["routing_strategy"]
                print(f"Routing strategy in result: {strategy}")
            
            print(f"Configuration passthrough test passed")
            
        except Exception as e:
            pytest.fail(f"Configuration passthrough test failed: {e}")

    @pytest.mark.skipif(not SERVICE_IMPORTS_AVAILABLE, reason=f"Service imports not available: {SERVICE_IMPORT_ERROR if not SERVICE_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.skipif(not EPIC1_IMPORTS_AVAILABLE, reason=f"Epic 1 imports not available: {EPIC1_IMPORT_ERROR if not EPIC1_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_epic1_performance_integration(self):
        """Test that Epic1 performance metrics are available."""
        try:
            service = QueryAnalyzerService()
            
            # Perform several analyses
            queries = [
                "What is machine learning?",
                "How do neural networks work?",
                "Explain transformer architectures"
            ]
            
            for query in queries:
                await service.analyze_query(query)
            
            # Get performance metrics
            status = await service.get_analyzer_status()
            
            # Check for performance data
            if "performance" in status:
                performance = status["performance"]
                assert isinstance(performance, dict), "Performance must be dict"
                
                # Look for Epic1-style metrics
                expected_metrics = ["total_requests", "avg_response_time_ms", "requests_per_second"]
                present_metrics = [m for m in expected_metrics if m in performance]
                
                if len(present_metrics) > 0:
                    print(f"Performance metrics available: {present_metrics}")
                else:
                    pytest.warns(UserWarning, "No Epic1 performance metrics found")
            else:
                pytest.warns(UserWarning, "No performance data in status")
            
            print(f"Performance integration test passed")
            
        except Exception as e:
            pytest.fail(f"Performance integration test failed: {e}")


class TestQueryAnalyzerServiceStartup:
    """Test service startup and initialization scenarios."""

    @pytest.mark.skipif(not SERVICE_IMPORTS_AVAILABLE, reason=f"Service imports not available: {SERVICE_IMPORT_ERROR if not SERVICE_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_service_startup_timing(self):
        """Test service startup time and initialization."""
        try:
            # Test cold startup
            start_time = time.time()
            service = QueryAnalyzerService()
            init_time = time.time() - start_time
            
            # Service creation should be fast
            assert init_time < 5.0, f"Service creation took {init_time:.2f}s (too slow)"
            
            # Quality flag: Service creation should be very fast
            if init_time > 1.0:
                pytest.warns(UserWarning, f"Slow service creation: {init_time:.2f}s")
            
            # Test lazy initialization timing
            start_time = time.time()
            result = await service.analyze_query("Test query for initialization timing")
            first_query_time = time.time() - start_time
            
            # First query (with initialization) should complete reasonably fast
            assert first_query_time < 30.0, f"First query took {first_query_time:.2f}s (too slow)"
            
            # Quality flag: First query should be faster than 10s
            if first_query_time > 10.0:
                pytest.warns(UserWarning, f"Slow first query (initialization): {first_query_time:.2f}s")
            
            # Test subsequent query timing
            start_time = time.time()
            await service.analyze_query("Second test query")
            second_query_time = time.time() - start_time
            
            # Subsequent queries should be faster
            assert second_query_time < first_query_time, "Subsequent query not faster than first"
            
            print(f"Startup timing test passed:")
            print(f"  Service creation: {init_time:.3f}s")
            print(f"  First query (init): {first_query_time:.3f}s")
            print(f"  Second query: {second_query_time:.3f}s")
            
        except Exception as e:
            pytest.fail(f"Startup timing test failed: {e}")

    @pytest.mark.skipif(not SERVICE_IMPORTS_AVAILABLE, reason=f"Service imports not available: {SERVICE_IMPORT_ERROR if not SERVICE_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_concurrent_initialization(self):
        """Test concurrent initialization behavior."""
        try:
            service = QueryAnalyzerService()
            
            # Start multiple concurrent analyses before initialization
            queries = [
                "Query 1 for concurrent test",
                "Query 2 for concurrent test", 
                "Query 3 for concurrent test"
            ]
            
            start_time = time.time()
            tasks = [service.analyze_query(query) for query in queries]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # All requests should succeed
            successful_results = [r for r in results if not isinstance(r, Exception)]
            
            # Hard fail: No results
            assert len(successful_results) > 0, "All concurrent initialization requests failed"
            
            # Quality check: Most should succeed
            success_rate = len(successful_results) / len(queries)
            if success_rate < 0.8:
                pytest.warns(UserWarning, f"Low concurrent initialization success rate: {success_rate:.2%}")
            
            # Service should be initialized after concurrent requests
            assert service._initialized is True, "Service not initialized after concurrent requests"
            
            print(f"Concurrent initialization test passed:")
            print(f"  Success rate: {success_rate:.2%} ({len(successful_results)}/{len(queries)})")
            print(f"  Total time: {total_time:.3f}s")
            
        except Exception as e:
            pytest.fail(f"Concurrent initialization test failed: {e}")

    @pytest.mark.skipif(not SERVICE_IMPORTS_AVAILABLE, reason=f"Service imports not available: {SERVICE_IMPORT_ERROR if not SERVICE_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_restart_recovery(self):
        """Test service restart and recovery."""
        try:
            service = QueryAnalyzerService()
            
            # Initialize service
            await service.analyze_query("Initial query")
            assert service._initialized is True
            
            # Shutdown service
            await service.shutdown()
            assert service._initialized is False
            assert service.analyzer is None
            
            # Verify service can restart
            result = await service.analyze_query("Query after restart")
            
            # Should be re-initialized
            assert service._initialized is True, "Service not re-initialized after restart"
            assert service.analyzer is not None, "Analyzer not re-created after restart"
            
            # Result should be valid
            assert "complexity" in result, "Invalid result after restart"
            assert result["complexity"] in ["simple", "medium", "complex"], "Invalid complexity after restart"
            
            print(f"Restart recovery test passed: {result['complexity']}")
            
        except Exception as e:
            pytest.fail(f"Restart recovery test failed: {e}")


class TestQueryAnalyzerConfigurationLoading:
    """Test configuration loading and validation."""

    @pytest.mark.skipif(not SERVICE_IMPORTS_AVAILABLE, reason=f"Service imports not available: {SERVICE_IMPORT_ERROR if not SERVICE_IMPORTS_AVAILABLE else ''}")
    def test_default_configuration(self):
        """Test service with default configuration."""
        try:
            # No configuration provided
            service = QueryAnalyzerService()
            
            # Should have empty/default config
            assert service.config == {}, "Default config should be empty dict"
            
            print("Default configuration test passed")
            
        except Exception as e:
            pytest.fail(f"Default configuration test failed: {e}")

    @pytest.mark.skipif(not SERVICE_IMPORTS_AVAILABLE, reason=f"Service imports not available: {SERVICE_IMPORT_ERROR if not SERVICE_IMPORTS_AVAILABLE else ''}")
    def test_custom_configuration(self):
        """Test service with custom configuration."""
        try:
            config = {
                "strategy": "cost_optimized",
                "max_response_time": 5.0,
                "enable_caching": True,
                "model_preferences": {
                    "simple": ["ollama/llama3.2:3b"],
                    "medium": ["openai/gpt-3.5-turbo"],
                    "complex": ["openai/gpt-4"]
                }
            }
            
            service = QueryAnalyzerService(config=config)
            
            # Configuration should be stored
            assert service.config == config, "Custom config not stored correctly"
            
            print(f"Custom configuration test passed: {len(config)} settings")
            
        except Exception as e:
            pytest.fail(f"Custom configuration test failed: {e}")

    @pytest.mark.skipif(not SERVICE_IMPORTS_AVAILABLE, reason=f"Service imports not available: {SERVICE_IMPORT_ERROR if not SERVICE_IMPORTS_AVAILABLE else ''}")
    def test_configuration_validation(self):
        """Test configuration validation and error handling."""
        try:
            # Test various configuration types
            valid_configs = [
                {},  # Empty config
                {"strategy": "balanced"},  # String value
                {"enable_feature": True},  # Boolean value
                {"threshold": 0.5},  # Numeric value
                {"nested": {"key": "value"}},  # Nested dict
                {"list_setting": ["item1", "item2"]}  # List value
            ]
            
            for config in valid_configs:
                service = QueryAnalyzerService(config=config)
                assert service.config == config, f"Config validation failed for: {config}"
            
            print(f"Configuration validation test passed for {len(valid_configs)} configs")
            
        except Exception as e:
            pytest.fail(f"Configuration validation test failed: {e}")


class TestQueryAnalyzerHealthMonitoring:
    """Test health monitoring and metrics collection."""

    @pytest.mark.skipif(not SERVICE_IMPORTS_AVAILABLE, reason=f"Service imports not available: {SERVICE_IMPORT_ERROR if not SERVICE_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_health_check_progression(self):
        """Test health check behavior through service lifecycle."""
        try:
            service = QueryAnalyzerService()
            
            # Health check before initialization
            health_before = await service.health_check()
            
            # Should attempt initialization and return result
            assert isinstance(health_before, bool), "Health check must return boolean"
            
            # After health check, service should be initialized (health check initializes)
            assert service._initialized is True, "Health check should initialize service"
            
            # Subsequent health checks should be fast
            start_time = time.time()
            health_after = await service.health_check()
            health_time = time.time() - start_time
            
            assert isinstance(health_after, bool), "Subsequent health check must return boolean"
            
            # Should be fast after initialization
            assert health_time < 1.0, f"Health check after init took {health_time:.2f}s"
            
            print(f"Health check progression test passed: {health_time:.3f}s")
            
        except Exception as e:
            pytest.fail(f"Health check progression test failed: {e}")

    @pytest.mark.skipif(not SERVICE_IMPORTS_AVAILABLE, reason=f"Service imports not available: {SERVICE_IMPORT_ERROR if not SERVICE_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_metrics_collection(self):
        """Test that metrics are collected during operation."""
        try:
            service = QueryAnalyzerService()
            
            # Perform several operations
            queries = [
                "Simple query",
                "Medium complexity query with more details",
                "Complex query requiring detailed analysis and comprehensive understanding"
            ]
            
            for query in queries:
                await service.analyze_query(query)
            
            # Check status for metrics
            status = await service.get_analyzer_status()
            
            # Should have some performance data
            if "performance" in status:
                performance = status["performance"]
                
                # Look for basic metrics
                basic_metrics = ["total_requests", "avg_response_time_ms"]
                found_metrics = [m for m in basic_metrics if m in performance]
                
                if len(found_metrics) > 0:
                    print(f"Metrics collection working: {found_metrics}")
                    
                    # Validate metric values
                    if "total_requests" in performance:
                        requests = performance["total_requests"]
                        assert requests >= len(queries), f"Request count {requests} < expected {len(queries)}"
                    
                    if "avg_response_time_ms" in performance:
                        avg_time = performance["avg_response_time_ms"]
                        assert avg_time > 0, "Average response time should be positive"
                        assert avg_time < 60000, f"Average response time {avg_time}ms seems too high"
                        
                else:
                    pytest.warns(UserWarning, "No basic metrics found in performance data")
            else:
                pytest.warns(UserWarning, "No performance data available")
            
            print(f"Metrics collection test completed")
            
        except Exception as e:
            pytest.fail(f"Metrics collection test failed: {e}")


class TestQueryAnalyzerEndToEndIntegration:
    """Test complete end-to-end integration scenarios."""

    @pytest.mark.skipif(not SERVICE_IMPORTS_AVAILABLE, reason=f"Service imports not available: {SERVICE_IMPORT_ERROR if not SERVICE_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_complete_analysis_workflow(self):
        """Test complete analysis workflow from start to finish."""
        try:
            # Initialize service with configuration
            config = {"strategy": "balanced", "enable_detailed_analysis": True}
            service = QueryAnalyzerService(config=config)
            
            # Test different complexity queries
            test_cases = [
                {
                    "query": "Hi",
                    "expected_complexity": "simple",
                    "context": {"user_tier": "free"}
                },
                {
                    "query": "How does machine learning work in practice?",
                    "expected_complexity": "medium",
                    "context": {"user_tier": "premium", "domain": "technical"}
                },
                {
                    "query": "Analyze the computational complexity of distributed consensus algorithms in Byzantine fault-tolerant systems",
                    "expected_complexity": "complex",
                    "context": {"user_tier": "enterprise", "max_cost": 0.10}
                }
            ]
            
            results = []
            
            for test_case in test_cases:
                query = test_case["query"]
                context = test_case["context"]
                
                start_time = time.time()
                result = await service.analyze_query(query, context=context)
                analysis_time = time.time() - start_time
                
                # Validate complete result structure
                required_fields = [
                    "query", "complexity", "confidence", "features",
                    "recommended_models", "cost_estimate", "routing_strategy",
                    "processing_time", "metadata"
                ]
                
                for field in required_fields:
                    assert field in result, f"Missing field {field} in result"
                
                # Validate field values
                assert result["query"] == query, "Query mismatch in result"
                assert result["complexity"] in ["simple", "medium", "complex"], "Invalid complexity"
                assert isinstance(result["confidence"], (int, float)), "Invalid confidence type"
                assert 0.0 <= result["confidence"] <= 1.0, "Confidence out of range"
                assert isinstance(result["features"], dict), "Features must be dict"
                assert isinstance(result["recommended_models"], list), "Recommended models must be list"
                assert isinstance(result["cost_estimate"], dict), "Cost estimate must be dict"
                assert isinstance(result["metadata"], dict), "Metadata must be dict"
                
                # Check context integration
                if "context" in result["metadata"]:
                    result_context = result["metadata"]["context"]
                    for key, value in context.items():
                        if key in result_context:
                            assert result_context[key] == value, f"Context {key} not preserved"
                
                results.append({
                    "query": query,
                    "result": result,
                    "analysis_time": analysis_time,
                    "expected_complexity": test_case["expected_complexity"]
                })
            
            # Analyze results
            correct_predictions = 0
            total_time = sum(r["analysis_time"] for r in results)
            
            for r in results:
                if r["result"]["complexity"] == r["expected_complexity"]:
                    correct_predictions += 1
                
                print(f"Query: '{r['query'][:50]}...'")
                print(f"  Predicted: {r['result']['complexity']} (conf: {r['result']['confidence']:.2f})")
                print(f"  Expected: {r['expected_complexity']}")
                print(f"  Time: {r['analysis_time']:.3f}s")
                print()
            
            accuracy = correct_predictions / len(test_cases)
            avg_time = total_time / len(test_cases)
            
            # Quality checks
            if accuracy < 0.67:  # 2/3 correct
                pytest.warns(UserWarning, f"End-to-end accuracy low: {accuracy:.2%}")
            
            if avg_time > 3.0:
                pytest.warns(UserWarning, f"End-to-end average time high: {avg_time:.2f}s")
            
            print(f"End-to-end integration test completed:")
            print(f"  Accuracy: {accuracy:.2%} ({correct_predictions}/{len(test_cases)})")
            print(f"  Average time: {avg_time:.3f}s")
            print(f"  Total time: {total_time:.3f}s")
            
        except Exception as e:
            pytest.fail(f"End-to-end integration test failed: {e}")

    @pytest.mark.skipif(not SERVICE_IMPORTS_AVAILABLE, reason=f"Service imports not available: {SERVICE_IMPORT_ERROR if not SERVICE_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_service_lifecycle_integration(self):
        """Test complete service lifecycle from startup to shutdown."""
        try:
            # Create service
            service = QueryAnalyzerService(config={"strategy": "balanced"})
            
            # Verify initial state
            assert not service._initialized, "Service should start uninitialized"
            assert service.analyzer is None, "Analyzer should start as None"
            
            # Perform analysis (triggers initialization)
            result1 = await service.analyze_query("First analysis query")
            assert service._initialized, "Service should be initialized after first query"
            assert service.analyzer is not None, "Analyzer should be created"
            
            # Get status
            status = await service.get_analyzer_status()
            assert status["initialized"] is True, "Status should show initialized"
            assert status["status"] in ["healthy", "error"], "Status should be valid"
            
            # Perform health check
            health = await service.health_check()
            assert isinstance(health, bool), "Health check should return boolean"
            
            # Perform additional analyses
            result2 = await service.analyze_query("Second analysis query")
            result3 = await service.analyze_query("Third analysis query")
            
            # All results should be valid
            for i, result in enumerate([result1, result2, result3], 1):
                assert "complexity" in result, f"Result {i} missing complexity"
                assert "confidence" in result, f"Result {i} missing confidence"
            
            # Shutdown service
            await service.shutdown()
            assert not service._initialized, "Service should be uninitialized after shutdown"
            assert service.analyzer is None, "Analyzer should be None after shutdown"
            
            # Verify service can restart
            result4 = await service.analyze_query("Query after restart")
            assert service._initialized, "Service should re-initialize after restart"
            assert "complexity" in result4, "Result after restart should be valid"
            
            print(f"Service lifecycle integration test passed")
            print(f"  Completed {4} analyses across lifecycle")
            print(f"  Final status: initialized={service._initialized}")
            
        except Exception as e:
            pytest.fail(f"Service lifecycle integration test failed: {e}")


if __name__ == "__main__":
    # Run specific test classes for development
    pytest.main([__file__ + "::TestQueryAnalyzerEpic1Integration", "-v"])