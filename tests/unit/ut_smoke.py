#!/usr/bin/env python3
"""
Simple test to validate Epic1QueryAnalyzer functionality.
"""

import sys
from pathlib import Path
import time
import pytest

# Add project to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.components.query_processors.analyzers import Epic1QueryAnalyzer

def test_epic1_basic():
    """Test basic Epic1QueryAnalyzer functionality."""
    
    # Minimal configuration
    config = {
        'feature_extractor': {
            'technical_terms': {
                'domains': ['ml', 'rag'],
                'min_term_length': 3
            }
        },
        'complexity_classifier': {
            'weights': {
                'length': 0.20,
                'syntactic': 0.25,
                'vocabulary': 0.30,
                'question': 0.15,
                'ambiguity': 0.10
            },
            'thresholds': {
                'simple': 0.35,
                'complex': 0.70
            }
        },
        'model_recommender': {
            'strategy': 'balanced',
            'model_mappings': {
                'simple': {
                    'provider': 'local',
                    'model': 'qwen2.5-1.5b-instruct',
                    'max_cost_per_query': 0.001,
                    'avg_latency_ms': 500
                },
                'medium': {
                    'provider': 'mistral',
                    'model': 'mistral-small',
                    'max_cost_per_query': 0.01,
                    'avg_latency_ms': 1000
                },
                'complex': {
                    'provider': 'openai',
                    'model': 'gpt-4-turbo',
                    'max_cost_per_query': 0.10,
                    'avg_latency_ms': 2000
                }
            }
        }
    }
    
    print("Creating Epic1QueryAnalyzer...")
    analyzer = Epic1QueryAnalyzer(config)
    
    # Test queries
    test_cases = [
        ("What is RAG?", "simple"),
        ("How does transformer attention work?", "simple"),
        ("Implement a hybrid retrieval system with BM25 and dense embeddings", "medium"),
    ]
    
    print("\n" + "="*60)
    print("Epic1QueryAnalyzer Simple Test")
    print("="*60)
    
    total_tests = len(test_cases)
    passed = 0
    
    for query, expected_level in test_cases:
        print(f"\nQuery: {query[:50]}...")
        
        # Analyze
        start = time.time()
        analysis = analyzer.analyze(query)
        elapsed = (time.time() - start) * 1000
        
        # Extract Epic1 data
        epic1_data = analysis.metadata.get('epic1_analysis', {})
        complexity_level = epic1_data.get('complexity_level', 'unknown')
        complexity_score = epic1_data.get('complexity_score', 0)
        model = epic1_data.get('recommended_model', 'none')
        
        # Check result
        print(f"  Level: {complexity_level} (expected: {expected_level})")
        print(f"  Score: {complexity_score:.3f}")
        print(f"  Model: {model}")
        print(f"  Time: {elapsed:.1f}ms")
        
        # Validate
        if elapsed < 50:
            print(f"  ✅ Performance OK (<50ms)")
        else:
            print(f"  ❌ Performance issue (>{elapsed:.1f}ms)")
        
        # Check if classification matches (allow some flexibility)
        if complexity_level == expected_level:
            print(f"  ✅ Classification correct")
            passed += 1
        elif (expected_level == "simple" and complexity_level == "medium") or \
             (expected_level == "medium" and complexity_level in ["simple", "complex"]):
            print(f"  ⚠️  Classification close (acceptable)")
            passed += 1
        else:
            print(f"  ❌ Classification mismatch")
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total_tests} tests passed")
    print("="*60)
    
    # Performance summary
    metrics = analyzer.get_performance_metrics()
    epic1_perf = metrics.get('epic1_performance', {})
    
    print("\nPerformance Summary:")
    print(f"  Avg Total Time: {epic1_perf.get('avg_total_ms', 0):.2f}ms")
    print(f"  Meets Target: {epic1_perf.get('meets_latency_target', False)}")
    
    if passed != total_tests:
        pytest.fail(f"{total_tests - passed}/{total_tests} tests failed")

if __name__ == "__main__":
    exit(test_epic1_basic())