"""
Task Complexity View for Epic 1 Multi-View Query Analyzer.

This view analyzes task complexity through a hybrid approach:
- Algorithmic: Uses pattern matching to identify task types and cognitive requirements
- ML: Leverages DeBERTa-v3 for advanced task classification and cognitive load assessment
- Hybrid: Combines both approaches with configurable weighting

Key Features:
- DeBERTa-v3 integration for task understanding and classification
- Fast algorithmic fallback using task pattern recognition
- Bloom's taxonomy cognitive level classification
- Task type identification (factual, analytical, creative, etc.)
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

from .base_view import HybridView

logger = logging.getLogger(__name__)


class TaskComplexityView(HybridView):
    """
    Task Complexity View using DeBERTa-v3 + Task Pattern Analysis.
    
    This view specializes in analyzing the cognitive complexity of tasks by:
    1. Algorithmic analysis using task patterns and Bloom's taxonomy classification
    2. ML analysis using DeBERTa-v3 for advanced task understanding
    3. Hybrid combination with configurable weighting
    
    Performance Targets:
    - Algorithmic analysis: <4ms
    - ML analysis: <25ms (with model loaded)
    - Hybrid analysis: <30ms total
    - Accuracy: >80% task complexity classification
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Task Complexity View.
        
        Args:
            config: Configuration dictionary with optional parameters:
                - algorithmic_weight: Weight for algorithmic analysis (default: 0.5)
                - ml_weight: Weight for ML analysis (default: 0.5)
                - enable_blooms_taxonomy: Enable Bloom's taxonomy classification (default: True)
                - cognitive_threshold: Threshold for high cognitive complexity (default: 0.7)
                - deberta_model_name: DeBERTa-v3 model name (default: 'microsoft/deberta-v3-base')
        """
        # Configure weights - balanced approach for task analysis
        config = config or {}
        config.setdefault('algorithmic_weight', 0.5)
        config.setdefault('ml_weight', 0.5)
        
        super().__init__(
            view_name='task',
            ml_model_name=config.get('deberta_model_name', 'microsoft/deberta-v3-base'),
            config=config
        )
        
        # Configuration
        self.enable_blooms_taxonomy = self.config.get('enable_blooms_taxonomy', True)
        self.cognitive_threshold = self.config.get('cognitive_threshold', 0.7)
        
        logger.info(f"Initialized TaskComplexityView with weights: "
                   f"algorithmic={self.algorithmic_weight:.2f}, ml={self.ml_weight:.2f}")
    
    def _initialize_algorithmic_components(self) -> None:
        """Initialize algorithmic components for fast task analysis."""
        try:
            # Bloom's Taxonomy levels (lowest to highest cognitive complexity)
            self.blooms_taxonomy = {
                'remember': {
                    'verbs': ['define', 'list', 'name', 'state', 'describe', 'identify', 'show', 
                             'label', 'collect', 'examine', 'tabulate', 'quote', 'recall', 'recognize'],
                    'patterns': [r'what is', r'define', r'list the', r'name the', r'identify'],
                    'complexity': 0.1,
                    'description': 'Retrieving relevant knowledge from memory'
                },
                'understand': {
                    'verbs': ['explain', 'describe', 'interpret', 'summarize', 'paraphrase', 
                             'classify', 'compare', 'contrast', 'demonstrate', 'illustrate'],
                    'patterns': [r'explain', r'describe', r'what does.*mean', r'summarize', 
                               r'compare.*with', r'illustrate'],
                    'complexity': 0.3,
                    'description': 'Constructing meaning from messages'
                },
                'apply': {
                    'verbs': ['solve', 'use', 'demonstrate', 'calculate', 'complete', 'examine', 
                             'modify', 'relate', 'change', 'classify', 'experiment', 'discover'],
                    'patterns': [r'solve', r'calculate', r'use.*to', r'apply', r'demonstrate',
                               r'implement', r'configure'],
                    'complexity': 0.5,
                    'description': 'Carrying out or using a procedure'
                },
                'analyze': {
                    'verbs': ['analyze', 'break down', 'compare', 'contrast', 'diagram', 
                             'deconstruct', 'differentiate', 'discriminate', 'distinguish', 'examine'],
                    'patterns': [r'analyze', r'break.*down', r'what are.*differences', 
                               r'compare.*and.*contrast', r'examine'],
                    'complexity': 0.7,
                    'description': 'Breaking material into parts and determining relationships'
                },
                'evaluate': {
                    'verbs': ['assess', 'critique', 'evaluate', 'judge', 'justify', 'argue', 
                             'defend', 'validate', 'support', 'weight', 'prioritize'],
                    'patterns': [r'evaluate', r'assess', r'critique', r'judge', r'which.*better',
                               r'justify', r'argue.*for'],
                    'complexity': 0.8,
                    'description': 'Making judgments based on criteria and standards'
                },
                'create': {
                    'verbs': ['design', 'construct', 'create', 'develop', 'formulate', 'build',
                             'invent', 'make', 'originate', 'plan', 'produce', 'generate'],
                    'patterns': [r'design', r'create', r'develop', r'build', r'construct',
                               r'formulate', r'generate'],
                    'complexity': 1.0,
                    'description': 'Putting elements together to form a coherent whole'
                }
            }
            
            # Task type patterns
            self.task_types = {
                'factual': {
                    'patterns': [r'what is', r'define', r'list', r'name', r'when did', r'where is'],
                    'complexity': 0.2,
                    'cognitive_load': 'low'
                },
                'procedural': {
                    'patterns': [r'how to', r'steps to', r'procedure', r'process', r'method'],
                    'complexity': 0.4,
                    'cognitive_load': 'medium'
                },
                'conceptual': {
                    'patterns': [r'why', r'explain', r'relationship', r'principle', r'theory'],
                    'complexity': 0.6,
                    'cognitive_load': 'medium'
                },
                'analytical': {
                    'patterns': [r'analyze', r'compare', r'evaluate', r'assess', r'examine'],
                    'complexity': 0.7,
                    'cognitive_load': 'high'
                },
                'creative': {
                    'patterns': [r'design', r'create', r'develop', r'propose', r'generate'],
                    'complexity': 0.9,
                    'cognitive_load': 'high'
                },
                'problem_solving': {
                    'patterns': [r'solve', r'troubleshoot', r'debug', r'fix', r'resolve'],
                    'complexity': 0.8,
                    'cognitive_load': 'high'
                }
            }
            
            # Multi-step task indicators
            self.multistep_indicators = [
                r'first.*then', r'step.*step', r'after.*do', r'once.*next',
                r'initially.*subsequently', r'begin.*then.*finally'
            ]
            
            # Compile patterns for efficiency
            self._compile_task_patterns()
            
            logger.debug("Initialized algorithmic components for task analysis")
            
        except Exception as e:
            logger.error(f"Failed to initialize algorithmic components: {e}")
            raise
    
    def _initialize_ml_components(self) -> None:
        """Initialize ML components for DeBERTa-v3 analysis."""
        try:
            # DeBERTa-v3 will be lazy-loaded via ModelManager
            self._deberta_model = None
            
            # Task complexity anchors for similarity comparison
            self.task_anchors = {
                'high_complexity': [
                    "Design and implement a comprehensive machine learning pipeline that addresses data preprocessing, feature engineering, model selection, hyperparameter optimization, and deployment considerations while evaluating multiple algorithms and ensuring reproducibility.",
                    "Develop a sophisticated natural language processing system that can analyze sentiment, extract entities, classify documents, and generate summaries while handling multiple languages and domain-specific terminology.",
                    "Create an end-to-end recommendation system that incorporates collaborative filtering, content-based methods, and deep learning approaches while addressing cold start problems, scalability issues, and real-time inference requirements.",
                    "Analyze the trade-offs between different distributed computing frameworks for large-scale data processing, considering factors such as performance, fault tolerance, ease of use, and ecosystem integration.",
                    "Evaluate and compare multiple deep learning architectures for computer vision tasks, considering their computational requirements, accuracy metrics, interpretability, and suitability for different deployment scenarios."
                ],
                'medium_complexity': [
                    "Implement a basic machine learning model using a popular framework and evaluate its performance on a standard dataset.",
                    "Configure a database system for optimal performance by adjusting indexing strategies and query optimization techniques.",
                    "Analyze the performance metrics of a web application and identify potential bottlenecks in the system architecture.",
                    "Compare the features and capabilities of two different software libraries for a specific use case.",
                    "Develop a simple data visualization dashboard that displays key metrics from multiple data sources."
                ],
                'low_complexity': [
                    "What is the definition of machine learning and how does it differ from traditional programming?",
                    "List the basic steps involved in training a neural network model.",
                    "Explain what a database is and describe its primary components.",
                    "Name three popular programming languages used in data science.",
                    "Describe the difference between supervised and unsupervised learning."
                ]
            }
            
            # Task classification anchors
            self.task_classification_anchors = {
                'analytical': [
                    "Compare and analyze the effectiveness of different approaches",
                    "Evaluate the advantages and disadvantages of this method",
                    "Examine the relationship between these variables"
                ],
                'creative': [
                    "Design a novel solution to address this challenge",
                    "Develop an innovative approach for implementing this system",
                    "Create a comprehensive framework that integrates multiple components"
                ],
                'procedural': [
                    "Follow these steps to configure the system correctly",
                    "Apply this methodology to solve the given problem",
                    "Implement the algorithm using the specified parameters"
                ],
                'factual': [
                    "What is the definition of this concept?",
                    "List the main characteristics of this technology",
                    "Identify the key components of this system"
                ]
            }
            
            # Cached embeddings for task anchors
            self._anchor_embeddings = {}
            
            logger.debug("Initialized ML components for DeBERTa-v3 analysis")
            
        except Exception as e:
            logger.error(f"Failed to initialize ML components: {e}")
            raise
    
    def _compile_task_patterns(self) -> None:
        """Compile regex patterns for efficient matching."""
        # Compile Bloom's taxonomy patterns
        for level, data in self.blooms_taxonomy.items():
            compiled_patterns = []
            for pattern in data['patterns']:
                try:
                    compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern}': {e}")
            data['compiled_patterns'] = compiled_patterns
        
        # Compile task type patterns
        for task_type, data in self.task_types.items():
            compiled_patterns = []
            for pattern in data['patterns']:
                try:
                    compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern}': {e}")
            data['compiled_patterns'] = compiled_patterns
        
        # Compile multi-step patterns
        self._multistep_compiled = []
        for pattern in self.multistep_indicators:
            try:
                self._multistep_compiled.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern}': {e}")
    
    def _analyze_algorithmic(self, query: str) -> Dict[str, Any]:
        """
        Perform fast algorithmic analysis using task patterns.
        
        Args:
            query: Query text to analyze
            
        Returns:
            Dictionary with score, confidence, features, and metadata
        """
        try:
            query_lower = query.lower().strip()
            
            # 1. Bloom's taxonomy classification
            blooms_analysis = self._classify_blooms_taxonomy(query_lower) if self.enable_blooms_taxonomy else {}
            
            # 2. Task type classification
            task_type_analysis = self._classify_task_type(query_lower)
            
            # 3. Multi-step task detection
            multistep_analysis = self._detect_multistep_task(query_lower)
            
            # 4. Cognitive load analysis
            cognitive_analysis = self._analyze_cognitive_load(query, task_type_analysis, multistep_analysis)
            
            # 5. Calculate complexity score
            final_score = self._calculate_task_complexity_score(
                blooms_analysis, task_type_analysis, multistep_analysis, cognitive_analysis
            )
            
            # 6. Calculate confidence
            confidence = self._calculate_algorithmic_confidence(
                blooms_analysis, task_type_analysis, multistep_analysis, cognitive_analysis
            )
            
            # 7. Features for explainability
            features = {
                'blooms_taxonomy': blooms_analysis,
                'task_type': task_type_analysis,
                'multistep_analysis': multistep_analysis,
                'cognitive_analysis': cognitive_analysis,
                'verb_complexity_score': self._analyze_verb_complexity(query_lower)
            }
            
            # 8. Metadata
            metadata = {
                'analysis_method': 'algorithmic_task_patterns',
                'blooms_level': blooms_analysis.get('primary_level', 'unknown'),
                'task_type': task_type_analysis.get('primary_type', 'unknown'),
                'is_multistep': multistep_analysis.get('is_multistep', False),
                'cognitive_load': cognitive_analysis.get('cognitive_load', 'medium'),
                'complexity_factors': cognitive_analysis.get('complexity_factors', [])
            }
            
            logger.debug(f"Algorithmic task analysis: score={final_score:.3f}, "
                        f"confidence={confidence:.3f}, "
                        f"blooms={blooms_analysis.get('primary_level', 'unknown')}, "
                        f"task={task_type_analysis.get('primary_type', 'unknown')}")
            
            return {
                'score': max(0.0, min(1.0, final_score)),
                'confidence': confidence,
                'features': features,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Algorithmic task analysis failed: {e}")
            return {
                'score': 0.5,
                'confidence': 0.3,
                'features': {'error': str(e)},
                'metadata': {'analysis_method': 'algorithmic_fallback'}
            }
    
    def _classify_blooms_taxonomy(self, query: str) -> Dict[str, Any]:
        """Classify query according to Bloom's taxonomy."""
        level_scores = {}
        
        for level, data in self.blooms_taxonomy.items():
            score = 0.0
            
            # Check verbs
            for verb in data['verbs']:
                if verb in query:
                    score += 1.0
            
            # Check patterns
            for pattern in data.get('compiled_patterns', []):
                matches = len(pattern.findall(query))
                score += matches * 0.5
            
            level_scores[level] = score
        
        # Find primary level
        if level_scores:
            primary_level = max(level_scores.items(), key=lambda x: x[1])[0]
            primary_score = self.blooms_taxonomy[primary_level]['complexity']
        else:
            primary_level = 'understand'  # Default
            primary_score = 0.3
        
        return {
            'level_scores': level_scores,
            'primary_level': primary_level,
            'primary_score': primary_score,
            'description': self.blooms_taxonomy.get(primary_level, {}).get('description', '')
        }
    
    def _classify_task_type(self, query: str) -> Dict[str, Any]:
        """Classify the type of task."""
        type_scores = {}
        
        for task_type, data in self.task_types.items():
            score = 0.0
            
            # Check patterns
            for pattern in data.get('compiled_patterns', []):
                matches = len(pattern.findall(query))
                score += matches
            
            type_scores[task_type] = score
        
        # Find primary type
        if type_scores and max(type_scores.values()) > 0:
            primary_type = max(type_scores.items(), key=lambda x: x[1])[0]
            primary_complexity = self.task_types[primary_type]['complexity']
        else:
            primary_type = 'conceptual'  # Default
            primary_complexity = 0.6
        
        return {
            'type_scores': type_scores,
            'primary_type': primary_type,
            'primary_complexity': primary_complexity,
            'cognitive_load': self.task_types.get(primary_type, {}).get('cognitive_load', 'medium')
        }
    
    def _detect_multistep_task(self, query: str) -> Dict[str, Any]:
        """Detect if task involves multiple steps."""
        multistep_indicators = 0
        
        for pattern in self._multistep_compiled:
            matches = len(pattern.findall(query))
            multistep_indicators += matches
        
        # Also check for sequence words
        sequence_words = ['then', 'next', 'after', 'subsequently', 'finally', 'first', 'second']
        sequence_count = sum(1 for word in sequence_words if word in query)
        
        is_multistep = multistep_indicators > 0 or sequence_count >= 2
        complexity_boost = min((multistep_indicators + sequence_count) * 0.1, 0.3)
        
        return {
            'is_multistep': is_multistep,
            'multistep_indicators': multistep_indicators,
            'sequence_words': sequence_count,
            'complexity_boost': complexity_boost
        }
    
    def _analyze_cognitive_load(
        self, query: str, task_analysis: Dict, multistep_analysis: Dict
    ) -> Dict[str, Any]:
        """Analyze cognitive load of the task."""
        complexity_factors = []
        cognitive_score = 0.5  # Base score
        
        # Factor 1: Task type complexity
        task_complexity = task_analysis.get('primary_complexity', 0.5)
        cognitive_score += task_complexity * 0.3
        if task_complexity > 0.7:
            complexity_factors.append('high_complexity_task_type')
        
        # Factor 2: Multi-step boost
        if multistep_analysis.get('is_multistep', False):
            cognitive_score += multistep_analysis.get('complexity_boost', 0.0)
            complexity_factors.append('multistep_task')
        
        # Factor 3: Query length (longer queries often more complex)
        query_length = len(query.split())
        if query_length > 15:
            length_boost = min((query_length - 15) * 0.02, 0.2)
            cognitive_score += length_boost
            complexity_factors.append('long_query')
        
        # Factor 4: Multiple concepts (indicated by conjunctions)
        conjunctions = ['and', 'but', 'or', 'while', 'whereas', 'although']
        conjunction_count = sum(1 for conj in conjunctions if conj in query.lower())
        if conjunction_count >= 2:
            cognitive_score += conjunction_count * 0.05
            complexity_factors.append('multiple_concepts')
        
        # Determine cognitive load category
        if cognitive_score >= self.cognitive_threshold:
            cognitive_load = 'high'
        elif cognitive_score >= 0.4:
            cognitive_load = 'medium'
        else:
            cognitive_load = 'low'
        
        return {
            'cognitive_score': min(cognitive_score, 1.0),
            'cognitive_load': cognitive_load,
            'complexity_factors': complexity_factors,
            'query_length': query_length,
            'conjunction_count': conjunction_count
        }
    
    def _analyze_verb_complexity(self, query: str) -> float:
        """Analyze complexity based on action verbs in query."""
        high_complexity_verbs = [
            'synthesize', 'evaluate', 'analyze', 'critique', 'assess', 'design',
            'create', 'formulate', 'develop', 'construct', 'build', 'generate'
        ]
        
        medium_complexity_verbs = [
            'compare', 'contrast', 'explain', 'apply', 'implement', 'solve',
            'demonstrate', 'modify', 'adapt', 'organize', 'classify'
        ]
        
        high_verb_matches = sum(1 for verb in high_complexity_verbs if verb in query)
        medium_verb_matches = sum(1 for verb in medium_complexity_verbs if verb in query)
        
        verb_score = (high_verb_matches * 0.8 + medium_verb_matches * 0.5) / 5.0
        return min(verb_score, 1.0)
    
    def _calculate_task_complexity_score(
        self, blooms: Dict, task_type: Dict, multistep: Dict, cognitive: Dict
    ) -> float:
        """Calculate overall task complexity score."""
        # Weight different components
        blooms_score = blooms.get('primary_score', 0.3)
        task_type_score = task_type.get('primary_complexity', 0.5)
        cognitive_score = cognitive.get('cognitive_score', 0.5)
        multistep_boost = multistep.get('complexity_boost', 0.0)
        
        # Weighted combination
        final_score = (
            blooms_score * 0.3 +
            task_type_score * 0.3 +
            cognitive_score * 0.3 +
            multistep_boost  # Additional boost, not weighted
        )
        
        return min(final_score, 1.0)
    
    def _calculate_algorithmic_confidence(
        self, blooms: Dict, task_type: Dict, multistep: Dict, cognitive: Dict
    ) -> float:
        """Calculate confidence based on pattern matching quality."""
        confidence = 0.4  # Base confidence
        
        # Boost from Bloom's classification
        if blooms.get('primary_level', 'unknown') != 'unknown':
            max_blooms_score = max(blooms.get('level_scores', {}).values(), default=0)
            if max_blooms_score > 0:
                confidence += min(max_blooms_score * 0.1, 0.2)
        
        # Boost from task type classification
        if task_type.get('primary_type', 'unknown') != 'unknown':
            max_task_score = max(task_type.get('type_scores', {}).values(), default=0)
            if max_task_score > 0:
                confidence += min(max_task_score * 0.1, 0.15)
        
        # Boost from complexity factors
        complexity_factors = len(cognitive.get('complexity_factors', []))
        confidence += min(complexity_factors * 0.05, 0.15)
        
        # Boost from multistep detection
        if multistep.get('is_multistep', False):
            confidence += 0.1
        
        return min(confidence, 0.85)  # Cap algorithmic confidence at 85%
    
    def _analyze_ml(self, query: str) -> Dict[str, Any]:
        """
        Perform ML analysis using DeBERTa-v3 for task understanding.
        
        Args:
            query: Query text to analyze
            
        Returns:
            Dictionary with score, confidence, features, and metadata
        """
        try:
            # Ensure DeBERTa-v3 model is available
            if not self._deberta_model:
                if not self.model_manager:
                    raise ValueError("ModelManager not set - cannot load DeBERTa-v3")
                
                # Load DeBERTa-v3 model through ModelManager
                self._deberta_model = self.model_manager.get_model(self.ml_model_name)
                if not self._deberta_model:
                    raise ValueError(f"Failed to load DeBERTa-v3 model: {self.ml_model_name}")
            
            # 1. Generate query embedding
            query_embedding = self._get_query_embedding(query)
            
            # 2. Compare with task complexity anchors
            anchor_similarities = self._compute_anchor_similarities(query_embedding)
            
            # 3. Task classification using ML
            task_classification = self._classify_task_ml(query, query_embedding)
            
            # 4. Calculate complexity score based on ML analysis
            complexity_score = self._calculate_ml_complexity_score(anchor_similarities, task_classification)
            
            # 5. Estimate confidence based on ML analysis quality
            confidence = self._calculate_ml_confidence(query_embedding, anchor_similarities, task_classification)
            
            # 6. Extract ML features for explainability
            features = {
                'query_embedding_norm': float(np.linalg.norm(query_embedding)),
                'anchor_similarities': anchor_similarities,
                'task_classification': task_classification,
                'embedding_dimensionality': query_embedding.shape[0] if hasattr(query_embedding, 'shape') else len(query_embedding)
            }
            
            # 7. ML-specific metadata
            metadata = {
                'analysis_method': 'ml_deberta_v3',
                'model_name': self.ml_model_name,
                'embedding_model': 'DeBERTa-v3',
                'high_complexity_similarity': anchor_similarities.get('high_complexity', 0.0),
                'medium_complexity_similarity': anchor_similarities.get('medium_complexity', 0.0),
                'low_complexity_similarity': anchor_similarities.get('low_complexity', 0.0),
                'predicted_task_type': task_classification.get('predicted_type', 'unknown')
            }
            
            logger.debug(f"ML task analysis: score={complexity_score:.3f}, "
                        f"confidence={confidence:.3f}, model={self.ml_model_name}")
            
            return {
                'score': complexity_score,
                'confidence': confidence,
                'features': features,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"ML task analysis failed: {e}")
            return {
                'score': 0.6,
                'confidence': 0.4,
                'features': {'error': str(e)},
                'metadata': {'analysis_method': 'ml_fallback', 'error': str(e)}
            }
    
    def _get_query_embedding(self, query: str) -> np.ndarray:
        """Get DeBERTa-v3 embedding for query."""
        try:
            # Handle model format - could be direct model or dict from ModelManager
            model = self._deberta_model
            tokenizer = None
            
            if isinstance(self._deberta_model, dict):
                model = self._deberta_model.get('model')
                tokenizer = self._deberta_model.get('tokenizer')
            
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
                inputs = self._deberta_model.tokenizer(query, return_tensors="pt", truncation=True, max_length=512)
                with torch.no_grad():
                    outputs = self._deberta_model(**inputs)
                    embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to get DeBERTa-v3 embedding: {e}")
            # Return zero embedding as fallback
            return np.zeros(768)  # Standard size for many transformer models
    
    def _compute_anchor_similarities(self, query_embedding: np.ndarray) -> Dict[str, float]:
        """Compute similarities to task complexity anchors."""
        similarities = {}
        
        try:
            for complexity_level, anchor_texts in self.task_anchors.items():
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
    
    def _classify_task_ml(self, query: str, embedding: np.ndarray) -> Dict[str, Any]:
        """Classify task type using ML embeddings."""
        try:
            classification_similarities = {}
            
            for task_type, anchor_texts in self.task_classification_anchors.items():
                type_similarities = []
                
                for anchor_text in anchor_texts:
                    # Get or compute anchor embedding
                    anchor_key = f"class_{anchor_text}"
                    if anchor_key not in self._anchor_embeddings:
                        self._anchor_embeddings[anchor_key] = self._get_query_embedding(anchor_text)
                    
                    anchor_embedding = self._anchor_embeddings[anchor_key]
                    similarity = self._cosine_similarity(embedding, anchor_embedding)
                    type_similarities.append(similarity)
                
                classification_similarities[task_type] = max(type_similarities) if type_similarities else 0.0
            
            # Find best matching task type
            if classification_similarities:
                predicted_type = max(classification_similarities.items(), key=lambda x: x[1])[0]
                confidence = classification_similarities[predicted_type]
            else:
                predicted_type = 'conceptual'
                confidence = 0.5
            
            return {
                'similarities': classification_similarities,
                'predicted_type': predicted_type,
                'classification_confidence': confidence
            }
            
        except Exception as e:
            logger.warning(f"ML task classification failed: {e}")
            return {
                'similarities': {},
                'predicted_type': 'conceptual',
                'classification_confidence': 0.5
            }
    
    def _calculate_ml_complexity_score(
        self, anchor_similarities: Dict[str, float], task_classification: Dict[str, Any]
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
            
            # Task type complexity contribution
            task_type = task_classification.get('predicted_type', 'conceptual')
            task_type_complexity = self.task_types.get(task_type, {}).get('complexity', 0.5)
            classification_confidence = task_classification.get('classification_confidence', 0.5)
            
            # Weight task type by classification confidence
            task_contribution = task_type_complexity * classification_confidence * 0.3
            
            # Combined score
            ml_score = min(weighted_similarity * 0.7 + task_contribution, 1.0)
            
            return max(0.0, ml_score)
            
        except Exception as e:
            logger.warning(f"ML complexity score calculation failed: {e}")
            return 0.5
    
    def _calculate_ml_confidence(
        self, embedding: np.ndarray, similarities: Dict[str, float], classification: Dict[str, Any]
    ) -> float:
        """Calculate confidence based on ML analysis quality."""
        try:
            # Base confidence from embedding quality
            embedding_quality = min(np.linalg.norm(embedding) / 20.0, 0.4)
            
            # Confidence from similarity clarity
            max_similarity = max(similarities.values()) if similarities else 0.0
            similarity_confidence = max_similarity * 0.3
            
            # Confidence from classification quality
            classification_confidence = classification.get('classification_confidence', 0.0) * 0.2
            
            # Combined confidence
            total_confidence = embedding_quality + similarity_confidence + classification_confidence + 0.1
            
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