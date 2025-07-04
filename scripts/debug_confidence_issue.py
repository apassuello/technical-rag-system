#!/usr/bin/env python3
"""
Debug script for confidence calculation issues.

This script traces through the confidence calculation step-by-step
to identify why confidence is still consistently low.
"""

import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

from shared_utils.generation.answer_generator import AnswerGenerator


def debug_confidence_calculation():
    """Debug confidence calculation step by step."""
    print("🔍 DEBUGGING CONFIDENCE CALCULATION")
    print("=" * 60)
    
    # Initialize generator
    generator = AnswerGenerator(enable_calibration=True)
    
    # Test case: Good context that should get high confidence
    good_chunks = [{
        "id": "chunk_1",
        "content": "RISC-V is an open-source instruction set architecture (ISA) based on reduced instruction set computer (RISC) principles. It was originally designed to support computer architecture research and education at UC Berkeley.",
        "metadata": {"page_number": 1, "source": "riscv-spec.pdf"},
        "score": 0.95  # Very high relevance
    }]
    
    print("\n1. TEST SETUP")
    print("-" * 30)
    print(f"Query: 'What is RISC-V?'")
    print(f"Chunk score: {good_chunks[0]['score']}")
    print(f"Chunk content length: {len(good_chunks[0]['content'])} chars")
    print(f"Calibration enabled: {generator.enable_calibration}")
    print(f"Calibrator fitted: {generator.calibrator.is_fitted if generator.calibrator else 'None'}")
    
    # Generate answer with detailed logging
    print("\n2. GENERATING ANSWER")
    print("-" * 30)
    
    result = generator.generate("What is RISC-V?", good_chunks)
    
    print(f"Generated answer: {result.answer[:200]}...")
    print(f"Citations found: {len(result.citations)}")
    print(f"Final confidence: {result.confidence_score:.3f}")
    
    # Now let's manually trace through the confidence calculation
    print("\n3. MANUAL CONFIDENCE CALCULATION TRACE")
    print("-" * 45)
    
    # Recreate the calculation step by step
    answer = result.answer
    citations = result.citations
    chunks = good_chunks
    
    print(f"Input answer length: {len(answer.split())} words")
    print(f"Input citations: {len(citations)}")
    print(f"Input chunks: {len(chunks)}")
    
    # Step 1: Check if no chunks
    if not chunks:
        print("❌ No chunks provided")
        return 0.05
    else:
        print("✅ Chunks provided")
    
    # Step 2: Assess context quality
    scores = [chunk.get('score', 0) for chunk in chunks]
    max_relevance = max(scores) if scores else 0
    avg_relevance = sum(scores) / len(scores) if scores else 0
    
    print(f"Max relevance: {max_relevance}")
    print(f"Avg relevance: {avg_relevance}")
    
    # Step 3: Dynamic base confidence
    if max_relevance >= 0.8:
        base_confidence = 0.6
        print(f"✅ High-quality context detected, base confidence: {base_confidence}")
    elif max_relevance >= 0.6:
        base_confidence = 0.4
        print(f"✅ Good context detected, base confidence: {base_confidence}")
    elif max_relevance >= 0.4:
        base_confidence = 0.2
        print(f"⚠️ Fair context detected, base confidence: {base_confidence}")
    else:
        base_confidence = 0.05
        print(f"❌ Poor context detected, base confidence: {base_confidence}")
    
    confidence = base_confidence
    
    # Step 4: Check for strong uncertainty
    strong_uncertainty_phrases = [
        "does not contain sufficient information",
        "context does not provide", 
        "insufficient information",
        "cannot determine",
        "refuse to answer",
        "cannot answer",
        "does not contain relevant",
        "no relevant context",
        "missing from the provided context"
    ]
    
    strong_uncertainty_detected = any(phrase in answer.lower() for phrase in strong_uncertainty_phrases)
    print(f"Strong uncertainty detected: {strong_uncertainty_detected}")
    
    # Debug which phrase is triggering
    if strong_uncertainty_detected:
        triggering_phrases = [phrase for phrase in strong_uncertainty_phrases if phrase in answer.lower()]
        print(f"❌ Triggering phrases: {triggering_phrases}")
        # Show context around the triggering phrase
        for phrase in triggering_phrases:
            start_idx = answer.lower().find(phrase)
            context = answer[max(0, start_idx-50):start_idx+len(phrase)+50]
            print(f"   Context: '...{context}...'")
    
    print(f"Full answer being analyzed: '{answer}'")
    
    if strong_uncertainty_detected:
        final_confidence = min(0.1, confidence * 0.2)
        print(f"❌ Strong uncertainty penalty applied: {confidence} -> {final_confidence}")
        return final_confidence
    
    # Step 5: Check for weak uncertainty
    weak_uncertainty_phrases = [
        "unclear", "conflicting", "not specified", "questionable", 
        "not contained", "no mention", "no relevant", "missing", "not explicitly"
    ]
    
    weak_uncertainty_count = sum(1 for phrase in weak_uncertainty_phrases if phrase in answer.lower())
    print(f"Weak uncertainty phrases found: {weak_uncertainty_count}")
    
    if weak_uncertainty_count > 0:
        if max_relevance >= 0.7 and citations:
            penalty_factor = 0.8 ** weak_uncertainty_count
            print(f"⚠️ Weak uncertainty (good context): {confidence} * {penalty_factor:.3f}")
        else:
            penalty_factor = 0.5 ** weak_uncertainty_count
            print(f"⚠️ Weak uncertainty (poor context): {confidence} * {penalty_factor:.3f}")
        
        confidence *= penalty_factor
        print(f"Confidence after uncertainty penalty: {confidence:.3f}")
    
    # Step 6: Citation analysis
    print(f"Citations found: {len(citations)}")
    if citations and chunks:
        citation_ratio = len(citations) / min(len(chunks), 3)
        relevant_chunks = [c for c in chunks if c.get('score', 0) > 0.6]
        
        print(f"Citation ratio: {citation_ratio:.3f}")
        print(f"Relevant chunks (>0.6): {len(relevant_chunks)}")
        
        if relevant_chunks:
            boost = 0.25 * citation_ratio
            print(f"✅ Citation boost for relevant chunks: +{boost:.3f}")
            confidence += boost
            
            if len(citations) >= len(relevant_chunks) * 0.5:
                extra_boost = 0.15
                print(f"✅ Extra citation coverage boost: +{extra_boost}")
                confidence += extra_boost
    
    # Step 7: Final adjustments
    print(f"Confidence before final adjustments: {confidence:.3f}")
    
    # High-quality scenario bonus
    if (max_relevance >= 0.8 and citations and len(citations) > 0 and not strong_uncertainty_detected):
        bonus = 0.15
        print(f"✅ High-quality scenario bonus: +{bonus}")
        confidence += bonus
    
    # Cap at 95%
    raw_confidence = min(confidence, 0.95)
    print(f"Raw confidence (before calibration): {raw_confidence:.3f}")
    
    # Check calibration
    if generator.enable_calibration and generator.calibrator and generator.calibrator.is_fitted:
        try:
            calibrated_confidence = generator.calibrator.calibrate_confidence(raw_confidence)
            print(f"✅ Calibration applied: {raw_confidence:.3f} -> {calibrated_confidence:.3f}")
            print(f"Calibration temperature: {generator.calibrator.temperature:.3f}")
        except Exception as e:
            print(f"❌ Calibration failed: {e}")
            calibrated_confidence = raw_confidence
    else:
        print("❌ No calibration applied")
        calibrated_confidence = raw_confidence
    
    print(f"\n🎯 FINAL CONFIDENCE: {calibrated_confidence:.3f}")
    print(f"Expected: >0.6 for good context")
    print(f"Status: {'✅ PASS' if calibrated_confidence >= 0.6 else '❌ FAIL'}")
    
    return calibrated_confidence


def test_specific_issues():
    """Test specific issues that might be causing low confidence."""
    print("\n\n🔬 TESTING SPECIFIC ISSUES")
    print("=" * 60)
    
    generator = AnswerGenerator(enable_calibration=False)  # Test without calibration first
    
    # Test 1: Simple, clear answer
    print("\n1. Testing with calibration disabled...")
    good_chunks = [{
        "id": "chunk_1",
        "content": "RISC-V is an open-source instruction set architecture.",
        "metadata": {"page_number": 1, "source": "riscv-spec.pdf"},
        "score": 0.95
    }]
    
    result1 = generator.generate("What is RISC-V?", good_chunks)
    print(f"Without calibration: {result1.confidence_score:.3f}")
    
    # Test 2: With calibration but no fitting
    print("\n2. Testing with calibration enabled but not fitted...")
    generator2 = AnswerGenerator(enable_calibration=True)
    result2 = generator2.generate("What is RISC-V?", good_chunks)
    print(f"With unfitted calibration: {result2.confidence_score:.3f}")
    
    # Test 3: Check if answer contains uncertainty language
    print(f"\n3. Checking answer for uncertainty language...")
    print(f"Answer: {result2.answer}")
    
    uncertainty_phrases = ["missing", "not explicitly", "unclear", "conflicting", 
                          "insufficient", "cannot determine", "questionable"]
    
    found_phrases = [phrase for phrase in uncertainty_phrases if phrase in result2.answer.lower()]
    print(f"Uncertainty phrases found: {found_phrases}")
    
    if found_phrases:
        print("❌ Answer contains uncertainty language - this may be causing low confidence!")
    else:
        print("✅ No uncertainty language detected")


if __name__ == "__main__":
    confidence = debug_confidence_calculation()
    test_specific_issues()
    
    print(f"\n\n📊 SUMMARY")
    print("=" * 60)
    print(f"Final confidence achieved: {confidence:.3f}")
    print(f"Target confidence: >0.6")
    print(f"Issue resolved: {'✅ YES' if confidence >= 0.6 else '❌ NO'}")
    
    if confidence < 0.6:
        print(f"\n🔧 RECOMMENDATIONS:")
        print(f"1. Check if uncertainty language is being generated")
        print(f"2. Verify calibration is being applied correctly") 
        print(f"3. Review system prompt for clarity")
        print(f"4. Consider adjusting confidence calculation parameters")