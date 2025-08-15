"""
Technical Complexity View for Epic 1 Multi-View Query Analyzer.

This view analyzes technical complexity through a hybrid approach:
- Algorithmic: Uses existing TechnicalTermManager for fast term-based analysis
- ML: Leverages SciBERT for advanced technical relationship understanding
- Hybrid: Combines both approaches with configurable weighting

Key Features:
- SciBERT integration for technical document understanding
- Fast algorithmic fallback using technical vocabulary
- Domain-aware technical term detection (297+ terms)
- Technical relationship graph analysis
- Configurable algorithmic/ML weighting
"""

import logging
import asyncio
import numpy as np
import torch
from typing import Dict, Any, Optional, List, Set, Tuple
from pathlib import Path
import sys

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from .base_view import HybridView
from .view_result import ViewResult, AnalysisMethod
from ..utils.technical_terms import TechnicalTermManager
from ..ml_models.model_manager import ModelManager

logger = logging.getLogger(__name__)


class TechnicalComplexityView(HybridView):
    """
    Technical Complexity View using SciBERT + TechnicalTermManager.
    
    This view specializes in analyzing the technical complexity of queries by:
    1. Algorithmic analysis using domain-specific technical vocabulary
    2. ML analysis using SciBERT for technical relationship understanding
    3. Hybrid combination with configurable weighting
    
    Performance Targets:
    - Algorithmic analysis: <5ms
    - ML analysis: <20ms (with model loaded)
    - Hybrid analysis: <25ms total
    - Accuracy: >80% technical complexity classification
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Technical Complexity View.
        
        Args:
            config: Configuration dictionary with optional parameters:
                - algorithmic_weight: Weight for algorithmic analysis (default: 0.3)
                - ml_weight: Weight for ML analysis (default: 0.7)
                - min_technical_density: Minimum technical term density (default: 0.1)
                - enable_domain_scoring: Enable domain-specific scoring (default: True)
                - scibert_model_name: SciBERT model name (default: 'allenai/scibert_scivocab_uncased')
        """
        # Configure weights - favor ML for technical analysis
        config = config or {}
        config.setdefault('algorithmic_weight', 0.3)
        config.setdefault('ml_weight', 0.7)
        
        super().__init__(
            view_name='technical',
            ml_model_name=config.get('scibert_model_name', 'allenai/scibert_scivocab_uncased'),
            config=config
        )
        
        # Configuration
        self.min_technical_density = self.config.get('min_technical_density', 0.1)
        self.enable_domain_scoring = self.config.get('enable_domain_scoring', True)
        
        logger.info(f"Initialized TechnicalComplexityView with weights: "
                   f"algorithmic={self.algorithmic_weight:.2f}, ml={self.ml_weight:.2f}")
    
    def _initialize_algorithmic_components(self) -> None:
        """Initialize algorithmic components for fast technical analysis."""
        try:
            # Initialize technical term manager with expanded vocabulary
            self.technical_terms = TechnicalTermManager()
            
            # Technical domains to focus on
            self.technical_domains = ['ml', 'engineering', 'rag', 'data_science', 'nlp']
            
            # Technical complexity indicators
            self.complexity_indicators = {
                'high': {
                    'transformer', 'architecture', 'optimization', 'distributed', 'scalability',
                    'implementation', 'algorithm', 'framework', 'infrastructure', 'integration',
                    'fine-tuning', 'hyperparameter', 'embeddings', 'reranking', 'quantization'
                },
                'medium': {
                    'model', 'training', 'deployment', 'pipeline', 'configuration', 'monitoring',
                    'performance', 'chunking', 'retrieval', 'generation', 'prompt', 'context'
                },
                'basic': {
                    'data', 'file', 'text', 'document', 'query', 'response', 'result'
                }
            }
            
            # Domain-specific multipliers
            self.domain_multipliers = {
                'ml': 1.2,        # ML queries often more complex
                'engineering': 1.1,  # Engineering queries moderately complex
                'rag': 1.0,       # RAG queries baseline complexity
                'data_science': 1.15,  # Data science moderately complex
                'nlp': 1.1        # NLP queries moderately complex
            }
            
            logger.debug("Initialized algorithmic components for technical analysis")
            
        except Exception as e:
            logger.error(f"Failed to initialize algorithmic components: {e}")
            raise
    
    def _initialize_ml_components(self) -> None:
        """Initialize ML components for SciBERT analysis."""
        try:
            # SciBERT will be lazy-loaded via ModelManager
            self._scibert_model = None
            
            # Technical relationship patterns to look for in embeddings
            self.technical_anchors = {
                'high_complexity': [
                    "design a distributed machine learning system for large-scale deployment",
                    "implement advanced transformer architecture with attention mechanisms",
                    "optimize neural network performance using quantization and pruning techniques",
                    "develop custom BERT fine-tuning pipeline with hyperparameter optimization",
                    "create scalable vector database indexing system with real-time updates"
                ],
                'medium_complexity': [
                    "train a machine learning model using existing framework",
                    "configure text preprocessing pipeline for document analysis", 
                    "implement basic retrieval system using vector similarity",
                    "set up monitoring and logging for ML model deployment",
                    "integrate language model API into existing application"
                ],
                'low_complexity': [
                    "what is machine learning",
                    "how to install Python packages",
                    "define neural network",
                    "list common data formats",
                    "explain basic concepts"
                ]
            }
            
            # Cached embeddings for technical anchors (computed on first use)
            self._anchor_embeddings = {}
            
            logger.debug("Initialized ML components for SciBERT analysis")
            
        except Exception as e:
            logger.error(f"Failed to initialize ML components: {e}")
            raise
    
    def _analyze_algorithmic(self, query: str) -> Dict[str, Any]:
        """
        Perform fast algorithmic analysis using technical vocabulary.
        
        Args:
            query: Query text to analyze
            
        Returns:
            Dictionary with score, confidence, features, and metadata
        """
        try:
            query_lower = query.lower()
            query_words = set(query_lower.split())
            
            # 1. Technical term density analysis
            technical_terms_found = self.technical_terms.find_terms_in_text(query)
            term_density = len(technical_terms_found) / max(len(query_words), 1)
            
            # 2. Complexity indicator analysis
            complexity_scores = {
                'high': sum(1 for term in self.complexity_indicators['high'] 
                           if term in query_lower) / len(self.complexity_indicators['high']),
                'medium': sum(1 for term in self.complexity_indicators['medium'] 
                             if term in query_lower) / len(self.complexity_indicators['medium']),
                'basic': sum(1 for term in self.complexity_indicators['basic'] 
                            if term in query_lower) / len(self.complexity_indicators['basic'])
            }
            
            # 3. Domain classification
            domain_scores = {}
            if self.enable_domain_scoring:
                for domain in self.technical_domains:
                    domain_terms = self.technical_terms.get_domain_terms(domain)
                    domain_matches = sum(1 for term in domain_terms if term in query_lower)
                    domain_scores[domain] = domain_matches / max(len(domain_terms), 1)
            
            # 4. Calculate base complexity score
            # Weight complexity indicators: high=1.0, medium=0.6, basic=0.2
            weighted_complexity = (
                complexity_scores['high'] * 1.0 +
                complexity_scores['medium'] * 0.6 +
                complexity_scores['basic'] * 0.2
            )
            
            # 5. Apply term density boost
            density_boost = min(term_density * 2.0, 0.4)  # Max 0.4 boost
            
            # 6. Apply domain multiplier
            primary_domain = max(domain_scores.items(), key=lambda x: x[1])[0] if domain_scores else 'rag'
            domain_multiplier = self.domain_multipliers.get(primary_domain, 1.0)
            
            # 7. Final score calculation
            base_score = weighted_complexity + density_boost
            final_score = min(base_score * domain_multiplier, 1.0)
            
            # 8. Confidence based on term coverage and clarity
            confidence = min(
                0.7 + (term_density * 0.3),  # Base confidence + term density boost
                0.95
            )
            
            # 9. Features for explainability
            features = {
                'technical_terms_found': technical_terms_found,
                'term_density': term_density,
                'complexity_indicators': complexity_scores,
                'domain_scores': domain_scores,
                'primary_domain': primary_domain,
                'domain_multiplier': domain_multiplier,
                'weighted_complexity': weighted_complexity,
                'density_boost': density_boost
            }
            
            # 10. Metadata
            metadata = {
                'analysis_method': 'algorithmic_technical_terms',
                'total_terms_analyzed': len(query_words),
                'technical_terms_count': len(technical_terms_found),
                'primary_domain': primary_domain,
                'high_complexity_indicators': complexity_scores['high'],
                'medium_complexity_indicators': complexity_scores['medium']
            }
            
            logger.debug(f"Algorithmic technical analysis: score={final_score:.3f}, "
                        f"confidence={confidence:.3f}, terms={len(technical_terms_found)}")
            
            return {
                'score': final_score,
                'confidence': confidence,
                'features': features,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Algorithmic technical analysis failed: {e}")
            # Return safe fallback
            return {
                'score': 0.5,
                'confidence': 0.3,
                'features': {'error': str(e)},
                'metadata': {'analysis_method': 'algorithmic_fallback'}
            }
    
    def _analyze_ml(self, query: str) -> Dict[str, Any]:
        """
        Perform ML analysis using SciBERT for technical relationship understanding.
        
        Args:
            query: Query text to analyze
            
        Returns:
            Dictionary with score, confidence, features, and metadata
        """
        try:
            # Ensure SciBERT model is available
            if not self._scibert_model:
                if not self.model_manager:
                    raise ValueError("ModelManager not set - cannot load SciBERT")
                
                # Load SciBERT model through ModelManager
                self._scibert_model = self.model_manager.get_model(self.ml_model_name)
                if not self._scibert_model:
                    raise ValueError(f"Failed to load SciBERT model: {self.ml_model_name}")
            
            # 1. Generate query embedding
            query_embedding = self._get_query_embedding(query)
            
            # 2. Compare with technical complexity anchors
            anchor_similarities = self._compute_anchor_similarities(query_embedding)
            
            # 3. Analyze technical relationship patterns
            technical_patterns = self._analyze_technical_patterns(query, query_embedding)
            
            # 4. Calculate complexity score based on similarities
            complexity_score = self._calculate_ml_complexity_score(anchor_similarities, technical_patterns)
            
            # 5. Estimate confidence based on embedding quality and pattern clarity
            confidence = self._calculate_ml_confidence(query_embedding, anchor_similarities, technical_patterns)
            
            # 6. Extract ML features for explainability
            features = {
                'query_embedding_norm': float(np.linalg.norm(query_embedding)),
                'anchor_similarities': anchor_similarities,
                'technical_patterns': technical_patterns,
                'embedding_dimensionality': query_embedding.shape[0] if hasattr(query_embedding, 'shape') else len(query_embedding)
            }
            
            # 7. ML-specific metadata
            metadata = {
                'analysis_method': 'ml_scibert',
                'model_name': self.ml_model_name,
                'embedding_model': 'SciBERT',
                'high_complexity_similarity': anchor_similarities.get('high_complexity', 0.0),
                'medium_complexity_similarity': anchor_similarities.get('medium_complexity', 0.0),
                'low_complexity_similarity': anchor_similarities.get('low_complexity', 0.0),
                'technical_pattern_strength': technical_patterns.get('pattern_strength', 0.0)
            }
            
            logger.debug(f"ML technical analysis: score={complexity_score:.3f}, "
                        f"confidence={confidence:.3f}, model={self.ml_model_name}")
            
            return {
                'score': complexity_score,
                'confidence': confidence,
                'features': features,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"ML technical analysis failed: {e}")
            # Return conservative fallback
            return {
                'score': 0.6,  # Assume medium complexity when uncertain
                'confidence': 0.4,
                'features': {'error': str(e)},
                'metadata': {'analysis_method': 'ml_fallback', 'error': str(e)}
            }
    
    def _get_query_embedding(self, query: str) -> np.ndarray:
        """Get SciBERT embedding for query."""
        try:
            # Handle model format - could be direct model or dict from ModelManager
            model = self._scibert_model
            tokenizer = None
            
            if isinstance(self._scibert_model, dict):
                model = self._scibert_model.get('model')
                tokenizer = self._scibert_model.get('tokenizer')
            
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
                inputs = self._scibert_model.tokenizer(query, return_tensors="pt", truncation=True, max_length=512)
                with torch.no_grad():
                    outputs = self._scibert_model(**inputs)
                    embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to get SciBERT embedding: {e}")
            # Return zero embedding as fallback
            return np.zeros(768)  # Standard BERT embedding size
    
    def _compute_anchor_similarities(self, query_embedding: np.ndarray) -> Dict[str, float]:
        """Compute similarities to technical complexity anchors."""
        similarities = {}
        
        try:
            for complexity_level, anchor_texts in self.technical_anchors.items():
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
    
    def _analyze_technical_patterns(self, query: str, embedding: np.ndarray) -> Dict[str, Any]:
        """Analyze technical patterns in the query embedding."""
        try:
            patterns = {}
            
            # 1. Embedding magnitude analysis (technical queries often have higher magnitude)
            embedding_magnitude = float(np.linalg.norm(embedding))
            patterns['embedding_magnitude'] = embedding_magnitude
            
            # 2. Technical vocabulary activation (approximate)
            # Higher magnitude in certain dimensions often correlates with technical content
            activation_threshold = np.percentile(np.abs(embedding), 90)
            high_activations = np.sum(np.abs(embedding) > activation_threshold)
            patterns['high_activations'] = int(high_activations)
            
            # 3. Pattern strength based on embedding distribution
            embedding_std = float(np.std(embedding))
            embedding_mean = float(np.mean(embedding))
            patterns['embedding_std'] = embedding_std
            patterns['embedding_mean'] = embedding_mean
            
            # 4. Overall pattern strength (heuristic)
            pattern_strength = min(
                (embedding_magnitude / 10.0) * 0.3 +  # Magnitude component
                (high_activations / len(embedding)) * 0.4 +  # Activation sparsity
                (embedding_std / 0.5) * 0.3,  # Distribution component
                1.0
            )
            patterns['pattern_strength'] = pattern_strength
            
            return patterns
            
        except Exception as e:
            logger.warning(f"Technical pattern analysis failed: {e}")
            return {
                'embedding_magnitude': 1.0,
                'high_activations': 0,
                'embedding_std': 0.1,
                'embedding_mean': 0.0,
                'pattern_strength': 0.5
            }
    
    def _calculate_ml_complexity_score(
        self, 
        anchor_similarities: Dict[str, float], 
        technical_patterns: Dict[str, Any]
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
            
            # Pattern strength contribution
            pattern_contribution = technical_patterns.get('pattern_strength', 0.5) * 0.3
            
            # Combined score
            ml_score = min(weighted_similarity * 0.7 + pattern_contribution, 1.0)
            
            return max(0.0, ml_score)
            
        except Exception as e:
            logger.warning(f"ML complexity score calculation failed: {e}")
            return 0.5
    
    def _calculate_ml_confidence(
        self, 
        embedding: np.ndarray, 
        similarities: Dict[str, float], 
        patterns: Dict[str, Any]
    ) -> float:
        """Calculate confidence based on ML analysis quality."""
        try:
            # Base confidence from embedding quality
            embedding_quality = min(np.linalg.norm(embedding) / 20.0, 0.4)
            
            # Confidence from similarity clarity (higher max similarity = more confident)
            max_similarity = max(similarities.values()) if similarities else 0.0
            similarity_confidence = max_similarity * 0.3
            
            # Confidence from pattern strength
            pattern_confidence = patterns.get('pattern_strength', 0.0) * 0.2
            
            # Combined confidence
            total_confidence = embedding_quality + similarity_confidence + pattern_confidence + 0.1  # Base
            
            return min(max(total_confidence, 0.0), 0.95)  # Cap at 95% for ML analysis
            
        except Exception as e:
            logger.warning(f"ML confidence calculation failed: {e}")
            return 0.6  # Safe default
    
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