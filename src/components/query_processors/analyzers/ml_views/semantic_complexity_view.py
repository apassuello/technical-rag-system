"""
Semantic Complexity View for Epic 1 Multi-View Query Analyzer.

This view analyzes semantic complexity through a hybrid approach:
- Algorithmic: Uses keyword analysis and semantic patterns for fast semantic assessment
- ML: Leverages Sentence-BERT for advanced semantic relationship understanding
- Hybrid: Combines both approaches with configurable weighting

Key Features:
- Sentence-BERT integration for semantic nuance detection
- Fast algorithmic fallback using semantic keywords and patterns
- Conceptual relationship analysis
- Domain knowledge complexity assessment
- Configurable algorithmic/ML weighting
"""

import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Set

import numpy as np
import torch

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from .base_view import HybridView

logger = logging.getLogger(__name__)


class SemanticComplexityView(HybridView):
    """
    Semantic Complexity View using Sentence-BERT + Semantic Pattern Analysis.
    
    This view specializes in analyzing the semantic complexity of queries by:
    1. Algorithmic analysis using semantic keywords and conceptual patterns
    2. ML analysis using Sentence-BERT for semantic relationship understanding
    3. Hybrid combination with configurable weighting
    
    Performance Targets:
    - Algorithmic analysis: <3ms
    - ML analysis: <18ms (with model loaded)
    - Hybrid analysis: <22ms total
    - Accuracy: >80% semantic complexity classification
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Semantic Complexity View.
        
        Args:
            config: Configuration dictionary with optional parameters:
                - algorithmic_weight: Weight for algorithmic analysis (default: 0.4)
                - ml_weight: Weight for ML analysis (default: 0.6)
                - min_concept_count: Minimum concepts for complex classification (default: 3)
                - enable_relationship_analysis: Enable relationship pattern analysis (default: True)
                - sentence_bert_model_name: Sentence-BERT model name (default: 'all-MiniLM-L6-v2')
        """
        # Configure weights - favor ML for semantic analysis
        config = config or {}
        config.setdefault('algorithmic_weight', 0.4)
        config.setdefault('ml_weight', 0.6)
        
        super().__init__(
            view_name='semantic',
            ml_model_name=config.get('sentence_bert_model_name', 'sentence-transformers/all-MiniLM-L6-v2'),
            config=config
        )
        
        # Configuration
        self.min_concept_count = self.config.get('min_concept_count', 3)
        self.enable_relationship_analysis = self.config.get('enable_relationship_analysis', True)
        
        logger.info(f"Initialized SemanticComplexityView with weights: "
                   f"algorithmic={self.algorithmic_weight:.2f}, ml={self.ml_weight:.2f}")
    
    def _initialize_algorithmic_components(self) -> None:
        """Initialize algorithmic components for fast semantic analysis."""
        try:
            # Semantic complexity indicators by category
            self.semantic_categories = {
                'abstract_concepts': {
                    'keywords': [
                        'theory', 'concept', 'principle', 'paradigm', 'philosophy', 'methodology',
                        'framework', 'abstraction', 'generalization', 'conceptualization',
                        'ideological', 'theoretical', 'conceptual', 'philosophical', 'strategic'
                    ],
                    'weight': 0.8,
                    'description': 'Abstract theoretical concepts'
                },
                'relationships': {
                    'keywords': [
                        'relationship', 'correlation', 'causation', 'dependency', 'association',
                        'interaction', 'connection', 'linkage', 'interdependence', 'influence',
                        'affects', 'impacts', 'relates', 'connected', 'associated'
                    ],
                    'weight': 0.7,
                    'description': 'Conceptual relationships and connections'
                },
                'multi_domain': {
                    'keywords': [
                        'interdisciplinary', 'cross-domain', 'multifaceted', 'holistic', 'comprehensive',
                        'integrative', 'multidimensional', 'systemic', 'ecosystem', 'synergy',
                        'convergence', 'intersection', 'confluence', 'amalgamation'
                    ],
                    'weight': 0.9,
                    'description': 'Multi-domain or interdisciplinary concepts'
                },
                'complex_modifiers': {
                    'keywords': [
                        'complex', 'sophisticated', 'intricate', 'elaborate', 'nuanced',
                        'subtle', 'implicit', 'latent', 'underlying', 'fundamental',
                        'inherent', 'intrinsic', 'emergent', 'contextual', 'conditional'
                    ],
                    'weight': 0.6,
                    'description': 'Complexity-indicating modifiers'
                },
                'cognitive_processes': {
                    'keywords': [
                        'reasoning', 'inference', 'deduction', 'induction', 'synthesis',
                        'analysis', 'interpretation', 'understanding', 'comprehension', 'insight',
                        'intuition', 'perception', 'cognition', 'metacognition', 'awareness'
                    ],
                    'weight': 0.7,
                    'description': 'Cognitive and mental processes'
                }
            }
            
            # Semantic relationship patterns
            self.relationship_patterns = {
                'causal': [
                    r'causes?', r'results? in', r'leads? to', r'triggers?', r'induces?',
                    r'brings? about', r'produces?', r'generates?', r'creates?'
                ],
                'comparative': [
                    r'compared? (?:to|with)', r'versus', r'vs\.?', r'differs? from',
                    r'similar to', r'like', r'unlike', r'contrasts? with'
                ],
                'conditional': [
                    r'if.*then', r'assuming', r'provided', r'given that', r'under.*conditions?',
                    r'depends? on', r'conditional', r'contingent'
                ],
                'temporal': [
                    r'before.*after', r'during.*while', r'simultaneously', r'concurrently',
                    r'sequence', r'temporal', r'chronological'
                ]
            }
            
            # Conceptual depth indicators
            self.depth_indicators = {
                'surface': ['what', 'when', 'where', 'who', 'which', 'list', 'name'],
                'intermediate': ['how', 'why', 'describe', 'explain', 'compare', 'contrast'],
                'deep': ['analyze', 'synthesize', 'evaluate', 'theorize', 'conceptualize', 'philosophize']
            }
            
            # Compile patterns for efficiency
            self._compile_semantic_patterns()
            
            logger.debug("Initialized algorithmic components for semantic analysis")
            
        except Exception as e:
            logger.error(f"Failed to initialize algorithmic components: {e}")
            raise
    
    def _initialize_ml_components(self) -> None:
        """Initialize ML components for Sentence-BERT analysis."""
        try:
            # Sentence-BERT will be lazy-loaded via ModelManager
            self._sentence_bert_model = None
            
            # Semantic complexity anchors for similarity comparison
            self.semantic_anchors = {
                'high_complexity': [
                    "Explore the nuanced interplay between theoretical frameworks and practical implementations, considering the epistemological foundations and ontological assumptions that underlie different methodological approaches.",
                    "Examine the multifaceted relationships between cognitive processes, contextual factors, and emergent properties within complex adaptive systems.",
                    "Analyze the philosophical implications of interdisciplinary convergence and the synthesis of disparate conceptual paradigms in contemporary research.",
                    "Investigate the subtle dynamics between implicit knowledge structures and explicit reasoning mechanisms in human cognition.",
                    "Consider the intricate web of causal relationships and feedback loops that characterize complex phenomena across multiple domains of inquiry."
                ],
                'medium_complexity': [
                    "Compare the theoretical foundations of different approaches and analyze their practical implications for implementation.",
                    "Examine the relationship between conceptual frameworks and their application in real-world scenarios.",
                    "Analyze how different factors interact to influence outcomes in complex systems.",
                    "Explore the connections between abstract principles and concrete implementations.",
                    "Investigate the underlying mechanisms that drive observable patterns in data."
                ],
                'low_complexity': [
                    "What is the basic definition of machine learning?",
                    "List the main components of a neural network.",
                    "Describe how a database stores information.",
                    "Explain what an algorithm does in simple terms.",
                    "Name the different types of data structures."
                ]
            }
            
            # Semantic domain anchors for conceptual clustering
            self.domain_anchors = {
                'abstract_theoretical': [
                    "theoretical frameworks and philosophical foundations",
                    "conceptual paradigms and methodological approaches",
                    "epistemological and ontological considerations"
                ],
                'relational_analytical': [
                    "relationships between concepts and their interactions",
                    "causal mechanisms and dependency structures",
                    "comparative analysis of different approaches"
                ],
                'concrete_practical': [
                    "specific implementation details and procedures",
                    "practical applications and real-world examples",
                    "step-by-step instructions and guidelines"
                ]
            }
            
            # Cached embeddings for semantic anchors
            self._anchor_embeddings = {}
            
            logger.debug("Initialized ML components for Sentence-BERT analysis")
            
        except Exception as e:
            logger.error(f"Failed to initialize ML components: {e}")
            raise
    
    def _compile_semantic_patterns(self) -> None:
        """Compile regex patterns for efficient matching."""
        self._compiled_relationship_patterns = {}
        
        for relationship_type, patterns in self.relationship_patterns.items():
            compiled_patterns = []
            for pattern in patterns:
                try:
                    compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern}': {e}")
            self._compiled_relationship_patterns[relationship_type] = compiled_patterns
    
    def _analyze_algorithmic(self, query: str) -> Dict[str, Any]:
        """
        Perform fast algorithmic analysis using semantic keywords and patterns.
        
        Args:
            query: Query text to analyze
            
        Returns:
            Dictionary with score, confidence, features, and metadata
        """
        try:
            query_lower = query.lower().strip()
            query_words = set(query_lower.split())
            
            # 1. Semantic category analysis
            category_analysis = self._analyze_semantic_categories(query_lower, query_words)
            
            # 2. Relationship pattern analysis
            relationship_analysis = self._analyze_relationship_patterns(query_lower) if self.enable_relationship_analysis else {}
            
            # 3. Conceptual depth analysis
            depth_analysis = self._analyze_conceptual_depth(query_lower)
            
            # 4. Multi-concept analysis
            concept_analysis = self._analyze_concept_density(query_lower, query_words)
            
            # 5. Calculate semantic complexity score
            final_score = self._calculate_semantic_complexity_score(
                category_analysis, relationship_analysis, depth_analysis, concept_analysis
            )
            
            # 6. Calculate confidence
            confidence = self._calculate_algorithmic_confidence(
                category_analysis, relationship_analysis, depth_analysis, concept_analysis
            )
            
            # 7. Features for explainability
            features = {
                'semantic_categories': category_analysis,
                'relationship_patterns': relationship_analysis,
                'conceptual_depth': depth_analysis,
                'concept_analysis': concept_analysis,
                'query_word_count': len(query_words),
                'unique_concepts': len(set(w for w in query_words if len(w) > 3))
            }
            
            # 8. Metadata
            metadata = {
                'analysis_method': 'algorithmic_semantic_patterns',
                'primary_category': category_analysis.get('dominant_category', 'unknown'),
                'conceptual_depth': depth_analysis.get('depth_level', 'intermediate'),
                'relationship_types': list(relationship_analysis.get('detected_patterns', {}).keys()),
                'concept_density': concept_analysis.get('concept_density', 0.0),
                'semantic_indicators': category_analysis.get('total_indicators', 0)
            }
            
            logger.debug(f"Algorithmic semantic analysis: score={final_score:.3f}, "
                        f"confidence={confidence:.3f}, "
                        f"category={category_analysis.get('dominant_category', 'unknown')}, "
                        f"depth={depth_analysis.get('depth_level', 'intermediate')}")
            
            return {
                'score': max(0.0, min(1.0, final_score)),
                'confidence': confidence,
                'features': features,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Algorithmic semantic analysis failed: {e}")
            return {
                'score': 0.5,
                'confidence': 0.3,
                'features': {'error': str(e)},
                'metadata': {'analysis_method': 'algorithmic_fallback'}
            }
    
    def _analyze_semantic_categories(self, query: str, query_words: Set[str]) -> Dict[str, Any]:
        """Analyze semantic categories in the query."""
        category_scores = {}
        total_indicators = 0
        
        for category, data in self.semantic_categories.items():
            matches = 0
            matched_keywords = []
            
            for keyword in data['keywords']:
                if keyword in query:
                    matches += 1
                    matched_keywords.append(keyword)
                    total_indicators += 1
            
            category_scores[category] = {
                'matches': matches,
                'weighted_score': matches * data['weight'],
                'matched_keywords': matched_keywords
            }
        
        # Find dominant category
        if category_scores:
            dominant_category = max(
                category_scores.items(), 
                key=lambda x: x[1]['weighted_score']
            )[0]
            dominant_score = category_scores[dominant_category]['weighted_score']
        else:
            dominant_category = 'unknown'
            dominant_score = 0.0
        
        return {
            'category_scores': category_scores,
            'dominant_category': dominant_category,
            'dominant_score': dominant_score,
            'total_indicators': total_indicators
        }
    
    def _analyze_relationship_patterns(self, query: str) -> Dict[str, Any]:
        """Analyze relationship patterns in the query."""
        detected_patterns = {}
        total_patterns = 0
        
        for pattern_type, compiled_patterns in self._compiled_relationship_patterns.items():
            pattern_matches = 0
            for pattern in compiled_patterns:
                matches = len(pattern.findall(query))
                pattern_matches += matches
                total_patterns += matches
            
            if pattern_matches > 0:
                detected_patterns[pattern_type] = pattern_matches
        
        # Calculate relationship complexity
        relationship_complexity = min(total_patterns * 0.2, 1.0)
        
        return {
            'detected_patterns': detected_patterns,
            'total_patterns': total_patterns,
            'relationship_complexity': relationship_complexity,
            'has_relationships': total_patterns > 0
        }
    
    def _analyze_conceptual_depth(self, query: str) -> Dict[str, Any]:
        """Analyze conceptual depth of the query."""
        depth_scores = {
            'surface': 0,
            'intermediate': 0,
            'deep': 0
        }
        
        for depth_level, indicators in self.depth_indicators.items():
            for indicator in indicators:
                if indicator in query:
                    depth_scores[depth_level] += 1
        
        # Determine primary depth level
        if depth_scores['deep'] > 0:
            depth_level = 'deep'
            depth_score = 0.9
        elif depth_scores['intermediate'] > depth_scores['surface']:
            depth_level = 'intermediate'
            depth_score = 0.6
        elif depth_scores['surface'] > 0:
            depth_level = 'surface'
            depth_score = 0.3
        else:
            depth_level = 'intermediate'  # Default
            depth_score = 0.5
        
        return {
            'depth_scores': depth_scores,
            'depth_level': depth_level,
            'depth_score': depth_score,
            'total_indicators': sum(depth_scores.values())
        }
    
    def _analyze_concept_density(self, query: str, query_words: Set[str]) -> Dict[str, Any]:
        """Analyze density of concepts in the query."""
        # Count potential concepts (words longer than 3 characters, excluding common words)
        common_words = {
            'the', 'and', 'but', 'for', 'with', 'from', 'that', 'this', 'they', 'them',
            'what', 'when', 'where', 'which', 'who', 'how', 'why', 'can', 'will', 'would'
        }
        
        potential_concepts = [
            word for word in query_words 
            if len(word) > 3 and word not in common_words and word.isalpha()
        ]
        
        concept_count = len(potential_concepts)
        concept_density = concept_count / max(len(query_words), 1)
        
        # Identify domain-specific concepts (using simple heuristics)
        domain_concepts = [
            word for word in potential_concepts
            if any(
                keyword in word for category in self.semantic_categories.values()
                for keyword in category['keywords']
            )
        ]
        
        complexity_boost = 0.0
        if concept_count >= self.min_concept_count:
            complexity_boost = min((concept_count - self.min_concept_count) * 0.1, 0.3)
        
        return {
            'concept_count': concept_count,
            'concept_density': concept_density,
            'domain_concepts': domain_concepts,
            'domain_concept_count': len(domain_concepts),
            'complexity_boost': complexity_boost,
            'is_concept_rich': concept_count >= self.min_concept_count
        }
    
    def _calculate_semantic_complexity_score(
        self, categories: Dict, relationships: Dict, depth: Dict, concepts: Dict
    ) -> float:
        """Calculate overall semantic complexity score."""
        # Component scores
        category_score = min(categories.get('dominant_score', 0.0) / 5.0, 1.0)  # Normalize
        relationship_score = relationships.get('relationship_complexity', 0.0)
        depth_score = depth.get('depth_score', 0.5)
        concept_boost = concepts.get('complexity_boost', 0.0)
        
        # Weighted combination
        final_score = (
            category_score * 0.3 +
            relationship_score * 0.25 +
            depth_score * 0.35 +
            concept_boost  # Additional boost
        )
        
        return min(final_score, 1.0)
    
    def _calculate_algorithmic_confidence(
        self, categories: Dict, relationships: Dict, depth: Dict, concepts: Dict
    ) -> float:
        """Calculate confidence based on semantic pattern matching quality."""
        confidence = 0.4  # Base confidence
        
        # Boost from semantic categories
        total_indicators = categories.get('total_indicators', 0)
        if total_indicators > 0:
            confidence += min(total_indicators * 0.05, 0.2)
        
        # Boost from relationship patterns
        if relationships.get('has_relationships', False):
            confidence += min(relationships.get('total_patterns', 0) * 0.05, 0.15)
        
        # Boost from conceptual depth
        depth_level = depth.get('depth_level', 'intermediate')
        if depth_level == 'deep':
            confidence += 0.15
        elif depth_level == 'intermediate':
            confidence += 0.1
        
        # Boost from concept richness
        if concepts.get('is_concept_rich', False):
            confidence += 0.1
        
        return min(confidence, 0.85)  # Cap algorithmic confidence at 85%
    
    def _analyze_ml(self, query: str) -> Dict[str, Any]:
        """
        Perform ML analysis using Sentence-BERT for semantic understanding.
        
        Args:
            query: Query text to analyze
            
        Returns:
            Dictionary with score, confidence, features, and metadata
        """
        try:
            # Ensure Sentence-BERT model is available
            if not self._sentence_bert_model:
                if not self.model_manager:
                    raise ValueError("ModelManager not set - cannot load Sentence-BERT")
                
                # Load Sentence-BERT model through ModelManager
                self._sentence_bert_model = self.model_manager.get_model(self.ml_model_name)
                if not self._sentence_bert_model:
                    raise ValueError(f"Failed to load Sentence-BERT model: {self.ml_model_name}")
            
            # 1. Generate query embedding
            query_embedding = self._get_query_embedding(query)
            
            # 2. Compare with semantic complexity anchors
            anchor_similarities = self._compute_anchor_similarities(query_embedding)
            
            # 3. Domain classification using semantic clustering
            domain_analysis = self._analyze_semantic_domains(query, query_embedding)
            
            # 4. Semantic relationship analysis using embeddings
            semantic_relationships = self._analyze_semantic_relationships(query, query_embedding)
            
            # 5. Calculate complexity score based on ML analysis
            complexity_score = self._calculate_ml_complexity_score(
                anchor_similarities, domain_analysis, semantic_relationships
            )
            
            # 6. Estimate confidence based on ML analysis quality
            confidence = self._calculate_ml_confidence(
                query_embedding, anchor_similarities, domain_analysis, semantic_relationships
            )
            
            # 7. Extract ML features for explainability
            features = {
                'query_embedding_norm': float(np.linalg.norm(query_embedding)),
                'anchor_similarities': anchor_similarities,
                'domain_analysis': domain_analysis,
                'semantic_relationships': semantic_relationships,
                'embedding_dimensionality': query_embedding.shape[0] if hasattr(query_embedding, 'shape') else len(query_embedding)
            }
            
            # 8. ML-specific metadata
            metadata = {
                'analysis_method': 'ml_sentence_bert',
                'model_name': self.ml_model_name,
                'embedding_model': 'Sentence-BERT',
                'high_complexity_similarity': anchor_similarities.get('high_complexity', 0.0),
                'medium_complexity_similarity': anchor_similarities.get('medium_complexity', 0.0),
                'low_complexity_similarity': anchor_similarities.get('low_complexity', 0.0),
                'primary_semantic_domain': domain_analysis.get('primary_domain', 'unknown'),
                'semantic_coherence': semantic_relationships.get('coherence_score', 0.0)
            }
            
            logger.debug(f"ML semantic analysis: score={complexity_score:.3f}, "
                        f"confidence={confidence:.3f}, model={self.ml_model_name}")
            
            return {
                'score': complexity_score,
                'confidence': confidence,
                'features': features,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"ML semantic analysis failed: {e}")
            return {
                'score': 0.6,
                'confidence': 0.4,
                'features': {'error': str(e)},
                'metadata': {'analysis_method': 'ml_fallback', 'error': str(e)}
            }
    
    def _get_query_embedding(self, query: str) -> np.ndarray:
        """Get Sentence-BERT embedding for query."""
        try:
            # Use the model's encode method (standard for sentence-transformers)
            if hasattr(self._sentence_bert_model, 'encode'):
                embedding = self._sentence_bert_model.encode(query, convert_to_numpy=True)
            elif hasattr(self._sentence_bert_model, 'embed'):
                embedding = self._sentence_bert_model.embed([query])[0]
            else:
                # Fallback for direct transformer models
                inputs = self._sentence_bert_model.tokenizer(query, return_tensors="pt", truncation=True, max_length=512)
                with torch.no_grad():
                    outputs = self._sentence_bert_model(**inputs)
                    embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to get Sentence-BERT embedding: {e}")
            # Return zero embedding as fallback
            return np.zeros(384)  # Standard MiniLM embedding size
    
    def _compute_anchor_similarities(self, query_embedding: np.ndarray) -> Dict[str, float]:
        """Compute similarities to semantic complexity anchors."""
        similarities = {}
        
        try:
            for complexity_level, anchor_texts in self.semantic_anchors.items():
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
            similarities = {
                'high_complexity': 0.3,
                'medium_complexity': 0.5,
                'low_complexity': 0.7
            }
        
        return similarities
    
    def _analyze_semantic_domains(self, query: str, embedding: np.ndarray) -> Dict[str, Any]:
        """Analyze semantic domains using embeddings."""
        try:
            domain_similarities = {}
            
            for domain, anchor_texts in self.domain_anchors.items():
                domain_sims = []
                
                for anchor_text in anchor_texts:
                    # Get or compute domain anchor embedding
                    domain_key = f"domain_{anchor_text}"
                    if domain_key not in self._anchor_embeddings:
                        self._anchor_embeddings[domain_key] = self._get_query_embedding(anchor_text)
                    
                    anchor_embedding = self._anchor_embeddings[domain_key]
                    similarity = self._cosine_similarity(embedding, anchor_embedding)
                    domain_sims.append(similarity)
                
                domain_similarities[domain] = max(domain_sims) if domain_sims else 0.0
            
            # Find primary domain
            if domain_similarities:
                primary_domain = max(domain_similarities.items(), key=lambda x: x[1])[0]
                domain_confidence = domain_similarities[primary_domain]
            else:
                primary_domain = 'concrete_practical'
                domain_confidence = 0.5
            
            return {
                'domain_similarities': domain_similarities,
                'primary_domain': primary_domain,
                'domain_confidence': domain_confidence
            }
            
        except Exception as e:
            logger.warning(f"Semantic domain analysis failed: {e}")
            return {
                'domain_similarities': {},
                'primary_domain': 'concrete_practical',
                'domain_confidence': 0.5
            }
    
    def _analyze_semantic_relationships(self, query: str, embedding: np.ndarray) -> Dict[str, Any]:
        """Analyze semantic relationships using embedding properties."""
        try:
            # 1. Embedding magnitude (often correlates with semantic complexity)
            embedding_magnitude = float(np.linalg.norm(embedding))
            
            # 2. Embedding dispersion (spread of values)
            embedding_std = float(np.std(embedding))
            embedding_mean = float(np.mean(embedding))
            
            # 3. High-activation dimensions (semantic richness indicator)
            activation_threshold = np.percentile(np.abs(embedding), 85)
            high_activations = int(np.sum(np.abs(embedding) > activation_threshold))
            
            # 4. Coherence score (heuristic based on embedding properties)
            coherence_score = min(
                (embedding_magnitude / 15.0) * 0.4 +  # Magnitude component
                (high_activations / len(embedding)) * 0.3 +  # Activation density
                (embedding_std / 0.4) * 0.3,  # Distribution component
                1.0
            )
            
            return {
                'embedding_magnitude': embedding_magnitude,
                'embedding_std': embedding_std,
                'embedding_mean': embedding_mean,
                'high_activations': high_activations,
                'coherence_score': coherence_score
            }
            
        except Exception as e:
            logger.warning(f"Semantic relationship analysis failed: {e}")
            return {
                'embedding_magnitude': 1.0,
                'embedding_std': 0.1,
                'embedding_mean': 0.0,
                'high_activations': 0,
                'coherence_score': 0.5
            }
    
    def _calculate_ml_complexity_score(
        self, anchor_similarities: Dict[str, float], domain_analysis: Dict[str, Any], relationships: Dict[str, Any]
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
            
            # Domain complexity contribution
            domain_complexity_mapping = {
                'abstract_theoretical': 0.9,
                'relational_analytical': 0.7,
                'concrete_practical': 0.4
            }
            
            primary_domain = domain_analysis.get('primary_domain', 'concrete_practical')
            domain_complexity = domain_complexity_mapping.get(primary_domain, 0.5)
            domain_confidence = domain_analysis.get('domain_confidence', 0.5)
            domain_contribution = domain_complexity * domain_confidence * 0.2
            
            # Relationship coherence contribution
            coherence_contribution = relationships.get('coherence_score', 0.5) * 0.2
            
            # Combined score
            ml_score = min(
                weighted_similarity * 0.6 + domain_contribution + coherence_contribution,
                1.0
            )
            
            return max(0.0, ml_score)
            
        except Exception as e:
            logger.warning(f"ML complexity score calculation failed: {e}")
            return 0.5
    
    def _calculate_ml_confidence(
        self, embedding: np.ndarray, similarities: Dict[str, float], 
        domains: Dict[str, Any], relationships: Dict[str, Any]
    ) -> float:
        """Calculate confidence based on ML analysis quality."""
        try:
            # Base confidence from embedding quality
            embedding_quality = min(np.linalg.norm(embedding) / 20.0, 0.4)
            
            # Confidence from similarity clarity
            max_similarity = max(similarities.values()) if similarities else 0.0
            similarity_confidence = max_similarity * 0.3
            
            # Confidence from domain classification
            domain_confidence = domains.get('domain_confidence', 0.0) * 0.2
            
            # Confidence from semantic coherence
            coherence_confidence = relationships.get('coherence_score', 0.0) * 0.1
            
            # Combined confidence
            total_confidence = embedding_quality + similarity_confidence + domain_confidence + coherence_confidence
            
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