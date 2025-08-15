"""
Rule-based query intent classifier.

Implements pattern-based intent classification to determine cognitive complexity
of queries independent of technical vocabulary density.
"""

import re
import logging
from typing import Dict, List, Any, Tuple

from ..base import IntentClassifier, IntentClassificationResult

logger = logging.getLogger(__name__)


class RuleBasedIntentClassifier(IntentClassifier):
    """
    Rule-based implementation of query intent classification.
    
    Uses linguistic patterns and question structures to determine the cognitive
    complexity required to answer a query, independent of technical domain knowledge.
    """
    
    # Intent types ordered by cognitive complexity
    DEFAULT_INTENT_TYPES = {
        'factual': {
            'complexity_score': 0.2,
            'description': 'Simple factual queries requiring definition or enumeration',
            'patterns': [
                r'\bwhat\s+is\b',
                r'\bwhat\s+are\b', 
                r'\bwhat\s+does\b',
                r'\bwho\s+is\b',
                r'\bwhere\s+is\b',
                r'\bwhen\s+is\b',
                r'\bdefine\b',
                r'\blist\b.*\bof\b',
                r'\bname\b.*\bof\b'
            ],
            'examples': [
                'What is RISC-V?',
                'What are the basic instruction formats?',
                'Define vector extension'
            ]
        },
        
        'procedural': {
            'complexity_score': 0.5,
            'description': 'Procedural queries requiring process understanding or implementation guidance',
            'patterns': [
                r'\bhow\s+to\b',
                r'\bhow\s+do\s+you\b',
                r'\bhow\s+does\b.*\bwork\b',
                r'\bhow\s+can\b.*\b(implement|use|configure|setup)\b',
                r'\bsteps\s+to\b',
                r'\bprocess\s+of\b',
                r'\bmethods?\s+for\b',
                r'\bway\s+to\b',
                r'\bprocedure\s+for\b'
            ],
            'examples': [
                'How do vector instructions work?',
                'How to implement matrix multiplication?',
                'Steps to configure RISC-V toolchain'
            ]
        },
        
        'analytical': {
            'complexity_score': 0.7,
            'description': 'Analytical queries requiring comparison, evaluation, or multi-factor reasoning',
            'patterns': [
                r'\bcompare\b',
                r'\bcontrast\b',
                r'\bdifference\b.*\bbetween\b',
                r'\bsimilarit(y|ies)\b.*\bbetween\b',
                r'\badvantages?\b.*\bof\b',
                r'\bdisadvantages?\b.*\bof\b',
                r'\bbenefit\b.*\bof\b',
                r'\btrade-?off\b',
                r'\bimplication\b',
                r'\bimpact\b.*\bof\b',
                r'\beffect\b.*\bof\b',
                r'\bwhy\s+(is|are|do|does)\b',
                r'\bfactor\b.*\b(affect|influence)\b'
            ],
            'examples': [
                'Compare RISC-V with traditional architectures',
                'What are the trade-offs between modular extensions?',
                'Advantages of vector processing'
            ]
        },
        
        'research': {
            'complexity_score': 0.8,
            'description': 'Research queries requiring literature survey, current state analysis, or synthesis',
            'patterns': [
                r'\bwhat\s+research\b',
                r'\bwhat\s+(has\s+been\s+)?done\b.*\bon\b',
                r'\blatest\s+(development|advance|research|study)\b',
                r'\brecent\s+(work|research|study|development)\b',
                r'\bstate\s+of\s+the\s+art\b',
                r'\bcurrent\s+(status|state|research)\b',
                r'\bsurvey\s+of\b',
                r'\breview\s+of\b',
                r'\btrend\b.*\bin\b',
                r'\bevolution\s+of\b',
                r'\bdevelopment\b.*\bin\b'
            ],
            'examples': [
                'What research has been done on RISC-V optimization?',
                'Latest developments in vector architecture',
                'Current state of RISC-V adoption'
            ]
        },
        
        'strategic': {
            'complexity_score': 0.9,
            'description': 'Strategic queries requiring methodology design, planning, or high-level decision making',
            'patterns': [
                r'\bhow\s+should\b',
                r'\bwhat\s+(approach|strategy|methodology)\b',
                r'\bbest\s+(practice|approach|way)\b',
                r'\brecommend(ation|ed)?\b.*\bfor\b',
                r'\bguide(line|ance)\b.*\bfor\b',
                r'\bframework\s+for\b',
                r'\bstrategy\s+for\b',
                r'\bplan\s+for\b',
                r'\bconsideration\b.*\bfor\b',
                r'\bcriteria\s+for\b',
                r'\brequirement\b.*\bfor\b'
            ],
            'examples': [
                'How should manufacturers approach validation?',
                'Best practices for RISC-V integration',
                'Strategy for medical device compliance'
            ]
        }
    }
    
    # Additional patterns that modify complexity
    COMPLEXITY_MODIFIERS = {
        'increases': {
            'patterns': [
                r'\bmultiple\b',
                r'\bvarious\b', 
                r'\bdifferent\b.*\btypes?\b',
                r'\brange\s+of\b',
                r'\bvariety\s+of\b',
                r'\bcomplex\b',
                r'\badvanced\b',
                r'\bsophisticated\b'
            ],
            'modifier': 0.1  # Add to base score
        },
        'decreases': {
            'patterns': [
                r'\bsimple\b',
                r'\bbasic\b',
                r'\belementary\b',
                r'\bfundamental\b',
                r'\bintroduction\b.*\bto\b'
            ],
            'modifier': -0.1  # Subtract from base score
        }
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize rule-based intent classifier."""
        super().__init__(config)
        
        # Load intent types from config or use defaults
        self.intent_types = self.config.get('patterns', self.DEFAULT_INTENT_TYPES.copy())
        
        # Compile regex patterns for efficiency
        self._compile_patterns()
        
        logger.info(f"Initialized RuleBasedIntentClassifier with {len(self.intent_types)} intent types")
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching."""
        self.compiled_patterns = {}
        
        # Compile main intent patterns
        for intent_type, data in self.intent_types.items():
            patterns = data['patterns']
            self.compiled_patterns[intent_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
        
        # Compile modifier patterns
        self.compiled_modifiers = {}
        for modifier_type, data in self.COMPLEXITY_MODIFIERS.items():
            patterns = data['patterns']
            self.compiled_modifiers[modifier_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
    
    def classify_intent(self, query: str) -> IntentClassificationResult:
        """
        Classify the intent and cognitive complexity of a query.
        
        Args:
            query: Input query to analyze
            
        Returns:
            IntentClassificationResult with intent type and complexity score
        """
        # Clean and normalize query
        query_clean = query.strip().rstrip('?!.')
        
        # Find matching intent patterns
        intent_matches = self._find_intent_matches(query_clean)
        
        # Determine primary intent (highest complexity if multiple matches)
        if intent_matches:
            primary_intent = max(intent_matches, key=lambda x: self.intent_types[x]['complexity_score'])
            base_complexity = self.intent_types[primary_intent]['complexity_score']
            patterns_matched = intent_matches
            confidence = 0.9  # High confidence for pattern matches
        else:
            # Default to procedural if no clear pattern
            primary_intent = 'procedural'
            base_complexity = 0.5
            patterns_matched = []
            confidence = 0.3  # Low confidence for default assignment
        
        # Apply complexity modifiers
        final_complexity = self._apply_complexity_modifiers(query_clean, base_complexity)
        
        # Ensure complexity stays in valid range
        final_complexity = max(0.0, min(1.0, final_complexity))
        
        return IntentClassificationResult(
            intent_type=primary_intent,
            complexity_score=final_complexity,
            confidence=confidence,
            patterns_matched=patterns_matched,
            metadata={
                'base_complexity': base_complexity,
                'modifiers_applied': self._get_applied_modifiers(query_clean),
                'query_length': len(query_clean.split()),
                'has_question_words': self._has_question_words(query_clean)
            }
        )
    
    def _find_intent_matches(self, query: str) -> List[str]:
        """Find all intent types that match the query."""
        matches = []
        
        for intent_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(query):
                    matches.append(intent_type)
                    break  # One match per intent type
        
        return matches
    
    def _apply_complexity_modifiers(self, query: str, base_score: float) -> float:
        """Apply complexity modifiers based on additional patterns."""
        modified_score = base_score
        
        for modifier_type, patterns in self.compiled_modifiers.items():
            modifier_value = self.COMPLEXITY_MODIFIERS[modifier_type]['modifier']
            
            for pattern in patterns:
                if pattern.search(query):
                    modified_score += modifier_value
                    break  # Only apply each modifier type once
        
        return modified_score
    
    def _get_applied_modifiers(self, query: str) -> List[str]:
        """Get list of modifiers that were applied."""
        applied = []
        
        for modifier_type, patterns in self.compiled_modifiers.items():
            for pattern in patterns:
                if pattern.search(query):
                    applied.append(modifier_type)
                    break
        
        return applied
    
    def _has_question_words(self, query: str) -> bool:
        """Check if query contains explicit question words."""
        question_words = ['what', 'how', 'why', 'when', 'where', 'who', 'which']
        query_lower = query.lower()
        return any(word in query_lower for word in question_words)
    
    def get_intent_types(self) -> Dict[str, Dict[str, Any]]:
        """Get available intent types and their properties."""
        return self.intent_types.copy()
    
    def add_pattern(self, intent_type: str, pattern: str):
        """Add a new pattern to an existing intent type."""
        if intent_type not in self.intent_types:
            logger.warning(f"Intent type '{intent_type}' not found")
            return
        
        self.intent_types[intent_type]['patterns'].append(pattern)
        self._compile_patterns()  # Recompile patterns
        
        logger.info(f"Added pattern '{pattern}' to intent type '{intent_type}'")
    
    def get_complexity_distribution(self) -> Dict[str, float]:
        """Get the complexity score distribution across intent types."""
        return {
            intent_type: data['complexity_score']
            for intent_type, data in self.intent_types.items()
        }