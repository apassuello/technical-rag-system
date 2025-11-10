#!/usr/bin/env python3
"""
Comprehensive test suite for Evaluation Framework.

This module provides complete test coverage for the Epic1 ML evaluation system
including individual view evaluators, ensemble evaluation, metrics calculation,
performance analysis, and visualization components.

Target Coverage: 70% (~464 test lines for 663 component lines)
Priority: HIGH (Training infrastructure evaluation system)
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock, mock_open
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
from pathlib import Path

# Import systems under test
from src.training.evaluation_framework import (
    ViewEvaluator,
    EnsembleEvaluator,
    EvaluationMetrics
)


class TestEvaluationMetricsDataStructure:
    """Test EvaluationMetrics data structure."""
    
    def test_evaluation_metrics_creation(self):
        """Test creation of EvaluationMetrics with all fields."""
        confusion_matrix = np.array([[10, 2], [3, 15]])
        classification_report = {'accuracy': 0.83, 'macro avg': {'f1-score': 0.82}}
        
        metrics = EvaluationMetrics(
            accuracy=0.85,
            precision=0.82,
            recall=0.78,
            f1_score=0.80,
            macro_f1=0.79,
            weighted_f1=0.81,
            mse=0.05,
            mae=0.03,
            r2=0.75,
            confusion_matrix=confusion_matrix,
            classification_report=classification_report,
            per_class_precision=[0.8, 0.84, 0.81],
            per_class_recall=[0.77, 0.79, 0.78],
            per_class_f1=[0.78, 0.81, 0.79]
        )
        
        assert metrics.accuracy == 0.85
        assert metrics.precision == 0.82
        assert metrics.r2 == 0.75
        assert np.array_equal(metrics.confusion_matrix, confusion_matrix)
        assert len(metrics.per_class_precision) == 3
        assert metrics.classification_report['accuracy'] == 0.83
        
    def test_evaluation_metrics_numpy_array_handling(self):
        """Test proper handling of numpy arrays in metrics."""
        confusion_matrix = np.array([[50, 5, 2], [3, 45, 7], [1, 4, 48]])
        
        metrics = EvaluationMetrics(
            accuracy=0.90,
            precision=0.88,
            recall=0.87,
            f1_score=0.87,
            macro_f1=0.86,
            weighted_f1=0.88,
            mse=0.02,
            mae=0.01,
            r2=0.85,
            confusion_matrix=confusion_matrix,
            classification_report={},
            per_class_precision=[0.85, 0.89, 0.90],
            per_class_recall=[0.86, 0.88, 0.89],
            per_class_f1=[0.85, 0.88, 0.89]
        )
        
        assert isinstance(metrics.confusion_matrix, np.ndarray)
        assert metrics.confusion_matrix.shape == (3, 3)
        assert np.sum(metrics.confusion_matrix) == 165  # Total samples


class TestViewEvaluatorInitialization:
    """Test ViewEvaluator initialization and configuration."""
    
    def test_default_initialization(self):
        """Test ViewEvaluator with default parameters."""
        evaluator = ViewEvaluator("technical")
        
        assert evaluator.view_name == "technical"
        assert evaluator.class_names == ['simple', 'medium', 'complex']
        assert evaluator.class_to_idx == {'simple': 0, 'medium': 1, 'complex': 2}
        
    def test_custom_class_names(self):
        """Test ViewEvaluator with custom class names."""
        custom_classes = ['low', 'high']
        evaluator = ViewEvaluator("linguistic", custom_classes)
        
        assert evaluator.view_name == "linguistic"
        assert evaluator.class_names == ['low', 'high']
        assert evaluator.class_to_idx == {'low': 0, 'high': 1}
        
    def test_class_to_idx_mapping(self):
        """Test class to index mapping."""
        evaluator = ViewEvaluator("semantic", ['beginner', 'intermediate', 'advanced', 'expert'])
        
        expected_mapping = {'beginner': 0, 'intermediate': 1, 'advanced': 2, 'expert': 3}
        assert evaluator.class_to_idx == expected_mapping


class TestViewEvaluatorScoreConversion:
    """Test score conversion utilities."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = ViewEvaluator("technical")
        
    def test_class_to_score_conversion(self):
        """Test conversion from class indices to complexity scores."""
        class_indices = np.array([0, 1, 2, 1, 0])
        scores = self.evaluator._class_to_score(class_indices)
        
        expected_scores = np.array([0.2, 0.5, 0.8, 0.5, 0.2])
        np.testing.assert_array_equal(scores, expected_scores)
        
    def test_class_to_score_unknown_indices(self):
        """Test class to score conversion with unknown indices."""
        # Test with out-of-range indices
        class_indices = np.array([0, 5, 1, -1])
        scores = self.evaluator._class_to_score(class_indices)
        
        # Unknown indices should default to 0.5
        expected_scores = np.array([0.2, 0.5, 0.5, 0.5])
        np.testing.assert_array_equal(scores, expected_scores)
        
    def test_empty_class_indices(self):
        """Test class to score conversion with empty input."""
        empty_indices = np.array([])
        scores = self.evaluator._class_to_score(empty_indices)
        
        assert len(scores) == 0
        assert isinstance(scores, np.ndarray)


class TestViewEvaluatorMetricsCalculation:
    """Test comprehensive metrics calculation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = ViewEvaluator("technical")
        
        # Sample predictions data
        self.predictions = {
            'score_predictions': np.array([0.8, 0.6, 0.3, 0.9, 0.4, 0.7]),
            'class_predictions': np.array([2, 1, 0, 2, 0, 1]),  # complex, medium, simple, complex, simple, medium
            'targets': np.array([2, 1, 0, 2, 1, 1])  # complex, medium, simple, complex, medium, medium
        }
        
    @patch('sklearn.metrics.accuracy_score')
    @patch('sklearn.metrics.precision_recall_fscore_support')
    @patch('sklearn.metrics.mean_squared_error')
    @patch('sklearn.metrics.mean_absolute_error')
    @patch('sklearn.metrics.r2_score')
    @patch('sklearn.metrics.confusion_matrix')
    @patch('sklearn.metrics.classification_report')
    def test_comprehensive_evaluation(self, mock_report, mock_cm, mock_r2, mock_mae, mock_mse,
                                    mock_prf, mock_accuracy):
        """Test comprehensive evaluation with all metrics."""
        # Mock return values
        mock_accuracy.return_value = 0.83
        mock_prf.return_value = (np.array([0.8, 0.85, 0.82]), np.array([0.78, 0.88, 0.80]), 
                                np.array([0.79, 0.86, 0.81]), None)
        mock_mse.return_value = 0.05
        mock_mae.return_value = 0.03
        mock_r2.return_value = 0.75
        mock_cm.return_value = np.array([[8, 1, 1], [0, 9, 1], [1, 0, 9]])
        mock_report.return_value = {'accuracy': 0.83, 'macro avg': {'f1-score': 0.82}}
        
        metrics = self.evaluator.evaluate(self.predictions)
        
        # Verify all metrics are calculated
        assert isinstance(metrics, EvaluationMetrics)
        assert metrics.accuracy == 0.83
        assert abs(metrics.precision - 0.823) < 0.01  # Average of precisions
        assert abs(metrics.macro_f1 - 0.82) < 0.01
        assert metrics.mse == 0.05
        assert metrics.r2 == 0.75
        
        # Verify sklearn functions were called
        mock_accuracy.assert_called_once()
        mock_prf.assert_called()
        mock_mse.assert_called_once()
        mock_mae.assert_called_once()
        mock_r2.assert_called_once()
        mock_cm.assert_called_once()
        mock_report.assert_called_once()
        
    def test_evaluation_with_minimal_data(self):
        """Test evaluation with minimal data."""
        minimal_predictions = {
            'score_predictions': np.array([0.8, 0.3]),
            'class_predictions': np.array([1, 0]),
            'targets': np.array([1, 0])
        }
        
        metrics = self.evaluator.evaluate(minimal_predictions, compute_detailed_metrics=False)
        
        assert isinstance(metrics, EvaluationMetrics)
        assert 0 <= metrics.accuracy <= 1
        assert metrics.mse >= 0
        assert isinstance(metrics.per_class_precision, list)
        
    def test_evaluation_with_mismatched_shapes(self):
        """Test evaluation handles mismatched array shapes."""
        mismatched_predictions = {
            'score_predictions': np.array([0.8, 0.6, 0.3]),
            'class_predictions': np.array([2, 1]),  # Wrong length
            'targets': np.array([2, 1, 0])
        }
        
        # Should handle gracefully or raise appropriate error
        try:
            metrics = self.evaluator.evaluate(mismatched_predictions)
            # If it succeeds, verify it's reasonable
            assert isinstance(metrics, EvaluationMetrics)
        except (ValueError, IndexError) as e:
            # Expected for mismatched data
            assert "shape" in str(e).lower() or "length" in str(e).lower()
            
    def test_perfect_predictions_metrics(self):
        """Test metrics calculation with perfect predictions."""
        perfect_predictions = {
            'score_predictions': np.array([0.2, 0.5, 0.8, 0.2, 0.5]),
            'class_predictions': np.array([0, 1, 2, 0, 1]),
            'targets': np.array([0, 1, 2, 0, 1])
        }
        
        metrics = self.evaluator.evaluate(perfect_predictions)
        
        assert metrics.accuracy == 1.0
        assert abs(metrics.mse) < 0.001  # Should be very small
        assert all(f1 >= 0.99 for f1 in metrics.per_class_f1)  # Near-perfect F1 scores


class TestViewEvaluatorVisualization:
    """Test visualization functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = ViewEvaluator("technical")
        self.confusion_matrix = np.array([[45, 3, 2], [5, 40, 5], [2, 4, 44]])
        
        self.predictions = {
            'score_predictions': np.array([0.8, 0.6, 0.3, 0.9, 0.4]),
            'class_predictions': np.array([2, 1, 0, 2, 0]),
            'targets': np.array([2, 1, 0, 2, 1])
        }
        
    @patch('matplotlib.pyplot.show')
    @patch('matplotlib.pyplot.savefig')
    @patch('seaborn.heatmap')
    def test_confusion_matrix_plotting(self, mock_heatmap, mock_savefig, mock_show):
        """Test confusion matrix visualization."""
        save_path = Path("test_confusion_matrix.png")
        
        self.evaluator.plot_confusion_matrix(self.confusion_matrix, save_path)
        
        # Verify seaborn heatmap was called
        mock_heatmap.assert_called_once()
        
        # Verify plot was saved
        mock_savefig.assert_called_once_with(save_path, dpi=300, bbox_inches='tight')
        mock_show.assert_called_once()
        
    @patch('matplotlib.pyplot.show')
    @patch('matplotlib.pyplot.savefig')
    def test_score_prediction_plotting(self, mock_savefig, mock_show):
        """Test score prediction visualization."""
        save_path = Path("test_score_predictions.png")
        
        with patch('matplotlib.pyplot.subplot'):
            with patch('matplotlib.pyplot.scatter'):
                with patch('matplotlib.pyplot.hist'):
                    with patch('pandas.DataFrame.boxplot'):
                        
                        self.evaluator.plot_score_predictions(self.predictions, save_path)
                        
                        mock_savefig.assert_called_once_with(save_path, dpi=300, bbox_inches='tight')
                        mock_show.assert_called_once()
                        
    @patch('matplotlib.pyplot.show')
    def test_plotting_without_save_path(self, mock_show):
        """Test plotting without saving to file."""
        with patch('seaborn.heatmap'):
            self.evaluator.plot_confusion_matrix(self.confusion_matrix)
            mock_show.assert_called_once()
            
        with patch('matplotlib.pyplot.subplot'):
            with patch('matplotlib.pyplot.scatter'):
                with patch('matplotlib.pyplot.hist'):
                    with patch('pandas.DataFrame.boxplot'):
                        
                        self.evaluator.plot_score_predictions(self.predictions)
                        # show() called twice - once for each plot
                        assert mock_show.call_count == 2


class TestViewEvaluatorReportGeneration:
    """Test comprehensive report generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = ViewEvaluator("technical")
        
        self.metrics = EvaluationMetrics(
            accuracy=0.85,
            precision=0.82,
            recall=0.78,
            f1_score=0.80,
            macro_f1=0.79,
            weighted_f1=0.81,
            mse=0.05,
            mae=0.03,
            r2=0.75,
            confusion_matrix=np.array([[8, 1, 1], [0, 9, 1], [1, 0, 9]]),
            classification_report={'accuracy': 0.85},
            per_class_precision=[0.8, 0.84, 0.81],
            per_class_recall=[0.77, 0.79, 0.78],
            per_class_f1=[0.78, 0.81, 0.79]
        )
        
        self.predictions = {
            'score_predictions': np.array([0.8, 0.6, 0.3, 0.9, 0.4, 0.7]),
            'class_predictions': np.array([2, 1, 0, 2, 0, 1]),
            'targets': np.array([2, 1, 0, 2, 1, 1])
        }
        
    def test_comprehensive_report_structure(self):
        """Test structure of comprehensive evaluation report."""
        report = self.evaluator.generate_report(self.metrics, self.predictions)
        
        # Verify top-level structure
        required_keys = ['view_name', 'dataset_size', 'class_distribution', 'metrics', 'analysis']
        for key in required_keys:
            assert key in report
            
        # Verify metrics structure
        metrics_section = report['metrics']
        assert 'classification' in metrics_section
        assert 'regression' in metrics_section
        assert 'per_class' in metrics_section
        
        # Verify classification metrics
        classification_metrics = metrics_section['classification']
        expected_classification_keys = ['accuracy', 'macro_precision', 'macro_recall', 'macro_f1', 'weighted_f1']
        for key in expected_classification_keys:
            assert key in classification_metrics
            
        # Verify regression metrics
        regression_metrics = metrics_section['regression']
        expected_regression_keys = ['mse', 'mae', 'rmse', 'r2']
        for key in expected_regression_keys:
            assert key in regression_metrics
            
    def test_class_distribution_calculation(self):
        """Test class distribution calculation in report."""
        report = self.evaluator.generate_report(self.metrics, self.predictions)
        
        class_distribution = report['class_distribution']
        
        # Verify all classes are represented
        for class_name in self.evaluator.class_names:
            assert class_name in class_distribution
            
        # Verify structure of distribution data
        for class_name, distribution_data in class_distribution.items():
            assert 'count' in distribution_data
            assert 'percentage' in distribution_data
            assert isinstance(distribution_data['count'], int)
            assert isinstance(distribution_data['percentage'], float)
            
        # Verify percentages sum to 100 (approximately)
        total_percentage = sum(data['percentage'] for data in class_distribution.values())
        assert abs(total_percentage - 100.0) < 0.1
        
    def test_performance_analysis_generation(self):
        """Test performance analysis generation."""
        with patch.object(self.evaluator, '_analyze_performance') as mock_analyze:
            mock_analyze.return_value = {
                'strengths': ['High accuracy'],
                'weaknesses': ['Low recall on complex class'],
                'recommendations': ['Increase training data']
            }
            
            report = self.evaluator.generate_report(self.metrics, self.predictions)
            
            mock_analyze.assert_called_once_with(self.metrics, self.predictions)
            assert report['analysis']['strengths'] == ['High accuracy']
            assert report['analysis']['weaknesses'] == ['Low recall on complex class']
            
    def test_report_saving_to_file(self):
        """Test saving report to JSON file."""
        save_path = Path("test_report.json")
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.dump') as mock_json_dump:
                
                report = self.evaluator.generate_report(self.metrics, self.predictions, save_path)
                
                mock_file.assert_called_once_with(save_path, 'w')
                mock_json_dump.assert_called_once()
                
                # Verify the report is returned even when saving
                assert isinstance(report, dict)
                assert 'view_name' in report


class TestViewEvaluatorPerformanceAnalysis:
    """Test automated performance analysis functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = ViewEvaluator("technical")
        
    def test_high_accuracy_analysis(self):
        """Test analysis of high-accuracy results."""
        high_accuracy_metrics = EvaluationMetrics(
            accuracy=0.92,
            precision=0.90,
            recall=0.88,
            f1_score=0.89,
            macro_f1=0.88,
            weighted_f1=0.90,
            mse=0.02,
            mae=0.01,
            r2=0.85,
            confusion_matrix=np.array([[10, 0, 0], [0, 10, 0], [0, 0, 10]]),
            classification_report={},
            per_class_precision=[0.9, 0.9, 0.9],
            per_class_recall=[0.9, 0.9, 0.9],
            per_class_f1=[0.9, 0.9, 0.9]
        )
        
        predictions = {
            'score_predictions': np.array([0.2, 0.5, 0.8] * 10),
            'targets': np.array([0, 1, 2] * 10)
        }
        
        analysis = self.evaluator._analyze_performance(high_accuracy_metrics, predictions)
        
        assert "High classification accuracy" in str(analysis['strengths'])
        assert len(analysis['weaknesses']) == 0  # Should have no significant weaknesses
        
    def test_low_accuracy_analysis(self):
        """Test analysis of low-accuracy results."""
        low_accuracy_metrics = EvaluationMetrics(
            accuracy=0.65,
            precision=0.60,
            recall=0.58,
            f1_score=0.59,
            macro_f1=0.58,
            weighted_f1=0.60,
            mse=0.15,
            mae=0.12,
            r2=0.25,
            confusion_matrix=np.array([[5, 3, 2], [4, 4, 2], [3, 2, 5]]),
            classification_report={},
            per_class_precision=[0.6, 0.6, 0.6],
            per_class_recall=[0.5, 0.4, 0.5],
            per_class_f1=[0.55, 0.48, 0.55]
        )
        
        predictions = {
            'score_predictions': np.array([0.3, 0.4, 0.6] * 10),
            'targets': np.array([0, 1, 2] * 10)
        }
        
        analysis = self.evaluator._analyze_performance(low_accuracy_metrics, predictions)
        
        assert any("Low classification accuracy" in weakness for weakness in analysis['weaknesses'])
        assert any("Poor performance" in weakness for weakness in analysis['weaknesses'])
        assert len(analysis['recommendations']) > 0
        
    def test_bias_detection_analysis(self):
        """Test bias detection in predictions."""
        biased_predictions = {
            'score_predictions': np.array([0.9, 0.8, 0.7, 0.85, 0.75]),  # Consistently high
            'targets': np.array([0, 1, 2, 0, 1])  # Should map to [0.2, 0.5, 0.8, 0.2, 0.5]
        }
        
        metrics = EvaluationMetrics(
            accuracy=0.8, precision=0.8, recall=0.8, f1_score=0.8,
            macro_f1=0.8, weighted_f1=0.8, mse=0.1, mae=0.08, r2=0.6,
            confusion_matrix=np.array([[2, 0, 0], [0, 2, 0], [0, 0, 1]]),
            classification_report={},
            per_class_precision=[0.8, 0.8, 0.8],
            per_class_recall=[0.8, 0.8, 0.8],
            per_class_f1=[0.8, 0.8, 0.8]
        )
        
        analysis = self.evaluator._analyze_performance(metrics, biased_predictions)
        
        # Should detect overprediction bias
        bias_weaknesses = [w for w in analysis['weaknesses'] if 'overpredict' in w.lower()]
        assert len(bias_weaknesses) > 0
        
        bias_recommendations = [r for r in analysis['recommendations'] if 'bias' in r.lower()]
        assert len(bias_recommendations) > 0
        
    def test_regression_performance_analysis(self):
        """Test analysis of regression performance."""
        good_regression_metrics = EvaluationMetrics(
            accuracy=0.8, precision=0.8, recall=0.8, f1_score=0.8,
            macro_f1=0.8, weighted_f1=0.8,
            mse=0.02, mae=0.01, r2=0.85,  # Good regression performance
            confusion_matrix=np.array([[8, 1, 1], [1, 8, 1], [1, 1, 8]]),
            classification_report={},
            per_class_precision=[0.8, 0.8, 0.8],
            per_class_recall=[0.8, 0.8, 0.8],
            per_class_f1=[0.8, 0.8, 0.8]
        )
        
        predictions = {'score_predictions': np.array([0.2, 0.5, 0.8]), 'targets': np.array([0, 1, 2])}
        
        analysis = self.evaluator._analyze_performance(good_regression_metrics, predictions)
        
        regression_strengths = [s for s in analysis['strengths'] if 'score prediction' in s.lower()]
        assert len(regression_strengths) > 0


class TestEnsembleEvaluatorInitialization:
    """Test EnsembleEvaluator initialization and setup."""
    
    def test_default_initialization(self):
        """Test default ensemble evaluator initialization."""
        evaluator = EnsembleEvaluator()
        
        assert evaluator.view_names == ['technical', 'linguistic', 'task', 'semantic', 'computational']
        assert len(evaluator.view_names) == 5
        
    def test_ensemble_evaluator_attributes(self):
        """Test that ensemble evaluator has required attributes."""
        evaluator = EnsembleEvaluator()
        
        assert hasattr(evaluator, 'view_names')
        assert hasattr(evaluator, 'evaluate_ensemble')
        assert hasattr(evaluator, '_compare_ensemble_to_views')
        assert hasattr(evaluator, '_analyze_view_contributions')


class TestEnsembleEvaluatorComprehensiveEvaluation:
    """Test comprehensive ensemble evaluation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = EnsembleEvaluator()
        
        # Create mock view predictions
        self.view_predictions = {}
        for view_name in self.evaluator.view_names:
            self.view_predictions[view_name] = {
                'score_predictions': np.random.uniform(0, 1, 100),
                'class_predictions': np.random.randint(0, 3, 100),
                'targets': np.random.randint(0, 3, 100)
            }
            
        # Create ensemble predictions
        self.ensemble_predictions = {
            'score_predictions': np.random.uniform(0, 1, 100),
            'class_predictions': np.random.randint(0, 3, 100),
            'targets': np.random.randint(0, 3, 100)
        }
        
        # Create mock weights
        self.weights = {name: 0.2 for name in self.evaluator.view_names}
        
    @patch('src.training.evaluation_framework.ViewEvaluator')
    def test_comprehensive_ensemble_evaluation(self, mock_view_evaluator_class):
        """Test comprehensive ensemble evaluation workflow."""
        # Setup mock view evaluators
        mock_view_evaluator = Mock()
        mock_metrics = Mock()
        mock_metrics.accuracy = 0.8
        mock_metrics.macro_f1 = 0.75
        mock_view_evaluator.evaluate.return_value = mock_metrics
        mock_view_evaluator_class.return_value = mock_view_evaluator
        
        result = self.evaluator.evaluate_ensemble(
            self.view_predictions,
            self.ensemble_predictions,
            self.weights
        )
        
        # Verify structure
        required_keys = ['ensemble_performance', 'individual_view_performance', 
                        'ensemble_vs_individual', 'view_contributions', 'overall_assessment']
        for key in required_keys:
            assert key in result
            
        # Verify ensemble performance section
        ensemble_perf = result['ensemble_performance']
        expected_metrics = ['accuracy', 'macro_f1', 'weighted_f1', 'mse', 'r2']
        for metric in expected_metrics:
            assert metric in ensemble_perf
            
        # Verify individual view performance
        individual_perf = result['individual_view_performance']
        for view_name in self.evaluator.view_names:
            assert view_name in individual_perf
            
    def test_ensemble_vs_individual_comparison(self):
        """Test comparison between ensemble and individual views."""
        # Create mock view evaluations
        mock_evaluations = {}
        for i, view_name in enumerate(self.evaluator.view_names):
            mock_metrics = Mock()
            mock_metrics.accuracy = 0.7 + i * 0.05  # Varying accuracies
            mock_metrics.macro_f1 = 0.65 + i * 0.05
            mock_evaluations[view_name] = {'metrics': mock_metrics}
            
        # Create mock ensemble metrics
        mock_ensemble_metrics = Mock()
        mock_ensemble_metrics.accuracy = 0.85  # Better than any individual
        mock_ensemble_metrics.macro_f1 = 0.82
        
        comparison = self.evaluator._compare_ensemble_to_views(
            mock_evaluations, mock_ensemble_metrics
        )
        
        # Verify comparison structure
        assert 'best_individual_view' in comparison
        assert 'improvement_over_best' in comparison
        assert 'improvement_over_average' in comparison
        
        # Verify best individual view identification
        best_view = comparison['best_individual_view']
        assert 'name' in best_view
        assert 'accuracy' in best_view
        
        # Verify improvement calculations
        accuracy_improvement = comparison['improvement_over_best']['accuracy']
        assert isinstance(accuracy_improvement, float)
        
    def test_view_contribution_analysis(self):
        """Test analysis of individual view contributions."""
        contribution_analysis = self.evaluator._analyze_view_contributions(
            self.view_predictions,
            self.ensemble_predictions,
            self.weights
        )
        
        # Verify structure
        expected_sections = ['correlation_with_ensemble', 'individual_importance', 'complementarity_analysis']
        for section in expected_sections:
            assert section in contribution_analysis
            
        # Verify correlations
        correlations = contribution_analysis['correlation_with_ensemble']
        for view_name in self.evaluator.view_names:
            assert view_name in correlations
            assert isinstance(correlations[view_name], float)
            assert -1 <= correlations[view_name] <= 1  # Valid correlation range
            
        # Verify importance weights
        if self.weights:
            importance = contribution_analysis['individual_importance']
            for view_name in self.evaluator.view_names:
                assert view_name in importance
                assert isinstance(importance[view_name], float)
                
    def test_overall_assessment_generation(self):
        """Test generation of overall ensemble assessment."""
        # Create mock data
        mock_ensemble_metrics = Mock()
        mock_ensemble_metrics.accuracy = 0.88
        mock_ensemble_metrics.r2 = 0.75
        
        mock_view_evaluations = {}
        for view_name in self.evaluator.view_names:
            mock_metrics = Mock()
            mock_metrics.accuracy = 0.8
            mock_view_evaluations[view_name] = {'metrics': mock_metrics}
            
        mock_comparison = {
            'improvement_over_best': {'accuracy': 0.08}
        }
        
        assessment = self.evaluator._generate_overall_assessment(
            mock_ensemble_metrics, mock_view_evaluations, mock_comparison
        )
        
        # Verify assessment structure
        required_keys = ['meets_target_accuracy', 'target_accuracy', 'actual_accuracy',
                        'performance_grade', 'strengths', 'areas_for_improvement', 'next_steps']
        for key in required_keys:
            assert key in assessment
            
        # Verify accuracy assessment
        assert assessment['meets_target_accuracy'] is True  # 0.88 >= 0.85
        assert assessment['actual_accuracy'] == 0.88
        
        # Verify performance grading
        assert "Good" in assessment['performance_grade'] or "Excellent" in assessment['performance_grade']
        
        # Verify strengths and recommendations
        assert isinstance(assessment['strengths'], list)
        assert isinstance(assessment['areas_for_improvement'], list)
        assert isinstance(assessment['next_steps'], list)


class TestEnsembleEvaluatorVisualization:
    """Test ensemble evaluation visualization functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = EnsembleEvaluator()
        
        # Create mock ensemble report
        self.ensemble_report = {
            'ensemble_performance': {
                'accuracy': 0.85,
                'macro_f1': 0.82,
                'r2': 0.75
            },
            'individual_view_performance': {
                'technical': {'accuracy': 0.80, 'macro_f1': 0.78, 'r2': 0.70},
                'linguistic': {'accuracy': 0.78, 'macro_f1': 0.75, 'r2': 0.68},
                'task': {'accuracy': 0.82, 'macro_f1': 0.79, 'r2': 0.72},
                'semantic': {'accuracy': 0.77, 'macro_f1': 0.74, 'r2': 0.65},
                'computational': {'accuracy': 0.81, 'macro_f1': 0.78, 'r2': 0.71}
            },
            'view_contributions': {
                'correlation_with_ensemble': {
                    'technical': 0.85,
                    'linguistic': 0.78,
                    'task': 0.82,
                    'semantic': 0.75,
                    'computational': 0.80
                }
            }
        }
        
    @patch('matplotlib.pyplot.show')
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.subplots')
    def test_ensemble_comparison_plotting(self, mock_subplots, mock_savefig, mock_show):
        """Test ensemble comparison visualization."""
        # Mock matplotlib components
        mock_fig = Mock()
        mock_axes = Mock()
        mock_subplots.return_value = (mock_fig, mock_axes)
        
        save_path = Path("test_ensemble_comparison.png")
        
        self.evaluator.plot_ensemble_comparison(self.ensemble_report, save_path)
        
        # Verify plotting functions were called
        mock_subplots.assert_called_once_with(2, 2, figsize=(15, 12))
        mock_savefig.assert_called_once_with(save_path, dpi=300, bbox_inches='tight')
        mock_show.assert_called_once()
        
    @patch('matplotlib.pyplot.show')
    @patch('matplotlib.pyplot.subplots')
    def test_plotting_without_save_path(self, mock_subplots, mock_show):
        """Test plotting without saving to file."""
        mock_fig = Mock()
        mock_axes = Mock()
        mock_subplots.return_value = (mock_fig, mock_axes)
        
        self.evaluator.plot_ensemble_comparison(self.ensemble_report)
        
        mock_show.assert_called_once()
        
    @patch('matplotlib.pyplot.subplots')
    def test_plotting_with_missing_data(self, mock_subplots):
        """Test plotting handles missing data gracefully."""
        incomplete_report = {
            'ensemble_performance': {'accuracy': 0.85},
            'individual_view_performance': {
                'technical': {'accuracy': 0.80}
            }
        }
        
        mock_fig = Mock()
        mock_axes = Mock()
        mock_subplots.return_value = (mock_fig, mock_axes)
        
        # Should not crash with incomplete data
        try:
            self.evaluator.plot_ensemble_comparison(incomplete_report)
        except Exception as e:
            # If it fails, should be due to expected data structure issues
            assert "key" in str(e).lower() or "index" in str(e).lower()


class TestEvaluationFrameworkIntegration:
    """Test integration scenarios and workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.view_evaluator = ViewEvaluator("technical")
        self.ensemble_evaluator = EnsembleEvaluator()
        
    def test_complete_evaluation_workflow(self):
        """Test complete evaluation workflow from individual views to ensemble."""
        # Step 1: Generate individual view predictions
        view_predictions = {}
        for view_name in ['technical', 'linguistic', 'task']:
            view_predictions[view_name] = {
                'score_predictions': np.random.uniform(0, 1, 50),
                'class_predictions': np.random.randint(0, 3, 50),
                'targets': np.random.randint(0, 3, 50)
            }
            
        # Step 2: Generate ensemble predictions
        ensemble_predictions = {
            'score_predictions': np.random.uniform(0, 1, 50),
            'class_predictions': np.random.randint(0, 3, 50),
            'targets': np.random.randint(0, 3, 50)
        }
        
        # Step 3: Evaluate individual views
        individual_results = {}
        for view_name, predictions in view_predictions.items():
            evaluator = ViewEvaluator(view_name)
            metrics = evaluator.evaluate(predictions)
            individual_results[view_name] = {
                'metrics': metrics,
                'evaluator': evaluator
            }
            
        # Step 4: Evaluate ensemble
        ensemble_report = self.ensemble_evaluator.evaluate_ensemble(
            view_predictions, ensemble_predictions
        )
        
        # Verify complete workflow
        assert len(individual_results) == 3
        for view_name in individual_results:
            assert isinstance(individual_results[view_name]['metrics'], EvaluationMetrics)
            
        assert isinstance(ensemble_report, dict)
        assert 'ensemble_performance' in ensemble_report
        assert 'overall_assessment' in ensemble_report
        
    def test_evaluation_consistency_across_runs(self):
        """Test that evaluation is consistent across multiple runs."""
        # Use same random seed for reproducibility
        np.random.seed(42)
        
        predictions = {
            'score_predictions': np.random.uniform(0, 1, 30),
            'class_predictions': np.random.randint(0, 3, 30),
            'targets': np.random.randint(0, 3, 30)
        }
        
        # Run evaluation twice
        metrics1 = self.view_evaluator.evaluate(predictions)
        metrics2 = self.view_evaluator.evaluate(predictions)
        
        # Results should be identical
        assert metrics1.accuracy == metrics2.accuracy
        assert metrics1.mse == metrics2.mse
        assert metrics1.r2 == metrics2.r2
        
    def test_cross_evaluator_compatibility(self):
        """Test compatibility between different evaluator instances."""
        technical_evaluator = ViewEvaluator("technical")
        linguistic_evaluator = ViewEvaluator("linguistic")
        
        # Same predictions should work with different evaluators
        predictions = {
            'score_predictions': np.array([0.8, 0.6, 0.3, 0.9]),
            'class_predictions': np.array([2, 1, 0, 2]),
            'targets': np.array([2, 1, 0, 2])
        }
        
        tech_metrics = technical_evaluator.evaluate(predictions)
        ling_metrics = linguistic_evaluator.evaluate(predictions)
        
        # Should produce valid metrics from both evaluators
        assert isinstance(tech_metrics, EvaluationMetrics)
        assert isinstance(ling_metrics, EvaluationMetrics)
        
        # Metrics should be identical (same data, same evaluation logic)
        assert tech_metrics.accuracy == ling_metrics.accuracy
        assert tech_metrics.mse == ling_metrics.mse


class TestEvaluationFrameworkErrorHandling:
    """Test error handling and edge cases."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = ViewEvaluator("technical")
        
    def test_empty_predictions_handling(self):
        """Test handling of empty prediction arrays."""
        empty_predictions = {
            'score_predictions': np.array([]),
            'class_predictions': np.array([]),
            'targets': np.array([])
        }
        
        try:
            metrics = self.evaluator.evaluate(empty_predictions)
            # If successful, should handle gracefully
            assert isinstance(metrics, EvaluationMetrics)
        except (ValueError, ZeroDivisionError) as e:
            # Expected for empty data
            assert "empty" in str(e).lower() or "zero" in str(e).lower()
            
    def test_invalid_score_ranges(self):
        """Test handling of invalid score ranges."""
        invalid_predictions = {
            'score_predictions': np.array([-0.5, 1.5, 2.0]),  # Outside [0,1] range
            'class_predictions': np.array([0, 1, 2]),
            'targets': np.array([0, 1, 2])
        }
        
        # Should handle gracefully (clipping or other normalization)
        try:
            metrics = self.evaluator.evaluate(invalid_predictions)
            assert isinstance(metrics, EvaluationMetrics)
        except Exception as e:
            # Or may raise appropriate validation errors
            assert isinstance(e, (ValueError, AssertionError))
            
    def test_mismatched_array_lengths(self):
        """Test handling of mismatched array lengths."""
        mismatched_predictions = {
            'score_predictions': np.array([0.8, 0.6]),
            'class_predictions': np.array([2, 1, 0]),  # Different length
            'targets': np.array([2, 1])
        }
        
        with pytest.raises((ValueError, IndexError)):
            self.evaluator.evaluate(mismatched_predictions)
            
    def test_invalid_class_indices(self):
        """Test handling of invalid class indices."""
        invalid_class_predictions = {
            'score_predictions': np.array([0.8, 0.6, 0.3]),
            'class_predictions': np.array([0, 5, 1]),  # Class 5 doesn't exist
            'targets': np.array([0, 1, 2])
        }
        
        # Should handle gracefully or raise appropriate error
        try:
            metrics = self.evaluator.evaluate(invalid_class_predictions)
            assert isinstance(metrics, EvaluationMetrics)
        except (ValueError, IndexError) as e:
            # Expected for invalid indices
            assert "index" in str(e).lower() or "class" in str(e).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])