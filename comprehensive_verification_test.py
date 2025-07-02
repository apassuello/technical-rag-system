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


def generate_verification_report(standalone_results, pipeline_results, edge_case_results):
    """Generate comprehensive verification report."""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE VERIFICATION REPORT")
    print("=" * 80)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "standalone_tests": standalone_results,
        "pipeline_tests": pipeline_results,
        "edge_case_tests": edge_case_results,
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
    
    # Overall system health
    critical_components_working = no_context_working and pipeline_working
    quality_components_working = fake_context_working and good_context_working
    
    report['overall_assessment'] = {
        "critical_components": critical_components_working,
        "quality_components": quality_components_working,
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
        
        # Generate report
        report = generate_verification_report(standalone_results, pipeline_results, edge_case_results)
        
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