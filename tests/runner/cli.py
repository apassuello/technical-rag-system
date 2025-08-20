"""
Command Line Interface

Main CLI for the test execution system with Epic-aware commands.
Provides user-friendly interface for running various test suites.
"""

import sys
import argparse
from pathlib import Path
from typing import List, Optional

from .config import TestConfig
from .executor import ExecutionOrchestrator
from .reporters import TerminalReporter, JSONReporter
from .discovery import TestDiscovery


class TestRunner:
    """Main test runner CLI."""
    
    def __init__(self):
        """Initialize test runner."""
        self.config = TestConfig()
        self.orchestrator = ExecutionOrchestrator()
        self.discovery = TestDiscovery()
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """Run the CLI with given arguments."""
        parser = self._create_parser()
        parsed_args = parser.parse_args(args)
        
        # Handle global options
        if hasattr(parsed_args, 'config') and parsed_args.config:
            self.config = TestConfig(Path(parsed_args.config))
        
        # Dispatch to subcommand handler
        if hasattr(parsed_args, 'func'):
            try:
                return parsed_args.func(parsed_args)
            except KeyboardInterrupt:
                print("\n⚠️  Test execution interrupted by user.")
                return 1
            except Exception as e:
                print(f"❌ Error: {e}")
                return 1
        else:
            parser.print_help()
            return 1
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser."""
        parser = argparse.ArgumentParser(
            prog='test-runner',
            description='RAG Portfolio Test Execution System',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Run all Epic 1 tests
  test-runner epic1 all
  
  # Run Epic 1 integration tests only
  test-runner epic1 integration
  
  # Run Epic 1 unit tests with JSON output
  test-runner epic1 unit --format json
  
  # Run quick smoke tests
  test-runner smoke
  
  # List available test suites
  test-runner list
  
  # Run specific patterns
  test-runner run "tests/epic1/**/*.py" --markers epic1,integration
            """
        )
        
        # Global options
        parser.add_argument(
            '--config', '-c',
            type=str,
            help='Path to test configuration file'
        )
        
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Verbose output'
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Epic 1 command
        self._add_epic1_parser(subparsers)
        
        # Epic 2 command (future)
        self._add_epic2_parser(subparsers)
        
        # Smoke tests command
        self._add_smoke_parser(subparsers)
        
        # Regression tests command
        self._add_regression_parser(subparsers)
        
        # Custom run command
        self._add_run_parser(subparsers)
        
        # List command
        self._add_list_parser(subparsers)
        
        # Validate command
        self._add_validate_parser(subparsers)
        
        return parser
    
    def _add_epic1_parser(self, subparsers):
        """Add Epic 1 test command."""
        epic1_parser = subparsers.add_parser(
            'epic1',
            help='Run Epic 1 tests',
            description='Execute Epic 1 multi-model routing tests'
        )
        
        epic1_subparsers = epic1_parser.add_subparsers(dest='epic1_command', help='Epic 1 test types')
        
        # Epic 1 unit tests
        unit_parser = epic1_subparsers.add_parser('unit', help='Run Epic 1 unit tests')
        self._add_common_test_options(unit_parser)
        unit_parser.set_defaults(func=lambda args: self._run_suite('epic1_unit', args))
        
        # Epic 1 integration tests
        integration_parser = epic1_subparsers.add_parser('integration', help='Run Epic 1 integration tests')
        self._add_common_test_options(integration_parser)
        integration_parser.set_defaults(func=lambda args: self._run_suite('epic1_integration', args))
        
        # Epic 1 phase 2 tests
        phase2_parser = epic1_subparsers.add_parser('phase2', help='Run Epic 1 Phase 2 tests')
        self._add_common_test_options(phase2_parser)
        phase2_parser.set_defaults(func=lambda args: self._run_suite('epic1_phase2', args))
        
        # All Epic 1 tests
        all_parser = epic1_subparsers.add_parser('all', help='Run all Epic 1 tests')
        self._add_common_test_options(all_parser)
        all_parser.set_defaults(func=lambda args: self._run_suite('epic1_all', args))
        
        # Set default to show help
        epic1_parser.set_defaults(func=lambda args: epic1_parser.print_help() or 0)
    
    def _add_epic2_parser(self, subparsers):
        """Add Epic 2 test command (placeholder)."""
        epic2_parser = subparsers.add_parser(
            'epic2', 
            help='Run Epic 2 tests (future)',
            description='Execute Epic 2 tests (not yet implemented)'
        )
        epic2_parser.set_defaults(func=lambda args: print("Epic 2 tests not yet implemented") or 0)
    
    def _add_smoke_parser(self, subparsers):
        """Add smoke test command."""
        smoke_parser = subparsers.add_parser(
            'smoke',
            help='Run smoke tests',
            description='Quick health checks across the system'
        )
        self._add_common_test_options(smoke_parser)
        smoke_parser.set_defaults(func=lambda args: self._run_suite('smoke', args))
    
    def _add_regression_parser(self, subparsers):
        """Add regression test command."""
        regression_parser = subparsers.add_parser(
            'regression',
            help='Run regression tests',
            description='Bug fix validation tests'
        )
        self._add_common_test_options(regression_parser)
        regression_parser.set_defaults(func=lambda args: self._run_suite('regression', args))
    
    def _add_run_parser(self, subparsers):
        """Add custom run command."""
        run_parser = subparsers.add_parser(
            'run',
            help='Run tests matching patterns',
            description='Run tests using custom patterns and filters'
        )
        
        run_parser.add_argument(
            'patterns',
            nargs='+',
            help='Test file patterns to run'
        )
        
        run_parser.add_argument(
            '--markers', '-m',
            help='Comma-separated list of test markers'
        )
        
        self._add_common_test_options(run_parser)
        run_parser.set_defaults(func=self._run_patterns)
    
    def _add_list_parser(self, subparsers):
        """Add list command."""
        list_parser = subparsers.add_parser(
            'list',
            help='List available test suites',
            description='Show all available test suites and their configurations'
        )
        list_parser.set_defaults(func=self._list_suites)
    
    def _add_validate_parser(self, subparsers):
        """Add validate command."""
        validate_parser = subparsers.add_parser(
            'validate',
            help='Validate test configuration',
            description='Check test setup and configuration'
        )
        validate_parser.set_defaults(func=self._validate_setup)
    
    def _add_common_test_options(self, parser):
        """Add common test execution options."""
        parser.add_argument(
            '--format', '-f',
            choices=['terminal', 'json'],
            default='terminal',
            help='Output format'
        )
        
        parser.add_argument(
            '--fail-fast', '-x',
            action='store_true',
            help='Stop on first failure'
        )
        
        parser.add_argument(
            '--parallel', '-n',
            action='store_true', 
            help='Run tests in parallel'
        )
        
        parser.add_argument(
            '--timeout', '-t',
            type=int,
            help='Test timeout in seconds'
        )
        
        parser.add_argument(
            '--output', '-o',
            help='Output file for JSON format'
        )
    
    def _run_suite(self, suite_name: str, args) -> int:
        """Run a specific test suite."""
        # Get suite configuration
        suite_config = self.config.get_suite(suite_name)
        if not suite_config:
            print(f"❌ Unknown test suite: {suite_name}")
            return 1
        
        # Apply command line overrides
        if hasattr(args, 'parallel') and args.parallel:
            suite_config.parallel = True
        if hasattr(args, 'timeout') and args.timeout:
            suite_config.timeout = args.timeout
        
        # Create run configuration
        run_config = self.config.create_run_config(
            [suite_name],
            output_format=getattr(args, 'format', 'terminal'),
            verbose=True,  # Always use verbose for better parsing
            fail_fast=getattr(args, 'fail_fast', False)
        )
        
        # Create reporter
        if run_config.output_format == 'json':
            output_file = getattr(args, 'output', f"{suite_name}_results.json")
            reporter = JSONReporter(output_file)
        else:
            reporter = TerminalReporter()
        
        # Execute tests
        results = self.orchestrator.execute_run_config(run_config, reporter)
        
        # Return exit code
        return 0 if all(result.success for result in results.values()) else 1
    
    def _run_patterns(self, args) -> int:
        """Run tests matching specific patterns."""
        patterns = args.patterns
        markers = args.markers.split(',') if args.markers else None
        
        # Execute using orchestrator
        result = self.orchestrator.execute_patterns(
            patterns=patterns,
            markers=markers,
            verbose=getattr(args, 'verbose', True),
            fail_fast=getattr(args, 'fail_fast', False),
            parallel=getattr(args, 'parallel', False),
            timeout=getattr(args, 'timeout', 300)
        )
        
        # Simple output for pattern execution
        print(f"\n📊 Executed {len(result.test_results)} tests in {result.duration:.2f}s")
        if result.summary:
            summary_parts = []
            for status, count in result.summary.items():
                if count > 0:
                    summary_parts.append(f"{count} {status}")
            print(f"Results: {', '.join(summary_parts)}")
        
        return 0 if result.success else 1
    
    def _list_suites(self, args) -> int:
        """List available test suites."""
        print("\n🧪 Available Test Suites:")
        print("=" * 50)
        
        suite_names = self.config.list_suites()
        
        if not suite_names:
            print("No test suites configured.")
            return 0
        
        for suite_name in sorted(suite_names):
            suite_config = self.config.get_suite(suite_name)
            if suite_config:
                epic_info = f" [{suite_config.epic}]" if suite_config.epic else ""
                timeout_info = f" (timeout: {suite_config.timeout}s)" if suite_config.timeout != 300 else ""
                parallel_info = " [parallel]" if suite_config.parallel else ""
                
                print(f"\n• {suite_config.name}{epic_info}{parallel_info}{timeout_info}")
                print(f"  {suite_config.description}")
                
                # Show first few patterns
                if suite_config.patterns:
                    pattern_display = suite_config.patterns[:2]
                    if len(suite_config.patterns) > 2:
                        pattern_display.append(f"... and {len(suite_config.patterns) - 2} more")
                    print(f"  Patterns: {', '.join(pattern_display)}")
                
                if suite_config.markers:
                    print(f"  Markers: {', '.join(suite_config.markers)}")
        
        print(f"\n📝 Use 'test-runner <suite-name>' to run a specific suite")
        print(f"📝 Use 'test-runner epic1 all' to run all Epic 1 tests")
        
        return 0
    
    def _validate_setup(self, args) -> int:
        """Validate test setup and configuration."""
        print("\n🔍 Validating Test Setup:")
        print("=" * 40)
        
        success = True
        
        # Validate adapter
        print("• Checking test adapter...")
        if self.orchestrator.validate_adapter():
            print("  ✓ Test adapter (pytest) is working")
        else:
            print("  ❌ Test adapter validation failed")
            success = False
        
        # Validate configuration
        print("\n• Checking configuration...")
        suite_names = self.config.list_suites()
        if suite_names:
            print(f"  ✓ Found {len(suite_names)} test suites")
        else:
            print("  ⚠️  No test suites configured")
        
        # Validate test patterns
        print("\n• Validating test patterns...")
        for suite_name in suite_names:
            suite_config = self.config.get_suite(suite_name)
            if suite_config:
                print(f"  {suite_config.name}:")
                pattern_results = self.discovery.validate_patterns(suite_config.patterns)
                for pattern, valid, message in pattern_results:
                    status = "✓" if valid else "❌"
                    print(f"    {status} {pattern}: {message}")
                    if not valid:
                        success = False
        
        # Overall result
        if success:
            print(f"\n✅ Test setup validation passed!")
            return 0
        else:
            print(f"\n❌ Test setup validation failed!")
            return 1


def main():
    """Main entry point for CLI."""
    runner = TestRunner()
    return runner.run()


if __name__ == '__main__':
    sys.exit(main())