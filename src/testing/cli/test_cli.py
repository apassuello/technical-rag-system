#!/usr/bin/env python3
"""
Unified Test Execution CLI

A sophisticated command-line interface for executing all test suites with
enhanced reporting, parallel execution, and extensible architecture.

Usage Examples:
    python -m src.testing.cli.test_cli epic1 integration
    python -m src.testing.cli.test_cli epic1 unit --parallel
    python -m src.testing.cli.test_cli epic1 all --output json
    python -m src.testing.cli.test_cli diagnostic --filter performance
    python -m src.testing.cli.test_cli --list-suites
    python -m src.testing.cli.test_cli epic2 smoke --verbose
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any, Dict

from src.testing.core.test_discovery import TestDiscovery
from src.testing.core.test_orchestrator import TestOrchestrator
from src.testing.reporting.report_manager import ReportManager
from src.testing.utils.logging_config import setup_cli_logging


class TestCLI:
    """Command-line interface for unified test execution."""
    
    def __init__(self):
        self.orchestrator = TestOrchestrator()
        self.discovery = TestDiscovery()
        self.report_manager = ReportManager()
        
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser with subcommands."""
        parser = argparse.ArgumentParser(
            prog='test-runner',
            description='Unified Test Execution System for RAG Portfolio',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s epic1 integration           # Run Epic 1 integration tests
  %(prog)s epic1 unit --parallel       # Run Epic 1 unit tests in parallel
  %(prog)s epic1 all --output json     # Run all Epic 1 tests with JSON output
  %(prog)s diagnostic --filter performance  # Run diagnostic performance tests
  %(prog)s --list-suites               # List all available test suites
  %(prog)s epic2 smoke --verbose       # Run Epic 2 smoke tests with verbose output
            """
        )
        
        # Global options
        parser.add_argument(
            '--version', 
            action='version', 
            version='Test Runner 1.0.0'
        )
        parser.add_argument(
            '--list-suites', 
            action='store_true',
            help='List all available test suites and exit'
        )
        parser.add_argument(
            '--config', 
            type=Path,
            default=Path('config/testing.yaml'),
            help='Path to test configuration file'
        )
        parser.add_argument(
            '--verbose', '-v',
            action='count',
            default=0,
            help='Increase verbosity (use -v, -vv, -vvv)'
        )
        parser.add_argument(
            '--quiet', '-q',
            action='store_true',
            help='Suppress output except for errors'
        )
        
        # Output options
        output_group = parser.add_argument_group('Output Options')
        output_group.add_argument(
            '--output',
            choices=['terminal', 'json', 'html', 'junit'],
            default='terminal',
            help='Output format for test results'
        )
        output_group.add_argument(
            '--output-dir',
            type=Path,
            default=Path('test-results'),
            help='Directory for output files'
        )
        output_group.add_argument(
            '--report-name',
            help='Custom name for report files'
        )
        
        # Execution options
        exec_group = parser.add_argument_group('Execution Options')
        exec_group.add_argument(
            '--parallel', '-p',
            action='store_true',
            help='Run tests in parallel where supported'
        )
        exec_group.add_argument(
            '--workers',
            type=int,
            default=4,
            help='Number of parallel workers (default: 4)'
        )
        exec_group.add_argument(
            '--timeout',
            type=int,
            default=300,
            help='Test execution timeout in seconds (default: 300)'
        )
        exec_group.add_argument(
            '--fail-fast',
            action='store_true',
            help='Stop execution on first failure'
        )
        
        # Filtering options
        filter_group = parser.add_argument_group('Filtering Options')
        filter_group.add_argument(
            '--filter',
            help='Filter tests by pattern (supports regex)'
        )
        filter_group.add_argument(
            '--exclude',
            help='Exclude tests by pattern (supports regex)'
        )
        filter_group.add_argument(
            '--tags',
            nargs='*',
            help='Run tests with specific tags'
        )
        filter_group.add_argument(
            '--since',
            help='Run tests for files changed since commit/branch'
        )
        
        # Main command structure
        subparsers = parser.add_subparsers(
            dest='suite',
            help='Test suite to run',
            metavar='SUITE'
        )
        
        # Epic 1 tests
        epic1_parser = subparsers.add_parser(
            'epic1',
            help='Epic 1 Multi-Model Answer Generator tests'
        )
        epic1_parser.add_argument(
            'test_type',
            choices=['unit', 'integration', 'regression', 'smoke', 'performance', 'ml_infrastructure', 'phase2', 'all'],
            help='Type of Epic 1 tests to run'
        )
        
        # Epic 2 tests
        epic2_parser = subparsers.add_parser(
            'epic2',
            help='Epic 2 tests (extensible for future epics)'
        )
        epic2_parser.add_argument(
            'test_type',
            choices=['unit', 'integration', 'smoke', 'validation', 'all'],
            help='Type of Epic 2 tests to run'
        )
        
        # Original/Legacy tests
        legacy_parser = subparsers.add_parser(
            'legacy',
            help='Original RAG system tests'
        )
        legacy_parser.add_argument(
            'test_type',
            choices=['unit', 'integration', 'diagnostic', 'component', 'all'],
            help='Type of legacy tests to run'
        )
        
        # Diagnostic tests
        diagnostic_parser = subparsers.add_parser(
            'diagnostic',
            help='System diagnostic and health tests'
        )
        diagnostic_parser.add_argument(
            'test_type',
            nargs='?',
            choices=['performance', 'health', 'compliance', 'all'],
            default='all',
            help='Type of diagnostic tests to run'
        )
        
        # All tests
        all_parser = subparsers.add_parser(
            'all',
            help='Run comprehensive test suite across all projects'
        )
        all_parser.add_argument(
            '--exclude-suites',
            nargs='*',
            choices=['epic1', 'epic2', 'legacy', 'diagnostic'],
            help='Exclude specific test suites'
        )
        
        return parser
    
    async def run(self, args: argparse.Namespace) -> int:
        """Execute the test runner with parsed arguments."""
        try:
            # Setup logging
            setup_cli_logging(args.verbose, args.quiet)
            
            # Handle list-suites
            if args.list_suites:
                self._list_suites()
                return 0
            
            # Validate arguments
            if not args.suite:
                print("Error: No test suite specified. Use --help for usage information.")
                return 1
            
            # Configure test execution
            config = await self._load_config(args.config)
            execution_config = self._build_execution_config(args)
            
            # Discover tests
            test_plan = await self.discovery.discover_tests(
                suite=args.suite,
                test_type=getattr(args, 'test_type', 'all'),
                filters=self._build_filters(args),
                config=config
            )
            
            if not test_plan.tests:
                print(f"No tests found matching criteria for suite '{args.suite}'")
                return 0
            
            # Execute tests
            results = await self.orchestrator.execute_tests(
                test_plan,
                execution_config
            )
            
            # Generate reports
            await self.report_manager.generate_reports(
                results,
                output_format=args.output,
                output_dir=args.output_dir,
                report_name=args.report_name
            )
            
            # Return appropriate exit code
            return 0 if results.success else 1
            
        except KeyboardInterrupt:
            print("\nTest execution interrupted by user")
            return 130
        except Exception as e:
            print(f"Error: {e}")
            if args.verbose >= 2:
                import traceback
                traceback.print_exc()
            return 1
    
    def _list_suites(self):
        """List all available test suites and their types."""
        suites = {
            'epic1': {
                'description': 'Multi-Model Answer Generator with Adaptive Routing',
                'types': ['unit', 'integration', 'regression', 'smoke', 'performance', 'ml_infrastructure', 'phase2', 'all'],
                'location': 'tests/epic1/'
            },
            'epic2': {
                'description': 'Future Epic 2 Implementation',
                'types': ['unit', 'integration', 'smoke', 'validation', 'all'],
                'location': 'tests/epic2_validation/'
            },
            'legacy': {
                'description': 'Original RAG System Components',
                'types': ['unit', 'integration', 'diagnostic', 'component', 'all'],
                'location': 'tests/unit/, tests/integration/, tests/diagnostic/'
            },
            'diagnostic': {
                'description': 'System Health and Performance Diagnostics',
                'types': ['performance', 'health', 'compliance', 'all'],
                'location': 'tests/diagnostic/'
            }
        }
        
        print("Available Test Suites:")
        print("=" * 50)
        
        for suite_name, info in suites.items():
            print(f"\n{suite_name.upper()}:")
            print(f"  Description: {info['description']}")
            print(f"  Location: {info['location']}")
            print(f"  Types: {', '.join(info['types'])}")
    
    async def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load test configuration from file."""
        # Implementation would load YAML/JSON config
        # For now, return default config
        return {
            'default_timeout': 300,
            'parallel_workers': 4,
            'output_formats': ['terminal', 'json'],
            'test_discovery': {
                'patterns': ['test_*.py', '*_test.py'],
                'exclude_patterns': ['__pycache__', '*.pyc']
            }
        }
    
    def _build_execution_config(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Build execution configuration from CLI arguments."""
        return {
            'parallel': args.parallel,
            'workers': args.workers,
            'timeout': args.timeout,
            'fail_fast': args.fail_fast,
            'verbose': args.verbose,
            'quiet': args.quiet
        }
    
    def _build_filters(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Build test filters from CLI arguments."""
        return {
            'pattern': args.filter,
            'exclude': args.exclude,
            'tags': args.tags or [],
            'since': args.since
        }


def main():
    """Main entry point for the CLI."""
    cli = TestCLI()
    parser = cli.create_parser()
    args = parser.parse_args()
    
    # Run the async main function
    exit_code = asyncio.run(cli.run(args))
    sys.exit(exit_code)


if __name__ == '__main__':
    main()