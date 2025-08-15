#!/usr/bin/env python3
"""
Quick integration test for the new modular document processor.

This script tests the basic functionality of the modular document processor
to ensure all components work together correctly.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.components.processors.document_processor import create_pdf_processor

def test_modular_processor():
    """Test the modular document processor with a sample PDF."""
    
    # Find a test PDF
    test_pdf_path = project_root / "data" / "test" / "riscv-card.pdf"
    
    if not test_pdf_path.exists():
        print(f"Test PDF not found at {test_pdf_path}")
        return False
    
    print(f"Testing modular processor with: {test_pdf_path}")
    
    try:
        # Create processor with default configuration
        processor = create_pdf_processor()
        
        print("Created processor with components:")
        component_info = processor.get_component_info()
        for component_type, info in component_info.items():
            type_info = info.get('type', 'N/A')
            class_info = info.get('class', 'N/A')
            print(f"  {component_type}: {class_info} ({type_info})")
        
        # Validate document
        validation_result = processor.validate_document(test_pdf_path)
        print(f"\nValidation result: {'PASSED' if validation_result.valid else 'FAILED'}")
        if validation_result.warnings:
            print(f"Warnings: {validation_result.warnings}")
        if validation_result.errors:
            print(f"Errors: {validation_result.errors}")
            return False
        
        # Process document
        print("\nProcessing document...")
        documents = processor.process(test_pdf_path)
        
        print(f"Processing completed successfully!")
        print(f"Created {len(documents)} document chunks")
        
        # Show sample chunks
        if documents:
            print("\nSample chunks:")
            for i, doc in enumerate(documents[:3]):
                print(f"\nChunk {i+1}:")
                print(f"  Content length: {len(doc.content)} characters")
                print(f"  Quality score: {doc.metadata.get('quality_score', 'N/A')}")
                print(f"  Source: {doc.metadata.get('source_name', 'N/A')}")
                print(f"  Content preview: {doc.content[:100]}...")
        
        # Show metrics
        metrics = processor.get_metrics()
        print(f"\nProcessing metrics:")
        print(f"  Documents processed: {metrics['documents_processed']}")
        print(f"  Total chunks created: {metrics['total_chunks_created']}")
        print(f"  Total processing time: {metrics['total_processing_time']:.3f}s")
        print(f"  Average chunks per document: {metrics.get('average_chunks_per_document', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration():
    """Test configuration-driven component selection."""
    
    print("\n" + "="*50)
    print("Testing configuration-driven processor")
    
    # Custom configuration
    config = {
        'parser': {
            'type': 'pymupdf',
            'config': {
                'max_file_size_mb': 50,
                'preserve_layout': False
            }
        },
        'chunker': {
            'type': 'sentence_boundary',
            'config': {
                'chunk_size': 1000,
                'overlap': 100,
                'quality_threshold': 0.3
            }
        },
        'cleaner': {
            'type': 'technical',
            'config': {
                'normalize_whitespace': True,
                'remove_artifacts': True,
                'preserve_code_blocks': False
            }
        }
    }
    
    try:
        processor = create_pdf_processor(config)
        
        print("Created processor with custom configuration:")
        current_config = processor.get_config()
        print(f"  Parser max file size: {current_config['parser']['config']['max_file_size_mb']}MB")
        print(f"  Chunker size: {current_config['chunker']['config']['chunk_size']} characters")
        print(f"  Cleaner preserves code: {current_config['cleaner']['config']['preserve_code_blocks']}")
        
        return True
        
    except Exception as e:
        print(f"Configuration test failed: {str(e)}")
        return False

def main():
    """Run all tests."""
    
    print("Testing Modular Document Processor")
    print("=" * 50)
    
    # Test basic functionality
    success1 = test_modular_processor()
    
    # Test configuration
    success2 = test_configuration()
    
    print("\n" + "="*50)
    if success1 and success2:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())