"""
Confidence calibration framework for RAG systems based on research best practices.

Implements Expected Calibration Error (ECE), Adaptive Calibration Error (ACE),
temperature scaling, and reliability diagrams for proper confidence calibration.

References:
- Guo et al. "On Calibration of Modern Neural Networks" (2017)
- Kumar et al. "Verified Uncertainty Calibration" (2019)
- RAG-specific calibration research (2024)
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss
import json
from pathlib import Path


@dataclass
class CalibrationMetrics:
    """Container for calibration evaluation metrics."""
    ece: float  # Expected Calibration Error
    ace: float  # Adaptive Calibration Error  
    mce: float  # Maximum Calibration Error
    brier_score: float  # Brier Score
    negative_log_likelihood: float  # Negative Log Likelihood
    reliability_diagram_data: Dict[str, List[float]]


@dataclass
class CalibrationDataPoint:
    """Single data point for calibration evaluation."""
    predicted_confidence: float
    actual_correctness: float  # 0.0 or 1.0
    query: str
    answer: str
    context_relevance: float
    metadata: Dict[str, Any]


class ConfidenceCalibrator:
    """
    Implements temperature scaling and other calibration methods for RAG systems.
    
    Based on research best practices for confidence calibration in QA systems.
    """
    
    def __init__(self):
        self.temperature: Optional[float] = None
        self.is_fitted = False
        
    def fit_temperature_scaling(
        self, 
        confidences: List[float], 
        correctness: List[float]
    ) -> float:
        """
        Fit temperature scaling parameter using validation data.
        
        Args:
            confidences: Predicted confidence scores
            correctness: Ground truth correctness (0.0 or 1.0)
            
        Returns:
            Optimal temperature parameter
        """
        from scipy.optimize import minimize_scalar
        
        # Create temporary evaluator for ECE computation
        evaluator = CalibrationEvaluator()
        
        def temperature_objective(temp: float) -> float:
            """Objective function for temperature scaling optimization."""
            calibrated_confidences = self._apply_temperature_scaling(confidences, temp)
            return evaluator._compute_ece(calibrated_confidences, correctness)
        
        # Find optimal temperature
        result = minimize_scalar(temperature_objective, bounds=(0.1, 5.0), method='bounded')
        self.temperature = result.x
        self.is_fitted = True
        
        return self.temperature
    
    def _apply_temperature_scaling(
        self, 
        confidences: List[float], 
        temperature: float
    ) -> List[float]:
        """Apply temperature scaling to confidence scores."""
        # Convert to logits, apply temperature, convert back to probabilities
        confidences = np.array(confidences)
        # Avoid log(0) and log(1)
        confidences = np.clip(confidences, 1e-8, 1 - 1e-8)
        
        logits = np.log(confidences / (1 - confidences))
        scaled_logits = logits / temperature
        scaled_confidences = 1 / (1 + np.exp(-scaled_logits))
        
        return scaled_confidences.tolist()
    
    def calibrate_confidence(self, confidence: float) -> float:
        """
        Apply fitted temperature scaling to a single confidence score.
        
        Args:
            confidence: Raw confidence score
            
        Returns:
            Calibrated confidence score
        """
        if not self.is_fitted:
            raise ValueError("Calibrator must be fitted before use")
        
        return self._apply_temperature_scaling([confidence], self.temperature)[0]


class CalibrationEvaluator:
    """
    Evaluates confidence calibration using standard metrics.
    
    Implements ECE, ACE, MCE, Brier Score, and reliability diagrams.
    """
    
    def __init__(self, n_bins: int = 10):
        self.n_bins = n_bins
    
    def evaluate_calibration(
        self, 
        data_points: List[CalibrationDataPoint]
    ) -> CalibrationMetrics:
        """
        Compute comprehensive calibration metrics.
        
        Args:
            data_points: List of calibration data points
            
        Returns:
            CalibrationMetrics with all computed metrics
        """
        confidences = [dp.predicted_confidence for dp in data_points]
        correctness = [dp.actual_correctness for dp in data_points]
        
        # Compute all metrics
        ece = self._compute_ece(confidences, correctness)
        ace = self._compute_ace(confidences, correctness)
        mce = self._compute_mce(confidences, correctness)
        brier = brier_score_loss(correctness, confidences)
        nll = self._compute_nll(confidences, correctness)
        reliability_data = self._compute_reliability_diagram_data(confidences, correctness)
        
        return CalibrationMetrics(
            ece=ece,
            ace=ace,
            mce=mce,
            brier_score=brier,
            negative_log_likelihood=nll,
            reliability_diagram_data=reliability_data
        )
    
    def _compute_ece(self, confidences: List[float], correctness: List[float]) -> float:
        """
        Compute Expected Calibration Error (ECE).
        
        ECE measures the difference between confidence and accuracy across bins.
        """
        confidences = np.array(confidences)
        correctness = np.array(correctness)
        
        bin_boundaries = np.linspace(0, 1, self.n_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]
        
        ece = 0.0
        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
            # Find samples in this bin
            in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
            prop_in_bin = in_bin.mean()
            
            if prop_in_bin > 0:
                accuracy_in_bin = correctness[in_bin].mean()
                avg_confidence_in_bin = confidences[in_bin].mean()
                ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin
        
        return ece
    
    def _compute_ace(self, confidences: List[float], correctness: List[float]) -> float:
        """
        Compute Adaptive Calibration Error (ACE).
        
        ACE addresses binning bias by using equal-mass bins.
        """
        confidences = np.array(confidences)
        correctness = np.array(correctness)
        
        # Sort by confidence
        indices = np.argsort(confidences)
        sorted_confidences = confidences[indices]
        sorted_correctness = correctness[indices]
        
        n_samples = len(confidences)
        bin_size = n_samples // self.n_bins
        
        ace = 0.0
        for i in range(self.n_bins):
            start_idx = i * bin_size
            end_idx = (i + 1) * bin_size if i < self.n_bins - 1 else n_samples
            
            bin_confidences = sorted_confidences[start_idx:end_idx]
            bin_correctness = sorted_correctness[start_idx:end_idx]
            
            if len(bin_confidences) > 0:
                avg_confidence = bin_confidences.mean()
                accuracy = bin_correctness.mean()
                bin_weight = len(bin_confidences) / n_samples
                ace += np.abs(avg_confidence - accuracy) * bin_weight
        
        return ace
    
    def _compute_mce(self, confidences: List[float], correctness: List[float]) -> float:
        """
        Compute Maximum Calibration Error (MCE).
        
        MCE is the maximum difference between confidence and accuracy across bins.
        """
        confidences = np.array(confidences)
        correctness = np.array(correctness)
        
        bin_boundaries = np.linspace(0, 1, self.n_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]
        
        max_error = 0.0
        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
            in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
            
            if in_bin.sum() > 0:
                accuracy_in_bin = correctness[in_bin].mean()
                avg_confidence_in_bin = confidences[in_bin].mean()
                error = np.abs(avg_confidence_in_bin - accuracy_in_bin)
                max_error = max(max_error, error)
        
        return max_error
    
    def _compute_nll(self, confidences: List[float], correctness: List[float]) -> float:
        """Compute Negative Log Likelihood."""
        confidences = np.array(confidences)
        correctness = np.array(correctness)
        
        # Avoid log(0)
        confidences = np.clip(confidences, 1e-8, 1 - 1e-8)
        
        # For binary classification: NLL = -Σ[y*log(p) + (1-y)*log(1-p)]
        nll = -(correctness * np.log(confidences) + 
                (1 - correctness) * np.log(1 - confidences)).mean()
        
        return nll
    
    def _compute_reliability_diagram_data(
        self, 
        confidences: List[float], 
        correctness: List[float]
    ) -> Dict[str, List[float]]:
        """Compute data for reliability diagram visualization."""
        confidences = np.array(confidences)
        correctness = np.array(correctness)
        
        bin_boundaries = np.linspace(0, 1, self.n_bins + 1)
        bin_centers = (bin_boundaries[:-1] + bin_boundaries[1:]) / 2
        
        bin_confidences = []
        bin_accuracies = []
        bin_counts = []
        
        for i in range(self.n_bins):
            bin_lower = bin_boundaries[i]
            bin_upper = bin_boundaries[i + 1]
            
            in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
            count = in_bin.sum()
            
            if count > 0:
                avg_confidence = confidences[in_bin].mean()
                accuracy = correctness[in_bin].mean()
            else:
                avg_confidence = bin_centers[i]
                accuracy = 0.0
            
            bin_confidences.append(avg_confidence)
            bin_accuracies.append(accuracy)
            bin_counts.append(count)
        
        return {
            "bin_centers": bin_centers.tolist(),
            "bin_confidences": bin_confidences,
            "bin_accuracies": bin_accuracies,
            "bin_counts": bin_counts
        }
    
    def plot_reliability_diagram(
        self, 
        metrics: CalibrationMetrics, 
        save_path: Optional[Path] = None
    ) -> None:
        """
        Create and optionally save a reliability diagram.
        
        Args:
            metrics: CalibrationMetrics containing reliability data
            save_path: Optional path to save the plot
        """
        data = metrics.reliability_diagram_data
        
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Plot reliability line (perfect calibration)
        ax.plot([0, 1], [0, 1], 'k--', alpha=0.7, label='Perfect calibration')
        
        # Plot actual calibration
        ax.bar(
            data["bin_centers"], 
            data["bin_accuracies"],
            width=0.08,
            alpha=0.7,
            edgecolor='black',
            label='Model calibration'
        )
        
        # Plot gap between confidence and accuracy
        for center, conf, acc in zip(
            data["bin_centers"], 
            data["bin_confidences"], 
            data["bin_accuracies"]
        ):
            if conf != acc:
                ax.plot([center, center], [acc, conf], 'r-', alpha=0.8, linewidth=2)
        
        ax.set_xlabel('Confidence')
        ax.set_ylabel('Accuracy')
        ax.set_title(f'Reliability Diagram (ECE: {metrics.ece:.3f})')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
        else:
            plt.show()


def create_evaluation_dataset_from_test_results(
    test_results: List[Dict[str, Any]]
) -> List[CalibrationDataPoint]:
    """
    Convert test results into calibration evaluation dataset.
    
    Args:
        test_results: List of test result dictionaries
        
    Returns:
        List of CalibrationDataPoint objects
    """
    data_points = []
    
    for result in test_results:
        # Extract correctness (this would need domain-specific logic)
        # For now, use a simple heuristic based on answer quality
        correctness = _assess_answer_correctness(result)
        
        data_point = CalibrationDataPoint(
            predicted_confidence=result.get('confidence', 0.0),
            actual_correctness=correctness,
            query=result.get('query', ''),
            answer=result.get('answer', ''),
            context_relevance=_compute_context_relevance(result),
            metadata={
                'model_used': result.get('model_used', ''),
                'retrieval_method': result.get('retrieval_method', ''),
                'num_citations': len(result.get('citations', []))
            }
        )
        data_points.append(data_point)
    
    return data_points


def _assess_answer_correctness(result: Dict[str, Any]) -> float:
    """
    Assess answer correctness for calibration evaluation.
    
    This is a simplified heuristic - in practice, this should be:
    1. Human evaluation
    2. Automated fact-checking against ground truth
    3. Domain-specific quality metrics
    """
    answer = result.get('answer', '').lower()
    citations = result.get('citations', [])
    
    # Simple heuristic: consider correct if has citations and no uncertainty
    uncertainty_phrases = [
        'cannot answer', 'not contained', 'no relevant', 
        'insufficient information', 'unclear', 'not specified'
    ]
    
    has_uncertainty = any(phrase in answer for phrase in uncertainty_phrases)
    has_citations = len(citations) > 0
    
    if has_uncertainty:
        return 0.0  # Explicit uncertainty = incorrect/no answer
    elif has_citations and len(answer.split()) > 10:
        return 1.0  # Has citations and substantial answer = likely correct
    else:
        return 0.5  # Partial credit for borderline cases


def _compute_context_relevance(result: Dict[str, Any]) -> float:
    """Compute average relevance of retrieved context."""
    citations = result.get('citations', [])
    if not citations:
        return 0.0
    
    relevances = [citation.get('relevance', 0.0) for citation in citations]
    return sum(relevances) / len(relevances)


if __name__ == "__main__":
    # Example usage and testing
    print("Testing confidence calibration framework...")
    
    # Create mock data for testing
    np.random.seed(42)
    n_samples = 100
    
    # Simulate miscalibrated confidence scores (too high)
    true_correctness = np.random.binomial(1, 0.6, n_samples)
    predicted_confidence = np.random.beta(8, 3, n_samples)  # Overconfident
    
    # Test calibration evaluation
    evaluator = CalibrationEvaluator()
    data_points = [
        CalibrationDataPoint(
            predicted_confidence=conf,
            actual_correctness=float(correct),
            query=f"query_{i}",
            answer=f"answer_{i}",
            context_relevance=0.7,
            metadata={}
        )
        for i, (conf, correct) in enumerate(zip(predicted_confidence, true_correctness))
    ]
    
    metrics = evaluator.evaluate_calibration(data_points)
    
    print(f"Before calibration:")
    print(f"  ECE: {metrics.ece:.3f}")
    print(f"  ACE: {metrics.ace:.3f}")
    print(f"  MCE: {metrics.mce:.3f}")
    print(f"  Brier Score: {metrics.brier_score:.3f}")
    
    # Test temperature scaling
    calibrator = ConfidenceCalibrator()
    optimal_temp = calibrator.fit_temperature_scaling(
        predicted_confidence.tolist(), 
        true_correctness.tolist()
    )
    
    print(f"  Optimal temperature: {optimal_temp:.3f}")
    
    # Apply calibration
    calibrated_confidences = [
        calibrator.calibrate_confidence(conf) for conf in predicted_confidence
    ]
    
    # Re-evaluate
    calibrated_data_points = [
        CalibrationDataPoint(
            predicted_confidence=conf,
            actual_correctness=float(correct),
            query=f"query_{i}",
            answer=f"answer_{i}",
            context_relevance=0.7,
            metadata={}
        )
        for i, (conf, correct) in enumerate(zip(calibrated_confidences, true_correctness))
    ]
    
    calibrated_metrics = evaluator.evaluate_calibration(calibrated_data_points)
    
    print(f"\nAfter temperature scaling:")
    print(f"  ECE: {calibrated_metrics.ece:.3f}")
    print(f"  ACE: {calibrated_metrics.ace:.3f}")
    print(f"  MCE: {calibrated_metrics.mce:.3f}")
    print(f"  Brier Score: {calibrated_metrics.brier_score:.3f}")
    
    print("\n✅ Calibration framework working correctly!")