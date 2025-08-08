#!/usr/bin/env python3
"""
Epic 1 MetaClassifier Training

Trains the meta-classifier (fusion model) that combines the 5 view predictions
into a final complexity score, following the Epic 1 ML architecture specification.

Architecture from docs/architecture/EPIC1_ML_IMPLEMENTATION_PLAN.md:
- 15-dimensional meta-feature vector (3 features per view)
- LogisticRegression with L2 regularization (C=0.1)
- Confidence calibration for probabilistic outputs
"""

import json
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, List, Tuple, Optional
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.isotonic import IsotonicRegression
from sklearn.calibration import calibration_curve
from sklearn.metrics import mean_absolute_error, accuracy_score, log_loss
import joblib
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set seeds for reproducibility
SEED = 42
np.random.seed(SEED)
torch.manual_seed(SEED)


class SimpleViewModel(nn.Module):
    """Simple neural network for view complexity prediction (must match training)."""
    
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


class MetaClassifierTrainer:
    """Trains the MetaClassifier for Epic 1 multi-view fusion."""
    
    def __init__(self, dataset_path: str, view_models_dir: str = "models/epic1"):
        """
        Initialize MetaClassifier trainer.
        
        Args:
            dataset_path: Path to the training dataset
            view_models_dir: Directory containing trained view models
        """
        self.dataset_path = Path(dataset_path)
        self.view_models_dir = Path(view_models_dir)
        
        # Load dataset
        with open(self.dataset_path, 'r') as f:
            self.dataset = json.load(f)
        
        # Split data (same split as view training for consistency)
        self.train_data, temp_data = train_test_split(
            self.dataset, test_size=0.3, random_state=SEED,
            stratify=[s['expected_complexity_level'] for s in self.dataset]
        )
        self.val_data, self.test_data = train_test_split(
            temp_data, test_size=0.5, random_state=SEED,
            stratify=[s['expected_complexity_level'] for s in temp_data]
        )
        
        logger.info(f"Dataset split: Train={len(self.train_data)}, Val={len(self.val_data)}, Test={len(self.test_data)}")
        
        # View names
        self.view_names = ['technical', 'linguistic', 'task', 'semantic', 'computational']
        
        # Load trained view models
        self.view_models = self._load_view_models()
        
        # Initialize meta-classifier components
        self.meta_classifier = None
        self.feature_scaler = StandardScaler()
        self.confidence_calibrator = None
        
        # Store results
        self.training_history = {}
        self.evaluation_results = {}
    
    def _load_view_models(self) -> Dict[str, nn.Module]:
        """Load all trained view models."""
        models = {}
        
        for view_name in self.view_names:
            checkpoint_path = self.view_models_dir / f"{view_name}_model.pth"
            if checkpoint_path.exists():
                model = SimpleViewModel()
                checkpoint = torch.load(checkpoint_path)
                model.load_state_dict(checkpoint['model_state_dict'])
                model.eval()
                models[view_name] = model
                logger.info(f"Loaded {view_name} model")
            else:
                raise FileNotFoundError(f"Model not found: {checkpoint_path}")
        
        return models
    
    def _extract_simple_features(self, query: str) -> np.ndarray:
        """Extract simple features from query (must match view training)."""
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
    
    def _get_view_predictions(self, queries: List[str]) -> Dict[str, np.ndarray]:
        """Get predictions from all view models for a list of queries."""
        view_predictions = {view: [] for view in self.view_names}
        
        for query in queries:
            features = self._extract_simple_features(query)
            features_tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0)
            
            with torch.no_grad():
                for view_name, model in self.view_models.items():
                    score = model(features_tensor).item()
                    view_predictions[view_name].append(score)
        
        # Convert to numpy arrays
        for view in self.view_names:
            view_predictions[view] = np.array(view_predictions[view])
        
        return view_predictions
    
    def _build_meta_features(self, view_predictions: Dict[str, np.ndarray], 
                            confidence_scores: Optional[Dict[str, np.ndarray]] = None) -> np.ndarray:
        """
        Build 15-dimensional meta-feature vectors from view predictions.
        
        Following Epic 1 spec: 3 features per view (score, confidence, method)
        
        Args:
            view_predictions: Dictionary of view scores
            confidence_scores: Optional confidence scores per view
            
        Returns:
            Meta-feature matrix (n_samples, 15)
        """
        n_samples = len(view_predictions[self.view_names[0]])
        meta_features = np.zeros((n_samples, 15))
        
        for i, view_name in enumerate(self.view_names):
            base_idx = i * 3
            
            # Feature 1: Complexity score
            meta_features[:, base_idx] = view_predictions[view_name]
            
            # Feature 2: Confidence (for now, use score variance as proxy)
            # In real implementation, each view would provide its confidence
            if confidence_scores and view_name in confidence_scores:
                meta_features[:, base_idx + 1] = confidence_scores[view_name]
            else:
                # Estimate confidence based on score distance from 0.5 (uncertain)
                # Higher confidence when score is closer to 0 or 1
                scores = view_predictions[view_name]
                confidence = 1.0 - 2.0 * np.abs(scores - 0.5)
                meta_features[:, base_idx + 1] = confidence
            
            # Feature 3: Analysis method (0=algorithmic, 0.5=hybrid, 1=ml)
            # Since we're using ML models, set to 1.0
            meta_features[:, base_idx + 2] = 1.0
        
        return meta_features
    
    def train_meta_classifier(self):
        """Train the LogisticRegression meta-classifier."""
        logger.info("\n" + "="*60)
        logger.info("TRAINING META-CLASSIFIER")
        logger.info("="*60)
        
        # Get view predictions for training data
        train_queries = [s['query_text'] for s in self.train_data]
        train_view_predictions = self._get_view_predictions(train_queries)
        
        # Build meta-features
        X_train = self._build_meta_features(train_view_predictions)
        
        # Target values (final complexity scores)
        y_train = np.array([s['expected_complexity_score'] for s in self.train_data])
        
        # For classification, create discrete labels
        y_train_class = np.array([
            0 if score < 0.33 else 1 if score < 0.67 else 2 
            for score in y_train
        ])
        
        # Normalize features
        X_train_scaled = self.feature_scaler.fit_transform(X_train)
        
        # Train LogisticRegression as specified in Epic 1 docs
        logger.info("Training LogisticRegression with L2 regularization (C=0.1)...")
        self.meta_classifier = LogisticRegression(
            C=0.1,  # As specified in Epic 1 architecture
            penalty='l2',
            solver='lbfgs',
            max_iter=1000,
            multi_class='multinomial',
            random_state=SEED
        )
        
        self.meta_classifier.fit(X_train_scaled, y_train_class)
        
        # Get predicted probabilities for regression adaptation
        train_probs = self.meta_classifier.predict_proba(X_train_scaled)
        
        # Convert class probabilities to continuous scores
        # Weighted average: simple=0.2, medium=0.5, complex=0.8
        class_centers = np.array([0.2, 0.5, 0.8])
        train_scores = np.dot(train_probs, class_centers)
        
        # Calculate training metrics
        train_mae = mean_absolute_error(y_train, train_scores)
        train_acc = accuracy_score(y_train_class, self.meta_classifier.predict(X_train_scaled))
        
        logger.info(f"Training MAE: {train_mae:.4f}")
        logger.info(f"Training Accuracy: {train_acc:.2%}")
        
        # Validate on validation set
        val_queries = [s['query_text'] for s in self.val_data]
        val_view_predictions = self._get_view_predictions(val_queries)
        X_val = self._build_meta_features(val_view_predictions)
        X_val_scaled = self.feature_scaler.transform(X_val)
        
        y_val = np.array([s['expected_complexity_score'] for s in self.val_data])
        y_val_class = np.array([
            0 if score < 0.33 else 1 if score < 0.67 else 2 
            for score in y_val
        ])
        
        val_probs = self.meta_classifier.predict_proba(X_val_scaled)
        val_scores = np.dot(val_probs, class_centers)
        
        val_mae = mean_absolute_error(y_val, val_scores)
        val_acc = accuracy_score(y_val_class, self.meta_classifier.predict(X_val_scaled))
        
        logger.info(f"Validation MAE: {val_mae:.4f}")
        logger.info(f"Validation Accuracy: {val_acc:.2%}")
        
        # Train confidence calibrator
        self._train_confidence_calibrator(X_val_scaled, val_probs, y_val_class)
        
        # Store training history
        self.training_history = {
            'train_mae': train_mae,
            'train_acc': train_acc,
            'val_mae': val_mae,
            'val_acc': val_acc,
            'feature_importance': self._get_feature_importance()
        }
    
    def _train_confidence_calibrator(self, X_val: np.ndarray, val_probs: np.ndarray, y_val: np.ndarray):
        """Train isotonic regression for confidence calibration."""
        logger.info("\nTraining confidence calibrator...")
        
        # Get maximum probability as confidence
        confidences = np.max(val_probs, axis=1)
        
        # Check if predictions are correct
        predictions = np.argmax(val_probs, axis=1)
        accuracies = (predictions == y_val).astype(float)
        
        # Train isotonic regression
        self.confidence_calibrator = IsotonicRegression(out_of_bounds='clip')
        self.confidence_calibrator.fit(confidences, accuracies)
        
        # Evaluate calibration
        calibrated_confidences = self.confidence_calibrator.transform(confidences)
        
        logger.info(f"Confidence calibration - Mean confidence: {np.mean(calibrated_confidences):.3f}")
        logger.info(f"Confidence calibration - Mean accuracy: {np.mean(accuracies):.3f}")
    
    def _get_feature_importance(self) -> Dict[str, float]:
        """Extract feature importance from LogisticRegression coefficients."""
        importance = {}
        
        # Get coefficient magnitudes (average across classes)
        coef_magnitudes = np.abs(self.meta_classifier.coef_).mean(axis=0)
        
        for i, view_name in enumerate(self.view_names):
            base_idx = i * 3
            importance[f"{view_name}_score"] = coef_magnitudes[base_idx]
            importance[f"{view_name}_confidence"] = coef_magnitudes[base_idx + 1]
            importance[f"{view_name}_method"] = coef_magnitudes[base_idx + 2]
        
        # Normalize to sum to 1
        total = sum(importance.values())
        for key in importance:
            importance[key] = importance[key] / total
        
        return importance
    
    def evaluate_and_compare(self):
        """Evaluate MetaClassifier and compare with fixed weights."""
        logger.info("\n" + "="*60)
        logger.info("EVALUATING META-CLASSIFIER")
        logger.info("="*60)
        
        # Get test predictions
        test_queries = [s['query_text'] for s in self.test_data]
        test_view_predictions = self._get_view_predictions(test_queries)
        
        # MetaClassifier predictions
        X_test = self._build_meta_features(test_view_predictions)
        X_test_scaled = self.feature_scaler.transform(X_test)
        
        test_probs = self.meta_classifier.predict_proba(X_test_scaled)
        class_centers = np.array([0.2, 0.5, 0.8])
        meta_scores = np.dot(test_probs, class_centers)
        
        # Fixed weight predictions (current approach)
        fixed_weights = {
            'technical': 0.30,
            'linguistic': 0.15,
            'task': 0.25,
            'semantic': 0.15,
            'computational': 0.15
        }
        
        fixed_scores = np.zeros(len(test_queries))
        for view_name, weight in fixed_weights.items():
            fixed_scores += test_view_predictions[view_name] * weight
        
        # Ground truth
        y_test = np.array([s['expected_complexity_score'] for s in self.test_data])
        y_test_class = np.array([
            0 if score < 0.33 else 1 if score < 0.67 else 2 
            for score in y_test
        ])
        
        # Calculate metrics
        meta_mae = mean_absolute_error(y_test, meta_scores)
        fixed_mae = mean_absolute_error(y_test, fixed_scores)
        
        meta_class_pred = self.meta_classifier.predict(X_test_scaled)
        fixed_class_pred = np.array([
            0 if score < 0.33 else 1 if score < 0.67 else 2 
            for score in fixed_scores
        ])
        
        meta_acc = accuracy_score(y_test_class, meta_class_pred)
        fixed_acc = accuracy_score(y_test_class, fixed_class_pred)
        
        # Calculate confidence scores
        meta_confidences = np.max(test_probs, axis=1)
        if self.confidence_calibrator:
            meta_confidences = self.confidence_calibrator.transform(meta_confidences)
        
        # Results
        logger.info("\n" + "-"*40)
        logger.info("COMPARISON: MetaClassifier vs Fixed Weights")
        logger.info("-"*40)
        logger.info(f"MAE - MetaClassifier: {meta_mae:.4f}")
        logger.info(f"MAE - Fixed Weights: {fixed_mae:.4f}")
        logger.info(f"MAE Improvement: {(fixed_mae - meta_mae)/fixed_mae*100:.1f}%")
        logger.info(f"\nAccuracy - MetaClassifier: {meta_acc:.2%}")
        logger.info(f"Accuracy - Fixed Weights: {fixed_acc:.2%}")
        logger.info(f"Accuracy Improvement: {(meta_acc - fixed_acc)*100:.1f}%")
        logger.info(f"\nMean Confidence (calibrated): {np.mean(meta_confidences):.3f}")
        
        # Feature importance
        logger.info("\n" + "-"*40)
        logger.info("FEATURE IMPORTANCE (Top 5)")
        logger.info("-"*40)
        importance = self.training_history['feature_importance']
        sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]
        for feat, imp in sorted_features:
            logger.info(f"  {feat:25}: {imp:.3f}")
        
        self.evaluation_results = {
            'meta_classifier': {
                'mae': meta_mae,
                'accuracy': meta_acc,
                'mean_confidence': float(np.mean(meta_confidences))
            },
            'fixed_weights': {
                'mae': fixed_mae,
                'accuracy': fixed_acc
            },
            'improvement': {
                'mae_reduction': (fixed_mae - meta_mae) / fixed_mae,
                'accuracy_increase': meta_acc - fixed_acc
            }
        }
    
    def save_meta_classifier(self):
        """Save the trained MetaClassifier and associated components."""
        output_dir = Path("models/epic1")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save LogisticRegression model
        meta_classifier_path = output_dir / "meta_classifier.pkl"
        joblib.dump(self.meta_classifier, meta_classifier_path)
        logger.info(f"Saved MetaClassifier to: {meta_classifier_path}")
        
        # Save feature scaler
        scaler_path = output_dir / "meta_classifier_scaler.pkl"
        joblib.dump(self.feature_scaler, scaler_path)
        logger.info(f"Saved feature scaler to: {scaler_path}")
        
        # Save confidence calibrator
        if self.confidence_calibrator:
            calibrator_path = output_dir / "confidence_calibrator.pkl"
            joblib.dump(self.confidence_calibrator, calibrator_path)
            logger.info(f"Saved confidence calibrator to: {calibrator_path}")
        
        # Save training results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_path = Path(f"data/training/meta_classifier_results_{timestamp}.json")
        
        results = {
            'timestamp': timestamp,
            'training_history': self.training_history,
            'evaluation_results': self.evaluation_results,
            'model_paths': {
                'meta_classifier': str(meta_classifier_path),
                'scaler': str(scaler_path),
                'calibrator': str(calibrator_path) if self.confidence_calibrator else None
            }
        }
        
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved results to: {results_path}")


def main():
    """Train and evaluate the MetaClassifier."""
    # Find latest dataset
    data_dir = Path("data/training")
    dataset_files = list(data_dir.glob("epic1_dataset_*.json"))
    
    if not dataset_files:
        logger.error("No dataset files found!")
        return
    
    latest_dataset = max(dataset_files, key=lambda p: p.stat().st_mtime)
    logger.info(f"Using dataset: {latest_dataset}")
    
    # Initialize trainer
    trainer = MetaClassifierTrainer(latest_dataset)
    
    # Train MetaClassifier
    trainer.train_meta_classifier()
    
    # Evaluate and compare
    trainer.evaluate_and_compare()
    
    # Save everything
    trainer.save_meta_classifier()
    
    logger.info("\n" + "="*60)
    logger.info("META-CLASSIFIER TRAINING COMPLETE!")
    logger.info("="*60)


if __name__ == "__main__":
    main()