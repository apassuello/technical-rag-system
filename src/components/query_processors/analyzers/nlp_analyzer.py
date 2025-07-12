"""
NLP-based Query Analyzer Implementation.

This module provides query analysis using spaCy NLP capabilities for
entity extraction, linguistic analysis, and advanced query understanding.

Features:
- Named entity recognition
- Technical term extraction
- Linguistic complexity analysis
- Intent classification
- Query optimization suggestions
"""

import logging
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
import sys

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from ..base import QueryAnalysis
from .base_analyzer import BaseQueryAnalyzer

logger = logging.getLogger(__name__)


class NLPAnalyzer(BaseQueryAnalyzer):
    """
    NLP-based query analyzer using spaCy for linguistic analysis.
    
    This analyzer provides advanced query understanding by leveraging
    spaCy's NLP capabilities including entity recognition, POS tagging,
    dependency parsing, and technical term identification.
    
    Configuration Options:
    - model: spaCy model name (default: "en_core_web_sm")
    - extract_entities: Enable named entity recognition (default: True)
    - extract_technical_terms: Enable technical term detection (default: True)
    - complexity_scoring: Enable complexity scoring (default: True)
    - min_confidence: Minimum confidence for entity extraction (default: 0.7)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize NLP analyzer with spaCy model.
        
        Args:
            config: Configuration dictionary
        """
        # Initialize attributes first before calling super().__init__
        self._nlp = None
        self._model_name = (config or {}).get('model', 'en_core_web_sm')
        self._extract_entities = (config or {}).get('extract_entities', True)
        self._extract_technical_terms = (config or {}).get('extract_technical_terms', True)
        self._complexity_scoring = (config or {}).get('complexity_scoring', True)
        self._min_confidence = (config or {}).get('min_confidence', 0.7)
        
        # Now call super().__init__ which may call configure()
        super().__init__(config)
        
        # Technical term patterns (can be extended via configuration)
        self._technical_patterns = set(self._config.get('technical_patterns', [
            'api', 'sdk', 'framework', 'library', 'protocol', 'algorithm',
            'implementation', 'architecture', 'design pattern', 'interface',
            'configuration', 'deployment', 'optimization', 'performance',
            'scalability', 'security', 'authentication', 'authorization',
            'database', 'query', 'index', 'cache', 'memory', 'cpu', 'processor',
            'network', 'http', 'tcp', 'udp', 'ssl', 'tls', 'json', 'xml',
            'yaml', 'markdown', 'regex', 'parse', 'serialize', 'encode',
            'decode', 'encrypt', 'decrypt', 'hash', 'token', 'session'
        ]))
        
        # Load spaCy model
        self._load_nlp_model()
    
    def _extract_basic_technical_terms(self, query: str) -> List[str]:
        """
        Extract technical terms using simple pattern matching when spaCy is not available.
        
        Args:
            query: Query string to analyze
            
        Returns:
            List of technical terms found
        """
        technical_terms = []
        query_lower = query.lower()
        
        # Check for individual technical patterns
        for pattern in self._technical_patterns:
            if pattern in query_lower:
                # Find the actual case-preserved term
                words = query.split()
                for word in words:
                    if word.lower() == pattern:
                        technical_terms.append(word)
                    elif pattern in word.lower():
                        technical_terms.append(word)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_terms = []
        for term in technical_terms:
            if term.lower() not in seen:
                seen.add(term.lower())
                unique_terms.append(term)
        
        return unique_terms
    
    def _load_nlp_model(self) -> None:
        """Load spaCy NLP model with error handling."""
        try:
            import spacy
            
            # Try to load the model
            try:
                self._nlp = spacy.load(self._model_name)
                logger.info(f"Loaded spaCy model: {self._model_name}")
            except OSError:
                # Fallback to basic English model
                logger.warning(f"Model {self._model_name} not found, trying en_core_web_sm")
                self._nlp = spacy.load("en_core_web_sm")
                self._model_name = "en_core_web_sm"
            
        except ImportError:
            logger.error("spaCy not available, NLP analysis will be limited")
            self._nlp = None
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")
            self._nlp = None
    
    def _analyze_query(self, query: str) -> QueryAnalysis:
        """
        Perform NLP-based query analysis.
        
        Args:
            query: Clean, validated query string
            
        Returns:
            QueryAnalysis with NLP-extracted characteristics
        """
        # Start with basic features
        basic_features = self._extract_basic_features(query)
        
        # Perform NLP analysis if available
        if self._nlp is not None:
            nlp_features = self._extract_nlp_features(query)
            basic_features.update(nlp_features)
        else:
            logger.warning("NLP model not available, using basic analysis only")
            # Add basic technical term extraction when spaCy is not available
            basic_features['technical_terms'] = self._extract_basic_technical_terms(query)
        
        # Extract query characteristics
        entities = basic_features.get('entities', [])
        technical_terms = basic_features.get('technical_terms', [])
        complexity_score = self._calculate_complexity_score(query, basic_features)
        intent_category = self._determine_intent_category(query, basic_features)
        suggested_k = self._suggest_retrieval_k(query, basic_features)
        confidence = self._calculate_confidence(basic_features)
        
        return QueryAnalysis(
            query=query,
            complexity_score=complexity_score,
            technical_terms=technical_terms,
            entities=entities,
            intent_category=intent_category,
            suggested_k=suggested_k,
            confidence=confidence,
            metadata={
                'analyzer_type': 'nlp',
                'model_used': self._model_name,
                'nlp_available': self._nlp is not None,
                'features': basic_features,
                'analysis_version': '1.0'
            }
        )
    
    def _extract_nlp_features(self, query: str) -> Dict[str, Any]:
        """
        Extract features using spaCy NLP analysis.
        
        Args:
            query: Query string to analyze
            
        Returns:
            Dictionary with NLP-extracted features
        """
        features = {}
        
        try:
            # Process query with spaCy
            doc = self._nlp(query)
            
            # Extract named entities
            if self._extract_entities:
                entities = []
                for ent in doc.ents:
                    if ent.label_ in ['PERSON', 'ORG', 'PRODUCT', 'TECHNOLOGY']:
                        entities.append({
                            'text': ent.text,
                            'label': ent.label_,
                            'confidence': getattr(ent, 'confidence', 1.0)
                        })
                
                features['entities'] = [e['text'] for e in entities if e['confidence'] >= self._min_confidence]
                features['entity_details'] = entities
            
            # Extract technical terms
            if self._extract_technical_terms:
                technical_terms = self._extract_technical_terms_from_doc(doc)
                features['technical_terms'] = technical_terms
            
            # Linguistic analysis
            features['pos_tags'] = [token.pos_ for token in doc]
            features['dependencies'] = [(token.text, token.dep_, token.head.text) for token in doc]
            
            # Complexity indicators
            features['avg_word_length'] = sum(len(token.text) for token in doc if token.is_alpha) / max(1, sum(1 for token in doc if token.is_alpha))
            features['noun_count'] = sum(1 for token in doc if token.pos_ == 'NOUN')
            features['verb_count'] = sum(1 for token in doc if token.pos_ == 'VERB')
            features['adj_count'] = sum(1 for token in doc if token.pos_ == 'ADJ')
            
            # Sentence structure
            features['sentence_structures'] = []
            for sent in doc.sents:
                features['sentence_structures'].append({
                    'length': len([token for token in sent if token.is_alpha]),
                    'complexity': self._analyze_sentence_complexity(sent)
                })
            
        except Exception as e:
            logger.warning(f"NLP feature extraction failed: {e}")
            features['nlp_error'] = str(e)
        
        return features
    
    def _extract_technical_terms_from_doc(self, doc) -> List[str]:
        """
        Extract technical terms from spaCy document.
        
        Args:
            doc: spaCy document object
            
        Returns:
            List of technical terms found
        """
        technical_terms = []
        
        # Check individual tokens
        for token in doc:
            if token.text.lower() in self._technical_patterns:
                technical_terms.append(token.text)
        
        # Check noun phrases for multi-word technical terms
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.lower()
            if any(pattern in chunk_text for pattern in self._technical_patterns):
                technical_terms.append(chunk.text)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_terms = []
        for term in technical_terms:
            if term.lower() not in seen:
                seen.add(term.lower())
                unique_terms.append(term)
        
        return unique_terms
    
    def _analyze_sentence_complexity(self, sent) -> str:
        """
        Analyze complexity of a single sentence.
        
        Args:
            sent: spaCy sentence object
            
        Returns:
            Complexity level: 'simple', 'medium', 'complex'
        """
        # Count syntactic features
        word_count = len([token for token in sent if token.is_alpha])
        clause_count = sum(1 for token in sent if token.dep_ in ['ccomp', 'xcomp', 'advcl'])
        subordinate_count = sum(1 for token in sent if token.dep_ in ['mark', 'prep'])
        
        # Determine complexity
        if word_count < 8 and clause_count == 0:
            return 'simple'
        elif word_count < 15 and clause_count <= 1:
            return 'medium'
        else:
            return 'complex'
    
    def _calculate_complexity_score(self, query: str, features: Dict[str, Any]) -> float:
        """
        Calculate numerical complexity score for the query.
        
        Args:
            query: Original query string
            features: Extracted features
            
        Returns:
            Complexity score between 0.0 and 1.0
        """
        if not self._complexity_scoring:
            return 0.5  # Default medium complexity
        
        score = 0.0
        
        # Word count factor (0.0 - 0.3)
        word_count = features.get('word_count', 0)
        word_factor = min(0.3, word_count / 20.0)
        score += word_factor
        
        # Technical terms factor (0.0 - 0.2)
        tech_terms = len(features.get('technical_terms', []))
        tech_factor = min(0.2, tech_terms / 5.0)
        score += tech_factor
        
        # Entity count factor (0.0 - 0.2)
        entities = len(features.get('entities', []))
        entity_factor = min(0.2, entities / 3.0)
        score += entity_factor
        
        # Linguistic complexity factor (0.0 - 0.3)
        if 'avg_word_length' in features:
            avg_word_len = features['avg_word_length']
            length_factor = min(0.15, (avg_word_len - 4.0) / 10.0) if avg_word_len > 4.0 else 0.0
            score += length_factor
        
        if 'sentence_structures' in features:
            complex_sentences = sum(1 for s in features['sentence_structures'] if s['complexity'] == 'complex')
            structure_factor = min(0.15, complex_sentences / 2.0)
            score += structure_factor
        
        return min(1.0, max(0.0, score))
    
    def _calculate_confidence(self, features: Dict[str, Any]) -> float:
        """
        Calculate confidence in the analysis results.
        
        Args:
            features: Extracted features
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.5  # Base confidence
        
        # Higher confidence if NLP model worked
        if self._nlp is not None and 'nlp_error' not in features:
            confidence += 0.3
        
        # Higher confidence for queries with clear characteristics
        if features.get('technical_terms'):
            confidence += 0.1
        
        if features.get('entities'):
            confidence += 0.1
        
        if features.get('has_question_words'):
            confidence += 0.1
        
        return min(1.0, max(0.0, confidence))
    
    def get_supported_features(self) -> List[str]:
        """
        Return list of features this NLP analyzer supports.
        
        Returns:
            List of feature names
        """
        base_features = super().get_supported_features()
        nlp_features = [
            'entities',
            'technical_terms', 
            'complexity_scoring',
            'intent_classification',
            'linguistic_analysis',
            'pos_tagging',
            'dependency_parsing'
        ]
        
        if self._nlp is None:
            nlp_features = ['basic_' + feature for feature in nlp_features]
        
        return base_features + nlp_features
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the NLP analyzer with provided settings.
        
        Args:
            config: Configuration dictionary
        """
        super().configure(config)
        
        # Update NLP-specific configuration
        old_model = self._model_name
        self._model_name = config.get('model', self._model_name)
        self._extract_entities = config.get('extract_entities', self._extract_entities)
        self._extract_technical_terms = config.get('extract_technical_terms', self._extract_technical_terms)
        self._complexity_scoring = config.get('complexity_scoring', self._complexity_scoring)
        self._min_confidence = config.get('min_confidence', self._min_confidence)
        
        # Update technical patterns if provided
        if 'technical_patterns' in config:
            additional_patterns = config['technical_patterns']
            if isinstance(additional_patterns, list):
                self._technical_patterns.update(additional_patterns)
        
        # Reload model if changed
        if old_model != self._model_name:
            logger.info(f"Model changed from {old_model} to {self._model_name}, reloading...")
            self._load_nlp_model()