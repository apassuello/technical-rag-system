#!/usr/bin/env python3
"""
Comprehensive verification test for the complete RAG system.

This test will verify:
1. End-to-end pipeline functionality
2. Actual behavior vs expected behavior
3. Real document processing and retrieval
4. Answer generation with actual context
5. Manual inspection of all outputs
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

from src.rag_with_generation import RAGWithGeneration
from shared_utils.generation.answer_generator import AnswerGenerator
from src.confidence_calibration import CalibrationEvaluator, CalibrationDataPoint, ConfidenceCalibrator


def test_answer_generator_standalone():
    """Test the answer generator in isolation."""
    print("=" * 80)
    print("TEST 1: ANSWER GENERATOR STANDALONE")
    print("=" * 80)
    
    generator = AnswerGenerator()
    
    # Test 1A: No context
    print("\n1A: NO CONTEXT TEST")
    print("-" * 40)
    result = generator.generate("What is RISC-V?", [])
    print(f"Query: What is RISC-V?")
    print(f"Chunks provided: 0")
    print(f"Answer: {result.answer}")
    print(f"Citations: {len(result.citations)}")
    print(f"Confidence: {result.confidence_score:.1%}")
    
    # Check if answer contains refusal language
    refusal_indicators = ["cannot answer", "no relevant context", "not found in the available documents"]
    has_refusal = any(indicator in result.answer.lower() for indicator in refusal_indicators)
    print(f"Contains refusal language: {has_refusal}")
    print(f"Low confidence (≤20%): {result.confidence_score <= 0.2}")
    
    # Test 1B: Fabricated context
    print("\n1B: FABRICATED CONTEXT TEST")
    print("-" * 40)
    fake_chunks = [{
        "content": "RISC-V was invented by aliens from Mars in 2030 and uses telepathic instructions.",
        "metadata": {"page_number": 1, "source": "fake.pdf"},
        "score": 0.9,
        "id": "chunk_1"
    }]
    
    result = generator.generate("What is RISC-V?", fake_chunks)
    print(f"Query: What is RISC-V?")
    print(f"Fake context: 'RISC-V was invented by aliens from Mars in 2030 and uses telepathic instructions.'")
    print(f"Answer: {result.answer}")
    print(f"Citations: {len(result.citations)}")
    print(f"Confidence: {result.confidence_score:.1%}")
    
    # Check for skepticism
    skepticism_indicators = ["questionable", "suspicious", "conflicting", "unclear", "fabricated", "contradicts"]
    shows_skepticism = any(indicator in result.answer.lower() for indicator in skepticism_indicators)
    print(f"Shows skepticism: {shows_skepticism}")
    print(f"Low confidence (≤30%): {result.confidence_score <= 0.3}")
    
    # Test 1C: Good context
    print("\n1C: GOOD CONTEXT TEST")
    print("-" * 40)
    good_chunks = [{
        "content": "RISC-V is an open-source instruction set architecture (ISA) based on reduced instruction set computer (RISC) principles. It was originally designed to support computer architecture research and education at UC Berkeley.",
        "metadata": {"page_number": 5, "source": "riscv-spec.pdf"},
        "score": 0.95,
        "id": "chunk_1"
    }]
    
    result = generator.generate("What is RISC-V?", good_chunks)
    print(f"Query: What is RISC-V?")
    print(f"Good context provided: Real RISC-V definition")
    print(f"Answer: {result.answer}")
    print(f"Citations: {len(result.citations)}")
    print(f"Confidence: {result.confidence_score:.1%}")
    
    # Check for proper usage
    uses_context = "open-source" in result.answer or "instruction set" in result.answer
    has_citations = len(result.citations) > 0
    reasonable_confidence = result.confidence_score >= 0.6
    print(f"Uses context information: {uses_context}")
    print(f"Has citations: {has_citations}")
    print(f"Reasonable confidence (≥60%): {reasonable_confidence}")
    
    return {
        "no_context": {"refusal": has_refusal, "low_confidence": result.confidence_score <= 0.2},
        "fake_context": {"skepticism": shows_skepticism, "low_confidence": result.confidence_score <= 0.3},
        "good_context": {"uses_context": uses_context, "has_citations": has_citations, "reasonable_confidence": reasonable_confidence}
    }


def test_full_rag_pipeline():
    """Test the complete RAG pipeline with real documents."""
    print("\n" + "=" * 80)
    print("TEST 2: FULL RAG PIPELINE WITH REAL DOCUMENTS")
    print("=" * 80)
    
    try:
        # Initialize RAG system
        rag = RAGWithGeneration()
        
        # Check if documents are indexed
        if len(rag.chunks) == 0:
            print("No documents indexed. Loading test documents...")
            test_folder = Path("data/test")
            if test_folder.exists():
                results = rag.index_documents(test_folder)
                total_chunks = sum(results.values())
                print(f"✅ Indexed {total_chunks} chunks from {len(results)} documents")
            else:
                print("❌ No test documents found")
                return {"error": "No test documents"}
        
        print(f"Documents indexed: {len(rag.chunks)} chunks available")
        
        # Test 2A: Question with good context available
        print("\n2A: QUESTION WITH AVAILABLE CONTEXT")
        print("-" * 50)
        query = "How does RISC-V determine instruction length?"
        
        result = rag.query_with_answer(
            question=query,
            top_k=3,
            use_hybrid=True,
            return_context=True
        )
        
        print(f"Query: {query}")
        print(f"Retrieved chunks: {len(result.get('context', []))}")
        print(f"Answer: {result['answer']}")
        print(f"Citations: {len(result.get('citations', []))}")
        print(f"Confidence: {result.get('confidence', 0):.1%}")
        
        # Examine context quality
        if 'context' in result:
            print(f"\nContext examination:")
            for i, chunk in enumerate(result['context'][:2], 1):
                content = chunk.get('text', chunk.get('content', ''))[:100]
                print(f"  Chunk {i}: {content}...")
        
        # Test 2B: Question with no relevant context
        print("\n2B: QUESTION WITH NO RELEVANT CONTEXT")
        print("-" * 50)
        query = "What is the capital of Mars?"
        
        result = rag.query_with_answer(
            question=query,
            top_k=3,
            use_hybrid=True,
            return_context=True
        )
        
        print(f"Query: {query}")
        print(f"Retrieved chunks: {len(result.get('context', []))}")
        print(f"Answer: {result['answer']}")
        print(f"Confidence: {result.get('confidence', 0):.1%}")
        
        # Check if system properly handles irrelevant context
        low_confidence = result.get('confidence', 1.0) <= 0.3
        contains_disclaimer = any(phrase in result['answer'].lower() for phrase in [
            "does not contain", "insufficient", "cannot", "not found"
        ])
        
        print(f"Low confidence for irrelevant query: {low_confidence}")
        print(f"Contains disclaimer: {contains_disclaimer}")
        
        return {
            "pipeline_working": True,
            "good_query": {"has_context": len(result.get('context', [])) > 0},
            "irrelevant_query": {"low_confidence": low_confidence, "has_disclaimer": contains_disclaimer}
        }
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


def test_edge_cases():
    """Test edge cases and potential failure modes."""
    print("\n" + "=" * 80)
    print("TEST 3: EDGE CASES AND FAILURE MODES")
    print("=" * 80)
    
    generator = AnswerGenerator()
    
    edge_cases = [
        {
            "name": "Empty string chunks",
            "chunks": [{"content": "", "metadata": {"page_number": 1, "source": "empty.pdf"}, "score": 0.1, "id": "chunk_1"}],
            "query": "What is RISC-V?"
        },
        {
            "name": "Very short chunks",
            "chunks": [{"content": "RISC-V.", "metadata": {"page_number": 1, "source": "short.pdf"}, "score": 0.5, "id": "chunk_1"}],
            "query": "What is RISC-V?"
        },
        {
            "name": "Contradictory chunks",
            "chunks": [
                {"content": "RISC-V has 32 registers.", "metadata": {"page_number": 1, "source": "doc1.pdf"}, "score": 0.9, "id": "chunk_1"},
                {"content": "RISC-V has 16 registers.", "metadata": {"page_number": 2, "source": "doc2.pdf"}, "score": 0.9, "id": "chunk_2"}
            ],
            "query": "How many registers does RISC-V have?"
        },
        {
            "name": "Technical jargon chunks",
            "chunks": [{"content": "The RISC-V ISA specification defines base integer instruction formats including R-type, I-type, S-type, B-type, U-type, and J-type formats with varying immediate field encodings.", "metadata": {"page_number": 10, "source": "spec.pdf"}, "score": 0.95, "id": "chunk_1"}],
            "query": "What are RISC-V instruction formats?"
        },
        {
            "name": "Hallucination-prone: Incomplete register info",
            "chunks": [{"content": "RV32E has fewer registers than standard RISC-V implementations.", "metadata": {"page_number": 1, "source": "test.pdf"}, "score": 0.8, "id": "chunk_1"}],
            "query": "How many registers does RV32E have?"
        },
        {
            "name": "Hallucination-prone: Vague performance specs",
            "chunks": [{"content": "The processor supports multiple clock frequencies for power optimization.", "metadata": {"page_number": 1, "source": "test.pdf"}, "score": 0.8, "id": "chunk_1"}],
            "query": "What are the supported clock frequencies?"
        },
        {
            "name": "Hallucination-prone: Partial instruction details",
            "chunks": [{"content": "RISC-V supports compressed instructions for code density optimization.", "metadata": {"page_number": 1, "source": "test.pdf"}, "score": 0.8, "id": "chunk_1"}],
            "query": "What is the size of compressed instructions?"
        }
    ]
    
    results = {}
    
    for case in edge_cases:
        print(f"\n3.{edge_cases.index(case) + 1}: {case['name'].upper()}")
        print("-" * 50)
        
        result = generator.generate(case['query'], case['chunks'])
        
        print(f"Query: {case['query']}")
        print(f"Context: {len(case['chunks'])} chunk(s)")
        print(f"Answer: {result.answer}")
        print(f"Confidence: {result.confidence_score:.1%}")
        print(f"Citations: {len(result.citations)}")
        
        # Analyze appropriateness of response
        answer_length = len(result.answer.split())
        has_uncertainty = any(phrase in result.answer.lower() for phrase in [
            "unclear", "conflicting", "insufficient", "does not contain"
        ])
        
        print(f"Answer length: {answer_length} words")
        print(f"Shows uncertainty: {has_uncertainty}")
        
        results[case['name']] = {
            "confidence": result.confidence_score,
            "answer_length": answer_length,
            "shows_uncertainty": has_uncertainty,
            "has_citations": len(result.citations) > 0
        }
    
    return results


def test_confidence_calibration():
    """Test the confidence calibration framework."""
    print("\n" + "=" * 80)
    print("TEST 4: CONFIDENCE CALIBRATION FRAMEWORK")
    print("=" * 80)
    
    print("\n4A: CALIBRATION METRICS TEST")
    print("-" * 40)
    
    # Create test data with known calibration issues
    import numpy as np
    np.random.seed(42)
    
    # Simulate overconfident predictions
    n_samples = 50
    true_correctness = np.random.binomial(1, 0.6, n_samples)  # 60% actual accuracy
    predicted_confidence = np.random.beta(8, 3, n_samples)    # Overconfident (high values)
    
    # Create calibration data points
    data_points = []
    for i, (conf, correct) in enumerate(zip(predicted_confidence, true_correctness)):
        data_points.append(CalibrationDataPoint(
            predicted_confidence=conf,
            actual_correctness=float(correct),
            query=f"test_query_{i}",
            answer=f"test_answer_{i}",
            context_relevance=0.7,
            metadata={"test_case": i}
        ))
    
    # Evaluate calibration
    evaluator = CalibrationEvaluator()
    metrics_before = evaluator.evaluate_calibration(data_points)
    
    print(f"Before calibration:")
    print(f"  ECE (Expected Calibration Error): {metrics_before.ece:.3f}")
    print(f"  ACE (Adaptive Calibration Error): {metrics_before.ace:.3f}")
    print(f"  MCE (Maximum Calibration Error): {metrics_before.mce:.3f}")
    print(f"  Brier Score: {metrics_before.brier_score:.3f}")
    
    print("\n4B: TEMPERATURE SCALING TEST")
    print("-" * 40)
    
    # Fit temperature scaling
    calibrator = ConfidenceCalibrator()
    optimal_temp = calibrator.fit_temperature_scaling(
        predicted_confidence.tolist(),
        true_correctness.tolist()
    )
    
    print(f"Optimal temperature parameter: {optimal_temp:.3f}")
    print(f"Temperature > 1.0 (overconfident): {'YES' if optimal_temp > 1.0 else 'NO'}")
    
    # Apply calibration
    calibrated_confidences = [
        calibrator.calibrate_confidence(conf) for conf in predicted_confidence
    ]
    
    # Create calibrated data points
    calibrated_data_points = []
    for i, (conf, correct) in enumerate(zip(calibrated_confidences, true_correctness)):
        calibrated_data_points.append(CalibrationDataPoint(
            predicted_confidence=conf,
            actual_correctness=float(correct),
            query=f"test_query_{i}",
            answer=f"test_answer_{i}",
            context_relevance=0.7,
            metadata={"test_case": i, "calibrated": True}
        ))
    
    # Re-evaluate
    metrics_after = evaluator.evaluate_calibration(calibrated_data_points)
    
    print(f"\nAfter temperature scaling:")
    print(f"  ECE: {metrics_after.ece:.3f}")
    print(f"  ACE: {metrics_after.ace:.3f}")
    print(f"  MCE: {metrics_after.mce:.3f}")
    print(f"  Brier Score: {metrics_after.brier_score:.3f}")
    
    # Calculate improvements
    ece_improvement = (metrics_before.ece - metrics_after.ece) / metrics_before.ece * 100
    ace_improvement = (metrics_before.ace - metrics_after.ace) / metrics_before.ace * 100
    brier_improvement = (metrics_before.brier_score - metrics_after.brier_score) / metrics_before.brier_score * 100
    
    print(f"\nCalibration improvements:")
    print(f"  ECE improvement: {ece_improvement:.1f}%")
    print(f"  ACE improvement: {ace_improvement:.1f}%")
    print(f"  Brier improvement: {brier_improvement:.1f}%")
    
    print("\n4C: CALIBRATION INTEGRATION TEST")
    print("-" * 40)
    
    # Test integration with actual RAG system
    generator = AnswerGenerator()
    
    # Test cases with different expected confidence levels
    test_cases = [
        {
            "name": "good_context",
            "query": "What is RISC-V?",
            "chunks": [
                {
                    "id": "chunk_1",
                    "content": "RISC-V is an open-source instruction set architecture (ISA) based on reduced instruction set computer (RISC) principles.",
                    "metadata": {"page_number": 1, "source": "riscv-spec.pdf"},
                    "score": 0.95
                }
            ],
            "expected_confidence_range": (0.6, 1.0)
        },
        {
            "name": "poor_context",
            "query": "What is RISC-V?",
            "chunks": [
                {
                    "id": "chunk_1", 
                    "content": "Copyright 2023. All rights reserved. This document contains confidential information.",
                    "metadata": {"page_number": 1, "source": "license.pdf"},
                    "score": 0.1
                }
            ],
            "expected_confidence_range": (0.0, 0.2)
        }
    ]
    
    calibration_results = {}
    for case in test_cases:
        result = generator.generate(case["query"], case["chunks"])
        
        expected_min, expected_max = case["expected_confidence_range"]
        confidence_appropriate = expected_min <= result.confidence_score <= expected_max
        
        print(f"\nCase: {case['name']}")
        print(f"  Confidence: {result.confidence_score:.3f}")
        print(f"  Expected range: {expected_min:.1f}-{expected_max:.1f}")
        print(f"  Appropriate: {'YES' if confidence_appropriate else 'NO'}")
        
        calibration_results[case['name']] = {
            "confidence": result.confidence_score,
            "expected_range": case["expected_confidence_range"],
            "appropriate": confidence_appropriate
        }
    
    return {
        "metrics_before": {
            "ece": metrics_before.ece,
            "ace": metrics_before.ace,
            "mce": metrics_before.mce,
            "brier_score": metrics_before.brier_score
        },
        "metrics_after": {
            "ece": metrics_after.ece,
            "ace": metrics_after.ace,
            "mce": metrics_after.mce,
            "brier_score": metrics_after.brier_score
        },
        "optimal_temperature": optimal_temp,
        "improvements": {
            "ece_improvement_pct": ece_improvement,
            "ace_improvement_pct": ace_improvement,
            "brier_improvement_pct": brier_improvement
        },
        "integration_tests": calibration_results
    }


def generate_verification_report(standalone_results, pipeline_results, edge_case_results, calibration_results=None):
    """Generate comprehensive verification report."""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE VERIFICATION REPORT")
    print("=" * 80)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "standalone_tests": standalone_results,
        "pipeline_tests": pipeline_results,
        "edge_case_tests": edge_case_results,
        "calibration_tests": calibration_results,
        "overall_assessment": {}
    }
    
    # Assess each component
    print("\n📊 COMPONENT ASSESSMENT")
    print("-" * 40)
    
    # No-context handling
    no_context_working = (
        standalone_results.get('no_context', {}).get('refusal', False) and
        standalone_results.get('no_context', {}).get('low_confidence', False)
    )
    print(f"✅ No-context refusal: {'PASS' if no_context_working else 'FAIL'}")
    
    # Fabricated context detection
    fake_context_working = (
        standalone_results.get('fake_context', {}).get('skepticism', False) or
        standalone_results.get('fake_context', {}).get('low_confidence', False)
    )
    print(f"✅ Fabricated context detection: {'PASS' if fake_context_working else 'FAIL'}")
    
    # Good context usage
    good_context_working = (
        standalone_results.get('good_context', {}).get('uses_context', False) and
        standalone_results.get('good_context', {}).get('has_citations', False) and
        standalone_results.get('good_context', {}).get('reasonable_confidence', False)
    )
    print(f"✅ Good context usage: {'PASS' if good_context_working else 'FAIL'}")
    
    # Pipeline functionality
    pipeline_working = not ('error' in pipeline_results)
    print(f"✅ Pipeline functionality: {'PASS' if pipeline_working else 'FAIL'}")
    
    # Confidence calibration
    if calibration_results:
        ece_improvement = calibration_results['improvements']['ece_improvement_pct']
        calibration_working = ece_improvement > 20  # At least 20% ECE improvement
        print(f"✅ Confidence calibration (>{ece_improvement:.1f}% ECE improvement): {'PASS' if calibration_working else 'FAIL'}")
        
        # Check integration tests
        good_context_appropriate = calibration_results['integration_tests']['good_context']['appropriate']
        poor_context_appropriate = calibration_results['integration_tests']['poor_context']['appropriate']
        integration_working = good_context_appropriate and poor_context_appropriate
        print(f"✅ Calibration integration: {'PASS' if integration_working else 'FAIL'}")
    else:
        calibration_working = False
        integration_working = False
        print(f"✅ Confidence calibration: SKIPPED")
    
    # Overall system health
    critical_components_working = no_context_working and pipeline_working
    quality_components_working = fake_context_working and good_context_working
    
    # Include calibration in quality assessment if tested
    if calibration_results:
        quality_components_working = quality_components_working and calibration_working and integration_working
    
    report['overall_assessment'] = {
        "critical_components": critical_components_working,
        "quality_components": quality_components_working,
        "calibration_framework": calibration_working if calibration_results else None,
        "production_ready": critical_components_working and quality_components_working
    }
    
    print(f"\n🎯 OVERALL SYSTEM STATUS")
    print("-" * 40)
    print(f"Critical components (no-context, pipeline): {'✅ WORKING' if critical_components_working else '❌ BROKEN'}")
    print(f"Quality components (skepticism, context usage): {'✅ WORKING' if quality_components_working else '❌ BROKEN'}")
    print(f"Production readiness: {'✅ READY' if report['overall_assessment']['production_ready'] else '❌ NOT READY'}")
    
    # Save detailed report
    report_file = f"verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📁 Detailed report saved: {report_file}")
    
    return report


def main():
    """Run comprehensive verification."""
    print("🔍 COMPREHENSIVE RAG SYSTEM VERIFICATION")
    print("Testing all components with fresh perspective")
    print("=" * 80)
    
    try:
        # Run all tests
        standalone_results = test_answer_generator_standalone()
        pipeline_results = test_full_rag_pipeline()
        edge_case_results = test_edge_cases()
        calibration_results = test_confidence_calibration()
        
        # Generate report
        report = generate_verification_report(standalone_results, pipeline_results, edge_case_results, calibration_results)
        
        # Final assessment
        if report['overall_assessment']['production_ready']:
            print("\n🎉 VERIFICATION COMPLETE: SYSTEM IS PRODUCTION READY")
        else:
            print("\n⚠️ VERIFICATION COMPLETE: SYSTEM NEEDS FIXES BEFORE PRODUCTION")
            
        return report
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


if __name__ == "__main__":
    main()