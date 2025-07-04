#!/usr/bin/env python3
"""
Test Ollama integration for RAG system
"""

import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from src.shared_utils.generation.ollama_answer_generator import OllamaAnswerGenerator

def test_ollama():
    """Test Ollama answer generator."""
    
    print("🦙 Testing Ollama Integration\n")
    
    # Test different model options
    models_to_test = [
        "llama3.2:3b",
        "llama3.2:1b", 
        "mistral",
        "llama2",
        "codellama"
    ]
    
    for model in models_to_test:
        print(f"\n📋 Testing model: {model}")
        
        try:
            # Initialize generator
            generator = OllamaAnswerGenerator(
                model_name=model,
                temperature=0.3,
                max_tokens=200
            )
            
            # Test chunks
            test_chunks = [
                {
                    "id": "chunk_1",
                    "content": "RISC-V is a free and open-source instruction set architecture (ISA) based on established reduced instruction set computer (RISC) principles. Unlike proprietary ISAs, RISC-V is provided under royalty-free open-source licenses.",
                    "metadata": {
                        "page_number": 1,
                        "source": "riscv-spec.pdf",
                        "quality_score": 0.95
                    },
                    "score": 0.89
                }
            ]
            
            # Test generation
            result = generator.generate(
                query="What is RISC-V?",
                chunks=test_chunks
            )
            
            print(f"✅ Model works!")
            print(f"Answer: {result.answer[:100]}...")
            print(f"Confidence: {result.confidence_score:.2%}")
            print(f"Time: {result.generation_time:.2f}s")
            print(f"Citations: {len(result.citations)}")
            
            break  # Use first working model
            
        except Exception as e:
            print(f"❌ Model failed: {str(e)}")
    
    print("\n" + "="*50)
    print("\n💡 To use Ollama in your deployment:")
    print("1. Set environment variables:")
    print("   export USE_OLLAMA=true")
    print("   export OLLAMA_MODEL=llama3.2:3b")
    print("   export OLLAMA_URL=http://localhost:11434")
    print("\n2. Make sure Ollama is running:")
    print("   ollama serve")
    print("\n3. Pull the model:")
    print("   ollama pull llama3.2:3b")


if __name__ == "__main__":
    test_ollama()