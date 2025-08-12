#!/usr/bin/env python3
"""
Detailed Testing of Trained Epic 1 Models

Test the trained models on a small, diverse set of queries and examine outputs closely.
"""

import json
import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List, Tuple
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


class DetailedModelTester:
    """Test trained models with detailed output analysis."""
    
    def __init__(self, checkpoint_dir: str = "models/epic1"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.view_names = ['technical', 'linguistic', 'task', 'semantic', 'computational']
        self.models = {}
        
        # Load all models
        self._load_models()
        
        # Test queries covering different complexity levels
        self.test_queries = [
            # Simple queries
            {
                "query": "How do I create a list in Python?",
                "expected_level": "simple",
                "expected_range": (0.1, 0.3)
            },
            {
                "query": "What is a variable?",
                "expected_level": "simple",
                "expected_range": (0.1, 0.25)
            },
            
            # Medium queries
            {
                "query": "How can I optimize database queries with multiple JOINs for better performance?",
                "expected_level": "medium",
                "expected_range": (0.4, 0.6)
            },
            {
                "query": "What's the difference between REST and GraphQL APIs in microservices architecture?",
                "expected_level": "medium",
                "expected_range": (0.45, 0.65)
            },
            
            # Complex queries
            {
                "query": "How would you design a distributed consensus algorithm with Byzantine fault tolerance for a blockchain system?",
                "expected_level": "complex",
                "expected_range": (0.7, 0.9)
            },
            {
                "query": "Explain the implementation of a lock-free concurrent data structure using compare-and-swap operations for high-throughput systems.",
                "expected_level": "complex",
                "expected_range": (0.75, 0.95)
            },
            
            # Edge cases
            {
                "query": "Help",
                "expected_level": "simple",
                "expected_range": (0.05, 0.2)
            },
            {
                "query": "What are the trade-offs between different approaches to implementing distributed tracing in a microservices architecture with heterogeneous technology stacks, considering both performance overhead and observability requirements?",
                "expected_level": "complex",
                "expected_range": (0.8, 0.95)
            }
        ]
    
    def _load_models(self):
        """Load all trained models from checkpoints."""
        logger.info("Loading trained models...")
        
        for view_name in self.view_names:
            checkpoint_path = self.checkpoint_dir / f"{view_name}_model.pth"
            if checkpoint_path.exists():
                model = SimpleViewModel()
                checkpoint = torch.load(checkpoint_path)
                model.load_state_dict(checkpoint['model_state_dict'])
                model.eval()
                self.models[view_name] = model
                logger.info(f"  Loaded {view_name} model (val_mae: {checkpoint.get('val_mae', 'N/A'):.4f})")
            else:
                logger.warning(f"  No checkpoint found for {view_name}")
    
    def _extract_simple_features(self, query: str) -> np.ndarray:
        """Extract simple features from query (must match training)."""
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
    
    def predict_complexity(self, query: str) -> Dict[str, float]:
        """Predict complexity scores for all views."""
        features = self._extract_simple_features(query)
        features_tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0)
        
        predictions = {}
        with torch.no_grad():
            for view_name, model in self.models.items():
                score = model(features_tensor).item()
                predictions[view_name] = score
        
        return predictions
    
    def calculate_final_score(self, view_scores: Dict[str, float]) -> Tuple[float, str]:
        """Calculate final complexity score and level (matching training fusion)."""
        weights = {
            'technical': 0.30,
            'linguistic': 0.15,
            'task': 0.25,
            'semantic': 0.15,
            'computational': 0.15
        }
        
        final_score = sum(view_scores.get(view, 0) * weights.get(view, 0) 
                         for view in self.view_names)
        
        # Determine level
        if final_score < 0.33:
            level = "simple"
        elif final_score < 0.67:
            level = "medium"
        else:
            level = "complex"
        
        return final_score, level
    
    def test_queries_detailed(self):
        """Test queries with detailed output analysis."""
        logger.info("\n" + "="*80)
        logger.info("DETAILED MODEL TESTING ON SAMPLE QUERIES")
        logger.info("="*80)
        
        results = []
        
        for i, test_case in enumerate(self.test_queries, 1):
            query = test_case["query"]
            expected_level = test_case["expected_level"]
            expected_range = test_case["expected_range"]
            
            print(f"\n{'='*80}")
            print(f"Query {i}: {query[:100]}{'...' if len(query) > 100 else ''}")
            print(f"Expected: {expected_level} (score range: {expected_range[0]:.2f}-{expected_range[1]:.2f})")
            print("-"*80)
            
            # Get predictions
            view_scores = self.predict_complexity(query)
            final_score, predicted_level = self.calculate_final_score(view_scores)
            
            # Extract features for display
            features = self._extract_simple_features(query)
            
            # Display features
            print("\nExtracted Features:")
            feature_names = ["Char count", "Word count", "Avg word len", "Questions", 
                           "Commas", "Long words", "Capitals", "Conjunctions"]
            for fname, fval in zip(feature_names, features):
                print(f"  {fname:15}: {fval:6.2f}")
            
            # Display view scores
            print("\nView Predictions:")
            for view_name in self.view_names:
                score = view_scores[view_name]
                indicator = "✓" if expected_range[0] <= score <= expected_range[1] else "✗"
                print(f"  {view_name:15}: {score:.4f} {indicator}")
            
            # Display final results
            print(f"\nFinal Score: {final_score:.4f}")
            print(f"Predicted Level: {predicted_level}")
            print(f"Expected Level: {expected_level}")
            
            # Check if prediction is reasonable
            level_match = predicted_level == expected_level
            score_in_range = expected_range[0] <= final_score <= expected_range[1]
            
            if level_match and score_in_range:
                print("Result: ✅ CORRECT (level matches and score in expected range)")
            elif level_match:
                print(f"Result: ⚠️  PARTIAL (level matches but score {final_score:.3f} outside range)")
            elif score_in_range:
                print(f"Result: ⚠️  PARTIAL (score in range but level mismatch: {predicted_level} vs {expected_level})")
            else:
                print(f"Result: ❌ INCORRECT (level: {predicted_level} vs {expected_level}, score: {final_score:.3f})")
            
            # Store results
            results.append({
                "query": query[:50] + "..." if len(query) > 50 else query,
                "expected_level": expected_level,
                "predicted_level": predicted_level,
                "final_score": final_score,
                "score_in_range": score_in_range,
                "level_match": level_match,
                "view_scores": view_scores
            })
        
        # Summary statistics
        print(f"\n{'='*80}")
        print("SUMMARY STATISTICS")
        print("="*80)
        
        correct_levels = sum(1 for r in results if r["level_match"])
        correct_ranges = sum(1 for r in results if r["score_in_range"])
        total = len(results)
        
        print(f"Level Accuracy: {correct_levels}/{total} ({correct_levels/total*100:.1f}%)")
        print(f"Score in Range: {correct_ranges}/{total} ({correct_ranges/total*100:.1f}%)")
        
        # Per-level analysis
        for level in ["simple", "medium", "complex"]:
            level_results = [r for r in results if r["expected_level"] == level]
            if level_results:
                avg_score = np.mean([r["final_score"] for r in level_results])
                correct = sum(1 for r in level_results if r["level_match"])
                print(f"\n{level.capitalize()} queries:")
                print(f"  Count: {len(level_results)}")
                print(f"  Avg Score: {avg_score:.3f}")
                print(f"  Accuracy: {correct}/{len(level_results)} ({correct/len(level_results)*100:.0f}%)")
        
        # View consistency analysis
        print("\nView Consistency (std dev of view scores per query):")
        for i, result in enumerate(results, 1):
            scores = list(result["view_scores"].values())
            std_dev = np.std(scores)
            consistency = "High" if std_dev < 0.1 else "Medium" if std_dev < 0.2 else "Low"
            print(f"  Query {i}: {std_dev:.3f} ({consistency})")
        
        return results
    
    def test_on_dataset_samples(self, dataset_path: str = None, num_samples: int = 10):
        """Test on random samples from the original dataset."""
        if dataset_path is None:
            # Find latest dataset
            data_dir = Path("data/training")
            dataset_files = list(data_dir.glob("epic1_dataset_*.json"))
            if not dataset_files:
                logger.error("No dataset files found!")
                return
            dataset_path = max(dataset_files, key=lambda p: p.stat().st_mtime)
        
        logger.info(f"\nTesting on samples from: {dataset_path}")
        
        with open(dataset_path, 'r') as f:
            dataset = json.load(f)
        
        # Sample randomly
        import random
        samples = random.sample(dataset, min(num_samples, len(dataset)))
        
        print(f"\n{'='*80}")
        print(f"TESTING ON {len(samples)} DATASET SAMPLES")
        print("="*80)
        
        errors = []
        
        for i, sample in enumerate(samples, 1):
            query = sample['query_text']
            expected_scores = sample['view_scores']
            expected_final = sample['expected_complexity_score']
            
            # Get predictions
            predicted_scores = self.predict_complexity(query)
            predicted_final, predicted_level = self.calculate_final_score(predicted_scores)
            
            print(f"\nSample {i}:")
            print(f"Query: {query[:80]}{'...' if len(query) > 80 else ''}")
            print(f"Expected Level: {sample['expected_complexity_level']}")
            print(f"Predicted Level: {predicted_level}")
            
            # Calculate errors
            view_errors = {}
            print("\nView Score Comparison (Expected → Predicted [Error]):")
            for view in self.view_names:
                expected = expected_scores[view]
                predicted = predicted_scores[view]
                error = abs(expected - predicted)
                view_errors[view] = error
                
                indicator = "✓" if error < 0.1 else "⚠" if error < 0.2 else "✗"
                print(f"  {view:15}: {expected:.3f} → {predicted:.3f} [{error:.3f}] {indicator}")
            
            # Final score comparison
            final_error = abs(expected_final - predicted_final)
            print(f"\nFinal Score: {expected_final:.3f} → {predicted_final:.3f} [Error: {final_error:.3f}]")
            
            errors.append({
                'final_error': final_error,
                'view_errors': view_errors,
                'avg_view_error': np.mean(list(view_errors.values()))
            })
        
        # Calculate statistics
        print(f"\n{'='*80}")
        print("ERROR STATISTICS")
        print("="*80)
        
        avg_final_error = np.mean([e['final_error'] for e in errors])
        avg_view_errors = {
            view: np.mean([e['view_errors'][view] for e in errors])
            for view in self.view_names
        }
        
        print(f"Average Final Score Error: {avg_final_error:.4f}")
        print("\nAverage View Errors:")
        for view, error in avg_view_errors.items():
            print(f"  {view:15}: {error:.4f}")
        
        return errors


def main():
    """Run detailed model testing."""
    tester = DetailedModelTester()
    
    # Test on predefined queries
    results = tester.test_queries_detailed()
    
    # Test on dataset samples
    errors = tester.test_on_dataset_samples(num_samples=10)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = Path(f"data/training/detailed_test_results_{timestamp}.json")
    
    with open(results_path, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'manual_test_results': results,
            'dataset_sample_errors': errors if errors else []
        }, f, indent=2)
    
    logger.info(f"\nResults saved to: {results_path}")


if __name__ == "__main__":
    main()