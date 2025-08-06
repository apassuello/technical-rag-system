#!/usr/bin/env python3
"""
Test script for Epic 1 Query Analyzer.

This script validates the Epic1QueryAnalyzer implementation
with various query types and complexities.
"""

import sys
from pathlib import Path
import time

# Add project to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.components.query_processors.analyzers import Epic1QueryAnalyzer


def test_epic1_analyzer():
    """Test Epic 1 Query Analyzer with various queries."""
    
    # Initialize analyzer with configuration
    config = {
        'feature_extractor': {
            'technical_terms': {
                'domains': ['ml', 'rag', 'llm'],
                'min_term_length': 3
            },
            'enable_entity_extraction': True
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
                    'provider': 'ollama',
                    'model': 'llama3.2:3b',
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
    
    analyzer = Epic1QueryAnalyzer(config)
    
    # Test queries of varying complexity
    test_queries = [
        # Simple queries
        "What is RAG?",
        "Define embedding",
        "List the components",
        
        # Medium queries
        "How does the retriever component work in a RAG system?",
        "Explain the difference between dense and sparse retrieval",
        "What are the best practices for chunking documents?",
        
        # Complex queries
        "Compare and contrast different neural reranking strategies and their impact on retrieval quality in domain-specific technical documentation, considering both computational efficiency and accuracy trade-offs",
        "How can we optimize transformer-based models for long-context retrieval while maintaining sub-second latency requirements in production environments?",
        "Implement a hybrid retrieval system that combines BM25, dense embeddings, and cross-encoder reranking with dynamic weight adjustment based on query characteristics"
    ]
    
    print("=" * 80)
    print("Epic 1 Query Analyzer Test")
    print("=" * 80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test {i} ---")
        print(f"Query: {query[:100]}{'...' if len(query) > 100 else ''}")
        print("-" * 40)
        
        # Analyze query
        start_time = time.time()
        analysis = analyzer.analyze(query)
        analysis_time = (time.time() - start_time) * 1000
        
        # Extract Epic 1 metadata
        epic1_data = analysis.metadata.get('epic1_analysis', {})
        
        # Display results
        print(f"Complexity Level: {epic1_data.get('complexity_level', 'N/A')}")
        print(f"Complexity Score: {epic1_data.get('complexity_score', 0):.3f}")
        print(f"Confidence: {epic1_data.get('complexity_confidence', 0):.3f}")
        print(f"Recommended Model: {epic1_data.get('recommended_model', 'N/A')}")
        print(f"Cost Estimate: ${epic1_data.get('cost_estimate', 0):.4f}")
        print(f"Latency Estimate: {epic1_data.get('latency_estimate', 0)}ms")
        print(f"Analysis Time: {analysis_time:.1f}ms")
        
        # Show breakdown
        breakdown = epic1_data.get('complexity_breakdown', {})
        if breakdown:
            print(f"Score Breakdown:")
            for category, score in breakdown.items():
                print(f"  - {category}: {score:.3f}")
        
        # Check if meeting <50ms target
        if analysis_time < 50:
            print("✅ Meets <50ms latency target")
        else:
            print(f"⚠️  Exceeds 50ms target by {analysis_time - 50:.1f}ms")
    
    print("\n" + "=" * 80)
    print("Performance Summary")
    print("=" * 80)
    
    # Get performance metrics
    metrics = analyzer.get_performance_metrics()
    epic1_metrics = metrics.get('epic1_performance', {})
    
    if epic1_metrics:
        print(f"Average Total Time: {epic1_metrics.get('avg_total_ms', 0):.2f}ms")
        print(f"Average Feature Extraction: {epic1_metrics.get('avg_feature_extraction_ms', 0):.2f}ms")
        print(f"Average Classification: {epic1_metrics.get('avg_complexity_classification_ms', 0):.2f}ms")
        print(f"Average Recommendation: {epic1_metrics.get('avg_model_recommendation_ms', 0):.2f}ms")
        print(f"Meets Latency Target: {epic1_metrics.get('meets_latency_target', False)}")
    
    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    test_epic1_analyzer()