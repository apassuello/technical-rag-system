#!/usr/bin/env python3
"""
View Model Trainer for Epic 1 ML Models

This module implements training for individual view models (Technical, Linguistic, 
Task, Semantic, Computational) using transformer architectures.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from transformers import AutoModel, AutoTokenizer, get_linear_schedule_with_warmup
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error
import wandb
from tqdm import tqdm
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ViewComplexityModel(nn.Module):
    """
    Hybrid model combining transformer embeddings with handcrafted features
    for complexity prediction.
    """
    
    def __init__(
        self,
        model_name: str,
        num_features: int,
        num_classes: int = 3,
        hidden_dim: int = 256,
        dropout: float = 0.3
    ):
        super().__init__()
        
        # Load transformer model
        self.transformer = AutoModel.from_pretrained(model_name)
        self.transformer_dim = self.transformer.config.hidden_size
        
        # Feature fusion layers
        self.feature_projection = nn.Linear(num_features, hidden_dim)
        self.transformer_projection = nn.Linear(self.transformer_dim, hidden_dim)
        
        # Combined processing
        self.fusion_layer = nn.Linear(hidden_dim * 2, hidden_dim)
        self.dropout = nn.Dropout(dropout)
        
        # Output layers
        self.score_head = nn.Linear(hidden_dim, 1)  # Regression for complexity score
        self.class_head = nn.Linear(hidden_dim, num_classes)  # Classification
        
        # Initialize weights
        self._init_weights()
        
    def _init_weights(self):
        """Initialize linear layer weights."""
        for module in [self.feature_projection, self.transformer_projection, 
                      self.fusion_layer, self.score_head, self.class_head]:
            if hasattr(module, 'weight'):
                nn.init.xavier_uniform_(module.weight)
                nn.init.zeros_(module.bias)
    
    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        features: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass combining transformer and feature inputs.
        
        Args:
            input_ids: Tokenized input sequences
            attention_mask: Attention masks
            features: Handcrafted features
            
        Returns:
            Dictionary with score and class predictions
        """
        # Get transformer embeddings
        transformer_output = self.transformer(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        
        # Use [CLS] token embedding or mean pooling
        if hasattr(transformer_output, 'pooler_output') and transformer_output.pooler_output is not None:
            transformer_embedding = transformer_output.pooler_output
        else:
            # Mean pooling over sequence length
            transformer_embedding = transformer_output.last_hidden_state.mean(dim=1)
        
        # Project inputs
        feature_embedding = self.feature_projection(features)
        transformer_embedding = self.transformer_projection(transformer_embedding)
        
        # Fuse embeddings
        fused = torch.cat([feature_embedding, transformer_embedding], dim=1)
        fused = self.fusion_layer(fused)
        fused = torch.relu(fused)
        fused = self.dropout(fused)
        
        # Generate outputs
        score_pred = torch.sigmoid(self.score_head(fused))  # Complexity score (0-1)
        class_pred = self.class_head(fused)  # Class logits
        
        return {
            'complexity_score': score_pred.squeeze(-1),
            'complexity_class': class_pred
        }


class ViewTrainer:
    """Trainer for individual view models."""
    
    def __init__(
        self,
        view_name: str,
        model_config: Dict[str, Any],
        training_config: Dict[str, Any],
        device: str = None
    ):
        self.view_name = view_name
        self.model_config = model_config
        self.training_config = training_config
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Model mappings
        self.model_mappings = {
            'technical': 'allenai/scibert_scivocab_uncased',
            'linguistic': 'distilbert-base-uncased', 
            'task': 'microsoft/deberta-v3-base',
            'semantic': 'sentence-transformers/all-MiniLM-L6-v2',
            'computational': 't5-small'
        }
        
        # Initialize model and tokenizer
        self.model_name = self.model_mappings.get(view_name)
        self.tokenizer = None
        self.model = None
        
        # Training state
        self.best_val_loss = float('inf')
        self.training_history = {
            'train_loss': [],
            'val_loss': [],
            'train_accuracy': [],
            'val_accuracy': []
        }
        
        # Setup paths
        self.output_dir = Path(training_config.get('output_dir', f'models/{view_name}'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def setup_model(self, num_features: int) -> None:
        """Setup model and tokenizer."""
        if not self.model_name:
            raise ValueError(f"No model mapping found for view: {self.view_name}")
        
        logger.info(f"Setting up model for {self.view_name} view: {self.model_name}")
        
        # Load tokenizer with fallbacks
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        except Exception as e:
            logger.warning(f"Fast tokenizer failed for {self.model_name}: {e}")
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, use_fast=False)
            except Exception as e2:
                logger.error(f"Both tokenizers failed: {e2}")
                raise
        
        # Add padding token if missing
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token or '[PAD]'
        
        # Create model
        self.model = ViewComplexityModel(
            model_name=self.model_name,
            num_features=num_features,
            num_classes=3,
            hidden_dim=self.model_config.get('hidden_dim', 256),
            dropout=self.model_config.get('dropout', 0.3)
        )
        
        self.model.to(self.device)
        logger.info(f"Model setup complete, device: {self.device}")
        
    def train(
        self,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None
    ) -> Dict[str, Any]:
        """
        Train the view model.
        
        Args:
            train_loader: Training data loader
            val_loader: Validation data loader (optional)
            
        Returns:
            Training results and metrics
        """
        if self.model is None:
            raise ValueError("Model not initialized. Call setup_model() first.")
        
        # Setup training components
        num_epochs = self.training_config.get('num_epochs', 10)
        learning_rate = self.training_config.get('learning_rate', 2e-5)
        weight_decay = self.training_config.get('weight_decay', 0.01)
        
        # Optimizer and scheduler
        optimizer = optim.AdamW(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
        
        num_training_steps = len(train_loader) * num_epochs
        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=num_training_steps * 0.1,
            num_training_steps=num_training_steps
        )
        
        # Loss functions
        regression_loss_fn = nn.MSELoss()
        classification_loss_fn = nn.CrossEntropyLoss()
        
        # Training loop
        self.model.train()
        
        for epoch in range(num_epochs):
            train_loss = 0.0
            train_predictions = []
            train_targets = []
            
            progress_bar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{num_epochs}")
            
            for batch in progress_bar:
                # Move batch to device
                batch = {k: v.to(self.device) for k, v in batch.items()}
                
                optimizer.zero_grad()
                
                # Forward pass
                outputs = self.model(
                    input_ids=batch['input_ids'],
                    attention_mask=batch['attention_mask'],
                    features=batch['features']
                )
                
                # Calculate losses
                reg_loss = regression_loss_fn(
                    outputs['complexity_score'],
                    batch['complexity_score']
                )
                
                class_loss = classification_loss_fn(
                    outputs['complexity_class'],
                    batch['complexity_level']
                )
                
                # Combined loss
                loss = reg_loss + class_loss
                
                # Backward pass
                loss.backward()
                optimizer.step()
                scheduler.step()
                
                # Track metrics
                train_loss += loss.item()
                
                # For accuracy calculation
                class_preds = torch.argmax(outputs['complexity_class'], dim=1)
                train_predictions.extend(class_preds.cpu().numpy())
                train_targets.extend(batch['complexity_level'].cpu().numpy())
                
                # Update progress bar
                progress_bar.set_postfix({'loss': f'{loss.item():.4f}'})
            
            # Calculate epoch metrics
            avg_train_loss = train_loss / len(train_loader)
            train_accuracy = accuracy_score(train_targets, train_predictions)
            
            self.training_history['train_loss'].append(avg_train_loss)
            self.training_history['train_accuracy'].append(train_accuracy)
            
            # Validation
            val_loss = 0.0
            val_accuracy = 0.0
            
            if val_loader:
                val_metrics = self._validate(val_loader, regression_loss_fn, classification_loss_fn)
                val_loss = val_metrics['loss']
                val_accuracy = val_metrics['accuracy']
                
                self.training_history['val_loss'].append(val_loss)
                self.training_history['val_accuracy'].append(val_accuracy)
                
                # Save best model
                if val_loss < self.best_val_loss:
                    self.best_val_loss = val_loss
                    self._save_checkpoint(epoch, is_best=True)
            
            # Log epoch results
            logger.info(f"Epoch {epoch+1}/{num_epochs}:")
            logger.info(f"  Train Loss: {avg_train_loss:.4f}, Train Acc: {train_accuracy:.4f}")
            if val_loader:
                logger.info(f"  Val Loss: {val_loss:.4f}, Val Acc: {val_accuracy:.4f}")
        
        # Save final model
        self._save_checkpoint(num_epochs, is_final=True)
        
        # Generate training report
        training_results = {
            'view_name': self.view_name,
            'final_train_loss': self.training_history['train_loss'][-1],
            'final_train_accuracy': self.training_history['train_accuracy'][-1],
            'best_val_loss': self.best_val_loss,
            'training_history': self.training_history
        }
        
        if val_loader:
            training_results['final_val_loss'] = self.training_history['val_loss'][-1]
            training_results['final_val_accuracy'] = self.training_history['val_accuracy'][-1]
        
        # Save training history
        self._save_training_results(training_results)
        
        return training_results
    
    def _validate(
        self,
        val_loader: DataLoader,
        regression_loss_fn: nn.Module,
        classification_loss_fn: nn.Module
    ) -> Dict[str, float]:
        """Run validation."""
        self.model.eval()
        
        val_loss = 0.0
        val_predictions = []
        val_targets = []
        
        with torch.no_grad():
            for batch in val_loader:
                # Move batch to device
                batch = {k: v.to(self.device) for k, v in batch.items()}
                
                # Forward pass
                outputs = self.model(
                    input_ids=batch['input_ids'],
                    attention_mask=batch['attention_mask'],
                    features=batch['features']
                )
                
                # Calculate losses
                reg_loss = regression_loss_fn(
                    outputs['complexity_score'],
                    batch['complexity_score']
                )
                
                class_loss = classification_loss_fn(
                    outputs['complexity_class'],
                    batch['complexity_level']
                )
                
                loss = reg_loss + class_loss
                val_loss += loss.item()
                
                # For accuracy calculation
                class_preds = torch.argmax(outputs['complexity_class'], dim=1)
                val_predictions.extend(class_preds.cpu().numpy())
                val_targets.extend(batch['complexity_level'].cpu().numpy())
        
        self.model.train()
        
        avg_val_loss = val_loss / len(val_loader)
        val_accuracy = accuracy_score(val_targets, val_predictions)
        
        return {
            'loss': avg_val_loss,
            'accuracy': val_accuracy,
            'predictions': val_predictions,
            'targets': val_targets
        }
    
    def _save_checkpoint(self, epoch: int, is_best: bool = False, is_final: bool = False) -> None:
        """Save model checkpoint."""
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'view_name': self.view_name,
            'model_name': self.model_name,
            'training_history': self.training_history,
            'model_config': self.model_config,
            'training_config': self.training_config
        }
        
        if is_best:
            checkpoint_path = self.output_dir / 'best_model.pt'
            torch.save(checkpoint, checkpoint_path)
            logger.info(f"Saved best model to {checkpoint_path}")
        
        if is_final:
            checkpoint_path = self.output_dir / 'final_model.pt'
            torch.save(checkpoint, checkpoint_path)
            logger.info(f"Saved final model to {checkpoint_path}")
    
    def _save_training_results(self, results: Dict[str, Any]) -> None:
        """Save training results and plots."""
        # Save results JSON
        results_path = self.output_dir / 'training_results.json'
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Create training plots
        self._plot_training_history()
    
    def _plot_training_history(self) -> None:
        """Plot training history."""
        fig, axes = plt.subplots(1, 2, figsize=(15, 5))
        
        # Loss plot
        axes[0].plot(self.training_history['train_loss'], label='Train Loss', marker='o')
        if self.training_history['val_loss']:
            axes[0].plot(self.training_history['val_loss'], label='Val Loss', marker='s')
        axes[0].set_title(f'{self.view_name} View - Training Loss')
        axes[0].set_xlabel('Epoch')
        axes[0].set_ylabel('Loss')
        axes[0].legend()
        axes[0].grid(True)
        
        # Accuracy plot
        axes[1].plot(self.training_history['train_accuracy'], label='Train Accuracy', marker='o')
        if self.training_history['val_accuracy']:
            axes[1].plot(self.training_history['val_accuracy'], label='Val Accuracy', marker='s')
        axes[1].set_title(f'{self.view_name} View - Training Accuracy')
        axes[1].set_xlabel('Epoch')
        axes[1].set_ylabel('Accuracy')
        axes[1].legend()
        axes[1].grid(True)
        
        plt.tight_layout()
        
        # Save plot
        plot_path = self.output_dir / 'training_history.png'
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved training plots to {plot_path}")
    
    def load_model(self, checkpoint_path: Path, num_features: int) -> None:
        """Load trained model from checkpoint."""
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
        
        # Setup model first
        self.setup_model(num_features)
        
        # Load checkpoint
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.training_history = checkpoint.get('training_history', {})
        
        logger.info(f"Loaded model from {checkpoint_path}")
    
    def predict(self, data_loader: DataLoader) -> Dict[str, np.ndarray]:
        """Make predictions on data."""
        if self.model is None:
            raise ValueError("Model not loaded. Call setup_model() or load_model() first.")
        
        self.model.eval()
        
        all_score_preds = []
        all_class_preds = []
        all_targets = []
        
        with torch.no_grad():
            for batch in data_loader:
                # Move batch to device
                batch = {k: v.to(self.device) for k, v in batch.items()}
                
                # Forward pass
                outputs = self.model(
                    input_ids=batch['input_ids'],
                    attention_mask=batch['attention_mask'],
                    features=batch['features']
                )
                
                # Collect predictions
                score_preds = outputs['complexity_score'].cpu().numpy()
                class_preds = torch.argmax(outputs['complexity_class'], dim=1).cpu().numpy()
                targets = batch['complexity_level'].cpu().numpy()
                
                all_score_preds.extend(score_preds)
                all_class_preds.extend(class_preds)
                all_targets.extend(targets)
        
        return {
            'score_predictions': np.array(all_score_preds),
            'class_predictions': np.array(all_class_preds),
            'targets': np.array(all_targets)
        }


def main():
    """Example training script for a single view."""
    # Configuration
    training_config = {
        'num_epochs': 5,
        'learning_rate': 2e-5,
        'weight_decay': 0.01,
        'output_dir': 'models/technical'
    }
    
    model_config = {
        'hidden_dim': 256,
        'dropout': 0.3
    }
    
    # Create trainer
    trainer = ViewTrainer(
        view_name='technical',
        model_config=model_config,
        training_config=training_config
    )
    
    # Setup model (num_features would come from data loader)
    trainer.setup_model(num_features=5)
    
    logger.info(f"Created trainer for {trainer.view_name} view")
    logger.info(f"Model: {trainer.model_name}")
    logger.info(f"Device: {trainer.device}")


if __name__ == "__main__":
    main()