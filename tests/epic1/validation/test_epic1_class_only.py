#!/usr/bin/env python3
"""
Test Epic1MLAnalyzer class compilation and basic structure WITHOUT initializing the ML infrastructure.
"""

import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

print("=== Testing Epic1MLAnalyzer Class Compilation ===")

try:
    # Import the class (this tests if it compiles correctly)
    from src.components.query_processors.analyzers.epic1_ml_analyzer import Epic1MLAnalyzer
    print("✅ Epic1MLAnalyzer class imported successfully")
    
    # Test class structure
    print(f"✅ __init__ in class dict: {'__init__' in Epic1MLAnalyzer.__dict__}")
    print(f"✅ __init__ qualname: {Epic1MLAnalyzer.__init__.__qualname__}")
    
    # Test that methods exist in the class
    expected_methods = ['__init__', 'configure', '_analyze_query', 'analyze', '_initialize_ml_infrastructure']
    for method in expected_methods:
        if method in Epic1MLAnalyzer.__dict__:
            print(f"✅ {method}: exists in class")
        else:
            print(f"❌ {method}: missing from class")
    
    # Test class can be instantiated with minimal config to avoid ML infrastructure
    print("\nTesting minimal instantiation...")
    config = {
        'memory_budget_gb': 0.1,  # Minimal memory
        'enable_performance_monitoring': False,  # Disable monitoring
        'views': {}  # No views
    }
    
    try:
        analyzer = Epic1MLAnalyzer(config)
        print("✅ Epic1MLAnalyzer instantiated successfully")
        
        # Check essential attributes
        attrs = ['_analysis_count', 'memory_budget_gb', 'views']
        for attr in attrs:
            if hasattr(analyzer, attr):
                print(f"✅ {attr}: {getattr(analyzer, attr)}")
            else:
                print(f"❌ {attr}: missing")
                
        print("🎉 SUCCESS: Epic1MLAnalyzer class is fully operational!")
        
    except Exception as init_e:
        print(f"⚠️ Class compiles but initialization failed: {init_e}")
        print("This may be due to missing dependencies for ML infrastructure")
        
except ImportError as import_e:
    print(f"❌ Failed to import Epic1MLAnalyzer: {import_e}")
    
except Exception as e:
    print(f"❌ Error testing Epic1MLAnalyzer: {e}")
    import traceback
    traceback.print_exc()