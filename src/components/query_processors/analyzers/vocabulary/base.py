"""
Abstract base classes for vocabulary analysis components.

Defines clean interfaces for term classification and intent detection that allow
easy swapping between rule-based and ML-based implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class TermClassificationResult:
    """Result of technical term classification."""
    technical_terms: List[str]
    term_categories: Dict[str, List[str]]  # category -> terms
    term_weights: Dict[str, float]  # term -> weight
    total_score: float
    density: float
    metadata: Dict[str, Any]


@dataclass  
class IntentClassificationResult:
    """Result of query intent classification."""
    intent_type: str  # factual, procedural, analytical, research, strategic
    complexity_score: float  # 0.0-1.0 cognitive complexity
    confidence: float  # 0.0-1.0 classification confidence
    patterns_matched: List[str]  # which patterns triggered
    metadata: Dict[str, Any]


class TermClassifier(ABC):
    """
    Abstract base class for technical term classification.
    
    Provides interface for identifying technical terms in text and assigning
    complexity weights based on the sophistication of the terminology.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize term classifier with configuration."""
        self.config = config or {}
    
    @abstractmethod
    def classify_terms(self, text: str) -> TermClassificationResult:
        """
        Classify technical terms in the given text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            TermClassificationResult with classified terms and scores
        """
        pass
    
    @abstractmethod
    def get_term_categories(self) -> Dict[str, Dict[str, Any]]:
        """
        Get available term categories and their properties.
        
        Returns:
            Dict mapping category names to category metadata
        """
        pass
    
    def is_technical_term(self, term: str) -> bool:
        """Check if a term is considered technical."""
        # Default implementation - subclasses can override
        result = self.classify_terms(term)
        return len(result.technical_terms) > 0


class IntentClassifier(ABC):
    """
    Abstract base class for query intent classification.
    
    Provides interface for analyzing query intent to determine cognitive
    complexity regardless of technical vocabulary density.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize intent classifier with configuration."""
        self.config = config or {}
    
    @abstractmethod
    def classify_intent(self, query: str) -> IntentClassificationResult:
        """
        Classify the intent and cognitive complexity of a query.
        
        Args:
            query: Input query to analyze
            
        Returns:
            IntentClassificationResult with intent type and complexity score
        """
        pass
    
    @abstractmethod
    def get_intent_types(self) -> Dict[str, Dict[str, Any]]:
        """
        Get available intent types and their properties.
        
        Returns:
            Dict mapping intent types to their metadata
        """
        pass
    
    def get_complexity_score(self, intent_type: str) -> float:
        """Get the complexity score for a given intent type."""
        intent_types = self.get_intent_types()
        return intent_types.get(intent_type, {}).get('complexity_score', 0.5)


class VocabularyAnalyzerBase(ABC):
    """
    Abstract base class for vocabulary analysis orchestrators.
    
    Coordinates term classification and intent classification to produce
    comprehensive vocabulary-based complexity scoring.
    """
    
    def __init__(self, 
                 term_classifier: TermClassifier,
                 intent_classifier: IntentClassifier,
                 config: Optional[Dict[str, Any]] = None):
        """Initialize with component classifiers."""
        self.term_classifier = term_classifier
        self.intent_classifier = intent_classifier
        self.config = config or {}
    
    @abstractmethod
    def analyze(self, query: str) -> Dict[str, Any]:
        """
        Perform comprehensive vocabulary analysis.
        
        Args:
            query: Input query to analyze
            
        Returns:
            Dict with comprehensive vocabulary and intent analysis
        """
        pass