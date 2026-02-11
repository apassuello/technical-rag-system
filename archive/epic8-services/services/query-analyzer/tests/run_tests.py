#!/usr/bin/env python3
"""
Test runner script for Query Analyzer Service.

This script provides different test execution modes and reporting options.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run Query Analyzer Service tests")
    
    parser.add_argument(
        "--suite",
        choices=["unit", "integration", "api", "performance", "all"],
        default="unit",
        help="Test suite to run (default: unit)"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true", 
        help="Run tests in parallel"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first failure"
    )
    
    parser.add_argument(
        "--markers",
        type=str,
        help="Run tests with specific markers (e.g., 'not slow')"
    )
    
    parser.add_argument(
        "--pattern",
        type=str,
        help="Run tests matching pattern"
    )
    
    args = parser.parse_args()
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test suite path
    if args.suite == "all":
        cmd.append(".")
    else:
        cmd.append(args.suite)
    
    # Add options
    if args.coverage:
        cmd.extend(["--cov=app", "--cov-report=html", "--cov-report=term-missing"])
    
    if args.parallel:
        cmd.extend(["-n", "auto"])
    
    if args.verbose:
        cmd.append("-v")
    
    if args.fail_fast:
        cmd.append("-x")
    
    if args.markers:
        cmd.extend(["-m", args.markers])
    
    if args.pattern:
        cmd.extend(["-k", args.pattern])
    
    # Set environment variables
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent)
    
    print(f"Running command: {' '.join(cmd)}")
    print(f"Working directory: {Path.cwd()}")
    print(f"PYTHONPATH: {env.get('PYTHONPATH', 'Not set')}")
    print("-" * 50)
    
    # Execute tests
    try:
        result = subprocess.run(cmd, env=env, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        return 130
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def run_unit_tests():
    """Run unit tests only."""
    return subprocess.run([
        "python", "-m", "pytest", "unit/",
        "-v", "--tb=short"
    ]).returncode


def run_integration_tests():
    """Run integration tests only."""
    return subprocess.run([
        "python", "-m", "pytest", "integration/", 
        "-v", "--tb=short"
    ]).returncode


def run_api_tests():
    """Run API tests only."""
    return subprocess.run([
        "python", "-m", "pytest", "api/",
        "-v", "--tb=short"
    ]).returncode


def run_performance_tests():
    """Run performance tests only."""
    return subprocess.run([
        "python", "-m", "pytest", "performance/",
        "-v", "--tb=short", "-m", "not slow"
    ]).returncode


def run_quick_tests():
    """Run quick smoke tests."""
    return subprocess.run([
        "python", "-m", "pytest", "unit/test_analyzer_service.py::TestQueryAnalyzerService::test_initialization",
        "api/test_health_endpoints.py::TestLivenessProbe::test_liveness_basic",
        "-v"
    ]).returncode


def run_with_coverage():
    """Run all tests with coverage report."""
    return subprocess.run([
        "python", "-m", "pytest", ".",
        "--cov=app",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-fail-under=80",
        "-v"
    ]).returncode


if __name__ == "__main__":
    # Change to tests directory
    tests_dir = Path(__file__).parent
    os.chdir(tests_dir)
    
    # Check if specific function requested
    if len(sys.argv) > 1 and sys.argv[1] in [
        "unit", "integration", "api", "performance", "quick", "coverage"
    ]:
        command = sys.argv[1]
        if command == "unit":
            exit_code = run_unit_tests()
        elif command == "integration":
            exit_code = run_integration_tests()
        elif command == "api":
            exit_code = run_api_tests()
        elif command == "performance":
            exit_code = run_performance_tests()
        elif command == "quick":
            exit_code = run_quick_tests()
        elif command == "coverage":
            exit_code = run_with_coverage()
        
        sys.exit(exit_code)
    
    # Default to main function with argument parsing
    sys.exit(main())