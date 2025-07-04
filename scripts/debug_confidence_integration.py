#!/usr/bin/env python3
"""
Debug the confidence integration bug by comparing direct generator vs RAG pipeline.

This test will directly compare:
1. AnswerGenerator.generate() called directly
2. RAGWithGeneration.query_with_answer() integrated pipeline

To identify where the confidence score gets artificially suppressed.
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.rag_with_generation import RAGWithGeneration
from shared_utils.generation.answer_generator import AnswerGenerator

def debug_confidence_discrepancy():
    """Debug confidence score discrepancy between direct and integrated calls."""
    print("🔍 DEBUGGING CONFIDENCE INTEGRATION BUG")
    print("=" * 80)
    print("Comparing direct generator vs integrated RAG pipeline")
    print("=" * 80)
    
    # Initialize systems
    rag = RAGWithGeneration()
    generator = AnswerGenerator()
    
    # Load a minimal document set for testing
    print("\n📚 Loading test documents...")
    test_doc = Path("data/test/riscv-base-instructions.pdf")
    if test_doc.exists():
        result = rag.index_document(test_doc)
        print(f"✅ Loaded {result} chunks from RISC-V instructions document")
    else:
        print("❌ Test document not found")
        return
    
    # Test query
    test_query = "What is RISC-V?"
    print(f"\n🧪 Test Query: '{test_query}'")
    print("-" * 60)
    
    # Step 1: Get RAG pipeline result (current buggy behavior)
    print("\n1️⃣ INTEGRATED RAG PIPELINE TEST")
    print("-" * 40)
    
    rag_result = rag.query_with_answer(
        question=test_query,
        top_k=5,
        use_hybrid=True,
        return_context=True
    )
    
    rag_confidence = rag_result.get('confidence', 0)
    rag_chunks = rag_result.get('context', [])
    rag_answer = rag_result.get('answer', '')
    rag_citations = len(rag_result.get('citations', []))
    
    print(f"RAG Confidence: {rag_confidence:.1%}")
    print(f"RAG Retrieved: {len(rag_chunks)} chunks")
    print(f"RAG Citations: {rag_citations}")
    print(f"RAG Answer: {rag_answer[:100]}...")
    
    # Step 2: Test direct generator with same chunks (expected correct behavior)
    print("\n2️⃣ DIRECT GENERATOR TEST")
    print("-" * 40)
    
    if rag_chunks:
        # Format chunks for direct generator call
        formatted_chunks = []
        for chunk in rag_chunks:
            formatted_chunk = {
                "id": f"chunk_{chunk.get('chunk_id', 0)}",
                "content": chunk.get("text", ""),
                "metadata": {
                    "page_number": chunk.get("page", 0),
                    "source": Path(chunk.get("source", "unknown")).name,
                    "quality_score": chunk.get("quality_score", 0.0)
                },
                "score": chunk.get("hybrid_score", chunk.get("similarity_score", 0.0))
            }
            formatted_chunks.append(formatted_chunk)
        
        # Call generator directly with same chunks
        direct_result = generator.generate(
            query=test_query,
            chunks=formatted_chunks
        )
        
        print(f"Direct Confidence: {direct_result.confidence_score:.1%}")
        print(f"Direct Chunks Used: {len(formatted_chunks)}")
        print(f"Direct Citations: {len(direct_result.citations)}")
        print(f"Direct Answer: {direct_result.answer[:100]}...")
        
        # Step 3: Compare and analyze the discrepancy
        print("\n3️⃣ DISCREPANCY ANALYSIS")
        print("-" * 40)
        
        confidence_diff = direct_result.confidence_score - rag_confidence
        print(f"Confidence Difference: {confidence_diff:.1%}")
        print(f"Ratio (Direct/RAG): {direct_result.confidence_score/rag_confidence:.1f}x" if rag_confidence > 0 else "∞")
        
        if abs(confidence_diff) > 0.1:  # Significant difference
            print(f"❌ SIGNIFICANT DISCREPANCY DETECTED!")
            print(f"   Direct method: {direct_result.confidence_score:.1%}")
            print(f"   Integrated method: {rag_confidence:.1%}")
            
            # Detailed chunk comparison
            print(f"\n🔍 CHUNK FORMATTING COMPARISON:")
            print(f"RAG chunks format: {type(rag_chunks[0]) if rag_chunks else 'None'}")
            print(f"Direct chunks format: {type(formatted_chunks[0]) if formatted_chunks else 'None'}")
            
            if rag_chunks and formatted_chunks:
                print(f"\nFirst chunk comparison:")
                print(f"RAG chunk keys: {list(rag_chunks[0].keys())}")
                print(f"Direct chunk keys: {list(formatted_chunks[0].keys())}")
                
                # Check score preservation
                rag_score = rag_chunks[0].get("hybrid_score", rag_chunks[0].get("similarity_score", 0))
                direct_score = formatted_chunks[0].get("score", 0)
                print(f"Score preservation: RAG={rag_score:.3f}, Direct={direct_score:.3f}")
                
                # Check content preservation
                rag_content = rag_chunks[0].get("text", "")[:50]
                direct_content = formatted_chunks[0].get("content", "")[:50]
                print(f"Content match: {rag_content == direct_content}")
        
        else:
            print(f"✅ Confidence scores are similar - no significant bug detected")
    
    else:
        print("❌ No chunks retrieved by RAG - cannot compare with direct generator")
    
    # Step 4: Test edge cases to understand the pattern
    print("\n4️⃣ EDGE CASE TESTING")
    print("-" * 40)
    
    edge_cases = [
        {
            "name": "Medical Device Query",
            "query": "What are FDA software validation requirements?",
            "expected": "Should have moderate-high confidence if medical docs loaded"
        },
        {
            "name": "Irrelevant Query", 
            "query": "What is the capital of Mars?",
            "expected": "Should have low confidence"
        }
    ]
    
    edge_results = []
    
    for case in edge_cases:
        print(f"\n📋 {case['name']}: {case['expected']}")
        
        try:
            edge_rag_result = rag.query_with_answer(
                question=case['query'],
                top_k=5,
                use_hybrid=True,
                return_context=True
            )
            
            edge_confidence = edge_rag_result.get('confidence', 0)
            edge_chunks = edge_rag_result.get('context', [])
            
            print(f"   RAG Confidence: {edge_confidence:.1%}")
            print(f"   Retrieved chunks: {len(edge_chunks)}")
            
            # Test direct generator if chunks available
            if edge_chunks:
                edge_formatted = []
                for chunk in edge_chunks:
                    edge_formatted.append({
                        "id": f"chunk_{chunk.get('chunk_id', 0)}",
                        "content": chunk.get("text", ""),
                        "metadata": {
                            "page_number": chunk.get("page", 0),
                            "source": Path(chunk.get("source", "unknown")).name
                        },
                        "score": chunk.get("hybrid_score", chunk.get("similarity_score", 0.0))
                    })
                
                edge_direct = generator.generate(case['query'], edge_formatted)
                print(f"   Direct Confidence: {edge_direct.confidence_score:.1%}")
                print(f"   Discrepancy: {edge_direct.confidence_score - edge_confidence:.1%}")
            
            edge_results.append({
                'name': case['name'],
                'query': case['query'],
                'rag_confidence': edge_confidence,
                'chunks_retrieved': len(edge_chunks)
            })
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            edge_results.append({
                'name': case['name'],
                'error': str(e)
            })
    
    # Step 5: Generate summary report
    print("\n" + "=" * 80)
    print("🎯 CONFIDENCE BUG ANALYSIS SUMMARY")
    print("=" * 80)
    
    print(f"\nMain Test Results:")
    print(f"  RAG Pipeline Confidence: {rag_confidence:.1%}")
    if rag_chunks:
        print(f"  Direct Generator Confidence: {direct_result.confidence_score:.1%}")
        print(f"  Discrepancy: {confidence_diff:.1%}")
        
        if abs(confidence_diff) > 0.1:
            print(f"\n❌ BUG CONFIRMED: Significant confidence discrepancy detected")
            print(f"   The integrated RAG pipeline artificially suppresses confidence scores")
            print(f"   Root cause likely in query_with_answer() method or chunk formatting")
        else:
            print(f"\n✅ No significant bug detected in main test")
    
    print(f"\nEdge Case Pattern Analysis:")
    for result in edge_results:
        if 'error' not in result:
            print(f"  {result['name']}: {result['rag_confidence']:.1%} confidence")
        else:
            print(f"  {result['name']}: Error - {result['error']}")
    
    # Check if all queries show suspiciously similar low confidence
    if len(edge_results) >= 2:
        confidences = [r['rag_confidence'] for r in edge_results if 'rag_confidence' in r]
        if confidences and max(confidences) - min(confidences) < 0.03:  # Less than 3% variation
            print(f"\n⚠️ PATTERN DETECTED: All queries show similar low confidence ({min(confidences):.1%}-{max(confidences):.1%})")
            print(f"   This suggests systematic confidence suppression in the integration")
    
    # Step 6: Save debug report
    report = {
        "timestamp": datetime.now().isoformat(),
        "bug_analysis": {
            "main_test": {
                "query": test_query,
                "rag_confidence": rag_confidence,
                "direct_confidence": direct_result.confidence_score if rag_chunks else None,
                "discrepancy": confidence_diff if rag_chunks else None,
                "chunks_retrieved": len(rag_chunks)
            },
            "edge_cases": edge_results
        },
        "conclusion": {
            "bug_detected": abs(confidence_diff) > 0.1 if rag_chunks else False,
            "pattern_analysis": "Systematic confidence suppression" if len([r for r in edge_results if 'rag_confidence' in r and r['rag_confidence'] < 0.1]) > 1 else "No clear pattern"
        }
    }
    
    report_file = f"confidence_debug_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📁 Debug report saved: {report_file}")
    
    # Final recommendation
    if rag_chunks and abs(confidence_diff) > 0.1:
        print(f"\n🔧 RECOMMENDED NEXT STEPS:")
        print(f"1. Examine query_with_answer() method line-by-line")
        print(f"2. Check chunk formatting in lines 124-137 of rag_with_generation.py")
        print(f"3. Verify confidence score propagation in line 160")
        print(f"4. Test with calibration disabled to isolate calibration vs core bug")
    else:
        print(f"\n✅ Further investigation needed to identify confidence issues")
    
    return report

if __name__ == "__main__":
    debug_confidence_discrepancy()