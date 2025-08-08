#!/usr/bin/env python3
"""
Epic 1 Model Training and Evaluation

This script:
1. Tests untrained models on the dataset (baseline)
2. Trains view models on the generated dataset
3. Saves model checkpoints for reuse
4. Compares trained vs untrained performance
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
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from torch.utils.data import Dataset, DataLoader
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set seeds for reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed(SEED)


class SimpleViewDataset(Dataset):
    """Simple dataset for view complexity prediction."""
    
    def __init__(self, samples: List[Dict], view_name: str):
        """
        Initialize dataset for a specific view.
        
        Args:
            samples: List of training samples
            view_name: Name of the view to train
        """
        self.samples = samples
        self.view_name = view_name
        
        # Extract data
        self.queries = [s['query_text'] for s in samples]
        self.scores = [s['view_scores'][view_name] for s in samples]
        
        # Simple feature extraction (character and word counts for now)
        self.features = []
        for query in self.queries:
            features = self._extract_simple_features(query)
            self.features.append(features)
        
        self.features = np.array(self.features, dtype=np.float32)
        self.scores = np.array(self.scores, dtype=np.float32)
    
    def _extract_simple_features(self, query: str) -> List[float]:
        """Extract simple features from query."""
        words = query.split()
        
        # Basic features (we'll use these as a simple baseline)
        features = [
            len(query),                          # Character count
            len(words),                           # Word count
            np.mean([len(w) for w in words]),    # Average word length
            query.count('?'),                     # Question marks
            query.count(','),                     # Commas (complexity indicator)
            len([w for w in words if len(w) > 6]),  # Long words
            len([w for w in words if w[0].isupper()]),  # Capitalized words
            query.count(' and ') + query.count(' or '),  # Conjunctions
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
    """Simple neural network for view complexity prediction."""
    
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
            nn.Sigmoid()  # Output in [0, 1] range
        )
    
    def forward(self, features):
        return self.network(features).squeeze()


class Epic1ModelTrainer:
    """Trainer for Epic 1 view models."""
    
    def __init__(self, dataset_path: str, checkpoint_dir: str = "models/epic1"):
        """
        Initialize trainer.
        
        Args:
            dataset_path: Path to the training dataset
            checkpoint_dir: Directory to save model checkpoints
        """
        self.dataset_path = Path(dataset_path)
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Load dataset
        with open(self.dataset_path, 'r') as f:
            self.dataset = json.load(f)
        
        # Split into train/val/test
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
        
        # Models and results storage
        self.models = {}
        self.untrained_results = {}
        self.trained_results = {}
    
    def test_untrained_baseline(self):
        """Test untrained models as baseline."""
        logger.info("\n" + "="*60)
        logger.info("TESTING UNTRAINED MODELS (BASELINE)")
        logger.info("="*60)
        
        for view_name in self.view_names:
            logger.info(f"\nTesting untrained {view_name} model...")
            
            # Create untrained model
            model = SimpleViewModel()
            model.eval()
            
            # Create test dataset
            test_dataset = SimpleViewDataset(self.test_data, view_name)
            test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
            
            # Evaluate
            predictions = []
            targets = []
            
            with torch.no_grad():
                for batch in test_loader:
                    features = batch['features']
                    scores = batch['score']
                    
                    preds = model(features)
                    
                    predictions.extend(preds.cpu().numpy())
                    targets.extend(scores.cpu().numpy())
            
            # Calculate metrics
            mae = mean_absolute_error(targets, predictions)
            rmse = np.sqrt(mean_squared_error(targets, predictions))
            r2 = r2_score(targets, predictions)
            
            self.untrained_results[view_name] = {
                'mae': mae,
                'rmse': rmse,
                'r2': r2,
                'predictions': predictions[:10],  # Save some examples
                'targets': targets[:10]
            }
            
            logger.info(f"  Untrained {view_name} - MAE: {mae:.4f}, RMSE: {rmse:.4f}, R²: {r2:.4f}")
    
    def train_view_model(self, view_name: str, epochs: int = 20):
        """Train a single view model."""
        logger.info(f"\nTraining {view_name} model...")
        
        # Create datasets
        train_dataset = SimpleViewDataset(self.train_data, view_name)
        val_dataset = SimpleViewDataset(self.val_data, view_name)
        
        train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
        
        # Create model
        model = SimpleViewModel()
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.MSELoss()
        
        # Training loop
        best_val_loss = float('inf')
        patience = 5
        patience_counter = 0
        
        train_losses = []
        val_losses = []
        
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
            train_losses.append(avg_train_loss)
            
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
            val_losses.append(avg_val_loss)
            
            val_mae = mean_absolute_error(val_targets, val_predictions)
            
            if epoch % 5 == 0:
                logger.info(f"  Epoch {epoch}: Train Loss={avg_train_loss:.4f}, Val Loss={avg_val_loss:.4f}, Val MAE={val_mae:.4f}")
            
            # Early stopping
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                patience_counter = 0
                
                # Save best model
                checkpoint_path = self.checkpoint_dir / f"{view_name}_model.pth"
                torch.save({
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'epoch': epoch,
                    'best_val_loss': best_val_loss,
                    'val_mae': val_mae
                }, checkpoint_path)
                
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    logger.info(f"  Early stopping at epoch {epoch}")
                    break
        
        # Load best model
        checkpoint = torch.load(self.checkpoint_dir / f"{view_name}_model.pth")
        model.load_state_dict(checkpoint['model_state_dict'])
        
        self.models[view_name] = model
        logger.info(f"  {view_name} model trained. Best Val MAE: {checkpoint['val_mae']:.4f}")
        
        return model, train_losses, val_losses
    
    def train_all_models(self, epochs: int = 20):
        """Train all view models."""
        logger.info("\n" + "="*60)
        logger.info("TRAINING VIEW MODELS")
        logger.info("="*60)
        
        for view_name in self.view_names:
            self.train_view_model(view_name, epochs=epochs)
    
    def test_trained_models(self):
        """Test trained models on test set."""
        logger.info("\n" + "="*60)
        logger.info("TESTING TRAINED MODELS")
        logger.info("="*60)
        
        for view_name in self.view_names:
            logger.info(f"\nTesting trained {view_name} model...")
            
            # Load model if not in memory
            if view_name not in self.models:
                checkpoint_path = self.checkpoint_dir / f"{view_name}_model.pth"
                if checkpoint_path.exists():
                    model = SimpleViewModel()
                    checkpoint = torch.load(checkpoint_path)
                    model.load_state_dict(checkpoint['model_state_dict'])
                    self.models[view_name] = model
                else:
                    logger.warning(f"  No checkpoint found for {view_name}")
                    continue
            
            model = self.models[view_name]
            model.eval()
            
            # Create test dataset
            test_dataset = SimpleViewDataset(self.test_data, view_name)
            test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
            
            # Evaluate
            predictions = []
            targets = []
            
            with torch.no_grad():
                for batch in test_loader:
                    features = batch['features']
                    scores = batch['score']
                    
                    preds = model(features)
                    
                    predictions.extend(preds.cpu().numpy())
                    targets.extend(scores.cpu().numpy())
            
            # Calculate metrics
            mae = mean_absolute_error(targets, predictions)
            rmse = np.sqrt(mean_squared_error(targets, predictions))
            r2 = r2_score(targets, predictions)
            
            self.trained_results[view_name] = {
                'mae': mae,
                'rmse': rmse,
                'r2': r2,
                'predictions': predictions[:10],
                'targets': targets[:10]
            }
            
            logger.info(f"  Trained {view_name} - MAE: {mae:.4f}, RMSE: {rmse:.4f}, R²: {r2:.4f}")
    
    def compare_results(self):
        """Compare untrained vs trained performance."""
        logger.info("\n" + "="*60)
        logger.info("PERFORMANCE COMPARISON: UNTRAINED VS TRAINED")
        logger.info("="*60)
        
        comparison = {}
        
        for view_name in self.view_names:
            if view_name in self.untrained_results and view_name in self.trained_results:
                untrained = self.untrained_results[view_name]
                trained = self.trained_results[view_name]
                
                mae_improvement = (untrained['mae'] - trained['mae']) / untrained['mae'] * 100
                rmse_improvement = (untrained['rmse'] - trained['rmse']) / untrained['rmse'] * 100
                r2_improvement = trained['r2'] - untrained['r2']
                
                comparison[view_name] = {
                    'untrained_mae': untrained['mae'],
                    'trained_mae': trained['mae'],
                    'mae_improvement_pct': mae_improvement,
                    'untrained_rmse': untrained['rmse'],
                    'trained_rmse': trained['rmse'],
                    'rmse_improvement_pct': rmse_improvement,
                    'untrained_r2': untrained['r2'],
                    'trained_r2': trained['r2'],
                    'r2_improvement': r2_improvement
                }
                
                logger.info(f"\n{view_name.upper()} View:")
                logger.info(f"  MAE: {untrained['mae']:.4f} → {trained['mae']:.4f} ({mae_improvement:+.1f}%)")
                logger.info(f"  RMSE: {untrained['rmse']:.4f} → {trained['rmse']:.4f} ({rmse_improvement:+.1f}%)")
                logger.info(f"  R²: {untrained['r2']:.4f} → {trained['r2']:.4f} ({r2_improvement:+.4f})")
        
        # Overall summary
        avg_mae_improvement = np.mean([c['mae_improvement_pct'] for c in comparison.values()])
        avg_r2_improvement = np.mean([c['r2_improvement'] for c in comparison.values()])
        
        logger.info(f"\nOVERALL IMPROVEMENT:")
        logger.info(f"  Average MAE improvement: {avg_mae_improvement:.1f}%")
        logger.info(f"  Average R² improvement: {avg_r2_improvement:.4f}")
        
        return comparison
    
    def save_results(self):
        """Save all results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_path = Path(f"data/training/training_results_{timestamp}.json")
        
        results = {
            'timestamp': timestamp,
            'dataset_path': str(self.dataset_path),
            'checkpoint_dir': str(self.checkpoint_dir),
            'dataset_stats': {
                'total': len(self.dataset),
                'train': len(self.train_data),
                'val': len(self.val_data),
                'test': len(self.test_data)
            },
            'untrained_results': self.untrained_results,
            'trained_results': self.trained_results,
            'model_checkpoints': [str(f) for f in self.checkpoint_dir.glob("*.pth")]
        }
        
        # Convert numpy arrays to lists for JSON serialization
        def convert_numpy(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, (np.float32, np.float64)):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_numpy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(item) for item in obj]
            return obj
        
        results = convert_numpy(results)
        
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\nResults saved to: {results_path}")
        return results_path


def main():
    """Run complete training pipeline."""
    # Find latest dataset
    data_dir = Path("data/training")
    dataset_files = list(data_dir.glob("epic1_dataset_*.json"))
    
    if not dataset_files:
        logger.error("No dataset files found!")
        return
    
    latest_dataset = max(dataset_files, key=lambda p: p.stat().st_mtime)
    logger.info(f"Using dataset: {latest_dataset}")
    
    # Initialize trainer
    trainer = Epic1ModelTrainer(latest_dataset)
    
    # Run pipeline
    # 1. Test untrained models (baseline)
    trainer.test_untrained_baseline()
    
    # 2. Train models
    trainer.train_all_models(epochs=30)
    
    # 3. Test trained models
    trainer.test_trained_models()
    
    # 4. Compare results
    comparison = trainer.compare_results()
    
    # 5. Save everything
    results_path = trainer.save_results()
    
    logger.info("\n" + "="*60)
    logger.info("TRAINING COMPLETE!")
    logger.info(f"Models saved to: {trainer.checkpoint_dir}")
    logger.info(f"Results saved to: {results_path}")
    logger.info("="*60)


if __name__ == "__main__":
    main()