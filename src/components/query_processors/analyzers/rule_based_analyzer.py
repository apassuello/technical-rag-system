"""
Rule-based Query Analyzer Implementation.

This module provides query analysis using rule-based heuristics and pattern
matching for fast, lightweight query understanding without external dependencies.

Features:
- Pattern-based intent classification
- Rule-based technical term detection
- Heuristic complexity scoring
- Fast performance for simple queries
- No external dependencies
"""

import re
import logging
from typing import Dict, Any, List, Optional, Set, Pattern
from pathlib import Path
import sys

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from ..base import QueryAnalysis
from .base_analyzer import BaseQueryAnalyzer

logger = logging.getLogger(__name__)


class RuleBasedAnalyzer(BaseQueryAnalyzer):
    """
    Rule-based query analyzer using pattern matching and heuristics.
    
    This analyzer provides fast query analysis using predefined rules and
    patterns without requiring external NLP libraries. It's optimized for
    performance and reliability in production environments.
    
    Configuration Options:
    - enable_pattern_matching: Enable regex pattern matching (default: True)
    - enable_technical_detection: Enable technical term detection (default: True)
    - enable_intent_classification: Enable intent classification (default: True)
    - custom_patterns: Custom regex patterns for specific domains
    - technical_keywords: Additional technical keywords to detect
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize rule-based analyzer with pattern configurations.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        
        # Configuration flags
        self._enable_pattern_matching = self._config.get('enable_pattern_matching', True)
        self._enable_technical_detection = self._config.get('enable_technical_detection', True)
        self._enable_intent_classification = self._config.get('enable_intent_classification', True)
        
        # Initialize pattern collections
        self._init_intent_patterns()
        self._init_technical_patterns()
        self._init_complexity_patterns()
        self._init_entity_patterns()
        
        # Load custom patterns if provided
        if 'custom_patterns' in self._config:
            self._load_custom_patterns(self._config['custom_patterns'])
        
        logger.info(f"Initialized RuleBasedAnalyzer with {len(self._intent_patterns)} intent patterns")
    
    def _init_intent_patterns(self) -> None:
        """Initialize regex patterns for intent classification."""
        self._intent_patterns = {
            'definition': [
                re.compile(r'\b(what\s+is|define|explain|meaning\s+of)\b', re.IGNORECASE),
                re.compile(r'\b(what\s+does\s+\w+\s+mean)\b', re.IGNORECASE),
                re.compile(r'\b(definition\s+of)\b', re.IGNORECASE)
            ],
            'procedural': [
                re.compile(r'\b(how\s+to|how\s+do|how\s+can)\b', re.IGNORECASE),
                re.compile(r'\b(step\s+by\s+step|implement|configure|setup)\b', re.IGNORECASE),
                re.compile(r'\b(create|build|develop|install)\b', re.IGNORECASE)
            ],
            'comparison': [
                re.compile(r'\b(compare|comparison|difference|vs|versus)\b', re.IGNORECASE),
                re.compile(r'\b(better|worse|advantages|disadvantages)\b', re.IGNORECASE),
                re.compile(r'\b(pros\s+and\s+cons|benefits)\b', re.IGNORECASE)
            ],
            'example': [
                re.compile(r'\b(example|sample|demo|demonstration)\b', re.IGNORECASE),
                re.compile(r'\b(show\s+me|give\s+me|provide)\b', re.IGNORECASE),
                re.compile(r'\b(tutorial|walkthrough)\b', re.IGNORECASE)
            ],
            'troubleshooting': [
                re.compile(r'\b(error|problem|issue|bug|fix)\b', re.IGNORECASE),
                re.compile(r'\b(troubleshoot|debug|solve|resolve)\b', re.IGNORECASE),
                re.compile(r'\b(why\s+is|why\s+does|not\s+working)\b', re.IGNORECASE)
            ],
            'list': [
                re.compile(r'\b(list|enumerate|all|every)\b', re.IGNORECASE),
                re.compile(r'\b(what\s+are\s+the|which\s+are)\b', re.IGNORECASE),
                re.compile(r'\b(types\s+of|kinds\s+of)\b', re.IGNORECASE)
            ]
        }
    
    def _init_technical_patterns(self) -> None:
        """Initialize patterns for technical term detection."""
        # Technical keywords (extensible via configuration)
        base_technical_keywords = [
            'api', 'sdk', 'framework', 'library', 'protocol', 'algorithm',
            'implementation', 'architecture', 'design', 'pattern', 'interface',
            'configuration', 'deployment', 'optimization', 'performance',
            'scalability', 'security', 'authentication', 'authorization',
            'database', 'query', 'index', 'cache', 'memory', 'cpu',
            'network', 'http', 'https', 'tcp', 'udp', 'ssl', 'tls',
            'json', 'xml', 'yaml', 'csv', 'markdown', 'html', 'css',
            'javascript', 'python', 'java', 'c++', 'rust', 'go',
            'docker', 'kubernetes', 'microservice', 'rest', 'graphql',
            'oauth', 'jwt', 'token', 'session', 'cookie', 'cors',
            'webpack', 'npm', 'yarn', 'pip', 'maven', 'gradle',
            'git', 'github', 'gitlab', 'cicd', 'devops', 'aws', 'azure'
        ]
        
        # Add custom technical keywords from config
        custom_keywords = self._config.get('technical_keywords', [])
        all_keywords = base_technical_keywords + custom_keywords
        
        # Create regex patterns for technical terms
        self._technical_keywords = set(all_keywords)
        self._technical_patterns = [
            re.compile(rf'\b{re.escape(keyword)}\b', re.IGNORECASE)
            for keyword in all_keywords
        ]
        
        # Patterns for technical structures
        self._technical_structure_patterns = [
            re.compile(r'\b\w+\.\w+\.\w+\b'),  # Package/module names (e.g., com.example.app)
            re.compile(r'\b\w+::\w+\b'),       # Namespace notation (e.g., std::vector)
            re.compile(r'\b\w+\[\]\b'),        # Array notation (e.g., int[])
            re.compile(r'\b[A-Z][a-z]+[A-Z]\w*\b'),  # CamelCase (likely class names)
            re.compile(r'\b[a-z]+_[a-z_]+\b'),       # snake_case (likely variables/functions)
            re.compile(r'\b[A-Z_]{3,}\b'),           # CONSTANTS
        ]
    
    def _init_complexity_patterns(self) -> None:
        """Initialize patterns for complexity assessment."""
        self._complexity_indicators = {
            'high': [
                re.compile(r'\b(implement|architecture|optimize|scale|performance)\b', re.IGNORECASE),
                re.compile(r'\b(enterprise|production|distributed|microservice)\b', re.IGNORECASE),
                re.compile(r'\b(security|authentication|authorization|encryption)\b', re.IGNORECASE)
            ],
            'medium': [
                re.compile(r'\b(configure|setup|install|deploy|integrate)\b', re.IGNORECASE),
                re.compile(r'\b(database|api|framework|library)\b', re.IGNORECASE),
                re.compile(r'\b(connect|parse|format|validate)\b', re.IGNORECASE)
            ],
            'low': [
                re.compile(r'\b(what|how|why|when|where)\b', re.IGNORECASE),
                re.compile(r'\b(basic|simple|example|tutorial)\b', re.IGNORECASE),
                re.compile(r'\b(hello\s+world|getting\s+started)\b', re.IGNORECASE)
            ]
        }
    
    def _init_entity_patterns(self) -> None:
        """Initialize patterns for entity detection."""
        self._entity_patterns = {
            'technology': re.compile(
                r'\b(React|Vue|Angular|Django|Flask|Spring|Node\.js|Express|'
                r'MongoDB|PostgreSQL|MySQL|Redis|Docker|Kubernetes|AWS|Azure|'
                r'Python|JavaScript|TypeScript|Java|C\+\+|Rust|Go|Swift)\b'
            ),
            'programming_concept': re.compile(
                r'\b(class|function|method|variable|array|object|inheritance|'
                r'polymorphism|encapsulation|recursion|algorithm|data\s+structure)\b',
                re.IGNORECASE
            ),
            'file_format': re.compile(
                r'\b\w+\.(json|xml|yaml|yml|csv|txt|md|html|css|js|py|java|cpp|rs)\b',
                re.IGNORECASE
            )
        }
    
    def _load_custom_patterns(self, custom_patterns: Dict[str, Any]) -> None:
        """Load custom regex patterns from configuration."""
        try:
            for category, patterns in custom_patterns.items():
                if isinstance(patterns, list):
                    compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
                    if category in self._intent_patterns:
                        self._intent_patterns[category].extend(compiled_patterns)
                    else:
                        self._intent_patterns[category] = compiled_patterns
                        
            logger.debug(f"Loaded {len(custom_patterns)} custom pattern categories")
        except Exception as e:
            logger.warning(f"Failed to load custom patterns: {e}")
    
    def _analyze_query(self, query: str) -> QueryAnalysis:
        """
        Perform rule-based query analysis.
        
        Args:
            query: Clean, validated query string
            
        Returns:
            QueryAnalysis with rule-based extracted characteristics
        """
        # Start with basic features
        basic_features = self._extract_basic_features(query)
        
        # Apply rule-based analysis
        rule_features = {}
        
        if self._enable_intent_classification:
            intent_category = self._classify_intent(query)
            rule_features['intent_category'] = intent_category
        
        if self._enable_technical_detection:
            technical_terms = self._extract_technical_terms(query)
            rule_features['technical_terms'] = technical_terms
        
        if self._enable_pattern_matching:
            entities = self._extract_entities(query)
            rule_features['entities'] = entities
        
        # Combine features
        all_features = {**basic_features, **rule_features}
        
        # Calculate derived metrics
        complexity_score = self._calculate_complexity_score(query, all_features)
        intent_category = rule_features.get('intent_category', self._determine_intent_category(query, all_features))
        suggested_k = self._suggest_retrieval_k(query, all_features)
        confidence = self._calculate_confidence(all_features)
        
        return QueryAnalysis(
            query=query,
            complexity_score=complexity_score,
            technical_terms=rule_features.get('technical_terms', []),
            entities=rule_features.get('entities', []),
            intent_category=intent_category,
            suggested_k=suggested_k,
            confidence=confidence,
            metadata={
                'analyzer_type': 'rule_based',
                'patterns_used': {
                    'intent_patterns': len(self._intent_patterns),
                    'technical_patterns': len(self._technical_patterns),
                    'entity_patterns': len(self._entity_patterns)
                },
                'features': all_features,
                'analysis_version': '1.0'
            }
        )
    
    def _classify_intent(self, query: str) -> str:
        """
        Classify query intent using pattern matching.
        
        Args:
            query: Query string to classify
            
        Returns:
            Intent category string
        """
        intent_scores = {}
        
        for intent, patterns in self._intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = pattern.findall(query)
                score += len(matches)
            
            if score > 0:
                intent_scores[intent] = score
        
        if intent_scores:
            # Return intent with highest score
            return max(intent_scores.items(), key=lambda x: x[1])[0]
        else:
            return 'general'
    
    def _extract_technical_terms(self, query: str) -> List[str]:
        """
        Extract technical terms using pattern matching.
        
        Args:
            query: Query string to analyze
            
        Returns:
            List of technical terms found
        """
        technical_terms = []
        
        # Check against known technical keywords
        for pattern in self._technical_patterns:
            matches = pattern.findall(query)
            technical_terms.extend(matches)
        
        # Check for technical structures
        for pattern in self._technical_structure_patterns:
            matches = pattern.findall(query)
            technical_terms.extend(matches)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_terms = []
        for term in technical_terms:
            term_lower = term.lower()
            if term_lower not in seen:
                seen.add(term_lower)
                unique_terms.append(term)
        
        return unique_terms
    
    def _extract_entities(self, query: str) -> List[str]:
        """
        Extract entities using pattern matching.
        
        Args:
            query: Query string to analyze
            
        Returns:
            List of entities found
        """
        entities = []
        
        for entity_type, pattern in self._entity_patterns.items():
            matches = pattern.findall(query)
            entities.extend(matches)
        
        # Remove duplicates
        return list(set(entities))
    
    def _calculate_complexity_score(self, query: str, features: Dict[str, Any]) -> float:
        """
        Calculate complexity score using rule-based heuristics.
        
        Args:
            query: Original query string
            features: Extracted features
            
        Returns:
            Complexity score between 0.0 and 1.0
        """
        score = 0.0
        
        # Check complexity indicator patterns
        for complexity_level, patterns in self._complexity_indicators.items():
            pattern_matches = sum(
                len(pattern.findall(query)) for pattern in patterns
            )
            
            if complexity_level == 'high':
                score += pattern_matches * 0.3
            elif complexity_level == 'medium':
                score += pattern_matches * 0.2
            elif complexity_level == 'low':
                score += pattern_matches * 0.1
        
        # Technical terms add complexity
        tech_term_count = len(features.get('technical_terms', []))
        score += min(0.3, tech_term_count * 0.1)
        
        # Query length factor
        word_count = features.get('word_count', 0)
        if word_count > 15:
            score += 0.2
        elif word_count > 10:
            score += 0.1
        
        # Multiple entities suggest complexity
        entity_count = len(features.get('entities', []))
        if entity_count > 2:
            score += 0.2
        elif entity_count > 0:
            score += 0.1
        
        return min(1.0, max(0.0, score))
    
    def _calculate_confidence(self, features: Dict[str, Any]) -> float:
        """
        Calculate confidence in rule-based analysis.
        
        Args:
            features: Extracted features
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.7  # Base confidence for rule-based analysis
        
        # Higher confidence when patterns match
        if features.get('intent_category') != 'general':
            confidence += 0.15
        
        if features.get('technical_terms'):
            confidence += 0.1
        
        if features.get('entities'):
            confidence += 0.05
        
        return min(1.0, max(0.0, confidence))
    
    def get_supported_features(self) -> List[str]:
        """
        Return list of features this rule-based analyzer supports.
        
        Returns:
            List of feature names
        """
        base_features = super().get_supported_features()
        rule_features = [
            'intent_classification',
            'technical_term_detection',
            'entity_extraction',
            'complexity_scoring',
            'pattern_matching',
            'fast_analysis'
        ]
        return base_features + rule_features