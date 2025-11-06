#!/usr/bin/env python3
"""
Integration Performance Fix Validation

This script specifically validates the integration performance issue identified
in the main validation and demonstrates the fix through proper configuration.

Issue: Epic1AnswerGenerator showing 613ms routing overhead (target: <50ms)
Root Cause: Development mode testing with per-request availability checks
Solution: Production mode configuration with cached availability
"""

import time
import sys
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, '/Users/apa/ml_projects/rag-portfolio/project-1-technical-rag')

from src.components.generators.epic1_answer_generator import Epic1AnswerGenerator
from src.core.interfaces import Document


def test_integration_performance_configurations():
    """Test Epic1AnswerGenerator with different performance configurations."""
    print("🔧 INTEGRATION PERFORMANCE FIX VALIDATION")
    print("=" * 60)
    
    # Mock context documents
    context = [
        Document(content="Machine learning is a subset of artificial intelligence.", metadata={}),
        Document(content="Neural networks are inspired by biological neurons.", metadata={})
    ]
    
    test_query = "What is machine learning?"
    
    # Test 1: Development Configuration (Problem)
    print("\n📊 Test 1: Development Configuration (Current Issue)")
    print("-" * 50)
    
    development_config = {
        "type": "adaptive",
        "routing": {
            "enabled": True,
            "default_strategy": "balanced"
        },
        "cost_tracking": {
            "enabled": True
        },
        "llm_client": {
            "type": "ollama",
            "config": {
                "model_name": "llama3.2:3b",
                "base_url": "http://localhost:11434"
            }
        }
    }
    
    try:
        dev_generator = Epic1AnswerGenerator(config=development_config)
        
        # Measure routing overhead in current configuration
        routing_times = []
        for i in range(3):  # Limited tests for faster validation
            start_time = time.perf_counter()
            try:
                answer = dev_generator.generate(test_query, context)
                total_time = (time.perf_counter() - start_time) * 1000  # ms
                
                # Extract routing time from metadata
                routing_metadata = answer.metadata.get('routing', {})
                routing_time = routing_metadata.get('routing_decision_time_ms', 0)
                routing_times.append(routing_time)
                
                print(f"  Test {i+1}: {total_time:.1f}ms total, {routing_time:.3f}ms routing")
                
            except Exception as e:
                print(f"  Test {i+1}: ERROR - {str(e)}")
                routing_times.append(float('inf'))
        
        valid_routing_times = [t for t in routing_times if t != float('inf')]
        dev_mean_routing = sum(valid_routing_times) / len(valid_routing_times) if valid_routing_times else float('inf')
        
        print(f"\n  Development Config Results:")
        print(f"    Mean routing time: {dev_mean_routing:.3f}ms")
        print(f"    Target: <50ms")
        print(f"    Status: {'✅ PASS' if dev_mean_routing < 50.0 else '❌ FAIL'}")
        
    except Exception as e:
        print(f"  Development configuration failed: {str(e)}")
        dev_mean_routing = float('inf')
    
    # Test 2: Production Configuration (Solution)
    print("\n📊 Test 2: Production Configuration (Optimized)")
    print("-" * 50)
    
    production_config = {
        "type": "adaptive",
        "routing": {
            "enabled": True,
            "default_strategy": "balanced",
            "enable_availability_testing": False,  # KEY FIX: Disable per-request testing
            "availability_check_mode": "startup",   # Use startup caching only
            "fallback_on_failure": True            # Enable failure-based fallback
        },
        "cost_tracking": {
            "enabled": True
        },
        "llm_client": {
            "type": "ollama",
            "config": {
                "model_name": "llama3.2:3b",
                "base_url": "http://localhost:11434"
            }
        }
    }
    
    try:
        # Create production-optimized generator
        prod_generator = Epic1AnswerGenerator(config=production_config)
        
        # Measure routing overhead with production configuration
        routing_times = []
        for i in range(3):  # Limited tests for faster validation
            start_time = time.perf_counter()
            try:
                answer = prod_generator.generate(test_query, context)
                total_time = (time.perf_counter() - start_time) * 1000  # ms
                
                # Extract routing time from metadata
                routing_metadata = answer.metadata.get('routing', {})
                routing_time = routing_metadata.get('routing_decision_time_ms', 0)
                routing_times.append(routing_time)
                
                print(f"  Test {i+1}: {total_time:.1f}ms total, {routing_time:.3f}ms routing")
                
            except Exception as e:
                print(f"  Test {i+1}: ERROR - {str(e)}")
                routing_times.append(float('inf'))
        
        valid_routing_times = [t for t in routing_times if t != float('inf')]
        prod_mean_routing = sum(valid_routing_times) / len(valid_routing_times) if valid_routing_times else float('inf')
        
        print(f"\n  Production Config Results:")
        print(f"    Mean routing time: {prod_mean_routing:.3f}ms")
        print(f"    Target: <50ms")
        print(f"    Status: {'✅ PASS' if prod_mean_routing < 50.0 else '❌ FAIL'}")
        
    except Exception as e:
        print(f"  Production configuration failed: {str(e)}")
        prod_mean_routing = float('inf')
    
    # Test 3: Backward Compatibility (Legacy Single-Model)
    print("\n📊 Test 3: Backward Compatibility (Legacy Mode)")
    print("-" * 50)
    
    try:
        # Test backward compatibility with legacy parameters
        legacy_generator = Epic1AnswerGenerator(
            model_name="llama3.2:3b",
            use_ollama=True,
            ollama_url="http://localhost:11434"
        )
        
        # Measure legacy performance (should skip routing entirely)
        routing_times = []
        for i in range(3):
            start_time = time.perf_counter()
            try:
                answer = legacy_generator.generate(test_query, context)
                total_time = (time.perf_counter() - start_time) * 1000  # ms
                
                # Legacy mode should have no routing metadata
                routing_metadata = answer.metadata.get('routing', {})
                routing_time = routing_metadata.get('routing_decision_time_ms', 0)  # Should be 0
                routing_times.append(routing_time)
                
                print(f"  Test {i+1}: {total_time:.1f}ms total, {routing_time:.3f}ms routing (legacy)")
                
            except Exception as e:
                print(f"  Test {i+1}: ERROR - {str(e)}")
                routing_times.append(float('inf'))
        
        valid_routing_times = [t for t in routing_times if t != float('inf')]
        legacy_mean_routing = sum(valid_routing_times) / len(valid_routing_times) if valid_routing_times else 0
        
        print(f"\n  Legacy Config Results:")
        print(f"    Mean routing time: {legacy_mean_routing:.3f}ms (should be ~0)")
        print(f"    Routing enabled: {legacy_generator.routing_enabled}")
        print(f"    Status: {'✅ PASS' if not legacy_generator.routing_enabled else '❌ FAIL'}")
        
    except Exception as e:
        print(f"  Legacy configuration failed: {str(e)}")
        legacy_mean_routing = float('inf')
    
    # Performance Comparison and Recommendations
    print("\n" + "=" * 60)
    print("🏆 INTEGRATION PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    print(f"\n📊 Configuration Performance Comparison:")
    print(f"  Development Config: {dev_mean_routing:.3f}ms routing overhead")
    print(f"  Production Config:  {prod_mean_routing:.3f}ms routing overhead")
    print(f"  Legacy Config:      {legacy_mean_routing:.3f}ms routing overhead")
    
    if prod_mean_routing < 50.0:
        improvement = dev_mean_routing / prod_mean_routing if prod_mean_routing > 0 else float('inf')
        print(f"\n✅ PERFORMANCE FIX VALIDATED:")
        print(f"  Improvement Factor: {improvement:.1f}x faster with production config")
        print(f"  Production config meets <50ms target: ✅")
        
        print(f"\n💡 DEPLOYMENT RECOMMENDATIONS:")
        print(f"  1. Use production config in all deployments")
        print(f"  2. Set enable_availability_testing=False for production")
        print(f"  3. Configure availability_check_mode='startup'")
        print(f"  4. Enable fallback_on_failure=True for reliability")
        
    else:
        print(f"\n⚠️  PERFORMANCE FIX NEEDS INVESTIGATION:")
        print(f"  Production config still exceeds 50ms target")
        print(f"  Additional optimization may be required")
    
    # Configuration Template
    print(f"\n📋 RECOMMENDED PRODUCTION CONFIGURATION:")
    print(f"```yaml")
    print(f"epic1_answer_generator:")
    print(f"  type: 'adaptive'")
    print(f"  routing:")
    print(f"    enabled: true")
    print(f"    default_strategy: 'balanced'")
    print(f"    enable_availability_testing: false  # KEY: No per-request testing")
    print(f"    availability_check_mode: 'startup'  # Cache at startup only")
    print(f"    fallback_on_failure: true          # Enable failure-based fallback")
    print(f"  cost_tracking:")
    print(f"    enabled: true")
    print(f"  llm_client:")
    print(f"    type: 'ollama'")
    print(f"    config:")
    print(f"      model_name: 'llama3.2:3b'")
    print(f"      base_url: 'http://localhost:11434'")
    print(f"```")
    
    return {
        'development_routing_ms': dev_mean_routing,
        'production_routing_ms': prod_mean_routing,
        'legacy_routing_ms': legacy_mean_routing,
        'target_met': prod_mean_routing < 50.0,
        'improvement_factor': dev_mean_routing / prod_mean_routing if prod_mean_routing > 0 else float('inf')
    }


if __name__ == "__main__":
    results = test_integration_performance_configurations()
    print(f"\n📁 Integration performance fix validation completed.")
    print(f"Production config target met: {'✅' if results['target_met'] else '❌'}")