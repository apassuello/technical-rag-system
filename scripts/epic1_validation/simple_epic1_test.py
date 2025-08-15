#!/usr/bin/env python3
"""
Simple Epic 1 Classifier Test

A minimal script to test Epic 1 classifier performance on external datasets
without external dependencies like matplotlib or seaborn.
"""

import json
import sys
import numpy as np
from pathlib import Path
from datetime import datetime

# Import the predictor
sys.path.append('models/epic1')
from epic1_predictor import Epic1Predictor

def test_epic1_classifier(test_dataset_path, model_dir="models/epic1"):
    """
    Simple test function for Epic 1 classifier.
    
    Args:
        test_dataset_path: Path to test dataset JSON
        model_dir: Directory containing trained models
    """
    print("🤖 Epic 1 Classifier - Simple Test")
    print("=" * 50)
    
    # Load test data
    with open(test_dataset_path, 'r') as f:
        test_data = json.load(f)
    
    print(f"📊 Loaded test dataset: {len(test_data)} samples")
    
    # Initialize predictor
    predictor = Epic1Predictor(model_dir)
    print(f"🔧 Using fusion method: {predictor.best_method}")
    
    # Run predictions
    predictions = []
    ground_truth_scores = []
    ground_truth_levels = []
    predicted_scores = []
    predicted_levels = []
    
    print("\\n⏳ Running predictions...")
    for i, sample in enumerate(test_data):
        if i % 50 == 0:
            print(f"  Progress: {i}/{len(test_data)}")
        
        try:
            result = predictor.predict(sample['query_text'])
            
            predictions.append(result)
            ground_truth_scores.append(sample['expected_complexity_score'])
            ground_truth_levels.append(sample['expected_complexity_level'])
            predicted_scores.append(result['complexity_score'])
            predicted_levels.append(result['complexity_level'])
            
        except Exception as e:
            print(f"❌ Error on sample {i}: {e}")
    
    print(f"✅ Completed: {len(predictions)} predictions")
    
    # Calculate metrics
    print("\\n📈 Performance Metrics:")
    
    # Score prediction metrics
    mae = np.mean(np.abs(np.array(predicted_scores) - np.array(ground_truth_scores)))
    rmse = np.sqrt(np.mean((np.array(predicted_scores) - np.array(ground_truth_scores))**2))
    
    errors = np.abs(np.array(predicted_scores) - np.array(ground_truth_scores))
    within_005 = np.sum(errors < 0.05) / len(errors) * 100
    within_010 = np.sum(errors < 0.10) / len(errors) * 100
    
    print(f"  📊 Score Prediction:")
    print(f"    MAE: {mae:.4f}")
    print(f"    RMSE: {rmse:.4f}")
    print(f"    Within ±0.05: {within_005:.1f}%")
    print(f"    Within ±0.10: {within_010:.1f}%")
    
    # Classification metrics
    correct_classifications = sum(1 for p, g in zip(predicted_levels, ground_truth_levels) if p == g)
    accuracy = correct_classifications / len(predicted_levels) * 100
    
    print(f"  🎯 Level Classification:")
    print(f"    Overall Accuracy: {accuracy:.1f}%")
    print(f"    Correct: {correct_classifications}/{len(predicted_levels)}")
    
    # Per-level breakdown
    levels = ['simple', 'medium', 'complex']
    for level in levels:
        level_indices = [i for i, gt in enumerate(ground_truth_levels) if gt == level]
        if level_indices:
            level_correct = sum(1 for i in level_indices if predicted_levels[i] == level)
            level_accuracy = level_correct / len(level_indices) * 100
            print(f"    {level.capitalize()}: {level_accuracy:.1f}% ({level_correct}/{len(level_indices)})")
    
    # Show some example predictions
    print("\\n🔍 Example Predictions:")
    for i in range(min(3, len(predictions))):
        result = predictions[i]
        sample = test_data[i]
        print(f"\\n  Example {i+1}:")
        query = sample['query_text']
        if len(query) > 80:
            query = query[:80] + "..."
        print(f"    Query: {query}")
        print(f"    Ground Truth: {sample['expected_complexity_score']:.3f} ({sample['expected_complexity_level']})")
        print(f"    Predicted: {result['complexity_score']:.3f} ({result['complexity_level']})")
        print(f"    Error: {abs(result['complexity_score'] - sample['expected_complexity_score']):.3f}")
    
    # Find worst predictions
    abs_errors = np.abs(np.array(predicted_scores) - np.array(ground_truth_scores))
    worst_idx = np.argmax(abs_errors)
    
    print(f"\\n⚠️  Worst Prediction:")
    worst_sample = test_data[worst_idx]
    worst_result = predictions[worst_idx]
    worst_query = worst_sample['query_text']
    if len(worst_query) > 100:
        worst_query = worst_query[:100] + "..."
    
    print(f"    Query: {worst_query}")
    print(f"    Ground Truth: {worst_sample['expected_complexity_score']:.3f} ({worst_sample['expected_complexity_level']})")
    print(f"    Predicted: {worst_result['complexity_score']:.3f} ({worst_result['complexity_level']})")
    print(f"    Error: {abs_errors[worst_idx]:.3f}")
    
    print("\\n" + "=" * 50)
    print("🏆 Test Complete!")
    
    return {
        'mae': mae,
        'rmse': rmse,
        'accuracy': accuracy / 100,
        'samples_tested': len(predictions),
        'within_005_percent': within_005,
        'within_010_percent': within_010
    }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python simple_epic1_test.py <test_dataset.json> [model_dir]")
        sys.exit(1)
    
    test_file = sys.argv[1]
    model_dir = sys.argv[2] if len(sys.argv) > 2 else "models/epic1"
    
    if not Path(test_file).exists():
        print(f"❌ Test dataset not found: {test_file}")
        sys.exit(1)
    
    if not Path(model_dir).exists():
        print(f"❌ Model directory not found: {model_dir}")
        sys.exit(1)
    
    results = test_epic1_classifier(test_file, model_dir)
    print(f"\\n📊 Final Results: MAE={results['mae']:.4f}, Accuracy={results['accuracy']:.1%}")