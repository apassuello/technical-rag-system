#!/usr/bin/env python3
"""
Epic 1 Fusion Layer Training

This script trains the meta-classifier/fusion layer that combines predictions
from all 5 trained view models to produce the final complexity score and level.

Architecture:
- Load 5 pre-trained view models (technical, linguistic, task, semantic, computational)
- Extract predictions from all views for the training dataset
- Train fusion models that combine view predictions → final complexity score & level
- Support multiple fusion strategies: weighted average, neural fusion, ensemble
"""

import json
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, List, Tuple, Optional
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, classification_report
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib

# Import view model architecture
from train_epic1_models import SimpleViewModel, SimpleViewDataset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set seeds for reproducibility
SEED = 42
np.random.seed(SEED)
torch.manual_seed(SEED)


class NeuralFusionModel(nn.Module):
    """Neural network for fusing view predictions."""
    
    def __init__(self, input_dim=5, hidden_dim=64):
        super().__init__()
        
        # Input: 5 view predictions
        # Output: final complexity score (regression) + level (classification)
        
        # Shared feature extraction
        self.shared_layers = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(0.3),
            
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim // 2),
            nn.Dropout(0.2)
        )
        
        # Regression head (complexity score 0-1)
        self.regression_head = nn.Sequential(
            nn.Linear(hidden_dim // 2, hidden_dim // 4),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim // 4, 1),
            nn.Sigmoid()
        )
        
        # Classification head (simple/medium/complex)
        self.classification_head = nn.Sequential(
            nn.Linear(hidden_dim // 2, hidden_dim // 4),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim // 4, 3),  # 3 complexity levels
            nn.Softmax(dim=1)
        )
    
    def forward(self, view_predictions):
        """
        Forward pass.
        
        Args:
            view_predictions: [batch_size, 5] view model outputs
            
        Returns:
            Tuple of (regression_output, classification_output)
        """
        shared_features = self.shared_layers(view_predictions)
        
        regression_output = self.regression_head(shared_features).squeeze()
        classification_output = self.classification_head(shared_features)
        
        return regression_output, classification_output


class Epic1FusionTrainer:
    """Trainer for Epic 1 fusion layer."""
    
    def __init__(self, dataset_path: str, view_models_dir: str = "models/epic1"):
        """
        Initialize fusion trainer.
        
        Args:
            dataset_path: Path to the training dataset (same one used for view training)
            view_models_dir: Directory containing trained view models
        """
        self.dataset_path = Path(dataset_path)
        self.view_models_dir = Path(view_models_dir)
        self.fusion_models_dir = self.view_models_dir / "fusion"
        self.fusion_models_dir.mkdir(exist_ok=True)
        
        # Load dataset
        with open(self.dataset_path, 'r') as f:
            self.dataset = json.load(f)
        
        # Split dataset (same split as view training for consistency)
        self.train_data, temp_data = train_test_split(
            self.dataset, test_size=0.3, random_state=SEED, 
            stratify=[s['expected_complexity_level'] for s in self.dataset]
        )
        self.val_data, self.test_data = train_test_split(
            temp_data, test_size=0.5, random_state=SEED,
            stratify=[s['expected_complexity_level'] for s in temp_data]
        )
        
        logger.info(f"Fusion training dataset split: Train={len(self.train_data)}, Val={len(self.val_data)}, Test={len(self.test_data)}")
        
        # View names
        self.view_names = ['technical', 'linguistic', 'task', 'semantic', 'computational']
        
        # Load pre-trained view models
        self._load_view_models()
        
        # Results storage
        self.fusion_results = {}
    
    def _load_view_models(self):
        """Load all pre-trained view models."""
        logger.info("Loading pre-trained view models...")
        
        self.view_models = {}
        for view_name in self.view_names:
            model_path = self.view_models_dir / f"{view_name}_model.pth"
            
            if model_path.exists():
                model = SimpleViewModel()
                checkpoint = torch.load(model_path)
                model.load_state_dict(checkpoint['model_state_dict'])
                model.eval()
                
                self.view_models[view_name] = model
                val_mae = checkpoint.get('val_mae', 'unknown')
                logger.info(f"  Loaded {view_name} model (Val MAE: {val_mae})")
            else:
                raise FileNotFoundError(f"View model not found: {model_path}")
        
        logger.info(f"Successfully loaded {len(self.view_models)} view models")
    
    def _extract_view_predictions(self, data: List[Dict]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Extract predictions from all view models for the given data.
        
        Args:
            data: List of training samples
            
        Returns:
            Tuple of (view_predictions, complexity_scores, complexity_levels)
        """
        logger.info(f"Extracting view predictions for {len(data)} samples...")
        
        view_predictions = []
        complexity_scores = []
        complexity_levels = []
        
        # Level mapping for classification
        level_mapping = {'simple': 0, 'medium': 1, 'complex': 2}
        
        with torch.no_grad():
            for sample in data:
                # Get view predictions
                sample_view_preds = []
                
                for view_name in self.view_names:
                    # Create dataset for this sample and view
                    view_dataset = SimpleViewDataset([sample], view_name)
                    features = torch.tensor(view_dataset.features[0], dtype=torch.float32)
                    
                    # Get prediction from view model
                    view_model = self.view_models[view_name]
                    prediction = view_model(features).item()
                    sample_view_preds.append(prediction)
                
                view_predictions.append(sample_view_preds)
                
                # Get ground truth
                complexity_scores.append(sample['expected_complexity_score'])
                complexity_levels.append(level_mapping[sample['expected_complexity_level']])
        
        return (
            np.array(view_predictions, dtype=np.float32),
            np.array(complexity_scores, dtype=np.float32),
            np.array(complexity_levels, dtype=int)
        )
    
    def train_weighted_average_fusion(self):
        """Train simple weighted average fusion."""
        logger.info("\\nTraining Weighted Average Fusion...")
        
        # Extract training predictions
        train_view_preds, train_scores, train_levels = self._extract_view_predictions(self.train_data)
        val_view_preds, val_scores, val_levels = self._extract_view_predictions(self.val_data)
        
        # Learn optimal weights using linear regression (constrained to sum=1)
        from scipy.optimize import minimize
        
        def objective(weights):
            # Ensure weights sum to 1 and are positive
            if np.sum(weights) != 1.0 or np.any(weights < 0):
                return 1e6
            
            weighted_preds = np.dot(train_view_preds, weights)
            return mean_squared_error(train_scores, weighted_preds)
        
        # Initial guess: equal weights
        initial_weights = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
        
        # Constraints: weights sum to 1, all positive
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
        bounds = [(0.0, 1.0) for _ in range(5)]
        
        result = minimize(objective, initial_weights, method='SLSQP', 
                         bounds=bounds, constraints=constraints)
        
        optimal_weights = result.x
        
        # Validate on validation set
        val_weighted_preds = np.dot(val_view_preds, optimal_weights)
        val_mae = mean_absolute_error(val_scores, val_weighted_preds)
        val_r2 = r2_score(val_scores, val_weighted_preds)
        
        # Classification (using thresholds)
        val_pred_levels = np.where(val_weighted_preds < 0.35, 0, 
                                  np.where(val_weighted_preds < 0.70, 1, 2))
        val_accuracy = accuracy_score(val_levels, val_pred_levels)
        
        logger.info(f"  Optimal weights: {dict(zip(self.view_names, optimal_weights))}")
        logger.info(f"  Val MAE: {val_mae:.4f}, R²: {val_r2:.4f}, Accuracy: {val_accuracy:.3f}")
        
        # Save model
        fusion_model = {
            'type': 'weighted_average',
            'weights': optimal_weights.tolist(),
            'view_names': self.view_names,
            'thresholds': [0.35, 0.70],  # simple/medium/complex thresholds
            'val_mae': val_mae,
            'val_r2': val_r2,
            'val_accuracy': val_accuracy
        }
        
        model_path = self.fusion_models_dir / "weighted_average_fusion.json"
        with open(model_path, 'w') as f:
            json.dump(fusion_model, f, indent=2)
        
        self.fusion_results['weighted_average'] = fusion_model
        logger.info(f"  Saved to: {model_path}")
    
    def train_neural_fusion(self, epochs=50):
        """Train neural fusion model."""
        logger.info(f"\\nTraining Neural Fusion Model ({epochs} epochs)...")
        
        # Extract predictions
        train_view_preds, train_scores, train_levels = self._extract_view_predictions(self.train_data)
        val_view_preds, val_scores, val_levels = self._extract_view_predictions(self.val_data)
        
        # Convert to tensors
        train_view_tensor = torch.tensor(train_view_preds, dtype=torch.float32)
        train_score_tensor = torch.tensor(train_scores, dtype=torch.float32)
        train_level_tensor = torch.tensor(train_levels, dtype=torch.long)
        
        val_view_tensor = torch.tensor(val_view_preds, dtype=torch.float32)
        val_score_tensor = torch.tensor(val_scores, dtype=torch.float32)
        val_level_tensor = torch.tensor(val_levels, dtype=torch.long)
        
        # Create model
        model = NeuralFusionModel(input_dim=5)
        optimizer = optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.01)
        
        # Loss functions
        regression_criterion = nn.MSELoss()
        classification_criterion = nn.CrossEntropyLoss()
        
        # Training loop
        best_combined_loss = float('inf')
        patience = 15
        patience_counter = 0
        
        for epoch in range(epochs):
            model.train()
            
            # Forward pass
            reg_pred, cls_pred = model(train_view_tensor)
            
            # Calculate losses
            reg_loss = regression_criterion(reg_pred, train_score_tensor)
            cls_loss = classification_criterion(cls_pred, train_level_tensor)
            combined_loss = reg_loss + 0.5 * cls_loss  # Weight classification lower
            
            # Backward pass
            optimizer.zero_grad()
            combined_loss.backward()
            optimizer.step()
            
            # Validation
            if epoch % 5 == 0:
                model.eval()
                with torch.no_grad():
                    val_reg_pred, val_cls_pred = model(val_view_tensor)
                    val_reg_loss = regression_criterion(val_reg_pred, val_score_tensor)
                    val_cls_loss = classification_criterion(val_cls_pred, val_level_tensor)
                    val_combined_loss = val_reg_loss + 0.5 * val_cls_loss
                    
                    val_mae = mean_absolute_error(val_score_tensor.numpy(), val_reg_pred.numpy())
                    val_cls_pred_labels = torch.argmax(val_cls_pred, dim=1)
                    val_accuracy = accuracy_score(val_level_tensor.numpy(), val_cls_pred_labels.numpy())
                    
                    logger.info(f"  Epoch {epoch}: Train Loss={combined_loss:.4f}, Val Loss={val_combined_loss:.4f}, "
                               f"Val MAE={val_mae:.4f}, Val Acc={val_accuracy:.3f}")
                    
                    # Early stopping
                    if val_combined_loss < best_combined_loss:
                        best_combined_loss = val_combined_loss
                        patience_counter = 0
                        
                        # Save best model
                        torch.save({
                            'model_state_dict': model.state_dict(),
                            'optimizer_state_dict': optimizer.state_dict(),
                            'epoch': epoch,
                            'val_combined_loss': val_combined_loss,
                            'val_mae': val_mae,
                            'val_accuracy': val_accuracy
                        }, self.fusion_models_dir / "neural_fusion_model.pth")
                        
                    else:
                        patience_counter += 1
                        if patience_counter >= patience:
                            logger.info(f"  Early stopping at epoch {epoch}")
                            break
        
        # Load best model for final evaluation
        checkpoint = torch.load(self.fusion_models_dir / "neural_fusion_model.pth")
        model.load_state_dict(checkpoint['model_state_dict'])
        
        self.fusion_results['neural'] = {
            'type': 'neural_fusion',
            'model_path': str(self.fusion_models_dir / "neural_fusion_model.pth"),
            'val_mae': checkpoint['val_mae'],
            'val_accuracy': checkpoint['val_accuracy'],
            'val_combined_loss': checkpoint['val_combined_loss']
        }
        
        logger.info(f"  Neural fusion trained. Best Val MAE: {checkpoint['val_mae']:.4f}, Accuracy: {checkpoint['val_accuracy']:.3f}")
    
    def train_ensemble_fusion(self):
        """Train ensemble-based fusion using Random Forest."""
        logger.info("\\nTraining Ensemble Fusion (Random Forest)...")
        
        # Extract predictions
        train_view_preds, train_scores, train_levels = self._extract_view_predictions(self.train_data)
        val_view_preds, val_scores, val_levels = self._extract_view_predictions(self.val_data)
        
        # Scale features
        scaler = StandardScaler()
        train_view_preds_scaled = scaler.fit_transform(train_view_preds)
        val_view_preds_scaled = scaler.transform(val_view_preds)
        
        # Train regression model (complexity score)
        reg_model = RandomForestRegressor(n_estimators=100, random_state=SEED, n_jobs=-1)
        reg_model.fit(train_view_preds_scaled, train_scores)
        
        # Train classification model (complexity level)
        cls_model = RandomForestClassifier(n_estimators=100, random_state=SEED, n_jobs=-1)
        cls_model.fit(train_view_preds_scaled, train_levels)
        
        # Validate
        val_score_preds = reg_model.predict(val_view_preds_scaled)
        val_level_preds = cls_model.predict(val_view_preds_scaled)
        
        val_mae = mean_absolute_error(val_scores, val_score_preds)
        val_r2 = r2_score(val_scores, val_score_preds)
        val_accuracy = accuracy_score(val_levels, val_level_preds)
        
        # Feature importance
        feature_importance = dict(zip(self.view_names, reg_model.feature_importances_))
        
        logger.info(f"  Feature importance: {feature_importance}")
        logger.info(f"  Val MAE: {val_mae:.4f}, R²: {val_r2:.4f}, Accuracy: {val_accuracy:.3f}")
        
        # Save models
        joblib.dump(reg_model, self.fusion_models_dir / "ensemble_regression_model.pkl")
        joblib.dump(cls_model, self.fusion_models_dir / "ensemble_classification_model.pkl")
        joblib.dump(scaler, self.fusion_models_dir / "ensemble_scaler.pkl")
        
        self.fusion_results['ensemble'] = {
            'type': 'ensemble_fusion',
            'regression_model_path': str(self.fusion_models_dir / "ensemble_regression_model.pkl"),
            'classification_model_path': str(self.fusion_models_dir / "ensemble_classification_model.pkl"),
            'scaler_path': str(self.fusion_models_dir / "ensemble_scaler.pkl"),
            'feature_importance': feature_importance,
            'val_mae': val_mae,
            'val_r2': val_r2,
            'val_accuracy': val_accuracy
        }
        
        logger.info(f"  Ensemble models saved to: {self.fusion_models_dir}")
    
    def evaluate_all_fusion_methods(self):
        """Evaluate all fusion methods on test set."""
        logger.info("\\n" + "="*70)
        logger.info("EVALUATING ALL FUSION METHODS ON TEST SET")
        logger.info("="*70)
        
        # Extract test predictions
        test_view_preds, test_scores, test_levels = self._extract_view_predictions(self.test_data)
        
        evaluation_results = {}
        
        # 1. Weighted Average
        if 'weighted_average' in self.fusion_results:
            weights = np.array(self.fusion_results['weighted_average']['weights'])
            test_weighted_preds = np.dot(test_view_preds, weights)
            test_pred_levels = np.where(test_weighted_preds < 0.35, 0, 
                                       np.where(test_weighted_preds < 0.70, 1, 2))
            
            mae = mean_absolute_error(test_scores, test_weighted_preds)
            r2 = r2_score(test_scores, test_weighted_preds)
            accuracy = accuracy_score(test_levels, test_pred_levels)
            
            evaluation_results['weighted_average'] = {'mae': mae, 'r2': r2, 'accuracy': accuracy}
            logger.info(f"\\nWeighted Average Fusion:")
            logger.info(f"  Test MAE: {mae:.4f}, R²: {r2:.4f}, Accuracy: {accuracy:.3f}")
        
        # 2. Neural Fusion
        if 'neural' in self.fusion_results:
            model = NeuralFusionModel(input_dim=5)
            checkpoint = torch.load(self.fusion_results['neural']['model_path'])
            model.load_state_dict(checkpoint['model_state_dict'])
            model.eval()
            
            with torch.no_grad():
                test_view_tensor = torch.tensor(test_view_preds, dtype=torch.float32)
                test_reg_pred, test_cls_pred = model(test_view_tensor)
                test_level_pred = torch.argmax(test_cls_pred, dim=1)
                
                mae = mean_absolute_error(test_scores, test_reg_pred.numpy())
                r2 = r2_score(test_scores, test_reg_pred.numpy())
                accuracy = accuracy_score(test_levels, test_level_pred.numpy())
                
                evaluation_results['neural'] = {'mae': mae, 'r2': r2, 'accuracy': accuracy}
                logger.info(f"\\nNeural Fusion:")
                logger.info(f"  Test MAE: {mae:.4f}, R²: {r2:.4f}, Accuracy: {accuracy:.3f}")
        
        # 3. Ensemble Fusion
        if 'ensemble' in self.fusion_results:
            # Load models
            reg_model = joblib.load(self.fusion_results['ensemble']['regression_model_path'])
            cls_model = joblib.load(self.fusion_results['ensemble']['classification_model_path'])
            scaler = joblib.load(self.fusion_results['ensemble']['scaler_path'])
            
            # Predictions
            test_view_preds_scaled = scaler.transform(test_view_preds)
            test_score_preds = reg_model.predict(test_view_preds_scaled)
            test_level_preds = cls_model.predict(test_view_preds_scaled)
            
            mae = mean_absolute_error(test_scores, test_score_preds)
            r2 = r2_score(test_scores, test_score_preds)
            accuracy = accuracy_score(test_levels, test_level_preds)
            
            evaluation_results['ensemble'] = {'mae': mae, 'r2': r2, 'accuracy': accuracy}
            logger.info(f"\\nEnsemble Fusion:")
            logger.info(f"  Test MAE: {mae:.4f}, R²: {r2:.4f}, Accuracy: {accuracy:.3f}")
        
        # Summary
        logger.info("\\n" + "="*70)
        logger.info("FUSION METHOD COMPARISON")
        logger.info("="*70)
        
        best_mae = float('inf')
        best_method = None
        
        for method, results in evaluation_results.items():
            logger.info(f"{method.upper():20} - MAE: {results['mae']:.4f}, R²: {results['r2']:.4f}, Acc: {results['accuracy']:.3f}")
            if results['mae'] < best_mae:
                best_mae = results['mae']
                best_method = method
        
        logger.info(f"\\nBEST METHOD: {best_method.upper()} (MAE: {best_mae:.4f})")
        
        return evaluation_results
    
    def save_complete_results(self):
        """Save all fusion training results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_path = self.fusion_models_dir / f"fusion_training_results_{timestamp}.json"
        
        complete_results = {
            'timestamp': timestamp,
            'dataset_path': str(self.dataset_path),
            'dataset_stats': {
                'total': len(self.dataset),
                'train': len(self.train_data),
                'val': len(self.val_data),
                'test': len(self.test_data)
            },
            'view_models_loaded': list(self.view_models.keys()),
            'fusion_results': self.fusion_results
        }
        
        with open(results_path, 'w') as f:
            json.dump(complete_results, f, indent=2, default=str)
        
        logger.info(f"\\nComplete results saved to: {results_path}")
        return results_path


def main():
    """Run complete fusion layer training."""
    # Use the same dataset as view training
    dataset_path = "data/training/epic1_dataset_679_samples.json"
    
    if not Path(dataset_path).exists():
        logger.error(f"Dataset not found: {dataset_path}")
        return
    
    # Check if view models exist
    view_models_dir = Path("models/epic1")
    required_models = ['technical_model.pth', 'linguistic_model.pth', 'task_model.pth', 
                      'semantic_model.pth', 'computational_model.pth']
    
    missing_models = []
    for model_file in required_models:
        if not (view_models_dir / model_file).exists():
            missing_models.append(model_file)
    
    if missing_models:
        logger.error(f"Missing view models: {missing_models}")
        logger.error("Please train view models first using: python train_epic1_models.py")
        return
    
    # Initialize trainer
    trainer = Epic1FusionTrainer(dataset_path)
    
    # Train all fusion methods
    logger.info("\\n" + "="*70)
    logger.info("EPIC 1 FUSION LAYER TRAINING")
    logger.info("="*70)
    
    # 1. Weighted Average (fast, interpretable)
    trainer.train_weighted_average_fusion()
    
    # 2. Neural Fusion (flexible, powerful)
    trainer.train_neural_fusion(epochs=50)
    
    # 3. Ensemble Fusion (robust, feature importance)
    trainer.train_ensemble_fusion()
    
    # 4. Evaluate all methods
    evaluation_results = trainer.evaluate_all_fusion_methods()
    
    # 5. Save results
    results_path = trainer.save_complete_results()
    
    logger.info("\\n" + "="*70)
    logger.info("FUSION LAYER TRAINING COMPLETE!")
    logger.info(f"Models saved to: {trainer.fusion_models_dir}")
    logger.info(f"Results saved to: {results_path}")
    logger.info("="*70)


if __name__ == "__main__":
    main()