#!/usr/bin/env python3
"""
Test script to verify component factory integration with ModularDocumentProcessor.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.core.component_factory import ComponentFactory

def test_component_factory_integration():
    """Test that ComponentFactory can create ModularDocumentProcessor."""
    
    print("Testing ComponentFactory integration with ModularDocumentProcessor...")
    
    try:
        # Test creating the modular processor
        print("\n1. Testing ModularDocumentProcessor creation...")
        processor = ComponentFactory.create_processor("hybrid_pdf")
        print(f"   ✅ Created processor: {processor.__class__.__name__}")
        
        # Test processor methods
        print("\n2. Testing processor interface...")
        supported_formats = processor.supported_formats()
        print(f"   ✅ Supported formats: {supported_formats}")
        
        component_info = processor.get_component_info()
        print(f"   ✅ Component info: {component_info}")
        
        # Test creating modular processor by name
        print("\n3. Testing modular processor by name...")
        modular_processor = ComponentFactory.create_processor("modular")
        print(f"   ✅ Created modular processor: {modular_processor.__class__.__name__}")
        
        # Test legacy processor still works
        print("\n4. Testing legacy processor access...")
        legacy_processor = ComponentFactory.create_processor("legacy_pdf")
        print(f"   ✅ Created legacy processor: {legacy_processor.__class__.__name__}")
        
        # Test component factory performance metrics
        print("\n5. Testing performance metrics...")
        metrics = ComponentFactory.get_performance_metrics()
        print(f"   ✅ Performance metrics: {metrics}")
        
        # Test available components
        print("\n6. Testing available components...")
        available = ComponentFactory.get_available_components()
        print(f"   ✅ Available processors: {available['processors']}")
        
        print("\n🎉 All integration tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_component_factory_integration()
    sys.exit(0 if success else 1)