#!/usr/bin/env python3
"""
Epic 1 Training Runner

This script demonstrates the complete Epic 1 training pipeline from data generation
through model training to final evaluation.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.training.dataset_generation_framework import ClaudeDatasetGenerator, DatasetGenerationConfig
from src.training.epic1_training_orchestrator import Epic1TrainingOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_complete_epic1_pipeline():
    """
    Run the complete Epic 1 ML training pipeline:
    1. Generate training dataset using Claude
    2. Train individual view models  
    3. Integrate with Epic1MLAnalyzer
    4. Evaluate ensemble performance
    """
    
    print("🚀 STARTING EPIC 1 COMPLETE ML TRAINING PIPELINE")
    print("="*80)
    
    try:
        # ===================================================================
        # PHASE 1: DATASET GENERATION
        # ===================================================================
        print("\n📊 PHASE 1: GENERATING TRAINING DATASET WITH CLAUDE")
        print("-" * 60)
        
        # Configure dataset generation
        dataset_config = DatasetGenerationConfig(
            total_samples=500,  # Smaller for demo
            complexity_distribution={"simple": 175, "medium": 200, "complex": 125},
            domain_distribution={"technical": 250, "general": 150, "academic": 100},
            batch_size=20,
            quality_threshold=0.75,
            output_dir=Path("data/training")
        )
        
        # Generate dataset
        generator = ClaudeDatasetGenerator(dataset_config)
        datapoints, generation_report = generator.generate_dataset()
        
        # Report generation results
        print(f"✅ Generated {len(datapoints)} high-quality training samples")
        print(f"   Dataset ready for training: {generation_report['ready_for_training']}")
        print(f"   Overall quality score: {generation_report['dataset_summary']['quality_metrics']['overall_health_score']:.3f}")
        
        dataset_path = list(dataset_config.output_dir.glob("epic1_dataset_*.json"))[-1]
        print(f"   Dataset saved to: {dataset_path}")
        
        # ===================================================================
        # PHASE 2: MODEL TRAINING
        # ===================================================================
        print("\n🤖 PHASE 2: TRAINING ML MODELS")
        print("-" * 60)
        
        # Create training configuration
        training_config_path = Path("config/epic1_training_config.yaml")
        
        # Update config with actual dataset path
        training_config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize orchestrator (will create default config)
        orchestrator = Epic1TrainingOrchestrator(training_config_path)
        
        # Update data path in config
        orchestrator.config['data']['dataset_path'] = str(dataset_path)
        
        # Run complete training pipeline
        training_results = await orchestrator.run_complete_training()
        
        # ===================================================================
        # PHASE 3: RESULTS SUMMARY
        # ===================================================================
        print("\n🎯 PHASE 3: TRAINING RESULTS SUMMARY")
        print("-" * 60)
        
        # Extract key metrics
        ensemble_accuracy = training_results['evaluation_results']['ensemble_performance']['accuracy']
        target_accuracy = training_results['training_summary']['configuration']['evaluation']['target_accuracy']
        meets_target = ensemble_accuracy >= target_accuracy
        
        individual_accuracies = training_results['evaluation_results']['individual_view_performance']
        
        print(f"📈 INDIVIDUAL VIEW PERFORMANCE:")
        for view_name, metrics in individual_accuracies.items():
            print(f"   {view_name.capitalize():>15}: {metrics['accuracy']:.3f} accuracy")
        
        print(f"\n🎯 ENSEMBLE PERFORMANCE:")
        print(f"   Ensemble Accuracy: {ensemble_accuracy:.3f}")
        print(f"   Target Accuracy:   {target_accuracy:.3f}")
        print(f"   Meets Target:      {'✅ YES' if meets_target else '❌ NO'}")
        
        improvement = training_results['evaluation_results']['performance_comparison']['improvement_over_best']
        print(f"   Improvement:       +{improvement*100:.1f}% over best individual view")
        
        # Overall assessment
        assessment = training_results['overall_assessment']
        print(f"\n📊 OVERALL ASSESSMENT:")
        print(f"   Success:           {'✅' if assessment['success'] else '❌'} {assessment['success']}")
        print(f"   Performance Grade: {assessment['performance_grade']}")
        
        if assessment['key_achievements']:
            print(f"\n✅ KEY ACHIEVEMENTS:")
            for achievement in assessment['key_achievements']:
                print(f"   • {achievement}")
        
        if assessment['areas_for_improvement']:
            print(f"\n🔧 AREAS FOR IMPROVEMENT:")
            for area in assessment['areas_for_improvement']:
                print(f"   • {area}")
        
        # ===================================================================
        # PHASE 4: NEXT STEPS
        # ===================================================================
        print("\n🔄 NEXT STEPS FOR PRODUCTION DEPLOYMENT:")
        print("-" * 60)
        
        if meets_target:
            print("   ✅ Model ready for production deployment")
            print("   ✅ Integrate trained models with Epic1MLAnalyzer")
            print("   ✅ Deploy to serving infrastructure") 
            print("   ✅ Set up monitoring and performance tracking")
        else:
            print("   🔧 Continue training with larger dataset")
            print("   🔧 Tune hyperparameters and model architecture")
            print("   🔧 Implement additional feature engineering")
            print("   🔧 Consider ensemble method improvements")
        
        print(f"\n📁 ARTIFACTS GENERATED:")
        print(f"   • Training dataset:     {dataset_path}")
        print(f"   • Model checkpoints:    {orchestrator.models_dir}/")
        print(f"   • Training reports:     {orchestrator.reports_dir}/")
        print(f"   • Generation report:    {dataset_config.output_dir}/generation_report_*.json")
        
        print("\n" + "="*80)
        print("🎉 EPIC 1 TRAINING PIPELINE COMPLETED SUCCESSFULLY!")
        
        return {
            'dataset_generation': generation_report,
            'training_results': training_results,
            'success': meets_target,
            'final_accuracy': ensemble_accuracy
        }
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        print(f"\n❌ PIPELINE FAILED: {e}")
        print(f"Check logs for detailed error information.")
        raise


def main():
    """Main entry point."""
    try:
        results = asyncio.run(run_complete_epic1_pipeline())
        
        if results['success']:
            print(f"\n🏆 SUCCESS: Achieved {results['final_accuracy']:.1%} accuracy!")
            return 0
        else:
            print(f"\n⚠️  TARGET NOT MET: {results['final_accuracy']:.1%} accuracy")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Training interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)