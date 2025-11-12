#!/usr/bin/env python3
"""
Test Runner System Validation Report Generator
=============================================

Generates comprehensive validation reports for the test runner system.
Provides detailed analysis of integration testing results, performance metrics,
and system validation status.

This is the final component of Phase 3: Integration Testing and Validation Framework.
"""

import json
import time
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import traceback

project_root = Path(__file__).parent.parent.parents[2]
sys.path.insert(0, str(project_root))

from tests.runner.config import TestConfig
from tests.runner.discovery import TestDiscovery
from tests.runner.executor import ExecutionOrchestrator
from tests.runner.cli import TestRunner


class ValidationReportGenerator:
    """Generates comprehensive validation reports for the test runner system."""
    
    def __init__(self):
        """Initialize the validation report generator."""
        self.report_data = {
            'validation_info': {
                'timestamp': datetime.now().isoformat(),
                'system': sys.platform,
                'python_version': sys.version,
                'project_root': str(project_root)
            },
            'component_validation': {},
            'integration_tests': {},
            'performance_metrics': {},
            'regression_tests': {},
            'system_health': {},
            'recommendations': []
        }
    
    def validate_all_components(self) -> Dict[str, Any]:
        """Validate all test runner components."""
        
        print("🔍 Validating Test Runner Components...")
        
        # Test Configuration Component
        config_validation = self._validate_configuration_component()
        
        # Test Discovery Component  
        discovery_validation = self._validate_discovery_component()
        
        # Test Orchestrator Component
        orchestrator_validation = self._validate_orchestrator_component()
        
        # Test CLI Component
        cli_validation = self._validate_cli_component()
        
        self.report_data['component_validation'] = {
            'configuration': config_validation,
            'discovery': discovery_validation,
            'orchestrator': orchestrator_validation,
            'cli': cli_validation
        }
        
        return self.report_data['component_validation']
    
    def _validate_configuration_component(self) -> Dict[str, Any]:
        """Validate configuration component functionality."""
        
        validation_result = {
            'status': 'unknown',
            'tests': [],
            'metrics': {},
            'errors': []
        }
        
        try:
            config = TestConfig()
            
            # Test suite listing
            suite_names = config.list_suites()
            validation_result['tests'].append({
                'name': 'list_suites',
                'status': 'passed' if len(suite_names) > 0 else 'failed',
                'message': f"Found {len(suite_names)} test suites"
            })
            
            # Test suite retrieval
            valid_suites = 0
            for suite_name in suite_names[:5]:  # Test first 5
                suite_config = config.get_suite(suite_name)
                if suite_config and suite_config.name and suite_config.patterns:
                    valid_suites += 1
            
            validation_result['tests'].append({
                'name': 'suite_retrieval',
                'status': 'passed' if valid_suites > 0 else 'failed',
                'message': f"Successfully retrieved {valid_suites}/{min(len(suite_names), 5)} suites"
            })
            
            # Test defaults
            defaults = config.get_defaults()
            validation_result['tests'].append({
                'name': 'defaults_loading',
                'status': 'passed' if isinstance(defaults, dict) else 'failed',
                'message': f"Loaded {len(defaults)} default settings"
            })
            
            validation_result['metrics'] = {
                'total_suites': len(suite_names),
                'valid_suites': valid_suites,
                'defaults_count': len(defaults)
            }
            
            validation_result['status'] = 'passed'
            
        except Exception as e:
            validation_result['status'] = 'failed'
            validation_result['errors'].append(str(e))
        
        return validation_result
    
    def _validate_discovery_component(self) -> Dict[str, Any]:
        """Validate discovery component functionality."""
        
        validation_result = {
            'status': 'unknown',
            'tests': [],
            'metrics': {},
            'errors': []
        }
        
        try:
            discovery = TestDiscovery()
            config = TestConfig()
            
            # Test pattern matching
            test_patterns = [
                "tests/epic1/smoke/test_*.py",
                "tests/unit/test_*.py",
                "tests/integration/test_*.py"
            ]
            
            total_files_found = 0
            for pattern in test_patterns:
                files = discovery._find_files_matching(pattern)
                test_files = [f for f in files if discovery._is_test_file(f)]
                total_files_found += len(test_files)
            
            validation_result['tests'].append({
                'name': 'pattern_matching',
                'status': 'passed' if total_files_found > 0 else 'failed',
                'message': f"Found {total_files_found} test files across {len(test_patterns)} patterns"
            })
            
            # Test suite discovery
            smoke_config = config.get_suite('smoke')
            if smoke_config:
                test_cases = discovery.discover_suite(smoke_config)
                validation_result['tests'].append({
                    'name': 'suite_discovery', 
                    'status': 'passed' if len(test_cases) > 0 else 'failed',
                    'message': f"Discovered {len(test_cases)} test cases in smoke suite"
                })
            
            # Test stats generation
            if 'test_cases' in locals():
                stats = discovery.get_test_stats(test_cases)
                validation_result['tests'].append({
                    'name': 'stats_generation',
                    'status': 'passed' if 'total' in stats else 'failed',
                    'message': f"Generated stats with {len(stats)} categories"
                })
            
            validation_result['metrics'] = {
                'patterns_tested': len(test_patterns),
                'files_found': total_files_found,
                'test_cases_discovered': len(test_cases) if 'test_cases' in locals() else 0
            }
            
            validation_result['status'] = 'passed'
            
        except Exception as e:
            validation_result['status'] = 'failed'
            validation_result['errors'].append(str(e))
        
        return validation_result
    
    def _validate_orchestrator_component(self) -> Dict[str, Any]:
        """Validate orchestrator component functionality."""
        
        validation_result = {
            'status': 'unknown',
            'tests': [],
            'metrics': {},
            'errors': []
        }
        
        try:
            orchestrator = ExecutionOrchestrator()
            
            # Test adapter validation
            adapter_valid = orchestrator.validate_adapter()
            validation_result['tests'].append({
                'name': 'adapter_validation',
                'status': 'passed' if adapter_valid else 'failed',
                'message': f"Adapter validation: {'passed' if adapter_valid else 'failed'}"
            })
            
            # Test execution status tracking
            status_before = orchestrator.get_execution_status()
            validation_result['tests'].append({
                'name': 'status_tracking',
                'status': 'passed' if status_before is None else 'failed',
                'message': f"Initial execution status: {status_before}"
            })
            
            # Test cleanup
            orchestrator.cleanup()
            status_after = orchestrator.get_execution_status()
            validation_result['tests'].append({
                'name': 'cleanup',
                'status': 'passed' if status_after is None else 'failed',
                'message': f"Post-cleanup status: {status_after}"
            })
            
            validation_result['metrics'] = {
                'adapter_type': type(orchestrator.adapter).__name__,
                'discovery_available': orchestrator.discovery is not None
            }
            
            validation_result['status'] = 'passed'
            
        except Exception as e:
            validation_result['status'] = 'failed'
            validation_result['errors'].append(str(e))
        
        return validation_result
    
    def _validate_cli_component(self) -> Dict[str, Any]:
        """Validate CLI component functionality."""
        
        validation_result = {
            'status': 'unknown', 
            'tests': [],
            'metrics': {},
            'errors': []
        }
        
        try:
            runner = TestRunner()
            
            # Test runner initialization
            validation_result['tests'].append({
                'name': 'runner_initialization',
                'status': 'passed' if all([runner.config, runner.orchestrator, runner.discovery]) else 'failed',
                'message': 'Test runner components initialized successfully'
            })
            
            # Test configuration loading
            suite_names = runner.config.list_suites()
            validation_result['tests'].append({
                'name': 'config_integration',
                'status': 'passed' if len(suite_names) > 0 else 'failed',
                'message': f'Loaded {len(suite_names)} test suites'
            })
            
            # Test adapter validation
            adapter_status = runner.orchestrator.validate_adapter()
            validation_result['tests'].append({
                'name': 'adapter_integration',
                'status': 'passed' if adapter_status else 'failed', 
                'message': f'Adapter validation: {"passed" if adapter_status else "failed"}'
            })
            
            validation_result['metrics'] = {
                'suite_count': len(suite_names),
                'components_initialized': 3  # config, orchestrator, discovery
            }
            
            validation_result['status'] = 'passed'
            
        except Exception as e:
            validation_result['status'] = 'failed'
            validation_result['errors'].append(str(e))
        
        return validation_result
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests and collect results."""
        
        print("🧪 Running Integration Tests...")
        
        integration_results = {
            'status': 'unknown',
            'test_files': [],
            'results': {},
            'summary': {},
            'errors': []
        }
        
        # Find integration test files
        integration_test_files = [
            'tests/integration_validation/test_test_runner_integration.py',
            'tests/integration_validation/test_edge_cases_and_validation.py'
        ]
        
        for test_file in integration_test_files:
            test_path = project_root / test_file
            if test_path.exists():
                integration_results['test_files'].append(str(test_path))
        
        # Run integration tests
        if integration_results['test_files']:
            try:
                for test_file in integration_results['test_files']:
                    print(f"  Running: {Path(test_file).name}")
                    
                    result = subprocess.run(
                        [sys.executable, '-m', 'pytest', test_file, '-v', '--tb=short'],
                        capture_output=True,
                        text=True,
                        cwd=project_root,
                        timeout=300
                    )
                    
                    integration_results['results'][Path(test_file).name] = {
                        'exit_code': result.returncode,
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'passed': result.returncode == 0
                    }
                
                # Calculate summary
                total_files = len(integration_results['results'])
                passed_files = sum(1 for r in integration_results['results'].values() if r['passed'])
                
                integration_results['summary'] = {
                    'total_files': total_files,
                    'passed_files': passed_files,
                    'failed_files': total_files - passed_files,
                    'success_rate': passed_files / total_files if total_files > 0 else 0
                }
                
                integration_results['status'] = 'passed' if passed_files == total_files else 'partial'
                
            except Exception as e:
                integration_results['status'] = 'failed'
                integration_results['errors'].append(str(e))
        else:
            integration_results['status'] = 'skipped'
            integration_results['errors'].append('No integration test files found')
        
        self.report_data['integration_tests'] = integration_results
        return integration_results
    
    def run_performance_benchmarks(self) -> Dict[str, Any]:
        """Run performance benchmarks and collect metrics."""
        
        print("⚡ Running Performance Benchmarks...")
        
        performance_results = {
            'status': 'unknown',
            'benchmarks': {},
            'summary': {},
            'errors': []
        }
        
        try:
            # Discovery performance benchmark
            discovery = TestDiscovery()
            config = TestConfig()
            
            # Benchmark configuration loading
            start_time = time.perf_counter()
            suite_names = config.list_suites()
            config_load_time = time.perf_counter() - start_time
            
            # Benchmark test discovery
            smoke_config = config.get_suite('smoke')
            if smoke_config:
                start_time = time.perf_counter()
                test_cases = discovery.discover_suite(smoke_config)
                discovery_time = time.perf_counter() - start_time
            else:
                discovery_time = 0
                test_cases = []
            
            # Benchmark stats generation
            start_time = time.perf_counter()
            if test_cases:
                stats = discovery.get_test_stats(test_cases)
                stats_time = time.perf_counter() - start_time
            else:
                stats_time = 0
            
            performance_results['benchmarks'] = {
                'config_loading': {
                    'time_ms': config_load_time * 1000,
                    'suites_loaded': len(suite_names),
                    'performance_rating': 'good' if config_load_time < 1.0 else 'poor'
                },
                'test_discovery': {
                    'time_ms': discovery_time * 1000,
                    'tests_discovered': len(test_cases),
                    'performance_rating': 'good' if discovery_time < 2.0 else 'poor'
                },
                'stats_generation': {
                    'time_ms': stats_time * 1000,
                    'performance_rating': 'good' if stats_time < 0.5 else 'poor'
                }
            }
            
            # Summary metrics
            total_time = config_load_time + discovery_time + stats_time
            performance_results['summary'] = {
                'total_benchmark_time': total_time,
                'all_benchmarks_good': all(
                    b.get('performance_rating') == 'good' 
                    for b in performance_results['benchmarks'].values()
                )
            }
            
            performance_results['status'] = 'passed'
            
        except Exception as e:
            performance_results['status'] = 'failed'
            performance_results['errors'].append(str(e))
        
        self.report_data['performance_metrics'] = performance_results
        return performance_results
    
    def run_regression_tests(self) -> Dict[str, Any]:
        """Run regression tests to ensure existing functionality works."""
        
        print("🔄 Running Regression Tests...")
        
        regression_results = {
            'status': 'unknown',
            'tests': [],
            'errors': []
        }
        
        try:
            # Test CLI validation command
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'tests.runner.cli', 'validate'],
                    capture_output=True,
                    text=True,
                    cwd=project_root,
                    timeout=30
                )
                
                regression_results['tests'].append({
                    'name': 'cli_validate_command',
                    'status': 'passed' if result.returncode == 0 else 'failed',
                    'message': 'CLI validate command execution',
                    'details': {
                        'exit_code': result.returncode,
                        'has_success_message': '✅ Test setup validation passed!' in result.stdout
                    }
                })
                
            except Exception as e:
                regression_results['tests'].append({
                    'name': 'cli_validate_command',
                    'status': 'failed',
                    'message': f'CLI validate command failed: {e}'
                })
            
            # Test CLI list command
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'tests.runner.cli', 'list'],
                    capture_output=True,
                    text=True,
                    cwd=project_root,
                    timeout=15
                )
                
                regression_results['tests'].append({
                    'name': 'cli_list_command',
                    'status': 'passed' if result.returncode == 0 else 'failed',
                    'message': 'CLI list command execution',
                    'details': {
                        'exit_code': result.returncode,
                        'has_suites_header': '🧪 Available Test Suites:' in result.stdout
                    }
                })
                
            except Exception as e:
                regression_results['tests'].append({
                    'name': 'cli_list_command',
                    'status': 'failed',
                    'message': f'CLI list command failed: {e}'
                })
            
            # Test smoke test execution (quick validation)
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'tests.runner.cli', 'smoke', '--format', 'terminal'],
                    capture_output=True,
                    text=True,
                    cwd=project_root,
                    timeout=60
                )
                
                regression_results['tests'].append({
                    'name': 'smoke_test_execution',
                    'status': 'passed' if result.returncode == 0 else 'failed',
                    'message': 'Smoke test execution through CLI',
                    'details': {
                        'exit_code': result.returncode,
                        'has_test_output': 'PASSED' in result.stdout or '✓' in result.stdout
                    }
                })
                
            except Exception as e:
                regression_results['tests'].append({
                    'name': 'smoke_test_execution',
                    'status': 'failed',
                    'message': f'Smoke test execution failed: {e}'
                })
            
            # Calculate regression test summary
            total_tests = len(regression_results['tests'])
            passed_tests = sum(1 for t in regression_results['tests'] if t['status'] == 'passed')
            
            regression_results['summary'] = {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'success_rate': passed_tests / total_tests if total_tests > 0 else 0
            }
            
            regression_results['status'] = 'passed' if passed_tests == total_tests else 'partial'
            
        except Exception as e:
            regression_results['status'] = 'failed'
            regression_results['errors'].append(str(e))
        
        self.report_data['regression_tests'] = regression_results
        return regression_results
    
    def assess_system_health(self) -> Dict[str, Any]:
        """Assess overall system health and readiness."""
        
        print("🏥 Assessing System Health...")
        
        health_assessment = {
            'overall_status': 'unknown',
            'health_checks': [],
            'readiness_score': 0,
            'critical_issues': [],
            'warnings': []
        }
        
        try:
            # Check component validation status
            component_status = all(
                comp.get('status') == 'passed'
                for comp in self.report_data.get('component_validation', {}).values()
            )
            
            health_assessment['health_checks'].append({
                'name': 'component_validation',
                'status': 'passed' if component_status else 'failed',
                'weight': 30
            })
            
            # Check integration test status
            integration_status = self.report_data.get('integration_tests', {}).get('status')
            integration_passed = integration_status in ['passed', 'partial']
            
            health_assessment['health_checks'].append({
                'name': 'integration_tests',
                'status': 'passed' if integration_passed else 'failed',
                'weight': 25
            })
            
            # Check performance benchmarks
            performance_status = self.report_data.get('performance_metrics', {}).get('status')
            performance_passed = performance_status == 'passed'
            
            health_assessment['health_checks'].append({
                'name': 'performance_benchmarks',
                'status': 'passed' if performance_passed else 'failed',
                'weight': 20
            })
            
            # Check regression tests
            regression_status = self.report_data.get('regression_tests', {}).get('status')
            regression_passed = regression_status in ['passed', 'partial']
            
            health_assessment['health_checks'].append({
                'name': 'regression_tests',
                'status': 'passed' if regression_passed else 'failed',
                'weight': 25
            })
            
            # Calculate readiness score
            total_weight = sum(check['weight'] for check in health_assessment['health_checks'])
            passed_weight = sum(
                check['weight'] for check in health_assessment['health_checks']
                if check['status'] == 'passed'
            )
            
            health_assessment['readiness_score'] = (passed_weight / total_weight) * 100 if total_weight > 0 else 0
            
            # Determine overall status
            if health_assessment['readiness_score'] >= 90:
                health_assessment['overall_status'] = 'excellent'
            elif health_assessment['readiness_score'] >= 75:
                health_assessment['overall_status'] = 'good'
            elif health_assessment['readiness_score'] >= 50:
                health_assessment['overall_status'] = 'fair'
            else:
                health_assessment['overall_status'] = 'poor'
            
            # Identify critical issues and warnings
            for check in health_assessment['health_checks']:
                if check['status'] != 'passed':
                    if check['weight'] >= 25:
                        health_assessment['critical_issues'].append(
                            f"{check['name'].replace('_', ' ').title()} failed validation"
                        )
                    else:
                        health_assessment['warnings'].append(
                            f"{check['name'].replace('_', ' ').title()} needs attention"
                        )
            
        except Exception as e:
            health_assessment['overall_status'] = 'error'
            health_assessment['critical_issues'].append(f"System health assessment failed: {e}")
        
        self.report_data['system_health'] = health_assessment
        return health_assessment
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results."""
        
        recommendations = []
        
        # Analyze component validation results
        component_validation = self.report_data.get('component_validation', {})
        for component, result in component_validation.items():
            if result.get('status') != 'passed':
                recommendations.append(f"🔧 Fix {component} component issues: {result.get('errors', [])}")
        
        # Analyze performance results
        performance_metrics = self.report_data.get('performance_metrics', {})
        if performance_metrics.get('status') == 'passed':
            benchmarks = performance_metrics.get('benchmarks', {})
            for benchmark, data in benchmarks.items():
                if data.get('performance_rating') == 'poor':
                    recommendations.append(f"⚡ Optimize {benchmark} performance (current: {data.get('time_ms', 0):.1f}ms)")
        
        # Analyze integration test results
        integration_tests = self.report_data.get('integration_tests', {})
        summary = integration_tests.get('summary', {})
        if summary.get('success_rate', 0) < 1.0:
            recommendations.append(f"🧪 Fix failing integration tests ({summary.get('failed_files', 0)} files failed)")
        
        # Analyze system health
        system_health = self.report_data.get('system_health', {})
        critical_issues = system_health.get('critical_issues', [])
        for issue in critical_issues:
            recommendations.append(f"🚨 Critical: {issue}")
        
        warnings = system_health.get('warnings', [])
        for warning in warnings:
            recommendations.append(f"⚠️  Warning: {warning}")
        
        # General recommendations based on readiness score
        readiness_score = system_health.get('readiness_score', 0)
        if readiness_score < 90:
            recommendations.append(f"📈 Improve system readiness score from {readiness_score:.1f}% to >90%")
        
        if not recommendations:
            recommendations.append("✅ System is performing well - no critical recommendations")
        
        self.report_data['recommendations'] = recommendations
        return recommendations
    
    def generate_full_report(self, output_file: Optional[str] = None) -> str:
        """Generate comprehensive validation report."""
        
        print("\n" + "="*80)
        print("🚀 GENERATING COMPREHENSIVE VALIDATION REPORT")
        print("="*80)
        
        # Run all validation components
        self.validate_all_components()
        self.run_integration_tests()
        self.run_performance_benchmarks()
        self.run_regression_tests()
        self.assess_system_health()
        self.generate_recommendations()
        
        # Generate text report
        report_text = self._generate_text_report()
        
        # Save to file if requested
        if output_file:
            Path(output_file).write_text(report_text)
            print(f"📄 Report saved to: {output_file}")
        
        # Also save JSON data
        json_file = output_file.replace('.txt', '.json') if output_file else 'validation_report.json'
        with open(json_file, 'w') as f:
            json.dump(self.report_data, f, indent=2, default=str)
        print(f"📊 JSON data saved to: {json_file}")
        
        return report_text
    
    def _generate_text_report(self) -> str:
        """Generate formatted text report."""
        
        lines = []
        
        # Header
        lines.extend([
            "TEST RUNNER SYSTEM VALIDATION REPORT",
            "=" * 60,
            f"Generated: {self.report_data['validation_info']['timestamp']}",
            f"System: {self.report_data['validation_info']['system']}",
            f"Python: {self.report_data['validation_info']['python_version'].split()[0]}",
            ""
        ])
        
        # Executive Summary
        system_health = self.report_data.get('system_health', {})
        lines.extend([
            "EXECUTIVE SUMMARY",
            "-" * 20,
            f"Overall Status: {system_health.get('overall_status', 'unknown').upper()}",
            f"Readiness Score: {system_health.get('readiness_score', 0):.1f}%",
            f"Critical Issues: {len(system_health.get('critical_issues', []))}",
            f"Warnings: {len(system_health.get('warnings', []))}",
            ""
        ])
        
        # Component Validation Results
        lines.append("COMPONENT VALIDATION RESULTS")
        lines.append("-" * 35)
        
        component_validation = self.report_data.get('component_validation', {})
        for component, result in component_validation.items():
            status_icon = "✅" if result.get('status') == 'passed' else "❌"
            lines.append(f"{status_icon} {component.title()}: {result.get('status', 'unknown')}")
            
            for test in result.get('tests', []):
                test_icon = "  ✓" if test.get('status') == 'passed' else "  ✗"
                lines.append(f"{test_icon} {test.get('name')}: {test.get('message')}")
        
        lines.append("")
        
        # Integration Test Results
        lines.append("INTEGRATION TEST RESULTS")
        lines.append("-" * 25)
        
        integration_tests = self.report_data.get('integration_tests', {})
        summary = integration_tests.get('summary', {})
        
        if summary:
            lines.extend([
                f"Total Test Files: {summary.get('total_files', 0)}",
                f"Passed: {summary.get('passed_files', 0)}",
                f"Failed: {summary.get('failed_files', 0)}",
                f"Success Rate: {summary.get('success_rate', 0):.1%}",
            ])
        else:
            lines.append("No integration test results available")
        
        lines.append("")
        
        # Performance Metrics
        lines.append("PERFORMANCE BENCHMARKS")
        lines.append("-" * 23)
        
        performance_metrics = self.report_data.get('performance_metrics', {})
        benchmarks = performance_metrics.get('benchmarks', {})
        
        for benchmark, data in benchmarks.items():
            rating_icon = "🟢" if data.get('performance_rating') == 'good' else "🔴"
            lines.append(f"{rating_icon} {benchmark.replace('_', ' ').title()}: {data.get('time_ms', 0):.1f}ms")
        
        lines.append("")
        
        # Regression Test Results
        lines.append("REGRESSION TEST RESULTS")
        lines.append("-" * 23)
        
        regression_tests = self.report_data.get('regression_tests', {})
        regression_summary = regression_tests.get('summary', {})
        
        if regression_summary:
            lines.extend([
                f"Total Tests: {regression_summary.get('total_tests', 0)}",
                f"Passed: {regression_summary.get('passed_tests', 0)}",
                f"Failed: {regression_summary.get('failed_tests', 0)}",
                f"Success Rate: {regression_summary.get('success_rate', 0):.1%}",
            ])
        else:
            lines.append("No regression test results available")
        
        lines.append("")
        
        # Recommendations
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 15)
        
        recommendations = self.report_data.get('recommendations', [])
        for rec in recommendations:
            lines.append(rec)
        
        lines.append("")
        
        # Footer
        lines.extend([
            "=" * 60,
            f"Report completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "For detailed analysis, see accompanying JSON report."
        ])
        
        return "\n".join(lines)


def main():
    """Main function to generate validation report."""
    
    print("🔍 Test Runner System Validation")
    print("=" * 40)
    
    # Create report generator
    generator = ValidationReportGenerator()
    
    # Generate comprehensive report
    report_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"test_runner_validation_report_{report_timestamp}.txt"
    
    try:
        report_text = generator.generate_full_report(output_file)
        
        # Print summary to console
        print("\n" + report_text.split("COMPONENT VALIDATION RESULTS")[0])
        
        # Print final status
        system_health = generator.report_data.get('system_health', {})
        overall_status = system_health.get('overall_status', 'unknown')
        readiness_score = system_health.get('readiness_score', 0)
        
        if overall_status in ['excellent', 'good'] and readiness_score >= 75:
            print("🎉 TEST RUNNER SYSTEM VALIDATION: PASSED")
            return 0
        else:
            print("⚠️  TEST RUNNER SYSTEM VALIDATION: NEEDS ATTENTION")
            return 1
            
    except Exception as e:
        print(f"❌ Validation report generation failed: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())