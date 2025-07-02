#!/usr/bin/env python3
"""
Test Fragment Fix
Verify that the sentence completion fix reduces fragment rate.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent  # Go up to project-1-technical-rag
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))  # Add rag-portfolio root for shared_utils

from src.basic_rag import BasicRAG


def analyze_fragments(chunks: list) -> dict:
    """Analyze fragment rate in chunks."""
    total_chunks = len(chunks)
    fragments = 0
    complete_chunks = 0
    empty_chunks = 0
    
    fragment_examples = []
    
    for chunk in chunks:
        text = chunk['text'].strip()
        
        if not text:
            empty_chunks += 1
            continue
        
        # Check if complete sentence
        is_complete = (
            text.endswith(('.', '!', '?', ':', ';')) and
            (text[0].isupper() or text.startswith(('The ', 'A ', 'An ', 'This ', 'RISC')))
        )
        
        if is_complete:
            complete_chunks += 1
        else:
            fragments += 1
            if len(fragment_examples) < 3:  # Collect samples
                fragment_examples.append({
                    'page': chunk.get('page', 'unknown'),
                    'text': text[:100] + "..." if len(text) > 100 else text,
                    'starts_properly': text[0].isupper() if text else False,
                    'ends_properly': text.endswith(('.', '!', '?', ':', ';')) if text else False
                })
    
    return {
        'total_chunks': total_chunks,
        'complete_chunks': complete_chunks,
        'fragments': fragments,
        'empty_chunks': empty_chunks,
        'fragment_rate': fragments / total_chunks if total_chunks > 0 else 0,
        'completion_rate': complete_chunks / total_chunks if total_chunks > 0 else 0,
        'fragment_examples': fragment_examples
    }


def test_fragment_fix():
    """Test fragment fix on RISC-V document (high fragment rate before)."""
    print("🧪 TESTING FRAGMENT FIX")
    print("=" * 40)
    
    # Test with RISC-V document (previously had 20% fragments)
    rag = BasicRAG()
    pdf_path = project_root / "data" / "test" / "riscv-base-instructions.pdf"
    
    print(f"📄 Testing: {pdf_path.name}")
    
    try:
        chunk_count = rag.index_document(pdf_path)
        
        # Analyze fragments
        analysis = analyze_fragments(rag.chunks)
        
        print(f"\n📊 Fragment Analysis:")
        print(f"   Total chunks: {analysis['total_chunks']}")
        print(f"   Complete chunks: {analysis['complete_chunks']}")
        print(f"   Fragments: {analysis['fragments']}")
        print(f"   Empty chunks: {analysis['empty_chunks']}")
        print(f"   Fragment rate: {analysis['fragment_rate']:.1%}")
        print(f"   Completion rate: {analysis['completion_rate']:.1%}")
        
        # Show fragment examples
        if analysis['fragment_examples']:
            print(f"\n❌ Fragment Examples:")
            for i, example in enumerate(analysis['fragment_examples']):
                print(f"   {i+1}. Page {example['page']}")
                print(f"      Text: \"{example['text']}\"")
                print(f"      Starts OK: {example['starts_properly']}")
                print(f"      Ends OK: {example['ends_properly']}")
        
        # Assessment
        print(f"\n🎯 Assessment:")
        if analysis['fragment_rate'] < 0.05:  # Less than 5%
            print("   ✅ EXCELLENT: Fragment rate very low")
        elif analysis['fragment_rate'] < 0.1:  # Less than 10%
            print("   🔄 GOOD: Fragment rate acceptable")
        elif analysis['fragment_rate'] < 0.2:  # Less than 20%
            print("   ⚠️ NEEDS WORK: Fragment rate still high")
        else:
            print("   ❌ POOR: Fragment rate too high")
        
        # Page coverage check
        pages_covered = len(set(chunk.get('page', 0) for chunk in rag.chunks))
        print(f"   Page coverage: {pages_covered} pages")
        
        return analysis
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return None


def test_small_document():
    """Test on smaller document for comparison."""
    print(f"\n📄 Testing smaller document for comparison...")
    
    rag = BasicRAG()
    pdf_path = project_root / "data" / "test" / "GMLP_Guiding_Principles.pdf"
    
    try:
        chunk_count = rag.index_document(pdf_path)
        analysis = analyze_fragments(rag.chunks)
        
        print(f"   {pdf_path.name}: {analysis['fragment_rate']:.1%} fragments ({analysis['total_chunks']} chunks)")
        return analysis
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return None


if __name__ == "__main__":
    # Test main document
    main_analysis = test_fragment_fix()
    
    # Test comparison document
    comparison_analysis = test_small_document()
    
    if main_analysis:
        print(f"\n🏆 OVERALL RESULT")
        print("=" * 30)
        
        fragment_rate = main_analysis['fragment_rate']
        
        if fragment_rate < 0.1:
            print(f"✅ SUCCESS: Fragment rate reduced to {fragment_rate:.1%}")
            print("   Fragment fix working effectively")
        else:
            print(f"🔄 PARTIAL: Fragment rate at {fragment_rate:.1%}")
            print("   May need additional refinement")
    
    print(f"\n🔧 Next steps: Test across all documents to verify consistency")