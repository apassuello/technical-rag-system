#!/usr/bin/env python3
"""
Test RoBERTa Squad2 model specifically
"""

import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from src.shared_utils.generation.hf_answer_generator import HuggingFaceAnswerGenerator

def test_squad2():
    """Test RoBERTa Squad2 with our RAG setup."""
    
    print("🧪 Testing RoBERTa Squad2 for RAG\n")
    
    # Get token
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_TOKEN")
    if token:
        print(f"✅ Using token: {token[:8]}...")
    else:
        print("⚠️ No token found")
    
    # Initialize generator
    try:
        generator = HuggingFaceAnswerGenerator(
            model_name="deepset/roberta-base-squad2",
            api_token=token
        )
        print("✅ Generator initialized")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # Create test chunks (like from RAG retrieval)
    test_chunks = [
        {
            "id": "chunk_1",
            "content": "RISC-V is a free and open-source instruction set architecture (ISA) based on established reduced instruction set computer (RISC) principles. Unlike most other ISA designs, RISC-V is provided under royalty-free open-source licenses.",
            "metadata": {
                "page_number": 1,
                "source": "riscv-spec.pdf",
                "quality_score": 0.95
            },
            "score": 0.89
        },
        {
            "id": "chunk_2",
            "content": "The RISC-V ISA includes a base integer instruction set and optional extensions. The base ISAs are RV32I and RV64I for 32-bit and 64-bit address spaces respectively. Extensions include M for multiplication, A for atomic instructions, F for single-precision floating-point, and D for double-precision floating-point.",
            "metadata": {
                "page_number": 5,
                "source": "riscv-spec.pdf",
                "quality_score": 0.92
            },
            "score": 0.85
        }
    ]
    
    # Test questions
    test_questions = [
        "What is RISC-V?",
        "What are the base instruction sets in RISC-V?",
        "What extensions are available for RISC-V?",
        "Is RISC-V open source?",
    ]
    
    print("\n📋 Testing Questions:\n")
    
    for question in test_questions:
        print(f"❓ Question: {question}")
        
        try:
            # Generate answer
            result = generator.generate(
                query=question,
                chunks=test_chunks
            )
            
            print(f"✅ Answer: {result.answer}")
            print(f"📊 Confidence: {result.confidence_score:.2%}")
            print(f"🤖 Model: {result.model_used}")
            print(f"⏱️ Time: {result.generation_time:.2f}s")
            
            if result.citations:
                print(f"📚 Citations: {len(result.citations)}")
                for citation in result.citations:
                    print(f"   - {citation.source_file} (Page {citation.page_number})")
            
        except Exception as e:
            print(f"❌ Failed: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "-"*50 + "\n")
    
    print("🎉 Squad2 test complete!")


if __name__ == "__main__":
    test_squad2()