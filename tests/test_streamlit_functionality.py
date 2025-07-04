#!/usr/bin/env python3
"""
Test script for Streamlit app functionality.

Tests the core components that the Streamlit app depends on
without requiring a browser or UI interaction.
"""

import sys
from pathlib import Path
import importlib.util
import traceback

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))


def test_streamlit_imports():
    """Test that all required modules can be imported."""
    print("=" * 60)
    print("TESTING STREAMLIT APP IMPORTS")
    print("=" * 60)
    
    required_modules = [
        'streamlit',
        'src.rag_with_generation',
        'shared_utils.generation.answer_generator',
        'shared_utils.generation.prompt_templates'
    ]
    
    for module_name in required_modules:
        try:
            if module_name == 'streamlit':
                import streamlit
            elif module_name == 'src.rag_with_generation':
                from src.rag_with_generation import RAGWithGeneration
            elif module_name == 'shared_utils.generation.answer_generator':
                from shared_utils.generation.answer_generator import AnswerGenerator
            elif module_name == 'shared_utils.generation.prompt_templates':
                from shared_utils.generation.prompt_templates import TechnicalPromptTemplates
            
            print(f"✅ {module_name}")
        except Exception as e:
            print(f"❌ {module_name}: {e}")
            return False
    
    return True


def test_streamlit_app_loading():
    """Test that the streamlit app file can be loaded."""
    print("\n" + "=" * 60)
    print("TESTING STREAMLIT APP LOADING")
    print("=" * 60)
    
    app_path = Path(__file__).parent / "streamlit_app.py"
    
    if not app_path.exists():
        print(f"❌ Streamlit app not found: {app_path}")
        return False
    
    try:
        # Load the module without executing main()
        spec = importlib.util.spec_from_file_location("streamlit_app", app_path)
        module = importlib.util.module_from_spec(spec)
        
        # Add required paths
        sys.path.insert(0, str(app_path.parent))
        
        # Execute the module (this will define functions but not run main)
        spec.loader.exec_module(module)
        
        print("✅ Streamlit app loaded successfully")
        
        # Check that key functions exist
        required_functions = [
            'initialize_rag_system',
            'display_header', 
            'handle_document_upload',
            'handle_query_interface',
            'display_answer_results'
        ]
        
        for func_name in required_functions:
            if hasattr(module, func_name):
                print(f"✅ Function {func_name} found")
            else:
                print(f"❌ Function {func_name} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to load streamlit app: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False


def test_rag_system_initialization():
    """Test RAG system initialization as used by Streamlit."""
    print("\n" + "=" * 60)
    print("TESTING RAG SYSTEM INITIALIZATION")
    print("=" * 60)
    
    try:
        from src.rag_with_generation import RAGWithGeneration
        
        # Test initialization (same as Streamlit cache function)
        rag = RAGWithGeneration(
            primary_model="llama3.2:3b",
            temperature=0.3,
            enable_streaming=True
        )
        
        print("✅ RAG system initialized")
        print(f"   Primary model: llama3.2:3b")
        print(f"   Temperature: 0.3")
        print(f"   Streaming: enabled")
        
        return rag
        
    except Exception as e:
        print(f"❌ RAG initialization failed: {e}")
        traceback.print_exc()
        return None


def test_document_processing_workflow():
    """Test the document upload and processing workflow."""
    print("\n" + "=" * 60)
    print("TESTING DOCUMENT PROCESSING WORKFLOW")
    print("=" * 60)
    
    rag = test_rag_system_initialization()
    if rag is None:
        return False
    
    # Test document indexing
    test_pdf = Path("data/test/riscv-base-instructions.pdf")
    
    if not test_pdf.exists():
        print(f"❌ Test PDF not found: {test_pdf}")
        return False
    
    try:
        chunk_count = rag.index_document(test_pdf)
        print(f"✅ Document indexed: {chunk_count} chunks")
        
        # Verify chunks are available
        if hasattr(rag, 'chunks') and rag.chunks:
            print(f"✅ Chunks available: {len(rag.chunks)} total")
            
            # Test source information
            sources = set(chunk.get('source', 'unknown') for chunk in rag.chunks)
            print(f"✅ Sources identified: {len(sources)} documents")
            
            return rag
        else:
            print("❌ No chunks found after indexing")
            return None
            
    except Exception as e:
        print(f"❌ Document processing failed: {e}")
        traceback.print_exc()
        return None


def test_query_interface_workflow():
    """Test the query processing workflow."""
    print("\n" + "=" * 60)
    print("TESTING QUERY INTERFACE WORKFLOW")
    print("=" * 60)
    
    rag = test_document_processing_workflow()
    if rag is None:
        return False
    
    # Test queries with different configurations
    test_queries = [
        {
            "query": "What is RISC-V?",
            "config": {"top_k": 5, "use_hybrid": True, "dense_weight": 0.7}
        },
        {
            "query": "How many registers does RV32E have?",
            "config": {"top_k": 3, "use_hybrid": False, "dense_weight": 1.0}
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\nTest Query {i}: {test_case['query']}")
        
        try:
            result = rag.query_with_answer(
                question=test_case['query'],
                **test_case['config'],
                return_context=True
            )
            
            # Validate result structure
            required_keys = ['answer', 'citations', 'confidence', 'sources', 'retrieval_stats', 'generation_stats']
            
            for key in required_keys:
                if key in result:
                    print(f"   ✅ {key}: {type(result[key])}")
                else:
                    print(f"   ❌ Missing key: {key}")
                    return False
            
            # Validate content quality
            if len(result['answer']) > 50:
                print(f"   ✅ Answer length: {len(result['answer'])} chars")
            else:
                print(f"   ⚠️ Short answer: {len(result['answer'])} chars")
            
            print(f"   ✅ Citations: {len(result['citations'])}")
            print(f"   ✅ Confidence: {result['confidence']:.1%}")
            
        except Exception as e:
            print(f"   ❌ Query failed: {e}")
            traceback.print_exc()
            return False
    
    return True


def test_citation_display_format():
    """Test citation formatting for display."""
    print("\n" + "=" * 60)
    print("TESTING CITATION DISPLAY FORMAT")
    print("=" * 60)
    
    # Test with sample result data
    sample_result = {
        'answer': 'RISC-V is an open instruction set architecture...',
        'citations': [
            {
                'source': 'riscv-base-instructions.pdf',
                'page': 19,
                'relevance': 0.95,
                'snippet': 'RISC-V is a new instruction-set architecture...'
            },
            {
                'source': 'riscv-base-instructions.pdf', 
                'page': 174,
                'relevance': 0.87,
                'snippet': 'The goals of defining RISC-V include...'
            }
        ],
        'confidence': 0.89,
        'retrieval_stats': {'method': 'hybrid', 'chunks_retrieved': 5},
        'generation_stats': {'model': 'llama3.2:3b', 'total_time': 8.5}
    }
    
    # Test that we can process this data as the UI would
    try:
        print(f"✅ Answer: {len(sample_result['answer'])} characters")
        print(f"✅ Citations: {len(sample_result['citations'])} sources")
        print(f"✅ Confidence: {sample_result['confidence']:.1%}")
        
        for i, citation in enumerate(sample_result['citations'], 1):
            print(f"   Citation {i}: {citation['source']} (Page {citation['page']})")
            print(f"   Relevance: {citation['relevance']:.1%}")
        
        print("✅ Citation display format validated")
        return True
        
    except Exception as e:
        print(f"❌ Citation format test failed: {e}")
        return False


def main():
    """Run all Streamlit functionality tests."""
    print("STREAMLIT APP FUNCTIONALITY TESTING")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_streamlit_imports),
        ("App Loading Test", test_streamlit_app_loading),
        ("RAG Initialization Test", lambda: test_rag_system_initialization() is not None),
        ("Document Processing Test", lambda: test_document_processing_workflow() is not None),
        ("Query Interface Test", test_query_interface_workflow),
        ("Citation Display Test", test_citation_display_format)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"RUNNING: {test_name}")
        print(f"{'='*60}")
        
        try:
            success = test_func()
            results[test_name] = success
            
            if success:
                print(f"\n🎉 {test_name} PASSED")
            else:
                print(f"\n❌ {test_name} FAILED")
                
        except Exception as e:
            results[test_name] = False
            print(f"\n💥 {test_name} CRASHED: {e}")
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:10} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Streamlit app should work correctly!")
        return True
    else:
        print("⚠️ SOME TESTS FAILED - Streamlit app may have issues")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)