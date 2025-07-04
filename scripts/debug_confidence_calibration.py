#!/usr/bin/env python3
"""
Debug confidence calibration to see if calibration is causing the artificial suppression.

This test compares confidence scores with and without calibration enabled.
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

def debug_confidence_calibration():
    """Debug confidence calibration effects."""
    print("🔧 DEBUGGING CONFIDENCE CALIBRATION")
    print("=" * 80)
    print("Testing with calibration enabled vs disabled")
    print("=" * 80)
    
    # Initialize answer generators - one with calibration, one without
    generator_with_calibration = AnswerGenerator(enable_calibration=True)
    generator_without_calibration = AnswerGenerator(enable_calibration=False)
    
    # Test with just a single document to avoid timeout
    rag = RAGWithGeneration()
    
    print("\n📚 Loading single test document...")
    test_doc = Path("data/test/riscv-base-instructions.pdf")
    if test_doc.exists():
        result = rag.index_document(test_doc)
        print(f"✅ Loaded {result} chunks from RISC-V instructions document")
    else:
        print("❌ Test document not found")
        return
    
    # Test queries
    test_queries = [
        {
            "name": "High Quality Query",
            "query": "What is RISC-V?",
            "expected": "Should have high confidence"
        },
        {
            "name": "Technical Query",
            "query": "What are the RISC-V instruction formats?",
            "expected": "Should have high confidence"
        },
        {
            "name": "Irrelevant Query",
            "query": "What is the capital of Mars?",
            "expected": "Should have low confidence"
        }
    ]
    
    print(f"\n🧪 CALIBRATION COMPARISON TEST")
    print("-" * 60)
    
    results = []
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n{i}. {test['name']}: {test['query']}")
        
        try:
            # Get chunks from RAG system
            rag_result = rag.hybrid_query(test['query'], top_k=5)
            chunks = rag_result.get("chunks", [])
            
            if not chunks:
                print("   ❌ No chunks retrieved")
                continue
            
            # Format chunks for generator
            formatted_chunks = []
            for chunk in chunks:
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
            
            # Test with calibration enabled
            result_with_cal = generator_with_calibration.generate(
                query=test['query'],
                chunks=formatted_chunks
            )
            
            # Test with calibration disabled
            result_without_cal = generator_without_calibration.generate(
                query=test['query'],
                chunks=formatted_chunks
            )
            
            print(f"   With Calibration:    {result_with_cal.confidence_score:.1%}")
            print(f"   Without Calibration: {result_without_cal.confidence_score:.1%}")
            
            cal_effect = result_with_cal.confidence_score - result_without_cal.confidence_score
            print(f"   Calibration Effect:  {cal_effect:+.1%}")
            
            if abs(cal_effect) > 0.1:  # >10% difference
                print(f"   ⚠️ SIGNIFICANT CALIBRATION EFFECT DETECTED")
            
            # Check if calibration is suppressing confidence 
            if result_without_cal.confidence_score > 0.5 and result_with_cal.confidence_score < 0.2:
                print(f"   ❌ CALIBRATION BUG: Severely suppressing confidence")
            
            results.append({
                'name': test['name'],
                'query': test['query'],
                'with_calibration': result_with_cal.confidence_score,
                'without_calibration': result_without_cal.confidence_score,
                'calibration_effect': cal_effect,
                'chunks_used': len(formatted_chunks),
                'max_chunk_score': max(c.get('score', 0) for c in formatted_chunks) if formatted_chunks else 0
            })
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                'name': test['name'],
                'error': str(e)
            })
    
    # Test the integrated RAG system too
    print(f"\n🔍 INTEGRATED RAG SYSTEM TEST")
    print("-" * 40)
    
    for test in test_queries[:2]:  # Just test first 2 to save time
        try:
            integrated_result = rag.query_with_answer(
                question=test['query'],
                top_k=5,
                use_hybrid=True
            )
            
            integrated_confidence = integrated_result.get('confidence', 0)
            print(f"   {test['name']}: {integrated_confidence:.1%} (integrated)")
            
            # Find corresponding direct results
            matching_result = next((r for r in results if r.get('name') == test['name']), None)
            if matching_result and 'error' not in matching_result:
                direct_with_cal = matching_result['with_calibration']
                direct_without_cal = matching_result['without_calibration']
                
                print(f"                      {direct_with_cal:.1%} (direct w/ cal)")
                print(f"                      {direct_without_cal:.1%} (direct w/o cal)")
                
                # Check if integrated matches direct with calibration
                if abs(integrated_confidence - direct_with_cal) < 0.02:  # Within 2%
                    print(f"   ✅ Integrated matches direct with calibration")
                elif abs(integrated_confidence - direct_without_cal) < 0.02:
                    print(f"   ✅ Integrated matches direct without calibration")
                else:
                    print(f"   ❌ Integrated differs from both direct methods")
                    print(f"      Difference from cal: {integrated_confidence - direct_with_cal:+.1%}")
                    print(f"      Difference from no-cal: {integrated_confidence - direct_without_cal:+.1%}")
        
        except Exception as e:
            print(f"   ❌ Integrated test error: {e}")
    
    # Analysis
    print(f"\n" + "=" * 80)
    print("🎯 CALIBRATION ANALYSIS")
    print("=" * 80)
    
    valid_results = [r for r in results if 'error' not in r]
    
    if valid_results:
        calibration_effects = [r['calibration_effect'] for r in valid_results]
        avg_effect = sum(calibration_effects) / len(calibration_effects)
        max_effect = max(calibration_effects, key=abs)
        
        print(f"\nCalibration Impact:")
        print(f"  Average effect: {avg_effect:+.1%}")
        print(f"  Maximum effect: {max_effect:+.1%}")
        
        # Check for systematic suppression
        strong_suppression = sum(1 for e in calibration_effects if e < -0.3)  # >30% reduction
        if strong_suppression > 0:
            print(f"❌ CALIBRATION BUG: {strong_suppression}/{len(calibration_effects)} queries severely suppressed")
            print(f"   Calibration is reducing confidence by >30%")
        elif avg_effect < -0.1:
            print(f"⚠️ Calibration systematically reducing confidence by {-avg_effect:.1%}")
        elif abs(avg_effect) < 0.05:
            print(f"✅ Calibration has minimal impact ({avg_effect:+.1%} average)")
        else:
            print(f"✅ Calibration working as expected ({avg_effect:+.1%} average)")
        
        # Check calibration status
        print(f"\nCalibration Status:")
        print(f"  With calibration fitted: {generator_with_calibration.calibrator.is_fitted if generator_with_calibration.calibrator else False}")
        print(f"  Calibration temperature: {generator_with_calibration.calibrator.temperature if generator_with_calibration.calibrator and generator_with_calibration.calibrator.is_fitted else 'N/A'}")
    
    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_results": results,
        "analysis": {
            "calibration_effects": calibration_effects if valid_results else [],
            "average_effect": avg_effect if valid_results else None,
            "calibration_fitted": generator_with_calibration.calibrator.is_fitted if generator_with_calibration.calibrator else False,
            "temperature": generator_with_calibration.calibrator.temperature if generator_with_calibration.calibrator and generator_with_calibration.calibrator.is_fitted else None
        }
    }
    
    report_file = f"calibration_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📁 Calibration debug report saved: {report_file}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS")
    print("-" * 30)
    
    if valid_results:
        if strong_suppression > 0:
            print("1. Disable calibration in AnswerGenerator initialization")
            print("2. Re-test confidence scores without calibration")
            print("3. If issue persists, investigate core confidence calculation")
        elif abs(avg_effect) < 0.05:
            print("1. Calibration not causing significant issues")
            print("2. Look for confidence bugs elsewhere in the pipeline")
            print("3. Check chunk formatting and score propagation")
        else:
            print("1. Calibration working but may need tuning")
            print("2. Consider adjusting calibration parameters")
            print("3. Validate calibration training data quality")
    
    return report

if __name__ == "__main__":
    debug_confidence_calibration()