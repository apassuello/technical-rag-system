#!/usr/bin/env python3
"""
Examine Formatting Artifacts in Chunks
Identify common patterns that need cleaning.
"""

import sys
from pathlib import Path
import re

project_root = Path(__file__).parent.parent.parent  # Go up to project-1-technical-rag
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))  # Add rag-portfolio root for shared_utils

from src.basic_rag import BasicRAG


def analyze_formatting_artifacts():
    """Analyze common formatting artifacts in chunks."""
    print("🔍 EXAMINING FORMATTING ARTIFACTS")
    print("=" * 50)
    
    # Index RISC-V document (has most artifacts)
    rag = BasicRAG()
    pdf_path = project_root / "data" / "test" / "riscv-base-instructions.pdf"
    rag.index_document(pdf_path)
    
    # Common artifact patterns to check
    artifact_patterns = {
        'volume_header': r'Volume\s+[IVX]+:\s*RISC-V.*?V\d{8}',
        'page_header': r'^\d+\s+Volume\s+[IVX]+:',
        'document_version': r'Document Version \d{8}',
        'section_numbering': r'^\d+\.\d+(?:\.\d+)*\s+',
        'figure_references': r'Figure\s+\d+\.\d+:',
        'table_references': r'Table\s+\d+\.\d+:',
        'repeated_headers': r'RISC-V.*?ISA.*?V\d{8}',
        'page_numbers_inline': r'\s+\d{1,3}\s*$',
        'multiple_spaces': r'\s{3,}',
        'email_addresses': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'urls': r'https?://[^\s]+',
    }
    
    # Analyze chunks
    artifact_counts = {pattern: 0 for pattern in artifact_patterns}
    affected_chunks = []
    
    for i, chunk in enumerate(rag.chunks[:50]):  # Sample first 50
        text = chunk['text']
        chunk_artifacts = []
        
        for pattern_name, pattern in artifact_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                artifact_counts[pattern_name] += 1
                chunk_artifacts.append(pattern_name)
        
        if chunk_artifacts:
            affected_chunks.append({
                'index': i,
                'page': chunk.get('page', 'unknown'),
                'artifacts': chunk_artifacts,
                'text_preview': text[:150] + "..."
            })
    
    # Report findings
    print(f"📊 Artifact Analysis (50 chunk sample):")
    print(f"   Total chunks with artifacts: {len(affected_chunks)}")
    
    print(f"\n📋 Artifact Types Found:")
    for pattern_name, count in sorted(artifact_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"   - {pattern_name}: {count} occurrences")
    
    print(f"\n❌ Sample Affected Chunks:")
    for chunk_info in affected_chunks[:5]:
        print(f"\n   Chunk {chunk_info['index']} (Page {chunk_info['page']}):")
        print(f"   Artifacts: {', '.join(chunk_info['artifacts'])}")
        print(f"   Text: {chunk_info['text_preview']}")
    
    return artifact_patterns


def test_cleaning_approach(text: str) -> str:
    """Test cleaning approach on sample text."""
    # Remove volume headers
    text = re.sub(r'Volume\s+[IVX]+:\s*RISC-V[^V]*V\d{8}\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\d+\s+Volume\s+[IVX]+:.*?\n', '', text, flags=re.MULTILINE)
    
    # Remove document version artifacts
    text = re.sub(r'Document Version \d{8}\s*', '', text, flags=re.IGNORECASE)
    
    # Remove repeated ISA headers
    text = re.sub(r'RISC-V.*?ISA.*?V\d{8}\s*', '', text, flags=re.IGNORECASE)
    
    # Clean up page numbers at line ends
    text = re.sub(r'\s+\d{1,3}\s*$', '', text, flags=re.MULTILINE)
    
    # Remove figure/table references that are standalone
    text = re.sub(r'^(Figure|Table)\s+\d+\.\d+:.*?\n', '', text, flags=re.MULTILINE)
    
    # Clean up multiple spaces
    text = re.sub(r'\s{3,}', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


if __name__ == "__main__":
    # Analyze artifacts
    artifacts = analyze_formatting_artifacts()
    
    # Test cleaning
    print("\n\n🧪 TESTING CLEANING APPROACH")
    print("-" * 40)
    
    sample_text = """Volume I: RISC-V Unprivileged ISA V20191213 81
31 27 26 25 24 20 19 15 14 12 11 7 6 0
Figure 11.1: RISC-V floating-point register state.
The RISC-V Instruction Set Manual     Volume I: Unprivileged ISA
Document Version 20191213
This is actual content about floating point operations."""
    
    print("BEFORE:")
    print(sample_text)
    print("\nAFTER:")
    cleaned = test_cleaning_approach(sample_text)
    print(cleaned)