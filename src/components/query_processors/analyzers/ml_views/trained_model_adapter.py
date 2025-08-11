"""
Trained Model Adapter for Epic 1 Integration.

This module provides the bridge between our trained PyTorch feature-based models
and the existing Epic 1 ML infrastructure framework. It wraps our trained models
to work seamlessly with the existing view interface while maintaining high performance.

Key Classes:
- TrainedModelAdapter: Main adapter for trained PyTorch models
- FeatureBasedView: View implementation using trained models
- Epic1Predictor: Wrapper for the trained predictor

Design Principles:
- Bridge architecture pattern for seamless integration
- Feature-based approach with our trained models
- Fallback to algorithmic approaches when needed
- Performance monitoring and error handling
"""

import os
import json
import time
import logging
import asyncio
import torch
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import sys

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from .base_view import MLView
from .view_result import ViewResult, AnalysisMethod

logger = logging.getLogger(__name__)


class TrainedModelAdapter:
    """
    Adapter class to bridge our trained PyTorch models with Epic 1 infrastructure.
    
    This class loads our trained models and provides a unified interface
    for complexity analysis that integrates with the existing system.
    """
    
    def __init__(self, model_dir: str = "models/epic1"):
        """
        Initialize the trained model adapter.
        
        Args:
            model_dir: Directory containing trained models
        """
        self.model_dir = Path(model_dir)
        self.predictor = None
        self.system_config = None
        
        # Performance tracking
        self._prediction_count = 0
        self._total_prediction_time = 0.0
        self._load_error_count = 0
        
        # Initialize adapter
        self._initialize_adapter()
        
        logger.info(f"TrainedModelAdapter initialized with model_dir: {model_dir}")
    
    def _initialize_adapter(self) -> None:
        """Initialize the adapter by loading trained models."""
        try:
            # Load system configuration
            config_path = self.model_dir / "epic1_system_config.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    self.system_config = json.load(f)
                    logger.debug(f"Loaded system config: {self.system_config['epic1_system_info']['version']}")
            
            # Import and initialize our trained predictor
            predictor_path = self.model_dir / "epic1_predictor.py"
            if predictor_path.exists():
                # Import the predictor dynamically
                spec = importlib.util.spec_from_file_location("epic1_predictor", predictor_path)
                predictor_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(predictor_module)
                
                # Initialize predictor
                self.predictor = predictor_module.Epic1Predictor(str(self.model_dir))
                logger.info("Epic1Predictor loaded successfully")
            else:
                logger.error(f"Predictor script not found at {predictor_path}")
                
        except Exception as e:
            self._load_error_count += 1
            logger.error(f"Failed to initialize TrainedModelAdapter: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if the trained models are available and loaded."""
        return self.predictor is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded models."""
        if not self.system_config:
            return {"status": "not_loaded"}
        
        return {
            "status": "loaded",
            "version": self.system_config["epic1_system_info"]["version"],
            "training_date": self.system_config["epic1_system_info"]["training_date"],
            "dataset_size": self.system_config["epic1_system_info"]["dataset_size"],
            "best_fusion_method": self.system_config["epic1_system_info"]["best_fusion_method"],
            "performance_summary": self.system_config["epic1_system_info"]["performance_summary"]
        }
    
    async def predict_complexity(self, query: str) -> Dict[str, Any]:
        """
        Predict query complexity using trained models.
        
        Args:
            query: Query text to analyze
            
        Returns:
            Dictionary with prediction results
        """
        if not self.is_available():
            raise RuntimeError("Trained models not available")
        
        start_time = time.time()
        
        try:
            # Use our trained predictor
            prediction = self.predictor.predict(query)
            
            prediction_time_ms = (time.time() - start_time) * 1000
            self._record_prediction(prediction_time_ms, success=True)
            
            # Convert to expected format
            return {
                'score': prediction['complexity_score'],
                'level': prediction['complexity_level'],
                'confidence': self._calculate_confidence(prediction),
                'view_scores': prediction['view_scores'],
                'fusion_method': prediction['fusion_method'],
                'metadata': {
                    'model_version': prediction['metadata']['model_version'],
                    'prediction_time_ms': prediction_time_ms,
                    'fusion_method': prediction['fusion_method']
                },
                'features': self._extract_features(prediction)
            }
            
        except Exception as e:
            prediction_time_ms = (time.time() - start_time) * 1000
            self._record_prediction(prediction_time_ms, success=False)
            logger.error(f"Prediction failed: {e}")
            raise
    
    def _calculate_confidence(self, prediction: Dict[str, Any]) -> float:
        """
        Calculate confidence score based on prediction characteristics.
        
        Args:
            prediction: Prediction result from trained model
            
        Returns:
            Confidence score between 0 and 1
        """
        try:
            view_scores = prediction['view_scores']
            scores = list(view_scores.values())
            
            # Base confidence on consistency across views
            mean_score = np.mean(scores)
            std_score = np.std(scores)
            
            # High consistency = high confidence
            consistency_factor = max(0.0, 1.0 - (std_score * 2))
            
            # Distance from decision boundaries
            complexity_score = prediction['complexity_score']
            
            # Distance from thresholds (0.35 and 0.7)
            if complexity_score <= 0.35:
                boundary_distance = complexity_score / 0.35
            elif complexity_score >= 0.7:
                boundary_distance = (complexity_score - 0.7) / 0.3
            else:
                # In the medium range - distance from either boundary
                dist_to_lower = (complexity_score - 0.35) / 0.35
                dist_to_upper = (0.7 - complexity_score) / 0.35
                boundary_distance = min(dist_to_lower, dist_to_upper)
            
            boundary_factor = min(1.0, boundary_distance * 2)
            
            # Combine factors
            confidence = (consistency_factor * 0.6 + boundary_factor * 0.4)
            
            # Ensure confidence is in valid range
            return max(0.1, min(0.95, confidence))
            
        except Exception as e:
            logger.warning(f"Confidence calculation failed: {e}")
            return 0.7  # Default confidence
    
    def _extract_features(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract features from prediction for analysis.
        
        Args:
            prediction: Prediction result
            
        Returns:
            Feature dictionary
        """
        return {
            'view_scores': prediction['view_scores'],
            'complexity_score': prediction['complexity_score'],
            'complexity_level': prediction['complexity_level'],
            'fusion_method': prediction['fusion_method']
        }
    
    def _record_prediction(self, prediction_time_ms: float, success: bool = True) -> None:
        """Record prediction performance metrics."""
        self._prediction_count += 1
        self._total_prediction_time += prediction_time_ms
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the adapter."""
        avg_time = self._total_prediction_time / self._prediction_count if self._prediction_count > 0 else 0.0
        
        return {
            'prediction_count': self._prediction_count,
            'total_prediction_time_ms': self._total_prediction_time,
            'average_prediction_time_ms': avg_time,
            'load_error_count': self._load_error_count,
            'model_info': self.get_model_info()
        }


class FeatureBasedView(MLView):
    """
    Feature-based view implementation using our trained models.
    
    This class wraps our trained models to work with the existing
    Epic 1 view interface while maintaining the feature-based approach.
    """
    
    def __init__(
        self,
        view_name: str,
        model_adapter: TrainedModelAdapter,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize feature-based view.
        
        Args:
            view_name: Name of this view
            model_adapter: Trained model adapter instance
            config: Configuration dictionary
        """
        # Initialize parent without ML model name (we use our adapter)
        super().__init__(view_name, "trained_model", config)
        
        self.model_adapter = model_adapter
        self.view_name = view_name
        
        # Initialize algorithmic fallback
        self._initialize_algorithmic_fallback()
        
        logger.debug(f"FeatureBasedView initialized for '{view_name}'")
    
    def _initialize_algorithmic_fallback(self) -> None:
        """Initialize simple algorithmic fallback for reliability."""
        # Simple keyword-based fallback
        self.complexity_keywords = {
            'simple': ['what', 'how', 'define', 'explain'],
            'medium': ['implement', 'configure', 'setup', 'best'],
            'complex': ['optimization', 'distributed', 'scalable', 'architecture']
        }
    
    async def _analyze_ml(self, query: str) -> Dict[str, Any]:
        """
        Analyze query using our trained models.
        
        Args:
            query: Query text to analyze
            
        Returns:
            Analysis result dictionary
        """
        if not self.model_adapter.is_available():
            raise RuntimeError("Trained model adapter not available")
        
        # Get full prediction from our trained model
        prediction = await self.model_adapter.predict_complexity(query)
        
        # Extract view-specific score if available
        view_score = prediction['view_scores'].get(self.view_name, prediction['score'])
        
        return {
            'score': view_score,
            'confidence': prediction['confidence'],
            'features': {
                f'{self.view_name}_score': view_score,
                'overall_score': prediction['score'],
                'complexity_level': prediction['level'],
                'view_scores': prediction['view_scores']
            },
            'metadata': {
                'model_version': prediction['metadata']['model_version'],
                'fusion_method': prediction['metadata']['fusion_method'],
                'prediction_time_ms': prediction['metadata']['prediction_time_ms'],
                'analysis_method': 'trained_model'
            }
        }
    
    async def _analyze_algorithmic_fallback(self, query: str) -> Dict[str, Any]:
        """
        Simple algorithmic fallback analysis.
        
        Args:
            query: Query text to analyze
            
        Returns:
            Fallback analysis result
        """
        query_lower = query.lower()
        
        # Simple keyword-based scoring
        simple_score = sum(1 for kw in self.complexity_keywords['simple'] if kw in query_lower)
        medium_score = sum(1 for kw in self.complexity_keywords['medium'] if kw in query_lower)
        complex_score = sum(1 for kw in self.complexity_keywords['complex'] if kw in query_lower)
        
        # Normalize by query length
        query_length = len(query_lower.split())
        length_factor = min(1.0, query_length / 20.0)  # Longer queries tend to be more complex
        
        # Calculate score
        if complex_score > 0:
            base_score = 0.7 + (complex_score * 0.05)
        elif medium_score > 0:
            base_score = 0.4 + (medium_score * 0.05)
        else:
            base_score = 0.2 + (simple_score * 0.05)
        
        # Apply length factor
        final_score = min(0.95, base_score + (length_factor * 0.2))
        
        return {
            'score': final_score,
            'confidence': 0.5,  # Lower confidence for fallback
            'features': {
                'keyword_scores': {
                    'simple': simple_score,
                    'medium': medium_score,
                    'complex': complex_score
                },
                'query_length': query_length,
                'length_factor': length_factor
            },
            'metadata': {
                'analysis_method': 'algorithmic_fallback',
                'fallback_reason': 'trained_model_unavailable'
            }
        }


# Dynamic import handling
try:
    import importlib.util
except ImportError:
    logger.error("importlib.util not available - trained model loading will fail")


class Epic1MLSystem:
    """
    Complete Epic 1 ML system integration.
    
    This class provides the full integration of our trained models
    with the Epic 1 infrastructure, managing all 5 views and providing
    a unified interface for complexity analysis.
    """
    
    def __init__(self, model_dir: str = "models/epic1"):
        """
        Initialize Epic 1 ML system.
        
        Args:
            model_dir: Directory containing trained models
        """
        self.model_dir = model_dir
        self.model_adapter = TrainedModelAdapter(model_dir)
        
        # Initialize all views
        self.views = {}
        self._initialize_views()
        
        logger.info("Epic1MLSystem initialized with trained models")
    
    def _initialize_views(self) -> None:
        """Initialize all 5 view components."""
        view_names = ['technical', 'linguistic', 'task', 'semantic', 'computational']
        
        for view_name in view_names:
            self.views[view_name] = FeatureBasedView(
                view_name=view_name,
                model_adapter=self.model_adapter
            )
            logger.debug(f"Initialized {view_name} view")
    
    def is_available(self) -> bool:
        """Check if the ML system is ready for analysis."""
        return self.model_adapter.is_available()
    
    async def analyze_complexity(self, query: str) -> Dict[str, Any]:
        """
        Perform complete multi-view complexity analysis.
        
        Args:
            query: Query text to analyze
            
        Returns:
            Complete analysis results
        """
        if not self.is_available():
            raise RuntimeError("Epic 1 ML system not available")
        
        start_time = time.time()
        
        try:
            # Get full prediction using our trained system
            prediction = await self.model_adapter.predict_complexity(query)
            
            # Get individual view results
            view_results = {}
            for view_name, view in self.views.items():
                try:
                    view_result = await view.analyze(query, mode='ml')
                    view_results[view_name] = {
                        'score': view_result.score,
                        'confidence': view_result.confidence,
                        'method': view_result.method.value,
                        'latency_ms': view_result.latency_ms
                    }
                except Exception as e:
                    logger.warning(f"View {view_name} analysis failed: {e}")
                    view_results[view_name] = {
                        'score': prediction['view_scores'].get(view_name, 0.5),
                        'confidence': 0.5,
                        'method': 'fallback',
                        'latency_ms': 0.0
                    }
            
            analysis_time_ms = (time.time() - start_time) * 1000
            
            return {
                'complexity_score': prediction['score'],
                'complexity_level': prediction['level'],
                'overall_confidence': prediction['confidence'],
                'view_results': view_results,
                'view_scores': prediction['view_scores'],
                'fusion_method': prediction['fusion_method'],
                'analysis_time_ms': analysis_time_ms,
                'metadata': {
                    'model_version': prediction['metadata']['model_version'],
                    'system_info': self.model_adapter.get_model_info(),
                    'analysis_timestamp': time.time()
                }
            }
            
        except Exception as e:
            analysis_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Complete analysis failed: {e}")
            raise
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get complete system performance statistics."""
        return {
            'model_adapter_stats': self.model_adapter.get_performance_stats(),
            'view_stats': {
                view_name: view.get_performance_stats() 
                for view_name, view in self.views.items()
            },
            'system_availability': self.is_available()
        }