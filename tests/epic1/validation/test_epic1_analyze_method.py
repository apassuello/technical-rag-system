#!/usr/bin/env python3
"""
Test Epic1MLAnalyzer analyze method functionality.
"""

import sys
import asyncio
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

print("=== Testing Epic1MLAnalyzer Analyze Method ===")

try:
    from src.components.query_processors.analyzers.epic1_ml_analyzer import Epic1MLAnalyzer
    
    # Create analyzer with minimal config
    config = {
        'memory_budget_gb': 0.1,
        'enable_performance_monitoring': False
    }
    analyzer = Epic1MLAnalyzer(config)
    print("✅ Epic1MLAnalyzer created successfully")
    
    # Test async analyze method
    async def test_analyze():
        try:
            result = await analyzer.analyze("What is machine learning?", mode="hybrid")
            print(f"✅ Analyze method executed successfully")
            print(f"  Query: {result.query}")
            print(f"  Final Score: {result.final_score}")
            print(f"  Final Complexity: {result.final_complexity.value if result.final_complexity else 'unknown'}")
            print(f"  Confidence: {result.confidence}")
            print(f"  Analysis Time: {result.total_latency_ms:.2f}ms")
            print(f"  Model Recommendation: {result.metadata.get('model_recommendation', 'unknown')}")
            return True
        except Exception as e:
            print(f"❌ Analyze method failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # Test sync _analyze_query method (BaseQueryAnalyzer interface)
    try:
        query_analysis = analyzer._analyze_query("What is deep learning?")
        print(f"✅ _analyze_query method executed successfully")
        print(f"  Query: {query_analysis.query}")
        print(f"  Complexity Score: {query_analysis.complexity_score}")
        print(f"  Complexity Level: {query_analysis.complexity_level}")
        print(f"  Confidence: {query_analysis.confidence}")
        print(f"  Technical Terms: {query_analysis.technical_terms}")
        print(f"  Entities: {query_analysis.entities}")
        print(f"  Intent Category: {query_analysis.intent_category}")
        print(f"  Suggested K: {query_analysis.suggested_k}")
    except Exception as e:
        print(f"❌ _analyze_query method failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Run async test
    async_success = asyncio.run(test_analyze())
    
    if async_success:
        print("🎉 SUCCESS: Both analyze methods work correctly!")
    else:
        print("⚠️ Async analyze method has issues")
        
except Exception as e:
    print(f"❌ Error during analysis test: {e}")
    import traceback
    traceback.print_exc()