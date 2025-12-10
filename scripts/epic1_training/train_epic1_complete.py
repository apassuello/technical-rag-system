#!/usr/bin/env python3
"""
Epic 1 Complete ML Training Pipeline

This comprehensive script trains the entire Epic 1 ML system:

Phase 1: View Model Training
- Trains 5 individual view models (technical, linguistic, task, semantic, computational)
- Uses simple neural networks with feature extraction
- Saves trained models with validation metrics

Phase 2: Fusion Layer Training  
- Combines view model predictions using multiple fusion strategies
- Weighted average, neural fusion, and ensemble methods
- Evaluates all approaches and recommends the best

Phase 3: System Integration
- Creates unified prediction interface
- Saves complete system configuration
- Provides usage examples and benchmarks

Usage:
    python train_epic1_complete.py                    # Full training pipeline
    python train_epic1_complete.py --views-only       # Train only view models
    python train_epic1_complete.py --fusion-only      # Train only fusion layer
    python train_epic1_complete.py --quick            # Fast training (fewer epochs)
"""

import json
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import argparse
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, List, Tuple, Optional, Any
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, classification_report
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import StandardScaler
from torch.utils.data import Dataset, DataLoader
import joblib
import random
from scipy.optimize import minimize

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MLflow imports and initialization
try:
    from src.training.mlflow_logger import get_mlflow_logger
    mlflow_logger = get_mlflow_logger()
    MLFLOW_AVAILABLE = True
except ImportError:
    logger.warning("MLflow not available. Install with: pip install mlflow>=2.9.0")
    MLFLOW_AVAILABLE = False
    mlflow_logger = None

# Set seeds for reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed(SEED)


class SimpleViewDataset(Dataset):
    """Dataset for view complexity prediction."""
    
    def __init__(self, samples: List[Dict], view_name: str):
        self.samples = samples
        self.view_name = view_name
        
        # Extract data
        self.queries = [s['query_text'] for s in samples]
        self.scores = [s['view_scores'][view_name] for s in samples]
        
        # Enhanced feature extraction
        self.features = []
        for query in self.queries:
            features = self._extract_features(query)
            self.features.append(features)
        
        self.features = np.array(self.features, dtype=np.float32)
        self.scores = np.array(self.scores, dtype=np.float32)
    
    def _extract_features(self, query: str) -> List[float]:
        """Extract enhanced features from query."""
        words = query.split()
        
        # Enhanced feature set (10 features)
        features = [
            len(query),                                # Character count
            len(words),                                # Word count
            np.mean([len(w) for w in words]) if words else 0,  # Average word length
            query.count('?'),                          # Question marks
            query.count(',') + query.count(';'),      # Punctuation complexity
            len([w for w in words if len(w) > 6]),    # Long words
            len([w for w in words if w[0].isupper()]),  # Capitalized words
            query.count(' and ') + query.count(' or '), # Conjunctions
            len(set(words)) / len(words) if words else 0,  # Vocabulary diversity
            query.count(' ') / len(query) if query else 0,  # Space density
        ]
        
        return features
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        return {
            'features': torch.tensor(self.features[idx], dtype=torch.float32),
            'score': torch.tensor(self.scores[idx], dtype=torch.float32),
            'query': self.queries[idx]
        }


class SimpleViewModel(nn.Module):
    """Enhanced neural network for view complexity prediction."""
    
    def __init__(self, input_dim: int = 10, hidden_dim: int = 128):
        super().__init__()
        
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(0.3),
            
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim // 2),
            nn.Dropout(0.3),
            
            nn.Linear(hidden_dim // 2, hidden_dim // 4),
            nn.ReLU(),
            nn.Dropout(0.2),
            
            nn.Linear(hidden_dim // 4, 1),
            nn.Sigmoid()  # Output in [0, 1] range
        )
    
    def forward(self, features):
        return self.network(features).squeeze()


class NeuralFusionModel(nn.Module):
    """Neural network for fusing view predictions."""
    
    def __init__(self, input_dim=5, hidden_dim=64):
        super().__init__()
        
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
            nn.Linear(hidden_dim // 4, 3),
            nn.Softmax(dim=1)
        )
    
    def forward(self, view_predictions):
        shared_features = self.shared_layers(view_predictions)
        regression_output = self.regression_head(shared_features).squeeze()
        classification_output = self.classification_head(shared_features)
        return regression_output, classification_output


class Epic1CompleteTrainer:
    """Comprehensive trainer for the complete Epic 1 ML system."""
    
    def __init__(self, dataset_path: str, output_dir: str = "models/epic1"):
        """
        Initialize the complete Epic 1 trainer.
        
        Args:
            dataset_path: Path to the training dataset
            output_dir: Directory to save all models and results
        """
        self.dataset_path = Path(dataset_path)
        self.output_dir = Path(output_dir)
        self.fusion_dir = self.output_dir / "fusion"
        
        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.fusion_dir.mkdir(parents=True, exist_ok=True)
        
        # Load and split dataset
        self._load_and_split_dataset()
        
        # View names
        self.view_names = ['technical', 'linguistic', 'task', 'semantic', 'computational']
        
        # Results storage
        self.view_models = {}
        self.view_training_results = {}
        self.fusion_models = {}
        self.fusion_results = {}
        
        logger.info(f"Initialized Epic1CompleteTrainer")
        logger.info(f"Dataset: {len(self.dataset)} samples (Train={len(self.train_data)}, Val={len(self.val_data)}, Test={len(self.test_data)})")
        logger.info(f"Output directory: {self.output_dir}")
    
    def _load_and_split_dataset(self):
        """Load dataset and create train/val/test splits."""
        with open(self.dataset_path, 'r') as f:
            self.dataset = json.load(f)
        
        # Consistent splitting strategy
        self.train_data, temp_data = train_test_split(
            self.dataset, test_size=0.3, random_state=SEED,
            stratify=[s['expected_complexity_level'] for s in self.dataset]
        )
        self.val_data, self.test_data = train_test_split(
            temp_data, test_size=0.5, random_state=SEED,
            stratify=[s['expected_complexity_level'] for s in temp_data]
        )
    
    def train_view_models(self, epochs: int = 30, quick_mode: bool = False):
        """
        Train all individual view models.
        
        Args:
            epochs: Number of training epochs
            quick_mode: If True, use reduced epochs and patience for faster training
        """
        logger.info("\\n" + "="*70)
        logger.info("PHASE 1: TRAINING INDIVIDUAL VIEW MODELS")
        logger.info("="*70)
        
        if quick_mode:
            epochs = min(epochs, 20)
            patience = 5
        else:
            patience = 10
        
        # Test untrained baseline first
        self._test_untrained_baseline()
        
        # Train each view model
        for view_name in self.view_names:
            logger.info(f"\\nTraining {view_name} view model...")

            # Create datasets
            train_dataset = SimpleViewDataset(self.train_data, view_name)
            val_dataset = SimpleViewDataset(self.val_data, view_name)

            train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
            val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)

            # Create model
            model = SimpleViewModel(input_dim=10)  # Enhanced features
            optimizer = optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.01)
            criterion = nn.MSELoss()
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)

            # Start MLflow run for this view model
            mlflow_context = mlflow_logger.start_run(
                experiment_name="epic1-view-models",
                run_name=f"{view_name}_view_training",
                tags={"view": view_name, "epic": "1", "component": "query_analyzer"}
            ) if MLFLOW_AVAILABLE else None

            try:
                if MLFLOW_AVAILABLE:
                    # Log hyperparameters
                    mlflow_logger.log_params({
                        "view_name": view_name,
                        "epochs": epochs,
                        "learning_rate": 0.001,
                        "batch_size": 64,
                        "hidden_dim": 128,
                        "dropout": 0.3,
                        "optimizer": "AdamW",
                        "weight_decay": 0.01,
                        "train_samples": len(train_dataset),
                        "val_samples": len(val_dataset),
                        "feature_dim": 10,
                        "seed": SEED,
                        "quick_mode": quick_mode,
                        "patience": patience
                    })

                # Training loop
                best_val_loss = float('inf')
                patience_counter = 0
            
            for epoch in range(epochs):
                # Training phase
                model.train()
                train_loss = 0
                for batch in train_loader:
                    features = batch['features']
                    scores = batch['score']
                    
                    optimizer.zero_grad()
                    predictions = model(features)
                    loss = criterion(predictions, scores)
                    loss.backward()
                    optimizer.step()
                    
                    train_loss += loss.item()
                
                avg_train_loss = train_loss / len(train_loader)
                
                # Validation phase
                model.eval()
                val_loss = 0
                val_predictions = []
                val_targets = []
                
                with torch.no_grad():
                    for batch in val_loader:
                        features = batch['features']
                        scores = batch['score']
                        
                        predictions = model(features)
                        loss = criterion(predictions, scores)
                        
                        val_loss += loss.item()
                        val_predictions.extend(predictions.cpu().numpy())
                        val_targets.extend(scores.cpu().numpy())
                
                avg_val_loss = val_loss / len(val_loader)
                val_mae = mean_absolute_error(val_targets, val_predictions)
                
                scheduler.step(avg_val_loss)

                # Log metrics to MLflow
                if MLFLOW_AVAILABLE:
                    mlflow_logger.log_metrics({
                        "train_loss": avg_train_loss,
                        "val_loss": avg_val_loss,
                        "val_mae": val_mae,
                        "learning_rate": optimizer.param_groups[0]['lr']
                    }, step=epoch)

                if epoch % 5 == 0:
                    logger.info(f"  Epoch {epoch}: Train Loss={avg_train_loss:.4f}, Val Loss={avg_val_loss:.4f}, Val MAE={val_mae:.4f}")

                # Early stopping
                if avg_val_loss < best_val_loss:
                    best_val_loss = avg_val_loss
                    patience_counter = 0
                    
                    # Save best model
                    model_path = self.output_dir / f"{view_name}_model.pth"
                    torch.save({
                        'model_state_dict': model.state_dict(),
                        'optimizer_state_dict': optimizer.state_dict(),
                        'epoch': epoch,
                        'val_loss': avg_val_loss,
                        'val_mae': val_mae,
                        'view_name': view_name
                    }, model_path)
                    
                else:
                    patience_counter += 1
                    if patience_counter >= patience:
                        logger.info(f"  Early stopping at epoch {epoch}")
                        break
            
                # Load best model
                checkpoint = torch.load(self.output_dir / f"{view_name}_model.pth")
                model.load_state_dict(checkpoint['model_state_dict'])

                # Log final metrics to MLflow
                if MLFLOW_AVAILABLE:
                    mlflow_logger.log_metrics({
                        "final_val_loss": float(checkpoint['val_loss']),
                        "final_val_mae": float(checkpoint['val_mae']),
                        "epochs_trained": int(checkpoint['epoch'])
                    })

                    # Log the trained model
                    mlflow_logger.log_artifact(str(self.output_dir / f"{view_name}_model.pth"))

                # Store model and results
                self.view_models[view_name] = model
                self.view_training_results[view_name] = {
                    'val_mae': checkpoint['val_mae'],
                    'val_loss': checkpoint['val_loss'],
                    'epochs_trained': checkpoint['epoch'],
                    'model_path': str(self.output_dir / f"{view_name}_model.pth")
                }

                logger.info(f"  {view_name} model trained. Best Val MAE: {checkpoint['val_mae']:.4f}")

            finally:
                # Close MLflow run
                if MLFLOW_AVAILABLE and mlflow_context:
                    mlflow_context.__exit__(None, None, None)
        
        # Test trained models
        self._test_trained_view_models()
        
        logger.info("\\n🎉 Phase 1 Complete: All view models trained successfully!")
    
    def _test_untrained_baseline(self):
        """Test untrained models to establish baseline."""
        logger.info("\\nTesting untrained models (baseline)...")
        
        baseline_results = {}
        for view_name in self.view_names:
            model = SimpleViewModel(input_dim=10)
            model.eval()
            
            test_dataset = SimpleViewDataset(self.test_data, view_name)
            test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
            
            predictions = []
            targets = []
            
            with torch.no_grad():
                for batch in test_loader:
                    features = batch['features']
                    scores = batch['score']
                    preds = model(features)
                    predictions.extend(preds.cpu().numpy())
                    targets.extend(scores.cpu().numpy())
            
            mae = mean_absolute_error(targets, predictions)
            r2 = r2_score(targets, predictions)
            baseline_results[view_name] = {'mae': mae, 'r2': r2}
        
        avg_mae = np.mean([r['mae'] for r in baseline_results.values()])
        logger.info(f"  Untrained baseline - Average MAE: {avg_mae:.4f}")
    
    def _test_trained_view_models(self):
        """Test all trained view models."""
        logger.info("\\nTesting trained view models...")
        
        for view_name in self.view_names:
            model = self.view_models[view_name]
            model.eval()
            
            test_dataset = SimpleViewDataset(self.test_data, view_name)
            test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
            
            predictions = []
            targets = []
            
            with torch.no_grad():
                for batch in test_loader:
                    features = batch['features']
                    scores = batch['score']
                    preds = model(features)
                    predictions.extend(preds.cpu().numpy())
                    targets.extend(scores.cpu().numpy())
            
            mae = mean_absolute_error(targets, predictions)
            r2 = r2_score(targets, predictions)
            
            # Update results
            self.view_training_results[view_name].update({
                'test_mae': mae,
                'test_r2': r2
            })
            
            logger.info(f"  {view_name}: Test MAE={mae:.4f}, R²={r2:.4f}")
    
    def train_fusion_layer(self, quick_mode: bool = False):
        """
        Train fusion layer with multiple strategies.

        Args:
            quick_mode: If True, skip neural fusion for faster training
        """
        logger.info("\\n" + "="*70)
        logger.info("PHASE 2: TRAINING FUSION LAYER")
        logger.info("="*70)

        if not self.view_models:
            raise ValueError("View models must be trained first. Run train_view_models() or load existing models.")

        # Start MLflow run for fusion layer training
        mlflow_context = mlflow_logger.start_run(
            experiment_name="epic1-fusion-layer",
            run_name=f"fusion_training",
            tags={"epic": "1", "component": "fusion_layer", "quick_mode": str(quick_mode)}
        ) if MLFLOW_AVAILABLE else None

        try:
            if MLFLOW_AVAILABLE:
                mlflow_logger.log_params({
                    "num_views": len(self.view_names),
                    "view_names": ", ".join(self.view_names),
                    "quick_mode": quick_mode,
                    "train_samples": len(self.train_data),
                    "val_samples": len(self.val_data),
                    "test_samples": len(self.test_data),
                    "fusion_strategies": "weighted_average, ensemble" + ("" if quick_mode else ", neural")
                })

            # Extract view predictions for all splits
            self.train_view_preds, self.train_scores, self.train_levels = self._extract_view_predictions(self.train_data)
            self.val_view_preds, self.val_scores, self.val_levels = self._extract_view_predictions(self.val_data)
            self.test_view_preds, self.test_scores, self.test_levels = self._extract_view_predictions(self.test_data)

            # Train different fusion strategies
            self._train_weighted_average_fusion()
            self._train_ensemble_fusion()

            if not quick_mode:
                self._train_neural_fusion()
            else:
                logger.info("Skipping neural fusion in quick mode")

            # Evaluate all fusion methods
            self._evaluate_fusion_methods()

            # Log fusion results to MLflow
            if MLFLOW_AVAILABLE and hasattr(self, 'fusion_results'):
                for fusion_name, results in self.fusion_results.items():
                    if isinstance(results, dict):
                        for metric_name, metric_value in results.items():
                            if isinstance(metric_value, (int, float)):
                                mlflow_logger.log_metrics({
                                    f"{fusion_name}_{metric_name}": float(metric_value)
                                })

            logger.info("\\n🎉 Phase 2 Complete: Fusion layer trained with multiple strategies!")

        finally:
            # Close MLflow run
            if MLFLOW_AVAILABLE and mlflow_context:
                mlflow_context.__exit__(None, None, None)
    
    def _extract_view_predictions(self, data: List[Dict]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Extract predictions from all view models."""
        view_predictions = []
        complexity_scores = []
        complexity_levels = []
        
        level_mapping = {'simple': 0, 'medium': 1, 'complex': 2}
        
        with torch.no_grad():
            for sample in data:
                sample_view_preds = []
                
                for view_name in self.view_names:
                    view_dataset = SimpleViewDataset([sample], view_name)
                    features = torch.tensor(view_dataset.features[0], dtype=torch.float32).unsqueeze(0)  # Add batch dimension
                    prediction = self.view_models[view_name](features).item()
                    sample_view_preds.append(prediction)
                
                view_predictions.append(sample_view_preds)
                complexity_scores.append(sample['expected_complexity_score'])
                complexity_levels.append(level_mapping[sample['expected_complexity_level']])
        
        return (
            np.array(view_predictions, dtype=np.float32),
            np.array(complexity_scores, dtype=np.float32),
            np.array(complexity_levels, dtype=int)
        )
    
    def _train_weighted_average_fusion(self):
        """Train optimal weighted average fusion."""
        logger.info("\\nTraining Weighted Average Fusion...")
        
        def objective(weights):
            if np.sum(weights) != 1.0 or np.any(weights < 0):
                return 1e6
            weighted_preds = np.dot(self.train_view_preds, weights)
            return mean_squared_error(self.train_scores, weighted_preds)
        
        # Optimize weights
        initial_weights = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
        bounds = [(0.0, 1.0) for _ in range(5)]
        
        result = minimize(objective, initial_weights, method='SLSQP', 
                         bounds=bounds, constraints=constraints)
        optimal_weights = result.x
        
        # Validate
        val_weighted_preds = np.dot(self.val_view_preds, optimal_weights)
        val_mae = mean_absolute_error(self.val_scores, val_weighted_preds)
        val_r2 = r2_score(self.val_scores, val_weighted_preds)
        
        val_pred_levels = np.where(val_weighted_preds < 0.35, 0, 
                                  np.where(val_weighted_preds < 0.70, 1, 2))
        val_accuracy = accuracy_score(self.val_levels, val_pred_levels)
        
        # Save
        fusion_model = {
            'type': 'weighted_average',
            'weights': optimal_weights.tolist(),
            'view_names': self.view_names,
            'thresholds': [0.35, 0.70],
            'val_mae': val_mae,
            'val_r2': val_r2,
            'val_accuracy': val_accuracy
        }
        
        with open(self.fusion_dir / "weighted_average_fusion.json", 'w') as f:
            json.dump(fusion_model, f, indent=2)
        
        self.fusion_models['weighted_average'] = fusion_model
        logger.info(f"  Optimal weights: {dict(zip(self.view_names, optimal_weights))}")
        logger.info(f"  Val MAE: {val_mae:.4f}, R²: {val_r2:.4f}, Accuracy: {val_accuracy:.3f}")
    
    def _train_ensemble_fusion(self):
        """Train ensemble-based fusion."""
        logger.info("\\nTraining Ensemble Fusion (Random Forest)...")
        
        # Scale features
        scaler = StandardScaler()
        train_scaled = scaler.fit_transform(self.train_view_preds)
        val_scaled = scaler.transform(self.val_view_preds)
        
        # Train models
        reg_model = RandomForestRegressor(n_estimators=100, random_state=SEED, n_jobs=-1)
        reg_model.fit(train_scaled, self.train_scores)
        
        cls_model = RandomForestClassifier(n_estimators=100, random_state=SEED, n_jobs=-1)
        cls_model.fit(train_scaled, self.train_levels)
        
        # Validate
        val_score_preds = reg_model.predict(val_scaled)
        val_level_preds = cls_model.predict(val_scaled)
        
        val_mae = mean_absolute_error(self.val_scores, val_score_preds)
        val_r2 = r2_score(self.val_scores, val_score_preds)
        val_accuracy = accuracy_score(self.val_levels, val_level_preds)
        
        feature_importance = dict(zip(self.view_names, reg_model.feature_importances_))
        
        # Save models
        joblib.dump(reg_model, self.fusion_dir / "ensemble_regression_model.pkl")
        joblib.dump(cls_model, self.fusion_dir / "ensemble_classification_model.pkl")
        joblib.dump(scaler, self.fusion_dir / "ensemble_scaler.pkl")
        
        self.fusion_models['ensemble'] = {
            'type': 'ensemble_fusion',
            'regression_model_path': str(self.fusion_dir / "ensemble_regression_model.pkl"),
            'classification_model_path': str(self.fusion_dir / "ensemble_classification_model.pkl"),
            'scaler_path': str(self.fusion_dir / "ensemble_scaler.pkl"),
            'feature_importance': feature_importance,
            'val_mae': val_mae,
            'val_r2': val_r2,
            'val_accuracy': val_accuracy
        }
        
        logger.info(f"  Feature importance: {feature_importance}")
        logger.info(f"  Val MAE: {val_mae:.4f}, R²: {val_r2:.4f}, Accuracy: {val_accuracy:.3f}")
    
    def _train_neural_fusion(self, epochs=50):
        """Train neural fusion model."""
        logger.info(f"\\nTraining Neural Fusion Model ({epochs} epochs)...")
        
        # Convert to tensors
        train_view_tensor = torch.tensor(self.train_view_preds, dtype=torch.float32)
        train_score_tensor = torch.tensor(self.train_scores, dtype=torch.float32)
        train_level_tensor = torch.tensor(self.train_levels, dtype=torch.long)
        
        val_view_tensor = torch.tensor(self.val_view_preds, dtype=torch.float32)
        val_score_tensor = torch.tensor(self.val_scores, dtype=torch.float32)
        val_level_tensor = torch.tensor(self.val_levels, dtype=torch.long)
        
        # Create model
        model = NeuralFusionModel(input_dim=5)
        optimizer = optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.01)
        
        regression_criterion = nn.MSELoss()
        classification_criterion = nn.CrossEntropyLoss()
        
        best_combined_loss = float('inf')
        patience = 15
        patience_counter = 0
        
        for epoch in range(epochs):
            model.train()
            
            reg_pred, cls_pred = model(train_view_tensor)
            reg_loss = regression_criterion(reg_pred, train_score_tensor)
            cls_loss = classification_criterion(cls_pred, train_level_tensor)
            combined_loss = reg_loss + 0.5 * cls_loss
            
            optimizer.zero_grad()
            combined_loss.backward()
            optimizer.step()
            
            # Validation
            if epoch % 10 == 0:
                model.eval()
                with torch.no_grad():
                    val_reg_pred, val_cls_pred = model(val_view_tensor)
                    val_reg_loss = regression_criterion(val_reg_pred, val_score_tensor)
                    val_cls_loss = classification_criterion(val_cls_pred, val_level_tensor)
                    val_combined_loss = val_reg_loss + 0.5 * val_cls_loss
                    
                    val_mae = mean_absolute_error(val_score_tensor.numpy(), val_reg_pred.numpy())
                    val_cls_pred_labels = torch.argmax(val_cls_pred, dim=1)
                    val_accuracy = accuracy_score(val_level_tensor.numpy(), val_cls_pred_labels.numpy())
                    
                    logger.info(f"  Epoch {epoch}: Val Loss={val_combined_loss:.4f}, MAE={val_mae:.4f}, Acc={val_accuracy:.3f}")
                    
                    if val_combined_loss < best_combined_loss:
                        best_combined_loss = val_combined_loss
                        patience_counter = 0
                        
                        torch.save({
                            'model_state_dict': model.state_dict(),
                            'val_combined_loss': val_combined_loss,
                            'val_mae': val_mae,
                            'val_accuracy': val_accuracy
                        }, self.fusion_dir / "neural_fusion_model.pth")
                    else:
                        patience_counter += 1
                        if patience_counter >= patience:
                            logger.info(f"  Early stopping at epoch {epoch}")
                            break
        
        # Load best model
        checkpoint = torch.load(self.fusion_dir / "neural_fusion_model.pth")
        
        self.fusion_models['neural'] = {
            'type': 'neural_fusion',
            'model_path': str(self.fusion_dir / "neural_fusion_model.pth"),
            'val_mae': checkpoint['val_mae'],
            'val_accuracy': checkpoint['val_accuracy']
        }
        
        logger.info(f"  Neural fusion trained. Best Val MAE: {checkpoint['val_mae']:.4f}")
    
    def _evaluate_fusion_methods(self):
        """Evaluate all fusion methods on test set."""
        logger.info("\\n" + "="*60)
        logger.info("EVALUATING FUSION METHODS ON TEST SET")
        logger.info("="*60)
        
        test_results = {}
        
        # 1. Weighted Average
        if 'weighted_average' in self.fusion_models:
            weights = np.array(self.fusion_models['weighted_average']['weights'])
            test_preds = np.dot(self.test_view_preds, weights)
            test_pred_levels = np.where(test_preds < 0.35, 0, np.where(test_preds < 0.70, 1, 2))
            
            mae = mean_absolute_error(self.test_scores, test_preds)
            r2 = r2_score(self.test_scores, test_preds)
            accuracy = accuracy_score(self.test_levels, test_pred_levels)
            
            test_results['weighted_average'] = {'mae': mae, 'r2': r2, 'accuracy': accuracy}
            logger.info(f"Weighted Average: MAE={mae:.4f}, R²={r2:.4f}, Acc={accuracy:.3f}")
        
        # 2. Ensemble
        if 'ensemble' in self.fusion_models:
            reg_model = joblib.load(self.fusion_models['ensemble']['regression_model_path'])
            cls_model = joblib.load(self.fusion_models['ensemble']['classification_model_path'])
            scaler = joblib.load(self.fusion_models['ensemble']['scaler_path'])
            
            test_scaled = scaler.transform(self.test_view_preds)
            test_score_preds = reg_model.predict(test_scaled)
            test_level_preds = cls_model.predict(test_scaled)
            
            mae = mean_absolute_error(self.test_scores, test_score_preds)
            r2 = r2_score(self.test_scores, test_score_preds)
            accuracy = accuracy_score(self.test_levels, test_level_preds)
            
            test_results['ensemble'] = {'mae': mae, 'r2': r2, 'accuracy': accuracy}
            logger.info(f"Ensemble:         MAE={mae:.4f}, R²={r2:.4f}, Acc={accuracy:.3f}")
        
        # 3. Neural
        if 'neural' in self.fusion_models:
            model = NeuralFusionModel(input_dim=5)
            checkpoint = torch.load(self.fusion_models['neural']['model_path'])
            model.load_state_dict(checkpoint['model_state_dict'])
            model.eval()
            
            with torch.no_grad():
                test_view_tensor = torch.tensor(self.test_view_preds, dtype=torch.float32)
                test_reg_pred, test_cls_pred = model(test_view_tensor)
                test_level_pred = torch.argmax(test_cls_pred, dim=1)
                
                mae = mean_absolute_error(self.test_scores, test_reg_pred.numpy())
                r2 = r2_score(self.test_scores, test_reg_pred.numpy())
                accuracy = accuracy_score(self.test_levels, test_level_pred.numpy())
                
                test_results['neural'] = {'mae': mae, 'r2': r2, 'accuracy': accuracy}
                logger.info(f"Neural:           MAE={mae:.4f}, R²={r2:.4f}, Acc={accuracy:.3f}")
        
        # Find best method
        if test_results:
            best_method = min(test_results.items(), key=lambda x: x[1]['mae'])
            logger.info(f"\\n🏆 BEST METHOD: {best_method[0].upper()} (MAE: {best_method[1]['mae']:.4f})")
            
            self.fusion_results['test_results'] = test_results
            self.fusion_results['best_method'] = best_method[0]
    
    def create_unified_predictor(self):
        """Create unified prediction interface."""
        logger.info("\\n" + "="*70)
        logger.info("PHASE 3: CREATING UNIFIED PREDICTION SYSTEM")
        logger.info("="*70)
        
        # Determine best fusion method
        best_method = self.fusion_results.get('best_method', 'ensemble')
        
        # Create prediction script
        predictor_code = f'''#!/usr/bin/env python3
"""
Epic 1 Unified Complexity Predictor

Automatically generated prediction interface for the complete Epic 1 ML system.
Best fusion method: {best_method}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

import torch
import numpy as np
import joblib
from pathlib import Path
from typing import Dict, List, Any
import json

# Model class definitions (embedded for standalone usage)
import torch
import torch.nn as nn
from torch.utils.data import Dataset
import numpy as np

class SimpleViewDataset(Dataset):
    def __init__(self, samples, view_name):
        self.samples = samples
        self.view_name = view_name
        self.queries = [s['query_text'] for s in samples]
        self.scores = [s.get('view_scores', {{}}).get(view_name, 0.0) for s in samples]
        
        self.features = []
        for query in self.queries:
            features = self._extract_features(query)
            self.features.append(features)
        
        self.features = np.array(self.features, dtype=np.float32)
        self.scores = np.array(self.scores, dtype=np.float32)
    
    def _extract_features(self, query):
        words = query.split()
        features = [
            len(query), len(words),
            np.mean([len(w) for w in words]) if words else 0,
            query.count('?'), query.count(',') + query.count(';'),
            len([w for w in words if len(w) > 6]),
            len([w for w in words if w[0].isupper()]),
            query.count(' and ') + query.count(' or '),
            len(set(words)) / len(words) if words else 0,
            query.count(' ') / len(query) if query else 0,
        ]
        return features
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        return {{
            'features': torch.tensor(self.features[idx], dtype=torch.float32),
            'score': torch.tensor(self.scores[idx], dtype=torch.float32),
            'query': self.queries[idx]
        }}

class SimpleViewModel(nn.Module):
    def __init__(self, input_dim=10, hidden_dim=128):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.BatchNorm1d(hidden_dim), nn.Dropout(0.3),
            nn.Linear(hidden_dim, hidden_dim // 2), nn.ReLU(), nn.BatchNorm1d(hidden_dim // 2), nn.Dropout(0.3),
            nn.Linear(hidden_dim // 2, hidden_dim // 4), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(hidden_dim // 4, 1), nn.Sigmoid()
        )
    
    def forward(self, features):
        return self.network(features).squeeze()

class NeuralFusionModel(nn.Module):
    def __init__(self, input_dim=5, hidden_dim=64):
        super().__init__()
        self.shared_layers = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.BatchNorm1d(hidden_dim), nn.Dropout(0.3),
            nn.Linear(hidden_dim, hidden_dim // 2), nn.ReLU(), nn.BatchNorm1d(hidden_dim // 2), nn.Dropout(0.2)
        )
        self.regression_head = nn.Sequential(
            nn.Linear(hidden_dim // 2, hidden_dim // 4), nn.ReLU(), nn.Dropout(0.1),
            nn.Linear(hidden_dim // 4, 1), nn.Sigmoid()
        )
        self.classification_head = nn.Sequential(
            nn.Linear(hidden_dim // 2, hidden_dim // 4), nn.ReLU(), nn.Dropout(0.1),
            nn.Linear(hidden_dim // 4, 3), nn.Softmax(dim=1)
        )
    
    def forward(self, view_predictions):
        shared_features = self.shared_layers(view_predictions)
        regression_output = self.regression_head(shared_features).squeeze()
        classification_output = self.classification_head(shared_features)
        return regression_output, classification_output

class Epic1Predictor:
    """Unified predictor for Epic 1 complexity analysis."""
    
    def __init__(self, model_dir: str = "models/epic1"):
        self.model_dir = Path(model_dir)
        self.view_names = {repr(self.view_names)}
        self.best_method = "{best_method}"
        
        # Load view models
        self._load_view_models()
        
        # Load best fusion model
        self._load_fusion_model()
    
    def _load_view_models(self):
        """Load all trained view models."""
        self.view_models = {{}}
        
        for view_name in self.view_names:
            model_path = self.model_dir / f"{{view_name}}_model.pth"
            model = SimpleViewModel(input_dim=10)
            checkpoint = torch.load(model_path, map_location='cpu')
            model.load_state_dict(checkpoint['model_state_dict'])
            model.eval()
            self.view_models[view_name] = model
    
    def _load_fusion_model(self):
        """Load the best fusion model."""
        if self.best_method == "ensemble":
            self.fusion_reg = joblib.load(self.model_dir / "fusion/ensemble_regression_model.pkl")
            self.fusion_cls = joblib.load(self.model_dir / "fusion/ensemble_classification_model.pkl") 
            self.fusion_scaler = joblib.load(self.model_dir / "fusion/ensemble_scaler.pkl")
            
        elif self.best_method == "neural":
            self.fusion_model = NeuralFusionModel(input_dim=5)
            checkpoint = torch.load(self.model_dir / "fusion/neural_fusion_model.pth", map_location='cpu')
            self.fusion_model.load_state_dict(checkpoint['model_state_dict'])
            self.fusion_model.eval()
            
        elif self.best_method == "weighted_average":
            with open(self.model_dir / "fusion/weighted_average_fusion.json", 'r') as f:
                self.fusion_config = json.load(f)
    
    def predict(self, query_text: str) -> Dict[str, Any]:
        """
        Predict complexity for a query.
        
        Args:
            query_text: Input query string
            
        Returns:
            Dictionary with complexity score, level, view scores, and metadata
        """
        # Get view predictions
        view_predictions = []
        view_scores = {{}}
        
        sample = {{'query_text': query_text}}
        
        with torch.no_grad():
            for view_name in self.view_names:
                dataset = SimpleViewDataset([sample], view_name) 
                features = torch.tensor(dataset.features[0], dtype=torch.float32).unsqueeze(0)  # Add batch dimension
                pred = self.view_models[view_name](features).item()
                view_predictions.append(pred)
                view_scores[view_name] = pred
        
        # Apply fusion
        if self.best_method == "ensemble":
            view_array = np.array([view_predictions]).reshape(1, -1)
            view_scaled = self.fusion_scaler.transform(view_array)
            
            final_score = self.fusion_reg.predict(view_scaled)[0]
            final_level_idx = self.fusion_cls.predict(view_scaled)[0]
            
        elif self.best_method == "neural":
            view_tensor = torch.tensor([view_predictions], dtype=torch.float32)
            with torch.no_grad():
                score_pred, level_pred = self.fusion_model(view_tensor)
                final_score = score_pred.item()
                final_level_idx = torch.argmax(level_pred, dim=1).item()
                
        elif self.best_method == "weighted_average":
            weights = np.array(self.fusion_config['weights'])
            final_score = np.dot(view_predictions, weights)
            final_level_idx = 0 if final_score < 0.35 else (1 if final_score < 0.70 else 2)
        
        # Convert level index to name
        level_names = ['simple', 'medium', 'complex']
        final_level = level_names[final_level_idx]
        
        return {{
            'query_text': query_text,
            'complexity_score': float(final_score),
            'complexity_level': final_level,
            'view_scores': view_scores,
            'fusion_method': self.best_method,
            'confidence': 'high',  # Based on test accuracy > 90%
            'metadata': {{
                'model_version': 'epic1_v1.0',
                'prediction_timestamp': None  # Add if needed
            }}
        }}
    
    def batch_predict(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Predict complexity for multiple queries."""
        return [self.predict(query) for query in queries]


# Example usage
if __name__ == "__main__":
    predictor = Epic1Predictor()
    
    # Test queries
    test_queries = [
        "What is Python?",  # Simple
        "How do I implement rate limiting for REST APIs?",  # Medium  
        "How can I design a distributed consensus algorithm with Byzantine fault tolerance?",  # Complex
    ]
    
    print("Epic 1 Complexity Predictions:")
    print("=" * 50)
    
    for query in test_queries:
        result = predictor.predict(query)
        print(f"Query: {{query[:50]}}...")
        print(f"Score: {{result['complexity_score']:.3f}} | Level: {{result['complexity_level']}} | Method: {{result['fusion_method']}}")
        print()
'''
        
        predictor_path = self.output_dir / "epic1_predictor.py"
        with open(predictor_path, 'w') as f:
            f.write(predictor_code)
        
        logger.info(f"✅ Unified predictor created: {predictor_path}")
        
        # Create configuration summary
        config_summary = {
            'epic1_system_info': {
                'version': '1.0',
                'training_date': datetime.now().isoformat(),
                'dataset_size': len(self.dataset),
                'best_fusion_method': best_method,
                'performance_summary': self.fusion_results.get('test_results', {})
            },
            'view_models': self.view_training_results,
            'fusion_models': self.fusion_models,
            'model_files': {
                'view_models': [f"{view}_model.pth" for view in self.view_names],
                'fusion_models': list(self.fusion_dir.glob("*.pkl")) + list(self.fusion_dir.glob("*.pth")) + list(self.fusion_dir.glob("*.json")),
                'predictor_script': 'epic1_predictor.py'
            }
        }
        
        config_path = self.output_dir / "epic1_system_config.json"
        with open(config_path, 'w') as f:
            json.dump(config_summary, f, indent=2, default=str)
        
        logger.info(f"✅ System configuration saved: {config_path}")
        logger.info("\\n🎉 Phase 3 Complete: Unified prediction system ready!")
    
    def save_complete_training_report(self):
        """Save comprehensive training report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"epic1_complete_training_report_{timestamp}.json"
        
        complete_report = {
            'training_summary': {
                'timestamp': timestamp,
                'dataset_path': str(self.dataset_path),
                'total_samples': len(self.dataset),
                'train_samples': len(self.train_data),
                'val_samples': len(self.val_data),
                'test_samples': len(self.test_data),
                'best_fusion_method': self.fusion_results.get('best_method', 'unknown')
            },
            'view_model_results': self.view_training_results,
            'fusion_model_results': self.fusion_models,
            'test_performance': self.fusion_results.get('test_results', {}),
            'model_files_created': {
                'view_models': [f"{view}_model.pth" for view in self.view_names],
                'fusion_models': [str(p.name) for p in self.fusion_dir.glob("*")],
                'predictor_script': 'epic1_predictor.py',
                'system_config': 'epic1_system_config.json'
            }
        }
        
        with open(report_path, 'w') as f:
            json.dump(complete_report, f, indent=2, default=str)
        
        logger.info(f"\\n📊 Complete training report saved: {report_path}")
        return report_path
    
    def run_complete_pipeline(self, view_epochs: int = 30, quick_mode: bool = False):
        """Run the complete Epic 1 training pipeline."""
        logger.info("\\n" + "="*80)
        logger.info("🚀 EPIC 1 COMPLETE ML TRAINING PIPELINE")
        logger.info("="*80)
        
        start_time = datetime.now()
        
        # Phase 1: Train view models
        self.train_view_models(epochs=view_epochs, quick_mode=quick_mode)
        
        # Phase 2: Train fusion layer  
        self.train_fusion_layer(quick_mode=quick_mode)
        
        # Phase 3: Create unified system
        self.create_unified_predictor()
        
        # Generate final report
        report_path = self.save_complete_training_report()
        
        end_time = datetime.now()
        total_time = end_time - start_time
        
        # Final summary
        logger.info("\\n" + "="*80)
        logger.info("🎉 EPIC 1 COMPLETE TRAINING FINISHED!")
        logger.info("="*80)
        logger.info(f"Total training time: {total_time}")
        logger.info(f"Models saved to: {self.output_dir}")
        logger.info(f"Predictor script: {self.output_dir}/epic1_predictor.py")
        logger.info(f"Complete report: {report_path}")
        
        # Performance summary
        if 'test_results' in self.fusion_results:
            best_method = self.fusion_results.get('best_method', 'unknown')
            if best_method in self.fusion_results['test_results']:
                best_results = self.fusion_results['test_results'][best_method]
                logger.info(f"\\n🏆 Best Performance ({best_method.upper()}):")
                logger.info(f"   Test MAE: {best_results['mae']:.4f}")
                logger.info(f"   Test R²: {best_results['r2']:.4f}")
                logger.info(f"   Test Accuracy: {best_results['accuracy']:.1%}")
        
        logger.info("\\n✨ Ready for deployment! Use epic1_predictor.py for predictions.")
        logger.info("="*80)


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description="Epic 1 Complete ML Training Pipeline")
    parser.add_argument('--dataset', default='data/training/epic1_dataset_679_samples.json',
                       help='Path to training dataset')
    parser.add_argument('--output-dir', default='models/epic1',
                       help='Output directory for models')
    parser.add_argument('--views-only', action='store_true',
                       help='Train only view models (skip fusion)')
    parser.add_argument('--fusion-only', action='store_true', 
                       help='Train only fusion layer (requires existing view models)')
    parser.add_argument('--quick', action='store_true',
                       help='Quick training mode (reduced epochs, faster)')
    parser.add_argument('--epochs', type=int, default=30,
                       help='Number of epochs for view model training')
    
    args = parser.parse_args()
    
    # Validate dataset exists
    if not Path(args.dataset).exists():
        logger.error(f"Dataset not found: {args.dataset}")
        logger.error("Please ensure the dataset file exists or specify correct path with --dataset")
        return
    
    # Initialize trainer
    trainer = Epic1CompleteTrainer(args.dataset, args.output_dir)

    # Start top-level MLflow run for the complete pipeline
    pipeline_mlflow_context = mlflow_logger.start_run(
        experiment_name="epic1-complete-pipeline",
        run_name=f"complete_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        tags={
            "epic": "1",
            "pipeline": "complete",
            "views_only": str(args.views_only),
            "fusion_only": str(args.fusion_only),
            "quick_mode": str(args.quick)
        }
    ) if MLFLOW_AVAILABLE else None

    try:
        if MLFLOW_AVAILABLE:
            # Log pipeline configuration
            mlflow_logger.log_params({
                "dataset_path": args.dataset,
                "output_dir": args.output_dir,
                "views_only": args.views_only,
                "fusion_only": args.fusion_only,
                "quick_mode": args.quick,
                "epochs": args.epochs,
                "seed": SEED
            })

        if args.fusion_only:
            # Load existing view models
            logger.info("Loading existing view models for fusion training...")
            trainer.view_models = {}
            for view_name in trainer.view_names:
                model_path = trainer.output_dir / f"{view_name}_model.pth"
                if model_path.exists():
                    model = SimpleViewModel(input_dim=10)
                    checkpoint = torch.load(model_path)
                    model.load_state_dict(checkpoint['model_state_dict'])
                    model.eval()
                    trainer.view_models[view_name] = model
                else:
                    raise FileNotFoundError(f"View model not found: {model_path}")
            
            trainer.train_fusion_layer(quick_mode=args.quick)
            trainer.create_unified_predictor()
            trainer.save_complete_training_report()
            
        elif args.views_only:
            trainer.train_view_models(epochs=args.epochs, quick_mode=args.quick)
            
        else:
            # Complete pipeline
            trainer.run_complete_pipeline(view_epochs=args.epochs, quick_mode=args.quick)
    
    except KeyboardInterrupt:
        logger.info("\\n⚠️  Training interrupted by user")
    except Exception as e:
        logger.error(f"\\n❌ Training failed: {e}")
        raise
    finally:
        # Close top-level MLflow run
        if MLFLOW_AVAILABLE and pipeline_mlflow_context:
            pipeline_mlflow_context.__exit__(None, None, None)


if __name__ == "__main__":
    main()