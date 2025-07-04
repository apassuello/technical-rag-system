#!/usr/bin/env python3
"""
Test the complete RAG answer generation with HuggingFace API
This simulates what will happen in your deployed app
"""

import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Import your actual components
from src.shared_utils.generation.hf_answer_generator import HuggingFaceAnswerGenerator

def test_rag_answer_generation():
    """Test the full RAG answer generation pipeline."""
    
    print("🧪 Testing RAG Answer Generation with HuggingFace API\n")
    
    # Check for token
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_TOKEN")
    if token:
        print(f"✅ Using HF token: {token[:8]}...")
    else:
        print("⚠️ No token found - will use free tier")
    
    # Initialize the answer generator
    print("\n📚 Initializing HuggingFaceAnswerGenerator...")
    try:
        generator = HuggingFaceAnswerGenerator(
            model_name="gpt2",
            api_token=token,
            temperature=0.3,
            max_tokens=150
        )
        print("✅ Generator initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # Create mock chunks (simulating RAG retrieval)
    mock_chunks = [
        {
            "id": "chunk_1",
            "content": "RISC-V is an open-source instruction set architecture (ISA) based on established reduced instruction set computer (RISC) principles. Unlike proprietary ISAs, RISC-V is free to use for anyone.",
            "metadata": {
                "page_number": 1,
                "source": "riscv-spec.pdf",
                "quality_score": 0.95
            },
            "score": 0.89
        },
        {
            "id": "chunk_2", 
            "content": "The RISC-V ISA includes a base integer instruction set with optional extensions. The base integer ISAs are RV32I (32-bit) and RV64I (64-bit). Standard extensions include M for multiplication, A for atomics, F for floating-point, and more.",
            "metadata": {
                "page_number": 15,
                "source": "riscv-spec.pdf",
                "quality_score": 0.93
            },
            "score": 0.85
        }
    ]
    
    # Test question
    test_question = "What is RISC-V and what are its main features?"
    
    print(f"\n❓ Test Question: {test_question}")
    print(f"📄 Using {len(mock_chunks)} retrieved chunks")
    
    # Generate answer
    print("\n🤖 Generating answer...")
    try:
        result = generator.generate(
            query=test_question,
            chunks=mock_chunks
        )
        
        print("\n✅ Generation successful!")
        print(f"\n📝 Answer:\n{result.answer}")
        print(f"\n📊 Metrics:")
        print(f"   - Confidence: {result.confidence_score:.2%}")
        print(f"   - Generation time: {result.generation_time:.2f}s")
        print(f"   - Model used: {result.model_used}")
        print(f"   - Citations: {len(result.citations)}")
        
        if result.citations:
            print("\n📚 Citations:")
            for i, citation in enumerate(result.citations, 1):
                print(f"   {i}. {citation.source_file} (Page {citation.page_number})")
        
    except Exception as e:
        print(f"\n❌ Generation failed: {e}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
    
    # Test fallback mechanism
    print("\n" + "="*50)
    print("\n🔄 Testing Fallback Mechanism...")
    
    # Try with a non-existent model to trigger fallback
    print("Testing with invalid model to trigger fallback...")
    generator_fallback = HuggingFaceAnswerGenerator(
        model_name="this-model-does-not-exist",
        api_token=token
    )
    
    try:
        result = generator_fallback.generate(
            query="Simple test question",
            chunks=mock_chunks[:1]
        )
        print("✅ Fallback worked! Answer generated despite invalid primary model")
        print(f"Model used: {result.model_used}")
    except Exception as e:
        print(f"❌ Fallback failed: {e}")
    
    print("\n🎉 Test complete!")


if __name__ == "__main__":
    # Instructions
    print("="*60)
    print("HuggingFace RAG Generation Test")
    print("="*60)
    print("\nBefore running, set your HF token:")
    print("  export HF_TOKEN='hf_your_token_here'")
    print("\nOr run directly with:")
    print("  HF_TOKEN='hf_your_token_here' python test_rag_generation.py")
    print("="*60 + "\n")
    
    test_rag_answer_generation()