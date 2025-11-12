#!/usr/bin/env python3
"""
Test script to verify legacy parameter compatibility with ModularDocumentProcessor.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.core.component_factory import ComponentFactory

def test_legacy_compatibility():
    """Test that ModularDocumentProcessor accepts legacy parameters."""
    
    print("Testing legacy parameter compatibility...")
    
    try:
        # Test creating with legacy parameters (as used by platform orchestrator)
        print("\n1. Testing legacy chunk_size and chunk_overlap parameters...")
        processor = ComponentFactory.create_processor(
            "hybrid_pdf",
            chunk_size=1024,
            chunk_overlap=128
        )
        print(f"   ✅ Created processor with legacy params: {processor.__class__.__name__}")
        
        # Check that config was properly set
        config = processor.get_config()
        print(f"   ✅ Chunk size set to: {config['chunker']['config']['chunk_size']}")
        print(f"   ✅ Chunk overlap set to: {config['chunker']['config']['overlap']}")
        
        # Test additional legacy parameters
        print("\n2. Testing additional legacy parameters...")
        processor2 = ComponentFactory.create_processor(
            "hybrid_pdf",
            chunk_size=800,
            chunk_overlap=100,
            min_chunk_size=200,
            preserve_layout=True,
            quality_threshold=0.5
        )
        print(f"   ✅ Created processor with extended legacy params: {processor2.__class__.__name__}")
        
        config2 = processor2.get_config()
        print(f"   ✅ Min chunk size: {config2['chunker']['config']['min_chunk_size']}")
        print(f"   ✅ Preserve layout: {config2['parser']['config']['preserve_layout']}")
        print(f"   ✅ Quality threshold: {config2['chunker']['config']['quality_threshold']}")
        
        # Test component info
        print("\n3. Testing component info...")
        info = processor.get_component_info()
        print(f"   ✅ Parser type: {info['parser']['type']}")
        print(f"   ✅ Chunker type: {info['chunker']['type']}")
        print(f"   ✅ Cleaner type: {info['cleaner']['type']}")
        
        print("\n🎉 All legacy compatibility tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Legacy compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_legacy_compatibility()
    sys.exit(0 if success else 1)