#!/usr/bin/env python3
"""
Simple test of Epic 1 dataset with algorithmic analyzers only.
"""

import json
import numpy as np
import asyncio
import logging
from pathlib import Path
from typing import Dict, List
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the analyzer we'll use
from src.components.query_processors.analyzers.epic1_query_analyzer import Epic1QueryAnalyzer


class SimpleDatasetTester:
    """Simple tester using algorithmic analyzers."""
    
    def __init__(self, dataset_path: str):
        self.dataset_path = Path(dataset_path)
        self.dataset = self._load_dataset()
        self.analyzer = None
        self.results = []
        
    def _load_dataset(self) -> List[Dict]:
        """Load dataset from JSON file."""
        with open(self.dataset_path, 'r') as f:
            return json.load(f)
    
    async def test_samples(self, num_samples: int = 50):
        """Test samples with the analyzer."""
        logger.info(f"Testing {num_samples} samples with Epic1QueryAnalyzer...")
        
        # Initialize analyzer (using the simpler one that works)
        try:
            self.analyzer = Epic1QueryAnalyzer()
            logger.info("Epic1QueryAnalyzer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize analyzer: {e}")
            return
        
        # Sample queries from each complexity level
        samples_per_level = num_samples // 3
        test_samples = []
        
        for level in ['simple', 'medium', 'complex']:
            level_samples = [s for s in self.dataset if s['expected_complexity_level'] == level]
            if level_samples:
                selected = np.random.choice(
                    level_samples, 
                    min(samples_per_level, len(level_samples)), 
                    replace=False
                )
                test_samples.extend(selected)
        
        logger.info(f"Selected {len(test_samples)} samples for testing")
        
        # Test each sample
        for i, sample in enumerate(test_samples):
            if i % 10 == 0:
                logger.info(f"  Testing sample {i+1}/{len(test_samples)}...")
            
            try:
                # Analyze query
                result = self.analyzer.analyze(sample['query_text'])
                
                # Calculate error
                error = abs(result['complexity_score'] - sample['expected_complexity_score'])
                
                # Store result
                self.results.append({
                    'query': sample['query_text'][:100],  # Truncate for display
                    'expected_score': sample['expected_complexity_score'],
                    'expected_level': sample['expected_complexity_level'],
                    'predicted_score': result['complexity_score'],
                    'predicted_level': result['complexity_level'],
                    'error': error,
                    'confidence': result.get('confidence', 0)
                })
                
            except Exception as e:
                logger.error(f"Error analyzing sample: {e}")
                continue
        
        logger.info(f"Testing complete! Analyzed {len(self.results)} samples")
    
    def calculate_metrics(self):
        """Calculate performance metrics."""
        if not self.results:
            logger.warning("No results to analyze")
            return
        
        # Overall metrics
        errors = [r['error'] for r in self.results]
        expected_scores = [r['expected_score'] for r in self.results]
        predicted_scores = [r['predicted_score'] for r in self.results]
        
        mae = np.mean(errors)
        rmse = np.sqrt(np.mean([e**2 for e in errors]))
        
        # Correlation
        if len(expected_scores) > 1:
            correlation = np.corrcoef(expected_scores, predicted_scores)[0, 1]
        else:
            correlation = 0
        
        # Per-level metrics
        level_metrics = {}
        for level in ['simple', 'medium', 'complex']:
            level_results = [r for r in self.results if r['expected_level'] == level]
            if level_results:
                level_errors = [r['error'] for r in level_results]
                level_metrics[level] = {
                    'count': len(level_results),
                    'mae': np.mean(level_errors),
                    'max_error': np.max(level_errors)
                }
        
        # Classification accuracy
        correct = sum(1 for r in self.results if r['expected_level'] == r['predicted_level'])
        accuracy = correct / len(self.results) if self.results else 0
        
        # Print results
        print("\n" + "="*60)
        print("DATASET TESTING RESULTS")
        print("="*60)
        print(f"\nSamples tested: {len(self.results)}")
        print(f"\nOverall Performance:")
        print(f"  MAE: {mae:.4f}")
        print(f"  RMSE: {rmse:.4f}")
        print(f"  Correlation: {correlation:.4f}")
        print(f"  Classification Accuracy: {accuracy:.1%}")
        
        print(f"\nPer-Level Performance:")
        for level, metrics in level_metrics.items():
            print(f"  {level.capitalize()}: N={metrics['count']}, MAE={metrics['mae']:.4f}, Max Error={metrics['max_error']:.4f}")
        
        # Show some examples
        print(f"\nExample Predictions (first 5):")
        for i, r in enumerate(self.results[:5]):
            print(f"  {i+1}. Query: '{r['query']}...'")
            print(f"     Expected: {r['expected_score']:.3f} ({r['expected_level']})")
            print(f"     Predicted: {r['predicted_score']:.3f} ({r['predicted_level']})")
            print(f"     Error: {r['error']:.3f}")
        
        print("\n" + "="*60)
        
        return {
            'mae': mae,
            'rmse': rmse,
            'correlation': correlation,
            'accuracy': accuracy,
            'level_metrics': level_metrics
        }
    
    def run_statistical_tests(self):
        """Run basic statistical tests on the dataset."""
        logger.info("Running statistical tests on dataset...")
        
        # Extract scores by level
        level_scores = {
            'simple': [],
            'medium': [],
            'complex': []
        }
        
        for sample in self.dataset:
            level = sample['expected_complexity_level']
            score = sample['expected_complexity_score']
            level_scores[level].append(score)
        
        print("\n" + "="*60)
        print("DATASET STATISTICAL ANALYSIS")
        print("="*60)
        
        # Distribution statistics
        print("\nScore Distributions:")
        for level, scores in level_scores.items():
            if scores:
                print(f"  {level.capitalize()}:")
                print(f"    Count: {len(scores)}")
                print(f"    Mean: {np.mean(scores):.3f}")
                print(f"    Std: {np.std(scores):.3f}")
                print(f"    Range: [{np.min(scores):.3f}, {np.max(scores):.3f}]")
        
        # View correlations
        view_names = ['technical', 'linguistic', 'task', 'semantic', 'computational']
        view_scores = {view: [] for view in view_names}
        final_scores = []
        
        for sample in self.dataset:
            final_scores.append(sample['expected_complexity_score'])
            for view in view_names:
                view_scores[view].append(sample['view_scores'][view])
        
        print("\nView Score Correlations with Final Score:")
        for view in view_names:
            if view_scores[view]:
                corr = np.corrcoef(view_scores[view], final_scores)[0, 1]
                print(f"  {view}: {corr:.3f}")
        
        # Inter-view correlations
        print("\nInter-View Correlations:")
        for i, view1 in enumerate(view_names[:-1]):
            for view2 in view_names[i+1:]:
                corr = np.corrcoef(view_scores[view1], view_scores[view2])[0, 1]
                print(f"  {view1}-{view2}: {corr:.3f}")
        
        # Consistency check
        std_devs = []
        for sample in self.dataset:
            scores = list(sample['view_scores'].values())
            std_devs.append(np.std(scores))
        
        print(f"\nView Score Consistency:")
        print(f"  Mean Std Dev: {np.mean(std_devs):.3f}")
        print(f"  Max Std Dev: {np.max(std_devs):.3f}")
        print(f"  Samples with high variance (>0.25): {sum(1 for s in std_devs if s > 0.25)}")
        
        print("\n" + "="*60)


async def main():
    """Run simple testing."""
    # Find latest dataset
    data_dir = Path("data/training")
    dataset_files = list(data_dir.glob("epic1_dataset_*.json"))
    
    if not dataset_files:
        logger.error("No dataset files found!")
        return
    
    latest_dataset = max(dataset_files, key=lambda p: p.stat().st_mtime)
    logger.info(f"Using dataset: {latest_dataset}")
    
    # Run tests
    tester = SimpleDatasetTester(latest_dataset)
    
    # Statistical analysis
    tester.run_statistical_tests()
    
    # Test with analyzer
    await tester.test_samples(num_samples=50)
    
    # Calculate metrics
    metrics = tester.calculate_metrics()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = Path(f"data/training/simple_test_results_{timestamp}.json")
    
    with open(results_path, 'w') as f:
        json.dump({
            'dataset': str(latest_dataset),
            'test_time': timestamp,
            'metrics': metrics,
            'sample_results': tester.results[:10]  # Save first 10 for inspection
        }, f, indent=2)
    
    logger.info(f"Results saved to: {results_path}")


if __name__ == "__main__":
    asyncio.run(main())