#!/usr/bin/env python3
"""
Test the structure and imports of our Inference Providers implementation.
This test doesn't require an API token.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all imports work correctly."""
    print("🔍 Testing imports...")
    
    try:
        # Test InferenceProvidersGenerator import
        from src.shared_utils.generation.inference_providers_generator import InferenceProvidersGenerator
        print("✅ InferenceProvidersGenerator imported successfully")
        
        # Test updated RAGWithGeneration import
        from src.rag_with_generation import RAGWithGeneration
        print("✅ RAGWithGeneration imported successfully")
        
        # Test that all needed classes are available
        from src.shared_utils.generation.hf_answer_generator import Citation, GeneratedAnswer
        print("✅ Citation and GeneratedAnswer imported successfully")
        
        from src.shared_utils.generation.prompt_templates import TechnicalPromptTemplates
        print("✅ TechnicalPromptTemplates imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_class_structure():
    """Test that classes have expected methods and attributes."""
    print("\n🔍 Testing class structure...")
    
    try:
        from src.shared_utils.generation.inference_providers_generator import InferenceProvidersGenerator
        
        # Check class attributes
        expected_methods = [
            '__init__',
            'generate',
            '_test_connection',
            '_format_context',
            '_create_messages',
            '_call_chat_completion',
            '_extract_citations',
            '_calculate_confidence'
        ]
        
        for method in expected_methods:
            if hasattr(InferenceProvidersGenerator, method):
                print(f"✅ {method} method found")
            else:
                print(f"❌ {method} method missing")
                return False
        
        # Check class constants
        if hasattr(InferenceProvidersGenerator, 'CHAT_MODELS'):
            print("✅ CHAT_MODELS constant found")
            print(f"   Models: {InferenceProvidersGenerator.CHAT_MODELS}")
        else:
            print("❌ CHAT_MODELS constant missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Class structure test failed: {e}")
        return False

def test_rag_integration():
    """Test that RAGWithGeneration properly integrates new generator."""
    print("\n🔍 Testing RAG integration...")
    
    try:
        from src.rag_with_generation import RAGWithGeneration
        
        # Test that constructor accepts new parameter
        import inspect
        sig = inspect.signature(RAGWithGeneration.__init__)
        params = list(sig.parameters.keys())
        
        if 'use_inference_providers' in params:
            print("✅ RAGWithGeneration accepts use_inference_providers parameter")
        else:
            print("❌ use_inference_providers parameter missing")
            return False
        
        # Test that get_generator_info includes new field
        if hasattr(RAGWithGeneration, 'get_generator_info'):
            print("✅ get_generator_info method found")
        else:
            print("❌ get_generator_info method missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ RAG integration test failed: {e}")
        return False

def test_without_token():
    """Test that we get proper error messages without token."""
    print("\n🔍 Testing behavior without API token...")
    
    try:
        # Make sure no token is set
        import os
        old_tokens = {}
        token_vars = ["HF_TOKEN", "HUGGINGFACE_API_TOKEN", "HF_API_TOKEN"]
        
        for var in token_vars:
            if var in os.environ:
                old_tokens[var] = os.environ[var]
                del os.environ[var]
        
        try:
            from src.shared_utils.generation.inference_providers_generator import InferenceProvidersGenerator
            
            # This should raise ValueError about missing token
            try:
                generator = InferenceProvidersGenerator()
                print("❌ Should have raised ValueError for missing token")
                return False
            except ValueError as e:
                if "token required" in str(e).lower():
                    print("✅ Properly raises ValueError for missing token")
                else:
                    print(f"❌ Wrong error message: {e}")
                    return False
            except Exception as e:
                print(f"❌ Unexpected error type: {e}")
                return False
                
        finally:
            # Restore old tokens
            for var, value in old_tokens.items():
                os.environ[var] = value
        
        return True
        
    except Exception as e:
        print(f"❌ Token test failed: {e}")
        return False

def main():
    """Run all structure tests."""
    print("🧪 Testing Inference Providers Implementation Structure")
    print("="*70)
    
    tests = [
        ("Import Tests", test_imports),
        ("Class Structure", test_class_structure), 
        ("RAG Integration", test_rag_integration),
        ("Token Handling", test_without_token)
    ]
    
    results = []
    for test_name, test_func in tests:
        success = test_func()
        results.append((test_name, success))
    
    # Summary
    print("\n" + "="*70)
    print("📊 STRUCTURE TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} structure tests passed")
    
    if passed == total:
        print("\n🎉 All structure tests passed! Implementation is ready for API testing.")
        print("💡 Next step: Set HF_TOKEN and run: python test_inference_providers.py")
    else:
        print("\n⚠️ Some structure tests failed. Please fix the issues above.")

if __name__ == "__main__":
    main()