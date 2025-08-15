"""
Base View Classes for Epic 1 Multi-View Query Complexity Analyzer.

This module provides the abstract base classes and concrete implementations
for different types of view analysis approaches in the hybrid ML system.

Key Classes:
- BaseView: Abstract base for all view implementations
- AlgorithmicView: Fast algorithmic-only analysis
- MLView: ML-primary analysis with algorithmic fallback
- HybridView: Balanced algorithmic + ML combination

Design Principles:
- Consistent interface across all view types
- Graceful fallback strategies for reliability
- Performance tracking and monitoring integration
- Configuration-driven behavior switching
"""

import time
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union, Callable
from pathlib import Path
import sys

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from .view_result import ViewResult, AnalysisMethod
from ..ml_models.model_manager import ModelManager

logger = logging.getLogger(__name__)


class BaseView(ABC):
    """
    Abstract base class for all view implementations.
    
    Defines the common interface that all view types must implement,
    ensuring consistency across the multi-view analysis system.
    """
    
    def __init__(self, view_name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize base view.
        
        Args:
            view_name: Name of this view (e.g., 'technical', 'linguistic')
            config: Configuration dictionary for this view
        """
        self.view_name = view_name
        self.config = config or {}
        self.model_manager: Optional[ModelManager] = None
        
        # Performance tracking
        self._analysis_count = 0
        self._total_analysis_time = 0.0
        self._error_count = 0
        
        logger.debug(f"Initialized {self.__class__.__name__} for view '{view_name}'")
    
    def set_model_manager(self, model_manager: ModelManager) -> None:
        """Set the model manager for ML operations."""
        self.model_manager = model_manager
        logger.debug(f"Model manager set for view '{self.view_name}'")
    
    @abstractmethod
    async def analyze(self, query: str, mode: str = 'auto') -> ViewResult:
        """
        Analyze query complexity from this view's perspective.
        
        Args:
            query: Query text to analyze
            mode: Analysis mode ('algorithmic', 'ml', 'hybrid', 'auto')
            
        Returns:
            ViewResult with complexity analysis
        """
        pass
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for this view."""
        avg_time = self._total_analysis_time / self._analysis_count if self._analysis_count > 0 else 0.0
        
        return {
            'view_name': self.view_name,
            'analysis_count': self._analysis_count,
            'total_analysis_time_ms': self._total_analysis_time,
            'average_analysis_time_ms': avg_time,
            'error_count': self._error_count,
            'error_rate': self._error_count / self._analysis_count if self._analysis_count > 0 else 0.0
        }
    
    def _record_analysis(self, analysis_time_ms: float, success: bool = True) -> None:
        """Record analysis performance metrics."""
        self._analysis_count += 1
        self._total_analysis_time += analysis_time_ms
        
        if not success:
            self._error_count += 1
    
    async def _measure_analysis_time(self, analysis_func: Callable) -> tuple[Any, float]:
        """Measure analysis time and return result with timing."""
        start_time = time.time()
        try:
            result = await analysis_func() if asyncio.iscoroutinefunction(analysis_func) else analysis_func()
            analysis_time_ms = (time.time() - start_time) * 1000
            return result, analysis_time_ms
        except Exception as e:
            analysis_time_ms = (time.time() - start_time) * 1000
            raise e
    
    def get_fallback_result(self, error: Exception, analysis_time_ms: float = 0.0) -> ViewResult:
        """
        Get fallback result when analysis fails.
        
        Args:
            error: The exception that caused the failure
            analysis_time_ms: Time spent before failure
            
        Returns:
            ViewResult with fallback values
        """
        self._record_analysis(analysis_time_ms, success=False)
        
        return ViewResult.create_error_result(
            view_name=self.view_name,
            error_message=str(error),
            latency_ms=analysis_time_ms
        )


class AlgorithmicView(BaseView):
    """
    Base class for fast algorithmic-only analysis views.
    
    Provides infrastructure for views that use only rule-based or
    heuristic approaches without ML models.
    """
    
    def __init__(self, view_name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize algorithmic view."""
        super().__init__(view_name, config)
        self._initialize_algorithmic_components()
    
    def _initialize_algorithmic_components(self) -> None:
        """Initialize algorithmic components specific to this view."""
        # Override in subclasses to initialize specific algorithmic tools
        pass
    
    async def analyze(self, query: str, mode: str = 'auto') -> ViewResult:
        """
        Analyze query using algorithmic approach.
        
        Args:
            query: Query text to analyze
            mode: Analysis mode (ignored for algorithmic views)
            
        Returns:
            ViewResult with algorithmic analysis
        """
        try:
            result, analysis_time_ms = await self._measure_analysis_time(
                lambda: self._analyze_algorithmic(query)
            )
            
            self._record_analysis(analysis_time_ms, success=True)
            
            return ViewResult(
                view_name=self.view_name,
                score=result['score'],
                confidence=result['confidence'],
                method=AnalysisMethod.ALGORITHMIC,
                latency_ms=analysis_time_ms,
                features=result.get('features', {}),
                metadata=result.get('metadata', {})
            )
            
        except Exception as e:
            logger.error(f"Algorithmic analysis failed for view '{self.view_name}': {e}")
            return self.get_fallback_result(e)
    
    @abstractmethod
    def _analyze_algorithmic(self, query: str) -> Dict[str, Any]:
        """
        Perform algorithmic analysis of the query.
        
        Args:
            query: Query text to analyze
            
        Returns:
            Dictionary with 'score', 'confidence', 'features', 'metadata'
        """
        pass


class MLView(BaseView):
    """
    Base class for ML-primary analysis views with algorithmic fallback.
    
    Provides infrastructure for views that primarily use ML models
    but can fall back to algorithmic approaches when needed.
    """
    
    def __init__(
        self, 
        view_name: str, 
        ml_model_name: str,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize ML view.
        
        Args:
            view_name: Name of this view
            ml_model_name: Name of the ML model to use
            config: Configuration dictionary
        """
        super().__init__(view_name, config)
        self.ml_model_name = ml_model_name
        self._ml_model = None
        
        # Initialize both ML and algorithmic components
        self._initialize_ml_components()
        self._initialize_algorithmic_fallback()
    
    def _initialize_ml_components(self) -> None:
        """Initialize ML-specific components."""
        # Override in subclasses to set up ML-specific tools
        pass
    
    def _initialize_algorithmic_fallback(self) -> None:
        """Initialize algorithmic fallback components."""
        # Override in subclasses to set up fallback analysis
        pass
    
    async def analyze(self, query: str, mode: str = 'auto') -> ViewResult:
        """
        Analyze query using ML approach with algorithmic fallback.
        
        Args:
            query: Query text to analyze
            mode: Analysis mode ('ml', 'algorithmic', 'auto')
            
        Returns:
            ViewResult with analysis
        """
        if mode == 'algorithmic':
            return await self._analyze_with_fallback(query)
        
        # Try ML analysis first
        try:
            return await self._analyze_with_ml(query)
        except Exception as e:
            logger.warning(f"ML analysis failed for view '{self.view_name}', using fallback: {e}")
            return await self._analyze_with_fallback(query)
    
    async def _analyze_with_ml(self, query: str) -> ViewResult:
        """Analyze using ML model."""
        # Ensure model is loaded
        if not self._ml_model and self.model_manager:
            self._ml_model = await self.model_manager.load_model(self.ml_model_name)
        
        if not self._ml_model:
            raise ValueError(f"ML model '{self.ml_model_name}' not available")
        
        try:
            result, analysis_time_ms = await self._measure_analysis_time(
                lambda: self._analyze_ml(query)
            )
            
            self._record_analysis(analysis_time_ms, success=True)
            
            return ViewResult(
                view_name=self.view_name,
                score=result['score'],
                confidence=result['confidence'],
                method=AnalysisMethod.ML,
                latency_ms=analysis_time_ms,
                features=result.get('features', {}),
                metadata=result.get('metadata', {})
            )
            
        except Exception as e:
            logger.error(f"ML analysis failed for view '{self.view_name}': {e}")
            raise
    
    async def _analyze_with_fallback(self, query: str) -> ViewResult:
        """Analyze using algorithmic fallback."""
        try:
            result, analysis_time_ms = await self._measure_analysis_time(
                lambda: self._analyze_algorithmic_fallback(query)
            )
            
            self._record_analysis(analysis_time_ms, success=True)
            
            return ViewResult(
                view_name=self.view_name,
                score=result['score'],
                confidence=result['confidence'] * 0.8,  # Reduce confidence for fallback
                method=AnalysisMethod.FALLBACK,
                latency_ms=analysis_time_ms,
                features=result.get('features', {}),
                metadata={**result.get('metadata', {}), 'fallback_reason': 'ml_unavailable'}
            )
            
        except Exception as e:
            logger.error(f"Fallback analysis failed for view '{self.view_name}': {e}")
            return self.get_fallback_result(e)
    
    @abstractmethod
    def _analyze_ml(self, query: str) -> Dict[str, Any]:
        """
        Perform ML analysis of the query.
        
        Args:
            query: Query text to analyze
            
        Returns:
            Dictionary with 'score', 'confidence', 'features', 'metadata'
        """
        pass
    
    @abstractmethod
    def _analyze_algorithmic_fallback(self, query: str) -> Dict[str, Any]:
        """
        Perform algorithmic fallback analysis.
        
        Args:
            query: Query text to analyze
            
        Returns:
            Dictionary with 'score', 'confidence', 'features', 'metadata'
        """
        pass


class HybridView(BaseView):
    """
    Base class for balanced algorithmic + ML combination views.
    
    Provides infrastructure for views that combine both algorithmic
    and ML approaches to achieve optimal accuracy and reliability.
    """
    
    def __init__(
        self,
        view_name: str,
        ml_model_name: str,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize hybrid view.
        
        Args:
            view_name: Name of this view
            ml_model_name: Name of the ML model to use
            config: Configuration dictionary
        """
        super().__init__(view_name, config)
        self.ml_model_name = ml_model_name
        self._ml_model = None
        
        # Weighting configuration
        self.algorithmic_weight = self.config.get('algorithmic_weight', 0.4)
        self.ml_weight = self.config.get('ml_weight', 0.6)
        
        # Normalize weights
        total_weight = self.algorithmic_weight + self.ml_weight
        if total_weight > 0:
            self.algorithmic_weight /= total_weight
            self.ml_weight /= total_weight
        
        # Initialize components
        self._initialize_algorithmic_components()
        self._initialize_ml_components()
    
    def _initialize_algorithmic_components(self) -> None:
        """Initialize algorithmic components."""
        # Override in subclasses
        pass
    
    def _initialize_ml_components(self) -> None:
        """Initialize ML components."""
        # Override in subclasses
        pass
    
    async def analyze(self, query: str, mode: str = 'auto') -> ViewResult:
        """
        Analyze query using hybrid approach.
        
        Args:
            query: Query text to analyze
            mode: Analysis mode ('algorithmic', 'ml', 'hybrid', 'auto')
            
        Returns:
            ViewResult with hybrid analysis
        """
        if mode == 'algorithmic':
            return await self._analyze_algorithmic_only(query)
        elif mode == 'ml':
            return await self._analyze_ml_only(query)
        else:  # hybrid or auto
            return await self._analyze_hybrid(query)
    
    async def _analyze_hybrid(self, query: str) -> ViewResult:
        """Perform hybrid analysis combining both approaches."""
        start_time = time.time()
        
        try:
            # Run both analyses
            algorithmic_task = asyncio.create_task(self._get_algorithmic_result(query))
            ml_task = asyncio.create_task(self._get_ml_result(query))
            
            # Wait for both to complete (or handle partial completion)
            results = await asyncio.gather(algorithmic_task, ml_task, return_exceptions=True)
            
            algorithmic_result = results[0] if not isinstance(results[0], Exception) else None
            ml_result = results[1] if not isinstance(results[1], Exception) else None
            
            # Combine results
            combined_result = self._combine_results(algorithmic_result, ml_result)
            
            analysis_time_ms = (time.time() - start_time) * 1000
            self._record_analysis(analysis_time_ms, success=True)
            
            return ViewResult(
                view_name=self.view_name,
                score=combined_result['score'],
                confidence=combined_result['confidence'],
                method=AnalysisMethod.HYBRID,
                latency_ms=analysis_time_ms,
                features=combined_result.get('features', {}),
                metadata=combined_result.get('metadata', {})
            )
            
        except Exception as e:
            analysis_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Hybrid analysis failed for view '{self.view_name}': {e}")
            return self.get_fallback_result(e, analysis_time_ms)
    
    async def _analyze_algorithmic_only(self, query: str) -> ViewResult:
        """Analyze using only algorithmic approach."""
        try:
            result, analysis_time_ms = await self._measure_analysis_time(
                lambda: self._analyze_algorithmic(query)
            )
            
            self._record_analysis(analysis_time_ms, success=True)
            
            return ViewResult(
                view_name=self.view_name,
                score=result['score'],
                confidence=result['confidence'],
                method=AnalysisMethod.ALGORITHMIC,
                latency_ms=analysis_time_ms,
                features=result.get('features', {}),
                metadata=result.get('metadata', {})
            )
            
        except Exception as e:
            logger.error(f"Algorithmic analysis failed for view '{self.view_name}': {e}")
            return self.get_fallback_result(e)
    
    async def _analyze_ml_only(self, query: str) -> ViewResult:
        """Analyze using only ML approach."""
        # Ensure model is loaded
        if not self._ml_model and self.model_manager:
            self._ml_model = await self.model_manager.load_model(self.ml_model_name)
        
        if not self._ml_model:
            logger.warning(f"ML model '{self.ml_model_name}' not available, falling back to algorithmic")
            return await self._analyze_algorithmic_only(query)
        
        try:
            result, analysis_time_ms = await self._measure_analysis_time(
                lambda: self._analyze_ml(query)
            )
            
            self._record_analysis(analysis_time_ms, success=True)
            
            return ViewResult(
                view_name=self.view_name,
                score=result['score'],
                confidence=result['confidence'],
                method=AnalysisMethod.ML,
                latency_ms=analysis_time_ms,
                features=result.get('features', {}),
                metadata=result.get('metadata', {})
            )
            
        except Exception as e:
            logger.warning(f"ML analysis failed for view '{self.view_name}', using algorithmic fallback: {e}")
            return await self._analyze_algorithmic_only(query)
    
    async def _get_algorithmic_result(self, query: str) -> Optional[Dict[str, Any]]:
        """Get algorithmic analysis result."""
        try:
            return self._analyze_algorithmic(query)
        except Exception as e:
            logger.warning(f"Algorithmic analysis failed for view '{self.view_name}': {e}")
            return None
    
    async def _get_ml_result(self, query: str) -> Optional[Dict[str, Any]]:
        """Get ML analysis result."""
        try:
            if not self._ml_model and self.model_manager:
                self._ml_model = await self.model_manager.load_model(self.ml_model_name)
            
            if self._ml_model:
                return self._analyze_ml(query)
        except Exception as e:
            logger.warning(f"ML analysis failed for view '{self.view_name}': {e}")
        
        return None
    
    def _combine_results(
        self, 
        algorithmic_result: Optional[Dict[str, Any]], 
        ml_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Combine algorithmic and ML results.
        
        Args:
            algorithmic_result: Result from algorithmic analysis
            ml_result: Result from ML analysis
            
        Returns:
            Combined result dictionary
        """
        # Handle cases where one or both analyses failed
        if not algorithmic_result and not ml_result:
            # Both failed - return default
            return {
                'score': 0.5,
                'confidence': 0.0,
                'features': {},
                'metadata': {'combination_error': 'both_analyses_failed'}
            }
        elif not algorithmic_result:
            # Only ML succeeded
            result = ml_result.copy()
            result['confidence'] *= 0.9  # Slight confidence reduction
            result['metadata']['combination_note'] = 'ml_only'
            return result
        elif not ml_result:
            # Only algorithmic succeeded
            result = algorithmic_result.copy()
            result['confidence'] *= 0.8  # Confidence reduction for no ML
            result['metadata']['combination_note'] = 'algorithmic_only'
            return result
        else:
            # Both succeeded - weighted combination
            combined_score = (
                self.algorithmic_weight * algorithmic_result['score'] +
                self.ml_weight * ml_result['score']
            )
            
            # Confidence is based on agreement between methods
            score_difference = abs(algorithmic_result['score'] - ml_result['score'])
            agreement_factor = 1.0 - min(score_difference, 0.5)  # Penalty for disagreement
            
            combined_confidence = (
                self.algorithmic_weight * algorithmic_result['confidence'] +
                self.ml_weight * ml_result['confidence']
            ) * agreement_factor
            
            # Combine features
            combined_features = {}
            combined_features.update(algorithmic_result.get('features', {}))
            combined_features.update(ml_result.get('features', {}))
            
            # Combine metadata
            combined_metadata = {
                'algorithmic_score': algorithmic_result['score'],
                'ml_score': ml_result['score'],
                'score_difference': score_difference,
                'agreement_factor': agreement_factor,
                'weights': {
                    'algorithmic': self.algorithmic_weight,
                    'ml': self.ml_weight
                }
            }
            combined_metadata.update(algorithmic_result.get('metadata', {}))
            combined_metadata.update(ml_result.get('metadata', {}))
            
            return {
                'score': combined_score,
                'confidence': combined_confidence,
                'features': combined_features,
                'metadata': combined_metadata
            }
    
    @abstractmethod
    def _analyze_algorithmic(self, query: str) -> Dict[str, Any]:
        """
        Perform algorithmic analysis.
        
        Args:
            query: Query text to analyze
            
        Returns:
            Dictionary with 'score', 'confidence', 'features', 'metadata'
        """
        pass
    
    @abstractmethod
    def _analyze_ml(self, query: str) -> Dict[str, Any]:
        """
        Perform ML analysis.
        
        Args:
            query: Query text to analyze
            
        Returns:
            Dictionary with 'score', 'confidence', 'features', 'metadata'
        """
        pass