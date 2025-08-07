"""
Rule-based technical term classifier.

Implements pattern and dictionary-based technical term classification with
categorized vocabulary and complexity weighting.
"""

import re
import logging
from typing import Dict, List, Any, Set
from pathlib import Path

from ..base import TermClassifier, TermClassificationResult

logger = logging.getLogger(__name__)


class RuleBasedTermClassifier(TermClassifier):
    """
    Rule-based implementation of technical term classification.
    
    Uses categorized dictionaries and patterns to identify technical terms
    and assign complexity weights based on domain sophistication.
    """
    
    # Expanded technical vocabulary organized by complexity
    DEFAULT_TERM_CATEGORIES = {
        'basic_technical': {
            'weight': 1.0,
            'description': 'Basic technical terms',
            'terms': [
                # Basic computing terms
                'instruction', 'memory', 'register', 'address', 'data', 'bit', 'byte',
                'processor', 'cpu', 'cache', 'pipeline', 'branch', 'jump', 'load', 'store',
                'stack', 'heap', 'buffer', 'pointer', 'array', 'function', 'method',
                'variable', 'parameter', 'argument', 'return', 'call', 'execution',
                
                # Basic RISC-V terms  
                'risc', 'architecture', 'isa', 'instruction', 'format', 'encoding',
                'opcode', 'immediate', 'offset', 'displacement',
                
                # Basic system terms
                'hardware', 'software', 'system', 'interface', 'protocol', 'standard',
                'specification', 'implementation', 'design', 'development'
            ]
        },
        
        'advanced_technical': {
            'weight': 1.5,
            'description': 'Advanced technical terms',
            'terms': [
                # Advanced architecture terms
                'optimization', 'speculation', 'prediction', 'superscalar', 'pipeline',
                'hazard', 'forwarding', 'stall', 'bubble', 'latency', 'throughput',
                'bandwidth', 'parallelism', 'concurrency', 'synchronization',
                'virtualization', 'hypervisor', 'privileged', 'unprivileged',
                'exception', 'interrupt', 'trap', 'fault', 'abort',
                
                # Advanced RISC-V terms
                'vector', 'extension', 'simd', 'vlen', 'elen', 'sew', 'lmul',
                'atomic', 'amo', 'lr', 'sc', 'fence', 'ordering', 'consistency',
                'compressed', 'quadrant', 'immediate', 'displacement',
                
                # Performance terms
                'performance', 'efficiency', 'scalability', 'bottleneck',
                'profiling', 'benchmarking', 'measurement', 'analysis',
                'compilation', 'compiler', 'toolchain', 'linker', 'assembler'
            ]
        },
        
        'research_terms': {
            'weight': 2.0,
            'description': 'Research and analysis terms',
            'terms': [
                # Research methodology
                'research', 'analysis', 'evaluation', 'assessment', 'study',
                'investigation', 'exploration', 'survey', 'review', 'comparison',
                'methodology', 'approach', 'technique', 'strategy', 'framework',
                'model', 'simulation', 'modeling', 'characterization',
                
                # Academic terms
                'hypothesis', 'experiment', 'validation', 'verification',
                'empirical', 'theoretical', 'analytical', 'quantitative', 'qualitative',
                'metrics', 'measurement', 'benchmark', 'baseline', 'correlation',
                'regression', 'classification', 'clustering', 'optimization',
                
                # Advanced concepts
                'trade-off', 'implications', 'considerations', 'challenges',
                'limitations', 'advantages', 'disadvantages', 'benefits', 'costs',
                'requirements', 'constraints', 'assumptions', 'objectives'
            ]
        },
        
        'domain_specific': {
            'weight': 1.3,
            'description': 'Domain-specific technical terms',
            'terms': [
                # Medical device terms  
                'validation', 'verification', 'fda', 'regulation', 'compliance',
                'safety', 'security', 'reliability', 'quality', 'assurance',
                'testing', 'documentation', 'traceability', 'risk', 'hazard',
                'medical', 'device', 'pharmaceutical', 'clinical', 'patient',
                
                # AI/ML terms
                'ai', 'ml', 'artificial', 'intelligence', 'machine', 'learning',
                'neural', 'network', 'deep', 'model', 'training', 'inference',
                'algorithm', 'classification', 'regression', 'clustering',
                'supervised', 'unsupervised', 'reinforcement', 'embedding',
                
                # Signal processing
                'signal', 'processing', 'filter', 'frequency', 'amplitude',
                'phase', 'transform', 'convolution', 'correlation', 'noise'
            ]
        },
        
        'operational_terms': {
            'weight': 1.1,
            'description': 'Operational and procedural terms',  
            'terms': [
                # Operational terms
                'configure', 'setup', 'install', 'deploy', 'maintain',
                'monitor', 'debug', 'troubleshoot', 'diagnose', 'fix',
                'update', 'upgrade', 'migrate', 'integrate', 'interface',
                'compatibility', 'interoperability', 'portability',
                
                # Process terms
                'process', 'workflow', 'pipeline', 'stage', 'phase',
                'step', 'procedure', 'protocol', 'methodology', 'practice',
                'guidelines', 'standards', 'best', 'practices', 'recommendations'
            ]
        }
    }
    
    # Acronym patterns that should be considered technical
    TECHNICAL_ACRONYM_PATTERNS = [
        r'\b[A-Z]{2,6}\b',  # 2-6 uppercase letters (CPU, RISC, SIMD, etc.)
        r'\b[A-Z][0-9]+\b',  # Letter followed by numbers (I32, F64, etc.)
    ]
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize rule-based term classifier."""
        super().__init__(config)
        
        # Load term categories from config or use defaults
        self.term_categories = self.config.get('categories', self.DEFAULT_TERM_CATEGORIES.copy())
        
        # Build lookup structures for efficient classification
        self._build_lookup_structures()
        
        # Compile acronym patterns
        self.acronym_patterns = [re.compile(pattern, re.IGNORECASE) 
                                for pattern in self.TECHNICAL_ACRONYM_PATTERNS]
        
        logger.info(f"Initialized RuleBasedTermClassifier with {len(self.term_categories)} categories")
        total_terms = sum(len(cat['terms']) for cat in self.term_categories.values())
        logger.debug(f"Total vocabulary size: {total_terms} terms")
    
    def _build_lookup_structures(self):
        """Build efficient lookup structures for term classification."""
        self.term_to_category = {}
        self.term_to_weight = {}
        self.all_technical_terms = set()
        
        for category_name, category_data in self.term_categories.items():
            weight = category_data['weight']
            terms = category_data['terms']
            
            for term in terms:
                term_lower = term.lower()
                self.term_to_category[term_lower] = category_name
                self.term_to_weight[term_lower] = weight
                self.all_technical_terms.add(term_lower)
    
    def classify_terms(self, text: str) -> TermClassificationResult:
        """
        Classify technical terms in the given text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            TermClassificationResult with classified terms and scores
        """
        # Normalize text for analysis
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        # Find technical terms
        found_terms = []
        term_categories = {}
        term_weights = {}
        
        # Dictionary-based term detection
        for word in words:
            if word in self.all_technical_terms:
                found_terms.append(word)
                category = self.term_to_category[word]
                weight = self.term_to_weight[word]
                
                if category not in term_categories:
                    term_categories[category] = []
                term_categories[category].append(word)
                term_weights[word] = weight
        
        # Pattern-based detection (acronyms, technical patterns)
        for pattern in self.acronym_patterns:
            matches = pattern.findall(text)
            for match in matches:
                match_lower = match.lower()
                if match_lower not in found_terms and len(match) >= 2:
                    found_terms.append(match_lower)
                    # Assign to basic_technical category with reduced weight
                    if 'basic_technical' not in term_categories:
                        term_categories['basic_technical'] = []
                    term_categories['basic_technical'].append(match_lower)
                    term_weights[match_lower] = 0.8  # Lower weight for pattern matches
        
        # Calculate scores
        total_words = len(words) if words else 1
        density = len(found_terms) / total_words
        
        # Calculate weighted total score
        total_score = sum(term_weights.values()) / total_words if term_weights else 0.0
        
        # Normalize total score to reasonable range (0-1)
        total_score = min(total_score, 1.0)
        
        return TermClassificationResult(
            technical_terms=found_terms,
            term_categories=term_categories,
            term_weights=term_weights,
            total_score=total_score,
            density=density,
            metadata={
                'total_words': total_words,
                'categories_found': list(term_categories.keys()),
                'category_counts': {cat: len(terms) for cat, terms in term_categories.items()}
            }
        )
    
    def get_term_categories(self) -> Dict[str, Dict[str, Any]]:
        """Get available term categories and their properties."""
        return self.term_categories.copy()
    
    def is_technical_term(self, term: str) -> bool:
        """Check if a term is considered technical."""
        term_lower = term.lower()
        if term_lower in self.all_technical_terms:
            return True
        
        # Check against patterns
        for pattern in self.acronym_patterns:
            if pattern.match(term):
                return True
        
        return False
    
    def get_category_weight(self, category: str) -> float:
        """Get the weight for a specific category."""
        return self.term_categories.get(category, {}).get('weight', 1.0)
    
    def add_terms(self, category: str, terms: List[str], weight: float = None):
        """Add terms to an existing category or create a new one."""
        if category not in self.term_categories:
            self.term_categories[category] = {
                'weight': weight or 1.0,
                'description': f'Custom category: {category}',
                'terms': []
            }
        
        # Add new terms
        existing_terms = set(self.term_categories[category]['terms'])
        new_terms = [term for term in terms if term not in existing_terms]
        self.term_categories[category]['terms'].extend(new_terms)
        
        # Rebuild lookup structures
        self._build_lookup_structures()
        
        logger.info(f"Added {len(new_terms)} terms to category '{category}'")