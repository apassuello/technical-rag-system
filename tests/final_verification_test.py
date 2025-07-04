#!/usr/bin/env python3
"""
Final verification test after all fixes.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared_utils.generation.answer_generator import AnswerGenerator


def test_final_verification():
    """Run final verification of all fixes."""
    print("🔍 FINAL VERIFICATION AFTER ALL FIXES")
    print("=" * 60)
    
    generator = AnswerGenerator()
    
    # Test 1: No context
    print("\n1️⃣ NO CONTEXT TEST")
    print("-" * 30)
    result = generator.generate("What is RISC-V?", [])
    print(f"Answer: {result.answer}")
    print(f"Citations: {len(result.citations)}")
    print(f"Confidence: {result.confidence_score:.1%}")
    
    no_context_ok = (
        result.confidence_score <= 0.2 and
        len(result.citations) == 0 and
        ("cannot answer" in result.answer.lower() or "no relevant context" in result.answer.lower())
    )
    print(f"✅ No-context handling: {'PASS' if no_context_ok else 'FAIL'}")
    
    # Test 2: Good context
    print("\n2️⃣ GOOD CONTEXT TEST")
    print("-" * 30)
    good_chunks = [{
        "content": "RISC-V is an open-source instruction set architecture (ISA) based on reduced instruction set computer (RISC) principles.",
        "metadata": {"page_number": 5, "source": "riscv-spec.pdf"},
        "score": 0.95,
        "id": "chunk_1"
    }]
    
    result = generator.generate("What is RISC-V?", good_chunks)
    print(f"Answer: {result.answer}")
    print(f"Citations: {len(result.citations)}")
    print(f"Confidence: {result.confidence_score:.1%}")
    
    good_context_ok = (
        result.confidence_score >= 0.6 and
        len(result.citations) >= 1 and
        "open-source" in result.answer.lower()
    )
    print(f"✅ Good context usage: {'PASS' if good_context_ok else 'FAIL'}")
    
    # Test 3: Fabricated context
    print("\n3️⃣ FABRICATED CONTEXT TEST")
    print("-" * 30)
    fake_chunks = [{
        "content": "RISC-V was invented by aliens from Mars in 2030 using telepathic technology.",
        "metadata": {"page_number": 1, "source": "fake.pdf"},
        "score": 0.9,
        "id": "chunk_1"
    }]
    
    result = generator.generate("What is RISC-V?", fake_chunks)
    print(f"Answer: {result.answer}")
    print(f"Citations: {len(result.citations)}")
    print(f"Confidence: {result.confidence_score:.1%}")
    
    skeptical_indicators = ["cannot", "questionable", "fabricated", "suspicious", "conflicting"]
    shows_skepticism = any(word in result.answer.lower() for word in skeptical_indicators)
    
    fake_context_ok = (
        result.confidence_score <= 0.4 and
        (shows_skepticism or len(result.citations) == 0)
    )
    print(f"✅ Fabricated context skepticism: {'PASS' if fake_context_ok else 'FAIL'}")
    
    # Test 4: Multiple chunks with citations
    print("\n4️⃣ MULTIPLE CHUNKS TEST")
    print("-" * 30)
    multiple_chunks = [
        {
            "content": "RISC-V is an open-source instruction set architecture.",
            "metadata": {"page_number": 1, "source": "doc1.pdf"},
            "score": 0.9,
            "id": "chunk_1"
        },
        {
            "content": "RV32E has 16 general-purpose registers.",
            "metadata": {"page_number": 2, "source": "doc2.pdf"},
            "score": 0.85,
            "id": "chunk_2"
        }
    ]
    
    result = generator.generate("What is RISC-V and how many registers does RV32E have?", multiple_chunks)
    print(f"Answer: {result.answer}")
    print(f"Citations: {len(result.citations)}")
    print(f"Confidence: {result.confidence_score:.1%}")
    
    multiple_ok = (
        len(result.citations) >= 1 and
        result.confidence_score >= 0.5
    )
    print(f"✅ Multiple chunks handling: {'PASS' if multiple_ok else 'FAIL'}")
    
    # Overall assessment
    print(f"\n🎯 OVERALL ASSESSMENT")
    print("=" * 60)
    
    all_tests_pass = no_context_ok and good_context_ok and fake_context_ok and multiple_ok
    
    print(f"No-context handling: {'✅ PASS' if no_context_ok else '❌ FAIL'}")
    print(f"Good context usage: {'✅ PASS' if good_context_ok else '❌ FAIL'}")
    print(f"Fabricated context skepticism: {'✅ PASS' if fake_context_ok else '❌ FAIL'}")
    print(f"Multiple chunks handling: {'✅ PASS' if multiple_ok else '❌ FAIL'}")
    
    if all_tests_pass:
        print(f"\n🎉 ALL TESTS PASS - SYSTEM IS PRODUCTION READY!")
        return True
    else:
        print(f"\n⚠️ SOME TESTS FAILED - SYSTEM NEEDS MORE WORK")
        return False


if __name__ == "__main__":
    success = test_final_verification()
    exit(0 if success else 1)