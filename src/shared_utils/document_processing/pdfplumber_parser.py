#!/usr/bin/env python3
"""
PDFPlumber-based Parser

Advanced PDF parsing using pdfplumber for better structure detection
and cleaner text extraction.

Author: Arthur Passuello
"""

import re
import pdfplumber
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


class PDFPlumberParser:
    """Advanced PDF parser using pdfplumber for structure-aware extraction."""
    
    def __init__(self, target_chunk_size: int = 1400, min_chunk_size: int = 800,
                 max_chunk_size: int = 2000):
        """Initialize PDFPlumber parser."""
        self.target_chunk_size = target_chunk_size
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        
        # Trash content patterns
        self.trash_patterns = [
            r'Creative Commons.*?License',
            r'International License.*?authors',
            r'RISC-V International',
            r'Visit.*?for further',
            r'editors to suggest.*?corrections',
            r'released under.*?license',
            r'\.{5,}',  # Long dots (TOC artifacts)
            r'^\d+\s*$',  # Page numbers alone
        ]
        
    def extract_with_structure(self, pdf_path: Path) -> List[Dict]:
        """Extract PDF content with structure awareness using pdfplumber."""
        chunks = []
        
        with pdfplumber.open(pdf_path) as pdf:
            current_section = None
            current_text = []
            
            for page_num, page in enumerate(pdf.pages):
                # Extract text with formatting info
                page_content = self._extract_page_content(page, page_num + 1)
                
                for element in page_content:
                    if element['type'] == 'header':
                        # Save previous section if exists
                        if current_text:
                            chunk_text = '\n\n'.join(current_text)
                            if self._is_valid_chunk(chunk_text):
                                chunks.extend(self._create_chunks(
                                    chunk_text, 
                                    current_section or "Document",
                                    page_num
                                ))
                        
                        # Start new section
                        current_section = element['text']
                        current_text = []
                        
                    elif element['type'] == 'content':
                        # Add to current section
                        if self._is_valid_content(element['text']):
                            current_text.append(element['text'])
            
            # Don't forget last section
            if current_text:
                chunk_text = '\n\n'.join(current_text)
                if self._is_valid_chunk(chunk_text):
                    chunks.extend(self._create_chunks(
                        chunk_text,
                        current_section or "Document",
                        len(pdf.pages)
                    ))
        
        return chunks
    
    def _extract_page_content(self, page: Any, page_num: int) -> List[Dict]:
        """Extract structured content from a page."""
        content = []
        
        # Get all text with positioning
        chars = page.chars
        if not chars:
            return content
        
        # Group by lines
        lines = []
        current_line = []
        current_y = None
        
        for char in sorted(chars, key=lambda x: (x['top'], x['x0'])):
            if current_y is None or abs(char['top'] - current_y) < 2:
                current_line.append(char)
                current_y = char['top']
            else:
                if current_line:
                    lines.append(current_line)
                current_line = [char]
                current_y = char['top']
        
        if current_line:
            lines.append(current_line)
        
        # Analyze each line
        for line in lines:
            line_text = ''.join(char['text'] for char in line).strip()
            
            if not line_text:
                continue
            
            # Detect headers by font size
            avg_font_size = sum(char.get('size', 12) for char in line) / len(line)
            is_bold = any(char.get('fontname', '').lower().count('bold') > 0 for char in line)
            
            # Classify content
            if avg_font_size > 14 or is_bold:
                # Likely a header
                if self._is_valid_header(line_text):
                    content.append({
                        'type': 'header',
                        'text': line_text,
                        'font_size': avg_font_size,
                        'page': page_num
                    })
            else:
                # Regular content
                content.append({
                    'type': 'content',
                    'text': line_text,
                    'font_size': avg_font_size,
                    'page': page_num
                })
        
        return content
    
    def _is_valid_header(self, text: str) -> bool:
        """Check if text is a valid header."""
        # Skip if too short or too long
        if len(text) < 3 or len(text) > 200:
            return False
        
        # Skip if matches trash patterns
        for pattern in self.trash_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        # Valid if starts with number or capital letter
        if re.match(r'^(\d+\.?\d*\s+|[A-Z])', text):
            return True
        
        # Valid if contains keywords
        keywords = ['chapter', 'section', 'introduction', 'conclusion', 'appendix']
        return any(keyword in text.lower() for keyword in keywords)
    
    def _is_valid_content(self, text: str) -> bool:
        """Check if text is valid content (not trash)."""
        # Skip very short text
        if len(text.strip()) < 10:
            return False
        
        # Skip trash patterns
        for pattern in self.trash_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        return True
    
    def _is_valid_chunk(self, text: str) -> bool:
        """Check if chunk text is valid."""
        # Must have minimum length
        if len(text.strip()) < self.min_chunk_size // 2:
            return False
        
        # Must have some alphabetic content
        alpha_chars = sum(1 for c in text if c.isalpha())
        if alpha_chars < len(text) * 0.5:
            return False
        
        return True
    
    def _create_chunks(self, text: str, title: str, page: int) -> List[Dict]:
        """Create chunks from text."""
        chunks = []
        
        # Clean text
        text = self._clean_text(text)
        
        if len(text) <= self.max_chunk_size:
            # Single chunk
            chunks.append({
                'text': text,
                'title': title,
                'page': page,
                'metadata': {
                    'parsing_method': 'pdfplumber',
                    'quality_score': self._calculate_quality_score(text)
                }
            })
        else:
            # Split into chunks
            text_chunks = self._split_text_into_chunks(text)
            for i, chunk_text in enumerate(text_chunks):
                chunks.append({
                    'text': chunk_text,
                    'title': f"{title} (Part {i+1})",
                    'page': page,
                    'metadata': {
                        'parsing_method': 'pdfplumber',
                        'part_number': i + 1,
                        'total_parts': len(text_chunks),
                        'quality_score': self._calculate_quality_score(chunk_text)
                    }
                })
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean text from artifacts."""
        # Remove volume headers (e.g., "Volume I: RISC-V Unprivileged ISA V20191213")
        text = re.sub(r'Volume\s+[IVX]+:\s*RISC-V[^V]*V\d{8}\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^\d+\s+Volume\s+[IVX]+:.*?$', '', text, flags=re.MULTILINE)
        
        # Remove document version artifacts
        text = re.sub(r'Document Version \d{8}\s*', '', text, flags=re.IGNORECASE)
        
        # Remove repeated ISA headers
        text = re.sub(r'RISC-V.*?ISA.*?V\d{8}\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'The RISC-V Instruction Set Manual\s*', '', text, flags=re.IGNORECASE)
        
        # Remove figure/table references that are standalone
        text = re.sub(r'^(Figure|Table)\s+\d+\.\d+:.*?$', '', text, flags=re.MULTILINE)
        
        # Remove email addresses (often in contributor lists)
        text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', text)
        
        # Remove URLs
        text = re.sub(r'https?://[^\s]+', '', text)
        
        # Remove page numbers at start/end of lines
        text = re.sub(r'^\d{1,3}\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\s+\d{1,3}$', '', text, flags=re.MULTILINE)
        
        # Remove excessive dots (TOC artifacts)
        text = re.sub(r'\.{3,}', '', text)
        
        # Remove standalone numbers (often page numbers or figure numbers)
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        
        # Clean up multiple spaces and newlines
        text = re.sub(r'\s{3,}', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)  # Normalize all whitespace
        
        # Remove common boilerplate phrases
        text = re.sub(r'Contains Nonbinding Recommendations\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Guidance for Industry and FDA Staff\s*', '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """Split text into chunks at sentence boundaries."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > self.target_chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size + 1
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _calculate_quality_score(self, text: str) -> float:
        """Calculate quality score for chunk."""
        score = 1.0
        
        # Penalize very short or very long
        if len(text) < self.min_chunk_size:
            score *= 0.8
        elif len(text) > self.max_chunk_size:
            score *= 0.9
        
        # Reward complete sentences
        if text.strip().endswith(('.', '!', '?')):
            score *= 1.1
        
        # Reward technical content
        technical_terms = ['risc', 'instruction', 'register', 'memory', 'processor']
        term_count = sum(1 for term in technical_terms if term in text.lower())
        score *= (1 + term_count * 0.05)
        
        return min(score, 1.0)

    def extract_with_page_coverage(self, pdf_path: Path, pymupdf_pages: List[Dict]) -> List[Dict]:
        """
        Extract content ensuring ALL pages are covered using PyMuPDF page data.
        
        Args:
            pdf_path: Path to PDF file
            pymupdf_pages: Page data from PyMuPDF with page numbers and text
            
        Returns:
            List of chunks covering ALL document pages
        """
        chunks = []
        chunk_id = 0
        
        print(f"📄 Processing {len(pymupdf_pages)} pages with PDFPlumber quality extraction...")
        
        with pdfplumber.open(str(pdf_path)) as pdf:
            for pymupdf_page in pymupdf_pages:
                page_num = pymupdf_page['page_number']  # 1-indexed from PyMuPDF
                page_idx = page_num - 1  # Convert to 0-indexed for PDFPlumber
                
                if page_idx < len(pdf.pages):
                    # Extract with PDFPlumber quality from this specific page
                    pdfplumber_page = pdf.pages[page_idx]
                    page_text = pdfplumber_page.extract_text()
                    
                    if page_text and page_text.strip():
                        # Clean and chunk the page text
                        cleaned_text = self._clean_text(page_text)
                        
                        if len(cleaned_text) >= 100:  # Minimum meaningful content
                            # Create chunks from this page
                            page_chunks = self._create_page_chunks(
                                cleaned_text, page_num, chunk_id
                            )
                            chunks.extend(page_chunks)
                            chunk_id += len(page_chunks)
                            
                            if len(chunks) % 50 == 0:  # Progress indicator
                                print(f"   Processed {page_num} pages, created {len(chunks)} chunks")
        
        print(f"✅ Full coverage: {len(chunks)} chunks from {len(pymupdf_pages)} pages")
        return chunks
    
    def _create_page_chunks(self, page_text: str, page_num: int, start_chunk_id: int) -> List[Dict]:
        """Create properly sized chunks from a single page's content."""
        # Clean and validate page text first
        cleaned_text = self._ensure_complete_sentences(page_text)
        
        if not cleaned_text or len(cleaned_text) < 50:
            # Skip pages with insufficient content
            return []
        
        if len(cleaned_text) <= self.max_chunk_size:
            # Single chunk for small pages
            return [{
                'text': cleaned_text,
                'title': f"Page {page_num}",
                'page': page_num,
                'metadata': {
                    'parsing_method': 'pdfplumber_page_coverage',
                    'quality_score': self._calculate_quality_score(cleaned_text),
                    'full_page_coverage': True
                }
            }]
        else:
            # Split large pages into chunks with sentence boundaries
            text_chunks = self._split_text_into_chunks(cleaned_text)
            page_chunks = []
            
            for i, chunk_text in enumerate(text_chunks):
                # Ensure each chunk is complete
                complete_chunk = self._ensure_complete_sentences(chunk_text)
                
                if complete_chunk and len(complete_chunk) >= 100:
                    page_chunks.append({
                        'text': complete_chunk,
                        'title': f"Page {page_num} (Part {i+1})",
                        'page': page_num,
                        'metadata': {
                            'parsing_method': 'pdfplumber_page_coverage',
                            'part_number': i + 1,
                            'total_parts': len(text_chunks),
                            'quality_score': self._calculate_quality_score(complete_chunk),
                            'full_page_coverage': True
                        }
                    })
            
            return page_chunks
    
    def _ensure_complete_sentences(self, text: str) -> str:
        """Ensure text contains only complete sentences."""
        text = text.strip()
        if not text:
            return ""
        
        # Find last complete sentence
        last_sentence_end = -1
        for i, char in enumerate(reversed(text)):
            if char in '.!?:':
                last_sentence_end = len(text) - i
                break
        
        if last_sentence_end > 0:
            # Return text up to last complete sentence
            complete_text = text[:last_sentence_end].strip()
            
            # Ensure it starts properly (capital letter or common starters)
            if complete_text and (complete_text[0].isupper() or 
                                complete_text.startswith(('The ', 'A ', 'An ', 'This ', 'RISC'))):
                return complete_text
        
        # If no complete sentences found, return empty
        return ""

    def parse_document(self, pdf_path: Path, pdf_data: Dict[str, Any] = None) -> List[Dict]:
        """
        Parse document using PDFPlumber (required by HybridParser).
        
        Args:
            pdf_path: Path to PDF file
            pdf_data: PyMuPDF page data to ensure full page coverage
            
        Returns:
            List of chunks with structure preservation across ALL pages
        """
        if pdf_data and 'pages' in pdf_data:
            # Use PyMuPDF page data to ensure full coverage
            return self.extract_with_page_coverage(pdf_path, pdf_data['pages'])
        else:
            # Fallback to structure-based extraction
            return self.extract_with_structure(pdf_path)


def parse_pdf_with_pdfplumber(pdf_path: Path, **kwargs) -> List[Dict]:
    """Main entry point for PDFPlumber parsing."""
    parser = PDFPlumberParser(**kwargs)
    chunks = parser.extract_with_structure(pdf_path)
    
    print(f"PDFPlumber extracted {len(chunks)} chunks")
    
    return chunks