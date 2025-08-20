"""
Terminal Reporter

Enhanced terminal output with diagnostic insights and actionable information.
Rich test execution progress with comprehensive issue analysis.
"""

import sys
from typing import Dict, List
from datetime import datetime

from .base import Reporter
from ..config import TestRunConfig, TestSuiteConfig
from ..adapters.base import ExecutionResult
from ..diagnostics import TestDiagnosticsEngine


class TerminalReporter(Reporter):
    """Enhanced terminal reporter with diagnostics."""
    
    def __init__(self, use_colors: bool = True, enable_diagnostics: bool = True):
        """Initialize enhanced terminal reporter."""
        self.use_colors = use_colors and hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
        self.enable_diagnostics = enable_diagnostics
        self.diagnostics_engine = TestDiagnosticsEngine() if enable_diagnostics else None
        self.start_time = None
        self.suite_count = 0
        self.total_suites = 0
        self.all_results = {}  # Store all results for final diagnostics
        
    def _color(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled."""
        if not self.use_colors:
            return text
        
        colors = {
            'green': '\033[92m',
            'red': '\033[91m', 
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'purple': '\033[95m',
            'cyan': '\033[96m',
            'bold': '\033[1m',
            'end': '\033[0m'
        }
        
        return f"{colors.get(color, '')}{text}{colors['end']}"
    
    def _print_header(self, title: str, char: str = "="):
        """Print a formatted header."""
        line = char * 60
        print(f"\n{self._color(line, 'blue')}")
        print(f"{self._color(title.center(60), 'bold')}")
        print(f"{self._color(line, 'blue')}\n")
    
    def _print_epic_info(self, suites: List[TestSuiteConfig]):
        """Print Epic-specific information."""
        epic_suites = {}
        for suite in suites:
            if suite.epic:
                if suite.epic not in epic_suites:
                    epic_suites[suite.epic] = []
                epic_suites[suite.epic].append(suite.name)
        
        if epic_suites:
            print(f"{self._color('Epic Test Suites:', 'purple')}")
            for epic, suite_names in epic_suites.items():
                print(f"  {self._color(epic.upper(), 'cyan')}: {', '.join(suite_names)}")
            print()
    
    def start_run(self, config: TestRunConfig):
        """Called when a test run starts."""
        self.start_time = datetime.now()
        self.suite_count = 0
        self.total_suites = len(config.suites)
        
        self._print_header("RAG Portfolio Test Execution")
        
        print(f"{self._color('Configuration:', 'bold')}")
        print(f"  Output Format: {config.output_format}")
        print(f"  Verbose: {config.verbose}")
        print(f"  Fail Fast: {config.fail_fast}")
        print(f"  Capture: {config.capture}")
        print()
        
        print(f"{self._color('Test Suites:', 'bold')} {len(config.suites)} suites scheduled")
        for suite in config.suites:
            timeout_info = f" (timeout: {suite.timeout}s)" if suite.timeout != 300 else ""
            parallel_info = " [parallel]" if suite.parallel else ""
            epic_info = f" [{suite.epic}]" if suite.epic else ""
            print(f"  • {suite.name}{epic_info}{parallel_info}{timeout_info}")
        print()
        
        self._print_epic_info(config.suites)
    
    def start_suite(self, suite_config: TestSuiteConfig):
        """Called when a test suite starts."""
        self.suite_count += 1
        
        progress = f"[{self.suite_count}/{self.total_suites}]"
        epic_info = f" ({suite_config.epic})" if suite_config.epic else ""
        
        print(f"{self._color(progress, 'blue')} {self._color('Running:', 'bold')} {suite_config.name}{epic_info}")
        print(f"    {suite_config.description}")
        
        # Show patterns being executed
        if suite_config.patterns:
            pattern_list = ', '.join(suite_config.patterns[:3])
            if len(suite_config.patterns) > 3:
                pattern_list += f" (and {len(suite_config.patterns) - 3} more)"
            print(f"    {self._color('Patterns:', 'cyan')} {pattern_list}")
        
        if suite_config.markers:
            marker_list = ', '.join(suite_config.markers)
            print(f"    {self._color('Markers:', 'cyan')} {marker_list}")
        
        print()
    
    def suite_complete(self, suite_config: TestSuiteConfig, result: ExecutionResult):
        """Called when a test suite completes."""
        # Status indicator
        if result.success:
            status = self._color("PASSED", 'green')
            icon = "✓"
        else:
            status = self._color("FAILED", 'red')
            icon = "✗"
        
        # Summary line
        duration_str = f"{result.duration:.2f}s"
        test_count = len(result.test_results)
        
        # If we don't have individual test results but have summary, use summary
        if test_count == 0 and result.summary:
            total_from_summary = sum(result.summary.values())
            if total_from_summary > 0:
                test_count = total_from_summary
        
        print(f"    {self._color(icon, 'bold')} {status} - {test_count} tests in {duration_str}")
        
        # Detailed summary
        if result.summary:
            summary_parts = []
            for status, count in result.summary.items():
                if count > 0:
                    color = self._get_status_color(status)
                    summary_parts.append(self._color(f"{count} {status}", color))
            
            if summary_parts:
                print(f"      {', '.join(summary_parts)}")
        
        # Show failures with enhanced diagnostics
        if not result.success and result.test_results:
            failed_tests = [tr for tr in result.test_results if tr.status in ['failed', 'error']]
            if failed_tests:
                print(f"      {self._color('Failed tests:', 'red')}")
                
                # Quick diagnostics for immediate feedback
                if self.enable_diagnostics and self.diagnostics_engine:
                    self._show_quick_diagnostics(failed_tests, suite_config.name)
                else:
                    # Fallback to simple list
                    for test in failed_tests[:3]:
                        print(f"        • {test.name}")
                    if len(failed_tests) > 3:
                        print(f"        ... and {len(failed_tests) - 3} more")
        
        print()
    
    def run_complete(self, config: TestRunConfig, results: Dict[str, ExecutionResult]):
        """Called when the entire test run completes."""
        self.all_results = results  # Store for diagnostics
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Calculate totals
        total_tests = sum(len(result.test_results) for result in results.values())
        passed_suites = sum(1 for result in results.values() if result.success)
        failed_suites = len(results) - passed_suites
        failed_tests = sum(
            len([test for test in result.test_results if test.status in ['failed', 'error']])
            for result in results.values()
        )
        
        # Overall status
        overall_success = all(result.success for result in results.values())
        if overall_success:
            status = self._color("PASSED", 'green')
            icon = "✓"
        else:
            status = self._color("FAILED", 'red') 
            icon = "✗"
        
        self._print_header(f"{icon} Test Run {status}")
        
        print(f"{self._color('Summary:', 'bold')}")
        print(f"  Total Duration: {total_duration:.2f}s")
        print(f"  Total Tests: {total_tests}")
        success_rate = ((total_tests - failed_tests) / total_tests * 100) if total_tests > 0 else 0
        print(f"  Success Rate: {self._color(f'{success_rate:.1f}%', 'green' if success_rate >= 95 else 'yellow' if success_rate >= 80 else 'red')}")
        print(f"  Suite Results: {self._color(f'{passed_suites} passed', 'green')}, {self._color(f'{failed_suites} failed', 'red') if failed_suites else '0 failed'}")
        if failed_tests > 0:
            print(f"  Failed Tests: {self._color(str(failed_tests), 'red')}")
        print()
        
        # Epic-specific summary
        epic_results = {}
        for suite_name, result in results.items():
            # Find suite config to get epic info
            suite_config = next((s for s in config.suites if s.name == suite_name), None)
            if suite_config and suite_config.epic:
                if suite_config.epic not in epic_results:
                    epic_results[suite_config.epic] = {'passed': 0, 'failed': 0}
                
                if result.success:
                    epic_results[suite_config.epic]['passed'] += 1
                else:
                    epic_results[suite_config.epic]['failed'] += 1
        
        if epic_results:
            print(f"{self._color('Epic Results:', 'purple')}")
            for epic, counts in epic_results.items():
                total_epic = counts['passed'] + counts['failed']
                success_rate = (counts['passed'] / total_epic * 100) if total_epic > 0 else 0
                print(f"  {self._color(epic.upper(), 'cyan')}: {success_rate:.1f}% success rate ({counts['passed']}/{total_epic} suites)")
            print()
        
        # Individual suite results
        print(f"{self._color('Suite Details:', 'bold')}")
        for suite_name, result in results.items():
            status_color = 'green' if result.success else 'red'
            status_text = "PASSED" if result.success else "FAILED"
            duration = f"{result.duration:.2f}s"
            test_count = len(result.test_results)
            
            print(f"  {self._color(status_text, status_color)} {suite_name} - {test_count} tests in {duration}")
        
        print(f"\n{self._color('=', 'blue') * 60}")
        
        # Enhanced diagnostics section
        if not overall_success and self.enable_diagnostics and self.diagnostics_engine:
            self._show_comprehensive_diagnostics(results)
        
        # Exit message
        if overall_success:
            print(f"\n{self._color('🎉 All tests passed! System is ready.', 'green')}")
        else:
            print(f"\n{self._color('❌ Some tests failed. Review the results above.', 'red')}")
            if self.enable_diagnostics:
                print(f"{self._color('💡 Check the diagnostic analysis above for actionable fix suggestions.', 'yellow')}")
    
    def run_failed(self, config: TestRunConfig, results: Dict[str, ExecutionResult]):
        """Called when a test run fails (e.g., fail-fast triggered)."""
        print(f"\n{self._color('⚠️  Test run stopped early due to fail-fast mode.', 'yellow')}")
        self.run_complete(config, results)
    
    def _get_status_color(self, status: str) -> str:
        """Get color for test status."""
        color_map = {
            'passed': 'green',
            'failed': 'red',
            'skipped': 'yellow',
            'error': 'red',
            'timeout': 'red'
        }
        return color_map.get(status, 'end')
    
    def _show_quick_diagnostics(self, failed_tests: List, suite_name: str):
        """Show quick diagnostics for failed tests in a suite."""
        
        # Categorize failures quickly
        import_errors = []
        assertion_errors = []
        api_errors = []
        other_errors = []
        
        for test in failed_tests[:5]:  # Limit to first 5 for quick feedback
            error_text = f"{test.message or ''} {test.traceback or ''}".lower()
            
            if 'import' in error_text or 'module' in error_text:
                import_errors.append(test.name)
            elif 'assertion' in error_text:
                assertion_errors.append(test.name)
            elif 'api' in error_text or 'connection' in error_text or 'auth' in error_text:
                api_errors.append(test.name)
            else:
                other_errors.append(test.name)
        
        # Show categorized failures
        if import_errors:
            print(f"        {self._color('🔴 Import Errors:', 'red')} {len(import_errors)} tests")
            for test_name in import_errors[:2]:
                print(f"          • {test_name}")
            if len(import_errors) > 2:
                print(f"          ... and {len(import_errors) - 2} more")
            print(f"        {self._color('💡 Fix: Check PYTHONPATH and module installation', 'yellow')}")
        
        if assertion_errors:
            print(f"        {self._color('🟡 Logic Errors:', 'yellow')} {len(assertion_errors)} tests")
            for test_name in assertion_errors[:2]:
                print(f"          • {test_name}")
            if len(assertion_errors) > 2:
                print(f"          ... and {len(assertion_errors) - 2} more")
            print(f"        {self._color('💡 Fix: Review test expectations and recent code changes', 'yellow')}")
        
        if api_errors:
            print(f"        {self._color('🔵 API Errors:', 'blue')} {len(api_errors)} tests")
            for test_name in api_errors[:2]:
                print(f"          • {test_name}")
            if len(api_errors) > 2:
                print(f"          ... and {len(api_errors) - 2} more")
            print(f"        {self._color('💡 Fix: Check API keys and network connectivity', 'yellow')}")
        
        if other_errors:
            for test_name in other_errors[:2]:
                print(f"        • {test_name}")
            if len(other_errors) > 2:
                print(f"        ... and {len(other_errors) - 2} more")
    
    def _show_comprehensive_diagnostics(self, results: Dict[str, ExecutionResult]):
        """Show comprehensive diagnostic analysis."""
        
        # Collect all failed tests
        all_failed_tests = []
        all_output = []
        all_error_output = []
        
        for result in results.values():
            failed_tests = [test for test in result.test_results if test.status in ['failed', 'error']]
            all_failed_tests.extend(failed_tests)
            all_output.append(result.output)
            all_error_output.append(result.error_output)
        
        if not all_failed_tests:
            return
        
        # Generate diagnostics
        diagnostics = self.diagnostics_engine.analyze_test_output(
            "\n".join(all_output),
            "\n".join(all_error_output),
            all_failed_tests
        )
        
        self._print_header("🔍 Diagnostic Analysis", "─")
        
        # Show executive summary
        summary = diagnostics.get('diagnostic_summary', {})
        if summary:
            print(f"{self._color('Executive Summary:', 'bold')}")
            print(f"  Total Issues: {summary.get('total_issues', 0)}")
            
            if summary.get('critical_issues', 0) > 0:
                print(f"  {self._color('⚠️  Critical Issues:', 'red')} {summary['critical_issues']} (immediate attention required)")
            if summary.get('major_issues', 0) > 0:
                print(f"  {self._color('🔸 Major Issues:', 'yellow')} {summary['major_issues']} (high priority)")
            if summary.get('minor_issues', 0) > 0:
                print(f"  {self._color('🔹 Minor Issues:', 'blue')} {summary['minor_issues']} (low priority)")
            
            print()
        
        # Show top priority actions
        priority_actions = summary.get('priority_actions', [])
        if priority_actions:
            print(f"{self._color('🚀 Priority Actions:', 'bold')}")
            for i, action in enumerate(priority_actions[:5], 1):
                print(f"  {i}. {action}")
            print()
        
        # Show component health
        component_health = diagnostics.get('component_health', {})
        if component_health:
            print(f"{self._color('🏥 Component Health:', 'bold')}")
            
            for component, health_data in component_health.items():
                status = health_data.get('status', 'unknown')
                issue_count = health_data.get('issue_count', 0)
                
                status_colors = {
                    'healthy': 'green',
                    'warning': 'yellow', 
                    'degraded': 'yellow',
                    'critical': 'red'
                }
                
                status_icons = {
                    'healthy': '✅',
                    'warning': '⚠️',
                    'degraded': '🟡',
                    'critical': '🔴'
                }
                
                color = status_colors.get(status, 'end')
                icon = status_icons.get(status, '❓')
                
                print(f"  {icon} {self._color(component, color)}: {status.upper()}")
                if issue_count > 0:
                    print(f"    Issues: {issue_count} ({health_data.get('critical_issues', 0)} critical, {health_data.get('major_issues', 0)} major)")
            print()
        
        # Show specific issue details for critical/major issues
        issues = diagnostics.get('issues', [])
        critical_major_issues = [
            issue for issue in issues 
            if issue.get('impact_level') in ['critical', 'major']
        ]
        
        if critical_major_issues:
            print(f"{self._color('🎯 High Priority Issue Details:', 'bold')}")
            
            for i, issue in enumerate(critical_major_issues[:3], 1):  # Show top 3
                impact = issue.get('impact_level', 'unknown')
                component = issue.get('component', 'Unknown')
                description = issue.get('description', 'No description')
                suggested_fixes = issue.get('suggested_fixes', [])
                
                impact_color = 'red' if impact == 'critical' else 'yellow'
                impact_icon = '🚨' if impact == 'critical' else '⚠️'
                
                print(f"\n  {impact_icon} {self._color(f'Issue #{i}: {component}', impact_color)}")
                print(f"     {description}")
                
                if suggested_fixes:
                    print(f"     {self._color('Suggested Fixes:', 'cyan')}")
                    for fix in suggested_fixes[:3]:  # Show top 3 fixes
                        print(f"       • {fix}")
            
            if len(critical_major_issues) > 3:
                remaining = len(critical_major_issues) - 3
                print(f"\n  {self._color(f'... and {remaining} more high-priority issues', 'yellow')}")
            print()
        
        # Show remediation summary
        remediation = diagnostics.get('remediation_plan', {})
        if remediation:
            estimated_effort = remediation.get('estimated_total_effort', 'Unknown')
            print(f"{self._color('⏱️  Estimated Fix Time:', 'bold')} {estimated_effort}")
            
            immediate_actions = remediation.get('immediate_actions', [])
            if immediate_actions:
                print(f"{self._color('🚨 Immediate Actions Required:', 'red')}")
                for action in immediate_actions[:3]:
                    component = action.get('component', 'Unknown')
                    description = action.get('description', 'No description')
                    print(f"  • {component}: {description}")
                if len(immediate_actions) > 3:
                    print(f"  ... and {len(immediate_actions) - 3} more immediate actions")
            print()
        
        print(f"{self._color('📄 Full diagnostic report saved to JSON output file', 'cyan')}")
        print(f"{self._color('─', 'blue') * 60}")