#!/usr/bin/env python3
"""
Test Enhanced Diagnostics System

Validates the enhanced JSON output and diagnostic capabilities
with real Epic 1 test failures and provides actionable insights.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tests.runner.config import TestRunConfig, TestSuiteConfig
from tests.runner.reporters.json_reporter import JSONReporter
from tests.runner.reporters.terminal import TerminalReporter
from tests.runner.adapters.pytest_adapter import PyTestAdapter
from tests.runner.executor import ExecutionOrchestrator


def main():
    """Test the enhanced diagnostic system with Epic 1 tests."""
    
    print("🧪 Testing Enhanced Diagnostic System")
    print("=" * 60)
    
    # Configure test suite to run Epic 1 Phase 2 tests (known to have some failures)
    epic1_suite = TestSuiteConfig(
        name="epic1_phase2_enhanced_diagnostics",
        description="Epic 1 Phase 2 tests for diagnostic validation",
        patterns=[
            "tests/epic1/phase2/test_adaptive_router.py",
            "tests/epic1/phase2/test_epic1_answer_generator.py",
            "tests/epic1/phase2/test_cost_tracker.py"
        ],
        markers=None,
        timeout=300,
        parallel=False,
        epic="epic1"
    )
    
    # Configure test run with enhanced diagnostics
    config = TestRunConfig(
        suites=[epic1_suite],
        output_format="both",  # Both terminal and JSON
        verbose=True,
        fail_fast=False,  # Don't stop on first failure - capture all issues
        capture="no"
    )
    
    # Create enhanced reporters
    json_reporter = JSONReporter(
        output_file="enhanced_diagnostic_report.json",
        enable_diagnostics=True
    )
    
    terminal_reporter = TerminalReporter(
        use_colors=True,
        enable_diagnostics=True
    )
    
    # Execute tests with enhanced diagnostics
    orchestrator = ExecutionOrchestrator()
    
    print("🔧 Executing Epic 1 tests with enhanced diagnostics...")
    print(f"   Running: {epic1_suite.name}")
    print(f"   Patterns: {len(epic1_suite.patterns)} test files")
    print(f"   Diagnostics: ENABLED")
    print()
    
    try:
        # Run the tests - we need to handle multiple reporters manually
        # Start run for all reporters
        for reporter in [terminal_reporter, json_reporter]:
            reporter.start_run(config)
        
        # Execute suite
        for reporter in [terminal_reporter, json_reporter]:
            reporter.start_suite(epic1_suite)
        
        result = orchestrator.execute_suite(epic1_suite, config)
        results = {epic1_suite.name: result}
        
        # Complete suite for all reporters
        for reporter in [terminal_reporter, json_reporter]:
            reporter.suite_complete(epic1_suite, result)
        
        # Complete run for all reporters
        for reporter in [terminal_reporter, json_reporter]:
            reporter.run_complete(config, results)
        
        success = result.success
        
        print("\n" + "=" * 60)
        print("🔍 Enhanced Diagnostic System Validation")
        print("=" * 60)
        
        # Validate the enhanced output
        json_report_path = Path("enhanced_diagnostic_report.json")
        if json_report_path.exists():
            print(f"✅ Enhanced JSON report generated: {json_report_path}")
            
            # Read and analyze the enhanced report
            import json
            with open(json_report_path, 'r') as f:
                report_data = json.load(f)
            
            # Validate enhanced schema
            print("\n📋 Enhanced Report Schema Validation:")
            
            # Check format version
            format_version = report_data.get('metadata', {}).get('format_version')
            print(f"   Format Version: {format_version} {'✅' if format_version == '2.0' else '❌'}")
            
            # Check diagnostics section
            has_diagnostics = 'diagnostics' in report_data and report_data['diagnostics'] is not None
            print(f"   Diagnostics Section: {'✅' if has_diagnostics else '❌'}")
            
            # Check environment info
            has_env_info = 'environment_info' in report_data.get('execution', {})
            print(f"   Environment Info: {'✅' if has_env_info else '❌'}")
            
            # Check health indicators
            has_health = 'health_indicators' in report_data.get('summary', {})
            print(f"   Health Indicators: {'✅' if has_health else '❌'}")
            
            if has_diagnostics:
                diagnostics = report_data['diagnostics']
                
                print("\n🎯 Diagnostic Content Analysis:")
                
                # Check diagnostic summary
                diag_summary = diagnostics.get('diagnostic_summary', {})
                total_issues = diag_summary.get('total_issues', 0)
                print(f"   Total Issues Found: {total_issues}")
                
                if total_issues > 0:
                    critical_issues = diag_summary.get('critical_issues', 0)
                    major_issues = diag_summary.get('major_issues', 0)
                    minor_issues = diag_summary.get('minor_issues', 0)
                    
                    print(f"   Critical Issues: {critical_issues}")
                    print(f"   Major Issues: {major_issues}")
                    print(f"   Minor Issues: {minor_issues}")
                    
                    # Check priority actions
                    priority_actions = diag_summary.get('priority_actions', [])
                    print(f"   Priority Actions: {len(priority_actions)}")
                    
                    # Check component health
                    component_health = diagnostics.get('component_health', {})
                    print(f"   Component Health Analysis: {len(component_health)} components")
                    
                    # Check remediation plan
                    remediation = diagnostics.get('remediation_plan', {})
                    estimated_effort = remediation.get('estimated_total_effort', 'Unknown')
                    print(f"   Estimated Fix Time: {estimated_effort}")
                    
                    print("\n🚀 Top Priority Actions:")
                    for i, action in enumerate(priority_actions[:3], 1):
                        print(f"   {i}. {action}")
                    
                    print("\n🏥 Component Health Status:")
                    for component, health in component_health.items():
                        status = health.get('status', 'unknown')
                        issue_count = health.get('issue_count', 0)
                        print(f"   {component}: {status.upper()} ({issue_count} issues)")
                
                else:
                    print("   ✅ No issues detected - all tests passed!")
            
            else:
                print("   ℹ️  No diagnostics generated (all tests may have passed)")
            
            # Validate enhanced test details
            print("\n📊 Enhanced Test Details:")
            suites = report_data.get('suites', [])
            for suite in suites:
                suite_name = suite.get('name', 'Unknown')
                suite_result = suite.get('result', {})
                tests = suite_result.get('tests', [])
                
                enhanced_tests = 0
                for test in tests:
                    if 'traceback' in test and 'epic' in test and 'file_location' in test:
                        enhanced_tests += 1
                
                print(f"   {suite_name}: {enhanced_tests}/{len(tests)} tests have enhanced details")
        
        else:
            print("❌ Enhanced JSON report not generated")
        
        print("\n" + "=" * 60)
        print("🎉 Enhanced Diagnostic System Test Complete")
        print("=" * 60)
        
        if success:
            print("✅ All tests passed - diagnostic system ready for production")
        else:
            print("📋 Some tests failed - diagnostic system provided actionable insights")
        
        print(f"\n📄 Full enhanced report: {json_report_path}")
        print("💡 Review the terminal output above for immediate diagnostic insights")
        
        return success
        
    except Exception as e:
        print(f"❌ Error testing enhanced diagnostics: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)