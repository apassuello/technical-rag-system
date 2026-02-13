"""
Linguistic Complexity View for Epic 1 Multi-View Query Analyzer.

This view analyzes linguistic complexity through a hybrid approach:
- Algorithmic: Uses existing SyntacticParser for fast rule-based syntax analysis
- ML: Leverages DistilBERT for advanced linguistic pattern understanding
- Hybrid: Combines both approaches with configurable weighting

Key Features:
- DistilBERT integration for linguistic nuance detection
- Fast algorithmic fallback using syntactic patterns
- Clause depth and conjunction analysis
- Question complexity classification
- Configurable algorithmic/ML weighting
"""

import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from ..utils.syntactic_parser import SyntacticParser
from .base_view import HybridView

logger = logging.getLogger(__name__)


class LinguisticComplexityView(HybridView):
    """
    Linguistic Complexity View using DistilBERT + SyntacticParser.
    
    This view specializes in analyzing the linguistic complexity of queries by:
    1. Algorithmic analysis using syntactic patterns and grammatical structures
    2. ML analysis using DistilBERT for linguistic nuance understanding
    3. Hybrid combination with configurable weighting
    
    Performance Targets:
    - Algorithmic analysis: <3ms
    - ML analysis: <15ms (with model loaded)
    - Hybrid analysis: <20ms total
    - Accuracy: >80% linguistic complexity classification
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Linguistic Complexity View.
        
        Args:
            config: Configuration dictionary with optional parameters:
                - algorithmic_weight: Weight for algorithmic analysis (default: 0.4)
                - ml_weight: Weight for ML analysis (default: 0.6)
                - min_clause_complexity: Minimum clause count for complexity (default: 2)
                - enable_question_classification: Enable question type analysis (default: True)
                - distilbert_model_name: DistilBERT model name (default: 'distilbert-base-uncased')
        """
        # Configure weights - balanced approach for linguistic analysis
        config = config or {}
        config.setdefault('algorithmic_weight', 0.4)
        config.setdefault('ml_weight', 0.6)
        
        super().__init__(
            view_name='linguistic',
            ml_model_name=config.get('distilbert_model_name', 'distilbert-base-uncased'),
            config=config
        )
        
        # Configuration
        self.min_clause_complexity = self.config.get('min_clause_complexity', 2)
        self.enable_question_classification = self.config.get('enable_question_classification', True)
        
        logger.info(f"Initialized LinguisticComplexityView with weights: "
                   f"algorithmic={self.algorithmic_weight:.2f}, ml={self.ml_weight:.2f}")
    
    def _initialize_algorithmic_components(self) -> None:
        """Initialize algorithmic components for fast linguistic analysis."""
        try:
            # Initialize syntactic parser with existing patterns
            self.syntactic_parser = SyntacticParser()
            
            # Additional linguistic complexity indicators
            self.complexity_patterns = {
                'high': [
                    r'\b(nevertheless|nonetheless|furthermore|moreover|consequently|subsequently)\b',
                    r'\b(notwithstanding|inasmuch|insofar|whereas|albeit)\b',
                    r'\b(assuming|provided|supposing|considering|given)\b',
                    r'\b(conditional|hypothetical|subjunctive)\b',
                    r'(not only.*but also|either.*or|neither.*nor)',
                    r'(if.*then.*else|when.*then|should.*then)',
                ],
                'medium': [
                    r'\b(however|therefore|although|because|since|while|unless)\b',
                    r'\b(which|that|who|whom|whose|where|when|why|how)\b',
                    r'\b(compare|contrast|analyze|evaluate|determine)\b',
                    r'(and|but|or|so|yet)(?=.*[,;])',
                    r'\?.*\?',  # Multiple questions
                ],
                'basic': [
                    r'\b(what|is|are|does|do|can|will|how|why)\b',
                    r'^(list|name|show|tell|give)\s',
                    r'\b(simple|basic|explain)\b'
                ]
            }
            
            # Question complexity levels
            self.question_complexity = {
                'analytical': ['analyze', 'evaluate', 'compare', 'contrast', 'assess', 'critique'],
                'synthetic': ['design', 'create', 'develop', 'formulate', 'construct', 'propose'],
                'comprehension': ['explain', 'describe', 'summarize', 'interpret', 'clarify'],
                'factual': ['what', 'when', 'where', 'who', 'list', 'name', 'define']
            }
            
            # Compile patterns for efficiency
            self._compile_complexity_patterns()
            
            logger.debug("Initialized algorithmic components for linguistic analysis")
            
        except Exception as e:
            logger.error(f"Failed to initialize algorithmic components: {e}")
            raise
    
    def _initialize_ml_components(self) -> None:
        """Initialize ML components for DistilBERT analysis."""
        try:
            # DistilBERT will be lazy-loaded via ModelManager
            self._distilbert_model = None
            
            # Linguistic complexity anchors for similarity comparison
            self.linguistic_anchors = {
                'high_complexity': [
                    "Analyze the intricate relationships between multiple interconnected variables while considering the underlying assumptions and potential confounding factors that might influence the observed correlations.",
                    "Evaluate the comparative effectiveness of alternative methodological approaches, taking into account their respective advantages, limitations, and contextual applicability.",
                    "Synthesize information from diverse sources to construct a comprehensive framework that addresses both theoretical foundations and practical implementation challenges.",
                    "Examine the multifaceted implications of implementing such a system, considering not only immediate technical requirements but also long-term maintenance and scalability concerns.",
                    "Critically assess the validity of the proposed solution by systematically identifying potential weaknesses, alternative interpretations, and areas requiring further investigation."
                ],
                'medium_complexity': [
                    "Compare and contrast the main features of these two approaches, highlighting their key differences and similarities.",
                    "Explain how this process works, including the sequential steps involved and the rationale behind each decision point.",
                    "Describe the relationship between these concepts and provide examples that illustrate their practical applications.",
                    "Analyze the factors that contribute to this phenomenon and discuss their relative importance in different contexts.",
                    "Evaluate the advantages and disadvantages of this method, considering both technical and practical perspectives."
                ],
                'low_complexity': [
                    "What is machine learning and how does it work in simple terms?",
                    "List the basic components needed to build a web application.",
                    "Define the term 'database' and explain its primary purpose.",
                    "How do you install Python on a computer?",
                    "What are the main differences between supervised and unsupervised learning?"
                ]
            }
            
            # Cached embeddings for linguistic anchors
            self._anchor_embeddings = {}
            
            # Linguistic features to analyze in embeddings
            self.linguistic_features = {
                'complexity_markers': ['complex', 'intricate', 'sophisticated', 'elaborate'],
                'analytical_verbs': ['analyze', 'evaluate', 'assess', 'examine', 'critique'],
                'connective_words': ['however', 'therefore', 'consequently', 'furthermore', 'nevertheless'],
                'qualification_words': ['might', 'could', 'potentially', 'presumably', 'arguably']
            }
            
            logger.debug("Initialized ML components for DistilBERT analysis")
            
        except Exception as e:
            logger.error(f"Failed to initialize ML components: {e}")
            raise
    
    def _compile_complexity_patterns(self) -> None:
        """Compile regex patterns for efficient matching."""
        self._compiled_patterns = {}
        
        for complexity_level, patterns in self.complexity_patterns.items():
            compiled_patterns = []
            for pattern in patterns:
                try:
                    compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern}': {e}")
            self._compiled_patterns[complexity_level] = compiled_patterns
    
    def _analyze_algorithmic(self, query: str) -> Dict[str, Any]:
        """
        Perform fast algorithmic analysis using syntactic patterns.
        
        Args:
            query: Query text to analyze
            
        Returns:
            Dictionary with score, confidence, features, and metadata
        """
        try:
            query_lower = query.lower().strip()
            
            # 1. Use existing syntactic parser for structural analysis
            syntactic_analysis = self.syntactic_parser.analyze_complexity(query)
            
            # 2. Pattern-based complexity analysis
            complexity_scores = self._analyze_complexity_patterns(query_lower)
            
            # 3. Question type classification
            question_analysis = self._classify_question_complexity(query_lower) if self.enable_question_classification else {}
            
            # 4. Linguistic structure analysis
            structure_analysis = self._analyze_linguistic_structure(query)
            
            # 5. Calculate base complexity score
            # Weight different analysis components
            syntactic_score = syntactic_analysis.get('complexity_score', 0.5)
            pattern_score = self._calculate_pattern_score(complexity_scores)
            question_score = question_analysis.get('complexity_score', 0.5)
            structure_score = structure_analysis.get('complexity_score', 0.5)
            
            # Weighted combination
            final_score = (
                syntactic_score * 0.3 +
                pattern_score * 0.25 +
                question_score * 0.25 +
                structure_score * 0.2
            )
            
            # 6. Confidence based on consistency and feature coverage
            confidence = self._calculate_algorithmic_confidence(
                syntactic_analysis, complexity_scores, question_analysis, structure_analysis
            )
            
            # 7. Features for explainability
            features = {
                'syntactic_analysis': syntactic_analysis,
                'complexity_patterns': complexity_scores,
                'question_analysis': question_analysis,
                'structure_analysis': structure_analysis,
                'component_scores': {
                    'syntactic': syntactic_score,
                    'pattern': pattern_score,
                    'question': question_score,
                    'structure': structure_score
                }
            }
            
            # 8. Metadata
            metadata = {
                'analysis_method': 'algorithmic_linguistic_patterns',
                'syntactic_complexity': syntactic_analysis.get('clause_count', 0),
                'question_type': question_analysis.get('question_type', 'unknown'),
                'sentence_count': structure_analysis.get('sentence_count', 1),
                'avg_sentence_length': structure_analysis.get('avg_sentence_length', 0)
            }
            
            logger.debug(f"Algorithmic linguistic analysis: score={final_score:.3f}, "
                        f"confidence={confidence:.3f}, clauses={syntactic_analysis.get('clause_count', 0)}")
            
            return {
                'score': max(0.0, min(1.0, final_score)),
                'confidence': confidence,
                'features': features,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Algorithmic linguistic analysis failed: {e}")
            # Return safe fallback
            return {
                'score': 0.5,
                'confidence': 0.3,
                'features': {'error': str(e)},
                'metadata': {'analysis_method': 'algorithmic_fallback'}
            }
    
    def _analyze_complexity_patterns(self, query: str) -> Dict[str, int]:
        """Analyze complexity patterns in query."""
        pattern_matches = {
            'high': 0,
            'medium': 0,
            'basic': 0
        }
        
        for complexity_level, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                matches = len(pattern.findall(query))
                pattern_matches[complexity_level] += matches
        
        return pattern_matches
    
    def _classify_question_complexity(self, query: str) -> Dict[str, Any]:
        """Classify question complexity."""
        question_info = {
            'is_question': '?' in query or query.startswith(tuple(['what', 'how', 'why', 'when', 'where', 'who', 'which'])),
            'question_type': 'unknown',
            'complexity_score': 0.5
        }
        
        if not question_info['is_question']:
            return question_info
        
        # Analyze question words and verbs to determine complexity
        for complexity_level, verbs in self.question_complexity.items():
            for verb in verbs:
                if verb in query:
                    question_info['question_type'] = complexity_level
                    # Assign complexity scores: analytical=0.9, synthetic=0.8, comprehension=0.6, factual=0.3
                    complexity_mapping = {
                        'analytical': 0.9,
                        'synthetic': 0.8,
                        'comprehension': 0.6,
                        'factual': 0.3
                    }
                    question_info['complexity_score'] = complexity_mapping.get(complexity_level, 0.5)
                    break
            
            if question_info['question_type'] != 'unknown':
                break
        
        return question_info
    
    def _analyze_linguistic_structure(self, query: str) -> Dict[str, Any]:
        """Analyze linguistic structure of query."""
        sentences = re.split(r'[.!?]+', query)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            sentences = [query]
        
        sentence_lengths = [len(s.split()) for s in sentences]
        avg_length = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
        
        # Calculate structure complexity
        # Longer sentences and more sentences generally indicate higher complexity
        length_complexity = min(avg_length / 15.0, 1.0)  # Normalize to sentence length of 15 words
        sentence_complexity = min(len(sentences) / 3.0, 1.0)  # Normalize to 3 sentences
        
        structure_score = (length_complexity * 0.6 + sentence_complexity * 0.4)
        
        return {
            'sentence_count': len(sentences),
            'avg_sentence_length': avg_length,
            'max_sentence_length': max(sentence_lengths) if sentence_lengths else 0,
            'complexity_score': structure_score
        }
    
    def _calculate_pattern_score(self, pattern_matches: Dict[str, int]) -> float:
        """Calculate score from pattern matches."""
        # Weight pattern matches by complexity level - with safe defaults
        weighted_score = (
            pattern_matches.get('high', 0) * 1.0 +
            pattern_matches.get('medium', 0) * 0.6 +
            pattern_matches.get('basic', 0) * 0.2
        )

        # Normalize by total patterns (arbitrary cap at 5 for normalization)
        return min(weighted_score / 5.0, 1.0)
    
    def _calculate_algorithmic_confidence(
        self, syntactic: Dict, patterns: Dict, questions: Dict, structure: Dict
    ) -> float:
        """Calculate confidence based on algorithmic analysis consistency."""
        # Base confidence
        confidence = 0.5
        
        # Boost from syntactic analysis quality
        if syntactic.get('clause_count', 0) > 0:
            confidence += 0.15
        
        # Boost from pattern matches
        total_patterns = sum(patterns.values())
        if total_patterns > 0:
            confidence += min(total_patterns * 0.1, 0.2)
        
        # Boost from question classification
        if questions.get('question_type') != 'unknown':
            confidence += 0.1
        
        # Boost from structure analysis
        if structure.get('sentence_count', 0) > 1:
            confidence += 0.05
        
        return min(confidence, 0.85)  # Cap algorithmic confidence at 85%
    
    def _analyze_ml(self, query: str) -> Dict[str, Any]:
        """
        Perform ML analysis using DistilBERT for linguistic understanding.
        
        Args:
            query: Query text to analyze
            
        Returns:
            Dictionary with score, confidence, features, and metadata
        """
        try:
            # Ensure DistilBERT model is available
            if not self._distilbert_model:
                if not self.model_manager:
                    raise ValueError("ModelManager not set - cannot load DistilBERT")
                
                # Load DistilBERT model through ModelManager
                self._distilbert_model = self.model_manager.get_model(self.ml_model_name)
                if not self._distilbert_model:
                    raise ValueError(f"Failed to load DistilBERT model: {self.ml_model_name}")
            
            # 1. Generate query embedding
            query_embedding = self._get_query_embedding(query)
            
            # 2. Compare with linguistic complexity anchors
            anchor_similarities = self._compute_anchor_similarities(query_embedding)
            
            # 3. Analyze linguistic features in embedding space
            linguistic_features = self._analyze_linguistic_features(query, query_embedding)
            
            # 4. Calculate complexity score based on ML analysis
            complexity_score = self._calculate_ml_complexity_score(anchor_similarities, linguistic_features)
            
            # 5. Estimate confidence based on ML analysis quality
            confidence = self._calculate_ml_confidence(query_embedding, anchor_similarities, linguistic_features)
            
            # 6. Extract ML features for explainability
            features = {
                'query_embedding_norm': float(np.linalg.norm(query_embedding)),
                'anchor_similarities': anchor_similarities,
                'linguistic_features': linguistic_features,
                'embedding_dimensionality': query_embedding.shape[0] if hasattr(query_embedding, 'shape') else len(query_embedding)
            }
            
            # 7. ML-specific metadata
            metadata = {
                'analysis_method': 'ml_distilbert',
                'model_name': self.ml_model_name,
                'embedding_model': 'DistilBERT',
                'high_complexity_similarity': anchor_similarities.get('high_complexity', 0.0),
                'medium_complexity_similarity': anchor_similarities.get('medium_complexity', 0.0),
                'low_complexity_similarity': anchor_similarities.get('low_complexity', 0.0),
                'linguistic_feature_strength': linguistic_features.get('feature_strength', 0.0)
            }
            
            logger.debug(f"ML linguistic analysis: score={complexity_score:.3f}, "
                        f"confidence={confidence:.3f}, model={self.ml_model_name}")
            
            return {
                'score': complexity_score,
                'confidence': confidence,
                'features': features,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"ML linguistic analysis failed: {e}")
            # Return conservative fallback
            return {
                'score': 0.6,  # Assume medium complexity when uncertain
                'confidence': 0.4,
                'features': {'error': str(e)},
                'metadata': {'analysis_method': 'ml_fallback', 'error': str(e)}
            }
    
    def _get_query_embedding(self, query: str) -> np.ndarray:
        """Get DistilBERT embedding for query."""
        try:
            # Handle model format - could be direct model or dict from ModelManager
            model = self._distilbert_model
            tokenizer = None
            
            if isinstance(self._distilbert_model, dict):
                model = self._distilbert_model.get('model')
                tokenizer = self._distilbert_model.get('tokenizer')
            
            # Use the model's encode method (standard for sentence-transformers)
            if hasattr(model, 'encode'):
                embedding = model.encode(query, convert_to_numpy=True)
            elif hasattr(model, 'embed'):
                embedding = model.embed([query])[0]
            elif tokenizer is not None:
                # Use transformers model with tokenizer from ModelManager
                import torch
                inputs = tokenizer(query, return_tensors="pt", truncation=True, max_length=512)
                with torch.no_grad():
                    outputs = model(**inputs)
                    embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
            else:
                # Fallback for direct transformer models (legacy)
                inputs = self._distilbert_model.tokenizer(query, return_tensors="pt", truncation=True, max_length=512)
                with torch.no_grad():
                    outputs = self._distilbert_model(**inputs)
                    embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to get DistilBERT embedding: {e}")
            # Return zero embedding as fallback
            return np.zeros(768)  # Standard DistilBERT embedding size
    
    def _compute_anchor_similarities(self, query_embedding: np.ndarray) -> Dict[str, float]:
        """Compute similarities to linguistic complexity anchors."""
        similarities = {}
        
        try:
            for complexity_level, anchor_texts in self.linguistic_anchors.items():
                level_similarities = []
                
                for anchor_text in anchor_texts:
                    # Get or compute anchor embedding
                    if anchor_text not in self._anchor_embeddings:
                        self._anchor_embeddings[anchor_text] = self._get_query_embedding(anchor_text)
                    
                    anchor_embedding = self._anchor_embeddings[anchor_text]
                    
                    # Compute cosine similarity
                    similarity = self._cosine_similarity(query_embedding, anchor_embedding)
                    level_similarities.append(similarity)
                
                # Use maximum similarity for this complexity level
                similarities[complexity_level] = max(level_similarities) if level_similarities else 0.0
            
        except Exception as e:
            logger.warning(f"Failed to compute anchor similarities: {e}")
            # Return safe defaults
            similarities = {
                'high_complexity': 0.3,
                'medium_complexity': 0.5,
                'low_complexity': 0.7
            }
        
        return similarities
    
    def _analyze_linguistic_features(self, query: str, embedding: np.ndarray) -> Dict[str, Any]:
        """Analyze linguistic features in the query and embedding."""
        try:
            features = {}
            
            # 1. Embedding-based feature analysis
            embedding_magnitude = float(np.linalg.norm(embedding))
            features['embedding_magnitude'] = embedding_magnitude
            
            # 2. Linguistic complexity indicators in text
            complexity_indicators = 0
            for category, words in self.linguistic_features.items():
                category_matches = sum(1 for word in words if word in query.lower())
                features[f'{category}_count'] = category_matches
                complexity_indicators += category_matches
            
            features['total_complexity_indicators'] = complexity_indicators
            
            # 3. Embedding distribution analysis
            embedding_std = float(np.std(embedding))
            embedding_mean = float(np.mean(embedding))
            features['embedding_std'] = embedding_std
            features['embedding_mean'] = embedding_mean
            
            # 4. Overall feature strength
            text_feature_strength = min(complexity_indicators / 10.0, 1.0)  # Normalize
            embedding_feature_strength = min(embedding_magnitude / 15.0, 1.0)  # Normalize
            
            feature_strength = (text_feature_strength * 0.6 + embedding_feature_strength * 0.4)
            features['feature_strength'] = feature_strength
            
            return features
            
        except Exception as e:
            logger.warning(f"Linguistic feature analysis failed: {e}")
            return {
                'embedding_magnitude': 1.0,
                'total_complexity_indicators': 0,
                'embedding_std': 0.1,
                'embedding_mean': 0.0,
                'feature_strength': 0.5
            }
    
    def _calculate_ml_complexity_score(
        self, 
        anchor_similarities: Dict[str, float], 
        linguistic_features: Dict[str, Any]
    ) -> float:
        """Calculate complexity score from ML features."""
        try:
            # Weight similarities by complexity level
            complexity_weights = {
                'high_complexity': 1.0,
                'medium_complexity': 0.6,
                'low_complexity': 0.2
            }
            
            # Weighted average of similarities
            weighted_similarity = sum(
                anchor_similarities.get(level, 0.0) * weight
                for level, weight in complexity_weights.items()
            ) / sum(complexity_weights.values())
            
            # Feature strength contribution
            feature_contribution = linguistic_features.get('feature_strength', 0.5) * 0.3
            
            # Combined score
            ml_score = min(weighted_similarity * 0.7 + feature_contribution, 1.0)
            
            return max(0.0, ml_score)
            
        except Exception as e:
            logger.warning(f"ML complexity score calculation failed: {e}")
            return 0.5
    
    def _calculate_ml_confidence(
        self, 
        embedding: np.ndarray, 
        similarities: Dict[str, float], 
        features: Dict[str, Any]
    ) -> float:
        """Calculate confidence based on ML analysis quality."""
        try:
            # Base confidence from embedding quality
            embedding_quality = min(np.linalg.norm(embedding) / 20.0, 0.4)
            
            # Confidence from similarity clarity
            max_similarity = max(similarities.values()) if similarities else 0.0
            similarity_confidence = max_similarity * 0.3
            
            # Confidence from feature strength
            feature_confidence = features.get('feature_strength', 0.0) * 0.2
            
            # Combined confidence
            total_confidence = embedding_quality + similarity_confidence + feature_confidence + 0.1  # Base
            
            return min(max(total_confidence, 0.0), 0.95)  # Cap at 95% for ML analysis
            
        except Exception as e:
            logger.warning(f"ML confidence calculation failed: {e}")
            return 0.6
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            # Handle potential dimension mismatches
            if len(vec1) != len(vec2):
                min_len = min(len(vec1), len(vec2))
                vec1 = vec1[:min_len]
                vec2 = vec2[:min_len]
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # Ensure result is in valid range
            return max(-1.0, min(1.0, float(similarity)))
            
        except Exception as e:
            logger.warning(f"Cosine similarity calculation failed: {e}")
            return 0.0