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

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from .base_analyzer import BaseQueryAnalyzer
from ..base import QueryAnalysis
from .ml_views.technical_complexity_view import TechnicalComplexityView
from .ml_views.linguistic_complexity_view import LinguisticComplexityView
from .ml_views.task_complexity_view import TaskComplexityView
from .ml_views.semantic_complexity_view import SemanticComplexityView
from .ml_views.computational_complexity_view import ComputationalComplexityView
from .ml_views.view_result import ViewResult, AnalysisResult, AnalysisMethod, ComplexityLevel
from .components.complexity_classifier import ComplexityClassifier, ComplexityClassification
from .components.model_recommender import ModelRecommender
from .ml_models.model_manager import ModelManager
from .ml_models.performance_monitor import PerformanceMonitor
from .ml_models.memory_monitor import MemoryMonitor

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
            config: Configuration dictionary with parameters:
                - memory_budget_gb: Memory budget for ML models (default: 2.0)
                - enable_performance_monitoring: Enable performance tracking (default: True)
                - view_weights: Weights for each view in meta-classification
                - parallel_execution: Execute views in parallel (default: True)
                - fallback_strategy: Strategy when ML analysis fails ('algorithmic' or 'conservative')
                - confidence_threshold: Minimum confidence for ML results (default: 0.6)
        """
        self.config = config or {}
        super().__init__(config)
        
        # Core configuration
        self.memory_budget_gb = self.config.get('memory_budget_gb', 2.0)
        self.enable_performance_monitoring = self.config.get('enable_performance_monitoring', True)
        self.parallel_execution = self.config.get('parallel_execution', True)
        self.fallback_strategy = self.config.get('fallback_strategy', 'algorithmic')
        self.confidence_threshold = self.config.get('confidence_threshold', 0.6)
        
        # View weights for meta-classification (sum to 1.0)
        self.view_weights = self.config.get('view_weights', {
            'technical': 0.25,      # Technical complexity often drives model choice
            'linguistic': 0.20,     # Linguistic patterns important for routing
            'task': 0.25,          # Task type crucial for model selection
            'semantic': 0.20,      # Semantic complexity affects reasoning needs
            'computational': 0.10   # Computational needs least predictive for LLM routing
        })
        
        # Validate view weights
        weight_sum = sum(self.view_weights.values())
        if abs(weight_sum - 1.0) > 0.001:
            logger.warning(f"View weights sum to {weight_sum:.3f}, normalizing to 1.0")
            for view in self.view_weights:
                self.view_weights[view] /= weight_sum
        
        # Initialize ML infrastructure
        self._initialize_ml_infrastructure()
        
        # Initialize views
        self._initialize_views()
        
        # Initialize meta-classifier
        self._initialize_meta_classifier()
        
        # Load trained models if available
        self._load_trained_models()
        
        # Performance tracking
        self._analysis_count = 0
        self._total_analysis_time = 0.0
        self._error_count = 0
        self._view_performance = {}
        
        logger.info(f"Initialized Epic1MLAnalyzer with {len(self.views)} views, "
                   f"memory budget: {self.memory_budget_gb}GB, "
                   f"trained models: {'loaded' if hasattr(self, 'trained_meta_classifier') else 'not available'}")
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure Epic1MLAnalyzer with ML-specific settings.
        
        Args:
            config: Configuration dictionary with ML analysis parameters
        """
        # Call parent configure method
        super().configure(config)
        
        # Update ML-specific configuration
        self.config.update(config)
        
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
            # Initialize model manager with proper parameters
            self.model_manager = ModelManager(
                memory_budget_gb=self.memory_budget_gb,
                cache_size=self.config.get('cache_size', 10),
                enable_quantization=self.config.get('enable_quantization', True),
                enable_monitoring=self.enable_performance_monitoring,
                model_timeout_seconds=self.config.get('model_timeout_seconds', 30.0),
                max_concurrent_loads=self.config.get('max_concurrent_loads', 2)
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
            # Initialize all views with their specific configurations
            view_configs = self.config.get('views', {})
            
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
            # Use existing ComplexityClassifier with ML-optimized configuration
            classifier_config = self.config.get('meta_classifier', {})
            
            # Adjust thresholds for ML-based classification (more confident boundaries)
            classifier_config.setdefault('thresholds', {
                'simple': 0.30,   # Lower threshold - ML is more discriminative
                'complex': 0.70   # Higher threshold - ML captures nuance better
            })
            
            self.complexity_classifier = ComplexityClassifier(config=classifier_config)
            
            # Initialize model recommender
            recommender_config = self.config.get('model_recommender', {})
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
            
            if view_model_loaded or hasattr(self, 'trained_meta_classifier'):
                logger.info(f"Successfully loaded trained models from {models_dir}")
                
        except Exception as e:
            logger.error(f"Error loading trained models: {e}")
            self.trained_view_models = {}
            self.trained_meta_classifier = None
    
    def _load_simple_view_model(self, model_path: Path):
        """Load a simple view model matching the training architecture."""
        
        class SimpleViewModel(nn.Module):
            def __init__(self, input_dim: int = 8, hidden_dim: int = 64):
                super().__init__()
                self.network = nn.Sequential(
                    nn.Linear(input_dim, hidden_dim),
                    nn.ReLU(),
                    nn.Dropout(0.2),
                    nn.Linear(hidden_dim, hidden_dim // 2),
                    nn.ReLU(),
                    nn.Dropout(0.2),
                    nn.Linear(hidden_dim // 2, 1),
                    nn.Sigmoid()
                )
            
            def forward(self, features):
                return self.network(features).squeeze()
        
        model = SimpleViewModel()
        checkpoint = torch.load(model_path, map_location='cpu')
        model.load_state_dict(checkpoint['model_state_dict'])
        model.eval()
        return model
    
    def _extract_simple_features(self, query: str) -> np.ndarray:
        """Extract simple features from query (matching training feature extraction)."""
        words = query.split()
        
        features = [
            len(query),                          # Character count
            len(words),                           # Word count
            np.mean([len(w) for w in words]) if words else 0,    # Average word length
            query.count('?'),                     # Question marks
            query.count(','),                     # Commas
            len([w for w in words if len(w) > 6]),  # Long words
            len([w for w in words if w and w[0].isupper()]),  # Capitalized words
            query.count(' and ') + query.count(' or '),  # Conjunctions
        ]
        
        return np.array(features, dtype=np.float32)
    
    def _get_trained_view_predictions(self, query: str) -> Dict[str, float]:
        """Get predictions from trained view models."""
        if not hasattr(self, 'trained_view_models') or not self.trained_view_models:
            return {}
        
        predictions = {}
        features = self._extract_simple_features(query)
        features_tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0)
        
        with torch.no_grad():
            for view_name, model in self.trained_view_models.items():
                try:
                    score = model(features_tensor).item()
                    predictions[view_name] = score
                except Exception as e:
                    logger.warning(f"Failed to get prediction from {view_name} model: {e}")
        
        return predictions
    
    def _get_single_view_prediction(self, query: str, view_name: str) -> Optional[float]:
        """Get prediction from a single trained view model."""
        if not hasattr(self, 'trained_view_models') or view_name not in self.trained_view_models:
            return None
        
        try:
            features = self._extract_simple_features(query)
            features_tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0)
            
            with torch.no_grad():
                model = self.trained_view_models[view_name]
                score = model(features_tensor).item()
                return score
        except Exception as e:
            logger.warning(f"Failed to get prediction from {view_name} model: {e}")
            return None
    
    def _score_to_level(self, score: float) -> ComplexityLevel:
        """Convert numeric score to ComplexityLevel."""
        if score < 0.33:
            return ComplexityLevel.SIMPLE
        elif score < 0.67:
            return ComplexityLevel.MEDIUM
        else:
            return ComplexityLevel.COMPLEX
    
    async def analyze(self, query: str, mode: str = 'hybrid') -> AnalysisResult:
        """
        Analyze query complexity using all 5 ML views.
        
        Args:
            query: Query text to analyze
            mode: Analysis mode ('hybrid', 'ml', 'algorithmic', 'auto')
            
        Returns:
            AnalysisResult with comprehensive complexity analysis
        """
        start_time = time.time()
        analysis_id = f"epic1_ml_{int(time.time() * 1000)}"
        
        try:
            # Track analysis start
            if self.performance_monitor:
                self.performance_monitor.record_operation_start(analysis_id, 'epic1_ml_analysis')
            
            logger.debug(f"Starting Epic1 ML analysis for query: '{query[:50]}...' (mode={mode})")
            
            # Execute all views
            if self.parallel_execution and mode in ['hybrid', 'ml', 'auto']:
                view_results = await self._execute_views_parallel(query, mode)
            else:
                view_results = await self._execute_views_sequential(query, mode)
            
            # Combine view results using meta-classifier
            combined_result = await self._combine_view_results(query, view_results, mode)
            
            # Generate model recommendation
            model_recommendation = self.model_recommender.recommend_model(
                combined_result['complexity_score'],
                combined_result['complexity_level'],
                strategy=self.config.get('routing_strategy', 'balanced')
            )
            
            # Calculate analysis time
            analysis_time_ms = (time.time() - start_time) * 1000
            
            # Create final analysis result
            analysis_result = AnalysisResult(
                query=query,
                view_results=view_results,
                final_score=combined_result['complexity_score'],
                final_complexity=self._string_to_complexity_level(combined_result['complexity_level']),
                confidence=combined_result['confidence'],
                total_latency_ms=analysis_time_ms,
                metadata={
                    'analyzer': 'Epic1MLAnalyzer',
                    'model_recommendation': model_recommendation,
                    'analysis_method': (AnalysisMethod.HYBRID if mode == 'hybrid' else AnalysisMethod.ML).value,
                    'view_count': len(view_results),
                    'successful_views': len([r for r in view_results.values() if r.confidence > 0]),
                    'meta_classification': {
                        'breakdown': combined_result['breakdown'],
                        'reasoning': combined_result['reasoning'],
                        'meta_classifier_used': combined_result.get('meta_classifier_used', False)
                    },
                    'view_weights': self.view_weights,
                    'parallel_execution': self.parallel_execution,
                    'memory_stats': self.memory_monitor.get_current_stats().__dict__ if self.memory_monitor else {}
                }
            )
            
            # Record successful analysis
            self._record_analysis(analysis_time_ms, success=True)
            
            # Track analysis completion
            if self.performance_monitor:
                self.performance_monitor.record_operation_end(
                    analysis_id, 'epic1_ml_analysis', 
                    success=True, metadata={'accuracy_target': '>85%'}
                )
            
            logger.info(f"Epic1 ML analysis completed: score={combined_result['complexity_score']:.3f}, "
                       f"level={combined_result['complexity_level']}, confidence={combined_result['confidence']:.3f}, "
                       f"time={analysis_time_ms:.1f}ms")
            
            return analysis_result
            
        except Exception as e:
            analysis_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Epic1 ML analysis failed: {e}")
            
            # Record failed analysis
            self._record_analysis(analysis_time_ms, success=False)
            
            # Track analysis failure
            if self.performance_monitor:
                self.performance_monitor.record_operation_end(
                    analysis_id, 'epic1_ml_analysis', 
                    success=False, error_message=str(e)
                )
            
            # Return fallback result
            return await self._get_fallback_result(query, e, analysis_time_ms)
    
    async def _execute_views_parallel(self, query: str, mode: str) -> Dict[str, ViewResult]:
        """Execute all views in parallel for optimal performance."""
        try:
            # Create analysis tasks for all views
            tasks = {}
            for view_name, view in self.views.items():
                tasks[view_name] = asyncio.create_task(
                    self._execute_view_safe(view_name, view, query, mode)
                )
            
            # Execute all views concurrently
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            
            # Collect results
            view_results = {}
            for view_name, result in zip(tasks.keys(), results):
                if isinstance(result, Exception):
                    logger.warning(f"View {view_name} failed: {result}")
                    # Create fallback result
                    view_results[view_name] = ViewResult.create_error_result(
                        view_name=view_name,
                        error_message=str(result),
                        latency_ms=0.0
                    )
                else:
                    view_results[view_name] = result
            
            return view_results
            
        except Exception as e:
            logger.error(f"Parallel view execution failed: {e}")
            # Fall back to sequential execution
            return await self._execute_views_sequential(query, mode)
    
    async def _execute_views_sequential(self, query: str, mode: str) -> Dict[str, ViewResult]:
        """Execute all views sequentially as fallback."""
        view_results = {}
        
        for view_name, view in self.views.items():
            try:
                result = await self._execute_view_safe(view_name, view, query, mode)
                view_results[view_name] = result
            except Exception as e:
                logger.warning(f"Sequential view {view_name} failed: {e}")
                view_results[view_name] = ViewResult.create_error_result(
                    view_name=view_name,
                    error_message=str(e),
                    latency_ms=0.0
                )
        
        return view_results
    
    async def _execute_view_safe(self, view_name: str, view: Any, query: str, mode: str) -> ViewResult:
        """Execute a single view with error handling and performance tracking."""
        start_time = time.time()
        
        try:
            # Check if we have a trained model for this view
            if (hasattr(self, 'trained_view_models') and 
                view_name in self.trained_view_models and 
                mode in ['hybrid', 'ml']):
                
                # Get prediction from trained model
                trained_score = self._get_single_view_prediction(query, view_name)
                
                if trained_score is not None:
                    # Create a ViewResult from trained model prediction
                    analysis_time = (time.time() - start_time) * 1000
                    
                    # Still run the view for additional features if in hybrid mode
                    if mode == 'hybrid':
                        original_result = await view.analyze(query, mode='algorithmic')
                        # Combine trained score with original features
                        result = ViewResult(
                            view_name=view_name,
                            score=trained_score,  # Use trained model score
                            confidence=0.85,  # High confidence for trained models
                            method=AnalysisMethod.ML,
                            latency_ms=analysis_time,
                            features=original_result.features if hasattr(original_result, 'features') else {},
                            metadata={
                                'trained_model_used': True,
                                'original_score': original_result.score,
                                'model_type': 'neural_network'
                            }
                        )
                    else:
                        # Pure ML mode - just use trained model
                        result = ViewResult(
                            view_name=view_name,
                            score=trained_score,
                            confidence=0.85,
                            method=AnalysisMethod.ML,
                            latency_ms=analysis_time,
                            features={},
                            metadata={'trained_model_used': True, 'model_type': 'neural_network'}
                        )
                    
                    # Record performance
                    if view_name not in self._view_performance:
                        self._view_performance[view_name] = {'total_time': 0, 'count': 0, 'errors': 0}
                    self._view_performance[view_name]['total_time'] += analysis_time
                    self._view_performance[view_name]['count'] += 1
                    
                    return result
            
            # Fall back to original view analysis
            result = await view.analyze(query, mode)
            
            # Record view performance
            analysis_time = (time.time() - start_time) * 1000
            if view_name not in self._view_performance:
                self._view_performance[view_name] = {'total_time': 0, 'count': 0, 'errors': 0}
            
            self._view_performance[view_name]['total_time'] += analysis_time
            self._view_performance[view_name]['count'] += 1
            
            return result
            
        except Exception as e:
            # Record view error
            analysis_time = (time.time() - start_time) * 1000
            if view_name not in self._view_performance:
                self._view_performance[view_name] = {'total_time': 0, 'count': 0, 'errors': 0}
            
            self._view_performance[view_name]['errors'] += 1
            
            logger.error(f"View {view_name} execution failed: {e}")
            raise
    
    async def _combine_view_results(
        self, query: str, view_results: Dict[str, ViewResult], mode: str
    ) -> ComplexityClassification:
        """Combine view results using meta-classifier."""
        try:
            # Check if we have trained models to use
            if hasattr(self, 'trained_meta_classifier') and self.trained_meta_classifier:
                # Use trained MetaClassifier (Epic 1 ML architecture)
                return self._combine_with_trained_meta_classifier(query, view_results)
            else:
                # Fall back to original ComplexityClassifier
                features = self._extract_meta_features(query, view_results)
                classification = self.complexity_classifier.classify(features)
                enhanced_classification = self._enhance_classification(classification, view_results)
                return enhanced_classification
            
        except Exception as e:
            logger.error(f"View result combination failed: {e}")
            # Return conservative fallback - use dictionary format like ComplexityClassifier
            return {
                'complexity_level': 'medium',
                'complexity_score': 0.5,
                'confidence': 0.5,
                'breakdown': {'fallback': 1.0},
                'reasoning': f"Meta-classification failed: {e}"
            }
    
    def _combine_with_trained_meta_classifier(self, query: str, view_results: Dict[str, ViewResult]) -> Dict[str, Any]:
        """Use trained MetaClassifier to combine view results (Epic 1 ML architecture)."""
        try:
            # Build 15-dimensional meta-feature vector (3 features per view)
            meta_features = self._build_trained_meta_features(view_results)
            
            # Scale features
            meta_features_scaled = self.meta_feature_scaler.transform(meta_features.reshape(1, -1))
            
            # Get predictions from MetaClassifier
            class_probs = self.trained_meta_classifier.predict_proba(meta_features_scaled)[0]
            predicted_class = self.trained_meta_classifier.predict(meta_features_scaled)[0]
            
            # Convert class probabilities to continuous score
            # Classes: 0=simple, 1=medium, 2=complex
            class_centers = np.array([0.2, 0.5, 0.8])
            final_score = np.dot(class_probs, class_centers)
            
            # Get calibrated confidence if available
            raw_confidence = np.max(class_probs)
            if hasattr(self, 'confidence_calibrator') and self.confidence_calibrator:
                calibrated_confidence = self.confidence_calibrator.transform([raw_confidence])[0]
            else:
                calibrated_confidence = raw_confidence
            
            # Determine complexity level
            if final_score < 0.33:
                complexity_level = 'simple'
            elif final_score < 0.67:
                complexity_level = 'medium'
            else:
                complexity_level = 'complex'
            
            # Build breakdown showing view contributions
            breakdown = {}
            for view_name, result in view_results.items():
                if result.confidence > 0:
                    breakdown[f'{view_name}_score'] = result.score
                    breakdown[f'{view_name}_confidence'] = result.confidence
            
            # Generate reasoning
            successful_views = [name for name, result in view_results.items() if result.confidence > 0]
            reasoning = (
                f"Trained MetaClassifier analysis using {len(successful_views)} views. "
                f"Final score: {final_score:.3f} (class probabilities: simple={class_probs[0]:.2f}, "
                f"medium={class_probs[1]:.2f}, complex={class_probs[2]:.2f}). "
                f"Calibrated confidence: {calibrated_confidence:.3f}"
            )
            
            return {
                'complexity_level': complexity_level,
                'complexity_score': final_score,
                'confidence': calibrated_confidence,
                'breakdown': breakdown,
                'reasoning': reasoning,
                'meta_classifier_used': True
            }
            
        except Exception as e:
            logger.error(f"Trained MetaClassifier failed: {e}, falling back to default combination")
            # Fall back to weighted average
            return self._fallback_combination(view_results)
    
    def _build_trained_meta_features(self, view_results: Dict[str, ViewResult]) -> np.ndarray:
        """Build 15-dimensional meta-feature vector for trained MetaClassifier."""
        meta_features = np.zeros(15)
        
        for i, view_name in enumerate(['technical', 'linguistic', 'task', 'semantic', 'computational']):
            base_idx = i * 3
            
            if view_name in view_results:
                result = view_results[view_name]
                # Feature 1: Complexity score
                meta_features[base_idx] = result.score
                # Feature 2: Confidence
                meta_features[base_idx + 1] = result.confidence
                # Feature 3: Analysis method (0=algorithmic, 0.5=hybrid, 1=ml)
                if result.is_ml_based:
                    meta_features[base_idx + 2] = 1.0
                elif hasattr(result, 'method') and result.method == AnalysisMethod.HYBRID:
                    meta_features[base_idx + 2] = 0.5
                else:
                    meta_features[base_idx + 2] = 0.0
            else:
                # Missing view - use defaults
                meta_features[base_idx] = 0.5      # Neutral score
                meta_features[base_idx + 1] = 0.0  # No confidence
                meta_features[base_idx + 2] = 0.0  # Algorithmic
        
        return meta_features
    
    def _fallback_combination(self, view_results: Dict[str, ViewResult]) -> Dict[str, Any]:
        """Fallback to weighted average when MetaClassifier fails."""
        weighted_scores = []
        weighted_confidences = []
        
        for view_name, result in view_results.items():
            if result.confidence > 0:
                weight = self.view_weights.get(view_name, 0.2)
                weighted_scores.append(result.score * weight)
                weighted_confidences.append(result.confidence * weight)
        
        if weighted_scores:
            final_score = sum(weighted_scores)
            final_confidence = min(sum(weighted_confidences), 0.95)
        else:
            final_score = 0.5
            final_confidence = 0.3
        
        # Determine level
        if final_score < 0.33:
            complexity_level = 'simple'
        elif final_score < 0.67:
            complexity_level = 'medium'
        else:
            complexity_level = 'complex'
        
        return {
            'complexity_level': complexity_level,
            'complexity_score': final_score,
            'confidence': final_confidence,
            'breakdown': {v: r.score for v, r in view_results.items() if r.confidence > 0},
            'reasoning': 'Fallback weighted average combination'
        }
    
    def _extract_meta_features(self, query: str, view_results: Dict[str, ViewResult]) -> Dict[str, Any]:
        """Extract features for meta-classifier from view results."""
        features = {
            'length': {
                'word_count': len(query.split()),
                'char_count': len(query),
                'sentence_count': query.count('.') + query.count('!') + query.count('?') + 1
            },
            'syntactic': {},
            'vocabulary': {},
            'question': {},
            'ambiguity': {}
        }
        
        # Extract view-specific features
        for view_name, result in view_results.items():
            if result.confidence > 0:  # Only use successful results
                # Add view score with weight
                view_weight = self.view_weights.get(view_name, 0.0)
                features[f'{view_name}_score'] = result.score * view_weight
                features[f'{view_name}_confidence'] = result.confidence
                
                # Extract specific features from view metadata
                if hasattr(result, 'features') and result.features:
                    self._merge_view_features(features, view_name, result.features)
        
        # Add aggregated features
        successful_views = [r for r in view_results.values() if r.confidence > 0]
        if successful_views:
            features['meta'] = {
                'avg_score': sum(r.score for r in successful_views) / len(successful_views),
                'avg_confidence': sum(r.confidence for r in successful_views) / len(successful_views),
                'score_std': np.std([r.score for r in successful_views]),
                'successful_view_count': len(successful_views),
                'ml_view_count': len([r for r in successful_views if r.is_ml_based])
            }
        
        return features
    
    def _merge_view_features(self, features: Dict[str, Any], view_name: str, view_features: Dict[str, Any]) -> None:
        """Merge view-specific features into meta-features."""
        try:
            # Map view features to meta-classifier categories
            if view_name == 'linguistic' and 'syntactic_analysis' in view_features:
                syntactic = view_features['syntactic_analysis']
                features['syntactic'].update({
                    'clause_complexity': syntactic.get('clause_count', 0) / 10.0,  # Normalize
                    'nesting_depth': syntactic.get('nesting_depth', 0) / 5.0,
                    'conjunction_complexity': len(syntactic.get('conjunctions', [])) / 5.0
                })
            
            if view_name == 'technical' and 'technical_terms_found' in view_features:
                tech_terms = view_features['technical_terms_found']
                features['vocabulary'].update({
                    'technical_density': len(tech_terms) / max(len(features['length']['word_count']), 1),
                    'technical_count': len(tech_terms),
                    'vocabulary_richness': view_features.get('term_density', 0.0)
                })
            
            if view_name == 'task' and 'question_analysis' in view_features:
                question = view_features['question_analysis']
                features['question'].update({
                    'question_type': 0.8 if question.get('question_type') == 'analytical' else 0.3,
                    'comparative_complexity': 0.7 if 'compare' in question.get('question_type', '') else 0.0
                })
                
        except Exception as e:
            logger.debug(f"Failed to merge features from {view_name}: {e}")
    
    def _enhance_classification(
        self, classification: Dict[str, Any], view_results: Dict[str, ViewResult]
    ) -> Dict[str, Any]:
        """Enhance classification with view-specific insights."""
        try:
            # Calculate view-weighted score
            weighted_scores = []
            weighted_confidences = []
            
            for view_name, result in view_results.items():
                if result.confidence > 0:
                    weight = self.view_weights.get(view_name, 0.0)
                    weighted_scores.append(result.score * weight)
                    weighted_confidences.append(result.confidence * weight)
            
            if weighted_scores:
                view_weighted_score = sum(weighted_scores)
                view_weighted_confidence = sum(weighted_confidences)
                
                # Combine with meta-classifier score (70% views, 30% meta-classifier)
                final_score = view_weighted_score * 0.7 + classification['complexity_score'] * 0.3
                final_confidence = min(view_weighted_confidence * 0.7 + classification['confidence'] * 0.3, 0.95)
                
                # Determine final level based on combined score
                if final_score < 0.30:
                    final_level = 'simple'
                elif final_score < 0.70:
                    final_level = 'medium'
                else:
                    final_level = 'complex'
                
                # Enhanced breakdown
                enhanced_breakdown = dict(classification['breakdown'])
                for view_name, result in view_results.items():
                    if result.confidence > 0:
                        enhanced_breakdown[f'{view_name}_contribution'] = result.score * self.view_weights.get(view_name, 0.0)
                
                # Enhanced reasoning
                successful_views = [name for name, result in view_results.items() if result.confidence > 0]
                enhanced_reasoning = (
                    f"ML analysis using {len(successful_views)} views: {', '.join(successful_views)}. "
                    f"Weighted score: {final_score:.3f}. {classification['reasoning']}"
                )
                
                return {
                    'complexity_level': final_level,
                    'complexity_score': final_score,
                    'confidence': final_confidence,
                    'breakdown': enhanced_breakdown,
                    'reasoning': enhanced_reasoning
                }
            else:
                # No successful views - return meta-classifier result
                return classification
                
        except Exception as e:
            logger.warning(f"Classification enhancement failed: {e}")
            return classification
    
    async def _get_fallback_result(self, query: str, error: Exception, analysis_time_ms: float) -> AnalysisResult:
        """Get fallback result when ML analysis fails."""
        if self.fallback_strategy == 'algorithmic':
            # Try pure algorithmic analysis
            try:
                algorithmic_results = {}
                for view_name, view in self.views.items():
                    try:
                        result = await view.analyze(query, mode='algorithmic')
                        algorithmic_results[view_name] = result
                    except Exception as view_error:
                        logger.debug(f"Algorithmic fallback failed for {view_name}: {view_error}")
                
                if algorithmic_results:
                    # Use algorithmic results
                    combined_result = await self._combine_view_results(query, algorithmic_results, 'algorithmic')
                    
                    return AnalysisResult(
                        query=query,
                        view_results=algorithmic_results,
                        final_score=combined_result['complexity_score'],
                        final_complexity=self._string_to_complexity_level(combined_result['complexity_level']),
                        confidence=combined_result['confidence'] * 0.8,  # Reduce confidence for fallback
                        total_latency_ms=analysis_time_ms,
                        metadata={
                            'analyzer': 'Epic1MLAnalyzer',
                            'model_recommendation': self.model_recommender.recommend_model(
                                combined_result['complexity_score'], combined_result['complexity_level'], strategy='conservative'
                            ),
                            'analysis_method': AnalysisMethod.FALLBACK.value,
                            'fallback_reason': str(error),
                            'fallback_strategy': 'algorithmic'
                        }
                    )
            except Exception as fallback_error:
                logger.error(f"Algorithmic fallback also failed: {fallback_error}")
        
        # Conservative fallback
        return AnalysisResult(
            query=query,
            view_results={},
            final_score=0.5,  # Medium complexity assumption
            final_complexity=ComplexityLevel.MEDIUM,
            confidence=0.3,  # Low confidence
            total_latency_ms=analysis_time_ms,
            metadata={
                'analyzer': 'Epic1MLAnalyzer',
                'model_recommendation': self.model_recommender.recommend_model(
                    0.5, 'medium', strategy='conservative'
                ),
                'analysis_method': AnalysisMethod.FALLBACK.value,
                'fallback_reason': str(error),
                'fallback_strategy': 'conservative'
            }
        )
    
    def _string_to_complexity_level(self, level_str: str) -> ComplexityLevel:
        """Convert complexity level string to enum."""
        try:
            return ComplexityLevel(level_str)
        except ValueError:
            logger.warning(f"Invalid complexity level: {level_str}, using MEDIUM")
            return ComplexityLevel.MEDIUM  # Safe default
    
    def _record_analysis(self, analysis_time_ms: float, success: bool = True) -> None:
        """Record analysis performance metrics."""
        self._analysis_count += 1
        self._total_analysis_time += analysis_time_ms
        
        if not success:
            self._error_count += 1
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        avg_time = self._total_analysis_time / self._analysis_count if self._analysis_count > 0 else 0.0
        error_rate = self._error_count / self._analysis_count if self._analysis_count > 0 else 0.0
        
        # View performance stats
        view_stats = {}
        for view_name, perf_data in self._view_performance.items():
            if perf_data['count'] > 0:
                view_stats[view_name] = {
                    'avg_time_ms': perf_data['total_time'] / perf_data['count'],
                    'analysis_count': perf_data['count'],
                    'error_count': perf_data['errors'],
                    'error_rate': perf_data['errors'] / perf_data['count']
                }
        
        return {
            'analyzer': 'Epic1MLAnalyzer',
            'analysis_count': self._analysis_count,
            'total_analysis_time_ms': self._total_analysis_time,
            'average_analysis_time_ms': avg_time,
            'error_count': self._error_count,
            'error_rate': error_rate,
            'accuracy_target': '>85%',
            'latency_target': '<50ms',
            'view_performance': view_stats,
            'view_weights': self.view_weights,
            'memory_budget_gb': self.memory_budget_gb,
            'parallel_execution': self.parallel_execution
        }
    
    def shutdown(self) -> None:
        """Shutdown ML analyzer and clean up resources."""
        try:
            logger.info("Shutting down Epic1MLAnalyzer...")
            
            # Shutdown model manager (which handles its own monitors)
            if hasattr(self, 'model_manager') and hasattr(self.model_manager, 'shutdown'):
                self.model_manager.shutdown()
            
            logger.info("Epic1MLAnalyzer shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during Epic1MLAnalyzer shutdown: {e}")
    
    def __del__(self):
        """Cleanup on destruction."""
        try:
            self.shutdown()
        except Exception:
            pass  # Ignore errors during cleanup