"""
Feature Extractor for Epic 1 Query Analysis.

This module extracts comprehensive linguistic and structural features
from queries to enable accurate complexity classification and model routing.

Architecture Notes:
- Direct implementation (no external dependencies)
- Modular feature extraction methods
- Optimized for <50ms performance
- Configurable feature sets
"""

import re
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from ..utils import TechnicalTermManager, SyntacticParser

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    Extracts linguistic and structural features from queries.
    
    This sub-component performs comprehensive feature extraction
    for Epic 1 query complexity analysis, including:
    - Length-based features
    - Syntactic complexity features
    - Vocabulary/technical term features
    - Question type classification
    - Entity-like pattern detection
    - Ambiguity indicators
    
    All features are normalized to 0.0-1.0 range for consistent classification.
    """
    
    # Common question words for classification
    QUESTION_WORDS = {
        'what', 'how', 'why', 'when', 'where', 'who', 'which',
        'whose', 'whom', 'whether', 'can', 'could', 'should',
        'would', 'will', 'does', 'do', 'did', 'is', 'are', 'was', 'were'
    }
    
    # Ambiguity indicators
    AMBIGUOUS_TERMS = {
        'it', 'this', 'that', 'these', 'those', 'they', 'them',
        'something', 'someone', 'somewhere', 'somehow', 'sometime',
        'anything', 'anyone', 'anywhere', 'stuff', 'thing',
        'maybe', 'perhaps', 'possibly', 'might', 'could be'
    }
    
    # Entity patterns (simplified without NLP)
    ENTITY_PATTERNS = [
        r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b',  # Proper names
        r'\b[A-Z]{2,}\b',  # Acronyms
        r'\b\d{4}\b',  # Years
        r'\b\d+(?:\.\d+)?%\b',  # Percentages
        r'\$\d+(?:\.\d+)?[MBK]?\b',  # Money amounts
        r'\b\d+(?:\.\d+)?[kKmMgGtT][bB]?\b',  # Data sizes
        r'\bv?\d+\.\d+(?:\.\d+)?\b',  # Version numbers
    ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize feature extractor.
        
        Args:
            config: Configuration dictionary with:
                - technical_terms_file: Path to technical vocabulary
                - enable_entity_extraction: Whether to extract entities
                - feature_weights: Weights for different feature categories
                - normalization_params: Parameters for feature normalization
        """
        self.config = config or {}
        
        # Initialize utilities
        self.technical_terms = TechnicalTermManager(
            self.config.get('technical_terms', {})
        )
        self.syntactic_parser = SyntacticParser(
            self.config.get('syntactic_parser', {})
        )
        
        # Compile entity patterns
        self.entity_patterns = [
            re.compile(pattern) for pattern in self.ENTITY_PATTERNS
        ]
        
        # Feature configuration
        self.enable_entities = self.config.get('enable_entity_extraction', True)
        self.normalization_params = self.config.get('normalization_params', {
            'max_words': 50,
            'max_chars': 300,
            'max_entities': 10,
            'max_technical_terms': 15
        })
        
        logger.info("Initialized FeatureExtractor for Epic 1 analysis")
    
    def extract(self, query: str) -> Dict[str, Any]:
        """
        Extract all features from query.
        
        Args:
            query: Input query string
            
        Returns:
            Dictionary containing all extracted features organized by category
        """
        # Clean and prepare query
        query = query.strip()
        
        # Extract different feature categories
        features = {
            'raw_query': query,
            'length_features': self._extract_length_features(query),
            'syntactic_features': self._extract_syntactic_features(query),
            'vocabulary_features': self._extract_vocabulary_features(query),
            'question_features': self._extract_question_features(query),
            'entity_features': self._extract_entity_features(query) if self.enable_entities else {},
            'ambiguity_features': self._extract_ambiguity_features(query),
            'structural_features': self._extract_structural_features(query)
        }
        
        # Add composite features
        features['composite_features'] = self._calculate_composite_features(features)
        
        return features
    
    def _extract_length_features(self, query: str) -> Dict[str, float]:
        """
        Extract length-based features.
        
        Args:
            query: Input query
            
        Returns:
            Dictionary of normalized length features
        """
        words = query.split()
        chars = len(query)
        
        # Estimate tokens (rough approximation)
        # Average English word is ~4-5 chars, tokens are ~3-4 chars
        token_estimate = chars / 3.5
        
        return {
            'word_count': len(words),
            'char_count': chars,
            'token_estimate': token_estimate,
            'avg_word_length': chars / max(1, len(words)),
            # Normalized versions (0-1)
            'word_count_norm': min(1.0, len(words) / self.normalization_params['max_words']),
            'char_count_norm': min(1.0, chars / self.normalization_params['max_chars']),
            'is_long_query': 1.0 if len(words) > 20 else 0.0,
            'is_very_long_query': 1.0 if len(words) > 40 else 0.0
        }
    
    def _extract_syntactic_features(self, query: str) -> Dict[str, float]:
        """
        Extract syntactic complexity features.
        
        Args:
            query: Input query
            
        Returns:
            Dictionary of syntactic features
        """
        # Use syntactic parser utility
        analysis = self.syntactic_parser.analyze_complexity(query)
        features = self.syntactic_parser.get_complexity_features(query)
        
        return {
            'clause_count': analysis['clause_count'],
            'nesting_depth': analysis['nesting_depth'],
            'conjunction_count': analysis['conjunction_count'],
            'sentence_count': analysis['sentence_count'],
            'avg_sentence_length': analysis['avg_sentence_length'],
            'has_comparison': 1.0 if analysis['has_comparison'] else 0.0,
            'has_enumeration': 1.0 if analysis['has_enumeration'] else 0.0,
            'parenthetical_depth': analysis['parenthetical_depth'],
            # Normalized syntactic score
            'syntactic_complexity': features['syntactic_score'],
            # Additional normalized features
            'clause_density': features['clause_density'],
            'nesting_norm': features['nesting_depth_norm'],
            'conjunction_density': features['conjunction_density']
        }
    
    def _extract_vocabulary_features(self, query: str) -> Dict[str, Any]:
        """
        Extract vocabulary and technical term features.
        
        Args:
            query: Input query
            
        Returns:
            Dictionary of vocabulary features
        """
        # Extract technical terms
        technical_terms = self.technical_terms.extract_terms(query)
        technical_density = self.technical_terms.calculate_density(query)
        domain_scores = self.technical_terms.get_domain_scores(query)
        is_technical = self.technical_terms.is_technical_query(query)
        
        # Calculate vocabulary richness
        words = re.findall(r'\b\w+\b', query.lower())
        unique_words = set(words)
        vocabulary_richness = len(unique_words) / max(1, len(words))
        
        return {
            'technical_terms': technical_terms,
            'technical_term_count': len(technical_terms),
            'technical_density': technical_density,
            'is_technical_query': 1.0 if is_technical else 0.0,
            'domain_scores': domain_scores,
            'vocabulary_richness': vocabulary_richness,
            'unique_word_ratio': vocabulary_richness,
            # Normalized counts
            'technical_term_norm': min(1.0, len(technical_terms) / self.normalization_params['max_technical_terms']),
            # Domain-specific flags
            'is_ml_heavy': 1.0 if domain_scores.get('ml', 0) > 0.2 else 0.0,
            'is_engineering_heavy': 1.0 if domain_scores.get('engineering', 0) > 0.2 else 0.0,
            'is_rag_specific': 1.0 if domain_scores.get('rag', 0) > 0.15 else 0.0
        }
    
    def _extract_question_features(self, query: str) -> Dict[str, float]:
        """
        Extract question type and structure features.
        
        Args:
            query: Input query
            
        Returns:
            Dictionary of question features
        """
        query_lower = query.lower().strip()
        words = query_lower.split()
        
        # Classify question type
        question_type = self.syntactic_parser._classify_question_type(query)
        
        # Question complexity by type
        type_complexity_map = {
            'what': 0.2,      # Simple factual
            'when': 0.2,      # Simple temporal
            'where': 0.2,     # Simple location
            'who': 0.2,       # Simple identification
            'how': 0.5,       # Process/mechanism
            'why': 0.6,       # Reasoning required
            'compare': 0.8,   # Analysis required
            'implement': 0.9, # Action/creation required
            'explain': 0.7,   # Explanation required
            'list': 0.3,      # Enumeration
            'statement': 0.3, # Not a question
            'other_question': 0.4, # Unknown question type
        }
        type_complexity = type_complexity_map.get(question_type, 0.3)
        
        # Complex question indicators
        complex_indicators = [
            'compare', 'contrast', 'analyze', 'evaluate', 'implement',
            'optimize', 'design', 'develop', 'assess', 'determine'
        ]
        is_complex = any(indicator in query_lower for indicator in complex_indicators)
        
        # Check for specific question patterns
        features = {
            'question_type': question_type,
            'type_complexity': type_complexity,
            'is_complex_question': 1.0 if is_complex else 0.0,
            'is_question': 1.0 if query.strip().endswith('?') else 0.0,
            'starts_with_question_word': 1.0 if words and words[0] in self.QUESTION_WORDS else 0.0,
            # Question complexity indicators
            'is_how_to': 1.0 if 'how to' in query_lower else 0.0,
            'is_what_is': 1.0 if query_lower.startswith('what is') else 0.0,
            'is_comparison': 1.0 if any(w in query_lower for w in ['compare', 'difference', 'vs', 'versus']) else 0.0,
            'is_explanation': 1.0 if any(w in query_lower for w in ['explain', 'describe', 'elaborate']) else 0.0,
            'is_listing': 1.0 if any(w in query_lower for w in ['list', 'enumerate', 'name all']) else 0.0,
            'is_implementation': 1.0 if any(w in query_lower for w in ['implement', 'create', 'build', 'develop']) else 0.0,
            'is_debugging': 1.0 if any(w in query_lower for w in ['debug', 'fix', 'error', 'issue', 'problem']) else 0.0,
            'is_optimization': 1.0 if any(w in query_lower for w in ['optimize', 'improve', 'enhance', 'speed up']) else 0.0,
            # Multi-part question
            'has_multiple_questions': 1.0 if query.count('?') > 1 else 0.0,
            'has_subquestions': 1.0 if any(w in query_lower for w in ['also', 'additionally', 'furthermore', 'and also']) else 0.0
        }
        
        # Calculate question complexity score (combining type and indicators)
        complexity_indicators = [
            features['is_comparison'],
            features['is_explanation'],
            features['is_implementation'],
            features['is_optimization'],
            features['has_multiple_questions'],
            features['has_subquestions']
        ]
        indicator_score = sum(complexity_indicators) / len(complexity_indicators)
        features['question_complexity'] = max(type_complexity, indicator_score)
        
        return features
    
    def _extract_entity_features(self, query: str) -> Dict[str, Any]:
        """
        Extract entity-like patterns from query.
        
        Args:
            query: Input query
            
        Returns:
            Dictionary of entity features
        """
        entities = []
        
        # Extract using patterns
        for pattern in self.entity_patterns:
            matches = pattern.findall(query)
            entities.extend(matches)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity not in seen:
                seen.add(entity)
                unique_entities.append(entity)
        
        return {
            'entities': unique_entities,
            'entity_count': len(unique_entities),
            'entity_density': len(unique_entities) / max(1, len(query.split())),
            # Normalized
            'entity_count_norm': min(1.0, len(unique_entities) / self.normalization_params['max_entities']),
            # Entity type flags
            'has_acronyms': 1.0 if any(re.match(r'^[A-Z]{2,}$', e) for e in unique_entities) else 0.0,
            'has_numbers': 1.0 if any(re.search(r'\d', e) for e in unique_entities) else 0.0,
            'has_versions': 1.0 if any(re.match(r'v?\d+\.\d+', e) for e in unique_entities) else 0.0
        }
    
    def _extract_ambiguity_features(self, query: str) -> Dict[str, float]:
        """
        Extract ambiguity indicators from query.
        
        Args:
            query: Input query
            
        Returns:
            Dictionary of ambiguity features
        """
        query_lower = query.lower()
        words = query_lower.split()
        
        # Count ambiguous terms
        ambiguous_count = sum(1 for word in words if word in self.AMBIGUOUS_TERMS)
        
        # Vague terms that make queries ambiguous
        vague_terms = ['this', 'that', 'it', 'they', 'some', 'many', 'few',
                      'good', 'bad', 'better', 'best', 'thing', 'stuff',
                      'various', 'different', 'certain', 'several']
        
        # Pronouns without clear antecedents
        pronouns = ['it', 'they', 'them', 'this', 'that', 'these', 'those']
        
        vague_count = sum(1 for word in words if word in vague_terms)
        pronoun_count = sum(1 for word in words if word in pronouns)
        
        has_vague = vague_count > 0
        pronoun_density = pronoun_count / max(1, len(words))
        vague_density = vague_count / max(1, len(words))
        
        # Calculate ambiguity score
        ambiguity_score = min(1.0, vague_density * 0.5 + pronoun_density * 0.5)
        
        # Check for specific ambiguity patterns
        features = {
            'ambiguous_term_count': ambiguous_count,
            'ambiguity_ratio': ambiguous_count / max(1, len(words)),
            # Specific ambiguity types
            'has_vague_terms': 1.0 if has_vague else 0.0,
            'pronoun_density': pronoun_density,
            'vague_term_density': vague_density,
            'has_pronouns': 1.0 if any(w in query_lower for w in pronouns) else 0.0,
            'has_vague_quantifiers': 1.0 if any(w in query_lower for w in ['some', 'many', 'few', 'several']) else 0.0,
            'has_unclear_references': 1.0 if any(w in query_lower for w in ['thing', 'stuff', 'something']) else 0.0,
            'has_hedging': 1.0 if any(w in query_lower for w in ['maybe', 'perhaps', 'possibly', 'might']) else 0.0,
            # Overall ambiguity score
            'ambiguity_score': ambiguity_score
        }
        
        return features
    
    def _extract_structural_features(self, query: str) -> Dict[str, float]:
        """
        Extract structural features from query.
        
        Args:
            query: Input query
            
        Returns:
            Dictionary of structural features
        """
        return {
            'has_code_snippet': 1.0 if any(p in query for p in ['```', '`', '{', '}', 'def ', 'function']) else 0.0,
            'has_quotes': 1.0 if '"' in query or "'" in query else 0.0,
            'has_parentheses': 1.0 if '(' in query else 0.0,
            'has_lists': 1.0 if any(p in query for p in ['1.', '2.', '•', '-', '*']) else 0.0,
            'has_urls': 1.0 if 'http' in query or 'www.' in query else 0.0,
            'has_file_paths': 1.0 if '/' in query or '\\' in query else 0.0,
            'punctuation_complexity': min(1.0, (query.count(',') + query.count(';') + query.count(':')) / 5)
        }
    
    def _calculate_composite_features(self, features: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate composite features from individual feature categories.
        
        Args:
            features: All extracted features
            
        Returns:
            Dictionary of composite features
        """
        length = features['length_features']
        syntactic = features['syntactic_features']
        vocabulary = features['vocabulary_features']
        question = features['question_features']
        ambiguity = features['ambiguity_features']
        
        return {
            # Overall complexity indicators
            'length_complexity': (length['word_count_norm'] + length['char_count_norm']) / 2,
            'syntactic_complexity': syntactic['syntactic_complexity'],
            'vocabulary_complexity': vocabulary['technical_density'],
            'question_complexity': question.get('question_complexity', 0.5),
            'ambiguity_level': ambiguity['ambiguity_score'],
            
            # Combined scores
            'technical_depth': (
                vocabulary['technical_density'] * 0.5 +
                vocabulary.get('is_ml_heavy', 0) * 0.2 +
                vocabulary.get('is_engineering_heavy', 0) * 0.2 +
                vocabulary.get('is_rag_specific', 0) * 0.1
            ),
            
            'structural_complexity': (
                syntactic['clause_density'] * 0.3 +
                syntactic['nesting_norm'] * 0.3 +
                syntactic['conjunction_density'] * 0.2 +
                features.get('structural_features', {}).get('punctuation_complexity', 0) * 0.2
            ),
            
            'clarity_score': 1.0 - ambiguity['ambiguity_score'],
            
            # Query type indicators
            'is_simple_lookup': 1.0 if (
                question.get('is_what_is', 0) == 1.0 and
                length['word_count'] < 10 and
                vocabulary['technical_density'] < 0.2
            ) else 0.0,
            
            'is_complex_analysis': 1.0 if (
                question.get('is_comparison', 0) == 1.0 or
                question.get('is_explanation', 0) == 1.0 or
                syntactic['syntactic_complexity'] > 0.6
            ) else 0.0,
            
            'requires_deep_understanding': 1.0 if (
                vocabulary['technical_density'] > 0.3 and
                syntactic['syntactic_complexity'] > 0.5
            ) else 0.0,
            
            # Overall complexity (weighted combination of all factors)
            'overall_complexity': min(1.0, (
                length['word_count_norm'] * 0.15 +
                syntactic['syntactic_complexity'] * 0.25 +
                vocabulary['technical_density'] * 0.30 +
                question.get('question_complexity', 0.3) * 0.20 +
                ambiguity['ambiguity_score'] * 0.10
            ))
        }
    
    def get_summary(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a summary of key features for logging/debugging.
        
        Args:
            features: Extracted features
            
        Returns:
            Summary dictionary
        """
        return {
            'word_count': features['length_features']['word_count'],
            'technical_density': features['vocabulary_features']['technical_density'],
            'syntactic_complexity': features['syntactic_features']['syntactic_complexity'],
            'question_type': features['question_features']['question_type'],
            'ambiguity_score': features['ambiguity_features']['ambiguity_score'],
            'technical_terms': features['vocabulary_features']['technical_terms'][:5],  # First 5
            'composite_scores': {
                'technical_depth': features['composite_features']['technical_depth'],
                'structural_complexity': features['composite_features']['structural_complexity'],
                'clarity_score': features['composite_features']['clarity_score']
            }
        }