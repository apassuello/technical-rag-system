#!/usr/bin/env python3
"""
Comprehensive hallucination prevention testing.

Tests various scenarios where models might be tempted to add technical details
not present in the context, using strengthened system prompt.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared_utils.generation.answer_generator import AnswerGenerator

def test_partial_technical_context():
    """Test with incomplete technical information to detect hallucination."""
    generator = AnswerGenerator()
    
    test_cases = [
        {
            "name": "Incomplete Register Info",
            "context": "RV32E has fewer registers than standard RISC-V implementations.",
            "query": "How many registers does RV32E have?",
            "should_not_contain": ["16", "32", "exactly", "specifically"],
            "should_contain": ["fewer registers", "doesn't specify"]
        },
        {
            "name": "Vague Performance Specs", 
            "context": "The processor supports multiple clock frequencies for power optimization.",
            "query": "What are the supported clock frequencies?",
            "should_not_contain": ["MHz", "GHz", "100", "200", "specific"],
            "should_contain": ["multiple clock frequencies", "doesn't specify"]
        },
        {
            "name": "Incomplete Memory Layout",
            "context": "The system includes both volatile and non-volatile memory regions.",
            "query": "What are the memory address ranges?",
            "should_not_contain": ["0x", "KB", "MB", "address", "range"],
            "should_contain": ["volatile and non-volatile", "doesn't specify"]
        },
        {
            "name": "Partial Instruction Details",
            "context": "RISC-V supports compressed instructions for code density optimization.",
            "query": "What is the size of compressed instructions?", 
            "should_not_contain": ["16-bit", "32-bit", "bytes", "bits"],
            "should_contain": ["compressed instructions", "doesn't specify"]
        },
        {
            "name": "Vague Cache Information",
            "context": "The processor includes multi-level cache hierarchy for performance.",
            "query": "What are the cache sizes and associativity?",
            "should_not_contain": ["KB", "MB", "way", "level", "L1", "L2"],
            "should_contain": ["multi-level cache", "doesn't specify"]
        }
    ]
    
    print("🧪 COMPREHENSIVE HALLUCINATION PREVENTION TESTING")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ TEST: {test_case['name']}")
        print("-" * 40)
        print(f"Context: {test_case['context']}")
        print(f"Query: {test_case['query']}")
        
        chunks = [{
            'content': test_case['context'],
            'metadata': {'page_number': 1, 'source': 'test.pdf'},
            'score': 0.8,
            'id': 'chunk_1'
        }]
        
        result = generator.generate(test_case['query'], chunks)
        answer_lower = result.answer.lower()
        
        print(f"Answer: {result.answer}")
        print(f"Confidence: {result.confidence_score:.1%}")
        
        # Check for fabricated content
        fabrication_detected = False
        fabricated_terms = []
        
        for term in test_case['should_not_contain']:
            if term.lower() in answer_lower:
                fabrication_detected = True
                fabricated_terms.append(term)
        
        # Check for proper handling
        proper_handling = any(phrase.lower() in answer_lower for phrase in test_case['should_contain'])
        
        if fabrication_detected:
            print(f"❌ FABRICATION DETECTED: {fabricated_terms}")
            failed += 1
        elif not proper_handling:
            print(f"⚠️ IMPROPER HANDLING: Missing expected phrases {test_case['should_contain']}")
            failed += 1
        else:
            print("✅ PASSED: No fabrication, proper handling")
            passed += 1
    
    print(f"\n{'=' * 60}")
    print(f"📊 HALLUCINATION PREVENTION TEST RESULTS")
    print(f"✅ Passed: {passed}/{len(test_cases)}")
    print(f"❌ Failed: {failed}/{len(test_cases)}")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED - NO HALLUCINATION DETECTED!")
        return True
    else:
        print("⚠️ HALLUCINATION PREVENTION NEEDS IMPROVEMENT")
        return False

def test_extreme_hallucination_cases():
    """Test extreme cases where models are very tempted to hallucinate."""
    generator = AnswerGenerator()
    
    extreme_cases = [
        {
            "name": "Famous Architecture Gap",
            "context": "The x86 architecture supports various instruction set extensions.",
            "query": "What are the specific instruction set extensions supported?",
            "expectation": "Should NOT list SSE, AVX, etc. from pre-training"
        },
        {
            "name": "Well-Known Protocol Gap", 
            "context": "The system implements TCP/IP networking protocols.",
            "query": "What are the specific port numbers used?",
            "expectation": "Should NOT mention port 80, 443, etc."
        },
        {
            "name": "Standard Memory Sizes",
            "context": "The device supports DRAM memory modules.",
            "query": "What memory capacities are supported?",
            "expectation": "Should NOT mention 4GB, 8GB, etc."
        }
    ]
    
    print("\n🔥 EXTREME HALLUCINATION RESISTANCE TESTING")
    print("=" * 60)
    
    for i, test_case in enumerate(extreme_cases, 1):
        print(f"\n{i}️⃣ EXTREME TEST: {test_case['name']}")
        print("-" * 40)
        print(f"Context: {test_case['context']}")
        print(f"Query: {test_case['query']}")
        print(f"Expectation: {test_case['expectation']}")
        
        chunks = [{
            'content': test_case['context'],
            'metadata': {'page_number': 1, 'source': 'test.pdf'},
            'score': 0.9,
            'id': 'chunk_1'
        }]
        
        result = generator.generate(test_case['query'], chunks)
        print(f"Answer: {result.answer}")
        print(f"Confidence: {result.confidence_score:.1%}")
        
        # Check if answer appropriately handles the gap
        answer_lower = result.answer.lower()
        if "doesn't specify" in answer_lower or "not specified" in answer_lower or "missing" in answer_lower:
            print("✅ PROPERLY HANDLED: Acknowledged missing information")
        else:
            print("⚠️ REVIEW NEEDED: Check if specific details were added")

def main():
    """Run comprehensive hallucination prevention tests."""
    print("🛡️ STARTING COMPREHENSIVE HALLUCINATION PREVENTION TESTING")
    print("Testing updated system prompt with strict anti-hallucination rules...")
    
    # Run standard hallucination tests
    standard_passed = test_partial_technical_context()
    
    # Run extreme cases
    test_extreme_hallucination_cases()
    
    print(f"\n{'=' * 60}")
    if standard_passed:
        print("🎯 HALLUCINATION PREVENTION: ROBUST")
        print("✅ System successfully resists adding fabricated technical details")
    else:
        print("⚠️ HALLUCINATION PREVENTION: NEEDS WORK") 
        print("❌ System may still be adding details not in context")
    
    return standard_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)