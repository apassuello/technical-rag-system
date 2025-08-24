#!/usr/bin/env python3
"""
Epic 1 Ground Truth Dataset Validation Framework

This module provides comprehensive validation of the ground truth dataset used
for Epic 1 training and accuracy measurement, ensuring data quality, consistency,
and reliability for the 99.5% accuracy validation claims.

Key Features:
1. Dataset Quality Validation
2. Label Consistency Checking  
3. Feature Distribution Analysis
4. Cross-Validation Framework
5. Statistical Validation Tests
"""

import pytest
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from scipy import stats
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GroundTruthValidator:
    """
    Comprehensive validation framework for Epic 1 ground truth dataset.
    
    This validator ensures the ground truth dataset used for Epic 1 accuracy
    claims is statistically sound, properly labeled, and suitable for
    machine learning validation.
    """
    
    def __init__(self, dataset_path: Path):
        """
        Initialize ground truth validator.
        
        Args:
            dataset_path: Path to the ground truth dataset JSON file
        """
        self.dataset_path = dataset_path
        self.dataset = self._load_and_validate_dataset()
        self.validation_results = {}
        
        # Statistical thresholds
        self.min_samples_per_class = 10
        self.max_class_imbalance_ratio = 5.0
        self.min_confidence_threshold = 0.6
        self.max_score_variance = 0.25
        
        logger.info(f"Initialized GroundTruthValidator with {len(self.dataset)} samples")
    
    def _load_and_validate_dataset(self) -> List[Dict[str, Any]]:
        """Load and perform basic validation of the dataset."""
        try:
            with open(self.dataset_path, 'r') as f:
                data = json.load(f)
            
            # Basic structure validation
            required_fields = [
                'query_text', 'expected_complexity_score', 'expected_complexity_level',
                'view_scores', 'confidence'
            ]
            
            valid_samples = []
            for i, sample in enumerate(data):
                if not all(field in sample for field in required_fields):
                    logger.warning(f"Sample {i} missing required fields: {sample.keys()}")
                    continue
                
                # Validate field types and ranges
                if not isinstance(sample['query_text'], str) or len(sample['query_text'].strip()) == 0:
                    logger.warning(f"Sample {i} has invalid query_text")
                    continue
                
                if not (0.0 <= sample['expected_complexity_score'] <= 1.0):
                    logger.warning(f"Sample {i} has invalid complexity_score: {sample['expected_complexity_score']}")
                    continue
                
                if sample['expected_complexity_level'] not in ['simple', 'medium', 'complex']:
                    logger.warning(f"Sample {i} has invalid complexity_level: {sample['expected_complexity_level']}")
                    continue
                
                if not isinstance(sample['view_scores'], dict):
                    logger.warning(f"Sample {i} has invalid view_scores format")
                    continue
                
                valid_samples.append(sample)
            
            logger.info(f"Loaded {len(valid_samples)}/{len(data)} valid samples")
            return valid_samples
            
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            return []
    
    def validate_dataset_quality(self) -> Dict[str, Any]:
        """
        Perform comprehensive dataset quality validation.
        
        Returns:
            Dictionary containing all quality metrics and validation results
        """
        logger.info("Starting comprehensive dataset quality validation")
        
        quality_results = {
            'sample_count': len(self.dataset),
            'basic_statistics': self._calculate_basic_statistics(),
            'class_distribution': self._analyze_class_distribution(),
            'label_consistency': self._validate_label_consistency(),
            'feature_quality': self._analyze_feature_quality(),
            'statistical_tests': self._perform_statistical_tests(),
            'cross_validation_results': self._perform_cross_validation(),
            'outlier_analysis': self._detect_outliers(),
            'correlation_analysis': self._analyze_correlations()
        }
        
        # Calculate overall quality score
        quality_results['overall_quality_score'] = self._calculate_quality_score(quality_results)
        quality_results['validation_timestamp'] = datetime.now().isoformat()
        
        self.validation_results = quality_results
        return quality_results
    
    def _calculate_basic_statistics(self) -> Dict[str, Any]:
        """Calculate basic dataset statistics."""
        if not self.dataset:
            return {}
        
        complexity_scores = [sample['expected_complexity_score'] for sample in self.dataset]
        confidence_scores = [sample['confidence'] for sample in self.dataset]
        query_lengths = [len(sample['query_text'].split()) for sample in self.dataset]
        
        return {
            'complexity_score_stats': {
                'mean': float(np.mean(complexity_scores)),
                'std': float(np.std(complexity_scores)),
                'min': float(np.min(complexity_scores)),
                'max': float(np.max(complexity_scores)),
                'median': float(np.median(complexity_scores))
            },
            'confidence_stats': {
                'mean': float(np.mean(confidence_scores)),
                'std': float(np.std(confidence_scores)),
                'min': float(np.min(confidence_scores)),
                'max': float(np.max(confidence_scores))
            },
            'query_length_stats': {
                'mean': float(np.mean(query_lengths)),
                'std': float(np.std(query_lengths)),
                'min': int(np.min(query_lengths)),
                'max': int(np.max(query_lengths))
            }
        }
    
    def _analyze_class_distribution(self) -> Dict[str, Any]:
        """Analyze distribution of complexity classes."""
        complexity_levels = [sample['expected_complexity_level'] for sample in self.dataset]
        unique, counts = np.unique(complexity_levels, return_counts=True)
        
        distribution = dict(zip(unique, counts.astype(int)))
        total_samples = len(complexity_levels)
        
        # Calculate class balance metrics
        max_class_size = max(counts)
        min_class_size = min(counts)
        imbalance_ratio = max_class_size / min_class_size if min_class_size > 0 else float('inf')
        
        # Check if minimum samples per class is met
        sufficient_samples = all(count >= self.min_samples_per_class for count in counts)
        
        return {
            'distribution': distribution,
            'percentages': {cls: (count / total_samples * 100) for cls, count in distribution.items()},
            'imbalance_ratio': float(imbalance_ratio),
            'sufficient_samples_per_class': sufficient_samples,
            'min_samples_per_class': int(min_class_size),
            'max_samples_per_class': int(max_class_size),
            'balanced': imbalance_ratio <= self.max_class_imbalance_ratio
        }
    
    def _validate_label_consistency(self) -> Dict[str, Any]:
        """Validate consistency between complexity scores and levels."""
        inconsistencies = []
        
        for i, sample in enumerate(self.dataset):
            score = sample['expected_complexity_score']
            level = sample['expected_complexity_level']
            
            # Define expected score ranges for each level
            expected_level = 'simple' if score < 0.35 else ('medium' if score < 0.70 else 'complex')
            
            if expected_level != level:
                inconsistencies.append({
                    'index': i,
                    'query': sample['query_text'][:100],
                    'score': score,
                    'labeled_level': level,
                    'expected_level': expected_level
                })
        
        consistency_rate = (len(self.dataset) - len(inconsistencies)) / len(self.dataset) if self.dataset else 0
        
        return {
            'consistency_rate': float(consistency_rate),
            'inconsistencies_count': len(inconsistencies),
            'inconsistencies': inconsistencies[:10],  # First 10 for review
            'consistent': consistency_rate >= 0.95  # 95% consistency threshold
        }
    
    def _analyze_feature_quality(self) -> Dict[str, Any]:
        """Analyze quality of view scores and other features."""
        if not self.dataset:
            return {}
        
        view_names = ['technical', 'linguistic', 'task', 'semantic', 'computational']
        view_analysis = {}
        
        for view_name in view_names:
            view_scores = []
            missing_count = 0
            
            for sample in self.dataset:
                if view_name in sample['view_scores']:
                    view_scores.append(sample['view_scores'][view_name])
                else:
                    missing_count += 1
            
            if view_scores:
                view_analysis[view_name] = {
                    'mean': float(np.mean(view_scores)),
                    'std': float(np.std(view_scores)),
                    'min': float(np.min(view_scores)),
                    'max': float(np.max(view_scores)),
                    'missing_count': missing_count,
                    'completeness': (len(view_scores) / len(self.dataset)) * 100
                }
        
        # Check for reasonable variance in view scores
        variance_analysis = {}
        for sample in self.dataset:
            if 'view_scores' in sample and isinstance(sample['view_scores'], dict):
                scores = list(sample['view_scores'].values())
                if len(scores) >= 2:
                    variance = np.var(scores)
                    variance_analysis[sample['query_text'][:50]] = variance
        
        avg_variance = np.mean(list(variance_analysis.values())) if variance_analysis else 0
        
        return {
            'view_analysis': view_analysis,
            'average_view_variance': float(avg_variance),
            'reasonable_variance': avg_variance <= self.max_score_variance,
            'high_variance_samples': len([v for v in variance_analysis.values() if v > self.max_score_variance])
        }
    
    def _perform_statistical_tests(self) -> Dict[str, Any]:
        """Perform statistical tests on the dataset."""
        if len(self.dataset) < 10:
            return {'insufficient_data': True}
        
        complexity_scores = [sample['expected_complexity_score'] for sample in self.dataset]
        confidence_scores = [sample['confidence'] for sample in self.dataset]
        
        # Test for normality
        complexity_normality = stats.shapiro(complexity_scores)
        confidence_normality = stats.shapiro(confidence_scores)
        
        # Test for correlation between complexity and confidence
        correlation, p_value = stats.pearsonr(complexity_scores, confidence_scores)
        
        # ANOVA test across complexity levels
        simple_scores = [s['expected_complexity_score'] for s in self.dataset if s['expected_complexity_level'] == 'simple']
        medium_scores = [s['expected_complexity_score'] for s in self.dataset if s['expected_complexity_level'] == 'medium']
        complex_scores = [s['expected_complexity_score'] for s in self.dataset if s['expected_complexity_level'] == 'complex']
        
        anova_result = None
        if len(simple_scores) > 1 and len(medium_scores) > 1 and len(complex_scores) > 1:
            anova_result = stats.f_oneway(simple_scores, medium_scores, complex_scores)
        
        return {
            'complexity_normality': {
                'statistic': float(complexity_normality.statistic),
                'p_value': float(complexity_normality.pvalue),
                'is_normal': complexity_normality.pvalue > 0.05
            },
            'confidence_normality': {
                'statistic': float(confidence_normality.statistic), 
                'p_value': float(confidence_normality.pvalue),
                'is_normal': confidence_normality.pvalue > 0.05
            },
            'complexity_confidence_correlation': {
                'correlation': float(correlation),
                'p_value': float(p_value),
                'significant': p_value < 0.05
            },
            'anova_across_levels': {
                'statistic': float(anova_result.statistic) if anova_result else None,
                'p_value': float(anova_result.pvalue) if anova_result else None,
                'significant_difference': anova_result.pvalue < 0.05 if anova_result else None
            }
        }
    
    def _perform_cross_validation(self) -> Dict[str, Any]:
        """Perform cross-validation to assess dataset reliability."""
        if len(self.dataset) < 20:
            return {'insufficient_data': True}
        
        # Prepare data for cross-validation
        X = []  # Features: view scores + query length
        y = []  # Target: complexity level
        
        for sample in self.dataset:
            if 'view_scores' in sample and isinstance(sample['view_scores'], dict):
                # Feature vector: view scores + query length + confidence
                features = [
                    sample['view_scores'].get('technical', 0.5),
                    sample['view_scores'].get('linguistic', 0.5),
                    sample['view_scores'].get('task', 0.5),
                    sample['view_scores'].get('semantic', 0.5),
                    sample['view_scores'].get('computational', 0.5),
                    len(sample['query_text'].split()) / 100.0,  # Normalized query length
                    sample['confidence']
                ]
                X.append(features)
                y.append(sample['expected_complexity_level'])
        
        if len(X) < 10:
            return {'insufficient_data': True}
        
        X = np.array(X)
        y = np.array(y)
        
        # Stratified K-fold cross-validation
        cv_results = []
        skf = StratifiedKFold(n_splits=min(5, len(np.unique(y))), shuffle=True, random_state=42)
        
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.linear_model import LogisticRegression
            
            models = {
                'RandomForest': RandomForestClassifier(n_estimators=50, random_state=42),
                'LogisticRegression': LogisticRegression(random_state=42, max_iter=1000)
            }
            
            for model_name, model in models.items():
                fold_accuracies = []
                
                for train_idx, val_idx in skf.split(X, y):
                    X_train, X_val = X[train_idx], X[val_idx]
                    y_train, y_val = y[train_idx], y[val_idx]
                    
                    model.fit(X_train, y_train)
                    predictions = model.predict(X_val)
                    accuracy = accuracy_score(y_val, predictions)
                    fold_accuracies.append(accuracy)
                
                cv_results.append({
                    'model': model_name,
                    'mean_accuracy': float(np.mean(fold_accuracies)),
                    'std_accuracy': float(np.std(fold_accuracies)),
                    'fold_accuracies': [float(acc) for acc in fold_accuracies]
                })
            
            return {
                'cross_validation_results': cv_results,
                'reliable_dataset': all(result['mean_accuracy'] > 0.6 for result in cv_results)
            }
            
        except ImportError:
            logger.warning("Scikit-learn not available for cross-validation")
            return {'sklearn_not_available': True}
    
    def _detect_outliers(self) -> Dict[str, Any]:
        """Detect outliers in the dataset."""
        complexity_scores = [sample['expected_complexity_score'] for sample in self.dataset]
        confidence_scores = [sample['confidence'] for sample in self.dataset]
        
        # IQR method for outlier detection
        def detect_outliers_iqr(data):
            Q1 = np.percentile(data, 25)
            Q3 = np.percentile(data, 75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            return [(i, val) for i, val in enumerate(data) if val < lower_bound or val > upper_bound]
        
        complexity_outliers = detect_outliers_iqr(complexity_scores)
        confidence_outliers = detect_outliers_iqr(confidence_scores)
        
        return {
            'complexity_outliers': len(complexity_outliers),
            'confidence_outliers': len(confidence_outliers),
            'total_outliers': len(set([idx for idx, _ in complexity_outliers + confidence_outliers])),
            'outlier_percentage': (len(set([idx for idx, _ in complexity_outliers + confidence_outliers])) / len(self.dataset) * 100) if self.dataset else 0,
            'acceptable_outlier_rate': (len(set([idx for idx, _ in complexity_outliers + confidence_outliers])) / len(self.dataset)) < 0.05 if self.dataset else True
        }
    
    def _analyze_correlations(self) -> Dict[str, Any]:
        """Analyze correlations between different features."""
        if len(self.dataset) < 10:
            return {'insufficient_data': True}
        
        # Prepare correlation matrix data
        features = []
        for sample in self.dataset:
            if 'view_scores' in sample and isinstance(sample['view_scores'], dict):
                row = [
                    sample['expected_complexity_score'],
                    sample['confidence'],
                    sample['view_scores'].get('technical', 0.5),
                    sample['view_scores'].get('linguistic', 0.5),
                    sample['view_scores'].get('task', 0.5),
                    sample['view_scores'].get('semantic', 0.5),
                    sample['view_scores'].get('computational', 0.5),
                    len(sample['query_text'].split())
                ]
                features.append(row)
        
        if len(features) < 10:
            return {'insufficient_data': True}
        
        feature_names = [
            'complexity_score', 'confidence', 'technical', 'linguistic', 
            'task', 'semantic', 'computational', 'query_length'
        ]
        
        df = pd.DataFrame(features, columns=feature_names)
        correlation_matrix = df.corr()
        
        # Find high correlations (potential redundancy)
        high_correlations = []
        for i, col1 in enumerate(feature_names):
            for j, col2 in enumerate(feature_names[i+1:], i+1):
                corr = correlation_matrix.iloc[i, j]
                if abs(corr) > 0.8 and col1 != col2:  # High correlation threshold
                    high_correlations.append({
                        'feature1': col1,
                        'feature2': col2,
                        'correlation': float(corr)
                    })
        
        return {
            'correlation_matrix': correlation_matrix.to_dict(),
            'high_correlations': high_correlations,
            'feature_redundancy': len(high_correlations) > 0
        }
    
    def _calculate_quality_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall dataset quality score (0-1 scale)."""
        quality_components = []
        
        # Sample count (0.1 weight)
        sample_count = results.get('sample_count', 0)
        sample_score = min(1.0, sample_count / 100.0)  # 100+ samples = full score
        quality_components.append(('sample_count', sample_score, 0.1))
        
        # Class balance (0.2 weight)
        class_dist = results.get('class_distribution', {})
        balance_score = 1.0 if class_dist.get('balanced', False) else 0.5
        quality_components.append(('class_balance', balance_score, 0.2))
        
        # Label consistency (0.3 weight)
        label_consistency = results.get('label_consistency', {})
        consistency_score = label_consistency.get('consistency_rate', 0.0)
        quality_components.append(('label_consistency', consistency_score, 0.3))
        
        # Feature quality (0.2 weight)
        feature_quality = results.get('feature_quality', {})
        feature_score = 1.0 if feature_quality.get('reasonable_variance', True) else 0.5
        quality_components.append(('feature_quality', feature_score, 0.2))
        
        # Cross-validation reliability (0.2 weight)
        cv_results = results.get('cross_validation_results', {})
        cv_score = 1.0 if cv_results.get('reliable_dataset', True) else 0.3
        quality_components.append(('cross_validation', cv_score, 0.2))
        
        # Calculate weighted average
        weighted_score = sum(score * weight for _, score, weight in quality_components)
        
        return float(weighted_score)
    
    def generate_validation_report(self) -> str:
        """Generate comprehensive validation report."""
        if not self.validation_results:
            self.validate_dataset_quality()
        
        results = self.validation_results
        
        report = []
        report.append("=" * 80)
        report.append("EPIC 1 GROUND TRUTH DATASET VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {results.get('validation_timestamp', 'N/A')}")
        report.append(f"Dataset: {self.dataset_path}")
        report.append(f"Sample Count: {results.get('sample_count', 0)}")
        report.append(f"Overall Quality Score: {results.get('overall_quality_score', 0):.3f}/1.000")
        report.append("")
        
        # Basic statistics
        basic_stats = results.get('basic_statistics', {})
        if basic_stats:
            report.append("BASIC STATISTICS:")
            complexity_stats = basic_stats.get('complexity_score_stats', {})
            report.append(f"  Complexity Score - Mean: {complexity_stats.get('mean', 0):.3f}, Std: {complexity_stats.get('std', 0):.3f}")
            confidence_stats = basic_stats.get('confidence_stats', {})
            report.append(f"  Confidence Score - Mean: {confidence_stats.get('mean', 0):.3f}, Std: {confidence_stats.get('std', 0):.3f}")
            query_stats = basic_stats.get('query_length_stats', {})
            report.append(f"  Query Length - Mean: {query_stats.get('mean', 0):.1f}, Range: {query_stats.get('min', 0)}-{query_stats.get('max', 0)}")
            report.append("")
        
        # Class distribution
        class_dist = results.get('class_distribution', {})
        if class_dist:
            report.append("CLASS DISTRIBUTION:")
            distribution = class_dist.get('distribution', {})
            percentages = class_dist.get('percentages', {})
            for cls in ['simple', 'medium', 'complex']:
                count = distribution.get(cls, 0)
                pct = percentages.get(cls, 0)
                report.append(f"  {cls.capitalize()}: {count} samples ({pct:.1f}%)")
            
            report.append(f"  Imbalance Ratio: {class_dist.get('imbalance_ratio', 0):.2f}")
            report.append(f"  Balanced: {'✓' if class_dist.get('balanced', False) else '✗'}")
            report.append("")
        
        # Label consistency
        label_consistency = results.get('label_consistency', {})
        if label_consistency:
            report.append("LABEL CONSISTENCY:")
            report.append(f"  Consistency Rate: {label_consistency.get('consistency_rate', 0):.3f}")
            report.append(f"  Inconsistencies: {label_consistency.get('inconsistencies_count', 0)}")
            report.append(f"  Consistent: {'✓' if label_consistency.get('consistent', False) else '✗'}")
            report.append("")
        
        # Cross-validation
        cv_results = results.get('cross_validation_results', {})
        if cv_results and not cv_results.get('insufficient_data', False):
            report.append("CROSS-VALIDATION RESULTS:")
            for result in cv_results.get('cross_validation_results', []):
                report.append(f"  {result['model']}: {result['mean_accuracy']:.3f} ± {result['std_accuracy']:.3f}")
            report.append(f"  Reliable Dataset: {'✓' if cv_results.get('reliable_dataset', False) else '✗'}")
            report.append("")
        
        # Quality assessment
        report.append("QUALITY ASSESSMENT:")
        quality_score = results.get('overall_quality_score', 0)
        if quality_score >= 0.9:
            report.append("  ✓ EXCELLENT - Dataset meets highest quality standards")
        elif quality_score >= 0.8:
            report.append("  ✓ GOOD - Dataset suitable for accuracy validation")
        elif quality_score >= 0.7:
            report.append("  ⚠ ACCEPTABLE - Dataset usable with minor concerns")
        else:
            report.append("  ✗ POOR - Dataset quality issues may affect validation reliability")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


@pytest.fixture
def ground_truth_validator():
    """Fixture providing GroundTruthValidator instance."""
    dataset_path = Path(__file__).parent.parent.parent / "data" / "training" / "epic1_training_dataset_679_samples.json"
    return GroundTruthValidator(dataset_path)


class TestGroundTruthDatasetValidation:
    """Test suite for ground truth dataset validation."""
    
    def test_dataset_loading_and_structure(self, ground_truth_validator):
        """
        Test that the dataset loads correctly and has proper structure.
        
        Validates basic dataset integrity and required field presence.
        """
        validator = ground_truth_validator
        
        # Check dataset was loaded
        assert len(validator.dataset) > 0, "No valid samples loaded from dataset"
        
        # Check required fields in first sample
        if validator.dataset:
            sample = validator.dataset[0]
            required_fields = [
                'query_text', 'expected_complexity_score', 'expected_complexity_level',
                'view_scores', 'confidence'
            ]
            
            for field in required_fields:
                assert field in sample, f"Required field '{field}' missing from sample"
            
            # Validate field types
            assert isinstance(sample['query_text'], str), "query_text must be string"
            assert isinstance(sample['expected_complexity_score'], (int, float)), "complexity_score must be numeric"
            assert sample['expected_complexity_level'] in ['simple', 'medium', 'complex'], "Invalid complexity_level"
            assert isinstance(sample['view_scores'], dict), "view_scores must be dictionary"
            assert isinstance(sample['confidence'], (int, float)), "confidence must be numeric"
        
        logger.info(f"Dataset structure validation passed - {len(validator.dataset)} samples")
    
    def test_dataset_quality_metrics(self, ground_truth_validator):
        """
        Test comprehensive dataset quality metrics.
        
        Validates data quality using statistical measures and consistency checks.
        """
        validator = ground_truth_validator
        quality_results = validator.validate_dataset_quality()
        
        # Assert basic quality requirements
        assert quality_results['sample_count'] >= 10, f"Insufficient samples: {quality_results['sample_count']}"
        
        # Class distribution requirements
        class_dist = quality_results.get('class_distribution', {})
        assert class_dist.get('sufficient_samples_per_class', False), "Insufficient samples per class"
        assert class_dist.get('imbalance_ratio', float('inf')) <= 10.0, "Excessive class imbalance"
        
        # Label consistency requirements
        label_consistency = quality_results.get('label_consistency', {})
        assert label_consistency.get('consistency_rate', 0) >= 0.90, "Low label consistency"
        
        # Overall quality score
        quality_score = quality_results.get('overall_quality_score', 0)
        assert quality_score >= 0.7, f"Dataset quality score too low: {quality_score:.3f}"
        
        logger.info(f"Dataset quality validation passed - Quality score: {quality_score:.3f}")
    
    def test_statistical_properties(self, ground_truth_validator):
        """
        Test statistical properties of the dataset.
        
        Validates statistical distributions and relationships in the data.
        """
        validator = ground_truth_validator
        quality_results = validator.validate_dataset_quality()
        
        # Statistical tests
        stat_tests = quality_results.get('statistical_tests', {})
        if not stat_tests.get('insufficient_data', True):
            # Check for reasonable correlation between complexity and confidence
            correlation = stat_tests.get('complexity_confidence_correlation', {})
            corr_value = correlation.get('correlation', 0)
            
            # Correlation should be positive but not too high (indicating diversity)
            assert -0.5 <= corr_value <= 0.8, f"Unreasonable complexity-confidence correlation: {corr_value}"
            
            # ANOVA should show significant difference between complexity levels
            anova = stat_tests.get('anova_across_levels', {})
            if anova and anova.get('p_value') is not None:
                assert anova.get('significant_difference', False), "No significant difference between complexity levels"
        
        # Basic statistics validation
        basic_stats = quality_results.get('basic_statistics', {})
        if basic_stats:
            complexity_stats = basic_stats.get('complexity_score_stats', {})
            
            # Complexity scores should cover reasonable range
            score_range = complexity_stats.get('max', 0) - complexity_stats.get('min', 1)
            assert score_range >= 0.5, f"Insufficient complexity score range: {score_range}"
            
            # Standard deviation should indicate reasonable variability
            score_std = complexity_stats.get('std', 0)
            assert 0.1 <= score_std <= 0.4, f"Unreasonable complexity score variance: {score_std}"
        
        logger.info("Statistical properties validation passed")
    
    def test_cross_validation_reliability(self, ground_truth_validator):
        """
        Test cross-validation reliability of the dataset.
        
        Validates that the dataset can be used reliably for machine learning validation.
        """
        validator = ground_truth_validator
        quality_results = validator.validate_dataset_quality()
        
        cv_results = quality_results.get('cross_validation_results', {})
        
        # Skip if insufficient data or sklearn not available
        if cv_results.get('insufficient_data', False) or cv_results.get('sklearn_not_available', False):
            pytest.skip("Insufficient data or sklearn not available for cross-validation")
        
        # Check cross-validation results
        cv_models = cv_results.get('cross_validation_results', [])
        assert len(cv_models) > 0, "No cross-validation results generated"
        
        # Check that at least one model achieves reasonable accuracy
        best_accuracy = max(model['mean_accuracy'] for model in cv_models)
        assert best_accuracy >= 0.6, f"Best cross-validation accuracy too low: {best_accuracy:.3f}"
        
        # Check dataset reliability
        assert cv_results.get('reliable_dataset', False), "Dataset failed reliability check"
        
        logger.info(f"Cross-validation reliability passed - Best accuracy: {best_accuracy:.3f}")
    
    def test_outlier_detection_and_handling(self, ground_truth_validator):
        """
        Test outlier detection and acceptable outlier rates.
        
        Validates that the dataset doesn't contain excessive outliers that could
        bias the accuracy validation.
        """
        validator = ground_truth_validator
        quality_results = validator.validate_dataset_quality()
        
        outlier_analysis = quality_results.get('outlier_analysis', {})
        
        # Check outlier rates
        outlier_percentage = outlier_analysis.get('outlier_percentage', 100)
        assert outlier_percentage <= 10.0, f"Excessive outlier rate: {outlier_percentage:.1f}%"
        
        # Check acceptable outlier rate flag
        assert outlier_analysis.get('acceptable_outlier_rate', False), "Unacceptable outlier rate detected"
        
        # Log outlier statistics
        complexity_outliers = outlier_analysis.get('complexity_outliers', 0)
        confidence_outliers = outlier_analysis.get('confidence_outliers', 0)
        
        logger.info(f"Outlier analysis passed - Complexity: {complexity_outliers}, Confidence: {confidence_outliers}, Total: {outlier_percentage:.1f}%")
    
    def test_view_scores_consistency(self, ground_truth_validator):
        """
        Test consistency and quality of view scores.
        
        Validates that the 5-view ML scores are consistent and reasonable.
        """
        validator = ground_truth_validator
        quality_results = validator.validate_dataset_quality()
        
        feature_quality = quality_results.get('feature_quality', {})
        view_analysis = feature_quality.get('view_analysis', {})
        
        expected_views = ['technical', 'linguistic', 'task', 'semantic', 'computational']
        
        for view_name in expected_views:
            view_stats = view_analysis.get(view_name, {})
            
            # Check completeness
            completeness = view_stats.get('completeness', 0)
            assert completeness >= 90.0, f"Low completeness for {view_name} view: {completeness:.1f}%"
            
            # Check score range
            min_score = view_stats.get('min', 1)
            max_score = view_stats.get('max', 0)
            score_range = max_score - min_score
            assert score_range >= 0.3, f"Insufficient score range for {view_name} view: {score_range}"
            
            # Check reasonable mean
            mean_score = view_stats.get('mean', -1)
            assert 0.0 <= mean_score <= 1.0, f"Invalid mean score for {view_name} view: {mean_score}"
        
        # Check overall view variance is reasonable
        avg_variance = feature_quality.get('average_view_variance', 1.0)
        assert feature_quality.get('reasonable_variance', False), f"Unreasonable view variance: {avg_variance}"
        
        logger.info("View scores consistency validation passed")
    
    def test_generate_validation_report(self, ground_truth_validator):
        """
        Test generation of comprehensive validation report.
        
        Validates that a detailed validation report can be generated with
        all quality metrics and recommendations.
        """
        validator = ground_truth_validator
        
        # Generate validation report
        report = validator.generate_validation_report()
        
        # Basic report checks
        assert len(report) > 100, "Validation report too short"
        assert "EPIC 1 GROUND TRUTH DATASET VALIDATION REPORT" in report, "Missing report header"
        assert "Overall Quality Score:" in report, "Missing quality score"
        assert "QUALITY ASSESSMENT:" in report, "Missing quality assessment"
        
        # Check for key sections
        required_sections = [
            "BASIC STATISTICS:",
            "CLASS DISTRIBUTION:",
            "LABEL CONSISTENCY:",
            "QUALITY ASSESSMENT:"
        ]
        
        for section in required_sections:
            assert section in report, f"Missing report section: {section}"
        
        logger.info("Validation report generation passed")
        
        # Print report for manual review
        print("\n" + report)


@pytest.mark.integration
def test_ground_truth_dataset_comprehensive_validation():
    """
    Comprehensive validation test that runs all validation checks
    and provides final assessment of dataset quality for Epic 1 accuracy claims.
    """
    dataset_path = Path(__file__).parent.parent.parent / "data" / "training" / "epic1_training_dataset_679_samples.json"
    
    if not dataset_path.exists():
        pytest.skip(f"Dataset not found at {dataset_path}")
    
    validator = GroundTruthValidator(dataset_path)
    quality_results = validator.validate_dataset_quality()
    
    # Generate and save comprehensive report
    report = validator.generate_validation_report()
    report_path = Path('/tmp/epic1_ground_truth_validation_report.txt')
    with open(report_path, 'w') as f:
        f.write(report)
    
    # Final validation assertions
    overall_quality = quality_results.get('overall_quality_score', 0)
    sample_count = quality_results.get('sample_count', 0)
    
    # Create final assessment
    assessment = {
        'dataset_path': str(dataset_path),
        'sample_count': sample_count,
        'overall_quality_score': overall_quality,
        'suitable_for_accuracy_validation': overall_quality >= 0.7,
        'validation_timestamp': datetime.now().isoformat(),
        'detailed_report_path': str(report_path)
    }
    
    # Save assessment
    assessment_path = Path('/tmp/epic1_dataset_assessment.json')
    with open(assessment_path, 'w') as f:
        json.dump(assessment, f, indent=2)
    
    # Final assertions
    assert sample_count >= 50, f"Insufficient samples for reliable validation: {sample_count}"
    assert overall_quality >= 0.7, f"Dataset quality too low for accuracy validation: {overall_quality:.3f}"
    
    logger.info(f"Ground truth dataset comprehensive validation completed")
    logger.info(f"Quality Score: {overall_quality:.3f}/1.000")
    logger.info(f"Sample Count: {sample_count}")
    logger.info(f"Suitable for accuracy validation: {assessment['suitable_for_accuracy_validation']}")
    logger.info(f"Report saved to: {report_path}")
    
    return assessment


if __name__ == "__main__":
    # Run comprehensive validation
    assessment = test_ground_truth_dataset_comprehensive_validation()
    
    print("\n" + "="*80)
    print("EPIC 1 GROUND TRUTH DATASET VALIDATION SUMMARY")
    print("="*80)
    print(f"Sample Count: {assessment['sample_count']}")
    print(f"Quality Score: {assessment['overall_quality_score']:.3f}/1.000")
    print(f"Suitable for Validation: {'✓ YES' if assessment['suitable_for_accuracy_validation'] else '✗ NO'}")
    print(f"Report: {assessment['detailed_report_path']}")
    print("="*80)