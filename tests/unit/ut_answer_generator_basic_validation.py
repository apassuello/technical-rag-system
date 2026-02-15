#!/usr/bin/env python3
"""
Epic 1 Basic Validation Script.

This script provides basic validation of the Epic 1 multi-model routing
implementation, testing key components without requiring external API keys.

Tests:
- Query complexity analysis
- Routing strategy selection
- Cost tracking functionality
- Component integration
- Fallback mechanisms
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any
from decimal import Decimal
import pytest

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cost_tracker():
    """Test cost tracking functionality."""
    print("🧮 Testing Cost Tracking System...")
    
    try:
        from src.components.generators.llm_adapters.cost_tracker import (
            CostTracker, 
            get_cost_tracker,
            record_llm_usage
        )
        
        # Create cost tracker
        tracker = CostTracker(precision_places=6)
        
        # Record some test usage
        tracker.record_usage(
            provider="local",
            model="qwen2.5-1.5b-instruct",
            input_tokens=100,
            output_tokens=50,
            cost_usd=Decimal('0.000000'),  # Free
            query_complexity="simple",
            request_time_ms=200.0,
            success=True
        )
        
        tracker.record_usage(
            provider="openai",
            model="gpt-4-turbo",
            input_tokens=200,
            output_tokens=150,
            cost_usd=Decimal('0.007000'),  # $0.007
            query_complexity="complex",
            request_time_ms=800.0,
            success=True
        )
        
        # Test cost calculations
        total_cost = tracker.get_total_cost()
        cost_by_provider = tracker.get_cost_by_provider()
        cost_by_complexity = tracker.get_cost_by_complexity()
        
        print(f"  ✅ Total cost tracked: ${total_cost:.6f}")
        print(f"  ✅ Cost by provider: {cost_by_provider}")
        print(f"  ✅ Cost by complexity: {cost_by_complexity}")
        
        # Test recommendations
        recommendations = tracker.get_cost_optimization_recommendations()
        print(f"  ✅ Generated {len(recommendations)} cost optimization recommendations")

    except Exception as e:
        pytest.fail(f"Cost tracker test failed: {str(e)}")

def test_routing_strategies():
    """Test routing strategy implementations."""
    print("🧭 Testing Routing Strategies...")

    try:
        from src.components.generators.routing.routing_strategies import (
            CostOptimizedStrategy,
            QualityFirstStrategy,
            BalancedStrategy,
            ModelOption
        )

        # Test queries with different complexity levels
        test_cases = [
            {'complexity': 0.2, 'level': 'simple', 'query': 'What is Python?'},
            {'complexity': 0.5, 'level': 'medium', 'query': 'How does a REST API work?'},
            {'complexity': 0.8, 'level': 'complex', 'query': 'Explain the implementation of distributed consensus algorithms in microservices architecture.'}
        ]

        # Create available model options
        available_models = [
            ModelOption(
                provider='local',
                model='qwen2.5-1.5b-instruct',
                estimated_cost=Decimal('0.0000'),
                estimated_quality=0.80,
                estimated_latency_ms=2000.0
            ),
            ModelOption(
                provider='mistral',
                model='mistral-small',
                estimated_cost=Decimal('0.002'),
                estimated_quality=0.85,
                estimated_latency_ms=1500.0
            ),
            ModelOption(
                provider='openai',
                model='gpt-3.5-turbo',
                estimated_cost=Decimal('0.0015'),
                estimated_quality=0.90,
                estimated_latency_ms=1000.0
            ),
            ModelOption(
                provider='openai',
                model='gpt-4-turbo',
                estimated_cost=Decimal('0.020'),
                estimated_quality=0.95,
                estimated_latency_ms=1200.0
            )
        ]

        strategies = {
            'cost_optimized': CostOptimizedStrategy(),
            'quality_first': QualityFirstStrategy(),
            'balanced': BalancedStrategy()
        }

        for strategy_name, strategy in strategies.items():
            print(f"  Testing {strategy_name} strategy:")

            for test_case in test_cases:
                # Build query_analysis dict
                query_analysis = {
                    'complexity_score': test_case['complexity'],
                    'complexity_level': test_case['level'],
                    'query_length': len(test_case['query'].split())
                }

                # Call with correct API signature
                model_option = strategy.select_model(
                    query_analysis=query_analysis,
                    available_models=available_models
                )

                # Assert result is valid
                assert model_option is not None, f"Strategy {strategy_name} returned None for {test_case['level']}"
                assert hasattr(model_option, 'provider'), "ModelOption missing provider attribute"
                assert hasattr(model_option, 'model'), "ModelOption missing model attribute"

                print(f"    {test_case['level']}: {model_option.provider}/{model_option.model} "
                      f"(cost=${model_option.estimated_cost:.4f}, quality={model_option.estimated_quality:.2f})")

        print("  ✅ All routing strategies working correctly")

    except Exception as e:
        pytest.fail(f"Routing strategies test failed: {str(e)}")

@pytest.mark.requires_ollama
def test_adaptive_router():
    """Test adaptive router — requires Ollama for model availability checks."""
    print("🤖 Testing Adaptive Router...")
    
    try:
        from src.components.generators.routing import AdaptiveRouter
        
        # Initialize router without query analyzer (fallback mode)
        router = AdaptiveRouter(
            default_strategy="balanced",
            query_analyzer=None,  # Will use basic fallback analysis
            enable_fallback=True,
            enable_cost_tracking=True
        )
        
        # Test queries
        test_queries = [
            "What is AI?",  # Simple
            "How does machine learning classification work?",  # Medium
            "Explain the mathematical foundations of transformer architectures and attention mechanisms in detail."  # Complex
        ]
        
        for query in test_queries:
            # Route query (will use basic complexity analysis)
            decision = router.route_query(query)
            
            print(f"  Query: '{query[:50]}...'")
            print(f"    Routed to: {decision.selected_model.provider}/{decision.selected_model.model}")
            print(f"    Complexity: {decision.complexity_level} ({decision.query_complexity:.3f})")
            print(f"    Decision time: {decision.decision_time_ms:.1f}ms")
            print(f"    Estimated cost: ${decision.selected_model.estimated_cost:.6f}")
        
        # Test routing statistics
        stats = router.get_routing_stats()
        print(f"  ✅ Routing stats: {stats['total_decisions']} decisions, "
              f"avg {stats['avg_decision_time_ms']:.1f}ms")

    except Exception as e:
        pytest.fail(f"Adaptive router test failed: {str(e)}")

def test_llm_adapters():
    """Test LLM adapter imports and basic functionality."""
    print("🔌 Testing LLM Adapters...")
    
    try:
        # Test adapter imports
        from src.components.generators.llm_adapters import (
            get_adapter_class,
            ADAPTER_REGISTRY
        )
        
        # Check all expected adapters are registered
        expected_adapters = ['ollama', 'openai', 'mistral', 'huggingface', 'mock']
        available_adapters = list(ADAPTER_REGISTRY.keys())
        
        for expected in expected_adapters:
            if expected in available_adapters:
                print(f"  ✅ {expected} adapter available")
                
                # Test adapter class retrieval
                adapter_class = get_adapter_class(expected)
                print(f"    Class: {adapter_class.__name__}")
            else:
                print(f"  ❌ {expected} adapter missing")
        
        # Test mock adapter (safe to initialize)
        from src.components.generators.llm_adapters import MockLLMAdapter
        mock_adapter = MockLLMAdapter()
        
        # Test basic functionality
        model_info = mock_adapter.get_model_info()
        print(f"  ✅ Mock adapter info: {model_info['provider']}/{model_info['model']}")

    except Exception as e:
        pytest.fail(f"LLM adapters test failed: {str(e)}")

def test_epic1_answer_generator():
    """Test Epic 1 Answer Generator in backward compatibility mode."""
    print("🎯 Testing Epic 1 Answer Generator...")
    
    try:
        from src.components.generators.epic1_answer_generator import Epic1AnswerGenerator
        
        # Test in backward compatibility mode (no Epic1QueryAnalyzer)
        generator = Epic1AnswerGenerator(
            model_name="mock",  # This should trigger backward compatibility mode
            temperature=0.7,
            max_tokens=100
        )
        
        print(f"  ✅ Epic 1 generator initialized")
        print(f"  Routing enabled: {generator.routing_enabled}")
        
        # Get generator info
        info = generator.get_generator_info()
        print(f"  Generator type: {info.get('type', 'standard')}")
        print(f"  Epic 1 available: {info.get('epic1_available', False)}")
        
        if generator.routing_enabled:
            routing_stats = generator.get_routing_statistics()
            print(f"  Routing stats: {routing_stats}")

    except Exception as e:
        pytest.fail(f"Epic 1 answer generator test failed: {str(e)}")

def main():
    """Run all basic validation tests."""
    print("🚀 Epic 1 Basic Validation Tests")
    print("=" * 50)
    
    tests = [
        test_cost_tracker,
        test_routing_strategies,
        test_adaptive_router,
        test_llm_adapters,
        test_epic1_answer_generator,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
            print()
        except Exception as e:
            print(f"  ❌ Test {test_func.__name__} failed with exception: {str(e)}")
            results.append(False)
            print()
    
    # Summary
    print("=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total) * 100
    
    print(f"Tests passed: {passed}/{total} ({success_rate:.1f}%)")
    
    if success_rate == 100:
        print("🎉 All Epic 1 basic validation tests passed!")
        print("✅ Epic 1 implementation is ready for integration testing")
    elif success_rate >= 80:
        print("⚠️  Most Epic 1 tests passed - minor issues detected")
        print("🔧 Review failed tests before proceeding to integration")
    else:
        print("❌ Significant issues detected in Epic 1 implementation")
        print("🚨 Fix critical issues before integration testing")
    
    return success_rate == 100

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)