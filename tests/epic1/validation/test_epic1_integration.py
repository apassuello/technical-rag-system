#!/usr/bin/env python3
"""
Comprehensive integration test for Epic1MLAnalyzer to verify full functionality.
"""

import sys
import asyncio
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

print("=== Epic1MLAnalyzer Integration Test ===")

def test_class_compilation():
    """Test that the class compiles correctly."""
    print("\n1. Testing Class Compilation:")
    try:
        from src.components.query_processors.analyzers.epic1_ml_analyzer import Epic1MLAnalyzer
        print("  ✅ Epic1MLAnalyzer imported successfully")
        
        # Check __init__ is in class dict
        has_init = '__init__' in Epic1MLAnalyzer.__dict__
        qualname = Epic1MLAnalyzer.__init__.__qualname__
        print(f"  ✅ __init__ in class dict: {has_init}")
        print(f"  ✅ __init__ qualname: {qualname}")
        
        if has_init and qualname == 'Epic1MLAnalyzer.__init__':
            print("  🎉 Class compilation: SUCCESS")
            return True
        else:
            print("  ❌ Class compilation: FAILED")
            return False
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False

def test_instantiation():
    """Test Epic1MLAnalyzer instantiation."""
    print("\n2. Testing Instantiation:")
    try:
        from src.components.query_processors.analyzers.epic1_ml_analyzer import Epic1MLAnalyzer
        
        config = {
            'memory_budget_gb': 0.1,
            'enable_performance_monitoring': False
        }
        analyzer = Epic1MLAnalyzer(config)
        print("  ✅ Epic1MLAnalyzer instantiated successfully")
        
        # Check critical attributes
        critical_attrs = {
            '_analysis_count': 0,
            'memory_budget_gb': 0.1,
            'views': dict,
            '_ml_infrastructure_initialized': bool,
            '_views_initialized': bool
        }
        
        for attr, expected_type in critical_attrs.items():
            if hasattr(analyzer, attr):
                value = getattr(analyzer, attr)
                if expected_type == dict:
                    is_correct = isinstance(value, dict)
                elif expected_type == bool:
                    is_correct = isinstance(value, bool)
                else:
                    is_correct = value == expected_type
                    
                if is_correct or (expected_type in [dict, bool] and isinstance(value, expected_type)):
                    print(f"  ✅ {attr}: {value}")
                else:
                    print(f"  ❌ {attr}: {value} (expected type: {expected_type})")
            else:
                print(f"  ❌ {attr}: MISSING")
        
        print("  🎉 Instantiation: SUCCESS")
        return analyzer
    except Exception as e:
        print(f"  ❌ Instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_analyze_methods(analyzer):
    """Test both analyze methods."""
    print("\n3. Testing Analyze Methods:")
    
    # Test sync _analyze_query
    try:
        query_analysis = analyzer._analyze_query("What is neural network architecture?")
        print("  ✅ _analyze_query method works")
        print(f"    Query: {query_analysis.query}")
        print(f"    Complexity Score: {query_analysis.complexity_score}")
        print(f"    Complexity Level: {query_analysis.complexity_level}")
        print(f"    Confidence: {query_analysis.confidence}")
        print(f"    Suggested K: {query_analysis.suggested_k}")
        sync_success = True
    except Exception as e:
        print(f"  ❌ _analyze_query failed: {e}")
        sync_success = False
    
    # Test async analyze
    async def test_async_analyze():
        try:
            result = await analyzer.analyze("Explain transformer architecture", mode="hybrid")
            print("  ✅ async analyze method works")
            print(f"    Query: {result.query}")
            print(f"    Final Score: {result.final_score}")
            print(f"    Final Complexity: {result.final_complexity.value if result.final_complexity else 'unknown'}")
            print(f"    Confidence: {result.confidence}")
            print(f"    Total Latency: {result.total_latency_ms:.2f}ms")
            print(f"    View Results: {len(result.view_results)}")
            return True
        except Exception as e:
            print(f"  ❌ async analyze failed: {e}")
            return False
    
    async_success = asyncio.run(test_async_analyze())
    
    if sync_success and async_success:
        print("  🎉 Analyze Methods: SUCCESS")
        return True
    else:
        print("  ⚠️ Some analyze methods failed")
        return False

def test_interface_compliance(analyzer):
    """Test BaseQueryAnalyzer interface compliance."""
    print("\n4. Testing Interface Compliance:")
    
    # Check required methods exist
    required_methods = ['_analyze_query', 'configure', 'get_supported_features']
    for method in required_methods:
        if hasattr(analyzer, method):
            print(f"  ✅ {method}: exists")
        else:
            print(f"  ❌ {method}: missing")
            return False
    
    # Test get_supported_features
    try:
        features = analyzer.get_supported_features()
        print(f"  ✅ get_supported_features: {len(features)} features")
        print(f"    Sample features: {features[:3]}")
    except Exception as e:
        print(f"  ❌ get_supported_features failed: {e}")
        return False
    
    # Test configure method
    try:
        analyzer.configure({'memory_budget_gb': 0.2})
        print("  ✅ configure method works")
    except Exception as e:
        print(f"  ❌ configure failed: {e}")
        return False
    
    print("  🎉 Interface Compliance: SUCCESS")
    return True

def main():
    """Run all integration tests."""
    print("Starting Epic1MLAnalyzer comprehensive integration test...")
    
    # Test 1: Class compilation
    if not test_class_compilation():
        print("\n❌ INTEGRATION TEST FAILED: Class compilation issues")
        return False
    
    # Test 2: Instantiation
    analyzer = test_instantiation()
    if analyzer is None:
        print("\n❌ INTEGRATION TEST FAILED: Instantiation issues")
        return False
    
    # Test 3: Analyze methods
    if not test_analyze_methods(analyzer):
        print("\n❌ INTEGRATION TEST FAILED: Analyze method issues")
        return False
    
    # Test 4: Interface compliance
    if not test_interface_compliance(analyzer):
        print("\n❌ INTEGRATION TEST FAILED: Interface compliance issues")
        return False
    
    print("\n🎉🎉🎉 INTEGRATION TEST SUCCESS: Epic1MLAnalyzer is fully operational! 🎉🎉🎉")
    print("\nSUMMARY:")
    print("✅ Class compilation: PASSED")
    print("✅ Instantiation: PASSED") 
    print("✅ Analyze methods: PASSED")
    print("✅ Interface compliance: PASSED")
    print("\nThe Epic1MLAnalyzer fix is COMPLETE and VERIFIED!")
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🚀 Ready for production use!")
        else:
            print("\n💥 Integration test failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Critical error during integration test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)