#!/usr/bin/env python3
"""
Epic 1 ML Infrastructure Test Runner.

Comprehensive test runner for all Epic 1 ML infrastructure components.
Provides detailed reporting, performance metrics, and coverage analysis.
"""

import sys
import os
import time
import argparse
from pathlib import Path
import unittest
import json
import importlib.util
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import logging

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parents[3] / 'src'))

# Test discovery and execution
from unittest import TestLoader, TextTestRunner
from io import StringIO


@dataclass
class TestResult:
    """Test execution result."""
    
    test_name: str
    status: str  # 'passed', 'failed', 'error', 'skipped'
    duration: float
    error_message: Optional[str] = None
    traceback: Optional[str] = None


@dataclass
class TestSuiteResult:
    """Test suite execution result."""
    
    suite_name: str
    total_tests: int
    passed: int
    failed: int
    errors: int
    skipped: int
    duration: float
    test_results: List[TestResult]
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_tests == 0:
            return 0.0
        return self.passed / self.total_tests
    
    @property
    def status(self) -> str:
        """Overall suite status."""
        if self.failed > 0 or self.errors > 0:
            return 'failed'
        elif self.skipped == self.total_tests:
            return 'skipped'
        elif self.passed == self.total_tests:
            return 'passed'
        else:
            return 'partial'


class MLInfrastructureTestRunner:
    """Test runner for Epic 1 ML infrastructure."""
    
    def __init__(self, verbose: bool = False, include_performance: bool = True):
        self.verbose = verbose
        self.include_performance = include_performance
        self.test_results: List[TestSuiteResult] = []
        
        # Configure logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def discover_test_suites(self) -> Dict[str, str]:
        """Discover all test suites in the ML infrastructure."""
        test_root = Path(__file__).parent
        
        test_suites = {
            # Unit tests
            'memory_monitor': str(test_root / 'unit' / 'test_memory_monitor.py'),
            'model_cache': str(test_root / 'unit' / 'test_model_cache.py'),
            'quantization': str(test_root / 'unit' / 'test_quantization.py'),
            'performance_monitor': str(test_root / 'unit' / 'test_performance_monitor.py'),
            'view_result': str(test_root / 'unit' / 'test_view_result.py'),
            'base_views': str(test_root / 'unit' / 'test_base_views.py'),
            
            # Integration tests
            'model_manager': str(test_root / 'integration' / 'test_model_manager.py'),
        }
        
        # Filter to existing files
        existing_suites = {}
        for name, path in test_suites.items():
            if os.path.exists(path):
                existing_suites[name] = path
            else:
                self.logger.warning(f"Test suite not found: {path}")
        
        return existing_suites
    
    def run_test_suite(self, suite_name: str, module_path: str) -> TestSuiteResult:
        """Run a single test suite."""
        self.logger.info(f"Running test suite: {suite_name}")
        
        start_time = time.time()
        
        # Load test module
        try:
            spec = importlib.util.spec_from_file_location(f"test_{suite_name}", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as e:
            self.logger.error(f"Failed to load test module {suite_name}: {e}")
            return TestSuiteResult(
                suite_name=suite_name,
                total_tests=0,
                passed=0,
                failed=1,
                errors=0,
                skipped=0,
                duration=time.time() - start_time,
                test_results=[TestResult(
                    test_name=f"{suite_name}_load_error",
                    status='error',
                    duration=0.0,
                    error_message=str(e)
                )]
            )
        
        # Discover and run tests
        loader = TestLoader()
        suite = loader.loadTestsFromModule(module)
        
        # Run tests with custom result collector
        stream = StringIO()
        runner = TextTestRunner(stream=stream, verbosity=2 if self.verbose else 1)
        
        test_results = []
        
        # Custom test result class to capture individual test results
        class CustomTestResult(unittest.TestResult):
            def __init__(self):
                super().__init__()
                self.test_results = []
            
            def startTest(self, test):
                super().startTest(test)
                self.start_time = time.time()
            
            def addSuccess(self, test):
                super().addSuccess(test)
                duration = time.time() - self.start_time
                self.test_results.append(TestResult(
                    test_name=str(test),
                    status='passed',
                    duration=duration
                ))
            
            def addError(self, test, err):
                super().addError(test, err)
                duration = time.time() - self.start_time
                self.test_results.append(TestResult(
                    test_name=str(test),
                    status='error',
                    duration=duration,
                    error_message=str(err[1]),
                    traceback=str(err[2])
                ))
            
            def addFailure(self, test, err):
                super().addFailure(test, err)
                duration = time.time() - self.start_time
                self.test_results.append(TestResult(
                    test_name=str(test),
                    status='failed',
                    duration=duration,
                    error_message=str(err[1]),
                    traceback=str(err[2])
                ))
            
            def addSkip(self, test, reason):
                super().addSkip(test, reason)
                duration = time.time() - self.start_time
                self.test_results.append(TestResult(
                    test_name=str(test),
                    status='skipped',
                    duration=duration,
                    error_message=reason
                ))
        
        # Run tests
        result = CustomTestResult()
        suite.run(result)
        
        duration = time.time() - start_time
        
        # Create suite result
        suite_result = TestSuiteResult(
            suite_name=suite_name,
            total_tests=result.testsRun,
            passed=result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
            failed=len(result.failures),
            errors=len(result.errors),
            skipped=len(result.skipped),
            duration=duration,
            test_results=result.test_results
        )
        
        self.logger.info(f"Suite {suite_name}: {suite_result.passed}/{suite_result.total_tests} passed "
                        f"({suite_result.success_rate:.1%}) in {duration:.2f}s")
        
        return suite_result
    
    def run_all_tests(self, suites_filter: Optional[List[str]] = None) -> List[TestSuiteResult]:
        """Run all test suites."""
        self.logger.info("Starting Epic 1 ML Infrastructure Test Execution")
        
        test_suites = self.discover_test_suites()
        
        if suites_filter:
            test_suites = {name: path for name, path in test_suites.items() if name in suites_filter}
        
        self.logger.info(f"Found {len(test_suites)} test suites: {list(test_suites.keys())}")
        
        results = []
        total_start_time = time.time()
        
        for suite_name, module_path in test_suites.items():
            try:
                result = self.run_test_suite(suite_name, module_path)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to run test suite {suite_name}: {e}")
                # Create error result
                error_result = TestSuiteResult(
                    suite_name=suite_name,
                    total_tests=0,
                    passed=0,
                    failed=0,
                    errors=1,
                    skipped=0,
                    duration=0.0,
                    test_results=[TestResult(
                        test_name=f"{suite_name}_execution_error",
                        status='error',
                        duration=0.0,
                        error_message=str(e)
                    )]
                )
                results.append(error_result)
        
        total_duration = time.time() - total_start_time
        
        self.logger.info(f"Completed test execution in {total_duration:.2f}s")
        self.test_results = results
        
        return results
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate comprehensive summary report."""
        if not self.test_results:
            return {'error': 'No test results available'}
        
        # Aggregate statistics
        total_tests = sum(result.total_tests for result in self.test_results)
        total_passed = sum(result.passed for result in self.test_results)
        total_failed = sum(result.failed for result in self.test_results)
        total_errors = sum(result.errors for result in self.test_results)
        total_skipped = sum(result.skipped for result in self.test_results)
        total_duration = sum(result.duration for result in self.test_results)
        
        overall_success_rate = total_passed / total_tests if total_tests > 0 else 0.0
        
        # Suite-level analysis
        suite_analysis = []
        for result in self.test_results:
            suite_analysis.append({
                'name': result.suite_name,
                'status': result.status,
                'success_rate': result.success_rate,
                'total_tests': result.total_tests,
                'passed': result.passed,
                'failed': result.failed,
                'errors': result.errors,
                'skipped': result.skipped,
                'duration': result.duration
            })
        
        # Performance analysis
        performance_analysis = {}
        if self.include_performance:
            # Fastest and slowest tests
            all_tests = []
            for result in self.test_results:
                all_tests.extend(result.test_results)
            
            passed_tests = [t for t in all_tests if t.status == 'passed']
            if passed_tests:
                fastest = min(passed_tests, key=lambda x: x.duration)
                slowest = max(passed_tests, key=lambda x: x.duration)
                avg_duration = sum(t.duration for t in passed_tests) / len(passed_tests)
                
                performance_analysis = {
                    'fastest_test': {
                        'name': fastest.test_name,
                        'duration': fastest.duration
                    },
                    'slowest_test': {
                        'name': slowest.test_name,
                        'duration': slowest.duration
                    },
                    'average_test_duration': avg_duration,
                    'total_test_time': sum(t.duration for t in passed_tests)
                }
        
        # Failure analysis
        failure_analysis = {}
        failed_tests = []
        error_tests = []
        
        for result in self.test_results:
            for test_result in result.test_results:
                if test_result.status == 'failed':
                    failed_tests.append({
                        'suite': result.suite_name,
                        'test': test_result.test_name,
                        'error': test_result.error_message
                    })
                elif test_result.status == 'error':
                    error_tests.append({
                        'suite': result.suite_name,
                        'test': test_result.test_name,
                        'error': test_result.error_message
                    })
        
        failure_analysis = {
            'failed_tests': failed_tests,
            'error_tests': error_tests,
            'common_failure_patterns': self._analyze_failure_patterns(failed_tests + error_tests)
        }
        
        # Coverage analysis (basic)
        coverage_analysis = {
            'tested_components': [result.suite_name for result in self.test_results],
            'component_coverage': {
                result.suite_name: {
                    'test_count': result.total_tests,
                    'success_rate': result.success_rate
                }
                for result in self.test_results
            }
        }
        
        return {
            'summary': {
                'timestamp': time.time(),
                'total_suites': len(self.test_results),
                'total_tests': total_tests,
                'passed': total_passed,
                'failed': total_failed,
                'errors': total_errors,
                'skipped': total_skipped,
                'success_rate': overall_success_rate,
                'total_duration': total_duration
            },
            'suite_analysis': suite_analysis,
            'performance_analysis': performance_analysis,
            'failure_analysis': failure_analysis,
            'coverage_analysis': coverage_analysis,
            'quality_assessment': self._assess_quality(),
            'recommendations': self._generate_recommendations()
        }
    
    def _analyze_failure_patterns(self, failures: List[Dict]) -> Dict[str, int]:
        """Analyze common failure patterns."""
        patterns = {}
        
        for failure in failures:
            error_msg = failure.get('error', '').lower()
            
            # Common patterns
            if 'not implemented' in error_msg or 'not available' in error_msg:
                patterns['implementation_missing'] = patterns.get('implementation_missing', 0) + 1
            elif 'import' in error_msg or 'module' in error_msg:
                patterns['import_errors'] = patterns.get('import_errors', 0) + 1
            elif 'timeout' in error_msg:
                patterns['timeout_errors'] = patterns.get('timeout_errors', 0) + 1
            elif 'memory' in error_msg:
                patterns['memory_errors'] = patterns.get('memory_errors', 0) + 1
            elif 'assertion' in error_msg:
                patterns['assertion_failures'] = patterns.get('assertion_failures', 0) + 1
            else:
                patterns['other_errors'] = patterns.get('other_errors', 0) + 1
        
        return patterns
    
    def _assess_quality(self) -> Dict[str, Any]:
        """Assess overall test quality."""
        if not self.test_results:
            return {'assessment': 'no_data'}
        
        total_tests = sum(result.total_tests for result in self.test_results)
        total_passed = sum(result.passed for result in self.test_results)
        success_rate = total_passed / total_tests if total_tests > 0 else 0.0
        
        # Quality thresholds
        if success_rate >= 0.95:
            quality_level = 'excellent'
        elif success_rate >= 0.85:
            quality_level = 'good'
        elif success_rate >= 0.70:
            quality_level = 'acceptable'
        elif success_rate >= 0.50:
            quality_level = 'needs_improvement'
        else:
            quality_level = 'poor'
        
        # Component coverage
        expected_components = [
            'memory_monitor', 'model_cache', 'quantization', 
            'performance_monitor', 'view_result', 'base_views', 
            'model_manager'
        ]
        
        tested_components = [result.suite_name for result in self.test_results if result.total_tests > 0]
        coverage_percentage = len(tested_components) / len(expected_components)
        
        return {
            'overall_quality': quality_level,
            'success_rate': success_rate,
            'component_coverage_percentage': coverage_percentage,
            'tested_components': tested_components,
            'missing_components': [comp for comp in expected_components if comp not in tested_components],
            'total_test_count': total_tests
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        if not self.test_results:
            return ["No test results available for analysis"]
        
        # Analyze results for recommendations
        total_tests = sum(result.total_tests for result in self.test_results)
        total_failed = sum(result.failed for result in self.test_results)
        total_errors = sum(result.errors for result in self.test_results)
        total_skipped = sum(result.skipped for result in self.test_results)
        
        success_rate = (total_tests - total_failed - total_errors - total_skipped) / total_tests if total_tests > 0 else 0.0
        
        # Success rate recommendations
        if success_rate < 0.70:
            recommendations.append("PRIORITY: Investigate and fix failing tests to improve success rate above 70%")
        
        if total_errors > total_failed:
            recommendations.append("Focus on resolving test errors (setup/teardown issues) before assertion failures")
        
        if total_skipped > total_tests * 0.3:
            recommendations.append("High skip rate detected - implement missing test infrastructure or mark as TODO")
        
        # Performance recommendations
        slow_suites = [r for r in self.test_results if r.duration > 30.0]
        if slow_suites:
            recommendations.append(f"Optimize slow test suites: {[s.suite_name for s in slow_suites]}")
        
        # Coverage recommendations
        quality_assessment = self._assess_quality()
        if quality_assessment['component_coverage_percentage'] < 1.0:
            missing = quality_assessment['missing_components']
            recommendations.append(f"Implement missing component tests: {missing}")
        
        if not recommendations:
            recommendations.append("Test suite is in good condition - consider adding performance benchmarks")
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any], filename: str = None) -> str:
        """Save report to JSON file."""
        if filename is None:
            timestamp = int(time.time())
            filename = f"epic1_ml_infrastructure_test_report_{timestamp}.json"
        
        report_path = Path(__file__).parent / filename
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return str(report_path)
    
    def print_summary(self, report: Dict[str, Any]):
        """Print formatted summary to console."""
        summary = report['summary']
        
        print("\n" + "="*80)
        print("EPIC 1 ML INFRASTRUCTURE TEST RESULTS")
        print("="*80)
        
        print(f"\nOVERALL RESULTS:")
        print(f"  Total Suites: {summary['total_suites']}")
        print(f"  Total Tests:  {summary['total_tests']}")
        print(f"  Passed:       {summary['passed']}")
        print(f"  Failed:       {summary['failed']}")
        print(f"  Errors:       {summary['errors']}")
        print(f"  Skipped:      {summary['skipped']}")
        print(f"  Success Rate: {summary['success_rate']:.1%}")
        print(f"  Duration:     {summary['total_duration']:.2f}s")
        
        # Quality assessment
        quality = report['quality_assessment']
        print(f"\nQUALITY ASSESSMENT:")
        print(f"  Overall Quality: {quality['overall_quality'].upper()}")
        print(f"  Component Coverage: {quality['component_coverage_percentage']:.1%}")
        
        # Suite breakdown
        print(f"\nSUITE BREAKDOWN:")
        for suite in report['suite_analysis']:
            status_symbol = "✅" if suite['status'] == 'passed' else "❌" if suite['status'] == 'failed' else "⚠️"
            print(f"  {status_symbol} {suite['name']}: {suite['passed']}/{suite['total_tests']} "
                  f"({suite['success_rate']:.1%}) - {suite['duration']:.2f}s")
        
        # Recommendations
        recommendations = report['recommendations']
        if recommendations:
            print(f"\nRECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        print("\n" + "="*80)


def main():
    """Main test execution entry point."""
    parser = argparse.ArgumentParser(description='Run Epic 1 ML Infrastructure Tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--no-performance', action='store_true', help='Skip performance analysis')
    parser.add_argument('--suites', nargs='+', help='Specific test suites to run')
    parser.add_argument('--output', '-o', help='Output file for JSON report')
    parser.add_argument('--quiet', '-q', action='store_true', help='Minimal output')
    
    args = parser.parse_args()
    
    # Create test runner
    runner = MLInfrastructureTestRunner(
        verbose=args.verbose,
        include_performance=not args.no_performance
    )
    
    # Run tests
    results = runner.run_all_tests(suites_filter=args.suites)
    
    # Generate report
    report = runner.generate_summary_report()
    
    # Save report
    if args.output:
        report_path = runner.save_report(report, args.output)
        print(f"Report saved to: {report_path}")
    else:
        report_path = runner.save_report(report)
        if not args.quiet:
            print(f"Report saved to: {report_path}")
    
    # Print summary
    if not args.quiet:
        runner.print_summary(report)
    
    # Exit with appropriate code
    success_rate = report['summary']['success_rate']
    exit_code = 0 if success_rate >= 0.70 else 1
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()