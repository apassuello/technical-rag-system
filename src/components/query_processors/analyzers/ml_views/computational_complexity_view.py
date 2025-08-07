"""
Computational Complexity View for Epic 1 Multi-View Query Analyzer.

This view analyzes computational complexity through a hybrid approach:
- Algorithmic: Uses computational heuristics and resource estimation patterns
- ML: Leverages T5-small for advanced computational requirement understanding
- Hybrid: Combines both approaches with configurable weighting

Key Features:
- T5-small integration for computational reasoning and analysis
- Fast algorithmic fallback using computational patterns and heuristics
- Resource requirement estimation (time, space, processing complexity)
- Algorithm complexity classification (O(n), O(log n), O(n²), etc.)
- Configurable algorithmic/ML weighting
"""

import logging
import asyncio
import numpy as np
import torch
from typing import Dict, Any, Optional, List, Set, Tuple
from pathlib import Path
import sys
import re
import math

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from .base_view import HybridView
from .view_result import ViewResult, AnalysisMethod
from ..ml_models.model_manager import ModelManager

logger = logging.getLogger(__name__)


class ComputationalComplexityView(HybridView):
    """
    Computational Complexity View using T5-small + Computational Heuristics.
    
    This view specializes in analyzing the computational complexity of queries by:
    1. Algorithmic analysis using computational patterns and resource estimation
    2. ML analysis using T5-small for computational reasoning
    3. Hybrid combination with configurable weighting
    
    Performance Targets:
    - Algorithmic analysis: <5ms
    - ML analysis: <30ms (with model loaded)
    - Hybrid analysis: <35ms total
    - Accuracy: >80% computational complexity classification
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Computational Complexity View.
        
        Args:
            config: Configuration dictionary with optional parameters:
                - algorithmic_weight: Weight for algorithmic analysis (default: 0.6)
                - ml_weight: Weight for ML analysis (default: 0.4)
                - enable_resource_estimation: Enable resource requirement estimation (default: True)
                - complexity_threshold: Threshold for high computational complexity (default: 0.7)
                - t5_model_name: T5-small model name (default: 't5-small')
        """
        # Configure weights - favor algorithmic for computational analysis (more precise)
        config = config or {}
        config.setdefault('algorithmic_weight', 0.6)
        config.setdefault('ml_weight', 0.4)
        
        super().__init__(
            view_name='computational',
            ml_model_name=config.get('t5_model_name', 't5-small'),
            config=config
        )
        
        # Configuration
        self.enable_resource_estimation = self.config.get('enable_resource_estimation', True)
        self.complexity_threshold = self.config.get('complexity_threshold', 0.7)
        
        logger.info(f"Initialized ComputationalComplexityView with weights: "
                   f"algorithmic={self.algorithmic_weight:.2f}, ml={self.ml_weight:.2f}")
    
    def _initialize_algorithmic_components(self) -> None:
        """Initialize algorithmic components for computational analysis."""
        try:
            # Algorithm complexity indicators
            self.algorithm_patterns = {
                'constant': {
                    'keywords': ['lookup', 'direct access', 'hash table', 'constant time', 'O(1)'],
                    'patterns': [r'lookup', r'direct.*access', r'hash.*table', r'constant.*time'],
                    'complexity_score': 0.1,
                    'description': 'Constant time operations'
                },
                'logarithmic': {
                    'keywords': ['binary search', 'tree traversal', 'divide and conquer', 'log', 'logarithmic'],
                    'patterns': [r'binary.*search', r'tree.*traversal', r'divide.*conquer', r'O\(log'],
                    'complexity_score': 0.3,
                    'description': 'Logarithmic time operations'
                },
                'linear': {
                    'keywords': ['iterate', 'scan', 'linear search', 'single pass', 'traverse'],
                    'patterns': [r'iterate', r'scan', r'linear.*search', r'single.*pass', r'O\(n\)'],
                    'complexity_score': 0.5,
                    'description': 'Linear time operations'
                },
                'linearithmic': {
                    'keywords': ['sort', 'merge sort', 'quick sort', 'heap sort', 'n log n'],
                    'patterns': [r'sort', r'merge.*sort', r'quick.*sort', r'O\(n.*log'],
                    'complexity_score': 0.6,
                    'description': 'n log n operations'
                },
                'quadratic': {
                    'keywords': ['nested loops', 'all pairs', 'brute force', 'quadratic', 'n squared'],
                    'patterns': [r'nested.*loops?', r'all.*pairs', r'brute.*force', r'O\(n\^?2'],
                    'complexity_score': 0.8,
                    'description': 'Quadratic time operations'
                },
                'exponential': {
                    'keywords': ['exponential', 'recursive', 'backtracking', 'exhaustive', 'all combinations'],
                    'patterns': [r'exponential', r'recursive', r'backtracking', r'exhaustive', r'O\(2\^n'],
                    'complexity_score': 1.0,
                    'description': 'Exponential time operations'
                }
            }
            
            # Computational resource indicators
            self.resource_patterns = {
                'memory_intensive': {
                    'keywords': ['large dataset', 'in-memory', 'cache', 'storage', 'memory'],
                    'patterns': [r'large.*dataset', r'in-memory', r'cache', r'storage'],
                    'resource_score': 0.7,
                    'resource_type': 'memory'
                },
                'cpu_intensive': {
                    'keywords': ['computation', 'processing', 'calculation', 'algorithm', 'compute'],
                    'patterns': [r'computation', r'processing', r'calculation', r'algorithm'],
                    'resource_score': 0.6,
                    'resource_type': 'cpu'
                },
                'io_intensive': {
                    'keywords': ['file', 'database', 'network', 'disk', 'stream'],
                    'patterns': [r'file', r'database', r'network', r'disk', r'stream'],
                    'resource_score': 0.5,
                    'resource_type': 'io'
                },
                'parallel_processing': {
                    'keywords': ['parallel', 'concurrent', 'distributed', 'multi-threaded', 'cluster'],
                    'patterns': [r'parallel', r'concurrent', r'distributed', r'multi-threaded'],
                    'resource_score': 0.8,
                    'resource_type': 'parallelism'
                }
            }
            
            # Scale and size indicators
            self.scale_patterns = {
                'small_scale': {
                    'keywords': ['small', 'few', 'limited', 'simple', 'basic'],
                    'patterns': [r'small', r'few', r'limited', r'simple', r'basic'],
                    'scale_multiplier': 0.3
                },
                'medium_scale': {
                    'keywords': ['moderate', 'standard', 'typical', 'medium', 'normal'],
                    'patterns': [r'moderate', r'standard', r'typical', r'medium'],
                    'scale_multiplier': 0.6
                },
                'large_scale': {
                    'keywords': ['large', 'massive', 'big data', 'enterprise', 'scalable'],
                    'patterns': [r'large', r'massive', r'big.*data', r'enterprise', r'scalable'],
                    'scale_multiplier': 1.0
                }
            }
            
            # Data structure complexity
            self.data_structure_complexity = {
                'array': 0.2,
                'list': 0.3,
                'hash': 0.3,
                'tree': 0.6,
                'graph': 0.8,
                'matrix': 0.7,
                'heap': 0.5,
                'trie': 0.7
            }
            
            # Compile patterns for efficiency
            self._compile_computational_patterns()
            
            logger.debug("Initialized algorithmic components for computational analysis")
            
        except Exception as e:
            logger.error(f"Failed to initialize algorithmic components: {e}")
            raise
    
    def _initialize_ml_components(self) -> None:
        """Initialize ML components for T5-small analysis."""
        try:
            # T5-small will be lazy-loaded via ModelManager
            self._t5_model = None
            
            # Computational complexity anchors for similarity comparison
            self.computational_anchors = {
                'high_complexity': [
                    "Design and implement a distributed algorithm that processes billions of records in parallel while maintaining consistency across multiple nodes and handling network partitions gracefully.",
                    "Develop a machine learning pipeline that trains deep neural networks on massive datasets using distributed computing with automatic hyperparameter optimization and real-time inference.",
                    "Create a real-time recommendation system that analyzes user behavior patterns across millions of users while maintaining sub-millisecond response times and handling peak loads.",
                    "Implement a graph algorithm that finds optimal paths in networks with millions of nodes and edges while considering dynamic weight updates and memory constraints.",
                    "Build a distributed search engine that indexes billions of documents, handles thousands of queries per second, and provides relevant results with advanced ranking algorithms."
                ],
                'medium_complexity': [
                    "Implement a sorting algorithm that efficiently handles datasets with thousands of records while minimizing memory usage.",
                    "Design a caching system that balances memory usage and access speed for a web application serving moderate traffic.",
                    "Create a data processing pipeline that transforms and analyzes structured data files with reasonable performance requirements.",
                    "Develop a simple machine learning model that trains on standard datasets and provides predictions within acceptable time limits.",
                    "Build a database query optimization system that improves performance for common operations."
                ],
                'low_complexity': [
                    "Write a simple function that calculates the sum of numbers in a list.",
                    "Create a basic script that reads data from a file and displays it.",
                    "Implement a straightforward search function that finds items in a small dataset.",
                    "Design a simple data structure that stores and retrieves basic information.",
                    "Write code that performs basic arithmetic operations on input values."
                ]
            }
            
            # Computational reasoning anchors
            self.reasoning_anchors = {
                'algorithmic_reasoning': [
                    "analyzing time complexity and space complexity trade-offs",
                    "comparing different algorithmic approaches for efficiency",
                    "optimizing performance through algorithm selection"
                ],
                'system_design': [
                    "designing scalable distributed systems architecture",
                    "planning resource allocation and capacity management",
                    "considering performance bottlenecks and optimization"
                ],
                'resource_planning': [
                    "estimating computational requirements and resource needs",
                    "planning for scalability and performance optimization",
                    "analyzing system capacity and throughput requirements"
                ]
            }
            
            # Cached embeddings for computational anchors
            self._anchor_embeddings = {}
            
            logger.debug("Initialized ML components for T5-small analysis")
            
        except Exception as e:
            logger.error(f"Failed to initialize ML components: {e}")
            raise
    
    def _compile_computational_patterns(self) -> None:
        """Compile regex patterns for efficient matching."""
        # Compile algorithm patterns
        for complexity_type, data in self.algorithm_patterns.items():
            compiled_patterns = []
            for pattern in data['patterns']:
                try:
                    compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern}': {e}")
            data['compiled_patterns'] = compiled_patterns
        
        # Compile resource patterns
        for resource_type, data in self.resource_patterns.items():
            compiled_patterns = []
            for pattern in data['patterns']:
                try:
                    compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern}': {e}")
            data['compiled_patterns'] = compiled_patterns
        
        # Compile scale patterns
        for scale_type, data in self.scale_patterns.items():
            compiled_patterns = []
            for pattern in data['patterns']:
                try:
                    compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern}': {e}")
            data['compiled_patterns'] = compiled_patterns
    
    def _analyze_algorithmic(self, query: str) -> Dict[str, Any]:
        """
        Perform fast algorithmic analysis using computational patterns.
        
        Args:
            query: Query text to analyze
            
        Returns:
            Dictionary with score, confidence, features, and metadata
        """
        try:
            query_lower = query.lower().strip()
            
            # 1. Algorithm complexity analysis
            algorithm_analysis = self._analyze_algorithm_complexity(query_lower)
            
            # 2. Resource requirement analysis
            resource_analysis = self._analyze_resource_requirements(query_lower) if self.enable_resource_estimation else {}
            
            # 3. Scale analysis
            scale_analysis = self._analyze_scale_indicators(query_lower)
            
            # 4. Data structure complexity analysis
            structure_analysis = self._analyze_data_structures(query_lower)
            
            # 5. Computational operation analysis
            operation_analysis = self._analyze_computational_operations(query_lower)
            
            # 6. Calculate computational complexity score
            final_score = self._calculate_computational_score(
                algorithm_analysis, resource_analysis, scale_analysis, 
                structure_analysis, operation_analysis
            )
            
            # 7. Calculate confidence
            confidence = self._calculate_algorithmic_confidence(
                algorithm_analysis, resource_analysis, scale_analysis, 
                structure_analysis, operation_analysis
            )
            
            # 8. Features for explainability
            features = {
                'algorithm_analysis': algorithm_analysis,
                'resource_analysis': resource_analysis,
                'scale_analysis': scale_analysis,
                'data_structure_analysis': structure_analysis,
                'operation_analysis': operation_analysis,
                'computational_indicators': self._count_computational_indicators(query_lower)
            }
            
            # 9. Metadata
            metadata = {
                'analysis_method': 'algorithmic_computational_patterns',
                'primary_complexity': algorithm_analysis.get('primary_complexity', 'linear'),
                'resource_requirements': list(resource_analysis.get('detected_resources', {}).keys()),
                'scale_level': scale_analysis.get('primary_scale', 'medium'),
                'complexity_score': algorithm_analysis.get('complexity_score', 0.5),
                'estimated_resources': resource_analysis.get('total_resource_score', 0.5)
            }
            
            logger.debug(f"Algorithmic computational analysis: score={final_score:.3f}, "
                        f"confidence={confidence:.3f}, "
                        f"complexity={algorithm_analysis.get('primary_complexity', 'linear')}, "
                        f"scale={scale_analysis.get('primary_scale', 'medium')}")
            
            return {
                'score': max(0.0, min(1.0, final_score)),
                'confidence': confidence,
                'features': features,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Algorithmic computational analysis failed: {e}")
            return {
                'score': 0.5,
                'confidence': 0.3,
                'features': {'error': str(e)},
                'metadata': {'analysis_method': 'algorithmic_fallback'}
            }
    
    def _analyze_algorithm_complexity(self, query: str) -> Dict[str, Any]:
        """Analyze algorithmic complexity patterns in query."""
        complexity_scores = {}
        matched_patterns = {}
        
        for complexity_type, data in self.algorithm_patterns.items():
            score = 0
            matches = []
            
            # Check keywords
            for keyword in data['keywords']:
                if keyword in query:
                    score += 1
                    matches.append(keyword)
            
            # Check patterns
            for pattern in data.get('compiled_patterns', []):
                pattern_matches = len(pattern.findall(query))
                score += pattern_matches * 0.5
                if pattern_matches > 0:
                    matches.append(f"pattern:{pattern.pattern}")
            
            complexity_scores[complexity_type] = {
                'score': score,
                'matches': matches,
                'complexity_value': data['complexity_score']
            }
        
        # Find primary complexity
        if complexity_scores:
            primary_complexity = max(complexity_scores.items(), key=lambda x: x[1]['score'])[0]
            primary_score = complexity_scores[primary_complexity]['complexity_value']
        else:
            primary_complexity = 'linear'
            primary_score = 0.5
        
        return {
            'complexity_scores': complexity_scores,
            'primary_complexity': primary_complexity,
            'complexity_score': primary_score,
            'total_matches': sum(len(data['matches']) for data in complexity_scores.values())
        }
    
    def _analyze_resource_requirements(self, query: str) -> Dict[str, Any]:
        """Analyze resource requirement patterns."""
        detected_resources = {}
        total_resource_score = 0.0
        
        for resource_type, data in self.resource_patterns.items():
            matches = 0
            matched_keywords = []
            
            # Check keywords
            for keyword in data['keywords']:
                if keyword in query:
                    matches += 1
                    matched_keywords.append(keyword)
            
            # Check patterns
            for pattern in data.get('compiled_patterns', []):
                pattern_matches = len(pattern.findall(query))
                matches += pattern_matches
            
            if matches > 0:
                resource_score = matches * data['resource_score']
                detected_resources[resource_type] = {
                    'matches': matches,
                    'keywords': matched_keywords,
                    'resource_score': resource_score,
                    'resource_type': data['resource_type']
                }
                total_resource_score += resource_score
        
        # Normalize total score
        normalized_score = min(total_resource_score / 3.0, 1.0)  # Normalize by max expected score
        
        return {
            'detected_resources': detected_resources,
            'total_resource_score': normalized_score,
            'resource_diversity': len(detected_resources),
            'primary_resource_type': max(
                detected_resources.items(), 
                key=lambda x: x[1]['resource_score']
            )[1]['resource_type'] if detected_resources else 'cpu'
        }
    
    def _analyze_scale_indicators(self, query: str) -> Dict[str, Any]:
        """Analyze scale indicators in query."""
        scale_scores = {}
        
        for scale_type, data in self.scale_patterns.items():
            score = 0
            matches = []
            
            # Check keywords
            for keyword in data['keywords']:
                if keyword in query:
                    score += 1
                    matches.append(keyword)
            
            # Check patterns
            for pattern in data.get('compiled_patterns', []):
                pattern_matches = len(pattern.findall(query))
                score += pattern_matches
            
            scale_scores[scale_type] = {
                'score': score,
                'matches': matches,
                'multiplier': data['scale_multiplier']
            }
        
        # Determine primary scale
        if scale_scores and max(scale_scores[s]['score'] for s in scale_scores) > 0:
            primary_scale = max(scale_scores.items(), key=lambda x: x[1]['score'])[0]
            scale_multiplier = scale_scores[primary_scale]['multiplier']
        else:
            primary_scale = 'medium_scale'
            scale_multiplier = 0.6
        
        return {
            'scale_scores': scale_scores,
            'primary_scale': primary_scale,
            'scale_multiplier': scale_multiplier,
            'total_scale_indicators': sum(data['score'] for data in scale_scores.values())
        }
    
    def _analyze_data_structures(self, query: str) -> Dict[str, Any]:
        """Analyze data structure mentions in query."""
        detected_structures = {}
        max_complexity = 0.0
        
        for structure, complexity in self.data_structure_complexity.items():
            if structure in query:
                detected_structures[structure] = complexity
                max_complexity = max(max_complexity, complexity)
        
        return {
            'detected_structures': detected_structures,
            'structure_count': len(detected_structures),
            'max_structure_complexity': max_complexity,
            'avg_structure_complexity': sum(detected_structures.values()) / len(detected_structures) if detected_structures else 0.0
        }
    
    def _analyze_computational_operations(self, query: str) -> Dict[str, Any]:
        """Analyze computational operations mentioned in query."""
        # High-complexity operations
        high_ops = ['optimization', 'machine learning', 'neural network', 'deep learning', 
                   'artificial intelligence', 'computer vision', 'natural language processing']
        
        # Medium-complexity operations
        medium_ops = ['sorting', 'searching', 'filtering', 'aggregation', 'transformation',
                     'parsing', 'validation', 'compression']
        
        # Low-complexity operations
        low_ops = ['reading', 'writing', 'copying', 'moving', 'deleting', 'displaying']
        
        high_count = sum(1 for op in high_ops if op in query)
        medium_count = sum(1 for op in medium_ops if op in query)
        low_count = sum(1 for op in low_ops if op in query)
        
        # Calculate operation complexity score
        operation_score = (high_count * 1.0 + medium_count * 0.6 + low_count * 0.2) / 5.0
        operation_score = min(operation_score, 1.0)
        
        return {
            'high_complexity_ops': high_count,
            'medium_complexity_ops': medium_count,
            'low_complexity_ops': low_count,
            'operation_score': operation_score,
            'total_operations': high_count + medium_count + low_count
        }
    
    def _count_computational_indicators(self, query: str) -> Dict[str, int]:
        """Count various computational indicators."""
        indicators = {
            'algorithm_keywords': 0,
            'performance_keywords': 0,
            'scale_keywords': 0,
            'complexity_keywords': 0
        }
        
        algorithm_keywords = ['algorithm', 'method', 'approach', 'technique', 'procedure']
        performance_keywords = ['performance', 'speed', 'efficiency', 'optimization', 'throughput']
        scale_keywords = ['scale', 'scalable', 'distributed', 'parallel', 'concurrent']
        complexity_keywords = ['complexity', 'time', 'space', 'memory', 'computational']
        
        indicators['algorithm_keywords'] = sum(1 for kw in algorithm_keywords if kw in query)
        indicators['performance_keywords'] = sum(1 for kw in performance_keywords if kw in query)
        indicators['scale_keywords'] = sum(1 for kw in scale_keywords if kw in query)
        indicators['complexity_keywords'] = sum(1 for kw in complexity_keywords if kw in query)
        
        return indicators
    
    def _calculate_computational_score(
        self, algorithm: Dict, resource: Dict, scale: Dict, structure: Dict, operation: Dict
    ) -> float:
        """Calculate overall computational complexity score."""
        # Component scores
        algorithm_score = algorithm.get('complexity_score', 0.5)
        resource_score = resource.get('total_resource_score', 0.5)
        scale_multiplier = scale.get('scale_multiplier', 0.6)
        structure_score = structure.get('max_structure_complexity', 0.3)
        operation_score = operation.get('operation_score', 0.3)
        
        # Base computational score
        base_score = (
            algorithm_score * 0.35 +
            resource_score * 0.25 +
            structure_score * 0.2 +
            operation_score * 0.2
        )
        
        # Apply scale multiplier
        final_score = base_score * (0.5 + scale_multiplier * 0.5)  # Scale factor between 0.5 and 1.0
        
        return min(final_score, 1.0)
    
    def _calculate_algorithmic_confidence(
        self, algorithm: Dict, resource: Dict, scale: Dict, structure: Dict, operation: Dict
    ) -> float:
        """Calculate confidence based on computational pattern matching quality."""
        confidence = 0.4  # Base confidence
        
        # Boost from algorithm matches
        total_algo_matches = algorithm.get('total_matches', 0)
        if total_algo_matches > 0:
            confidence += min(total_algo_matches * 0.05, 0.2)
        
        # Boost from resource detection
        resource_diversity = resource.get('resource_diversity', 0)
        if resource_diversity > 0:
            confidence += min(resource_diversity * 0.05, 0.15)
        
        # Boost from scale indicators
        scale_indicators = scale.get('total_scale_indicators', 0)
        if scale_indicators > 0:
            confidence += min(scale_indicators * 0.03, 0.1)
        
        # Boost from data structures
        structure_count = structure.get('structure_count', 0)
        if structure_count > 0:
            confidence += min(structure_count * 0.05, 0.1)
        
        # Boost from operations
        total_ops = operation.get('total_operations', 0)
        if total_ops > 0:
            confidence += min(total_ops * 0.02, 0.08)
        
        return min(confidence, 0.85)  # Cap algorithmic confidence at 85%
    
    def _analyze_ml(self, query: str) -> Dict[str, Any]:
        """
        Perform ML analysis using T5-small for computational understanding.
        
        Args:
            query: Query text to analyze
            
        Returns:
            Dictionary with score, confidence, features, and metadata
        """
        try:
            # Ensure T5-small model is available
            if not self._t5_model:
                if not self.model_manager:
                    raise ValueError("ModelManager not set - cannot load T5-small")
                
                # Load T5-small model through ModelManager
                self._t5_model = self.model_manager.get_model(self.ml_model_name)
                if not self._t5_model:
                    raise ValueError(f"Failed to load T5-small model: {self.ml_model_name}")
            
            # 1. Generate query embedding
            query_embedding = self._get_query_embedding(query)
            
            # 2. Compare with computational complexity anchors
            anchor_similarities = self._compute_anchor_similarities(query_embedding)
            
            # 3. Computational reasoning analysis
            reasoning_analysis = self._analyze_computational_reasoning(query, query_embedding)
            
            # 4. Generate computational insights using T5 (if applicable)
            t5_insights = self._generate_computational_insights(query)
            
            # 5. Calculate complexity score based on ML analysis
            complexity_score = self._calculate_ml_complexity_score(
                anchor_similarities, reasoning_analysis, t5_insights
            )
            
            # 6. Estimate confidence based on ML analysis quality
            confidence = self._calculate_ml_confidence(
                query_embedding, anchor_similarities, reasoning_analysis, t5_insights
            )
            
            # 7. Extract ML features for explainability
            features = {
                'query_embedding_norm': float(np.linalg.norm(query_embedding)),
                'anchor_similarities': anchor_similarities,
                'reasoning_analysis': reasoning_analysis,
                't5_insights': t5_insights,
                'embedding_dimensionality': query_embedding.shape[0] if hasattr(query_embedding, 'shape') else len(query_embedding)
            }
            
            # 8. ML-specific metadata
            metadata = {
                'analysis_method': 'ml_t5_small',
                'model_name': self.ml_model_name,
                'embedding_model': 'T5-small',
                'high_complexity_similarity': anchor_similarities.get('high_complexity', 0.0),
                'medium_complexity_similarity': anchor_similarities.get('medium_complexity', 0.0),
                'low_complexity_similarity': anchor_similarities.get('low_complexity', 0.0),
                'reasoning_type': reasoning_analysis.get('primary_reasoning', 'algorithmic_reasoning')
            }
            
            logger.debug(f"ML computational analysis: score={complexity_score:.3f}, "
                        f"confidence={confidence:.3f}, model={self.ml_model_name}")
            
            return {
                'score': complexity_score,
                'confidence': confidence,
                'features': features,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"ML computational analysis failed: {e}")
            return {
                'score': 0.6,
                'confidence': 0.4,
                'features': {'error': str(e)},
                'metadata': {'analysis_method': 'ml_fallback', 'error': str(e)}
            }
    
    def _get_query_embedding(self, query: str) -> np.ndarray:
        """Get T5-small embedding for query."""
        try:
            # Handle model format - could be direct model or dict from ModelManager
            model = self._t5_model
            tokenizer = None
            
            if isinstance(self._t5_model, dict):
                model = self._t5_model.get('model')
                tokenizer = self._t5_model.get('tokenizer')
            
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
                    # Handle T5 encoder-decoder architecture
                    if hasattr(model, 'encoder') and model.config.model_type == 't5':
                        # Use encoder-only for T5 models
                        encoder_outputs = model.encoder(**inputs)
                        embedding = encoder_outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
                    else:
                        # Standard BERT-style models
                        outputs = model(**inputs)
                        embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
            else:
                # Fallback for direct transformer models (legacy)
                inputs = self._t5_model.tokenizer(query, return_tensors="pt", truncation=True, max_length=512)
                with torch.no_grad():
                    # Handle T5 encoder-decoder architecture in legacy mode too
                    if hasattr(self._t5_model, 'encoder') and hasattr(self._t5_model, 'config') and self._t5_model.config.model_type == 't5':
                        encoder_outputs = self._t5_model.encoder(**inputs)
                        embedding = encoder_outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
                    else:
                        outputs = self._t5_model(**inputs)
                        embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to get T5-small embedding: {e}")
            # Return zero embedding as fallback
            return np.zeros(512)  # Standard T5-small embedding size
    
    def _compute_anchor_similarities(self, query_embedding: np.ndarray) -> Dict[str, float]:
        """Compute similarities to computational complexity anchors."""
        similarities = {}
        
        try:
            for complexity_level, anchor_texts in self.computational_anchors.items():
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
    
    def _analyze_computational_reasoning(self, query: str, embedding: np.ndarray) -> Dict[str, Any]:
        """Analyze computational reasoning using embeddings."""
        try:
            reasoning_similarities = {}
            
            for reasoning_type, anchor_texts in self.reasoning_anchors.items():
                type_similarities = []
                
                for anchor_text in anchor_texts:
                    # Get or compute reasoning anchor embedding
                    reasoning_key = f"reasoning_{anchor_text}"
                    if reasoning_key not in self._anchor_embeddings:
                        self._anchor_embeddings[reasoning_key] = self._get_query_embedding(anchor_text)
                    
                    anchor_embedding = self._anchor_embeddings[reasoning_key]
                    similarity = self._cosine_similarity(embedding, anchor_embedding)
                    type_similarities.append(similarity)
                
                reasoning_similarities[reasoning_type] = max(type_similarities) if type_similarities else 0.0
            
            # Find primary reasoning type
            if reasoning_similarities:
                primary_reasoning = max(reasoning_similarities.items(), key=lambda x: x[1])[0]
                reasoning_confidence = reasoning_similarities[primary_reasoning]
            else:
                primary_reasoning = 'algorithmic_reasoning'
                reasoning_confidence = 0.5
            
            return {
                'reasoning_similarities': reasoning_similarities,
                'primary_reasoning': primary_reasoning,
                'reasoning_confidence': reasoning_confidence
            }
            
        except Exception as e:
            logger.warning(f"Computational reasoning analysis failed: {e}")
            return {
                'reasoning_similarities': {},
                'primary_reasoning': 'algorithmic_reasoning',
                'reasoning_confidence': 0.5
            }
    
    def _generate_computational_insights(self, query: str) -> Dict[str, Any]:
        """Generate computational insights using T5 if applicable."""
        try:
            # For computational analysis, T5 insights are more limited
            # Focus on embedding-based analysis rather than text generation
            
            # Simple heuristic-based insights
            insights = {
                'has_algorithmic_focus': any(word in query.lower() for word in ['algorithm', 'complexity', 'performance']),
                'has_scale_focus': any(word in query.lower() for word in ['scale', 'distributed', 'parallel']),
                'has_resource_focus': any(word in query.lower() for word in ['memory', 'cpu', 'storage']),
                'query_length': len(query.split()),
                'computational_density': sum(1 for word in query.lower().split() 
                                           if word in ['compute', 'process', 'algorithm', 'optimize', 'performance'])
            }
            
            # Calculate insight score
            insight_factors = [
                insights['has_algorithmic_focus'],
                insights['has_scale_focus'], 
                insights['has_resource_focus']
            ]
            insight_score = sum(insight_factors) / len(insight_factors)
            insights['insight_score'] = insight_score
            
            return insights
            
        except Exception as e:
            logger.warning(f"T5 computational insights generation failed: {e}")
            return {
                'has_algorithmic_focus': False,
                'has_scale_focus': False,
                'has_resource_focus': False,
                'query_length': 0,
                'computational_density': 0,
                'insight_score': 0.5
            }
    
    def _calculate_ml_complexity_score(
        self, anchor_similarities: Dict[str, float], reasoning_analysis: Dict[str, Any], insights: Dict[str, Any]
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
            
            # Reasoning contribution
            reasoning_confidence = reasoning_analysis.get('reasoning_confidence', 0.5)
            reasoning_type = reasoning_analysis.get('primary_reasoning', 'algorithmic_reasoning')
            
            reasoning_complexity = {
                'system_design': 0.8,
                'resource_planning': 0.7,
                'algorithmic_reasoning': 0.6
            }
            
            reasoning_score = reasoning_complexity.get(reasoning_type, 0.6) * reasoning_confidence
            reasoning_contribution = reasoning_score * 0.3
            
            # Insights contribution
            insight_contribution = insights.get('insight_score', 0.5) * 0.2
            
            # Combined score
            ml_score = min(
                weighted_similarity * 0.5 + reasoning_contribution + insight_contribution,
                1.0
            )
            
            return max(0.0, ml_score)
            
        except Exception as e:
            logger.warning(f"ML complexity score calculation failed: {e}")
            return 0.5
    
    def _calculate_ml_confidence(
        self, embedding: np.ndarray, similarities: Dict[str, float], 
        reasoning: Dict[str, Any], insights: Dict[str, Any]
    ) -> float:
        """Calculate confidence based on ML analysis quality."""
        try:
            # Base confidence from embedding quality
            embedding_quality = min(np.linalg.norm(embedding) / 25.0, 0.4)
            
            # Confidence from similarity clarity
            max_similarity = max(similarities.values()) if similarities else 0.0
            similarity_confidence = max_similarity * 0.3
            
            # Confidence from reasoning analysis
            reasoning_confidence = reasoning.get('reasoning_confidence', 0.0) * 0.2
            
            # Confidence from insights quality
            insight_confidence = insights.get('insight_score', 0.0) * 0.1
            
            # Combined confidence
            total_confidence = embedding_quality + similarity_confidence + reasoning_confidence + insight_confidence
            
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