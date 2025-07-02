#!/usr/bin/env python3
"""
Test Page Coverage Fix Across All Documents
Verify the fix works for all 5 PDFs in the test set.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent  # Go up to project-1-technical-rag
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))  # Add rag-portfolio root for shared_utils

from src.basic_rag import BasicRAG


def test_individual_document(pdf_path: Path) -> dict:
    """Test page coverage for a single document."""
    print(f"\n📄 Testing: {pdf_path.name}")
    print("-" * 50)
    
    rag = BasicRAG()
    
    try:
        chunk_count = rag.index_document(pdf_path)
        
        # Analyze page coverage
        pages_covered = set()
        parsing_methods = {}
        
        for chunk in rag.chunks:
            page = chunk.get('page', 0)
            pages_covered.add(page)
            
            method = chunk.get('metadata', {}).get('parsing_method', 'unknown')
            parsing_methods[method] = parsing_methods.get(method, 0) + 1
        
        # Sample chunk quality
        fragments = 0
        complete_chunks = 0
        
        for chunk in rag.chunks[:10]:  # Sample first 10
            text = chunk['text'].strip()
            if text.endswith(('.', '!', '?', ':', ';')):
                complete_chunks += 1
            else:
                fragments += 1
        
        results = {
            'success': True,
            'total_chunks': len(rag.chunks),
            'pages_covered': len(pages_covered),
            'page_range': f"{min(pages_covered)}-{max(pages_covered)}" if pages_covered else "none",
            'parsing_methods': parsing_methods,
            'fragment_rate': fragments / 10 if fragments + complete_chunks > 0 else 0,
            'error': None
        }
        
        print(f"✅ Success: {chunk_count} chunks, {len(pages_covered)} pages")
        print(f"   Page range: {results['page_range']}")
        print(f"   Parsing methods: {parsing_methods}")
        print(f"   Fragment rate: {results['fragment_rate']:.1%}")
        
        return results
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'total_chunks': 0,
            'pages_covered': 0,
            'page_range': 'none',
            'parsing_methods': {},
            'fragment_rate': 0
        }


def test_all_documents():
    """Test all documents in the test folder."""
    print("🧪 TESTING PAGE COVERAGE ACROSS ALL DOCUMENTS")
    print("=" * 70)
    
    data_folder = project_root / "data" / "test"
    pdf_files = list(data_folder.glob("*.pdf"))
    
    print(f"📁 Found {len(pdf_files)} PDF documents")
    
    results = {}
    total_chunks = 0
    total_pages = 0
    successful_docs = 0
    
    for pdf_file in pdf_files:
        result = test_individual_document(pdf_file)
        results[pdf_file.name] = result
        
        if result['success']:
            successful_docs += 1
            total_chunks += result['total_chunks']
            total_pages += result['pages_covered']
    
    # Summary
    print(f"\n📊 OVERALL SUMMARY")
    print("=" * 50)
    print(f"📈 Success rate: {successful_docs}/{len(pdf_files)} documents ({successful_docs/len(pdf_files)*100:.1f}%)")
    print(f"📄 Total chunks: {total_chunks}")
    print(f"📋 Total pages covered: {total_pages}")
    
    # Detailed results
    print(f"\n📋 DETAILED RESULTS")
    print("-" * 50)
    
    for doc_name, result in results.items():
        status = "✅" if result['success'] else "❌"
        print(f"{status} {doc_name}")
        print(f"   Chunks: {result['total_chunks']}")
        print(f"   Pages: {result['pages_covered']} ({result['page_range']})")
        print(f"   Methods: {result['parsing_methods']}")
        print(f"   Fragments: {result['fragment_rate']:.1%}")
        if result['error']:
            print(f"   Error: {result['error']}")
    
    # Assessment
    success_rate = successful_docs / len(pdf_files)
    
    print(f"\n🎯 ASSESSMENT")
    print("-" * 20)
    
    if success_rate == 1.0:
        print("✅ EXCELLENT: All documents processed successfully")
    elif success_rate >= 0.8:
        print("🔄 GOOD: Most documents processed successfully")
    else:
        print("❌ POOR: Multiple document failures")
    
    # Check if page coverage is significantly improved
    avg_pages_per_doc = total_pages / successful_docs if successful_docs > 0 else 0
    
    if avg_pages_per_doc > 20:
        print("✅ PAGE COVERAGE: Significant improvement achieved")
    elif avg_pages_per_doc > 5:
        print("🔄 PAGE COVERAGE: Some improvement, needs work")
    else:
        print("❌ PAGE COVERAGE: Still limited coverage")
    
    return results


if __name__ == "__main__":
    results = test_all_documents()
    
    # Quick fragment analysis
    total_fragment_rate = sum(r['fragment_rate'] for r in results.values() if r['success']) / len([r for r in results.values() if r['success']])
    
    print(f"\n🔧 NEXT PRIORITY")
    print(f"Average fragment rate: {total_fragment_rate:.1%}")
    
    if total_fragment_rate > 0.3:
        print("🎯 HIGH PRIORITY: Fix fragment issue (>30% fragments)")
    elif total_fragment_rate > 0.1:
        print("🔄 MEDIUM PRIORITY: Improve chunking quality")
    else:
        print("✅ LOW PRIORITY: Fragment rate acceptable")