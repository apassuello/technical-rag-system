"""
Vocabulary index for corpus-aware query enhancement.

Tracks all unique terms in the document corpus to enable intelligent
synonym expansion that only adds terms actually present in documents.
"""

from typing import Set, Dict, List, Optional
from collections import defaultdict
import re
from pathlib import Path
import json


class VocabularyIndex:
    """
    Maintains vocabulary statistics for intelligent query enhancement.
    
    Features:
    - Tracks all unique terms in document corpus
    - Stores term frequencies for relevance weighting
    - Identifies technical terms and domain vocabulary
    - Enables vocabulary-aware synonym expansion
    
    Performance: 
    - Build time: ~1s per 1000 chunks
    - Memory: ~3MB for 80K unique terms
    - Lookup: O(1) set operations
    """
    
    def __init__(self):
        """Initialize empty vocabulary index."""
        self.vocabulary: Set[str] = set()
        self.term_frequencies: Dict[str, int] = defaultdict(int)
        self.technical_terms: Set[str] = set()
        self.document_frequencies: Dict[str, int] = defaultdict(int)
        self.total_documents = 0
        self.total_terms = 0
        
        # Regex for term extraction
        self._term_pattern = re.compile(r'\b[a-zA-Z][a-zA-Z0-9\-_]*\b')
        self._technical_pattern = re.compile(r'\b[A-Z]{2,}|[a-zA-Z]+[\-_][a-zA-Z]+|\b\d+[a-zA-Z]+\b')
        
    def build_from_chunks(self, chunks: List[Dict]) -> None:
        """
        Build vocabulary index from document chunks.
        
        Args:
            chunks: List of document chunks with 'text' field
            
        Performance: ~1s per 1000 chunks
        """
        self.total_documents = len(chunks)
        
        for chunk in chunks:
            text = chunk.get('text', '')
            
            # Extract and process terms
            terms = self._extract_terms(text)
            unique_terms = set(terms)
            
            # Update vocabulary
            self.vocabulary.update(unique_terms)
            
            # Update frequencies
            for term in terms:
                self.term_frequencies[term] += 1
                self.total_terms += 1
            
            # Update document frequencies
            for term in unique_terms:
                self.document_frequencies[term] += 1
            
            # Identify technical terms
            technical = self._extract_technical_terms(text)
            self.technical_terms.update(technical)
    
    def _extract_terms(self, text: str) -> List[str]:
        """Extract normalized terms from text."""
        # Convert to lowercase and extract words
        text_lower = text.lower()
        terms = self._term_pattern.findall(text_lower)
        
        # Filter short terms
        return [term for term in terms if len(term) > 2]
    
    def _extract_technical_terms(self, text: str) -> Set[str]:
        """Extract technical terms (acronyms, hyphenated, etc)."""
        technical = set()
        
        # Find potential technical terms
        matches = self._technical_pattern.findall(text)
        
        for match in matches:
            # Normalize but preserve technical nature
            normalized = match.lower()
            if len(normalized) > 2:
                technical.add(normalized)
                
        return technical
    
    def contains(self, term: str) -> bool:
        """Check if term exists in vocabulary."""
        return term.lower() in self.vocabulary
    
    def get_frequency(self, term: str) -> int:
        """Get term frequency in corpus."""
        return self.term_frequencies.get(term.lower(), 0)
    
    def get_document_frequency(self, term: str) -> int:
        """Get number of documents containing term."""
        return self.document_frequencies.get(term.lower(), 0)
    
    def is_common_term(self, term: str, min_frequency: int = 5) -> bool:
        """Check if term appears frequently enough."""
        return self.get_frequency(term) >= min_frequency
    
    def is_technical_term(self, term: str) -> bool:
        """Check if term is identified as technical."""
        return term.lower() in self.technical_terms
    
    def filter_synonyms(self, synonyms: List[str], 
                       min_frequency: int = 3,
                       require_technical: bool = False) -> List[str]:
        """
        Filter synonym list to only include terms in vocabulary.
        
        Args:
            synonyms: List of potential synonyms
            min_frequency: Minimum term frequency required
            require_technical: Only include technical terms
            
        Returns:
            Filtered list of valid synonyms
        """
        valid_synonyms = []
        
        for synonym in synonyms:
            # Check existence
            if not self.contains(synonym):
                continue
                
            # Check frequency threshold
            if self.get_frequency(synonym) < min_frequency:
                continue
                
            # Check technical requirement
            if require_technical and not self.is_technical_term(synonym):
                continue
                
            valid_synonyms.append(synonym)
            
        return valid_synonyms
    
    def get_vocabulary_stats(self) -> Dict[str, any]:
        """Get comprehensive vocabulary statistics."""
        return {
            'unique_terms': len(self.vocabulary),
            'total_terms': self.total_terms,
            'technical_terms': len(self.technical_terms),
            'total_documents': self.total_documents,
            'avg_terms_per_doc': self.total_terms / self.total_documents if self.total_documents > 0 else 0,
            'vocabulary_richness': len(self.vocabulary) / self.total_terms if self.total_terms > 0 else 0,
            'technical_ratio': len(self.technical_terms) / len(self.vocabulary) if self.vocabulary else 0
        }
    
    def get_top_terms(self, n: int = 100, technical_only: bool = False) -> List[tuple]:
        """
        Get most frequent terms in corpus.
        
        Args:
            n: Number of top terms to return
            technical_only: Only return technical terms
            
        Returns:
            List of (term, frequency) tuples
        """
        if technical_only:
            term_freq = {
                term: freq for term, freq in self.term_frequencies.items()
                if term in self.technical_terms
            }
        else:
            term_freq = self.term_frequencies
            
        return sorted(term_freq.items(), key=lambda x: x[1], reverse=True)[:n]
    
    def detect_domain(self) -> str:
        """
        Detect document domain from vocabulary patterns.
        
        Returns:
            Detected domain name
        """
        # Domain detection heuristics
        domain_indicators = {
            'embedded_systems': ['microcontroller', 'rtos', 'embedded', 'firmware', 'mcu'],
            'processor_architecture': ['risc-v', 'riscv', 'instruction', 'register', 'isa'],
            'regulatory': ['fda', 'validation', 'compliance', 'regulation', 'guidance'],
            'ai_ml': ['model', 'training', 'neural', 'algorithm', 'machine learning'],
            'software_engineering': ['software', 'development', 'testing', 'debugging', 'code']
        }
        
        domain_scores = {}
        
        for domain, indicators in domain_indicators.items():
            score = sum(
                self.get_document_frequency(indicator) 
                for indicator in indicators
                if self.contains(indicator)
            )
            domain_scores[domain] = score
            
        # Return domain with highest score
        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
        return 'general'
    
    def save_to_file(self, path: Path) -> None:
        """Save vocabulary index to JSON file."""
        data = {
            'vocabulary': list(self.vocabulary),
            'term_frequencies': dict(self.term_frequencies),
            'technical_terms': list(self.technical_terms),
            'document_frequencies': dict(self.document_frequencies),
            'total_documents': self.total_documents,
            'total_terms': self.total_terms
        }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_from_file(self, path: Path) -> None:
        """Load vocabulary index from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
            
        self.vocabulary = set(data['vocabulary'])
        self.term_frequencies = defaultdict(int, data['term_frequencies'])
        self.technical_terms = set(data['technical_terms'])
        self.document_frequencies = defaultdict(int, data['document_frequencies'])
        self.total_documents = data['total_documents']
        self.total_terms = data['total_terms']
    
    def merge_with(self, other: 'VocabularyIndex') -> None:
        """Merge another vocabulary index into this one."""
        # Merge vocabularies
        self.vocabulary.update(other.vocabulary)
        self.technical_terms.update(other.technical_terms)
        
        # Merge frequencies
        for term, freq in other.term_frequencies.items():
            self.term_frequencies[term] += freq
            
        for term, doc_freq in other.document_frequencies.items():
            self.document_frequencies[term] += doc_freq
            
        # Update totals
        self.total_documents += other.total_documents
        self.total_terms += other.total_terms