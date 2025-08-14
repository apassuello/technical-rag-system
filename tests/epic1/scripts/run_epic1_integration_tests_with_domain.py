#!/usr/bin/env python3
"""
Run Epic1 Integration Tests with Domain Relevance

This script demonstrates how the existing Epic1 integration tests work
with the new domain relevance filtering and shows proof of all components
working together.
"""

import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def run_command(cmd: str, description: str) -> Tuple[bool, str, str]:
    """
    Run a command and capture output.
    
    Returns: (success, stdout, stderr)
    """
    print(f"\n{'='*70}")
    print(f"🔧 {description}")
    print(f"{'='*70}")
    print(f"Command: {cmd}")
    print("-"*70)
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        success = result.returncode == 0
        
        if success:
            print("✅ Command succeeded!")
        else:
            print("❌ Command failed!")
            
        if result.stdout:
            print("\nOutput:")
            print(result.stdout[:1000])  # Limit output
            
        if result.stderr and not success:
            print("\nErrors:")
            print(result.stderr[:500])
            
        return success, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        print("⏱️ Command timed out!")
        return False, "", "Timeout"
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False, "", str(e)


def test_epic1_integration_with_domain():
    """Test Epic1 integration with domain relevance."""
    
    print("🚀 EPIC1 INTEGRATION TESTS WITH DOMAIN RELEVANCE")
    print("="*70)
    print("This script runs all Epic1 integration tests and shows how")
    print("domain relevance filtering works with the existing system.")
    print("="*70)
    
    results = {}
    
    # Test 1: Epic1 Query Analyzer Basic Functionality
    success, stdout, stderr = run_command(
        "python test_epic1_integration.py",
        "Test 1: Epic1MLAnalyzer Basic Integration"
    )
    results['epic1_ml_analyzer'] = {
        'success': success,
        'tests_passed': "INTEGRATION TEST SUCCESS" in stdout,
        'evidence': "Epic1MLAnalyzer is fully operational" in stdout
    }
    
    # Test 2: Epic1 Focused Debug (Confirms all fixes)
    success, stdout, stderr = run_command(
        "python test_epic1_focused_debug.py",
        "Test 2: Epic1 Focused Debug (OpenAI Fix Verification)"
    )
    results['epic1_focused_debug'] = {
        'success': success,
        'all_tests_passed': "3/3 tests passed (100.0%)" in stdout,
        'openai_fixed': "Openai Parameters" in stdout and "PASSED" in stdout
    }
    
    # Test 3: Domain Relevance Scoring
    success, stdout, stderr = run_command(
        """python -c "
from src.components.query_processors.domain_relevance_filter import DomainRelevanceScorer
scorer = DomainRelevanceScorer()

queries = [
    'Explain transformer attention mechanisms',
    'What is the weather today?',
    'How does FAISS work?'
]

for q in queries:
    score, tier, _ = scorer.score_query(q)
    print(f'{q[:30]:30} -> {tier:20} (score: {score:.3f})')
"
        """,
        "Test 3: Domain Relevance Scoring"
    )
    results['domain_relevance'] = {
        'success': success,
        'scoring_works': "high_relevance" in stdout or "medium_relevance" in stdout
    }
    
    # Test 4: Epic1 End-to-End with Routing
    success, stdout, stderr = run_command(
        """python -c "
from src.components.generators.epic1_answer_generator import Epic1AnswerGenerator
from src.core.interfaces import Document

config = {
    'routing': {'enabled': True, 'default_strategy': 'balanced'},
    'models': {
        'simple': {'primary': {'provider': 'ollama', 'model': 'llama3.2:3b'}},
        'medium': {'primary': {'provider': 'ollama', 'model': 'llama3.2:3b'}},
        'complex': {'primary': {'provider': 'ollama', 'model': 'llama3.2:3b'}}
    },
    'fallback': {'enabled': True, 'provider': 'ollama', 'model': 'llama3.2:3b'}
}

generator = Epic1AnswerGenerator(config=config)
print(f'✅ Epic1AnswerGenerator created')
print(f'   Routing: {generator.routing_enabled}')
print(f'   Analyzer: {generator.query_analyzer is not None}')
print(f'   Router: {generator.adaptive_router is not None}')

# Test with actual query
docs = [Document(content='RISC-V is an open ISA', metadata={})]
answer = generator.generate('What is RISC-V?', docs)
print(f'✅ Answer generated: {len(answer.text)} chars')
print(f'   Confidence: {answer.confidence:.3f}')
"
        """,
        "Test 4: Epic1 End-to-End Generation"
    )
    results['epic1_generation'] = {
        'success': success,
        'generator_works': "Answer generated" in stdout,
        'routing_enabled': "Routing: True" in stdout
    }
    
    # Test 5: Run existing Epic1 integration tests
    test_files = [
        "tests/epic1/integration/test_epic1_end_to_end.py",
        "tests/epic1/integration/test_epic1_query_analyzer.py",
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            success, stdout, stderr = run_command(
                f"python {test_file}",
                f"Test 5: {Path(test_file).name}"
            )
            results[Path(test_file).stem] = {
                'success': success,
                'output_excerpt': stdout[:200] if stdout else stderr[:200]
            }
    
    # Test 6: Complete Integration Demo
    success, stdout, stderr = run_command(
        """python -c "
import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))

from src.components.query_processors.domain_relevance_filter import DomainRelevanceScorer
from src.components.query_processors.analyzers.epic1_query_analyzer import Epic1QueryAnalyzer
from src.components.generators.routing.adaptive_router import AdaptiveRouter

# Initialize components
scorer = DomainRelevanceScorer()
analyzer = Epic1QueryAnalyzer({'memory_budget_gb': 0.1})
router = AdaptiveRouter(query_analyzer=analyzer)

# Test query
query = 'Explain how transformers use attention mechanisms for NLP tasks'

# Stage 1: Domain Relevance
score, tier, details = scorer.score_query(query)
print(f'🎯 Domain Relevance: {tier} (score: {score:.3f})')

# Stage 2: Epic1 ML Analysis
analysis = analyzer._analyze_query(query)
print(f'🧠 ML Complexity: {analysis.complexity_level} (score: {analysis.complexity_score:.3f})')

# Stage 3: Adaptive Routing
decision = router.route_query(query, strategy_override='balanced')
print(f'🚀 Model Selected: {decision.selected_model.provider}/{decision.selected_model.model}')
print(f'⏱️ Routing Time: {decision.decision_time_ms:.2f}ms')

print('\\n✅ Complete Integration Working!')
"
        """,
        "Test 6: Complete Integration Pipeline"
    )
    results['complete_integration'] = {
        'success': success,
        'all_stages_work': "Complete Integration Working" in stdout
    }
    
    # Print Summary
    print("\n" + "="*70)
    print("📊 TEST RESULTS SUMMARY")
    print("="*70)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r.get('success', False))
    
    for test_name, result in results.items():
        status = "✅" if result.get('success', False) else "❌"
        print(f"{status} {test_name}")
        for key, value in result.items():
            if key != 'success' and key != 'output_excerpt':
                print(f"    {key}: {value}")
    
    print(f"\n📈 Overall: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
    
    # Save results
    results_file = Path("epic1_integration_test_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n💾 Results saved to: {results_file}")
    
    # Generate proof commands
    print("\n" + "="*70)
    print("🔍 COMMANDS TO REPRODUCE RESULTS")
    print("="*70)
    
    proof_commands = [
        "# 1. Test Epic1MLAnalyzer is working:",
        "python test_epic1_integration.py",
        "",
        "# 2. Test OpenAI adapter fix:",
        "python test_epic1_focused_debug.py",
        "",
        "# 3. Test domain relevance scoring:",
        "python -c \"from src.components.query_processors.domain_relevance_filter import DomainRelevanceScorer; s = DomainRelevanceScorer(); print(s.score_query('What is transformer attention?'))\"",
        "",
        "# 4. Test Epic1 answer generation:",
        "python test_epic1_final_validation.py",
        "",
        "# 5. Run existing Epic1 integration tests:",
        "python tests/epic1/integration/test_epic1_end_to_end.py",
        "python tests/epic1/integration/test_epic1_query_analyzer.py",
        "",
        "# 6. Run complete demo:",
        "python demo_complete_epic1_domain_integration.py"
    ]
    
    print("\n".join(proof_commands))
    
    if passed_tests == total_tests:
        print("\n" + "="*70)
        print("🎉 ALL TESTS PASSED - EPIC1 INTEGRATION COMPLETE!")
        print("="*70)
        print("✅ Epic1MLAnalyzer: WORKING")
        print("✅ Domain Relevance: WORKING")
        print("✅ Adaptive Routing: WORKING")
        print("✅ OpenAI Fix: VERIFIED")
        print("✅ End-to-End: FUNCTIONAL")
        return True
    else:
        print("\n⚠️ Some tests failed - review results above")
        return False


if __name__ == "__main__":
    try:
        success = test_epic1_integration_with_domain()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test runner failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)