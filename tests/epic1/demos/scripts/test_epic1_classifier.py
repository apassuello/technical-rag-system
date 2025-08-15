#!/usr/bin/env python3
"""
Epic 1 Classifier Testing Script

This script comprehensively tests the trained Epic 1 classifier on external test datasets.
It provides detailed performance analysis including:
- Individual view model performance
- Fusion layer performance 
- Complexity level classification accuracy
- Per-level performance breakdown
- Error analysis and diagnostics
- Visual performance reports

Usage:
    python test_epic1_classifier.py --test-dataset epic1_training_dataset_215_samples.json
    python test_epic1_classifier.py --test-dataset path/to/test.json --model-dir models/epic1
    python test_epic1_classifier.py --test-dataset test.json --detailed --export-results
"""

import json
import torch
import numpy as np
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    
try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False
from pathlib import Path
from datetime import datetime
import argparse
import logging
from typing import Dict, List, Tuple, Any
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score, 
    accuracy_score, classification_report, confusion_matrix,
    precision_recall_fscore_support
)
import joblib

# Import the predictor
import sys
sys.path.append('models/epic1')
from epic1_predictor import Epic1Predictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Epic1ClassifierTester:
    """Comprehensive tester for Epic 1 classifier system."""
    
    def __init__(self, model_dir: str = "models/epic1"):
        """
        Initialize the tester.
        
        Args:
            model_dir: Directory containing trained Epic 1 models
        """
        self.model_dir = Path(model_dir)
        self.predictor = Epic1Predictor(str(model_dir))
        
        # Results storage
        self.test_results = {}
        self.detailed_predictions = []
        self.performance_metrics = {}
        
        logger.info(f"Initialized Epic1ClassifierTester with models from: {model_dir}")
        logger.info(f"Using fusion method: {self.predictor.best_method}")
    
    def load_test_dataset(self, test_dataset_path: str) -> List[Dict]:
        """Load test dataset from JSON file."""
        test_path = Path(test_dataset_path)
        
        if not test_path.exists():
            raise FileNotFoundError(f"Test dataset not found: {test_dataset_path}")
        
        with open(test_path, 'r') as f:
            test_data = json.load(f)
        
        logger.info(f"Loaded test dataset: {len(test_data)} samples from {test_dataset_path}")
        
        # Validate dataset format
        required_fields = ['query_text', 'expected_complexity_score', 'expected_complexity_level']
        if test_data and not all(field in test_data[0] for field in required_fields):
            logger.warning("Test dataset may be missing required fields")
        
        return test_data
    
    def run_comprehensive_test(self, test_data: List[Dict]) -> Dict[str, Any]:
        """
        Run comprehensive testing on the dataset.
        
        Args:
            test_data: List of test samples
            
        Returns:
            Dictionary with comprehensive test results
        """
        logger.info("\\n" + "="*70)
        logger.info("RUNNING COMPREHENSIVE EPIC 1 CLASSIFIER TEST")
        logger.info("="*70)
        
        # Run predictions
        logger.info(f"Running predictions on {len(test_data)} test samples...")
        predictions = []
        
        for i, sample in enumerate(test_data):
            if i % 50 == 0:
                logger.info(f"  Processing sample {i}/{len(test_data)}")
            
            try:
                prediction = self.predictor.predict(sample['query_text'])
                
                # Add ground truth for comparison
                prediction['ground_truth'] = {
                    'complexity_score': sample['expected_complexity_score'],
                    'complexity_level': sample['expected_complexity_level'],
                    'view_scores': sample.get('view_scores', {})
                }
                
                predictions.append(prediction)
                
            except Exception as e:
                logger.error(f"Error predicting sample {i}: {e}")
                continue
        
        self.detailed_predictions = predictions
        logger.info(f"Completed predictions: {len(predictions)} successful")
        
        # Analyze results
        self._analyze_score_prediction_performance(predictions)
        self._analyze_level_classification_performance(predictions)
        self._analyze_view_model_performance(predictions)
        self._analyze_error_patterns(predictions)
        
        return self.test_results
    
    def _analyze_score_prediction_performance(self, predictions: List[Dict]):
        """Analyze regression performance (complexity score prediction)."""
        logger.info("\\n📊 Analyzing Score Prediction Performance...")
        
        predicted_scores = [p['complexity_score'] for p in predictions]
        ground_truth_scores = [p['ground_truth']['complexity_score'] for p in predictions]
        
        # Calculate metrics
        mae = mean_absolute_error(ground_truth_scores, predicted_scores)
        rmse = np.sqrt(mean_squared_error(ground_truth_scores, predicted_scores))
        r2 = r2_score(ground_truth_scores, predicted_scores)
        
        # Additional metrics
        mean_error = np.mean(np.array(predicted_scores) - np.array(ground_truth_scores))
        abs_errors = np.abs(np.array(predicted_scores) - np.array(ground_truth_scores))
        
        score_results = {
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'mean_error': mean_error,
            'median_abs_error': np.median(abs_errors),
            'max_abs_error': np.max(abs_errors),
            'std_error': np.std(abs_errors),
            'samples_within_0.1': np.sum(abs_errors < 0.1) / len(abs_errors) * 100,
            'samples_within_0.05': np.sum(abs_errors < 0.05) / len(abs_errors) * 100
        }
        
        self.test_results['score_prediction'] = score_results
        
        logger.info(f"  Mean Absolute Error: {mae:.4f}")
        logger.info(f"  Root Mean Square Error: {rmse:.4f}")
        logger.info(f"  R² Score: {r2:.4f}")
        logger.info(f"  Mean Bias: {mean_error:+.4f}")
        logger.info(f"  Samples within ±0.05: {score_results['samples_within_0.05']:.1f}%")
        logger.info(f"  Samples within ±0.10: {score_results['samples_within_0.1']:.1f}%")
    
    def _analyze_level_classification_performance(self, predictions: List[Dict]):
        """Analyze classification performance (complexity level prediction)."""
        logger.info("\\n🎯 Analyzing Level Classification Performance...")
        
        predicted_levels = [p['complexity_level'] for p in predictions]
        ground_truth_levels = [p['ground_truth']['complexity_level'] for p in predictions]
        
        # Overall accuracy
        accuracy = accuracy_score(ground_truth_levels, predicted_levels)
        
        # Detailed classification metrics
        precision, recall, f1, support = precision_recall_fscore_support(
            ground_truth_levels, predicted_levels, average=None, labels=['simple', 'medium', 'complex']
        )
        
        # Per-class metrics
        levels = ['simple', 'medium', 'complex']
        classification_results = {
            'overall_accuracy': accuracy,
            'per_class_metrics': {}
        }
        
        for i, level in enumerate(levels):
            classification_results['per_class_metrics'][level] = {
                'precision': precision[i] if i < len(precision) else 0.0,
                'recall': recall[i] if i < len(recall) else 0.0,
                'f1_score': f1[i] if i < len(f1) else 0.0,
                'support': int(support[i]) if i < len(support) else 0
            }
        
        # Confusion matrix
        cm = confusion_matrix(ground_truth_levels, predicted_levels, labels=levels)
        classification_results['confusion_matrix'] = cm.tolist()
        
        self.test_results['level_classification'] = classification_results
        
        logger.info(f"  Overall Accuracy: {accuracy:.3f} ({accuracy*100:.1f}%)")
        logger.info("  Per-Class Performance:")
        for level in levels:
            metrics = classification_results['per_class_metrics'][level]
            logger.info(f"    {level.capitalize():8} - Precision: {metrics['precision']:.3f}, "
                       f"Recall: {metrics['recall']:.3f}, F1: {metrics['f1_score']:.3f}, "
                       f"Support: {metrics['support']}")
        
        # Confusion Matrix Summary
        logger.info("  Confusion Matrix:")
        logger.info("    Predicted:  Simple  Medium  Complex")
        for i, true_level in enumerate(levels):
            row = "".join(f"{cm[i,j]:8}" for j in range(len(levels)))
            logger.info(f"    {true_level.capitalize():8}:{row}")
    
    def _analyze_view_model_performance(self, predictions: List[Dict]):
        """Analyze individual view model performance."""
        logger.info("\\n🔍 Analyzing Individual View Model Performance...")
        
        view_names = ['technical', 'linguistic', 'task', 'semantic', 'computational']
        view_results = {}
        
        for view_name in view_names:
            # Extract predictions and ground truth for this view
            predicted_view_scores = []
            ground_truth_view_scores = []
            
            for p in predictions:
                if view_name in p['view_scores'] and view_name in p['ground_truth'].get('view_scores', {}):
                    predicted_view_scores.append(p['view_scores'][view_name])
                    ground_truth_view_scores.append(p['ground_truth']['view_scores'][view_name])
            
            if predicted_view_scores:
                mae = mean_absolute_error(ground_truth_view_scores, predicted_view_scores)
                r2 = r2_score(ground_truth_view_scores, predicted_view_scores)
                correlation = np.corrcoef(ground_truth_view_scores, predicted_view_scores)[0,1]
                
                view_results[view_name] = {
                    'mae': mae,
                    'r2': r2,
                    'correlation': correlation,
                    'samples': len(predicted_view_scores)
                }
                
                logger.info(f"  {view_name.capitalize():12} - MAE: {mae:.4f}, R²: {r2:.4f}, "
                           f"Correlation: {correlation:.4f}, Samples: {len(predicted_view_scores)}")
            else:
                logger.warning(f"  {view_name.capitalize():12} - No ground truth available for comparison")
                view_results[view_name] = {'error': 'no_ground_truth'}
        
        self.test_results['view_models'] = view_results
    
    def _analyze_error_patterns(self, predictions: List[Dict]):
        """Analyze error patterns and edge cases."""
        logger.info("\\n⚠️  Analyzing Error Patterns...")
        
        # Score prediction errors
        predicted_scores = np.array([p['complexity_score'] for p in predictions])
        ground_truth_scores = np.array([p['ground_truth']['complexity_score'] for p in predictions])
        score_errors = predicted_scores - ground_truth_scores
        
        # Find worst predictions
        abs_errors = np.abs(score_errors)
        worst_indices = np.argsort(abs_errors)[-5:]  # Top 5 worst
        
        error_analysis = {
            'worst_score_predictions': [],
            'classification_errors': [],
            'systematic_biases': {}
        }
        
        # Worst score predictions
        for idx in reversed(worst_indices):
            sample = predictions[idx]
            error_analysis['worst_score_predictions'].append({
                'query': sample['query_text'][:100] + "..." if len(sample['query_text']) > 100 else sample['query_text'],
                'predicted_score': sample['complexity_score'],
                'ground_truth_score': sample['ground_truth']['complexity_score'],
                'absolute_error': abs_errors[idx],
                'predicted_level': sample['complexity_level'],
                'ground_truth_level': sample['ground_truth']['complexity_level']
            })
        
        # Classification errors
        for sample in predictions:
            if sample['complexity_level'] != sample['ground_truth']['complexity_level']:
                error_analysis['classification_errors'].append({
                    'query': sample['query_text'][:80] + "..." if len(sample['query_text']) > 80 else sample['query_text'],
                    'predicted_level': sample['complexity_level'],
                    'ground_truth_level': sample['ground_truth']['complexity_level'],
                    'predicted_score': sample['complexity_score'],
                    'ground_truth_score': sample['ground_truth']['complexity_score']
                })
        
        # Systematic biases by complexity level
        for level in ['simple', 'medium', 'complex']:
            level_indices = [i for i, p in enumerate(predictions) 
                           if p['ground_truth']['complexity_level'] == level]
            
            if level_indices:
                level_errors = score_errors[level_indices]
                error_analysis['systematic_biases'][level] = {
                    'mean_bias': float(np.mean(level_errors)),
                    'std_error': float(np.std(level_errors)),
                    'samples': len(level_indices)
                }
        
        self.test_results['error_analysis'] = error_analysis
        
        logger.info(f"  Classification errors: {len(error_analysis['classification_errors'])}")
        logger.info("  Systematic biases by level:")
        for level, bias_info in error_analysis['systematic_biases'].items():
            logger.info(f"    {level.capitalize():8} - Mean bias: {bias_info['mean_bias']:+.4f}, "
                       f"Std: {bias_info['std_error']:.4f}, Samples: {bias_info['samples']}")
        
        if error_analysis['worst_score_predictions']:
            logger.info("  Worst score predictions:")
            for i, worst in enumerate(error_analysis['worst_score_predictions'][:3], 1):
                logger.info(f"    {i}. Error: {worst['absolute_error']:.3f} - {worst['query']}")
    
    def generate_performance_report(self, output_file: str = None) -> str:
        """Generate comprehensive performance report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_file is None:
            output_file = f"epic1_test_report_{timestamp}.json"
        
        # Compile complete report
        report = {
            'test_info': {
                'timestamp': timestamp,
                'model_dir': str(self.model_dir),
                'fusion_method': self.predictor.best_method,
                'test_samples': len(self.detailed_predictions)
            },
            'performance_summary': {
                'score_prediction': self.test_results.get('score_prediction', {}),
                'level_classification': self.test_results.get('level_classification', {}),
                'view_models': self.test_results.get('view_models', {}),
                'error_analysis': self.test_results.get('error_analysis', {})
            },
            'detailed_predictions': self.detailed_predictions[:10] if len(self.detailed_predictions) > 10 else self.detailed_predictions,  # Sample for size
            'model_configuration': self._get_model_config()
        }
        
        # Save report
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"\\n📄 Performance report saved: {output_path}")
        return str(output_path)
    
    def _get_model_config(self) -> Dict[str, Any]:
        """Get model configuration information."""
        try:
            config_path = self.model_dir / "epic1_system_config.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load model config: {e}")
        
        return {"error": "config_not_available"}
    
    def create_visualizations(self, output_dir: str = "test_results"):
        """Create performance visualization plots."""
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("Matplotlib not available - skipping visualizations")
            return
            
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        logger.info(f"\\n📈 Creating visualizations in: {output_path}")
        
        if not self.detailed_predictions:
            logger.warning("No predictions available for visualization")
            return
        
        # Extract data for plotting
        predicted_scores = [p['complexity_score'] for p in self.detailed_predictions]
        ground_truth_scores = [p['ground_truth']['complexity_score'] for p in self.detailed_predictions]
        
        # 1. Score Prediction Scatter Plot
        plt.figure(figsize=(10, 8))
        plt.scatter(ground_truth_scores, predicted_scores, alpha=0.6)
        plt.plot([0, 1], [0, 1], 'r--', label='Perfect Prediction')
        plt.xlabel('Ground Truth Complexity Score')
        plt.ylabel('Predicted Complexity Score')
        plt.title('Epic 1 Classifier: Score Prediction Performance')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Add R² annotation
        r2 = self.test_results.get('score_prediction', {}).get('r2', 0)
        mae = self.test_results.get('score_prediction', {}).get('mae', 0)
        plt.text(0.05, 0.95, f'R² = {r2:.3f}\\nMAE = {mae:.3f}', 
                transform=plt.gca().transAxes, fontsize=12, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
        
        plt.tight_layout()
        plt.savefig(output_path / "score_prediction_scatter.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Classification Confusion Matrix
        if 'level_classification' in self.test_results:
            cm = np.array(self.test_results['level_classification']['confusion_matrix'])
            
            plt.figure(figsize=(8, 6))
            if SEABORN_AVAILABLE:
                sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                           xticklabels=['Simple', 'Medium', 'Complex'],
                           yticklabels=['Simple', 'Medium', 'Complex'])
            else:
                # Manual confusion matrix plot
                plt.imshow(cm, interpolation='nearest', cmap='Blues')
                plt.colorbar()
                for i in range(len(cm)):
                    for j in range(len(cm[i])):
                        plt.text(j, i, str(cm[i, j]), ha='center', va='center')
                plt.xticks(range(3), ['Simple', 'Medium', 'Complex'])
                plt.yticks(range(3), ['Simple', 'Medium', 'Complex'])
            
            plt.title('Epic 1 Classifier: Confusion Matrix')
            plt.ylabel('Ground Truth')
            plt.xlabel('Predicted')
            
            # Add accuracy
            accuracy = self.test_results['level_classification']['overall_accuracy']
            plt.text(1.5, -0.1, f'Overall Accuracy: {accuracy:.1%}', 
                    transform=plt.gca().transAxes, fontsize=12,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.7))
            
            plt.tight_layout()
            plt.savefig(output_path / "confusion_matrix.png", dpi=300, bbox_inches='tight')
            plt.close()
        
        # 3. Error Distribution
        errors = np.array(predicted_scores) - np.array(ground_truth_scores)
        
        plt.figure(figsize=(10, 6))
        plt.hist(errors, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        plt.axvline(0, color='red', linestyle='--', label='Perfect Prediction')
        plt.xlabel('Prediction Error (Predicted - Ground Truth)')
        plt.ylabel('Frequency')
        plt.title('Epic 1 Classifier: Score Prediction Error Distribution')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Add statistics
        mean_error = np.mean(errors)
        std_error = np.std(errors)
        plt.text(0.02, 0.98, f'Mean Error: {mean_error:+.4f}\\nStd Error: {std_error:.4f}', 
                transform=plt.gca().transAxes, fontsize=12, verticalalignment='top',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.7))
        
        plt.tight_layout()
        plt.savefig(output_path / "error_distribution.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("  ✅ Visualizations created:")
        logger.info("    - score_prediction_scatter.png")
        logger.info("    - confusion_matrix.png") 
        logger.info("    - error_distribution.png")
    
    def print_summary(self):
        """Print a concise summary of test results."""
        logger.info("\\n" + "="*70)
        logger.info("🏆 EPIC 1 CLASSIFIER TEST SUMMARY")
        logger.info("="*70)
        
        if 'score_prediction' in self.test_results:
            score_metrics = self.test_results['score_prediction']
            logger.info(f"📊 Score Prediction Performance:")
            logger.info(f"   MAE: {score_metrics['mae']:.4f} | R²: {score_metrics['r2']:.4f}")
            logger.info(f"   Within ±0.05: {score_metrics['samples_within_0.05']:.1f}% | Within ±0.10: {score_metrics['samples_within_0.1']:.1f}%")
        
        if 'level_classification' in self.test_results:
            class_metrics = self.test_results['level_classification']
            logger.info(f"🎯 Classification Performance:")
            logger.info(f"   Overall Accuracy: {class_metrics['overall_accuracy']:.1%}")
            
            for level, metrics in class_metrics['per_class_metrics'].items():
                logger.info(f"   {level.capitalize():8} - F1: {metrics['f1_score']:.3f} | Support: {metrics['support']}")
        
        logger.info(f"🔍 Test Dataset: {len(self.detailed_predictions)} samples")
        logger.info(f"🤖 Fusion Method: {self.predictor.best_method}")
        logger.info("="*70)


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description="Test Epic 1 Classifier on External Dataset")
    parser.add_argument('--test-dataset', required=True,
                       help='Path to test dataset JSON file')
    parser.add_argument('--model-dir', default='models/epic1',
                       help='Directory containing trained Epic 1 models')
    parser.add_argument('--output-dir', default='test_results',
                       help='Directory for output files')
    parser.add_argument('--detailed', action='store_true',
                       help='Generate detailed analysis and visualizations')
    parser.add_argument('--export-results', action='store_true',
                       help='Export detailed results to JSON')
    
    args = parser.parse_args()
    
    try:
        # Initialize tester
        tester = Epic1ClassifierTester(args.model_dir)
        
        # Load test data
        test_data = tester.load_test_dataset(args.test_dataset)
        
        # Run comprehensive test
        results = tester.run_comprehensive_test(test_data)
        
        # Print summary
        tester.print_summary()
        
        # Generate detailed outputs if requested
        if args.detailed:
            tester.create_visualizations(args.output_dir)
        
        if args.export_results:
            output_path = Path(args.output_dir)
            output_path.mkdir(exist_ok=True)
            report_file = output_path / f"epic1_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            tester.generate_performance_report(str(report_file))
        
        logger.info("\\n✅ Testing completed successfully!")
        
    except Exception as e:
        logger.error(f"\\n❌ Testing failed: {e}")
        raise


if __name__ == "__main__":
    main()