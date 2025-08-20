"""
JSON Reporter

Enhanced JSON output with comprehensive diagnostics and actionable insights.
Provides detailed issue analysis, root cause identification, and remediation guidance.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from .base import Reporter
from ..config import TestRunConfig, TestSuiteConfig
from ..adapters.base import ExecutionResult
from ..diagnostics import TestDiagnosticsEngine


class JSONReporter(Reporter):
    """Enhanced JSON reporter with comprehensive diagnostics."""
    
    def __init__(self, output_file: str = "test_results.json", 
                 enable_diagnostics: bool = True):
        """Initialize enhanced JSON reporter."""
        self.output_file = Path(output_file)
        self.enable_diagnostics = enable_diagnostics
        self.diagnostics_engine = TestDiagnosticsEngine() if enable_diagnostics else None
        
        self.report_data = {
            'metadata': {
                'format_version': '2.0',
                'generated_at': None,
                'generator': 'RAG Portfolio Enhanced Test Runner',
                'diagnostics_enabled': enable_diagnostics
            },
            'execution': {
                'start_time': None,
                'end_time': None,
                'duration': 0,
                'success': False,
                'fail_fast_triggered': False,
                'environment_info': {}
            },
            'configuration': {},
            'suites': [],
            'summary': {
                'total_suites': 0,
                'passed_suites': 0,
                'failed_suites': 0,
                'total_tests': 0,
                'total_duration': 0,
                'epic_summary': {},
                'health_indicators': {}
            },
            'diagnostics': None  # Will be populated if enabled
        }
    
    def start_run(self, config: TestRunConfig):
        """Called when a test run starts."""
        self.report_data['metadata']['generated_at'] = datetime.now().isoformat()
        self.report_data['execution']['start_time'] = datetime.now().isoformat()
        
        # Capture environment information
        self.report_data['execution']['environment_info'] = self._capture_environment_info()
        
        # Store configuration
        self.report_data['configuration'] = {
            'output_format': config.output_format,
            'verbose': config.verbose,
            'fail_fast': config.fail_fast,
            'capture': config.capture,
            'suite_count': len(config.suites),
            'suites': [
                {
                    'name': suite.name,
                    'description': suite.description,
                    'patterns': suite.patterns,
                    'markers': suite.markers,
                    'timeout': suite.timeout,
                    'parallel': suite.parallel,
                    'epic': suite.epic
                }
                for suite in config.suites
            ]
        }
        
        self.report_data['summary']['total_suites'] = len(config.suites)
    
    def start_suite(self, suite_config: TestSuiteConfig):
        """Called when a test suite starts."""
        suite_data = {
            'name': suite_config.name,
            'description': suite_config.description,
            'epic': suite_config.epic,
            'patterns': suite_config.patterns,
            'markers': suite_config.markers,
            'timeout': suite_config.timeout,
            'parallel': suite_config.parallel,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'duration': 0,
            'success': False,
            'result': None
        }
        
        self.report_data['suites'].append(suite_data)
    
    def suite_complete(self, suite_config: TestSuiteConfig, result: ExecutionResult):
        """Called when a test suite completes."""
        # Find the suite data
        suite_data = None
        for suite in self.report_data['suites']:
            if suite['name'] == suite_config.name:
                suite_data = suite
                break
        
        if suite_data:
            suite_data['end_time'] = datetime.now().isoformat()
            suite_data['duration'] = result.duration
            suite_data['success'] = result.success
            suite_data['result'] = {
                'exit_code': result.exit_code,
                'test_count': len(result.test_results),
                'summary': result.summary,
                'tests': [
                    {
                        'name': test.name,
                        'status': test.status,
                        'duration': test.duration,
                        'message': test.message,
                        'traceback': test.traceback,  # Enhanced: Include traceback
                        'markers': test.markers,
                        'file_location': self._extract_file_location(test.name),  # Enhanced
                        'epic': self._extract_epic_from_test_name(test.name)  # Enhanced
                    }
                    for test in result.test_results
                ],
                'output': result.output,
                'error_output': result.error_output,
                'diagnostics': None  # Will be populated if enabled
            }
            
            # Generate diagnostics for this suite if enabled
            if self.enable_diagnostics and self.diagnostics_engine:
                failed_tests = [test for test in result.test_results if test.status in ['failed', 'error']]
                if failed_tests:
                    suite_diagnostics = self.diagnostics_engine.analyze_test_output(
                        result.output, result.error_output, failed_tests
                    )
                    suite_data['result']['diagnostics'] = suite_diagnostics
            
            # Update summary counters
            if result.success:
                self.report_data['summary']['passed_suites'] += 1
            else:
                self.report_data['summary']['failed_suites'] += 1
            
            self.report_data['summary']['total_tests'] += len(result.test_results)
            self.report_data['summary']['total_duration'] += result.duration
            
            # Update epic summary
            if suite_config.epic:
                epic = suite_config.epic
                if epic not in self.report_data['summary']['epic_summary']:
                    self.report_data['summary']['epic_summary'][epic] = {
                        'total_suites': 0,
                        'passed_suites': 0,
                        'failed_suites': 0,
                        'total_tests': 0,
                        'success_rate': 0
                    }
                
                epic_summary = self.report_data['summary']['epic_summary'][epic]
                epic_summary['total_suites'] += 1
                epic_summary['total_tests'] += len(result.test_results)
                
                if result.success:
                    epic_summary['passed_suites'] += 1
                else:
                    epic_summary['failed_suites'] += 1
                
                # Calculate success rate
                if epic_summary['total_suites'] > 0:
                    epic_summary['success_rate'] = (epic_summary['passed_suites'] / 
                                                  epic_summary['total_suites'] * 100)
    
    def run_complete(self, config: TestRunConfig, results: Dict[str, ExecutionResult]):
        """Called when the entire test run completes."""
        self.report_data['execution']['end_time'] = datetime.now().isoformat()
        
        # Calculate total duration
        if self.report_data['execution']['start_time']:
            start_time = datetime.fromisoformat(self.report_data['execution']['start_time'])
            end_time = datetime.fromisoformat(self.report_data['execution']['end_time'])
            self.report_data['execution']['duration'] = (end_time - start_time).total_seconds()
        
        # Set overall success
        self.report_data['execution']['success'] = all(result.success for result in results.values())
        
        # Generate comprehensive diagnostics if enabled
        if self.enable_diagnostics and self.diagnostics_engine:
            self._generate_comprehensive_diagnostics(results)
        
        # Calculate health indicators
        self._calculate_health_indicators(results)
        
        # Write JSON file
        self._write_json_file()
        
        # Enhanced output with diagnostics summary
        self._print_enhanced_summary()
    
    def run_failed(self, config: TestRunConfig, results: Dict[str, ExecutionResult]):
        """Called when a test run fails (e.g., fail-fast triggered)."""
        self.report_data['execution']['fail_fast_triggered'] = True
        self.run_complete(config, results)
    
    def _write_json_file(self):
        """Write the JSON report to file."""
        try:
            # Ensure output directory exists
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write JSON with pretty formatting
            with open(self.output_file, 'w') as f:
                json.dump(self.report_data, f, indent=2, default=self._json_serializer)
                
        except Exception as e:
            print(f"Warning: Could not write JSON report to {self.output_file}: {e}")
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for complex objects."""
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        elif hasattr(obj, 'value'):  # Handle Enum types
            return obj.value
        elif hasattr(obj, '__dict__'):  # Handle dataclasses
            return obj.__dict__
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def _capture_environment_info(self) -> Dict[str, Any]:
        """Capture environment information for diagnostics."""
        import sys
        import platform
        import os
        
        return {
            'python_version': sys.version,
            'platform': platform.platform(),
            'architecture': platform.architecture(),
            'working_directory': os.getcwd(),
            'python_path': sys.path[:5],  # First 5 entries
            'environment_variables': {
                key: value for key, value in os.environ.items() 
                if key.startswith(('TEST_', 'PYTEST_', 'RAG_', 'OPENAI_', 'MISTRAL_'))
                and 'KEY' not in key and 'TOKEN' not in key  # Don't expose secrets
            }
        }
    
    def _extract_file_location(self, test_name: str) -> Optional[str]:
        """Extract file location from test name."""
        if "::" in test_name:
            return test_name.split("::")[0]
        return None
    
    def _extract_epic_from_test_name(self, test_name: str) -> Optional[str]:
        """Extract epic information from test name."""
        if "epic1" in test_name.lower():
            return "epic1"
        elif "epic2" in test_name.lower():
            return "epic2"
        return None
    
    def _generate_comprehensive_diagnostics(self, results: Dict[str, ExecutionResult]):
        """Generate comprehensive diagnostics across all test results."""
        all_failed_tests = []
        all_output = []
        all_error_output = []
        
        # Collect all failed tests and output
        for result in results.values():
            failed_tests = [test for test in result.test_results if test.status in ['failed', 'error']]
            all_failed_tests.extend(failed_tests)
            all_output.append(result.output)
            all_error_output.append(result.error_output)
        
        if all_failed_tests:
            # Generate comprehensive diagnostics
            diagnostics = self.diagnostics_engine.analyze_test_output(
                "\n".join(all_output),
                "\n".join(all_error_output), 
                all_failed_tests
            )
            
            # Add timestamp
            diagnostics['generated_at'] = datetime.now().isoformat()
            
            # Store in report
            self.report_data['diagnostics'] = diagnostics
    
    def _calculate_health_indicators(self, results: Dict[str, ExecutionResult]):
        """Calculate overall health indicators."""
        total_tests = sum(len(result.test_results) for result in results.values())
        failed_tests = sum(
            len([test for test in result.test_results if test.status in ['failed', 'error']])
            for result in results.values()
        )
        
        success_rate = ((total_tests - failed_tests) / total_tests * 100) if total_tests > 0 else 0
        
        # Categorize health status
        if success_rate >= 95:
            health_status = "excellent"
        elif success_rate >= 85:
            health_status = "good"
        elif success_rate >= 70:
            health_status = "fair"
        elif success_rate >= 50:
            health_status = "poor"
        else:
            health_status = "critical"
        
        self.report_data['summary']['health_indicators'] = {
            'overall_success_rate': round(success_rate, 2),
            'health_status': health_status,
            'total_failed_tests': failed_tests,
            'epic_health': self._calculate_epic_health(),
            'component_health_summary': self._extract_component_health_summary()
        }
    
    def _calculate_epic_health(self) -> Dict[str, Any]:
        """Calculate health indicators per epic."""
        epic_health = {}
        
        for epic, epic_summary in self.report_data['summary']['epic_summary'].items():
            if epic:  # Skip None epic
                epic_health[epic] = {
                    'success_rate': epic_summary.get('success_rate', 0),
                    'total_tests': epic_summary.get('total_tests', 0),
                    'status': 'excellent' if epic_summary.get('success_rate', 0) >= 95 else
                             'good' if epic_summary.get('success_rate', 0) >= 85 else
                             'fair' if epic_summary.get('success_rate', 0) >= 70 else 'poor'
                }
        
        return epic_health
    
    def _extract_component_health_summary(self) -> Dict[str, Any]:
        """Extract component health from diagnostics if available."""
        if self.report_data.get('diagnostics') and 'component_health' in self.report_data['diagnostics']:
            return self.report_data['diagnostics']['component_health']
        return {}
    
    def _print_enhanced_summary(self):
        """Print enhanced summary with diagnostics information."""
        print(f"\n📊 Enhanced JSON report written to: {self.output_file}")
        
        # Print health indicators
        health = self.report_data['summary']['health_indicators']
        status_emoji = {
            'excellent': '🟢',
            'good': '🟡', 
            'fair': '🟠',
            'poor': '🔴',
            'critical': '💀'
        }
        
        emoji = status_emoji.get(health['health_status'], '❓')
        print(f"{emoji} Overall Health: {health['health_status'].upper()} ({health['overall_success_rate']}% success rate)")
        
        # Print diagnostic summary if available
        if self.report_data.get('diagnostics'):
            diag_summary = self.report_data['diagnostics'].get('diagnostic_summary', {})
            if diag_summary.get('total_issues', 0) > 0:
                print(f"🔍 Issues Found: {diag_summary['total_issues']} total")
                if diag_summary.get('critical_issues', 0) > 0:
                    print(f"   ⚠️  {diag_summary['critical_issues']} critical issues requiring immediate attention")
                if diag_summary.get('major_issues', 0) > 0:
                    print(f"   🔸 {diag_summary['major_issues']} major issues")
                
                # Print top priority actions
                priority_actions = diag_summary.get('priority_actions', [])
                if priority_actions:
                    print(f"🚀 Top Priority Actions:")
                    for i, action in enumerate(priority_actions[:3], 1):
                        print(f"   {i}. {action}")
            else:
                print("✅ No issues detected")
        
        print(f"📈 Epic Status:")
        for epic, epic_data in self.report_data['summary']['epic_summary'].items():
            if epic:
                epic_emoji = status_emoji.get(
                    'excellent' if epic_data.get('success_rate', 0) >= 95 else
                    'good' if epic_data.get('success_rate', 0) >= 85 else 'fair', '❓'
                )
                print(f"   {epic_emoji} {epic.upper()}: {epic_data.get('success_rate', 0):.1f}% ({epic_data.get('total_tests', 0)} tests)")
    
    def get_report_data(self) -> Dict[str, Any]:
        """Get the current report data."""
        return self.report_data.copy()