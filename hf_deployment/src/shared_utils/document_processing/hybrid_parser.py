#!/usr/bin/env python3
"""
Hybrid TOC + PDFPlumber Parser

Combines the best of both approaches:
1. TOC-guided navigation for reliable chapter/section mapping
2. PDFPlumber's precise content extraction with formatting awareness
3. Aggressive trash content filtering while preserving actual content

This hybrid approach provides:
- Reliable structure detection (TOC)
- High-quality content extraction (PDFPlumber)
- Optimal chunk sizing and quality
- Fast processing with precise results

Author: Arthur Passuello
Date: 2025-07-01
"""

import re
import pdfplumber
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from .toc_guided_parser import TOCGuidedParser, TOCEntry
from .pdfplumber_parser import PDFPlumberParser


class HybridParser:
    """
    Hybrid parser combining TOC navigation with PDFPlumber extraction.
    
    Architecture:
    1. Use TOC to identify chapter/section boundaries and pages
    2. Use PDFPlumber to extract clean content from those specific pages
    3. Apply aggressive content filtering to remove trash
    4. Create optimal chunks with preserved structure
    """
    
    def __init__(self, target_chunk_size: int = 1400, min_chunk_size: int = 800, 
                 max_chunk_size: int = 2000):
        """Initialize hybrid parser."""
        self.target_chunk_size = target_chunk_size
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        
        # Initialize component parsers
        self.toc_parser = TOCGuidedParser(target_chunk_size, min_chunk_size, max_chunk_size)
        self.plumber_parser = PDFPlumberParser(target_chunk_size, min_chunk_size, max_chunk_size)
        
        # Content filtering patterns (aggressive trash removal)
        self.trash_patterns = [
            # License and legal text
            r'Creative Commons.*?License',
            r'International License.*?authors',
            r'released under.*?license',
            r'derivative of.*?License',
            r'Document Version \d+',
            
            # Table of contents artifacts
            r'\.{3,}',  # Multiple dots
            r'^\s*\d+\s*$',  # Standalone page numbers
            r'Contents\s*$',
            r'Preface\s*$',
            
            # PDF formatting artifacts
            r'Volume\s+[IVX]+:.*?V\d+',
            r'^\s*[ivx]+\s*$',  # Roman numerals alone
            r'^\s*[\d\w\s]{1,3}\s*$',  # Very short meaningless lines
            
            # Redundant headers and footers
            r'RISC-V.*?ISA.*?V\d+',
            r'Volume I:.*?Unprivileged',
            
            # Editor and publication info
            r'Editors?:.*?[A-Z][a-z]+',
            r'[A-Z][a-z]+\s+\d{1,2},\s+\d{4}',  # Dates
            r'@[a-z]+\.[a-z]+',  # Email addresses
            
            # Boilerplate text
            r'please contact editors to suggest corrections',
            r'alphabetical order.*?corrections',
            r'contributors to all versions',
        ]
        
        # Content quality patterns (preserve these)
        self.preserve_patterns = [
            r'RISC-V.*?instruction',
            r'register.*?file',
            r'memory.*?operation',
            r'processor.*?implementation',
            r'architecture.*?design',
        ]
        
        # TOC-specific patterns to exclude from searchable content
        self.toc_exclusion_patterns = [
            r'^\s*Contents\s*$',
            r'^\s*Table\s+of\s+Contents\s*$',
            r'^\s*\d+(?:\.\d+)*\s*$',  # Standalone section numbers
            r'^\s*\d+(?:\.\d+)*\s+[A-Z]',  # "1.1 INTRODUCTION" style
            r'\.{3,}',  # Multiple dots (TOC formatting)
            r'^\s*Chapter\s+\d+\s*$',  # Standalone "Chapter N"
            r'^\s*Section\s+\d+(?:\.\d+)*\s*$',  # Standalone "Section N.M"
            r'^\s*Appendix\s+[A-Z]\s*$',  # Standalone "Appendix A"
            r'^\s*[ivxlcdm]+\s*$',  # Roman numerals alone
            r'^\s*Preface\s*$',
            r'^\s*Introduction\s*$',
            r'^\s*Conclusion\s*$',
            r'^\s*Bibliography\s*$',
            r'^\s*Index\s*$',
        ]
    
    def parse_document(self, pdf_path: Path, pdf_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse document using hybrid approach.
        
        Args:
            pdf_path: Path to PDF file
            pdf_data: PDF data from extract_text_with_metadata()
            
        Returns:
            List of high-quality chunks with preserved structure
        """
        print("🔗 Starting Hybrid TOC + PDFPlumber parsing...")
        
        # Step 1: Use TOC to identify structure
        print("📋 Step 1: Extracting TOC structure...")
        toc_entries = self.toc_parser.parse_toc(pdf_data['pages'])
        print(f"   Found {len(toc_entries)} TOC entries")
        
        # Check if TOC is reliable (multiple entries or quality single entry)
        toc_is_reliable = (
            len(toc_entries) > 1 or  # Multiple entries = likely real TOC
            (len(toc_entries) == 1 and len(toc_entries[0].title) > 10)  # Quality single entry
        )
        
        if not toc_entries or not toc_is_reliable:
            if not toc_entries:
                print("   ⚠️ No TOC found, using full page coverage parsing")
            else:
                print(f"   ⚠️ TOC quality poor (title: '{toc_entries[0].title}'), using full page coverage")
            return self.plumber_parser.parse_document(pdf_path, pdf_data)
        
        # Step 2: Use PDFPlumber for precise extraction
        print("🔬 Step 2: PDFPlumber extraction of TOC sections...")
        chunks = []
        chunk_id = 0
        
        with pdfplumber.open(str(pdf_path)) as pdf:
            for i, toc_entry in enumerate(toc_entries):
                next_entry = toc_entries[i + 1] if i + 1 < len(toc_entries) else None
                
                # Extract content using PDFPlumber
                section_content = self._extract_section_with_plumber(
                    pdf, toc_entry, next_entry
                )
                
                if section_content:
                    # Apply aggressive content filtering
                    cleaned_content = self._filter_trash_content(section_content)
                    
                    if cleaned_content and len(cleaned_content) >= 200:  # Minimum meaningful content
                        # Create chunks from cleaned content
                        section_chunks = self._create_chunks_from_clean_content(
                            cleaned_content, chunk_id, toc_entry
                        )
                        chunks.extend(section_chunks)
                        chunk_id += len(section_chunks)
        
        print(f"   Created {len(chunks)} high-quality chunks")
        return chunks
    
    def _extract_section_with_plumber(self, pdf, toc_entry: TOCEntry, 
                                     next_entry: Optional[TOCEntry]) -> str:
        """
        Extract section content using PDFPlumber's precise extraction.
        
        Args:
            pdf: PDFPlumber PDF object
            toc_entry: Current TOC entry
            next_entry: Next TOC entry (for boundary detection)
            
        Returns:
            Clean extracted content for this section
        """
        start_page = max(0, toc_entry.page - 1)  # Convert to 0-indexed
        
        if next_entry:
            end_page = min(len(pdf.pages), next_entry.page - 1)
        else:
            end_page = len(pdf.pages)
        
        content_parts = []
        
        for page_idx in range(start_page, end_page):
            if page_idx < len(pdf.pages):
                page = pdf.pages[page_idx]
                
                # Extract text with PDFPlumber (preserves formatting)
                page_text = page.extract_text()
                
                if page_text:
                    # Clean page content while preserving structure
                    cleaned_text = self._clean_page_content_precise(page_text)
                    if cleaned_text.strip():
                        content_parts.append(cleaned_text)
        
        return ' '.join(content_parts)
    
    def _clean_page_content_precise(self, page_text: str) -> str:
        """
        Clean page content with precision, removing artifacts but preserving content.
        
        Args:
            page_text: Raw page text from PDFPlumber
            
        Returns:
            Cleaned text with artifacts removed
        """
        lines = page_text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Skip obvious artifacts but be conservative
            if (len(line) < 3 or  # Very short lines
                re.match(r'^\d+$', line) or  # Standalone numbers
                re.match(r'^[ivx]+$', line.lower()) or  # Roman numerals alone
                '.' * 5 in line):  # TOC dots
                continue
            
            # Preserve technical content even if it looks like an artifact
            has_technical_content = any(term in line.lower() for term in [
                'risc', 'register', 'instruction', 'memory', 'processor', 
                'architecture', 'implementation', 'specification'
            ])
            
            if has_technical_content or len(line) >= 10:
                cleaned_lines.append(line)
        
        return ' '.join(cleaned_lines)
    
    def _filter_trash_content(self, content: str) -> str:
        """
        Apply aggressive trash filtering while preserving actual content.
        
        Args:
            content: Raw content to filter
            
        Returns:
            Content with trash removed but technical content preserved
        """
        if not content.strip():
            return ""
        
        # First, identify and preserve important technical sentences
        sentences = re.split(r'[.!?]+\s*', content)
        preserved_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if sentence contains important technical content
            is_technical = any(term in sentence.lower() for term in [
                'risc-v', 'register', 'instruction', 'memory', 'processor',
                'architecture', 'implementation', 'specification', 'encoding',
                'bit', 'byte', 'address', 'data', 'control', 'operand'
            ])
            
            # Check if sentence is trash (including general trash and TOC content)
            is_trash = any(re.search(pattern, sentence, re.IGNORECASE) 
                          for pattern in self.trash_patterns)
            
            # Check if sentence is TOC content (should be excluded)
            is_toc_content = any(re.search(pattern, sentence, re.IGNORECASE) 
                               for pattern in self.toc_exclusion_patterns)
            
            # Preserve if technical and not trash/TOC, or if substantial and not clearly trash/TOC
            if ((is_technical and not is_trash and not is_toc_content) or 
                (len(sentence) > 50 and not is_trash and not is_toc_content)):
                preserved_sentences.append(sentence)
        
        # Reconstruct content from preserved sentences
        filtered_content = '. '.join(preserved_sentences)
        
        # Final cleanup
        filtered_content = re.sub(r'\s+', ' ', filtered_content)  # Normalize whitespace
        filtered_content = re.sub(r'\.+', '.', filtered_content)  # Remove multiple dots
        
        # Ensure proper sentence ending
        if filtered_content and not filtered_content.rstrip().endswith(('.', '!', '?', ':', ';')):
            filtered_content = filtered_content.rstrip() + '.'
        
        return filtered_content.strip()
    
    def _create_chunks_from_clean_content(self, content: str, start_chunk_id: int, 
                                         toc_entry: TOCEntry) -> List[Dict[str, Any]]:
        """
        Create optimally-sized chunks from clean content.
        
        Args:
            content: Clean, filtered content
            start_chunk_id: Starting chunk ID
            toc_entry: TOC entry metadata
            
        Returns:
            List of chunk dictionaries
        """
        if not content or len(content) < 100:
            return []
        
        chunks = []
        
        # If content fits in one chunk, create single chunk
        if self.min_chunk_size <= len(content) <= self.max_chunk_size:
            chunk = self._create_chunk(content, start_chunk_id, toc_entry)
            chunks.append(chunk)
        
        # If too large, split intelligently at sentence boundaries
        elif len(content) > self.max_chunk_size:
            sub_chunks = self._split_large_content_smart(content, start_chunk_id, toc_entry)
            chunks.extend(sub_chunks)
        
        # If too small but substantial, keep it
        elif len(content) >= 200:  # Lower threshold for cleaned content
            chunk = self._create_chunk(content, start_chunk_id, toc_entry)
            chunks.append(chunk)
        
        return chunks
    
    def _split_large_content_smart(self, content: str, start_chunk_id: int, 
                                  toc_entry: TOCEntry) -> List[Dict[str, Any]]:
        """
        Split large content intelligently at natural boundaries.
        
        Args:
            content: Content to split
            start_chunk_id: Starting chunk ID
            toc_entry: TOC entry metadata
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        
        # Split at sentence boundaries
        sentences = re.split(r'([.!?:;]+\s*)', content)
        
        current_chunk = ""
        chunk_id = start_chunk_id
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i].strip()
            if not sentence:
                continue
            
            # Add punctuation if available
            punctuation = sentences[i + 1] if i + 1 < len(sentences) else '.'
            full_sentence = sentence + punctuation
            
            # Check if adding this sentence exceeds max size
            potential_chunk = current_chunk + (" " if current_chunk else "") + full_sentence
            
            if len(potential_chunk) <= self.max_chunk_size:
                current_chunk = potential_chunk
            else:
                # Save current chunk if it meets minimum size
                if current_chunk and len(current_chunk) >= self.min_chunk_size:
                    chunk = self._create_chunk(current_chunk, chunk_id, toc_entry)
                    chunks.append(chunk)
                    chunk_id += 1
                
                # Start new chunk
                current_chunk = full_sentence
        
        # Add final chunk if substantial
        if current_chunk and len(current_chunk) >= 200:
            chunk = self._create_chunk(current_chunk, chunk_id, toc_entry)
            chunks.append(chunk)
        
        return chunks
    
    def _create_chunk(self, content: str, chunk_id: int, toc_entry: TOCEntry) -> Dict[str, Any]:
        """Create a chunk dictionary with hybrid metadata."""
        return {
            "text": content,
            "chunk_id": chunk_id,
            "title": toc_entry.title,
            "parent_title": toc_entry.parent_title,
            "level": toc_entry.level,
            "page": toc_entry.page,
            "size": len(content),
            "metadata": {
                "parsing_method": "hybrid_toc_pdfplumber",
                "has_context": True,
                "content_type": "filtered_structured_content",
                "quality_score": self._calculate_quality_score(content),
                "trash_filtered": True
            }
        }
    
    def _calculate_quality_score(self, content: str) -> float:
        """Calculate quality score for filtered content."""
        if not content.strip():
            return 0.0
        
        words = content.split()
        score = 0.0
        
        # Length score (25%)
        if self.min_chunk_size <= len(content) <= self.max_chunk_size:
            score += 0.25
        elif len(content) >= 200:  # At least some content
            score += 0.15
        
        # Content richness (25%)
        substantial_words = sum(1 for word in words if len(word) > 3)
        richness_score = min(substantial_words / 30, 1.0)  # Lower threshold for filtered content
        score += richness_score * 0.25
        
        # Technical content (30%)
        technical_terms = ['risc', 'register', 'instruction', 'cpu', 'memory', 'processor', 'architecture']
        technical_count = sum(1 for word in words if any(term in word.lower() for term in technical_terms))
        technical_score = min(technical_count / 3, 1.0)  # Lower threshold
        score += technical_score * 0.30
        
        # Completeness (20%)
        completeness_score = 0.0
        if content[0].isupper() or content.startswith(('The ', 'A ', 'An ', 'RISC')):
            completeness_score += 0.5
        if content.rstrip().endswith(('.', '!', '?', ':', ';')):
            completeness_score += 0.5
        score += completeness_score * 0.20
        
        return min(score, 1.0)


def parse_pdf_with_hybrid_approach(pdf_path: Path, pdf_data: Dict[str, Any],
                                  target_chunk_size: int = 1400, min_chunk_size: int = 800,
                                  max_chunk_size: int = 2000) -> List[Dict[str, Any]]:
    """
    Parse PDF using hybrid TOC + PDFPlumber approach.
    
    This function combines:
    1. TOC-guided structure detection for reliable navigation
    2. PDFPlumber's precise content extraction
    3. Aggressive trash filtering while preserving technical content
    
    Args:
        pdf_path: Path to PDF file
        pdf_data: PDF data from extract_text_with_metadata()
        target_chunk_size: Preferred chunk size
        min_chunk_size: Minimum chunk size
        max_chunk_size: Maximum chunk size
        
    Returns:
        List of high-quality, filtered chunks ready for RAG indexing
        
    Example:
        >>> from src.shared_utils.document_processing.pdf_parser import extract_text_with_metadata
        >>> from src.shared_utils.document_processing.hybrid_parser import parse_pdf_with_hybrid_approach
        >>> 
        >>> pdf_data = extract_text_with_metadata("document.pdf")
        >>> chunks = parse_pdf_with_hybrid_approach(Path("document.pdf"), pdf_data)
        >>> print(f"Created {len(chunks)} hybrid-parsed chunks")
    """
    parser = HybridParser(target_chunk_size, min_chunk_size, max_chunk_size)
    return parser.parse_document(pdf_path, pdf_data)


# Example usage
if __name__ == "__main__":
    print("Hybrid TOC + PDFPlumber Parser")
    print("Combines TOC navigation with PDFPlumber precision and aggressive trash filtering")