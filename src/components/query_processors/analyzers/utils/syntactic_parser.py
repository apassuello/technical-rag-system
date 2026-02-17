"""
Syntactic Parser for Epic 1 Query Analysis.

This module provides lightweight syntax analysis without heavy NLP dependencies,
using regex patterns and heuristics to assess query complexity.

Architecture Notes:
- No external NLP libraries required (lightweight)
- Pattern-based analysis for efficiency
- Configurable complexity thresholds
- Optimized for <50ms performance
"""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SyntacticParser:
    """
    Lightweight syntax analyzer for query complexity assessment.

    Features:
    - Clause detection and counting
    - Nesting depth analysis
    - Conjunction and connector analysis
    - Question structure classification
    - Sentence segmentation
    - Complexity scoring

    All analysis is done using regex and heuristics for speed,
    avoiding heavy NLP dependencies.
    """

    # Linguistic patterns
    CLAUSE_INDICATORS = [
        r'\b(which|that|who|whom|whose|where|when|why|how)\b',
        r'\b(if|unless|although|though|because|since|while|whereas)\b',
        r'\b(after|before|until|as|once)\b'
    ]

    CONJUNCTIONS = {
        'coordinating': ['and', 'but', 'or', 'nor', 'for', 'yet', 'so'],
        'subordinating': ['because', 'although', 'since', 'unless', 'if', 'when',
                         'while', 'before', 'after', 'though', 'whereas'],
        'correlative': ['either...or', 'neither...nor', 'both...and',
                       'not only...but also', 'whether...or']
    }

    QUESTION_PATTERNS = {
        'what': r'^what\s+(is|are|was|were|does|do|did|can|could|should|would)',
        'how': r'^how\s+(does|do|did|can|could|should|would|to|many|much)',
        'why': r'^why\s+(is|are|was|were|does|do|did|should|would)',
        'when': r'^when\s+(is|are|was|were|does|do|did|will|would|should)',
        'where': r'^where\s+(is|are|was|were|does|do|can|could|should)',
        'who': r'^who\s+(is|are|was|were|does|do|did|can|could|should)',
        'which': r'^which\s+(is|are|was|were|one|ones|of)',
        'compare': r'(compare|difference|between|versus|vs\.?)\s',
        'explain': r'^(explain|describe|elaborate|clarify)\s',
        'list': r'^(list|enumerate|name|provide|give)\s'
    }

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize syntactic parser.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}

        # Compile patterns for efficiency
        self.clause_pattern = re.compile(
            '|'.join(self.CLAUSE_INDICATORS),
            re.IGNORECASE
        )

        self.question_patterns = {
            qtype: re.compile(pattern, re.IGNORECASE)
            for qtype, pattern in self.QUESTION_PATTERNS.items()
        }

        logger.debug("Initialized SyntacticParser")

    def analyze_complexity(self, text: str) -> Dict[str, Any]:
        """
        Analyze syntactic complexity of text.

        Args:
            text: Input text to analyze

        Returns:
            Dictionary with complexity metrics
        """
        # Clean and normalize text
        text = text.strip()

        # Perform various analyses
        sentences = self._segment_sentences(text)

        return {
            'sentence_count': len(sentences),
            'avg_sentence_length': self._avg_sentence_length(sentences),
            'clause_count': self._count_clauses(text),
            'nesting_depth': self._calculate_nesting_depth(text),
            'conjunction_count': self._count_conjunctions(text),
            'question_type': self._classify_question_type(text),
            'has_comparison': self._has_comparison(text),
            'has_enumeration': self._has_enumeration(text),
            'punctuation_complexity': self._analyze_punctuation(text),
            'parenthetical_depth': self._calculate_parenthetical_depth(text)
        }

    def _segment_sentences(self, text: str) -> List[str]:
        """
        Segment text into sentences.

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        # Simple sentence segmentation
        # Handle common abbreviations
        text = re.sub(r'\b(Dr|Mr|Mrs|Ms|Prof|Sr|Jr)\. ', r'\1<DOT> ', text)
        text = re.sub(r'\b(Inc|Ltd|Corp|Co)\. ', r'\1<DOT> ', text)
        text = re.sub(r'\b(i\.e|e\.g|etc|vs|cf)\. ', r'\1<DOT> ', text)

        # Split on sentence boundaries
        sentences = re.split(r'[.!?]+\s+', text)

        # Restore dots
        sentences = [s.replace('<DOT>', '.') for s in sentences if s.strip()]

        return sentences

    def _avg_sentence_length(self, sentences: List[str]) -> float:
        """Calculate average sentence length in words."""
        if not sentences:
            return 0.0

        total_words = sum(len(s.split()) for s in sentences)
        return total_words / len(sentences)

    def _count_clauses(self, text: str) -> int:
        """
        Count number of clauses in text.
        A clause has a subject and predicate.

        Args:
            text: Input text

        Returns:
            Number of clauses detected
        """
        if not text.strip():
            return 0

        # Start with 1 for the main clause
        count = 1

        # Handle compound verb phrases that shouldn't be counted as separate clauses
        text_processed = text
        compound_phrases = [
            r'\bcompare\s+and\s+contrast\b',
            r'\bback\s+and\s+forth\b',
            r'\bup\s+and\s+down\b',
            r'\bin\s+and\s+out\b'
        ]
        for phrase in compound_phrases:
            text_processed = re.sub(phrase, lambda m: m.group(0).replace(' and ', ' AND_COMPOUND '), text_processed, flags=re.IGNORECASE)

        # Coordinating conjunctions that often separate independent clauses
        # Look for ", and", ", but", ", or" etc. AND standalone "and", "but", "or"
        coord_pattern = r'(?:,\s+(?:and|but|or|nor|for|yet|so)\s+|\s+(?:and|but|or)\s+)'
        coord_matches = re.findall(coord_pattern, text_processed, re.IGNORECASE)
        # Filter out compound phrase markers
        coord_matches = [m for m in coord_matches if 'AND_COMPOUND' not in m]
        count += len(coord_matches)

        # Handle conditional structures (if...then...otherwise) as a unit
        has_conditional = bool(re.search(r'\bif\b', text, re.IGNORECASE))
        has_then = bool(re.search(r'\bthen\b', text, re.IGNORECASE))
        has_otherwise = bool(re.search(r'\botherwise\b', text, re.IGNORECASE))

        if has_conditional and (has_then or has_otherwise):
            # If-then-otherwise is a conditional structure with 2 main parts:
            # 1. The condition (if X)
            # 2. The consequence (then Y, otherwise Z)
            conditional_clauses = 1  # One additional clause for the conditional
            if has_then and has_otherwise:
                conditional_clauses += 1  # Extra for "otherwise" alternative
            count += conditional_clauses
        else:
            # Regular subordinating conjunctions
            subord_pattern = r'\b(?:because|since|although|though|when|while|where|after|before|until|unless|whereas|whether|considering|given)\s+'
            subord_matches = re.findall(subord_pattern, text, re.IGNORECASE)
            count += len(subord_matches)

            # Handle standalone "if" without then/otherwise
            if has_conditional and not (has_then or has_otherwise):
                count += 1

        # Semicolons and colons can separate clauses
        count += text.count(';')
        count += text.count(':') // 2  # Conservative for colons

        # Relative clauses (which, that, who) - both with and without commas
        relative_pattern = r'(?:,\s*)?(?:which|who|whom|whose|that)\s+'
        count += len(re.findall(relative_pattern, text, re.IGNORECASE))

        # Additional clause indicators
        # Infinitive phrases can indicate additional clauses
        infinitive_pattern = r'\bto\s+(?:be|have|get|make|take|give|find|show|help|allow|enable)\b'
        count += len(re.findall(infinitive_pattern, text, re.IGNORECASE)) // 2

        # Participial phrases
        participle_pattern = r'\b(?:considering|including|containing|involving|requiring|providing)\b'
        count += len(re.findall(participle_pattern, text, re.IGNORECASE)) // 2

        # Question words at the beginning that create additional clauses
        question_clause_pattern = r'\b(?:what|how|why|when|where|who)\s+(?:is|are|was|were|does|do|did|can|could|should|would)'
        if re.search(question_clause_pattern, text, re.IGNORECASE):
            # Question structure adds complexity but doesn't necessarily add clauses
            pass

        return count

    def _calculate_nesting_depth(self, text: str) -> int:
        """
        Calculate maximum nesting depth of clauses.

        Args:
            text: Input text

        Returns:
            Maximum nesting depth
        """
        # Track nesting with parentheses, brackets, and clause indicators
        max_depth = 0
        current_depth = 0

        # Check parenthetical nesting
        for char in text:
            if char in '([{':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char in ')]}':
                current_depth = max(0, current_depth - 1)

        # Check clause nesting (simplified)
        clause_words = ['if', 'when', 'while', 'although', 'because']
        text_lower = text.lower()

        clause_depth = 0
        for word in clause_words:
            if word in text_lower:
                clause_depth += 1

        # Conservative estimate of nesting
        return max(max_depth, min(3, clause_depth))

    def _count_conjunctions(self, text: str) -> int:
        """
        Count conjunctions in text.

        Args:
            text: Input text

        Returns:
            Total conjunction count
        """
        text_lower = text.lower()
        count = 0

        # Count all conjunction types
        for conj_type, conj_list in self.CONJUNCTIONS.items():
            for conj in conj_list:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(conj) + r'\b'
                count += len(re.findall(pattern, text_lower))

        return count

    def _classify_question_type(self, text: str) -> str:
        """
        Classify the type of question.

        Args:
            text: Input text

        Returns:
            Question type or 'unknown'
        """
        text_lower = text.lower().strip()

        # Check each question pattern
        for qtype, pattern in self.question_patterns.items():
            if pattern.search(text_lower):
                return qtype

        # Check if it's a question at all
        if text.strip().endswith('?'):
            return 'other_question'

        return 'statement'

    def _has_comparison(self, text: str) -> bool:
        """Check if text contains comparison indicators."""
        comparison_words = [
            'compare', 'comparison', 'versus', 'vs', 'difference',
            'better', 'worse', 'more', 'less', 'similar', 'different',
            'contrast', 'distinguish', 'prefer'
        ]

        text_lower = text.lower()
        return any(word in text_lower for word in comparison_words)

    def _has_enumeration(self, text: str) -> bool:
        """Check if text requests enumeration/listing."""
        enumeration_words = [
            'list', 'enumerate', 'name all', 'what are all',
            'give me all', 'show all', 'provide all'
        ]

        text_lower = text.lower()
        return any(phrase in text_lower for phrase in enumeration_words)

    def _analyze_punctuation(self, text: str) -> Dict[str, int]:
        """Analyze punctuation complexity."""
        return {
            'commas': text.count(','),
            'semicolons': text.count(';'),
            'colons': text.count(':'),
            'parentheses': text.count('(') + text.count(')'),
            'quotes': text.count('"') + text.count("'"),
            'dashes': text.count('-') + text.count('—')
        }

    def _calculate_parenthetical_depth(self, text: str) -> int:
        """Calculate maximum parenthetical nesting depth."""
        max_depth = 0
        current_depth = 0

        for char in text:
            if char == '(':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == ')':
                current_depth = max(0, current_depth - 1)

        return max_depth

    def calculate_complexity_score(self, analysis: Dict[str, Any]) -> float:
        """
        Calculate overall syntactic complexity score.

        Args:
            analysis: Results from analyze_complexity

        Returns:
            Complexity score between 0.0 and 1.0
        """
        score = 0.0

        # Sentence complexity (0-0.3)
        avg_length = analysis.get('avg_sentence_length', 0)
        if avg_length < 10:
            score += 0.0
        elif avg_length < 20:
            score += 0.15
        else:
            score += 0.3

        # Clause complexity (0-0.3)
        clause_count = analysis.get('clause_count', 0)
        if clause_count == 0:
            score += 0.0
        elif clause_count <= 2:
            score += 0.15
        else:
            score += 0.3

        # Nesting complexity (0-0.2)
        nesting = analysis.get('nesting_depth', 0)
        score += min(0.2, nesting * 0.1)

        # Conjunction complexity (0-0.1)
        conjunctions = analysis.get('conjunction_count', 0)
        score += min(0.1, conjunctions * 0.02)

        # Special features (0-0.1)
        if analysis.get('has_comparison'):
            score += 0.05
        if analysis.get('has_enumeration'):
            score += 0.05

        return min(1.0, score)

    def get_complexity_features(self, text: str) -> Dict[str, float]:
        """
        Get normalized complexity features for classification.

        Args:
            text: Input text

        Returns:
            Dictionary of normalized features (0.0 to 1.0)
        """
        analysis = self.analyze_complexity(text)

        # Normalize features to 0-1 range
        return {
            'sentence_length_norm': min(1.0, analysis['avg_sentence_length'] / 30),
            'clause_density': min(1.0, analysis['clause_count'] / 5),
            'nesting_depth_norm': min(1.0, analysis['nesting_depth'] / 3),
            'conjunction_density': min(1.0, analysis['conjunction_count'] / 8),
            'has_comparison': 1.0 if analysis['has_comparison'] else 0.0,
            'has_enumeration': 1.0 if analysis['has_enumeration'] else 0.0,
            'syntactic_score': self.calculate_complexity_score(analysis)
        }

    # Public API methods for testing
    def count_clauses(self, text: str) -> int:
        """Public method to count clauses."""
        return self._count_clauses(text)

    def calculate_nesting_depth(self, text: str) -> int:
        """Public method to calculate nesting depth."""
        return self._calculate_nesting_depth(text)

    def count_conjunctions(self, text: str) -> int:
        """Public method to count conjunctions."""
        return self._count_conjunctions(text)

    def classify_question(self, text: str) -> str:
        """Public method to classify question type."""
        return self._classify_question_type(text)

    def calculate_punctuation_complexity(self, text: str) -> float:
        """Calculate punctuation complexity score."""
        punct = self._analyze_punctuation(text)
        # Simple scoring based on punctuation diversity and count
        score = 0.0
        score += min(0.3, punct['commas'] * 0.05)
        score += min(0.2, punct['semicolons'] * 0.1)
        score += min(0.2, punct['colons'] * 0.1)
        score += min(0.2, punct['parentheses'] * 0.02)
        score += min(0.1, punct['quotes'] * 0.02)
        return min(1.0, score)

    def parse(self, text: str) -> Dict[str, Any]:
        """Public method for comprehensive parsing (alias for analyze_complexity)."""
        analysis = self.analyze_complexity(text)
        # Add complexity score to the analysis
        analysis['complexity_score'] = self.calculate_complexity_score(analysis)
        return analysis
