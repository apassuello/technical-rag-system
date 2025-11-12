#!/usr/bin/env python3
"""
Comprehensive Test Runner Validation Suite
==========================================

Complete validation suite that runs all integration tests, performance benchmarks,
and generates comprehensive validation reports.

This is the main entry point for Phase 3: Integration Testing and Validation Framework.

Usage:
    python tests/integration_validation/run_comprehensive_validation.py
    python -m tests.integration_validation.run_comprehensive_validation
"""

import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime
import argparse

# Add project to path
project_root = Path(__file__).parent.parent.parents[2]
sys.path.insert(0, str(project_root))


def run_test_suite(test_file: Path, description: str, timeout: int = 300) -> dict:
    """Run a specific test suite and return results."""
    
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    print(f"📁 Running: {test_file.name}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', str(test_file), '-v', '--tb=short'],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=timeout
        )
        
        execution_time = time.time() - start_time
        
        # Parse pytest output for results
        output_lines = result.stdout.split('\n')
        test_results = {
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0
        }
        
        for line in output_lines:
            if 'passed' in line and 'failed' in line:
                # Parse summary line: "5 passed, 1 failed, 2 skipped in 10.23s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part in test_results and i > 0 and parts[i-1].isdigit():
                        test_results[part] = int(parts[i-1])
        
        success = result.returncode == 0
        
        # Print immediate results
        if success:
            print(f"✅ {description} - PASSED")
            print(f"   Tests: {test_results['passed']} passed, {test_results['failed']} failed, {test_results['skipped']} skipped")
        else:
            print(f"❌ {description} - FAILED")
            print(f"   Tests: {test_results['passed']} passed, {test_results['failed']} failed, {test_results['skipped']} skipped")
            if result.stderr:
                print(f"   Error: {result.stderr[:200]}...")
        
        print(f"⏱️  Execution time: {execution_time:.2f}s")
        
        return {
            'success': success,
            'exit_code': result.returncode,
            'execution_time': execution_time,
            'test_results': test_results,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'description': description
        }
        
    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        print(f"⏰ {description} - TIMEOUT after {execution_time:.2f}s")
        return {
            'success': False,
            'exit_code': -1,
            'execution_time': execution_time,
            'test_results': {'timeout': 1},
            'stdout': '',
            'stderr': f'Test suite timed out after {timeout}s',
            'description': description
        }
    
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"💥 {description} - ERROR: {e}")
        return {
            'success': False,
            'exit_code': -2,
            'execution_time': execution_time,
            'test_results': {'error': 1},
            'stdout': '',
            'stderr': str(e),
            'description': description
        }


def run_validation_report() -> dict:
    """Run the validation report generator."""
    
    print(f"\n{'='*60}")
    print(f"📊 GENERATING COMPREHENSIVE VALIDATION REPORT")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        from tests.integration_validation.validation_report_generator import ValidationReportGenerator
        
        generator = ValidationReportGenerator()
        
        # Generate report with timestamp
        report_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"comprehensive_validation_report_{report_timestamp}.txt"
        
        report_text = generator.generate_full_report(output_file)
        
        execution_time = time.time() - start_time
        
        # Extract key metrics
        system_health = generator.report_data.get('system_health', {})
        readiness_score = system_health.get('readiness_score', 0)
        overall_status = system_health.get('overall_status', 'unknown')
        
        print(f"📋 Report generated: {output_file}")
        print(f"🏥 System Health: {overall_status.upper()}")
        print(f"📈 Readiness Score: {readiness_score:.1f}%")
        print(f"⏱️  Generation time: {execution_time:.2f}s")
        
        return {
            'success': readiness_score >= 75,
            'readiness_score': readiness_score,
            'overall_status': overall_status,
            'execution_time': execution_time,
            'report_file': output_file,
            'system_health': system_health
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"💥 Report generation failed: {e}")
        return {
            'success': False,
            'readiness_score': 0,
            'overall_status': 'error',
            'execution_time': execution_time,
            'error': str(e)
        }


def run_basic_system_validation() -> dict:
    """Run basic system validation checks."""
    
    print(f"\n{'='*60}")
    print(f"🔍 BASIC SYSTEM VALIDATION")
    print(f"{'='*60}")
    
    validation_results = {
        'cli_validate': False,
        'cli_list': False,
        'smoke_test': False,
        'import_test': False
    }
    
    try:
        # Test CLI validate command
        print("🧪 Testing CLI validate command...")
        result = subprocess.run(
            [sys.executable, '-m', 'tests.runner.cli', 'validate'],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=30
        )
        validation_results['cli_validate'] = result.returncode == 0
        status = "✅ PASSED" if validation_results['cli_validate'] else "❌ FAILED"
        print(f"   {status}")
        
        # Test CLI list command
        print("📋 Testing CLI list command...")
        result = subprocess.run(
            [sys.executable, '-m', 'tests.runner.cli', 'list'],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=15
        )
        validation_results['cli_list'] = result.returncode == 0
        status = "✅ PASSED" if validation_results['cli_list'] else "❌ FAILED"
        print(f"   {status}")
        
        # Test smoke test execution
        print("💨 Testing smoke test execution...")
        result = subprocess.run(
            [sys.executable, '-m', 'tests.runner.cli', 'smoke'],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=60
        )
        validation_results['smoke_test'] = result.returncode == 0
        status = "✅ PASSED" if validation_results['smoke_test'] else "❌ FAILED"
        print(f"   {status}")
        
        # Test module imports
        print("📦 Testing module imports...")
        try:
            from tests.runner.cli import TestRunner
            from tests.runner.config import TestConfig
            from tests.runner.discovery import TestDiscovery
            from tests.runner.executor import ExecutionOrchestrator
            validation_results['import_test'] = True
            print("   ✅ PASSED")
        except ImportError as e:
            validation_results['import_test'] = False
            print(f"   ❌ FAILED: {e}")
        
    except Exception as e:
        print(f"💥 Basic validation error: {e}")
    
    # Summary
    passed_tests = sum(1 for result in validation_results.values() if result)
    total_tests = len(validation_results)
    success_rate = passed_tests / total_tests
    
    print(f"\n📊 Basic Validation Summary:")
    print(f"   Tests passed: {passed_tests}/{total_tests}")
    print(f"   Success rate: {success_rate:.1%}")
    
    return {
        'success': success_rate >= 0.75,
        'results': validation_results,
        'success_rate': success_rate,
        'passed_tests': passed_tests,
        'total_tests': total_tests
    }


def main():
    """Main comprehensive validation function."""
    
    parser = argparse.ArgumentParser(description='Comprehensive Test Runner Validation Suite')
    parser.add_argument('--quick', action='store_true', help='Run quick validation only')
    parser.add_argument('--no-performance', action='store_true', help='Skip performance benchmarks')
    parser.add_argument('--timeout', type=int, default=300, help='Test timeout in seconds')
    
    args = parser.parse_args()
    
    print("🚀 COMPREHENSIVE TEST RUNNER VALIDATION SUITE")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project root: {project_root}")
    
    overall_start_time = time.time()
    
    # Track all results
    all_results = {}
    
    # Phase 1: Basic System Validation
    basic_results = run_basic_system_validation()
    all_results['basic_validation'] = basic_results
    
    if not basic_results['success']:
        print("\n❌ BASIC VALIDATION FAILED - Stopping validation")
        print("Fix basic system issues before running comprehensive validation")
        return 1
    
    if args.quick:
        print("\n🏃 Quick validation completed successfully")
        return 0
    
    # Phase 2: Integration Tests
    integration_test_files = [
        (
            project_root / "tests/integration_validation/test_test_runner_integration.py",
            "Integration Tests - Core System Flow",
            args.timeout
        ),
        (
            project_root / "tests/integration_validation/test_edge_cases_and_validation.py",
            "Edge Cases and Validation Tests",
            args.timeout
        )
    ]
    
    for test_file, description, timeout in integration_test_files:
        if test_file.exists():
            result = run_test_suite(test_file, description, timeout)
            all_results[test_file.stem] = result
        else:
            print(f"⚠️  Test file not found: {test_file}")
            all_results[test_file.stem] = {
                'success': False,
                'error': 'Test file not found'
            }
    
    # Phase 3: Performance Benchmarks (if not skipped)
    if not args.no_performance:
        performance_test_file = project_root / "tests/integration_validation/test_performance_benchmarks.py"
        if performance_test_file.exists():
            result = run_test_suite(
                performance_test_file,
                "Performance Benchmarks and Stress Tests",
                args.timeout * 2  # Double timeout for performance tests
            )
            all_results['performance_benchmarks'] = result
        else:
            print(f"⚠️  Performance test file not found: {performance_test_file}")
    
    # Phase 4: Comprehensive Validation Report
    report_result = run_validation_report()
    all_results['validation_report'] = report_result
    
    # Final Summary
    total_time = time.time() - overall_start_time
    
    print(f"\n{'='*80}")
    print(f"🏁 COMPREHENSIVE VALIDATION COMPLETE")
    print(f"{'='*80}")
    
    # Calculate overall success
    successful_phases = sum(1 for result in all_results.values() if result.get('success', False))
    total_phases = len(all_results)
    overall_success_rate = successful_phases / total_phases if total_phases > 0 else 0
    
    print(f"⏱️  Total execution time: {total_time:.2f}s")
    print(f"📊 Phases completed: {successful_phases}/{total_phases}")
    print(f"📈 Overall success rate: {overall_success_rate:.1%}")
    
    # Detailed results
    print(f"\n📋 DETAILED RESULTS:")
    print("-" * 40)
    
    for phase_name, result in all_results.items():
        status = "✅ PASSED" if result.get('success', False) else "❌ FAILED"
        time_info = f" ({result.get('execution_time', 0):.1f}s)" if 'execution_time' in result else ""
        print(f"{status} {phase_name.replace('_', ' ').title()}{time_info}")
        
        # Show additional details for specific phases
        if phase_name == 'validation_report' and 'readiness_score' in result:
            print(f"        Readiness Score: {result['readiness_score']:.1f}%")
            print(f"        System Status: {result.get('overall_status', 'unknown').title()}")
    
    # Final verdict
    if overall_success_rate >= 0.8:
        print(f"\n🎉 TEST RUNNER SYSTEM VALIDATION: PASSED")
        print(f"   System is ready for production use")
        return 0
    elif overall_success_rate >= 0.6:
        print(f"\n⚠️  TEST RUNNER SYSTEM VALIDATION: PARTIAL SUCCESS")
        print(f"   System has some issues but is mostly functional")
        return 1
    else:
        print(f"\n❌ TEST RUNNER SYSTEM VALIDATION: FAILED")
        print(f"   System has significant issues requiring attention")
        return 2


if __name__ == "__main__":
    exit(main())