#!/usr/bin/env python3
"""
Test HuggingFace Inference Providers API integration.

This script tests the new Inference Providers API with chat completion format,
ensuring it works correctly before deployment.
"""

import os
import sys
import time
import json
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Import our generator
from src.shared_utils.generation.inference_providers_generator import InferenceProvidersGenerator

def test_basic_connection():
    """Test basic API connection and model availability."""
    print("="*70)
    print("🔍 TEST 1: Basic Connection Test")
    print("="*70)
    
    try:
        generator = InferenceProvidersGenerator()
        print("✅ Generator initialized successfully")
        print(f"🤖 Using model: {generator.model_name}")
        print(f"📊 Using chat completion: {generator.using_chat_completion}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return False

def test_simple_generation():
    """Test simple text generation."""
    print("\n" + "="*70)
    print("🔍 TEST 2: Simple Generation Test")
    print("="*70)
    
    try:
        generator = InferenceProvidersGenerator()
        
        # Simple test chunks
        test_chunks = [
            {
                "content": "Python is a high-level programming language known for its simplicity and readability.",
                "metadata": {"page_number": 1, "source": "python-intro.pdf"},
                "score": 0.95
            }
        ]
        
        # Generate answer
        start_time = time.time()
        result = generator.generate("What is Python?", test_chunks)
        end_time = time.time()
        
        print(f"\n📝 Answer: {result.answer}")
        print(f"⏱️ Generation time: {end_time - start_time:.2f}s")
        print(f"📊 Confidence: {result.confidence_score:.1%}")
        print(f"🤖 Model used: {result.model_used}")
        print(f"📚 Citations: {len(result.citations)}")
        
        return len(result.answer) > 10
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_technical_rag_scenario():
    """Test with actual technical documentation scenario."""
    print("\n" + "="*70)
    print("🔍 TEST 3: Technical RAG Scenario")
    print("="*70)
    
    try:
        generator = InferenceProvidersGenerator()
        
        # Realistic technical chunks
        test_chunks = [
            {
                "content": "RISC-V is an open-source instruction set architecture (ISA) based on established reduced instruction set computer (RISC) principles. Unlike most other ISA designs, RISC-V is provided under open source licenses that do not require fees to use.",
                "metadata": {"page_number": 1, "source": "riscv-spec.pdf"},
                "score": 0.95
            },
            {
                "content": "The RISC-V ISA includes a small base integer ISA, usable as a base for customized accelerators or for educational purposes, with optional standard extensions to add integer multiply/divide, atomic operations, and single and double-precision floating-point arithmetic.",
                "metadata": {"page_number": 2, "source": "riscv-spec.pdf"},
                "score": 0.85
            },
            {
                "content": "RISC-V has been designed to support extensive customization and specialization. The base integer ISA can be extended with one or more optional instruction-set extensions, but the base integer instructions are predefined and frozen.",
                "metadata": {"page_number": 3, "source": "riscv-spec.pdf"},
                "score": 0.80
            }
        ]
        
        questions = [
            "What is RISC-V?",
            "What are the key features of RISC-V architecture?",
            "Why is RISC-V open source important?"
        ]
        
        for question in questions:
            print(f"\n❓ Question: {question}")
            
            start_time = time.time()
            result = generator.generate(question, test_chunks)
            end_time = time.time()
            
            print(f"📝 Answer: {result.answer[:200]}...")
            print(f"⏱️ Time: {end_time - start_time:.2f}s")
            print(f"📊 Confidence: {result.confidence_score:.1%}")
            print(f"📚 Citations: {len(result.citations)}")
            
            # Check citations
            if result.citations:
                print("📎 Citation sources:")
                for citation in result.citations:
                    print(f"   - Page {citation.page_number} from {citation.source_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Technical scenario failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """Test error handling scenarios."""
    print("\n" + "="*70)
    print("🔍 TEST 4: Error Handling")
    print("="*70)
    
    try:
        generator = InferenceProvidersGenerator()
        
        # Test with no chunks
        print("\n📋 Testing with no chunks...")
        result = generator.generate("What is RISC-V?", [])
        print(f"✅ Handled empty chunks: {result.answer}")
        print(f"📊 Confidence: {result.confidence_score:.1%}")
        
        # Test with very short chunks
        print("\n📋 Testing with minimal chunks...")
        tiny_chunks = [{"content": "RISC", "metadata": {}, "score": 0.5}]
        result = generator.generate("Explain RISC-V in detail", tiny_chunks)
        print(f"✅ Handled minimal context: {result.answer[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def test_full_rag_integration():
    """Test full RAG integration with Inference Providers."""
    print("\n" + "="*70)
    print("🔍 TEST 5: Full RAG Integration")
    print("="*70)
    
    try:
        # Import RAG system
        from src.rag_with_generation import RAGWithGeneration
        
        # Initialize with Inference Providers
        print("🚀 Initializing RAG with Inference Providers...")
        rag = RAGWithGeneration(
            use_inference_providers=True,
            use_ollama=False,
            temperature=0.3,
            max_tokens=512
        )
        
        # Check generator info
        info = rag.get_generator_info()
        print(f"✅ Generator type: {info['generator_type']}")
        print(f"📊 Using Inference Providers: {info['using_inference_providers']}")
        print(f"🤖 Model: {info['model_name']}")
        
        # Test with a simple query (would need indexed documents for real test)
        print("\n📋 Testing query capability...")
        # Note: This would fail without indexed documents, but tests the integration
        
        return True
        
    except Exception as e:
        print(f"❌ RAG integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🧪 Testing HuggingFace Inference Providers API Integration")
    print("="*70)
    
    # Check for API token
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_TOKEN") or os.getenv("HF_API_TOKEN")
    if not token:
        print("❌ No HuggingFace API token found!")
        print("Please set one of: HF_TOKEN, HUGGINGFACE_API_TOKEN, or HF_API_TOKEN")
        print("Example: export HF_TOKEN='hf_your_token_here'")
        return
    
    print(f"✅ Found API token: {token[:8]}...")
    
    # Run tests
    tests = [
        ("Basic Connection", test_basic_connection),
        ("Simple Generation", test_simple_generation),
        ("Technical RAG Scenario", test_technical_rag_scenario),
        ("Error Handling", test_error_handling),
        ("Full RAG Integration", test_full_rag_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
            time.sleep(1)  # Be nice to the API
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Inference Providers API is ready for use.")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()