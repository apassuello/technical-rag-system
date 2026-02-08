"""
View Result Data Structures for Epic 1 ML Views.

This module defines standardized result formats for all view implementations,
ensuring consistent data flow and enabling effective aggregation across
the multi-view analysis system.

Key Features:
- Standardized ViewResult format for individual views
- AnalysisResult format for complete multi-view analysis
- Rich metadata support for explainability
- Performance tracking integration
- JSON serialization support
"""

import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np


class AnalysisMethod(Enum):
    """Analysis method used by a view."""
    ALGORITHMIC = "algorithmic"
    ML = "ml"
    HYBRID = "hybrid"
    FALLBACK = "fallback"


class ComplexityLevel(Enum):
    """Complexity level classification."""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


@dataclass
class ViewResult:
    """
    Standardized result from any view analysis.
    
    This class provides a consistent interface for all view results,
    enabling effective aggregation and meta-analysis.
    """
    
    view_name: str                              # Name of the view (e.g., 'technical', 'linguistic')
    score: float                               # Complexity score [0, 1]
    confidence: float                          # Analysis confidence [0, 1]
    method: AnalysisMethod                     # Method used for analysis
    latency_ms: float                         # Analysis time in milliseconds
    features: Dict[str, Any] = field(default_factory=dict)  # Extracted features
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata
    
    def __post_init__(self):
        """Validate and normalize result values."""
        # Ensure score is in valid range
        self.score = max(0.0, min(1.0, float(self.score)))
        
        # Ensure confidence is in valid range
        self.confidence = max(0.0, min(1.0, float(self.confidence)))
        
        # Ensure latency is positive
        self.latency_ms = max(0.0, float(self.latency_ms))
        
        # Convert method to enum if string
        if isinstance(self.method, str):
            self.method = AnalysisMethod(self.method)
        
        # Add creation timestamp to metadata
        if 'timestamp' not in self.metadata:
            self.metadata['timestamp'] = time.time()
    
    @property
    def complexity_level(self) -> ComplexityLevel:
        """Get complexity level based on score."""
        if self.score < 0.35:
            return ComplexityLevel.SIMPLE
        elif self.score < 0.70:
            return ComplexityLevel.MEDIUM
        else:
            return ComplexityLevel.COMPLEX
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if result has high confidence (>0.8)."""
        return self.confidence > 0.8
    
    @property
    def is_ml_based(self) -> bool:
        """Check if result used ML analysis."""
        return self.method in [AnalysisMethod.ML, AnalysisMethod.HYBRID]
    
    def with_fallback_flag(self) -> 'ViewResult':
        """Return a copy with fallback method indicated."""
        result = ViewResult(
            view_name=self.view_name,
            score=self.score,
            confidence=self.confidence * 0.8,  # Reduce confidence for fallback
            method=AnalysisMethod.FALLBACK,
            latency_ms=self.latency_ms,
            features=self.features.copy(),
            metadata=self.metadata.copy()
        )
        result.metadata['fallback_from'] = self.method.value
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['method'] = self.method.value
        result['complexity_level'] = self.complexity_level.value
        return result
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ViewResult':
        """Create ViewResult from dictionary."""
        # Handle method conversion
        if 'method' in data and isinstance(data['method'], str):
            data['method'] = AnalysisMethod(data['method'])
        
        # Remove computed properties if present
        data.pop('complexity_level', None)
        
        return cls(**data)
    
    @classmethod
    def create_error_result(cls, view_name: str, error_message: str, latency_ms: float = 0.0) -> 'ViewResult':
        """Create a result indicating analysis error."""
        return cls(
            view_name=view_name,
            score=0.5,  # Default to medium complexity
            confidence=0.0,  # Zero confidence for error
            method=AnalysisMethod.FALLBACK,
            latency_ms=latency_ms,
            features={},
            metadata={'error': error_message, 'is_error': True}
        )


@dataclass
class AnalysisResult:
    """
    Complete analysis result from all views in the multi-view system.
    
    Aggregates results from individual views and provides meta-analysis
    with final complexity determination and comprehensive metadata.
    """
    
    query: str                                                     # Original query
    view_results: Dict[str, ViewResult]                           # view_name -> ViewResult
    meta_features: Optional[np.ndarray] = None                    # 15-dimension feature vector
    final_score: Optional[float] = None                           # Meta-classifier output
    final_complexity: Optional[ComplexityLevel] = None            # Final complexity level
    total_latency_ms: float = 0.0                                # Total analysis time
    confidence: float = 0.0                                      # Overall confidence
    method_breakdown: Dict[str, int] = field(default_factory=dict)  # Count of methods used
    metadata: Dict[str, Any] = field(default_factory=dict)       # Additional metadata
    
    def __post_init__(self):
        """Compute derived fields and validate data."""
        self._compute_derived_fields()
        self._validate_data()
    
    def _compute_derived_fields(self) -> None:
        """Compute fields derived from view results."""
        if not self.view_results:
            return
        
        # Compute total latency
        self.total_latency_ms = sum(result.latency_ms for result in self.view_results.values())
        
        # Compute method breakdown
        self.method_breakdown = {}
        for result in self.view_results.values():
            method = result.method.value
            self.method_breakdown[method] = self.method_breakdown.get(method, 0) + 1
        
        # Compute overall confidence (weighted by individual confidences)
        if self.view_results:
            total_confidence = sum(result.confidence for result in self.view_results.values())
            self.confidence = total_confidence / len(self.view_results)
        
        # Compute final score if not provided (simple average for fallback)
        if self.final_score is None and self.view_results:
            scores = [result.score for result in self.view_results.values()]
            self.final_score = sum(scores) / len(scores)
        
        # Compute final complexity level
        if self.final_complexity is None and self.final_score is not None:
            if self.final_score < 0.35:
                self.final_complexity = ComplexityLevel.SIMPLE
            elif self.final_score < 0.70:
                self.final_complexity = ComplexityLevel.MEDIUM
            else:
                self.final_complexity = ComplexityLevel.COMPLEX
        
        # Add timestamp to metadata
        if 'timestamp' not in self.metadata:
            self.metadata['timestamp'] = time.time()
    
    def _validate_data(self) -> None:
        """Validate analysis result data."""
        # Ensure final score is in valid range
        if self.final_score is not None:
            self.final_score = max(0.0, min(1.0, float(self.final_score)))
        
        # Ensure confidence is in valid range
        self.confidence = max(0.0, min(1.0, float(self.confidence)))
        
        # Ensure latency is positive
        self.total_latency_ms = max(0.0, float(self.total_latency_ms))
    
    @property
    def num_views(self) -> int:
        """Get number of views analyzed."""
        return len(self.view_results)
    
    @property
    def successful_views(self) -> List[str]:
        """Get list of views that completed successfully."""
        return [
            name for name, result in self.view_results.items()
            if not result.metadata.get('is_error', False)
        ]
    
    @property
    def failed_views(self) -> List[str]:
        """Get list of views that failed."""
        return [
            name for name, result in self.view_results.items()
            if result.metadata.get('is_error', False)
        ]
    
    @property
    def ml_view_count(self) -> int:
        """Get count of views that used ML analysis."""
        return sum(1 for result in self.view_results.values() if result.is_ml_based)
    
    @property
    def algorithmic_view_count(self) -> int:
        """Get count of views that used only algorithmic analysis."""
        return sum(1 for result in self.view_results.values() if result.method == AnalysisMethod.ALGORITHMIC)
    
    @property
    def average_view_confidence(self) -> float:
        """Get average confidence across all views."""
        if not self.view_results:
            return 0.0
        return sum(result.confidence for result in self.view_results.values()) / len(self.view_results)
    
    @property
    def performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        return {
            'total_latency_ms': self.total_latency_ms,
            'average_latency_ms': self.total_latency_ms / len(self.view_results) if self.view_results else 0,
            'fastest_view': min(self.view_results.items(), key=lambda x: x[1].latency_ms)[0] if self.view_results else None,
            'slowest_view': max(self.view_results.items(), key=lambda x: x[1].latency_ms)[0] if self.view_results else None,
            'method_breakdown': self.method_breakdown
        }
    
    def get_view_result(self, view_name: str) -> Optional[ViewResult]:
        """Get result for a specific view."""
        return self.view_results.get(view_name)
    
    def get_feature_contributions(self) -> Dict[str, float]:
        """Get feature contributions from meta-features if available."""
        if self.meta_features is None:
            # Fallback to simple view score contributions
            total_score = sum(result.score for result in self.view_results.values())
            if total_score == 0:
                return {}
            
            return {
                view_name: result.score / total_score
                for view_name, result in self.view_results.items()
            }
        
        # Extract contributions from meta-features (first 5 dimensions are view scores)
        view_names = list(self.view_results.keys())
        contributions = {}
        
        if len(self.meta_features) >= len(view_names):
            total_contribution = sum(self.meta_features[:len(view_names)])
            if total_contribution > 0:
                for i, view_name in enumerate(view_names):
                    contributions[view_name] = self.meta_features[i] / total_contribution
        
        return contributions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            'query': self.query,
            'view_results': {name: result.to_dict() for name, result in self.view_results.items()},
            'final_score': self.final_score,
            'final_complexity': self.final_complexity.value if self.final_complexity else None,
            'total_latency_ms': self.total_latency_ms,
            'confidence': self.confidence,
            'method_breakdown': self.method_breakdown,
            'metadata': self.metadata,
            'performance_summary': self.performance_summary
        }
        
        # Include meta_features if available
        if self.meta_features is not None:
            result['meta_features'] = self.meta_features.tolist()
        
        return result
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str, indent=2)
    
    @classmethod
    def create_error_result(cls, query: str, error_message: str) -> 'AnalysisResult':
        """Create an analysis result indicating complete failure."""
        return cls(
            query=query,
            view_results={},
            final_score=0.5,  # Default to medium complexity
            final_complexity=ComplexityLevel.MEDIUM,
            confidence=0.0,
            metadata={'error': error_message, 'is_error': True}
        )
    
    def is_successful(self) -> bool:
        """Check if analysis completed successfully."""
        return (
            len(self.successful_views) > 0 and
            not self.metadata.get('is_error', False)
        )
    
    def get_explanation(self) -> Dict[str, Any]:
        """Get human-readable explanation of the analysis."""
        explanation = {
            'query': self.query,
            'final_complexity': self.final_complexity.value if self.final_complexity else 'unknown',
            'final_score': round(self.final_score, 3) if self.final_score else None,
            'confidence': round(self.confidence, 3),
            'analysis_summary': {
                'total_views_analyzed': self.num_views,
                'successful_views': len(self.successful_views),
                'ml_based_views': self.ml_view_count,
                'algorithmic_views': self.algorithmic_view_count,
                'total_time_ms': round(self.total_latency_ms, 1)
            },
            'view_breakdown': {},
            'feature_contributions': self.get_feature_contributions()
        }
        
        # Add individual view explanations
        for view_name, result in self.view_results.items():
            explanation['view_breakdown'][view_name] = {
                'score': round(result.score, 3),
                'confidence': round(result.confidence, 3),
                'method': result.method.value,
                'latency_ms': round(result.latency_ms, 1),
                'complexity_level': result.complexity_level.value,
                'key_features': {k: v for k, v in result.features.items() if isinstance(v, (int, float, str))}
            }
        
        return explanation