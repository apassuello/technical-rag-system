#!/usr/bin/env python3
"""
Epic 1 Fixes Validation Test

This script validates that the Epic 1 component fixes are working correctly
by testing the improved vocabulary, clause detection, and feature extraction.
"""

import time
from typing import Dict, List, Tuple

from src.components.query_processors.analyzers.utils import TechnicalTermManager, SyntacticParser
from src.components.query_processors.analyzers.components import FeatureExtractor, ComplexityClassifier

def test_technical_term_improvements():
    """Test that TechnicalTermManager now detects more terms."""
    print("=" * 80)
    print("TESTING TECHNICAL TERM MANAGER IMPROVEMENTS")
    print("=" * 80)
    
    manager = TechnicalTermManager({
        'domains': ['ml', 'rag', 'llm', 'general_technical'],
        'min_term_length': 3,
        'case_sensitive': False
    })
    
    # Test complex query that was previously failing
    test_query = (
        "Compare and contrast different neural reranking strategies and their impact "
        "on retrieval quality in domain-specific technical documentation, considering "
        "both computational efficiency and accuracy trade-offs"
    )
    
    print(f"Test Query: {test_query}")
    print(f"Total vocabulary size: {len(manager.terms)} terms")
    
    # Expected technical terms that should now be detected
    expected_terms = [
        'neural', 'reranking', 'strategies', 'impact', 'retrieval', 'quality',
        'domain', 'specific', 'technical', 'documentation', 'computational',
        'efficiency', 'accuracy', 'trade-offs'
    ]
    
    print(f"\nExpected technical terms: {expected_terms}")
    
    # Test individual term detection
    detected_terms = []
    missed_terms = []
    
    for term in expected_terms:
        if manager.contains_term(term):
            detected_terms.append(term)
        else:
            missed_terms.append(term)
    
    print(f"\n✓ Detected terms ({len(detected_terms)}/{len(expected_terms)}): {detected_terms}")
    if missed_terms:
        print(f"✗ Missed terms: {missed_terms}")
    
    # Calculate detection rate
    detection_rate = len(detected_terms) / len(expected_terms)
    print(f"\nDetection Rate: {detection_rate:.1%} (Target: >80%)")
    
    # Test full extraction
    extracted_terms = manager.extract_terms(test_query)
    density = manager.calculate_density(test_query)
    
    print(f"\nExtracted terms: {extracted_terms}")
    print(f"Technical density: {density:.3f} (Previous: ~0.125, Target: >0.5)")
    
    # Performance test
    start_time = time.time()
    for _ in range(100):
        manager.extract_terms(test_query)
    avg_time = (time.time() - start_time) * 10  # ms per call
    print(f"Average extraction time: {avg_time:.2f}ms (Target: <5ms)")

def test_syntactic_parser_improvements():
    """Test that SyntacticParser now properly counts clauses."""
    print("\n" + "=" * 80)
    print("TESTING SYNTACTIC PARSER IMPROVEMENTS")
    print("=" * 80)
    
    parser = SyntacticParser()
    
    # Test cases with expected clause counts
    test_cases = [
        ("What is RAG?", 1),
        ("How does the retriever work in a RAG system?", 1), 
        ("First clause, and second clause", 2),
        ("If this, then that, otherwise something else", 3),
        ("Compare and contrast different neural reranking strategies and their impact on retrieval quality", 2),
        ("Complex query, which has multiple clauses, and uses various techniques", 3)
    ]
    
    results = []
    
    for query, expected_clauses in test_cases:
        actual_clauses = parser.count_clauses(query)
        correct = actual_clauses == expected_clauses
        results.append((query, expected_clauses, actual_clauses, correct))
        
        status = "✓" if correct else "✗"
        print(f"{status} '{query[:50]}...' Expected: {expected_clauses}, Got: {actual_clauses}")
    
    accuracy = sum(1 for _, _, _, correct in results if correct) / len(results)
    print(f"\nClause Detection Accuracy: {accuracy:.1%} (Target: >90%)")

    # Test complex analysis
    complex_query = test_cases[-1][0]
    analysis = parser.analyze_complexity(complex_query)
    features = parser.get_complexity_features(complex_query)

    print(f"\nComplex Query Analysis:")
    print(f"  Query: {complex_query}")
    print(f"  Clause count: {analysis['clause_count']}")
    print(f"  Nesting depth: {analysis['nesting_depth']}")
    print(f"  Conjunction count: {analysis['conjunction_count']}")
    print(f"  Syntactic complexity: {features['syntactic_score']:.3f}")

def test_feature_extractor_improvements():
    """Test that FeatureExtractor now provides all required features."""
    print("\n" + "=" * 80)
    print("TESTING FEATURE EXTRACTOR IMPROVEMENTS")
    print("=" * 80)
    
    config = {
        'technical_terms': {
            'domains': ['ml', 'rag', 'llm', 'general_technical'],
            'min_term_length': 3
        },
        'enable_entity_extraction': True
    }
    
    extractor = FeatureExtractor(config)
    
    # Test queries with different complexity levels
    test_queries = [
        ("What is RAG?", "simple"),
        ("How does the retriever work in a RAG system?", "medium"),
        ("Compare and contrast different neural reranking strategies and their impact on retrieval quality in domain-specific technical documentation, considering both computational efficiency and accuracy trade-offs", "complex")
    ]
    
    for query, expected_level in test_queries:
        print(f"\n--- Testing: {query[:60]}... (Expected: {expected_level}) ---")
        
        features = extractor.extract(query)
        
        # Check all feature categories exist
        required_categories = [
            'length_features', 'syntactic_features', 'vocabulary_features',
            'question_features', 'ambiguity_features', 'composite_features'
        ]
        
        for category in required_categories:
            if category not in features:
                print(f"✗ Missing category: {category}")
            else:
                print(f"✓ Category present: {category}")
        
        # Check specific features that were missing
        vocab_features = features.get('vocabulary_features', {})
        question_features = features.get('question_features', {})
        ambiguity_features = features.get('ambiguity_features', {})
        composite_features = features.get('composite_features', {})
        
        print(f"  Technical density: {vocab_features.get('technical_density', 'MISSING'):.3f}")
        print(f"  Is technical query: {vocab_features.get('is_technical_query', 'MISSING')}")
        print(f"  Type complexity: {question_features.get('type_complexity', 'MISSING'):.3f}")
        print(f"  Is complex question: {question_features.get('is_complex_question', 'MISSING')}")
        print(f"  Ambiguity score: {ambiguity_features.get('ambiguity_score', 'MISSING'):.3f}")
        print(f"  Overall complexity: {composite_features.get('overall_complexity', 'MISSING'):.3f}")
        
        # Count features that are no longer MISSING or 0.000
        total_features = 0
        working_features = 0
        
        for category_name, category_features in features.items():
            if isinstance(category_features, dict):
                for key, value in category_features.items():
                    if key != 'raw_query':
                        total_features += 1
                        if isinstance(value, (int, float)) and value != 0.0:
                            working_features += 1
                        elif isinstance(value, str) and value != 'MISSING':
                            working_features += 1
                        elif isinstance(value, list):
                            working_features += 1
        
        feature_success_rate = working_features / max(1, total_features)
        print(f"  Feature success rate: {feature_success_rate:.1%} ({working_features}/{total_features})")

def test_complexity_classifier_improvements():
    """Test that ComplexityClassifier now produces realistic scores."""
    print("\n" + "=" * 80)
    print("TESTING COMPLEXITY CLASSIFIER IMPROVEMENTS")
    print("=" * 80)
    
    # Create extractor and classifier
    extractor_config = {
        'technical_terms': {
            'domains': ['ml', 'rag', 'llm', 'general_technical'],
            'min_term_length': 3
        },
        'enable_entity_extraction': True
    }
    
    classifier_config = {
        'weights': {
            'length': 0.20,
            'syntactic': 0.25,
            'vocabulary': 0.30,
            'question': 0.15,
            'ambiguity': 0.10
        },
        'thresholds': {
            'simple': 0.30,
            'complex': 0.50
        }
    }
    
    extractor = FeatureExtractor(extractor_config)
    classifier = ComplexityClassifier(classifier_config)
    
    # Test queries with expected complexity levels
    test_cases = [
        ("What is RAG?", "simple", 0.20),
        ("How does the retriever work in a RAG system?", "simple", 0.25),
        ("Compare and contrast different neural reranking strategies and their impact on retrieval quality in domain-specific technical documentation, considering both computational efficiency and accuracy trade-offs", "complex", 0.55)
    ]
    
    results = []
    
    for query, expected_level, expected_score in test_cases:
        print(f"\n--- Query: {query[:50]}... ---")
        print(f"Expected: {expected_level} (~{expected_score:.2f})")
        
        # Extract features
        features = extractor.extract(query)
        
        # Classify
        classification = classifier.classify(features)
        
        print(f"Actual: {classification['complexity_level']} ({classification['complexity_score']:.3f})")
        print(f"Confidence: {classification['confidence']:.3f}")
        
        # Check breakdown
        print("Score breakdown:")
        for category, score in classification['breakdown'].items():
            weight = classifier.weights.get(category, 0.0)
            print(f"  {category}: {score:.3f} × {weight:.2f} = {score * weight:.3f}")
        
        # Check if level matches expectation
        level_correct = classification['complexity_level'] == expected_level
        score_reasonable = abs(classification['complexity_score'] - expected_score) < 0.3
        
        results.append({
            'query': query,
            'expected_level': expected_level,
            'actual_level': classification['complexity_level'],
            'expected_score': expected_score,
            'actual_score': classification['complexity_score'],
            'level_correct': level_correct,
            'score_reasonable': score_reasonable
        })
        
        status = "✓" if level_correct and score_reasonable else "✗"
        print(f"{status} Classification: {'Correct' if level_correct else 'Incorrect'}, Score: {'Reasonable' if score_reasonable else 'Off'}")
    
    # Calculate accuracy
    level_accuracy = sum(1 for r in results if r['level_correct']) / len(results)
    score_accuracy = sum(1 for r in results if r['score_reasonable']) / len(results)
    
    print(f"\nClassification Results:")
    print(f"Level Accuracy: {level_accuracy:.1%} (Target: >85%)")
    print(f"Score Reasonableness: {score_accuracy:.1%} (Target: >80%)")

def test_end_to_end_performance():
    """Test overall system performance improvements."""
    print("\n" + "=" * 80)
    print("TESTING END-TO-END PERFORMANCE")
    print("=" * 80)
    
    # Performance test with timing
    test_query = "How can we optimize transformer-based RAG systems for production deployment with minimal latency?"
    
    # Initialize components
    extractor = FeatureExtractor({
        'technical_terms': {
            'domains': ['ml', 'rag', 'llm', 'general_technical'],
        }
    })
    classifier = ComplexityClassifier()
    
    # Run multiple iterations for performance measurement
    iterations = 50
    times = []
    
    print(f"Running {iterations} iterations for performance testing...")
    
    for i in range(iterations):
        start_time = time.time()
        
        # Full pipeline
        features = extractor.extract(test_query)
        classification = classifier.classify(features)
        
        end_time = time.time()
        times.append((end_time - start_time) * 1000)  # Convert to ms
    
    avg_time = sum(times) / len(times)
    p95_time = sorted(times)[int(0.95 * len(times))]
    
    print(f"\nPerformance Results:")
    print(f"Average time: {avg_time:.1f}ms")
    print(f"P95 time: {p95_time:.1f}ms (Target: <50ms)")
    print(f"Classification: {classification['complexity_level']} (score: {classification['complexity_score']:.3f})")

def main():
    """Run all validation tests."""
    print("EPIC 1 FIXES VALIDATION")
    print("Testing improvements to TechnicalTermManager, SyntacticParser, FeatureExtractor, and ComplexityClassifier")
    print()
    
    results = {}
    
    # Run all tests
    try:
        results['technical_terms'] = test_technical_term_improvements()
        results['syntactic_parser'] = test_syntactic_parser_improvements()
        results['feature_extractor'] = test_feature_extractor_improvements()
        results['complexity_classifier'] = test_complexity_classifier_improvements()
        results['performance'] = test_end_to_end_performance()
        
        # Summary
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        
        print(f"Technical Term Detection: {results['technical_terms']['detection_rate']:.1%} (Target: >80%)")
        print(f"Technical Density: {results['technical_terms']['technical_density']:.3f} (Target: >0.5)")
        print(f"Clause Detection Accuracy: {results['syntactic_parser']['clause_accuracy']:.1%} (Target: >90%)")
        print(f"Classification Level Accuracy: {results['complexity_classifier']['level_accuracy']:.1%} (Target: >85%)")
        print(f"End-to-End Performance: {results['performance']['p95_time_ms']:.1f}ms (Target: <50ms)")
        
        # Overall success assessment
        success_criteria = [
            results['technical_terms']['detection_rate'] > 0.8,
            results['technical_terms']['technical_density'] > 0.5,
            results['syntactic_parser']['clause_accuracy'] > 0.9,
            results['complexity_classifier']['level_accuracy'] > 0.85,
            results['performance']['p95_time_ms'] < 50
        ]
        
        success_rate = sum(success_criteria) / len(success_criteria)
        print(f"\nOverall Success Rate: {success_rate:.1%} ({sum(success_criteria)}/{len(success_criteria)} criteria met)")
        
        if success_rate >= 0.8:
            print("🎉 EPIC 1 FIXES VALIDATION PASSED!")
        else:
            print("⚠️  Some issues remain - additional fixes needed")
            
    except Exception as e:
        print(f"Error during validation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()