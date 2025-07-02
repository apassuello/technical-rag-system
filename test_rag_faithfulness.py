#!/usr/bin/env python3
"""
Test script to verify RAG faithfulness - ensuring the model uses retrieved context
rather than pre-trained knowledge.

This script tests:
1. Model behavior without context
2. Model behavior with context
3. Model behavior with contradictory context
4. Model behavior with very specific/obscure information
"""

import sys
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import directly since we're in the project directory
sys.path.insert(0, str(Path(__file__).parent))
from src.rag_with_generation import RAGWithGeneration


def test_no_context_behavior():
    """Test how the model behaves when no context is provided."""
    print("=" * 80)
    print("TEST 1: Model Behavior WITHOUT Context")
    print("=" * 80)
    
    rag = RAGWithGeneration()
    
    # Test with empty chunks
    empty_chunks = []
    
    test_queries = [
        "What is RISC-V?",
        "What are the RISC-V register naming conventions?",
        "How many registers does RV32E have?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        try:
            result = rag.answer_generator.generate(
                query=query,
                chunks=empty_chunks
            )
            print(f"Answer: {result.answer}")
            print(f"Citations: {len(result.citations)}")
            print(f"Confidence: {result.confidence_score:.1%}")
        except Exception as e:
            print(f"Error: {e}")


def test_with_fake_context():
    """Test with completely fabricated context to see if model follows it."""
    print("\n" + "=" * 80)
    print("TEST 2: Model Behavior WITH Fabricated Context")
    print("=" * 80)
    
    rag = RAGWithGeneration()
    
    # Create fake chunks with fabricated information
    fake_chunks = [
        {
            "id": "chunk_1",
            "content": "RISC-V is actually a quantum computing architecture developed by NASA in 2019. It uses 128 quantum registers called q0-q127.",
            "metadata": {"page_number": 1, "source": "fake-document.pdf"},
            "score": 0.95
        },
        {
            "id": "chunk_2",
            "content": "The RV32E variant of RISC-V has exactly 64 integer registers, which is double the standard amount for embedded systems.",
            "metadata": {"page_number": 2, "source": "fake-document.pdf"},
            "score": 0.90
        }
    ]
    
    test_queries = [
        "What is RISC-V?",
        "How many registers does RV32E have?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        try:
            result = rag.answer_generator.generate(
                query=query,
                chunks=fake_chunks
            )
            print(f"Answer: {result.answer}")
            print(f"Citations: {len(result.citations)}")
            print(f"Confidence: {result.confidence_score:.1%}")
            
            # Check if the fake information appears in the answer
            if "quantum" in result.answer.lower() or "nasa" in result.answer.lower():
                print("🚨 ALERT: Model used fabricated information!")
            elif "64 integer registers" in result.answer or "64 registers" in result.answer:
                print("🚨 ALERT: Model used fabricated RV32E information!")
            else:
                print("✅ Model appears to have rejected fabricated information")
                
        except Exception as e:
            print(f"Error: {e}")


def test_specific_context_following():
    """Test with very specific information to see if model uses it."""
    print("\n" + "=" * 80)
    print("TEST 3: Model Following Specific Context")
    print("=" * 80)
    
    rag = RAGWithGeneration()
    
    # Create chunks with very specific, less common information
    specific_chunks = [
        {
            "id": "chunk_1", 
            "content": "The RISC-V specification version 2.3 introduced the concept of 'instruction parcels' which are 16-bit aligned instruction fragments. Each instruction consists of one or more 16-bit parcels.",
            "metadata": {"page_number": 15, "source": "riscv-spec-v2.3.pdf"},
            "score": 0.92
        },
        {
            "id": "chunk_2",
            "content": "RISC-V uses a specific encoding where bits [1:0] of an instruction determine the instruction length: 00, 01, 10 indicate 16-bit instructions, while 11 indicates 32-bit or longer instructions.",
            "metadata": {"page_number": 16, "source": "riscv-spec-v2.3.pdf"},
            "score": 0.88
        }
    ]
    
    query = "How does RISC-V determine instruction length encoding?"
    
    print(f"\nQuery: {query}")
    try:
        result = rag.answer_generator.generate(
            query=query,
            chunks=specific_chunks
        )
        print(f"Answer: {result.answer}")
        print(f"Citations: {len(result.citations)}")
        print(f"Confidence: {result.confidence_score:.1%}")
        
        # Check for specific terms from context
        context_terms = ["instruction parcels", "16-bit aligned", "bits [1:0]", "00, 01, 10"]
        used_terms = [term for term in context_terms if term in result.answer]
        
        print(f"\nContext terms used: {used_terms}")
        if len(used_terms) >= 2:
            print("✅ Model appears to be using specific context information")
        else:
            print("⚠️ Model may not be fully utilizing the specific context")
            
    except Exception as e:
        print(f"Error: {e}")


def test_contradictory_context():
    """Test with context that contradicts common knowledge."""
    print("\n" + "=" * 80)
    print("TEST 4: Model With Contradictory Context")
    print("=" * 80)
    
    rag = RAGWithGeneration()
    
    # Create context that contradicts well-known facts
    contradictory_chunks = [
        {
            "id": "chunk_1",
            "content": "RISC-V was originally developed by Intel in the 1990s as a proprietary instruction set architecture for their Pentium processors.",
            "metadata": {"page_number": 1, "source": "wrong-history.pdf"},
            "score": 0.95
        },
        {
            "id": "chunk_2",
            "content": "The RISC-V standard requires exactly 64 general-purpose registers in all implementations, making it incompatible with embedded systems.",
            "metadata": {"page_number": 2, "source": "wrong-specs.pdf"},
            "score": 0.90
        }
    ]
    
    queries = [
        "Who developed RISC-V?",
        "How many registers does RISC-V have?"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        try:
            result = rag.answer_generator.generate(
                query=query,
                chunks=contradictory_chunks
            )
            print(f"Answer: {result.answer}")
            print(f"Citations: {len(result.citations)}")
            
            # Check if model follows the contradictory information
            if "intel" in result.answer.lower() and "1990s" in result.answer.lower():
                print("🚨 ALERT: Model followed contradictory historical information!")
            elif "64 general-purpose registers" in result.answer:
                print("🚨 ALERT: Model followed contradictory register information!")
            else:
                print("✅ Model appears to have rejected contradictory information")
                
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Run all RAG faithfulness tests."""
    print("RAG FAITHFULNESS TESTING")
    print("Testing whether the model actually uses provided context vs pre-trained knowledge")
    
    # Test 1: No context
    test_no_context_behavior()
    
    # Test 2: Fabricated context
    test_with_fake_context()
    
    # Test 3: Specific context following
    test_specific_context_following()
    
    # Test 4: Contradictory context
    test_contradictory_context()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("Review the results above to assess:")
    print("1. Does the model refuse to answer without context?")
    print("2. Does the model follow fabricated information inappropriately?")
    print("3. Does the model use specific context details?")
    print("4. Does the model reject contradictory information?")
    print("\nIdeal behavior: Strong context following but with contradiction detection")


if __name__ == "__main__":
    main()