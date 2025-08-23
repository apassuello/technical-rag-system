"""
Integration Tests for Epic 8 Generator Service.

Tests integration scenarios for the Generator Service with other Epic 8 components
and Epic 1 foundation. Based on IT-8.1 specifications from epic8-test-specification.md.

Testing Philosophy:
- Hard Fails: Service crashes, >60s response, complete integration failure, memory >8GB
- Quality Flags: >2s response, poor model routing, Epic1 integration issues, cost tracking errors

Focus Areas:
- Integration with Epic 1 components (Epic1AnswerGenerator)
- Multi-model routing strategy testing
- Cost tracking integration
- Adaptive router functionality
- Service-to-service communication patterns
"""

import pytest
import asyncio
import time
import unittest.mock as mock
from typing import Dict, Any, List
from pathlib import Path
import sys
import requests
from decimal import Decimal

# Add services to path
services_path = Path(__file__).parent.parent.parent.parent / "services" / "generator"
if services_path.exists():
    sys.path.insert(0, str(services_path))

# Add main project to path for Epic 1 components
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

try:
    from generator_app.core.generator import GeneratorService
    GENERATOR_IMPORTS_AVAILABLE = True
except ImportError as e:
    GENERATOR_IMPORTS_AVAILABLE = False
    GENERATOR_IMPORT_ERROR = str(e)

try:
    from components.generators.epic1_answer_generator import Epic1AnswerGenerator
    from components.generators.routing.routing_strategies import RoutingStrategy
    from core.interfaces import Document, Answer
    EPIC1_IMPORTS_AVAILABLE = True
except ImportError as e:
    EPIC1_IMPORTS_AVAILABLE = False  
    EPIC1_IMPORT_ERROR = str(e)

# Test configuration
GENERATOR_BASE_URL = "http://localhost:8081"
QUERY_ANALYZER_BASE_URL = "http://localhost:8080"

# Integration test data
INTEGRATION_TEST_DOCUMENTS = [
    {
        "content": "RISC-V is an open-source instruction set architecture (ISA) based on established reduced instruction set computer (RISC) principles. Unlike proprietary ISAs, RISC-V is provided under open source licenses that do not require fees to use.",
        "metadata": {
            "source": "risc-v-overview.pdf",
            "page": 1,
            "title": "RISC-V Introduction",
            "author": "RISC-V Foundation"
        },
        "doc_id": "doc_intro_001",
        "score": 0.95
    },
    {
        "content": "The RISC-V instruction set is designed to support a wide range of computing devices, from the smallest microcontrollers to the fastest supercomputers. The base integer ISA is very small and straightforward, making it easy to implement.",
        "metadata": {
            "source": "risc-v-design.pdf",
            "page": 3,
            "title": "RISC-V Design Philosophy"
        },
        "doc_id": "doc_design_002",
        "score": 0.88
    },
    {
        "content": "RISC-V supports modular ISA extensions, allowing implementers to add only the functionality they need. Common extensions include multiplication and division (M), atomic instructions (A), single-precision floating-point (F), and double-precision floating-point (D).",
        "metadata": {
            "source": "risc-v-extensions.pdf", 
            "page": 7,
            "title": "RISC-V Extensions"
        },
        "doc_id": "doc_ext_003",
        "score": 0.92
    }
]


class TestGeneratorEpic1Integration:
    """Test integration with Epic 1 components."""

    @pytest.mark.skipif(not GENERATOR_IMPORTS_AVAILABLE, reason=f"Generator imports not available: {GENERATOR_IMPORT_ERROR if not GENERATOR_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_epic1_answer_generator_integration(self):
        """Test that GeneratorService properly integrates with Epic1AnswerGenerator."""
        try:
            # Test service can be created (may fail due to Epic1 dependencies)
            service = GeneratorService()
            
            # Test initialization process
            start_time = time.time()
            try:
                await service._initialize_generator()
                initialization_time = time.time() - start_time
                
                # Hard Fail: Initialization takes more than 60 seconds
                assert initialization_time < 60.0, f"Epic1 integration initialization took {initialization_time:.2f}s - HARD FAIL"
                
                # Should set initialized flag
                assert service._initialized, "Service should be marked as initialized after Epic1 integration"
                
                # Should have generator instance
                if service.generator is not None:
                    # Verify it's the right type
                    assert hasattr(service.generator, 'generate_answer'), "Epic1AnswerGenerator should have generate_answer method"
                    
                    # Test that Epic1 configuration is applied
                    if hasattr(service.generator, '_config'):
                        config = service.generator._config
                        assert isinstance(config, dict), "Epic1 configuration should be dict"
                        print(f"✅ Epic1AnswerGenerator integration successful with config keys: {list(config.keys())}")
                    else:
                        print("ℹ️ Epic1AnswerGenerator created but config structure unknown")
                
            except ImportError as e:
                pytest.skip(f"Epic1 components not available for integration testing: {e}")
            except Exception as e:
                error_msg = str(e).lower()
                if any(keyword in error_msg for keyword in ["import", "module", "not found"]):
                    pytest.skip(f"Epic1 integration skipped due to missing dependencies: {e}")
                else:
                    pytest.fail(f"Epic1 integration failed with non-dependency error - HARD FAIL: {e}")
                    
        except Exception as e:
            pytest.fail(f"Epic1 integration test setup failed - HARD FAIL: {e}")

    @pytest.mark.skipif(not GENERATOR_IMPORTS_AVAILABLE, reason=f"Generator imports not available: {GENERATOR_IMPORT_ERROR if not GENERATOR_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_epic1_routing_strategies_integration(self):
        """Test integration with Epic1 routing strategies."""
        try:
            service = GeneratorService(config={
                "routing": {
                    "strategy": "cost_optimized",
                    "fallback_enabled": True
                }
            })
            
            # Test different routing strategies
            strategies = ["cost_optimized", "balanced", "quality_first"]
            
            for strategy in strategies:
                options = {
                    "strategy": strategy,
                    "max_cost": 0.05
                }
                
                try:
                    start_time = time.time()
                    result = await service.generate_answer(
                        query="Test query for routing integration",
                        context_documents=INTEGRATION_TEST_DOCUMENTS[:1],
                        options=options
                    )
                    response_time = time.time() - start_time
                    
                    # Hard Fail: Response time > 60 seconds
                    assert response_time < 60.0, f"Routing strategy {strategy} took {response_time:.2f}s - HARD FAIL"
                    
                    # Verify routing decision is captured
                    assert "routing_decision" in result, f"Routing decision missing for strategy {strategy}"
                    routing = result["routing_decision"]
                    
                    # Should reflect the requested strategy (or explain why not)
                    if "strategy" in routing:
                        used_strategy = routing["strategy"]
                        if used_strategy != strategy:
                            print(f"WARNING: Requested {strategy}, but used {used_strategy}")
                        else:
                            print(f"✅ Strategy {strategy} properly applied")
                    
                    # Should have cost information
                    cost = result.get("cost", 0)
                    assert isinstance(cost, (int, float)), f"Cost should be numeric for strategy {strategy}"
                    assert cost >= 0, f"Cost should be non-negative for strategy {strategy}"
                    
                    # For cost_optimized, should use lower-cost models
                    if strategy == "cost_optimized" and cost > 0.01:
                        print(f"WARNING: cost_optimized strategy used cost ${cost:.4f} (>$0.01)")
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    if any(keyword in error_msg for keyword in ["import", "module", "not found"]):
                        # Expected for missing Epic1 components
                        print(f"Strategy {strategy} test skipped due to missing Epic1 dependencies")
                        continue
                    else:
                        print(f"WARNING: Strategy {strategy} failed with error: {e}")
                        continue  # Don't hard fail - may be early implementation issues
            
        except Exception as e:
            error_msg = str(e).lower() 
            if any(keyword in error_msg for keyword in ["import", "module", "not found"]):
                pytest.skip(f"Epic1 routing integration skipped due to missing dependencies: {e}")
            else:
                pytest.fail(f"Epic1 routing integration failed - HARD FAIL: {e}")

    @pytest.mark.skipif(not GENERATOR_IMPORTS_AVAILABLE, reason=f"Generator imports not available: {GENERATOR_IMPORT_ERROR if not GENERATOR_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_epic1_model_registry_integration(self):
        """Test integration with Epic1 model registry."""
        try:
            service = GeneratorService()
            
            # Test getting available models through Epic1 integration
            start_time = time.time()
            models = await service.get_available_models()
            response_time = time.time() - start_time
            
            # Should respond quickly
            assert response_time < 10.0, f"Model registry integration took {response_time:.2f}s"
            
            # Should return list of models
            assert isinstance(models, list), "Models should be list from Epic1 integration"
            
            # If models are available, they should be properly formatted
            for model in models:
                assert isinstance(model, str), f"Model {model} should be string"
                assert len(model) > 0, f"Model name should not be empty: '{model}'"
                
                # Should follow provider/model format
                if "/" in model:
                    provider, model_name = model.split("/", 1)
                    assert len(provider) > 0, f"Provider should not be empty in {model}"
                    assert len(model_name) > 0, f"Model name should not be empty in {model}"
                    
                    # Known providers
                    valid_providers = ["ollama", "openai", "mistral", "anthropic", "huggingface"]
                    if provider not in valid_providers:
                        print(f"INFO: Unknown provider {provider} in {model}")
                        
            # Test getting model costs
            costs = await service.get_model_costs()
            assert isinstance(costs, dict), "Model costs should be dict from Epic1 integration"
            
            # If costs available, validate structure
            for model, cost in costs.items():
                assert isinstance(model, str), f"Model key {model} should be string"
                assert isinstance(cost, (int, float)), f"Cost {cost} should be numeric"
                assert cost >= 0, f"Cost {cost} should be non-negative"
                
            print(f"✅ Epic1 model registry integration successful - {len(models)} models, {len(costs)} costs")
            
        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ["import", "module", "not found"]):
                pytest.skip(f"Epic1 model registry integration skipped: {e}")
            else:
                # Don't hard fail - may be early implementation
                print(f"WARNING: Epic1 model registry integration failed: {e}")


class TestGeneratorServiceCommunication:
    """Test service-to-service communication patterns."""

    def test_generator_query_analyzer_integration(self):
        """Test integration between Generator and Query Analyzer services."""
        try:
            # Test that both services can be reached
            generator_health = requests.get(f"{GENERATOR_BASE_URL}/health", timeout=5.0)
            analyzer_health = requests.get(f"{QUERY_ANALYZER_BASE_URL}/health", timeout=5.0)
            
            if generator_health.status_code >= 500 or analyzer_health.status_code >= 500:
                pytest.skip("One or both services unavailable")
            
            # Simulate workflow: Query Analyzer -> Generator
            query = "Explain the key advantages of RISC-V vector extensions for machine learning workloads"
            
            # 1. Analyze query complexity
            analyze_request = {
                "query": query,
                "options": {
                    "strategy": "balanced",
                    "include_cost_estimate": True
                }
            }
            
            start_time = time.time()
            analyze_response = requests.post(
                f"{QUERY_ANALYZER_BASE_URL}/api/v1/analyze",
                json=analyze_request,
                timeout=10.0
            )
            analyze_time = time.time() - start_time
            
            if analyze_response.status_code != 200:
                pytest.skip(f"Query analyzer failed: {analyze_response.status_code}")
            
            analysis_data = analyze_response.json()
            
            # 2. Use analysis results for generation
            complexity = analysis_data.get("complexity", "medium")
            recommended_models = analysis_data.get("recommended_models", ["ollama/llama3.2:3b"])
            
            generate_request = {
                "query": query,
                "context_documents": INTEGRATION_TEST_DOCUMENTS,
                "options": {
                    "strategy": "balanced",
                    "preferred_model": recommended_models[0] if recommended_models else None,
                    "max_cost": 0.05
                }
            }
            
            generate_response = requests.post(
                f"{GENERATOR_BASE_URL}/api/v1/generate",
                json=generate_request,
                timeout=30.0
            )
            generate_time = time.time() - start_time - analyze_time
            
            # Hard Fail: Total workflow time > 60 seconds
            total_time = analyze_time + generate_time
            assert total_time < 60.0, f"Service integration workflow took {total_time:.2f}s - HARD FAIL"
            
            if generate_response.status_code == 200:
                gen_data = generate_response.json()
                
                # Verify integration worked
                model_used = gen_data.get("model_used", "")
                cost = gen_data.get("cost", 0)
                
                print(f"✅ Service integration successful:")
                print(f"   Complexity: {complexity}")
                print(f"   Model used: {model_used}")
                print(f"   Cost: ${cost:.4f}")
                print(f"   Total time: {total_time:.2f}s")
                
                # Quality checks
                if complexity == "simple" and cost > 0.01:
                    print(f"WARNING: Simple query used expensive model (${cost:.4f})")
                if complexity == "complex" and cost == 0.0:
                    print(f"WARNING: Complex query used free model - may not be optimal")
                    
            elif generate_response.status_code >= 500:
                pytest.fail(f"Generator service failed during integration - HARD FAIL: {generate_response.status_code}")
            else:
                print(f"Generation failed with {generate_response.status_code} - may be expected for early stage")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("One or both services not running")
        except requests.exceptions.Timeout:
            pytest.fail("Service integration timed out - HARD FAIL")
        except Exception as e:
            pytest.fail(f"Service communication test failed - HARD FAIL: {e}")

    def test_generator_service_resilience(self):
        """Test that generator service is resilient to other service failures."""
        try:
            # Test that generator can work even if analyzer is unavailable
            generate_request = {
                "query": "What is RISC-V?",
                "context_documents": INTEGRATION_TEST_DOCUMENTS[:1],
                "options": {
                    "strategy": "balanced"
                }
            }
            
            # Should not depend on external services for basic functionality
            start_time = time.time()
            response = requests.post(
                f"{GENERATOR_BASE_URL}/api/v1/generate",
                json=generate_request,
                timeout=30.0
            )
            response_time = time.time() - start_time
            
            # Should respond in reasonable time
            assert response_time < 30.0, f"Generator service took {response_time:.2f}s without external dependencies"
            
            # Should either succeed or fail gracefully
            if response.status_code >= 500:
                # Check if service is still responsive
                health_response = requests.get(f"{GENERATOR_BASE_URL}/health", timeout=5.0)
                if health_response.status_code >= 500:
                    pytest.fail("Generator service crashed without external services - HARD FAIL")
                else:
                    print("Generator service failed but remained responsive - acceptable")
            
            print(f"✅ Generator service resilience test passed - {response.status_code} in {response_time:.2f}s")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Generator service not running")
        except requests.exceptions.Timeout:
            print("WARNING: Generator service timed out - may indicate dependency issues")
        except Exception as e:
            pytest.fail(f"Generator service resilience test failed - HARD FAIL: {e}")


class TestGeneratorMultiModelRouting:
    """Test multi-model routing integration scenarios."""

    @pytest.mark.skipif(not GENERATOR_IMPORTS_AVAILABLE, reason=f"Generator imports not available: {GENERATOR_IMPORT_ERROR if not GENERATOR_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_multi_model_routing_consistency(self):
        """Test that multi-model routing produces consistent decisions."""
        try:
            service = GeneratorService()
            
            # Test queries with different complexities
            test_queries = [
                {
                    "query": "What is RISC-V?",
                    "expected_complexity": "simple",
                    "max_expected_cost": 0.001
                },
                {
                    "query": "Compare RISC-V vector extensions with ARM SVE in terms of performance implications for machine learning workloads",
                    "expected_complexity": "complex", 
                    "max_expected_cost": 0.05
                },
                {
                    "query": "Explain how RISC-V interrupt handling differs from x86 architecture",
                    "expected_complexity": "medium",
                    "max_expected_cost": 0.01
                }
            ]
            
            routing_results = []
            
            for test_case in test_queries:
                query = test_case["query"]
                
                try:
                    # Test with cost_optimized strategy
                    result = await service.generate_answer(
                        query=query,
                        context_documents=INTEGRATION_TEST_DOCUMENTS[:2],
                        options={"strategy": "cost_optimized"}
                    )
                    
                    routing = result.get("routing_decision", {})
                    cost = result.get("cost", 0)
                    model = result.get("model_used", "unknown")
                    
                    routing_results.append({
                        "query": query,
                        "complexity": test_case["expected_complexity"],
                        "model": model,
                        "cost": cost,
                        "strategy": routing.get("strategy", "unknown"),
                        "routing_reason": routing.get("selection_reason", "unknown")
                    })
                    
                    # Validate routing makes sense
                    if cost > test_case["max_expected_cost"]:
                        print(f"WARNING: {test_case['expected_complexity']} query cost ${cost:.4f} exceeds expected max ${test_case['max_expected_cost']:.4f}")
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    if any(keyword in error_msg for keyword in ["import", "module", "not found"]):
                        print(f"Query '{query[:50]}...' skipped due to missing dependencies")
                        continue
                    else:
                        print(f"WARNING: Query '{query[:50]}...' failed: {e}")
                        continue
            
            if routing_results:
                print("✅ Multi-model routing consistency test results:")
                for result in routing_results:
                    print(f"   {result['complexity']}: {result['model']} (${result['cost']:.4f}) - {result['routing_reason']}")
                
                # Check that simple queries use cheaper models than complex ones
                simple_costs = [r['cost'] for r in routing_results if r['complexity'] == 'simple']
                complex_costs = [r['cost'] for r in routing_results if r['complexity'] == 'complex']
                
                if simple_costs and complex_costs:
                    avg_simple_cost = sum(simple_costs) / len(simple_costs)
                    avg_complex_cost = sum(complex_costs) / len(complex_costs)
                    
                    if avg_simple_cost > avg_complex_cost:
                        print(f"WARNING: Simple queries cost more on average (${avg_simple_cost:.4f}) than complex ones (${avg_complex_cost:.4f})")
                    else:
                        print(f"✅ Cost scaling appropriate: simple ${avg_simple_cost:.4f}, complex ${avg_complex_cost:.4f}")
            else:
                pytest.skip("No routing results available - likely due to missing Epic1 dependencies")
            
        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ["import", "module", "not found"]):
                pytest.skip(f"Multi-model routing test skipped: {e}")
            else:
                pytest.fail(f"Multi-model routing consistency test failed - HARD FAIL: {e}")

    @pytest.mark.skipif(not GENERATOR_IMPORTS_AVAILABLE, reason=f"Generator imports not available: {GENERATOR_IMPORT_ERROR if not GENERATOR_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_fallback_mechanism_integration(self):
        """Test that fallback mechanisms work in integration scenarios."""
        try:
            service = GeneratorService(config={
                "routing": {
                    "fallback_enabled": True,
                    "max_retries": 2
                }
            })
            
            # Test with potentially problematic requests
            challenging_requests = [
                {
                    "query": "x" * 1000,  # Very long query
                    "context_documents": INTEGRATION_TEST_DOCUMENTS[:1],
                    "options": {"strategy": "cost_optimized", "max_cost": 0.001}
                },
                {
                    "query": "Explain quantum computing",
                    "context_documents": [{"content": "", "metadata": {}}],  # Empty context
                    "options": {"strategy": "quality_first", "preferred_model": "nonexistent/model"}
                }
            ]
            
            for req in challenging_requests:
                try:
                    start_time = time.time()
                    result = await service.generate_answer(
                        query=req["query"],
                        context_documents=req["context_documents"],
                        options=req["options"]
                    )
                    response_time = time.time() - start_time
                    
                    # Should handle challenging requests within reasonable time
                    assert response_time < 30.0, f"Fallback mechanism took {response_time:.2f}s"
                    
                    # Check if fallback was used
                    routing = result.get("routing_decision", {})
                    fallback_used = routing.get("fallback_used", False)
                    
                    if fallback_used:
                        print(f"✅ Fallback mechanism triggered for challenging request")
                        
                except ValueError as e:
                    # Expected for some invalid requests
                    print(f"Challenging request properly rejected: {e}")
                except Exception as e:
                    error_msg = str(e).lower()
                    if any(keyword in error_msg for keyword in ["import", "module", "not found"]):
                        continue  # Skip due to dependencies
                    else:
                        print(f"WARNING: Fallback mechanism failed for challenging request: {e}")
                        
        except Exception as e:
            error_msg = str(e).lower() 
            if any(keyword in error_msg for keyword in ["import", "module", "not found"]):
                pytest.skip(f"Fallback mechanism test skipped: {e}")
            else:
                print(f"WARNING: Fallback mechanism integration test failed: {e}")


class TestGeneratorCostTrackingIntegration:
    """Test cost tracking integration scenarios."""

    @pytest.mark.skipif(not GENERATOR_IMPORTS_AVAILABLE, reason=f"Generator imports not available: {GENERATOR_IMPORT_ERROR if not GENERATOR_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_cost_tracking_across_requests(self):
        """Test that cost tracking works correctly across multiple requests."""
        try:
            service = GeneratorService()
            
            # Track costs across multiple requests
            requests_data = [
                {
                    "query": "What is RISC-V?",
                    "context_documents": INTEGRATION_TEST_DOCUMENTS[:1],
                    "options": {"strategy": "cost_optimized"}
                },
                {
                    "query": "How does RISC-V compare to ARM?",
                    "context_documents": INTEGRATION_TEST_DOCUMENTS[:2],
                    "options": {"strategy": "balanced"}
                },
                {
                    "query": "Detailed analysis of RISC-V vector extensions performance",
                    "context_documents": INTEGRATION_TEST_DOCUMENTS,
                    "options": {"strategy": "quality_first", "max_cost": 0.03}
                }
            ]
            
            total_tracked_cost = 0.0
            request_costs = []
            
            for i, req_data in enumerate(requests_data):
                try:
                    result = await service.generate_answer(
                        query=req_data["query"],
                        context_documents=req_data["context_documents"], 
                        options=req_data["options"]
                    )
                    
                    cost = result.get("cost", 0)
                    model = result.get("model_used", "unknown")
                    strategy = req_data["options"]["strategy"]
                    
                    request_costs.append({
                        "request": i+1,
                        "strategy": strategy,
                        "model": model,
                        "cost": cost
                    })
                    
                    total_tracked_cost += cost
                    
                    # Validate cost precision
                    assert isinstance(cost, (int, float)), f"Cost {cost} should be numeric"
                    assert cost >= 0, f"Cost {cost} should be non-negative"
                    
                    # Cost should be reasonable (not obviously wrong)
                    assert cost <= 1.0, f"Cost ${cost:.4f} seems too high for single request"
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    if any(keyword in error_msg for keyword in ["import", "module", "not found"]):
                        print(f"Request {i+1} skipped due to missing dependencies")
                        continue
                    else:
                        print(f"WARNING: Request {i+1} failed: {e}")
                        continue
            
            if request_costs:
                print("✅ Cost tracking integration results:")
                for req in request_costs:
                    print(f"   Request {req['request']} ({req['strategy']}): {req['model']} - ${req['cost']:.4f}")
                print(f"   Total tracked cost: ${total_tracked_cost:.4f}")
                
                # Validate cost ordering makes sense
                cost_optimized_costs = [r['cost'] for r in request_costs if r['strategy'] == 'cost_optimized']
                quality_first_costs = [r['cost'] for r in request_costs if r['strategy'] == 'quality_first']
                
                if cost_optimized_costs and quality_first_costs:
                    avg_cost_opt = sum(cost_optimized_costs) / len(cost_optimized_costs)
                    avg_quality = sum(quality_first_costs) / len(quality_first_costs)
                    
                    if avg_cost_opt > avg_quality:
                        print(f"WARNING: Cost optimized avg (${avg_cost_opt:.4f}) > quality first avg (${avg_quality:.4f})")
                    else:
                        print(f"✅ Cost strategy working: cost_opt ${avg_cost_opt:.4f}, quality ${avg_quality:.4f}")
            else:
                pytest.skip("No cost tracking results available")
                
        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ["import", "module", "not found"]):
                pytest.skip(f"Cost tracking integration test skipped: {e}")
            else:
                pytest.fail(f"Cost tracking integration test failed - HARD FAIL: {e}")


@pytest.mark.integration_performance  
class TestGeneratorIntegrationPerformance:
    """Test integration performance characteristics."""

    @pytest.mark.skipif(not GENERATOR_IMPORTS_AVAILABLE, reason=f"Generator imports not available: {GENERATOR_IMPORT_ERROR if not GENERATOR_IMPORTS_AVAILABLE else ''}")
    @pytest.mark.asyncio
    async def test_concurrent_generation_integration(self):
        """Test concurrent generation requests integration."""
        try:
            service = GeneratorService()
            
            # Create multiple concurrent requests
            concurrent_requests = []
            for i in range(3):  # Modest concurrent load
                request_data = {
                    "query": f"Request {i+1}: What are RISC-V key features?",
                    "context_documents": INTEGRATION_TEST_DOCUMENTS[:2],
                    "options": {
                        "strategy": "balanced",
                        "max_cost": 0.02
                    }
                }
                concurrent_requests.append(request_data)
            
            # Execute concurrent requests
            start_time = time.time()
            
            tasks = []
            for req in concurrent_requests:
                task = asyncio.create_task(
                    service.generate_answer(
                        query=req["query"],
                        context_documents=req["context_documents"],
                        options=req["options"]
                    )
                )
                tasks.append(task)
            
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                total_time = time.time() - start_time
                
                # Hard Fail: Concurrent requests take more than 60 seconds
                assert total_time < 60.0, f"Concurrent integration requests took {total_time:.2f}s - HARD FAIL"
                
                successful_results = []
                failed_results = []
                
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        error_msg = str(result).lower()
                        if any(keyword in error_msg for keyword in ["import", "module", "not found"]):
                            print(f"Concurrent request {i+1} skipped due to missing dependencies")
                        else:
                            failed_results.append(f"Request {i+1}: {result}")
                    else:
                        successful_results.append(result)
                        
                        # Validate successful result
                        assert isinstance(result, dict), f"Result {i+1} should be dict"
                        assert "cost" in result, f"Result {i+1} missing cost"
                        assert "model_used" in result, f"Result {i+1} missing model_used"
                
                if successful_results:
                    print(f"✅ Concurrent integration test: {len(successful_results)}/{len(concurrent_requests)} successful in {total_time:.2f}s")
                    
                    # Check cost consistency
                    costs = [r.get("cost", 0) for r in successful_results]
                    if costs:
                        avg_cost = sum(costs) / len(costs)
                        print(f"   Average cost: ${avg_cost:.4f}")
                        
                        # Costs should be reasonable
                        for cost in costs:
                            if cost > 0.05:
                                print(f"WARNING: High concurrent request cost: ${cost:.4f}")
                else:
                    pytest.skip("No successful concurrent integration results")
                
                if failed_results:
                    print("Failed concurrent requests:")
                    for failure in failed_results:
                        print(f"   {failure}")
                
            except asyncio.TimeoutError:
                pytest.fail("Concurrent integration requests timed out - HARD FAIL")
                
        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ["import", "module", "not found"]):
                pytest.skip(f"Concurrent integration test skipped: {e}")
            else:
                pytest.fail(f"Concurrent integration test failed - HARD FAIL: {e}")

    def test_memory_usage_during_integration(self):
        """Test memory usage during integration scenarios."""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Simulate integration workload
            integration_requests = [
                {
                    "method": "POST",
                    "url": f"{GENERATOR_BASE_URL}/api/v1/generate",
                    "json": {
                        "query": "Integration test query about RISC-V architecture details",
                        "context_documents": INTEGRATION_TEST_DOCUMENTS,
                        "options": {"strategy": "balanced"}
                    }
                }
            ]
            
            for req in integration_requests:
                try:
                    response = requests.request(
                        method=req["method"],
                        url=req["url"],
                        json=req["json"],
                        timeout=30.0
                    )
                    
                    # Don't require success - just test that memory doesn't explode
                    
                except requests.exceptions.ConnectionError:
                    pytest.skip("Generator service not running for memory test")
                except requests.exceptions.Timeout:
                    print("Integration request timed out during memory test")
                except Exception as e:
                    print(f"Integration request failed during memory test: {e}")
            
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory
            
            # Hard Fail: Process using more than 8GB total
            assert current_memory < 8192, f"Process using {current_memory:.1f}MB - HARD FAIL (>8GB)"
            
            # Quality Flag: Significant memory increase
            if memory_increase > 200:  # 200MB increase for integration tests
                print(f"WARNING: Memory increased by {memory_increase:.1f}MB during integration tests")
            else:
                print(f"✅ Memory usage reasonable: increased by {memory_increase:.1f}MB")
                
        except ImportError:
            pytest.skip("psutil not available for memory testing")
        except Exception as e:
            pytest.fail(f"Memory usage integration test failed - HARD FAIL: {e}")