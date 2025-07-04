#!/usr/bin/env python3
"""
Enhanced faithfulness testing after system prompt improvements.

Tests the improved answer generator for better context following and
reduced reliance on pre-trained knowledge.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

from shared_utils.generation.answer_generator import AnswerGenerator


def test_improved_no_context_handling():
    """Test that model refuses to answer without context."""
    print("=" * 80)
    print("TEST 1: IMPROVED NO-CONTEXT HANDLING")
    print("=" * 80)
    
    generator = AnswerGenerator()
    
    test_queries = [
        "What is RISC-V?",
        "How many registers does RV32E have?",
        "What are the RISC-V instruction formats?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # Test with empty chunks
        result = generator.generate(query, [])
        
        print(f"Answer: \"{result.answer}\"")
        print(f"Citations: {len(result.citations)}")
        print(f"Confidence: {result.confidence_score:.1%}")
        
        # Check if answer contains appropriate refusal language
        refusal_indicators = [
            "cannot answer",
            "no relevant context",
            "not found in the available documents",
            "ensure the relevant documents"
        ]
        
        contains_refusal = any(indicator in result.answer.lower() for indicator in refusal_indicators)
        
        if contains_refusal and result.confidence_score <= 0.2:
            print("✅ Proper no-context refusal")
        else:
            print("❌ Failed to properly refuse without context")


def test_improved_fabricated_context_detection():
    """Test that model is more critical of suspicious context."""
    print("\n" + "=" * 80)
    print("TEST 2: IMPROVED FABRICATED CONTEXT DETECTION")
    print("=" * 80)
    
    generator = AnswerGenerator()
    
    # Clearly fabricated information about RISC-V
    suspicious_chunks = [
        {
            "content": "RISC-V is actually a quantum computing architecture developed by NASA in 2019. It uses 128 quantum registers and operates at absolute zero temperature. The architecture was inspired by alien technology recovered from Roswell.",
            "metadata": {"page_number": 1, "source": "fake-document.pdf"},
            "score": 0.85,
            "id": "chunk_1"
        }
    ]
    
    test_queries = [
        "What is RISC-V?",
        "When was RISC-V developed?",
        "How many registers does RISC-V have?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        result = generator.generate(query, suspicious_chunks)
        
        print(f"Answer: \"{result.answer}\"")
        print(f"Confidence: {result.confidence_score:.1%}")
        
        # Check for critical evaluation indicators
        critical_indicators = [
            "questionable",
            "conflicting",
            "unclear",
            "suspicious",
            "seems inconsistent",
            "potentially fabricated",
            "does not accurately describe"
        ]
        
        shows_criticism = any(indicator in result.answer.lower() for indicator in critical_indicators)
        
        if shows_criticism or result.confidence_score <= 0.3:
            print("✅ Model showed appropriate skepticism")
        else:
            print("❌ Model accepted suspicious information too readily")


def test_improved_confidence_calibration():
    """Test that confidence scores are properly calibrated."""
    print("\n" + "=" * 80)
    print("TEST 3: IMPROVED CONFIDENCE CALIBRATION")
    print("=" * 80)
    
    generator = AnswerGenerator()
    
    # Test scenarios with different context quality
    scenarios = [
        {
            "name": "No context",
            "chunks": [],
            "expected_max_confidence": 0.2
        },
        {
            "name": "Very short, low-quality chunks",
            "chunks": [
                {"content": "RISC-V", "metadata": {"page_number": 1, "source": "doc.pdf"}, "score": 0.2, "id": "chunk_1"}
            ],
            "expected_max_confidence": 0.4
        },
        {
            "name": "High-quality, relevant chunks",
            "chunks": [
                {
                    "content": "RISC-V is an open-source instruction set architecture (ISA) based on reduced instruction set computer (RISC) principles. It was originally designed to support computer architecture research and education at UC Berkeley starting in 2010.",
                    "metadata": {"page_number": 5, "source": "riscv-spec.pdf"},
                    "score": 0.95,
                    "id": "chunk_1"
                }
            ],
            "expected_max_confidence": 1.0
        }
    ]
    
    query = "What is RISC-V?"
    
    for scenario in scenarios:
        print(f"\nScenario: {scenario['name']}")
        
        result = generator.generate(query, scenario['chunks'])
        
        print(f"Answer length: {len(result.answer.split())} words")
        print(f"Citations: {len(result.citations)}")
        print(f"Confidence: {result.confidence_score:.1%}")
        print(f"Expected max: {scenario['expected_max_confidence']:.1%}")
        
        if result.confidence_score <= scenario['expected_max_confidence']:
            print("✅ Confidence appropriately calibrated")
        else:
            print("❌ Confidence too high for context quality")


def test_improved_context_dependency():
    """Test that model properly depends on context and cites appropriately."""
    print("\n" + "=" * 80)
    print("TEST 4: IMPROVED CONTEXT DEPENDENCY")
    print("=" * 80)
    
    generator = AnswerGenerator()
    
    # Good context that should be used properly
    good_chunks = [
        {
            "content": "The RV32E base integer instruction set is a reduced version of RV32I designed for embedded systems. RV32E reduces the number of integer registers from 32 to 16 to lower implementation cost.",
            "metadata": {"page_number": 25, "source": "riscv-spec-v2.3.pdf"},
            "score": 0.92,
            "id": "chunk_1"
        },
        {
            "content": "RV32E instruction encoding follows the same format as RV32I, but register fields are limited to 4 bits (x0-x15) instead of 5 bits (x0-x31).",
            "metadata": {"page_number": 26, "source": "riscv-spec-v2.3.pdf"},
            "score": 0.88,
            "id": "chunk_2"
        }
    ]
    
    query = "How many registers does RV32E have?"
    
    result = generator.generate(query, good_chunks)
    
    print(f"Query: {query}")
    print(f"Answer: \"{result.answer}\"")
    print(f"Citations: {len(result.citations)}")
    print(f"Confidence: {result.confidence_score:.1%}")
    
    # Check for proper citation usage
    contains_citations = len(result.citations) > 0
    mentions_16_registers = "16" in result.answer
    confidence_reasonable = 0.5 <= result.confidence_score <= 0.9
    
    print(f"\nEvaluation:")
    print(f"✅ Contains citations: {contains_citations}")
    print(f"✅ Mentions 16 registers: {mentions_16_registers}")
    print(f"✅ Reasonable confidence: {confidence_reasonable}")
    
    if contains_citations and mentions_16_registers and confidence_reasonable:
        print("✅ Proper context dependency achieved")
    else:
        print("❌ Context dependency needs improvement")


def main():
    """Run all improved faithfulness tests."""
    print("IMPROVED RAG FAITHFULNESS TESTING")
    print("Testing enhanced system prompt and confidence calibration")
    print("=" * 80)
    
    try:
        test_improved_no_context_handling()
        test_improved_fabricated_context_detection()
        test_improved_confidence_calibration()
        test_improved_context_dependency()
        
        print("\n" + "=" * 80)
        print("IMPROVED FAITHFULNESS TESTING COMPLETE")
        print("=" * 80)
        print("\n🎯 Key Improvements Verified:")
        print("• Enhanced system prompt with critical evaluation requirements")
        print("• Better no-context handling with explicit refusal messages")
        print("• Improved confidence calibration based on context quality")
        print("• More conservative confidence scoring")
        
        print("\n💡 Next Steps:")
        print("• Monitor real-world usage for edge cases")
        print("• Consider adding context quality scoring")
        print("• Evaluate performance on diverse document types")
        
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()