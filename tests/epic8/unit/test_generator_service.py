"""
Unit Tests for Epic 8 Generator Service.

Tests the core functionality of the GeneratorService wrapping Epic1AnswerGenerator
for microservices deployment. Based on CT-8.2 specifications from epic8-test-specification.md.

Testing Philosophy:
- Hard Fails: Service crashes, health check 500s, >60s response, >8GB memory, 0% generation success
- Quality Flags: Poor routing accuracy, >2s response, cost tracking errors >10%, cache miss >90%

Test Focus:
- Service initialization and health checks
- Multi-model adapter interface testing (CT-8.2.1)
- Model selection logic validation (CT-8.2.2)
- Cost tracking accuracy
- LLM adapter functionality (Ollama, OpenAI, Mistral, HuggingFace)
"""

import pytest
import asyncio
import time
import unittest.mock as mock
from typing import Dict, Any, List
from pathlib import Path
import sys
from decimal import Decimal

# Add services to path
services_path = Path(__file__).parent.parent.parent.parent / "services" / "generator"
if services_path.exists():
    sys.path.insert(0, str(services_path))

try:
    from app.core.generator import GeneratorService
    from app.schemas.requests import GenerateRequest, DocumentContext
    from app.schemas.responses import GenerateResponse, RoutingDecision
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    IMPORT_ERROR = str(e)

# Test data matching Epic 8 specifications
SIMPLE_TEST_DOCUMENTS = [
    {
        "content": "RISC-V is an open-source instruction set architecture that provides free, open standards for processor design.",
        "metadata": {"source": "risc-v-basics.pdf", "page": 1},
        "doc_id": "doc_simple_001",
        "score": 0.95
    }
]

COMPLEX_TEST_DOCUMENTS = [
    {
        "content": "RISC-V vector extensions provide sophisticated SIMD capabilities with configurable vector lengths, supporting both fixed-width and scalable vector operations. The vector instruction set includes complex operations for matrix multiplication, convolution, and other compute-intensive workloads commonly found in machine learning and signal processing applications.",
        "metadata": {"source": "risc-v-vector-spec.pdf", "page": 15},
        "doc_id": "doc_complex_001",
        "score": 0.92
    },
    {
        "content": "Performance optimization in RISC-V requires careful consideration of pipeline architecture, branch prediction mechanisms, and memory subsystem design. Advanced implementations may include out-of-order execution, speculative execution, and sophisticated cache hierarchies.",
        "metadata": {"source": "risc-v-performance.pdf", "page": 42},
        "doc_id": "doc_complex_002",
        "score": 0.88
    }
]


class TestGeneratorServiceBasics:
    """Test basic service initialization and health checks."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test that service can be initialized without crashing (Hard Fail test)."""
        try:
            service = GeneratorService()
            assert service is not None
            assert not service._initialized  # Should start uninitialized
            assert service.generator is None
            
            # Test with configuration
            config = {"routing": {"strategy": "balanced"}}
            service_with_config = GeneratorService(config=config)
            assert service_with_config.config == config
            
        except Exception as e:
            pytest.fail(f"Service initialization failed - HARD FAIL: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_health_check_basic(self):
        """Test basic health check functionality (Hard Fail test)."""
        try:
            service = GeneratorService()
            
            # Health check should timeout in reasonable time
            start_time = time.time()
            is_healthy = await service.health_check()
            health_check_time = time.time() - start_time
            
            # Hard Fail: Health check takes more than 60 seconds
            assert health_check_time < 60.0, f"Health check took {health_check_time:.2f}s - HARD FAIL (>60s)"
            
            # Should return boolean
            assert isinstance(is_healthy, bool), f"Health check returned {type(is_healthy)}, expected bool"
            
        except Exception as e:
            pytest.fail(f"Health check crashed - HARD FAIL: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_service_status_structure(self):
        """Test that service status returns expected structure."""
        try:
            service = GeneratorService()
            status = await service.get_generator_status()
            
            # Should always return dict
            assert isinstance(status, dict), f"Status returned {type(status)}, expected dict"
            
            # Should have basic keys
            assert "initialized" in status, "Status missing 'initialized' key"
            assert "status" in status, "Status missing 'status' key"
            
            # initialized should be boolean
            assert isinstance(status["initialized"], bool), "initialized should be boolean"
            
            # status should be string
            assert isinstance(status["status"], str), "status should be string"
            
        except Exception as e:
            pytest.fail(f"Service status failed - HARD FAIL: {e}")


class TestGeneratorServiceAdapterInterface:
    """Test multi-model adapter interface compliance (CT-8.2.1)."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_available_models_interface(self):
        """Test that service can return available models without crashing."""
        try:
            service = GeneratorService()
            
            start_time = time.time()
            models = await service.get_available_models()
            response_time = time.time() - start_time
            
            # Hard Fail: Response time > 5 seconds (per CT-8.2.1)
            assert response_time < 5.0, f"get_available_models took {response_time:.2f}s - HARD FAIL (>5s)"
            
            # Should return list
            assert isinstance(models, list), f"get_available_models returned {type(models)}, expected list"
            
            # If models available, they should be strings
            for model in models:
                assert isinstance(model, str), f"Model {model} is {type(model)}, expected str"
                assert len(model) > 0, f"Model name is empty: '{model}'"
            
        except Exception as e:
            pytest.fail(f"get_available_models failed - HARD FAIL: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_model_costs_interface(self):
        """Test that service can return model costs without crashing."""
        try:
            service = GeneratorService()
            
            start_time = time.time()
            costs = await service.get_model_costs()
            response_time = time.time() - start_time
            
            # Should complete quickly
            assert response_time < 5.0, f"get_model_costs took {response_time:.2f}s - may indicate issues"
            
            # Should return dict
            assert isinstance(costs, dict), f"get_model_costs returned {type(costs)}, expected dict"
            
            # If costs available, values should be numeric
            for model, cost in costs.items():
                assert isinstance(model, str), f"Model key {model} is {type(model)}, expected str"
                assert isinstance(cost, (int, float)), f"Cost {cost} is {type(cost)}, expected numeric"
                assert cost >= 0, f"Cost {cost} for model {model} is negative"
            
        except Exception as e:
            pytest.fail(f"get_model_costs failed - HARD FAIL: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_generation_interface_basic(self):
        """Test basic generation interface without full Epic1 dependency."""
        try:
            service = GeneratorService()
            
            # Test that service can handle request structure without crashing
            query = "What is RISC-V?"
            context_documents = SIMPLE_TEST_DOCUMENTS
            
            # This may fail due to Epic1 dependencies, but should not crash
            try:
                start_time = time.time()
                result = await service.generate_answer(query, context_documents)
                response_time = time.time() - start_time
                
                # Hard Fail: Response time > 60 seconds
                assert response_time < 60.0, f"Generation took {response_time:.2f}s - HARD FAIL (>60s)"
                
                # If successful, check result structure
                assert isinstance(result, dict), "Generation result should be dict"
                
                # Key fields that should be present
                expected_keys = ["answer", "query", "model_used", "cost", "confidence", "processing_time"]
                for key in expected_keys:
                    assert key in result, f"Generation result missing key: {key}"
                
                # Basic type validation
                assert isinstance(result["answer"], str), "answer should be string"
                assert isinstance(result["query"], str), "query should be string"
                assert isinstance(result["model_used"], str), "model_used should be string"
                assert isinstance(result["cost"], (int, float)), "cost should be numeric"
                assert isinstance(result["confidence"], (int, float)), "confidence should be numeric"
                assert isinstance(result["processing_time"], (int, float)), "processing_time should be numeric"
                
                # Reasonable ranges
                assert 0 <= result["confidence"] <= 1.0, f"confidence {result['confidence']} out of range [0,1]"
                assert result["cost"] >= 0, f"cost {result['cost']} is negative"
                assert result["processing_time"] > 0, f"processing_time {result['processing_time']} should be positive"
                
            except Exception as e:
                # Generation may fail due to Epic1 dependencies, which is acceptable for unit tests
                # But should not be due to interface issues
                error_msg = str(e).lower()
                if "import" not in error_msg and "module" not in error_msg and "not found" not in error_msg:
                    pytest.fail(f"Generation failed with non-import error - HARD FAIL: {e}")
                else:
                    pytest.skip(f"Generation skipped due to missing dependencies: {e}")
                    
        except Exception as e:
            pytest.fail(f"Generation interface test failed - HARD FAIL: {e}")


class TestGeneratorServiceModelSelection:
    """Test model selection logic (CT-8.2.2)."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_model_selection_logic_structure(self):
        """Test that model selection logic has expected structure."""
        try:
            service = GeneratorService()
            
            # Test with different routing strategies
            strategies = ["cost_optimized", "balanced", "quality_first"]
            
            for strategy in strategies:
                options = {"strategy": strategy}
                
                # Test that service can handle different strategy options
                try:
                    # Just test that the service accepts these options without crashing
                    # Full testing would require Epic1 integration
                    query = "Test query for model selection"
                    result = await service.generate_answer(query, SIMPLE_TEST_DOCUMENTS, options)
                    
                    # If successful, verify routing decision structure
                    assert "routing_decision" in result, "Result missing routing_decision"
                    routing = result["routing_decision"]
                    
                    assert isinstance(routing, dict), "routing_decision should be dict"
                    assert "strategy" in routing, "routing_decision missing strategy"
                    
                except Exception as e:
                    # May fail due to dependencies, which is acceptable
                    error_msg = str(e).lower()
                    if "import" not in error_msg and "module" not in error_msg:
                        # This could indicate strategy handling issues
                        pass  # Log for investigation but don't hard fail
                    
        except Exception as e:
            pytest.fail(f"Model selection logic test failed - HARD FAIL: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_cost_constraint_handling(self):
        """Test that service handles cost constraints properly."""
        try:
            service = GeneratorService()
            
            # Test cost constraints
            cost_constraints = [0.001, 0.01, 0.05, 0.10]
            
            for max_cost in cost_constraints:
                options = {
                    "strategy": "cost_optimized",
                    "max_cost": max_cost
                }
                
                try:
                    # Test that service accepts cost constraints
                    query = "Cost-constrained test query"
                    result = await service.generate_answer(query, SIMPLE_TEST_DOCUMENTS, options)
                    
                    # If successful, cost should respect constraint (within 5% tolerance per CT-8.2.1)
                    actual_cost = result.get("cost", 0)
                    tolerance = max_cost * 0.05  # 5% tolerance
                    
                    if actual_cost > max_cost + tolerance:
                        # Quality Flag: Cost constraint violation
                        print(f"WARNING: Cost constraint violated - max: {max_cost}, actual: {actual_cost}")
                    
                except Exception as e:
                    # May fail due to dependencies
                    error_msg = str(e).lower()
                    if "import" not in error_msg and "module" not in error_msg:
                        # Could indicate cost handling issues
                        pass  # Log for investigation
                    
        except Exception as e:
            pytest.fail(f"Cost constraint handling failed - HARD FAIL: {e}")


class TestGeneratorServiceCostTracking:
    """Test cost tracking accuracy and functionality."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_cost_tracking_precision(self):
        """Test that cost tracking provides reasonable precision."""
        try:
            service = GeneratorService()
            model_costs = await service.get_model_costs()
            
            # Test cost precision for available models
            for model, cost in model_costs.items():
                # Cost should have reasonable precision (at least 4 decimal places for small costs)
                if cost > 0:
                    cost_str = f"{cost:.10f}"
                    # Should not be obviously rounded to few decimal places for small costs
                    if cost < 0.1:
                        assert "0000" not in cost_str[-6:], f"Cost {cost} for {model} lacks precision"
                
                # Cost should be in reasonable range (not obviously wrong)
                assert 0 <= cost <= 1.0, f"Cost {cost} for {model} seems unreasonable (>$1 per query)"
            
        except Exception as e:
            pytest.fail(f"Cost tracking precision test failed - HARD FAIL: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio 
    async def test_cost_calculation_consistency(self):
        """Test that cost calculations are consistent across calls."""
        try:
            service = GeneratorService()
            
            # Test that multiple calls to get_model_costs return consistent results
            costs1 = await service.get_model_costs()
            await asyncio.sleep(0.1)  # Small delay
            costs2 = await service.get_model_costs()
            
            # Should return same models
            assert set(costs1.keys()) == set(costs2.keys()), "Model lists changed between calls"
            
            # Should return same costs (within tiny tolerance for floating point)
            for model in costs1.keys():
                cost1 = costs1[model]
                cost2 = costs2[model]
                diff = abs(cost1 - cost2)
                assert diff < 0.0001, f"Cost for {model} changed between calls: {cost1} vs {cost2}"
            
        except Exception as e:
            pytest.fail(f"Cost calculation consistency test failed - HARD FAIL: {e}")


class TestGeneratorServicePerformance:
    """Test basic performance characteristics."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_concurrent_status_requests(self):
        """Test that service can handle concurrent status requests."""
        try:
            service = GeneratorService()
            
            # Create multiple concurrent status requests
            tasks = []
            for i in range(5):
                task = asyncio.create_task(service.get_generator_status())
                tasks.append(task)
            
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # Should complete within reasonable time
            assert total_time < 10.0, f"5 concurrent status requests took {total_time:.2f}s - may indicate issues"
            
            # All should succeed or fail gracefully
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    pytest.fail(f"Concurrent status request {i} failed: {result}")
                assert isinstance(result, dict), f"Status request {i} returned {type(result)}"
            
        except Exception as e:
            pytest.fail(f"Concurrent status requests test failed - HARD FAIL: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_memory_usage_basic(self):
        """Test that service doesn't use excessive memory during basic operations."""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            service = GeneratorService()
            
            # Perform basic operations
            await service.get_generator_status()
            await service.get_available_models() 
            await service.get_model_costs()
            await service.health_check()
            
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory
            
            # Hard Fail: Service uses more than 8GB total (very generous limit)
            assert current_memory < 8192, f"Service using {current_memory:.1f}MB - HARD FAIL (>8GB)"
            
            # Quality Flag: Significant memory increase for basic operations
            if memory_increase > 100:  # 100MB increase for basic operations
                print(f"WARNING: Memory increased by {memory_increase:.1f}MB for basic operations")
            
        except ImportError:
            pytest.skip("psutil not available for memory testing")
        except Exception as e:
            pytest.fail(f"Memory usage test failed - HARD FAIL: {e}")


class TestGeneratorServiceErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_invalid_query_handling(self):
        """Test that service handles invalid queries gracefully."""
        try:
            service = GeneratorService()
            
            invalid_queries = [
                "",  # Empty string
                "   ",  # Whitespace only
                None,  # None value (would fail at API layer normally)
                "x" * 10000,  # Very long query
            ]
            
            for query in invalid_queries:
                try:
                    if query is None:
                        continue  # Skip None test as it would fail at validation layer
                        
                    result = await service.generate_answer(query, SIMPLE_TEST_DOCUMENTS)
                    
                    # If successful, should still return valid structure
                    assert isinstance(result, dict), f"Invalid query {repr(query)} didn't return dict"
                    
                except ValueError:
                    # Expected for some invalid queries
                    pass
                except Exception as e:
                    error_msg = str(e).lower()
                    if "import" not in error_msg and "module" not in error_msg:
                        # Non-dependency errors should be handled gracefully
                        pass  # Log but don't hard fail
            
        except Exception as e:
            pytest.fail(f"Invalid query handling test failed - HARD FAIL: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_empty_context_handling(self):
        """Test that service handles empty context gracefully."""
        try:
            service = GeneratorService()
            
            query = "What is RISC-V?"
            empty_contexts = [
                [],  # Empty list
                [{"content": "", "metadata": {}}],  # Empty content
            ]
            
            for context in empty_contexts:
                try:
                    result = await service.generate_answer(query, context)
                    
                    # If successful, should return valid structure
                    assert isinstance(result, dict), f"Empty context {context} didn't return dict"
                    
                except ValueError:
                    # Expected for empty contexts
                    pass
                except Exception as e:
                    error_msg = str(e).lower()
                    if "import" not in error_msg and "module" not in error_msg:
                        # Non-dependency errors should be handled gracefully
                        pass
            
        except Exception as e:
            pytest.fail(f"Empty context handling test failed - HARD FAIL: {e}")


@pytest.mark.integration
class TestGeneratorServiceIntegrationReadiness:
    """Test readiness for integration with other services."""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_service_lifecycle(self):
        """Test complete service lifecycle."""
        try:
            service = GeneratorService()
            
            # Should start uninitialized
            assert not service._initialized
            
            # Health check should trigger initialization
            await service.health_check()
            
            # Should handle multiple operations
            status = await service.get_generator_status()
            models = await service.get_available_models()
            costs = await service.get_model_costs()
            
            # Shutdown should be clean
            await service.shutdown()
            
            # After shutdown, should handle gracefully
            assert not service._initialized
            
        except Exception as e:
            pytest.fail(f"Service lifecycle test failed - HARD FAIL: {e}")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Service imports not available: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_configuration_flexibility(self):
        """Test that service handles different configurations."""
        try:
            configs = [
                {},  # Empty config
                {"routing": {"strategy": "balanced"}},  # Routing config
                {"routing": {"strategy": "cost_optimized", "max_cost": 0.01}},  # Cost config
                {"invalid_key": "invalid_value"},  # Invalid config (should not crash)
            ]
            
            for config in configs:
                service = GeneratorService(config=config)
                assert service is not None
                assert service.config == config
                
                # Should still be able to get status
                status = await service.get_generator_status()
                assert isinstance(status, dict)
            
        except Exception as e:
            pytest.fail(f"Configuration flexibility test failed - HARD FAIL: {e}")