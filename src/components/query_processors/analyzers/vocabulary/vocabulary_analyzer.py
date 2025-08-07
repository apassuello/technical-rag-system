"""
Vocabulary Analyzer orchestrator component.

Coordinates term classification and intent classification to produce comprehensive
vocabulary-based complexity scoring for query analysis.
"""

import logging
from typing import Dict, Any, Optional

from .base import VocabularyAnalyzerBase, TermClassifier, IntentClassifier
from .term_classifiers import RuleBasedTermClassifier
from .intent_classifiers import RuleBasedIntentClassifier

logger = logging.getLogger(__name__)


class VocabularyAnalyzer(VocabularyAnalyzerBase):
    """
    Main vocabulary analysis orchestrator.
    
    Combines technical term classification and query intent analysis to produce
    comprehensive vocabulary-based complexity scoring that addresses both technical
    domain knowledge and cognitive complexity.
    """
    
    def __init__(self,
                 term_classifier: Optional[TermClassifier] = None,
                 intent_classifier: Optional[IntentClassifier] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize vocabulary analyzer.
        
        Args:
            term_classifier: Optional term classifier (creates default if None)
            intent_classifier: Optional intent classifier (creates default if None)
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Initialize classifiers (create defaults if not provided)
        if term_classifier is None:
            term_config = self.config.get('term_classifier', {}).get('config', {})
            term_classifier = RuleBasedTermClassifier(term_config)
        
        if intent_classifier is None:
            intent_config = self.config.get('intent_classifier', {}).get('config', {})
            intent_classifier = RuleBasedIntentClassifier(intent_config)
        
        super().__init__(term_classifier, intent_classifier, config)
        
        # Scoring configuration
        scoring_config = self.config.get('scoring', {})
        self.technical_domain_weight = scoring_config.get('technical_domain_weight', 0.4)
        self.intent_complexity_weight = scoring_config.get('intent_complexity_weight', 0.6)
        
        # Ensure weights sum to 1.0
        total_weight = self.technical_domain_weight + self.intent_complexity_weight
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Scoring weights sum to {total_weight}, normalizing to 1.0")
            self.technical_domain_weight /= total_weight
            self.intent_complexity_weight /= total_weight
        
        logger.info(f"Initialized VocabularyAnalyzer with weights: "
                   f"technical_domain={self.technical_domain_weight:.2f}, "
                   f"intent_complexity={self.intent_complexity_weight:.2f}")
    
    @classmethod
    def create_from_config(cls, config: Dict[str, Any]) -> 'VocabularyAnalyzer':
        """
        Factory method to create VocabularyAnalyzer from configuration.
        
        Args:
            config: Full configuration dictionary
            
        Returns:
            Configured VocabularyAnalyzer instance
        """
        # Create term classifier based on config
        term_config = config.get('term_classifier', {})
        term_type = term_config.get('type', 'rule_based')
        
        if term_type == 'rule_based':
            term_classifier = RuleBasedTermClassifier(term_config.get('config', {}))
        else:
            # Future: Support other classifier types
            logger.warning(f"Unsupported term classifier type: {term_type}, using rule_based")
            term_classifier = RuleBasedTermClassifier(term_config.get('config', {}))
        
        # Create intent classifier based on config
        intent_config = config.get('intent_classifier', {})
        intent_type = intent_config.get('type', 'rule_based')
        
        if intent_type == 'rule_based':
            intent_classifier = RuleBasedIntentClassifier(intent_config.get('config', {}))
        else:
            # Future: Support other classifier types
            logger.warning(f"Unsupported intent classifier type: {intent_type}, using rule_based")
            intent_classifier = RuleBasedIntentClassifier(intent_config.get('config', {}))
        
        return cls(term_classifier, intent_classifier, config)
    
    def analyze(self, query: str) -> Dict[str, Any]:
        """
        Perform comprehensive vocabulary analysis.
        
        Args:
            query: Input query to analyze
            
        Returns:
            Dict with comprehensive vocabulary and intent analysis
        """
        # Perform term classification
        term_result = self.term_classifier.classify_terms(query)
        
        # Perform intent classification
        intent_result = self.intent_classifier.classify_intent(query)
        
        # Calculate composite scores
        technical_domain_score = term_result.total_score
        intent_complexity_score = intent_result.complexity_score
        
        # Weighted composite score
        composite_score = (
            technical_domain_score * self.technical_domain_weight +
            intent_complexity_score * self.intent_complexity_weight
        )
        
        # Create comprehensive result
        analysis_result = {
            # Composite scoring
            'composite_score': composite_score,
            'technical_domain_score': technical_domain_score,
            'intent_complexity_score': intent_complexity_score,
            'scoring_weights': {
                'technical_domain_weight': self.technical_domain_weight,
                'intent_complexity_weight': self.intent_complexity_weight
            },
            
            # Term classification results
            'technical_terms': term_result.technical_terms,
            'term_categories': term_result.term_categories,
            'term_weights': term_result.term_weights,
            'technical_density': term_result.density,
            'term_metadata': term_result.metadata,
            
            # Intent classification results
            'intent_type': intent_result.intent_type,
            'intent_confidence': intent_result.confidence,
            'patterns_matched': intent_result.patterns_matched,
            'intent_metadata': intent_result.metadata,
            
            # Legacy compatibility (for existing feature extractor)
            'technical_term_count': len(term_result.technical_terms),
            'is_technical_query': len(term_result.technical_terms) > 0,
            'domain_scores': self._calculate_domain_scores(term_result),
            'vocabulary_richness': self._calculate_vocabulary_richness(query, term_result)
        }
        
        return analysis_result
    
    def _calculate_domain_scores(self, term_result) -> Dict[str, float]:
        """Calculate domain-specific scores for backward compatibility."""
        domain_scores = {}
        total_terms = len(term_result.technical_terms) or 1
        
        # Calculate scores by category
        for category, terms in term_result.term_categories.items():
            category_score = len(terms) / total_terms
            
            # Map categories to legacy domain names
            if 'research' in category:
                domain_scores['research'] = category_score
            elif 'ml' in category or 'ai' in category:
                domain_scores['ml'] = category_score
            elif 'medical' in category:
                domain_scores['medical'] = category_score
            else:
                domain_scores.setdefault('general_technical', 0.0)
                domain_scores['general_technical'] += category_score
        
        return domain_scores
    
    def _calculate_vocabulary_richness(self, query: str, term_result) -> float:
        """Calculate vocabulary richness for backward compatibility."""
        words = query.lower().split()
        unique_words = set(words)
        return len(unique_words) / len(words) if words else 0.0
    
    def get_feature_breakdown(self, query: str) -> Dict[str, Any]:
        """Get detailed breakdown of vocabulary features for debugging."""
        analysis = self.analyze(query)
        
        return {
            'query': query,
            'composite_score': analysis['composite_score'],
            'components': {
                'technical_domain': {
                    'score': analysis['technical_domain_score'],
                    'weight': analysis['scoring_weights']['technical_domain_weight'],
                    'contribution': analysis['technical_domain_score'] * analysis['scoring_weights']['technical_domain_weight'],
                    'terms_found': analysis['technical_terms'],
                    'categories': analysis['term_categories']
                },
                'intent_complexity': {
                    'score': analysis['intent_complexity_score'],
                    'weight': analysis['scoring_weights']['intent_complexity_weight'], 
                    'contribution': analysis['intent_complexity_score'] * analysis['scoring_weights']['intent_complexity_weight'],
                    'intent_type': analysis['intent_type'],
                    'patterns_matched': analysis['patterns_matched']
                }
            }
        }
    
    def update_weights(self, technical_weight: float, intent_weight: float):
        """Update scoring weights (useful for calibration)."""
        # Normalize weights
        total = technical_weight + intent_weight
        self.technical_domain_weight = technical_weight / total
        self.intent_complexity_weight = intent_weight / total
        
        logger.info(f"Updated vocabulary scoring weights: "
                   f"technical={self.technical_domain_weight:.3f}, "
                   f"intent={self.intent_complexity_weight:.3f}")
    
    def get_classifier_info(self) -> Dict[str, Any]:
        """Get information about the configured classifiers."""
        return {
            'term_classifier': {
                'type': type(self.term_classifier).__name__,
                'categories': list(self.term_classifier.get_term_categories().keys())
                if hasattr(self.term_classifier, 'get_term_categories') else []
            },
            'intent_classifier': {
                'type': type(self.intent_classifier).__name__,
                'intent_types': list(self.intent_classifier.get_intent_types().keys())
                if hasattr(self.intent_classifier, 'get_intent_types') else []
            },
            'scoring_weights': {
                'technical_domain_weight': self.technical_domain_weight,
                'intent_complexity_weight': self.intent_complexity_weight
            }
        }