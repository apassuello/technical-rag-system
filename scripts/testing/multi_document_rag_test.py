#!/usr/bin/env python3
"""
Multi-Document RAG Testing Script
=================================

Tests the RAG system with all available documents to identify and fix:
1. Single document limitation
2. TOC content not being removed from chunks
3. Limited page coverage
4. Source diversity issues
"""

import sys
from pathlib import Path
import time

# Add project paths
project_root = Path(__file__).parent.parent.parent  # Go up to project-1-technical-rag
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))  # Add rag-portfolio root for shared_utils

from src.basic_rag import BasicRAG
from shared_utils.document_processing.pdf_parser import extract_text_with_metadata
from shared_utils.document_processing.hybrid_parser import parse_pdf_with_hybrid_approach


def analyze_available_documents():
    """Analyze all available documents in test folder."""
    print("📚 AVAILABLE DOCUMENTS ANALYSIS")
    print("="*70)
    
    test_folder = project_root / "data" / "test"
    pdf_files = list(test_folder.glob("*.pdf"))
    
    print(f"Found {len(pdf_files)} PDF documents:")
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n{i}. {pdf_path.name}")
        
        try:
            # Quick analysis of each document
            text_data = extract_text_with_metadata(pdf_path)
            
            print(f"   Pages: {text_data.get('page_count', 'Unknown')}")
            print(f"   Text length: {len(text_data.get('text', '')):,} characters")
            print(f"   File size: {pdf_path.stat().st_size / 1024 / 1024:.1f} MB")
            
            # Quick TOC analysis
            pages_data = text_data.get('pages', [])
            if pages_data:
                sample_page = pages_data[0].get('text', '')[:200] if pages_data else ''
                print(f"   Sample content: '{sample_page}...'")
            
        except Exception as e:
            print(f"   ❌ Error analyzing: {e}")
    
    return pdf_files


def test_single_document_processing(pdf_path):
    """Test processing of a single document in detail."""
    print(f"\n📄 DETAILED SINGLE DOCUMENT ANALYSIS: {pdf_path.name}")
    print("="*70)
    
    # Extract basic document info
    text_data = extract_text_with_metadata(pdf_path)
    total_pages = text_data.get('page_count', 0)
    total_text = len(text_data.get('text', ''))
    
    print(f"Document stats:")
    print(f"   Total pages: {total_pages}")
    print(f"   Total text: {total_text:,} characters")
    
    # Test hybrid parsing
    print(f"\n🔗 Testing hybrid parsing...")
    start_time = time.time()
    chunks = parse_pdf_with_hybrid_approach(pdf_path, text_data)
    parsing_time = time.time() - start_time
    
    print(f"   Parsing time: {parsing_time:.2f}s")
    print(f"   Chunks created: {len(chunks)}")
    
    if chunks:
        # Analyze page coverage
        pages_in_chunks = [chunk.get('page', 0) for chunk in chunks]
        unique_pages = set(pages_in_chunks)
        
        print(f"\n📊 Page Coverage Analysis:")
        print(f"   Pages with chunks: {len(unique_pages)} out of {total_pages}")
        print(f"   Coverage percentage: {len(unique_pages)/total_pages*100:.1f}%")
        print(f"   Page range: {min(pages_in_chunks)} - {max(pages_in_chunks)}")
        
        # Check for TOC content in chunks
        toc_indicators = ['contents', 'table of contents', '...', 'chapter', 'section']
        toc_chunks = 0
        
        for chunk in chunks[:10]:  # Check first 10 chunks
            text = chunk['text'].lower()
            if any(indicator in text for indicator in toc_indicators):
                if '...' in text or 'contents' in text:
                    toc_chunks += 1
        
        print(f"\n📋 TOC Content Analysis:")
        print(f"   Potential TOC chunks: {toc_chunks} out of {min(10, len(chunks))} examined")
        
        # Sample chunks
        print(f"\n📝 Sample Chunk Analysis:")
        for i in range(min(3, len(chunks))):
            chunk = chunks[i]
            text = chunk['text']
            title = chunk.get('title', 'No title')
            page = chunk.get('page', 'Unknown')
            
            print(f"\n   Chunk {i+1}:")
            print(f"     Title: '{title}'")
            print(f"     Page: {page}")
            print(f"     Size: {len(text)} chars")
            print(f"     Content: '{text[:150]}...'")
            
            # Check for TOC indicators
            if '...' in text or 'contents' in text.lower():
                print(f"     ⚠️  Contains TOC-like content")
    
    return chunks


def test_multi_document_rag():
    """Test RAG system with multiple documents."""
    print(f"\n🔗 MULTI-DOCUMENT RAG SYSTEM TEST")
    print("="*70)
    
    # Get all PDFs
    test_folder = project_root / "data" / "test"
    pdf_files = list(test_folder.glob("*.pdf"))
    
    print(f"Testing RAG system with {len(pdf_files)} documents...")
    
    # Initialize RAG system
    rag = BasicRAG()
    
    # Process each document
    total_chunks = 0
    document_stats = []
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n📄 Processing document {i}/{len(pdf_files)}: {pdf_path.name}")
        
        try:
            start_time = time.time()
            chunks_count = rag.index_document(pdf_path)
            processing_time = time.time() - start_time
            
            total_chunks += chunks_count
            document_stats.append({
                'name': pdf_path.name,
                'chunks': chunks_count,
                'time': processing_time
            })
            
            print(f"   ✅ Processed: {chunks_count} chunks in {processing_time:.2f}s")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            document_stats.append({
                'name': pdf_path.name,
                'chunks': 0,
                'time': 0,
                'error': str(e)
            })
    
    print(f"\n📊 Multi-Document Processing Summary:")
    print(f"   Total documents: {len(pdf_files)}")
    print(f"   Successfully processed: {sum(1 for stat in document_stats if stat['chunks'] > 0)}")
    print(f"   Total chunks: {total_chunks}")
    
    # Analyze source diversity
    if rag.chunks:
        sources = [chunk.get('source', 'Unknown') for chunk in rag.chunks]
        unique_sources = set(sources)
        
        print(f"\n📍 Source Diversity Analysis:")
        print(f"   Unique sources: {len(unique_sources)}")
        
        for source in unique_sources:
            count = sources.count(source)
            percentage = count / len(rag.chunks) * 100
            source_name = Path(source).name if source != 'Unknown' else source
            print(f"   {source_name}: {count} chunks ({percentage:.1f}%)")
    
    return rag, document_stats


def test_queries_with_multi_documents(rag):
    """Test queries across multiple documents."""
    print(f"\n🔍 MULTI-DOCUMENT QUERY TESTING")
    print("="*70)
    
    # Test queries that should find content in different documents
    test_queries = [
        ("Medical Software", "software medical device validation"),
        ("RISC-V Technical", "RISC-V instruction encoding"),
        ("Regulatory Guidance", "FDA guidance principles"),
        ("Quality Management", "quality management principles"),
        ("Risk Management", "risk assessment software"),
    ]
    
    for query_type, query in test_queries:
        print(f"\n🎯 {query_type}: '{query}'")
        
        # Test semantic search
        semantic_result = rag.query(query, top_k=3)
        chunks = semantic_result.get('chunks', [])
        
        if chunks:
            sources = [Path(chunk.get('source', 'Unknown')).name for chunk in chunks]
            pages = [chunk.get('page', 'Unknown') for chunk in chunks]
            scores = [chunk.get('similarity_score', 0.0) for chunk in chunks]
            
            print(f"   Results: {len(chunks)} chunks found")
            print(f"   Sources: {sources}")
            print(f"   Pages: {pages}")
            print(f"   Scores: {[f'{s:.3f}' for s in scores]}")
            
            # Check source diversity
            unique_sources = len(set(sources))
            print(f"   Source diversity: {unique_sources} unique sources")
            
            # Sample top result
            top_chunk = chunks[0]
            content_preview = top_chunk['text'][:200]
            print(f"   Top result: '{content_preview}...'")
        else:
            print(f"   ❌ No results found")


def main():
    """Main testing function."""
    print("🧪 COMPREHENSIVE MULTI-DOCUMENT RAG TESTING")
    print("Testing document coverage, TOC handling, and source diversity")
    print("="*80)
    
    # Phase 1: Analyze available documents
    pdf_files = analyze_available_documents()
    
    if not pdf_files:
        print("❌ No PDF files found in test folder")
        return
    
    # Phase 2: Test single document processing in detail
    main_pdf = None
    for pdf in pdf_files:
        if 'riscv' in pdf.name.lower():
            main_pdf = pdf
            break
    
    if main_pdf:
        chunks = test_single_document_processing(main_pdf)
    
    # Phase 3: Test multi-document RAG system
    rag, stats = test_multi_document_rag()
    
    # Phase 4: Test queries across documents
    if rag and rag.chunks:
        test_queries_with_multi_documents(rag)
    
    print(f"\n🎊 MULTI-DOCUMENT TESTING COMPLETE!")
    print("="*80)
    
    # Final assessment
    if len(pdf_files) > 1 and len(set(chunk.get('source', '') for chunk in rag.chunks)) == 1:
        print("❌ CRITICAL: System only processes one document despite multiple available")
    
    return rag, stats


if __name__ == "__main__":
    main()