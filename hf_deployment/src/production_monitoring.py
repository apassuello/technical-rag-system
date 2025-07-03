#!/usr/bin/env python3
"""
Production Monitoring for Confidence Calibration Drift

This module provides real-time monitoring of confidence calibration quality
in production, detecting drift and triggering recalibration alerts when needed.
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from collections import deque
import statistics

# Import calibration framework
from confidence_calibration import CalibrationEvaluator, CalibrationDataPoint

logger = logging.getLogger(__name__)


@dataclass
class MonitoringMetrics:
    """Metrics for confidence calibration monitoring."""
    timestamp: datetime
    ece_score: float
    ace_score: float
    mce_score: float
    brier_score: float
    sample_count: int
    avg_confidence: float
    high_confidence_rate: float  # Rate of >70% confidence predictions
    low_confidence_rate: float   # Rate of <30% confidence predictions
    accuracy: float              # Overall accuracy when available


@dataclass
class DriftAlert:
    """Alert for calibration drift detection."""
    timestamp: datetime
    alert_type: str  # 'ECE_DRIFT', 'ACCURACY_DROP', 'CALIBRATION_DEGRADATION'
    severity: str    # 'WARNING', 'CRITICAL'
    current_value: float
    baseline_value: float
    threshold: float
    sample_count: int
    recommendation: str


class CalibrationMonitor:
    """
    Production monitoring system for confidence calibration drift detection.
    
    Monitors confidence calibration quality in real-time and alerts when
    recalibration is needed.
    """
    
    def __init__(
        self,
        ece_threshold: float = 0.1,
        accuracy_threshold: float = 0.05,
        min_samples: int = 100,
        monitoring_window: int = 1000,
        baseline_metrics: Optional[MonitoringMetrics] = None
    ):
        """
        Initialize the calibration monitor.
        
        Args:
            ece_threshold: Maximum acceptable ECE score
            accuracy_threshold: Minimum accuracy drop to trigger alert
            min_samples: Minimum samples before drift detection
            monitoring_window: Size of rolling window for monitoring
            baseline_metrics: Baseline metrics from validation
        """
        self.ece_threshold = ece_threshold
        self.accuracy_threshold = accuracy_threshold
        self.min_samples = min_samples
        self.monitoring_window = monitoring_window
        self.baseline_metrics = baseline_metrics
        
        # Rolling windows for monitoring
        self.confidence_history = deque(maxlen=monitoring_window)
        self.correctness_history = deque(maxlen=monitoring_window)
        self.query_history = deque(maxlen=monitoring_window)
        
        # Metrics tracking
        self.metrics_history: List[MonitoringMetrics] = []
        self.alerts_history: List[DriftAlert] = []
        
        # Calibration evaluator for metrics calculation
        self.evaluator = CalibrationEvaluator()
        
        logger.info(f"CalibrationMonitor initialized with ECE threshold: {ece_threshold}")
    
    def add_query_result(
        self, 
        confidence: float, 
        correctness: Optional[float] = None,
        query_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[DriftAlert]:
        """
        Add a query result to the monitoring system.
        
        Args:
            confidence: Predicted confidence (0.0-1.0)
            correctness: Actual correctness (0.0-1.0) if available
            query_metadata: Additional query metadata
            
        Returns:
            DriftAlert if drift detected, None otherwise
        """
        # Add to rolling windows
        self.confidence_history.append(confidence)
        if correctness is not None:
            self.correctness_history.append(correctness)
        
        query_data = {
            'timestamp': datetime.now(),
            'confidence': confidence,
            'correctness': correctness,
            'metadata': query_metadata
        }
        self.query_history.append(query_data)
        
        # Check for drift if we have enough samples
        if len(self.confidence_history) >= self.min_samples:
            return self._check_drift()
        
        return None
    
    def _check_drift(self) -> Optional[DriftAlert]:
        """
        Check for calibration drift in recent samples.
        
        Returns:
            DriftAlert if drift detected, None otherwise
        """
        # Calculate current metrics
        current_metrics = self._calculate_current_metrics()
        
        if current_metrics is None:
            return None
        
        # Store metrics
        self.metrics_history.append(current_metrics)
        
        # Check for drift against thresholds
        drift_alert = None
        
        # ECE drift check
        if current_metrics.ece_score > self.ece_threshold:
            drift_alert = DriftAlert(
                timestamp=datetime.now(),
                alert_type='ECE_DRIFT',
                severity='WARNING' if current_metrics.ece_score < self.ece_threshold * 1.5 else 'CRITICAL',
                current_value=current_metrics.ece_score,
                baseline_value=self.baseline_metrics.ece_score if self.baseline_metrics else 0.0,
                threshold=self.ece_threshold,
                sample_count=current_metrics.sample_count,
                recommendation=self._get_drift_recommendation('ECE_DRIFT', current_metrics.ece_score)
            )
        
        # Accuracy drop check (if we have baseline)
        elif (self.baseline_metrics and 
              current_metrics.accuracy < self.baseline_metrics.accuracy - self.accuracy_threshold):
            drift_alert = DriftAlert(
                timestamp=datetime.now(),
                alert_type='ACCURACY_DROP',
                severity='WARNING',
                current_value=current_metrics.accuracy,
                baseline_value=self.baseline_metrics.accuracy,
                threshold=self.accuracy_threshold,
                sample_count=current_metrics.sample_count,
                recommendation=self._get_drift_recommendation('ACCURACY_DROP', current_metrics.accuracy)
            )
        
        # Log and store alert if detected
        if drift_alert:
            self.alerts_history.append(drift_alert)
            logger.warning(f"Calibration drift detected: {drift_alert.alert_type} "
                         f"({drift_alert.current_value:.3f} vs threshold {drift_alert.threshold:.3f})")
        
        return drift_alert
    
    def _calculate_current_metrics(self) -> Optional[MonitoringMetrics]:
        """
        Calculate current monitoring metrics from recent samples.
        
        Returns:
            MonitoringMetrics if sufficient data, None otherwise
        """
        if len(self.confidence_history) < self.min_samples:
            return None
        
        confidences = list(self.confidence_history)
        
        # If we have correctness data, calculate full metrics
        if len(self.correctness_history) >= self.min_samples:
            correctness = list(self.correctness_history)
            
            # Calculate calibration metrics using simple data structure
            data_points = [
                CalibrationDataPoint(
                    predicted_confidence=conf,
                    actual_correctness=corr,
                    query="monitoring_query",  # Placeholder for monitoring
                    answer="monitoring_answer",  # Placeholder for monitoring
                    context_relevance=0.8,  # Default relevance
                    metadata={"source": "production_monitoring"}
                ) 
                for conf, corr in zip(confidences[-len(correctness):], correctness)
            ]
            
            # Calculate calibration metrics using evaluator
            calibration_metrics = self.evaluator.evaluate_calibration(data_points)
            ece = calibration_metrics.ece
            ace = calibration_metrics.ace
            mce = calibration_metrics.mce
            brier = calibration_metrics.brier_score
            accuracy = np.mean(correctness)
        else:
            # Limited metrics without correctness data
            ece = ace = mce = brier = accuracy = 0.0
        
        # Calculate distribution metrics
        avg_confidence = np.mean(confidences)
        high_confidence_rate = np.mean([c >= 0.7 for c in confidences])
        low_confidence_rate = np.mean([c <= 0.3 for c in confidences])
        
        return MonitoringMetrics(
            timestamp=datetime.now(),
            ece_score=ece,
            ace_score=ace,
            mce_score=mce,
            brier_score=brier,
            sample_count=len(confidences),
            avg_confidence=avg_confidence,
            high_confidence_rate=high_confidence_rate,
            low_confidence_rate=low_confidence_rate,
            accuracy=accuracy
        )
    
    def _get_drift_recommendation(self, alert_type: str, current_value: float) -> str:
        """
        Get recommendation for handling detected drift.
        
        Args:
            alert_type: Type of drift detected
            current_value: Current metric value
            
        Returns:
            Recommendation string
        """
        recommendations = {
            'ECE_DRIFT': f"""
                Current ECE ({current_value:.3f}) exceeds threshold ({self.ece_threshold:.3f}).
                Recommendations:
                1. Collect new validation dataset (500+ samples)
                2. Refit temperature scaling calibration
                3. Update production calibration parameters
                4. Monitor for improvement over next 100 queries
            """,
            'ACCURACY_DROP': f"""
                Accuracy dropped to {current_value:.3f} (threshold: {self.accuracy_threshold:.3f}).
                Recommendations:
                1. Review recent query patterns for distribution shift
                2. Check document quality and relevance
                3. Consider expanding knowledge base
                4. Retrain retrieval components if needed
            """,
            'CALIBRATION_DEGRADATION': f"""
                Overall calibration quality degraded.
                Recommendations:
                1. Full system calibration review
                2. Retrain confidence prediction components
                3. Update system prompts and parameters
                4. Implement A/B testing for improvements
            """
        }
        
        return recommendations.get(alert_type, "Contact ML engineering team for investigation.")
    
    def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """
        Get data for monitoring dashboard display.
        
        Returns:
            Dictionary with dashboard metrics and visualizations
        """
        current_metrics = self._calculate_current_metrics()
        
        # Recent alerts (last 24 hours)
        recent_alerts = [
            alert for alert in self.alerts_history
            if alert.timestamp > datetime.now() - timedelta(hours=24)
        ]
        
        # Metrics trends (last 10 measurements)
        recent_metrics = self.metrics_history[-10:] if self.metrics_history else []
        
        dashboard_data = {
            'current_status': {
                'ece_score': current_metrics.ece_score if current_metrics else 0.0,
                'ece_threshold': self.ece_threshold,
                'sample_count': len(self.confidence_history),
                'alerts_24h': len(recent_alerts),
                'status': 'HEALTHY' if not recent_alerts else 'NEEDS_ATTENTION'
            },
            'metrics': {
                'avg_confidence': current_metrics.avg_confidence if current_metrics else 0.0,
                'high_confidence_rate': current_metrics.high_confidence_rate if current_metrics else 0.0,
                'low_confidence_rate': current_metrics.low_confidence_rate if current_metrics else 0.0,
                'accuracy': current_metrics.accuracy if current_metrics else 0.0
            },
            'trends': {
                'timestamps': [m.timestamp.isoformat() for m in recent_metrics],
                'ece_scores': [m.ece_score for m in recent_metrics],
                'avg_confidences': [m.avg_confidence for m in recent_metrics],
                'accuracies': [m.accuracy for m in recent_metrics]
            },
            'recent_alerts': [
                {
                    'timestamp': alert.timestamp.isoformat(),
                    'type': alert.alert_type,
                    'severity': alert.severity,
                    'current_value': alert.current_value,
                    'threshold': alert.threshold
                }
                for alert in recent_alerts
            ]
        }
        
        return dashboard_data
    
    def export_monitoring_report(self, filepath: str) -> bool:
        """
        Export comprehensive monitoring report to file.
        
        Args:
            filepath: Path to save report
            
        Returns:
            True if successful, False otherwise
        """
        try:
            report_data = {
                'report_timestamp': datetime.now().isoformat(),
                'monitoring_config': {
                    'ece_threshold': self.ece_threshold,
                    'accuracy_threshold': self.accuracy_threshold,
                    'min_samples': self.min_samples,
                    'monitoring_window': self.monitoring_window
                },
                'baseline_metrics': asdict(self.baseline_metrics) if self.baseline_metrics else None,
                'current_metrics': asdict(self._calculate_current_metrics()) if self._calculate_current_metrics() else None,
                'metrics_history': [asdict(m) for m in self.metrics_history],
                'alerts_history': [asdict(a) for a in self.alerts_history],
                'dashboard_data': self.get_monitoring_dashboard_data(),
                'recommendations': self._generate_system_recommendations()
            }
            
            with open(filepath, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            logger.info(f"Monitoring report exported to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export monitoring report: {e}")
            return False
    
    def _generate_system_recommendations(self) -> List[str]:
        """
        Generate system-level recommendations based on monitoring data.
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        current_metrics = self._calculate_current_metrics()
        
        if not current_metrics:
            return ["Insufficient data for recommendations. Continue monitoring."]
        
        # ECE recommendations
        if current_metrics.ece_score > self.ece_threshold:
            recommendations.append(f"ECE score ({current_metrics.ece_score:.3f}) exceeds threshold. Recalibration needed.")
        elif current_metrics.ece_score > self.ece_threshold * 0.8:
            recommendations.append("ECE score approaching threshold. Monitor closely.")
        
        # Confidence distribution recommendations
        if current_metrics.high_confidence_rate < 0.3:
            recommendations.append("Low high-confidence rate. Review system prompt and context quality.")
        elif current_metrics.high_confidence_rate > 0.8:
            recommendations.append("Very high confidence rate. Check for overconfidence bias.")
        
        if current_metrics.low_confidence_rate > 0.3:
            recommendations.append("High low-confidence rate. Improve context retrieval or expand knowledge base.")
        
        # Alert-based recommendations
        recent_alerts = [a for a in self.alerts_history if a.timestamp > datetime.now() - timedelta(days=7)]
        if len(recent_alerts) > 3:
            recommendations.append("Multiple alerts in past week. Full system review recommended.")
        
        if not recommendations:
            recommendations.append("System performing within acceptable parameters. Continue monitoring.")
        
        return recommendations


class ProductionIntegration:
    """
    Integration helper for adding monitoring to production RAG system.
    """
    
    @staticmethod
    def create_monitoring_middleware(monitor: CalibrationMonitor):
        """
        Create middleware function for automatic monitoring integration.
        
        Args:
            monitor: CalibrationMonitor instance
            
        Returns:
            Middleware function
        """
        def monitoring_middleware(query_func):
            def wrapped_query(*args, **kwargs):
                # Execute original query
                result = query_func(*args, **kwargs)
                
                # Extract confidence for monitoring
                confidence = result.get('confidence', 0.0)
                
                # Add to monitoring (correctness would need human labeling)
                alert = monitor.add_query_result(confidence)
                
                # Add monitoring metadata to result
                result['monitoring'] = {
                    'alert': asdict(alert) if alert else None,
                    'sample_count': len(monitor.confidence_history),
                    'ece_status': 'OK' if not alert else alert.alert_type
                }
                
                return result
            
            return wrapped_query
        
        return monitoring_middleware
    
    @staticmethod
    def setup_production_monitoring(
        rag_system,
        baseline_metrics_file: Optional[str] = None,
        monitoring_config: Optional[Dict[str, Any]] = None
    ) -> CalibrationMonitor:
        """
        Set up production monitoring for RAG system.
        
        Args:
            rag_system: RAG system instance
            baseline_metrics_file: Path to baseline metrics JSON
            monitoring_config: Configuration overrides
            
        Returns:
            Configured CalibrationMonitor
        """
        # Load baseline metrics if available
        baseline_metrics = None
        if baseline_metrics_file and Path(baseline_metrics_file).exists():
            try:
                with open(baseline_metrics_file, 'r') as f:
                    baseline_data = json.load(f)
                baseline_metrics = MonitoringMetrics(**baseline_data)
                logger.info(f"Loaded baseline metrics from {baseline_metrics_file}")
            except Exception as e:
                logger.warning(f"Failed to load baseline metrics: {e}")
        
        # Apply configuration
        config = monitoring_config or {}
        monitor = CalibrationMonitor(
            ece_threshold=config.get('ece_threshold', 0.1),
            accuracy_threshold=config.get('accuracy_threshold', 0.05),
            min_samples=config.get('min_samples', 100),
            monitoring_window=config.get('monitoring_window', 1000),
            baseline_metrics=baseline_metrics
        )
        
        # Integrate monitoring middleware
        if hasattr(rag_system, 'query_with_answer'):
            middleware = ProductionIntegration.create_monitoring_middleware(monitor)
            rag_system.query_with_answer = middleware(rag_system.query_with_answer)
            logger.info("Monitoring middleware integrated with RAG system")
        
        return monitor


def create_baseline_metrics_from_validation(
    validation_data: List[Dict[str, float]], 
    output_file: str
) -> MonitoringMetrics:
    """
    Create baseline metrics from validation dataset.
    
    Args:
        validation_data: List of dicts with 'confidence' and 'correctness'
        output_file: Path to save baseline metrics
        
    Returns:
        MonitoringMetrics baseline
    """
    evaluator = CalibrationEvaluator()
    
    # Convert to data points
    data_points = [
        CalibrationDataPoint(item['confidence'], item['correctness'])
        for item in validation_data
    ]
    
    # Calculate metrics
    ece = evaluator.expected_calibration_error(data_points)
    ace = evaluator.adaptive_calibration_error(data_points)
    mce = evaluator.maximum_calibration_error(data_points)
    brier = evaluator.brier_score(data_points)
    
    confidences = [item['confidence'] for item in validation_data]
    correctness = [item['correctness'] for item in validation_data]
    
    baseline_metrics = MonitoringMetrics(
        timestamp=datetime.now(),
        ece_score=ece,
        ace_score=ace,
        mce_score=mce,
        brier_score=brier,
        sample_count=len(validation_data),
        avg_confidence=np.mean(confidences),
        high_confidence_rate=np.mean([c >= 0.7 for c in confidences]),
        low_confidence_rate=np.mean([c <= 0.3 for c in confidences]),
        accuracy=np.mean(correctness)
    )
    
    # Save baseline metrics
    with open(output_file, 'w') as f:
        json.dump(asdict(baseline_metrics), f, indent=2, default=str)
    
    logger.info(f"Baseline metrics saved to {output_file}")
    return baseline_metrics


if __name__ == "__main__":
    # Example usage
    print("🔍 Testing Production Monitoring System")
    
    # Create monitor
    monitor = CalibrationMonitor(
        ece_threshold=0.1,
        min_samples=10  # Lower for testing
    )
    
    # Simulate some queries
    import random
    np.random.seed(42)
    
    print("\n📊 Simulating query results...")
    for i in range(50):
        # Simulate realistic confidence and correctness
        confidence = max(0.1, min(0.9, np.random.normal(0.7, 0.2)))
        correctness = 1.0 if confidence > 0.6 else 0.0
        
        alert = monitor.add_query_result(confidence, correctness)
        
        if alert:
            print(f"🚨 Alert detected: {alert.alert_type} (ECE: {alert.current_value:.3f})")
    
    # Get dashboard data
    dashboard = monitor.get_monitoring_dashboard_data()
    print(f"\n📈 Dashboard Status: {dashboard['current_status']['status']}")
    print(f"Current ECE: {dashboard['current_status']['ece_score']:.3f}")
    print(f"Sample Count: {dashboard['current_status']['sample_count']}")
    
    # Export report
    monitor.export_monitoring_report("monitoring_test_report.json")
    print("✅ Production monitoring test completed!")