#!/usr/bin/env python3
"""
Training Data Loader and Preprocessor for Epic 1 ML Models

This module loads Claude-generated training data and preprocesses it
for training the 5 ML view models.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from dataclasses import dataclass
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TrainingExample:
    """Single training example for a view model."""
    query_text: str
    features: np.ndarray
    complexity_score: float
    complexity_level: str
    view_name: str
    metadata: Dict[str, Any]


class ViewDataset(Dataset):
    """PyTorch dataset for training a single view model."""
    
    def __init__(
        self,
        examples: List[TrainingExample],
        tokenizer: Any,
        max_length: int = 512,
        view_name: str = None
    ):
        self.examples = examples
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.view_name = view_name
        
        # Extract features and labels
        self.queries = [ex.query_text for ex in examples]
        self.features = np.array([ex.features for ex in examples])
        self.scores = np.array([ex.complexity_score for ex in examples])
        self.levels = [ex.complexity_level for ex in examples]
        
        # Convert levels to numeric
        self.level_to_idx = {"simple": 0, "medium": 1, "complex": 2}
        self.level_indices = np.array([self.level_to_idx[level] for level in self.levels])
        
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        """Get a single training example."""
        query = self.queries[idx]
        features = self.features[idx]
        score = self.scores[idx]
        level_idx = self.level_indices[idx]
        
        # Tokenize query
        encoding = self.tokenizer(
            query,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'features': torch.tensor(features, dtype=torch.float32),
            'complexity_score': torch.tensor(score, dtype=torch.float32),
            'complexity_level': torch.tensor(level_idx, dtype=torch.long)
        }


class Epic1DataLoader:
    """Main data loader for Epic 1 training."""
    
    def __init__(self, data_path: Path):
        """
        Initialize data loader.
        
        Args:
            data_path: Path to the JSON dataset file
        """
        self.data_path = Path(data_path)
        self.raw_data = None
        self.view_datasets = {}
        self.feature_scalers = {}
        
        # View-specific feature definitions
        self.view_features = {
            'technical': [
                'technical_terms_count', 'domain_specificity_score', 
                'jargon_density', 'concept_depth', 'passive_voice_ratio'
            ],
            'linguistic': [
                'avg_sentence_length', 'syntactic_depth', 'clause_complexity',
                'abstract_concept_ratio', 'lexical_diversity'
            ],
            'task': [
                'primary_bloom_level', 'cognitive_load', 'task_scope',
                'solution_steps', 'creativity_required'
            ],
            'semantic': [
                'concept_density', 'relationship_complexity', 'abstraction_level',
                'context_dependency', 'implicit_knowledge'
            ],
            'computational': [
                'algorithm_mentions', 'complexity_class', 'data_structure_count',
                'implementation_difficulty', 'optimization_aspects'
            ]
        }
        
    def load_dataset(self) -> None:
        """Load the dataset from JSON file."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Dataset not found at {self.data_path}")
        
        with open(self.data_path, 'r') as f:
            self.raw_data = json.load(f)
        
        logger.info(f"Loaded {len(self.raw_data)} training examples from {self.data_path}")
        
    def preprocess_data(self) -> Dict[str, List[TrainingExample]]:
        """
        Preprocess data for all views.
        
        Returns:
            Dictionary mapping view names to lists of TrainingExamples
        """
        if self.raw_data is None:
            self.load_dataset()
        
        view_examples = {
            'technical': [],
            'linguistic': [],
            'task': [],
            'semantic': [],
            'computational': []
        }
        
        for datapoint in self.raw_data:
            query_text = datapoint['query_text']
            expected_score = datapoint['expected_complexity_score']
            expected_level = datapoint['expected_complexity_level']
            
            # Process each view
            for view_name in view_examples.keys():
                view_data = datapoint['view_scores'].get(view_name, {})
                
                if not view_data:
                    continue
                
                # Extract features for this view
                features = self._extract_view_features(view_data, view_name)
                
                # Create training example
                example = TrainingExample(
                    query_text=query_text,
                    features=features,
                    complexity_score=view_data.get('complexity_score', expected_score),
                    complexity_level=expected_level,
                    view_name=view_name,
                    metadata={
                        'confidence': view_data.get('confidence', 0.8),
                        'reasoning': view_data.get('reasoning', ''),
                        'domain': datapoint['metadata'].get('domain', 'general')
                    }
                )
                
                view_examples[view_name].append(example)
        
        # Log statistics
        for view_name, examples in view_examples.items():
            logger.info(f"View '{view_name}': {len(examples)} examples")
            
        return view_examples
    
    def _extract_view_features(self, view_data: Dict[str, Any], view_name: str) -> np.ndarray:
        """
        Extract feature vector for a specific view.
        
        Args:
            view_data: View-specific data from dataset
            view_name: Name of the view
            
        Returns:
            Numpy array of features
        """
        feature_names = self.view_features.get(view_name, [])
        feature_values = view_data.get('feature_values', {})
        
        features = []
        for feature_name in feature_names:
            value = feature_values.get(feature_name, 0.0)
            # Handle None values
            if value is None:
                value = 0.0
            features.append(float(value))
        
        return np.array(features)
    
    def create_train_val_split(
        self,
        view_examples: Dict[str, List[TrainingExample]],
        val_ratio: float = 0.2,
        random_state: int = 42
    ) -> Dict[str, Tuple[List[TrainingExample], List[TrainingExample]]]:
        """
        Create train/validation splits for each view.
        
        Args:
            view_examples: Dictionary of view examples
            val_ratio: Ratio of validation data
            random_state: Random seed for reproducibility
            
        Returns:
            Dictionary mapping view names to (train, val) tuples
        """
        splits = {}
        
        for view_name, examples in view_examples.items():
            if len(examples) < 10:
                logger.warning(f"View '{view_name}' has only {len(examples)} examples, using all for training")
                splits[view_name] = (examples, [])
                continue
            
            # Stratified split by complexity level
            levels = [ex.complexity_level for ex in examples]
            
            train_examples, val_examples = train_test_split(
                examples,
                test_size=val_ratio,
                stratify=levels,
                random_state=random_state
            )
            
            splits[view_name] = (train_examples, val_examples)
            
            logger.info(f"View '{view_name}': {len(train_examples)} train, {len(val_examples)} val")
        
        return splits
    
    def normalize_features(
        self,
        view_splits: Dict[str, Tuple[List[TrainingExample], List[TrainingExample]]]
    ) -> Dict[str, Tuple[List[TrainingExample], List[TrainingExample]]]:
        """
        Normalize features for each view using StandardScaler.
        
        Args:
            view_splits: Dictionary of train/val splits
            
        Returns:
            Dictionary with normalized features
        """
        normalized_splits = {}
        
        for view_name, (train_examples, val_examples) in view_splits.items():
            if not train_examples:
                continue
            
            # Fit scaler on training data
            train_features = np.array([ex.features for ex in train_examples])
            scaler = StandardScaler()
            scaler.fit(train_features)
            
            # Store scaler for later use
            self.feature_scalers[view_name] = scaler
            
            # Transform training features
            normalized_train_features = scaler.transform(train_features)
            for i, ex in enumerate(train_examples):
                ex.features = normalized_train_features[i]
            
            # Transform validation features
            if val_examples:
                val_features = np.array([ex.features for ex in val_examples])
                normalized_val_features = scaler.transform(val_features)
                for i, ex in enumerate(val_examples):
                    ex.features = normalized_val_features[i]
            
            normalized_splits[view_name] = (train_examples, val_examples)
            
        return normalized_splits
    
    def create_dataloaders(
        self,
        view_splits: Dict[str, Tuple[List[TrainingExample], List[TrainingExample]]],
        tokenizers: Dict[str, Any],
        batch_size: int = 16,
        num_workers: int = 4
    ) -> Dict[str, Tuple[DataLoader, DataLoader]]:
        """
        Create PyTorch DataLoaders for each view.
        
        Args:
            view_splits: Dictionary of train/val splits
            tokenizers: Dictionary mapping view names to tokenizers
            batch_size: Batch size for training
            num_workers: Number of data loading workers
            
        Returns:
            Dictionary mapping view names to (train_loader, val_loader) tuples
        """
        dataloaders = {}
        
        for view_name, (train_examples, val_examples) in view_splits.items():
            if not train_examples:
                continue
            
            tokenizer = tokenizers.get(view_name)
            if tokenizer is None:
                logger.warning(f"No tokenizer provided for view '{view_name}', skipping")
                continue
            
            # Create datasets
            train_dataset = ViewDataset(train_examples, tokenizer, view_name=view_name)
            val_dataset = ViewDataset(val_examples, tokenizer, view_name=view_name) if val_examples else None
            
            # Create dataloaders
            train_loader = DataLoader(
                train_dataset,
                batch_size=batch_size,
                shuffle=True,
                num_workers=num_workers,
                pin_memory=True
            )
            
            val_loader = None
            if val_dataset:
                val_loader = DataLoader(
                    val_dataset,
                    batch_size=batch_size,
                    shuffle=False,
                    num_workers=num_workers,
                    pin_memory=True
                )
            
            dataloaders[view_name] = (train_loader, val_loader)
            
            logger.info(f"Created dataloaders for view '{view_name}'")
        
        return dataloaders
    
    def get_class_weights(self, view_name: str) -> torch.Tensor:
        """
        Calculate class weights for imbalanced data.
        
        Args:
            view_name: Name of the view
            
        Returns:
            Tensor of class weights
        """
        if view_name not in self.view_datasets:
            return None
        
        dataset = self.view_datasets[view_name]
        levels = dataset.level_indices
        
        # Calculate class frequencies
        unique, counts = np.unique(levels, return_counts=True)
        
        # Calculate weights (inverse frequency)
        weights = 1.0 / counts
        weights = weights / weights.sum() * len(unique)
        
        return torch.tensor(weights, dtype=torch.float32)
    
    def get_feature_names(self, view_name: str) -> List[str]:
        """Get feature names for a specific view."""
        return self.view_features.get(view_name, [])
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get dataset statistics."""
        if self.raw_data is None:
            return {}
        
        stats = {
            'total_samples': len(self.raw_data),  # Fixed: was 'total_examples'
            'total_examples': len(self.raw_data), # Keep both for compatibility
            'complexity_distribution': {},
            'domain_distribution': {},
            'view_statistics': {}
        }
        
        # Calculate distributions
        complexity_counts = {}
        domain_counts = {}
        
        for datapoint in self.raw_data:
            level = datapoint['expected_complexity_level']
            complexity_counts[level] = complexity_counts.get(level, 0) + 1
            
            domain = datapoint['metadata'].get('domain', 'unknown')
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        stats['complexity_distribution'] = complexity_counts
        stats['domain_distribution'] = domain_counts
        
        # Calculate view statistics
        for view_name in ['technical', 'linguistic', 'task', 'semantic', 'computational']:
            view_scores = []
            for datapoint in self.raw_data:
                view_data = datapoint['view_scores'].get(view_name, {})
                if view_data:
                    view_scores.append(view_data.get('complexity_score', 0))
            
            if view_scores:
                stats['view_statistics'][view_name] = {
                    'mean': np.mean(view_scores),
                    'std': np.std(view_scores),
                    'min': np.min(view_scores),
                    'max': np.max(view_scores)
                }
        
        return stats


def main():
    """Example usage of the data loader."""
    # Path to generated dataset
    data_path = Path("data/training/epic1_dataset_20250108_120000.json")
    
    # Initialize loader
    loader = Epic1DataLoader(data_path)
    
    # Load and preprocess data
    loader.load_dataset()
    view_examples = loader.preprocess_data()
    
    # Create train/val splits
    view_splits = loader.create_train_val_split(view_examples)
    
    # Normalize features
    normalized_splits = loader.normalize_features(view_splits)
    
    # Get statistics
    stats = loader.get_statistics()
    logger.info("\nDataset Statistics:")
    logger.info(f"Total examples: {stats['total_examples']}")
    logger.info(f"Complexity distribution: {stats['complexity_distribution']}")
    logger.info(f"Domain distribution: {stats['domain_distribution']}")
    
    for view_name, view_stats in stats['view_statistics'].items():
        logger.info(f"\n{view_name} view:")
        logger.info(f"  Mean score: {view_stats['mean']:.3f}")
        logger.info(f"  Std dev: {view_stats['std']:.3f}")
        logger.info(f"  Range: [{view_stats['min']:.3f}, {view_stats['max']:.3f}]")


if __name__ == "__main__":
    main()