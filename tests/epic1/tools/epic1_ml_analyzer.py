"""
Epic 1 ML Analyzer - Multi-View Query Complexity Analysis Orchestrator.

This is the main orchestrator for Epic 1's ML-powered query complexity analysis,
coordinating 5 specialized views to achieve >85% classification accuracy through
intelligent multi-model routing.

Key Features:
- Orchestrates 5 ML views: Technical, Linguistic, Task, Semantic, Computational
- Uses existing ML infrastructure (ModelManager, MemoryMonitor, etc.)
- Integrates with existing ComplexityClassifier for meta-classification
- Provides comprehensive analysis results for multi-model routing
- Maintains <50ms routing overhead through efficient coordination

Architecture:
- Multi-view stacking with pretrained transformer models
- Hybrid algorithmic/ML approach for reliability
- Meta-classifier combines view outputs for final decision
- Comprehensive error handling and fallback strategies
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import sys
import numpy as np
import torch
import torch.nn as nn
import joblib

# Imports handled by conftest.py
import pytest

from .base_analyzer import BaseQueryAnalyzer
from ..base import QueryAnalysis

# Core imports that are always needed
from .ml_views.view_result import ViewResult, AnalysisResult, AnalysisMethod, ComplexityLevel

# Import type hints needed for method signatures
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .components.complexity_classifier import ComplexityClassification

# Heavy imports will be done lazily to avoid class compilation issues
# from .ml_views.technical_complexity_view import TechnicalComplexityView
# from .ml_views.linguistic_complexity_view import LinguisticComplexityView  
# from .ml_views.task_complexity_view import TaskComplexityView
# from .ml_views.semantic_complexity_view import SemanticComplexityView
# from .ml_views.computational_complexity_view import ComputationalComplexityView
# from .components.complexity_classifier import ComplexityClassifier, ComplexityClassification
# from .components.model_recommender import ModelRecommender
# from .ml_models.model_manager import ModelManager
# from .ml_models.performance_monitor import PerformanceMonitor
# from .ml_models.memory_monitor import MemoryMonitor

logger = logging.getLogger(__name__)


class Epic1MLAnalyzer(BaseQueryAnalyzer):
    """
    Epic 1 ML Analyzer - Multi-View Query Complexity Analysis Orchestrator.
    
    This orchestrator coordinates 5 specialized ML views to analyze query complexity
    from multiple perspectives, providing comprehensive analysis for intelligent
    multi-model routing.
    
    Views:
    1. Technical: SciBERT + technical vocabulary analysis
    2. Linguistic: DistilBERT + syntactic pattern analysis  
    3. Task: DeBERTa-v3 + Bloom's taxonomy classification
    4. Semantic: Sentence-BERT + semantic relationship analysis
    5. Computational: T5-small + computational pattern analysis
    
    Performance Targets:
    - Classification accuracy: >85% (vs 58.1% rule-based)
    - Analysis time: <50ms total routing overhead
    - Memory usage: <2GB with all models loaded
    - Reliability: 100% (algorithmic fallbacks)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Epic1MLAnalyzer with ML infrastructure and view coordination.
        
        Args:
            config: Configuration dictionary with ML analysis parameters
        """
        # Call parent constructor first
        super().__init__(config)
        
        # Access config from parent (stored as _config) 
        config = self._config
        
        # Core configuration - ALWAYS set these first
        self.memory_budget_gb = config.get('memory_budget_gb', 2.0)
        self.enable_performance_monitoring = config.get('enable_performance_monitoring', True)
        self.parallel_execution = config.get('parallel_execution', True)
        self.fallback_strategy = config.get('fallback_strategy', 'algorithmic')
        self.confidence_threshold = config.get('confidence_threshold', 0.6)
        
        # Performance tracking - ALWAYS initialize
        self._analysis_count = 0
        self._total_analysis_time = 0.0
        self._error_count = 0
        self._view_performance = {}
        
        # Initialize core containers - ALWAYS create these
        self.views = {}
        self.trained_view_models = None
        self.neural_fusion_model = None
        self.ensemble_models = None
        self.model_manager = None
        self.performance_monitor = None
        self.memory_monitor = None
        
        # View weights for meta-classification (sum to 1.0)
        self.view_weights = config.get('view_weights', {
            'technical': 0.25,
            'linguistic': 0.20,
            'task': 0.25,
            'semantic': 0.20,
            'computational': 0.10
        })
        
        # Validate and normalize view weights
        weight_sum = sum(self.view_weights.values())
        if abs(weight_sum - 1.0) > 0.001:
            logger.warning(f"View weights sum to {weight_sum:.3f}, normalizing to 1.0")
            for view in self.view_weights:
                self.view_weights[view] /= weight_sum
        
        # Status tracking for initialization phases
        self._ml_infrastructure_initialized = False
        self._views_initialized = False
        self._meta_classifier_initialized = False
        self._trained_models_loaded = False
        
        # Safe initialization with comprehensive error handling
        self._safe_initialize_ml_infrastructure()
        self._safe_initialize_views()
        self._safe_initialize_meta_classifier()  
        self._safe_load_trained_models()
        
        logger.info(f"Initialized Epic1MLAnalyzer with {len(self.views)} views, "
                   f"memory budget: {self.memory_budget_gb}GB")
    
    def _safe_initialize_ml_infrastructure(self):
        """Safely initialize ML infrastructure with fallbacks."""
        try:
            if hasattr(self, '_initialize_ml_infrastructure'):
                self._initialize_ml_infrastructure()
                self._ml_infrastructure_initialized = True
            else:
                self._setup_minimal_infrastructure()
        except Exception as e:
            logger.warning(f"ML infrastructure initialization failed: {e}, using minimal setup")
            self._setup_minimal_infrastructure()
    
    def _safe_initialize_views(self):
        """Safely initialize views with fallbacks."""
        try:
            if hasattr(self, '_initialize_views'):
                self._initialize_views()
                self._views_initialized = True
            else:
                self.views = {}
        except Exception as e:
            logger.warning(f"Views initialization failed: {e}, using empty views")
            self.views = {}
    
    def _safe_initialize_meta_classifier(self):
        """Safely initialize meta-classifier with fallbacks.""" 
        try:
            if hasattr(self, '_initialize_meta_classifier'):
                self._initialize_meta_classifier()
                self._meta_classifier_initialized = True
            else:
                self._setup_basic_classifier()
        except Exception as e:
            logger.warning(f"Meta-classifier initialization failed: {e}, using basic classifier")
            self._setup_basic_classifier()
    
    def _safe_load_trained_models(self):
        """Safely load trained models with fallbacks."""
        try:
            if hasattr(self, '_load_trained_models'):
                self._load_trained_models()
                self._trained_models_loaded = True
            else:
                logger.info("Trained models not available")
        except Exception as e:
            logger.warning(f"Failed to load trained models: {e}")
    
    def _setup_minimal_infrastructure(self) -> None:
        """Setup minimal infrastructure when full ML infrastructure fails."""
        self.model_manager = None
        self.performance_monitor = None
        self.memory_monitor = None
        logger.info("Using minimal infrastructure (no ML model manager)")
    
    def _setup_basic_classifier(self) -> None:
        """Setup basic classifier when meta-classifier initialization fails."""
        try:
            # Lazy import to avoid class compilation issues
            from .components.complexity_classifier import ComplexityClassifier
            self.complexity_classifier = ComplexityClassifier()
            self.model_recommender = None
            logger.info("Using basic complexity classifier (no model recommender)")
        except Exception as e:
            logger.error(f"Failed to setup basic classifier: {e}")
            self.complexity_classifier = None
            self.model_recommender = None
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure Epic1MLAnalyzer with ML-specific settings.
        
        Args:
            config: Configuration dictionary with ML analysis parameters
        """
        # Call parent configure method
        super().configure(config)
        
        # Update ML-specific configuration (use _config from parent)
        # No need to update again as parent already did this
        
        # Reconfigure core settings
        if 'memory_budget_gb' in config:
            self.memory_budget_gb = config['memory_budget_gb']
            # Note: ModelManager doesn't support runtime memory budget changes
            # Would need to recreate the ModelManager for this change
        
        if 'view_weights' in config:
            new_weights = config['view_weights']
            # Validate weights sum to 1.0
            weight_sum = sum(new_weights.values())
            if abs(weight_sum - 1.0) > 0.001:
                logger.warning(f"View weights sum to {weight_sum:.3f}, normalizing to 1.0")
                for view in new_weights:
                    new_weights[view] /= weight_sum
            self.view_weights = new_weights
        
        if 'parallel_execution' in config:
            self.parallel_execution = config['parallel_execution']
        
        if 'fallback_strategy' in config:
            self.fallback_strategy = config['fallback_strategy']
        
        if 'confidence_threshold' in config:
            self.confidence_threshold = config['confidence_threshold']
        
        # Reconfigure individual views if configurations provided
        if 'views' in config:
            view_configs = config['views']
            for view_name, view_config in view_configs.items():
                if view_name in self.views:
                    try:
                        # Use the view's configure method if available
                        if hasattr(self.views[view_name], 'configure'):
                            self.views[view_name].configure(view_config)
                        else:
                            # Reinitialize view with new config
                            if view_name == 'technical':
                                self.views[view_name] = TechnicalComplexityView(view_config)
                            elif view_name == 'linguistic':
                                self.views[view_name] = LinguisticComplexityView(view_config)
                            elif view_name == 'task':
                                self.views[view_name] = TaskComplexityView(view_config)
                            elif view_name == 'semantic':
                                self.views[view_name] = SemanticComplexityView(view_config)
                            elif view_name == 'computational':
                                self.views[view_name] = ComputationalComplexityView(view_config)
                            
                            # Reset model manager for the view
                            if hasattr(self, 'model_manager'):
                                self.views[view_name].set_model_manager(self.model_manager)
                                
                    except Exception as e:
                        logger.warning(f"Failed to reconfigure {view_name} view: {e}")
        
        # Reconfigure meta-classifier
        if 'meta_classifier' in config:
            try:
                self.complexity_classifier = ComplexityClassifier(config['meta_classifier'])
            except Exception as e:
                logger.warning(f"Failed to reconfigure meta-classifier: {e}")
        
        # Reconfigure model recommender
        if 'model_recommender' in config:
            try:
                self.model_recommender = ModelRecommender(config['model_recommender'])
            except Exception as e:
                logger.warning(f"Failed to reconfigure model recommender: {e}")
        
        logger.info(f"Reconfigured Epic1MLAnalyzer with updated settings")
    
    def get_supported_features(self) -> List[str]:
        """
        Get list of features supported by Epic1MLAnalyzer.
        
        Returns:
            List of supported feature names
        """
        return [
            "complexity_classification",
            "technical_term_extraction", 
            "entity_recognition",
            "syntactic_analysis",
            "bloom_taxonomy_classification",
            "semantic_relationship_analysis",
            "computational_pattern_detection",
            "ml_powered_analysis",
            "multi_view_stacking",
            "model_recommendation",
            "confidence_scoring",
            "performance_monitoring",
            "fallback_strategies",
            "parallel_execution",
            "memory_management"
        ]
    
    def _analyze_query(self, query: str) -> QueryAnalysis:
        """
        Implement BaseQueryAnalyzer interface to perform ML-powered query analysis.
        
        Args:
            query: User query string
            
        Returns:
            QueryAnalysis with extracted characteristics from ML analysis
        """
        # Use asyncio to run the async analyze method
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async analysis
        ml_result = loop.run_until_complete(self.analyze(query, mode='hybrid'))
        
        # Convert AnalysisResult to QueryAnalysis format
        return self._convert_to_query_analysis(ml_result)
    
    def _convert_to_query_analysis(self, ml_result: AnalysisResult) -> QueryAnalysis:
        """
        Convert ML analysis result to QueryAnalysis format expected by QueryProcessor.
        
        Args:
            ml_result: AnalysisResult from ML analysis
            
        Returns:
            QueryAnalysis with standard format
        """
        try:
            # Extract technical terms from view results
            technical_terms = []
            entities = []
            
            # Technical terms from TechnicalComplexityView
            if 'technical' in ml_result.view_results:
                tech_view = ml_result.view_results['technical']
                if hasattr(tech_view, 'features') and tech_view.features:
                    technical_terms.extend(tech_view.features.get('technical_terms_found', []))
            
            # Entities from LinguisticComplexityView
            if 'linguistic' in ml_result.view_results:
                ling_view = ml_result.view_results['linguistic'] 
                if hasattr(ling_view, 'features') and ling_view.features:
                    entities.extend(ling_view.features.get('entities_found', []))
            
            # Determine intent category based on TaskComplexityView
            intent_category = "general"
            if 'task' in ml_result.view_results:
                task_view = ml_result.view_results['task']
                if hasattr(task_view, 'metadata') and task_view.metadata:
                    task_type = task_view.metadata.get('task_type', 'general')
                    intent_category = task_type
            
            # Determine suggested k based on complexity
            complexity_score = ml_result.complexity_score
            if complexity_score < 0.3:
                suggested_k = 3  # Simple queries need fewer results
            elif complexity_score < 0.7:
                suggested_k = 5  # Medium complexity
            else:
                suggested_k = 8  # Complex queries benefit from more context
            
            # Build comprehensive metadata
            analysis_metadata = {
                'analyzer': 'Epic1MLAnalyzer',
                'ml_analysis_time_ms': ml_result.analysis_time_ms,
                'view_count': len(ml_result.view_results),
                'successful_views': len([v for v in ml_result.view_results.values() if v.confidence > 0]),
                'analysis_method': ml_result.analysis_method.value if hasattr(ml_result.analysis_method, 'value') else str(ml_result.analysis_method),
                'model_recommendation': ml_result.model_recommendation,
                'view_breakdown': {name: v.score for name, v in ml_result.view_results.items()},
                'original_ml_metadata': ml_result.metadata
            }
            
            return QueryAnalysis(
                query=ml_result.query,
                complexity_score=ml_result.complexity_score,
                complexity_level=ml_result.complexity_level,
                technical_terms=technical_terms,
                entities=entities,
                intent_category=intent_category,
                suggested_k=suggested_k,
                confidence=ml_result.confidence,
                metadata=analysis_metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to convert ML analysis result to QueryAnalysis: {e}")
            # Return conservative fallback  
            fallback_query = query  # query is available from the method parameter
            if hasattr(ml_result, 'query'):
                fallback_query = ml_result.query
            
            return QueryAnalysis(
                query=fallback_query,
                complexity_score=0.5,
                complexity_level='medium',
                technical_terms=[],
                entities=[],
                intent_category='general',
                suggested_k=5,
                confidence=0.3,
                metadata={
                    'analyzer': 'Epic1MLAnalyzer',
                    'conversion_error': str(e),
                    'fallback_analysis': True
                }
            )
    
    def _initialize_ml_infrastructure(self) -> None:
        """Initialize the underlying ML infrastructure."""
        try:
            # Lazy import to avoid class compilation issues
            from .ml_models.model_manager import ModelManager
            
            # Initialize model manager with proper parameters
            self.model_manager = ModelManager(
                memory_budget_gb=self.memory_budget_gb,
                cache_size=self._config.get('cache_size', 10),
                enable_quantization=self._config.get('enable_quantization', True),
                enable_monitoring=self.enable_performance_monitoring,
                model_timeout_seconds=self._config.get('model_timeout_seconds', 30.0),
                max_concurrent_loads=self._config.get('max_concurrent_loads', 2)
            )
            
            # Note: ModelManager creates its own MemoryMonitor and PerformanceMonitor
            # We can access them through the model_manager if needed
            self.performance_monitor = None  # Not created separately
            self.memory_monitor = None  # Not created separately
            
            logger.debug("ML infrastructure initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ML infrastructure: {e}")
            raise
    
    def _initialize_views(self) -> None:
        """Initialize all 5 specialized ML views."""
        try:
            # Lazy imports to avoid class compilation issues
            from .ml_views.technical_complexity_view import TechnicalComplexityView
            from .ml_views.linguistic_complexity_view import LinguisticComplexityView
            from .ml_views.task_complexity_view import TaskComplexityView
            from .ml_views.semantic_complexity_view import SemanticComplexityView
            from .ml_views.computational_complexity_view import ComputationalComplexityView
            
            # Initialize all views with their specific configurations
            view_configs = self._config.get('views', {})
            
            self.views = {
                'technical': TechnicalComplexityView(
                    config=view_configs.get('technical', {})
                ),
                'linguistic': LinguisticComplexityView(
                    config=view_configs.get('linguistic', {})
                ),
                'task': TaskComplexityView(
                    config=view_configs.get('task', {})
                ),
                'semantic': SemanticComplexityView(
                    config=view_configs.get('semantic', {})
                ),
                'computational': ComputationalComplexityView(
                    config=view_configs.get('computational', {})
                )
            }
            
            # Set model manager for all views
            for view_name, view in self.views.items():
                view.set_model_manager(self.model_manager)
                logger.debug(f"Initialized {view_name} view with model manager")
            
            logger.info(f"Initialized {len(self.views)} ML views successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ML views: {e}")
            raise
    
    def _initialize_meta_classifier(self) -> None:
        """Initialize the meta-classifier for combining view results."""
        try:
            # Lazy imports to avoid class compilation issues
            from .components.complexity_classifier import ComplexityClassifier
            from .components.model_recommender import ModelRecommender
            
            # Use existing ComplexityClassifier with ML-optimized configuration
            classifier_config = self._config.get('meta_classifier', {})
            
            # Adjust thresholds for ML-based classification (more confident boundaries)
            classifier_config.setdefault('thresholds', {
                'simple': 0.30,   # Lower threshold - ML is more discriminative
                'complex': 0.70   # Higher threshold - ML captures nuance better
            })
            
            self.complexity_classifier = ComplexityClassifier(config=classifier_config)
            
            # Initialize model recommender
            recommender_config = self._config.get('model_recommender', {})
            self.model_recommender = ModelRecommender(config=recommender_config)
            
            logger.debug("Meta-classifier and model recommender initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize meta-classifier: {e}")
            raise
    
    def _load_trained_models(self) -> None:
        """Load trained view models and MetaClassifier if available."""
        models_dir = Path("models/epic1")
        
        if not models_dir.exists():
            logger.warning(f"Models directory not found: {models_dir}")
            return
        
        try:
            # Load trained view models
            self.trained_view_models = {}
            view_model_loaded = False
            
            for view_name in self.views.keys():
                model_path = models_dir / f"{view_name}_model.pth"
                if model_path.exists():
                    try:
                        # Load the simple view model (matching training architecture)
                        model = self._load_simple_view_model(model_path)
                        self.trained_view_models[view_name] = model
                        view_model_loaded = True
                        logger.info(f"Loaded trained model for {view_name} view")
                    except Exception as e:
                        logger.warning(f"Failed to load {view_name} model: {e}")
            
            # Load MetaClassifier
            meta_classifier_path = models_dir / "meta_classifier.pkl"
            scaler_path = models_dir / "meta_classifier_scaler.pkl"
            calibrator_path = models_dir / "confidence_calibrator.pkl"
            
            if meta_classifier_path.exists() and scaler_path.exists():
                self.trained_meta_classifier = joblib.load(meta_classifier_path)
                self.meta_feature_scaler = joblib.load(scaler_path)
                
                if calibrator_path.exists():
                    self.confidence_calibrator = joblib.load(calibrator_path)
                else:
                    self.confidence_calibrator = None
                
                logger.info("Loaded trained MetaClassifier with scaler and calibrator")
            else:
                logger.warning("MetaClassifier not found, using default weighted combination")
                self.trained_meta_classifier = None
            
            # Load fusion models
            try:
                neural_fusion_path = models_dir / "fusion" / "neural_fusion_model.pth"
                if neural_fusion_path.exists():
                    self.neural_fusion_model = self._load_fusion_model(neural_fusion_path)
                    logger.info("Loaded neural fusion model successfully")
                else:
                    self.neural_fusion_model = None
                    
                self.ensemble_models = self._load_ensemble_models()
                if self.ensemble_models:
                    logger.info(f"Loaded {len(self.ensemble_models)} ensemble models")
                    
            except Exception as e:
                logger.warning(f"Failed to load fusion models: {e}")
                self.neural_fusion_model = None
                self.ensemble_models = {}
            
            if view_model_loaded or hasattr(self, 'trained_meta_classifier') or self.neural_fusion_model or self.ensemble_models:
                logger.info(f"Successfully loaded trained models from {models_dir}")
                
        except Exception as e:
            logger.error(f"Error loading trained models: {e}")
            self.trained_view_models = {}
            self.trained_meta_classifier = None
    
    def _load_simple_view_model(self, model_path: Path):
        """Load a simple view model matching the training architecture."""
        
        class SimpleViewModel(nn.Module):
            def __init__(self, input_dim=10, hidden_dim=128):
                super().__init__()
                self.network = nn.Sequential(
                    nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.BatchNorm1d(hidden_dim), nn.Dropout(0.3),
                    nn.Linear(hidden_dim, hidden_dim // 2), nn.ReLU(), nn.BatchNorm1d(hidden_dim // 2), nn.Dropout(0.3),
                    nn.Linear(hidden_dim // 2, hidden_dim // 4), nn.ReLU(), nn.Dropout(0.2),
                    nn.Linear(hidden_dim // 4, 1), nn.Sigmoid()
                )
            
            def forward(self, features):
                return self.network(features).squeeze()
        
        model = SimpleViewModel()
        checkpoint = torch.load(model_path, map_location='cpu')
        model.load_state_dict(checkpoint['model_state_dict'])
        model.eval()
        return model


class NeuralFusionModel(nn.Module):
    """Neural fusion model for combining view predictions - EXACT MATCH to epic1_predictor.py"""
    def __init__(self, input_dim=5, hidden_dim=64):
        super().__init__()
        self.shared_layers = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.BatchNorm1d(hidden_dim), nn.Dropout(0.3),
            nn.Linear(hidden_dim, hidden_dim // 2), nn.ReLU(), nn.BatchNorm1d(hidden_dim // 2), nn.Dropout(0.2)
        )
        self.regression_head = nn.Sequential(
            nn.Linear(hidden_dim // 2, hidden_dim // 4), nn.ReLU(), nn.Dropout(0.1),
            nn.Linear(hidden_dim // 4, 1), nn.Sigmoid()
        )
        self.classification_head = nn.Sequential(
            nn.Linear(hidden_dim // 2, hidden_dim // 4), nn.ReLU(), nn.Dropout(0.1),
            nn.Linear(hidden_dim // 4, 3), nn.Softmax(dim=1)
        )
    
    def forward(self, view_predictions):
        shared_features = self.shared_layers(view_predictions)
        regression_output = self.regression_head(shared_features).squeeze()
        classification_output = self.classification_head(shared_features)
        return regression_output, classification_output

