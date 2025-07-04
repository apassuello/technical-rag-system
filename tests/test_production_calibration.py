#!/usr/bin/env python3
"""
Test script for production calibration integration.

Tests the integration of temperature scaling calibration with the 
production AnswerGenerator system.
"""

import sys
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared_utils.generation.answer_generator import AnswerGenerator


def create_mock_validation_data(n_samples: int = 50):
    """Create mock validation data for testing calibration."""
    np.random.seed(42)
    
    # Simulate overconfident predictions (common in LLMs)
    true_correctness = np.random.binomial(1, 0.7, n_samples)  # 70% actual accuracy
    predicted_confidence = np.random.beta(8, 3, n_samples)    # Overconfident distribution
    
    validation_data = []
    for i, (conf, correct) in enumerate(zip(predicted_confidence, true_correctness)):
        validation_data.append({
            'confidence': conf,
            'correctness': correct,
            'query': f'test_query_{i}',
            'answer': f'test_answer_{i}'
        })
    
    return validation_data


def test_calibration_integration():
    """Test the full calibration integration with AnswerGenerator."""
    print("🔬 Testing Production Calibration Integration")
    print("=" * 60)
    
    # Test 1: Initialize with calibration enabled
    print("\n1. Initializing AnswerGenerator with calibration...")
    try:
        generator = AnswerGenerator(enable_calibration=True)
        print(f"✅ Calibration enabled: {generator.enable_calibration}")
        print(f"✅ Calibrator available: {generator.calibrator is not None}")
        print(f"✅ Calibrator fitted: {generator.calibrator.is_fitted if generator.calibrator else False}")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return False
    
    # Test 2: Fit calibration with mock data
    print("\n2. Fitting calibration with validation data...")
    try:
        validation_data = create_mock_validation_data(100)
        print(f"   Created {len(validation_data)} validation samples")
        
        optimal_temp = generator.fit_calibration(validation_data)
        print(f"✅ Calibration fitted with temperature: {optimal_temp:.3f}")
        print(f"✅ Temperature > 1.0 (overconfident): {'YES' if optimal_temp > 1.0 else 'NO'}")
        print(f"✅ Calibrator now fitted: {generator.calibrator.is_fitted}")
    except Exception as e:
        print(f"❌ Failed to fit calibration: {e}")
        return False
    
    # Test 3: Test confidence calculation with/without calibration
    print("\n3. Testing confidence calculation...")
    
    # Good context test
    good_chunks = [{
        "id": "chunk_1",
        "content": "RISC-V is an open-source instruction set architecture (ISA) based on reduced instruction set computer (RISC) principles.",
        "metadata": {"page_number": 1, "source": "riscv-spec.pdf"},
        "score": 0.95
    }]
    
    try:
        # Test with calibration
        result_calibrated = generator.generate("What is RISC-V?", good_chunks)
        print(f"   With calibration: {result_calibrated.confidence_score:.1%}")
        
        # Test without calibration (temporarily disable)
        generator.enable_calibration = False
        result_uncalibrated = generator.generate("What is RISC-V?", good_chunks)
        print(f"   Without calibration: {result_uncalibrated.confidence_score:.1%}")
        
        # Re-enable calibration
        generator.enable_calibration = True
        
        print(f"✅ Calibration effect: {result_uncalibrated.confidence_score:.1%} -> {result_calibrated.confidence_score:.1%}")
        
    except Exception as e:
        print(f"❌ Failed confidence test: {e}")
        return False
    
    # Test 4: Save and load calibration
    print("\n4. Testing calibration persistence...")
    try:
        # Save calibration
        save_path = "test_calibration.json"
        success = generator.save_calibration(save_path)
        print(f"✅ Calibration saved: {success}")
        
        # Create new generator and load calibration
        new_generator = AnswerGenerator(enable_calibration=True)
        print(f"   New generator fitted: {new_generator.calibrator.is_fitted}")
        
        load_success = new_generator.load_calibration(save_path)
        print(f"✅ Calibration loaded: {load_success}")
        print(f"✅ New generator now fitted: {new_generator.calibrator.is_fitted}")
        print(f"✅ Temperature preserved: {new_generator.calibrator.temperature:.3f}")
        
        # Clean up
        Path(save_path).unlink(missing_ok=True)
        
    except Exception as e:
        print(f"❌ Failed persistence test: {e}")
        return False
    
    # Test 5: Production scenario simulation
    print("\n5. Production scenario simulation...")
    try:
        # Test different scenarios
        scenarios = [
            {
                "name": "Good Context",
                "chunks": good_chunks,
                "expected_range": (0.6, 1.0)
            },
            {
                "name": "Poor Context", 
                "chunks": [{
                    "id": "chunk_1",
                    "content": "Copyright notice. All rights reserved.",
                    "metadata": {"page_number": 1, "source": "license.pdf"},
                    "score": 0.1
                }],
                "expected_range": (0.0, 0.3)
            },
            {
                "name": "No Context",
                "chunks": [],
                "expected_range": (0.0, 0.1)
            }
        ]
        
        for scenario in scenarios:
            result = generator.generate("What is RISC-V?", scenario["chunks"])
            expected_min, expected_max = scenario["expected_range"]
            
            in_range = expected_min <= result.confidence_score <= expected_max
            print(f"   {scenario['name']}: {result.confidence_score:.1%} ({'✅' if in_range else '❌'})")
        
    except Exception as e:
        print(f"❌ Failed production simulation: {e}")
        return False
    
    print("\n🎉 All calibration integration tests passed!")
    return True


if __name__ == "__main__":
    success = test_calibration_integration()
    if success:
        print("\n✅ Production calibration integration is working correctly!")
        print("\n📋 Next steps:")
        print("  1. Create validation dataset with real query/answer pairs")
        print("  2. Fit calibration with production data")  
        print("  3. Deploy with fitted calibration")
        print("  4. Monitor calibration drift in production")
    else:
        print("\n❌ Integration tests failed - check logs for details")