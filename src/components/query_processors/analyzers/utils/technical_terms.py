"""
Technical Term Manager for Epic 1 Query Analysis.

This module manages domain-specific technical vocabulary used to assess
query complexity and determine appropriate model routing.

Architecture Notes:
- Direct implementation (no external dependencies)
- Configurable vocabulary sets
- Efficient lookup using sets and tries
- Extensible for multiple domains
"""

import logging
from typing import Set, Dict, List, Optional
from pathlib import Path
import json
import re

logger = logging.getLogger(__name__)


class TrieNode:
    """Node in a trie data structure for efficient term lookup."""
    
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.term_info = None  # Can store additional metadata


class TechnicalTermManager:
    """
    Manages domain-specific technical vocabulary for complexity analysis.
    
    Features:
    - Efficient term lookup using trie data structure
    - Multi-domain vocabulary support
    - Configurable term loading from files
    - Term density calculation
    - Pattern matching for technical formats
    
    Configuration:
    - terms_file: Path to JSON file with technical terms
    - domains: List of domains to include (ml, engineering, rag, etc.)
    - min_term_length: Minimum length for term recognition
    """
    
    # Default technical terms by domain
    DEFAULT_TERMS = {
        'ml': {
            'embedding', 'vector', 'transformer', 'neural', 'gradient',
            'backpropagation', 'optimizer', 'hyperparameter', 'epoch',
            'batch', 'tensor', 'activation', 'dropout', 'regularization',
            'overfitting', 'underfitting', 'cross-validation', 'fine-tuning',
            'attention', 'encoder', 'decoder', 'lstm', 'gru', 'cnn', 'rnn'
        },
        'engineering': {
            'latency', 'throughput', 'scalability', 'pipeline', 'architecture',
            'microservice', 'api', 'endpoint', 'cache', 'database', 'queue',
            'async', 'synchronous', 'concurrency', 'parallelization',
            'optimization', 'performance', 'bottleneck', 'profiling',
            'deployment', 'container', 'orchestration', 'kubernetes', 'docker'
        },
        'rag': {
            'retrieval', 'generation', 'chunking', 'reranking', 'similarity',
            'semantic', 'lexical', 'dense', 'sparse', 'hybrid', 'fusion',
            'context', 'prompt', 'completion', 'augmentation', 'grounding',
            'hallucination', 'citation', 'relevance', 'precision', 'recall',
            'faiss', 'pinecone', 'weaviate', 'chromadb', 'langchain'
        },
        'llm': {
            'token', 'tokenization', 'context', 'temperature', 'top-p',
            'top-k', 'beam', 'greedy', 'sampling', 'logit', 'perplexity',
            'few-shot', 'zero-shot', 'chain-of-thought', 'reasoning',
            'instruction', 'alignment', 'rlhf', 'constitutional', 'safety'
        }
    }
    
    # Technical patterns (regex)
    TECHNICAL_PATTERNS = [
        r'\b[A-Z]{2,}\b',  # Acronyms (API, LLM, etc.)
        r'\b\w+_\w+\b',    # Snake_case terms
        r'\b\w+\.\w+\b',   # Dotted notation (model.fit, etc.)
        r'\b\d+[kKmMgG][bB]?\b',  # Memory/size notation (16GB, 512MB)
        r'\bv?\d+\.\d+\b',  # Version numbers (v1.0, 2.5)
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize technical term manager.
        
        Args:
            config: Configuration dictionary with:
                - terms_file: Path to custom terms file
                - domains: List of domains to include
                - min_term_length: Minimum term length (default: 3)
                - case_sensitive: Whether to match case (default: False)
        """
        self.config = config or {}
        self.min_term_length = self.config.get('min_term_length', 3)
        self.case_sensitive = self.config.get('case_sensitive', False)
        
        # Initialize term storage
        self.terms: Set[str] = set()
        self.domain_terms: Dict[str, Set[str]] = {}
        self.trie = TrieNode()
        
        # Load terms
        self._load_default_terms()
        self._load_custom_terms()
        self._build_trie()
        
        # Compile patterns
        self.technical_patterns = [
            re.compile(pattern) for pattern in self.TECHNICAL_PATTERNS
        ]
        
        logger.info(f"Initialized TechnicalTermManager with {len(self.terms)} terms")
    
    def _load_default_terms(self) -> None:
        """Load default technical terms based on configured domains."""
        domains = self.config.get('domains', ['ml', 'rag', 'llm'])
        
        for domain in domains:
            if domain in self.DEFAULT_TERMS:
                domain_terms = self.DEFAULT_TERMS[domain]
                if not self.case_sensitive:
                    domain_terms = {term.lower() for term in domain_terms}
                self.domain_terms[domain] = domain_terms
                self.terms.update(domain_terms)
                logger.debug(f"Loaded {len(domain_terms)} terms for domain: {domain}")
    
    def _load_custom_terms(self) -> None:
        """Load custom terms from configuration file."""
        terms_file = self.config.get('terms_file')
        if not terms_file:
            return
        
        terms_path = Path(terms_file)
        if not terms_path.exists():
            logger.warning(f"Terms file not found: {terms_file}")
            return
        
        try:
            with open(terms_path, 'r') as f:
                custom_terms = json.load(f)
            
            # Handle different file formats
            if isinstance(custom_terms, list):
                # Simple list of terms
                terms = set(custom_terms)
                if not self.case_sensitive:
                    terms = {term.lower() for term in terms}
                self.terms.update(terms)
                self.domain_terms['custom'] = terms
            elif isinstance(custom_terms, dict):
                # Domain-organized terms
                for domain, terms in custom_terms.items():
                    if not self.case_sensitive:
                        terms = {term.lower() for term in terms}
                    self.domain_terms[domain] = terms
                    self.terms.update(terms)
            
            logger.info(f"Loaded custom terms from {terms_file}")
            
        except Exception as e:
            logger.error(f"Failed to load custom terms: {e}")
    
    def _build_trie(self) -> None:
        """Build trie data structure for efficient term lookup."""
        for term in self.terms:
            self._insert_trie(term)
    
    def _insert_trie(self, term: str) -> None:
        """Insert a term into the trie."""
        node = self.trie
        for char in term:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True
        node.term_info = {'original': term}
    
    def contains_term(self, word: str) -> bool:
        """
        Check if a word is a technical term.
        
        Args:
            word: Word to check
            
        Returns:
            True if word is a technical term
        """
        if len(word) < self.min_term_length:
            return False
        
        check_word = word if self.case_sensitive else word.lower()
        
        # Check trie
        node = self.trie
        for char in check_word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end
    
    def extract_terms(self, text: str) -> List[str]:
        """
        Extract all technical terms from text.
        
        Args:
            text: Input text
            
        Returns:
            List of technical terms found
        """
        # Tokenize text
        words = re.findall(r'\b[\w\-\.]+\b', text)
        
        found_terms = []
        for word in words:
            if self.contains_term(word):
                found_terms.append(word)
        
        # Also check for pattern-based terms
        for pattern in self.technical_patterns:
            matches = pattern.findall(text)
            found_terms.extend(matches)
        
        return found_terms
    
    def calculate_density(self, text: str) -> float:
        """
        Calculate technical term density in text.
        
        Args:
            text: Input text
            
        Returns:
            Ratio of technical terms to total words (0.0 to 1.0)
        """
        words = re.findall(r'\b[\w\-\.]+\b', text)
        if not words:
            return 0.0
        
        technical_count = sum(1 for word in words if self.contains_term(word))
        
        # Add pattern matches
        for pattern in self.technical_patterns:
            matches = pattern.findall(text)
            technical_count += len(matches)
        
        # Cap at 1.0 in case of overlaps
        density = min(1.0, technical_count / len(words))
        return density
    
    def get_domain_scores(self, text: str) -> Dict[str, float]:
        """
        Calculate term density for each domain.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary mapping domain to density score
        """
        words = re.findall(r'\b[\w\-\.]+\b', text)
        if not words:
            return {domain: 0.0 for domain in self.domain_terms}
        
        check_words = words if self.case_sensitive else [w.lower() for w in words]
        
        domain_scores = {}
        for domain, terms in self.domain_terms.items():
            count = sum(1 for word in check_words if word in terms)
            domain_scores[domain] = count / len(words)
        
        return domain_scores
    
    def is_technical_query(self, text: str, threshold: float = 0.15) -> bool:
        """
        Determine if query has significant technical content.
        
        Args:
            text: Query text
            threshold: Minimum density to be considered technical
            
        Returns:
            True if query is technical
        """
        density = self.calculate_density(text)
        return density >= threshold
    
    def get_statistics(self) -> Dict[str, any]:
        """Get statistics about loaded terms."""
        return {
            'total_terms': len(self.terms),
            'domains': list(self.domain_terms.keys()),
            'terms_per_domain': {
                domain: len(terms) 
                for domain, terms in self.domain_terms.items()
            },
            'min_term_length': self.min_term_length,
            'case_sensitive': self.case_sensitive
        }