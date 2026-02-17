"""
Complexity Classifier for Epic 1 Query Analysis.

This module classifies query complexity based on extracted features,
determining whether queries are simple, medium, or complex for optimal
model routing.

Architecture Notes:
- Direct implementation (pure algorithm)
- Weighted scoring system
- Configurable thresholds
- Confidence scoring based on threshold distance
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class ComplexityClassification:
    """Result of complexity classification."""
    level: str  # simple/medium/complex
    score: float  # 0.0-1.0 normalized score
    confidence: float  # 0.0-1.0 confidence in classification
    breakdown: Dict[str, float]  # Score breakdown by category
    reasoning: str  # Human-readable explanation


class ComplexityClassifier:
    """
    Classifies query complexity based on extracted features.

    This sub-component analyzes features from FeatureExtractor to determine
    query complexity level for Epic 1 model routing.

    Levels:
    - Simple: Basic factual queries, single concepts (0.0-0.35)
    - Medium: Multi-step reasoning, moderate technical depth (0.35-0.70)
    - Complex: Advanced analysis, multiple concepts, deep technical (0.70-1.0)

    Configuration:
    - weights: Feature category weights (must sum to 1.0)
    - thresholds: Boundaries for classification levels
    - confidence_params: Parameters for confidence calculation
    """

    # Default feature weights (sum to 1.0)
    DEFAULT_WEIGHTS = {
        'length': 0.20,      # Query length and structure
        'syntactic': 0.25,   # Syntactic complexity
        'vocabulary': 0.30,  # Technical vocabulary
        'question': 0.15,    # Question type and complexity
        'ambiguity': 0.10    # Ambiguity and clarity
    }

    # Default sub-category weights for fine-grained tuning
    DEFAULT_SUB_WEIGHTS = {
        'length': {
            'word_count': 0.6,      # Word count contribution
            'char_count': 0.2,      # Character count contribution
            'sentence_count': 0.2   # Sentence count contribution
        },
        'vocabulary': {
            'technical_density': 0.5,      # Technical term density
            'technical_count': 0.3,        # Raw technical term count
            'vocabulary_richness': 0.2     # Unique word ratio
        },
        'syntactic': {
            'clause_complexity': 0.4,      # Clause structure
            'nesting_depth': 0.3,          # Structural nesting
            'conjunction_complexity': 0.3  # Coordination complexity
        },
        'question': {
            'question_type': 0.6,          # Type-based complexity
            'comparative_complexity': 0.4  # Comparative structures
        },
        'ambiguity': {
            'ambiguous_terms': 0.7,        # Ambiguous term presence
            'pronoun_references': 0.3      # Pronoun complexity
        }
    }

    # Default complexity thresholds - Optimized based on ground truth analysis
    DEFAULT_THRESHOLDS = {
        'simple': 0.150,   # Below this = simple (optimized for 58.1% accuracy)
        'complex': 0.320   # Above this = complex (optimized for 58.1% accuracy)
    }

    # Confidence calculation parameters
    DEFAULT_CONFIDENCE_PARAMS = {
        'high_confidence_margin': 0.15,   # Distance from threshold for high confidence
        'medium_confidence_margin': 0.10,  # Distance for medium confidence
        'low_confidence_margin': 0.05     # Distance for low confidence
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize complexity classifier.

        Args:
            config: Configuration dictionary with:
                - weights: Feature category weights (must sum to 1.0)
                - sub_weights: Sub-category weights within each category
                - thresholds: Classification level boundaries
                - confidence_params: Confidence calculation parameters
        """
        self.config = config or {}

        # Load configuration
        self.weights = self.config.get('weights', self.DEFAULT_WEIGHTS.copy())
        self.sub_weights = self.config.get('sub_weights', self.DEFAULT_SUB_WEIGHTS.copy())
        self.thresholds = self.config.get('thresholds', self.DEFAULT_THRESHOLDS.copy())
        self.confidence_params = self.config.get(
            'confidence_params',
            self.DEFAULT_CONFIDENCE_PARAMS.copy()
        )

        # Validate weights sum to 1.0
        weight_sum = sum(self.weights.values())
        if abs(weight_sum - 1.0) > 0.01:
            logger.warning(f"Weights sum to {weight_sum}, normalizing to 1.0")
            self.weights = {k: v/weight_sum for k, v in self.weights.items()}

        # Validate sub-weights sum to 1.0 for each category
        for category, sub_weights in self.sub_weights.items():
            if sub_weights:  # Only validate if sub-weights exist
                sub_sum = sum(sub_weights.values())
                if abs(sub_sum - 1.0) > 0.01:
                    logger.warning(f"{category} sub-weights sum to {sub_sum}, normalizing to 1.0")
                    self.sub_weights[category] = {k: v/sub_sum for k, v in sub_weights.items()}

        logger.info(f"Initialized ComplexityClassifier with thresholds: {self.thresholds}")
        logger.debug(f"Category weights: {self.weights}")
        logger.debug(f"Sub-category weights loaded: {list(self.sub_weights.keys())}")

    def classify(self, features: Dict[str, Any]) -> ComplexityClassification:
        """
        Classify query complexity from features.

        Args:
            features: Feature dictionary from FeatureExtractor

        Returns:
            ComplexityClassification with level, score, and confidence
        """
        # Calculate category scores
        category_scores = self._calculate_category_scores(features)

        # Calculate weighted overall score
        overall_score = self._calculate_weighted_score(category_scores)

        # Determine complexity level
        level = self._determine_level(overall_score)

        # Calculate confidence
        confidence = self._calculate_confidence(overall_score)

        # Generate reasoning
        reasoning = self._generate_reasoning(level, overall_score, category_scores)

        # Return both dataclass and dictionary for compatibility
        classification = ComplexityClassification(
            level=level,
            score=overall_score,
            confidence=confidence,
            breakdown=category_scores,
            reasoning=reasoning
        )

        # Return dictionary format for backward compatibility
        return {
            'complexity_level': level,
            'complexity_score': overall_score,
            'confidence': confidence,
            'breakdown': category_scores,
            'reasoning': reasoning,
            '_classification_object': classification  # Store dataclass for advanced use
        }

    def _calculate_category_scores(self, features: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate normalized scores for each feature category.

        Args:
            features: Raw features from FeatureExtractor or test format

        Returns:
            Dictionary mapping categories to normalized scores (0.0-1.0)
        """
        scores = {}

        # Handle both full feature format and test format
        if 'length_features' in features:
            # Full FeatureExtractor format
            length_features = features.get('length_features', {})
            syntactic_features = features.get('syntactic_features', {})
            vocabulary_features = features.get('vocabulary_features', {})
            question_features = features.get('question_features', {})
            ambiguity_features = features.get('ambiguity_features', {})
        else:
            # Test format - direct category access
            length_features = features.get('length', {})
            syntactic_features = features.get('syntactic', {})
            vocabulary_features = features.get('vocabulary', {})
            question_features = features.get('question', {})
            ambiguity_features = features.get('ambiguity', {})

        # Calculate scores for each category
        scores['length'] = self._calculate_length_score(length_features)
        scores['syntactic'] = self._calculate_syntactic_score(syntactic_features)
        scores['vocabulary'] = self._calculate_vocabulary_score(vocabulary_features)
        scores['question'] = self._calculate_question_score(question_features)
        scores['ambiguity'] = self._calculate_ambiguity_score(ambiguity_features)

        return scores

    def _calculate_length_score(self, features: Dict[str, Any]) -> float:
        """
        Calculate length-based complexity score.

        Longer queries tend to be more complex, but plateaus after certain length.
        """
        # Handle both formats
        if 'normalized' in features:
            # Test format - use normalized value directly
            return features.get('normalized', 0.0)
        else:
            # Full format
            word_count_norm = features.get('word_count_norm', 0.0)
            is_long = features.get('is_long_query', 0.0)
            is_very_long = features.get('is_very_long_query', 0.0)

            # Weighted combination
            score = (
                word_count_norm * 0.6 +
                is_long * 0.2 +
                is_very_long * 0.2
            )

            return min(1.0, score)

    def _calculate_syntactic_score(self, features: Dict[str, Any]) -> float:
        """
        Calculate syntactic complexity score.

        Based on clause structure, nesting, and overall syntactic complexity.
        """
        # Handle both formats
        if 'normalized' in features:
            # Test format - use normalized value directly
            return features.get('normalized', 0.0)
        else:
            # Full format
            # Primary syntactic complexity score from parser
            syntactic_complexity = features.get('syntactic_complexity', 0.0)

            # Additional indicators
            clause_density = features.get('clause_density', 0.0)
            nesting_norm = features.get('nesting_norm', 0.0)
            conjunction_density = features.get('conjunction_density', 0.0)
            has_comparison = features.get('has_comparison', 0.0)
            has_enumeration = features.get('has_enumeration', 0.0)

            # Weighted combination
            score = (
                syntactic_complexity * 0.4 +
                clause_density * 0.2 +
                nesting_norm * 0.2 +
                conjunction_density * 0.1 +
                has_comparison * 0.05 +
                has_enumeration * 0.05
            )

            return min(1.0, score)

    def _calculate_vocabulary_score(self, features: Dict[str, Any]) -> float:
        """
        Calculate vocabulary/technical complexity score.

        Technical queries require more sophisticated models.
        """
        # Handle both formats
        if 'complexity_score' in features:
            # Test format - use complexity_score directly
            return features.get('complexity_score', 0.0)
        else:
            # Full format
            technical_density = features.get('technical_density', 0.0)
            is_technical = features.get('is_technical_query', 0.0)
            technical_term_norm = features.get('technical_term_norm', 0.0)

            # Domain-specific indicators
            is_ml_heavy = features.get('is_ml_heavy', 0.0)
            is_engineering_heavy = features.get('is_engineering_heavy', 0.0)
            is_rag_specific = features.get('is_rag_specific', 0.0)

            # Vocabulary richness
            vocabulary_richness = features.get('vocabulary_richness', 0.0)

            # Weighted combination - Higher weight for technical density
            score = (
                technical_density * 0.50 +  # Increased from 0.35
                is_technical * 0.20 +       # Increased from 0.15
                technical_term_norm * 0.10 + # Decreased from 0.15
                (is_ml_heavy + is_engineering_heavy + is_rag_specific) / 3 * 0.15 +
                vocabulary_richness * 0.05  # Decreased from 0.15
            )

            return min(1.0, score)

    def _calculate_question_score(self, features: Dict[str, Any]) -> float:
        """
        Calculate question type complexity score.

        Different question types have inherent complexity differences.
        """
        # Handle both formats
        if 'complexity' in features:
            # Test format - use complexity value directly
            return features.get('complexity', 0.0)
        else:
            # Full format
            # Base question complexity from extractor
            question_complexity = features.get('question_complexity', 0.0)

            # Specific question types
            is_comparison = features.get('is_comparison', 0.0)
            is_explanation = features.get('is_explanation', 0.0)
            is_implementation = features.get('is_implementation', 0.0)
            is_optimization = features.get('is_optimization', 0.0)
            is_debugging = features.get('is_debugging', 0.0)

            # Simple question indicators (negative contribution)
            is_what_is = features.get('is_what_is', 0.0)
            is_listing = features.get('is_listing', 0.0)

            # Multi-part questions
            has_multiple_questions = features.get('has_multiple_questions', 0.0)
            has_subquestions = features.get('has_subquestions', 0.0)

            # Calculate score (complex types increase, simple types decrease)
            complex_indicators = (
                is_comparison * 0.8 +
                is_explanation * 0.7 +
                is_implementation * 0.9 +
                is_optimization * 0.9 +
                is_debugging * 0.8
            ) / 5

            simple_indicators = (
                is_what_is * 0.3 +
                is_listing * 0.4
            ) / 2

            multipart_score = (
                has_multiple_questions * 0.8 +
                has_subquestions * 0.6
            ) / 2

            # Combine scores
            score = (
                question_complexity * 0.3 +
                complex_indicators * 0.4 +
                multipart_score * 0.2 +
                (1.0 - simple_indicators) * 0.1  # Inverted simple indicators
            )

            return min(1.0, max(0.0, score))

    def _calculate_ambiguity_score(self, features: Dict[str, Any]) -> float:
        """
        Calculate ambiguity contribution to complexity.

        More ambiguous queries may need better models to disambiguate.
        """
        # Handle both formats
        if 'score' in features:
            # Test format - use score value directly
            return features.get('score', 0.0)
        else:
            # Full format
            ambiguity_score = features.get('ambiguity_score', 0.0)
            has_pronouns = features.get('has_pronouns', 0.0)
            has_vague_quantifiers = features.get('has_vague_quantifiers', 0.0)
            has_unclear_references = features.get('has_unclear_references', 0.0)

            # Weighted combination
            score = (
                ambiguity_score * 0.5 +
                has_pronouns * 0.2 +
                has_vague_quantifiers * 0.15 +
                has_unclear_references * 0.15
            )

            return min(1.0, score)

    def _calculate_weighted_score(self, category_scores: Dict[str, float]) -> float:
        """
        Calculate weighted overall complexity score.

        Args:
            category_scores: Normalized scores by category

        Returns:
            Overall complexity score (0.0-1.0)
        """
        total_score = 0.0

        for category, weight in self.weights.items():
            score = category_scores.get(category, 0.0)
            total_score += score * weight

        # Ensure score is in valid range
        return min(1.0, max(0.0, total_score))

    def _determine_level(self, score: float) -> str:
        """
        Determine complexity level from score.

        Args:
            score: Overall complexity score (0.0-1.0)

        Returns:
            Complexity level: 'simple', 'medium', or 'complex'
        """
        if score < self.thresholds['simple']:
            return 'simple'
        elif score < self.thresholds['complex']:
            return 'medium'
        else:
            return 'complex'

    def _calculate_confidence(self, score: float) -> float:
        """
        Calculate confidence based on distance from thresholds.

        Higher confidence when score is far from decision boundaries.

        Args:
            score: Overall complexity score

        Returns:
            Confidence score (0.0-1.0)
        """
        # Calculate distances to thresholds
        simple_threshold = self.thresholds['simple']
        complex_threshold = self.thresholds['complex']

        distances = [
            abs(score - simple_threshold),
            abs(score - complex_threshold)
        ]
        min_distance = min(distances)

        # Map distance to confidence
        high_margin = self.confidence_params['high_confidence_margin']
        medium_margin = self.confidence_params['medium_confidence_margin']
        low_margin = self.confidence_params['low_confidence_margin']

        if min_distance >= high_margin:
            confidence = 0.95
        elif min_distance >= medium_margin:
            confidence = 0.85
        elif min_distance >= low_margin:
            confidence = 0.70
        else:
            # Linear interpolation for very close calls
            confidence = 0.55 + (min_distance / low_margin) * 0.15

        return confidence

    def _generate_reasoning(
        self,
        level: str,
        score: float,
        category_scores: Dict[str, float]
    ) -> str:
        """
        Generate human-readable reasoning for classification.

        Args:
            level: Determined complexity level
            score: Overall score
            category_scores: Breakdown by category

        Returns:
            Reasoning string
        """
        # Find dominant factors
        sorted_categories = sorted(
            category_scores.items(),
            key=lambda x: x[1] * self.weights.get(x[0], 0),
            reverse=True
        )

        top_factors = []
        for category, cat_score in sorted_categories[:2]:
            if cat_score > 0.5:
                top_factors.append(f"{category} ({cat_score:.2f})")

        reasoning = f"Classified as {level} (score: {score:.2f}). "

        if top_factors:
            reasoning += f"Primary factors: {', '.join(top_factors)}. "

        # Add level-specific insights
        if level == 'simple':
            reasoning += "Query appears to be a basic factual question or simple lookup."
        elif level == 'medium':
            reasoning += "Query requires moderate reasoning or technical understanding."
        else:
            reasoning += "Query involves complex analysis or deep technical knowledge."

        return reasoning

    def get_statistics(self) -> Dict[str, Any]:
        """Get classifier configuration statistics."""
        return {
            'weights': self.weights,
            'thresholds': self.thresholds,
            'confidence_params': self.confidence_params,
            'levels': ['simple', 'medium', 'complex']
        }
