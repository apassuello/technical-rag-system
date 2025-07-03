#!/usr/bin/env python3
"""
TOC-Guided PDF Parser

Uses the Table of Contents to guide intelligent chunking that respects
document structure and hierarchy.

Author: Arthur Passuello
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TOCEntry:
    """Represents a table of contents entry."""
    title: str
    page: int
    level: int  # 0 for chapters, 1 for sections, 2 for subsections
    parent: Optional[str] = None
    parent_title: Optional[str] = None  # Added for hybrid parser compatibility


class TOCGuidedParser:
    """Parser that uses TOC to create structure-aware chunks."""
    
    def __init__(self, target_chunk_size: int = 1400, min_chunk_size: int = 800,
                 max_chunk_size: int = 2000):
        """Initialize TOC-guided parser."""
        self.target_chunk_size = target_chunk_size
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        
    def parse_toc(self, pages: List[Dict]) -> List[TOCEntry]:
        """Parse table of contents from pages."""
        toc_entries = []
        
        # Find TOC pages (usually early in document)
        toc_pages = []
        for i, page in enumerate(pages[:20]):  # Check first 20 pages
            page_text = page.get('text', '').lower()
            if 'contents' in page_text or 'table of contents' in page_text:
                toc_pages.append((i, page))
        
        if not toc_pages:
            print("No TOC found, using fallback structure detection")
            return self._detect_structure_without_toc(pages)
        
        # Parse TOC entries
        for page_idx, page in toc_pages:
            text = page.get('text', '')
            lines = text.split('\n')
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Skip empty lines and TOC header
                if not line or 'contents' in line.lower():
                    i += 1
                    continue
                
                # Pattern 1: "1.1 Title .... 23"
                match1 = re.match(r'^(\d+(?:\.\d+)*)\s+(.+?)\s*\.{2,}\s*(\d+)$', line)
                if match1:
                    number, title, page_num = match1.groups()
                    level = len(number.split('.')) - 1
                    toc_entries.append(TOCEntry(
                        title=title.strip(),
                        page=int(page_num),
                        level=level
                    ))
                    i += 1
                    continue
                
                # Pattern 2: Multi-line format
                # "1.1"
                # "Title"
                # ". . . . 23"
                if re.match(r'^(\d+(?:\.\d+)*)$', line):
                    number = line
                    if i + 1 < len(lines):
                        title_line = lines[i + 1].strip()
                        if i + 2 < len(lines):
                            dots_line = lines[i + 2].strip()
                            page_match = re.search(r'(\d+)\s*$', dots_line)
                            if page_match and '.' in dots_line:
                                title = title_line
                                page_num = int(page_match.group(1))
                                level = len(number.split('.')) - 1
                                toc_entries.append(TOCEntry(
                                    title=title,
                                    page=page_num,
                                    level=level
                                ))
                                i += 3
                                continue
                
                # Pattern 3: "Chapter 1: Title ... 23"
                match3 = re.match(r'^(Chapter|Section|Part)\s+(\d+):?\s+(.+?)\s*\.{2,}\s*(\d+)$', line, re.IGNORECASE)
                if match3:
                    prefix, number, title, page_num = match3.groups()
                    level = 0 if prefix.lower() == 'chapter' else 1
                    toc_entries.append(TOCEntry(
                        title=f"{prefix} {number}: {title}",
                        page=int(page_num),
                        level=level
                    ))
                    i += 1
                    continue
                
                i += 1
        
        # Add parent relationships
        for i, entry in enumerate(toc_entries):
            if entry.level > 0:
                # Find parent (previous entry with lower level)
                for j in range(i - 1, -1, -1):
                    if toc_entries[j].level < entry.level:
                        entry.parent = toc_entries[j].title
                        entry.parent_title = toc_entries[j].title  # Set both for compatibility
                        break
        
        return toc_entries
    
    def _detect_structure_without_toc(self, pages: List[Dict]) -> List[TOCEntry]:
        """Fallback: detect structure from content patterns across ALL pages."""
        entries = []
        
        # Expanded patterns for better structure detection
        chapter_patterns = [
            re.compile(r'^(Chapter|CHAPTER)\s+(\d+|[IVX]+)(?:\s*[:\-]\s*(.+))?', re.MULTILINE),
            re.compile(r'^(\d+)\s+([A-Z][^.]*?)(?:\s*\.{2,}\s*\d+)?$', re.MULTILINE),  # "1 Introduction"
            re.compile(r'^([A-Z][A-Z\s]{10,})$', re.MULTILINE),  # ALL CAPS titles
        ]
        
        section_patterns = [
            re.compile(r'^(\d+\.\d+)\s+(.+?)(?:\s*\.{2,}\s*\d+)?$', re.MULTILINE),  # "1.1 Section"
            re.compile(r'^(\d+\.\d+\.\d+)\s+(.+?)(?:\s*\.{2,}\s*\d+)?$', re.MULTILINE),  # "1.1.1 Subsection"
        ]
        
        # Process ALL pages, not just first 20
        for i, page in enumerate(pages):
            text = page.get('text', '')
            if not text.strip():
                continue
            
            # Find chapters with various patterns
            for pattern in chapter_patterns:
                for match in pattern.finditer(text):
                    if len(match.groups()) >= 2:
                        if len(match.groups()) >= 3 and match.group(3):
                            title = match.group(3).strip()
                        else:
                            title = match.group(2).strip() if match.group(2) else f"Section {match.group(1)}"
                        
                        # Skip very short or likely false positives
                        if len(title) >= 3 and not re.match(r'^\d+$', title):
                            entries.append(TOCEntry(
                                title=title,
                                page=i + 1,
                                level=0
                            ))
            
            # Find sections
            for pattern in section_patterns:
                for match in pattern.finditer(text):
                    section_num = match.group(1)
                    title = match.group(2).strip() if len(match.groups()) >= 2 else f"Section {section_num}"
                    
                    # Determine level by number of dots
                    level = section_num.count('.') 
                    
                    # Skip very short titles or obvious artifacts
                    if len(title) >= 3 and not re.match(r'^\d+$', title):
                        entries.append(TOCEntry(
                            title=title,
                            page=i + 1,
                            level=level
                        ))
        
        # If still no entries found, create page-based entries for full coverage
        if not entries:
            print("No structure patterns found, creating page-based sections for full coverage")
            # Create sections every 10 pages to ensure full document coverage
            for i in range(0, len(pages), 10):
                start_page = i + 1
                end_page = min(i + 10, len(pages))
                title = f"Pages {start_page}-{end_page}"
                entries.append(TOCEntry(
                    title=title,
                    page=start_page,
                    level=0
                ))
        
        return entries
    
    def create_chunks_from_toc(self, pdf_data: Dict, toc_entries: List[TOCEntry]) -> List[Dict]:
        """Create chunks based on TOC structure."""
        chunks = []
        pages = pdf_data.get('pages', [])
        
        for i, entry in enumerate(toc_entries):
            # Determine page range for this entry
            start_page = entry.page - 1  # Convert to 0-indexed
            
            # Find end page (start of next entry at same or higher level)
            end_page = len(pages)
            for j in range(i + 1, len(toc_entries)):
                if toc_entries[j].level <= entry.level:
                    end_page = toc_entries[j].page - 1
                    break
            
            # Extract text for this section
            section_text = []
            for page_idx in range(max(0, start_page), min(end_page, len(pages))):
                page_text = pages[page_idx].get('text', '')
                if page_text.strip():
                    section_text.append(page_text)
            
            if not section_text:
                continue
            
            full_text = '\n\n'.join(section_text)
            
            # Create chunks from section text
            if len(full_text) <= self.max_chunk_size:
                # Single chunk for small sections
                chunks.append({
                    'text': full_text.strip(),
                    'title': entry.title,
                    'parent_title': entry.parent_title or entry.parent or '',
                    'level': entry.level,
                    'page': entry.page,
                    'context': f"From {entry.title}",
                    'metadata': {
                        'parsing_method': 'toc_guided',
                        'section_title': entry.title,
                        'hierarchy_level': entry.level
                    }
                })
            else:
                # Split large sections into chunks
                section_chunks = self._split_text_into_chunks(full_text)
                for j, chunk_text in enumerate(section_chunks):
                    chunks.append({
                        'text': chunk_text.strip(),
                        'title': f"{entry.title} (Part {j+1})",
                        'parent_title': entry.parent_title or entry.parent or '',
                        'level': entry.level,
                        'page': entry.page,
                        'context': f"Part {j+1} of {entry.title}",
                        'metadata': {
                            'parsing_method': 'toc_guided',
                            'section_title': entry.title,
                            'hierarchy_level': entry.level,
                            'part_number': j + 1,
                            'total_parts': len(section_chunks)
                        }
                    })
        
        return chunks
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """Split text into chunks while preserving sentence boundaries."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > self.target_chunk_size and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size + 1  # +1 for space
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks


def parse_pdf_with_toc_guidance(pdf_data: Dict, **kwargs) -> List[Dict]:
    """Main entry point for TOC-guided parsing."""
    parser = TOCGuidedParser(**kwargs)
    
    # Parse TOC
    pages = pdf_data.get('pages', [])
    toc_entries = parser.parse_toc(pages)
    
    print(f"Found {len(toc_entries)} TOC entries")
    
    if not toc_entries:
        print("No TOC entries found, falling back to basic chunking")
        from .chunker import chunk_technical_text
        return chunk_technical_text(pdf_data.get('text', ''))
    
    # Create chunks based on TOC
    chunks = parser.create_chunks_from_toc(pdf_data, toc_entries)
    
    print(f"Created {len(chunks)} chunks from TOC structure")
    
    return chunks