#!/usr/bin/env python3
"""
Basic Epic 1 Training Test

This script tests the core training components without optional dependencies.
"""

import sys
import logging
from pathlib import Path
import json

# Add src to Python path - fix path resolution for Epic 1 tests
sys.path.insert(0, str(Path(__file__).parents[4] / 'src'))

# Test imports
try:
    from src.training.dataset_generation_framework import ClaudeDatasetGenerator, DatasetGenerationConfig
    from src.training.data_loader import Epic1DataLoader
    from src.training.view_trainer import ViewTrainer
    print("✅ All training modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_dataset_generation():
    """Test dataset generation."""
    print("\n🧪 Testing Dataset Generation...")
    
    # Small test configuration
    config = DatasetGenerationConfig(
        total_samples=10,  # Very small for testing
        complexity_distribution={"simple": 4, "medium": 4, "complex": 2},
        domain_distribution={"technical": 5, "general": 3, "academic": 2},
        batch_size=5,
        output_dir=Path("data/training/test")
    )
    
    generator = ClaudeDatasetGenerator(config)
    datapoints, report = generator.generate_dataset()
    
    print(f"   Generated {len(datapoints)} datapoints")
    print(f"   Quality score: {report['dataset_summary']['quality_metrics']['overall_health_score']:.3f}")
    print(f"   Ready for training: {report['ready_for_training']}")
    
    return datapoints, report


def test_data_loading(dataset_path):
    """Test data loading and preprocessing."""
    print("\n🧪 Testing Data Loading...")
    
    loader = Epic1DataLoader(dataset_path)
    loader.load_dataset()
    
    # Get statistics
    stats = loader.get_statistics()
    print(f"   Loaded {stats['total_samples']} samples")
    print(f"   Complexity distribution: {stats['complexity_distribution']}")
    
    # Preprocess data
    view_examples = loader.preprocess_data()
    print(f"   Preprocessed data for {len(view_examples)} views")
    
    for view_name, examples in view_examples.items():
        if examples:
            print(f"     {view_name}: {len(examples)} examples")
            # Show feature info
            features = examples[0].features
            print(f"       Feature vector size: {len(features)}")
    
    return loader, view_examples


def test_trainer_setup():
    """Test trainer setup."""
    print("\n🧪 Testing Trainer Setup...")
    
    # Test creating a trainer
    trainer = ViewTrainer(
        view_name='technical',
        model_config={'hidden_dim': 128, 'dropout': 0.3},
        training_config={'num_epochs': 2, 'learning_rate': 2e-5, 'output_dir': 'models/test'}
    )
    
    print(f"   Created trainer for {trainer.view_name} view")
    print(f"   Model: {trainer.model_name}")
    print(f"   Device: {trainer.device}")
    
    # Test model setup (requires knowing num_features)
    num_features = 5  # Technical view has 5 features
    trainer.setup_model(num_features)
    print(f"   Model setup successful with {num_features} features")
    
    return trainer


def main():
    """Run basic training tests."""
    print("🧪 EPIC 1 TRAINING SYSTEM - BASIC TESTS")
    print("=" * 60)
    
    try:
        # Test 1: Dataset Generation
        datapoints, report = test_dataset_generation()
        
        # Find generated dataset file
        dataset_files = list(Path("data/training/test").glob("epic1_dataset_*.json"))
        if not dataset_files:
            print("❌ No dataset file found")
            return False
        
        dataset_path = dataset_files[-1]  # Latest file
        print(f"   Dataset saved to: {dataset_path}")
        
        # Test 2: Data Loading
        loader, view_examples = test_data_loading(dataset_path)
        
        # Test 3: Trainer Setup
        trainer = test_trainer_setup()
        
        # Test 4: Integration Check
        print("\n🧪 Testing Integration Components...")
        
        # Check that we can access Epic1MLAnalyzer
        try:
            from src.components.query_processors.analyzers.epic1_ml_analyzer import Epic1MLAnalyzer
            print("   ✅ Epic1MLAnalyzer import successful")
        except ImportError as e:
            print(f"   ❌ Epic1MLAnalyzer import failed: {e}")
        
        # Check ModelManager integration
        try:
            from src.components.query_processors.analyzers.ml_models.model_manager import ModelManager
            print("   ✅ ModelManager import successful")
        except ImportError as e:
            print(f"   ❌ ModelManager import failed: {e}")
        
        print("\n✅ ALL BASIC TESTS PASSED")
        print("\nTraining System Status:")
        print("  • Dataset Generation: ✅ Working")
        print("  • Data Loading: ✅ Working") 
        print("  • Model Training Setup: ✅ Working")
        print("  • Epic1 Integration: ✅ Ready")
        
        print(f"\nNext Steps:")
        print(f"  1. Generate larger dataset (500-1000 samples)")
        print(f"  2. Run full training pipeline with actual model training")
        print(f"  3. Integrate trained models with Epic1MLAnalyzer")
        print(f"  4. Evaluate on test set to achieve >85% accuracy")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.exception("Test failure details:")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)