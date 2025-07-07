#!/usr/bin/env python3
"""
Manual Quality Assessment - Rigorous Validation
Following CLAUDE.md lessons: "Never trust metrics alone - examine actual content"

This script provides detailed manual verification of:
1. Actual chunk content quality (not just metrics)
2. Scoring system soundness (actual score variation)
3. Page coverage reality (not just statistics)
4. Fragment detection (sentence completeness)
5. Source diversity validation

Author: Arthur Passuello
Date: 2025-07-02
"""

import sys
from pathlib import Path
from typing import Dict, List, Any
import re
import random

# Add project paths
project_root = Path(__file__).parent.parent.parent  # Go up to project-1-technical-rag
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))  # Add rag-portfolio root for shared_utils

from src.core.pipeline import RAGPipeline


def assess_chunk_quality_manually(chunks: List[Dict], sample_size: int = 10) -> Dict:
    """Manually assess chunk quality by examining actual content."""
    print(f"\n🔍 MANUAL CHUNK QUALITY ASSESSMENT")
    print(f"Examining {sample_size} random chunks from {len(chunks)} total")
    print("=" * 60)
    
    # Sample random chunks for manual review
    sample_chunks = random.sample(chunks, min(sample_size, len(chunks)))
    
    quality_issues = {
        'fragments': 0,
        'trash_content': 0,
        'toc_contamination': 0,
        'poor_technical_content': 0,
        'good_chunks': 0
    }
    
    for i, chunk in enumerate(sample_chunks):
        print(f"\n📄 CHUNK {i+1}/{len(sample_chunks)}")
        print(f"Source: {Path(chunk['source']).name}")
        print(f"Page: {chunk.get('page', 'Unknown')}")
        print(f"Size: {len(chunk['text'])} chars")
        print(f"Title: {chunk.get('title', 'No title')}")
        print("-" * 40)
        
        text = chunk['text']
        
        # Show first 200 chars for manual inspection
        preview = text[:200] + "..." if len(text) > 200 else text
        print(f"Content Preview:\n{preview}")
        
        # Check for fragments (incomplete sentences)
        is_fragment = not (text.strip().endswith(('.', '!', '?', ':', ';')) and 
                          (text[0].isupper() or text.startswith(('The ', 'A ', 'An ', 'RISC'))))
        
        # Check for trash content
        trash_patterns = [
            r'Creative Commons.*?License',
            r'\.{5,}',  # Long dots
            r'^\d+\s*$',  # Page numbers alone
            r'Visit.*?for further'
        ]
        has_trash = any(re.search(pattern, text, re.IGNORECASE) for pattern in trash_patterns)
        
        # Check for TOC contamination
        toc_patterns = [
            r'\.{3,}',  # Multiple dots
            r'^\s*\d+(?:\.\d+)*\s*$',  # Standalone numbers
            r'Contents\s*$'
        ]
        has_toc = any(re.search(pattern, text, re.MULTILINE | re.IGNORECASE) for pattern in toc_patterns)
        
        # Check technical content quality
        technical_terms = ['risc', 'register', 'instruction', 'memory', 'processor', 'software', 'validation', 'guidance']
        technical_count = sum(1 for term in technical_terms if term in text.lower())
        has_good_technical = technical_count >= 2
        
        # Assess overall quality
        if is_fragment:
            quality_issues['fragments'] += 1
            print("❌ ISSUE: Fragment (incomplete sentence)")
        elif has_trash:
            quality_issues['trash_content'] += 1
            print("❌ ISSUE: Trash content detected")
        elif has_toc:
            quality_issues['toc_contamination'] += 1
            print("❌ ISSUE: TOC contamination")
        elif not has_good_technical:
            quality_issues['poor_technical_content'] += 1
            print("⚠️  WARNING: Limited technical content")
        else:
            quality_issues['good_chunks'] += 1
            print("✅ GOOD: Quality technical content")
        
        print(f"Technical terms found: {technical_count}")
        print(f"Fragment check: {'FAIL' if is_fragment else 'PASS'}")
        print(f"Trash check: {'FAIL' if has_trash else 'PASS'}")
        print(f"TOC check: {'FAIL' if has_toc else 'PASS'}")
    
    return quality_issues


def test_scoring_soundness(rag: BasicRAG) -> Dict:
    """Test if scoring system produces sound, varied results."""
    print(f"\n🎯 SCORING SYSTEM SOUNDNESS TEST")
    print("Testing identical vs different queries for score variation")
    print("=" * 60)
    
    # Test 1: Identical queries should produce identical scores
    query = "RISC-V instruction format"
    print(f"\n🔄 Test 1: Identical Query Consistency")
    print(f"Query: {query}")
    
    result1 = rag.query(query, top_k=3)
    result2 = rag.query(query, top_k=3)
    
    scores1 = [chunk.get('hybrid_score', 0) for chunk in result1.get('chunks', [])]
    scores2 = [chunk.get('hybrid_score', 0) for chunk in result2.get('chunks', [])]
    
    print(f"Run 1 scores: {[f'{s:.6f}' for s in scores1]}")
    print(f"Run 2 scores: {[f'{s:.6f}' for s in scores2]}")
    
    identical_consistency = scores1 == scores2
    print(f"Consistency: {'✅ PASS' if identical_consistency else '❌ FAIL'}")
    
    # Test 2: Different queries should produce different scores
    queries = [
        "RISC-V instruction format",
        "memory address validation", 
        "software development guidelines",
        "processor register implementation",
        "technical documentation standards"
    ]
    
    print(f"\n🔀 Test 2: Different Query Variation")
    all_scores = []
    query_results = []
    
    for query in queries:
        result = rag.query(query, top_k=2)
        scores = [chunk.get('hybrid_score', 0) for chunk in result.get('chunks', [])]
        all_scores.extend(scores)
        query_results.append((query[:30] + "...", scores))
        
    for query_short, scores in query_results:
        print(f"{query_short}: {[f'{s:.6f}' for s in scores]}")
    
    # Check for artificial patterns (like 0.350, 0.233, 0.175)
    score_strings = [f'{s:.3f}' for s in all_scores]
    unique_scores = len(set(score_strings))
    total_scores = len(score_strings)
    variation_ratio = unique_scores / total_scores
    
    print(f"\nScore Analysis:")
    print(f"Total scores: {total_scores}")
    print(f"Unique scores: {unique_scores}")
    print(f"Variation ratio: {variation_ratio:.2f}")
    
    # Check for the specific problematic pattern mentioned in CLAUDE.md
    problematic_scores = ['0.350', '0.233', '0.175']
    has_problematic_pattern = all(score in score_strings for score in problematic_scores)
    
    print(f"Problematic pattern check: {'❌ DETECTED' if has_problematic_pattern else '✅ CLEAR'}")
    
    return {
        'identical_consistency': identical_consistency,
        'variation_ratio': variation_ratio,
        'has_problematic_pattern': has_problematic_pattern,
        'all_scores': all_scores
    }


def verify_page_coverage_reality(rag: BasicRAG) -> Dict:
    """Verify actual page coverage by examining chunk metadata."""
    print(f"\n📊 PAGE COVERAGE REALITY CHECK")
    print("Examining actual page distribution across documents")
    print("=" * 60)
    
    coverage_data = {}
    for chunk in rag.chunks:
        source = Path(chunk['source']).name
        page = chunk.get('page', 0)
        
        if source not in coverage_data:
            coverage_data[source] = {
                'pages': set(),
                'chunk_count': 0,
                'sample_chunks': []
            }
        
        coverage_data[source]['pages'].add(page)
        coverage_data[source]['chunk_count'] += 1
        
        # Collect sample chunks for inspection
        if len(coverage_data[source]['sample_chunks']) < 3:
            coverage_data[source]['sample_chunks'].append({
                'page': page,
                'text_preview': chunk['text'][:150] + "...",
                'size': len(chunk['text'])
            })
    
    total_pages_covered = 0
    documents_with_good_coverage = 0
    
    for doc, data in coverage_data.items():
        page_count = len(data['pages'])
        chunk_count = data['chunk_count']
        total_pages_covered += page_count
        
        print(f"\n📄 {doc}")
        print(f"   Pages covered: {page_count}")
        print(f"   Chunks created: {chunk_count}")
        print(f"   Pages: {sorted(list(data['pages']))}")
        
        if page_count > 1:
            documents_with_good_coverage += 1
            print(f"   ✅ Good coverage")
        else:
            print(f"   ⚠️  Limited coverage")
            
        # Show sample chunks
        print(f"   Sample chunks:")
        for i, sample in enumerate(data['sample_chunks']):
            print(f"     {i+1}. Page {sample['page']}, {sample['size']} chars")
            print(f"        \"{sample['text_preview']}\"")
    
    coverage_ratio = documents_with_good_coverage / len(coverage_data)
    
    return {
        'total_documents': len(coverage_data),
        'documents_with_good_coverage': documents_with_good_coverage,
        'coverage_ratio': coverage_ratio,
        'total_pages_covered': total_pages_covered,
        'coverage_data': coverage_data
    }


def test_source_diversity_reality(rag: BasicRAG) -> Dict:
    """Test actual source diversity in query results."""
    print(f"\n🌐 SOURCE DIVERSITY REALITY TEST")
    print("Testing if queries actually return diverse sources")
    print("=" * 60)
    
    test_queries = [
        "software validation requirements",
        "technical documentation standards", 
        "RISC-V processor implementation",
        "medical device software guidance",
        "validation and verification processes"
    ]
    
    diversity_results = []
    
    for query in test_queries:
        result = rag.query(query, top_k=8)
        chunks = result.get('chunks', [])
        
        sources = [Path(chunk['source']).name for chunk in chunks]
        unique_sources = set(sources)
        
        print(f"\n🔍 Query: {query}")
        print(f"   Results: {len(chunks)} chunks")
        print(f"   Unique sources: {len(unique_sources)}")
        print(f"   Sources: {list(unique_sources)}")
        
        # Show source distribution
        source_counts = {}
        for source in sources:
            source_counts[source] = source_counts.get(source, 0) + 1
        
        for source, count in source_counts.items():
            print(f"     - {source}: {count} chunks")
        
        diversity_ratio = len(unique_sources) / len(chunks) if chunks else 0
        diversity_results.append({
            'query': query,
            'total_chunks': len(chunks),
            'unique_sources': len(unique_sources),
            'diversity_ratio': diversity_ratio,
            'source_distribution': source_counts
        })
    
    avg_diversity = sum(r['diversity_ratio'] for r in diversity_results) / len(diversity_results)
    print(f"\n📊 Overall Diversity Analysis:")
    print(f"   Average diversity ratio: {avg_diversity:.2f}")
    print(f"   {'✅ GOOD' if avg_diversity > 0.3 else '⚠️ LIMITED'} source diversity")
    
    return {
        'average_diversity': avg_diversity,
        'query_results': diversity_results
    }


def main():
    """Run comprehensive manual quality assessment."""
    print("🔬 MANUAL QUALITY ASSESSMENT - RIGOROUS VALIDATION")
    print("Following CLAUDE.md lessons: 'Never trust metrics alone'")
    print("=" * 80)
    
    # Initialize and index documents
    rag = RAGPipeline("config/default.yaml")
    data_folder = project_root / "data" / "test"
    
    print(f"🔄 Indexing documents from {data_folder}...")
    try:
        results = rag.index_document(data_folder)
        print(f"✅ Indexed {len(rag.chunks)} total chunks from {len(results)} documents")
    except Exception as e:
        print(f"❌ Indexing failed: {e}")
        return False
    
    # Manual assessments
    chunk_quality = assess_chunk_quality_manually(rag.chunks, sample_size=15)
    scoring_soundness = test_scoring_soundness(rag)
    page_coverage = verify_page_coverage_reality(rag)
    source_diversity = test_source_diversity_reality(rag)
    
    # Final assessment
    print(f"\n🎯 FINAL MANUAL ASSESSMENT")
    print("=" * 80)
    
    total_sampled = sum(chunk_quality.values())
    good_chunk_ratio = chunk_quality['good_chunks'] / total_sampled if total_sampled > 0 else 0
    
    print(f"📊 Chunk Quality (Manual Sample of {total_sampled}):")
    print(f"   ✅ Good chunks: {chunk_quality['good_chunks']} ({good_chunk_ratio:.1%})")
    print(f"   ❌ Fragments: {chunk_quality['fragments']}")
    print(f"   ❌ Trash content: {chunk_quality['trash_content']}")
    print(f"   ❌ TOC contamination: {chunk_quality['toc_contamination']}")
    print(f"   ⚠️  Poor technical: {chunk_quality['poor_technical_content']}")
    
    print(f"\n🎯 Scoring System:")
    print(f"   Consistency: {'✅ PASS' if scoring_soundness['identical_consistency'] else '❌ FAIL'}")
    print(f"   Variation: {scoring_soundness['variation_ratio']:.2f} ({'✅ GOOD' if scoring_soundness['variation_ratio'] > 0.7 else '⚠️ LIMITED'})")
    print(f"   Problematic pattern: {'❌ DETECTED' if scoring_soundness['has_problematic_pattern'] else '✅ CLEAR'}")
    
    print(f"\n📄 Page Coverage:")
    print(f"   Documents with good coverage: {page_coverage['documents_with_good_coverage']}/{page_coverage['total_documents']}")
    print(f"   Coverage ratio: {page_coverage['coverage_ratio']:.1%}")
    
    print(f"\n🌐 Source Diversity:")
    print(f"   Average diversity: {source_diversity['average_diversity']:.2f}")
    
    # Overall assessment
    quality_score = (
        good_chunk_ratio * 0.4 +  # 40% chunk quality
        (1 if scoring_soundness['identical_consistency'] else 0) * 0.2 +  # 20% scoring
        scoring_soundness['variation_ratio'] * 0.2 +  # 20% score variation
        page_coverage['coverage_ratio'] * 0.1 +  # 10% page coverage
        min(source_diversity['average_diversity'] * 3, 1) * 0.1  # 10% diversity
    )
    
    print(f"\n🏆 OVERALL QUALITY SCORE: {quality_score:.2f}/1.0")
    
    if quality_score >= 0.8:
        print("✅ ASSESSMENT: Production-ready quality achieved")
    elif quality_score >= 0.6:
        print("⚠️  ASSESSMENT: Acceptable quality with room for improvement")
    else:
        print("❌ ASSESSMENT: Quality issues need addressing before production")
    
    return quality_score >= 0.6


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)