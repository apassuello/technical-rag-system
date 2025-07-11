"""
Markdown response parser implementation.

This module provides a parser that extracts structured information
from markdown-formatted LLM responses, including citations and formatting.

Architecture Notes:
- Direct implementation (no adapter needed)
- Pure text parsing algorithms
- Handles various markdown conventions
- Robust citation extraction
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from ..base import ResponseParser, Citation, Document, ParsingError, ConfigurableComponent

logger = logging.getLogger(__name__)


class MarkdownParser(ResponseParser, ConfigurableComponent):
    """
    Parser for markdown-formatted responses.
    
    Features:
    - Extract main answer text
    - Parse inline citations [1], [Document 1], etc.
    - Handle footnote-style citations
    - Preserve formatting (headers, lists, code blocks)
    - Extract confidence statements
    
    Configuration:
    - extract_citations: Whether to extract citations (default: True)
    - citation_patterns: Regex patterns for citations (customizable)
    - preserve_formatting: Keep markdown formatting (default: True)
    - extract_sections: Parse into sections by headers (default: False)
    """
    
    # Default citation patterns
    DEFAULT_CITATION_PATTERNS = [
        r'\[(\d+)\]',                    # [1], [2], etc.
        r'\[Document\s+(\d+)\]',          # [Document 1], [Document 2]
        r'\[Document\s+(\d+),\s*Page\s+\d+\]',  # [Document 1, Page 1], [Document 2, Page 15]
        r'\[Doc\s+(\d+)\]',               # [Doc 1], [Doc 2]
        r'\[\^(\d+)\]',                   # Footnote style [^1]
        r'¹²³⁴⁵⁶⁷⁸⁹⁰',                   # Unicode superscripts
    ]
    
    def __init__(self,
                 extract_citations: bool = True,
                 preserve_formatting: bool = True,
                 extract_sections: bool = False,
                 citation_patterns: Optional[List[str]] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize markdown parser.
        
        Args:
            extract_citations: Whether to extract citations
            preserve_formatting: Keep markdown formatting
            extract_sections: Parse into sections by headers
            citation_patterns: Custom citation regex patterns
            config: Additional configuration
        """
        # Merge config
        parser_config = {
            'extract_citations': extract_citations,
            'preserve_formatting': preserve_formatting,
            'extract_sections': extract_sections,
            'citation_patterns': citation_patterns or self.DEFAULT_CITATION_PATTERNS,
            **(config or {})
        }
        
        super().__init__(parser_config)
        
        self.extract_citations_enabled = parser_config['extract_citations']
        self.preserve_formatting = parser_config['preserve_formatting']
        self.extract_sections = parser_config['extract_sections']
        
        # Compile citation patterns
        self.citation_patterns = [
            re.compile(pattern) for pattern in parser_config['citation_patterns']
        ]
    
    def parse(self, raw_response: str) -> Dict[str, Any]:
        """
        Parse the raw LLM response into structured format.
        
        Args:
            raw_response: Raw text from LLM
            
        Returns:
            Structured dictionary with parsed content
            
        Raises:
            ParsingError: If parsing fails
        """
        if not raw_response:
            raise ParsingError("Empty response to parse")
        
        try:
            # Clean response
            cleaned = self._clean_response(raw_response)
            
            # Extract main components
            result = {
                'answer': cleaned,
                'raw_response': raw_response,
                'format': 'markdown',
                'metadata': {}
            }
            
            # Extract sections if requested
            if self.extract_sections:
                sections = self._extract_sections(cleaned)
                result['sections'] = sections
                result['answer'] = self._merge_sections(sections)
            
            # Extract confidence if present
            confidence = self._extract_confidence(cleaned)
            if confidence is not None:
                result['confidence'] = confidence
            
            # Extract any metadata
            metadata = self._extract_metadata(cleaned)
            result['metadata'].update(metadata)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse response: {str(e)}")
            raise ParsingError(f"Markdown parsing failed: {str(e)}")
    
    def extract_citations(self, response: Dict[str, Any], context: List[Document]) -> List[Citation]:
        """
        Extract citations from the parsed response.
        
        Args:
            response: Parsed response dictionary
            context: Original context documents
            
        Returns:
            List of extracted citations
        """
        if not self.extract_citations_enabled:
            return []
        
        answer_text = response.get('answer', '')
        citations = []
        
        # Find all citation markers in the text
        for pattern in self.citation_patterns:
            for match in pattern.finditer(answer_text):
                citation_marker = match.group(0)
                citation_id = match.group(1) if match.groups() else match.group(0)
                
                # Try to resolve to document
                doc_index = self._resolve_citation_index(citation_id)
                if doc_index is not None and 0 <= doc_index < len(context):
                    # Create citation object
                    citation = Citation(
                        source_id=f"doc_{doc_index}",
                        text=citation_marker,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=0.9  # High confidence for explicit citations
                    )
                    citations.append(citation)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_citations = []
        for citation in citations:
            key = (citation.source_id, citation.text)
            if key not in seen:
                seen.add(key)
                unique_citations.append(citation)
        
        logger.debug(f"Extracted {len(unique_citations)} unique citations")
        return unique_citations
    
    def get_parser_info(self) -> Dict[str, Any]:
        """Get information about the parser."""
        return {
            'type': 'markdown',
            'parser_class': self.__class__.__name__,
            'extract_citations': self.extract_citations_enabled,
            'preserve_formatting': self.preserve_formatting,
            'extract_sections': self.extract_sections,
            'citation_patterns': len(self.citation_patterns),
            'capabilities': {
                'handles_markdown': True,
                'extracts_structure': self.extract_sections,
                'preserves_formatting': self.preserve_formatting
            }
        }
    
    def _clean_response(self, response: str) -> str:
        """
        Clean the response while preserving formatting.
        
        Args:
            response: Raw response text
            
        Returns:
            Cleaned response
        """
        # Remove leading/trailing whitespace
        cleaned = response.strip()
        
        # Remove any markdown artifacts if not preserving
        if not self.preserve_formatting:
            # Remove code blocks
            cleaned = re.sub(r'```[\s\S]*?```', '', cleaned)
            # Remove inline code
            cleaned = re.sub(r'`[^`]+`', lambda m: m.group(0)[1:-1], cleaned)
            # Remove emphasis
            cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)
            cleaned = re.sub(r'\*([^*]+)\*', r'\1', cleaned)
            cleaned = re.sub(r'__([^_]+)__', r'\1', cleaned)
            cleaned = re.sub(r'_([^_]+)_', r'\1', cleaned)
        
        return cleaned
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """
        Extract sections based on markdown headers.
        
        Args:
            text: Markdown text
            
        Returns:
            Dictionary of section_name -> content
        """
        sections = {}
        current_section = "main"
        current_content = []
        
        lines = text.split('\n')
        for line in lines:
            # Check for headers
            header_match = re.match(r'^#+\s+(.+)$', line)
            if header_match:
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = header_match.group(1).strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _merge_sections(self, sections: Dict[str, str]) -> str:
        """
        Merge sections back into a single answer.
        
        Args:
            sections: Dictionary of sections
            
        Returns:
            Merged text
        """
        # Prioritize certain sections
        priority_sections = ['answer', 'response', 'main', 'summary']
        
        merged = []
        
        # Add priority sections first
        for section_name in priority_sections:
            if section_name in sections and sections[section_name]:
                merged.append(sections[section_name])
        
        # Add remaining sections
        for section_name, content in sections.items():
            if section_name not in priority_sections and content:
                merged.append(content)
        
        return '\n\n'.join(merged)
    
    def _extract_confidence(self, text: str) -> Optional[float]:
        """
        Extract confidence score if mentioned in text.
        
        Args:
            text: Response text
            
        Returns:
            Confidence score or None
        """
        # Look for confidence patterns
        confidence_patterns = [
            r'confidence:?\s*(\d+(?:\.\d+)?)\s*%',
            r'confidence:?\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*%\s*confident',
        ]
        
        for pattern in confidence_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1))
                    # Normalize to 0-1 range
                    if value > 1:
                        value = value / 100
                    return min(max(value, 0.0), 1.0)
                except ValueError:
                    continue
        
        return None
    
    def _extract_metadata(self, text: str) -> Dict[str, Any]:
        """
        Extract any metadata from the response.
        
        Args:
            text: Response text
            
        Returns:
            Metadata dictionary
        """
        metadata = {}
        
        # Extract word count
        words = text.split()
        metadata['word_count'] = len(words)
        
        # Check for specific markers
        if re.search(r'uncertain|not sure|unclear', text, re.IGNORECASE):
            metadata['uncertainty_detected'] = True
        
        if re.search(r'no information|not found|not available', text, re.IGNORECASE):
            metadata['no_answer_detected'] = True
        
        # Count citations
        citation_count = 0
        for pattern in self.citation_patterns:
            citation_count += len(pattern.findall(text))
        metadata['citation_count'] = citation_count
        
        return metadata
    
    def _resolve_citation_index(self, citation_id: str) -> Optional[int]:
        """
        Resolve citation ID to document index.
        
        Args:
            citation_id: Citation identifier (e.g., "1", "2")
            
        Returns:
            Zero-based document index or None
        """
        try:
            # Try to parse as integer
            index = int(citation_id) - 1  # Convert to 0-based
            return index
        except ValueError:
            # Handle special cases
            if citation_id.lower() in ['a', 'b', 'c', 'd', 'e']:
                return ord(citation_id.lower()) - ord('a')
            return None