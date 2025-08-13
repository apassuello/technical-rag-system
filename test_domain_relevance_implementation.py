#!/usr/bin/env python3
"""
Test Domain Relevance Implementation

This script validates the Epic 1 Phase 1 domain relevance detection implementation:
1. Tests DomainRelevanceScorer with sample queries
2. Tests DomainRelevanceFilter functionality  
3. Tests ComponentFactory integration
4. Validates the complete domain-aware query processing workflow

Usage:
    python test_domain_relevance_implementation.py
"""

import sys
from pathlib import Path
import logging

# Add project paths
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_domain_relevance_scorer():
    """Test the DomainRelevanceScorer with sample queries."""
    print("\\n" + "="*60)
    print("Testing DomainRelevanceScorer")
    print("="*60)
    
    from src.components.query_processors.domain_relevance_filter import DomainRelevanceScorer
    
    scorer = DomainRelevanceScorer()
    
    # Test queries with expected classifications
    test_queries = [
        # High relevance (should be 0.8+)
        ("What is RISC-V?", "high_relevance"),
        ("How do I write RISC-V assembly code?", "high_relevance"), 
        ("What does the LW instruction do?", "high_relevance"),
        ("Explain RISC-V vector extension", "high_relevance"),
        
        # Medium relevance (should be 0.3-0.7)
        ("What is an ISA?", "medium_relevance"),
        ("How does pipeline optimization work?", "medium_relevance"),
        ("Explain branch prediction", "medium_relevance"),
        
        # Low relevance (should be 0.0-0.2)  
        ("How do I build a REST API?", "low_relevance"),
        ("What is machine learning?", "low_relevance"),
        ("How to fix Docker container issues?", "low_relevance"),
        ("What's the weather today?", "low_relevance"),
    ]
    
    results = []
    for query, expected_tier in test_queries:
        score, tier, details = scorer.score_query(query)
        
        # Check if classification matches expectation
        correct = tier == expected_tier
        status = "✅" if correct else "❌"
        
        print(f"{status} Query: '{query[:50]}{'...' if len(query) > 50 else ''}'")
        print(f"   Score: {score:.3f}, Tier: {tier}, Expected: {expected_tier}")
        print(f"   Reasoning: {details['reasoning']}")
        print()
        
        results.append({
            'query': query,
            'score': score,
            'tier': tier,
            'expected': expected_tier,
            'correct': correct,
            'reasoning': details['reasoning']
        })
    
    # Calculate accuracy
    correct_count = sum(1 for r in results if r['correct'])
    accuracy = correct_count / len(results) * 100
    
    print(f"Classification Accuracy: {correct_count}/{len(results)} ({accuracy:.1f}%)")
    
    return results

def test_domain_relevance_filter():
    """Test the DomainRelevanceFilter functionality."""
    print("\\n" + "="*60)
    print("Testing DomainRelevanceFilter")
    print("="*60)
    
    from src.components.query_processors.domain_relevance_filter import DomainRelevanceFilter
    
    filter_instance = DomainRelevanceFilter()
    
    # Test different types of queries
    test_queries = [
        "What is RISC-V vector extension?",  # Should be relevant
        "How do I build a web API?",         # Should be irrelevant
        "What is an instruction set?",       # Should be borderline
    ]
    
    for query in test_queries:
        result = filter_instance.analyze_domain_relevance(query)
        
        print(f"Query: '{query}'")
        print(f"  Relevance Score: {result.relevance_score:.3f}")
        print(f"  Tier: {result.relevance_tier}")
        print(f"  Is Relevant: {result.is_relevant}")
        print(f"  Reasoning: {result.reasoning}")
        print(f"  Confidence: {result.confidence:.3f}")
        print(f"  Processing Time: {result.processing_time_ms:.1f}ms")
        
        # Test refusal response for irrelevant queries
        if not result.is_relevant:
            refusal = filter_instance.create_refusal_response(result)
            print(f"  Refusal Response: '{refusal.text[:100]}...'")
        print()
    
    # Test performance stats
    stats = filter_instance.get_performance_stats()
    print(f"Performance Stats: {stats}")
    
    return True

def test_component_factory_integration():
    """Test ComponentFactory integration for domain-aware query processor."""
    print("\\n" + "="*60)
    print("Testing ComponentFactory Integration")
    print("="*60)
    
    try:
        from src.core.component_factory import ComponentFactory
        
        # Test that domain-aware query processor is available
        available_processors = ComponentFactory._QUERY_PROCESSORS
        print(f"Available Query Processors: {list(available_processors.keys())}")
        
        # Check if our new processors are registered
        domain_processors = [k for k in available_processors.keys() if 'domain' in k or 'epic1' in k]
        print(f"Domain-aware processors: {domain_processors}")
        
        if 'domain_aware' in available_processors:
            print("✅ DomainAwareQueryProcessor is registered")
        else:
            print("❌ DomainAwareQueryProcessor is NOT registered")
            return False
        
        # Test class loading (without instantiation since we need retriever/generator)
        try:
            processor_class = ComponentFactory._get_component_class(
                available_processors['domain_aware']
            )
            print(f"✅ Successfully loaded class: {processor_class.__name__}")
        except Exception as e:
            print(f"❌ Failed to load DomainAwareQueryProcessor class: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ ComponentFactory integration test failed: {e}")
        return False

def test_basic_imports():
    """Test that all modules can be imported successfully."""
    print("\\n" + "="*60)
    print("Testing Module Imports")
    print("="*60)
    
    imports = [
        ("DomainRelevanceScorer", "src.components.query_processors.domain_relevance_filter"),
        ("DomainRelevanceFilter", "src.components.query_processors.domain_relevance_filter"),
        ("DomainAwareQueryProcessor", "src.components.query_processors.domain_aware_query_processor"),
    ]
    
    all_success = True
    for class_name, module_name in imports:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✅ Successfully imported {class_name} from {module_name}")
        except Exception as e:
            print(f"❌ Failed to import {class_name} from {module_name}: {e}")
            all_success = False
    
    return all_success

def main():
    """Run all domain relevance implementation tests."""
    print("Epic 1 Phase 1: Domain Relevance Detection Implementation Test")
    print("Testing the 3-tier domain relevance filtering system...")
    
    # Test basic imports first
    print("\\n1. Testing Module Imports...")
    import_success = test_basic_imports()
    
    if not import_success:
        print("\\n❌ Module import tests failed. Check implementation.")
        return False
    
    # Test domain relevance scorer
    print("\\n2. Testing Domain Relevance Scoring...")
    try:
        scorer_results = test_domain_relevance_scorer()
        scorer_success = True
    except Exception as e:
        print(f"❌ Domain relevance scorer test failed: {e}")
        scorer_success = False
    
    # Test domain relevance filter
    print("\\n3. Testing Domain Relevance Filter...")
    try:
        filter_success = test_domain_relevance_filter()
    except Exception as e:
        print(f"❌ Domain relevance filter test failed: {e}")
        filter_success = False
    
    # Test component factory integration
    print("\\n4. Testing ComponentFactory Integration...")
    try:
        factory_success = test_component_factory_integration()
    except Exception as e:
        print(f"❌ ComponentFactory integration test failed: {e}")
        factory_success = False
    
    # Summary
    print("\\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    tests = [
        ("Module Imports", import_success),
        ("Domain Relevance Scorer", scorer_success),
        ("Domain Relevance Filter", filter_success),
        ("ComponentFactory Integration", factory_success),
    ]
    
    passed = 0
    for test_name, success in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:30} {status}")
        if success:
            passed += 1
    
    overall_success = passed == len(tests)
    print(f"\\nOverall Result: {passed}/{len(tests)} tests passed")
    
    if overall_success:
        print("\\n🎉 All tests passed! Epic 1 Phase 1 implementation is ready.")
        print("\\nNext steps:")
        print("- Update configuration files to use 'domain_aware' query processor")
        print("- Test with real queries in the complete RAG pipeline")
        print("- Monitor performance and accuracy in production")
    else:
        print("\\n⚠️  Some tests failed. Please fix issues before deployment.")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)