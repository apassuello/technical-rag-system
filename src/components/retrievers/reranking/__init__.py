"""
Neural Reranking Module for Advanced Retriever.

This module provides sophisticated neural reranking capabilities for the Epic 2 
Advanced Retriever system. It includes cross-encoder models, adaptive strategies,
score fusion, and performance optimization for enhanced retrieval quality.

Key Components:
- NeuralReranker: Main neural reranking orchestrator
- CrossEncoderModels: Model management and inference optimization
- ScoreFusion: Advanced score combination strategies
- AdaptiveStrategies: Query-type aware reranking approaches
- PerformanceOptimizer: Latency and throughput optimization

Features:
- Cross-encoder transformer models (ms-marco-MiniLM-L6-v2)
- Keras/TensorFlow and sentence-transformers backend support
- Query-type adaptive reranking strategies
- Advanced neural + retrieval score fusion
- <200ms additional latency optimization
- Batch processing and model caching
- Graceful degradation and error handling
"""

from .neural_reranker import NeuralReranker
from .cross_encoder_models import CrossEncoderModels, ModelManager
from .score_fusion import ScoreFusion, WeightedFusion, LearnedFusion
from .adaptive_strategies import AdaptiveStrategies, QueryTypeDetector
from .performance_optimizer import PerformanceOptimizer, BatchProcessor

__all__ = [
    "NeuralReranker",
    "CrossEncoderModels", 
    "ModelManager",
    "ScoreFusion",
    "WeightedFusion", 
    "LearnedFusion",
    "AdaptiveStrategies",
    "QueryTypeDetector",
    "PerformanceOptimizer",
    "BatchProcessor"
]

# Version info
__version__ = "1.0.0"
__epic__ = "Epic 2 Week 3"
__status__ = "Production Ready"