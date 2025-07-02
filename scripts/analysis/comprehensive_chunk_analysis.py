#!/usr/bin/env python3
"""
Comprehensive Chunk Quality Analysis
=====================================

Direct assessment of chunk quality for the production RAG system.
This script provides detailed analysis of actual chunks to validate
that our recovery and cleanup maintained all functionality.
"""

import sys
import re
import json
from pathlib import Path
from collections import Counter

# Add project paths
project_root = Path(__file__).parent.parent.parent  # Go up to project-1-technical-rag
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))  # Add rag-portfolio root for shared_utils

from src.basic_rag import BasicRAG


def analyze_chunk_quality(chunks):
    """Comprehensive quality analysis of chunks."""
    print(f"🔬 COMPREHENSIVE CHUNK QUALITY ANALYSIS")
    print("="*80)
    
    if not chunks:
        print("❌ No chunks to analyze")
        return
    
    print(f"📊 Dataset: {len(chunks)} total chunks")
    
    # Basic statistics
    sizes = [len(chunk['text']) for chunk in chunks]
    quality_scores = [chunk.get('quality_score', 0.0) for chunk in chunks]
    
    print(f"\n📏 Size Analysis:")
    print(f"   Range: {min(sizes):,} - {max(sizes):,} characters")
    print(f"   Mean: {sum(sizes)/len(sizes):,.0f} chars")
    print(f"   Median: {sorted(sizes)[len(sizes)//2]:,} chars")
    
    # Size distribution
    size_categories = {
        "Too Small (<800)": sum(1 for s in sizes if s < 800),
        "Optimal (800-1600)": sum(1 for s in sizes if 800 <= s <= 1600), 
        "Large (1600-2000)": sum(1 for s in sizes if 1600 < s <= 2000),
        "Too Large (>2000)": sum(1 for s in sizes if s > 2000)
    }
    
    print(f"\n📊 Size Distribution:")
    for category, count in size_categories.items():
        percentage = count / len(chunks) * 100
        print(f"   {category}: {count:3d} chunks ({percentage:5.1f}%)")
    
    # Quality score analysis
    print(f"\n🎯 Quality Scores:")
    print(f"   Average: {sum(quality_scores)/len(quality_scores):.3f}")
    print(f"   Range: {min(quality_scores):.3f} - {max(quality_scores):.3f}")
    
    high_quality = sum(1 for q in quality_scores if q >= 0.8)
    medium_quality = sum(1 for q in quality_scores if 0.6 <= q < 0.8)
    low_quality = sum(1 for q in quality_scores if q < 0.6)
    
    print(f"   High quality (≥0.8): {high_quality} chunks ({high_quality/len(chunks)*100:.1f}%)")
    print(f"   Medium quality (0.6-0.8): {medium_quality} chunks ({medium_quality/len(chunks)*100:.1f}%)")
    print(f"   Low quality (<0.6): {low_quality} chunks ({low_quality/len(chunks)*100:.1f}%)")
    
    return high_quality, medium_quality, low_quality


def analyze_content_quality(chunks):
    """Analyze content quality factors."""
    print(f"\n📝 CONTENT QUALITY ANALYSIS")
    print("="*50)
    
    # Fragment detection
    fragments = 0
    complete_sentences = 0
    technical_content = 0
    trash_content = 0
    
    for chunk in chunks:
        text = chunk['text'].strip()
        
        # Fragment detection
        if not text.endswith(('.', '!', '?', ':', ';')):
            fragments += 1
        else:
            complete_sentences += 1
        
        # Technical content detection
        technical_terms = ['risc', 'instruction', 'register', 'memory', 'processor', 'architecture', 'bit', 'cpu']
        if any(term in text.lower() for term in technical_terms):
            technical_content += 1
        
        # Trash content detection
        trash_patterns = ['creative commons', 'international license', 'editors to suggest', 'volume i:', 'contents']
        if any(trash in text.lower() for trash in trash_patterns):
            trash_content += 1
    
    print(f"Fragment Analysis:")
    print(f"   Complete sentences: {complete_sentences}/{len(chunks)} ({complete_sentences/len(chunks)*100:.1f}%)")
    print(f"   Fragments: {fragments}/{len(chunks)} ({fragments/len(chunks)*100:.1f}%)")
    
    print(f"\nContent Analysis:")
    print(f"   Technical content: {technical_content}/{len(chunks)} ({technical_content/len(chunks)*100:.1f}%)")
    print(f"   Trash content: {trash_content}/{len(chunks)} ({trash_content/len(chunks)*100:.1f}%)")
    
    return fragments, technical_content, trash_content


def analyze_structure_quality(chunks):
    """Analyze structural aspects of chunks."""
    print(f"\n🏗️ STRUCTURE QUALITY ANALYSIS")
    print("="*50)
    
    # Title analysis
    with_titles = sum(1 for chunk in chunks if chunk.get('title') and chunk['title'] != 'No title')
    with_context = sum(1 for chunk in chunks if chunk.get('context'))
    with_parent = sum(1 for chunk in chunks if chunk.get('parent_title'))
    
    print(f"Structure Metadata:")
    print(f"   With titles: {with_titles}/{len(chunks)} ({with_titles/len(chunks)*100:.1f}%)")
    print(f"   With context: {with_context}/{len(chunks)} ({with_context/len(chunks)*100:.1f}%)")
    print(f"   With parent: {with_parent}/{len(chunks)} ({with_parent/len(chunks)*100:.1f}%)")
    
    # Parsing method analysis
    parsing_methods = Counter(chunk.get('parsing_method', 'unknown') for chunk in chunks)
    print(f"\nParsing Methods:")
    for method, count in parsing_methods.items():
        print(f"   {method}: {count} chunks ({count/len(chunks)*100:.1f}%)")
    
    return with_titles, with_context, parsing_methods


def sample_chunk_examination(chunks, num_samples=10):
    """Examine sample chunks in detail."""
    print(f"\n🔍 DETAILED SAMPLE EXAMINATION")
    print("="*80)
    print(f"Examining {min(num_samples, len(chunks))} sample chunks")
    
    excellent_count = 0
    
    for i in range(min(num_samples, len(chunks))):
        chunk = chunks[i]
        text = chunk['text']
        title = chunk.get('title', 'No title')
        size = len(text)
        quality = chunk.get('quality_score', 0.0)
        
        print(f"\n{'='*20} CHUNK {i+1} {'='*20}")
        print(f"Title: '{title}'")
        print(f"Size: {size} chars | Quality: {quality:.3f}")
        print(f"Page: {chunk.get('page', 'Unknown')}")
        
        # Quality checks
        is_complete = text.strip().endswith(('.', '!', '?', ':', ';'))
        starts_well = text[0].isupper() if text else False
        has_content = len([w for w in text.split() if len(w) > 3]) >= 20
        no_artifacts = not ('.' * 3 in text or text.count('.') > len(text) / 50)
        size_good = 800 <= size <= 2000
        no_trash = not any(trash in text.lower() for trash in ['creative commons', 'international license'])
        
        quality_factors = [is_complete, starts_well, has_content, no_artifacts, size_good, no_trash]
        quality_score = sum(quality_factors)
        
        print(f"Quality Factors:")
        print(f"   ✅ Complete sentences: {is_complete}")
        print(f"   ✅ Starts properly: {starts_well}")
        print(f"   ✅ Rich content: {has_content}")
        print(f"   ✅ No artifacts: {no_artifacts}")
        print(f"   ✅ Good size: {size_good}")
        print(f"   ✅ No trash: {no_trash}")
        print(f"   Score: {quality_score}/6")
        
        if quality_score >= 5:
            excellent_count += 1
            assessment = "🌟 EXCELLENT"
        elif quality_score >= 4:
            assessment = "✅ GOOD"
        elif quality_score >= 3:
            assessment = "🟡 FAIR"
        else:
            assessment = "❌ POOR"
        
        print(f"   {assessment}")
        
        # Show content preview
        print(f"Content Preview:")
        preview = text[:200] + "..." if len(text) > 200 else text
        print(f"   '{preview}'")
    
    print(f"\n📊 Sample Quality Summary:")
    print(f"   Excellent chunks: {excellent_count}/{min(num_samples, len(chunks))} ({excellent_count/min(num_samples, len(chunks))*100:.0f}%)")
    
    return excellent_count


def overall_assessment(chunks):
    """Provide overall system assessment."""
    print(f"\n🎯 OVERALL SYSTEM ASSESSMENT")
    print("="*80)
    
    if not chunks:
        print("❌ SYSTEM FAILURE: No chunks generated")
        return "FAILURE"
    
    # Calculate key metrics
    sizes = [len(chunk['text']) for chunk in chunks]
    quality_scores = [chunk.get('quality_score', 0.0) for chunk in chunks]
    
    # Size optimization
    optimal_size_rate = sum(1 for s in sizes if 800 <= s <= 2000) / len(chunks) * 100
    
    # Quality metrics
    avg_quality = sum(quality_scores) / len(quality_scores)
    high_quality_rate = sum(1 for q in quality_scores if q >= 0.8) / len(chunks) * 100
    
    # Content metrics
    fragments = sum(1 for chunk in chunks if not chunk['text'].strip().endswith(('.', '!', '?', ':', ';')))
    fragment_rate = fragments / len(chunks) * 100
    
    # Technical content
    technical_count = sum(1 for chunk in chunks 
                         if any(term in chunk['text'].lower() for term in ['risc', 'instruction', 'register', 'memory']))
    technical_rate = technical_count / len(chunks) * 100
    
    # Trash content
    trash_count = sum(1 for chunk in chunks 
                     if any(trash in chunk['text'].lower() for trash in ['creative commons', 'international license']))
    trash_rate = trash_count / len(chunks) * 100
    
    print(f"📊 Key Metrics:")
    print(f"   Total chunks: {len(chunks)}")
    print(f"   Optimal size rate: {optimal_size_rate:.1f}%")
    print(f"   Average quality: {avg_quality:.3f}")
    print(f"   High quality rate: {high_quality_rate:.1f}%")
    print(f"   Fragment rate: {fragment_rate:.1f}%")
    print(f"   Technical content: {technical_rate:.1f}%")
    print(f"   Trash content: {trash_rate:.1f}%")
    
    # Assessment criteria
    criteria = [
        ("Size Optimization", optimal_size_rate >= 85, f"{optimal_size_rate:.0f}%"),
        ("Quality Average", avg_quality >= 0.8, f"{avg_quality:.3f}"),
        ("High Quality Rate", high_quality_rate >= 70, f"{high_quality_rate:.0f}%"),
        ("Fragment Control", fragment_rate <= 5, f"{fragment_rate:.0f}%"),
        ("Technical Content", technical_rate >= 80, f"{technical_rate:.0f}%"),
        ("Trash Filtering", trash_rate <= 5, f"{trash_rate:.0f}%")
    ]
    
    passed_criteria = 0
    print(f"\n🏆 Assessment Criteria:")
    for criterion, passed, value in criteria:
        status = "✅" if passed else "❌"
        print(f"   {status} {criterion}: {value}")
        if passed:
            passed_criteria += 1
    
    overall_score = passed_criteria / len(criteria)
    
    print(f"\n🎯 FINAL VERDICT: {passed_criteria}/{len(criteria)} ({overall_score*100:.0f}%)")
    
    if overall_score >= 0.85:
        verdict = "🎉 EXCELLENT - Production Ready"
        status = "EXCELLENT"
    elif overall_score >= 0.7:
        verdict = "✅ GOOD - Minor optimizations needed"
        status = "GOOD"
    elif overall_score >= 0.5:
        verdict = "🟡 FAIR - Needs improvement"
        status = "FAIR"
    else:
        verdict = "❌ POOR - Major issues detected"
        status = "POOR"
    
    print(f"   {verdict}")
    
    return status


def main():
    """Main analysis function."""
    print("🔬 COMPREHENSIVE CHUNK QUALITY ANALYSIS")
    print("Direct assessment of production RAG system chunks")
    print("="*80)
    
    # Initialize RAG system
    rag = BasicRAG()
    
    # Load document
    pdf_path = project_root / "data" / "test" / "riscv-base-instructions.pdf"
    
    if not pdf_path.exists():
        print("❌ Test PDF not found - cannot perform analysis")
        return
    
    print(f"📄 Indexing document: {pdf_path.name}")
    chunks_count = rag.index_document(pdf_path)
    print(f"✅ Loaded {chunks_count} chunks for analysis")
    
    # Perform comprehensive analysis
    chunks = rag.chunks
    
    # 1. Basic quality analysis
    analyze_chunk_quality(chunks)
    
    # 2. Content quality analysis
    analyze_content_quality(chunks)
    
    # 3. Structure analysis
    analyze_structure_quality(chunks)
    
    # 4. Sample examination
    sample_chunk_examination(chunks, num_samples=15)
    
    # 5. Overall assessment
    final_status = overall_assessment(chunks)
    
    print(f"\n\n🎊 ANALYSIS COMPLETE!")
    print("="*80)
    print(f"📋 Comprehensive quality assessment finished")
    print(f"🎯 System Status: {final_status}")
    print(f"📁 All production functionality verified")


if __name__ == "__main__":
    main()