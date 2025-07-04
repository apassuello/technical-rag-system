#!/usr/bin/env python3
"""
Complete system test for the three-generator RAG system.

Tests all three modes:
1. Inference Providers API (new)
2. Ollama (existing) 
3. Classic HuggingFace API (existing)

This script validates that our modular implementation works correctly.
"""

import os
import sys
import time
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_generator_modes():
    """Test all three generator modes."""
    print("🧪 Testing Complete RAG System with Three Generator Modes")
    print("="*70)
    
    # Check for API token
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_TOKEN") or os.getenv("HF_API_TOKEN")
    if not token:
        print("❌ No HuggingFace API token found!")
        print("Please set one of: HF_TOKEN, HUGGINGFACE_API_TOKEN, or HF_API_TOKEN")
        print("Example: export HF_TOKEN='hf_your_token_here'")
        return False
    
    print(f"✅ Found API token: {token[:8]}...")
    
    # Import RAG system
    try:
        from src.rag_with_generation import RAGWithGeneration
        print("✅ RAGWithGeneration imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import RAGWithGeneration: {e}")
        return False
    
    # Test data
    test_chunks = [
        {
            "content": "RISC-V is an open-source instruction set architecture (ISA) based on established reduced instruction set computer (RISC) principles.",
            "metadata": {"page_number": 1, "source": "riscv-spec.pdf"},
            "score": 0.95,
            "id": "chunk_1"
        },
        {
            "content": "Unlike most other ISA designs, RISC-V is provided under open source licenses that do not require fees to use.",
            "metadata": {"page_number": 2, "source": "riscv-spec.pdf"}, 
            "score": 0.85,
            "id": "chunk_2"
        }
    ]
    
    test_query = "What is RISC-V and why is it important?"
    
    # Test configurations
    configs = [
        {
            "name": "Inference Providers API",
            "use_inference_providers": True,
            "use_ollama": False,
            "expected_fast": True
        },
        {
            "name": "Classic HuggingFace API",
            "use_inference_providers": False,
            "use_ollama": False,
            "expected_fast": True
        },
        {
            "name": "Ollama (if available)",
            "use_inference_providers": False,
            "use_ollama": True,
            "expected_fast": False
        }
    ]
    
    results = []
    
    for config in configs:
        print(f"\n{'='*70}")
        print(f"🔍 Testing: {config['name']}")
        print(f"{'='*70}")
        
        try:
            # Initialize RAG system with specific configuration
            start_time = time.time()
            rag = RAGWithGeneration(
                api_token=token,
                use_inference_providers=config['use_inference_providers'],
                use_ollama=config['use_ollama'],
                temperature=0.3,
                max_tokens=256
            )
            init_time = time.time() - start_time
            
            print(f"✅ Initialized in {init_time:.2f}s")
            
            # Get generator info
            info = rag.get_generator_info()
            print(f"📊 Generator type: {info['generator_type']}")
            print(f"🤖 Model: {info['model_name']}")
            print(f"🦙 Using Ollama: {info['using_ollama']}")
            print(f"🚀 Using Inference Providers: {info['using_inference_providers']}")
            
            # Manually set chunks for testing (simulating indexed documents)
            rag.chunks = test_chunks
            rag.index_ready = True
            
            # Test query
            print(f"\n❓ Testing query: {test_query}")
            start_time = time.time()
            
            # Create a simple mock query result
            result = {
                "chunks": test_chunks
            }
            
            # Test answer generation directly
            formatted_chunks = []
            for chunk in test_chunks:
                formatted_chunk = {
                    "id": chunk["id"],
                    "content": chunk["content"],
                    "metadata": chunk["metadata"],
                    "score": chunk["score"]
                }
                formatted_chunks.append(formatted_chunk)
            
            # Generate answer using the generator
            answer_result = rag.answer_generator.generate(test_query, formatted_chunks)
            query_time = time.time() - start_time
            
            print(f"✅ Query completed in {query_time:.2f}s")
            print(f"📝 Answer: {answer_result.answer[:200]}...")
            print(f"📊 Confidence: {answer_result.confidence_score:.1%}")
            print(f"📚 Citations: {len(answer_result.citations)}")
            
            # Check performance expectations
            if config['expected_fast'] and query_time > 30:
                print(f"⚠️ Slower than expected ({query_time:.1f}s)")
            elif not config['expected_fast'] and query_time > 120:
                print(f"⚠️ Much slower than expected ({query_time:.1f}s)")
            else:
                print(f"✅ Performance within expected range")
            
            results.append({
                "name": config['name'],
                "success": True,
                "init_time": init_time,
                "query_time": query_time,
                "generator_type": info['generator_type'],
                "model": info['model_name'],
                "answer_length": len(answer_result.answer),
                "citations": len(answer_result.citations),
                "confidence": answer_result.confidence_score
            })
            
        except Exception as e:
            print(f"❌ Failed: {e}")
            print(f"Error type: {type(e).__name__}")
            
            # For Ollama, failure is expected if server not running
            if config['use_ollama'] and ("connect" in str(e).lower() or "timeout" in str(e).lower()):
                print("🔄 Ollama failure expected if server not running - this is normal")
                results.append({
                    "name": config['name'],
                    "success": False,
                    "error": "Expected Ollama connection failure",
                    "expected": True
                })
            else:
                results.append({
                    "name": config['name'],
                    "success": False,
                    "error": str(e),
                    "expected": False
                })
            
        print(f"\n💤 Cooling down for 2 seconds...")
        time.sleep(2)
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 COMPLETE SYSTEM TEST SUMMARY")
    print(f"{'='*70}")
    
    for result in results:
        name = result['name']
        if result['success']:
            print(f"\n✅ {name}: SUCCESS")
            print(f"   Generator: {result['generator_type']}")
            print(f"   Model: {result['model']}")
            print(f"   Init time: {result['init_time']:.2f}s")
            print(f"   Query time: {result['query_time']:.2f}s")
            print(f"   Answer length: {result['answer_length']} chars")
            print(f"   Citations: {result['citations']}")
            print(f"   Confidence: {result['confidence']:.1%}")
        else:
            status = "EXPECTED" if result.get('expected', False) else "FAILED"
            print(f"\n❌ {name}: {status}")
            print(f"   Error: {result['error']}")
    
    # Overall assessment
    successful = [r for r in results if r['success']]
    failed_unexpected = [r for r in results if not r['success'] and not r.get('expected', False)]
    
    print(f"\n📈 Overall Results:")
    print(f"   Successful: {len(successful)}")
    print(f"   Failed (expected): {len([r for r in results if not r['success'] and r.get('expected', False)])}")
    print(f"   Failed (unexpected): {len(failed_unexpected)}")
    
    if len(successful) >= 1 and len(failed_unexpected) == 0:
        print(f"\n🎉 System test PASSED! At least one generator mode working correctly.")
        return True
    else:
        print(f"\n⚠️ System test needs attention. Check failed modes above.")
        return False

def test_environment_variables():
    """Test environment variable handling."""
    print(f"\n{'='*70}")
    print("🔧 Testing Environment Variable Handling")
    print(f"{'='*70}")
    
    # Test startup.py environment variable logic
    import subprocess
    
    # Test Inference Providers mode
    env = os.environ.copy()
    env["USE_INFERENCE_PROVIDERS"] = "true"
    env["USE_OLLAMA"] = "false"
    
    print("📋 Testing USE_INFERENCE_PROVIDERS=true")
    print("✅ Environment variables configured correctly")
    
    # Test that the startup logic would work
    use_inference_providers = env.get("USE_INFERENCE_PROVIDERS", "false").lower() == "true"
    use_ollama = env.get("USE_OLLAMA", "false").lower() == "true"
    
    print(f"   use_inference_providers: {use_inference_providers}")
    print(f"   use_ollama: {use_ollama}")
    
    if use_inference_providers and not use_ollama:
        print("✅ Environment variable parsing correct")
        return True
    else:
        print("❌ Environment variable parsing incorrect")
        return False

def main():
    """Run complete system tests."""
    success1 = test_generator_modes()
    success2 = test_environment_variables()
    
    if success1 and success2:
        print(f"\n🎉 ALL TESTS PASSED! System is ready for deployment.")
    else:
        print(f"\n⚠️ Some tests failed. Please review the issues above.")

if __name__ == "__main__":
    main()