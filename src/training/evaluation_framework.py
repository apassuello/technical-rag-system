#!/usr/bin/env python3
"""
Evaluation Framework for Epic 1 ML Models

This module provides comprehensive evaluation capabilities for individual view models
and the ensemble Epic1MLAnalyzer system.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support, confusion_matrix,
    mean_squared_error, mean_absolute_error, r2_score,
    classification_report, roc_auc_score, roc_curve
)
from sklearn.preprocessing import label_binarize
import scipy.stats as stats
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EvaluationMetrics:
    """Container for evaluation metrics."""
    
    # Classification metrics
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    macro_f1: float
    weighted_f1: float
    
    # Regression metrics
    mse: float
    mae: float
    r2: float
    
    # Additional metrics
    confusion_matrix: np.ndarray
    classification_report: Dict[str, Any]
    
    # Per-class metrics
    per_class_precision: List[float]
    per_class_recall: List[float]
    per_class_f1: List[float]


class ViewEvaluator:
    """Evaluator for individual view models."""
    
    def __init__(self, view_name: str, class_names: List[str] = None):
        self.view_name = view_name
        self.class_names = class_names or ['simple', 'medium', 'complex']
        self.class_to_idx = {name: idx for idx, name in enumerate(self.class_names)}
        
    def evaluate(
        self,
        predictions: Dict[str, np.ndarray],
        compute_detailed_metrics: bool = True
    ) -> EvaluationMetrics:
        """
        Comprehensive evaluation of model predictions.
        
        Args:
            predictions: Dictionary containing predictions and targets
            compute_detailed_metrics: Whether to compute detailed metrics
            
        Returns:
            EvaluationMetrics object with all computed metrics
        """
        score_preds = predictions['score_predictions']
        class_preds = predictions['class_predictions']
        targets = predictions['targets']
        
        # Convert targets to scores (for regression metrics)
        target_scores = self._class_to_score(targets)
        
        # Classification metrics
        accuracy = accuracy_score(targets, class_preds)
        precision, recall, f1, _ = precision_recall_fscore_support(
            targets, class_preds, average=None
        )
        macro_f1 = np.mean(f1)
        weighted_f1 = precision_recall_fscore_support(
            targets, class_preds, average='weighted'
        )[2]
        
        # Regression metrics  
        mse = mean_squared_error(target_scores, score_preds)
        mae = mean_absolute_error(target_scores, score_preds)
        r2 = r2_score(target_scores, score_preds)
        
        # Confusion matrix
        cm = confusion_matrix(targets, class_preds)
        
        # Classification report
        report = classification_report(
            targets, class_preds,
            target_names=self.class_names,
            output_dict=True
        )
        
        metrics = EvaluationMetrics(
            accuracy=accuracy,
            precision=np.mean(precision),
            recall=np.mean(recall),
            f1_score=np.mean(f1),
            macro_f1=macro_f1,
            weighted_f1=weighted_f1,
            mse=mse,
            mae=mae,
            r2=r2,
            confusion_matrix=cm,
            classification_report=report,
            per_class_precision=precision.tolist(),
            per_class_recall=recall.tolist(),
            per_class_f1=f1.tolist()
        )
        
        return metrics
    
    def _class_to_score(self, class_indices: np.ndarray) -> np.ndarray:
        """Convert class indices to complexity scores."""
        # Simple mapping: simple=0.2, medium=0.5, complex=0.8
        score_map = {0: 0.2, 1: 0.5, 2: 0.8}
        return np.array([score_map.get(idx, 0.5) for idx in class_indices])
    
    def plot_confusion_matrix(
        self,
        confusion_matrix: np.ndarray,
        save_path: Optional[Path] = None
    ) -> None:
        """Plot confusion matrix."""
        plt.figure(figsize=(8, 6))
        
        sns.heatmap(
            confusion_matrix,
            annot=True,
            fmt='d',
            cmap='Blues',
            xticklabels=self.class_names,
            yticklabels=self.class_names
        )
        
        plt.title(f'{self.view_name} View - Confusion Matrix')
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved confusion matrix to {save_path}")
        
        plt.show()
    
    def plot_score_predictions(
        self,
        predictions: Dict[str, np.ndarray],
        save_path: Optional[Path] = None
    ) -> None:
        """Plot regression predictions vs targets."""
        score_preds = predictions['score_predictions']
        targets = predictions['targets']
        target_scores = self._class_to_score(targets)
        
        plt.figure(figsize=(10, 8))
        
        # Scatter plot
        plt.subplot(2, 2, 1)
        plt.scatter(target_scores, score_preds, alpha=0.6)
        plt.plot([0, 1], [0, 1], 'r--', lw=2)
        plt.xlabel('True Complexity Score')
        plt.ylabel('Predicted Complexity Score')
        plt.title('Predictions vs True Values')
        plt.grid(True)
        
        # Residuals plot
        plt.subplot(2, 2, 2)
        residuals = score_preds - target_scores
        plt.scatter(target_scores, residuals, alpha=0.6)
        plt.axhline(y=0, color='r', linestyle='--')
        plt.xlabel('True Complexity Score')
        plt.ylabel('Residuals')
        plt.title('Residual Plot')
        plt.grid(True)
        
        # Distribution of predictions
        plt.subplot(2, 2, 3)
        plt.hist(score_preds, bins=20, alpha=0.7, label='Predictions')
        plt.hist(target_scores, bins=20, alpha=0.7, label='True Values')
        plt.xlabel('Complexity Score')
        plt.ylabel('Frequency')
        plt.title('Score Distributions')
        plt.legend()
        plt.grid(True)
        
        # Box plot by class
        plt.subplot(2, 2, 4)
        df = pd.DataFrame({
            'true_class': [self.class_names[i] for i in targets],
            'predicted_score': score_preds
        })
        df.boxplot(column='predicted_score', by='true_class', ax=plt.gca())
        plt.title('Predicted Scores by True Class')
        plt.suptitle('')  # Remove automatic title
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved score prediction plots to {save_path}")
        
        plt.show()
    
    def generate_report(
        self,
        metrics: EvaluationMetrics,
        predictions: Dict[str, np.ndarray],
        save_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive evaluation report."""
        
        report = {
            'view_name': self.view_name,
            'dataset_size': len(predictions['targets']),
            'class_distribution': {},
            'metrics': {
                'classification': {
                    'accuracy': float(metrics.accuracy),
                    'macro_precision': float(metrics.precision),
                    'macro_recall': float(metrics.recall),
                    'macro_f1': float(metrics.macro_f1),
                    'weighted_f1': float(metrics.weighted_f1)
                },
                'regression': {
                    'mse': float(metrics.mse),
                    'mae': float(metrics.mae),
                    'rmse': float(np.sqrt(metrics.mse)),
                    'r2': float(metrics.r2)
                },
                'per_class': {
                    'precision': dict(zip(self.class_names, metrics.per_class_precision)),
                    'recall': dict(zip(self.class_names, metrics.per_class_recall)),
                    'f1_score': dict(zip(self.class_names, metrics.per_class_f1))
                }
            },
            'analysis': {}
        }
        
        # Class distribution
        targets = predictions['targets']
        unique, counts = np.unique(targets, return_counts=True)
        for class_idx, count in zip(unique, counts):
            class_name = self.class_names[class_idx]
            report['class_distribution'][class_name] = {
                'count': int(count),
                'percentage': float(count / len(targets) * 100)
            }
        
        # Performance analysis
        report['analysis'] = self._analyze_performance(metrics, predictions)
        
        if save_path:
            with open(save_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Saved evaluation report to {save_path}")
        
        return report
    
    def _analyze_performance(
        self,
        metrics: EvaluationMetrics,
        predictions: Dict[str, np.ndarray]
    ) -> Dict[str, Any]:
        """Analyze model performance and identify issues."""
        
        analysis = {
            'strengths': [],
            'weaknesses': [],
            'recommendations': []
        }
        
        # Classification analysis
        if metrics.accuracy >= 0.85:
            analysis['strengths'].append("High classification accuracy (≥85%)")
        elif metrics.accuracy >= 0.75:
            analysis['strengths'].append("Good classification accuracy (≥75%)")
        else:
            analysis['weaknesses'].append("Low classification accuracy (<75%)")
            analysis['recommendations'].append("Consider adjusting model architecture or training parameters")
        
        # Per-class analysis
        worst_class_idx = np.argmin(metrics.per_class_f1)
        worst_class = self.class_names[worst_class_idx]
        worst_f1 = metrics.per_class_f1[worst_class_idx]
        
        if worst_f1 < 0.7:
            analysis['weaknesses'].append(f"Poor performance on '{worst_class}' class (F1={worst_f1:.3f})")
            analysis['recommendations'].append(f"Increase training data for '{worst_class}' class")
        
        # Regression analysis
        if metrics.r2 >= 0.7:
            analysis['strengths'].append("Good score prediction (R²≥0.7)")
        elif metrics.r2 >= 0.5:
            analysis['strengths'].append("Moderate score prediction (R²≥0.5)")
        else:
            analysis['weaknesses'].append("Poor score prediction (R²<0.5)")
            analysis['recommendations'].append("Review feature engineering and model architecture")
        
        # Bias analysis
        score_preds = predictions['score_predictions']
        targets = predictions['targets']
        target_scores = self._class_to_score(targets)
        
        bias = np.mean(score_preds - target_scores)
        if abs(bias) > 0.1:
            if bias > 0:
                analysis['weaknesses'].append(f"Model tends to overpredict complexity (bias=+{bias:.3f})")
            else:
                analysis['weaknesses'].append(f"Model tends to underpredict complexity (bias={bias:.3f})")
            analysis['recommendations'].append("Consider adjusting training data distribution or loss function")
        
        return analysis


class EnsembleEvaluator:
    """Evaluator for the complete Epic1MLAnalyzer ensemble."""
    
    def __init__(self):
        self.view_names = ['technical', 'linguistic', 'task', 'semantic', 'computational']
        
    def evaluate_ensemble(
        self,
        view_predictions: Dict[str, Dict[str, np.ndarray]],
        ensemble_predictions: Dict[str, np.ndarray],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate ensemble performance and view contributions.
        
        Args:
            view_predictions: Predictions from individual views
            ensemble_predictions: Final ensemble predictions
            weights: View weights used in ensemble
            
        Returns:
            Comprehensive ensemble evaluation report
        """
        
        # Individual view evaluations
        view_evaluations = {}
        for view_name, predictions in view_predictions.items():
            evaluator = ViewEvaluator(view_name)
            metrics = evaluator.evaluate(predictions)
            view_evaluations[view_name] = {
                'metrics': metrics,
                'evaluator': evaluator
            }
        
        # Ensemble evaluation
        ensemble_evaluator = ViewEvaluator('ensemble')
        ensemble_metrics = ensemble_evaluator.evaluate(ensemble_predictions)
        
        # Compare ensemble vs individual views
        comparison = self._compare_ensemble_to_views(
            view_evaluations, ensemble_metrics
        )
        
        # Analyze view contributions
        contribution_analysis = self._analyze_view_contributions(
            view_predictions, ensemble_predictions, weights
        )
        
        # Generate comprehensive report
        ensemble_report = {
            'ensemble_performance': {
                'accuracy': float(ensemble_metrics.accuracy),
                'macro_f1': float(ensemble_metrics.macro_f1),
                'weighted_f1': float(ensemble_metrics.weighted_f1),
                'mse': float(ensemble_metrics.mse),
                'r2': float(ensemble_metrics.r2)
            },
            'individual_view_performance': {},
            'ensemble_vs_individual': comparison,
            'view_contributions': contribution_analysis,
            'overall_assessment': self._generate_overall_assessment(
                ensemble_metrics, view_evaluations, comparison
            )
        }
        
        # Add individual view performance
        for view_name, evaluation in view_evaluations.items():
            metrics = evaluation['metrics']
            ensemble_report['individual_view_performance'][view_name] = {
                'accuracy': float(metrics.accuracy),
                'macro_f1': float(metrics.macro_f1),
                'mse': float(metrics.mse),
                'r2': float(metrics.r2)
            }
        
        return ensemble_report
    
    def _compare_ensemble_to_views(
        self,
        view_evaluations: Dict[str, Any],
        ensemble_metrics: EvaluationMetrics
    ) -> Dict[str, Any]:
        """Compare ensemble performance to individual views."""
        
        comparison = {
            'best_individual_view': None,
            'improvement_over_best': {},
            'improvement_over_average': {}
        }
        
        # Find best individual view
        best_accuracy = 0
        best_view = None
        
        view_accuracies = {}
        for view_name, evaluation in view_evaluations.items():
            accuracy = evaluation['metrics'].accuracy
            view_accuracies[view_name] = accuracy
            
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_view = view_name
        
        comparison['best_individual_view'] = {
            'name': best_view,
            'accuracy': float(best_accuracy)
        }
        
        # Calculate improvements
        ensemble_accuracy = ensemble_metrics.accuracy
        comparison['improvement_over_best']['accuracy'] = float(ensemble_accuracy - best_accuracy)
        
        avg_accuracy = np.mean(list(view_accuracies.values()))
        comparison['improvement_over_average']['accuracy'] = float(ensemble_accuracy - avg_accuracy)
        
        # Same for F1 scores
        view_f1s = {name: eval_data['metrics'].macro_f1 for name, eval_data in view_evaluations.items()}
        best_f1 = max(view_f1s.values())
        avg_f1 = np.mean(list(view_f1s.values()))
        
        comparison['improvement_over_best']['macro_f1'] = float(ensemble_metrics.macro_f1 - best_f1)
        comparison['improvement_over_average']['macro_f1'] = float(ensemble_metrics.macro_f1 - avg_f1)
        
        return comparison
    
    def _analyze_view_contributions(
        self,
        view_predictions: Dict[str, Dict[str, np.ndarray]],
        ensemble_predictions: Dict[str, np.ndarray],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Analyze how each view contributes to ensemble performance."""
        
        contribution_analysis = {
            'correlation_with_ensemble': {},
            'individual_importance': {},
            'complementarity_analysis': {}
        }
        
        ensemble_scores = ensemble_predictions['score_predictions']
        
        # Calculate correlations
        for view_name, predictions in view_predictions.items():
            view_scores = predictions['score_predictions']
            correlation = np.corrcoef(view_scores, ensemble_scores)[0, 1]
            contribution_analysis['correlation_with_ensemble'][view_name] = float(correlation)
        
        # Importance based on weights (if provided)
        if weights:
            contribution_analysis['individual_importance'] = {
                name: float(weight) for name, weight in weights.items()
            }
        
        # Complementarity analysis - how much each view adds beyond others
        for view_name in view_predictions.keys():
            other_views = {k: v for k, v in view_predictions.items() if k != view_name}
            
            # Simple ensemble of other views (mean)
            other_scores = np.mean([
                pred['score_predictions'] for pred in other_views.values()
            ], axis=0)
            
            # Compare full ensemble vs ensemble without this view
            full_ensemble_error = np.mean((ensemble_scores - ensemble_predictions['targets']) ** 2)
            partial_ensemble_error = np.mean((other_scores - self._class_to_score(ensemble_predictions['targets'])) ** 2)
            
            contribution = partial_ensemble_error - full_ensemble_error
            contribution_analysis['complementarity_analysis'][view_name] = float(contribution)
        
        return contribution_analysis
    
    def _class_to_score(self, class_indices: np.ndarray) -> np.ndarray:
        """Convert class indices to complexity scores."""
        score_map = {0: 0.2, 1: 0.5, 2: 0.8}
        return np.array([score_map.get(idx, 0.5) for idx in class_indices])
    
    def _generate_overall_assessment(
        self,
        ensemble_metrics: EvaluationMetrics,
        view_evaluations: Dict[str, Any],
        comparison: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate overall assessment of the ensemble system."""
        
        assessment = {
            'meets_target_accuracy': ensemble_metrics.accuracy >= 0.85,
            'target_accuracy': 0.85,
            'actual_accuracy': float(ensemble_metrics.accuracy),
            'performance_grade': '',
            'strengths': [],
            'areas_for_improvement': [],
            'next_steps': []
        }
        
        # Performance grading
        if ensemble_metrics.accuracy >= 0.90:
            assessment['performance_grade'] = 'Excellent (≥90%)'
        elif ensemble_metrics.accuracy >= 0.85:
            assessment['performance_grade'] = 'Good (≥85%)'
        elif ensemble_metrics.accuracy >= 0.75:
            assessment['performance_grade'] = 'Fair (≥75%)'
        else:
            assessment['performance_grade'] = 'Needs Improvement (<75%)'
        
        # Identify strengths
        if comparison['improvement_over_best']['accuracy'] > 0.02:
            assessment['strengths'].append("Ensemble significantly outperforms best individual view")
        
        if ensemble_metrics.r2 >= 0.7:
            assessment['strengths'].append("Good regression performance (R²≥0.7)")
        
        # Identify areas for improvement
        if ensemble_metrics.accuracy < 0.85:
            assessment['areas_for_improvement'].append("Accuracy below target (85%)")
            assessment['next_steps'].append("Increase training data or improve model architecture")
        
        if comparison['improvement_over_best']['accuracy'] < 0.01:
            assessment['areas_for_improvement'].append("Limited ensemble benefit")
            assessment['next_steps'].append("Review view diversity and ensemble strategy")
        
        # Check individual view performance
        weak_views = []
        for view_name, evaluation in view_evaluations.items():
            if evaluation['metrics'].accuracy < 0.7:
                weak_views.append(view_name)
        
        if weak_views:
            assessment['areas_for_improvement'].append(f"Weak individual views: {', '.join(weak_views)}")
            assessment['next_steps'].append("Focus training efforts on underperforming views")
        
        return assessment
    
    def plot_ensemble_comparison(
        self,
        ensemble_report: Dict[str, Any],
        save_path: Optional[Path] = None
    ) -> None:
        """Plot comparison of ensemble vs individual view performance."""
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Accuracy comparison
        view_names = list(ensemble_report['individual_view_performance'].keys())
        accuracies = [ensemble_report['individual_view_performance'][name]['accuracy'] 
                     for name in view_names]
        accuracies.append(ensemble_report['ensemble_performance']['accuracy'])
        names = view_names + ['Ensemble']
        
        axes[0, 0].bar(names, accuracies, color='skyblue', alpha=0.7)
        axes[0, 0].axhline(y=0.85, color='red', linestyle='--', label='Target (85%)')
        axes[0, 0].set_title('Accuracy Comparison')
        axes[0, 0].set_ylabel('Accuracy')
        axes[0, 0].tick_params(axis='x', rotation=45)
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # F1 scores comparison
        f1_scores = [ensemble_report['individual_view_performance'][name]['macro_f1'] 
                    for name in view_names]
        f1_scores.append(ensemble_report['ensemble_performance']['macro_f1'])
        
        axes[0, 1].bar(names, f1_scores, color='lightgreen', alpha=0.7)
        axes[0, 1].set_title('Macro F1-Score Comparison')
        axes[0, 1].set_ylabel('Macro F1-Score')
        axes[0, 1].tick_params(axis='x', rotation=45)
        axes[0, 1].grid(True, alpha=0.3)
        
        # View contributions
        if 'correlation_with_ensemble' in ensemble_report['view_contributions']:
            correlations = ensemble_report['view_contributions']['correlation_with_ensemble']
            axes[1, 0].bar(correlations.keys(), correlations.values(), color='orange', alpha=0.7)
            axes[1, 0].set_title('View Correlation with Ensemble')
            axes[1, 0].set_ylabel('Correlation Coefficient')
            axes[1, 0].tick_params(axis='x', rotation=45)
            axes[1, 0].grid(True, alpha=0.3)
        
        # R² comparison
        r2_scores = [ensemble_report['individual_view_performance'][name]['r2'] 
                    for name in view_names]
        r2_scores.append(ensemble_report['ensemble_performance']['r2'])
        
        axes[1, 1].bar(names, r2_scores, color='lightcoral', alpha=0.7)
        axes[1, 1].set_title('R² Score Comparison')
        axes[1, 1].set_ylabel('R² Score')
        axes[1, 1].tick_params(axis='x', rotation=45)
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved ensemble comparison plot to {save_path}")
        
        plt.show()


def main():
    """Example usage of the evaluation framework."""
    
    # Mock predictions for demonstration
    np.random.seed(42)
    n_samples = 1000
    
    # Generate mock predictions
    targets = np.random.choice([0, 1, 2], size=n_samples, p=[0.3, 0.4, 0.3])
    score_preds = np.random.uniform(0, 1, n_samples)
    class_preds = np.random.choice([0, 1, 2], size=n_samples, p=[0.25, 0.5, 0.25])
    
    predictions = {
        'score_predictions': score_preds,
        'class_predictions': class_preds,
        'targets': targets
    }
    
    # Evaluate single view
    evaluator = ViewEvaluator('technical')
    metrics = evaluator.evaluate(predictions)
    
    print(f"Accuracy: {metrics.accuracy:.3f}")
    print(f"Macro F1: {metrics.macro_f1:.3f}")
    print(f"R²: {metrics.r2:.3f}")
    
    # Generate report
    report = evaluator.generate_report(metrics, predictions)
    print(f"\nStrengths: {report['analysis']['strengths']}")
    print(f"Weaknesses: {report['analysis']['weaknesses']}")


if __name__ == "__main__":
    main()