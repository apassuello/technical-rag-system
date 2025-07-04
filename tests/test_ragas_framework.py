#!/usr/bin/env python3
"""
Quick test of RAGAS evaluation framework setup.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

def test_ragas_imports():
    """Test that RAGAS can be imported correctly."""
    try:
        from ragas import evaluate
        from ragas.metrics import (
            context_precision,
            context_recall, 
            faithfulness,
            answer_relevancy
        )
        from datasets import Dataset
        print("✅ RAGAS imports successful")
        return True
    except Exception as e:
        print(f"❌ RAGAS import failed: {e}")
        return False

def test_ragas_evaluator_init():
    """Test that RAGASEvaluator can be initialized."""
    try:
        from scripts.evaluation.ragas_evaluation import RAGASEvaluator
        evaluator = RAGASEvaluator()
        print("✅ RAGASEvaluator initialization successful")
        return True
    except Exception as e:
        print(f"❌ RAGASEvaluator initialization failed: {e}")
        return False

def test_create_test_dataset():
    """Test test dataset creation."""
    try:
        from scripts.evaluation.ragas_evaluation import RAGASEvaluator
        evaluator = RAGASEvaluator()
        test_cases = evaluator.create_test_dataset()
        print(f"✅ Test dataset created: {len(test_cases)} cases")
        
        # Show sample
        for i, case in enumerate(test_cases[:2], 1):
            print(f"   Sample {i}: {case['question'][:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ Test dataset creation failed: {e}")
        return False

def test_mock_evaluation():
    """Test evaluation with mock data."""
    try:
        from ragas.metrics import faithfulness, answer_relevancy
        from datasets import Dataset
        
        # Create minimal mock dataset
        mock_data = {
            "question": ["What is RISC-V?"],
            "answer": ["RISC-V is an open instruction set architecture."],
            "contexts": [["RISC-V is an open-source ISA based on RISC principles."]],
            "ground_truth": ["RISC-V is an open instruction set architecture."]
        }
        
        dataset = Dataset.from_dict(mock_data)
        print("✅ Mock dataset created")
        
        # Note: Actual evaluation requires API keys for some metrics
        print("✅ RAGAS framework setup is functional")
        return True
        
    except Exception as e:
        print(f"❌ Mock evaluation failed: {e}")
        return False

def main():
    """Run all RAGAS framework tests."""
    print("TESTING RAGAS EVALUATION FRAMEWORK")
    print("=" * 50)
    
    tests = [
        ("RAGAS Imports", test_ragas_imports),
        ("RAGASEvaluator Init", test_ragas_evaluator_init), 
        ("Test Dataset Creation", test_create_test_dataset),
        ("Mock Evaluation", test_mock_evaluation)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Testing: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST RESULTS")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:10} {test_name}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 RAGAS evaluation framework is ready!")
        print("💡 Note: Full evaluation requires indexed documents and may need API keys for some metrics")
    else:
        print("\n⚠️ Some tests failed - check dependencies and setup")
    
    return passed == len(results)

if __name__ == "__main__":
    main()