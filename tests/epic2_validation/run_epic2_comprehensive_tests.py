#!/usr/bin/env python3
"""
Epic 2 Comprehensive Test Suite Runner
======================================

This script runs the complete Epic 2 validation test suite including:
- Configuration validation tests
- Sub-component integration tests
- Performance validation tests
- Quality improvement tests
- End-to-end pipeline tests

The script provides multiple execution modes:
- Quick validation (basic functionality)
- Comprehensive validation (all tests)
- Performance-only testing
- Quality-only testing
- Custom test selection

Usage:
    python run_epic2_comprehensive_tests.py --mode comprehensive
    python run_epic2_comprehensive_tests.py --mode quick
    python run_epic2_comprehensive_tests.py --mode performance
    python run_epic2_comprehensive_tests.py --mode quality
    python run_epic2_comprehensive_tests.py --tests config,subcomponent
"""

import sys
import argparse
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import new Epic 2 test modules
from test_epic2_configuration_validation_new import Epic2ConfigurationValidator
from test_epic2_subcomponent_integration_new import (
    Epic2SubComponentIntegrationValidator,
)
from test_epic2_performance_validation_new import Epic2PerformanceValidator
from test_epic2_quality_validation_new import Epic2QualityValidator
from test_epic2_pipeline_validation_new import Epic2PipelineValidator
from epic2_test_utilities import (
    Epic2TestEnvironment,
    Epic2TestReporter,
    Epic2PerformanceMetrics,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("epic2_test_results.log")],
)
logger = logging.getLogger(__name__)


class Epic2ComprehensiveTestRunner:
    """
    Comprehensive test runner for Epic 2 validation suite.

    Orchestrates execution of all Epic 2 validation tests and provides
    detailed reporting and analysis of results.
    """

    def __init__(self):
        """Initialize comprehensive test runner."""
        self.reporter = Epic2TestReporter()
        self.performance_metrics = Epic2PerformanceMetrics()

        # Available test validators
        self.validators = {
            "configuration": Epic2ConfigurationValidator,
            "subcomponent": Epic2SubComponentIntegrationValidator,
            "performance": Epic2PerformanceValidator,
            "quality": Epic2QualityValidator,
            "pipeline": Epic2PipelineValidator,
        }

        # Test execution modes
        self.modes = {
            "quick": ["configuration", "subcomponent"],
            "comprehensive": [
                "configuration",
                "subcomponent",
                "performance",
                "quality",
                "pipeline",
            ],
            "performance": ["performance"],
            "quality": ["quality"],
            "integration": ["subcomponent", "pipeline"],
            "config": ["configuration"],
        }

    def validate_environment(self) -> bool:
        """Validate test environment before running tests."""
        logger.info("Validating Epic 2 test environment...")

        env_results = Epic2TestEnvironment.validate_environment()

        if env_results["overall"]["ready"]:
            logger.info("✅ Environment validation passed")
            return True
        else:
            logger.error("❌ Environment validation failed:")
            for issue in env_results["overall"]["issues"]:
                logger.error(f"  - {issue}")
            return False

    def run_test_suite(
        self, mode: str = "comprehensive", custom_tests: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run Epic 2 test suite with specified mode or custom tests."""

        # Validate environment
        if not self.validate_environment():
            return {
                "overall_score": 0,
                "status": "ENVIRONMENT_FAILED",
                "error": "Environment validation failed",
            }

        # Determine tests to run
        if custom_tests:
            tests_to_run = [test for test in custom_tests if test in self.validators]
            if not tests_to_run:
                return {
                    "overall_score": 0,
                    "status": "INVALID_TESTS",
                    "error": f"No valid tests found in: {custom_tests}",
                }
        elif mode in self.modes:
            tests_to_run = self.modes[mode]
        else:
            return {
                "overall_score": 0,
                "status": "INVALID_MODE",
                "error": f"Unknown mode: {mode}. Available: {list(self.modes.keys())}",
            }

        logger.info(f"Running Epic 2 tests: {tests_to_run}")

        # Set baseline memory
        self.performance_metrics.set_baseline_memory()

        # Execute tests
        all_results = {}
        total_tests = 0
        total_passed = 0

        for test_name in tests_to_run:
            logger.info(f"Executing {test_name} validation...")

            try:
                # Create and run validator
                self.performance_metrics.start_timer(f"{test_name}_execution")
                validator = self.validators[test_name]()
                results = validator.run_all_validations()
                execution_time = self.performance_metrics.end_timer(
                    f"{test_name}_execution"
                )

                # Store results
                all_results[test_name] = results
                self.reporter.add_test_result(test_name, results)

                # Update totals
                total_tests += results.get("total_tests", 0)
                total_passed += results.get("passed_tests", 0)

                # Log results
                score = results.get("overall_score", 0)
                status = "✅ PASS" if score >= 80 else "❌ FAIL"
                logger.info(
                    f"{test_name}: {status} ({score:.1f}%, {execution_time:.1f}ms)"
                )

                # Add test-specific metrics
                if "performance_metrics" in results:
                    for metric_name, metric_value in results[
                        "performance_metrics"
                    ].items():
                        self.performance_metrics.record_metric(
                            f"{test_name}_{metric_name}", metric_value
                        )

            except Exception as e:
                logger.error(f"Failed to execute {test_name} validation: {e}")
                all_results[test_name] = {
                    "overall_score": 0,
                    "passed_tests": 0,
                    "total_tests": 1,
                    "error": str(e),
                }

        # Calculate overall metrics
        overall_score = (total_passed / total_tests * 100) if total_tests > 0 else 0
        memory_overhead = self.performance_metrics.calculate_memory_overhead()

        # Add performance metrics to reporter
        self.reporter.add_performance_metrics(
            self.performance_metrics.get_all_metrics()
        )

        # Generate comprehensive results
        comprehensive_results = {
            "overall_score": overall_score,
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_tests - total_passed,
            "success_rate": overall_score,
            "status": "PASS" if overall_score >= 80 else "FAIL",
            "mode": mode,
            "tests_executed": tests_to_run,
            "test_results": all_results,
            "performance_summary": {
                "memory_overhead_mb": memory_overhead,
                "total_execution_time_ms": sum(
                    self.performance_metrics.get_all_metrics().get(
                        f"{test}_execution_time_ms", 0
                    )
                    for test in tests_to_run
                ),
            },
        }

        return comprehensive_results

    def generate_detailed_report(
        self, results: Dict[str, Any], output_format: str = "console"
    ) -> str:
        """Generate detailed test report."""

        if output_format == "console":
            return self._generate_console_report(results)
        elif output_format == "json":
            return json.dumps(results, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _generate_console_report(self, results: Dict[str, Any]) -> str:
        """Generate console-formatted test report."""
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append("EPIC 2 COMPREHENSIVE VALIDATION REPORT")
        lines.append("=" * 80)

        # Overall summary
        overall_score = results.get("overall_score", 0)
        status = results.get("status", "UNKNOWN")

        if overall_score >= 90:
            status_icon = "🎉 EXCELLENT"
        elif overall_score >= 80:
            status_icon = "✅ GOOD"
        elif overall_score >= 60:
            status_icon = "⚠️  NEEDS IMPROVEMENT"
        else:
            status_icon = "❌ FAILED"

        lines.append(f"Overall Status: {status_icon}")
        lines.append(f"Overall Score: {overall_score:.1f}%")
        lines.append(
            f"Tests Passed: {results['total_passed']}/{results['total_tests']}"
        )
        lines.append(f"Mode: {results['mode']}")
        lines.append("")

        # Performance summary
        perf_summary = results.get("performance_summary", {})
        if perf_summary:
            lines.append("Performance Summary:")
            lines.append("-" * 40)

            memory_overhead = perf_summary.get("memory_overhead_mb", 0)
            if memory_overhead:
                lines.append(f"Memory Overhead: {memory_overhead:.1f} MB")

            total_time = perf_summary.get("total_execution_time_ms", 0)
            if total_time:
                lines.append(f"Total Execution Time: {total_time:.1f} ms")

            lines.append("")

        # Individual test results
        lines.append("Test Results:")
        lines.append("-" * 40)

        test_results = results.get("test_results", {})
        for test_name, test_result in test_results.items():
            score = test_result.get("overall_score", 0)
            passed = test_result.get("passed_tests", 0)
            total = test_result.get("total_tests", 0)

            if score >= 80:
                status_icon = "✅"
            elif score >= 60:
                status_icon = "⚠️"
            else:
                status_icon = "❌"

            lines.append(
                f"{status_icon} {test_name.title()}: {score:.1f}% ({passed}/{total})"
            )

            # Show errors if any
            if test_result.get("validation_errors"):
                for error in test_result["validation_errors"][
                    :3
                ]:  # Show first 3 errors
                    lines.append(f"    • {error}")
                if len(test_result["validation_errors"]) > 3:
                    lines.append(
                        f"    • ... and {len(test_result['validation_errors']) - 3} more errors"
                    )

        lines.append("")

        # Detailed metrics (if available)
        if any("performance_metrics" in tr for tr in test_results.values()):
            lines.append("Key Performance Metrics:")
            lines.append("-" * 40)

            for test_name, test_result in test_results.items():
                metrics = test_result.get("performance_metrics", {})
                if metrics:
                    lines.append(f"{test_name.title()}:")
                    for metric_name, metric_value in list(metrics.items())[
                        :5
                    ]:  # Show top 5 metrics
                        if isinstance(metric_value, (int, float)):
                            if "ms" in metric_name:
                                lines.append(f"  {metric_name}: {metric_value:.1f}ms")
                            elif "percent" in metric_name or "rate" in metric_name:
                                lines.append(f"  {metric_name}: {metric_value:.1f}%")
                            else:
                                lines.append(f"  {metric_name}: {metric_value:.3f}")
                        else:
                            lines.append(f"  {metric_name}: {metric_value}")
            lines.append("")

        # Recommendations
        lines.append("Recommendations:")
        lines.append("-" * 40)

        if overall_score >= 90:
            lines.append("🎯 Epic 2 system is production-ready!")
            lines.append("   • All validation targets exceeded")
            lines.append("   • System demonstrates advanced capabilities")
            lines.append("   • Ready for portfolio demonstration")
        elif overall_score >= 80:
            lines.append("✅ Epic 2 system meets most requirements")
            lines.append("   • Core functionality validated")
            lines.append("   • Minor optimizations recommended")
            lines.append("   • Suitable for demonstration with caveats")
        elif overall_score >= 60:
            lines.append("⚠️  Epic 2 system needs improvement")
            lines.append("   • Several validation targets missed")
            lines.append("   • Performance or quality issues detected")
            lines.append("   • Requires debugging before demonstration")
        else:
            lines.append("❌ Epic 2 system has significant issues")
            lines.append("   • Multiple validation failures")
            lines.append("   • System not ready for demonstration")
            lines.append("   • Requires comprehensive debugging")

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def save_results(
        self, results: Dict[str, Any], output_dir: str = "validation_results"
    ):
        """Save test results to files."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")

        # Save JSON results
        json_file = output_path / f"epic2_validation_{timestamp}.json"
        with open(json_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        # Save console report
        console_report = self.generate_detailed_report(results, "console")
        txt_file = output_path / f"epic2_validation_{timestamp}.txt"
        with open(txt_file, "w") as f:
            f.write(console_report)

        # Save reporter data
        self.reporter.save_json_report(
            str(output_path / f"epic2_detailed_{timestamp}.json")
        )

        logger.info(f"Results saved to {output_dir}/")
        return {
            "json_file": str(json_file),
            "txt_file": str(txt_file),
            "detailed_file": str(output_path / f"epic2_detailed_{timestamp}.json"),
        }


def main():
    """Main entry point for Epic 2 comprehensive test runner."""
    parser = argparse.ArgumentParser(
        description="Epic 2 Comprehensive Test Suite Runner"
    )

    parser.add_argument(
        "--mode",
        choices=[
            "quick",
            "comprehensive",
            "performance",
            "quality",
            "integration",
            "config",
        ],
        default="comprehensive",
        help="Test execution mode",
    )

    parser.add_argument("--tests", help="Comma-separated list of specific tests to run")

    parser.add_argument(
        "--output-dir",
        default="validation_results",
        help="Output directory for test results",
    )

    parser.add_argument(
        "--output-format",
        choices=["console", "json"],
        default="console",
        help="Output format for report",
    )

    parser.add_argument(
        "--save-results", action="store_true", help="Save results to files"
    )

    parser.add_argument("--quiet", action="store_true", help="Reduce logging output")

    args = parser.parse_args()

    # Configure logging
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    # Parse custom tests
    custom_tests = None
    if args.tests:
        custom_tests = [test.strip() for test in args.tests.split(",")]

    # Create test runner
    runner = Epic2ComprehensiveTestRunner()

    try:
        # Run tests
        logger.info("Starting Epic 2 comprehensive validation...")
        start_time = time.time()

        results = runner.run_test_suite(mode=args.mode, custom_tests=custom_tests)

        execution_time = time.time() - start_time
        results["execution_time_seconds"] = execution_time

        # Generate and display report
        report = runner.generate_detailed_report(results, args.output_format)
        print(report)

        # Save results if requested
        if args.save_results:
            saved_files = runner.save_results(results, args.output_dir)
            print(f"\nResults saved to:")
            for file_type, file_path in saved_files.items():
                print(f"  {file_type}: {file_path}")

        # Set exit code based on results
        overall_score = results.get("overall_score", 0)
        if overall_score >= 80:
            logger.info(
                f"✅ Epic 2 validation completed successfully ({overall_score:.1f}%)"
            )
            sys.exit(0)
        else:
            logger.error(f"❌ Epic 2 validation failed ({overall_score:.1f}%)")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Test execution interrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
