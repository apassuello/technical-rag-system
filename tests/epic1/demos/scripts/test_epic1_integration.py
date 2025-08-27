#!/usr/bin/env python3
"""
Epic 1 Integration Test Script.

Tests the end-to-end Epic 1 Multi-Model Answer Generator functionality.
"""

import sys
import time
import logging
from pathlib import Path

# Add src to path - fix path resolution for Epic 1 tests
sys.path.insert(0, str(Path(__file__).parents[4] / 'src'))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_epic1_component_factory():
    """Test Epic1AnswerGenerator creation via ComponentFactory."""
    print("🏭 Testing Epic1 ComponentFactory Integration...")
    
    try:
        from src.core.component_factory import ComponentFactory
        
        # Test factory registration
        factory = ComponentFactory()
        print("✅ ComponentFactory initialized")
        
        # Test Epic1 generator creation
        epic1_generator = factory.create_generator("epic1")
        print(f"✅ Epic1AnswerGenerator created: {type(epic1_generator).__name__}")
        
        # Test generator info
        info = epic1_generator.get_generator_info()
        print(f"✅ Generator info retrieved:")
        print(f"   Type: {info.get('type')}")
        print(f"   Routing enabled: {info.get('routing_enabled')}")
        print(f"   Epic1 available: {info.get('epic1_available')}")
        
        return epic1_generator
        
    except Exception as e:
        print(f"❌ ComponentFactory test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_epic1_configuration_loading():
    """Test Epic1 configuration loading."""
    print("\n⚙️  Testing Epic1 Configuration Loading...")
    
    try:
        from src.core.config import load_config
        
        # Load Epic1 configuration
        config_path = Path("config/epic1_multi_model.yaml")
        if config_path.exists():
            config = load_config(config_path)
            print("✅ Epic1 configuration loaded successfully")
            
            # Check key configuration sections
            answer_gen_config = config.answer_generator
            print(f"   Answer generator type: {answer_gen_config.type}")
            
            routing_config = answer_gen_config.config.get('routing', {})
            print(f"   Routing enabled: {routing_config.get('enabled')}")
            print(f"   Default strategy: {routing_config.get('default_strategy')}")
            
            return config
        else:
            print(f"❌ Configuration file not found: {config_path}")
            return None
            
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_epic1_with_config():
    """Test Epic1AnswerGenerator with full configuration."""
    print("\n🚀 Testing Epic1 with Full Configuration...")
    
    try:
        from src.core.component_factory import ComponentFactory
        from src.core.config import load_config
        
        # Load configuration
        config_path = Path("config/epic1_multi_model.yaml")
        if not config_path.exists():
            print("❌ Epic1 configuration not found, using default config")
            config = None
        else:
            config = load_config(config_path)
            print("✅ Configuration loaded")
        
        # Create factory and generator
        factory = ComponentFactory()
        
        # Get answer generator config
        if config:
            answer_gen_config = config.answer_generator.config
        else:
            answer_gen_config = {}
        
        # Create Epic1 generator with configuration
        epic1_generator = factory.create_generator("epic1", config=answer_gen_config)
        print(f"✅ Epic1AnswerGenerator created with configuration")
        
        # Test generator capabilities
        info = epic1_generator.get_generator_info()
        print(f"   Generator type: {info.get('type')}")
        print(f"   Routing enabled: {info.get('routing_enabled')}")
        
        if info.get('routing_enabled'):
            routing_stats = epic1_generator.get_routing_statistics()
            print(f"   Routing decisions made: {routing_stats.get('total_routing_decisions', 0)}")
            
            cost_breakdown = epic1_generator.get_cost_breakdown()
            if cost_breakdown:
                print(f"   Cost tracking enabled: ✅")
            else:
                print(f"   Cost tracking: Not yet used")
        
        return epic1_generator
        
    except Exception as e:
        print(f"❌ Epic1 configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_query_complexity_analyzer():
    """Test the Epic1 Query Complexity Analyzer directly."""
    print("\n🧠 Testing Epic1 Query Complexity Analyzer...")
    
    try:
        from src.components.query_processors.analyzers.epic1_query_analyzer import Epic1QueryAnalyzer
        
        # Create analyzer
        analyzer = Epic1QueryAnalyzer()
        print("✅ Epic1QueryAnalyzer created")
        
        # Test queries of different complexity
        test_queries = [
            "What is 2+2?",  # Simple
            "How does OAuth 2.0 authentication work with JWT tokens?",  # Medium
            "Design a distributed microservices architecture with event-driven patterns for real-time data processing and explain the trade-offs between consistency models"  # Complex
        ]
        
        for i, query in enumerate(test_queries):
            start_time = time.time()
            analysis = analyzer.analyze(query)
            analysis_time = (time.time() - start_time) * 1000
            
            print(f"   Query {i+1}: {query[:50]}...")
            print(f"     Complexity level: {analysis.complexity_level}")
            print(f"     Complexity score: {analysis.complexity_score:.3f}")
            print(f"     Analysis time: {analysis_time:.1f}ms")
            recommended_model = analysis.metadata.get('epic1_analysis', {}).get('recommended_model', 'unknown')
            print(f"     Recommended model: {recommended_model}")
        
        return analyzer
        
    except Exception as e:
        print(f"❌ Query analyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Run all Epic1 integration tests."""
    print("🎯 Epic 1 Multi-Model Integration Test Suite")
    print("=" * 50)
    
    # Test 1: ComponentFactory integration
    epic1_generator = test_epic1_component_factory()
    
    # Test 2: Configuration loading
    config = test_epic1_configuration_loading()
    
    # Test 3: Epic1 with full configuration
    configured_generator = test_epic1_with_config()
    
    # Test 4: Query complexity analyzer
    analyzer = test_query_complexity_analyzer()
    
    # Summary
    print("\n📊 Integration Test Results:")
    print("=" * 50)
    
    results = {
        "ComponentFactory integration": "✅ PASS" if epic1_generator else "❌ FAIL",
        "Configuration loading": "✅ PASS" if config else "❌ FAIL", 
        "Epic1 with configuration": "✅ PASS" if configured_generator else "❌ FAIL",
        "Query complexity analyzer": "✅ PASS" if analyzer else "❌ FAIL"
    }
    
    for test_name, result in results.items():
        print(f"{test_name}: {result}")
    
    # Overall status
    all_passed = all("✅ PASS" in result for result in results.values())
    overall_status = "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"
    
    print(f"\nOverall Status: {overall_status}")
    
    if all_passed:
        print("\n🎉 Epic 1 Multi-Model Integration is READY!")
        print("   - ComponentFactory registration: Working")
        print("   - Configuration system: Working")
        print("   - Query complexity analysis: Working")
        print("   - Multi-model routing: Initialized")
        print("   - Cost tracking: Ready")
        
        print("\n🚀 Next Steps:")
        print("   1. Test end-to-end query processing with real documents")
        print("   2. Validate cost optimization with different query types")
        print("   3. Test all routing strategies (cost_optimized, quality_first, balanced)")
        print("   4. Validate fallback chains and error handling")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)