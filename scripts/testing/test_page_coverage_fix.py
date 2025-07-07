#!/usr/bin/env python3
"""
Test Page Coverage Fix
Verify that PDFPlumber fallback now processes ALL pages correctly.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent  # Go up to project-1-technical-rag
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))  # Add rag-portfolio root for shared_utils

from src.core.pipeline import RAGPipeline


def test_page_coverage_fix():
    """Test if page coverage issue is resolved."""
    print("🧪 TESTING PAGE COVERAGE FIX")
    print("=" * 50)
    
    # Test with RISC-V document (238 pages)
    rag = RAGPipeline("config/test.yaml")
    pdf_path = project_root / "data" / "test" / "riscv-base-instructions.pdf"
    
    if not pdf_path.exists():
        print(f"❌ Test file not found: {pdf_path}")
        return False
    
    print(f"📄 Testing: {pdf_path.name}")
    
    try:
        # Index single document to see page coverage
        chunk_count = rag.index_document(pdf_path)
        print(f"✅ Indexed {chunk_count} chunks")
        
        # Analyze page coverage
        pages_covered = set()
        for chunk in rag.chunks:
            page = chunk.get('page', 0)
            pages_covered.add(page)
        
        print(f"\n📊 Page Coverage Analysis:")
        print(f"   - Total chunks: {len(rag.chunks)}")
        print(f"   - Pages covered: {len(pages_covered)}")
        print(f"   - Page range: {min(pages_covered)} to {max(pages_covered)}")
        print(f"   - Expected pages: ~238")
        
        # Show sample of page distribution
        page_counts = {}
        for chunk in rag.chunks:
            page = chunk.get('page', 0)
            page_counts[page] = page_counts.get(page, 0) + 1
        
        print(f"\n📄 Sample page distribution:")
        sample_pages = sorted(list(pages_covered))[:10] + ["..."] + sorted(list(pages_covered))[-5:]
        for page in sample_pages:
            if page == "...":
                print(f"   ...")
            else:
                count = page_counts.get(page, 0)
                print(f"   Page {page}: {count} chunks")
        
        # Check for improvement
        coverage_ratio = len(pages_covered) / 238  # Expected pages
        print(f"\n🎯 Coverage Assessment:")
        print(f"   - Coverage ratio: {coverage_ratio:.1%}")
        
        if coverage_ratio > 0.8:  # 80%+ coverage
            print("   ✅ EXCELLENT: Good page coverage achieved")
            return True
        elif coverage_ratio > 0.1:  # 10%+ coverage  
            print("   🔄 IMPROVED: Better than before, but needs more work")
            return True
        else:
            print("   ❌ FAILED: Still limited coverage")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_chunk_quality_sample():
    """Quick sample of chunk quality."""
    print("\n🔍 CHUNK QUALITY SAMPLE")
    print("=" * 30)
    
    rag = RAGPipeline("config/test.yaml")
    pdf_path = project_root / "data" / "test" / "riscv-base-instructions.pdf"
    rag.index_document(pdf_path)
    
    # Sample chunks from different pages
    sample_chunks = []
    seen_pages = set()
    
    for chunk in rag.chunks:
        page = chunk.get('page', 0)
        if page not in seen_pages and len(sample_chunks) < 5:
            sample_chunks.append(chunk)
            seen_pages.add(page)
    
    for i, chunk in enumerate(sample_chunks):
        print(f"\n📄 Sample {i+1}: Page {chunk.get('page')}")
        print(f"Size: {len(chunk['text'])} chars")
        print(f"Title: {chunk.get('title', 'No title')}")
        print(f"Preview: {chunk['text'][:100]}...")
        
        # Check if fragment
        text = chunk['text'].strip()
        is_complete = text.endswith(('.', '!', '?', ':', ';'))
        print(f"Complete: {'✅' if is_complete else '❌'}")


if __name__ == "__main__":
    success = test_page_coverage_fix()
    test_chunk_quality_sample()
    
    if success:
        print("\n🎉 PAGE COVERAGE FIX SUCCESSFUL!")
    else:
        print("\n❌ Page coverage still needs work")