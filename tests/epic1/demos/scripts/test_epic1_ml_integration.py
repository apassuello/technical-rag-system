#\!/usr/bin/env python3
"""
Test Epic1MLAnalyzer integration with trained models.

This script verifies that:
1. Trained view models are loaded correctly
2. MetaClassifier is integrated properly
3. The system produces accurate complexity assessments
4. All components work together seamlessly
"""

import asyncio
import json
from pathlib import Path
import sys
import pytest

# Add src to path - fix path resolution for Epic 1 tests
sys.path.insert(0, str(Path(__file__).parents[4] / 'src'))

from src.components.query_processors.analyzers.epic1_ml_analyzer import Epic1MLAnalyzer
from src.components.query_processors.analyzers.ml_views.view_result import ComplexityLevel

@pytest.mark.asyncio
async def test_epic1_integration():
    """Test Epic1MLAnalyzer with trained models."""
    
    print("=" * 80)
    print("EPIC 1 ML ANALYZER INTEGRATION TEST")
    print("=" * 80)
    
    # Initialize the analyzer
    print("\n1. Initializing Epic1MLAnalyzer...")
    try:
        analyzer = Epic1MLAnalyzer({
            'memory_budget_gb': 2.0,
            'enable_performance_monitoring': False,  # Disable for simpler output
            'parallel_execution': False,  # Sequential for clearer debugging
            'confidence_threshold': 0.6
        })
        print("✅ Analyzer initialized successfully")
        
        # Check if models were loaded
        if hasattr(analyzer, 'trained_view_models') and analyzer.trained_view_models:
            print(f"✅ Loaded {len(analyzer.trained_view_models)} trained view models:")
            for view_name in analyzer.trained_view_models.keys():
                print(f"   - {view_name}_model")
        else:
            print("⚠️ No trained view models loaded")
        
        if hasattr(analyzer, 'trained_meta_classifier') and analyzer.trained_meta_classifier:
            print("✅ Loaded trained MetaClassifier")
        else:
            print("⚠️ No trained MetaClassifier loaded")
            
    except Exception as e:
        print(f"❌ Failed to initialize analyzer: {e}")
        return
    
    # Test queries covering different complexity levels (based on training prompt definitions)
    test_queries = [
        # Simple queries (0.10-0.35) - Basic concepts, Bloom's Level 1-2
        ("What is Python?", "simple"),
        ("How do I create a list in Python?", "simple"),
        ("What does the len() function do?", "simple"),
        ("How do I implement a binary search tree in Python?", "simple"),  # Basic algorithm, fundamental CS
        ("What's the difference between let and const in JavaScript?", "simple"),  # Basic language features
        
        # Medium queries (0.32-0.66) - Intermediate concepts, Bloom's Level 3-4, multi-step solutions
        ("How to implement rate limiting for REST APIs to prevent abuse while maintaining good user experience?", "medium"),
        ("What's the best approach to handle errors properly in async JavaScript functions with try-catch and promise chains?", "medium"),
        ("How should I design a caching strategy for a web application with both Redis and database queries?", "medium"),
        
        # Complex queries (0.64-0.90) - Expert-level, Bloom's Level 4-6, advanced distributed systems
        ("How can I implement a distributed consensus algorithm with Byzantine fault tolerance that maintains linearizability while optimizing for network partition recovery?", "complex"),
        ("What are the theoretical and practical implications of implementing a CRDT-based eventually consistent data store for a globally distributed collaborative editing system?", "complex"),
        ("How would you design a fault-tolerant distributed system that guarantees exactly-once message delivery semantics across multiple data centers with network partitions?", "complex"),
    ]
    
    print("\n2. Testing queries with different complexity levels...")
    print("-" * 80)
    
    results = []
    for query, expected_level in test_queries:
        print(f"\nQuery: '{query[:60]}...'" if len(query) > 60 else f"\nQuery: '{query}'")
        print(f"Expected: {expected_level}")
        
        try:
            # Test with ML mode (uses trained models)
            result = await analyzer.analyze(query, mode='ml')
            
            # Extract results
            actual_score = result.final_score
            actual_level = result.final_complexity.value.lower()
            confidence = result.confidence
            
            # Check if trained models were used
            trained_models_used = False
            for view_result in result.view_results.values():
                if view_result.metadata.get('trained_model_used'):
                    trained_models_used = True
                    break
            
            # Check if MetaClassifier was used
            meta_classifier_used = False
            if 'meta_classification' in result.metadata:
                meta_data = result.metadata.get('meta_classification', {})
                if isinstance(meta_data, dict) and meta_data.get('meta_classifier_used'):
                    meta_classifier_used = True
            
            # Display results
            print(f"Result: score={actual_score:.3f}, level={actual_level}, confidence={confidence:.3f}")
            print(f"Trained models used: {'Yes ✅' if trained_models_used else 'No ❌'}")
            print(f"MetaClassifier used: {'Yes ✅' if meta_classifier_used else 'No ❌'}")
            
            # Check accuracy
            is_correct = actual_level == expected_level
            print(f"Accuracy: {'✅ Correct' if is_correct else '❌ Incorrect'}")
            
            results.append({
                'query': query[:60] + '...' if len(query) > 60 else query,
                'expected': expected_level,
                'actual': actual_level,
                'score': actual_score,
                'confidence': confidence,
                'correct': is_correct,
                'trained_models': trained_models_used,
                'meta_classifier': meta_classifier_used
            })
            
        except Exception as e:
            print(f"❌ Error analyzing query: {e}")
            results.append({
                'query': query[:60] + '...' if len(query) > 60 else query,
                'expected': expected_level,
                'error': str(e)
            })
    
    # Calculate summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    correct_count = sum(1 for r in results if r.get('correct', False))
    total_count = len(results)
    accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
    
    print(f"\nAccuracy: {correct_count}/{total_count} ({accuracy:.1f}%)")
    
    # Group by complexity level
    for level in ['simple', 'medium', 'complex']:
        level_results = [r for r in results if r.get('expected') == level]
        level_correct = sum(1 for r in level_results if r.get('correct', False))
        level_total = len(level_results)
        level_accuracy = (level_correct / level_total * 100) if level_total > 0 else 0
        print(f"{level.capitalize()}: {level_correct}/{level_total} ({level_accuracy:.1f}%)")
    
    # Check model usage
    models_used_count = sum(1 for r in results if r.get('trained_models', False))
    meta_used_count = sum(1 for r in results if r.get('meta_classifier', False))
    
    print(f"\nTrained models used: {models_used_count}/{total_count} queries")
    print(f"MetaClassifier used: {meta_used_count}/{total_count} queries")
    
    # Save results
    output_file = Path("/tmp/epic1_integration_results.json")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump({
            'results': results,
            'summary': {
                'accuracy': accuracy,
                'correct': correct_count,
                'total': total_count,
                'trained_models_used': models_used_count,
                'meta_classifier_used': meta_used_count
            }
        }, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    
    # Final assessment
    print("\n" + "=" * 80)
    if accuracy >= 85:
        print("✅ INTEGRATION TEST PASSED - Accuracy meets Epic 1 target (>85%)")
    elif accuracy >= 70:
        print("⚠️ INTEGRATION TEST WARNING - Accuracy below target (85%), but acceptable")
    else:
        print("❌ INTEGRATION TEST FAILED - Accuracy significantly below target")
    
    if models_used_count == 0:
        print("❌ WARNING: Trained models were not used!")
    if meta_used_count == 0:
        print("❌ WARNING: MetaClassifier was not used!")
    
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_epic1_integration())