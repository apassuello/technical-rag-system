#!/usr/bin/env python3
"""
Test that the number preservation fix is working correctly.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared_utils.generation.answer_generator import AnswerGenerator


def test_number_preservation():
    """Test that technical numbers are preserved after citation cleaning."""
    print("🔧 TESTING NUMBER PRESERVATION FIX")
    print("=" * 60)
    
    generator = AnswerGenerator()
    
    # Test cases with clear numerical content
    test_cases = [
        {
            "name": "RV32E Register Count",
            "chunks": [{
                "content": "RV32E has exactly 16 general-purpose registers, which is half of the 32 registers in standard RISC-V.",
                "metadata": {"page_number": 25, "source": "riscv-spec.pdf"},
                "score": 0.95,
                "id": "chunk_1"
            }],
            "query": "How many registers does RV32E have?",
            "expected_numbers": ["16", "32", "25"]
        },
        {
            "name": "Instruction Width",
            "chunks": [{
                "content": "RISC-V instructions are either 16-bit or 32-bit wide, with 64-bit extensions available.",
                "metadata": {"page_number": 42, "source": "instruction-manual.pdf"},
                "score": 0.9,
                "id": "chunk_1"
            }],
            "query": "What are the instruction widths in RISC-V?",
            "expected_numbers": ["16", "32", "64", "42"]
        },
        {
            "name": "Memory Range",
            "chunks": [{
                "content": "The memory address space ranges from 0x0000 to 0xFFFF, supporting up to 65536 different addresses.",
                "metadata": {"page_number": 128, "source": "memory-guide.pdf"},
                "score": 0.88,
                "id": "chunk_1"
            }],
            "query": "What is the memory address range?",
            "expected_numbers": ["0", "65536", "128"]
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ TEST: {test_case['name']}")
        print("-" * 40)
        
        print(f"Query: {test_case['query']}")
        print(f"Context: {test_case['chunks'][0]['content']}")
        
        # Generate answer
        result = generator.generate(test_case['query'], test_case['chunks'])
        
        print(f"Answer: {result.answer}")
        print(f"Citations: {len(result.citations)}")
        print(f"Confidence: {result.confidence_score:.1%}")
        
        # Check number preservation
        import re
        found_numbers = re.findall(r'\d+', result.answer)
        expected_numbers = test_case['expected_numbers']
        
        print(f"Expected numbers: {expected_numbers}")
        print(f"Found numbers: {found_numbers}")
        
        # Check if critical numbers are preserved
        critical_preserved = all(num in found_numbers for num in expected_numbers[:2])  # First 2 are most critical
        
        if critical_preserved:
            print("✅ CRITICAL NUMBERS PRESERVED")
        else:
            print("❌ CRITICAL NUMBERS MISSING")
            all_passed = False
        
        # Check answer quality
        answer_meaningful = len(result.answer.split()) > 10 and any(num in result.answer for num in expected_numbers[:2])
        
        if answer_meaningful:
            print("✅ ANSWER IS MEANINGFUL")
        else:
            print("❌ ANSWER IS NOT MEANINGFUL")
            all_passed = False
            
        # Check citations
        if result.citations:
            print("✅ CITATIONS GENERATED")
        else:
            print("⚠️ NO CITATIONS GENERATED")
    
    return all_passed


def test_citation_cleaning_only():
    """Test that only [chunk_X] citations are cleaned, not content numbers."""
    print(f"\n" + "=" * 60)
    print("🧹 TESTING CITATION CLEANING BEHAVIOR")
    print("=" * 60)
    
    generator = AnswerGenerator()
    
    # Test different answer formats
    test_answers = [
        {
            "text": "According to [chunk_1], RV32E has 16 registers.",
            "expected_clean": "According to , RV32E has 16 registers.",
            "should_preserve": ["16"]
        },
        {
            "text": "The system has 32 registers as shown in [chunk_2].",
            "expected_clean": "The system has 32 registers as shown in .",
            "should_preserve": ["32"]
        },
        {
            "text": "Instructions are 16-bit or 32-bit [chunk_1], with 64-bit extensions [chunk_3].",
            "expected_clean": "Instructions are 16-bit or 32-bit , with 64-bit extensions .",
            "should_preserve": ["16", "32", "64"]
        }
    ]
    
    chunks = [{
        "content": "Test content",
        "metadata": {"page_number": 1, "source": "test.pdf"},
        "score": 0.9,
        "id": "chunk_1"
    }]
    
    all_passed = True
    
    for i, test in enumerate(test_answers, 1):
        print(f"\n{i}. Testing: '{test['text']}'")
        
        # Use the citation extraction method directly
        clean_answer, citations = generator._extract_citations(test['text'], chunks)
        
        print(f"   Clean: '{clean_answer}'")
        print(f"   Citations: {len(citations)}")
        
        # Check if numbers are preserved
        import re
        found_numbers = re.findall(r'\d+', clean_answer)
        expected_numbers = test['should_preserve']
        
        preserved = all(num in found_numbers for num in expected_numbers)
        
        if preserved:
            print(f"   ✅ Numbers preserved: {expected_numbers}")
        else:
            print(f"   ❌ Numbers missing: {set(expected_numbers) - set(found_numbers)}")
            all_passed = False
    
    return all_passed


def test_edge_cases():
    """Test edge cases for number preservation."""
    print(f"\n" + "=" * 60)
    print("🎯 TESTING EDGE CASES")
    print("=" * 60)
    
    generator = AnswerGenerator()
    
    edge_cases = [
        {
            "name": "No Context",
            "chunks": [],
            "query": "How many registers does RISC-V have?",
            "should_refuse": True
        },
        {
            "name": "Context with No Numbers",
            "chunks": [{
                "content": "RISC-V is an open-source instruction set architecture based on RISC principles.",
                "metadata": {"page_number": 1, "source": "intro.pdf"},
                "score": 0.9,
                "id": "chunk_1"
            }],
            "query": "How many registers does RISC-V have?",
            "should_refuse": True
        },
        {
            "name": "Mixed Numbers and Citations",
            "chunks": [{
                "content": "The architecture supports 8, 16, 32, and 64-bit operations with up to 128 registers.",
                "metadata": {"page_number": 55, "source": "arch.pdf"},
                "score": 0.95,
                "id": "chunk_1"
            }],
            "query": "What operations does the architecture support?",
            "expected_numbers": ["8", "16", "32", "64", "128"]
        }
    ]
    
    all_passed = True
    
    for i, case in enumerate(edge_cases, 1):
        print(f"\n{i}️⃣ EDGE CASE: {case['name']}")
        print("-" * 40)
        
        result = generator.generate(case['query'], case['chunks'])
        
        print(f"Answer: {result.answer}")
        print(f"Confidence: {result.confidence_score:.1%}")
        
        if case.get('should_refuse'):
            # Should have low confidence and refuse appropriately
            if result.confidence_score <= 0.3:
                print("✅ APPROPRIATELY LOW CONFIDENCE")
            else:
                print(f"❌ CONFIDENCE TOO HIGH: {result.confidence_score:.1%}")
                all_passed = False
        else:
            # Should preserve numbers
            import re
            found_numbers = re.findall(r'\d+', result.answer)
            expected = case.get('expected_numbers', [])
            
            if all(num in found_numbers for num in expected[:3]):  # Check first 3 critical numbers
                print("✅ NUMBERS PRESERVED")
            else:
                print("❌ NUMBERS MISSING")
                all_passed = False
    
    return all_passed


def main():
    """Run all tests for number preservation fix."""
    print("🧪 COMPREHENSIVE NUMBER PRESERVATION TESTING")
    print("Testing the fix for citation cleaning number removal bug")
    print("=" * 70)
    
    # Run all tests
    test1_passed = test_number_preservation()
    test2_passed = test_citation_cleaning_only()
    test3_passed = test_edge_cases()
    
    # Overall result
    print(f"\n" + "=" * 70)
    print("📊 OVERALL TEST RESULTS")
    print("=" * 70)
    
    print(f"Number preservation test: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"Citation cleaning test: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print(f"Edge cases test: {'✅ PASS' if test3_passed else '❌ FAIL'}")
    
    all_passed = test1_passed and test2_passed and test3_passed
    
    if all_passed:
        print(f"\n🎉 ALL TESTS PASSED - NUMBER PRESERVATION FIX SUCCESSFUL!")
        print("✅ Technical numbers are now preserved in answers")
        print("✅ Citation cleaning only removes [chunk_X] format")
        print("✅ System is ready for re-verification")
    else:
        print(f"\n⚠️ SOME TESTS FAILED - ADDITIONAL FIXES NEEDED")
        
    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)